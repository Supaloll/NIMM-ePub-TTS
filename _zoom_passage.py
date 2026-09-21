# -*- coding: utf-8 -*-
"""Zoom sur UN passage : les morceaux enregistres, et qui les lit.

Demande de Laurent (21/09/2026) : un passage ou il entend « quelque chose qui
cloche » (un beat de narration lu par un personnage, et la seconde moitie d'un
cri renvoyee au narrateur). Ce script montre, morceau par morceau, ce que la
base a enregistre -- sans rien modifier.

Usage :
    python _zoom_passage.py 36 "Au commandement du frere"
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
MOTIF = sys.argv[2] if len(sys.argv) > 2 else 'Jésus'

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
print(' %s -- mode %s' % (titre, 'DIALOGUE' if drapeau else 'origine'))
print('=' * 78)

for ch, chapitre in enumerate(epub_parser.get_chapters(
        str(RACINE / 'data' / 'library' / fichier))):
    morceaux = decoupage.phrases(chapitre.get('text') or '', regle)
    cible = [i for i, m in enumerate(morceaux) if MOTIF.lower() in m.lower()]
    if not cible:
        continue
    debut = max(0, cible[0] - 1)
    for idx in range(debut, min(len(morceaux), cible[-1] + 4)):
        phrase = morceaux[idx]
        # Ce morceau est-il un BEAT de narration (il finit par ':' et introduit
        # une replique) ? C'est le cas que Laurent a repere.
        beat = (decoupage.introduit_une_replique(phrase)
                and idx + 1 < len(morceaux)
                and morceaux[idx + 1].lstrip().startswith('«'))
        print('')
        print('  ch.%d #%-4d locuteur = %-22s %s'
              % (ch, idx, locuteurs.get((ch, idx)),
                 'BEAT DE NARRATION' if beat else ''))
        print('     %s' % phrase[:150])
    break
