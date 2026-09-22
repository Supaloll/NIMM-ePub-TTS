# -*- coding: utf-8 -*-
"""PROTOTYPE (mesure seule) -- incises d'AUXILIAIRE + PARTICIPE.

Le module incises.py ne connait que les formes simples : « , dit-il, »,
« , répondit Morrel, ». Il ne voit PAS les formes tres frequentes du recit au
passe compose, qui disent pourtant QUI parle :

    "m'a-t-elle repondu."        -> m' + a-t-elle + repondu
    "m'a-t-il dit."              -> m' + a-t-il + dit
    "a-t-il confirme."           -> a-t-il + confirme
    "me dit Annette Founijello." -> me + dit + NOM

Mesure du 22/09/2026 : 40 phrases de ce type dans 22/11/63, dont AUCUNE n'est
retiree aujourd'hui -- elles sont donc lues avec la voix du personnage, alors
que c'est le narrateur qui parle.

Ce script NE MODIFIE RIEN : il applique la regle candidate, compte, et montre
le AVANT / APRES. C'est la mesure qui precede la decision.

ATTENTION : la mesure se lance A L'IMPORT (le script n'est pas protege par
`__main__`), donc `_preuve_candidat.py`, qui importe ce fichier pour reutiliser
ses motifs, affiche d'abord le rapport complet du livre 28. C'est voulu : ces
deux scripts sont jetables.

Usage : python _moisson_incise_proto.py [book_id ...]
"""

import os
import re
import sqlite3
import sys
from pathlib import Path

try:
    RACINE = Path(__file__).resolve().parent
    sys.path.insert(0, str(RACINE))
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:                                    # pragma: no cover
    RACINE = Path('.')

from core.epub_parser import get_chapters                       # noqa: E402
from modules import incises as inc                              # noqa: E402
from modules.decoupage import (phrases as _phrases,             # noqa: E402
                               REGLE_DIALOGUE)

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
LIVRES = []
if __name__ == '__main__':
    LIVRES = [int(a) for a in sys.argv[1:] if a.isdigit()] or [28]
# Un importateur -- le banc d'ecoute des incises (`test_voix/_banc_incises.py`)
# reutilise les motifs d'ici -- ne mesure RIEN : il lit le fichier pour ses
# fonctions. (Erreur corrigee le 22/09/2026 : l'import lisait les arguments de
# ligne de commande de l'importateur, et `--livre` etait pris pour un numero de
# livre.)
if os.environ.get('NIMM_SANS_MESURE'):
    LIVRES = []

# --- La regle candidate ------------------------------------------------------
# Participes passes des verbes de PAROLE (ceux de incises.VERBES, au participe).
# ⚠ Ils doivent etre ecrits AVEC leurs accents : `_variantes` derive la graphie
# sans accent, jamais l'inverse (erreur corrigee le 22/09/2026 : « repondu »
# sans accent laissait passer tous les « m'a-t-elle répondu »).
PARTICIPES = (
    'dit', 'dis', 'répondu', 'répliqué', 'écrié', 'crié', 'demandé',
    'repris', 'ajouté', 'murmuré', 'poursuivi', 'continué', 'hasardé',
    'observé', 'remarqué', 'exclamé', 'prononcé', 'balbutié', 'soupiré',
    'grommelé', 'grondé', 'tonné', 'vociféré', 'interrompu', 'répété', 'avoué',
    'déclaré', 'conclu', 'achevé', 'commencé', 'terminé', 'insisté', 'objecté',
    'riposté', 'réparti', 'interrogé', 'questionné', 'exigé', 'ordonné',
    'supplié', 'prié', 'songé', 'gémi', 'sangloté', 'plaidé', 'protesté',
    'appelé', 'conseillé', 'recommandé', 'expliqué', 'raconté', 'enchaîné',
    'grincé', 'lancé', 'soufflé', 'marmonné', 'hurlé', 'précisé', 'rappelé',
    'confirmé', 'annoncé', 'rétorqué', 'tranché', 'souri', 'ri', 'pleuré',
    'sifflé', 'chantonné', 'plaisanté',
)


def _variantes(mot):
    """Les deux graphies d'un mot accentue (comme incises.py : repondit/repondit)."""
    paires = (('é', 'e'), ('è', 'e'), ('ê', 'e'), ('î', 'i'), ('û', 'u'),
              ('ô', 'o'), ('à', 'a'), ('ç', 'c'))
    formes = {mot}
    for accent, simple in paires:
        for f in list(formes):
            if accent in f:
                formes.add(f.replace(accent, simple))
    return formes


MOTS_PARTICIPES = sorted({v for m in PARTICIPES for v in _variantes(m)})
PART = r'(?:%s)' % '|'.join(MOTS_PARTICIPES)

# "m'a-t-elle repondu", "a-t-il confirme", "lui ai-je recommande" :
# AUXILIAIRE + pronom + PARTICIPE. Le pronom inclut "je" : la forme renversee
# « ai-je » est tres frequente dans un recit a la premiere personne.
AUXILIAIRE = r'(?:ai|as|a|avons|avez|ont)'
PRONOM = r'(?:il|elle|on|je|nous|vous|ils|elles)'
DEVANT = r"(?:m[\u2019']|t[\u2019']|l[\u2019']|me\s|te\s|lui\s|nous\s|vous\s)?"
MOTIF_AUX = re.compile(
    r"[,;\u2013\u2014]\s*%s%s[\u2013-]?t?[\u2013-]?%s\s+%s\b"
    % (DEVANT, AUXILIAIRE, PRONOM, PART))
# "me dit Annette Founijello", "lui dit Fleur-de-Lys" : PRONOM + verbe + NOM.
# Le pronom est EXIGE (la forme sans pronom est deja traitee par MOTIF_NOM du
# module). Le nom accepte un second mot capitalise (« Annette Founijello »,
# « Bill Turcotte ») : sans cela, l'incise n'etait jamais consideree comme
# fermee, donc jamais retiree.
NOM = (r"[A-Z\u00c0-\u00d6\u00d8-\u00dd][\w\u00c0-\u00ff'-]*"
       r"(?:\s+[A-Z\u00c0-\u00d6\u00d8-\u00dd][\w\u00c0-\u00ff'-]*)?")
VERBE_AVEC_PRON = (r'(?:me\s|te\s|lui\s|nous\s|vous\s|m[\u2019\']|t[\u2019\'])'
                   r'(?:%s)\s+' % '|'.join(inc.VERBES))
MOTIF_PRON_NOM = re.compile(
    r"[,;\u2013\u2014]\s*%s%s%s" % (VERBE_AVEC_PRON, inc.CIVILITE, NOM))


def spans_candidats(phrase):
    """[(debut, fin)] des incises de la regle candidate, validees et etendues."""
    trouves = []
    for motif in (MOTIF_AUX, MOTIF_PRON_NOM):
        for m in motif.finditer(phrase):
            debut, fin = m.start(), m.end()
            if not inc._ferme_ou_terminal(phrase, debut, fin):
                fin = inc._etendre(phrase, fin)
            if not inc._ferme_ou_terminal(phrase, debut, fin):
                continue
            fin = max(fin, inc._etendre_relative(phrase, fin))
            fin = max(fin, inc._etendre_participle(phrase, fin))
            trouves.append((debut, fin))
    return sorted(set(trouves))


def retirer(phrase, spans):
    """La phrase sans les incises trouvees (memes garde-fous que le module)."""
    texte = phrase
    for debut, fin in sorted(spans, reverse=True):
        texte = texte[:debut] + ' ' + texte[fin:]
    texte = re.sub(r'\s{2,}', ' ', texte)
    texte = re.sub(r'\s+([.,;:\u2026])', r'\1', texte)
    texte = re.sub(r',\s*,+', ',', texte)
    texte = texte.strip().lstrip(' \u00a0,;:.\u2026')
    if not re.search(r'[A-Za-z\u00c0-\u024f]', texte):
        return phrase
    return texte


conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
conn.row_factory = sqlite3.Row

for BID in LIVRES:
    livre = conn.execute('SELECT title, filename FROM books WHERE id = ?',
                         (BID,)).fetchone()
    chemin = BIBLIOTHEQUE / livre['filename']
    if not chemin.is_file():
        print('livre %d : fichier absent, ignore' % BID)
        continue
    print('=' * 100)
    print('LIVRE %d : %s' % (BID, livre['title']))
    print('=' * 100)
    total = 0
    candidates = 0
    deja = 0
    exemples = []
    terminales = 0
    medianes = 0
    ex_term = []
    ex_med = []
    for chap in get_chapters(str(chemin)):
        for texte in _phrases(chap.get('text') or '', REGLE_DIALOGUE):
            total += 1
            if inc.retirer_incises(texte) != texte:
                deja += 1
                continue
            spans = spans_candidats(texte)
            if not spans:
                continue
            candidates += 1
            # TERMINALE : plus rien apres l'incise (hors ponctuation finale).
            reste = texte[max(f for _d, f in spans):].strip()
            if not re.search(r'[A-Za-z\u00c0-\u024f]', reste):
                terminales += 1
                if len(ex_term) < 6:
                    ex_term.append((chap['index'], texte, retirer(texte, spans)))
            else:
                medianes += 1
                if len(ex_med) < 6:
                    ex_med.append((chap['index'], texte, retirer(texte, spans)))
            if len(exemples) < 12:
                exemples.append((chap['index'], texte, retirer(texte, spans)))
    print('  phrases : %d | incises deja retirees aujourd hui : %d'
          % (total, deja))
    print('  phrases que la regle candidate retirerait EN PLUS : %d (%.2f %%)'
          % (candidates, 100.0 * candidates / max(total, 1)))
    print('    dont incise TERMINALE (fin de phrase) : %d  <-- la variante prudente'
          % terminales)
    print('    dont incise MEDIANE (coupee dans la phrase) : %d  <-- la plus delicate'
          % medianes)
    print('')
    print('  --- TERMINALES (fin de phrase) ---')
    for c, avant, apres in ex_term:
        print('   chap. %-3d AVANT : %s' % (c, avant[:132]))
        print('           APRES : %s' % apres[:132])
    print('')
    print('  --- MEDIANES (a l interieur de la phrase) ---')
    for c, avant, apres in ex_med:
        print('   chap. %-3d AVANT : %s' % (c, avant[:132]))
        print('           APRES : %s' % apres[:132])

conn.close()
if LIVRES:
    print('--- fin du prototype (RIEN n a ete modifie) ---')
