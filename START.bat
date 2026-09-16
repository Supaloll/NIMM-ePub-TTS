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
rem  MOTEUR DE VOIX LOURD (XTTS v2 ou Kyutai) : allume en meme
rem  temps que le lecteur, dans sa propre fenetre, parce qu'il
rem  exige Python 3.12 + PyTorch alors que le lecteur tourne en
rem  Python 3.14.
rem
rem  LEQUEL ? Celui utilise en DERNIER (demande de Laurent,
rem  14/09/2026). Chaque lanceur de moteur note son nom dans
rem  data\moteur_voix.txt ; c'est ce fichier qu'on relit ici :
rem
rem      xtts    -> XTTS v2 (port 8083)
rem      kyutai  -> Kyutai  (port 8082)
rem      aucun   -> demarrer SANS moteur de voix lourd
rem
rem  Modifier ce fichier a la main change le moteur du prochain
rem  demarrage : c'est le reglage, rien d'autre a toucher.
rem
rem  Trois precautions :
rem   - si un moteur tourne deja (ou finit de charger), on ne le
rem     relance pas : deux moteurs occuperaient 2 x 3,8 Go de
rem     carte graphique ;
rem   - si son environnement n'est pas installe, le lecteur demarre
rem     quand meme -- seules ses voix seront indisponibles ;
rem   - le moteur charge en tache de fond pendant qu'on utilise le
rem     lecteur : il est pret en une quinzaine de secondes.
rem ============================================================

rem -- Quel moteur a ete utilise la derniere fois ? (defaut : xtts,
rem    le moteur vers lequel on va).
rem    Forme volontairement simple : "set /p" lit la premiere ligne du
rem    fichier. Pas de bloc ( ) ni de boucle for ici -- un bloc multi-lignes
rem    contenant un "for" fait derailler l'analyseur de cmd (constate au
rem    test le 14/09/2026). Les espaces ajoutes a la main sont ignores.
set MOTEUR_VOIX=xtts
if exist "data\moteur_voix.txt" set /p MOTEUR_VOIX=<"data\moteur_voix.txt"
set MOTEUR_VOIX=%MOTEUR_VOIX: =%

if /i "%MOTEUR_VOIX%"=="aucun" (
    echo  Moteur de voix : AUCUN - choix enregistre.
    echo  Seules les voix Edge, Kokoro et Piper seront disponibles.
    echo  Pour en changer : editer data\moteur_voix.txt
    goto lecteur
)
if /i "%MOTEUR_VOIX%"=="xtts"   goto moteur_xtts
if /i "%MOTEUR_VOIX%"=="kyutai" goto moteur_kyutai

echo  Moteur de voix : "%MOTEUR_VOIX%" n'est pas un nom connu - aucun moteur lance.
echo  Valeurs acceptees dans data\moteur_voix.txt : xtts, kyutai, aucun
goto lecteur

:moteur_xtts
echo  Moteur de voix : XTTS v2 (le dernier utilise).
rem -- L'AUTRE moteur (Kyutai) est-il deja allume ? Les deux ne tiennent pas
rem    ensemble sur la carte graphique (constat de Laurent, 15/09/2026 :
rem    7,6 Go de memoire video sur 8). On ne lance donc rien du tout, et on
rem    le dit. Changer de moteur se fait par le bouton en bas du lecteur.
curl -s -o NUL --max-time 2 http://127.0.0.1:8082/sante >nul 2>&1
if not errorlevel 1 (
    echo  Moteur de voix Kyutai : deja en marche.
    echo  Un seul moteur de voix a la fois : XTTS v2 n'est pas lance.
    echo  Pour changer de moteur : bouton en bas de la fenetre du lecteur.
    goto lecteur
)
rem -- Le port est ouvert des les premieres secondes du chargement,
rem    donc ce seul test suffit a ne jamais lancer un second moteur.
curl -s -o NUL --max-time 2 http://127.0.0.1:8083/sante >nul 2>&1
if not errorlevel 1 (
    echo  Moteur de voix XTTS v2 : deja en marche.
    goto lecteur
)
if not exist "xtts_service\.venv\Scripts\python.exe" (
    echo  Moteur de voix XTTS v2 : NON INSTALLE - ses voix seront indisponibles.
    echo  Pour l'installer une fois pour toutes : xtts_service\INSTALLER_XTTS.bat
    goto lecteur
)
echo  Moteur de voix XTTS v2 : demarrage - pret dans une quinzaine de secondes...
start "NIMM ePub - moteur de voix XTTS v2" /D "%~dp0xtts_service" cmd /k DEMARRER_XTTS.bat
goto lecteur

:moteur_kyutai
echo  Moteur de voix : Kyutai (le dernier utilise).
rem -- L'AUTRE moteur (XTTS v2) est-il deja allume ? Meme regle que dans la
rem    branche XTTS : un seul moteur de voix a la fois.
curl -s -o NUL --max-time 2 http://127.0.0.1:8083/sante >nul 2>&1
if not errorlevel 1 (
    echo  Moteur de voix XTTS v2 : deja en marche.
    echo  Un seul moteur de voix a la fois : Kyutai n'est pas lance.
    echo  Pour changer de moteur : bouton en bas de la fenetre du lecteur.
    goto lecteur
)
curl -s -o NUL --max-time 2 http://127.0.0.1:8082/sante >nul 2>&1
if not errorlevel 1 (
    echo  Moteur de voix Kyutai : deja en marche.
    goto lecteur
)
if not exist "kyutai_service\.venv\Scripts\python.exe" (
    echo  Moteur de voix Kyutai : NON INSTALLE - les voix Kyutai seront indisponibles.
    echo  Pour l'installer une fois pour toutes : kyutai_service\INSTALLER_KYUTAI.bat
    goto lecteur
)
echo  Moteur de voix Kyutai : demarrage - pret dans une quinzaine de secondes...
start "NIMM ePub - moteur de voix Kyutai" /D "%~dp0kyutai_service" cmd /k DEMARRER_KYUTAI.bat

:lecteur
echo.
python main.py
pause

