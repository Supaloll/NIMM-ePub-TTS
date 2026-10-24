@echo off
chcp 65001 >nul
title NIMM ePub
echo.
echo  NIMM ePub - Demarrage...
echo  Adresse locale  : http://localhost:8081
echo  Adresse Tailscale : http://[ton-IP-Tailscale]:8081
echo.
cd /d "%~dp0"

rem ============================================================
rem  CE QUI S'ALLUME, DEPUIS LE 29/09/2026 (demande de Laurent :
rem  « on ne garde que les moteurs dont j'ai besoin »)
rem
rem  - QWEN3-TTS (qwentts_service, port 8086) : LE moteur des voix de
rem    personnages. DEPUIS LE 01/10/2026 il tourne SUR LA CARTE GRAPHIQUE
rem    (repli processeur automatique), et c'est lui que le lecteur appelle
rem    par defaut.
rem  - POCKET TTS : SUSPENDU (essais d'ecoute non conclusifs, et sa seule
rem    voix encore attribuee est passee chez Qwen). Il ne s'allume plus.
rem  - KYUTAI : PLUS ALLUME (data\moteur_voix.txt porte « aucun » depuis
rem    le 29/09/2026). Il reste INSTALLE et intact.
rem
rem  POUR REBRANCHER KYUTAI : bouton « Voix de personnages » du lecteur
rem  (il le rallume ET reecrit moteur_voix.txt, donc START.bat le
rem  rallumera tout seul ensuite), ou kyutai_service\DEMARRER_KYUTAI.bat.
rem  Pour POCKET : voir le bloc « POCKET TTS », plus bas.
rem
rem  Ce qui suit decrit l'ancien fonctionnement (Kyutai automatique) : il
rem  est CONSERVE tel quel, parce qu'il sert le jour ou l'on rebranche.
rem  MAIS LA REGLE, ELLE, A CHANGE LE 24/10/2026 (demande de Laurent :
rem  « il ne devrait y avoir que Qwen qui se lance ») : seule la valeur
rem  « kyutai » allume Kyutai. Voir le bloc « QUI DEMARRE », plus bas --
rem  c'est LUI qui fait foi.
rem ============================================================

rem ============================================================
rem  MOTEUR DE VOIX (Kyutai TTS) : allume en meme temps que le
rem  lecteur, dans sa propre fenetre, parce qu'il exige Python 3.12
rem  + PyTorch alors que le lecteur tourne en Python 3.14.
rem
rem  CHANGEMENT DU 17/09/2026 (demande de Laurent) : le moteur
rem  automatique devient Kyutai TTS 1.6B (port 8082), apres les
rem  ecoutes comparatives du meme jour -- sur les MEMES phrases
rem  courtes et les MEMES voix, Kyutai ne produit ni gargouillis, ni
rem  mots repetes, ni silences parasites, la ou NeuTTS en produisait
rem  (mesure : « Non. » de 1,14 a 2,68 s chez NeuTTS, 0,56 a 0,88 s
rem  chez Kyutai, et un seul silence parasite contre dix). Il est
rem  aussi plus rapide. Le casting des livres est passe chez lui.
rem
rem  Les autres moteurs restent disponibles, A LA MAIN :
rem      - neutts_service\DEMARRER_NEUTTS.bat   (l'ancien moteur auto)
rem      - xtts_service\DEMARRER_XTTS.bat
rem  ou le bouton « Voix de personnages », en bas de la fenetre du
rem  lecteur (il eteint l'autre moteur avant d'allumer le nouveau).
rem
rem  data\moteur_voix.txt est toujours lu (le bouton du lecteur y
rem  ecrit le moteur choisi). DEPUIS LE 24/10/2026, seule la valeur
rem  « kyutai » fait demarrer Kyutai : « aucun », « qwen », un mot
rem  inconnu ou un fichier absent laissent Kyutai eteint. Voir le bloc
rem  « QUI DEMARRE », plus bas.
rem
rem  Deux precautions, inchangees :
rem   - si le moteur tourne deja ou finit de charger, on ne le
rem     relance pas (le port est ouvert des les premieres secondes) ;
rem   - si son environnement n'est pas installe, le lecteur demarre
rem     quand meme -- seules ses voix seront indisponibles.
rem ============================================================

rem -- Le moteur retenu la derniere fois (ecrit par le bouton du lecteur).
rem    Forme volontairement simple : "set /p" lit la premiere ligne du
rem    fichier. Pas de bloc ( ) ni de boucle for ici -- un bloc multi-lignes
rem    contenant un "for" fait derailler l'analyseur de cmd (constate au
rem    test le 14/09/2026). Les espaces ajoutes a la main sont ignores.
rem    DEFAUT quand le fichier n'existe pas : « aucun » (depuis le 24/10/2026).
rem    Avant, c'etait « kyutai » ; depuis que QWEN3-TTS est notre moteur et
rem    qu'il est allume plus bas de facon INCONDITIONNELLE, demarrer Kyutai
rem    par defaut n'a plus aucun sens.
rem
rem    CHEMIN DETOURNABLE (24/10/2026) : la variable d'environnement
rem    NIMM_MOTEUR_VOIX_FICHIER remplace ce chemin. Raison : le test
rem    test_voix\test_start_moteur.py a besoin d'ecrire des valeurs de
rem    provocation pour verifier ce fichier, et il ecrivait dans le VRAI
rem    pense-bete de la machine -- un run interrompu y laissait « kyutai », et
rem    START.bat rallumait Kyutai a chaque demarrage (constate les 01/10 et
rem    24/10/2026). Avec cette variable, le test ecrit dans un fichier JETABLE.
rem    Personne d'autre ne la pose : sans elle, rien ne change.
set "MOTEUR_VOIX_FICHIER=data\moteur_voix.txt"
if defined NIMM_MOTEUR_VOIX_FICHIER set "MOTEUR_VOIX_FICHIER=%NIMM_MOTEUR_VOIX_FICHIER%"
set MOTEUR_VOIX=aucun
if exist "%MOTEUR_VOIX_FICHIER%" set /p MOTEUR_VOIX=<"%MOTEUR_VOIX_FICHIER%"
set MOTEUR_VOIX=%MOTEUR_VOIX: =%

rem ============================================================
rem  MOTEUR DE VOIX POCKET TTS : allume TOUJOURS, et AVANT le choix
rem  du moteur lourd.
rem
rem  CORRECTIF DU 21/09/2026 (panne constatee par Laurent) : ce bloc
rem  vivait plus bas, APRES le choix de Kyutai -- dont tous les
rem  chemins finissaient par « goto lecteur ». Il n'etait donc
rem  JAMAIS atteint, et Pocket TTS ne demarrait jamais avec le
rem  lecteur. Ce qu'on voyait a l'ecran : le casting ne proposait
rem  plus aucune des 18 voix Pocket TTS (il ne propose que les voix
rem  lisibles tout de suite), donc plus aucun moyen de les choisir.
rem
rem  Particularite : ce moteur tourne sur le PROCESSEUR et n'occupe
rem  PAS la carte graphique -- il COHABITE donc avec Kyutai, Edge,
rem  Kokoro et Piper. Il ne remplace personne, et rien ne l'eteint.
rem
rem  Pourquoi SANS FENETRE : Laurent n'a rien a ouvrir ni a fermer.
rem  Le moteur s'endort apres 3 heures sans la moindre phrase
rem  (=NIMM_POCKET_TTS_INACTIF ; 30 min jusqu'au 21/09/2026, ce qui
rem  l'endormait en pleine journee d'ecoute). S'il s'endort quand
rem  meme, le LECTEUR le rallume tout seul : il y a une ronde toutes
rem  les 30 s dans main.py (le veilleur).
rem
rem  Deux precautions, comme pour Kyutai :
rem   - s'il tourne deja, on ne le relance pas ;
rem   - s'il n'est pas installe, le lecteur demarre quand meme
rem     (ses voix seront simplement indisponibles).
rem ============================================================
rem -- POCKET TTS EST SUSPENDU depuis le 29/09/2026 (demande de Laurent : ses
rem    essais d'ecoute n'etaient pas conclusifs, et presque toutes les voix sont
rem    passees chez Qwen3-TTS). AVANT, deux lignes EFFACAIENT le marqueur d'arret
rem    volontaire a chaque demarrage : c'etait voulu alors (« un demarrage remet
rem    les pendules a l'heure »). Maintenant on le LAISSE, parce que c'est LUI qui
rem    dit au veilleur du lecteur « ne le rallume pas » (main.py,
rem    _pocket_arrete_volontairement). Sans lui, le lecteur rallumerait Pocket
rem    15 secondes apres son demarrage, et la suspension ne servirait a rien.
rem    (La ligne d'effacement elle-meme est dans l'historique Git et dans
rem    START.bat.bak_avant_suspendre_pocket_20260929.)

rem ============================================================
rem  POCKET TTS : PLUS ALLUME AU DEMARRAGE (29/09/2026)
rem
rem  Le moteur reste INSTALLE et intact. Ses 28 voix disparaissent seulement des
rem  menus (le lecteur ne propose que les voix ECOUTABLES TOUT DE SUITE), et
rem  aucun livre ne les utilise plus : la seule voix encore attribuee
rem  (`pocket:Homme001`, Deke Simmons du livre 28) a ete basculee vers sa
rem  jumelle Qwen le meme jour -- memes extraits, donc meme timbre.
rem
rem  POUR LE REBRANCHER (deux gestes, dans cet ordre) :
rem    1. pocket_tts_service\DEMARRER_POCKET_TTS.bat   (sa fenetre s'ouvre)
rem    2. supprimer pocket_tts_service\arrete_volontaire.txt, sinon le veilleur
rem       du lecteur considere l'arret comme VOLONTAIRE et ne le rallume pas.
rem  Et remettre ce bloc en service (il est conserve juste en dessous, en
rem  commentaire, pour ne rien reinventer).
rem ============================================================
if exist "pocket_tts_service\arrete_volontaire.txt" (
    echo  Moteur de voix Pocket TTS : SUSPENDU - ses voix ne sont plus proposees.
) else (
    echo  Pocket TTS est SUSPENDU mais son marqueur d'arret manque : le lecteur
    echo  risque de le rallumer. Voir START.bat, bloc POCKET TTS.
)
goto pocket_pret

rem -- L'ANCIEN BLOC de lancement de Pocket TTS (test du port 8085, message
rem    « deja en marche », verification de l'environnement, ouverture de sa
rem    fenetre) est CONSERVE DANS L'HISTORIQUE GIT (revision du 29/09/2026,
rem    commit precedent) et dans START.bat.bak_avant_suspendre_pocket_20260929.
rem    Il n'est PAS laisse ici en commentaire : des lignes de code mortes
rem    trompent les filets du projet (test_start_moteur.py cherche le TEXTE
rem    commandes de lancement, commentaires compris).

:pocket_pret

rem -- QWEN3-TTS / qwentts.cpp : le moteur de voix Qwen. DEPUIS LE 01/10/2026 il
rem    est allume SUR LA CARTE GRAPHIQUE (bouton DEMARRER_QWENTTS_CPP_GPU.bat ;
rem    mesure du 01/10/2026 : x3,9 a x7 le temps reel selon la phrase). C'est
rem    START.bat qui l'allume : Laurent n'a rien a ouvrir. Son port est le 8086,
rem    celui que le lecteur appelle PAR DEFAUT (aucune variable a poser).
rem    SI LA CARTE ECHOUE, le service reprend TOUT SEUL sur le processeur (il ne
rem    s'arrete jamais) : /sante le dit. Pour repasser au processeur a la main :
rem    fermer sa fenetre, puis double-clic sur DEMARRER_QWENTTS_CPP.bat.
if not exist "qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat" (
    echo  Moteur de voix Qwen3-TTS : NON INSTALLE - ses voix seront indisponibles.
    goto qwentts_pret
)
curl -s -o NUL --max-time 2 http://127.0.0.1:8086/sante >nul 2>&1
if not errorlevel 1 (
    echo  Moteur de voix Qwen3-TTS : deja en marche.
    goto qwentts_pret
)
rem -- CHEMIN COMPLET dans le `start` (29/09/2026) : quand START.bat est lance par
rem    un PROGRAMME (le bouton « Redemarrer NIMM ePub » du lecteur), Windows pose
rem    la variable NoDefaultCurrentDirectoryInExePath=1 : cmd ne cherche plus dans
rem    son dossier courant, et un nom court (le lanceur ecrit seul) n'est PAS
rem    trouve -- la fenetre s'ouvre sur une erreur, et AUCUN moteur ne demarre.
rem    Avec le chemin complet, ca marche dans les deux cas. Constat du 29/09/2026.
echo  Moteur de voix Qwen3-TTS : demarrage SUR LA CARTE - sa fenetre s'ouvre...
start "NIMM ePub - appareil de voix Qwen3-TTS" /D "%~dp0qwentts_service" cmd /k "%~dp0qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat"

:qwentts_pret


rem ============================================================
rem  QUI DEMARRE, DEPUIS LE 24/10/2026 (demande de Laurent : « il ne
rem  devrait y avoir que Qwen qui se lance », Kyutai etant en standby)
rem
rem  KYUTAI NE DEMARRE QUE SI le fichier dit exactement « kyutai ».
rem  Tout le reste laisse Kyutai ETEINT : « aucun », « qwen », « xtts »,
rem  « neutts », un mot inconnu, un fichier vide ou absent.
rem
rem  AVANT, toute valeur autre que « aucun » allumait Kyutai -- « qwen »
rem  compris, au nom d'une « cohabitation » datee du 26/09/2026, du temps
rem  ou Qwen n'etait pas encore allume d'office. Deux moteurs sur la carte
rem  graphique pour rien, et ~3,7 Go perdus : c'est corrige ici.
rem
rem  QWEN3-TTS, lui, est allume PLUS HAUT et TOUJOURS : c'est le moteur
rem  des voix de personnages (carte graphique, repli processeur).
rem ============================================================
if /i "%MOTEUR_VOIX%"=="kyutai" goto demarrer_kyutai

if /i "%MOTEUR_VOIX%"=="qwen" (
    echo  Moteur de voix Kyutai : en STANDBY - il ne demarre plus avec Qwen.
    goto lecteur
)
if /i "%MOTEUR_VOIX%"=="xtts" (
    echo  Moteur retenu : XTTS v2.
    echo  Son allumage automatique est desactive.
    echo  Pour utiliser XTTS : xtts_service\DEMARRER_XTTS.bat
    goto lecteur
)
if /i "%MOTEUR_VOIX%"=="neutts" (
    echo  Moteur retenu : NeuTTS.
    echo  Son allumage automatique est desactive.
    echo  Pour utiliser NeuTTS : neutts_service\DEMARRER_NEUTTS.bat
    goto lecteur
)
echo  Moteur de voix LOURD : aucun - QWEN3-TTS est allume plus haut.
echo  Kyutai est en STANDBY. Voix disponibles tout de suite : Edge, Kokoro,
echo  Piper et Qwen3-TTS. Pour rallumer Kyutai : kyutai_service\DEMARRER_KYUTAI.bat
goto lecteur

:demarrer_kyutai
rem -- Kyutai est-il deja allume ? Le port s'ouvre des les premieres secondes
rem    du chargement : ce seul test suffit a ne pas lancer un second moteur.
curl -s -o NUL --max-time 2 http://127.0.0.1:8082/sante >nul 2>&1
if not errorlevel 1 (
    echo  Moteur de voix Kyutai : deja en marche.
    goto lecteur
)
if not exist "kyutai_service\.venv\Scripts\python.exe" (
    echo  Moteur de voix Kyutai : NON INSTALLE - ses voix seront indisponibles.
    echo  Pour l'installer une fois pour toutes : kyutai_service\INSTALLER_KYUTAI.bat
    goto lecteur
)
echo  Moteur de voix Kyutai : demarrage - pret dans une dizaine de secondes...
start "NIMM ePub - appareil de voix Kyutai" /D "%~dp0kyutai_service" cmd /k "%~dp0kyutai_service\DEMARRER_KYUTAI.bat"
goto lecteur

rem -- (Le 17/09/2026, Kyutai a remplace NeuTTS comme moteur automatique : il
rem    gagne a l'ecoute sur les phrases courtes, et le casting est passe chez
rem    lui. L'ancien bloc NeuTTS est conserve dans l'historique Git ; NeuTTS
rem    reste lancable a la main : neutts_service\DEMARRER_NEUTTS.bat.)

rem -- (Le bloc « MOTEUR DE VOIX POCKET TTS » a ete DEPLACE le 21/09/2026 : il
rem    est desormais plus HAUT, AVANT le choix du moteur lourd. Ici, apres le
rem    « goto lecteur » du bloc Kyutai, il n'etait jamais atteint -- voir le
rem    commentaire du nouveau bloc, tout en haut.)

:lecteur

rem ============================================================
rem  GARDE-FOU AJOUTE LE 18/09/2026 (piege constate le meme soir)
rem
rem  PROBLEME : fermer la fenetre de commande ne tue pas toujours le
rem  processus Python. Le port 8081 reste alors PRIS par l'ancien serveur ;
rem  le nouveau ne peut pas demarrer (message d'erreur d'une seconde, puis
rem  la fenetre se ferme) et c'est l'ANCIEN serveur qui repond -- avec
rem  l'ANCIEN code en memoire. Ce soir-la, Laurent a relance plusieurs fois
rem  en croyant tester les corrections, alors que tout etait inchange a
rem  l'oreille.
rem
rem  Donc : avant de demarrer, on ARRETE tout serveur deja en marche.
rem
rem  ATTENTION (lecon du 18/09/2026, apprise a mes depens) : on cible le
rem  processus par le PORT (8081), JAMAIS par le nom du script. NIMM (le
rem  chatbot de Laurent, G:\NIMM) utilise lui aussi un "main.py" et tourne
rem  sur le port 8080 : un filtre par nom de fichier l'aurait tue lui.
rem  Et on exige un processus PYTHON, pour ne jamais toucher le relais
rem  Tailscale qui ecoute aussi sur 8081 (adresse Tailscale uniquement).
rem ============================================================
curl -s -o NUL --max-time 2 http://127.0.0.1:8081/ >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  Un serveur NIMM ePub tourne DEJA sur le port 8081.
    echo  On l'arrete, pour que le nouveau demarre avec le code a jour.
    echo  ^(Sans cela, le nouveau ne demarre pas et c'est l'ANCIEN qui
    echo   continue de repondre : on croirait que rien ne change.^)
    echo.
    powershell -NoProfile -Command "$pids = Get-NetTCPConnection -LocalPort 8081 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($p in $pids) { $proc = Get-Process -Id $p -ErrorAction SilentlyContinue; if ($proc -and $proc.ProcessName -like 'python*') { Stop-Process -Id $p -Force } }"
    timeout /t 2 /nobreak >nul
    echo  Ancien serveur arrete.
    echo.
)

rem ============================================================
rem  LE MOTEUR QWEN EST MAINTENANT CHEZ NOUS (28/09/2026, le soir)
rem
rem  Le portage qwentts.cpp est installe dans  qwentts_service\  et il
rem  ecoute sur le port 8086 -- celui que le lecteur appelle PAR DEFAUT.
rem  Il est allume PLUS HAUT, avec Pocket (il cohabite : il ne prend pas
rem  la carte graphique).
rem
rem  Le branchement provisoire sur le port 8087, qui pointait sur le
rem  service de NIMM Voix, n'a donc plus lieu d'etre : notre moteur prend
rem  sa place, et NIMM_QWEN_URL redevient inutile. Son historique est au
rem  BACKLOG : il a servi une seule soiree, celle du 28/09/2026.
rem ============================================================

echo.
python main.py
pause

