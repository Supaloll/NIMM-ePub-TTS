# -*- coding: utf-8 -*-
"""Bascule les voix KYUTAI d'un livre vers leurs jumelles NeuTTS.

OBJECTIF (Laurent, 16 et 17/09/2026) : garder les MEMES voix -- meme extrait
source, donc meme timbre -- mais les faire lire par NeuTTS, qui est STABLE et
reproductible, au lieu de Kyutai.

POURQUOI C'EST POSSIBLE : les voix Kyutai du catalogue sont des EMPREINTES
tirees des memes extraits CML-TTS que les voix NeuTTS ; les deux moteurs
partagent donc les memes identifiants (verifie par ce script, pas suppose) :
    kyutai:10087_11650_000028-0002  ->  neutts:10087_11650_000028-0002
    kyutai:577_394_000070-0001      ->  neutts:577_394_000070-0001
Un identifiant SANS jumelle chez le moteur fait REFUSER l'ecriture : on ne
distribue jamais une voix qui n'existe pas.

VERROUS : une voix verrouillee dans le lecteur est basculee COMME LES AUTRES.
Le verrou protege contre un RE-CAST automatique (il fige la voix d'un
personnage), il n'interdit pas de corriger un moteur a la main -- c'est
precisement la demande. Le personnage reste verrouille sur sa voix NeuTTS.

SECURITE : rapport seul par defaut (la base est ouverte en lecture seule).
Avec --ecrire, la base est COPIEE (fichier date, annonce) avant toute
modification, et la copie suffit a revenir en arriere.

Usage :
    python test_voix/_basculer_voix_kyutai_vers_neutts.py           # rapport
    python test_voix/_basculer_voix_kyutai_vers_neutts.py --livre 34
    python test_voix/_basculer_voix_kyutai_vers_neutts.py --ecrire
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

from _rapprocher_neutts_xtts import (entrees_du_catalogue,  # noqa: E402
                                     identifiants_references)

BASE = RACINE / 'data' / 'nimm_epub.db'
COLONNE = 'voice_id'


def extraits_du_moteur():
    """Les identifiants d'extraits REELLEMENT presents chez le moteur.

    On demande au service (fonction importee, jamais une copie) : si un
    extrait n'est pas la, la voix `neutts:<extrait>` n'existe pas dans le
    catalogue et le personnage se retrouverait sans voix.
    """
    presents = set()
    for _dossier, identifiants in identifiants_references().items():
        presents.update(identifiants)
    return presents


def catalogue_neutts():
    """Les voix `neutts:` que le LECTEUR propose (bloc genere de tts.py)."""
    try:
        return set(entrees_du_catalogue('NEUTTS_VOICES'))
    except ValueError:
        return set()


def jumelle_de(voix, extraits, catalogue):
    """La voix NeuTTS qui remplace une voix Kyutai, ou None si elle manque."""
    identifiant = voix.split(':', 1)[1]
    candidate = 'neutts:' + identifiant
    if identifiant in extraits and candidate in catalogue:
        return candidate
    return None


def main():
    analyseur = argparse.ArgumentParser(
        description="Bascule les voix Kyutai vers leurs jumelles NeuTTS.")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="ne traiter qu'un livre (numero)")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee de la base d'abord)")
    options = analyseur.parse_args()

    if not BASE.exists():
        print('ERR : base introuvable : %s' % BASE)
        return 1

    extraits = extraits_du_moteur()
    catalogue = catalogue_neutts()
    print('')
    print('=' * 70)
    print('VOIX KYUTAI  ->  VOIX NEUTTS (memes extraits, moteur stable)')
    print('=' * 70)
    print('extraits disponibles chez le moteur : %d' % len(extraits))
    print('voix NeuTTS proposees par le lecteur : %d' % len(catalogue))
    print('base : %s   (%s)' % (BASE.name,
                               'ECRITURE' if options.ecrire else 'rapport seul'))

    connection = sqlite3.connect(
        'file:%s?mode=%s' % (BASE.as_posix(),
                             'rw' if options.ecrire else 'ro'), uri=True)

    requete = ("SELECT book_id, %s, locked, character_name FROM voices "
               "WHERE %s LIKE 'kyutai:%%'" % (COLONNE, COLONNE))
    if options.livre is not None:
        requete += " AND book_id = %d" % options.livre
    lignes = list(connection.execute(requete))

    if not lignes:
        print('')
        print('aucune voix Kyutai a basculer : rien a faire.')
        connection.close()
        return 0

    par_livre = {}
    for book_id, voix, verrou, personnage in lignes:
        par_livre.setdefault(book_id, []).append((voix, verrou, personnage))

    total = 0
    verrouilles = 0
    sans_jumelle = {}
    print('')
    for book_id in sorted(par_livre):
        personnages = par_livre[book_id]
        total += len(personnages)
        print('  livre %-4s : %3d personnage(s), %2d voix Kyutai distincte(s)'
              % (book_id, len(personnages),
                 len({v for v, _l, _c in personnages})))
        for voix, verrou, personnage in sorted(personnages):
            jumelle = jumelle_de(voix, extraits, catalogue)
            if jumelle is None:
                sans_jumelle.setdefault(voix, []).append(book_id)
            if verrou:
                verrouilles += 1

    print('')
    print('total : %d personnage(s) a basculer, dont %d verrouille(s)'
          % (total, verrouilles))

    if sans_jumelle:
        print('')
        print('ATTENTION : %d voix Kyutai sans jumelle chez le moteur :'
              % len(sans_jumelle))
        for voix, livres in sorted(sans_jumelle.items()):
            print('    %-34s (livre %s)' % (voix, ', '.join(map(str, livres))))
        print('Ces personnages garderaient leur voix Kyutai, donc un moteur a')
        print('allumer. Ne rien ecrire avant de savoir pourquoi.')
        connection.close()
        return 2

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        connection.close()
        return 0

    # --- Ecriture : copie datee AVANT toute modification (regle du projet) ---
    horodatage = datetime.now().strftime('%Y%m%d_%H%M')
    sauvegarde = BASE.with_name('%s.bak_avant_bascule_kyutai_%s'
                                % (BASE.name, horodatage))
    shutil.copy2(str(BASE), str(sauvegarde))
    print('')
    print('copie de la base : %s' % sauvegarde.name)

    modifiees = 0
    with connection:
        for book_id in sorted(par_livre):
            for voix, _verrou, _personnage in par_livre[book_id]:
                jumelle = jumelle_de(voix, extraits, catalogue)
                if jumelle is None:
                    continue
                curseur = connection.execute(
                    "UPDATE voices SET %s = ? WHERE book_id = ? AND %s = ?"
                    % (COLONNE, COLONNE), (jumelle, book_id, voix))
                modifiees += curseur.rowcount
    connection.close()
    print('personnages bascules : %d' % modifiees)
    print('')
    print('A SAVOIR : les voix restent VERROUILLEES comme avant (le verrou')
    print('suit le personnage, pas le moteur).')
    print('A FAIRE ENSUITE : relancer le lecteur, puis ecouter un chapitre')
    print('d un livre concerne (par exemple Notre-Dame de Paris, livre 34).')
    print('RETOUR ARRIERE : recopier %s sur la base.' % sauvegarde.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
