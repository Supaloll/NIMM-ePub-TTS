@echo off
chcp 65001 >nul
setlocal
title NIMM ePub - ECOUTER LES PRENOMS ANGLAIS (22/11/63)
cd /d "%~dp0.."

rem ============================================================
rem  LES PRENOMS ANGLAIS DE 22/11/63 -- BANC D'ECOUTE (16/10/2026)
rem
rem  Demande de Laurent : « que la prononciation se fasse a
rem  l'anglaise quand ce sont des noms ou des prenoms anglais ».
rem
rem  POURQUOI ON CHERCHE DU COTE DE L'ORTHOGRAPHE : le moteur en
rem  service, Qwen3-TTS, recoit UNE SEULE langue pour toute la
rem  phrase et refuse de vrais phonemes -- verifie le 16/10/2026.
rem  Le seul levier est donc CE QU'ON ECRIT.
rem
rem  CE QUE TU ENTENDS, pour chaque nom :
rem     1_CIBLE_anglaise  le nom dit par une VRAIE voix anglaise :
rem                       c'est le repere, voila le son a atteindre
rem     2_AUJOURD_HUI    le nom tel que le livre l'ecrit, avec SA
rem                       voix du casting : ce que tu entends
rem     3_B1, 4_B2...    des graphies candidates, a departager
rem
rem  RIEN N'EST MODIFIE : ni la base, ni les voix, ni le lecteur.
rem  Le banc n'ecrit que dans son dossier d'ecoute.
rem
rem  Le moteur Qwen s'allume SUR LA CARTE s'il ne tourne pas deja
rem  -- fenetre separee, a NE PAS FERMER pendant le banc. C'est le
rem  meme moteur que celui de la lecture.
rem ============================================================

set BANC=test_voix\ecouter_prenoms_22_11_63.py
set MOTEUR=qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat
set SUIVI=test_voix\_dernier_lot_prenoms.txt

if not exist "%BANC%" goto :pas_de_banc
if not exist "qwen_tts_service\voix\references.csv" goto :pas_de_voix

echo ======================================================
echo   NIMM ePub - LES PRENOMS ANGLAIS DE 22/11/63
echo ======================================================
echo.
echo   Pour chaque nom, tu entendras trois choses :
echo.
echo     1_CIBLE_anglaise   une VRAIE voix anglaise : le repere
echo     2_AUJOURD_HUI      ce que tu entends aujourd'hui
echo     3_B1, 4_B2...      des graphies candidates
echo.
echo   Compte quelques minutes : chaque phrase est fabriquee
echo   pour de vrai. Rien n'est facture, aucun acces payant.
echo   Le dossier s'ouvre tout seul a la fin.
echo.

rem -- Le moteur Qwen : on l'allume seulement s'il ne repond pas.
curl -s -o NUL --max-time 3 http://127.0.0.1:8086/sante >nul 2>&1
if not errorlevel 1 (
    echo   Moteur Qwen : deja en marche.
    goto :banc
)
if not exist "%MOTEUR%" goto :pas_de_moteur
echo   Moteur Qwen : allumage SUR LA CARTE - sa fenetre s'ouvre...
start "NIMM ePub - appareil de voix Qwen3-TTS" /D "%~dp0qwentts_service" cmd /k "%~dp0qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat"

:banc
python "%BANC%" --attente 180
set CODE=%ERRORLEVEL%

echo.
if not "%CODE%"=="0" goto :avec_erreur

echo ======================================================
echo   C'EST PRET
echo ======================================================
echo.
if not exist "%SUIVI%" goto :sans_suivi
set /p LOT=<"%SUIVI%"
start "" explorer "%LOT%"
timeout /t 2 /nobreak >nul
if exist "%LOT%\LISEZ-MOI.txt" start "" notepad.exe "%LOT%\LISEZ-MOI.txt"
echo.
echo   Ecoute, pour chaque nom, dans cet ordre :
echo     1_CIBLE_anglaise, puis 2_AUJOURD_HUI, puis les B.
echo.
echo   Puis dis a Cline, pour chaque nom : « ca me va »,
echo   « c'est B2 », ou « aucune ».
echo.
pause
exit /b 0

:sans_suivi
echo   Le dossier du lot n'a pas ete note : regarde dans test_voix\
pause
exit /b 0

:avec_erreur
echo.
echo   LE BANC S'EST ARRETE, code %CODE%.
echo.
echo   Si le moteur n'a pas repondu : ferme tout, relance ce
echo   bouton, et attends que la fenetre du moteur dise qu'il
echo   est pret avant de continuer.
echo.
pause
exit /b %CODE%

:pas_de_banc
echo   Fichier manquant : %BANC%
pause
exit /b 1

:pas_de_voix
echo   Fichier manquant : qwen_tts_service\voix\references.csv
echo   Les voix du moteur n'ont pas ete trouvees.
pause
exit /b 1

:pas_de_moteur
echo   Fichier manquant : %MOTEUR%
echo   Le moteur Qwen n'est pas installe sur ce PC.
pause
exit /b 1
