# -*- coding: utf-8 -*-
"""Combien de « ! » sont des INTERJECTIONS COURTES, et quelles abrev. collent ?

Deux questions nées de l'ecoute du banc du 18/09/2026 :

1. **Quelle ponctuation pour le « ! » ?** Laurent a tranche sur les phrases du
   banc : la VIRGULE gagne sur les phrases courtes (« Oh ! », « Comte ! »,
   « quel poignet ! »), le POINT reste le meilleur sur les phrases longues
   (« Cela recommence, comte ! »). D'ou une regle a deux cas, et la question du
   SEUIL : combien de phrases tombent de chaque cote, selon la longueur ?

2. **Le « mleu » du banc** : dans le tome 5, le texte contient « MlleEugénie »
   (espace manquant dans l'epub), donc la regle d'abreviation ne reconnait pas
   « Mlle » (elle exige une frontiere de mot apres) et le moteur lit « mleu ».
   Combien de cas de ce genre dans les livres ?

Lecture seule, aucun moteur necessaire.

Usage :
    python test_voix/_mesurer_exclamations.py --livre 16
"""

import argparse
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.decoupage import phrases as _phrases                    # noqa: E402

# Les abrev. de civilite suivies d'une MAJUSCULE, avec ou sans espace entre les
# deux (« MlleEugénie » = espace manquant dans l'epub). Le repr() du texte
# montre les caracteres EXACTS (espace insecable fine, etc.).
COLLEES = re.compile(
    r'(?:MM|Mmes|Mme|Mlles|Mlle|Mgr|Dr|Pr|St|Ste)\b[ \u00a0\u202f]*(?=[A-ZÀ-ÖØ-Ý])')

SEUILS = (20, 25, 30, 40, 50)


def lire_phrases(livre_id):
    import sqlite3
    base = RACINE / 'data' / 'nimm_epub.db'
    conn = sqlite3.connect('file:%s?mode=ro' % base.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT * FROM books WHERE id = ?',
                         (livre_id,)).fetchone()
    conn.close()
    if livre is None:
        return None, []
    from core.epub_parser import get_chapters
    chapitres = get_chapters(str(RACINE / 'data' / 'library' / livre['filename']))
    phrases = []
    for chapitre in chapitres:
        phrases.extend(_phrases(chapitre.get('text') or ''))
    return dict(livre), phrases


def main():
    analyseur = argparse.ArgumentParser(
        description='Les interjections courtes et les abrev. collees.')
    analyseur.add_argument('--livre', type=int, default=16)
    options = analyseur.parse_args()

    livre, phrases = lire_phrases(options.livre)
    if livre is None:
        print('Livre %d introuvable.' % options.livre)
        return 1

    avec = [p for p in phrases if '!' in p]
    print('')
    print('=' * 76)
    print('%s' % livre['title'][:60])
    print('=' * 76)
    print('  %d phrases, dont %d avec un « ! » (%.1f %%)'
          % (len(phrases), len(avec), 100.0 * len(avec) / max(len(phrases), 1)))
    print('')
    print('  SI ON DIFFERENCES PAR LA LONGUEUR DE LA PHRASE :')
    print('  %6s %10s %10s %10s' % ('seuil', 'courtes', 'longues', 'part courtes'))
    for seuil in SEUILS:
        courtes = [p for p in avec if len(p) <= seuil]
        part = 100.0 * len(courtes) / max(len(avec), 1)
        print('  %6d %10d %10d %9.0f %%'
              % (seuil, len(courtes), len(avec) - len(courtes), part))
    print('')
    print('  Exemples les plus COURTS (ce sont les interjections) :')
    for p in sorted(avec, key=len)[:8]:
        print('    %-40s (%d car.)' % (p[:40], len(p)))
    print('')
    print('  Exemples les plus LONGS (vraies phrases exclamatives) :')
    for p in sorted(avec, key=len)[-3:]:
        print('    %s' % p[:100])

    print('')
    print('=' * 76)
    print('  ABREVIATIONS COLLEES A UN PRENOM (le « mleu » du banc)')
    print('=' * 76)
    total = 0
    exemples = []
    for phrase in phrases:
        for m in COLLEES.finditer(phrase):
            total += 1
            if len(exemples) < 8:
                debut = max(0, m.start() - 15)
                morceau = phrase[debut:m.end() + 22]
                exemples.append(repr(morceau))
    print('  %d cas dans ce livre.' % total)
    for exemple in exemples:
        print('    %s' % exemple)
    print('')
    print('  Ces cas sortent un « mleu » / « meu » a l oreille : le moteur ne sait')
    print('  pas que c est une civilité, faute d espace dans le texte d origine.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
