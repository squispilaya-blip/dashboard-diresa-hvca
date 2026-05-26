"""
Página 03 — Comparativo por Red de Salud
Muestra el ranking de cobertura por Red para cada indicador,
con línea de meta, colores semáforo y tabla resumen.
NO modifica ninguna página existente.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.auth import require_auth
from utils.ui import load_css, render_sidebar_brand, render_sidebar_logout
from utils.constants import SEMAFORO, COLORS

st.set_page_config(
    page_title='Comparativo por Red',
    page_icon='📊',
    layout='wide',
)
load_css()
require_auth()

fichas = st.session_state.get('fichas', {})

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    render_sidebar_brand()

    if fichas:
        ids = sorted(fichas.keys())
        st.markdown('<p class="sb-section-title">🔍 INDICADOR</p>',
                    unsafe_allow_html=True)
        fid = st.selectbox(
            'Seleccionar indicador:',
            ids,
            key='comp_ficha',
            format_func=lambda x: f'{fichas[x]["icono"]} ID {x} — {fichas[x]["titulo"][:42]}',
        )

    render_sidebar_logout()

# ── Guardia ───────────────────────────────────────────────────────────────────
if not fichas:
    st.warning('⚠️ Primero carga los archivos Excel en la página de Inicio.')
    st.stop()

ficha    = fichas[fid]
df_base  = ficha['df']
logro    = ficha.get('logro')
logro_str= ficha.get('logro_str', 'N/D')
tipo     = ficha.get('tipo', 'pct')
unidad   = ficha.get('unidad', '%')

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="header-diresa">
  <div style="flex:1">
    <h1>{ficha['icono']} Comparativo por Red — Indicador {fid}</h1>
    <p>{ficha['titulo']}</p>
    <p style="font-size:0.8rem;opacity:0.7;">
      DIRESA Huancavelica &nbsp;·&nbsp; 2026 &nbsp;·&nbsp;
      Ranking de cobertura por Red de Salud
    </p>
  </div>
</div>""", unsafe_allow_html=True)

# ── Verificar que haya datos de Red ──────────────────────────────────────────
if 'red' not in df_base.columns or not df_base['red'].str.len().gt(0).any():
    st.warning('⚠️ Este indicador no tiene datos de Red de Salud en los archivos cargados.')
    st.stop()

# ── Agrupación por RED ────────────────────────────────────────────────────────
df_con_red = df_base[df_base['red'].str.len() > 0]
agg = (df_con_red
       .groupby('red')
       .agg(den=('den', 'sum'), num=('num', 'sum'))
       .reset_index())
agg['pct'] = np.where(agg['den'] > 0, agg['num'] / agg['den'] * 100, 0).round(1)

# Totales DIRESA
den_total = int(df_base['den'].sum())
num_total = int(df_base['num'].sum())
pct_total = round(num_total / den_total * 100, 1) if den_total > 0 else 0

# Umbral de meta en %
thr = (logro or 0) * 100


def _color(pct_val: float) -> str:
    """Color semáforo según % respecto a la meta."""
    if tipo != 'pct' or logro is None or thr == 0:
        return '#4a85c0'
    if pct_val >= thr:
        return SEMAFORO['verde']
    elif pct_val >= thr * 0.80:
        return SEMAFORO['amarillo']
    else:
        return SEMAFORO['rojo']


def _emoji(pct_val: float) -> str:
    c = _color(pct_val)
    if c == SEMAFORO['verde']:   return '🟢'
    if c == SEMAFORO['amarillo']: return '🟡'
    if c == SEMAFORO['rojo']:    return '🔴'
    return '🔵'


# Ordenar por cobertura descendente (ranking)
agg = agg.sort_values('pct', ascending=False).reset_index(drop=True)
agg['rank'] = range(1, len(agg) + 1)

# ── Construcción del gráfico ──────────────────────────────────────────────────
fig = go.Figure()

bar_colors  = [_color(p) for p in agg['pct']]
text_labels = [f'<b>{p:.1f}%</b>' for p in agg['pct']]

fig.add_trace(go.Bar(
    name='Cobertura 2026',
    x=agg['red'],
    y=agg['pct'],
    marker=dict(
        color=bar_colors,
        line=dict(color='rgba(255,255,255,0.15)', width=1),
    ),
    text=text_labels,
    textposition='outside',
    textfont=dict(size=11, color='white', family='Inter'),
    width=0.55,
    customdata=agg[['den', 'num', 'rank']].values,
    hovertemplate=(
        '<b>%{x}</b><br>'
        'Cobertura: %{y:.1f}%<br>'
        'PROG (den): %{customdata[0]:,}<br>'
        'EJEC (num): %{customdata[1]:,}<br>'
        'Ranking: #%{customdata[2]}'
        '<extra></extra>'
    ),
))

# Línea DIRESA (referencia total)
fig.add_hline(
    y=pct_total,
    line_dash='dot',
    line_color='rgba(100,180,255,0.7)',
    line_width=1.5,
    annotation_text=f'  DIRESA: {pct_total:.1f}%',
    annotation_position='top right',
    annotation_font=dict(color='rgba(100,180,255,0.9)', size=11),
)

# Línea META (solo indicadores tipo pct con meta definida)
if logro and tipo == 'pct':
    fig.add_hline(
        y=thr,
        line_dash='dash',
        line_color='#FFB703',
        line_width=2.5,
        annotation_text=f'  META: {thr:.0f}%',
        annotation_position='top left',
        annotation_font=dict(color='#FFB703', size=13, family='Inter'),
    )

y_max = max(agg['pct'].max() if not agg.empty else 0, thr, pct_total) * 1.3
y_max = max(y_max, 20)

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font_color='white',
    height=430,
    margin=dict(l=10, r=10, t=30, b=60),
    xaxis=dict(
        title='Red de Salud',
        gridcolor='rgba(255,255,255,0.06)',
        tickfont=dict(size=10, color='white'),
        tickangle=-20,
    ),
    yaxis=dict(
        title='% Cobertura',
        range=[0, y_max],
        gridcolor='rgba(255,255,255,0.08)',
        ticksuffix='%',
    ),
    bargap=0.25,
    showlegend=False,
)

# ── Layout: gráfico + caja de resumen ────────────────────────────────────────
col_chart, col_box = st.columns([5, 1])

# Caja lateral con META y LOGRO DIRESA
with col_box:
    color_diresa = _color(pct_total)
    emoji_diresa = _emoji(pct_total)

    if logro and tipo == 'pct':
        border_color = '#FFB703'
        meta_html = f"""
  <div style="color:#FFB703;font-size:0.82rem;margin:6px 0;">
    <b>META</b><br>
    <span style="font-size:1.6rem;font-weight:900;">{thr:.0f}%</span>
  </div>
  <hr style="border-color:rgba(255,255,255,0.15);margin:8px 0;">"""
    else:
        border_color = '#4a85c0'
        meta_html = '<div style="color:rgba(255,255,255,0.4);font-size:0.75rem;">Sin meta definida</div><hr style="border-color:rgba(255,255,255,0.15);margin:8px 0;">'

    st.markdown(f"""
<div style="background:#112240;border:2px solid {border_color};border-radius:12px;
            padding:14px 10px;margin-top:28px;text-align:center;">
  <div style="color:{border_color};font-weight:800;font-size:0.75rem;
              text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">
    📋 Resumen</div>
  {meta_html}
  <div style="color:rgba(255,255,255,0.8);font-size:0.78rem;margin:4px 0;">
    <b>LOGRO DIRESA</b><br>
    <span style="font-size:1.4rem;font-weight:900;
                 color:{'#2DC653' if color_diresa==SEMAFORO['verde'] else ('#FFB703' if color_diresa==SEMAFORO['amarillo'] else '#E63946')};">
      {pct_total:.1f}%
    </span> {emoji_diresa}
  </div>
  <hr style="border-color:rgba(255,255,255,0.15);margin:8px 0;">
  <div style="color:rgba(255,255,255,0.5);font-size:0.72rem;line-height:1.6;">
    PROG<br><b style="color:white;">{den_total:,}</b><br>
    EJEC<br><b style="color:white;">{num_total:,}</b>
  </div>
</div>""", unsafe_allow_html=True)

with col_chart:
    st.plotly_chart(fig, use_container_width=True)

# ── Tabla de ranking ──────────────────────────────────────────────────────────
st.markdown('<div class="seccion-titulo">📋 Ranking de Redes — Tabla Resumen</div>',
            unsafe_allow_html=True)

tbl = agg[['rank', 'red', 'pct', 'den', 'num']].copy()
tbl['pendiente'] = (tbl['den'] - tbl['num']).clip(lower=0)

if logro and tipo == 'pct':
    tbl['estado'] = tbl['pct'].apply(
        lambda p: '🟢 En meta' if p >= thr
        else ('🟡 Cerca' if p >= thr * 0.80 else '🔴 Bajo meta')
    )
    col_cfg_extra = {'estado': st.column_config.TextColumn('Estado', width='medium')}
else:
    col_cfg_extra = {}

tbl = tbl.rename(columns={
    'rank':       '#',
    'red':        'Red de Salud',
    'pct':        'Cobertura %',
    'den':        'PROG',
    'num':        'EJEC',
    'pendiente':  'Pendiente',
    'estado':     'Estado',
})

# Fila DIRESA al final como referencia total
fila_diresa = pd.DataFrame([{
    '#': '—',
    'Red de Salud': '📊 DIRESA (Total)',
    'Cobertura %': pct_total,
    'PROG': den_total,
    'EJEC': num_total,
    'Pendiente': max(0, den_total - num_total),
}])
if 'Estado' in tbl.columns:
    fila_diresa['Estado'] = _emoji(pct_total) + (
        ' En meta' if pct_total >= thr else (' Cerca' if pct_total >= thr * 0.8 else ' Bajo meta')
    )

tbl_display = pd.concat([tbl, fila_diresa], ignore_index=True)

st.dataframe(
    tbl_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        '#':            st.column_config.TextColumn('#', width='small'),
        'Red de Salud': st.column_config.TextColumn('Red de Salud', width='large'),
        'Cobertura %':  st.column_config.NumberColumn('Cobertura %', format='%.1f%%', width='medium'),
        'PROG':         st.column_config.NumberColumn('PROG', format='%d', width='small'),
        'EJEC':         st.column_config.NumberColumn('EJEC', format='%d', width='small'),
        'Pendiente':    st.column_config.NumberColumn('Pendiente', format='%d', width='small'),
        **col_cfg_extra,
    },
)

# Leyenda de colores
if logro and tipo == 'pct':
    st.markdown(f"""
<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px;font-size:0.8rem;color:#8892a4;">
  <span>🟢 En meta &nbsp;(≥ {thr:.0f}%)</span>
  <span>🟡 Cerca de meta &nbsp;(≥ {thr*0.8:.0f}%)</span>
  <span>🔴 Bajo meta &nbsp;(< {thr*0.8:.0f}%)</span>
  <span style="color:rgba(100,180,255,0.7);">― ― DIRESA total</span>
  <span style="color:#FFB703;">--- META {thr:.0f}%</span>
</div>""", unsafe_allow_html=True)
