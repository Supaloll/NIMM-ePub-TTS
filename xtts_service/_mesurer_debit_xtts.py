# -*- coding: utf-8 -*-
"""Mesure le DEBIT du moteur XTTS sur des repliques courtes (outil jetable).

Pourquoi cet outil (retour d'ecoute de Laurent, 15/09/2026) : a l'ecoute d'un
livre, il a entendu des « changements de rythme », surtout sur les successions
de petites phrases echangees entre deux interlocuteurs, et il soupconne le
prechargement du lecteur d'etre un peu juste.

Hypothese a verifier : le cout de calcul d'une phrase XTTS est presque FIXE
(extraction de la voix de reference + calcul), quelle que soit la duree de la
phrase -- ce qui penaliserait les courtes repliques de dialogue.

    >>> HYPOTHESE INFIRMEE PAR LA MESURE (RTX 4060, 15/09/2026) <<<
    Repliques courtes : 0,47 s de calcul pour 1,4 s d'audio (facteur 0,32).
    Phrase longue     : 4,78 s de calcul pour 15,7 s d'audio (facteur 0,30).
    Le cout est donc PROPORTIONNEL a la duree (ratio long/court = 1,0) et le
    moteur produit ~3 fois plus vite que la lecture : ce n'est PAS le debit du
    moteur qui fait « casser » le rythme des dialogues. Piste a regarder
    ailleurs : le silence de QUEUE, long et VARIABLE d'une phrase a l'autre
    (0,54 a 0,91 s mesures sur les WAV du lot) -- voir _mesurer_bords_xtts.py.
    Cet outil reste utile : il permet de refaire la mesure apres tout
    changement (autre carte, autre version du moteur, autre voix).

L'outil envoie deux series de phrases a voix haute (le moteur doit etre
allume), chronometre chaque generation et compare au temps de lecture :

    facteur = temps de calcul / duree de l'audio produit

    facteur < 1  ->  moteur PLUS RAPIDE que la lecture (marge = 1 / facteur)
    facteur > 1  ->  moteur plus LENT : la file de prechargement se videra

Ce n'est PAS un test automatique : il ne fait qu'afficher des mesures.

Usage :
    .venv\\Scripts\\python.exe _mesurer_debit_xtts.py
    .venv\\Scripts\\python.exe _mesurer_debit_xtts.py --voix cml9804
    .venv\\Scripts\\python.exe _mesurer_debit_xtts.py --repetitions 3

Le moteur s'allume avec DEMARRER_XTTS.bat.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import wave

sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:8083"

# Repliques courtes (le cas qui pose probleme) et une phrase de narration
# longue (le cas qui marche). Textes volontairement simples : on mesure du
# temps de calcul, pas la qualite de la voix.
COURTES = [
    "Oui, monsieur.",
    "Que voulez-vous ?",
    "Il est parti.",
    "Merci, monsieur.",
    "Prenez garde.",
    "Je ne sais pas.",
]

LONGUE = (
    "Le navire, apres avoir longe la cote pendant plusieurs heures, "
    "finit par jeter l'ancre dans la petite baie, et les hommes de "
    "l'equipage se mirent aussitot au travail, tandis que le jeune "
    "capitaine observait la mer avec une attention que rien ne "
    "semblait pouvoir distraire."
)


def _get_json(chemin, delai=10.0):
    with urllib.request.urlopen(BASE + chemin, timeout=delai) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def sante():
    """(pret, texte lisible) -- jamais d'exception."""
    try:
        infos = _get_json("/sante", delai=5.0)
    except urllib.error.URLError as erreur:
        return False, "aucune reponse sur %s (%s)" % (BASE, erreur)
    except Exception as erreur:
        return False, "reponse illisible sur %s (%s)" % (BASE, erreur)
    if not infos.get("pret"):
        return False, "moteur present mais PAS encore pret"
    return True, "%s -- %s voix" % (infos.get("appareil", "?"),
                                    infos.get("voix", "?"))


def generer(texte, voix, delai=240.0):
    """Envoie une phrase, renvoie (secondes de calcul, octets WAV)."""
    corps = json.dumps({"texte": texte, "voix": voix}).encode("utf-8")
    demande = urllib.request.Request(
        BASE + "/tts", data=corps,
        headers={"Content-Type": "application/json"})
    debut = time.time()
    with urllib.request.urlopen(demande, timeout=delai) as reponse:
        wav = reponse.read()
    return time.time() - debut, wav


def duree_wav(octets):
    """Duree en secondes d'un WAV en memoire."""
    import io
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        return fichier.getnframes() / float(fichier.getframerate())


def liste_voix():
    try:
        return _get_json("/voix", delai=5.0).get("voix") or []
    except Exception:
        return []


def mesurer(etiquette, textes, voix, repetitions):
    """Mesure une serie de phrases ; renvoie le bilan (ou None)."""
    print("")
    print("--- %s (%d phrase(s) x %d) ---"
          % (etiquette, len(textes), repetitions))
    print("%-46s %8s %8s %8s" % ("phrase", "calcul", "audio", "facteur"))

    calculs, facteurs = [], []
    for _ in range(repetitions):
        for texte in textes:
            try:
                secondes, wav = generer(texte, voix)
            except Exception as erreur:
                print("  ECHEC sur « %s » : %s" % (texte[:40], erreur))
                continue
            duree = duree_wav(wav)
            facteur = (secondes / duree) if duree > 0 else 0.0
            calculs.append(secondes)
            facteurs.append(facteur)
            coupe = texte if len(texte) <= 44 else texte[:41] + "..."
            print("%-46s %7.2fs %7.2fs %8.2f"
                  % (coupe, secondes, duree, facteur))

    if not facteurs:
        return None
    bilan = {
        "etiquette": etiquette,
        "calcul_moyen": sum(calculs) / len(calculs),
        "facteur_moyen": sum(facteurs) / len(facteurs),
        "facteur_mini": min(facteurs),
        "facteur_maxi": max(facteurs),
        "nombre": len(facteurs),
    }
    print("  temps de calcul moyen : %.2f s   facteur : moyen %.2f "
          "(mini %.2f / maxi %.2f)"
          % (bilan["calcul_moyen"], bilan["facteur_moyen"],
             bilan["facteur_mini"], bilan["facteur_maxi"]))
    return bilan


def main():
    parseur = argparse.ArgumentParser(
        description="Mesure le debit du moteur XTTS sur des repliques courtes.")
    parseur.add_argument(
        "--voix", default="",
        help="identifiant de voix (defaut : la premiere du catalogue)")
    parseur.add_argument(
        "--repetitions", type=int, default=2,
        help="nombre de passages sur chaque phrase (defaut 2)")
    options = parseur.parse_args()

    pret, texte_sante = sante()
    print("Moteur %s : %s" % (BASE, texte_sante))
    if not pret:
        print("")
        print("Rien a mesurer pour l'instant : allume le moteur avec "
              "DEMARRER_XTTS.bat, puis relance cet outil.")
        return 1

    voix = options.voix
    if not voix:
        disponibles = liste_voix()
        if not disponibles:
            print("Aucune voix dans le catalogue du moteur.")
            return 1
        voix = disponibles[0]
    print("Voix mesuree : %s" % voix)

    courte = mesurer("repliques courtes (dialogue)", COURTES, voix,
                     options.repetitions)
    longue = mesurer("phrase longue (narration)", [LONGUE], voix,
                     options.repetitions)

    print("")
    print("=== Lecture des chiffres ===")
    print("facteur = temps de calcul / duree de l'audio produit")
    for bilan in (courte, longue):
        if not bilan:
            continue
        facteur = bilan["facteur_moyen"]
        if facteur <= 0:
            continue
        if facteur < 1.0:
            verdict = ("plus RAPIDE que la lecture : marge x%.1f"
                       % (1.0 / facteur))
        else:
            verdict = ("PLUS LENT que la lecture : la file de prechargement "
                       "se videra sur ce genre de phrases")
        print("  %-34s facteur %.2f -> %s"
              % (bilan["etiquette"], facteur, verdict))
    if courte and longue and courte["facteur_moyen"] > 0:
        rapport = longue["facteur_moyen"] / courte["facteur_moyen"]
        print("  Rapport longue / courte : %.2f" % rapport)
        print("  Proche de 1,0 -> le cout est proportionnel a la duree (aucun")
        print("  cout fixe par phrase : les dialogues ne sont pas penalises).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

