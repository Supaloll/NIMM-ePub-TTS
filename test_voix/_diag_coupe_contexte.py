# -*- coding: utf-8 -*-
"""Pourquoi la coupe tombe-t-elle mal ? (diagnostic, lecture seule)

Montre la structure exacte de l'audio « contexte + phrase » : ou sont les
silences, ou finit le contexte seul, et ou la coupe a ete placee. Sert a
comprendre un residu de contexte (constat de Laurent, 17/09/2026).

Usage : python test_voix/_diag_coupe_contexte.py
"""

import io
import json
import sys
import urllib.request
import wave

sys.stdout.reconfigure(encoding='utf-8')

SERVICE = "http://127.0.0.1:8082"
VOIX = "2114_1656_000053-0001"
SEUIL = 0.012
PAS_S = 0.01

CONTEXTE = ("D'abord il y a une montagne, puis il n'y en a plus, puis il y a de "
            "nouveau une montagne.")
PHRASE = "Va faire un petit tour, avait dit Al."


def demander(texte, contexte=""):
    corps = {"texte": texte, "voix": VOIX}
    if contexte:
        corps["contexte"] = contexte
    requete = urllib.request.Request(
        SERVICE + "/tts", data=json.dumps(corps).encode('utf-8'),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=180) as reponse:
        return reponse.read()


def blocs(octets):
    """[(debut, fin, duree)] des blocs de son audible, en secondes."""
    import array
    with wave.open(io.BytesIO(octets), "rb") as f:
        frequence = f.getframerate()
        echantillons = array.array('h')
        echantillons.frombytes(f.readframes(f.getnframes()))
    pas = max(1, int(PAS_S * frequence))
    trouves = []
    for debut in range(0, len(echantillons), pas):
        bloc = echantillons[debut:debut + pas]
        if bloc and max(abs(v) for v in bloc) / 32768.0 >= SEUIL:
            if trouves and debut - trouves[-1][1] <= pas * 1.5:
                trouves[-1] = (trouves[-1][0], debut + len(bloc))
            else:
                trouves.append((debut, debut + len(bloc)))
    return ([(a / frequence, b / frequence, (b - a) / frequence)
             for a, b in trouves], len(echantillons) / frequence)


def afficher(titre, octets):
    trouves, duree = blocs(octets)
    print('')
    print('%s  --  duree %.2f s, %d bloc(s) de parole' % (titre, duree, len(trouves)))
    precedent = 0.0
    for debut, fin, longueur in trouves:
        silence = debut - precedent
        marque = '  <<< silence de %.2f s' % silence if silence >= 0.10 else ''
        print('    %6.2f -> %6.2f  (parle %.2f s)%s' % (debut, fin, longueur, marque))
        precedent = fin
    return trouves, duree


def main():
    print('contexte : « %s »  (%d caracteres)' % (CONTEXTE, len(CONTEXTE)))
    print('phrase   : « %s »' % PHRASE)

    c = demander(CONTEXTE)
    blocs_c, duree_c = afficher('CONTEXTE SEUL', c)
    fin_c = blocs_c[-1][1] if blocs_c else 0.0

    l = demander(PHRASE, CONTEXTE)
    blocs_l, duree_l = afficher('CONTEXTE + PHRASE (coupe appliquee)', l)

    s = demander(PHRASE)
    blocs_s, duree_s = afficher('PHRASE SEULE (reference)', s)

    print('')
    print('fin du contexte seul          : %.2f s' % fin_c)
    print('duree de la phrase seule      : %.2f s' % duree_s)
    print('duree de l audio coupe        : %.2f s' % duree_l)
    print('ecart (residu)                : %+.2f s' % (duree_l - duree_s))
    print('')
    print('A LIRE : si l audio coupe fait la duree de la phrase seule (a 0,3 s')
    print('pres), la coupe est bonne. Au-dela, un morceau du contexte reste.')
    return 0


if __name__ == '__main__':
    sys.exit(main())