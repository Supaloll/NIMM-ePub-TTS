# -*- coding: utf-8 -*-
"""
Mesure LECTURE SEULE : les NOMS portes par les voix du catalogue, par famille.

Pourquoi (29/09/2026) : Laurent veut que l'ecoute d'une voix dise
« Bonjour, je suis <nom> » au lieu de la phrase de reference. Encore faut-il que
le nom soit PRONONCABLE : un identifiant technique (« Femme001 », « 577_394 »)
donnerait une phrase absurde. Cet outil dit, famille par famille, combien de
noms sont lisibles et combien ne le sont pas.
"""
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(RACINE))

from modules.tts import (KOKORO_VOICES, PIPER_VOICES, KYUTAI_VOICES,  # noqa: E402
                         QWEN_VOICES, XTTS_VOICES, NEUTTS_VOICES,
                         POCKET_VOICES)

# Un nom est considere PRONONCABLE s'il contient au moins une lettre, s'il tient
# en quelques mots, et s'il ne porte ni chiffre ni souligne (marques des
# identifiants de fichiers venus du clonage).
TECHNIQUE = re.compile(r"[\d_]|^\s*$")


def lisible(nom: str) -> bool:
    nom = (nom or "").strip()
    if TECHNIQUE.search(nom):
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]", nom)) and len(nom) <= 40


def examiner(nom_famille, liste):
    total = len(liste)
    illisibles = [v.get("name", "") for v in liste
                  if not lisible(v.get("name", ""))]
    print("")
    print("--- {} : {} voix ---".format(nom_famille, total))
    if not total:
        return
    exemple = liste[0]
    print("  champs d'une entree : {}".format(", ".join(sorted(exemple.keys()))))
    print("  exemples : {}".format(
        " | ".join(str(v.get("name", "")) for v in liste[:6])))
    if total > 6:
        print("  (fin)    : {}".format(
            " | ".join(str(v.get("name", "")) for v in liste[-3:])))
    print("  noms NON prononcables : {} sur {}".format(len(illisibles), total))
    for nom in illisibles[:10]:
        print("      {}".format(nom))


def main():
    try:
        import main  # FRENCH_VOICES (Edge) vit dans main.py, pas dans tts.py
        edge = main.FRENCH_VOICES
    except Exception as e:
        print("Edge (FRENCH_VOICES) illisible : {}".format(e))
        edge = []

    examiner("Edge (FRENCH_VOICES)", edge)
    examiner("Kokoro", KOKORO_VOICES)
    examiner("Piper", PIPER_VOICES)
    examiner("Kyutai", KYUTAI_VOICES)
    examiner("Qwen", QWEN_VOICES)
    examiner("XTTS", XTTS_VOICES)
    examiner("NeuTTS", NEUTTS_VOICES)
    examiner("Pocket", POCKET_VOICES)
    print("")


if __name__ == "__main__":
    main()
