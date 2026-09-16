# -*- coding: utf-8 -*-
"""
Jetable : cout d'un casting multi-voix, par livre, avec la MEME formule que
l'application (modules/voice_casting.estimate_cast_cost). Lecture seule,
aucun appel reseau. Sortie ASCII uniquement.
"""
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.getcwd())

from core.epub_parser import get_chapters          # noqa: E402
from modules import voice_casting                   # noqa: E402

TAUX_EUR = 0.92   # 1,068 $ ~ 0,98 EUR (calibration du 14/09/2026)

LIB = os.path.join("data", "library")
conn = sqlite3.connect(os.path.join("data", "nimm_epub.db"))

print("BATCH_SIZE =", voice_casting.BATCH_SIZE)
print("tarifs gemini $/M tokens :", voice_casting.PROVIDER_PRICES_USD["gemini"])
print("")
print("livre | chapitres | phrases | caracteres | tokens_in | tokens_out | cout max")
print("-" * 92)

lignes = []
for bid, fichier, titre in conn.execute(
        "SELECT id, filename, title FROM books ORDER BY id"):
    chemin = os.path.join(LIB, fichier)
    if not os.path.exists(chemin):
        continue
    try:
        chapitres = get_chapters(chemin)
    except Exception as e:
        print("%s | (illisible : %s)" % (titre[:30], str(e)[:30]))
        continue
    textes = [c.get("text") or "" for c in chapitres]
    est = voice_casting.estimate_cast_cost(textes, "gemini")
    chars = sum(len(t) for t in textes)
    if not est["sentences"]:
        continue
    lignes.append((titre, est, chars))
    print("%s | %s | %s | %s | %s | %s | %s (~%.2f EUR)"
          % (titre[:34], est["chapters"], est["sentences"], chars,
             est["tokens_in"], est["tokens_out"], est["cost_display"],
             est["cost_usd_max"] * TAUX_EUR))

print("-" * 92)
if lignes:
    moyen_chars = sum(l[2] for l in lignes) / len(lignes)
    moyen_phrases = sum(l[1]["sentences"] for l in lignes) / len(lignes)
    print("moyenne par livre : %s caracteres, %s phrases"
          % (round(moyen_chars), round(moyen_phrases)))
    print("rapport caracteres / phrase : %.0f"
          % (sum(l[2] for l in lignes) / sum(l[1]["sentences"] for l in lignes)))

print("")
print("=== Journal des tokens : ce qui a REELLEMENT ete consomme ===")
tot_in = tot_out = tot_refl = 0
par_modele = {}
with open(os.path.join("data", "journal_tokens.csv"), encoding="utf-8") as f:
    entete = f.readline()
    for ligne in f:
        morceaux = ligne.rstrip("\n").split(";")
        if len(morceaux) < 5:
            continue
        modele = morceaux[1]
        try:
            e, s, r = int(morceaux[2]), int(morceaux[3]), int(morceaux[4])
        except ValueError:
            continue
        tot_in += e
        tot_out += s
        tot_refl += r
        m = par_modele.setdefault(modele, [0, 0, 0])
        m[0] += e
        m[1] += s
        m[2] += r

for modele, (e, s, r) in sorted(par_modele.items(), key=lambda x: -x[1][0]):
    cout = (e / 1e6) * 0.42 + ((s + r) / 1e6) * 3.50
    print("  %-26s in=%-10s out=%-8s reflexion=%-8s ~%s"
          % (modele[:26], e, s, r,
             ("gratuit" if "qwen" in modele or "llama" in modele or ":" in modele
              else "%.2f $ (~%.2f EUR)" % (cout, cout * TAUX_EUR))))
print("  TOTAL in=%s out=%s reflexion=%s" % (tot_in, tot_out, tot_refl))
cout_total = (tot_in / 1e6) * 0.42 + ((tot_out + tot_refl) / 1e6) * 3.50
print("  cout cumule estime (hors moteurs locaux) : %.2f $ (~%.2f EUR)"
      % (cout_total, cout_total * TAUX_EUR))

print("")
print("=== Cout par jour (pour retrouver le prix d'une session) ===")
par_jour = {}
with open(os.path.join("data", "journal_tokens.csv"), encoding="utf-8") as f:
    f.readline()
    for ligne in f:
        morceaux = ligne.rstrip("\n").split(";")
        if len(morceaux) < 5:
            continue
        try:
            e, s, r = int(morceaux[2]), int(morceaux[3]), int(morceaux[4])
        except ValueError:
            continue
        jour = morceaux[0][:10]
        d = par_jour.setdefault(jour, {"in": 0, "out": 0, "refl": 0, "local": 0})
        if ":" in morceaux[1] and "gemini" not in morceaux[1]:
            d["local"] += 1
            continue
        d["in"] += e
        d["out"] += s
        d["refl"] += r

for jour in sorted(par_jour):
    d = par_jour[jour]
    cout = (d["in"] / 1e6) * 0.42 + ((d["out"] + d["refl"]) / 1e6) * 3.50
    print("  %s  in=%-9s out=%-7s  ~%5.2f $ (~%.2f EUR)  appels locaux : %s"
          % (jour, d["in"], d["out"], cout, cout * TAUX_EUR, d["local"]))

conn.close()
