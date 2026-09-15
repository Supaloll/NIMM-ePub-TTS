# -*- coding: utf-8 -*-
"""
Diagnostic jetable (lecture seule, aucun appel IA) : quel est le PREMIER lot
de phrases envoye pour le chapitre qui a ete refuse par Google ?

Google a bloque la demande AVANT de repondre (motif PROHIBITED_CONTENT) sur
7894 tokens d'entree. On regarde donc, en local, ce que contenait ce lot :
nombre de phrases, taille, et presence de mots habituellement surveilles par
les filtres de securite (violence, sexe, armes...).

Lancer depuis la racine : python test_voix/_diag_blocage_chapitre.py 28 16
"""
import sys
import re
import sqlite3
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 28
CHAPITRE = int(sys.argv[2]) if len(sys.argv) > 2 else 16

# Mots que les filtres de securite surveillent, en francais et en anglais.
MOTS_SENSIBLES = [
    'viol', 'violer', 'violée', 'violee', 'sexe', 'sexuel', 'sexuelle',
    'nue', 'nu', 'seins', 'pénis', 'penis', 'vagin', 'orgasme',
    'sang', 'sanglant', 'cadavre', 'tuer', 'tué', 'tuee', 'meurtre',
    'assassinat', 'assassiner', 'assassin', 'arme', 'fusil', 'revolver',
    'pistolet', 'balle', 'poignard', 'couteau', 'gorge', 'égorgé',
    'violence', 'torture', 'suicide', 'drogue', 'héroïne', 'cocaïne',
    'nègre', 'negre', 'négro', 'bâtard', 'putain', 'salope', 'con',
    'rape', 'sex', 'gun', 'kill', 'murder', 'blood', 'dead', 'corpse',
    'nigger', 'faggot', 'whore', 'fuck',
]

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
if CHAPITRE >= len(chapters):
    print('Chapitre {} introuvable (le livre en compte {}).'.format(CHAPITRE, len(chapters)))
    sys.exit(1)

texte = chapters[CHAPITRE]['text']
sentences = vc._split_chapter_sentences(texte)
lot1 = sentences[:vc.BATCH_SIZE]

print('')
print('Livre        : {}'.format(book[1]))
print('Chapitre     : index {} ("{}")'.format(CHAPITRE, chapters[CHAPITRE]['title']))
print('Phrases      : {} au total, {} dans le premier lot envoye'.format(len(sentences), len(lot1)))
print('Taille du lot: {} caracteres (le refus de Google portait sur 7894 tokens)'.format(
    sum(len(s['texte']) for s in lot1)))

# A quoi ressemble le prompt complet du 1er lot ?
fiche = [{'nom': 'X', 'genre': 'H', 'age': 'adulte'}] * 88
prompt = vc._build_prompt(fiche, lot1)
print('Prompt envoye: {} caracteres (~{} tokens estimes)'.format(len(prompt), len(prompt) // 4))

print('')
print('MOTS SURVEILLES PRESENTS DANS CE LOT')
trouves = []
for s in lot1:
    plat = unicodedata.normalize('NFD', s['texte'].lower())
    plat = ''.join(c for c in plat if unicodedata.category(c) != 'Mn')
    for mot in MOTS_SENSIBLES:
        motif = unicodedata.normalize('NFD', mot.lower())
        motif = ''.join(c for c in motif if unicodedata.category(c) != 'Mn')
        # Frontiere de mot des DEUX cotes, avec pluriel tolere : sans cela,
        # "con" detecterait "contre" et "nu" detecterait "nuit".
        if re.search(r'\b' + re.escape(motif) + r'(?:s|es)?\b', plat):
            trouves.append((s['id'], mot))

if not trouves:
    print('  Aucun mot surveille detecte : le blocage ne vient probablement')
    print('  pas du vocabulaire, mais du contexte (scene, situation, recit).')
else:
    for sid, mot in trouves[:40]:
        print('  phrase {:>3} : "{}"'.format(sid, mot))
    print('')
    print('  {} occurrence(s) dans le lot.'.format(len(trouves)))

print('')
print('Fin du diagnostic blocage.')
