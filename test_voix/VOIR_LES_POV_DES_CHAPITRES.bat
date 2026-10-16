@echo off
rem ---------------------------------------------------------------------
rem  LA CARTE DES POV : qui raconte chaque chapitre ?
rem  NIMM ePub -- 15/10/2026 -- demande de Laurent : avant d'ecouter
rem  "Le Trone de Fer", voir ce qu'on ARRIVERAIT a reconnaitre.
rem
rem  Dans cette saga, chaque chapitre est ecrit du point de vue d'un
rem  personnage (troisieme personne focalisee) : le narrateur du chapitre
rem  EST ce personnage ("BRAN", "CATELYN", "EDDARD"...). Cet outil dit,
rem  chapitre par chapitre, le nom reconnu -- et surtout la liste des
rem  chapitres ou l'on n'arrive a RIEN.
rem
rem  Il lit les 15 tomes de  D:\Livres Epub\Le Trone de Fer
rem  (dossier modifiable en tete du script).
rem
rem  LECTURE SEULE : rien n'est modifie (ni la base, ni le lecteur),
rem  aucun moteur a allumer, rien de facture.
rem
rem  Le detail complet s'ouvre a la fin dans le Bloc-notes.
rem  ASCII pur : aucun accent, aucun caractere special.
rem ---------------------------------------------------------------------
setlocal
title LA CARTE DES POV - NIMM ePub
cd /d "%~dp0.."

set OUTIL=test_voix\_voir_pov_chapitres.py
set RAPPORT=test_voix\sortie_pov_chapitres.txt

if not exist "%OUTIL%" goto :pas_d_outil
where python >nul 2>&1
if errorlevel 1 goto :pas_de_python

echo ======================================================
echo   NIMM ePub - LA CARTE DES POV
echo   QUI RACONTE CHAQUE CHAPITRE ?
echo ======================================================
echo.
echo   Il lit les 15 tomes de "Le Trone de Fer" et dit, chapitre
echo   par chapitre, quel personnage raconte -- et lesquels
echo   echappent a la reconnaissance.
echo.
echo   LECTURE SEULE : rien n'est modifie, rien n'est facture.
echo   Compte quelques secondes.
echo.

python "%OUTIL%"
set CODE=%ERRORLEVEL%
echo.
if not "%CODE%"=="0" goto :avec_erreur

echo ======================================================
echo   C'EST FAIT -- le detail complet va s'ouvrir
echo ======================================================
echo.
echo   Dans le fichier qui s'ouvre :
echo.
echo     - "POV RECONNUS"  : les noms lus dans les titres ;
echo     - "POV LU DANS LE TEXTE" : les tomes ou le nom ouvre
echo       le chapitre (a confirmer) ;
echo     - "CHAPITRES SANS POV" : ceux ou l'on n'arrive a rien.
echo       C'est LA que se cachent les surnoms ("Le lord perdu",
echo       "Le domestique du marchand") et les pages de garde.
echo.
echo   Dis a Cline ce que tu veux qu'on fasse de ces surnoms.
echo.
start "" notepad.exe "%RAPPORT%"
pause
exit /b 0

:avec_erreur
echo   L'outil s'est arrete (code %CODE%). Lis le message ci-dessus.
echo.
pause
exit /b %CODE%

:pas_de_python
echo   PYTHON EST INTROUVABLE.
echo   Ouvre NIMM ePub une fois (START.bat), puis reessaie.
echo.
pause
exit /b 1

:pas_d_outil
echo   SCRIPT INTROUVABLE : %OUTIL%
echo.
pause
exit /b 1
