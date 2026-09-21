# -*- coding: utf-8 -*-
"""Prononciation française imposée : les mots que le phonémiseur prend pour de
l'anglais, écrits pour la LECTURE (Kokoro et Piper).

**Pourquoi ce module** (cause établie le 20/09/2026 à l'atelier NIMM Voix,
mesure et verdict d'oreille dans son `ARCHITECTURE.md`) :

1. pour `lang=fr-fr`, Kokoro n'a **pas** de phonémiseur français : il appelle
   **espeak-ng** (via `phonemizer`), un moteur multi-langues dont les
   dictionnaires de toutes les langues cohabitent ;
2. quand un mot est reconnu dans le dictionnaire **anglais** — le cas de
   beaucoup de prénoms (`Andrea`, `Marthe`, `Arthur`, `Nathan`…) —, espeak-ng
   **change de langue** et **marque la frontière** : `(en)ˈandɹiə(fr)`. Le
   tokenizer de kokoro-onnx garde ces caractères (ils sont dans son
   vocabulaire) : Laurent entendait « énAndréa fe » ;
3. **même sans la marque**, le mot reste prononcé à l'anglaise : c'est le cas
   de Piper, qui la retire — `Marthe` devient *marth*, `Nathan` *néythane*.

**Le remède retenu par son oreille** (« c'est toujours C qui prononce les
prénoms correctement », verdict du 20/09/2026 sur le lot A/B/C) : **imposer les
sons français**. Deux mécanismes, tous les deux dans `modules/tts.py` :

- donner les **phonèmes** au moteur (`is_phonemes=True`) après avoir retiré les
  marques de langue → plus aucune syllabe inventée, **partout**, même sur les
  mots que cette table ne connaît pas ;
- **réécrire le mot dans la version PARLÉE seulement** (ce module-ci) → le texte
  affiché ne bouge jamais, exactement comme les abréviations et les majuscules.

**Comment on ajoute une entrée** : on la **mesure** d'abord au phonémiseur et on
l'**écoute** (`test_voix/_mesurer_prononciation_kokoro.py`, qui écrit la sortie
du phonémiseur et un lot d'écoute A/B/C). Une graphie fausse serait **pire** que
le défaut qu'elle corrige : elle s'entendrait dans tout le livre.
"""

import re

# La table. Clé : le mot tel qu'il est écrit dans le livre (en minuscules).
# Valeur : la graphie qui donne le son français.
#   **TOUTES LES ENTRÉES SONT VALIDÉES À L'OREILLE DE LAURENT** (21/09/2026) :
#   les quatre premières venaient du lot de l'atelier NIMM Voix (20/09/2026,
#   graphies vérifiées françaises), et les cinq suivantes ont été confirmées sur
#   le lot de ce projet — « tous les « après » sont ok, c'est parfait ! »
#   - `Andrea → Andréa`, `Marthe → Marte`, `Arthur → Artur`, `Nathan → Natan` ;
#   - `Ethan → Étan`, `Maëlys → Maélis`, `Mathis → Matis`, `Noah → Noa` ;
#   - `dos → dô` : mot français ordinaire que l'analyse rate (l'anglais « dos »
#     se dit *doss*) ; « dô » redonne le son français /do/.
PRONONCIATION = {
    "andrea":  "Andréa",
    "arthur":  "Artur",
    "marthe":  "Marte",
    "nathan":  "Natan",
    "ethan":   "Étan",
    "maëlys":  "Maélis",
    "mathis":  "Matis",
    "noah":    "Noa",
    "dos":     "dô",
}

# L'apostrophe COURBE empêche espeak-ng de reconnaître le mot français
# (« d’aujourd’hui » part en anglais) : on la remet droite pour la lecture.
# Relevé du 20/09/2026 : 3 occurrences dans le tome 5 du Comte de Monte-Cristo.
APOSTROPHES = {"\u2019": "'", "\u2018": "'"}


def _respecter_la_casse(mot_source: str, graphie: str) -> str:
    """« ANDREA » → « Andréa », « andrea » → « andréa », « Andrea » → « Andréa ».

    Un mot **tout en majuscules** est ramené en casse de titre, jamais laissé en
    capitales : espeak-ng **épelle** les mots tout en capitales
    (« A-N-D-R-É-A »), et ce serait pire que le défaut qu'on corrige. La casse
    n'a par ailleurs aucun effet sur les sons.
    """
    if mot_source.isupper():
        return graphie[:1].upper() + graphie[1:]
    if mot_source[:1].islower() and graphie[:1].isupper():
        return graphie[:1].lower() + graphie[1:]
    return graphie


def pour_lecture(text: str) -> str:
    """Le texte tel qu'il faut le DONNER au phonémiseur (Kokoro, Piper).

    Ne touche jamais au texte affiché : appelé juste avant la synthèse, comme
    les abréviations (`_expand_abbreviations`) et les majuscules.
    """
    if not text:
        return text

    for courbe, droite in APOSTROPHES.items():
        text = text.replace(courbe, droite)

    if not PRONONCIATION:
        return text

    # Les clés les plus LONGUES d'abord : « mathis » doit l'emporter sur une
    # éventuelle entrée plus courte qui le préfixerait.
    motif = r"\b(?:%s)\b" % "|".join(
        re.escape(cle) for cle in sorted(PRONONCIATION, key=len, reverse=True))

    def _remplacer(trouve):
        mot = trouve.group(0)
        return _respecter_la_casse(mot, PRONONCIATION[mot.lower()])

    return re.sub(motif, _remplacer, text, flags=re.IGNORECASE)
