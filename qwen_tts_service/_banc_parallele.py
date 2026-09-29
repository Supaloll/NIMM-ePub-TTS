"""Banc JETABLE : combien de phrases Qwen par seconde en PARALLELE ?

Question posee le 26/09/2026, apres une mesure genante : phrase par phrase,
Qwen tourne a x0,45 le temps reel (il lui faut deux fois la duree de
l'audio), et la carte graphique n'est utilisee qu'a 27 % pendant ce temps.
L'attente est donc dans la boucle du modele, pas dans la carte : deux
generations de front devraient presque doubler le debit.

Ce banc compare donc, sur LES MEMES phrases :
  - N phrases envoyees une par une (comme le lecteur aujourd'hui) ;
  - les memes N phrases envoyees DE FRONT (N requetes simultanees).

A lancer avec n'importe quel Python (bibliotheque standard seulement), le
service Qwen etant demarre :
    python _banc_parallele.py --front 2
"""

import argparse
import json
import sys
import threading
import time
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
DOSSIER = ICI / "_banc_parallele"
PHRASES = [
    "Le 24 février 1815, la vigie de Notre-Dame de la Garde signala le "
    "trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples.",
    "« Ah ! s'écria-t-il, je le savais bien : c'est le bonheur de cet "
    "homme qui me tue. »",
    "En 1815, monsieur Dantès avait vingt-deux ans ; il paraissait "
    "n'en avoir que dix-huit.",
    "Très bien.",
]


def demander(adresse, texte, voix, resultats, rang, verrou):
    corps = json.dumps({"texte": texte, "voix": voix},
                       ensure_ascii=False).encode("utf-8")
    requete = urllib.request.Request(
        adresse + "/tts", data=corps,
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(requete, timeout=600) as reponse:
        audio = reponse.read()
    calcul = time.time() - t0
    chemin = DOSSIER / ("phrase%d.wav" % rang)
    with verrou:
        chemin.write_bytes(audio)
    with wave.open(str(chemin), "rb") as f:
        duree = f.getnframes() / float(f.getframerate())
    resultats[rang] = (calcul, duree)


def main():
    analyseur = argparse.ArgumentParser()
    analyseur.add_argument("--adresse", default="http://127.0.0.1:8086")
    analyseur.add_argument("--front", type=int, default=2,
                           help="nombre de phrases envoyees DE FRONT")
    analyseur.add_argument("--voix", default="10087_11650_000028-0002")
    options = analyseur.parse_args()

    DOSSIER.mkdir(parents=True, exist_ok=True)
    verrou = threading.Lock()

    print("=" * 70)
    print("QWEN : UNE PAR UNE  contre  %d DE FRONT" % options.front)
    print("=" * 70)

    for mode, taille in (("une par une", 1), (("%d de front" % options.front),
                                              options.front)):
        resultats = {}
        t0 = time.time()
        fil = 0
        while fil < len(PHRASES):
            paquet = list(enumerate(PHRASES[fil:fil + taille], fil))
            fils = [threading.Thread(target=demander,
                                     args=(options.adresse, texte, options.voix,
                                           resultats, rang, verrou))
                    for rang, texte in paquet]
            for f in fils:
                f.start()
            for f in fils:
                f.join()
            fil += taille
        total_calcul = time.time() - t0
        total_audio = sum(d for _c, d in resultats.values())
        print("")
        print("  %-12s : %5.1f s d'audio en %5.1f s  ->  x%.2f le temps reel"
              % (mode, total_audio, total_calcul,
                 total_audio / total_calcul if total_calcul else 0))
        for rang in sorted(resultats):
            calcul, duree = resultats[rang]
            print("      phrase %d : %5.1f s de calcul pour %5.1f s d'audio"
                  " (x%.2f)" % (rang + 1, calcul, duree,
                                duree / calcul if calcul else 0))

    print("")
    print("Au-dessus de x1 : le moteur produit plus vite qu'on ne lit.")
    print("FIN")


if __name__ == "__main__":
    main()
