# -*- coding: utf-8 -*-
"""Qui doit passer en MODE DIALOGUE, en une page (lecture seule).

POURQUOI CET OUTIL (23/09/2026). La migration des index (`_migrer_index_dialogue.py`)
se fait LIVRE PAR LIVRE, et avant de la lancer il faut savoir exactement :
  - quels livres sont DEJA en mode dialogue (interdits : leurs index sont deja
    ceux du decoupage fin, les remapper les decalerait) ;
  - quels livres sont CASTES (des attributions en base) et donc MIGRABLES ;
  - quels livres ne sont pas castes : rien a migrer, ils seront castes en mode
    dialogue directement (activation automatique au nouveau casting).

Il ne modifie RIEN et n'appelle aucune API (base ouverte en lecture seule).

Usage : python test_voix/_etat_migration_dialogue.py
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
LARGEUR = 78


def main():
    conn = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row

    attributions = {r['book_id']: (r['phrases'], r['chapitres']) for r in conn.execute(
        'SELECT book_id, COUNT(*) AS phrases, COUNT(DISTINCT chapter_index) '
        'AS chapitres FROM speaker_attribution GROUP BY book_id')}
    personnages = {r['book_id']: r['n'] for r in conn.execute(
        'SELECT book_id, COUNT(*) AS n FROM voices GROUP BY book_id')}
    livres = list(conn.execute(
        'SELECT id, title, COALESCE(decoupe_dialogue, 0) AS dialogue '
        'FROM books ORDER BY id'))
    conn.close()

    journal = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro',
                              uri=True).execute('PRAGMA journal_mode').fetchone()
    print('=' * LARGEUR)
    print(' MIGRATION EN MODE DIALOGUE : qui est concerne (lecture seule)')
    print('=' * LARGEUR)
    print('  base : data/nimm_epub.db -- %d livres -- journal : %s'
          % (len(livres), (journal or ['?'])[0]))

    a_migrer, deja, pas_castes = [], [], []
    for livre in livres:
        identifiant = livre['id']
        phrases, chapitres = attributions.get(identifiant, (0, 0))
        ligne = (identifiant, (livre['title'] or '?')[:42], phrases, chapitres,
                 personnages.get(identifiant, 0))
        if livre['dialogue']:
            deja.append(ligne)
        elif phrases:
            a_migrer.append(ligne)
        else:
            pas_castes.append(ligne)

    def _table(titre, note, lignes):
        print('')
        print('-' * LARGEUR)
        print(' %s -- %s' % (titre, note))
        print('-' * LARGEUR)
        if not lignes:
            print('  (aucun)')
            return
        print('  %-4s %-44s %8s %6s %6s' % ('#', 'Livre', 'phrases',
                                           'chap.', 'pers.'))
        for identifiant, titre_l, phrases, chapitres, pers in lignes:
            print('  %-4d %-44s %8d %6d %6d'
                  % (identifiant, titre_l, phrases, chapitres, pers))

    _table('A MIGRER (castes, decoupage d origine)',
           '%d livres' % len(a_migrer), a_migrer)
    _table('DEJA EN MODE DIALOGUE (INTERDITS : index deja fins)',
           '%d livres' % len(deja), deja)
    _table('PAS CASTES (rien a migrer)',
           '%d livres' % len(pas_castes), pas_castes)

    print('')
    print('=' * LARGEUR)
    print('  Pour mesurer un livre (rien n est ecrit) :')
    print('    python test_voix/_migrer_index_dialogue.py --livre <id> '
          '--variante B')
    print('  Pour ecrire (copie datee de la base AVANT, controle APRES) :')
    print('    python test_voix/_migrer_index_dialogue.py --livre <id> '
          '--variante B --ecrire')
    print('=' * LARGEUR)
    return 0


if __name__ == '__main__':
    sys.exit(main())
