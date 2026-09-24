# -*- coding: utf-8 -*-
"""Rognage du silence de QUEUE des phrases Kyutai (decision de Laurent, 23/09/2026).

Le moteur Kyutai ne rogne pas ses bords : il garde la respiration qu'il a
produite lui-meme -- 0,30 a 0,43 s mesurees les 17 et 21/09/2026, confirmees le
23/09/2026 sur les fichiers reels du cache (queue mediane 0,37 s sur 300 WAV).
A l'ecoute du 23/09/2026, Laurent a trouve les pauses APRES LES POINTS trop
longues, et les SAUTS DE LIGNE trop rapides. Les deux se cumulant, on regle les
deux ensemble :
  - ici : la queue du moteur est ramenee a `QUEUE_GARDEE_S` (0,20 s) ;
  - `frontend/app.js` : la pause entre paragraphes remonte a 600 ms.

Pourquoi ICI et pas dans le service du moteur : c'est du post-traitement du WAV,
sur le meme chemin que `audio_rate`, `audio_gain` et `audio_trim` (applique
APRES la reception, AVANT la vitesse, la hauteur et le niveau). Avantage : la
phrase mise en cache est deja rognee, et le rognage se TESTE A FROID -- aucun
moteur a allumer, aucune carte graphique, aucun appel facture.

La PAROLE n'est jamais touchee : on ne retire que ce qui suit le dernier son
audible. Si le WAV est vide, muet, d'un format inattendu, ou si le calcul
echoue, les octets d'origine sont renvoyes tels quels -- on ne casse jamais la
lecture (meme regle que `audio_trim.py` et `audio_rate.py`).
"""

import array
import io
import wave

# Marge conservee apres le dernier son audible. 0,20 s : entre les 0,10 s de
# Kokoro/Piper (audio natif, non rogne) et les 0,25 s de XTTS/NeuTTS. Valeur
# choisie par Laurent le 23/09/2026 (« les pauses apres les points un peu
# longues, un peu moins ; les sauts de ligne un peu plus »).
QUEUE_GARDEE_S = 0.20
SEUIL_SON = 0.012            # meme seuil que les autres outils d'atelier
BLOC_ANALYSE_S = 0.01        # granularite d'analyse : 10 ms


def rogner_queue_wav(wav_bytes: bytes, gardee_s: float = QUEUE_GARDEE_S,
                     seuil: float = SEUIL_SON) -> bytes:
    """Ne garde que `gardee_s` de silence apres le dernier son audible.

    Renvoie un WAV du meme format (canaux, bits, cadence) ; renvoie les octets
    d'origine si le fichier est vide, muet, d'un format inattendu, si la queue
    est deja plus courte que la marge, ou si le traitement echoue.
    """
    if not wav_bytes:
        return wav_bytes
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as entree:
            canaux = entree.getnchannels()
            largeur = entree.getsampwidth()
            frequence = entree.getframerate()
            total = entree.getnframes()
            params = entree.getparams()
            brut = entree.readframes(total)
        if total <= 0 or frequence <= 0 or largeur != 2:
            return wav_bytes             # format inattendu : on ne touche a rien

        echantillons = array.array('h')
        echantillons.frombytes(brut)
        # Analyse a plat : sur du multicanal, un bloc de 10 ms couvre tous les
        # canaux, ce qui suffit pour trouver le dernier son audible.
        pas = max(canaux, int(BLOC_ANALYSE_S * frequence))
        dernier = -1
        for debut in range(0, len(echantillons), pas):
            bloc = echantillons[debut:debut + pas]
            if bloc and max(abs(v) for v in bloc) / 32768.0 >= seuil:
                dernier = debut
        if dernier < 0:
            return wav_bytes             # aucun son audible : rien a rogner

        fin = dernier + pas + int(gardee_s * frequence)
        fin -= fin % canaux              # on ne coupe pas au milieu d'une trame
        if fin >= len(echantillons):
            return wav_bytes             # queue deja courte : rien a faire

        coupe = array.array('h', echantillons[:fin])
        sortie = io.BytesIO()
        with wave.open(sortie, "wb") as fichier:
            fichier.setparams(params)
            fichier.writeframes(coupe.tobytes())
        return sortie.getvalue()
    except Exception:
        return wav_bytes
