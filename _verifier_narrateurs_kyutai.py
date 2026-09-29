# -*- coding: utf-8 -*-
"""
Mesure LECTURE SEULE : les NARRATEURS de livre (`books.narrator_voice`) qui
sont des voix Kyutai, et l'existence de leur jumelle Qwen chez le moteur.

Pourquoi : `test_voix/_basculer_voix_kyutai_vers_qwen.py` ne bascule que la
table `voices` ; le narrateur d'un livre vit dans `books.narrator_voice`.
Debrancher Kyutai sans traiter ce champ rendrait le livre muet.
"""
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(RACINE))

from modules.tts import QWEN_VOICES  # noqa: E402

BASE = RACINE / "data" / "nimm_epub.db"
DOSSIER_VOIX = RACINE / "qwen_tts_service" / "voix"
SUFFIXE = "_enhanced_reference.wav"


def extraits_presents():
    presents = set()
    if DOSSIER_VOIX.is_dir():
        for fichier in DOSSIER_VOIX.glob("*.wav"):
            nom = fichier.name
            if nom.endswith(SUFFIXE):
                nom = nom[: -len(SUFFIXE)]
            presents.add(nom)
    return presents


def main():
    presents = extraits_presents()
    catalogue = {v["id"] for v in QWEN_VOICES}
    print("Extraits presents chez Qwentts : {}".format(len(presents)))
    print("Voix qwen: proposees par le lecteur : {}".format(len(catalogue)))
    print()

    conn = sqlite3.connect("file:{}?mode=ro".format(BASE.as_posix()), uri=True)
    conn.row_factory = sqlite3.Row

    rows = list(conn.execute(
        "SELECT id, title, narrator_voice FROM books "
        "WHERE narrator_voice LIKE 'kyutai:%' ORDER BY id"))

    print("Livres dont le NARRATEUR est une voix Kyutai : {}".format(len(rows)))
    for r in rows:
        voix = r["narrator_voice"]
        identifiant = voix.split(":", 1)[1]
        jumelle = "qwen:" + identifiant
        extrait_ok = identifiant in presents
        catalogue_ok = jumelle in catalogue
        verdict = "OK" if (extrait_ok and catalogue_ok) else "MANQUE"
        print("  livre {:<4} {:<36} {}".format(
            r["id"], (r["title"] or "?")[:36], voix))
        print("        jumelle {} : extrait={} catalogue={} -> {}".format(
            jumelle, "oui" if extrait_ok else "NON",
            "oui" if catalogue_ok else "NON", verdict))

    # Controle de coherence : un narrateur Kyutai absent de la table `voices`
    # ne serait pas bascule par l'outil existant.
    for r in rows:
        n = conn.execute(
            "SELECT COUNT(*) FROM voices WHERE book_id = ? AND voice_id = ?",
            (r["id"], r["narrator_voice"])).fetchone()[0]
        print("  livre {:<4} ligne(s) dans voices pour cette voix : {}".format(
            r["id"], n))

    # TOUS les champs de la base qui portent une voix Kyutai : si un champ est
    # oublie par la bascule, un livre s'arretera (503) le jour ou le moteur est
    # eteint. On ne suppose aucun nom de colonne : on les lit dans la base.
    print()
    print("Champs de toute la base qui portent encore une voix Kyutai :")
    trouves = 0
    for (table,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"):
        colonnes = [c[1] for c in conn.execute("PRAGMA table_info({})".format(table))]
        for colonne in colonnes:
            if "voice" not in colonne.lower() and "voix" not in colonne.lower():
                continue
            try:
                n = conn.execute(
                    "SELECT COUNT(*) FROM {} WHERE {} LIKE 'kyutai:%'".format(
                        table, colonne)).fetchone()[0]
            except Exception as e:
                print("  {}.{} : illisible ({})".format(table, colonne, e))
                continue
            if n:
                trouves += 1
                print("  {}.{} : {} ligne(s)".format(table, colonne, n))
    if not trouves:
        print("  aucune")

    conn.close()


if __name__ == "__main__":
    main()
