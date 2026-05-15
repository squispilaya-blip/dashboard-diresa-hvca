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
    '01': {'nombre': 'Porcentaje de niñas y niños de 12 a 18 meses, con diagnóstico de anemia entre los 6 y 11 meses, que se han recuperado',
           'logro_default': 0.50, 'icono': '🩸'},
    '02': {'nombre': 'Porcentaje de niñas y niños de 6 a 11 meses que iniciaron suplementación preventiva con hierro, culminan el esquema completo de 6 meses y se mantienen sin anemia',
           'logro_default': 0.70, 'icono': '💊'},
    '03': {'nombre': 'Porcentaje de recién nacidos con tamizaje neonatal metabólico',
           'logro_default': 0.80, 'icono': '👶'},
    '04': {'nombre': 'Niñas y niños menores de 2 años en condición de crecimiento inadecuado que luego de un periodo de seguimiento mejora sus condiciones nutricionales',
           'logro_default': 0.50, 'icono': '📈'},
    '05': {'nombre': 'Niñas y niños de 24 meses que reciben vacunas para su edad',
           'logro_default': 0.85, 'icono': '💉'},
    '06': {'nombre': 'Recién nacidos de parto institucional, vacunados con BCG y Anti hepatitis B, dentro de las 24 horas después del nacimiento',
           'logro_default': 0.95, 'icono': '🏥'},
    '10': {'nombre': 'Porcentaje de niñas y niños (6 meses a 6 años 11 meses y 29 días) que reciben procedimientos estomatológicos preventivos',
           'logro_default': None, 'icono': '🦷'},
    '11': {'nombre': 'Porcentaje de personas que acceden a algún método anticonceptivo moderno de planificación familiar',
           'logro_default': 0.45, 'icono': '🔵'},
    '12': {'nombre': 'Porcentaje de gestantes atendidas con 2 ó más Atenciones Prenatales (APN) en el hospital, referidas por factores de riesgo',
           'logro_default': 0.80, 'icono': '🤰'},
    '13': {'nombre': 'Porcentaje de gestantes con paquete preventivo básico priorizado',
           'logro_default': 0.60, 'icono': '📋'},
    '15': {'nombre': 'Porcentaje de mujeres de 40 a 69 años con mamografía bilateral de tamizaje',
           'logro_default': 0.90, 'icono': '🎀'},
    '16': {'nombre': 'Porcentaje de niñas y niños de 9 años de edad vacunados contra el virus del papiloma humano (VPH)',
           'logro_default': 0.90, 'icono': '💉'},
    '17': {'nombre': 'Porcentaje de niños y niñas menores de 5 años con deficiencias o factores de riesgo de discapacidad, con seis o más atenciones en la UPSS Medicina de Rehabilitación',
           'logro_default': 0.30, 'icono': '♿'},
    '19': {'nombre': 'Porcentaje de personas con diagnóstico de depresión que recibieron paquete estándar de intervenciones',
           'logro_default': None, 'icono': '🧠'},
    '25': {'nombre': 'Promedio de espera para la atención en Consulta Externa de un paciente referido',
           'logro_default': None, 'icono': '⏱️',
           'tipo': 'promedio', 'unidad': 'hrs'},
    '32': {'nombre': 'Tasas de uso de los servicios de telemedicina',
           'logro_default': None, 'icono': '📱',
           'tipo': 'tasa', 'unidad': 'x10k',
           # Ficha técnica oficial (Anexo I 2026, pág. 78):
           #   num = (TeleInterconsulta×6/4 + TeleConsulta×1/3 + TeleMonitoreo×30/72)×10,000
           #   den = Poblacion asignada (1er nivel) | Atenciones (2do/3er nivel)
           #   TASA = num/den
           #   Valor umbral   = 10   (tasa minima)
           #   Logro esperado = 100  (tasa objetivo)
           #   % Cumplimiento = (tasa - umbral) / (logro_tasa - umbral) x 100, cap 100%
           'sheet_filter': {'col': 'Indicador', 'val': 'Indicador A'},
           'umbral':     10,
           'logro_tasa': 100},
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
    # ── Columnas adicionales de contexto clínico ──────────────────────────
    # fecha_nac: Fichas 01, 02, 03, 06
    'fecha_nac':  ['fecha_nac', 'Fecha_Nac', 'FECHA_NAC', 'fecha_nacimiento', 'Fecha_Nacimiento'],
    # fecha_dx: diagnóstico (F01,F04), parto (F13), referencia (F12), dx depresión (F19)
    'fecha_dx':   ['fecha_dx', 'Fecha_Dx', 'FECHA_DX', 'fecha_parto', 'Fecha_Parto',
                   'Fecha_Referencia', 'fecha_referencia',
                   'fecha_diagnostico', 'Fecha_diagnostico', 'FECHA_DIAGNOSTICO'],
    # genero: Fichas 10, 11, 16, 19
    'genero':     ['genero', 'Genero', 'GENERO', 'id_genero', 'sexo', 'Sexo', 'SEXO'],
    # seguro: Fichas 01, 02
    'seguro':     ['seguro', 'Seguro', 'SEGURO', 'tipo_seguro'],
    # categoria: categoría del EESS — Fichas 04, 06, 10, 11, 12, 17, 25
    'categoria':  ['Categoria', 'CATEGORIA', 'cat_estab', 'CAT_ESTAB', 'Categoria_Estab'],
    # edad: Ficha 16 (VPH — niños de 9 años)
    'edad':       ['edad', 'Edad', 'EDAD'],
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
