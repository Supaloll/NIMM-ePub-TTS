# -*- coding: utf-8 -*-
"""
ETUDE (lecture seule, gratuit) : combien de phrases contiennent une INCISE
(« ... », dit Franz) qui pourrait etre lue par le narrateur au lieu du
personnage ? -- piste proposee par Laurent le 13/09/2026.

On reste VOLONTAIREMENT prudent : on ne detecte que le cas sans ambiguite,
c'est-a-dire une incise placee APRES un guillemet fermant. Sans ce signal, le
risque de confondre une incise avec le verbe de la replique elle-meme est trop
grand ("— Il m'a dit de partir." : "dit" n'est pas une incise).

Lancer depuis la racine : python test_voix/_etude_incises.py 28
"""
import sys
import re
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 28

VERBES = (r"(dit|dis|dire|répondit|repondit|répond|repond|demanda|demand|"
          r"s'écria|s'ecria|ajouta|ajout|reprit|reprenn|murmura|murmur|"
          r"s'étonna|setonna|répéta|repeta|continua|poursuivit|observa|"
          r"remarqua|soupira|soupir|grommela|lança|lanca|protesta|conclut|"
          r"avoua|annonça|annoca|annonc|cria|appela|précisa|precisa|"
          r"expliqua|expliqu|répliqua|repliqua|hasarda|insista|s'exclama|"
          r"sexclama|marmonna|bougonna|rican|s'inquiéta|setonne)")

# Incise APRES un guillemet fermant (cas sur), avec ou sans virgule, et
# forme inversee frequente en francais : "dit-il", "reprit-elle".
RE_INCISE = re.compile(r'[»"]\s*[,;:]?\s*' + VERBES + r'(?:-[a-zà-ÿ]+)?\b.*$', re.IGNORECASE)

# Incise APRES UN TIRET DE DIALOGUE (style francais : "— Je pars, dit Franz").
# Plus risque que le guillemet, car le verbe de parole peut appartenir a la
# replique elle-meme : on exige un debut de phrase par tiret ET une virgule
# juste avant le verbe, en fin de phrase.
RE_TIRET = re.compile(r'^\s*[—–-]\s+.*,\s*' + VERBES + r'(?:-[a-zà-ÿ]+)?\b[^»"«]*$',
                      re.IGNORECASE | re.DOTALL)

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
attrib = {(r[0], r[1]): r[2] for r in conn.execute(
    "SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution WHERE book_id = ?",
    (BOOK_ID,))}
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))

total = 0
total_repliques = 0
avec_incise = 0
car_incise = 0
car_total_repliques = 0
avec_tiret = 0
car_tiret = 0
exemples = []
exemples_tiret = []

for ch in chapters:
    for s in vc._split_chapter_sentences(ch['text']):
        locuteur = attrib.get((ch['index'], s['id']))
        if locuteur is None:
            continue
        total += 1
        if locuteur == 'narration':
            continue
        total_repliques += 1
        car_total_repliques += len(s['texte'])
        m = RE_INCISE.search(s['texte'])
        if m:
            avec_incise += 1
            car_incise += len(m.group(0))
            if len(exemples) < 8:
                exemples.append((ch['index'] + 1, s['id'], len(m.group(0)), locuteur))
        mt = RE_TIRET.search(s['texte'])
        if mt:
            avec_tiret += 1
            car_tiret += len(mt.group(0))
            if len(exemples_tiret) < 8:
                exemples_tiret.append((ch['index'] + 1, s['id'], len(mt.group(0)), locuteur))

print('')
print('=' * 70)
print('INCISES DETECTABLES -- {}'.format(book[1]))
print('=' * 70)
print('Phrases analysees          : {:,}'.format(total).replace(',', ' '))
print('Dont attribuees a un personnage : {:,}'.format(total_repliques).replace(',', ' '))
print('')
print('PHRASES AVEC UNE INCISE APRES GUILLEMET (cas sur) : {:,}'.format(avec_incise).replace(',', ' '))
if total_repliques:
    print('  soit {:.1f} % des repliques'.format(100.0 * avec_incise / total_repliques))
if car_total_repliques:
    print('  et {:.1f} % des caracteres de repliques'.format(100.0 * car_incise / car_total_repliques))
print('  caracteres concernes : {:,}'.format(car_incise).replace(',', ' '))
print('')
print('PHRASES AVEC UNE INCISE APRES UN TIRET DE DIALOGUE : {:,}'.format(avec_tiret).replace(',', ' '))
if total_repliques:
    print('  soit {:.1f} % des repliques'.format(100.0 * avec_tiret / total_repliques))
if car_total_repliques:
    print('  et {:.1f} % des caracteres de repliques'.format(100.0 * car_tiret / car_total_repliques))
print('  caracteres concernes : {:,}'.format(car_tiret).replace(',', ' '))
print('')
if exemples_tiret:
    print('Exemples (chapitre, phrase, longueur de l\'incise, locuteur actuel) :')
    for ch_num, sid, longueur, locuteur in exemples_tiret:
        print('   chapitre {:>3}, phrase {:>4} : incise de {:>3} caracteres'.format(
            ch_num, sid, longueur))
print('')
if exemples:
    print('Exemples (chapitre, phrase, longueur de l\'incise, locuteur actuel) :')
    for ch_num, sid, longueur, locuteur in exemples:
        print('   chapitre {:>3}, phrase {:>4} : incise de {:>3} caracteres (locuteur {} -> narrateur)'.format(
            ch_num, sid, longueur, locuteur))
print('')
print('Lecture du resultat :')
print('  - un faible pourcentage = le gain d\'ecoute est marginal, on laisse tomber ;')
print('  - un pourcentage eleve = le gain est audible, la piste vaut le travail.')
print('')
print('Fin de l\'etude.')
