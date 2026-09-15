# -*- coding: utf-8 -*-
"""
Test de la Passe 2 (consolidation des doublons + attribution des voix)
SANS rappeler Gemini pour la Passe 1 : on recharge le fichier
resultat_passe1_multi_test.json deja sauvegarde. Seul l'appel Gemini de
la consolidation (Passe 2) est effectue, une seule requete.

Lancer depuis la racine du projet : python test_voix/test_passe2_consolidation.py
"""
import sys
import json
import asyncio
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.voice_casting import consolidate_book

JSON_PASSE1 = Path(__file__).parent / "resultat_passe1_multi_test.json"


async def main():
    if not JSON_PASSE1.exists():
        print(f"Introuvable : {JSON_PASSE1}")
        return

    print(f"Chargement de la Passe 1 depuis : {JSON_PASSE1.name}")
    resultats = json.loads(JSON_PASSE1.read_text(encoding="utf-8"))
    print(f"{len(resultats)} chapitres charges, fiche brute de "
          f"{len(resultats[-1]['personnages'])} personnages.")

    # Sauvegarde des locuteurs AVANT fusion, pour comparer
    avant = [
        [p.get("locuteur") for p in res.get("phrases", [])]
        for res in resultats
    ]

    print("\nAppel a Gemini pour la consolidation (1 seule requete)...\n")
    passe2 = await consolidate_book(resultats)

    fusion = passe2["fusion"]
    personnages = passe2["personnages"]
    compte = passe2["compte_phrases"]
    voix = passe2["voix"]

    print("=== FUSION (doublons) ===")
    modifiees = {a: b for a, b in fusion.items() if a != b}
    if modifiees:
        for a, b in sorted(modifiees.items()):
            print(f"  {a} -> {b}")
    else:
        print("  (aucune fusion -- la fiche etait deja propre)")

    print(f"\n=== {len(personnages)} PERSONNAGES FINAUX : compte phrases / voix / pitch ===")
    for p in sorted(personnages, key=lambda x: compte.get(x.get('nom'), 0), reverse=True):
        nom = p.get("nom")
        v = voix.get(nom, {})
        print(f"  {nom} ({p.get('genre')}, {p.get('age')}) | "
              f"{compte.get(nom, 0)} phrases | {v.get('voice_id')} {v.get('pitch')}")

    # Verifie la coherence : les locuteurs fusionnes ont bien change
    modifs_reecrites = 0
    for res, av in zip(resultats, avant):
        for p, loc_avant in zip(res.get("phrases", []), av):
            if p.get("locuteur") != loc_avant:
                modifs_reecrites += 1
    print(f"\n{modifs_reecrites} locuteurs reecrits par la fusion.")

    locuteurs = set()
    for res in resultats:
        for ph in res.get("phrases", []):
            locuteurs.add(ph.get("locuteur"))
    print(f"{len(locuteurs)} locuteurs distincts apres fusion.")

    out_path = Path(__file__).parent / "resultat_passe2_consolidation_test.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(passe2, f, ensure_ascii=False, indent=2)
    print(f"\nResultat complet sauvegarde dans : {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
