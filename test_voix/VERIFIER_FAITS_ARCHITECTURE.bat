@echo off
chcp 65001 >nul
title NIMM ePub - VERIFIER LES FAITS DE ARCHITECTURE.md
cd /d "%~dp0.."

rem ============================================================
rem  LES FAITS DE ARCHITECTURE.md, VERIFIES CONTRE LE CODE
rem  (lecture seule)
rem
rem  A quoi ca sert : ce document raconte l'etat du projet, et il
rem  peut se tromper sans que personne ne le voie -- c'est arrive
rem  le 23/09/2026 avec la pause entre paragraphes : la page
rem  annoncait 0 alors que le code portait 300 depuis six jours.
rem
rem  L'audit de la documentation, lui, verifie les NOMS (le
rem  fichier cite existe, la fonction citee existe...). Cet
rem  outil-ci verifie les PHRASES verifiables : le plan du
rem  dossier, les constantes citees avec leur valeur, les ports
rem  des moteurs, les fichiers de donnees, la version de cache,
rem  et -- depuis le 23/09/2026 -- les sujets passes a l'etat
rem  actuel en clair (modules/tts.py, la page, Pocket TTS, les
rem  notes d'ecoute, le casting, les symboles de genre, le
rem  lecteur et l'ecran verrouille) : leurs moteurs, leurs
rem  icones, leurs routes, leurs tests.
rem
rem  POUR COMPTER LES CONTROLES DES TESTS CITES, il LANCE quatre
rem  tests (trois JavaScript, un Python). Ce sont des tests HORS
rem  LIGNE : pas de navigateur, pas de reseau, pas de base -- et
rem  rien n'est facture.
rem
rem  Ce qu'on lit a la fin : le nombre d'ECARTS a lire. Un ecart
rem  n'est pas forcement une erreur : une phrase datee a le droit
rem  de raconter une decision d'hier.
rem
rem  RIEN n'est modifie, rien n'est facture, et AUCUN moteur de
rem  voix n'est demarre.
rem ============================================================

echo.
echo   ==========================================================
echo    VERIFIER LES FAITS DE ARCHITECTURE.md  (lecture seule)
echo   ==========================================================
echo.
echo   Il compare les PHRASES du document au code : plan du
echo   dossier, constantes citees avec leur valeur, ports des
echo   moteurs, fichiers de donnees, version de cache, et les
echo   sujets passes a l'etat actuel en clair (les moteurs,
echo   les vues de la page, le casting, les symboles de genre,
echo   le lecteur et l'ecran verrouille...).
echo.
echo   Pour compter les controles des tests cites, il LANCE
echo   quatre tests hors ligne. Rien n'est modifie, rien n'est
echo   facture, aucun moteur de voix n'est demarre.
echo.
echo   Rien n'est modifie. Rien n'est facture. Aucun moteur n'est
echo   demarre.
echo.
echo   A la fin, tu dois lire :   0 ecart(s) a lire
echo.
pause

python "_verifier_faits_architecture.py"

echo.
echo ----------------------------------------------------------
echo  Un ECART n'est pas forcement une erreur : chaque ligne
echo  est a LIRE (une phrase datee a le droit de raconter une
echo  decision d'hier).
echo.
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
