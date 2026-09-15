# -*- coding: utf-8 -*-
"""
Test jetable du contournement des filtres de l'IA (session du 13/09/2026).
AUCUN appel reseau, AUCUN euro depense : on remplace l'appel a l'IA par une
simulation qui refuse exactement comme Google l'a fait (BlocageContenu).

On verifie les deux parades :
  1. un lot trop gros est coupe en deux jusqu'a passer ;
  2. une phrase que le filtre refuse TOUJOURS, meme seule, est attribuee au
     narrateur avec une raison explicite -- le chapitre reste complet.

Lancer depuis la racine : python test_voix/test_anti_blocage.py
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
appels_ok = []               # tailles des lots que le "filtre" a acceptes
TAILLE_MAX_ACCEPTEE = 4      # au-dela, le "filtre" refuse (comme Google)


async def faux_call_llm(prompt, provider='gemini'):
    """Simule l'IA : refuse les gros lots, et refuse toute phrase piegee.

    Attention : le prompt contient un EXEMPLE de reponse JSON qui inclut
    lui aussi "id" et "locuteur" -- on compte donc les phrases sur le
    marqueur '"texte":' et on extrait les ids avec le motif complet
    {"id": N, "texte":, pour ne jamais confondre l'exemple et les vraies
    phrases envoyees.
    """
    nb_phrases = prompt.count('"texte":')
    ids = [int(x) for x in re.findall(r'\{"id": (\d+), "texte":', prompt)]
    appels.append(nb_phrases)
    if 'INTERDIT' in prompt:
        raise vc.BlocageContenu('simulation : filtre de securite (phrase piegee)')
    if nb_phrases > TAILLE_MAX_ACCEPTEE:
        raise vc.BlocageContenu('simulation : filtre de securite (lot trop gros)')
    appels_ok.append(nb_phrases)
    return {
        'personnages': [{'nom': 'Testeur', 'genre': 'H', 'age': 'adulte'}],
        'phrases': [{'id': i, 'locuteur': 'Testeur', 'confiance': 'haute', 'anomalie': None}
                    for i in ids]
    }


vc._call_llm = faux_call_llm

# ==============================================================
# 1. Lot trop gros : doit etre coupe en deux jusqu'a passer
# ==============================================================
print('')
print('--- 1. Un lot refuse est coupe en deux jusqu a passer ---')
appels.clear()
appels_ok.clear()
TEXTE = ' '.join(['Phrase %d du recit.' % i for i in range(20)])
res = asyncio.run(vc.analyze_chapter(TEXTE, []))
print('     appels IA simules : %d' % len(appels))
verifier(len(res['phrases']) == 20, 'les 20 phrases ont toutes un locuteur')
verifier(all(p['locuteur'] == 'Testeur' for p in res['phrases']),
         'toutes les phrases ont ete attribuees malgre les refus')
verifier(len(appels) > 1, 'le decoupage a bien eu lieu (plusieurs appels)')
verifier(max(appels_ok) <= TAILLE_MAX_ACCEPTEE,
         'aucun appel ACCEPTE ne depassait la taille que le filtre tolere')
verifier(res['personnages'][0]['nom'] == 'Testeur', 'la fiche remontee est conservee')

# ==============================================================
# 2. Phrase impossible a faire passer : narrateur + raison explicite
# ==============================================================
print('')
print('--- 2. Une phrase toujours refusee passe au narrateur, avec la raison ---')
appels.clear()
appels_ok.clear()
mots = ['Phrase %d du recit.' % i for i in range(20)]
mots[5] = 'Cette phrase INTERDIT doit etre refusee.'
TEXTE2 = ' '.join(mots)
res2 = asyncio.run(vc.analyze_chapter(TEXTE2, []))
print('     appels IA simules : %d' % len(appels))
par_id = {p['id']: p for p in res2['phrases']}
verifier(len(res2['phrases']) == 20, 'le chapitre reste complet (20 phrases)')
verifier(par_id[5]['locuteur'] == 'narration', 'la phrase refusee revient au narrateur')
verifier('non attribuable' in (par_id[5]['anomalie'] or ''),
         'la raison exacte est inscrite dans la fiche (anomalie explicite)')
verifier(par_id[4]['locuteur'] == 'Testeur',
         'les phrases voisines, elles, sont bien analysees')

# ==============================================================
# 3. Reprise du texte : la reponse d'un lot coupe ne perd rien
# ==============================================================
print('')
print('--- 3. Aucune phrase perdue, meme avec un filtre tres strict ---')
appels.clear()
appels_ok.clear()
TAILLE_MAX_ACCEPTEE = 1      # le filtre ne tolere qu'une phrase a la fois
res3 = asyncio.run(vc.analyze_chapter(TEXTE, []))
attribuees = [p for p in res3['phrases'] if p['locuteur'] == 'Testeur']
print('     appels IA simules : %d pour 20 phrases' % len(appels))
verifier(len(attribuees) == 20, 'les 20 phrases sont attribuees une par une')
verifier(max(appels_ok) == 1, 'chaque envoi ACCEPTE ne contenait qu une seule phrase')

print('')
print('=' * 60)
print('RESULTAT : %d OK, %d ERR' % (OK, ERR))
print('=' * 60)
sys.exit(1 if ERR else 0)
