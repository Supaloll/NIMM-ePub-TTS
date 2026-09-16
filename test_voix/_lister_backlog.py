# -*- coding: utf-8 -*-
"""Liste les items NON COCHES du BACKLOG, par section.

Sert a faire le point en debut de session : « qu'est-ce qui reste, et dans quel
ordre ? ». Lecture seule.

Usage :
    python test_voix/_lister_backlog.py            (items ouverts seulement)
    python test_voix/_lister_backlog.py --tous     (ajoute les items livres)
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BACKLOG = Path(__file__).resolve().parent.parent / 'BACKLOG.md'
TOUS = '--tous' in sys.argv

lignes = BACKLOG.read_text(encoding='utf-8').splitlines()
section = '(sans section)'
ouverts = 0
livres = 0
numero_section = 0

print('=' * 78)
print('BACKLOG : ce qui reste a faire, par section')
print('=' * 78)

for ligne in lignes:
    if ligne.startswith('## '):
        section = ligne.lstrip('# ').strip()
        print('')
        print('[%s]' % section)
        print('-' * 78)
        continue
    if ligne.startswith('- [ ]'):
        titre = ligne[6:].strip()
        # Le titre peut tenir sur plusieurs lignes : on prend la suite tant que
        # la ligne suivante n'est pas un nouvel item ni une liste vide.
        print('   A FAIRE  %s' % titre[:104])
        ouverts += 1
    elif ligne.startswith('- [x]') and TOUS:
        print('   fait     %s' % ligne[6:].strip()[:104])
        livres += 1
    elif ligne.startswith('- [x]'):
        livres += 1

print('')
print('=' * 78)
print('Items a faire : %d   |   items livres : %d' % (ouverts, livres))
