"""Generación y verificación de los mini retos con la API de Claude. Los textos de los prompts viven en bot/prompts.py.
Flujo: ideas -> elegir la mejor -> escribir -> verificar (con reintentos y, si hace falta, la segunda mejor idea)."""
import json
import re
import anthropic
from . import prompts as P
from .config import HASHTAGS_FIJOS, MODEL, N_IDEAS, PESOS_IDEA

_client = None
THREADS_MAX = 500  # límite de caracteres de un post de texto en Threads


def _cli():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
    return _client


def _ask(user: str, max_tokens: int = 8000) -> str:
    r = _cli().messages.create(
        model=MODEL, max_tokens=max_tokens, system=P.SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    # La respuesta puede traer bloques de razonamiento antes del texto: se concatenan solo los de tipo "text".
    text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    if not text.strip():
        raise RuntimeError(f"Respuesta sin texto (stop_reason={r.stop_reason}); sube max_tokens.")
    return text


def _json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            return json.loads(text[a:b + 1])
        raise


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def contexto_rendimiento(insights: dict | None) -> str:
    """Convierte state/insights.json en el bloque de texto para el prompt de ideas."""
    if not insights or not insights.get("top"):
        return ""

    def linea(p: dict) -> str:
        m = p.get("metricas", {})
        return (f"- \"{p.get('titulo', '')}\" (formato {p.get('formato')}, tipo {p.get('estilo')}, nivel {p.get('nivel')}, gancho {p.get('hook')}, "
                f"reto {p.get('tema')}; alcance {m.get('reach', '?')}, comentarios {m.get('comments', '?')}, "
                f"compartidos {m.get('shares', '?')}, guardados {m.get('saved', '?')})")

    return P.render(P.CONTEXTO_RENDIMIENTO,
                    top="\n".join(linea(p) for p in insights["top"]),
                    bottom="\n".join(linea(p) for p in insights.get("bottom", [])) or "- (sin datos)")


def _comun(plan: dict) -> dict:
    return dict(manual=P.MANUAL, formato=P.FORMATOS[plan["formato"]], estilo=P.ESTILOS[_estilo(plan)],
                nivel=P.NIVELES[plan["nivel"]], audiencia=P.AUDIENCIA, area=plan["area"])


def _estilo(plan: dict) -> str:
    return plan.get("estilo") if plan.get("estilo") in P.ESTILOS else "exacto"


def ideas(plan: dict, evitar: list[str], contexto: str = "") -> list[dict]:
    """Pide N ideas y las devuelve ordenadas de mejor a peor según config.PESOS_IDEA."""
    prompt = P.render(P.IDEAS, n_ideas=N_IDEAS, hook=P.HOOKS.get(plan["hook"], plan["hook"]),
                      contexto=contexto, evitar="; ".join(evitar[-80:]) or "ninguno", **_comun(plan))
    data = _json(_ask(prompt, max_tokens=6000))
    lista = [i for i in data.get("ideas", []) if isinstance(i, dict) and i.get("reto")]
    if not lista:
        raise RuntimeError("Claude no devolvió ideas válidas")
    for i in lista:
        i["_puntaje"] = round(sum(_num(i.get(k)) * peso for k, peso in PESOS_IDEA.items()), 2)
    return sorted(lista, key=lambda i: i["_puntaje"], reverse=True)


def _hashtags(caption: str) -> str:
    """Garantiza los hashtags fijos al final del caption."""
    faltan = [h for h in HASHTAGS_FIJOS if h.lower() not in caption.lower()]
    return (caption.rstrip() + " " + " ".join(faltan)) if faltan else caption


def _normalizar(plan: dict, content: dict) -> list[str]:
    """Ajusta detalles de forma y devuelve los problemas que obligan a reescribir."""
    slides = content.get("slides")
    if not isinstance(slides, list) or len(slides) != 1 or not isinstance(slides[0], dict):
        return ["El campo slides debe ser una lista con exactamente 1 objeto"]
    s = slides[0]
    for k in ("title", "text", "display"):
        s[k] = str(s.get(k) or "").strip()
    s["title"] = re.sub(r"^\s*reto\s*(#\s*\d+)?\s*[:\-–—]?\s*", "", s["title"], flags=re.I)
    s["layout"] = "reto"
    if not s["title"]:
        return ["Falta el título (title) de la imagen"]
    if not (s["text"] or s["display"]):
        return ["El reto debe ir en 'text' o en 'display'"]
    if plan["formato"] == "error_oculto" and not s["display"]:
        return ["En el formato error_oculto, 'display' debe tener la demostración falsa"]
    if not str(content.get("caption") or "").strip():
        return ["Falta el caption"]
    content["caption"] = _hashtags(str(content["caption"]).strip())
    th = str(content.get("threads") or "").strip()
    if not th:
        return ["Falta el texto para Threads (threads)"]
    if "$" in th or "\\" in th:
        return ["El texto de threads no puede llevar LaTeX ni $"]
    if len(th) > THREADS_MAX:
        return [f"El texto de threads tiene {len(th)} caracteres; máximo {THREADS_MAX - 50}"]
    content["threads"] = th
    return []


def _verify(plan: dict, content: dict) -> dict:
    limpio = {k: v for k, v in content.items() if not k.startswith("_")}
    prompt = P.render(P.VERIFICACION, formato=plan["formato"], estilo_nombre=_estilo(plan),
                      estilo_verificacion=P.ESTILOS_VERIFICACION[_estilo(plan)],
                      contenido=json.dumps(limpio, ensure_ascii=False))
    return _json(_ask(prompt, max_tokens=8000))


def write(plan: dict, idea: dict, retries: int = 3) -> tuple[dict | None, list[str]]:
    idea_txt = json.dumps({k: v for k, v in idea.items() if not k.startswith("_")}, ensure_ascii=False)
    base = P.render(P.ESCRIBIR, idea=idea_txt, schema=P.SCHEMA, **_comun(plan))
    issues: list[str] = []
    for _ in range(retries):
        extra = P.render(P.CORRECCION, errores=issues) if issues else ""
        try:
            content = _json(_ask(base + extra))
        except (json.JSONDecodeError, ValueError):
            issues = ["La respuesta no era JSON válido; responde solo con el JSON pedido"]
            continue
        issues = _normalizar(plan, content)
        if issues:
            continue
        check = _verify(plan, content)
        if check.get("ok"):
            return content, []
        issues = check.get("issues") or ["error no especificado"]
    return None, issues


def generate(plan: dict, evitar: list[str], insights: dict | None = None) -> dict:
    """plan viene de bot/planner.py. Devuelve el contenido verificado, con la idea elegida en '_idea'."""
    # Los posts de exploración no ven los datos de rendimiento, para no sesgarlos hacia lo de siempre.
    contexto = contexto_rendimiento(insights) if plan.get("modo") != "explorar" else ""
    candidatas = ideas(plan, evitar, contexto)
    ultimo: list[str] = []
    for idea, intentos in zip(candidatas[:3], (3, 2, 2)):  # mejor idea con 3 intentos; luego las siguientes con 2
        content, ultimo = write(plan, idea, retries=intentos)
        if content:
            content["_idea"] = {k: v for k, v in idea.items() if k != "respuesta"}
            content["_ideas_descartadas"] = [i.get("tema") for i in candidatas if i is not idea]
            return content
        print(f"Idea descartada tras verificación: {idea.get('tema')} -> {ultimo}")
    raise RuntimeError(f"No se obtuvo contenido verificado: {ultimo}")
