# -*- coding: utf-8 -*-
"""Les INCISES de parole sont-elles supprimables ? Mesure, pas opinion.

Idée de Laurent (18/09/2026) : avec un casting multi-voix, les incises
(« — Il partit, dit-il. ») sont largement inutiles — la voix dit déjà qui
parle — et elles coupent le débit de la réplique. Il a proposé de les retirer.

Cet outil répond par des chiffres, en trois temps :
  1. COMBIEN : quelle part des phrases contient une incise, et de quel type ;
  2. LES PIÈGES : les cas où une suppression naïve abîmerait le texte
     (verbe plein, incise suivie d'un complément, « M. » abrégé...) ;
  3. LE CODE PROPOSÉ, ESSAYÉ : une règle reçue ailleurs est appliquée à de
     vraies phrases, et on COMPTE les dégâts (mots supprimés à tort).

Rappel de la méthode de l'atelier : une mesure ne remplace pas l'oreille.
Aucun fichier n'est modifié, aucun moteur n'est nécessaire.

Usage :
    python test_voix/_mesurer_incises_supprimables.py --livre 16
    python test_voix/_mesurer_incises_supprimables.py --livre 16 --exemples 12
"""

import argparse
import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

from modules.decoupage import phrases as _phrases                    # noqa: E402

# Les verbes de parole : ce sont eux qui trahissent une incise.
VERBES = ('dit', 'dis', 'dit-il', 'répondit', 'repondit', 'répliqua', 'repliqua',
          's\'écria', 's\'ecria', 'écria', 'ecria', 'demanda', 'reprit', 'ajouta',
          'murmura', 'fit', 'poursuivit', 'continua', 's\'exclama', 's\'exclama',
          'prononça', 'prononca', 'hasarda', 'observa', 'remarqua', 'interrompit',
          'balbutia', 'soupira', 'grommela')

# Les traits d'union possibles dans « dit-il » (clavier, typographique, insécable)
TIRETS = '\u002d\u2010\u2011\u2012\u2013'

# --- 1. La règle PRUDENTE (celle qu'on pourrait adopter) -------------------
# Une incise à PRONOM : « , dit-il, » « , s'écria-t-elle, ». Le \b devant le
# verbe est indispensable : sans lui, « maudit-il » ou « interdit-il »
# seraient pris pour « dit-il ».
MOTIF_PRONOM = re.compile(
    r'[,—]\s*\b(?:%s)[%s\s]?(?:il|elle|on|je|nous|vous|ils|elles)\b\s*,?'
    % ('|'.join(v.replace('-il', '') for v in VERBES), TIRETS))

# Une incise à NOM PROPRE, encadrée par des virgules : « , dit Beauchamp, ».
# Le nom peut être une civilité abrégée (« M. Morrel »), d'où le (?:\w\.\s*)*.
MOTIF_NOM = re.compile(
    r',\s*(?:%s)\s+(?:(?:M|MM|Mme|Mmes|Mlle|Mlles|Mgr|Dr|Pr)\.\s*)*'
    r'[A-ZÀ-ÖØ-Ý][\w\u00c0-\u00ff\'-]*\s*,'
    % '|'.join(v for v in VERBES if '-' not in v))

# L'incise suivie d'un COMPLÉMENT est un vrai piège : « , dit-il en souriant, ».
DEBUT_COMPLEMENT = re.compile(
    r"^(?:en\s|d[\u2019']un[e]?\s|à\s|au\s|avec\s|sans\s|tout\s|comme\s"
    r"|paraissant|souriant|pleurant|haussant|baissant|serrant|tendant|reprenant)",
    re.IGNORECASE)

# --- 2. Le code PROPOSÉ ailleurs (tel quel, pour mesurer) -----------------
PROPOSE = [
    r",?\s*—?\s*(dit|répondit|répliqua|s\'écria|demanda|reprit|ajouta)\s+-[a-z]+,?",
    r",?\s*—?\s*(dit|répondit|répliqua|s\'écria|demanda|reprit|ajouta)\s+[A-Z][a-zA-Zà-ÿ]+,?",
    r",?\s*(dit|répondit|répliqua|s\'écria|demanda|reprit|ajouta)\s+[A-Z][a-zA-Zà-ÿ]+\s*\.",
]


def _supprimer_propose(texte):
    """Le code proposé AILLEURS, recopié tel quel (pour le mesurer, pas l'adopter)."""
    for motif in PROPOSE:
        texte = re.sub(motif, '', texte, flags=re.IGNORECASE)
    return texte.strip()


def etudier(phrases):
    """Bilan chiffré sur une liste de phrases."""
    bilan = {
        'phrases': len(phrases), 'avec_incise': 0, 'pronom': 0, 'nom': 0,
        'caracteres_retires': 0, 'exemples': [], 'pieges': [],
        'propose_touche': 0, 'propose_a_tort': 0, 'exemples_degats': [],
    }
    for phrase in phrases:
        trouves = []
        for motif, nom in ((MOTIF_PRONOM, 'pronom'), (MOTIF_NOM, 'nom')):
            for m in motif.finditer(phrase):
                trouves.append((nom, m.group(0)))
        if trouves:
            bilan['avec_incise'] += 1
            for nom, incise in trouves:
                bilan[nom] += 1
                bilan['caracteres_retires'] += len(incise)
            if len(bilan['exemples']) < 60:
                bilan['exemples'].append((phrase, trouves))
            # Piège : l'incise est suivie d'un COMPLÉMENT (« , dit-il en
            # souriant, ») — le retirer laisserait « en souriant » tout seul.
            # Une simple suite de réplique (« , dit Barrois, que je meurs de
            # soif ») n'est PAS un piège : la phrase redevient correcte.
            for _nom, incise in trouves:
                reste = phrase.split(incise, 1)[-1].strip()
                if reste and DEBUT_COMPLEMENT.match(reste):
                    bilan['pieges'].append((phrase, incise, reste[:60]))
        # Le code proposé, essayé sur la MÊME phrase
        essai = _supprimer_propose(phrase)
        if essai != phrase:
            bilan['propose_touche'] += 1
            if not trouves:
                bilan['propose_a_tort'] += 1
                if len(bilan['exemples_degats']) < 60:
                    bilan['exemples_degats'].append((phrase, essai))
    return bilan




def main():
    analyseur = argparse.ArgumentParser(
        description='Mesure ce que donnerait la suppression des incises.')
    analyseur.add_argument('--livre', type=int, default=None,
                           help='identifiant du livre (defaut : tous les livres castes)')
    analyseur.add_argument('--exemples', type=int, default=6,
                           help="nombre d exemples a afficher par categorie")
    options = analyseur.parse_args()

    from core.epub_parser import get_chapters

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    if options.livre:
        livres = conn.execute('SELECT * FROM books WHERE id = ?',
                              (options.livre,)).fetchall()
    else:
        livres = [r for r in conn.execute(
            'SELECT DISTINCT b.* FROM books b JOIN speaker_attribution s '
            'ON s.book_id = b.id ORDER BY b.id')]

    print('')
    print('=' * 82)
    print('LES INCISES DE PAROLE : COMBIEN, LESQUELLES, ET CE QUE FERAIT LE CODE PROPOSE')
    print('=' * 82)

    total = {'phrases': 0, 'avec_incise': 0, 'pronom': 0, 'nom': 0,
             'caracteres_retires': 0, 'propose_touche': 0, 'propose_a_tort': 0,
             'caracteres_totaux': 0}
    montres, degats_montres, pieges_montres = 0, 0, 0

    for livre in livres:
        chemin = BIBLIOTHEQUE / livre['filename']
        if not chemin.is_file():
            continue
        phrases = []
        for chapitre in get_chapters(str(chemin)):
            phrases.extend(_phrases(chapitre.get('text') or ''))
        bilan = etudier(phrases)
        part = 100.0 * bilan['avec_incise'] / max(bilan['phrases'], 1)
        print('')
        print('  %s' % livre['title'][:62])
        print('    phrases                : %d' % bilan['phrases'])
        print('    phrases avec incise    : %d  (%.2f %%)'
              % (bilan['avec_incise'], part))
        print('    dont pronom / nom      : %d / %d'
              % (bilan['pronom'], bilan['nom']))
        print('    caracteres retires     : %d' % bilan['caracteres_retires'])

        for cle in ('phrases', 'avec_incise', 'pronom', 'nom',
                    'caracteres_retires', 'propose_touche', 'propose_a_tort'):
            total[cle] += bilan[cle]
        total['caracteres_totaux'] += sum(len(p) for p in phrases)

        if montres < options.exemples:
            print('')
            print('    EXEMPLES D INCISES TROUVEES :')
            for phrase, trouves in bilan['exemples']:
                if montres >= options.exemples:
                    break
                print('      %s' % phrase[:110])
                print('        -> %s' % ' | '.join(i for _n, i in trouves)[:100])
                montres += 1
        if pieges_montres < options.exemples:
            for phrase, incise, reste in bilan['pieges']:
                if pieges_montres >= options.exemples:
                    break
                print('')
                print('    PIEGE (du texte reste APRES l incise) :')
                print('      %s' % phrase[:110])
                print('      incise : %-40s  reste : %s' % (incise[:40], reste))
                pieges_montres += 1
        if degats_montres < options.exemples:
            for avant, apres in bilan['exemples_degats']:
                if degats_montres >= options.exemples:
                    break
                print('')
                print('    LE CODE PROPOSE ABIME CETTE PHRASE :')
                print('      avant : %s' % avant[:110])
                print('      apres : %s' % apres[:110])
                degats_montres += 1

    print('')
    print('=' * 82)
    print('BILAN')
    print('=' * 82)
    part = 100.0 * total['avec_incise'] / max(total['phrases'], 1)
    print('  %d phrases analysees : %d avec incise (%.2f %%)'
          % (total['phrases'], total['avec_incise'], part))
    print('  %d caracteres d incise sur %d caracteres lus (%.2f %% du texte)'
          % (total['caracteres_retires'], total['caracteres_totaux'],
             100.0 * total['caracteres_retires'] / max(total['caracteres_totaux'], 1)))
    print('  CODE PROPOSE AILLEURS : il touche %d phrases, dont %d SANS incise'
          % (total['propose_touche'], total['propose_a_tort']))
    if total['propose_touche']:
        print('     soit %.0f %% de ses retouches qui abiment le texte'
              % (100.0 * total['propose_a_tort'] / total['propose_touche']))
    print('')
    print('  RAPPEL : ceci MESURE. Reste a ecouter avant d adopter quoi que ce soit.')
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
