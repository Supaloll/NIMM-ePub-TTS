# -*- coding: utf-8 -*-
"""
Diagnostic jetable #2 : combien de chapitres a le livre, combien ont ete
payes, combien il reste, et a quoi ressemble l'appel de la Passe 2.
Lecture seule (base ouverte en "ro"), aucun appel IA.
"""
import sys
import json
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

DB = BASE / 'data' / 'nimm_epub.db'
LIB = BASE / 'data' / 'library'
BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 28

conn = sqlite3.connect('file:{}?mode=ro'.format(DB.as_posix()), uri=True)
conn.row_factory = sqlite3.Row

book = conn.execute("SELECT * FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
epub_path = str(LIB / book['filename'])

print('Livre {} : {}'.format(BOOK_ID, book['title']))
print('Fichier  : {}'.format(book['filename']))
print('')

chapters = get_chapters(epub_path)
print('CHAPITRES DU LIVRE (fichier epub) : {}'.format(len(chapters)))

faits = {r['chapter_index']: r['nb'] for r in conn.execute(
    "SELECT chapter_index, COUNT(*) AS nb FROM speaker_attribution "
    "WHERE book_id = ? GROUP BY chapter_index", (BOOK_ID,))}

print('')
print('{:>4}  {:<34} {:>8} {:>10}'.format('ch', 'titre', 'phrases', 'en base'))
for c in chapters:
    sents = vc._split_chapter_sentences(c['text'])
    nb = faits.get(c['index'])
    marque = 'PAYE' if nb else '----'
    print('{:>4}  {:<34} {:>8} {:>10}  {}'.format(
        c['index'], (c['title'] or '')[:34], len(sents), nb if nb else '', marque))

print('')
total = len(chapters)
faits_nb = len(faits)
print('>>> chapitres total : {}'.format(total))
print('>>> chapitres payes : {}'.format(faits_nb))
print('>>> chapitres non traites : {}'.format(total - faits_nb))
print('>>> cast_status en base : {}'.format(book['cast_status']))

# --- Estimation du cout (sans appel IA) ---
texts = [c.get('text') or '' for c in chapters]
est = vc.estimate_cast_cost(texts, 'gemini')
print('')
print('ESTIMATION DU COUT (methode de l\'app, provider gemini)')
print('   phrases du livre    : {}'.format(est['sentences']))
print('   appels prevus       : {}'.format(est['calls']))
print('   tokens entree       : {:,}'.format(est['tokens_in']).replace(',', ' '))
print('   tokens sortie       : {:,}'.format(est['tokens_out']).replace(',', ' '))
print('   cout brut           : {} $'.format(est['cost_usd']))
print('   cout affiche (x1.5) : {}'.format(est['cost_display']))

est_faits = vc.estimate_cast_cost(
    [c.get('text') or '' for c in chapters if c['index'] in faits], 'gemini')
print('')
print('COUT DEJA ENGAGE ({} chapitres traites) : {} (brut {} $)'.format(
    faits_nb, est_faits['cost_display'], est_faits['cost_usd']))

# Ce que l'app annonce desormais dans la fenetre de choix du moteur :
# uniquement ce qui reste a payer (les chapitres deja faits ne sont pas
# refactures par la reprise).
est_restants = vc.estimate_cast_cost(
    [c.get('text') or '' for c in chapters if c['index'] not in faits], 'gemini')
print('')
print('ESTIMATION RESTANTE (ce que l\'app affiche desormais) : {} ({} appels, {} chapitres)'.format(
    est_restants['cost_display'], est_restants['calls'], est_restants['chapters']))

# --- Reconstitution de l'appel de Passe 2 ---
noms = [r['speaker'] for r in conn.execute(
    "SELECT DISTINCT speaker FROM speaker_attribution WHERE book_id = ? "
    "AND speaker != 'narration'", (BOOK_ID,))]
fiche = [{'nom': n, 'genre': 'H', 'age': 'adulte'} for n in noms]
prompt2 = vc._build_passe2_prompt(fiche)
print('')
print('APPEL DE PASSE 2 (consolidation des personnages)')
print('   personnages a consolider : {}'.format(len(fiche)))
print('   taille du prompt envoye  : {:,} caracteres'.format(len(prompt2)).replace(',', ' '))
print('   reponse attendue (fusion de CHAQUE nom + liste finale)')
print('   -> estimation ~{:,} caracteres de sortie'.format(len(noms) * 60).replace(',', ' '))

conn.close()
print('')
print('Fin du diagnostic 2.')
