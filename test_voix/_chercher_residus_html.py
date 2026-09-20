# -*- coding: utf-8 -*-
"""CHERCHER LES RESIDUS HTML DANS LE TEXTE LU (20/09/2026).

A lancer avec le Python du LECTEUR :
    python test_voix/_chercher_residus_html.py
    python test_voix/_chercher_residus_html.py --livre 16
    python test_voix/_chercher_residus_html.py --livre 16 --html

Pourquoi : Laurent a trouve, au chapitre 98 d'un livre, un morceau de balise
incruste dans le texte lu et affiche :

    « M class="textsuperscript">lle Danglars »

Ce script refait exactement ce que fait le lecteur -- il passe par le VRAI
parseur (`core/epub_parser._html_to_text`) -- sur TOUS les livres de la base, et
signale tout ce qui ne devrait jamais y figurer : balises, attributs orphelins,
entites HTML non decodees.

LECTURE SEULE : rien n'est modifie.

--html : affiche en plus le HTML BRUT du document fautif, autour du residu (c'est
         ce qui montre d'ou vient le probleme, et ce qu'il faut corriger).
"""

import argparse
import re
import sqlite3
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
BASE = RACINE / "data" / "nimm_epub.db"
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser                                     # noqa: E402
import ebooklib                                                  # noqa: E402
from ebooklib import epub                                        # noqa: E402

# Ce qu'on cherche : tout ce qui ne doit jamais se trouver dans du texte lu.
# Les motifs sont volontairement larges : on veut VOIR ce qui traine.
MOTIFS = [
    ('attribut orphelin (morceau de balise)', re.compile(r'\w+ [a-zA-Z-]+="[^"]*">')),
    ('balise HTML', re.compile(r'</?[a-zA-Z][^>]*>')),
    ('entite HTML non decodee', re.compile(r'&[a-zA-Z]{2,10};')),
]


def chemin_de_livre(livre):
    nom = livre['filename']
    if not nom:
        return None
    for essai in (Path(nom), RACINE / 'data' / 'library' / nom):
        if essai.is_file():
            return essai
    return None


def documents_du_livre(chemin):
    """[(nom du document, HTML brut), ...], dans l'ordre du livre.

    On lit l'EPUB UNE SEULE FOIS : c'est ce qui rend le balayage de toute la
    bibliotheque supportable (une lecture par livre, pas par chapitre).
    """
    livre = epub.read_epub(str(chemin))
    docs = []
    for item in livre.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        if not epub_parser._is_content_document(item):
            continue
        docs.append((item.get_name(),
                     item.get_content().decode('utf-8', errors='ignore')))
    return docs


def main():
    parseur = argparse.ArgumentParser(
        description="Cherche les residus HTML dans le texte que le lecteur produit.")
    parseur.add_argument('--livre', type=int, default=0,
                         help='ne verifier qu un livre (son identifiant)')
    parseur.add_argument('--html', action='store_true',
                         help='montrer aussi le HTML brut autour du premier residu')
    parseur.add_argument('--max', type=int, default=6,
                         help='nombre de residus montres par livre (defaut 6)')
    args = parseur.parse_args()

    if not BASE.is_file():
        print('Base introuvable : %s' % BASE)
        return 1
    connexion = sqlite3.connect(BASE)
    connexion.row_factory = sqlite3.Row
    livres = list(connexion.execute(
        'SELECT id, title, filename FROM books ORDER BY id'))
    if args.livre:
        livres = [b for b in livres if b['id'] == args.livre]

    print('=' * 66)
    print('RESIDUS HTML DANS LE TEXTE LU')
    print('=' * 66)
    total_docs = 0
    livres_touches = 0
    for livre in livres:
        chemin = chemin_de_livre(livre)
        if not chemin:
            print('  livre %s : fichier introuvable' % livre['id'])
            continue
        try:
            docs = documents_du_livre(chemin)
        except Exception as e:                                   # noqa: BLE001
            print('  livre %s : lecture impossible (%s)' % (livre['id'], e))
            continue
        trouves = []
        for nom, html_brut in docs:
            total_docs += 1
            texte = epub_parser._html_to_text(html_brut)
            for libelle, motif in MOTIFS:
                for m in motif.finditer(texte):
                    debut = max(0, m.start() - 45)
                    fin = min(len(texte), m.end() + 45)
                    trouves.append((nom, libelle, m.group(0),
                                    texte[debut:fin].replace('\n', ' '), html_brut))
        if not trouves:
            print('  livre %s — %s : propre' % (livre['id'], livre['title']))
            continue
        livres_touches += 1
        print('')
        print('  LIVRE %s — %s' % (livre['id'], livre['title']))
        print('    %d document(s), %d residu(s) :' % (len(docs), len(trouves)))
        for nom, libelle, extrait, contexte, _html in trouves[:args.max]:
            print('      %s' % nom)
            print('        %s -> %r' % (libelle, extrait))
            print('        ...%s...' % contexte)
        if args.html:
            nom, libelle, extrait, _c, html_brut = trouves[0]
            # On cherche dans le HTML un morceau CARACTERISTIQUE du residu : le nom
            # de la classe (ou l'attribut). Le HTML brut ne contient evidemment pas
            # le residu lui-meme : c'est le PARSEUR qui l'a fabrique, et c'est donc
            # la balise d'origine qu'il faut voir.
            m_attribut = re.search(r'[a-zA-Z-]+="[^"]*"', extrait)
            cle = m_attribut.group(0) if m_attribut else extrait[:12]
            print('')
            print('    (recherche de %r dans le HTML brut)' % cle)
            for m in re.finditer(re.escape(cle), html_brut):
                print('')
                print('    HTML BRUT autour de %r :' % cle)
                print('      ...%s...' % html_brut[max(0, m.start() - 260):
                                                  m.end() + 110].replace('\n', ' '))
                break

    print('')
    print('documents analyses : %d | livres avec un residu : %d'
          % (total_docs, livres_touches))
    return 0


if __name__ == '__main__':
    sys.exit(main())
