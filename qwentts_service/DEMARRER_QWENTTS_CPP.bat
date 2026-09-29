@echo off
chcp 65001 >nul
title NIMM ePub - appareil de voix Qwen3-TTS (qwentts.cpp)
cd /d "%~dp0"

rem ============================================================
rem  MOTEUR DE VOIX QWEN3-TTS -- qwentts.cpp, port 8086
rem
rem  C'est le portage C++/GGML de Qwen3-TTS : il tourne sur le
rem  PROCESSEUR, sans PyTorch et sans occuper la carte graphique.
rem  Laurent l'a ecoute et valide le 28/09/2026 : « c'est vraiment
rem  bon, pas d'accrocs, prosodie impec, on a notre moteur ! »
rem
rem  En usage normal, c'est START.bat qui l'allume : Laurent n'a
rem  rien a ouvrir. Cette fenetre-ci sert a VOIR ce que dit le
rem  moteur, ou a l'allumer a la main pour un essai.
rem
rem  Fermer cette fenetre ETEINT le moteur -- et le veilleur du
rem  lecteur le rallumera au prochain demarrage de START.bat.
rem
rem  Une seule fenetre a la fois : le service REFUSE de demarrer si
rem  le port 8086 est deja pris, plutot que de partager le port avec
rem  un autre moteur -- lecon du 28/09/2026.
rem ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   Le moteur n'est pas installe sur ce PC.
  echo   Il faut le paquet realtimetts-qwen-native-cpu et les modeles.
  echo   Voir  qwentts_service\LIRE_MOI.md
  echo.
  pause
  exit /b 1
)

rem  Les MODELES en service depuis le 29/09/2026 sont les Q4_K_M (choisis a
rem  l'oreille par Laurent : « les plus jolies a l'oreille », prosodie et clarte
rem  un demi-cran au-dessus). Les Q8_0 restent sur le disque comme REPLI : il
rem  suffit qu'UNE des deux paires soit presente.
if not exist "models\qwen-talker-0.6b-base-Q4_K_M.gguf" if not exist "models\qwen-talker-0.6b-base-Q8_0.gguf" (
  echo.
  echo   Les MODELES du moteur sont absents du dossier  models\
  echo.
  echo   En service : qwen-talker-0.6b-base-Q4_K_M.gguf
  echo                qwen-tokenizer-12hz-Q4_K_M.gguf
  echo   Le repli  : qwen-talker-0.6b-base-Q8_0.gguf
  echo                qwen-tokenizer-12hz-Q8_0.gguf
  echo.
  pause
  exit /b 1
)

echo.
echo   ======================================================
echo    MOTEUR DE VOIX QWEN3-TTS -- qwentts.cpp -- port 8086
echo   ======================================================
echo.
echo   Ce moteur tourne sur le PROCESSEUR : il n'occupe pas la
echo   carte graphique, et il cohabite avec Kyutai et Pocket.
echo.
echo   Premier demarrage : le modele se charge en 1 a 3 secondes.
echo   La PREMIERE phrase de chaque voix est plus lente : le moteur
echo   prepare son empreinte, une fois par voix.
echo.
echo   Fermer cette fenetre ETEINT le moteur.
echo.

".venv\Scripts\python.exe" -u servir_qwentts_cpp.py

echo.
echo   Le moteur est arrete.
pause
