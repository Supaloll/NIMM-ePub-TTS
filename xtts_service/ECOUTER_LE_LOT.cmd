@echo off
chcp 65001 >nul
title NIMM ePub - ecoute des voix du domaine public (XTTS)
cd /d "%~dp0"

rem ============================================================
rem  Joue le lot d'ecoute, l'un apres l'autre : pour chaque voix,
rem  d'abord l'EXTRAIT DE REFERENCE puis le CLONE. Aucune
rem  application ne s'ouvre : la lecture se fait dans la fenetre.
rem ============================================================

for %%f in ("sortie_ecoute_dp\*.wav") do (
  echo.
  echo   Lecture : %%~nxf
  powershell -NoProfile -Command "(New-Object Media.SoundPlayer '%~dp0sortie_ecoute_dp\%%~nxf').PlaySync()"
)

echo.
echo  Ecoute terminee.
echo.
pause
