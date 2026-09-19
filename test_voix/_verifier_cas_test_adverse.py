# -*- coding: utf-8 -*-
"""Verifie les cas trouves par le TEST ADVERSE (Claude.AI, 19/09/2026).

Le document `REGLES_INCISES_a_eprouver.md` a ete donne a d'autres assistants
avec pour mission de CASSER les regles d'incises. Ce script passe leurs phrases
dans le VRAI code et montre, pour chacune :

  - le texte du livre ;
  - ce que le module en fait (`retirer_incises`) ;
  - ce que le moteur recoit vraiment (`_clean_text`).

Aucun jugement automatique : c'est Laurent (et la mesure sur un vrai tome) qui
tranche. Le script ne modifie RIEN.

Usage : python test_voix/_verifier_cas_test_adverse.py
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.incises import retirer_incises, incises_gardees      # noqa: E402
from modules.tts import _clean_text                               # noqa: E402

# Chaque cas : (numero, famille, ce que Claude annonce, la phrase du livre).
# Les familles : A = retrait a tort, B = retrait manque, C = effet de bord.
CAS = [
    # --- A1 : un verbe de parole employe comme verbe ordinaire (RECIT mange)
    ('A1', 'A', 'le recit disparait',
     'Il ouvrit la porte, appela la femme de chambre, et attendit.'),
    ('A1', 'A', 'le recit disparait', 'Il fit un pas.'),
    ('A1', 'A', 'le recit disparait', 'Morrel reprit le chemin de Marseille.'),
    ('A1', 'A', 'le recit disparait', 'Il appela Baptistin.'),
    ('A1', 'A', 'le recit disparait', 'Il interrogea Villefort.'),
    ('A1', 'A', 'le recit disparait', 'Il termina la lecture.'),
    # --- A2 : la relative fait partie de la replique
    ('A2', 'A', 'la replique est tronquee',
     '\u2014 C\u2019est lui, dit Morrel, qui l\u2019a voulu.'),
    ('A2', 'A', 'la replique est tronquee',
     '\u2014 Voici la lettre, dit Morrel, dont je vous parlais.'),
    # --- A3 : la relative emporte la fin de la replique
    ('A3', 'A', 'la fin de la replique part',
     '\u2014 Il faut, dit Morrel, qui pleurait, que tu partes.'),
    ('A3', 'A', 'la fin de la replique part',
     '\u2014 Oui, dit Morrel en regardant Valentine, qui p\u00e2lit, oui.'),
    # --- A4 : les imperatifs de la liste
    ('A4', 'A', 'un ordre de la replique disparait',
     '\u2014 Parle, dis la v\u00e9rit\u00e9, et je t\u2019\u00e9coute.'),
    ('A4', 'A', 'un ordre de la replique disparait',
     '\u2014 Viens, demande une chaise \u00e0 Baptistin, et assieds-toi.'),
    ('A4', 'A', 'un ordre de la replique disparait',
     '\u2014 Pars, ajoute un couvert, et reviens.'),
    # --- A5 : « dis-nous » est un imperatif, pas une incise
    ('A5', 'A', 'un ordre de la replique disparait',
     '\u2014 Voyons, dis-nous, Morrel, ce que tu sais.'),
    # --- A6 : la branche virgule de `_etendre` n a pas le garde-fou
    ('A6', 'A', 'la fin de la replique part',
     '\u2014 Oui, dit Morrel vous avez raison, mais j\u2019h\u00e9site.'),
    # --- B1 : l incise a PRONOM en tete de morceau (le decoupage la separe)
    ('B1', 'B', 'lue alors qu elle ne devrait pas', 'dit-il.'),
    ('B1', 'B', 'lue alors qu elle ne devrait pas', 'demanda-t-elle.'),
    ('B1', 'B', 'lue alors qu elle ne devrait pas',
     's\u2019\u00e9cria-t-elle en pleurant.'),
    # --- B2 : les noms composes
    ('B2', 'B', 'nom composes non reconnus',
     '\u2014 Non, dit le comte de Monte-Cristo.'),
    ('B2', 'B', 'nom composes non reconnus',
     '\u2014 Non, dit Valentine de Villefort.'),
    ('B2', 'B', 'nom composes non reconnus', '\u2014 Non, dit M. Morrel p\u00e8re.'),
    ('B2', 'B', 'nom composes non reconnus', '\u2014 Non, dit l\u2019abb\u00e9 Faria.'),
    ('B2', 'B', 'nom composes non reconnus',
     '\u2014 Non, dit le procureur du roi.'),
    # --- B3 : les verbes absents de la liste
    ('B3', 'B', 'verbe absent de la liste', '\u2014 Il partit, chuchota-t-il.'),
    ('B3', 'B', 'verbe absent de la liste',
     '\u2014 Il partit, lan\u00e7a Morrel.'),
    ('B3', 'B', 'verbe absent de la liste', '\u2014 Il partit, pensa le comte.'),
    # --- B4 : le reflexif manque dans le motif a NOM
    ('B4', 'B', 'reflexif non reconnu', '\u2014 Il partit, se dit Morrel.'),
    ('B4', 'B', 'reflexif non reconnu', '\u2014 Il partit, se demanda le comte.'),
    # --- B5 : les adverbes et les complements non reconnus
    ('B5', 'B', 'adverbe non reconnu', '\u2014 Il partit, dit-il alors.'),
    ('B5', 'B', 'adverbe non reconnu',
     '\u2014 Il partit, r\u00e9pondit Morrel froidement.'),
    ('B5', 'B', 'adverbe non reconnu', '\u2014 Il partit, dit le comte gravement.'),
    # --- B6 : le tiret ne ferme pas l incise
    ('B6', 'B', 'tiret fermant non reconnu',
     '\u2014 Je vous \u00e9coute \u2014 dit Morrel \u2014 parlez.'),
    # --- B7 : les imparfaits pluriels absents de la liste
    ('B7', 'B', 'imparfait pluriel absent', '\u2014 Il partit, disaient-ils.'),
    # --- C1 : le participe reste orphelin apres une incise FERMEE
    ('C1', 'C', 'participe orphelin', '\u2014 Merci, dit Morrel, se levant.'),
    ('C1', 'C', 'participe orphelin',
     '\u2014 Je pars, dit Morrel, avec un sourire.'),
    ('C1', 'C', 'participe orphelin', '\u2014 Il partit, dit le comte, souriant.'),
    # --- C2 : le recit colle a la replique
    ('C2', 'C', 'recit colle a la replique',
     '\u2014 Adieu, dit Morrel, et il sortit.'),
    ('C2', 'C', 'recit colle a la replique',
     '\u2014 Il partit, dit Morrel, tandis que Valentine pleurait.'),
    # --- C3 : la virgule du vocatif est mangee
    ('C3', 'C', 'virgule du vocatif mangee', '\u2014 Non, dit le comte, jamais.'),
    ('C3', 'C', 'virgule du vocatif mangee',
     '\u2014 Comte, dit Morrel, vous ici ?'),
    # ==========================================================
    # DEUXIEME RETOUR : Mistral (19/09/2026, meme document)
    # Ces cas sont comptes a part : le tri se fait au meme endroit.
    # ==========================================================
    ('M-A1', 'M', 'la subordonnee serait perdue (dit-il)',
     'Je ne sais, murmura-t-il en baissant les yeux, si cela est juste.'),
    ('M-A2', 'M', 'la virgule de « avant que » serait perdue',
     'Partons, dit-il, avant que la nuit ne tombe !'),
    ('M-A3', 'M', 'la relative serait detachee',
     'C\u2019est lui, s\u2019\u00e9cria-t-elle, qui a tout fait !'),
    ('M-B1', 'M', 'verbe absent de la liste', 'Je vous en prie, chuchota-t-elle.'),
    ('M-B2', 'M', 'complement avant le nom',
     'Non, dit avec un rire amer le comte.'),
    ('M-B3', 'M', 'incise suivie de « et » : non retiree ?',
     'Il est parti, dit Morrel, et il ne reviendra pas.'),
    ('M-B4', 'M', '« de nouveau » non capture',
     'Qui est l\u00e0 ? demanda-t-il de nouveau.'),
    ('M-B5', 'M', 'le sujet serait retire a tort',
     'Le comte, dit-il, est un homme dangereux.'),
    ('M-C1', 'M', 'double ponctuation', 'Bonjour, dit-il ; comment allez-vous ?'),
    ('M-C2', 'M', 'phrase trop courte apres retrait', 'Je ne sais, r\u00e9pondit-il.'),
    ('M-C3', 'M', 'virgule orpheline devant « et »',
     'Il part, dit-il, et elle reste.'),
]

TITRES = {'A': 'A. RETRAIT A TORT (le plus grave)',
          'B': 'B. RETRAIT MANQUE',
          'C': 'C. EFFET DE BORD',
          'M': 'M. DEUXIEME RETOUR (Mistral) — a trier'}


def main():
    print('=' * 78)
    print('LES CAS DU TEST ADVERSE (Claude.AI), PASSES DANS LE VRAI CODE')
    print('=' * 78)
    print('')
    print('  RETIRE = le module modifie la phrase ;  garde = il n y touche pas.')
    famille = None
    retires = 0
    for numero, fam, annonce, phrase in CAS:
        if fam != famille:
            famille = fam
            print('')
            print('-' * 78)
            print('%s' % TITRES.get(fam, fam))
            print('-' * 78)
        parle = retirer_incises(phrase)
        retire = (parle != phrase)
        if retire:
            retires += 1
        print('')
        print('  [%s] %s  ->  %s' % (numero, annonce,
                                     'RETIRE' if retire else 'garde'))
        print('      livre  : %s' % phrase)
        print('      parle  : %s' % parle)
        print('      moteur : %s' % _clean_text(phrase))
    print('')
    print('=' * 78)
    print('%d cas sur %d sont TOUCHES par le module.' % (retires, len(CAS)))
    print('La LECTURE de ce tableau dit lesquels sont des defauts, lesquels non.')
    print('=' * 78)


if __name__ == '__main__':
    main()
