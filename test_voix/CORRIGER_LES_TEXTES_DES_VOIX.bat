@echo off
rem ---------------------------------------------------------------------
rem  CORRIGER LES TEXTES DES VOIX  -  NIMM ePub  (02/10/2026)
rem
rem  Double-clic : ouvre une page dans ton navigateur ou tu ECOUTES la
rem  reference de chaque voix et tu REECRIS, a l'oreille, ce qu'elle dit
rem  vraiment. Tes corrections sont enregistrees tout de suite dans
rem  test_voix\_corrections_oreille.csv : jamais perdues.
rem
rem  POURQUOI : le clonage d'une voix s'appuie sur le texte de sa
rem  reference. S'il ne colle pas a l'audio (mot incomplet au debut ou a
rem  la fin, mot manquant), le moteur fabrique un mot parasite au debut
rem  des phrases. C'est ce defaut que Laurent a entendu.
rem
rem  RIEN N'EST APPLIQUE AUX VOIX : remplacer le texte de production est
rem  un geste separe, apres son accord.
rem
rem  Aucun moteur n'a besoin d'etre allume (ni lecteur, ni Qwen).
rem  Pour quitter : le bouton "Arreter l'outil" de la page, ou ferme cette
rem  fenetre noire.
rem
rem  ASCII pur : aucun accent, aucun caractere special.
rem ---------------------------------------------------------------------
setlocal
title CORRIGER LES TEXTES DES VOIX - NIMM ePub
cd /d "%~dp0.."

if not exist "qwen_tts_service\voix\references.csv" goto :pas_de_fichier
if not exist "test_voix\_corriger_references_a_l_oreille.py" goto :pas_d_outil

echo ======================================================
echo   NIMM ePub - CORRIGER LES TEXTES DES VOIX A L OREILLE
echo ======================================================
echo.
echo   La page va s'ouvrir dans ton navigateur (3 secondes).
echo.
echo   ECOUTE le debut de la reference, puis REECRIS exactement ce que
echo   tu entends. Ctrl+Entree enregistre et passe a la voix suivante.
echo.
echo   Rien n'est applique aux voix : tes corrections attendent.
echo.
echo   Pour ARRETER : le bouton de la page, ou ferme cette fenetre.
echo.

python "test_voix\_corriger_references_a_l_oreille.py"
set CODE=%ERRORLEVEL%

echo.
if not "%CODE%"=="0" goto :avec_erreur

echo   Outil arrete. Tes corrections sont dans :
echo   test_voix\_corrections_oreille.csv
echo.
pause
exit /b 0

:avec_erreur
echo   L'outil s'est arrete avec le code %CODE%.
echo.
echo   Si le message parle du port 8099, c'est qu'une autre fenetre
echo   utilise deja la page. Ferme-la, puis relance ce fichier.
echo.
pause
exit /b %CODE%

:pas_de_fichier
echo ======================================================
echo   FICHIER INTROUVABLE
echo ======================================================
echo.
echo   qwen_tts_service\voix\references.csv est absent.
echo   Ce fichier est la liste des voix du moteur Qwen.
echo.
pause
exit /b 1

:pas_d_outil
echo ======================================================
echo   SCRIPT INTROUVABLE
echo ======================================================
echo.
echo   test_voix\_corriger_references_a_l_oreille.py est absent.
echo.
pause
exit /b 1
