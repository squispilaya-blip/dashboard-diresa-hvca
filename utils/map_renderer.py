"""
Colorea el mapa PNG de Huancavelica con flood-fill según avance del indicador.
"""
import io
import os
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import numpy as np

MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'mapa_hvca.png')

# Puntos semilla por provincia — coordenadas px en imagen 827×1170
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
    'verde':    (45, 198, 83),    # #2DC653
    'amarillo': (255, 183, 3),    # #FFB703
    'rojo':     (230, 57, 70),    # #E63946
    'sin_data': (74, 85, 104),    # gris
}


def _load_font(size: int):
    for name in ['arialbd.ttf', 'arial.ttf', 'DejaVuSans-Bold.ttf',
                 'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/arial.ttf']:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _get_semaforo(pct: float, logro: float | None) -> str:
    if logro is None:
        return 'verde' if pct > 0 else 'rojo'
    ratio = pct / logro if logro > 0 else 0
    if ratio >= 1.0:
        return 'verde'
    if ratio >= 0.80:
        return 'amarillo'
    return 'rojo'


def _draw_badge(draw, cx, cy, text, font, rgb_color):
    try:
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
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


def render_map(df: pd.DataFrame, logro: float | None) -> bytes:
    """
    Genera mapa PNG con Redes/provincias coloreadas según % avance.
    df debe tener columnas: red, den, num
    Retorna bytes PNG.
    """
    img = Image.open(MAP_PATH).convert('RGBA')
    overlay = img.copy()

    # Agregar por red
    if df.empty or 'red' not in df.columns:
        data = {}
    else:
        agg = (df[df['red'].str.len() > 0]
               .groupby('red')
               .agg(den=('den', 'sum'), num=('num', 'sum'))
               .reset_index())
        agg['pct'] = np.where(agg['den'] > 0, agg['num'] / agg['den'], 0)
        data = {row['red'].upper(): row for _, row in agg.iterrows()}

    # Flood-fill cada provincia
    for prov, seeds in PROVINCE_SEEDS.items():
        row = data.get(prov)
        if row is not None:
            pct = float(row['pct'])
            estado = _get_semaforo(pct, logro)
        else:
            estado = 'sin_data'
        rgb = SEMAFORO_COLORS[estado]
        rgba = rgb + (185,)
        for seed in seeds:
            try:
                px = overlay.getpixel(seed)
                if px[0] > 50 or px[1] > 50 or px[2] > 50:
                    ImageDraw.floodfill(overlay, seed, rgba, thresh=80)
                    break
            except Exception:
                continue

    result = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(result)
    font = _load_font(20)

    # Badges de % por provincia
    for prov, pos in LABEL_POSITIONS.items():
        row = data.get(prov)
        if row is None:
            continue
        pct = float(row['pct'])
        estado = _get_semaforo(pct, logro)
        rgb = SEMAFORO_COLORS[estado]
        _draw_badge(draw, pos[0], pos[1], f'{pct*100:.0f}%', font, rgb)

    # Leyenda
    _draw_legend(draw, result.size[0], result.size[1], logro)

    buf = io.BytesIO()
    result.convert('RGB').save(buf, format='PNG', dpi=(120, 120))
    buf.seek(0)
    return buf.getvalue()


def _draw_legend(draw, W, H, logro):
    logro_pct = logro * 100 if logro else 0
    items = [
        (SEMAFORO_COLORS['verde'],    'En Meta',        f'≥ {logro_pct:.0f}%'),
        (SEMAFORO_COLORS['amarillo'], 'Cerca de Meta',  f'≥ {logro_pct*0.8:.0f}%'),
        (SEMAFORO_COLORS['rojo'],     'Por Debajo',     f'< {logro_pct*0.8:.0f}%'),
    ]
    font_b = _load_font(16)
    font_s = _load_font(13)
    lx, ly = W - 215, H - 178
    pad, bw, bh = 10, 200, 160
    draw.rounded_rectangle([lx - pad, ly - pad, lx + bw, ly + bh],
                           radius=10, fill=(10, 15, 30, 215),
                           outline=(255, 255, 255, 55), width=1)
    draw.text((lx + 5, ly + 3), 'SEMÁFORO', font=font_b, fill=(150, 200, 255, 255))
    for i, (color, label, rango) in enumerate(items):
        iy = ly + 35 + i * 40
        draw.rounded_rectangle([lx + 4, iy, lx + 26, iy + 22], radius=5,
                                fill=color + (230,))
        draw.text((lx + 34, iy + 2), label, font=font_b, fill=(255, 255, 255, 255))
        draw.text((lx + 34, iy + 20), rango, font=font_s, fill=(170, 170, 170, 210))
