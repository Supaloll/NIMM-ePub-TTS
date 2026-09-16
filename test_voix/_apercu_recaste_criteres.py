# -*- coding: utf-8 -*-
"""Apercu du re-cast PAR CRITERES : ce qui changerait sur un livre, sans ecrire.

Compare l'ancien tri (paliers d'etoiles) et le nouveau (annotations d'ecoute),
personnage par personnage, en respectant les verrous. Lecture seule.

Usage : python test_voix/_apercu_recaste_criteres.py [book_id] [nombre]
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

import main                                                     # noqa: E402
from modules import tts, voice_casting                          # noqa: E402

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 35
TOP = int(sys.argv[2]) if len(sys.argv) > 2 else 22


def libelles():
    noms = {}
    for source in (main.FRENCH_VOICES, tts.KOKORO_VOICES, tts.XTTS_VOICES,
                   tts.KYUTAI_VOICES, tts.PIPER_VOICES):
        for voix in source:
            noms[voix['id']] = voix.get('name') or voix['id']
    return noms


def main_apercu():
    base = 'file:%s?mode=ro' % (RACINE / 'data' / 'nimm_epub.db').as_posix()
    conn = sqlite3.connect(base, uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT title FROM books WHERE id = ?', (BOOK_ID,)).fetchone()
    rows = list(conn.execute(
        'SELECT character_name, voice_id, genre, line_count, locked '
        'FROM voices WHERE book_id = ? ORDER BY line_count DESC', (BOOK_ID,)))
    fiche = {r['character_name']: (r['age'] or 'adulte') for r in conn.execute(
        'SELECT character_name, age FROM cast_fiche WHERE book_id = ?', (BOOK_ID,))}
    conn.close()
    if not rows:
        print('Aucun personnage caste pour ce livre.')
        return

    personnages = [{'nom': r['character_name'], 'genre': r['genre'] or 'H',
                    'age': fiche.get(r['character_name'], 'adulte')} for r in rows]
    compte = {r['character_name']: r['line_count'] or 0 for r in rows}
    figees = {r['character_name']: {'voice_id': r['voice_id'], 'pitch': '+0Hz',
                                    'rate': '+0%', 'genre': r['genre'] or 'H'}
              for r in rows if r['locked']}

    nouveau = voice_casting.assign_voices(personnages, compte,
                                          voix_figees=figees, par_criteres=True)
    ancien = voice_casting.assign_voices(personnages, compte,
                                         voix_figees=figees, par_criteres=False)
    notes = voice_casting.lire_annotations_voix()
    noms = libelles()

    print('Livre %d : %s' % (BOOK_ID, livre['title'] if livre else '?'))
    print('Personnages : %d (verrouilles : %d)'
          % (len(rows), len(figees)))
    print('')
    print('%-26s %-6s %5s  %-22s -> %-22s %s'
          % ('personnage', 'age', 'repl', 'ancien tri', 'par criteres', 'critere'))
    print('-' * 108)

    changes = 0
    for r in rows[:TOP]:
        nom = r['character_name']
        av = ancien.get(nom, {}).get('voice_id') or '-'
        ap = nouveau.get(nom, {}).get('voice_id') or '-'
        note = notes.get(ap) or {}
        critere = '/'.join(x for x in (note.get('age'), note.get('timbre'),
                                       note.get('debit')) if x)
        etoiles = note.get('stars')
        if av != ap and ap:
            changes += 1
        marque = 'verrou' if r['locked'] else (
            critere + (' %s*' % etoiles if etoiles is not None else ''))
        print('%-26s %-6s %5s  %-22s -> %-22s %s'
              % (nom[:26], fiche.get(nom, '?'), r['line_count'],
                 noms.get(av, av)[:22], noms.get(ap, ap)[:22], marque))

    print('-' * 108)
    differents = sum(1 for r in rows
                     if (ancien.get(r['character_name'], {}).get('voice_id')
                         != nouveau.get(r['character_name'], {}).get('voice_id')))
    print('Voix qui changeraient : %d sur %d personnages.' % (differents, len(rows)))
    print('Rappel : rien n a ete ecrit. Le bouton « Re-caster » du lecteur'
          ' applique ce resultat.')


main_apercu()
