# -*- coding: utf-8 -*-
"""RE-CASTER un livre entier (PAYANT) -- l'outil de Laurent.

POURQUOI IL EXISTE (question de Laurent, 17/09/2026 : « depuis mon interface, je
ne sais pas si je peux re-caster un livre qui le serait deja ») : NON, on ne peut
pas -- et c'est voulu. Le casting ne refait JAMAIS un chapitre deja analyse
(« plus jamais deux fois le meme chapitre paye »). Pour re-caster un livre, il
faut donc d'abord EFFACER son attribution. C'est ce que fait ce script, dans le
bon ordre et sans danger :

    1. COPIE DATEE de la base (le seul retour arriere) ;
    2. remise a zero de l'attribution du livre -- la FICHE des personnages est
       conservee, elle sert de fiche de depart au nouveau casting ;
    3. ESTIMATION du cout, puis CONFIRMATION (on ne part jamais sans un « oui ») ;
    4. lancement du casting, puis suivi de la progression chapitre par chapitre ;
    5. controles finaux : coherence de saga et voix lisibles.

Ce qui est REPRIS automatiquement : les voix des personnages deja castes sur les
AUTRES TOMES de la meme saga (meme si le moteur a change entre-temps -- seule
l'identifiant de la voix compte).

PAYANT : chaque appel d'IA est facture (compter ~0,30 $ pour un gros tome).
Sans `--je-paie`, le script s'arrete sans rien faire.

Usage :
    python test_voix/_PAYANT_recaster_un_livre.py 17 --je-paie
    python test_voix/_PAYANT_recaster_un_livre.py 17 --fournisseur gemini --je-paie
"""

import argparse
import json
import shutil
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

LECTEUR = "http://127.0.0.1:8081"
BASE = RACINE / 'data' / 'nimm_epub.db'


def appeler(chemin, methode="GET", timeout=3600):
    """Un appel au lecteur (qui porte la route de casting)."""
    requete = urllib.request.Request(LECTEUR + chemin, method=methode, data=b"")
    with urllib.request.urlopen(requete, timeout=timeout) as reponse:
        return json.loads(reponse.read().decode('utf-8'))


def etat_du_livre(book_id):
    """(phrases attribuees, chapitres attribues, personnages) du livre."""
    connection = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    phrases = connection.execute(
        'SELECT COUNT(1) FROM speaker_attribution WHERE book_id = ?',
        (book_id,)).fetchone()[0]
    chapitres = connection.execute(
        'SELECT COUNT(DISTINCT chapter_index) FROM speaker_attribution '
        'WHERE book_id = ?', (book_id,)).fetchone()[0]
    personnages = connection.execute(
        'SELECT COUNT(1) FROM voices WHERE book_id = ?', (book_id,)).fetchone()[0]
    connection.close()
    return phrases, chapitres, personnages


def main():
    analyseur = argparse.ArgumentParser(
        description="Re-caste un livre entier (PAYANT) : sauvegarde, remise a "
                    "zero, estimation, confirmation, lancement, suivi.")
    analyseur.add_argument('book_id', type=int, help="numero du livre (voir la base)")
    analyseur.add_argument('--fournisseur', default='gemini',
                           choices=('gemini', 'mistral', 'deepseek'))
    analyseur.add_argument('--user', type=int, default=1, help="numero d'utilisateur (1 par defaut)")
    analyseur.add_argument('--je-paie', action='store_true',
                           help="OBLIGATOIRE : confirme qu'on accepte de payer les appels d'IA")
    options = analyseur.parse_args()

    if not options.je_paie:
        print('')
        print('  ATTENTION : ce script fait des appels d\'IA FACTURES.')
        print('  Il ne partira pas sans l\'option  --je-paie.')
        return 2

    # 1) Le lecteur repond-il ? (c'est lui qui porte la route de casting)
    try:
        livre = appeler('/api/books/%d?user_id=%d' % (options.book_id, options.user),
                        timeout=30)
    except Exception as erreur:
        print('ERR : le lecteur ne repond pas (%s).' % erreur)
        print('      Double-clique sur START.bat, puis relance ce script.')
        return 1

    print('')
    print('=' * 74)
    print('RE-CAST COMPLET D UN LIVRE  --  fournisseur : %s' % options.fournisseur)
    print('=' * 74)
    print('livre %s : %s' % (options.book_id, livre.get('title')))

    phrases, chapitres, personnages = etat_du_livre(options.book_id)
    print('  a effacer   : %d phrase(s) sur %d chapitre(s)' % (phrases, chapitres))
    print('  personnages : %d (les voix du nouveau casting suivront la saga)' % personnages)

    # 2) Copie datee de la base AVANT toute modification.
    horodatage = datetime.now().strftime('%Y%m%d_%H%M')
    copie = BASE.with_name('%s.bak_avant_recaste_%s_%s'
                           % (BASE.name, options.book_id, horodatage))
    shutil.copy2(str(BASE), str(copie))
    print('')
    print('  COPIE DE SURETE : %s' % copie.name)
    print('  (pour revenir en arriere : recopier ce fichier sur la base)')

    # 3) Remise a zero de l'attribution (la fiche des personnages est conservee).
    connection = sqlite3.connect(str(BASE))
    with connection:
        connection.execute('DELETE FROM speaker_attribution WHERE book_id = ?',
                           (options.book_id,))
        connection.execute("UPDATE books SET cast_status = 'none' WHERE id = ?",
                           (options.book_id,))
    connection.close()
    print('  attribution effacee : le prochain casting refera TOUT le livre.')

    # 4) Estimation du cout, puis confirmation.
    estimation = appeler('/api/books/%d/cast/estimate?user_id=%d&provider=%s'
                         % (options.book_id, options.user, options.fournisseur))
    print('')
    print('  ESTIMATION : %s chapitres, %s phrases, %s appels  ->  %s'
          % (estimation.get('chapters'), estimation.get('sentences'),
             estimation.get('calls'), estimation.get('cost_display')))

    reponse = input('\n  Lancer le casting maintenant ? (oui / non) : ')
    if reponse.strip().lower() not in ('oui', 'o', 'yes', 'y'):
        print('')
        print('  Arret demande : rien n\'a ete lance.')
        print('  L\'attribution du livre a ete effacee -- la copie de surete est :')
        print('  %s' % copie.name)
        return 0

    # 5) Lancement, puis suivi de la progression.
    print('')
    print('  Lancement... (le premier chapitre part tout de suite)')
    try:
        depart = appeler('/api/books/%d/cast?user_id=%d&provider=%s'
                         % (options.book_id, options.user, options.fournisseur),
                         methode="POST", timeout=900)
        print('  reponse du lecteur : %s' % json.dumps(depart, ensure_ascii=False))
    except Exception as erreur:
        print('ERR : le lancement a echoue (%s)' % erreur)
        return 1

    precedent = ''
    while True:
        time.sleep(6)
        try:
            statut = appeler('/api/books/%d/cast/status?user_id=%d'
                             % (options.book_id, options.user), timeout=30)
        except Exception:
            continue
        etat = statut.get('cast_status', '?')
        if etat != precedent:
            print('  %s' % etat)
            precedent = etat
        if etat == 'done' or etat.startswith('error'):
            break

    print('')
    phrases, chapitres, personnages = etat_du_livre(options.book_id)
    print('TERMINE : %d personnage(s), %d phrase(s) sur %d chapitre(s).'
          % (personnages, phrases, chapitres))
    print('')
    print('CONTROLES A LANCER MAINTENANT (le lanceur double-clic les enchainent) :')
    print('  python test_voix/_controler_saga.py "%s"' % (livre.get('saga') or ''))
    print('  python test_voix/_controler_voix_kyutai.py')
    print('')
    print('RETOUR ARRIERE : recopier %s sur data/nimm_epub.db' % copie.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
