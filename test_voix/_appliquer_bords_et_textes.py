# -*- coding: utf-8 -*-
r"""APPLIQUER a la production les bords propres ET les textes corriges.

DEMANDE DE LAURENT, 03/10/2026 : « Oui, applique tout : les 35 bords propres +
les 8 textes (copie datee d'abord, et tu montes le cache). »

CE QUE L'OUTIL APPLIQUE, ET RIEN D'AUTRE :
  1. les 35 references KYUTAI a bords propres, fabriquees par
     `_preparer_lot_kyutai_recoupe.py` (marge de 150 ms a chaque bord, fondu de
     20 ms, AUCUN mot coupe) : elles REMPLACENT celles de production **sous le
     MEME nom de fichier** (`<voix>_enhanced_reference.wav`). Ecrire a cote, en
     `<voix>_reference.wav`, donnerait DEUX fichiers pour le MEME identifiant
     de voix -- et le service prendrait l'un ou l'autre au hasard ;
  2. les textes corriges A L'OREILLE par Laurent : ceux du lot des 35 **et**
     ceux de son fichier du dossier `test_voix` (8 au total le 03/10/2026) ;
  3. une remise en forme de ses propres notes : les lignes enregistrees avec un
     nom abime (`..._enhanced`) sont recollees sur le VRAI nom de la voix.

GARDE-FOUS (les regles du projet, appliquees telles quelles) :
  - RAPPORT SEUL par defaut : **rien n'est ecrit sans `--ecrire`** ;
  - **copie datee** de `references.csv` ET des 35 WAV avant toute ecriture (les
    anciennes references partent dans `voix\_avants_bords_<date>\`, un
    sous-dossier que le service NE scanne PAS) ;
  - `VERSION_CACHE` monte de 1 (copie datee de `modules/tts_cache.py`) : sans
    ca, le lecteur resservirait les phrases deja generees avec l'ancien texte ;
  - le service doit ensuite **recharger ses voix** (il garde en memoire le texte
    ET l'empreinte de chaque voix) : la route `/recharger` s'en charge ;
  - **relecture de controle** apres ecriture : ce qui devait changer a change.

Usage :
    python test_voix/_appliquer_bords_et_textes.py            # RAPPORT SEUL
    python test_voix/_appliquer_bords_et_textes.py --ecrire
"""
import argparse
import csv
import re
import shutil
import sys
import time
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.stdout.reconfigure(encoding='utf-8')

DOSSIER_VOIX = RACINE / 'qwen_tts_service' / 'voix'
CSV_TEXTE = DOSSIER_VOIX / 'references.csv'
LOT = ICI / 'lot_kyutai_bords_propres_20261003'
CORRECTIONS_LOT = LOT / '_corrections_oreille.csv'
CORRECTIONS_PRODUCTION = ICI / '_corrections_oreille.csv'
CACHE = RACINE / 'modules' / 'tts_cache.py'

SUFFIXES = ('_enhanced_reference.wav', '_reference.wav')
DATE = time.strftime('%Y%m%d')


def nom_court(nom_fichier):
    """Le nom de la voix, sans son suffixe de fichier (les deux sont connus)."""
    for suffixe in SUFFIXES:
        if nom_fichier.endswith(suffixe):
            return nom_fichier[:-len(suffixe)]
    return nom_fichier


def sans_orphelin(nom):
    """« 10087_..._enhanced » -> « 10087_... » (nom abime par l'ancien outil)."""
    return nom[:-len('_enhanced')] if nom.endswith('_enhanced') else nom


def lire_references():
    """(entete, lignes) de `references.csv`, TOUT garde (les 5 colonnes)."""
    if not CSV_TEXTE.is_file():
        return None, []
    with open(CSV_TEXTE, encoding='utf-8', newline='') as flux:
        lignes = list(csv.reader(flux, delimiter=';'))
    if not lignes:
        return None, []
    return lignes[0], lignes[1:]


def lire_corrections(chemin):
    """{nom de voix: texte entendu}."""
    table = {}
    if not chemin.is_file():
        return table
    with open(chemin, encoding='utf-8', newline='') as flux:
        for ligne in csv.reader(flux, delimiter=';'):
            if len(ligne) >= 2 and ligne[0].strip() \
                    and ligne[0].strip().lower() != 'nom':
                table[ligne[0].strip()] = ligne[1]
    return table


def construire_plan():
    """(textes, references, orphelines) -- tout ce que l'application ferait."""
    entete, corps = lire_references()
    if entete is None:
        return None, None, None

    # 1. LES TEXTES. On lit les deux fichiers de notes de Laurent ; le LOT passe
    #    en dernier, donc c'est lui qui gagne si les deux parlent d'une meme voix.
    corriges = {}
    for chemin in (CORRECTIONS_PRODUCTION, CORRECTIONS_LOT):
        for nom, texte in lire_corrections(chemin).items():
            corriges[nom_court(sans_orphelin(nom))] = texte

    textes = []
    for rang, ligne in enumerate(corps):
        if len(ligne) < 2:
            continue
        voix = nom_court(ligne[0].strip())
        apres = corriges.get(voix)
        if apres is not None and apres != ligne[1].strip():
            textes.append({'rang': rang, 'voix': voix, 'fichier': ligne[0].strip(),
                           'avant': ligne[1].strip(), 'apres': apres})

    # 2. LES REFERENCES. Le lot a ete fabrique DEPUIS la production : on
    #    remplace le fichier de production qui porte le meme identifiant.
    references = []
    manquantes = []
    for fichier in sorted(LOT.glob('*_reference.wav')):
        voix = nom_court(fichier.name)
        cible = None
        for suffixe in SUFFIXES:
            essai = DOSSIER_VOIX / (voix + suffixe)
            if essai.is_file():
                cible = essai
                break
        if cible is None:
            manquantes.append(voix)
            continue
        references.append({'voix': voix, 'source': fichier, 'cible': cible,
                           'avant': cible.stat().st_size,
                           'apres': fichier.stat().st_size})

    # 3. LES NOTES ABIMEES de son propre fichier.
    orphelines = []
    table = lire_corrections(CORRECTIONS_PRODUCTION)
    for nom in sorted(table):
        if sans_orphelin(nom) != nom:
            orphelines.append(nom)
    return {'textes': textes, 'references': references,
            'manquantes': manquantes, 'orphelines': orphelines}, entete, corps


def sauvegarder(chemin, quoi):
    """Copie datee d'un fichier : `<nom>.bak_<quoi>_<date>`."""
    copie = chemin.with_name('%s.bak_%s_%s' % (chemin.name, quoi, DATE))
    shutil.copy2(str(chemin), str(copie))
    return copie


def ecrire_textes(plan, entete, corps):
    """Reecrit `references.csv` avec les textes corriges (copie datee d'abord)."""
    copie = sauvegarder(CSV_TEXTE, 'avant_bords_et_textes')
    nouvelles = [list(ligne) for ligne in corps]
    for changement in plan['textes']:
        nouvelles[changement['rang']][1] = changement['apres']
    with open(CSV_TEXTE, 'w', encoding='utf-8', newline='') as flux:
        graveur = csv.writer(flux, delimiter=';')
        graveur.writerow(entete)
        for ligne in nouvelles:
            graveur.writerow(ligne)
    return copie


def ecrire_references(plan):
    """Remplace les WAV de production par ceux du lot (copie datee d'abord).

    Le sous-dossier `_avants_bords_<date>` n'est PAS scanne par le service (il
    ne regarde que les fichiers du dossier, pas ceux des sous-dossiers) : les
    anciennes references y dorment, pretes a revenir.
    """
    garde = DOSSIER_VOIX / ('_avants_bords_' + DATE)
    garde.mkdir(exist_ok=True)
    remplacees = 0
    for item in plan['references']:
        shutil.copy2(str(item['cible']), str(garde / item['cible'].name))
        shutil.copy2(str(item['source']), str(item['cible']))
        remplacees += 1
    return garde, remplacees


def monter_le_cache():
    """`VERSION_CACHE = N` devient N+1 (copie datee de `modules/tts_cache.py`)."""
    if not CACHE.is_file():
        return None, None, None
    texte = CACHE.read_text(encoding='utf-8')
    trouve = re.search(r'^VERSION_CACHE = (\d+)\s*$', texte, re.M)
    if not trouve:
        return None, None, None
    avant = int(trouve.group(1))
    copie = sauvegarder(CACHE, 'avant_version_cache')
    texte = (texte[:trouve.start()]
             + ('VERSION_CACHE = %d' % (avant + 1))
             + texte[trouve.end():])
    CACHE.write_text(texte, encoding='utf-8')
    relu = re.search(r'^VERSION_CACHE = (\d+)\s*$',
                     CACHE.read_text(encoding='utf-8'), re.M)
    return avant, (int(relu.group(1)) if relu else None), copie


def recoller_les_notes():
    """Renomme les lignes `..._enhanced` sur le VRAI nom de la voix."""
    with open(CORRECTIONS_PRODUCTION, encoding='utf-8', newline='') as flux:
        lignes = list(csv.reader(flux, delimiter=';'))
    copie = sauvegarder(CORRECTIONS_PRODUCTION, 'avant_recollage')
    recollees = 0
    nouvelles = []
    for ligne in lignes:
        if len(ligne) >= 2 and sans_orphelin(ligne[0].strip()) != ligne[0].strip():
            ligne = list(ligne)
            ligne[0] = sans_orphelin(ligne[0].strip())
            recollees += 1
        nouvelles.append(ligne)
    with open(CORRECTIONS_PRODUCTION, 'w', encoding='utf-8', newline='') as flux:
        graveur = csv.writer(flux, delimiter=';')
        for ligne in nouvelles:
            graveur.writerow(ligne)
    return copie, recollees


def main():
    analyseur = argparse.ArgumentParser(
        description='Appliquer les bords propres et les textes corriges.')
    analyseur.add_argument('--ecrire', action='store_true',
                           help='ecrire vraiment (sinon : rapport seul)')
    options = analyseur.parse_args()

    plan, entete, corps = construire_plan()
    if plan is None:
        print('ARRET : %s est introuvable.' % CSV_TEXTE)
        return 2

    print('=' * 80)
    print(' APPLIQUER LES BORDS PROPRES ET LES TEXTES CORRIGES')
    print('=' * 80)
    print(' references : %s' % CSV_TEXTE)
    print('   %d voix, %d colonnes' % (len(corps), len(entete)))
    print(' lot        : %s' % LOT)
    print(' cache      : VERSION_CACHE, dans %s' % CACHE.name)
    print('')

    print(' 1) LES TEXTES A CORRIGER : %d' % len(plan['textes']))
    for changement in plan['textes']:
        print('    --- %s' % changement['voix'])
        print('        AVANT : %s' % changement['avant'])
        print('        APRES : %s' % changement['apres'])
    print('')
    print(' 2) LES REFERENCES A REMPLACER : %d' % len(plan['references']))
    if plan['manquantes']:
        print('    ATTENTION : %d voix du lot sans fichier en production : %s'
              % (len(plan['manquantes']), ', '.join(plan['manquantes'][:5])))
    print('')
    print(' 3) LES NOTES A RECOLLER : %d' % len(plan['orphelines']))
    for nom in plan['orphelines']:
        print('    %s  ->  %s' % (nom, sans_orphelin(nom)))
    print('')

    if not options.ecrire:
        print('=' * 80)
        print(' RAPPORT SEUL : rien n a ete ecrit. Ajoute --ecrire pour appliquer.')
        print('=' * 80)
        return 0

    if not plan['textes'] and not plan['references']:
        print('Rien a faire : tout est deja applique.')
        return 0

    print('=' * 80)
    print(' APPLICATION')
    print('=' * 80)
    # Les references D'ABORD : si un fichier manque, on veut le savoir AVANT
    # d'avoir touche au fichier des textes.
    garde, remplacees = ecrire_references(plan)
    print('  references remplacees : %d' % remplacees)
    print('  anciennes gardees dans : %s' % garde)
    if plan['textes']:
        copie = ecrire_textes(plan, entete, corps)
        print('  textes ecrits : %d   (copie : %s)'
              % (len(plan['textes']), copie.name))
    if plan['orphelines']:
        copie, recollees = recoller_les_notes()
        print('  notes recollees : %d   (copie : %s)' % (recollees, copie.name))
    avant_cache, apres_cache, copie_cache = monter_le_cache()
    if avant_cache is None:
        print('  ATTENTION : VERSION_CACHE n a PAS ete monte (a faire a la main)')
    else:
        print('  VERSION_CACHE : %d -> %d   (copie : %s)'
              % (avant_cache, apres_cache, copie_cache.name))

    # RELECTURE DE CONTROLE : ce qui devait changer a change.
    _entete_apres, corps_apres = lire_references()
    verifies = 0
    for changement in plan['textes']:
        ligne = corps_apres[changement['rang']]
        if len(ligne) >= 2 and ligne[1].strip() == changement['apres']:
            verifies += 1
    verifiees = sum(1 for item in plan['references']
                    if item['cible'].stat().st_size == item['apres'])
    print('')
    print(' RELECTURE : textes verifies %d sur %d'
          % (verifies, len(plan['textes'])))
    print('             references verifiees %d sur %d'
          % (verifiees, len(plan['references'])))

    print('')
    print('=' * 80)
    print(' A FAIRE MAINTENANT, ET C EST IMPORTANT')
    print('=' * 80)
    print('  1) FAIRE RECHARGER LES VOIX PAR LE SERVICE : il garde en memoire le')
    print('     texte ET l empreinte de chaque voix. Sans ca, il continuerait de')
    print('     parler avec les anciennes references, en silence.')
    print('     -> redemarrer le service Qwen (START.bat), ou appeler sa route')
    print('        /recharger (corrigee le 03/10 : elle oublie les empreintes).')
    print('  2) reecouter une voix Kyutai dans le lecteur pour confirmer.')
    print('')
    print(' RETOUR ARRIERE : recopier les fichiers *.bak_..._%s, et le contenu' % DATE)
    print('                  de %s' % garde)
    return 0


if __name__ == '__main__':
    sys.exit(main())
