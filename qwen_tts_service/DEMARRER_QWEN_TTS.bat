@echo off
chcp 65001 >nul
title NIMM ePub - appareil de voix Qwen3-TTS (laisser cette fenetre ouverte)
cd /d "%~dp0"

rem ============================================================
rem  Demarre l'appareil de voix Qwen3-TTS (Alibaba, Apache-2.0).
rem  A laisser ouvert pendant l'ecoute des livres qui utilisent
rem  les voix Qwen. Fermer cette fenetre = arreter le moteur
rem  (les voix Edge, Kokoro et Piper continuent de fonctionner).
rem
rem  C'est le MEME materiau que le moteur Kyutai : les 35 memes
rem  extraits de voix, mais lus par Qwen3-TTS. Un seul moteur
rem  lourd a la fois sur la carte graphique (8 Go) : celui-ci
rem  prend la place de Kyutai, il ne s'y ajoute pas.
rem ============================================================

rem -- QUEL PYTHON ? Deux cas, dans l'ordre :
rem    1. l'environnement installe ICI (qwen_tts_service\.venv), le jour
rem       ou on l'aura : c'est celui qu'on veut a terme ;
rem    2. l'environnement de l'atelier NIMM Voix (Python 3.12 + PyTorch +
rem       qwen-tts), PREte et utilise pour l'essai du 26/09/2026. Rien
rem       n'est installe ni telecharge : on emprunte celui qui existe.
rem    Si aucun des deux n'existe, on le dit et on n'essaie meme pas.
set PYTHON_MOTEUR=
if exist ".venv\Scripts\python.exe" set PYTHON_MOTEUR=.venv\Scripts\python.exe
if not defined PYTHON_MOTEUR if exist "G:\NIMM Voix\outils\qwen3_tts\.venv\Scripts\python.exe" set PYTHON_MOTEUR=G:\NIMM Voix\outils\qwen3_tts\.venv\Scripts\python.exe

if not defined PYTHON_MOTEUR (
  echo.
  echo  L'environnement du moteur Qwen3-TTS est introuvable.
  echo.
  echo  Cherche, dans cet ordre :
  echo    1. %~dp0.venv\Scripts\python.exe
  echo    2. G:\NIMM Voix\outils\qwen3_tts\.venv\Scripts\python.exe
  echo.
  echo  Aucun des deux n'est la : les voix Qwen resteront impossibles
  echo  a lire tant que l'un des deux n'existe pas.
  echo.
  pause
  exit /b 1
)

rem -- NIMM ePub note ici LE DERNIER MOTEUR UTILISE (pense-bete relu par
rem    START.bat au prochain demarrage). Ecrit AVANT le chargement.
if not exist "..\data" mkdir "..\data"
> "..\data\moteur_voix.txt" echo qwen

rem HF_HUB_DISABLE_XET=1 : le stockage "xet" de Hugging Face a deja
rem bloque un telechargement le 11/09/2026 (meme precaution que Kyutai).
set HF_HUB_DISABLE_XET=1

echo.
echo  ==========================================================
echo    NIMM ePub - appareil de voix Qwen3-TTS
echo    Adresse : http://127.0.0.1:8086
echo    Le moteur se charge (quelques secondes), puis reste pret.
echo    Fermer cette fenetre = arreter le moteur.
echo  ==========================================================
echo.

"%PYTHON_MOTEUR%" servir_qwen_tts.py

echo.
echo  Le moteur est arrete.
pause
