@echo off
chcp 65001 >nul
title NIMM ePub - ou en sont mes voix ?
cd /d "%~dp0"

rem ============================================================
rem  Affiche OU EN SONT TES VOIX : combien de personnages
rem  lisent avec chaque moteur (Edge, Kokoro, Kyutai, XTTS,
rem  NeuTTS, Piper), combien sont verrouilles, et si chaque
rem  voix attribuee existe bien dans le catalogue du lecteur.
rem
rem  Ce fichier NE MODIFIE RIEN : la base est ouverte en
rem  lecture seule. Aucun moteur n'a besoin d'etre allume.
rem
rem  Double-clic sur ce fichier suffit : rien a taper.
rem ============================================================

echo.
echo ==========================================================
echo   OU EN SONT MES VOIX  (lecture seule, rien n'est modifie)
echo ==========================================================
echo.

python "_etat_familles_voix.py"
if errorlevel 1 (
  echo.
  echo  ERREUR : le script n'a pas pu aller au bout.
  echo  Verifie que Python est installe et que  data\nimm_epub.db  existe.
)

echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
