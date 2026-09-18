# -*- coding: utf-8 -*-
"""Pourquoi certaines incises passent encore ? Les verbes de parole REELS.

Constat de Laurent, 18/09/2026 au soir : « pour les incises, elles sont toujours
presentes ». Le retrait fonctionne pourtant sur ses exemples de banc... donc la
question est : QUELLES incises echappent a la regle, et pourquoi ?

Cet outil repond par les chiffres : il balaie un livre, ramasse toutes les
formes qui RESSEMBLENT a une incise de parole (« , dit-il », « , reprit Morrel, »)
et les classe en trois tas :
  1. RETIREES par le nettoyage du lecteur (`modules/tts.py`) ;
  2. GARDEES parce que le VERBE n'est pas dans la liste de `modules/incises.py`
     (le tas qui explique le constat de Laurent) ;
  3. GARDEES pour une bonne raison (complement apres l'incise, incise non
     fermee, phrase qui n'est QUE l'incise...).

Lecture seule, aucun moteur necessaire.

Usage :
    python test_voix/_diag_incises_reelles.py --livre 16
"""

import argparse
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.decoupage import phrases as _phrases                    # noqa: E402
from modules.incises import VERBES, incises, incises_gardees       # noqa: E402
from modules.tts import _clean_text                                  # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

# Formes qui RESSEMBLENT a une incise, meme si le verbe nous est inconnu :
#   « , mot-il » / « , mot-t-il » (verbe + pronom, TOUJOURS colle par un tiret)
#   « , mot Dupont, » (verbe + nom propre)
# Une incise a pronom prend toujours un trait d'union : l'exiger evite les faux
# positifs (« , et il », « , mais je ») qui noyaient le precedent diagnostic.
MOTIF_LARGE = re.compile(
    r',\s*([a-zà-öø-ÿ\u2019\'\-]+)[-\u2010\u2011\u2012\u2013]t?'
    r'(?:il|elle|on|je|nous|vous|ils|elles)\b'
    r'|,\s*([a-zà-öø-ÿ\u2019\'\-]+)\s+'
    r'(?:(?:M|MM|Mme|Mmes|Mlle|Mlles|Mgr|Dr|Pr)\.\s*)*'
    r'[A-ZÀ-ÖØ-Ý][\w\u00c0-\u00ff\'-]*\s*[,.]')

# Mots-outils qui ne sont PAS des verbes de parole (evite de fausses pistes dans
# le second motif : « , monsieur Dupont, » par exemple).
OUTILS = {'et', 'mais', 'car', 'comme', 'si', 'que', 'quand', 'puisque',
          'dont', 'ou', 'je', 'vous', 'nous', 'il', 'elle', 'on', 'un', 'une',
          'le', 'la', 'les', 'ce', 'c', 'monsieur', 'madame', 'mademoiselle',
          'auquel', 'plus', 'moins', 'alors', 'donc', 'or', 'ni'}


def main():
    analyseur = argparse.ArgumentParser(
        description="Les verbes de parole reels d'un livre.")
    analyseur.add_argument('--livre', type=int, default=16)
    analyseur.add_argument('--exemples', type=int, default=10)
    analyseur.add_argument('--chercher', default=None,
                           help='montrer les phrases qui contiennent ce mot, '
                                'et ce que le nettoyage en fait')
    analyseur.add_argument('--temps', action='store_true',
                           help='mesurer le temps du nettoyage sur tout le livre')
    options = analyseur.parse_args()

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT * FROM books WHERE id = ?',
                         (options.livre,)).fetchone()
    conn.close()
    if livre is None:
        print('Livre %d introuvable.' % options.livre)
        return 1

    from core.epub_parser import get_chapters
    chapitres = get_chapters(str(BIBLIOTHEQUE / livre['filename']))
    phrases = []
    for chapitre in chapitres:
        phrases.extend(_phrases(chapitre.get('text') or ''))

    connus = {v.replace('-il', '').replace("s'", 's\u2019') for v in VERBES}
    connus |= {v for v in VERBES}

    # --- Mode « temps » : le nettoyage est-il vraiment instantane ? --------
    if options.temps:
        import time
        debut = time.perf_counter()
        for phrase in phrases:
            _clean_text(phrase)
        duree = time.perf_counter() - debut
        print('')
        print('  TEMPS DU NETTOYAGE (le code qui retire les incises) :')
        print('    %d phrases en %.3f s  ->  %.2f ms par phrase'
              % (len(phrases), duree,
                 1000.0 * duree / max(len(phrases), 1)))
        print('    soit %.0f phrases par seconde -- sans reseau, sans IA.'
              % (len(phrases) / max(duree, 1e-9)))
        print('')
        return 0

    # --- Mode « montrer un passage » ---------------------------------------
    if options.chercher:
        print('')
        print('  PHRASES DECOUPEES CONTENANT « %s » ET CE QUE LE NETTOYAGE EN FAIT :'
              % options.chercher)
        montres = 0
        for phrase in phrases:
            if options.chercher.lower() not in phrase.lower():
                continue
            retirees = incises(phrase)
            etat = 'RETIREE' if retirees else 'GARDEE '
            print('')
            print('    [%s] phrase envoyee : %s' % (etat, phrase[:150]))
            print('              (longueur %d, fin : ...%s)' % (len(phrase), phrase[-70:]))
            if retirees:
                print('              devient : %s' % _clean_text(phrase)[:150])
                for debut, fin in retirees:
                    print('              incise vue : %r (de %d a %d)'
                          % (phrase[debut:fin][:90], debut, fin))
            gardees = incises_gardees(phrase)
            if gardees:
                print('              incise gardee : « %s » (%s)'
                      % (gardees[0][0][:60], gardees[0][1]))
            montres += 1
            if montres >= 8:
                break
        if not montres:
            print('    (aucune phrase)')
        print('')
        return 0

    # --- Controle de SECURITE : aucune phrase ne doit etre videe ---
    # Une incise bien identifiee fait quelques mots ; si le nettoyage emporte
    # plus de la moitie d'une phrase, c'est le signe qu'on a avale autre chose
    # que l'incise. On le dit, avec des exemples, AVANT de livrer.
    amaigries = []
    incises_seules = []
    for phrase in phrases:
        retirees = incises(phrase)
        if not retirees:
            continue
        # Le garde-fou de `retirer_incises` renvoie la phrase entiere quand le
        # retrait la viderait : on detecte donc le cas AVANT lui, en enlevant
        # les incises ici, a la main.
        texte = phrase
        for debut, fin in sorted(retirees, reverse=True):
            texte = texte[:debut] + ' ' + texte[fin:]
        if not texte.strip(' .,;:!?\u2026\u2014\u00ab\u00bb\""\''):
            incises_seules.append(phrase)
            continue
        nettoyee = _clean_text(phrase)
        if len(phrase) >= 40 and len(nettoyee) < 0.5 * len(phrase):
            amaigries.append((phrase, nettoyee))

    verbes_inconnus = Counter()
    exemples_inconnus = []
    raisons = Counter()
    exemples_gardees = []
    retirees = 0
    gardees_bonnes_raisons = 0
    gardees_verbe_inconnu = 0

    for phrase in phrases:
        formes = [m.group(1) or m.group(2) for m in MOTIF_LARGE.finditer(phrase)]
        if not formes:
            continue
        nettoyee = _clean_text(phrase)
        if incises(phrase):
            retirees += 1
            continue
        gardees = incises_gardees(phrase)
        if gardees:
            gardees_bonnes_raisons += 1
            for _texte, raison in gardees:
                raisons[raison] += 1
            if len(exemples_gardees) < options.exemples:
                exemples_gardees.append((gardees[0][0], gardees[0][1], phrase[:90]))
            continue
        # Rien de detecte : le verbe est-il seulement dans notre liste ?
        inconnu = False
        for forme in formes:
            base = forme.lower().lstrip('\u2019\'')
            if base in OUTILS:
                continue
            if base in connus or ('s\u2019' + base) in connus:
                continue
            inconnu = True
            verbes_inconnus[base] += 1
            if len(exemples_inconnus) < options.exemples:
                exemples_inconnus.append((forme, phrase[:90]))
        if inconnu:
            gardees_verbe_inconnu += 1

    print('')
    print('=' * 78)
    print('LES INCISES REELLES DE %s' % livre['title'][:44])
    print('=' * 78)
    print('  %d phrases analysees' % len(phrases))
    print('')
    print('  incises RETIREES par le nettoyage       : %d' % retirees)
    print('  incises GARDEES pour une bonne raison   : %d' % gardees_bonnes_raisons)
    for raison, nombre in raisons.most_common():
        libelle = ('suivie d\'un complement (« , dit-il en souriant, »)'
                   if raison == 'complement'
                   else 'non fermee (elle coupe la replique en deux)')
        print('      - %-52s %d' % (libelle, nombre))
    if exemples_gardees:
        print('')
        print('  EXEMPLES D INCISES GARDEES VOLONTAIREMENT :')
        for texte, raison, extrait in exemples_gardees:
            print('    « %s » (%s)' % (texte[:44], raison))
            print('      %s' % extrait)
    print('  incises GARDEES car VERBE INCONNU       : %d  <-- a examiner'
          % gardees_verbe_inconnu)

    if verbes_inconnus:
        print('')
        print('  LES VERBES DE PAROLE QUI MANQUENT A LA LISTE :')
        for verbe, nombre in verbes_inconnus.most_common(25):
            print('    %-18s %5d fois' % (verbe, nombre))
        print('')
        print('  EXEMPLES :')
        for forme, extrait in exemples_inconnus:
            print('    « %s »  ->  %s' % (forme, extrait))

    print('')
    print('  CONTROLE DE SECURITE (phrases qui perdent plus de la moitie) : %d'
          % len(amaigries))
    for avant, apres in amaigries[:5]:
        print('    AVANT : %s' % avant[:110])
        print('    APRES : %s' % apres[:110])
    print('')
    print('  PHRASES QUI NE SONT QU UNE INCISE (le decoupage les a isolees, elles')
    print('  sont lues aujourd hui et ne peuvent pas etre retirees) : %d'
          % len(incises_seules))
    for phrase in incises_seules[:8]:
        print('    - %s' % phrase[:100])
    return 0


if __name__ == '__main__':
    sys.exit(main())
