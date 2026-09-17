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
rem  MOTEUR DE VOIX (NeuTTS) : allume en meme temps que le lecteur,
rem  dans sa propre fenetre, parce qu'il exige Python 3.12 + PyTorch
rem  alors que le lecteur tourne en Python 3.14.
rem
rem  CHANGEMENT DU 16/09/2026 (demande de Laurent) : le lecteur ne
rem  lance PLUS XTTS v2 ni Kyutai tout seul. NeuTTS (port 8084)
rem  prend leur place : il est STABLE (meme texte = meme audio, a
rem  l'octet pres), il ne babille pas sur les phrases courtes, et il
rem  evite de jongler entre deux moteurs. XTTS et Kyutai restent
rem  disponibles, mais A LA MAIN :
rem      - xtts_service\DEMARRER_XTTS.bat
rem      - kyutai_service\DEMARRER_KYUTAI.bat
rem  ou le bouton « Voix de personnages », en bas de la fenetre du
rem  lecteur (il eteint l'autre moteur avant d'allumer le nouveau).
rem
rem  data\moteur_voix.txt est toujours lu (le bouton du lecteur y
rem  ecrit le moteur choisi) : la valeur « aucun » est respectee --
rem  demarrage sans moteur lourd -- et toute autre valeur fait
rem  demarrer NeuTTS.
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
set MOTEUR_VOIX=neutts
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
    echo  Son allumage automatique est desactive : NeuTTS demarre a sa place.
    echo  Pour utiliser XTTS : xtts_service\DEMARRER_XTTS.bat
)
if /i "%MOTEUR_VOIX%"=="kyutai" (
    echo  Moteur retenu : Kyutai.
    echo  Son allumage automatique est desactive : NeuTTS demarre a sa place.
    echo  Pour utiliser Kyutai : kyutai_service\DEMARRER_KYUTAI.bat
)

rem -- NeuTTS est-il deja allume ? Le port s'ouvre des les premieres secondes
rem    du chargement : ce seul test suffit a ne pas lancer un second moteur.
curl -s -o NUL --max-time 2 http://127.0.0.1:8084/sante >nul 2>&1
if not errorlevel 1 (
    echo  Moteur de voix NeuTTS : deja en marche.
    goto lecteur
)
if not exist "neutts_service\.venv\Scripts\python.exe" (
    echo  Moteur de voix NeuTTS : NON INSTALLE - ses voix seront indisponibles.
    echo  Pour l'installer une fois pour toutes : neutts_service\INSTALLER_NEUTTS.bat
    goto lecteur
)
echo  Moteur de voix NeuTTS : demarrage - pret dans une dizaine de secondes...
start "NIMM ePub - appareil de voix NeuTTS" /D "%~dp0neutts_service" cmd /k DEMARRER_NEUTTS.bat
goto lecteur

rem -- (Les blocs d'allumage AUTOMATIQUE d'XTTS v2 et de Kyutai ont ete retires
rem    le 16/09/2026 : NeuTTS les remplace, et il n'y a plus a jongler entre
rem    deux moteurs. Leur code est conserve tel quel dans
rem    START.bat.bak_avant_neutts_20260916 ; les deux moteurs restent lancables
rem    a la main : xtts_service\DEMARRER_XTTS.bat et
rem    kyutai_service\DEMARRER_KYUTAI.bat.)

:lecteur
echo.
python main.py
pause

