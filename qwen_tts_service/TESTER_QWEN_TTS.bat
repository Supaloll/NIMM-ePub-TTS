@echo off
chcp 65001 >nul
title NIMM ePub - ecouter les voix Qwen3-TTS
cd /d "%~dp0"

rem ============================================================
rem  Fait lire quatre phrases de test par trois voix Qwen, et
rem  ecrit les fichiers dans  sortie_ecoute\  (a ecouter).
rem
rem  IL FAUT que le moteur tourne : double-clique d'abord sur
rem  DEMARRER_QWEN_TTS.bat, et LAISSE sa fenetre ouverte.
rem ============================================================

echo.
echo   ==========================================================
echo    ECOUTE DES VOIX QWEN3-TTS
echo   ==========================================================
echo.
echo   Il faut que le moteur tourne (fenetre DEMARRER_QWEN_TTS.bat
echo   ouverte). Sinon, ferme cette fenetre et allume-le d'abord.
echo.

curl -s -o NUL --max-time 3 http://127.0.0.1:8086/sante >nul 2>&1
if errorlevel 1 (
  echo   Le moteur Qwen NE REPOND PAS sur le port 8086.
  echo.
  echo   Double-clique d'abord sur DEMARRER_QWEN_TTS.bat, laisse sa
  echo   fenetre ouverte, puis relance ce test.
  echo.
  pause
  exit /b 1
)

python tester_service.py

echo.
echo ----------------------------------------------------------
echo  Les fichiers sont dans :  %~dp0sortie_ecoute
echo  Ouvre-les et ecoute (l'index dit quelle voix a lu quoi).
echo ----------------------------------------------------------
pause >nul
