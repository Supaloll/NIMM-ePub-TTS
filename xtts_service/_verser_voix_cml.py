# -*- coding: utf-8 -*-
"""
Verse dans la banque XTTS les voix CML-TTS retenues a l'ecoute.

Laurent a ecoute les 32 extraits de `sortie_ecoute_cml/` et a note chaque voix
dans son `index_ecoute.txt` (genre, etoiles, remarque). Ce script fait la
conversion :

  1. lit son index et ne garde que les voix a **1 etoile ou plus** (les 0 sont
     ecartees, c'est son verdict) ;
  2. verifie qu'aucun PRENOM ne fait doublon avec le catalogue existant
     (Edge, Kokoro, Piper, Kyutai) -- indispensable, les menus affichent les
     voix par prenom ;
  3. copie chaque extrait dans `xtts_service/voix_fr/` sous le nom
     `<identifiant>_enhanced.wav` (convention du dossier, seule la version
     `_enhanced` est retenue par le service) ;
  4. affiche les lignes a ajouter au catalogue `XTTS_VOICES`
     (`modules/tts.py`), pretes a coller.

Aucune conversion audio n'est necessaire : les extraits du jeu CML-TTS sont
DEJA en mono 24 000 Hz 16 bits, exactement le format attendu par XTTS.

Usage :
    .venv\\Scripts\\python.exe _verser_voix_cml.py            (simulation)
    .venv\\Scripts\\python.exe _verser_voix_cml.py --copier   (ecrit vraiment)
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

INDEX = ICI / "sortie_ecoute_cml" / "index_ecoute.txt"
DOSSIER_SOURCE = ICI / "sortie_ecoute_cml"
DOSSIER_VOIX = ICI / "voix_fr"

# Prenoms proposes pour les 25 voix retenues (choisis du XIXe siecle, pour
# rester dans l'ambiance des romans, et VERIFIES sans doublon par le script).
# Le second element est l'accent entendu par Laurent, s'il y en a un : il est
# reporte dans le libelle du menu, pour retrouver ces voix d'un coup d'oeil
# quand un personnage etranger se presente.
PRENOMS = {
    1840:  ("Achille",   None),
    9804:  ("Alphonse",  None),
    3060:  ("Armand",    None),
    10065: ("Auguste",   None),
    7423:  ("Basile",    "accent canadien"),
    12501: ("Charles",   None),
    6249:  ("Célestin",  "accent paysan"),
    5525:  ("Émile",     None),
    7377:  ("Ernest",    None),
    12512: ("Eugène",    None),
    3503:  ("Félix",     None),
    7614:  ("Gustave",   None),
    7239:  ("Hector",    None),
    5526:  ("Hippolyte", None),
    3344:  ("Honoré",    None),
    2771:  ("Lucien",    None),
    3182:  ("Maurice",   None),
    12823: ("Agathe",    None),
    1649:  ("Berthe",    "accent allemand"),
    1869:  ("Cécile",    None),
    6070:  ("Estelle",   None),
    6381:  ("Gabrielle", None),
    6348:  ("Hortense",  "accent espagnol/italien"),
    2316:  ("Joséphine", None),
    2033:  ("Lucie",     "accent anglais"),
}

# index_ecoute.txt : colonnes tapees a la main, donc espacement irregulier.
# On lit : le nom de fichier, la duree, la hauteur, le genre, les etoiles,
# puis tout ce qui reste est la remarque.
LIGNE_VOIX = re.compile(
    r"^\s+(voix\d+_lecteur\d+)\.wav\s+([\d.]+)\s*s\s+(\S+)\s*Hz"
    r"\s+(\S+)\s+(\d)\s*(.*)$")


def lire_index():
    """Renvoie (voix annotees, nombre de lignes lues puis ecartees).

    Une ligne est ecartee quand Laurent n'a pas rempli le genre : ce sont les
    voix qu'il a notees 0 etoile, laissees de cote volontairement.
    """
    if not INDEX.is_file():
        print("Index introuvable : %s" % INDEX)
        sys.exit(1)
    voix, ecartees = [], 0
    for ligne in INDEX.read_text(encoding="utf-8").splitlines():
        m = LIGNE_VOIX.match(ligne)
        if not m:
            continue
        base, duree, _hauteur, genre, etoiles, reste = m.groups()
        lecteur = int(base.split("_lecteur")[1])
        if genre not in ("H", "F"):
            ecartees += 1
            continue
        voix.append({
            "base": base, "lecteur": lecteur, "duree": float(duree),
            "genre": genre, "stars": int(etoiles),
            "remarque": " ".join(reste.split()).strip(".").strip(),
        })
    return voix, ecartees


def prenoms_deja_utilises():
    """Tous les prenoms deja presents dans les catalogues du lecteur."""
    import main
    from modules.tts import (KOKORO_VOICES, PIPER_VOICES,
                             KYUTAI_VOICES, XTTS_VOICES)
    pris = {}
    for famille, catalogue in (("Edge", main.FRENCH_VOICES),
                               ("Kokoro", KOKORO_VOICES),
                               ("Piper", PIPER_VOICES),
                               ("Kyutai", KYUTAI_VOICES),
                               ("XTTS deja en place", XTTS_VOICES)):
        for v in catalogue:
            pris.setdefault(v["name"].strip().lower(), famille)
    return pris


def verifier_prenoms(voix, pris):
    """Prenoms en doublon : les menus affichent les voix par prenom."""
    soucis, vus = [], {}
    for v in voix:
        prenom, _accent = PRENOMS.get(v["lecteur"], (None, None))
        if not prenom:
            soucis.append("lecteur %d : aucun prenom propose" % v["lecteur"])
            continue
        cle = prenom.strip().lower()
        if cle in pris:
            soucis.append("%s (lecteur %d) est deja pris par %s"
                          % (prenom, v["lecteur"], pris[cle]))
        if cle in vus:
            soucis.append("%s en double dans ce lot (lecteurs %d et %d)"
                          % (prenom, vus[cle], v["lecteur"]))
        vus[cle] = v["lecteur"]
    return soucis


def convertir(voix, copier):
    """Copie les extraits retenus dans voix_fr/ (ou simule si copier=False)."""
    DOSSIER_VOIX.mkdir(parents=True, exist_ok=True)
    faites = 0
    for v in voix:
        source = DOSSIER_SOURCE / (v["base"] + ".wav")
        cible = DOSSIER_VOIX / ("cml%d_enhanced.wav" % v["lecteur"])
        if not source.is_file():
            print("   ABSENT : %s" % source.name)
            continue
        if copier:
            shutil.copy2(source, cible)
        faites += 1
        print("   %-24s -> %-26s %s"
              % (source.name, cible.name,
                 "copie" if copier else "(simulation)"))
    return faites


def lignes_catalogue(voix):
    """Les lignes pretes a coller dans XTTS_VOICES (modules/tts.py)."""
    lignes = []
    for v in sorted(voix, key=lambda x: (-x["stars"], x["lecteur"])):
        prenom, accent = PRENOMS.get(v["lecteur"], ("?", None))
        region = "\\U0001F1EB\\U0001F1F7 France (XTTS)"
        if accent:
            region += " - " + accent
        # ATTENTION : le catalogue du lecteur utilise F/M, alors que Laurent
        # note H/F a l'ecoute (convention du CASTING). Sans cette conversion,
        # les nouvelles voix masculines restent invisibles du pool
        # automatique -- erreur commise puis corrigee le 14/09/2026.
        genre_catalogue = "M" if v["genre"] == "H" else v["genre"]
        lignes.append(
            '    {"id": "xtts:cml%d", "name": "%s", "region": "%s", '
            '"gender": "%s", "stars": %d},'
            % (v["lecteur"], prenom, region, genre_catalogue, v["stars"]))
    return lignes


def main():
    analyseur = argparse.ArgumentParser(
        description="Verse les voix CML-TTS retenues dans la banque XTTS.")
    analyseur.add_argument("--copier", action="store_true",
                           help="ecrire vraiment les fichiers (sinon simulation)")
    options = analyseur.parse_args()

    voix, ecartees = lire_index()
    retenues = [v for v in voix if v["stars"] >= 1]
    print("Index de Laurent : %d voix retenues (1 etoile ou plus)."
          % len(retenues))
    print("   laissees de cote (0 etoile, genre non rempli) : %d" % ecartees)
    print("")

    pris = prenoms_deja_utilises()
    print("Prenoms deja pris dans les catalogues : %d" % len(pris))
    soucis = verifier_prenoms(retenues, pris)
    if soucis:
        print("")
        print("ARRET : prenom(s) en conflit -- a corriger dans PRENOMS :")
        for s in soucis:
            print("   - " + s)
        return 1
    print("Aucun conflit de prenom.")
    print("")

    print("Copie vers %s" % DOSSIER_VOIX)
    faites = convertir(retenues, options.copier)
    print("")

    print("=" * 78)
    print("LIGNES A AJOUTER DANS XTTS_VOICES (modules/tts.py)")
    print("=" * 78)
    for ligne in lignes_catalogue(retenues):
        print(ligne)
    print("")
    print("%d voix %s." % (faites, "copiees" if options.copier
                           else "en simulation -- relancer avec --copier"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
