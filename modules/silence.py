# -*- coding: utf-8 -*-
"""Un court silence en WAV, pour les phrases qui ne sont QU'UNE INCISE.

Pourquoi (retour d'écoute de Laurent, 18/09/2026) : le découpage sépare les
phrases au « ! » et au « ? », donc une incise se retrouve parfois **seule**, en
phrase à part entière. Exemple réel du tome 5 :

    « — Ah ! vraiment ? dit Monte-Cristo. »
    -> trois phrases : « — Ah ! » | « vraiment ? » | « dit Monte-Cristo. »

La dernière **n'est que l'incise** : on ne peut pas la vider (le moteur refuse un
texte vide, et la phrase **disparaîtrait** de l'écoute). On renvoie donc un
**silence court** : l'auditeur n'entend plus « dit Monte-Cristo » — la voix du
personnage dit déjà qui parle — et le rythme de lecture est conservé, le curseur
s'arrêtant sur la phrase le temps du silence.

Mesure : **91 phrases** de ce genre dans le seul tome 5.

Durée réglable : `SILENCE_INCISE_MS` (150 ms). Mettre 0 désactive le dispositif
(les phrases-incises redeviennent lues).
"""

import io
import wave

SILENCE_INCISE_MS = 150
FREQUENCE = 24000


def wav_silence(duree_ms=SILENCE_INCISE_MS, frequence=FREQUENCE):
    """Un WAV mono 16 bits de silence, de `duree_ms` millisecondes."""
    nombre = max(1, int(frequence * duree_ms / 1000.0))
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(frequence))
        fichier.writeframes(b"\x00\x00" * nombre)
    return tampon.getvalue()
