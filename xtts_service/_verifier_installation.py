# -*- coding: utf-8 -*-
"""
Verifie que l'environnement XTTS v2 est utilisable, SANS rien telecharger :
Python, PyTorch + CUDA, transformers, et import de la bibliotheque coqui-tts.
Le nombre de voix de reference est compte aussi.

Usage (avec le python du moteur) :
    .venv\\Scripts\\python.exe _verifier_installation.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent

print('python       : %s' % sys.version.split()[0])

import torch                                        # noqa: E402

print('torch        : %s | cuda %s | disponible %s'
      % (torch.__version__, torch.version.cuda, torch.cuda.is_available()))
if torch.cuda.is_available():
    print('gpu          : %s (%.1f Go)'
          % (torch.cuda.get_device_name(0),
             torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)))
else:
    print('gpu          : AUCUNE -> le moteur tournera sur le processeur (lent)')

import transformers                               # noqa: E402

print('transformers : %s' % transformers.__version__)
if transformers.__version__.split('.')[0] >= '5':
    print('ATTENTION    : transformers 5.x fait planter l import de coqui-tts '
          '(isin_mps_friendly). Installer "transformers>=4.57,<5".')

import TTS                                        # noqa: E402
from TTS.api import TTS as ApiTTS                 # noqa: E402

print('coqui-tts    : import OK')

voix = sorted((ICI / 'voix_fr').rglob('*_enhanced.wav'))
print('voix         : %d extraits de reference dans %s' % (len(voix), ICI / 'voix_fr'))
if not voix:
    print('ATTENTION    : aucune voix -> lancer .venv\\Scripts\\python.exe _telecharger.py')

print('')
print('VERIFICATION OK - l\'environnement est pret (le modele, 2,1 Go, se '
      'telecharge au premier chargement s\'il n\'est pas deja en cache).')
