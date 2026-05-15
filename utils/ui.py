"""
Componentes de UI reutilizables — elimina el código duplicado entre páginas.

Antes: _css(), bloque sb-brand y botón logout repetidos en app.py,
       01_Resumen.py y 02_Detalle.py (3 copias de ~20 líneas c/u).
Ahora: una sola definición aquí; cada página llama a las funciones.
"""
import os
import streamlit as st
from utils.auth import do_logout


def load_css() -> None:
    """Inyecta assets/style.css en la página actual.

    Funciona tanto desde app.py como desde pages/* porque la ruta
    se calcula relativa a este archivo (utils/ui.py → ../assets/).
    Reemplaza la función _css() que estaba duplicada en los 3 archivos.
    """
    css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
    if os.path.exists(css_path):
        with open(css_path, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    """Logo DIRESA + enlaces de navegación + separador.

    Llamar dentro de «with st.sidebar:» al INICIO del bloque.
    Muestra el nombre del usuario autenticado desde session_state.
    """
    st.markdown(f'''<div class="sb-brand">
      <div style="font-size:2rem">🏥</div>
      <div class="sb-brand-name">DIRESA<br>HUANCAVELICA</div>
      <div class="sb-brand-sub">DL 1153 · 2026</div>
      <div class="sb-user">👤 {st.session_state.get("user_name", "")}</div>
    </div>''', unsafe_allow_html=True)

    st.markdown('<p class="sb-nav-title">NAVEGACIÓN</p>', unsafe_allow_html=True)
    st.page_link('app.py',              label='🏠 Inicio / Carga')
    st.page_link('pages/01_Resumen.py', label='📊 Resumen General')
    st.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)


def render_sidebar_logout() -> None:
    """Separador + botón de cierre de sesión.

    Llamar dentro de «with st.sidebar:» al FINAL del bloque.
    Al pulsar, limpia session_state y redirige a app.py (pantalla de login).
    """
    st.markdown('<div class="sb-sep"></div>', unsafe_allow_html=True)
    if st.button('🚪 Cerrar sesión', use_container_width=True):
        do_logout()
        st.switch_page('app.py')
