# -*- coding: utf-8 -*-
"""
Recopie les notes d'ecoute des voix KOKORO sur leurs jumelles QWEN (29/09/2026).

Pourquoi : les 94 voix Kokoro portent le MEME identifiant que 94 des 157 voix
Qwen (`kokoro:af_nicole` et `qwen:af_nicole` : meme extrait, donc meme timbre et
meme prenom). Depuis que Kokoro n'est PLUS PROPOSE dans les menus (doublons,
demande de Laurent), « Ecouter les voix » ne montrerait que les voix Qwen --
SANS les etoiles et les criteres de Laurent, qui sont ranges sous `kokoro:`.

Ce que fait l'outil : pour chaque cle `kokoro:` du fichier de notes, si sa
jumelle `qwen:` n'existe pas et si cette jumelle est bien une voix du catalogue,
il recopie la fiche telle quelle. Il n'ecrase JAMAIS une fiche existante, et les
cles `kokoro:` sont conservees (retour arriere possible a tout moment).

Usage :
    python test_voix/_heriter_annotations_kokoro_vers_qwen.py           # rapport
    python test_voix/_heriter_annotations_kokoro_vers_qwen.py --ecrire
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


def main():
    analyseur = argparse.ArgumentParser(
        description="Recopie les notes d'ecoute Kokoro sur leurs jumelles Qwen.")
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
    for cle in notes:
        if not cle.startswith("kokoro:"):
            continue
        jumelle = "qwen:" + cle.split(":", 1)[1]
        if jumelle in notes:
            continue                  # deja notee chez Qwen : on n'ecrase pas
        if jumelle not in catalogue:
            sans_jumelle.append(cle)  # aucun extrait Qwen de ce nom
            continue
        a_recopier[cle] = jumelle

    print("=" * 68)
    print(" NOTES D'ECOUTE : KOKORO -> QWEN")
    print("=" * 68)
    print("fichier : %s" % NOTES.name)
    print("notes Kokoro lues : %d" % sum(1 for c in notes
                                         if c.startswith("kokoro:")))
    print("a recopier vers qwen : %d" % len(a_recopier))
    if sans_jumelle:
        print("sans jumelle Qwen, laissees telles quelles : %d"
              % len(sans_jumelle))
        for cle in sorted(sans_jumelle)[:10]:
            print("    %s" % cle)

    if not options.ecrire:
        print("")
        print("(rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        return 0

    horodatage = datetime.now().strftime("%Y%m%d_%H%M")
    sauvegarde = NOTES.with_name("%s.bak_avant_heritage_qwen_%s"
                                 % (NOTES.name, horodatage))
    shutil.copy2(str(NOTES), str(sauvegarde))
    for cle, jumelle in a_recopier.items():
        notes[jumelle] = dict(notes[cle])
    NOTES.write_text(json.dumps(notes, ensure_ascii=False, indent=2,
                                sort_keys=True), encoding="utf-8")
    print("")
    print("copie des notes : %s" % sauvegarde.name)
    print("notes recopiees vers les voix Qwen : %d" % len(a_recopier))
    print("RETOUR ARRIERE : recopier %s sur le fichier." % sauvegarde.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
