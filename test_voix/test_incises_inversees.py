# -*- coding: utf-8 -*-
"""Vérification des INCISES INVERSÉES (24/09/2026) — le correctif du soir.

A lancer avec le Python du LECTEUR (aucun moteur nécessaire) :
    python test_voix/test_incises_inversees.py

Pourquoi : Laurent a entendu, dans 22/11/63, l'incise « m'a-t-il dit avec son
plaisant accent du Sud. » dite par le PERSONNAGE. Mesure du 24/09/2026 :
**132 sur 139** incises de cette famille échappaient au module dans ce livre,
**52 sur 68** dans le tome 5 de Monte-Cristo. Le français met le sujet inversé
AVANT le verbe (« m'a-t-il dit », « m'annonça-t-il ») et l'incise coupée dans sa
propre phrase commence par une majuscule avec un pronom (« Demanda-t-elle. ») :
deux formes que rien ne couvrait.

Ce qui est vérifié, et pourquoi chaque bloc existe :
  1. les formes inversées sont **reconnues**, et la version PARLÉE est la bonne
     (c'est elle que Laurent entend) ;
  2. le **cas exact de Laurent** (phrase #150 du livre 28), figé en dur ;
  3. les formes qui RESTENT dehors : c'est une **décision assumée** (voir
     `modules/incises.py`), et le test la fige pour qu'un changement futur soit
     conscient ;
  4. le **piège écarté** : « Dis voir, Mike … » ne perd jamais son « Dis voir, »
     (rendre le motif de tête insensible à la casse l'abîmait) ;
  5. une **vraie question** n'est JAMAIS touchée (« A-t-il mangé ? »,
     « M'a-t-il dit la vérité ? ») : c'est le risque principal du correctif ;
  6. le **garde-fou vital** : une phrase qui n'est qu'une incise garde son texte
     (sinon elle disparaîtrait de l'écoute) — et `_est_incise_seule` la voit,
     donc elle devient un court silence (mode « incises muettes ») ou un morceau
     confié au narrateur (mode « incises lues »).
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.incises import incises, retirer_incises                   # noqa: E402
from main import _est_incise_seule                                     # noqa: E402

ECHECS = 0
CONTROLES = 0


def verifier(nom, condition, detail=''):
    global ECHECS, CONTROLES
    CONTROLES += 1
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + repr(detail) if detail != '' else ''))
        ECHECS += 1


# (entrée, version parlée attendue) — la clé, c'est la DEUXIÈME colonne : c'est
# ce que le moteur reçoit, donc ce que l'oreille de Laurent entend.
RECONNUES = (
    ('demanda-t-elle.', 'demanda-t-elle.'),          # garde-fou : rien à vider
    ('Demanda-t-elle.', 'Demanda-t-elle.'),
    ('murmura-t-il.', 'murmura-t-il.'),
    ('dit-il.', 'dit-il.'),
    ('gueula-t-il.', 'gueula-t-il.'),
    ('« Entre, m\u2019a-t-il dit.', '« Entre.'),
    ('« Je suis désolé, m\u2019a-t-il dit.', '« Je suis désolé.'),
    ('« Je voulais juste vous remercier pour tout », me dit-il.',
     '« Je voulais juste vous remercier pour tout ».'),
    ('murmura-t-il, dans ma maison !', 'dans ma maison !'),
    ('s\u2019écria-t-il, plaignez-moi, secourez-moi.',
     'plaignez-moi, secourez-moi.'),
    ('« Monsieur Andrea, lui dit-il, n\u2019êtes-vous pas un peu jeune ?',
     '« Monsieur Andrea n\u2019êtes-vous pas un peu jeune ?'),
    # --- Le sujet « je » et l'auxiliaire SANS objet (24/09/2026) ------------
    # C'est la forme la plus fréquente de 22/11/63 : mesure du 24/09, sans elle
    # le livre 28 ne corrigeait que 66 phrases, avec elle 203.
    ('\u2013 Epping, ai-je dit spontanément, trop pris de court.',
     '\u2013 Epping trop pris de court.'),
    ('\u2013 Exact, a-t-il confirmé.', '\u2013 Exact.'),
    ('\u2013 Je ne sais pas encore \u00bb, ai-je répondu.',
     '\u2013 Je ne sais pas encore \u00bb.'),
    ('Ces bagnoles appartiennent à de vrais ouvriers, ai-je pensé.',
     'Ces bagnoles appartiennent à de vrais ouvriers.'),
    # Une phrase qui n'est QU'une incise garde son texte (garde-fou vital) : elle
    # part en court silence, ou au narrateur selon le réglage du livre.
    (', lui ai-je recommandé.', ', lui ai-je recommandé.'),
)

# Décisions ASSUMÉES (voir le bloc « INCISES INVERSÉES » de modules/incises.py) :
# ces formes restent au personnage, et le test le fige.
NON_RECONNUES = (
    # Incise de NOM en tête MAJUSCULE : sa variante insensible à la casse a été
    # mesurée puis ÉCARTÉE (elle abîmait « Dis voir, Mike, … »).
    'Fit celui-ci avec sa voix demi-railleuse, comment vous portez-vous ?',
    'Repondit Morrel.',
    # Il faudrait élargir `DEBUT_COMPLEMENT` à « de ce ton… » (non retenu).
    '« Je t\u2019aime », m\u2019a-t-elle dit de ce ton cassant.',
    # Objet + VERBE + NOM (« me dit Annette ») : autre forme, autre motif.
    ', me dit Annette Founijello.',
)

# Le risque principal : une VRAIE question ressemble à s'y méprendre à une
# incise inversée. Aucune ne doit être touchée.
QUESTIONS = (
    'A-t-il mangé ?',
    'M\u2019a-t-il dit la vérité ?',
    'Est-il parti ?',
    'Ai-je bien fait de venir ?',
    'Que m\u2019a-t-il répondu ?',
    'S\u2019est-elle levée tôt ?',
)

# Une question qui SE TERMINE par une incise : la question reste, l'incise part.
QUESTION_ET_INCISE = (
    ('Ai-je bien fait de venir, ai-je pensé ?', 'Ai-je bien fait de venir ?'),
)

# Le piège écarté : ce n'est pas une incise, c'est une interpellation.
PAS_UNE_INCISE = (
    'Dis voir, Mike, vous nous préparez quoi, les gars, pour la rentrée ?',
    'dis voir, Mike, vous nous préparez quoi, les gars, pour la rentrée ?',
    'Dis voir Mike.',
)


def main():
    print('')
    print('=' * 74)
    print('VERIFICATION : les incises inversees (m a-t-il dit, demanda-t-elle)')
    print('=' * 74)

    print('')
    print('1) les formes inversees sont reconnues, et la version parlee est juste')
    for entree, attendu in RECONNUES:
        parle = retirer_incises(entree)
        verifier('%r -> %r' % (entree[:40], attendu[:34]), parle == attendu,
                 parle)

    print('')
    print('2) le cas de Laurent (livre 28, chapitre 14)')
    phrase = ('\u00ab Si seulement vous étiez là tout le temps, monsieur '
              'Amberson, m\u2019a-t-il dit avec son plaisant accent du Sud.')
    attendu = ('\u00ab Si seulement vous étiez là tout le temps, '
               'monsieur Amberson')
    verifier("l'incise de la phrase #150 est vue", bool(incises(phrase)),
             [phrase[a:b] for a, b in incises(phrase)])
    verifier("l'incise part EN ENTIER (avec son complement « avec son "
             "plaisant accent du Sud »)", retirer_incises(phrase) == attendu,
             retirer_incises(phrase))
    verifier("ce n'est PAS une incise seule (la replique reste)",
             not _est_incise_seule(phrase))

    print('')
    print('3) les formes qui restent dehors : decision ASSUMEE, figee ici')
    for entree in NON_RECONNUES:
        verifier('%r non reconnue' % entree[:44], not incises(entree),
                 [entree[a:b] for a, b in incises(entree)])

    print('')
    print('4) le piege ecarte : « Dis voir » n est JAMAIS avale')
    for entree in PAS_UNE_INCISE:
        verifier('%r intacte' % entree[:44], not incises(entree)
                 and retirer_incises(entree) == entree)

    print('')
    print('5) une VRAIE question n est jamais touchee')
    for entree in QUESTIONS:
        verifier('%r intacte' % entree[:44], not incises(entree)
                 and retirer_incises(entree) == entree)
    for entree, attendu in QUESTION_ET_INCISE:
        verifier('%r -> la question seule reste' % entree[:40],
                 retirer_incises(entree) == attendu, retirer_incises(entree))

    print('')
    print('6) garde-fou vital : une phrase-incise garde son texte, et devient '
          'un morceau a part')
    verifier("« demanda-t-elle. » : incise seule -> court silence (ou narrateur)",
             _est_incise_seule('demanda-t-elle.'))
    verifier("« dit-il. » : idem", _est_incise_seule('dit-il.'))
    verifier("« « Entre, m\u2019a-t-il dit. » : PAS une incise seule (la "
             "replique « Entre » reste)",
             not _est_incise_seule('\u00ab Entre, m\u2019a-t-il dit.'))
    verifier("« « Entre, dit-il. » : la replique reste aussi",
             not _est_incise_seule('\u2014 Entre, dit-il.'))

    print('')
    print('%d controles, %d en echec' % (CONTROLES, ECHECS))
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
