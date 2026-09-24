# -*- coding: utf-8 -*-
"""Verification du rognage du silence de QUEUE des phrases Kyutai (23/09/2026).

A lancer avec le Python du LECTEUR (aucun moteur, aucune carte graphique) :
    python test_voix/test_rogner_queue_kyutai.py

Pourquoi : le modele Kyutai ne rogne pas ses bords -- il garde la respiration
qu'il vient de produire (0,30 a 0,43 s mesurees les 17 et 21/09/2026, queue
MEDIANE de 0,37 s sur les 300 WAV du cache le 23/09/2026). A l'ecoute de ce
jour-la, Laurent a trouve les pauses APRES LES POINTS trop longues et les SAUTS
DE LIGNE trop rapides : la queue est ramenee a 0,20 s par
`modules/audio_queue.py`, et la pause entre paragraphes remonte a 600 ms
(`frontend/app.js`).

Ce test verifie quatre choses :
  - le silence de queue est bien ramene a 0,20 s, quel que soit le silence
    d'origine ;
  - la PAROLE n'est jamais touchee (rien avant le dernier son, tete conservee),
    et rien n'est rallonge (une queue deja courte reste courte) ;
  - le format du WAV est inchange (canaux, bits, cadence) : c'est ce qui permet
    au lecteur de coller les phrases entre elles ;
  - le rognage est bien BRANCHE dans `synthesize_kyutai`, AVANT la mise en
    cache (comme le rognage d'Edge, verifie par le sujet « Rognage des
    silences de bord »).
"""

import array
import inspect
import io
import os
import sys
import wave

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

from modules import audio_queue
from modules import tts as _tts

FREQ = 24000                    # frequence du moteur Kyutai (Mimi)
MARGE = audio_queue.QUEUE_GARDEE_S
PA = int(0.01 * FREQ)           # bloc d'analyse de 10 ms
ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + repr(detail) if detail != '' else ''))
        ECHECS += 1


def son(duree, amplitude=0.3):
    """Un vrai son audible (sinus 220 Hz) en entiers 16 bits."""
    n = int(duree * FREQ)
    return array.array('h', [
        int(32767 * amplitude * (1 if (i // 24) % 2 else -1))
        for i in range(n)
    ])


def silence(duree):
    return array.array('h', [0] * int(duree * FREQ))


def en_wav(echantillons, frequence=FREQ, canaux=1):
    sortie = io.BytesIO()
    with wave.open(sortie, 'wb') as fichier:
        fichier.setnchannels(canaux)
        fichier.setsampwidth(2)
        fichier.setframerate(frequence)
        fichier.writeframes(echantillons.tobytes())
    return sortie.getvalue()


def lire_wav(octets):
    """(echantillons, canaux, bits, frequence) d'un WAV en memoire."""
    with wave.open(io.BytesIO(octets), 'rb') as fichier:
        canaux = fichier.getnchannels()
        bits = fichier.getsampwidth()
        frequence = fichier.getframerate()
        echantillons = array.array('h')
        echantillons.frombytes(fichier.readframes(fichier.getnframes()))
    return echantillons, canaux, bits, frequence


def queue(echantillons, canaux=1):
    """Silence de fin mesure, en secondes (meme methode que les outils)."""
    pas = max(canaux, PA)
    dernier = -1
    for debut in range(0, len(echantillons), pas):
        bloc = echantillons[debut:debut + pas]
        if bloc and max(abs(v) for v in bloc) / 32768.0 >= audio_queue.SEUIL_SON:
            dernier = debut
    if dernier < 0:
        return len(echantillons) / float(FREQ)
    return (len(echantillons) - (dernier + pas)) / float(FREQ)


def main():
    print('')
    print('1) le silence de queue est ramene a %.2f s (Kyutai : 0,30 a 1,15 s)'
          % MARGE)
    for origine in (0.30, 0.37, 0.43, 1.15):
        octets = en_wav(son(0.5) + silence(origine))
        obtenu = audio_queue.rogner_queue_wav(octets)
        echantillons, _c, _b, _f = lire_wav(obtenu)
        q = queue(echantillons)
        verifier('queue de %.2f s d origine -> %.2f s' % (origine, q),
                 MARGE - 0.02 <= q <= MARGE + 0.03, q)

    print('')
    print('2) rien n est rallonge, rien n est deforme')
    sig = son(0.5) + silence(0.43)
    octets = en_wav(sig)
    obtenu = audio_queue.rogner_queue_wav(octets)
    echantillons, _c, _b, _f = lire_wav(obtenu)
    verifier('le fichier rogne est plus COURT',
             len(echantillons) < len(sig),
             '%d -> %d echantillons' % (len(sig), len(echantillons)))
    verifier('aucun echantillon modifie avant le dernier son',
             list(echantillons[:int(0.55 * FREQ)]) ==
             list(sig[:int(0.55 * FREQ)]))
    court = en_wav(son(0.5) + silence(0.05))
    obtenu_court = audio_queue.rogner_queue_wav(court)
    verifier('une queue deja courte (0,05 s) est renvoyee telle quelle',
             obtenu_court == court)
    tete = en_wav(silence(0.08) + son(0.5) + silence(1.0))
    obtenu_tete = audio_queue.rogner_queue_wav(tete)
    ech_tete, _c, _b, _f = lire_wav(obtenu_tete)
    verifier('le silence de tete est conserve (0,08 s)',
             queue(ech_tete) <= MARGE + 0.03 and
             max(abs(v) for v in ech_tete[:int(0.05 * FREQ)]) == 0,
             queue(ech_tete))

    print('')
    print('3) plusieurs sons : on garde jusqu au DERNIER son')
    deux = en_wav(son(0.3) + silence(0.4) + son(0.3) + silence(1.2))
    obtenu_deux = audio_queue.rogner_queue_wav(deux)
    ech_deux, _c, _b, _f = lire_wav(obtenu_deux)
    verifier('la deuxieme phrase est conservee (pas de coupe au 1er son)',
             len(ech_deux) > 0.6 * FREQ, len(ech_deux))
    verifier('le grand silence final est retire',
             queue(ech_deux) <= MARGE + 0.03, queue(ech_deux))

    print('')
    print('4) le format du WAV ne change pas (le lecteur colle les phrases)')
    echantillons, canaux, bits, frequence = lire_wav(obtenu)
    verifier('mono, 16 bits, 24 kHz : identiques a l entree',
             (canaux, bits, frequence) == (1, 2, FREQ),
             (canaux, bits, frequence))

    print('')
    print('5) securite : jamais de plantage, jamais d audio perdu')
    vide = en_wav(array.array('h', []))
    verifier('un WAV vide est renvoye tel quel',
             audio_queue.rogner_queue_wav(vide) == vide)
    muet = en_wav(silence(1.0))
    verifier('un WAV tout silence est renvoye tel quel',
             audio_queue.rogner_queue_wav(muet) == muet)
    huit = io.BytesIO()
    with wave.open(huit, 'wb') as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(1)
        fichier.setframerate(FREQ)
        fichier.writeframes(bytes([128]) * int(0.5 * FREQ))
    octets_huit = huit.getvalue()
    verifier('un format inattendu (8 bits) est renvoye tel quel',
             audio_queue.rogner_queue_wav(octets_huit) == octets_huit)
    verifier('des octets vides ne font pas planter',
             audio_queue.rogner_queue_wav(b'') == b'')
    verifier('une entree inattendue ne fait pas planter',
             audio_queue.rogner_queue_wav(None) is None)

    print('')
    print('6) le rognage est bien BRANCHE dans la generation Kyutai')
    source = None
    try:
        source = inspect.getsource(_tts.synthesize_kyutai)
    except Exception as erreur:
        print('  (source illisible : %s)' % erreur)
    verifier('synthesize_kyutai appelle rogner_queue_wav',
             source is not None and 'rogner_queue_wav' in source)
    verifier('le rognage precede la mise en cache',
             source is not None and 0 <= source.find('rogner_queue_wav')
             < source.find('put_audio'),
             'dans modules/tts.py, le rognage doit venir avant put_audio')

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    print('=' * 70)
    print('VERIFICATION : rognage du silence de queue Kyutai (0,20 s)')
    print('=' * 70)
    sys.exit(main())
