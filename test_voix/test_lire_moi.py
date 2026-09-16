# -*- coding: utf-8 -*-
"""Verifie que le mode d'emploi du dossier ne cite QUE des fichiers existants.

`test_voix/LIRE_MOI.md` sert a retrouver ses petits quand on ne sait plus quel
script fait quoi. Un mode d'emploi qui cite un fichier renomme ou supprime est
pire que pas de mode d'emploi : il envoie dans le mur. Ce test l'empeche.

Il verifie aussi que le script payant et son lanceur sont TOUJOURS proteges :
le mot « PAYANT » dans leur nom, et le garde-fou `--je-paie` dans le script.

Usage : python test_voix/test_lire_moi.py
"""

import re
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
sys.stdout.reconfigure(encoding='utf-8')

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def main_verifications():
    lire_moi = DOSSIER / 'LIRE_MOI.md'
    verifier('le mode d emploi existe', lire_moi.is_file(), lire_moi)
    if not lire_moi.is_file():
        return
    texte = lire_moi.read_text(encoding='utf-8')

    # Tous les fichiers cites entre accents graves, avec une extension connue.
    motif = r'`([A-Za-z0-9_\-]+\.(?:py|js|bat|txt|json|md))`'
    cites = sorted(set(re.findall(motif, texte)))
    verifier('le mode d emploi cite des fichiers', len(cites) >= 15, len(cites))

    manquants = [nom for nom in cites
                 if not (DOSSIER / nom).exists() and not (RACINE / nom).exists()]
    verifier('aucun fichier cite n a disparu', not manquants, manquants)

    # Le script payant et son lanceur : proteges, et annonces comme tels.
    script = DOSSIER / '_PAYANT_test_attribution_api.py'
    lanceur = DOSSIER / '_PAYANT_lancer_test_attribution.bat'
    verifier('le script payant est renomme avec PAYANT', script.is_file(), script)
    verifier('son lanceur est renomme avec PAYANT', lanceur.is_file(), lanceur)
    if script.is_file():
        contenu = script.read_text(encoding='utf-8')
        verifier('le script payant exige --je-paie (garde-fou)',
                 '--je-paie' in contenu and 'sys.exit(2)' in contenu)
    if lanceur.is_file():
        contenu = lanceur.read_text(encoding='utf-8')
        verifier('le lanceur demande confirmation avant de payer',
                 'choice' in contenu and '--je-paie' in contenu)
    verifier('l ancien nom « test_attribution.py » n existe plus',
             not (DOSSIER / 'test_attribution.py').exists())
    verifier('l ancien lanceur neutre n existe plus',
             not (DOSSIER / 'LANCER_TEST.bat').exists())
    verifier('le mode d emploi annonce le danger',
             'PAYANT' in texte and 'factur' in texte.lower())


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : mode d emploi du dossier test_voix')
    print('=' * 66)
    main_verifications()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    sys.exit(0 if ECHECS == 0 else 1)
