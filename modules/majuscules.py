# -*- coding: utf-8 -*-
"""Les mots TOUT EN MAJUSCULES : les remettre en casse normale avant le moteur.

Demande de Laurent (19/09/2026) : « les mots en majuscule donnent une
prononciation bizarre, il faudrait modifier pour qu'ils soient lus normalement ».

Le probleme, MESURE sur ses livres (outil
`test_voix/_mesurer_majuscules_20260919.py --tous`) : il y a DEUX familles
indiscernables a l'oeil nu.
  - des **mots de la langue** mis en majuscules pour insister (« c'est LUI »,
    « LA raison ») : les moteurs neuronaux les traitent comme des sigles, et la
    lecture devient bizarre. 22/11/63 en compte **531 phrases** touchees ;
  - de **vrais sigles** (« JFK », « FBI », « DSK », « TSBD ») : la, l'epellation
    est VOULUE.

Comment les trier sans liste a maintenir : un mot en majuscules est un mot de la
langue s'il est ecrit **aussi en casse normale ailleurs dans le meme livre**
(« DE » et « de », « JIM » et « Jim »). S'il n'apparait **jamais** autrement,
c'est un sigle. Mesure sur 22/11/63 : **682 mots distincts convertibles**
(1 423 occurrences), tous les sigles preserves.

Le texte AFFICHE n'est jamais modifie : seule la version parlee change.
"""

import re

# Un mot de 2 lettres et plus, TOUT en majuscules (« DE », « BASTILLE », « JIM »).
# Une lettre seule n'est pas touchee : « M. » (civilité) ou « A » gardent leur sens.
MOT_MAJUSCULES = re.compile(r'\b[A-Z\u00c0-\u00d6\u00d8-\u00de]{2,}\b')

# Les chiffres romains s'ecrivent en majuscules et ne sont PAS des mots :
# « XIV », « MCMXC ». On n'y touche jamais.
ROMAIN = re.compile(r'^[IVXLCDM]+$')

# Un mot quelconque de 2 lettres et plus (majuscule initiale acceptee) : sert a
# construire le vocabulaire. ATTENTION : ne compter que les minuscules
# raterait « Jim » (majuscule initiale) et « JIM » serait pris pour un sigle.
MOT_QUELCONQUE = re.compile(r"[\w\u00c0-\u00ff\u2019'-]{2,}", re.UNICODE)


def enrichir_vocabulaire(texte, vocabulaire):
    """Ajoute au vocabulaire les mots ecrits en casse NORMALE dans ce texte.

    `vocabulaire` : {mot_en_minuscules: forme_canonique}. La forme canonique est
    celle rencontree en premier (« Bastille », « Jim ») : c'est elle qui
    remplacera la version en majuscules, pour garder un texte propre.
    """
    for mot in MOT_QUELCONQUE.findall(texte or ''):
        if MOT_MAJUSCULES.fullmatch(mot) or ROMAIN.match(mot):
            continue            # tout en majuscules : candidat a convertir
        cle = mot.lower()
        if cle not in vocabulaire:
            vocabulaire[cle] = mot
    return vocabulaire


def reduire_majuscules(text, vocabulaire):
    """Met en casse normale les mots en majuscules CONNUS du livre.

    Un mot en majuscules qui n'est pas au vocabulaire est laisse tel quel :
    c'est un sigle (ou un mot du livre pas encore lu).
    """
    if not text or not vocabulaire:
        return text

    def remplacer(m):
        mot = m.group(0)
        if ROMAIN.match(mot):
            return mot
        return vocabulaire.get(mot.lower(), mot)

    return MOT_MAJUSCULES.sub(remplacer, text)
