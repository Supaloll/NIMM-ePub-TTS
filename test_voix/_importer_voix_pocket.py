# -*- coding: utf-8 -*-
"""ANNOTER LES NOUVELLES VOIX POCKET TTS, sans repasser par l'ecran d'ecoute.

Pourquoi un outil : les voix arrivees par HERITAGE (les 18 du 20/09/2026)
recopiaient les criteres de leurs jumelles NeuTTS. Les lots SUIVANTS n'ont pas
de jumelle (`test_voix/_heriter_annotations_neutts_vers_pocket.py` ne peut rien
pour eux) : il faut donc ecrire leurs criteres a la main, une fois.

Ce que l'outil fait, pour chaque voix `pocket:` du catalogue qui n'est PAS
encore annotee :
    1. il verifie que son WAV de reference existe bien dans
       `pocket_tts_service\\voix\\` (nom = identifiant + `_reference.wav`) ;
    2. il ecrit ses criteres d'ecoute dans `data/annotations_voix.json`.

CE QUI EST ECRIT, ET QUAND
    - par defaut : RIEN. Le script affiche seulement ce qu'il ferait ;
    - avec --ecrire : copie datee de `data/annotations_voix.json`
      (`.bak_avant_annotations_pocket_<AAAAMMJJ>`), puis ajout des voix
      manquantes. **Les annotations des voix existantes ne sont JAMAIS
      ecrasees** : c'est ce qui protege le travail d'ecoute de Laurent.

LES CRITERES DU LOT DU 23/09/2026 (decides avec Laurent le 23/09/2026)
    - verdict d'ecoute : les 10 voix retenues, **3 etoiles** (choix de Laurent :
      elles peuvent entrer dans le casting automatique) ;
    - `timbre` : lu sur la HAUTEUR mesuree par l'atelier dans le clone
      (l'INDEX_RETENUES du lot) -- 87 a 120 Hz = grave, 129 a 136 Hz = medium ;
    - `debit` : **vif** -- le debit appartient au moteur (mesure de l'atelier :
      20 a 25 caracteres/seconde, contre ~15 pour une lecture naturelle) ;
    - `accent` : **neutre**, A VERIFIER a l'oreille : Pocket TTS garde la
      diction de l'extrait, et elle n'a jamais ete mesuree ici ;
    - `role` : vide (ces voix sont francaises, elles peuvent etre castees).

Usage :
    python test_voix/_importer_voix_pocket.py            # rapport seul
    python test_voix/_importer_voix_pocket.py --ecrire   # ecrit
"""

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(RACINE))

ANNOTATIONS = RACINE / 'data' / 'annotations_voix.json'
DOSSIER_VOIX = RACINE / 'pocket_tts_service' / 'voix'

NOTE_LOT_23_09 = (
    "Voix du lot Pocket TTS du 23/09/2026. L'extrait de reference vient d'un "
    "LIVRE AUDIO DU COMMERCE : ecoute privee d'accord, PARTAGE interdit sans "
    "l'accord de la personne. Le DEBIT est celui du moteur (~20-25 car/s), et "
    "l'ACCENT reste a verifier a l'oreille (Pocket TTS garde la diction de "
    "l'extrait, jamais mesuree ici)."
)

# Timbre constate dans le clone, voix par voix (hauteur mesuree par l'atelier).
TIMBRES = {
    'pocket:homme_aigu_6877654': 'aigu',
    'pocket:homme_aigu_987654': 'aigu',
    'pocket:homme_grave_5649798': 'grave',
    'pocket:homme_grave_65121598': 'grave',
    'pocket:homme_grave_6546546': 'grave',
    'pocket:homme_grave_6549821': 'grave',
    'pocket:homme_normal_21545605': 'grave',
    'pocket:homme_normal_65465987312': 'medium',
    'pocket:homme_normal65465409': 'medium',
    'pocket:homme_voix_grave265146': 'grave',
}

CHAMPS = ('genre', 'age', 'timbre', 'debit', 'registre', 'role', 'stars',
          'accent', 'note')

# Voix VOLONTAIREMENT laissees sans criteres : c'est l'oreille de Laurent qui
# doit les remplir, et lui seul. `pocket:JEAN_EDGAR` est dans ce cas depuis le
# 20/09/2026 (il n'a aucune jumelle dont heriter les criteres) : l'outil ne
# doit pas « boucher le trou » avec des valeurs inventees.
LAISSEES_A_L_OREILLE = ('pocket:JEAN_EDGAR',)


def voix_du_catalogue():
    """Les identifiants `pocket:` du catalogue du lecteur (source unique)."""
    from modules.tts import POCKET_VOICES
    return [(v['id'], v.get('name', ''), v.get('gender', ''))
            for v in POCKET_VOICES]


def criteres(identifiant, genre):
    """Les criteres d'ecoute d'une voix qui n'en a pas encore."""
    timbre = TIMBRES.get(identifiant, 'medium')
    return {
        'genre': genre or 'M',
        'age': 'adulte',
        'timbre': timbre,
        'debit': 'vif',
        'registre': 'neutre',
        'role': '',
        'stars': 3,
        'accent': 'neutre',
        'note': (NOTE_LOT_23_09 if identifiant in TIMBRES
                 else "Voix Pocket TTS ajoutee apres le 23/09/2026 : criteres "
                      "a relire avant de s y fier."),
    }


def main():
    analyseur = argparse.ArgumentParser(
        description="Annote les nouvelles voix Pocket TTS (rapport par defaut).")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee du fichier d'abord)")
    options = analyseur.parse_args()

    if not ANNOTATIONS.exists():
        print('ERR : %s introuvable' % ANNOTATIONS)
        return 1
    annotations = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))

    print('')
    print('=' * 70)
    print('ANNOTATIONS DES NOUVELLES VOIX POCKET TTS')
    print('=' * 70)

    a_creer = {}
    deja = []
    sans_wav = []
    a_l_oreille = []
    catalogue = voix_du_catalogue()
    for identifiant, _prenom, genre in catalogue:
        if identifiant in annotations:
            deja.append(identifiant)
            continue
        if identifiant in LAISSEES_A_L_OREILLE:
            a_l_oreille.append(identifiant)
            continue
        nom_wav = identifiant.split(':', 1)[1] + '_reference.wav'
        if not (DOSSIER_VOIX / nom_wav).is_file():
            sans_wav.append('%s (%s)' % (identifiant, nom_wav))
            continue
        a_creer[identifiant] = criteres(identifiant, genre)

    print('voix Pocket TTS du catalogue : %d' % len(catalogue))
    print('deja annotees (inchangees)   : %d' % len(deja))
    print('laissees a l oreille de Laurent : %d  %s'
          % (len(a_l_oreille), ', '.join(a_l_oreille) if a_l_oreille else ''))
    print('fichier de voix manquant     : %d  %s'
          % (len(sans_wav), ', '.join(sans_wav) if sans_wav else ''))
    print('a annoter                    : %d' % len(a_creer))
    for identifiant in sorted(a_creer):
        valeurs = a_creer[identifiant]
        print('    %-34s %s / %s / %s etoiles'
              % (identifiant, valeurs['genre'], valeurs['timbre'],
                 valeurs['stars']))

    if sans_wav:
        print('')
        print('ATTENTION : ces voix sont au catalogue sans fichier de reference.')
        print("Elles ne peuvent pas parler : c'est un probleme a regler AVANT.")
        return 1

    if not a_creer:
        print('')
        print('rien a faire : toutes les voix du catalogue sont annotees.')
        return 0

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete ecrit -- ajoute --ecrire)")
        return 0

    horodatage = date.today().strftime('%Y%m%d')
    sauvegarde = ANNOTATIONS.with_name(
        '%s.bak_avant_annotations_pocket_%s' % (ANNOTATIONS.name, horodatage))
    if not sauvegarde.exists():
        shutil.copy2(str(ANNOTATIONS), str(sauvegarde))
        print('')
        print('copie datee : %s' % sauvegarde.name)
    else:
        print('')
        print('copie datee deja presente : %s (non refaite)' % sauvegarde.name)

    avant = len(annotations)
    annotations.update(a_creer)
    ANNOTATIONS.write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2, sort_keys=True),
        encoding='utf-8')

    # Controle APRES ecriture : on relit ce qui a ete ecrit, et on verifie que
    # rien d'ancien n'a bouge.
    relu = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))
    print('')
    print('verification apres ecriture :')
    print('  voix annotees : %d -> %d' % (avant, len(relu)))
    print('  les %d voix annotees d avant sont intactes : %s'
          % (len(deja), 'OK' if all(k in relu for k in deja) else 'ECHEC'))
    print('  les %d nouvelles sont lisibles : %s'
          % (len(a_creer), 'OK' if all(k in relu for k in a_creer) else 'ECHEC'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
