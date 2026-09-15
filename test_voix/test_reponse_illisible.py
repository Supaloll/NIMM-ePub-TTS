# -*- coding: utf-8 -*-
"""
Test de la parade aux REPONSES ILLISIBLES (session du 14/09/2026).
AUCUN appel reseau, AUCUN euro depense.

Contexte : un JSON malforme renvoye par DeepSeek a fait echouer TOUT le casting
du tome 5 de Monte-Cristo (15 chapitres traites, puis arret). On verifie ici
que le meme incident est desormais absorbe : nouvel essai du meme lot, puis
decoupage, et attribution au narrateur en dernier recours -- jamais l'arret du
traitement.

Lancer depuis la racine : python test_voix/test_reponse_illisible.py
"""
import sys
import re
import asyncio
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


appels = []
TAILLE_MAX = 4          # au-dela, le faux moteur renvoie un JSON malforme


async def faux_call_llm(prompt, provider='gemini'):
    """Simule DeepSeek : JSON malforme des que le lot depasse TAILLE_MAX
    phrases, et une seule phrase impossible a traiter (contient INTERDIT)."""
    nb = prompt.count('"texte":')
    ids = [int(x) for x in re.findall(r'\{"id": (\d+), "texte":', prompt)]
    appels.append(nb)
    if 'INTERDIT' in prompt:
        raise vc.ReponseIllisible('simulation : JSON malforme (phrase piegee)')
    if nb > TAILLE_MAX:
        # Cas reel du 14/09/2026 (Notre-Dame de Paris, chapitre 31) : la
        # reponse est un JSON VALIDE mais sans 'repliques' ni 'phrases'. C'est
        # _normaliser_reponse qui doit la rejeter, et la parade doit la
        # rattraper comme une reponse illisible.
        return {'personnages': []}
    return {
        'personnages': [{'nom': 'Testeur', 'genre': 'H', 'age': 'adulte'}],
        'repliques': {'Testeur': ids},
    }


vc._call_llm = faux_call_llm

# ==============================================================
# 1. Un JSON malforme n'arrete plus le chapitre
# ==============================================================
print('')
print('--- 1. JSON malforme : reessai puis decoupage, sans arret ---')
TEXTE = ' '.join(['Phrase %d du recit.' % i for i in range(20)])
res = asyncio.run(vc.analyze_chapter(TEXTE, []))
print('     appels simules : %d' % len(appels))
verifier(len(res['phrases']) == 20, 'les 20 phrases ont un locuteur (le chapitre est complet)')
verifier(all(p['locuteur'] == 'Testeur' for p in res['phrases']),
         'malgre les JSON malformes, tout a fini par etre attribue')
verifier(len(appels) > 3, 'des nouvels essais ET des decoupages ont eu lieu')

# ==============================================================
# 2. Une phrase impossible a traiter passe au narrateur
# ==============================================================
print('')
print('--- 2. Phrase impossible : narrateur, avec la raison ---')
appels.clear()
mots = ['Phrase %d du recit.' % i for i in range(20)]
mots[5] = 'Cette phrase INTERDIT resiste a tout.'
res2 = asyncio.run(vc.analyze_chapter(' '.join(mots), []))
par_id = {p['id']: p for p in res2['phrases']}
print('     appels simules : %d' % len(appels))
verifier(len(res2['phrases']) == 20, 'le chapitre reste complet')
verifier(par_id[5]['locuteur'] == 'narration', 'la phrase resistante revient au narrateur')
verifier('non attribuable' in (par_id[5]['anomalie'] or ''),
         'la raison est inscrite dans la fiche')
verifier(par_id[4]['locuteur'] == 'Testeur', 'les phrases voisines sont bien attribuees')

print('')
print('=' * 60)
print('RESULTAT : %d OK, %d ERR' % (OK, ERR))
print('=' * 60)
sys.exit(1 if ERR else 0)
