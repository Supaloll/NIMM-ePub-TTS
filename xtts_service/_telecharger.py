# -*- coding: utf-8 -*-
"""
Preparation des elements du moteur XTTS v2 pour NIMM ePub.

Ce script ne s'occupe QUE des fichiers a recuperer une fois pour toutes :

  1. les 35 VOIX FRANCAISES de reference : des extraits de 9 a 10 secondes,
     issus de CML-TTS (CC BY 4.0). XTTS v2 sait cloner une voix a partir de
     6 secondes seulement -- ils servent donc TELLS QUELS, sans preparation.
     Ils sont DEJA sur cette machine, puisque le moteur Kyutai s'en sert
     aussi : on les COPIE depuis kyutai_service\\voix_fr\\cml-tts\\fr\\ pour
     que ce moteur-ci soit autonome (il reste utilisable meme si le moteur
     Kyutai etait desinstalle un jour). Si le dossier Kyutai n'existe plus,
     elles sont retelechargees depuis Hugging Face (meme banque, CC BY 4.0).
  2. le MODELE XTTS v2 (2,09 Go) : coqui-tts le telecharge lui-meme au
     premier chargement. On le declenche ici une bonne fois, pour ne pas
     decouvrir l'attente au milieu d'une lecture.

Si un fichier est deja present, il est ignore : le script peut etre relance
autant de fois que necessaire.

Usage : .venv\\Scripts\\python.exe _telecharger.py
"""

import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
# Licence CPML du modele : usage prive (voir ATTRIBUTION.md). Cet accord
# evite que coqui-tts pose la question au premier telechargement.
os.environ.setdefault('COQUI_TOS_AGREED', '1')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

ICI = Path(__file__).resolve().parent
DOSSIER_VOIX = ICI / "voix_fr"
# Les 35 extraits deja utilises par le moteur Kyutai (meme projet).
DOSSIER_KYUTAI = ICI.parent / "kyutai_service" / "voix_fr" / "cml-tts" / "fr"

REPO_VOIX = "kyutai/tts-voices"
DOSSIER_BANQUE = "cml-tts/fr"
MODULE_MODELE = "tts_models/multilingual/multi-dataset/xtts_v2"


def copier_les_voix_de_kyutai():
    """Copie les extraits de reference depuis le moteur Kyutai.

    Rien a telecharger : les 35 voix sont deja la, et ce sont exactement
    celles qu'il faut (memes identifiants que le catalogue Kyutai, ce qui
    permet a Laurent de retrouver ses reperes).
    """
    if not DOSSIER_KYUTAI.is_dir():
        return 0
    DOSSIER_VOIX.mkdir(parents=True, exist_ok=True)
    faites = 0
    for source in sorted(DOSSIER_KYUTAI.glob("*_enhanced.wav")):
        cible = DOSSIER_VOIX / source.name
        if cible.is_file() and cible.stat().st_size == source.stat().st_size:
            faites += 1
            continue
        shutil.copy2(source, cible)
        faites += 1
        print("  %s" % source.name)
    return faites


def telecharger_les_voix_de_la_banque():
    """Repli : retelecharge les extraits depuis Hugging Face (CC BY 4.0)."""
    from huggingface_hub import HfApi, hf_hub_download

    api = HfApi()
    tous = api.list_repo_files(REPO_VOIX, repo_type="model")
    references = sorted(f for f in tous
                        if f.startswith(DOSSIER_BANQUE + "/")
                        and f.endswith("_enhanced.wav"))
    print("  voix trouvees dans la banque : %d" % len(references))

    DOSSIER_VOIX.mkdir(parents=True, exist_ok=True)
    faites = 0
    for rang, reference in enumerate(references, 1):
        nom = Path(reference).name
        # Deja copiee depuis le moteur Kyutai ? Alors rien a faire.
        if (DOSSIER_VOIX / nom).is_file():
            faites += 1
            continue
        hf_hub_download(REPO_VOIX, reference, repo_type="model",
                        local_dir=str(DOSSIER_VOIX))
        faites += 1
        print("  %02d/%02d  %s" % (rang, len(references), nom))
    return faites


def telecharger_le_modele():
    """Fait telecharger le modele XTTS v2 par coqui-tts (2,09 Go).

    L'appel charge le modele : s'il est deja en cache, c'est l'affaire de
    quelques secondes et rien n'est telecharge a nouveau.
    """
    import torch
    from TTS.api import TTS

    print("  chargement du modele par coqui-tts...")
    if torch.cuda.is_available():
        print("  carte graphique : %s" % torch.cuda.get_device_name(0))
        modele = TTS(MODULE_MODELE)
        try:
            modele = modele.to("cuda")
        except (AttributeError, TypeError):
            pass
    else:
        print("  aucune carte graphique detectee : le modele tournera sur le "
              "processeur, beaucoup plus lentement")
        TTS(MODULE_MODELE)
    return True


def main():
    print("")
    print("===== Preparation du moteur XTTS v2 =====")
    print("")
    print("1) voix francaises de reference (extraits CML-TTS, CC BY 4.0)")

    faites = copier_les_voix_de_kyutai()
    if faites:
        print("  %d voix copiees depuis le moteur Kyutai (rien a "
              "telecharger)." % faites)
    else:
        print("  dossier du moteur Kyutai introuvable : telechargement "
              "depuis la banque Hugging Face...")
        faites = telecharger_les_voix_de_la_banque()

    if not faites:
        print("  ECHEC : aucune voix recuperee.")
        print("  Verifie la connexion, puis relance ce script.")
        sys.exit(1)

    print("")
    print("2) modele XTTS v2 (2,09 Go, une seule fois)")
    telecharger_le_modele()

    print("")
    print("TOUT EST PRET.")
    print("Voix   : %s" % DOSSIER_VOIX)
    print("Etape suivante : double-clique sur DEMARRER_XTTS.bat")
    print("")


if __name__ == "__main__":
    main()
