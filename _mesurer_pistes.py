# -*- coding: utf-8 -*-
"""MESURE DES TROIS PISTES d'amélioration (21/09/2026) -- lecture seule.

Relevées à l'oreille par Laurent, sur le chapitre d'essai de « 22/11/63 » :
  A. **Beat sans verbe de parole** : « Puis : « D'accord… » » — la coupe
     « dialogue » exige un verbe de parole, donc elle ne voit pas les petits
     liants narratifs (« Puis : », « Alors : », « Et : »), et le beat reste collé
     à la réplique (donc lu par le personnage).
  B. **Incise isolée** : « m'a-t-elle demandé. » occupe tout un morceau, sans
     virgule : le module d'incises ne la reconnaît pas (il attend « , dit-il, »),
     et c'est le personnage qui la lit.
  C. **Acronymes** : « URSS » (et compagnie) — à prononcer comme FBI, CIA.

Ce script COMPTE et MONTRE, il ne corrige rien. Lire les morceaux montrés :
c'est la règle de la maison.

Usage : python _mesurer_pistes.py 37 [nb_exemples]
"""
import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage, incises

LIVRE = int(sys.argv[1]) if len(sys.argv) > 1 else 37
MAXI = int(sys.argv[2]) if len(sys.argv) > 2 else 8
BASE = RACINE / 'data' / 'nimm_epub.db'

# --- Motifs de travail (des CANDIDATS, a valider par la lecture) -------------
RE_FIN_COLON = re.compile(r':\s*$')
# Une incise isolée : courte, finit par un point, et porte une forme verbale
# pronominale (« m'a-t-elle demandé. », « dit-il. », « demanda-t-elle. »).
RE_TRAIT_INCISE = re.compile(r'-(?:t-)?(?:il|elle|on|ils|elles|je|tu)\b')
MOTIF_INCISE_VERBE = re.compile(
    r"\b(?:m'|t'|s'|l'|n')?a?-?(?:%s)" % '|'.join(
        re.escape(v) for v in
        [v for v in getattr(incises, 'VERBES', ())][:60]), re.IGNORECASE)
RE_ACRONYME = re.compile(r'\b[A-ZÉÈÀÂÎÔÛ]{2,6}\b')

con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
fichier, titre, drapeau = con.execute(
    'SELECT filename, title, COALESCE(decoupe_dialogue, 0) FROM books '
    'WHERE id = ?', (LIVRE,)).fetchone()
con.close()
regle = decoupage.REGLE_DIALOGUE if drapeau else decoupage.REGLE_ACTUELLE

piste_a, piste_a2, piste_b, piste_d, acronymes = [], [], [], [], {}
total = 0
for ch, chapitre in enumerate(epub_parser.get_chapters(
        str(RACINE / 'data' / 'library' / fichier))):
    texte = chapitre.get('text') or ''
    morceaux = decoupage.phrases(texte, regle)
    total += len(morceaux)
    for idx, morceau in enumerate(morceaux):
        suivant = morceaux[idx + 1] if idx + 1 < len(morceaux) else ''
        # A. beat sans verbe : un morceau qui COLLE « <texte> : « ... » » alors
        #    que le texte avant les deux-points n'a aucun verbe de parole
        #    (« Puis : « D'accord… » »). Deux formes possibles : le morceau
        #    contient la citation (cas de Laurent), ou il finit par ':' et la
        #    citation suit dans le morceau d'apres.
        ouverture = morceau.find('«')
        avant = morceau[:ouverture] if ouverture > 0 else (
            morceau if RE_FIN_COLON.search(morceau)
            and suivant.lstrip().startswith('«') else '')
        if avant and RE_FIN_COLON.search(avant) \
                and not decoupage.introduit_une_replique(avant):
            piste_a.append((ch, idx, avant.rstrip(), suivant or
                            morceau[ouverture:]))
        # A2. beats DEJA coupes : on montre les deux familles pour les LIRE.
        #     A2a : le beat finit par ':' et n'a aucun verbe de parole.
        #     A2b : le beat n'a PAS de deux-points mais contient un verbe.
        # D.  LE CHIFFRE QUI COMPTE : les beats qui n'existent QUE grace a la
        #     nouvelle branche (l'ancienne regle ne les aurait pas coupes).
        if suivant.lstrip().startswith('«') and '«' not in morceau:
            avant_b = morceau.rstrip()
            ancien = (avant_b.replace('\u2019', "'").endswith(':')
                      and decoupage.MOTIF_VERBE_PAROLE.search(
                          avant_b.replace('\u2019', "'")))
            if not ancien:
                piste_d.append((ch, idx, avant_b, suivant))
            if RE_FIN_COLON.search(morceau) \
                    and not decoupage.introduit_une_replique(morceau):
                piste_a2.append((ch, idx, 'deux-points sans verbe', morceau))
            elif not RE_FIN_COLON.search(morceau) \
                    and decoupage.MOTIF_VERBE_PAROLE.search(morceau):
                piste_a2.append((ch, idx, 'verbe sans deux-points', morceau))

        nu = morceau.strip()
        if (len(nu) <= 45 and nu.endswith('.') and '«' not in nu
                and RE_TRAIT_INCISE.search(nu)
                and MOTIF_INCISE_VERBE.search(nu)):
            piste_b.append((ch, idx, nu))
    for mot in RE_ACRONYME.findall(texte):
        acronymes[mot] = acronymes.get(mot, 0) + 1

print('=' * 78)
print(' %s (livre %s, mode %s) -- %d morceaux'
      % (titre, LIVRE, 'DIALOGUE' if drapeau else 'origine', total))
print('=' * 78)
print('')
print(' A. BEAT SANS VERBE DE PAROLE : %d cas' % len(piste_a))
for ch, idx, avant, suivant in piste_a[:MAXI]:
    print('    ch.%d #%-4d %-40s -> %s' % (ch, idx, avant[:40], suivant[:40]))
print('')
print(' A2. BEATS COUPES PAR LA NOUVELLE BRANCHE (a LIRE) : %d cas' % len(piste_a2))
for ch, idx, famille, morceau in piste_a2[:MAXI]:
    print('    ch.%d #%-4d %-22s %s' % (ch, idx, famille, morceau[:86]))
print('')
print(' B. INCISE ISOLEE (a retirer du texte parle) : %d cas' % len(piste_b))
for ch, idx, nu in piste_b[:MAXI]:
    print('    ch.%d #%-4d %s' % (ch, idx, nu))
print('')
print('')
print(' D. BEATS QUI N EXISTENT QUE GRACE A LA NOUVELLE BRANCHE : %d' % len(piste_d))
for ch, idx, beat, replique in piste_d[:MAXI]:
    print('    ch.%d #%-4d %-58s -> %s' % (ch, idx, beat[:58], replique[:34]))
for mot, n in sorted(acronymes.items(), key=lambda x: -x[1])[:14]:
    print('    %-8s %d fois' % (mot, n))
