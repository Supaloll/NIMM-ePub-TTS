# -*- coding: utf-8 -*-
"""Trace une replique de bout en bout : texte envoye, voix, et fichier de CACHE.

Repond a la question « qu'a donc recu le moteur pour cette phrase ? » :
  1. retrouve la phrase dans le chapitre et le PERSONNAGE qui la dit ;
  2. affiche le texte exact envoye par le lecteur (et son nettoyage) ;
  3. recalcule la CLE DE CACHE (meme formule que modules/tts_cache.py) ;
  4. dit si l'audio existe deja en cache, sa taille et sa DUREE reelle --
     une duree trop longue pour le texte est la signature d'un babil.

Lecture seule. Usage :
    python test_voix/_tracer_phrase_cache.py [book_id] [chapitre] [extrait]
"""

import sqlite3
import sys
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                        # noqa: E402
from modules import tts_cache                                    # noqa: E402
from modules.tts import _clean_text                              # noqa: E402
from modules.voice_casting import _split_chapter_sentences        # noqa: E402

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 35
CHAPITRE = int(sys.argv[2]) if len(sys.argv) > 2 else 1
EXTRAIT = sys.argv[3] if len(sys.argv) > 3 else "agneau"


def duree_wav(chemin):
    try:
        with wave.open(str(chemin), "rb") as f:
            return f.getnframes() / float(f.getframerate())
    except Exception:
        return None


def main_trace():
    base = 'file:%s?mode=ro' % (RACINE / 'data' / 'nimm_epub.db').as_posix()
    conn = sqlite3.connect(base, uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT filename, title FROM books WHERE id = ?',
                         (BOOK_ID,)).fetchone()
    chapitres = get_chapters(str(RACINE / 'data' / 'library' / livre['filename']))
    texte = chapitres[CHAPITRE].get('text') or ''

    phrases = _split_chapter_sentences(texte)
    numeros = [i for i, p in enumerate(phrases) if EXTRAIT in p.get('texte', '')]
    if not numeros:
        print('Extrait introuvable dans le chapitre %d.' % CHAPITRE)
        return

    print('Livre %d : %s | chapitre %d : %s'
          % (BOOK_ID, livre['title'], CHAPITRE, chapitres[CHAPITRE].get('title', '')))
    print('')
    for numero in numeros:
        phrase = phrases[numero]['texte']
        locuteur = conn.execute(
            'SELECT speaker FROM speaker_attribution '
            'WHERE book_id = ? AND chapter_index = ? AND sentence_idx = ?',
            (BOOK_ID, CHAPITRE, numero)).fetchone()
        nom = (locuteur or {'speaker': '?'})['speaker']
        voix = conn.execute(
            'SELECT voice_id, pitch, rate FROM voices WHERE book_id = ? AND character_name = ?',
            (BOOK_ID, nom)).fetchone()
        print('--- phrase n° %d (chapitre), dite par %s' % (numero, nom))
        print('    texte brut du lecteur : %r' % phrase)
        nettoye = _clean_text(phrase)
        print('    texte nettoye (cle)   : %r' % nettoye)
        if not voix:
            print('    aucune voix en base pour ce personnage.')
            continue
        rate = voix['rate'] or '+0%'
        pitch = voix['pitch'] or '+0Hz'
        print('    voix : %s | vitesse %s | hauteur %s'
              % (voix['voice_id'], rate, pitch))
        cle = tts_cache._hash_key(nettoye, voix['voice_id'], rate, pitch)
        for extension in ('wav', 'mp3'):
            chemin = tts_cache.CACHE_DIR / (cle + '.' + extension)
            if chemin.is_file():
                taille = chemin.stat().st_size
                duree = duree_wav(chemin)
                print('    EN CACHE : %s (%s octets%s)'
                      % (chemin.name, taille,
                         ', %.2f s' % duree if duree else ''))
                if duree:
                    # Repere : environ 14 caracteres par seconde en francais.
                    attendu = max(0.8, len(nettoye) / 14.0)
                    verdict = ('NORMAL' if duree <= attendu * 1.8 + 1.2
                               else 'SUSPECT (babil probable)')
                    print('    duree attendue d apres le texte : ~%.1f s -> %s'
                          % (attendu, verdict))
            else:
                print('    pas encore en cache (.%s)' % extension)
        print('')


main_trace()
