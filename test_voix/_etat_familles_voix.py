# -*- coding: utf-8 -*-
"""Etat des familles de voix dans la base : qui lit avec quel moteur ?

Question a laquelle il repond (demande de Laurent, 17/09/2026 : « remplacer les
voix XTTS par celles de NeuTTS dans mes castings ») : reste-t-il des voix d'un
moteur qu'on veut quitter ? Et ces voix sont-elles VERROUILLEES ?

Lecture seule : ce script ne modifie jamais la base (ouverte en mode=ro).

Usage : python test_voix/_etat_familles_voix.py
        python test_voix/_etat_familles_voix.py --livre 35
"""

import argparse
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
FAMILLES = ('edge', 'kokoro', 'kyutai', 'xtts', 'neutts', 'piper', 'autre')


def colonnes(connection, table):
    return [ligne[1] for ligne in connection.execute(
        'PRAGMA table_info(%s)' % table)]


def famille(voix):
    """La famille d'un identifiant de voix (meme regle que le lecteur)."""
    if not voix:
        return 'autre'
    prefixe = voix.split(':')[0].lower() if ':' in voix else 'edge'
    return prefixe if prefixe in FAMILLES else 'autre'


def identifiants_dune_liste(source, nom_liste):
    """Les identifiants `"id": "..."` d'une liste declaree dans un source."""
    try:
        debut = source.index(nom_liste + ' = [')
    except ValueError:
        return set()
    fin = source.index('\n]', debut)
    import re
    return set(re.findall(r'"id":\s*"([^"]+)"', source[debut:fin]))


def catalogue_du_lecteur():
    """Tous les identifiants de voix que le lecteur peut proposer."""
    tts = (RACINE / 'modules' / 'tts.py').read_text(encoding='utf-8')
    lecteur = (RACINE / 'main.py').read_text(encoding='utf-8')
    trouves = set()
    for nom in ('KOKORO_VOICES', 'XTTS_VOICES', 'KYUTAI_VOICES',
                'NEUTTS_VOICES', 'PIPER_VOICES'):
        trouves |= identifiants_dune_liste(tts, nom)
    trouves |= identifiants_dune_liste(lecteur, 'FRENCH_VOICES')   # Edge
    return trouves


def colonne_verrou(connection):
    """Le nom de la colonne qui porte le verrou, s'il existe."""
    for nom in colonnes(connection, 'voices'):
        if nom.lower() in ('locked', 'lock', 'verrou', 'verrouille',
                           'figee', 'fige', 'garder', 'gardee'):
            return nom
    return None


def main():
    analyseur = argparse.ArgumentParser(
        description="Etat des familles de voix dans la base.")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="ne regarder qu'un livre (numero)")
    options = analyseur.parse_args()

    if not BASE.exists():
        print('ERR : base introuvable : %s' % BASE)
        return 1

    connection = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)

    print('')
    print('=' * 70)
    print('FAMILLES DE VOIX DANS LA BASE  --  lecture seule')
    print('=' * 70)
    print('base : %s' % BASE.name)
    print('')
    print('colonnes de `voices` : %s' % ', '.join(colonnes(connection, 'voices')))
    verrou = colonne_verrou(connection)
    print('colonne du verrou   : %s' % (verrou or 'AUCUNE TROUVEE'))
    print('colonnes de `books` : %s' % ', '.join(colonnes(connection, 'books')))

    # Titre du livre : la colonne qui ressemble le plus a un titre.
    noms_books = colonnes(connection, 'books')
    titre = next((n for n in ('title', 'titre', 'name', 'nom', 'filename',
                              'fichier') if n in noms_books), None)

    requete = 'SELECT book_id, voice_id, locked FROM voices'
    if options.livre is not None:
        requete += ' WHERE book_id = %d' % options.livre
    lignes = list(connection.execute(requete))

    titres = {}
    if titre:
        for ligne in connection.execute('SELECT id, %s FROM books' % titre):
            titres[ligne[0]] = ligne[1]
    connection.close()

    if not lignes:
        print('')
        print('aucun personnage caste (table `voices` vide).')
        return 0

    # --- Vue d'ensemble par famille ---
    global_par_famille = {}
    verrous_par_famille = {}
    par_livre = {}
    for book_id, voix, verrou in lignes:
        fam = famille(voix)
        global_par_famille[fam] = global_par_famille.get(fam, 0) + 1
        if verrou:
            verrous_par_famille[fam] = verrous_par_famille.get(fam, 0) + 1
        par_livre.setdefault(book_id, {}).setdefault(fam, []).append(voix)

    total = len(lignes)
    print('')
    print('-' * 70)
    print('VUE D ENSEMBLE  (%d personnages)' % total)
    print('-' * 70)
    for fam in FAMILLES:
        if fam in global_par_famille:
            nombre = global_par_famille[fam]
            print('  %-8s %5d personnage(s)  %5.1f %%   dont %d verrouille(s)'
                  % (fam, nombre, 100.0 * nombre / total,
                     verrous_par_famille.get(fam, 0)))
    print('  TOTAL personnages verrouilles : %d' % sum(verrous_par_famille.values()))

    # --- Detail par livre ---
    print('')
    print('-' * 70)
    print('DETAIL PAR LIVRE')
    print('-' * 70)
    for book_id in sorted(par_livre):
        familles = par_livre[book_id]
        etat = '  '.join('%s:%d' % (f, len(familles[f]))
                         for f in FAMILLES if f in familles)
        nom = titres.get(book_id) or '(sans titre)'
        if len(nom) > 38:
            nom = nom[:35] + '...'
        print('  livre %-4s %-40s %s' % (book_id, nom, etat))
        for fam in FAMILLES:
            if fam in ('xtts', 'kyutai', 'autre'):
                distinctes = sorted(set(familles.get(fam, [])))
                for voix in distinctes[:15]:
                    print('        %-34s (%d personnage(s))'
                          % (voix or '(sans voix)', familles[fam].count(voix)))
                if len(distinctes) > 15:
                    print('        ... et %d autre(s) identifiant(s) de ce type'
                          % (len(distinctes) - 15))

    # --- Sante : chaque voix attribuee existe-t-elle dans le catalogue ? ---
    lecteur = catalogue_du_lecteur()
    absentes = {}
    for book_id, voix, _verrou in lignes:
        if voix and voix not in lecteur:
            absentes.setdefault(voix, []).append(book_id)
    print('')
    print('-' * 70)
    print('SANTE DES VOIX  (catalogue du lecteur : %d voix)' % len(lecteur))
    print('-' * 70)
    if absentes:
        print('  ATTENTION : %d voix attribuee(s) absente(s) du catalogue --'
              % len(absentes))
        print('  ces personnages ne pourraient pas etre lus :')
        for voix, livres in sorted(absentes.items())[:15]:
            print('      %-34s (livre %s)' % (voix, ', '.join(map(str, livres))))
    else:
        print('  OK : toutes les voix attribuees existent dans le catalogue.')

    a_remplacer = [f for f in ('xtts', 'kyutai') if f in global_par_famille]
    print('')
    if a_remplacer:
        print('MOTEURS A QUITTER ENCORE PRESENTS : %s' % ', '.join(a_remplacer))
        for fam in a_remplacer:
            print('  %-8s -> python test_voix/_basculer_voix_%s_vers_neutts.py'
                  % (fam, fam))
    else:
        print('AUCUNE voix XTTS ni Kyutai dans les castings : la bascule est')
        print('deja faite (XTTS le 16/09/2026, Kyutai le 17/09/2026 -- voir')
        print('BACKLOG, item NeuTTS).')
    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())
