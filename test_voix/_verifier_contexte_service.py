# -*- coding: utf-8 -*-
"""Verifie qu'AUCUN mot du contexte ne traine devant la phrase (lecture seule).

CONSTAT DE LAURENT (17/09/2026) : apres un saut de ligne, il entendait le dernier
mot du paragraphe precedent avant la phrase du nouveau paragraphe :

    « ... puis il y a de nouveau une montagne. »   (fin de paragraphe)
    « Va faire un petit tour, avait dit Al. »      (phrase suivante)
    -> entendu : « montagne. Va faire un petit tour, avait dit Al. »

Cause : la coupe tombait sur une VIRGULE du contexte, donc trop tot. Ce script
verifie la correction -- et servira a chaque fois qu'on touche a la coupe.

COMMENT IL JUGE : il demande au moteur (a) la phrase SEULE et (b) « contexte +
phrase », coupee. Si la coupe est bonne, les deux durees sont proches. Un ecart
de plus d'une seconde annonce un residu de contexte.

Le moteur doit etre allume. Usage :
    python test_voix/_verifier_contexte_service.py
    python test_voix/_verifier_contexte_service.py --voix 2114_1656_000053-0001
"""

import argparse
import io
import json
import sys
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

SERVICE = "http://127.0.0.1:8082"
VOIX_DEFAUT = "2114_1656_000053-0001"       # Claude (Monte-Cristo T2)

# Le cas rapporte par Laurent, plus deux autres pieges (virgules nombreuses).
CAS = [
    ("le cas de Laurent (saut de ligne)",
     "D'abord il y a une montagne, puis il n'y en a plus, puis il y a de nouveau une montagne.",
     "Va faire un petit tour, avait dit Al."),
    ("contexte riche en virgules",
     "Il prit le chemin, lentement, sans se retourner, et disparut derriere la colline.",
     "Le lendemain, personne ne parla plus de lui."),
    ("phrase longue apres un contexte lo",
     "Elle ferma la porte, posa son sac sur la chaise, et regarda longuement la fenetre.",
     "Dehors, la pluie continuait de tomber sur les toits du vieux quartier, et les "
     "rues se vidaient peu a peu."),
    # Le cas rapporte par Laurent le 17/09/2026 au soir : le contexte tel que la
    # page l'envoie (les derniers mots de la phrase precedente).
    ("« pas marche » (cas de Laurent)",
     "mais ca n'a pas marche.",
     "Les philosophes et les psychologues peuvent debattre de ce qui est reel et de "
     "ce qui ne l'est pas, mais nous qui vivons des vies ordinaires nous connaissons "
     "et acceptons pour la plupart la texture du monde qui nous entoure."),
]


def demander(texte, voix, contexte=""):
    corps = {"texte": texte, "voix": voix}
    if contexte:
        corps["contexte"] = contexte
    requete = urllib.request.Request(
        SERVICE + "/tts", data=json.dumps(corps).encode('utf-8'),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=180) as reponse:
        return reponse.read()


def duree(octets):
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        return fichier.getnframes() / float(fichier.getframerate())


def main():
    analyseur = argparse.ArgumentParser(
        description="Verifie qu'aucun mot du contexte ne traine devant la phrase.")
    analyseur.add_argument('--voix', default=VOIX_DEFAUT)
    options = analyseur.parse_args()

    print('')
    print('=' * 78)
    print('CONTROLE DE LA COUPE DU CONTEXTE  (moteur Kyutai)')
    print('=' * 78)
    print('voix : %s' % options.voix)
    print('')
    print('  %-34s %8s %8s %8s   %s'
          % ('cas', 'seule', 'coupee', 'ecart', 'verdict'))

    souci = 0
    for titre, contexte, phrase in CAS:
        seule = demander(phrase, options.voix)
        coupee = demander(phrase, options.voix, contexte)
        d1, d2 = duree(seule), duree(coupee)
        ecart = d2 - d1
        # Une coupe juste donne des durees voisines (le contexte ajoute au plus
        # une respiration). Au-dela d'une seconde, il reste un mot du contexte.
        verdict = 'OK'
        if ecart > 1.0:
            verdict = 'RESIDU DE CONTEXTE ?'
            souci += 1
        elif ecart < -0.8:
            verdict = 'PHRASE AMPUTEE ?'
            souci += 1
        print('  %-34s %7.2fs %7.2fs %+7.2fs   %s'
              % (titre[:34], d1, d2, ecart, verdict))

    print('')
    if souci:
        print('A REGARDER : %d cas douteux.' % souci)
        return 1
    print('TOUT EST OK : la phrase coupee fait la meme longueur que la phrase seule.')
    return 0


if __name__ == '__main__':
    sys.exit(main())