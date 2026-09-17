# -*- coding: utf-8 -*-
"""Bascule les voix NEUTTS d'un livre vers leurs jumelles KYUTAI.

Décision de Laurent, 17/09/2026 : Kyutai l'emporte sur NeuTTS (« tout est propre »
sur les mêmes phrases, mêmes voix). Ce script fait l'operation INVERSE de
`_basculer_voix_kyutai_vers_neutts.py`, avec les memes garanties :

  - il VERIFIE que chaque jumelle `kyutai:<id>` existe vraiment dans le
    catalogue du lecteur (`KYUTAI_VOICES`) ET dans les empreintes du moteur
    (`kyutai_service/voix_fr`, via le nommage du service) ;
  - il REFUSE d'ecrire si une seule voix n'a pas de jumelle : on ne distribue
    jamais une voix inexistante ;
  - RAPPORT SEUL par defaut (base ouverte en lecture seule) ;
  - avec `--ecrire`, la base est COPIEE (fichier date, annonce) avant toute
    modification -- c'est le seul retour arriere.

Verrous : une voix verrouillee est basculee comme les autres (le verrou protege
du re-cast automatique, pas d'une correction de moteur) et elle le reste.

Usage :
    python test_voix/_basculer_voix_neutts_vers_kyutai.py            # rapport
    python test_voix/_basculer_voix_neutts_vers_kyutai.py --livre 34
    python test_voix/_basculer_voix_neutts_vers_kyutai.py --ecrire
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

from _rapprocher_neutts_xtts import entrees_du_catalogue  # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
EMPREINTES = RACINE / 'kyutai_service' / 'voix_fr'
COLONNE = 'voice_id'
MARQUEUR = '_enhanced.wav'


def identifiants_moteur():
    """Les voix REELLEMENT presentes chez Kyutai (d'apres le nommage du service).

    Le service retient, pour `voix_fr/`, la partie du nom avant `_enhanced.wav`
    (voir `_repertorier_voix` dans servir_kyutai.py) : on lit donc les fichiers,
    pas une liste recopiee a la main.
    """
    presents = set()
    for fichier in sorted(EMPREINTES.rglob('*.safetensors')):
        nom = fichier.name
        if MARQUEUR in nom:
            presents.add(nom.split(MARQUEUR)[0])
        elif '.wav.' in nom:
            presents.add(nom.split('.wav.')[0])
    return presents


def jumelle_de(voix, catalogue, empreintes):
    """La voix Kyutai qui remplace une voix NeuTTS, ou None si elle manque."""
    identifiant = voix.split(':', 1)[1]
    candidate = 'kyutai:' + identifiant
    if candidate in catalogue and identifiant in empreintes:
        return candidate
    return None


def main():
    analyseur = argparse.ArgumentParser(
        description="Bascule les voix NeuTTS vers leurs jumelles Kyutai.")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="ne traiter qu'un livre (numero)")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee de la base d'abord)")
    options = analyseur.parse_args()

    if not BASE.exists():
        print('ERR : base introuvable : %s' % BASE)
        return 1

    catalogue = set(entrees_du_catalogue('KYUTAI_VOICES'))
    empreintes = identifiants_moteur()
    print('')
    print('=' * 70)
    print('VOIX NEUTTS ET XTTS  ->  VOIX KYUTAI (memes extraits, moteur retenu)')
    print('=' * 70)
    print('catalogue du lecteur   : %d voix Kyutai' % len(catalogue))
    print('empreintes du moteur   : %d voix' % len(empreintes))
    print('base : %s   (%s)' % (BASE.name,
                               'ECRITURE' if options.ecrire else 'rapport seul'))

    connection = sqlite3.connect(
        'file:%s?mode=%s' % (BASE.as_posix(),
                             'rw' if options.ecrire else 'ro'), uri=True)

    requete = ("SELECT book_id, %s, locked FROM voices "
               "WHERE %s LIKE 'neutts:%%' OR %s LIKE 'xtts:%%'"
               % (COLONNE, COLONNE, COLONNE))
    if options.livre is not None:
        requete += " AND book_id = %d" % options.livre
    lignes = list(connection.execute(requete))

    if not lignes:
        print('')
        print('aucune voix NeuTTS a basculer : rien a faire.')
        connection.close()
        return 0

    par_livre = {}
    for book_id, voix, verrou in lignes:
        par_livre.setdefault(book_id, []).append((voix, verrou))

    total = 0
    verrouilles = 0
    sans_jumelle = {}
    for book_id in sorted(par_livre):
        personnages = par_livre[book_id]
        total += len(personnages)
        basculables = 0
        for voix, verrou in personnages:
            if verrou:
                verrouilles += 1
            if jumelle_de(voix, catalogue, empreintes):
                basculables += 1
            else:
                sans_jumelle.setdefault(voix, []).append(book_id)
        print('  livre %-4s : %3d personnage(s), %3d basculable(s)'
              % (book_id, len(personnages), basculables))

    print('')
    print('total : %d personnage(s) en NeuTTS, dont %d verrouille(s)'
          % (total, verrouilles))

    if sans_jumelle:
        print('')
        print('ATTENTION : %d voix NeuTTS sans jumelle Kyutai :'
              % len(sans_jumelle))
        for voix, livres in sorted(sans_jumelle.items())[:20]:
            print('    %-34s (livre %s)' % (voix, ', '.join(map(str, livres))))
        print('Ces personnages garderaient leur voix NeuTTS : le moteur NeuTTS')
        print('devrait donc encore etre allume pour eux. Ne rien ecrire avant')
        print('de savoir quoi faire de ces voix (les importer chez Kyutai ?).')
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
            for voix, _verrou in par_livre[book_id]:
                jumelle = jumelle_de(voix, catalogue, empreintes)
                if jumelle is None:
                    continue
                curseur = connection.execute(
                    "UPDATE voices SET %s = ? WHERE book_id = ? AND %s = ?"
                    % (COLONNE, COLONNE), (jumelle, book_id, voix))
                modifiees += curseur.rowcount
    connection.close()
    print('personnages bascules : %d' % modifiees)
    print('')
    print('A SAVOIR : les verrous suivent les personnages (un personnage')
    print('verrouille le reste, sur sa voix Kyutai).')
    print('RETOUR ARRIERE : recopier %s sur la base.' % sauvegarde.name)
    print('A FAIRE ENSUITE : relancer le lecteur (START.bat allume Kyutai).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
