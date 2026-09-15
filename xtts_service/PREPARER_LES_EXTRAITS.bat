@echo off
chcp 65001 >nul
title NIMM ePub - preparer mes extraits de voix pour XTTS
cd /d "%~dp0"

rem ============================================================
rem  Prepare les extraits de voix (MP3) deposes dans
rem  ..\Extraits de voix\ pour le moteur XTTS du lecteur :
rem
rem    1. conversion en WAV mono 24 kHz 16 bits (format du
rem       moteur) + rognage des silences de bord, puis
rem       versement dans xtts_service\voix_fr\ ;
rem    2. fabrication du lot d'ecoute : pour chaque voix,
rem       l'EXTRAIT DE REFERENCE puis le CLONE du meme texte.
rem
rem  Le moteur doit etre allume (DEMARRER_XTTS.bat) : c'est lui
rem  qui clone. Une voix deja presente dans la banque n'est
rem  JAMAIS ecrasee (l'outil refuse et le dit).
rem
rem  Rappel de Laurent (15/09/2026) : les nouvelles voix ne
rem  sont PAS ajoutees au catalogue du lecteur ici -- l'ajout
rem  se fera en une seule fois, quand tout le lot sera pret.
rem ============================================================

rem -- 1) Le moteur repond-il ? (0,5 s de test, aucune erreur affichee)
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:8083/sante' -TimeoutSec 3 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo.
  echo  Le moteur XTTS n'est pas allume.
  echo  Double-clique d'abord sur DEMARRER_XTTS.bat, puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

echo.
echo ==========================================================
echo   1/2  Conversion + versement dans la banque du moteur
echo ==========================================================
python _preparer_extraits.py --verser
if errorlevel 1 goto fin

echo.
echo ==========================================================
echo   2/2  Lot d'ecoute (reference puis clone, pour chaque voix)
echo ==========================================================
python _ecouter_extraits_dp.py
if errorlevel 1 goto fin

echo.
choice /c ON /n /m " Ecouter le lot maintenant ? [O = oui, N = non] "
if errorlevel 2 goto fin
call ECOUTER_LE_LOT.cmd

:fin
echo.
echo  Termine. Pour ajouter ces voix au LECTEUR (menus et casting), il
echo  faudra l'ajout groupe prevu a la fin du lot : dis-le a Cline.
echo.
pause
