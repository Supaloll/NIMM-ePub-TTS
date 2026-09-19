@echo off
rem Ouvre le document des REGLES D'INCISES, pret a etre copie-colle dans un
rem autre assistant (LLM) pour qu'il cherche a contourner les regles.
rem Fait le 19/09/2026, idee de Laurent.
rem
rem Ce document ne modifie RIEN : il se contente d'ouvrir le texte.

setlocal
set FICHIER=%~dp0REGLES_INCISES_a_eprouver.md

if not exist "%FICHIER%" (
    echo.
    echo  ERREUR : le document est introuvable :
    echo    %FICHIER%
    echo.
    pause
    exit /b 1
)

echo.
echo  Ouverture du document des regles d'incises...
echo.
echo  Dans le Bloc-notes : Ctrl+A puis Ctrl+C pour tout copier,
echo  et collez-le dans l'autre assistant.
echo.
echo  Appuyez sur une touche pour l'ouvrir...
pause > nul

start "" notepad "%FICHIER%"
endlocal
