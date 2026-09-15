# -*- coding: utf-8 -*-
"""Verification des annotations de voix (fenetre « Ecouter les voix »).

A lancer avec le Python du LECTEUR :
    python test_voix/test_annotations_voix.py

Ce que le script verifie (session du 14/09/2026) :
  1. la lecture des notes est vide tant que rien n'a ete annote ;
  2. une note s'enregistre et se relit ;
  3. une note entierement vide est SUPPRIMEE (le catalogue reprend la main) ;
  4. un appel sans identifiant de voix est refuse (400) ;
  5. le fichier de notes survit a un redemarrage du serveur.

IMPORTANT : les notes de Laurent sont SAUVEGARDEES puis RESTAUREES a la fin.
Ce test ne doit jamais effacer un travail d'ecoute.
"""

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient                      # noqa: E402
import main                                                     # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def verifications():
    chemin = main.ANNOTATIONS_VOIX_PATH
    sauvegarde = chemin.read_text(encoding='utf-8') if chemin.exists() else None
    print('Fichier de notes : %s' % chemin)
    print('   notes deja presentes : %s'
          % ('conservees (sauvegardees)' if sauvegarde else 'aucune'))

    try:
        if chemin.exists():
            chemin.unlink()
        client = TestClient(main.app)

        print('')
        print('1) lecture initiale')
        reponse = client.get('/api/annotations_voix')
        verifier('la route repond', reponse.status_code == 200, reponse.status_code)
        verifier('aucune note au depart', reponse.json() == {}, reponse.json())

        print('')
        print('2) enregistrement et relecture')
        reponse = client.post('/api/annotations_voix', json={
            'voice_id': 'xtts:test_ecoute', 'genre': 'F', 'stars': 2,
            'note': 'test automatique'})
        verifier('enregistrement accepte', reponse.status_code == 200,
                 reponse.status_code)
        notes = client.get('/api/annotations_voix').json()
        verifier('la note est relue', 'xtts:test_ecoute' in notes, notes)
        verifier('le genre est conserve',
                 notes.get('xtts:test_ecoute', {}).get('genre') == 'F', notes)
        verifier('les etoiles sont conservees',
                 notes.get('xtts:test_ecoute', {}).get('stars') == 2, notes)
        verifier('le fichier est ecrit sur le disque', chemin.exists())

        print('')
        print('3) une note vide est supprimee')
        reponse = client.post('/api/annotations_voix',
                              json={'voice_id': 'xtts:test_ecoute'})
        verifier('note vide -> entree retiree',
                 reponse.json().get('annotations') == {},
                 reponse.json())

        print('')
        print('4) appel invalide')
        reponse = client.post('/api/annotations_voix', json={'voice_id': ''})
        verifier('sans identifiant de voix -> 400', reponse.status_code == 400,
                 reponse.status_code)

        print('')
        print('5) les notes survivent a un redemarrage du serveur')
        client.post('/api/annotations_voix', json={
            'voice_id': 'xtts:test_ecoute', 'genre': 'H', 'stars': 3,
            'note': 'relu apres redemarrage'})
        main._ETAT_MOTEURS['etat'] = None          # on simule un demarrage
        notes = TestClient(main.app).get('/api/annotations_voix').json()
        verifier('la note est toujours la',
                 notes.get('xtts:test_ecoute', {}).get('note')
                 == 'relu apres redemarrage', notes)
    finally:
        # On rend le fichier dans son etat d'origine, quoi qu'il arrive.
        if sauvegarde is None:
            if chemin.exists():
                chemin.unlink()
        else:
            chemin.write_text(sauvegarde, encoding='utf-8')
        print('')
        print('Notes de Laurent : %s'
              % ('restaurees' if sauvegarde else 'aucune a restaurer'))


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : annotations des voix (« Ecouter les voix »)')
    print('=' * 66)
    verifications()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    sys.exit(0 if ECHECS == 0 else 1)
