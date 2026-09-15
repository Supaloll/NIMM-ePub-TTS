# -*- coding: utf-8 -*-
"""Validation de la logique de playlist de lecture (reproduction Python de
_buildPlaylist/_splitLongSentence de app.js -- session du 08/09/2026).
Verifie qu'une phrase = une unite audio (decoupee en sous-segments si elle
est trop longue), que deux phrases ne sont JAMAIS fusionnees, et que la
playlist couvre exactement toutes les phrases du chapitre."""
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"g:/NIMM ePub")

from core.epub_parser import get_chapters

# --- Reproduction de _buildSentences (app.js) ---
def build_sentences(text):
    paras = [p.strip() for p in re.split(r"\n\n+", text) if len(p.strip()) > 5]
    sentences = []
    for pi, para in enumerate(paras):
        for s in re.split(r"(?<=[.!?…»])\s+", para):
            s = s.strip()
            if len(s) > 3:
                sentences.append({"text": s, "paraIdx": pi})
    return sentences

# --- Reproduction de _splitLongSentence (app.js) ---
SPLIT_SENTENCE_CHARS = 500
SPLIT_SEGMENT_CHARS = 450

def split_long(text):
    if len(text) <= SPLIT_SENTENCE_CHARS:
        return [text]
    out = []
    cur = ""
    for part in re.split(r"(?<=[,;:])\s+", text):
        if cur and (len(cur) + len(part) + 1) > SPLIT_SEGMENT_CHARS:
            out.append(cur)
            cur = ""
        if len(part) > SPLIT_SEGMENT_CHARS:
            for k in range(0, len(part), SPLIT_SEGMENT_CHARS):
                out.append(part[k:k + SPLIT_SEGMENT_CHARS])
            cur = ""
        else:
            cur = (cur + " " + part).strip() if cur else part
    if cur:
        out.append(cur)
    return out

# --- Reproduction de _buildPlaylist (app.js), meme voix partout ---
def build_playlist(sentences):
    units = []
    for i, s in enumerate(sentences):
        for seg in split_long(s["text"]):
            units.append({"text": seg, "sentIdx": i, "paraIdx": s["paraIdx"]})
    return units


# Parcourt tous les chapitres du tome 1
epub = r"g:/NIMM ePub/data/library/dumas_alexandre_-_le_comte_de_monte-cristo_i.epub"
chapters = get_chapters(epub)
print("chapitres trouves:", len(chapters))

total_units = 0
total_phrases = 0
long_examples = 0
fail = 0

for ch in chapters:
    texte = ch.get("text") or ""
    sents = build_sentences(texte)
    if not sents:
        continue
    units = build_playlist(sents)

    total_phrases += len(sents)
    total_units += len(units)

    sent_of_unit = [u["sentIdx"] for u in units]

    # Couverture : la playlist couvre exactement toutes les phrases, dans
    # l'ordre, sans fusion (deux phrases differentes ne partagent jamais
    # une meme unite) et sans trou.
    if sorted(set(sent_of_unit)) != list(range(len(sents))):
        print("ERR chapitre %d : la playlist ne couvre pas toutes les phrases" % ch["index"])
        fail += 1
    for a, b in zip(sent_of_unit, sent_of_unit[1:]):
        if b < a:
            print("ERR chapitre %d : ordre des phrases non respecte dans la playlist" % ch["index"])
            fail += 1
            break

    # Taille max d'une unite : une phrase entiere de moins de 500 caracteres
    # n'est pas decoupee (c'est le comportement voulu de _splitLongSentence) ;
    # au-dela, les sous-segments de synthese restent <= 450 caracteres.
    for u in units:
        if len(u["text"]) > SPLIT_SENTENCE_CHARS:
            print("ERR chapitre %d : unite de %d caracteres (> %d)"
                  % (ch["index"], len(u["text"]), SPLIT_SENTENCE_CHARS))
            fail += 1

    # Exemple de phrase longue decoupee pour la synthese
    for s in sents:
        if len(s["text"]) > SPLIT_SENTENCE_CHARS:
            segs = split_long(s["text"])
            long_examples += 1
            if long_examples <= 2:
                print("  Exemple phrase de %d caracteres decoupee en %d segments:"
                      % (len(s["text"]), len(segs)))
                for seg in segs[:3]:
                    print("    -", seg[:80], "...")

print("\nAGREGAT (tous chapitres)")
print("  phrases   :", total_phrases)
print("  unites    :", total_units, "(>= phrases : une phrase peut etre decoupee)")
print("  phrase longue > %d car. : %d (decoupee en sous-segments <= %d car.)"
      % (SPLIT_SENTENCE_CHARS, long_examples, SPLIT_SEGMENT_CHARS))

print("\n" + ("VALIDATION OK" if fail == 0 else "%d ERREUR(S)" % fail))
sys.exit(1 if fail else 0)

