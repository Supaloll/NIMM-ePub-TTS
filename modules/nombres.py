# -*- coding: utf-8 -*-
"""Les NOMBRES, ecrits en LETTRES avant la lecture (demande de Laurent, 03/10/2026).

POURQUOI. Un moteur de voix lit des LETTRES, pas des CHIFFRES. Le 03/10/2026,
Laurent a entendu « La vie prend des virages a 180 degres » sortir en
« ... a PI HUIT-CENT degres » -- deux tirages, deux fois le meme defaut, et
l'audio **plus court de 1,5 s** que la version en lettres. Le chiffre n'est donc
pas lu : il est DEVINE. (Et le meme moteur lit « cent quatre-vingts » tout seul.)

CE QUE FAIT CE MODULE : il reecrit les nombres en lettres AVANT de les donner au
moteur. Le TEXTE AFFICHE ne bouge jamais -- meme principe que
`modules/prononciation.py` et les abreviations. Appele depuis `_clean_text`,
donc il vaut pour TOUS les moteurs.

CE QU'IL TRAITE :
  - les entiers, jusqu'aux milliards, a l'orthographe francaise
    (« 180 » -> « cent quatre-vingts », « 1815 » -> « mille huit cent quinze »,
     « 71 » -> « soixante et onze », « 81 » -> « quatre-vingt-un ») ;
  - les nombres a virgule (« 3,5 » -> « trois virgule cinq ») ;
  - les pourcentages (« 50 % » -> « cinquante pour cent ») ;
  - les ordinaux en chiffres (« 1er » -> « premier », « 1re » -> « premiere »,
    « 2e » -> « deuxieme », « 9e » -> « neuvieme »).

CE QU'IL NE TOUCHE PAS, VOLONTAIREMENT -- et c'est ecrit ici pour qu'on ne
l'oublie pas :
  - un chiffre COLLE a un autre chiffre par un tiret ou une barre oblique
    (« 10-12 », « 22/11/63 ») : deux lectures sont possibles, et une mauvaise
    graphie serait PIRE que le defaut qu'elle corrige. A trancher avec Laurent,
    a l'oreille ;
  - les nombres romains (« XXe ») ;
  - les numeros de plus de 15 chiffres.

CE QUE L'OREILLE DE LAURENT VALIDERA ENSUITE : le choix « mille » ou « mil »
pour les annees (« 1815 » -> « mille huit cent quinze » ici).
"""
import re

UNITES = ["zero", "un", "deux", "trois", "quatre", "cinq", "six", "sept",
          "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze",
          "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
DIZAINES = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante",
            "", "quatre-vingt", ""]


def _sous_cent(n):
    """0 a 99, orthographe francaise."""
    if n < 20:
        return UNITES[n]
    dizaine, unite = divmod(n, 10)
    if dizaine == 7:                      # 70 a 79 : soixante + 10..19
        if unite == 1:
            return 'soixante et onze'
        return 'soixante-' + UNITES[10 + unite]
    if dizaine == 9:                      # 90 a 99 : quatre-vingt + 10..19
        return 'quatre-vingt-' + UNITES[10 + unite]
    if unite == 0:
        return 'quatre-vingts' if dizaine == 8 else DIZAINES[dizaine]
    if unite == 1 and dizaine != 8:       # 21, 31... 61 : « et un »
        return DIZAINES[dizaine] + ' et un'
    return DIZAINES[dizaine] + '-' + UNITES[unite]


def _sous_mille(n):
    """0 a 999."""
    if n < 100:
        return _sous_cent(n)
    centaines, reste = divmod(n, 100)
    if centaines == 1:
        mot = 'cent'
    else:
        mot = UNITES[centaines] + ' cent' + ('s' if reste == 0 else '')
    if reste:
        mot += ' ' + _sous_cent(reste)
    return mot


def _sans_s_final(mot):
    """« quatre-vingts » et « deux cents » perdent leur s devant mille/million."""
    if mot.endswith('vingts') or mot.endswith('cents'):
        return mot[:-1]
    return mot


def en_lettres(n):
    """Un entier en lettres (jusqu'aux milliards)."""
    if n == 0:
        return 'zero'
    if n < 0:
        return 'moins ' + en_lettres(-n)
    morceaux = []
    milliards, reste = divmod(n, 10 ** 9)
    millions, reste = divmod(reste, 10 ** 6)
    milliers, reste = divmod(reste, 1000)
    if milliards:
        morceaux.append(_sans_s_final(_sous_mille(milliards)) + ' milliard'
                        + ('s' if milliards > 1 else ''))
    if millions:
        morceaux.append(_sans_s_final(_sous_mille(millions)) + ' million'
                        + ('s' if millions > 1 else ''))
    if milliers:
        if milliers == 1:
            morceaux.append('mille')
        else:
            morceaux.append(_sans_s_final(_sous_mille(milliers)) + ' mille')
    if reste:
        morceaux.append(_sous_mille(reste))
    return ' '.join(morceaux)


def ordinal(n):
    """Le mot ordinal d'un entier : 1 -> premier, 2 -> deuxieme, 5 -> cinquieme."""
    if n == 1:
        return 'premier'
    if n == 0:
        return 'zero'
    mot = en_lettres(n)
    if mot.endswith('cinq'):              # cinq -> cinquieme
        mot += 'u'
    elif mot.endswith('neuf'):            # neuf -> neuvieme
        mot = mot[:-1] + 'v'
    if mot.endswith('vingts'):            # quatre-vingts -> quatre-vingtieme
        mot = mot[:-1]
    if mot.endswith('e'):                 # quatre -> quatrieme, onze -> onzieme
        mot = mot[:-1]
    return mot + 'ieme'


# Un nombre qu'on accepte de reecrire : ni colle a un autre nombre par un tiret
# ou une barre oblique, ni colle a d'autres chiffres. Ces bornes laissent donc
# TRANQUILLES « 22/11/63 » et « 10-12 », qui demandent un CHOIX de lecture.
MOTIF_POURCENT = re.compile(r'(?<![\d/\-])(\d{1,15})\s*%')
MOTIF_DECIMAL = re.compile(r'(?<![\d/\-])(\d{1,15}),(\d{1,6})(?![\d/\-])')
MOTIF_ORDINAL = re.compile(r'(?<![\d/\-])(\d{1,4})(er|re|ème|eme|e)(?!\w)',
                           re.IGNORECASE)
MOTIF_NOMBRE = re.compile(r'(?<![\d/\-])(\d{1,15})(?![\d/\-])')


def _remplacer_pourcent(trouve):
    return en_lettres(int(trouve.group(1))) + ' pour cent'


def _remplacer_decimal(trouve):
    return (en_lettres(int(trouve.group(1))) + ' virgule '
            + ' '.join(UNITES[int(chiffre)] for chiffre in trouve.group(2)))


def _remplacer_ordinal(trouve):
    nombre = int(trouve.group(1))
    suffixe = trouve.group(2).lower()
    if nombre == 1 and suffixe in ('re', 'ème', 'eme'):
        return 'premiere'
    return ordinal(nombre)


def _remplacer_nombre(trouve):
    return en_lettres(int(trouve.group(1)))


def pour_lecture(text):
    """Le texte avec ses nombres ECRITS EN LETTRES.

    Meme contrat que `modules/prononciation.py` : on ne touche jamais au texte
    affiche, seulement a celui qu'on donne au moteur.

    L'ORDRE COMPTE : le pourcentage, le decimal et l'ordinal AVANT le nombre
    seul -- sinon « 50 % » serait vu comme « cinquante » puis « % ».
    """
    if not text:
        return text
    text = MOTIF_POURCENT.sub(_remplacer_pourcent, text)
    text = MOTIF_DECIMAL.sub(_remplacer_decimal, text)
    text = MOTIF_ORDINAL.sub(_remplacer_ordinal, text)
    text = MOTIF_NOMBRE.sub(_remplacer_nombre, text)
    return text
