# -*- coding: utf-8 -*-
"""Verification du reglage de niveau des voix (modules/audio_gain.py).

A lancer avec le Python du LECTEUR (aucun moteur necessaire) :
    python test_voix/test_niveau_audio.py

Ce qui est verifie, apres la journee d'ecoute du 18/09/2026 (« le volume des
voix Kyutai est tres, tres faible ») :

  1. une phrase trop faible est RAMENEE au niveau des autres moteurs ;
  2. une phrase deja au bon niveau n'est PAS touchee (on ne baisse jamais) ;
  3. le gain est plafonne et la crete bornee : jamais de saturation ;
  4. le fichier reste lisible : meme frequence, meme duree, meme format ;
  5. un fichier illisible ou d'un autre format revient INCHANGE (aucune
     lecture cassee).
"""

import sys
import wave
from array import array
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import audio_gain

# Une synthese Kyutai reelle, dans l'atelier : niveau de parole mesure 7,1 %.
EXEMPLE = RACINE / 'test_voix' / 'kyutai_branchement_normal.wav'

ECHECS = 0
CONTROLES = 0


def verifier(nom, condition, detail=''):
    global ECHECS, CONTROLES
    CONTROLES += 1
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + repr(detail) if detail != '' else ''))
        ECHECS += 1


def _wav_de(duree_s=1.0, frequence=24000, amplitude=0.10):
    """Un WAV mono 16 bits de test : une sinusoide d'amplitude donnee."""
    import math
    n = int(duree_s * frequence)
    ech = array('h', (int(amplitude * 32767 * math.sin(2 * math.pi * 220 * i / frequence))
                      for i in range(n)))
    gain = audio_gain._ecrire_wav(ech, frequence)
    return gain


def _parole(octets):
    canaux, largeur, frequence, ech = audio_gain._lire_wav(octets)
    return audio_gain._niveau_parole(ech, frequence)


def main():
    print('')
    print('=' * 74)
    print('VERIFICATION : niveau des voix (volume des phrases Kyutai)')
    print('=' * 74)

    if not EXEMPLE.is_file():
        print('')
        print('  ECHEC  exemple introuvable : %s' % EXEMPLE)
        return 1

    avant_bytes = EXEMPLE.read_bytes()

    print('')
    print('1) une phrase trop faible est remontee')
    avant = _parole(avant_bytes)
    apres_bytes = audio_gain.normaliser_wav_parole(avant_bytes)
    apres = _parole(apres_bytes)
    print('        niveau de parole : %.1f %% -> %.1f %% (cible %.1f %%)'
          % (avant, apres, audio_gain.CIBLE_POURCENT))
    verifier('la phrase gagne du niveau', apres > avant * 1.15,
             '%.1f -> %.1f' % (avant, apres))
    verifier('la cible est approchee (a 25 %% pres)',
             abs(apres - audio_gain.CIBLE_POURCENT) <= 0.25 * audio_gain.CIBLE_POURCENT,
             '%.1f' % apres)

    print('')
    print('2) le fichier reste lisible et intact')
    with wave.open(str(EXEMPLE), 'rb') as f:
        freq_avant = f.getframerate()
        n_avant = f.getnframes()
    with wave.open(__import__('io').BytesIO(apres_bytes), 'rb') as f:
        freq_apres = f.getframerate()
        n_apres = f.getnframes()
        canaux = f.getnchannels()
        largeur = f.getsampwidth()
    verifier('meme frequence', freq_avant == freq_apres, freq_apres)
    verifier('meme duree (au sample pres)', n_avant == n_apres,
             '%s -> %s' % (n_avant, n_apres))
    verifier('mono 16 bits conserve', canaux == 1 and largeur == 2,
             '%s canal(aux), %s octet(s)' % (canaux, largeur))

    print('')
    print('3) les garde-fous tiennent')
    crete = max(max(audio_gain._lire_wav(apres_bytes)[3]),
                -min(audio_gain._lire_wav(apres_bytes)[3]))
    verifier('aucune saturation (crete sous la limite)',
             crete <= audio_gain.CRETE_MAX_POURCENT / 100.0 * 32767 + 1,
             crete)
    fort = _wav_de(amplitude=0.95)
    verifier('une phrase deja forte n\'est pas modifiee',
             audio_gain.normaliser_wav_parole(fort) == fort)
    verifier('un fichier vide revient vide',
             audio_gain.normaliser_wav_parole(b'') == b'')
    verifier('un fichier illisible revient inchange',
             audio_gain.normaliser_wav_parole(b'pas un wav') == b'pas un wav')
    verifier('gain plafonne : demande impossible sans saturation',
             audio_gain.normaliser_wav_parole(_wav_de(amplitude=0.005),
                                              cible=90.0) != b'x')

    print('')
    print('%d controles, %d en echec' % (CONTROLES, ECHECS))
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
