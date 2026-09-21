# -*- coding: utf-8 -*-
"""MODE DIALOGUE d'un livre : la narration separee des repliques (21/09/2026).

Demande de Laurent : dans un morceau qui colle une narration et une replique
(« Avant que j'aie pu repondre, Richie est intervenu : «Non, c'est pas ca. » »),
le beat doit revenir au NARRATEUR et la replique au PERSONNAGE.

Cette regle de decoupage est plus fine que celle d'origine : elle ne s'applique
donc QU'AUX LIVRES MARQUES, un par un (colonne `books.decoupe_dialogue`). Les
livres non marques gardent le decoupage d'origine, caractere pour caractere --
indispensable, car les numeros de phrases sont ENREGISTRES en base
(`speaker_attribution`) : changer le decoupage d'un livre deja caste decalerait
ses voix.

SECURITE : rien n'est ecrit sans `--activer` ou `--desactiver`, et une copie
datee de la base est faite AVANT d'ecrire.

Usage :
    python test_voix/regler_mode_dialogue.py                       (liste seule)
    python test_voix/regler_mode_dialogue.py --livre 40 --activer
    python test_voix/regler_mode_dialogue.py --livre 40 --desactiver
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'


def _colonne_absente(conn) -> bool:
    """La colonne `decoupe_dialogue` manque-t-elle encore en base ?"""
    return 'decoupe_dialogue' not in [r[1] for r in
                                      conn.execute('PRAGMA table_info(books)')]


def _liste(conn, colonne: bool) -> None:
    print('%-4s %-44s %s' % ('#', 'Livre', 'mode de decoupage'))
    select = ('SELECT id, title, COALESCE(decoupe_dialogue, 0) AS m FROM books '
              'ORDER BY id') if colonne else \
             'SELECT id, title, 0 AS m FROM books ORDER BY id'
    for r in conn.execute(select):
        print('%-4d %-44s %s' % (r[0], (r[1] or '?')[:44],
                                 'DIALOGUE (narration separee)'
                                 if r[2] else 'origine'))
    if not colonne:
        print('')
        print('   (la colonne n existe pas encore : elle sera ajoutee par le'
              ' serveur au prochain demarrage, ou par --activer/--desactiver)')


def main():
    livre = None
    for i, arg in enumerate(sys.argv):
        if arg == '--livre' and i + 1 < len(sys.argv):
            livre = int(sys.argv[i + 1])
    activer = '--activer' in sys.argv
    desactiver = '--desactiver' in sys.argv

    conn = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
    colonne = not _colonne_absente(conn)
    print('=' * 74)
    print(' MODE DIALOGUE : quels livres separent la narration des repliques ?')
    print('=' * 74)
    _liste(conn, colonne)
    conn.close()

    if not (activer or desactiver):
        print('')
        print('Aucune ecriture : ajoutez --activer ou --desactiver'
              ' (avec --livre <numero>).')
        return 0
    if livre is None:
        print('')
        print('Precisez le livre : --livre <numero>.')
        return 2

    # --- Copie datee AVANT d'ecrire -----------------------------------------
    copie = BASE.with_name(BASE.name + '.bak_avant_mode_dialogue_'
                           + datetime.now().strftime('%Y%m%d_%H%M'))
    src = sqlite3.connect(str(BASE))
    dst = sqlite3.connect(str(copie))
    with dst:
        src.backup(dst)
    dst.close()
    src.close()
    print('')
    print('Copie de la base faite AVANT d ecrire : ' + copie.name)

    conn = sqlite3.connect(str(BASE))
    conn.execute('PRAGMA busy_timeout = 20000')
    if _colonne_absente(conn):
        conn.execute('ALTER TABLE books ADD COLUMN decoupe_dialogue '
                     'INTEGER DEFAULT 0')
        print('Colonne decoupe_dialogue ajoutee (non destructif).')
    conn.execute('UPDATE books SET decoupe_dialogue = ? WHERE id = ?',
                 (1 if activer else 0, livre))
    conn.commit()
    ligne = conn.execute('SELECT title FROM books WHERE id = ?',
                         (livre,)).fetchone()
    conn.close()
    print('')
    print('Livre %s (%s) regle en mode %s.'
          % (livre, (ligne[0] if ligne else '?')[:40],
             'DIALOGUE' if activer else 'ORIGINE'))
    print('Retour arriere : remplacer data/%s par %s' % (BASE.name, copie.name))
    print('')
    print('A SAVOIR : pour un livre DEJA caste, le decoupage change -> les'
          ' numeros de phrases enregistres ne correspondent plus. Il faut'
          ' RE-CASTER le livre (ou migrer ses index) pour que les voix'
          ' suivent le nouveau decoupage.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
