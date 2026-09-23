# -*- coding: utf-8 -*-
"""RESTAURER les morceaux qui sont DANS une replique en tiret.

POURQUOI CET OUTIL (note urgente de Claude, 23/09/2026). `_beat()` refuse un
morceau qui contient `«`. Une REPLIQUE EN TIRET n'en contient pas : elle a un
verbe de parole et le morceau suivant commence par `«` (chez Dumas, la premiere
replique est entre «, les suivantes en tiret). Elle a donc ete prise pour un
beat, et **remise au narrateur** -- a tort, c'est la replique d'un personnage.

Mesure (`_essais/_mesurer_dans_la_replique.py`) : **134** morceaux sont dans une
replique en tiret, dont **81** sont deja au personnage. Restent **53** a
reparer : **14** mis au narrateur par la migration du 23/09 et **39** par le
rattrapage des beats (`_rattraper_beats_derive.py`, meme jour).

CE QUE FAIT CET OUTIL : il rend a ces morceaux **l'etiquette d'origine**, celle
de la copie `bak_avant_dialogue_20260922_1311` -- ce n'est PAS un nouveau
casting, c'est une **restauration**. Pour un beat, le morceau neuf commence a la
position de l'ancien morceau : l'index se remappe 1 pour 1, donc la
correspondance est exacte.

USAGE :
    python test_voix/_restaurer_hors_replique.py              (simulation)
    python test_voix/_restaurer_hors_replique.py --livres 33 17
    python test_voix/_restaurer_hors_replique.py --ecrire     (ECRIT)
"""

import importlib.util
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                          # noqa: E402

spec = importlib.util.spec_from_file_location(
    'mig', RACINE / 'test_voix' / '_migrer_index_dialogue.py')
mig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mig)

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
LARGEUR = 78
TIRETS = ('\u2014', '\u2013')
OUVREURS = TIRETS + ('\u00ab', '"')
FERMANTS = ('\u00bb', '\u201d')


def _copies():
    return sorted((RACINE / 'data').glob('nimm_epub.db.bak_avant_dialogue_*'))


def _ligne_et_position(texte, position):
    gauche = texte.rfind('\n', 0, position)
    gauche = 0 if gauche < 0 else gauche + 1
    droite = texte.find('\n', position)
    droite = len(texte) if droite < 0 else droite
    return texte[gauche:droite], position - gauche


def _dans_la_replique(ligne, position):
    """La regle de Claude : la ligne ouvre un dialogue et le morceau est avant
    son guillemet fermant (ou la ligne n'en a aucun)."""
    if ligne.lstrip()[:1] not in OUVREURS:
        return False
    fermi = len(ligne)
    for caractere in FERMANTS:
        index = ligne.find(caractere)
        if index >= 0:
            fermi = min(fermi, index)
    return True if fermi == len(ligne) else position < fermi


def _a_restaurer(conn, conn_act, identifiant, fichier):
    """[(chapitre, index, locuteur_origine, texte)] a rendre au personnage."""
    attributions = mig._attributions(conn, identifiant)
    chapitres = {c['index']: (c.get('text') or '') for c in get_chapters(
        str(BIBLIOTHEQUE / fichier))}
    resultat = []
    for chapitre, lignes in sorted(attributions.items()):
        texte = chapitres.get(chapitre, '')
        if not texte:
            continue
        detail = mig.etudier_chapitre(texte, lignes, 'B')
        for j, _o, locuteur_origine in detail['beats']:
            debut, _fin, morceau = detail['nouvelles'][j]
            ligne, position = _ligne_et_position(texte, debut)
            if not _dans_la_replique(ligne, position):
                continue
            actuel = conn_act.execute(
                'SELECT speaker FROM speaker_attribution WHERE book_id = ? '
                'AND chapter_index = ? AND sentence_idx = ?',
                (identifiant, chapitre, j)).fetchone()
            if actuel is None or actuel[0] != 'narration':
                continue                    # deja au personnage : rien a faire
            resultat.append((chapitre, j, locuteur_origine, morceau.strip()))
    return resultat


def main():
    livres = []
    ecrire = False
    exemples = 3
    for position, argument in enumerate(sys.argv):
        if argument == '--livres':
            livres = [int(a) for a in sys.argv[position + 1:] if a.isdigit()]
        elif argument == '--ecrire':
            ecrire = True
        elif argument == '--exemples' and position + 1 < len(sys.argv):
            exemples = int(sys.argv[position + 1])

    copies = _copies()
    if not copies:
        print('Aucune copie datee : impossible de restaurer l etiquette '
              'd origine.')
        return 2
    origine = copies[0]
    conn = sqlite3.connect('file:' + origine.as_posix() + '?mode=ro', uri=True)
    conn_act = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)

    print('=' * LARGEUR)
    print(' RESTAURER LES MORCEAUX QUI SONT DANS UNE REPLIQUE EN TIRET')
    print('  etiquette d origine : %s' % origine.name)
    print('  mode : %s' % ('ECRITURE' if ecrire else 'simulation'))
    print('=' * LARGEUR)

    travail, total = [], 0
    for identifiant, titre, fichier, dialogue in conn.execute(
            'SELECT id, title, filename, COALESCE(decoupe_dialogue, 0) '
            'FROM books ORDER BY id'):
        if dialogue or (livres and identifiant not in livres):
            continue
        a_faire = _a_restaurer(conn, conn_act, identifiant, fichier)
        if a_faire:
            total += len(a_faire)
            travail.append((identifiant, titre, a_faire))
            print('')
            print('  livre %-3d %-34s %4d morceaux a restaurer'
                  % (identifiant, titre[:34], len(a_faire)))
            for chapitre, index, locuteur, morceau in a_faire[:exemples]:
                print('        ch.%-3d #%-4d -> %-22s %s'
                      % (chapitre, index, locuteur[:22], morceau[:62]))
    conn.close()
    conn_act.close()
    if not travail:
        print('')
        print('  Rien a restaurer.')
        print('=' * LARGEUR)
        return 0

    print('')
    print('  TOTAL a restaurer : %d morceaux' % total)
    if not ecrire:
        print('')
        print('  SIMULATION : AUCUNE ecriture. (pour ecrire : --ecrire)')
        print('=' * LARGEUR)
        return 0
    return _ecrire(travail, origine)


def _ecrire(travail, origine):
    """Copie datee, restauration, controles APRES."""
    copie = BASE.with_name(BASE.name + '.bak_avant_restauration_repliques_'
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
    total = 0
    with conn:
        for identifiant, _titre, a_faire in travail:
            conn.executemany(
                'UPDATE speaker_attribution SET speaker = ? WHERE book_id = ? '
                'AND chapter_index = ? AND sentence_idx = ?',
                [(locuteur, identifiant, chapitre, index)
                 for chapitre, index, locuteur, _t in a_faire])
            total += len(a_faire)
            conn.execute(
                'UPDATE voices SET line_count = (SELECT COUNT(*) FROM '
                'speaker_attribution WHERE book_id = voices.book_id AND '
                'speaker = voices.character_name) WHERE book_id = ?',
                (identifiant,))
    print('  ecrit : %d morceaux rendus a leur personnage' % total)

    print('')
    print('  CONTROLE APRES ECRITURE')
    souci = 0
    for identifiant, titre, _a_faire in travail:
        relu = conn.execute(
            'SELECT COUNT(*) FROM speaker_attribution WHERE book_id = ?',
            (identifiant,)).fetchone()[0]
        # ATTENTION : des locuteurs hors casting EXISTENT depuis le debut
        # (des roles que l IA a nommes sans les mettre au casting). Ce n'est pas
        # un degat de la restauration : le chiffre comparable est celui d'avant
        # (`_essais/_controler_hors_casting.py`). On l'affiche pour information.
        hors = conn.execute(
            'SELECT COUNT(*) FROM speaker_attribution WHERE book_id = ? '
            'AND speaker NOT IN (SELECT character_name FROM voices WHERE '
            'book_id = ?) AND speaker != \'narration\'',
            (identifiant, identifiant)).fetchone()[0]
        print('    livre %-3d %-32s %6d lignes, %d phrases hors casting '
              '(etat preexistant)' % (identifiant, titre[:32], relu, hors))
    conn.close()

    print('')
    print('  OK : la restauration remet les etiquettes d ORIGINE -- elle n en '
          'invente aucune.')
    print('  (les locuteurs hors casting sont un sujet de CASTING, pas de '
          'decoupage)')
    print('')
    print('  RETOUR ARRIERE : recopier %s sur data/%s'
          % (copie.name, BASE.name))
    print('  A FAIRE COTE LECTEUR : recharger la page.')
    print('  A NOTER : la copie d origine utilisee est %s (lecture seule).'
          % origine.name)
    print('=' * LARGEUR)
    return 0


if __name__ == '__main__':
    sys.exit(main())
