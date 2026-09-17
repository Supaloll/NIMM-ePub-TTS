# -*- coding: utf-8 -*-
"""Remplace les voix sans jumelle Kyutai, pour passer TOUT le casting en Kyutai.

Décision de Laurent, 17/09/2026 : les 196 personnages dont la voix existe chez
Kyutai gardent leur voix EXACTE (et sont verrouilles), et les 26 restants
recoivent une voix Kyutai **du meme genre et du meme profil**.

Le profil, justement, on l'a : les 35 voix Kyutai ne sont pas annotees, mais
elles partagent leurs EXTRAITS avec les voix XTTS/NeuTTS (memes identifiants),
et celles-la sont annotees (109 voix, `data/annotations_voix.json`). Une voix
Kyutai peut donc etre choisie sur des criteres ENTENDUS (timbre, age, debit,
registre), et non au hasard.

Ce que le script ne fait PAS : toucher aux voix deja valables (Kokoro, Edge,
Piper) ni aux verrous. Il ne traite que les `neutts:` sans jumelle.

SECURITE : rapport seul par defaut ; `--ecrire` copie la base (fichier date)
avant toute modification.

Usage :
    python test_voix/_remplacer_voix_sans_jumelle.py            # rapport
    python test_voix/_remplacer_voix_sans_jumelle.py --livre 33
    python test_voix/_remplacer_voix_sans_jumelle.py --ecrire
"""

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _rapprocher_neutts_xtts import entrees_du_catalogue  # noqa: E402
from _basculer_voix_neutts_vers_kyutai import (            # noqa: E402
    identifiants_moteur, jumelle_de)

BASE = RACINE / 'data' / 'nimm_epub.db'
ANNOTATIONS = RACINE / 'data' / 'annotations_voix.json'
COLONNE = 'voice_id'
# Les criteres d'ecoute qui decrivent un timbre (ordre d'importance).
CRITERES = ('timbre', 'age', 'debit', 'registre')


def charger_annotations():
    if not ANNOTATIONS.exists():
        return {}
    return json.loads(ANNOTATIONS.read_text(encoding='utf-8'))


def profil_de(voix, annotations):
    """Le profil d'ecoute d'une voix, en essayant son identifiant chez NeuTTS.

    Une voix Kyutai `kyutai:X` a le meme extrait que `neutts:X` : c'est donc
    l'annotation de `neutts:X` qui la decrit.
    """
    for cle in (voix, 'neutts:' + voix.split(':', 1)[1] if ':' in voix else voix):
        if cle in annotations:
            return annotations[cle]
    return None


def score(profil_source, profil_candidat):
    """Combien de criteres entendus sont communs (0 si l'un des deux manque)."""
    if not profil_source or not profil_candidat:
        return 0
    return sum(1 for critere in CRITERES
               if profil_source.get(critere)
               and profil_source.get(critere) == profil_candidat.get(critere))


def choisir(genre, profil_source, catalogue, annotations, deja_prises):
    """La meilleure voix Kyutai libre : genre impose, puis profil, puis etoiles.

    ATTENTION aux conventions : la base (personnages, fiches) ecrit **H** pour
    un homme, les catalogues de voix ecrivent **M** (c'est historique). On
    compare donc la FAMILLE ('F' ou non), comme le fait deja
    `voice_casting.py` (`DEDICATED_VOICES_F if genre == "F" else ...`).
    """
    candidats = []
    for identifiant, (_prenom, genre_voix, etoiles, _region) in catalogue.items():
        if genre and (genre_voix == "F") != (genre == "F"):
            continue
        if identifiant in deja_prises:
            continue
        candidats.append((identifiant, etoiles or 0,
                          score(profil_source, profil_de(identifiant, annotations)),
                          profil_de(identifiant, annotations)))
    if not candidats:
        return None
    candidats.sort(key=lambda c: (-c[2], -c[1], c[0]))
    return candidats[0]


def main():
    analyseur = argparse.ArgumentParser(
        description="Remplace les voix sans jumelle Kyutai (profil equivalent).")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="ne traiter qu'un livre (numero)")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee de la base d'abord)")
    options = analyseur.parse_args()

    if not BASE.exists():
        print('ERR : base introuvable : %s' % BASE)
        return 1

    catalogue = entrees_du_catalogue('KYUTAI_VOICES')
    empreintes = identifiants_moteur()
    annotations = charger_annotations()

    print('')
    print('=' * 74)
    print('VOIX SANS JUMELLE KYUTAI  ->  VOIX KYUTAI EQUIVALENTE')
    print('=' * 74)
    print('voix Kyutai au catalogue : %d' % len(catalogue))
    print('profils d ecoute connus  : %d' % len(annotations))
    print('base : %s   (%s)' % (BASE.name,
                               'ECRITURE' if options.ecrire else 'rapport seul'))

    connection = sqlite3.connect(
        'file:%s?mode=%s' % (BASE.as_posix(),
                             'rw' if options.ecrire else 'ro'), uri=True)
    colonnes = [ligne[1] for ligne in connection.execute('PRAGMA table_info(voices)')]
    if 'genre' not in colonnes:
        print('ERR : la table `voices` n a pas de colonne `genre`.')
        connection.close()
        return 1

    requete = ("SELECT book_id, character_name, %s, genre, locked FROM voices "
               "WHERE %s LIKE 'neutts:%%' OR %s LIKE 'xtts:%%'"
               % (COLONNE, COLONNE, COLONNE))
    if options.livre is not None:
        requete += " AND book_id = %d" % options.livre
    lignes = list(connection.execute(requete))

    # Toutes les voix deja utilisees dans chaque livre (pour ne pas doubler).
    prises_par_livre = {}
    for book_id, voix in connection.execute(
            'SELECT book_id, %s FROM voices' % COLONNE):
        prises_par_livre.setdefault(book_id, set()).add(voix)

    a_remplacer = [l for l in lignes
                   if not jumelle_de(l[2], catalogue, empreintes)]
    print('')
    print('a remplacer : %d personnage(s)' % len(a_remplacer))
    if not a_remplacer:
        print('rien a faire : toutes les voix NeuTTS ont une jumelle Kyutai.')
        connection.close()
        return 0

    propositions = []
    for book_id, personnage, voix, genre, verrou in sorted(a_remplacer):
        prises = prises_par_livre.setdefault(book_id, set())
        profil = profil_de(voix, annotations)
        choix = choisir(genre, profil, catalogue, annotations, prises)
        partagee = False
        if not choix:
            # Plus aucune voix de cette famille n'est libre dans le livre (cas
            # des gros livres : 40 personnages pour 17 voix masculines Kyutai).
            # On PARTAGE alors la voix la plus proche deja utilisee dans ce
            # livre -- c'est deja ce que fait le lecteur quand le pool est
            # epuise (badge « voix partagee »).
            choix = choisir(genre, profil, catalogue, annotations, set())
            partagee = True
        if not choix:
            print('  !! aucune voix Kyutai du tout pour %s (livre %s)'
                  % (personnage, book_id))
            continue
        prises.add(choix[0])
        propositions.append((book_id, personnage, voix, choix[0], genre,
                             profil, choix[3], verrou, partagee))

    print('')
    print('-' * 74)
    print('PROPOSITIONS')
    print('-' * 74)
    livre_courant = None
    for (book_id, personnage, avant, apres, genre, avant_profil, apres_profil,
         _verrou, partagee) in propositions:
        if book_id != livre_courant:
            livre_courant = book_id
            print('')
            print('  livre %s :' % book_id)
        detail = ''
        if avant_profil and apres_profil:
            communs = [c for c in CRITERES
                       if avant_profil.get(c) == apres_profil.get(c)]
            detail = '  (meme %s)' % ', '.join(communs)
        marque = '  [VOIX PARTAGEE]' if partagee else ''
        print('     %-26s %-30s -> %-30s [%s]%s%s'
              % (personnage[:26], avant[:30], apres[:30], genre, detail, marque))

    total_partagees = sum(1 for p in propositions if p[8])
    print('')
    print('total : %d personnage(s) a remplacer, dont %d sur une voix partagee'
          % (len(propositions), total_partagees))

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        connection.close()
        return 0

    # --- Ecriture : copie datee AVANT toute modification (regle du projet) ---
    horodatage = datetime.now().strftime('%Y%m%d_%H%M')
    sauvegarde = BASE.with_name('%s.bak_avant_remplacement_voix_%s'
                                % (BASE.name, horodatage))
    shutil.copy2(str(BASE), str(sauvegarde))
    print('')
    print('copie de la base : %s' % sauvegarde.name)

    modifiees = 0
    with connection:
        for (book_id, personnage, avant, apres, _genre, _pa, _pp,
             _verrou, _partagee) in propositions:
            curseur = connection.execute(
                "UPDATE voices SET %s = ? WHERE book_id = ? AND character_name = ? "
                "AND %s = ?" % (COLONNE, COLONNE),
                (apres, book_id, personnage, avant))
            modifiees += curseur.rowcount
    connection.close()
    print('personnages remplaces : %d' % modifiees)
    print('')
    print('A FAIRE ENSUITE : basculer les voix qui ont une jumelle (script')
    print('_basculer_voix_neutts_vers_kyutai.py), puis relancer le lecteur.')
    print('RETOUR ARRIERE : recopier %s sur la base.' % sauvegarde.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
