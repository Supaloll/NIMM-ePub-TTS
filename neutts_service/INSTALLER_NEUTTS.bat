@echo off
chcp 65001 >nul
title NIMM ePub - installation du moteur de voix NeuTTS
cd /d "%~dp0"

rem ============================================================
rem  Installation du moteur de voix NeuTTS (clonage de voix,
rem  Neuphonic) pour NIMM ePub. A lancer UNE SEULE FOIS.
rem  Tout est consigne dans journal_installation.txt (a ouvrir si
rem  quelque chose echoue).
rem
rem  Meme principe que les moteurs Kyutai et XTTS : un
rem  environnement Python 3.12 DEDIE, a cote du lecteur (3.14).
rem
rem  Duree : quelques minutes. Les roues PyTorch sont deja dans
rem  le cache pip de cette machine, et les modeles sont deja dans
rem  le cache Hugging Face (5,3 Go) : rien a telecharger.
rem
rem  ATTENTION : les depots de modeles sont « gated » -- il faut
rem  un compte Hugging Face et avoir accepte leurs conditions.
rem  L'atelier NIMM Voix l'a deja fait avec ce compte, et le jeton
rem  est en cache sur ce PC : l'installation part donc toute
rem  seule. Sinon : voir LIRE_MOI.md, section « jeton Hugging Face ».
rem ============================================================

set JOURNAL=%~dp0journal_installation.txt
echo Installation du moteur NeuTTS pour NIMM ePub > "%JOURNAL%"
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
  echo  NeuTTS ne fonctionne pas avec Python 3.14, qui est la version
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
  if errorlevel 1 goto echec
)

echo Etape 2/5 : mise a jour de l'outil d'installation...
".venv\Scripts\python.exe" -m pip install --upgrade pip >> "%JOURNAL%" 2>&1

echo Etape 3/5 : PyTorch 2.11 avec CUDA 12.8 -- deja dans le cache...
rem PyTorch 2.11 et PAS 2.8 : la chaine de NeuTTS passe par neucodec, qui
rem importe torchtune, et torchtune 0.6.1 refuse torch 2.8. Voir
rem requirements.txt pour le detail des deux pieges.
if exist ".venv\Lib\site-packages\torch\version.py" goto torch_pret
".venv\Scripts\python.exe" -m pip install "torch==2.11.*" "torchaudio==2.11.*" --index-url https://download.pytorch.org/whl/cu128 >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec

:torch_pret
echo Etape 4/5 : la bibliotheque neutts et ses deux corrections...
".venv\Scripts\python.exe" -m pip install neutts >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec
rem CORRECTION OBLIGATOIRE : pip tire torchao 0.18, qui a supprime le module
rem torchao.dtypes.nf4tensor reclame par torchtune -- plantage a l'import.
rem La 0.16.0 est la derniere qui l'a encore ; --no-deps est imperatif, sinon
rem pip essaie de deplacer PyTorch au passage.
".venv\Scripts\python.exe" -m pip install --no-deps "torchao==0.16.0" >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec
".venv\Scripts\python.exe" -m pip install espeakng-loader >> "%JOURNAL%" 2>&1
if errorlevel 1 goto echec

echo Etape 5/5 : verification de l'environnement...
".venv\Scripts\python.exe" _verifier_installation.py
if errorlevel 1 goto echec

echo.
echo  INSTALLATION TERMINEE.
echo.
echo  Il reste a poser les voix : les extraits doivent etre dans le
echo  dossier references (voir LIRE_MOI.md, section « les voix »).
echo.
echo  Deux facons de s'en servir :
echo    - DEMARRER_NEUTTS.bat ....... allumer le moteur seul (test)
echo    - START.bat ................. allumer le lecteur
echo.
pause
exit /b 0

:echec
echo.
echo  L'installation s'est arretee sur une erreur.
echo  Ouvre le fichier journal_installation.txt : le detail y est ecrit.
echo  Tu peux relancer ce fichier : il reprend ou il s'est arrete.
echo.
pause
exit /b 1
