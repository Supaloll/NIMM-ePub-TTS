# -*- coding: utf-8 -*-
"""Extrait les ITEMS OUVERTS de BACKLOG.md dans BACKLOG_ouvert.md.

Option demandee par Claude.AI (01/10/2026) : un BACKLOG reduit a ce qui RESTE,
pour l'ajouter a la « copie pour Claude » sans le poids de l'historique livre.

Ce qui est retire : tout ce qui suit le titre « ## ✅ Déjà livré » (par
convention, les items livres sont ranges a la fin du BACKLOG).

Lecture seule sur BACKLOG.md ; ecrit seulement BACKLOG_ouvert.md (racine).
Usage : python _extraire_backlog_ouvert.py
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8')

SOURCE = RACINE / 'BACKLOG.md'
DESTIN = RACINE / 'BACKLOG_ouvert.md'
MARQUE = '## ✅ Déjà livré'


def main():
    if not SOURCE.is_file():
        print('ARRET : %s est absent.' % SOURCE.name)
        return 2
    ouvertes = []
    for ligne in SOURCE.read_text(encoding='utf-8').splitlines():
        if ligne.startswith(MARQUE):
            break
        ouvertes.append(ligne)
    entete = [
        '# BACKLOG_ouvert -- NIMM ePub',
        '',
        '_Items OUVERTS seulement (la section « Déjà livré » est retiree)._',
        '_Genere par `_extraire_backlog_ouvert.py` ; ne pas editer a la main._',
        '',
        '---',
        '',
    ]
    texte = '\n'.join(entete + ouvertes).rstrip() + '\n'
    DESTIN.write_text(texte, encoding='utf-8')
    print('BACKLOG_ouvert.md ecrit : %d ligne(s), %d o (~%d Ko)'
          % (len(entete) + len(ouvertes), len(texte), int(len(texte) / 1024)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
