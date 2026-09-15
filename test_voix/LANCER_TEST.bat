@echo off
chcp 65001 >nul
title Test attribution de voix - NIMM ePub
echo.
echo  Test d'attribution des personnages (Claude / Mistral / Gemini)
echo.
cd /d "%~dp0"
python test_attribution.py
echo.
pause
