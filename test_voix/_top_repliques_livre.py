# -*- coding: utf-8 -*-
"""Classement des personnages d'un livre par nombre de repliques (lecture seule).

Sert a decider QUELS roles meritent une voix maison (ou une voix dediee) :
les premiers du classement portent la quasi-totalite du texte parle.

Usage : python test_voix/_top_repliques_livre.py <book_id> [nombre]
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

DB = Path(__file__).resolve().parent.parent / 'data' / 'nimm_epub.db'
BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 35
TOP = int(sys.argv[2]) if len(sys.argv) > 2 else 25

conn = sqlite3.connect('file:{}?mode=ro'.format(DB.as_posix()), uri=True)
conn.row_factory = sqlite3.Row

livre = conn.execute('SELECT title, saga FROM books WHERE id = ?',
                     (BOOK_ID,)).fetchone()
print('Livre %d : %s  (saga : %s)'
      % (BOOK_ID, (livre or {'title': '?'})['title'],
         (livre or {'saga': '-'})['saga']))

lignes = list(conn.execute(
    'SELECT character_name, voice_id, genre, line_count, pitch, rate, locked '
    'FROM voices WHERE book_id = ? ORDER BY line_count DESC', (BOOK_ID,)))

total = sum((r['line_count'] or 0) for r in lignes)
print('Personnages : %d | repliques attribuees : %d' % (len(lignes), total))
print('')

print('%-4s %-30s %6s %5s %-30s %s' % ('#', 'personnage', 'repl.', '%', 'voix', 'H/F'))
print('-' * 100)
cumul = 0
for i, r in enumerate(lignes[:TOP], 1):
    n = r['line_count'] or 0
    cumul += n
    print('%-4s %-30s %6s %4s%% %-30s %s'
          % (i, (r['character_name'] or '')[:30], n,
             round(100 * n / total) if total else 0,
             (r['voice_id'] or '')[:30], r['genre'] or '?'))

print('-' * 100)
print('Les %d premiers portent %.0f%% des repliques.'
      % (min(TOP, len(lignes)), 100 * cumul / total if total else 0))

seuils = [10, 25, 50, 100, 200]
print('')
print('Paliers : ' + ' | '.join(
    '>= %s repl. : %s perso' % (s, sum(1 for r in lignes if (r['line_count'] or 0) >= s))
    for s in seuils))
conn.close()
