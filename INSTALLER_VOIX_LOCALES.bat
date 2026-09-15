@echo off
chcp 65001 >nul
title NIMM ePub - telechargement des voix locales
cd /d "%~dp0"
setlocal enabledelayedexpansion

rem ============================================================
rem  Telecharge les fichiers de voix locales (Kokoro + Piper) et
rem  les pose a la racine du projet, a cote de main.py.
rem  A lancer UNE SEULE FOIS, par double-clic. Tout est consigne
rem  dans installation_voix_locales.log. Environ 550 Mo.
rem  Relancable sans risque : ce qui est deja la n'est pas
rem  re-telecharge, et un telechargement interrompu REPREND ou il
rem  s'est arrete.
rem  NB : pas d'accents ni de parentheses dans les messages -- la
rem  console Windows les affiche mal, et les parentheses coupent
rem  la lecture des blocs par Windows.
rem ============================================================

set JOURNAL=installation_voix_locales.log
set ECHECS=0
echo Telechargement des voix locales NIMM ePub > "%JOURNAL%"
echo Debut : %DATE% %TIME% >> "%JOURNAL%"

echo.
echo  ==========================================================
echo   NIMM ePub - voix locales Kokoro et Piper
echo  ==========================================================
echo.
echo   Ce programme recupere les fichiers de voix locales et les
echo   pose a la racine du projet, a cote de main.py :
echo.
echo     Kokoro : le modele + sa banque de voix   environ 350 Mo
echo     Piper  : trois voix francaises           environ 190 Mo
echo.
echo   Total : environ 550 Mo. Compte de quelques minutes a un
echo   quart d'heure selon la connexion.
echo.
echo   Le lecteur fonctionne meme sans ces fichiers : seules les
echo   voix Kokoro et Piper sont alors indisponibles.
echo.

where curl.exe >nul 2>&1
if errorlevel 1 goto pas_de_curl

call :obtenir "kokoro-v1.0.onnx"             "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"              300000000
call :obtenir "voices-v1.0.bin"              "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"               20000000
call :obtenir "fr_FR-siwis-medium.onnx"      "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx"      50000000
call :obtenir "fr_FR-siwis-medium.onnx.json" "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json" 1000
call :obtenir "fr_FR-upmc-medium.onnx"       "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/upmc/medium/fr_FR-upmc-medium.onnx"        50000000
call :obtenir "fr_FR-upmc-medium.onnx.json"  "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/upmc/medium/fr_FR-upmc-medium.onnx.json"  1000
call :obtenir "fr_FR-tom-medium.onnx"        "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/tom/medium/fr_FR-tom-medium.onnx"          50000000
call :obtenir "fr_FR-tom-medium.onnx.json"   "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/tom/medium/fr_FR-tom-medium.onnx.json"    1000

echo.
if not "!ECHECS!"=="0" goto bilan_echecs

echo  ==========================================================
echo   TERMINE - les voix locales sont en place.
echo  ==========================================================
echo.
echo   Si NIMM ePub est ouvert, ferme sa fenetre puis relance
echo   START.bat : les voix Kokoro et Piper apparaitront.
echo.
echo   Pour verifier que le lecteur voit ces voix, relance START.bat :
echo   elles apparaissent dans le menu des voix du narrateur et dans
echo   la fenetre du casting, sous les noms Kokoro et Piper.
echo.
echo   Rappel : le fichier de voix de Kokoro fourni ici contient
echo   54 voix. Des voix francaises supplementaires peuvent etre
echo   copiees depuis un autre poste, sous le meme nom de fichier.
echo.
pause
exit /b 0

:bilan_echecs
echo  ==========================================================
echo   TERMINE AVEC !ECHECS! PROBLEME(S)
echo  ==========================================================
echo.
echo   Un ou plusieurs fichiers n'ont pas pu etre telecharges.
echo   Relance simplement ce fichier : le telechargement reprend
echo   la ou il s'est arrete.
echo.
echo   Si un fichier reste en echec, supprime-le puis relance :
echo   une reprise sur un fichier abime peut rester abimee.
echo.
echo   Detail de ce qui s'est passe : %JOURNAL%
echo.
pause
exit /b 1

:pas_de_curl
echo  curl.exe est introuvable sur cette machine.
echo  Il est fourni avec Windows 10 et 11 : lance Windows Update,
echo  puis relance ce fichier.
echo.
pause
exit /b 1

rem ------------------------------------------------------------
rem  :obtenir <fichier> <adresse> <taille mini en octets>
rem  Ne telecharge que si le fichier manque ou est incomplet.
rem ------------------------------------------------------------
:obtenir
set FICHIER=%~1
set URL=%~2
set MINI=%~3

if not exist "%FICHIER%" goto telecharger
for %%A in ("%FICHIER%") do set TAILLE=%%~zA
if !TAILLE! GEQ %MINI% goto deja_la
echo    %FICHIER% : incomplet, reprise du telechargement...
goto telecharger

:deja_la
echo    %FICHIER% : deja present
echo %FICHIER% : deja present >> "%JOURNAL%"
goto :eof

:telecharger
echo    %FICHIER% : telechargement...
echo    Cela peut rester immobile plusieurs minutes :
echo    c'est normal pour les gros fichiers.
curl.exe -L -C - --retry 20 --retry-all-errors --retry-delay 3 -o "%FICHIER%" "%URL%" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto fichier_rate
for %%A in ("%FICHIER%") do set TAILLE=%%~zA
if !TAILLE! LSS %MINI% goto fichier_rate
echo    %FICHIER% : OK
echo %FICHIER% : OK, !TAILLE! octets >> "%JOURNAL%"
goto :eof

:fichier_rate
echo    %FICHIER% : ECHEC
echo %FICHIER% : ECHEC >> "%JOURNAL%"
set /a ECHECS+=1
goto :eof
