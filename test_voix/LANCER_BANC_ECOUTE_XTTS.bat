@echo off
chcp 65001 >nul
title NIMM ePub - banc d'ecoute XTTS (qualite des phrases)
cd /d "%~dp0"

rem ============================================================
rem  Genere un petit LOT D'ECOUTE pour verifier la qualite des
rem  phrases XTTS : attaque du premier mot, incise, tiret en tete
rem  de replique, phrase ultra-courte, fin de phrase -- le tout
rem  sur DEUX voix (une aigue, une grave).
rem
rem  Pourquoi : le BACKLOG a un item « XTTS : defauts residuels
rem  entendus le 15/09/2026 ». Ce lot sert a ecouter l'etat
rem  d'aujourd'hui et a decider ce qui merite un remede.
rem
rem  Le moteur XTTS doit etre allume (DEMARRER_XTTS.bat) :
rem  c'est lui qui fabrique l'audio.
rem
rem  Resultat : un dossier ecoute_xtts_<date> contenant les WAV
rem  numerotes, un index.txt (quoi ecouter) et un lanceur
rem  ECOUTER_LE_LOT.cmd (double-clic).
rem
rem  Double-clic sur ce fichier suffit : rien a taper.
rem ============================================================

rem -- Le moteur XTTS repond-il ? (0,5 s de test, aucune erreur affichee)
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:8083/sante' -TimeoutSec 3 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo.
  echo  Le moteur XTTS n'est pas allume.
  echo  Double-clique d'abord sur  xtts_service\DEMARRER_XTTS.bat
  echo  puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

echo.
echo ==========================================================
echo   Fabrication du lot d'ecoute (une dizaine de phrases)
echo ==========================================================
python _banc_ecoute_xtts.py
if errorlevel 1 goto fin

echo.
echo  Termine : un dossier  ecoute_xtts_^<date^>  vient d'etre cree ici.
echo  Ouvre-le et double-clique sur  ECOUTER_LE_LOT.cmd  pour ecouter.

:fin
echo.
pause
