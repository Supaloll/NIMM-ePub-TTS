@echo off
chcp 65001 >nul
title NIMM ePub - banc d'ecoute NeuTTS (ou ca derape ?)
cd /d "%~dp0"

rem ============================================================
rem  BANC D'ECOUTE NEUTTS
rem
rem  Fabrique un petit LOT D'ECOUTE pour comprendre ou la voix
rem  NeuTTS derape : de vraies phrases d'un de tes livres, puis
rem  la MEME phrase avec et sans les signes de dialogue
rem  (guillemets et tirets), puis des phrases courtes, puis une
rem  phrase longue lue d'un bloc et coupee en deux.
rem
rem  Le moteur NeuTTS doit etre allume (DEMARRER_NEUTTS.bat) :
rem  c'est lui qui fabrique l'audio. Compte 4 a 5 minutes.
rem
rem  Resultat : un dossier ecoute_neutts_<date> contenant les WAV
rem  numerotes, un index.txt (quoi ecouter, dans quel ordre) et un
rem  lanceur ECOUTER_LE_LOT.cmd (double-clic).
rem
rem  Double-clic sur ce fichier suffit : rien a taper.
rem ============================================================

rem -- Le moteur NeuTTS repond-il ? (0,5 s de test, aucune erreur affichee)
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:8084/sante' -TimeoutSec 4 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo.
  echo  Le moteur NeuTTS n'est pas allume.
  echo  Double-clique d'abord sur  neutts_service\DEMARRER_NEUTTS.bat
  echo  puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

echo.
echo ==========================================================
echo   BANC D'ECOUTE NEUTTS
echo ==========================================================
echo.
echo  Appuie sur Entree pour garder la valeur entre crochets.
echo.
set LIVRE=34
set CHAPITRE=6
set /p LIVRE=Numero du livre a ecouter [%LIVRE%] :
if "%LIVRE%"=="" set LIVRE=34
set /p CHAPITRE=Numero du chapitre [%CHAPITRE%] :
if "%CHAPITRE%"=="" set CHAPITRE=6

echo.
echo  Fabrication du lot (livre %LIVRE%, chapitre %CHAPITRE%)...
echo.

python -u "_banc_ecoute_neutts.py" --livre %LIVRE% --chapitre %CHAPITRE%

echo.
echo ==========================================================
echo  C'EST FINI.
echo  Un dossier  ecoute_neutts_...  vient d'apparaitre dans
echo  test_voix : ouvre-le et double-clique sur
echo  ECOUTER_LE_LOT.cmd (l'index dit dans quel ordre ecouter).
echo  Si aucun dossier n'est apparu, il y a eu une erreur :
echo  relis ce qui est affiche juste au-dessus.
echo ==========================================================
echo.
pause
