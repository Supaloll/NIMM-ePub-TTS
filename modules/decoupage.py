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
ABREVIATIONS = ('M', 'MM', 'Mme', 'Mmes', 'Mlle', 'Mlles', 'Mgr', 'Dr', 'Pr',
                'St', 'Ste', 'Mr', 'Mx')

# Celles qui s'écrivent SANS point mais ne finissent pas une phrase pour autant.
ABREVIATIONS_SANS_POINT = ('Mme', 'Mmes', 'Mlle', 'Mlles', 'Mgr')

REGLE_ANCIENNE = 'ancienne'
REGLE_ACTUELLE = 'actuelle'


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
    return sortie


def phrases_avec_positions(texte, regle=REGLE_ACTUELLE):
    """[(debut, fin, phrase)] pour chaque phrase conservée, dans l'ordre.

    `debut`/`fin` sont des positions dans le texte complet du chapitre : c'est
    ce qui permet de savoir quelle ancienne phrase est devenue quelle nouvelle
    (migration des index, `test_voix/_migrer_index_phrases.py`).

    Avec `REGLE_ANCIENNE`, les morceaux coupés après une abréviation restent
    séparés (l'ancien comportement) ; avec `REGLE_ACTUELLE`, ils sont recollés.
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

