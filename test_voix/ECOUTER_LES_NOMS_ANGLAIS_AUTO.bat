@echo off
chcp 65001 >nul
setlocal
title NIMM ePub - LES NOMS ANGLAIS (lot AUTOMATIQUE)
cd /d "%~dp0.."

rem ============================================================
rem  LES NOMS ANGLAIS DU TRONE DE FER -- PREMIER LOT AUTOMATIQUE
rem  (16/10/2026)
rem
rem  CE QU'IL A DE NOUVEAU : AUCUNE graphie n'est ecrite a la main.
rem  Elles sortent de la FORMULE (phonemes anglais -> graphie
rem  francaise), calculee sur ta machine, hors ligne, en quelques
rem  secondes. Si tu valides, on ne corrige plus les noms un par un.
rem
rem  POUR CHAQUE NOM, tu entends trois fichiers (la meme phrase) :
rem     1_CIBLE_anglaise  une VRAIE voix anglaise : le repere
rem     2_FRANCAIS        le nom tel que le livre l'ecrit
rem     3_ANGLAIS         la graphie de la FORMULE, MEME voix
rem
rem  RIEN N'EST MODIFIE : ni la base, ni les voix, ni le lecteur.
rem  Le moteur Qwen s'allume s'il ne tourne pas -- fenetre separee,
rem  a ne pas fermer pendant le lot.
rem ============================================================

set BANC=test_voix\ecouter_noms_got_auto.py
set MOTEUR=qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat
set SUIVI=test_voix\_dernier_lot_got_auto.txt

if not exist "%BANC%" goto :pas_de_banc

echo ======================================================
echo   NIMM ePub - LES NOMS ANGLAIS  (lot AUTOMATIQUE)
echo ======================================================
echo.
echo   Les graphies viennent de la FORMULE, pas de Cline :
echo   c'est le premier lot ou la machine travaille seule.
echo.
echo   Pour chaque nom, trois fichiers :
echo     1_CIBLE_anglaise   une vraie voix anglaise
echo     2_FRANCAIS         le nom tel que le livre l'ecrit
echo     3_ANGLAIS          la graphie de la formule
echo.
echo   Dis ensuite, nom par nom : « 2 » pour le francais, « 3 »
echo   pour l'anglais, « les deux pareils » ou « aucune ».
echo.
echo   Compte quelques minutes, et rien n'est facture.
echo.

rem -- Le moteur Qwen : on l'allume seulement s'il ne repond pas.
curl -s -o NUL --max-time 3 http://127.0.0.1:8086/sante >nul 2>&1
if not errorlevel 1 (
    echo   Moteur Qwen : deja en marche.
    goto :banc
)
if not exist "%MOTEUR%" goto :pas_de_moteur
echo   Moteur Qwen : allumage SUR LA CARTE - sa fenetre s'ouvre...
start "NIMM ePub - appareil de voix Qwen3-TTS" /D "%~dp0qwentts_service" cmd /k "%~dp0qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat"

:banc
python "%BANC%" --attente 180
set CODE=%ERRORLEVEL%

echo.
if not "%CODE%"=="0" goto :avec_erreur

echo ======================================================
echo   C'EST PRET
echo ======================================================
echo.
if not exist "%SUIVI%" goto :sans_suivi
set /p LOT=<"%SUIVI%"
start "" explorer "%LOT%"
timeout /t 2 /nobreak >nul
if exist "%LOT%\LISEZ-MOI.txt" start "" notepad.exe "%LOT%\LISEZ-MOI.txt"
echo.
echo   Ecoute dans l'ordre : 1_CIBLE_anglaise, puis 2_FRANCAIS,
echo   puis 3_ANGLAIS. Le temoin est le dernier nom : « Jake ».
echo.
pause
exit /b 0

:sans_suivi
echo   Le dossier du lot n'a pas ete note : regarde dans test_voix\
pause
exit /b 0

:avec_erreur
echo.
echo   LE LOT S'EST ARRETE, code %CODE%.
echo.
echo   Si le moteur n'a pas repondu : relance ce bouton, et attends
echo   que la fenetre du moteur dise qu'il est pret.
echo.
pause
exit /b %CODE%

:pas_de_banc
echo   Fichier manquant : %BANC%
pause
exit /b 1

:pas_de_moteur
echo   Fichier manquant : %MOTEUR%
echo   Le moteur Qwen n'est pas installe sur ce PC.
pause
exit /b 1
