# -*- coding: utf-8 -*-
"""
Test isole de la Passe 1 (attribution des personnages via Gemini)
sur un chapitre reel. Ne touche a rien du reste de l'application.
Lancer depuis la racine du projet : python test_voix/test_passe1.py
"""
import sys
import json
import asyncio
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.voice_casting import analyze_chapter

# Reprend le meme chapitre que le test precedent (chapitre_test.txt),
# celui avec les pieges deja identifies (5+ personnages, Ali muet, Simbad/Dantes)
CHAPITRE_PATH = Path(__file__).parent / "chapitre_test.txt"


async def main():
    provider = sys.argv[1] if len(sys.argv) > 1 else "gemini"

    if not CHAPITRE_PATH.exists():
        print(f"Fichier introuvable : {CHAPITRE_PATH}")
        print("Adapte CHAPITRE_PATH vers un fichier texte contenant un chapitre a tester.")
        return

    with open(CHAPITRE_PATH, "r", encoding="utf-8") as f:
        chapter_text = f.read()

    print(f"Chapitre charge : {len(chapter_text)} caracteres")
    print(f"Moteur utilise : {provider}")
    print("Appel en cours...")

    result = await analyze_chapter(chapter_text, fiche_personnages=[], provider=provider)

    print(f"\n{len(result['sentences'])} phrases decoupees cote serveur")
    print(f"{len(result['phrases'])} phrases attribuees par Gemini")
    print(f"{len(result['personnages'])} personnages identifies :\n")

    for p in result["personnages"]:
        print(f"  - {p.get('nom')} ({p.get('genre')}, {p.get('age')})")

    # Verification de coherence : meme nombre de phrases des deux cotes,
    # et les id doivent correspondre exactement (pas de decalage)
    ids_attendus = [s["id"] for s in result["sentences"]]
    ids_recus = [p["id"] for p in result["phrases"]]
    if ids_attendus == ids_recus:
        print("\n✅ Correspondance des id parfaite (aucun decalage).")
    else:
        print("\n⚠️ ATTENTION : les id ne correspondent pas exactement !")
        print(f"   Attendus : {ids_attendus[:10]}...")
        print(f"   Recus    : {ids_recus[:10]}...")

    # Sauvegarde du resultat complet pour inspection
    out_path = Path(__file__).parent / "resultat_passe1_test.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nResultat complet sauvegarde dans : {out_path}")

    # Affiche les 15 premieres phrases avec locuteur, pour verif visuelle rapide
    print("\n--- Apercu ---")
    phrases_by_id = {p["id"]: p for p in result["phrases"]}
    for s in result["sentences"][:15]:
        loc = phrases_by_id.get(s["id"], {}).get("locuteur", "?")
        texte_court = s["texte"][:60] + ("..." if len(s["texte"]) > 60 else "")
        print(f"  [{s['id']:3d}] ({loc}) {texte_court}")


if __name__ == "__main__":
    asyncio.run(main())
