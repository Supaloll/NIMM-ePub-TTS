# -*- coding: utf-8 -*-
"""PROFIL D'INCISES d'un livre (mesure seule) -- de quoi decider a l'avance.

Repond a la question de Laurent (22/09/2026) : « pour savoir a l'avance sur un
livre inconnu, c'est impossible ». C'est vrai a l'oreille -- mais le TEXTE, lui,
se compte : combien d'incises, et combien sont au « je » (recit du narrateur) ?
Un livre ou la plupart des incises sont au « je » est un recit a la premiere
personne (Stephen King) ; un livre ou elles nomment des tiers est un roman
classique (Monte-Cristo).

Usage : python _moisson_profil_incises.py [book_id ...]
"""

import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                       # noqa: E402
from modules import incises as inc                              # noqa: E402
from modules.decoupage import (phrases as _phrases,             # noqa: E402
                               REGLE_DIALOGUE)
import _moisson_incise_proto as proto                           # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
LIVRES = [int(a) for a in sys.argv[1:]] or [28, 16]

# Le « je » d'une incise : sujet du verbe de parole (« ai-je dit », « dis-je »,
# « m'a-t-il repondu » = NON, c'est un tiers), ou pronom objet du recit.
MOTIF_JE = re.compile(r"(?:^|[\s\u00ab\u201c\"\u2013\u2014])j[\u2019']"
                      r"|\bje\b|[\u2019'-]je\b", re.IGNORECASE)


def _compte(spans, phrase):
    """(total, dont « je ») pour une liste de spans d'incises."""
    total = 0
    je = 0
    for debut, fin in spans:
        total += 1
        if MOTIF_JE.search(phrase[debut:fin]):
            je += 1
    return total, je


conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
conn.row_factory = sqlite3.Row

print('PROFIL D INCISES DES LIVRES')
print('')
print('%-44s %8s %10s %10s' % ('livre', 'phrases', 'aujourd hui', 'a ajouter'))
print('-' * 76)
for BID in LIVRES:
    livre = conn.execute('SELECT title, filename FROM books WHERE id = ?',
                         (BID,)).fetchone()
    chemin = BIBLIOTHEQUE / (livre['filename'] or '')
    if not chemin.is_file():
        print('livre %d : fichier absent' % BID)
        continue
    total = auj_tot = auj_je = cand_tot = cand_je = 0
    for chap in get_chapters(str(chemin)):
        for texte in _phrases(chap.get('text') or '', REGLE_DIALOGUE):
            total += 1
            spans_auj = inc.incises(texte)
            t, j = _compte(spans_auj, texte)
            auj_tot += t
            auj_je += j
            candidats = [s for s in proto.spans_candidats(texte)
                         if not any(s[0] >= a and s[1] <= b
                                    for a, b in spans_auj)]
            t, j = _compte(candidats, texte)
            cand_tot += t
            cand_je += j
    print('%-44s %8d %10s %10s'
          % ((livre['title'] or '')[:44], total,
             '%d (dont %d je)' % (auj_tot, auj_je),
             '%d (dont %d je)' % (cand_tot, cand_je)))
    # Le verdict que la page pourrait AFFICHER pour aider Laurent a choisir.
    if cand_tot + auj_tot:
        part = 100.0 * (cand_je + auj_je) / (cand_tot + auj_tot)
        avis = ('profil « recit a la 1re personne » : les incises se lisent'
                if part >= 30 else
                'profil « roman classique » : les incises sont des etiquettes')
        print('   -> %d incises au total, %.0f %% au « je » : %s'
              % (auj_tot + cand_tot, part, avis))
    print('')

conn.close()
print('--- fin (rien n a ete modifie) ---')
