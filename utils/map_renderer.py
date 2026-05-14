"""
Colorea el mapa PNG de Huancavelica con flood-fill según avance del indicador.
"""
import io
import os
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import numpy as np

MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'mapa_hvca.png')
EXPECTED_W, EXPECTED_H = 827, 1170   # CRITICAL-3: guard de resolución

# CRITICAL-5 corregido: COLCABAMBA pertenece a TAYACAJA (eliminada entrada duplicada de CASTROVIRREYNA)
MICRORED_TO_PROVINCE = {
    'ACOBAMBA':              'ACOBAMBA',
    'SAN ISIDRO DE ACOBAMBA': 'ACOBAMBA',
    'ANGARAES':              'ANGARAES',
    'LIRCAY':                'ANGARAES',
    'CCOCHACCASA':           'ANGARAES',
    'SECCLLA':               'ANGARAES',
    'CASTROVIRREYNA':        'CASTROVIRREYNA',
    'CORDOVA':               'CASTROVIRREYNA',
    'HUACHOS':               'CASTROVIRREYNA',
    'MOYA':                  'CASTROVIRREYNA',
    'SANTA ANA':             'CASTROVIRREYNA',
    'SANTIAGO DE CHOCORVOS': 'CASTROVIRREYNA',
    'TANTARA':               'CASTROVIRREYNA',
    'CHURCAMPA':             'CHURCAMPA',
    'PAUCARBAMBA':           'CHURCAMPA',
    'HUANCAVELICA':          'HUANCAVELICA',
    'ACORIA':                'HUANCAVELICA',
    'ACOSTAMBO':             'HUANCAVELICA',
    'ASCENSION':             'HUANCAVELICA',
    'AYACCOCHA':             'HUANCAVELICA',
    'DANIEL HERNANDEZ':      'HUANCAVELICA',
    'HUANDO':                'HUANCAVELICA',
    'IZCUCHACA':             'HUANCAVELICA',
    'PAUCARA':               'HUANCAVELICA',
    'PILPICHACA':            'HUANCAVELICA',
    'YAULI':                 'HUANCAVELICA',
    'HUAYTARA':              'HUAYTARA',
    'PAZOS':                 'HUAYTARA',
    'SURCUBAMBA':            'HUAYTARA',
    'TAYACAJA':              'TAYACAJA',
    'ACRAQUIA':              'TAYACAJA',
    'SALCAHUASI':            'TAYACAJA',
    'HUARIBAMBA':            'TAYACAJA',
    'PAMPAS':                'TAYACAJA',
    'COLCABAMBA':            'TAYACAJA',   # único — distrito de Tayacaja
}

PROVINCE_SEEDS = {
    'TAYACAJA':       [(530, 180), (480, 140), (600, 200)],
    'CHURCAMPA':      [(630, 335), (660, 345)],
    'ACOBAMBA':       [(575, 450), (600, 430)],
    'HUANCAVELICA':   [(330, 430), (360, 380), (300, 500)],
    'ANGARAES':       [(540, 580), (560, 600), (520, 550)],
    'CASTROVIRREYNA': [(190, 630), (160, 600), (220, 660)],
    'HUAYTARA':       [(420, 820), (380, 800), (450, 850)],
}

LABEL_POSITIONS = {
    'TAYACAJA':       (480, 188),
    'CHURCAMPA':      (614, 345),
    'ACOBAMBA':       (558, 448),
    'HUANCAVELICA':   (305, 435),
    'ANGARAES':       (524, 588),
    'CASTROVIRREYNA': (172, 638),
    'HUAYTARA':       (395, 825),
}

SEMAFORO_COLORS = {
    'verde':    (45, 198, 83),
    'amarillo': (255, 183, 3),
    'rojo':     (230, 57, 70),
    'sin_data': (74, 85, 104),
}

PROVINCIAS = ['ACOBAMBA', 'ANGARAES', 'CASTROVIRREYNA', 'CHURCAMPA',
              'HUANCAVELICA', 'HUAYTARA', 'TAYACAJA']


def _load_font(size: int):
    # MINOR-2: rutas Linux para Streamlit Cloud + Windows
    candidates = [
        'arialbd.ttf', 'arial.ttf', 'DejaVuSans-Bold.ttf',
        'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _get_semaforo(pct: float, logro: float | None) -> str:
    if logro is None:
        return 'verde' if pct > 0 else 'rojo'
    ratio = pct / logro if logro > 0 else 0
    if ratio >= 1.0:   return 'verde'
    if ratio >= 0.80:  return 'amarillo'
    return 'rojo'


def _draw_badge(draw, cx, cy, text, font, rgb_color):
    try:
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = len(text) * 10, 16
    px, py = 9, 4
    w, h = tw + px * 2, th + py * 2
    x0, y0 = cx - w // 2, cy - h // 2
    darker = tuple(max(0, c - 50) for c in rgb_color)
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=6,
                            fill=darker + (220,), outline=(255, 255, 255, 160), width=1)
    tc = (30, 20, 0) if rgb_color == SEMAFORO_COLORS['amarillo'] else (255, 255, 255)
    draw.text((cx, cy), text, font=font, fill=tc + (255,), anchor='mm')


def _microred_to_provincia(nombre: str) -> str | None:
    nombre = nombre.upper().strip()
    if nombre in MICRORED_TO_PROVINCE:
        return MICRORED_TO_PROVINCE[nombre]
    if nombre in PROVINCIAS:
        return nombre
    for prov in PROVINCIAS:
        if prov in nombre or nombre in prov:
            return prov
    keywords = {
        'ACOBAMBA':       ['SAN ISIDRO'],
        'ANGARAES':       ['LIRCAY', 'CCOCHACCASA', 'SECCLLA'],
        'CASTROVIRREYNA': ['CORDOVA', 'HUACHOS', 'TANTARA', 'CHOCORVOS'],
        'CHURCAMPA':      ['PAUCARBAMBA'],
        'HUANCAVELICA':   ['ACORIA', 'ACOSTAMBO', 'ASCENSION', 'AYACCOCHA',
                           'DANIEL', 'HUANDO', 'IZCUCHACA', 'PAUCARA',
                           'PILPICHACA', 'YAULI'],
        'HUAYTARA':       ['PAZOS', 'SURCUBAMBA'],
        'TAYACAJA':       ['ACRAQUIA', 'SALCAHUASI', 'HUARIBAMBA', 'PAMPAS',
                           'COLCABAMBA'],
    }
    for prov, kws in keywords.items():
        if any(kw in nombre for kw in kws):
            return prov
    return None


def _agrupar_por_provincia(df: pd.DataFrame) -> dict:
    """CRITICAL-4: vectorizado con groupby+map en lugar de iterrows."""
    prov_data = {p: {'den': 0, 'num': 0, 'pct': 0.0} for p in PROVINCIAS}

    if df.empty or 'red' not in df.columns:
        return prov_data
    if not df['red'].str.len().gt(0).any():
        return prov_data

    df2 = df[df['red'].str.len() > 0].copy()
    df2['_prov'] = df2['red'].map(_microred_to_provincia)
    df2 = df2[df2['_prov'].notna()]

    if df2.empty:
        return prov_data

    agg = (df2.groupby('_prov')
              .agg(den=('den', 'sum'), num=('num', 'sum'))
              .reset_index())

    for _, row in agg.iterrows():
        p = row['_prov']
        if p in prov_data:
            d, n = int(row['den']), int(row['num'])
            prov_data[p] = {'den': d, 'num': n, 'pct': n / d if d > 0 else 0.0}

    return prov_data


@st.cache_data(max_entries=20, show_spinner=False)   # CRITICAL-1: cache PIL flood-fill
def render_map(df: pd.DataFrame, logro: float | None) -> bytes:
    """
    Genera mapa PNG con provincias coloreadas según % avance.
    Retorna bytes PNG.
    """
    img = Image.open(MAP_PATH).convert('RGBA')

    # CRITICAL-3: guard de resolución
    if img.size != (EXPECTED_W, EXPECTED_H):
        raise ValueError(
            f"mapa_hvca.png es {img.size}, se esperaba ({EXPECTED_W}, {EXPECTED_H}). "
            "Actualiza PROVINCE_SEEDS y LABEL_POSITIONS si cambiaste la imagen."
        )

    overlay = img.copy()
    prov_data = _agrupar_por_provincia(df)

    for prov, seeds in PROVINCE_SEEDS.items():
        pdata = prov_data.get(prov, {})
        if pdata and pdata.get('den', 0) > 0:
            estado = _get_semaforo(float(pdata['pct']), logro)
        else:
            estado = 'sin_data'
        rgba = SEMAFORO_COLORS[estado] + (185,)

        coloreado = False
        for seed in seeds:
            try:
                px = overlay.getpixel(seed)
                if (px[0] + px[1] + px[2]) / 3 > 60:
                    ImageDraw.floodfill(overlay, seed, rgba, thresh=80)
                    coloreado = True
                    break
            except Exception:
                continue

        if not coloreado:
            for seed in seeds:
                sx, sy = seed
                for dx in range(-20, 21, 5):
                    for dy in range(-20, 21, 5):
                        try:
                            px = overlay.getpixel((sx + dx, sy + dy))
                            if (px[0] + px[1] + px[2]) / 3 > 60:
                                ImageDraw.floodfill(overlay, (sx + dx, sy + dy), rgba, thresh=80)
                                coloreado = True
                                break
                        except Exception:
                            continue
                    if coloreado:
                        break
                if coloreado:
                    break

    result = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(result)
    font = _load_font(20)

    for prov, pos in LABEL_POSITIONS.items():
        pdata = prov_data.get(prov, {})
        if pdata and pdata.get('den', 0) > 0:
            pct = float(pdata['pct'])
            estado = _get_semaforo(pct, logro)
            _draw_badge(draw, pos[0], pos[1], f'{pct*100:.0f}%', font,
                        SEMAFORO_COLORS[estado])

    _draw_legend(draw, result.size[0], result.size[1], logro)

    buf = io.BytesIO()
    result.convert('RGB').save(buf, format='PNG', dpi=(120, 120))
    buf.seek(0)
    return buf.getvalue()


def _draw_legend(draw, W, H, logro):
    logro_pct = logro * 100 if logro else 0
    items = [
        (SEMAFORO_COLORS['verde'],    'En Meta',       f'>= {logro_pct:.0f}%'),
        (SEMAFORO_COLORS['amarillo'], 'Cerca de Meta', f'>= {logro_pct*0.8:.0f}%'),
        (SEMAFORO_COLORS['rojo'],     'Por Debajo',    f'< {logro_pct*0.8:.0f}%'),
    ]
    font_b = _load_font(16)
    font_s = _load_font(13)
    lx, ly = W - 215, H - 178
    draw.rounded_rectangle([lx - 10, ly - 10, lx + 200, ly + 160],
                           radius=10, fill=(10, 15, 30, 215),
                           outline=(255, 255, 255, 55), width=1)
    draw.text((lx + 5, ly + 3), 'SEMAFORO', font=font_b, fill=(150, 200, 255, 255))
    for i, (color, label, rango) in enumerate(items):
        iy = ly + 35 + i * 40
        draw.rounded_rectangle([lx + 4, iy, lx + 26, iy + 22], radius=5,
                                fill=color + (230,))
        draw.text((lx + 34, iy + 2),  label, font=font_b, fill=(255, 255, 255, 255))
        draw.text((lx + 34, iy + 20), rango, font=font_s, fill=(170, 170, 170, 210))
