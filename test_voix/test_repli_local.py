# -*- coding: utf-8 -*-
"""
Test du REPLI AUTOMATIQUE vers le moteur local (session du 13/09/2026).
GRATUIT : le refus du moteur distant est simule, mais le moteur local
travaille pour de vrai (aucun euro, rien ne sort du poste).

Scenario reproduit : un moteur distant refuse SYSTEMATIQUEMENT le texte (ce
que fait Google sur une scene qu'il juge interdite). Le decoupage en lots plus
petits n'y change rien. Sans repli, les phrases concernees seraient lues par
le narrateur ; avec le repli, elles sont confiees au moteur local, qui
n'applique aucun filtre.

Lancer depuis la racine : python test_voix/test_repli_local.py
"""
import sys
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


etat = vc.local_disponible()
if not etat.get('disponible'):
    print('')
    print('Le moteur local n\'est pas disponible ({}) : test ignore.'.format(etat.get('raison')))
    print('RESULTAT : 0 OK, 0 ERR')
    sys.exit(0)

# --- Simulation : le moteur distant refuse TOUT, le local est le vrai ---
vrai_call_llm = vc._call_llm


async def faux_call_llm(prompt, provider='gemini'):
    if provider == 'local':
        return await vrai_call_llm(prompt, provider)
    raise vc.BlocageContenu('simulation : le filtre du moteur distant refuse ce texte')


vc._call_llm = faux_call_llm

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename FROM books WHERE id = 28").fetchone()
fiche = [{'nom': r[0], 'genre': r[1], 'age': r[2]} for r in conn.execute(
    "SELECT character_name, genre, age FROM cast_fiche WHERE book_id = 28")]
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
extrait = vc._split_chapter_sentences(chapters[16]['text'])[:6]
texte = ' '.join(s['texte'] for s in extrait)
print('')
print('--- Extrait de {} phrase(s) du chapitre 17 ---'.format(len(extrait)))

# ==============================================================
# 1. SANS repli : les phrases refusees restent au narrateur
# ==============================================================
print('')
print('--- 1. Sans repli (comportement precedent) ---')
sans = asyncio.run(vc.analyze_chapter(texte, fiche, 'gemini'))
refusees_sans = sans.get('refusees') or []
narration_sans = [p for p in sans['phrases'] if p['locuteur'] == 'narration']
print('     phrases refusees : {}'.format(len(refusees_sans)))
verifier(bool(refusees_sans), 'le refus est bien detecte et trace')
verifier(len(narration_sans) == len(sans['phrases']),
         'sans repli, toutes les phrases restent au narrateur (rien n\'est perdu, mais pas attribue)')

# ==============================================================
# 2. AVEC repli : le moteur local recupere les phrases refusees
# ==============================================================
print('')
print('--- 2. Avec repli local (nouveau comportement) ---')
avec = asyncio.run(vc.analyze_chapter(texte, fiche, 'gemini', provider_repli='local'))
rattrapees = [p for p in avec['phrases']
              if p.get('anomalie') and 'rattrapee par local' in p['anomalie']]
print('     phrases rattrapees en local : {}'.format(len(rattrapees)))
for p in rattrapees:
    print('        phrase {} : {}'.format(p['id'], p['locuteur']))
verifier(bool(rattrapees), 'au moins une phrase refusee a ete rattrapee par le moteur local')
verifier(all(p['locuteur'] != 'narration' for p in rattrapees),
         'les phrases rattrapees ont bien un vrai locuteur')
verifier(len(avec['phrases']) == len(sans['phrases']),
         'le chapitre reste complet (aucune phrase perdue)')

print('')
print('=' * 60)
print('RESULTAT : %d OK, %d ERR' % (OK, ERR))
print('=' * 60)
sys.exit(1 if ERR else 0)
