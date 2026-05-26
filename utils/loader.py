import io
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
    # Columnas de texto → limpiar y convertir a MAYÚSCULAS
    for col in ['red', 'microred', 'eess', 'provincia', 'nombres', 'num_doc',
                'genero', 'seguro', 'categoria']:
        s = result[col].fillna('').astype(str).str.strip().str.upper()
        result[col] = s.where(~s.isin(_NAN_VALS), '')
    # Columnas de fecha → conservar formato original (no mayúsculas)
    for col in ['fecha_nac', 'fecha_dx']:
        s = result[col].fillna('').astype(str).str.strip()
        # Convertir timestamps "2026-01-15 00:00:00" → "2026-01-15"
        s = s.str.replace(r'\s+00:00:00$', '', regex=True)
        result[col] = s.where(~s.str.upper().isin(_NAN_VALS), '')
    # Edad → número entero como cadena (quitar ".0" de float)
    s = result['edad'].fillna('').astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    result['edad'] = s.where(~s.isin(_NAN_VALS), '')
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


def _load_ficha_16_vph(xl, meta: dict) -> dict | None:
    """Loader especial para Ficha 16 (VPH) — lee la hoja COMPARATIVO del monitoreo diario.

    Estructura del archivo: hoja '26 MAY (COMPARATIVO)' (o la más reciente con 'COMPARATIVO').
    Sección VPH: col0=RIS, col4=META 9años, col5=DU 9años, col7=META 10-18años, col8=DU 10-18años.
    """
    comp_sheet = None
    for sh in reversed(xl.sheet_names):
        if 'COMPARATIVO' in sh.upper():
            comp_sheet = sh
            break
    if comp_sheet is None:
        return None

    df_raw = xl.parse(comp_sheet, header=None)

    # Detectar dinámicamente la fila de cabecera de la sección VPH buscando 'RIS' en col0
    # y '9' o 'VPH' en la misma fila
    header_row = None
    for i in range(len(df_raw)):
        val0 = str(df_raw.iloc[i, 0]).strip().upper()
        row_str = ' '.join(str(v) for v in df_raw.iloc[i].tolist())
        if val0 == 'RIS' and 'VPH' in row_str:
            header_row = i
            break
    if header_row is None:
        return None

    # Columnas VPH: determinadas por encabezados en header_row+1 / header_row+2
    # Buscar las columnas META de '9 AÑOS' y '10 A 18 AÑOS' en las filas siguientes
    col_meta9, col_meta18 = None, None
    for check_row in range(header_row + 1, min(header_row + 4, len(df_raw))):
        row_vals = [str(v).strip() for v in df_raw.iloc[check_row].tolist()]
        for j, v in enumerate(row_vals):
            if '9' in v and 'O' in v.upper() and col_meta9 is None:
                # Encontrar el META que precede a la columna '9 AÑOS'
                # Buscar 'META' antes de este índice
                for k in range(j - 1, max(j - 3, -1), -1):
                    if 'META' in str(df_raw.iloc[check_row, k]).upper():
                        col_meta9 = k
                        break
                if col_meta9 is None:
                    col_meta9 = j - 1  # fallback: columna anterior es META
            if '10' in v and '18' in v and col_meta18 is None:
                for k in range(j - 1, max(j - 3, -1), -1):
                    if 'META' in str(df_raw.iloc[check_row, k]).upper():
                        col_meta18 = k
                        break
                if col_meta18 is None:
                    col_meta18 = j - 1
        if col_meta9 is not None and col_meta18 is not None:
            break

    # Valores por defecto confirmados empíricamente si la detección falla
    if col_meta9 is None:
        col_meta9 = 4
    if col_meta18 is None:
        col_meta18 = 7

    col_du9  = col_meta9  + 1
    col_du18 = col_meta18 + 1

    _SKIP = {'ESSALUD', 'ESSALUD ', 'DIRESA', 'HUANCAVELICA'}
    rows = []
    for i in range(header_row + 3, len(df_raw)):
        r = df_raw.iloc[i].tolist()
        if not isinstance(r[0], str):
            continue
        red = str(r[0]).strip().upper()
        if not red or red in _SKIP:
            continue
        try:
            m9  = int(r[col_meta9])
            du9 = int(r[col_du9])
            m18 = int(r[col_meta18])
            du18= int(r[col_du18])
        except (ValueError, TypeError, IndexError):
            continue
        # Normalizar nombres de Red al formato TITLE CASE
        red_fmt = red.title()
        rows.append({'red': red_fmt, 'den': m9,  'num': du9,  'categoria': '9 AÑOS',    'año': 2026, 'mes': 5})
        rows.append({'red': red_fmt, 'den': m18, 'num': du18, 'categoria': '10-18 AÑOS','año': 2026, 'mes': 5})

    if not rows:
        return None

    df_norm = pd.DataFrame(rows)
    for col in ['microred', 'eess', 'provincia', 'nombres', 'num_doc',
                'genero', 'seguro', 'fecha_nac', 'fecha_dx', 'edad']:
        df_norm[col] = ''
    df_norm['pct'] = np.where(df_norm['den'] > 0, df_norm['num'] / df_norm['den'], 0.0)
    df_norm['ficha_id'] = '16'

    logro = meta.get('logro_default', 0.90)

    return {
        'id':         '16',
        'titulo':     meta.get('nombre', 'Vacunación VPH'),
        'logro':      logro,
        'logro_str':  f'{logro*100:.0f}%',
        'icono':      meta.get('icono', '💉'),
        'tipo':       'pct',
        'unidad':     '%',
        'umbral':     None,
        'logro_tasa': None,
        'df':         df_norm,
        'has_nombres':   False,
        'has_numdoc':    False,
        'has_red':       True,
        'has_eess':      False,
        'has_fecha_nac': False,
        'has_fecha_dx':  False,
        'has_genero':    False,
        'has_seguro':    False,
        'has_categoria': True,
        'has_edad':      False,
        'sub_grupos': [
            {'titulo': 'VPH — Niñas/os 9 años',         'categoria': '9 AÑOS',    'logro': logro},
            {'titulo': 'VPH — Adolescentes 10-18 años',  'categoria': '10-18 AÑOS','logro': logro},
        ],
    }


def load_ficha(file, filename: str) -> dict | None:
    ficha_id = detect_ficha_id(filename)
    if ficha_id is None:
        return None
    meta = INDICADORES.get(ficha_id, {})

    # Abrir el archivo UNA SOLA VEZ con ExcelFile + motor calamine (Rust, ~3.5x más rápido)
    # (también usado por el loader especial de Ficha 16)
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

    # Ficha 16 tiene formato especial (monitoreo diario vacunación)
    if ficha_id == '16':
        return _load_ficha_16_vph(xl, meta)

    # Leer Hoja1 para extraer logro y título
    try:
        if 'Hoja1' in sheets_set:
            hoja1 = xl.parse('Hoja1', header=None)
            logro = extract_logro(hoja1)
            titulo_raw = str(hoja1.iloc[0, 0])
            titulo = re.sub(r'^Ficha\s*(N[°º]?\s*)?\d+[:\.\-]?\s*', '', titulo_raw,
                            flags=re.IGNORECASE).strip()
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

    # Filtrar solo MINSA si la columna seguro tiene valores (DL 1153 solo MINSA)
    if df_norm['seguro'].str.len().gt(0).any():
        minsa_mask = df_norm['seguro'] == 'MINSA'
        if minsa_mask.any():
            df_norm = df_norm[minsa_mask].reset_index(drop=True)

    # Si no hay columna Red pero sí hay Provincia, usar Provincia como Red
    # (aplica a Ficha 19 donde el nivel de análisis es provincia)
    if not df_norm['red'].str.len().gt(0).any():
        if df_norm['provincia'].str.len().gt(0).any():
            df_norm['red'] = df_norm['provincia']

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
        'titulo':     meta.get('nombre') or titulo or f'Indicador {ficha_id}',
        'logro':      logro_efectivo,
        'logro_str':  logro_str_efectivo,
        'icono':      meta.get('icono', '📊'),
        'tipo':       tipo,
        'unidad':     unidad,
        'umbral':     umbral,
        'logro_tasa': logro_tasa,
        'df':         df_norm,
        'has_nombres':   df_norm['nombres'].str.len().gt(0).any(),
        'has_numdoc':    df_norm['num_doc'].str.len().gt(0).any(),
        'has_red':       df_norm['red'].str.len().gt(0).any(),
        'has_eess':      df_norm['eess'].str.len().gt(0).any(),
        # Columnas clínicas adicionales
        'has_fecha_nac': df_norm['fecha_nac'].str.len().gt(0).any(),
        'has_fecha_dx':  df_norm['fecha_dx'].str.len().gt(0).any(),
        'has_genero':    df_norm['genero'].str.len().gt(0).any(),
        'has_seguro':    df_norm['seguro'].str.len().gt(0).any(),
        'has_categoria': df_norm['categoria'].str.len().gt(0).any(),
        'has_edad':      df_norm['edad'].str.len().gt(0).any(),
    }


def load_ficha_bytes(file_bytes: bytes, filename: str) -> dict | None:
    """Versión thread-safe de load_ficha: acepta bytes en lugar de un objeto file.

    Cada hilo crea su propio BytesIO, así que no hay condición de carrera.
    Úsala con ThreadPoolExecutor para carga paralela de múltiples fichas.
    """
    return load_ficha(io.BytesIO(file_bytes), filename)
