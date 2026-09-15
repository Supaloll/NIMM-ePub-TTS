# -*- coding: utf-8 -*-
"""Verification du pool automatique du casting apres l'arrivee de XTTS v2.

A lancer avec le Python du lecteur :
    python test_voix/test_pool_casting.py

Ce que le script verifie (regle des paliers d'etoiles, decision de Laurent
du 15/09/2026 -- elle remplace l'ordre du 14/09/2026) :
  1. le pool se parcourt par PALIERS D'ETOILES (3, puis 2, puis 1) et, dans
     chaque palier, Edge, puis XTTS v2, puis Kokoro ;
  2. les etoiles des voix Edge sont bien celles du catalogue FRENCH_VOICES
     de main.py (c'est lui qui les transmet au module au demarrage) ;
  3. une voix notee 0 etoile est ECARTEE du pool automatique, sur tous les
     moteurs (Edge, Kokoro comme XTTS) -- c'est le moyen de retirer une voix
     du casting automatique ;
  4. Kyutai est ABSENT du pool automatique (reste choisissable a la main) ;
  5. un personnage important recoit une voix du palier 3 etoiles ;
  6. un petit role (moins de 8 repliques) recoit la voix Piper generique
     (Siwis pour une femme, Tom pour un homme) ;
  7. le seuil des petits roles du client (frontend/app.js) est le meme que
     celui du serveur : sinon la fenetre du casting annoncerait « a caster »
     sur des personnages que le serveur traite comme normaux.
"""

import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

from modules import voice_casting as vc                    # noqa: E402
from modules.tts import KOKORO_VOICES, KYUTAI_VOICES, XTTS_VOICES  # noqa: E402

# main.py porte le catalogue des voix Edge (FRENCH_VOICES) et appelle
# vc.definir_voix_edge() au demarrage : c'est la chaine reelle du programme,
# le test la suit plutot que de recopier des valeurs.
import main                                                # noqa: E402

NOTES_EDGE   = {v["id"]: int(v.get("stars", 0)) for v in main.FRENCH_VOICES}
NOTES_XTTS   = {v["id"]: int(v.get("stars", 0)) for v in XTTS_VOICES}
NOTES_KOKORO = {v["id"]: int(v.get("stars", 0)) for v in KOKORO_VOICES}

# Ordre des moteurs DANS un palier d'etoiles (decision du 15/09/2026).
RANG_FAMILLE = {"edge": 0, "xtts": 1, "kokoro": 2}


def famille(identifiant):
    if identifiant.startswith("xtts:"):
        return "xtts"
    if identifiant.startswith("kokoro:"):
        return "kokoro"
    return "edge"


def etoiles(identifiant):
    return {"xtts": NOTES_XTTS, "kokoro": NOTES_KOKORO}.get(
        famille(identifiant), NOTES_EDGE).get(identifiant, 0)


def main_test():
    # On repasse par la fonction de main.py : le test verifie la chaine
    # complete, pas seulement le calcul interne du module.
    vc.definir_voix_edge(main.FRENCH_VOICES)

    print("1) pool compose par paliers d'etoiles, Edge puis XTTS puis Kokoro")
    for genre, pool in (("F", vc.DEDICATED_VOICES_F), ("M", vc.DEDICATED_VOICES_M)):
        cles = [(-etoiles(v), RANG_FAMILLE[famille(v)]) for v in pool]
        assert cles == sorted(cles), "l'ordre des paliers est faux : %s" % cles
        details = []
        for palier in (3, 2, 1):
            familles = [f for f in ("edge", "xtts", "kokoro")
                        if any(etoiles(v) == palier and famille(v) == f for v in pool)]
            details.append("%d* %s" % (palier, "+".join(familles) or "-"))
        print("   %s : %d voix au total | %s" % (genre, len(pool), " ; ".join(details)))
        print("      premieres : %s" % ", ".join(pool[:4]))

    print("2) les etoiles des voix Edge viennent du catalogue de main.py")
    for identifiant, note in vc._EDGE_STARS.items():
        attendu = NOTES_EDGE.get(identifiant)
        assert attendu is None or note == attendu, \
            "%s : %s dans le pool, %s dans le catalogue" % (identifiant, note, attendu)
    assert vc.DEDICATED_VOICES_F[0] == "fr-FR-DeniseNeural", vc.DEDICATED_VOICES_F[0]
    assert vc.DEDICATED_VOICES_M[0] == "fr-FR-HenriNeural", vc.DEDICATED_VOICES_M[0]

    print("3) voix notees 0 etoile ECARTEES du pool (tous les moteurs)")
    for genre, pool in (("F", vc.DEDICATED_VOICES_F), ("M", vc.DEDICATED_VOICES_M)):
        nulles = [v for v in pool if etoiles(v) <= 0]
        assert not nulles, "voix a 0 etoile encore dans le pool %s : %s" % (genre, nulles)
    ecartees = {"edge": [i for i, n in NOTES_EDGE.items() if n == 0],
                "xtts": [i for i, n in NOTES_XTTS.items() if n == 0],
                "kokoro": [i for i, n in NOTES_KOKORO.items() if n == 0]}
    for moteur, identifiants in ecartees.items():
        for identifiant in identifiants:
            assert identifiant not in vc.DEDICATED_VOICES_F
            assert identifiant not in vc.DEDICATED_VOICES_M
        print("   %-6s %s" % (moteur, ", ".join(identifiants) or "aucune"))

    print("4) Kyutai absent du pool automatique")
    for genre, pool in (("F", vc.DEDICATED_VOICES_F), ("M", vc.DEDICATED_VOICES_M)):
        kyutai = [v for v in pool if v.startswith("kyutai:")]
        assert not kyutai, "Kyutai ne doit plus etre dans le pool : %s" % kyutai

    print("5) attribution automatique (6 personnages importants)")
    fiche = [
        {"nom": "Alice", "genre": "F", "age": "adulte"},
        {"nom": "Beatrice", "genre": "F", "age": "jeune"},
        {"nom": "Camille", "genre": "F", "age": "age"},
        {"nom": "Daniel", "genre": "H", "age": "adulte"},
        {"nom": "Etienne", "genre": "H", "age": "adulte"},
        {"nom": "Felix", "genre": "H", "age": "jeune"},
    ]
    compte = {p["nom"]: 40 for p in fiche}
    voix = vc.assign_voices(fiche, compte)
    for nom in sorted(voix):
        print("   %-10s %-34s %s" % (nom, voix[nom]["voice_id"], voix[nom]["pitch"]))
    # Les roles les plus presents doivent partir du PALIER 3 etoiles : c'est
    # tout l'interet de la regle (les meilleurs timbres aux roles principaux).
    palier3 = set(v for v in vc.DEDICATED_VOICES_F if etoiles(v) == 3)
    palier3 |= set(v for v in vc.DEDICATED_VOICES_M if etoiles(v) == 3)
    hors_palier = {n: v["voice_id"] for n, v in voix.items()
                   if v["voice_id"] not in palier3}
    assert not hors_palier, "role important hors du palier 3 etoiles : %s" % hors_palier
    assert voix["Alice"]["voice_id"] == "fr-FR-DeniseNeural"
    assert voix["Daniel"]["voice_id"] == "fr-FR-HenriNeural"

    print("6) petit role (2 repliques) -> AUCUNE voix dediee (lu par le narrateur)")
    fiche2 = fiche + [{"nom": "Petit", "genre": "H", "age": "adulte"},
                      {"nom": "Petite", "genre": "F", "age": "adulte"}]
    compte2 = dict(compte)
    compte2["Petit"] = 2
    compte2["Petite"] = 2
    voix2 = vc.assign_voices(fiche2, compte2)
    print("   Petit  -> %r" % voix2["Petit"]["voice_id"])
    print("   Petite -> %r" % voix2["Petite"]["voice_id"])
    # Regle du 15/09/2026 (decision de Laurent apres l'ecoute de Shantaram) :
    # les petits roles n'ont plus de voix dediee NI de voix generique Piper
    # (« inaudibles, vraiment moches »). Leur voice_id est VIDE : le lecteur
    # les lit avec la voix du NARRATEUR, et la ligne reste visible dans la
    # fenetre du casting sous la mention « (lu par le narrateur) ».
    assert voix2["Petit"]["voice_id"] == "", voix2["Petit"]["voice_id"]
    assert voix2["Petite"]["voice_id"] == "", voix2["Petite"]["voice_id"]
    assert voix2["Petit"]["pitch"] == "+0Hz", voix2["Petit"]["pitch"]
    # ...et un petit role ne consomme PAS une voix du pool dedie.
    dediees_utilisees = [v["voice_id"] for n, v in voix2.items()
                         if n not in ("Petit", "Petite")]
    assert "" not in dediees_utilisees

    print("7) seuil des petits roles : le client et le serveur doivent dire pareil")
    with open(os.path.join(RACINE, "frontend", "app.js"), encoding="utf-8") as f:
        js = f.read()
    trouve = re.search(r"_CAST_MINOR_THRESHOLD\s*=\s*(\d+)", js)
    assert trouve, "constante _CAST_MINOR_THRESHOLD absente de frontend/app.js"
    seuil_client = int(trouve.group(1))
    print("   client %d / serveur %d" % (seuil_client, vc.MINOR_THRESHOLD))
    assert seuil_client == vc.MINOR_THRESHOLD, \
        "le seuil du client (%d) differe de celui du serveur (%d)" \
        % (seuil_client, vc.MINOR_THRESHOLD)

    print("")
    print("TOUT EST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main_test())
