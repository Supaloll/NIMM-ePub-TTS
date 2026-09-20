# -*- coding: utf-8 -*-
"""IMPORTER UNE BANQUE DE VOIX KOKORO DANS LE LECTEUR (20/09/2026).

Un lecteur Kokoro (kokoro-onnx) ne charge QU'UN fichier de voix. Pour utiliser
les voix fabriquees dans l'atelier NIMM Voix, il faut donc y AJOUTER leurs
timbres : c'est exactement ce que fait ce script.

    source : un fichier .bin de voix (npz, comme ceux de NIMM Voix)
    cible  : voices-v1.0.bin, le fichier de reference du lecteur
             (54 voix officielles + 30 voix NIMM depuis le 12/09/2026)

CE QUI EST ECRIT, ET QUAND
    - par defaut : RIEN. Le script affiche seulement ce qu'il ferait ;
    - avec --ecrire : il copie d'abord la cible en
      .bak_avant_<quoi>_<AAAAMMJJ> (ce fichier est la reference de TOUTES les
      voix : sans copie, une erreur d'ecriture les emporterait toutes), puis
      ajoute les voix MANQUANTES, sans toucher aux autres.

CE QUI EST VERIFIE (avant ET apres l'ecriture)
    - la cible est un fichier de voix lisible, voix par voix ;
    - aucune voix de la source ne porte un nom DEJA present dans la cible
      (un doublon ecraserait une voix existante en silence) ;
    - chaque voix ajoutee a la bonne forme (510, 1, 256) en float32, et n'est
      pas vide (un timbre tout a zero serait muet) ;
    - APRES ecriture : chaque voix d'AVANT est identique (empreinte md5
      calculee voix par voix, comparee avant / apres), le compte est juste, et
      les voix ajoutees se relisent PAR LEUR NOM -- ce que fera le lecteur.

Usage :
    python test_voix/_importer_voix_kokoro.py
    python test_voix/_importer_voix_kokoro.py --source "G:\\chemin\\voix.bin" --ecrire
    python test_voix/_importer_voix_kokoro.py --quoi accent_allemand --ecrire
"""

import argparse
import hashlib
import shutil
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

import numpy as np

RACINE = Path(__file__).resolve().parent.parent
CIBLE_DEFAUT = RACINE / "voices-v1.0.bin"
SOURCE_DEFAUT = Path(r"G:\NIMM Voix\voix_generees\voices-accent-allemand.bin")

FORME_ATTENDUE = (510, 1, 256)

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def empreinte(tableau) -> str:
    """Empreinte d'une voix entiere (les octets du tableau, tels quels)."""
    return hashlib.md5(np.ascontiguousarray(tableau).tobytes()).hexdigest()


def lire_banque(chemin: Path) -> dict:
    """{nom: tableau} d'un fichier de voix. Rien n'est garde ouvert."""
    with np.load(str(chemin)) as charge:
        return {nom: charge[nom] for nom in charge.files}


def main():
    parseur = argparse.ArgumentParser(
        description="Ajoute des voix Kokoro au fichier de voix du lecteur.")
    parseur.add_argument('--source', default=str(SOURCE_DEFAUT),
                         help='fichier .bin de voix a importer (defaut : accent allemand)')
    parseur.add_argument('--cible', default=str(CIBLE_DEFAUT),
                         help='fichier de voix du lecteur (defaut : voices-v1.0.bin)')
    parseur.add_argument('--quoi', default='voix_kokoro',
                         help='mot de la copie de sauvegarde (.bak_avant_<quoi>_<date>)')
    parseur.add_argument('--ecrire', action='store_true',
                         help='ECRIT vraiment (sans cette option : simple apercu)')
    args = parseur.parse_args()

    source = Path(args.source)
    cible = Path(args.cible)

    print('=' * 66)
    print('IMPORT DE VOIX KOKORO'
          + ('' if args.ecrire else '  (APERCU : rien ne sera ecrit)'))
    print('=' * 66)
    print('  source : ' + str(source))
    print('  cible  : ' + str(cible))

    print('')
    print('1) les deux fichiers se lisent')
    verifier('la source existe', source.is_file(), source)
    verifier('la cible existe (fichier de reference du lecteur)',
             cible.is_file(), cible)
    if ECHECS:
        return 1
    avant = lire_banque(cible)
    nouvelles = lire_banque(source)
    verifier('la cible contient des voix', len(avant) > 0, len(avant))
    verifier('la source contient des voix', len(nouvelles) > 0, len(nouvelles))
    print('   cible : %d voix   |   source : %d voix'
          % (len(avant), len(nouvelles)))

    print('')
    print('2) les voix a ajouter')
    # Un nom DEJA pris ne doit jamais etre ecrase : ce serait une voix
    # existante qui disparaitrait sans que personne ne le voie.
    doublons = sorted(set(nouvelles) & set(avant))
    verifier('aucun nom en double entre la source et la cible', not doublons, doublons)
    a_ajouter = [nom for nom in nouvelles if nom not in doublons]

    for nom in a_ajouter:
        tableau = nouvelles[nom]
        bon = (tuple(tableau.shape) == FORME_ATTENDUE
               and tableau.dtype == np.float32
               and float(np.abs(tableau).max()) > 0)
        verifier('%-20s forme %s, float32, non vide' % (nom, tuple(tableau.shape)),
                 bon, tableau.dtype)

    # Les voix deja presentes ne sont meme pas relues : elles ne bougeront pas.
    empreintes_avant = {nom: empreinte(t) for nom, t in avant.items()}

    print('')
    print('3) ecriture')
    if not args.ecrire:
        print('   APERCU : %d voix seraient ajoutees (%d -> %d).'
              % (len(a_ajouter), len(avant), len(avant) + len(a_ajouter)))
        print('   Relancer avec --ecrire pour le faire vraiment.')
        return 0 if ECHECS == 0 else 1

    if not a_ajouter:
        print('   Rien a faire : toutes les voix de la source sont deja dans la cible.')
        return 0 if ECHECS == 0 else 1

    sauvegarde = cible.with_name(cible.name + '.bak_avant_' + args.quoi + '_'
                                 + date.today().strftime('%Y%m%d'))
    shutil.copy2(cible, sauvegarde)
    print('   copie de sauvegarde : ' + sauvegarde.name)

    melange = dict(avant)
    for nom in a_ajouter:
        melange[nom] = nouvelles[nom]

    # np.savez ajouterait « .npz » a un nom de fichier : on lui donne un
    # fichier OUVERT, pour ecrire exactement le nom demande.
    with open(str(cible), 'wb') as fichier:
        np.savez(fichier, **melange)

    print('')
    print('4) relecture de la cible, voix par voix')
    apres = lire_banque(cible)
    verifier('le compte est bon', len(apres) == len(melange),
             '%d au lieu de %d' % (len(apres), len(melange)))
    inchangees = [nom for nom, marque in empreintes_avant.items()
                  if nom in apres and empreinte(apres[nom]) == marque]
    verifier('aucune voix existante n a change (%d voix)' % len(avant),
             len(inchangees) == len(avant),
             sorted(set(avant) - set(inchangees)))
    relues = [nom for nom in a_ajouter
              if nom in apres and empreinte(apres[nom]) == empreinte(nouvelles[nom])]
    verifier('les voix importees se relisent par leur nom (%d)' % len(a_ajouter),
             len(relues) == len(a_ajouter), sorted(set(a_ajouter) - set(relues)))

    print('')
    print('   %d -> %d voix. Pour ANNULER : recopier %s sur %s.'
          % (len(avant), len(apres), sauvegarde.name, cible.name))
    print('   Les voix ne sont utilisables qu apres leur ajout dans modules/tts.py.')
    print('')
    print('TOUT EST OK' if ECHECS == 0 else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
