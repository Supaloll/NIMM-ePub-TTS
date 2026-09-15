# -*- coding: utf-8 -*-
"""
Diagnostic jetable (lecture seule) : livres PAS ENCORE castes, avec leur
taille -- pour choisir le meilleur candidat a un essai d'ecoute en local
(plus le livre est petit, plus l'essai est rapide).
"""
import sys
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters
from modules import voice_casting as vc

LIB = BASE / 'data' / 'library'
conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)

print('')
print('LIVRES PAS ENCORE CASTES')
print('%-5s %-44s %6s %9s' % ('id', 'titre', 'chap.', 'phrases'))
print('-' * 70)
for r in conn.execute("SELECT id, title, filename, cast_status FROM books WHERE user_id = 1 ORDER BY id"):
    if (r[3] or 'none') != 'none':
        continue
    chapters = get_chapters(str(LIB / r[2]))
    phrases = sum(len(vc._split_chapter_sentences(c['text'])) for c in chapters)
    print('%-5d %-44s %6d %9d' % (r[0], (r[1] or '')[:44], len(chapters), phrases))
conn.close()
print('')
print('Rappel : cout d\'un casting Gemini = environ 0,23 EUR pour 1 000 phrases ;')
print('         avec le moteur local, c\'est gratuit, mais environ 2 h par livre.')
