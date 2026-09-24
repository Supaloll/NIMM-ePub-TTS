# -*- coding: utf-8 -*-
"""Verifie les FAITS de ARCHITECTURE.md contre le code (LECTURE SEULE).

POURQUOI CET OUTIL (question de Laurent, 22/09/2026) : « Est-ce que ce qui est
ecrit dans ce document reflete reellement l'etat du code. C'est un point
capital. » Question capitale, en effet -- et l'audit `_auditer_documentation.py`
n'y repond PAS : il verifie les NOMS (le fichier cite existe, la fonction citee
existe, la route citee existe, la colonne citee existe), il ne verifie JAMAIS
si la PHRASE DIT VRAI. Un document peut citer 100 % de noms justes et raconter
n'importe quoi.

Ce que cet outil verifie, lui -- les PHRASES verifiables :
  1. le PLAN DU DOSSIER ecrit en tete du document : chaque entree citee
     existe-t-elle encore a cet endroit ?
  2. ce qui existe dans le projet mais n'est PAS dans le plan ;
  3. les CONSTANTES citees avec une valeur (`MINOR_THRESHOLD` = 8...) ;
  4. les PORTS des moteurs (8081 a 8085) ;
  5. les FICHIERS DE DONNEES cites (config.json, moteur_voix.txt...) ;
  6. la VERSION de cache (`?v=`) des fichiers de la page.

Et, pour le chantier de l'etape 3 (un bloc « Aujourd'hui » en tete de chaque
sujet), le SUJET lui-meme : « modules/tts.py » annonce-t-il les bons moteurs et
les bons nombres de voix, ou bien le tableau d'hier (section 9) ? Meme question
pour la PAGE, sujet « frontend/ — Interface » (section 10) : combien de vues
porte-t-elle, et le document dit-il le bon nombre ? Et pour le MOTEUR Pocket TTS
(section 11), dont le document annoncait le mauvais nombre de parametres : ses
voix ont-elles vraiment leur fichier, et ses constantes sont-elles celles du
service ?

La section 12 tient les faits du report des notes d'ecoute, et la section 13
ceux du CASTING : quatre moteurs -- dont le MODELE LOCAL (Ollama), oublie du
document pendant dix jours --, le moteur par defaut, le repli automatique, les
routes, les huit colonnes de la table `voices` et le chemin de la voix a la
lecture.

La section 14 tient ceux des SYMBOLES DE GENRE et de leurs voisins du meme
sujet : la fonction des symboles et ses deux conventions (M / H), les trois
emplacements, le libelle exact d'une voix (les drapeaux, jamais le pays ecrit),
la table des icones de moteurs -- SEPT depuis Pocket, la ou le tableau du
document s'arretait a six -- et la regle de style commune des boutons de la
barre du lecteur, qui en porte six elle aussi.

La section 15 tient ceux du LECTEUR et de l'ECRAN VERROUILLE : les quatre
constantes du prechargement avec leur valeur, le declencheur de la reserve
« a bloc », les HUIT actions du lecteur du systeme, les SEPT telecommandes du
lecteur integre, le collage des phrases et son filet, et la pause venue de
l'exterieur. Elle compte aussi les CONTROLES des tests cites en les LANCANT
(les sections 12 et 14 comptent les `verifier(` ecrits : juste pour un test
sans boucle, faux des qu'une boucle parcourt une liste).

La section 16 tient ceux du ROGNAGE DES SILENCES DE BORD : les marges REELLES du
filtre d'Edge (`modules/audio_trim.py` : -45 dB, 0,08 s en tete, 0,35 s en
queue), le rognage de queue des services XTTS et NeuTTS, la respiration de
Kyutai (0 par defaut), ce que Pocket fait a la place, la cle du cache (c'est la
VERSION qui l'invalide, pas le rognage) et les quatre tests cites -- comptes en
les lancant eux aussi.

Chaque fait est ECRIT ICI, en clair, avec la facon de le verifier : pas de
devinette, pas d'heuristique qui crie au loup. Un fait est OK, ou c'est un
ECART -- et un ecart est a LIRE : il peut etre legitime (une phrase datee qui
raconte une decision d'hier) ou une vraie derive.

Usage : python _verifier_faits_architecture.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent
DOC = RACINE / 'ARCHITECTURE.md'

ECARTS = []


def lire(chemin):
    """Le texte d'un fichier, ou une chaine vide s'il n'existe pas."""
    try:
        return chemin.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def fait(intitule, vrai, constat, ligne_doc=''):
    """Consigne un fait verifie : OK, ou ECART a lire."""
    if vrai:
        print('  OK    %s' % intitule)
    else:
        print('  ECART %s' % intitule)
        print('        %s' % constat)
        if ligne_doc:
            print('        dans le document : %s' % ligne_doc)
        ECARTS.append(intitule)


def bloc_plan(lignes):
    """Le bloc ``` du « Structure du dossier », et sa ligne de depart.

    Le titre peut etre `##` (document a plat) ou `###` (document regroupe en
    parties) : on le designe par sa FIN, jamais par son niveau.
    """
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('#') and l.rstrip().endswith(
                       'Structure du dossier')), None)
    if depart is None:
        return [], 0
    debut = next((n for n in range(depart, len(lignes))
                  if lignes[n].startswith('```')), None)
    fin = next((n for n in range(debut + 1, len(lignes))
                if lignes[n].startswith('```')), None)
    return lignes[debut + 1:fin], debut + 2


def entrees_du_plan(bloc):
    """[(index, chemin)] : reconstruit l'arbre du plan par l'indentation."""
    sortie, pile = [], {}
    for i, ligne in enumerate(bloc):
        m = re.match(r'^([\s│]*)(?:├──|└──)\s+(.*)$', ligne)
        if not m:
            continue
        profondeur = len(m.group(1)) // 4
        nom = re.split(r'\s{2,}|\s+—\s+', m.group(2))[0].strip()
        pile[profondeur] = nom
        chemin = '/'.join(pile[d] for d in sorted(pile) if d <= profondeur)
        sortie.append((i, chemin.rstrip('/')))
    return sortie


def check_plan_du_dossier():
    """1 et 2. Le plan du dossier dit-il ce qui existe vraiment ?"""
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    bloc, depart = bloc_plan(lignes)
    entrees = entrees_du_plan(bloc)

    absents = [(depart + i, c) for i, c in entrees
               if not (RACINE / c).exists()]
    if absents:
        for numero, chemin in absents:
            fait('le plan cite %s' % chemin, False,
                 'cette entree n existe plus a cet endroit',
                 'ligne %d' % numero)
    else:
        fait('toutes les entrees du plan existent (%d)' % len(entrees), True, '')

    # Ce qui existe et n'est PAS dans le plan (seule la presence est comparee).
    cites = {c.split('/')[0] for _i, c in entrees}
    reels = {d.name for d in RACINE.iterdir()
             if d.is_dir() and not d.name.startswith(('.', '_'))}
    oublies = sorted(reels - cites)
    fait('aucun dossier du projet n est oublie par le plan', not oublies,
         'absents du plan : %s' % ', '.join(oublies) if oublies else '')

    modules_plan = {c.split('/')[-1] for _i, c in entrees
                    if c.startswith('modules/')}
    modules_reels = {f.name for f in (RACINE / 'modules').glob('*.py')}
    oublies_m = sorted(modules_reels - modules_plan)
    fait('aucun module de modules/ n est oublie par le plan', not oublies_m,
         'absents du plan : %s' % ', '.join(oublies_m) if oublies_m else '')


def check_moteurs_de_tts():
    """3. Le plan decrit-il les moteurs que porte vraiment modules/tts.py ?"""
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    bloc, depart = bloc_plan(lignes)
    # La ligne du PLAN qui parle de tts.py (pas celle du sommaire).
    numero = next((depart + i for i, l in enumerate(bloc)
                   if 'tts.py' in l), None)
    decrits = (lignes[numero - 1].upper() if numero else '')
    tts = lire(RACINE / 'modules' / 'tts.py')
    catalogues = set(re.findall(r'(?m)^([A-Z]+)_VOICES = \[', tts))
    familles = {'EDGE', 'KOKORO', 'PIPER', 'KYUTAI', 'XTTS', 'NEUTTS', 'POCKET'}
    reels = sorted((catalogues | {'EDGE'}) & familles)
    manquants = [f for f in reels if f not in decrits]
    fait('le plan decrit tous les moteurs portes par tts.py', not manquants,
         'catalogues trouves dans modules/tts.py : %s\n'
         '        la ligne du plan n en cite que : %s'
         % (', '.join(reels),
            (lignes[numero - 1].split('—')[-1].strip() if numero else 'aucun')),
         'ligne %d' % numero if numero else '')


def _valeur(motif, texte):
    m = re.search(motif, texte)
    return m.group(1).strip() if m else None


def check_constantes():
    """4. Les constantes citees en clair dans le document."""
    doc = DOC.read_text(encoding='utf-8')
    casting = lire(RACINE / 'modules' / 'voice_casting.py')
    page = lire(RACINE / 'frontend' / 'app.js')

    # MINOR_THRESHOLD : le document l ecrit « moins de `MINOR_THRESHOLD` = 8 ».
    doc_seuil = _valeur(r'MINOR_THRESHOLD`?\s*=\s*(\d+)', doc)
    code_seuil = _valeur(r'(?m)^MINOR_THRESHOLD = (\d+)', casting)
    fait('MINOR_THRESHOLD : le document et le code disent le meme nombre',
         doc_seuil is not None and doc_seuil == code_seuil,
         'document : %s / modules/voice_casting.py : %s'
         % (doc_seuil, code_seuil))

    page_seuil = _valeur(r'_CAST_MINOR_THRESHOLD = (\d+)', page)
    fait('le seuil des petits roles est le meme cote page et cote serveur',
         page_seuil == code_seuil,
         'frontend/app.js : %s / voice_casting.py : %s'
         % (page_seuil, code_seuil))

    doc_nar = _valeur(r"NARRATEUR_VOIX_DEFAUT\s*=\s*'([^']+)'", doc)
    code_nar = _valeur(r"NARRATEUR_VOIX_DEFAUT = '([^']+)'", page)
    fait('NARRATEUR_VOIX_DEFAUT : la voix citee est celle du code',
         doc_nar is not None and doc_nar == code_nar,
         'document : %s / frontend/app.js : %s' % (doc_nar, code_nar))

    # PERSONNAGE_RATE_DEFAUT : le document doit donner la VALEUR du code, pas
    # seulement le libelle du reglage (« Normale » est le nom du menu).
    code_rate = _valeur(r"PERSONNAGE_RATE_DEFAUT = '([^']+)'", page)
    m = re.search(r'PERSONNAGE_RATE_DEFAUT', doc)
    fenetre = doc[m.start():m.start() + 240] if m else ''
    fait('PERSONNAGE_RATE_DEFAUT : la valeur citee est celle du code',
         code_rate is not None and code_rate in fenetre,
         "frontend/app.js porte '%s' ; le document ecrit : %s"
         % (code_rate, fenetre[:130].replace('\n', ' ')))

    # PARAGRAPH_PAUSE_MS : la pause entre paragraphes. Derive REELLE, trouvee
    # par l'audit du 23/09/2026 : la page annoncait « 0 » (15/09/2026) alors que
    # le code etait REVENU a 300 le 17/09/2026 -- personne ne l'avait ecrit.
    # Comme l'etat actuel est en tete de sujet (regle du document), c'est la
    # PREMIERE mention qui fait foi.
    code_pause = _valeur(r'(?m)^const PARAGRAPH_PAUSE_MS = (\d+);', page)
    m = re.search(r'PARAGRAPH_PAUSE_MS', doc)
    fenetre = doc[m.start():m.start() + 120] if m else ''
    fait('PARAGRAPH_PAUSE_MS : la valeur citee en tete de sujet est celle du code',
         code_pause is not None and ('= %s' % code_pause) in fenetre,
         "frontend/app.js porte %s ; le document ecrit : %s"
         % (code_pause, fenetre[:100].replace('\n', ' ')))


def check_ports():
    """5. Les ports des moteurs : ceux du code doivent etre ceux du document."""
    main = lire(RACINE / 'main.py')
    doc = DOC.read_text(encoding='utf-8')
    urls = {'kyutai': r'KYUTAI_URL = "http://127\.0\.0\.1:(\d+)',
            'xtts': r'XTTS_URL = "http://127\.0\.0\.1:(\d+)',
            'neutts': r'NEUTTS_URL = "http://127\.0\.0\.1:(\d+)',
            'pocket': r'POCKET_URL = "http://127\.0\.0\.1:(\d+)'}
    for moteur, motif in urls.items():
        port = _valeur(motif, main)
        fait('le port de %s annonce par le document est celui du code' % moteur,
             port is not None and port in doc,
             'main.py dit %s et le document ne cite pas ce numero' % port)
    lecteur = _valeur(r'port=(\d+)', main)
    fait('le port du lecteur annonce par le document est celui du code',
         lecteur is not None and lecteur in doc,
         'main.py dit %s' % lecteur)


def check_donnees():
    """6. Les fichiers de donnees cites par le document existent-ils ?"""
    for chemin, quoi in (('data/config.json', 'les cles API'),
                         ('data/moteur_voix.txt', 'le moteur choisi'),
                         ('data/annotations_voix.json', 'les notes d ecoute'),
                         ('data/nimm_epub.db', 'la base')):
        fait('%s existe (%s)' % (chemin, quoi), (RACINE / chemin).is_file(),
             'le document en parle, mais le fichier est absent')


def check_version_cache():
    """7. La version de cache de la page : une seule valeur, pour tous les fichiers."""
    page = lire(RACINE / 'frontend' / 'index.html')
    versions = sorted(set(re.findall(r'\?v=([0-9a-zA-Z._-]+)', page)))
    fait('la page utilise une seule version de cache', len(versions) == 1,
         'versions trouvees dans frontend/index.html : %s' % versions)
    if versions:
        print('        (version en place aujourd hui : %s)' % versions[-1])


def check_etat_actuel():
    """8. Combien de sujets portent un bloc « Aujourd'hui » (l'etat actuel) ?

    Chantier du 22/09/2026 : chaque sujet doit a terme commencer par un bloc
    court et verifiable, la chronique datant l'histoire. Ce compte suit
    l'avancement -- ce n'est pas une alerte, c'est un thermometre.
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    sujets = [l for l in lignes if l.startswith('### ')]
    avec = [l[4:].strip() for i, l in enumerate(lignes)
            if l.startswith('### ')
            and any("**Aujourd'hui" in s for s in lignes[i + 1:i + 4])]
    print('  %d sujets ; %d commence(nt) par un bloc « Aujourd hui »'
          % (len(sujets), len(avec)))
    for titre in avec:
        print('        OK : %s' % titre[:66])
    if len(sujets) > len(avec):
        print('        reste a faire : %d sujet(s), un par session'
              % (len(sujets) - len(avec)))


def _compter_liste(texte, nom):
    """Nombre d'entrees `{"id": ...}` de la liste `nom = [` d'un fichier.

    Meme compte que `_essais/_mesurer_voix_tts.py` : le bloc part de la ligne
    `NOM = [` et va jusqu'a la premiere ligne `]` seule. Retourne None si la
    liste n'existe pas (on ne devine pas).
    """
    lignes = texte.splitlines()
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith(nom + ' = [')), None)
    if depart is None:
        return None
    fin = next((k for k in range(depart + 1, len(lignes))
                if lignes[k].startswith(']')), None)
    if fin is None:
        return None
    return sum(1 for l in lignes[depart:fin + 1] if '"id": "' in l)


def _catalogues_de_voix(tts):
    """{'KOKORO': 94, 'PIPER': 4, ...} -- les catalogues de modules/tts.py."""
    sortie = {}
    for m in re.finditer(r'(?m)^([A-Z_]+)_VOICES = \[', tts):
        sortie[m.group(1)] = _compter_liste(tts, m.group(1) + '_VOICES')
    return sortie


def check_sujet_tts():
    """9. Le sujet « modules/tts.py » dit-il ce que le module porte vraiment ?

    Chantier de l'etape 3 : en donnant a chaque sujet un bloc « Aujourd'hui »,
    on ECRIT des faits -- et un fait ecrit sans controle redevient faux tout
    seul, c'est l'histoire de `PARAGRAPH_PAUSE_MS`.

    Deux verites faciles a laisser filer, toutes deux trouvees fausses le
    23/09/2026 : le sujet annoncait QUATRE moteurs (ils sont sept depuis NeuTTS
    et Pocket, et le tableau n'en listait que cinq) et des comptes de voix
    d'avant les lots suivants (Kokoro 84 au lieu de 94, XTTS 60 au lieu de 79).
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('### ') and 'tts.py' in l), None)
    if depart is None:
        fait('le sujet qui parle de modules/tts.py existe', False,
             'aucun titre ### ne mentionne tts.py')
        return
    fin = next((n for n in range(depart + 1, len(lignes))
                if lignes[n].startswith('### ')), len(lignes))
    lignes_sujet = lignes[depart:fin]
    # On lit le TABLEAU du Role (les lignes qui commencent par « | ») : le bloc
    # « Aujourd'hui » cite lui aussi les prefixes, et le controle serait aveugle
    # s'il se contentait de chercher dans tout le sujet.
    tableau = [l for l in lignes_sujet if l.startswith('|')]

    prefixes = ['kokoro', 'piper', 'kyutai', 'xtts', 'neutts', 'pocket']
    absents = [p for p in prefixes
               if not any(('`%s:`' % p) in l for l in tableau)]
    fait('les %d moteurs a prefixe ont leur ligne dans le tableau du Role'
         % len(prefixes), not absents,
         'absents du tableau (ligne %d) : %s' % (depart + 1, ', '.join(absents)))

    # Le nombre de voix annonce sur la LIGNE du moteur (premier « N voix »).
    # La ligne Piper dit « (3 modeles, 4 voix) » : on lit donc le premier
    # nombre suivi du mot « voix », sans exiger la parenthese.
    tts = lire(RACINE / 'modules' / 'tts.py')
    catalogues = _catalogues_de_voix(tts)
    for prefixe in prefixes:
        ligne = next((l for l in tableau if ('`%s:`' % prefixe) in l), '')
        annonce = _valeur(r'(\d+)\s+voix', ligne)
        reel = catalogues.get(prefixe.upper())
        fait('%s : le nombre de voix annonce est celui du catalogue'
             % prefixe.upper(),
             annonce is not None and reel is not None and int(annonce) == reel,
             '%s_VOICES compte %s voix ; le document ecrit %s'
             % (prefixe.upper(), reel, annonce))

    # Edge est a part : sa liste vit dans main.py (FRENCH_VOICES).
    edge_doc = _valeur(r'Edge TTS \((\d+) voix\)', '\n'.join(tableau))
    edge_code = _compter_liste(lire(RACINE / 'main.py'), 'FRENCH_VOICES')
    fait('EDGE : le nombre de voix annonce est celui de FRENCH_VOICES',
         edge_doc is not None and edge_code is not None
         and int(edge_doc) == edge_code,
         'FRENCH_VOICES compte %s voix ; le document ecrit %s'
         % (edge_code, edge_doc))


def check_sujet_frontend():
    """10. Le sujet « frontend/ — Interface » dit-il ce que la page porte vraiment ?

    Meme logique que la section 9 : un fait ecrit dans un bloc « Aujourd'hui »
    redevient faux tout seul s'il n'est pas controle -- et la page est l'endroit
    ou les choses bougent le plus vite. Deux derives trouvees le 23/09/2026,
    toutes deux invisibles depuis des jours :
      - le sujet annoncait DEUX vues (bibliotheque et lecteur) alors que la page
        en porte QUATRE depuis le choix du profil (20/08/2026) et le mode RSVP ;
      - le bouton « Installer l'application » disparait aussi SUR ORDINATEUR
        (`_majBoutonInstaller` -> `_appareilMobile`), ce que le document ne disait
        pas, et ses quatre fonctions n'etaient nommees nulle part.
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('### ') and 'frontend/' in l), None)
    if depart is None:
        fait('le sujet « frontend/ — Interface » existe', False,
             'aucun titre ### ne commence par « frontend/ »')
        return
    fin = next((n for n in range(depart + 1, len(lignes))
                if lignes[n].startswith('### ')), len(lignes))
    texte = '\n'.join(lignes[depart:fin])

    page = lire(RACINE / 'frontend' / 'index.html')
    js = lire(RACINE / 'frontend' / 'app.js')

    # Les vues REELLES : les `<div id="view-...">` de la page.
    vues = sorted(set(re.findall(r'id="(view-[a-z0-9-]+)"', page)))
    basculees = [v for v in vues if ("getElementById('%s')" % v) in js]
    fait('les vues de la page sont celles que showView() bascule',
         bool(vues) and len(basculees) == len(vues),
         'declarees dans index.html : %s ; basculees dans app.js : %s'
         % (', '.join(vues), ', '.join(basculees)))

    # Le NOMBRE de vues, ecrit en toutes lettres dans le bloc « Aujourd'hui »
    # (« une seule page, quatre vues »).
    NOMBRES = {'deux': 2, 'trois': 3, 'quatre': 4, 'cinq': 5}
    annonce = _valeur(r'(?i)(deux|trois|quatre|cinq) vues', texte)
    fait('le nombre de vues annonce est celui de la page',
         annonce is not None and NOMBRES[annonce.lower()] == len(vues),
         'la page porte %d vues ; le sujet annonce « %s »'
         % (len(vues), annonce))

    # Chaque vue reelle doit etre NOMMEE dans le sujet : c'est ce qui permet de
    # tomber juste par une recherche sur son identifiant.
    oubliees = [v for v in vues if ('`%s`' % v) not in texte]
    fait('chaque vue de la page est nommee dans le sujet', not oubliees,
         'jamais nommees : %s' % ', '.join(oubliees))

    # Les constantes du chargement de chapitre citees par le bloc.
    for nom in ('CHARGEMENT_ESSAIS', 'CHARGEMENT_PAUSE_MS'):
        doc_valeur = _valeur(r'`%s`? = (\d+)' % nom, texte)
        code_valeur = _valeur(r'(?m)^const %s\s*=\s*(\d+);' % nom, js)
        fait('%s : la valeur citee est celle du code' % nom,
             doc_valeur is not None and doc_valeur == code_valeur,
             'frontend/app.js porte %s ; le sujet ecrit %s'
             % (code_valeur, doc_valeur))

    # Le bouton d'installation : ses fonctions existent dans la page, et le sujet
    # les nomme (un nom sans accents graves ne se retrouve pas par recherche).
    fonctions = ('_majBoutonInstaller', '_appareilMobile',
                 '_applicationInstallee', '_proposerInstallation')
    absentes = [f for f in fonctions if ('function %s(' % f) not in js]
    fait('les fonctions du bouton d installation existent dans la page',
         not absentes,
         'introuvables dans frontend/app.js : %s' % ', '.join(absentes))
    non_citees = [f for f in fonctions if ('`%s' % f) not in texte]
    fait('le sujet nomme les fonctions du bouton d installation', not non_citees,
         'jamais nommees dans le sujet : %s' % ', '.join(non_citees))


def _parametres_safetensors(chemin):
    """(parametres, tenseurs, octets) lus dans l'EN-TETE d'un safetensors.

    Aucun import de torch : les 8 premiers octets donnent la longueur du JSON
    d'en-tete, et chaque tenseur y annonce sa forme -- c'est la seule facon de
    compter les parametres SANS charger le modele (mesure du 23/09/2026).
    """
    import json
    import struct

    octets = chemin.stat().st_size
    with chemin.open('rb') as flux:
        taille = struct.unpack('<Q', flux.read(8))[0]
        entete = json.loads(flux.read(taille).decode('utf-8'))
    tenseurs = [v for cle, v in entete.items() if cle != '__metadata__']
    parametres = 0
    for tenseur in tenseurs:
        nombre = 1
        for dimension in tenseur.get('shape', []):
            nombre *= dimension
        parametres += nombre
    return parametres, len(tenseurs), octets


def _modele_pocket():
    """Le `model.safetensors` de `french_24l` en cache Hugging Face, ou None."""
    cache = (Path.home() / '.cache' / 'huggingface' / 'hub'
             / 'models--kyutai--pocket-tts')
    trouves = sorted(cache.rglob('languages/french_24l/model.safetensors'))
    return trouves[0] if trouves else None


def check_sujet_pocket():
    """11. Le sujet « Moteur de voix Pocket TTS » dit-il ce que le moteur fait ?

    Meme logique que les sections 9 et 10 -- avec une derive qui valait le
    detour, trouvee le 23/09/2026 : le document annoncait « 100 M de
    parametres ». C'est le chiffre des variantes LEGERES de Pocket TTS
    (`config/english.yaml` : 6 couches) ; le modele francais que NIMM ePub
    utilise, `french_24l`, en porte 336 M (24 couches) -- lu dans l'en-tete du
    fichier de poids en cache, et confirme par sa taille (641 Mo : 336 M de
    BF16, soit 2 octets par parametre).
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('### ') and 'Pocket TTS' in l), None)
    if depart is None:
        fait('le sujet « Moteur de voix Pocket TTS » existe', False,
             'aucun titre ### ne nomme Pocket TTS')
        return
    fin = next((n for n in range(depart + 1, len(lignes))
                if lignes[n].startswith('### ')), len(lignes))
    texte = '\n'.join(lignes[depart:fin])

    fait("le sujet s ouvre par un bloc « Aujourd hui »",
         "Aujourd'hui — l'état actuel en clair" in texte,
         'le bloc « Aujourd hui » manque a la ligne %d' % (depart + 1))

    tts = lire(RACINE / 'modules' / 'tts.py')
    service = lire(RACINE / 'pocket_tts_service' / 'servir_pocket_tts.py')
    lecteur = lire(RACINE / 'main.py')

    # Le catalogue : le nombre annonce, et chaque voix reellement jouable.
    annonce = _valeur(r'`POCKET_VOICES`\s*=\s*\*\*(\d+) voix', texte)
    reel = _compter_liste(tts, 'POCKET_VOICES')
    fait('POCKET_VOICES : le nombre de voix annonce est celui du catalogue',
         annonce is not None and reel is not None and int(annonce) == reel,
         'POCKET_VOICES compte %s voix ; le document ecrit %s'
         % (reel, annonce))

    identifiants = re.findall(r'(?m)^\s*\{"id": "(pocket:[^"]+)"', tts)
    dossier = RACINE / 'pocket_tts_service' / 'voix'
    injouables = [i for i in identifiants
                  if not (dossier / (i.split(':', 1)[1] + '_reference.wav')
                          ).is_file()]
    fait('chaque voix du catalogue Pocket a son fichier de reference',
         bool(identifiants) and not injouables,
         'voix sans WAV (donc injouables) : %s' % ', '.join(injouables))


    # Les valeurs lues dans le SERVICE : le document les cite en clair.
    constantes = (
        ('NIVEAU_MINI', r'`NIVEAU_MINI`\s*=\s*\*\*([\d,\.]+)\*\*',
         r'(?m)^NIVEAU_MINI = ([\d.]+)', lambda v: v.replace(',', '.')),
        ('ESSAIS_MAX', r'\*\*`ESSAIS_MAX` = (\d+)\*\*',
         r'(?m)^ESSAIS_MAX = (\d+)', lambda v: v),
        ('PORT', r'port\s*\*\*(\d+)\*\*',
         r'(?m)^PORT = int\(os\.environ\.get\("NIMM_POCKET_TTS_PORT", "(\d+)"\)',
         lambda v: v),
        ('COEURS', r'\*\*(\d+) c\u0153urs\*\*',
         r'(?m)^COEURS = int\(os\.environ\.get\("NIMM_POCKET_TTS_COEURS", "(\d+)"\)',
         lambda v: v),
        ('INACTIF_MIN', r'auto-extinction apr\S*s (\d+) min',
         r'(?m)^INACTIF_MIN = int\(os\.environ\.get\("NIMM_POCKET_TTS_INACTIF", "(\d+)"\)',
         lambda v: v),
    )
    for nom, motif_doc, motif_code, normaliser in constantes:
        valeur_doc = _valeur(motif_doc, texte)
        valeur_code = _valeur(motif_code, service)
        fait('%s : la valeur citee est celle du service' % nom,
             valeur_doc is not None and valeur_code is not None
             and normaliser(valeur_doc) == valeur_code,
             'servir_pocket_tts.py porte %s ; le sujet ecrit %s'
             % (valeur_code, valeur_doc))

    # La cohabitation : c'est elle qui tient le moteur a l'ecart de la bascule.
    fait('MOTEURS_VOIX porte bien `cohabite` pour pocket',
         re.search(r'"pocket":\s*\{[^}]*"cohabite":\s*True', lecteur)
         is not None,
         'la fiche « pocket » de MOTEURS_VOIX (main.py) n a plus cohabite: True')

    # L'ancien nom : le sujet l'ecrit « ex- », il ne doit plus etre defini.
    fait('le sujet ne cite pas un nom de fonction encore vivant',
         'def _sans_fenetre(' not in lecteur,
         'main.py definit encore _sans_fenetre, que le sujet presente comme '
         '« ex- »')

    # Le modele : le nombre de parametres, lu dans l'en-tete du fichier de poids.
    documente = _valeur(r'\*\*(\d+) M de param', texte)
    modele = _modele_pocket()
    if modele is None:
        print('  (non controle : le modele Pocket n est pas dans le cache '
              'Hugging Face de cette machine)')
    else:
        parametres, tenseurs, octets = _parametres_safetensors(modele)
        millions = round(parametres / 1e6)
        fait('le nombre de parametres annonce est celui du modele en cache',
             documente is not None and int(documente) == millions,
             'model.safetensors : %s parametres (%d tenseurs, %.0f Mo) ; '
             'le sujet ecrit %s M'
             % ('{:,}'.format(parametres).replace(',', ' '), tenseurs,
                octets / 1024 / 1024, documente))


def _nombre_apres(texte, motif, fenetre=120):
    """Le premier nombre EN GRAS qui suit un motif (« **33 controles** »).

    Sert aux chiffres ANNONCES par le document (le nombre de controles d'un
    test) : on ne devine rien, on lit le premier nombre en gras apres le nom
    cite, dans une fenetre courte.
    """
    m = re.search(motif, texte)
    if not m:
        return None
    suivant = texte[m.end():m.end() + fenetre]
    n = re.search(r'\*\*(\d+)', suivant)
    return n.group(1) if n else None


def check_sujet_notes():
    """12. Le sujet « Report des notes d ecoute » dit-il ce que le code fait ?

    Meme logique que les sections 9 a 11. Ce sujet est composite -- le report des
    notes d'ecoute (15/09/2026), les badges d'etat du casting, les voix libres
    (19/09) et la barre de recherche (20/09) -- et c'est celui qui portait la
    derive la plus discrete de l'audit : il parlait encore des « trois boutons »
    de la barre d'etat, alors que le quatrieme (« Voix libres ») est arrive le
    19/09/2026 ; `test_ids_ecran.py` verifiait, lui, les quatre. De la meme
    famille : « 175 personnages » (le livre de reference en porte 176) et une
    voix « portee par dix-huit personnages » dans « 22/11/63 » (la plus grande
    famille hors generiques en porte 3). Les chiffres du CASTING sont dates dans
    le document (ils bougent a chaque re-cast) ; les faits STABLES sont controles
    ici.
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('### ') and 'Report des notes' in l), None)
    if depart is None:
        fait('le sujet « Report des notes d ecoute » existe', False,
             'aucun titre ### ne commence par « Report des notes »')
        return
    fin = next((n for n in range(depart + 1, len(lignes))
                if lignes[n].startswith('### ')), len(lignes))
    texte = '\n'.join(lignes[depart:fin])

    fait("le sujet s ouvre par un bloc « Aujourd hui »",
         "Aujourd'hui — l'état actuel en clair" in texte,
         'le bloc « Aujourd hui » manque a la ligne %d' % (depart + 1))

    # -- Le report des notes : le fichier, l'outil, ses garde-fous. -----------
    fait('le fichier de notes des voix existe',
         (RACINE / 'data' / 'annotations_voix.json').is_file(),
         'le sujet en fait le lieu des notes, mais le fichier est absent')

    outil = lire(RACINE / 'test_voix' / '_appliquer_annotations_voix.py')
    for intitule, present in (
            ('le report est un APERCU tant que --ecrire n est pas donne',
             "ecrire_vraiment = '--ecrire' in sys.argv" in outil),
            ('la sauvegarde annoncee *.bak_avant_annotations_voix',
             '.bak_avant_annotations_voix' in outil),
            ('la conversion H -> M annoncee',
             "if g == 'H':" in outil and "return 'M'" in outil)):
        fait(intitule, present,
             'test_voix/_appliquer_annotations_voix.py ne le fait plus')

    tts = lire(RACINE / 'modules' / 'tts.py')
    lecteur = lire(RACINE / 'main.py')
    attendus = ('FRENCH_VOICES', 'KOKORO_VOICES', 'KYUTAI_VOICES',
                'XTTS_VOICES', 'NEUTTS_VOICES', 'POCKET_VOICES')
    absents = [c for c in attendus
               if not re.search(r'(?m)^%s = \[' % c, tts + lecteur)]
    fait('les six catalogues reportes existent tous', not absents,
         'catalogues introuvables : %s' % ', '.join(absents))
    fait('l outil balaie bien les deux fichiers de catalogues',
         "'main.py'" in outil and "'tts.py'" in outil,
         'les CIBLES de l outil ne portent plus main.py ET modules/tts.py')

    # -- La barre d'etat : combien de boutons, et quels seuils ? --------------
    page = lire(RACINE / 'frontend' / 'index.html')
    js = lire(RACINE / 'frontend' / 'app.js')
    serveur = lire(RACINE / 'modules' / 'voice_casting.py')
    NOMBRES = {'deux': 2, 'trois': 3, 'quatre': 4, 'cinq': 5}

    boutons = re.findall(r'data-etat="([^"]+)"', page)
    annonce = _valeur(r'(?i)(deux|trois|quatre|cinq) boutons', texte)
    fait('le nombre de boutons d etat annonce est celui de la page',
         annonce is not None and NOMBRES[annonce.lower()] == len(boutons),
         'la page porte %d boutons (%s) ; le sujet annonce « %s »'
         % (len(boutons), ', '.join(boutons), annonce))

    seuil_doc = _valeur(r'`_CAST_MINOR_THRESHOLD` = \*\*(\d+)\*\*', texte)
    seuil_page = _valeur(r'_CAST_MINOR_THRESHOLD = (\d+)', js)
    seuil_serveur = _valeur(r'(?m)^MINOR_THRESHOLD = (\d+)', serveur)
    fait('le seuil des petits roles cite est celui des deux codes',
         seuil_doc is not None and seuil_doc == seuil_page == seuil_serveur,
         'app.js : %s / voice_casting.py : %s ; le sujet ecrit %s'
         % (seuil_page, seuil_serveur, seuil_doc))
    fait('le sujet donne aussi la valeur du seuil cote serveur',
         ('`MINOR_THRESHOLD` = **%s**' % seuil_serveur) in texte
         if seuil_serveur else False,
         'voice_casting.py porte %s ; le sujet ne l ecrit pas ainsi'
         % seuil_serveur)

    # Les voix generiques : la page, le serveur et le document disent pareil.
    bloc_generiques = re.findall(r'_CAST_VOIX_GENERIQUES = \[([^\]]*)\]', js)
    generiques_page = re.findall(r"'([^']+)'", bloc_generiques[0]) \
        if bloc_generiques else []
    generiques_serveur = re.findall(r'GENERIC_VOICE_\w = "([^"]+)"', serveur)
    generiques_doc = re.findall(r'`(piper:upmc:\d+)`', texte)
    # Le sujet a le droit de citer une voix generique PLUSIEURS fois (le nombre
    # de ses porteurs, par exemple) : on compare la liste des identifiants
    # DISTINCTS, dans leur ordre de premiere apparition.
    cites = sorted(set(generiques_doc), key=generiques_doc.index)
    fait('les voix generiques citees sont celles de la page et du serveur',
         bool(cites) and cites == generiques_page == generiques_serveur,
         'app.js : %s / voice_casting.py : %s ; le sujet ecrit %s'
         % (', '.join(generiques_page), ', '.join(generiques_serveur),
            ', '.join(cites)))

    # Le plafond de noms du badge : le document cite le code, mot pour mot.
    fait('le plafond de noms du badge cite est celui du code',
         'noms.slice(0, 6)' in js and 'noms.slice(0, 6)' in texte,
         'app.js ne porte plus `noms.slice(0, 6)`, ou le sujet ne le cite plus')

    # -- Les tests cites, et le nombre de controles annonce. ------------------
    for nom in ('test_etat_casting.js', 'test_tiroir_voix_libres.js',
                'test_recherche_casting.js'):
        chemin = RACINE / 'test_voix' / nom
        if not chemin.is_file():
            fait('le test cite %s existe' % nom, False,
                 'test_voix/%s est introuvable' % nom)
            continue
        reel = len(re.findall(r'(?m)^\s*verifier\(',
                              chemin.read_text(encoding='utf-8')))
        annonce = _nombre_apres(texte, r'`test_voix/%s`' % re.escape(nom))
        fait('%s : le nombre de controles annonce est le vrai' % nom,
             annonce is not None and int(annonce) == reel,
             'le fichier compte %d controles ; le sujet annonce %s'
             % (reel, annonce))

    for nom in ('test_ids_ecran.py', 'test_annotations_voix.py',
                'test_lire_moi.py'):
        fait('le sujet cite %s, qui existe' % nom,
             (RACINE / 'test_voix' / nom).is_file(),
             'test_voix/%s est introuvable' % nom)


def check_sujet_casting():
    """13. Le sujet « Distribution de voix par personnage (IA) » dit-il ce que le
    code fait ?

    Meme logique que les sections 9 a 12. Ce sujet est celui qui avait le plus
    retarde : il annoncait « DeepSeek par defaut » (Gemini l'est depuis le
    23/08/2026), il ignorait le MOTEUR LOCAL (Ollama, 13/09/2026) -- absent de
    TOUT le document --, une seule route, une table `voices` de quatre colonnes,
    et des attributs `data-voice` / `data-pitch` qui n'existent nulle part dans
    la page. Les faits verifies ici sont ceux qui ne bougent pas : les moteurs et
    le defaut, le repli, les routes, les colonnes de la table, le chemin de la
    voix a la lecture, et les tests cites.
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('### ')
                   and 'Distribution de voix par personnage' in l), None)
    if depart is None:
        fait('le sujet « Distribution de voix par personnage » existe', False,
             'aucun titre ### ne porte ce nom')
        return
    fin = next((n for n in range(depart + 1, len(lignes))
                if lignes[n].startswith('### ')), len(lignes))
    texte = '\n'.join(lignes[depart:fin])

    fait("le sujet s ouvre par un bloc « Aujourd hui »",
         "Aujourd'hui — l'état actuel en clair" in texte,
         'le bloc « Aujourd hui » manque a la ligne %d' % (depart + 1))

    vc = lire(RACINE / 'modules' / 'voice_casting.py')
    programme = lire(RACINE / 'main.py')
    page = lire(RACINE / 'frontend' / 'app.js')
    html = lire(RACINE / 'frontend' / 'index.html')
    config = lire(RACINE / 'modules' / 'config.py')

    # -- 1. Les quatre moteurs, et le defaut. ---------------------------------
    aiguillage = re.search(r'async def _call_llm\(.*?(?=\nasync def |\Z)',
                           vc, re.S)
    bloc_llm = aiguillage.group(0) if aiguillage else ''
    for moteur in ('mistral', 'deepseek', 'local'):
        fait('l aiguillage de _call_llm mene au moteur %s' % moteur,
             'provider == "%s"' % moteur in bloc_llm,
             'modules/voice_casting.py n aiguille plus vers %s' % moteur)
    fait('l aiguillage de _call_llm se termine par Gemini',
         '_call_gemini(' in bloc_llm,
         'le repli de _call_llm n appelle plus _call_gemini')

    manquants = [m for m in ('Gemini', 'DeepSeek', 'Mistral', 'modèle local')
                 if m not in texte]
    fait('les quatre moteurs sont nommes dans le sujet', not manquants,
         'le sujet ne nomme pas : %s' % ', '.join(manquants))

    defauts = len(re.findall(r'provider: str = "gemini"', programme))
    fait('Gemini est bien le defaut du serveur, et le sujet le dit',
         defauts >= 2 and 'provider: str = "gemini"' in texte,
         'main.py porte %d fois `provider: str = "gemini"` ; le sujet le cite '
         'ou non' % defauts)

    fait('la page marque le bouton Gemini comme recommande',
         'provider-btn provider-recommended" data-provider="gemini"' in html
         and 'provider-recommended' in texte,
         'frontend/index.html ne porte plus `provider-recommended` sur Gemini, '
         'ou le sujet ne le cite plus')

    # -- 2. Le repli automatique. ---------------------------------------------
    fait('les moteurs de secours sont ceux annonces par le sujet',
         'MOTEURS_DE_SECOURS = ["deepseek", "local"]' in programme
         and re.search(r'MOTEURS_DE_SECOURS = \["deepseek",\s*"local"\]',
                       texte) is not None,
         'main.py porte `MOTEURS_DE_SECOURS = ["deepseek", "local"]` et le '
         'sujet ne le cite plus tel quel')
    fait('le repli est bien branche sur les deux appels au casting',
         programme.count('provider_repli=MOTEURS_DE_SECOURS') == 2,
         'main.py passe provider_repli %d fois (2 attendus)'
         % programme.count('provider_repli=MOTEURS_DE_SECOURS'))

    # -- 3. Le moteur local (absent du document avant le 23/09/2026). --------
    for intitule, vrai in (
            ('la route de l etat du moteur local existe',
             '@app.get("/api/llm/local")' in programme),
            ('le moteur local se configure dans config.py',
             'def get_local_model(' in config and 'def get_local_url(' in config),
            ('config.py lit `local_model` et `local_url`',
             '"local_model"' in config and '"local_url"' in config),
            ('l appel au moteur local existe (Ollama)',
             'async def _call_ollama(' in vc and 'api/chat' in vc),
            ('le paquet du moteur local est nomme dans le sujet',
             'BATCH_SIZE_LOCAL = ' in vc and 'BATCH_SIZE_LOCAL' in texte),
            ('le sujet nomme les deux cles de configuration',
             'local_model' in texte and 'local_url' in texte)):
        fait(intitule, vrai,
             'le code ne le porte plus, ou le sujet a cesse de le dire')

    modele = re.search(r'(?m)^GEMINI_MODEL = "([^"]+)"', vc)
    fait('le modele Gemini annonce est celui du code',
         modele is not None and 'GEMINI_MODEL' in texte
         and modele.group(1) in vc,
         'modules/voice_casting.py ne porte plus GEMINI_MODEL')


    # -- 4. Les routes du casting : la liste du sujet est celle du code. -----
    routes = re.findall(r'@app\.(?:get|post|put)\("/api/books/\{book_id\}/cast'
                        r'(/[a-z_\-]*)?"', programme)
    chemins = sorted(('/cast' + (r or '')).rstrip('/') for r in routes)
    absentes = [c for c in chemins if c not in texte]
    fait('les %d routes du casting sont toutes citees par le sujet'
         % len(chemins),
         bool(chemins) and not absentes and 'onze routes' in texte,
         'le code porte %d routes ; le sujet n en cite pas : %s'
         % (len(chemins), ', '.join(absentes) or 'aucune'))

    # -- 5. La table `voices` : les colonnes citees sont les vraies. ---------
    table = re.search(r'CREATE TABLE IF NOT EXISTS voices \((.*?)\)\n\s*"""',
                      programme, re.S)
    colonnes_code = re.findall(r'(?m)^\s+([a-z_]+)\s', table.group(1)) \
        if table else []
    colonnes_code += re.findall(r'ALTER TABLE voices ADD COLUMN ([a-z_]+)',
                                programme)
    bloc_table = re.search(r'la table `voices` porte huit colonnes\*\* '
                           r'— ([^;]+);', texte, re.S)
    colonnes_doc = re.findall(r'`([a-z_]+)`', bloc_table.group(1)) \
        if bloc_table else []
    fait('les huit colonnes de `voices` sont celles du code',
         colonnes_doc == colonnes_code,
         'le code porte %s ; le sujet ecrit %s'
         % (', '.join(colonnes_code), ', '.join(colonnes_doc) or 'rien'))

    fait('l insertion dans `voices` cite les memes colonnes',
         'INSERT INTO voices (book_id, character_name, voice_id, pitch, rate, '
         'genre, line_count)' in programme,
         'main.py n insere plus les sept colonnes attendues dans `voices`')

    # -- 6. La voix d une phrase se decide a la lecture. --------------------
    fait('la page n a ni `data-voice` ni `data-pitch`',
         all('data-voice' not in t and 'data-pitch' not in t
             for t in (page, html)),
         'la page porte de nouveau des attributs `data-voice` / `data-pitch` : '
         'le sujet dit le contraire')
    for intitule, vrai in (
            ('le sujet dit que la voix se decide a la lecture',
             'se décide à la LECTURE' in texte),
            ('le span porte bien `data-idx`',
             'data-idx="' in page and 'data-idx' in texte),
            ('_voiceForSentence decide la voix d une phrase',
             'function _voiceForSentence(' in page
             and '_voiceForSentence' in texte),
            ('_buildPlaylist construit la playlist',
             'function _buildPlaylist(' in page and '_buildPlaylist' in texte),
            ('la voix du narrateur appartient au livre',
             'narrator_voice' in programme and 'books.narrator_voice' in texte)):
        fait(intitule, vrai,
             'le code ne le porte plus, ou le sujet a cesse de le dire')

    seuil = re.search(r'(?m)^MINOR_THRESHOLD = (\d+)', vc)
    seuil_page = re.search(r'const _CAST_MINOR_THRESHOLD = (\d+);', page)
    fait('le seuil des petits roles est le meme des deux cotes, et le sujet '
         'le dit',
         seuil is not None and seuil_page is not None
         and seuil.group(1) == seuil_page.group(1)
         and 'moins de %s répliques' % seuil.group(1) in texte,
         'voice_casting.py : %s / app.js : %s ; le sujet ecrit « moins de 8 '
         'repliques » ou non'
         % (seuil.group(1) if seuil else '?',
            seuil_page.group(1) if seuil_page else '?'))

    # -- 7. Les tests cites, et le nombre de controles annonce. --------------
    fait('l outil de mesure gratuit du casting est cite et existe',
         (RACINE / 'test_voix' / '_mesurer_casting_erreurs.py').is_file()
         and '_mesurer_casting_erreurs.py' in texte,
         'test_voix/_mesurer_casting_erreurs.py est introuvable, ou le sujet '
         'ne le cite plus')

    for nom in ('test_recaste_ia.py', 'test_reprise_casting.py',
                'test_decoupage_auto_casting.py'):
        chemin = RACINE / 'test_voix' / nom
        if not chemin.is_file():
            fait('le test cite %s existe' % nom, False,
                 'test_voix/%s est introuvable' % nom)
            continue
        reel = len(re.findall(r'(?m)^\s*verifier\(',
                              chemin.read_text(encoding='utf-8')))
        annonce = _nombre_apres(texte, r'`test_voix/%s`' % re.escape(nom))
        fait('%s : le nombre de controles annonce est le vrai' % nom,
             annonce is not None and int(annonce) == reel,
             'le fichier compte %d controles ; le sujet annonce %s'
             % (reel, annonce))

    for nom in ('test_pool_casting.py', 'test_moteur_local.py',
                'test_passe1.py'):
        fait('le sujet cite %s, qui existe' % nom,
             (RACINE / 'test_voix' / nom).is_file(),
             'test_voix/%s est introuvable' % nom)


def _unites_utf16(texte):
    """Les unites UTF-16 d'une chaine -- un emoji 🎎 en vaut deux (0xD83C, 0xDF8E)."""
    brut = texte.encode('utf-16-le')
    return [brut[i] | (brut[i + 1] << 8) for i in range(0, len(brut), 2)]


def _unites_de_icone(icone):
    """Les unites d'une icone, qu'elle soit ECRITE en echappements ou en emoji.

    `frontend/app.js` ecrit `'\\uD83C\\uDF8E'` ; ce document porte l'emoji reel.
    Comparer les deux textes par `in` ne trouverait jamais rien : on compare donc
    leurs unites UTF-16. Le cas des echappements est reconnu sur la chaine
    ENTIERE (et non sur n'importe quel `\\uXXXX` qu'elle contient), sinon un
    document qui cite un code quelque part verrait sa comparaison faussee.
    """
    if re.fullmatch(r'(\\u[0-9A-Fa-f]{4})+', icone):
        return [int(c, 16) for c in re.findall(r'\\u([0-9A-Fa-f]{4})', icone)]
    return _unites_utf16(icone)


def _contient_unites(texte, icone):
    """`texte` porte-t-il cette icone, dans l'une ou l'autre ecriture ?"""
    aiguille = _unites_de_icone(icone)
    meule = _unites_utf16(texte)
    n = len(aiguille)
    return any(meule[i:i + n] == aiguille for i in range(len(meule) - n + 1))


def check_sujet_symboles():
    """14. Le sujet « Symboles de genre devant les prenoms » dit-il ce que le
    code fait ?

    Meme logique que les sections 9 a 13. Ce sujet est composite lui aussi --
    les symboles de genre (19/09/2026), les icones des moteurs, la mise a
    l'echelle des boutons de la barre du lecteur et le bouton « Vider le cache »
    (20/09/2026) -- et il portait TROIS derives, toutes trouvees le 23/09/2026 :
    un tableau d'icones qui s'arretait a SIX moteurs alors que la table en porte
    SEPT depuis Pocket TTS, un exemple de libelle qui datait du matin meme
    (« Allemagne (NIMM Voix) ... — Kokoro », la ou le code ecrit les drapeaux et
    l'icone seule), et une regle de style annoncee « les trois » alors qu'elle en
    porte six. Les faits verifies ici sont ceux qui ne bougent pas.
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('### ') and 'Symboles' in l), None)
    if depart is None:
        fait('le sujet des symboles de genre existe', False,
             'aucun titre ### ne porte « Symboles »')
        return
    fin = next((n for n in range(depart + 1, len(lignes))
                if lignes[n].startswith('### ')), len(lignes))
    texte = '\n'.join(lignes[depart:fin])

    fait("le sujet s ouvre par un bloc « Aujourd hui »",
         "Aujourd'hui — l'état actuel en clair" in texte,
         'le bloc « Aujourd hui » manque a la ligne %d' % (depart + 1))

    page = lire(RACINE / 'frontend' / 'app.js')
    html = lire(RACINE / 'frontend' / 'index.html')
    css = lire(RACINE / 'frontend' / 'styles.css').replace('\r\n', '\n')
    programme = lire(RACINE / 'main.py')
    cache = lire(RACINE / 'modules' / 'tts_cache.py')

    # -- 1. La fonction des symboles, ses conventions, le piege du vide. ------
    fonction = re.search(r'function _symboleGenre\(genre\) \{.*?\n\}', page, re.S)
    bloc = fonction.group(0) if fonction else ''
    fait('_symboleGenre existe dans frontend/app.js', bool(bloc),
         '_symboleGenre est introuvable dans la page')
    fait('le symbole feminin porte son selecteur emoji',
         "'\\u2640\\uFE0F'" in bloc,
         'le symbole femme n est plus ecrit avec son selecteur \\uFE0F')
    fait('le symbole masculin vaut pour « M » comme pour « H »',
         "'\\u2642\\uFE0F'" in bloc and "genre === 'M' || genre === 'H'" in bloc,
         'la tolerance M / H a disparu de _symboleGenre')
    fait('un genre inconnu ne recoit AUCUN symbole',
         re.search(r"return '';", bloc) is not None,
         '_symboleGenre ne retombe plus sur la chaine vide')
    fait('la colonne `genre` des fiches a bien « H » pour defaut',
         "genre           TEXT DEFAULT 'H'" in programme,
         'main.py ne declare plus DEFAULT H sur la colonne genre')

    # -- 2. Les trois emplacements. ------------------------------------------
    fait('la ligne de personnage porte le symbole ET le mot',
         "(v.genre === 'F') ? 'Femme' : (v.genre ? 'Homme' : '')" in page
         and 'const symboleGenre = _symboleGenre(v.genre);' in page,
         'la ligne de personnage du casting a change de regle')
    fait('l ancien repli sur « Homme » a bien disparu',
         "v.genre === 'F' ? 'Femme' : 'Homme'" not in page,
         "l ancien repli (tout ce qui n est pas F devient Homme) est revenu")
    fait('la barre « Voix proposees » porte ses deux symboles',
         '&#x2640;&#xFE0F; Femmes' in html and '&#x2642;&#xFE0F; Hommes' in html,
         'les entites des symboles ont disparu de #cast-gender-actions')

    # -- 3. Le libelle d une voix : les drapeaux, puis l icone seule. --------
    identite = re.search(r'function _identiteVoix\(v\) \{.*?\n\}', page, re.S)
    corps = identite.group(0) if identite else ''
    fait('le libelle d une voix s arrete aux drapeaux (jamais le pays ecrit)',
         'DRAPEAU_FR + _secondDrapeauDeVoix(v)' in corps,
         'le libelle d une voix ne se compose plus des deux drapeaux')
    fait('le libelle d une voix ne porte plus le NOM du moteur',
         "return _identiteVoix(v) + (icone ? ' \\u2014 ' + icone : '');" in page,
         'le libelle complet ne fait plus suivre l icone seule')
    fait('la page ne cite plus la provenance « NIMM Voix »',
         'NIMM Voix' not in page,
         'la page ecrit de nouveau « NIMM Voix » quelque part')

    # -- 4. Les sept moteurs, et leurs icones ECRITES dans cette page. -------
    table = re.search(r'const FAMILLES_VOIX = \[(.*?)\n\];', page, re.S)
    entrees = re.findall(r"\['([a-z]+)',\s*'([^']*)',\s*'([^']*)'\]",
                         table.group(1) if table else '')
    fait('FAMILLES_VOIX porte sept moteurs', len(entrees) == 7,
         'la table des familles porte %d moteur(s)' % len(entrees))
    fait('Pocket TTS est dans la table',
         any(cle == 'pocket' for cle, _, _ in entrees),
         'la famille pocket a disparu de FAMILLES_VOIX')
    for cle, libelle, icone in entrees:
        fait('le sujet ecrit l icone de %s' % libelle,
             _contient_unites(texte, icone),
             'l icone de %s (%s) n est pas dans le sujet' % (libelle, icone))

    # -- 5. La regle de style commune des boutons du lecteur. ----------------
    bloc_regle = next((m.group(1) for m in
                       re.finditer(r'((?:#[a-z-]+,\n)*#[a-z-]+ \{)', css)
                       if '#multivoice-btn' in m.group(1)), '')
    boutons = re.findall(r'#[a-z-]+', bloc_regle)
    fait('la regle de style commune des boutons porte six boutons',
         len(boutons) == 6,
         'la regle commune porte %d selecteur(s) : %s' % (len(boutons), boutons))
    fait('les boutons de la regle sont TOUS cites par le sujet',
         bool(boutons) and all(b in texte for b in boutons),
         'bouton(s) de la regle absent(s) du sujet : %s'
         % [b for b in boutons if b not in texte])

    # -- 6. Le bouton du cache : ses deux routes et son quota. ---------------
    for route in ('/api/cache_audio', '/api/cache_audio/vider'):
        fait('la route %s existe dans main.py' % route,
             '"%s"' % route in programme,
             'main.py ne declare plus %s' % route)
    fait('le quota du cache est de 2 Go',
         '_QUOTA_GB = int(os.environ.get("NIMM_TTS_CACHE_GB", "2")' in cache,
         'la valeur par defaut du quota a change dans modules/tts_cache.py')
    fait('l en-tete du module de cache annonce le bon defaut',
         'defaut : 2 Go' in cache and 'defaut : 20 Go' not in cache,
         'modules/tts_cache.py annonce encore 20 Go comme defaut '
         '(l historique du passage a 2 Go, lui, doit rester)')
    fait('la page compose le libelle du bouton du cache',
         'function _libelleBoutonCache' in page
         and 'function _formatOctets' in page,
         '_libelleBoutonCache ou _formatOctets est introuvable')

    # -- 7. Les tests cites, et les chiffres annonces. -----------------------
    for nom in ('test_libelle_voix.js', 'test_ids_ecran.py',
                'test_tiroir_voix_libres.js', 'test_bouton_moteur.js',
                'test_cache_audio.py', 'test_cache_audio.js'):
        chemin = RACINE / 'test_voix' / nom
        if not chemin.is_file():
            fait('le test cite %s existe' % nom, False,
                 'test_voix/%s est introuvable' % nom)
            continue
        reel = len(re.findall(r'(?m)^\s*(?:verifier|egal)\(',
                              chemin.read_text(encoding='utf-8')))
        annonce = _nombre_apres(texte, r'`test_voix/%s`' % re.escape(nom))
        fait('%s : le nombre de controles annonce est le vrai' % nom,
             annonce is not None and int(annonce) == reel,
             'le fichier compte %d controles ; le sujet annonce %s'
             % (reel, annonce))


def check_sujet_ecran_verrouille():
    """15. Le sujet « Lire ecran verrouille » dit-il ce que le code fait ?

    Meme logique que les sections 9 a 14. Ce sujet (chronique du 20/09/2026, la
    reserve « a bloc » et le lecteur facon Deezer) portait une derive : il
    annoncait « **160 controles** au total » pour `test_ids_ecran.py`, alors que
    la meme page ecrivait **168** vingt lignes plus haut, et que le test en
    EXECUTE 168 (25 dans sa seule section « 3 sexies »). Les controles des tests
    sont donc lus par EXECUTION ici (`_controles_executes`), pas en comptant les
    `verifier(` ecrits -- sinon on compterait 22 la ou le lecteur integre en
    verifie 42.

    Les faits verifies sont ceux du bloc « Aujourd'hui » : les quatre constantes
    du prechargement avec leur valeur, le declencheur de la reserve, les HUIT
    actions du lecteur systeme, les SEPT telecommandes du lecteur integre, le
    collage des phrases (et son filet), la pause venue de l'exterieur.
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('### ') and 'verrouillé' in l), None)
    if depart is None:
        fait('le sujet « Lire ecran verrouille » existe', False,
             'aucun titre ### ne porte « verrouillé »')
        return
    fin = next((n for n in range(depart + 1, len(lignes))
                if lignes[n].startswith('### ')), len(lignes))
    texte = '\n'.join(lignes[depart:fin])

    fait("le sujet s ouvre par un bloc « Aujourd hui »",
         "Aujourd'hui — l'état actuel en clair" in texte,
         'le bloc « Aujourd hui » manque a la ligne %d' % (depart + 1))

    js = lire(RACINE / 'frontend' / 'app.js')
    html = lire(RACINE / 'frontend' / 'index.html')

    # -- 1. Les quatre constantes, avec leur valeur. --------------------------
    for nom, motif in (
            ('PREFETCH_MAX_AHEAD_CHARS_BURST',
             r'const PREFETCH_MAX_AHEAD_CHARS_BURST\s*=\s*(\d+)'),
            ('PREFETCH_MAX_AHEAD_CHARS',
             r'const PREFETCH_MAX_AHEAD_CHARS\s*=\s*(\d+)'),
            ('PREFETCH_CONCURRENCY', r'const PREFETCH_CONCURRENCY\s*=\s*(\d+)'),
            ('_PAS_PARAGRAPHES', r'const _PAS_PARAGRAPHES\s*=\s*(\d+)')):
        valeur = _valeur(motif, js)
        cite = re.search(r'`%s`\s*=\s*\*\*([\d\s]+?)\*\*' % re.escape(nom), texte)
        ecrit = cite.group(1).replace(' ', '') if cite else None
        fait('%s : la valeur citee est celle du code' % nom,
             valeur is not None and ecrit == valeur,
             'frontend/app.js porte %s ; le sujet ecrit %s' % (valeur, ecrit))

    # -- 2. Le declencheur de la reserve. -------------------------------------
    for nom, quoi in (
            ('_prechargementBurst', 'le drapeau de la reserve'),
            ('_pumpCourant', 'le crochet qui relance le remplissage')):
        fait('%s : %s existe dans la page' % (nom, quoi),
             nom in js, 'frontend/app.js ne porte plus %s' % nom)
        fait('%s est nomme dans le sujet' % nom, ('`%s`' % nom) in texte,
             'le sujet ne nomme plus %s' % nom)
    fait('le garde-fou « hors lecture, rien ne se declenche » est dans le code',
         "if (_ttsState !== 'playing' && _ttsState !== 'loading') return;" in js,
         'le declencheur visibilitychange ne teste plus l etat de lecture')

    # -- 3. Les huit actions du lecteur SYSTEME, et le sujet les nomme. -------
    actions = re.findall(r"lier\('([a-z]+)'", js)
    fait('le lecteur systeme declare huit actions', len(actions) == 8,
         'frontend/app.js declare %d action(s) : %s' % (len(actions), actions))
    non_citees = [a for a in actions if ('`%s`' % a) not in texte]
    fait('chaque action du lecteur systeme est nommee dans le sujet',
         not non_citees, 'jamais nommees : %s' % ', '.join(non_citees))
    fait('la page envoie sa progression au lecteur systeme',
         '_majPositionMediaSession(' in js,
         '_majPositionMediaSession est introuvable')
    fait('la position envoyee est BORNEE et PROTEGEE',
         'Math.min(Math.max(0, idx || 0), duree)' in js and 'catch (e)' in js,
         'le bornage ou le try a disparu de _majPositionMediaSession')
    fait('la couverture du lecteur systeme est en URL absolue',
         'location.origin + ' in js,
         '_urlCouvertureLivre ne compose plus une URL absolue')

    # -- 4. Les sept telecommandes du lecteur INTEGRE. -----------------------
    paires = re.findall(r"\['(lecteur-[a-z-]+)',\s*'([a-z-]+)'\]", js)
    fait('le lecteur integre porte sept telecommandes', len(paires) == 7,
         'frontend/app.js porte %d paire(s) : %s' % (len(paires), paires))
    fait('le sujet annonce sept boutons',
         re.search(r'\*\*sept\*{0,2} boutons', texte) is not None,
         'le sujet n ecrit plus « sept boutons »')
    fait('la barre de progression est la porte d entree du lecteur',
         "getElementById('tts-progress-row')" in js
         and "addEventListener('click', _ouvrirLecteur)" in js,
         'le branchement de la barre de progression a change')
    for nom in ('lecteur-modal', 'tts-progress-row', 'tts-progress-ouvrir'):
        fait('#%s existe dans la page et est nomme par le sujet' % nom,
             ('id="%s"' % nom) in html and ('#%s' % nom) in texte,
             '#%s absent de la page, ou jamais nomme par le sujet' % nom)

    # -- 5. Le collage des phrases, et son filet. ----------------------------
    for nom, quoi in (
            ('_collerWav', 'le collage en un seul morceau'),
            ('_blobSilence', 'le silence de la pause entre paragraphes'),
            ('_dureeWav', 'la duree calculee'),
            ('_enteteDeBlob', 'la lecture du debut du fichier'),
            ('_playBlob', 'la lecture phrase par phrase (le filet)')):
        fait('%s : %s existe' % (nom, quoi), ('function %s' % nom) in js,
             'frontend/app.js ne porte plus %s' % nom)
        fait('%s est nomme dans le sujet' % nom, ('`%s' % nom) in texte,
             'le sujet ne nomme plus %s' % nom)
    fait('l en-tete de blob transmet la taille REELLE du fichier',
         'function _enteteWav(octets, tailleFichier)' in js
         and 'blob.slice(0, 64)' in js,
         'la lecture des 64 premiers octets, ou la taille reelle, a change')

    # -- 6. La pause venue de l exterieur. -----------------------------------
    fait('l ecouteur de pause exterieure est pose par le collage',
         'audio.onpause = () => {' in js,
         'audio.onpause n est plus pose par _jouerMorceauColle')
    fait('la boucle de lecture rend la main sur une pause',
         "if (_ttsState === 'paused') break;" in js,
         'la boucle ne teste plus l etat « paused »')
    fait('le lecteur du telephone est remis en pause',
         "navigator.mediaSession.playbackState = 'paused'" in js,
         'le playbackState du lecteur systeme n est plus mis a jour')

    # -- 7. Les controles des tests cites : par EXECUTION, pas par ecriture. --
    for nom, commande in (
            ('test_lecteur_media.js', ['node', 'test_voix/test_lecteur_media.js']),
            ('test_pause_casque.js', ['node', 'test_voix/test_pause_casque.js']),
            ('test_collage_wav.js', ['node', 'test_voix/test_collage_wav.js'])):
        if not (RACINE / 'test_voix' / nom).is_file():
            fait('le test cite %s existe' % nom, False,
                 'test_voix/%s est introuvable' % nom)
            continue
        reel = _controles_executes(commande)
        if reel is None:
            print('        (test non lance : interpreteur absent -- ignore)')
            continue
        annonce = _nombre_apres(texte, r'`test_voix/%s`' % re.escape(nom))
        fait('%s : le nombre de controles annonce est le vrai' % nom,
             annonce is not None and int(annonce) == reel,
             'le test execute %d controles ; le sujet annonce %s'
             % (reel, annonce))

    # `test_ids_ecran.py` : la section « 3 sexies », ET le fichier entier.
    par_section, total = _controles_par_section(
        [sys.executable, 'test_voix/test_ids_ecran.py'])
    if total is None:
        print('        (test non lance : interpreteur absent -- ignore)')
    else:
        sexies = next((n for titre, n in par_section.items()
                       if titre.startswith('3 sexies')), None)
        annonce_sexies = _valeur(
            r'`test_voix/test_ids_ecran\.py`\s*\(\*\*(\d+)\*\*', texte)
        annonce_total = _valeur(r'\*\*(\d+)\*\*\s*pour le fichier entier', texte)
        fait('test_ids_ecran.py, section « 3 sexies » : le compte annonce est le vrai',
             annonce_sexies is not None and sexies is not None
             and int(annonce_sexies) == sexies,
             'la section « 3 sexies » execute %s controles ; le sujet annonce %s'
             % (sexies, annonce_sexies))
        fait('test_ids_ecran.py, fichier entier : le compte annonce est le vrai',
             annonce_total is not None and int(annonce_total) == total,
             'le fichier execute %d controles ; le sujet annonce %s'
             % (total, annonce_total))


def _nombre_fr(valeur):
    """'0.25' -> '0,25' : le document ecrit les nombres a la francaise."""
    return str(valeur).replace('.', ',')


def _valeur_constante(source, nom):
    """La valeur d'une constante, meme ecrite sur deux lignes.

    Deux ecritures existent dans les services :
        SILENCE_QUEUE_S = 0.25
        SILENCE_QUEUE_S = float(os.environ.get("NIMM_...", "0.0") or "0.0")
    Dans le second cas on renvoie la valeur par DEFAUT (celle du code).
    """
    simple = _valeur(r'(?m)^%s\s*=\s*([0-9.]+)' % nom, source)
    if simple is not None:
        return simple
    m = re.search(r'(?m)^%s\s*=\s*float\(\s*(?:os\.)?environ\.get\('
                  r'\s*"[^"]+"\s*,\s*"([^"]+)"' % nom, source)
    return m.group(1) if m else None


def _sujet(nom, lignes):
    """(texte, premiere ligne) d'un sujet `### ` designe par un morceau de titre."""
    depart = next((n for n, l in enumerate(lignes)
                   if l.startswith('### ') and nom in l), None)
    if depart is None:
        return None, None
    fin = next((n for n in range(depart + 1, len(lignes))
                if lignes[n].startswith('### ')), len(lignes))
    return '\n'.join(lignes[depart:fin]), depart + 1


def check_sujet_rognage():
    """16. Le sujet « Rognage des silences de bord » dit-il ce que le code fait ?

    Meme logique que les sections 9 a 15. Ce sujet ouvrait encore sur le monde
    d'AVANT : il annoncait « ~0,15 s en fin » la ou `modules/audio_trim.py` porte
    **0,35 s** depuis le 17/09/2026, « 12 controles » la ou
    `test_rogner_babil_xtts.py` en execute **11**, et il ignorait les rognages
    arrives apres lui -- **NeuTTS** (16/09/2026) et la respiration de **Kyutai**
    (17/09/2026), tous deux DANS leur service.

    Les faits verifies sont ceux du bloc « Aujourd'hui » : les marges d'Edge,
    celles du service XTTS et ses deux filets, le rognage de NeuTTS, la
    respiration de Kyutai, ce que fait Pocket a la place, la cle du cache, et les
    quatre tests cites -- comptes en les LANCANT (lecon du 23/09/2026).
    """
    lignes = DOC.read_text(encoding='utf-8').splitlines()
    texte, numero = _sujet('Rognage des silences de bord', lignes)
    if texte is None:
        fait('le sujet « Rognage des silences de bord » existe', False,
             'aucun titre ### ne porte « Rognage des silences de bord »')
        return

    fait("le sujet s ouvre par un bloc « Aujourd hui »",
         "Aujourd'hui — l'état actuel en clair" in texte,
         'le bloc « Aujourd hui » manque a la ligne %d' % numero)

    # -- 1. Edge : les marges REELLES du filtre, et celles que la page cite. ---
    trim = lire(RACINE / 'modules' / 'audio_trim.py')
    filtres = re.search(r'filtres = \((.*?)\)\n', trim, re.S)
    filtres = filtres.group(1) if filtres else ''
    marges = re.findall(r'start_silence=([0-9.]+)', filtres)
    seuil = _valeur(r'start_threshold=(-?[0-9]+dB)', filtres)
    fait('audio_trim.py rogne a -45 dB, et le sujet le dit',
         seuil == '-45dB' and '-45 dB' in texte,
         'le filtre porte %s ; le sujet ecrit %s'
         % (seuil, 'oui' if '-45 dB' in texte else 'non'))
    fait('la marge de tete citee est celle du filtre',
         len(marges) > 0 and ('**%s s** de marge en tête' % _nombre_fr(marges[0]))
         in texte,
         'le filtre porte %s s de tete' % (marges[0] if marges else '?'))
    fait('la marge de queue citee est celle du filtre',
         len(marges) > 1 and ('**%s s** en queue' % _nombre_fr(marges[-1]))
         in texte,
         'le filtre porte %s s de queue (le sujet doit porter 0,35)'
         % (marges[-1] if len(marges) > 1 else '?'))

    # -- 2. Edge : le rognage en place AVANT la mise en cache. -----------------
    tts = lire(RACINE / 'modules' / 'tts.py')
    i_trim = tts.find('trim_mp3_silence')
    i_cache = tts.find('put_audio', i_trim)
    fait('le rognage d Edge est applique avant la mise en cache',
         0 <= i_trim < i_cache,
         'dans modules/tts.py, trim_mp3_silence ne precede plus put_audio')
    fait('le sujet nomme la fonction qui rogne cote Edge',
         '`synthesize_stream`' in texte,
         'le sujet ne nomme plus synthesize_stream')

    # -- 3. XTTS : les constantes du service, avec leur valeur. ---------------
    xtts = lire(RACINE / 'xtts_service' / 'servir_xtts.py')
    for nom in ('SILENCE_QUEUE_S', 'SEUIL_SON', 'SILENCE_PHRASE_S'):
        code = _valeur_constante(xtts, nom)
        cite = _valeur(r'`%s`?\s*=\s*\*{0,2}([0-9,]+)' % re.escape(nom), texte)
        fait('%s : la valeur citee est celle du service' % nom,
             code is not None and cite == _nombre_fr(code),
             'xtts_service/servir_xtts.py porte %s ; le sujet ecrit %s'
             % (code, cite))
    ms = _valeur_constante(xtts, 'BLOC_ANALYSE_S')
    fait('les blocs d analyse de 20 ms sont ceux du service',
         ms is not None and abs(float(ms) - 0.02) < 0.0001
         and '20 ms' in texte,
         'BLOC_ANALYSE_S vaut %s ; le sujet ecrit « 20 ms » : %s'
         % (ms, '20 ms' in texte))

    # -- 4. XTTS : les deux filets anti-babil. --------------------------------
    for nom in ('SEUIL_SILENCE_LONG_S', 'RESIDU_MAX_S', 'TOKENS_MINIMUM',
                'TOKENS_PLAFOND'):
        code = _valeur_constante(xtts, nom)
        present = code is not None and (('`%s`' % nom) in texte)
        fait('%s est nommee dans le sujet' % nom, present,
             'le service porte %s = %s ; le sujet ne la nomme plus'
             % (nom, code))

    # -- 5. XTTS : les bornes de longueur, recalculees par le code du service. -
    espace = {}
    try:
        lignes_const = [l for l in xtts.splitlines()
                        if re.match(r'^[A-Z][A-Z0-9_]*\s*=', l)
                        and l.count('(') == l.count(')')]
        fragment = ('\n'.join(lignes_const) + '\n'
                    + xtts[xtts.index('def duree_max_morceau'):
                           xtts.index('def rogner_a_duree')])
        espace.update({'Path': Path, 'os': os,
                       '__file__': str(RACINE / 'xtts_service' /
                                       'servir_xtts.py')})
        exec(compile(fragment, 'servir_xtts', 'exec'), espace)
        for taille, cite in ((19, '3,04 s'), (250, '32,7 s')):
            borne = espace['duree_max_morceau']('x' * taille)
            fait('la borne d un morceau de %d caracteres est bien %s'
                 % (taille, cite),
                 abs(borne - float(cite.replace(' s', '').replace(',', '.')))
                 < 0.05 and cite in texte,
                 'le service calcule %.3f s ; le sujet ecrit %s'
                 % (borne, cite if cite in texte else '(absent)'))
        plancher = espace['TOKENS_MINIMUM'] * espace['SECONDES_PAR_TOKEN']
        plafond = espace['TOKENS_PLAFOND'] * espace['SECONDES_PAR_TOKEN']
        fait('le plancher de jetons vaut bien ~1 s',
             abs(plancher - 1.02) < 0.05,
             'TOKENS_MINIMUM x SECONDES_PAR_TOKEN = %.3f s' % plancher)
        fait('le plafond de jetons vaut bien ~38 s',
             abs(plafond - 38.4) < 0.5,
             'TOKENS_PLAFOND x SECONDES_PAR_TOKEN = %.3f s' % plafond)
    except Exception as erreur:
        fait('les bornes du service XTTS sont recalculables', False,
             'le fragment du service n a pas pu etre execute : %s' % erreur)

    # -- 6. NeuTTS : il rogne, et le sujet le dit. ----------------------------
    neutts = lire(RACINE / 'neutts_service' / 'servir_neutts.py')
    for nom in ('rogner_queue', 'rogner_a_duree', 'duree_max_derivee'):
        fait('neutts_service/servir_neutts.py porte %s' % nom,
             ('def %s(' % nom) in neutts,
             '%s a disparu du service NeuTTS' % nom)
        fait('%s est nommee dans le sujet' % nom, nom in texte,
             'le sujet ne nomme plus %s (le rognage de NeuTTS est oublie)' % nom)
    marge_neutts = _valeur_constante(neutts, 'SILENCE_QUEUE_S')
    fait('la marge de queue de NeuTTS est bien celle d Edge (0,25 s)',
         marge_neutts is not None and abs(float(marge_neutts) - 0.25) < 0.001,
         'neutts_service/servir_neutts.py porte %s' % marge_neutts)

    # -- 7. Kyutai : sa respiration vaut 0 par defaut. ------------------------
    kyutai = lire(RACINE / 'kyutai_service' / 'servir_kyutai.py')
    respiration = _valeur_constante(kyutai, 'SILENCE_QUEUE_S')
    fait('SILENCE_QUEUE_S de Kyutai vaut 0 par defaut',
         respiration is not None and abs(float(respiration)) < 0.0001,
         'kyutai_service/servir_kyutai.py porte %s par defaut' % respiration)
    fait('le sujet dit que la respiration de Kyutai vaut 0',
         'elle vaut donc **0** par défaut' in texte,
         'le sujet doit rappeler que Kyutai ne rogne pas (0 par defaut)')

    # -- 8. Pocket : il regenere au lieu de rogner. ---------------------------
    pocket = lire(RACINE / 'pocket_tts_service' / 'servir_pocket_tts.py')
    for nom in ('NIVEAU_MINI', 'ESSAIS_MAX'):
        code = _valeur_constante(pocket, nom)
        fait('%s de Pocket : la valeur citee est celle du service' % nom,
             code is not None
             and ('`%s = %s`' % (nom, _nombre_fr(code))) in texte,
             'servir_pocket_tts.py porte %s = %s ; le sujet ecrit %s'
             % (nom, code, _valeur(r'`%s = ([0-9,]+)`' % nom, texte)))

    # -- 9. La cle du cache : la version, pas le rognage. ---------------------
    cache = lire(RACINE / 'modules' / 'tts_cache.py')
    version = _valeur(r'(?m)^VERSION_CACHE = (\d+)', cache)
    fait('la version de cache citee est celle du code',
         version is not None and ('**%s** aujourd' % version) in texte,
         'modules/tts_cache.py porte VERSION_CACHE = %s ; le sujet ecrit %s'
         % (version, _valeur(r'\*\*(\d+)\*\* aujourd', texte)))
    cle = cache[cache.find('def _hash_key'):cache.find('def _dir_size')]
    fait('le rognage n entre pas dans la cle du cache',
         'trim' not in cle and 'audio_trim' not in cle,
         'la cle de cache cite desormais le rognage : le sujet doit le dire')
    fait('le sujet previent que le cache garde l ancien rendu',
         "jusqu'à purge de `data/tts_cache/`" in texte,
         'le sujet ne dit plus ce que devient une phrase deja generee')

    # -- 10. Les quatre tests : comptes en les LANÇANT. ----------------------
    lanceur = lire(RACINE / 'test_voix' / 'lancer_tous_les_tests.py')
    tous_dans_le_lanceur = True
    for nom in ('test_rogner_queue_xtts.py', 'test_borne_babil_xtts.py',
                'test_rogner_babil_xtts.py', 'test_neutts_service.py'):
        if not (RACINE / 'test_voix' / nom).is_file():
            fait('le test cite %s existe' % nom, False,
                 'test_voix/%s est introuvable' % nom)
            continue
        tous_dans_le_lanceur = tous_dans_le_lanceur and (nom in lanceur)
        reel = _controles_executes([sys.executable, 'test_voix/' + nom])
        if reel is None:
            print('        (test non lance : interpreteur absent -- ignore)')
            continue
        annonce = _nombre_apres(texte, r'`test_voix/%s`' % re.escape(nom))
        fait('%s : le nombre de controles annonce est le vrai' % nom,
             annonce is not None and int(annonce) == reel,
             'le test execute %d controles ; le sujet annonce %s'
             % (reel, annonce))
    fait('le sujet dit vrai sur le lanceur',
         (not tous_dans_le_lanceur)
         == ("Aucun des quatre n'est dans la" in texte),
         'dans test_voix/lancer_tous_les_tests.py : les quatre y sont : %s ;'
         '\n        le sujet ecrit %s'
         % (tous_dans_le_lanceur,
            'oui' if "Aucun des quatre n'est dans la" in texte else 'non'))

    # -- 11. Les outils d atelier cites existent. -----------------------------
    for chemin in ('xtts_service/_mesurer_bords_xtts.py',
                   'test_voix/_inspecter_phrase_xtts.py',
                   'test_voix/_tracer_phrase_cache.py',
                   'test_voix/_chercher_babil_cache.py',
                   'test_voix/_mesurer_phrases_courtes.py',
                   'test_voix/ecoute_babil'):
        fait('l outil cite %s existe' % chemin, (RACINE / chemin).exists(),
             '%s est introuvable' % chemin)


def _controles_executes(commande):
    """Le nombre de controles qu'un test EXECUTE vraiment (ses lignes OK).

    Les sections 12 et 14 comptent les `verifier(` ECRITS dans le fichier : c'est
    juste pour un test sans boucle, et faux des qu'une boucle parcourt une liste
    -- le lecteur integre en execute 42 pour 22 appels ecrits, et
    `test_ids_ecran.py` 168 pour 70. Ici on LANCE le test (hors ligne : pas de
    navigateur, pas de reseau, pas de base, aucune ecriture) et on compte.
    Retourne None si l'interpreteur manque : on ne crie pas pour un outil absent.
    """
    try:
        r = subprocess.run(commande, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', cwd=str(RACINE))
    except OSError:
        return None
    sortie = (r.stdout or '') + (r.stderr or '')
    return len(re.findall(r'(?m)^\s*OK\b', sortie))


def _controles_par_section(commande):
    """{titre de section: nombre de controles} et le total, test lance."""
    try:
        r = subprocess.run(commande, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', cwd=str(RACINE))
    except OSError:
        return None, None
    section = '(hors section)'
    par_section = {}
    total = 0
    for ligne in ((r.stdout or '') + (r.stderr or '')).splitlines():
        if (re.match(r'\s*\d+( \w+)?\)', ligne)
                and not re.match(r'\s*(OK|ECHEC)\b', ligne)):
            section = ligne.strip()
        if re.match(r'\s*(OK|ECHEC)\b', ligne):
            total += 1
            par_section[section] = par_section.get(section, 0) + 1
    return par_section, total


def main():
    print('=' * 74)
    print(' FAITS de ARCHITECTURE.md verifies contre le code (lecture seule)')
    print('=' * 74)
    print('Chaque ligne se lit : OK, ou ECART (a LIRE -- il peut etre legitime).')

    print('')
    print('--- 1 et 2. Le plan du dossier ---')
    check_plan_du_dossier()
    print('')
    print('--- 3. Les moteurs de voix ---')
    check_moteurs_de_tts()
    print('')
    print('--- 4. Les constantes citees ---')
    check_constantes()
    print('')
    print('--- 5. Les ports ---')
    check_ports()
    print('')
    print('--- 6. Les fichiers de donnees ---')
    check_donnees()
    print('')
    print('--- 7. La version de cache ---')
    check_version_cache()

    print('')
    print('--- 8. L etat actuel, sujet par sujet ---')
    check_etat_actuel()

    print('')
    print('--- 9. Le sujet « modules/tts.py » : moteurs et catalogues ---')
    check_sujet_tts()

    print('')
    print('--- 10. Le sujet « frontend/ — Interface » : les vues de la page ---')
    check_sujet_frontend()

    print('')
    print('--- 11. Le sujet « Moteur de voix Pocket TTS » : catalogue, service, ---')
    print('        modele et parametres ---')
    check_sujet_pocket()

    print('')
    print('--- 12. Le sujet « Report des notes d ecoute » : l outil de report, ---')
    print('        les boutons d etat, les seuils et les tests cites ---')
    check_sujet_notes()

    print('')
    print('--- 13. Le sujet « Distribution de voix par personnage (IA) » : --------')
    print('        les moteurs et le defaut, le repli, les routes, la table ---')
    print('        `voices`, le chemin de la voix a la lecture, les tests ---')
    check_sujet_casting()

    print('')
    print('--- 14. Le sujet « Symboles de genre devant les prenoms » : la --------')
    print('        fonction des symboles, les icones des moteurs, la regle des ---')
    print('        boutons du lecteur, le bouton du cache, les tests cites ---')
    check_sujet_symboles()

    print('')
    print('--- 15. Le sujet « Lire ecran verrouille » : la reserve « a bloc », ---')
    print('        le lecteur du systeme, le lecteur integre, le collage, la ---')
    print('        pause exterieure, et les tests cites (lances pour compter) ---')
    check_sujet_ecran_verrouille()

    print('')
    print('--- 16. Le sujet « Rognage des silences de bord » : les marges --------')
    print('        d Edge, le rognage des services XTTS et NeuTTS, la respiration -')
    print('        de Kyutai, Pocket, la cle du cache, les tests cites ---')
    check_sujet_rognage()

    print('')
    print('=' * 74)
    print(' %d ecart(s) a lire -- aucune ecriture, aucun fichier modifie'
          % len(ECARTS))
    print('=' * 74)
    return 0


if __name__ == '__main__':
    sys.exit(main())

