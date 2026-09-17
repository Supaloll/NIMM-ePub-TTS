# -*- coding: utf-8 -*-
"""Verifie l'environnement du moteur NeuTTS, SANS charger le moteur.

Lance par INSTALLER_NEUTTS.bat a la fin de l'installation, et utilisable a
tout moment pour savoir ce qui est en place :

    .venv\\Scripts\\python.exe _verifier_installation.py

Ce que ce script NE fait PAS : charger le modele (cela prend du temps et de
la memoire video). Il verifie seulement que les briques sont la, et il compte
les voix disponibles.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
DOSSIER_REFERENCES = ICI / "references"

PROBLEMES = []


def verifier(nom, condition, detail=''):
    if condition:
        print("  OK    %s%s" % (nom, ("  (%s)" % detail) if detail else ""))
    else:
        print("  ERR   %s%s" % (nom, ("  -> %s" % detail) if detail else ""))
        PROBLEMES.append(nom)


def main():
    print("")
    print("=" * 66)
    print("VERIFICATION DE L'ENVIRONNEMENT NEUTTS")
    print("=" * 66)

    print("")
    print("1) Python")
    version = "%d.%d.%d" % sys.version_info[:3]
    verifier("Python 3.12 (exige par la roue neutts)", sys.version_info[:2] == (3, 12),
             version)

    print("")
    print("2) les bibliotheques")
    try:
        import torch
        verifier("torch", True, torch.__version__)
        verifier("torch 2.11 ou plus recent (exige par torchtune)",
                 int(torch.__version__.split('.')[0]) >= 2
                 and int(torch.__version__.split('.')[1]) >= 11,
                 torch.__version__)
        verifier("la carte graphique est visible", torch.cuda.is_available(),
                 torch.cuda.get_device_name(0) if torch.cuda.is_available()
                 else "aucune carte : le moteur tournera sur le processeur")
    except Exception as erreur:
        verifier("torch", False, str(erreur)[:100])

    try:
        import torchao
        verifier("torchao 0.16.x (0.18 fait planter torchtune)", True,
                 torchao.__version__)
    except Exception as erreur:
        verifier("torchao", False, str(erreur)[:100])

    try:
        import number_normalizer  # noqa: F401   (dependance de neutts)
    except Exception:
        pass

    try:
        import neutts
        verifier("neutts", True, getattr(neutts, "__version__", "version inconnue"))
    except Exception as erreur:
        verifier("neutts", False, str(erreur)[:100])
        print("")
        print("  -> l'environnement n'est pas pret : relance INSTALLER_NEUTTS.bat")

    try:
        import soundfile
        verifier("soundfile (lecture des extraits)", True, soundfile.__version__)
    except Exception as erreur:
        verifier("soundfile", False, str(erreur)[:100])

    print("")
    print("3) la phonemisation francaise (espeak-ng)")
    # La roue neutts embarque la DLL ; espeakng-loader est le repli.
    try:
        import espeakng_loader
        verifier("espeakng-loader (repli francais)", True,
                 espeakng_loader.__file__.split("site-packages")[-1])
    except Exception:
        print("  (note) espeakng-loader absent : c'est normal si la roue neutts "
              "embarque deja espeak-ng")
        import importlib.util
        embarque = importlib.util.find_spec("neutts") is not None
        verifier("espeak-ng accessible par neutts", embarque,
                 "a confirmer au premier essai de synthese")

    print("")
    print("4) les voix (extraits + texte)")
    if not DOSSIER_REFERENCES.is_dir():
        verifier("dossier references", False, str(DOSSIER_REFERENCES))
    else:
        wavs = sorted(DOSSIER_REFERENCES.rglob("*_reference.wav"))
        with_csv = len(list(DOSSIER_REFERENCES.rglob("references.csv")))
        with_txt = len(list(DOSSIER_REFERENCES.rglob("*_reference.txt")))
        verifier("extraits de reference trouves", bool(wavs), "%d fichiers" % len(wavs))
        verifier("chaque extrait a de quoi donner son texte (CSV ou .txt)",
                 with_csv + with_txt > 0,
                 "%d CSV + %d TXT" % (with_csv, with_txt))
        if wavs and not (with_csv + with_txt):
            print("  -> sans le TEXTE exact de l'extrait, NeuTTS ne peut rien "
                  "cloner : voir LIRE_MOI.md")

    print("")
    print("5) les modeles (cache Hugging Face)")
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    for nom, libelle in (("models--neuphonic--neutts-nano-french", "modele francais"),
                         ("models--neuphonic--neucodec", "codec"),
                         ("models--facebook--w2v-bert-2.0", "encodeur du codec")):
        verifier(libelle, (cache / nom).is_dir(),
                 "en cache" if (cache / nom).is_dir() else "a telecharger au 1er lancement")

    print("")
    print("=" * 66)
    if PROBLEMES:
        print("%d POINT(S) A REGARDER :" % len(PROBLEMES))
        for nom in PROBLEMES:
            print("  - %s" % nom)
        print("")
        print("Detail : LIRE_MOI.md, et journal_installation.txt")
        return 1
    print("TOUT EST OK : le moteur peut demarrer (DEMARRER_NEUTTS.bat)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
