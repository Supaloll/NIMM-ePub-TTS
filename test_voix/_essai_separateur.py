# -*- coding: utf-8 -*-
"""Quel separateur force une VRAIE pause entre le contexte et la phrase ?

Le modele enchainait parfois contexte et phrase SANS pause detectable : la coupe
n'avait alors aucun reperage fiable (constat de Laurent, 17/09/2026). Ce script
essaie trois separateurs ecrits entre les deux et montre, pour chacun, ou se
trouve le premier silence franc APRES le contexte.

Usage : python test_voix/_essai_separateur.py
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

SEPARATEURS = [
    ("espace simple (actuel)", " "),
    ("points de suspension", " ... "),
    ("saut de ligne", "\n"),
    ("point-virgule", " ; "),
]


def demander(texte):
    corps = {"texte": texte, "voix": VOIX}
    requete = urllib.request.Request(
        SERVICE + "/tts", data=json.dumps(corps).encode('utf-8'),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=180) as reponse:
        return reponse.read()


def blocs(octets):
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
    return ([(a / frequence, b / frequence) for a, b in trouves],
            len(echantillons) / frequence)


def main():
    print('')
    print('=' * 78)
    print('QUEL SEPARATEUR FORCE UNE PAUSE FRANCHE APRES LE CONTEXTE ?')
    print('=' * 78)
    print('contexte (%d car.) : « %s »' % (len(CONTEXTE), CONTEXTE[:60]))
    print('phrase   : « %s »' % PHRASE)
    print('')

    for titre, separateur in SEPARATEURS:
        texte = CONTEXTE + separateur + PHRASE
        trouves, duree = blocs(demander(texte))
        # Les silences internes, du plus long au plus court.
        silences = []
        for rang in range(1, len(trouves)):
            longueur = trouves[rang][0] - trouves[rang - 1][1]
            if longueur >= 0.10:
                silences.append((round(longueur, 2), round(trouves[rang][0], 2)))
        silences.sort(reverse=True)
        print('  %-26s duree %5.2fs  silences : %s'
              % (titre, duree,
                 ', '.join('%.2fs a %.2fs' % (longueur, debut)
                           for longueur, debut in silences[:4]) or 'AUCUN'))
    print('')
    print('A LIRE : un separateur interessant fait apparaitre un silence franc')
    print('juste apres le contexte (donc un repere fiable pour la coupe).')
    return 0


if __name__ == '__main__':
    sys.exit(main())