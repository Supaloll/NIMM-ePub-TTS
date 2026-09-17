@echo off
chcp 65001 >nul
title NIMM ePub - appareil de voix NeuTTS (laisser cette fenetre ouverte)
cd /d "%~dp0"

rem ============================================================
rem  Demarre l'appareil de voix NeuTTS (clonage de voix).
rem  A laisser ouvert pendant l'ecoute des livres qui utilisent
rem  les voix NeuTTS. Fermer cette fenetre = arreter le moteur
rem  (les voix Edge, Kokoro et Piper continuent de fonctionner).
rem
rem  Adresse : http://127.0.0.1:8084
rem  Chargement du modele : ~10 s a chaud.
rem
rem  NB : contrairement au moteur XTTS, ce n'est PAS un moteur de
rem  carte graphique obligatoire -- il tourne aussi sur le
rem  processeur (3 a 4 fois plus lent). Pour le forcer sur le
rem  processeur : mettre NIMM_NEUTTS_APPAREIL=cpu ci-dessous.
rem
rem  NB 2 : ce lanceur note « neutts » dans data\moteur_voix.txt,
rem  comme le font les lanceurs XTTS et Kyutai : c'est le pense-bete du
rem  dernier moteur utilise (START.bat le relit au demarrage suivant).
rem ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo  L'environnement du moteur NeuTTS n'existe pas encore.
  echo  Double-clique d'abord sur INSTALLER_NEUTTS.bat
  echo.
  pause
  exit /b 1
)

rem -- NIMM ePub note ici LE DERNIER MOTEUR UTILISE (comme les lanceurs
rem    XTTS et Kyutai) : c'est un simple pense-bete, ecrit AVANT le
rem    chargement -- aucune influence sur le moteur.
if not exist "..\data" mkdir "..\data"
> "..\data\moteur_voix.txt" echo neutts

rem Le stockage « xet » de Hugging Face a deja bloque un telechargement
rem le 11/09/2026 : on le desactive preventivement (meme precaution que
rem pour Kyutai et XTTS).
set HF_HUB_DISABLE_XET=1

rem Appareil : auto (carte graphique si elle est libre), cuda, ou cpu.
set NIMM_NEUTTS_APPAREIL=auto

echo.
echo  ==========================================================
echo    NIMM ePub - appareil de voix NeuTTS (clonage)
echo    Adresse : http://127.0.0.1:8084
echo    Le moteur se charge (~10 s), puis reste pret.
echo    Fermer cette fenetre = arreter le moteur.
echo  ==========================================================
echo.

".venv\Scripts\python.exe" servir_neutts.py

echo.
echo  Le moteur est arrete.
pause
