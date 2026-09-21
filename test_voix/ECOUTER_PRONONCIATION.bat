@echo off
chcp 65001 >nul
title NIMM ePub - ecouter la prononciation des prenoms (Kokoro)
cd /d "%~dp0.."

rem ============================================================
rem  LOT D'ECOUTE : LA PRONONCIATION DES PRENOMS (21/09/2026)
rem
rem  POURQUOI CE LANCEUR : Kokoro lit le francais avec un
rem  phonemiseur multi-langues (espeak-ng). Sur certains prenoms
rem  -- Andrea, Marthe, Arthur, Nathan, Ethan, Maelys, Mathis,
rem  Noah -- ce phonemiseur bascule sur son dictionnaire ANGLAIS
rem  et MARQUE la frontiere dans sa sortie ; le moteur, lui,
rem  PRONONCE cette marque : Laurent entendait « en Andrea fe ».
rem
rem  Le correctif impose les SONS FRANCAIS. Ce dossier compare,
rem  pour les MEMES phrases, l'avant et l'apres : c'est TON oreille
rem  qui tranche, et une graphie que tu n'aimes pas est retiree
rem  (une ligne a changer dans modules/prononciation.py).
rem
rem  Aucun acces Internet, rien de facture : tout se passe ici.
rem ============================================================

echo.
echo   ==========================================================
echo    PRONONCIATION DES PRENOMS : LOT D'ECOUTE (voix Narrateur)
echo   ==========================================================
echo.
echo   Le lot contient des PAIRES de fichiers, pour les MEMES phrases :
echo.
echo      NN_avant_^<mot^>.wav   ce que tu entends AUJOURD'HUI  ^(on entend
echo                             les marques : « en ... fe »^)
echo      NN_apres_^<mot^>.wav   APRES le correctif  ^(sons francais^)
echo.
echo   Ce qu'il faut juger, pour CHAQUE paire :
echo      1. les syllabes en trop ^(« en » et « fe »^) ont-elles disparu ?
echo      2. le prenom sonne-t-il francais, et non anglais ?
echo.
echo   Andrea est le TEMOIN : ce cas a deja ete valide en atelier.
echo   Les cinq a departager : Ethan, Maelys, Mathis, Noah, dos.
echo.
echo   Le mode d'emploi du lot :  A_LIRE.txt
echo   Le detail des phonemes   :  mesure_phonemes.txt
echo.
echo   La generation prend une trentaine de secondes ^(le modele
echo   Kokoro de 300 Mo doit se charger^).
echo.
pause

echo.
echo ==========================================================
echo   GENERATION DU LOT
echo ==========================================================
echo.
python "test_voix\_mesurer_prononciation_kokoro.py"

echo.
echo ==========================================================
echo   LE DOSSIER VA S'OUVRIR : double-clique sur les fichiers
echo   dans l'ordre (01_avant, 01_apres, 02_avant, 02_apres...)
echo ==========================================================
echo.
start "" "test_voix\sortie_ecoute_prononciation"
echo.
echo ----------------------------------------------------------
echo  Dis a Cline ce que tu retiens de chaque paire.
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
