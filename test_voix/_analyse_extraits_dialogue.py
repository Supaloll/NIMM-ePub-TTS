# -*- coding: utf-8 -*-
"""Quelles voix ont un extrait de DIALOGUE, et lesquelles de la NARRATION ?

Remarque de Laurent, 18/09/2026 : « quand je choisis un extrait dans
Librivox, il faut que je trouve des passages ou le lecteur lit un dialogue.
J'ai remarque que des passages que j'ai pris sont des passages de "narrateur",
lu comme quelqu'un qui lit une histoire. Mais les passages qui contiennent des
dialogues donnent une prosodie toute differente. Il faut que je choisisse des
passages audio de dialogues : ca ameliorera nettement l'effet "quelqu'un qui
parle" plutot que "quelqu'un qui lit". »

Verifier cette intuition, sans oreille : l'atelier a garde la TRANSCRIPTION de
chaque extrait de reference (`references.csv`, colonne `texte`). Un extrait de
dialogue se reconnait a ses marques de prise de parole : guillemets francais,
guillemets droits, tirets cadratins qui ouvrent une replique.

Ce script dit, famille par famille : combien d'extraits portent un dialogue, et
lesquels n'en portent AUCUN (les voix qui « lisent une histoire » a la place de
« parler ») -- avec le prenom du catalogue quand il est connu.

Lecture seule : rien n'est ecrit, aucun moteur n'est necessaire.

Usage :
    python test_voix/_analyse_extraits_dialogue.py
    python test_voix/_analyse_extraits_dialogue.py --tout    (texte de chaque extrait)
"""

import csv
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

REFERENCES = RACINE / 'neutts_service' / 'references'
TOUT = '--tout' in sys.argv

# Les marques d'une PRISE DE PAROLE dans un texte francais. Les guillemets et le
# tiret cadratin sont les deux facons d'ecrire un dialogue : une seule suffit.
MARQUES_DIALOGUE = re.compile(r'[\u00ab\u00bb\u201c\u201d\u2014"]')

# Familles de references : le dossier, ce a quoi ses extraits servent de voix, et
# la FIABILITE du texte disponible pour la detection.
#   - `cml_tts` : le texte vient de la banque CML-TTS (ponctuation officielle) :
#     la detection est fiable.
#   - `voix_libres_dp` et `kokoro` : le texte est une TRANSCRIPTION automatique
#     (Whisper). Elle met la ponctuation de phrase mais PAS les guillemets de
#     dialogue : un extrait de dialogue peut donc passer pour de la narration.
#     Le compteur y est donc un PLANCHER, pas une verite.
FAMILLES = [
    ('cml_tts', 'Kyutai / XTTS / NeuTTS (35 voix CML-TTS)', True),
    ('voix_libres_dp', 'voix libres de droits (extraits choisis par Laurent)', False),
    ('kokoro', 'voix Kokoro clonees', False),
]


def _id_depuis_fichier(nom):
    """'10087_11650_000028-0002_enhanced_reference.wav' -> id du catalogue."""
    for marque in ('_enhanced_reference.wav', '_reference.wav', '_enhanced.wav',
                   '.wav', '.mp3'):
        if nom.endswith(marque):
            return nom[:-len(marque)]
    return nom


def _prenoms_du_catalogue():
    """{identifiant: prenom} pour les voix Kyutai et XTTS du catalogue."""
    try:
        from modules.tts import KYUTAI_VOICES, XTTS_VOICES
    except Exception:
        return {}
    prenoms = {}
    for voix in list(KYUTAI_VOICES) + list(XTTS_VOICES):
        cle = voix['id'].split(':', 1)[1] if ':' in voix['id'] else voix['id']
        prenoms.setdefault(cle, voix['name'])
    return prenoms


def analyser(famille):
    """(lignes, nb_dialogue, nb_narration) d'une famille de references."""
    chemin = REFERENCES / famille / 'references.csv'
    if not chemin.is_file():
        return None, 0, 0
    lignes = []
    try:
        with open(chemin, 'r', encoding='utf-8', newline='') as f:
            for ligne in csv.DictReader(f, delimiter=';'):
                texte = (ligne.get('texte') or '').strip()
                fichier = (ligne.get('fichier') or '').strip()
                if not texte or not fichier:
                    continue
                lignes.append({
                    'fichier': fichier,
                    'id': _id_depuis_fichier(fichier),
                    'texte': texte,
                    'dialogue': bool(MARQUES_DIALOGUE.search(texte)),
                })
    except Exception as e:
        print('  ERREUR de lecture de %s : %s' % (chemin, e))
        return None, 0, 0
    nb = sum(1 for l in lignes if l['dialogue'])
    return lignes, nb, len(lignes) - nb


def main():
    print('')
    print('=' * 78)
    print('EXTRAITS DE VOIX : DIALOGUE OU NARRATION ?')
    print('=' * 78)
    print('')
    print('  Question de Laurent (18/09/2026) : un extrait de DIALOGUE donnerait')
    print('  une prosodie de « quelqu\'un qui parle », la narration donnant')
    print('  « quelqu\'un qui lit une histoire ». On lit ici les transcriptions')
    print('  gardees par l\'atelier, pas une impression.')

    prenoms = _prenoms_du_catalogue()
    total_dialogue = 0
    total_narration = 0
    sans_dialogue = []

    for famille, libelle, fiable in FAMILLES:
        lignes, nb_dialogue, nb_narration = analyser(famille)
        print('')
        print('=' * 78)
        print('%s' % libelle)
        print('=' * 78)
        if lignes is None:
            print('  aucune reference trouvee (%s)' % (REFERENCES / famille))
            continue
        total_dialogue += nb_dialogue
        total_narration += nb_narration

        print('  %d extraits : %d avec DIALOGUE (%.0f %%), %d sans (%.0f %%)'
              % (len(lignes), nb_dialogue,
                 100.0 * nb_dialogue / max(len(lignes), 1),
                 nb_narration, 100.0 * nb_narration / max(len(lignes), 1)))
        if not fiable:
            print('  ATTENTION : texte issu d\'une TRANSCRIPTION automatique (sans')
            print('  guillemets de dialogue) -> le nombre de dialogues est un PLANCHER.')

        sans = [l for l in lignes if not l['dialogue']]
        if sans:
            print('')
            print('  EXTRAITS SANS AUCUNE MARQUE DE DIALOGUE (voix qui « lit ») :')
            for l in sans:
                prenom = prenoms.get(l['id'], '')
                etiquette = ('%s (%s)' % (prenom, l['id'])) if prenom else l['id']
                print('    - %s' % etiquette[:72])
                sans_dialogue.append((libelle, etiquette, l['texte']))
        if TOUT:
            print('')
            print('  (texte de TOUS les extraits)')
            for l in lignes:
                etat = 'DIALOGUE ' if l['dialogue'] else 'narration'
                print('    [%s] %s' % (etat, l['texte'][:150]))
        elif sans:
            print('')
            print('  Exemple d\'un extrait sans dialogue :')
            print('    %s' % sans[0]['texte'][:140])

    print('')
    print('=' * 78)
    print('BILAN')
    print('=' * 78)
    total = total_dialogue + total_narration
    if total:
        print('  %d extraits analyses : %d avec dialogue (%.0f %%), %d sans (%.0f %%)'
              % (total, total_dialogue, 100.0 * total_dialogue / total,
                 total_narration, 100.0 * total_narration / total))
    if sans_dialogue:
        print('')
        print('  %d voix dont l\'extrait ne contient AUCUN dialogue :'
              % len(sans_dialogue))
        for libelle, etiquette, _texte in sans_dialogue:
            print('    - %s' % etiquette[:72])
    print('')
    print('  RAPPEL (methode de l\'atelier) : une mesure ne remplace pas')
    print('  l\'oreille. A confirmer en ecoutant une voix de chaque colonne.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
