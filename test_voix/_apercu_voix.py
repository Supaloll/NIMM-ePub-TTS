# -*- coding: utf-8 -*-
"""
Apercu du casting d'un livre (session du 14/09/2026) : personnages, voix,
nombre de repliques, et repartition narration / dialogues.

Usage :
    python test_voix/_apercu_voix.py 33
    python test_voix/_apercu_voix.py 33 25
"""
import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent

if len(sys.argv) < 2:
    print('Usage : python test_voix/_apercu_voix.py <book_id> [nombre]')
    sys.exit(1)

book_id = int(sys.argv[1])
limite = int(sys.argv[2]) if len(sys.argv) > 2 else 15

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT title, cast_status FROM books WHERE id = ?", (book_id,)).fetchone()
if not book:
    print('Livre {} introuvable.'.format(book_id))
    sys.exit(1)

voix = conn.execute("""
    SELECT character_name, voice_id, genre, line_count
    FROM voices WHERE book_id = ? ORDER BY line_count DESC
""", (book_id,)).fetchall()
total_phrases = conn.execute(
    "SELECT COUNT(*) FROM speaker_attribution WHERE book_id = ?", (book_id,)).fetchone()[0]
narration = conn.execute(
    "SELECT COUNT(*) FROM speaker_attribution WHERE book_id = ? AND speaker = 'narration'",
    (book_id,)).fetchone()[0]

print('')
print('Livre {} : {}  [{}]'.format(book_id, book[0], book[1]))
print('  {} personnages avec une voix'.format(len(voix)))
print('  {} phrases attribuees : {} narration ({:.0f} %) | {} repliques ({:.0f} %)'.format(
    total_phrases, narration, 100.0 * narration / max(total_phrases, 1),
    total_phrases - narration, 100.0 * (total_phrases - narration) / max(total_phrases, 1)))
print('')
print('  {:<30} {:<32} {:>3} {:>8}'.format('personnage', 'voix', 'G', 'repliques'))
print('  ' + '-' * 76)
for r in voix[:limite]:
    print('  {:<30} {:<32} {:>3} {:>8}'.format(
        r[0][:30], r[1][:32], r[2], r[3]))
if len(voix) > limite:
    print('  ... et {} autres'.format(len(voix) - limite))
conn.close()
print('')
print('Fin de l\'apercu.')
