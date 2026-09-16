# -*- coding: utf-8 -*-
"""
Preuve du bug d'affichage des couvertures NIMM ePub.

Construit une page de test qui reprend EXACTEMENT le markup genere par
renderLibrary() (frontend/app.js) et la vraie feuille frontend/styles.css,
puis mesure la taille rendue de la vignette .book-cover dans un vrai moteur
de navigateur.

Attendu si tout va bien : hauteur = largeur x 1.5 (ratio 2/3).
Sortie ASCII uniquement.
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER_CSS = os.path.join(RACINE, "frontend", "styles.css")

# La feuille est integree telle quelle dans la page de test : aucune
# dependance externe (styles.css ne contient ni url() ni @import), donc la
# mesure porte bien sur le vrai CSS de l'application.
with open(FICHIER_CSS, "r", encoding="utf-8") as f:
    CSS_INLINE = f.read()

# Titres reels de la bibliotheque de Laurent, dont les plus longs.
TITRES = [
    "Le comte de Monte-Cristo - Tome 1 - Alexandre Dumas",
    "Memoires authentiques de Latude (Jean-Henri Latude [Latude, Jean-Henri])"
    " (z-library.sk, 1lib.sk, z-lib.sk)",
    "Dialogues desaccordes -- Eric Naulleau & Alain Soral -- Anna's Archive",
    "Jacques Cellard - Souvenirs d'une gamine effrontee",
    "Le Retour de l'enfant prodigue - Andre Gide",
    "Marathoniens-9782212149838",
    "Nabokov Vladimir - Ada ou l'ardeur",
    "Stephen King - 22-11-63",
    "Roberts, Gregory David - Shantaram",
    "Notre-Dame de Paris - Victor Hugo",
    "Cosmetique de l'ennemi - Amelie Nothomb",
    "DUMAS_T1 - Le Comte de Monte-Cristo",
]

# Vraie couverture du projet (600x800) en data URL : aucune requete reseau.
FICHIER_IMG = os.path.join(
    RACINE, "data", "library",
    "Le comte de Monte-Cristo - Tome 1 - Alexandre Dumas_cover.jpg")
import base64

with open(FICHIER_IMG, "rb") as f:
    IMG = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")

cartes = ""
for titre in TITRES:
    cartes += """
      <div class="book-card" role="listitem">
        <img class="book-cover" src="%s" alt="Couverture">
        <div class="book-info">
          <div class="book-title">%s</div>
          <div class="book-author">Alexandre Dumas</div>
          <div class="book-progress-bar"><div class="book-progress-fill"></div></div>
        </div>
      </div>""" % (IMG, titre)

HTML = """<!DOCTYPE html>
<html lang="fr" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>%s</style>
</head><body>
<div id="app">
  <div id="view-library" class="view">
    <header id="library-header">
      <span id="app-title">NIMM <span class="accent">ePub</span></span>
      <label id="upload-btn">Ajouter</label>
    </header>
    <div id="book-grid" role="list">%s
    </div>
  </div>
</div>
</body></html>""" % (CSS_INLINE, cartes)


def mesurer(navigateur, nom, largeur, hauteur):
    nav = getattr(navigateur, nom)
    browser = nav.launch()
    page = browser.new_page(viewport={"width": largeur, "height": hauteur},
                            device_scale_factor=2, is_mobile=True,
                            has_touch=True)

    conditions = [
        ("texte normal 100%", ""),
        ("texte agrandi 130% (reglage systeme)", "html { font-size: 21px; }"),
        ("texte agrandi 200% (reglage systeme)", "html { font-size: 32px; }"),
    ]
    correctifs = [
        ("CSS actuel", ""),
        ("CSS corrige", "#book-grid { grid-auto-rows: max-content; }"),
    ]
    variantes = []
    for lib_cond, css_cond in conditions:
        for lib_fix, css_fix in correctifs:
            variantes.append(("%s | %s" % (lib_cond, lib_fix), css_cond + css_fix))

    print("")
    print("=== %s | viewport %sx%s ===" % (nom, largeur, hauteur))
    for titre_variante, css_extra in variantes:
        page.set_content(HTML)
        if css_extra:
            page.add_style_tag(content=css_extra)
        page.wait_for_timeout(900)
        infos = page.evaluate("""() => {
          const grille = document.getElementById('book-grid');
          const img    = document.querySelector('.book-cover');
          const rg = grille.getBoundingClientRect();
          const ri = img.getBoundingClientRect();
          const style = getComputedStyle(grille);
          // Toutes les cartes : detecte le chevauchement carte / contenu.
          const cartes = Array.from(document.querySelectorAll('.book-card')).map((c) => {
            const r = c.getBoundingClientRect();
            const im = c.querySelector('.book-cover').getBoundingClientRect();
            const inf = c.querySelector('.book-info').getBoundingClientRect();
            return {
              h: Math.round(r.height),
              besoin: Math.round(im.height + inf.height),
            };
          });
          const chevauche = cartes.filter(c => c.h < c.besoin - 2).length;
          // Toutes les vignettes : verifie le ratio 2/3 de chacune.
          const vignettes = Array.from(document.querySelectorAll('.book-cover'))
            .map((im) => {
              const r = im.getBoundingClientRect();
              const l = r.width, h = r.height;
              return Math.abs(h - l * 1.5) <= 2 ? 'ok' : 'ecrasee';
            });
          return {
            grille: Math.round(rg.width) + 'x' + Math.round(rg.height),
            colonnes: style.gridTemplateColumns,
            img: Math.round(ri.width) + 'x' + Math.round(ri.height),
            vignettes: vignettes,
            defilable: grille.scrollHeight > grille.clientHeight + 2,
            cartes: cartes,
            chevauche: chevauche,
            doc: Math.round(document.documentElement.scrollWidth) + 'x'
                 + Math.round(document.documentElement.scrollHeight),
            chargee: img.complete && img.naturalWidth > 0,
          };
        }""")
        ratio = infos["img"].split("x")
        l, h = int(ratio[0]), int(ratio[1])
        attendu = round(l * 1.5)
        etat = "OK ratio 2/3" if abs(h - attendu) <= 2 else "ECRASEE"
        print("")
        print("  %s" % titre_variante)
        print("    grille %s | colonnes %s" % (infos["grille"], infos["colonnes"]))
        print("    vignette %s px (attendu %s px de haut) -> %s"
              % (infos["img"], attendu, etat))
        ecrasees = infos["vignettes"].count("ecrasee")
        print("    vignettes ecrasees : %s / %s | grille defilable : %s"
              % (ecrasees, len(infos["vignettes"]),
                 "oui" if infos["defilable"] else "non"))
        print("    cartes : %s" % " | ".join(
            "%s px (contenu %s)" % (c["h"], c["besoin"]) for c in infos["cartes"]))
        print("    cartes trop courtes pour leur contenu (chevauchement) : %s / %s"
              % (infos["chevauche"], len(infos["cartes"])))
    browser.close()


with sync_playwright() as p:
    for nom in ("chromium", "firefox"):
        try:
            mesurer(p, nom, 390, 844)
        except Exception as e:
            print("")
            print("=== %s indisponible : %s" % (nom, str(e)[:160]))
