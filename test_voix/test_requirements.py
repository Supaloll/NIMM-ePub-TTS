# -*- coding: utf-8 -*-
"""Verifie que les dependances figees correspondent aux environnements reels.

Deux environnements sont controles, chacun avec son fichier :

  1. le LECTEUR (Python 3.14)      -> requirements.txt (racine)
  2. le MOTEUR KYUTAI (Python 3.12) -> kyutai_service/requirements.txt

Le controle est fait paquet par paquet, **sans reseau** : on lit la version
installee et on la compare a celle ecrite dans le fichier. A relancer apres
toute mise a jour de dependances (et utile avant une reinstallation sur une
autre machine).

Usage : python test_voix/test_requirements.py
"""

import subprocess
import sys
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
FICHIER_LECTEUR = RACINE / "requirements.txt"
FICHIER_MOTEUR = RACINE / "kyutai_service" / "requirements.txt"
PYTHON_MOTEUR = RACINE / "kyutai_service" / ".venv" / "Scripts" / "python.exe"

sys.stdout.reconfigure(encoding='utf-8')

# Petit programme execute par le python du moteur pour lire SES paquets
# (il ne connait pas ceux du lecteur : les environnements sont separes).
INSPECTEUR = (
    "import sys\n"
    "from importlib.metadata import version, PackageNotFoundError\n"
    "for nom in sys.argv[1:]:\n"
    "    try:\n"
    "        print(nom + '==' + version(nom))\n"
    "    except PackageNotFoundError:\n"
    "        print(nom + '==MANQUANT')\n"
)


def lire_paquets(fichier):
    """Renvoie [(nom, version attendue), ...] en ignorant commentaires et vides."""
    paquets = []
    for ligne in fichier.read_text(encoding="utf-8").splitlines():
        ligne = ligne.split("#")[0].strip()
        if not ligne or "==" not in ligne:
            continue
        nom, attendu = [x.strip() for x in ligne.split("==", 1)]
        paquets.append((nom, attendu))
    return paquets


def controler(nom_env, fichier, versions_installees):
    """Compare un fichier de dependances a {nom: version installee}."""
    print("--- %s" % nom_env)
    print("    fichier : %s" % fichier.relative_to(RACINE))
    ok = True
    for nom, attendu in lire_paquets(fichier):
        installe = versions_installees.get(nom.lower())
        if installe is None:
            print("    MANQUANT   %s (attendu %s)" % (nom, attendu))
            ok = False
        elif installe != attendu:
            print("    ECART      %s : fichier %s, installe %s" % (nom, attendu, installe))
            ok = False
        else:
            print("    OK         %s %s" % (nom, attendu))
    print("    => %s" % ("conforme" if ok else "A CORRIGER"))
    print("")
    return ok


def versions_du_processus(paquets):
    """{nom: version} pour l'environnement Python courant."""
    trouvees = {}
    for nom, _ in paquets:
        try:
            trouvees[nom.lower()] = version(nom)
        except PackageNotFoundError:
            pass
    return trouvees


def versions_du_moteur(paquets):
    """{nom: version} dans l'environnement du moteur (sous-processus)."""
    if not PYTHON_MOTEUR.is_file():
        return None
    noms = [nom for nom, _ in paquets]
    resultat = subprocess.run(
        [str(PYTHON_MOTEUR), "-c", INSPECTEUR] + noms,
        capture_output=True, text=True, encoding="utf-8", timeout=120
    )
    trouvees = {}
    for ligne in (resultat.stdout or "").splitlines():
        if "==" in ligne:
            nom, valeur = ligne.split("==", 1)
            if valeur.strip() != "MANQUANT":
                trouvees[nom.strip().lower()] = valeur.strip()
    return trouvees


def main():
    print("")
    paquets_lecteur = lire_paquets(FICHIER_LECTEUR)
    ok1 = controler("LECTEUR (Python %s)" % sys.version.split()[0],
                    FICHIER_LECTEUR, versions_du_processus(paquets_lecteur))

    paquets_moteur = lire_paquets(FICHIER_MOTEUR)
    versions = versions_du_moteur(paquets_moteur)
    if versions is None:
        print("--- MOTEUR KYUTAI : environnement absent (%s)" % PYTHON_MOTEUR)
        print("    (lance INSTALLER_KYUTAI.bat pour l'installer)")
        print("")
        ok2 = True          # son absence n'est pas une incoherence
    else:
        ok2 = controler("MOTEUR KYUTAI (environnement separe)",
                        FICHIER_MOTEUR, versions)

    print("TOUT EST COHERENT" if (ok1 and ok2) else "DES ECARTS SONT A CORRIGER")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
