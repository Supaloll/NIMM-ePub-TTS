@echo off
chcp 65001 >nul
title NIMM ePub - RE-CASTER UN LIVRE avec l'IA (PAYANT)
cd /d "%~dp0.."

rem ============================================================
rem  RE-CASTER UN LIVRE ENTIER avec Gemini -- PAYANT
rem
rem  POURQUOI CE LANCEUR : un livre deja caste ne peut PAS etre
rem  re-caste depuis l'interface (le casting ne refait jamais un
rem  chapitre deja analyse, pour ne pas payer deux fois). Ce
rem  lanceur fait donc la chose proprement :
rem     1. copie de surete DATE de ta base ;
rem     2. effacement de l'attribution du livre (la fiche des
rem        personnages est conservee) ;
rem     3. estimation du cout, et DEMANDE DE CONFIRMATION ;
rem     4. casting Gemini, avec la progression a l'ecran ;
rem     5. controles finaux (coherence de saga, voix lisibles).
rem
rem  Les voix des autres tomes de la meme saga sont REPRISES
rem  automatiquement.
rem
rem  Il faut que le lecteur soit allume : double-clique d'abord
rem  sur START.bat (a la racine du projet).
rem
rem  Double-clic sur ce fichier suffit : rien a taper.
rem ============================================================

echo.
echo ==========================================================
echo   RE-CASTER UN LIVRE AVEC L'IA  (ATTENTION : PAYANT)
echo ==========================================================
echo.
echo  Chaque appel d'IA est facture : compte environ 0,30 $
echo  pour un gros tome. Le script affichera l'estimation et te
echo  demandera de confirmer AVANT de payer quoi que ce soit.
echo.

rem -- Le lecteur repond-il ? (0,5 s de test, aucune erreur affichee)
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:8081/' -TimeoutSec 4 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo  Le lecteur n'est pas allume.
  echo  Double-clique d'abord sur  START.bat  a la racine du projet,
  echo  puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

set LIVRE=
set /p LIVRE=Numero du livre a re-caster (le Tome 6 de Monte-Cristo = 17) :
if "%LIVRE%"=="" (
  echo  Aucun numero saisi : arret.
  pause
  exit /b 1
)

set FOURNISSEUR=
set /p FOURNISSEUR=Fournisseur d'IA [gemini] :
if "%FOURNISSEUR%"=="" set FOURNISSEUR=gemini

echo.
python "test_voix\_PAYANT_recaster_un_livre.py" %LIVRE% --fournisseur %FOURNISSEUR% --je-paie

echo.
echo ==========================================================
echo   CONTROLES (lecture seule)
echo ==========================================================
echo.
python "test_voix\_controler_saga.py"
echo.
python "test_voix\_controler_voix_kyutai.py"

echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
