# -*- coding: utf-8 -*-
"""QUI RACONTE CHAQUE CHAPITRE ? -- la « carte des POV », regle ecrite UNE SEULE FOIS.

POURQUOI CE MODULE (15/10/2026, chantier « le narrateur d'un chapitre est le
personnage du chapitre »). Dans *Le Trone de Fer*, chaque chapitre est ecrit a la
troisieme personne focalisee : le narrateur du chapitre EST le personnage du
chapitre (« BRAN », « CATELYN », « EDDARD »...). Laurent veut donc que la
NARRATION d'un chapitre soit lue par la VOIX de son personnage, au lieu d'un
narrateur unique pour tout le livre.

Une seule voix, la meme, pour la narration ET pour le dialogue du personnage qui
raconte -- decision de Laurent du 15/10/2026 : la distinction dialogue / narration
se fait par l'ATTRIBUTION des phrases, pas par le timbre.

OU SE TROUVE LE PERSONNAGE (mesure du 15/10/2026, les 15 tomes francais) :
  - tomes 01 a 09 : le PRENOM EST LE TITRE du chapitre (« BRAN », « EDDARD ») ;
  - tomes 10 a 12 : melange de prenoms et de SURNOMS (« LE PROPHETE », « LA FILLE
    DE LA SEICHE ») -- un surnom ne se devine pas : il se relie a la main ;
  - tomes 13 a 15 : le titre est « Chapitre N », mais le PRENOM OUVRE LE TEXTE
    (« Tyrion Il passa tout le detroit a boire. ») ;
  - tome 00 (Le Chevalier Errant) : aucun nom nulle part, POV unique (Dunk).

CE MODULE EST LA REGLE, ET RIEN D'AUTRE. Il ne choisit aucune voix et n'ecrit
rien : il dit ce qu'on ARRIVE a reconnaitre. Ses deux appelants sont `main.py`
(le point d'entree `GET /api/books/{id}/pov`) et `test_voix/_voir_pov_chapitres.py`
(l'outil de controle de l'atelier). Une seule copie de la regle : deux copies
auraient derive (lecon du decoupage des phrases, `modules/decoupage.py`).

LE VRAI FILTRE, C'EST LE CASTING : on ne rapproche un nom que des personnages
DEJA castes du livre (table `voices`, alias compris). Les noms lus dans le texte
ne sont fiables qu'apres ce croisement.
"""

import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from core.epub_parser import get_chapters                          # noqa: E402

# Un titre de chapitre qui porte un personnage est COURT. Au-dela, c'est un vrai
# titre (« La Bataille sur la Verchere »), donc pas un POV.
#
# BORNE MESUREE LE 15/10/2026, sur les 15 tomes francais (404 chapitres) : passer de
# 4 a 5 mots et de 30 a 34 caracteres n'ajoute que DEUX titres -- « LA FILLE DE LA
# SEICHE » (tome 10, POV Asha Greyjoy) et « LA PRINCESSE EN LA TOUR » (tome 12, POV
# Arianne Martell). Ce sont deux VRAIS POV, et aucun bruit avec eux : la borne est
# donc ouverte a 5 mots. Au-dela, ce sont des titres, pas des personnages.
LONGUEUR_MAX_TITRE = 34
MOTS_MAX_TITRE = 5
# Le premier mot du texte compte comme un prenom s'il fait 3 a 15 lettres.
LETTRES_MIN = 3
LETTRES_MAX = 15

# Un titre DESCRIPTIF colle au debut du chapitre : « Le lord perdu Ça n'aurait pas du
# prendre aussi longtemps » -> le POV est « Le lord perdu ». On le reconnait a sa
# forme : un DETERMINANT au debut, puis des mots qui S'ARRETENT sur la majuscule qui
# ouvre la VRAIE phrase. Sans cette majuscule, c'est une phrase ordinaire (« Le vent
# soufflait sur les creneaux »), et il n'y a rien a en tirer.
#
# POURQUOI C'EST NECESSAIRE : la table des surnoms (`pov_surnoms`) a besoin d'un
# CANDIDAT pour relier un chapitre. Un titre comme « Le lord perdu » n'en produisait
# aucun, donc ce chapitre ne pouvait JAMAIS etre relie -- ni par le casting, ni par la
# table. Depuis le 15/10/2026, il en produit un.
DETERMINANTS_DE_TITRE = ('LE', 'LA', 'LES', 'UN', 'UNE', 'L', 'DU', 'DES')
# Mots qui ANNONCENT une suite dans un titre : apres eux, une majuscule fait partie du
# titre (« Le prince de Winterfell », « Le pretendant de Fer »), tandis qu'ailleurs
# elle ouvre la phrase (« Le lord perdu Ca n'aurait pas du... »). Mesure du 15/10/2026 :
# sans cette regle, la capture s'arretait a « Le prince de » et « Un fantome a ».
LIAISONS_DE_TITRE = ('DE', 'DU', 'DES', 'D', 'LA', 'LE', 'LES', 'A', 'AU', 'AUX',
                     'EN', 'SUR', 'SOUS', 'DANS', 'ET', 'OU', 'DU.', 'DE.')


def surnom_du_debut(premiere):
    """Le titre descriptif qui ouvre un chapitre, ou '' s'il n'y en a pas.

    Mesure du 15/10/2026 : le tome 13 en porte deux (« Le lord perdu », « Le
    domestique du marchand ») et le tome 14 trois (« Le prince de Winterfell », « Un
    fantome a Winterfell », « Le pretendant de Fer ») -- tous de VRAIS POV. Deux
    garde-fous : la capture s'arrete sur la majuscule qui ouvre la VRAIE phrase (sans
    quoi « Le vent soufflait sur les creneaux » passerait pour un nom), SAUF si cette
    majuscule est precedee d'une liaison (« de Winterfell »).
    """
    mots = (premiere or '').split()
    if not mots or len(mots) < 2:
        return ''
    if normaliser(mots[0]).strip("'") not in DETERMINANTS_DE_TITRE:
        return ''
    # CAS 1 : la ligne ENTIERE est le titre, sans phrase derriere. C'est le cas des
    # tomes 14 et 15 (« Le prince de Winterfell », « Un fantome a Winterfell », « Le
    # pretendant de Fer ») : il n'y a alors AUCUNE majuscule d'arret, et c'est la ligne
    # entiere qui compte. Un titre ne finit pas par un point -- c'est ce qui ecarte
    # « Le vieil homme marchait. » -- et il reste court.
    if (len(mots) <= MOTS_MAX_TITRE and not premiere.rstrip().endswith('.')
            and len(premiere) <= LONGUEUR_MAX_TITRE):
        return _titre_acceptable(premiere)
    # CAS 2 : le titre est COLLE a la phrase (« Le lord perdu Ca n'aurait pas du... »).
    # On s'arrete a la majuscule qui ouvre la VRAIE phrase, SAUF si elle est precedee
    # d'une liaison (« Le prince de Winterfell » : « Winterfell » reste dans le titre).
    gardes = [mots[0]]
    arrete = False
    for position, mot in enumerate(mots[1:7], start=1):
        commence_par_majuscule = (mot[:1].isupper() and mot[:1].isalpha()
                                  and not mot.isupper())
        if commence_par_majuscule:
            precedent = normaliser(mots[position - 1]).strip("'")
            if precedent not in LIAISONS_DE_TITRE:
                arrete = True
                break
        gardes.append(mot)
    if not arrete or len(gardes) < 2:
        return ''
    return _titre_acceptable(' '.join(gardes))


def _titre_acceptable(titre):
    """Le titre nettoye, ou '' : longueur tenue, et jamais un titre generique."""
    titre = ' '.join(titre.split()).strip(' .,;:\u00ab\u00bb')
    normalise = normaliser(titre)
    if not normalise or len(normalise) > LONGUEUR_MAX_TITRE:
        return ''
    if est_generique(normalise):
        return ''
    return titre

# Mots qui disent « ce chapitre n'a pas de personnage qui raconte » : page de
# garde, sommaire, resume, remerciements... UN SEUL de ces mots suffit a classer
# le titre comme generique (donc narration par le narrateur du livre).
MOTS_GENERIQUES = {
    'CHAPITRE', 'CHAPITRES', 'CH', 'CHAPTER', 'CHAPTERS',
    'TOME', 'TOMES', 'LIVRE', 'LIVRES', 'PARTIE', 'PARTIES', 'DIVISION',
    'PROLOGUE', 'PROLOGUES', 'PRELUDE', 'EPILOGUE', 'EPILOGUES', 'POSTLUDE',
    'ENTRE-TEMPS', 'RESUME', 'REMERCIEMENTS', 'DEDICACE', 'APPENDICE',
    'ANNEXE', 'ANNEXES', 'SOMMAIRE', 'TABLE', 'MATIERES', 'COUVERTURE',
    'GARDE', 'PAGE', 'TITRE', 'INDEX', 'GLOSSAIRE', 'GENEALOGIE',
    'AVERTISSEMENT', 'NOTE', 'NOTES', 'CHRONOLOGIE', 'AUTEUR', 'PRINCIPAUX',
    'PERSONNAGES', 'CARTE', 'CARTES', 'MAISON', 'OUVRAGE', 'EDITION',
    'PRESENTATION', 'PREFACE', 'INTRODUCTION', 'CONCLUSION', 'BIOGRAPHIE',
    'TEMOIGNAGES', 'EXTRAITS', 'LEXIQUE', 'BIBLIOGRAPHIE', 'FILMOGRAPHIE',
    'ARGUTIE', 'ARGUTIES',
}

# Mots trop communs pour ouvrir un chapitre sur un prenom : « Ce volume est pour
# mes fans », « Une argutie sur la chronologie »... Aucun n'est un POV.
PAS_UN_PRENOM = {
    'CE', 'CET', 'CETTE', 'CES', 'IL', 'ELLE', 'ILS', 'ELLES', 'ON', 'NOUS',
    'VOUS', 'JE', 'TU', 'UNE', 'UN', 'DES', 'DU', 'DE', 'LA', 'LE', 'LES',
    'POUR', 'DANS', 'QUAND', 'ALORS', 'PLUS', 'TOUT', 'TOUS', 'TOUTE',
    'TOUTES', 'MAIS', 'ET', 'OU', 'SUR', 'SOUS', 'APRES', 'AVANT', 'DEPUIS',
    'PENDANT', 'ENFIN', 'EN', 'AU', 'AUX', 'SA', 'SON', 'SES', 'QUI', 'QUE',
    'QUOI', 'NE', 'PAS', 'PLUS.', 'L', 'D', 'LE.', 'IL.', 'UNE.',
    'ENSUITE', 'SOUDAIN', 'LORSQUE', 'CAR', 'DONC', 'AINSI', 'DEJA', 'PUIS',
    'ENCORE', 'TOUJOURS', 'JAMAIS', 'RIEN', 'PERSONNE', 'COMME', 'DEPUIS.',
    'CHEZ', 'VERS', 'ENTRE', 'SANS', 'AVEC', 'LORSQU', 'QUAND.', 'APRES.',
}

# Ce qu'on retire autour du premier mot d'une ligne : ponctuation et guillemets,
# y compris les guillemets francais (ecrits par leur code, pour que ce fichier
# reste en ASCII pur).
PONCTUATION_DE_BORD = '.,:;()[]"\'' + chr(171) + chr(187) + chr(8217)

# Des INITIALES en pleine premiere ligne (« George R.R. Martin ») : c'est une
# page de titre ou de copyright, jamais un chapitre raconte par un personnage.
_INITIALES = re.compile(r'\b[A-Z]\.[A-Z]?\.')

# Un chapitre qui ouvre sur du DIALOGUE ne commence pas par un nom : le tiret
# cadratin, le tiret simple et les guillemets sont ecartes d'entree.
DIALOGUE_OU_TIRET = ('\u2014', '-', '\u00ab', '\u201c', '"', '\u2013')


def normaliser(texte):
    """Majuscules, sans accents, espaces simples, « _ » et apostrophes a plat.

    C'est la meme normalisation des deux cotes de la comparaison : un titre de
    chapitre (« EDDARD ») et un nom de casting (« Eddard_Stark »).
    """
    texte = unicodedata.normalize('NFKD', texte or '')
    texte = ''.join(c for c in texte if not unicodedata.combining(c))
    texte = texte.replace('_', ' ').replace('\u2019', "'")
    texte = re.sub(r'\s+', ' ', texte).upper()
    return texte.strip()


def est_generique(normalise):
    """Titre sans personnage (chapitre numerote, page de garde, resume...) ?"""
    if not normalise:
        return True
    for mot in normalise.split():
        if mot.strip('.,:;()[]') in MOTS_GENERIQUES:
            return True
    return False


def premiere_ligne(texte):
    """La premiere ligne NON VIDE d'un chapitre, quel que soit son saut de ligne.

    Pourquoi c'est necessaire : certains EPUB separent leurs paragraphes par un
    simple RETOUR CHARIOT (`\\r`) et non par un saut de ligne. Lire « la premiere
    ligne » d'un tel fichier donne alors le chapitre ENTIER, donc aucune
    reconnaissance n'est possible -- c'est exactement ce qui est arrive au
    tome 13 (26 chapitres muets) avant le 15/10/2026.
    """
    texte = (texte or '').replace('\r\n', '\n').replace('\r', '\n')
    for ligne in texte.split('\n'):
        if ligne.strip():
            return ligne.strip()
    return ''


def candidat_du_titre(titre):
    """Le TITRE porte-t-il un nom de personnage ? -> (candidat, 'titre') ou (None, None).

    « BRAN », « CATELYN », « ALAYNE » : oui. « Chapitre 12 », « PRELUDE »,
    « PRINCIPAUX PERSONNAGES », « LA BATAILLE SUR LA VERCHE » : non (titre
    generique, ou titre trop long pour etre un nom de personnage).
    """
    normalise = normaliser(titre)
    if not normalise or est_generique(normalise):
        return None, None
    if len(normalise) > LONGUEUR_MAX_TITRE:
        return None, None
    if len(normalise.split()) > MOTS_MAX_TITRE:
        return None, None
    return normalise, 'titre'


def candidat_du_texte(texte):
    """Titre generique : le PREMIER MOT du chapitre dit-il qui raconte ?

    C'est le cas des tomes 13 a 15, ou le titre est « Chapitre N » mais ou le
    texte ouvre sur « Tyrion Il passa tout le detroit a boire. ».

    Quatre precautions, parce qu'un premier mot n'est un prenom que rarement :
      - la ligne ne doit pas etre du DIALOGUE (ni tiret, ni guillemets) et ne pas
        porter d'INITIALES (« George R.R. Martin ») : c'est une page de titre ou
        d'auteur, pas un personnage ;
      - le mot doit etre Capitalise (« Tyrion »), jamais en CAPITALES (« UNE »)
        ni en minuscules -- c'est ce qui ecarte « PRINCIPAUX », « TRONE » ;
      - il doit faire 3 a 15 lettres ;
      - il ne doit pas etre un mot courant francais (« Ce volume... », « Une
        argutie... »). Les propositions vues UNE SEULE fois dans tout le livre
        sont listees a part par l'outil : ce sont souvent des faux.

    La ligne n'a PAS besoin d'etre courte : dans les tomes 13 a 15, le prenom
    est colle au premier paragraphe (« Daenerys Elle entendait le mort gravir
    les mats... »).
    """
    premiere = premiere_ligne(texte)
    if not premiere:
        return None, None
    if premiere[:1] in DIALOGUE_OU_TIRET:
        return None, None
    if _INITIALES.search(premiere):
        return None, None
    premier = premiere.split()[0].strip(PONCTUATION_DE_BORD)
    normalise = normaliser(premier)
    if (normalise and not est_generique(normalise)
            and normalise not in PAS_UN_PRENOM
            and LETTRES_MIN <= len(normalise) <= LETTRES_MAX
            and normalise.isalpha()
            and not premier.isupper() and premier[:1].isupper()):
        return normalise, 'texte'
    # Le premier mot n'est PAS un prenom : c'est peut-etre un TITRE DESCRIPTIF colle
    # au debut (« Le lord perdu », « Le domestique du marchand »). Sans cela, ces
    # chapitres ne pourraient jamais etre relies : la table des surnoms a besoin d'un
    # CANDIDAT (mesure du 15/10/2026 : deux chapitres du tome 13, deux vrais POV).
    titre = surnom_du_debut(premiere)
    if titre:
        return normaliser(titre), 'texte'
    return None, None


def creer_table_surnoms(conn):
    """Cree la table des SURNOMS de POV si elle n'existe pas (15/10/2026).

    Elle vit ICI, avec la regle qui la lit, et non dans `main.py` : les deux
    appelants (`init_db()` au demarrage du serveur, et l'outil
    `test_voix/_proposer_surnoms_pov.py` qui l'ecrit) la creent par la MEME
    fonction -- une seule definition, donc aucune derive possible entre les deux.

    Pourquoi une table : un titre de chapitre peut porter un SURNOM et non un
    prenom (« LE PROPHETE », « LE NOYE », « SCHLINGUE », « Le lord perdu »), et le
    texte ne le donne pas toujours (« SCHLINGUE » n'est nomme « Theon » qu'une fois
    dans son chapitre). PORTEE (`portee`) : les tomes d'une saga PARTAGENT leur
    casting, donc un surnom vaut pour la SAGA entiere quand elle est renseignee --
    et pour le livre seul sinon. Forme : 'saga:Trone de fer' ou 'livre:35'.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pov_surnoms (
            portee          TEXT NOT NULL,
            surnom          TEXT NOT NULL,
            canonical_name  TEXT NOT NULL,
            source          TEXT DEFAULT 'main',
            preuve          TEXT DEFAULT '',
            ajoute_le       TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (portee, surnom)
        )
    """)


def portees(conn, book_id):
    """Les portées de surnoms qui s'appliquent à ce livre, la plus précise d'abord.

    Un surnom se range à la portée de la **saga** quand le livre en a une (les tomes
    d'une saga **partagent leur casting**, donc leurs surnoms aussi), et à celle du
    **livre** sinon — ou pour un surnom qui ne vaut que pour un tome. Renvoie
    `['livre:35', 'saga:Trone de fer']`, ou `['livre:35']` pour un livre isolé.

    Tolérant par construction : une base sans colonne `saga`, ou sans la table des
    surnoms, répond la portée du livre — jamais une surprise.
    """
    liste = ['livre:%d' % book_id]
    try:
        ligne = conn.execute('SELECT saga FROM books WHERE id = ?',
                             (book_id,)).fetchone()
    except sqlite3.Error:
        return liste
    saga = (ligne[0] if ligne else None) or ''
    if saga.strip():
        liste.append('saga:' + saga.strip())
    return liste


def personnages_du_livre(conn, book_id):
    """Le casting du livre, prêt à être comparé à un titre de chapitre.

    Renvoie {NOM_NORMALISE: {"nom", "voice_id", "pitch", "rate", "repliques"}}.
    Les ALIAS comptent : si « ALAYNE » a été regroupé sous « Sansa », le titre
    « ALAYNE » trouvera Sansa, avec sa voix ET ses réglages.
    """
    personnes = {}
    for ligne in conn.execute(
            'SELECT character_name, voice_id, pitch, rate, line_count '
            'FROM voices WHERE book_id = ?', (book_id,)):
        personnes[normaliser(ligne['character_name'])] = {
            'nom':       ligne['character_name'],
            'voice_id':  ligne['voice_id'] or '',
            'pitch':     ligne['pitch'] or '+0Hz',
            'rate':      ligne['rate'] or '+0%',
            'repliques': ligne['line_count'] or 0,
        }
    for ligne in conn.execute(
            'SELECT alias_name, canonical_name FROM character_aliases '
            'WHERE book_id = ?', (book_id,)):
        principal = normaliser(ligne['canonical_name'])
        alias = normaliser(ligne['alias_name'])
        if principal in personnes and alias:
            personnes[alias] = personnes[principal]
    # LES SURNOMS DE POV (15/10/2026) : un titre de chapitre peut porter un nom qui
    # n'est PAS un prenom -- « LE PROPHETE », « LE NOYE », « LA FILLE DE LA SEICHE »,
    # « SCHLINGUE », « Le lord perdu ». Ils vivent dans la table `pov_surnoms`, a la
    # portee de la saga ou du livre, et pointent sur un personnage DU CASTING : comme
    # les alias, ils enrichissent donc le dictionnaire, et TOUT le reste suit (la
    # carte, l'outil de controle, les replis). La table peut manquer (base non
    # migree, base de test) : on continue alors sans elle.
    try:
        portees_livre = portees(conn, book_id)
        marques = ', '.join('?' * len(portees_livre))
        for ligne in conn.execute(
                'SELECT surnom, canonical_name FROM pov_surnoms '
                'WHERE portee IN (%s)' % marques, portees_livre):
            principal = normaliser(ligne[1])
            surnom = normaliser(ligne[0])
            if principal in personnes and surnom:
                personnes[surnom] = personnes[principal]
    except sqlite3.Error:
        pass
    return personnes


def rapprocher(candidat, personnes):
    """Quel personnage du casting porte ce nom ? -> son dict, ou None.

    Deux facons de trouver : l'egalite (« BRAN » = « Bran ») et le candidat qui
    compte comme un MOT du nom complet (« EDDARD » trouve « Eddard Stark »).
    Quand plusieurs personnages collent, **le plus BAVARD gagne** : un titre de
    chapitre designe le personnage principal, pas un homonyme de deux repliques
    -- dans *Le Trone de Fer*, le titre « JON » est Jon Snow, pas un autre Jon.
    """
    if not candidat:
        return None
    trouves = [personne for nom, personne in personnes.items()
               if candidat == nom or candidat in nom.split()]
    if not trouves:
        return None
    trouves.sort(key=lambda personne: personne['repliques'], reverse=True)
    return trouves[0]


def carte_du_livre(chemin, personnes):
    """Une ligne par chapitre : ce qu'on reconnait, et avec quel personnage.

    `personnes` peut etre vide (livre pas encore caste) : les candidats sont
    alors donnes SANS confirmation -- c'est ce que fait l'outil de controle de
    l'atelier, pour voir la matiere avant tout casting.
    """
    lignes = []
    for chapitre in get_chapters(str(chemin)):
        titre = chapitre.get('title') or ''
        texte = chapitre.get('text') or ''
        candidat, source = candidat_du_titre(titre)
        if not candidat:
            candidat, source = candidat_du_texte(texte)
        personne = None
        if candidat and personnes:
            personne = rapprocher(candidat, personnes)
        lignes.append({
            'index':      chapitre.get('index', len(lignes)),
            'titre':      titre,
            'source':     source if candidat else None,
            'candidat':   candidat,
            'personnage': personne,
            'debut':      premiere_ligne(texte)[:60],
        })
    return lignes


def compte_par_nom(lignes):
    """nom normalise -> liste des numeros de chapitres qui le portent."""
    compte = {}
    for ligne in lignes:
        if ligne['candidat']:
            compte.setdefault(ligne['candidat'], []).append(ligne['index'])
    return compte


def carte_pour_api(lignes):
    """La carte telle que la page la reçoit : {index: {"nom", "source"}}.

    ELLE NE PORTE QUE « QUI RACONTE QUEL CHAPITRE », et c'est volontaire -- leçon
    de l'audit du 15/10/2026 : une carte qui embarquerait AUSSI la voix, la
    hauteur et la vitesse les FIGERAIT jusqu'à la réouverture du livre. Or la page
    relit ces réglages dans le CASTING à chaque phrase, comme pour les répliques
    (`_voiceForSentence`, `frontend/app.js`) : c'est ce qui fait qu'un changement
    de voix s'entend TOUT DE SUITE, dans la narration comme dans le dialogue.

    Les chapitres SANS personnage reconnu, et ceux dont le personnage n'a PAS de
    voix au casting, n'y figurent pas : le lecteur leur garde la voix du narrateur
    du livre. Les seconds sont listés à part par `sans_voix_pour_api`.
    """
    carte = {}
    for ligne in lignes:
        personne = ligne.get('personnage')
        if not personne or not personne.get('voice_id'):
            continue
        carte[str(ligne['index'])] = {
            'nom':    personne['nom'],
            'source': ligne['source'],
        }
    return carte


def sans_voix_pour_api(lignes):
    """Les chapitres reconnus dont le personnage n'a PAS de voix au casting.

    C'est une LIMITE, pas une panne (signalée par l'audit du 15/10/2026) : un
    personnage qui ne parle jamais dans le livre n'a aucune ligne dans la table
    `voices` -- on ne lui a jamais donné de voix. Son chapitre sera donc lu par le
    narrateur du livre. Le lecteur le DIT à Laurent, qui peut alors relier le nom
    au casting. Renvoie {index: nom propose}.
    """
    sans_voix = {}
    for ligne in lignes:
        if not ligne.get('candidat'):
            continue
        personne = ligne.get('personnage')
        if personne and personne.get('voice_id'):
            continue
        sans_voix[str(ligne['index'])] = (personne['nom'] if personne
                                          else ligne['candidat'])
    return sans_voix
