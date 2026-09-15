# -*- coding: utf-8 -*-
"""
Ecoute d'autres voix FRANCAISES : le jeu CML-TTS, source de nos 35 voix.

Nos 35 voix viennent du dossier `cml-tts/fr` de la banque Kyutai, qui n'est
qu'un EXTRAIT du jeu public « CML-TTS » (Universite federale de Goias,
`ylacombe/cml-tts` sur Hugging Face) : des audiobooks du domaine public lus
par des volontaires, en CC BY 4.0. La partie francaise contient ~115 000
extraits (~286 h) : il y a donc bien d'autres voix a decouvrir.

CONTRAINTE : ce jeu pese 580 Go. On ne le telecharge donc JAMAIS. On
interroge l'API publique du jeu (`datasets-server`), qui renvoie pour chaque
extrait une adresse directe vers son WAV ; on ne recupere que les quelques
extraits voulus.

Ce script :
  1. parcourt le jeu pour trouver des LECTEURS DIFFERENTS de ceux deja en
     service (un extrait par lecteur, jamais deux fois la meme voix) ;
  2. telecharge ces extraits dans `sortie_ecoute_cml/`, numerotes dans
     l'ordre d'ecoute ;
  3. ecrit `index_ecoute.txt` : genre, etoiles, remarque, plus la duree, la
     hauteur mesuree et le DEBUT DU TEXTE LU (pour reperer une mauvaise
     prononciation).

La sortie sert a XTTS v2 (clonage) : un extrait de 10 a 16 s lui suffit.
Pour Kyutai, c'est inutilisable (il faudrait fabriquer une empreinte, ce
qu'aucun outil ne permet).

Usage :
    .venv\\Scripts\\python.exe _ecouter_voix_cml.py --reperage
    .venv\\Scripts\\python.exe _ecouter_voix_cml.py --nombre 50
    .venv\\Scripts\\python.exe _ecouter_voix_cml.py --nombre 50 --pas 900
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
DOSSIER_SORTIE = ICI / "sortie_ecoute_cml"
DOSSIER_35 = ICI / "voix_fr"
# Liste de reprise : une ligne par voix deja telechargee. Permet de relancer
# le script sans rien refaire (et de ne rien perdre si l'API nous bloque).
REPRISE = DOSSIER_SORTIE / "_reprise.txt"

API = "https://datasets-server.huggingface.co/rows"
DATASET = "ylacombe/cml-tts"
CONFIG = "french"
SPLIT = "train"
PAGE = 100          # l'API ne renvoie pas plus de 100 lignes par appel
TOTAL = 107598      # lignes du jeu francais (verifie le 14/09/2026)


def speakers_deja_utilises():
    """Identifiants des 35 lecteurs deja en service.

    Le nom des fichiers (ex. `10087_11650_000028-0002_enhanced.wav`) commence
    par le numero du lecteur : c'est ce premier nombre qu'on ecarte, pour ne
    pas reecouter quelqu'un dont une voix est deja dans le lecteur.
    """
    utilises = set()
    if DOSSIER_35.is_dir():
        for fichier in DOSSIER_35.rglob("*.wav"):
            nom = fichier.stem
            if nom.endswith("_enhanced"):
                nom = nom[:-len("_enhanced")]
            premier = nom.split("_")[0]
            if premier.isdigit():
                utilises.add(int(premier))
    return utilises


def lire_page(offset, pause=1.5, essais=4):
    """Une page de 100 extraits du jeu (aucune donnee lourde telechargee).

    L'API publique limite le rythme des appels : au-dela, elle repond
    « 429 Too Many Requests ». Constate le 14/09/2026 : le script s'etait
    fait bloquer a l'appel 89, apres avoir repere 32 voix -- tout etait
    perdu, car rien n'avait encore ete telecharge. D'ou la PAUSE entre deux
    appels, et la nouvelle tentative apres une attente plus longue.
    """
    adresse = (API + "?dataset=" + urllib.parse.quote(DATASET, safe="")
               + "&config=" + CONFIG + "&split=" + SPLIT
               + "&offset=%d&length=%d" % (offset, PAGE))
    for essai in range(essais):
        try:
            with urllib.request.urlopen(adresse, timeout=90) as reponse:
                page = json.loads(reponse.read().decode("utf-8"))
            time.sleep(pause)
            return page
        except urllib.error.HTTPError as erreur:
            if erreur.code == 429 and essai < essais - 1:
                attente = 15 * (essai + 1)
                print("      (l'API demande de ralentir : pause de %d s)"
                      % attente)
                time.sleep(attente)
                continue
            raise
    return {"rows": []}


def duree_wav(chemin):
    with wave.open(str(chemin), "rb") as f:
        return f.getnframes() / float(f.getframerate())


def hauteur_mediane(chemin):
    """Repere grave/aigu (autocorrelation), meme methode que l'atelier."""
    import numpy as np
    with wave.open(str(chemin), "rb") as f:
        signal = np.frombuffer(
            f.readframes(f.getnframes()), dtype="<i2"
        ).astype(np.float64)
        sr = f.getframerate()
    if sr <= 0 or len(signal) < sr:
        return None
    fenetre = int(sr * 0.04)
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


def reperage(pas, appels):
    """Ou sont les voix dans le jeu ? (diagnostic, rien n'est telecharge)"""
    print("Reperage dans le jeu francais (%d lignes au total)..." % TOTAL)
    print("")
    offset = 0
    for _ in range(appels):
        if offset >= TOTAL:
            break
        page = lire_page(offset)
        lecteurs = sorted({l["row"]["speaker_id"] for l in page["rows"]})
        exemple = page["rows"][0]["row"]["text"][:45]
        print("  offset %7d : lecteurs %s" % (offset, lecteurs))
        print("                  exemple : %s..." % exemple)
        offset += pas
    print("")
    print("Les 35 lecteurs deja en service :")
    print("  %s" % sorted(speakers_deja_utilises()))
    return 0


def fiches_reprises():
    """Voix deja telechargees lors d'une execution precedente.

    Fichier `_reprise.txt`, une ligne par voix :
        numero|lecteur|fichier|duree|hauteur|texte lu
    """
    fiches = []
    if REPRISE.is_file():
        for ligne in REPRISE.read_text(encoding="utf-8").splitlines():
            m = ligne.split("|")
            if len(m) >= 6 and m[1].strip().isdigit():
                try:
                    fiches.append({
                        "fichier": m[2],
                        "lecteur": int(m[1]),
                        "duree": float(m[3]),
                        "hauteur": (int(m[4]) if m[4].strip().isdigit()
                                    else None),
                        "texte": m[5],
                    })
                except ValueError:
                    continue
    return fiches


def noter_reprise(rang, fiche):
    """Ajoute une voix a la liste de reprise (une ligne par voix)."""
    with open(REPRISE, "a", encoding="utf-8") as f:
        f.write("%d|%d|%s|%.1f|%s|%s\n" % (
            rang, fiche["lecteur"], fiche["fichier"], fiche["duree"],
            ("%d" % fiche["hauteur"]) if fiche["hauteur"] else "n/d",
            " ".join(fiche["texte"].split()).replace("|", " ")))


def collecter_et_telecharger(nombre, pas, appels_max, stagnation):
    """Cherche des lecteurs DIFFERENTS et telecharge chaque extrait aussitot.

    Le telechargement se fait AU FUR ET A MESURE, et non a la fin : constate
    le 14/09/2026, l'API avait bloque le script a l'appel 89 apres avoir
    repere 32 voix -- et tout avait ete perdu, car rien n'etait encore pris.
    Desormais chaque voix trouvee est ecrite sur le disque tout de suite, et
    `_reprise.txt` permet de repartir de la ou on s'etait arrete.
    """
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    fiches = fiches_reprises()
    en_service = speakers_deja_utilises()
    deja = en_service | {f["lecteur"] for f in fiches}
    print("Lecteurs ecartes : %d deja en service + %d deja telecharges"
          % (len(en_service), len(fiches)))
    offset = 0
    appels = 0
    sans_nouveaute = 0
    while len(fiches) < nombre and offset < TOTAL and appels < appels_max:
        page = lire_page(offset)
        appels += 1
        avant = len(fiches)
        for ligne in page["rows"]:
            r = ligne["row"]
            lecteur = r["speaker_id"]
            if lecteur in deja:
                continue
            if float(r.get("levenshtein") or 0) < 0.93:
                continue          # texte et audio ne concordent pas assez
            if not 10.0 <= float(r.get("duration") or 0) <= 16.5:
                continue
            deja.add(lecteur)
            fiche = telecharger_un(len(fiches) + 1, lecteur, r)
            if fiche:
                fiches.append(fiche)
                noter_reprise(len(fiches), fiche)
            if len(fiches) >= nombre:
                break
        sans_nouveaute = 0 if len(fiches) > avant else sans_nouveaute + 1
        print("   %3d appel(s) -- offset %7d -- %d voix -- "
              "%d appel(s) sans nouveaute"
              % (appels, offset, len(fiches), sans_nouveaute))
        if sans_nouveaute >= stagnation:
            print("   ARRET : plus aucun nouveau lecteur depuis %d appels."
                  % stagnation)
            break
        offset += pas
    return fiches


def telecharger_un(numero, lecteur, r):
    """Telecharge UN extrait et renvoie sa fiche (None si echec).

    Appelee des qu'un nouveau lecteur est trouve : la voix est ainsi ecrite
    sur le disque tout de suite, et plus rien ne peut etre perdu.
    """
    adresse = r["audio"][0]["src"]
    cible = DOSSIER_SORTIE / ("voix%02d_lecteur%d.wav" % (numero, lecteur))
    try:
        with urllib.request.urlopen(adresse, timeout=120) as flux:
            cible.write_bytes(flux.read())
    except Exception as erreur:
        print("   voix%02d : telechargement impossible (%s)"
              % (numero, type(erreur).__name__))
        return None
    hauteur = hauteur_mediane(cible)
    duree = duree_wav(cible)
    print("   voix%02d  lecteur %-6d %5.1f s  %6s   %s..."
          % (numero, lecteur, duree,
             ("%.0f Hz" % hauteur) if hauteur else "n/d",
             r["text"][:48]))
    return {"fichier": cible.name, "lecteur": lecteur,
            "duree": round(duree, 1),
            "hauteur": round(hauteur) if hauteur else None,
            "texte": r["text"]}


def ecrire_index(fiches):
    chemin = DOSSIER_SORTIE / "index_ecoute.txt"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("# Autres voix FRANCAISES du jeu CML-TTS (source de nos 35 voix)\n")
        f.write("# Jeu : ylacombe/cml-tts, partie francaise -- licence CC BY 4.0\n")
        f.write("# Attribution a conserver : Kyutai + jeu de donnees CML-TTS "
                "(LibriVox)\n")
        f.write("#\n")
        f.write("# Ce sont des ENREGISTREMENTS D'ORIGINE (aucun moteur, aucune\n")
        f.write("# synthese) : on juge la VOIX, pas un moteur.\n")
        f.write("# Un seul extrait par lecteur : aucun doublon avec les 35 voix\n")
        f.write("# deja en service dans le lecteur.\n")
        f.write("#\n")
        f.write("# A REMPLIR : genre (H/F), etoiles (3 = excellente, 2 = bien,\n")
        f.write("# 1 = passable, 0 = a ecarter) et une remarque libre.\n")
        f.write("# La ligne « texte lu » sert a reperer une mauvaise prononciation.\n")
        f.write("#\n")
        f.write("# %-26s %5s  %6s   %-5s  %-7s  %s\n"
                % ("fichier", "duree", "hauteur", "genre", "etoiles", "remarque"))
        f.write("# " + "-" * 92 + "\n")
        for fiche in fiches:
            f.write("  %-26s %4.1f s  %6s   ......   .......   "
                    "..................\n"
                    % (fiche["fichier"], fiche["duree"],
                       ("%.0f Hz" % fiche["hauteur"])
                       if fiche["hauteur"] else "n/d"))
            f.write("    texte lu : %s\n"
                    % " ".join(fiche["texte"].split())[:150])
    return chemin


def main():
    analyseur = argparse.ArgumentParser(
        description="Ecoute d'autres voix francaises du jeu CML-TTS.")
    analyseur.add_argument("--reperage", action="store_true",
                           help="diagnostic : ou sont les voix dans le jeu ?")
    analyseur.add_argument("--nombre", type=int, default=50,
                           help="nombre de voix a ecouter (defaut 50)")
    analyseur.add_argument("--pas", type=int, default=700,
                           help="ecart entre deux pages parcourues (defaut 700)")
    analyseur.add_argument("--appels-max", dest="appels_max", type=int,
                           default=200, help="garde-fou sur les appels reseau")
    analyseur.add_argument("--stagnation", type=int, default=40,
                           help="arreter apres N appels sans nouveau lecteur "
                                "(defaut 40)")
    analyseur.add_argument("--index-seulement", dest="index_seulement",
                           action="store_true",
                           help="regenerer l'index depuis les voix deja "
                                "telechargees, sans aucun appel reseau")
    options = analyseur.parse_args()

    if options.index_seulement:
        fiches = fiches_reprises()
        if not fiches:
            print("Aucune voix deja telechargee dans %s" % DOSSIER_SORTIE)
            return 1
        index = ecrire_index(fiches)
        total = sum(f["duree"] for f in fiches)
        print("%d voix -- index regenere : %s" % (len(fiches), index))
        print("Duree totale d'ecoute : %.1f minutes" % (total / 60.0))
        return 0

    if options.reperage:
        return reperage(options.pas, 8)

    print("Recherche de %d voix differentes dans le jeu CML-TTS..."
          % options.nombre)
    print("(chaque voix trouvee est telechargee aussitot : rien n'est perdu)")
    print("")
    fiches = collecter_et_telecharger(options.nombre, options.pas,
                                      options.appels_max, options.stagnation)
    if not fiches:
        print("")
        print("Aucune voix trouvee. Le jeu est peut-etre injoignable.")
        return 1

    index = ecrire_index(fiches)
    total = sum(f["duree"] for f in fiches)
    print("")
    print("%d voix pretes dans %s" % (len(fiches), DOSSIER_SORTIE))
    print("Duree totale d'ecoute : %.1f minutes" % (total / 60.0))
    print("Index a remplir      : %s" % index)
    print("FIN")
    return 0


if __name__ == "__main__":
    sys.exit(main())

