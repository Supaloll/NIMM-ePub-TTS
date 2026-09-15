# -*- coding: utf-8 -*-
"""
Test jetable du FORMAT COMPACT des reponses de l'IA (session du 13/09/2026).
AUCUN appel reseau, AUCUN euro depense.

Ce qui est verifie : la reponse compacte (nom ecrit une seule fois, narration
implicite, uniquement les personnages nouveaux) est bien convertie en
structure interne -- et l'ancien format verbeux reste accepte en secours.

Lancer depuis la racine : python test_voix/test_format_compact.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from modules import voice_casting as vc

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


# ==============================================================
# 1. Le prompt demande bien le format compact
# ==============================================================
print('')
print('--- 1. Prompt ---')
prompt = vc._build_prompt(
    [{'nom': 'Jake', 'genre': 'H', 'age': 'adulte'}],
    [{'id': 0, 'texte': 'Il entra.'}, {'id': 1, 'texte': 'Bonjour, dit Jake.'}]
)
verifier('"repliques"' in prompt, 'le prompt demande le champ "repliques"')
verifier('"nouveaux"' in prompt, 'le prompt demande le champ "nouveaux"')
verifier('"phrases"' not in prompt, 'le prompt ne demande PLUS le champ "phrases" (verbeux)')
verifier('confiance' not in prompt, 'le prompt ne demande plus de champ "confiance" par phrase')
verifier('Jake' in prompt, 'la fiche de personnages est bien fournie')

# ==============================================================
# 2. Conversion du format compact
# ==============================================================
print('')
print('--- 2. Format compact -> structure interne ---')
fiche = [{'nom': 'Jake', 'genre': 'H', 'age': 'adulte'}]
resultat = {
    'nouveaux': [{'nom': 'Sadie', 'genre': 'F', 'age': 'adulte'}],
    'repliques': {'Jake': [1, 2], 'Sadie': [4]},
    'douteux': [2],
}
norm = vc._normaliser_reponse(resultat, fiche, {0, 1, 2, 3, 4, 5})
par_id = {p['id']: p for p in norm['phrases']}

verifier(len(norm['phrases']) == 6, 'les 6 phrases du lot ont toutes un locuteur')
verifier(par_id[0]['locuteur'] == 'narration', 'une phrase absente des listes devient narration')
verifier(par_id[1]['locuteur'] == 'Jake', 'la replique de Jake est bien attribuee')
verifier(par_id[2]['confiance'] == 'basse', 'une phrase listee comme douteuse passe en confiance basse')
verifier(par_id[4]['locuteur'] == 'Sadie', 'la replique de Sadie est bien attribuee')
verifier(par_id[3]['locuteur'] == 'narration', 'la phrase 3, non citee, devient narration')
verifier(len(norm['personnages']) == 2, 'la fiche finale contient l\'ancien + le nouveau personnage')

# ==============================================================
# 3. Securites
# ==============================================================
print('')
print('--- 3. Securites ---')
resultat2 = {
    'nouveaux': [],
    'repliques': {'Jake': [1, 999, 1]},   # 999 n'existe pas, 1 est en double
    'douteux': 'pas une liste',
}
norm2 = vc._normaliser_reponse(resultat2, fiche, {0, 1, 2})
ids = [p['id'] for p in norm2['phrases']]
verifier(999 not in ids, 'un numero INVENTE par l\'IA est ignore')
verifier(ids.count(1) == 1, 'un numero repete n\'est compte qu\'une fois')
verifier(len(norm2['phrases']) == 3, 'le lot reste complet (les autres en narration)')

# ==============================================================
# 4. Ancien format accepte en secours
# ==============================================================
print('')
print('--- 4. Ancien format (secours) ---')
ancien = {
    'personnages': [{'nom': 'Jake', 'genre': 'H', 'age': 'adulte'}],
    'phrases': [{'id': 0, 'locuteur': 'Jake', 'confiance': 'haute', 'anomalie': None}],
}
norm3 = vc._normaliser_reponse(ancien, fiche, {0})
verifier(norm3['phrases'][0]['locuteur'] == 'Jake', 'l\'ancien format passe toujours')

# ==============================================================
# 5. Reponses invalides
# ==============================================================
print('')
print('--- 5. Reponses invalides ---')
for mauvais, libelle in (({'rien': 1}, 'objet sans repliques ni phrases'),
                         ('texte brut', 'texte au lieu d\'un objet')):
    try:
        vc._normaliser_reponse(mauvais, fiche, {0})
        verifier(False, 'une reponse invalide doit lever une erreur (%s)' % libelle)
    except RuntimeError:
        verifier(True, 'une reponse invalide leve bien une erreur claire (%s)' % libelle)

# ==============================================================
# 6. Fusion de fiches (lots coupes)
# ==============================================================
print('')
print('--- 6. Fusion des fiches ---')
f = vc._fusionner_fiches([{'nom': 'Jake'}], [{'nom': 'Jake'}, {'nom': 'Sadie'}])
verifier(len(f) == 2, 'la fusion par nom ne cree pas de doublon')

print('')
print('=' * 60)
print('RESULTAT : %d OK, %d ERR' % (OK, ERR))
print('=' * 60)
sys.exit(1 if ERR else 0)
