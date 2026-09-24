# -*- coding: utf-8 -*-
"""Affiche la sortie COMPLETE d'un test node (PowerShell coupe les erreurs).

Usage : python _voir_test.py test_voix/test_filtre_age_casting.js
"""
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
script = sys.argv[1] if len(sys.argv) > 1 else 'test_voix/test_filtre_age_casting.js'
r = subprocess.run(['node', script], capture_output=True, text=True,
                   encoding='utf-8', errors='replace')
print(r.stdout)
if r.stderr:
    print('--- STDERR ---')
    print(r.stderr)
print('code de sortie :', r.returncode)
