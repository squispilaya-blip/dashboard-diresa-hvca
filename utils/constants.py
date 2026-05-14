COLORS = {
    'primary':   '#003087',
    'secondary': '#00843D',
    'accent':    '#F5A623',
    'danger':    '#E63946',
    'warning':   '#FFB703',
    'success':   '#2DC653',
    'bg_dark':   '#0A1628',
    'bg_card':   '#112240',
    'text':      '#E8EAF0',
}

SEMAFORO = {
    'verde':    '#2DC653',
    'amarillo': '#FFB703',
    'rojo':     '#E63946',
}

INDICADORES = {
    '01': {'nombre': 'Anemia Recuperados',           'logro_default': 0.50, 'icono': '🩸'},
    '02': {'nombre': 'Suplementación Preventiva',    'logro_default': 0.70, 'icono': '💊'},
    '03': {'nombre': 'RN Tamizaje Neonatal',         'logro_default': 0.80, 'icono': '👶'},
    '04': {'nombre': 'Crecimiento Inadecuado <2a',   'logro_default': 0.50, 'icono': '📈'},
    '05': {'nombre': 'Vacuna Niños 24 Meses',        'logro_default': 0.85, 'icono': '💉'},
    '06': {'nombre': 'BCG + Hepatitis B RN',         'logro_default': 0.95, 'icono': '🏥'},
    '10': {'nombre': 'Salud Bucal',                  'logro_default': None, 'icono': '🦷'},
    '11': {'nombre': 'Anticonceptivos',              'logro_default': 0.45, 'icono': '🔵'},
    '12': {'nombre': 'Gestantes Referidas',          'logro_default': 0.80, 'icono': '🤰'},
    '13': {'nombre': 'Gestante Paquete Prev.',       'logro_default': 0.60, 'icono': '📋'},
    '15': {'nombre': 'Mamografía',                   'logro_default': 0.90, 'icono': '🎀'},
    '16': {'nombre': 'Vacuna VPH',                   'logro_default': 0.90, 'icono': '💉'},
    '17': {'nombre': 'Discapacidad <5 años',         'logro_default': 0.30, 'icono': '♿'},
    '19': {'nombre': 'Depresión',                    'logro_default': None, 'icono': '🧠'},
    '25': {'nombre': 'Espera Atención Referido',     'logro_default': None, 'icono': '⏱️'},
    '32': {'nombre': 'Telemedicina',                 'logro_default': None, 'icono': '📱'},
}

# Mapeo: columna estándar → variantes encontradas en los 16 Excel
COLUMN_MAP = {
    'año':       ['año', 'Año', 'anio', 'Anio', 'año'],
    'mes':       ['mes', 'Mes', 'mes_eva'],
    'provincia': ['Provincia', 'PROVINCIA', 'Prov', 'DESC_DPTO'],
    'red':       ['Red', 'RED', 'red'],
    'microred':  ['MicroRed', 'MICRORED', 'Microred_Atc', 'microred'],
    'eess':      ['Eess_Atc', 'ESTABLECIMIENTO', 'eess_nombre', 'EESS',
                  'Columna1', 'Establecimiento', 'establecimiento'],
    'renaes':    ['renaes', 'renaes_atc', 'RENAES', 'Columna2'],
    'num_doc':   ['num_doc', 'ndoc', 'num_cnv', 'num_dni'],
    'nombres':   ['nombres'],
    'den':       ['den', 'Den', 'Denominador', 'DENOMINADOR'],
    'num':       ['num', 'Num', 'Numerador', 'NUMERADOR'],
}

PROVINCIAS_HVCA = [
    'ACOBAMBA', 'ANGARAES', 'CASTROVIRREYNA',
    'CHURCAMPA', 'HUANCAVELICA', 'HUAYTARA', 'TAYACAJA',
]

# Centroides reales de las capitales de provincia de Huancavelica
PROVINCE_CENTROIDS = {
    'ACOBAMBA':       {'lat': -12.850, 'lon': -74.570},
    'ANGARAES':       {'lat': -12.978, 'lon': -74.724},
    'CASTROVIRREYNA': {'lat': -13.276, 'lon': -75.230},
    'CHURCAMPA':      {'lat': -12.444, 'lon': -74.367},
    'HUANCAVELICA':   {'lat': -12.786, 'lon': -74.974},
    'HUAYTARA':       {'lat': -13.633, 'lon': -75.333},
    'TAYACAJA':       {'lat': -12.395, 'lon': -74.858},
}

MESES = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
         7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
MESES_CORTO = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
               7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}

# IMPORTANT-5: Conjunto compartido para limpiar opciones de dropdowns
# Excluye NaN, vacíos, colores de semáforo y valores nulos de Excel
EXCLUIR_OPCIONES = {
    'NAN', 'NONE', 'N/A', 'NA', '0', '0.0', '', 'NULL',
    '#N/A', '#VALUE!', '#REF!', '#NAME?',
    'ROJO', 'VERDE', 'AMARILLO', 'AZUL', 'NARANJA', 'GRIS',
}
