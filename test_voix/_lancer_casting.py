# -*- coding: utf-8 -*-
"""
Lance le casting voix multiples d'un livre par l'API (meme route que le bouton
de l'interface). Utile pour automatiser un essai.

Usage :
    python test_voix/_lancer_casting.py 30 local
    python test_voix/_lancer_casting.py 30 gemini

Attention : la requete attend la fin de l'analyse du PREMIER chapitre (c'est
le fonctionnement normal de l'application, pour la barre de progression).
Comptez une minute environ avec le moteur local, davantage avec Gemini.
"""
import sys

sys.stdout.reconfigure(encoding='utf-8')

import httpx

if len(sys.argv) < 2:
    print('Usage : python test_voix/_lancer_casting.py <book_id> [provider]')
    sys.exit(1)

book_id = sys.argv[1]
provider = sys.argv[2] if len(sys.argv) > 2 else 'local'
url = 'http://127.0.0.1:8081/api/books/{}/cast?user_id=1&provider={}'.format(book_id, provider)

print('Lancement du casting : livre {}, moteur {}.'.format(book_id, provider))
print('(la requete attend la fin du premier chapitre, c\'est normal)')
try:
    r = httpx.post(url, timeout=3600.0)
except Exception as e:
    print('Echec : {}'.format(e))
    sys.exit(1)

print('Reponse ({}): {}'.format(r.status_code, r.text[:400]))
