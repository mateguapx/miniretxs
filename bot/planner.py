"""Decide QUÉ reto publicar en cada post: formato, gancho, tema y fondo.
- 70% de las veces aprovecha lo que mejor ha funcionado (pesos de state/weights.json, calculados por bot/learn.py).
- 30% explora al azar para seguir descubriendo cosas nuevas.
- Enfriamiento: no repite un tema usado en los últimos posts, para que el contenido no sea monótono."""
import random
import unicodedata
from .config import (TEMAS_POPULAR, COOLDOWN_TEMA, ESTILOS, EXPLORE_P, SOLO_EXACTO, FONDOS_DEFAULT, FONDOS_POR_TEMA, GAMMA, HOOKS, MIN_DATOS, SLOTS, TEMAS)


def _sin_acentos(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))


def fondos_para(texto: str) -> list[str]:
    """Motivos de fondo que encajan con el tema (bot/config.py → FONDOS_POR_TEMA)."""
    t = _sin_acentos(texto)
    out: list[str] = []
    for claves, motivos in FONDOS_POR_TEMA:
        if any(c in t for c in claves):
            out += [m for m in motivos if m not in out]
    return out or list(FONDOS_DEFAULT)


def _factor(weights: dict, dim: str, valor: str) -> float:
    return float(weights.get(dim, {}).get(valor, 1.0))


def _elegir(opciones: dict[str, float], weights: dict, dim: str, explorar: bool, usar_pesos: bool,
            rng: random.Random) -> str:
    """opciones: {valor: peso_base}. Explorar = uniforme; si no, peso_base × factor_aprendido^GAMMA."""
    claves = list(opciones)
    if explorar:
        return rng.choice(claves)
    pesos = [opciones[k] * (_factor(weights, dim, k) ** GAMMA if usar_pesos else 1.0) for k in claves]
    return rng.choices(claves, weights=pesos, k=1)[0]


def _sin_recientes(candidatos: list[str], recientes: list) -> list[str]:
    libres = [c for c in candidatos if c not in recientes]
    return libres or candidatos


def elegir_fondo(tema_clave: str, posts: list[dict], weights: dict, rng: random.Random | None = None,
                 explorar: bool = False) -> str:
    """Motivo de fondo para un tema, sin repetir el del post anterior si hay alternativas."""
    rng = rng or random.Random()
    usar_pesos = int(weights.get("n", 0)) >= MIN_DATOS
    candidatos = _sin_recientes(fondos_para(tema_clave), [p.get("fondo") for p in posts[-1:]])
    return _elegir({f: 1.0 for f in candidatos}, weights, "fondo", explorar, usar_pesos, rng)


def elegir(tipo: int, posts: list[dict], weights: dict, rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    slot = SLOTS[tipo]
    usar_pesos = int(weights.get("n", 0)) >= MIN_DATOS
    explorar = usar_pesos and rng.random() < EXPLORE_P
    recientes = [p.get("tema_clave") for p in posts[-COOLDOWN_TEMA:]]
    formatos_recientes = [p.get("formato") for p in posts[-1:]]

    # 1) Formato (evita repetir el del post anterior si el horario tiene alternativas)
    opciones = {f: w for f, w in slot["formatos"].items() if f not in formatos_recientes} or dict(slot["formatos"])
    formato = _elegir(opciones, weights, "formato", explorar, usar_pesos, rng)
    # 2) Tipo de reto: exacto o de debate
    estilo = "exacto" if formato in SOLO_EXACTO else _elegir(dict(ESTILOS), weights, "estilo", explorar, usar_pesos, rng)
    # 3) Tema
    banco = TEMAS_POPULAR.get(formato) if slot["nivel"] == "popular" else None
    tema_clave = _elegir({t: 1.0 for t in _sin_recientes(banco or TEMAS[formato], recientes)}, weights, "tema",
                         explorar, usar_pesos, rng)
    # 4) Gancho
    hook = _elegir({h: 1.0 for h in HOOKS}, weights, "hook", explorar, usar_pesos, rng)
    # 5) Fondo según el tema (sin repetir el del post anterior si hay alternativas)
    fondo = elegir_fondo(tema_clave, posts, weights, rng, explorar)
    return {
        "tipo": tipo, "nivel": slot["nivel"], "formato": formato, "estilo": estilo, "hook": hook,
        "tema_clave": tema_clave, "area": tema_clave, "fondo": fondo,
        "numero": max([int(p.get("numero") or 0) for p in posts], default=0) + 1, "semilla": rng.randrange(1, 10**6),
        "modo": "explorar" if explorar else ("explotar" if usar_pesos else "inicial"),
    }
