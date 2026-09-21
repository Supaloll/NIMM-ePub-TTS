# -*- coding: utf-8 -*-
"""Lance TOUS les tests de l'atelier, et ne garde que l'essentiel.

Pourquoi cet outil (21/09/2026) : les tests se lançaient un par un, à la main --
et sous PowerShell, la moindre ligne écrite sur `stderr` fait croire à un échec
de la commande. Ici l'exécution est faite par Python, donc le **code de sortie**
est la seule vérité : « OK » veut dire OK.

Ce qu'il lance :
  - tous les `test_voix/test_*.js` (avec `node`) ;
  - les tests Python de la liste ci-dessous, ceux qui ne demandent ni moteur ni
    serveur particulier (les autres se lancent à la main, voir LIRE_MOI.md).

Usage : python test_voix/lancer_tous_les_tests.py
Double-clic : LANCER_TOUS_LES_TESTS.bat (même dossier)
"""

import io
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent

TESTS_PY = [
    "test_ids_ecran.py", "test_lire_moi.py", "test_import_main.py",
    "test_pas_de_secrets.py", "test_reparer_moteurs.py",
    "test_prononciation_kokoro.py", "test_bascule_moteur.py",
    "test_start_moteur.py", "test_decoupage_phrases.py",
    "test_niveau_audio.py", "test_nettoyage_tts.py", "test_majuscules.py",
    "test_incise_seule.py", "test_pool_casting.py", "test_residus_html.py",
    "test_onglets.py",
    # Ajoute le 21/09/2026 : ce test verifie l'ATTRIBUTION des voix (dont la
    # regle des petits roles -> Jessica/Pierre). Il existait depuis le 17/09
    # mais n'etait pas dans cette liste : il ne tournait donc JAMAIS, et il
    # avait derive sans que rien ne le signale.
    "test_attribution_criteres.py",
]


def lancer(commande):
    """(code de sortie, sortie complete) : le code est la seule verite."""
    r = subprocess.run(commande, cwd=str(RACINE), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    echecs = []

    print("")
    print("=" * 66)
    print(" TOUS LES TESTS DE NIMM ePub")
    print("=" * 66)

    print("")
    print("--- Tests de la page (JavaScript) ---")
    for fichier in sorted(DOSSIER.glob("test_*.js")):
        code, sortie = lancer(["node", str(fichier)])
        print(("  OK    " if code == 0 else "  ECHEC ") + fichier.name)
        if code != 0:
            echecs.append(fichier.name)
            for ligne in sortie.splitlines()[-6:]:
                print("        " + ligne)

    print("")
    print("--- Tests du serveur (Python) ---")
    for nom in TESTS_PY:
        chemin = DOSSIER / nom
        if not chemin.exists():
            print("  (absent) " + nom)
            continue
        code, sortie = lancer([sys.executable, str(chemin)])
        print(("  OK    " if code == 0 else "  ECHEC ") + nom)
        if code != 0:
            echecs.append(nom)
            for ligne in sortie.splitlines()[-6:]:
                print("        " + ligne)

    print("")
    print("=" * 66)
    if not echecs:
        print(" TOUT EST OK")
    else:
        print(" EN ECHEC : " + ", ".join(echecs))
        print(" (le detail des controles est affiche ci-dessus)")
    print("=" * 66)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
