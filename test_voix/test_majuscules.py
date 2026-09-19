# -*- coding: utf-8 -*-
"""Verifie la correction des MAJUSCULES (demande de Laurent, 19/09/2026).

Constat : « les mots en majuscule donnent une prononciation bizarre ». Cause
mesuree : deux familles indiscernables a l'oeil nu —
  - des mots de la langue mis en majuscules pour insister (DE, LUI, MOI), que
    les moteurs traitent comme des sigles et lisent bizarrement ;
  - de VRAIS sigles (JFK, FBI, DSK), que le moteur doit EPELER.

La regle : un mot en majuscules ecrit AUSSI en casse normale dans le livre est
un mot de la langue -> on le remet en casse normale ; sinon c'est un sigle -> on
n'y touche pas.

Usage : python test_voix/test_majuscules.py
"""

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

from modules.majuscules import (enrichir_vocabulaire,          # noqa: E402
                                reduire_majuscules)
from modules.tts import _clean_text                            # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def egal(nom, obtenu, attendu):
    verifier(nom, obtenu == attendu, '%r (attendu %r)' % (obtenu, attendu))


def main_test():
    print('')
    print('=' * 70)
    print('LES MAJUSCULES : remises en casse normale avant le moteur')
    print('=' * 70)

    print('')
    print('1) le vocabulaire s apprend sur un texte')
    vocabulaire = {}
    enrichir_vocabulaire(
        'Le comte de Monte-Cristo arriva a la Bastille. Jim lui parla de JFK.',
        vocabulaire)
    verifier('« de » est appris', 'de' in vocabulaire)
    verifier('« Bastille » garde sa forme',
             vocabulaire.get('bastille') == 'Bastille',
             vocabulaire.get('bastille'))
    verifier('« Jim » est appris (majuscule initiale comprise)',
             vocabulaire.get('jim') == 'Jim', vocabulaire.get('jim'))
    verifier('« JFK » n est PAS appris (c est un sigle)',
             'jfk' not in vocabulaire)

    print('')
    print('2) les mots connus repassent en casse normale')
    egal('« DE » -> « de »', reduire_majuscules('Le DE du roi', vocabulaire),
         'Le de du roi')
    egal('« BASTILLE » -> « Bastille »',
         reduire_majuscules('il entra a la BASTILLE', vocabulaire),
         'il entra a la Bastille')
    egal('« JIM » -> « Jim »', reduire_majuscules('JIM arriva', vocabulaire),
         'Jim arriva')

    print('')
    print('3) les sigles et les chiffres romains ne sont PAS touches')
    egal('« JFK » reste JFK', reduire_majuscules('il vit JFK', vocabulaire),
         'il vit JFK')
    egal('« FBI » reste FBI', reduire_majuscules('le FBI enquete', vocabulaire),
         'le FBI enquete')
    egal('« XIV » reste XIV',
         reduire_majuscules('Louis XIV regnait', vocabulaire),
         'Louis XIV regnait')
    egal('une lettre seule reste (« M. »)',
         reduire_majuscules('M. de Morcerf', vocabulaire), 'M. de Morcerf')

    print('')
    print('4) sans vocabulaire, RIEN ne change (comportement d avant)')
    egal('texte inchange', reduire_majuscules('c est LUI', None), 'c est LUI')

    print('')
    print('5) dans le circuit complet du nettoyage')
    egal('« c est LUI ! » -> « c est lui, »',
         _clean_text('c\u2019est LUI !', vocabulaire), 'c\u2019est lui,')
    egal('et le sigle survit',
         _clean_text('le FBI arrive.', vocabulaire), 'le FBI arrive.')

    print('')
    print('6) sur un VRAI livre de Laurent (si la base est la)')
    base = os.path.join(RACINE, 'data', 'nimm_epub.db')
    if not os.path.exists(base):
        print('   (pas de base locale : controle ignore)')
        return ECHECS
    import main
    vrai = main._vocabulaire_du_livre(28)          # 22/11/63 (Stephen King)
    if not vrai:
        print('   (22/11/63 absent de la base : controle ignore)')
        return ECHECS
    print('   %d mots appris dans 22/11/63' % len(vrai))
    verifier('« LUI » est un mot du livre', 'lui' in vrai)
    verifier('« DE » est un mot du livre', 'de' in vrai)
    verifier('« JFK » n en est pas (sigle preserve)', 'jfk' not in vrai)
    egal('la correction marche sur le vrai vocabulaire',
         reduire_majuscules('c\u2019est LUI qui l\u2019a dit', vrai),
         'c\u2019est lui qui l\u2019a dit')

    return ECHECS


if __name__ == '__main__':
    echecs = main_test()
    print('')
    print('TOUT EST OK' if echecs == 0
          else '%d VERIFICATION(S) EN ECHEC' % echecs)
    sys.exit(0 if echecs == 0 else 1)
