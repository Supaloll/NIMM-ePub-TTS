# -*- coding: utf-8 -*-
"""Script JETABLE -- verifie la logique de demarrage des moteurs de voix.

REGLE EN VIGUEUR DEPUIS LE 29/09/2026 (demande de Laurent : « on ne garde que les
moteurs dont j'ai besoin ») :
  - POCKET TTS est SUSPENDU : il ne demarre PLUS (essais d'ecoute non conclusifs,
    et sa seule voix encore attribuee, `pocket:Homme001`, est passee chez Qwen).
    Son marqueur d'arret volontaire n'est donc PLUS efface au demarrage -- c'est
    lui qui empeche le veilleur du lecteur de le rallumer ;
  - le moteur LOURD lu dans data\\moteur_voix.txt vaut « aucun » depuis le
    29/09/2026. DEPUIS LE 24/10/2026, seule la valeur « kyutai » allume KYUTAI :
    « aucun », « qwen », un mot inconnu ou un fichier absent laissent Kyutai
    ETEINT. Il reste INSTALLE et rebranchable par son propre lanceur, qui
    reecrit ce fichier -- donc START.bat le rallumera ensuite. XTTS v2 et NeuTTS
    restent lancables a la main, par leur propre lanceur ;
  - QWEN3-TTS (qwentts.cpp, port 8086) est le moteur des voix de personnages : il
    tourne SUR LA CARTE GRAPHIQUE depuis le 01/10/2026 (repli processeur
    automatique), et il demarre avec le lecteur, TOUJOURS.

Ce que le script controle, sans RIEN lancer (ni moteur, ni lecteur) :
  1. les trois lanceurs ecrivent bien leur nom dans data\\moteur_voix.txt ;
  2. START.bat lit ce fichier : « kyutai » -> Kyutai, TOUT LE RESTE -> aucun
     moteur lourd (y compris vide, inconnu, « qwen »), et un message clair quand
     le fichier dit encore « xtts » ou « neutts » ;
  3. les garde-fous : les ports 8085 (Pocket) et 8082 (Kyutai) sont testes avant
     tout lancement, l'absence d'environnement n'empeche pas le lecteur de
     demarrer, Pocket TTS part SANS fenetre, et les anciens blocs
     (moteur_xtts / moteur_kyutai) ont bien disparu ;
  4. le piege des parentheses dans un bloc cmd (lecon du 14/09/2026).

Methode : une COPIE de START.bat est fabriquee avec TOUTES les commandes qui
lancent reellement quelque chose (le lanceur de Kyutai, celui de Qwen3-TTS,
`python main.py`) remplacees par des affichages, et le « pause » final retire.
Rien n'est donc execute. La « regle » du moteur, elle, est ecrite dans un fichier
JETABLE (voir juste apres) -- plus jamais dans celui de la machine.

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

DEPUIS LE 24/10/2026, CE TEST N'ECRIT PLUS DANS LE VRAI PENSE-BETE. START.bat lit
son chemin dans la variable NIMM_MOTEUR_VOIX_FICHIER ; on la detourne vers
data\\_test_moteur_voix_jetable.txt. Avant, ce test ecrivait VRAIMENT dans
data\\moteur_voix.txt : un run INTERROMPU (fenetre fermee, plantage) y laissait
« kyutai », et START.bat rallumait alors Kyutai a chaque demarrage -- constate les
01/10 et 24/10/2026. Un filet de plus, a la fin du run, verifie que le VRAI
fichier n'a pas bouge, et le RESTAURE s'il a bouge (avec un ECHEC affiche).

A lancer avec le Python du lecteur :
    python test_voix/test_start_moteur.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

# Le pense-bete de la MACHINE. Ce test ne l'ecrit JAMAIS (depuis le 24/10/2026) :
# il le surveille seulement, et le restaure s'il a bouge (voir la fin de main).
REGLE = RACINE / "data" / "moteur_voix.txt"
# Le fichier JETABLE ou l'on ecrit les valeurs de provocation. START.bat le lit a
# la place du vrai, grace a la variable NIMM_MOTEUR_VOIX_FICHIER.
JETABLE = RACINE / "data" / "_test_moteur_voix_jetable.txt"
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
        ('start "NIMM ePub - appareil de voix Kyutai" /D "%~dp0kyutai_service" cmd /k "%~dp0kyutai_service\\DEMARRER_KYUTAI.bat"',
         'echo [NEUTRE] ici serait lance : Kyutai'),
        # POCKET TTS : son remplacement a ete RETIRE le 29/09/2026 -- le moteur
        # est suspendu, START.bat n'a donc plus AUCUNE ligne de lancement pour
        # lui, et le compte des affichages neutres passe de six a cinq.
        # RAPPEL TOUJOURS VALABLE pour les textes neutres : AUCUNE PARENTHESE
        # (26/09/2026). Une parenthese dans un texte, DANS UN BLOC « ( ... ) »,
        # ferme le bloc et fait derailler cmd -- la lecon du 14/09/2026,
        # retrouvee ici par accident : le remplacement du « timeout » plus bas
        # vit, lui, DANS le bloc du garde-fou.
        # Qwen3-TTS : c'est qwentts.cpp, lance PLUS HAUT, avec Pocket, et depuis
        # le 01/10/2026 par le bouton CARTE GRAPHIQUE.
        # Oublier cette ligne ferait LANCER POUR DE VRAI le moteur pendant le
        # test (1,2 Go de modeles charges en memoire) -- c'est exactement le
        # piege du 21/09/2026 avec NeuTTS. Le controle « la copie neutre ne
        # lance plus rien » (section 2 bis) est la pour l'attraper.
        # CHEMIN COMPLET depuis le 29/09/2026 (voir START.bat) : sans lui, lancer
        # START.bat depuis un programme (variable NoDefaultCurrentDirectoryInExePath)
        # fait echouer le `cmd /k` sur un nom court, et AUCUN moteur ne demarre.
        ('start "NIMM ePub - appareil de voix Qwen3-TTS" /D "%~dp0qwentts_service" cmd /k "%~dp0qwentts_service\\DEMARRER_QWENTTS_CPP_GPU.bat"',
         'echo [NEUTRE] ici serait lance : Qwen3-TTS, dans sa fenetre'),
        ('python main.py', 'echo [NEUTRE] ici le lecteur demarrerait'),
        ('pause', ''),
    ]
    for avant, apres in remplacements:
        source = source.replace(avant, apres)
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
    # MEME REGLE QUE PLUS HAUT : aucune parenthese dans le texte neutre, car
    # cette ligne vit DANS le bloc du garde-fou.
    source = re.sub(r'(?m)^[ \t]*timeout /t 2.*$',
                    'echo [NEUTRE] pause de 2 s passee',
                    source)
    # `newline="\r\n"` : INDISPENSABLE. `read_text()` a converti les fins de ligne
    # en LF, et un .bat ecrit en LF fait DERAILLER cmd -- il execute alors le
    # texte de ses propres commentaires (constate le 21/09/2026 : la copie a
    # lance pour de vrai le moteur Kyutai, et un diagnostic a lance NeuTTS).
    # REGLE DU PROJET : un .bat s'ecrit TOUJOURS en CRLF.
    COPIE.write_text(source, encoding='utf-8', newline="\r\n")
    return source


def lancer_start(contenu_regle):
    """Ecrit la regle demandee dans le fichier JETABLE, puis execute la copie neutre.

    Le CHEMIN COMPLET est passe a `cmd`, jamais le seul nom du fichier : depuis
    Python 3.11, les processus enfants sont lances avec la variable
    `NoDefaultCurrentDirectoryInExePath`, donc cmd ne cherche plus dans le
    dossier courant (panne du 21/09/2026 : « '_test_start_neutre.bat' n'est pas
    reconnu... »). Le chemin complet, lui, marche toujours.

    DEPUIS LE 24/10/2026 : la regle va dans JETABLE, et on pose
    `NIMM_MOTEUR_VOIX_FICHIER` pour que START.bat la lise LA au lieu du vrai
    `data\\moteur_voix.txt`. C'est ce detour qui a manque pendant deux mois : le
    test ecrivait dans le pense-bete de la machine, et un run interrompu y
    laissait « kyutai » (donc Kyutai rallume a chaque demarrage).
    """
    if contenu_regle is None:
        if JETABLE.exists():
            JETABLE.unlink()
    else:
        JETABLE.write_text(contenu_regle, encoding='utf-8')
    environnement = dict(os.environ)
    environnement['NIMM_MOTEUR_VOIX_FICHIER'] = str(JETABLE)
    r = subprocess.run(['cmd', '/c', str(COPIE)], cwd=str(RACINE),
                       env=environnement,
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
    # REGLE DU 24/10/2026 : « kyutai » est la SEULE valeur qui allume Kyutai.
    # Avant, toute valeur autre que « aucun » l'allumait, « qwen » compris.
    cas = [
        (None,           'Moteur de voix LOURD : aucun'),  # pas de fichier -> rien
        ('neutts',       'Moteur retenu : NeuTTS'),       # plus allume tout seul
        ('xtts',         'Moteur retenu : XTTS v2'),      # plus allume tout seul
        ('kyutai',       'Moteur de voix Kyutai'),        # LE SEUL cas qui l'allume
        ('aucun',        'Moteur de voix LOURD : aucun'),
        ('qwen',         'en STANDBY'),                   # 24/10 : plus de cohabitation
        ('bidule',       'Moteur de voix LOURD : aucun'), # inconnu -> rien
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
    verifier('les cinq affichages neutres sont en place (Pocket n a plus de ligne)',
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
    verifier('le port 8085 (Pocket TTS) n est plus teste ni lance',
             '127.0.0.1:8085' not in source)
    # Ce controle porte sur le VRAI START.bat : dans la copie neutre, les lignes
    # de lancement sont justement remplacees par des affichages.
    original = (RACINE / "START.bat").read_text(encoding='utf-8', errors='replace')
    verifier('Pocket TTS est SUSPENDU : plus aucun lancement dans START.bat',
             'cmd /k DEMARRER_POCKET_TTS' not in original
             and 'appareil de voix Pocket TTS' not in original
             and 'POCKET TTS' in original)
    verifier('le marqueur d arret de Pocket n est PLUS efface au demarrage',
             'del "pocket_tts_service\\arrete_volontaire.txt"' not in original
             and 'arrete_volontaire.txt' in original)
    verifier('le bloc Pocket TTS ne saute plus vers le lecteur',
             ':pocket_pret' in source)
    verifier('les anciens blocs :moteur_xtts / :moteur_kyutai ont disparu',
             ':moteur_xtts' not in source and ':moteur_kyutai' not in source)
    # Depuis le 21/09/2026, les moteurs automatiques ont leur fenetre : Kyutai
    # (comme avant), Pocket TTS (pour pouvoir l'eteindre en la fermant), et
    # Qwen3-TTS -- le portage qwentts.cpp : depuis le 01/10/2026 il tourne SUR LA
    # CARTE GRAPHIQUE (repli processeur automatique), et c'est START.bat qui
    # l'allume en meme temps que Pocket.
    verifier('les deux moteurs a fenetre sont Qwen et Kyutai, en CHEMIN COMPLET',
             original.count('start "') == 2
             and 'cmd /k "%~dp0qwentts_service\\DEMARRER_QWENTTS_CPP_GPU.bat"' in original
             and 'cmd /k "%~dp0kyutai_service\\DEMARRER_KYUTAI.bat"' in original
             and 'cmd /k DEMARRER_POCKET_TTS' not in original
             and 'cmd /k DEMARRER_XTTS' not in original
             and 'cmd /k DEMARRER_NEUTTS' not in original,
             'lignes start : %d' % original.count('start "'))
    # PANNE DU 29/09/2026 : lance par un PROGRAMME (bouton « Redemarrer NIMM ePub »
    # du lecteur), START.bat voyait ses `start ... cmd /k <lanceur>` echouer sur un
    # nom court, a cause de NoDefaultCurrentDirectoryInExePath : la fenetre
    # s'ouvrait sur une erreur et AUCUN moteur ne demarrait. Le chemin complet est
    # la correction, et ce controle l'empeche de revenir en arriere.
    verifier('aucun lancement de moteur par NOM COURT (panne du 29/09/2026)',
             'cmd /k DEMARRER_QWENTTS_CPP' not in original
             and 'cmd /k DEMARRER_KYUTAI' not in original)



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

    # Photographie du VRAI pense-bete de la machine : depuis le 24/10/2026, ce
    # test ne doit plus y toucher. On lit des OCTETS, pour ne rien normaliser.
    vrai_avant = REGLE.read_bytes() if REGLE.exists() else None
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
        if JETABLE.exists():
            JETABLE.unlink()

    print('')
    print('6) le pense-bete de la machine n a pas bouge')
    # FILET DU 24/10/2026 : le vrai fichier doit etre IDENTIQUE a l'arrivee. Sans
    # ce controle, la panne des 01/10 et 24/10 restait invisible : le test
    # ecrivait dans le pense-bete de la machine, et « kyutai » y restait pour de
    # bon -- START.bat rallumait alors Kyutai a chaque demarrage.
    vrai_apres = REGLE.read_bytes() if REGLE.exists() else None
    verifier("data\\moteur_voix.txt est intact apres le test",
             vrai_apres == vrai_avant,
             'avant : %r  apres : %r' % (vrai_avant, vrai_apres))
    if vrai_apres != vrai_avant:
        if vrai_avant is None:
            if REGLE.exists():
                REGLE.unlink()
        else:
            REGLE.write_bytes(vrai_avant)
        print('      -> fichier RESTAURE a sa valeur d avant le test.')

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('(copie de test et fichier jetable nettoyes ; pense-bete de la machine intact)')
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
