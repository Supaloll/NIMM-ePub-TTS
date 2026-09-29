# -*- coding: utf-8 -*-
"""Bascule les voix KYUTAI d'un livre vers leurs jumelles QWEN (moteur Qwen3-TTS).

OBJECTIF (Laurent, 26/09/2026) : garder les MEMES voix -- meme extrait source,
donc meme timbre et meme prenom -- mais les faire lire par Qwen3-TTS au lieu de
Kyutai. C'est possible parce que les deux moteurs clonent **les memes 35
enregistrements** (verifie le 26/09/2026 : les 35 identifiants du catalogue
Kyutai sont exactement les 35 references de la garde-robe Qwen) :

    kyutai:10087_11650_000028-0002  ->  qwen:10087_11650_000028-0002

Depuis le 29/09/2026, le script accepte `--famille` (defaut `kyutai`) : la
memе mecanique sert a basculer les jumelles **Pocket** ou **NeuTTS** (memes
identifiants d'extraits, ex. `pocket:Homme001` -> `qwen:Homme001`). Le refus
d'ecrire sans jumelle protege les trois familles.

Un identifiant SANS jumelle fait REFUSER l'ecriture : on ne distribue jamais
une voix qui n'existe pas chez le moteur.

Depuis le 29/09/2026, le script bascule AUSSI le NARRATEUR du livre
(`books.narrator_voice`) : c'est un AUTRE champ, il ne suit pas la table
`voices`. Deux livres (27 et 35) avaient un narrateur Kyutai -- sans ce
traitement, ils s'arreteraient (503) le jour ou le moteur Kyutai est eteint.

CE QUI NE CHANGE PAS : les prenoms, les etoiles, les annotations d'ecoute et
les verrous. Une voix verrouillee est basculee COMME LES AUTRES (le verrou
protege d'un re-cast automatique, il n'interdit pas de changer de moteur a la
main) ; le personnage reste verrouille sur sa voix.

SECURITE : rapport seul par defaut (base en lecture seule). Avec --ecrire, la
base est COPIEE (fichier date, annonce) avant toute modification, et cette
copie suffit a revenir en arriere.

Usage :
    python test_voix/_basculer_voix_kyutai_vers_qwen.py            # rapport
    python test_voix/_basculer_voix_kyutai_vers_qwen.py --livre 34
    python test_voix/_basculer_voix_kyutai_vers_qwen.py --ecrire
"""

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(RACINE))

from modules.tts import QWEN_VOICES  # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
DOSSIER_VOIX = RACINE / 'qwen_tts_service' / 'voix'
# Suffixes de fichiers de reference RECONNUS PAR LE SERVICE (meme liste que
# `SUFFIXES_FICHIERS` de `qwentts_service/servir_qwentts_cpp.py`) : les NOTRES
# (`..._enhanced_reference.wav` : 35 extraits communs avec Kyutai) et ceux des
# voix clonees par NIMM Voix (`..._reference.wav` : 94 Kokoro + 28 « Decoupage
# OK », arrives le 28/09/2026). CORRIGE le 29/09/2026 : un seul suffixe etait
# connu, donc les 122 voix cloncees etaient invisibles pour ce script.
SUFFIXE = ('_enhanced_reference.wav', '_reference.wav')
COLONNE = 'voice_id'


def extraits_du_moteur():
    """Les identifiants d'extraits REELLEMENT presents chez le moteur.

    On lit le dossier que le SERVICE scanne (`qwen_tts_service/voix/`), avec les
    DEUX suffixes qu'il reconnait (`_enhanced_reference.wav` : nos 35 extraits
    Kyutai ; `_reference.wav` : les 94 Kokoro et 28 « Decoupage OK » arrives le
    28/09/2026, soit 122 fichiers).

    CORRIGE LE 29/09/2026 : ce script ne connaissait que le PREMIER suffixe, donc
    `pocket:Homme001` (fichier `Homme001_reference.wav`) etait declare « sans
    jumelle » a tort -- et le danger etait SILENCIEUX, parce que le COMPTE
    tombait juste (157 fichiers au total = 35 + 122). Une voix utilisable
    s'appelait donc « Homme001_reference.wav » dans les yeux du script.
    """
    presents = set()
    if DOSSIER_VOIX.is_dir():
        for fichier in DOSSIER_VOIX.glob('*.wav'):
            nom = fichier.name
            for suffixe in SUFFIXE:
                if nom.endswith(suffixe):
                    nom = nom[:-len(suffixe)]
                    break
            presents.add(nom)
    return presents


def catalogue_qwen():
    """Les voix `qwen:` que le LECTEUR propose (lues dans modules/tts.py).

    Import direct et non analyse de texte : `QWEN_VOICES` est CONSTRUIT a partir
    de `KYUTAI_VOICES` dans le module, donc il n'existe aucune ligne
    `{"id": "qwen:..."}` a lire dans le fichier.
    """
    return {v['id'] for v in QWEN_VOICES}


def jumelle_de(voix, extraits, catalogue):
    """La voix Qwen qui remplace une voix Kyutai, ou None si elle manque."""
    identifiant = voix.split(':', 1)[1]
    candidate = 'qwen:' + identifiant
    if identifiant in extraits and candidate in catalogue:
        return candidate
    return None


ANNOTATIONS = RACINE / 'data' / 'annotations_voix.json'


def notes_du_fichier():
    """Les notes d'ecoute de Laurent (data/annotations_voix.json), ou {}."""
    if not ANNOTATIONS.exists():
        return {}
    try:
        donnees = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))
        return donnees if isinstance(donnees, dict) else {}
    except Exception:
        return {}


def notes_a_recopier(voix_basculees, extraits, catalogue, famille='kyutai'):
    """{cle Kyutai: cle Qwen} des notes d'ecoute a DOUBLER (ajout du 29/09/2026).

    Pourquoi : les notes de Laurent sont lues PAR IDENTIFIANT de voix
    (`annotations.get(ident)`, modules/voice_casting.py). Un personnage qui
    passe de `kyutai:X` a `qwen:X` garde son timbre mais PERDRAIT ses notes
    (etoiles, age, timbre, debit, remarque) dans la fenetre « Ecouter les voix ».
    On DOUBLE donc la cle : les notes `kyutai:` restent en place (aucune perte
    si on revient en arriere) et `qwen:` recoit la MEME fiche.

    `voix_basculees` : les voix REELLEMENT traitees par ce passage (avec
    `--livre`, on ne touche pas aux notes des autres livres).
    """
    notes = notes_du_fichier()
    a_recopier = {}
    for cle in notes:
        if not cle.startswith(famille + ':') or cle not in voix_basculees:
            continue
        jumelle = jumelle_de(cle, extraits, catalogue)
        if jumelle is None:
            continue            # pas de voix Qwen pour cet extrait : on n'y touche pas
        if jumelle in notes:
            continue            # deja notee chez Qwen : on ne l'ecrase pas
        a_recopier[cle] = jumelle
    return a_recopier


def main():
    analyseur = argparse.ArgumentParser(
        description="Bascule les voix Kyutai vers leurs jumelles Qwen.")
    analyseur.add_argument('--famille', default='kyutai',
                           choices=('kyutai', 'pocket', 'neutts'),
                           help="famille de depart (defaut kyutai)")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="ne traiter qu'un livre (numero)")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment (copie datee de la base d'abord)")
    options = analyseur.parse_args()

    # LA FAMILLE DE DEPART (29/09/2026) : `kyutai` par defaut, et aussi `pocket`
    # ou `neutts`, dont les extraits portent les MEMES identifiants que leurs
    # jumelles Qwen (`pocket:Homme001` -> `qwen:Homme001`). La liste est FERMEE
    # (argparse) : aucune valeur libre n'entre dans la requete SQL.
    famille = options.famille

    if not BASE.exists():
        print('ERR : base introuvable : %s' % BASE)
        return 1

    extraits = extraits_du_moteur()
    catalogue = catalogue_qwen()
    print('')
    print('=' * 70)
    print('VOIX %s  ->  VOIX QWEN (memes extraits, autre moteur)'
          % famille.upper())
    print('=' * 70)
    print('extraits presents chez le moteur : %d' % len(extraits))
    print('voix Qwen proposees par le lecteur : %d' % len(catalogue))
    print('base : %s   (%s)' % (BASE.name,
                               'ECRITURE' if options.ecrire else 'rapport seul'))

    connection = sqlite3.connect(
        'file:%s?mode=%s' % (BASE.as_posix(),
                             'rw' if options.ecrire else 'ro'), uri=True)

    # LA FAMILLE DE DEPART a ete lue plus haut, depuis `--famille` (liste
    # fermee) : les requetes ci-dessous ne portent donc aucune valeur libre.
    requete = ("SELECT book_id, %s, locked, character_name FROM voices "
               "WHERE %s LIKE '%s:%%'" % (COLONNE, COLONNE, famille))
    if options.livre is not None:
        requete += " AND book_id = %d" % options.livre
    lignes = list(connection.execute(requete))

    # NARRATEURS DE LIVRE (ajout du 29/09/2026) : `books.narrator_voice` est un
    # champ a part, qui ne suit PAS la table `voices`. Le 29/09/2026, deux livres
    # (27 et 35) avaient un narrateur Kyutai : sans ce traitement, ils
    # s'arreteraient (503) le jour ou le moteur Kyutai est eteint. Ils sont lus
    # AVANT le test « rien a faire » (defaut dormant corrige le 29/09/2026 : le
    # test les citait avant leur lecture, donc un livre dont SEUL le narrateur
    # etait concerne n'aurait jamais ete traite).
    requete_narrateurs = ("SELECT id, title, narrator_voice FROM books "
                          "WHERE narrator_voice LIKE '%s:%%'" % famille)
    if options.livre is not None:
        requete_narrateurs += " AND id = %d" % options.livre
    narrateurs = list(connection.execute(requete_narrateurs))

    if not lignes and not narrateurs:
        print('')
        print('aucune voix %s a basculer : rien a faire.' % famille)
        connection.close()
        return 0

    par_livre = {}
    for book_id, voix, verrou, personnage in lignes:
        par_livre.setdefault(book_id, []).append((voix, verrou, personnage))

    titres = {r[0]: r[1] for r in connection.execute(
        "SELECT id, title FROM books")}

    total = 0
    verrouilles = 0
    sans_jumelle = {}
    print('')
    for book_id in sorted(par_livre):
        personnages = par_livre[book_id]
        total += len(personnages)
        print('  livre %-4s %-40s %3d personnage(s), %2d voix %s distincte(s)'
              % (book_id, str(titres.get(book_id, '?'))[:40], len(personnages),
                 len({v for v, _l, _c in personnages}), famille))
        for voix, verrou, personnage in sorted(personnages):
            jumelle = jumelle_de(voix, extraits, catalogue)
            if jumelle is None:
                sans_jumelle.setdefault(voix, []).append(book_id)
            if verrou:
                verrouilles += 1

    print('')
    print('total : %d personnage(s) a basculer, dont %d verrouille(s)'
          % (total, verrouilles))

    if narrateurs:
        print('')
        print('NARRATEURS de livre en voix Kyutai : %d' % len(narrateurs))
        for book_id, titre, voix in narrateurs:
            jumelle = jumelle_de(voix, extraits, catalogue)
            print('  livre %-4s %-40s %s -> %s'
                  % (book_id, str(titre or '?')[:40], voix,
                     jumelle if jumelle else 'AUCUNE JUMELLE'))
            if jumelle is None:
                sans_jumelle.setdefault(voix, []).append(book_id)

    # NOTES D'ECOUTE (ajout du 29/09/2026) : elles suivent le changement de
    # moteur, sinon les etoiles et les remarques de Laurent seraient perdues
    # dans la fenetre « Ecouter les voix ».
    a_recopier = notes_a_recopier(
        {v for personnages in par_livre.values() for v, _l, _c in personnages}
        | {voix for _bid, _titre, voix in narrateurs},
        extraits, catalogue, famille)
    if ANNOTATIONS.exists():
        cles_kyutai = [c for c in notes_du_fichier() if c.startswith('kyutai:')]
        print('')
        print('notes d ecoute (%s) : %d cle(s) en voix %s'
              % (ANNOTATIONS.name, len(cles_kyutai), famille))
        print('  a DOUBLER vers leur jumelle Qwen : %d'
              ' (les cles Kyutai sont gardees)' % len(a_recopier))

    if sans_jumelle:
        print('')
        print('ATTENTION : %d voix Kyutai sans jumelle chez Qwen :'
              % len(sans_jumelle))
        for voix, livres in sorted(sans_jumelle.items()):
            print('    %-34s (livre %s)' % (voix, ', '.join(map(str, livres))))
        print('Ces personnages garderaient leur voix Kyutai, donc un moteur a')
        print('allumer. Ne rien ecrire avant de savoir pourquoi.')
        connection.close()
        return 2

    if not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        connection.close()
        return 0

    # --- Ecriture : copie datee AVANT toute modification (regle du projet) ---
    horodatage = datetime.now().strftime('%Y%m%d_%H%M')
    sauvegarde = BASE.with_name('%s.bak_avant_bascule_qwen_%s'
                                % (BASE.name, horodatage))
    shutil.copy2(str(BASE), str(sauvegarde))
    print('')
    print('copie de la base : %s' % sauvegarde.name)

    modifiees = 0
    narrateurs_bascules = 0
    with connection:
        for book_id in sorted(par_livre):
            for voix, _verrou, _personnage in par_livre[book_id]:
                jumelle = jumelle_de(voix, extraits, catalogue)
                if jumelle is None:
                    continue
                curseur = connection.execute(
                    "UPDATE voices SET %s = ? WHERE book_id = ? AND %s = ?"
                    % (COLONNE, COLONNE), (jumelle, book_id, voix))
                modifiees += curseur.rowcount
        # Le narrateur du livre : un AUTRE champ, a basculer separement.
        for book_id, _titre, voix in narrateurs:
            jumelle = jumelle_de(voix, extraits, catalogue)
            if jumelle is None:
                continue
            curseur = connection.execute(
                "UPDATE books SET narrator_voice = ? WHERE id = ? "
                "AND narrator_voice = ?", (jumelle, book_id, voix))
            narrateurs_bascules += curseur.rowcount
    connection.close()
    print('personnages bascules : %d' % modifiees)
    if narrateurs:
        print('narrateurs de livre bascules : %d' % narrateurs_bascules)

    # Les notes d'ecoute suivent le changement de moteur (copie datee AVANT).
    if a_recopier:
        sauvegarde_notes = ANNOTATIONS.with_name(
            '%s.bak_avant_bascule_qwen_%s' % (ANNOTATIONS.name, horodatage))
        shutil.copy2(str(ANNOTATIONS), str(sauvegarde_notes))
        notes = notes_du_fichier()
        for cle, jumelle in a_recopier.items():
            notes[jumelle] = dict(notes[cle])
        ANNOTATIONS.write_text(
            json.dumps(notes, ensure_ascii=False, indent=2, sort_keys=True),
            encoding='utf-8')
        print('notes d ecoute recopiees vers les voix Qwen : %d' % len(a_recopier))
        print('copie des notes : %s' % sauvegarde_notes.name)
    print('')
    print('A SAVOIR : les voix restent VERROUILLEES comme avant (le verrou')
    print('suit le personnage, pas le moteur), et les prenoms ne changent pas.')
    print('A FAIRE ENSUITE : allumer le moteur Qwen (qwentts_service\\'
          'DEMARRER_QWENTTS_CPP.bat) -- ou simplement lancer START.bat, qui'
          ' s en charge tout seul depuis le 28/09/2026')
    print('puis ecouter un chapitre du livre concerne.')
    print('RETOUR ARRIERE : recopier %s sur la base.' % sauvegarde.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())

