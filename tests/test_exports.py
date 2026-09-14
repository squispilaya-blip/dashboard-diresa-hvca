import pytest
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.exports import df_to_excel_bytes, build_pdf_bytes

class TestExcelExport:
    def test_retorna_bytes(self):
        df = pd.DataFrame({'red': ['ACOBAMBA'], 'den': [10], 'num': [5], 'pct': [0.5]})
        result = df_to_excel_bytes(df, 'Anemia Recuperados', 'RED ACOBAMBA')
        assert isinstance(result, bytes)
        assert len(result) > 200

    def test_df_vacio_retorna_bytes(self):
        result = df_to_excel_bytes(pd.DataFrame(), 'Vacío', 'Todas')
        assert isinstance(result, bytes)

class TestPdfExport:
    def test_retorna_bytes(self):
        df = pd.DataFrame({'red': ['ACOBAMBA'], 'eess': ['C.S. PAMPAS'],
                           'mes': [1], 'den': [10], 'num': [5], 'pct': [0.5]})
        result = build_pdf_bytes(df, 'Anemia', 'ACOBAMBA', '50%', 'ENERO - ABRIL 2026')
        assert isinstance(result, bytes)
        assert len(result) > 500

    def test_df_vacio_retorna_bytes(self):
        result = build_pdf_bytes(pd.DataFrame(), 'Test', 'Todas', 'N/D', 'ENERO - ABRIL 2026')
        assert isinstance(result, bytes)


class TestAnioEnReportes:
    """El anio de los reportes sale del dato, no de una constante escrita a mano."""

    def _df(self, anio):
        return pd.DataFrame({'red': ['ACOBAMBA'] * 2, 'mes': [1, 8],
                             'año': [anio] * 2, 'den': [10, 10], 'num': [5, 5]})

    def test_excel_usa_el_anio_del_dato(self):
        import io as _io, openpyxl
        for anio in (2026, 2031):
            wb = openpyxl.load_workbook(
                _io.BytesIO(df_to_excel_bytes(self._df(anio), 'X', 'Todos')))
            assert f'ENERO - AGOSTO {anio}' in wb.active['A2'].value

    def test_pdf_cambia_con_el_anio(self):
        a = build_pdf_bytes(self._df(2026), 'X', 'Todos', '50%', 'ENERO - AGOSTO 2026')
        b = build_pdf_bytes(self._df(2031), 'X', 'Todos', '50%', 'ENERO - AGOSTO 2031')
        assert a != b and len(a) > 1000
