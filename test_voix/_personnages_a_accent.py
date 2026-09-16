# -*- coding: utf-8 -*-
"""Quels PERSONNAGES portent une voix a ACCENT et risquent de la perdre ?

Un re-cast redistribue les voix de tous les personnages NON verrouilles : un
personnage qui a herite d'une voix etrangere (italienne, espagnole, anglaise...)
peut donc la perdre -- or ces voix sont precieuses et rares.

Cet outil liste, pour chaque livre, les personnages dont la voix porte un accent
note a l'ecoute (ou est reservee a un role), avec l'etat du verrou. Il sert a
savoir QUOI verrouiller AVANT de relancer un re-cast.

Lecture seule. Usage :
    python test_voix/_personnages_a_accent.py [saga]
"""

import json
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

SAGA = sys.argv[1] if len(sys.argv) > 1 else ''

ACCENTS_NEUTRES = ('', 'neutre')
DOSSARD = RACINE / 'data' / 'annotations_voix.json'

annotations = json.loads(DOSSARD.read_text(encoding='utf-8'))
accentuees = {ident for ident, note in annotations.items()
              if (note.get('accent') or '') not in ACCENTS_NEUTRES}
reservees = {ident for ident, note in annotations.items()
             if note.get('role')}

base = 'file:%s?mode=ro' % (RACINE / 'data' / 'nimm_epub.db').as_posix()
conn = sqlite3.connect(base, uri=True)
conn.row_factory = sqlite3.Row

requete = ('SELECT v.book_id, b.title, b.saga, v.character_name, v.voice_id, '
           'v.line_count, v.locked FROM voices v JOIN books b ON b.id = v.book_id')
parametres = ()
if SAGA:
    requete += ' WHERE b.saga LIKE ?'
    parametres = ('%' + SAGA + '%',)
requete += ' ORDER BY v.book_id, v.line_count DESC'

lignes = [r for r in conn.execute(requete, parametres)
          if r['voice_id'] in accentuees or r['voice_id'] in reservees]
conn.close()

if not lignes:
    print('Aucun personnage a voix accentuee%s.'
          % (' dans la saga « %s »' % SAGA if SAGA else ''))
    sys.exit(0)

print('PERSONNAGES A VOIX ACCENTUEE%s — a verrouiller avant un re-cast'
      % (' (saga %s)' % SAGA if SAGA else ''))
print('=' * 78)
livre_courant = None
for r in lignes:
    if r['book_id'] != livre_courant:
        livre_courant = r['book_id']
        print('')
        print('livre %s — %s%s' % (r['book_id'], r['title'],
                                   ' [%s]' % r['saga'] if r['saga'] else ''))
    note = annotations.get(r['voice_id'], {})
    genre = note.get('genre', '?')
    etat = 'VERROUILLE' if r['locked'] else '** a verrouiller **'
    print('   %-26s %-3s %-22s accent=%-18s %s'
          % (r['character_name'][:26], genre, r['voice_id'][:22],
             note.get('accent') or ('role=' + (note.get('role') or '')), etat))

print('')
print('%d personnage(s) concerne(s).' % len(lignes))
print('Un personnage verrouille garde sa voix a chaque re-cast (case « garder »')
print('dans la fenetre du casting).')
