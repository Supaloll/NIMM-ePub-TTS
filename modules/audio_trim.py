# -*- coding: utf-8 -*-
"""Rognage des silences de bord des fichiers audio Edge TTS.

Les MP3 produits par Edge TTS contiennent ~0,25 s de silence au debut et
~1 s de silence a la fin de chaque phrase (pause de fin d'enonce ajoutee
par le service). En lecture phrase par phrase, ces blancs s'accumulent
(~1,2 s entre deux phrases) : rythme hachu et surbrillance decalee.

On rogne ici les silences en conservant une micro-pause naturelle, AVANT
la mise en cache. La parole elle-meme n'est jamais touchee.

Technique : ffmpeg (binaire deja embarque par le paquet `imageio-ffmpeg`,
aucune nouvelle dependance), filtre `silenceremove` applique dans les deux
sens (debut puis fin) via `areverse`. En cas d'echec quelconque, on
renvoie l'audio original : on ne casse jamais la lecture.
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


def trim_mp3_silence(mp3_bytes: bytes) -> bytes:
    """Rogne les silences de debut/fin d'un MP3 Edge.

    Renvoie le MP3 nettoye ; renvoie l'original si le traitement echoue
    (fichier illisible, ffmpeg indisponible, timeout...).
    """
    if not mp3_bytes:
        return mp3_bytes
    try:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "in.mp3"
            dst = td / "out.mp3"
            src.write_bytes(mp3_bytes)

            # -45 dB : seuil de silence. Marges conservees : ~0,08 s apres
            # le debut de la parole, ~0,25 s avant la fin (respiration).
            # La marge de fin est passee de 0,15 s a 0,25 s le 15/09/2026, a la
            # demande de Laurent : l'enchainement des phrases lui paraissait un
            # peu sec apres le rognage. Il a demande un ajout TRES LEGER
            # (+100 ms) : c'est ce que fait cette valeur, et rien d'autre.
            filtres = (
                "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,"
                "areverse,"
                "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,"
                "areverse"
            )
            cmd = [
                _ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(src),
                "-af", filtres,
                "-c:a", "libmp3lame", "-b:a", "48k", "-ar", "24000", "-ac", "1",
                str(dst),
            ]
            r = subprocess.run(cmd, capture_output=True, timeout=30)
            if r.returncode != 0:
                return mp3_bytes
            out = dst.read_bytes()
            return out if out else mp3_bytes
    except Exception:
        return mp3_bytes
