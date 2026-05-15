"""
Autenticación y gestión de usuarios para DIRESA Huancavelica.
"""
import os
import streamlit as st
import yaml
from yaml.loader import SafeLoader
import bcrypt

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'users.yaml')


def load_config() -> dict:
    with open(CONFIG_PATH, encoding='utf-8') as f:
        return yaml.load(f, Loader=SafeLoader)


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(12)).decode()


def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def do_login(username: str, password: str) -> bool:
    """Verifica credenciales y puebla session_state. Retorna True si OK."""
    config = load_config()
    users = config.get('credentials', {}).get('usernames', {})
    if username not in users:
        return False
    user = users[username]
    if not check_password(password, user.get('password', '')):
        return False
    st.session_state['authenticated']  = True
    st.session_state['username']        = username
    st.session_state['user_name']       = user.get('name', username)
    st.session_state['role']            = user.get('role', 'user')
    return True


def do_logout() -> None:
    for k in ['authenticated', 'username', 'user_name', 'role']:
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get('authenticated'))


def is_admin() -> bool:
    return st.session_state.get('role') == 'admin'


def require_auth():
    """
    Llama al inicio de cada página protegida.
    Si no está autenticado, muestra mensaje y detiene la ejecución.
    """
    if not is_authenticated():
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;color:#8892a4;">
          <div style="font-size:4rem">🔒</div>
          <h3 style="color:#E8EAF0;margin-top:12px;">Acceso restringido</h3>
          <p>Debes iniciar sesión para ver este contenido.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button('🔑 Ir al inicio de sesión', use_container_width=False):
            st.switch_page('app.py')
        st.stop()


# ── Admin: gestión de usuarios ────────────────────────────────────────────────

def add_user(username: str, name: str, email: str, password: str, role: str = 'user') -> str:
    """Agrega un usuario. Retorna mensaje de éxito o error."""
    config = load_config()
    users  = config['credentials']['usernames']
    if username in users:
        return f'El usuario "{username}" ya existe.'
    if len(password) < 6:
        return 'La contraseña debe tener al menos 6 caracteres.'
    users[username] = {
        'name':                  name,
        'email':                 email,
        'password':              hash_password(password),
        'role':                  role,
        'failed_login_attempts': 0,
        'logged_in':             False,
    }
    save_config(config)
    return 'OK'


def delete_user(username: str) -> str:
    """Elimina un usuario. No permite eliminar al admin."""
    if username == 'admin':
        return 'No se puede eliminar al administrador.'
    config = load_config()
    users  = config['credentials']['usernames']
    if username not in users:
        return f'Usuario "{username}" no encontrado.'
    del users[username]
    save_config(config)
    return 'OK'


def list_users() -> list[dict]:
    """Retorna lista de usuarios (sin contraseñas)."""
    config = load_config()
    result = []
    for uname, data in config['credentials']['usernames'].items():
        result.append({
            'usuario':  uname,
            'nombre':   data.get('name', ''),
            'email':    data.get('email', ''),
            'rol':      data.get('role', 'user'),
        })
    return result
