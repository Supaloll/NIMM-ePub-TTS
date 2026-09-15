# -*- coding: utf-8 -*-
"""
Essai : une voix ETRANGERE lue sur du texte FRANCAIS.

Question de Laurent (12/09/2026) : « peut-on forcer les voix étrangères en
fr_fr comme pour Kokoro ? »

Kokoro a un réglage de LANGUE (`lang=`) indépendant du timbre : on force
« fr-fr » et la voix garde son accent d'origine. Kyutai n'a pas ce réglage :
c'est le TEXTE donné qui décide de la langue lue. La question devient donc :
que donne le TIMBRE d'une voix anglophone sur une phrase française ? Ce
script met la réponse à l'oreille.

Il télécharge quelques voix d'autres familles de la banque Kyutai, puis fait
lire la même phrase française par chacune :

    vctk             — 106 voix anglaises        (CC BY 4.0)
    voice-donations  — 228 voix données, CC0     (langue non déclarée !)
    ears             — 153 voix anglaises        (CC BY-NC : usage PRIVÉ)

Les fichiers arrivent dans `sortie_ecoute_etrangeres/`, avec un index à noter.

Usage :
    .venv\\Scripts\\python.exe _tester_voix_etrangeres.py
    .venv\\Scripts\\python.exe _tester_voix_etrangeres.py --par-famille 3
    .venv\\Scripts\\python.exe _tester_voix_etrangeres.py --familles vctk voice-donations
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

ICI = Path(__file__).resolve().parent
DOSSIER_AUTRES = ICI / "voix_autres"
DOSSIER_SORTIE = ICI / "sortie_ecoute_etrangeres"
REPO = "kyutai/tts-voices"
SUFFIXE_EMPREINTE = "_enhanced.wav.1e68beda@240.safetensors"

# familles : (dossier dans la banque, description, licence)
FAMILLES = {
    "vctk": ("vctk", "anglais (VCTK)", "CC BY 4.0"),
    "voice-donations": ("voice-donations", "dons de voix (langue non declaree)",
                        "CC0 : domaine public"),
    "ears": ("ears", "anglais expressif (EARS)", "CC BY-NC 4.0 : usage prive"),
}

PHRASES = [
    "Le 24 février 1815, la vigie de Notre-Dame de la Garde signala le "
    "trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples.",
    "« Ah ! s'écria-t-il, je le savais bien : c'est le bonheur de cet "
    "homme qui me tue. »",
]


def appeler(adresse, chemin, donnees=None, delai=600):
    if donnees is None:
        requete = urllib.request.Request(adresse + chemin)
    else:
        corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
        requete = urllib.request.Request(
            adresse + chemin, data=corps,
            headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(requete, timeout=delai) as reponse:
        return reponse.read()


def attendre_moteur(adresse, limite=180):
    debut = time.time()
    while time.time() - debut < limite:
        try:
            etat = json.loads(appeler(adresse, "/sante").decode("utf-8"))
            if etat.get("pret"):
                return etat
        except Exception:
            pass
        time.sleep(2)
    print("Le moteur Kyutai ne repond pas sur %s (DEMARRER_KYUTAI.bat ?)" % adresse)
    sys.exit(1)


def duree_wav(chemin):
    with wave.open(str(chemin), "rb") as f:
        return f.getnframes() / float(f.getframerate())


def f0_median(chemin):
    """Hauteur mediane (Hz), meme methode que l'atelier (autocorrelation)."""
    import numpy as np
    with wave.open(str(chemin), "rb") as f:
        signal = np.frombuffer(f.readframes(-1), dtype=np.int16).astype(np.float64)
    sr, fenetre = 24000, 2400
    lag_min, lag_max = int(sr / 400.0), int(sr / 60.0)
    valeurs = []
    for debut in range(0, len(signal) - fenetre, fenetre // 2):
        bloc = signal[debut:debut + fenetre]
        bloc = bloc - bloc.mean()
        if np.sqrt((bloc ** 2).mean()) < 0.02 * 32768.0:
            continue
        auto = np.correlate(bloc, bloc, mode="full")[len(bloc) - 1:]
        if auto[0] <= 0:
            continue
        lag = int(np.argmax(auto[lag_min:lag_max])) + lag_min
        if auto[lag] / auto[0] < 0.3:
            continue
        valeurs.append(sr / lag)
    if not valeurs:
        return None
    return float((np.median(valeurs) + np.mean(valeurs)) / 2.0)


def choisir_voix(api, famille, combien):
    """Les `combien` premieres voix d'une famille (une par locuteur distinct).

    Deux conventions de nommage coexistent dans la banque :
        cml-tts/fr : <nom>_enhanced.wav.1e68beda@240.safetensors
        vctk, dons : <nom>.wav.1e68beda@240.safetensors
    On accepte les deux, exactement comme le service.
    """
    from huggingface_hub import hf_hub_download

    dossier_repo = FAMILLES[famille][0]
    tous = api.list_repo_files(REPO, repo_type="model")

    def _nom(fichier):
        if "_enhanced.wav" in fichier:
            return Path(fichier).name.split("_enhanced.wav")[0], True
        if ".wav." in fichier:
            return Path(fichier).name.split(".wav.")[0], False
        return None, False

    empreintes = sorted(f for f in tous
                        if f.startswith(dossier_repo + "/")
                        and f.endswith(".safetensors")
                        and _nom(f)[0])

    choisies, vus = [], set()
    for reference in empreintes:
        nom, ameliore = _nom(reference)
        locuteur = nom.split("_")[0]
        if locuteur in vus:
            continue
        vus.add(locuteur)
        choisies.append((nom, reference))
        if len(choisies) >= combien:
            break

    for nom, reference in choisies:
        hf_hub_download(REPO, reference, repo_type="model",
                        local_dir=str(DOSSIER_AUTRES))
    return choisies


def ecrire_index(lignes, phrase):
    chemin = DOSSIER_SORTIE / "index_ecoute.txt"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("# Voix ETRANGERES lues sur du texte FRANCAIS (moteur Kyutai TTS 1.6B)\n")
        f.write("# Moteur : kyutai/tts-1.6b-en_fr (bilingue anglais + francais)\n")
        f.write("# Phrase lue (en francais) : %s\n" % phrase)
        f.write("#\n")
        f.write("# Question posee : une voix anglaise garde-t-elle son accent quand elle\n")
        f.write("# lit du francais ? (comme les voix Kokoro forcees en fr-fr)\n")
        f.write("#\n")
        f.write("# A REMPLIR : « accent ? » (aucun / leger / fort) et « a garder ? » (oui/non)\n")
        f.write("#\n")
        f.write("# fichier                              famille           licence                  duree   F0      accent ?  a garder ?\n")
        f.write("# " + "-" * 132 + "\n")
        for l in lignes:
            f.write("  %-36s %-17s %-24s %5.1f s  %5s   ........  .........\n"
                    % (l["fichier"], l["famille"], l["licence"], l["duree"],
                       ("%.0f Hz" % l["f0"]) if l["f0"] else "n/d"))
    return chemin


def main():
    analyseur = argparse.ArgumentParser(
        description="Fait lire une phrase francaise par des voix etrangeres.")
    analyseur.add_argument("--adresse", default="http://127.0.0.1:8082")
    analyseur.add_argument("--familles", nargs="*", default=list(FAMILLES),
                           choices=list(FAMILLES))
    analyseur.add_argument("--par-famille", dest="combien", type=int, default=2,
                           help="nombre de voix par famille (defaut 2)")
    analyseur.add_argument("--phrase", type=int, default=1, choices=[1, 2])
    options = analyseur.parse_args()

    from huggingface_hub import HfApi

    attendre_moteur(options.adresse)
    api = HfApi()
    phrase = PHRASES[options.phrase - 1]
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

    connues = set(json.loads(appeler(options.adresse, "/voix").decode("utf-8"))["voix"])
    print("Le moteur connait %d voix (dont les voix d'essai deja telechargees)."
          % len(connues))
    print("Phrase lue : %s" % phrase)
    print("")

    lignes = []
    for famille in options.familles:
        description, licence = FAMILLES[famille][1], FAMILLES[famille][2]
        print("--- %s -- %s (%s)" % (famille, description, licence))
        voix_famille = choisir_voix(api, famille, options.combien)
        # On demande au service de relire ses dossiers de voix : ainsi une voix
        # tout juste telechargee est utilisable SANS redemarrer le moteur.
        recharge = json.loads(appeler(options.adresse, "/recharger", {}).decode("utf-8"))
        connues = set(recharge["liste"])
        for nom, _reference in voix_famille:
            identifiant = "%s_%s" % (famille, nom)
            if identifiant not in connues:
                print("   %-22s IGNOREE : le service ne connait pas cette voix "
                      "(redemarre DEMARRER_KYUTAI.bat et relance)." % identifiant)
                continue
            cible = DOSSIER_SORTIE / ("%s_%s.wav" % (famille, nom))
            t0 = time.time()
            cible.write_bytes(appeler(options.adresse, "/tts",
                                      {"texte": phrase, "voix": identifiant}))
            f0 = f0_median(cible)
            print("   %-22s %5.1f s d'audio  %5s  calcul %4.1f s"
                  % (identifiant, duree_wav(cible),
                     ("%.0f Hz" % f0) if f0 else "n/d", time.time() - t0))
            lignes.append({"fichier": cible.name, "famille": famille,
                           "licence": licence, "duree": round(duree_wav(cible), 1),
                           "f0": round(f0) if f0 else None})

    if not lignes:
        print("")
        print("Rien a ecouter : aucune voix d'essai n'a pu etre generee.")
        return 1

    index = ecrire_index(lignes, phrase)
    print("")
    print("%d fichiers a ecouter dans %s" % (len(lignes), DOSSIER_SORTIE))
    print("Index a remplir : %s" % index)
    print("FIN")
    return 0


if __name__ == "__main__":
    sys.exit(main())

