# -*- coding: utf-8 -*-
"""Enquete jetable -- moisson d'ecoute de Laurent, 22/11/63 chapitres 10 et 11.

Lecture SEULE : rien n'est modifie (base ouverte en mode=ro).

Question 1 : la voix des personnages < 8 repliques (voix generique par genre).
Question 2 : l'incise « m'a-t-elle repondu » lue avec la voix du personnage.
Question 3 : la narration entre tirets (« il a brandi la baionnette... »).
Question 4 : « Col Bleu sans bretelles » / « Bill Turcotte » (alias non groupes).
Question 5 : Jake Epping / George Amberson (deux noms, un seul personnage).

Usage : python _moisson_22_11_63.py [book_id]
"""

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.decoupage import phrases as _phrases             # noqa: E402
from modules.incises import retirer_incises                   # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

MOTS = ['Mouseketeer', 'baionnette', 'baïonnette', 'Cashman', 'Founijello']

# Chapitres examinés (index en base) : Laurent a écouté les chapitres 10 et 11
# de l'affichage. On prend 9, 10 et 11 pour être sûr de tomber dessus.
CHAPITRES = {9, 10, 11}

conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
conn.row_factory = sqlite3.Row

print('=' * 100)
print('1. LIVRES CANDIDATS')
print('=' * 100)
livres = []
for r in conn.execute('SELECT id, title, filename, saga, narrator_voice, '
                      'decoupe_dialogue, cast_status, multi_voice_enabled '
                      'FROM books ORDER BY id'):
    if '22' in (r['title'] or '') and '63' in (r['title'] or ''):
        livres.append(r)
        print('  livre %-3d  %-45s  saga=%-12s  dialogue=%s  narrateur=%s'
              % (r['id'], (r['title'] or '')[:45], r['saga'] or '-',
                 r['decoupe_dialogue'], r['narrator_voice'] or '-'))

if not livres:
    print('  AUCUN livre 22/11/63 trouve.')
    sys.exit(1)
if len(sys.argv) > 1:
    livres = [l for l in livres if l['id'] == int(sys.argv[1])] or livres
LIVRE = livres[0]
BID = LIVRE['id']

print('')
print('=' * 100)
print('2. PERSONNAGES DU LIVRE %d (%s)' % (BID, LIVRE['title']))
print('=' * 100)
voix = list(conn.execute(
    'SELECT character_name, voice_id, pitch, rate, genre, line_count, locked '
    'FROM voices WHERE book_id = ? ORDER BY line_count DESC', (BID,)))
print('  %-4s %-32s %-26s %-8s %6s %-8s %s'
      % ('#', 'personnage', 'voix', 'hauteur', 'repl.', 'genre', 'vitesse'))
print('  ' + '-' * 96)
for i, r in enumerate(voix[:40], 1):
    print('  %-4s %-32s %-26s %-8s %6s %-8s %s'
          % (i, (r['character_name'] or '')[:32], (r['voice_id'] or '')[:26],
             r['pitch'] or '', r['line_count'], r['genre'] or '?', r['rate'] or ''))
print('  ... total : %d personnages' % len(voix))

generiques = [r for r in voix if (r['voice_id'] or '').startswith('piper:upmc:')]
print('')
print('  PETITS ROLES (voix generique Piper) : %d' % len(generiques))
for r in generiques[:15]:
    print('    %-32s %-16s genre=%s  repl.=%s'
          % ((r['character_name'] or '')[:32], r['voice_id'], r['genre'],
             r['line_count']))

print('')
print('=' * 100)
print('3. NOMS CITES PAR LAURENT')
print('=' * 100)
for motif in ['Annette', 'Founijello', 'Mouseketeer', 'Turcotte', 'Col',
              'Jake', 'Amberson', 'Epping', 'Bill', 'Miss']:
    for r in [x for x in voix if motif.lower() in (x['character_name'] or '').lower()]:
        print('  %-14s -> %-32s voix=%-22s genre=%s repl.=%s'
              % (motif, (r['character_name'] or '')[:32], r['voice_id'] or '',
                 r['genre'], r['line_count']))

print('')
print('=' * 100)
print('4. REGROUPEMENTS D ALIAS EN BASE (character_aliases)')
print('=' * 100)
lignes = list(conn.execute('SELECT alias_name, canonical_name FROM character_aliases '
                           'WHERE book_id = ? ORDER BY canonical_name', (BID,)))
if not lignes:
    print('  (aucun alias enregistre pour ce livre)')
for r in lignes:
    print('  %-34s  ->  %s' % (r['alias_name'], r['canonical_name']))

print('')
print('=' * 100)
print('5. FICHE DE CASTING (cast_fiche)')
print('=' * 100)
for r in conn.execute('SELECT character_name, genre, age FROM cast_fiche '
                      'WHERE book_id = ? ORDER BY character_name', (BID,)):
    if any(m.lower() in (r['character_name'] or '').lower()
           for m in ['Annette', 'Founijello', 'Turcotte', 'Col', 'Jake',
                     'Amberson', 'Miss', 'Mickey']):
        print('  %-34s genre=%s age=%s' % (r['character_name'], r['genre'], r['age']))
total_fiche = conn.execute('SELECT COUNT(*) FROM cast_fiche WHERE book_id = ?',
                           (BID,)).fetchone()[0]
print('  ... %d personnages dans la fiche' % total_fiche)

print('')
print('=' * 100)
print('6. LES PHRASES CITEES PAR LAURENT (texte + attribution reelle)')
print('=' * 100)

from core.epub_parser import get_chapters                            # noqa: E402
from modules.decoupage import REGLE_ACTUELLE, REGLE_DIALOGUE         # noqa: E402

chemin = BIBLIOTHEQUE / LIVRE['filename']
chapitres = get_chapters(str(chemin))
regle = REGLE_DIALOGUE if LIVRE['decoupe_dialogue'] else REGLE_ACTUELLE
print('  Regle de decoupage en service : %s' % regle)
print('  (%d chapitres dans le livre)' % len(chapitres))

for chap in chapitres:
    if chap['index'] not in CHAPITRES:
        continue
    textes = _phrases(chap.get('text') or '', regle)
    print('  chapitre %d : %s  (%d phrases)'
          % (chap['index'], (chap.get('title') or '')[:60], len(textes)))
    lignes = {r['sentence_idx']: r['speaker'] for r in conn.execute(
        'SELECT sentence_idx, speaker FROM speaker_attribution '
        'WHERE book_id = ? AND chapter_index = ?', (BID, chap['index']))}
    for idx, texte in enumerate(textes):
        if not any(m.lower() in texte.lower() for m in MOTS):
            continue
        print('')
        print('  --- chapitre %d (%s) phrase %d ---'
              % (chap['index'], (chap.get('title') or '')[:35], idx))
        for j in range(max(0, idx - 2), min(len(textes), idx + 3)):
            loc = lignes.get(j, '')
            v = next((x for x in voix if x['character_name'] == loc), None)
            nom_voix = (v['voice_id'] if v else '(pas de voix)')
            marque = '  <<<< ICI' if j == idx else ''
            print('   %4d %-24s %-20s %s%s'
                  % (j, (loc or '?')[:24], (nom_voix or '')[:20],
                     textes[j][:100], marque))
            if j == idx:
                propre = retirer_incises(textes[j])
                if propre != textes[j]:
                    print('        APRES RETRAIT DES INCISES : %s' % propre[:150])
                else:
                    print('        (aucune incise retiree ici)')

conn.close()
print('')
print('--- fin de l enquete ---')
