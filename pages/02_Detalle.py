from datetime import datetime
import streamlit as st
import numpy as np
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.loader import get_semaforo_color
from utils.charts import bar_chart_por_eess, donut_chart
from utils.map_renderer import render_map
from utils.exports import df_to_excel_bytes, build_pdf_bytes
from utils.constants import MESES

st.set_page_config(page_title='Detalle por Indicador', page_icon='🔍', layout='wide')

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
ids = sorted(fichas.keys())

# Pre-seleccionar si venimos del Resumen
default_idx = 0
if st.session_state.get('selected_ficha') in ids:
    default_idx = ids.index(st.session_state.selected_ficha)


_EXCLUIR = {'NAN', 'NONE', 'N/A', 'NA', '0', '0.0', '', 'ROJO', 'VERDE',
             'AMARILLO', 'AZUL', 'NARANJA', 'GRIS', 'NULL', '#N/A', '#VALUE!'}

def _limpiar_opciones(serie):
    """Retorna lista limpia sin NAN/vacíos/colores semáforo/nulos, ordenada."""
    vals = set()
    for v in serie.unique():
        v = str(v).strip()
        if v.upper() not in _EXCLUIR:
            vals.add(v)
    return sorted(vals)


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
    st.markdown('### 🔍 Indicador')
    fid = st.selectbox(
        'Seleccionar indicador:',
        ids,
        index=default_idx,
        format_func=lambda x: f'{fichas[x]["icono"]} ID {x} — {fichas[x]["titulo"][:26]}',
    )
    st.session_state.selected_ficha = fid
    ficha = fichas[fid]
    df_base = ficha['df'].copy()
    logro, logro_str = ficha.get('logro'), ficha.get('logro_str', 'N/D')

    st.markdown('---')
    st.markdown('### 🎯 Filtros')

    # ── Cascading: Red ─────────────────────────────────────────────────────
    redes_opts = _limpiar_opciones(df_base['red'])
    red_sel = st.selectbox('Red de Salud', ['Todas'] + redes_opts)
    df_r = df_base if red_sel == 'Todas' else df_base[df_base['red'] == red_sel]

    # ── Cascading: Microred (depende de Red) ───────────────────────────────
    mrs_opts = _limpiar_opciones(df_r['microred'])
    mr_sel = st.selectbox('Microred', ['Todas'] + mrs_opts)
    df_mr = df_r if mr_sel == 'Todas' else df_r[df_r['microred'] == mr_sel]

    # ── Cascading: EESS (depende de Microred) ─────────────────────────────
    eess_opts = _limpiar_opciones(df_mr['eess'])
    eess_sel = st.selectbox('Establecimiento', ['Todas'] + eess_opts)

    # ── Mes ────────────────────────────────────────────────────────────────
    meses_disp = sorted(m for m in df_base['mes'].unique() if m > 0)
    MESES_L = ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    meses_sel = st.multiselect('📅 Mes(es)', meses_disp, default=meses_disp,
                               format_func=lambda m: MESES_L[int(m)])
    if not meses_sel:
        meses_sel = meses_disp

# ── Filtrado ──────────────────────────────────────────────────────────────────
df_f = df_base.copy()
if red_sel   != 'Todas': df_f = df_f[df_f['red']      == red_sel]
if mr_sel    != 'Todas': df_f = df_f[df_f['microred']  == mr_sel]
if eess_sel  != 'Todas': df_f = df_f[df_f['eess']      == eess_sel]
df_f = df_f[df_f['mes'].isin(meses_sel)]

# ── Header del indicador ──────────────────────────────────────────────────────
den_t = int(df_f['den'].sum())
num_t = int(df_f['num'].sum())
pct_t = num_t / den_t if den_t > 0 else 0
color = get_semaforo_color(pct_t, logro)
emoji = '🟢' if color == 'verde' else ('🟡' if color == 'amarillo' else '🔴')
estado_txt = 'EN META' if color == 'verde' else ('CERCA DE META' if color == 'amarillo' else 'POR DEBAJO')

now = datetime.now()
fecha_txt = now.strftime('%d/%m/%Y %H:%M:%S')
filtro_lbl = f'{red_sel} > {mr_sel} > {eess_sel}'

st.markdown(f"""<div class="header-diresa">
  <div style="flex:1">
    <h1>{ficha['icono']} {ficha['titulo']}</h1>
    <p>Meta: <b>{logro_str}</b> &nbsp;·&nbsp; {filtro_lbl}</p>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px">
    <span class="en-vivo-badge"><span class="en-vivo-dot"></span>&nbsp;EN VIVO &nbsp;·&nbsp; {fecha_txt}</span>
    <div style="text-align:center;background:rgba(0,0,0,0.2);border-radius:10px;padding:8px 18px;">
      <div style="font-size:2rem">{emoji}</div>
      <div style="color:white;font-weight:700;font-size:0.75rem">{estado_txt}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Métricas principales ──────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric('Denominador', f'{den_t:,}')
m2.metric('Numerador',   f'{num_t:,}')
m3.metric('% Avance',    f'{pct_t*100:.1f}%')
pendientes = den_t - num_t
m4.metric('Pendientes',  f'{max(0, pendientes):,}',
          delta=f'{abs(pendientes/den_t*100):.1f}% restante' if den_t > 0 else None,
          delta_color='inverse')

# ── Tabs: Análisis | Pacientes ────────────────────────────────────────────────
has_pacientes = ficha['has_numdoc'] or ficha['has_nombres']
tab_labels = ['📊 Análisis por Red / EESS', '👥 Pacientes Pendientes'] if has_pacientes else ['📊 Análisis por Red / EESS']
tabs = st.tabs(tab_labels)

# ── TAB 1: Análisis ────────────────────────────────────────────────────────────
with tabs[0]:
    col_map, col_bar = st.columns([1, 1])

    # Renderizar mapa una sola vez (reutilizado en pantalla y PDF)
    _map_bytes = None
    try:
        _map_bytes = render_map(df_f, logro)
    except Exception:
        pass

    with col_map:
        st.markdown('<div class="seccion-titulo">🗺️ Mapa por Red / Provincia</div>',
                    unsafe_allow_html=True)
        if _map_bytes:
            st.markdown('<div class="mapa-container">', unsafe_allow_html=True)
            st.image(_map_bytes, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning('No se pudo renderizar el mapa.')

    with col_bar:
        st.markdown('<div class="seccion-titulo">📊 Avance por Establecimiento</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(
            bar_chart_por_eess(df_f, 'Por Establecimiento / Red', logro),
            use_container_width=True,
        )

    # Tabla de avance agrupada
    st.markdown('<div class="seccion-titulo">📋 Tabla de Avance Detallada</div>',
                unsafe_allow_html=True)
    grp = next((c for c in ['eess', 'microred', 'red']
                if c in df_f.columns and df_f[c].str.len().gt(0).any()), None)
    if grp and not df_f.empty:
        tbl = (df_f.groupby([grp, 'mes'])
                   .agg(den=('den','sum'), num=('num','sum'))
                   .reset_index()
                   .sort_values(['mes', grp]))          # ← orden por mes
        tbl['% Avance'] = np.where(tbl['den'] > 0,
                                   (tbl['num']/tbl['den']*100).round(1), 0)
        tbl['Meta'] = logro_str
        tbl['Pendiente'] = (tbl['den'] - tbl['num']).clip(lower=0)
        tbl['Estado'] = tbl['% Avance'].apply(
            lambda p: '🟢 En meta' if (logro and p/100 >= logro)
                      else ('🟡 Cerca' if (logro and p/100 >= logro * 0.8) else '🔴 Bajo')
        )
        tbl['Mes'] = tbl['mes'].map(MESES)
        tbl = tbl.drop(columns=['mes'])
        tbl = tbl.rename(columns={grp: grp.upper(), 'den': 'DEN', 'num': 'NUM'})
        # Reordenar columnas: Mes primero
        cols_order = ['Mes'] + [c for c in tbl.columns if c != 'Mes']
        tbl = tbl[cols_order]
        st.dataframe(tbl, use_container_width=True, hide_index=True,
                     column_config={'% Avance': st.column_config.NumberColumn(format='%.1f%%'),
                                    'Estado': st.column_config.TextColumn(width='medium')})
    elif df_f.empty:
        st.info('Sin datos para los filtros seleccionados.')

    # Descargas
    st.markdown('<div class="seccion-titulo">⬇️ Descargar Reporte</div>',
                unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            '📥 Descargar Excel',
            data=df_to_excel_bytes(df_f, ficha['titulo'], filtro_lbl),
            file_name=f'Ficha{fid}_{red_sel.replace(" ","_")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,
        )
    with d2:
        st.download_button(
            '📄 Descargar PDF',
            data=build_pdf_bytes(df_f, ficha['titulo'], filtro_lbl,
                                 logro_str, 'ENERO - ABRIL 2026',
                                 map_bytes=_map_bytes),
            file_name=f'Ficha{fid}_{red_sel.replace(" ","_")}.pdf',
            mime='application/pdf',
            use_container_width=True,
        )

# ── TAB 2: Pacientes pendientes ────────────────────────────────────────────────
if has_pacientes:
    with tabs[1]:
        st.markdown('<div class="seccion-titulo">👥 Lista de Pacientes Pendientes</div>',
                    unsafe_allow_html=True)
        st.caption('Pacientes que **aún no han cumplido** el indicador (num = 0) para el filtro actual.')

        # Ordenar por mes, red, establecimiento desde el inicio
        df_pend = (df_f[df_f['num'] == 0]
                   .sort_values([c for c in ['mes', 'red', 'eess'] if c in df_f.columns])
                   .copy())

        # ── Buscador en tiempo real ────────────────────────────────────────
        buscar = st.text_input('🔍 Buscar por N° Documento o Nombre',
                               placeholder='Escribe DNI o nombre del paciente...',
                               key=f'buscar_{fid}')
        if buscar.strip():
            q = buscar.strip()
            mask = (
                df_pend['num_doc'].str.contains(q, case=False, na=False) |
                df_pend['nombres'].str.contains(q, case=False, na=False)
            )
            df_pend = df_pend[mask]

        # ── Sub-filtro por EESS dentro de pendientes ───────────────────────
        eess_pend_opts = _limpiar_opciones(df_pend['eess']) if not df_pend.empty else []
        if eess_pend_opts:
            pa, pb = st.columns(2)
            with pa:
                eess_pend = st.selectbox('Filtrar por Establecimiento',
                                         ['Todos'] + eess_pend_opts,
                                         key=f'eess_pend_{fid}')
            if eess_pend != 'Todos':
                df_pend = df_pend[df_pend['eess'] == eess_pend]

        # ── Métricas de pendientes ─────────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        c1.metric('Pendientes (filtro)', f'{len(df_pend):,}')
        c2.metric('Total denominador', f'{den_t:,}')
        c3.metric('% Pendiente',
                  f'{len(df_pend)/den_t*100:.1f}%' if den_t > 0 else 'N/A')

        # ── Columnas a mostrar ─────────────────────────────────────────────
        SHOW_PREF = ['mes', 'red', 'microred', 'eess', 'nombres', 'num_doc', 'provincia']
        SHOW = [c for c in SHOW_PREF if c in df_pend.columns]
        RENAME = {
            'mes': 'Mes', 'red': 'Red', 'microred': 'Microred',
            'eess': 'Establecimiento', 'nombres': 'Nombre Paciente',
            'num_doc': 'N° Documento', 'provincia': 'Provincia',
        }

        if df_pend.empty:
            st.success('🎉 No hay pacientes pendientes para este filtro.')
        else:
            # df_pend ya está ordenado por mes/red/eess — construir df_disp igual
            df_disp = df_pend[SHOW].rename(columns=RENAME).copy()
            if 'Mes' in df_disp.columns:
                df_disp['Mes'] = df_disp['Mes'].map(MESES)
            for col in df_disp.select_dtypes(include='object').columns:
                df_disp[col] = df_disp[col].replace({'NAN': '', 'nan': ''})

            st.dataframe(df_disp, use_container_width=True, hide_index=True, height=420)

            # Descarga = exactamente lo que se ve en pantalla (mismo orden, mismas columnas)
            st.download_button(
                '📥 Descargar lista de pendientes (Excel)',
                data=df_to_excel_bytes(
                    df_disp,                             # usar df_disp ya procesado
                    f'Pendientes — {ficha["titulo"]}',
                    filtro_lbl,
                ),
                file_name=f'Pendientes_F{fid}_{red_sel.replace(" ","_")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True,
            )
