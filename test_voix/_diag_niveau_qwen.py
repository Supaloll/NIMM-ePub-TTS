# -*- coding: utf-8 -*-
"""
POURQUOI le volume de Qwen reste bas ? Mesure le BRUT du moteur et ce que le
lecteur en fait (29/09/2026, retour d'ecoute de Laurent : « le volume a tendance
a un peu plus varier que les autres moteurs »).

Mesure faite juste avant : par le LECTEUR, Qwen rend median 5,96 % de la pleine
echelle, alors que la cible de `modules/audio_gain.py` est 8,5 % et qu'Edge rend
9,29 %. On cherche donc ou le gain se perd :

  1. le BRUT du service Qwen (port 8086, aucune retouche) : niveau + CRETE ;
  2. la MEME phrase par le lecteur (port 8081, normalisation comprise) ;
  3. on affiche ce que la normalisation a reellement gagne, et si la CRETE
     plafonne (rappel : `CRETE_MAX_POURCENT` = 98 %, et le gain est borne par
     `GAIN_MAX` = x4).

LECTURE SEULE : rien n'est ecrit, rien n'est modifie.

Usage : python test_voix/_diag_niveau_qwen.py
"""
import io
import json
import math
import sys
import urllib.request
import wave
from array import array

sys.stdout.reconfigure(encoding="utf-8")

SERVICE_QWEN = "http://127.0.0.1:8086/tts"
LECTEUR = "http://127.0.0.1:8081/api/tts"
VOIX = "af_nicole"          # l'identifiant, sans prefixe, cote service

PHRASES = [
    "Le vent soufflait sur la lande, et personne ne savait ce qui allait arriver.",
    "Est-ce que quelqu'un a pense a fermer la porte de la grange ?",
]

FENETRE_S = 0.030
SEUIL_PAROLE = 0.02 * 32768.0


def appeler(url, charge):
    corps = json.dumps(charge).encode("utf-8")
    requete = urllib.request.Request(url, data=corps,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
    with urllib.request.urlopen(requete, timeout=600) as reponse:
        return reponse.read()


def mesures(octets):
    """(niveau de parole en %, crete en %) d'un WAV en memoire."""
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        frequence = fichier.getframerate()
        echantillons = array("h")
        echantillons.frombytes(fichier.readframes(fichier.getnframes()))
    pas = max(1, int(FENETRE_S * frequence))
    crete = max(max(echantillons), -min(echantillons)) * 100.0 / 32768.0
    niveaux = []
    for debut in range(0, len(echantillons) - pas + 1, pas):
        fenetre = echantillons[debut:debut + pas]
        if max(max(fenetre), -min(fenetre)) < SEUIL_PAROLE:
            continue
        carres = sum(float(v) * v for v in fenetre) / len(fenetre)
        niveaux.append(100.0 * (carres ** 0.5) / 32768.0)
    if not niveaux:
        return 0.0, crete
    niveaux.sort()
    return niveaux[len(niveaux) // 2], crete


def en_db(a, b):
    if a <= 0 or b <= 0:
        return 0.0
    return 20.0 * math.log10(a / b)


def main():
    print("")
    print("=" * 74)
    print(" D'OU VIENT LE VOLUME DE QWEN ? brut du moteur contre lecteur")
    print("=" * 74)
    print(" cible du module audio_gain : 8,5 %   |   plafond de crete : 98 %")
    print("")
    for phrase in PHRASES:
        print("« %s… »" % phrase[:60])
        try:
            brut = appeler(SERVICE_QWEN, {"texte": phrase, "voix": VOIX})
            niveau_brut, crete_brute = mesures(brut)
            lecteur = appeler(LECTEUR, {"text": phrase,
                                        "voice": "qwen:" + VOIX,
                                        "rate": "+0%", "pitch": "+0Hz",
                                        "book_id": 0})
            niveau_lecteur, crete_lecteur = mesures(lecteur)
        except Exception as e:
            print("   ERREUR : %s" % str(e)[:70])
            continue
        print("   moteur BRUT    : parole %5.2f %%   crete %5.1f %%"
              % (niveau_brut, crete_brute))
        print("   par le LECTEUR : parole %5.2f %%   crete %5.1f %%"
              % (niveau_lecteur, crete_lecteur))
        print("   gain applique  : %+.2f dB   (pour aller a 8,5 %% il faudrait "
              "%+.2f dB)" % (en_db(niveau_lecteur, niveau_brut),
                             en_db(8.5, niveau_brut)))
        print("")
    print(" Lecture : si la crete du brut est haute, le gain est PLAFONNE par")
    print(" CRETE_MAX (98 %) -- et la cible de 8,5 % n'est jamais atteinte.")
    print("")
    print(" Rien n'a ete modifie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
