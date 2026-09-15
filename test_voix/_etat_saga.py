# -*- coding: utf-8 -*-
"""
Etat du partage entre tomes d'une saga (session du 14/09/2026).

Affiche, pour chaque livre : la fiche de personnages memorisee (cast_fiche),
et les noms de personnages proches d'un nom donne (pour reperer les renommages
d'un tome a l'autre, comme « Albert » contre « Albert de Morcerf »).

Usage : python test_voix/_etat_saga.py [debut_du_nom]
"""
import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
DEBUT = sys.argv[1] if len(sys.argv) > 1 else 'Albert'

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)

print('')
print('--- fiche de personnages memorisee (cast_fiche) ---')
for r in conn.execute("SELECT book_id, COUNT(*) AS n FROM cast_fiche GROUP BY book_id ORDER BY book_id"):
    livre = conn.execute("SELECT title, saga FROM books WHERE id = ?", (r[0],)).fetchone()
    print('  livre {:<3} : {:>3} personnages   {}   [saga={}]'.format(
        r[0], r[1], (livre[0] or '')[:34] if livre else '?', (livre[1] if livre else None)))

print('')
print('--- personnages dont le nom commence par "{}" ---'.format(DEBUT))
for r in conn.execute("""
    SELECT v.book_id, b.title, v.character_name, v.voice_id, v.line_count
    FROM voices v JOIN books b ON b.id = v.book_id
    WHERE v.character_name LIKE ?
    ORDER BY v.book_id, v.line_count DESC
""", (DEBUT + '%',)):
    print('  livre {:<3} {:<24} {:<26} {:>5} repliques'.format(
        r[0], r[2][:24], r[3][:26], r[4]))

conn.close()
print('')
print('Fin.')
