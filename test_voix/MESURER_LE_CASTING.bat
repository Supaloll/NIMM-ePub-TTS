@echo off
chcp 65001 >nul
title NIMM ePub - MESURER LE CASTING (gratuit)
cd /d "%~dp0.."

rem ============================================================
rem  LE CASTING IA SE TROMPE-T-IL BEAUCOUP ? -- mesure GRATUITE
rem
rem  Question de fond : faut-il donner plus de contexte au
rem  casting (resume de scene, personnages presents) pour qu'il
rem  attribue mieux les voix ? Avant de construire quoi que ce
rem  soit, on MESURE.
rem
rem  Ce lanceur regarde les etiquettes QUE L'IA A PRODUITES (une
rem  copie de la base d'avant migration) sur 4 chapitres
rem  difficiles, et compte les erreurs OBJECTIVES -- celles qui
rem  ne dependent d'aucune interpretation :
rem    - une replique donnee au narrateur ;
rem    - une incise seule donnee a un personnage ;
rem    - un texte LU (lettre, acte, testament) donne a un personnage ;
rem    - un locuteur hors casting.
rem
rem  Lecture seule : RIEN n'est ecrit, RIEN n'est facture, aucun
rem  moteur de voix n'est demarre.
rem ============================================================

echo.
echo   ==========================================================
echo    MESURER LE CASTING -- gratuit, lecture seule
echo   ==========================================================
echo.
echo   4 chapitres difficiles, et le compte des erreurs que
echo   l'IA a vraiment faites (celles qui ne se discutent pas).
echo.
echo   A la fin, tu lis un pourcentage :
echo     moins de 1 %% : le casting est bon, le contexte narratif
echo                     n'est pas le probleme ;
echo     plus de 3 %%  : il faudra une lecture humaine de
echo                     reference pour savoir ce qui domine.
echo.
echo   Rien n'est modifie, rien n'est facture.
echo.
pause

python "test_voix\_mesurer_casting_erreurs.py"

echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
