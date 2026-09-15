# -*- coding: utf-8 -*-
"""Verification du nettoyage du texte avant envoi a XTTS (15/09/2026).

A lancer avec le Python du LECTEUR (aucun moteur necessaire) :
    python test_voix/test_nettoyage_xtts.py

Pourquoi : XTTS ne sait pas ignorer la ponctuation de dialogue, contrairement a
Edge, Kokoro et Piper. A l'ecoute du lot comparatif du 15/09/2026 (voix
Bertrand), Laurent a entendu le moteur PRONONCER les guillemets (« ogui ...
haa ») et buter sur le tiret cadratin (« vous eteetes sur de vous »). Le
service les retire donc avant d'envoyer le texte (nettoyer_pour_xtts).

Ce test verifie que le nettoyage enleve EXACTEMENT ce qu'il faut -- et surtout
qu'il ne touche pas au reste : un tiret d'union (« demanda-t-il »), une
apostrophe ou des points de suspension effaces casseraient le texte lu.
"""

import os
import sys
from importlib.util import module_from_spec, spec_from_file_location

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

# Le service n'importe que la bibliotheque standard au chargement : on peut le
# lire sans demarrer le moteur ni charger PyTorch.
CHEMIN = os.path.join(RACINE, 'xtts_service', 'servir_xtts.py')
_spec = spec_from_file_location('servir_xtts_test', CHEMIN)
service = module_from_spec(_spec)
_spec.loader.exec_module(service)

net = service.nettoyer_pour_xtts
ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + repr(detail) if detail != '' else ''))
        ECHECS += 1


def egal(nom, texte, attendu):
    obtenu = net(texte)
    verifier(nom, obtenu == attendu, '%r  (attendu %r)' % (obtenu, attendu))


def main():
    print('')
    print('1) guillemets : le moteur les prononçait, on les retire')
    egal('phrase de reference du lot',
         '\u00ab Vous \u00eates s\u00fbr de vous, monsieur ? \u00bb '
         'demanda-t-il en souriant.',
         'Vous \u00eates s\u00fbr de vous, monsieur ? demanda-t-il en souriant.')
    egal('guillemets droits anglais',
         '"Bonjour", dit-il.', 'Bonjour , dit-il.')
    egal('guillemets courbes', '\u201cBonjour\u201d, dit-il.', 'Bonjour , dit-il.')
    egal('dialogue avec ponctuation interne',
         '\u00ab Que voulez-vous ? dit-il. Il est d\u00e9j\u00e0 trop tard ! \u00bb',
         'Que voulez-vous ? dit-il. Il est d\u00e9j\u00e0 trop tard !')

    print('')
    print('2) tiret cadratin : retire en tete, virgule pour une incise')
    egal('tiret ouvrant (le defaut « eteetes »)',
         '\u2014 Vous \u00eates s\u00fbr de vous, monsieur ? demanda-t-il.',
         'Vous \u00eates s\u00fbr de vous, monsieur ? demanda-t-il.')
    egal('deux repliques dans le meme morceau',
         '\u2014 Bonjour. \u2014 Bonjour.',
         'Bonjour., Bonjour.')
    egal('incise encadree',
         'Il arriva \u2014 enfin \u2014 \u00e0 midi.',
         'Il arriva, enfin, \u00e0 midi.')

    print('')
    print('3) ce qui NE DOIT PAS changer')
    egal('tiret d union (demanda-t-il)', 'demanda-t-il en souriant.',
         'demanda-t-il en souriant.')
    egal('trait d union dans « est-ce »', 'est-ce que tu viens ?',
         'est-ce que tu viens ?')
    egal('apostrophe droite', "l'homme qui dort", "l'homme qui dort")
    egal('apostrophe typographique', 'l\u2019homme qui dort',
         'l\u2019homme qui dort')
    egal('points de suspension', 'Il h\u00e9sita\u2026 puis parla.',
         'Il h\u00e9sita\u2026 puis parla.')
    egal('phrase ordinaire, inchangee',
         'Le train partit \u00e0 huit heures du matin.',
         'Le train partit \u00e0 huit heures du matin.')
    egal('virgules et points-virgules conserves',
         'Il partit ; elle resta, sans rien dire.',
         'Il partit ; elle resta, sans rien dire.')

    print('')
    print('4) securite')
    egal('morceau qui ne contient que des guillemets', '\u00ab \u00bb', '')
    egal('moins de 250 caracteres conserve (limite du moteur)',
         'a' * 240, 'a' * 240)
    phare = ('\u00ab ' + 'mot ' * 60 + '\u00bb')
    verifier('un long morceau ne perd pas de mots',
             len(net(phare).split()) == len(('\u00ab ' + 'mot ' * 60 + '\u00bb').split()) - 2,
             len(net(phare).split()))

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    print('=' * 70)
    print('VERIFICATION : nettoyage du texte avant XTTS (guillemets, tirets)')
    print('=' * 70)
    sys.exit(main())
