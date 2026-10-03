@echo off
rem ---------------------------------------------------------------------
rem  TEST A/B : LA LONGUEUR DE LA REFERENCE CHANGE-T-ELLE LA VOIX ?
rem  NIMM ePub -- 03/10/2026 -- demande de Laurent
rem
rem  Double-clic : il fabrique 12 fichiers a ecouter (environ 4 a 8 minutes,
rem  le processeur travaille), puis ouvre le dossier et la feuille de notes.
rem
rem  LA QUESTION : Laurent trouve que beaucoup de references font 7-8 s et
rem  pense que la qualite des voix vient de la. Le moteur, lui, prend la
rem  reference ENTIERE (mesure : 17,2 s de reference = 215 trames utilisees),
rem  donc la longueur change vraiment ce qu'il entend. Reste a savoir si ca
rem  s'entend.
rem
rem  CE QU'IL FABRIQUE : pour DEUX voix (Femme001 et Homme004), DEUX
rem  references coupees EXACTEMENT pareil -- l'une COURTE (5,7 s et 8,3 s),
rem  l'autre LONGUE (17,3 s et 20,3 s) -- puis il fait dire LA MEME PHRASE
rem  a chacune, 3 fois. Les fichiers portent des NOMS AU HASARD, et la cle
rem  reste HORS du dossier d'ecoute : tu notes sans savoir ce que tu ecoutes.
rem
rem  RIEN N'EST MODIFIE : ni la base, ni les voix du service, ni les
rem  catalogues. Les references de test sont chargees EN MEMOIRE et tout
rem  s'ecrit dans test_voix\sortie_test_AB_longueur\.
rem
rem  Le moteur tourne SUR LE PROCESSEUR, dans le processus : le service de la
rem  carte (port 8086) n'est ni touche ni arrete.
rem
rem  ASCII pur : aucun accent, aucun caractere special.
rem ---------------------------------------------------------------------
setlocal
title TEST A/B LONGUEUR DES REFERENCES - NIMM ePub
cd /d "%~dp0.."

set PY=qwentts_service\.venv\Scripts\python.exe
set SCRIPT=test_voix\_test_AB_longueur_reference.py
set LOT=test_voix\sortie_test_AB_longueur

if not exist "%PY%" goto :pas_de_python
if not exist "%SCRIPT%" goto :pas_de_script
if not exist "qwen_tts_service\voix\Femme001_reference.wav" goto :pas_de_voix
if not exist "qwentts_service\models\qwen-talker-0.6b-base-Q4_K_M.gguf" goto :pas_de_modele

echo ======================================================
echo   NIMM ePub - TEST A/B : REFERENCE COURTE CONTRE LONGUE
echo ======================================================
echo.
echo   Il fabrique 12 fichiers : la meme voix, la meme phrase,
echo   avec une reference COURTE puis LONGUE. Noms au hasard.
echo.
echo   COMPTE 4 A 8 MINUTES. Le processeur travaille : le
echo   ventilateur peut se faire entendre, c'est normal.
echo.
echo   Rien n'est modifie dans le projet.
echo.
echo   (Tu peux fermer cette fenetre, mais tu perdrais le test.)
echo.

"%PY%" "%SCRIPT%"
set CODE=%ERRORLEVEL%

echo.
if not "%CODE%"=="0" goto :avec_erreur

echo ======================================================
echo   C'EST PRET : %LOT%\A_ECOUTER
echo ======================================================
echo.
echo   Ecoute, donne une note de 1 a 5 a chaque fichier dans la
echo   feuille qui va s'ouvrir, puis dis-le a Cline : il croisera
echo   tes notes avec la cle.
echo.
start "" explorer "%LOT%\A_ECOUTER"
timeout /t 2 /nobreak >nul
if exist "%LOT%\A_ECOUTER\LISEZ-MOI.txt" start "" notepad.exe "%LOT%\A_ECOUTER\LISEZ-MOI.txt"
echo.
pause
exit /b 0

:avec_erreur
echo   Le test s'est arrete avec le code %CODE%.
echo.
echo   Regarde les dernieres lignes ci-dessus : elles disent pourquoi.
echo   Le journal complet est dans :
echo   test_voix\sortie_test_AB_longueur\journal.txt
echo.
pause
exit /b %CODE%

:pas_de_python
echo   LE MOTEUR N'EST PAS INSTALLE ICI
echo.
echo   Fichier introuvable : %PY%
echo.
pause
exit /b 1

:pas_de_script
echo   SCRIPT INTROUVABLE : %SCRIPT%
echo.
pause
exit /b 1

:pas_de_voix
echo   LA VOIX Femme001 EST INTROUVABLE
echo.
echo   Fichier attendu : qwen_tts_service\voix\Femme001_reference.wav
echo.
pause
exit /b 1

:pas_de_modele
echo   LE MODELE Q4_K_M EST INTROUVABLE
echo.
echo   Attendu : qwentts_service\models\qwen-talker-0.6b-base-Q4_K_M.gguf
echo.
pause
exit /b 1
