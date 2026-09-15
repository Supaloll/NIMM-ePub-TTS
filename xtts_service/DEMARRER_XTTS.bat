@echo off
chcp 65001 >nul
title NIMM ePub - appareil de voix XTTS v2 (laisser cette fenetre ouverte)
cd /d "%~dp0"

rem ============================================================
rem  Demarre l'appareil de voix XTTS v2 (clonage de voix).
rem  A laisser ouvert pendant l'ecoute des livres qui utilisent
rem  les voix XTTS. Fermer cette fenetre = arreter le moteur
rem  (les voix Edge, Kokoro et Piper continuent de fonctionner).
rem
rem  Un seul moteur lourd a la fois : Kyutai et XTTS occupent
rem  chacun la carte graphique, les deux ne tiennent pas ensemble.
rem ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo  L'environnement du moteur XTTS v2 n'existe pas encore.
  echo  Double-clique d'abord sur INSTALLER_XTTS.bat
  echo.
  pause
  exit /b 1
)

rem -- NIMM ePub note ici LE DERNIER MOTEUR UTILISE (demande de Laurent,
rem    14/09/2026) : c'est ce nom que START.bat relira au prochain
rem    demarrage pour allumer le bon moteur. C'est un simple pense-bete,
rem    ecrit AVANT le chargement -- aucune influence sur le moteur.
if not exist "..\data" mkdir "..\data"
> "..\data\moteur_voix.txt" echo xtts

rem Le stockage « xet » de Hugging Face a deja bloque un telechargement
rem le 11/09/2026 : on le desactive preventivement (meme precaution que
rem pour Kyutai).
set HF_HUB_DISABLE_XET=1

echo.
echo  ==========================================================
echo    NIMM ePub - appareil de voix XTTS v2 (clonage)
echo    Adresse : http://127.0.0.1:8083
echo    Le moteur se charge (10 a 20 s), puis reste pret.
echo    Fermer cette fenetre = arreter le moteur.
echo  ==========================================================
echo.

".venv\Scripts\python.exe" servir_xtts.py

echo.
echo  Le moteur est arrete.
pause
