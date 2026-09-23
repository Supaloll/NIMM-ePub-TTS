@echo off
chcp 65001 >nul
title NIMM ePub - CORRIGER LA VOIX D UN MORCEAU
cd /d "%~dp0.."

rem ============================================================
rem  CORRIGER LA VOIX D UN MORCEAU (retour d'ecoute de Laurent)
rem
rem  Quand un morceau est lu par la mauvaise voix -- une replique
rem  courte lue par le narrateur, par exemple -- on le corrige
rem  ici, morceau par morceau.
rem
rem  On ne cherche PAS par numero (les numeros bougent quand le
rem  decoupage change) : tu donnes un EXTRAIT DU TEXTE que tu as
rem  entendu, l'outil le retrouve et te dit qui le lit aujourd'hui.
rem
rem  Il refuse d'ecrire si l'extrait designe plusieurs morceaux (il
rem  faut etre plus precis) ou si le personnage demande n'est pas au
rem  casting du livre -- et il fait une COPIE DATEE de la base avant
rem  d'ecrire. C'est le retour arriere.
rem
rem  Rien ne part sur Internet, rien n'est facture.
rem ============================================================

echo.
echo   ==========================================================
echo    CORRIGER LA VOIX D UN MORCEAU
echo   ==========================================================
echo.
echo   Tu entends un passage lu par la mauvaise voix :
echo     1. donne le NUMERO du livre (ex. 34) ;
echo     2. donne un EXTRAIT du texte entendu (quelques mots) ;
echo     3. l'outil dit qui le lit aujourd'hui et te propose le
echo        nom exact du personnage a mettre a la place ;
echo     4. tu confirmes, il ecrit -- avec une copie datee de la
echo        base AVANT.
echo.
pause

:debut
echo.
set /p livre="Numero du livre (Entree seule = quitter) : "
if "%livre%"=="" goto fin
echo.
set /p extrait="Extrait du texte entendu : "
if "%extrait%"=="" goto debut

echo.
python "test_voix\_corriger_locuteur.py" --livre %livre% --texte "%extrait%"
echo.
echo ----------------------------------------------------------
echo   Pour corriger : tape le nom EXACT du personnage (il est
echo   dans la liste ci-dessus). Entree seule = ne rien faire.
echo ----------------------------------------------------------
set /p locuteur="Nom du personnage : "
if "%locuteur%"=="" goto apres

echo.
python "test_voix\_corriger_locuteur.py" --livre %livre% --texte "%extrait%" --locuteur "%locuteur%"
echo.
set /p reponse="J'applique ? (O/N) "
if /i not "%reponse%"=="O" goto apres
python "test_voix\_corriger_locuteur.py" --livre %livre% --texte "%extrait%" --locuteur "%locuteur%" --ecrire

:apres
echo.
echo   Rappel : dans le lecteur, RECHARGE la page avant d'ecouter.
echo.
set /p encore="Un autre morceau a corriger ? (O/N) "
if /i "%encore%"=="O" goto debut

:fin
echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
