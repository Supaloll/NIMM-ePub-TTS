# -*- coding: utf-8 -*-
"""
Test jetable de la REPRISE du casting (session du 13/09/2026).
Aucun appel IA : les deux fonctions payantes sont remplacees par des
doublons instantanes. On verifie que les chapitres deja en base ne sont
JAMAIS reanalyses, et que la reprise repart exactement ou il faut.

La base reelle n'est pas touchee : main.DB_PATH est redirige vers un
fichier temporaire, supprime a la fin.

Lancer depuis la racine du projet : python test_voix/test_reprise_casting.py
"""
import sys
import asyncio
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

import main
from modules import voice_casting

DB_TEST = RACINE / 'data' / '_test_reprise.db'
if DB_TEST.exists():
    DB_TEST.unlink()
main.DB_PATH = DB_TEST          # la vraie base n'est pas touchee

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
# 0. Table cast_fiche creee par init_db (non destructif)
# ==============================================================
print('')
print('--- 0. Creation des tables ---')
main.init_db()
conn = sqlite3.connect(str(DB_TEST))
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
conn.close()
verifier('cast_fiche' in tables, 'la table cast_fiche est creee')
verifier('speaker_attribution' in tables, 'les tables existantes sont intactes')

# ==============================================================
# 1. Jeu d'essai : livre 28, 5 chapitres, les 3 premiers deja payes
# ==============================================================
conn = main.get_db()
conn.execute("""INSERT INTO books (id, user_id, filename, title, cast_status, multi_voice_enabled)
                VALUES (28, 1, 'faux.epub', 'Livre test', 'error', 1)""")
for ch in (0, 1, 2):
    for s in range(3):
        conn.execute("""INSERT INTO speaker_attribution (book_id, chapter_index, sentence_idx, speaker)
                        VALUES (28, ?, ?, ?)""", (ch, s, 'Alice' if s < 2 else 'Bob'))
conn.commit()
conn.close()

chapters = [{'index': i, 'title': 'Chapitre %d' % i, 'text': 'Texte du chapitre %d.' % i}
            for i in range(5)]

# --- Doublons des fonctions payantes ---
appels = []


async def faux_analyze_chapter(chapter_text, fiche_personnages, provider='gemini',
                               provider_repli=None):
    """Doublon de l'analyse : accepte provider_repli, comme la vraie fonction
    (c'est le moteur de secours utilise pour les phrases refusees)."""
    appels.append(chapter_text)
    return {
        'personnages': [{'nom': 'Nouveau%d' % len(appels), 'genre': 'F', 'age': 'adulte'}],
        'phrases': [{'id': 0, 'locuteur': 'Nouveau%d' % len(appels)}],
        'sentences': []
    }


async def faux_consolidate_book(resultats, provider='gemini', voix_figees=None, fiche_brute=None):
    return {
        'fusion': {},
        'personnages': fiche_brute or [],
        'voix': {'Alice': {'voice_id': 'v1', 'pitch': '+0Hz', 'rate': '+0%', 'genre': 'F', 'line_count': 2}},
        'compte_phrases': {'Alice': 2}
    }


voice_casting.analyze_chapter = faux_analyze_chapter
voice_casting.consolidate_book = faux_consolidate_book

# ==============================================================
# 2. Detection des chapitres deja payes
# ==============================================================
print('')
print('--- 2. Detection des chapitres deja payes ---')
conn = main.get_db()
deja = main._chapitres_deja_traites(conn, 28)
fiche_secours = main._fiche_de_secours(conn, 28)
resultats_base = main._charger_resultats_en_base(conn, 28)
conn.close()
verifier(deja == {0, 1, 2}, 'les 3 chapitres en base sont reconnus comme deja payes')
verifier(len(fiche_secours) == 2, 'fiche de secours reconstruite avec 2 noms (hors narration)')
verifier(len(resultats_base) == 3 and len(resultats_base[0]['phrases']) == 3,
         'les attributions en base sont relues dans le bon format')

# ==============================================================
# 3. REPRISE : seuls les chapitres manquants partent a l'IA
# ==============================================================
print('')
print('--- 3. Reprise apres erreur (chapitres 3 et 4 manquants) ---')
appels.clear()
asyncio.run(main._process_remaining_chapters(
    28, chapters, fiche_secours, None, None, 'gemini', None))
print('     appels IA effectues : %d' % len(appels))
verifier(len(appels) == 2, 'SEULS les 2 chapitres manquants ont ete factures')

conn = main.get_db()
statut = conn.execute("SELECT cast_status FROM books WHERE id = 28").fetchone()['cast_status']
nb_ch = conn.execute("SELECT COUNT(DISTINCT chapter_index) AS n FROM speaker_attribution WHERE book_id = 28").fetchone()['n']
nb_voix = conn.execute("SELECT COUNT(*) AS n FROM voices WHERE book_id = 28").fetchone()['n']
nb_fiche = conn.execute("SELECT COUNT(*) AS n FROM cast_fiche WHERE book_id = 28").fetchone()['n']
conn.close()
verifier(statut == 'done', 'le livre passe en done (statut = %s)' % statut)
verifier(nb_ch == 5, 'les 5 chapitres sont en base (relecture + nouveaux)')
verifier(nb_voix == 1, 'les voix ont bien ete enregistrees')
verifier(nb_fiche >= 1, 'la fiche a ete memorisee en base pour les reprises futures')

# ==============================================================
# 4. Livre neuf : premier chapitre en direct, le reste en fond
# ==============================================================
print('')
print('--- 4. Livre neuf (aucun chapitre en base) ---')
conn = main.get_db()
conn.execute("""INSERT INTO books (id, user_id, filename, title, cast_status, multi_voice_enabled)
                VALUES (29, 1, 'faux2.epub', 'Livre neuf', 'none', 0)""")
conn.commit()
conn.close()

appels.clear()
premier = asyncio.run(faux_analyze_chapter('Texte du chapitre 0.', []))
deja_direct = len(appels)
asyncio.run(main._process_remaining_chapters(
    29, chapters, premier['personnages'], premier, 0, 'gemini', None))
print('     appels IA dans la tache de fond : %d' % (len(appels) - deja_direct))
verifier(len(appels) - deja_direct == 4,
         'seuls les 4 chapitres suivants ont ete analyses (le premier etait deja fait)')

conn = main.get_db()
nb_ch = conn.execute("SELECT COUNT(DISTINCT chapter_index) AS n FROM speaker_attribution WHERE book_id = 29").fetchone()['n']
conn.close()
verifier(nb_ch == 5, 'le livre neuf a bien ses 5 chapitres en base')

# ==============================================================
# 4b. TOUS les chapitres deja payes : seule la Passe 2 repart
#     (cas d'un plantage a la toute fin, apres le dernier chapitre --
#      c'est le scenario le plus frustrant, donc celui qu'il faut garantir)
# ==============================================================
print('')
print('--- 4b. Tous les chapitres deja en base : seule la Passe 2 repart ---')
conn = main.get_db()
conn.execute("""INSERT INTO books (id, user_id, filename, title, cast_status, multi_voice_enabled)
                VALUES (30, 1, 'faux3.epub', 'Livre entierement analyse', 'error', 1)""")
for ch in range(5):
    for s in range(2):
        conn.execute("""INSERT INTO speaker_attribution (book_id, chapter_index, sentence_idx, speaker)
                        VALUES (30, ?, ?, ?)""", (ch, s, 'Alice'))
conn.commit()
conn.close()

appels.clear()
asyncio.run(main._process_remaining_chapters(
    30, chapters, fiche_secours, None, None, 'gemini', None))
print('     appels IA de Passe 1 : %d' % len(appels))
verifier(len(appels) == 0, 'AUCUN chapitre n a ete renvoye a l IA (tout etait deja paye)')

conn = main.get_db()
statut30 = conn.execute("SELECT cast_status FROM books WHERE id = 30").fetchone()['cast_status']
voix30 = conn.execute("SELECT COUNT(*) AS n FROM voices WHERE book_id = 30").fetchone()['n']
conn.close()
verifier(statut30 == 'done', 'le livre repasse bien en done (statut = %s)' % statut30)
verifier(voix30 == 1, 'les voix sont enfin attribuees : la Passe 2 a joue seule')

# ==============================================================
# 5. Deviner le genre (reprise d'un livre sans fiche memorisee)
# ==============================================================
print('')
print('--- 5. Genres devines sur les personnages du livre 28 ---')
for nom in ['Mimi Corcoran', 'Beverly Marsh', 'Sadie Clayton', 'Ellen Dunning']:
    verifier(voice_casting.deviner_genre(nom) == 'F', '%s -> F' % nom)
for nom in ['Jake Epping', 'Al Templeton', 'Charles Frati', 'Bill Turcotte', 'Richie Tozier']:
    verifier(voice_casting.deviner_genre(nom) == 'H', '%s -> H' % nom)
verifier(voice_casting.deviner_genre('Col-bleu sans bretelles') == 'H',
         'un surnom sans prenom connu -> H (defaut, corrigeable a la main)')

# ==============================================================
# Nettoyage
# ==============================================================
if DB_TEST.exists():
    DB_TEST.unlink()

print('')
print('=' * 60)
print('RESULTAT : %d OK, %d ERR' % (OK, ERR))
print('=' * 60)
sys.exit(1 if ERR else 0)
