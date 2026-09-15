# -*- coding: utf-8 -*-
"""
Efface les donnees de casting d'un livre, pour pouvoir le refaire (session du
14/09/2026).

ATTENTION -- OPERATION DESTRUCTIVE sur ce livre uniquement :
  - speaker_attribution (qui parle, phrase par phrase)
  - voices (les voix attribuees)
  - cast_fiche (la fiche de personnages memorisee)
  - cast_status remis a 'none'
Le fichier EPUB, la progression de lecture et le texte NE SONT PAS touches.

Indispensable avant un « re-cast » : sans cela, le mecanisme de reprise saute
tous les chapitres (il les croit deja faits) et le nouveau casting ne fait
rien.

Usage : python test_voix/_effacer_casting.py 16
"""
import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent

if len(sys.argv) < 2:
    print('Usage : python test_voix/_effacer_casting.py <book_id>')
    sys.exit(1)

book_id = int(sys.argv[1])

conn = sqlite3.connect(str(BASE / 'data' / 'nimm_epub.db'))
book = conn.execute("SELECT title FROM books WHERE id = ?", (book_id,)).fetchone()
if not book:
    print('Livre {} introuvable.'.format(book_id))
    sys.exit(1)

avant = {
    'phrases': conn.execute("SELECT COUNT(*) FROM speaker_attribution WHERE book_id = ?", (book_id,)).fetchone()[0],
    'voix': conn.execute("SELECT COUNT(*) FROM voices WHERE book_id = ?", (book_id,)).fetchone()[0],
    'fiche': conn.execute("SELECT COUNT(*) FROM cast_fiche WHERE book_id = ?", (book_id,)).fetchone()[0],
}

conn.execute("DELETE FROM speaker_attribution WHERE book_id = ?", (book_id,))
conn.execute("DELETE FROM voices WHERE book_id = ?", (book_id,))
conn.execute("DELETE FROM cast_fiche WHERE book_id = ?", (book_id,))
conn.execute("UPDATE books SET cast_status = 'none' WHERE id = ?", (book_id,))
conn.commit()

print('Livre {} : {}'.format(book_id, book[0]))
print('  avant  : {} phrases attribuees | {} voix | {} personnages en fiche'.format(
    avant['phrases'], avant['voix'], avant['fiche']))
print('  apres  : tout est efface, cast_status = none')
print('  (l\'epub et la progression de lecture ne sont pas touches)')
conn.close()
