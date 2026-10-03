@echo off
chcp 65001 >nul
title NIMM ePub - Pocket TTS : le modele francais LEGER est-il plus rapide ?
cd /d "%~dp0.."

rem ============================================================
rem  POCKET TTS FRANCAIS : 24 COUCHES CONTRE 6 COUCHES
rem  (30/09/2026, demande de Laurent : la lecture s'arrete
rem  completement [...] un modele encore plus leger si ca existe)
rem
rem  A quoi ca sert : a savoir COMBIEN DE FOIS le moteur fait
rem  l'audio plus vite que la lecture. C'est ce chiffre qui decide
rem  des blancs : un moteur a x1,04 (le Qwen d'aujourd'hui) n'a
rem  aucune marge, un moteur a x3 en a beaucoup.
rem
rem  Ce qui va se passer : le banc fait dire les MEMES phrases
rem  reelles de livre a deux modeles francais, dans les memes
rem  conditions que le service (4 coeurs, temperature 0,3), et pose
rem  les WAV cote a cote pour ton oreille :
rem     A = le modele d'aujourd'hui (24 couches, 672 Mo)
rem     B = le modele LEGER (6 couches, 219 Mo)
rem
rem  ATTENTION, UNE SEULE FOIS : le modele B se telecharge au
rem  premier passage (219 Mo, dans le cache Hugging Face ; rien
rem  n'est installe ailleurs). Compte 3 a 6 minutes en tout.
rem  Le processeur travaille a plein -- exactement les memes calculs
rem  que pendant une lecture, juste groupes. Rien n'est modifie :
rem  ni la base, ni les voix, ni le service.
rem
rem  Le moteur Pocket doit etre ETEINT : si le service repond sur
rem  le port 8085, le banc refuse de partir.
rem ============================================================

echo.
echo   ==========================================================
echo    POCKET TTS EN FRANCAIS : 24 COUCHES CONTRE 6 COUCHES
echo   ==========================================================
echo.
echo   A = le modele d'aujourd'hui (24 couches, 672 Mo)
echo   B = le modele LEGER          (6 couches, 219 Mo)
echo.
echo   Reglages identiques a ceux du service : 4 coeurs,
echo   temperature 0,3, max_tokens 200. Memes phrases de livre.
echo.

if not exist "pocket_tts_service\.venv\Scripts\python.exe" (
    echo  Le moteur Pocket TTS n'est pas installe sur ce PC.
    echo  Voir : pocket_tts_service\LIRE_MOI.md
    echo.
    pause
    exit /b 1
)

if not exist "pocket_tts_service\configs\french_leger.yaml" (
    echo  La configuration du modele LEGER est absente :
    echo      pocket_tts_service\configs\french_leger.yaml
    echo  Sans elle, le banc ne peut pas charger le modele 6 couches.
    echo.
    pause
    exit /b 1
)

if not exist "pocket_tts_service\voix\Femme001_reference.wav" (
    echo  La voix d'essai est absente :
    echo      pocket_tts_service\voix\Femme001_reference.wav
    echo.
    pause
    exit /b 1
)

echo  Verifie que le moteur Pocket n'est pas deja allume...
curl -s -o NUL --max-time 3 http://127.0.0.1:8085/sante
if not errorlevel 1 (
    echo.
    echo  Le moteur Pocket REPOND deja sur le port 8085.
    echo  Ferme sa fenetre, puis relance ce banc :
    echo  sinon les deux se partageraient les coeurs et les chiffres
    echo  ne voudraient rien dire.
    echo.
    pause
    exit /b 1
)

echo  Le moteur est eteint : parfait.
echo.
echo  Premiere fois seulement : telechargement du modele leger (219 Mo).
echo  Les passages suivants partiront du cache (donc plus rapides).
echo.
echo  LA MESURE COMMENCE. Ne ferme pas cette fenetre avant la fin.
echo.

"pocket_tts_service\.venv\Scripts\python.exe" "test_voix\_mesurer_debit_pocket.py" %*
if errorlevel 1 (
    echo.
    echo  La mesure s'est arretee : lis le message ci-dessus.
    echo.
    pause
    exit /b 1
)

echo.
echo  ==========================================================
echo   C'EST FINI : les WAV a ecouter sont dans le dossier
echo   date ci-dessus (A = 24 couches, B = 6 couches, meme phrase).
echo   Le rapport complet est le fichier RAPPORT.txt de ce dossier.
echo  ==========================================================
echo.
echo  Ouvre ce dossier pour ecouter ? (il va s'ouvrir)
echo.

for /f "delims=" %%i in ('dir /b /ad /o-d "test_voix\mesure_pocket_*" 2^>nul') do (
    start "" "test_voix\%%i"
    goto :ouvert
)
:ouvert

echo  Ecoute A puis B, phrase par phrase (01, 02, 03) :
echo  c'est ton oreille qui tranche, pas les chiffres.
echo.
pause
