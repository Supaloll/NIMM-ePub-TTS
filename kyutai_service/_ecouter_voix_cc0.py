# -*- coding: utf-8 -*-
"""
Ecoute DIRECTE des voix CC0 de la banque Kyutai (aucun moteur necessaire).

Question de Laurent (14/09/2026) : « les 228 voix CC0 de voice-donations,
est-ce qu'elles valent le coup ? » On ne sait presque rien d'elles : leur
LANGUE n'est pas declaree dans la banque (ce sont des dons internationaux),
et seules 2 avaient ete ecoutees le 12/09/2026 (verdict : « non »).

Ce script repond donc a la seule vraie question -- quelle langue, quel
accent ? -- de la facon la plus directe possible : il TELEcharge un
echantillon de voix et les fait ecouter TELLES QUELLES, sans passer par un
moteur. Aucune synthese, donc aucun calcul : juste les enregistrements
d'origine.

Difference avec `_tester_voix_etrangeres.py` : celui-ci fait LIRE du francais
par Kyutai (pour juger un accent), alors qu'ici on veut d'abord savoir ce que
la voix EST. Les deux se completent.

Licence : CC0 (domaine public) -- la plus libre de la banque. Attention tout
de meme : si ces voix servent ensuite de modele de CLONAGE a XTTS v2, l'audio
produit reste soumis a la licence non commerciale du moteur (CPML).

Usage :
    .venv\\Scripts\\python.exe _ecouter_voix_cc0.py
    .venv\\Scripts\\python.exe _ecouter_voix_cc0.py --nombre 12
    .venv\\Scripts\\python.exe _ecouter_voix_cc0.py --graine 1
"""

import argparse
import os
import random
import shutil
import sys
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

ICI = Path(__file__).resolve().parent
DOSSIER_SORTIE = ICI / "sortie_ecoute_cc0"
REPO = "kyutai/tts-voices"
FAMILLE = "voice-donations"

# Les 2 voix deja ecoutees le 12/09/2026 (verdict « non », dont la « voix
# caverne ») : on ne les refait pas ecouter, ce serait du temps perdu.
DEJA_ECOUTEES = {"0a67", "1410"}

# Graine fixe : le meme tirage peut etre refait a l'identique plus tard
# (utile pour retrouver un lot precis). Change-la pour un autre echantillon.
GRAINE_DEFAUT = 20260914


def duree_wav(chemin):
    with wave.open(str(chemin), "rb") as f:
        return f.getnframes() / float(f.getframerate())


def hauteur_mediane(chemin):
    """Hauteur mediane (Hz), meme methode que l'atelier (autocorrelation).

    Sert seulement de repere pour l'ecoute : une valeur basse = voix grave,
    une valeur haute = voix aigue. `None` si le calcul n'aboutit pas (voix
    chuchotee, silence, bruit de fond).
    """
    import numpy as np
    with wave.open(str(chemin), "rb") as f:
        signal = np.frombuffer(
            f.readframes(f.getnframes()), dtype="<i2"
        ).astype(np.float64)
        sr = f.getframerate()
    if sr <= 0 or len(signal) < sr:
        return None
    fenetre = int(sr * 0.04)
    if fenetre <= 0:
        return None
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


def lister_voix(api, nombre, graine):
    """Choisit `nombre` voix de la famille, au hasard mais reproductible.

    On ecarte l'empreinte .safetensors et la version brute : c'est le fichier
    `_enhanced.wav` (enregistrement nettoye, celui que le service utilise)
    qui nous interesse.
    """
    tous = api.list_repo_files(REPO, repo_type="model")
    fichiers = sorted(
        f for f in tous
        if f.startswith(FAMILLE + "/") and f.endswith("_enhanced.wav")
    )
    voix = []
    for fichier in fichiers:
        nom = Path(fichier).name[:-len("_enhanced.wav")]
        if nom in DEJA_ECOUTEES:
            continue
        voix.append((nom, fichier))
    if not voix:
        return []
    if nombre >= len(voix):
        return voix
    return sorted(random.Random(graine).sample(voix, nombre))


def telecharger(voix):
    """Telecharge chaque voix et la pose a plat, numerotee dans l'ordre.

    Numero (`voix01_`, `voix02_`...) pour que le tri du dossier corresponde a
    l'ordre d'ecoute : sur 30 fichiers, on se perd vite autrement.
    """
    from huggingface_hub import hf_hub_download

    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    lignes = []
    for numero, (nom, fichier) in enumerate(voix, 1):
        recu = Path(hf_hub_download(REPO, fichier, repo_type="model",
                                    local_dir=str(DOSSIER_SORTIE)))
        cible = DOSSIER_SORTIE / ("voix%02d_%s.wav" % (numero, nom))
        shutil.move(str(recu), str(cible))
        hauteur = hauteur_mediane(cible)
        duree = duree_wav(cible)
        print("   voix%02d_%-28s %5.1f s  %5s" % (
            numero, nom, duree,
            ("%.0f Hz" % hauteur) if hauteur else "n/d"))
        lignes.append({"fichier": cible.name, "duree": round(duree, 1),
                       "hauteur": round(hauteur) if hauteur else None})

    # Menage : le sous-dossier `voice-donations/` et le cache laisses par le
    # telechargement n'ont plus d'utilite, les fichiers sont a plat.
    for reste in (DOSSIER_SORTIE / FAMILLE, DOSSIER_SORTIE / ".cache"):
        if reste.is_dir():
            shutil.rmtree(reste, ignore_errors=True)
    return lignes


def ecrire_index(lignes, graine):
    chemin = DOSSIER_SORTIE / "index_ecoute.txt"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("# Voix CC0 de la banque Kyutai, ECOUTEES TELLES QUELLES\n")
        f.write("# (aucun moteur, aucune synthese : ce sont les "
                "enregistrements d'origine)\n")
        f.write("#\n")
        f.write("# Banque : kyutai/tts-voices -- dossier `%s`\n" % FAMILLE)
        f.write("# Licence : CC0 (domaine public) -- la plus libre de la banque\n")
        f.write("# Echantillon : %d voix tirees au hasard (graine %d)\n"
                % (len(lignes), graine))
        f.write("# Les 2 voix deja ecoutees le 12/09/2026 (%s) sont ecartees.\n"
                % ", ".join(sorted(DEJA_ECOUTEES)))
        f.write("#\n")
        f.write("# A REMPLIR pour chacune : la LANGUE entendue, l'ACCENT, et\n")
        f.write("# « a garder ? » (oui / non). C'est tout ce qu'on cherche :\n")
        f.write("# reste-t-il des voix interessantes, et pour quel usage ?\n")
        f.write("#\n")
        f.write("# La colonne « hauteur » est un simple repere calcule\n")
        f.write("# automatiquement (grave = valeur basse).\n")
        f.write("#\n")
        f.write("# fichier                  duree   hauteur   langue ?    "
                "accent ?    a garder ?\n")
        f.write("# " + "-" * 100 + "\n")
        for l in lignes:
            f.write("  %-24s %5.1f s  %6s    ..........  ..........  ..........\n"
                    % (l["fichier"], l["duree"],
                       ("%.0f Hz" % l["hauteur"]) if l["hauteur"] else "n/d"))
    return chemin


def main():
    analyseur = argparse.ArgumentParser(
        description="Ecoute directe des voix CC0 de la banque Kyutai.")
    analyseur.add_argument("--nombre", type=int, default=30,
                           help="nombre de voix a ecouter (defaut 30)")
    analyseur.add_argument("--graine", type=int, default=GRAINE_DEFAUT,
                           help="graine du tirage aleatoire (defaut %d)"
                                % GRAINE_DEFAUT)
    options = analyseur.parse_args()

    from huggingface_hub import HfApi

    print("Banque : %s -- dossier %s" % (REPO, FAMILLE))
    print("Tirage de %d voix (graine %d)..."
          % (options.nombre, options.graine))
    voix = lister_voix(HfApi(), options.nombre, options.graine)
    if not voix:
        print("Aucune voix trouvee (reseau ?). Rien n'a ete telecharge.")
        return 1

    print("")
    print("Telechargement (%d voix, environ %d Mo)..."
          % (len(voix), (len(voix) * 640) // 1024))
    lignes = telecharger(voix)

    index = ecrire_index(lignes, options.graine)
    total = sum(l["duree"] for l in lignes)
    print("")
    print("%d voix pretes dans %s" % (len(lignes), DOSSIER_SORTIE))
    print("Duree totale d'ecoute : %.1f minutes" % (total / 60.0))
    print("Index a remplir      : %s" % index)
    print("FIN")
    return 0


if __name__ == "__main__":
    sys.exit(main())

