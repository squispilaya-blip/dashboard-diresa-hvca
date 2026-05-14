import io
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from fpdf import FPDF


def df_to_excel_bytes(df: pd.DataFrame, titulo: str, filtro: str) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Reporte'

    hdr_fill = PatternFill('solid', fgColor='003087')
    hdr_font = Font(bold=True, color='FFFFFF', size=11)
    alt_fill = PatternFill('solid', fgColor='EEF2FF')

    ws['A1'] = f'DIRESA HUANCAVELICA — {titulo}'
    ws['A1'].font = Font(bold=True, color='003087', size=13)
    ws['A2'] = f'Filtro: {filtro}  |  PERIODO: ENERO - ABRIL 2026'
    ws['A2'].font = Font(italic=True, color='444444', size=10)

    max_col = max(8, 1)
    ws.merge_cells(f'A1:{get_column_letter(max_col)}1')
    ws.merge_cells(f'A2:{get_column_letter(max_col)}2')
    ws.row_dimensions[3].height = 5

    if df.empty:
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    RENAME = {
        'año': 'AÑO', 'mes': 'MES', 'provincia': 'PROVINCIA',
        'red': 'RED', 'microred': 'MICRORED', 'eess': 'ESTABLECIMIENTO',
        'renaes': 'RENAES', 'num_doc': 'N° DOCUMENTO', 'nombres': 'NOMBRES',
        'den': 'DENOMINADOR', 'num': 'NUMERADOR', 'pct': '% AVANCE',
    }
    df_out = df.copy()
    if 'pct' in df_out.columns:
        df_out['pct'] = (df_out['pct'] * 100).round(1).astype(str) + '%'
    df_out = df_out.rename(columns=RENAME)
    cols = [c for c in df_out.columns if c not in ('ficha_id',)]
    df_out = df_out[cols]

    start = 4
    for ci, col in enumerate(df_out.columns, 1):
        cell = ws.cell(row=start, column=ci, value=col)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal='center')

    for ri, row in enumerate(df_out.itertuples(index=False), start + 1):
        for ci, val in enumerate(row, 1):
            cell = ws.cell(row=ri, column=ci, value=val)
            if ri % 2 == 0:
                cell.fill = alt_fill
            cell.alignment = Alignment(horizontal='center')

    for ci in range(1, len(df_out.columns) + 1):
        ws.column_dimensions[get_column_letter(ci)].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _latin1(s: str) -> str:
    """Convierte a latin-1 reemplazando caracteres fuera de rango (ej: ›, →)."""
    return s.encode('latin-1', errors='replace').decode('latin-1')


def build_pdf_bytes(df: pd.DataFrame, titulo: str, filtro: str,
                    logro_str: str, periodo: str) -> bytes:
    titulo  = _latin1(titulo)
    filtro  = _latin1(filtro.replace('›', '>').replace('→', '>'))
    logro_str = _latin1(logro_str)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Encabezado institucional
    pdf.set_fill_color(0, 48, 135)
    pdf.rect(0, 0, 210, 36, 'F')
    pdf.set_font('Helvetica', 'B', 15)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 8)
    pdf.cell(190, 8, 'DIRESA HUANCAVELICA', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_x(10)
    pdf.cell(190, 6, 'Indicadores de Desempeno DL 1153 - 2026', align='C',
             new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(10)
    pdf.cell(190, 6, periodo, align='C', new_x='LMARGIN', new_y='NEXT')

    pdf.set_xy(10, 44)
    pdf.set_text_color(0, 48, 135)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.multi_cell(190, 7, titulo)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(95, 7, f'Red / Filtro: {filtro}')
    pdf.cell(95, 7, f'Logro esperado: {logro_str}', align='R',
             new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    if df.empty:
        pdf.set_text_color(180, 0, 0)
        pdf.cell(190, 8, 'Sin datos para el filtro seleccionado.',
                 new_x='LMARGIN', new_y='NEXT')
        return bytes(pdf.output())

    COLS = [c for c in ['red', 'eess', 'mes', 'den', 'num', 'pct'] if c in df.columns]
    HDRS = {'red': 'RED', 'eess': 'ESTABLECIMIENTO', 'mes': 'MES',
            'den': 'DEN', 'num': 'NUM', 'pct': '% AVZ'}
    WIDTHS = {'red': 32, 'eess': 58, 'mes': 13, 'den': 20, 'num': 20, 'pct': 22}

    df_p = df[COLS].copy()
    if 'pct' in df_p.columns:
        df_p['pct'] = (df_p['pct'] * 100).round(1).astype(str) + '%'

    pdf.set_fill_color(0, 48, 135)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 8)
    for col in COLS:
        pdf.cell(WIDTHS[col], 7, HDRS[col], border=1, fill=True, align='C')
    pdf.ln()

    alt = False
    pdf.set_font('Helvetica', '', 7)
    for _, row in df_p.iterrows():
        if alt:
            pdf.set_fill_color(238, 242, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(30, 30, 30)
        for col in COLS:
            val = str(row[col])[:28]
            pdf.cell(WIDTHS[col], 6, val, border=1, fill=True, align='C')
        pdf.ln()
        alt = not alt

    pdf.set_y(-14)
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f'Dashboard DIRESA Huancavelica  |  Pagina {pdf.page_no()}', align='C')

    return bytes(pdf.output())
