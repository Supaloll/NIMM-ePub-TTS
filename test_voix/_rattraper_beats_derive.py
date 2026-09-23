# -*- coding: utf-8 -*-
"""RATTRAPAGE : les beats perdus par la derive du compteur de citation ouverte.

POURQUOI CET OUTIL (23/09/2026). La migration des livres deja castes a utilise
un compteur de citation ouverte qui comptait les guillemets depuis le DEBUT DU
CHAPITRE : apres un passage lu a voix haute, tout le reste du chapitre etait
refuse. Mesure : **244 beats** refuses a tort, dont **200 sur les 9 livres
migres le 23/09** et 41 sur « 22/11/63 » (migre le 22/09).

Ces livres sont DEJA en mode dialogue : on ne peut pas les re-migrer (l'outil de
migration refuse, et il a raison — les index en base sont deja ceux du decoupage
fin). Cet outil-ci fait donc le geste inverse, et ce qu'il fait est simple :
**il remet au narrateur les morceaux qui sont des beats et qui sont restes a un
personnage**, en s'appuyant sur le compteur CORRIGE (par paragraphe).

PERIMETRE. Uniquement les livres reellement MIGRES (leur page a ete remappee) :
  - 8, 14, 15, 16, 17, 27, 33, 34, 35 : migres le 23/09/2026 ;
  - 28 (« 22/11/63 ») : migre le 22/09/2026, meme defaut.
Les livres 36 et 37 ne sont PAS concernes : ils ont ete castes directement en
mode dialogue (l'IA a etiquette le decoupage fin), il n'y a pas eu de migration.

DEUX FAMILLES, DEUX TRAITEMENTS (mesure du 23/09/2026 : 169 propres / 75 impurs) :
  - PROPRE : le morceau est de la narration pure (« Elle arretait les passants
    et criait : ») -> remis au narrateur. C'est ce que fait cet outil ;
  - IMPUR : le morceau commence par une minuscule, par » ou contient un » : sa
    tete appartient a une replique (« une seule, dit le Lucquois »). Le donner au
    narrateur ferait lire un mot de la replique par le narrateur -> traite par la
    regle R3, dans une session a part. IGNORES par defaut, donc.

USAGE :
    python test_voix/_rattraper_beats_derive.py                  (simulation)
    python test_voix/_rattraper_beats_derive.py --livres 34 33
    python test_voix/_rattraper_beats_derive.py --ecrire         (ECRIT)
    python test_voix/_rattraper_beats_derive.py --avec-impurs    (R3 inclus)
"""

import importlib.util
import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                          # noqa: E402
from modules.decoupage import (phrases_avec_positions,             # noqa: E402
                               introduit_une_replique, REGLE_DIALOGUE)

spec = importlib.util.spec_from_file_location(
    'mig', RACINE / 'test_voix' / '_migrer_index_dialogue.py')
mig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mig)

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
LARGEUR = 78
LIVRES_MIGRES = (8, 14, 15, 16, 17, 27, 28, 33, 34, 35)

# Marques de 2e personne. Presence = le morceau s'adresse a quelqu'un : c'est le
# signal qui sauve le cas du docteur d'Avrigny (tome 5) — « Si elle avait commis
# un second crime, je vous dirais : » — qui est DU DISCOURS du personnage, sans
# guillemet ouvrant. En narration a la troisieme personne, une adresse au « vous »
# hors citation est quasi inexistante ; dans un recit a la premiere personne, le
# « je » est partout et ne prouve RIEN (mesure : « Il m'a adresse un sourire en
# ajoutant : » est de la narration). Donc : deuxieme personne SEULE. « ton / ta /
# tes » sont EXCLUS : en roman, ce sont surtout le nom commun (« d'un ton sec »).
DEUXIEME_PERSONNE = re.compile(
    r"\b(tu|te|toi|vous|votre|vos)\b", re.IGNORECASE)


def _morceaux_a_corriger(texte, attributions):
    """(surs, avec_personne, impurs) : [(index, locuteur, texte)] a corriger.

    Un morceau est concerne s'il est un BEAT (le texte avant une citation : pas de
    « dedans, il introduit une replique, et le morceau suivant commence par «),
    qu'il appartient encore a un PERSONNAGE, et que le compteur CORRIGE (par
    paragraphe) ne le trouve PAS dans une citation ouverte.
    """
    morceaux = phrases_avec_positions(texte, REGLE_DIALOGUE)
    surs, avec_personne, impurs = [], [], []
    for index, locuteur in attributions:
        if locuteur in (None, 'narration') or index >= len(morceaux):
            continue
        _debut, _fin, morceau = morceaux[index]
        if '\u00ab' in morceau:
            continue
        if not introduit_une_replique(morceau):
            continue
        if index + 1 >= len(morceaux):
            continue
        if not morceaux[index + 1][2].lstrip().startswith('\u00ab'):
            continue
        if mig._citation_ouverte(texte, morceaux[index][0]):
            continue                      # vrai cas Lazarille : on n'y touche pas
        nu = morceau.strip()
        impur = (nu[:1].islower() or nu[:1] in ('\u00bb', '\u2014')
                 or '\u00bb' in nu)
        if impur:
            impurs.append((index, locuteur, nu))
        elif DEUXIEME_PERSONNE.search(nu.replace('\u2019', "'")):
            avec_personne.append((index, locuteur, nu))
        else:
            surs.append((index, locuteur, nu))
    return surs, avec_personne, impurs


def main():
    livres = []
    ecrire = False
    avec_impurs = False
    avec_personne_livre = False
    exemples = 4
    for position, argument in enumerate(sys.argv):
        if argument == '--livres':
            livres = [int(a) for a in sys.argv[position + 1:]
                      if a.isdigit()]
        elif argument == '--ecrire':
            ecrire = True
        elif argument == '--avec-impurs':
            avec_impurs = True
        elif argument == '--avec-personne':
            avec_personne_livre = True
        elif argument == '--exemples' and position + 1 < len(sys.argv):
            exemples = int(sys.argv[position + 1])
    if not livres:
        livres = list(LIVRES_MIGRES)

    conn = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)
    print('=' * LARGEUR)
    print(' RATTRAPAGE DES BEATS PERDUS PAR LA DERIVE DU COMPTEUR')
    print('=' * LARGEUR)
    print('  livres : %s' % ', '.join(str(i) for i in livres))
    print('  impurs : %s' % ('INCLUS (regle R3)'
                              if avec_impurs else 'ignores (session R3)'))
    print('  mode   : %s' % ('ECRITURE' if ecrire else 'simulation'))
    print('')

    travail, total_surs, total_personne, total_impurs = [], 0, 0, 0
    doutes, impurs_liste = [], []
    for identifiant in livres:
        ligne = mig._livre(conn, identifiant)
        if ligne is None:
            print('  livre %d inconnu.' % identifiant)
            continue
        if not ligne[3]:
            print('  livre %-3d %s : PAS en mode dialogue -- ignore (aucune '
                  'migration, donc aucune derive).' % (identifiant, ligne[1]))
            continue
        attributions = mig._attributions(conn, identifiant)
        chapitres = {c['index']: (c.get('text') or '') for c in get_chapters(
            str(BIBLIOTHEQUE / ligne[2]))}
        corrections, morceaux_par_chapitre = [], {}
        surs_livre = personne_livre = impurs_livre = 0
        exemples_livre = []
        for chapitre, lignes in sorted(attributions.items()):
            texte = chapitres.get(chapitre, '')
            if not texte:
                continue
            surs, avec_personne, impurs = _morceaux_a_corriger(texte, lignes)
            morceaux_par_chapitre[chapitre] = phrases_avec_positions(
                texte, REGLE_DIALOGUE)
            surs_livre += len(surs)
            personne_livre += len(avec_personne)
            impurs_livre += len(impurs)
            retenus = list(surs)
            if avec_personne_livre:
                retenus += avec_personne
            if avec_impurs:
                retenus += impurs
            for index, _locuteur, nu in retenus:
                corrections.append((chapitre, index))
                if len(exemples_livre) < exemples:
                    exemples_livre.append((chapitre, _locuteur, nu))
            for index, locuteur, nu in avec_personne:
                doutes.append((identifiant, chapitre, locuteur, nu))
            for index, locuteur, nu in impurs:
                impurs_liste.append((identifiant, chapitre, locuteur, nu))
        total_surs += surs_livre
        total_personne += personne_livre
        total_impurs += impurs_livre
        print('  livre %-3d %-34s surs %4d  1re/2e pers. %3d  impurs %3d'
              % (identifiant, ligne[1][:34], surs_livre, personne_livre,
                 impurs_livre))
        for chapitre, locuteur, nu in exemples_livre:
            print('        ex. ch.%-3d [%s] %s' % (chapitre, locuteur,
                                                     nu[:88]))
        if corrections:
            travail.append((identifiant, ligne[1], corrections,
                            morceaux_par_chapitre))

    print('')
    print('  TOTAL a remettre au narrateur : %d' % total_surs
          + (' + %d (1re/2e personne)' % total_personne
             if avec_personne_livre else '')
          + (' + %d impurs' % total_impurs if avec_impurs else ''))
    print('  LAISSES DE COTE -- 1re/2e personne (doute, regle R6) : %d'
          % (0 if avec_personne_livre else total_personne))
    print('  LAISSES DE COTE -- impurs (regle R3)                 : %d'
          % (0 if avec_impurs else total_impurs))
    print('  (les deux listes se relisent : ce sont les cas ou le morceau peut')
    print('   appartenir au personnage -- « je vous dirais : » du docteur')
    print('   d Avrigny, par exemple)')
    if doutes:
        print('')
        print('-' * LARGEUR)
        print(' LES %d MORCEAUX LAISSES POUR 2e PERSONNE -- a lire'
              % len(doutes))
        print('-' * LARGEUR)
        for identifiant, chapitre, locuteur, nu in doutes[:40]:
            print('  livre %-3d ch.%-3d [%s] %s'
                  % (identifiant, chapitre, locuteur[:20], nu[:80]))
    if impurs_liste:
        print('')
        print('-' * LARGEUR)
        print(' LES %d MORCEAUX IMPURS (regle R3) -- a lire'
              % len(impurs_liste))
        print('-' * LARGEUR)
        for identifiant, chapitre, locuteur, nu in impurs_liste[:40]:
            print('  livre %-3d ch.%-3d [%s] %s'
                  % (identifiant, chapitre, locuteur[:20], nu[:80]))
    conn.close()

    if not ecrire:
        print('')
        print('=' * LARGEUR)
        print(' SIMULATION : AUCUNE ecriture. (pour ecrire : --ecrire)')
        print('=' * LARGEUR)
        return 0
    return _ecrire(travail)


def _ecrire(travail):
    """Copie datee, ecriture des corrections, controles APRES."""
    if not travail:
        print('')
        print('  Rien a corriger : aucune ecriture.')
        return 0

    copie = mig._copie_datee(BASE)
    print('')
    print('  copie datee AVANT d ecrire : %s' % copie.name)

    conn = sqlite3.connect(str(BASE))
    conn.execute('PRAGMA busy_timeout = 20000')
    corriges = 0
    with conn:
        for identifiant, _titre, corrections, _morceaux in travail:
            conn.executemany(
                'UPDATE speaker_attribution SET speaker = ? WHERE book_id = ? '
                'AND chapter_index = ? AND sentence_idx = ?',
                [('narration', identifiant, chapitre, index)
                 for chapitre, index in corrections])
            corriges += len(corrections)
            # le nombre de repliques de chaque personnage a change : on recompte,
            # exactement comme l'outil de migration.
            conn.execute(
                'UPDATE voices SET line_count = (SELECT COUNT(*) FROM '
                'speaker_attribution WHERE book_id = voices.book_id AND '
                'speaker = voices.character_name) WHERE book_id = ?',
                (identifiant,))
    print('  ecrit : %d morceaux remis au narrateur' % corriges)

    print('')
    print('  CONTROLE APRES ECRITURE')
    souci_total = 0
    for identifiant, titre, _corrections, morceaux_par_chapitre in travail:
        detail = {chapitre: {'nouvelles': morceaux}
                  for chapitre, morceaux in morceaux_par_chapitre.items()}
        controle = mig.verifier(conn, identifiant, detail)
        restants = _restants(conn, identifiant)
        souci_total += len(controle['souci']) + restants
        print('    livre %-3d %-32s %6d lignes, mode %s, reste a corriger : %d'
              % (identifiant, titre[:32], controle['lignes'],
                 controle['mode_dialogue'], restants))
        for ligne in controle['souci'][:3]:
            print('        A REGARDER : %s' % ligne)
    conn.close()

    print('')
    if souci_total:
        print('  %d SOUCI(S) : voir ci-dessus, et la copie datee pour revenir '
              'en arriere.' % souci_total)
    else:
        print('  OK : chaque voix pointe sur une phrase qui existe, les '
              'locuteurs sont au casting,\n       et il ne reste aucun beat '
              'perdu par la derive.')
    print('')
    print('  RETOUR ARRIERE : recopier %s sur data/%s'
          % (copie.name, BASE.name))
    print('  A FAIRE COTE LECTEUR : recharger la page.')
    print('=' * LARGEUR)
    return 0 if not souci_total else 1


def _restants(conn, identifiant):
    """Combien de morceaux resteraient a corriger (relecture apres ecriture)."""
    ligne = mig._livre(conn, identifiant)
    attributions = mig._attributions(conn, identifiant)
    chapitres = {c['index']: (c.get('text') or '') for c in get_chapters(
        str(BIBLIOTHEQUE / ligne[2]))}
    restants = 0
    for chapitre, lignes in attributions.items():
        texte = chapitres.get(chapitre, '')
        if not texte:
            continue
        surs, _personne, _impurs = _morceaux_a_corriger(texte, lignes)
        restants += len(surs)
    return restants


if __name__ == '__main__':
    sys.exit(main())
