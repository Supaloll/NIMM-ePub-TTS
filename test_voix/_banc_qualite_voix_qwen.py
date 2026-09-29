# -*- coding: utf-8 -*-
"""
Banc de QUALITE des voix Qwen : lesquelles DERIVENT (gargouillis) ou rendent du
silence ?

Pourquoi (29/09/2026) : Laurent a entendu un GARGOUILLIS en changeant la voix de
Lord_ivrogne (livre 35, `homme_aigu_6877654`). Le journal du moteur montre
163,84 s d'audio pour une replique de 8 jetons : le moteur a atteint son plafond
de frames (2048) sans jamais s'arreter -- il a DERIVE. Cause probable : les
textes de reference des voix clonees, transcrits par Whisper (« le trois males
pharaon » pour « le trois-mats le Pharaon »). En mode ICL, le moteur recoit un
audio qui dit une chose et un texte qui en dit une autre.

Ce que fait cet outil, pour CHAQUE voix du service :
  - lui fait dire une ou deux phrases courtes ;
  - mesure la duree de l'audio rendu et sa crete ;
  - compare la duree a la duree PLAUSIBLE du texte, avec la MEME regle que le
    service NeuTTS (`duree_max_derivee` : 3 fois la duree plausible, plus 1 s,
    plancher 3 s) ;
  - classe la voix : OK / SILENCE / DERIVE / ERREUR ;
  - copie les WAV fautifs dans `test_voix/sortie_banc_voix_qwen/` pour l'ecoute.

LECTURE SEULE sur le projet : il n'ecrit NI dans la base, NI dans les
catalogues, NI dans les annotations d'ecoute. Il ecrit seulement son rapport.

Usage :
    python test_voix/_banc_qualite_voix_qwen.py                # toutes les voix
    python test_voix/_banc_qualite_voix_qwen.py --phrases 1    # une seule phrase
    python test_voix/_banc_qualite_voix_qwen.py --depuis 40    # reprendre
    python test_voix/_banc_qualite_voix_qwen.py --voix Aubin   # une voix (prenom)
"""
import argparse
import io
import json
import sys
import time
import urllib.request
import wave
from array import array
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_FAUTIFS = Path(__file__).resolve().parent / "sortie_banc_voix_qwen"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(RACINE))

from modules.tts import QWEN_VOICES  # noqa: E402

SERVICE = "http://127.0.0.1:8086"

# Les MEMES seuils que `neutts_service/servir_neutts.py` (3 fois la duree
# plausible, plus 1 s, plancher 3 s) : une phrase francaise lue normalement ne
# peut pas les atteindre, donc au-dela le moteur a derive.
CARACTERES_PAR_SECONDE = 14.0
MARGE_DERIVE = 3.0
MARGE_DERIVE_S = 1.0
DERIVE_MINIMUM_S = 3.0
# En dessous de cette crete, l'audio est un silence (meme seuil que le service).
SEUIL_SILENCE = 0.01
# Une reponse peut legitimement prendre deux minutes si le moteur derape : on
# attend, mais pas indefiniment.
DELAI_S = 600

PHRASES = [
    "Oui, je suis la.",
    "Le 24 fevrier 1815, la vigie de Notre-Dame de la Garde signala le "
    "trois-mats le Pharaon.",
]


def duree_plausible(texte):
    return max(DERIVE_MINIMUM_S,
               (len(texte) / CARACTERES_PAR_SECONDE) * MARGE_DERIVE + MARGE_DERIVE_S)


def prenoms():
    """{identifiant du moteur: prenom du catalogue} (pour lire le rapport)."""
    table = {}
    for voix in QWEN_VOICES:
        table[voix["id"].split(":", 1)[1]] = voix.get("name") or ""
    return table


def lister_voix():
    with urllib.request.urlopen(SERVICE + "/voix", timeout=10) as reponse:
        donnees = json.loads(reponse.read().decode("utf-8", "replace"))
    return list(donnees.get("voix") or [])


def demander(texte, voix):
    """(octets WAV, secondes de calcul). Leve une exception si le service refuse."""
    corps = json.dumps({"texte": texte, "voix": voix}).encode("utf-8")
    requete = urllib.request.Request(
        SERVICE + "/tts", data=corps,
        headers={"Content-Type": "application/json"})
    debut = time.time()
    with urllib.request.urlopen(requete, timeout=DELAI_S) as reponse:
        octets = reponse.read()
    return octets, time.time() - debut


def analyser_wav(octets):
    """(duree, crete) de l'audio rendu, ou (None, None) si illisible."""
    try:
        with wave.open(io.BytesIO(octets), "rb") as f:
            images = f.getnframes()
            frequence = f.getframerate() or 1
            largeur = f.getsampwidth()
            brut = f.readframes(images)
        crete = 0.0
        if largeur == 2 and brut:
            valeurs = array("h")
            valeurs.frombytes(brut[:len(brut) - (len(brut) % 2)])
            if valeurs:
                crete = max(abs(min(valeurs)), abs(max(valeurs))) / 32768.0
        return images / float(frequence), crete
    except Exception:
        return None, None


def verdict(duree, crete, texte):
    """OK / SILENCE / DERIVE / ILLISIBLE, avec la raison en clair."""
    if duree is None:
        return "ILLISIBLE", "WAV illisible"
    if crete is not None and crete < SEUIL_SILENCE:
        return "SILENCE", "audio muet (crete %.4f)" % crete
    maximum = duree_plausible(texte)
    if duree > maximum:
        return "DERIVE", ("%.1f s pour un texte de %d caracteres (plafond %.1f s)"
                          % (duree, len(texte), maximum))
    return "OK", "%.2f s (plafond %.1f s)" % (duree, maximum)


def main():
    analyseur = argparse.ArgumentParser(
        description="Mesure la qualite des voix Qwen, une par une.")
    analyseur.add_argument("--phrases", type=int, default=2,
                           help="nombre de phrases de test (1 ou 2, defaut 2)")
    analyseur.add_argument("--depuis", type=int, default=0,
                           help="reprendre a la Nieme voix (1 = la premiere)")
    analyseur.add_argument("--voix", default="",
                           help="ne tester qu'une voix : identifiant ou prenom")
    options = analyseur.parse_args()

    try:
        voix_service = lister_voix()
    except Exception as e:
        print("ERR : le moteur ne repond pas sur %s (%s)" % (SERVICE, e))
        print("      Lancer d'abord : qwentts_service\\DEMARRER_QWENTTS_CPP.bat")
        return 1

    table = prenoms()
    if options.voix:
        cherche = options.voix.lower()
        voix_service = [v for v in voix_service
                        if cherche in v.lower()
                        or cherche == (table.get(v, "").lower())]
        if not voix_service:
            print("ERR : aucune voix ne correspond a « %s »" % options.voix)
            return 1
    if options.depuis > 0:
        voix_service = voix_service[options.depuis - 1:]

    phrases = PHRASES[:max(1, min(options.phrases, len(PHRASES)))]

    print("=" * 72)
    print(" BANC DE QUALITE DES VOIX QWEN -- %d voix, %d phrase(s)"
          % (len(voix_service), len(phrases)))
    print("=" * 72)
    print(" Moteur : %s" % SERVICE)
    print(" Regle de derive : 3 x duree plausible + 1 s (plancher 3 s), la meme")
    print(" que le service NeuTTS. Rien n'est modifie : on ecoute ce que le")
    print(" moteur rend, on ne touche ni a la base, ni aux voix, ni aux notes.")
    print("")

    debut_general = time.time()
    resultats = []
    for rang, voix in enumerate(voix_service, 1):
        prenom = table.get(voix, "")
        etiquettes = []
        pire = "OK"
        for texte in phrases:
            octets = b""
            try:
                octets, calcul = demander(texte, voix)
                duree, crete = analyser_wav(octets)
                etat, raison = verdict(duree, crete, texte)
            except Exception as e:
                etat, raison, calcul = "ERREUR", str(e)[:70], 0.0
            etiquettes.append((etat, raison, calcul))
            if etat != "OK":
                pire = etat
                try:                     # le WAV fautif, pour l'oreille de Laurent
                    DOSSIER_FAUTIFS.mkdir(parents=True, exist_ok=True)
                    nom = "%s_%s_%d.wav" % (voix, etat.lower(), len(etiquettes))
                    (DOSSIER_FAUTIFS / nom).write_bytes(octets)
                except Exception:
                    pass
        ecoule = time.time() - debut_general
        print("[%3d/%3d] %-24s %-18s %-9s (%.0f s ecoulees)"
              % (rang, len(voix_service), voix[:24], prenom[:18], pire, ecoule),
              flush=True)
        for etat, raison, calcul in etiquettes:
            print("          %-9s %-50s %5.1f s de calcul"
                  % (etat, raison[:50], calcul), flush=True)
        resultats.append((voix, prenom, pire, etiquettes))

    print("")
    print("=" * 72)
    fautives = [r for r in resultats if r[2] != "OK"]
    print(" RESUME : %d voix testee(s), %d fautive(s)"
          % (len(resultats), len(fautives)))
    print("=" * 72)
    for voix, prenom, pire, etiquettes in fautives:
        print("  %-9s %-24s %-18s" % (pire, voix, prenom))
        for etat, raison, _calcul in etiquettes:
            if etat != "OK":
                print("            %-9s %s" % (etat, raison))
    if not fautives:
        print("  aucune : toutes les voix ont rendu une phrase plausible.")
    print("")
    print(" WAV des voix fautives (a ecouter) : %s" % DOSSIER_FAUTIFS)
    print(" Rien n'a ete modifie dans le projet (ni base, ni catalogue, ni notes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
