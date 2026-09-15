# -*- coding: utf-8 -*-
"""Valide l'estimation du cout voix multiples sur un livre reel (sans appel IA)."""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"g:/NIMM ePub")

from core.epub_parser import get_chapters
from modules.voice_casting import estimate_cast_cost

epub = r"g:/NIMM ePub/data/library/dumas_alexandre_-_le_comte_de_monte-cristo_i.epub"
chapters = get_chapters(epub)
texts = [c.get("text") or "" for c in chapters]

fail = 0
for provider in ("gemini", "deepseek", "mistral", "inconnu"):
    est = estimate_cast_cost(texts, provider)
    print(f"[{est['provider']}] {est['chapters']} chapitres, {est['sentences']} phrases, "
          f"{est['calls']} appels | in={est['tokens_in']} out={est['tokens_out']} | "
          f"cout majore {est['cost_display']}")
    if est["calls"] < 1 or est["sentences"] < 1:
        print("  ERR : estimation vide")
        fail += 1
    if est["cost_usd_max"] < est["cost_usd"]:
        print("  ERR : majore < brut")
        fail += 1
    if est["provider"] not in ("gemini", "deepseek", "mistral"):
        print("  ERR : provider inconnu non ramene a gemini")
        fail += 1

# Ordre de grandeur : Gemini doit etre entre DeepSeek et Mistral sur ce livre
g = estimate_cast_cost(texts, "gemini")["cost_usd"]
d = estimate_cast_cost(texts, "deepseek")["cost_usd"]
m = estimate_cast_cost(texts, "mistral")["cost_usd"]
print(f"\nordres de grandeur (brut) : deepseek={d} < gemini={g} < mistral={m}")
if not (d <= g <= m):
    print("ERR : classement des couts inattendu (verifier les tarifs)")
    fail += 1

# Provider invalide -> gemini
bad = estimate_cast_cost(texts, "claude")
if bad["provider"] != "gemini":
    print("ERR : fallback provider invalide")
    fail += 1

print("\n" + ("ESTIMATION OK" if fail == 0 else f"{fail} ERREUR(S)"))
sys.exit(1 if fail else 0)
