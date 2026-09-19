# -*- coding: utf-8 -*-
"""MESURE de la VAGUE 1 : combien de phrases sont concernees, dans un vrai tome ?

Trois defauts confirmes par le test adverse du 19/09/2026 (Claude.AI), tous dans
des phrases de REPLIQUE (donc que la « 3e voie » ne protegerait pas) :

  A2/A3 : l'incise emporte la RELATIVE qui suit, alors qu'elle appartient a la
          replique.  « — C'est lui, dit Morrel, qui l'a voulu. » -> « — C'est lui »
  A4/A5 : un IMPERATIF de la liste est pris pour une incise.
          « — Parle, dis la verite, et je t'ecoute. » -> un ordre disparait
  C1    : le PARTICIPE qui suit une incise fermee reste orphelin.
          « — Merci, dit Morrel, se levant. » -> « — Merci se levant. »

Les motifs ci-dessous sont VOLONTAIREMENT simples : ce sont des ordres de
grandeur, pas des comptes exacts. Ils servent a savoir ou mettre l'effort.

Lecture seule : rien n'est modifie.

Usage : python test_voix/_mesurer_vague1_20260919.py --livre 16
"""

import argparse
import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

from modules.decoupage import phrases as _phrases                    # noqa: E402

VERBES_INCISE = (r'(?:dit|dis|dirent|r\u00e9pondit|repondit|reprit|s\u2019\u00e9cria'
                 r'|fit|ajouta|murmura|demanda|continua|poursuivit|observa'
                 r'|remarqua|r\u00e9pliqua|repliqua|cria)')
VERBES_AMBIGUS = (r'(?:dis|demande|ajoute|r\u00e9p\u00e8te|repete|r\u00e9pond|repond'
                  r'|reprend|murmure|poursuis|continue|insiste|objecte|riposte'
                  r'|r\u00e9partit|repartit|pr\u00e9cise|precise|proteste)')

CAS = [
    ('A2/A3', 'incise + RELATIVE emportee',
     re.compile(r'[,\u2014]\s*%s\s+[^,]{2,40},\s+(?:qui|dont|o\u00f9|auquel)\b'
                % VERBES_INCISE)),
    ('A4/A5', 'IMPERATIF ou PRESENT pris pour une incise',
     re.compile(r'[,\u2014]\s*%s\s+(?:le|la|les|un|une)\b'
                % VERBES_AMBIGUS)),
    ('C1', 'participe ORPHELIN apres une incise fermee',
     re.compile(r'[,\u2014]\s*%s\s+[^,]{2,40},\s+(?:se\s+\w+ant|avec un)\b'
                % VERBES_INCISE)),
]


def main():
    analyseur = argparse.ArgumentParser(
        description='Mesure la vague 1 dans un vrai tome.')
    analyseur.add_argument('--livre', type=int, default=16)
    analyseur.add_argument('--exemples', type=int, default=4)
    options = analyseur.parse_args()

    from core.epub_parser import get_chapters

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT * FROM books WHERE id = ?',
                         (options.livre,)).fetchone()
    if livre is None:
        print('livre %d introuvable' % options.livre)
        return
    locuteurs = {}
    for ligne in conn.execute(
            'SELECT chapter_index, sentence_idx, speaker FROM'
            ' speaker_attribution WHERE book_id = ?', (options.livre,)):
        locuteurs[(ligne['chapter_index'], ligne['sentence_idx'])] = \
            ligne['speaker']
    conn.close()

    total = {cle: {'toutes': 0, 'replique': 0, 'exemples': []}
             for cle, _libelle, _motif in CAS}
    phrases_total = 0

    for chapitre in get_chapters(str(BIBLIOTHEQUE / livre['filename'])):
        for idx, phrase in enumerate(_phrases(chapitre['text'])):
            phrases_total += 1
            locuteur = locuteurs.get((chapitre['index'], idx))
            for cle, libelle, motif in CAS:
                if not motif.search(phrase):
                    continue
                total[cle]['toutes'] += 1
                if locuteur and locuteur != 'narration':
                    total[cle]['replique'] += 1
                elif locuteur == 'narration':
                    continue
                if len(total[cle]['exemples']) < options.exemples:
                    total[cle]['exemples'].append(
                        (chapitre['index'], idx, phrase, locuteur))

    print('')
    print('=' * 78)
    print('VAGUE 1 — LIVRE %d : %s' % (options.livre, livre['title']))
    print('%d phrases' % phrases_total)
    print('=' * 78)
    for cle, libelle, _motif in CAS:
        d = total[cle]
        print('')
        print('  [%s] %s' % (cle, libelle))
        print('      phrases concernees (motif simple)      %6d' % d['toutes'])
        print('      dont phrases de REPLIQUE               %6d'
              % d['replique'])
        for chapitre, idx, phrase, locuteur in d['exemples']:
            print('        ch.%d ph.%d  (%s)' % (chapitre, idx, locuteur))
            print('          %s' % phrase[:100])
    print('')
    print('=' * 78)
    print('RAPPEL : ordres de grandeur (motifs simples), a confirmer par un')
    print('correctif mesure avant/apres.')
    print('=' * 78)


if __name__ == '__main__':
    main()
