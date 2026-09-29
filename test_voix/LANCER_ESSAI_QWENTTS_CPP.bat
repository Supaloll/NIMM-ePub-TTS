@echo off
chcp 65001 >nul
title NIMM ePub - ESSAI qwentts.cpp : lecteur branche sur le moteur de NIMM Voix
cd /d "%~dp0.."

rem ============================================================
rem  ESSAI qwentts.cpp -- 28/09/2026, demande de Laurent :
rem  ecouter le livre 28 avec les voix Qwen lues par le moteur
rem  de NIMM Voix, qui tourne sur le PROCESSEUR et ne prend
rem  donc PAS la carte graphique.
rem
rem  CE QUE FAIT CE LANCEUR : il branche le lecteur sur le
rem  service de NIMM Voix -- port 8087 -- au lieu de notre
rem  service Qwen local, puis il lance le lecteur normalement.
rem  Une seule chose est posee : la variable NIMM_QWEN_URL.
rem  Ni fichier, ni base, ni voix ne sont modifies ici.
rem
rem  A FAIRE AVANT, en un double-clic :
rem    G:\NIMM Voix\DEMARRER_QWENTTS_CPP.cmd
rem  et LAISSER SA FENETRE OUVERTE -- c'est le moteur.
rem
rem  POUR REVENIR A LA NORMALE : fermer la fenetre du moteur de
rem  NIMM Voix, puis relancer  START.bat  simplement.
rem ============================================================

echo.
echo   ==========================================================
echo    ESSAI qwentts.cpp : le lecteur branche sur NIMM Voix
echo   ==========================================================
echo.

set NIMM_QWEN_URL=http://127.0.0.1:8087

echo   Verification du moteur de NIMM Voix sur le port 8087...
curl -s -o NUL --max-time 3 http://127.0.0.1:8087/sante >nul 2>&1
if errorlevel 1 goto moteur_absent

echo.
echo   Le moteur repond : les voix Qwen du livre 28 seront lues par lui.
echo.
echo   Le lecteur va s'ouvrir dans une autre fenetre. Laisse-la ouverte,
echo   ouvre le livre 22/11/63 et lance un chapitre.
echo.
pause
call START.bat
exit /b 0

:moteur_absent
echo.
echo   Le moteur de NIMM Voix ne repond PAS sur le port 8087.
echo.
echo   Fais ceci AVANT de relancer ce lanceur :
echo     1. ouvre le dossier  G:\NIMM Voix
echo     2. double-clique sur  DEMARRER_QWENTTS_CPP.cmd
echo     3. attends la ligne  Service pret : http://127.0.0.1:8087
echo     4. garde cette fenetre ouverte, puis relance ce lanceur.
echo.
echo   Tant que le moteur est eteint, les voix Qwen du livre 28
echo   n'apparaitraient meme pas dans les menus du lecteur.
echo.
pause
exit /b 1
