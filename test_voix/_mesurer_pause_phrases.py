# -*- coding: utf-8 -*-
"""Mesure les PAUSES autour des phrases, moteur par moteur (constat de Laurent).

QUESTION (17/09/2026) : « le point passe tres vite » ; « il faudrait augmenter la
pause de peut-etre 100 millisecondes (Kyutai, et Edge aussi) ». Avant de regler
quoi que ce soit, on MESURE : combien de silence y a-t-il vraiment en tete et en
queue de chaque phrase, pour chaque moteur ?

Comment : on interroge LE LECTEUR (`/api/tts`), donc le chemin reel -- rognage,
cache et post-traitement compris. Puis on decoupe l'audio en trois :
    silence de TETE | parole | silence de QUEUE
et on affiche les trois, en millisecondes.

Reglages en jeu, pour memoire :
  - Edge        : `modules/audio_trim.py` (marge de fin conservee : 0,25 s)
  - XTTS/NeuTTS : `SILENCE_QUEUE_S = 0.25` dans leur service
  - Kyutai      : AUCUN rognage et AUCUNE pause ajoutee (c'est le modele seul)
  - Kokoro/Piper: pas de rognage (audio natif)

Le lecteur doit tourner (START.bat). Usage :
    python test_voix/_mesurer_pause_phrases.py
    python test_voix/_mesurer_pause_phrases.py --phrase "Il partit."
"""

import argparse
import array
import io
import json
import sys
import urllib.request
import wave

sys.stdout.reconfigure(encoding='utf-8')

LECTEUR = "http://127.0.0.1:8081"
PHRASE = "Il partit."
SEUIL = 0.012                 # meme seuil que les autres outils d'atelier
BLOC_S = 0.01

# Une voix par moteur (les trois familles qui lisent aujourd'hui).
VOIX = [
    ("kyutai:1770_1028_000036-0002", "Kyutai (Bertrand)"),
    ("fr-FR-HenriNeural", "Edge (Henri)"),
    ("kokoro:fm_lucas", "Kokoro (Lucas)"),
    ("piper:siwis:0", "Piper (Siwis)"),
]


def demander(texte, voix):
    """Un appel au LECTEUR, comme le fait la page de lecture."""
    corps = json.dumps({"text": texte, "voice": voix,
                        "rate": "+0%", "pitch": "+0Hz"}).encode('utf-8')
    requete = urllib.request.Request(
        LECTEUR + "/api/tts", data=corps,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=120) as reponse:
        return reponse.read()


def en_wav(octets):
    """Garantit du WAV PCM : Edge renvoie du MP3, les autres moteurs du WAV."""
    if octets[:4] == b'RIFF':
        return octets
    import subprocess
    import tempfile
    from pathlib import Path
    from imageio_ffmpeg import get_ffmpeg_exe

    with tempfile.TemporaryDirectory() as td:
        source = Path(td) / 'entree.mp3'
        cible = Path(td) / 'sortie.wav'
        source.write_bytes(octets)
        subprocess.run(
            [get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-ar", "24000", "-ac", "1",
             "-c:a", "pcm_s16le", str(cible)],
            capture_output=True, timeout=60)
        return cible.read_bytes() if cible.exists() else octets


def bornes(octets):
    """(duree, debut de la parole, fin de la parole) en secondes."""
    octets = en_wav(octets)
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        frequence = fichier.getframerate()
        brut = fichier.readframes(fichier.getnframes())
    echantillons = array.array('h')
    echantillons.frombytes(brut)
    duree = len(echantillons) / float(frequence)
    pas = max(1, int(BLOC_S * frequence))
    premier = dernier = None
    for debut in range(0, len(echantillons), pas):
        bloc = echantillons[debut:debut + pas]
        if bloc and max(abs(v) for v in bloc) / 32768.0 >= SEUIL:
            if premier is None:
                premier = debut / float(frequence)
            dernier = (debut + len(bloc)) / float(frequence)
    if premier is None:
        return duree, None, None
    return duree, premier, dernier


def main():
    analyseur = argparse.ArgumentParser(
        description="Mesure les silences de tete et de queue, moteur par moteur.")
    analyseur.add_argument('--phrase', default=PHRASE,
                           help='la phrase a lire (defaut : "%s")' % PHRASE)
    options = analyseur.parse_args()

    print('')
    print('=' * 78)
    print('PAUSES AUTOUR DE LA PHRASE  (mesure via le lecteur)')
    print('=' * 78)
    print('phrase : « %s »' % options.phrase)
    print('')
    print('  %-22s %8s %8s %8s %8s' % ('moteur', 'duree', 'tete', 'parole',
                                       'queue'))
    print('  ' + '-' * 60)

    for voix, libelle in VOIX:
        try:
            octets = demander(options.phrase, voix)
        except Exception as erreur:
            print('  %-22s ECHEC : %s' % (libelle[:22], erreur))
            continue
        duree, debut, fin = bornes(octets)
        if debut is None:
            print('  %-22s %7.3fs   (aucun son audible)' % (libelle[:22], duree))
            continue
        tete = debut
        queue = duree - fin
        parole = fin - debut
        print('  %-22s %7.3fs %7.0fms %7.0fms %7.0fms'
              % (libelle[:22], duree, tete * 1000, parole * 1000, queue * 1000))

    print('')
    print('A LIRE : la "queue" est la respiration disponible avant le debut de')
    print('la phrase suivante. Laurent la trouve trop courte sur Kyutai')
    print('(aucune pause ajoutee par le service) et sur Edge (rognage a 0,25 s).')
    print('Le reglage vise +100 ms : voir audio_trim.py pour Edge, et la queue')
    print('de silence du service pour Kyutai.')
    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())
