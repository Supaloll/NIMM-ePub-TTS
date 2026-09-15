# -*- coding: utf-8 -*-
"""
Liste les TITRES des chapitres des tomes de Monte-Cristo (session du
14/09/2026) : ils permettent de reperer precisement une scene (par exemple
« Le diner d'Auteuil ») et de verifier qu'aucun chapitre ne manque.

Lancer depuis la racine : python test_voix/_titres_chapitres_monte_cristo.py
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters

DOSSIER = Path(r'D:/Livres Epub')
fichiers = sorted([f for f in DOSSIER.rglob('*.epub') if 'Monte-Cristo - Tome' in f.name])

RE_CHAP = re.compile(r'^\s*Chapitre\s+(\d+)\s*:?\s*(.*)$', re.IGNORECASE)

for f in fichiers:
    chapters = get_chapters(str(f))
    print('')
    print('=' * 78)
    print(f.name[:70])
    print('=' * 78)
    for c in chapters:
        for ligne in (c.get('text') or '').split('\n'):
            ligne = ligne.strip()
            if len(ligne) > 90:
                continue
            m = RE_CHAP.match(ligne)
            if m:
                num = int(m.group(1))
                titre = (m.group(2) or '').strip()
                print('  {:>3} : {}'.format(num, titre if titre else '(titre sur la ligne suivante ?)'))

print('')
print('Fin de la liste.')
