# -*- coding: utf-8 -*-
"""
Jetable : combien de personnages (et de repliques) chaque livre demande,
pour dimensionner un casting de voix. Lecture seule.
Sortie ASCII uniquement.
"""
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = "data/nimm_epub.db"
conn = sqlite3.connect(BASE)
conn.row_factory = sqlite3.Row

print("=== Par livre : personnages connus et repliques attribuees ===")
livres = conn.execute("SELECT id, saga, title FROM books ORDER BY id").fetchall()
for b in livres:
    n_fiche = conn.execute(
        "SELECT COUNT(*) FROM cast_fiche WHERE book_id = ?", (b["id"],)).fetchone()[0]
    n_parlants = conn.execute(
        "SELECT COUNT(DISTINCT speaker) FROM speaker_attribution WHERE book_id = ?",
        (b["id"],)).fetchone()[0]
    n_phrases = conn.execute(
        "SELECT COUNT(*) FROM speaker_attribution WHERE book_id = ?",
        (b["id"],)).fetchone()[0]
    if n_fiche or n_phrases:
        print("  #%s %-38s fiche=%-4s parlants=%-4s phrases=%s"
              % (b["id"], (b["title"] or "")[:38], n_fiche, n_parlants, n_phrases))

print("")
print("=== Detail Monte-Cristo : repliques par personnage ===")
seuils = [1, 5, 10, 25, 50, 100, 200, 500]
for b in livres:
    if not b["saga"]:
        continue
    lignes = conn.execute(
        "SELECT speaker, COUNT(*) AS n FROM speaker_attribution "
        "WHERE book_id = ? GROUP BY speaker ORDER BY n DESC", (b["id"],)).fetchall()
    if not lignes:
        continue
    total = sum(l["n"] for l in lignes)
    print("")
    print("  --- #%s %s | %s phrases attribuees, %s intervenants"
          % (b["id"], b["saga"], total, len(lignes)))
    paliers = []
    for s in seuils:
        paliers.append("%s>=%s" % (s, sum(1 for l in lignes if l["n"] >= s)))
    print("      paliers (repliques min) : " + " | ".join(paliers))
    print("      top 20 :")
    for l in lignes[:20]:
        print("        %-32s %s" % ((l["speaker"] or "")[:32], l["n"]))

print("")
print("=== Saga entiere (tous les tomes cumules) ===")
lignes = conn.execute(
    "SELECT speaker, COUNT(*) AS n FROM speaker_attribution "
    "WHERE book_id IN (SELECT id FROM books WHERE saga IS NOT NULL) "
    "GROUP BY speaker ORDER BY n DESC").fetchall()
print("  intervenants distincts toutes sagas : %s" % len(lignes))
print("  paliers : " + " | ".join(
    "%s>=%s" % (s, sum(1 for l in lignes if l["n"] >= s)) for s in seuils))
print("  top 25 (tous tomes) :")
for l in lignes[:25]:
    print("    %-32s %s" % ((l["speaker"] or "")[:32], l["n"]))

conn.close()
