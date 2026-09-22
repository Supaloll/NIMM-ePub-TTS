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

Chaque fait est ECRIT ICI, en clair, avec la facon de le verifier : pas de
devinette, pas d'heuristique qui crie au loup. Un fait est OK, ou c'est un
ECART -- et un ecart est a LIRE : il peut etre legitime (une phrase datee qui
raconte une decision d'hier) ou une vraie derive.

Usage : python _verifier_faits_architecture.py
"""

import re
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
    print('=' * 74)
    print(' %d ecart(s) a lire -- aucune ecriture, aucun fichier modifie'
          % len(ECARTS))
    print('=' * 74)
    return 0


if __name__ == '__main__':
    sys.exit(main())

