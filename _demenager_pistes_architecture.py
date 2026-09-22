# -*- coding: utf-8 -*-
"""Demenage les pistes ouvertes de ARCHITECTURE.md vers le BACKLOG (une fois).

POURQUOI (decision de Laurent, 22/09/2026) : le document d'ARCHITECTURE decrit
l'etat ACTUEL et l'histoire des decisions ; la liste des TACHES vit dans
`BACKLOG.md`. La section « 🎬 Prochaine session — pistes ouvertes » (journal du
21/08/2026) melangeait les deux -- et une partie de son contenu etait deja
recopiee dans le BACKLOG, le reste etant perime.

Ce que fait l'outil, et RIEN d'autre : il remplace cette section (39 lignes) par
un RENVOI court qui dit ou chaque piste vit maintenant, et pourquoi quatre notes
ont ete retirees le 22/09/2026 (accord de Laurent).

Garde-fous : deux signatures de lignes sont verifiees AVANT toute ecriture (le
titre de la section et le titre de la section suivante) : l'outil refuse de
tourner sur un fichier qui a bouge, ou deux fois de suite. Aucune autre ligne
n'est touchee, et c'est PROUVE ligne par ligne.

Usage : python _demenager_pistes_architecture.py            (apercu)
        python _demenager_pistes_architecture.py --ecrire   (applique)
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent
FICHIER = RACINE / 'ARCHITECTURE.md'

DEBUT = 3366          # « ## 🎬 Prochaine session — pistes ouvertes »
FIN = 3404            # derniere ligne de la section (la 3405 est la suivante)
TITRE_DEBUT = '## 🎬 Prochaine session — pistes ouvertes'
TITRE_APRES = '## ✅ Validation terrain complète — session du 21/08/2026'

RENVOI = """## 🎬 Pistes ouvertes de la session du 21/08/2026 — déménagées

Les idées ouvertes ce soir-là **vivent maintenant dans `BACKLOG.md`**, qui est la
liste de travail : le **réglage du pitch par personnage** (« Édition du pitch par
personnage dans la fenêtre du casting »), le **regroupement des voix par pays**
(`<optgroup>`), la **surveillance des voix Edge « trop robotiques »** et le
**gard « citation ouverte »** (les tirets de dialogue coupés par un `!` ou un `?`
interne). Retirées le **22/09/2026**, avec l'accord de Laurent, parce qu'elles
n'étaient plus vraies ou plus utiles :
- l'état Git de ce soir-là (4 fichiers non commités — sans objet aujourd'hui) ;
- le compte de voix des menus (« 12 Edge + 54 Kokoro = 66 entrées » : il y en a
  **175** aujourd'hui, et la question du rangement est déjà au BACKLOG) ;
- « Nettoyage de `test_voix/` », note vague jamais traitée ;
- « ✅ Profil Nadia créé » : c'est du **déjà livré**, et ce qui compte — le
  profil — est écrit dans « Profils familiaux » (la base a **3 profils**).

*Le texte d'origine (journal du 21/08/2026) est conservé dans
`ARCHITECTURE.md.bak_avant_demenagement_20260922`.*"""


def main():
    ecrire = '--ecrire' in sys.argv
    brut = FICHIER.read_text(encoding='utf-8')
    fin_par_nl = brut.endswith('\n')
    lignes = brut.splitlines()

    # GARDE-FOU : la section est-elle bien la ou on la croit ?
    souci = None
    if len(lignes) < FIN:
        souci = 'le fichier est trop court (%d lignes)' % len(lignes)
    elif lignes[DEBUT - 1] != TITRE_DEBUT:
        souci = 'ligne %d : « %s » attendu, trouve « %s »' % (
            DEBUT, TITRE_DEBUT, lignes[DEBUT - 1][:60])
    elif lignes[FIN] != TITRE_APRES:
        souci = 'ligne %d : « %s » attendu, trouve « %s »' % (
            FIN + 1, TITRE_APRES, lignes[FIN][:60])
    if souci:
        print('REFUS : %s' % souci)
        print('        (rien n a ete ecrit -- le fichier a deja bouge ?)')
        return 2

    nouvelles = RENVOI.split('\n')
    apres = lignes[:DEBUT - 1] + nouvelles + lignes[FIN:]

    print('=' * 74)
    print(' DEMENAGEMENT des pistes ouvertes%s'
          % ('' if ecrire else '  (apercu -- rien n est ecrit)'))
    print('=' * 74)
    print('  section remplacee : lignes %d a %d (%d lignes)'
          % (DEBUT, FIN, FIN - DEBUT + 1))
    print('  renvoi ecrit      : %d lignes' % len(nouvelles))

    # LA PREUVE : rien d'autre n'a bouge, et aucune ligne de contenu ne manque.
    avant_ok = lignes[:DEBUT - 1] == apres[:DEBUT - 1]
    apres_ok = lignes[FIN:] == apres[len(apres) - len(lignes[FIN:]):]
    supprimees = FIN - DEBUT + 1
    print('')
    print('--- preuve ---')
    print('  lignes avant la section, identiques : %s'
          % ('OUI' if avant_ok else 'NON'))
    print('  lignes apres la section, identiques : %s'
          % ('OUI' if apres_ok else 'NON'))
    print('  %d lignes remplacees par %d -> fichier : %d lignes'
          % (supprimees, len(nouvelles), len(apres)))
    if not (avant_ok and apres_ok):
        print('  REFUS : la comptabilite ne tombe pas juste.')
        return 1
    if len(apres) != len(lignes) - supprimees + len(nouvelles):
        print('  REFUS : le nombre de lignes ne tombe pas juste.')
        return 1

    if not ecrire:
        print('')
        print('  Apercu seulement : ajoute --ecrire pour appliquer.')
        return 0

    copie = FICHIER.with_name(FICHIER.name + '.bak_avant_demenagement_'
                              + datetime.now().strftime('%Y%m%d_%H%M'))
    if not copie.exists():
        shutil.copy2(FICHIER, copie)
    FICHIER.write_text('\n'.join(apres) + ('\n' if fin_par_nl else ''),
                       encoding='utf-8')
    print('')
    print('  Copie datee   : %s' % copie.name)
    print('  Fichier ecrit : %s (%d lignes)' % (FICHIER.name, len(apres)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
