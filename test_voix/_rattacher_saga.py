# -*- coding: utf-8 -*-
"""
Petit utilitaire : rattacher un ou plusieurs livres a une saga.

Usage :
    python test_voix/_rattacher_saga.py 16,17 "Monte Cristo"

Utile avant un casting : un livre rattache a une saga HERITE des voix des
autres tomes de la meme saga (le tome le plus anciennement ajoute fait
reference), pour qu'un personnage ne change pas de voix d'un tome a l'autre.
"""
import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent

if len(sys.argv) < 3:
    print('Usage : python test_voix/_rattacher_saga.py 16,17 "Monte Cristo"')
    sys.exit(1)

book_ids = [int(x) for x in sys.argv[1].split(',')]
saga = sys.argv[2]

conn = sqlite3.connect(str(BASE / 'data' / 'nimm_epub.db'))
for bid in book_ids:
    conn.execute("UPDATE books SET saga = ? WHERE id = ?", (saga, bid))
conn.commit()

print('Saga mise a jour :')
for bid in book_ids:
    r = conn.execute("SELECT id, title, saga FROM books WHERE id = ?", (bid,)).fetchone()
    print('  id {:<3} {:<42} saga={}'.format(r[0], (r[1] or '')[:42], r[2]))
conn.close()
