from datetime import datetime
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.loader import get_semaforo_color
from utils.charts import kpi_card_html
from utils.constants import EXCLUIR_OPCIONES
from utils.auth import require_auth
from utils.ui import load_css, render_sidebar_brand, render_sidebar_logout

st.set_page_config(page_title='Resumen General', page_icon='📊', layout='wide')
load_css()

require_auth()

fichas     = st.session_state.get('fichas', {})
red_filtro = 'Todas'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand()

    if fichas:
        st.markdown('<p class="sb-section-title">🌐 FILTRO DE RED</p>',
                    unsafe_allow_html=True)
        redes_disp = sorted({r for f in fichas.values()
                             for r in f['df']['red'].unique()
                             if r and len(r) > 1 and r.upper() not in EXCLUIR_OPCIONES})
        red_filtro = st.selectbox('Red de Salud / Provincia',
                                  ['Todas'] + redes_disp,
                                  label_visibility='collapsed')

    render_sidebar_logout()

# ── Guardia: sin fichas cargadas ──────────────────────────────────────────────
if not fichas:
    st.warning('⚠️ Primero carga los archivos Excel en la página de Inicio.')
    st.stop()


def filtrar(df):
    if red_filtro == 'Todas':
        return df
    return df[df['red'] == red_filtro]


filtered_dfs = {fid: filtrar(f['df']) for fid, f in fichas.items()}

# ── Header ────────────────────────────────────────────────────────────────────
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

# ── Semáforo global ───────────────────────────────────────────────────────────
total = len(fichas)
verdes, amarillos = 0, 0
for fid, f in fichas.items():
    df_f = filtered_dfs[fid]
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

# ── 16 KPI Cards ──────────────────────────────────────────────────────────────
st.markdown('<div class="seccion-titulo">🎯 Todos los Indicadores — Haz clic para ver detalle</div>',
            unsafe_allow_html=True)
ids = sorted(fichas.keys())
for i in range(0, len(ids), 4):
    cols = st.columns(4)
    for j, fid in enumerate(ids[i:i+4]):
        f    = fichas[fid]
        df_f = filtered_dfs[fid]
        den  = int(df_f['den'].sum())
        num  = int(df_f['num'].sum())
        pct  = num / den if den > 0 else 0
        color = get_semaforo_color(pct, f.get('logro'))
        with cols[j]:
            st.markdown(
                kpi_card_html(f['icono'], f['titulo'][:60], pct, f.get('logro'), color,
                              tipo=f.get('tipo', 'pct'), unidad=f.get('unidad', '%'),
                              titulo_full=f['titulo']),
                unsafe_allow_html=True,
            )
            if st.button(f'📋 Ver detalle', key=f'btn_{fid}', use_container_width=True):
                st.session_state.selected_ficha = fid
                st.switch_page('pages/02_Detalle.py')
