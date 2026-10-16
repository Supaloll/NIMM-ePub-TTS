# -*- coding: utf-8 -*-
"""LES SURNOMS DE POV : les PROPOSER, puis les ECRIRE -- NIMM ePub (15/10/2026).

POURQUOI. Dans *Le Trone de Fer*, certains chapitres portent un SURNOM au lieu d'un
prenom : « LE PROPHETE », « LE NOYE », « LA FILLE DE LA SEICHE », « SCHLINGUE »,
« Le lord perdu », « Le domestique du marchand ». La carte des POV ne peut pas les
deviner, et le texte ne le dit pas toujours (mesure du 15/10/2026 : « Quentyn »
apparait 48 fois dans le chapitre « Le domestique du marchand », « Griff » 54 fois
dans « Le lord perdu » -- mais « Theon » UNE seule fois dans les chapitres
« Schlingue »). D'ou la table `pov_surnoms` (voir `main.py`), et cet outil qui la
remplit.

COMMENT IL PROCEDE, ET DANS QUEL ORDRE (l'ordre retenu avec Laurent) :
  1. LE TEXTE D'ABORD -- gratuit et VERIFIABLE : on compte, DANS le chapitre au
     surnom, combien de fois chaque personnage DU CASTING est nomme. Au-dessus du
     seuil (`--seuil`, 3 par defaut), c'est une proposition SOLIDE, avec sa preuve
     (le compte et un extrait du chapitre) ;
  2. sinon, des PISTES : les noms propres les plus frequents du chapitre, hors
     debut de phrase -- a confirmer a la main, jamais appliquees toutes seules ;
  3. LE LLM en dernier recours (pas dans cet outil) : il devra CITER l'extrait qui
     prouve, et rien ne sera applique sans validation.

CE QU'IL ECRIT. RIEN par defaut : il AFFICHE. Pour ecrire, il faut le demander
ligne par ligne, en francais clair :
    python test_voix/_proposer_surnoms_pov.py --livre 12 --ecrire "LE PROPHETE=Aeron"
Il refuse une ligne dont le personnage n'est PAS au casting (sinon la narration ne
changerait pas d'un iota), il fait une COPIE DATEE de la base avant d'ecrire, et il
RELIT ce qu'il a ecrit. Rappel : la table est a la portee de la SAGA quand le livre
en a une -- une ligne ecrite une fois sert donc tous les tomes.

Usage :
  python test_voix/_proposer_surnoms_pov.py                     (les tomes du dossier par defaut)
  python test_voix/_proposer_surnoms_pov.py --livre 12          (un livre de la bibliotheque)
  python test_voix/_proposer_surnoms_pov.py "chemin.epub"       (un fichier precis)
  python test_voix/_proposer_surnoms_pov.py --livre 12 --ecrire "SCHLINGUE=Theon_Greyjoy"
"""

import datetime
import re
import shutil
import sqlite3
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import get_chapters                            # noqa: E402
from modules import pov                                              # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
DOSSIER_PAR_DEFAUT = Path(r'D:\Livres Epub\Le Trone de Fer')
RAPPORT = Path(__file__).resolve().parent / 'sortie_surnoms_pov.txt'

# Au-dessus de ce nombre de mentions DANS LE CHAPITRE, un nom du casting est tenu
# pour une proposition solide : mesure du 15/10/2026 -- 48 et 54 pour les cas
# solides, 1 pour le cas ou le texte se tait. 3 separe proprement les deux.
SEUIL_PREUVE = 3
# Une piste (nom propre frequent, hors debut de phrase) doit apparaitre au moins
# deux fois pour valoir la peine d'etre lue.
SEUIL_PISTE = 2

# Ce qu'on refuse d'appeler un nom propre quand on cherche des pistes : les memes
# listes que la reconnaissance, plus les mots francais qui ouvrent une phrase.
MOTS_A_ECARTER = pov.MOTS_GENERIQUES | pov.PAS_UN_PRENOM | {
    'MONSIEUR', 'MADAME', 'SEIGNEUR', 'LORD', 'LADY', 'SER', 'MESTRE', 'PRINCE',
    'PRINCESSE', 'ROI', 'REINE', 'CHEVALIER', 'CAPITAINE', 'MERE', 'PERE',
    'DIEUX', 'SEPT', 'MUR', 'NORD', 'SUD', 'EST', 'OUEST', 'HIVER', 'FER',
    'TOUT', 'RIEN', 'PLUS', 'MOINS', 'BIEN', 'MAL', 'OUI', 'NON', 'POURQUOI',
    'COMME', 'QUAND', 'ALORS', 'APRES', 'AVANT', 'DEPUIS', 'PENDANT', 'ENCORE',
}

_RE_MOT_CAPITALISE = re.compile(r'(?<![A-Za-z\u00c0-\u024f])([A-Z\u00c0-\u00de]'
                                r'[a-z\u00e0-\u00ff\u0153\u2019\'-]{2,})')


def _mentions(texte, motif):
    """Combien de fois ce nom est NOMME dans ce texte (bordures de mot)."""
    if len(motif) < 3:
        return 0
    return len(re.findall(r'(?<![A-Za-z\u00c0-\u024f])' + re.escape(motif)
                          + r'(?![A-Za-z\u00c0-\u024f])', texte))


def _est_debut_de_phrase(texte, position):
    """Le mot commence-t-il une phrase ? (il serait alors capitalise par nature)"""
    avant = texte[:position].rstrip()
    if not avant:
        return True
    return avant[-1] in '.!?\u00ab\u2014:;\n'


def preuves_par_casting(texte, personnes):
    """Les personnages du CASTING nommes dans ce chapitre -> [(mentions, nom)].

    C'est la PREUVE (gratuite, verifiable) : on essaie le PRENOM (« Theon ») et le
    nom complet sans underscore (« Theon Greyjoy »), et on garde le meilleur des
    deux -- un personnage peut n'etre nomme que par son nom de famille, ou que par
    son prenom.
    """
    trouves = []
    for personne in {p['nom']: p for p in personnes.values()}.values():
        nom = personne['nom']
        essais = [nom.split('_')[0], nom.replace('_', ' ')]
        nombre = max(_mentions(texte, e) for e in essais)
        if nombre:
            trouves.append((nombre, nom))
    trouves.sort(reverse=True)
    return trouves


def pistes_par_noms_propres(texte):
    """Les noms propres qui reviennent dans le chapitre -> [(mentions, mot)].

    Ce n'est PAS une preuve, et l'outil le dit : ce sont les mots Capitalises hors
    debut de phrase, hors articles, hors titres de noblesse. A confirmer a la main.
    """
    compte = {}
    for trouve in _RE_MOT_CAPITALISE.finditer(texte):
        mot = trouve.group(1)
        if _est_debut_de_phrase(texte, trouve.start()):
            continue
        cle = pov.normaliser(mot)
        if cle in MOTS_A_ECARTER or len(cle) < 4:
            continue
        compte[mot] = compte.get(mot, 0) + 1
    return sorted(((nombre, mot) for mot, nombre in compte.items()
                   if nombre >= SEUIL_PISTE), reverse=True)[:5]


def _chapitres_a_relier(chemin, personnes):
    """Les chapitres dont le narrateur n'est PAS identifie, avec leurs indices.

    Deux familles, et l'outil les montre toutes les deux :
      - le titre porte un SURNOM (« SCHLINGUE », « LE PROPHETE ») : il n'est pas au
        casting, donc le chapitre n'est pas relie ;
      - le titre ne dit RIEN et la premiere ligne non plus (« Le lord perdu »,
        « Le domestique du marchand ») : aucune reconnaissance possible.
    """
    sortie = []
    chapitres = get_chapters(str(chemin))
    lignes = pov.carte_du_livre(chemin, personnes)
    for ligne, chapitre in zip(lignes, chapitres):
        if ligne['personnage']:
            continue
        texte = chapitre.get('text') or ''
        sortie.append({
            'index':   ligne['index'],
            'titre':   ligne['titre'],
            'surnom':  ligne['candidat'] or '',
            'debut':   ligne['debut'],
            'preuves': preuves_par_casting(texte, personnes) if personnes else [],
            'pistes':  pistes_par_noms_propres(texte) if not personnes else [],
        })
    return sortie


def main():
    args = sys.argv[1:]
    if '--aide' in args or '--help' in args or '-h' in args:
        print(__doc__)
        return 0

    # --- Les options -------------------------------------------------------
    identifiant = None
    a_ecrire = []
    chemins = []
    i = 0
    while i < len(args):
        if args[i] == '--livre' and i + 1 < len(args):
            try:
                identifiant = int(args[i + 1])
            except ValueError:
                print('Usage : --livre <numero du livre>')
                return 1
            i += 2
            continue
        if args[i] == '--ecrire' and i + 1 < len(args):
            a_ecrire.append(args[i + 1])
            i += 2
            continue
        if args[i].startswith('--'):
            print('Option inconnue : %s (voir --aide)' % args[i])
            return 1
        chemins.append(args[i])
        i += 1

    conn = None
    if BASE.exists():
        conn = sqlite3.connect(str(BASE))
        conn.row_factory = sqlite3.Row
    livres = {}
    if conn is not None:
        for ligne in conn.execute('SELECT id, title, filename FROM books'):
            livres[ligne['filename']] = (BIBLIOTHEQUE / ligne['filename'],
                                         ligne['title'], ligne['id'])

    # --- Ce qu'on regarde --------------------------------------------------
    cibles = []
    if identifiant is not None:
        if conn is None:
            print('La base est introuvable : %s' % BASE)
            return 1
        trouve = _livre_de_la_bibliotheque(conn, identifiant)
        if not trouve:
            print('Livre %d introuvable dans la base.' % identifiant)
            return 1
        cibles.append(trouve)
    elif chemins:
        for chemin in chemins:
            info = livres.get(Path(chemin).name)
            cibles.append(info if info else (Path(chemin), '', None))
    else:
        if not DOSSIER_PAR_DEFAUT.exists():
            print('Dossier introuvable : %s' % DOSSIER_PAR_DEFAUT)
            print('Donne un epub en argument, ou --livre <numero>.')
            return 1
        for chemin in sorted(DOSSIER_PAR_DEFAUT.glob('*.epub')):
            info = livres.get(chemin.name)
            cibles.append(info if info else (chemin, '', None))

    # --- Le rapport (et les propositions) ----------------------------------
    journal = ['LA TABLE DES SURNOMS DE POV - NIMM ePub',
               '(%s)  lecture seule, sauf si --ecrire est demande'
               % datetime.date.today().strftime('%d/%m/%Y'), '']
    total_propositions = 0
    for chemin, titre, book_id in cibles:
        personnes = (pov.personnages_du_livre(conn, book_id)
                     if (conn is not None and book_id) else {})
        total_propositions += _afficher_cible(chemin, titre, personnes, journal)

    RAPPORT.write_text('\n'.join(journal), encoding='utf-8')

    print('')
    print('-' * 74)
    print(' %d proposition(s) solide(s) : mention >= %d dans le chapitre.'
          % (total_propositions, SEUIL_PREUVE))
    print(' Detail complet, chapitre par chapitre : %s' % RAPPORT.name)
    if not a_ecrire:
        print(' RIEN n a ete ecrit. Pour ecrire un surnom VALIDE a la main :')
        print('   python test_voix/_proposer_surnoms_pov.py --livre <n>'
              ' --ecrire "SURNOM=Personnage"')
        if conn is not None:
            conn.close()
        return 0

    # --- L'ecriture (copie datee, refus, relecture) ------------------------
    if identifiant is None:
        print('')
        print(' Pour ECRIRE, il faut NOMMER le livre : --livre <numero> --ecrire ...')
        if conn is not None:
            conn.close()
        return 1
    chemin, titre, book_id = cibles[0]
    personnes = pov.personnages_du_livre(conn, book_id)
    print('')
    print('=== ECRITURE dans le livre %d (%s) ===' % (book_id, titre or '?'))
    if not personnes:
        print('   REFUSE : ce livre n a AUCUN casting. Un surnom doit pointer sur un')
        print('   personnage du casting, sinon la narration ne changerait pas d un iota.')
        conn.close()
        return 1
    ecrits = _ecrire(conn, book_id, a_ecrire, personnes)
    conn.close()
    if ecrits:
        print('')
        print(' %d surnom(s) ecrit(s), portee %s.' % (ecrits, 'saga ou livre'))
        print(' Recharge la page du lecteur (F5) : la carte des POV est calculee a la')
        print(' demande, donc elle en tient compte TOUT DE SUITE (aucun redemarrage).')
    return 0


def _afficher_cible(chemin, titre, personnes, journal, detail=True):
    """Affiche les chapitres a relier, RANGES EN TROIS FAMILLES. Renvoie le nombre de
    propositions solides.

    POURQUOI TROIS FAMILLES (15/10/2026) : la liste brute est tres longue (tous les
    chapitres d'un livre pas encore caste), et 90 % de ce qu'elle porte n'est PAS du
    travail a faire :
      - les SURNOMS (plusieurs mots : « LE NOYE », « Le lord perdu ») : c'est LA liste
        a relier -> detail complet, avec les preuves ;
      - les PRENOMS (un seul mot : « BRAN ») : ils seront reconnus TOUT SEULS des que
        le livre sera caste -> un simple compte ;
      - les TITRES MUETS (aucun candidat) : pages de garde, remerciements -> un compte,
        et les premiers pour qu'on les reconnaisse.
    """
    a_relier = _chapitres_a_relier(chemin, personnes)
    surnoms = [c for c in a_relier if c['surnom'] and ' ' in c['surnom']]
    prenoms = [c for c in a_relier if c['surnom'] and ' ' not in c['surnom']]
    muets   = [c for c in a_relier if not c['surnom']]

    entete = '=== %s%s ===' % (chemin.name, ('   [' + titre + ']') if titre else '')
    journal.append(entete)
    etat = (('casting : %d personnages -- les propositions viennent du TEXTE'
             % len(personnes)) if personnes
            else 'casting : AUCUN (livre pas encore caste) -- ce ne sont que des PISTES')
    journal.append('   ' + etat)
    if detail:
        print('')
        print(entete)
        print('   ' + etat)
    if not a_relier:
        journal.append('   aucun chapitre a relier')
        if detail:
            print('   aucun chapitre a relier')
        return 0

    # --- 1. LES SURNOMS : le travail a faire, en detail --------------------
    propositions = 0
    if surnoms:
        titre_famille = '   --- %d SURNOM(S) A RELIER ---' % len(surnoms)
        journal.append(titre_famille)
        if detail:
            print(titre_famille)
    for item in surnoms:
        tete = '   ch.%-3d %-30s surnom : %s' % (item['index'],
                                                 item['titre'][:30], item['surnom'])
        journal.append(tete)
        if detail:
            print(tete)
        if item['preuves']:
            fort = [(n, m) for n, m in item['preuves'] if n >= SEUIL_PREUVE]
            ligne = ('        preuves (texte) : %s'
                     % ' | '.join('%s (%d)' % (m, n) for n, m in item['preuves'][:3]))
            if fort:
                propositions += 1
                ligne += ('\n        >>> PROPOSITION : %s = %s'
                          % (item['surnom'], fort[0][1]))
        elif item['pistes']:
            ligne = ('        pistes (a verifier, PAS une preuve) : %s'
                     % ' | '.join('%s (%d)' % (m, n) for n, m in item['pistes']))
        else:
            ligne = '        rien : le texte ne nomme personne dans ce chapitre'
        journal.append(ligne)
        if detail:
            print(ligne)

    # --- 2. LES PRENOMS : reconnus tout seuls, des que le livre sera caste --
    if prenoms:
        compte = {}
        for item in prenoms:
            compte[item['surnom']] = compte.get(item['surnom'], 0) + 1
        ordonne = sorted(compte.items(), key=lambda x: (-x[1], x[0]))
        ligne = ('   %d chapitres a PRENOM (reconnus tout seuls des que le livre sera'
                 ' caste -- aucune ligne a ecrire) : %s'
                 % (len(prenoms), ', '.join('%s %d' % (n, k) for n, k in ordonne[:12])))
        journal.append(ligne)
        if detail:
            print(ligne)

    # --- 3. LES TITRES MUETS : pages de garde, notes, resumes --------------
    if muets:
        ligne = ('   %d chapitre(s) SANS candidat (pages de garde, notes, resumes) : %s'
                 % (len(muets),
                    ' ; '.join('ch.%d %s' % (c['index'], c['debut'][:26])
                               for c in muets[:6])))
        journal.append(ligne)
        if detail:
            print(ligne)
    return propositions


def _livre_de_la_bibliotheque(conn, identifiant):
    """Le livre de la bibliotheque : (chemin, titre, identifiant)."""
    ligne = conn.execute('SELECT title, filename FROM books WHERE id = ?',
                         (identifiant,)).fetchone()
    if not ligne:
        return None
    return BIBLIOTHEQUE / ligne[1], ligne[0], identifiant


def _portee_d_ecriture(conn, book_id):
    """Ou ecrire les surnoms : la portee de la SAGA si le livre en a une, sinon lui.

    Les tomes d'une saga partagent leur casting : une ligne ecrite une fois a la
    portee de la saga sert donc les quinze tomes, au lieu de quinze fois la meme.
    """
    portees = pov.portees(conn, book_id)
    for candidat in portees:
        if candidat.startswith('saga:'):
            return candidat
    return portees[0] if portees else ('livre:%d' % book_id)


def _ecrire(conn, book_id, paires, personnes):
    """Ecrit les surnoms demandes. Copie datee AVANT, refus, relecture APRES.

    `paires` : liste de « SURNOM=Personnage » dictee par Laurent. Le nom du
    personnage est RAPPROCHE du casting comme un titre de chapitre : « Theon »
    trouve donc « Theon_Greyjoy », et un nom qui n'est pas au casting est REFUSE
    (la narration ne changerait pas d'un iota : mieux vaut le dire tout de suite).
    """
    portee = _portee_d_ecriture(conn, book_id)
    retenues = []
    for paire in paires:
        if '=' not in paire:
            print('   REFUSE (format attendu SURNOM=Personnage) : %s' % paire)
            continue
        surnom, recherche = paire.split('=', 1)
        surnom = surnom.strip()
        personne = pov.rapprocher(pov.normaliser(recherche), personnes)
        if not surnom or not personne:
            print('   REFUSE (pas au casting) : %s' % paire)
            continue
        retenues.append((surnom, personne['nom']))
    if not retenues:
        print('   Rien a ecrire.')
        return 0

    date = datetime.datetime.now().strftime('%Y%m%d')
    copie = BASE.with_name(BASE.name + '.bak_avant_surnoms_' + date)
    if BASE.exists() and not copie.exists():
        shutil.copy(BASE, copie)
        print('   copie datee de la base : %s' % copie.name)
    # La table peut ne pas exister encore (elle nait au demarrage du SERVEUR) : on la
    # cree par LA MEME fonction que lui (`modules/pov.py`), jamais par une copie du
    # SQL, sinon les deux definitions deriveraient.
    pov.creer_table_surnoms(conn)
    for surnom, nom in retenues:
        conn.execute(
            'INSERT INTO pov_surnoms (portee, surnom, canonical_name, source) '
            'VALUES (?, ?, ?, ?) '
            'ON CONFLICT(portee, surnom) DO UPDATE SET '
            'canonical_name = excluded.canonical_name, '
            "source = excluded.source, ajoute_le = datetime('now')",
            (portee, surnom, nom, 'main'))
        print('   ECRIT : %s -> %s   (portee %s)' % (surnom, nom, portee))
    conn.commit()

    # RELECTURE : on ne croit pas l'ecriture sur parole.
    for ligne in conn.execute(
            'SELECT surnom, canonical_name, source FROM pov_surnoms '
            'WHERE portee = ? ORDER BY surnom', (portee,)):
        print('   en base : %-28s -> %-24s (%s)'
              % (ligne[0], ligne[1], ligne[2]))
    return len(retenues)


if __name__ == '__main__':
    sys.exit(main())
