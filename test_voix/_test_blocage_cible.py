# -*- coding: utf-8 -*-
"""
Test CIBLE du blocage Google (session du 13/09/2026).
ATTENTION : ce script fait de VRAIS appels a Gemini -- donc payants, mais
minuscules : seuls les lots ACCEPTES consomment des tokens d'entree
(~1500 a 4000 par appel), les lots refuses ne generent aucun texte.

Principe : on envoie le premier lot du chapitre, et s'il est refuse on le
coupe en deux, puis encore en deux, jusqu'a isoler la ou les phrases qui
declenchent le filtre PROHIBITED_CONTENT.

Lancer depuis la racine :
    python test_voix/_test_blocage_cible.py 28 16
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

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 28
CHAPITRE = int(sys.argv[2]) if len(sys.argv) > 2 else 16
APPELS_MAX = 30
COUPABLES_MAX = 3


def fiche_du_livre():
    """Meme fiche que celle qu'utilisera la reprise : noms deja en base,
    genre devine par le prenom."""
    conn = sqlite3.connect('file:{}?mode=ro'.format(
        (BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
    noms = [r[0] for r in conn.execute(
        "SELECT DISTINCT speaker FROM speaker_attribution WHERE book_id = ? "
        "AND speaker != 'narration'", (BOOK_ID,))]
    conn.close()
    return [{'nom': n, 'genre': vc.deviner_genre(n), 'age': 'adulte'} for n in noms]


async def essayer(fiche, batch):
    """Envoie un lot ; retourne True si l'IA a repondu, False si elle refuse."""
    prompt = vc._build_prompt(fiche, batch)
    try:
        await vc._call_llm(prompt, 'gemini')
        return True
    except RuntimeError as e:
        print('      (motif : {})'.format(str(e)[:160]), flush=True)
        return False


async def localiser(fiche, batch, etiquette, etat, profondeur=0):
    if etat['appels'] >= APPELS_MAX or len(etat['coupables']) >= COUPABLES_MAX:
        return
    ok = await essayer(fiche, batch)
    etat['appels'] += 1
    if ok:
        etat['acceptes'] += 1
    print('{}{} ({} phrases, id {} a {}) : {}'.format(
        '   ' * profondeur, etiquette, len(batch), batch[0]['id'], batch[-1]['id'],
        'ACCEPTE' if ok else 'REFUSE'), flush=True)

    if ok:
        return
    if len(batch) <= 1:
        etat['coupables'].append(batch[0]['id'])
        print('{}>>> PHRASE RESPONSABLE : id {}'.format('   ' * profondeur, batch[0]['id']), flush=True)
        return

    milieu = len(batch) // 2
    await localiser(fiche, batch[:milieu], etiquette + '-A', etat, profondeur + 1)
    await localiser(fiche, batch[milieu:], etiquette + '-B', etat, profondeur + 1)


async def main():
    conn = sqlite3.connect('file:{}?mode=ro'.format(
        (BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
    book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
    conn.close()

    chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
    sentences = vc._split_chapter_sentences(chapters[CHAPITRE]['text'])
    lot = sentences[:vc.BATCH_SIZE]
    fiche = fiche_du_livre()

    print('=' * 66)
    print('TEST CIBLE DE BLOCAGE')
    print('=' * 66)
    print('Livre    : {}'.format(book[1]))
    print('Chapitre : index {} ("{}"), {} phrases'.format(
        CHAPITRE, chapters[CHAPITRE]['title'], len(sentences)))
    print('Lot teste: {} premieres phrases'.format(len(lot)))
    print('Fiche    : {} personnages (reconstruite comme lors d\'une reprise)'.format(len(fiche)))
    print('Limite   : {} appels maximum'.format(APPELS_MAX))
    print('')
    print('Debut des envois...')
    print('')

    etat = {'appels': 0, 'acceptes': 0, 'coupables': []}
    await localiser(fiche, lot, 'LOT', etat)

    print('')
    print('=' * 66)
    print('RESULTAT')
    print('=' * 66)
    print('Appels effectues        : {}'.format(etat['appels']))
    print('Lots acceptes par Google: {} (seuls ceux-la sont factures)'.format(etat['acceptes']))
    if etat['coupables']:
        print('Phrases responsables    : {}'.format(etat['coupables']))
        print('(la phrase id 0 est la 1re du chapitre : id 55 = 56e phrase)')
    else:
        print('Aucune phrase isolee     : le blocage depend du CONTEXTE global')
        print('(une moitie acceptee, l\'autre refusee, sans phrase unique coupable)')
    print('')
    print('Fin du test cible.')


asyncio.run(main())
