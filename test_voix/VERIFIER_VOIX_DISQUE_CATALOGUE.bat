@echo off
chcp 65001 >nul
title NIMM ePub - VOIX : DISQUE ET CATALOGUE
cd /d "%~dp0.."

rem ============================================================
rem  LE DISQUE ET LE CATALOGUE DES VOIX DISENT-ILS LA MEME CHOSE ?
rem  (lecture seule)
rem
rem  A quoi ca sert (demande de Laurent, 24/10/2026) : il clone des
rem  voix, et trois choses doivent arriver ENSEMBLE -- le fichier de
rem  reference dans le dossier du service, sa ligne de TEXTE, et son
rem  entree dans le CATALOGUE (modules/tts.py). En oublier une ne
rem  casse rien tout de suite :
rem
rem    - entree au catalogue SANS fichier  = personnage MUET ;
rem    - fichier SANS entree au catalogue  = voix INVISIBLE dans les
rem      menus (on peut l'entendre dans un livre sans pouvoir la
rem      choisir ailleurs) ;
rem    - fichier SANS texte (qwen, neutts) = le service refuse la
rem      voix, ou le moteur invente une prononciation.
rem
rem  Il verifie les cinq familles a fichiers : qwen, kyutai, xtts,
rem  neutts et pocket. Kokoro, Piper et Edge n'ont pas de fichier par
rem  voix (modeles ou cloud) : ils ne sont pas verifiables ici.
rem
rem  Il signale aussi les voix dont la DUREE ANNONCEE s'ecarte de 2 s
rem  ou plus de celle du fichier : c'est le signe qu'un texte a ete
rem  colle a un AUTRE enregistrement.
rem
rem  « A LIRE » n'est pas forcement une erreur ; un ECHEC, si.
rem
rem  RIEN n'est modifie, rien n'est facture, et AUCUN moteur de voix
rem  n'est demarre.
rem ============================================================

echo.
echo   ==========================================================
echo    VOIX : LE DISQUE ET LE CATALOGUE DANSENT-ILS ENSEMBLE ?
echo   ==========================================================
echo.
echo   Pour chaque famille (qwen, kyutai, xtts, neutts, pocket) :
echo     - chaque voix du catalogue a son fichier de reference ;
echo     - chaque fichier a son entree au catalogue ;
echo     - pour qwen et neutts, chaque voix a son TEXTE.
echo.
echo   A lancer APRES avoir clone des voix : c'est le controle
echo   avant de les ecouter. Une voix muette, ou une voix invisible
echo   dans les menus, se voit ici tout de suite.
echo.
echo   Rien n'est modifie. Rien n'est facture. Aucun moteur n'est
echo   demarre.
echo.
pause

python "test_voix\test_coherence_voix.py" > "_voix_disque_catalogue.txt" 2>&1
type "_voix_disque_catalogue.txt"

echo.
echo ----------------------------------------------------------
echo  Le meme rapport est enregistre dans
echo  _voix_disque_catalogue.txt  (racine du projet).
echo.
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
