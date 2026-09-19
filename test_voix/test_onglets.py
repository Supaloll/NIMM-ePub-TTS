# -*- coding: utf-8 -*-
"""Verifie les ONGLETS de lecture (demande de Laurent, 19/09/2026).

« j'aimerais bien pouvoir me faire une liste d'onglets » : la table `progress`
ne garde QU'UN endroit par livre (le dernier visite). Cette table en plus laisse
poser PLUSIEURS marques, par profil, chacune avec son libelle.

Usage : python test_voix/test_onglets.py
"""

import os
import sqlite3
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient                       # noqa: E402
import main                                                     # noqa: E402

BASE = os.path.join(RACINE, 'data', 'nimm_epub.db')
ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def main_test():
    client = TestClient(main.app)
    # `TestClient` n'execute PAS le « lifespan » de l'application (le demarrage
    # reel, qui cree les tables) : on l'appelle donc ici, exactement comme le
    # fait START.bat au lancement du serveur.
    main.init_db()

    print('')
    print('=' * 70)
    print('LES ONGLETS : poser une marque, la retrouver, la retirer')
    print('=' * 70)

    print('')
    print('1) la table existe')
    conn = sqlite3.connect(BASE)
    tables = [r[0] for r in conn.execute(
        "select name from sqlite_master where type='table'")]
    conn.close()
    verifier('la table bookmarks est creee', 'bookmarks' in tables)

    print('')
    print('2) poser un onglet')
    corps = {'chapter_index': 21, 'cursor_idx': 194,
             'label': 'Chapitre 22 - Il n y aurait cependant point de ma faute'}
    res = client.post('/api/bookmarks/16?user_id=1', json=corps)
    verifier('la pose repond OK', res.status_code == 200, res.status_code)
    onglet = res.json().get('bookmark') or {}
    identifiant = onglet.get('id')
    verifier('un identifiant est attribue', bool(identifiant), onglet)
    verifier('le chapitre est garde', onglet.get('chapter_index') == 21, onglet)
    verifier('la position est gardee', onglet.get('cursor_idx') == 194, onglet)
    verifier('le libelle est garde',
             'point de ma faute' in (onglet.get('label') or ''))

    print('')
    print('3) le retrouver dans la liste du livre')
    liste = client.get('/api/bookmarks/16?user_id=1').json()
    verifier('il est dans la liste',
             any(o['id'] == identifiant for o in liste), liste)

    print('')
    print('4) chaque profil a les siens')
    autres = client.get('/api/bookmarks/16?user_id=2').json()
    verifier('un autre profil ne le voit pas',
             not any(o['id'] == identifiant for o in autres), autres)

    print('')
    print('5) le retirer')
    res = client.delete('/api/bookmarks/16/%s?user_id=1' % identifiant)
    verifier('la suppression repond OK', res.status_code == 200, res.status_code)
    liste = client.get('/api/bookmarks/16?user_id=1').json()
    verifier('il a disparu',
             not any(o['id'] == identifiant for o in liste), liste)

    print('')
    print('6) ordre de lecture')
    premier = client.post('/api/bookmarks/16?user_id=3',
                          json={'chapter_index': 5, 'label': 'B'}).json()
    second = client.post('/api/bookmarks/16?user_id=3',
                         json={'chapter_index': 2, 'label': 'A'}).json()
    liste = client.get('/api/bookmarks/16?user_id=3').json()
    verifier('les onglets sont ranges par chapitre',
             [o['label'] for o in liste] == ['A', 'B'],
             [o['label'] for o in liste])
    for onglet in (premier, second):
        client.delete('/api/bookmarks/16/%s?user_id=3'
                      % onglet['bookmark']['id'])

    return ECHECS


if __name__ == '__main__':
    echecs = main_test()
    print('')
    print('TOUT EST OK' if echecs == 0
          else '%d VERIFICATION(S) EN ECHEC' % echecs)
    sys.exit(0 if echecs == 0 else 1)
