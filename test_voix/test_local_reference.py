# -*- coding: utf-8 -*-
"""
Mesure de REFERENCE du moteur local (session du 14/09/2026).
GRATUIT : tout se passe sur le poste.

Ce test fait tourner le VRAI code de production (analyze_chapter avec
provider="local") sur un chapitre deja caste, et affiche la duree, le rappel,
la precision et l'accord avec Gemini.

Il sert de reference : un essai d'optimisation du 14/09/2026 (fiche compacte
+ contexte 8 192) avait fait tomber l'accord de 67 % a 36 % ; ce test a permis
de verifier le retour a la normale. Toute modification du prompt ou des
reglages locaux doit etre validee par ce test AVANT d'etre gardee.

Lancer depuis la racine :
    python test_voix/test_local_reference.py
    python test_voix/test_local_reference.py 4
"""
import sys
import time
import asyncio
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc
from modules.config import get_local_model

CHAPITRE = int(sys.argv[1]) if len(sys.argv) > 1 else 4
BOOK_ID = 28

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
fiche = [{'nom': r[0], 'genre': r[1], 'age': r[2]} for r in conn.execute(
    "SELECT character_name, genre, age FROM cast_fiche WHERE book_id = ?", (BOOK_ID,))]
verite = {(r[0], r[1]): r[2] for r in conn.execute(
    "SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution "
    "WHERE book_id = ? AND chapter_index = ?", (BOOK_ID, CHAPITRE))}
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
sentences = vc._split_chapter_sentences(chapters[CHAPITRE]['text'])
ref_repliques = {s['id'] for s in sentences
                 if verite.get((CHAPITRE, s['id']), 'narration') != 'narration'}

avant = vc.tokens_session('local')

print('')
print('=' * 70)
print('MOTEUR LOCAL -- mesure de reference ({})'.format(get_local_model()))
print('=' * 70)
print('Livre    : {}'.format(book[1]))
print('Chapitre : {} ("{}"), {} phrases'.format(
    CHAPITRE + 1, chapters[CHAPITRE]['title'], len(sentences)))
print('Fiche    : {} personnages, format compact'.format(len(fiche)))
print('Paquets  : {} phrases (local) | contexte 8192'.format(vc.BATCH_SIZE_LOCAL))
print('')
print('Analyse en cours (le vrai code de production)...')

t0 = time.time()
resultat = asyncio.run(vc.analyze_chapter(chapters[CHAPITRE]['text'], fiche, 'local'))
duree = time.time() - t0
apres = vc.tokens_session('local')

trouve = {p['id'] for p in resultat['phrases'] if p['locuteur'] != 'narration'}
rappel = 100.0 * len(trouve & ref_repliques) / max(len(ref_repliques), 1)
precision = 100.0 * len(trouve & ref_repliques) / max(len(trouve), 1)
accord = sum(1 for s in sentences if (s['id'] in trouve) == (s['id'] in ref_repliques))

print('')
print('=' * 70)
print('RESULTAT DE L\'OPTIMISATION')
print('=' * 70)
print('Duree                 : {:.0f} s ({:.1f} min)'.format(duree, duree / 60.0))
print('Repliques trouvees    : {} sur {} -> rappel {:.0f} %'.format(
    len(trouve & ref_repliques), len(ref_repliques), rappel))
print('Precision             : {:.0f} %'.format(precision))
print('Accord avec Gemini    : {:.0f} %'.format(100.0 * accord / max(len(sentences), 1)))
print('Mots factures (gratuit) : entree {} | sortie {}'.format(
    apres['entree'] - avant['entree'], apres['sortie'] - avant['sortie']))
print('')
print('Pour comparaison, hier soir sur le chapitre 5 (qwen3:8b, fiche JSON,')
print('paquets de 150, contexte 10 240) : 148 s, rappel 82 %, precision 52 %,')
print('accord 67 %, avec un debordement de la carte (8 % sur le processeur).')
print('')
print('Fin du test.')
