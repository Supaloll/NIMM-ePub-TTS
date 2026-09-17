# -*- coding: utf-8 -*-
"""Fait heriter aux voix NeuTTS les annotations d'ecoute de leurs jumelles XTTS.

DEMANDE DE LAURENT (16/09/2026) : « les voix peuvent garder leur tags pour le
moment (les memes que XTTS) ». Autrement dit : pas question de re-annoter 109
voix a l'oreille ce soir -- on recopie ce qui existe deja sur les voix XTTS.

CE QUI EST RECOPIE : genre, age, timbre, debit, registre, role, etoiles, note.
CE QUI N'EST PAS RECOPIE : l'ACCENT. Raison mesuree : NeuTTS prononce avec SON
modele francais, donc les accents s'effacent (ecoute de Laurent le 16/09/2026 :
« les accents Kokoro ont disparu »). Recopier « accent anglais » sur une voix
NeuTTS ferait envoyer cette voix sur un personnage etranger alors qu'elle ne
sonne pas anglaise. L'accent est donc remis a « neutre », avec une note qui le
dit -- une seule case a corriger si Laurent juge autrement a l'ecoute.

Les annotations existantes d'une voix NeuTTS ne sont JAMAIS ecrasees.

Usage :
    python test_voix/_heriter_annotations_xtts_vers_neutts.py            # rapport
    python test_voix/_heriter_annotations_xtts_vers_neutts.py --ecrire   # ecrit
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _rapprocher_neutts_xtts import candidats, identifiants_references  # noqa: E402

ANNOTATIONS = RACINE / 'data' / 'annotations_voix.json'
CHAMPS = ('genre', 'age', 'timbre', 'debit', 'registre', 'role', 'stars', 'note')
NOTE_HERITAGE = ("Tags herites d'XTTS ou de Kokoro (a revérifier a l'oreille). "
                 "Accent non repris : NeuTTS efface les accents.")


def mapping_vers_neutts():
    """{voix deja cataloguee (xtts: ou kokoro:) -> voix NeuTTS jumelle}.

    On ne se limite pas aux voix XTTS : les 30 voix Kokoro ont elles aussi des
    annotations, et leurs jumelles NeuTTS en manquent tout autant.
    """
    table = {}
    for _dossier, identifiants in identifiants_references().items():
        for identifiant in identifiants:
            for candidat in candidats(identifiant):
                if candidat.startswith(('xtts:', 'kokoro:')):
                    table[candidat] = 'neutts:' + identifiant
    return table


def main():
    analyseur = argparse.ArgumentParser(
        description="Herite les annotations XTTS sur les voix NeuTTS.")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee du fichier d'abord)")
    options = analyseur.parse_args()

    if not ANNOTATIONS.exists():
        print('ERR : %s introuvable' % ANNOTATIONS)
        return 1
    annotations = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))
    table = mapping_vers_neutts()

    print('')
    print('=' * 70)
    print('ANNOTATIONS XTTS  ->  VOIX NEUTTS (les memes tags)')
    print('=' * 70)
    print('jumelles connues      : %d' % len(table))
    print('annotations existantes: %d voix' % len(annotations))

    a_creer = {}
    deja = []
    sans_annotation = []
    for voix_xtts, voix_neutts in sorted(table.items()):
        source = annotations.get(voix_xtts)
        if not source:
            sans_annotation.append(voix_xtts)
            continue
        if voix_neutts in annotations:
            deja.append(voix_neutts)
            continue
        copie = {champ: source.get(champ, '') for champ in CHAMPS}
        copie['accent'] = 'neutre'                 # voir la docstring
        copie['note'] = NOTE_HERITAGE
        a_creer[voix_neutts] = copie

    print('')
    print('deja annotees (laissees telles quelles) : %d' % len(deja))
    print('jumelles XTTS sans annotation           : %d' % len(sans_annotation))
    print('voix NeuTTS a annoter                   : %d' % len(a_creer))

    exemple = sorted(a_creer)[:3]
    for ident in exemple:
        print('    %-28s %s' % (ident, a_creer[ident]))

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
        '%s.bak_avant_heritage_neutts_%s' % (ANNOTATIONS.name, horodatage))
    shutil.copy2(str(ANNOTATIONS), str(sauvegarde))
    print('')
    print('copie : %s' % sauvegarde.name)

    annotations.update(a_creer)
    ANNOTATIONS.write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2, sort_keys=True),
        encoding='utf-8')
    print('annotations ecrites : %d voix au total' % len(annotations))
    print('')
    print('A SAVOIR : les accents des voix NeuTTS sont a « neutre » -- a')
    print('corriger a l\'oreille dans la fenetre « Ecouter les voix ».')
    return 0


if __name__ == '__main__':
    sys.exit(main())
