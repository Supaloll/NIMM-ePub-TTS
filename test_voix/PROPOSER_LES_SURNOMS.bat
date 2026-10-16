@echo off
rem ---------------------------------------------------------------------
rem  LES SURNOMS DE POV : qui se cache derriere « SCHLINGUE », « LE NOYE »,
rem  « Le lord perdu » ?  NIMM ePub -- 15/10/2026 (chantier Le Trone de Fer).
rem
rem  Pourquoi : certains chapitres portent un SURNOM au lieu d'un prenom, et la
rem  carte des POV ne peut pas les deviner. Cet outil PROPOSE un rattachement, et
rem  il le PROUVE quand il peut : il compte, DANS le chapitre, combien de fois
rem  chaque personnage du casting est nomme (seuil 3).
rem
rem  Il n'ECRIT RIEN : il affiche, et il laisse son rapport dans
rem  test_voix\sortie_surnoms_pov.txt (le Bloc-notes s'ouvre a la fin).
rem  Pour ecrire un surnom, c'est Cline qui le fera avec toi, en le nommant :
rem     python test_voix/_proposer_surnoms_pov.py --livre <n> --ecrire "SURNOM=Personnage"
rem
rem  ASCII pur : aucun accent, aucun caractere special.
rem ---------------------------------------------------------------------
setlocal
title LES SURNOMS DE POV - NIMM ePub
cd /d "%~dp0.."

set OUTIL=test_voix\_proposer_surnoms_pov.py
set RAPPORT=test_voix\sortie_surnoms_pov.txt

if not exist "%OUTIL%" goto :pas_d_outil
where python >nul 2>&1
if errorlevel 1 goto :pas_de_python

echo ======================================================
echo   NIMM ePub - LES SURNOMS DE POV
echo   QUI SE CACHE DERRIERE CHAQUE SURNOM ?
echo ======================================================
echo.
echo   Il lit les chapitres des tomes et, pour chaque surnom,
echo   il regarde qui est NOMME dans le chapitre :
echo.
echo     - si le livre est caste : le compte est une PREUVE
echo       (une mention ou plus de 3 : la proposition tient) ;
echo     - sinon : ce ne sont que des PISTES, a verifier.
echo.
echo   LECTURE SEULE : rien n'est ecrit, rien n'est facture.
echo   Compte une vingtaine de secondes pour les 15 tomes.
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
echo     - "preuves (texte)"  : les personnages nommes dans le
echo       chapitre, avec leur nombre de mentions ;
echo     - ">>> PROPOSITION"  : un rattachement solide ;
echo     - "pistes"           : quand le texte ne tranche pas,
echo       a confirmer a la main.
echo.
echo   Dis a Cline ce que tu valides : c'est lui qui ecrit la table,
echo   et la carte des POV en tient compte tout de suite (F5).
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
