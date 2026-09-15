# -*- coding: utf-8 -*-
"""Verification du rognage du silence de QUEUE avant XTTS (15/09/2026).

A lancer avec le Python du LECTEUR (aucun moteur necessaire) :
    python test_voix/test_rogner_queue_xtts.py

Pourquoi : a l'ecoute d'une heure du Comte de Monte-Cristo, Laurent a trouve
les pauses de fin de phrase plus longues qu'avec Kokoro ou Edge, avec encore
des respirations en fin de phrase. Mesure d'atelier : chaque phrase XTTS se
terminait par un silence de 0,54 a 0,91 s (outil _mesurer_bords_xtts.py). Le
service ramene donc ce silence a SILENCE_QUEUE_S = 0,25 s, comme Edge dans le
lecteur (modules/audio_trim.py).

Ce test verifie deux choses :
  - le silence de queue est bien ramene a 0,25 s, quel que soit le silence
    d'origine ;
  - la PAROLE n'est jamais touchee (ni au debut, ni avant le dernier son),
    et rien n'est rallonge (un silence de queue deja court reste court).
"""

import os
import sys
from importlib.util import module_from_spec, spec_from_file_location

import numpy as np

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

CHEMIN = os.path.join(RACINE, 'xtts_service', 'servir_xtts.py')
_spec = spec_from_file_location('servir_xtts_test_queue', CHEMIN)
service = module_from_spec(_spec)
_spec.loader.exec_module(service)

FREQ = service.FREQUENCE
SEUIL = service.SEUIL_SON
PA = int(0.02 * FREQ)          # bloc d'analyse du service (20 ms)
MARGE = service.SILENCE_QUEUE_S
ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + repr(detail) if detail != '' else ''))
        ECHECS += 1


def son(duree, amplitude=0.3):
    """Un vrai son audible (sinus) de la duree demandee."""
    n = int(duree * FREQ)
    t = np.arange(n) / FREQ
    return (amplitude * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def silence(duree):
    return np.zeros(int(duree * FREQ), dtype=np.float32)


def queue(signal):
    """Silence de fin mesure (meme methode que l'outil d'atelier)."""
    dernier = -1
    for debut in range(0, signal.size, PA):
        bloc = signal[debut:debut + PA]
        if bloc.size and float(np.max(np.abs(bloc))) >= SEUIL:
            dernier = debut
    if dernier < 0:
        return signal.size / float(FREQ)
    return (signal.size - (dernier + PA)) / float(FREQ)


def main():
    print('')
    print('1) le silence de queue est ramene a %.2f s' % MARGE)
    for origine in (0.54, 0.60, 0.91, 2.00):
        sig = np.concatenate([son(0.5), silence(origine)])
        obtenu = service.rogner_queue(sig, FREQ)
        q = queue(obtenu)
        verifier('queue de %.2f s d origine -> %.2f s' % (origine, q),
                 MARGE - 0.02 <= q <= MARGE + 0.03, q)

    print('')
    print('2) rien n est rallonge ni deforme')
    court = np.concatenate([son(0.5), silence(0.05)])
    obtenu = service.rogner_queue(court, FREQ)
    verifier('un silence de queue deja court reste court',
             obtenu.size == court.size and queue(obtenu) <= 0.06,
             queue(obtenu))

    sig = np.concatenate([silence(0.08), son(0.5), silence(1.0)])
    obtenu = service.rogner_queue(sig, FREQ)
    verifier('le silence de tete est conserve (0,08 s)',
             queue(obtenu) >= MARGE - 0.02 and
             (obtenu.size - int(MARGE * FREQ)) > int(0.5 * FREQ),
             obtenu.size)
    verifier('aucun echantillon modifie avant le dernier son',
             np.array_equal(obtenu[:int(0.58 * FREQ)], sig[:int(0.58 * FREQ)]))

    print('')
    print('3) plusieurs sons : on garde jusqu au DERNIER son')
    deux = np.concatenate([son(0.3), silence(0.4), son(0.3), silence(1.2)])
    obtenu = service.rogner_queue(deux, FREQ)
    verifier('la deuxieme phrase est conservee (pas de coupe au 1er son)',
             obtenu.size > deux.size - FREQ, obtenu.size)
    verifier('le grand silence final est retire',
             queue(obtenu) <= MARGE + 0.03, queue(obtenu))

    print('')
    print('4) securite : jamais de plantage, jamais d audio perdu')
    vide = np.zeros(0, dtype=np.float32)
    verifier('audio vide renvoye tel quel', service.rogner_queue(vide, FREQ).size == 0)
    tout_silence = silence(1.0)
    verifier('silence total renvoye tel quel',
             service.rogner_queue(tout_silence, FREQ).size == tout_silence.size)
    verifier('une entree inattendue ne fait pas planter',
             service.rogner_queue(None, FREQ) is None)
    bruit = (0.001 * np.sin(np.arange(int(1.0 * FREQ)))).astype(np.float32)
    verifier('un bruit sous le seuil est traite comme du silence',
             service.rogner_queue(bruit, FREQ).size == bruit.size)

    print('')
    print('5) le rognage est bien BRANCHE dans la generation')
    source = None
    try:
        import inspect
        source = inspect.getsource(service.generer_wav)
    except Exception as erreur:
        print('  (source illisible : %s)' % erreur)
    verifier('generer_wav appelle rogner_queue',
             source is not None and 'rogner_queue(' in source)

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    print('=' * 70)
    print('VERIFICATION : rognage du silence de queue XTTS (0,25 s)')
    print('=' * 70)
    sys.exit(main())
