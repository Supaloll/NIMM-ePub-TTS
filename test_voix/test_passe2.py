# -*- coding: utf-8 -*-
"""
Test de la Passe 2 (consolidation + attribution des voix) a partir du
resultat deja sauvegarde par test_passe1_multi.py -- pas de nouvel
appel Gemini pour la Passe 1, on economise les requetes.

Lancer depuis la racine du projet : python test_voix/test_passe2.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.voice_casting import consolidate_book

RESULTAT_PATH = Path(__file__).parent / "resultat_passe1_multi_test.json"


async def main():
    if not RESULTAT_PATH.exists():
        print(f"Fichier introuvable : {RESULTAT_PATH}")
        print("Lance d'abord test_passe1_multi.py.")
        return

    with open(RESULTAT_PATH, "r", encoding="utf-8") as f:
        resultats = json.load(f)

    print(f"{len(resultats)} chapitres charges depuis la Passe 1.")
    fiche_brute = resultats[-1]["personnages"]
    print(f"Fiche brute avant consolidation : {len(fiche_brute)} noms\n")
    for p in fiche_brute:
        print(f"  - {p.get('nom')} ({p.get('genre')}, {p.get('age')})")

    print("\nAppel a Gemini pour la Passe 2 (consolidation)...\n")
    result = await consolidate_book(resultats)

    print("=== Table de fusion ===")
    for original, final in result["fusion"].items():
        marqueur = "  (fusionne)" if original != final else ""
        print(f"  {original} -> {final}{marqueur}")

    print(f"\n=== Personnages finaux ({len(result['personnages'])}) avec voix attribuee ===")
    for p in result["personnages"]:
        nom = p.get("nom")
        count = result["compte_phrases"].get(nom, 0)
        voix_info = result["voix"].get(nom, {})
        print(f"  - {nom} ({p.get('genre')}, {p.get('age')}) "
              f"| {count} phrases | voix: {voix_info.get('voice_id')} | pitch: {voix_info.get('pitch')}")

    out_path = Path(__file__).parent / "resultat_passe2_test.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nResultat complet sauvegarde dans : {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
