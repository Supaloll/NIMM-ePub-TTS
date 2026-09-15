# -*- coding: utf-8 -*-
"""
Test de la Passe 1 sur plusieurs chapitres a la suite, avec la vraie
fiche de personnages qui voyage d'un chapitre a l'autre.
Utilise epub_parser.py pour extraire les chapitres, comme le fait
l'application normalement -- pas de texte colle a la main.

Lancer depuis la racine du projet : python test_voix/test_passe1_multi.py
"""
import sys
import json
import asyncio
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.epub_parser import get_chapters
from modules.voice_casting import analyze_chapters

# Adapte ce chemin vers le fichier EPUB du Comte de Monte-Cristo
# present dans data/library/
EPUB_PATH = r"G:\NIMM ePub\data\library\DUMAS_T1 - Le Comte de Monte-Cristo.epub"
NB_CHAPITRES_TEST = 3


async def main():
    if EPUB_PATH is None:
        print("EPUB_PATH n'est pas renseigne en haut du script.")
        print("Cherche le fichier .epub du Comte de Monte-Cristo dans data/library/")
        print("et colle son chemin complet dans EPUB_PATH.")
        return

    epub_path = Path(EPUB_PATH)
    if not epub_path.exists():
        print(f"Fichier introuvable : {epub_path}")
        return

    print(f"Extraction des chapitres depuis : {epub_path.name}")
    all_chapters = get_chapters(str(epub_path))
    print(f"{len(all_chapters)} chapitres trouves au total.")

    # Les 3 DERNIERS chapitres du Tome 1 (XXIX, XXX, XXXI), selectionnes
    # par titre exact : l'EPUB contient des pages de fin d'edition ("A propos
    # de cette edition", "Vous avez aime ce livre ?") apres le chapitre XXXI,
    # donc un simple [-3:] ne donnerait pas les bons chapitres.
    TITRES_CIBLES = [
        "XXIX – La maison Morrel.",
        "XXX – Le cinq septembre.",
        "XXXI – Italie. – Simbad le marin.",
    ]
    subset = [c for c in all_chapters if c["title"] in TITRES_CIBLES]
    if len(subset) != NB_CHAPITRES_TEST:
        print(f"ATTENTION : {len(subset)} chapitres cibles trouves au lieu de {NB_CHAPITRES_TEST}.")
        print("Verrifie les titres dans le EPUB (encodage des tirets notamment).")
    print(f"Test sur {len(subset)} chapitres :\n")
    for c in subset:
        print(f"  - Chapitre {c['index']} : {c['title']} ({len(c['text'])} caracteres)")

    print("\nAppel a Gemini, chapitre par chapitre (la fiche s'enrichit au fil de l'eau)...\n")

    textes = [c["text"] for c in subset]
    resultats = await analyze_chapters(textes)

    for i, (chap, res) in enumerate(zip(subset, resultats)):
        print(f"\n=== Chapitre {chap['index']} : {chap['title']} ===")
        print(f"  {len(res['sentences'])} phrases | {len(res['phrases'])} attributions")

        ids_attendus = [s["id"] for s in res["sentences"]]
        ids_recus = [p["id"] for p in res["phrases"]]
        if ids_attendus == ids_recus:
            print("  ✅ Correspondance id parfaite.")
        else:
            print("  ⚠️ DECALAGE d'id detecte !")

    # Fiche finale = celle du dernier chapitre traite (la plus enrichie)
    fiche_finale = resultats[-1]["personnages"]
    print(f"\n=== Fiche de personnages apres {len(subset)} chapitres ===")
    for p in fiche_finale:
        print(f"  - {p.get('nom')} ({p.get('genre')}, {p.get('age')})")

    # Verifie qu'aucun nom canonique n'a change de chapitre en chapitre
    # (on ne le peut verifier qu'en observant les noms au fil des reponses)
    noms_par_chapitre = [
        {p.get("nom") for p in res["personnages"]} for res in resultats
    ]
    tous_les_noms = set()
    for noms in noms_par_chapitre:
        tous_les_noms |= noms
    print(f"\n{len(tous_les_noms)} noms distincts vus au total sur {len(subset)} chapitres.")
    print("(A verifier manuellement dans le detail ci-dessus : pas de quasi-doublons")
    print(" du style 'Matelot' / 'Matelots' ou changement de nom en cours de route.)")

    # Sauvegarde complete pour inspection
    out_path = Path(__file__).parent / "resultat_passe1_multi_test.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
    print(f"\nResultat complet sauvegarde dans : {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
