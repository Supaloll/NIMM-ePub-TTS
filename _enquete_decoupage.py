# -*- coding: utf-8 -*-
"""ENQUETE (LECTURE SEULE) : comment le decoupage traite-t-il les dialogues ?

Demande de Laurent (21/09/2026) : dans « 22/11/63 », les dialogues sont marques
par - ou « , et une phrase qui MELANGE narration et dialogue (par exemple
« Avant que j'aie pu repondre, Richie est intervenu : «Non, c'est pas ca. » »)
devrait etre coupee en deux morceaux : la NARRATION d'un cote, le DIALOGUE de
l'autre, pour que chaque voix lise ce qui la concerne.

Ce script ne modifie RIEN. Il montre :
    1. ce que la regle de decoupage actuelle fait de l'exemple de Laurent ;
    2. combien de morceaux MELANGENT narration et dialogue dans un vrai livre ;
    3. ce que la base a enregistre comme locuteur pour ces morceaux ;
    4. les tokens reellement consommes par chapitre (journal des appels IA).

Usage : python _enquete_decoupage.py [book_id]   (defaut : 28 = 22/11/63)
"""
import csv
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import decoupage

BASE = RACINE / 'data' / 'nimm_epub.db'
LIVRE = int(sys.argv[1]) if len(sys.argv) > 1 else 28

EXEMPLE = ("Avant que j'aie pu répondre, Richie est intervenu : «Non, c'est pas "
           "ça. C'est… Je sais pas. Vous cherchez….»")

print('=' * 74)
print(' 1) L EXEMPLE DE LAURENT, decoupe par la regle ACTUELLE')
print('=' * 74)
print('   Texte : ' + EXEMPLE)
print('')
for i, phrase in enumerate(decoupage.phrases(EXEMPLE), 1):
    dans_citation = ('«' in phrase) or phrase.strip().startswith('»')
    genre = 'DIALOGUE ?' if dans_citation else 'NARRATION ?'
    print('   %d. [%s] %s' % (i, genre, phrase))
print('')


def morceaux(texte):
    return decoupage.phrases(texte)


def melange(phrase):
    """Vrai si le morceau contient du texte AVANT une ouverture de citation :
    c'est le cas ou narration et dialogue se retrouvent dans le MEME morceau."""
    debut = phrase.find('«')
    if debut <= 0:
        return False
    return bool(phrase[:debut].strip(' :;,.-—'))


print('=' * 74)
print(' 2) CE QUE DEVIENT UN VRAI LIVRE (book_id=%d)' % LIVRE)
print('=' * 74)
con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
cur = con.cursor()
ligne = cur.execute('SELECT filename, title FROM books WHERE id = ?',
                    (LIVRE,)).fetchone()
if not ligne:
    print('   livre %d introuvable' % LIVRE)
    sys.exit(1)
fichier, titre = ligne
print('   %s  (fichier : %s)' % (titre, fichier))

chemin = RACINE / 'data' / 'library' / fichier
if not chemin.exists():
    print('   fichier EPUB introuvable : %s' % chemin)
    sys.exit(1)

from core import epub_parser

chapitres = epub_parser.get_chapters(str(chemin))
print('   %d chapitres' % len(chapitres))

# Locuteurs enregistres : {(chapitre, index du morceau): locuteur}
locuteurs = {}
for ch, idx, speaker in cur.execute(
        'SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution '
        'WHERE book_id = ?', (LIVRE,)):
    locuteurs[(ch, idx)] = speaker

total_morceaux = 0
melanges = []          # (chapitre, index, morceau, locuteur enregistre)
for ch, chap in enumerate(chapitres):
    morceaux = decoupage.phrases(chap.get('text') or '')
    total_morceaux += len(morceaux)
    for idx, phrase in enumerate(morceaux):
        if melange(phrase):
            melanges.append((ch, idx, phrase, locuteurs.get((ch, idx))))

print('   %d morceaux de phrase au total' % total_morceaux)
print('   %d morceaux MELANGENT narration et dialogue (texte avant «)'
      % len(melanges))
print('')
print('   Exemples reels, avec le locuteur ENREGISTRE en base :')
for ch, idx, phrase, speaker in melanges[:8]:
    print('      ch.%d #%d  locuteur = %s' % (ch, idx, speaker))
    print('         %s' % phrase[:110])

# Combien de morceaux la regle AMELIOREE creerait-elle ? On simule une coupe
# AVANT chaque « ouverture » de citation, et on compare les deux nombres.
def morceaux_avec_coupe_citation(texte):
    sortie = []
    for morceau in decoupage.phrases(texte):
        debut = morceau.find('«')
        if debut > 0 and morceau[:debut].strip(' :;,.-—'):
            sortie.append(morceau[:debut].strip())
            sortie.append(morceau[debut:].strip())
        else:
            sortie.append(morceau)
    return sortie


apres = sum(len(morceaux_avec_coupe_citation(c.get('text') or ''))
            for c in chapitres)
print('')
print('   Simulation d une regle qui coupe AVANT chaque « :')
print('      aujourd hui : %d morceaux -> apres : %d morceaux (%+d)'
      % (total_morceaux, apres, apres - total_morceaux))
print('      (les index de speaker_attribution devraient donc etre migres,')
print('       comme lors du changement de regle du 18/09/2026)')

con.close()

print('')
print('=' * 74)
print(' 4) TRI DES MORCEAUX MELANGES : vrai dialogue, ou citation racontee ?')
print('=' * 74)
# Deux familles tres differentes se cachent derriere le meme « texte avant « » :
#   A. le BEAT de narration qui introduit une replique -- « Richie est
#      intervenu : «Non, c'est pas ça. » -- ou la coupe est SOUHAITABLE : le
#      beat revient au narrateur, la replique au personnage ;
#   B. la CITATION a l'interieur du recit -- « J'ai jamais eu « la larme
#      facile », comme on dit. » -- ou couper CASSERAIT la phrase (deux moities
#      lues separement, avec deux intonations finales).
# Le discriminant retenu : le texte avant le « est un beat court qui finit par
# deux-points, ou qui contient un VERBE DE PAROLE (la liste du projet existe
# deja : voice_casting._RE_VERBE_PAROLE, et incises.VERBES).
import re as _re
from modules import voice_casting as _vc

RE_FIN_DEUX_POINTS = _re.compile(r':\s*$')


def classe_de(phrase):
    """'A' (beat + replique), 'B' (citation racontee), ou None (pas melange)."""
    debut = phrase.find('«')
    if debut <= 0:
        return None
    avant = phrase[:debut].strip()
    if not avant.strip(' :;,.-—'):
        return None
    citation_ouverte = phrase.count('«') != phrase.count('»')
    beat = bool(RE_FIN_DEUX_POINTS.search(avant)) \
        or bool(_vc._RE_VERBE_PAROLE.search(avant))
    if citation_ouverte and beat:
        return 'A'
    return 'B'


familles = {'A': [], 'B': []}
for ch, idx, phrase, speaker in melanges:
    familles[classe_de(phrase)].append((ch, idx, phrase, speaker))

for cle, nom in (('A', 'A. VRAI DIALOGUE (beat + replique) -> couper'),
                 ('B', 'B. CITATION DANS LA NARRATION -> laisser tel quel')):
    lot = familles[cle]
    attribues = [x for x in lot if x[3] not in (None, 'narration')]
    print('')
    print('   %s : %d morceau(x)' % (nom, len(lot)))
    print('      dont %d attribues a un PERSONNAGE aujourd hui'
          % len(attribues))
    for ch, idx, phrase, speaker in lot[:6]:
        print('      ch.%d #%d locuteur=%s | %s' % (ch, idx, speaker, phrase[:88]))

print('')
print('=' * 74)
print(' 5) PRIX REEL D UN RE-CAST DU LIVRE (estimation du projet, sans appel)')
print('=' * 74)
try:
    est = _vc.estimate_cast_cost([c.get('text') or '' for c in chapitres],
                                 'gemini')
    print('   chapitres : %s | morceaux de phrase : %s | appels IA : %s'
          % (est['chapters'], est['sentences'], est['calls']))
    print('   tokens : entree %s / sortie %s'
          % (est['tokens_in'], est['tokens_out']))
    print('   cout estime : %s (soit %.2f $ au plus)'
          % (est['cost_display'], est['cost_usd_max']))
except Exception as e:      # noqa: BLE001  (diagnostic : on montre l'erreur)
    print('   estimation impossible : %s' % e)

print('')
print('=' * 74)
print(' 6) QUELLE REGLE CHOISIR ? (precision mesuree sur le livre)')
print('=' * 74)
# Trois variantes du discriminant, du plus large au plus strict :
#   V1 : texte avant le « finit par ':' OU contient un verbe de parole ;
#   V2 : ':' ET verbe de parole (les deux) ;
#   V3 : V2, avec une liste de verbes ELARGIE (intervint, enchaîna...).
VERBES_EN_PLUS = _re.compile(
    r"\b(interv|interven|enchain|enchaîn|renchér|rench|poursuiv|rispost|"
    r"gliss|souffl|lâch|lança|lanca|rétorqu|retorqu|object|approuv|"
    r"répondit|repondit|précisa|precisa|expliqu|précis|precis)", _re.IGNORECASE)


def variante(phrase, numero):
    debut = phrase.find('«')
    if debut <= 0:
        return False
    avant = phrase[:debut].strip()
    if not avant.strip(' :;,.-—'):
        return False
    if phrase.count('«') == phrase.count('»'):
        return False                     # citation fermee dans le morceau
    colon = bool(RE_FIN_DEUX_POINTS.search(avant))
    verbe = bool(_vc._RE_VERBE_PAROLE.search(avant))
    verbe_large = verbe or bool(VERBES_EN_PLUS.search(avant))
    if numero == 1:
        return colon or verbe
    if numero == 2:
        return colon and verbe
    return colon and verbe_large


for numero, etiquette in ((1, 'V1 : deux-points OU verbe de parole'),
                          (2, 'V2 : deux-points ET verbe de parole'),
                          (3, 'V3 : deux-points ET verbe (liste elargie)')):
    lot = [x for x in melanges if variante(x[2], numero)]
    attribues = [x for x in lot if x[3] not in (None, 'narration')]
    print('')
    print('   %-42s %3d morceaux, dont %3d attribues a un PERSONNAGE'
          % (etiquette, len(lot), len(attribues)))
    for ch, idx, phrase, speaker in lot[:4]:
        print('      ch.%d #%d locuteur=%-14s | %s'
              % (ch, idx, str(speaker)[:14], phrase[:78]))

print('=' * 74)
lignes = list(csv.reader(open(str(RACINE / 'data' / 'journal_tokens.csv'),
                             encoding='utf-8'), delimiter=';'))
gem = [l for l in lignes[1:] if len(l) >= 5 and 'gemini' in l[1]]
entree = sum(int(l[2]) for l in gem)
sortie = sum(int(l[3]) for l in gem)
cout = entree / 1e6 * 0.42 + sortie / 1e6 * 3.50      # tarifs calibres facture
print('   %d appels Gemini enregistres dans le journal' % len(gem))
print('   entree : %d tokens / sortie : %d tokens' % (entree, sortie))
print('   cout cumule de CES appels : %.4f $ (environ %.2f EUR)' % (cout, cout * 0.92))
print('   soit environ %.4f EUR par appel (un appel = un lot de phrases d un '
      'chapitre)' % (cout * 0.92 / len(gem)))

