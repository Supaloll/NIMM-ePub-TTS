# -*- coding: utf-8 -*-
"""Lot d'ecoute pour les extraits de voix du domaine public (voix « dp_* »).

But : juger le CLONAGE sans rien installer dans le lecteur. Pour chaque voix,
DEUX fichiers, ecoutes dans cet ordre :

    01a_<voix>_reference.wav  -> l'extrait de reference lui-meme (ce que le
                                 moteur a entendu) ;
    01b_<voix>_clone.wav      -> la meme voix, clonee sur un court passage.

Ecouter les deux a la suite dit tout de suite si le clonage est FIDELE
(timbre, debit, accent) ou s'il invente autre chose. Le lot ne touche NI au
catalogue des voix ni aux menus du lecteur : il ne fait que demander au moteur
XTTS allume de parler avec ces voix.

Sortie : xtts_service/sortie_ecoute_dp/ (fichiers WAV + index_ecoute.txt +
ECOUTER_LE_LOT.cmd, a double-cliquer pour tout ecouter d'affilee).

Le moteur doit etre allume (DEMARRER_XTTS.bat) et connaitre les voix : elles
sont versees par `_preparer_extraits.py --verser`.

Usage :
    python _ecouter_extraits_dp.py                    (toutes les voix dp_*)
    python _ecouter_extraits_dp.py --prefixe dp_
    python _ecouter_extraits_dp.py --voix dp_femme001 dp_homme002
"""

import argparse
import io
import json
import sys
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
DOSSIER_VOIX = ICI / "voix_fr"
SORTIE = ICI / "sortie_ecoute_dp"
MOTEUR = "http://127.0.0.1:8083"

# Passage de test : une narration puis une replique (ce qui attend la voix dans
# un livre). C'est une phrase d'atelier, libre de droits.
TEXTE = ("Le comte se retourna lentement vers la porte. Un sourire imperceptible "
         "passa sur ses lèvres. — Vous êtes bien sûr de vous, monsieur, "
         "dit-il d'une voix calme.")

CMD = """@echo off
chcp 65001 >nul
title NIMM ePub - ecoute des voix du domaine public (XTTS)
cd /d "%~dp0"

rem ============================================================
rem  Joue le lot d'ecoute, l'un apres l'autre : pour chaque voix,
rem  d'abord l'EXTRAIT DE REFERENCE puis le CLONE. Aucune
rem  application ne s'ouvre : la lecture se fait dans la fenetre.
rem ============================================================

for %%f in ("sortie_ecoute_dp\\*.wav") do (
  echo.
  echo   Lecture : %%~nxf
  powershell -NoProfile -Command "(New-Object Media.SoundPlayer '%~dp0sortie_ecoute_dp\\%%~nxf').PlaySync()"
)

echo.
echo  Ecoute terminee.
echo.
pause
"""


def _get_json(chemin, delai=10.0):
    with urllib.request.urlopen(MOTEUR + chemin, timeout=delai) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def moteur_pret():
    """(pret, message) -- ne leve jamais."""
    try:
        infos = _get_json("/sante", delai=5.0)
    except Exception as erreur:
        return False, "moteur injoignable sur %s (%s)" % (MOTEUR, erreur)
    if not infos.get("pret"):
        return False, "moteur present mais pas encore pret"
    return True, "%s -- %s voix" % (infos.get("appareil", "?"), infos.get("voix", "?"))


def generer(voix, texte, delai=240.0):
    """Demande une phrase au moteur. Renvoie les octets WAV."""
    corps = json.dumps({"texte": texte, "voix": voix}).encode("utf-8")
    demande = urllib.request.Request(
        MOTEUR + "/tts", data=corps,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(demande, timeout=delai) as reponse:
        return reponse.read()


def duree_wav(octets):
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        return fichier.getnframes() / float(fichier.getframerate())


def voix_disponibles(prefixe):
    """Identifiants des voix de la banque qui commencent par le prefixe."""
    if not DOSSIER_VOIX.is_dir():
        return []
    trouvees = []
    for fichier in sorted(DOSSIER_VOIX.glob("*.wav")):
        nom = fichier.stem
        if nom.endswith("_enhanced"):
            nom = nom[:-len("_enhanced")]
        if nom.startswith(prefixe):
            trouvees.append(nom)
    return trouvees



def main():
    parseur = argparse.ArgumentParser(
        description="Fabrique un lot d'ecoute (reference + clone) pour les "
                    "voix XTTS issues d'extraits libres de droits.")
    parseur.add_argument("--prefixe", default="dp_",
                         help="prefixe des voix a ecouter (defaut : dp_)")
    parseur.add_argument("--voix", nargs="*", default=None,
                         help="identifiants precis a ecouter (defaut : toutes)")
    options = parseur.parse_args()

    pret, message = moteur_pret()
    print("Moteur : %s" % message)
    if not pret:
        print("Allume le moteur (DEMARRER_XTTS.bat), puis relance cet outil.")
        return 1

    voix = options.voix or voix_disponibles(options.prefixe)
    if not voix:
        print("Aucune voix trouvee dans %s (prefixe « %s »)."
              % (DOSSIER_VOIX, options.prefixe))
        print("Verse d'abord les extraits : python _preparer_extraits.py --verser")
        return 1

    SORTIE.mkdir(parents=True, exist_ok=True)
    print("Voix a ecouter : %d" % len(voix))
    print("Sortie         : %s" % SORTIE)
    print("")
    print("%-16s %10s %10s" % ("voix", "reference", "clone"))

    lignes = []
    souci = 0
    for rang, ident in enumerate(voix, 1):
        reference_src = DOSSIER_VOIX / (ident + "_enhanced.wav")
        if not reference_src.is_file():
            reference_src = DOSSIER_VOIX / (ident + ".wav")
        if not reference_src.is_file():
            print("%-16s  introuvable dans la banque" % ident)
            souci += 1
            continue

        octets_reference = reference_src.read_bytes()
        duree_reference = duree_wav(octets_reference)
        cible_reference = SORTIE / ("%02da_%s_reference.wav" % (rang, ident))
        cible_reference.write_bytes(octets_reference)

        try:
            octets_clone = generer(ident, TEXTE)
        except Exception as erreur:
            print("%-16s  ECHEC du clonage : %s" % (ident, erreur))
            souci += 1
            continue
        duree_clone = duree_wav(octets_clone)
        cible_clone = SORTIE / ("%02db_%s_clone.wav" % (rang, ident))
        cible_clone.write_bytes(octets_clone)

        print("%-16s %8.2f s %8.2f s" % (ident, duree_reference, duree_clone))
        lignes.append({
            "rang": rang, "id": ident,
            "reference": cible_reference.name, "duree_reference": duree_reference,
            "clone": cible_clone.name, "duree_clone": duree_clone,
        })

    # Index lisible : ce qu'on ecoute, dans quel ordre, et le texte lu.
    index = SORTIE / "index_ecoute.txt"
    with open(index, "w", encoding="utf-8") as fichier:
        fichier.write("LOT D'ECOUTE -- voix XTTS issues d'extraits libres de droits\n")
        fichier.write("=" * 66 + "\n\n")
        fichier.write("Pour chaque voix, DEUX fichiers dans cet ordre :\n")
        fichier.write("   ...a_<voix>_reference.wav  : l'extrait de reference\n")
        fichier.write("   ...b_<voix>_clone.wav      : le meme texte lu par le clone\n\n")
        fichier.write("Texte lu par le clone :\n%s\n\n" % TEXTE)
        for ligne in lignes:
            fichier.write("%d) %s\n" % (ligne["rang"], ligne["id"]))
            fichier.write("   reference : %s (%.2f s)\n"
                          % (ligne["reference"], ligne["duree_reference"]))
            fichier.write("   clone     : %s (%.2f s)\n"
                          % (ligne["clone"], ligne["duree_clone"]))
            fichier.write("   a noter   : timbre fidele ? debit ? accent ? "
                          "defaut d'attaque en debut de phrase ?\n\n")

    (SORTIE.parent / "ECOUTER_LE_LOT.cmd").write_text(CMD, encoding="utf-8")

    print("")
    print("%d voix preparee(s), %d fichier(s) WAV dans %s"
          % (len(lignes), len(lignes) * 2, SORTIE.name))
    print("Index  : %s" % index.name)
    print("Ecoute : double-clique sur ECOUTER_LE_LOT.cmd (racine de xtts_service)")
    if souci:
        print("%d voix en echec (voir ci-dessus)." % souci)
    return 0


if __name__ == "__main__":
    sys.exit(main())
