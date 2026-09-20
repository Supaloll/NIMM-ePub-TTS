@echo off
chcp 65001 >nul
title NIMM ePub - ecouter la mesure du debit Pocket TTS
echo.
echo   ==========================================================
echo    TROIS FICHIERS A ECOUTER  (voix Femme001)
echo   ==========================================================
echo.
echo   Le texte lu est celui de Monte-Cristo, en trois longueurs :
echo.
echo     courte_...wav     4 caracteres  (^"Non.^")            0,7 s
echo     moyenne_...wav  125 caracteres                        8,9 s
echo     longue_...wav   295 caracteres                       14,5 s
echo.
echo   Ce qu'il faut juger :
echo     1. la VOIX sonne-t-elle bien (c'est le timbre de Femme001,
echo        un extrait de 12,5 s du domaine public) ?
echo     2. le texte est-il lu SANS mot saute ni parasite ?
echo        ^(le point faible connu du moteur au-dela de ~350 caracteres^)
echo.
echo   Reperes mesures le 20/09/2026 : environ 49 minutes de calcul
echo   pour 1 heure d'audio, et 2,3 Go de memoire au pic.
echo.
echo   Le rapport chiffre complet : sortie_mesure\rapport_mesure.txt
echo.
start "" "%~dp0sortie_mesure"
echo   Le dossier vient de s'ouvrir : double-clique sur un fichier.
echo.
pause
