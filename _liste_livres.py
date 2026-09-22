# -*- coding: utf-8 -*-
"""Liste les livres de la bibliotheque dont le fichier est present (lecture seule)."""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8')
BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
conn.row_factory = sqlite3.Row
for r in conn.execute('SELECT id, title, filename, cast_status FROM books ORDER BY id'):
    chemin = BIBLIOTHEQUE / (r['filename'] or '')
    taille = chemin.stat().st_size if chemin.is_file() else 0
    print('%3d  %-46s  %-10s  %8.1f Mo'
          % (r['id'], (r['title'] or '')[:46], r['cast_status'] or '-',
             taille / 1048576.0))
conn.close()
