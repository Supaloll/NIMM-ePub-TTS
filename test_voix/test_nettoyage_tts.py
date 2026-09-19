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
    # 19/09/2026 -- CE CONTROLE A ETE REFORMULE, et voici POURQUOI (pour que la
    # question ne revienne pas dans six mois).
    # Il s'appelait « le sujet de la phrase n'est jamais supprime » et exigeait
    # que « jeune homme » RESTE dans « j'ecoute, repondit le jeune homme ;
    # parlez. ». Il avait ete ecrit AVANT que le module apprenne les noms communs
    # avec article (« , dit le comte, »), et il ne passait que PAR ACCIDENT : le
    # « ; » n'etait alors pas reconnu comme une fin d'incise, donc l'incise etait
    # toujours gardee -- et LUE.
    # Laurent a tranche le 19/09/2026, apres avoir entendu le chapitre 96 du
    # Comte de Monte-Cristo : « repondit le jeune homme ; » se retire comme
    # « dit le comte ; », c'est la MEME construction. Le sujet de la REPLIQUE,
    # lui, n'est jamais touche : il reste « j'ecoute » et « parlez ».
    egal('incise a nom commun + point-virgule : RETIREE (19/09/2026)',
         "j\u2019\u00e9coute, r\u00e9pondit le jeune homme ; parlez.",
         "j\u2019\u00e9coute, parlez.")
    egal('point-virgule ORPHELIN en tete : nettoye',
         "criait Villefort ; o\u00f9 est-il ?", "o\u00f9 est-il ?")
    # Le vrai garde-fou, lui, reste : un mot qui CONTIENT un verbe de parole ne
    # doit pas etre pris pour une incise (frontiere de mot exigee).
    verifier('un mot en -dit n est pas pris pour une incise (frontiere de mot)',
             'maudit' in _clean_text("\u2014 Il partit, maudit-il."))
    # 19/09/2026 -- LE GESTE qui suit une incise FERMEE part avec elle (cas C1
    # du test adverse). Sans cela, « — Merci se levant. » laissait un mot
    # ORPHELIN, ce qui violait le garde-fou. Mesure : 2 phrases dans le tome 5.
    egal('geste apres une incise fermee : parti avec elle',
         '\u2014 Merci, dit Morrel, se levant.', '\u2014 Merci.')
    egal('geste « avec un ... » : parti avec l incise',
         '\u2014 Je pars, dit Morrel, avec un sourire.', '\u2014 Je pars.')
    # ...et les PIEGES : ce ne sont PAS des gestes, c'est la replique qui
    # continue. Les emporter effacerait du texte parle (piège repéré le meme
    # jour : un motif large sur « ...ant » attrapait « maintenant »).
    verifier('« maintenant » n est pas pris pour un participe',
             'maintenant' in _clean_text(
                 '\u2014 Il partit, dit-il, maintenant il faut partir.'))
    verifier('« pendant » n est pas pris pour un participe',
             'pendant' in _clean_text(
                 '\u2014 Il partit, dit-il, pendant que je le regardais.'))
    verifier('« avec vous » n est pas emporte (la replique continue)',
             'avec vous' in _clean_text('\u2014 Je pars, dit Morrel, avec vous.'))
    verifier('« en me regardant » n est pas emporte (pronom de replique)',
             'me regardant' in _clean_text(
                 '\u2014 Il partit, dit-il, en me regardant.'))
    # Une ENUMERATION de gestes part EN ENTIER : sinon il ne resterait que le
    # premier morceau retire et le texte serait bancal (« voyez avec un habit
    # ouvert... »). Constat fait a l'oreille, chapitre 90 du tome 5.
    enumeration = ('\u2014 Et puis, voyez, dit Beauchamp, avec un col, avec un '
                   'habit, avec un gilet blanc, que ne fait-il pas ?')
    verifier('une ENUMERATION de gestes part en entier',
             'avec un col' not in _clean_text(enumeration)
             and 'avec un gilet' not in _clean_text(enumeration))
    verifier('...et la suite de la replique est conservee',
             'que ne fait-il pas' in _clean_text(enumeration))

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
