# -*- coding: utf-8 -*-
"""Cherche les phrases du cache dont l'audio est ANORMALEMENT LONG.

Signature du babil de XTTS : un texte court (souvent une phrase de quelques
mots) dont l'audio en cache dure beaucoup plus que ce que le texte justifie.
Le fichier est alors rejoue tel quel a chaque ecoute.

Methode : pour chaque phrase d'un livre, on retrouve son locuteur, donc sa
voix, sa vitesse et sa hauteur -- et on recalcule la CLE DE CACHE exacte
(meme formule que modules/tts_cache.py). Si le fichier existe, on compare sa
DUREE REELLE a la duree attendue d'apres le texte.

Lecture seule (aucune suppression). Usage :
    python test_voix/_chercher_babil_cache.py [book_id]
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

# Reperes de duree : environ 14 caracteres par seconde en francais, plus une
# marge. Au-dela, l'audio ne peut pas venir du texte : c'est du babil.
CARACTERES_PAR_SECONDE = 14.0
MARGE_S = 1.2
FACTEUR = 1.8


def duree_de(chemin):
    try:
        with wave.open(str(chemin), "rb") as f:
            return f.getnframes() / float(f.getframerate())
    except Exception:
        return None


def main_recherche():
    base = 'file:%s?mode=ro' % (RACINE / 'data' / 'nimm_epub.db').as_posix()
    conn = sqlite3.connect(base, uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT filename, title FROM books WHERE id = ?',
                         (BOOK_ID,)).fetchone()
    chapitres = get_chapters(str(RACINE / 'data' / 'library' / livre['filename']))

    voix = {(r['character_name']): r for r in conn.execute(
        'SELECT character_name, voice_id, pitch, rate FROM voices WHERE book_id = ?',
        (BOOK_ID,))}
    locuteurs = {(r['chapter_index'], r['sentence_idx']): r['speaker']
                 for r in conn.execute(
                     'SELECT chapter_index, sentence_idx, speaker FROM '
                     'speaker_attribution WHERE book_id = ?', (BOOK_ID,))}
    conn.close()

    print('Livre %d : %s' % (BOOK_ID, livre['title']))
    print('')

    phrases_vues = 0
    en_cache = 0
    suspects = []
    for index, chapitre in enumerate(chapitres):
        texte = chapitre.get('text') or ''
        for numero, phrase in enumerate(_split_chapter_sentences(texte)):
            brut = phrase.get('texte') or ''
            if not brut.strip():
                continue
            nom = locuteurs.get((index, numero))
            if not nom:
                continue
            fiche = voix.get(nom)
            if not fiche or not fiche['voice_id']:
                continue                 # petit role / narration : voix du lecteur
            propre = _clean_text(brut)
            if not propre:
                continue
            phrases_vues += 1
            rate = fiche['rate'] or '+0%'
            pitch = fiche['pitch'] or '+0Hz'
            cle = tts_cache._hash_key(propre, fiche['voice_id'], rate, pitch)
            chemin = tts_cache.CACHE_DIR / (cle + '.wav')
            if not chemin.is_file():
                chemin = tts_cache.CACHE_DIR / (cle + '.mp3')
            if not chemin.is_file():
                continue
            en_cache += 1
            duree = duree_de(chemin)
            if not duree:
                continue
            attendu = max(0.8, len(propre) / CARACTERES_PAR_SECONDE)
            if duree > attendu * FACTEUR + MARGE_S:
                suspects.append((duree, attendu, len(propre), nom,
                                 fiche['voice_id'], propre, index, numero))

    suspects.sort(reverse=True)
    print('Phrases avec voix dediee etudiees : %d' % phrases_vues)
    print('Dont deja en cache                : %d' % en_cache)
    print('SUSPECTES (audio trop long)       : %d' % len(suspects))
    print('')
    for duree, attendu, taille, nom, voix_id, propre, index, numero in suspects[:25]:
        print('  %6.2f s (attendu ~%4.1f s) | %3d car. | %-22s | %s'
              % (duree, attendu, taille, nom[:22], voix_id))
        print('          chapitre %d, phrase %d : %r'
              % (index, numero, propre[:70]))
    if len(suspects) > 25:
        print('  ... et %d autre(s).' % (len(suspects) - 25))

    # Option : copier les suspects dans un dossier d'ecoute (noms lisibles)
    # pour confirmer le diagnostic a l'oreille, ou les PURGER du cache
    # (--purger) pour qu'ils soient regeneres proprement au prochain passage.
    # Le cache est jetable par nature : aucune donnee de Laurent n'est perdue.
    if len(sys.argv) > 2:
        import re
        import shutil
        purger = (sys.argv[2] == '--purger')
        if not purger:
            dossier = Path(sys.argv[2])
            dossier.mkdir(parents=True, exist_ok=True)
        for rang, (duree, attendu, taille, nom, voix_id, propre, index,
                   numero) in enumerate(suspects, 1):
            fiche = voix.get(nom)
            if not fiche:
                continue
            rate = fiche['rate'] or '+0%'
            pitch = fiche['pitch'] or '+0Hz'
            cle = tts_cache._hash_key(propre, fiche['voice_id'], rate, pitch)
            for extension in ('wav', 'mp3'):
                source = tts_cache.CACHE_DIR / (cle + '.' + extension)
                if not source.is_file():
                    continue
                if purger:
                    source.unlink()
                    print('  purge : %s (%.2f s, rejoue jusqu ici)'
                          % (source.name[:16], duree))
                else:
                    etiquette = re.sub(r'[^A-Za-z0-9]+', '_', propre)[:40].strip('_')
                    cible = dossier / ('babil_%02d_%s_%.2fs.%s'
                                       % (rang, etiquette, duree, extension))
                    shutil.copy2(source, cible)
                    print('  copie : %s' % cible.name)
                break


main_recherche()
