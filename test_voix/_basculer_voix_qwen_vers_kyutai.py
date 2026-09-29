# -*- coding: utf-8 -*-
"""Bascule les voix QWEN d'un livre vers leurs jumelles KYUTAI (retour arriere).

C'est le chemin INVERSE de `_basculer_voix_kyutai_vers_qwen.py` : meme extrait
source, donc meme timbre et meme prenom, mais lu par Kyutai TTS 1.6B.

Il sert a deux choses :
  - **revenir en arriere** apres un essai Qwen (l'essai du 26/09/2026 a montre
    que Qwen, phrase par phrase, tourne a x0,45 le temps reel : environ deux
    fois trop lent pour suivre la lecture) ;
  - rebasculer un livre si le moteur Qwen n'est plus allume.

Les jumelles sont lues la ou le SERVICE Kyutai les voit (sa propre fonction de
reperage, jamais une copie) : un extrait absent chez le moteur fait REFUSER
l'ecriture.

SECURITE : rapport seul par defaut (base en lecture seule). Avec --ecrire, la
base est COPIEE (fichier date, annonce) avant toute modification.

Usage :
    python test_voix/_basculer_voix_qwen_vers_kyutai.py            # rapport
    python test_voix/_basculer_voix_qwen_vers_kyutai.py --livre 28
    python test_voix/_basculer_voix_qwen_vers_kyutai.py --ecrire
"""

import argparse
import importlib.util
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(RACINE))

from modules.tts import KYUTAI_VOICES  # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
SERVICE = RACINE / 'kyutai_service' / 'servir_kyutai.py'
COLONNE = 'voice_id'


def extraits_du_moteur():
    """Les identifiants d'extraits REELLEMENT presents chez Kyutai.

    On appelle la fonction de reperage DU SERVICE (import direct, jamais une
    copie) : ce sont exactement les voix qu'il annoncera au lecteur.
    """
    spec = importlib.util.spec_from_file_location('servir_kyutai', SERVICE)
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)
    service._repertorier_voix()
    return set(service._voix_cache.keys())


def catalogue_kyutai():
    """Les voix `kyutai:` que le LECTEUR propose (lues dans modules/tts.py)."""
    return {v['id'] for v in KYUTAI_VOICES}


def jumelle_de(voix, extraits, catalogue):
    """La voix Kyutai qui remplace une voix Qwen, ou None si elle manque."""
    identifiant = voix.split(':', 1)[1]
    candidate = 'kyutai:' + identifiant
    if identifiant in extraits and candidate in catalogue:
        return candidate
    return None


def main():
    analyseur = argparse.ArgumentParser(
        description="Bascule les voix Qwen vers leurs jumelles Kyutai.")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="ne traiter qu'un livre (numero)")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee de la base d'abord)")
    options = analyseur.parse_args()

    if not BASE.exists():
        print('ERR : base introuvable : %s' % BASE)
        return 1
    if not SERVICE.exists():
        print('ERR : service Kyutai introuvable : %s' % SERVICE)
        return 1

    extraits = extraits_du_moteur()
    catalogue = catalogue_kyutai()
    print('')
    print('=' * 70)
    print('VOIX QWEN  ->  VOIX KYUTAI (memes extraits, retour arriere)')
    print('=' * 70)
    print('extraits presents chez le moteur : %d' % len(extraits))
    print('voix Kyutai proposees par le lecteur : %d' % len(catalogue))
    print('base : %s   (%s)' % (BASE.name,
                               'ECRITURE' if options.ecrire else 'rapport seul'))

    connection = sqlite3.connect(
        'file:%s?mode=%s' % (BASE.as_posix(),
                             'rw' if options.ecrire else 'ro'), uri=True)

    requete = ("SELECT book_id, %s, locked, character_name FROM voices "
               "WHERE %s LIKE 'qwen:%%'" % (COLONNE, COLONNE))
    if options.livre is not None:
        requete += " AND book_id = %d" % options.livre
    lignes = list(connection.execute(requete))

    if not lignes:
        print('')
        print('aucune voix Qwen a rebasculer : rien a faire.')
        connection.close()
        return 0

    par_livre = {}
    for book_id, voix, verrou, personnage in lignes:
        par_livre.setdefault(book_id, []).append((voix, verrou, personnage))

    titres = {r[0]: r[1] for r in connection.execute(
        "SELECT id, title FROM books")}

    total = verrouilles = 0
    sans_jumelle = {}
    print('')
    for book_id in sorted(par_livre):
        personnages = par_livre[book_id]
        total += len(personnages)
        print('  livre %-4s %-40s %3d personnage(s), %2d voix Qwen distincte(s)'
              % (book_id, str(titres.get(book_id, '?'))[:40], len(personnages),
                 len({v for v, _l, _c in personnages})))
        for voix, verrou, _personnage in sorted(personnages):
            if jumelle_de(voix, extraits, catalogue) is None:
                sans_jumelle.setdefault(voix, []).append(book_id)
            if verrou:
                verrouilles += 1

    print('')
    print('total : %d personnage(s) a rebasculer, dont %d verrouille(s)'
          % (total, verrouilles))

    if sans_jumelle:
        print('')
        print('ATTENTION : %d voix Qwen sans jumelle chez Kyutai :'
              % len(sans_jumelle))
        for voix, livres in sorted(sans_jumelle.items()):
            print('    %-34s (livre %s)' % (voix, ', '.join(map(str, livres))))
        connection.close()
        return 2

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        connection.close()
        return 0

    horodatage = datetime.now().strftime('%Y%m%d_%H%M')
    sauvegarde = BASE.with_name('%s.bak_avant_retour_kyutai_%s'
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
    print('personnages rebascules : %d' % modifiees)
    print('')
    print('A FAIRE ENSUITE : allumer le moteur Kyutai')
    print('(kyutai_service\\DEMARRER_KYUTAI.bat), qui redeviendra le moteur')
    print('en service au prochain demarrage du lecteur.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
