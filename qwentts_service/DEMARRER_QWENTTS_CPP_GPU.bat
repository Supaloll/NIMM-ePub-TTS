@echo off
chcp 65001 >nul
title NIMM ePub - moteur de voix Qwen3-TTS SUR LA CARTE GRAPHIQUE (qwentts.cpp)
cd /d "%~dp0"

rem ============================================================
rem  MOTEUR DE VOIX QWEN3-TTS SUR LA CARTE GRAPHIQUE -- port 8086
rem
rem  Le MEME moteur que DEMARRER_QWENTTS_CPP.bat, mais il utilise la
rem  CARTE GRAPHIQUE au lieu du processeur. Mesure du 01/10/2026 (atelier
rem  NIMM Voix) : x6,5 a x7,5 le temps reel, contre x0,85 sur le processeur.
rem  DEPUIS LE 03/10/2026 la variante est Q8_0 (voir plus bas) : x5,1 a x5,9.
rem
rem  SI LA CARTE ECHOUE, LE SERVICE REPLIE TOUT SEUL SUR LE PROCESSEUR : il ne
rem  s'arrete pas, et la page /sante le dit.
rem
rem  ATTENTION : sur la carte, ce moteur prend environ 4,7 Go de memoire video.
rem  Ne lancez pas Kyutai en meme temps (Pocket, lui, tourne sur le processeur
rem  et ne gene pas).
rem
rem  POUR REVENIR AU PROCESSEUR : fermer cette fenetre, puis double-clic sur
rem  DEMARRER_QWENTTS_CPP.bat (le bouton habituel, inchange).
rem
rem  Fermer cette fenetre ETEINT le moteur.
rem ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   Le moteur n'est pas installe sur ce PC.
  echo   Voir  qwentts_service\LIRE_MOI.md
  echo.
  pause
  exit /b 1
)

if not exist "models\qwen-talker-0.6b-base-Q8_0.gguf" (
  echo.
  echo   Les MODELES Q8_0 sont absents du dossier  models\
  echo   ce sont eux que ce bouton utilise sur la carte.
  echo.
  pause
  exit /b 1
)

rem  Les deux reglages qui font tourner le service sur la CARTE.
rem  Le moteur choisit la carte tout seul (backend CUDA0) ; s'il echoue,
rem  le service reprend sur le processeur (repli automatique).
rem
rem  VARIANTE Q8_0 depuis le 03/10/2026, sur le verdict d'oreille de Laurent.
rem  Mesure du 01/10/2026 (atelier NIMM Voix), meme protocole, 20 tirages par
rem  variante : Q4_K_M PART 3 fois sur 20, Q8_0 1 fois sur 20 -- et Laurent a
rem  designe a l'oreille EXACTEMENT ce fichier-la. Prix de ce choix : x5,1 a
rem  x5,9 le temps reel au lieu de x7,6 a x8,2 (donc encore 5 fois plus vite
rem  que la lecture), et environ 0,6 Go de memoire video en plus.
rem  POUR REVENIR EN ARRIERE : remettre Q4_K_M sur la ligne VARIANTE.
rem  (Le REPLI processeur, lui, garde Q4_K_M : c'est un mode degrade, on ne
rem  l'alourdit pas.)
set NIMM_QWENTTS_MOTEUR=gpu
set NIMM_QWENTTS_VARIANTE=Q8_0

echo.
echo   ======================================================
echo    MOTEUR DE VOIX QWEN3-TTS SUR LA CARTE GRAPHIQUE
echo    qwentts.cpp -- port 8086 -- Q8_0
echo   ======================================================
echo.
echo   Memoire video utilisee : environ 4,7 Go.
echo   Si la carte echoue, le service reprend sur le processeur.
echo.
echo   Si le moteur ne repond pas, c'est peut-etre que la carte est
echo   deja prise par un autre programme : fermez-le, puis relancez.
echo.
echo   Fermer cette fenetre ETEINT le moteur.
echo.

".venv\Scripts\python.exe" -u servir_qwentts_cpp.py

echo.
echo   Le moteur est arrete.
pause
