# -*- coding: utf-8 -*-
"""
Choix d'un livre de TEST pour l'essai d'ecoute du moteur local (14/09/2026).

Critere : un livre COURT (rapide a caster) mais avec BEAUCOUP de DIALOGUE et
plusieurs personnages -- c'est la ou l'attribution des voix se juge.

La taille du fichier n'est pas un bon critere (un epub contient les images de
couverture) : on ouvre donc chaque candidat et on compte les phrases et la
part de phrases qui portent un signe de dialogue (guillemets ou tiret).

Lancer depuis la racine : python test_voix/_choisir_livre_test.py
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
MIN_KO, MAX_KO = 80, 500      # livres courts, mais pas des plaquettes
MAX_LIVRES = 35               # nombre de candidats analyses

MARQUE = re.compile(r'[«»"]|\u2014|(^|\s)[-–]\s')

if not DOSSIER.exists():
    print('Dossier introuvable : {}'.format(DOSSIER))
    sys.exit(1)

tous = [f for f in DOSSIER.rglob('*.epub')]
candidats = [f for f in tous
             if MIN_KO * 1024 <= f.stat().st_size <= MAX_KO * 1024]
candidats.sort(key=lambda f: f.stat().st_size)
candidats = candidats[:MAX_LIVRES]

print('')
print('{} epub au total ; {} candidats entre {} et {} Ko analyses.'.format(
    len(tous), len(candidats), MIN_KO, MAX_KO))
print('')
print('{:<44} {:>6} {:>5} {:>7} {:>9}'.format(
    'titre', 'Ko', 'chap.', 'phrases', 'dialogue'))
print('-' * 78)

resultats = []
for i, f in enumerate(candidats, 1):
    try:
        chapters = get_chapters(str(f))
    except Exception:
        continue
    if not chapters:
        continue
    total = 0
    avec_dialogue = 0
    for c in chapters:
        for s in vc._split_chapter_sentences(c['text']):
            total += 1
            if MARQUE.search(s['texte']):
                avec_dialogue += 1
    if total < 200:
        continue
    part = 100.0 * avec_dialogue / total
    resultats.append((part, total, len(chapters), f))
    print('{:<44} {:>6} {:>5} {:>7} {:>8.0f}%'.format(
        f.stem[:44], round(f.stat().st_size / 1024), len(chapters), total, part), flush=True)

print('')
print('=' * 78)
print('LES MEILLEURS CANDIDATS (beaucoup de dialogue, taille raisonnable)')
print('=' * 78)
resultats.sort(key=lambda r: (-r[0], r[1]))
for part, total, nch, f in resultats[:6]:
    print('')
    print('  {}'.format(f.stem[:70]))
    print('     {} chapitres | {} phrases | {:.0f} % de phrases avec dialogue | {} Ko'.format(
        nch, total, part, round(f.stat().st_size / 1024)))
    print('     {}'.format(f))
print('')
print('Rappel : au rythme du moteur local, comptez ~1 minute pour 500 phrases.')
print('Fin du choix.')
