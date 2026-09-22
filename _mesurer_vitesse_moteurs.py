# -*- coding: utf-8 -*-
"""MESURE : la REACTIVITE des moteurs de voix (question de Laurent, 22/09/2026).

« Les frequences ont-elles une influence sur la vitesse de generation ? Si on
baisse la frequence, est-ce qu'on gagne en reactivite ? »

Ce script CHRONOMETRE les moteurs sur la MEME phrase, une phrase NEUVE (jamais
synthetisee, donc pas servie par le cache), et rapporte le rapport « vitesse /
temps reel » -- la convention deja utilisee dans ARCHITECTURE.md (« 1 h d'audio
= 18 min de calcul » pour Kyutai).

Ce qu'on cherche a voir : ce qui fait la reactivite, c'est le MOTEUR (et la
longueur du texte), pas la frequence de sortie.

Lecture seule : aucune donnee n'est modifiee (on ajoute meme des morceaux au
cache audio, ce qui est sans consequence).

Usage : python _mesurer_vitesse_moteurs.py [--livre 28] [--chapitre 20]
"""

import argparse
import io
import json
import sqlite3
import sys
import time
import urllib.request
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

SERVEUR = 'http://127.0.0.1:8081'
BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

# Les voix a comparer : un petit role (Piper), un personnage (Kokoro), le
# narrateur du livre (Kyutai), et une voix du reseau (Edge), pour voir la
# difference de nature entre un modele local et un service distant.
VOIX = [
    ('Piper (processeur)', 'piper:upmc:1'),
    ('Kokoro',             'kokoro:am_onyx'),
    ('Kyutai',             'kyutai:1770_1028_000036-0002'),
    ('Edge (reseau)',      'fr-FR-DeniseNeural'),
]


def demander(texte, voix, book_id):
    """(octets du WAV, secondes ecoulees) pour un texte au serveur NIMM."""
    corps = json.dumps({'text': texte, 'voice': voix, 'rate': '+0%',
                        'pitch': '+0Hz', 'book_id': book_id}).encode('utf-8')
    requete = urllib.request.Request(SERVEUR + '/api/tts', data=corps,
                                     headers={'Content-Type': 'application/json'})
    debut = time.perf_counter()
    with urllib.request.urlopen(requete, timeout=300) as reponse:
        octets = reponse.read()
    return octets, time.perf_counter() - debut


def duree(octets):
    """(secondes d'audio, cadence, canaux, bits)."""
    try:
        with wave.open(io.BytesIO(octets), 'rb') as f:
            return (f.getnframes() / float(f.getframerate() or 1),
                    f.getframerate(), f.getnchannels(), f.getsampwidth() * 8)
    except Exception:
        return 0.0, 0, 0, 0


def phrase_neuve(book_id, chapitre):
    """Une phrase reelle du livre, prise dans un chapitre NON encore ecoute.

    Pourquoi une phrase neuve : le cache repondrait en quelques millisecondes et
    fausserait la mesure -- on veut le temps de CALCUL du moteur.
    """
    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT title, filename, decoupe_dialogue FROM books '
                         'WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    if livre is None:
        return None, None
    from core.epub_parser import get_chapters
    from modules.decoupage import phrases as _decouper
    from modules.decoupage import REGLE_ACTUELLE, REGLE_DIALOGUE
    regle = REGLE_DIALOGUE if livre['decoupe_dialogue'] else REGLE_ACTUELLE
    for ch in get_chapters(str(BIBLIOTHEQUE / livre['filename'])):
        if ch['index'] != chapitre:
            continue
        for texte in _decouper(ch.get('text') or '', regle):
            if 90 <= len(texte) <= 160:
                return texte, livre['title']
    return None, livre['title']


def main():
    analyseur = argparse.ArgumentParser(
        description='Chronometre les moteurs de voix sur une meme phrase neuve.')
    analyseur.add_argument('--livre', type=int, default=28)
    analyseur.add_argument('--chapitre', type=int, default=20,
                           help='chapitre OU PRENDRE la phrase (defaut : 20)')
    options = analyseur.parse_args()

    try:
        with urllib.request.urlopen(SERVEUR + '/api/users', timeout=5):
            pass
    except Exception as erreur:
        print('Le serveur NIMM ne repond pas sur %s (%s).' % (SERVEUR, erreur))
        print('Double-clique sur START.bat, puis relance.')
        return 1

    texte, titre = phrase_neuve(options.livre, options.chapitre)
    if not texte:
        print('Phrase introuvable (livre %d, chapitre %d).'
              % (options.livre, options.chapitre))
        return 1

    print('')
    print('=' * 92)
    print('VITESSE DES MOTEURS -- livre %s, chapitre %d' % (titre, options.chapitre))
    print('=' * 92)
    print('Phrase de mesure (%d caracteres) :' % len(texte))
    print('  %s' % texte[:140])
    print('')
    print('%-22s %10s %11s %10s %12s %9s'
          % ('moteur', 'audio', 'calcul', 'x temps', 'poids WAV', 'cadence'))
    print('-' * 92)

    for libelle, voix in VOIX:
        try:
            octets, ecoule = demander(texte, voix, options.livre)
        except Exception as erreur:
            print('%-22s   indisponible (%s)' % (libelle, str(erreur)[:40]))
            continue
        secondes, cadence, canaux, bits = duree(octets)
        rapport = (secondes / ecoule) if ecoule > 0 else 0
        print('%-22s %9.2f s %10.2f s %9.1f x %10.0f ko %7d Hz'
              % (libelle, secondes, ecoule, rapport, len(octets) / 1024.0,
                 cadence))
        if rapport > 50:
            print('    (rapport anormalement eleve : cette phrase etait sans doute'
                  ' deja en cache)')

    print('')
    print('Lecture : « x temps » = combien de fois plus vite que le temps reel.')
    print('Repere deja dans la doc : Kyutai annonce x3,3 sur la RTX 4060.')
    print('')
    print('Le POIDS, lui, ne bouge QU AVEC la frequence et le format :')
    print('  WAV 24 000 Hz mono 16 bits = 48 ko/s (2,9 Mo/min) ;')
    print('  WAV 16 000 Hz = 32 ko/s ; MP3 32 kbit/s = 4 ko/s (12 fois moins).')
    return 0


if __name__ == '__main__':
    sys.exit(main())

