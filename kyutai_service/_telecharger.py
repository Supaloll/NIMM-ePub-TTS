# -*- coding: utf-8 -*-
"""
Preparation des elements du moteur Kyutai TTS 1.6B pour NIMM ePub.

Ce script ne s'occupe QUE des fichiers a recuperer une fois pour toutes :

  1. les 35 VOIX FRANCAISES libres (banque « kyutai/tts-voices »,
     dossier cml-tts/fr : 8,5 Mo d'empreintes + les references audio) ;
  2. le MODELE lui-meme (« kyutai/tts-1.6b-en_fr ») :
       - config.json + tokeniseurs (~367 Mo) dans le cache Hugging Face ;
       - le gros fichier de 3,4 Go, telecharge avec reprise automatique
         (c'est la methode qui a debloque le telechargement le 12/09/2026).

Si un fichier est deja present et complet, il est simplement ignore :
on peut relancer le script autant de fois que necessaire.

Usage : .venv\\Scripts\\python.exe _telecharger.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

ICI = Path(__file__).resolve().parent
DOSSIER_VOIX = ICI / "voix_fr"
DOSSIER_MODELE = ICI / "modele"

REPO_VOIX = "kyutai/tts-voices"
REPO_MODELE = "kyutai/tts-1.6b-en_fr"

# Fichiers du modele hors gros poids (tokeniseur de texte + codec audio Mimi).
FICHIERS_MODELE = [
    "config.json",
    "tokenizer_spm_8k_en_fr_audio.model",
    "tokenizer-e351c8d8-checkpoint125.safetensors",
]

NOM_GROS_FICHIER = "dsm_tts_1e68beda@240.safetensors"
# Taille exacte du gros fichier chez Kyutai (3,43 Go) : sert a verifier
# qu'un telechargement interrompu ne passe pas pour un fichier complet.
TAILLE_ATTENDUE = 3683719712
URL_GROS_FICHIER = ("https://huggingface.co/%s/resolve/main/%s"
                    % (REPO_MODELE, NOM_GROS_FICHIER))


def trouver_gros_fichier():
    """Meme recherche que le service : variable, dossier local, cache."""
    force = os.environ.get("NIMM_KYUTAI_POIDS", "").strip()
    candidats = []
    if force:
        candidats.append(Path(force))
    candidats.append(DOSSIER_MODELE / NOM_GROS_FICHIER)
    candidats.append(Path(os.path.expanduser("~")) / ".cache" / "kyutai_modele"
                          / NOM_GROS_FICHIER)
    for chemin in candidats:
        if chemin.is_file() and chemin.stat().st_size == TAILLE_ATTENDUE:
            return chemin
    return None


def telecharger_voix():
    """Recupere les 35 voix francaises libres (empreinte + reference)."""
    from huggingface_hub import HfApi, hf_hub_download

    api = HfApi()
    tous = api.list_repo_files(REPO_VOIX, repo_type="model")
    references = sorted(f for f in tous
                        if f.startswith("cml-tts/fr/") and f.endswith("_enhanced.wav"))
    print("voix francaises trouvees : %d" % len(references))

    DOSSIER_VOIX.mkdir(parents=True, exist_ok=True)
    faites = 0
    for rang, reference in enumerate(references, 1):
        empreinte = reference + ".1e68beda@240.safetensors"
        local = DOSSIER_VOIX / empreinte
        if local.is_file() and local.stat().st_size > 0:
            faites += 1
            continue
        for fichier in (reference, empreinte):
            hf_hub_download(REPO_VOIX, fichier, repo_type="model",
                            local_dir=str(DOSSIER_VOIX))
        faites += 1
        print("  %02d/%02d  %s" % (rang, len(references),
                                   Path(reference).name))
    print("voix pretes : %d (dossier %s)" % (faites, DOSSIER_VOIX))


def telecharger_petits_morceaux():
    """config.json + tokeniseurs (environ 367 Mo), dans le cache HF."""
    from huggingface_hub import hf_hub_download

    for nom in FICHIERS_MODELE:
        chemin = Path(hf_hub_download(REPO_MODELE, nom))
        print("  OK  %-45s %6.1f Mo" % (nom, chemin.stat().st_size / 1048576))


def telecharger_gros_fichier():
    """Le gros fichier de 3,4 Go, avec reprise automatique (curl)."""
    deja = trouver_gros_fichier()
    if deja is not None:
        print("  OK  gros fichier deja present : %s" % deja)
        return deja

    DOSSIER_MODELE.mkdir(parents=True, exist_ok=True)
    cible = DOSSIER_MODELE / NOM_GROS_FICHIER

    if shutil.which("curl"):
        commande = ["curl.exe", "-L", "--retry", "20", "--retry-all-errors",
                    "--retry-delay", "3", "-C", "-", "-o", str(cible),
                    URL_GROS_FICHIER]
        print("  telechargement en cours (reprise automatique) ...")
        resultat = subprocess.run(commande)
        if resultat.returncode != 0:
            print("  ECHEC de curl (code %d). Relance le script : il reprendra "
                  "ou il s'est arrete." % resultat.returncode)
            sys.exit(1)
    else:
        # Repli : telechargement classique par Hugging Face.
        from huggingface_hub import hf_hub_download
        hf_hub_download(REPO_MODELE, NOM_GROS_FICHIER, local_dir=str(DOSSIER_MODELE))

    if cible.stat().st_size != TAILLE_ATTENDUE:
        print("  ATTENTION : taille inattendue (%.2f Go au lieu de 3,43 Go). "
              "Relance le script pour terminer le telechargement."
              % (cible.stat().st_size / 1073741824))
        sys.exit(1)
    print("  OK  gros fichier complet (3,43 Go)")
    return cible


def main():
    print("")
    print("===== Preparation du moteur Kyutai TTS 1.6B =====")
    print("")
    print("1) voix francaises libres (CC BY 4.0)")
    telecharger_voix()
    print("")
    print("2) tokeniseurs et configuration du modele")
    telecharger_petits_morceaux()
    print("")
    print("3) modele Kyutai (3,43 Go, une seule fois)")
    chemin = telecharger_gros_fichier()
    print("")
    print("TOUT EST PRET.")
    print("Modele : %s" % chemin)
    print("Voix   : %s" % (DOSSIER_VOIX / 'cml-tts' / 'fr'))
    print("Etape suivante : double-clique sur DEMARRER_KYUTAI.bat")
    print("")


if __name__ == "__main__":
    main()
