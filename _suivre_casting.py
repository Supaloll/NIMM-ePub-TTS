# -*- coding: utf-8 -*-
"""
Surveillance de l'attribution des voix (lecture seule).

Affiche, sans jamais toucher au code ni declencher d'appel IA, l'avancement
reel du casting d'un livre : etat, chapitres deja attribues, personnages,
voix. Permet de suivre depuis ce terminal un cast lance dans le navigateur.

Usage :
    python _suivre_casting.py                  -> livre 28, 1 releve
    python _suivre_casting.py 28 5 5           -> livre 28, 5 releves, 5 s
"""
import sys
import time
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent
DB = BASE / 'data' / 'nimm_epub.db'

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 28
NB_RELEVES = int(sys.argv[2]) if len(sys.argv) > 2 else 1
INTERVALLE = int(sys.argv[3]) if len(sys.argv) > 3 else 5


def releve():
    """Un instantane de l'etat du casting."""
    conn = sqlite3.connect('file:{}?mode=ro'.format(DB.as_posix()), uri=True)
    conn.row_factory = sqlite3.Row
    book = conn.execute(
        "SELECT title, cast_status, multi_voice_enabled FROM books WHERE id = ?",
        (BOOK_ID,)
    ).fetchone()
    if not book:
        conn.close()
        return None
    chapitres = conn.execute(
        "SELECT COUNT(DISTINCT chapter_index) AS n FROM speaker_attribution WHERE book_id = ?",
        (BOOK_ID,)
    ).fetchone()['n']
    phrases = conn.execute(
        "SELECT COUNT(*) AS n FROM speaker_attribution WHERE book_id = ?",
        (BOOK_ID,)
    ).fetchone()['n']
    locuteurs = conn.execute(
        "SELECT COUNT(DISTINCT speaker) AS n FROM speaker_attribution WHERE book_id = ?",
        (BOOK_ID,)
    ).fetchone()['n']
    voix = conn.execute(
        "SELECT COUNT(*) AS n FROM voices WHERE book_id = ?", (BOOK_ID,)
    ).fetchone()['n']
    conn.close()
    return {
        'titre': book['title'],
        'statut': str(book['cast_status']),
        'chapitres': chapitres,
        'phrases': phrases,
        'locuteurs': locuteurs,
        'voix': voix,
    }


def afficher(bloc, precedent):
    print('[{}] livre {} "{}"'.format(
        time.strftime('%H:%M:%S'), BOOK_ID, bloc['titre']))
    print('   etat serveur    : {}'.format(bloc['statut']))
    print('   chapitres payes : {}{}'.format(
        bloc['chapitres'],
        '' if not precedent else '  ({:+d} depuis le dernier releve)'.format(
            bloc['chapitres'] - precedent['chapitres'])))
    print('   phrases         : {}{}'.format(
        bloc['phrases'],
        '' if not precedent else '  ({:+d})'.format(
            bloc['phrases'] - precedent['phrases'])))
    print('   personnages     : {}'.format(bloc['locuteurs']))
    print('   voix enregistrees : {}{}'.format(
        bloc['voix'],
        '  <-- LA PASSE 2 EST PASSEE' if bloc['voix'] else ''))


print('Surveillance du casting (lecture seule, aucun appel IA).')
print('Arret : Ctrl+C.  Aucun impact sur ce que fait le navigateur.')
print('')

precedent = None
for i in range(NB_RELEVES):
    bloc = releve()
    if bloc is None:
        print('Livre {} introuvable.'.format(BOOK_ID))
        break
    afficher(bloc, precedent)
    precedent = bloc
    if bloc['statut'] in ('done', 'error'):
        print('')
        print('>>> Etat final atteint : {}'.format(bloc['statut']))
        break
    if i < NB_RELEVES - 1:
        print('')
        time.sleep(INTERVALLE)

print('')
print('Fin de la surveillance.')
