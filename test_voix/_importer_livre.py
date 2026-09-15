# -*- coding: utf-8 -*-
"""
Import d'un livre dans NIMM ePub par l'API (meme route que le glisser-deposer
de l'interface). Utile pour automatiser un essai.

Usage :
    python test_voix/_importer_livre.py "D:/chemin/vers/livre.epub"
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

import httpx

API = 'http://127.0.0.1:8081/api/books/upload?user_id=1'

if len(sys.argv) < 2:
    print('Usage : python test_voix/_importer_livre.py "chemin\\du\\livre.epub"')
    sys.exit(1)

chemin = Path(sys.argv[1])
if not chemin.exists():
    print('Fichier introuvable : {}'.format(chemin))
    sys.exit(1)

print('Import de : {}'.format(chemin.name))
try:
    with open(str(chemin), 'rb') as f:
        r = httpx.post(API, files={'file': (chemin.name, f, 'application/epub+zip')},
                       timeout=180.0)
except Exception as e:
    print('Echec de l\'envoi : {}'.format(e))
    sys.exit(1)

print('Reponse du serveur ({}): {}'.format(r.status_code, r.text[:400]))
