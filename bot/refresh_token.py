"""Imprime un token renovado (lo usa el workflow refresh-tokens).
Uso: python -m bot.refresh_token ig | threads | fb   (fb solo revisa que el token de Página siga vigente)
Si Meta rechaza la petición, el motivo queda como error visible en Actions (sin mostrar el token)."""
import sys
from . import meta

if __name__ == "__main__":
    red = sys.argv[1] if len(sys.argv) > 1 else "ig"
    try:
        if red == "fb":
            print("Token de Página vigente:", meta.revisar_page_token())
        else:
            print(meta.refresh_threads_token() if red == "threads" else meta.refresh_ig_token())
    except Exception as e:
        print(f"::error title=Token {red}::{e}", file=sys.stderr)
        sys.exit(1)
