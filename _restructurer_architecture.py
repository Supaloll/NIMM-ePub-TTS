# -*- coding: utf-8 -*-
"""Repare la STRUCTURE des titres de ARCHITECTURE.md, et PROUVE ce qu'il fait.

POURQUOI (decision de Laurent, 22/09/2026) : « Ide-alement, ce que je voudrais,
c'est que ce document TE soit utile. Il faut qu'il soit "pratique" a lire pour
TOI. C'est un peu un journal de bord, mais qui doit t'aider dans les
recherches. » Le document sert donc de memoire technique a Cline : il faut
pouvoir le PARCOURIR (plan des titres) et le BALAYER (sommaire en tete).

CE QUI EST CASSE (mesure du 22/09/2026, 4 453 lignes) :
  - une seule section `##` -- « Profils familiaux (multi-utilisateurs) », ligne
    1512 -- avale 2 740 lignes, soit 61,5 % du fichier : 70 sujets etrangers
    (casting, mode dialogue, moteurs de voix, cache, listener...) sont imbriques
    dessous, donc le plan des titres ment ;
  - 8 sujets vraiment distincts sont ecrits en GRAS au lieu d'etre des titres ;
  - il n'y a AUCUN sommaire.

CE QUE FAIT CET OUTIL -- et RIEN D'AUTRE :
  R1. les `###` de la zone 1513-4251 passent en `##` (ce sont des sujets a part,
      pas des parties de « Profils familiaux »). Aucun titre n'est renomme :
      les autres documents renvoient aux sections par leur TITRE, donc un
      renommage casserait leurs renvois ;
  R2. les 8 sujets ecrits en gras deviennent des titres `##` (R2) ;
  R3. le renvoi « Profils familiaux » de la ligne 3002 est remis d'aplomb
      (il renvoyait « plus bas » vers une section situee... plus haut) ;
  R4. un sommaire -- et un mode d'emploi du document -- sont inseres en tete,
      sommaire CALCULE a partir des titres, donc jamais faux le jour de
      l'ecriture.

LA PREUVE : l'outil ne modifie AUCUNE ligne de contenu. Il tient la
comptabilite de chaque ligne du fichier -- inchangee, transformee (liste
exacte), remplacee (liste exacte), inseree (liste exacte) -- et refuse
d'ecrire si le compte ne tombe pas juste. C'est le meme principe que la
lecon du 21/09/2026 : un chiffre ne vaut rien sans verification.

Usage : python _restructurer_architecture.py            (apercu, n'ecrit rien)
        python _restructurer_architecture.py --ecrire   (copie datee + ecriture)
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent
FICHIER = RACINE / 'ARCHITECTURE.md'

# La zone mal rangee : tout `###` entre ces deux lignes est un sujet a part.
# La borne de debut est la ligne 1584, et pas 1513 : les cinq `###` de 1514 a
# 1575 (Rôle, Base de données, Routes API, Frontend, Migration) sont les VRAIES
# parties de « Profils familiaux (multi-utilisateurs) », qui s'arrete la.
ZONE_DEBUT = 1584
ZONE_FIN = 4251            # juste avant `## Moteur NeuTTS` (ligne 4252)

# Les sujets ecrits en gras (ligne -> titre). Verifies un par un a la lecture
# le 22/09/2026 : chacun introduit un sujet different du titre de sa section.
SUJETS_EN_GRAS = [1783, 1795, 1821, 1983, 2128, 2187, 2209, 2291]

# Le renvoi de la ligne 3002 : titre et corps reecrits (il disait « plus bas »
# alors que la section dediee est 1 500 lignes PLUS HAUT).
LIGNE_RENVOI = 3002
TITRE_RENVOI = '👨‍👩‍👧 Profils familiaux (multi-utilisateurs) — renvoi'
CORPS_RENVOI = [
    '✅ **Réalisé** — la section « Profils familiaux (multi-utilisateurs) —',
    'main.py + index.html + app.js + styles.css » est **plus haut** dans ce document.',
]

MODE_EMPLOI = [
    '**Comment se servir de ce document** — c\'est la **mémoire technique** du',
    'projet (comment chaque pièce fonctionne, et pourquoi elle est ainsi). Les',
    'tâches à faire vivent dans `BACKLOG.md`, pas ici. Pour s\'y retrouver :',
    '',
    '- **le sommaire ci-dessous suit l\'ordre du fichier** : un `##` est un sujet,',
    '  les `###` dessous en sont les parties ;',
    '- **une date entre parenthèses** marque la session où le sujet a été livré ;',
    '  les phrases sans date décrivent l\'**état actuel**, les passages datés',
    '  racontent l\'**histoire** d\'une décision — et les noms de code qui',
    '  n\'existent plus y sont écrits « ex-… » ou « les anciennes … » ;',
    '- **les identifiants du code** (fonction, route, colonne de table) sont entre',
    '  accents graves : c\'est par eux qu\'une recherche tombe juste.',
]

# La ligne du fichier apres laquelle le sommaire est insere (la phrase « Décrit
# la logique en vigueur... »), pour qu'il reste en tete de document.
LIGNE_SOMMAIRE = 3


def construire(lignes):
    """Reconstruit le document : [(genre, ligne_source|None, texte)].

    Aucune ligne de CONTENU n'est touchee : chaque ligne du fichier d'origine
    ressort soit inchangee, soit transformee en titre (R1, R2), soit remplacee
    par une ligne du meme role (R3). Le sommaire (R4) est le seul ajout.
    """
    sortie, coupees = [], 0
    for numero, ligne in enumerate(lignes, 1):
        # R3 — le renvoi « Profils familiaux » : titre + corps remis d'aplomb.
        if numero == LIGNE_RENVOI:
            sortie.append(('titre', numero, '## ' + TITRE_RENVOI))
            for k, corps in enumerate(CORPS_RENVOI):
                sortie.append(('remplacee', numero + 1 + k, corps))
            continue
        if LIGNE_RENVOI < numero <= LIGNE_RENVOI + len(CORPS_RENVOI):
            continue
        # R2 — un sujet ecrit en gras devient un titre.
        if numero in SUJETS_EN_GRAS:
            m = re.match(r'^\*\*(.+?)\*\*(.*)$', ligne)
            if not m:
                raise SystemExit('LIGNE %d : pas la forme `**titre** suite` '
                                 'attendue -> %r' % (numero, ligne[:60]))
            sortie.append(('titre', numero, '## ' + m.group(1).strip()))
            reste = m.group(2).strip()
            if reste:                       # titre et texte sur la meme ligne
                # `None` : c'est une ligne AJOUTEE, pas une ligne d'origine
                # (sinon la preuve compterait la ligne 1795 deux fois).
                sortie.append(('coupee', None, reste))
                coupees += 1
            continue
        # R1 — un `###` de la zone mal rangee est un SUJET, pas une partie.
        if ligne.startswith('### ') and ZONE_DEBUT <= numero <= ZONE_FIN:
            sortie.append(('titre', numero, '## ' + ligne[4:].strip()))
            continue
        sortie.append(('inchangee', numero, ligne))
        # R4 — le sommaire, une fois la ligne d'en-tete passee.
        if numero == LIGNE_SOMMAIRE:
            sortie.append(('inseree', None, ''))          # place pour le bloc
    return sortie, coupees


def bloc_sommaire(entrees):
    """Les lignes du sommaire, CALCULEES depuis les titres `##` du document."""
    titres = [e[2] for e in entrees
              if e[0] != 'inseree' and e[2].startswith('## ')]
    bloc = ['']
    bloc += MODE_EMPLOI
    bloc += ['', '**Sommaire**', '']
    bloc += ['- ' + t[3:].strip() for t in titres]
    return bloc, len(titres)


def rapport(entrees, lignes_avant, coupees, titres_sommaire):
    """Comptabilite ligne par ligne, et preuve qu'aucun contenu n'est perdu."""
    par_genre = {}
    for genre, _numero, _texte in entrees:
        par_genre[genre] = par_genre.get(genre, 0) + 1
    inserees = [e for e in entrees if e[0] == 'inseree']

    print('')
    print('--- comptabilite des lignes ---')
    print('  lignes AVANT            : %d' % len(lignes_avant))
    print('  lignes APRES            : %d' % len(entrees))
    print('  dont inchangees         : %d' % par_genre.get('inchangee', 0))
    print('  dont titres repares     : %d' % par_genre.get('titre', 0))
    print('  dont lignes remplacees  : %d' % par_genre.get('remplacee', 0))
    print('  dont lignes inserees    : %d' % len(inserees))
    print('  dont lignes coupees     : %d' % coupees)
    print('  (titres listes au sommaire : %d)' % titres_sommaire)

    # LA PREUVE : chaque ligne declaree inchangee est bien identique a l'original.
    fautes = [numero for genre, numero, texte in entrees
              if genre == 'inchangee' and lignes_avant[numero - 1] != texte]
    # Et chaque ligne d'origine est prise en compte une fois, et une seule.
    sources = [numero for genre, numero, _t in entrees if numero is not None]
    trous = [n for n in range(1, len(lignes_avant) + 1) if n not in sources]
    doubles = sorted({n for n in sources if sources.count(n) > 1})
    print('')
    print('--- preuve ---')
    print('  lignes inchangees differentes de l original : %s'
          % (fautes if fautes else 'AUCUNE'))
    print('  lignes d origine non traitees              : %s'
          % (trous if trous else 'AUCUNE'))
    print('  lignes d origine traitees deux fois        : %s'
          % (doubles if doubles else 'AUCUNE'))
    return fautes or trous or doubles



def main():
    ecrire = '--ecrire' in sys.argv
    brut = FICHIER.read_text(encoding='utf-8')
    fin_par_nl = brut.endswith('\n')
    lignes = brut.splitlines()

    # GARDE-FOU : cet outil n'est fait que pour le fichier D'ORIGINE, parce que
    # ses reperes sont des NUMEROS DE LIGNE. Relance sur un fichier deja
    # restructure, il abimerait les titres. Donc on verifie sa signature avant
    # de toucher a quoi que ce soit.
    signatures = {
        1512: '## Profils familiaux (multi-utilisateurs)',
        1584: '### 🎭 Distribution de voix par personnage',
        LIGNE_RENVOI: '### 👨‍👩‍👧 Profils familiaux',
    }
    for numero, debut in signatures.items():
        if not (0 < numero <= len(lignes)) \
                or not lignes[numero - 1].startswith(debut):
            print('REFUS : ce n est pas le fichier d AVANT la restructuration.')
            print('        Ligne %d attendue : « %s »' % (numero, debut))
            print('        (rien n a ete ecrit)')
            return 2

    entrees, coupees = construire(lignes)
    bloc, nb_titres = bloc_sommaire(entrees)
    # Le bloc du sommaire remplace le marqueur pose par `construire`.
    i = entrees.index(('inseree', None, ''))
    entrees[i:i + 1] = [('inseree', None, t) for t in bloc]

    print('=' * 74)
    print(' RESTRUCTURATION de ARCHITECTURE.md%s'
          % ('' if ecrire else '  (apercu -- rien n est ecrit)'))
    print('=' * 74)
    print('  R1  les `###` des lignes %d a %d deviennent `##`'
          % (ZONE_DEBUT, ZONE_FIN))
    print('  R2  les %d sujets ecrits en gras deviennent des titres'
          % len(SUJETS_EN_GRAS))
    print('  R3  le renvoi de la ligne %d est remis d aplomb' % LIGNE_RENVOI)
    print('  R4  sommaire et mode d emploi inseres en tete')

    print('')
    print('--- les titres repares (R1 et R2) ---')
    for genre, numero, texte in entrees:
        if genre == 'titre':
            avant = lignes[numero - 1].lstrip('#').strip()
            print('  L%-5d %s' % (numero, avant[:72]))
    print('')
    print('--- les lignes remplacees (R3) ---')
    for genre, numero, texte in entrees:
        if genre == 'remplacee':
            print('  L%-5d %s' % (numero, texte[:96]))
    print('')
    print('--- les 10 premieres lignes inserees (R4) ---')
    for ligne in bloc[:10]:
        print('  | ' + ligne)

    souci = rapport(entrees, lignes, coupees, nb_titres)
    if souci:
        print('')
        print('  REFUS : la comptabilite ne tombe pas juste, RIEN n est ecrit.')
        return 1

    if not ecrire:
        print('')
        print('  Apercu seulement : ajoute --ecrire pour appliquer'
              ' (avec copie datee).')
        return 0

    copie = FICHIER.with_name(FICHIER.name + '.bak_avant_audit_structure_'
                              + datetime.now().strftime('%Y%m%d_%H%M'))
    shutil.copy2(FICHIER, copie)
    FICHIER.write_text('\n'.join(e[2] for e in entrees)
                       + ('\n' if fin_par_nl else ''), encoding='utf-8')
    print('')
    print('  Copie datee   : %s' % copie.name)
    print('  Fichier ecrit : %s (%d lignes)' % (FICHIER.name, len(entrees)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
