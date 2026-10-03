@echo off
rem ---------------------------------------------------------------------
rem  LES SOUFFLES SUR LA CARTE : comparer les moteurs, a l'oreille
rem  NIMM ePub -- 03/10/2026 -- retour d'ecoute de Laurent :
rem  " parfois je me retrouve avec des parasites dans la voix comme un
rem    bruit de fond, un souffle, juste sur une phrase [...] quand c'etait
rem    sur CPU, c'etait tres lent, mais c'etait tres propre "
rem
rem  Double-clic : il fabrique QUATRE passages continus -- la meme voix, les
rem  memes phrases, mais un MOTEUR different a chaque fois :
rem     A) carte, Q4_K_M, reglage de precision OFF  (ce qu'on entend aujourd'hui)
rem     B) carte, Q4_K_M, reglage de precision ON   (le levier direct)
rem     C) processeur                                (le " propre " de Laurent)
rem     D) carte, Q8_0                                (des poids plus fins)
rem  Noms au hasard, cle HORS du dossier : tu notes sans savoir ce que tu ecoutes.
rem
rem  IL REFUSE DE PARTIR SI LE MOTEUR TOURNE (port 8086) : les deux se
rem  partageraient la carte, et un repli silencieux sur le processeur
rem  fausserait tout le test.
rem
rem  RIEN N'EST MODIFIE : ni la base, ni les voix, ni le service.
rem  Compte 4 a 8 minutes, le processeur travaille pendant l'essai du
rem  processeur. ASCII pur : aucun accent, aucun caractere special.
rem ---------------------------------------------------------------------
setlocal
title TESTER LES SOUFFLES DE LA CARTE - NIMM ePub
cd /d "%~dp0.."

set PY=qwentts_service\.venv\Scripts\python.exe
set BANC=test_voix\_banc_gpu_souffles.py
set LOT=test_voix\sortie_banc_souffles_gpu

if not exist "%PY%" goto :pas_de_python
if not exist "%BANC%" goto :pas_de_banc
if not exist "qwen_tts_service\voix\references.csv" goto :pas_de_voix
if not exist "qwentts_service\models\qwen-talker-0.6b-base-Q4_K_M.gguf" goto :pas_de_modele

echo ======================================================
echo   NIMM ePub - LES SOUFFLES : QUEL MOTEUR EST LE PLUS PROPRE ?
echo ======================================================
echo.
echo   Il fabrique 4 passages : la meme voix, les memes phrases,
echo   avec 4 moteurs differents. Noms au hasard.
echo.
echo   COMPTE 4 A 8 MINUTES. Le processeur travaille : le ventilateur
echo   peut se faire entendre, c'est normal.
echo.
echo   Ferme cette fenetre pour interrompre (mais tu perdrais le test).
echo.

"%PY%" "%BANC%"
set CODE=%ERRORLEVEL%

echo.
if not "%CODE%"=="0" goto :avec_erreur

echo ======================================================
echo   C'EST PRET
echo ======================================================
echo.
echo   Ecoute les passages, note ceux qui portent un SOUFFLE, puis
echo   dis-le a Cline : il croisera tes notes avec la cle.
echo.
start "" explorer "%LOT%\A_ECOUTER"
timeout /t 2 /nobreak >nul
if exist "%LOT%\A_ECOUTER\LISEZ-MOI.txt" start "" notepad.exe "%LOT%\A_ECOUTER\LISEZ-MOI.txt"
echo.
pause
exit /b 0

:avec_erreur
echo   Le banc s'est arrete (code %CODE%).
echo.
echo   Si le message parle du port 8086, c'est que le moteur tourne
echo   encore : FERME NIMM ePub, puis relance ce fichier.
echo.
pause
exit /b %CODE%

:pas_de_python
echo   LE MOTEUR N'EST PAS INSTALLE ICI : %PY%
echo.
pause
exit /b 1

:pas_de_banc
echo   SCRIPT INTROUVABLE : %BANC%
echo.
pause
exit /b 1

:pas_de_voix
echo   LES VOIX SONT INTROUVABLES : qwen_tts_service\voix\references.csv
echo.
pause
exit /b 1

:pas_de_modele
echo   LE MODELE EST INTROUVABLE : qwen-talker-0.6b-base-Q4_K_M.gguf
echo.
pause
exit /b 1
