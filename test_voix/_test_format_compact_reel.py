# -*- coding: utf-8 -*-
"""
Test REEL du format compact (session du 13/09/2026).
UN SEUL appel a Gemini : quelques centimes, pas plus.

Ce que le test mesure :
  1. la TAILLE de la reponse demandee, avant (ancien format) et apres ;
  2. les tokens REELLEMENT factures par Google (entree, sortie, reflexion) ;
  3. la QUALITE : chaque phrase du lot est comparee a ce que Gemini avait
     repondu pour le meme passage lors du casting du livre 28 (deja en base,
     donc aucune depense supplementaire pour la reference).

Critere de qualite principal, independant des noms : la phrase est-elle vue
comme une REPLIQUE ou comme de la NARRATION ? (C'est ce qui decide de la voix.)

Lancer depuis la racine : python test_voix/_test_format_compact_reel.py
"""
import sys
import json
import asyncio
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

BOOK_ID = 28
CHAPITRE = 16        # chapitre 17 du livre
LOT = 0              # premier paquet de 150 phrases
TAILLE_ANCIEN_FORMAT = 79.8   # caracteres par phrase, mesure le 13/09/2026

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
# Fiche telle qu'elle etait au lancement : les personnages des 16 chapitres
# deja analyses avant la reprise, genre devine par le prenom.
noms = [r[0] for r in conn.execute(
    "SELECT DISTINCT speaker FROM speaker_attribution WHERE book_id = ? "
    "AND chapter_index <= 15 AND speaker != 'narration'", (BOOK_ID,))]
verite = {(r[0], r[1]): r[2] for r in conn.execute(
    "SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution "
    "WHERE book_id = ? AND chapter_index = ?", (BOOK_ID, CHAPITRE))}
conn.close()

fiche = [{'nom': n, 'genre': vc.deviner_genre(n), 'age': 'adulte'} for n in noms]
chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
sentences = vc._split_chapter_sentences(chapters[CHAPITRE]['text'])
batch = sentences[LOT * vc.BATCH_SIZE:(LOT + 1) * vc.BATCH_SIZE]

print('')
print('=' * 70)
print('TEST REEL DU FORMAT COMPACT -- {}'.format(book[1]))
print('=' * 70)
print('Chapitre {} ("{}"), phrases {} a {}'.format(
    CHAPITRE + 1, chapters[CHAPITRE]['title'], batch[0]['id'], batch[-1]['id']))
print('Fiche envoyee : {} personnages'.format(len(fiche)))
print('')
print('Envoi a Gemini en cours (1 appel)...')

avant = vc.tokens_session()
resultat = asyncio.run(vc._analyser_lot(fiche, batch, 'gemini', set()))
apres = vc.tokens_session()

# --- Taille de la reponse demandee ---
sortie_tokens = apres['sortie'] - avant['sortie']
taille_ancienne = int(len(batch) * TAILLE_ANCIEN_FORMAT)
tokens_anciens_estimes = int(len(batch) * 22)   # TOKENS_OUT_PER_SENTENCE

print('')
print('--- TAILLE DE LA REPONSE DEMANDEE ---')
print('  ancien format : {:>8} caracteres (~{} tokens de sortie estimes)'.format(
    taille_ancienne, tokens_anciens_estimes))
print('  nouveau format: {} tokens de sortie REELLEMENT produits pour ce lot'.format(sortie_tokens))
print('  soit {} phrases listees ; les autres sont de la narration implicite'.format(
    sum(1 for p in resultat['phrases'] if p['locuteur'] != 'narration')))

# --- Tokens reellement factures ---
print('')
print('--- TOKENS REELLEMENT FACTURES PAR GOOGLE ---')
print('  appels          : {}'.format(apres['appels'] - avant['appels']))
print('  tokens entree   : {}'.format(apres['entree'] - avant['entree']))
print('  tokens sortie   : {}'.format(apres['sortie'] - avant['sortie']))
print('  tokens REFLEXION: {}'.format(apres['reflexion'] - avant['reflexion']))
cout = round(apres['cout_usd_estime'] - avant['cout_usd_estime'], 5)
print('  cout estime     : {} $ pour ce lot'.format(cout))
if len(batch):
    print('  soit ~{:.5f} $ par phrase, ~{:.2f} $ pour un livre de 25 000 phrases'.format(
        cout / len(batch), cout / len(batch) * 25000))

# --- Qualite : comparaison avec la reference deja en base ---
print('')
print('--- QUALITE (comparaison avec le casting de reference) ---')
accords = 0
desaccords = []
for p in resultat['phrases']:
    ref = verite.get((CHAPITRE, p['id']))
    if ref is None:
        continue
    nouveau_replique = p['locuteur'] != 'narration'
    ref_replique = ref != 'narration'
    if nouveau_replique == ref_replique:
        accords += 1
    else:
        desaccords.append((p['id'], p['locuteur'], ref))

total = accords + len(desaccords)
print('  phrases comparees      : {}'.format(total))
print('  meme diagnostic        : {} ({:.1f} %)'.format(
    accords, 100.0 * accords / max(total, 1)))
print('  desaccords narration/replique : {}'.format(len(desaccords)))
for sid, nouveau, ref in desaccords[:12]:
    print('     phrase {:>3} : nouveau = {:<20} reference = {}'.format(sid, str(nouveau), ref))

# --- Coherence des citations fragmentees ---
print('')
print('--- COHERENCE DES CITATIONS (filet automatique) ---')
vc._harmonize_open_quotes(batch, resultat['phrases'])
harmonisees = sum(1 for p in resultat['phrases'] if p['anomalie'] and 'harmonis' in p['anomalie'])
print('  fragments de citation re-harmonises : {}'.format(harmonisees))
print('  => plus ce nombre est faible, mieux le modele a compris la consigne (règle 9)')

print('')
print('Fin du test.')
