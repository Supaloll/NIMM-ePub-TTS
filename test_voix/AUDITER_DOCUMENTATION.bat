@echo off
chcp 65001 >nul
title NIMM ePub - AUDIT DE LA DOCUMENTATION
cd /d "%~dp0.."

rem ============================================================
rem  AUDIT DE LA DOCUMENTATION CONTRE LE CODE  (lecture seule)
rem
rem  A quoi ca sert : la documentation raconte l'histoire du
rem  projet, et une histoire vieillit. Cet audit repere les
rem  REFERENCES MORTES -- un fichier renomme, une fonction qui
rem  n'existe plus, une route qui a disparu, une colonne de table
rem  qui a change de nom -- et les items du BACKLOG dont le sujet
rem  est deja livre.
rem
rem  Demande de Laurent, 22/09/2026.
rem
rem  Ce qu'on lit a la fin : le nombre d'alertes, par section. Le
rem  « ! » devant une reference veut dire : document d'ETAT
rem  ACTUEL (les memos, eux, sont des notes datees).
rem
rem  ATTENTION : une alerte n'est pas forcement une erreur. Une
rem  page qui raconte l'histoire d'un fichier disparu a le droit
rem  de le citer. Chaque ligne est a LIRE.
rem
rem  RIEN n'est modifie, rien n'est facture, et AUCUN moteur de
rem  voix n'est demarre.
rem ============================================================

echo.
echo   ==========================================================
echo    AUDIT DE LA DOCUMENTATION  (lecture seule)
echo   ==========================================================
echo.
echo   Il compare les documents au code : fichiers cites,
echo   fonctions, routes, colonnes de la base, tests, et items du
echo   BACKLOG deja livres.
echo.
echo   Rien n'est modifie. Rien n'est facture. Aucun moteur n'est
echo   demarre.
echo.
echo   Le rapport defile ci-dessous, et il est aussi enregistre
echo   dans  _audit_documentation.txt  (racine du projet).
echo.
pause

python "test_voix\_auditer_documentation.py" > "_audit_documentation.txt" 2>&1
type "_audit_documentation.txt"

echo.
echo ----------------------------------------------------------
echo  Le meme rapport est enregistre dans _audit_documentation.txt
echo  (tu peux l'ouvrir pour le lire tranquillement).
echo.
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
