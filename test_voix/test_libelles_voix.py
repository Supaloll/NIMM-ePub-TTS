# -*- coding: utf-8 -*-
"""Verification des noms de voix affiches dans le lecteur (15/09/2026).

A lancer avec le Python du LECTEUR :
    python test_voix/test_libelles_voix.py

Pourquoi ce test (constat de Laurent, apres un re-cast de Shantaram) : la
fenetre du casting affichait l'IDENTIFIANT technique des voix XTTS
(« xtts:cml9804 ») au lieu du prenom donne a la voix (« Alphonse »). Cause :
la liste des voix proposees (/api/voices) ne contient les voix XTTS que si
LEUR MOTEUR EST PRET, et elle peut dater d'avant l'allumage du moteur.

La route /api/voix_catalogue repond a ce besoin : TOUTES les voix, moteurs
eteints compris, avec leur prenom et un drapeau `dispo`. Ce test verifie :
  1. le catalogue contient bien toutes les familles de voix ;
  2. chaque voix porte un nom lisible (jamais un identifiant vide) ;
  3. le cas signale par Laurent : xtts:cml9804 s'appelle « Alphonse » ;
  4. `dispo` dit la verite, comparee a /api/moteurs ;
  5. sur un VRAI livre caste de la base, chaque voix attribuee a un nom.
"""

import os
import sqlite3
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


def main_test():
    client = TestClient(main.app)

    print('')
    print('1) le catalogue complet des voix')
    catalogue = client.get('/api/voix_catalogue').json()
    familles = {}
    for voix in catalogue:
        familles.setdefault(voix.get('famille'), []).append(voix['id'])
    print('   %d voix, familles : %s'
          % (len(catalogue), ', '.join('%s %d' % (f, len(i))
                                       for f, i in sorted(familles.items()))))
    verifier('plus de 150 voix au catalogue', len(catalogue) > 150, len(catalogue))
    for famille in ('edge', 'kokoro', 'piper', 'kyutai', 'xtts'):
        verifier('la famille %s est presente' % famille, bool(familles.get(famille)))

    print('')
    print('2) chaque voix porte un nom lisible')
    sans_nom = [v['id'] for v in catalogue if not (v.get('name') or '').strip()]
    verifier('aucune voix sans nom', not sans_nom, sans_nom)
    sans_region = [v['id'] for v in catalogue if not (v.get('region') or '').strip()]
    verifier('aucune voix sans region (le drapeau des menus)',
             not sans_region, sans_region)

    print('')
    print('3) le cas signale par Laurent : la voix XTTS de Shantaram')
    alphonse = next((v for v in catalogue if v['id'] == 'xtts:cml9804'), None)
    verifier('xtts:cml9804 est au catalogue', alphonse is not None)
    verifier('elle s appelle « Alphonse »',
             alphonse and alphonse['name'] == 'Alphonse',
             alphonse and alphonse['name'])
    verifier('elle porte sa region (d ou vient le drapeau XTTS)',
             alphonse and 'XTTS' in (alphonse.get('region') or ''),
             alphonse and alphonse.get('region'))

    print('')
    print('4) le drapeau `dispo` dit la verite')
    etat      = client.get('/api/moteurs').json()
    proposees = client.get('/api/voices').json()
    ids_offerts = set(v['id'] for v in proposees)
    for famille in ('xtts', 'kyutai'):
        pret = bool((etat.get(famille) or {}).get('pret'))
        erreurs = [v['id'] for v in catalogue
                   if v.get('famille') == famille and bool(v.get('dispo')) != pret]
        verifier('dispo de %s = moteur %s'
                 % (famille, 'pret' if pret else 'pas pret'), not erreurs, erreurs)
        # Coherence avec la liste des voix PROPOSEES : un moteur qui n'est pas
        # pret ne propose aucune de ses voix (decision du 14/09/2026).
        offertes = [i for i in ids_offerts if i.startswith(famille + ':')]
        verifier('voix %s proposees seulement si le moteur est pret' % famille,
                 bool(offertes) == pret, '%d proposee(s)' % len(offertes))
    # Edge, Kokoro et Piper sont toujours lisibles tout de suite.
    for famille in ('edge', 'kokoro', 'piper'):
        disponible = all(v.get('dispo') for v in catalogue
                         if v.get('famille') == famille)
        verifier('%s toujours disponible' % famille, disponible)

    print('')
    print('5) sur un vrai livre caste : chaque voix attribuee a un nom')
    base = os.path.join(RACINE, 'data', 'nimm_epub.db')
    noms = {v['id']: v['name'] for v in catalogue}
    if not os.path.exists(base):
        print('   (pas de base locale : controle ignore)')
    else:
        conn = sqlite3.connect(base)
        conn.row_factory = sqlite3.Row
        livre = conn.execute(
            "SELECT id, title FROM books WHERE title LIKE '%Shantaram%' "
            "AND cast_status = 'done' ORDER BY id DESC LIMIT 1").fetchone()
        if not livre:
            livre = conn.execute(
                "SELECT id, title FROM books WHERE cast_status = 'done' "
                "ORDER BY id DESC LIMIT 1").fetchone()
        if not livre:
            print('   (aucun livre caste en base : controle ignore)')
        else:
            voix = conn.execute(
                'SELECT character_name, voice_id FROM voices WHERE book_id = ?',
                (livre['id'],)).fetchall()
            print('   livre : %s (%d personnages)' % (livre['title'], len(voix)))
            orphelines = [r['voice_id'] for r in voix if r['voice_id'] not in noms]
            verifier('chaque voix attribuee existe au catalogue',
                     not orphelines, sorted(set(orphelines))[:5])
            xtts_livre = [r for r in voix if r['voice_id'].startswith('xtts:')]
            print('   dont %d voix XTTS, par exemple : %s'
                  % (len(xtts_livre),
                     ', '.join('%s -> %s' % (r['character_name'],
                                             noms.get(r['voice_id']))
                               for r in xtts_livre[:4])))
        conn.close()

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    print('=' * 70)
    print('VERIFICATION : noms des voix (catalogue complet /api/voix_catalogue)')
    print('=' * 70)
    sys.exit(main_test())
