# -*- coding: utf-8 -*-
"""Migration des INDEX DE PHRASES après la correction du découpage (18/09/2026).

POURQUOI : jusqu'au 18/09/2026, le découpage coupait les phrases après le point
d'une abréviation (« … complimenter M. » / « de Morcerf ; … »). La correction
(`modules/decoupage.py`, règle ACTUELLE) RECOLLE ces morceaux : un chapitre a
donc **moins de phrases** qu'avant, et tous les index qui suivent se décalent.

Deux choses portent un index de phrase en base :
  - `speaker_attribution.sentence_idx` : qui parle (donc la voix de la phrase) ;
  - `progress.cursor_idx` : la phrase où le lecteur s'est arrêté.

Sans migration, les voix se décaleraient dès la première abréviation rencontrée :
un personnage parlerait à la place d'un autre. C'est exactement le risque qui
avait fait reporter ce chantier.

COMMENT : chaque NOUVELLE phrase est la réunion d'une ou plusieurs ANCIENNES
phrases, dans l'ordre du texte. On calcule donc, pour chaque ancienne phrase, la
nouvelle qui la CONTIENT (comparaison de positions), et on remappe. Aucune
interprétation, aucun texte deviné : uniquement des positions.

Si une fusion réunit deux phrases qui avaient des **locuteurs différents**, on
garde le locuteur de la plus longue (le plus probable) et on le SIGNALE dans le
rapport — à corriger à la main dans la fenêtre du casting si besoin.

USAGE (la simulation n'écrit jamais rien) :
    python test_voix/_migrer_index_phrases.py                (simulation)
    python test_voix/_migrer_index_phrases.py --livre 16     (un seul livre)
    python test_voix/_migrer_index_phrases.py --ecrire       (copie la base AVANT)
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

from modules.decoupage import (                                    # noqa: E402
    phrases_avec_positions, REGLE_ANCIENNE, REGLE_ACTUELLE,
)


def construire_mapping(texte):
    """({ancien_idx: nouveau_idx}, anciennes, nouvelles) d'un chapitre.

    Une ancienne phrase peut ne correspondre à AUCUNE nouvelle (c'est le cas
    d'un morceau du genre « M. » seul, qui n'était déjà pas conservé) : la
    valeur est alors None, et l'appelant décide.
    """
    anciennes = phrases_avec_positions(texte, REGLE_ANCIENNE)
    nouvelles = phrases_avec_positions(texte, REGLE_ACTUELLE)
    mapping = {}
    for i, (debut, fin, _texte) in enumerate(anciennes):
        cible = None
        for j, (n_debut, n_fin, _n_texte) in enumerate(nouvelles):
            if n_debut <= debut and fin <= n_fin:
                cible = j
                break
        mapping[i] = cible
    return mapping, anciennes, nouvelles


def _lignes_du_livre(conn, book_id):
    return conn.execute(
        'SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution '
        'WHERE book_id = ? ORDER BY chapter_index, sentence_idx', (book_id,)
    ).fetchall()


def etudier_livre(conn, book, chapitres):
    """Rapport d'un livre : ce qui bougerait, sans rien écrire."""
    lignes = _lignes_du_livre(conn, book['id'])
    if not lignes:
        return None

    par_chapitre = {}
    for ligne in lignes:
        par_chapitre.setdefault(ligne['chapter_index'], []).append(ligne)

    texte_par_index = {c['index']: (c.get('text') or '') for c in chapitres}
    rapport = {
        'livre': book['title'], 'book_id': book['id'],
        'chapitres': 0, 'phrases_avant': 0, 'phrases_apres': 0,
        'phrases_fusionnees': 0, 'attributions': 0, 'sans_cible': 0,
        'desaccords': [], 'chapitres_touches': 0,
    }

    for chapitre_index, lignes_chapitre in sorted(par_chapitre.items()):
        texte = texte_par_index.get(chapitre_index, '')
        if not texte:
            rapport['sans_cible'] += len(lignes_chapitre)
            continue
        mapping, anciennes, nouvelles = construire_mapping(texte)
        rapport['chapitres'] += 1
        rapport['phrases_avant'] += len(anciennes)
        rapport['phrases_apres'] += len(nouvelles)
        rapport['phrases_fusionnees'] += len(anciennes) - len(nouvelles)
        rapport['attributions'] += len(lignes_chapitre)
        if len(anciennes) != len(nouvelles):
            rapport['chapitres_touches'] += 1

        # Locuteurs par nouvelle phrase : sert a detecter les desaccords.
        locuteurs = {}
        for ligne in lignes_chapitre:
            cible = mapping.get(ligne['sentence_idx'])
            if cible is None:
                rapport['sans_cible'] += 1
                continue
            locuteurs.setdefault(cible, []).append(
                (ligne['speaker'], ligne['sentence_idx']))
        for cible, liste in locuteurs.items():
            noms = {nom for nom, _idx in liste}
            if len(noms) > 1:
                longueurs = {}
                for nom, idx in liste:
                    texte_ancien = anciennes[idx][2] if idx < len(anciennes) else ''
                    longueurs[nom] = max(longueurs.get(nom, 0), len(texte_ancien))
                garde = max(longueurs, key=lambda n: longueurs[n])
                rapport['desaccords'].append(
                    (chapitre_index, noms, garde,
                     nouvelles[cible][2][:70] if cible < len(nouvelles) else '?'))
    return rapport

def remapper_livre(conn, book_id, chapitres):
    """Réécrit les attributions d'un livre avec les nouveaux index. Renvoie un bilan."""
    lignes = _lignes_du_livre(conn, book_id)
    if not lignes:
        return None
    par_chapitre = {}
    for ligne in lignes:
        par_chapitre.setdefault(ligne['chapter_index'], []).append(ligne)
    texte_par_index = {c['index']: (c.get('text') or '') for c in chapitres}

    avant, apres, modifiees = 0, 0, 0
    for chapitre_index, lignes_chapitre in sorted(par_chapitre.items()):
        texte = texte_par_index.get(chapitre_index, '')
        if not texte:
            continue
        mapping, anciennes, nouvelles = construire_mapping(texte)
        avant += len(lignes_chapitre)

        # Une seule ligne par nouvelle phrase (la fusion peut en réunir
        # plusieurs) : on garde le locuteur de la plus longue.
        retenues = {}
        for ligne in lignes_chapitre:
            cible = mapping.get(ligne['sentence_idx'])
            if cible is None:
                continue
            longueur = len(anciennes[ligne['sentence_idx']][2]) \
                if ligne['sentence_idx'] < len(anciennes) else 0
            actuel = retenues.get(cible)
            if actuel is None or longueur > actuel[1]:
                retenues[cible] = (ligne['speaker'], longueur)

        conn.execute(
            'DELETE FROM speaker_attribution WHERE book_id = ? AND chapter_index = ?',
            (book_id, chapitre_index))
        for cible, (locuteur, _longueur) in sorted(retenues.items()):
            conn.execute(
                'INSERT INTO speaker_attribution '
                '(book_id, chapter_index, sentence_idx, speaker) VALUES (?, ?, ?, ?)',
                (book_id, chapitre_index, cible, locuteur))
            apres += 1
        modifiees += 1
    conn.commit()
    return {'livre_id': book_id, 'chapitres': modifiees,
            'lignes_avant': avant, 'lignes_apres': apres}


def remapper_progression(conn, book_id, chapitres):
    """Décale `progress.cursor_idx` du même mapping, pour chaque profil."""
    texte_par_index = {c['index']: (c.get('text') or '') for c in chapitres}
    lignes = conn.execute(
        'SELECT user_id, chapter_index, cursor_idx FROM progress WHERE book_id = ?',
        (book_id,)).fetchall()
    changes = 0
    for ligne in lignes:
        texte = texte_par_index.get(ligne['chapter_index'], '')
        if not texte or not ligne['cursor_idx']:
            continue
        mapping, _a, nouvelles = construire_mapping(texte)
        cible = mapping.get(ligne['cursor_idx'])
        if cible is None or cible == ligne['cursor_idx']:
            continue
        if cible >= len(nouvelles):
            continue
        conn.execute(
            'UPDATE progress SET cursor_idx = ? WHERE user_id = ? AND book_id = ?',
            (cible, ligne['user_id'], book_id))
        changes += 1
    conn.commit()
    return changes

def verifier_livre(conn, book, chapitres):
    """Contrôle APRÈS migration : chaque index en base existe-t-il vraiment ?

    Le seul risque qui compte pour Laurent : une attribution qui pointerait
    au-delà du nombre de phrases du chapitre (elle ne serait jamais utilisée,
    ou pire, sur la mauvaise phrase). On le dit ici, chiffre à l'appui.
    """
    lignes = _lignes_du_livre(conn, book['id'])
    if not lignes:
        return None
    texte_par_index = {c['index']: (c.get('text') or '') for c in chapitres}
    par_chapitre = {}
    for ligne in lignes:
        par_chapitre.setdefault(ligne['chapter_index'], []).append(ligne)

    hors_bornes = 0
    total = 0
    for chapitre_index, lignes_chapitre in par_chapitre.items():
        texte = texte_par_index.get(chapitre_index, '')
        if not texte:
            hors_bornes += len(lignes_chapitre)
            continue
        nombre = len(phrases_avec_positions(texte, REGLE_ACTUELLE))
        for ligne in lignes_chapitre:
            total += 1
            if ligne['sentence_idx'] >= nombre or ligne['sentence_idx'] < 0:
                hors_bornes += 1
    return {'total': total, 'hors_bornes': hors_bornes,
            'chapitres': len(par_chapitre)}


def main():
    analyseur = argparse.ArgumentParser(
        description='Migre les index de phrases apres la correction du decoupage.')
    analyseur.add_argument('--livre', type=int, default=None,
                           help="ne traiter qu'un livre (identifiant)")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="appliquer (copie la base AVANT d'ecrire)")
    analyseur.add_argument('--verifier', action='store_true',
                           help='controle APRES migration : index dans les bornes ?')
    options = analyseur.parse_args()

    from core.epub_parser import get_chapters

    print('')
    print('=' * 78)
    if options.verifier:
        titre = '- CONTROLE DE LA BASE (apres migration)'
    elif options.ecrire:
        titre = '- APPLICATION'
    else:
        titre = "- SIMULATION (rien n'est ecrit)"
    print('MIGRATION DES INDEX DE PHRASES %s' % titre)
    print('=' * 78)

    conn = sqlite3.connect(str(BASE))
    conn.row_factory = sqlite3.Row
    if options.livre:
        livres = conn.execute('SELECT * FROM books WHERE id = ?',
                              (options.livre,)).fetchall()
    else:
        livres = conn.execute('SELECT * FROM books ORDER BY id').fetchall()

    cibles = [livre for livre in livres
              if (BIBLIOTHEQUE / livre['filename']).is_file()]
    print('')
    print('  %d livre(s) a examiner.' % len(cibles))

    # --- Mode CONTROLE (apres migration) ----------------------------------
    if options.verifier:
        from core.epub_parser import get_chapters as _get_chapters
        total, hors = 0, 0
        print('')
        for livre in cibles:
            chapitres = _get_chapters(str(BIBLIOTHEQUE / livre['filename']))
            if not chapitres:
                continue
            r = verifier_livre(conn, livre, chapitres)
            if r is None:
                continue
            total += r['total']
            hors += r['hors_bornes']
            etat = 'OK' if r['hors_bornes'] == 0 else 'A REGARDER'
            print('  %-46s %6d attributions, %d hors bornes  [%s]'
                  % (livre['title'][:46], r['total'], r['hors_bornes'], etat))
        print('')
        print('=' * 78)
        print('  %d attributions verifiees, %d hors bornes' % (total, hors))
        print('  ' + ("Chaque voix pointe sur une phrase qui existe."
                      if hors == 0 else
                      "DES INDEX SONT HORS BORNES : ne pas utiliser la base"
                      " telle quelle."))
        conn.close()
        return 0

    if options.ecrire:
        horodatage = datetime.now().strftime('%Y%m%d_%H%M')
        sauvegarde = BASE.with_name('nimm_epub.db.bak_avant_migration_phrases_%s'
                                    % horodatage)
        shutil.copy2(BASE, sauvegarde)
        print('  Sauvegarde de la base : %s' % sauvegarde.name)

    total = {'chapitres': 0, 'phrases_avant': 0, 'phrases_apres': 0,
             'attributions': 0, 'desaccords': 0, 'chapitres_touches': 0,
             'sans_cible': 0}

    for livre in cibles:
        chapitres = get_chapters(str(BIBLIOTHEQUE / livre['filename']))
        if not chapitres:
            continue
        rapport = etudier_livre(conn, livre, chapitres)
        if rapport is None:
            continue
        print('')
        print('  %s (id %s)' % (livre['title'][:60], livre['id']))
        print('    chapitres attribues      : %d' % rapport['chapitres'])
        print('    phrases avant / apres    : %d / %d  (%d fusionnees)'
              % (rapport['phrases_avant'], rapport['phrases_apres'],
                 rapport['phrases_fusionnees']))
        print('    chapitres concernes      : %d' % rapport['chapitres_touches'])
        print('    attributions (voix)      : %d' % rapport['attributions'])
        if rapport['sans_cible']:
            print('    sans cible (a verifier)  : %d' % rapport['sans_cible'])
        for chapitre_index, noms, garde, extrait in rapport['desaccords'][:5]:
            print('      ! locuteurs melanges au chapitre %d : %s -> garde %s'
                  % (chapitre_index, ' / '.join(sorted(noms)), garde))
            print('        %s...' % extrait)

        for cle in ('chapitres', 'phrases_avant', 'phrases_apres',
                    'attributions', 'chapitres_touches', 'sans_cible'):
            total[cle] += rapport[cle]
        total['desaccords'] += len(rapport['desaccords'])

        if options.ecrire:
            bilan = remapper_livre(conn, livre['id'], chapitres)
            curseurs = remapper_progression(conn, livre['id'], chapitres)
            if bilan:
                print('    ECRIT : %d lignes -> %d lignes (%d chapitres), '
                      '%d curseur(s) de reprise decale(s)'
                      % (bilan['lignes_avant'], bilan['lignes_apres'],
                         bilan['chapitres'], curseurs))

    print('')
    print('=' * 78)
    print('BILAN')
    print('=' * 78)
    print('  %d chapitres attribues, %d phrases -> %d phrases (%d fusions)'
          % (total['chapitres'], total['phrases_avant'], total['phrases_apres'],
             total['phrases_avant'] - total['phrases_apres']))
    print('  %d attributions de voix a remapper, %d chapitres concernes'
          % (total['attributions'], total['chapitres_touches']))
    if total['desaccords']:
        print('  %d fusion(s) avec des locuteurs differents : le locuteur de la'
              % total['desaccords'])
        print('  phrase la plus longue est garde (a verifier dans le casting).')
    if total['sans_cible']:
        print('  %d attribution(s) SANS cible : a regarder avant d\'appliquer.'
              % total['sans_cible'])
    print('')
    if not options.ecrire:
        print('  SIMULATION : rien n\'a ete modifie. Pour appliquer :')
        print('      python test_voix/_migrer_index_phrases.py --ecrire')
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
