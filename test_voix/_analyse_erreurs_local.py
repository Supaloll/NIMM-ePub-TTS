# -*- coding: utf-8 -*-
"""
Analyse FINE des erreurs du moteur local (session du 14/09/2026, gratuit).

Repond a une question precise : le modele local RATE-t-il des dialogues, ou
en INVENTE-t-il ? Les deux se ressemblent dans un pourcentage global, mais
n'appellent pas du tout les memes remedes.

Classification de chaque phrase, en comparant le local au casting Gemini
de reference :
  - ok narration        : les deux disent narration
  - ok attribution      : les deux disent dialogue, avec le meme nom
  - mauvais nom         : les deux disent dialogue, mais pas le meme nom
  - FAUX POSITIF        : le local invente un dialogue (Gemini dit narration)
  - REPLIQUE RATEE      : le local oublie un dialogue (Gemini dit dialogue)

Pour les faux positifs, on regarde en plus si la phrase porte un marqueur
objectif de dialogue (guillemets, tiret cadratin, verbe de parole) : cela dit
si un filtrage de sortie par marqueurs les eliminerait.

Lancer depuis la racine : python test_voix/_analyse_erreurs_local.py
                          python test_voix/_analyse_erreurs_local.py 4
"""
import sys
import re
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

MARQUES = re.compile(r'[«»"]|\u2014|(^|\s)[-–]\s')
VERBES = re.compile(
    r"\b(dit|dis|répond|repond|demand|s'écri|s'ecri|murmur|ajout|reprit|"
    r"soupir|grommel|poursuiv|observ|reprenn|répét|repet|cria|appela|"
    r"expliqu|avou|annonc|annonç|protest|conclut)", re.IGNORECASE)


def a_un_marqueur(texte):
    """La phrase porte-t-elle un signe objectif de dialogue ? (independant de
    toute IA : guillemets, tiret de dialogue, verbe de parole)"""
    return bool(MARQUES.search(texte) or VERBES.search(texte))


conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
fiche = [{'nom': r[0], 'genre': r[1], 'age': r[2]} for r in conn.execute(
    "SELECT character_name, genre, age FROM cast_fiche WHERE book_id = ?", (BOOK_ID,))]
ref = {r[1]: r[2] for r in conn.execute(
    "SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution "
    "WHERE book_id = ? AND chapter_index = ?", (BOOK_ID, CHAPITRE))}
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
sentences = vc._split_chapter_sentences(chapters[CHAPITRE]['text'])
print('')
print('ANALYSE FINE DES ERREURS -- {}'.format(get_local_model()))
print('Chapitre {} ("{}"), {} phrases'.format(
    CHAPITRE + 1, chapters[CHAPITRE]['title'], len(sentences)))
print('Analyse en cours (gratuit, ~1 a 2 min)...')

t0 = time.time()
resultat = asyncio.run(vc.analyze_chapter(chapters[CHAPITRE]['text'], fiche, 'local'))
loc = {p['id']: p['locuteur'] for p in resultat['phrases']}

cats = {'ok_narration': 0, 'ok_attribution': 0, 'mauvais_nom': 0,
        'faux_positif': 0, 'replique_ratee': 0}
fp_avec_marqueur = 0
rr_avec_marqueur = 0
exemples_fp, exemples_rr, exemples_nom = [], [], []

for s in sentences:
    a = loc.get(s['id'], 'narration')
    b = ref.get(s['id'], 'narration')
    if a == 'narration' and b == 'narration':
        cats['ok_narration'] += 1
    elif a != 'narration' and b == 'narration':
        cats['faux_positif'] += 1
        if a_un_marqueur(s['texte']):
            fp_avec_marqueur += 1
        if len(exemples_fp) < 8:
            exemples_fp.append((s['id'], a))
    elif a == 'narration' and b != 'narration':
        cats['replique_ratee'] += 1
        if a_un_marqueur(s['texte']):
            rr_avec_marqueur += 1
        if len(exemples_rr) < 8:
            exemples_rr.append((s['id'], b))
    elif a == b:
        cats['ok_attribution'] += 1
    else:
        cats['mauvais_nom'] += 1
        if len(exemples_nom) < 8:
            exemples_nom.append((s['id'], a, b))

total = sum(cats.values())
repliques_ref = cats['ok_attribution'] + cats['mauvais_nom'] + cats['replique_ratee']
repliques_loc = cats['ok_attribution'] + cats['mauvais_nom'] + cats['faux_positif']

print('')
print('=' * 72)
print('OU SE TROMPE LE MODELE LOCAL ?')
print('=' * 72)
print('Duree de l\'analyse : {:.0f} s'.format(time.time() - t0))
print('')
for cle, libelle in (('ok_narration', 'narration correcte (les deux d\'accord)'),
                     ('ok_attribution', 'replique correcte (meme personnage)'),
                     ('mauvais_nom', 'replique vue, mais MAUVAIS personnage'),
                     ('faux_positif', 'FAUX POSITIF : dialogue invente'),
                     ('replique_ratee', 'REPLIQUE RATEE : dialogue oublie')):
    print('  {:>6}  {:>5.1f} %  {}'.format(
        cats[cle], 100.0 * cats[cle] / max(total, 1), libelle))
print('')
print('  Repliques selon Gemini   : {}'.format(repliques_ref))
print('  Repliques selon le local : {}'.format(repliques_loc))
print('')
print('  Parmi les FAUX POSITIFS, {} sur {} portent un marqueur objectif'.format(
    fp_avec_marqueur, cats['faux_positif']))
print('  Parmi les REPLIQUES RATEES, {} sur {} portent un marqueur objectif'.format(
    rr_avec_marqueur, cats['replique_ratee']))
print('')
if exemples_fp:
    print('Faux positifs (phrase : personnage invente par le local) :')
    for sid, nom in exemples_fp:
        print('   phrase {:>4} : {}'.format(sid, nom))
if exemples_rr:
    print('Repliques ratees (phrase : personnage selon Gemini) :')
    for sid, nom in exemples_rr:
        print('   phrase {:>4} : {}'.format(sid, nom))
if exemples_nom:
    print('Mauvais personnage (phrase : local / Gemini) :')
    for sid, a, b in exemples_nom:
        print('   phrase {:>4} : {} / {}'.format(sid, a, b))
print('')
print('Fin de l\'analyse.')

