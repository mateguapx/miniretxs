"""Aprendizaje automático: mide los posts publicados y ajusta qué publicar.
Uso: python -m bot.learn   (corre 1 vez al día con .github/workflows/learn.yml)

1) Mide cada post de Instagram con más de 48 h (alcance, compartidos, guardados, seguidores ganados, comentarios, likes).
2) Calcula un puntaje relativo: 1.0 = un post normal de su mismo tipo; 2.0 = el doble de bueno.
   60% calidad (interacciones valiosas por cada 1000 personas alcanzadas) + 40% alcance.
3) Promedia el puntaje por formato, gancho, tema y fondo -> state/weights.json (lo usa bot/planner.py).
4) Guarda los mejores y peores posts -> state/insights.json (se le muestran a Claude para que aprenda el patrón).
5) Escribe un informe legible en state/informe.md."""
import json
import statistics
from datetime import datetime, timezone
from . import meta
from .config import (MAX_EDAD_DIAS, MIN_EDAD_H, PESO_ALCANCE, PESOS_METRICAS, ROOT, SHRINK_K, VENTANA)

STATE = ROOT / "state"
METRICAS = ["reach", "shares", "saved", "follows", "profile_visits", "views", "likes", "comments"]
DIMENSIONES = ["formato", "estilo", "hook", "tema_clave", "fondo"]


def _load(name: str, default):
    p = STATE / name
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except json.JSONDecodeError:
        return default


def _save(name: str, data) -> None:
    STATE.mkdir(exist_ok=True)
    (STATE / name).write_text(json.dumps(data, ensure_ascii=False, indent=1))


def _edad_h(p: dict, ahora: datetime) -> float:
    return (ahora - datetime.fromisoformat(p["ts"])).total_seconds() / 3600


# ---------------------------------------------------------------- 1) medir
def medir(posts: list[dict], ahora: datetime) -> list[str]:
    """Actualiza p['metricas'] de los posts elegibles. Devuelve avisos."""
    avisos: list[str] = []
    sin_permiso = False
    for p in posts:
        if not p.get("ig_id") or p.get("final"):
            continue
        edad = _edad_h(p, ahora)
        if edad < MIN_EDAD_H:
            continue
        m: dict = {}
        for metric in METRICAS:
            try:
                v = meta.ig_media_insight(p["ig_id"], metric)
                if v is not None:
                    m[metric] = v
            except Exception as e:  # una métrica que no aplica a ese tipo de post se ignora
                if metric == "reach":
                    sin_permiso = sin_permiso or "permission" in str(e).lower() or "(#10)" in str(e)
                    avisos.append(f"No se pudo leer el alcance de {p['ig_id']}: {str(e)[:300]}")
        try:  # likes y comentarios también salen sin permiso de insights
            info = meta.ig_media_info(p["ig_id"])
            m.setdefault("likes", info.get("like_count"))
            m.setdefault("comments", info.get("comments_count"))
        except Exception as e:
            avisos.append(f"No se pudo leer el post {p['ig_id']}: {e}")
            continue
        p["metricas"] = {k: v for k, v in m.items() if v is not None}
        p["medido"] = ahora.isoformat(timespec="seconds")
        if edad > MAX_EDAD_DIAS * 24:
            p["final"] = True
    if sin_permiso:
        avisos.append("Falta el permiso instagram_business_manage_insights en IG_TOKEN: sin alcance ni compartidos "
                      "no se puede aprender. Agrégalo en la app de Meta y regenera el token.")
    return avisos


# ---------------------------------------------------------------- 2) puntuar
def _interacciones(p: dict) -> float:
    m = p["metricas"]
    total = 0.0
    for k, w in PESOS_METRICAS.items():
        total += w * float(m.get(k) or 0)
    return total


def puntuar(posts: list[dict]) -> list[dict]:
    """Asigna p['score'] a los posts recientes con alcance medido. Devuelve esa lista."""
    medidos = [p for p in posts if (p.get("metricas") or {}).get("reach")][-VENTANA:]
    if not medidos:
        return []
    for p in medidos:
        p["_eng"] = 1000 * _interacciones(p) / max(float(p["metricas"]["reach"]), 100.0)
        p["_reach"] = float(p["metricas"]["reach"])

    def mediana(lista: list[dict], campo: str) -> float:
        return statistics.median([x[campo] for x in lista]) if lista else 0.0

    for p in medidos:
        grupo = [x for x in medidos if x.get("tipo") == p.get("tipo")]
        if len(grupo) < 3:
            grupo = medidos
        med_eng, med_reach = mediana(grupo, "_eng"), mediana(grupo, "_reach")
        r_eng = min(max(p["_eng"] / med_eng, 0.1), 5.0) if med_eng > 0 else 1.0
        r_reach = min(max(p["_reach"] / med_reach, 0.1), 5.0) if med_reach > 0 else 1.0
        p["score"] = round((1 - PESO_ALCANCE) * r_eng + PESO_ALCANCE * r_reach, 3)
    for p in medidos:
        p.pop("_eng", None)
        p.pop("_reach", None)
    return medidos


# ---------------------------------------------------------------- 3) pesos
def calcular_pesos(medidos: list[dict]) -> dict:
    pesos: dict = {"n": len(medidos), "actualizado": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for dim in DIMENSIONES:
        acum: dict[str, list[float]] = {}
        for p in medidos:
            if p.get(dim):
                acum.setdefault(p[dim], []).append(p["score"])
        # Promedio "prudente": con pocos datos se queda cerca de 1.0 (neutral)
        pesos["tema" if dim == "tema_clave" else dim] = {
            v: round((sum(s) + SHRINK_K * 1.0) / (len(s) + SHRINK_K), 3) for v, s in acum.items()}
    return pesos


def calcular_insights(medidos: list[dict]) -> dict:
    if len(medidos) < 6:
        return {}
    orden = sorted(medidos, key=lambda p: p["score"], reverse=True)
    campos = ("titulo", "formato", "estilo", "nivel", "hook", "tema", "fondo", "score", "metricas")
    resumen = lambda p: {k: p.get(k) for k in campos}
    return {"top": [resumen(p) for p in orden[:3]], "bottom": [resumen(p) for p in orden[-3:]]}


# ---------------------------------------------------------------- 5) informe
def informe(medidos: list[dict], pesos: dict, avisos: list[str]) -> str:
    l = ["# Informe de rendimiento", f"Actualizado: {pesos.get('actualizado')} · posts medidos: {len(medidos)}", ""]
    l += [f"> ⚠️ {a}" for a in avisos]
    if medidos:
        l += ["", "## Posts (puntaje 1.0 = normal para su tipo)", "",
              "| Puntaje | Horario | Formato | Gancho | Título | Alcance | Compart. | Guard. | Seguid. | Coment. |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for p in sorted(medidos, key=lambda p: p["score"], reverse=True):
            m = p["metricas"]
            l.append(f"| {p['score']:.2f} | {p.get('tipo')} | {p.get('formato')} | {p.get('hook')} | "
                     f"{(p.get('titulo') or '')[:40]} | {m.get('reach', '')} | {m.get('shares', '')} | "
                     f"{m.get('saved', '')} | {m.get('follows', '')} | {m.get('comments', '')} |")
    for dim, nombre in (("formato", "Formatos"), ("estilo", "Exacto vs. debate"), ("hook", "Ganchos"), ("tema", "Temas"), ("fondo", "Fondos")):
        if pesos.get(dim):
            l += ["", f"## {nombre} (>1 = funciona mejor que el promedio)", ""]
            l += [f"- {v}: {w:.2f}" for v, w in sorted(pesos[dim].items(), key=lambda x: -x[1])]
    return "\n".join(l) + "\n"


def run(ahora: datetime | None = None) -> None:
    ahora = ahora or datetime.now(timezone.utc)
    posts = _load("posts.json", [])
    avisos = medir(posts, ahora)
    medidos = puntuar(posts)
    pesos = calcular_pesos(medidos)
    _save("posts.json", posts)
    _save("weights.json", pesos)
    _save("insights.json", calcular_insights(medidos))
    texto = informe(medidos, pesos, avisos)
    (STATE / "informe.md").write_text(texto)
    print(texto)


if __name__ == "__main__":
    run()
