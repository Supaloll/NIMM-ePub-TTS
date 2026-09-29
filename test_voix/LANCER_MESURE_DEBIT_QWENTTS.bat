@echo off
chcp 65001 >nul
title NIMM ePub - debit du moteur Qwen selon les reglages du processeur
cd /d "%~dp0.."

rem ============================================================
rem  DEBIT DU MOTEUR QWEN (qwentts.cpp) SELON LE PROCESSEUR
rem  (29/09/2026, question de Laurent : « c'est optimisable ? »)
rem
rem  A quoi ca sert : le moteur tourne deja a x0,94 le temps reel
rem  avec les trois reglages du service. Ce banc mesure ce qu'il
rem  reste a prendre du cote du PROCESSEUR : 4, 6, 8 et 12 coeurs,
rem  plus deux configurations EPINGLEES si tu ajoutes --affinite.
rem
rem  Ce qui va se passer : le processeur travaille a PLEIN pendant
rem  cinq a dix minutes. Le ventilateur peut se faire entendre : c'est
rem  NORMAL, ce sont exactement les memes calculs que pendant la
rem  lecture d'un livre, juste groupes au lieu d'etre etales. Un
rem  processeur qui chauffe se ralentit tout seul : il ne casse pas.
rem
rem  Rien n'est modifie : ni la base, ni les voix, ni le service.
rem  Le moteur doit etre ETEINT pour que la mesure soit juste : si
rem  le service repond sur le port 8086, le banc refuse de partir.
rem ============================================================

echo.
echo   ==========================================================
echo    DEBIT DU MOTEUR QWEN -- SELON LES REGLAGES DU PROCESSEUR
echo   ==========================================================
echo.

if not exist "qwentts_service\.venv\Scripts\python.exe" (
    echo  Le moteur Qwen n'est pas installe sur ce PC.
    echo  Voir : qwentts_service\LIRE_MOI.md
    echo.
    pause
    exit /b 1
)

if not exist "qwentts_service\models\qwen-talker-0.6b-base-Q8_0.gguf" (
    echo  Les MODELES du moteur sont absents : qwentts_service\models\
    echo  Attendus : qwen-talker-0.6b-base-Q8_0.gguf et
    echo             qwen-tokenizer-12hz-Q8_0.gguf
    echo.
    pause
    exit /b 1
)

echo  Verifie que le moteur n'est pas deja allume...
curl -s -o NUL --max-time 3 http://127.0.0.1:8086/sante
if not errorlevel 1 (
    echo.
    echo  Le moteur Qwen REPOND deja sur le port 8086.
    echo  Ferme sa fenetre, puis relance ce banc :
    echo  sinon les deux se partageraient les coeurs et les chiffres
    echo  ne voudraient rien dire.
    echo.
    pause
    exit /b 1
)

echo  Le moteur est eteint : c'est bon.
echo  Compte de 5 a 10 minutes, selon le nombre de configurations.
echo  Le detail defile ici, ligne par ligne.
echo.

"qwentts_service\.venv\Scripts\python.exe" "test_voix\_mesurer_debit_qwentts.py" %*

echo.
echo ----------------------------------------------------------
echo  Rien n'a ete modifie dans le projet.
echo  A lire : le RESUME DE LA CAMPAGNE, a la fin.
echo  Le reglage d'aujourd'hui reste 6 coeurs, 4 fils de codec,
echo  tranches de 2 images -- c'est celui du service.
echo ----------------------------------------------------------
pause >nul
