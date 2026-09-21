# -*- coding: utf-8 -*-
"""ESSAI A BLANC : ce que des regles deterministes corrigeraient -- et pourquoi
elles se trompent (a lire avant de croire un chiffre).

Deux familles de cas sont MESUREES, jamais ecrites :
  1. morceaux qui RESSEMBLENT a un beat de narration alors qu'ils sont
     attribues a un personnage ;
  2. suites de replique (« « Jesus ! Jesus ! » ») restees au narrateur.

VERDICT DU 21/09/2026, sur « Lazarille de Tormes » : les deux familles sont des
FAUX POSITIFS. L'essai a blanc donne 13 corrections, et la lecture du texte
montre que 11 d'entre elles sont des phrases de NARRATION (« Je m'approchai et
lui montrai le pain. ») et 2 des citations IMBRIQUEES dans le long discours d'un
personnage. Les appliquer aurait abime le livre.

C'est pour cela que l'outil N'ECRIT JAMAIS : il sert a mesurer, puis on LIT les
textes. La vraie correction des deux defauts entendus par Laurent venait
d'ailleurs, et elle est en place : l'apostrophe typographique reconnue, et la
citation ouverte qui garde son locuteur quand un cri se poursuit.

Usage : python _corriger_livre.py 36
"""
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage, voice_casting
from modules.decoupage import introduit_une_replique

LIVRE = int(sys.argv[1]) if len(sys.argv) > 1 else 36
BASE = RACINE / 'data' / 'nimm_epub.db'

con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
fichier, titre, drapeau = con.execute(
    'SELECT filename, title, COALESCE(decoupe_dialogue, 0) FROM books '
    'WHERE id = ?', (LIVRE,)).fetchone()
locuteurs = {(ch, idx): sp for ch, idx, sp in con.execute(
    'SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution '
    'WHERE book_id = ?', (LIVRE,))}
con.close()
if not drapeau:
    print('Livre %s en mode origine : ces correctifs ne s appliquent pas.' % LIVRE)
    sys.exit(0)

chapitres = epub_parser.get_chapters(str(RACINE / 'data' / 'library' / fichier))

corrections = []      # (chapitre, index, ancien, nouveau, raison, morceau, avant)
for ch, chapitre in enumerate(chapitres):
    morceaux = decoupage.phrases(chapitre.get('text') or '',
                                 decoupage.REGLE_DIALOGUE)
    # 1) beats de narration -> narrateur (meme regle que le pipeline).
    #    On garde l'etiquette D'ORIGINE pour le rapport.
    origine = {i: locuteurs.get((ch, i), 'narration')
               for i in range(len(morceaux))}
    phrases = [{'id': i, 'texte': m, 'locuteur': origine[i]}
               for i, m in enumerate(morceaux)]
    voice_casting._forcer_beats_en_narration(
        [{'id': i, 'texte': m} for i, m in enumerate(morceaux)], phrases)
    for p in phrases:
        if p.get('anomalie'):
            corrections.append((ch, p['id'], origine[p['id']], 'narration',
                                'beat de narration', p['texte'],
                                morceaux[p['id'] - 1] if p['id'] else ''))
    # 2) suite d'un cri reste au narrateur -> locuteur de la citation.
    for idx, morceau in enumerate(morceaux):
        if idx + 1 >= len(morceaux):
            continue
        etiquette = locuteurs.get((ch, idx))
        suivant = morceaux[idx + 1]
        etiquette_suivante = locuteurs.get((ch, idx + 1))
        if (morceau.lstrip().startswith('«')
                and etiquette not in (None, 'narration')
                and etiquette_suivante in (None, 'narration')
                and not suivant.lstrip().startswith('«')
                and len(suivant) <= voice_casting.LONGUEUR_CRI
                and not introduit_une_replique(suivant)):
            corrections.append((ch, idx + 1, etiquette_suivante, etiquette,
                                "suite d'un cri", suivant, morceau))

print('=' * 78)
print(' CORRECTIFS DETERMINISTES -- %s (livre %s)' % (titre, LIVRE))
print('=' * 78)
print('   %d correction(s) a appliquer :' % len(corrections))
for ch, idx, ancien, nouveau, raison, morceau, avant in corrections:
    print('')
    print('   ch.%d #%-4d %-20s -> %-20s (%s)'
          % (ch, idx, str(ancien)[:20], str(nouveau)[:20], raison))
    print('        AVANT : %s' % (avant or '')[:90])
    print('        ICI   : %s' % morceau[:90])

if not corrections:
    print('   Rien a signaler.')
    sys.exit(0)

print('')
print('   ESSAI A BLANC : rien n a ete ecrit, et rien NE SERA ecrit.')
print('   Ces cas sont a LIRE un par un (voir l en-tete du script) : sur ce livre')
print('   les deux familles sont des faux positifs.')
