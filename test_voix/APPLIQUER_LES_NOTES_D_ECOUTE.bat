@echo off
chcp 65001 >nul
title NIMM ePub - APPLIQUER LES NOTES D'ECOUTE DES VOIX
cd /d "%~dp0.."

rem ============================================================
rem  APPLIQUER LES NOTES D'ECOUTE (23/09/2026)
rem
rem  A quoi ca sert : la fenetre « Ecouter les voix » range tes
rem  notes (etoiles, genre, age, timbre, debit, accent, registre,
rem  role) dans data\annotations_voix.json -- un fichier LOCAL.
rem  Tant qu'elles ne sont pas REPORTEES, ces notes ne servent
rem  qu'a l'affichage : ni les menus du lecteur, ni le casting
rem  automatique ne les voient.
rem
rem  Cet outil fait le report. Il ne reporte QUE deux choses :
rem    - les ETOILES (0 etoile = voix ECARTEE du casting auto) ;
rem    - le GENRE (H/F de l'ecoute -> M/F des catalogues).
rem  Le reste (age, timbre, debit, accent, registre, role) reste
rem  dans le fichier de notes, ou le casting automatique le lit
rem  directement. La remarque libre n'est pas reportee.
rem
rem  Etape 1 : un ESSAI -- rien n'est ecrit, tu lis les
rem            changements ligne par ligne.
rem  Etape 2 : si tout te va, il APPLIQUE pour de vrai -- avec
rem            une COPIE DATEE de main.py et modules\tts.py AVANT
rem            d'ecrire (.bak_avant_annotations_voix). C'est le
rem            retour arriere.
rem
rem  APRES : relance le lecteur (START.bat) pour que les menus et
rem  le casting voient les nouveaux reglages.
rem
rem  Rien ne part sur Internet, rien n'est facture, aucun moteur
rem  de voix n'est demarre ni arrete.
rem ============================================================

echo.
echo   ==========================================================
echo    APPLIQUER LES NOTES D'ECOUTE DES VOIX
echo    (les etoiles et le genre passent dans les catalogues)
echo   ==========================================================
echo.
echo   Etape 1 : ESSAI. Rien n'est modifie, tu lis d'abord.
echo.

if not exist "data\annotations_voix.json" (
    echo   Aucun fichier de notes : data\annotations_voix.json
    echo   Annote d'abord des voix dans la fenetre « Ecouter les voix ».
    echo.
    echo ----------------------------------------------------------
    echo  Appuie sur une touche pour fermer cette fenetre.
    echo ----------------------------------------------------------
    pause >nul
    exit /b 1
)

python "test_voix\_appliquer_annotations_voix.py"
if errorlevel 1 goto fin

echo.
echo ----------------------------------------------------------
echo   Pour APPLIQUER pour de vrai : tape O puis Entree.
echo   Pour ne rien faire : tape N (ou ferme la fenetre).
echo ----------------------------------------------------------
echo.
set /p reponse="J'applique ? (O/N) "
if /i not "%reponse%"=="O" goto fin

python "test_voix\_appliquer_annotations_voix.py" --ecrire

echo.
echo ----------------------------------------------------------
echo   Controle du pool automatique du casting (rien n'est ecrit) :
echo ----------------------------------------------------------
echo.
python "test_voix\test_pool_casting.py"

echo.
echo   N'oublie pas : relance le lecteur (START.bat) pour que les
echo   menus de voix et le casting voient les nouveaux reglages.

:fin
echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
