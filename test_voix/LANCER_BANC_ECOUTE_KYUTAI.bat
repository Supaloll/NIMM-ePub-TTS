@echo off
chcp 65001 >nul
title NIMM ePub - banc d'ecoute Kyutai (comparer avec NeuTTS)
cd /d "%~dp0"

rem ============================================================
rem  BANC D'ECOUTE KYUTAI
rem
rem  Meme banc que pour NeuTTS, sur le meme chapitre et les MEMES
rem  voix : les deux moteurs partagent les memes extraits, donc les
rem  memes identifiants de voix. C'est la seule comparaison honnete
rem  entre deux moteurs.
rem
rem  Le moteur Kyutai doit etre allume (DEMARRER_KYUTAI.bat), et
rem  NEUTTS doit etre ETEINT : les deux ne tiennent pas ensemble
rem  sur la carte graphique.
rem
rem  Resultat : un dossier ecoute_kyutai_<date> (WAV numerotes,
rem  index.txt, ECOUTER_LE_LOT.cmd).
rem
rem  Double-clic sur ce fichier suffit : rien a taper.
rem ============================================================

rem -- Le moteur Kyutai repond-il ? (0,5 s de test, aucune erreur affichee)
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:8082/sante' -TimeoutSec 4 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo.
  echo  Le moteur Kyutai n'est pas allume.
  echo  Double-clique d'abord sur  kyutai_service\DEMARRER_KYUTAI.bat
  echo  -- et ferme NeuTTS s'il tourne : les deux ne tiennent pas
  echo  ensemble sur la carte graphique --
  echo  puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

echo.
echo ==========================================================
echo   BANC D'ECOUTE KYUTAI  (memes phrases, memes voix)
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

python -u "_banc_ecoute_neutts.py" --moteur kyutai --volet voix --livre %LIVRE% --chapitre %CHAPITRE%

echo.
echo ==========================================================
echo  C'EST FINI.
echo  Un dossier  ecoute_kyutai_...  vient d'apparaitre dans
echo  test_voix : ouvre-le et double-clique sur
echo  ECOUTER_LE_LOT.cmd.
echo  Pour comparer : meme chose dans  ecoute_neutts_...  (le lot
echo  NeuTTS fabrique avec LANCER_BANC_ECOUTE_NEUTTS.bat).
echo ==========================================================
echo.
pause
