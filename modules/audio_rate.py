# -*- coding: utf-8 -*-
"""Vitesse de lecture pour les moteurs qui ne l'ont pas en natif.

Edge TTS (`rate=`), Kokoro (`speed=`) et Piper (`length_scale`) savent
ralentir ou accelerer une phrase nativement. Kyutai, lui, n'expose
AUCUN reglage de vitesse : la vitesse y est donc appliquee APRES coup,
avec ffmpeg (binaire deja embarque par `imageio-ffmpeg`, celui qui sert
aussi au rognage des silences).

Le filtre utilise est `atempo`, concu exactement pour cela : il change la
DUREE sans toucher a la hauteur de la voix (contrairement a un simple
changement de frequence d'echantillonnage, qui ferait varier la hauteur).
Au-dela de 2x, le filtre est chaine (`atempo=2.0,atempo=...`).

En cas d'echec (fichier illisible, ffmpeg indisponible...), l'audio
d'origine est renvoye tel quel : on ne casse jamais la lecture.
"""

import subprocess
import tempfile
from pathlib import Path

_FFMPEG_EXE = None


def _ffmpeg():
    """Chemin du binaire ffmpeg fourni par imageio-ffmpeg (charge une fois)."""
    global _FFMPEG_EXE
    if _FFMPEG_EXE is None:
        from imageio_ffmpeg import get_ffmpeg_exe
        _FFMPEG_EXE = get_ffmpeg_exe()
    return _FFMPEG_EXE


def _filtre_atempo(vitesse: float) -> str:
    """Chaine de filtres `atempo` pour une vitesse quelconque (0,5 a 4)."""
    morceaux = []
    reste = vitesse
    while reste > 2.0:
        morceaux.append("atempo=2.0")
        reste /= 2.0
    while reste < 0.5:
        morceaux.append("atempo=0.5")
        reste /= 0.5
    morceaux.append("atempo=%.4f" % reste)
    return ",".join(morceaux)


def appliquer_vitesse(wav_bytes: bytes, vitesse: float) -> bytes:
    """Renvoie le WAV a la vitesse demandee (1.0 = inchange).

    La frequence d'echantillonnage et le nombre de canaux d'origine sont
    conserves : seul le rythme change.
    """
    if not wav_bytes or abs(vitesse - 1.0) < 0.01:
        return wav_bytes

    frequence = None
    try:
        import wave
        with wave.open(_flux(wav_bytes), "rb") as fichier:
            frequence = fichier.getframerate()
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            source = td / "entree.wav"
            cible = td / "sortie.wav"
            source.write_bytes(wav_bytes)

            cmd = [
                _ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(source),
                "-filter:a", _filtre_atempo(vitesse),
                "-ar", str(frequence), "-ac", "1",
                "-c:a", "pcm_s16le",
                str(cible),
            ]
            resultat = subprocess.run(cmd, capture_output=True, timeout=60)
            if resultat.returncode != 0:
                return wav_bytes
            sortie = cible.read_bytes()
            return sortie if sortie else wav_bytes
    except Exception:
        return wav_bytes


def _flux(octets: bytes):
    """Petit flux en memoire, pour lire l'entete d'un WAV sans fichier."""
    import io
    return io.BytesIO(octets)
