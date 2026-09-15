# -*- coding: utf-8 -*-
"""
Diagnostic jetable (lecture seule, aucun appel IA) : RETROUVER le lot de
phrases qui a ete refuse par Google, a partir de la taille du prompt affichee
dans la fenetre de NIMM ePub.

Chaque lot produit un prompt de taille tres precise : cette taille sert
d'empreinte. On recalcule donc tous les prompts des chapitres restants et on
cherche celui qui correspond a la taille observee.

Lancer depuis la racine :
    python test_voix/_diag_lot_refuse.py 23321
"""
import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

TAILLE_CIBLE = int(sys.argv[1]) if len(sys.argv) > 1 else 23321
TOLERANCE = 60
BOOK_ID = 28
# Le refus a eu lieu pendant la relance du 13/09/2026, alors que les chapitres
# 1 a 16 etaient deja analyses : la fiche de l'epoque etait donc celle des
# personnages vus dans ces 16 premiers chapitres.
CHAPITRES_CONNUS = 15

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
noms = [r[0] for r in conn.execute(
    "SELECT DISTINCT speaker FROM speaker_attribution "
    "WHERE book_id = ? AND chapter_index <= ? AND speaker != 'narration'",
    (BOOK_ID, CHAPITRES_CONNUS))]
conn.close()

fiche = [{'nom': n, 'genre': vc.deviner_genre(n), 'age': 'adulte'} for n in noms]

print('')
print('Livre : {}'.format(book[1]))
print('Fiche reconstruite au moment du refus : {} personnages'.format(len(fiche)))
print('Taille de prompt recherchee : {} caracteres (tolerance +/- {})'.format(TAILLE_CIBLE, TOLERANCE))
print('')
print('{:>4}  {:<6} {:>12} {:>8}  {}'.format('ch', 'lot', 'caracteres', 'ecart', 'phrases'))
print('-' * 62)

trouves = []
chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
for ch in chapters:
    if ch['index'] <= CHAPITRES_CONNUS:
        continue
    sentences = vc._split_chapter_sentences(ch['text'])
    for num, i in enumerate(range(0, len(sentences), vc.BATCH_SIZE), start=1):
        lot = sentences[i:i + vc.BATCH_SIZE]
        taille = len(vc._build_prompt(fiche, lot))
        ecart = abs(taille - TAILLE_CIBLE)
        if ecart <= TOLERANCE:
            trouves.append((ch['index'], num, taille, ecart, lot))
            print('{:>4}  {:<6} {:>12} {:>8}  id {} a {}'.format(
                ch['index'], 'n°' + str(num), taille, ('+' if taille > TAILLE_CIBLE else '-') + str(ecart),
                lot[0]['id'], lot[-1]['id']))

if not trouves:
    print('  Aucun lot ne correspond exactement : la fiche a evolue entre-temps.')
else:
    print('')
    print('MOTS SURVEILLES DANS LE(S) LOT(S) TROUVE(S)')
    for ch_index, num, taille, ecart, lot in trouves:
        mots = []
        for s in lot:
            texte = s['texte'].lower()
            for mot in ('sadie', 'agress', 'coup', 'poing', 'etrangl', 'menac',
                        'sang', 'tuer', 'arme', 'salope', 'viol', 'bat', 'frapp'):
                if mot in texte:
                    mots.append('p{}:{}'.format(s['id'], mot))
        print('  chapitre {} lot {} : {}'.format(ch_index + 1, num, ', '.join(mots) if mots else 'aucun'))

print('')
print('Fin du diagnostic lot refuse.')
