# -*- coding: utf-8 -*-
"""
Ecoute du moteur Qwen3-TTS avant (ou pendant) son usage dans le lecteur.

Ce petit programme interroge l'appareil Qwen3-TTS deja demarre
(DEMARRER_QWEN_TTS.bat) et fait lire quelques phrases par plusieurs voix
francaises. Les fichiers arrivent dans le dossier « sortie_ecoute » : il
suffit de les ecouter pour juger.

Ce qu'il affiche en plus des fichiers : le RAPPORT AU TEMPS REEL de chaque
phrase (> 1 = le moteur produit plus vite qu'on ne lit). C'est la mesure qui
dit si Qwen peut tenir un chapitre entier sans trou.

Aucune dependance : bibliotheque standard uniquement (n'importe quel Python).

Usage (l'appareil doit tourner) :
    python test_service.py
    python test_service.py --nombre 3 --voix 10087_11650_000028-0002
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

# Phrases de test : une narration, un dialogue, une phrase avec des nombres
# et des noms propres, et une phrase TRES COURTE (le cas ou Qwen est parfois
# juste en dessous du temps reel, et celui ou il rend parfois du silence).
PHRASES = [
    "Le 24 février 1815, la vigie de Notre-Dame de la Garde signala le "
    "trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples.",
    "« Ah ! s'écria-t-il, je le savais bien : c'est le bonheur de cet "
    "homme qui me tue. »",
    "En 1815, monsieur Dantès avait vingt-deux ans ; il paraissait "
    "n'en avoir que dix-huit.",
    "Très bien.",
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
    print("L'appareil Qwen ne repond pas sur %s" % adresse)
    print("Verifie que la fenetre DEMARRER_QWEN_TTS.bat est bien ouverte.")
    sys.exit(1)


def duree_wav(chemin):
    with wave.open(str(chemin), "rb") as fichier:
        return fichier.getnframes() / float(fichier.getframerate())


def main():
    analyseur = argparse.ArgumentParser(
        description="Fait lire quelques phrases par l'appareil Qwen3-TTS.")
    analyseur.add_argument("--adresse", default="http://127.0.0.1:8086",
                           help="adresse de l'appareil (defaut 8086)")
    analyseur.add_argument("--nombre", type=int, default=3,
                           help="nombre de voix a essayer (defaut 3)")
    analyseur.add_argument("--voix", nargs="*", default=None,
                           help="voix precises (defaut : les 3 premieres)")
    options = analyseur.parse_args()

    etat = attendre_moteur(options.adresse)
    print("Moteur pret : %s" % etat.get("appareil"))
    print("Modele : %s" % etat.get("moteur"))
    print("Voix disponibles : %d" % etat.get("voix"))
    if etat.get("memoire_go"):
        print("Memoire video au pic : %.2f Go" % etat["memoire_go"])

    _, contenu = appeler(options.adresse, "/voix")
    toutes = json.loads(contenu.decode("utf-8"))["voix"]
    voix = options.voix if options.voix else toutes[:options.nombre]
    for choisie in voix:
        if choisie not in toutes:
            print("Voix inconnue : %s" % choisie)
            sys.exit(1)

    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

    lignes_index = []
    ratios = []
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
            ratio = (duree / calcul) if calcul else 0.0
            ratios.append(ratio)
            print("  %-22s %-28s %5.1f s d'audio  calcul %5.1f s  x%.2f"
                  % (nom, identifiant, duree, calcul, ratio))
            lignes_index.append((nom, identifiant, duree, calcul, ratio,
                                 phrase))

    with open(DOSSIER_SORTIE / "index_ecoute.txt", "w",
              encoding="utf-8") as f:
        f.write("# Ecoute du moteur Qwen3-TTS (NIMM ePub)\n")
        f.write("# Moteur : Qwen/Qwen3-TTS-12Hz-0.6B-Base (Apache-2.0)\n")
        f.write("# Voix   : kyutai/tts-voices, dossier cml-tts/fr (CC BY 4.0)\n")
        f.write("#\n")
        f.write("# fichier   voix   duree audio   calcul   x le temps reel\n")
        f.write("# " + "-" * 68 + "\n")
        for nom, identifiant, duree, calcul, ratio, _ in lignes_index:
            f.write("# %-22s %-28s %5.1f s %5.1f s  x%.2f\n"
                    % (nom, identifiant, duree, calcul, ratio))
        f.write("#\n# Phrases lues :\n")
        for numero, phrase in enumerate(PHRASES, 1):
            f.write("#   %d. %s\n" % (numero, phrase))
        if ratios:
            f.write("#\n# rapport au temps reel : de x%.2f a x%.2f"
                    "  (au-dessus de 1 = plus vite qu'on ne lit)\n"
                    % (min(ratios), max(ratios)))

    print("")
    if ratios:
        print("Rapport au temps reel : de x%.2f a x%.2f (moyenne x%.2f)"
              % (min(ratios), max(ratios), sum(ratios) / len(ratios)))
    print("Fichiers a ecouter : %s" % DOSSIER_SORTIE)
    print("FIN")


if __name__ == "__main__":
    main()

