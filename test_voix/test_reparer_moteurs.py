# -*- coding: utf-8 -*-
"""Script JETABLE -- verifie le voyant « Reparer » et le veilleur Pocket TTS.

Ecrit le 21/09/2026, apres la panne racontee par Laurent : « j'ai clique par
erreur sur la ligne tout en bas, qui me permet de changer de serveur,
apparemment ca a coupe le moteur POCKET TTS. Je ne trouve plus les voix a
l'interieur du casting. »

Ce que le script controle, SANS RIEN LANCER (aucun moteur, aucun lecteur,
aucune fenetre) :
  1. START.bat allume Pocket TTS AVANT le choix du moteur lourd -- c'est LA
     cause de la panne : le bloc Pocket vivait apres les « goto lecteur » de
     Kyutai, donc il n'etait JAMAIS atteint ;
  2. « attendu » : Pocket TTS l'est toujours (il cohabite) ; XTTS, non ;
  3. le veilleur rallume Pocket TTS quand il le trouve eteint, dit pourquoi, et
     respecte son delai de repos (pas d'essais en rafale) ;
  4. le lancement sans fenetre vise le bon script, dans le bon dossier, avec le
     python du service ;
  5. les deux routes du panneau existent bien en POST ;
  6. l'auto-extinction du service Pocket TTS est passee a 180 minutes.

A lancer depuis la racine : python test_voix/test_reparer_moteurs.py
"""

import inspect
import io
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

import main

ECHECS = 0
TEMOIN = RACINE / "test_voix" / "_test_moteur_retenu_reparer.txt"


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def main_test():
    # --- 1. START.bat : la non-regression de la panne du jour -------------
    print('')
    print('1) START.bat allume Pocket TTS AVANT le choix du moteur lourd')
    bat = (RACINE / "START.bat").read_text(encoding="utf-8", errors="replace")
    i_pocket = bat.find("http://127.0.0.1:8085/sante")
    i_kyutai = bat.find("http://127.0.0.1:8082/sante")
    verifier('le port 8085 (Pocket TTS) est teste AVANT le port 8082 (Kyutai)',
             i_pocket > 0 and i_kyutai > 0 and i_pocket < i_kyutai,
             'pocket=%s kyutai=%s' % (i_pocket, i_kyutai))
    verifier('le bloc Pocket TTS ne renvoie plus au lecteur (:pocket_pret)',
             bat.count(':pocket_pret') == 1, bat.count(':pocket_pret'))
    if i_pocket > 0 and ':pocket_pret' in bat:
        bloc = bat[i_pocket:bat.find(':pocket_pret')]
        verifier('aucun « goto lecteur » ne saute plus ce bloc',
                 'goto lecteur' not in bloc, bloc[:120])
        verifier('le bloc lance bien le service Pocket TTS',
                 'DEMARRER_POCKET_TTS.bat' in bloc)
    verifier('le service a sa FENETRE (fermer la fenetre eteint le moteur)',
             'cmd /k DEMARRER_POCKET_TTS.bat' in bat)
    verifier('START.bat efface le marqueur d arret volontaire',
             'arrete_volontaire.txt' in bat)

    # --- 2. Quels moteurs sont ATTENDUS ? --------------------------------
    print('')
    print('2) quels moteurs sont attendus (le voyant ne parle que de ceux-la)')
    vrai_chemin = main.MOTEUR_VOIX_PATH
    try:
        TEMOIN.write_text("kyutai\n", encoding="utf-8")
        main.MOTEUR_VOIX_PATH = TEMOIN
        attendus = main.moteurs_attendus()
        verifier('Pocket TTS est TOUJOURS attendu (il cohabite)',
                 'pocket' in attendus, attendus)
        verifier('le moteur lourd retenu est attendu', 'kyutai' in attendus, attendus)
        verifier('les moteurs lourds non retenus ne sont pas attendus',
                 'xtts' not in attendus and 'neutts' not in attendus, attendus)

        TEMOIN.write_text("aucun\n", encoding="utf-8")
        aucun = main.moteurs_attendus()
        verifier('avec « aucun » enregistre, seul Pocket TTS est attendu',
                 aucun == ['pocket'], aucun)

        TEMOIN.write_text("pocket\n", encoding="utf-8")
        avec_pocket = main.moteurs_attendus()
        verifier('« pocket » dans le pense-bete ne le compte pas deux fois',
                 avec_pocket == ['pocket'], avec_pocket)
    finally:
        main.MOTEUR_VOIX_PATH = vrai_chemin
        if TEMOIN.exists():
            TEMOIN.unlink()

    # --- 3. L'etat porte cohabite / attendu ------------------------------
    print('')
    print('3) l etat des moteurs porte « cohabite » et « attendu »')
    vraie_sante = main._sante_moteur
    try:
        main._sante_moteur = lambda url: {"actif": False, "pret": False}
        etat = main.etat_moteurs_voix(force=True)
        verifier('chaque moteur dit s il cohabite',
                 etat['pocket']['cohabite'] is True
                 and etat['kyutai']['cohabite'] is False)
        verifier('chaque moteur dit s il est attendu',
                 etat['pocket']['attendu'] is True)
    finally:
        main._sante_moteur = vraie_sante
        main._ETAT_MOTEURS["etat"] = None

    # --- 4. Le veilleur rallume Pocket TTS -------------------------------
    print('')
    print('4) le veilleur rallume Pocket TTS, sans essais en rafale')
    vrai_demarrer = main._demarrer_pocket_avec_fenetre
    vrai_etat = main.etat_moteurs_voix
    vrai_installe = main._moteur_voix_installe
    try:
        rallumes = []

        def faux_demarrer():
            rallumes.append(1)
            return True

        main._demarrer_pocket_avec_fenetre = faux_demarrer
        main._moteur_voix_installe = lambda prefixe: True
        main.etat_moteurs_voix = lambda force=False: {
            "pocket": {"actif": False, "pret": False, "cohabite": True,
                       "attendu": True}}
        main._veilleur_pocket.update(
            {"dernier_essai": 0.0, "echecs": 0, "lancements": 0})

        resultat = main._assurer_pocket_vivant()
        verifier('moteur eteint : le veilleur le rallume',
                 resultat.get('lance') is True, resultat)
        verifier('et il le DIT (message lisible)',
                 'relanc' in str(resultat.get('message')), resultat.get('message'))

        resultat2 = main._assurer_pocket_vivant()
        verifier('pas deux essais coup sur coup (delai de repos)',
                 resultat2.get('lance') is False, resultat2)
        verifier('un seul lancement a eu lieu', len(rallumes) == 1, len(rallumes))

        resultat3 = main._assurer_pocket_vivant(force=True)
        verifier('un clic de Laurent force le nouvel essai',
                 resultat3.get('lance') is True, resultat3)

        main.etat_moteurs_voix = lambda force=False: {
            "pocket": {"actif": True, "pret": False, "cohabite": True,
                       "attendu": True}}
        resultat4 = main._assurer_pocket_vivant(force=True)
        verifier('moteur en cours de chargement : on ne le relance pas',
                 resultat4.get('lance') is False
                 and 'deja' in str(resultat4.get('message')), resultat4)

        main._moteur_voix_installe = lambda prefixe: False
        main.etat_moteurs_voix = lambda force=False: {
            "pocket": {"actif": False, "pret": False, "cohabite": True,
                       "attendu": True}}
        resultat5 = main._assurer_pocket_vivant(force=True)
        verifier('moteur non installe : refus clair, aucun lancement',
                 resultat5.get('lance') is False
                 and 'installe' in str(resultat5.get('message')), resultat5)

        # NOUVEAU (21/09/2026) : un arret VOLONTAIRE -- la fenetre du moteur a
        # ete fermee -- ne doit pas etre contredit par le veilleur. Sans ce
        # controle, Laurent fermait la fenetre et le moteur revenait moins d'une
        # minute plus tard : le geste n'aurait servi a rien.
        vrai_marqueur = main._pocket_arrete_volontairement
        main._pocket_arrete_volontairement = lambda: True
        main._moteur_voix_installe = lambda prefixe: True
        main.etat_moteurs_voix = lambda force=False: {
            "pocket": {"actif": False, "pret": False, "cohabite": True,
                       "attendu": True}}
        main._veilleur_pocket.update(
            {"dernier_essai": 0.0, "echecs": 0, "lancements": 0})
        avant = len(rallumes)
        resultat6 = main._assurer_pocket_vivant()
        verifier('arret volontaire : le veilleur ne rallume RIEN',
                 resultat6.get('lance') is False
                 and 'volontairement' in str(resultat6.get('message')),
                 resultat6)
        verifier('et aucun lancement n a eu lieu', len(rallumes) == avant,
                 len(rallumes))
        resultat7 = main._assurer_pocket_vivant(force=True)
        verifier('mais un clic de Laurent (« Relancer les moteurs ») rallume',
                 resultat7.get('lance') is True, resultat7)
        main._pocket_arrete_volontairement = vrai_marqueur
    finally:
        main._demarrer_pocket_avec_fenetre = vrai_demarrer
        main.etat_moteurs_voix = vrai_etat
        main._moteur_voix_installe = vrai_installe
        main._veilleur_pocket.update(
            {"dernier_essai": 0.0, "echecs": 0, "lancements": 0})

    # --- 5. La commande de lancement AVEC fenetre -------------------------
    print('')
    print('5) la commande de lancement (fenetre visible, comme Kyutai)')
    vraie_popen = subprocess.Popen
    captures = []

    def faux_popen(argv, **kwargs):
        captures.append((argv, kwargs))
        return None

    try:
        subprocess.Popen = faux_popen
        lance = vrai_demarrer()
    finally:
        subprocess.Popen = vraie_popen
    verifier('le lancement part bien', lance is True)
    verifier('un seul processus demande', len(captures) == 1, len(captures))
    if captures:
        argv = captures[0][0]
        verifier('c est le LANCEUR du service qui est appele',
                 argv[0] == 'cmd' and argv[-1] == 'DEMARRER_POCKET_TTS.bat',
                 argv)
        verifier('la fenetre du moteur s ouvre (CREATE_NEW_CONSOLE)',
                 captures[0][1].get('creationflags')
                 == subprocess.CREATE_NEW_CONSOLE,
                 captures[0][1].get('creationflags'))

    # --- 6. Les routes du panneau ----------------------------------------
    print('')
    print('6) les routes du panneau « Reparer »')
    chemins = {}
    for route in main.app.routes:
        chemin = getattr(route, "path", "")
        if chemin:
            chemins[chemin] = getattr(route, "methods", set()) or set()
    verifier('la route « relancer les moteurs » existe en POST',
             'POST' in chemins.get('/api/moteurs/relancer', set()),
             sorted(chemins.keys()))
    verifier('la route « redemarrer NIMM ePub » existe en POST',
             'POST' in chemins.get('/api/serveur/redemarrer', set()))
    verifier('l ancienne route de bascule est conservee',
             '/api/moteur/basculer' in chemins)
    verifier('START.bat est bien trouve sur le disque',
             main.START_BAT_PATH.exists(), main.START_BAT_PATH)
    verifier('le redemarrage ne bloque pas la reponse (coroutine)',
             inspect.iscoroutinefunction(main._lancer_start_bat_apres_reponse))
    verifier('le veilleur ne bloque pas les requetes (coroutine)',
             inspect.iscoroutinefunction(main._veiller_moteurs))

    # --- 7. Branchement et reglages --------------------------------------
    print('')
    print('7) branchement et reglages')
    source = (RACINE / "main.py").read_text(encoding="utf-8")
    verifier('le veilleur est demarre avec le lecteur',
             'create_task(_veiller_moteurs())' in source)
    pocket_py = (RACINE / "pocket_tts_service"
                 / "servir_pocket_tts.py").read_text(encoding="utf-8")
    verifier('l auto-extinction est passee a 180 min (30 min endormait en pleine ecoute)',
             'NIMM_POCKET_TTS_INACTIF", "180"' in pocket_py)

    print('')
    print('=' * 66)
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('=' * 66)
    return ECHECS


if __name__ == '__main__':
    sys.exit(1 if main_test() else 0)
