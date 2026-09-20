# -*- coding: utf-8 -*-
"""L'ecoute de controle du moteur Pocket TTS.

Il interroge le service EXACTEMENT comme le fait le lecteur (/sante, /voix), puis
genere un petit lot d'ecoute dans `sortie_ecoute\\` avec un `index_ecoute.txt` :
c'est la liste a ecouter pour dire oui ou non avant tout branchement.

Usage (depuis pocket_tts_service, le moteur doit etre allume) :
    .venv\\Scripts\\python.exe tester_service.py
    .venv\\Scripts\\python.exe tester_service.py --voix Femme001 --voix Homme002
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

ICI = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8085"

# Trois phrases de controle, de longueurs differentes : la courte dit si le
# moteur decroche sur les repliques, la longue si le texte est saute (defaut
# connu au-dela de ~350 caracteres).
PHRASES = [
    ("01_courte", "Non."),
    ("02_moyenne", "Le 24 fevrier 1815, la vigie de Notre-Dame de la Garde "
                   "signala le trois-mats le Pharaon, venant de Smyrne, "
                   "Trieste et Naples."),
    ("03_longue", "Comme d'habitude, un pilote cotier partit aussitot du port, "
                  "rasa le chateau d'If, et alla aborder le navire entre le cap "
                  "de Morgion et l'ile de Rion ; puis il jeta l'ancre, et le "
                  "jeune homme que l'on voyait sur le pont se disposa a "
                  "remplir son devoir, en donnant ses ordres pour le "
                  "dechargement."),
]


def appeler(chemin, corps=None):
    """Appelle le service : GET si `corps` est None, POST sinon."""
    if corps is None:
        requete = urllib.request.Request(URL + chemin)
    else:
        donnees = json.dumps(corps, ensure_ascii=False).encode("utf-8")
        requete = urllib.request.Request(
            URL + chemin, data=donnees,
            headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(requete, timeout=180) as reponse:
        return reponse.read(), reponse.headers.get("Content-Type", "")


def duree(wav_bytes):
    """Duree d'un WAV en memoire (on la MESURE, jamais de calcul de tete)."""
    import io
    with wave.open(io.BytesIO(wav_bytes), "rb") as fichier:
        return (fichier.getnframes() / float(fichier.getframerate()),
                fichier.getnframes(), fichier.getframerate())


def main():
    analyseur = argparse.ArgumentParser(
        description="Ecoute de controle du moteur Pocket TTS.")
    analyseur.add_argument("--voix", action="append", default=None,
                           help="voix a essayer (repetable) ; defaut : Femme001")
    analyseur.add_argument("--sortie", default=str(ICI / "sortie_ecoute"))
    options = analyseur.parse_args()
    voix = options.voix or ["Femme001"]

    print("")
    print("=" * 68)
    print("  ESSAI DE CONTROLE -- moteur Pocket TTS (%s)" % URL)
    print("=" * 68)

    # 1) Le service repond-il, et est-il pret ?
    try:
        sante = json.loads(appeler("/sante")[0].decode("utf-8"))
    except Exception as erreur:
        print("  Le moteur ne repond pas (%s)." % erreur)
        print("  Allume-le : DEMARRER_POCKET_TTS.bat")
        return 1
    print("  pret              : %s" % sante.get("pret"))
    print("  modele            : %s" % sante.get("modele"))
    print("  coeurs du moteur  : %s" % sante.get("coeurs"))
    if sante.get("erreur"):
        print("  ERREUR du moteur  : %s" % sante.get("erreur"))
    if not sante.get("pret"):
        print("  Le moteur charge encore : relance dans quelques secondes.")
        return 1

    # 2) Les voix annoncees par le moteur.
    liste = json.loads(appeler("/voix")[0].decode("utf-8"))
    print("  voix disponibles  : %d" % liste.get("nombre", 0))
    inconnues = [v for v in voix if v not in (liste.get("voix") or [])]
    if inconnues:
        print("  VOIX INCONNUE(S)  : %s" % ", ".join(inconnues))
        print("  (voix connues : %s)" % ", ".join(sorted(liste.get("voix") or [])))
        return 1

    dossier = Path(options.sortie)
    dossier.mkdir(parents=True, exist_ok=True)
    index = ["# Ecoute de controle -- moteur Pocket TTS",
             "# %d voix, %d phrases chacune" % (len(voix), len(PHRASES)),
             ""]

    print("")
    print("  %-12s %-8s %9s %9s %9s" % ("voix", "phrase", "audio", "calcul", "ratio"))
    print("  " + "-" * 56)

    for nom_voix in voix:
        for etiquette, texte in PHRASES:
            debut = time.time()
            try:
                audio, _type = appeler("/tts", {"texte": texte, "voix": nom_voix})
            except urllib.error.HTTPError as erreur:
                detail = erreur.read().decode("utf-8", "replace")
                print("  %-12s %-8s ECHEC HTTP %d : %s"
                      % (nom_voix, etiquette, erreur.code, detail[:60]))
                return 1
            calcul = time.time() - debut
            secondes, images, frequence = duree(audio)
            ratio = calcul / secondes if secondes else 0.0

            fichier = dossier / ("%s_%s.wav" % (nom_voix, etiquette))
            fichier.write_bytes(audio)
            print("  %-12s %-8s %7.1f s %7.1f s %9.2f"
                  % (nom_voix, etiquette, secondes, calcul, ratio))
            index.append("%-34s %-12s %5.1f s d'audio  (calcul %.1f s)"
                         % (fichier.name, nom_voix, secondes, calcul))

    index.append("")
    index.append("A ecouter : la voix sonne-t-elle bien ? le texte est-il lu")
    index.append("SANS mot saute ni parasite ? (point faible connu du moteur")
    index.append("au-dela de ~350 caracteres)")
    (dossier / "index_ecoute.txt").write_text("\n".join(index), encoding="utf-8")
    print("")
    print("  Lot d'ecoute : %s" % dossier)
    print("  (index : index_ecoute.txt)")
    print("FIN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
