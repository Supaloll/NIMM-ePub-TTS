# -*- coding: utf-8 -*-
"""CHOISIR UN LIVRE DE TEST pour la nouvelle regle de decoupage (21/09/2026).

Demande de Laurent : essayer le decoupage « narration / dialogue » sur un livre
NEUF, pour ne rien casser dans les livres deja castes. Ce script parcourt un
dossier d'EPUB, mesure chaque candidat et les classe.

Ce qu'il mesure, par livre :
    - la taille (un livre COURT = un essai pas cher) ;
    - le nombre de morceaux de phrase (regle ACTUELLE) ;
    - les morceaux de type A (beat + replique : la narration qui parle avec la
      voix d'un personnage -- ce que la nouvelle regle coupe) ;
    - les morceaux de type B (citation racontee : a ne PAS toucher) ;
    - le prix estime d'un casting complet (estimation du projet, sans appel).

LECTURE SEULE : aucun fichier n'est modifie, aucun appel facture.

Usage :
    python _choisir_livre_test.py                      (dossier par defaut)
    python _choisir_livre_test.py "D:\\Livres Epub" 60   (dossier + nb maxi)
"""
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage, voice_casting

DOSSIER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r'D:\Livres Epub')
MAXI = int(sys.argv[2]) if len(sys.argv) > 2 else 60

# Bornes de taille : sous 10 Ko ce sont des notes ou des extraits ; au-dela de
# 800 Ko ce n'est plus un « petit essai ».
MIN_KO, MAX_KO = 10, 800
# Un texte de moins de 9 000 caracteres n'a pas assez de dialogues pour prouver
# quoi que ce soit, et on accepte les livres a chapitre unique (nouvelles).
MIN_CARACTERES = 9000
MIN_CHAPITRES = 1
MIN_CAS_A = 15

# Le discriminant retenu (variante V3, mesuree sur « 22/11/63 ») : le texte
# AVANT le « finit par deux-points ET contient un verbe de parole.
VERBES_LARGES = re.compile(
    r"\b(dit|dis|répond|repond|demand|s'écri|s'ecri|murmur|ajout|reprit|"
    r"soupir|grommel|poursuiv|observ|reprenn|répét|repet|cria|appela|"
    r"expliqu|avou|annonc|annonç|protest|conclut|lança|lanca|hasarda|"
    r"marmonna|bougonna|rican|s'exclam|interv|interven|enchain|enchaîn|"
    r"renchér|rench|rispost|gliss|souffl|lâch|rétorqu|retorqu|object|"
    r"précisa|precisa|précis|precis)", re.IGNORECASE)
RE_FIN_COLON = re.compile(r':\s*$')


def _mesure(texte):
    """(morceaux, type A, type B) pour un texte de chapitre."""
    morceaux = decoupage.phrases(texte)
    a = b = 0
    for phrase in morceaux:
        debut = phrase.find('«')
        if debut <= 0:
            continue
        avant = phrase[:debut].strip()
        if not avant.strip(' :;,.-—'):
            continue
        if phrase.count('«') == phrase.count('»'):
            b += 1
            continue
        if RE_FIN_COLON.search(avant) and VERBES_LARGES.search(avant):
            a += 1
        else:
            b += 1
    return morceaux, a, b


def main():
    print('=' * 78)
    print(' LIVRES CANDIDATS pour l essai (dossier : %s)' % DOSSIER)
    print('=' * 78)
    fichiers = [f for f in DOSSIER.rglob('*.epub') if f.is_file()]
    fichiers = [f for f in fichiers
                if MIN_KO * 1024 <= f.stat().st_size <= MAX_KO * 1024]
    fichiers.sort(key=lambda f: f.stat().st_size)
    fichiers = fichiers[:MAXI]
    print('   %d livre(s) examines (entre %d et %d Ko)' % (len(fichiers),
                                                           MIN_KO, MAX_KO))

    resultats = []
    for chemin in fichiers:
        try:
            chapitres = epub_parser.get_chapters(str(chemin))
        except Exception:                       # EPUB illisible : on passe
            continue
        textes = [c.get('text') or '' for c in chapitres]
        total = sum(len(t) for t in textes)
        if total < MIN_CARACTERES or len(chapitres) < MIN_CHAPITRES:
            continue
        morceaux = a = b = 0
        for t in textes:
            m, ta, tb = _mesure(t)
            morceaux += len(m)
            a += ta
            b += tb
        cout = voice_casting.estimate_cast_cost(textes, 'gemini')
        resultats.append({
            'nom': chemin.name,
            'ko': round(chemin.stat().st_size / 1024),
            'chapitres': len(chapitres),
            'caracteres': total,
            'morceaux': morceaux,
            'a': a,
            'b': b,
            'prix': cout['cost_usd_max'],
            'dollars': cout['cost_usd'],
        })

    # Classement : les livres les plus DENSES en cas a corriger, a taille
    # raisonnable. On demande au moins 20 cas (sinon l'essai ne prouve rien).
    resultats = [r for r in resultats if r['a'] >= MIN_CAS_A]
    resultats.sort(key=lambda r: -(r['a'] / max(1, r['caracteres']) * 10000))
    print('')
    print('%-46s %5s %4s %8s %7s %5s %5s %7s'
          % ('Livre', 'Ko', 'chap', 'signes', 'morc.', 'A', 'B', 'prix $'))
    for r in resultats[:15]:
        print('%-46s %5d %4d %8d %7d %5d %5d %7.2f'
              % (r['nom'][:46], r['ko'], r['chapitres'], r['caracteres'],
                 r['morceaux'], r['a'], r['b'], r['prix']))
    print('')
    print('   A = morceaux « beat + replique » (la narration lue par un '
          'personnage : ce que la nouvelle regle corrige)')
    print('   B = citations racontees (a laisser telles quelles)')
    print('   prix $ = estimation d un casting complet (calibree sur facture)')

    # Exemples concrets dans le candidat le mieux classe : Laurent doit voir
    # ce qui changerait, pas seulement un chiffre.
    if resultats:
        meilleur = resultats[0]
        chemin = next(f for f in fichiers if f.name == meilleur['nom'])
        print('')
        print('   Exemples de cas A dans « %s » :' % meilleur['nom'])
        montres = 0
        for chapitre in epub_parser.get_chapters(str(chemin)):
            for phrase in decoupage.phrases(chapitre.get('text') or ''):
                debut = phrase.find('«')
                if debut <= 0:
                    continue
                avant = phrase[:debut].strip()
                if (phrase.count('«') != phrase.count('»')
                        and RE_FIN_COLON.search(avant)
                        and VERBES_LARGES.search(avant)):
                    print('      - %s' % avant[:70])
                    print('        -> coupe : le beat revient au narrateur')
                    montres += 1
                    if montres >= 6:
                        break
            if montres >= 6:
                break


if __name__ == '__main__':
    main()
