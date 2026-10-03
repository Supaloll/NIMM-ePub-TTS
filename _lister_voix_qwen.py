# -*- coding: utf-8 -*-
"""Liste les voix QWEN annotees (genre, timbre, registre, accent, etoiles).

Sert a choisir deux voix neutres (une F, une M) pour les petits roles.
Lecture seule.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
RACINE = Path(__file__).resolve().parent

donnees = json.loads((RACINE / 'data' / 'annotations_voix.json')
                     .read_text(encoding='utf-8'))
lignes = []
for ident, fiche in donnees.items():
    if not ident.startswith('qwen:'):
        continue
    lignes.append((fiche.get('genre', '?'), fiche.get('timbre', '?'),
                   fiche.get('registre', '?'), fiche.get('accent', '?'),
                   fiche.get('debit', '?'), int(fiche.get('stars', 0) or 0),
                   fiche.get('note', '') or '', ident))

print('%d voix Qwen annotees' % len(lignes))

for genre in ('F', 'H'):
    print('')
    print('=== genre %s : candidates NEUTRES (accent/registre neutres) ===' % genre)
    neutres = [l for l in lignes
               if l[0] == genre and l[3] == 'neutre' and l[2] == 'neutre']
    neutres.sort(key=lambda x: (x[1], -x[5]))
    for g, t, r, a, d, s, note, ident in neutres:
        print('  %-3s %-8s %-9s %-7s %d*  %-32s %s'
              % (g, t, r, d, s, ident, note[:36]))
