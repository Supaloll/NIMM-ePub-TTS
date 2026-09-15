# -*- coding: utf-8 -*-
"""
Diagnostic jetable (lecture seule) : ou en est le casting voix multiples ?
Affiche l'etat du livre, les chapitres deja payes, les personnages trouves.
Aucune ecriture en base : connexion ouverte en mode "ro" (read-only).
"""
import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
DB = BASE / 'data' / 'nimm_epub.db'

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 28


def ligne(titre):
    print('')
    print('=' * 62)
    print(titre)
    print('=' * 62)


conn = sqlite3.connect('file:{}?mode=ro'.format(DB.as_posix()), uri=True)
conn.row_factory = sqlite3.Row

ligne('1. TABLES PRESENTES')
for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(' -', r['name'])

ligne('2. COLONNES DES TABLES UTILES')
for table in ('books', 'speaker_attribution', 'voices', 'progress'):
    try:
        cols = [c['name'] for c in conn.execute('PRAGMA table_info({})'.format(table))]
        print('{:22s} : {}'.format(table, ', '.join(cols)))
    except sqlite3.Error as e:
        print('{:22s} : ERR {}'.format(table, e))

ligne('3. TOUS LES LIVRES (etat du casting)')
sql = """SELECT id, title, cast_status, multi_voice_enabled, saga
         FROM books WHERE user_id = 1 ORDER BY id"""
for r in conn.execute(sql):
    print(' id={:<4} status={:<22} mv={:<3} saga={:<14} {}'.format(
        r['id'], str(r['cast_status']), str(r['multi_voice_enabled']),
        str(r['saga']), str(r['title'])[:40]))

ligne('4. LIVRE {} : DETAIL'.format(BOOK_ID))
b = conn.execute("SELECT * FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
if not b:
    print('Livre {} introuvable.'.format(BOOK_ID))
else:
    for cle in b.keys():
        val = b[cle]
        if isinstance(val, str) and len(val) > 120:
            val = val[:120] + '...'
        print(' {:<20} : {}'.format(cle, val))

ligne('5. CHAPITRES DEJA ATTRIBUES (donc deja payes)')
sql = """SELECT chapter_index, COUNT(*) AS nb, COUNT(DISTINCT speaker) AS perso
         FROM speaker_attribution WHERE book_id = ?
         GROUP BY chapter_index ORDER BY chapter_index"""
rows = list(conn.execute(sql, (BOOK_ID,)))
if not rows:
    print(' Aucune attribution enregistree pour ce livre.')
else:
    for r in rows:
        print('   chapitre {:>3} : {:>4} phrases, {:>3} locuteurs distincts'.format(
            r['chapter_index'], r['nb'], r['perso']))
    print('')
    print(' >>> {} chapitre(s) enregistre(s), {} phrases au total'.format(
        len(rows), sum(r['nb'] for r in rows)))
    print(' >>> index des chapitres : {}'.format([r['chapter_index'] for r in rows]))

ligne('6. PERSONNAGES IDENTIFIES (livre {})'.format(BOOK_ID))
sql = """SELECT speaker AS nom, COUNT(*) AS nb FROM speaker_attribution
         WHERE book_id = ? GROUP BY speaker ORDER BY nb DESC"""
rows = list(conn.execute(sql, (BOOK_ID,)))
print(' {} locuteur(s) different(s) :'.format(len(rows)))
for r in rows[:15]:
    print('   {:>5} repliques  {}'.format(r['nb'], r['nom']))
if len(rows) > 15:
    print('   ... et {} autres'.format(len(rows) - 15))

ligne('7. VOIX ENREGISTREES (livre {})'.format(BOOK_ID))
rows = list(conn.execute(
    "SELECT character_name, voice_id, genre, line_count FROM voices WHERE book_id = ? ORDER BY line_count DESC",
    (BOOK_ID,)))
if not rows:
    print(' Aucune voix enregistree -> la Passe 2 ne s\'est jamais terminee.')
else:
    for r in rows:
        print('   {:>5} repliques  {:<24} {} ({})'.format(
            r['line_count'], r['character_name'], r['voice_id'], r['genre']))
    print(' >>> {} voix au total'.format(len(rows)))

conn.close()
print('')
print('Fin du diagnostic.')
