# -*- coding: utf-8 -*-
"""Test rapide du pretraitement TTS (encodage, points de suspension, chunks)."""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"g:/NIMM ePub")

from modules.tts import _clean_text, _split_into_chunks, _split_long_sentence

fail = 0

def check(label, got, expected):
    global fail
    ok = got == expected
    if not ok:
        fail += 1
        print("ERR", label, "->", repr(got), "attendu", repr(expected))
    else:
        print("OK ", label, "->", repr(got))

# 1. Points de suspension normalises (pas de pause par point)
check("suspension", _clean_text("Bonjour... comment vas-tu ?"), "Bonjour… comment vas-tu ?")
check("suspension2", _clean_text("Il dit . . . M. Dantes."), "Il dit… Monsieur Dantes.")

# 2. Retours a la ligne -> espace simple (pas de virgule)
check("newline", _clean_text("Ligne 1\nligne 2."), "Ligne 1 ligne 2.")

# 3. Abreviation developpee, ponctuation francaise conservee
check("guillemet", _clean_text("\"Au revoir\""), "\"Au revoir\"")
# Attendu mis a jour le 18/09/2026 : depuis le 17/09/2026 au soir, le
# deux-points devient une virgule (le moteur n'en faisait AUCUNE pause, constat
# de Laurent) -- ce test datait d'avant et n'avait pas suivi.
check("guillemet2", _clean_text("Elle dit : « Bonjour »"), "Elle dit, « Bonjour »")

# 4. Espaces parasites avant point/virgule supprimes, espace avant ? gardee
check("espace_ponct", _clean_text("Une phrase , puis une autre ."), "Une phrase, puis une autre.")

# 5. Fin par suspension -> pas de point ajoute
check("fin_suspension", _clean_text("Et soudain..."), "Et soudain…")

# 6. Chunk : phrase trop longue coupee aux virgules, jamais en milieu de mot
long = "mot1, mot2, " * 300  # 2100 caracteres avec virgules
chunks = _split_into_chunks(long, max_chars=1000)
print("OK  chunk_long", len(chunks), "morceaux, chacun <= 1015 chars",
      all(len(c) <= 1015 for c in chunks))
for c in chunks:
    if c.endswith("mot") or c.startswith(","):
        print("ERR chunk_long coupe en plein milieu de mot:", repr(c[-30:]))
        fail += 1

# 7. Phrase longue -> sous-segments aux virgules
segs = _split_long_sentence("a, b, c, " * 100, 450)
print("OK  split_long", len(segs), "segments, max", max(len(s) for s in segs))
if any(len(s) > 470 for s in segs):
    print("ERR split_long segment trop long")
    fail += 1

# 8. Chunk apres clean_text (production : _clean_text puis _split_into_chunks)
# Attendu mis a jour le 18/09/2026 : le point d'exclamation est retire du texte
# envoye au moteur (il faisait monter la voix). Le « ! » de la phrase affichee
# ne change pas ; seule la version parlee devient un point.
cleaned = _clean_text("Premiere phrase...\nSeconde phrase!")
check("chunk_suspension", _split_into_chunks(cleaned, max_chars=4000),
      ["Premiere phrase… Seconde phrase."])

# 9. Fin de segment sur virgule -> point final (pas de "virgule puis point")
check("fin_virgule", _clean_text("Premier morceau, seconde moitie,"),
      "Premier morceau, seconde moitie.")
check("fin_virgule2", _clean_text("Il repondit, puis se tut ;"),
      "Il repondit, puis se tut.")

print("\n" + ("TOUS LES TESTS PASSENT" if fail == 0 else f"{fail} TEST(S) EN ERREUR"))
sys.exit(1 if fail else 0)
