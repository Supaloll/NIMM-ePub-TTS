# -*- coding: utf-8 -*-
"""CORRIGER LE LOCUTEUR D'UN MORCEAU precis (retour d'ecoute de Laurent).

POURQUOI CET OUTIL (23/09/2026). Retour de Laurent sur Notre-Dame ch.28 : le
morceau « — Ah bah ! » est lu par le NARRATEUR alors que c'est une replique
d'Oudarde. Diagnostic fait (`_diagnostiquer_passage.py`) : le defaut vient de
l'etiquetage d'origine par l'IA, pas de la migration ni du rattrapage — et AUCUNE
regle simple ne le detecte (sur les livres, 147 morceaux commencent par un tiret
et appartiennent au narrateur, dont beaucoup de digressions de l'auteur).

Quand une regle ne sait pas trancher, on corrige a la main — proprement :
  - on cherche le morceau par un EXTRAIT DE TEXTE (pas par un numero : les
    numeros bougent quand le decoupage change) ;
  - on refuse d'ecrire si l'extrait designe plusieurs morceaux (il faut etre plus
    precis) ou si le locuteur demande n'est pas au casting du livre ;
  - avec `--ecrire` : copie datee de la base AVANT, ecriture, controle APRES.

USAGE :
    python test_voix/_corriger_locuteur.py --livre 34 --texte "Ah bah"
    python test_voix/_corriger_locuteur.py --livre 34 --texte "Ah bah" --locuteur Oudarde_Musnier --ecrire
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                          # noqa: E402
from modules.decoupage import (phrases_avec_positions,             # noqa: E402
                               REGLE_ACTUELLE, REGLE_DIALOGUE)

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
LARGEUR = 78


def _arguments():
    options = {'livre': None, 'texte': None, 'locuteur': None, 'ecrire': False,
               'chapitre': None, 'de': None, 'a': None}
    for position, argument in enumerate(sys.argv):
        suivant = sys.argv[position + 1] if position + 1 < len(sys.argv) else ''
        if argument == '--livre':
            options['livre'] = int(suivant)
        elif argument == '--texte':
            options['texte'] = suivant
        elif argument == '--locuteur':
            options['locuteur'] = suivant
        elif argument == '--chapitre':
            options['chapitre'] = int(suivant)
        elif argument == '--de':
            options['de'] = int(suivant)
        elif argument == '--a':
            options['a'] = int(suivant)
        elif argument == '--ecrire':
            options['ecrire'] = True
    return options


def _plage(options):
    """(titre, dialogue, morceaux, casting) pour une PLAGE de morceaux.

    Sert quand une TIRADE entiere est mal attribuee : on corrige les morceaux
    d'un coup, au lieu de les chercher un par un par leur texte.
    """
    conn = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)
    ligne = conn.execute('SELECT title, filename, COALESCE(decoupe_dialogue, 0) '
                         'FROM books WHERE id = ?',
                         (options['livre'],)).fetchone()
    if ligne is None:
        conn.close()
        return None, 'Livre %d inconnu.' % options['livre']
    titre, fichier, dialogue = ligne
    locuteurs = {(ch, idx): sp for ch, idx, sp in conn.execute(
        'SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution '
        'WHERE book_id = ?', (options['livre'],))}
    casting = sorted(r[0] for r in conn.execute(
        'SELECT character_name FROM voices WHERE book_id = ?',
        (options['livre'],)))
    conn.close()
    regle = REGLE_DIALOGUE if dialogue else REGLE_ACTUELLE
    for chapitre in get_chapters(str(BIBLIOTHEQUE / fichier)):
        if chapitre['index'] != options['chapitre']:
            continue
        morceaux = phrases_avec_positions(chapitre.get('text') or '', regle)
        begin = options['de'] if options['de'] is not None else 0
        end = options['a'] if options['a'] is not None else len(morceaux) - 1
        if not (0 <= begin <= end < len(morceaux)):
            return None, ('Plage invalide : le chapitre %d a %d morceaux (0..%d).'
                          % (chapitre['index'], len(morceaux),
                             len(morceaux) - 1))
        return (titre, dialogue,
                [(chapitre['index'], index,
                  locuteurs.get((chapitre['index'], index)), morceaux[index][2])
                 for index in range(begin, end + 1)], casting), None
    return None, 'Chapitre %s introuvable.' % options['chapitre']


def _trouver(options):
    """(titre, dialogue, morceaux, casting) ou (None, message d'erreur)."""
    if options['livre'] is None or not options['texte']:
        return None, 'Precisez --livre <numero> et --texte "<extrait>".'
    conn = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)
    ligne = conn.execute('SELECT title, filename, COALESCE(decoupe_dialogue, 0) '
                         'FROM books WHERE id = ?',
                         (options['livre'],)).fetchone()
    if ligne is None:
        conn.close()
        return None, 'Livre %d inconnu.' % options['livre']
    titre, fichier, dialogue = ligne
    locuteurs = {(ch, idx): sp for ch, idx, sp in conn.execute(
        'SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution '
        'WHERE book_id = ?', (options['livre'],))}
    casting = sorted(r[0] for r in conn.execute(
        'SELECT character_name FROM voices WHERE book_id = ?',
        (options['livre'],)))
    conn.close()
    regle = REGLE_DIALOGUE if dialogue else REGLE_ACTUELLE
    trouve = []
    for chapitre in get_chapters(str(BIBLIOTHEQUE / fichier)):
        if (options['chapitre'] is not None
                and chapitre['index'] != options['chapitre']):
            continue
        morceaux = phrases_avec_positions(chapitre.get('text') or '', regle)
        for index, (_d, _f, morceau) in enumerate(morceaux):
            if options['texte'].lower() in morceau.lower():
                trouve.append((chapitre['index'], index,
                               locuteurs.get((chapitre['index'], index)),
                               morceau.strip()))
    return (titre, dialogue, trouve, casting), None


def main():
    options = _arguments()
    par_plage = options['de'] is not None or options['a'] is not None
    if par_plage:
        if options['chapitre'] is None:
            print('Pour une plage : precisez --chapitre, --de et --a.')
            return 2
        resultat, erreur = _plage(options)
    else:
        resultat, erreur = _trouver(options)
    if erreur:
        print(erreur)
        return 2
    titre, dialogue, trouve, casting = resultat

    print('=' * LARGEUR)
    print(' CORRIGER LE LOCUTEUR D UN MORCEAU')
    print('=' * LARGEUR)
    print('  livre  : %s (id %d), decoupage %s'
          % (titre, options['livre'], 'DIALOGUE' if dialogue else 'origine'))
    if par_plage:
        print('  plage  : chapitre %d, morceaux %s a %s'
              % (options['chapitre'], options['de'], options['a']))
    else:
        print('  extrait cherche : « %s »' % options['texte'])
    print('  morceaux concernes : %d' % len(trouve))
    print('')
    for chapitre, index, locuteur, texte in trouve:
        print('  ch.%-3d #%-4d  locuteur actuel : %-22s  %s'
              % (chapitre, index, locuteur or '(aucun)', texte[:80]))

    if not options['locuteur']:
        print('')
        print('  (pour corriger : ajoutez --locuteur <nom du casting>)')
        print('  personnages du casting : %s' % ', '.join(casting))
        return 0

    print('')
    if not par_plage and len(trouve) != 1:
        print('  REFUS : l extrait designe %d morceaux. Soyez plus precis '
              '(extrait plus long, ou --chapitre).' % len(trouve))
        return 2
    if options['locuteur'] not in casting:
        print('  REFUS : « %s » n est pas au casting de ce livre.'
              % options['locuteur'])
        print('  personnages possibles : %s' % ', '.join(casting))
        return 2

    print('  correction : %d morceaux  ->  %s' % (len(trouve),
                                                  options['locuteur']))
    if not options['ecrire']:
        print('')
        print('  SIMULATION : rien n est ecrit. (pour ecrire : --ecrire)')
        print('=' * LARGEUR)
        return 0

    copie = BASE.with_name(BASE.name + '.bak_avant_correction_'
                           + datetime.now().strftime('%Y%m%d_%H%M'))
    source = sqlite3.connect(str(BASE))
    cible = sqlite3.connect(str(copie))
    with cible:
        source.backup(cible)
    cible.close()
    source.close()
    print('')
    print('  copie datee AVANT d ecrire : %s' % copie.name)

    conn = sqlite3.connect(str(BASE))
    conn.execute('PRAGMA busy_timeout = 20000')
    with conn:
        conn.executemany(
            'UPDATE speaker_attribution SET speaker = ? WHERE book_id = ? '
            'AND chapter_index = ? AND sentence_idx = ?',
            [(options['locuteur'], options['livre'], chapitre, index)
             for chapitre, index, _l, _t in trouve])
        conn.execute(
            'UPDATE voices SET line_count = (SELECT COUNT(*) FROM '
            'speaker_attribution WHERE book_id = voices.book_id AND '
            'speaker = voices.character_name) WHERE book_id = ?',
            (options['livre'],))
    restants = 0
    for chapitre, index, _l, _t in trouve:
        lu = conn.execute('SELECT speaker FROM speaker_attribution WHERE '
                          'book_id = ? AND chapter_index = ? AND '
                          'sentence_idx = ?',
                          (options['livre'], chapitre, index)).fetchone()
        if not lu or lu[0] != options['locuteur']:
            restants += 1
    conn.close()
    print('  ecrit : %d morceaux. relecture : %s'
          % (len(trouve),
             'OK' if not restants else '%d A REGARDER' % restants))
    print('  RETOUR ARRIERE : recopier %s sur data/%s'
          % (copie.name, BASE.name))
    print('  A FAIRE COTE LECTEUR : recharger la page.')
    print('=' * LARGEUR)
    return 0 if not restants else 1


if __name__ == '__main__':
    sys.exit(main())
