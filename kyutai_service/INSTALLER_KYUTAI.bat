@echo off
chcp 65001 >nul
title NIMM ePub - installation du moteur de voix Kyutai
cd /d "%~dp0"

rem ============================================================
rem  Installation du moteur Kyutai TTS 1.6B pour NIMM ePub.
rem  A lancer UNE SEULE FOIS. Tout est consigne dans le fichier
rem  journal_installation.txt (a ouvrir si quelque chose echoue).
rem  Environ 2,5 Go a telecharger, compter 10 a 20 minutes.
rem ============================================================

set JOURNAL=%~dp0journal_installation.txt
echo Installation du moteur Kyutai pour NIMM ePub > "%JOURNAL%"
echo Debut : %DATE% %TIME% >> "%JOURNAL%"

rem Le moteur a besoin de Python 3.12 : la version 3.14 du lecteur ne
rem le fait pas fonctionner, les outils du moteur n'existant pas encore
rem pour cette version de Python.
rem NB : pas de parentheses dans les messages des blocs if / else --
rem elles coupent la lecture du fichier par Windows.
py -3.12 -c "print('ok')" >nul 2>&1
if errorlevel 1 (
  echo.
  echo  ATTENTION : Python 3.12 est introuvable sur cette machine.
  echo.
  echo  Telecharge-le sur python.org -- choisis la version 3.12 --
  echo  installe-le, puis relance ce fichier.
  echo.
  echo  Le moteur Kyutai ne fonctionne pas avec Python 3.14, qui est
  echo  la version utilisee par le lecteur NIMM ePub.
  echo.
  pause
  exit /b 1
)

if exist ".venv\Scripts\python.exe" (
  echo Etape 1/4 : environnement dedie deja present.
) else (
  echo Etape 1/4 : creation de l'environnement dedie -- Python 3.12...
  py -3.12 -m venv ".venv" >> "%JOURNAL%" 2>&1
)

echo Etape 2/4 : mise a jour de l'outil d'installation...
".venv\Scripts\python.exe" -m pip install --upgrade pip >> "%JOURNAL%" 2>&1

echo Etape 3/4 : installation du moteur -- 2,9 Go, environ 5 minutes...
rem PyTorch est un tres gros paquet. Le laisser telecharger par pip s'est
rem bloque le 12/09/2026 (aucun octet pendant 7 minutes) alors que le
rem reseau allait tres bien : on le telecharge donc avec curl, qui sait
rem reprendre un telechargement interrompu, puis on installe depuis le
rem fichier local. Meme methode que celle utilisee dans l'atelier NIMM Voix.
if exist "_tmp_wheel\torch-2.9.1+cu128-cp312-cp312-win_amd64.whl" goto torch_pret
if not exist "_tmp_wheel" mkdir "_tmp_wheel"
echo    telechargement de PyTorch en cours -- la fenetre peut rester "immobile"...
curl.exe -L --retry 20 --retry-all-errors --retry-delay 3 -C - -o "_tmp_wheel\torch-2.9.1+cu128-cp312-cp312-win_amd64.whl" "https://download.pytorch.org/whl/cu128/torch-2.9.1%%2Bcu128-cp312-cp312-win_amd64.whl" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec
:torch_pret
echo    installation de PyTorch depuis le fichier local...
".venv\Scripts\python.exe" -m pip install "_tmp_wheel\torch-2.9.1+cu128-cp312-cp312-win_amd64.whl" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec

echo    installation du moteur Kyutai et de ses petits compagnons...
".venv\Scripts\python.exe" -m pip install "moshi==0.2.13" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec

rem Le paquet PyTorch a servi : on le supprime pour ne pas laisser 2,9 Go
rem inutiles sur le disque.
rmdir /s /q "_tmp_wheel"

echo Etape 4/4 : telechargement des voix francaises et du modele...
".venv\Scripts\python.exe" _telecharger.py >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec

echo.
echo  INSTALLATION TERMINEE.
echo.
echo  Pour entendre le moteur : double-clique sur DEMARRER_KYUTAI.bat
echo.
pause
exit /b 0

:echec
echo.
echo  L'installation s'est arretee sur une erreur.
echo  Ouvre le fichier journal_installation.txt : le detail y est ecrit.
echo  Tu peux relancer ce fichier : il reprend ou il s'est arrete.
echo.
echo  Si le probleme vient de PyTorch, supprime le dossier _tmp_wheel,
echo  puis relance ce fichier.
echo.
pause
exit /b 1
