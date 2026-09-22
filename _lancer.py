# -*- coding: utf-8 -*-
"""Lance un script et affiche TOUTE sa sortie (capture par Python).

Pourquoi ce petit outil : sous PowerShell, la moindre ligne ecrite sur `stderr`
fait croire a un echec de la commande, et le message d'erreur lui-meme se perd
dans le passage. Ici, c'est Python qui capture : le code de sortie et le message
arrivent entiers.

Usage : python _lancer.py <script.py> [arguments...]
"""

import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 2:
    print('Usage : python _lancer.py <script.py> [arguments...]')
    sys.exit(2)

commande = [sys.executable, '-u', sys.argv[1]] + sys.argv[2:]
resultat = subprocess.run(commande, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', cwd=str(RACINE),
                          timeout=1800)
print('code de sortie : %d' % resultat.returncode)
print('--- sortie ---')
print(resultat.stdout)
if resultat.stderr:
    print('--- erreurs ---')
    print(resultat.stderr)
sys.exit(resultat.returncode)
