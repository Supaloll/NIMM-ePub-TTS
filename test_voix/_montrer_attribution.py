# -*- coding: utf-8 -*-
"""Montre, phrase par phrase, QUI PARLE et AVEC QUELLE VOIX dans un chapitre.

Outil de consultation (lecture seule, rien à allumer). Il répond à la question
« comment sont taggées les voix ? » en montrant la réalité :

    n°  locuteur                 voix                    texte
    12  Eugenie_Danglars         Angèle — France (Kyutai) — Merci. Un dernier mot...
    13  narration                Ariane — France (Edge)   Le baron se tut un instant...

Deux étages, et c'est tout :
  1. `speaker_attribution` : à la phrase n°X du chapitre Y, c'est TEL locuteur ;
  2. `voices` : TEL personnage parle avec TELLE voix (vitesse et hauteur comprises).
Le texte, lui, n'est PAS en base : il est relu de l'epub (fichier du livre).

Usage :
    python test_voix/_montrer_attribution.py --livre 16 --chapitre 16
    python test_voix/_montrer_attribution.py --livre 16 --chapitre 16 --autour 20
    python test_voix/_montrer_attribution.py --livre 16 --chapitre 16 --seulement Personnage
"""

import argparse
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

from modules.decoupage import phrases as _phrases                    # noqa: E402


def main():
    analyseur = argparse.ArgumentParser(
        description='Montre qui parle, phrase par phrase, dans un chapitre.')
    analyseur.add_argument('--livre', type=int, required=True)
    analyseur.add_argument('--chapitre', type=int, required=True,
                           help='index du chapitre (0 = le premier du livre)')
    analyseur.add_argument('--autour', type=int, default=0,
                           help='ne montrer que N phrases autour de --phrase')
    analyseur.add_argument('--phrase', type=int, default=None,
                           help='numero de phrase a entourer')
    analyseur.add_argument('--seulement', default=None,
                           help='ne montrer que les phrases de ce locuteur')
    analyseur.add_argument('--texte', type=int, default=90,
                           help='longueur du texte affiche (0 = pas de texte)')
    options = analyseur.parse_args()

    from core.epub_parser import get_chapters

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT * FROM books WHERE id = ?',
                         (options.livre,)).fetchone()
    if livre is None:
        print('Livre %d introuvable.' % options.livre)
        return 1

    chemin = BIBLIOTHEQUE / livre['filename']
    if not chemin.is_file():
        print('Fichier introuvable : %s' % chemin)
        return 1

    chapitres = get_chapters(str(chemin))
    chapitre = None
    for c in chapitres:
        if c['index'] == options.chapitre:
            chapitre = c
            break
    if chapitre is None:
        print('Chapitre %d absent du livre (%d chapitres).'
              % (options.chapitre, len(chapitres)))
        return 1

    textes = _phrases(chapitre.get('text') or '')
    attributions = {r['sentence_idx']: r['speaker'] for r in conn.execute(
        'SELECT sentence_idx, speaker FROM speaker_attribution '
        'WHERE book_id = ? AND chapter_index = ?',
        (options.livre, options.chapitre))}
    voix = {r['character_name']: (r['voice_id'], r['rate'], r['pitch'])
            for r in conn.execute(
                'SELECT character_name, voice_id, rate, pitch FROM voices '
                'WHERE book_id = ?', (options.livre,))}

    print('')
    print('=' * 90)
    print('%s' % livre['title'])
    print('Chapitre %d : %s   (%d phrases, %d attributions en base)'
          % (options.chapitre, (chapitre.get('title') or '')[:40],
             len(textes), len(attributions)))
    print('=' * 90)

    debut, fin = 0, len(textes) - 1
    if options.autour and options.phrase is not None:
        debut = max(0, options.phrase - options.autour)
        fin = min(len(textes) - 1, options.phrase + options.autour)

    montrees = 0
    for idx in range(debut, fin + 1):
        locuteur = attributions.get(idx, '')
        if options.seulement and locuteur != options.seulement:
            continue
        if locuteur:
            infos = voix.get(locuteur)
            if infos:
                nom_voix = infos[0]
                if infos[1] and infos[1] not in ('+0%', ''):
                    nom_voix += '  vitesse ' + infos[1]
                if infos[2] and infos[2] not in ('+0Hz', ''):
                    nom_voix += '  hauteur ' + infos[2]
            else:
                nom_voix = '(aucune voix : voix du lecteur)'
        else:
            nom_voix = '(aucune attribution : voix du lecteur)'
            locuteur = '?'
        extrait = (' \u2014 ' + textes[idx][:options.texte]) if options.texte else ''
        print('%5d  %-24s %-30s%s'
              % (idx, locuteur[:24], nom_voix[:30], extrait))
        montrees += 1

    print('')
    print('  %d phrase(s) affichee(s).' % montrees)
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
