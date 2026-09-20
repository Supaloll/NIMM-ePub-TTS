# -*- coding: utf-8 -*-
"""Verification de la coherence entre l'ecran et le code (frontend).

A lancer avec le Python du LECTEUR :
    python test_voix/test_ids_ecran.py

Pourquoi ce test (session du 14/09/2026, fenetre « Ecouter les voix ») :
un `getElementById('xxx')` qui ne trouve pas son element dans la page fait
planter TOUT le script au chargement -- et l'ecran reste mort, sans message
clair. C'est l'erreur la plus facile a commettre en ajoutant une fenetre, et
la plus penible a diagnostiquer. On la verifie donc ici, sans navigateur.

Le test controle aussi que les fonctions du listener et sa phrase d'ecoute
sont bien presentes : si quelqu'un renomme une fonction, on le sait tout de
suite au lieu de le decouvrir a l'usage. Il verifie enfin, depuis le
15/09/2026, les deux barres de filtre de la fenetre du casting (genre des
voix proposees / etat des personnages) et les badges d'etat. Depuis le
19/09/2026, il verifie aussi le tiroir des VOIX LIBRES, le depliage des
partages de voix et la ligne d'usage du panneau « Voir la voix ». Depuis le
20/09/2026, la barre de RECHERCHE du casting (champ, compteur, fonctions de
filtrage et remise a zero a la fermeture) et les SYMBOLES DE GENRE (homme /
femme) dans les libelles et la ligne de personnage.
"""

import os
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

APP_JS = RACINE / "frontend" / "app.js"
INDEX_HTML = RACINE / "frontend" / "index.html"
STYLES_CSS = RACINE / "frontend" / "styles.css"

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def main():
    js = APP_JS.read_text(encoding='utf-8')
    html = INDEX_HTML.read_text(encoding='utf-8')

    print('')
    print('1) chaque element recherche par le code existe dans la page')
    ids_js = set(re.findall(r"getElementById\('([^']+)'\)", js))
    ids_html = set(re.findall(r'id="([^"]+)"', html))
    manquants = sorted(i for i in ids_js if i not in ids_html)
    print('   %d identifiants cherches par app.js, %d presents dans la page'
          % (len(ids_js), len(ids_html)))
    verifier('aucun identifiant manquant', not manquants, manquants)

    print('')
    print('2) la fenetre « Ecouter les voix » est complete')
    for identifiant in ('voices-modal', 'voices-open-btn', 'voices-close-btn',
                        'voices-search', 'voices-famille', 'voices-list',
                        'voices-recap'):
        verifier('element #%s present dans la page' % identifiant,
                 identifiant in ids_html)

    print('')
    print('3) les fonctions du listener existent dans app.js')
    for fonction in ('_ouvrirEcouteurVoix', '_fermerEcouteurVoix',
                     '_rafraichirEcouteurVoix', '_construireLigneVoix',
                     '_ecouterVoix', '_chargerAnnotationsVoix',
                     '_sauverAnnotationVoix', '_familleDeVoix',
                     '_libelleCourtCritere'):
        verifier('fonction %s' % fonction,
                 ('function %s' % fonction) in js)

    print('')
    print('3 bis) les RUBRIQUES des criteres sont ECRITES devant leurs menus')
    # Item du BACKLOG du 19/09/2026 (demande de Laurent) : « une fois une valeur
    # choisie, la ligne affiche "adulte" ou "aigu" sans dire de quelle rubrique
    # il s'agit ». Le nom de la rubrique est donc ecrit une fois pour toutes
    # devant son menu, et l'option vide affiche un tiret -- comme les menus
    # « genre » et « etoiles » (avant, c'etait elle qui portait le nom, donc il
    # disparaissait des le premier choix).
    verifier('etiquette creee dans la ligne de voix',
             "etiquette.className = 'voice-critere-label';" in js)
    verifier('etiquette et son menu dans le MEME groupe',
             "champ.className = 'voice-critere-champ';" in js
             and 'champ.appendChild(etiquette);' in js
             and 'champ.appendChild(sel);' in js)
    verifier('l option vide du menu est le tiret',
             "const options = [['', '\\u2013']];" in js)
    styles_listener = STYLES_CSS.read_text(encoding='utf-8')
    for classe in ('.voice-critere-label', '.voice-critere-champ'):
        verifier('style %s declare' % classe, classe in styles_listener)

    print('')
    print('3 ter) les ICONES des moteurs (20/09/2026)')
    # Demande de Laurent : « trouver des icones pour les moteurs, histoire
    # d'avoir un visuel sur les moteurs plutot que les noms ». UNE seule table
    # (`FAMILLES_VOIX`, app.js) : le libelle d'une voix montre l'icone SEULE
    # (le nom y prenait la moitie de la ligne) ; les endroits ou il y a la place
    # -- fenetre d'ecoute, tiroir, filtre, bouton des moteurs -- gardent le nom
    # precede de l'icone.
    for icone in ('\\u2601\\uFE0F', '\\uD83C\\uDF8E', '\\uD83C\\uDFB6',
                  '\\u26A1\\uFE0F', '\\uD83E\\uDDEC', '\\uD83E\\uDDEA'):
        verifier('icone %s declaree dans app.js' % icone,
                 "'" + icone + "'" in js)
    verifier('le libelle d une voix montre l icone (et plus le nom)',
             'const iconeMoteur = (typeof _iconeFamille' in js
             and 'const moteur = iconeMoteur ?' in js)
    verifier('les deux fonctions d icone existent',
             'function _iconeFamille' in js
             and 'function _libelleFamilleIcone' in js)
    verifier('le bouton des moteurs porte l icone',
             'const avecIcone = (prefixe, nom) =>' in js)
    verifier('le filtre des moteurs affiche les icones dans la page',
             '&#x1F38E; Kokoro' in html and '&#x1F9EA; NeuTTS' in html)
    verifier('NeuTTS est enfin filtrable (il manquait dans la liste)',
             '<option value="neutts">' in html)

    print('')
    print('3 quater) les trois boutons du lecteur ont la meme echelle')
    # Constat de Laurent (20/09/2026) : « 🔖 Onglets » n'etait pas dans la regle
    # de style commune -- il gardait l'apparence native du navigateur (plus
    # grand, fond plus clair) a cote de « Voix multiples » et « Ecouter les
    # voix ». Les trois partagent maintenant la MEME regle.
    styles_lecteur = STYLES_CSS.read_text(encoding='utf-8')
    styles_normalises = ' '.join(styles_lecteur.split())
    verifier('« Onglets » partage la regle des deux autres boutons',
             '#multivoice-btn, #voices-open-btn, #bookmarks-open-btn'
             in styles_normalises)

    print('')
    print('3 quinquies) barre de navigation et boutons du lecteur (20/09/2026)')
    # Demande de Laurent, 20/09/2026 : QUATRE fleches symetriques (les chapitres
    # aux extremites, les phrases au milieu), toutes de la MEME famille visuelle
    # (marron fonce, fleches blanches) ; le mode RSVP sort de la barre de
    # navigation (c'est un MODE, pas une fleche) ; et un bouton « Vider le
    # cache » rejoint la ligne des boutons d'action.
    for identifiant in ('prev-btn', 'para-prev-btn', 'sent-prev-btn', 'sent-next-btn',
                        'para-next-btn', 'next-btn', 'cache-open-btn', 'rsvp-open-btn'):
        verifier('bouton #%s present dans la page' % identifiant,
                 identifiant in ids_html)
    # TROIS niveaux de saut (20/09/2026, idee de Laurent) : les chapitres aux
    # extremites, le saut MOYEN (plusieurs paragraphes) au milieu, et la PHRASE
    # au plus pres du bouton de lecture. Le pas moyen est LU dans app.js.
    verifier('les fleches ◀ / ▶ sont branchees sur la PHRASE',
             "'sent-prev-btn').addEventListener('click', _cursorSentPrev)" in js
             and "'sent-next-btn').addEventListener('click', _cursorSentNext)" in js)
    verifier('les fleches ⏪ / ⏩ sautent PLUSIEURS paragraphes',
             '_cursorParaPrev(_PAS_PARAGRAPHES)' in js
             and '_cursorParaNext(_PAS_PARAGRAPHES)' in js)
    verifier('le pas du saut moyen est une constante (ajustable en une ligne)',
             'const _PAS_PARAGRAPHES' in js)
    styles_barre = ' '.join(STYLES_CSS.read_text(encoding='utf-8').split())
    verifier('les six fleches partagent la meme regle de style',
             '#prev-btn, #next-btn,' in styles_barre
             and '#sent-prev-btn, #sent-next-btn {' in styles_barre)
    verifier('la barre se resserre sur telephone (6 boutons + lecture)',
             '@media (max-width: 640px)' in styles_barre
             and '@media (max-width: 380px)' in styles_barre)
    verifier('l ancien conteneur #tts-nav a disparu (aucune regle orpheline)',
             'tts-nav' not in styles_barre and 'tts-nav' not in ids_html)
    # Le mode RSVP doit etre dans la rangee des boutons d'action, donc APRES
    # #reader-settings dans la page -- et non dans la barre de navigation.
    verifier('le mode RSVP a quitte la barre de navigation',
             html.index('id="reader-settings"') < html.index('id="rsvp-open-btn"'))
    styles_nav = ' '.join(STYLES_CSS.read_text(encoding='utf-8').split())
    verifier('les SIX fleches partagent la meme regle de style (marron / blanc)',
             '#para-prev-btn, #para-next-btn' in styles_nav
             and '#sent-prev-btn, #sent-next-btn' in styles_nav
             and 'var(--nav-btn)' in styles_nav)
    verifier('le bouton du cache et le RSVP partagent le style des boutons d action',
             '#rsvp-open-btn, #cache-open-btn' in styles_nav)
    for route in ('/api/cache_audio', '/api/cache_audio/vider'):
        verifier('route %s appelee par la page' % route, route in js)

    print('')
    print('3 sexies) lecteur integre et lecteur systeme (20/09/2026)')
    # Demandes de Laurent : « la lecture s'arrete si je verrouille le telephone »
    # et « une petite modale qui ressemblerait a la lecture de Deezer ». Le
    # lecteur s'ouvre par la BARRE DE PROGRESSION, et ses sept boutons sont des
    # TELECOMMANDES de la barre du bas (aucune logique de navigation en double).
    for identifiant in ('lecteur-modal', 'lecteur-close-btn', 'lecteur-couverture',
                        'lecteur-titre', 'lecteur-chapitre', 'lecteur-qui',
                        'lecteur-phrase', 'lecteur-barre-fill', 'lecteur-compteur',
                        'lecteur-boutons', 'tts-progress-ouvrir'):
        verifier('element #%s present dans la page' % identifiant,
                 identifiant in ids_html)
    for fonction in ('_ouvrirLecteur', '_fermerLecteur', '_majLecteurIntegre',
                     '_majLecteurEtat', '_majPositionMediaSession',
                     '_urlCouvertureLivre'):
        verifier('fonction %s' % fonction, ('function %s' % fonction) in js)
    verifier('la barre de progression ouvre le lecteur',
             '_ouvrirLecteur);' in js and 'tts-progress-row' in js)
    verifier('la RESERVE « a bloc » existe (arriere-plan pendant une lecture)',
             'PREFETCH_MAX_AHEAD_CHARS_BURST' in js
             and "document.addEventListener('visibilitychange'" in js)
    verifier('la couverture et la progression habillent le lecteur systeme',
             'artwork: couverture' in js and 'setPositionState' in js)
    styles_lecteur = ' '.join(STYLES_CSS.read_text(encoding='utf-8').split())
    for classe in ('#lecteur-modal', '#lecteur-inner', '#lecteur-boutons',
                   '#lecteur-barre-fill', '#tts-progress-ouvrir'):
        verifier('style %s declare' % classe, classe in styles_lecteur)

    print('')
    print('4) la phrase d\'ecoute est bien definie (une seule, pour toutes)')
    verifier('constante PHRASE_ECOUTE presente', 'const PHRASE_ECOUTE' in js)
    verifier('phrase non vide',
             re.search(r"const PHRASE_ECOUTE\s*=\s*'[^']{20,}", js) is not None)

    print('')
    print('5) le code se connecte bien aux routes du serveur')
    for route in ('/api/annotations_voix', '/api/tts', '/api/voix_catalogue',
                  '/api/voices'):
        verifier('route %s appelee par le code' % route, route in js)

    print('')
    print('6) les barres de filtre du casting existent dans la page')
    # Les deux barres se ressemblent mais ne font pas la meme chose : celle du
    # genre filtre les voix proposees dans les menus, celle d'etat filtre les
    # lignes de personnages (15/09/2026).
    for identifiant in ('cast-gender-bar', 'cast-gender-actions',
                        'cast-etat-bar', 'cast-etat-actions',
                        'cast-etat-resume', 'cast-list'):
        verifier('element #%s present dans la page' % identifiant,
                 identifiant in ids_html)
    for etat in ('T', 'caster', 'partagee', 'libres'):
        verifier('bouton data-etat="%s" present' % etat,
                 ('data-etat="%s"' % etat) in html)
    verifier('seuil des petits roles declare dans app.js',
             '_CAST_MINOR_THRESHOLD' in js)
    verifier('badges d\'etat declares dans styles.css',
             all(classe in STYLES_CSS.read_text(encoding='utf-8')
                 for classe in ('.cast-badge-caster', '.cast-badge-partagee')))

    print('')
    print('6 bis) voix libres et partages de voix (19/09/2026)')
    # Demande de Laurent : voir QUELLE voix est libre dans la fenetre du casting
    # et savoir PAR QUEL personnage une voix est partagee. Le panneau « Voir la
    # voix » doit aussi ECRIRE l'etat de la voix choisie : sur mobile il n'y a ni
    # survol ni appui long, donc rien ne doit dependre d'un `title`.
    verifier('element #cast-libres-info present dans la page',
             'cast-libres-info' in ids_html)
    verifier('element #voice-phrase-usage present dans la page',
             'voice-phrase-usage' in ids_html)
    for fonction in ('_etatVoix', '_lignesPersonnages', '_afficherVoixLibres',
                     '_detailPartageVoix', '_previewVoixLibre',
                     '_majInfoVoixLibres', '_etatVoixLivre',
                     '_rafraichirCastingApresChangement', '_allerAuPersonnage'):
        verifier('fonction %s' % fonction,
                 ('function %s' % fonction) in js)
    styles = STYLES_CSS.read_text(encoding='utf-8')
    for classe in ('.cast-group', '.cast-partage-detail', '.cast-voix-libre',
                   '#cast-libres-info', '.cast-badge-narrateur',
                   '.cast-partage-chip', '.cast-row-survol'):
        verifier('style %s declare' % classe, classe in styles)

    print('')
    print('6 ter) modale « Partager / Deplacer » (19/09/2026)')
    # Choisir une voix deja portee par un autre personnage n'est plus un
    # accident silencieux : la fenetre demande, et dit ce que chaque choix fait.
    for identifiant in ('partage-modal', 'partage-modal-header', 'partage-texte',
                        'partage-note', 'partage-partager-btn',
                        'partage-deplacer-btn', 'partage-annuler-btn',
                        'partage-close-btn'):
        verifier('element #%s present dans la page' % identifiant,
                 identifiant in ids_html)
    for fonction in ('_pitchPartageLibre', '_demanderPartage',
                     '_deplacerAutresVersGenerique'):
        verifier('fonction %s' % fonction,
                 ('function %s' % fonction) in js)
    verifier('bouton « Partager » mis en avant dans styles.css',
             '#partage-partager-btn' in styles)

    print('')
    print('6 quater) « Prendre une voix libre » depuis une fiche (19/09/2026)')
    # Second morceau : on part du personnage qu'on caste (il a un bouton 🔓),
    # pas du tiroir -- sinon il faudrait le retrouver parmi 175.
    for identifiant in ('voixlibres-modal', 'voixlibres-modal-header',
                        'voixlibres-titre', 'voixlibres-note',
                        'voixlibres-list', 'voixlibres-close-btn',
                        'voixlibres-annuler-btn'):
        verifier('element #%s present dans la page' % identifiant,
                 identifiant in ids_html)
    for fonction in ('_ouvrirVoixLibres', '_fermerVoixLibres',
                     '_donnerVoixLibre'):
        verifier('fonction %s' % fonction,
                 ('function %s' % fonction) in js)
    for classe in ('.cast-libre-btn', '.cast-voix-libre-actions',
                   '.cast-voix-libre-choisir', '#voixlibres-list'):
        verifier('style %s declare' % classe, classe in styles)

    print('')
    print('3 septies) installer l application (20/09/2026)')
    # Demande de Laurent : Chrome ne lui proposait pas « Installer », et rien ne
    # disait pourquoi. Le bouton de la bibliotheque declenche l'installation
    # quand le navigateur sait la faire, et EXPLIQUE ou chercher sinon ; il
    # disparait quand l'application est deja installee.
    verifier('element #installer-btn present dans la page',
             'installer-btn' in ids_html)
    verifier('element #installer-note present dans la page',
             'installer-note' in ids_html)
    verifier('le bouton est branche',
             "getElementById('installer-btn').addEventListener" in js)
    verifier('le navigateur est ecoute (beforeinstallprompt)',
             "'beforeinstallprompt'" in js and 'e.preventDefault()' in js)
    verifier('une installation reussie est reconnue (appinstalled)',
             "'appinstalled'" in js)
    verifier('une application deja installee masque le bouton',
             '(display-mode: standalone)' in js)
    verifier('sans proposition du navigateur, on dit OU chercher',
             'ouvre son menu' in js)
    styles_inst = ' '.join(STYLES_CSS.read_text(encoding='utf-8').split())
    verifier('styles #installer-btn et #installer-note declares',
             '#installer-btn' in styles_inst and '#installer-note' in styles_inst)

    print('')
    print('6 quinquies) barre de recherche du casting (20/09/2026)')
    # Item du BACKLOG du 14/09/2026 : sur un livre a 176 personnages, on ne
    # retrouve plus un nom a la main. Le champ filtre les lignes PENDANT la
    # frappe. Dans le tiroir des voix libres, la liste ne montre plus des
    # personnages mais des VOIX : la meme barre cherche alors leur prenom,
    # sinon elle aurait l'air morte dans cet onglet.
    for identifiant in ('cast-search-bar', 'cast-search', 'cast-search-resume'):
        verifier('element #%s present dans la page' % identifiant,
                 identifiant in ids_html)
    for fonction in ('_cleRecherche', '_filtrerPersonnages',
                     '_filtrerVoixLibres'):
        verifier('fonction %s' % fonction,
                 ('function %s' % fonction) in js)
    verifier('la frappe est branchee sur la liste du casting',
             "document.getElementById('cast-search')" in js
             and '_openCastModal(false, true)' in js)
    verifier('la recherche survit a une reconstruction de l affichage',
             'const recherche      = _castRecherche.trim();' in js)
    verifier('elle est remise a zero a la fermeture de la fenetre',
             "_castRecherche = '';" in js)
    verifier('style #cast-search declare', '#cast-search' in styles)

    print('')
    print('6 sexies) symboles du genre, homme / femme (item du BACKLOG du 19/09/2026)')
    # Demande de Laurent : « on laisse le prenom, mais on ajoute les symboles,
    # ca sera plus simple a l'oeil ». Deux pieges verifies ici, parce qu'ils ne
    # se voient qu'a l'usage :
    #   - le symbole doit porter son SELECTEUR EMOJI, sinon il sort en petit
    #     noir et blanc sur beaucoup de claviers (on cherche donc la sequence
    #     \u2640\uFE0F, et pas le seul caractere \u2640) ;
    #   - un genre INCONNU ne doit PAS tomber sur « Homme » : l'ancien code le
    #     faisait (tout ce qui n'etait pas 'F' devenait 'Homme'), donc pouvait
    #     annoncer un genre faux. Le libelle n'ecrit alors ni signe ni mot.
    for symbole in ('\\u2640\\uFE0F', '\\u2642\\uFE0F'):
        verifier('symbole %s ecrit avec son selecteur emoji (app.js)' % symbole,
                 symbole in js)
    for entite in ('&#x2640;&#xFE0F; Femmes', '&#x2642;&#xFE0F; Hommes'):
        verifier('bouton de filtre « %s » dans la page' % entite, entite in html)
    verifier('les libelles de voix portent le symbole (fonction pure)',
             'function _symboleGenre' in js
             and 'const symbole = _symboleGenre(v.gender);' in js)
    verifier('la ligne de personnage porte le symbole',
             'const symboleGenre = _symboleGenre(v.genre);' in js)
    verifier('un genre inconnu n est plus annonce « Homme » par defaut',
             "(v.genre === 'F') ? 'Femme' : (v.genre ? 'Homme' : '')" in js
             and "v.genre === 'F' ? 'Femme' : 'Homme'" not in js)

    print('')
    print('7) un changement de voix relance la lecture en cours')
    # Pourquoi (constat de Laurent, 15/09/2026) : la playlist de lecture fige la
    # voix de chaque phrase ; sans relance, la suite du chapitre continuait avec
    # les anciennes voix et il fallait fermer/rouvrir l'application (surtout sur
    # mobile). Si quelqu'un retire appel a _startTTS, on le sait ici.
    debut = js.index('async function _updateCharacterVoice')
    corps = js[debut:js.index('\n}', debut)]
    verifier('la fonction existe', True)
    verifier('elle relance la lecture (_startTTS)', '_startTTS()' in corps)
    verifier('elle arrete d abord la lecture en cours (_stopTTS)',
             '_stopTTS()' in corps)

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : coherence ecran <-> code (frontend)')
    print('=' * 66)
    sys.exit(main())
