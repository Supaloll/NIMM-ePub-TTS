# -*- coding: utf-8 -*-
"""LA CARTE DES POV : la regle et sa forme, verrouillees (15/10/2026).

Pourquoi ce test : l'AUDIT DU 15/10/2026 (Claude.AI) a montre qu'une carte qui
embarque la VOIX d'un personnage la FIGE -- changer la voix dans le casting ne
s'entendait alors dans la narration qu'apres avoir rouvert le livre, donc deux
voix pour la meme personne. La decision est donc : **la carte ne dit que QUI
raconte quel chapitre**. Ce test l'empeche de revenir en arriere, et verrouille
la reconnaissance elle-meme (titre, premiere ligne, rapprochement au casting,
alias, limite des personnages sans voix).

Rien a allumer, rien a payer, aucune base touchee : la base de travail est une
base SQLite EN MEMOIRE.

Usage : python test_voix/test_pov_carte.py
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import pov                                                  # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def egal(nom, obtenu, attendu):
    verifier(nom, obtenu == attendu, '%r au lieu de %r' % (obtenu, attendu))


def _base_demo():
    """Un casting en memoire : deux personnages, un alias, un sans-voix."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE voices (book_id INTEGER, character_name TEXT, '
                 'voice_id TEXT, pitch TEXT, rate TEXT, line_count INTEGER)')
    conn.execute('CREATE TABLE character_aliases (book_id INTEGER, '
                 'alias_name TEXT, canonical_name TEXT)')
    for nom, voix, repliques in (('Bran_Stark', 'qwen:BRAN', 300),
                                 ('Catelyn_Stark', 'qwen:CAT', 420),
                                 ('Jon', 'qwen:JON2', 12),
                                 ('Jon_Snow', 'qwen:JON', 500),
                                 ('Melisandre', '', 0)):
        conn.execute('INSERT INTO voices VALUES (1, ?, ?, "+0Hz", "+0%", ?)',
                     (nom, voix, repliques))
    conn.execute('INSERT INTO character_aliases VALUES (1, "ALAYNE", "Sansa_Stark")')
    conn.execute('INSERT INTO voices VALUES (1, "Sansa_Stark", "qwen:SANSA", '
                 '"+0Hz", "+0%", 400)')
    # Les livres (pour la PORTEE des surnoms) et la table des surnoms elle-meme,
    # creee par LA MEME fonction que le serveur (`modules/pov.py`).
    conn.execute('CREATE TABLE books (id INTEGER, saga TEXT)')
    conn.execute('INSERT INTO books VALUES (1, NULL)')
    conn.execute('INSERT INTO books VALUES (2, "Saga Test")')
    # Le livre 2 a SON casting (les tomes d'une saga partagent leur casting : c'est
    # ce qui permet a un surnom de saga de le concerner).
    conn.execute('INSERT INTO voices VALUES (2, "Catelyn_Stark", "qwen:CAT", '
                 '"+0Hz", "+0%", 420)')
    pov.creer_table_surnoms(conn)
    conn.execute('INSERT INTO pov_surnoms (portee, surnom, canonical_name, source) '
                 'VALUES (?, ?, ?, ?)', ('livre:1', 'LE PROPHETE', 'Bran_Stark', 'main'))
    conn.execute('INSERT INTO pov_surnoms (portee, surnom, canonical_name, source) '
                 'VALUES (?, ?, ?, ?)', ('saga:Saga Test', 'LE NOYE', 'Catelyn_Stark', 'main'))
    conn.execute('INSERT INTO pov_surnoms (portee, surnom, canonical_name, source) '
                 'VALUES (?, ?, ?, ?)', ('livre:1', 'INCONNU', 'Personnage_Absent', 'main'))
    return conn


def main():
    print('')
    print('1) la reconnaissance par le TITRE')
    egal('un prenom de titre est reconnu',
         pov.candidat_du_titre('BRAN'), ('BRAN', 'titre'))
    egal('un titre accentue aussi',
         pov.candidat_du_titre('Catelyn'), ('CATELYN', 'titre'))
    egal('un chapitre numerote n est pas un POV',
         pov.candidat_du_titre('Chapitre 12'), (None, None))
    egal('un prelude non plus',
         pov.candidat_du_titre('PRÉLUDE'), (None, None))
    egal('une page de personnages non plus',
         pov.candidat_du_titre('PRINCIPAUX PERSONNAGES'), (None, None))
    egal('un vrai titre de chapitre n est pas un nom de personnage',
         pov.candidat_du_titre('La Bataille sur la Verchere du Nord'), (None, None))
    egal('un SURNOM de cinq mots passe (les POV d Asha et d Arianne)',
         pov.candidat_du_titre('LA FILLE DE LA SEICHE'),
         ('LA FILLE DE LA SEICHE', 'titre'))
    egal('un SURNOM passe (a relier a la main ensuite)',
         pov.candidat_du_titre('LE PROPHETE'), ('LE PROPHETE', 'titre'))

    print('')
    print('2) la reconnaissance par la PREMIERE LIGNE du texte')
    egal('le prenom qui ouvre le chapitre',
         pov.candidat_du_texte('Tyrion Il passa tout le d\u00e9troit \u00e0 boire.'),
         ('TYRION', 'texte'))
    egal('avec un accent',
         pov.candidat_du_texte('Daenerys Elle entendait le mort'),
         ('DAENERYS', 'texte'))
    egal('la page de l auteur est ecartee',
         pov.candidat_du_texte('George R.R. Martin'), (None, None))
    egal('le dialogue en tete est ecarte',
         pov.candidat_du_texte('\u2014 Quoi ? dit-il.'), (None, None))
    egal('un prologue est ecarte',
         pov.candidat_du_texte('Prologue L\u2019odeur de l\u2019homme'), (None, None))
    egal('un mot courant en tete est ecarte',
         pov.candidat_du_texte('Ce volume est pour mes fans'), (None, None))

    print('')
    print('3) la premiere ligne, quel que soit le saut de ligne (piege du tome 13)')
    egal('un paragraphe separe par un RETOUR CHARIOT',
         pov.premiere_ligne('Tyrion\rIl passa\rla mer'), 'Tyrion')
    egal('un paragraphe separe par un saut de ligne',
         pov.premiere_ligne('\n\nTyrion\nla mer'), 'Tyrion')
    egal('les lignes vides sont sautees',
         pov.premiere_ligne('\r\n\r\n  \r\nBran'), 'Bran')

    print('')
    print('4) le rapprochement avec le CASTING')
    conn = _base_demo()
    personnes = pov.personnages_du_livre(conn, 1)
    egal('l egalite (« BRAN » = « Bran_Stark ») : son nom est un mot du titre',
         pov.rapprocher('BRAN', personnes)['nom'], 'Bran_Stark')
    egal('un alias compte (« ALAYNE » trouve Sansa)',
         pov.rapprocher('ALAYNE', personnes)['nom'], 'Sansa_Stark')
    egal('en cas d homonymie, le plus BAVARD gagne (JON -> Jon Snow)',
         pov.rapprocher('JON', personnes)['nom'], 'Jon_Snow')
    egal('un nom absent du casting ne trouve rien',
         pov.rapprocher('DAVOS', personnes), None)
    egal('la voix ET les reglages sont dans la fiche',
         (pov.rapprocher('BRAN', personnes)['voice_id'],
          pov.rapprocher('BRAN', personnes)['pitch'],
          pov.rapprocher('BRAN', personnes)['rate']),
         ('qwen:BRAN', '+0Hz', '+0%'))

    print('')
    print('5) LA CARTE NE PORTE QUE « QUI RACONTE » (decision de l audit du 15/10/2026)')
    lignes = [
        {'index': 3, 'candidat': 'BRAN', 'source': 'titre',
         'personnage': pov.rapprocher('BRAN', personnes)},
        {'index': 4, 'candidat': 'MELISANDRE', 'source': 'titre',
         'personnage': pov.rapprocher('MELISANDRE', personnes)},
        {'index': 5, 'candidat': None, 'source': None, 'personnage': None},
        {'index': 6, 'candidat': 'DAVOS', 'source': 'titre', 'personnage': None},
    ]
    carte = pov.carte_pour_api(lignes)
    egal('les chapitres reconnus ET pourvus d une voix sont dans la carte',
         sorted(carte), ['3'])
    egal('la carte ne dit que le nom et la source',
         sorted(carte['3']), ['nom', 'source'])
    verifier('aucune voix, hauteur ni vitesse dans la carte (sinon elles seraient'
             ' figees jusqu a la reouverture du livre)',
             'voice_id' not in carte['3'] and 'pitch' not in carte['3']
             and 'rate' not in carte['3'], carte['3'])
    egal('un personnage SANS voix au casting n entre pas dans la carte',
         '4' in carte, False)
    egal('un chapitre sans personnage non plus', '5' in carte, False)

    print('')
    print('6) la LIMITE est LISTEE a part (pour que le lecteur la DISE)')
    sans_voix = pov.sans_voix_pour_api(lignes)
    egal('le personnage connu mais sans voix est signale',
         sans_voix.get('4'), 'Melisandre')
    egal('le nom reconnu mais absent du casting aussi',
         sans_voix.get('6'), 'DAVOS')
    egal('un chapitre sans personnage n est pas signale', '5' in sans_voix, False)

    print('')
    print('7) LES SURNOMS de POV (table `pov_surnoms`, 15/10/2026)')
    egal('un livre SANS saga : la portee de son livre seul',
         pov.portees(conn, 1), ['livre:1'])
    egal('un livre en saga : son livre ET la saga (les tomes partagent leur casting)',
         pov.portees(conn, 2), ['livre:2', 'saga:Saga Test'])
    personnes_livre = pov.personnages_du_livre(conn, 1)
    personnes_saga = pov.personnages_du_livre(conn, 2)
    egal('un surnom du livre est lu par la carte',
         pov.rapprocher('LE PROPHETE', personnes_livre)['nom'], 'Bran_Stark')
    egal('un surnom de la SAGA ne deborde pas sur un autre livre',
         pov.rapprocher('LE NOYE', personnes_livre), None)
    egal('... mais il sert bien les livres de sa saga',
         pov.rapprocher('LE NOYE', personnes_saga)['nom'], 'Catelyn_Stark')
    egal('un surnom qui pointe sur un absent du casting est IGNORE (rien a lire)',
         pov.rapprocher('INCONNU', personnes_livre), None)
    conn.close()

    print('')
    if ECHECS == 0:
        print('TOUT EST OK')
        return 0
    print('%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 1


if __name__ == '__main__':
    sys.exit(main())
