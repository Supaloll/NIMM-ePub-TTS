# -*- coding: utf-8 -*-
"""Etat d'un casting, en chiffres (lecture seule, outil d'atelier).

Repond en un coup d'oeil aux questions qu'on se pose avant un re-cast :
    - combien de personnages, combien VERROUILLES (ils garderont leur voix) ;
    - combien de PETITS ROLES (< seuil de repliques) : aujourd'hui ils portent
      la voix generique Piper (siwis/tom), partagee par genre ;
    - quelles voix du catalogue sont deja prises, et lesquelles ne le sont pas.

Usage : python test_voix/_etat_casting_livre.py <book_id>
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

from modules.voice_casting import (MINOR_THRESHOLD, GENERIC_VOICE_F,
                                   GENERIC_VOICE_M)

DB = Path(__file__).resolve().parent.parent / 'data' / 'nimm_epub.db'
BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 33

conn = sqlite3.connect('file:{}?mode=ro'.format(DB.as_posix()), uri=True)
conn.row_factory = sqlite3.Row

livre = conn.execute('SELECT title FROM books WHERE id = ?', (BOOK_ID,)).fetchone()
lignes = list(conn.execute(
    'SELECT character_name, voice_id, pitch, genre, line_count, locked '
    'FROM voices WHERE book_id = ? ORDER BY line_count DESC', (BOOK_ID,)))

print('Livre %d : %s' % (BOOK_ID, (livre or {'title': '?'})['title']))
print('=' * 72)
print('Personnages au casting : %d' % len(lignes))
verrouilles = [r for r in lignes if r['locked']]
petits = [r for r in lignes if (r['line_count'] or 0) < MINOR_THRESHOLD]
generiques = [r for r in lignes
              if (r['voice_id'] or '') in (GENERIC_VOICE_F, GENERIC_VOICE_M)]
dediees = [r for r in lignes if r not in generiques]
print('  verrouilles (voix conservee au re-cast) : %d' % len(verrouilles))
print('  petits roles (< %d repliques) : %d (dont %d voix generique Piper)'
      % (MINOR_THRESHOLD, len(petits), len(generiques)))
print('  voix dediees (Piper inclus s il y en a) : %d' % len(dediees))
print('')
print('Petits roles par genre : %d femmes / %d hommes'
      % (sum(1 for r in petits if r['genre'] == 'F'),
         sum(1 for r in petits if r['genre'] != 'F')))
if verrouilles:
    print('')
    print('Verrouilles :')
    for r in verrouilles:
        print('   %-30s %-28s %5s repliques'
              % ((r['character_name'] or '')[:30], (r['voice_id'] or '')[:28],
                 r['line_count']))

print('')
print('Voix deja prises (hors generique) :')
prises = sorted({r['voice_id'] for r in dediees if r['voice_id']})
for voix in prises:
    noms = [r['character_name'] for r in dediees if r['voice_id'] == voix]
    print('   %-30s %s' % (voix[:30], ', '.join(noms)[:60]))
