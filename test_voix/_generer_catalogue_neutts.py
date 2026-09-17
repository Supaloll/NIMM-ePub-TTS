# -*- coding: utf-8 -*-
"""Genere NEUTTS_VOICES dans modules/tts.py a partir des extraits du service.

POURQUOI UN GENERATEUR : les voix NeuTTS sont des EXTRAITS (109 aujourd'hui,
d'autres demain), et chaque extrait doit apparaitre dans le catalogue du
lecteur avec le MEME prenom, le MEME genre et les MEMES etoiles que la voix
deja connue -- sinon plus personne ne s'y retrouve a l'oreille. Saisir cela a
la main serait long et faux.

D'ou ce script, qui croise deux sources uniques :
  - la liste des extraits vient DU SERVICE (`_repertorier_references`) ;
  - les prenoms, genres et etoiles viennent du catalogue existant, par le meme
    rapprochement que `_rapprocher_neutts_xtts.py` (fonctions importees, pas
    recopiees).

Le bloc est ecrit entre les reperes `DEBUT CATALOGUE NEUTTS` et
`FIN CATALOGUE NEUTTS` de modules/tts.py : tout ce qui est entre les deux est
reconstruit, le reste du fichier n'est pas touche.

Usage :
    python test_voix/_generer_catalogue_neutts.py            # rapport seul
    python test_voix/_generer_catalogue_neutts.py --ecrire   # ecrit vraiment

Un extrait sans voix connue est REFUSE (le script s'arrete) : il faut d'abord
savoir a quelle voix il correspond, on ne l'invente pas.
"""

import argparse
import importlib.util
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _rapprocher_neutts_xtts import (candidats, entrees_du_catalogue,  # noqa: E402
                                     identifiants_references)

TTS = RACINE / 'modules' / 'tts.py'
DEBUT = '# --- DEBUT CATALOGUE NEUTTS (genere) ---'
FIN = '# --- FIN CATALOGUE NEUTTS ---'
# La meme convention que les autres moteurs : le drapeau + le pays + le moteur
# entre parentheses. C'est ce qui distingue « Adele - France (NeuTTS) » de
# « Adele - France (XTTS) » : deux voix differentes, un meme prenom.
REGION = '\\U0001F1EB\\U0001F1F7 France (NeuTTS)'

EN_TETE = """# --- DEBUT CATALOGUE NEUTTS (genere) ---
# Ce bloc est GENERE par test_voix/_generer_catalogue_neutts.py : ne pas
# l'editer a la main. Il est reconstruit a partir des extraits reellement
# presents dans neutts_service\\references\\ (source unique), en HERITANT des
# prenoms, genres et etoiles des voix deja cataloguees (memes identifiants) :
# une voix doit porter le meme prenom d'un moteur a l'autre, sinon plus
# personne ne s'y retrouve a l'oreille. La region, elle, distingue les
# moteurs (« France (NeuTTS) » face a « France (XTTS) »).
#
# ATTENTION aux ACCENTS : les mentions « accent paysan / anglais / ... » du
# catalogue XTTS decrivaient ce que Laurent entendait SUR XTTS. Elles ne sont
# PAS reprises ici : NeuTTS prononce avec SON modele francais, donc l'accent
# s'efface (constat d'ecoute du 16/09/2026) et il faudra le renseigner a
# nouveau, a l'oreille, dans la fenetre « Ecouter les voix »."""


def construire_bloc(connu):
    """(bloc de code, nombre de voix, extraits sans voix connue)."""
    references = identifiants_references()      # tel que le SERVICE les voit
    lignes = []
    nombre = 0
    sans_voix = []
    for dossier in sorted(references):
        identifiants = references[dossier]
        lignes.append('    # --- %s : %d voix ---' % (dossier, len(identifiants)))
        for identifiant in identifiants:
            trouve = None
            for candidat in candidats(identifiant):
                if candidat in connu:
                    trouve = connu[candidat]
                    break
            if not trouve:
                sans_voix.append('%s / %s' % (dossier, identifiant))
                continue
            prenom, genre, etoiles, _region = trouve
            lignes.append(
                '    {"id": "neutts:%s", "name": "%s", "region": "%s", '
                '"gender": "%s", "stars": %d},'
                % (identifiant, prenom, REGION, genre,
                   etoiles if etoiles is not None else 0))
            nombre += 1
    bloc = (EN_TETE + '\nNEUTTS_VOICES = [\n' + '\n'.join(lignes)
            + '\n]\n' + FIN + '\n')
    return bloc, nombre, sans_voix


def main():
    analyseur = argparse.ArgumentParser(
        description="Genere NEUTTS_VOICES dans modules/tts.py.")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit le catalogue (sans cela : rapport seul)")
    options = analyseur.parse_args()

    connu = {}
    kokoro = entrees_du_catalogue('KOKORO_VOICES')
    xtts = entrees_du_catalogue('XTTS_VOICES')
    connu.update(xtts)
    connu.update(kokoro)

    print('')
    print('=' * 70)
    print('CATALOGUE NEUTTS -- generation dans modules/tts.py')
    print('=' * 70)
    print('catalogue lu : %d voix Kokoro + %d voix XTTS' % (len(kokoro), len(xtts)))

    bloc, nombre, sans_voix = construire_bloc(connu)

    print('')
    for ligne in bloc.splitlines():
        if ligne.strip().startswith('# ---'):
            print('  %s' % ligne.strip())
    print('')
    print('voix a ecrire : %d' % nombre)

    if sans_voix:
        print('')
        print('REFUS : %d extrait(s) sans voix connue dans le catalogue :'
              % len(sans_voix))
        for reference in sans_voix[:20]:
            print('    %s' % reference)
        print('')
        print("On n'invente pas un prenom : il faut d'abord rattacher cet")
        print('extrait a une voix connue (ou lui en donner une).')
        return 1

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete ecrit -- ajoute --ecrire)")
        return 0

    source = TTS.read_text(encoding='utf-8')
    if DEBUT not in source or FIN not in source:
        print('')
        print('ERR : les reperes DEBUT/FIN CATALOGUE NEUTTS sont absents de')
        print('      modules/tts.py : le bloc ne peut pas etre remplace.')
        return 1
    debut = source.index(DEBUT)
    fin = source.index(FIN) + len(FIN)
    TTS.write_text(source[:debut] + bloc.rstrip('\n') + source[fin:],
                   encoding='utf-8')
    print('')
    print('modules/tts.py mis a jour : %d voix NeuTTS.' % nombre)
    print('Verifie ensuite : python -m py_compile modules/tts.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())

