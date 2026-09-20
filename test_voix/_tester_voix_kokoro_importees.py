# -*- coding: utf-8 -*-
"""VERIFIER QUE LES VOIX KOKORO IMPORTEES PARLENT VRAIMENT (20/09/2026).

Un fichier de voix bien forme ne prouve pas grand-chose : ce qui compte, c'est
que le MOTEUR DU LECTEUR produise du son avec ce timbre. Ce script fait donc
parler Kokoro par le VRAI chemin du lecteur (modules/tts.py, lang="fr-fr"
force, comme dans l'application), voix par voix, et mesure ce qui sort :

    - de l'audio non vide (un timbre tout a zero sortirait muet) ;
    - un WAV valide, d'une duree plausible pour la phrase ;
    - un niveau de parole reel (pas du silence, pas un souffle).

Il ne sauvegarde rien par defaut (l'ecoute se fait dans le lecteur, avec le
bouton ▶ de « Ecouter les voix ») ; `--dossier <chemin>` ecrit les WAV pour
les ecouter a la suite.

Pourquoi ce script existe : le 20/09/2026, 10 voix a accent allemand
fabriquees dans NIMM Voix ont ete importees (voices-v1.0.bin, 84 -> 94 voix,
plus 10 lignes dans KOKORO_VOICES). Le nom de ces voix commence par `fa_`.

Usage :
    python test_voix/_tester_voix_kokoro_importees.py
    python test_voix/_tester_voix_kokoro_importees.py --prefixe fa_
    python test_voix/_tester_voix_kokoro_importees.py --voix fa_eva,fa_bernd
    python test_voix/_tester_voix_kokoro_importees.py --dossier "%TEMP%\\voix_allemandes"
"""

import argparse
import asyncio
import io
import os
import struct
import sys
import time
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import tts                                                    # noqa: E402

# Une phrase courte, mais une VRAIE phrase francaise : c'est ce que le lecteur
# enverra, et c'est ce qui fait apparaitre l'accent.
PHRASE = "Le soleil se couchait derriere les collines."

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def mesure_wav(octets: bytes) -> tuple:
    """(duree en secondes, crete en dBFS) d'un WAV, ou (0, -999) si illisible."""
    try:
        with wave.open(io.BytesIO(octets)) as w:
            cadence = w.getframerate()
            largeur = w.getsampwidth()
            images = w.readframes(w.getnframes())
    except Exception as e:                                   # noqa: BLE001
        return 0.0, -999.0, str(e)
    if largeur != 2 or not images:
        return 0.0, -999.0, 'format inattendu'
    valeurs = struct.unpack('<%dh' % (len(images) // 2), images)
    crete = max(abs(v) for v in valeurs) / 32768.0
    import math
    dbfs = 20.0 * math.log10(crete) if crete > 0 else -999.0
    return len(images) / 2.0 / cadence, dbfs, ''


def main():
    parseur = argparse.ArgumentParser(
        description="Fait parler Kokoro avec les voix importees et mesure le son.")
    parseur.add_argument('--prefixe', default='fa_',
                         help='prefixe des voix a tester (defaut : fa_, accent allemand)')
    parseur.add_argument('--voix', default='',
                         help='noms explicites, separes par des virgules (prioritaire)')
    parseur.add_argument('--dossier', default='',
                         help='ecrit les WAV dans ce dossier (sinon rien n est garde)')
    args = parseur.parse_args()

    if args.voix:
        voulues = [v.strip() for v in args.voix.split(',') if v.strip()]
        lignes = [v for v in tts.KOKORO_VOICES
                  if v['id'].replace('kokoro:', '') in voulues]
    else:
        lignes = [v for v in tts.KOKORO_VOICES
                  if v['id'].replace('kokoro:', '').startswith(args.prefixe)]

    print('=' * 66)
    print('VOIX KOKORO IMPORTEES : parlent-elles vraiment ?')
    print('=' * 66)
    print('  phrase testee : ' + PHRASE)
    print('  voix a tester : %d' % len(lignes))
    for v in lignes:
        print('    - %-28s %s (%s)' % (v['id'], v['name'], v['gender']))
    if not lignes:
        print('')
        print('Aucune voix a tester : verifier le prefixe ou --voix.')
        return 1

    dossier = Path(args.dossier) if args.dossier else None
    if dossier:
        dossier.mkdir(parents=True, exist_ok=True)

    print('')
    print('1) le moteur parle, voix par voix')
    print('   %-28s %8s %9s %s' % ('voix', 'duree', 'crete', 'verdict'))
    for v in lignes:
        identifiant = v['id']
        nom_court = identifiant.replace('kokoro:', '')
        debut = time.time()
        try:
            octets = asyncio.run(tts.synthesize_kokoro(PHRASE, identifiant))
        except Exception as e:                               # noqa: BLE001
            verifier('%s repond' % nom_court, False, e)
            continue
        duree, dbfs, souci = mesure_wav(octets)
        secondes = time.time() - debut
        # Bornes larges et volontaires : la phrase fait ~2,5 s de voix. On
        # cherche un SILENCE ou un plantage, pas a juger la beaute du son
        # (cela, c'est l'oreille de Laurent, dans le lecteur).
        bon = (len(octets) > 1000 and not souci
               and 0.5 <= duree <= 20.0 and dbfs > -40.0)
        print('   %-28s %7.2fs %8.1f dB %s'
              % (nom_court, duree, dbfs, 'OK' if bon else 'ECHEC'))
        verifier('%s produit de l audio (%.2f s, %.1f dBFS, %.1f s de calcul)'
                 % (nom_court, duree, dbfs, secondes), bon, souci or len(octets))
        if dossier and octets:
            (dossier / (nom_court + '.wav')).write_bytes(octets)

    print('')
    if dossier:
        print('   WAV ecrits dans : ' + str(dossier))
    print('TOUT EST OK' if ECHECS == 0 else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
