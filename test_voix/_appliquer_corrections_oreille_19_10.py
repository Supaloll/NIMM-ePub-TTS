# -*- coding: utf-8 -*-
"""APPLIQUER LES CORRECTIONS D'OREILLE DE LAURENT (19/10/2026).

POURQUOI. Laurent a relu les neuf voix dans `CORRIGER_LES_TEXTES_DES_VOIX.bat`
et a enregistre `_corrections_oreille.csv` a la racine de NIMM ePub. Ce script
reporte ses textes dans les DEUX fichiers que lit le service Qwen :

    qwen_tts_service/voix/references.csv           (voix publiques)
    qwen_tts_service/voix/references_privees.csv   (Maya, hors Git)

Il ne touche QUE la colonne du texte des neuf voix signalees. Les durees, les
hauteurs, les sources et toutes les autres voix restent identiques.

DEUX PRECAUTIONS :
  - le crochet `[` que Laurent met devant un mot coupe (`[tait...`) est une
    NOTATION, pas une parole : il est retire avant l'ecriture ;
  - copies datees des deux CSV AVANT toute ecriture, puis relecture : les neuf
    textes doivent etre la, et aucune autre ligne ne doit avoir bouge.

Usage :
    python test_voix/_appliquer_corrections_oreille_19_10.py          # rapport
    python test_voix/_appliquer_corrections_oreille_19_10.py --ecrire # applique
"""
import argparse
import csv
import shutil
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

CORRECTIONS = RACINE / '_corrections_oreille.csv'
VOIX = RACINE / 'qwen_tts_service' / 'voix'
FICHIERS = (
    (VOIX / 'references.csv', 'public'),
    (VOIX / 'references_privees.csv', 'prive'),
)
SUFFIXES = ('_enhanced_reference.wav', '_reference.wav')

NOMS = {
    'Homme002', 'Homme004', 'Maya_normale', 'cml1649', 'cml1840',
    'cml1869', 'cml2316', 'cml3182', 'homme_aigu_6877654',
}


def nom_court(fichier):
    for suffixe in SUFFIXES:
        if fichier.endswith(suffixe):
            return fichier[:-len(suffixe)]
    return fichier


def lire_corrections():
    """{nom court: texte entendu}, avec le crochet de notation retire."""
    if not CORRECTIONS.is_file():
        raise SystemExit('introuvable : %s' % CORRECTIONS)
    textes = {}
    with open(CORRECTIONS, encoding='utf-8-sig', newline='') as fichier:
        for ligne in csv.reader(fichier, delimiter=';'):
            if len(ligne) < 2 or ligne[0].strip() not in NOMS:
                continue
            texte = ligne[1].strip()
            if texte.startswith('['):
                texte = texte[1:].lstrip()
            textes[ligne[0].strip()] = texte
    return textes


def lire_csv(chemin):
    with open(chemin, encoding='utf-8-sig', newline='') as fichier:
        return list(csv.reader(fichier, delimiter=';'))


def fin_de_ligne(chemin):
    brut = chemin.read_bytes()
    return '\r\n' if b'\r\n' in brut else '\n'


def ecrire_csv(chemin, lignes, fin):
    with open(chemin, 'w', encoding='utf-8', newline='') as fichier:
        graveur = csv.writer(fichier, delimiter=';', lineterminator=fin)
        graveur.writerows(lignes)


def main():
    options = argparse.ArgumentParser(
        description='Applique les corrections d oreille aux textes Qwen.')
    options.add_argument('--ecrire', action='store_true',
                         help='applique (copies datees avant) ; sans, rapport seul')
    options = options.parse_args()

    textes = lire_corrections()
    manquants = NOMS - set(textes)
    if manquants:
        raise SystemExit('corrections manquantes : %s' % ', '.join(sorted(manquants)))

    print('Corrections lues : %d' % len(textes))
    for nom in sorted(textes):
        print('  %-22s %4d car.  debut=%s'
              % (nom, len(textes[nom]), ascii(textes[nom][:45])))
    print('')

    # Rapport : ce qui changerait, fichier par fichier.
    plans = []
    for chemin, etiquette in FICHIERS:
        if not chemin.is_file():
            print('ABSENT : %s' % chemin)
            continue
        lignes = lire_csv(chemin)
        changes = []
        for ligne in lignes[1:]:
            if len(ligne) < 2 or not ligne[0].strip():
                continue
            court = nom_court(ligne[0].strip())
            if court in textes and ligne[1] != textes[court]:
                changes.append((ligne[0].strip(), ligne[1], textes[court]))
        print('%s : %d ligne(s) a changer' % (etiquette, len(changes)))
        for fichier, avant, apres in changes:
            print('  %s' % fichier)
            print('    avant : %s' % ascii(avant[:100]))
            print('    apres : %s' % ascii(apres[:100]))
        plans.append((chemin, etiquette, lignes, changes))

    if not options.ecrire:
        print('\nRAPPORT SEUL : rien n a ete ecrit.')
        return 0

    horodatage = time.strftime('%Y%m%d_%H%M')
    for chemin, etiquette, lignes, changes in plans:
        if not changes:
            continue
        copie = chemin.with_name(
            chemin.name + '.bak_avant_corrections_laurent_' + horodatage)
        shutil.copy2(chemin, copie)
        print('\nCopie datee (%s) : %s' % (etiquette, copie.name))
        for ligne in lignes[1:]:
            if len(ligne) < 2 or not ligne[0].strip():
                continue
            court = nom_court(ligne[0].strip())
            if court in textes:
                ligne[1] = textes[court]
        ecrire_csv(chemin, lignes, fin_de_ligne(copie))

    # Relecture de controle : les neuf textes, et rien d'autre qui bouge.
    echecs = 0
    for chemin, etiquette, lignes_avant, changes in plans:
        relu = lire_csv(chemin)
        par_fichier = {ligne[0].strip(): ligne for ligne in relu[1:]
                       if ligne and ligne[0].strip()}
        for fichier, _avant, _apres in changes:
            court = nom_court(fichier)
            if (par_fichier.get(fichier) or ['', ''])[1] != textes[court]:
                print('  ECHEC : %s n a pas le bon texte' % fichier)
                echecs += 1
        # Toutes les lignes hors des neuf doivent etre identiques a l'avant.
        avant_par_fichier = {ligne[0].strip(): ligne for ligne in lignes_avant[1:]
                             if ligne and ligne[0].strip()}
        for fichier, ligne in par_fichier.items():
            if nom_court(fichier) in textes:
                continue
            if avant_par_fichier.get(fichier) != ligne:
                print('  ECHEC : ligne modifiee par erreur : %s' % fichier)
                echecs += 1
        print('%s : %d ligne(s), %d changement(s) controle(s)'
              % (etiquette, len(relu) - 1, len(changes)))

    if echecs:
        print('\n%d ERREUR(S)' % echecs)
        return 1
    print('\nTOUT EST OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())

