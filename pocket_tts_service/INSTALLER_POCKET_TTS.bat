@echo off
chcp 65001 >nul
title NIMM ePub - installation de Pocket TTS
rem ---------------------------------------------------------------------
rem  INSTALLER POCKET TTS (moteur de voix Kyutai, avec le FRANCAIS)
rem
rem  Ce que fait ce script, et RIEN d'autre :
rem    1. il cree un environnement dedie  pocket_tts_service\.venv ;
rem    2. il installe PyTorch en version CPU (environ 300 Mo au lieu de
rem       3 Go : Pocket TTS n'a PAS besoin de la carte graphique -- Kyutai,
rem       ses auteurs, ont mesure qu'il n'y gagne rien) ;
rem    3. il installe le paquet pocket-tts ;
rem    4. il verifie que les deux repondent.
rem
rem  Duree : 5 a 15 minutes (telechargement). La fenetre peut sembler
rem  figee pendant l'installation : c'est normal.
rem
rem  Rien n'est modifie ailleurs sur le PC. Le modele francais (641 Mo)
rem  est DEJA dans le cache Hugging Face de cette machine : il n'est pas
rem  retelcharge.
rem
rem  Peut etre relance sans risque : ce qui est deja installe est saute.
rem ---------------------------------------------------------------------
setlocal
cd /d "%~dp0"

set JOURNAL=%~dp0journal_installation.txt

echo ======================================================
echo   INSTALLATION DE POCKET TTS (voix francaises)
echo ======================================================
echo.
echo   Duree : 5 a 15 minutes. La fenetre peut sembler figee : normal.
echo.

echo   1/4  Creation de l'environnement dedie...
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if not exist ".venv\Scripts\python.exe" (
  echo   ECHEC : impossible de creer l'environnement.
  echo   Verifier que Python 3.14 est installe et accessible avec "python".
  if "%~1" neq "/auto" pause
  exit /b 1
)

echo   2/4  Mise a jour de pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip > "%JOURNAL%" 2>&1

echo   3/4  Installation de PyTorch (version CPU, environ 300 Mo)...
".venv\Scripts\python.exe" -m pip install torch --index-url https://download.pytorch.org/whl/cpu >> "%JOURNAL%" 2>&1

echo   4/4  Installation de pocket-tts...
".venv\Scripts\python.exe" -m pip install pocket-tts >> "%JOURNAL%" 2>&1

echo.
echo   Verification...
".venv\Scripts\python.exe" -c "import sys; sys.stdout.reconfigure(encoding='utf-8'); import torch, pocket_tts; print('torch', torch.__version__); print('pocket_tts : OK')" 2>&1
echo.
echo   Journal complet : %JOURNAL%
echo.
echo   Si vous voyez « torch 2.x » et « pocket_tts : OK » ci-dessus,
echo   l'installation a reussi. Etape suivante : DEMARRER_POCKET_TTS.bat
echo.
if "%~1" neq "/auto" pause
