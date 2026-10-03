# -*- coding: utf-8 -*-
"""Les NOMBRES en lettres : la batterie de controle.

Un module qui reecrit les nombres doit etre JUSTE : une graphie fausse
s'entendrait dans tout un livre, et serait pire que le defaut qu'elle corrige
(c'est la regle de l'atelier, deja ecrite pour les prenoms). D'ou cette
batterie : l'orthographe francaise des nombres, cas par cas.

Usage : python test_voix/test_nombres.py
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import nombres  # noqa: E402

ECHECS = 0


def verifier(attendu, obtenu, quoi):
    global ECHECS
    if attendu == obtenu:
        print('  OK    %-34s %s' % (quoi, obtenu))
    else:
        print('  ECHEC %-34s attendu : %s   obtenu : %s'
              % (quoi, attendu, obtenu))
        ECHECS += 1


# --- l'orthographe des nombres, cas par cas --------------------------------
NOMBRES = [
    (0, 'zero'),
    (1, 'un'),
    (9, 'neuf'),
    (17, 'dix-sept'),
    (20, 'vingt'),
    (21, 'vingt et un'),
    (22, 'vingt-deux'),
    (30, 'trente'),
    (70, 'soixante-dix'),
    (71, 'soixante et onze'),        # le seul « et » apres 60
    (72, 'soixante-douze'),
    (79, 'soixante-dix-neuf'),
    (80, 'quatre-vingts'),           # avec le s quand il finit le nombre
    (81, 'quatre-vingt-un'),         # sans s, et sans « et »
    (90, 'quatre-vingt-dix'),
    (91, 'quatre-vingt-onze'),
    (99, 'quatre-vingt-dix-neuf'),
    (100, 'cent'),
    (101, 'cent un'),
    (180, 'cent quatre-vingts'),
    (200, 'deux cents'),
    (201, 'deux cent un'),
    (999, 'neuf cent quatre-vingt-dix-neuf'),
    (1000, 'mille'),
    (1815, 'mille huit cent quinze'),
    (1954, 'mille neuf cent cinquante-quatre'),
    (2000, 'deux mille'),
    (80000, 'quatre-vingt mille'),   # « vingts » perd son s devant mille
    (800000, 'huit cent mille'),     # « cents » aussi
    (1000000, 'un million'),
    (2000000, 'deux millions'),
    (1000000000, 'un milliard'),
]

# --- les ordinaux ----------------------------------------------------------
ORDINAUX = [
    (1, 'premier'),
    (2, 'deuxieme'),
    (4, 'quatrieme'),
    (5, 'cinquieme'),                # cinq -> cinqu
    (9, 'neuvieme'),                 # neuf -> neuv
    (11, 'onzieme'),
    (20, 'vingtieme'),
    (80, 'quatre-vingtieme'),
    (100, 'centieme'),
]

# --- la reecriture dans une phrase -----------------------------------------
PHRASES = [
    ('La vie prend des virages à 180 degrés.',
     'La vie prend des virages à cent quatre-vingts degrés.'),
    ('Le 24 février 1815, la vigie signala le Pharaon.',
     'Le vingt-quatre février mille huit cent quinze, la vigie signala le Pharaon.'),
    ('50 % des gens, 3,5 fois plus.',
     'cinquante pour cent des gens, trois virgule cinq fois plus.'),
    ('Le 1er jour, la 1re fois, le 2e essai, le 9e rang.',
     'Le premier jour, la premiere fois, le deuxieme essai, le neuvieme rang.'),
    # --- et ce qu'il ne doit PAS toucher ---
    ('22/11/63', '22/11/63'),
    ('les pages 10-12', 'les pages 10-12'),
    ('le XXe siècle', 'le XXe siècle'),
]


def main():
    print('=' * 70)
    print('VERIFICATION : les nombres en lettres (modules/nombres.py)')
    print('=' * 70)
    print('')
    print("L'ORTHOGRAPHE DES NOMBRES")
    for valeur, attendu in NOMBRES:
        verifier(attendu, nombres.en_lettres(valeur), str(valeur))
    print('')
    print('LES ORDINAUX')
    for valeur, attendu in ORDINAUX:
        verifier(attendu, nombres.ordinal(valeur), str(valeur))
    print('')
    print('DANS UNE PHRASE')
    for avant, attendu in PHRASES:
        verifier(attendu, nombres.pour_lecture(avant), avant[:34])
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
