@echo off
chcp 65001 >nul
title NIMM ePub - PETITS ROLES : Jessica et Pierre
cd /d "%~dp0.."

rem ============================================================
rem  PETITS ROLES : une voix par genre (Jessica et Pierre)
rem
rem  Decision de Laurent du 21/09/2026 : tout personnage de
rem  MOINS de 8 repliques est joue par une voix generique selon
rem  son genre -- Jessica (femmes), Pierre (hommes), en Piper.
rem
rem  Cet outil applique la decision aux livres DEJA CASTES :
rem  la voix generique du genre, PLUS une VARIANTE de hauteur et
rem  de vitesse propre a chaque petit role (11 hauteurs x 13
rem  vitesses = 143 variantes par voix), pour que deux petits
rem  roles d'un meme livre ne se ressemblent pas.
rem
rem  Il ne touche a RIEN d'autre : ni aux roles principaux, ni
rem  aux lignes VERROUILLEES (un verrou = « je garde »).
rem
rem  Etape 1 : un ESSAI -- rien n'est ecrit, tu lis ce qu'il
rem            ferait, livre par livre.
rem  Etape 2 : si tout te va, il APPLIQUE pour de vrai -- et il
rem            fait une COPIE DATEE de la base AVANT d'ecrire.
rem            C'est le retour arriere.
rem
rem  Rien ne part sur Internet, rien n'est facture, aucun moteur
rem  de voix n'est demarre ni arrete.
rem ============================================================

echo.
echo   ==========================================================
echo    PETITS ROLES : Jessica (femmes) / Pierre (hommes)
echo    et une VARIANTE de hauteur + vitesse pour chacun
echo   ==========================================================
echo.
echo   11 hauteurs x 13 vitesses = 143 variantes par voix :
echo   deux petits roles d'un meme livre ne se ressemblent pas.
echo.
echo   Etape 1 : ESSAI. Rien n'est modifie, tu lis d'abord.
echo.
pause

python "test_voix\migrer_petits_roles.py"
if errorlevel 1 goto fin

echo.
echo ----------------------------------------------------------
echo   Pour APPLIQUER pour de vrai : tape O puis Entree.
echo   Pour ne rien faire : tape N (ou ferme la fenetre).
echo ----------------------------------------------------------
echo.
set /p reponse="J'applique ? (O/N) "
if /i not "%reponse%"=="O" goto fin

python "test_voix\migrer_petits_roles.py" --appliquer

:fin
echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
