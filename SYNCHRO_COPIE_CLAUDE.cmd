@echo off
chcp 65001 >nul
title NIMM ePub - sync copie pour Claude
cd /d "%~dp0"

rem ============================================================
rem  SYNCHRO "COPIE POUR CLAUDE" -- NIMM ePub
rem
rem  Remplit (vide puis recopie) le dossier  copie_pour_Claude\  a la racine,
rem  a partir de la liste  copie_pour_Claude_liste.txt .
rem  Rien n'est ecrit en dehors de copie_pour_Claude\.
rem
rem  A faire APRES une session ou des fichiers ont change : Laurent selectionne
rem  TOUT le dossier copie_pour_Claude\ et le glisse dans un projet Claude,
rem  puis lit d'abord  _ETAT_DU_JOUR.md .
rem ============================================================

where python >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Python n'est pas trouve. Voir  test_voix\LIRE_MOI.md
  echo.
  pause
  exit /b 1
)

echo.
echo   ======================================================
echo    SYNCHRO "COPIE POUR CLAUDE"
echo   ======================================================
echo   On commence par un TEST A BLANC : rien n'est copie.
echo.
python _synchroniser_copie_claude.py --blanc

echo.
set /p OK=  Ecrire la VRAIE copie maintenant (vider puis recopier copie_pour_Claude) ? o/n : 
if /i not "%OK%"=="o" (
  echo.
  echo   Annule : rien n'a ete copie.
  echo.
  pause
  exit /b 0
)

echo.
python _synchroniser_copie_claude.py
echo.
echo   C'est pret : glisse TOUT le dossier  copie_pour_Claude\  dans ton projet
echo   Claude, et lis d'abord  _ETAT_DU_JOUR.md .
echo.
pause
