
from datetime import datetime
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.loader import get_semaforo_color
from utils.charts import kpi_card_html
from utils.map_renderer import render_map
from utils.constants import EXCLUIR_OPCIONES

st.set_page_config(page_title='Resumen General', page_icon='📊', layout='wide')

def _css():
    p = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
    if os.path.exists(p):
        with open(p) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
_css()

if not st.session_state.get('fichas'):
    st.warning('⚠️ Primero carga los archivos Excel en la página de Inicio.')
    st.stop()

fichas = st.session_state.fichas

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('''<div style="text-align:center;padding:10px 0 14px 0;
        border-bottom:1px solid rgba(255,255,255,0.18);margin-bottom:14px">
      <div style="font-size:2.2rem">🏥</div>
      <div style="color:white;font-weight:800;font-size:0.95rem;line-height:1.3">
        DIRESA<br>HUANCAVELICA</div>
      <div style="color:rgba(255,255,255,0.55);font-size:0.6rem;margin-top:3px">
        DL 1153 · 2026</div>
    </div>''', unsafe_allow_html=True)
    st.markdown('### 🌐 Filtro de Red')
    redes_disp = sorted({r for f in fichas.values()
                         for r in f['df']['red'].unique()
                         if r and len(r) > 1 and r.upper() not in EXCLUIR_OPCIONES})
    red_filtro = st.selectbox('Red de Salud / Provincia',
                              ['Todas'] + redes_disp)

    st.markdown('---')
    st.markdown('### 🗺️ Indicador en el mapa')
    ids = sorted(fichas.keys())
    ind_mapa = st.selectbox(
        'Ver en el mapa:',
        ids,
        format_func=lambda x: f'{fichas[x]["icono"]} ID {x} — {fichas[x]["titulo"][:28]}',
    )


def filtrar(df):
    if red_filtro == 'Todas':
        return df.copy()
    return df[df['red'] == red_filtro].copy()


# ── Header con EN VIVO ────────────────────────────────────────────────────────
now = datetime.now()
fecha_txt = now.strftime('%d/%m/%Y %H:%M:%S')

st.markdown(f"""<div class="header-diresa">
  <div style="flex:1">
    <h1>📊 Resumen General — 16 Indicadores DL 1153</h1>
    <p>DIRESA Huancavelica &nbsp;·&nbsp; Haz clic en cualquier tarjeta para ver el detalle completo</p>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px">
    <span class="en-vivo-badge"><span class="en-vivo-dot"></span>&nbsp;EN VIVO &nbsp;·&nbsp; {fecha_txt}</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── Conteo de semáforo por indicador ─────────────────────────────────────────
total = len(fichas)
verdes, amarillos = 0, 0
for fid, f in fichas.items():
    df_f = filtrar(f['df'])
    d = int(df_f['den'].sum())
    n = int(df_f['num'].sum())
    color = get_semaforo_color(n / d if d > 0 else 0, f.get('logro'))
    if color == 'verde':
        verdes += 1
    elif color == 'amarillo':
        amarillos += 1
rojos = total - verdes - amarillos

m1, m2, m3, m4 = st.columns(4)
m1.metric('Indicadores cargados', total)
m2.metric('🟢 En meta', verdes)
m3.metric('🟡 Cerca de meta', amarillos)
m4.metric('🔴 Por debajo', rojos)

# ── Columnas: Mapa PNG | Detalle del indicador ────────────────────────────────
col_mapa, col_kpi = st.columns([1, 1])

with col_mapa:
    st.markdown('<div class="seccion-titulo">🗺️ Mapa de Avance por Provincia / Red</div>',
                unsafe_allow_html=True)
    f_mapa = fichas[ind_mapa]
    df_mapa = filtrar(f_mapa['df'])
    try:
        img_bytes = render_map(df_mapa, f_mapa.get('logro'))
        st.markdown('<div class="mapa-container">', unsafe_allow_html=True)
        st.image(img_bytes, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.warning(f'No se pudo renderizar el mapa: {e}')

with col_kpi:
    st.markdown(f'<div class="seccion-titulo">📊 {f_mapa["icono"]} {f_mapa["titulo"][:40]}</div>',
                unsafe_allow_html=True)
    df_sel = df_mapa
    den_s = int(df_sel['den'].sum())
    num_s = int(df_sel['num'].sum())
    pct_s = num_s / den_s if den_s > 0 else 0
    color_s = get_semaforo_color(pct_s, f_mapa.get('logro'))
    emoji_s = '🟢' if color_s == 'verde' else ('🟡' if color_s == 'amarillo' else '🔴')
    estado_lbl = 'En Meta' if color_s == 'verde' else ('Cerca de Meta' if color_s == 'amarillo' else 'Por Debajo')

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric('Denominador', f'{den_s:,}')
    mc2.metric('Numerador',   f'{num_s:,}')
    mc3.metric('% Avance',    f'{pct_s*100:.1f}%')
    mc4, mc5, mc6 = st.columns(3)
    mc4.metric('Pendientes',  f'{max(0, den_s - num_s):,}')
    mc5.metric('Meta',        f_mapa.get('logro_str', 'N/D'))
    mc6.metric('Estado', emoji_s, estado_lbl)

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button('📋 Ver análisis completo', key='btn_mapa_detail', use_container_width=True):
        st.session_state.selected_ficha = ind_mapa
        st.switch_page('pages/02_Detalle.py')

# ── 16 KPI Cards ──────────────────────────────────────────────────────────────
st.markdown('<div class="seccion-titulo">🎯 Todos los Indicadores — Haz clic para ver detalle</div>',
            unsafe_allow_html=True)
ids = sorted(fichas.keys())
for i in range(0, len(ids), 4):
    cols = st.columns(4)
    for j, fid in enumerate(ids[i:i+4]):
        f = fichas[fid]
        df_f = filtrar(f['df'])
        den = int(df_f['den'].sum())
        num = int(df_f['num'].sum())
        pct = num / den if den > 0 else 0
        color = get_semaforo_color(pct, f.get('logro'))
        with cols[j]:
            st.markdown(
                kpi_card_html(f['icono'], f['titulo'][:34], pct, f.get('logro'), color,
                              tipo=f.get('tipo', 'pct'), unidad=f.get('unidad', '%')),
                unsafe_allow_html=True,
            )
            if st.button(f'📋 Ver detalle', key=f'btn_{fid}', use_container_width=True):
                st.session_state.selected_ficha = fid
                st.switch_page('pages/02_Detalle.py')
