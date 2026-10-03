@echo off
chcp 65001 >nul
title NIMM ePub - Recoudre les silences trop longs (Pocket, sans perdre la voix)
cd /d "%~dp0.."

rem ============================================================
rem  RECOUDRE LES SILENCES TROP LONGS  (30/09/2026)
rem
rem  L'idee : le modele francais 24 couches (A) fait des TROUS
rem  au milieu des phrases (mesure : 4 silences dont un de 2,02 s
rem  dans la premiere phrase ; au banc, 2,30 s). Le 6 couches (B)
rem  n'en fait presque pas -- mais Laurent prefere les VOIX de A.
rem
rem  Or un silence trop long n'est pas de la voix : c'est du temps
rem  mort. On le COUPE, exactement comme le lecteur rogne deja la
rem  queue des phrases des autres moteurs.
rem
rem  Ce que fait ce lanceur : il relit le dernier lot d'ecoute
rem  (mesure_pocket_... ou banc_reglages_pocket_...) et ecrit des
rem  versions RECOUSUES de chaque WAV, une par plafond :
rem      S45 = on ne garde jamais plus de 0,45 s de silence interne
rem      S35 = 0,35 s
rem      S25 = 0,25 s
rem  La voix n'est PAS touchee : seuls les temps morts sont coupes
rem  (milieu du silence conserve, fondu de 10 ms aux jonctions).
rem
rem  Aucun moteur, aucune base, aucun acces reseau : quelques
rem  secondes seulement.
rem ============================================================

echo.
echo   ==========================================================
echo    RECOUDRE LES SILENCES TROP LONGS
echo   ==========================================================
echo.
echo   Pour chaque phrase, tu entendras :
echo      l'original, puis S45, S35, S25.
echo.
echo   La question n'est pas "lequel est le plus rapide" mais :
echo      - la respiration est-elle naturelle (S45) ou etouffee (S25) ?
echo      - la pause genante et le mot redit ont-ils disparu ?
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo  Python n'est pas trouve dans le PATH de cette fenetre.
    echo  Verifie l'installation de Python, puis relance.
    echo.
    pause
    exit /b 1
)

if not exist "test_voix\_banc_resserrage_silences.py" (
    echo  L'outil est absent : test_voix\_banc_resserrage_silences.py
    echo.
    pause
    exit /b 1
)

echo  TRAITEMENT EN COURS (quelques secondes)...
echo.

python "test_voix\_banc_resserrage_silences.py"
if errorlevel 1 (
    echo.
    echo  Le traitement s'est arrete : lis le message ci-dessus.
    echo.
    pause
    exit /b 1
)

echo.
echo  Ouverture du dossier des WAV recousus...
echo.

if exist "test_voix\_dernier_recousu.txt" (
    set /p DOSSIER_RECOUSU=<"test_voix\_dernier_recousu.txt"
) else (
    set DOSSIER_RECOUSU=
)

if not "%DOSSIER_RECOUSU%"=="" (
    start "" "%DOSSIER_RECOUSU%"
) else (
    echo  Je n'ai pas retrouve le dossier : ouvre-le a la main,
    echo  il s'appelle "recousu_..." et il est dans le dernier lot
    echo  d'ecoute de test_voix.
)

echo.
echo  ==========================================================
echo   A ECOUTER : l'original, puis S45, S35, S25 (meme phrase).
echo   Dis simplement lequel sonne le mieux : c'est ton oreille
echo   qui decide du plafond.
echo  ==========================================================
echo.
pause
