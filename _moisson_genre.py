# -*- coding: utf-8 -*-
"""Enquete jetable n2 -- le GENRE des petits roles du livre 28 (22/11/63).

Lecture SEULE. Question : pourquoi une voix d'homme sur une fillette ?

Compare, pour chaque petit role (< 8 repliques, voix generique Piper) :
  - le genre enregistre en base (celui qui choisit Jessica ou Pierre) ;
  - le genre que l'app devine par le NOM (voice_casting.deviner_genre) ;
  - le genre que la fiche de casting a retenu (cast_fiche).

Usage : python _moisson_genre.py [book_id]
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.voice_casting import (deviner_genre, MINOR_THRESHOLD,        # noqa: E402
                                   GENERIC_VOICE_F, GENERIC_VOICE_M)

BASE = RACINE / 'data' / 'nimm_epub.db'
BID = int(sys.argv[1]) if len(sys.argv) > 1 else 28

conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
conn.row_factory = sqlite3.Row

fiche = {r['character_name']: (r['genre'], r['age']) for r in conn.execute(
    'SELECT character_name, genre, age FROM cast_fiche WHERE book_id = ?', (BID,))}
voix = list(conn.execute('SELECT character_name, voice_id, genre, line_count '
                         'FROM voices WHERE book_id = ? ORDER BY line_count DESC',
                         (BID,)))

print('Seuil petit role : %d repliques | voix generiques : F=%s  M=%s'
      % (MINOR_THRESHOLD, GENERIC_VOICE_F, GENERIC_VOICE_M))
print('')

petits = [r for r in voix if (r['voice_id'] or '') in
          (GENERIC_VOICE_F, GENERIC_VOICE_M)]
print('Petits roles a voix generique : %d sur %d personnages'
      % (len(petits), len(voix)))
print('  dont voix FEMME : %d | voix HOMME : %d'
      % (sum(1 for r in petits if r['voice_id'] == GENERIC_VOICE_F),
         sum(1 for r in petits if r['voice_id'] == GENERIC_VOICE_M)))
print('')

# 1. Le cas signale : la fillette deguisee (Annette Founijello)
print('=' * 96)
print('1. LE CAS SIGNALE (Annette Founijello / « Fillette deguisee »)')
print('=' * 96)
for r in voix:
    if 'fillette' in (r['character_name'] or '').lower():
        g_fiche = fiche.get(r['character_name'], ('?',))[0]
        print('  %-30s voix=%-14s genre_base=%s genre_fiche=%s devine_par_nom=%s repl.=%s'
              % (r['character_name'], r['voice_id'], r['genre'], g_fiche,
                 deviner_genre(r['character_name']), r['line_count']))
print('  filles/soeurs/tantes reconnues par deviner_genre :')
for nom in ['Fillette deguisee', 'Fillette corde a sauter', 'fille', 'la jeune fille',
            'Fille de la veuve', 'une fillette', 'petite fille', 'gamine',
            'Mimi Corcoran', 'Marie_standardiste']:
    print('    %-26s -> %s' % (nom, deviner_genre(nom)))

# 2. Tous les petits roles F/H en base
print('')
print('=' * 96)
print('2. LES PETITS ROLES, PAR GENRE ENREGISTRE')
print('=' * 96)
print('  %-34s %-14s %-6s %-6s %s'
      % ('personnage', 'voix', 'base', 'nom', 'repl.'))
for r in petits:
    g_fiche = fiche.get(r['character_name'], ('?',))[0]
    print('  %-34s %-14s %-6s %-6s %s'
          % ((r['character_name'] or '')[:34], r['voice_id'], r['genre'],
             deviner_genre(r['character_name']), r['line_count']))

# 3. Doutes : un nom qui se lit comme feminin mais une voix d'homme (ou l'inverse)
print('')
print('=' * 96)
print('3. DOUTES A CORRIGER (nom et voix ne s accordent pas)')
print('=' * 96)
doutes = 0
for r in petits:
    devine = deviner_genre(r['character_name'])
    if devine != (r['genre'] or 'H'):
        doutes += 1
        print('  %-34s voix=%-14s base=%s  mais le nom se lit %s  (repl.=%s)'
              % ((r['character_name'] or '')[:34], r['voice_id'], r['genre'],
                 devine, r['line_count']))
print('  -> %d doute(s) detecte(s) par le nom sur %d petits roles.' % (doutes, len(petits)))
print('')
print('  A SAVOIR : ce controle ne voit que ce que le NOM dit. Un nom neutre')
print('  (« La Chose », « Public », « Deke Simmons ») reste invisible ici :')
print('  seule la lecture des repliques (ou la fiche IA) peut trancher.')

conn.close()
print('')
print('--- fin ---')
