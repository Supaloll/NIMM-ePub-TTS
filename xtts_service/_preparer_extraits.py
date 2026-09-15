# -*- coding: utf-8 -*-
"""Prepare des extraits de voix (MP3) pour le moteur XTTS du lecteur.

Reprend la METHODE VALIDEE A L'ATELIER (outil de reference de NIMM Voix :
`G:\\NIMM Voix\\outils\\xtts_tts\\_preparer_reference.py`) et l'adapte a la
banque de voix de NIMM ePub :

  1. convertit chaque source en **WAV mono 24 000 Hz 16 bits** -- le format
     natif du moteur, celui que le service XTTS attend ;
  2. rogne les silences de **tete et de queue** (ffmpeg, -45 dB, la meme regle
     que pour Edge) pour que l'extrait commence et finisse sur la voix ;
  3. MESURE ce qui sort : duree, silence de tete, silence de queue, et dit si
     c'est dans la plage ideale. Reperes de l'atelier : **10 a 20 s** (6 s =
     minimum officiel du moteur ; au-dela de 30 s le moteur ne garde rien de
     plus) ;
  4. propose l'identifiant de la voix : <prefixe><nom du fichier> en
     minuscules, sans espaces -- « dp_femme001 » pour « Femme001.mp3 » ;
  5. REFUSE d'ecraser une voix deja presente dans xtts_service\\voix_fr\\
     (les 60 voix actuelles ne doivent jamais etre touchees par accident).

DEUX MODES :
    --verifier (defaut) : n'ecrit RIEN, affiche seulement le rapport.
    --verser            : ecrit les WAV dans xtts_service\\voix_fr\\ sous le nom
                          <identifiant>_enhanced.wav (convention du dossier :
                          le service ne retient que la version « _enhanced »
                          quand deux fichiers portent le meme nom).

Apres un versement, le moteur EN MARCHE prend les nouvelles voix sans
redemarrage : le script appelle tout seul POST /recharger s'il repond.

RAPPEL DROITS : ne cloner que sa propre voix, une voix du domaine public
(LibriVox...) ou une voix dont on a les droits. Voir xtts_service\\ATTRIBUTION.md.

Usage :
    python _preparer_extraits.py                      (rapport, dossier par defaut)
    python _preparer_extraits.py --verifier "..\\Extraits de voix"
    python _preparer_extraits.py --verser --prefixe dp_
"""

import argparse
import io
import json
import re
import sys
import tempfile
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
DOSSIER_VOIX = ICI / "voix_fr"
SOURCE_DEFAUT = ICI.parent / "Extraits de voix"
MOTEUR = "http://127.0.0.1:8083"

# Reperes de duree (memes valeurs que l'atelier NIMM Voix).
DUREE_MIN = 6.0        # en dessous : le moteur manque de matiere
DUREE_IDEALE_MIN = 10.0
DUREE_IDEALE_MAX = 20.0
DUREE_MAX_UTILE = 30.0  # au-dela : le moteur tronque, aucun gain

# Seuils de mesure (ceux des outils de mesure deja valides ici).
SEUIL = 0.012
BLOC_S = 0.02

# Rogne les silences de bord en conservant 0,10 s (memes filtres que l'atelier).
ROGNAGE = (
    "silenceremove=start_periods=1:start_duration=0.1:start_threshold=-45dB,"
    "areverse,"
    "silenceremove=start_periods=1:start_duration=0.1:start_threshold=-45dB,"
    "areverse"
)

_FFMPEG = None


def ffmpeg():
    """Le ffmpeg deja embarque dans le lecteur (imageio-ffmpeg, rien a installer)."""
    global _FFMPEG
    if _FFMPEG is None:
        from imageio_ffmpeg import get_ffmpeg_exe
        _FFMPEG = get_ffmpeg_exe()
    return _FFMPEG



def convertir(source, cible, rogner=True):
    """Convertit la source en WAV mono 24 kHz 16 bits. Renvoie (ok, message)."""
    import subprocess

    def lancer(avec_rognage):
        commande = [
            ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(source), "-vn",
            "-ac", "1", "-ar", "24000", "-sample_fmt", "s16",
        ]
        if avec_rognage:
            commande += ["-af", ROGNAGE]
        commande += ["-c:a", "pcm_s16le", str(cible)]
        resultat = subprocess.run(commande, capture_output=True, timeout=180)
        return resultat.returncode == 0, resultat.stderr.decode("utf-8", "replace")

    ok, erreur = lancer(rogner)
    if not ok and rogner:
        # Le filtre peut echouer sur un fichier tres court : on refait sans.
        ok, erreur = lancer(False)
        if ok:
            erreur = "(rognage impossible sur ce fichier : garde tel quel)"
    return ok, erreur.strip()


def mesurer(chemin):
    """(duree, silence_tete, silence_queue) d'un WAV, en secondes."""
    import array

    with wave.open(str(chemin), "rb") as f:
        frequence = f.getframerate()
        canaux = f.getnchannels()
        donnees = array.array("h")
        donnees.frombytes(f.readframes(f.getnframes()))
    if canaux > 1:
        donnees = donnees[::canaux]
    duree = len(donnees) / float(frequence)
    if not donnees:
        return 0.0, 0.0, 0.0

    pas = max(1, int(BLOC_S * frequence))
    seuil = SEUIL * 32768
    parles = []
    for debut in range(0, len(donnees), pas):
        bloc = donnees[debut:debut + pas]
        parles.append(1 if bloc and max(abs(v) for v in bloc) >= seuil else 0)
    if not any(parles):
        return duree, duree, 0.0
    premier = parles.index(1)
    dernier = len(parles) - 1 - parles[::-1].index(1)
    return (duree, premier * BLOC_S, (len(parles) - 1 - dernier) * BLOC_S)


def identifiant(source, prefixe):
    """« Femme001.mp3 » -> « dp_femme001 » (minuscules, sans espace ni accent)."""
    base = source.stem.lower()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    return (prefixe or "") + base


def voix_existantes():
    """Identifiants deja presents dans la banque du moteur."""
    if not DOSSIER_VOIX.is_dir():
        return set()
    noms = set()
    for fichier in DOSSIER_VOIX.glob("*.wav"):
        nom = fichier.stem
        if nom.endswith("_enhanced"):
            nom = nom[:-len("_enhanced")]
        noms.add(nom)
    return noms


def recharger_moteur():
    """Demande au moteur en marche de rescaner le dossier. Ne bloque jamais."""
    try:
        demande = urllib.request.Request(MOTEUR + "/recharger", data=b"", method="POST")
        with urllib.request.urlopen(demande, timeout=8) as reponse:
            infos = json.loads(reponse.read().decode("utf-8"))
        return "moteur recharge : %s voix" % infos.get("voix", "?")
    except Exception as erreur:
        return ("moteur non recharge (%s) : relance DEMARRER_XTTS.bat "
                "pour qu'il voie les nouvelles voix" % erreur)



def main():
    parseur = argparse.ArgumentParser(
        description="Prepare des extraits de voix (MP3) pour le moteur XTTS.")
    parseur.add_argument("source", nargs="?", default=str(SOURCE_DEFAUT),
                         help="dossier des extraits (defaut : « Extraits de voix »)")
    parseur.add_argument("--verser", action="store_true",
                         help="ecrit les WAV dans xtts_service/voix_fr/ "
                              "(sans cette option : rapport seulement)")
    parseur.add_argument("--prefixe", default="dp_",
                         help="prefixe des identifiants (defaut : dp_ = domaine public)")
    parseur.add_argument("--sans-rognage", action="store_true",
                         help="ne pas rogner les silences de bord")
    options = parseur.parse_args()

    dossier = Path(options.source)
    if not dossier.is_dir():
        print("Dossier introuvable : %s" % dossier)
        return 1

    sources = sorted([p for p in dossier.iterdir()
                      if p.is_file() and p.suffix.lower() in
                      (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus")])
    if not sources:
        print("Aucun fichier audio dans %s" % dossier)
        return 1

    deja = voix_existantes()
    print("Sources    : %s (%d fichier(s))" % (dossier, len(sources)))
    print("Banque     : %s (%d voix deja presentes)" % (DOSSIER_VOIX, len(deja)))
    print("Rognage    : %s" % ("non" if options.sans_rognage else "oui (-45 dB, marge 0,10 s)"))
    print("Mode       : %s" % ("VERSER dans la banque" if options.verser
                                 else "verification seulement (rien n'est ecrit)"))
    print("")
    print("%-22s %-14s %7s %6s %6s  %s"
          % ("fichier", "identifiant", "duree", "tete", "queue", "verdict"))

    resultats = []
    a_verser = []
    souci = 0
    with tempfile.TemporaryDirectory() as temporaire:
        for source in sources:
            ident = identifiant(source, options.prefixe)
            cible = Path(temporaire) / (ident + ".wav")
            ok, message = convertir(source, cible, not options.sans_rognage)
            if not ok:
                print("%-22s %-14s %7s %6s %6s  ECHEC : %s"
                      % (source.name, ident, "-", "-", "-", message[:60]))
                souci += 1
                continue

            duree, tete, queue = mesurer(cible)
            verdict = "OK"
            if duree < DUREE_MIN:
                verdict = "TROP COURT (< %.0f s)" % DUREE_MIN
                souci += 1
            elif duree < DUREE_IDEALE_MIN:
                verdict = "un peu court (ideal %.0f-%.0f s)" % (DUREE_IDEALE_MIN, DUREE_IDEALE_MAX)
            elif duree > DUREE_MAX_UTILE:
                verdict = "trop long : le moteur n'utilise que les 30 premieres s"
            elif duree > DUREE_IDEALE_MAX:
                verdict = "un peu long (ideal %.0f-%.0f s)" % (DUREE_IDEALE_MIN, DUREE_IDEALE_MAX)
            if queue > 0.5:
                verdict += " + queue de %.2f s" % queue
            if tete > 0.5:
                verdict += " + tete de %.2f s" % tete

            print("%-22s %-14s %6.2fs %5.2fs %5.2fs  %s"
                  % (source.name, ident, duree, tete, queue, verdict))

            if options.verser:
                if ident in deja:
                    print("       -> REFUSE : la voix « %s » existe deja (rien ecrase)" % ident)
                    souci += 1
                    continue
                if duree < DUREE_MIN:
                    print("       -> REFUSE : trop court pour un clonage fiable")
                    continue
                finale = DOSSIER_VOIX / (ident + "_enhanced.wav")
                DOSSIER_VOIX.mkdir(parents=True, exist_ok=True)
                finale.write_bytes(cible.read_bytes())
                a_verser.append(ident)
                print("       -> versee : %s" % finale.name)
            resultats.append((source.name, ident, duree, tete, queue))

    print("")
    if options.verser:
        print("%d voix versee(s) : %s" % (len(a_verser), ", ".join(a_verser) or "-"))
        if a_verser:
            print(recharger_moteur())
    else:
        print("%d fichier(s) analyse(s). Pour les verser :" % len(resultats))
        print("    python _preparer_extraits.py --verser")
    if souci:
        print("%d point(s) a corriger (voir ci-dessus)." % souci)
    return 0


if __name__ == "__main__":
    sys.exit(main())
