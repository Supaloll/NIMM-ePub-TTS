# -*- coding: utf-8 -*-
"""
Comparaison chiffree de DEUX castings du meme livre (session du 14/09/2026).

Sert a voir, dans les chiffres, ce qui separe deux moteurs : repartition
narration / personnages, nombre de repliques par personnage, et noms trouves.

Usage :
    python test_voix/_comparer_attributions.py 30 31
    (30 = version locale, 31 = version Gemini)
"""
import sys
import sqlite3
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent

if len(sys.argv) < 3:
    print('Usage : python test_voix/_comparer_attributions.py <book_id_1> <book_id_2>')
    sys.exit(1)

id1, id2 = int(sys.argv[1]), int(sys.argv[2])

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
conn.row_factory = sqlite3.Row


def profil(book_id):
    book = conn.execute("SELECT title, cast_status FROM books WHERE id = ?", (book_id,)).fetchone()
    total = conn.execute("SELECT COUNT(*) AS n FROM speaker_attribution WHERE book_id = ?",
                         (book_id,)).fetchone()['n']
    narr = conn.execute("SELECT COUNT(*) AS n FROM speaker_attribution WHERE book_id = ? AND speaker = 'narration'",
                        (book_id,)).fetchone()['n']
    persos = conn.execute("""
        SELECT speaker AS nom, COUNT(*) AS nb FROM speaker_attribution
        WHERE book_id = ? AND speaker != 'narration'
        GROUP BY speaker ORDER BY nb DESC
    """, (book_id,)).fetchall()
    voix = conn.execute("SELECT COUNT(*) AS n FROM voices WHERE book_id = ?", (book_id,)).fetchone()['n']
    return {
        'titre': book['title'], 'statut': book['cast_status'], 'total': total,
        'narration': narr, 'repliques': total - narr, 'persos': persos, 'voix': voix,
    }


a, b = profil(id1), profil(id2)

print('')
print('=' * 76)
print('COMPARAISON DES ATTRIBUTIONS -- meme livre, deux moteurs')
print('=' * 76)
print('  livre {} : {}'.format(id1, a['titre']))
print('  livre {} : {}'.format(id2, b['titre']))
print('')
print('{:<34} {:>14} {:>14}'.format('', 'local (id {})'.format(id1), 'cloud (id {})'.format(id2)))
print('-' * 76)
print('{:<34} {:>14} {:>14}'.format('phrases attribuees', a['total'], b['total']))
print('{:<34} {:>14} {:>14}'.format('  dont NARRATION', a['narration'], b['narration']))
print('{:<34} {:>14} {:>14}'.format('  dont repliques', a['repliques'], b['repliques']))
if a['total']:
    print('{:<34} {:>13.0f}% {:>13.0f}%'.format(
        '  part de repliques', 100.0 * a['repliques'] / a['total'], 100.0 * b['repliques'] / b['total']))
print('{:<34} {:>14} {:>14}'.format('personnages distincts', len(a['persos']), len(b['persos'])))
print('{:<34} {:>14} {:>14}'.format('voix attribuees', a['voix'], b['voix']))
print('')
print('REPARTITION DES REPLIQUES PAR PERSONNAGE')
print('-' * 76)
print('{:<30} {:>10}   {:<30} {:>10}'.format(
    'version locale', 'repliques', 'version cloud', 'repliques'))
print('-' * 76)
lignes = max(len(a['persos']), len(b['persos']))
for i in range(min(lignes, 18)):
    g = a['persos'][i] if i < len(a['persos']) else None
    d = b['persos'][i] if i < len(b['persos']) else None
    print('{:<30} {:>10}   {:<30} {:>10}'.format(
        (g['nom'] if g else '')[:30], (g['nb'] if g else ''),
        (d['nom'] if d else '')[:30], (d['nb'] if d else '')))
if lignes > 18:
    print('   ... et {} autres lignes'.format(lignes - 18))
print('')

# ==============================================================
# ACCORD PHRASE PAR PHRASE (valable seulement si les deux livres sont le
# MEME texte : meme nombre de chapitres et de phrases -- c'est le cas quand on
# a caste deux fois le meme epub avec deux moteurs differents)
# ==============================================================
paires = conn.execute("""
    SELECT a.chapter_index, a.sentence_idx, a.speaker AS s1, b.speaker AS s2
    FROM speaker_attribution a
    JOIN speaker_attribution b
      ON b.book_id = ? AND a.chapter_index = b.chapter_index
     AND a.sentence_idx = b.sentence_idx
    WHERE a.book_id = ?
""", (id2, id1)).fetchall()

if paires and len(paires) == a['total'] == b['total']:
    sys.path.insert(0, str(BASE))
    from modules.voice_casting import normalize_character_name

    meme_categorie = 0
    meme_nom = 0
    divergences = []
    for p in paires:
        s1, s2 = p['s1'], p['s2']
        c1 = (s1 == 'narration')
        c2 = (s2 == 'narration')
        if c1 == c2:
            meme_categorie += 1
            if c1 or normalize_character_name(s1) == normalize_character_name(s2):
                meme_nom += 1
        elif len(divergences) < 12:
            divergences.append((p['chapter_index'], p['sentence_idx'], s1, s2))

    n = len(paires)
    print('=' * 76)
    print('ACCORD PHRASE PAR PHRASE (meme texte, deux moteurs)')
    print('=' * 76)
    print('  phrases comparees            : {}'.format(n))
    print('  meme categorie (narr/dialogue) : {} ({:.1f} %)'.format(
        meme_categorie, 100.0 * meme_categorie / n))
    print('  meme personnage nomme          : {} ({:.1f} %)'.format(
        meme_nom, 100.0 * meme_nom / n))
    print('  divergences de categorie       : {} ({:.1f} %)'.format(
        n - meme_categorie, 100.0 * (n - meme_categorie) / n))
    if divergences:
        print('')
        print('  Exemples de divergence (chapitre, phrase, moteur {} / moteur {}) :'.format(id1, id2))
        for ch, sid, s1, s2 in divergences:
            print('    ch.{:>2} phrase {:>4} : {:<26} / {}'.format(ch + 1, sid, s1[:26], s2[:26]))
    print('')
else:
    print('(Accord phrase par phrase non calculable : les deux livres n\'ont pas')
    print(' exactement le meme decoupage de phrases.)')
    print('')

conn.close()
print('Fin de la comparaison.')

