import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

st.set_page_config(page_title='Pacientes Pendientes', page_icon='👥', layout='wide')

def _css():
    p = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
    if os.path.exists(p):
        with open(p) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
_css()

st.markdown("""<div class="header-diresa">
  <div><h1>👥 Pacientes Pendientes</h1>
  <p>Ahora integrado en la página de Detalle — tab "Pacientes Pendientes"</p></div>
</div>""", unsafe_allow_html=True)

st.info("""
**Esta función ahora está integrada directamente en la página de Detalle.**

Para buscar pacientes pendientes:
1. Ve a **📋 Detalle por Indicador** en el menú lateral
2. Selecciona el indicador (Ficha 01, 02, 03, etc.)
3. Haz clic en la pestaña **👥 Pacientes Pendientes**
4. Usa el buscador por DNI o Nombre
5. Filtra por Red → Microred → Establecimiento
""")

if st.button('📋 Ir a Detalle por Indicador', use_container_width=False):
    st.switch_page('pages/02_Detalle.py')
