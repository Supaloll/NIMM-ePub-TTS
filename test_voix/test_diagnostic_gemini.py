# -*- coding: utf-8 -*-
"""
Test jetable du diagnostic d'un refus de l'IA (session du 13/09/2026).
Aucun appel reseau, aucun euro depense : on rejoue a la main les formes
de reponse que Google peut renvoyer quand il refuse de repondre.

Lancer depuis la racine du projet : python test_voix/test_diagnostic_gemini.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from modules.voice_casting import _expliquer_reponse_gemini, _journaliser_reponse_gemini

OK = 0
ERR = 0


def verifier(condition, message):
    global OK, ERR
    if condition:
        OK += 1
        print('  OK  ' + message)
    else:
        ERR += 1
        print('  ERR ' + message)


# --- 1. Blocage du texte envoye (le cas le plus probable pour le livre 28) ---
blocage = {
    "promptFeedback": {"blockReason": "PROHIBITED_CONTENT"},
    "usageMetadata": {"promptTokenCount": 18000}
}
texte = _expliquer_reponse_gemini(blocage)
print('Cas 1 : ' + texte)
verifier('REFUSE' in texte and 'PROHIBITED_CONTENT' in texte,
         'un blocage de Google est explique en clair, avec son motif')

# --- 2. Liste de reponses vide ---
vide = {"candidates": []}
texte = _expliquer_reponse_gemini(vide)
print('Cas 2 : ' + texte)
verifier('VIDE' in texte, 'une liste de reponses vide est expliquee')

# --- 3. Reponse coupee avant le texte (limite de longueur atteinte) ---
coupe = {"candidates": [{"finishReason": "MAX_TOKENS", "index": 0}]}
texte = _expliquer_reponse_gemini(coupe)
print('Cas 3 : ' + texte)
verifier('MAX_TOKENS' in texte, 'une generation interrompue est expliquee')

# --- 4. Erreur renvoyee dans la reponse ---
erreur = {"error": {"code": 400, "message": "API key not valid"}}
texte = _expliquer_reponse_gemini(erreur)
print('Cas 4 : ' + texte)
verifier('API key not valid' in texte, 'une erreur de Google est remontee telle quelle')

# --- 5. Ecriture du journal (doit etre robuste, jamais bloquante) ---
fichier = RACINE / 'data' / 'journal_erreurs_gemini.log'
# ATTENTION : ce journal est un VRAI outil de diagnostic -- il contient les
# refus reels de Google, qu'il ne faut jamais perdre. Le test met donc son
# contenu de cote et le restaure a l'identique a la fin.
contenu_initial = fichier.read_text(encoding='utf-8') if fichier.exists() else None

chemin = _journaliser_reponse_gemini(blocage, 'motif de test')
print('Cas 5 : journal -> ' + chemin)
verifier(fichier.exists(), 'le journal est bien ecrit sur le disque')
if fichier.exists():
    contenu = fichier.read_text(encoding='utf-8')
    verifier('PROHIBITED_CONTENT' in contenu, 'la reponse brute est bien conservee')
    verifier('motif de test' in contenu, 'la raison est bien conservee')

# --- 6. Robustesse : un contenu inattendu ne doit pas planter ---
texte = _expliquer_reponse_gemini("ce n'est pas un dictionnaire")
print('Cas 6 : ' + texte)
verifier('inattendue' in texte, 'un contenu inattendu est gere sans plantage')

# Nettoyage : on remet le journal EXACTEMENT dans l'etat ou il etait avant le
# test. Il contient les VRAIS refus de Google, utiles au diagnostic : le test
# ne doit jamais les perdre (constat du 13/09/2026, corrige dans la foulee).
if contenu_initial is None:
    if fichier.exists():
        fichier.unlink()
else:
    fichier.write_text(contenu_initial, encoding='utf-8')

print('')
print('=' * 60)
print('RESULTAT : %d OK, %d ERR' % (OK, ERR))
print('=' * 60)
sys.exit(1 if ERR else 0)
