# -*- coding: utf-8 -*-
"""LA FENETRE D'ECOUTE AFFICHE-T-ELLE LES PRENOMS ? (19/10/2026)

POURQUOI (retour de Laurent) : dans `CORRIGER_LES_TEXTES_DES_VOIX.bat`, les
voix s'appelaient `Homme002`, `cml1840`... -- des noms de FICHIERS, pas les
prenoms qu'il connait. La page lit maintenant le catalogue (`modules/tts.py`)
et affiche « Theodore (Homme002) ».

Ce que ce test verifie, SANS lancer la page ni le serveur :
  1. les neuf voix signalees le 19/10/2026 sont bien la, avec leur PRENOM ;
  2. Maya est presente : elle vit dans `references_privees.csv`, que l'outil
     doit lire EN PLUS du public (sinon elle manquait : 8 sur 9) ;
  3. aucune voix n'est en double ;
  4. le catalogue ne perd pas de voix (au moins 206).

Usage : python test_voix/test_outil_ecoute_prenoms.py
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / 'test_voix'))
sys.stdout.reconfigure(encoding='utf-8')

import _corriger_references_a_l_oreille as outil  # noqa: E402

ATTENDU = {
    'Homme002': 'Théodore',
    'Homme004': 'Édouard',
    'homme_aigu_6877654': 'Aubin',
    'Maya_normale': 'Maya',
    'cml1840': 'Achille',
    'cml1649': 'Berthe',
    'cml1869': 'Cécile',
    'cml2316': 'Joséphine',
    'cml3182': 'Maurice',
}

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def main():
    voix = outil.lire_references()
    par_nom = {v['nom']: v for v in voix}
    print('Voix lues : %d' % len(voix))

    print('')
    print('1) les neuf voix signalees, avec leur prenom')
    for nom, prenom in sorted(ATTENDU.items()):
        fiche = par_nom.get(nom)
        verifier('%s -> %s' % (nom, prenom),
                 fiche is not None and fiche.get('prenom') == prenom
                 and fiche.get('signalee') is True,
                 fiche and (fiche.get('prenom'), fiche.get('signalee')))

    print('')
    print('2) Maya vient du fichier prive')
    maya = par_nom.get('Maya_normale')
    verifier('Maya est dans la liste', maya is not None)
    verifier('son texte prive est lu', bool(maya and maya.get('texte')))
    verifier('elle est marquee « a reprendre »', bool(maya and maya.get('signalee')))

    print('')
    print('3) aucune voix en double')
    verifier('autant de noms que de voix', len(par_nom) == len(voix),
             '%d noms pour %d voix' % (len(par_nom), len(voix)))

    print('')
    print('4) le catalogue ne perd pas de voix')
    verifier('au moins 206 voix', len(voix) >= 206, len(voix))
    verifier('exactement 9 signalees',
             sum(1 for v in voix if v.get('signalee')) == 9,
             sum(1 for v in voix if v.get('signalee')))

    print('')
    print('TOUT EST OK' if ECHECS == 0 else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
