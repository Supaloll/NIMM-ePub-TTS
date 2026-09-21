# -*- coding: utf-8 -*-
"""Niveau sonore d'un WAV : ramene la PAROLE dans une fourchette, pas a un niveau unique.

Pourquoi ce module (retour d'ecoute de Laurent, 18/09/2026) : « le volume des
voix Kyutai est tres, tres faible ». Mesure du meme jour
(`test_voix/_mesurer_niveau.py`, sur le cache du lecteur) :

    Edge TTS : niveau de parole median 8,4 % de la pleine echelle
    Kyutai   : 6,2 %, et jusqu'a 3,4 % sur certaines phrases

Ce que fait ce module : il mesure le niveau de la PAROLE SEULE -- fenetres de
30 ms ou l'on parle vraiment, et non la moyenne du fichier, qui est tiree vers le
bas par les silences -- puis corrige ce qu'il faut.

**CE QUI A CHANGE LE 21/09/2026 : la correction joue DANS LES DEUX SENS, mais
seulement pour ce qui SORT de la fourchette.**

L'ancienne regle ne faisait que REMONTER, vers une cible de 8,5 % (le niveau
d'Edge) : une phrase DEJA plus forte n'etait donc jamais ramenee. Mesure du
21/09/2026 sur dix phrases d'un long paragraphe de 22/11/63, lues une par une
comme en lecture (`test_voix/_mesurer_pocket_defauts.py`) :

    Kyutai  : de 3,8 a 10,8 % (median 6,6) -- eparpille de 9,1 dB a la sortie
    Pocket  : de 7,5 a 12,8 % (median 9,6) -- 4,6 dB

Le module ramenait deja les phrases FAIBLES vers 8,5 % (d'ou ~2 dB d'ecart chez
Kyutai), mais il laissait les phrases FORTES au-dessus : chez Pocket, une phrase
a 12,8 % restait **3,6 dB au-dessus** de ses voisines. La fourchette corrige ce
reste, sans rien aplatir.

Regle actuelle (depuis le 21/09/2026) :
  - une phrase TROP FAIBLE est **remontee jusqu'a la cible** (au plus `GAIN_MAX`)
  - une phrase TROP FORTE est **ramenee vers la cible**, sans jamais perdre plus
    de `GAIN_MIN` (-6 dB) : on ne l'ecrase pas ;
  - une correction inaudible (moins de 2 %, dans un sens comme dans l'autre)
    n'est pas appliquee.

*Pourquoi pas une simple « bande de +/- 3 dB »* (idee du 21/09/2026, **essayee
puis abandonnee**) : elle laissait en place les petites variations -- mesure
faite, il restait **3,7 dB d'ecart** entre les phrases d'un meme paragraphe,
soit exactement le defaut entendu. Ces variations ne sont pas des nuances
voulues : c'est l'instabilite du moteur.

Garde-fous (on ne casse jamais la lecture) :
  - le gain est PLAFONNE vers le haut : au-dela, on amplifierait surtout le
    souffle du modele, et une phrase un peu faible vaut mieux qu'une phrase
    soufflante ;
  - la crete de sortie est bornee : aucun echantillon ne sature ;
  - une correction inaudible (moins de 2 %) n'est pas appliquee ;
  - tout format inattendu ou tout echec renvoie l'audio d'origine.
"""

import io
import math
import wave
from array import array

# Niveau de parole vise, en pourcentage de la pleine echelle (100 = 0 dBFS).
# 8,5 % = le niveau mesure d'Edge TTS, la reference que Laurent n'a jamais
# trouvee faible.
CIBLE_POURCENT = 8.5

# Gain maximal. 4x = +12 dB : de quoi rattraper les phrases les plus faibles
# mesurees (3,4 % -> 13,6 % serait trop, la crete borne de toute facon).
GAIN_MAX = 4.0

# LA MARGE INUTILE (21/09/2026) : une correction de moins de 2 % ne s'entend pas,
# et elle n'est pas appliquee -- que ce soit vers le haut ou vers le bas.
GAIN_MIN_INTERET = 1.02

# On n'ecrase jamais une phrase trop forte : au plus -6 dB (la moitie du volume).
GAIN_MIN = 0.5

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
    """Ramene la parole du WAV DANS LA FOURCHETTE autour de `cible` (en %).

    Ne touche pas une phrase qui est deja dans la bande de +/- BANDE_DB : c'est
    ce qui garde les nuances entre voix. Renvoie l'audio d'origine si le format
    est inattendu, si le niveau n'est pas mesurable, ou si la retouche serait
    inaudible.
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

        # Correction vers la cible : VERS LE BAS COMME VERS LE HAUT, mais
        # bornee des deux cotes (une phrase faible n'est pas poussee dans le
        # souffle, une phrase forte n'est jamais ecrasee).
        #
        # POURQUOI PAS UNE BANDE DE +/- 3 dB (essayee le 21/09/2026, puis
        # abandonnee) : l'idee etait de laisser en place les petites variations.
        # La mesure l'a ecartee -- sur dix phrases reelles d'un meme paragraphe,
        # laisser 3 dB de liberte en gardait 3,7 dB d'ecart a l'oreille, soit
        # exactement le defaut signale (« le volume baisse »). Ces variations ne
        # sont pas des nuances voulues : c'est l'instabilite du moteur.
        gain = cible / niveau
        if gain > gain_max:
            gain = gain_max
        if gain < GAIN_MIN:
            gain = GAIN_MIN
        pic = _pic(ech)
        if pic > 0:
            plafond = CRETE_MAX_POURCENT / 100.0 * 32767.0
            if pic * gain > plafond:
                gain = plafond / pic
        if abs(gain - 1.0) < GAIN_MIN_INTERET - 1.0:
            # Correction inaudible : moins de 2 %, vers le haut COMME vers le bas
            # (avant la fourchette du 21/09/2026 le gain ne pouvait etre que
            # superieur a 1 ; il peut desormais etre inferieur, d'ou la
            # comparaison en ECART et non en seuil).
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
