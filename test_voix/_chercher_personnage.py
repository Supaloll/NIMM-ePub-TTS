# -*- coding: utf-8 -*-
"""Cherche un PERSONNAGE dans tous les livres castes : fiche, voix, verrou.

Repond a la question « qui est ce personnage, qui le lit aujourd'hui ? » --
utile pour decider a la main d'une voix (personnage etranger, role precis...).

Usage :
    python test_voix/_chercher_personnage.py <morceau_de_nom>
Exemple :
    python test_voix/_chercher_personnage.py Cavalcanti
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

MOTIF = sys.argv[1] if len(sys.argv) > 1 else ''
if not MOTIF:
    print(__doc__)
    sys.exit(1)

base = 'file:%s?mode=ro' % (RACINE / 'data' / 'nimm_epub.db').as_posix()
conn = sqlite3.connect(base, uri=True)
conn.row_factory = sqlite3.Row

livres = {r['id']: r['title'] for r in conn.execute('SELECT id, title FROM books')}
fiches = {(r['book_id'], r['character_name']): r
          for r in conn.execute('SELECT book_id, character_name, genre, age '
                                'FROM cast_fiche')}

lignes = list(conn.execute(
    'SELECT book_id, character_name, voice_id, pitch, rate, genre, '
    'line_count, locked FROM voices WHERE character_name LIKE ? '
    'ORDER BY book_id, line_count DESC', ('%' + MOTIF + '%',)))
conn.close()

if not lignes:
    print('Aucun personnage ne contient « %s ».' % MOTIF)
    sys.exit(0)

print('Personnages contenant « %s » : %d' % (MOTIF, len(lignes)))
print('')
for r in lignes:
    fiche = fiches.get((r['book_id'], r['character_name']))
    age = fiche['age'] if fiche else '?'
    genre = r['genre'] or (fiche['genre'] if fiche else '?')
    print('  livre %s — %s' % (r['book_id'], livres.get(r['book_id'], '?')))
    print('     %-30s %s | %s | %s repliques%s'
          % (r['character_name'], genre or '?', age or '?', r['line_count'],
             ' | VERROUILLE' if r['locked'] else ''))
    print('     voix : %-34s hauteur %s | vitesse %s'
          % (r['voice_id'] or '(aucune — lu par le narrateur)',
             r['pitch'], r['rate']))
