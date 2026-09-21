# -*- coding: utf-8 -*-
"""Script JETABLE -- verifie la logique de demarrage des moteurs de voix.

REGLE EN VIGUEUR DEPUIS LE 21/09/2026 :
  - POCKET TTS demarre TOUJOURS, et AVANT le choix du moteur lourd : il tourne
    sur le processeur, il cohabite avec tout le monde, et ses 18 voix doivent
    etre proposables dans le casting des l'ouverture ;
  - le moteur LOURD est KYUTAI, quel que soit ce qu'ecrit data\\moteur_voix.txt
    (« aucun » excepte : la, pas de moteur lourd du tout). XTTS v2 et NeuTTS
    restent lancables a la main, par leur propre lanceur.

Ce que le script controle, sans RIEN lancer (ni moteur, ni lecteur) :
  1. les trois lanceurs ecrivent bien leur nom dans data\\moteur_voix.txt ;
  2. START.bat lit ce fichier : « aucun » -> pas de moteur lourd, toute autre
     valeur (y compris vide ou inconnue) -> Kyutai, et un message clair quand le
     fichier dit encore « xtts » ou « neutts » ;
  3. les garde-fous : les ports 8085 (Pocket) et 8082 (Kyutai) sont testes avant
     tout lancement, l'absence d'environnement n'empeche pas le lecteur de
     demarrer, Pocket TTS part SANS fenetre, et les anciens blocs
     (moteur_xtts / moteur_kyutai) ont bien disparu ;
  4. le piege des parentheses dans un bloc cmd (lecon du 14/09/2026).

Methode : une COPIE de START.bat est fabriquee avec TOUTES les commandes qui
lancent reellement quelque chose (le lanceur de Kyutai, celui de Pocket TTS,
`python main.py`) remplacees par des affichages, et le « pause » final retire.
Rien n'est donc execute.

ATTENTION (revision du 21/09/2026) : cette neutralisation avait cesse de
fonctionner sans qu'on s'en apercoive. Deux consequences, toutes les deux
reelles :
  - les motifs a remplacer dataient de l'epoque NeuTTS, et la ligne de Kyutai
    passait au travers : le test lancait donc pour de vrai le lanceur du moteur,
    sept fois de suite ;
  - le GARDE-FOU de START.bat (« j'arrete le serveur qui ecoute sur 8081 ») n'
    etait pas neutralise du tout : **le test tuait le lecteur de Laurent**.
Le controle « la copie neutre ne lance plus rien » (section 2 bis) empeche que
cela recommence.

A lancer avec le Python du lecteur :
    python test_voix/test_start_moteur.py
"""

import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

REGLE = RACINE / "data" / "moteur_voix.txt"
COPIE = RACINE / "_test_start_neutre.bat"
ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def fabriquer_copie_neutre():
    """Copie de START.bat ou rien ne se lance vraiment."""
    source = (RACINE / "START.bat").read_text(encoding='utf-8', errors='replace')
    remplacements = [
        ('start "NIMM ePub - appareil de voix Kyutai" /D "%~dp0kyutai_service" cmd /k DEMARRER_KYUTAI.bat',
         'echo [NEUTRE] ici serait lance : Kyutai'),
        ('python main.py', 'echo [NEUTRE] ici le lecteur demarrerait'),
        ('pause', ''),
    ]
    for avant, apres in remplacements:
        source = source.replace(avant, apres)
    # Pocket TTS : lancee par PowerShell, en arriere-plan (une seule ligne).
    source = re.sub(r'(?m)^powershell -NoProfile -Command "Start-Process.*pocket_tts_service.*$',
                    'echo [NEUTRE] ici serait lance : Pocket TTS (sans fenetre)',
                    source)
    # Le GARDE-FOU du 18/09/2026 arrete le serveur qui ecoute sur 8081 -- donc,
    # dans cette copie, il ARRETAIT POUR DE VRAI le lecteur de Laurent
    # (constate le 21/09/2026 : le lecteur est mort pendant le test, deux fois).
    # Meme traitement que le reste : on remplace par un affichage.
    # ATTENTION : ces deux lignes sont INDENTEES dans START.bat (elles vivent
    # dans un bloc « if not errorlevel 1 ( ... ) ») -- d'ou le [ \t]* : sans lui,
    # le remplacement ne s'applique pas et le lecteur se fait tuer pour de vrai.
    source = re.sub(r'(?m)^[ \t]*powershell -NoProfile -Command "\$pids.*$',
                    'echo [NEUTRE] ici serait arrete le serveur du port 8081',
                    source)
    # `timeout` refuse une entree redirigee (le test en redirige une) : sans
    # cette ligne, il ecrit une erreur sur stderr a chaque execution.
    source = re.sub(r'(?m)^[ \t]*timeout /t 2.*$',
                    'echo [NEUTRE] pause de 2 s (passee)',
                    source)
    # `newline="\r\n"` : INDISPENSABLE. `read_text()` a converti les fins de ligne
    # en LF, et un .bat ecrit en LF fait DERAILLER cmd -- il execute alors le
    # texte de ses propres commentaires (constate le 21/09/2026 : la copie a
    # lance pour de vrai le moteur Kyutai, et un diagnostic a lance NeuTTS).
    # REGLE DU PROJET : un .bat s'ecrit TOUJOURS en CRLF.
    COPIE.write_text(source, encoding='utf-8', newline="\r\n")
    return source


def lancer_start(contenu_regle):
    """Ecrit le fichier de regle demande puis execute la copie neutre.

    Le CHEMIN COMPLET est passe a `cmd`, jamais le seul nom du fichier : depuis
    Python 3.11, les processus enfants sont lances avec la variable
    `NoDefaultCurrentDirectoryInExePath`, donc cmd ne cherche plus dans le
    dossier courant (panne du 21/09/2026 : « '_test_start_neutre.bat' n'est pas
    reconnu... »). Le chemin complet, lui, marche toujours.
    """
    if contenu_regle is None:
        if REGLE.exists():
            REGLE.unlink()
    else:
        REGLE.write_text(contenu_regle, encoding='utf-8')
    r = subprocess.run(['cmd', '/c', str(COPIE)], cwd=str(RACINE),
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    return (r.stdout or '') + (r.stderr or '')


def test_ecriture_par_les_lanceurs():
    """Les lignes ajoutees aux lanceurs ecrivent-elles le bon nom ?"""
    print('')
    print('1) ce que les lanceurs ecrivent dans data\\moteur_voix.txt')
    temoin = RACINE / "data" / "_test_ecriture.txt"
    for dossier, attendu in (("neutts_service", "neutts"),
                             ("xtts_service", "xtts"),
                             ("kyutai_service", "kyutai")):
        if temoin.exists():
            temoin.unlink()
        commande = '> "..\\data\\_test_ecriture.txt" echo %s' % attendu
        subprocess.run(commande, cwd=str(RACINE / dossier), shell=True,
                       capture_output=True, text=True)
        contenu = temoin.read_text(encoding='utf-8').strip() if temoin.exists() else ''
        verifier('%s -> ecrit "%s"' % (dossier, attendu), contenu == attendu,
                 'contenu lu : %r' % contenu)
    if temoin.exists():
        temoin.unlink()


def test_choix_du_moteur():
    print('')
    print('2) ce que START.bat choisit selon le fichier de regle')
    cas = [
        (None,           'Moteur de voix Kyutai'),        # pas de fichier -> Kyutai
        ('neutts',       'Moteur retenu : NeuTTS'),       # plus allume tout seul
        ('xtts',         'Moteur retenu : XTTS v2'),      # plus allume tout seul
        ('kyutai',       'Moteur de voix Kyutai'),
        ('aucun',        'AUCUN - choix enregistre'),
        ('bidule',       'Moteur de voix Kyutai'),        # inconnu -> Kyutai
        ('xtts\r\n',     'Moteur retenu : XTTS v2'),      # saut de ligne final
        ('  kyutai  \n', 'Moteur de voix Kyutai'),        # espaces parasites
    ]
    for contenu, attendu in cas:
        sortie = lancer_start(contenu)
        etiquette = 'aucun fichier' if contenu is None else repr(contenu)
        lignes = ' | '.join(l.strip() for l in sortie.splitlines() if l.strip())
        verifier('regle %-16s -> %s' % (etiquette, attendu),
                 attendu in sortie, 'sortie : ' + lignes[:160])


def test_copie_neutre_sans_lancement():
    """La copie de test ne doit RIEN pouvoir lancer (revision du 21/09/2026).

    C'est ce controle qui manquait : les motifs a neutraliser dataient de
    l'epoque ou START.bat allumait NeuTTS, donc la ligne de Kyutai passait au
    travers et le test lancait le moteur pour de vrai, sept fois de suite.
    """
    print('')
    print('2 bis) la copie neutre ne lance plus rien pour de vrai')
    source = COPIE.read_text(encoding='utf-8')
    verifier('aucun lancement de moteur (start ... cmd /k)',
             'start "' not in source)
    verifier('aucun lancement de Pocket TTS (PowerShell Start-Process)',
             'Start-Process' not in source)
    verifier('aucun lancement du lecteur (python main.py)',
             'python main.py' not in source)
    verifier('le lecteur en marche n est plus ARRETE (garde-fou du 18/09/2026)',
             'Stop-Process' not in source)
    verifier('les cinq affichages neutres sont en place',
             source.count('[NEUTRE]') == 5, source.count('[NEUTRE]'))
    # Un .bat en LF seul fait LIRE DE TRAVERS par cmd : il execute le texte de
    # ses propres commentaires (le 21/09/2026, cela a lance le moteur Kyutai pour
    # de vrai). On verifie donc la forme du fichier, pas seulement son contenu.
    octets = COPIE.read_bytes()
    verifier('la copie est bien en CRLF (un .bat en LF fait derailler cmd)',
             octets.count(b"\n") == octets.count(b"\r\n"),
             'CRLF=%d  fins de ligne=%d'
             % (octets.count(b"\r\n"), octets.count(b"\n")))


def test_garde_fou_deja_en_marche():
    print('')
    print('3) garde-fous presents dans START.bat')
    source = COPIE.read_text(encoding='utf-8')
    verifier('le port 8082 (Kyutai) est teste avant tout lancement',
             '127.0.0.1:8082/sante' in source)
    verifier('le test de port precede le lancement du moteur',
             source.index('127.0.0.1:8082/sante')
             < source.index('ici serait lance : Kyutai'))
    verifier('un moteur deja en marche ne relance rien',
             'deja en marche' in source)
    verifier("l'environnement est verifie avant de lancer",
             'kyutai_service\\.venv' in source)
    verifier('le port 8085 (Pocket TTS) est teste AVANT celui de Kyutai',
             '127.0.0.1:8085/sante' in source
             and source.index('127.0.0.1:8085/sante')
             < source.index('127.0.0.1:8082/sante'))
    # Ce controle porte sur le VRAI START.bat : dans la copie neutre, la ligne
    # de lancement de Pocket TTS est justement remplacee par un affichage.
    original = (RACINE / "START.bat").read_text(encoding='utf-8', errors='replace')
    verifier('Pocket TTS est lance SANS FENETRE',
             '-WindowStyle Hidden' in original)
    verifier('le bloc Pocket TTS ne saute plus vers le lecteur',
             ':pocket_pret' in source)
    verifier('les anciens blocs :moteur_xtts / :moteur_kyutai ont disparu',
             ':moteur_xtts' not in source and ':moteur_kyutai' not in source)
    verifier('un seul moteur lourd est lance automatiquement : Kyutai',
             original.count('start "') == 1
             and 'cmd /k DEMARRER_KYUTAI' in original
             and 'cmd /k DEMARRER_XTTS' not in original
             and 'cmd /k DEMARRER_NEUTTS' not in original,
             'lignes start : %d' % original.count('start "'))



def test_parentheses_dans_les_blocs():
    """Piege cmd : dans un bloc ( ... ), une parenthese DANS UN TEXTE ferme
    le bloc -- le reste de la ligne devient une erreur de syntaxe
    (constate le 14/09/2026 : "echo ... (choix enregistre).").

    On verifie donc qu'aucun message affiche dans un bloc n'en contient.
    Les parentheses ECHAPPEES (`^(` et `^)`) sont du texte pour cmd : elles sont
    retirees avant le controle -- sans cela, le garde-fou du 18/09/2026
    (« ^(Sans cela, ... ^) ») faisait echouer ce test a tort.
    """
    print('')
    print('4) aucun message dans un bloc ne contient de parenthese')
    profondeur = 0
    fautives = []
    for numero, ligne in enumerate(
            (RACINE / "START.bat").read_text(encoding='utf-8').splitlines(), 1):
        nue = ligne.strip()
        sans_echappees = nue.replace('^(', '').replace('^)', '')
        dans_bloc = profondeur > 0
        if (dans_bloc and sans_echappees.lower().startswith('echo')
                and ('(' in sans_echappees or ')' in sans_echappees)):
            fautives.append('ligne %d : %s' % (numero, nue))
        # A jour de la profondeur : une ligne qui ouvre un bloc se termine par (
        if nue.endswith('('):
            profondeur += 1
        elif nue == ')':
            profondeur -= 1
    verifier('aucun echo de bloc ne contient de parenthese',
             not fautives, ' | '.join(fautives))


def test_parcours_complet():
    """A quoi ressemble ce que Laurent verra a l'ecran ?"""
    print('')
    print('5) parcours complet, tel qu affiche a l ecran (regle = "xtts")')
    sortie = lancer_start('xtts')
    for ligne in sortie.splitlines():
        if ligne.strip() and not ligne.startswith('Microsoft'):
            print('      ' + ligne.rstrip())


def main():
    print('=' * 66)
    print('VERIFICATION : demarrage du moteur de voix par START.bat')
    print('=' * 66)

    regle_avant = REGLE.read_text(encoding='utf-8') if REGLE.exists() else None
    try:
        fabriquer_copie_neutre()
        test_ecriture_par_les_lanceurs()
        test_choix_du_moteur()
        test_copie_neutre_sans_lancement()
        test_garde_fou_deja_en_marche()
        test_parentheses_dans_les_blocs()
        test_parcours_complet()
    finally:
        if COPIE.exists():
            COPIE.unlink()
        if regle_avant is None:
            if REGLE.exists():
                REGLE.unlink()
        else:
            REGLE.write_text(regle_avant, encoding='utf-8')

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('(fichier de regle et copie de test nettoyes)')
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
