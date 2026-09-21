# -*- coding: utf-8 -*-
"""Fabrique un EPUB d'UN SEUL CHAPITRE (copie d'essai) -- 21/09/2026.

Demande de Laurent : plutot qu'essayer sur un livre entier penible a lire,
prendre UN chapitre d'un livre qu'il connait (22/11/63), riche en dialogues, et
y mener tous les essais de decoupage et d'attribution.

L'EPUB produit est un LIVRE NEUF (identifiant propre, titre explicite) : le livre
d'origine n'est jamais touche.

Usage :
    python _creer_epub_chapitre.py 28 27 essai-221163-chapitre-Sadie
"""
import sqlite3
import sys
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage

LIVRE = int(sys.argv[1]) if len(sys.argv) > 1 else 28
CHAPITRE = int(sys.argv[2]) if len(sys.argv) > 2 else 27
NOM = sys.argv[3] if len(sys.argv) > 3 else 'essai-chapitre'
TITRE = "22/11/63 - chapitre d'essai (Sadie) - decoupage"

BASE = RACINE / 'data' / 'nimm_epub.db'
con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
fichier, titre_livre = con.execute('SELECT filename, title FROM books WHERE id = ?',
                                   (LIVRE,)).fetchone()
con.close()

chapitres = epub_parser.get_chapters(str(RACINE / 'data' / 'library' / fichier))
if CHAPITRE >= len(chapitres):
    print('chapitre %d introuvable (le livre en a %d)' % (CHAPITRE, len(chapitres)))
    sys.exit(1)
texte = chapitres[CHAPITRE]['text']


def echapper(t):
    '''Echappe le texte pour du XHTML.'''
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


paragraphes = [p.strip() for p in texte.split('\n\n') if p.strip()]
corps = '\n'.join('  <p>%s</p>' % echapper(p) for p in paragraphes)

xhtml = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
<head><meta charset="utf-8"/><title>%(t)s</title></head>
<body>
<h1>%(t)s</h1>
%(corps)s
</body></html>
""" % {'t': echapper(TITRE), 'corps': corps}

nav = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="fr">
<head><meta charset="utf-8"/><title>Sommaire</title></head>
<body><nav epub:type="toc"><ol><li><a href="chapitre.xhtml">%(t)s</a></li>
</ol></nav></body></html>
""" % {'t': echapper(TITRE)}

opf = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0"
         unique-identifier="bookid" xml:lang="fr">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:nimm-%(n)s</dc:identifier>
    <dc:title>%(t)s</dc:title>
    <dc:language>fr</dc:language>
    <dc:creator>Essai NIMM ePub (copie d'un chapitre de %(livre)s)</dc:creator>
  </metadata>
  <manifest>
    <item id="chap" href="chapitre.xhtml" media-type="application/xhtml+xml"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml"
          properties="nav"/>
  </manifest>
  <spine><itemref idref="chap"/></spine>
</package>
""" % {'n': NOM, 't': echapper(TITRE), 'livre': echapper(titre_livre or '')}

container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf"
              media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

sortie = RACINE / '_essais' / (NOM + '.epub')
sortie.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(sortie, 'w', zipfile.ZIP_DEFLATED) as z:
    # Le mimetype doit etre le PREMIER fichier et NON compresse (regle EPUB).
    z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip',
               compress_type=zipfile.ZIP_STORED)
    z.writestr('META-INF/container.xml', container)
    z.writestr('OEBPS/content.opf', opf)
    z.writestr('OEBPS/nav.xhtml', nav)
    z.writestr('OEBPS/chapitre.xhtml', xhtml)

# Relecture : on verifie que NOTRE lecteur y voit bien UN chapitre.
relus = epub_parser.get_chapters(str(sortie))
morceaux = decoupage.phrases(texte)
beats = [m for m in morceaux if decoupage._couper_avant_replique((0, len(m), m))[1:]]
print('=' * 78)
print(' EPUB D ESSAI CREE : %s' % sortie)
print('=' * 78)
print('   chapitre source : %s, chapitre n°%d (%s)'
      % (titre_livre, CHAPITRE, chapitres[CHAPITRE].get('title')))
print('   %d caracteres, %d paragraphes' % (len(texte), len(paragraphes)))
print('   relu par notre lecteur : %d chapitre(s)' % len(relus))
print('   morceaux de phrase : %d  |  signes « : %d'
      % (len(morceaux), texte.count('«')))
print('   beats (narration collee a une replique) : %d' % len(beats))
print('   morceaux en mode dialogue : %d'
      % len(decoupage.phrases(texte, decoupage.REGLE_DIALOGUE)))
