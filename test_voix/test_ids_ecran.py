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
partages de voix et la ligne d'usage du panneau « Voir la voix ».
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
                     '_sauverAnnotationVoix', '_familleDeVoix'):
        verifier('fonction %s' % fonction,
                 ('function %s' % fonction) in js)

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
