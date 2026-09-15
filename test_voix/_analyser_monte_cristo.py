# -*- coding: utf-8 -*-
"""
Analyse des versions de Monte-Cristo disponibles (session du 14/09/2026).

Objectif : savoir laquelle est la plus COMPLETE, et OU se situe le chapitre
« Haydée » (chapitre 77 de la version que Laurent a lue), pour qu'il puisse
reprendre sa lecture dans la version integrale.

Lancer depuis la racine : python test_voix/_analyser_monte_cristo.py
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

DOSSIER = Path(r'D:\Livres Epub')

# On rassemble toutes les versions presentes dans le dossier.
fichiers = []
for motif in ('*monte-cristo*.epub', '*Monte-Cristo*.epub', '*monte_cristo*.epub'):
    fichiers.extend(DOSSIER.rglob(motif))
fichiers = sorted(set(fichiers))

if not fichiers:
    print('Aucune version trouvee.')
    sys.exit(1)

print('')
print('{} version(s) trouvee(s).'.format(len(fichiers)))
print('')
print('{:<52} {:>7} {:>6} {:>8} {:>9}'.format('fichier', 'Ko', 'chap.', 'phrases', 'Haydee ?'))
print('-' * 88)

resultats = []
for f in fichiers:
    try:
        chapters = get_chapters(str(f))
    except Exception as e:
        print('{:<52}  ERREUR {}'.format(f.name[:52], str(e)[:20]))
        continue
    if not chapters:
        continue
    total = sum(len(vc._split_chapter_sentences(c['text'])) for c in chapters)
    ou_haydee = None
    for i, c in enumerate(chapters):
        if re.search(r'hayd[ée]e', c['text'], re.IGNORECASE):
            ou_haydee = i
            break
    resultats.append((total, len(chapters), f, ou_haydee))
    print('{:<52} {:>7} {:>6} {:>8} {:>9}'.format(
        f.name[:52], round(f.stat().st_size / 1024), len(chapters), total,
        ('chap. ' + str(ou_haydee + 1)) if ou_haydee is not None else 'non'))

print('')
print('=' * 88)
print('CONCLUSION')
print('=' * 88)
resultats.sort(key=lambda r: -r[0])
for total, nch, f, haydee in resultats[:5]:
    print('  {:>7} phrases, {:>3} chapitres : {}'.format(total, nch, f.name[:60]))
print('')
print('Le plus grand nombre de phrases designe la version la plus complete.')
print('Fin de l\'analyse.')
