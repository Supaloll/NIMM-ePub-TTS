# -*- coding: utf-8 -*-
"""CHOISIR UN CHAPITRE ou le dialogue domine (pour un essai a l'oreille).

Demande de Laurent (21/09/2026) : plutot qu'un livre entier penible a lire,
prendre UN chapitre d'un livre qu'il connait, riche en dialogues, et y mener
tous les essais.

Ce que le script mesure, chapitre par chapitre :
    - les morceaux de phrase (regle actuelle) ;
    - les signes de dialogue (« et tirets de dialogue) ;
    - les morceaux qui MELANGENT narration et replique (les « beats » : la
      narration qui est aujourd'hui lue par un personnage) ;
    - le debut du chapitre, pour que Laurent le reconnaisse.

LECTURE SEULE. Usage : python _choisir_chapitre.py 28
"""
import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage

LIVRE = int(sys.argv[1]) if len(sys.argv) > 1 else 28
BASE = RACINE / 'data' / 'nimm_epub.db'

con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
fichier, titre, drapeau = con.execute(
    'SELECT filename, title, COALESCE(decoupe_dialogue, 0) FROM books '
    'WHERE id = ?', (LIVRE,)).fetchone()
con.close()

RE_TIRET = re.compile(r'^\s*[\u2014\u2013-]\s', re.M)
RE_BEAT = re.compile(r':\s*$')

lignes = []
for ch, chapitre in enumerate(epub_parser.get_chapters(
        str(RACINE / 'data' / 'library' / fichier))):
    texte = chapitre.get('text') or ''
    if len(texte) < 2000:
        continue
    morceaux = decoupage.phrases(texte)
    # Beats : morceaux ou la coupe « dialogue » s'appliquerait.
    beats = [m for m in morceaux
             if decoupage._couper_avant_replique((0, len(m), m))[1:]]
    lignes.append({
        'index': ch,
        'titre': chapitre.get('title') or '',
        'morceaux': len(morceaux),
        'guillemets': texte.count('«'),
        'tirets': len(RE_TIRET.findall(texte)),
        'beats': len(beats),
        'debut': ' '.join(texte.split())[:110],
    })

lignes.sort(key=lambda l: -l['beats'])
print('=' * 90)
print(' %s (livre %s) -- chapitres classes par nombre de beats (narration + replique)'
      % (titre, LIVRE))
print('=' * 90)
print('%-5s %-28s %8s %6s %6s %6s' % ('chap.', 'titre', 'morceaux', '«', 'tirets', 'beats'))
for l in lignes[:8]:
    print('%-5d %-28s %8d %6d %6d %6d'
          % (l['index'], (l['titre'] or '?')[:28], l['morceaux'],
             l['guillemets'], l['tirets'], l['beats']))
print('')
print('   Debut des 3 meilleurs (pour les reconnaitre) :')
for l in lignes[:3]:
    print('')
    print('   ch.%d (%s) -- %d beats' % (l['index'], (l['titre'] or '?')[:40],
                                         l['beats']))
    print('      %s…' % l['debut'])
