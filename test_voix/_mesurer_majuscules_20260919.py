# -*- coding: utf-8 -*-
"""MESURE : les mots TOUT EN MAJUSCULES dans un livre (demande de Laurent).

Constat de Laurent (19/09/2026) : « les mots en majuscule donnent une
prononciation bizarre, il faudrait modifier pour qu'ils soient lus normalement ».

Ce script liste les mots de 2 lettres et plus ecrits ENTIEREMENT en majuscules,
combien de fois, et dans quelles phrases — pour savoir quoi corriger, et si la
regle doit avoir des exceptions (initiales, sigles, chiffres romains).

Lecture seule : rien n'est modifie.

Usage : python test_voix/_mesurer_majuscules_20260919.py --livre 16
"""

import argparse
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

from modules.decoupage import phrases as _phrases                    # noqa: E402

# Un mot de 2 lettres et plus, TOUT en majuscules. On accepte les accents et les
# apostrophes a l'interieur (« D'ARTAGNAN »). Les chiffres romains et les
# initiales seules (« M. », « V ») sont vus a part.
MOT_MAJUSCULES = re.compile(r'\b[A-Z\u00c0-\u00d6\u00d8-\u00de]{2,}\b')
ROMAIN = re.compile(r'^[IVXLCDM]+$')

# Un mot en casse NORMALE : minuscules, ou majuscule initiale (« Jim »), ou
# mixte — tout sauf un mot ENTIEREMENT en majuscules. Sert a tester l'idee qui
# suit : un mot ecrit aussi en casse normale ailleurs dans le livre est un mot
# de la langue (« DE » et « de », « JIM » et « Jim ») ; un mot qui n'apparait
# JAMAIS autrement est un sigle (« JFK », « FBI »).
MOT_QUELCONQUE = re.compile(r"[\w\u00c0-\u00ff\u2019'-]{2,}", re.UNICODE)


def _compter(chemin):
    """(phrases, phrases avec majuscules, compteurs majuscules et minuscules)."""
    from core.epub_parser import get_chapters
    total = 0
    touchees = 0
    comptes = Counter()
    normaux = Counter()
    for chapitre in get_chapters(str(chemin)):
        for phrase in _phrases(chapitre['text']):
            total += 1
            for mot in MOT_QUELCONQUE.findall(phrase):
                if MOT_MAJUSCULES.fullmatch(mot) or ROMAIN.match(mot):
                    continue
                normaux[mot.lower()] += 1
            trouves = [m for m in MOT_MAJUSCULES.findall(phrase)
                       if not ROMAIN.match(m)]
            if trouves:
                touchees += 1
                for mot in trouves:
                    comptes[mot] += 1
    return total, touchees, comptes, normaux


def _tous_les_livres(livres):
    """Le resume livre par livre, puis TOUS les mots distincts a trier."""
    print('')
    print('=' * 78)
    print('LES MAJUSCULES, LIVRE PAR LIVRE')
    print('=' * 78)
    global_comptes = Counter()
    for ligne in livres:
        chemin = BIBLIOTHEQUE / ligne['filename']
        if not chemin.is_file():
            print('  [%2d] %-40s (fichier absent)'
                  % (ligne['id'], (ligne['title'] or '')[:40]))
            continue
        total, touchees, comptes, _normaux = _compter(chemin)
        global_comptes.update(comptes)
        top = ', '.join('%s(%d)' % (m, n) for m, n in comptes.most_common(4))
        print('  [%2d] %-36s %5d phr., %4d avec maj.  %s'
              % (ligne['id'], (ligne['title'] or '')[:36], total, touchees, top))
    print('')
    print('=' * 78)
    print('TOUS LES MOTS EN MAJUSCULES, TOUS LIVRES CONFONDUS (%d distincts)'
          % len(global_comptes))
    print('  -> a TRIER : un mot de la langue (DE, LA, LUI...) se met en')
    print('     minuscules ; un SIGLE (OK, DSK, ISBN...) ne se touche pas.')
    print('=' * 78)
    ligne_courante = ''
    for mot, nombre in global_comptes.most_common():
        ligne_courante += '%-14s%5d  ' % (mot, nombre)
        if len(ligne_courante) > 62:
            print('  ' + ligne_courante.rstrip())
            ligne_courante = ''
    if ligne_courante:
        print('  ' + ligne_courante.rstrip())
    print('')


def main():
    analyseur = argparse.ArgumentParser(
        description='Mesure les mots tout en majuscules dans un livre.')
    analyseur.add_argument('--livre', type=int, default=16)
    analyseur.add_argument('--exemples', type=int, default=8)
    analyseur.add_argument('--mot', default=None,
                           help='montrer les phrases contenant ce mot')
    analyseur.add_argument('--tous', action='store_true',
                           help='parcourir TOUS les livres (reperer ou sont'
                                ' les majuscules)')
    options = analyseur.parse_args()

    from core.epub_parser import get_chapters

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    if options.tous:
        livres = list(conn.execute('SELECT * FROM books ORDER BY id'))
    else:
        livres = list(conn.execute('SELECT * FROM books WHERE id = ?',
                                   (options.livre,)))
    conn.close()
    if not livres:
        print('aucun livre')
        return
    if options.tous:
        _tous_les_livres(livres)
        return
    livre = livres[0]

    comptes = Counter()
    normaux = Counter()
    phrases_par_mot = {}
    total_phrases = 0
    phrases_touchees = 0
    romains = Counter()

    for chapitre in get_chapters(str(BIBLIOTHEQUE / livre['filename'])):
        for phrase in _phrases(chapitre['text']):
            total_phrases += 1
            for mot in MOT_QUELCONQUE.findall(phrase):
                if MOT_MAJUSCULES.fullmatch(mot) or ROMAIN.match(mot):
                    continue
                normaux[mot.lower()] += 1
            trouves = MOT_MAJUSCULES.findall(phrase)
            if not trouves:
                continue
            phrases_touchees += 1
            for mot in trouves:
                if ROMAIN.match(mot):
                    romains[mot] += 1
                    continue
                comptes[mot] += 1
                phrases_par_mot.setdefault(mot, []).append(phrase)

    print('')
    print('=' * 78)
    print('LES MAJUSCULES — LIVRE %d : %s' % (options.livre, livre['title']))
    print('%d phrases, dont %d contiennent un mot en majuscules (%.2f %%)'
          % (total_phrases, phrases_touchees,
             100.0 * phrases_touchees / max(total_phrases, 1)))
    print('=' * 78)
    print('')
    print('  MOTS DISTINCTS (hors chiffres romains) : %d' % len(comptes))
    print('  OCCURRENCES                            : %d'
          % sum(comptes.values()))
    print('  dont CHIFFRES ROMAINS (a ne pas toucher): %d'
          % sum(romains.values()))
    print('')
    print('  --- les 25 majuscules les plus frequentes')
    for mot, nombre in comptes.most_common(25):
        print('     %-22s %5d' % (mot, nombre))
    print('')
    print('  --- L IDEE, TESTEE : le mot est-il ecrit AUSSI en minuscules ?')
    print('      mot de la langue -> minuscules ; jamais en minuscules')
    print('      -> c est un SIGLE, on n y touche pas.')
    print('')
    convertibles = sigles = 0
    for mot, nombre in comptes.most_common(30):
        en_minuscules = normaux.get(mot.lower(), 0)
        if en_minuscules:
            verdict = 'MINUSCULES'
            convertibles += 1
        else:
            verdict = 'SIGLE (garder)'
            sigles += 1
        print('      %-16s maj %4d | minuscules %5d  -> %s'
              % (mot, nombre, en_minuscules, verdict))
    print('')
    tot_conv = sum(1 for m in comptes if normaux.get(m.lower(), 0))
    tot_sig = len(comptes) - tot_conv
    occ_conv = sum(n for m, n in comptes.items() if normaux.get(m.lower(), 0))
    occ_sig = sum(comptes.values()) - occ_conv
    print('      les 30 premiers : %d convertibles, %d sigles'
          % (convertibles, sigles))
    print('      TOUT LE LIVRE : %d mots distincts convertibles (%d occurrences)'
          % (tot_conv, occ_conv))
    print('                     %d mots distincts gardes comme sigles (%d occ.)'
          % (tot_sig, occ_sig))
    print('')
    print('  --- exemples de phrases (les plus longs mots d abord)')
    for mot, _nombre in sorted(comptes.items(),
                               key=lambda x: -len(x[0]))[:options.exemples]:
        print('')
        print('     [%s]' % mot)
        print('       %s' % phrases_par_mot[mot][0][:100])
    if options.mot:
        print('')
        print('  --- phrases contenant « %s »' % options.mot)
        for phrase in phrases_par_mot.get(options.mot, [])[:options.exemples]:
            print('       %s' % phrase[:110])
    print('')


if __name__ == '__main__':
    main()
