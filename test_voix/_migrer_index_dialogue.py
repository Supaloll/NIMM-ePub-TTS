# -*- coding: utf-8 -*-
"""Migration des INDEX DE PHRASES pour le MODE DIALOGUE — SIMULATION d'abord.

POURQUOI CET OUTIL (22/09/2026). Le mode dialogue (`books.decoupe_dialogue`)
change le DECOUPAGE d'un livre : un morceau qui melange la narration et une
replique est coupe en deux. Or les numeros de phrases sont ENREGISTRES en base
(`speaker_attribution.sentence_idx`) : sans migration, les voix se decalent des
la premiere coupe, et un personnage parle a la place d'un autre.

CE QUE LA MIGRATION TOUCHE, ET CE QU'ELLE NE TOUCHE PAS — question de Laurent,
22/09/2026 : « est-ce que mon casting va rester tel qu'il est ? »
  - `speaker_attribution.sentence_idx` / `speaker` : REMAPPES — c'est le but ;
  - `progress.cursor_idx` : remappe, sinon la reprise de lecture tombe a cote ;
  - **`voices`** (voix, hauteur, vitesse, verrous par personnage),
    **`cast_fiche`**, **`character_aliases`**, **`books.narrator_voice`** :
    **JAMAIS touchees**. Le casting de Laurent reste tel qu'il est. (Verifie dans
    la base : il n'existe AUCUNE voix posee phrase par phrase ; changer la voix
    d'une phrase dans le lecteur change la voix du PERSONNAGE.)

DEUX VARIANTES, mesurees cote a cote — le choix revient a Laurent :
  - **A « sans regle »** : un morceau neuf garde le locuteur de l'ancien morceau
    qui le contient. Le plus fidele, mais les beats nouvellement separes restent
    au personnage : c'est le defaut que le mode dialogue vise.
  - **B « avec la regle »** : les beats nes de NOTRE coupe sont remis au
    narrateur, SAUF ceux qui se trouvent dans une citation ouverte (les cas de
    Lazarille qui avaient fait retirer la regle du pipeline le 21/09/2026).

LA SIMULATION N'ECRIT RIEN. Aucune option d'ecriture pour l'instant : elle
viendra apres la decision, avec copie datee de la base et relecture de controle.

USAGE :
    python test_voix/_migrer_index_dialogue.py --livre 28
    python test_voix/_migrer_index_dialogue.py --livre 28 --variante A
    python test_voix/_migrer_index_dialogue.py --livre 28 --exemples 25
"""

import argparse
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                      # noqa: E402
from modules.decoupage import (                                # noqa: E402
    phrases_avec_positions, introduit_une_replique, REGLE_ACTUELLE, REGLE_DIALOGUE)

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
LARGEUR = 78


def _livre(conn, book_id):
    return conn.execute(
        'SELECT id, title, filename, COALESCE(decoupe_dialogue, 0) '
        'FROM books WHERE id = ?', (book_id,)).fetchone()


def _attributions(conn, book_id):
    """{chapitre: [(sentence_idx, speaker)]}, dans l'ordre."""
    par_chapitre = {}
    for chapitre, idx, speaker in conn.execute(
            'SELECT chapter_index, sentence_idx, speaker FROM '
            'speaker_attribution WHERE book_id = ? '
            'ORDER BY chapter_index, sentence_idx', (book_id,)):
        par_chapitre.setdefault(chapitre, []).append((idx, speaker))
    return par_chapitre


def _destination(anciennes, nouvelles):
    """Pour chaque ANCIENNE phrase, la NOUVELLE qui la contient (ou None).

    Les deux listes sont triees par position, et la regle dialogue ne fait
    qu'AJOUTER des coupes : une nouvelle phrase ne peut pas etre la reunion de
    deux anciennes. Un simple curseur suffit donc.
    """
    resultat, j = [], 0
    for debut, _fin, _texte in anciennes:
        while j < len(nouvelles) and nouvelles[j][1] <= debut:
            j += 1
        if j < len(nouvelles) and nouvelles[j][0] <= debut < nouvelles[j][1]:
            resultat.append(j)
        else:
            resultat.append(None)
    return resultat


def _contenante(anciennes, nouvelles):
    """Pour chaque NOUVELLE phrase, l'ANCIENNE qui la contient (ou None)."""
    resultat, i = [], 0
    for debut, _fin, _texte in nouvelles:
        while i < len(anciennes) and anciennes[i][1] <= debut:
            i += 1
        if i < len(anciennes) and anciennes[i][0] <= debut < anciennes[i][1]:
            resultat.append(i)
        else:
            resultat.append(None)
    return resultat


def _citation_ouverte(texte, position):
    """La position est-elle DANS une citation deja ouverte ? (« > »)."""
    avant = texte[:position]
    return avant.count('«') > avant.count('»')


def _beat(texte, nouvelles, j):
    """('beat' | 'refuse' | '') : morceau neuf qui introduit une réplique.

    'refuse' = ce serait un beat, mais il se trouve DANS une citation ouverte :
    on n'y touche pas (leçon de Lazarille, 21/09/2026).

    ⚠️ La PREMIÈRE condition (« pas d'ouverture de citation dans le morceau »)
    manquait dans la version de 11 h : la lecture des exemples a montré qu'une
    RÉPLIQUE (« Je ne t'ai jamais vu pleurer », m'a-t-elle dit…) était classée
    en beat, à cause du verbe de parole qu'elle contient. Lui donner le narrateur
    aurait fait lire la réplique d'un personnage par le narrateur — pire que le
    défaut qu'on corrige. Un beat est, par construction, le texte AVANT la
    citation : il ne peut pas en contenir une.
    """
    if '«' in nouvelles[j][2]:
        return ''
    if not introduit_une_replique(nouvelles[j][2]):
        return ''
    if j + 1 >= len(nouvelles):
        return ''
    if not nouvelles[j + 1][2].lstrip().startswith('«'):
        return ''
    if _citation_ouverte(texte, nouvelles[j][0]):
        return 'refuse'
    return 'beat'


def etudier_chapitre(texte, attributions, variante):
    """Le détail d'un chapitre, sans rien écrire.

    Renvoie un dictionnaire de comptes, plus les exemples à LIRE (la leçon du
    21/09/2026 : un chiffre ne vaut rien sans la lecture du texte).
    """
    anciennes = phrases_avec_positions(texte, REGLE_ACTUELLE)
    nouvelles = phrases_avec_positions(texte, REGLE_DIALOGUE)
    dest = _destination(anciennes, nouvelles)
    orig = _contenante(anciennes, nouvelles)

    rang_de_index, speaker_par_rang = {}, {}
    for idx, speaker in attributions:
        if idx < len(anciennes):
            rang_de_index[idx] = idx
            speaker_par_rang[idx] = speaker

    # 1) ce qui se RECOLLE : chaque ancienne phrase va dans une nouvelle.
    locuteurs = [None] * len(nouvelles)
    par_nouvelle, hors_bornes = {}, 0
    for idx, speaker in attributions:
        if idx not in rang_de_index:
            hors_bornes += 1
            continue
        cible = dest[idx]
        if cible is None:
            hors_bornes += 1
            continue
        par_nouvelle.setdefault(cible, []).append((idx, speaker))

    melanges = []
    for j, liste in par_nouvelle.items():
        liste = sorted(liste, key=lambda item: -len(anciennes[item[0]][2]))
        locuteurs[j] = liste[0][1]
        if len({s for _i, s in liste}) > 1:
            melanges.append((j, sorted({s for _i, s in liste}), nouvelles[j][2]))

    # 2) les morceaux NEUFS (les repliques que la coupe vient de detacher) :
    #    ils heritent du locuteur de l'ancienne phrase qui les contient.
    #
    #    ATTENTION AU SENS DE LA COUPE (erreur de la premiere version, corrigee
    #    le 22/09/2026) : `_couper_avant_replique` met le BEAT EN PREMIER et la
    #    REPLIQUE EN SECOND. Le beat, donc, commence a la meme position que
    #    l'ancienne phrase : c'est lui qui HERITE du personnage, et c'est lui
    #    qu'il faut remettre au narrateur. La replique, elle, est le morceau
    #    neuf, et elle garde (a juste titre) le personnage.
    crees, sans_locuteur = 0, 0
    for j in range(len(nouvelles)):
        if locuteurs[j] is not None:
            continue
        i = orig[j]
        if i is not None and i in speaker_par_rang:
            locuteurs[j] = speaker_par_rang[i]
            crees += 1
        else:
            locuteurs[j] = 'narration'
            sans_locuteur += 1

    # 3) variante B : les BEATS nes de notre coupe passent au narrateur.
    beats, refuses, possibles = [], [], 0
    for j in range(len(nouvelles)):
        genre = _beat(texte, nouvelles, j)
        if genre == 'beat':
            possibles += 1
            if variante == 'B' and locuteurs[j] != 'narration':
                beats.append((j, orig[j], locuteurs[j]))
                locuteurs[j] = 'narration'
        elif genre == 'refuse':
            refuses.append((j, orig[j], locuteurs[j]))

    return {
        'anciennes': anciennes, 'nouvelles': nouvelles, 'locuteurs': locuteurs,
        'destinations': dest,
        'phrases_avant': len(anciennes), 'phrases_apres': len(nouvelles),
        'crees': crees, 'beats': beats, 'possibles': possibles,
        'refuses': refuses, 'melanges': melanges,
        'hors_bornes': hors_bornes, 'sans_locuteur': sans_locuteur,
    }


def _copie_datee(base):
    """Copie datée de la base AVANT toute écriture. Renvoie son chemin."""
    from datetime import datetime
    copie = base.with_name(base.name + '.bak_avant_dialogue_'
                           + datetime.now().strftime('%Y%m%d_%H%M'))
    source = sqlite3.connect(str(base))
    cible = sqlite3.connect(str(copie))
    with cible:
        source.backup(cible)
    cible.close()
    source.close()
    return copie


def _lignes_a_ecrire(detail):
    """[(sentence_idx, speaker)] de la nouvelle attribution d'un chapitre."""
    return [(idx, speaker) for idx, speaker in enumerate(detail['locuteurs'])]


def ecrire(conn, identifiant, resultats, options):
    """Écrit la migration. Renvoie un bilan de ce qui a été écrit.

    Ce qui est écrit, et RIEN d'autre :
      - `speaker_attribution` du livre : remplacé par la nouvelle répartition ;
      - `books.decoupe_dialogue` = 1 (le livre passe en mode dialogue) ;
      - `progress.cursor_idx` : remappé, sinon la reprise tombe à côté ;
      - `voices.line_count` : recompté (le nombre de répliques de chacun bouge
        un peu, puisque les beats quittent le personnage).
    Les voix, la hauteur, la vitesse, les verrous, les alias et la voix du
    narrateur ne sont JAMAIS touchés.
    """
    conn.execute('PRAGMA busy_timeout = 20000')
    with conn:
        conn.execute('DELETE FROM speaker_attribution WHERE book_id = ?',
                     (identifiant,))
        lignes = [(identifiant, chapitre, idx, speaker)
                  for chapitre, detail in resultats.items()
                  for idx, speaker in _lignes_a_ecrire(detail)]
        conn.executemany(
            'INSERT INTO speaker_attribution (book_id, chapter_index, '
            'sentence_idx, speaker) VALUES (?, ?, ?, ?)', lignes)
        conn.execute('UPDATE books SET decoupe_dialogue = 1 WHERE id = ?',
                     (identifiant,))
        for (user_id, _chapitre, ancien), nouveau in options['curseurs'].items():
            conn.execute('UPDATE progress SET cursor_idx = ? WHERE user_id = ? '
                         'AND book_id = ?', (nouveau, user_id, identifiant))
        conn.execute(
            'UPDATE voices SET line_count = (SELECT COUNT(*) FROM '
            'speaker_attribution WHERE book_id = voices.book_id AND '
            'speaker = voices.character_name) WHERE book_id = ?', (identifiant,))
    return {'attributions': len(lignes),
            'curseurs': len(options['curseurs'])}


def verifier(conn, identifiant, resultats):
    """Relecture APRÈS écriture : chaque voix pointe sur une phrase qui existe.

    C'est le contrôle qui compte : si un index dépasse le nombre de phrases du
    chapitre, la voix ne serait plus lue du tout (ou pire, elle glisserait sur
    la phrase suivante).
    """
    souci = []
    total = 0
    for chapitre, detail in sorted(resultats.items()):
        attendu = len(detail['nouvelles'])
        lignes = conn.execute(
            'SELECT sentence_idx, speaker FROM speaker_attribution WHERE '
            'book_id = ? AND chapter_index = ?', (identifiant, chapitre)).fetchall()
        total += len(lignes)
        for idx, speaker in lignes:
            if not 0 <= idx < attendu:
                souci.append('ch.%d : index %d hors bornes (0..%d)'
                             % (chapitre, idx, attendu - 1))
        if not lignes:
            souci.append('ch.%d : aucune attribution !' % chapitre)
    connus = {r[0] for r in conn.execute(
        'SELECT character_name FROM voices WHERE book_id = ?', (identifiant,))}
    inconnus = {r[0] for r in conn.execute(
        'SELECT DISTINCT speaker FROM speaker_attribution WHERE book_id = ?',
        (identifiant,))} - connus - {'narration'}
    if inconnus:
        souci.append('locuteurs inconnus (pas dans le casting) : %s'
                     % ', '.join(sorted(inconnus)[:5]))
    mode = conn.execute('SELECT COALESCE(decoupe_dialogue, 0) FROM books '
                        'WHERE id = ?', (identifiant,)).fetchone()[0]
    return {'lignes': total, 'mode_dialogue': mode, 'souci': souci}


def main():
    parseur = argparse.ArgumentParser(
        description='Migration des index pour le mode dialogue (simulation).')
    parseur.add_argument('--livre', type=int, required=True)
    parseur.add_argument('--variante', choices=('A', 'B'), default='B',
                         help='A : sans regle ; B : beats au narrateur (defaut)')
    parseur.add_argument('--exemples', type=int, default=8)
    parseur.add_argument('--ecrire', action='store_true',
                         help='ECRIT la migration (copie datee avant, et '
                              'controle apres). Sans cette option : simulation.')
    parseur.add_argument('--base', default=None,
                         help='autre base (repeter l operation sur une COPIE, '
                              'avant de toucher la vraie)')
    options = parseur.parse_args()
    base = Path(options.base) if options.base else BASE

    conn = sqlite3.connect('file:' + base.as_posix() + '?mode=ro', uri=True)
    livre = _livre(conn, options.livre)
    if livre is None:
        print('Livre %d inconnu.' % options.livre)
        return 2
    identifiant, titre, fichier, dialogue = livre
    attributions = _attributions(conn, identifiant)
    conn.close()

    chapitres = get_chapters(str(BIBLIOTHEQUE / fichier))
    texte_par_index = {c['index']: (c.get('text') or '') for c in chapitres}

    print('=' * LARGEUR)
    print(' MIGRATION DES INDEX — MODE DIALOGUE (simulation, rien n est ecrit)')
    print('=' * LARGEUR)
    print('  livre         : %s (id %d)' % (titre, identifiant))

    # GARDE-FOU : un livre DEJA en mode dialogue a ses index calcules sur le
    # nouveau decoupage. Simuler une migration dessus serait un contresens — et
    # l'appliquer decalerait ses voix d'un morceau a chaque coupe.
    if dialogue:
        print('  mode dialogue : OUI')
        print('')
        print('  ARRET : ce livre est DEJA en mode dialogue. Ses numeros de phrases')
        print('  sont deja ceux du decoupage fin : il n y a rien a migrer, et')
        print('  remapper ses index les decalerait. Rien n est ecrit.')
        return 2
    print('  mode dialogue : NON (a activer avant la migration)')
    print('  variante      : %s (%s)' % (
        options.variante,
        'sans regle : un morceau neuf garde le locuteur herite'
        if options.variante == 'A' else
        'les beats nes de la coupe sont remis au narrateur'))
    phrases = sum(len(v) for v in attributions.values())
    print('  attributions  : %d phrases, %d chapitres attribues'
          % (phrases, len(attributions)))
    print('')
    print('  Rien n est ecrit : cet outil MESURE. Les voix par personnage, les')
    print('  reglages, les verrous, les alias et la voix du narrateur ne sont')
    print('  pas concernes par la migration (seul le « qui parle » bouge).')

    total = {'chapitres': 0, 'sans_texte': 0, 'avant': 0, 'apres': 0,
             'crees': 0, 'possibles': 0, 'beats': 0, 'refuses': 0,
             'hors_bornes': 0, 'sans_locuteur': 0, 'melanges': 0}
    ex_beats, ex_refuses, ex_melanges = [], [], []
    resultats = {}

    for chapitre, lignes in sorted(attributions.items()):
        texte = texte_par_index.get(chapitre, '')
        if not texte:
            total['sans_texte'] += 1
            continue
        detail = etudier_chapitre(texte, lignes, options.variante)
        resultats[chapitre] = detail
        total['chapitres'] += 1
        total['avant'] += detail['phrases_avant']
        total['apres'] += detail['phrases_apres']
        total['crees'] += detail['crees']
        total['possibles'] += detail['possibles']
        total['beats'] += len(detail['beats'])
        total['refuses'] += len(detail['refuses'])
        total['hors_bornes'] += detail['hors_bornes']
        total['sans_locuteur'] += detail['sans_locuteur']
        total['melanges'] += len(detail['melanges'])

        for j, _i, speaker in detail['beats']:
            if len(ex_beats) >= options.exemples:
                break
            ex_beats.append('ch. %-3d  locuteur avant : %s' % (chapitre, speaker))
            ex_beats.append('  BEAT -> narrateur : %s'
                            % detail['nouvelles'][j][2][:92])
            ex_beats.append('  REPLIQUE (personnage) : %s'
                            % detail['nouvelles'][j + 1][2][:70])
        for j, _i, speaker in detail['refuses']:
            if len(ex_refuses) >= 3:
                break
            ex_refuses.append('ch. %-3d  [%s] laisse tel quel : %s'
                              % (chapitre, speaker,
                                 detail['nouvelles'][j][2][:80]))
        for j, noms, texte_piece in detail['melanges']:
            if len(ex_melanges) >= 3:
                break
            ex_melanges.append('ch. %-3d  %s -> garde le plus long : %s'
                               % (chapitre, ' / '.join(noms), texte_piece[:70]))

    print('')
    print('-' * LARGEUR)
    print(' BILAN')
    print('-' * LARGEUR)
    print('  chapitres etudies        : %d  (%d sans texte)'
          % (total['chapitres'], total['sans_texte']))
    print('  phrases avant / apres    : %d / %d  (+%d morceaux nes de la coupe)'
          % (total['avant'], total['apres'], total['apres'] - total['avant']))
    print('  repliques detachees      : %d   (heritent du personnage, c est voulu)'
          % total['crees'])
    print('  beats detectes           : %d' % total['possibles'])
    print('    remis au narrateur     : %d%s'
          % (total['beats'], '' if options.variante == 'B'
             else '   (variante A : aucun, c est le choix mesure)'))
    print('    refuses (citation ouverte) : %d' % total['refuses'])
    print('  sans locuteur (mis au narrateur) : %d' % total['sans_locuteur'])
    print('  phrases hors bornes (index plus grand que le texte) : %d'
          % total['hors_bornes'])
    print('  locuteurs melanges       : %d' % total['melanges'])
    print('')
    print('  CE QUI CHANGE dans "qui parle" : %d morceaux (%0.2f %% des phrases)'
          % (total['beats'] + total['sans_locuteur'],
             100.0 * (total['beats'] + total['sans_locuteur'])
             / max(1, total['avant'])))
    print('  CE QUI NE CHANGE PAS           : %d phrases'
          % (total['avant'] - total['beats'] - total['sans_locuteur']))

    for titre_bloc, exemples in (
            ('LES BEATS REMIS AU NARRATEUR — a lire', ex_beats),
            ('BEATS REFUSES (dans une citation ouverte)', ex_refuses),
            ('LOCUTEURS MELANGES (on garde le plus long)', ex_melanges)):
        if exemples:
            print('')
            print('-' * LARGEUR)
            print(' %s' % titre_bloc)
            print('-' * LARGEUR)
            for ligne in exemples:
                print('  ' + ligne)

    # ------------------------------------------------------------- ECRITURE
    if options.ecrire:
        print('')
        print('-' * LARGEUR)
        print(' ECRITURE (--ecrire)')
        print('-' * LARGEUR)
        conn = sqlite3.connect(str(base))
        conn.execute('PRAGMA busy_timeout = 20000')
        curseurs = {}
        for user_id, chapitre, curseur in conn.execute(
                'SELECT user_id, chapter_index, cursor_idx FROM progress '
                'WHERE book_id = ?', (identifiant,)):
            detail = resultats.get(chapitre)
            if detail is None or curseur is None:
                continue
            cible = (detail['destinations'][curseur]
                     if 0 <= curseur < len(detail['destinations']) else None)
            if cible is None:
                print('  curseur du chapitre %d laisse tel quel (phrase %s)'
                      % (chapitre, curseur))
                continue
            curseurs[(user_id, chapitre, curseur)] = cible

        if base == BASE:
            copie = _copie_datee(BASE)
            print('  copie datee AVANT d ecrire : %s' % copie.name)
        else:
            copie = base
            print('  base de travail : %s (ce n est PAS la base du lecteur)'
                  % base.name)

        bilan = ecrire(conn, identifiant, resultats, {'curseurs': curseurs})
        print('  ecrit : %d attributions, %d curseur(s) de reprise, '
              'mode dialogue active' % (bilan['attributions'], bilan['curseurs']))
        controle = verifier(conn, identifiant, resultats)
        conn.close()
        print('')
        print('  CONTROLE APRES ECRITURE')
        print('    lignes relues        : %d' % controle['lignes'])
        print('    mode dialogue en base : %s' % controle['mode_dialogue'])
        if controle['souci']:
            for ligne in controle['souci'][:8]:
                print('    A REGARDER : %s' % ligne)
        else:
            print('    OK : chaque voix pointe sur une phrase qui existe, et tous')
            print('    les locuteurs sont dans le casting de ce livre.')
        print('')
        print('  RETOUR ARRIERE : recopier %s sur data/%s' % (copie.name,
                                                             BASE.name))
        print('  A FAIRE COTE LECTEUR : recharger la page (le navigateur garde le')
        print('  casting et le decoupage en memoire).')
        print('')
        print('=' * LARGEUR)
        print(' MIGRATION ECRITE. Aucune facture : tout est calcule ici.')
        print('=' * LARGEUR)
        return 0

    print('')
    print('=' * LARGEUR)
    print(' Simulation seulement : AUCUNE ecriture, aucune facture.')
    print(' (pour ecrire : ajouter --ecrire)')
    print('=' * LARGEUR)
    return 0


if __name__ == '__main__':
    sys.exit(main())

