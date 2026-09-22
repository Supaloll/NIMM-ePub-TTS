# -*- coding: utf-8 -*-
"""Le TIROIR DES FILTRES doit ETRE VISIBLE quand il est ouvert (22/09/2026).

Bug rapporte par Laurent : « Quelque chose empeche l'ouverture de ⚙️ Filtres
(sur pc et mobile). Les options qu'on a cachees ne s'affichent pas a l'appui du
bouton. »

Ce qui se passait VRAIMENT (mesure sur l'application en marche, avant
correction) : le panneau s'ouvrait bien, mais le navigateur l'ECRASAIT --
`#cast-tools` ne mesurait plus que **5 px de haut sur ordinateur** et **12 px sur
telephone**, pour un contenu de 427 px, parce qu'il etait le SEUL element
autorise a se reduire (`min-height: 0`) face a une longue liste de personnages.
Appuyer sur le bouton semblait donc ne rien faire (et sur ordinateur, le premier
appui le REFERMAIT, puisqu'il part ouvert).

Ce que ce test mesure, dans un VRAI moteur de navigateur et SANS serveur :
  - il extrait le VRAI bloc `#cast-modal` de `frontend/index.html` et la VRAIE
    feuille `frontend/styles.css` : rien n'est recopie, donc la mesure porte sur
    ce qui est reellement livre ;
  - il remplit la liste avec 120 personnages, comme un livre reel (c'est la
    LISTE LONGUE qui declenchait le bug : sur une petite liste, il n'y paraissait
    pas) ;
  - il verifie que le tiroir ouvert garde une hauteur UTILE (>= 150 px), que ses
    barres ne sont pas ecrasees (hauteur > 0), et que le reste est atteignable ;
  - sur telephone, il verifie en plus que la fenetre ne deborde pas de l'ecran.

⚠️ Ce que ce test NE verifie PAS : l'etat de depart (replie sur telephone, ouvert
sur ordinateur) et le clic -- c'est `test_entete_casting.js` qui les couvre, sans
navigateur. Ici, on ouvre le tiroir a la main (comme le fait `app.js`) et on
mesure ce que le navigateur en fait.

Sortie ASCII uniquement. Il faut Playwright (comme test_couverture_mobile.py).
Usage : python test_voix/test_filtres_rendu.py
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(RACINE, 'frontend', 'styles.css'), encoding='utf-8') as f:
    CSS_INLINE = f.read()
with open(os.path.join(RACINE, 'frontend', 'index.html'), encoding='utf-8') as f:
    PAGE = f.read()

# Les commentaires HTML de la page decrivent la structure et citent des balises
# (« <div id=...> ») : ils faussaient le comptage des balises. On les retire
# AVANT de decouper le bloc -- ils n'ont aucun role dans la mise en page.
PAGE = re.sub(r'<!--.*?-->', '', PAGE, flags=re.S)

HAUTEUR_MINIMALE = 240      # la borne posee dans styles.css (#cast-tools)


def extraire_bloc(page, marqueur):
    """Le bloc HTML complet (balise ouvrante a fermante) qui contient `marqueur`.

    Un simple `index()` ne suffit pas : la fenetre du casting contient des blocs
    imbriques, et couper au premier `</div>` laisserait la page en morceaux. On
    compte donc les balises `div` ouvertes et fermees.
    """
    debut = page.rindex('<', 0, page.index(marqueur))
    i, profondeur = debut, 0
    while i < len(page):
        fin = page.find('>', i) + 1
        if fin <= 0:
            raise ValueError('bloc non termine : %s' % marqueur)
        # `lstrip()` est indispensable : le morceau lu commence a la fin de la
        # balise precedente, donc par l'INDENTATION de celle-ci -- sans lui,
        # `startswith('<div')` est faux et le comptage ne veut rien dire (piege
        # trouve le 22/09/2026 en deboguant ce test).
        balise = page[i:fin].lstrip()
        if balise.startswith('<div'):
            profondeur += 1
        elif balise.startswith('</div'):
            profondeur -= 1
            if profondeur == 0:
                return page[debut:fin]
        i = fin


MODALE = extraire_bloc(PAGE, 'id="cast-modal"')

# 120 personnages : la liste longue qui declenchait le bug.
ROWS = ''.join(
    '<div class="cast-row"><div class="cast-row-top">Personnage %d</div></div>' % i
    for i in range(1, 121))

HTML = """<!DOCTYPE html>
<html lang="fr" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>%s</style>
</head><body>
%s
</body></html>""" % (CSS_INLINE, MODALE)

MESURE = """() => {
  const h = (id) => {
    const el = document.getElementById(id);
    return el ? Math.round(el.getBoundingClientRect().height) : -1;
  };
  const outils = document.getElementById('cast-tools');
  const boite  = document.querySelector('.cast-box');
  return {
    outils: h('cast-tools'),
    genre: h('cast-gender-bar'),
    filtre: h('cast-filtre-bar'),
    saga: h('cast-saga-bar'),
    recast: h('cast-recast-bar'),
    liste: h('cast-list'),
    boite: boite ? Math.round(boite.getBoundingClientRect().height) : -1,
    debordement: outils.scrollHeight - outils.clientHeight,
    dansEcran: boite ? Math.round(boite.getBoundingClientRect().bottom)
                       <= (window.innerHeight + 1) : false,
  };
}"""

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for nom, largeur in (('ordinateur', 1200), ('telephone', 360)):
        page = navigateur.new_page(viewport={'width': largeur, 'height': 740})
        page.set_content(HTML)
        # La liste longue, puis l'etat OUVERT (comme le fait _appliquerEnteteCasting).
        page.evaluate("""(rows) => {
          // La fenetre du casting est cachee d'origine (class="hidden") : on
          // l'ouvre, comme le fait l'application quand on appuie sur « Voix
          // multiples ». Puis la liste longue, puis l'etat OUVERT du tiroir.
          document.getElementById('cast-modal').classList.remove('hidden');
          document.getElementById('cast-list').innerHTML = rows;
          document.getElementById('cast-tools').classList.remove('hidden');
        }""", ROWS)
        page.wait_for_timeout(200)
        m = page.evaluate(MESURE)
        print('')
        print('--- %s (%d px) ---' % (nom, largeur))
        print('    tiroir %s px / voix proposees %s px / filtres %s px / '
              'saga %s px / re-cast %s px'
              % (m['outils'], m['genre'], m['filtre'], m['saga'], m['recast']))
        print('    liste %s px / fenetre %s px / reste a faire defiler : %s px'
              % (m['liste'], m['boite'], m['debordement']))
        verifier('le tiroir ouvert garde une hauteur utilisable (>= %d px)'
                 % HAUTEUR_MINIMALE, m['outils'] >= HAUTEUR_MINIMALE, m['outils'])
        verifier('la barre "voix proposees" n est pas ecrasee',
                 m['genre'] > 0, m['genre'])
        verifier('la barre des filtres (age, genre) n est pas ecrasee',
                 m['filtre'] > 0, m['filtre'])
        verifier('la barre de saga (sous les filtres) est presente',
                 m['saga'] > 0, m['saga'])
        verifier('la liste des personnages garde de la place',
                 m['liste'] >= 90, m['liste'])
        verifier('la fenetre ne deborde pas de l ecran', m['dansEcran'],
                 'bas de fenetre : %s px' % m['boite'])
        page.close()
    navigateur.close()

print('')
print('TOUT EST OK' if ECHECS == 0 else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
sys.exit(0 if ECHECS == 0 else 1)

