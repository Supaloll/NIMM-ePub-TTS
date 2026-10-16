@echo off
chcp 65001 >nul
setlocal
title NIMM ePub - OUVRIR UN LOT POUR L'ECOUTER
cd /d "%~dp0.."

rem ============================================================
rem  OUVRIR UN LOT D'ECOUTE, RECOLLE EN UN FICHIER PAR NOM
rem  (16/10/2026, pour Laurent : « je n'ai pas les liens pour les
rem   ecouter »)
rem
rem  CE QU'IL FAIT : il prend un dossier de lot et recolle les prises
rem  de chaque nom EN UN SEUL FICHIER, dans l'ordre, avec 0,70 s de
rem  silence entre elles. Puis il ouvre le dossier d'ecoute et sa
rem  notice.
rem
rem  COMMENT S'EN SERVIR :
rem    - DOUBLE-CLIC        -> il prend le DERNIER lot fabrique ;
rem    - GLISSER-DEPOSER un dossier de lot sur ce fichier -> celui-la.
rem
rem  Le dossier d'ecoute s'appelle POUR_ECOUTER : il est refabrique a
rem  chaque passage (n'y range rien). Les prises d'origine, elles, ne
rem  sont JAMAIS touchees.
rem
rem  Aucun moteur a allumer, rien de facture : c'est du recollage de
rem  fichiers WAV, rien de plus.
rem ============================================================

set DOSSIER=%~1
if not "%DOSSIER%"=="" goto :dossier_pret
if exist "test_voix\_dernier_lot_got_auto.txt" set /p DOSSIER=<"test_voix\_dernier_lot_got_auto.txt"
if not "%DOSSIER%"=="" goto :dossier_pret
if exist "test_voix\_dernier_lot_prenoms.txt" set /p DOSSIER=<"test_voix\_dernier_lot_prenoms.txt"
if not "%DOSSIER%"=="" goto :dossier_pret

echo.
echo   Je n'ai pas trouve de lot. Glisse un dossier de lot sur ce
echo   fichier, ou lance d'abord un banc d'ecoute.
echo.
pause
exit /b 1

:dossier_pret
echo ======================================================
echo   NIMM ePub - OUVRIR UN LOT POUR L'ECOUTER
echo ======================================================
echo.
echo   Lot : %DOSSIER%
echo.
echo   Je recolle les prises de chaque nom en UN fichier, dans
echo   l'ordre, pour que tu n'aies pas a cliquer 39 fois.
echo.

python "test_voix\_grouper_un_lot.py" "%DOSSIER%"
set CODE=%ERRORLEVEL%

echo.
if not "%CODE%"=="0" goto :avec_erreur

echo ======================================================
echo   C'EST PRET
echo ======================================================
echo.
echo   Le dossier d'ecoute s'ouvre, avec sa notice A_LIRE.txt.
echo.
echo   Pour tout ecouter d'affilee : double-clic sur
echo   00_ECOUTER_DANS_L_ORDRE.m3u (si tu as VLC ou Media Player).
echo.
echo   Sinon, ouvre les fichiers un par un : chacun contient les
echo   trois prises du meme nom, dans l'ordre annonce par son nom.
echo.
start "" explorer "%DOSSIER%\POUR_ECOUTER"
timeout /t 2 /nobreak >nul
if exist "%DOSSIER%\POUR_ECOUTER\A_LIRE.txt" start "" notepad.exe "%DOSSIER%\POUR_ECOUTER\A_LIRE.txt"
pause
exit /b 0

:avec_erreur
echo   Le recollage s'est arrete, code %CODE%.
echo   Verifie que le dossier du lot existe bien, et qu'il contient
echo   des fichiers .wav.
echo.
pause
exit /b %CODE%
