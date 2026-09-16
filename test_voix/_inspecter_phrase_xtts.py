# -*- coding: utf-8 -*-
"""Que recoit VRAIMENT le moteur XTTS pour une phrase donnee ? (lecture seule)

- retrouve la phrase dans un chapitre du livre ;
- affiche le texte exact, caractere par caractere la ou c'est utile ;
- rejoue le DECOUPAGE et le NETTOYAGE du service XTTS
  (xtts_service/servir_xtts.py, fonctions extraites du fichier reel --
   jamais recopiees) ;
- affiche le nettoyage du lecteur (modules/tts._clean_text).

Usage : python test_voix/_inspecter_phrase_xtts.py [book_id] [chapitre] [extrait]
"""

import io
import os
import re
import sqlite3
import sys
import threading
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                        # noqa: E402
from modules.tts import _clean_text                              # noqa: E402

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 35
CHAPITRE = int(sys.argv[2]) if len(sys.argv) > 2 else 1
EXTRAIT = sys.argv[3] if len(sys.argv) > 3 else "agneau"

SERVICE = RACINE / 'xtts_service' / 'servir_xtts.py'


def fonctions_du_service():
    """Charge les fonctions de decoupage/nettoyage du service, sans le moteur.

    Elles sont extraites DU FICHIER REEL : si elles changent la-bas, ce script
    les voit changer ici (aucune copie a maintenir). On prend soigneusement :
      - les constantes de reglage (MAX_CARACTERES, seuils, abreviations...) ;
      - les fonctions de decoupage et de nettoyage ;
    et on evite le chargement du moteur (torch, coqui-tts) et les variables
    propres au service (_moteur, _infos...).
    """
    source = SERVICE.read_text(encoding='utf-8')
    bornes = [
        ('MAX_CARACTERES = 250', '# Une seule generation a la fois'),
        ('def _commence_minuscule', '# LES VOIX (extraits de reference a cloner)'),
    ]
    espace = {'re': re, 'io': io, 'os': os, 'sys': sys, 'time': time,
              'threading': threading, 'json': __import__('json')}
    for debut_balise, fin_balise in bornes:
        fragment = source[source.index(debut_balise):source.index(fin_balise)]
        exec(compile(fragment, str(SERVICE), 'exec'), espace)
    return espace


def montre(texte, etiquette):
    print('  %s' % etiquette)
    print('    longueur : %d caracteres' % len(texte))
    print('    texte    : %s' % texte)
    suspects = [(i, c) for i, c in enumerate(texte)
                if ord(c) > 127 or c in '\t\r\n']
    if suspects:
        print('    caracteres speciaux :')
        for position, caractere in suspects:
            print('      position %3d : %r (U+%04X)'
                  % (position, caractere, ord(caractere)))
    else:
        print('    caracteres speciaux : aucun')


def main_inspection():
    conn = sqlite3.connect(
        'file:%s?mode=ro' % (RACINE / 'data' / 'nimm_epub.db').as_posix(), uri=True)
    ligne = conn.execute('SELECT filename, title FROM books WHERE id = ?',
                         (BOOK_ID,)).fetchone()
    conn.close()
    if not ligne:
        print('Livre %d introuvable.' % BOOK_ID)
        return
    fichier, titre = ligne
    chapitres = get_chapters(str(RACINE / 'data' / 'library' / fichier))
    if CHAPITRE >= len(chapitres):
        print('Le livre n a que %d chapitres.' % len(chapitres))
        return
    texte = chapitres[CHAPITRE].get('text') or ''

    print('Livre %d : %s' % (BOOK_ID, titre))
    print('Chapitre %d : %s' % (CHAPITRE, chapitres[CHAPITRE].get('title', '')))
    print('Recherche de : %r' % EXTRAIT)
    print('')
    position = texte.find(EXTRAIT)
    if position < 0:
        print('Extrait introuvable dans ce chapitre.')
        return
    # Le paragraphe qui contient la phrase, puis la phrase elle-meme.
    debut_paragraphe = texte.rfind('\n', 0, position) + 1
    fin_paragraphe = texte.find('\n', position)
    if fin_paragraphe < 0:
        fin_paragraphe = len(texte)
    paragraphe = texte[debut_paragraphe:fin_paragraphe]
    print('PARAGRAPHE COMPLET (ce que le lecteur decoupe en phrases) :')
    montre(paragraphe, '')
    print('')

    espace = fonctions_du_service()
    phrases = espace['decouper_phrases'](paragraphe)
    print('DECOUPAGE DU PARAGRAPHE EN PHRASES (service XTTS) : %d phrase(s)'
          % len(phrases))
    for numero, phrase in enumerate(phrases, 1):
        print('')
        montre(phrase, 'phrase %d' % numero)

    print('')
    print('PLAN DE LECTURE (morceaux reellement envoyes au moteur) :')
    plan = espace['plan_de_lecture'](paragraphe)
    for numero, morceaux in enumerate(plan, 1):
        for rang, morceau in enumerate(morceaux, 1):
            print('')
            print('  phrase %d, morceau %d :' % (numero, rang))
            montre(morceau, 'brut (recu du lecteur)')
            montre(espace['nettoyer_pour_xtts'](morceau), 'nettoye (envoye a XTTS)')
    print('')
    print('CE QUE FAIT LE LECTEUR AVANT L ENVOI (modules.tts._clean_text) :')
    montre(_clean_text(paragraphe), 'clean_text(paragraphe)')


main_inspection()
