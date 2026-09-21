# -*- coding: utf-8 -*-
"""Quel separateur fait une pause FRANCHE, et TOUJOURS LA MEME, entre le contexte
et la phrase ?

QUESTION DE LAURENT (21/09/2026) : « Est-ce qu'il existe une ponctuation qui est
traitee toujours de la meme facon par Kyutai ? Si oui, on aurait un point fixe de
secondes, toujours le meme, sans que ca ne deforme la phrase [...] Le truc c'est
qu'il faut une ponctuation qui ne provoque pas de coupure dans le contexte qu'on
lui aurait donne. »

C'est exactement le bon raisonnement : quand la coupe se fie a une ESTIMATION
(la part du contexte dans le total), elle tombe bien ou mal selon le tirage --
le moteur n'est pas deterministe. Avec un separateur dont la pause est CONSTANTE
et RECONNAISSABLE, la coupe devient mecanique : on cherche ce silence-la, on
coupe a sa fin, et la phrase commence.

Ce que ce script mesure, pour chaque separateur, sur PLUSIEURS ESSAIS (c'est la
nouveaute : la constance, pas seulement l'existence) :
  - la duree de la PREMIERE pause franche apres le contexte (le repere) ;
  - sa position, et l'ecart entre le plus court et le plus long des essais.

A LIRE : un bon separateur fait une pause LONGUE, toujours de la meme longueur
(ecart faible), et plus longue que n'importe quelle pause naturelle des trois
mots de contexte -- sinon on couperait au mauvais endroit.

Le moteur doit etre allume. Usage : python test_voix/_essai_separateur.py
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
ESSAIS = 3                       # combien de fois on redemande la meme chose

# Les trois mots de contexte tels que la page les envoie aujourd'hui
# (CONTEXTE_MOTS = 3), puis la phrase a lire.
CONTEXTE = "une montagne."
CONTEXTE_PIEGE = "pas, alors"
PHRASE = "Va faire un petit tour, avait dit Al."

SEPARATEURS = [
    ("espace seule", " "),
    ("virgule", " , "),
    ("point", " . "),
    ("points de suspension", " ... "),
    ("point d'interrogation", " ? "),
    ("point d'exclamation", " ! "),
    ("point-virgule", " ; "),
    ("deux-points", " : "),
    ("saut de ligne", "\n"),
    ("tiret cadratin", " \u2014 "),
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


def une_passe(titre_passe, contexte, separateurs=None):
    """Le tableau d'une passe : un separateur par ligne, ESSAIS essais chacun."""
    separateurs = separateurs or SEPARATEURS
    print('')
    print(titre_passe)
    print('  contexte : « %s »' % contexte)
    print('')
    print('  %-24s %-40s %8s %8s' % ('separateur', 'plus longs silences (essais)',
                                     'moyenne', 'ecart'))
    print('  ' + '-' * 86)

    for titre, separateur in separateurs:
        texte = contexte + separateur + PHRASE
        pauses = []
        details = []
        for _ in range(ESSAIS):
            trouves, _duree = blocs(demander(texte))
            silences = []
            for rang in range(1, len(trouves)):
                longueur = trouves[rang][0] - trouves[rang - 1][1]
                if longueur >= 0.10:
                    silences.append((longueur, trouves[rang][0]))
            if silences:
                # On regarde la pause LA PLUS LONGUE : c'est celle du separateur
                # si elle est bien plus longue que les pauses naturelles du
                # contexte (une virgule en fait une de ~0,5 s).
                pauses.append(max(silences)[0])
                details.append('%.2f@%.2f' % max(silences))
            else:
                details.append('AUCUNE')
        if pauses:
            moyenne = sum(pauses) / len(pauses)
            ecart = max(pauses) - min(pauses)
        else:
            moyenne = ecart = 0.0
        print('  %-24s %-40s %7.2fs %7.2fs'
              % (titre, ', '.join(details), moyenne, ecart))


def main():
    print('')
    print('=' * 88)
    print('QUEL SEPARATEUR FAIT UNE PAUSE FRANCHE, ET TOUJOURS LA MEME ?')
    print('=' * 88)
    print('Phrase a lire : « %s »' % PHRASE)
    print('%d essais par separateur : c est la CONSTANCE qui compte.' % ESSAIS)

    une_passe('1) Contexte SANS ponctuation interne (« une montagne. »)', CONTEXTE)
    # Passe 2 : les trois candidats les plus prometteurs seulement -- c'est la
    # question que Laurent se pose (« et si la ponctuation du contexte elle-meme
    # faisait une pause ? »). La virgule interne est dans le contexte.
    une_passe('2) Contexte AVEC une virgule (« pas, alors ») : la virgule du '
              'contexte',
              CONTEXTE_PIEGE,
              [candidat for candidat in SEPARATEURS
               if candidat[0] in ("espace seule", "points de suspension",
                                  "point d'exclamation")])

    print('')
    print('A LIRE : chaque essai s ecrit « duree@position ». Un bon separateur')
    print('donne une pause LONGUE, un ECART FAIBLE entre les essais, et une pause')
    print('PLUS LONGUE que celle de la virgule interne du contexte (passe 2) --')
    print('sinon la coupe tomberait dans le contexte, ce que Laurent redoutait.')
    return 0


if __name__ == '__main__':
    sys.exit(main())