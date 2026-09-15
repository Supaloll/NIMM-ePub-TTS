# -*- coding: utf-8 -*-
"""Verification des voix ECOUTABLES tout de suite (session du 14/09/2026).

A lancer avec le Python du LECTEUR (3.14) :
    python test_voix/test_voix_ecoutables.py

Demande de Laurent : les menus ne doivent proposer que des voix qu'on peut
ecouter immediatement. Ce que le script verifie, sans navigateur :
  1. l'etat des moteurs lourds se lit (Kyutai port 8082, XTTS v2 port 8083) ;
  2. un moteur qui ne repond pas (ou qui charge encore) n'est jamais « pret » ;
  3. GET /api/voices ne contient les voix Kyutai QUE si le moteur est pret ;
  4. les voix Edge, Kokoro et Piper sont TOUJOURS proposees (aucun service a
     allumer pour elles) ;
  5. aucune voix XTTS n'est proposee tant que le service n'existe pas ici ;
  6. l'etat est garde 5 s en memoire (pas d'appel reseau a chaque menu).
"""

import asyncio
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

import main                                                    # noqa: E402
from modules.tts import KOKORO_VOICES, KYUTAI_VOICES, PIPER_VOICES, XTTS_VOICES  # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def resume(etat):
    morceaux = []
    for nom in sorted(etat):
        info = etat[nom]
        quoi = 'pret' if info['pret'] else ('en chargement' if info['actif'] else 'eteint')
        morceaux.append('{} : {}'.format(info.get('nom') or nom, quoi))
    return ' | '.join(morceaux)


def verifications():
    print('')
    print('1) etat des moteurs de voix lourds')
    etat = main.etat_moteurs_voix(force=True)
    verifier('Kyutai et XTTS v2 sont suivis',
             sorted(etat) == ['kyutai', 'xtts'], sorted(etat))
    verifier('chaque moteur a un nom lisible',
             all(etat[nom].get('nom') for nom in etat), etat)
    verifier('chaque moteur dit s\'il repond ET s\'il est pret',
             all(('actif' in etat[nom] and 'pret' in etat[nom]) for nom in etat), etat)
    verifier('un moteur eteint n\'est jamais annonce pret',
             not any((not etat[nom]['actif']) and etat[nom]['pret'] for nom in etat))
    print('   releve : ' + resume(etat))

    print('')
    print('2) voix proposees par GET /api/voices')
    routes = [r.path for r in main.app.routes]
    verifier('route /api/moteurs presente', '/api/moteurs' in routes)

    voix = asyncio.run(main.get_voices())
    ids = [v['id'] for v in voix]
    kyutai = [i for i in ids if i.startswith('kyutai:')]
    xtts = [i for i in ids if i.startswith('xtts:')]
    legeres = main.FRENCH_VOICES + KOKORO_VOICES + PIPER_VOICES

    if etat['kyutai']['pret']:
        verifier('moteur Kyutai pret -> les 35 voix Kyutai sont proposees',
                 len(kyutai) == len(KYUTAI_VOICES), len(kyutai))
    else:
        verifier('moteur Kyutai pas pret -> AUCUNE voix Kyutai proposee',
                 len(kyutai) == 0, kyutai[:3])
    if etat['xtts']['pret']:
        verifier('moteur XTTS pret -> les 35 voix XTTS sont proposees',
                 len(xtts) == len(XTTS_VOICES), len(xtts))
    else:
        verifier('moteur XTTS pas pret -> AUCUNE voix XTTS proposee',
                 len(xtts) == 0, xtts[:3])
    verifier('les voix Edge, Kokoro et Piper sont toujours proposees',
             all(v['id'] in ids for v in legeres), len(ids))
    verifier('la voix du narrateur (Ariane) est proposee',
             'fr-CH-ArianeNeural' in ids)
    verifier('aucun doublon dans le catalogue propose',
             len(ids) == len(set(ids)))
    print('   %d voix proposees' % len(ids))

    print('')
    print('3) memoire de 5 s (le menu ne relance pas un appel a chaque fois)')
    etat1 = main.etat_moteurs_voix(force=True)
    etat2 = main.etat_moteurs_voix()
    verifier('un appel rapproche relit la memoire, pas les moteurs', etat1 is etat2)
    etat3 = main.etat_moteurs_voix(force=True)
    verifier('un controle force interroge vraiment les moteurs', etat3 is not etat1)


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : voix ecoutables tout de suite')
    print('=' * 66)
    verifications()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    sys.exit(0 if ECHECS == 0 else 1)
