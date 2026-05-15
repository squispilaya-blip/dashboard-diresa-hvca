import hashlib
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
import pandas as pd
from utils.loader import load_ficha_bytes, get_semaforo_color
from utils.auth import (do_login, is_authenticated, is_admin,
                        list_users, add_user, delete_user)
from utils.ui import load_css, render_sidebar_brand, render_sidebar_logout

st.set_page_config(
    page_title='Dashboard DIRESA Huancavelica',
    page_icon='🏥',
    layout='wide',
    initial_sidebar_state='expanded',
)

load_css()


# ══════════════════════════════════════════════════════════════════
#  CACHÉ COMPARTIDA — UN SOLO CONJUNTO DE DATOS PARA TODOS
#  st.cache_resource crea un singleton en el servidor.
#  El admin lo puebla; todos los usuarios leen de aquí.
#  Resultado: N usuarios → misma RAM que 1 usuario.
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def _shared_fichas() -> dict:
    """Diccionario global de fichas. Compartido entre TODAS las sesiones."""
    return {}

@st.cache_resource
def _hash_cache() -> dict:
    """Cache MD5→ficha. Evita reprocesar el mismo Excel en el servidor."""
    return {}


# ══════════════════════════════════════════════════════════════════
#  PANTALLA DE LOGIN
# ══════════════════════════════════════════════════════════════════
if not is_authenticated():
    st.markdown("""
    <div style="display:flex;justify-content:center;margin-top:60px;">
      <div style="background:linear-gradient(135deg,#112240,#1a3460);
                  border-radius:20px;padding:48px 52px;width:420px;
                  box-shadow:0 12px 48px rgba(0,0,0,0.5);
                  border:1px solid rgba(255,255,255,0.1);">
        <div style="text-align:center;margin-bottom:28px;">
          <div style="font-size:3.2rem">🏥</div>
          <h2 style="color:#fff;font-weight:800;margin:8px 0 2px;font-size:1.35rem;">
            DIRESA Huancavelica</h2>
          <p style="color:rgba(255,255,255,0.5);font-size:0.78rem;margin:0;">
            Sistema de Monitoreo · DL 1153 · 2026</p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('login_error'):
        st.markdown("""
        <div style="background:rgba(230,57,70,0.15);border:1.5px solid #E63946;
                    border-radius:10px;padding:11px 16px;margin-bottom:14px;
                    color:#ff6b6b;font-size:0.85rem;text-align:center;">
            ❌ &nbsp; <b>Usuario o contraseña incorrectos.</b><br>
            <span style="font-size:0.78rem;opacity:0.85;">
              Verifica tus datos e intenta nuevamente.</span>
        </div>
        """, unsafe_allow_html=True)

    with st.form('login_form', clear_on_submit=False):
        usuario  = st.text_input('👤 Usuario', placeholder='Ingresa tu usuario')
        password = st.text_input('🔑 Contraseña', type='password',
                                 placeholder='Ingresa tu contraseña')
        submit   = st.form_submit_button('Iniciar sesión', use_container_width=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

    if submit:
        if do_login(usuario.strip(), password):
            st.session_state.pop('login_error', None)
            st.rerun()
        else:
            st.session_state['login_error'] = True
            st.rerun()
    st.stop()


# ══════════════════════════════════════════════════════════════════
#  USUARIO AUTENTICADO
#  Apuntar st.session_state.fichas al dict compartido (singleton).
#  Así TODOS los usuarios — sin importar cuántos sean — usan la
#  misma copia de datos en memoria.
# ══════════════════════════════════════════════════════════════════
_shared = _shared_fichas()
st.session_state.fichas = _shared          # referencia directa al singleton

with st.sidebar:
    render_sidebar_brand()
    render_sidebar_logout()

# ══════════════════════════════════════════════════════════════════
#  CABECERA
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="header-diresa">
  <div>
    <h1>🏥 DIRESA Huancavelica</h1>
    <p>Sistema de Monitoreo de Indicadores de Desempeño &nbsp;·&nbsp; D.L. 1153 &nbsp;·&nbsp; 2026</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  PANEL DE ADMINISTRACIÓN (solo admin)
# ══════════════════════════════════════════════════════════════════
if is_admin():
    with st.expander('⚙️ Panel de Administración — Gestión de Usuarios', expanded=False):
        st.markdown('<div class="seccion-titulo">👥 Usuarios del Sistema</div>',
                    unsafe_allow_html=True)

        usuarios = list_users()
        df_users = pd.DataFrame(usuarios)
        st.dataframe(df_users, use_container_width=True, hide_index=True,
                     column_config={
                         'usuario': st.column_config.TextColumn('Usuario', width='medium'),
                         'nombre':  st.column_config.TextColumn('Nombre completo', width='large'),
                         'email':   st.column_config.TextColumn('Correo', width='large'),
                         'rol':     st.column_config.TextColumn('Rol', width='small'),
                     })

        st.markdown('<div class="seccion-titulo">➕ Agregar Usuario</div>',
                    unsafe_allow_html=True)
        with st.form('form_add_user', clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_usr  = c1.text_input('Usuario (login)', placeholder='ej: jefe_acobamba')
            new_name = c2.text_input('Nombre completo', placeholder='ej: Juan Pérez')
            new_mail = c1.text_input('Correo electrónico', placeholder='ej: juan@diresa.gob.pe')
            new_pwd  = c2.text_input('Contraseña inicial', type='password',
                                     placeholder='Mínimo 6 caracteres')
            new_rol  = st.selectbox('Rol', ['user', 'admin'],
                                    format_func=lambda x: '👤 Usuario normal' if x == 'user'
                                                          else '⚙️ Administrador')
            if st.form_submit_button('➕ Crear usuario', use_container_width=True):
                if not all([new_usr, new_name, new_mail, new_pwd]):
                    st.error('Completa todos los campos.')
                else:
                    msg = add_user(new_usr.strip(), new_name.strip(),
                                   new_mail.strip(), new_pwd, new_rol)
                    if msg == 'OK':
                        st.success(f'Usuario "{new_usr}" creado correctamente.')
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown('<div class="seccion-titulo">🗑️ Eliminar Usuario</div>',
                    unsafe_allow_html=True)
        other_users = [u['usuario'] for u in usuarios if u['usuario'] != 'admin']
        if other_users:
            del_usr = st.selectbox('Selecciona usuario a eliminar', other_users)
            if st.button(f'🗑️ Eliminar "{del_usr}"', type='secondary'):
                msg = delete_user(del_usr)
                if msg == 'OK':
                    st.success(f'Usuario "{del_usr}" eliminado.')
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info('No hay usuarios adicionales para eliminar.')

    # ── Carga de archivos — SOLO ADMIN ────────────────────────────────────────
    st.markdown('<div class="seccion-titulo">📤 Carga de Indicadores</div>',
                unsafe_allow_html=True)

    c_info, c_up = st.columns([1, 2])
    with c_info:
        st.info("""
**¿Cómo actualizar el dashboard?**
1. Descarga los reportes desde el [Portal de Indicadores DIRESA Huancavelica](https://sites.google.com/saludhuancavelica.pe/indicadores-diresa-hvca/indicadores-de-desempe%C3%B1o-minsa)
2. Cárgalos aquí — todos los usuarios verán los nuevos datos
3. ¡El dashboard se actualiza automáticamente!

Puedes cargar múltiples archivos a la vez.
""")
        if _shared:
            if st.button('🗑️ Limpiar todos los datos cargados', type='secondary',
                         use_container_width=True,
                         help='Borra los indicadores del servidor. Úsalo antes de cargar un nuevo mes.'):
                _shared.clear()
                _hash_cache().clear()
                st.success('Datos eliminados. Carga los nuevos archivos Excel.')
                st.rerun()

    with c_up:
        uploaded = st.file_uploader(
            'Selecciona las fichas Excel (Ficha_01, Ficha_02 … Ficha_32)',
            type=['xlsx'],
            accept_multiple_files=True,
            help='Arrastra aquí los archivos Excel de indicadores DL 1153 2026',
        )

    if uploaded:
        files_data = [(f.read(), f.name) for f in uploaded]
        _hcache = _hash_cache()

        pending, nuevas, desde_cache, errores = [], 0, 0, []
        for fb, fn in files_data:
            md5 = hashlib.md5(fb).hexdigest()
            if md5 in _hcache:                  # ya procesado en el servidor
                cached = _hcache[md5]
                if cached:
                    _shared[cached['id']] = cached
                    desde_cache += 1
            else:
                pending.append((fb, fn, md5))

        if pending:
            def _procesar(args):
                fb, fn, md5 = args
                return load_ficha_bytes(fb, fn), md5

            with st.spinner(f'Procesando {len(pending)} archivo(s) nuevos…'):
                workers = min(len(pending), 8)
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    for result, md5 in pool.map(_procesar, pending):
                        _hcache[md5] = result       # guardar en caché del servidor
                        if result:
                            _shared[result['id']] = result
                            nuevas += 1
                        else:
                            errores.append(md5)

        partes = []
        if nuevas:        partes.append(f'{nuevas} nuevo(s)')
        if desde_cache:   partes.append(f'{desde_cache} ya procesado(s) — sin reprocesar')
        if partes:
            st.success(f'✅ {" · ".join(partes)} indicador(es) cargado(s). '
                       f'Todos los usuarios ya pueden ver los datos.')
        if errores:
            st.warning(f'⚠️ {len(errores)} archivo(s) no reconocido(s) '
                       f'(el nombre debe incluir "Ficha_NN").')


# ══════════════════════════════════════════════════════════════════
#  RESUMEN DE INDICADORES — visible para todos los usuarios
# ══════════════════════════════════════════════════════════════════
if _shared:
    st.markdown('<div class="seccion-titulo">📋 Indicadores Cargados</div>',
                unsafe_allow_html=True)
    rows = []
    for fid, f in sorted(_shared.items()):
        df  = f['df']
        den = int(df['den'].sum())
        num = int(df['num'].sum())
        pct = num / den if den > 0 else 0
        color = get_semaforo_color(pct, f.get('logro'))
        emoji = '🟢' if color == 'verde' else ('🟡' if color == 'amarillo' else '🔴')
        rows.append({'ID': fid,
                     'Indicador': f'{f["icono"]} {f["titulo"][:52]}',
                     'Meta': f['logro_str'],
                     'Den.': f'{den:,}', 'Num.': f'{num:,}',
                     '% Avance': f'{pct*100:.1f}%', 'Estado': emoji})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={
                     'Estado':   st.column_config.TextColumn(width='small'),
                     '% Avance': st.column_config.TextColumn(width='small'),
                     'Meta':     st.column_config.TextColumn(width='small'),
                 })
    total  = len(_shared)
    verdes = sum(1 for r in rows if r['Estado'] == '🟢')
    rojos  = sum(1 for r in rows if r['Estado'] == '🔴')
    m1, m2, m3 = st.columns(3)
    m1.metric('Indicadores cargados', total)
    m2.metric('En meta o superando 🟢', verdes)
    m3.metric('Por debajo de meta 🔴', rojos)
    st.info('👈 Usa el menú lateral para navegar al Resumen General o Detalle por Indicador.')

else:
    # Sin datos cargados
    if is_admin():
        st.markdown("""
<div style="text-align:center;padding:60px 20px;color:#8892a4;">
  <div style="font-size:4.5rem">📂</div>
  <h3 style="color:#E8EAF0;margin-top:12px;">Aún no has cargado ningún indicador</h3>
  <p>Sube los archivos Excel de las fichas DL 1153 2026 para comenzar</p>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div style="text-align:center;padding:60px 20px;color:#8892a4;">
  <div style="font-size:4.5rem">⏳</div>
  <h3 style="color:#E8EAF0;margin-top:12px;">El administrador aún no ha cargado los datos</h3>
  <p>Los indicadores estarán disponibles en cuanto el administrador suba los archivos Excel.</p>
  <p style="margin-top:8px;font-size:0.85rem;">Intenta recargar la página en unos minutos.</p>
</div>""", unsafe_allow_html=True)
