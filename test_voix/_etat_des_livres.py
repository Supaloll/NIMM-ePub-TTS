# -*- coding: utf-8 -*-
"""TABLEAU DE BORD DES LIVRES : ou en est chacun, en une page (lecture seule).

POURQUOI CET OUTIL (23/09/2026, demande de Laurent : « je ne sais pas trop ou on
en est »). Une journee a touche la base trois fois (migration, rattrapage,
restauration a venir) : il faut un endroit qui dise, POUR CHAQUE LIVRE :
  - le mode de decoupage (origine ou dialogue) ;
  - la part de NARRATION et le nombre de gros locuteurs — c'est ce qui décide du
    futur reglage « roman / entretien » (R5) ;
  - les INCISES de parole : muettes ou lues par le narrateur ;
  - s'il a des morceaux hors casting (points de casting a revoir).

Usage : python test_voix/_etat_des_livres.py
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
LARGEUR = 96


def main():
    conn = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    print('=' * LARGEUR)
    print(' TABLEAU DE BORD DES LIVRES -- lecture seule')
    print('=' * LARGEUR)
    print('%-4s %-30s %7s %8s %9s %6s %5s %7s'
          % ('#', 'Livre', 'phrases', 'decoupe', 'narration', 'perso.', 'gros',
             'incises'))
    print('-' * LARGEUR)
    total_phrases = 0
    for livre in conn.execute(
            'SELECT id, title, COALESCE(decoupe_dialogue, 0) AS dialogue, '
            'COALESCE(incises_narrateur, 0) AS incises, '
            'COALESCE(narrator_voice, "") AS narrateur, '
            'COALESCE(multi_voice_enabled, 0) AS voix '
            'FROM books ORDER BY id'):
        lignes = list(conn.execute(
            'SELECT speaker, COUNT(*) AS n FROM speaker_attribution '
            'WHERE book_id = ? GROUP BY speaker ORDER BY n DESC',
            (livre['id'],)))
        total = sum(r['n'] for r in lignes)
        total_phrases += total
        if not total:
            print('%-4d %-30s %7s %8s %9s %6s %5s %7s'
                  % (livre['id'], (livre['title'] or '?')[:30], '-',
                     'origine', '-', '-', '-', '-'))
            continue
        narration = next((100.0 * r['n'] / total for r in lignes
                          if r['speaker'] == 'narration'), 0.0)
        personnages = len([r for r in lignes if r['speaker'] != 'narration'])
        gros = len([r for r in lignes if r['speaker'] != 'narration'
                    and 100.0 * r['n'] / total > 15])
        hors = len({r['speaker'] for r in lignes if r['speaker'] != 'narration'}
                   - {v['character_name'] for v in conn.execute(
                       'SELECT character_name FROM voices WHERE book_id = ?',
                       (livre['id'],))})
        print('%-4d %-30s %7d %8s %8.1f%% %6d %5d %7s'
              % (livre['id'], (livre['title'] or '?')[:30], total,
                 'DIALOGUE' if livre['dialogue'] else 'origine', narration,
                 personnages, gros,
                 'lues' if livre['incises'] else 'muettes'))
        if hors:
            print('       ^ %d locuteur(s) hors casting : a revoir au casting'
                  % hors)
    conn.close()
    print('-' * LARGEUR)
    print('  %d phrases attribuees au total.' % total_phrases)
    print('')
    print('  A LIRE : « gros » = nombre de personnages qui prennent plus de')
    print('  15 % des phrases. C est le critere du futur reglage par livre :')
    print('  « entretien » = narration < 20 % ET deux gros locuteurs ou plus.')
    print('=' * LARGEUR)
    return 0


if __name__ == '__main__':
    sys.exit(main())
