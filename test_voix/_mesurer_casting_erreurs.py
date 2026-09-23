# -*- coding: utf-8 -*-
"""LE CASTING IA SE TROMPE-T-IL BEAUCOUP ? -- mesure GRATUITE, sans appeler l'IA.

POURQUOI CET OUTIL (23/09/2026). Question de fond : faut-il donner au casting IA
plus de contexte (resume de scene, personnages presents, relations) pour qu'il
attribue mieux les voix ? Avant de construire quoi que ce soit, une evidence
manquait : **le taux d'erreur du casting, pris seul**, n'avait jamais ete mesure.

Cet outil le mesure SANS DEPENSER UN CENTIME, sur les etiquettes d'ORIGINE (la
copie d'avant migration, qui porte encore ce que l'IA a produit), et sur quatre
chapitres difficiles choisis :

  - Notre-Dame ch.55   (une longue lecture par un personnage, plusieurs voix)
  - Monte-Cristo T3 ch.8 (dialogue en tiret, Bertuccio qui raconte)
  - Dialogues desaccordes ch.9 (citation imbriquee, livre d'entretien)
  - Shantaram ch.6     (« Le narrateur » et « narration » dans un recit a la 1re personne)

IL COMPTE LES ERREURS **OBJECTIVES** -- celles qui ne dependent d'aucune
interpretation, donc acceptables comme verite sans lecture humaine :

  1. une REPLIQUE DONNEE AU NARRATEUR : le morceau est dans une ligne qui ouvre
     un dialogue (tiret, guillemet) et avant le guillemet fermant, et il est
     etiquette « narration » ;
  2. une INCISE SEULE DONNEE A UN PERSONNAGE : le morceau n'est rien d'autre
     qu'une incise de parole (« repondit Mahiette. ») et il est au personnage,
     alors que la consigne 8 du prompt dit « incise seule = narration » ;
  3. un TEXTE LU donne a un personnage : morceau sans guillemet, du meme
     locuteur que le precedent (bloc), au personnage (lettre, acte, testament) ;
  4. un LOCUTEUR HORS CASTING : un nom que l'IA a invente et qui n'est pas dans
     `voices` (la voix ne sera pas la bonne).

Sortie : par chapitre, le nombre de phrases, les erreurs par famille, le taux, et
les exemples a lire. Lecture seule, rien n'est ecrit, rien n'est facture.

Usage : python test_voix/_mesurer_casting_erreurs.py
"""

import importlib.util
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                          # noqa: E402
from modules.decoupage import (phrases_avec_positions,             # noqa: E402
                               REGLE_ACTUELLE, REGLE_DIALOGUE)
import main as nimm_app                                        # noqa: E402

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

# Les quatre chapitres difficiles : (livre, chapitre, pourquoi celui-la)
CHAPITRES = (
    (34, 55, 'longue lecture par un personnage, plusieurs voix'),
    (14, 8, 'dialogue en tiret, Bertuccio qui raconte'),
    (18, 9, 'citation imbriquee, livre d entretien'),
    (33, 6, '« Le narrateur » et « narration » en recit a la 1re personne'),
)


def _source():
    """La copie d'AVANT migration : elle porte encore le casting d'origine."""
    copies = sorted((RACINE / 'data').glob('nimm_epub.db.bak_avant_dialogue_*'))
    return copies[0] if copies else BASE


def _ligne_et_position(texte, position):
    gauche = texte.rfind('\n', 0, position)
    gauche = 0 if gauche < 0 else gauche + 1
    droite = texte.find('\n', position)
    droite = len(texte) if droite < 0 else droite
    return texte[gauche:droite], position - gauche


def _dans_la_replique(ligne, position):
    if ligne.lstrip()[:1] not in OUVREURS:
        return False
    fermi = len(ligne)
    for caractere in FERMANTS:
        index = ligne.find(caractere)
        if index >= 0:
            fermi = min(fermi, index)
    return True if fermi == len(ligne) else position < fermi


def analyser_chapitre(conn, identifiant, chapitre, exemples=6):
    """(titre, bilan) des erreurs OBJECTIVES d'un chapitre. Lecture seule."""
    livre = conn.execute('SELECT title, filename, COALESCE(decoupe_dialogue, 0) '
                         'FROM books WHERE id = ?', (identifiant,)).fetchone()
    if livre is None:
        return None
    titre, fichier, dialogue = livre
    connus = {r[0] for r in conn.execute(
        'SELECT character_name FROM voices WHERE book_id = ?', (identifiant,))}
    texte = None
    for ch in get_chapters(str(BIBLIOTHEQUE / fichier)):
        if ch['index'] == chapitre:
            texte = ch.get('text') or ''
            break
    if not texte:
        return None
    regle = REGLE_DIALOGUE if dialogue else REGLE_ACTUELLE
    morceaux = phrases_avec_positions(texte, regle)
    locuteurs = {r[0]: r[1] for r in conn.execute(
        'SELECT sentence_idx, speaker FROM speaker_attribution WHERE book_id = ? '
        'AND chapter_index = ?', (identifiant, chapitre))}

    bilan = {'phrases': len(morceaux), 'replique_au_narrateur': [],
             'incise_au_personnage': [], 'texte_lu': [], 'hors_casting': []}
    for index, (debut, _fin, morceau) in enumerate(morceaux):
        locuteur = locuteurs.get(index)
        if locuteur is None:
            continue
        nu = morceau.strip()
        ligne, position = _ligne_et_position(texte, debut)
        if locuteur == 'narration':
            if _dans_la_replique(ligne, position):
                bilan['replique_au_narrateur'].append((index, nu))
            continue
        if locuteur not in connus:
            bilan['hors_casting'].append((index, '%s : %s' % (locuteur,
                                                              nu[:60])))
        if '\u00ab' not in morceau and nimm_app._est_incise_seule(nu):
            bilan['incise_au_personnage'].append((index, nu))
            continue
        if '\u00ab' in morceau or '\u00bb' in morceau:
            continue
        if index > 0 and locuteurs.get(index - 1) == locuteur:
            precedent = morceaux[index - 1][2]
            ligne_avant, position_avant = _ligne_et_position(
                texte, morceaux[index - 1][0])
            if '\u00ab' not in precedent and '\u00bb' not in precedent \
                    and not _dans_la_replique(ligne_avant, position_avant) \
                    and not _dans_la_replique(ligne, position):
                bilan['texte_lu'].append((index, nu))
    return titre, bilan


def main():
    source = _source()
    print('=' * LARGEUR)
    print(' LE CASTING IA SE TROMPE-T-IL BEAUCOUP ? -- mesure gratuite')
    print('  etiquettes : %s' % source.name)
    print('  (celles de l IA, avant toute regle de migration)')
    print('  4 chapitres difficiles -- aucune ecriture, aucun appel payant')
    print('=' * LARGEUR)
    conn = sqlite3.connect('file:' + source.as_posix() + '?mode=ro', uri=True)

    total_phrases = total_erreurs = 0
    total_discutables = 0
    for identifiant, chapitre, pourquoi in CHAPITRES:
        resultat = analyser_chapitre(conn, identifiant, chapitre)
        if resultat is None:
            print('')
            print('  livre %d ch.%d : introuvable.' % (identifiant, chapitre))
            continue
        titre, bilan = resultat
        dures = len(bilan['replique_au_narrateur']) + len(bilan['hors_casting'])
        discutables = len(bilan['incise_au_personnage'])
        a_lire = len(bilan['texte_lu'])
        total_phrases += bilan['phrases']
        total_erreurs += dures
        total_discutables += discutables
        print('')
        print('-' * LARGEUR)
        print(' livre %d (%s) ch.%d' % (identifiant, titre[:38], chapitre))
        print('   (%s)' % pourquoi)
        print('-' * LARGEUR)
        print('  %d phrases dans le chapitre' % bilan['phrases'])
        print('  ERREURS DURES : %d  (%.2f %%)   <- on ne peut pas les defendre'
              % (dures, 100.0 * dures / bilan['phrases']
                 if bilan['phrases'] else 0))
        print('  a discuter    : %d  (la consigne 8 dit non, l oreille tranche)'
              % discutables)
        print('  a LIRE        : %d  (peut etre du dialogue continu : pas un'
              ' compte)' % a_lire)
        for cle, libelle in (
                ('replique_au_narrateur', 'repliques donnees au narrateur'),
                ('hors_casting', 'locuteurs hors casting'),
                ('incise_au_personnage',
                 'incises seules donnees a un personnage'),
                ('texte_lu', 'a LIRE -- morceau du meme locuteur que le '
                             'precedent')):
            liste = bilan[cle]
            if not liste:
                continue
            print('    %-42s %4d' % (libelle, len(liste)))
            for index, extrait in liste[:6]:
                print('        #%-4d %s' % (index, extrait[:66]))
    conn.close()

    print('')
    print('=' * LARGEUR)
    if total_phrases:
        print(' TOTAL : %d phrases' % total_phrases)
        print('   erreurs DURES (replique au narrateur, hors casting) : %d (%.2f %%)'
              % (total_erreurs, 100.0 * total_erreurs / total_phrases))
        print('   a discuter (incise seule chez un personnage)        : %d (%.2f %%)'
              % (total_discutables,
                 100.0 * total_discutables / total_phrases))
    print('')
    print(' COMMENT LIRE CE CHIFFRE')
    print('  Le taux qui compte est celui des ERREURS DURES : une replique lue')
    print('  par le narrateur, ou un locuteur que le casting ne connait pas.')
    print('  moins de 1 % : le casting est bon -- le contexte narratif n est PAS')
    print('     le levier. L energie va plutot au balisage des repliques en')
    print('     tiret (gratuit) et a un prompt qui apprend les cinq formes ;')
    print('  plus de 3 %  : une verite de reference (lecture humaine) sur ces')
    print('     chapitres vaut le coup, pour savoir quel type d erreur domine.')
    print('  La ligne « a LIRE » n est PAS un compte : elle contient du dialogue')
    print('  continu (un personnage qui enchaine ses repliques), qui n est pas une')
    print('  erreur. Elle est la pour la lecture, pas pour le jugement.')
    print('=' * LARGEUR)
    return 0


if __name__ == '__main__':
    sys.exit(main())
