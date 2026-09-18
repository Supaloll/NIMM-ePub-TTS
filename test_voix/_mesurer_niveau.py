# -*- coding: utf-8 -*-
"""Mesure le niveau reel (crete + RMS) de fichiers audio. LECTURE SEULE.

Sert a comparer le volume d'un moteur a un autre : un WAV Kokoro/Piper/Kyutai
et un MP3 Edge se mesurent avec la meme echelle (pourcentage de la pleine
echelle ; 100 % = 0 dBFS, le maximum possible).

Usage :
    python test_voix/_mesurer_niveau.py fichier1.wav fichier2.mp3 ...
"""
import subprocess
import sys
import wave
from array import array
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def _niveau(ech):
    """(crete, rms) en pourcentage de la pleine echelle."""
    try:
        import numpy as np
        donnees = np.frombuffer(ech, dtype='<i2')
        if donnees.size == 0:
            return 0.0, 0.0
        pic = float(np.max(np.abs(donnees.astype('float32'))))
        rms = float(np.sqrt(np.mean(donnees.astype('float64') ** 2)))
        return 100.0 * pic / 32768.0, 100.0 * rms / 32768.0
    except Exception:
        if len(ech) == 0:
            return 0.0, 0.0
        pic = max(max(ech), -min(ech))
        carres = sum(v * v for v in ech) / float(len(ech))
        return 100.0 * pic / 32768.0, 100.0 * (carres ** 0.5) / 32768.0


def _lire_wav(chemin):
    with wave.open(str(chemin), 'rb') as f:
        freq = f.getframerate()
        largeur = f.getsampwidth()
        brut = f.readframes(f.getnframes())
    if largeur != 2:
        return None
    ech = array('h')
    ech.frombytes(brut)
    return freq, ech


def _lire_mp3(chemin):
    from imageio_ffmpeg import get_ffmpeg_exe
    cmd = [get_ffmpeg_exe(), '-v', 'error', '-i', str(chemin),
           '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', '24000', '-ac', '1', '-']
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    if r.returncode != 0 or not r.stdout:
        return None
    ech = array('h')
    ech.frombytes(r.stdout[:len(r.stdout) // 2 * 2])
    return 24000, ech


def _niveau_parole(ech, freq):
    """Niveau de la PAROLE seule : mediane des RMS des fenetres actives.

    Le RMS global d'un fichier est tire vers le bas par ses silences : deux
    moteurs peuvent avoir le meme RMS global et une parole tres differente.
    On decoupe donc en fenetres de 30 ms, on garde celles dont le pic depasse
    2 % de la pleine echelle (donc de la voix, pas du souffle), et on prend la
    MEDIANE de leur RMS -- c'est le niveau entendu, en pourcentage de la
    pleine echelle.
    """
    try:
        import numpy as np
        donnees = np.frombuffer(ech, dtype='<i2').astype('float64')
    except Exception:
        return None
    taille = max(1, int(0.030 * freq))
    nb = len(donnees) // taille
    if nb < 2:
        return None
    blocs = donnees[:nb * taille].reshape(nb, taille)
    pics = np.max(np.abs(blocs), axis=1)
    rms = np.sqrt(np.mean(blocs ** 2, axis=1))
    actifs = rms[pics > 0.02 * 32768.0]
    if actifs.size < 2:
        return None
    return 100.0 * float(np.median(actifs)) / 32768.0


def mesurer(chemin):
    p = Path(chemin)
    if not p.is_file():
        print('  ABSENT  %s' % chemin)
        return
    try:
        if p.suffix.lower() == '.wav':
            lu = _lire_wav(p)
        else:
            lu = _lire_mp3(p)
    except Exception as e:
        print('  ERREUR  %s (%s)' % (chemin, e))
        return
    if not lu:
        print('  ILLISIBLE  %s' % chemin)
        return
    freq, ech = lu
    crete, rms = _niveau(ech)
    parole = _niveau_parole(ech, freq)
    duree = len(ech) / float(freq)
    print('  %-44s %5d Hz %5.2f s | crete %5.1f %% | global %5.1f %% | PAROLE %s'
          % (p.name[:44], freq, duree, crete, rms,
             ('%5.1f %%' % parole) if parole is not None else '   n/d '))


def main():
    if len(sys.argv) < 2:
        print('Usage : python test_voix/_mesurer_niveau.py fichier1 fichier2 ...')
        return 1
    print('')
    print('NIVEAU DES FICHIERS (100 %% de crete = 0 dBFS, le maximum)')
    print('')
    for chemin in sys.argv[1:]:
        mesurer(chemin)
    return 0


if __name__ == '__main__':
    sys.exit(main())
