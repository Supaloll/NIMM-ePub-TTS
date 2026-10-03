@echo off
rem ---------------------------------------------------------------------
rem  LES 35 VOIX KYUTAI : LES ECOUTER ET CORRIGER LEURS TEXTES
rem  NIMM ePub -- 03/10/2026 -- demande de Laurent
rem
rem  Double-clic :
rem    1. il prepare le lot -- bords propres : 150 ms de silence a chaque
rem       bord et fondu de 20 ms, AUCUN mot coupe (quelques secondes) ;
rem    2. il ouvre la page ou tu ECOUTES chaque voix et ou tu REECRIS son
rem       texte, mot pour mot, tel que tu l'entends.
rem
rem  POURQUOI (Laurent, 03/10/2026) : " beaucoup d'erreurs venaient d'une
rem  erreur de transcription, donc il faudrait les 35 passages audio plus
rem  les 35 transcriptions texte que je corrige a l'oreille. "
rem
rem  RIEN N'EST APPLIQUE AUX VOIX : les corrections attendent dans le lot,
rem  et les voix de production ne sont ni touchees ni deplacees.
rem  Aucun moteur n'a besoin d'etre allume. ASCII pur.
rem ---------------------------------------------------------------------
setlocal
title CORRIGER LES TEXTES DES VOIX KYUTAI - NIMM ePub
cd /d "%~dp0.."

set LOT=test_voix\lot_kyutai_bords_propres_20261003

if not exist "qwen_tts_service\voix\references.csv" goto :pas_de_voix
if not exist "test_voix\_preparer_lot_kyutai_recoupe.py" goto :pas_de_script
if not exist "test_voix\_corriger_references_a_l_oreille.py" goto :pas_de_script

echo ======================================================
echo   NIMM ePub - LES VOIX KYUTAI : ECOUTER ET CORRIGER
echo ======================================================
echo.
echo   ETAPE 1 : bords propres (marge de 150 ms + fondu de 20 ms,
echo   aucun mot coupe). Quelques secondes.
echo.

python "test_voix\_preparer_lot_kyutai_recoupe.py"
if not "%ERRORLEVEL%"=="0" goto :avec_erreur

echo.
echo   ETAPE 2 : la page d'ecoute va s'ouvrir.
echo.
echo   ECOUTE la voix, REECRIS son texte tel que tu l'entends,
echo   puis Ctrl+Entree : il enregistre et passe a la suivante.
echo.
echo   (Le bouton "Rejouer le debut" sert a entendre l'attaque ; pense a
echo   ecouter aussi la FIN.)
echo.
echo   Pour ARRETER : le bouton de la page, ou ferme cette fenetre.
echo.

python "test_voix\_corriger_references_a_l_oreille.py" --lot "%LOT%"

echo.
echo   Outil arrete. Tes corrections sont dans :
echo   %LOT%\_corrections_oreille.csv
echo.
echo   Quand tu as fini, dis-le a Cline : il reportera tes corrections.
echo.
pause
exit /b 0

:avec_erreur
echo   La preparation du lot s'est arretee en erreur.
echo   Regarde les lignes ci-dessus : elles disent pourquoi.
echo.
pause
exit /b 1

:pas_de_voix
echo   LES VOIX DE PRODUCTION SONT INTROUVABLES
echo   Fichier attendu : qwen_tts_service\voix\references.csv
echo.
pause
exit /b 1

:pas_de_script
echo   SCRIPT INTROUVABLE dans test_voix\
echo   (_preparer_lot_kyutai_recoupe.py et _corriger_references_a_l_oreille.py)
echo.
pause
exit /b 1
