# -*- coding: utf-8 -*-
"""
Test du MOTEUR LOCAL integre (session du 13/09/2026).
AUCUN euro depense : tout se passe sur le poste.

Ce qui est verifie :
  1. l'etat du moteur local (Ollama repond-il, modele installe ?) ;
  2. un appel reel de bout en bout par la fonction du logiciel
     (_call_llm avec provider="local") sur un mini-lot de phrases ;
  3. la lecture de la reponse par le code de production (_normaliser_reponse).

Lancer depuis la racine : python test_voix/test_moteur_local.py
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

OK = 0
ERR = 0


def verifier(condition, message):
    global OK, ERR
    if condition:
        OK += 1
        print('  OK  ' + message)
    else:
        ERR += 1
        print('  ERR ' + message)


# ==============================================================
# 1. Etat du moteur local
# ==============================================================
print('')
print('--- 1. Etat du moteur local ---')
etat = vc.local_disponible()
print('     modele configure : {}'.format(etat.get('modele')))
print('     disponible       : {}'.format(etat.get('disponible')))
if etat.get('raison'):
    print('     raison           : {}'.format(etat.get('raison')))
verifier('disponible' in etat and 'modele' in etat, 'la fonction repond une structure exploitable')
if not etat.get('disponible'):
    print('')
    print('  Le moteur local n\'est pas disponible : le reste du test est ignore.')
    print('  (Demarrer Ollama, puis relancer ce test.)')
    print('')
    print('RESULTAT : {} OK, {} ERR'.format(OK, ERR))
    sys.exit(0)
verifier(True, 'le modele configure est bien installe')

# ==============================================================
# 2. Appel reel par le code de production
# ==============================================================
print('')
print('--- 2. Appel reel sur un mini-lot (5 phrases) ---')
conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = 28").fetchone()
fiche = [{'nom': r[0], 'genre': r[1], 'age': r[2]} for r in conn.execute(
    "SELECT character_name, genre, age FROM cast_fiche WHERE book_id = 28")]
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
sentences = vc._split_chapter_sentences(chapters[16]['text'])[:5]
prompt = vc._build_prompt(fiche, sentences)

t0 = time.time()
try:
    brut = asyncio.run(vc._call_llm(prompt, 'local'))
    duree = time.time() - t0
    print('     reponse recue en {:.1f} s'.format(duree))
    verifier(isinstance(brut, dict), 'le moteur local a renvoye un objet exploitable')
    norm = vc._normaliser_reponse(brut, fiche, {s['id'] for s in sentences})
    verifier(len(norm['phrases']) == 5, 'les 5 phrases ont un locuteur apres lecture')
    repliques = [p for p in norm['phrases'] if p['locuteur'] != 'narration']
    print('     repliques detectees dans ce mini-lot : {}'.format(len(repliques)))
    for p in repliques:
        print('        phrase {} : {}'.format(p['id'], p['locuteur']))
except Exception as e:
    verifier(False, 'appel local : {}'.format(str(e)[:200]))

# ==============================================================
# 3. Cout annonce a zero
# ==============================================================
print('')
print('--- 3. Cout ---')
est = vc.estimate_cast_cost(['Phrase une. Phrase deux.'], 'local')
verifier(est['cost_display'].startswith('gratuit'), 'l\'estimation annonce bien « gratuit »')
t = vc.tokens_session('local')
verifier(t['cout_usd_estime'] == 0, 'le decompte de cout du moteur local est bien a zero')

print('')
print('=' * 60)
print('RESULTAT : %d OK, %d ERR' % (OK, ERR))
print('=' * 60)
sys.exit(1 if ERR else 0)
