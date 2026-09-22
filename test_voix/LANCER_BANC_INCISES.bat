@echo off
chcp 65001 >nul
title NIMM ePub - banc d'ecoute : les incises (muettes, ou lues par le narrateur)
cd /d "%~dp0"

rem ============================================================
rem  BANC D'ECOUTE : LES INCISES DE PAROLE
rem
rem  Question posee a Laurent le 22/09/2026 : l'incise de parole
rem  (« , dit-il, ») doit-elle etre MUETTE, ou DITE PAR LE NARRATEUR ?
rem  Le reglage existe maintenant, livre par livre, avec le bouton
rem  « Incises » du lecteur. Ce banc sert a JUGER A L'OREILLE :
rem     - est-ce plus agreable ?
rem     - entend-on un petit silence a la jonction ?
rem     - la vitesse du narrateur sur le morceau d'incise choque-t-elle ?
rem
rem  Resultat : un dossier ecoute_incises_<date> avec les WAV numerotes,
rem  un index.txt (ce qu'on te demande) et ECOUTER_LE_LOT.cmd.
rem
rem  Il faut le SERVEUR NIMM (START.bat) et le moteur Kyutai, parce que
rem  l'extrait est fabrique par le VRAI chemin du lecteur.
rem ============================================================

echo.
echo  Verification de ce qui doit etre allume...
echo.

curl -s -o NUL --max-time 3 http://127.0.0.1:8081/api/users >nul 2>&1
if errorlevel 1 (
  echo  Le SERVEUR NIMM n'est pas allume ^(port 8081^).
  echo  Double-clique d'abord sur  START.bat  ^(racine du projet^),
  echo  puis relance ce fichier.
  echo.
  pause
  exit /b 1
)
echo    serveur NIMM : allume  OK

curl -s -o NUL --max-time 3 http://127.0.0.1:8082/sante >nul 2>&1
if errorlevel 1 (
  echo.
  echo  Le moteur KYUTAI n'est pas allume ^(port 8082^).
  echo  C'est lui qui fait la voix du NARRATEUR du livre : sans lui, la
  echo  version « au narrateur » ne peut pas etre fabriquee.
  echo  Double-clique sur  kyutai_service\DEMARRER_KYUTAI.bat  ^(et ferme
  echo  NeuTTS s'il tourne : les deux ne tiennent pas sur la carte graphique^),
  echo  puis relance ce fichier.
  echo.
  pause
  exit /b 1
)
echo    moteur Kyutai : allume  OK

echo.
echo ==========================================================
echo   BANC D'ECOUTE : LES INCISES DE PAROLE
echo ==========================================================
echo.
echo  Appuie sur Entree pour garder la valeur entre crochets.
echo.
set LIVRE=28
set CHAPITRES=10 11
set PHRASES=4
set /p LIVRE=Numero du livre [%LIVRE%] :
if "%LIVRE%"=="" set LIVRE=28
echo    (les chapitres sont ceux que tu as ecoutes : 10 et 11)
set /p PHRASES=Nombre de phrases par serie [%PHRASES%] :
if "%PHRASES%"=="" set PHRASES=4

echo.
echo  Fabrication du lot (livre %LIVRE%, chapitres %CHAPITRES%)...
echo  Ca peut prendre une minute : chaque morceau est vraiment synthetise.
echo.

python -u "_banc_incises.py" --livre %LIVRE% --chapitres %CHAPITRES% --phrases %PHRASES%

echo.
echo ==========================================================
echo  C'EST FINI.
echo.
echo  Pour ecouter : ouvre le dossier  ecoute_incises_...
echo  (le dernier en date) et double-clique sur  ECOUTER_LE_LOT.cmd
echo.
echo  Tu y trouveras ce qu'on te demande, fichier par fichier.
echo ==========================================================
echo.
pause
