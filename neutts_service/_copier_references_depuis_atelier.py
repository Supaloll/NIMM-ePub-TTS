# -*- coding: utf-8 -*-
"""Copie les extraits de reference de l'atelier NIMM Voix vers ce service.

A QUOI CA SERT : NeuTTS clone une voix a partir d'un extrait de 3 a 15 s ET du
texte exact qui y est dit. L'atelier NIMM Voix a prepare et transcrit ces
extraits le 16/09/2026 (Whisper large-v3), et ecrit un `references.csv` par
dossier. Ce script les recopie ici, tels quels -- il ne fabrique rien, il ne
transcode rien, il ne supprime rien.

Usage (depuis neutts_service, avec le python du lecteur suffit -- aucun modele
n'est charge) :

    python _copier_references_depuis_atelier.py
    python _copier_references_depuis_atelier.py --depuis "G:\\NIMM Voix\\outils\\neutts_tts\\references"
    python _copier_references_depuis_atelier.py --rapport-seulement

Les dossiers recopies : cml_tts (60 voix CML-TTS), voix_libres_dp (19 voix du
domaine public). Les extraits de Kokoro, eux, viennent du catalogue de
l'atelier (voir LIRE_MOI.md, section « les 30 voix Kokoro »).
"""
import argparse
import csv
import shutil
import sys
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
DESTINATION = ICI / "references"
SOURCE_DEFAUT = Path(r"G:\NIMM Voix\outils\neutts_tts\references")
# Le catalogue de l'atelier : un dossier par voix Kokoro, avec son extrait de
# controle (`echantillon_controle.wav`) -- c'est l'extrait qui a servi a faire
# parler NeuTTS avec les 30 voix Kokoro, celles que Laurent a validees.
CATALOGUE_ATELIER = Path(r"G:\NIMM Voix\catalogue")
# Le texte EXACT de cet extrait (la phrase 1 de l'atelier). C'est la paire
# (extrait + texte) telle qu'elle a produit les 30 voix validees a l'oreille le
# 16/09/2026 : on ne la modifie pas, sinon on changerait le resultat.
TEXTE_CONTROLE = (
    "Le soleil se couchait derrière les collines et la vieille cloche de "
    "l'église sonnait doucement dans le soir paisible. Il marchait d'un pas "
    "lent le long de la rivière, songeant aux lettres qu'il n'avait jamais osé "
    "envoyer.")


def copier_kokoro():
    """Copie les extraits de controle des voix Kokoro de l'atelier.

    Pourquoi a part : ces voix ne sont pas dans `outils\\neutts_tts\\references`.
    Leur extrait de reference est l'echantillon de controle du catalogue
    (`catalogue\\<voix>\\echantillon_controle.wav`) et leur texte est la phrase 1
    de l'atelier. C'est cette paire (extrait + texte) qui a produit les 30 voix
    Kokoro validees a l'oreille le 16/09/2026.

    Renvoie le nombre d'extraits copies.
    """
    dossier = DESTINATION / "kokoro"
    dossier.mkdir(parents=True, exist_ok=True)
    lignes = []
    for voix in sorted(CATALOGUE_ATELIER.iterdir()):
        wav = voix / "echantillon_controle.wav"
        if not wav.is_file():
            continue
        nom = voix.name
        shutil.copy2(str(wav), str(dossier / ("%s_reference.wav" % nom)))
        try:
            with wave.open(str(wav), "rb") as fichier:
                duree = fichier.getnframes() / float(fichier.getframerate() or 24000)
        except Exception:
            duree = 0.0
        lignes.append([nom + "_reference.wav", TEXTE_CONTROLE,
                       "%.2f" % duree, "", "echantillon_controle.wav"])
    with open(dossier / "references.csv", "w", encoding="utf-8",
              newline="") as fichier:
        ecrivain = csv.writer(fichier, delimiter=";")
        ecrivain.writerow(["fichier", "texte", "duree", "hauteur", "source"])
        ecrivain.writerows(lignes)
    return len(lignes)


def compter(dossier):
    """(extraits, textes) d'un dossier : ce qui est vraiment utilisable."""
    if not dossier.is_dir():
        return (0, 0)
    wavs = list(dossier.glob("*_reference.wav"))
    textes = 0
    csv = dossier / "references.csv"
    if csv.exists():
        import csv as _csv
        try:
            with open(csv, "r", encoding="utf-8", newline="") as fichier:
                for ligne in _csv.DictReader(fichier, delimiter=";"):
                    if (ligne.get("fichier") or "").strip() and (ligne.get("texte") or "").strip():
                        textes += 1
        except Exception:
            pass
    textes += len(list(dossier.glob("*_reference.txt")))
    return (len(wavs), textes)


def main():
    analyseur = argparse.ArgumentParser(
        description="Copie les extraits de reference de NIMM Voix vers le service.")
    analyseur.add_argument("--depuis", default=str(SOURCE_DEFAUT),
                           help="dossier des references de l'atelier")
    analyseur.add_argument("--rapport-seulement", action="store_true",
                           help="ne copie rien : dit seulement ce qui serait copie")
    analyseur.add_argument("--kokoro", action="store_true",
                           help="copie EN PLUS les extraits de controle des voix "
                                "Kokoro (ils viennent du catalogue de l'atelier, "
                                "pas du dossier references)")
    options = analyseur.parse_args()

    source = Path(options.depuis)
    print("")
    print("=" * 66)
    print("REFERENCES NeuTTS -- de l'atelier vers NIMM ePub")
    print("=" * 66)
    print("source      : %s" % source)
    print("destination : %s" % DESTINATION)
    print("")

    if not source.is_dir():
        print("ERR : dossier source introuvable. Verifie le chemin (--depuis).")
        return 1

    dossiers = sorted(p for p in source.iterdir() if p.is_dir())
    if not dossiers:
        print("ERR : aucun sous-dossier dans la source.")
        return 1

    total_wav = total_txt = 0
    for dossier in dossiers:
        wavs, textes = compter(dossier)
        total_wav += wavs
        total_txt += textes
        etat = "OK" if (wavs and textes) else "INCOMPLET"
        print("  %-10s %-24s %3d extraits, %3d textes  %s"
              % (etat, dossier.name, wavs, textes,
                 "" if (wavs and textes) else "<- texte manquant : voix inutilisables"))
        if options.rapport_seulement:
            continue
        cible = DESTINATION / dossier.name
        cible.mkdir(parents=True, exist_ok=True)
        copies = 0
        for fichier in sorted(dossier.iterdir()):
            if fichier.is_file() and (fichier.suffix in (".wav", ".csv", ".txt")
                                      or fichier.name.lower().startswith("lisez")):
                shutil.copy2(str(fichier), str(cible / fichier.name))
                copies += 1
        print("     -> %d fichier(s) copie(s) dans references\\%s"
              % (copies, dossier.name))

    if options.kokoro:
        if not CATALOGUE_ATELIER.is_dir():
            print("")
            print("ERR : catalogue de l'atelier introuvable (%s)" % CATALOGUE_ATELIER)
            return 1
        a_copier = [p for p in CATALOGUE_ATELIER.iterdir()
                    if (p / "echantillon_controle.wav").is_file()]
        if options.rapport_seulement:
            print("")
            print("kokoro         %3d extraits de controle (catalogue de l'atelier)"
                  % len(a_copier))
        else:
            nombre = copier_kokoro()
            print("")
            print("kokoro         %3d extraits de controle copies dans "
                  "references\\kokoro" % nombre)

    print("")
    print("total : %d extraits, %d textes" % (total_wav, total_txt))
    if options.rapport_seulement:
        print("(rapport seulement : rien n'a ete copie)")
    else:
        print("Verifie ensuite avec : .venv\\Scripts\\python.exe _verifier_installation.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
