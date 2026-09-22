# -*- coding: utf-8 -*-
"""Rendu du TIROIR DU MENU DU LECTEUR (22/09/2026) -- preuve visuelle.

Demande de Laurent : « Pour le menu du bas, on va faire un tiroir. Il faut
afficher uniquement les boutons de lecture [...]. Dessous, tout le reste du menu
qui s'ouvre en ouvrant ce menu tiroir. »

Ce que ce test regarde, dans un VRAI moteur de navigateur, et sans serveur :
  - il extrait le pied du lecteur (`<footer id="reader-footer">`) du VRAI
    index.html, et la VRAIE feuille frontend/styles.css : rien n'est recopie,
    donc si la poignee ou un reglage demenage, la mesure porte sur ce qui est
    reellement livre ;
  - sur un TELEPHONE (360 px), il verifie que le tiroir REPLIE ne montre plus
    aucun reglage, que les sept commandes de lecture tiennent sur UNE ligne,
    que la poignee est bien visible et facile a taper (largeur), et que RIEN ne
    deborde de l'ecran ;
  - il verifie que le tiroir OUVERT rend toute la place aux reglages, et qu'il
    laisse MOINS de place au texte quand il est ouvert (c'est le but) ;
  - sur un ORDINATEUR (1200 px), la poignee DISPARAIT et les reglages restent
    la, comme avant le tiroir.

Sortie ASCII uniquement. Il faut Playwright (comme test_couverture_mobile.py).
Usage : python test_voix/test_tiroir_lecteur_rendu.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER_CSS = os.path.join(RACINE, "frontend", "styles.css")
FICHIER_HTML = os.path.join(RACINE, "frontend", "index.html")

with open(FICHIER_CSS, "r", encoding="utf-8") as f:
    CSS_INLINE = f.read()

with open(FICHIER_HTML, "r", encoding="utf-8") as f:
    PAGE = f.read()

# Le vrai pied du lecteur, extrait de la vraie page.
debut = PAGE.index('<footer id="reader-footer">')
fin = PAGE.index("</footer>", debut) + len("</footer>")
FOOTER = PAGE[debut:fin]

# Les sept commandes de lecture de la barre du bas.
BOUTONS = ["prev-btn", "para-prev-btn", "sent-prev-btn", "tts-play-btn",
           "sent-next-btn", "para-next-btn", "next-btn"]

TEXTE = ("Le soleil se couchait sur les toits de Marseille. " * 12).strip()

ECHE = 0


def verifier(nom, condition, detail=""):
    global ECHE
    if condition:
        print("  OK    " + nom)
    else:
        print("  ECHEC " + nom + ("  -> " + str(detail) if detail else ""))
        ECHE += 1


HTML = """<!DOCTYPE html>
<html lang="fr" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>%s</style>
</head><body>
<div id="app">
  <div id="view-reader" class="view active">
    <header id="reader-header"><div id="reader-book-title">Le Comte de Monte-Cristo</div></header>
    <div id="chapter-info"><span id="chapter-title-display">Chapitre 96</span></div>
    <div id="reader-content">%s</div>
    %s
  </div>
</div>
</body></html>""" % (CSS_INLINE, TEXTE, FOOTER)

MESURES = """() => {
  const pied     = document.getElementById('reader-footer');
  const poignee  = document.getElementById('reader-tiroir-btn');
  const reglages = document.getElementById('reader-settings');
  const rp = poignee.getBoundingClientRect();
  const nav = document.getElementById('reader-nav');
  // Seuls les boutons AFFICHES comptent (le bouton « Reparer » vide, plus bas,
  // ne s'affiche jamais : il est exclu de ce compte).
  const boutons = %s.map((id) => document.getElementById(id))
                    .filter((b) => b.offsetParent !== null);
  // Deux boutons sont sur la MEME ligne quand leurs sommets sont proches : le
  // bouton rond de lecture est plus HAUT (44 ou 48 px) que ses voisins (36 ou
  // 40 px), donc comparer les sommets a l'unite dirait « deux lignes » a tort.
  // On compte les groupes de sommets : un ecart de plus de 20 px veut dire une
  // nouvelle ligne (sur la barre, une ligne en plus, c'est 40 px et plus).
  const sommets = boutons.map((b) => b.getBoundingClientRect().top)
                         .sort((a, b) => a - b);
  let nbLignes = sommets.length ? 1 : 0;
  for (let i = 1; i < sommets.length; i++) {
    if (sommets[i] - sommets[i - 1] > 20) nbLignes++;
  }
  // Les reglages a compter : les menus, et les boutons qui ONT UN LIBELLE (le
  // bouton « Reparer » est vide ici, et le CSS lui interdit de s'afficher vide).
  const champs = Array.from(reglages.querySelectorAll('button, select'))
    .filter((e) => e.tagName !== 'BUTTON' || e.textContent.trim() !== '');
  const reparer = document.getElementById('reparer-open-btn');
  return {
    footer: Math.round(pied.getBoundingClientRect().height),
    contenu: Math.round(document.getElementById('reader-content').getBoundingClientRect().height),
    poignee: Math.round(rp.width) + 'x' + Math.round(rp.height),
    poigneeVisible: poignee.offsetParent !== null,
    poigneeExpanded: poignee.getAttribute('aria-expanded'),
    reglagesCaches: reglages.offsetParent === null,
    reglagesVisibles: champs.filter((e) => e.offsetParent !== null).length,
    reglagesTotal: champs.length,
    reparerVideSansPlace: reparer.offsetParent === null,
    lignes: [nbLignes, boutons.length],
    hauteurBarre: Math.round(nav.getBoundingClientRect().height),
    hauteurBouton: Math.round(Math.max(
      ...boutons.map((b) => b.getBoundingClientRect().height))),
    debordement: Math.round(document.documentElement.scrollWidth) - window.innerWidth,
  };
}""" % str(BOUTONS).replace('"', "'")


def mesurer(page, ouvert):
    """Charge la page dans l'etat demande et renvoie les mesures.

    Le tiroir est OUVERT dans la page (etat par defaut) ; sur telephone, le
    script le replie a l'entree dans le lecteur (_appliquerTiroirLecteur,
    app.js). Ici on refait exactement ce geste : sans cela, le test mesurerait
    un etat que Laurent ne voit jamais.
    """
    page.set_content(HTML)
    if not ouvert:
        page.eval_on_selector('#reader-settings',
                              "el => el.classList.add('hidden')")
        page.eval_on_selector(
            '#reader-tiroir-btn',
            "el => { el.setAttribute('aria-expanded', 'false');"
            " el.setAttribute('aria-label', 'Ouvrir le menu du lecteur'); }")
    page.wait_for_timeout(150)
    return page.evaluate(MESURES)


with sync_playwright() as p:
    navigateur = p.chromium.launch()

    # --- 1) Telephone, tiroir replie ---
    print("")
    print("1) telephone, tiroir replie (ce qu'on voit en ouvrant un livre)")
    page = navigateur.new_page(viewport={"width": 360, "height": 740},
                               device_scale_factor=2, is_mobile=True,
                               has_touch=True)
    replie = mesurer(page, False)
    print("    pied %s px | texte %s px | poignee %s px"
          % (replie["footer"], replie["contenu"], replie["poignee"]))
    verifier("plus aucun reglage n'est montre",
             replie["reglagesCaches"] and replie["reglagesVisibles"] == 0,
             "%s visibles sur %s" % (replie["reglagesVisibles"],
                                     replie["reglagesTotal"]))
    verifier("les sept commandes de lecture tiennent sur UNE ligne",
             replie["lignes"][0] == 1
             and replie["hauteurBarre"] <= replie["hauteurBouton"] + 8,
             "%s ligne(s), barre %s px pour un bouton de %s px"
             % (replie["lignes"][0], replie["hauteurBarre"],
                replie["hauteurBouton"]))
    verifier("aucune commande de lecture ne manque",
             replie["lignes"][1] == 7, replie["lignes"][1])
    verifier("la poignee est visible", replie["poigneeVisible"])
    largeur_poignee = int(replie["poignee"].split("x")[0])
    hauteur_poignee = int(replie["poignee"].split("x")[1])
    verifier("elle couvre la largeur (cible facile au doigt)",
             largeur_poignee >= 300, replie["poignee"])
    verifier("elle reste fine (elle ne mange pas le texte)",
             20 <= hauteur_poignee <= 32, replie["poignee"])
    verifier("l'etat annonce est bien « replie »",
             replie["poigneeExpanded"] == "false", replie["poigneeExpanded"])
    verifier("rien ne deborde de l'ecran", replie["debordement"] <= 0,
             replie["debordement"])

    # --- 2) Le meme telephone, tiroir ouvert ---
    print("")
    print("2) le meme telephone, tiroir ouvert")
    ouvert = mesurer(page, True)
    print("    pied %s px | texte %s px | reglages %s / %s visibles"
          % (ouvert["footer"], ouvert["contenu"],
             ouvert["reglagesVisibles"], ouvert["reglagesTotal"]))
    verifier("tous les reglages sont la",
             ouvert["reglagesTotal"] > 0
             and ouvert["reglagesVisibles"] == ouvert["reglagesTotal"],
             "%s / %s" % (ouvert["reglagesVisibles"], ouvert["reglagesTotal"]))
    verifier("le bouton « Reparer », vide, ne prend aucune place",
             ouvert["reparerVideSansPlace"])
    verifier("le pied grandit quand le tiroir s'ouvre",
             ouvert["footer"] > replie["footer"],
             "%s px -> %s px" % (replie["footer"], ouvert["footer"]))
    verifier("le texte cede la place (c'est le but du tiroir)",
             ouvert["contenu"] < replie["contenu"],
             "%s px -> %s px" % (replie["contenu"], ouvert["contenu"]))
    verifier("la poignee reste a sa place, en haut du tiroir",
             ouvert["poigneeVisible"])
    verifier("l'etat annonce est bien « ouvert »",
             ouvert["poigneeExpanded"] == "true", ouvert["poigneeExpanded"])
    verifier("rien ne deborde de l'ecran non plus",
             ouvert["debordement"] <= 0, ouvert["debordement"])

    # --- 3) Ordinateur ---
    print("")
    print("3) ordinateur (1200 px) : la poignee disparait, les reglages restent")
    page_pc = navigateur.new_page(viewport={"width": 1200, "height": 800})
    pc = mesurer(page_pc, True)
    print("    pied %s px | poignee %s" % (pc["footer"], pc["poignee"]))
    verifier("la poignee est masquee sur ordinateur", not pc["poigneeVisible"])
    verifier("les reglages restent affiches, comme avant le tiroir",
             pc["reglagesTotal"] > 0
             and pc["reglagesVisibles"] == pc["reglagesTotal"],
             "%s / %s" % (pc["reglagesVisibles"], pc["reglagesTotal"]))
    verifier("les sept commandes de lecture tiennent toujours sur une ligne",
             pc["lignes"][0] == 1
             and pc["hauteurBarre"] <= pc["hauteurBouton"] + 8,
             "%s ligne(s), barre %s px pour un bouton de %s px"
             % (pc["lignes"][0], pc["hauteurBarre"], pc["hauteurBouton"]))
    verifier("rien ne deborde de la fenetre", pc["debordement"] <= 0,
             pc["debordement"])

    navigateur.close()

print("")
print("TOUT EST OK" if ECHE == 0 else "%s VERIFICATION(S) EN ECHEC" % ECHE)
sys.exit(0 if ECHE == 0 else 1)
