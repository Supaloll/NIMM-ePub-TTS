# -*- coding: utf-8 -*-
"""Garde-fou de la « copie pour Claude » (01/10/2026).

Verifie, SANS rien copier, deux choses :

  1. `refus()` refuse TOUS les fichiers sensibles, meme s'ils figurent dans la
     liste : `data/config.json`, les `.env`, `references_privees.csv`, les bases,
     l'audio, les modeles, les `.bak`, `.venv`, `__pycache__`... ;
  2. `refus()` laisse passer les fichiers normaux du projet, et `nom_plat()`
     fabrique bien le nom plat (modules/tts.py -> modules__tts.py).

Lecture seule : ce test n'ecrit RIEN, et ne copie RIEN.
Usage : python test_voix/test_copie_claude.py
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(RACINE))

import _synchroniser_copie_claude as copie      # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  ->  ' + str(detail) if detail else ''))
        ECHECS += 1


# Ce qui doit etre REFUSE (raison non vide), meme si c'est dans la liste.
SENSIBLES = [
    'data/config.json',
    '.env',
    'data/.env',
    'qwen_tts_service/voix/references_privees.csv',
    'data/nimm_epub.db',
    'data/progress.sqlite',
    'pocket_tts_service/voix/Femme001.wav',
    'Extraits de voix/ma_voix.mp3',
    'qwentts_service/models/qwen-talker-0.6b-base-Q4_K_M.gguf',
    'xtts_service/modeles/modele.safetensors',
    'qwentts_service/.venv/Lib/site-packages/rien.py',
    'frontend/node_modules/truc.js',
    'modules/__pycache__/tts.cpython-314.pyc',
    'servir_qwentts_cpp.py.bak_avant_option_gpu_20261001',
    'data/tts_cache/une_phrase.wav',
]

# Ce qui doit PASSER (raison vide : None).
NORMALES = [
    'modules/tts.py',
    'MOTEURS_DE_VOIX.md',
    'frontend/app.js',
    'START.bat',
    'qwentts_service/servir_qwentts_cpp.py',
]


def main():
    print('')
    print('=' * 66)
    print(' GARDE-FOU -- copie pour Claude')
    print('=' * 66)

    print('')
    print('1) les fichiers sensibles sont TOUJOURS refuses')
    for chemin in SENSIBLES:
        raison = copie.refus(Path(chemin))
        verifier('%s' % chemin, bool(raison), 'PASSE (raison vide !)')

    print('')
    print('2) les fichiers normaux passent')
    for chemin in NORMALES:
        raison = copie.refus(Path(chemin))
        verifier('%s' % chemin, not raison, 'refuse : %s' % raison)

    print('')
    print('3) le nom plat porte le PREFIXE puis le chemin')
    prefixe, chemins = copie.lire_liste()
    verifier('la liste donne un prefixe de projet', bool(prefixe), prefixe)
    verifier('modules/tts.py -> <prefixe>__modules__tts.py',
             copie.nom_plat(Path('modules/tts.py'), prefixe)
             == '%s__modules__tts.py' % prefixe,
             copie.nom_plat(Path('modules/tts.py'), prefixe))
    verifier('main.py -> <prefixe>__main.py',
             copie.nom_plat(Path('main.py'), prefixe) == '%s__main.py' % prefixe)

    print('')
    print('4) la liste se lit et ne contient AUCUN fichier sensible')
    verifier('la liste existe et se lit', chemins is not None)
    fautifs = [str(c) for c in (chemins or []) if copie.refus(c)]
    verifier('aucun chemin de la liste n est refuse', not fautifs, fautifs)
    verifier('la liste a des fichiers', bool(chemins) and len(chemins) >= 20,
             len(chemins or []))

    print('')
    print('=' * 66)
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('=' * 66)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
