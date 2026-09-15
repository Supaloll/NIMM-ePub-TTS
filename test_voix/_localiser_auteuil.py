# -*- coding: utf-8 -*-
"""
Localise PRECISEMENT la scene du diner d'Auteuil dans les tomes de Laurent
(session du 14/09/2026).

Laurent n'a pas entendu le passage ou les invites arrivent a la maison
d'Auteuil et ou Bertuccio montre Villefort au Comte. Or le texte semble
complet : on cherche donc dans QUEL chapitre numerote se trouve cette scene,
pour verifier si elle est bien dans le livre qu'il a ecoute.

Lancer depuis la racine : python test_voix/_localiser_auteuil.py
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

RE_CHAP = re.compile(r'Chapitre\s+(\d+)')

for f in fichiers:
    chapters = get_chapters(str(f))
    chapitres = {}          # numero -> liste de phrases
    courant = None
    for c in chapters:
        for para in (c.get('text') or '').split('\n\n'):
            m = RE_CHAP.search(para)
            if m and len(para) < 80:
                courant = int(m.group(1))
                chapitres.setdefault(courant, [])
            if courant is not None:
                chapitres[courant].append(para)

    trouves = []
    for num, paras in sorted(chapitres.items()):
        texte = '\n'.join(paras)
        if re.search(r'Auteuil', texte) and re.search(r'Bertuccio', texte):
            # On regarde si la scene des invites y est (Villefort + arrivee)
            indice = ('Villefort' in texte)
            trouves.append((num, len(paras), indice))

    if trouves:
        print('')
        print('=== {} ==='.format(f.name[:58]))
        for num, nparas, avec_villefort in trouves:
            print('   chapitre {:>3} : {} paragraphes, Villefort cite : {}'.format(
                num, nparas, 'oui' if avec_villefort else 'non'))

print('')
print('Fin de la localisation.')
