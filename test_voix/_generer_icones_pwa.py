# -*- coding: utf-8 -*-
"""GENERER LES ICONES DE LA PWA (20/09/2026).

Pourquoi ce script existe : Chrome n'accepte d'installer une application que
s'il trouve des icones dont la TAILLE DECLAREE dans `manifest.json` correspond
a la TAILLE REELLE du fichier. NIMM ePub declarait la MEME image (512x512) en
`192x192`, `512x512` et `2048x2048` : Chrome rejetait donc toutes les icones, et
l'entree « Installer l'application » n'apparaissait pas (constat de Laurent,
20/09/2026 : « chez NIMM ca marche, chez NIMM ePub je n'ai pas l'option »).

Ce script REGENERE les fichiers manquants a partir du logo maitre
(`frontend/image_NIMM_ePub.png`, 1523x1523) et VERIFIE que chaque taille
declaree dans le manifeste existe vraiment.

Apercu par defaut (rien n'est ecrit) :
    python test_voix/_generer_icones_pwa.py
Pour ecrire les fichiers :
    python test_voix/_generer_icones_pwa.py --ecrire
"""

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
FRONTEND = RACINE / "frontend"
MAITRE = FRONTEND / "image_NIMM_ePub.png"
MANIFESTE = FRONTEND / "manifest.json"

# (fichier a produire, taille) -- la liste est LUE dans le manifeste ; ces
# entrees servent de plan de secours si le manifeste ne les declare pas encore.
A_PRODURE = [
    ("icon-192.png", 192),
    ("icon-512.png", 512),
    ("apple-touch-icon.png", 180),
    # Icone « maskable » : Android decoupe l'icone (rond, carre arrondi...) et
    # attend une marge de securite autour du dessin. Sans elle, le logo est
    # rogne sur l'ecran d'accueil.
    ("icon-maskable-512.png", 512),
]

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def ecrire_icone(taille, chemin, maskable=False):
    """Fabrique une icone carree a partir du logo maitre."""
    from PIL import Image
    logo = Image.open(MAITRE).convert('RGBA')
    if maskable:
        # Logo a 78 % dans un carre plein (la zone sure d'une icone maskable),
        # sur le fond sombre de l'application.
        fond = Image.new('RGBA', (taille, taille), (13, 13, 13, 255))
        cote = int(taille * 0.78)
        mini = logo.resize((cote, cote), Image.LANCZOS)
        fond.paste(mini, ((taille - cote) // 2, (taille - cote) // 2), mini)
        fond.convert('RGB').save(chemin, 'PNG', optimize=True)
    else:
        logo.resize((taille, taille), Image.LANCZOS).save(chemin, 'PNG',
                                                          optimize=True)


def main():
    from PIL import Image

    ecrire = '--ecrire' in sys.argv

    print('=' * 66)
    print('ICONES DE LA PWA' + ('' if ecrire else '  (APERCU : rien ne sera ecrit)'))
    print('=' * 66)
    verifier('le logo maitre existe', MAITRE.is_file(), MAITRE)
    verifier('le manifeste existe', MANIFESTE.is_file(), MANIFESTE)
    if ECHECS:
        return 1
    maitre = Image.open(MAITRE)
    print('   logo maitre : %sx%s' % (maitre.width, maitre.height))

    manifeste = json.loads(MANIFESTE.read_text(encoding='utf-8'))

    print('')
    print('1) ce que le manifeste declare, et ce que les fichiers sont vraiment')
    for icone in manifeste.get('icons', []):
        nom = Path(icone['src']).name
        chemin = FRONTEND / nom
        declare = icone.get('sizes', '')
        if not chemin.is_file():
            # Pas encore generee : ce n'est PAS un echec en soi (le script est
            # justement fait pour la fabriquer) -- mais Chrome, lui, la refusera
            # tant qu'elle n'existe pas.
            print('   %-26s declare %-10s -> A GENERER' % (nom, declare))
            continue
        reel = Image.open(chemin)
        taille_reelle = '%dx%d' % (reel.width, reel.height)
        verifier('%-26s declare %-10s reel %s' % (nom, declare, taille_reelle),
                 declare == taille_reelle,
                 'la taille declaree ne correspond pas au fichier : Chrome '
                 'rejette cette icone')

    print('')
    print('2) les icones a produire (a partir du logo maitre)')
    for nom, taille in A_PRODURE:
        chemin = FRONTEND / nom
        if chemin.is_file():
            reel = Image.open(chemin)
            if reel.width == taille and reel.height == taille:
                print('   %-26s deja bonne (%dx%d)' % (nom, reel.width, reel.height))
                continue
        print('   %-26s a generer en %dx%d' % (nom, taille, taille))
        if ecrire:
            ecrire_icone(taille, chemin, maskable=nom.startswith('icon-maskable'))
            fait = Image.open(chemin)
            verifier('%s ecrit en %dx%d' % (nom, fait.width, fait.height),
                     fait.width == taille and fait.height == taille)

    if not ecrire:
        print('')
        print('   APERCU SEUL : relancer avec --ecrire pour fabriquer les fichiers.')
        return 0 if ECHECS == 0 else 1

    print('')
    print('3) relecture : chaque icone declaree correspond a son fichier')
    manifeste = json.loads(MANIFESTE.read_text(encoding='utf-8'))
    for icone in manifeste.get('icons', []):
        chemin = FRONTEND / Path(icone['src']).name
        if not chemin.is_file():
            verifier('%s existe' % icone['src'], False, 'absent')
            continue
        reel = Image.open(chemin)
        verifier('%s = %s' % (icone['src'], icone.get('sizes')),
                 icone.get('sizes') == '%dx%d' % (reel.width, reel.height))

    print('')
    print('TOUT EST OK' if ECHECS == 0 else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
