"""COLA DE RETOS: el bot publica retos ya escritos, sin llamar a la API de Claude.

Los retos los escribe una tarea programada de Claude (fuera de GitHub) con exactamente las mismas reglas que
bot/prompts.py, y los deja en state/cola/<tipo>/<id>.json. En cada horario, bot/main.py toma el primero de su
carpeta, lo publica y lo borra. Un archivo por reto para que la tarea programada (que agrega) y el bot (que borra)
nunca choquen al hacer git push.

Uso:
  python -m bot.cola estado                      # cuántos retos quedan por horario
  python -m bot.cola plan --hasta 8 > plan.json  # qué retos faltan (formato, tipo, gancho, tema) según el aprendizaje
  python -m bot.cola instrucciones plan.json     # las instrucciones completas para escribir cada reto del plan
  python -m bot.cola agregar retos.json          # valida y mete los retos escritos a la cola
  python -m bot.cola revisar 3                   # (workflow) si la cola del horario 3 está vacía, avisa y marca SKIP=1

Formato de retos.json: lista de objetos = cada objeto del plan + los campos que pide SCHEMA en bot/prompts.py
(tema, caption, threads, slides=[{text, display}]).
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from . import planner
from . import prompts as P
from .config import FORMAS_THREADS, ROOT, SLOTS
from .contenido import contexto_rendimiento, normalizar

STATE = ROOT / "state"
COLA = STATE / "cola"
CAMPOS_PLAN = ("tipo", "nivel", "formato", "estilo", "hook", "tema_clave")


def _load(name: str, default):
    p = STATE / name
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except json.JSONDecodeError:
        return default


def archivos(tipo: int) -> list:
    d = COLA / str(tipo)
    return sorted(d.glob("*.json")) if d.exists() else []


def pendientes() -> list[dict]:
    """Todos los retos en cola, en orden, como si ya se hubieran publicado (para planear sin repetir)."""
    out = []
    for t in SLOTS:
        for f in archivos(t):
            try:
                out.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                pass
    return out


def estado() -> dict[int, int]:
    return {t: len(archivos(t)) for t in SLOTS}


def plan(hasta: int, seed: int | None = None) -> dict:
    """Para cada horario, planea los retos que faltan para tener `hasta` en cola.
    Usa el mismo planner y el mismo aprendizaje (state/weights.json) que antes usaba el bot en cada post."""
    rng = random.Random(seed)
    weights = _load("weights.json", {})
    historia = _load("posts.json", []) + pendientes()
    faltan = {t: max(0, hasta - n) for t, n in estado().items()}
    items = []
    ultima = None
    while any(faltan.values()):  # intercala horarios como pasa en la vida real (día por día)
        for t in SLOTS:
            if faltan[t] > 0:
                p = planner.elegir(t, historia, weights, rng)
                item = {k: p[k] for k in CAMPOS_PLAN}
                formas = [f for f in FORMAS_THREADS if f != ultima]
                item["forma_threads"] = ultima = rng.choice(formas)
                items.append(item)
                historia.append(item)
                faltan[t] -= 1
    viejos = _load("history.json", [])
    ya = [x for p in _load("posts.json", [])[-120:] + pendientes() for x in (p.get("tema"), p.get("titulo")) if x]
    return {"evitar": (viejos + ya)[-160:], "insights": _load("insights.json", {}), "retos": items}


def _arranque(texto: str, n: int = 3) -> str:
    """Primeras n palabras del texto de Threads, normalizadas (para que los retos no arranquen todos igual)."""
    import re
    import unicodedata
    t = unicodedata.normalize("NFKD", str(texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9ñ]+", t)[:n])


def arranques_recientes() -> list[str]:
    """Arranques de los textos de Threads ya publicados (últimos 40) y de los que están en cola."""
    textos = [p.get("threads_texto") for p in _load("posts.json", [])[-40:]] + [p.get("threads") for p in pendientes()]
    return [a for a in (_arranque(t) for t in textos if t) if a]


def instrucciones(plan_data: dict) -> str:
    """Texto completo para escribir cada reto del plan: el mismo que recibía la API (bot/prompts.py)."""
    partes = [
        "INSTRUCCIONES GENERALES (rol)", P.SYSTEM, "", P.MANUAL, "",
        "No repitas estos retos ya publicados o en cola: " + ("; ".join(plan_data.get("evitar", [])) or "ninguno"),
    ]
    arr = sorted(set(arranques_recientes()))
    partes += ["", "VARIEDAD EN THREADS (Threads borró retos por spam): cada texto de Threads debe sonar distinto a los "
               "demás del lote y a los recientes: cambia el arranque, la longitud, el orden (reto primero o contexto primero) "
               "y el tono. No arranques con las mismas 3 palabras que ninguno de estos: " + ("; ".join(arr) or "ninguno")]
    ctx = contexto_rendimiento(plan_data.get("insights"))
    if ctx:
        partes += ["", ctx]
    partes += ["", "Cada reto debe devolverse con este JSON exacto (más los campos del plan tal cual):", P.SCHEMA,
               "", "Antes de entregar, revisa cada reto con este checklist del verificador:",
               P.VERIFICACION.split("\n\n{contenido}")[0], ""]
    for i, r in enumerate(plan_data["retos"], 1):
        partes += [
            f"===== RETO {i} — horario {r['tipo']} =====",
            "Plan: " + json.dumps(r, ensure_ascii=False),
            "Formato: " + P.FORMATOS[r["formato"]],
            "Tipo de reto: " + P.ESTILOS[r["estilo"]],
            "Verificación de tipo: " + P.ESTILOS_VERIFICACION[r["estilo"]],
            "Dificultad: " + P.NIVELES[r["nivel"]],
            "Verificación de nivel: " + P.NIVEL_VERIFICACION.get(r["nivel"], P.NIVEL_VERIFICACION["default"]),
            "Audiencia: " + P.AUDIENCIAS.get(r["nivel"], P.AUDIENCIAS["default"]),
            "Tema de partida: " + r["tema_clave"],
            "Gancho (cómo arranca el enunciado): " + P.HOOKS.get(r["hook"], r["hook"]),
            "Forma del texto de Threads: " + FORMAS_THREADS.get(r.get("forma_threads"), FORMAS_THREADS["directo"]),
            "",
        ]
    return "\n".join(partes)


def validar(item: dict) -> list[str]:
    """Mismas comprobaciones de forma que hacía el bot con la respuesta de la API (bot/contenido.py → normalizar)."""
    errores = [f"falta '{k}'" for k in CAMPOS_PLAN if not item.get(k)]
    if errores:
        return errores
    if int(item["tipo"]) not in SLOTS:
        return [f"tipo inválido: {item['tipo']}"]
    for k, banco in (("formato", P.FORMATOS), ("estilo", P.ESTILOS), ("nivel", P.NIVELES), ("hook", P.HOOKS)):
        if item[k] not in banco:
            return [f"{k} inválido: {item[k]}"]
    return normalizar(item, item)


def agregar(lista: list[dict]) -> tuple[int, list[str]]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    ok, malos = 0, []
    usados = set(arranques_recientes())
    for i, item in enumerate(lista):
        errores = validar(item)
        a = _arranque(item.get("threads"))
        if not errores and a in usados:
            errores = [f"el texto de threads arranca igual que otro reciente o del lote («{a}…»): cambia el arranque"]
        if not errores:
            usados.add(a)
        if errores:
            malos.append(f"reto {i + 1} ({item.get('tema', '?')}): {'; '.join(errores)}")
            continue
        item.pop("_idea", None)
        d = COLA / str(int(item["tipo"]))
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{stamp}-{i:03d}.json").write_text(json.dumps(item, ensure_ascii=False, indent=1))
        ok += 1
    return ok, malos


def tomar(tipo: int) -> tuple[dict | None, object]:
    """Primer reto válido de la cola de ese horario (los inválidos se descartan). No borra el archivo."""
    for f in archivos(tipo):
        try:
            item = json.loads(f.read_text())
        except json.JSONDecodeError:
            print(f"::warning::Reto ilegible en la cola, se descarta: {f.name}")
            f.unlink()
            continue
        errores = validar(item)
        if errores:
            print(f"::warning::Reto inválido en la cola, se descarta ({f.name}): {errores}")
            f.unlink()
            continue
        return item, f
    return None, None


def revisar(tipo: int) -> bool:
    """Para el workflow: si la cola de ese horario está vacía, deja el aviso y marca SKIP=1 (no se instala nada)."""
    if archivos(tipo):
        print(f"Cola del horario {tipo}: {len(archivos(tipo))} retos")
        return True
    print(f"::warning title=Cola vacía::No hay retos en la cola del horario {tipo}; no se publica.")
    if os.getenv("GITHUB_ENV"):
        with open(os.environ["GITHUB_ENV"], "a") as f:
            f.write("SKIP=1\n")
    return False


def _main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("estado")
    sp = sub.add_parser("plan")
    sp.add_argument("--hasta", type=int, default=8)
    sp.add_argument("--seed", type=int)
    si = sub.add_parser("instrucciones")
    si.add_argument("plan")
    sa = sub.add_parser("agregar")
    sa.add_argument("archivo")
    sr = sub.add_parser("revisar")
    sr.add_argument("tipo", type=int)
    a = ap.parse_args()
    if a.cmd == "estado":
        print(json.dumps(estado()))
    elif a.cmd == "plan":
        print(json.dumps(plan(a.hasta, a.seed), ensure_ascii=False, indent=1))
    elif a.cmd == "instrucciones":
        print(instrucciones(json.loads(open(a.plan).read())))
    elif a.cmd == "agregar":
        ok, malos = agregar(json.loads(open(a.archivo).read()))
        print(f"Agregados: {ok}")
        for m in malos:
            print("RECHAZADO:", m)
        print("Cola:", json.dumps(estado()))
        if malos:
            sys.exit(1)
    elif a.cmd == "revisar":
        revisar(a.tipo)


if __name__ == "__main__":
    _main()
