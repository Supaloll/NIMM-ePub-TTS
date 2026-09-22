# -*- coding: utf-8 -*-
"""Relit un journal UTF-16 ecrit par PowerShell et en montre les lignes utiles."""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

chemin = Path(sys.argv[1])
motifs = sys.argv[2:]
for encodage in ('utf-16', 'utf-8', 'cp1252'):
    try:
        texte = chemin.read_text(encoding=encodage)
    except Exception:
        continue
    if 'LIVRE' in texte or 'phrases' in texte:
        print('[encodage lu : %s]' % encodage)
        for ligne in texte.splitlines():
            if not motifs or any(m.lower() in ligne.lower() for m in motifs):
                print(ligne)
        break
else:
    print('rien de lisible dans %s' % chemin)
