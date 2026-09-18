# -*- coding: utf-8 -*-
"""Vérification des PHRASES QUI NE SONT QU'UNE INCISE (18/09/2026).

A lancer avec le Python du LECTEUR (aucun moteur nécessaire) :
    python test_voix/test_incise_seule.py

Pourquoi : le découpage sépare les phrases au « ! » et au « ? », donc une incise
se retrouve parfois seule en phrase à part entière (« — Ah ! vraiment ? dit
Monte-Cristo. » → la dernière phrase est « dit Monte-Cristo. »). Elle ne peut pas
être vidée sans faire disparaître la phrase : le lecteur joue un **court silence**
(`modules/silence.py`), décidé par `_est_incise_seule()` dans `main.py`.

Ce qui est vérifié :
  1. les phrases-incises sont **détectées** (dont les trois exemples de Laurent) ;
  2. les phrases **normales** ne le sont jamais (sinon on perdrait du texte !) ;
  3. le silence produit est un WAV valide, de la durée voulue, vraiment muet ;
  4. la détection est **cohérente avec le nettoyage** : ce qui est déclaré
     « incise seule » est bien ce que le nettoyage viderait.
"""

import io
import sys
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from main import _est_incise_seule                                 # noqa: E402
from modules.silence import wav_silence, SILENCE_INCISE_MS         # noqa: E402

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


def main():
    print('')
    print('=' * 74)
    print('VERIFICATION : les phrases qui ne sont qu une incise (court silence)')
    print('=' * 74)

    print('')
    print('1) les cas de Laurent sont bien reconnus')
    for phrase in ('dit Monte-Cristo.',
                   'dit le comte.',
                   'demanda Morrel.',
                   'ajouta Valentine en s\u2019adressant \u00e0 Noirtier.',
                   '\u2014 dit-il.'):
        verifier('%r' % phrase[:44], _est_incise_seule(phrase))

    print('')
    print('2) une phrase NORMALE n est jamais prise pour une incise seule')
    for phrase in ('\u2014 Ah ! vraiment ?',
                   'dit Monte-Cristo en souriant, puis il partit.',
                   'Le comte regarda Morrel avec attention.',
                   '\u2014 Il partit, dit-il.',
                   'Il arriva. Elle partit.'):
        verifier('%r' % phrase[:44], not _est_incise_seule(phrase))

    print('')
    print('3) le silence produit est valide et vraiment muet')
    octets = wav_silence()
    with wave.open(io.BytesIO(octets), 'rb') as f:
        canaux = f.getnchannels()
        largeur = f.getsampwidth()
        frequence = f.getframerate()
        donnees = f.readframes(f.getnframes())
        duree = f.getnframes() / float(frequence)
    verifier('WAV mono 16 bits', canaux == 1 and largeur == 2,
             (canaux, largeur))
    verifier('duree attendue (%.0f ms)' % SILENCE_INCISE_MS,
             abs(duree * 1000 - SILENCE_INCISE_MS) < 5, duree)
    verifier('aucun son (tous les echantillons a zero)',
             set(donnees) == {0}, len(set(donnees)))

    print('')
    print('4) coherence avec le nettoyage')
    from modules.incises import incises, retirer_incises
    phrase = 'dit Monte-Cristo.'
    verifier('l incise est bien vue par la regle', bool(incises(phrase)))
    verifier('le nettoyage garde la phrase entiere (garde-fou)',
             retirer_incises(phrase) == phrase)

    print('')
    print('%d controles, %d en echec' % (CONTROLES, ECHECS))
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
