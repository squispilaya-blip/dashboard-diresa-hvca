import re
import pandas as pd
import numpy as np
from utils.constants import COLUMN_MAP, INDICADORES, SEMAFORO


def detect_ficha_id(filename: str) -> str | None:
    m = re.search(r'[Ff]icha[_\s]?(\d{2})', filename)
    return m.group(1) if m else None


def extract_logro(hoja1_df: pd.DataFrame) -> float | None:
    for r in range(min(20, len(hoja1_df))):
        for c in range(len(hoja1_df.columns)):
            val = str(hoja1_df.iloc[r, c]).lower()
            if 'logro' in val:
                for cc in range(c, min(c + 7, len(hoja1_df.columns))):
                    raw = str(hoja1_df.iloc[r, cc]).strip()
                    pct_match = re.search(r'([\d]+(?:\.[\d]+)?)%', raw)
                    if pct_match:
                        return float(pct_match.group(1)) / 100
                    dec_match = re.match(r'^0\.\d+$', raw)
                    if dec_match:
                        return float(raw)
    return None


def _find_col(cols_set: set, cols_lower: dict, standard: str) -> str | None:
    """Busca la columna estándar usando el set y dict ya construidos."""
    candidates = COLUMN_MAP.get(standard, [])
    for cand in candidates:
        if cand in cols_set:
            return cand
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def normalize_df(df: pd.DataFrame, ficha_id: str) -> pd.DataFrame:
    # Construir lookup una sola vez para los 11 estándares de COLUMN_MAP
    cols_set   = set(df.columns)
    cols_lower = {c.lower().strip(): c for c in df.columns}
    out = {}
    for std in COLUMN_MAP:
        found = _find_col(cols_set, cols_lower, std)
        out[std] = df[found] if found is not None else np.nan
    result = pd.DataFrame(out)
    result['den'] = pd.to_numeric(result['den'], errors='coerce').fillna(0).astype(int)
    result['num'] = pd.to_numeric(result['num'], errors='coerce').fillna(0).astype(int)
    result['año'] = pd.to_numeric(result['año'], errors='coerce').fillna(0).astype(int)
    result['mes'] = pd.to_numeric(result['mes'], errors='coerce').fillna(0).astype(int)
    result['pct'] = np.where(result['den'] > 0, result['num'] / result['den'], 0.0)
    _NAN_VALS = {'NAN', 'NONE', 'N/A', 'NA', '#N/A', '#VALUE!', 'NULL', '0.0', 'NAN '}
    for col in ['red', 'microred', 'eess', 'provincia', 'nombres', 'num_doc']:
        s = result[col].fillna('').astype(str).str.strip().str.upper()
        result[col] = s.where(~s.isin(_NAN_VALS), '')
    result['ficha_id'] = ficha_id
    return result.reset_index(drop=True)


def get_semaforo_color(pct: float, logro: float | None) -> str:
    if logro is None:
        return 'verde' if pct > 0 else 'rojo'
    ratio = pct / logro if logro > 0 else 0
    if ratio >= 1.0:
        return 'verde'
    if ratio >= 0.80:
        return 'amarillo'
    return 'rojo'


def load_ficha(file, filename: str) -> dict | None:
    ficha_id = detect_ficha_id(filename)
    if ficha_id is None:
        return None
    meta = INDICADORES.get(ficha_id, {})

    # Abrir el archivo UNA SOLA VEZ con ExcelFile + motor calamine (Rust, ~3.5x más rápido)
    # Antes: pd.read_excel() hasta 11 veces por archivo; ahora: 1 apertura, N parses directos
    try:
        file.seek(0)
        xl = pd.ExcelFile(file, engine='calamine')
        sheets_set = set(xl.sheet_names)
    except Exception:
        # Fallback a openpyxl si calamine no está disponible
        try:
            file.seek(0)
            xl = pd.ExcelFile(file, engine='openpyxl')
            sheets_set = set(xl.sheet_names)
        except Exception:
            return None

    # Leer Hoja1 para extraer logro y título
    try:
        if 'Hoja1' in sheets_set:
            hoja1 = xl.parse('Hoja1', header=None)
            logro = extract_logro(hoja1)
            titulo_raw = str(hoja1.iloc[0, 0])
            titulo = re.sub(r'^Ficha\s*(N[°º]?\s*)?\d+[:\.\-]?\s*', '', titulo_raw,
                            flags=re.IGNORECASE).strip()[:80]
        else:
            raise ValueError('sin Hoja1')
    except Exception:
        logro = None
        titulo = meta.get('nombre', f'Indicador {ficha_id}')

    # Encontrar la hoja de datos: lookup O(1) contra el set, sin reabrir el archivo
    _SHEET_CANDIDATES = ['sheet1', 'Sheet1', 'SHEET1', 'Hoja2', 'hoja2',
                         'datos', 'Datos', 'DATOS', 'data', 'Data']
    df = None
    for _sheet in _SHEET_CANDIDATES:
        if _sheet in sheets_set:          # solo parsea si la hoja existe
            try:
                df = xl.parse(_sheet)
                break
            except Exception:
                continue

    if df is None:
        # Fallback: iterar todas las hojas que no sean Hoja1
        otras = [s for s in xl.sheet_names if s != 'Hoja1']
        for sheet in otras:
            try:
                df = xl.parse(sheet)
                break
            except Exception:
                continue
        if df is None:
            return None
    if logro is None:
        logro = meta.get('logro_default')

    # Filtro específico por ficha (ej. Ficha 32: solo filas 'Indicador A')
    sheet_filter = meta.get('sheet_filter')
    if sheet_filter:
        fcol, fval = sheet_filter.get('col'), sheet_filter.get('val')
        if fcol and fcol in df.columns:
            df = df[df[fcol] == fval].copy()

    df_norm = normalize_df(df, ficha_id)
    tipo      = meta.get('tipo', 'pct')   # 'pct' | 'promedio' | 'tasa'
    unidad    = meta.get('unidad', '%')   # '%' | 'hrs' | 'x10k'
    umbral    = meta.get('umbral', None)
    logro_tasa= meta.get('logro_tasa', None)

    # Para tipo='tasa': calcular % cumplimiento = (tasa-umbral)/(logro_tasa-umbral)
    # y usarlo como logro efectivo para el semaforo
    logro_efectivo = logro
    logro_str_efectivo = f'{logro*100:.0f}%' if logro else 'N/D'
    if tipo == 'tasa' and umbral is not None and logro_tasa is not None:
        # tasa total = num/den sobre todo el df
        d_total = int(df_norm['den'].sum())
        n_total = int(df_norm['num'].sum())
        tasa_total = n_total / d_total if d_total > 0 else 0
        pct_cumpl = min(1.0, max(0.0,
                        (tasa_total - umbral) / (logro_tasa - umbral)))
        # Guardamos en un campo extra del df para uso en mapas/graficos
        df_norm['_cumplimiento'] = pct_cumpl
        logro_efectivo     = 1.0          # logro = 100% cumplimiento
        logro_str_efectivo = f'Tasa {logro_tasa} (umbral {umbral})'

    return {
        'id':         ficha_id,
        'titulo':     titulo or meta.get('nombre', f'Indicador {ficha_id}'),
        'logro':      logro_efectivo,
        'logro_str':  logro_str_efectivo,
        'icono':      meta.get('icono', '📊'),
        'tipo':       tipo,
        'unidad':     unidad,
        'umbral':     umbral,
        'logro_tasa': logro_tasa,
        'df':         df_norm,
        'has_nombres': df_norm['nombres'].str.len().gt(0).any(),
        'has_numdoc':  df_norm['num_doc'].str.len().gt(0).any(),
        'has_red':     df_norm['red'].str.len().gt(0).any(),
        'has_eess':    df_norm['eess'].str.len().gt(0).any(),
    }
