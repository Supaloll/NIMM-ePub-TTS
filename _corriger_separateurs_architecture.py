# -*- coding: utf-8 -*-
"""Corrige les doubles separateurs `---` laisses par le regroupement (une fois).

D'ou ca vient : dans le document a plat, chaque sujet se terminait par son
propre `---` de separation (celui qui precedait le titre suivant). Le
regroupement ajoute lui aussi son separateur avant chaque partie -- d'ou deux
`---` qui se suivent (10 fois). C'est purement visuel, mais c'est laid.

Ce que fait l'outil : il remplace `---` / vide / `---` / vide par `---` / vide,
partout ou ca se produit, et il PROUVE le compte (nombre de remplacements) et
l'absence de perte (aucune autre ligne touchee).

Usage : python _corriger_separateurs_architecture.py            (apercu)
        python _corriger_separateurs_architecture.py --ecrire   (applique)
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent
FICHIER = RACINE / 'ARCHITECTURE.md'
A_CORRIGER = '---\n\n---\n\n'
CORRIGE = '---\n\n'


def main():
    ecrire = '--ecrire' in sys.argv
    brut = FICHIER.read_text(encoding='utf-8')
    nombre = brut.count(A_CORRIGER)
    apres = brut.replace(A_CORRIGER, CORRIGE)

    print('=' * 74)
    print(' SEPARATEURS `---` en double%s'
          % ('' if ecrire else '  (apercu -- rien n est ecrit)'))
    print('=' * 74)
    print('  doubles sepateurs trouves : %d' % nombre)
    print('  lignes : %d -> %d' % (brut.count('\n'), apres.count('\n')))

    # LA PREUVE : le CONTENU (les lignes non vides) est identique, et il ne
    # manque que des separateurs `---` et les lignes vides qui les suivent.
    avant_lignes = brut.splitlines()
    apres_lignes = apres.splitlines()
    sans_avant = [l for l in avant_lignes if l != '---' and l.strip()]
    sans_apres = [l for l in apres_lignes if l != '---' and l.strip()]
    nb_avant = sum(1 for l in avant_lignes if l == '---')
    nb_apres = sum(1 for l in apres_lignes if l == '---')
    meme = (sans_avant == sans_apres
            and nb_avant - nb_apres == nombre
            and len(avant_lignes) - len(apres_lignes) == 2 * nombre)
    print('  separateurs avant/apres : %d -> %d (il doit en manquer %d)'
          % (nb_avant, nb_apres, nombre))
    print('  lignes non vides, hors separateurs : %d -> %d'
          % (len(sans_avant), len(sans_apres)))
    print('  reste du document identique : %s' % ('OUI' if meme else 'NON'))
    if not meme:
        print('  REFUS : rien n est ecrit.')
        return 1
    if nombre == 0:
        print('  rien a corriger (deja fait ?)')
        return 0

    if not ecrire:
        print('')
        print('  Apercu seulement : ajoute --ecrire pour appliquer.')
        return 0

    copie = FICHIER.with_name(FICHIER.name + '.bak_avant_separateurs_'
                              + datetime.now().strftime('%Y%m%d_%H%M'))
    if not copie.exists():
        shutil.copy2(FICHIER, copie)
    FICHIER.write_text(apres, encoding='utf-8')
    print('')
    print('  Copie datee   : %s' % copie.name)
    print('  Fichier ecrit : %s' % FICHIER.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
