# -*- coding: utf-8 -*-
"""
Analyse un livre AVANT de lancer son casting (session du 14/09/2026) :
taille, densite de dialogue, et estimation du cout pour chaque moteur.

Lancer depuis la racine :
    python test_voix/_analyser_livre.py "D:/chemin/du/livre.epub"
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

if len(sys.argv) < 2:
    print('Usage : python test_voix/_analyser_livre.py "chemin/du/livre.epub"')
    sys.exit(1)

chemin = Path(sys.argv[1])
if not chemin.exists():
    print('Fichier introuvable : {}'.format(chemin))
    sys.exit(1)

MARQUE = re.compile(r'[«»"]|\u2014|(^|\s)[-–]\s')

print('')
print('Analyse de : {}'.format(chemin.name))
chapters = get_chapters(str(chemin))
if not chapters:
    print('  Aucun chapitre extrait : epub illisible ou structure inhabituelle.')
    sys.exit(1)

texts = [c.get('text') or '' for c in chapters]
total = 0
avec_dialogue = 0
for t in texts:
    for s in vc._split_chapter_sentences(t):
        total += 1
        if MARQUE.search(s['texte']):
            avec_dialogue += 1

print('')
print('  chapitres          : {}'.format(len(chapters)))
print('  phrases            : {:,}'.format(total).replace(',', ' '))
print('  phrases avec dialogue : {:.0f} %'.format(100.0 * avec_dialogue / max(total, 1)))
print('')
print('  ESTIMATION DU COUT (methode de l\'app, recalibree le 14/09/2026)')
for p in ('gemini', 'deepseek', 'mistral'):
    e = vc.estimate_cast_cost(texts, p)
    print('    {:<9} : {:<22} ({} appels)'.format(p, e['cost_display'], e['calls']))
print('')
print('  Rappel des couts REELS mesures le 14/09/2026 (petit livre, 557 phrases) :')
print('    gemini 0,0155 $ | deepseek 0,0101 $  -- l\'estimation encadre le reel.')
print('')
print('Fin de l\'analyse.')
