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


def _find_col(df: pd.DataFrame, standard: str) -> str | None:
    candidates = COLUMN_MAP.get(standard, [])
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def normalize_df(df: pd.DataFrame, ficha_id: str) -> pd.DataFrame:
    out = {}
    for std in COLUMN_MAP:
        found = _find_col(df, std)
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
    try:
        hoja1 = pd.read_excel(file, sheet_name='Hoja1', header=None)
        logro = extract_logro(hoja1)
        titulo_raw = str(hoja1.iloc[0, 0])
        titulo = re.sub(r'^Ficha\s*(N[°º]?\s*)?\d+[:\.\-]?\s*', '', titulo_raw,
                        flags=re.IGNORECASE).strip()[:80]
    except Exception:
        logro = None
        titulo = meta.get('nombre', f'Indicador {ficha_id}')
    # CRITICAL-2: intentar varios nombres de hoja de datos
    _SHEET_CANDIDATES = ['sheet1', 'Sheet1', 'SHEET1', 'Hoja2', 'hoja2',
                         'datos', 'Datos', 'DATOS', 'data', 'Data']
    df = None
    for _sheet in _SHEET_CANDIDATES:
        try:
            file.seek(0)
            df = pd.read_excel(file, sheet_name=_sheet)
            break
        except Exception:
            continue
    if df is None:
        # último recurso: leer la segunda hoja por índice
        try:
            file.seek(0)
            df = pd.read_excel(file, sheet_name=1)
        except Exception:
            return None
    if logro is None:
        logro = meta.get('logro_default')
    df_norm = normalize_df(df, ficha_id)
    tipo   = meta.get('tipo', 'pct')      # 'pct' | 'promedio' | 'tasa'
    unidad = meta.get('unidad', '%')      # '%' | 'hrs' | etc.
    return {
        'id':         ficha_id,
        'titulo':     titulo or meta.get('nombre', f'Indicador {ficha_id}'),
        'logro':      logro,
        'logro_str':  f'{logro*100:.0f}%' if logro else 'N/D',
        'icono':      meta.get('icono', '📊'),
        'tipo':       tipo,
        'unidad':     unidad,
        'df':         df_norm,
        'has_nombres': df_norm['nombres'].str.len().gt(0).any(),
        'has_numdoc':  df_norm['num_doc'].str.len().gt(0).any(),
        'has_red':     df_norm['red'].str.len().gt(0).any(),
        'has_eess':    df_norm['eess'].str.len().gt(0).any(),
    }
