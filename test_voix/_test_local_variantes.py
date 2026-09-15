# -*- coding: utf-8 -*-
"""
Test LOCAL : recherche du bon REGLAGE (session du 13/09/2026, gratuit).

Premier constat : avec des lots de 150 phrases et la consigne actuelle, Qwen2.5
ne repere que la moitie des repliques (51 % d'accord avec la reference Gemini).
Hypothese : un petit modele ne fait pas un travail long et exhaustif. On teste
donc, sur le MEME passage, plusieurs reglages :

  A. lots de 150 phrases, consigne actuelle (repere de comparaison) ;
  B. lots de 40 phrases, consigne actuelle ;
  C. lots de 40 phrases, consigne + aide explicite de reperage des repliques ;
  D. lots de 20 phrases, consigne + aide.

Indicateurs : precision (ce que le local annonce est-il une vraie replique ?)
et rappel (a-t-il trouve toutes les vraies repliques ?). Le RAPPEL est le plus
important : une replique oubliee est lue par le narrateur.

Lancer depuis la racine : python test_voix/_test_local_variantes.py
"""
import sys
import json
import time
import sqlite3
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

# API NATIVE d'Ollama (et non la compatibilite OpenAI) : c'est la seule qui
# permette de fixer num_ctx. Constat du 13/09/2026 : Ollama bride le contexte
# a 4096 tokens par defaut, alors que notre prompt en fait ~7800 -- le modele
# ne voyait donc qu'une PARTIE du texte et "oubliait" la moitie des repliques.
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
CONTEXTE_TOKENS = 16384
BOOK_ID = 28
CHAPITRE = int(sys.argv[1]) if len(sys.argv) > 1 else 16
NB_PHRASES = int(sys.argv[2]) if len(sys.argv) > 2 else 150
MODELE = sys.argv[3] if len(sys.argv) > 3 else "Qwen2.5:latest"

AIDE = """
AIDE POUR REPERER LES REPLIQUES (a appliquer sans aucune exception) :
- Toute phrase qui commence par un tiret (— ou -) est une replique.
- Toute phrase qui contient un passage entre guillemets (« ... » ou " ... ") est une replique.
- Toute phrase qui contient une incise du type "dit-il", "reprit X", "s'ecria Y" est une replique.
- Une phrase n'est de la NARRATION que si elle ne contient AUCUNE replique.
- Tu dois lister TOUTES les repliques du lot, sans en oublier : un lot de 40 phrases en contient souvent 15 a 25. Ne t'arrete pas aux premieres.
"""


def appeler(prompt):
    corps = {
        "model": MODELE,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_ctx": CONTEXTE_TOKENS, "num_predict": 4096},
    }
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(corps).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=1800) as r:
        rep = json.loads(r.read().decode("utf-8"))
    return (rep.get("message") or {}).get("content", ""), time.time() - t0


def extraire_json(texte):
    texte = (texte or "").strip()
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut >= 0 and fin > debut:
        texte = texte[debut:fin + 1]
    return json.loads(texte)


conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
fiche = [{'nom': r[0], 'genre': r[1], 'age': r[2]} for r in conn.execute(
    "SELECT character_name, genre, age FROM cast_fiche WHERE book_id = ?", (BOOK_ID,))]
verite = {(r[0], r[1]): r[2] for r in conn.execute(
    "SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution "
    "WHERE book_id = ? AND chapter_index = ?", (BOOK_ID, CHAPITRE))}
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
sentences = vc._split_chapter_sentences(chapters[CHAPITRE]['text'])[:NB_PHRASES]
ref_repliques = {s['id'] for s in sentences if verite.get((CHAPITRE, s['id']), 'narration') != 'narration'}

print('')
print('=' * 74)
print('REGLAGES DU MODELE LOCAL -- {} sur {} phrases'.format(MODELE, len(sentences)))
print('=' * 74)
print('Reference Gemini : {} repliques sur {} phrases ({:.0f} %)'.format(
    len(ref_repliques), len(sentences), 100.0 * len(ref_repliques) / max(len(sentences), 1)))
print('')
print('{:<6} {:<8} {:>9} {:>8} {:>8} {:>8} {:>10}'.format(
    'casse', 'lot', 'duree', 'trouve', 'rappel', 'precision', 'accord'))
print('-' * 74)

for etiquette, taille_lot, avec_aide in (('A', 150, False), ('B', 40, False), ('C', 40, True), ('D', 20, True)):
    trouve = set()
    duree = 0.0
    for i in range(0, len(sentences), taille_lot):
        lot = sentences[i:i + taille_lot]
        prompt = vc._build_prompt(fiche, lot) + (AIDE if avec_aide else '')
        try:
            texte, d = appeler(prompt)
            norm = vc._normaliser_reponse(extraire_json(texte), fiche, {s['id'] for s in lot})
        except Exception as e:
            print('   {} : erreur {}'.format(etiquette, str(e)[:60]))
            continue
        duree += d
        for p in norm['phrases']:
            if p['locuteur'] != 'narration':
                trouve.add(p['id'])

    rappel = 100.0 * len(trouve & ref_repliques) / max(len(ref_repliques), 1)
    precision = 100.0 * len(trouve & ref_repliques) / max(len(trouve), 1)
    accord = sum(1 for s in sentences
                 if (s['id'] in trouve) == (s['id'] in ref_repliques))
    print('{:<6} {:<8} {:>8.0f}s {:>8} {:>7.0f}% {:>7.0f}% {:>9.0f}%'.format(
        etiquette, taille_lot, duree, len(trouve), rappel, precision,
        100.0 * accord / max(len(sentences), 1)), flush=True)

print('')
print('rappel    = part des vraies repliques que le local a bien vues (a maximiser)')
print('precision = part de ses reponses qui sont de vraies repliques')
print('accord    = phrases avec le meme diagnostic que Gemini')
print('')
print('Fin du test des reglages.')
