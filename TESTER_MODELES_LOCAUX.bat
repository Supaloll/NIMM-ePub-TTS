@echo off
chcp 65001 >nul
title NIMM ePub - test des modeles locaux (gratuit)
cd /d "%~dp0"

echo.
echo  ============================================================
echo   TEST DES MODELES DE LANGUE LOCAUX  -  aucun euro depense
echo  ============================================================
echo.
echo   Ce test compare trois modeles locaux NOUVEAUX (qwen3,
echo   aya-expanse, granite3.3) sur trois chapitres deja castes par
echo   Gemini, qui sert de reference. Il mesure la qualite et le temps,
echo   puis ecrit un rapport lisible.
echo.
echo   IMPORTANT : si les telechargements ne sont pas termines, ce
echo   script ATTEND tout seul (verification toutes les 30 secondes).
echo   Tu peux donc le lancer et aller dormir.
echo.
echo   Duree : 15 a 30 minutes une fois les modeles telecharges.
echo   Rapport : data\rapport_modeles_locaux.txt
echo   Pour l'arreter : Ctrl+C.
echo.

python test_voix\_test_nuit_modeles.py 4,12,20 "qwen3:8b,aya-expanse:8b,granite3.3:8b"

echo.
echo  ============================================================
echo   TERMINE - rapport : data\rapport_modeles_locaux.txt
echo  ============================================================
pause

