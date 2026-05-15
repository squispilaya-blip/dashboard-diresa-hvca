import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.constants import COLORS, SEMAFORO, MESES_CORTO, PROVINCE_CENTROIDS


def _layout_base(title: str, height: int = 340) -> dict:
    return dict(
        title=dict(text=title, font=dict(color='white', size=13)),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=height,
        margin=dict(l=10, r=20, t=44, b=20),
    )


def kpi_card_html(icono: str, titulo: str, pct: float,
                  logro: float | None, color: str,
                  tipo: str = 'pct', unidad: str = '%',
                  titulo_full: str = '') -> str:
    if tipo == 'promedio':
        pct_str  = f'{pct:.2f} {unidad}'
        meta_str = 'Promedio de espera'
        bar_w    = 0          # sin barra de progreso
        bar_color = '#4a5568'
        emoji    = '⏱️'
        color    = 'sin_data' if color not in SEMAFORO else color
    elif tipo == 'tasa':
        pct_str  = f'{pct:.1f} ×10k'
        meta_str = 'Tasa ponderada de telemedicina'
        bar_w    = 0
        bar_color = '#4a5568'
        emoji    = '📊'
        color    = color if color in SEMAFORO else 'rojo'
    else:
        pct_str  = f'{pct*100:.1f}%'
        meta_str = f'Meta: {logro*100:.0f}%' if logro else 'Sin meta definida'
        bar_w    = min(100, int(pct * 100))
        bar_color = SEMAFORO.get(color, '#4a5568')
        emoji    = '🟢' if color == 'verde' else ('🟡' if color == 'amarillo' else '🔴')

    card_color = color if color in ('verde', 'amarillo', 'rojo') else 'rojo'
    tooltip = titulo_full or titulo
    return f"""<div class="kpi-card {card_color}" title="{tooltip}">
  <div class="kpi-icono">{icono}&nbsp;{emoji}</div>
  <div class="kpi-titulo">{titulo}</div>
  <div class="kpi-valor">{pct_str}</div>
  <div class="kpi-meta">{meta_str}</div>
  <div class="kpi-barra-bg">
    <div class="kpi-barra" style="width:{bar_w}%;background:{bar_color};"></div>
  </div>
</div>"""


def scatter_map_provincias(df: pd.DataFrame, logro: float | None,
                           titulo: str) -> go.Figure:
    """Mapa scatter real de Huancavelica con puntos por provincia/Red coloreados por % avance."""
    rows = []
    if not df.empty and 'red' in df.columns and df['red'].str.len().gt(0).any():
        agg = (df[df['red'].str.len() > 0]
               .groupby('red')
               .agg(den=('den', 'sum'), num=('num', 'sum'))
               .reset_index())
        agg['pct'] = np.where(agg['den'] > 0, agg['num'] / agg['den'] * 100, 0).round(1)
        for _, row in agg.iterrows():
            red_name = row['red'].upper()
            # Match Red name to a known province centroid (or use closest match)
            centroid = None
            for prov, coords in PROVINCE_CENTROIDS.items():
                if prov in red_name or red_name in prov:
                    centroid = coords
                    break
            if centroid is None:
                # Assign sequentially to any unmatched centroid
                assigned = [r['prov'] for r in rows]
                for prov, coords in PROVINCE_CENTROIDS.items():
                    if prov not in assigned:
                        centroid = coords
                        break
            if centroid:
                thr = (logro or 0) * 100
                color = (SEMAFORO['verde'] if row['pct'] >= thr
                         else SEMAFORO['amarillo'] if thr > 0 and row['pct'] >= thr * 0.8
                         else SEMAFORO['rojo'])
                rows.append({
                    'Red': row['red'],
                    'lat': centroid['lat'],
                    'lon': centroid['lon'],
                    'pct': row['pct'],
                    'den': int(row['den']),
                    'num': int(row['num']),
                    'color': color,
                    'prov': red_name,
                })

    if not rows:
        # Si no hay datos de Red, mostrar las 7 provincias en gris
        for prov, coords in PROVINCE_CENTROIDS.items():
            rows.append({'Red': prov, 'lat': coords['lat'], 'lon': coords['lon'],
                         'pct': 0, 'den': 0, 'num': 0, 'color': '#4a5568', 'prov': prov})

    map_df = pd.DataFrame(rows)
    thr = (logro or 0) * 100

    fig = go.Figure()

    # Círculo de fondo (borde)
    fig.add_trace(go.Scattermapbox(
        lat=map_df['lat'], lon=map_df['lon'],
        mode='markers',
        marker=dict(size=52, color='rgba(255,255,255,0.15)'),
        hoverinfo='skip',
        showlegend=False,
    ))

    # Círculos coloreados
    fig.add_trace(go.Scattermapbox(
        lat=map_df['lat'], lon=map_df['lon'],
        mode='markers+text',
        marker=dict(
            size=46,
            color=map_df['color'],
            opacity=0.88,
        ),
        text=map_df['pct'].apply(lambda p: f'{p:.0f}%'),
        textfont=dict(size=11, color='white', family='Inter'),
        textposition='middle center',
        customdata=map_df[['Red', 'num', 'den']].values,
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            'Avance: %{text}<br>'
            'Num: %{customdata[1]:,} / Den: %{customdata[2]:,}'
            '<extra></extra>'
        ),
        showlegend=False,
    ))

    fig.update_layout(
        mapbox=dict(
            style='carto-darkmatter',
            center={'lat': -12.9, 'lon': -74.9},
            zoom=7.2,
        ),
        **_layout_base(titulo, 420),
        margin=dict(l=0, r=0, t=44, b=0),
    )

    if logro:
        fig.add_annotation(
            text=f'Meta: {thr:.0f}%', xref='paper', yref='paper',
            x=0.01, y=0.04, showarrow=False,
            font=dict(color=COLORS['accent'], size=12, family='Inter'),
            bgcolor='rgba(0,0,0,0.6)', borderpad=5,
        )
    return fig


@st.cache_data(show_spinner=False)
def bar_chart_por_eess(df: pd.DataFrame, titulo: str,
                       logro: float | None,
                       tipo: str = 'pct', unidad: str = '%') -> go.Figure:
    col = next((c for c in ['eess', 'microred', 'red']
                if c in df.columns and df[c].str.len().gt(0).any()), None)
    if not col or df.empty:
        return go.Figure()
    agg = (df.groupby(col)
             .agg(den=('den', 'sum'), num=('num', 'sum'))
             .reset_index())
    agg['pct'] = np.where(agg['den'] > 0, agg['num'] / agg['den'], 0)
    agg = agg[agg[col].str.len() > 0]

    if tipo == 'promedio':
        # Para promedio: menor espera = mejor → ordenar descendente para visualizar
        agg = agg.sort_values('pct', ascending=False).tail(20)
        bar_colors = ['#4a85c0'] * len(agg)
        text_vals  = [f'{p:.2f} {unidad}' for p in agg['pct']]
        x_title    = f'Promedio ({unidad})'
        x_range    = [0, agg['pct'].max() * 1.2 + 0.5]
        hover_tmpl = f'<b>%{{y}}</b><br>Promedio: %{{x:.2f}} {unidad}<extra></extra>'
        vline_x    = None
    elif tipo == 'tasa':
        # Tasa ponderada × 10,000 — mayor es mejor
        agg = agg.sort_values('pct').tail(20)
        bar_colors = ['#7b5ea7'] * len(agg)   # morado neutro
        text_vals  = [f'{p:.1f}' for p in agg['pct']]
        x_title    = 'Tasa (×10,000)'
        x_range    = [0, agg['pct'].max() * 1.2 + 1]
        hover_tmpl = '<b>%{y}</b><br>Tasa: %{x:.1f} ×10k<extra></extra>'
        vline_x    = None
    else:
        agg = agg.sort_values('pct').tail(20)
        pcts_pct   = agg['pct'] * 100
        thr        = (logro or 0) * 100
        bar_colors = [SEMAFORO['verde'] if p >= thr
                      else SEMAFORO['amarillo'] if thr > 0 and p >= thr * 0.8
                      else SEMAFORO['rojo'] for p in pcts_pct]
        text_vals  = [f'{p:.1f}%' for p in pcts_pct]
        agg['pct'] = pcts_pct    # convertir a % para el eje
        x_title    = '% Avance'
        x_range    = [0, 120]
        hover_tmpl = '<b>%{y}</b><br>%{x:.1f}%<extra></extra>'
        vline_x    = thr if logro else None

    fig = go.Figure(go.Bar(
        x=agg['pct'], y=agg[col], orientation='h',
        marker_color=bar_colors,
        text=text_vals,
        textposition='outside',
        hovertemplate=hover_tmpl,
    ))
    if vline_x:
        fig.add_vline(x=vline_x, line_dash='dash', line_color=COLORS['accent'],
                      annotation_text=f'Meta {vline_x:.0f}%',
                      annotation_font_color=COLORS['accent'])
    fig.update_layout(
        **_layout_base(titulo, max(300, len(agg) * 34 + 80)),
        xaxis=dict(range=x_range, gridcolor='rgba(255,255,255,0.08)', title=x_title),
        yaxis=dict(gridcolor='rgba(255,255,255,0.08)'),
    )
    return fig


@st.cache_data(show_spinner=False)
def donut_chart(num: int, den: int, logro: float | None, titulo: str) -> go.Figure:
    pendiente = max(0, den - num)
    pct = num / den * 100 if den > 0 else 0
    thr = (logro or 0) * 100
    color = (SEMAFORO['verde'] if pct >= thr
             else SEMAFORO['amarillo'] if thr > 0 and pct >= thr * 0.8
             else SEMAFORO['rojo'])
    fig = go.Figure(go.Pie(
        labels=['Logrado', 'Pendiente'],
        values=[num, max(0, pendiente)],
        hole=0.66,
        marker_colors=[color, '#1e3a5f'],
        textinfo='none',
        hovertemplate='%{label}: %{value:,}<extra></extra>',
    ))
    fig.add_annotation(text=f'<b>{pct:.1f}%</b>', x=0.5, y=0.5,
                       font=dict(size=20, color='white'), showarrow=False)
    fig.update_layout(
        **_layout_base(titulo, 280),
        showlegend=True,
        legend=dict(font=dict(color='white'), orientation='h', yanchor='bottom', y=-0.2),
    )
    return fig


@st.cache_data(show_spinner=False)
def line_chart_mensual(df: pd.DataFrame, titulo: str) -> go.Figure:
    if df.empty or 'mes' not in df.columns:
        return go.Figure()
    tiene_red = ('red' in df.columns and df['red'].str.len().gt(0).any())
    if tiene_red:
        agg = (df.groupby(['mes', 'red'])
                 .agg(den=('den', 'sum'), num=('num', 'sum'))
                 .reset_index())
        agg['pct'] = np.where(agg['den'] > 0, agg['num'] / agg['den'] * 100, 0)
        fig = px.line(agg, x='mes', y='pct', color='red', markers=True,
                      labels={'mes': 'Mes', 'pct': '% Avance', 'red': 'Red'},
                      color_discrete_sequence=px.colors.qualitative.Bold)
    else:
        agg = (df.groupby('mes')
                 .agg(den=('den', 'sum'), num=('num', 'sum'))
                 .reset_index())
        agg['pct'] = np.where(agg['den'] > 0, agg['num'] / agg['den'] * 100, 0)
        fig = px.line(agg, x='mes', y='pct', markers=True,
                      labels={'mes': 'Mes', 'pct': '% Avance'},
                      color_discrete_sequence=[COLORS['secondary']])
    tick_vals = sorted(agg['mes'].unique().tolist())
    tick_text = [MESES_CORTO.get(int(m), str(m)) for m in tick_vals]
    fig.update_xaxes(tickvals=tick_vals, ticktext=tick_text)
    fig.update_layout(
        **_layout_base(titulo, 300),
        xaxis=dict(gridcolor='rgba(255,255,255,0.08)'),
        yaxis=dict(title='% Avance', gridcolor='rgba(255,255,255,0.08)', range=[0, 110]),
        legend=dict(font=dict(color='white')),
    )
    return fig
