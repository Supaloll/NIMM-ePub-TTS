@echo off
chcp 65001 >nul
title NIMM ePub - UN SEUL fichier a ecouter : un chapitre lu par Pocket (leger)
cd /d "%~dp0.."

rem ============================================================
rem  UN CHAPITRE ENTIER, EN UN SEUL FICHIER  (30/09/2026)
rem
rem  Pourquoi ce banc existe : Laurent a du ecouter 36 prises
rem  une par une et il a dit, tres justement : « je ne suis pas
rem  la pour deboguer un moteur ». Ici, la MACHINE fait le tri.
rem
rem  Ce que fait ce lanceur :
rem    1. il prend un VRAI chapitre (Monte-Cristo, tome 4,
rem       chapitre « Le telegraphe »), lu par le meme lecteur
rem       d'EPUB que l'application, nettoye par le meme code ;
rem    2. il fait lire chaque phrase DEUX FOIS par le moteur
rem       Pocket LEGER (6 couches) a 0,70 ;
rem    3. il TRIE par machine : silences trop longs MESURES, et
rem       transcription (Whisper) pour reperer les mots en trop
rem       ou manquants ;
rem    4. il RECOUD les silences trop longs (0,45 s maximum) ;
rem    5. il assemble les 12 phrases avec les pauses du lecteur
rem       (300 ms entre phrases, 800 ms entre paragraphes).
rem
rem  Tu n'as QU'UN SEUL fichier a ecouter, une fois. Compte 2 a
rem  4 minutes. Rien n'est modifie : ni la base, ni les voix, ni
rem  le service, ni le lecteur. Le moteur Pocket doit etre ETEINT.
rem ============================================================

echo.
echo   ==========================================================
echo    UN CHAPITRE ENTIER, EN UN SEUL FICHIER
echo   ==========================================================
echo.
echo   Un vrai chapitre, lu par le Pocket LEGER (6 couches) a 0,70.
echo   Chaque phrase est lue DEUX fois, puis la machine garde la
echo   meilleure (silences mesures + transcription) ; les silences
echo   trop longs sont recousus, et les pauses du lecteur sont
echo   remises (300 ms / 800 ms).
echo.
echo   A la fin, tu auras UN SEUL fichier a ecouter, une fois.
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo  Python n'est pas trouve dans le PATH de cette fenetre.
    echo.
    pause
    exit /b 1
)

if not exist "pocket_tts_service\.venv\Scripts\python.exe" (
    echo  Le moteur Pocket TTS n'est pas installe sur ce PC.
    echo  Voir : pocket_tts_service\LIRE_MOI.md
    echo.
    pause
    exit /b 1
)

if not exist "test_voix\_banc_chapitre_pocket.py" (
    echo  Le banc est absent : test_voix\_banc_chapitre_pocket.py
    echo.
    pause
    exit /b 1
)

echo  Verifie que le moteur Pocket n'est pas allume...
curl -s -o NUL --max-time 3 http://127.0.0.1:8085/sante
if not errorlevel 1 (
    echo.
    echo  Le moteur Pocket REPOND deja sur le port 8085.
    echo  Ferme sa fenetre, puis relance : sinon les deux se
    echo  partageraient les coeurs et la mesure serait faussee.
    echo.
    pause
    exit /b 1
)

echo  Le moteur est eteint : parfait.
echo.
echo  TRAVAIL EN COURS -- ne ferme pas cette fenetre.
echo.

python "test_voix\_banc_chapitre_pocket.py" %*
if errorlevel 1 (
    echo.
    echo  Le banc s'est arrete : lis le message ci-dessus.
    echo.
    pause
    exit /b 1
)

echo.
echo  ==========================================================
echo   C'EST FINI. Le fichier a ecouter s'appelle
echo   CHAPITRE_livre15_chap4_pocket_leger_T070.wav
echo   et il est dans le dossier du banc.
echo.
echo   Ecoute-le UNE FOIS, en entier, comme une vraie lecture.
echo   La question est simple : est-ce que tu pourrais lire un
echo   livre comme ca ?
echo  ==========================================================
echo.

if exist "test_voix\_dernier_chapitre.txt" (
    set /p FICHIER_CHAPITRE=<"test_voix\_dernier_chapitre.txt"
) else (
    set FICHIER_CHAPITRE=
)

if not "%FICHIER_CHAPITRE%"=="" (
    echo  Fichier :
    echo    %FICHIER_CHAPITRE%
    echo.
    echo  Il va s'ouvrir pour que tu puisses l'ecouter.
    start "" "%FICHIER_CHAPITRE%"
) else (
    echo  Je n'ai pas retrouve le fichier : ouvre-le a la main,
    echo  il est dans test_voix\banc_chapitre_pocket_...
)

echo.
echo  Le rapport (ce que la machine a retenu, phrase par phrase)
echo  est le fichier RAPPORT.txt du meme dossier.
echo.
pause
