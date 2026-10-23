# -*- coding: utf-8 -*-
"""LES NEUF TEXTES CORRIGES PAR LAURENT SONT-ILS BIEN EN PRODUCTION ?

POURQUOI (19/10/2026). Laurent a relu les neuf voix dans la fenetre d'ecoute ;
son CSV est la source de verite. Ce test compare, pour les neuf, le texte du CSV
d'oreille au texte que le service Qwen lira vraiment :

    qwen_tts_service/voix/references.csv           (public)
    qwen_tts_service/voix/references_privees.csv   (Maya, hors Git)

Il verifie aussi que Maya est bien dans le PRIVE (pas dans le public), et que le
crochet `[` de notation (`[tait...`) a bien ete retire.

Usage : python test_voix/test_corrections_voix_appliquees.py
"""
import csv
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
VOIX = RACINE / 'qwen_tts_service' / 'voix'
OREILLE = RACINE / 'test_voix' / '_corrections_oreille.csv'
OREILLE_PRIVEES = RACINE / 'test_voix' / '_corrections_oreille_privees.csv'
SUFFIXES = ('_enhanced_reference.wav', '_reference.wav')
NOMS = {
    'Homme002', 'Homme004', 'Maya_normale', 'cml1649', 'cml1840',
    'cml1869', 'cml2316', 'cml3182', 'homme_aigu_6877654',
}
# Deux textes ont ete RACCOURCIS le 20/10/2026 parce que leur audio a ete
# recoupe sur un mot complet (Theodore : debut ; Aubin : fin). Les sept autres
# doivent rester exactement ceux du CSV d'oreille.
TEXTES_REPARES = {
    'Homme002': "Le château des seigneurs d'Albray, où Marguerite d'Angoulême "
                "avait tenu sa cour, mis au monde sa fille Jeanne, et où son "
                "petit-fils, Henri, avait passé sa jeunesse, était redevenu "
                "une forteresse du Moyen-Âge.",
    'homme_aigu_6877654': "Le 24 février 1815, la vigie de Notre-Dame de la "
                          "Garde signala le trois-mats le Pharaon venant de "
                          "Smyrne, Trieste et Naples.",
}
sys.stdout.reconfigure(encoding='utf-8')

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def nom_court(fichier):
    for suffixe in SUFFIXES:
        if fichier.endswith(suffixe):
            return fichier[:-len(suffixe)]
    return fichier


def lire_un_fichier(chemin):
    textes = {}
    if not chemin.is_file():
        return textes
    with open(chemin, encoding='utf-8-sig', newline='') as fichier:
        for ligne in csv.reader(fichier, delimiter=';'):
            if len(ligne) >= 2 and ligne[0].strip() in NOMS:
                texte = ligne[1].strip()
                if texte.startswith('['):
                    texte = texte[1:].lstrip()
                textes[ligne[0].strip()] = texte
    return textes


def lire_corrections():
    """Les corrections des DEUX fichiers : public + prive (Maya)."""
    textes = {}
    for chemin in (OREILLE, OREILLE_PRIVEES):
        textes.update(lire_un_fichier(chemin))
    return textes


def lire_references(chemin):
    with open(chemin, encoding='utf-8-sig', newline='') as fichier:
        lignes = list(csv.reader(fichier, delimiter=';'))
    return {nom_court(ligne[0].strip()): ligne[1].strip()
            for ligne in lignes[1:] if len(ligne) >= 2 and ligne[0].strip()}


def main():
    corrections = lire_corrections()
    public = lire_references(VOIX / 'references.csv')
    prive = lire_references(VOIX / 'references_privees.csv')

    print('Corrections d oreille : %d voix' % len(corrections))
    print('Public : %d voix | Prive : %d voix' % (len(public), len(prive)))

    print('')
    print('1) les neuf textes sont ceux de Laurent (ou ceux des coupes)')
    for nom in sorted(NOMS):
        attendu = TEXTES_REPARES.get(nom) or corrections.get(nom)
        obtenu = (prive if nom == 'Maya_normale' else public).get(nom)
        verifier(nom, attendu is not None and obtenu == attendu,
                 'attendu=%s obtenu=%s' % (ascii((attendu or '')[:50]),
                                           ascii((obtenu or '')[:50])))
    verifier('Theodore : texte raccourci apres la coupe',
             len(public.get('Homme002', '')) < len(corrections.get('Homme002', '')))
    verifier('Aubin : texte raccourci apres la coupe',
             len(public.get('homme_aigu_6877654', ''))
             < len(corrections.get('homme_aigu_6877654', '')))

    print('')
    print('2) Maya est dans le PRIVE, pas dans le public')
    verifier('Maya absente du public', 'Maya_normale' not in public)
    verifier('Maya presente dans le prive', 'Maya_normale' in prive)

    print('')
    print('3) le crochet de notation a disparu')
    verifier('aucun texte ne commence par « [ »',
             all(not texte.startswith('[') for texte in corrections.values()))

    print('')
    print('4) les corrections privees sont dans un fichier SEPARE')
    corr_public = lire_un_fichier(OREILLE)
    corr_prive = lire_un_fichier(OREILLE_PRIVEES)
    verifier('Maya absente du CSV public', 'Maya_normale' not in corr_public)
    verifier('Maya presente dans le CSV prive', 'Maya_normale' in corr_prive)

    print('')
    print('TOUT EST OK' if ECHECS == 0 else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
