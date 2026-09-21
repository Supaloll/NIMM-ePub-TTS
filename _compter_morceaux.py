# -*- coding: utf-8 -*-
"""Compte les morceaux d'un livre avec la regle ACTUELLE du code.

Sert a verifier que le SERVEUR utilise bien le decoupage a jour : on compare ce
que le code local compte avec ce que la base contient (une ligne d'attribution
par morceau).

Usage : python _compter_morceaux.py 36
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
lignes = con.execute('SELECT COUNT(*) FROM speaker_attribution WHERE book_id = ?',
                     (LIVRE,)).fetchone()[0]
con.close()

chapitres = epub_parser.get_chapters(str(RACINE / 'data' / 'library' / fichier))
texte = [c.get('text') or '' for c in chapitres]

def compte(regle):
    total = 0
    beats_typo = 0
    for t in texte:
        for phrase in decoupage.phrases(t, regle):
            total += 1
            # Beat reconnu SEULEMENT grace a la normalisation des apostrophes ?
            if ('\u2019' in phrase and decoupage.introduit_une_replique(phrase)):
                beats_typo += 1
    return total, beats_typo

t_orig, _ = compte(decoupage.REGLE_ACTUELLE)
t_dial, beats_typo = compte(decoupage.REGLE_DIALOGUE)
print('=' * 70)
print(' %s (livre %s, mode %s)' % (titre, LIVRE, 'DIALOGUE' if drapeau else 'origine'))
print('=' * 70)
print('   regle d origine        : %d morceaux' % t_orig)
print('   regle dialogue (code   : %d morceaux   <- ce que le SERVEUR devrait' % t_dial)
print('   a jour)                  avoir utilise')
print('   base (lignes attribuees): %d morceaux' % lignes)
print('   morceaux concernes par l apostrophe typographique : %d' % beats_typo)
print('')
print('   VERDICT : %s' % ('le serveur a bien le code a jour'
                          if lignes == t_dial
                          else 'ECART -> le serveur a peut-etre encore l ancien code'))
