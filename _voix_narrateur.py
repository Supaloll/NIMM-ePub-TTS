# -*- coding: utf-8 -*-
"""Verifie l'identite narrateur / personnage principal (recit a la 1re personne).

Ouvre la question notee au BACKLOG : « dans un recit a la 1re personne, la voix
du narrateur devrait etre celle du personnage principal ». Lecture SEULE.

Usage : python _voix_narrateur.py [book_id]
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8')
BASE = RACINE / 'data' / 'nimm_epub.db'

BID = int(sys.argv[1]) if len(sys.argv) > 1 else 28
conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
conn.row_factory = sqlite3.Row

livre = conn.execute('SELECT title, narrator_voice FROM books WHERE id = ?',
                     (BID,)).fetchone()
print('Livre %d : %s' % (BID, livre['title']))
print('  voix du NARRATEUR (books.narrator_voice) : %s'
      % (livre['narrator_voice'] or '(defaut du lecteur)'))
print('')
print('  Principaux personnages (voix) :')
for r in conn.execute('SELECT character_name, voice_id, line_count FROM voices '
                      'WHERE book_id = ? ORDER BY line_count DESC LIMIT 6', (BID,)):
    marque = ''
    if livre['narrator_voice'] and r['voice_id'] == livre['narrator_voice']:
        marque = '   <-- MEME VOIX QUE LE NARRATEUR'
    print('    %-30s %-34s %6s%s'
          % (r['character_name'], r['voice_id'], r['line_count'], marque))
conn.close()
