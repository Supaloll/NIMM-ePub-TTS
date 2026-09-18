# -*- coding: utf-8 -*-
"""Verification des regles de texte avant synthese (18/09/2026).

A lancer avec le Python du LECTEUR (aucun moteur necessaire) :
    python test_voix/test_nettoyage_tts.py

Ce qui est verifie, apres la journee d'ecoute du 18/09/2026 :

1. POINT D'EXCLAMATION retire du texte envoye au moteur. Laurent entendait
   « OOOOOOoooooh » sur les interjections : les moteurs neuronaux jouent le
   « ! » comme une montee de hauteur. Le texte AFFICHE garde son « ! ».
2. POINT FINAL NON AJOUTE apres une abreviation developpee (M. -> Monsieur).
   La page decoupe les phrases apres le point d'une abreviation, donc le moteur
   recevait un morceau finissant par « ... complimenter Monsieur » ; le point
   final ajoute en faisait une vraie fin de phrase, d'ou le silence entendu.
3. Ce qui NE DOIT PAS changer : les reglages d'ecoute precedents
   (point-virgule -> virgule, parenthese -> virgules, deux-points -> virgule).
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.tts import _clean_text

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


def egal(nom, texte, attendu):
    obtenu = _clean_text(texte)
    verifier(nom, obtenu == attendu, '%r  (attendu %r)' % (obtenu, attendu))


def main():
    print('')
    print('=' * 74)
    print('VERIFICATION : texte envoye au moteur de voix (exclamations, abreviations)')
    print('=' * 74)

    print('')
    print('1) le point d\'exclamation ne fait plus monter la voix')
    print('   (banc du 18/09/2026 : VIRGULE dans les phrases courtes, POINT dans')
    print('    les phrases entieres — deux choix de Laurent a l\'ecoute)')
    egal('interjection courte -> virgule', 'Oh !', 'Oh,')
    egal('replique courte -> virgule', 'Il partit !', 'Il partit,')
    egal('exclamation collee au mot', 'Viens!', 'Viens,')
    egal('exclamations en rafale', 'Oh !!', 'Oh,')
    egal('exclamation dans une replique courte',
         '\u00ab Va-t\'en ! \u00bb', '\u00ab Va-t\'en, \u00bb')
    egal('phrase entiere -> point (choix de Laurent)',
         '\u2014 Cela recommence, comte !', '\u2014 Cela recommence, comte.')
    egal('exclamation dans une phrase longue',
         'Bonjour ! Comment vas-tu ?', 'Bonjour. Comment vas-tu ?')
    egal('interrogation + exclamation',
         'Quoi ?!', 'Quoi ?')

    print('')
    print('2) pas de point final apres une abreviation (le silence de Laurent)')
    egal('M. en fin de morceau (le cas entendu)',
         'Le temps de complimenter M.', 'Le temps de complimenter Monsieur')
    egal('M. au milieu de la phrase',
         'Le lendemain, M. de Morcerf partit.',
         'Le lendemain, Monsieur de Morcerf partit.')
    egal('Mme en fin de morceau',
         'Il salua Mme', 'Il salua Madame')
    egal('MM. en fin de morceau',
         'Ils attendirent MM.', 'Ils attendirent Messieurs')
    egal('Dr en fin de morceau',
         'Il appela le Dr', 'Il appela le Docteur')

    print('')
    print('3) une phrase ordinaire garde son point final')
    egal('phrase qui se termine par un mot normal',
         'Il arriva enfin', 'Il arriva enfin.')
    egal('phrase deja ponctuee', 'Il partit.', 'Il partit.')
    egal('fin de morceau sur une virgule',
         'Il partit, elle resta,', 'Il partit, elle resta.')

    print('')
    print('4) les reglages precedents tiennent toujours (17/09/2026)')
    egal('point-virgule -> virgule',
         'Il partit ; elle resta.', 'Il partit, elle resta.')
    egal('parentheses -> virgules',
         'Paul (son frere) arriva.', 'Paul, son frere, arriva.')
    egal('deux-points -> virgule',
         'Il dit : bonjour.', 'Il dit, bonjour.')
    egal('points de suspension conserves',
         'Il h\u00e9sita\u2026 puis parla.', 'Il h\u00e9sita\u2026 puis parla.')

    print('')
    print('5) les incises de parole sont retirees du texte parle')
    print('   (decision de Laurent, 18/09/2026 : « la voix me parait plus fluide »)')
    egal('incise a pronom terminale',
         '\u2014 Il partit, dit-il.', '\u2014 Il partit.')
    egal('incise a nom encadree',
         '\u2014 Le fait est, dit Barrois, que je meurs de soif.',
         '\u2014 Le fait est que je meurs de soif.')
    egal('incise suivie d un complement : retiree EN ENTIER (18/09 au soir)',
         '\u2014 Il partit, dit-il en souriant.', '\u2014 Il partit.')
    egal('incise terminale avec complement',
         'bonjour, dit-il au comte.', 'bonjour.')
    egal('incise en TETE de phrase (apres un « ! » qui coupe)',
         'fit celui-ci avec sa voix demi-railleuse, comment vous portez-vous ?',
         'comment vous portez-vous ?')
    egal('phrase qui n est QUE l incise : gardee entiere (jamais videe)',
         'ajouta Valentine en s\u2019adressant \u00e0 Noirtier.',
         'ajouta Valentine en s\u2019adressant \u00e0 Noirtier.')
    verifier('le sujet de la phrase n est jamais supprime',
             'jeune homme' in _clean_text(
                 "j\u2019\u00e9coute, r\u00e9pondit le jeune homme ; parlez."))

    print('')
    print('6) les abreviations collees a une majuscule (le « mleu » du banc)')
    # Le tome 5 contient « Mlle\xa0Eugénie » (espace insecable, 72 cas) : le banc
    # d'ecoute envoie le texte BRUT, d'ou le « mleu » qu'il a entendu. La
    # lecture, elle, developpe l'abreviation AVANT l'envoi au moteur.
    egal('Mlle avant un prenom',
         'par Mlle\u00a0Eugénie.', 'par Mademoiselle\u00a0Eugénie.')
    egal('Mme avant un prenom',
         'Mme\u00a0Danglars arriva.', 'Madame\u00a0Danglars arriva.')

    print('')
    print('%d controles, %d en echec' % (CONTROLES, ECHECS))
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
