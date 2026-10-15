"""Configuración central de @miniretxs: mini retos de matemáticas, 6 al día, UNA imagen por post."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v26.0")
THREADS_VERSION = os.getenv("THREADS_VERSION", "v1.0")

HANDLE = os.getenv("PAGE_HANDLE", "@miniretxs")
FOOTER = "UN MINI RETO NUEVO CADA DÍA"   # texto al pie de cada imagen

# Paleta (misma que Mateguapo: negro / blanco / amarillo / rojo)
BRAND = {"bg": "#000000", "fg": "#FFFFFF", "accent": "#ffde59", "alert": "#ff3131"}
# Color de la etiqueta de dificultad en la imagen
COLOR_NIVEL = {"facil": "#7ed957", "medio": "#ffde59", "dificil": "#ff3131"}
NOMBRE_NIVEL = {"facil": "FÁCIL", "medio": "MEDIO", "dificil": "DIFÍCIL"}

# Hashtags que SIEMPRE van en el caption de Instagram/Facebook (Claude agrega 2-4 más)
HASHTAGS_FIJOS = ["#miniretxs", "#retomatematico"]

# ---------------------------------------------------------------------------
# HORARIOS (tipo de post). Los 6 posts son UNA imagen con el reto, sin imagen final ni respuesta.
#   nivel:    dificultad del reto ("facil" | "medio" | "dificil")
#   formatos: peso base de cada formato (claves de bot/prompts.py → FORMATOS).
#             El aprendizaje automático multiplica estos pesos según el rendimiento.
# Las horas están en .github/workflows/post.yml (cron en UTC).
# ---------------------------------------------------------------------------
SLOTS = {
    1: {"nivel": "facil",   "formatos": {"operacion": 3, "patron": 2, "cual_mayor": 1}},                 # 08:00
    2: {"nivel": "medio",   "formatos": {"logica": 3, "palabras": 2, "emoji": 2}},                       # 11:00
    3: {"nivel": "facil",   "formatos": {"emoji": 3, "operacion": 2, "palabras": 1, "cual_mayor": 1}},   # 14:00
    4: {"nivel": "medio",   "formatos": {"patron": 2, "conteo": 2, "probabilidad": 2, "cual_mayor": 1}}, # 17:00
    5: {"nivel": "facil",   "formatos": {"operacion": 2, "palabras": 2, "logica": 2, "emoji": 1}},       # 20:00
    6: {"nivel": "dificil", "formatos": {"logica": 3, "error_oculto": 2, "conteo": 1, "probabilidad": 1}},  # 22:00
}

# TIPO DE RETO: peso base de cada uno (el aprendizaje los ajusta según el rendimiento).
#   exacto: una sola respuesta correcta · debate: varias respuestas defendibles (genera discusión en comentarios)
ESTILOS = {"exacto": 1, "debate": 1}
SOLO_EXACTO = ["error_oculto"]  # formatos que siempre son exactos (en "¿dónde está el error?" hay un único paso inválido)

# Bancos de temas por formato (se rotan para no repetir)
TEMAS = {
    "operacion": ["orden de operaciones con trampa", "fracciones que engañan", "potencias y signos negativos",
                  "decimales y porcentajes", "raíces y potencias sencillas", "operaciones con paréntesis anidados",
                  "multiplicar y dividir de izquierda a derecha"],
    "cual_mayor": ["comparar potencias", "comparar fracciones", "comparar porcentajes encadenados",
                   "comparar raíces", "comparar expresiones que parecen iguales"],
    "patron": ["sucesiones aritméticas con giro", "sucesiones con cuadrados o cubos", "Fibonacci disfrazado",
               "patrones con números primos", "el número que falta en una figura de números", "patrones con letras y números"],
    "palabras": ["máquinas y tiempo de trabajo", "precios y descuentos", "edades", "velocidades y trayectos",
                 "repartos y proporciones", "el bat y la pelota (intuición contra cálculo)", "llenar tanques y llaves"],
    "emoji": ["sistema de ecuaciones con frutas", "sistema con animales", "sistema con comida",
              "sistema con objetos de la escuela", "sistema con trampa de cantidades (racimos, mitades)"],
    "logica": ["caballeros que dicen la verdad y bribones que mienten", "monedas y balanzas", "cajas con etiquetas equivocadas",
               "cruzar el río con restricciones", "relojes y calendarios", "quién es quién (deducción por pistas)",
               "sombreros de colores", "focos e interruptores"],
    "conteo": ["apretones de manos", "caminos en una cuadrícula", "contar cuadrados o triángulos descritos con palabras",
               "formar números con dígitos", "repartir objetos", "partidos de un torneo"],
    "probabilidad": ["dados", "monedas", "cartas", "calcetines en un cajón (peor caso)", "Monty Hall y variantes",
                     "cumpleaños y coincidencias"],
    "error_oculto": ["demostración falsa de 1 = 2", "dividir entre cero escondido", "raíz cuadrada de un negativo",
                     "cancelar mal en una fracción", "una desigualdad multiplicada por un negativo"],
}

# Tipos de gancho del título (el aprendizaje ajusta cuál funciona mejor)
HOOKS = ["pregunta_directa", "parece_facil", "contrarreloj", "sin_calculadora", "debate", "historia"]

# Cómo se elige la mejor de las ideas que propone Claude (pesos de sus autoevaluaciones 1-10)
PESOS_IDEA = {"compartible": 0.30, "curiosidad": 0.20, "comentable": 0.50}
N_IDEAS = 6

# ---------------------------------------------------------------------------
# FONDOS (arte matemático generado en bot/fondos.js). Se elige según palabras del tema;
# si no hay coincidencia, uno de FONDOS_DEFAULT. El aprendizaje también mide qué fondos funcionan mejor.
# ---------------------------------------------------------------------------
FONDOS_POR_TEMA = [
    (["probab", "dado", "moneda", "carta", "calcetin", "monty", "cumplea"], ["probabilidad", "red"]),
    (["primo"], ["primos"]),
    (["fibonacci", "sucesion", "patron", "cuadrados o cubos"], ["espiral", "fractal"]),
    (["cuadricula", "camino", "cuadrado", "triangul"], ["geometria", "rejilla"]),
    (["reloj", "calendario"], ["trig"]),
    (["logic", "caballero", "balanza", "caja", "rio", "sombrero", "foco", "quien", "torneo", "apreton"], ["red", "formulas"]),
    (["velocidad", "tanque", "maquina", "descuento", "precio", "porcentaje"], ["funciones", "formulas"]),
    (["fraccion", "potencia", "raiz", "operacion", "decimal", "parentesis", "comparar", "demostracion",
      "dividir", "desigualdad", "cancelar"], ["formulas", "rejilla", "funciones"]),
]
FONDOS_DEFAULT = ["formulas", "lissajous", "espiral", "fractal", "geometria"]

# ---------------------------------------------------------------------------
# APRENDIZAJE (bot/learn.py y bot/planner.py)
# ---------------------------------------------------------------------------
EXPLORE_P = 0.30        # 30% de los posts prueban algo al azar; 70% aprovechan lo que va funcionando
MIN_DATOS = 12          # posts medidos necesarios antes de confiar en los pesos aprendidos
GAMMA = 2.0             # qué tan fuerte se favorece lo que funciona (1 = proporcional)
SHRINK_K = 2            # prudencia: con pocos datos, los pesos se quedan cerca de 1
COOLDOWN_TEMA = 10      # un tema no se repite en los últimos N posts (si hay alternativas)
MIN_EDAD_H = 48         # horas antes de medir un post
MAX_EDAD_DIAS = 10      # después de esto sus métricas se dan por finales
VENTANA = 60            # posts recientes usados para aprender
# Valor de cada interacción para el puntaje. En una página de comunidad los comentarios pesan más.
PESOS_METRICAS = {"shares": 5, "saved": 3, "follows": 10, "comments": 4, "likes": 0.5}
PESO_ALCANCE = 0.4      # puntaje = 60% calidad de interacción por alcance + 40% alcance relativo

SIZE = (1080, 1350)
