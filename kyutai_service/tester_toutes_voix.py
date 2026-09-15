# -*- coding: utf-8 -*-
"""
Ecoute des 35 voix francaises Kyutai -- une par fichier, pour l'etiquetage.

Pour chaque voix (dans l'ordre du catalogue du lecteur, c'est-a-dire le tri
des identifiants de fichiers), le script :

  1. fait lire une phrase de reference par le moteur -> un fichier WAV ;
  2. mesure la hauteur (F0 mediane par autocorrelation, meme methode que
     l'atelier NIMM Voix) sur DEUX enregistrements :
       - l'enregistrement de REFERENCE (la personne reelle de CML-TTS),
         qui sert a proposer Homme / Femme / a confirmer ;
       - la voix GENREE par Kyutai (pour information : ce moteur monte
         generalement le registre de 40 a 60 Hz par rapport a la reference) ;
  3. ecrit un index d'ecoute a remplir (a garder ? + etoiles), un mode
     d'emploi en francais et un fichier JSON des propositions.

Le tri des identifiants est ce qui definit le numero « Kyutai NN » du
lecteur : les deux documents doivent donc rester dans cet ordre.

Usage (moteur allume) :
    .venv\\Scripts\\python.exe tester_toutes_voix.py
    .venv\\Scripts\\python.exe tester_toutes_voix.py --phrase 2 --cfg 2.0
"""

import argparse
import json
import sys
import time
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
DOSSIER_VOIX = ICI / "voix_fr" / "cml-tts" / "fr"
DOSSIER_SORTIE = ICI / "sortie_ecoute_toutes"

# Deux phrases au choix : la premiere est celle des autres ecoutes du projet.
PHRASES = [
    "Le 24 février 1815, la vigie de Notre-Dame de la Garde signala le "
    "trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples.",
    "« Ah ! s'écria-t-il, je le savais bien : c'est le bonheur de cet "
    "homme qui me tue. »",
]

SR = 24000
FENETRE = 2400                 # 100 ms
LAG_MIN = int(SR / 400.0)      # borne haute : 400 Hz
LAG_MAX = int(SR / 60.0)       # borne basse : 60 Hz
SEUIL_SILENCE = 0.02 * 32768.0

# Bornes de proposition de genre, sur l'enregistrement de REFERENCE :
# en dessous de 160 Hz c'est presque toujours un homme, au-dessus de 190 Hz
# presque toujours une femme ; entre les deux, l'oreille de Laurent tranche.
SEUIL_HOMME = 160.0
SEUIL_FEMME = 190.0


def lister_voix():
    """Identifiants des voix, tries comme dans le catalogue du lecteur."""
    return sorted(f.name.split("_enhanced.wav")[0]
                  for f in DOSSIER_VOIX.glob("*.safetensors"))


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
    print("L'appareil Kyutai ne repond pas sur %s" % adresse)
    print("Verifie que la fenetre DEMARRER_KYUTAI.bat est bien ouverte.")
    sys.exit(1)


def lire_wav(chemin):
    import numpy as np
    with wave.open(str(chemin), "rb") as f:
        return np.frombuffer(f.readframes(-1), dtype=np.int16).astype(np.float64)


def f0_median(chemin):
    """Hauteur mediane (Hz) sur les portions nettement periodiques."""
    import numpy as np
    signal = lire_wav(chemin)
    valeurs = []
    for debut in range(0, len(signal) - FENETRE, FENETRE // 2):
        bloc = signal[debut:debut + FENETRE]
        bloc = bloc - bloc.mean()
        if np.sqrt((bloc ** 2).mean()) < SEUIL_SILENCE:
            continue
        auto = np.correlate(bloc, bloc, mode="full")[len(bloc) - 1:]
        if auto[0] <= 0:
            continue
        lag = int(np.argmax(auto[LAG_MIN:LAG_MAX])) + LAG_MIN
        if auto[lag] / auto[0] < 0.3:
            continue
        valeurs.append(SR / lag)
    if not valeurs:
        return None
    return float((np.median(valeurs) + np.mean(valeurs)) / 2.0)


def duree_wav(chemin):
    with wave.open(str(chemin), "rb") as f:
        return f.getnframes() / float(f.getframerate())


def proposition(f0_reference):
    """H / F / ? a partir de la hauteur de l'enregistrement de reference."""
    if not f0_reference:
        return "?"
    if f0_reference < SEUIL_HOMME:
        return "H"
    if f0_reference > SEUIL_FEMME:
        return "F"
    return "?"


def ecrire_index(lignes, phrase):
    chemin = DOSSIER_SORTIE / "index_ecoute.txt"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("# Ecoute des 35 voix francaises Kyutai (moteur Kyutai TTS 1.6B)\n")
        f.write("# Moteur : kyutai/tts-1.6b-en_fr (CC BY 4.0)\n")
        f.write("# Voix   : kyutai/tts-voices, dossier cml-tts/fr (CC BY 4.0, CML-TTS)\n")
        f.write("# Phrase lue : %s\n" % phrase)
        f.write("#\n")
        f.write("# F0 ref  = hauteur de la personne enregistree (CML-TTS) : base de la proposition\n")
        f.write("# F0 voix = hauteur de la voix produite par Kyutai (souvent 40 a 60 Hz plus haut)\n")
        f.write("# proposition : H = homme, F = femme, ? = a confirmer a l'oreille\n")
        f.write("#\n")
        f.write("# A REMPLIR : colonne « garder » (oui / non) et « etoiles » (1 a 3, comme Kokoro)\n")
        f.write("#\n")
        f.write("# n°  natif  fichier WAV                    duree   F0 ref   F0 voix  proposition  garder ?  etoiles\n")
        f.write("# " + "-" * 116 + "\n")
        for l in lignes:
            f.write("  %02d  %-5s %-32s %5.1f s  %6s   %6s    %-11s  .........  ......\n"
                    % (l["numero"], l["nom_court"], l["fichier"], l["duree"],
                       ("%.0f Hz" % l["f0_ref"]) if l["f0_ref"] else "n/d",
                       ("%.0f Hz" % l["f0_voix"]) if l["f0_voix"] else "n/d",
                       l["proposition"]))
    return chemin


def ecrire_mode_emploi(phrase):
    chemin = DOSSIER_SORTIE / "mode_emploi_ecoute.txt"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("ECOUTE DES 35 VOIX FRANCAISES KYUTAI\n")
        f.write("=" * 60 + "\n\n")
        f.write("Phrase lue par toutes les voix :\n  %s\n\n" % phrase)
        f.write("Les fichiers sont numerotes dans l'ordre du catalogue du lecteur :\n")
        f.write("  01_...wav = « Kyutai 01 » dans les menus du narrateur et du casting.\n\n")
        f.write("A faire :\n")
        f.write("  1. ecouter chaque fichier (lecteur audio, dans ce dossier) ;\n")
        f.write("  2. dans index_ecoute.txt, remplir deux colonnes :\n")
        f.write("       - « garder ? »  : oui si la voix te plait, non sinon ;\n")
        f.write("       - « etoiles »   : 1 a 3, comme les voix Kokoro. Elles servent\n")
        f.write("         a trier automatiquement : les mieux notees sont proposees\n")
        f.write("         en premier aux personnages importants ;\n")
        f.write("  3. la colonne « proposition » (H = homme, F = femme, ? = a\n")
        f.write("     confirmer) vient de la hauteur mesuree sur l'enregistrement\n")
        f.write("     d'origine : elle sert a ranger les voix par genre.\n\n")
        f.write("Rien n'est modifie dans le lecteur : ce dossier ne sert qu'a ecouter.\n")
    return chemin


def main():
    analyseur = argparse.ArgumentParser(
        description="Fait lire une phrase par les 35 voix Kyutai, une par fichier.")
    analyseur.add_argument("--adresse", default="http://127.0.0.1:8082")
    analyseur.add_argument("--phrase", type=int, default=1, choices=[1, 2],
                           help="quelle phrase faire lire (1 ou 2)")
    analyseur.add_argument("--cfg", type=float, default=None,
                           help="guidage par la voix (defaut : celui du service)")
    analyseur.add_argument("--a-partir-de", dest="depart", type=int, default=1,
                           help="reprendre a la voix n° N (1 par defaut)")
    options = analyseur.parse_args()

    attendre_moteur(options.adresse)
    voix = lister_voix()
    phrase = PHRASES[options.phrase - 1]
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

    print("%d voix a faire lire (phrase %d)." % (len(voix), options.phrase))
    print("")

    lignes = []
    for numero, identifiant in enumerate(voix, 1):
        nom_fichier = "%02d_%s.wav" % (numero, identifiant)
        cible = DOSSIER_SORTIE / nom_fichier

        if numero < options.depart and cible.is_file():
            f0_voix = f0_median(cible)      # deja genere : on ne refait pas
        else:
            demande = {"texte": phrase, "voix": identifiant}
            if options.cfg is not None:
                demande["cfg"] = options.cfg
            t0 = time.time()
            cible.write_bytes(appeler(options.adresse, "/tts", demande))
            f0_voix = f0_median(cible)
            print("  %02d/%02d  %-30s %5.1f s d'audio  calcul %4.1f s"
                  % (numero, len(voix), identifiant, duree_wav(cible),
                     time.time() - t0))

        reference = DOSSIER_VOIX / (identifiant + "_enhanced.wav")
        f0_ref = f0_median(reference) if reference.is_file() else None

        lignes.append({
            "numero": numero,
            "identifiant": identifiant,
            "nom_catalogue": "Kyutai %02d" % numero,
            "nom_court": identifiant.split("_")[0],
            "fichier": nom_fichier,
            "duree": round(duree_wav(cible), 1),
            "f0_ref": round(f0_ref) if f0_ref else None,
            "f0_voix": round(f0_voix) if f0_voix else None,
            "proposition": proposition(f0_ref),
        })

    index = ecrire_index(lignes, phrase)
    mode = ecrire_mode_emploi(phrase)
    with open(DOSSIER_SORTIE / "propositions_genre.json", "w",
              encoding="utf-8") as f:
        json.dump({l["identifiant"]: {"nom_catalogue": l["nom_catalogue"],
                                      "proposition": l["proposition"],
                                      "f0_ref": l["f0_ref"]}
                   for l in lignes}, f, ensure_ascii=False, indent=2)

    hommes = sum(1 for l in lignes if l["proposition"] == "H")
    femmes = sum(1 for l in lignes if l["proposition"] == "F")
    doute = sum(1 for l in lignes if l["proposition"] == "?")
    print("")
    print("Voix proposees : %d hommes, %d femmes, %d a confirmer."
          % (hommes, femmes, doute))
    print("Fichiers a ecouter : %s" % DOSSIER_SORTIE)
    print("Index a remplir   : %s" % index)
    print("Mode d'emploi     : %s" % mode)
    print("FIN")


if __name__ == "__main__":
    main()
