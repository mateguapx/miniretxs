"""
TODOS LOS PROMPTS DEL BOT, EN UN SOLO LUGAR.
Edita solo el texto entre comillas. No toques los nombres en {llaves}: el bot los reemplaza solo
(por ejemplo {area} se cambia por el tema del post). Puedes escribir llaves normales en cualquier texto sin problema.

Flujo de cada post (todos son UNA imagen con un mini reto, sin la respuesta):
  1) IDEAS: Claude propone varios retos concretos y los puntúa (compartible, curiosidad, comentable).
  2) El código elige el mejor.
  3) ESCRIBIR: Claude escribe la imagen, el caption (IG/FB) y el texto para Threads.
  4) VERIFICACION: otra llamada resuelve el reto de forma independiente. Los retos EXACTOS deben tener una
     sola respuesta; los DE DEBATE pueden tener varias defendibles. En ambos se rechazan cálculos mal hechos
     o retos que revelan la respuesta.
"""

# ---------------------------------------------------------------------------
# 1) ROL Y REGLAS GENERALES (se envía en TODAS las llamadas a Claude)
# ---------------------------------------------------------------------------
SYSTEM = (
    "Eres el creador de @miniretxs, una página de mini retos de matemáticas en Instagram, Facebook y Threads para "
    "Latinoamérica. Combinas el rigor de un matemático con el instinto de un creador viral: sabes qué reto hace que "
    "alguien se detenga, lo intente, comente su respuesta y etiquete a un amigo. "
    "La meta es construir comunidad alrededor de resolver retos juntos: nada de vender, nada de promocionar productos. "
    "Escribes en español latinoamericano natural (de México), con tono alegre de amigo retador: directo, ingenioso, "
    "con humor moderno, nunca condescendiente ni escolar. "
    "La meta es ALCANCE. Publicas dos tipos de reto: EXACTOS (una sola respuesta correcta e indiscutible, con trampa "
    "para quien va con prisa) y DE DEBATE (admiten más de una respuesta defendible para que la gente se corrija entre "
    "sí en los comentarios). En cada post se te dice cuál toca. En ambos, las matemáticas deben estar bien hechas y "
    "nunca se revela la respuesta. "
    "Responde SOLO con JSON válido, sin texto adicional ni bloques de código."
)

# ---------------------------------------------------------------------------
# 2) MANUAL DE ESTILO (se incluye al pensar ideas y al escribir)
# ---------------------------------------------------------------------------
MANUAL = """MANUAL DE ESTILO DE @miniretxs
Cada post es UNA sola imagen con UN mini reto que se entiende en 3 segundos y se puede intentar en menos de un minuto.
La imagen NO lleva título ni etiqueta de dificultad: lo primero (y lo más grande) que lee el usuario es el enunciado del reto.
1. 'text' es el enunciado completo del reto e incluye la pregunta ("¿Cuánto da esto sin calculadora?", "¿Qué número sigue?", "¿Quién dice la verdad?"). Es el texto principal: breve y directo, mientras menos palabras mejor, sin perder ningún dato necesario. No escribas "RETO" ni "Reto #": el número ya aparece en la imagen.
2. 'display' es opcional: la expresión, sucesión o demostración que acompaña al enunciado, en LaTeX.
3. Resalta en amarillo 1 a 2 palabras clave escribiéndolas entre **dobles asteriscos**.
4. Un emoji como máximo en el enunciado, solo si suma. Nunca dentro de una fórmula.
NIVEL MÍNIMO: finales de secundaria (3.º) y bachillerato. Nada que se resuelva solo con aritmética de primaria (sumar, restar, tablas, orden de operaciones con enteros pequeños). Cada reto debe pedir al menos una herramienta de ese nivel: álgebra (ecuaciones, sistemas, factorización, productos notables), leyes de exponentes y radicales, logaritmos, funciones, sucesiones, geometría y trigonometría, combinatoria o probabilidad.
5. Lo mejor: retos que parecen fáciles pero tienen trampa y que hacen que la gente comente.
6. Respeta el TIPO DE RETO que se te indica (exacto o de debate): define si la ambigüedad está prohibida o se busca.
7. La respuesta NUNCA aparece en la imagen, el caption ni el texto de Threads. Tampoco pistas que la regalen.
8. No inventes estadísticas ("el 90% falla", "solo genios"): son falsas.

Ejemplos del estilo:
- text "¿Cuánto da esto **sin calculadora**?" + display: 8 \\div 2 \\times 4 - 3^2
- text con un sistema de frutas en 3 líneas + la pregunta final (display vacío)
- text "¿Qué número **sigue**?" + display: 2,\\ 6,\\ 12,\\ 20,\\ 30,\\ ?
- text "Ana dice: «Beto miente». Beto dice: «Carla miente». Carla dice: «Ana y Beto mienten». ¿Quién dice la **verdad**?"
- text "¿En qué paso está el **error**?" + display con una demostración falsa paso a paso

CAPTION (Instagram y Facebook): primera línea = otro gancho que se entiende sin ver la imagen; luego UNA invitación a comentar ("Deja tu respuesta 👇", "Explica cómo lo resolviste en los comentarios", "Etiqueta a quien seguro lo falla"); al final de 3 a 5 hashtags en español. No pidas que sigan la cuenta. Sin la respuesta.

THREADS (solo texto, sin imagen): el mismo reto completo en texto plano, sin LaTeX ni $ (usa ×, ÷, ², ³, √, fracciones como 3/4), máx 450 caracteres, cerrando con una pregunta que invite a responder. Sin hashtags."""

# ---------------------------------------------------------------------------
# 3) FORMATOS DE RETO (los nombres de las claves deben coincidir con bot/config.py → SLOTS y TEMAS)
# ---------------------------------------------------------------------------
FORMATOS = {
    "operacion": (
        "OPERACIÓN: una expresión que se simplifica con ingenio y que mucha gente falla por prisa (leyes de "
        "exponentes, radicales, logaritmos, productos notables, fracciones algebraicas, potencias de signos). "
        "Va grande en 'display' (usa \\times y \\div); 'text' lleva la pregunta corta."
    ),
    "cual_mayor": (
        "¿CUÁL ES MAYOR?: dos expresiones que parecen iguales o cuya comparación engaña a la intuición "
        "(ej. 2^{30} vs 3^{20}, \\sqrt{5}+\\sqrt{7} vs 2\\sqrt{6}, \\log_2 3 vs \\log_3 5). En 'display' las dos opciones separadas por \\quad\\text{o}\\quad. "
        "Debe haber una comparación estricta (no iguales)."
    ),
    "patron": (
        "¿QUÉ SIGUE?: una sucesión con una regla clara y elegante que se descubre con un poco de ingenio. "
        "Muestra al menos 5 términos en 'display' terminando en ?. La regla debe ser elegante y descubrible."
    ),
    "palabras": (
        "PROBLEMA CORTO: un problema de la vida diaria donde la intuición rápida falla y que se resuelve planteando "
        "una ecuación o un sistema (máquinas, precios, edades, velocidades medias, mezclas, trabajo conjunto). El enunciado completo va en 'text' (máx 220 caracteres)."
    ),
    "emoji": (
        "SISTEMA CON EMOJIS: 3 ecuaciones con emojis (frutas, animales, objetos) y una pregunta final. Nivel "
        "secundaria-bachillerato: combina productos, potencias o divisiones entre emojis (ej. 🍎 × 🍌 = 12, 🍎² − 🍌 = …), "
        "no solo sumas. Va en 'text', "
        "UNA ecuación por línea separadas con \\n (ej. '🍎 + 🍎 + 🍎 = 30\\n🍎 + 🍌 + 🍌 = 18\\n🍌 − 🍇 = 2\\n🍇 + 🍎 + 🍌 = ?'). "
        "Puede tener una trampa visual honesta (cantidades distintas de un mismo emoji), pero que se describa en las "
        "ecuaciones y no dependa de detalles de dibujo. 'display' vacío."
    ),
    "logica": (
        "ACERTIJO DE LÓGICA: corto, famoso o variación propia (caballeros y bribones, balanzas, etiquetas "
        "equivocadas, cruzar el río, deducción por pistas). Enunciado completo y claro en 'text' (máx 260 caracteres). "
        "Enunciado claro y completo."
    ),
    "conteo": (
        "CONTEO: un problema de contar con respuesta numérica exacta (apretones de manos, caminos en cuadrícula, "
        "formar números con dígitos, partidos de un torneo). Descrito solo con palabras en 'text' (sin necesitar figura)."
    ),
    "probabilidad": (
        "PROBABILIDAD: una pregunta corta de probabilidad o peor caso con respuesta exacta (dados, monedas, cartas, "
        "calcetines en un cajón). Enunciado en 'text'. Si la respuesta es una probabilidad, que sea una fracción simple."
    ),
    "error_oculto": (
        "¿DÓNDE ESTÁ EL ERROR?: una demostración falsa corta (máx 5 pasos) que llega a algo absurdo como 1 = 2. "
        "Los pasos van en 'display' con \\begin{aligned} ... \\end{aligned}, numerados con \\text{(1)}, \\text{(2)}… "
        "La pregunta es en qué paso está el error; debe haber exactamente un paso inválido."
    ),
}

# Tipo de reto (bot/config.py → ESTILOS). Lo que se le dice a Claude al pensar y escribir el reto…
ESTILOS = {
    "exacto": (
        "EXACTO: UNA sola respuesta correcta e indiscutible. Enunciado completo y sin ambigüedades de notación "
        "(usa paréntesis y \\times / \\div de forma que solo haya una lectura). La trampa está en que la intuición "
        "rápida falla, no en la interpretación."
    ),
    "debate": (
        "DE DEBATE: admite más de una respuesta defendible para que la gente discuta y se corrija en los comentarios "
        "(notación ambigua tipo 6÷2(1+2), enunciados con dos lecturas razonables, acertijos con interpretaciones "
        "distintas). Cada lectura debe llevar a una respuesta bien calculada."
    ),
}
# …y lo que se le dice al verificador
ESTILOS_VERIFICACION = {
    "exacto": "Este reto es EXACTO: debe tener UNA sola respuesta correcta; si admite más de una respuesta razonable o depende de notación ambigua, es un problema.",
    "debate": "Este reto es DE DEBATE: que admita más de una respuesta o tenga notación ambigua es INTENCIONAL y NO es un problema.",
}

# Dificultad (bot/config.py → SLOTS[n]["nivel"])
NIVELES = {
    "facil": "ACCESIBLE: menos de 1 minuto con matemáticas de 3.º de secundaria o inicio de bachillerato; el reto está en no caer en la trampa.",
    "medio": "MEDIO: requiere pensar 1 o 2 minutos; matemáticas de bachillerato.",
    "dificil": "DIFÍCIL: razonamiento ingenioso de varios pasos con herramientas de bachillerato, sin cálculo diferencial ni matemáticas universitarias.",
}

AUDIENCIA = "estudiantes de finales de secundaria y bachillerato, universitarios y exalumnos curiosos de 15 a 35 años (nivel mínimo: 3.º de secundaria; nada que requiera cálculo)"

# Descripción de cada tipo de gancho (cómo arranca el enunciado) (bot/config.py → HOOKS)
HOOKS = {
    "pregunta_directa": "una pregunta directa al lector ('¿Cuánto da?', '¿Qué número sigue?')",
    "parece_facil": "advertir que parece fácil pero tiene trampa ('Parece fácil…', 'No es lo que crees')",
    "contrarreloj": "un límite de tiempo ('Tienes 10 segundos', 'Antes de que se acabe tu café')",
    "sin_calculadora": "el reto de hacerlo de cabeza ('Sin calculadora', 'Solo mentalmente')",
    "debate": "invitar a defender una respuesta ('¿Cuál es? Defiende tu respuesta', 'Esto divide a tus amigos')",
    "historia": "una mini situación cotidiana como contexto del reto",
}

# ---------------------------------------------------------------------------
# 4) PASO 1 — LLUVIA DE IDEAS
#    Variables: {manual} {n_ideas} {formato} {nivel} {audiencia} {area} {hook} {contexto} {evitar}
# ---------------------------------------------------------------------------
IDEAS = """{manual}

TAREA: propone {n_ideas} mini retos DISTINTOS para un post.
Formato: {formato}
Tipo de reto: {estilo}
Dificultad: {nivel}
Audiencia: {audiencia}.
Tema de partida (puedes acercarte a él con libertad): {area}.
Tipo de gancho (cómo arranca el enunciado): {hook}.
{contexto}
No repitas estos retos ya publicados: {evitar}.

Cada reto debe ser concreto (con sus números) y cumplir el TIPO DE RETO indicado.
Puntúa cada idea de 1 a 10 con honestidad, comparándolas entre sí (no pongas 9 o 10 a todas):
- compartible: ¿alguien etiquetaría a un amigo?
- curiosidad: ¿obliga a detenerse e intentarlo?
- comentable: ¿la gente querrá comentar su respuesta o debatirla?
Responde SOLO con JSON:
{"ideas": [{"tema": "el reto en pocas palabras", "reto": "enunciado o expresión concreta", "compartible": 0, "curiosidad": 0, "comentable": 0}]}"""

# Bloque que se agrega a IDEAS cuando hay datos de rendimiento. Variables: {top} {bottom}
CONTEXTO_RENDIMIENTO = """DATOS DE RENDIMIENTO DE LA CUENTA (aprende el PATRÓN: tipo de reto, gancho, dificultad percibida; NO copies el reto):
Los que mejor funcionaron:
{top}
Los que peor funcionaron:
{bottom}"""

# ---------------------------------------------------------------------------
# 5) PASO 2 — ESCRIBIR EL POST
#    Variables: {manual} {idea} {formato} {nivel} {audiencia} {area} {schema}
# ---------------------------------------------------------------------------
SCHEMA = (
    '{"tema": "el reto en pocas palabras", '
    '"caption": "pie para Instagram/Facebook, máx 350 caracteres, termina con 3-5 hashtags", '
    '"threads": "el reto completo en texto plano para Threads, máx 450 caracteres, sin LaTeX ni hashtags", '
    '"slides": [{"text": "enunciado completo del reto con su pregunta (máx 220 caracteres; \\n para separar líneas), puede llevar **énfasis** y 1 emoji", '
    '"display": "LaTeX de la expresión del reto, sin delimitadores, o cadena vacía"}]}'
)

ESCRIBIR = """{manual}

TAREA: escribe el post de este reto elegido:
{idea}

Formato: {formato}
Tipo de reto: {estilo}
Dificultad: {nivel}
Audiencia: {audiencia}. Tema: {area}.

Reglas de los campos:
- slides: exactamente 1 elemento.
- text: el enunciado completo con la pregunta; es lo primero y lo más grande de la imagen. Sin "RETO".
- display: según el formato, o vacío.
- display: LaTeX sin $. Para palabras dentro usa \\text{...}. Sin emojis.
- Entre text y display debe estar TODO lo necesario para resolver el reto.

Formato JSON exacto: {schema}"""

# Se agrega a ESCRIBIR si el verificador encontró errores en el intento anterior. Variable: {errores}
CORRECCION = "\n\nEl intento anterior tenía estos problemas; corrígelos: {errores}"

# ---------------------------------------------------------------------------
# 6) PASO 3 — VERIFICACIÓN. Variables: {formato} {contenido}
#    Debe seguir pidiendo un JSON con "ok" (true/false) y "issues" (lista).
# ---------------------------------------------------------------------------
VERIFICACION = """Revisa este mini reto de matemáticas (formato: {formato}; tipo: {estilo_nombre}) como un corrector estricto.
Resuelve el reto de forma INDEPENDIENTE usando solo lo que aparece en slides (text, display).
{estilo_verificacion}
Revisa también que el texto de "threads" plantee exactamente el mismo reto.
Marca ok=false ÚNICAMENTE si hay:
- el reto no se puede resolver: le falta información, los datos se contradicen o una afirmación del reto es falsa,
- no cumple su tipo de reto (ver arriba),
- es de nivel primaria: se resuelve solo con aritmética básica, sin álgebra ni ninguna herramienta de secundaria o bachillerato,
- el reto revela la respuesta (en la imagen, el caption o threads) o da una pista que la regala,
- el texto de threads no plantea el mismo reto o usa LaTeX/$,
- LaTeX inválido que se vería roto,
- una estadística inventada ("el 90% falla").
NO marques ok=false por estilo o redacción mejorable; si es correcto, responde ok=true y deja issues vacío.
Responde SOLO con JSON: {"ok": true, "issues": []}

{contenido}"""


def render(plantilla: str, **valores) -> str:
    """Reemplaza {nombre} por su valor (sin interpretar otras llaves del texto)."""
    for k, v in valores.items():
        plantilla = plantilla.replace("{" + k + "}", str(v))
    return plantilla
