# -*- coding: utf-8 -*-
"""MESURE des deux defauts d'attribution reperes par Laurent (21/09/2026).

Défaut 1 : un BEAT de narration (« Frère Mariano, …, s'écria : ») attribue a un
           PERSONNAGE au lieu du narrateur. C'est du ressort du decoupage ET de
           l'etiquetage : la coupe est bonne, c'est l'etiquette qui est fausse.
Défaut 2 : la SECONDE moitie d'un cri coupe par la ponctuation (« Jésus ! »
           apres « « Jésus ! ») renvoyee au narrateur, alors que la citation est
           encore ouverte.

LECTURE SEULE. Usage : python _mesurer_fragments_36.py 36
"""
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage

LIVRE = int(sys.argv[1]) if len(sys.argv) > 1 else 36
BASE = RACINE / 'data' / 'nimm_epub.db'

con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
fichier, titre, drapeau = con.execute(
    'SELECT filename, title, COALESCE(decoupe_dialogue, 0) FROM books '
    'WHERE id = ?', (LIVRE,)).fetchone()
locuteurs = {(ch, idx): sp for ch, idx, sp in con.execute(
    'SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution '
    'WHERE book_id = ?', (LIVRE,))}
con.close()
regle = decoupage.REGLE_DIALOGUE if drapeau else decoupage.REGLE_ACTUELLE

print('=' * 78)
print(' %s (livre %s) -- mode %s' % (titre, LIVRE, 'DIALOGUE' if drapeau else 'ORIGINE'))
print('=' * 78)

defaut1 = []      # (chapitre, index, morceau, locuteur)
defaut2 = []      # (chapitre, index crie, index fragment, locuteur du cri)
total_pieces = 0

for ch, chapitre in enumerate(epub_parser.get_chapters(
        str(RACINE / 'data' / 'library' / fichier))):
    morceaux = decoupage.phrases(chapitre.get('text') or '', regle)
    total_pieces += len(morceaux)
    for idx, phrase in enumerate(morceaux):
        etiquette = locuteurs.get((ch, idx))
        # --- Defaut 1 : un beat attribue a un personnage --------------------
        if (etiquette not in (None, 'narration')
                and decoupage.introduit_une_replique(phrase)):
            defaut1.append((ch, idx, phrase, etiquette))
        # --- Defaut 2 : une citation ouverte, dont la suite est au narrateur -
        if (phrase.lstrip().startswith('«')
                and etiquette not in (None, 'narration')
                and idx + 1 < len(morceaux)
                and locuteurs.get((ch, idx + 1)) in (None, 'narration')
                and not morceaux[idx + 1].lstrip().startswith('«')
                and len(morceaux[idx + 1]) <= 90):
            defaut2.append((ch, idx, idx + 1, etiquette))

print('')
print('  %d morceaux dans le livre' % total_pieces)
print('')
print('  DEFAUT 1 -- %d beat(s) de narration attribues a un PERSONNAGE :'
      % len(defaut1))
for ch, idx, phrase, etiquette in defaut1[:10]:
    print('     ch.%d #%-4d %-22s %s' % (ch, idx, etiquette, phrase[:70]))
print('')
print('  DEFAUT 2 -- %d cri(s) dont la SUITE reste au narrateur :'
      % len(defaut2))
for ch, idx, suite, etiquette in defaut2[:10]:
    print('     ch.%d #%-4d (replique = %s) -> fragment au narrateur'
          % (ch, idx, etiquette))
