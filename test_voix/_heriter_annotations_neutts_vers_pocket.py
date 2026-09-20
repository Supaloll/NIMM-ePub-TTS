# -*- coding: utf-8 -*-
"""Fait heriter aux voix Pocket TTS les annotations d'ecoute de leurs jumelles.

DEMANDE DE LAURENT (20/09/2026) : « les autres prenoms sont ok pour moi. S'ils
existent deja dans un autre moteur, autant les utiliser, c'est bien plus
intuitif. » Les 18 voix Pocket TTS sont EXACTEMENT les memes extraits que les
voix de NeuTTS (`neutts:Femme001`, `neutts:Homme002`...), qui portent deja
genre, etoiles et criteres releves a l'oreille : on recopie, on ne re-annote
pas 18 voix pour rien.

DIFFERENCE AVEC L'OUTIL XTTS -> NEUTTS : ici les identifiants sont IDENTIQUES
(`neutts:Femme001` -> `pocket:Femme001`), il n'y a donc aucune table de
correspondance a construire.

CE QUI EST RECOPIE : genre, age, timbre, debit, registre, role, etoiles, note.
CE QUI RESTE A VERIFIER : l'ACCENT. Pocket TTS garde la diction de l'extrait
(mesure de l'atelier), mais il n'a JAMAIS ete ecoute pour l'accent sur ces 18
voix : on reprend donc la valeur existante, en le DISANT dans la note. Une case
a corriger dans la fenetre « Ecouter les voix » si Laurent juge autrement.

L'unique voix sans jumelle est `pocket:JEAN_EDGAR` (valide le 18/09/2026) : ni
elle ni `neutts:JEAN_EDGAR` n'existent, elle restera a annoter a l'oreille.

Les annotations existantes d'une voix Pocket TTS ne sont JAMAIS ecrasees.

Usage (avec le Python du lecteur) :
    python test_voix/_heriter_annotations_neutts_vers_pocket.py            # rapport
    python test_voix/_heriter_annotations_neutts_vers_pocket.py --ecrire   # ecrit
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(RACINE))

ANNOTATIONS = RACINE / 'data' / 'annotations_voix.json'
CHAMPS = ('genre', 'age', 'timbre', 'debit', 'registre', 'role', 'stars')
NOTE_HERITAGE = ("Tags herites de la meme voix dans un autre moteur (meme "
                 "extrait). L'ACCENT est a verifier a l'oreille : Pocket TTS "
                 "garde la diction de l'extrait, jamais mesuree ici.")


def voix_pocket():
    """Les identifiants `pocket:` du catalogue du lecteur (source unique)."""
    from modules.tts import POCKET_VOICES
    return [v['id'] for v in POCKET_VOICES]


def main():
    analyseur = argparse.ArgumentParser(
        description="Herite les annotations des voix jumelles sur Pocket TTS.")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee du fichier d'abord)")
    options = analyseur.parse_args()

    if not ANNOTATIONS.exists():
        print('ERR : %s introuvable' % ANNOTATIONS)
        return 1
    annotations = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))

    print('')
    print('=' * 70)
    print('ANNOTATIONS DES VOIX JUMELLES  ->  VOIX POCKET TTS')
    print('=' * 70)

    a_creer = {}
    deja = []
    sans_jumelle = []
    for identifiant in voix_pocket():
        if identifiant in annotations:
            deja.append(identifiant)
            continue
        jumeau = 'neutts:' + identifiant.split(':', 1)[1]
        source = annotations.get(jumeau)
        if not source:
            sans_jumelle.append(identifiant)
            continue
        copie = {champ: source.get(champ, '') for champ in CHAMPS}
        # On garde l'accent existant s'il y en a un : c'est la seule valeur que
        # Pocket TTS pourrait rendre differente, faute d'ecoute.
        copie['accent'] = source.get('accent', '') or 'neutre'
        copie['note'] = NOTE_HERITAGE
        a_creer[identifiant] = copie

    print('voix Pocket TTS du catalogue  : %d' % len(voix_pocket()))
    print('deja annotees (inchangees)    : %d' % len(deja))
    print('sans jumelle annotee          : %d  %s'
          % (len(sans_jumelle), ', '.join(sans_jumelle)))
    print('a annoter par heritage        : %d' % len(a_creer))

    for ident in sorted(a_creer)[:4]:
        valeurs = a_creer[ident]
        print('    %-24s %s / %s / %s / %s etoiles'
              % (ident, valeurs['genre'], valeurs['age'], valeurs['timbre'],
                 valeurs['stars']))

    if not a_creer:
        print('')
        print('rien a faire : tout est deja en place.')
        return 0

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete ecrit -- ajoute --ecrire)")
        return 0

    horodatage = datetime.now().strftime('%Y%m%d_%H%M')
    sauvegarde = ANNOTATIONS.with_name(
        '%s.bak_avant_heritage_pocket_%s' % (ANNOTATIONS.name, horodatage))
    shutil.copy2(str(ANNOTATIONS), str(sauvegarde))
    print('')
    print('copie datee : %s' % sauvegarde.name)

    annotations.update(a_creer)
    ANNOTATIONS.write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2, sort_keys=True),
        encoding='utf-8')
    print('annotations ecrites : %d voix au total' % len(annotations))
    print('')
    print("A SAVOIR : l'ACCENT de ces 18 voix reste a verifier a l'oreille dans")
    print("la fenetre « Ecouter les voix » (Pocket TTS garde la diction de")
    print("l'extrait, ce qui n'a jamais ete mesure ici).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
