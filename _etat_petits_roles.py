# -*- coding: utf-8 -*-
"""Diagnostic (LECTURE SEULE) : ou en sont les PETITS ROLES dans la base ?

Question de Laurent (21/09/2026) : faire jouer les personnages de moins de
8 repliques par deux voix generiques Piper -- Jessica (femmes) et Pierre
(hommes). Avant de proposer un plan, ce script dit ce que la base contient
AUJOURD'HUI, livre par livre.

Il ne modifie RIEN : la base est ouverte en lecture seule.
Usage : python _etat_petits_roles.py
"""
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'data/nimm_epub.db'
SEUIL = 8

con = sqlite3.connect('file:' + BASE + '?mode=ro', uri=True)
cur = con.cursor()

print('== Colonnes de la table voices ==')
for ligne in cur.execute('PRAGMA table_info(voices)'):
    print('   ', ligne[1], ligne[2])

print()
print('== Livres et petits roles (< %d repliques) ==' % SEUIL)
cur.execute("""
    SELECT b.id, b.title,
           COUNT(v.character_name) AS total,
           SUM(CASE WHEN v.line_count < ? THEN 1 ELSE 0 END) AS petits,
           SUM(CASE WHEN v.line_count < ? AND (v.voice_id IS NULL OR v.voice_id = '')
                    THEN 1 ELSE 0 END) AS petits_sans_voix
      FROM books b LEFT JOIN voices v ON v.book_id = b.id
     GROUP BY b.id ORDER BY b.title
""", (SEUIL, SEUIL))
for bid, titre, total, petits, sans_voix in cur.fetchall():
    print('   #%s %-46s total %4s | <8 : %4s | dont SANS voix : %4s'
          % (bid, (titre or '?')[:46], total, petits, sans_voix))

print()
print('== Detail des petits roles qui ONT deja une voix ==')
cur.execute("""
    SELECT b.title, v.character_name, v.voice_id, v.line_count, v.locked
      FROM voices v JOIN books b ON b.id = v.book_id
     WHERE v.line_count < ? AND v.voice_id IS NOT NULL AND v.voice_id != ''
     ORDER BY b.title, v.line_count DESC
""", (SEUIL,))
lignes = cur.fetchall()
print('   ', len(lignes), 'lignes')
for titre, nom, vid, n, locked in lignes[:25]:
    print('    %-28s %-26s %-16s %s repl. %s'
          % ((titre or '?')[:28], nom[:26], vid, n, 'VERROUILLE' if locked else ''))

print()
print('== Petits roles : verrou, genre, voix deja posee, hauteur ==')
cur.execute('SELECT locked, COUNT(*) FROM voices WHERE line_count < ? GROUP BY locked',
            (SEUIL,))
for verrou, n in cur.fetchall():
    print('   %-10s : %s ligne(s)' % ('VERROUILLE' if verrou else 'libre', n))
cur.execute('SELECT genre, COUNT(*) FROM voices WHERE line_count < ? GROUP BY genre',
            (SEUIL,))
for genre, n in cur.fetchall():
    print('   genre %-6s : %s ligne(s)' % (genre, n))
cur.execute("""
    SELECT CASE WHEN v.voice_id IS NULL OR v.voice_id = '' THEN '(VIDE : narrateur)'
                ELSE v.voice_id END AS quoi, COUNT(*) AS n
      FROM voices v WHERE v.line_count < ? GROUP BY quoi ORDER BY n DESC
""", (SEUIL,))
print('   voix portees aujourd hui par ces petits roles :')
for quoi, n in cur.fetchall():
    print('      %-30s %s' % (quoi[:30], n))
cur.execute('SELECT pitch, COUNT(*) FROM voices WHERE line_count < ? GROUP BY pitch',
            (SEUIL,))
print('   hauteurs (pitch) :', dict(cur.fetchall()))

# ORPHELINES : des lignes de voix dont le livre n'existe plus. Elles sont
# invisibles dans l'application (qui part de la liste des livres) mais elles
# existent encore en base -- c'est ce qui explique un total global plus gros
# que la somme des livres.
cur.execute('SELECT COUNT(*) FROM voices WHERE book_id NOT IN (SELECT id FROM books)')
print('   lignes ORPHELINES (livre supprime) :', cur.fetchone()[0])

print()
print('== Ce qu une migration ciblee toucherait, livre par livre ==')
cur.execute("""
    SELECT b.title, v.genre,
           SUM(CASE WHEN v.voice_id <> 'piper:upmc:0' AND v.genre = 'F' THEN 1 ELSE 0 END),
           SUM(CASE WHEN v.voice_id <> 'piper:upmc:1' AND v.genre <> 'F' THEN 1 ELSE 0 END)
      FROM voices v JOIN books b ON b.id = v.book_id
     WHERE v.line_count < ? AND (v.locked IS NULL OR v.locked = 0)
     GROUP BY b.id ORDER BY b.title
""", (SEUIL,))
for titre, _g, nf, nh in cur.fetchall():
    print('   %-46s femmes -> Jessica : %3s | hommes -> Pierre : %3s'
          % ((titre or '?')[:46], nf, nh))

print()
print('== Variations possibles (vitesse x hauteur) et BESOIN reel ==')
# Les bornes sont celles des curseurs du casting (frontend/app.js) :
#   vitesse : -30 % a +30 %, pas de 5  -> 13 crans
#   hauteur : -20 Hz a +20 Hz, pas de 4 -> 11 crans
# Une voix generique peut donc porter 13 x 11 = 143 couples (hauteur, vitesse)
# differents. Question de Laurent (21/09/2026) : est-ce assez pour tous les
# personnages de moins de 8 repliques ?
CRANS_PITCH = 11
CRANS_RATE = 13
print('   hauteur : %d crans x vitesse : %d crans = %d variations par voix'
      % (CRANS_PITCH, CRANS_RATE, CRANS_PITCH * CRANS_RATE))
print('   (Jessica : %d variations possibles ; Pierre : %d -- les deux voix '
      'generiques)' % (CRANS_PITCH * CRANS_RATE, CRANS_PITCH * CRANS_RATE))
cur.execute("""
    SELECT b.title, v.genre, COUNT(*) AS n
      FROM voices v JOIN books b ON b.id = v.book_id
     WHERE v.line_count < ?
     GROUP BY b.id, v.genre ORDER BY n DESC LIMIT 6
""", (SEUIL,))
print('   les plus gros besoins, par livre et par genre :')
for titre, genre, n in cur.fetchall():
    print('      %-40s %s : %3d petits roles' % ((titre or '?')[:40], genre, n))
cur.execute("""
    SELECT MAX(n) FROM (SELECT COUNT(*) AS n FROM voices v
                          JOIN books b ON b.id = v.book_id
                         WHERE v.line_count < ? GROUP BY v.book_id, v.genre)
""", (SEUIL,))
besoin = cur.fetchone()[0]
print('   besoin MAXIMUM dans un livre, pour un seul genre : %d' % besoin)
print('   -> couverture : %s'
      % ('LARGEMENT SUFFISANTE' if CRANS_PITCH * CRANS_RATE >= besoin
         else 'INSUFFISANTE : il faudrait elargir les bornes'))
cur.execute('SELECT rate, COUNT(*) FROM voices WHERE line_count < ? GROUP BY rate',
            (SEUIL,))
print('   vitesses actuelles des petits roles :', dict(cur.fetchall()))
cur.execute('SELECT pitch, COUNT(*) FROM voices WHERE line_count < ? GROUP BY pitch '
            'ORDER BY COUNT(*) DESC LIMIT 5', (SEUIL,))
print('   hauteurs les plus frequentes :', dict(cur.fetchall()))

print()
print('== Collisions : deux petits roles d un meme livre au meme timbre EXACT ==')
# Un « timbre exact » = meme voix + meme hauteur + meme vitesse. Depuis la
# repartition du 21/09/2026, deux petits roles d'un meme livre et d'un meme
# genre ne devraient JAMAIS tomber sur le meme couple, sauf au-dela de 143.
# Les lignes VERROUILLEES, elles, n'ont pas ete touchees : une collision peut
# donc encore les concerner, et c'est normal (un verrou = « je garde »).
cur.execute("""
    SELECT b.title, v.genre, v.voice_id, v.pitch, v.rate, COUNT(*) AS n,
           GROUP_CONCAT(v.character_name, ', ')
      FROM voices v JOIN books b ON b.id = v.book_id
     WHERE v.line_count < ?
     GROUP BY b.id, v.genre, v.voice_id, v.pitch, v.rate
    HAVING n > 1
     ORDER BY n DESC
""", (SEUIL,))
collisions = cur.fetchall()
print('   %d groupe(s) en collision (toutes lignes confondues)' % len(collisions))
for titre, genre, vid, pitch, rate, n, noms in collisions[:10]:
    print('      %-28s %s %-14s %5s %5s : %d -> %s'
          % ((titre or '?')[:28], genre, vid, pitch, rate, n, noms[:55]))

print()
print('== Les deux voix generiques existent-elles ? ==')
for vid in ('piper:upmc:0', 'piper:upmc:1', 'piper:siwis:0', 'piper:tom:0'):
    cur.execute('SELECT COUNT(*) FROM voices WHERE voice_id = ?', (vid,))
    print('   %-16s portee par %s personnage(s)' % (vid, cur.fetchone()[0]))

con.close()
