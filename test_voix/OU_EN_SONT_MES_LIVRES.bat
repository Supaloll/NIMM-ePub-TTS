@echo off
chcp 65001 >nul
title NIMM ePub - OU EN SONT MES LIVRES
cd /d "%~dp0.."

rem ============================================================
rem  OU EN SONT MES LIVRES : le tableau de bord, en une page
rem
rem  Pour chaque livre : combien de phrases, si la narration est
rem  separee des repliques (mode dialogue), la part de narration,
rem  le nombre de personnages et de "gros" locuteurs, les incises
rem  (muettes ou lues), et les locuteurs hors casting a revoir.
rem
rem  Lecture seule : rien n'est modifie, rien n'est facture.
rem ============================================================

echo.
echo   ==========================================================
echo    OU EN SONT MES LIVRES
echo   ==========================================================
echo.
echo   Une page : le decoupage de chaque livre, la part de
echo   narration, les personnages, les incises, et ce qui reste
echo   a revoir au casting.
echo.
echo   Lecture seule : rien n'est modifie.
echo.
pause

python "test_voix\_etat_des_livres.py"

echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
