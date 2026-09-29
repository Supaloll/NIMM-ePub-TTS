# -*- coding: utf-8 -*-
"""
Ou est utilisee une voix ? (LECTURE SEULE)

Pourquoi (29/09/2026) : Laurent a entendu un gargouillis en changeant une voix
dans « Le Chevalier Errant ». Il faut savoir QUELS personnages portent la voix
fautive avant de toucher a quoi que ce soit.

Usage : python _chercher_voix_dans_livres.py 87976454321 6877654
"""
import json
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
BASE = RACINE / "data" / "nimm_epub.db"
NOTES = RACINE / "data" / "annotations_voix.json"
sys.stdout.reconfigure(encoding="utf-8")


def main():
    motifs = sys.argv[1:]
    if not motifs:
        print("Donne au moins un morceau d'identifiant de voix.")
        return 1
    conn = sqlite3.connect("file:{}?mode=ro".format(BASE.as_posix()), uri=True)
    conn.row_factory = sqlite3.Row
    notes = {}
    if NOTES.exists():
        try:
            notes = json.loads(NOTES.read_text(encoding="utf-8"))
        except Exception:
            notes = {}

    for motif in motifs:
        print("=" * 68)
        print("MOTIF : {}".format(motif))
        print("=" * 68)
        lignes = list(conn.execute(
            "SELECT book_id, character_name, voice_id, line_count, pitch, rate "
            "FROM voices WHERE voice_id LIKE ?", ("%" + motif + "%",)))
        if lignes:
            print("Personnages qui portent cette voix :")
            for r in lignes:
                print("  livre {:<4} {:<28} {:<26} {:>5} phrases".format(
                    r["book_id"], (r["character_name"] or "")[:28],
                    r["voice_id"][:26], r["line_count"] or 0))
        else:
            print("Personnages : aucun")
        for r in conn.execute(
                "SELECT id, title, narrator_voice FROM books "
                "WHERE narrator_voice LIKE ?", ("%" + motif + "%",)):
            print("  NARRATEUR du livre {} : {}".format(r["id"], r["title"]))
        for r in lignes:
            fiche = notes.get(r["voice_id"])
            if fiche:
                print("  notes d'ecoute de {} : {}".format(
                    r["voice_id"], json.dumps(fiche, ensure_ascii=False)))
        print("")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
