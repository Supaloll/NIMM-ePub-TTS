# -*- coding: utf-8 -*-
"""Verifie la coupure du BABIL isole par un silence (service XTTS, 16/09/2026).

Motifs MESURES sur le moteur en marche (test_voix/_mesurer_phrases_courtes.py) :
    « Non. »              -> parole 0,02-0,28 | SILENCE 0,34 | residu 0,62-0,80
    « ...pour la nuit ? » -> parole 0,00-1,82 | SILENCE 0,36 | residu 2,18-2,24
Sur une phrase normale, les pauses internes sont bien plus courtes (0,04 s) et
un long silence est suivi d'une VRAIE suite de phrase : rien ne doit etre coupe.

La fonction est extraite DE servir_xtts.py (jamais recopiee). Aucun moteur
n'est charge : on travaille sur des signaux fabriques a la main.

Usage : python test_voix/test_rogner_babil_xtts.py
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np                                              # noqa: E402

SERVICE = RACINE / 'xtts_service' / 'servir_xtts.py'

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def espace_du_service():
    source = SERVICE.read_text(encoding='utf-8')
    bornes = [
        ('MAX_CARACTERES = 250', '# Une seule generation a la fois'),
        ('# ---- Deuxieme filet', 'def _lire_un_morceau'),
    ]
    espace = {}
    for debut_balise, fin_balise in bornes:
        fragment = source[source.index(debut_balise):source.index(fin_balise)]
        exec(compile(fragment, str(SERVICE), 'exec'), espace)
    return espace


def signal(frequence, morceaux):
    """Fabrique un signal : (duree_parole, duree_silence, ...) en secondes."""
    donnees = []
    for rang, duree in enumerate(morceaux):
        nombre = int(duree * frequence)
        if rang % 2 == 0:                     # parole : signal audible
            donnees.append(np.full(nombre, 0.4, dtype=np.float32))
        else:                                 # silence
            donnees.append(np.zeros(nombre, dtype=np.float32))
    return np.concatenate(donnees) if donnees else np.zeros(0, dtype=np.float32)


def duree_de(sons, frequence):
    return sons.size / float(frequence)


def main_verifications():
    espace = espace_du_service()
    rogner = espace['rogner_babil_apres_silence']
    frequence = espace['FREQUENCE']
    seuil_silence = espace['SEUIL_SILENCE_LONG_S']
    residu_max = espace['RESIDU_MAX_S']
    queue = espace['SILENCE_QUEUE_S']

    print('')
    print('1) les motifs MESURES sont bien coupes')
    # « Non. » : 0,26 s de mot, 0,34 s de silence, 0,18 s de babil.
    non = signal(frequence, (0.26, 0.34, 0.18))
    coupe = rogner(non)
    obtenue = duree_de(coupe, frequence)
    verifier('« Non. » : le residu de 0,18 s est coupe',
             abs(obtenue - (0.26 + queue)) < 0.03,
             '%.2f s au lieu de %.2f s' % (obtenue, duree_de(non, frequence)))
    # « ...pour la nuit ? » : 1,80 s de phrase, 0,36 s de silence, 0,06 s de babil.
    nuit = signal(frequence, (1.80, 0.36, 0.06))
    obtenue = duree_de(rogner(nuit), frequence)
    verifier('« ...pour la nuit ? » : le micro-residu est coupe',
             abs(obtenue - (1.80 + queue)) < 0.03, '%.2f s' % obtenue)

    print('')
    print('2) une phrase NORMALE n est jamais touchee')
    # Long silence en pleine phrase, suivi d'une vraie suite (comme mesure).
    longue = signal(frequence, (1.90, 0.40, 2.04))
    verifier('un long silence suivi d une vraie suite : rien n est coupe',
             rogner(longue).size == longue.size,
             '%.2f s / %.2f s' % (duree_de(rogner(longue), frequence),
                                  duree_de(longue, frequence)))
    # Pauses internes courtes (0,04 s mesures entre groupes de mots).
    normale = signal(frequence, (0.90, 0.04, 0.90, 0.04, 0.90))
    verifier('les pauses internes courtes ne declenchent rien',
             rogner(normale).size == normale.size)
    # Une seule phrase d'un trait.
    dune_trait = signal(frequence, (2.0,))
    verifier('une phrase sans silence : rien n est coupe',
             rogner(dune_trait).size == dune_trait.size)

    print('')
    print('3) cas limites')
    verifier('audio vide : renvoye tel quel',
             rogner(np.zeros(0, dtype=np.float32)).size == 0)
    verifier('silence total : renvoye tel quel (rogner_queue s en occupe)',
             rogner(np.zeros(int(2.0 * frequence), dtype=np.float32)).size
             == int(2.0 * frequence))
    # Un silence long mais un residu PLUS LONG que la limite = vraie fin.
    vraie_fin = signal(frequence, (1.0, 0.40, 0.90))
    verifier('residu plus long que %.2f s : considere comme une vraie phrase'
             % residu_max, rogner(vraie_fin).size == vraie_fin.size,
             '%.2f s de residu' % 0.90)
    # Une interruption au tout debut ne doit pas tout couper.
    debut = signal(frequence, (0.10, 0.40, 0.10))
    verifier('le motif cherche le DERNIER silence long, pas le premier',
             rogner(debut).size > 0)
    # Le seuil est bien celui annonce par le service.
    verifier('le seuil de silence long est %.2f s' % seuil_silence,
             abs(seuil_silence - 0.30) < 0.001, seuil_silence)

    print('')
    print('4) le resultat reste audible (la parole est conservee)')
    garde = rogner(signal(frequence, (1.80, 0.36, 0.06)))
    verifier('les 1,80 s de parole sont intactes',
             np.max(np.abs(garde)) > 0.3 and
             duree_de(garde, frequence) >= 1.80,
             duree_de(garde, frequence))


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : coupure du babil isole par un silence (XTTS)')
    print('=' * 66)
    main_verifications()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    sys.exit(0 if ECHECS == 0 else 1)
