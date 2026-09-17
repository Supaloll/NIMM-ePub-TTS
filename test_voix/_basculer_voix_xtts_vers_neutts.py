# -*- coding: utf-8 -*-
"""Bascule les voix XTTS d'un livre vers leurs jumelles NeuTTS.

OBJECTIF (Laurent, 16/09/2026) : garder les MEMES voix -- meme prenom, meme
timbre -- mais les faire lire par NeuTTS, qui est STABLE, au lieu d'XTTS.

Comment c'est possible : chaque voix XTTS a une jumelle NeuTTS, parce que les
deux catalogues partagent les memes identifiants (rapprochement calcule par
`_rapprocher_neutts_xtts.py`, importe ici -- source unique, jamais recopiee) :
    xtts:10087_11650_000028-0002  ->  neutts:10087_11650_000028-0002
    xtts:cml9804                  ->  neutts:cml9804
    xtts:dp_femme001              ->  neutts:Femme001
    xtts:dp_homme1122544987       ->  neutts:Homme1122544987

SECURITE : le script fait un RAPPORT SEUL par defaut (il ne modifie rien).
Avec --ecrire, la base est d'abord COPIEE (fichier date) puis mise a jour --
et la copie est annoncee avec son chemin. Un livre deja lu garde par ailleurs
ses fichiers audio en cache (le cache est indexe par voix : rien n'est
melange).

Usage :
    python test_voix/_basculer_voix_xtts_vers_neutts.py
    python test_voix/_basculer_voix_xtts_vers_neutts.py --livre 35
    python test_voix/_basculer_voix_xtts_vers_neutts.py --ecrire
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _rapprocher_neutts_xtts import (candidats, identifiants_references)  # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'


def mapping_xtts_vers_neutts():
    """{identifiant de voix XTTS -> identifiant de la jumelle NeuTTS}."""
    table = {}
    for _dossier, identifiants in identifiants_references().items():
        for identifiant in identifiants:
            for candidat in candidats(identifiant):
                if candidat.startswith('xtts:'):
                    table[candidat] = 'neutts:' + identifiant
    return table


def colonnes(connection, table):
    return [ligne[1] for ligne in connection.execute(
        'PRAGMA table_info(%s)' % table)]


def colonne_des_voix(connection):
    """Le nom de la colonne qui porte la voix, dans la table `voices`."""
    noms = colonnes(connection, 'voices')
    for candidat in ('voice_id', 'voice', 'voix', 'voix_id'):
        if candidat in noms:
            return candidat
    raise SystemExit('ERR : aucune colonne de voix dans `voices` (%s)' % noms)


def main():
    analyseur = argparse.ArgumentParser(
        description="Bascule les voix XTTS vers leurs jumelles NeuTTS.")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="ne traiter qu'un livre (numero)")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee de la base d'abord)")
    options = analyseur.parse_args()

    if not BASE.exists():
        print('ERR : base introuvable : %s' % BASE)
        return 1

    table = mapping_xtts_vers_neutts()
    print('')
    print('=' * 70)
    print('VOIX XTTS  ->  VOIX NEUTTS (memes prenoms, moteur stable)')
    print('=' * 70)
    print('jumelles disponibles : %d voix' % len(table))
    print('base : %s   (%s)' % (BASE.name,
                               'ECRITURE' if options.ecrire else 'rapport seul'))

    connection = sqlite3.connect(
        'file:%s?mode=%s' % (BASE.as_posix(),
                             'rw' if options.ecrire else 'ro'), uri=True)
    colonne = colonne_des_voix(connection)
    print('colonne des voix : `voices.%s`' % colonne)

    requete = ("SELECT book_id, %s, COUNT(1) FROM voices "
               "WHERE %s LIKE 'xtts:%%'" % (colonne, colonne))
    if options.livre is not None:
        requete += " AND book_id = %d" % options.livre
    requete += " GROUP BY book_id, %s ORDER BY book_id, %s" % (colonne, colonne)
    lignes = list(connection.execute(requete))

    if not lignes:
        print('')
        print('aucune voix XTTS a basculer : rien a faire.')
        return 0

    par_livre = {}
    inconnues = set()
    for book_id, voix, nombre in lignes:
        par_livre.setdefault(book_id, []).append((voix, nombre))
        if voix not in table:
            inconnues.add(voix)

    total = 0
    print('')
    for book_id in sorted(par_livre):
        personnages = sum(nombre for _v, nombre in par_livre[book_id])
        total += personnages
        print('  livre %-4s : %3d personnage(s), %2d voix XTTS distincte(s)'
              % (book_id, personnages, len(par_livre[book_id])))
        for voix, nombre in sorted(par_livre[book_id]):
            print('      %-34s -> %-34s (%d)'
                  % (voix, table.get(voix, 'ABSENTE'), nombre))
    print('')
    print('total : %d personnage(s) a basculer' % total)

    if inconnues:
        print('')
        print('ATTENTION : %d voix XTTS sans jumelle NeuTTS :' % len(inconnues))
        for voix in sorted(inconnues):
            print('    %s' % voix)
        print('Ces personnages garderaient leur voix XTTS, donc un moteur a')
        print('allumer. Ne rien ecrire avant de savoir pourquoi.')
        return 2

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        return 0

    # --- Ecriture : copie datee AVANT toute modification (regle du projet) ---
    horodatage = datetime.now().strftime('%Y%m%d_%H%M')
    sauvegarde = BASE.with_name('%s.bak_avant_bascule_neutts_%s'
                                % (BASE.name, horodatage))
    shutil.copy2(str(BASE), str(sauvegarde))
    print('')
    print('copie de la base : %s' % sauvegarde.name)

    modifiees = 0
    with connection:
        for voix, jumelle in sorted(table.items()):
            requete = "UPDATE voices SET %s = ? WHERE %s = ?" % (colonne, colonne)
            if options.livre is not None:
                curseur = connection.execute(requete,
                                             (jumelle, voix, options.livre))
            else:
                curseur = connection.execute(requete, (jumelle, voix))
            modifiees += curseur.rowcount
    connection.close()
    print('personnages bascules : %d' % modifiees)
    print('')
    print('A FAIRE ENSUITE : relancer le lecteur, puis ecouter un chapitre du')
    print('livre concerne.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
