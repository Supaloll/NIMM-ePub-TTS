# -*- coding: utf-8 -*-
"""Simulation de la migration "mode dialogue" sur TOUS les livres concernes.

POURQUOI CET OUTIL (23/09/2026). La migration se fait livre par livre, et un
livre peut prendre du temps a decouper : lancer les dix a la main, un par un,
fait expirer les commandes. Cet outil enchaine donc les simulations (RIEN N EST
ECRIT : il ne passe jamais `--ecrire`) et range chaque rapport dans `_essais/`,
avec un resume global a la fin.

Il ne fait que piloter l'outil de reference : `_migrer_index_dialogue.py`.

Usage : python test_voix/_simuler_migration_dialogue.py
        python test_voix/_simuler_migration_dialogue.py --livres 34 18 --exemples 20
"""

import argparse
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
OUTIL = Path(__file__).resolve().parent / '_migrer_index_dialogue.py'
SORTIE = RACINE / '_essais'
LARGEUR = 78

MOTIFS = {
    'avant': re.compile(r'phrases avant / apres\s*:\s*(\d+)\s*/\s*(\d+)'),
    'beats': re.compile(r'beats detectes\s*:\s*(\d+)'),
    'narrateur': re.compile(r'remis au narrateur\s*:\s*(\d+)'),
    'refuses': re.compile(r'refuses \(citation ouverte\)\s*:\s*(\d+)'),
    'melanges': re.compile(r'locuteurs melanges\s*:\s*(\d+)'),
    'hors_bornes': re.compile(r'phrases hors bornes\s*:\s*(\d+)'),
}


def _livres(ids):
    """[(id, titre)] a simuler : ceux demandes, sinon tous les livres castes
    encore en decoupage d'origine (les livres deja en mode dialogue sont
    ecartes : leurs index sont deja fins, il n'y a rien a migrer)."""
    conn = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)
    castes = {r[0] for r in conn.execute(
        'SELECT DISTINCT book_id FROM speaker_attribution')}
    lignes = [(r[0], r[1] or '?', r[2]) for r in conn.execute(
        'SELECT id, title, COALESCE(decoupe_dialogue, 0) FROM books '
        'ORDER BY id')]
    conn.close()
    if ids:
        return [(i, titre) for i, titre, _d in lignes if i in ids]
    return [(i, titre) for i, titre, dialogue in lignes
            if i in castes and not dialogue]


def _mesures(texte):
    """Les chiffres du rapport, lus dans la sortie de l'outil (pas recalcules)."""
    chiffres = {}
    for cle, motif in MOTIFS.items():
        trouve = motif.search(texte)
        if cle == 'avant':
            if trouve:
                chiffres['avant'], chiffres['apres'] = (int(trouve.group(1)),
                                                        int(trouve.group(2)))
        elif trouve:
            chiffres[cle] = int(trouve.group(1))
    return chiffres


def main():
    parseur = argparse.ArgumentParser(
        description='Simulation de la migration en mode dialogue (ecrit rien).')
    parseur.add_argument('--livres', type=int, nargs='*', default=None)
    parseur.add_argument('--variante', choices=('A', 'B'), default='B')
    parseur.add_argument('--exemples', type=int, default=12)
    options = parseur.parse_args()

    livres = _livres(options.livres)

    print('=' * LARGEUR)
    print(' SIMULATION DE LA MIGRATION "MODE DIALOGUE" (aucune ecriture)')
    print('=' * LARGEUR)
    print('  variante : %s -- livres : %d -- exemples par livre : %d'
          % (options.variante, len(livres), options.exemples))
    print('')

    SORTIE.mkdir(exist_ok=True)
    lignes_resume = []
    for identifiant, titre in livres:
        print('  livre %-3d %-44s ...' % (identifiant, titre[:44]), end=' ')
        sys.stdout.flush()
        rapport = subprocess.run(
            [sys.executable, str(OUTIL), '--livre', str(identifiant),
             '--variante', options.variante, '--exemples',
             str(options.exemples)],
            capture_output=True, text=True, encoding='utf-8', cwd=str(RACINE))
        texte = (rapport.stdout or '') + (rapport.stderr or '')
        fichier = SORTIE / ('_simu_dialogue_%d.txt' % identifiant)
        fichier.write_text(texte, encoding='utf-8')
        chiffres = _mesures(texte)
        if chiffres.get('narrateur') is None:
            print('A REGARDER (voir %s)' % fichier.name)
        else:
            print('%d beats gagnes, %d refuses'
                  % (chiffres['narrateur'], chiffres.get('refuses', 0)))
        lignes_resume.append((identifiant, titre, chiffres))

    print('')
    print('-' * LARGEUR)
    print(' RESUME (variante %s)' % options.variante)
    print('-' * LARGEUR)
    print('  %-4s %-40s %7s %8s %13s' % ('#', 'Livre', 'beats', 'refuses',
                                          'phrases'))
    total_beats = total_refuses = 0
    for identifiant, titre, chiffres in lignes_resume:
        beats = chiffres.get('narrateur', 0) or 0
        refuses = chiffres.get('refuses', 0) or 0
        total_beats += beats
        total_refuses += refuses
        print('  %-4d %-40s %7d %8d %13s'
              % (identifiant, titre[:40], beats, refuses,
                 '%s > %s' % (chiffres.get('avant', '?'),
                              chiffres.get('apres', '?'))))
    print('  %-4s %-40s %7d %8d' % ('', 'TOTAL', total_beats, total_refuses))

    resume = SORTIE / '_simu_dialogue_resume.txt'
    with resume.open('w', encoding='utf-8') as sortie:
        sortie.write('Simulation migration mode dialogue -- variante %s -- %s\n\n'
                     % (options.variante,
                        datetime.now().strftime('%d/%m/%Y %H:%M')))
        for identifiant, titre, chiffres in lignes_resume:
            sortie.write('livre %-3d %-44s beats=%-5s refuses=%-5s phrases=%s -> %s\n'
                         % (identifiant, titre[:44], chiffres.get('narrateur'),
                            chiffres.get('refuses'), chiffres.get('avant'),
                            chiffres.get('apres')))
        sortie.write('\nTOTAL beats gagnes : %d, refuses : %d\n'
                     % (total_beats, total_refuses))
    print('')
    print('  resume ecrit dans : _essais/%s' % resume.name)
    print('  rapports detailles : _essais/_simu_dialogue_<numero>.txt')
    print('=' * LARGEUR)
    return 0


if __name__ == '__main__':
    sys.exit(main())
