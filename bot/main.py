"""Uso: python -m bot.main --type 1..6 [--dry]
Cada post es UNA imagen con un mini reto (sin respuesta, sin imagen final).
Instagram y Facebook: la imagen + caption. Threads: solo el reto en texto.
La mezcla de formatos y la dificultad por horario están en bot/config.py → SLOTS.
Los textos NO se generan aquí (no se usa la API de Claude): se toman ya escritos de la cola state/cola/<tipo>/
(ver bot/cola.py). Si la cola de ese horario está vacía, no se publica nada en ese horario."""
import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .config import ROOT, SLOTS, THREADS_ESPERA_MAX_MIN, THREADS_PAUSA_HASTA, THREADS_POR_DIA, threads_horarios
from . import cola, meta, planner
from .render import render_many, slide_html

OUT = ROOT / "out"
STATE = ROOT / "state"


def _load(name: str, default):
    p = STATE / name
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except json.JSONDecodeError:
        return default


def _save(name: str, data) -> None:
    STATE.mkdir(exist_ok=True)
    (STATE / name).write_text(json.dumps(data, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", type=int, required=True, choices=SLOTS)
    ap.add_argument("--dry", action="store_true", help="genera y renderiza pero no publica ni guarda estado")
    a = ap.parse_args()

    posts = _load("posts.json", [])
    content, archivo = cola.tomar(a.type)
    if content is None:
        print(f"::warning title=Cola vacía::No hay retos en la cola del horario {a.type}; no se publica.")
        if os.getenv("GITHUB_ENV"):
            with open(os.environ["GITHUB_ENV"], "a") as f:
                f.write("SKIP=1\n")
        return
    print("Cola:", json.dumps(cola.estado()), "· tomado:", archivo.name)
    weights = _load("weights.json", {})
    plan = planner.elegir(a.type, posts, weights)  # número de reto y semilla del fondo
    plan.update({k: content[k] for k in cola.CAMPOS_PLAN})
    plan["area"] = plan["tema_clave"]
    plan["fondo"] = planner.elegir_fondo(plan["tema_clave"], posts, weights)
    plan["modo"] = "cola"
    print("Plan:", json.dumps(plan, ensure_ascii=False))

    slide = content["slides"][0]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    img = OUT / f"{stamp}-reto{plan['numero']}.png"
    render_many([slide_html(slide, plan["fondo"], plan["semilla"], plan["numero"], plan["nivel"])], [img])
    print("Renderizado:", img.name)
    print("Enunciado:", slide.get("text"))
    print("Caption IG/FB:", content["caption"])
    print("Threads:", content["threads"])

    record = {
        "id": f"{stamp}-t{a.type}", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **{k: plan[k] for k in ("tipo", "nivel", "formato", "estilo", "hook", "tema_clave", "fondo", "numero", "modo")},
        "tema": content.get("tema") or (content.get("_idea") or {}).get("tema", ""),
        "titulo": slide.get("text", "")[:120],
    }
    (OUT / "post.json").write_text(json.dumps({"record": record, "content": content}, ensure_ascii=False, indent=1))
    if a.dry:
        return
    archivo.unlink()  # se confirma en el repo solo si la publicación sale bien (paso "Guardar estado")

    repo, branch = os.environ["GITHUB_REPOSITORY"], os.getenv("MEDIA_BRANCH", "media")
    # El workflow sube out/ a la rama 'media' antes de llamar a --publish-step (ver post.yml)
    (OUT / "urls.json").write_text(json.dumps({
        "image_url": f"https://raw.githubusercontent.com/{repo}/{branch}/{img.name}",
        "caption": content["caption"], "threads": content["threads"], "record": record,
    }, ensure_ascii=False))


def _threads_omitir(tipo: int, hoy: str, mx) -> str:
    """Motivo para NO publicar este reto en Threads (vacío = sí se publica). Ver bot/config.py."""
    if hoy < THREADS_PAUSA_HASTA:
        return f"en pausa hasta {THREADS_PAUSA_HASTA} (avisos de spam)"
    horarios = threads_horarios(hoy)
    if tipo not in horarios:
        return f"hoy solo publican en Threads los horarios {horarios}"
    ya = sum(1 for p in _load("posts.json", []) if p.get("threads_id") and p.get("ts")
             and datetime.fromisoformat(p["ts"]).astimezone(mx).date().isoformat() == hoy)
    if ya >= THREADS_POR_DIA:  # por si un cron atrasado de ayer ya cayó hoy
        return f"ya van {ya} hoy (máximo {THREADS_POR_DIA})"
    return ""


def publish_step() -> None:
    """Segunda fase (tras subir la imagen a la rama media): publica en cada red de forma independiente.
    Si una red falla, las demás se publican igual y el estado se guarda; el fallo queda como advertencia visible.
    Las redes sin secrets configurados se omiten."""
    d = json.loads((OUT / "urls.json").read_text())
    ids: dict[str, str | None] = {"ig": None, "fb": None, "threads": None}
    tareas = {
        "ig": lambda: meta.publish_instagram(d["image_url"], d["caption"]),
        "fb": lambda: meta.publish_facebook(d["image_url"], d["caption"]),
        "threads": lambda: meta.publish_threads(d["threads"]),
    }
    errores = []
    tipo = int((d.get("record") or {}).get("tipo") or 0)
    mx = ZoneInfo("America/Mexico_City")
    hoy = datetime.now(mx).date().isoformat()
    motivo = _threads_omitir(tipo, hoy, mx)
    if motivo:
        tareas.pop("threads")
        print("threads:", motivo, "; se omite")
    for red, publicar in tareas.items():
        if not meta.activo(red):
            print(f"{red}: sin secrets, se omite")
            continue
        if red == "threads" and THREADS_ESPERA_MAX_MIN and os.getenv("GITHUB_ACTIONS"):
            espera = random.randint(0, THREADS_ESPERA_MAX_MIN * 60)  # IG y FB ya salieron: Threads a una hora no fija
            print(f"threads: espera aleatoria de {espera // 60} min")
            time.sleep(espera)
        try:
            ids[red] = publicar()
            print(f"{red}:", ids[red])
        except Exception as e:
            errores.append(f"{red}: {e}")
    for err in errores:
        print(f"::warning title=Fallo de publicación::{err}")
    if any(ids.values()):
        record = d.get("record") or {}
        if ids["threads"]:
            record["threads_texto"] = d["threads"]  # para que los siguientes no arranquen igual (bot/contenido.py)
        record.update({"ig_id": ids["ig"], "fb_id": ids["fb"], "threads_id": ids["threads"],
                       "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        posts = _load("posts.json", [])
        posts.append(record)
        _save("posts.json", posts[-500:])
    else:
        raise RuntimeError("No se publicó en ninguna red: " + (" | ".join(errores) or "no hay redes configuradas"))


if __name__ == "__main__":
    import sys
    if "--publish-step" in sys.argv:
        publish_step()
    else:
        main()
