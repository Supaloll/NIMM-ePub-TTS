@echo off
chcp 65001 >nul
title ATTENTION - ce lanceur DEPENSE de l'argent (API payantes)
cd /d "%~dp0"

rem ============================================================
rem  ATTENTION : cet outil envoie un chapitre aux API d'IA
rem  (Gemini, Mistral, DeepSeek) et chaque appel est FACTURE
rem  sur la cle de Laurent.
rem
rem  Ce n'est PAS un test de non-regression : c'est l'outil
rem  d'atelier qui a servi a comparer les modeles les 12 et
rem  13/09/2026. Il a ete renomme et protege le 16/09/2026 :
rem  avant, un simple double-clic suffisait a le faire partir.
rem
rem  Pour verifier le projet sans rien payer : les scripts
rem  « test_*.py » du dossier (aucune API, aucun moteur) --
rem  liste dans test_voix\LIRE_MOI.md.
rem ============================================================

echo.
echo  ============================================================
echo   ATTENTION : cet outil appelle de VRAIES API PAYANTES.
echo   Chaque appel est FACTURE sur ta cle (Gemini, Mistral,
echo   DeepSeek). Ce n'est pas un test du projet.
echo  ============================================================
echo.

choice /c ON /n /m "  Lancer quand meme (donc payer) ? [O = oui, N = non] "
if errorlevel 2 goto fin

python _PAYANT_test_attribution_api.py --je-paie

:fin
echo.
pause
