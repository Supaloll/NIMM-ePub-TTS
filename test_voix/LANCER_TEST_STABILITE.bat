@echo off
chcp 65001 >nul
title NIMM ePub - XTTS est-il STABLE ? (3 reglages compares)
cd /d "%~dp0"

rem ============================================================
rem  Genere LA MEME PHRASE plusieurs fois avec trois reglages du
rem  moteur XTTS, et affiche la STABILITE obtenue (ecart de duree,
rem  nombre de segments de parole).
rem
rem  Pourquoi : Laurent trouve XTTS inegal (« 3 phrases excellentes,
rem  puis il hachure, bafouille, traine ») alors que Kokoro redit
rem  toujours la meme chose. XTTS echantillonne (temperature 0,75
rem  par defaut) : ce banc mesure l'effet d'une generation plus
rem  SAGE (0,60 puis 0,45).
rem
rem  ATTENTION : le moteur XTTS doit avoir ete REDEMARRE apres le
rem  16/09/2026 (le parametre « reglages » a ete ajoute ce jour-la).
rem  Sinon les trois series seront identiques.
rem
rem  Resultat : un dossier stabilite_xtts_<date> avec les WAV, un
rem  index.txt et un ECOUTER_LE_LOT.cmd (double-clic).
rem
rem  Double-clic sur ce fichier suffit : rien a taper.
rem ============================================================

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
echo   Comparaison de stabilite (15 courtes syntheses)
echo ==========================================================
python _banc_stabilite_xtts.py
if errorlevel 1 goto fin

echo.
echo  Termine : un dossier  stabilite_xtts_^<date^>  vient d'etre cree.
echo  Ouvre-le et double-clique sur  ECOUTER_LE_LOT.cmd.

:fin
echo.
pause
