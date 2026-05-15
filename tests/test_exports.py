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
