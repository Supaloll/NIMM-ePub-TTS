@echo off
chcp 65001 >nul
title NIMM ePub - ouvrir le fichier des cles API
setlocal
cd /d "%~dp0"

rem ============================================================
rem  OU OU SONT MES CLES API ?
rem
rem  Demande de Laurent, 24/09/2026 : « il y a trop de fichiers,
rem  je ne trouve pas le fichier .txt pour les cles api ».
rem
rem  C'est vrai : il est noye dans les 289 fichiers du dossier
rem  test_voix. D'ou ce raccourci : un double-clic ouvre le
rem  fichier dans le Bloc-notes, et rappelle ce qu'on y met.
rem
rem  Ce lanceur N'AFFICHE JAMAIS tes cles a l'ecran : il dit
rem  seulement si la ligne existe ou non.
rem
rem  Ce fichier n'est PAS suivi par Git (il est dans .gitignore) :
rem  tes cles ne partent dans aucun commit.
rem ============================================================

set FICHIER=%~dp0test_voix\cles_api.txt

echo.
echo  ============================================================
echo   TES CLES API : LE FICHIER ET SA VERSION
echo  ============================================================
echo.
echo   Emplacement exact :
echo     %FICHIER%
echo.

if not exist "%FICHIER%" (
  echo   ERREUR : le fichier est introuvable.
  echo.
  echo   Ouvre le dossier test_voix et regarde s'il n'a pas ete
  echo   renomme. Sinon, demande a Cline de le recreer.
  echo.
  pause
  exit /b 1
)

echo   Ce qu'on met dedans, une ligne par cle, sous la forme
echo   NOM=valeur  --  jamais d'espace autour du signe egal :
echo.
echo     ANTHROPIC_API_KEY=...   (Claude)
echo     MISTRAL_API_KEY=...     (Mistral)
echo     GOOGLE_API_KEY=...      (Gemini, pour l'ancien outil)
echo     DEEPSEEK_API_KEY=...    (DeepSeek)
echo     OPENAI_API_KEY=...      (OpenAI -- la ligne a ajouter)
echo.
echo   Pour l'essai de comparaison des providers, la seule ligne
echo   a ajouter est  OPENAI_API_KEY=ta_cle  . Les trois autres
echo   moteurs (Gemini, Mistral, DeepSeek) sont deja lus par
echo   l'application dans data\config.json : rien a faire pour eux.
echo.

findstr /C:"OPENAI_API_KEY=" "%FICHIER%" >nul 2>&1
if errorlevel 1 (
  echo   ETAT : la ligne OPENAI_API_KEY n'est PAS encore la.
  echo          Ajoute-la a la fin du fichier, puis enregistre.
) else (
  echo   ETAT : la ligne OPENAI_API_KEY est presente.
  echo          Verifie qu'il y a bien une valeur apres le signe egal.
)
echo.
echo   (Tu peux aussi retrouver ce fichier a la main : dans le dossier
echo    test_voix, tape « cles » dans la barre de recherche.)
echo.
echo   Appuie sur une touche pour ouvrir le fichier dans le Bloc-notes...
pause >nul

start "" notepad "%FICHIER%"

echo.
echo   Le Bloc-notes est ouvert.
echo   Pense a ENREGISTRER (Ctrl+S) apres avoir colle ta cle.
echo.
echo   Ensuite, pour lancer la comparaison des providers : ouvre le
echo   dossier test_voix, tape COMPARER dans la barre de recherche,
echo   et double-clique sur le fichier .bat trouve.
echo.
pause
endlocal
