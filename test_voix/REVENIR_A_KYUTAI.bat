@echo off
chcp 65001 >nul
title NIMM ePub - revenir aux voix Kyutai
cd /d "%~dp0.."

rem ============================================================
rem  RETOUR ARRIERE de l'essai Qwen (26/09/2026).
rem
rem  Les voix Qwen et les voix Kyutai sont LES MEMES enregistrements :
rem  ce geste ne change donc ni les timbres, ni les prenoms. Il fait
rem  seulement relire ces voix par Kyutai au lieu de Qwen.
rem
rem  D'abord le RAPPORT (rien n'est modifie), puis la question.
rem  En cas de reponse O, la base est COPIEE (fichier date) avant
rem  l'ecriture : c'est le retour arriere de secours.
rem ============================================================

echo.
echo   ==========================================================
echo    REVENIR AUX VOIX KYUTAI  (basculer les voix Qwen)
echo   ==========================================================
echo.

python "test_voix\_basculer_voix_qwen_vers_kyutai.py"

echo.
echo ----------------------------------------------------------
echo  Ci-dessus : ce qui SERAIT fait. Rien n'a ete modifie.
echo ----------------------------------------------------------
echo.
set /p reponse="  Ecrire vraiment maintenant ? (O pour oui, autre touche pour non) "
echo.
if /i not "%reponse%"=="O" (
  echo  Rien n'a ete modifie.
  echo.
  pause
  exit /b 0
)

python "test_voix\_basculer_voix_qwen_vers_kyutai.py" --ecrire

echo.
echo ----------------------------------------------------------
echo  A FAIRE ENSUITE : allumer le moteur Kyutai, et le laisser
echo  ouvert (kyutai_service\DEMARRER_KYUTAI.bat). Au prochain
echo  demarrage, START.bat le rallumera tout seul.
echo ----------------------------------------------------------
pause >nul
