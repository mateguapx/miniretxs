# miniretxs

Bot en GitHub Actions para **@miniretxs**: 6 mini retos de matemáticas al día en Instagram, Facebook y Threads, con aprendizaje automático de qué retos funcionan mejor. Sin ventas ni palabras clave: solo comunidad.

Nivel: **1 reto al día (20:00) para cualquiera** (aritmética con trampa, estilo "¡La respuesta NO es 49!"); los otros 5 con nivel mínimo de **finales de secundaria y bachillerato**. Respuestas siempre cortas (un número o una palabra).

Cada post es **una sola imagen** con el reto: el enunciado es el texto principal y más grande, sin título ni etiqueta de dificultad. La respuesta **nunca** se publica.
Instagram y Facebook: imagen + caption. Threads: el mismo reto en **texto**.

| Tipo | Hora (México) | Dificultad | Formatos (mezcla en `bot/config.py` → `SLOTS`) |
|---|---|---|---|
| 1 | 08:00 | Accesible | operación, patrón, ¿cuál es mayor? |
| 2 | 11:00 | Medio | lógica, problema corto, sistema con emojis |
| 3 | 14:00 | Accesible | sistema con emojis, operación, problema corto, ¿cuál es mayor? |
| 4 | 17:00 | Medio | patrón, conteo, probabilidad, ¿cuál es mayor? |
| 5 | 20:00 | **Popular** (para cualquiera) | operación, problema corto, emojis, patrón |
| 6 | 22:00 | Difícil | lógica, ¿dónde está el error?, conteo, probabilidad |

**Cómo se genera cada reto (sin API de Claude)**: los textos ya vienen escritos en una cola dentro del repo (`state/cola/<horario>/`). Una **tarea programada de Claude** corre cada semana: lee el aprendizaje (`state/weights.json`, `state/insights.json`), planea los retos que faltan con `python -m bot.cola plan`, los escribe con las mismas reglas de `bot/prompts.py`, los revisa y los sube con `python -m bot.cola agregar`. En cada horario, GitHub toma el primer reto de su carpeta, genera la imagen, publica y lo borra de la cola. Si la cola de un horario se vacía, ese horario **no publica** (aviso amarillo "Cola vacía" en Actions). Ver cuántos quedan: `python -m bot.cola estado`.

**Dos tipos de reto** (mezcla en `bot/config.py` → `ESTILOS`, 50/50 al inicio y luego según rendimiento): **exactos** (una sola respuesta correcta; el verificador rechaza cualquier ambigüedad) y **de debate** (varias respuestas defendibles a propósito, para que la gente se corrija en los comentarios). Todos los textos de los prompts están en `bot/prompts.py`.

**Imágenes**: HTML + KaTeX + Playwright (sin generador de imágenes: la notación nunca sale deformada). Paleta negro/blanco/amarillo y fondo de arte matemático generado por código (`bot/fondos.js`).

**Aprendizaje** (`learn.yml`, diario 07:40 México): mide los posts de Instagram con más de 48 h (alcance, comentarios, compartidos, guardados, seguidores) y ajusta qué formatos, ganchos, temas y fondos se publican. Informe en `state/informe.md`. Requiere el permiso `instagram_business_manage_insights`.

## Puesta en marcha
1. Repo **público** (Meta necesita URLs públicas para las imágenes; viven en la rama `media`). No subas secretos.
2. Prueba local sin publicar: `pip install -r requirements.txt && playwright install chromium && python -m bot.main --type 1 --dry` (revisa `out/`).
3. Meta: cuenta de Instagram profesional (@miniretxs), Página de Facebook vinculada y perfil de Threads. App de Meta con:
   - Instagram Login: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights`.
   - Página: `pages_manage_posts`, `pages_read_engagement`.
   - Threads API: `threads_basic`, `threads_content_publish`.
4. Secrets del repo (Settings → Secrets and variables → Actions):
   - `IG_TOKEN`, `IG_USER_ID` (Instagram)
   - `META_PAGE_TOKEN`, `FB_PAGE_ID` (Facebook)
   - `THREADS_TOKEN`, `THREADS_USER_ID` (Threads)
   - `GH_PAT` (opcional, para renovar tokens solos; ver abajo)
   - Variable opcional: `PAGE_HANDLE` (por defecto `@miniretxs`).
   **Una red sin sus secrets simplemente se omite**: puedes arrancar solo con Instagram y agregar Facebook/Threads después.
5. Actions → `post` → Run workflow (por defecto `dry=true`: genera la imagen y la deja como artefacto descargable). Cuando te guste, déjalo correr por cron.

## Tokens
Los tokens de Instagram y Threads duran 60 días. `refresh-tokens.yml` los renueva los días 1 y 15 de cada mes y los guarda como secrets; necesita `GH_PAT`: un token fine-grained de GitHub con permiso **Secrets: Read and write** sobre este repo. También revisa que `META_PAGE_TOKEN` siga vigente: si venció, la corrida queda en rojo (hay que generar un token de Página que no caduque).

## Horarios (UTC → México)
`post.yml`: 14:00, 17:00, 20:00, 23:00, 02:00, 04:00 UTC = tipos 1-6. El cron de GitHub puede retrasarse varios minutos.
