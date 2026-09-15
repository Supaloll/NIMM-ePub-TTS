@echo off
chcp 65001 >nul
title NIMM ePub - appareil de voix Kyutai (laisser cette fenetre ouverte)
cd /d "%~dp0"

rem ============================================================
rem  Demarre l'appareil de voix Kyutai TTS 1.6B.
rem  A laisser ouvert pendant l'ecoute des livres qui utilisent
rem  les voix Kyutai. Fermer cette fenetre = arreter le moteur
rem  (les voix Edge, Kokoro et Piper continuent de fonctionner).
rem ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo  L'environnement du moteur Kyutai n'existe pas encore.
  echo  Double-clique d'abord sur INSTALLER_KYUTAI.bat
  echo.
  pause
  exit /b 1
)

rem -- NIMM ePub note ici LE DERNIER MOTEUR UTILISE (demande de Laurent,
rem    14/09/2026) : c'est ce nom que START.bat relira au prochain
rem    demarrage pour allumer le bon moteur. C'est un simple pense-bete,
rem    ecrit AVANT le chargement -- aucune influence sur le moteur.
if not exist "..\data" mkdir "..\data"
> "..\data\moteur_voix.txt" echo kyutai

rem NO_TORCH_COMPILE=1 : indispensable sous Windows (torch.compile()
rem ne peut pas fonctionner ici, faute de Triton) -- remede indique
rem par la documentation de Kyutai.
set NO_TORCH_COMPILE=1
set HF_HUB_DISABLE_XET=1

echo.
echo  ==========================================================
echo    NIMM ePub - appareil de voix Kyutai TTS 1.6B
echo    Adresse : http://127.0.0.1:8082
echo    Le moteur se charge (quelques secondes), puis reste pret.
echo    Fermer cette fenetre = arreter le moteur.
echo  ==========================================================
echo.

".venv\Scripts\python.exe" servir_kyutai.py

echo.
echo  Le moteur est arrete.
pause
