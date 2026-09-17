# -*- coding: utf-8 -*-
"""Controle que CHAQUE voix Kyutai attribuee existe VRAIMENT chez le moteur.

Pourquoi ce controle existe (constat de Laurent, 17/09/2026) : apres la bascule,
certaines voix Kyutai ne donnent aucun audio dans le lecteur (« erreur »).
Une voix peut etre au catalogue du lecteur ET absente du moteur : le catalogue
(`KYUTAI_VOICES`, dans modules/tts.py) est une liste ecrite a la main, alors que
le moteur, lui, ne sait lire que les empreintes presentes dans ses dossiers.

Ce script compare donc les TROIS listes :
    - les voix utilisees par les livres (base `voices`) ;
    - le catalogue du lecteur (ce que le lecteur propose) ;
    - les empreintes REELLES du moteur (ce qu'il sait lire).
et signale toute voix presente dans la base mais absente du moteur.

Lecture seule : aucun moteur a allumer, rien n'est modifie.

Usage : python test_voix/_controler_voix_kyutai.py
"""

import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _basculer_voix_neutts_vers_kyutai import identifiants_moteur  # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
TTS = RACINE / 'modules' / 'tts.py'


def catalogue_du_lecteur():
    """Les identifiants de KYUTAI_VOICES (sans dependre du reste de tts.py)."""
    source = TTS.read_text(encoding='utf-8')
    debut = source.index('KYUTAI_VOICES = [')
    fin = source.index('\n]', debut)
    return set(re.findall(r'"id":\s*"kyutai:([^"]+)"', source[debut:fin]))


def main():
    empreintes = identifiants_moteur()
    catalogue = catalogue_du_lecteur()

    connection = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    lignes = connection.execute(
        "SELECT voice_id, book_id FROM voices WHERE voice_id LIKE 'kyutai:%'"
    ).fetchall()
    connection.close()

    utilisees = {}
    for voix, book_id in lignes:
        identifiant = voix.split(':', 1)[1]
        utilisees.setdefault(identifiant, []).append(book_id)

    print('')
    print('=' * 74)
    print('CONTROLE DES VOIX KYUTAI  (base / catalogue / moteur)')
    print('=' * 74)
    print('empreintes du moteur   : %d' % len(empreintes))
    print('catalogue du lecteur   : %d' % len(catalogue))
    print('voix distinctes en base : %d  (%d personnages)'
          % (len(utilisees), len(lignes)))

    manquantes_moteur = {v: l for v, l in utilisees.items() if v not in empreintes}
    manquantes_catalogue = {v: l for v, l in utilisees.items()
                            if v not in catalogue}
    moteur_hors_catalogue = sorted(empreintes - catalogue)

    print('')
    print('-' * 74)
    print('1) VOIX DE LA BASE ABSENTES DU MOTEUR  (cause probable du silence)')
    print('-' * 74)
    if manquantes_moteur:
        total = sum(len(l) for l in manquantes_moteur.values())
        print('  %d voix, %d personnages concernes :' % (len(manquantes_moteur),
                                                         total))
        for voix, livres in sorted(manquantes_moteur.items())[:30]:
            print('    %-34s livre(s) %s' % (voix[:34],
                                             ', '.join(map(str, sorted(set(livres))))))
    else:
        print('  aucune : toutes les voix de la base existent chez le moteur.')

    print('')
    print('-' * 74)
    print('2) VOIX DE LA BASE ABSENTES DU CATALOGUE DU LECTEUR')
    print('-' * 74)
    if manquantes_catalogue:
        for voix, livres in sorted(manquantes_catalogue.items())[:20]:
            print('    %-34s livre(s) %s' % (voix[:34],
                                             ', '.join(map(str, sorted(set(livres))))))
    else:
        print('  aucune : le lecteur propose toutes les voix utilisees.')

    print('')
    print('-' * 74)
    print('3) VOIX DU MOTEUR ABSENTES DU CATALOGUE  (pistes d enrichissement)')
    print('-' * 74)
    if moteur_hors_catalogue:
        for voix in moteur_hors_catalogue:
            print('    %s' % voix)
    else:
        print('  aucune : le catalogue propose deja tout ce que le moteur a.')

    # --- 4) Les voix qui appartiennent a un AUTRE moteur -----------------
    # Elles ne liront que si CE moteur est allume : sur une machine ou seul
    # Kyutai tourne, elles affichent « erreur » dans le lecteur.
    connection = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    autres = list(connection.execute(
        "SELECT voice_id, book_id, character_name FROM voices "
        "WHERE voice_id LIKE 'xtts:%' OR voice_id LIKE 'neutts:%' "
        "ORDER BY voice_id"))
    vides = list(connection.execute(
        "SELECT book_id, COUNT(1) FROM voices "
        "WHERE voice_id IS NULL OR voice_id = '' GROUP BY book_id ORDER BY 2 DESC"))
    connection.close()

    print('')
    print('-' * 74)
    print('4) VOIX QUI DEMANDENT UN AUTRE MOTEUR  (silence si ce moteur est eteint)')
    print('-' * 74)
    if autres:
        par_livre = {}
        for voix, book_id, _personnage in autres:
            par_livre.setdefault(book_id, []).append(voix.split(':', 1)[0])
        print('  %d personnage(s) sur des voix d un autre moteur :' % len(autres))
        for book_id, familles in sorted(par_livre.items()):
            compte = {}
            for famille in familles:
                compte[famille] = compte.get(famille, 0) + 1
            print('    livre %-4s %s' % (book_id,
                                         '  '.join('%s:%d' % (f, n)
                                                   for f, n in sorted(compte.items()))))
    else:
        print('  aucun : tous les personnages lus par un moteur sont en Kyutai.')

    if vides:
        print('')
        print('  Personnages SANS voix (lus par le narrateur) : %d, surtout :'
              % sum(n for _b, n in vides))
        for book_id, nombre in vides[:6]:
            print('    livre %-4s %d' % (book_id, nombre))
    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())