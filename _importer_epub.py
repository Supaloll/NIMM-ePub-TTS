# -*- coding: utf-8 -*-
"""IMPORTE un EPUB dans la bibliotheque du lecteur (par l'API) -- 21/09/2026.

Sert aux livres d'essai fabriques pour les tests de decoupage : plutot que de
demander a Laurent de passer par le bouton « Ajouter », on depose le fichier
directement. L'import est celui de l'application (meme route, memes controles).

Usage : python _importer_epub.py "_essais\\mon-essai.epub" [user_id]
"""
import sys
from pathlib import Path

import requests

fichier = Path(sys.argv[1])
user = int(sys.argv[2]) if len(sys.argv) > 2 else 1
if not fichier.exists():
    print('fichier introuvable : %s' % fichier)
    sys.exit(1)

url = 'http://127.0.0.1:8081/api/books/upload?user_id=%d' % user
with open(fichier, 'rb') as f:
    reponse = requests.post(
        url, files={'file': (fichier.name, f, 'application/epub+zip')},
        timeout=600)

print('HTTP %s' % reponse.status_code)
print(reponse.text[:500])
