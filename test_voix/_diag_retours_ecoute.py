# -*- coding: utf-8 -*-
"""Diagnostic des retours d'ecoute de Laurent (18/09/2026). LECTURE SEULE.

Repond a deux questions posees apres une demi-journee d'ecoute :

1. « J'entends un silence apres M. (lu "monsieur") ou Mme (lu "madame") » :
   le decoupage des phrases coupe APRES le point d'une abreviation, ce qui
   fait deux morceaux -- le 1er se termine par l'abreviation seule, le 2e
   commence par le nom. Ce script compte ces coupures dans le chapitre en
   cours de lecture et montre ce que recoit le moteur TTS.

2. « Le volume des voix Kyutai est tres, tres faible » : mesure le niveau
   reel (crete + RMS) des audio du cache disque, par famille (WAV = Kokoro,
   Piper, Kyutai, XTTS ; MP3 = Edge TTS).

N'ecrit rien, ne synthetise rien : aucun moteur n'est necessaire.

Usage :
    python test_voix/_diag_retours_ecoute.py
    python test_voix/_diag_retours_ecoute.py --chapitre 81
"""

import os
import re
import sqlite3
import sys
import wave
from array import array
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

BASE = Path(RACINE)
DB = BASE / 'data' / 'nimm_epub.db'
CACHE = BASE / 'data' / 'tts_cache'

# Bornes du diagnostic -- pour rester rapide (mesure du 18/09/2026 :
# ~2100 WAV et ~1300 MP3 dans le cache).
MAX_WAV = 500
MAX_MP3 = 6

# Les abreviations qui, dans le texte FRANCAIS, ne finissent JAMAIS une
# phrase. Si le decoupage coupe juste apres, c'est une coupure parasite.
ABREVIATIONS = ('M', 'MM', 'Mme', 'Mmes', 'Mlle', 'Mlles', 'Mgr', 'Dr', 'Pr',
                'St', 'Ste', 'Mr', 'Mx')


def _lire_wav(chemin):
    """(frequence, canaux, echantillons int16) d'un fichier WAV, ou None."""
    try:
        with wave.open(str(chemin), 'rb') as f:
            freq = f.getframerate()
            canaux = f.getnchannels()
            largeur = f.getsampwidth()
            brut = f.readframes(f.getnframes())
    except Exception:
        return None
    if largeur != 2:
        return None
    ech = array('h')
    ech.frombytes(brut)
    if not ech:
        return None
    return freq, canaux, ech


def _niveau_parole(ech, freq):
    """Niveau de la PAROLE seule, en % de la pleine echelle (None si n/d).

    Le RMS global est tire vers le bas par les silences : on prend la mediane
    du niveau des fenetres de 30 ms qui contiennent vraiment du son. C'est la
    mesure qui correspond a ce que l'oreille entend.
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


def _decoder_avec_ffmpeg(chemin):
    """(frequence, echantillons int16) d'un MP3, decode par ffmpeg."""
    import subprocess
    from imageio_ffmpeg import get_ffmpeg_exe
    cmd = [get_ffmpeg_exe(), '-v', 'error', '-i', str(chemin),
           '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', '24000', '-ac', '1', '-']
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60)
    except Exception:
        return None
    if r.returncode != 0 or not r.stdout:
        return None
    ech = array('h')
    ech.frombytes(r.stdout[:len(r.stdout) // 2 * 2])
    if not ech:
        return None
    return 24000, ech


def _niveau(ech):
    """(crete, rms) en pourcentage de la pleine echelle (100 = 0 dBFS)."""
    try:
        import numpy as np
        donnees = np.frombuffer(ech, dtype='<i2')
        if donnees.size == 0:
            return 0.0, 0.0
        pic = float(np.max(np.abs(donnees.astype('float32'))))
        rms = float(np.sqrt(np.mean(donnees.astype('float64') ** 2)))
        return 100.0 * pic / 32768.0, 100.0 * rms / 32768.0
    except Exception:
        pass
    if len(ech) == 0:
        return 0.0, 0.0
    pic = max(max(ech), -min(ech))
    moyen = sum(ech) / float(len(ech))
    carres = sum((v - moyen) ** 2 for v in ech) / float(len(ech))
    return 100.0 * pic / 32768.0, 100.0 * (carres ** 0.5) / 32768.0


# ==============================================================
# 1) DECOUPAGE DES PHRASES -- le silence apres « M. » / « Mme »
# ==============================================================

def _morceaux_actuels(paragraphe):
    """Exactement le decoupage du lecteur (app.js _buildSentences,
    voice_casting._split_chapter_sentences, main._decouper_phrases_du_chapitre)."""
    return [s.strip() for s in re.split(r'(?<=[.!?\u2026\u00bb])\s+', paragraphe)
            if len(s.strip()) > 3]


def _abreviation_finale(morceau):
    """Le dernier mot du morceau est-il une abreviation francaise ?"""
    mots = morceau.split()
    if not mots:
        return None
    dernier = mots[-1].strip('\u00ab\u00bb"()')
    sans_point = dernier.rstrip('.')
    if sans_point in ABREVIATIONS and (dernier.endswith('.') or
                                       sans_point in ('Mme', 'Mmes', 'Mlle',
                                                      'Mlles', 'Mgr')):
        return sans_point
    return None


def partie_abreviations(chapitre_vise=None):
    print('=' * 78)
    print('1) DECOUPAGE DES PHRASES : les silences apres M. / Mme')
    print('=' * 78)

    from core.epub_parser import get_chapters
    from modules.tts import _clean_text

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    livres = {r['id']: dict(r) for r in conn.execute('SELECT * FROM books')}

    # Le livre le plus recemment lu : c'est celui de la session d'ecoute.
    dernier = conn.execute(
        'SELECT * FROM progress ORDER BY rowid DESC LIMIT 1'
    ).fetchone()
    if dernier is None:
        print('  Aucune progression enregistree : rien a analyser.')
        conn.close()
        return
    livre = livres.get(dernier['book_id'])
    if livre is None:
        print('  Livre %s introuvable en base.' % dernier['book_id'])
        conn.close()
        return

    chapitre = chapitre_vise
    if chapitre is None:
        chapitre = dernier['chapter_index']
    print('')
    print('  Livre en cours    : %s (id %s)' % (livre['title'], livre['id']))
    print('  Dernier chapitre lu en base : %s' % dernier['chapter_index'])
    print('  Chapitre analyse  : %s' % chapitre)

    chemin = BASE / 'data' / 'library' / livre['filename']
    if not chemin.exists():
        print('  Fichier introuvable : %s' % chemin)
        conn.close()
        return

    chapitres = get_chapters(str(chemin))
    cible = None
    for c in chapitres:
        if c.get('index') == chapitre:
            cible = c
            break
    if cible is None:
        print('  Chapitre %s absent du livre (%d chapitres).'
              % (chapitre, len(chapitres)))
        conn.close()
        return

    texte = cible.get('text') or ''
    parasites = 0
    exemples = []
    total = 0
    for paragraphe in re.split(r'\n\n+', texte):
        paragraphe = paragraphe.strip()
        if len(paragraphe) <= 5:
            continue
        morceaux = _morceaux_actuels(paragraphe)
        total += len(morceaux)
        for i, morceau in enumerate(morceaux):
            if _abreviation_finale(morceau):
                parasites += 1
                if len(exemples) < 4:
                    suite = morceaux[i + 1] if i + 1 < len(morceaux) else '(fin)'
                    exemples.append((morceau, suite, _clean_text(morceau)))

    print('')
    print('  Phrases de ce chapitre            : %d' % total)
    print('  Coupures APRES une abreviation    : %d' % parasites)
    if parasites:
        print('')
        print('  Chacune produit DEUX phrases au lieu d\'une : la 1re se termine')
        print('  par l\'abreviation (le TTS y ajoute un point final -> le silence')
        print('  entendu), la 2e perd son debut a l\'ecran.')
        for morceau, suite, envoye in exemples:
            print('')
            print('    morceau 1 envoye au TTS : %r' % envoye)
            print('    morceau 2 lu ensuite    : %r' % suite)

    touches = 0
    total_livre = 0
    for c in chapitres:
        nb = 0
        for paragraphe in re.split(r'\n\n+', c.get('text') or ''):
            for morceau in _morceaux_actuels(paragraphe.strip()):
                if _abreviation_finale(morceau):
                    nb += 1
        if nb:
            touches += 1
            total_livre += nb
    print('')
    print('  Sur tout le livre : %d chapitres touches, %d coupures au total.'
          % (touches, total_livre))
    conn.close()


# ==============================================================
# 2) NIVEAU AUDIO DU CACHE -- le volume des voix Kyutai
# ==============================================================

def partie_niveaux():
    print('')
    print('=' * 78)
    print('2) NIVEAU AUDIO DES FICHIERS EN CACHE')
    print('=' * 78)

    if not CACHE.is_dir():
        print('  Cache absent : %s' % CACHE)
        return

    wavs = sorted(CACHE.glob('*.wav'), key=lambda p: p.stat().st_mtime, reverse=True)
    mp3s = sorted(CACHE.glob('*.mp3'), key=lambda p: p.stat().st_mtime, reverse=True)
    print('')
    print('  Cache : %d WAV, %d MP3. Analyse des %d WAV et %d MP3 les plus recents.'
          % (len(wavs), len(mp3s), min(MAX_WAV, len(wavs)), min(MAX_MP3, len(mp3s))))

    groupes = {}
    for chemin in wavs[:MAX_WAV]:
        info = _lire_wav(chemin)
        if info is None:
            continue
        freq, _canaux, ech = info
        crete, rms = _niveau(ech)
        groupes.setdefault(freq, []).append((crete, rms))

    print('')
    print('  --- WAV (Kokoro, Piper, Kyutai, XTTS) ---')
    for freq in sorted(groupes, reverse=True):
        mesures = groupes[freq]
        cretes = sorted(m[0] for m in mesures)
        rmss = sorted(m[1] for m in mesures)
        print('')
        print('  %5d Hz : %4d fichiers | crete mediane %5.1f %% (min %5.1f, max %5.1f)'
              % (freq, len(mesures), cretes[len(cretes) // 2], cretes[0], cretes[-1]))
        print('                       | RMS median     %5.1f %%'
              % rmss[len(rmss) // 2])
        tranches = {}
        for c in cretes:
            cle = int(c // 10) * 10
            tranches[cle] = tranches.get(cle, 0) + 1
        detail = ', '.join('%d-%d %%: %d' % (k, k + 10, v)
                           for k, v in sorted(tranches.items()))
        print('                       | repartition crete : %s' % detail)

    if mp3s:
        print('')
        print('  --- MP3 (Edge TTS, la reference de Laurent) ---')
        mesures = []
        for chemin in mp3s[:MAX_MP3]:
            r = _decoder_avec_ffmpeg(chemin)
            if r is None:
                continue
            mesures.append(_niveau(r[1]))
        if mesures:
            cretes = sorted(m[0] for m in mesures)
            rmss = sorted(m[1] for m in mesures)
            print('  %4d fichiers analyses | crete mediane %5.1f %% | RMS median %5.1f %%'
                  % (len(mesures), cretes[len(cretes) // 2], rmss[len(rmss) // 2]))
        else:
            print('  (decodage ffmpeg indisponible)')


def partie_normalisation():
    """Ce que la normalisation change vraiment, sur les phrases du jour."""
    print('')
    print('=' * 78)
    print('3) EFFET DE LA NORMALISATION DU NIVEAU (modules/audio_gain.py)')
    print('=' * 78)

    from modules import audio_gain

    wavs = sorted(CACHE.glob('*.wav'), key=lambda p: p.stat().st_mtime, reverse=True)
    essais = wavs[:120]
    avant, apres, gains = [], [], []
    for chemin in essais:
        octets = chemin.read_bytes()
        info = _lire_wav(chemin)
        if info is None:
            continue
        freq, _canaux, ech = info
        n_avant = _niveau_parole(ech, freq)
        if n_avant is None:
            continue
        nouveau = audio_gain.normaliser_wav_parole(octets)
        info2 = None
        try:
            import io
            import wave as _wave
            with _wave.open(io.BytesIO(nouveau), 'rb') as f:
                freq2 = f.getframerate()
                brut = f.readframes(f.getnframes())
            ech2 = array('h')
            ech2.frombytes(brut)
            info2 = (freq2, ech2)
        except Exception:
            info2 = None
        if info2 is None:
            continue
        n_apres = _niveau_parole(info2[1], info2[0])
        if n_apres is None:
            continue
        avant.append(n_avant)
        apres.append(n_apres)
        if n_avant > 0:
            gains.append(n_apres / n_avant)

    if not avant:
        print('  Aucun fichier mesurable.')
        return

    def mediane(v):
        v = sorted(v)
        return v[len(v) // 2]

    print('')
    print('  %d phrases du cache analysees (les plus recentes).' % len(avant))
    print('  Niveau de parole median : %5.1f %%  ->  %5.1f %%'
          % (mediane(avant), mediane(apres)))
    print('  Niveau de parole le plus bas : %5.1f %%  ->  %5.1f %%'
          % (min(avant), min(apres)))
    print('  Gain median applique    : x%.2f' % mediane(gains))
    print('  Cible du reglage        : %.1f %% (niveau d\'Edge TTS mesure)'
          % audio_gain.CIBLE_POURCENT)


def main():
    chapitre = None
    if '--chapitre' in sys.argv:
        i = sys.argv.index('--chapitre')
        if i + 1 < len(sys.argv):
            chapitre = int(sys.argv[i + 1])

    print('')
    print('DIAGNOSTIC DES RETOURS D\'ECOUTE -- lecture seule, rien n\'est modifie.')
    partie_abreviations(chapitre)
    partie_niveaux()
    partie_normalisation()
    print('')
    print('Fin du diagnostic.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

