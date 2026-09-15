# -*- coding: utf-8 -*-
"""
Verifie si les passages signales par Laurent existent bien dans ses tomes de
Monte-Cristo (session du 14/09/2026).

Laurent soupconne des passages manquants dans son tome 3 : le diner de la
maison d'Auteuil, l'arrivee des invites (Danglars, Villefort, Morel), et
Bertuccio montrant Villefort au Comte.

On cherche donc, dans chaque tome, les lieux et personnages cles de ce
passage, et on repere les TITRES de chapitres presents.

Lancer depuis la racine : python test_voix/_verifier_monte_cristo.py
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

DOSSIER = Path(r'D:\Livres Epub')

fichiers = sorted([f for f in DOSSIER.rglob('*.epub') if 'Monte-Cristo - Tome' in f.name])
if not fichiers:
    print('Aucun tome trouve.')
    sys.exit(1)

# Mots cles du passage manque signale par Laurent.
MOTS_CLES = ['Auteuil', 'Bertuccio', 'diner', 'invites', 'Danglars', 'Villefort',
             'Haydee', 'Morcerf', 'Morel']
MOTS_CLES = ['Auteuil', 'Bertuccio', 'Danglars', 'Villefort', 'Haydée', 'Morcerf']

# Titres de chapitres : lignes courtes qui commencent par un numero romain ou
# par le mot CHAPITRE.
RE_TITRE = re.compile(r'^\s{0,4}(CHAPITRE\s+[IVXLC0-9]+|(?=[IVXLC]+\.\s)[IVXLC]+\.)\s*[^\n]{3,70}$',
                      re.IGNORECASE | re.MULTILINE)

print('')
for f in fichiers:
    chapters = get_chapters(str(f))
    texte = '\n'.join((c.get('text') or '') for c in chapters)
    print('=' * 74)
    print('{}  ({} chapitres epub, {} phrases)'.format(
        f.name[:60], len(chapters), sum(len(vc._split_chapter_sentences(c['text'])) for c in chapters)))
    print('=' * 74)
    print('  occurrences :', ' | '.join(
        '{} {}'.format(m, len(re.findall(m, texte, re.IGNORECASE))) for m in MOTS_CLES))
    titres = RE_TITRE.findall(texte)
    titres = [t[0].strip() if isinstance(t, tuple) else t for t in titres]
    print('  titres de chapitres detectes : {}'.format(len(titres)))
    for t in titres[:40]:
        print('     {}'.format(t[:70]))
    print('')

print('Fin de la verification.')
