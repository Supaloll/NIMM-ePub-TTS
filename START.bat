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
rem  ecrit le moteur choisi) : la valeur « aucun » est respectee --
rem  demarrage sans moteur lourd -- et toute autre valeur fait
rem  demarrer Kyutai.
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
set MOTEUR_VOIX=kyutai
if exist "data\moteur_voix.txt" set /p MOTEUR_VOIX=<"data\moteur_voix.txt"
set MOTEUR_VOIX=%MOTEUR_VOIX: =%

if /i "%MOTEUR_VOIX%"=="aucun" (
    echo  Moteur de voix : AUCUN - choix enregistre.
    echo  Seules les voix Edge, Kokoro et Piper seront disponibles.
    echo  Pour en changer : bouton en bas de la fenetre du lecteur.
    goto lecteur
)
if /i "%MOTEUR_VOIX%"=="xtts" (
    echo  Moteur retenu : XTTS v2.
    echo  Son allumage automatique est desactive : Kyutai demarre a sa place.
    echo  Pour utiliser XTTS : xtts_service\DEMARRER_XTTS.bat
)
if /i "%MOTEUR_VOIX%"=="neutts" (
    echo  Moteur retenu : NeuTTS.
    echo  Son allumage automatique est desactive : Kyutai demarre a sa place.
    echo  Pour utiliser NeuTTS : neutts_service\DEMARRER_NEUTTS.bat
)

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
start "NIMM ePub - appareil de voix Kyutai" /D "%~dp0kyutai_service" cmd /k DEMARRER_KYUTAI.bat
goto lecteur

rem -- (Le 17/09/2026, Kyutai a remplace NeuTTS comme moteur automatique : il
rem    gagne a l'ecoute sur les phrases courtes, et le casting est passe chez
rem    lui. L'ancien bloc NeuTTS est conserve dans l'historique Git ; NeuTTS
rem    reste lancable a la main : neutts_service\DEMARRER_NEUTTS.bat.)

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

echo.
python main.py
pause

