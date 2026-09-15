@echo off
chcp 65001 >nul
title NIMM ePub - ecoute du test du moteur XTTS v2
cd /d "%~dp0"

rem ============================================================
rem  Joue les fichiers d'ecoute du moteur XTTS v2, l'un apres
rem  l'autre (ils ont ete produits par tester_service.py).
rem  Aucune application ne s'ouvre : la lecture se fait dans la
rem  fenetre, et on entend chaque fichier jusqu'au bout.
rem
rem  Rappel sur les voix : elles sont CLONEES a partir des extraits
rem  CML-TTS (CC BY 4.0), les memes que le moteur Kyutai -- c'est
rem  ce qui permet de comparer les deux moteurs de vive voix.
rem ============================================================

if not exist "sortie_ecoute\voix01_phrase1.wav" (
  echo.
  echo  Aucun fichier a ecouter pour l'instant.
  echo.
  echo  Pour en fabriquer : allume d'abord le moteur (DEMARRER_XTTS.bat),
  echo  puis lance dans une autre fenetre :
  echo      .venv\Scripts\python.exe tester_service.py
  echo.
  pause
  exit /b 1
)

for %%f in ("sortie_ecoute\voix*.wav") do (
  echo.
  echo   Lecture : %%~nxf
  powershell -NoProfile -Command "(New-Object Media.SoundPlayer '%~dp0sortie_ecoute\%%~nxf').PlaySync()"
)

echo.
echo  Ecoute terminee.
echo.
pause
