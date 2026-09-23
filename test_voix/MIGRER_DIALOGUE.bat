@echo off
chcp 65001 >nul
title NIMM ePub - MIGRATION en mode dialogue
cd /d "%~dp0.."

rem ============================================================
rem  MIGRATION EN MODE DIALOGUE -- un livre a la fois
rem
rem  POUR QUI / POURQUOI (23/09/2026). Les livres deja castes
rem  avant le 21/09 ont ete decoupes avec l'ANCIENNE regle : un
rem  morceau qui melange la narration et une replique est lu en
rem  entier par le personnage. Le mode dialogue separe les deux,
rem  MAIS il change les numeros de phrases -- et ces numeros sont
rem  enregistres en base. Sans migration, les voix se decalent.
rem
rem  Cet outil fait les DEUX en une fois, pour un livre :
rem    1. il remappe les numeros de phrases (qui parle) ;
rem    2. il active le mode dialogue du livre.
rem  Les beats (morceaux de narration colles a une replique) sont
rem  remis au NARRATEUR -- sauf ceux qui se trouvent dans une
rem  citation ouverte, qui restent au personnage (lecon de
rem  Lazarille, 21/09/2026).
rem
rem  Ton CASTING ne bouge pas : voix, hauteurs, vitesses, verrous,
rem  alias, voix du narrateur -- jamais touches. Seul le "qui
rem  parle" bouge, et la reprise de lecture est remappee.
rem
rem  Etape 1 : un ESSAI. Rien n'est ecrit, tu lis d'abord.
rem  Etape 2 : si tu tapes O, il APPLIQUE -- avec une COPIE DATEE
rem            de la base AVANT d'ecrire. C'est le retour arriere.
rem
rem  Ne PAS utiliser MODE_DIALOGUE.bat sur ces livres : activer le
rem  mode la-bas, sans migration, decalerait les voix.
rem
rem  Rien ne part sur Internet, rien n'est facture, aucun moteur de
rem  voix n'est demarre ni arrete.
rem ============================================================

echo.
echo   ==========================================================
echo    MIGRATION EN MODE DIALOGUE -- un livre a la fois
echo   ==========================================================
echo.
echo   La narration revient au narrateur, la replique reste au
echo   personnage -- et les numeros de phrases sont remappes pour
echo   que les voix ne se decalent pas.
echo.
echo   Ton casting ne bouge pas (voix, hauteurs, vitesses, verrous).
echo.
echo   Etape 1 : ESSAI -- rien n'est modifie, tu lis d'abord.
echo   Etape 2 : tu tapes O et il APPLIQUE, avec une COPIE DATEE
echo             de la base AVANT d'ecrire.
echo.
pause

:debut
echo.
python "test_voix\_etat_migration_dialogue.py"
echo.
set /p livre="Numero du livre a migrer (Entree seule = quitter) : "
if "%livre%"=="" goto fin

echo.
python "test_voix\_migrer_index_dialogue.py" --livre %livre% --variante B --exemples 21
if errorlevel 1 goto apres

echo.
echo ----------------------------------------------------------
echo   Pour APPLIQUER pour de vrai : tape O puis Entree.
echo   Pour ne rien faire : tape N (ou ferme la fenetre).
echo ----------------------------------------------------------
echo.
set /p reponse="J'applique ? (O/N) "
if /i not "%reponse%"=="O" goto apres

echo.
python "test_voix\_migrer_index_dialogue.py" --livre %livre% --variante B --ecrire

:apres
echo.
echo   Rappel : dans le lecteur, RECHARGE la page avant d'ecouter
echo   (le navigateur garde l'ancien decoupage en memoire).
echo.
set /p encore="Un autre livre ? (O/N) "
if /i "%encore%"=="O" goto debut

:fin
echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
