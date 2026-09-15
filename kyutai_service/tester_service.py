# -*- coding: utf-8 -*-
"""
Ecoute du moteur Kyutai avant branchement dans le lecteur.

Ce petit programme interroge l'appareil Kyutai deja demarre
(DEMARRER_KYUTAI.bat) et fait lire quelques phrases par plusieurs voix
francaises. Les fichiers arrivent dans le dossier « sortie_ecoute » :
il suffit de les ecouter pour juger de la qualite.

Aucune dependance : bibliotheque standard uniquement.

Usage (l'appareil doit tourner) :
    .venv\\Scripts\\python.exe tester_service.py
    .venv\\Scripts\\python.exe tester_service.py --nombre 3 --voix 10087_11650_000028-0002
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
DOSSIER_SORTIE = ICI / "sortie_ecoute"

# Phrases de test : une narration, un dialogue, une phrase avec des
# nombres et des noms propres (les pieges habituels de la lecture).
PHRASES = [
    "Le 24 février 1815, la vigie de Notre-Dame de la Garde signala le "
    "trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples.",
    "« Ah ! s'écria-t-il, je le savais bien : c'est le bonheur de cet "
    "homme qui me tue. »",
    "En 1815, monsieur Dantès avait vingt-deux ans ; il paraissait "
    "n'en avoir que dix-huit.",
]


def appeler(adresse, chemin, donnees=None, delai=600):
    """Appel HTTP simple (GET si donnees est None, sinon POST JSON)."""
    if donnees is None:
        requete = urllib.request.Request(adresse + chemin)
    else:
        corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
        requete = urllib.request.Request(
            adresse + chemin, data=corps,
            headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(requete, timeout=delai) as reponse:
        return reponse.headers.get("Content-Type", ""), reponse.read()


def attendre_moteur(adresse, limite=180):
    """Attend que l'appareil reponde (le chargement prend quelques s)."""
    debut = time.time()
    while time.time() - debut < limite:
        try:
            _, contenu = appeler(adresse, "/sante")
            etat = json.loads(contenu.decode("utf-8"))
            if etat.get("pret"):
                return etat
        except Exception:
            pass
        time.sleep(2)
    print("L'appareil Kyutai ne repond pas sur %s" % adresse)
    print("Verifie que la fenetre DEMARRER_KYUTAI.bat est bien ouverte.")
    sys.exit(1)


def duree_wav(chemin):
    with wave.open(str(chemin), "rb") as fichier:
        return fichier.getnframes() / float(fichier.getframerate())


def main():
    analyseur = argparse.ArgumentParser(
        description="Fait lire quelques phrases par l'appareil Kyutai.")
    analyseur.add_argument("--adresse", default="http://127.0.0.1:8082",
                           help="adresse de l'appareil (defaut 8082)")
    analyseur.add_argument("--nombre", type=int, default=3,
                           help="nombre de voix a essayer (defaut 3)")
    analyseur.add_argument("--voix", nargs="*", default=None,
                           help="voix precises a essayer (defaut : les 3 premieres)")
    options = analyseur.parse_args()

    etat = attendre_moteur(options.adresse)
    print("Moteur pret : %s" % etat.get("appareil"))
    print("Voix disponibles : %d" % etat.get("voix"))

    _, contenu = appeler(options.adresse, "/voix")
    toutes = json.loads(contenu.decode("utf-8"))["voix"]
    voix = options.voix if options.voix else toutes[:options.nombre]
    for choisie in voix:
        if choisie not in toutes:
            print("Voix inconnue : %s" % choisie)
            sys.exit(1)

    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

    lignes_index = []
    for rang, identifiant in enumerate(voix, 1):
        for numero, phrase in enumerate(PHRASES, 1):
            nom = "voix%02d_phrase%d.wav" % (rang, numero)
            cible = DOSSIER_SORTIE / nom
            t0 = time.time()
            _, audio = appeler(options.adresse, "/tts",
                               {"texte": phrase, "voix": identifiant})
            cible.write_bytes(audio)
            calcul = time.time() - t0
            duree = duree_wav(cible)
            print("  %-22s %s  %5.1f s d'audio  calcul %4.1f s"
                  % (nom, identifiant, duree, calcul))
            lignes_index.append((nom, identifiant, duree, calcul, phrase))

    with open(DOSSIER_SORTIE / "index_ecoute.txt", "w", encoding="utf-8") as f:
        f.write("# Ecoute du moteur Kyutai TTS 1.6B (NIMM ePub)\n")
        f.write("# Moteur : kyutai/tts-1.6b-en_fr (CC BY 4.0)\n")
        f.write("# Voix   : kyutai/tts-voices, dossier cml-tts/fr (CC BY 4.0)\n")
        f.write("#\n")
        f.write("# fichier                 voix                          duree   calcul\n")
        f.write("# " + "-" * 68 + "\n")
        for nom, identifiant, duree, calcul, _ in lignes_index:
            f.write("# %-22s %-28s %5.1f s %5.1f s\n"
                    % (nom, identifiant, duree, calcul))
        f.write("#\n# Phrases lues :\n")
        for numero, phrase in enumerate(PHRASES, 1):
            f.write("#   %d. %s\n" % (numero, phrase))

    print("")
    print("Fichiers a ecouter : %s" % DOSSIER_SORTIE)
    print("FIN")


if __name__ == "__main__":
    main()
