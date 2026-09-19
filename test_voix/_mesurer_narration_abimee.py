# -*- coding: utf-8 -*-
"""Les phrases de NARRATION sont-elles abimees par le retrait des incises ?

Question posee par le TEST ADVERSE du 19/09/2026 (cas A1 de Claude.AI) : une
phrase de RECIT comme

    « Il ouvrit la porte, appela la femme de chambre, et attendit. »

deviendrait « Il ouvrit la porte et attendit. » -- une ACTION disparait. Or une
phrase de narration ne devrait JAMAIS etre modifiee : elle ne contient aucune
replique, donc aucune incise a retirer.

Ce script croise DEUX sources :
  - qui prononce chaque phrase (base `speaker_attribution`) ;
  - ce que le retrait des incises lui fait (`modules/incises.py`).

Lecture seule : rien n'est modifie.

Usage : python test_voix/_mesurer_narration_abimee.py --livre 16
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
from modules.incises import retirer_incises, incises                 # noqa: E402


def main():
    analyseur = argparse.ArgumentParser(
        description='Compte les phrases de NARRATION abimees par les incises.')
    analyseur.add_argument('--livre', type=int, default=16)
    analyseur.add_argument('--exemples', type=int, default=8)
    options = analyseur.parse_args()

    from core.epub_parser import get_chapters

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT * FROM books WHERE id = ?',
                         (options.livre,)).fetchone()
    if livre is None:
        print('livre %d introuvable' % options.livre)
        return
    chemin = BIBLIOTHEQUE / livre['filename']
    print('')
    print('=' * 78)
    print('LIVRE %d : %s' % (options.livre, livre['title']))
    print('=' * 78)

    # Qui parle : (chapitre, numero de phrase) -> locuteur.
    locuteurs = {}
    for ligne in conn.execute(
            'SELECT chapter_index, sentence_idx, speaker'
            ' FROM speaker_attribution WHERE book_id = ?', (options.livre,)):
        locuteurs[(ligne['chapter_index'], ligne['sentence_idx'])] = \
            ligne['speaker']
    conn.close()

    total = {'phrases': 0, 'narration': 0, 'narration_abimee': 0,
             'perso': 0, 'perso_abimee': 0,
             # Heuristique de FORME : une replique commence-t-elle par un tiret
             # de dialogue ou un guillemet ? Si c'est fiable, on peut proteger
             # le recit SANS toucher a l'architecture (pas de champ a ajouter).
             'replique_tiret': 0, 'replique_sans_tiret': 0,
             'narration_tiret': 0,
             'incises_rates_par_forme': 0, 'incises_gagnees_par_forme': 0}
    exemples = []
    exemples_forme = []

    for chapitre in get_chapters(str(chemin)):
        for idx, phrase in enumerate(_phrases(chapitre['text'])):
            total['phrases'] += 1
            locuteur = locuteurs.get((chapitre['index'], idx))
            est_narration = (locuteur == 'narration')
            if est_narration:
                total['narration'] += 1
            elif locuteur:
                total['perso'] += 1
            if not incises(phrase):
                continue
            # --- Heuristique de FORME : tiret de dialogue ou guillemet ouvrant.
            a_tiret = phrase.lstrip()[:1] in ('\u2014', '\u2013', '\u00ab')
            if est_narration:
                if a_tiret:
                    total['narration_tiret'] += 1
            else:
                if a_tiret:
                    total['replique_tiret'] += 1
                else:
                    total['replique_sans_tiret'] += 1
            # On ne compte que les VRAIES modifications : une phrase qui n'est
            # qu'une incise est protegee par le garde-fou de `retirer_incises`
            # (elle revient inchangee), ce n'est donc PAS un degat.
            apres = retirer_incises(phrase)
            if apres == phrase:
                continue
            if est_narration:
                total['narration_abimee'] += 1
                if len(exemples) < options.exemples:
                    exemples.append((chapitre['index'], idx, phrase, apres))
            else:
                total['perso_abimee'] += 1
                # Ce qu'on PERDRAIT si on ne retirait les incises que dans les
                # phrases a tiret : une incise de replique sans tiret.
                if not a_tiret:
                    total['incises_rates_par_forme'] += 1
                    if len(exemples_forme) < options.exemples:
                        exemples_forme.append((chapitre['index'], idx, phrase,
                                               apres))

    print('')
    print('-' * 78)
    print('RESULTATS')
    print('-' * 78)
    print('  phrases du livre                          %6d' % total['phrases'])
    print('  dont phrases de NARRATION                 %6d' % total['narration'])
    print('  dont phrases de PERSONNAGE                %6d' % total['perso'])
    print('')
    print('  NARRATION touchee par le retrait          %6d   <-- a examiner'
          % total['narration_abimee'])
    part = 100.0 * total['narration_abimee'] / max(total['narration'], 1)
    print('     soit %.3f %% des phrases de narration' % part)
    print('  PERSONNAGE touche par le retrait          %6d   (normal : c est'
          ' le but)' % total['perso_abimee'])
    print('')
    print('  --- HEURISTIQUE DE FORME (tiret de dialogue ou guillemet)')
    print('      repliques qui COMMENCENT par un tiret   %6d'
          % total['replique_tiret'])
    print('      repliques SANS tiret                   %6d'
          % total['replique_sans_tiret'])
    print('      phrases de NARRATION avec un tiret     %6d'
          % total['narration_tiret'])
    print('')
    print('  Si on ne retirait les incises QUE dans les phrases a tiret :')
    print('     narration encore abimee                 %6d  (au lieu de %d)'
          % (total['narration_tiret'], total['narration_abimee']))
    print('     incises de replique RATEES               %6d'
          % total['incises_rates_par_forme'])
    print('')
    if exemples_forme:
        print('  --- EXEMPLES d incises de replique SANS tiret (ratees par la')
        print('      forme -- elles seraient encore lues) :')
        for chapitre, idx, avant, apres in exemples_forme:
            print('      chapitre %d, phrase %d' % (chapitre, idx))
            print('      livre : %s' % avant[:104])
            print('      sans l incise : %s' % apres[:104])
            print('')
    if exemples:
        print('  --- EXEMPLES de narration abimee (avant -> apres)')
        for chapitre, idx, avant, apres in exemples:
            print('      chapitre %d, phrase %d' % (chapitre, idx))
            print('      livre : %s' % avant[:104])
            print('      apres : %s' % apres[:104])
            print('')


if __name__ == '__main__':
    main()
