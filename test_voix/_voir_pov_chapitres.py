# -*- coding: utf-8 -*-
"""LA CARTE DES POV : qui raconte chaque chapitre, et avec quelle voix ?

Demande de Laurent (15/10/2026). Dans *Le Trone de Fer*, chaque chapitre est
ecrit a la troisieme personne focalisee : le narrateur du chapitre EST le
personnage du chapitre (« BRAN », « CATELYN », « EDDARD »...). L'idee (topo de
Gemini) est donc de confier la NARRATION d'un chapitre a la VOIX de son
personnage, au lieu d'un narrateur unique pour tout le livre.

Cet outil est la PREMIERE etape, et il ne change RIEN au lecteur : il se
contente de MONTRER, livre par livre, ce qu'on arriverait a reconnaitre -- et
surtout ce qu'on n'arriverait PAS a reconnaitre.

OU SE TROUVE LE PERSONNAGE (mesure du 15/10/2026, sur les 15 tomes francais) :
  - tomes 01 a 09 : le PRENOM est le TITRE du chapitre (« BRAN », « EDDARD ») ;
  - tomes 10 a 12 : melange de prenoms et de SURNOMS (« LE PROPHETE », « LA
    FILLE DE LA SEICHE », « LE NOYE ») -- un surnom ne se devine pas : il
    faudra le relier a la main ;
  - tomes 13 a 15 : le titre est « Chapitre N », mais le PRENOM ouvre le TEXTE
    du chapitre (« Tyrion Il passa tout le detroit a boire. ») ;
  - tome 00 (Le Chevalier Errant) : aucun nom nulle part, et un seul POV (Dunk).

CE QU'IL FAIT : il lit les chapitres avec le VRAI parseur du lecteur
(`core/epub_parser.py`), classe chaque titre (POV par le titre / POV par le
texte / titre generique), et -- quand le livre est DEJA dans la bibliotheque --
rapproche le nom du CASTING pour dire QUELLE VOIX lirait ce chapitre.

LECTURE SEULE : aucune base modifiee, aucun moteur a allumer, rien de facture.
Le detail complet, chapitre par chapitre, est ecrit dans
`test_voix/sortie_pov_chapitres.txt` ; l'ecran n'en montre que le resume.

Usage :
  python test_voix/_voir_pov_chapitres.py                  (les tomes du dossier par defaut)
  python test_voix/_voir_pov_chapitres.py --livre 35       (un livre de la bibliotheque)
  python test_voix/_voir_pov_chapitres.py "chemin.epub"    (un fichier precis)
"""

import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

# (`core/epub_parser.py` n'est plus importe ici : c'est `modules/pov.py` qui lit
#  les chapitres, pour que la lecture soit la MEME des deux cotes.)

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
DOSSIER_PAR_DEFAUT = Path(r'D:\Livres Epub\Le Trone de Fer')
RAPPORT = Path(__file__).resolve().parent / 'sortie_pov_chapitres.txt'

# LA REGLE VIT AILLEURS, ET ELLE VIT UNE SEULE FOIS : dans `modules/pov.py`, qui
# sert A LA FOIS l'outil de controle (ici) et le point d'entree du lecteur
# (`GET /api/books/{id}/pov`, dans `main.py`). Deux copies de la regle auraient
# derive -- c'est arrive avec le decoupage des phrases.
from modules.pov import (candidat_du_titre, candidat_du_texte, carte_du_livre,
                         compte_par_nom, personnages_du_livre, rapprocher)

# (les listes de mots, la normalisation et les deux detections -- titre et
#  premiere ligne -- sont dans `modules/pov.py`)

# (les mots courants a ne pas prendre pour un prenom, la ponctuation de bord, le
#  motif des initiales et le tiret de dialogue sont dans `modules/pov.py`)


# (les fonctions de reconnaissance -- normalisation, titre, premiere ligne --
#  sont dans `modules/pov.py`)


# (le casting d'un livre et le rapprochement d'un nom de titre avec lui sont dans
#  `modules/pov.py` : `personnages_du_livre`, `rapprocher`)


def _livre_de_la_bibliotheque(conn, identifiant):
    """Le livre de la bibliotheque : (chemin, titre, voix du narrateur)."""
    ligne = conn.execute(
        'SELECT title, filename, narrator_voice FROM books WHERE id = ?',
        (identifiant,)).fetchone()
    if not ligne:
        return None
    return (BIBLIOTHEQUE / ligne['filename'], ligne['title'],
            ligne['narrator_voice'] or '(voix par defaut du menu)')


def _livres_par_fichier(conn):
    """Les livres de la bibliotheque, ranges par NOM DE FICHIER.

    C'est ce qui permet de croiser un epub du disque avec son casting : meme
    quand on balaie un dossier entier, le tome deja importe garde sa carte.
    """
    table = {}
    if conn is None:
        return table
    for ligne in conn.execute(
            'SELECT id, title, filename, narrator_voice FROM books'):
        table[ligne['filename']] = (ligne['id'], ligne['title'],
                                    ligne['narrator_voice'] or '')
    return table


# (la carte d'un livre -- une ligne par chapitre -- et le comptage par nom sont
#  dans `modules/pov.py` : `carte_du_livre`, `compte_par_nom`)


def _rapport_d_un_livre(chemin, titre, narrateur, lignes, personnes):
    """Le detail, chapitre par chapitre (va dans le fichier de rapport)."""
    sortie = []
    sortie.append('=' * 78)
    sortie.append(' FICHIER : %s' % chemin.name)
    if titre:
        sortie.append(' LIVRE   : %s' % titre)
    else:
        sortie.append(' LIVRE   : pas dans la bibliotheque (aucun casting connu)')
    sortie.append(' NARRATEUR DU LIVRE (menu du bas) : %s' % narrateur)
    sortie.append(' %d chapitres' % len(lignes))
    sortie.append('=' * 78)
    sortie.append('  idx | titre du chapitre             | source | POV propose'
                  '      | voix du casting')
    sortie.append('-' * 78)
    for ligne in lignes:
        if ligne['candidat']:
            source = ligne['source']
            personne = ligne['personnage']
            if personne:
                voix = '%s  [%s]  %d repliques' % (
                    personne['nom'], personne['voice_id'], personne['repliques'])
            else:
                voix = 'ABSENT du casting' if personnes else '(casting inconnu)'
        else:
            source = '--'
            voix = 'narrateur du livre'
        sortie.append('  %3d | %-28s | %-6s | %-18s | %s' % (
            ligne['index'], ligne['titre'][:28], source,
            ligne['candidat'] or '--', voix))

    compte = compte_par_nom(lignes)
    une_seule_fois = [nom for nom, indices in compte.items() if len(indices) == 1]
    reconnus = {nom: indices for nom, indices in compte.items()
                if len(indices) > 1}
    sans_pov = [ligne['index'] for ligne in lignes if not ligne['candidat']]

    sortie.append('-' * 78)
    sortie.append(' POV RECONNUS (par nombre de chapitres)')
    if not reconnus:
        sortie.append('     aucun')
    for nom in sorted(reconnus, key=lambda n: -len(reconnus[n])):
        indices = reconnus[nom]
        exemple = [l for l in lignes if l['candidat'] == nom][0]
        personne = exemple['personnage']
        if personne:
            suite = '-> %s  [%s]  %d repliques' % (
                personne['nom'], personne['voice_id'], personne['repliques'])
        else:
            suite = '-> ABSENT du casting' if personnes else '-> casting inconnu'
        sortie.append('     %2d chapitres : %-24s %s' % (len(indices), nom, suite))
        sortie.append('        chapitres %s%s'
                      % (', '.join(str(i) for i in indices[:24]),
                         ' ...' if len(indices) > 24 else ''))

    sortie.append('')
    sortie.append(' A VERIFIER (vus UNE SEULE fois -- souvent des faux :'
                  ' page de garde, nom d\'auteur)')
    if not une_seule_fois:
        sortie.append('     aucun')
    for nom in sorted(une_seule_fois):
        indices = compte[nom]
        exemple = [l for l in lignes if l['candidat'] == nom][0]
        sortie.append('     chapitre %d : %-20s (source %s)  debut : %s' % (
            indices[0], nom, exemple['source'], exemple['debut'][:40]))

    par_le_texte = [l for l in lignes if l['source'] == 'texte']
    sortie.append('')
    sortie.append(' POV LU DANS LE TEXTE (le nom ouvre le chapitre -- a confirmer)')
    if not par_le_texte:
        sortie.append('     aucun')
    for exemple in par_le_texte:
        sortie.append('     chapitre %d : %-18s  debut : %s'
                      % (exemple['index'], exemple['candidat'],
                         exemple['debut'][:46]))

    sortie.append('')
    sortie.append(' CHAPITRES SANS POV (la narration reste au narrateur du livre)')
    sortie.append('     %d chapitres -- voici sur quoi ils ouvrent (c\'est la'
                  ' que se cachent les surnoms et les pages de garde)'
                  % len(sans_pov))
    for exemple in lignes:
        if not exemple['candidat']:
            sortie.append('     chapitre %d : titre « %s »  debut : %s'
                          % (exemple['index'], exemple['titre'][:24],
                             exemple['debut'][:46]))
    sortie.append('')
    return sortie


def _resume_d_un_livre(chemin, titre, narrateur, lignes, personnes):
    """Trois a six lignes pour l'ecran (le detail va dans le fichier)."""
    compte = compte_par_nom(lignes)
    par_titre = len([l for l in lignes if l['source'] == 'titre'])
    par_texte = len([l for l in lignes if l['source'] == 'texte'])
    sans_pov = len([l for l in lignes if not l['candidat']])
    reconnus = sorted([n for n, i in compte.items() if len(i) > 1],
                      key=lambda n: -len(compte[n]))
    sortie = [chemin.name]
    if titre:
        sortie.append('   livre  : %s   |   narrateur du livre : %s'
                      % (titre, narrateur))
    sortie.append('   %d chapitres : %d POV reconnus (par le titre %d / par le'
                  ' texte %d), %d sans POV'
                  % (len(lignes), len(compte), par_titre, par_texte, sans_pov))
    if reconnus:
        sortie.append('   POV    : %s' % ', '.join(
            '%s (%d)' % (nom, len(compte[nom])) for nom in reconnus))
    else:
        sortie.append('   POV    : AUCUN -- ce livre ne dit pas qui raconte')
    une_seule = sorted(n for n, i in compte.items() if len(i) == 1)
    if une_seule:
        sortie.append('   a verifier (vus 1 fois) : %s' % ', '.join(une_seule))
    if personnes:
        manquants = sorted({l['candidat'] for l in lignes
                            if l['candidat'] and not l['personnage']})
        if manquants:
            sortie.append('   ABSENTS du casting : %s' % ', '.join(manquants))
    sortie.append('')
    return sortie


def main():
    args = sys.argv[1:]
    if '--aide' in args or '--help' in args or '-h' in args:
        print(__doc__)
        return 0

    conn = None
    if BASE.exists():
        conn = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
    livres = _livres_par_fichier(conn)

    # --- Ce qu'on va lire -------------------------------------------------
    cibles = []
    if '--livre' in args:
        position = args.index('--livre')
        try:
            identifiant = int(args[position + 1])
        except (IndexError, ValueError):
            print('Usage : --livre <numero du livre>')
            return 1
        trouve = _livre_de_la_bibliotheque(conn, identifiant) if conn else None
        if not trouve:
            print('Livre %d introuvable dans la base.' % identifiant)
            return 1
        cibles.append(trouve[0])
    elif args and not args[0].startswith('--'):
        cibles.append(Path(args[0]))
    else:
        if not DOSSIER_PAR_DEFAUT.exists():
            print('Dossier introuvable : %s' % DOSSIER_PAR_DEFAUT)
            print('Donne un epub en argument, ou --livre <numero>.')
            return 1
        cibles = sorted(DOSSIER_PAR_DEFAUT.glob('*.epub'))
        if not cibles:
            print('Aucun epub dans %s' % DOSSIER_PAR_DEFAUT)
            return 1

    # --- La carte ---------------------------------------------------------
    detail = []
    resume = []
    total_pov = 0
    total_chapitres = 0
    for chemin in cibles:
        info = livres.get(chemin.name)
        personnes = personnages_du_livre(conn, info[0]) if info else {}
        titre = info[1] if info else ''
        narrateur = (info[2] if info and info[2]
                     else '(voix par defaut du menu)')
        lignes = carte_du_livre(chemin, personnes)
        detail += _rapport_d_un_livre(chemin, titre, narrateur, lignes, personnes)
        resume += _resume_d_un_livre(chemin, titre, narrateur, lignes, personnes)
        total_chapitres += len(lignes)
        total_pov += len(compte_par_nom(lignes))

    entete = [
        '=' * 78,
        ' LA CARTE DES POV - NIMM ePub -- qui raconte chaque chapitre ?',
        ' (lecture seule : rien n\'est modifie, ni la base, ni le lecteur)',
        '=' * 78,
        '',
    ]
    RAPPORT.write_text('\n'.join(entete + detail), encoding='utf-8')

    for ligne in entete[:-1]:
        print(ligne)
    for ligne in resume:
        print(ligne)
    print('-' * 78)
    print(' %d chapitres lus, %d noms de POV differents.'
          % (total_chapitres, total_pov))
    print(' Detail complet, chapitre par chapitre : %s' % RAPPORT.name)
    if conn is not None:
        conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
