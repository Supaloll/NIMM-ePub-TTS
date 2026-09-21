# -*- coding: utf-8 -*-
"""MESURE « la narration est-elle lue par un personnage ? » -- tout livre.

Principe : un morceau attribue a un PERSONNAGE qui ne porte **aucun signe de
dialogue** (ni guillemet, ni tiret de dialogue, ni verbe de parole) est
suspect : c'est souvent de la narration (ou une incise) lue par une voix de
personnage. C'est le meme signal que le « controle de vraisemblance » du
projet (`voice_casting._a_un_signe_de_dialogue`), ici en LECTURE SEULE : on
compte, on montre les textes, et on juge a la lecture.

ATTENTION : ce compteur sur-signale (un morceau peut etre la SUITE d'une
replique, apres un point d'exclamation). Il sert a trouver ou regarder, pas a
decider. Toujours LIRE les morceaux montres.

Usage : python _mesurer_sans_signe.py 37 [nb_exemples]
"""
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage, voice_casting

LIVRE = int(sys.argv[1]) if len(sys.argv) > 1 else 37
MAXI = int(sys.argv[2]) if len(sys.argv) > 2 else 12
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
suspects = []
total = 0
for ch, chapitre in enumerate(epub_parser.get_chapters(
        str(RACINE / 'data' / 'library' / fichier))):
    for idx, morceau in enumerate(decoupage.phrases(chapitre.get('text') or '',
                                                    regle)):
        total += 1
        etiquette = locuteurs.get((ch, idx))
        if etiquette in (None, 'narration'):
            continue
        if not voice_casting._a_un_signe_de_dialogue(morceau):
            suspects.append((ch, idx, etiquette, morceau))

print('=' * 78)
print(' %s (livre %s, mode %s) -- %d morceaux'
      % (titre, LIVRE, 'DIALOGUE' if drapeau else 'origine', total))
print('=' * 78)
print('   %d morceau(x) attribue(s) a un PERSONNAGE sans signe de dialogue'
      % len(suspects))
print('   (a LIRE avant de conclure : une suite de replique est legitime)')
print('')
for ch, idx, etiquette, morceau in suspects[:MAXI]:
    print('   ch.%d #%-4d %-24s %s' % (ch, idx, etiquette[:24], morceau[:84]))
