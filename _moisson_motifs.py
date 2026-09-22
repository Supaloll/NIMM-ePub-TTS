# -*- coding: utf-8 -*-
"""Enquete jetable n3 -- mesure des trois motifs signales par Laurent.

Lecture SEULE.

  A. « George Amberson » existe-t-il quelque part dans la base ?
  B. Motif 1 : narration ENTRE TIRETS a l'interieur d'une replique
     (« – il a brandi la baionnette ... –, « ce sera moi. »).
  C. Motif 2 : incises d'AUXILIAIRE + PARTICIPE (« m'a-t-elle repondu »,
     « me dit Annette », « l'ai-je complimentee ») que le module incises.py
     ne reconnait pas aujourd'hui.

Usage : python _moisson_motifs.py [book_id]
"""

import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                       # noqa: E402
from modules.decoupage import (phrases as _phrases,             # noqa: E402
                               REGLE_DIALOGUE)
from modules.incises import retirer_incises                     # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
BID = int(sys.argv[1]) if len(sys.argv) > 1 else 28

conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
conn.row_factory = sqlite3.Row

# ---------------------------------------------------------------- A
print('=' * 96)
print('A. « GEORGE AMBERSON » DANS LA BASE (tous les livres)')
print('=' * 96)
for table, col in (('voices', 'character_name'), ('cast_fiche', 'character_name'),
                   ('speaker_attribution', 'speaker')):
    for motif in ('%Amberson%', '%George%'):
        n = conn.execute('SELECT COUNT(*) FROM %s WHERE %s LIKE ?' % (table, col),
                         (motif,)).fetchone()[0]
        print('  %-20s %-12s : %4d ligne(s)' % (table, motif, n))
print('')
for r in conn.execute("SELECT book_id, character_name, voice_id, line_count "
                      "FROM voices WHERE character_name LIKE '%Amberson%' "
                      "OR character_name LIKE '%George%' ORDER BY book_id"):
    print('  voices      livre %-4d %-30s %-24s %s'
          % (r['book_id'], r['character_name'], r['voice_id'], r['line_count']))
for r in conn.execute("SELECT book_id, speaker, COUNT(*) n FROM speaker_attribution "
                      "WHERE speaker LIKE '%Amberson%' GROUP BY book_id, speaker"):
    print('  attribution livre %-4d %-30s %s phrase(s)'
          % (r['book_id'], r['speaker'], r['n']))

# ---------------------------------------------------------------- B et C
livre = conn.execute('SELECT title, filename FROM books WHERE id = ?', (BID,)).fetchone()
chemin = BIBLIOTHEQUE / livre['filename']
print('')
print('=' * 96)
print('B/C. MOTIFS DANS LE LIVRE %d (%s)' % (BID, livre['title']))
print('=' * 96)

# B : narration entre tirets, suivie d'une replique.
MOTIF_TIRETS = re.compile(r'^[\u2013\u2014\-]\s.+\s[\u2013\u2014\-],\s*[\u00ab"]')
# C : incise d'auxiliaire + participe (« m'a-t-elle repondu »).
AUX = r'(?:ai|as|a|avons|avez|ont)'
PRONOM = r'(?:il|elle|on|ils|elles)'
DEBUT_M = r"(?:m[\u2019']|t[\u2019']|l[\u2019']|me\s|te\s|lui\s|nous\s|vous\s)?"
MOTIF_AUX = re.compile(r'[,;\u2013\u2014]\s*' + DEBUT_M + AUX + r'[\u2013-]?t?[\u2013-]?'
                       + PRONOM + r'\s+\w')
# Les participes de parole courants, pour savoir si l'incise dit QUI parle.
PARTICIPES = ('repondu', 'demande', 'dit', 'ajoute', 'murmure', 'replique',
              'crie', 'repondu', 'recommande', 'explique', 'declare', 'avoue',
              'repondu', 'grince', 'soupire', 'lance', 'repondu')
MOTIF_PART = re.compile(r'\b(?:%s)\b' % '|'.join(set(PARTICIPES)), re.IGNORECASE)

total_phrases = 0
tirets = []
incises_aux = []
incises_aux_parole = []
for chap in get_chapters(str(chemin)):
    textes = _phrases(chap.get('text') or '', REGLE_DIALOGUE)
    total_phrases += len(textes)
    for idx, t in enumerate(textes):
        if MOTIF_TIRETS.search(t):
            tirets.append((chap['index'], idx, t))
        m = MOTIF_AUX.search(t)
        if m:
            incises_aux.append((chap['index'], idx, t, m.group(0)))
            if MOTIF_PART.search(t):
                incises_aux_parole.append((chap['index'], idx, t))
                # Retrait possible aujourd'hui ?
                if retirer_incises(t) == t:
                    pass

print('  %d phrases dans le livre.' % total_phrases)
print('')
print('  MOTIF 1 (narration entre tirets puis replique) : %d phrase(s)' % len(tirets))
for c, i, t in tirets[:8]:
    print('    chap. %-3d phrase %-5d %s' % (c, i, t[:150]))
print('')
print('  MOTIF 2 (incise d auxiliaire + participe) : %d phrase(s)' % len(incises_aux))
print('    dont la parole est nommee (repondu, dit, recommande...) : %d'
      % len(incises_aux_parole))
inchangees = [x for x in incises_aux_parole if retirer_incises(x[2]) == x[2]]
print('    dont le module incises.py ne retire RIEN aujourd hui : %d'
      % len(inchangees))
for c, i, t, g in incises_aux[:10]:
    etat = 'RETIREE' if retirer_incises(t) != t else 'LAISSEE'
    print('    chap. %-3d phrase %-5d [%-8s] %s' % (c, i, etat, t[:130]))
print('')
print('  --- echantillon des incises d auxiliaire LAISSEES malgre un verbe de parole ---')
for c, i, t in incises_aux_parole[:10]:
    if retirer_incises(t) == t:
        print('    chap. %-3d %s' % (c, t[:150]))

conn.close()
print('')
print('--- fin ---')
