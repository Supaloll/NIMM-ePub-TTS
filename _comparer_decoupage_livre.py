# -*- coding: utf-8 -*-
"""AVANT / APRES : qui lit les beats de narration ? (essai « mode dialogue »)

Affiche, pour un livre, les morceaux ou une NARRATION introduit une replique
(« Et le More, riant, repondit : « ... » ») et le LOCUTEUR ENREGISTRE de chaque
morceau. C'est la preuve a l'oreille : en mode ORIGINE, le beat est colle a la
replique et c'est donc le personnage qui lit la narration ; en mode DIALOGUE, le
beat est un morceau a part, attribue au narrateur.

LECTURE SEULE. Usage :
    python _comparer_decoupage_livre.py 36 origine
    python _comparer_decoupage_livre.py 36 dialogue
"""
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage

LIVRE = int(sys.argv[1]) if len(sys.argv) > 1 else 36
MODE = (sys.argv[2] if len(sys.argv) > 2 else 'origine').lower()
REGLE = (decoupage.REGLE_DIALOGUE if MODE.startswith('d')
         else decoupage.REGLE_ACTUELLE)

BASE = RACINE / 'data' / 'nimm_epub.db'
con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
livre = con.execute('SELECT filename, title, COALESCE(decoupe_dialogue, 0) '
                    'FROM books WHERE id = ?', (LIVRE,)).fetchone()
if not livre:
    print('livre %s introuvable' % LIVRE)
    sys.exit(1)
fichier, titre, drapeau = livre
locuteurs = {(ch, idx): sp for ch, idx, sp in con.execute(
    'SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution '
    'WHERE book_id = ?', (LIVRE,))}
con.close()

chapitres = epub_parser.get_chapters(str(RACINE / 'data' / 'library' / fichier))

print('=' * 78)
print(' %s  (livre %s) -- mode %s  [drapeau du livre : %s]'
      % (titre, LIVRE, MODE.upper(), drapeau))
print('=' * 78)

montres = 0
total_beats = 0
beats_narration = 0
repliques_personnage = 0
for ch, chapitre in enumerate(chapitres):
    morceaux = decoupage.phrases(chapitre.get('text') or '', REGLE)
    for idx, phrase in enumerate(morceaux):
        if REGLE == decoupage.REGLE_DIALOGUE:
            # Le beat est un morceau a part : il finit par ':' et introduit une
            # replique. On montre le beat ET le morceau suivant (la replique).
            est_beat = (decoupage.introduit_une_replique(phrase)
                        and idx + 1 < len(morceaux)
                        and morceaux[idx + 1].lstrip().startswith('«'))
            if est_beat:
                total_beats += 1
                if locuteurs.get((ch, idx)) == 'narration':
                    beats_narration += 1
                if locuteurs.get((ch, idx + 1)) not in (None, 'narration'):
                    repliques_personnage += 1
        else:
            # En mode origine, on repere le morceau qu'on COUPERAIT : il colle le
            # beat et le debut de la replique.
            est_beat = bool(decoupage._couper_avant_replique(
                (0, len(phrase), phrase))[1:])
            if est_beat:
                total_beats += 1
                if locuteurs.get((ch, idx)) != 'narration':
                    beats_narration += 1
        if not est_beat or montres >= 12:
            continue
        print('')
        print('  ch.%d  #%d  locuteur enregistre = %s'
              % (ch, idx, locuteurs.get((ch, idx))))
        print('     beat    : %s' % phrase[:96])
        if REGLE == decoupage.REGLE_DIALOGUE and idx + 1 < len(morceaux):
            print('     replique: %s  -> locuteur = %s'
                  % (morceaux[idx + 1][:66], locuteurs.get((ch, idx + 1))))
        montres += 1
print('')
print('-' * 78)
if REGLE == decoupage.REGLE_DIALOGUE:
    print('  %d beat(s) de narration dans le livre : %d lus par le NARRATEUR,'
          % (total_beats, beats_narration))
    print('  et %d replique(s) attribuees a un PERSONNAGE.'
          % repliques_personnage)
else:
    print('  %d beat(s) de narration dans le livre, dont %d lus par un'
          % (total_beats, beats_narration))
    print('  PERSONNAGE (la narration dans la voix du personnage).')
print('  (%d exemples montres)' % montres)
