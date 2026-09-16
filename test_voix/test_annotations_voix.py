# -*- coding: utf-8 -*-
"""Verification des annotations de voix (fenetre « Ecouter les voix »).

A lancer avec le Python du LECTEUR :
    python test_voix/test_annotations_voix.py

Ce que le script verifie (session du 14/09/2026, etendue le 16/09/2026) :
  1. la lecture des notes est vide tant que rien n'a ete annote ;
  2. une note s'enregistre et se relit ;
  3. une note entierement vide est SUPPRIMEE (le catalogue reprend la main) ;
  4. un appel sans identifiant de voix est refuse (400) ;
  5. les criteres FIXES (age, timbre, debit, accent, registre, role) sont
     annonces par le serveur -- c'est cette liste qui alimente les menus ;
  6. les criteres s'enregistrent et se relisent, sans toucher aux etoiles ;
  7. une valeur hors liste est REFUSEE (400) : les annotations restent
     calibrees, lisibles par l'attribution automatique des voix ;
  8. une annotation remise a zero disparait entierement ;
  9. une annotation d'AVANT les criteres (14/09) reste lisible telle quelle ;
 10. le fichier de notes survit a un redemarrage du serveur.

IMPORTANT : les notes de Laurent sont SAUVEGARDEES puis RESTAUREES a la fin.
Ce test ne doit jamais effacer un travail d'ecoute.
"""

import json
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
        print('5) les criteres FIXES sont annonces par le serveur')
        criteres = client.get('/api/annotations_voix/criteres').json()
        cles = [c.get('cle') for c in criteres]
        verifier('les 6 criteres, dans l ordre',
                 cles == ['age', 'timbre', 'debit', 'accent', 'registre', 'role'],
                 cles)
        verifier('chaque critere a un libelle et des valeurs',
                 all(c.get('libelle') and c.get('valeurs') for c in criteres),
                 criteres)
        verifier('chaque valeur a un libelle',
                 all(v.get('valeur') and v.get('libelle')
                     for c in criteres for v in c.get('valeurs', [])), criteres)
        verifier('le genre H/F n est pas un critere de la liste (il reste a part)',
                 'genre' not in cles, cles)

        print('')
        print('6) les criteres s enregistrent et se relisent')
        reponse = client.post('/api/annotations_voix', json={
            'voice_id': 'xtts:test_criteres', 'genre': 'H', 'stars': 3,
            'note': 'grave top !', 'age': 'vieux', 'timbre': 'grave',
            'debit': 'lent', 'accent': 'paysan', 'registre': 'populaire',
            'role': 'vieux'})
        verifier('enregistrement accepte', reponse.status_code == 200,
                 reponse.status_code)
        entree = client.get('/api/annotations_voix').json().get(
            'xtts:test_criteres', {})
        for cle, attendu in (('age', 'vieux'), ('timbre', 'grave'),
                             ('debit', 'lent'), ('accent', 'paysan'),
                             ('registre', 'populaire'), ('role', 'vieux'),
                             ('note', 'grave top !')):
            verifier('critere « %s » conserve' % cle,
                     entree.get(cle) == attendu, entree)
        verifier('les etoiles restent un nombre', entree.get('stars') == 3, entree)

        print('')
        print('7) une valeur hors liste est REFUSEE')
        reponse = client.post('/api/annotations_voix', json={
            'voice_id': 'xtts:test_criteres', 'timbre': 'rugueux'})
        verifier('timbre inconnu -> 400', reponse.status_code == 400,
                 reponse.status_code)
        reponse = client.post('/api/annotations_voix', json={
            'voice_id': 'xtts:test_criteres', 'age': 'Vieux'})
        verifier('majuscule refusee (les valeurs sont fixes) -> 400',
                 reponse.status_code == 400, reponse.status_code)
        entree = client.get('/api/annotations_voix').json().get(
            'xtts:test_criteres', {})
        verifier('un refus n abime pas l annotation deja enregistree',
                 entree.get('age') == 'vieux', entree)

        print('')
        print('8) une annotation remise a zero disparait')
        reponse = client.post('/api/annotations_voix',
                              json={'voice_id': 'xtts:test_criteres'})
        verifier('entree retiree',
                 'xtts:test_criteres' not in reponse.json().get('annotations', {}),
                 reponse.json().get('annotations'))

        print('')
        print('9) une annotation d AVANT les criteres reste lisible')
        chemin.write_text(json.dumps({
            'fr-CH-ArianeNeural': {'genre': 'F', 'note': '', 'stars': 3}}),
            encoding='utf-8')
        ancienne = client.get('/api/annotations_voix').json().get(
            'fr-CH-ArianeNeural', {})
        verifier('ancienne annotation relue', ancienne.get('stars') == 3, ancienne)
        verifier('absence de criteres = non renseigne (aucune erreur)',
                 ancienne.get('age') is None, ancienne)

        print('')
        print('10) les notes survivent a un redemarrage du serveur')
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
