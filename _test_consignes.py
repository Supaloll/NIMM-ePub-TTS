# -*- coding: utf-8 -*-
"""Jetable : quelle CONSIGNE fait vraiment corriger le modele local ?

Le 29/09/2026, avec la consigne « corrige uniquement ce qui est mal transcrit »,
le modele a laisse passer LE cas d'ecole : « le trois males pharaon » au lieu de
« le trois-mats le Pharaon » (Monte-Cristo). Avec une consigne qui DONNAIT cet
exemple, il avait trouve la bonne correction. On compare donc deux variantes sur
le meme texte, et on regarde ce qui change.
"""

import json
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

OLLAMA = "http://127.0.0.1:11434/api/generate"
MODELE = "qwen3:8b"

TEXTE = ("Le 24 février 1815, la vigie de Notre-Dame de la Garde signala le "
         "trois mâles pharaon venant de Smyrne, Trieste et Naples. Comme "
         "d'habitude, un pilote côtier partit aussitôt du port, rasa le château "
         "d'If et alla aborder le navire entre le cap de Morgue.")

# Variante A : consigne stricte, sans exemple (celle qui a echoue).
CONSIGNE_A = """Tu recois la transcription automatique d'un extrait de livre audio
en francais. Corrige uniquement les mots mal transcrits, sans reformuler.
Reponds uniquement par le texte corrige.

TRANSCRIPTION :
%s"""

# Variante B : la meme, avec UN exemple du type d'erreur a trouver.
CONSIGNE_B = """Tu recois la transcription automatique d'un extrait de livre audio
en francais (classiques du domaine public). L'outil de reconnaissance vocale se
trompe surtout sur les mots rares et les noms propres : il ecrit par exemple
« le trois males pharaon » pour « le trois-mats le Pharaon » (Monte-Cristo).

Corrige les mots mal transcrits, en gardant tout le reste tel quel (aucune
reformulation, aucune modernisation). Reponds uniquement par le texte corrige.

TRANSCRIPTION :
%s"""


def demander(consigne, pense):
    corps = json.dumps({
        "model": MODELE,
        "prompt": consigne % TEXTE,
        "stream": False,
        "think": pense,
        "options": {"temperature": 0},
    }).encode("utf-8")
    requete = urllib.request.Request(OLLAMA, data=corps,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
    with urllib.request.urlopen(requete, timeout=900) as reponse:
        return json.loads(reponse.read().decode("utf-8", "replace"))


def main():
    print("=" * 74)
    print(" QUELLE CONSIGNE CORRIGE VRAIMENT ? (texte d'Aubin)")
    print("=" * 74)
    print("AVANT : %s" % TEXTE[:90])
    print("")
    for nom, consigne, pense in (("A. stricte, sans exemple", CONSIGNE_A, False),
                                 ("B. avec exemple", CONSIGNE_B, False),
                                 ("C. avec exemple + raisonnement", CONSIGNE_B, True)):
        debut = time.time()
        try:
            donnees = demander(consigne, pense)
        except Exception as e:
            print("%-32s ERREUR : %s" % (nom, str(e)[:60]))
            continue
        reponse = (donnees.get("response") or "").strip().splitlines()
        texte = reponse[-1] if reponse else ""
        corrige = "trois-mâts" in texte or "trois-mats" in texte
        print("%-32s %5.0f s   corrige « trois-mâts » : %s"
              % (nom, time.time() - debut, "OUI" if corrige else "non"))
        print("      %s" % texte[:150])
        print("")
    print("Rien n'a ete modifie dans le projet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
