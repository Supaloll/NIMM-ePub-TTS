@echo off
chcp 65001 >nul
title NIMM ePub - Pocket TTS : quelle temperature supprime les trous ?
cd /d "%~dp0.."

rem ============================================================
rem  POCKET TTS : LA VOIX DE A, SANS LES TROUS DE A ?
rem  (30/09/2026 -- ecoute de Laurent : « Le A a un probleme de
rem  coupure/collage/raccord de phrases : soit il fait une pause
rem  au moment de la coupure, soit il repete 2 fois le meme mot
rem  [...] Je dirais A, parce que les voix sont quand meme
rem  meilleures, mais il faut reussir a coller les morceaux. »)
rem
rem  CE QU'ON SAIT DEJA (mesure de ses 6 WAV, le meme jour) :
rem    A (24 couches) : 18 silences internes, dont un de 2,02 s ;
rem    B (6 couches)  : 7 silences internes, aucun au-dela de 0,60 s.
rem  Donc le defaut vient du MODELE 24 couches, pas du montage.
rem
rem  CE QUE FAIT CE BANC : il fait dire les 3 memes phrases aux deux
rem  modeles, avec PLUSIEURS temperatures d'echantillonnage
rem  (0,30 = aujourd'hui, puis 0,50, 0,70, 0,90) et PLUSIEURS
rem  tirages par phrase, puis il MESURE chaque prise : nombre de
rem  silences internes, silence le plus long, duree.
rem  But : retrouver une voix de A qui se tient comme la voix de B.
rem
rem  Ce qui va se passer : le processeur travaille a plein pendant
rem  8 a 12 minutes. Rien n'est modifie : ni la base, ni les voix,
rem  ni le service, ni le lecteur.
rem
rem  Le moteur Pocket doit etre ETEINT : si le service repond sur le
rem  port 8085, le banc refuse de partir.
rem ============================================================

echo.
echo   ==========================================================
echo    POCKET TTS : LA VOIX DE A, SANS LES TROUS DE A ?
echo   ==========================================================
echo.
echo   Deux modeles francais :  A = 24 couches (vos voix preferees)
echo                            B = 6 couches  (les raccords propres)
echo   Quatre temperatures : 0,30 / 0,50 / 0,70 / 0,90
echo   Trois tirages par phrase (le moteur ne redonne jamais deux
echo   fois la meme prise).
echo.
echo   Chaque prise est MESUREE : nombre de silences internes,
echo   silence le plus long, duree. Le rapport dit tout a la fin.
echo.

if not exist "pocket_tts_service\.venv\Scripts\python.exe" (
    echo  Le moteur Pocket TTS n'est pas installe sur ce PC.
    echo  Voir : pocket_tts_service\LIRE_MOI.md
    echo.
    pause
    exit /b 1
)

if not exist "pocket_tts_service\configs\french_leger.yaml" (
    echo  Configuration du modele LEGER absente :
    echo      pocket_tts_service\configs\french_leger.yaml
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
    echo  Ferme sa fenetre, puis relance ce banc : sinon les deux se
    echo  partageraient les coeurs et les chiffres ne voudraient rien dire.
    echo.
    pause
    exit /b 1
)

echo  Le moteur est eteint : parfait.
echo.
echo  LE BANC COMMENCE. Ne ferme pas cette fenetre avant la fin :
echo  sur cette machine, compte 8 a 12 minutes.
echo.

"pocket_tts_service\.venv\Scripts\python.exe" "test_voix\_banc_reglages_pocket.py" %*
if errorlevel 1 (
    echo.
    echo  Le banc s'est arrete : lis le message ci-dessus.
    echo.
    pause
    exit /b 1
)

echo.
echo  ==========================================================
echo   C'EST FINI. Les WAV sont ranges un dossier par modele,
echo   et dedans un dossier par temperature (T030, T050, T070,
echo   T090), avec 3 tirages par phrase.
echo.
echo   La bonne facon d'ecouter : prendre UNE phrase, et passer
echo   les temperatures dans l'ordre, plusieurs tirages.
echo   Deux questions : les trous ont-ils disparu ? et la voix
echo   est-elle restee celle de A ?
echo  ==========================================================
echo.

rem Le dossier est retrouve par le REPERE ecrit par le banc (30/09/2026) :
rem la premiere version devinait le nom du dossier et n'ouvrait rien.
if exist "test_voix\_dernier_banc.txt" (
    set /p DOSSIER_BANC=<"test_voix\_dernier_banc.txt"
) else (
    set DOSSIER_BANC=
)

if not "%DOSSIER_BANC%"=="" (
    echo  Dossier de ce banc :
    echo    %DOSSIER_BANC%
    echo.
    echo  Il va s'ouvrir maintenant.
    start "" "%DOSSIER_BANC%"
) else (
    echo  Je n'ai pas retrouve le dossier du banc : ouvre-le a la main,
    echo  il s'appelle "banc_reglages_pocket_..." et il est dans test_voix.
)

echo.
echo  Le rapport complet est le fichier RAPPORT.txt de ce dossier.
echo.
pause
