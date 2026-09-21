@echo off
chcp 65001 >nul
title NIMM ePub - TOUS LES TESTS
cd /d "%~dp0.."

rem ============================================================
rem  LANCE TOUS LES TESTS (page + serveur), EN UNE FOIS
rem
rem  A quoi ca sert : verifier que RIEN n'a ete casse avant de
rem  livrer une modification. Les tests ne touchent ni a la
rem  bibliotheque, ni a la base, ni aux voix : ils lisent le
rem  code et simulent le reste.
rem
rem  Ce qu'on lit a la fin :  TOUT EST OK, ou la liste des tests
rem  en echec (avec, juste au-dessus, le detail des controles qui
rem  ont echoue).
rem
rem  Rien ne part sur Internet, rien n'est facture, et AUCUN
rem  moteur de voix n'est demarre ni arrete.
rem ============================================================

echo.
echo   ==========================================================
echo    TOUS LES TESTS DE NIMM ePub  ^(page + serveur^)
echo   ==========================================================
echo.
echo   Environ quarante secondes. Rien n'est modifie : les tests
echo   lisent le code et simulent le reste.
echo.
echo   A la fin, tu dois lire :   TOUT EST OK
echo.
pause

python "test_voix\lancer_tous_les_tests.py"

echo.
echo ----------------------------------------------------------
echo  Appuie sur une touche pour fermer cette fenetre.
echo ----------------------------------------------------------
pause >nul
