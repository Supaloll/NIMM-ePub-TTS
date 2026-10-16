@echo off
chcp 65001 >nul
rem ---------------------------------------------------------------------
rem  LES POINTS D'EXCLAMATION SUR LA CARTE -- moteur Qwen Q8_0
rem  NIMM ePub -- 04/10/2026 -- chantier de Laurent :
rem  " voir si le moteur Qwen Q8_0 supporte maintenant les points
rem    d'exclamation lus comme de vrais points d'exclamation "
rem
rem  Aujourd'hui le lecteur RETIRE le "!" avant de donner le texte au
rem  moteur (virgule si la phrase est courte, point sinon) ; ce reglage a
rem  ete choisi a l'oreille le 18/09/2026 avec d'AUTRES moteurs (Kokoro,
rem  Edge). Ce banc fait dire la MEME voix, la MEME phrase, de SIX facons
rem  differentes, sur la carte, en Q8_0 -- et tu notes a l'aveugle.
rem
rem  IL REFUSE DE PARTIR SI LE MOTEUR TOURNE (port 8086) : les deux se
rem  partageraient la carte, et un repli silencieux sur le processeur
rem  fausserait tout le test. Il REFUSE aussi si la carte est saturee
rem  (memoire video insuffisante : lecon du 03/10/2026).
rem
rem  RIEN N'EST MODIFIE : ni la base, ni les voix, ni le service.
rem  ASCII/UTF-8 possible ; aucun caractere exotique.
rem ---------------------------------------------------------------------
setlocal
title ECOUTER LES EXCLAMATIONS SUR LA CARTE - NIMM ePub
cd /d "%~dp0.."

set PY=qwentts_service\.venv\Scripts\python.exe
set BANC=test_voix\_banc_qwen_exclamations.py
set SUIVI=test_voix\_dernier_banc_exclamations.txt

if not exist "%PY%" goto :pas_de_python
if not exist "%BANC%" goto :pas_de_banc
if not exist "qwen_tts_service\voix\references.csv" goto :pas_de_voix
if not exist "qwentts_service\models\qwen-talker-0.6b-base-Q8_0.gguf" goto :pas_de_modele

echo ======================================================
echo   NIMM ePub - LES POINTS D'EXCLAMATION SUR LA CARTE
echo ======================================================
echo.
echo   Le moteur Qwen Q8_0 (carte graphique) va dire la MEME voix,
echo   la MEME phrase, de SIX facons differentes. Les fichiers
echo   portent des noms au hasard : tu ecoutes a l'aveugle.
echo.
echo   AVANT DE COMMENCER : FERME NIMM ePub. Le moteur occupe la
echo   carte, et le banc REFUSE de partir s'il tourne encore.
echo.
echo   Compte quelques minutes. Ferme cette fenetre pour interrompre.
echo.

"%PY%" "%BANC%"
set CODE=%ERRORLEVEL%

echo.
if not "%CODE%"=="0" goto :avec_erreur

echo ======================================================
echo   C'EST PRET
echo ======================================================
echo.
echo   Le dossier d'ecoute va s'ouvrir, avec LISEZ-MOI.txt.
echo   Fais chaque dossier PHRASE_NN (le fichier 00_PASSAGE en
echo   premier), classe les six facons, puis dis-moi tes notes.
echo.
if not exist "%SUIVI%" goto :pas_de_suivi
set /p LOT=<"%SUIVI%"
start "" explorer "%LOT%"
timeout /t 2 /nobreak >nul
if exist "%LOT%\LISEZ-MOI.txt" start "" notepad.exe "%LOT%\LISEZ-MOI.txt"
echo.
pause
exit /b 0

:pas_de_suivi
start "" explorer "test_voix"
echo.
pause
exit /b 0

:avec_erreur
echo   Le banc s'est arrete (code %CODE%).
echo.
echo   - message sur le port 8086 : FERME NIMM ePub, puis relance.
echo   - message sur la memoire video : ferme ce qui occupe la carte
echo     (jeu, navigateur, autre moteur), puis relance.
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
echo   LE MODELE Q8_0 EST INTROUVABLE : qwen-talker-0.6b-base-Q8_0.gguf
echo.
pause
exit /b 1
