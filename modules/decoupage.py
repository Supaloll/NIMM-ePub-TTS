# -*- coding: utf-8 -*-
"""Découpage d'un chapitre en phrases — LA règle de référence du projet.

Pourquoi ce module (18/09/2026) : la même règle était écrite **quatre fois**
(page, casting, re-cast, recherche), et elle **coupait les phrases après le
point d'une abréviation**. Exemple réel (tome 5 de Monte-Cristo) :

    « … le temps de complimenter M.  |  de Morcerf ; il a fait preuve… »

Deux phrases au lieu d'une : le moteur recevait un morceau finissant par
« monsieur » (d'où le silence entendu par Laurent), et le texte perdait son
début à l'écran. Mesure : **207 coupures** dans un seul tome.

La règle, identique à celle de la page (`frontend/app.js`, `_buildSentences`) :
  1. paragraphes séparés par une ligne vide, ignorés sous 6 caractères ;
  2. phrases coupées APRÈS un point, un point d'interrogation, un point
     d'exclamation, une ellipse ou un guillemet fermant, suivi d'un espace ;
  3. SAUF si le mot avant le point est une abréviation française (M., Mme,
     Mgr, Dr…) : ce point appartient au mot, il ne finit pas la phrase ;
  4. phrases de 4 caractères ou plus conservées.

Historique des valeurs (pour la migration des index de `speaker_attribution`) :
  - `REGLE_ANCIENNE` : ce qui était en service jusqu'au 18/09/2026 (coupait
    après les abréviations) ;
  - `REGLE_ACTUELLE` : la règle corrigée.
`phrases_avec_positions()` sert à la migration : elle donne, pour chaque
phrase, sa position dans le texte, ce qui permet de savoir quelle ancienne
phrase est devenue quelle nouvelle.
"""

import re

# Motifs de coupe, à garder IDENTIQUES dans `frontend/app.js` (une copie est
# inévitable : le navigateur ne lit pas le Python). Le test
# `test_voix/test_decoupage_phrases.py` compare les deux fichiers.
MOTIF_COUPE = r'(?<=[.!?…»])\s+'
MOTIF_PARAGRAPHES = r'\n\n+'

# Taille minimale d'une phrase conservée, et d'un paragraphe examiné.
MIN_PHRASE = 4      # plus de 3 caracteres
MIN_PARAGRAPHE = 6  # plus de 5 caracteres

# Les abréviations françaises APRÈS lesquelles un point ne finit JAMAIS une
# phrase. Écrire « M. » ou « Mme » est une civilité : le nom qui suit fait
# partie de la même phrase.
# Les formes TOUT EN MAJUSCULES sont là aussi : un texte traduit de l'anglais
# écrit « MR. CURRIE » (constat de Laurent, 21/09/2026, 22/11/63 chapitre 10).
# Sans elles, la phrase était COUPÉE juste avant le nom : le moteur recevait un
# morceau finissant par « MR. » et INVENTAIT un son (« [féè] »), et le nom
# partait dans un second morceau de six caractères.
# « Mrs » est là pour la même raison (constat du même jour) : NON reconnu, il
# coupait la phrase après « Mrs. », et Laurent entendait une **grande pause**
# avant le nom. On ne touche PAS à sa lecture (le moteur dit « Misses », ce qui
# lui convient) : ici, c'est seulement la frontière de phrase qui change.
ABREVIATIONS = ('M', 'MM', 'Mme', 'Mmes', 'Mlle', 'Mlles', 'Mgr', 'Dr', 'Pr',
                'St', 'Ste', 'Mr', 'Mx', 'Mrs',
                'MR', 'MRS', 'MME', 'MMES', 'MLLE', 'MLLES', 'MGR', 'DR', 'PR')

# Celles qui s'écrivent SANS point mais ne finissent pas une phrase pour autant.
ABREVIATIONS_SANS_POINT = ('Mme', 'Mmes', 'Mlle', 'Mlles', 'Mgr')

REGLE_ANCIENNE = 'ancienne'
REGLE_ACTUELLE = 'actuelle'
# Regle « dialogue » (21/09/2026) : REGLE_ACTUELLE, PLUS une coupe de la
# narration d'avec la replique quand un VRAI dialogue est introduit par un beat.
REGLE_DIALOGUE = 'dialogue'

# --- Pourquoi cette troisieme regle -----------------------------------------
# Demande de Laurent : un morceau qui MELANGE narration et dialogue --
# « Avant que j'aie pu repondre, Richie est intervenu : «Non, c'est pas ca. » --
# doit etre coupe en deux, pour que le beat revienne au NARRATEUR et la replique
# au PERSONNAGE. Aujourd'hui, comme le prompt donne un morceau mixte au
# personnage (consigne 8), c'est le personnage qui lit la narration.
#
# La coupe ne s'applique QU'A UN VRAI DIALOGUE introduit par un beat, jamais a
# une citation racontee : « J'ai jamais eu « la larme facile », comme on dit. »
# doit rester d'un seul morceau, sinon la phrase serait lue en deux fois, avec
# deux intonations finales. Mesure sur « 22/11/63 » : 606 morceaux contiennent
# du texte avant un «, mais la moitie sont des citations racontees.
#
# Discriminant retenu, mesure le 21/09/2026 sur « 22/11/63 » (166 morceaux, dont
# 159 attribues a un personnage a tort) : le texte avant la citation finit par
# DEUX-POINTS et contient un VERBE DE PAROLE. Les variantes plus larges
# attrapaient des citations apres deux-points sans verbe de parole
# (« Le sujet que j'avais donne etait : « Le jour qui a change ma vie. » »).
#
# Les radicaux sont donnes au RADICAL : « repond », attrape « repondit »,
# « repondirent », « repondait ». La liste de reference du projet pour les
# verbes de parole reste `modules/incises.py` (VERBES), qui sert a RETIRER une
# incise du texte parle ; ici, il s'agit seulement de reconnaitre un beat.
#
# CONTRAINTE (21/09/2026) : chaque radical commence par une lettre ASCII. Ce
# n'est pas cosmetique : le motif utilise `\b`, qui ne se comporte pas pareil en
# Python (Unicode) et en JavaScript (ASCII) devant une lettre accentuee. Un
# radical commence par « e » serait trouve en Python et jamais en JavaScript.
# C'est pour cela que « écria » n'y est pas (les formes courantes sont
# « s'écria », couvertes par "s'écri").
VERBES_DE_PAROLE = (
    'dit', 'dis', 'dirent', 'répond', 'repond', 'répliqu', 'repliqu',
    "s'écri", "s'ecri", 'ecria', 'cria', 'crie', 'crièrent', 'crierent',
    'demand', 'repri', 'reprend', 'ajout', 'murmur', 'poursuiv', 'poursuit',
    'continua', 'hasard', 'observ', 'remarqu', 'souffl', 'soupir', 'grommel',
    'grond', 'tonna', 'vocifér', 'vocifer', 'interromp', 'interv', 'interven',
    'fit', 'firent', 'répét', 'repet', 'avou', 'déclar', 'declar', 'conclut',
    'conclu', 'achev', 'commença', 'commenca', 'termina', 'insista',
    'object', 'ripost', 'rispost', 'répartit', 'repartit', 'interroge',
    'questionn', 'exige', 'ordonna', 'supplia', 'pria', 'songea', 'gémit',
    'gemit', 'sanglota', 'plaida', 'protest', 'appel', 'conseilla',
    'enchain', 'enchaîn', 'renchér', 'rench', 'gliss', 'lâch', 'lach',
    'rétorqu', 'retorqu', 'approuv', 'précis', 'precis', 'expliqu', 'annonc',
    'annonç', 'marmonn', 'bougonn', 'rican', 'exclam', 'lança', 'lanca',
    'balbuti', 'bredouill', 'prononç', 'prononc', 'chuchot', 'articul',
    'se demanda', 'se dit', 'pensa', 'pensai',
)
MOTIF_VERBE_PAROLE = re.compile(r'\b(?:%s)' % '|'.join(VERBES_DE_PAROLE),
                                re.IGNORECASE)
RE_FIN_DEUX_POINTS = re.compile(r':\s*$')


def introduit_une_replique(avant):
    """Le texte AVANT une ouverture de citation introduit-il une REPLIQUE ?

    « Et le More, riant, repondit : » -> oui.
    « Puis : » -> oui.
    « J'ai jamais eu » -> non (ni deux-points, ni verbe de parole).
    « Le sujet que j'avais donne etait : » -> oui, par prudence (voir plus bas).

    HISTORIQUE (21/09/2026 au soir) : la regle exigeait d'abord un VERBE DE PAROLE
    apres les deux-points. Laurent a entendu ce qu'elle laissait passer --
    « Puis : « D'accord, j'ai pu le faire. » » restait UN morceau, lu par le
    personnage. Les quatre cas du chapitre d'essai, lus un par un, montrent que
    le DEUX-POINTS juste avant la citation suffit :
        « Puis : »
        « Je lui ai accordé deux secondes de répit, puis : »
        « Elle m'a décoché un sourire carnassier puis a tourné la tête et crié : »
          (et « crié », participe, n'était pas reconnu non plus)
        « Je me suis cramponné… pour faire une seconde tentative : »
    Aucun n'a besoin d'un verbe. La regle est donc : **deux-points**, OU
    **verbe de parole** (pour les styles sans deux-points : « il murmura « Non » »).

    Les apostrophes TYPOGRAPHIQUES (’), celles des textes bien composes, sont
    ramenees a l'apostrophe droite AVANT l'analyse. Sans cela, les verbes
    pronominaux (s'ecria, s'ecrierent, s'exclama) passaient inapercus, le beat
    n'etait donc pas coupe et la narration restait collee a la replique -- donc
    lue par le personnage. Constat de Laurent le 21/09/2026, sur « Lazarille de
    Tormes » : « Frère Mariano, …, s’écria : « Jésus ! » » etait un seul
    morceau.

    Fonction PURE : c'est le garde-fou de la regle « dialogue », verifie par
    test_voix/test_decoupage_phrases.py.
    """
    if not avant:
        return False
    beat = avant.rstrip().replace('\u2019', "'")
    if not beat.strip(' \t:;,.\u2014\u2013-'):
        return False                      # rien avant la citation
    return beat.endswith(':') or bool(MOTIF_VERBE_PAROLE.search(beat))


def _couper_avant_replique(morceau):
    """Coupe (debut, fin, texte) en DEUX morceaux si c'est un vrai dialogue.

    Renvoie [morceau] quand la coupe ne s'applique pas -- c'est le cas normal.
    Les POSITIONS des deux moities restent exactes : la migration des index
    (`test_voix/_migrer_index_phrases.py`) en depend.
    """
    debut, fin, texte = morceau
    ouverture = texte.find('«')
    if ouverture <= 0:
        return [morceau]
    avant = texte[:ouverture]
    if not introduit_une_replique(avant):
        return [morceau]
    beat = avant.rstrip()
    blanc = len(avant) - len(beat)
    return [(debut, debut + len(beat), beat),
            (debut + len(beat) + blanc, fin, texte[len(beat) + blanc:])]



def _finit_par_abreviation(morceau):
    """Le dernier mot du morceau est-il une abréviation de civilité ?"""
    mots = morceau.split()
    if not mots:
        return False
    dernier = mots[-1].strip('«»"()')
    if not dernier:
        return False
    # Un guillemet fermant peut coller au mot : « … dit M. » »
    dernier = dernier.rstrip('»"')
    sans_point = dernier.rstrip('.')
    if sans_point not in ABREVIATIONS:
        return False
    return dernier.endswith('.') or sans_point in ABREVIATIONS_SANS_POINT


def _paragraphes(texte):
    """Les paragraphes examinés, dans l'ordre du texte."""
    return [p.strip() for p in re.split(MOTIF_PARAGRAPHES, texte or '')
            if len(p.strip()) >= MIN_PARAGRAPHE]
def _phrases_du_paragraphe(paragraphe, base, regle):
    """[(debut, fin, phrase)] d'un paragraphe, positions absolues."""
    morceaux = []
    position = 0
    for morceau in re.split(MOTIF_COUPE, paragraphe):
        debut = position
        position += len(morceau) + 1        # + 1 : l'espace consommé par la coupe
        morceaux.append((debut, morceau))

    if regle == REGLE_ANCIENNE:
        sortie = []
        for debut, morceau in morceaux:
            propre = morceau.strip()
            if len(propre) <= 3:
                continue
            # Le morceau peut commencer par des espaces : on ajuste le début.
            marge = len(morceau) - len(morceau.lstrip())
            sortie.append((base + debut + marge,
                           base + debut + marge + len(propre), propre))
        return sortie

    # Règle actuelle : on recolle les morceaux qui appartiennent à la même
    # phrase, c'est-à-dire ceux dont le dernier mot est une abréviation.
    sortie = []
    courant = None                      # [debut, fin, texte]
    for debut, morceau in morceaux:
        propre = morceau.strip()
        if not propre:
            continue
        marge = len(morceau) - len(morceau.lstrip())
        debut_abs = base + debut + marge
        fin_abs = debut_abs + len(propre)
        if courant is None:
            courant = [debut_abs, fin_abs, propre]
        else:
            courant[2] = courant[2] + ' ' + propre
            courant[1] = fin_abs
        if not _finit_par_abreviation(courant[2]):
            if len(courant[2]) > 3:
                sortie.append((courant[0], courant[1], courant[2]))
            courant = None
    if courant is not None and len(courant[2]) > 3:
        sortie.append((courant[0], courant[1], courant[2]))
    if regle == REGLE_DIALOGUE:
        # Regle « dialogue » : on separe le beat de narration de la replique,
        # morceau par morceau (voir introduit_une_replique ci-dessus).
        sortie = [piece for morceau in sortie
                  for piece in _couper_avant_replique(morceau)]
    return sortie


def phrases_avec_positions(texte, regle=REGLE_ACTUELLE):
    """[(debut, fin, phrase)] pour chaque phrase conservée, dans l'ordre.

    `debut`/`fin` sont des positions dans le texte complet du chapitre : c'est
    ce qui permet de savoir quelle ancienne phrase est devenue quelle nouvelle
    (migration des index, `test_voix/_migrer_index_phrases.py`).

    Avec `REGLE_ANCIENNE`, les morceaux coupés après une abréviation restent
    séparés (l'ancien comportement) ; avec `REGLE_ACTUELLE`, ils sont recollés ;
    avec `REGLE_DIALOGUE`, ils sont recollés ET la narration est séparée de la
    réplique quand un vrai dialogue est introduit par un beat.
    """
    resultat = []
    texte = texte or ''
    position = 0
    for brut in re.split(MOTIF_PARAGRAPHES, texte):
        debut_para = texte.find(brut, position) if brut else -1
        if debut_para < 0:
            debut_para = position
        position = debut_para + len(brut)
        paragraphe = brut.strip()
        if len(paragraphe) < MIN_PARAGRAPHE:
            continue
        base = debut_para + (len(brut) - len(brut.lstrip()))
        resultat.extend(_phrases_du_paragraphe(paragraphe, base, regle))
    return resultat


def phrases(texte, regle=REGLE_ACTUELLE):
    """La liste des phrases d'un chapitre (le texte seul)."""
    return [phrase for _debut, _fin, phrase in phrases_avec_positions(texte, regle)]

def phrases_d_un_paragraphe(paragraphe, regle=REGLE_ACTUELLE):
    """Les phrases d'UN paragraphe déjà isolé (recherche dans le livre)."""
    return [phrase for _debut, _fin, phrase
            in _phrases_du_paragraphe((paragraphe or '').strip(), 0, regle)]

