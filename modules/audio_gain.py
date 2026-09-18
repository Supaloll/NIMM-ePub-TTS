# -*- coding: utf-8 -*-
"""Niveau sonore d'un WAV : ramene la PAROLE au niveau des autres moteurs.

Pourquoi ce module (retour d'ecoute de Laurent, 18/09/2026) : « le volume des
voix Kyutai est tres, tres faible ». Mesure du meme jour
(`test_voix/_mesurer_niveau.py`, sur le cache du lecteur) :

    Edge TTS : niveau de parole median 8,4 % de la pleine echelle
    Kyutai   : 6,2 %, et jusqu'a 3,4 % sur certaines phrases

Soit jusqu'a -8 dB par rapport a Edge. Le moteur Kyutai ne regle pas son volume
de sortie (le script officiel de la banque de voix, lui, normalise a -22 LUFS).

Ce que fait ce module : il mesure le niveau de la PAROLE SEULE -- fenetres de
30 ms ou l'on parle vraiment, et non la moyenne du fichier, qui est tiree vers
le bas par les silences -- puis applique le gain qui amene ce niveau a la cible.

Garde-fous (on ne casse jamais la lecture) :
  - le gain est PLAFONNE : au-dela, on amplifierait surtout le souffle du
    modele, et une phrase un peu faible vaut mieux qu'une phrase soufflante ;
  - la crete de sortie est bornee : aucun echantillon ne sature ;
  - on n'attenue JAMAIS (gain < 1) : le role est de remonter, pas de calmer ;
  - tout format inattendu ou tout echec renvoie l'audio d'origine.
"""

import io
import wave
from array import array

# Niveau de parole vise, en pourcentage de la pleine echelle (100 = 0 dBFS).
# 8,5 % = le niveau mesure d'Edge TTS, la reference que Laurent n'a jamais
# trouvee faible.
CIBLE_POURCENT = 8.5

# Gain maximal. 4x = +12 dB : de quoi rattraper les phrases les plus faibles
# mesurees (3,4 % -> 13,6 % serait trop, la crete borne de toute facon).
GAIN_MAX = 4.0

# Crete maximale en sortie, en pourcentage de la pleine echelle.
CRETE_MAX_POURCENT = 98.0

# Une retouche de moins de 2 % ne s'entend pas : on ne touche a rien.
GAIN_MIN_INTERET = 1.02

# Fenetre d'analyse et seuil de « ca parle » (meme esprit que SEUIL_SON des
# outils d'atelier, qui est a 0,012 en amplitude flottante).
FENETRE_S = 0.030
SEUIL_PAROLE = 0.02 * 32768.0


def _lire_wav(octets):
    """(canaux, largeur, frequence, echantillons int16) d'un WAV en memoire."""
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        canaux = fichier.getnchannels()
        largeur = fichier.getsampwidth()
        frequence = fichier.getframerate()
        brut = fichier.readframes(fichier.getnframes())
    ech = array("h")
    ech.frombytes(brut[:len(brut) // 2 * 2])
    return canaux, largeur, frequence, ech


def _ecrire_wav(ech, frequence):
    """Reconstruit un WAV mono 16 bits a partir d'echantillons int16."""
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(frequence))
        fichier.writeframes(ech.tobytes())
    return tampon.getvalue()


def _niveau_parole(ech, frequence):
    """Niveau de la parole seule, en % de la pleine echelle (None si indecidable).

    On decoupe en fenetres de 30 ms, on ne garde que celles qui contiennent
    vraiment du son, et on prend la MEDIANE de leur niveau -- c'est ce que
    l'oreille entend, independamment des silences du fichier.
    """
    taille = max(1, int(FENETRE_S * frequence))
    nb = len(ech) // taille
    if nb < 2:
        return None
    actifs = []
    for i in range(nb):
        bloc = ech[i * taille:(i + 1) * taille]
        pic = max(max(bloc), -min(bloc))
        if pic <= SEUIL_PAROLE:
            continue
        somme = 0
        for v in bloc:
            somme += v * v
        actifs.append((somme / len(bloc)) ** 0.5)
    if len(actifs) < 2:
        return None
    actifs.sort()
    return 100.0 * actifs[len(actifs) // 2] / 32768.0


def _pic(ech):
    return max(max(ech), -min(ech))


def normaliser_wav_parole(wav_bytes, cible=CIBLE_POURCENT, gain_max=GAIN_MAX):
    """Renvoie le WAV avec sa parole ramenee a `cible` % de la pleine echelle.

    Renvoie l'audio d'origine si le format est inattendu, si le niveau n'est pas
    mesurable, si le gain necessaire depasserait `gain_max`, ou si la retouche
    serait inaudible.
    """
    if not wav_bytes:
        return wav_bytes
    try:
        canaux, largeur, frequence, ech = _lire_wav(wav_bytes)
        if largeur != 2 or canaux != 1 or len(ech) < 10:
            return wav_bytes

        niveau = _niveau_parole(ech, frequence)
        if not niveau or niveau < 0.1:
            return wav_bytes

        gain = cible / niveau
        if gain > gain_max:
            gain = gain_max
        pic = _pic(ech)
        if pic > 0:
            plafond = CRETE_MAX_POURCENT / 100.0 * 32767.0
            if pic * gain > plafond:
                gain = plafond / pic
        if gain <= GAIN_MIN_INTERET:
            return wav_bytes

        sortie = array("h")
        for v in ech:
            x = int(v * gain)
            if x > 32767:
                x = 32767
            elif x < -32768:
                x = -32768
            sortie.append(x)
        return _ecrire_wav(sortie, frequence)
    except Exception:
        # Jamais d'echec de lecture a cause d'un reglage de volume.
        return wav_bytes
