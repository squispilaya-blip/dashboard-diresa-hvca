import streamlit as st
import pandas as pd
import os
from utils.loader import load_ficha, get_semaforo_color

st.set_page_config(
    page_title='Dashboard DIRESA Huancavelica',
    page_icon='🏥',
    layout='wide',
    initial_sidebar_state='expanded',
)

def _css():
    p = os.path.join(os.path.dirname(__file__), 'assets', 'style.css')
    if os.path.exists(p):
        with open(p) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

_css()

st.markdown("""
<div class="header-diresa">
  <div>
    <h1>🏥 DIRESA Huancavelica</h1>
    <p>Sistema de Monitoreo de Indicadores de Desempeño &nbsp;·&nbsp; D.L. 1153 &nbsp;·&nbsp; 2026</p>
  </div>
</div>
""", unsafe_allow_html=True)

if 'fichas' not in st.session_state:
    st.session_state.fichas = {}

st.markdown('<div class="seccion-titulo">📤 Carga de Indicadores</div>', unsafe_allow_html=True)

c_info, c_up = st.columns([1, 2])
with c_info:
    st.info("""
**¿Cómo actualizar el dashboard?**
1. Recibe los nuevos Excel de MINSA cada mes
2. Cárgalos aquí — reemplazan los anteriores
3. ¡El dashboard se actualiza automáticamente!

Puedes cargar múltiples archivos a la vez.
""")
with c_up:
    uploaded = st.file_uploader(
        'Selecciona las fichas Excel (Ficha_01, Ficha_02 … Ficha_32)',
        type=['xlsx'],
        accept_multiple_files=True,
        help='Arrastra aquí los archivos Excel de indicadores DL 1153 2026',
    )

if uploaded:
    nuevas, errores = 0, []
    with st.spinner('Procesando archivos...'):
        for f in uploaded:
            result = load_ficha(f, f.name)
            if result:
                st.session_state.fichas[result['id']] = result
                nuevas += 1
            else:
                errores.append(f.name)
    if nuevas:
        st.success(f'✅ {nuevas} indicador(es) cargados correctamente.')
    if errores:
        st.warning(f'⚠️ No reconocidos (sin "Ficha_NN" en el nombre): {", ".join(errores)}')

if st.session_state.fichas:
    st.markdown('<div class="seccion-titulo">📋 Indicadores Cargados</div>', unsafe_allow_html=True)
    rows = []
    for fid, f in sorted(st.session_state.fichas.items()):
        df = f['df']
        den = int(df['den'].sum())
        num = int(df['num'].sum())
        pct = num / den if den > 0 else 0
        color = get_semaforo_color(pct, f.get('logro'))
        emoji = '🟢' if color == 'verde' else ('🟡' if color == 'amarillo' else '🔴')
        rows.append({
            'ID': fid,
            'Indicador': f'{f["icono"]} {f["titulo"][:52]}',
            'Meta': f['logro_str'],
            'Den.': f'{den:,}',
            'Num.': f'{num:,}',
            '% Avance': f'{pct*100:.1f}%',
            'Estado': emoji,
        })
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            'Estado':   st.column_config.TextColumn(width='small'),
            '% Avance': st.column_config.TextColumn(width='small'),
            'Meta':     st.column_config.TextColumn(width='small'),
        },
    )
    total  = len(st.session_state.fichas)
    verdes = sum(1 for r in rows if r['Estado'] == '🟢')
    rojos  = sum(1 for r in rows if r['Estado'] == '🔴')
    m1, m2, m3 = st.columns(3)
    m1.metric('Indicadores cargados', total)
    m2.metric('En meta o superando 🟢', verdes)
    m3.metric('Por debajo de meta 🔴', rojos)
    st.info('👈 Usa el menú lateral para navegar a Resumen, Detalle o Pendientes.')
else:
    st.markdown("""
<div style="text-align:center;padding:60px 20px;color:#8892a4;">
  <div style="font-size:4.5rem">📂</div>
  <h3 style="color:#E8EAF0;margin-top:12px;">Aún no has cargado ningún indicador</h3>
  <p>Sube los archivos Excel de las fichas DL 1153 2026 para comenzar</p>
</div>""", unsafe_allow_html=True)
