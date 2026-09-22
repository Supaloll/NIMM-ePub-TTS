# -*- coding: utf-8 -*-
"""Analyse de la STRUCTURE de ARCHITECTURE.md (LECTURE SEULE).

POURQUOI : la note du BACKLOG (ligne 60, 22/09/2026) dit qu'une seule section
`##` avale environ 65 % du fichier, si bien que la table des matieres ne
correspond plus au contenu. Cet outil MESURE la structure au lieu de la croire :
il liste les titres avec leur numero de ligne, la taille de chaque section et,
pour un titre de niveau 1 ou 2, le detail de ce qu'il contient dessous.

Il ne modifie RIEN et n'ecrit RIEN.

Usage : python _analyse_structure_architecture.py
        python _analyse_structure_architecture.py --taille 20
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent
FICHIER = RACINE / 'ARCHITECTURE.md'
TITRE = re.compile(r'^(#{1,6})\s+(.*?)\s*$')

# Nombre de plus grosses sections affichees.
TAILLE = 15
if '--taille' in sys.argv:
    TAILLE = int(sys.argv[sys.argv.index('--taille') + 1])


def titres(lignes):
    """Retourne la liste des titres : ligne, niveau, texte."""
    out = []
    for i, texte in enumerate(lignes, start=1):
        m = TITRE.match(texte)
        if m:
            out.append({'ligne': i, 'niveau': len(m.group(1)),
                        'titre': m.group(2)})
    return out


def taille_section(titres_, index, total_lignes):
    """Etendue d'un titre : jusqu'au prochain titre de niveau <= le sien."""
    debut = titres_[index]['ligne']
    niveau = titres_[index]['niveau']
    fin = total_lignes
    for suivant in titres_[index + 1:]:
        if suivant['niveau'] <= niveau:
            fin = suivant['ligne'] - 1
            break
    return debut, fin


def main():
    lignes = FICHIER.read_text(encoding='utf-8').splitlines()
    total_lignes = len(lignes)
    hs = titres(lignes)

    print('=' * 74)
    print(' STRUCTURE de ARCHITECTURE.md (lecture seule)')
    print('=' * 74)
    print('%s' % FICHIER.name)
    print('%d lignes, %d titres' % (total_lignes, len(hs)))
    print('')
    print('--- combien de titres par niveau ---')
    for niveau in range(1, 7):
        n = sum(1 for h in hs if h['niveau'] == niveau)
        if n:
            print('  %-8s %3d' % ('#' * niveau, n))

    # Les sections de niveau 1 et 2, de la plus grosse a la plus petite.
    print('')
    print('--- plus grosses sections (niveau 1 et 2) ---')
    grosses = []
    for i, h in enumerate(hs):
        if h['niveau'] > 2:
            continue
        debut, fin = taille_section(hs, i, total_lignes)
        nb = fin - debut + 1
        grosses.append((nb, h['niveau'], h['ligne'], h['titre']))
    grosses.sort(reverse=True)
    for nb, niveau, ligne, titre in grosses[:TAILLE]:
        print('  %6d lignes  %5.1f %%  %-4s ligne %-5d %s'
              % (nb, 100.0 * nb / total_lignes, '#' * niveau, ligne,
                 titre[:70]))

    # Les titres de niveau 3 et 4 qui vivent SOUS la plus grosse section.
    if grosses:
        nb, niveau, ligne, titre = grosses[0]
        print('')
        print('--- ce qui est imbrique sous la plus grosse section ---')
        print('  (« %s », ligne %d, %d lignes = %.1f %% du fichier)'
              % (titre, ligne, nb, 100.0 * nb / total_lignes))
        i = next(k for k, h in enumerate(hs) if h['ligne'] == ligne)
        for h in hs[i + 1:]:
            if h['niveau'] <= niveau:
                break
            if h['niveau'] == 3:
                print('    ### ligne %-5d %s' % (h['ligne'], h['titre'][:66]))

    # La table des matieres ecrite en tete du fichier, si elle existe.
    print('')
    print('--- table des matieres ecrite dans le fichier (liens internes) ---')
    liens = []
    for i, texte in enumerate(lignes, start=1):
        for m in re.finditer(r'\]\(#([^)]+)\)', texte):
            liens.append((i, m.group(1)))
    print('  %d lien(s) interne(s) trouve(s)' % len(liens))
    for ligne, cible in liens[:40]:
        print('    ligne %-5d -> #%s' % (ligne, cible))
    return 0


if __name__ == '__main__':
    sys.exit(main())
