@echo off
chcp 65001 >nul
title NIMM ePub - banc de qualite des voix Qwen
cd /d "%~dp0.."

rem ============================================================
rem  BANC DE QUALITE DES VOIX QWEN (29/09/2026)
rem
rem  A quoi ca sert : Laurent a entendu un GARGOUILLIS en changeant
rem  la voix de Lord_ivrogne (livre 35). Ce banc fait dire une ou
rem  deux phrases courtes a CHACUNE des voix Qwen, mesure la duree
rem  de l'audio rendu, et dit lesquelles DERIVENT (l'audio est
rem  beaucoup trop long : le moteur s'emballe et n'arrete jamais) ou
rem  rendent du silence.
rem
rem  Rien n'est modifie : ni la base, ni les voix, ni les notes.
rem  Les WAV des voix fautives sont poses dans
rem  test_voix\sortie_banc_voix_qwen\ pour que Laurent les ecoute.
rem
rem  Compte environ 20 a 40 minutes : les voix fautives peuvent
rem  demander deux minutes chacune.
rem ============================================================

echo.
echo   ==========================================================
echo    BANC DE QUALITE DES VOIX QWEN
echo   ==========================================================
echo.

rem -- Le moteur Qwen doit etre allume (fenetre « appareil de voix Qwen3-TTS »).
curl -s -o NUL --max-time 3 http://127.0.0.1:8086/sante
if errorlevel 1 (
    echo  Le moteur Qwen ne repond pas : il doit etre allume.
    echo  Ouvre d'abord : qwentts_service\DEMARRER_QWENTTS_CPP.bat
    echo  ^(ou lance START.bat, qui l'allume tout seul.^)
    echo.
    pause
    exit /b 1
)

echo  Le moteur repond. C'est parti -- compte 20 a 40 minutes.
echo  Laisse cette fenetre ouverte : tu verras defiler chaque voix.
echo.

python "test_voix\_banc_qualite_voix_qwen.py" %*

echo.
echo ----------------------------------------------------------
echo  Rien n'a ete modifie dans le projet.
echo  A lire : le RESUME, a la fin de ce qui vient de defiler.
echo  A ecouter : test_voix\sortie_banc_voix_qwen\
echo ----------------------------------------------------------
pause >nul
