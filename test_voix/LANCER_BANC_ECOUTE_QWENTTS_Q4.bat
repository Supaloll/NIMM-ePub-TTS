@echo off
chcp 65001 >nul
title NIMM ePub - banc d'ecoute Qwen : Q8_0 contre Q4_K_M
cd /d "%~dp0.."

rem ============================================================
rem  BANC D'ECOUTE QWEN -- Q8_0 (A, aujourd'hui) contre Q4_K_M (B)
rem  (29/09/2026, demande de Laurent : « il faut tester ce que ca
rem  donne a l'oreille »)
rem
rem  A quoi ca sert : le modele Q8_0 fait 947 Mo et son codec 278 Mo ;
rem  les Q4_K_M font 629 Mo et 255 Mo. Moins de bits = plus rapide,
rem  mais la VOIX peut y perdre -- et ca, seule ton oreille le dit.
rem
rem  Ce que tu vas voir : pour chaque voix et chaque phrase, DEUX WAV
rem  cote a cote dans  test_voix\sortie_banc_qwentts_q4\  :
rem     ...__A_Q8_0.wav    = l'ANCIEN modele, garde sur le disque
rem     ...__B_Q4_K_M.wav  = celui EN SERVICE depuis le 29/09/2026
rem  ...plus un RECAP.txt avec les chiffres (debit des deux).
rem
rem  A quoi ca sert aujourd'hui : a RE-ECOUTER les deux quand tu veux,
rem  ou a refaire l'essai sur d'autres voix (--voix a,b). La bascule est
rem  faite : le service charge les Q4_K_M.
rem
rem  Compte deux a quatre minutes : le processeur travaille a plein,
rem  le ventilateur peut se faire entendre -- c'est normal.
rem
rem  Rien n'est modifie : le service continue d'utiliser les Q8_0. Le
rem  moteur doit etre ETEINT pour que la mesure soit juste.
rem ============================================================

echo.
echo   ==========================================================
echo    BANC D'ECOUTE QWEN -- Q8_0 (A) contre Q4_K_M (B)
echo   ==========================================================
echo.

if not exist "qwentts_service\.venv\Scripts\python.exe" (
    echo  Le moteur Qwen n'est pas installe sur ce PC.
    echo  Voir : qwentts_service\LIRE_MOI.md
    echo.
    pause
    exit /b 1
)

if not exist "qwentts_service\models\qwen-talker-0.6b-base-Q4_K_M.gguf" (
    echo  Il manque les MODELES du candidat Q4_K_M dans
    echo  qwentts_service\models\ :
    echo    qwen-talker-0.6b-base-Q4_K_M.gguf   ^(629 Mo^)
    echo    qwen-tokenizer-12hz-Q4_K_M.gguf     ^(255 Mo^)
    echo.
    echo  Ils viennent du depot  Serveurperso/Qwen3-TTS-GGUF  ^(Hugging Face^).
    echo  Les Q8_0 actuels ne sont PAS touches : ce sont des fichiers en plus.
    echo.
    pause
    exit /b 1
)

echo  Verifie que le moteur n'est pas allume...
curl -s -o NUL --max-time 3 http://127.0.0.1:8086/sante
if not errorlevel 1 (
    echo.
    echo  Le moteur Qwen REPOND deja sur le port 8086.
    echo  Ferme sa fenetre, puis relance ce banc : sinon les deux se
    echo  partageraient les coeurs et les chiffres ne voudraient rien dire.
    echo.
    pause
    exit /b 1
)

echo  Le moteur est eteint : c'est bon. C'est parti.
echo.

"qwentts_service\.venv\Scripts\python.exe" "test_voix\_banc_ecoute_qwentts_q4.py" %*

echo.
echo ----------------------------------------------------------
echo  Rien n'a ete modifie dans le projet.
echo  A ECOUTER : test_voix\sortie_banc_qwentts_q4\
echo    ...__A_Q8_0.wav    = l'ancien modele (Q8_0, garde comme repli)
echo    ...__B_Q4_K_M.wav  = celui en service depuis le 29/09/2026
echo  Ecoute les deux d'une MEME voix, l'un apres l'autre, et dis
echo  ce qui change : timbre, clarte, accrocs, respiration, prosodie.
echo  Les chiffres sont dans RECAP.txt, dans le meme dossier.
echo ----------------------------------------------------------
echo.
echo  J'ouvre le dossier des WAV pour que tu n'aies rien a chercher.
start "" "%~dp0sortie_banc_qwentts_q4"
pause >nul
