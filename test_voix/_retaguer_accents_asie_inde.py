# -*- coding: utf-8 -*-
"""RETAGUER les accents « hindou » et « asiatique » (19/10/2026).

POURQUOI. Laurent a demande que le drapeau aille avec l'accent note. Les voix
indiennes et japonaises/chinoises etaient toutes marquees « autre » (la valeur
« hindou » n'existait pas, et « asiatique » non plus). Maintenant que les deux
valeurs existent, on remplace « autre » par la valeur exacte, UNIQUEMENT pour
les familles dont l'identifiant ne laisse aucun doute :

    hindi_*, hf_*, hm_*        -> hindou
    jf_*, jm_*, zf_*, zm_*     -> asiatique

Tout le reste est laisse INTACT, y compris les autres « autre » (voix
portugaises, maghrebines, accents non identifies) : on ne devine pas.

SECURITE. Rapport seul par defaut. Avec `--ecrire`, copie datee de
`data/annotations_voix.json` AVANT toute ecriture, puis relecture de controle.

Usage :
    python test_voix/_retaguer_accents_asie_inde.py
    python test_voix/_retaguer_accents_asie_inde.py --ecrire
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
FICHIER = RACINE / 'data' / 'annotations_voix.json'
sys.stdout.reconfigure(encoding='utf-8')


def famille(identifiant):
    """La valeur d'accent exacte, ou None si l'identifiant ne tranche pas."""
    court = identifiant.split(':', 1)[-1]
    if court.startswith(('hindi_', 'hf_', 'hm_')):
        return 'hindou'
    if court.startswith(('jf_', 'jm_', 'zf_', 'zm_')):
        return 'asiatique'
    return None


def main():
    options = argparse.ArgumentParser(
        description='Retaguer les accents hindou/asiatique des voix evidentes.')
    options.add_argument('--ecrire', action='store_true',
                         help='applique (copie datee avant) ; sans, rapport seul')
    options = options.parse_args()

    donnees = json.loads(FICHIER.read_text(encoding='utf-8'))
    changements = []
    for identifiant, fiche in sorted(donnees.items()):
        if (fiche.get('accent') or '') != 'autre':
            continue
        cible = famille(identifiant)
        if cible:
            changements.append((identifiant, cible))

    print('Fichier : %s' % FICHIER)
    print('Entrees : %d' % len(donnees))
    print('A changer : %d' % len(changements))
    for cible in ('hindou', 'asiatique'):
        morceaux = [identifiant for identifiant, valeur in changements
                    if valeur == cible]
        print('  %-9s : %d' % (cible, len(morceaux)))
        for identifiant in morceaux:
            print('      %s' % identifiant)

    if not options.ecrire:
        print('\nRAPPORT SEUL : rien n a ete ecrit.')
        return 0
    if not changements:
        print('\nRien a changer.')
        return 0

    copie = FICHIER.with_name(
        FICHIER.name + '.bak_avant_accents_asie_inde_'
        + time.strftime('%Y%m%d_%H%M'))
    shutil.copy2(FICHIER, copie)
    print('\nCopie datee : %s' % copie.name)

    for identifiant, cible in changements:
        donnees[identifiant]['accent'] = cible
    FICHIER.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2, sort_keys=True),
        encoding='utf-8')

    relu = json.loads(FICHIER.read_text(encoding='utf-8'))
    restes = []
    for identifiant, cible in changements:
        if (relu.get(identifiant) or {}).get('accent') != cible:
            restes.append(identifiant)
    print('Relecture : %d changement(s) applique(s), %d reste(s)'
          % (len(changements) - len(restes), len(restes)))
    if restes:
        for identifiant in restes:
            print('  RESTE : %s' % identifiant)
        return 1
    print('TOUT EST OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
