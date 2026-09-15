@echo off
chcp 65001 >nul
title NIMM ePub - installation du moteur de voix XTTS v2
cd /d "%~dp0"

rem ============================================================
rem  Installation du moteur XTTS v2 (clonage de voix, coqui-tts)
rem  pour NIMM ePub. A lancer UNE SEULE FOIS.
rem  Tout est consigne dans journal_installation.txt (a ouvrir si
rem  quelque chose echoue).
rem
rem  Poids : environ 3,5 Go a telecharger pour PyTorch (une fois), et
rem  environ 8 Go sur le disque une fois tout installe (PyTorch prend
rem  beaucoup de place). Le modele XTTS v2 (2,1 Go) se telecharge au
rem  premier chargement s'il n'est pas deja en cache.
rem  Si PyTorch a deja servi sur cette machine, pip le reprend dans
rem  son cache : l'installation prend alors quelques minutes.
rem
rem  Meme principe que le moteur Kyutai : un environnement Python
rem  3.12 DEDIE, a cote du lecteur (qui tourne en 3.14).
rem ============================================================

set JOURNAL=%~dp0journal_installation.txt
echo Installation du moteur XTTS v2 pour NIMM ePub > "%JOURNAL%"
echo Debut : %DATE% %TIME% >> "%JOURNAL%"

rem Le moteur a besoin de Python 3.12. NB : pas de parentheses dans les
rem messages des blocs if / else -- elles coupent la lecture du fichier
rem par Windows (lecon des installateurs precedents).
py -3.12 -c "print('ok')" >nul 2>&1
if errorlevel 1 (
  echo.
  echo  ATTENTION : Python 3.12 est introuvable sur cette machine.
  echo.
  echo  Telecharge-le sur python.org -- choisis la version 3.12 --
  echo  installe-le, puis relance ce fichier.
  echo.
  echo  XTTS v2 ne fonctionne pas avec Python 3.14, qui est la version
  echo  utilisee par le lecteur NIMM ePub.
  echo.
  pause
  exit /b 1
)

if exist ".venv\Scripts\python.exe" (
  echo Etape 1/5 : environnement dedie deja present.
) else (
  echo Etape 1/5 : creation de l'environnement dedie -- Python 3.12...
  py -3.12 -m venv ".venv" >> "%JOURNAL%" 2>&1
)

echo Etape 2/5 : mise a jour de l'outil d'installation...
".venv\Scripts\python.exe" -m pip install --upgrade pip >> "%JOURNAL%" 2>&1

echo Etape 3/5 : PyTorch 2.8 avec CUDA 12.8 -- 3,5 Go, patience...
rem Deux precautions, apprises a l'atelier NIMM Voix le 14/09/2026 :
rem  - PyTorch 2.8 et PAS plus recent : a partir de 2.9, coqui-tts
rem    reclame la bibliotheque torchcodec, qui reclame a son tour les
rem    DLL FFmpeg « partagees » absentes de cette machine -- erreur
rem    « Could not load libtorchcodec ». Avec 2.8, coqui-tts passe par
rem    torchaudio et tout fonctionne ; un torch plus recent n'apporte
rem    rien ici ;
rem  - si pip se bloque en pleine descente, on reprend par curl, qui
rem    sait reprendre un telechargement interrompu (meme parade que
rem    pour Kyutai le 12/09/2026).
if exist ".venv\Lib\site-packages\torch\version.py" goto torch_pret
".venv\Scripts\python.exe" -m pip install "torch==2.8.*" "torchaudio==2.8.*" --index-url https://download.pytorch.org/whl/cu128 >> "%JOURNAL%" 2>&1
if errorlevel 1 goto torch_par_curl
goto torch_pret

:torch_par_curl
echo    pip n'a pas abouti : nouvelle tentative par curl, en direct...
if not exist "_tmp_wheel" mkdir "_tmp_wheel"
curl.exe -L --retry 20 --retry-all-errors --retry-delay 3 -C - -o "_tmp_wheel\torch-2.8.0+cu128-cp312-cp312-win_amd64.whl" "https://download.pytorch.org/whl/cu128/torch-2.8.0%%2Bcu128-cp312-cp312-win_amd64.whl" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec
curl.exe -L --retry 20 --retry-all-errors --retry-delay 3 -C - -o "_tmp_wheel\torchaudio-2.8.0+cu128-cp312-cp312-win_amd64.whl" "https://download.pytorch.org/whl/cu128/torchaudio-2.8.0%%2Bcu128-cp312-cp312-win_amd64.whl" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec
".venv\Scripts\python.exe" -m pip install "_tmp_wheel\torch-2.8.0+cu128-cp312-cp312-win_amd64.whl" "_tmp_wheel\torchaudio-2.8.0+cu128-cp312-cp312-win_amd64.whl" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec
rmdir /s /q "_tmp_wheel"

:torch_pret
echo Etape 4/5 : la bibliotheque coqui-tts et ses compagnons...
rem PRECAUTION (mesuree a l'atelier) : coqui-tts 0.27.5 exige
rem « transformers >= 4.57 » SANS borne haute, or transformers 5.x a
rem supprime une fonction qu'il utilise (isin_mps_friendly) -- l'import
rem de TTS echoue. On borne donc a la branche 4.x.
".venv\Scripts\python.exe" -m pip install coqui-tts "transformers>=4.57,<5" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec

echo Etape 5/5 : voix francaises et modele XTTS v2 -- 2,1 Go...
rem Cette etape s'affiche A L'ECRAN (et pas seulement dans le journal) :
rem c'est le seul moment ou l'on attend vraiment, autant voir ou on en est.
".venv\Scripts\python.exe" _telecharger.py
if errorlevel 1 goto echec

echo.
echo  INSTALLATION TERMINEE.
echo.
echo  Deux facons de s'en servir :
echo    - DEMARRER_XTTS.bat ......... allumer le moteur seul (test)
echo    - START.bat ................. allumer le lecteur, qui s'en occupe
echo.
echo  Pour verifier l'environnement sans rien lancer :
echo    .venv\Scripts\python.exe _verifier_installation.py
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
