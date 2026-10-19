"""Configuración central de @miniretxs: mini retos de matemáticas, 6 al día, UNA imagen por post."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v26.0")
THREADS_VERSION = os.getenv("THREADS_VERSION", "v1.0")

HANDLE = os.getenv("PAGE_HANDLE", "@miniretxs")
FOOTER = "UN MINI RETO NUEVO CADA DÍA"   # texto al pie de cada imagen

# Paleta (misma que Mateguapo: negro / blanco / amarillo / rojo)
BRAND = {"bg": "#000000", "fg": "#FFFFFF", "accent": "#ffde59", "alert": "#ff3131"}

# Hashtags que SIEMPRE van en el caption de Instagram/Facebook (Claude agrega 2-4 más)
HASHTAGS_FIJOS = ["#miniretxs", "#retomatematico"]

# THREADS: Threads borró 2 retos por "spam" (18 y 19 oct 2026). Hasta esta fecha (México) solo se publican en Threads
# los retos de estos horarios (3 al día); Instagram y Facebook siguen con los 6.
THREADS_HORARIOS_REDUCIDOS = (1, 3, 5)
THREADS_REDUCIDO_HASTA = "2026-11-09"

# Formas del texto de Threads: cada reto usa una distinta a la del anterior para que no parezcan todos iguales.
FORMAS_THREADS = {
    "directo": "El reto tal cual, sin introducción ni cierre.",
    "minima": "Solo la expresión o sucesión y una pregunta de 2 a 5 palabras.",
    "contexto": "Una situación cotidiana neutra (tienda, cocina, reloj, liga, examen) que plantea el reto. Sin familiares ni amigos como personajes.",
    "dato": "Una frase verdadera de contexto o curiosidad que lleva al reto, sin pistas que regalen la respuesta.",
    "opinion": "Un comentario breve de la página sobre el reto (\"este parece que necesita calculadora, pero no\") y luego el reto.",
}

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
    5: {"nivel": "popular", "formatos": {"operacion": 4, "palabras": 2, "emoji": 1, "patron": 1}},       # 20:00 — para cualquiera
    6: {"nivel": "dificil", "formatos": {"logica": 3, "error_oculto": 2, "conteo": 1, "probabilidad": 1}},  # 22:00
}

# TIPO DE RETO: peso base de cada uno (el aprendizaje los ajusta según el rendimiento).
#   exacto: una sola respuesta correcta · debate: varias respuestas defendibles (genera discusión en comentarios)
ESTILOS = {"exacto": 1, "debate": 1}
SOLO_EXACTO = ["error_oculto"]  # formatos que siempre son exactos (en "¿dónde está el error?" hay un único paso inválido)

# Bancos de temas por formato (se rotan para no repetir)
TEMAS = {
    "operacion": ["leyes de exponentes con trampa", "radicales y racionalización", "logaritmos que se simplifican",
                  "productos notables y diferencia de cuadrados", "fracciones algebraicas", "potencias de números negativos",
                  "jerarquía con potencias y raíces", "expresiones que se cancelan con ingenio"],
    "cual_mayor": ["comparar potencias con bases y exponentes distintos", "comparar sumas de raíces", "comparar logaritmos",
                   "comparar porcentajes encadenados", "comparar expresiones que parecen iguales"],
    "patron": ["sucesiones cuadráticas (diferencias de segundo orden)", "sucesiones geométricas con giro", "Fibonacci disfrazado",
               "patrones con números primos", "sucesiones con cuadrados, cubos o factoriales", "sucesiones recursivas"],
    "palabras": ["trabajo conjunto (máquinas, llaves, personas)", "descuentos y aumentos sucesivos", "edades con sistema de ecuaciones",
                 "velocidad media de ida y vuelta", "mezclas y concentraciones", "el bat y la pelota (intuición contra álgebra)",
                 "áreas y perímetros con ecuación"],
    "emoji": ["sistema con frutas y productos", "sistema con animales y potencias", "sistema con comida y divisiones",
              "sistema no lineal con objetos de la escuela", "sistema con trampa de cantidades (racimos, mitades)"],
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

# Temas del nivel "popular" (horario para cualquiera). Sustituyen a TEMAS en ese horario.
TEMAS_POPULAR = {
    "operacion": ["jerarquía de operaciones con trampa (multiplicar/dividir antes que sumar)", "negativos que engañan",
                  "fracciones sencillas", "porcentajes que engañan", "potencias pequeñas y signos", "operaciones con ceros y unos"],
    "palabras": ["el bat y la pelota", "5 máquinas, 5 piezas, 5 minutos", "edades sencillas", "precios y vueltos",
                 "caracol que sube un pozo", "repartos que engañan"],
    "emoji": ["sistema de frutas con sumas", "sistema con trampa de cantidades (racimos, mitades)", "sistema con animales"],
    "patron": ["sucesión sencilla con giro", "el número que sigue en un patrón de dobles", "sucesión que suma los dos anteriores"],
    "cual_mayor": ["comparar fracciones simples", "comparar porcentajes", "comparar decimales que engañan"],
}

# Tipos de gancho (cómo arranca el enunciado) (el aprendizaje ajusta cuál funciona mejor)
HOOKS = ["pregunta_directa", "parece_facil", "contrarreloj", "sin_calculadora", "debate", "historia", "no_es_x"]

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
