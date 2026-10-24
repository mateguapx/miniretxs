"""Publicación en Instagram (API con Instagram Login), Facebook (token de Página) y Threads (solo texto).
Verifica endpoints contra la doc vigente de Meta."""
import os
import time
import requests
from .config import GRAPH_VERSION, THREADS_VERSION

IG_BASE = f"https://graph.instagram.com/{GRAPH_VERSION}"
FB_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
TH_BASE = f"https://graph.threads.net/{THREADS_VERSION}"
IG_TOKEN = lambda: os.environ["IG_TOKEN"]            # token de usuario de Instagram (larga duración, 60 días)
PAGE_TOKEN = lambda: os.environ["META_PAGE_TOKEN"]   # token de Página (solo Facebook)
TH_TOKEN = lambda: os.environ["THREADS_TOKEN"]       # token de Threads (larga duración, 60 días)
IG_ID = lambda: os.environ["IG_USER_ID"]
PAGE_ID = lambda: os.environ["FB_PAGE_ID"]
TH_ID = lambda: os.getenv("THREADS_USER_ID") or "me"


def activo(red: str) -> bool:
    """Una red se publica solo si sus secrets están configurados (así puedes empezar solo con Instagram)."""
    req = {"ig": ("IG_TOKEN", "IG_USER_ID"), "fb": ("META_PAGE_TOKEN", "FB_PAGE_ID"), "threads": ("THREADS_TOKEN",)}[red]
    return all(os.getenv(v) for v in req)


def _check(r: requests.Response, what: str) -> dict:
    if not r.ok:
        raise RuntimeError(f"{what} -> {r.status_code}: {r.text}")
    return r.json()


def _ig_post(path: str, **data) -> dict:
    return _check(requests.post(f"{IG_BASE}/{path}", data={**data, "access_token": IG_TOKEN()}, timeout=60), f"IG POST {path}")


def _ig_get(path: str, **params) -> dict:
    return _check(requests.get(f"{IG_BASE}/{path}", params={**params, "access_token": IG_TOKEN()}, timeout=60), f"IG GET {path}")


def _fb_post(path: str, **data) -> dict:
    return _check(requests.post(f"{FB_BASE}/{path}", data={**data, "access_token": PAGE_TOKEN()}, timeout=60), f"FB POST {path}")


def _th_post(path: str, **data) -> dict:
    return _check(requests.post(f"{TH_BASE}/{path}", data={**data, "access_token": TH_TOKEN()}, timeout=60), f"Threads POST {path}")


def _th_get(path: str, **params) -> dict:
    return _check(requests.get(f"{TH_BASE}/{path}", params={**params, "access_token": TH_TOKEN()}, timeout=60), f"Threads GET {path}")


def _wait_ready(container_id: str, tries: int = 30) -> None:
    for _ in range(tries):
        status = _ig_get(container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Contenedor {container_id} en estado {status}")
        time.sleep(4)
    raise TimeoutError(f"Contenedor {container_id} no terminó a tiempo")


def _no_listo(r: requests.Response) -> bool:
    """Meta a veces responde 'Media ID is not available' (9007/2207027) aunque el contenedor ya diga FINISHED."""
    try:
        e = r.json().get("error", {})
    except ValueError:
        return False
    return e.get("code") == 9007 or e.get("error_subcode") == 2207027


def _ig_publicar(creation_id: str) -> str:
    """media_publish con reintentos SOLO ante 'contenedor aún no listo': ese error garantiza que no se publicó,
    así que reintentar no duplica el post."""
    for espera in (10, 20, 30, None):
        r = requests.post(f"{IG_BASE}/{IG_ID()}/media_publish",
                          data={"creation_id": creation_id, "access_token": IG_TOKEN()}, timeout=60)
        if r.ok or espera is None or not _no_listo(r):
            return _check(r, f"IG POST {IG_ID()}/media_publish")["id"]
        time.sleep(espera)
        _wait_ready(creation_id)
    raise AssertionError("inalcanzable")


# --- Instagram ---
def publish_instagram(image_url: str, caption: str) -> str:
    """Post de una sola imagen."""
    c = _ig_post(f"{IG_ID()}/media", image_url=image_url, caption=caption)["id"]
    _wait_ready(c)
    return _ig_publicar(c)


def ig_media_info(media_id: str) -> dict:
    """Datos básicos del post (no requieren permiso de insights)."""
    return _ig_get(media_id, fields="like_count,comments_count,timestamp,permalink,media_type")


def ig_media_insight(media_id: str, metric: str) -> float | None:
    """Una métrica de insights del post (requiere instagram_business_manage_insights).
    Se pide de una en una porque si una no aplica a ese tipo de post, Meta rechaza toda la petición."""
    data = _ig_get(f"{media_id}/insights", metric=metric).get("data", [])
    if not data:
        return None
    d = data[0]
    if d.get("total_value"):
        return d["total_value"].get("value")
    vals = d.get("values") or []
    return vals[0].get("value") if vals else None


def refresh_ig_token() -> str:
    """Renueva el token de larga duración de Instagram (válido 60 días; renovable después de 24 h de emitido)."""
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": IG_TOKEN()}, timeout=60)
    return _check(r, "IG refresh")["access_token"]


# --- Facebook ---
def publish_facebook(image_url: str, caption: str) -> str:
    """Foto publicada directamente (devuelve el id del post)."""
    r = _fb_post(f"{PAGE_ID()}/photos", url=image_url, caption=caption, published="true")
    return r.get("post_id") or r["id"]


# --- Threads (solo texto) ---
def publish_threads(text: str, tries: int = 10) -> str:
    """Crea un contenedor de texto y lo publica (Meta recomienda esperar a que el contenedor esté listo)."""
    c = _th_post(f"{TH_ID()}/threads", media_type="TEXT", text=text)["id"]
    for _ in range(tries):
        time.sleep(3)
        status = _th_get(c, fields="status").get("status")
        if status in (None, "FINISHED"):
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Contenedor de Threads {c} en estado {status}")
    return _th_post(f"{TH_ID()}/threads_publish", creation_id=c)["id"]


def refresh_threads_token() -> str:
    """Renueva el token de larga duración de Threads (válido 60 días; renovable después de 24 h de emitido)."""
    r = requests.get("https://graph.threads.net/refresh_access_token",
                     params={"grant_type": "th_refresh_token", "access_token": TH_TOKEN()}, timeout=60)
    return _check(r, "Threads refresh")["access_token"]


def revisar_page_token() -> str:
    """Comprueba que el token de Página siga vigente (si venció, Facebook deja de publicar). Devuelve el nombre de la Página."""
    r = requests.get(f"{FB_BASE}/me", params={"fields": "id,name", "access_token": PAGE_TOKEN()}, timeout=60)
    return _check(r, "FB token de Página").get("name", "")
