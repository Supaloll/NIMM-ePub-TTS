# -*- coding: utf-8 -*-
"""Depouille un test a l'aveugle « point final » : croise le classement de
Laurent avec la correspondance cachee.

Usage :
    python test_voix/_depouiller_point_final.py <dossier_du_test>

Le classement (donne a l'oreille) se met a jour dans les constantes ci-dessous.
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Classement de Laurent, test large du 16/09/2026.
VIVANTS = {'A03', 'A06', 'A08', 'A10', 'B01', 'B03', 'B04', 'B05', 'B07', 'B10'}
PLATS = {'A02', 'A04', 'A07', 'A09', 'B02', 'B06', 'B08', 'B09'}
# Cas particuliers signales a l'oreille (fin de phrase montante, « comme une
# interrogation ») -- ils ne comptent pas dans vivant/plat.
PARTICULIERS = {'A01', 'A04'}
SERIES = ('A', 'B')


def cle(nom_fichier):
    """`phraseA_03.wav` -> `A03`"""
    base = Path(nom_fichier).stem          # phraseA_03
    return base.replace('phrase', '').replace('_', '')


def main_depouillement():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    dossier = Path(sys.argv[1])
    corr = dossier / 'correspondance.txt'
    if not corr.is_file():
        print('Correspondance introuvable : %s' % corr)
        return 1

    tableau = {}
    for ligne in corr.read_text(encoding='utf-8').splitlines():
        if '<-' not in ligne:
            continue
        nom, variante = ligne.split('  <-  ')
        variante = 'avec' if 'AVEC' in variante else 'sans'
        tableau[cle(nom)] = (variante, cle(nom)[0])

    print('DEPOUILLEMENT DU TEST A L\'AVEUGLE — %s' % dossier.name)
    print('=' * 66)
    for variante, libelle in (('avec', 'AVEC le point final'),
                              ('sans', 'SANS le point final')):
        par_serie = {}
        for code, (var, serie) in tableau.items():
            if var != variante:
                continue
            if code not in VIVANTS and code not in PLATS:
                continue                 # cas particuliers : hors comptage
            vivant = code in VIVANTS
            compte = par_serie.setdefault(serie, [0, 0])
            compte[0 if vivant else 1] += 1
        total_vivants = sum(c[0] for c in par_serie.values())
        total_plats = sum(c[1] for c in par_serie.values())
        detail = ' | '.join(
            'serie %s : %d vivant(s) / %d plat(s)' % (s, c[0], c[1])
            for s, c in sorted(par_serie.items()))
        print('%-20s %d vivant(s), %d plat(s)   (%s)'
              % (libelle, total_vivants, total_plats, detail))

    print('')
    print('Cas particuliers signales (%s) :' % ', '.join(sorted(PARTICULIERS)))
    for code in sorted(PARTICULIERS):
        if code in tableau:
            variante, _serie = tableau[code]
            print('   %s : %s le point final' % (code, variante))
    print('')
    print('Rappel : aucune difference ne prouve rien sur 10 tirages ; c\'est la')
    print('TENDANCE entre les deux series qui parle, et la coherence entre deux')
    print('tests successifs.')
    return 0


if __name__ == '__main__':
    sys.exit(main_depouillement())
