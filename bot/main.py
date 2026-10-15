"""Uso: python -m bot.main --type 1..6 [--dry]
Cada post es UNA imagen con un mini reto (sin respuesta, sin imagen final).
Instagram y Facebook: la imagen + caption. Threads: solo el reto en texto.
La mezcla de formatos y la dificultad por horario están en bot/config.py → SLOTS."""
import argparse
import json
import os
from datetime import datetime, timezone
from .config import ROOT, SLOTS
from . import llm, meta, planner
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


def _evitar(posts: list[dict]) -> list[str]:
    """Retos ya publicados, para no repetirlos."""
    viejos = _load("history.json", [])
    nuevos = [x for p in posts[-120:] for x in (p.get("tema"), p.get("titulo")) if x]
    return (viejos + nuevos)[-160:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", type=int, required=True, choices=SLOTS)
    ap.add_argument("--dry", action="store_true", help="genera y renderiza pero no publica ni guarda estado")
    a = ap.parse_args()

    posts = _load("posts.json", [])
    plan = planner.elegir(a.type, posts, _load("weights.json", {}))
    print("Plan:", json.dumps(plan, ensure_ascii=False))
    content = llm.generate(plan, _evitar(posts), _load("insights.json", {}))
    print("Idea elegida:", json.dumps(content.get("_idea"), ensure_ascii=False))

    slide = content["slides"][0]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    img = OUT / f"{stamp}-reto{plan['numero']}.png"
    render_many([slide_html(slide, plan["fondo"], plan["semilla"], plan["numero"], plan["nivel"])], [img])
    print("Renderizado:", img.name)
    print("Título:", slide.get("title"))
    print("Caption IG/FB:", content["caption"])
    print("Threads:", content["threads"])

    record = {
        "id": f"{stamp}-t{a.type}", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **{k: plan[k] for k in ("tipo", "nivel", "formato", "estilo", "hook", "tema_clave", "fondo", "numero", "modo")},
        "tema": content.get("tema") or (content.get("_idea") or {}).get("tema", ""),
        "titulo": slide.get("title", ""),
        "puntaje_idea": (content.get("_idea") or {}).get("_puntaje"),
    }
    (OUT / "post.json").write_text(json.dumps({"record": record, "content": content}, ensure_ascii=False, indent=1))
    if a.dry:
        return

    repo, branch = os.environ["GITHUB_REPOSITORY"], os.getenv("MEDIA_BRANCH", "media")
    # El workflow sube out/ a la rama 'media' antes de llamar a --publish-step (ver post.yml)
    (OUT / "urls.json").write_text(json.dumps({
        "image_url": f"https://raw.githubusercontent.com/{repo}/{branch}/{img.name}",
        "caption": content["caption"], "threads": content["threads"], "record": record,
    }, ensure_ascii=False))


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
    for red, publicar in tareas.items():
        if not meta.activo(red):
            print(f"{red}: sin secrets, se omite")
            continue
        try:
            ids[red] = publicar()
            print(f"{red}:", ids[red])
        except Exception as e:
            errores.append(f"{red}: {e}")
    for err in errores:
        print(f"::warning title=Fallo de publicación::{err}")
    if any(ids.values()):
        record = d.get("record") or {}
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
