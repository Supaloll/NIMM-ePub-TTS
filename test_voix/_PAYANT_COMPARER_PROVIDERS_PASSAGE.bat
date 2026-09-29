@echo off
chcp 65001 >nul
title NIMM ePub - comparer les providers sur un passage piege (PAYANT)
cd /d "%~dp0"

rem ============================================================
rem  ESSAI DEMANDE PAR LAURENT LE 24/09/2026 : « quel provider
rem  s'en sort le mieux sur un passage court et litigieux ? »
rem
rem  Le passage est celui de  test_voix\passage_piege.txt : un
rem  texte de roman fabrique pour contenir les pieges que ce
rem  projet a repares (incise isolee, citation coupee par un
rem  « ! », beat qui annonce une replique, pere et fils
rem  homonymes).
rem
rem  ATTENTION : les providers DISTANTS sont factures sur tes
rem  cles. Le moteur local (Ollama) est gratuit. Sans reponse
rem  « OUI » ci-dessous, rien n'est appele.
rem
rem  Aucun moteur de voix ni serveur NIMM n'est necessaire : le
rem  script interroge les API d'IA directement. Ollama, lui, doit
rem  tourner si tu gardes le modele local dans la liste.
rem ============================================================

echo.
echo  ============================================================
echo   COMPARER LES PROVIDERS SUR UN PASSAGE PIEGE
echo  ============================================================
echo.
echo   Rien a allumer : ni serveur NIMM, ni moteur de voix
echo   (sauf Ollama, pour la ligne « modele local »).
echo.
echo   D'abord une verification GRATUITE : quelles cles sont la,
echo   et combien coute ce petit passage.
echo.

python _PAYANT_comparer_providers_passage.py --verifier

echo.
echo  ------------------------------------------------------------
echo   Rappel : pour ajouter OpenAI, ouvre  test_voix\cles_api.txt
echo   et ajoute une ligne :   OPENAI_API_KEY=ta_cle
echo   (Claude n'est pas dans la liste par defaut : trop cher.)
echo  ------------------------------------------------------------
echo.

choice /c ON /n /m "  Lancer pour de vrai (donc payer) ? [O = oui, N = non] "
if errorlevel 2 goto fin

set TOURS=2
set /p TOURS=Nombre d'essais par provider, 1 a 3 [%TOURS%] :
if "%TOURS%"=="" set TOURS=2

echo.
echo  C'est parti (passage court : compte une a deux minutes)...
echo.

python _PAYANT_comparer_providers_passage.py --je-paie --tours %TOURS%

:fin
echo.
echo  ============================================================
echo   Le rapport complet est enregistre dans
echo   test_voix\rapport_passage_piege_...txt
echo  ============================================================
echo.
pause
