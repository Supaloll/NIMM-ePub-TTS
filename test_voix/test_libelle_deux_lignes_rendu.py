# -*- coding: utf-8 -*-
"""Les DEUX LIGNES d'un libelle de voix : ce que le navigateur en fait vraiment.

Demande de Laurent (22/09/2026) : « Si c'est dur a manipuler, est-ce qu'on peut
forcer un saut de ligne ? Si oui, on laisse sur la 1ere ligne : Prenom -
drapeaux - age et timbre, et sur la 2eme ligne : moteur - nom du personnage
portant la voix / LIBRE. »

Le libelle porte un saut de ligne (`_libelleVoix(v, true)`, app.js) et c'est la
VRAIE feuille styles.css qui le fait respecter (`white-space: pre-line` sur les
options). Ce test mesure les deux, dans un vrai navigateur, sur une liste
OUVERTE (un `<select size=...>`) : les options y sont rendues DANS la page, donc
mesurables -- contrairement a la liste derobante habituelle, que le navigateur
dessine hors de la page.

Ce qu'il prouve, et ce qu'il ne prouve pas -- dit franchement :
  - il prouve que la regle CSS fonctionne : la meme option occupe DEUX lignes
    avec la feuille de l'application, et UNE seule si on la neutralise ;
  - il ne prouve RIEN pour la liste deroulante d'un telephone : sur Android, la
    liste ouverte est dessinee par le systeme (grosse police, fond clair), et
    elle peut aplatir le saut de ligne. Seul l'oeil de Laurent tranche, sur son
    telephone.

Depuis le 24/09/2026, sa section 3 ne mesure plus l'encart qui se depliait DANS
la ligne du personnage (`.voix-liste-encart`, supprime) mais la MODALE qui l'a
remplace : `#cast-voix-modal`, ouverte par le bouton de voix. Elle verifie la
taille qu'elle prend sur un telephone et sur un ordinateur, le defilement de la
liste, et le fait que le bouton « Fermer » reste DANS l'ecran.

Sortie ASCII uniquement. Il faut Playwright (comme test_couverture_mobile.py).
Usage : python test_voix/test_libelle_deux_lignes_rendu.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER_CSS = os.path.join(RACINE, "frontend", "styles.css")

with open(FICHIER_CSS, "r", encoding="utf-8") as f:
    CSS_INLINE = f.read()

# Le libelle REELLEMENT produit par _libelleVoix(v, true) + l'etat de la voix :
# « <symbole> Anna <drapeau FR> adulte grave » puis, sur la 2e ligne,
# « <icone XTTS> · LIBRE ». Ecrit ici en clair pour que la mesure soit lisible.
LIBELLE = ("\u2640\ufe0f Anna \U0001F1EB\U0001F1F7 adulte grave"
           "\n\U0001F9EC \u00b7 LIBRE")
# Le meme, sans saut de ligne : la ligne de reference.
LIBELLE_UNE_LIGNE = LIBELLE.replace("\n", " ")

# Un libelle volontairement PLUS LONG que le menu, pour verifier que le texte
# d'un choix ne se replie jamais non plus -- la cause est donc le choix
# lui-meme, et non la regle CSS.
TEXTE_LONG = ("\u2640\ufe0f Anne-Charlotte de la Rochefoucauld "
              "\U0001F1EB\U0001F1F7\U0001F1EC\U0001F1E7 vieille tres aigu "
              "\U0001F9EC \u00b7 Edmond Dantes (1 234 repliques)")

HTML = """<!DOCTYPE html>
<html lang="fr" data-theme="dark"><head><meta charset="utf-8">
<style>%s</style>
</head><body>
<div id="app">
  <select id="voice-phrase-select" size="8">
    <option id="deux">%s</option>
    <option id="une">%s</option>
    <option id="longue">%s</option>
  </select>
</div>
</body></html>""" % (CSS_INLINE, LIBELLE, LIBELLE_UNE_LIGNE, TEXTE_LONG)

ECHE = 0


def verifier(nom, condition, detail=""):
    global ECHE
    if condition:
        print("  OK    " + nom)
    else:
        print("  ECHEC " + nom + ("  -> " + str(detail) if detail else ""))
        ECHE += 1


def hauteurs(page):
    return page.evaluate("""() => {
      const h = (id) => Math.round(
        document.getElementById(id).getBoundingClientRect().height);
      return { deux: h('deux'), une: h('une'), longue: h('longue'),
               // Le fond du corps dit que la VRAIE feuille est chargee : elle
               // donne au body la couleur du theme sombre de l'application.
               // (On ne regarde plus `white-space` : la regle `pre-line` a ete
               // essayee puis retiree le 22/09/2026, faute d'effet.)
               fond: getComputedStyle(document.body).backgroundColor,
               largeurSelect: Math.round(
                 document.getElementById('voice-phrase-select')
                   .getBoundingClientRect().width) };
    }""")


with sync_playwright() as p:
    navigateur = p.chromium.launch()

    print("")
    print("CE QUE LE NAVIGATEUR FAIT DU SAUT DE LIGNE DANS UN CHOIX DE MENU")
    print("(mesure, pas verdict : c'est l'oeil de Laurent qui tranche, sur son")
    print(" telephone -- la liste deroulante du telephone n'est pas mesurable ici)")
    for nom, largeur in (("telephone", 360), ("ordinateur", 1200)):
        print("")
        print("--- %s (%s px) ---" % (nom, largeur))
        page = navigateur.new_page(viewport={"width": largeur, "height": 740})
        page.set_content(HTML)
        page.wait_for_timeout(150)
        mesure = hauteurs(page)
        print("    option a deux lignes ........ %s px" % mesure["deux"])
        print("    option d'une ligne (temoin) .. %s px" % mesure["une"])
        print("    option tres longue ........... %s px (largeur du menu : %s px)"
              % (mesure["longue"], mesure["largeurSelect"]))
        print("    regle CSS appliquee .......... feuille de l'application, fond %s"
              % mesure["fond"])
        # 1) la feuille est bien celle de l'application (fond du theme sombre)
        verifier("la feuille de style de l'application est bien prise en compte",
                 mesure["fond"] == "rgb(13, 13, 13)", mesure["fond"])
        # 2) et pourtant, le saut de ligne ne fait AUCUNE ligne de plus
        verifier("le saut de ligne ne change PAS la hauteur du choix "
                 "(il est donc aplati)",
                 mesure["deux"] == mesure["une"],
                 "%s px contre %s px" % (mesure["deux"], mesure["une"]))
        # 3) et un libelle plus long que le menu se replie TOUT SEUL : le texte
        #    n'est pas perdu, mais le repli est SUBI (on ne choisit pas ou il
        #    tombe) -- c'est exactement ce que Laurent voyait sur son telephone.
        verifier("un libelle plus long que le menu se replie tout seul "
                 "(repli subi, pas choisi)",
                 mesure["longue"] >= mesure["une"],
                 "%s px contre %s px" % (mesure["longue"], mesure["une"]))
        page.close()

    navigateur.close()

print("")
print("CONCLUSION (mesuree le 22/09/2026, Chromium) :")
print("  - on ne peut PAS forcer un saut de ligne dans un choix de menu :")
print("    le libelle qui en porte un occupe la MEME hauteur qu'un autre,")
print("    le saut est aplati ;")
print("  - un libelle plus long que le menu se replie tout seul, mais on ne")
print("    choisit pas ou : le repli est subi ;")
print("  - la liste DEROULANTE d'un telephone n'est pas mesurable ici (elle est")
print("    dessinee par le systeme, hors de la page) : seul l'oeil tranche.")
print("")
print("2) LA LISTE DE L'APPLICATION, elle, fait vraiment DEUX lignes")
print("   (c'est ce qui remplace le menu deroulant : voir BACKLOG, voie B)")
print("")

# Le fragment est celui que _peindreListeVoixPhrase construit, avec la VRAIE
# feuille de style : rien n'est recopie du CSS, et les noms de classes sont
# ceux du code (une faute de classe ferait echouer les mesures).
LIGNE = """<li class="voix-liste-item"%(actuelle)s>
  <button class="voix-liste-choix">
    <span class="voix-liste-nom">%(nom)s</span>
    <span class="voix-liste-etat">%(etat)s</span>
  </button>
  <button class="voix-liste-ecoute">\u25b6</button>
</li>"""

HTML_LISTE = """<!DOCTYPE html>
<html lang="fr" data-theme="dark"><head><meta charset="utf-8">
<style>%s</style>
</head><body><div id="app">
<ul id="voice-phrase-liste" style="width:340px">
  <li class="voix-liste-groupe">\U0001F469 Femmes</li>
  %s
  %s
</ul>
</div></body></html>""" % (
    CSS_INLINE,
    LIGNE % {"actuelle": ' data-actuelle="true"',
             "nom": '\u2714 \u2640\ufe0f Anna \U0001F1EB\U0001F1F7 adulte grave',
             "etat": '\U0001F9EC \u00b7 LIBRE'},
    LIGNE % {"actuelle": '',
             "nom": '\u2642\ufe0f Bruno \U0001F1EB\U0001F1F7 jeune m\u00e9dium',
             "etat": '\u2601\ufe0f \u00b7 Edmond'})

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    page = navigateur.new_page(viewport={"width": 360, "height": 740})
    page.set_content(HTML_LISTE)
    page.wait_for_timeout(150)
    liste = page.evaluate("""() => {
      const items = Array.from(document.querySelectorAll('.voix-liste-item'));
      const lire = (li) => {
        const nom   = li.querySelector('.voix-liste-nom').getBoundingClientRect();
        const etat  = li.querySelector('.voix-liste-etat').getBoundingClientRect();
        const item  = li.getBoundingClientRect();
        const style = getComputedStyle(li.querySelector('.voix-liste-nom'));
        const styleEtat = getComputedStyle(li.querySelector('.voix-liste-etat'));
        const fond  = getComputedStyle(document.getElementById('voice-phrase-liste'));
        return {
          hauteurItem: Math.round(item.height),
          hauteurNom:  Math.round(nom.height),
          nomX: Math.round(nom.left), etatX: Math.round(etat.left),
          nomBas: Math.round(nom.bottom), etatHaut: Math.round(etat.top),
          couleur: style.color, graisse: style.fontWeight,
          couleurEtat: styleEtat.color,
          fond: fond.backgroundColor, actuelle: li.dataset.actuelle === 'true',
        };
      };
      return items.map(lire);
    }""")
    print("    (fond de la liste : %s)" % liste[0]["fond"])
    verifier("le fond de la liste est celui du theme sombre, pas du blanc",
             liste[0]["fond"] == "rgb(13, 13, 13)", liste[0]["fond"])
    verifier("chaque ligne occupe DEUX lignes de texte (nom + etat)",
             all(l["hauteurItem"] > l["hauteurNom"] + 10 for l in liste),
             [l["hauteurItem"] for l in liste])
    verifier("la 2e ligne est bien SOUS la premiere",
             all(l["etatHaut"] >= l["nomBas"] - 2 for l in liste),
             [(l["nomBas"], l["etatHaut"]) for l in liste])
    verifier("les deux lignes commencent au meme endroit (alignees)",
             all(abs(l["nomX"] - l["etatX"]) <= 1 for l in liste),
             [(l["nomX"], l["etatX"]) for l in liste])
    verifier("la voix portee par le personnage ressort (couleur d'accent)",
             liste[0]["couleur"] != liste[1]["couleur"]
             and liste[0]["couleur"] == "rgb(200, 169, 110)"
             and liste[1]["actuelle"] is False,
             liste[0]["couleur"] + ' / ' + liste[1]["couleur"])
    verifier("elle ressort aussi par sa graisse",
             liste[0]["graisse"] != liste[1]["graisse"],
             liste[0]["graisse"] + ' / ' + liste[1]["graisse"])
    # Demande de Laurent apres son essai du 22/09/2026 : la 2e ligne (moteur +
    # etat) doit etre en BLANC comme la 1re -- elle etait en gris. La taille, elle,
    # ne change pas (0.7rem).
    verifier("la 2e ligne est ecrite en BLANC, comme la 1re (demande de Laurent)",
             all(l["couleurEtat"] == "rgb(232, 227, 218)" for l in liste),
             [l["couleurEtat"] for l in liste])
    navigateur.close()

print("")
print("3) LA MODALE DES VOIX D'UN PERSONNAGE (24/09/2026)")
print("   (elle remplace l'encart qui se depliait DANS la ligne du personnage :")
print("   demande de Laurent, « une genre de modale classique, qui prend plus de")
print("   place sur l'ecran (mobile et pc), pour une meilleure visibilite »)")
print("")

# Le fragment est celui que _ouvrirVoixPersonnage remplit : la fenetre du
# casting (pour comparer les largeurs) PUIS la modale des voix, avec vingt
# lignes -- assez pour que la liste defile et pour verifier que le bouton
# « Fermer » ne part pas hors de l'ecran. La VRAIE feuille de style est
# injectee, et les classes sont celles du code : une faute de classe ferait
# echouer les mesures.
LIGNE_MODALE = LIGNE % {"actuelle": '', "nom": '\u2640\ufe0f Anna \U0001F1EB\U0001F1F7 m\u00e9dium',
                        "etat": '\U0001F9EC \u00b7 LIBRE'}
LIGNE_ACTUELLE = LIGNE % {"actuelle": ' data-actuelle="true"',
                          "nom": '\u2714 \u2642\ufe0f Edmond \U0001F1EB\U0001F1F7 adulte grave',
                          "etat": '\U0001F9EC \u00b7 LIBRE'}
HTML_MODALE = """<!DOCTYPE html>
<html lang="fr" data-theme="dark"><head><meta charset="utf-8">
<style>%s</style>
</head><body>
<div id="cast-modal" class="modal-overlay">
  <div class="modal-box cast-box" id="boite-casting">
    <ul id="cast-list" style="height:180px"></ul>
  </div>
</div>
<div id="cast-voix-modal" class="modal-overlay">
  <div class="modal-box cast-box voix-perso-box" id="boite-voix">
    <div id="cast-voix-modal-header">
      <h3 id="cast-voix-titre">Voix de Edmond Dantes</h3>
      <button id="cast-voix-close-btn">&#x2715;</button>
    </div>
    <div id="cast-voix-filtres">
      <div id="cast-voix-genre-actions">
        <button type="button" data-genre="T" class="actif">Toutes</button>
        <button type="button" data-genre="F">&#x2640;&#xFE0F; Femmes</button>
        <button type="button" data-genre="M">&#x2642;&#xFE0F; Hommes</button>
      </div>
      <div id="cast-voix-age-actions">
        <button type="button" data-age="T" class="actif">Tous</button>
        <button type="button" data-age="enfant">&#x1F466; Enfant</button>
        <button type="button" data-age="jeune">&#x1F468;&#x200D;&#x1F9B1; Jeune</button>
        <button type="button" data-age="adulte">&#x1F9D1;&#x200D;&#x1F9B2; Adulte</button>
        <button type="button" data-age="vieux">&#x1F474; Vieux</button>
      </div>
      <span id="cast-voix-recap">20 voix</span>
    </div>
    <ul id="cast-voix-liste">%s</ul>
    <div class="modal-actions">
      <button id="cast-voix-annuler-btn" class="btn-secondary">Fermer</button>
    </div>
  </div>
</div>
</body></html>""" % (CSS_INLINE, LIGNE_ACTUELLE + LIGNE_MODALE * 19)

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for nom, largeur, hauteur in (("telephone", 360, 740),
                                  ("ordinateur", 1200, 800)):
        print("")
        print("--- %s (%s x %s px) ---" % (nom, largeur, hauteur))
        page = navigateur.new_page(viewport={"width": largeur, "height": hauteur})
        page.set_content(HTML_MODALE)
        page.wait_for_timeout(150)
        mesure = page.evaluate("""() => {
          const boite   = document.getElementById('boite-voix');
          const liste   = document.getElementById('cast-voix-liste');
          const modal   = document.getElementById('cast-voix-modal');
          const casting = document.getElementById('boite-casting');
          const fermer  = document.getElementById('cast-voix-annuler-btn');
          const styleModal = getComputedStyle(modal);
          const items = Array.from(liste.querySelectorAll('.voix-liste-item'));
          return {
            largeur: Math.round(boite.getBoundingClientRect().width),
            hauteur: Math.round(boite.getBoundingClientRect().height),
            largeurCasting: Math.round(casting.getBoundingClientRect().width),
            largeurListe: Math.round(liste.getBoundingClientRect().width),
            position: styleModal.position,
            zIndex: styleModal.zIndex,
            ecran: window.innerHeight,
            fermerBas: Math.round(fermer.getBoundingClientRect().bottom),
            defile: liste.scrollHeight > liste.clientHeight + 2,
            lignes: items.length,
            hauteurMin: items.length
              ? Math.round(Math.min.apply(null, items.map(
                  li => li.getBoundingClientRect().height))) : 0,
            fond: getComputedStyle(liste).backgroundColor,
            actuelle: liste.querySelectorAll('[data-actuelle]').length,
            nomPx: Math.round(parseFloat(getComputedStyle(
              liste.querySelector('.voix-liste-nom')).fontSize)),
            ecoutePx: Math.round(liste.querySelector('.voix-liste-ecoute')
              .getBoundingClientRect().width),
            hauteurListe: Math.round(liste.getBoundingClientRect().height),
            // Les pastilles de filtre (24/09/2026) doivent tenir sur UN SEUL rang
            // qui defile : deux rangs mangeraient la place de la liste.
            ageDefile: (() => {
              const e = document.getElementById('cast-voix-age-actions');
              return e.scrollWidth > e.clientWidth + 2;
            })(),
            recap: (document.getElementById('cast-voix-recap') || {}).textContent,
          };
        }""")
        print("    fenetre .............. %s x %s px (ecran de %s px de haut)"
              % (mesure["largeur"], mesure["hauteur"], mesure["ecran"]))
        print("    liste ................ %s px de large, %s lignes, defile : %s"
              % (mesure["largeurListe"], mesure["lignes"], mesure["defile"]))
        print("    une voix ............. %s px de haut, texte %s px, ▶ %s px"
              % (mesure["hauteurMin"], mesure["nomPx"], mesure["ecoutePx"]))
        print("    filtres .............. liste %s px de haut, compte : « %s »"
              % (mesure["hauteurListe"], mesure["recap"]))
        # 1) C'est une VRAIE fenetre (overlay plein ecran), plus un encart glisse
        #    dans la ligne : c'est toute la demande de Laurent.
        verifier("la liste s'ouvre dans une VRAIE fenetre (overlay fixe)",
                 mesure["position"] == "fixed" and mesure["zIndex"] == "300",
                 "%s / z-index %s" % (mesure["position"], mesure["zIndex"]))
        # 2) La demande, precisement : « qui prend plus de place sur l'ecran ».
        if nom == "telephone":
            verifier("sur telephone, la fenetre prend toute la largeur de l'ecran",
                     mesure["largeur"] >= largeur - 20,
                     "%s px pour un ecran de %s px" % (mesure["largeur"], largeur))
        else:
            verifier("sur ordinateur, la fenetre est plus large que celle du casting",
                     mesure["largeur"] > mesure["largeurCasting"],
                     "%s px contre %s px"
                     % (mesure["largeur"], mesure["largeurCasting"]))
        # 3) La liste occupe cette largeur (elle ne reste pas etroite au milieu)
        verifier("la liste occupe toute la largeur offerte",
                 mesure["largeurListe"] >= mesure["largeur"] - 38,
                 "%s px pour %s px de fenetre"
                 % (mesure["largeurListe"], mesure["largeur"]))
        # 4) Les vingt voix sont atteignables, et le bouton « Fermer » reste DANS
        #    l'ecran (c'est ce que `min-height: 0` garantit sur une longue liste).
        verifier("les vingt voix sont atteignables (la liste defile)",
                 mesure["defile"], mesure["lignes"])
        verifier("le bouton « Fermer » reste dans l'ecran",
                 mesure["fermerBas"] <= mesure["ecran"],
                 "%s px pour un ecran de %s px"
                 % (mesure["fermerBas"], mesure["ecran"]))
        # 4 bis) Les FILTRES de la liste (24/09/2026, demande de Laurent : « les
        #        boutons Femme / Homme + Tous / Enfant / Adulte / Vieux doivent
        #        trier les voix selon leur tag ») : ils ne doivent pas manger la
        #        place de la liste, et le compte doit dire ce qu'elle montre.
        verifier("la liste garde de la place sous les filtres",
                 mesure["hauteurListe"] >= 150, mesure["hauteurListe"])
        verifier("le compte des voix est annonce",
                 str(mesure["recap"]).endswith("voix"), mesure["recap"])
        if nom == "telephone":
            verifier("sur telephone, les pastilles tiennent sur UN rang qui defile",
                     mesure["ageDefile"] is True, mesure["ageDefile"])
        # 5) Les lignes sont plus aerees que dans l'ancien encart (240 px de haut,
        #    quatre ou cinq voix visibles sur un telephone).
        verifier("chaque voix se lit sur 52 px au moins (avant : une quarantaine)",
                 mesure["hauteurMin"] >= 52, mesure["hauteurMin"])
        verifier("le texte est un cran plus grand (0,9 rem)", mesure["nomPx"] >= 14,
                 mesure["nomPx"])
        verifier("le bouton d'ecoute a grossi (40 px, le doigt le vise)",
                 mesure["ecoutePx"] >= 40, mesure["ecoutePx"])
        # 6) L'apparence reste celle de l'application, et la voix portee par le
        #    personnage reste marquee (comme la valeur du menu deroulant d'origine).
        verifier("le fond de la liste est celui du theme, pas du blanc",
                 mesure["fond"] == "rgb(13, 13, 13)", mesure["fond"])
        verifier("la voix portee par le personnage est toujours marquee",
                 mesure["actuelle"] == 1, mesure["actuelle"])
        page.close()
    navigateur.close()

print("")
print("TOUT EST OK" if ECHE == 0 else "%s VERIFICATION(S) EN ECHEC" % ECHE)
sys.exit(0 if ECHE == 0 else 1)
