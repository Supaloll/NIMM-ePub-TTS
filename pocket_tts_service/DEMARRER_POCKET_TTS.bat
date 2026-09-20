@echo off
chcp 65001 >nul
title NIMM ePub - moteur de voix Pocket TTS
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   Le moteur n'est pas installe sur ce PC.
  echo   Double-clique d'abord sur  INSTALLER_POCKET_TTS.bat
  echo.
  pause
  exit /b 1
)

echo.
echo   ======================================================
echo    MOTEUR DE VOIX POCKET TTS (francais) - port 8085
echo   ======================================================
echo.
echo   C'est l'allumage A LA MAIN, pour un essai ou un diagnostic.
echo.
echo   En usage normal, c'est START.bat qui l'allume -- et il le
echo   fait SANS fenetre, en arriere-plan : Laurent n'a rien a
echo   ouvrir. Cette fenetre-ci sert a VOIR ce que dit le moteur.
echo.
echo   Fermer cette fenetre ETEINT le moteur.
echo.
echo   Premier demarrage : le modele se charge en quelques
echo   secondes, puis le moteur annonce ses voix.
echo.

".venv\Scripts\python.exe" servir_pocket_tts.py

echo.
echo   Le moteur est arrete.
pause
