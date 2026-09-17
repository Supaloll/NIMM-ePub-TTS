# -*- coding: utf-8 -*-
"""Rapproche les extraits de reference NeuTTS des voix DEJA cataloguees.

Question a laquelle il repond : pour chaque extrait de neutts_service\\references,
quelle voix du catalogue (modules/tts.py) porte le meme identifiant ? C'est ce
qui permettra d'heriter des MEMES prenoms, etoiles et genres que les voix XTTS
et Kokoro, au lieu de tout re-saisir a la main.

Regles de correspondance (verifiees le 16/09/2026) :
  - identifiant tel quel        -> "xtts:<identifiant>"    (les voix CML-TTS) ;
  - "Femme001" / "Homme..."     -> "dp_" + minuscules      (les 19 voix libres) ;
  - "ff_amelie" / "fm_hugo"     -> "kokoro:<identifiant>"  (les voix Kokoro).

Lecture seule : ce script ne modifie rien, il ne fait que comparer.

Usage : python test_voix/_rapprocher_neutts_xtts.py
"""

import importlib.util
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

REFERENCES = RACINE / 'neutts_service' / 'references'
TTS = RACINE / 'modules' / 'tts.py'


def entrees_du_catalogue(nom_liste):
    """{identifiant: (prenom, genre, etoiles, region)} d'une liste de tts.py."""
    source = TTS.read_text(encoding='utf-8')
    debut = source.index(nom_liste + ' = [')
    fin = source.index('\n]', debut)
    entrees = {}
    for ligne in source[debut:fin].splitlines():
        identifiant = re.search(r'"id":\s*"([^"]+)"', ligne)
        if not identifiant:
            continue
        prenom = re.search(r'"name":\s*"([^"]*)"', ligne)
        genre = re.search(r'"gender":\s*"([^"]*)"', ligne)
        etoiles = re.search(r'"stars":\s*(\d+)', ligne)
        region = re.search(r'"region":\s*"([^"]*)"', ligne)
        entrees[identifiant.group(1)] = (
            prenom.group(1) if prenom else '?',
            genre.group(1) if genre else '?',
            int(etoiles.group(1)) if etoiles else None,
            region.group(1) if region else '')
    return entrees


def identifiants_references():
    """{dossier: [identifiants]} des extraits, TELS QUE LE SERVICE LES VOIT.

    On appelle la fonction de reperage du service (jamais une copie) : les
    identifiants sont donc exactement ceux qu'il annoncera au lecteur
    (`GET /voix`), suffixe `_enhanced` retire compris.
    """
    chemin = RACINE / 'neutts_service' / 'servir_neutts.py'
    spec = importlib.util.spec_from_file_location('servir_neutts', chemin)
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)

    trouves = {}
    for identifiant, valeurs in service._repertorier_references().items():
        wav = valeurs[0]
        trouves.setdefault(wav.parent.name, []).append(identifiant)
    for liste in trouves.values():
        liste.sort()
    return trouves


def candidats(identifiant):
    """Les identifiants de catalogue possibles pour un extrait."""
    if re.match(r'^(ff|fm|af|am|bf|bm)[a-z0-9_]+$', identifiant):
        return ['kokoro:' + identifiant]          # voix Kokoro
    if re.match(r'^(Femme|Homme)\d+$', identifiant):
        return ['xtts:dp_' + identifiant.lower()]  # extraits libres de droits
    return ['xtts:' + identifiant]                 # voix CML-TTS


def main():
    kokoro = entrees_du_catalogue('KOKORO_VOICES')
    xtts = entrees_du_catalogue('XTTS_VOICES')
    catalogue = dict(xtts)
    catalogue.update(kokoro)

    references = identifiants_references()

    print('')
    print('=' * 70)
    print('REFERENCES NeuTTS  ->  CATALOGUE DU LECTEUR')
    print('=' * 70)
    print('catalogue lu dans : %s' % TTS.name)
    print('  KOKORO_VOICES : %d voix   |   XTTS_VOICES : %d voix'
          % (len(kokoro), len(xtts)))
    print('')

    if not references:
        print('aucun extrait dans %s' % REFERENCES)
        return 0

    total = trouves = 0
    inconnus = []
    for dossier in sorted(references):
        liste = references[dossier]
        trouves_dossier = 0
        lignes = []
        for identifiant in liste:
            total += 1
            trouve = None
            for candidat in candidats(identifiant):
                if candidat in catalogue:
                    trouve = (candidat, catalogue[candidat])
                    break
            if trouve:
                trouves += 1
                trouves_dossier += 1
                if len(lignes) < 3:
                    _cle, (prenom, genre, etoiles, region) = trouve
                    lignes.append('%s -> %-28s %-12s %s  %s etoile(s)'
                                  % (identifiant, trouve[0], prenom, genre,
                                     etoiles))
            else:
                inconnus.append((dossier, identifiant))
        print('%-16s %3d extraits, %3d avec une voix connue'
              % (dossier, len(liste), trouves_dossier))
        for ligne in lignes:
            print('    %s' % ligne)

    print('')
    print('total : %d extraits, %d rapproches' % (total, trouves))
    if inconnus:
        print('')
        print('SANS VOIX CONNUE (%d) : a nommer a la main avant le branchement'
              % len(inconnus))
        for dossier, identifiant in inconnus[:20]:
            print('    %-16s %s' % (dossier, identifiant))
    else:
        print('chaque extrait a une voix connue : le catalogue peut heriter des')
        print('memes prenoms, genres et etoiles (aucune saisie a la main).')
    print('')
    print('Rappel : ce script ne modifie RIEN. Le catalogue NeuTTS de')
    print('modules/tts.py est GENERE par _generer_catalogue_neutts.py :')
    print('relance-le (avec --ecrire) apres avoir ajoute des voix au moteur.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
