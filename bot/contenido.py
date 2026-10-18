"""Comprobaciones de forma de cada reto (antes vivían en bot/llm.py, junto a la API de Claude).
Los retos ya no los genera la API: los escribe la tarea programada semanal y entran a la cola (bot/cola.py).
Aquí se aplican exactamente las mismas comprobaciones que el bot aplicaba a la respuesta de la API."""
import re
from . import prompts as P
from .config import HASHTAGS_FIJOS

THREADS_MAX = 500  # límite de caracteres de un post de texto en Threads


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


def _hashtags(caption: str) -> str:
    """Garantiza los hashtags fijos al final del caption."""
    faltan = [h for h in HASHTAGS_FIJOS if h.lower() not in caption.lower()]
    return (caption.rstrip() + " " + " ".join(faltan)) if faltan else caption


def normalizar(plan: dict, content: dict) -> list[str]:
    """Ajusta detalles de forma y devuelve los problemas que obligan a reescribir."""
    slides = content.get("slides")
    if not isinstance(slides, list) or len(slides) != 1 or not isinstance(slides[0], dict):
        return ["El campo slides debe ser una lista con exactamente 1 objeto"]
    s = slides[0]
    s.pop("title", None)
    for k in ("text", "display"):
        s[k] = str(s.get(k) or "").strip()
    s["text"] = re.sub(r"^\s*reto\s*(#\s*\d+)?\s*[:\-–—]\s*", "", s["text"], flags=re.I)
    s["layout"] = "reto"
    if not s["text"]:
        return ["Falta el enunciado del reto (text)"]
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
