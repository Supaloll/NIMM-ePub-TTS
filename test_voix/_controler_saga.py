# -*- coding: utf-8 -*-
"""Contrôle la COHERENCE DES VOIX entre les tomes d'une saga (lecture seule).

POURQUOI (question de Laurent, 17/09/2026) : « si je caste les deux derniers
tomes de Monte-Cristo, vais-je retrouver les memes voix, meme si le moteur a
change entre-temps ? »

Reponse que ce script verifie : la coherence de saga reprend la voix stockee
dans **le tome le plus ancien** (`_fetch_saga_voix_figees`, dans main.py), et
elle ne regarde **jamais le moteur** -- seulement l'identifiant de la voix. Donc
un moteur qui change (XTTS -> Kyutai) ne casse rien, TANT QUE les identifiants
suivent (c'est ce qu'a fait la bascule du 17/09/2026).

Il signale les personnages presents dans PLUSIEURS tomes d'une meme saga qui
n'ont PAS la meme voix : ce sont eux qui feront tache a l'ecoute.

Usage :
    python test_voix/_controler_saga.py                 # toutes les sagas
    python test_voix/_controler_saga.py "Monte-Cristo"  # une saga
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'


def main():
    filtre = sys.argv[1] if len(sys.argv) > 1 else None

    connection = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    sagas = [ligne[0] for ligne in connection.execute(
        "SELECT saga FROM books WHERE saga IS NOT NULL AND saga != '' "
        "GROUP BY saga HAVING COUNT(1) > 1 ORDER BY saga")]
    if filtre:
        sagas = [s for s in sagas if filtre.lower() in s.lower()]

    print('')
    print('=' * 78)
    print('COHERENCE DES VOIX ENTRE LES TOMES D UNE SAGA')
    print('=' * 78)
    if not sagas:
        print('  aucune saga de plusieurs tomes%s.'
              % (' correspondant a %r' % filtre if filtre else ''))
        return 0

    total_souci = 0
    for saga in sagas:
        livres = list(connection.execute(
            "SELECT id, title, date_added FROM books WHERE saga = ? "
            "ORDER BY date_added ASC, id ASC", (saga,)))
        print('')
        print('  SAGA « %s »  (%d tomes)' % (saga, len(livres)))
        for ident, titre, ajoute in livres:
            print('     livre %-4s %-46s ajoute le %s'
                  % (ident, (titre or '(sans titre)')[:46], (ajoute or '')[:10]))

        # {personnage: {book_id: voix}}
        par_personnage = {}
        for ident, _titre, _ajoute in livres:
            for personnage, voix in connection.execute(
                    "SELECT character_name, voice_id FROM voices WHERE book_id = ?",
                    (ident,)):
                par_personnage.setdefault(personnage, {})[ident] = voix or ''

        divergents = {p: v for p, v in par_personnage.items()
                      if len(set(v.values())) > 1}
        print('')
        if not divergents:
            print('     OK : chaque personnage garde la meme voix d un tome a '
                  'l autre (%d personnages communs).' % len(par_personnage))
        else:
            total_souci += len(divergents)
            print('     A REGARDER : %d personnage(s) changent de voix selon le '
                  'tome :' % len(divergents))
            for personnage, par_tome in sorted(divergents.items())[:25]:
                detail = ', '.join('%s=%s' % (b, (v or '(aucune)')[:26])
                                   for b, v in sorted(par_tome.items()))
                print('        %-26s %s' % (personnage[:26], detail))
            if len(divergents) > 25:
                print('        ... et %d autre(s)' % (len(divergents) - 25))

    connection.close()
    print('')
    if total_souci:
        print('RESULTAT : %d personnage(s) a voix divergente entre tomes.' % total_souci)
        print('(la coherence est reprise du tome le PLUS ANCIEN a chaque')
        print(' casting ou re-cast : re-caster le tome fautif suffit a le fixer)')
        return 1
    print('TOUT EST OK : aucune divergence de voix entre les tomes.')
    return 0


if __name__ == '__main__':
    sys.exit(main())