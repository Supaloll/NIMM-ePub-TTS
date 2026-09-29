# -*- coding: utf-8 -*-
"""Recopie les notes d'ecoute des voix XTTS sur leurs jumelles QWEN, et applique
le verdict d'ecoute de Laurent du 30/09/2026 sur les 25 voix CML-TTS.

Pourquoi (30/09/2026) : NIMM Voix a clone les 25 voix CML-TTS qui restaient
(« vague 6 », lot `cml_restants`) et les a deposees ici via le memo
`_MEMO_25_VOIX_CML_20260930/`. Ces 25 voix portent le MEME identifiant que des
voix XTTS deja au catalogue (`xtts:cml3344` : meme extrait que `qwen:cml3344`),
donc leurs notes d'ecoute existent deja -- cote XTTS.

DEUX ETAPES, dans cet ordre :

  1. HERITAGE : pour chaque cle `xtts:` dont la jumelle `qwen:` n'a pas encore
     de fiche ET dont la jumelle est bien au catalogue, recopier la fiche telle
     quelle. Meme mecanique que `_heriter_annotations_kokoro_vers_qwen.py`, et
     memes garde-fous : jamais d'ecrasement, cles `xtts:` conservees.

  2. VERDICT : Laurent a REECOUTE les 25 clones le 30/09/2026. Ses etoiles, ses
     accents et ses mots sont dans `VERDICT_30_09` ci-dessous, recopies mot pour
     mot du memo. 12 voix sur 25 changent d'etoiles par rapport a la fiche XTTS
     -- c'est SON oreille du 30/09 qui fait foi, pas celle du 14/09.

CE QUI EST TOUCHE, ET CE QUI NE L'EST PAS
    - `stars`   : remplace (verdict du 30/09) ;
    - `note`    : ses mots du 30/09, suivis de « -- avant : <ancienne remarque> »
      quand la fiche heritee en portait une autre. Rien n'est perdu : les
      remarques du 14/09 (« top ! », « souffle », « jeune homme »...) restent
      lisibles ;
    - `accent`  : remplace uniquement la ou il l'a dit (`cml1649` anglais --
      c'est une CORRECTION : la fiche XTTS disait « allemand »). Pour `cml7239`,
      « leger accent Maghreb » n'est pas une valeur de `CRITERES_VOIX`
      (`main.py`) : c'est donc `autre`, et son mot reste dans la note ;
    - le reste (timbre, debit, age, role, registre, genre) : herite de la
      jumelle, jamais invente. `cml7614` herite ainsi « enfant ».

SECURITE : rapport seul par defaut. Avec --ecrire, copie datee de
`data/annotations_voix.json` (`.bak_avant_heritage_cml_<AAAAMMJJ>_<HHMM>`) puis
ecriture. Retour arriere : recopier la copie.

Usage :
    python test_voix/_heriter_annotations_xtts_vers_qwen.py           # rapport
    python test_voix/_heriter_annotations_xtts_vers_qwen.py --ecrire
"""
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
NOTES = RACINE / "data" / "annotations_voix.json"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(RACINE))

from modules.tts import QWEN_VOICES  # noqa: E402

# Verdict d'ecoute de Laurent, 30/09/2026, mot pour mot
# (`_MEMO_25_VOIX_CML_20260930/MEMO_25_VOIX_CML_30-09-2026_pour_la_session_NIMM_ePub.md`,
# tableau du point 3). Une voix absente d'ici n'a pas ete re-jugee : elle garde
# la fiche heritee de sa jumelle XTTS.
VERDICT_30_09 = {
    "cml10065": {"stars": 2, "note": "OK"},
    "cml12501": {"stars": 3, "note": "OK"},
    "cml12512": {"stars": 3, "note": "OK"},
    "cml12823": {"stars": 3, "note": "OK"},
    # `cml1649` : l'accent est ALLEMAND, pas anglais. Laurent a corrige le memo
    # du 30/09/2026 le soir meme (« au temps pour moi ») : sa fiche XTTS du
    # 14/09 disait deja « accent allemand », et c'est elle qui avait raison.
    "cml1649": {"stars": 3, "note": "OK, accent allemand",
                "accent": "allemand"},
    "cml1840": {"stars": 3, "note": "OK"},
    "cml1869": {"stars": 3, "note": "OK"},
    "cml2033": {"stars": 3, "note": "OK"},
    "cml2316": {"stars": 1, "note": "OK"},
    "cml2771": {"stars": 3,
                "note": "reprise : parasite de debut (\"ter\") disparu, 5/5"},
    "cml3060": {"stars": 2, "note": "OK"},
    "cml3182": {"stars": 3,
                "note": "reprise : parasite (\"ets\") disparu, 5/5"},
    "cml3344": {"stars": 3, "note": "OK"},
    "cml3503": {"stars": 3, "note": "OK"},
    "cml5525": {"stars": 3, "note": "OK"},
    "cml5526": {"stars": 2, "note": "reprise : parasite disparu, 5/5"},
    "cml6070": {"stars": 2, "note": "OK"},
    "cml6249": {"stars": 3,
                "note": "OK, accent paysan -- \"roule les R, excellent !\"",
                "accent": "paysan"},
    "cml6348": {"stars": 2, "note": "OK"},
    "cml6381": {"stars": 2, "note": "OK"},
    "cml7239": {"stars": 3,
                "note": "reprise : 5/5, \"leger accent Maghreb\"",
                "accent": "autre"},
    "cml7377": {"stars": 3, "note": "OK"},
    "cml7423": {"stars": 2, "note": "OK, accent canadien"},
    "cml7614": {"stars": 3, "note": "OK -- une voix d'ENFANT"},
    "cml9804": {"stars": 3, "note": "OK"},
}

# HORS DU LOT DU 30/09/2026, et volontairement (voir la raison de chaque voix) :
# ces deux jumelles XTTS n'ont JAMAIS eu leurs notes migrees vers Qwen -- le
# 29/09/2026, on avait migre Kokoro seulement (`_heriter_annotations_kokoro_...`).
# Elles ne font pas partie du memo du 30/09, donc on n'y touche pas ici :
#   - `5830_4703_000037-0001` (Perrine) : rien ne diverge, report possible ;
#   - `7591_6742_000149-0002` (Suzanne) : les etoiles DIVERGENT -- 2 sur la fiche
#     XTTS, 3 au catalogue Qwen. Un report automatique contredirait le catalogue :
#     c'est une decision de Laurent, pas un heritage.
# Pour les migrer un jour : retirer ces deux identifiants de cette liste.
HORS_LOT_30_09 = ("5830_4703_000037-0001", "7591_6742_000149-0002")


def note_finale(nouvelle, ancienne):
    """Ses mots du 30/09, plus l'ancienne remarque si elle disait autre chose.

    Comparaison SANS la casse (lecon du 30/09/2026) : pour `cml7614`, l'ancienne
    remarque « enfant » et ses mots « une voix d'ENFANT » disent la meme chose --
    la note ressortait en « ... -- avant : enfant », deux fois la meme idee.
    """
    ancienne = (ancienne or "").strip()
    if ancienne and ancienne.lower() not in nouvelle.lower():
        return "%s -- avant : %s" % (nouvelle, ancienne)
    return nouvelle


def main():
    analyseur = argparse.ArgumentParser(
        description="Recopie les notes d'ecoute XTTS sur leurs jumelles Qwen.")
    analyseur.add_argument("--ecrire", action="store_true",
                           help="ecrit vraiment (copie datee du fichier d'abord)")
    options = analyseur.parse_args()

    if not NOTES.exists():
        print("ERR : %s introuvable" % NOTES)
        return 1
    notes = json.loads(NOTES.read_text(encoding="utf-8"))
    catalogue = {v["id"] for v in QWEN_VOICES}

    a_recopier = {}
    sans_jumelle = []
    hors_lot = []
    for cle in notes:
        if not cle.startswith("xtts:"):
            continue
        identifiant = cle.split(":", 1)[1]
        if identifiant in HORS_LOT_30_09:
            hors_lot.append(cle)      # hors du lot : voir HORS_LOT_30_09
            continue
        jumelle = "qwen:" + identifiant
        if jumelle in notes:
            continue                  # deja notee chez Qwen : on n'ecrase pas
        if jumelle not in catalogue:
            sans_jumelle.append(cle)  # aucun extrait Qwen de ce nom
            continue
        a_recopier[cle] = jumelle

    print("=" * 70)
    print(" NOTES D'ECOUTE : XTTS -> QWEN  (verdict du 30/09/2026 applique)")
    print("=" * 70)
    print("fichier : %s" % NOTES.name)
    print("notes XTTS lues : %d" % sum(1 for c in notes if c.startswith("xtts:")))
    print("a recopier vers qwen : %d" % len(a_recopier))
    if hors_lot:
        print("hors du lot du 30/09, laissees telles quelles : %d"
              % len(hors_lot))
        for cle in sorted(hors_lot):
            print("    %s" % cle)
    if sans_jumelle:
        print("sans jumelle Qwen, laissees telles quelles : %d"
              % len(sans_jumelle))
        for cle in sorted(sans_jumelle)[:10]:
            print("    %s" % cle)

    ecarts = 0
    print("")
    print("DETAIL (etoile heritee -> etoile du 30/09)")
    for cle in sorted(a_recopier):
        identifiant = cle.split(":", 1)[1]
        heritee = notes[cle].get("stars", 0)
        verdict = VERDICT_30_09.get(identifiant)
        if not verdict:
            print("  %-9s %s etoile(s)   (pas re-jugee : fiche heritee)"
                  % (identifiant, heritee))
            continue
        if heritee != verdict["stars"]:
            ecarts += 1
            marque = "CHANGE"
        else:
            marque = "  =   "
        print("  %-9s %s -> %s   %s   %s"
              % (identifiant, heritee, verdict["stars"], marque,
                 verdict["note"]))
    print("")
    print("voix dont les etoiles changent : %d sur %d" % (ecarts, len(a_recopier)))
    print("voix couvertes par le verdict du 30/09 : %d"
          % sum(1 for cle in a_recopier
                if cle.split(":", 1)[1] in VERDICT_30_09))

    if not options.ecrire:
        print("")
        print("(rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        return 0

    horodatage = datetime.now().strftime("%Y%m%d_%H%M")
    sauvegarde = NOTES.with_name("%s.bak_avant_heritage_cml_%s"
                                 % (NOTES.name, horodatage))
    shutil.copy2(str(NOTES), str(sauvegarde))

    for cle, jumelle in a_recopier.items():
        fiche = dict(notes[cle])
        verdict = VERDICT_30_09.get(cle.split(":", 1)[1])
        if verdict:
            fiche["note"] = note_finale(verdict["note"], fiche.get("note"))
            fiche["stars"] = verdict["stars"]
            if verdict.get("accent"):
                fiche["accent"] = verdict["accent"]
        notes[jumelle] = fiche

    NOTES.write_text(json.dumps(notes, ensure_ascii=False, indent=2,
                                sort_keys=True), encoding="utf-8")
    print("")
    print("copie des notes : %s" % sauvegarde.name)
    print("notes recopiees vers les voix Qwen : %d" % len(a_recopier))
    print("RETOUR ARRIERE : recopier %s sur le fichier." % sauvegarde.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
