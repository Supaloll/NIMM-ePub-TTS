# -*- coding: utf-8 -*-
"""Ce que le SERVEUR renvoie vraiment pour une phrase : mesure de la duree.

Question de Laurent (18/09/2026 au soir) : « j'ai toujours les incises » alors que
le nettoyage les retire (verifie sur le texte). Ce petit outil interroge le
LECTEUR en marche, comme le fait la page (`POST /api/tts`), et mesure la duree
de l'audio renvoye :

    - phrase AVEC son incise, et phrase SANS : si les deux durent pareil, le
      nettoyage n'est PAS applique sur ce chemin (bug a chercher) ;
    - si la phrase avec incise sort courte, le nettoyage est bien applique et
      c'est le CACHE (fichier deja genere) qu'il faut vider.

Le serveur du lecteur doit etre allume (port 8081). Aucune synthese n'est
inventee : tout passe par l'application.

Usage :
    python test_voix/_tester_tts_serveur.py
    python test_voix/_tester_tts_serveur.py --voix kokoro:ff_siwis
"""

import argparse
import io
import json
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.tts import _clean_text                                  # noqa: E402

SERVEUR = "http://127.0.0.1:8081"

PHRASES = [
    '\u2014 Mais oui, r\u00e9pondit Cavalcanti avec un accent plein de modestie.',
    '\u2014 Elle est surtout fort riche, \u00e0 ce que je crois du moins, dit Monte-Cristo.',
    '\u2014 Sans compter, ajouta Monte-Cristo, qu\u2019il est \u00e0 la veille d\u2019entrer dans un genre de sp\u00e9culation.',
]


def demander(texte, voix, rate, pitch):
    corps = json.dumps({"text": texte, "voice": voix, "rate": rate,
                        "pitch": pitch, "context": ""},
                       ensure_ascii=False).encode('utf-8')
    requete = urllib.request.Request(
        SERVEUR + "/api/tts", data=corps,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(requete, timeout=120) as reponse:
            return reponse.read(), reponse.headers.get('Content-Type', '')
    except urllib.error.HTTPError as erreur:
        try:
            detail = erreur.read().decode('utf-8', 'replace')
        except Exception:
            detail = ''
        raise RuntimeError('%s : %s' % (erreur.code, detail[:160]))


def duree(octets, type_contenu):
    """Duree en secondes, WAV ou MP3 (via ffmpeg pour le MP3)."""
    if not octets:
        return 0.0
    if 'wav' in (type_contenu or '').lower() or octets[:4] == b'RIFF':
        try:
            with wave.open(io.BytesIO(octets), 'rb') as f:
                return f.getnframes() / float(f.getframerate())
        except Exception:
            return 0.0
    try:
        import subprocess
        from imageio_ffmpeg import get_ffmpeg_exe
        cmd = [get_ffmpeg_exe(), '-v', 'error', '-i', 'pipe:0', '-f', 'null', '-']
        r = subprocess.run(cmd, input=octets, capture_output=True, timeout=60)
        # ffmpeg ecrit le resume sur stderr : on relit la duree autrement
        import re
        m = re.search(rb'time=(\d+):(\d+):(\d+\.\d+)', r.stderr)
        if m:
            h, mn, s = (float(x) for x in m.groups())
            return h * 3600 + mn * 60 + s
    except Exception:
        pass
    return 0.0


def main():
    analyseur = argparse.ArgumentParser(
        description="Ce que le serveur renvoie pour une phrase (mesure).")
    analyseur.add_argument('--voix', default='fr-FR-HenriNeural',
                           help='voix a interroger (defaut : Edge Henri)')
    analyseur.add_argument('--rate', default='+0%')
    analyseur.add_argument('--pitch', default='+0Hz')
    options = analyseur.parse_args()

    print('')
    print('=' * 78)
    print('CE QUE LE SERVEUR RENVOIE VRAIMENT (voix %s)' % options.voix)
    print('=' * 78)
    print('')
    print('  1) la phrase NETTOYEE (ce que le serveur devrait envoyer au moteur)')
    print('  2) la phrase d ORIGINE (avec son incise)')
    print('  -> si les deux durent pareil, le nettoyage n est pas applique.')
    print('     si la 1re est nettement plus courte, le nettoyage agit :')
    print('     c est alors le CACHE qu il faut vider.')

    for numero, phrase in enumerate(PHRASES, 1):
        nettoyee = _clean_text(phrase)
        print('')
        print('PHRASE %d' % numero)
        print('  nettoyee : %s' % nettoyee[:110])
        for libelle, texte in (('attendue', nettoyee), ('origine', phrase)):
            try:
                octets, type_contenu = demander(texte, options.voix,
                                                options.rate, options.pitch)
            except Exception as erreur:
                print('    %-9s ECHEC : %s' % (libelle, erreur))
                continue
            print('    %-9s %6.2f s  (%s, %d octets)'
                  % (libelle, duree(octets, type_contenu), type_contenu, len(octets)))
    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())
