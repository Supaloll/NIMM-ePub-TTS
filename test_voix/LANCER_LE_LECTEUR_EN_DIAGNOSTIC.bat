@echo off
rem ---------------------------------------------------------------------
rem  LANCER LE LECTEUR EN MODE DIAGNOSTIC -- NIMM ePub
rem  (03/10/2026, demande de Laurent : " je stoppe et je te dis de quelle
rem   phrase il s'agit " -- pour retrouver d'ou vient un SOUFFLE)
rem
rem  Double-clic : il allume le moteur (la carte), lance le LECTEUR avec le
rem  mode diagnostic, puis ouvre la page.
rem
rem  CE QUE LE MODE DIAGNOSTIC CHANGE, ET RIEN D'AUTRE :
rem    1. AUCUNE phrase n'est mise en cache -- ni lue, ni ecrite. Chaque
rem       phrase est REELLEMENT fabriquee au moment ou tu l'ecoutes ;
rem    2. chaque phrase laisse une TRACE dans
rem       test_voix\sortie_diagnostic_phrase\ : le texte avant et apres le
rem       nettoyage, la voix, la vitesse, la hauteur, et l'audio A CHAQUE
rem       ETAPE du traitement (moteur brut, rognage, vitesse, hauteur,
rem       normalisation, fondu), avec le niveau mesure de chacune.
rem
rem  A QUOI CA SERT : quand tu entends un souffle, tu notes la phrase et tu
rem  le dis. On ecoute alors les 6 etapes de CETTE phrase, l'une apres
rem  l'autre, et on entend A QUEL MOMENT le souffle arrive.
rem
rem  ATTENTION : la lecture est plus LENTE (tout est refabrique) -- c'est
rem  normal, c'est le prix de la tracabilite.
rem
rem  RIEN D'AUTRE N'EST TOUCHE : ni la base, ni les voix, ni les notes.
rem  ASCII pur : aucun accent, aucun caractere special.
rem ---------------------------------------------------------------------
setlocal
title LECTEUR EN DIAGNOSTIC - NIMM ePub
cd /d "%~dp0.."

if not exist "main.py" goto :pas_de_lecteur
if not exist "qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat" goto :pas_de_moteur
if not exist "test_voix\sortie_diagnostic_phrase" mkdir "test_voix\sortie_diagnostic_phrase"

echo ======================================================
echo   NIMM ePub - LECTEUR EN MODE DIAGNOSTIC
echo ======================================================
echo.
echo   1) j'allume le moteur sur la carte ;
echo   2) je lance le LECTEUR en mode diagnostic ;
echo   3) j'ouvre la page.
echo.
echo   En mode diagnostic : AUCUN cache. Chaque phrase est refabriquee,
echo   et sa trace est ecrite dans :
echo   test_voix\sortie_diagnostic_phrase\
echo.
echo   La lecture sera plus LENTE : c'est normal.
echo.
echo   Quand tu entends un souffle, note la phrase et dis-le.
echo.

echo   [1/3] le moteur...
start "Moteur Qwen (carte)" cmd /c "qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat"
timeout /t 8 /nobreak >nul

echo   [2/3] le lecteur, en mode diagnostic...
set NIMM_DIAGNOSTIC=1
start "Lecteur NIMM ePub (DIAGNOSTIC)" cmd /c "python main.py"
timeout /t 10 /nobreak >nul

echo   [3/3] la page...
start "" http://127.0.0.1:8081/

echo.
echo   C'est parti. Lis normalement, et note les phrases bizarres.
echo   (Les fenetres "Moteur" et "Lecteur" doivent rester ouvertes.)
echo.
echo   Appuie sur une touche pour fermer CETTE fenetre.
pause >nul
exit /b 0

:pas_de_lecteur
echo   main.py est introuvable : lance ce fichier depuis NIMM ePub.
echo.
pause
exit /b 1

:pas_de_moteur
echo   qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat est introuvable.
echo.
pause
exit /b 1
