import streamlit as st
import pandas as pd
from utils.loader import load_ficha, get_semaforo_color
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

    # Mensaje de error dentro de la tarjeta (persiste entre reruns via session_state)
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
            st.session_state.pop('login_error', None)   # limpiar error anterior
            st.rerun()
        else:
            st.session_state['login_error'] = True      # guardar error → rerun muestra aviso
            st.rerun()
    st.stop()


# ══════════════════════════════════════════════════════════════════
#  USUARIO AUTENTICADO — Sidebar con navegación
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    render_sidebar_brand()
    render_sidebar_logout()

if 'fichas' not in st.session_state:
    st.session_state.fichas = {}

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

# ══════════════════════════════════════════════════════════════════
#  CARGA DE INDICADORES
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="seccion-titulo">📤 Carga de Indicadores</div>',
            unsafe_allow_html=True)

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
    st.markdown('<div class="seccion-titulo">📋 Indicadores Cargados</div>',
                unsafe_allow_html=True)
    rows = []
    for fid, f in sorted(st.session_state.fichas.items()):
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
    total  = len(st.session_state.fichas)
    verdes = sum(1 for r in rows if r['Estado'] == '🟢')
    rojos  = sum(1 for r in rows if r['Estado'] == '🔴')
    m1, m2, m3 = st.columns(3)
    m1.metric('Indicadores cargados', total)
    m2.metric('En meta o superando 🟢', verdes)
    m3.metric('Por debajo de meta 🔴', rojos)
    st.info('👈 Usa el menú lateral para navegar al Resumen o Detalle.')
else:
    st.markdown("""
<div style="text-align:center;padding:60px 20px;color:#8892a4;">
  <div style="font-size:4.5rem">📂</div>
  <h3 style="color:#E8EAF0;margin-top:12px;">Aún no has cargado ningún indicador</h3>
  <p>Sube los archivos Excel de las fichas DL 1153 2026 para comenzar</p>
</div>""", unsafe_allow_html=True)
