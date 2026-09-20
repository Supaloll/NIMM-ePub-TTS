# -*- coding: utf-8 -*-
"""Verification de l'application INSTALLABLE (PWA) — 20/09/2026.

A lancer avec le Python du LECTEUR :
    python test_voix/test_pwa_manifeste.py

Pourquoi ce test existe : Laurent n'avait **pas** l'option « Installer
l'application » dans Chrome, alors qu'elle lui est proposee pour NIMM (le
chatbot). Cause trouvee : le manifeste declairait la **meme** image (512x512) en
`192x192`, `512x512` **et** `2048x2048`. Chrome verifie que la taille ANNONCEE
correspond a l'image : il rejetait donc **toutes** les icones -- et sans icone
valide de 192 px, l'installation n'est pas proposee.

Ce que le test verifie (les criteres reels d'installation de Chrome) :
  1. le manifeste est un JSON valide, avec `name`, `short_name`, `start_url`,
     `display` et les couleurs ;
  2. CHAQUE icone declaree EXISTE et sa TAILLE REELLE correspond a la taille
     annoncee (c'est le point qui manquait) ;
  3. il y a au moins une icone >= 192 px et une >= 512 px ;
  4. la page lie le manifeste et les favicons, et l'apple-touch-icon existe ;
  5. le service worker existe et repond aux requetes (`fetch`) : sans lui, Chrome
     n'installe pas non plus.

Regenerer les icones : `python test_voix/_generer_icones_pwa.py --ecrire`.
"""

import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
FRONTEND = RACINE / "frontend"
MANIFESTE = FRONTEND / "manifest.json"
INDEX = FRONTEND / "index.html"
SW = FRONTEND / "sw.js"

sys.stdout.reconfigure(encoding='utf-8')

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def main():
    from PIL import Image

    print('')
    print('1) le manifeste annonce ce qu il faut')
    verifier('le manifeste existe', MANIFESTE.is_file(), MANIFESTE)
    if not MANIFESTE.is_file():
        return 1
    manifeste = json.loads(MANIFESTE.read_text(encoding='utf-8'))
    for cle in ('name', 'short_name', 'start_url', 'display',
                'background_color', 'theme_color'):
        verifier('cle « %s » presente' % cle, bool(manifeste.get(cle)))
    verifier('mode « standalone » (une vraie fenetre, pas un onglet)',
             manifeste.get('display') == 'standalone', manifeste.get('display'))
    verifier('le depart est la racine de l application',
             manifeste.get('start_url') == '/', manifeste.get('start_url'))

    print('')
    print('2) chaque icone declaree existe, A LA TAILLE ANNONCEE')
    icones = manifeste.get('icons') or []
    verifier('des icones sont declarees', len(icones) > 0, len(icones))
    grandes = []
    for icone in icones:
        nom = Path(icone.get('src', '')).name
        chemin = FRONTEND / nom
        annoncee = icone.get('sizes', '')
        if not chemin.is_file():
            verifier('%s existe' % nom, False, chemin)
            continue
        reel = Image.open(chemin)
        reelle = '%dx%d' % (reel.width, reel.height)
        verifier('%-26s annonce %-10s et le fichier fait %s'
                 % (nom, annoncee, reelle), annoncee == reelle,
                 'Chrome rejette une icone dont la taille annoncee ne '
                 'correspond pas au fichier')
        if reel.width >= 192:
            grandes.append(nom)
    verifier('au moins une icone de 192 px (critere de Chrome)',
             len(grandes) >= 1, grandes)
    verifier('au moins une icone de 512 px (icone de demarrage Android)',
             any((Image.open(FRONTEND / Path(i['src']).name).width >= 512)
                 for i in icones
                 if (FRONTEND / Path(i['src']).name).is_file()),
             [i.get('src') for i in icones])
    verifier('une icone « maskable » existe (Android ne rogne pas le logo)',
             any('maskable' in (i.get('purpose') or '') for i in icones),
             [i.get('purpose') for i in icones])

    print('')
    print('3) la page lie le manifeste, les favicons et l icone Apple')
    page = INDEX.read_text(encoding='utf-8')
    verifier('le manifeste est lie',
             re.search(r'<link[^>]+rel="manifest"[^>]+href="[^"]*manifest\.json', page)
             is not None)
    verifier('l apple-touch-icon est lie',
             'apple-touch-icon' in page)
    verifier('les favicons 192 et 512 sont lies',
             'sizes="192x192"' in page and 'sizes="512x512"' in page)
    for nom in ('apple-touch-icon.png', 'icon-192.png', 'icon-512.png'):
        verifier('le fichier %s existe' % nom, (FRONTEND / nom).is_file())

    print('')
    print('4) le service worker (sans lui, Chrome n installe pas)')
    verifier('sw.js existe', SW.is_file(), SW)
    if SW.is_file():
        contenu = SW.read_text(encoding='utf-8')
        verifier('il repond aux requetes (fetch)', "addEventListener('fetch'" in contenu)
        verifier('il ne met PAS l API en cache (donnees toujours fraiches)',
                 "url.pathname.startsWith('/api/')" in contenu)

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : application installable (PWA)')
    print('=' * 66)
    sys.exit(main())
