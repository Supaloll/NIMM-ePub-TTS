@echo off
chcp 65001 >nul
title NIMM ePub - MODE DIALOGUE par livre
cd /d "%~dp0.."

rem ============================================================
rem  MODE DIALOGUE : la narration separee des repliques
rem
rem  Dans un morceau qui colle une narration et une replique
rem  (« Richie est intervenu : «Non, c'est pas ca. » »), le beat
rem  revient au NARRATEUR et la replique au PERSONNAGE.
rem
rem  Ce reglage s'applique LIVRE PAR LIVRE, et jamais tout seul :
rem  les livres non marques gardent le decoupage d'origine.
rem
rem  IMPORTANT : pour un livre DEJA caste, changer le decoupage
rem  decale les numeros de phrases enregistres. Il faut donc le
rem  RE-CASTER pour que les voix suivent.
rem
rem  Ce lanceur affiche la liste, puis demande le numero du livre
rem  et ce qu'on veut faire. Copie datee de la base avant d'ecrire.
rem ============================================================

echo.
echo   ==========================================================
echo    MODE DIALOGUE : narrateur / personnages bien separes
echo   ==========================================================
echo.
python "test_voix\regler_mode_dialogue.py"
if errorlevel 1 goto fin

echo.
set /p numero="Numero du livre (Entree pour ne rien faire) : "
if "%numero%"=="" goto fin

echo.
echo   Tape A pour ACTIVER le mode dialogue, D pour revenir au
echo   decoupage d'origine.
echo.
set /p action="A ou D ? "
if /i "%action%"=="A" goto activer
if /i "%action%"=="D" goto desactiver
goto fin

:activer
python "test_voix\regler_mode_dialogue.py" --livre %numero% --activer
goto fin

:desactiver
python "test_voix\regler_mode_dialogue.py" --livre %numero% --desactiver

:fin
echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
