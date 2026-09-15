# -*- coding: utf-8 -*-
"""
Inventaire de la banque de voix Kyutai (lecture seule, aucune installation).

Interroge le depot Hugging Face `kyutai/tts-voices` et affiche, dossier par
dossier, combien de voix il contient, dans quelle(s) langue(s), avec la
licence connue a ce jour. Sert a repondre a la question :

    « y a-t-il encore d'autres voix francaises que les 35 de cml-tts/fr ? »

Aucun fichier n'est telecharge : seul le listing du depot est lu.

Usage : .venv\\Scripts\\python.exe _lister_banque.py
        .venv\\Scripts\\python.exe _lister_banque.py --mot fr
"""

import argparse
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

REPO = "kyutai/tts-voices"

# Licences documentees par l'atelier NIMM Voix (ARCHITECTURE.md, 12/09/2026).
# Tout dossier absent de cette table est signale comme « a verifier » : on
# n'invente jamais une licence.
LICENCES = {
    "cml-tts":      "CC BY 4.0 (jeu de donnees CML-TTS) : attribution obligatoire",
    "vctk":         "CC BY 4.0",
    "alba-mackenna": "CC BY 4.0",
    "expresso":     "CC BY-NC 4.0 : usage prive seulement",
    "ears":         "CC BY-NC 4.0 : usage prive seulement",
    "voice-zero":   "CC0 (domaine public)",
    "donations":    "CC0 (domaine public)",
    "voice-donations": "CC0 (domaine public)",
}


def main():
    analyseur = argparse.ArgumentParser(description="Inventaire de la banque de voix Kyutai.")
    analyseur.add_argument("--repo", default=REPO, help="depot Hugging Face a lister")
    analyseur.add_argument("--mot", default=None,
                           help="ne montrer que les dossiers contenant ce mot (ex: fr, en)")
    options = analyseur.parse_args()

    from huggingface_hub import HfApi

    api = HfApi()
    fichiers = api.list_repo_files(options.repo, repo_type="model")

    # Une « voix » = un fichier _enhanced.wav (+ son empreinte .safetensors).
    par_dossier = Counter()
    for fichier in fichiers:
        if fichier.endswith("_enhanced.wav"):
            dossier = os.path.dirname(fichier)
            par_dossier[dossier] += 1

    print("Banque : %s" % options.repo)
    print("%d voix au total, dans %d dossiers." % (sum(par_dossier.values()),
                                                   len(par_dossier)))
    print("")
    print("%-34s %6s   %s" % ("dossier", "voix", "licence"))
    print("-" * 96)

    for dossier in sorted(par_dossier):
        if options.mot and options.mot.lower() not in dossier.lower():
            continue
        racine = dossier.split("/")[0]
        licence = LICENCES.get(racine, "a verifier")
        print("%-34s %6d   %s" % (dossier, par_dossier[dossier], licence))

    print("")
    print("Repères :")
    print("  cml-tts/fr = les 35 voix francaises libres deja installées (CC BY 4.0).")
    print("  cml-tts/<xx> = le meme jeu de donnees, autres langues.")
    print("  Un dossier de langue (vctk = anglais, expresso = anglais US, etc.)")
    print("  contient des voix d'une AUTRE langue, mais l'empreinte de voix peut")
    print("  etre essayee sur du texte francais (voir _tester_voix_etrangeres.py).")
    print("")
    print("RESUME par famille de premier niveau :")
    print("-" * 60)
    par_racine = Counter()
    for dossier, nombre in par_dossier.items():
        par_racine[dossier.split("/")[0]] += nombre
    for racine in sorted(par_racine):
        print("%-24s %5d voix   %s"
              % (racine, par_racine[racine], LICENCES.get(racine, "a verifier")))
    print("FIN")


if __name__ == "__main__":
    main()
