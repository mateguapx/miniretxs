"""Imprime un token renovado (lo usa el workflow refresh-tokens).
Uso: python -m bot.refresh_token ig | threads"""
import sys
from . import meta

if __name__ == "__main__":
    red = sys.argv[1] if len(sys.argv) > 1 else "ig"
    print(meta.refresh_threads_token() if red == "threads" else meta.refresh_ig_token())
