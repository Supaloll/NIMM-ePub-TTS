# -*- coding: utf-8 -*-
"""Bascule TOUTES les voix d'un livre vers des voix QWEN -- banc d'ecoute.

OBJECTIF (Laurent, 28/09/2026) : « je ne vois pas les voix qui sont utilisees
lors de l'ecoute. Il y a du kokoro, du Kyutai, edge... » -- pour juger le moteur
Qwen a l'oreille, il faut un chapitre ou TOUT est lu par lui : ni Pocket, ni
Kokoro, ni Edge, ni Piper ne doivent s'inviter dans l'ecoute.

CE QU'IL FAIT, personnage par personnage :
  - une voix `kyutai:X` devient sa JUMELLE `qwen:X` : meme extrait source, donc
    meme timbre et meme prenom (c'est deja ce que fait
    `_basculer_voix_kyutai_vers_qwen.py`) ;
  - une voix deja `qwen:` ne bouge pas ;
  - toute autre voix (pocket:, kokoro:, piper:, edge sans prefixe) recoit une
    voix Qwen du MEME GENRE -- F pour une femme, H pour un homme -- prise parmi
    les mieux notees a l'ecoute par Laurent, en TOURNANT d'un personnage a
    l'autre pour que tout le monde n'ait pas la meme voix ;
  - le NARRATEUR du livre suit la meme regle ; `--narrateur` permet de forcer.

SECURITE : rapport seul par defaut (base ouverte en lecture seule) et livre
OBLIGATOIRE -- on ne bascule jamais toute la bibliotheque d'un coup. Avec
`--ecrire`, la base est COPIEE (fichier date, annonce) avant toute modification,
et cette copie suffit a revenir en arriere.

Usage :
    python test_voix/_basculer_tout_en_qwen.py --livre 37
    python test_voix/_basculer_tout_en_qwen.py --livre 37 --ecrire
    python test_voix/_basculer_tout_en_qwen.py --livre 37 --narrateur qwen:1406_1028_000009-0003 --ecrire
"""

import argparse
import shutil
import sqlite3
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(RACINE))

from modules.tts import QWEN_VOICES  # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
DOSSIER_VOIX = RACINE / 'qwen_tts_service' / 'voix'
SUFFIXE = '_enhanced_reference.wav'

# Indices de genre pour le NARRATEUR, dont la voix ne dit pas toujours son genre.
INDICES_FEMME = ('femme', 'alice', 'delphine', 'ariane', 'amelie', 'denise',
                 'eloise', 'jacqueline', 'vivienne', 'siwis', 'brigitte',
                 'audrey', 'marie', 'chantal', 'genevieve', 'helene')


def sans_accent(texte):
    """Un texte affichable dans une console, sans accent."""
    return (unicodedata.normalize('NFKD', str(texte))
            .encode('ascii', 'ignore').decode('ascii'))


def extraits_du_moteur():
    """Les identifiants d'extraits REELLEMENT presents chez le moteur.

    On lit le dossier que le SERVICE scanne, pas une liste ecrite a la main :
    une voix dont l'extrait manque n'existe pas et laisserait le personnage
    muet.
    """
    presents = set()
    if DOSSIER_VOIX.is_dir():
        for fichier in DOSSIER_VOIX.glob('*.wav'):
            nom = fichier.name
            if nom.endswith(SUFFIXE):
                nom = nom[:-len(SUFFIXE)]
            presents.add(nom)
    return presents


def catalogue_qwen(extraits):
    """{identifiant de voix: fiche} pour les voix Qwen utilisables ici."""
    fiches = {}
    for voix in QWEN_VOICES:
        if voix['id'].split(':', 1)[-1] in extraits:
            fiches[voix['id']] = voix
    return fiches


def genre_du_catalogue(genre_base):
    """Le genre de la BASE (F / H) vers celui des CATALOGUES (F / M).

    La base ecrit 'F' pour une femme et 'H' pour un homme (verifie le
    28/09/2026 : 290 femmes, 981 hommes) ; les catalogues du moteur, eux,
    ecrivent 'F' et 'M'. On accepte aussi les mots ecrits en clair, pour
    resister a une saisie faite a la main.
    """
    valeur = (genre_base or '').strip().upper()
    if valeur.startswith('F'):
        return 'F'
    if valeur.startswith('H') or valeur.startswith('M'):
        return 'M'
    return 'M'


def voix_du_genre(fiches, genre):
    """Les voix Qwen du genre demande, les mieux notees d'abord."""
    liste = [f for f in fiches.values() if f.get('gender') == genre]
    liste.sort(key=lambda f: (-(f.get('stars') or 0), f['id']))
    return liste


def jumelle_kyutai(voix, fiches):
    """La voix Qwen qui remplace une voix Kyutai, ou None s'il n'y en a pas."""
    identifiant = voix.split(':', 1)[1]
    candidate = 'qwen:' + identifiant
    return candidate if candidate in fiches else None


def genre_du_narrateur(voix):
    """F ou M pour le narrateur, deduit de son nom ; None s'il est deja Qwen."""
    if (voix or '').lower().startswith('qwen:'):
        return None
    minuscule = (voix or '').lower()
    for indice in INDICES_FEMME:
        if indice in minuscule:
            return 'F'
    return 'M'


def main():
    analyseur = argparse.ArgumentParser(
        description="Bascule TOUTES les voix d'un livre vers des voix Qwen.")
    analyseur.add_argument('--livre', type=int, required=True,
                           help="le livre a traiter (numero) -- obligatoire")
    analyseur.add_argument('--narrateur', default=None,
                           help="voix `qwen:...` imposee pour le narrateur")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee de la base d'abord)")
    options = analyseur.parse_args()

    if not BASE.exists():
        print('ERR : base introuvable : %s' % BASE)
        return 1

    fiches = catalogue_qwen(extraits_du_moteur())
    print('')
    print('=' * 72)
    print('TOUT UN LIVRE EN QWEN -- banc d\'ecoute, un seul moteur a l\'oreille')
    print('=' * 72)
    print('voix Qwen utilisables : %d' % len(fiches))
    print('base : %s   (%s)' % (BASE.name,
                               'ECRITURE' if options.ecrire else 'rapport seul'))

    connection = sqlite3.connect(
        'file:%s?mode=%s' % (BASE.as_posix(),
                             'rw' if options.ecrire else 'ro'), uri=True)
    entete = connection.execute(
        'SELECT title, narrator_voice FROM books WHERE id = ?',
        (options.livre,)).fetchone()
    if entete is None:
        print('ERR : le livre %d n\'existe pas.' % options.livre)
        connection.close()
        return 1
    titre_livre, narrateur = entete

    lignes = list(connection.execute(
        'SELECT character_name, voice_id, genre, locked FROM voices '
        'WHERE book_id = ? ORDER BY character_name', (options.livre,)))
    if not lignes:
        print('')
        print('aucun personnage dans ce livre : rien a faire.')
        connection.close()
        return 0

    # --- Les cibles : jumelle exacte quand elle existe, sinon voix du genre ---
    rotations = {'F': 0, 'M': 0}
    assignations = []
    for personnage, voix, genre_base, verrou in lignes:
        genre = genre_du_catalogue(genre_base)
        if voix.startswith('qwen:'):
            assignations.append((personnage, voix, voix, genre,
                                 'deja en Qwen', verrou))
            continue
        if voix.startswith('kyutai:'):
            jumelle = jumelle_kyutai(voix, fiches)
            if jumelle:
                assignations.append((personnage, voix, jumelle, genre,
                                     'jumelle exacte', verrou))
                continue
        liste = voix_du_genre(fiches, genre)
        if not liste:
            print('ERR : aucune voix Qwen de genre %s dans le moteur.' % genre)
            connection.close()
            return 1
        cible = liste[rotations[genre] % len(liste)]['id']
        rotations[genre] += 1
        assignations.append((personnage, voix, cible, genre,
                             'voix du genre', verrou))

    # --- Le narrateur : meme regle, avec priorite a l'option --narrateur -----
    if options.narrateur:
        narrateur_cible = options.narrateur
        raison_narrateur = 'impose par --narrateur'
    elif (narrateur or '').lower().startswith('qwen:'):
        narrateur_cible = narrateur
        raison_narrateur = 'deja en Qwen'
    else:
        genre_nar = genre_du_narrateur(narrateur)
        liste = voix_du_genre(fiches, genre_nar)
        if not liste:
            print('ERR : aucune voix Qwen de genre %s pour le narrateur.'
                  % genre_nar)
            connection.close()
            return 1
        narrateur_cible = liste[0]['id']
        raison_narrateur = 'voix du genre %s, la mieux notee' % genre_nar

    def lisible(identifiant):
        """La voix en clair : prenom plus identifiant."""
        fiche = fiches.get(identifiant)
        if not fiche:
            return identifiant
        return '%s %s' % (sans_accent(fiche['name']), identifiant)

    # --- Le rapport, personnage par personnage -------------------------------
    print('')
    print('livre %d : %s' % (options.livre, titre_livre))
    print('narrateur : %s' % narrateur)
    print('            -> %s   [%s]' % (lisible(narrateur_cible),
                                        raison_narrateur))
    print('')
    print('  %-30s %-30s %s' % ('personnage', 'voix actuelle', 'voix Qwen'))
    print('  ' + '-' * 96)
    changent = 0
    used = {}
    for personnage, voix, cible, _genre, raison, verrou in assignations:
        if cible != voix:
            changent += 1
        used[cible] = used.get(cible, 0) + 1
        marque = '  [verrou]' if verrou else ''
        print('  %-30s %-30s -> %s%s'
              % (sans_accent(personnage)[:30], voix[:30], lisible(cible),
                 marque))
        if raison == 'voix du genre':
            print('  %-30s %-30s    (%s)' % ('', '', raison))
    print('')
    print('personnages : %d  dont %d changent de moteur'
          % (len(assignations), changent))
    print('voix Qwen distinctes employees : %d' % len(used))
    print('  ' + ', '.join('%s x%d' % (sans_accent(fiches[v]['name'])
                                        if v in fiches else v, n)
                           for v, n in sorted(used.items(),
                                              key=lambda paire: -paire[1])))

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        connection.close()
        return 0

    # --- Ecriture : copie datee AVANT toute modification (regle du projet) ---
    horodatage = datetime.now().strftime('%Y%m%d_%H%M')
    sauvegarde = BASE.with_name('%s.bak_avant_tout_qwen_%s'
                                % (BASE.name, horodatage))
    shutil.copy2(str(BASE), str(sauvegarde))
    print('')
    print('copie de la base : %s' % sauvegarde.name)

    modifiees = 0
    with connection:
        for personnage, voix, cible, _genre, _raison, _verrou in assignations:
            if cible == voix:
                continue
            curseur = connection.execute(
                "UPDATE voices SET voice_id = ? WHERE book_id = ? "
                "AND character_name = ? AND voice_id = ?",
                (cible, options.livre, personnage, voix))
            modifiees += curseur.rowcount
        if narrateur_cible != narrateur:
            connection.execute(
                "UPDATE books SET narrator_voice = ? WHERE id = ?",
                (narrateur_cible, options.livre))
    connection.close()
    print('personnages bascules : %d' % modifiees)
    print('narrateur : %s -> %s' % (narrateur, narrateur_cible))
    print('')
    print('A SAVOIR : les verrous ne bougent pas (le verrou protege d\'un')
    print('re-cast automatique, il n\'empeche pas de changer de moteur), et les')
    print('prenoms des personnages ne changent pas -- seule la VOIX change.')
    print('A FAIRE ENSUITE : allumer le moteur Qwen, puis ecouter le chapitre.')
    print('RETOUR ARRIERE : recopier %s sur la base.' % sauvegarde.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())


