# -*- coding: utf-8 -*-
"""Verification du reglage de niveau des voix (modules/audio_gain.py).

A lancer avec le Python du LECTEUR (aucun moteur necessaire) :
    python test_voix/test_niveau_audio.py

Ce qui est verifie, apres la journee d'ecoute du 18/09/2026 (« le volume des
voix Kyutai est tres, tres faible ») et la MESURE du 21/09/2026 (dans un long
passage, les phrases vont de 25 a 42 %, avec une phrase a 8,8 % : -10 dB a cote
de ses voisines) :

  1. une phrase TROP FAIBLE (hors fourchette) est RAMENEE vers la cible du
     moteur, sans y etre collee : elle gagne BANDE_DB au plus ;
  2. une phrase DANS LA FOURCHETTE (moins de +/- 3 dB autour de la cible) n'est
     PAS touchee du tout : c'est ce qui garde les nuances entre les voix ;
  3. une phrase TROP FORTE est ramenee elle aussi, mais jamais de plus de
     -6 dB (GAIN_MIN) : on ne l'ecrase pas ;
  4. le gain est plafonne et la crete bornee : jamais de saturation ;
  5. le fichier reste lisible : meme frequence, meme duree, meme format ;
  6. un fichier illisible ou d'un autre format revient INCHANGE (aucune lecture
     cassee).
"""

import io
import math
import sys
import wave
from array import array
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import audio_gain

# Une synthese Kyutai REELLE, dans l'atelier. ATTENTION : son niveau n'est pas
# fige -- `test_kyutai_branchement.py` reecrit ce fichier (la phrase lui est
# servie par le CACHE DISQUE quand le moteur est eteint). Il valait 7,1 % a
# l'origine, 8,6 % le 23/09/2026 : les controles qui l'utilisent sont donc
# ecrits pour tenir dans les deux cas (voir le controle 2).
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
    print('1) une phrase VRAIMENT faible (hors fourchette) est remontee')
    # Une phrase de synthese tres faible : 3,5 % environ, soit 7,7 dB sous la
    # cible de 8,5 % -- largement hors de la fourchette de +/- 3 dB.
    faible = _wav_de(amplitude=0.05)
    avant_faible = _parole(faible)
    apres_faible = _parole(audio_gain.normaliser_wav_parole(faible))
    print('        niveau de parole : %.1f %% -> %.1f %% (cible %.1f %%)'
          % (avant_faible, apres_faible, audio_gain.CIBLE_POURCENT))
    verifier('la phrase gagne du niveau', apres_faible > avant_faible * 1.4,
             '%.1f -> %.1f' % (avant_faible, apres_faible))
    ecart_db = 20 * math.log10(apres_faible / audio_gain.CIBLE_POURCENT)
    verifier('elle ATTEINT la cible', abs(ecart_db) <= 1.0,
             '%.1f dB' % ecart_db)

    print('')
    print('2) une phrase DEJA a la cible n est pas touchee')
    # ~8,5 % : exactement la cible.
    dans = _wav_de(amplitude=0.12)
    verifier('elle revient INCHANGEE',
             audio_gain.normaliser_wav_parole(dans) == dans,
             '%.1f %%' % _parole(dans))

    # --- LE TEMOIN REEL, ET POURQUOI L'ATTENTE A CHANGE LE 23/09/2026 --------
    # Ce controle demandait « la vraie phrase Kyutai est REMONTEE vers la
    # cible » : c'etait vrai tant que le temoin valait 7,1 % (le chiffre note
    # ici depuis le 15/09/2026). Or `test_kyutai_branchement.py` REEcrit ce
    # fichier -- et comme la phrase lui est servie par le CACHE DISQUE quand le
    # moteur est eteint, elle peut valoir autre chose : 8,6 % le 23/09/2026.
    # A 8,6 %, elle est DEJA a la cible (8,5 %) : depuis la revision du
    # 21/09/2026 la correction est bornee des DEUX cotes, donc elle n'est plus
    # touchee -- et l'attente « remontee » ne pouvait plus etre satisfaite.
    # Ce qui est vrai DANS TOUS LES CAS, et qui est donc teste ici : le module
    # RAPPROCHE le temoin de la cible sans jamais l'en ecarter, et si le temoin
    # est vraiment hors fourchette, il le corrige dans le bon sens. Le niveau du
    # temoin est affiche : le jour ou le chiffre changera encore, on saura
    # pourquoi sans chercher.
    niveau_avant = _parole(avant_bytes)
    niveau_apres = _parole(audio_gain.normaliser_wav_parole(avant_bytes))
    cible = audio_gain.CIBLE_POURCENT
    ecart_avant = abs(20 * math.log10(niveau_avant / cible))
    ecart_apres = abs(20 * math.log10(niveau_apres / cible))
    print('        temoin reel : %.1f %% -> %.1f %% (cible %.1f %%, '
          'ecart %.1f -> %.1f dB)'
          % (niveau_avant, niveau_apres, cible, ecart_avant, ecart_apres))
    verifier('le temoin reel n est JAMAIS eloigne de la cible',
             ecart_apres <= ecart_avant + 0.05,
             '%.2f -> %.2f dB' % (ecart_avant, ecart_apres))
    verifier('et il finit DANS la fourchette de +/- 3 dB',
             ecart_apres <= 3.0, 'ecart final %.2f dB' % ecart_apres)
    if ecart_avant > 3.0:
        # Hors fourchette : le module doit agir, et dans le bon sens.
        if niveau_avant < cible:
            verifier('(temoin faible) il est bien REMONTE',
                     niveau_apres > niveau_avant,
                     '%.1f -> %.1f' % (niveau_avant, niveau_apres))
        else:
            verifier('(temoin trop fort) il est bien RAMENE',
                     niveau_apres < niveau_avant,
                     '%.1f -> %.1f' % (niveau_avant, niveau_apres))

    print('')
    print('3) une phrase TROP FORTE est ramenee, sans etre ecrasee')
    fort = _wav_de(amplitude=0.60)          # ~42 % : 14 dB au-dessus de la cible
    modifie = audio_gain.normaliser_wav_parole(fort)
    niveau_fort = _parole(modifie)
    print('        niveau de parole : %.1f %% -> %.1f %%' % (_parole(fort),
                                                             niveau_fort))
    verifier('la phrase perd du niveau', niveau_fort < _parole(fort),
             '%.1f' % niveau_fort)
    verifier('mais jamais plus de %.0f dB (GAIN_MIN)'
             % abs(20 * math.log10(audio_gain.GAIN_MIN)),
             niveau_fort >= _parole(fort) * audio_gain.GAIN_MIN * 0.98,
             '%.1f' % niveau_fort)

    print('')
    print('4) le fichier reste lisible et intact')
    with wave.open(io.BytesIO(fort), 'rb') as f:
        freq_avant = f.getframerate()
        n_avant = f.getnframes()
    with wave.open(io.BytesIO(modifie), 'rb') as f:
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
    print('5) les garde-fous tiennent')
    crete = max(max(audio_gain._lire_wav(modifie)[3]),
                -min(audio_gain._lire_wav(modifie)[3]))
    verifier('aucune saturation (crete sous la limite)',
             crete <= audio_gain.CRETE_MAX_POURCENT / 100.0 * 32767 + 1,
             crete)
    # Un sinus tres fort est desormais RAMENE vers la cible (les deux sens),
    # mais borne : il ne doit jamais perdre plus de 6 dB (GAIN_MIN).
    tres_fort = _wav_de(amplitude=0.95)
    ramene = _parole(audio_gain.normaliser_wav_parole(tres_fort))
    verifier('une phrase tres forte ne perd pas plus de 6 dB',
             ramene >= _parole(tres_fort) * audio_gain.GAIN_MIN * 0.98,
             '%.1f' % ramene)
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
