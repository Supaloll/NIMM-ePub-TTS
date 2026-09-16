# -*- coding: utf-8 -*-
"""Verifie le garde-fou anti-BABIL du service XTTS (session du 16/09/2026).

Contexte : sur un texte court, le moteur de clonage partait en bouillie
(« Que preferez-vous ? » : 19 caracteres -> 9,11 s d'audio, dont ~4 s de
babil). Le service borne desormais la longueur de generation d'apres le texte,
et rogne en dernier recours.

Les fonctions sont extraites DE servir_xtts.py (jamais recopiees) : si elles
changent la-bas, ce test les suit. Le moteur n'est PAS charge : on verifie la
logique, pas la synthese.

Usage : python test_voix/test_borne_babil_xtts.py
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np                                              # noqa: E402

SERVICE = RACINE / 'xtts_service' / 'servir_xtts.py'

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def espace_du_service():
    source = SERVICE.read_text(encoding='utf-8')
    bornes = [
        ('MAX_CARACTERES = 250', '# Une seule generation a la fois'),
        ('def duree_max_morceau', 'def _lire_un_morceau'),
    ]
    espace = {}
    for debut_balise, fin_balise in bornes:
        fragment = source[source.index(debut_balise):source.index(fin_balise)]
        exec(compile(fragment, str(SERVICE), 'exec'), espace)
    return espace


def main_verifications():
    espace = espace_du_service()
    duree_max = espace['duree_max_morceau']
    tokens_max = espace['tokens_max_morceau']
    rogner = espace['rogner_a_duree']
    frequence = espace['FREQUENCE']

    print('')
    print('1) la borne grandit avec le texte (et reste large)')
    for taille, attendu_min, attendu_max in ((10, 1.5, 2.5), (19, 2.5, 3.6),
                                             (28, 3.5, 5.0), (120, 14.0, 17.0),
                                             (250, 30.0, 35.0)):
        borne = duree_max('x' * taille)
        verifier('texte de %3d caracteres : borne ~%.2f s'
                 % (taille, borne), attendu_min <= borne <= attendu_max, borne)

    print('')
    print('2) la borne ne gene JAMAIS une phrase de longueur normale')
    # Duree naturelle estimee : environ 14 caracteres par seconde.
    for taille in (20, 60, 120, 250):
        naturelle = taille / 14.0
        verifier('texte de %3d caracteres : borne (%.1f s) > rythme naturel (%.1f s)'
                 % (taille, duree_max('x' * taille), naturelle),
                 duree_max('x' * taille) > naturelle * 1.5)

    print('')
    print('3) les jetons demandes au moteur restent dans les clous')
    verifier('texte minuscule : jamais moins de %d jetons'
             % espace['TOKENS_MINIMUM'],
             tokens_max('Oui.') >= espace['TOKENS_MINIMUM'], tokens_max('Oui.'))
    verifier('texte enorme : plafonne a %d jetons' % espace['TOKENS_PLAFOND'],
             tokens_max('x' * 5000) == espace['TOKENS_PLAFOND'],
             tokens_max('x' * 5000))
    verifier('la borne de « Que preferez-vous ? » laisse passer ~1,4 s de parole',
             tokens_max('Que preferez-vous ?') * espace['SECONDES_PAR_TOKEN'] >= 1.6,
             tokens_max('Que preferez-vous ?') * espace['SECONDES_PAR_TOKEN'])

    print('')
    print('4) le rognage de secours')
    # 9,11 s de signal (le babil constate) contre une borne de ~3 s.
    babil = np.ones(int(9.11 * frequence), dtype=np.float32)
    coupe = rogner(babil, duree_max('Que preferez-vous ?'))
    obtenue = coupe.size / float(frequence)
    verifier('un audio de 9,11 s est ramene sous la borne',
             abs(obtenue - duree_max('Que preferez-vous ?')) < 0.02,
             '%.2f s' % obtenue)
    # Un audio normal ne doit pas etre touche.
    normal = np.ones(int(1.4 * frequence), dtype=np.float32)
    verifier('un audio de longueur normale n est pas touche',
             rogner(normal, duree_max('Que preferez-vous ?')).size == normal.size)
    # Un audio vide reste vide.
    verifier('un audio vide ne casse rien',
             rogner(np.zeros(0, dtype=np.float32), 3.0).size == 0)
    # Une duree absurde ne fait pas planter.
    verifier('une duree aberrante est absorbee sans erreur',
             rogner(normal, 0.0).size in (0, normal.size))


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : garde-fou anti-babil du service XTTS')
    print('=' * 66)
    main_verifications()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    sys.exit(0 if ECHECS == 0 else 1)
