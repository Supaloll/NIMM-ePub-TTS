# -*- coding: utf-8 -*-
"""
Mesure LECTURE SEULE : combien de voix assignees par famille de moteur,
et sur combien de livres -- avant de debrancher un moteur du demarrage.

Outil d'atelier jetable (prefixe _). La base est ouverte en mode "ro" :
aucune ecriture n'est possible, meme par erreur.
"""
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).parent / "data" / "nimm_epub.db"

# Familles telles que le lecteur les nomme : le prefixe de la voix ("kyutai:...",
# "kokoro:...", "pocket:...") ; une voix sans prefixe est une voix Edge.
FAMILLES = ("kokoro", "kyutai", "pocket", "qwen", "xtts", "neutts", "piper")


def famille(voice_id: str) -> str:
    v = (voice_id or "").strip().lower()
    for f in FAMILLES:
        if v.startswith(f + ":"):
            return f
    return "edge"


def main() -> None:
    conn = sqlite3.connect("file:{}?mode=ro".format(BASE.as_posix()), uri=True)
    conn.row_factory = sqlite3.Row

    print("Base : {} (lecture seule)".format(BASE.name))
    print()

    # 1. Structure des tables lues (on ne suppose jamais les colonnes).
    for table in ("voices", "books"):
        cols = [r["name"] for r in conn.execute(
            "PRAGMA table_info({})".format(table))]
        print("Table {} : {}".format(table, ", ".join(cols)))
    print()

    cols_voices = [r["name"] for r in conn.execute("PRAGMA table_info(voices)")]
    col_voix = "voice_id" if "voice_id" in cols_voices else "voice"
    print("Colonne utilisee pour la voix : {}".format(col_voix))
    print()

    # 2. Toutes les voix assignees, par famille.
    lignes = list(conn.execute(
        "SELECT book_id, {} AS voix FROM voices".format(col_voix)))
    par_famille = Counter()
    livres_par_famille = defaultdict(set)
    for r in lignes:
        f = famille(r["voix"])
        par_famille[f] += 1
        livres_par_famille[f].add(r["book_id"])

    print("Voix assignees dans la table voices : {} au total".format(len(lignes)))
    for f, n in par_famille.most_common():
        print("  {:<8} {:>6} voix   sur {:>3} livre(s)".format(
            f, n, len(livres_par_famille[f])))
    print()

    # 3. Le narrateur de chaque livre (c'est lui qui lit la majorite du texte).
    if "narrator_voice" in [c["name"] for c in conn.execute("PRAGMA table_info(books)")]:
        print("Narrateur enregistre dans books.narrator_voice :")
        rows = list(conn.execute(
            "SELECT id, title, narrator_voice FROM books ORDER BY id"))
        par_famille_narrateur = Counter()
        for r in rows:
            f = famille(r["narrator_voice"])
            par_famille_narrateur[f] += 1
            print("  livre {:<4} {:<38} {}".format(
                r["id"], (r["title"] or "")[:38], r["narrator_voice"] or ""))
        print()
        print("Narrateurs par famille :")
        for f, n in par_famille_narrateur.most_common():
            print("  {:<8} {:>3} livre(s)".format(f, n))
        print()

    # 4. Le personnage qui lit le plus de phrases, par famille (voix assignees).
    print("Personnages a fort volume lus par Kokoro ou Kyutai (top 15) :")
    for r in conn.execute(
        "SELECT book_id, character_name, voice_id, line_count FROM voices "
        "WHERE voice_id LIKE 'kokoro:%' OR voice_id LIKE 'kyutai:%' "
        "ORDER BY line_count DESC LIMIT 15"):
        print("  livre {:<4} {:<28} {:<22} {:>5} phrases".format(
            r["book_id"], (r["character_name"] or "")[:28],
            r["voice_id"][:22], r["line_count"] or 0))
    print()

    conn.close()


if __name__ == "__main__":
    main()
