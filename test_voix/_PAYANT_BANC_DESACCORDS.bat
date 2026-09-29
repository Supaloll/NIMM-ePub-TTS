@echo off
chcp 65001 >nul
title NIMM ePub - le banc des desaccords (PAYANT)
cd /d "%~dp0"

rem ============================================================
rem  LE BANC DES DESACCORDS (24/09/2026)
rem
rem  A quoi ca sert : sur un VRAI chapitre, faire analyser le
rem  texte par plusieurs moteurs et ne montrer QUE les phrases ou
rem  ils ne sont PAS d'accord. C'est Laurent qui tranche, et on
rem  obtient une verite terrain sur du texte reel (le passage
rem  piege, lui, ne dit que « qui est le plus discipline »).
rem
rem  ATTENTION : les moteurs distants sont factures (un appel par
rem  moteur et par lot de 150 phrases). Le modele local est gratuit.
rem  Sans reponse « OUI », rien n'est appele.
rem
rem  Aucun moteur de voix ni serveur NIMM n'est necessaire.
rem ============================================================

echo.
echo  ============================================================
echo   LE BANC DES DESACCORDS
echo  ============================================================
echo.
echo   Rien a allumer : il interroge les API d'IA directement.
echo.
set LIVRE=28
set /p LIVRE=Numero du livre a analyser [%LIVRE%] :
if "%LIVRE%"=="" set LIVRE=28

echo.
echo   Liste des chapitres du livre %LIVRE% (index, titre, debut)...
echo.
python _PAYANT_banc_desaccords.py --livre %LIVRE% --liste-chapitres

set CHAPITRE=
set /p CHAPITRE=Numero de chapitre (colonne « index ») : 
if "%CHAPITRE%"=="" (
  echo  Aucun chapitre saisi : arret.
  pause
  exit /b 1
)

echo.
echo  ------------------------------------------------------------
echo   Verification GRATUITE : moteurs disponibles et cout estime
echo  ------------------------------------------------------------
echo.
python _PAYANT_banc_desaccords.py --livre %LIVRE% --chapitre %CHAPITRE% --verifier

echo.
choice /c ON /n /m "  Lancer pour de vrai (donc payer) ? [O = oui, N = non] "
if errorlevel 2 goto fin

echo.
echo  C'est parti (compte une a trois minutes)...
echo.
python _PAYANT_banc_desaccords.py --livre %LIVRE% --chapitre %CHAPITRE% --je-paie

:fin
echo.
echo  ============================================================
echo   Le rapport est enregistre dans
echo   test_voix\banc_desaccords_livre...txt
echo   (il contient des lignes « A TOI DE DIRE » a remplir)
echo  ============================================================
echo.
pause
