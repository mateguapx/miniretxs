"""HTML + KaTeX -> PNG con Playwright. Determinista: sin generadores de imagen, sin errores de notación.
Cada post de @miniretxs es UNA imagen: número de reto, etiqueta de dificultad, título, enunciado y/o expresión.
Fondos: arte matemático generado por código (bot/fondos.js), oscurecido para que el texto se lea."""
import html
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from .config import BRAND, COLOR_NIVEL, FOOTER, HANDLE, NOMBRE_NIVEL, SIZE

VENDOR = Path(__file__).parent / "vendor"
W, H = SIZE


def _page(inner: str) -> str:
    b = BRAND
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="vendor/katex/katex.min.css">
<style>
@font-face{{font-family:Anton;src:url(vendor/fonts/anton-latin-400-normal.woff2)}}
@font-face{{font-family:Oswald;font-weight:400;src:url(vendor/fonts/oswald-latin-400-normal.woff2)}}
@font-face{{font-family:Oswald;font-weight:700;src:url(vendor/fonts/oswald-latin-700-normal.woff2)}}
*{{box-sizing:border-box;margin:0}}
body{{width:{W}px;height:{H}px;background:{b['bg']};color:{b['fg']};font-family:Oswald,sans-serif;overflow:hidden;position:relative}}
.wrap{{position:absolute;inset:0;padding:90px 80px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;font-size:30px;letter-spacing:2px;color:{b['accent']}}}
.main{{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:34px}}
.kicker{{display:inline-block;align-self:flex-start;background:{b['accent']};color:#000;font-weight:700;font-size:32px;padding:6px 22px;letter-spacing:3px;text-transform:uppercase}}
.title{{font-family:Anton;font-size:104px;line-height:1.12;letter-spacing:.5px}}
.title .katex{{font-size:1.25em}}
.title.big{{font-size:104px}}
.em{{color:{b['accent']}}}
.text{{font-size:50px;line-height:1.35;font-weight:400}}
.display{{font-size:70px;text-align:center;padding:36px 20px;border:4px solid {b['accent']};color:{b['accent']}}}
.katex-display{{margin:0!important}}
.text .katex{{white-space:nowrap}}
.foot{{display:flex;justify-content:space-between;font-size:30px;color:#aaa}}
.accent{{color:{b['accent']}}} .alert{{color:{b['alert']}}}
#bg,#bgf{{position:absolute;inset:0;z-index:0}} #bgf{{overflow:hidden}} .wrap{{z-index:1}}
.title,.text,.top,.foot{{text-shadow:0 0 14px #000,0 0 28px #000,0 2px 4px #000}}
.display{{background:rgba(0,0,0,.72)}}
.error .display{{border-color:{b['alert']};color:#fff;position:relative}}
.error .display::after{{content:'✗';position:absolute;top:-34px;right:16px;width:68px;height:68px;border-radius:50%;background:{b['alert']};color:#fff;font:700 46px/68px Oswald,sans-serif;text-align:center}}
.error .display .katex{{text-decoration:line-through;text-decoration-color:{b['alert']};text-decoration-thickness:5px}}
.reto .main{{align-items:center;text-align:center;gap:44px}}
.reto .kicker{{align-self:center;font-size:40px;padding:8px 34px}}
.reto .title{{font-size:100px}}
.reto .display{{font-size:124px;width:100%;padding:56px 24px;border-width:6px}}
.reto .text{{font-size:44px}}
.reto .text.lineas{{font-size:66px;line-height:1.45;font-weight:700}}
.top .num{{font-family:Anton;font-size:40px;letter-spacing:3px}}
.nivel{{color:#000;text-shadow:none}}
</style></head><body>{inner}
<script src="vendor/katex/katex.min.js"></script>
<script src="vendor/katex/contrib/auto-render.min.js"></script>
<script src="fondos.js"></script>
<script>
const bgc=document.getElementById('bg');
if(bgc&&window.drawFondo)drawFondo(bgc.dataset.motivo,+bgc.dataset.semilla);
renderMathInElement(document.querySelector('.wrap')||document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}],throwOnError:false}});
document.querySelectorAll('.display').forEach(e=>katex.render(e.dataset.tex,e,{{displayMode:true,throwOnError:false}}));
const px=e=>parseFloat(getComputedStyle(e).fontSize);
function fitWidth(){{document.querySelectorAll('.display').forEach(e=>{{let fs=px(e);while(e.scrollWidth>e.clientWidth+1&&fs>24){{fs-=3;e.style.fontSize=fs+'px'}}}})}}
function contentH(m){{const c=[...m.children];return c.reduce((a,x)=>a+x.offsetHeight,0)+parseFloat(getComputedStyle(m).rowGap||0)*Math.max(c.length-1,0)}}
document.fonts.ready.then(()=>{{
fitWidth();
const m=document.querySelector('.main');
let k=0;
while(m&&contentH(m)>m.clientHeight&&k<40){{
  m.querySelectorAll('.title,.text,.display').forEach(e=>{{e.style.fontSize=(px(e)*0.94)+'px'}});
  fitWidth();k++}}
window.__ready=true}});
</script></body></html>"""


def _fmt(t: str) -> str:
    """Escapa HTML, convierte **palabra** en énfasis amarillo y los saltos de línea en <br>.
    Las fórmulas $...$ las dibuja KaTeX después."""
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r'<span class="em">\1</span>', t)
    return t.replace("\\n", "\n").replace("\n", "<br>")


def slide_html(s: dict, fondo: str | None = None, semilla: int = 1, numero: int | None = None,
               nivel: str = "facil") -> str:
    """Una imagen: arriba el handle y el número de reto; etiqueta de dificultad; título; expresión; enunciado.
    fondo: nombre de motivo de bot/fondos.js (None = negro liso)."""
    e = html.escape
    disp = f'<div class="display" data-tex="{e(s["display"], quote=True)}"></div>' if s.get("display") else ""
    title = f'<div class="title big">{_fmt(s["title"])}</div>' if s.get("title") else ""
    texto = s.get("text") or ""
    clase = "text lineas" if ("\n" in texto.replace("\\n", "\n")) else "text"
    text = f'<div class="{clase}">{_fmt(texto)}</div>' if texto else ""
    kicker = (f'<div class="kicker nivel" style="background:{COLOR_NIVEL.get(nivel, BRAND["accent"])}">'
              f'{e(NOMBRE_NIVEL.get(nivel, nivel.upper()))}</div>')
    num = f"RETO #{numero}" if numero else "RETO"
    bg = (f'<canvas id="bg" width="{W}" height="{H}" data-motivo="{e(fondo)}" data-semilla="{int(semilla)}"></canvas>'
          f'<div id="bgf"></div>') if fondo else ""
    return f"""{bg}<div class="wrap reto">
<div class="top"><span>{e(HANDLE)}</span><span class="num">{e(num)}</span></div>
<div class="main">{kicker}{title}{disp}{text}</div>
<div class="foot"><span>{e(FOOTER)}</span><span></span></div>
</div>"""


def render_many(inners: list[str], out_paths: list[Path]) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        for inner, out in zip(inners, out_paths):
            tmp = Path(__file__).parent / "_tmp.html"
            tmp.write_text(_page(inner), encoding="utf-8")
            page.goto(tmp.as_uri())
            page.wait_for_function("window.__ready === true")
            out.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out))
            tmp.unlink()
        browser.close()
