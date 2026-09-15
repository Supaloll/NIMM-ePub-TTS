# -*- coding: utf-8 -*-
"""
Test de la gestion du moteur de voix Kyutai pendant une analyse locale
(session du 13/09/2026, demande de Laurent).

Ce qui est verifie, en vrai (une fenetre du moteur va s'ouvrir puis se
refermer, c'est normal) :
  1. le moteur de voix Kyutai demarre ;
  2. il est ETEINT quand on lance une analyse en local (la carte graphique
     doit etre libre pour le modele de langage) ;
  3. la memoire video est bien rendue ;
  4. il est RALLUME a la fin de l'analyse.

Lancer depuis la racine : python test_voix/test_gestion_kyutai.py
"""
import sys
import json
import time
import subprocess
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import main

OK = 0
ERR = 0


def verifier(condition, message):
    global OK, ERR
    if condition:
        OK += 1
        print('  OK  ' + message)
    else:
        ERR += 1
        print('  ERR ' + message)


def vram_utilisee():
    """Memoire video utilisee, en Mo (lecture seule)."""
    try:
        r = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=15)
        return int(r.stdout.strip().split('\n')[0])
    except Exception:
        return -1


def attendre_etat(voulu, secondes=90):
    """Attend que le moteur soit actif (ou eteint), jusqu'a `secondes`."""
    fin = time.time() + secondes
    while time.time() < fin:
        if main._moteur_kyutai_actif() == voulu:
            return True
        time.sleep(3)
    return main._moteur_kyutai_actif() == voulu


def moteur_pret():
    """Le moteur a-t-il FINI de charger son modele ? /sante repond des le
    demarrage, avec "pret": false pendant tout le chargement -- or c'est
    seulement une fois pret qu'il occupe vraiment la memoire video."""
    try:
        with urllib.request.urlopen('http://127.0.0.1:8082/sante', timeout=3) as r:
            return bool(json.loads(r.read().decode('utf-8')).get('pret'))
    except Exception:
        return False


def attendre_pret(secondes=120):
    fin = time.time() + secondes
    while time.time() < fin:
        if moteur_pret():
            return True
        time.sleep(3)
    return moteur_pret()


print('')
print('=' * 66)
print('GESTION DU MOTEUR DE VOIX KYUTAI PENDANT UNE ANALYSE LOCALE')
print('=' * 66)

# --- 1. Le moteur doit tourner (c'est la situation de depart de Laurent) ---
print('')
print('--- 1. Le moteur de voix doit etre allume ---')
if not main._moteur_kyutai_actif():
    print('     demarrage du moteur (comme START.bat)... patiente quelques secondes')
    main._relancer_moteur_kyutai()
    attendre_etat(True)
verifier(main._moteur_kyutai_actif(), 'le moteur Kyutai repond')
print('     attente de la fin du chargement du modele...')
attendre_pret()
vram_avant = vram_utilisee()
print('     memoire video utilisee : {} Mo'.format(vram_avant))

# --- 2. Analyse en local : on doit liberer la carte ---
print('')
print('--- 2. Lancement d\'une analyse en local (provider = local) ---')
main._liberer_la_carte_pour_analyse_locale()
attendre_etat(False, 60)
verifier(not main._moteur_kyutai_actif(), 'le moteur Kyutai a bien ete eteint')
verifier(main._kyutai_coupe_pour_casting, 'l\'application retient qu\'elle l\'a eteint (pour le rallumer)')
time.sleep(4)
vram_pendant = vram_utilisee()
print('     memoire video utilisee : {} Mo'.format(vram_pendant))
verifier(vram_pendant < vram_avant, 'de la memoire video a bien ete rendue')

# --- 3. Fin de l'analyse : le moteur doit revenir ---
print('')
print('--- 3. Fin de l\'analyse : le moteur doit se rallumer ---')
main._restaurer_moteur_kyutai()
attendre_etat(True, 90)
verifier(main._moteur_kyutai_actif(), 'le moteur Kyutai est de nouveau operationnel')
verifier(not main._kyutai_coupe_pour_casting, 'le drapeau interne est remis a zero')
print('     rechargement du modele : {}'.format(
    'termine' if attendre_pret() else 'encore en cours (normal, il finit seul)'))

print('')
print('=' * 66)
print('RESULTAT : %d OK, %d ERR' % (OK, ERR))
print('=' * 66)
sys.exit(1 if ERR else 0)
