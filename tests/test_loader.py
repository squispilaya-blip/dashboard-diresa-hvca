import pytest
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.loader import detect_ficha_id, extract_logro, normalize_df, get_semaforo_color

class TestDetectFichaId:
    def test_detecta_01(self):
        assert detect_ficha_id('Ficha_01_DL1153_202604_Anemia.xlsx') == '01'

    def test_detecta_32(self):
        assert detect_ficha_id('Ficha_32_DL1153_Telemedicina.xlsx') == '32'

    def test_detecta_15(self):
        assert detect_ficha_id('Ficha_15_Mamografia.xlsx') == '15'

    def test_desconocido_retorna_none(self):
        assert detect_ficha_id('datos_varios.xlsx') is None

class TestExtractLogro:
    def test_extrae_50_decimal(self):
        df = pd.DataFrame({0: ['Logro esperado:'], 1: ['0.5']})
        assert extract_logro(df) == pytest.approx(0.5)

    def test_extrae_85_porcentaje(self):
        df = pd.DataFrame({0: ['x', 'Logro esperado:'], 1: ['x', '>=85%']})
        assert extract_logro(df) == pytest.approx(0.85)

    def test_extrae_90_porcentaje_simple(self):
        df = pd.DataFrame({0: ['Logro esperado:', 'otro'], 1: ['>=90%', 'dato']})
        assert extract_logro(df) == pytest.approx(0.90)

    def test_retorna_none_cuando_falta(self):
        df = pd.DataFrame({0: ['sin logro aqui'], 1: ['dato']})
        assert extract_logro(df) is None

class TestNormalizeDf:
    def test_normaliza_den_num(self):
        df = pd.DataFrame({
            'Denominador': [10, 20], 'Numerador': [5, 15],
            'RED': ['A', 'B'], 'año': [2026, 2026], 'mes': [1, 2]
        })
        result = normalize_df(df, '01')
        assert 'den' in result.columns
        assert 'num' in result.columns
        assert result['den'].tolist() == [10, 20]

    def test_agrega_columna_pct(self):
        df = pd.DataFrame({'den': [10], 'num': [5], 'año': [2026], 'mes': [1]})
        result = normalize_df(df, '01')
        assert 'pct' in result.columns
        assert result['pct'].iloc[0] == pytest.approx(0.5)

    def test_normaliza_red_maiuscula(self):
        df = pd.DataFrame({'RED': ['acobamba'], 'den': [5], 'num': [3], 'año': [2026], 'mes': [1]})
        result = normalize_df(df, '11')
        assert result['red'].iloc[0] == 'ACOBAMBA'

    def test_pct_cero_cuando_den_cero(self):
        df = pd.DataFrame({'den': [0], 'num': [0], 'año': [2026], 'mes': [1]})
        result = normalize_df(df, '01')
        assert result['pct'].iloc[0] == 0.0

class TestSemaforoColor:
    def test_verde_cuando_supera_meta(self):
        assert get_semaforo_color(0.55, 0.50) == 'verde'

    def test_amarillo_entre_80_y_100_pct_meta(self):
        assert get_semaforo_color(0.42, 0.50) == 'amarillo'

    def test_rojo_por_debajo_80_pct_meta(self):
        assert get_semaforo_color(0.30, 0.50) == 'rojo'

    def test_verde_cuando_logro_none_y_hay_avance(self):
        assert get_semaforo_color(0.10, None) == 'verde'

    def test_rojo_cuando_logro_none_y_sin_avance(self):
        assert get_semaforo_color(0.0, None) == 'rojo'
