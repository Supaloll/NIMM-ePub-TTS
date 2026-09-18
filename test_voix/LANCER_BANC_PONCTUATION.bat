@echo off
chcp 65001 >nul
title NIMM ePub - banc d'ecoute : la ponctuation du point d'exclamation
cd /d "%~dp0"

rem ============================================================
rem  BANC D'ECOUTE : QUELLE PONCTUATION REMPLACER LE « ! » ?
rem  (+ les incises de dialogue : gardees ou retirees)
rem
rem  Le « ! » n'est plus envoye au moteur (il faisait monter la voix :
rem  « Oh ! » sortait en « OOOOOOoooooh »). Il est remplace par un POINT
rem  pour l'instant. Ce banc compare QUATRE choix sur les MEMES phrases
rem  reelles de ton livre, pour choisir a l'oreille :
rem     P1 le point / P2 la virgule / P3 la suspension / P4 rien
rem
rem  Meme lot, deuxieme question : les INCISES (« , dit-il, ») —
rem     I1 gardee / I2 retiree (une voix par personnage dit deja qui parle).
rem
rem  Resultat : un dossier ecoute_ponctuation_<date> avec les WAV numerotes,
rem  un index.txt (ce qu'on te demande) et ECOUTER_LE_LOT.cmd.
rem
rem  Le moteur Kyutai doit etre allume. Double-clic sur ce fichier suffit.
rem ============================================================

rem -- Le moteur Kyutai repond-il ? (test de 4 s, aucune erreur affichee)
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
echo   BANC D'ECOUTE : LA PONCTUATION DU « ! » (et les incises)
echo ==========================================================
echo.
echo  Appuie sur Entree pour garder la valeur entre crochets.
echo.
set LIVRE=16
set PHRASES=6
set /p LIVRE=Numero du livre ou prendre les phrases [%LIVRE%] :
if "%LIVRE%"=="" set LIVRE=16
set /p PHRASES=Nombre de phrases par serie [%PHRASES%] :
if "%PHRASES%"=="" set PHRASES=6

echo.
echo  Fabrication du lot (livre %LIVRE%, %PHRASES% phrases par serie)...
echo.

python -u "_banc_ponctuation_exclamation.py" --livre %LIVRE% --phrases %PHRASES%

echo.
echo ==========================================================
echo  C'EST FINI.
echo.
echo  Pour ecouter : ouvre le dossier  ecoute_ponctuation_...
echo  (le dernier en date) et double-clique sur  ECOUTER_LE_LOT.cmd
echo.
echo  Tu y trouveras ce qu'on te demande, phrase par phrase.
echo ==========================================================
echo.
pause
