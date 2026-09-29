# -*- coding: utf-8 -*-
"""
Compare le VOLUME entendu, phrase par phrase, entre Qwen et d'autres moteurs.

Pourquoi (29/09/2026, retour d'ecoute de Laurent) : « voir si on peut lisser le
volume, qui a tendance a un peu plus varier que les autres moteurs ».

Ce que l'outil mesure, sur les MEMES phrases, moteur par moteur :

  1. le **niveau de parole** de chaque phrase (mediane des fenetres de 30 ms ou
     l'on parle vraiment, en % de la pleine echelle) : c'est ce que
     `modules/audio_gain.py` corrige, vers une cible de 8,5 % ;
  2. l'**ecart entre la phrase la plus faible et la plus forte, en dB** : c'est
     ce qui s'entend comme « un volume qui varie » ;
  3. la **dispersion INTERNE** de chaque phrase (etendue des niveaux de fenetres,
     en dB) : le module corrige le niveau GLOBAL d'une phrase, jamais ses
     variations A L'INTERIEUR -- c'est la qu'un moteur peut se distinguer.

Les phrases passent par le **LECTEUR** (port 8081) : c'est le chemin de la
lecture, donc la normalisation du projet s'applique comme en vrai.

Les voix `qwen:af_nicole` et `kokoro:af_nicole` sont **LE MEME extrait** : le
meme timbre lu par deux moteurs, c'est la comparaison la plus juste. Une voix
Edge sert de repere (c'est la reference de volume du projet : 8,5 %).

Rien n'est modifie : on ne fait qu'ecouter ce que le lecteur rend.

Usage : python test_voix/_comparer_volume_moteurs.py
"""
import argparse
import io
import json
import math
import sys
import urllib.request
import wave
from array import array
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

LECTEUR = "http://127.0.0.1:8081/api/tts"

# Fenetre d'analyse et seuil « ca parle » : les MEMES valeurs que
# `modules/audio_gain.py`, sans quoi on ne mesurerait pas la meme chose que ce
# que le module corrige.
FENETRE_S = 0.030
SEUIL_PAROLE = 0.02 * 32768.0

PHRASES = [
    "Oui.",
    "Il ne repondit pas tout de suite.",
    "Le vent soufflait sur la lande, et personne ne savait ce qui allait arriver.",
    "Mais enfin, mon vieux, tu ne peux pas partir comme ca !",
    "Est-ce que quelqu'un a pense a fermer la porte de la grange ?",
]

# Voix COMPAREES par defaut. Le premier essai (29/09/2026) n'utilisait que
# `af_nicole` -- et Laurent a fait remarquer, tres justement, que c'est une voix
# MURMUREE : « les pointes doivent ressortir plus sur ce genre de voix ». On
# compare donc, sur les MEMES phrases, une voix notee 3 etoiles (fm_lucas), une
# voix neutre (ff_siwis, accent neutre, debit normal) et la voix murmuree, pour
# voir si le defaut lui est propre ou s'il touche tout le moteur.
VOIX_PAR_DEFAUT = ["fm_lucas", "ff_siwis", "af_nicole"]
VOIX_EDGE = "fr-FR-DeniseNeural"


def series(voix):
    """[(etiquette a afficher, identifiant complet)] a mesurer.

    Chaque voix est mesuree chez **Qwen** et chez **Kokoro** : ce sont les MEMES
    extraits, donc le meme timbre lu par deux moteurs. Edge sert de repere (c'est
    la reference de volume du projet, 8,5 %).
    """
    paires = []
    for identifiant in voix:
        paires.append(("qwen:%s" % identifiant, "qwen:%s" % identifiant))
        paires.append(("kokoro:%s" % identifiant, "kokoro:%s" % identifiant))
    paires.append(("edge (repere)", VOIX_EDGE))
    return paires


def demander(texte, voix):
    corps = json.dumps({"text": texte, "voice": voix, "rate": "+0%",
                        "pitch": "+0Hz", "book_id": 0}).encode("utf-8")
    requete = urllib.request.Request(
        LECTEUR, data=corps, headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(requete, timeout=600) as reponse:
        return reponse.read()


def lire_wav(octets):
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        frequence = fichier.getframerate()
        echantillons = array("h")
        echantillons.frombytes(fichier.readframes(fichier.getnframes()))
    return frequence, echantillons


def niveaux_des_fenetres(frequence, echantillons):
    """Niveaux (RMS, en % de la pleine echelle) des fenetres ou l'on PARLE."""
    pas = max(1, int(FENETRE_S * frequence))
    niveaux = []
    for debut in range(0, len(echantillons) - pas + 1, pas):
        fenetre = echantillons[debut:debut + pas]
        pic = max(max(fenetre), -min(fenetre))
        if pic < SEUIL_PAROLE:
            continue                    # silence : on ne mesure pas le souffle
        carres = sum(float(v) * v for v in fenetre) / len(fenetre)
        niveaux.append(100.0 * (carres ** 0.5) / 32768.0)
    return sorted(niveaux)


def mediane(valeurs):
    if not valeurs:
        return 0.0
    milieu = len(valeurs) // 2
    if len(valeurs) % 2:
        return valeurs[milieu]
    return 0.5 * (valeurs[milieu - 1] + valeurs[milieu])


def en_db(niveau, reference):
    """Ecart en dB entre deux niveaux (un rapport, pas un niveau absolu)."""
    if niveau <= 0 or reference <= 0:
        return 0.0
    return 20.0 * math.log10(niveau / reference)


def lire_audio(octets):
    """(frequence, echantillons) : WAV (la plupart des moteurs) ou MP3 (Edge)."""
    if octets[:4] == b"RIFF":
        return lire_wav(octets)
    import subprocess
    import tempfile
    from imageio_ffmpeg import get_ffmpeg_exe
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fichier:
        fichier.write(octets)
        chemin = fichier.name
    try:
        commande = [get_ffmpeg_exe(), "-v", "error", "-i", chemin,
                    "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "24000",
                    "-ac", "1", "-"]
        resultat = subprocess.run(commande, capture_output=True, timeout=180)
        echantillons = array("h")
        echantillons.frombytes(resultat.stdout[:len(resultat.stdout) // 2 * 2])
        return 24000, echantillons
    finally:
        try:
            Path(chemin).unlink()
        except OSError:
            pass


def mesurer(octets):
    """(niveau de parole, etendue interne en dB) d'un audio rendu."""
    frequence, echantillons = lire_audio(octets)
    niveaux = niveaux_des_fenetres(frequence, echantillons)
    if not niveaux:
        return 0.0, 0.0
    niveau = mediane(niveaux)
    # Etendue INTERNE : du 10e au 90e centile, pour ignorer les extremes
    # (une attaque tres faible ou une fin tres forte ne font pas « un volume qui
    # varie » du debut a la fin de la phrase).
    bas = niveaux[int(0.10 * (len(niveaux) - 1))]
    haut = niveaux[int(0.90 * (len(niveaux) - 1))]
    return niveau, en_db(haut, bas)


def main():
    analyseur = argparse.ArgumentParser(
        description="Compare le volume entendu entre Qwen, Kokoro et Edge.")
    analyseur.add_argument("--voix", nargs="*", default=VOIX_PAR_DEFAUT,
                           help="voix a comparer, sans prefixe "
                                "(defaut : %s)" % " ".join(VOIX_PAR_DEFAUT))
    options = analyseur.parse_args()

    print("")
    print("=" * 76)
    print(" VOLUME ENTENDU, PHRASE PAR PHRASE -- Qwen contre les autres moteurs")
    print("=" * 76)
    print(" Chemin de mesure : le LECTEUR (port 8081), donc normalisation comprise,")
    print(" exactement comme en lecture. Cible du module audio_gain : 8,5 %.")
    print(" Voix comparees : %s" % ", ".join(options.voix))
    print("")

    resultats = {}
    for etiquette, voix in series(options.voix):
        lignes = []
        print("--- %s ---" % etiquette.upper())
        for rang, phrase in enumerate(PHRASES, 1):
            try:
                octets = demander(phrase, voix)
                niveau, interne = mesurer(octets)
            except Exception as e:
                print("  %2d. ERREUR : %s" % (rang, str(e)[:60]), flush=True)
                continue
            lignes.append((len(phrase), niveau, interne))
            print("  %2d. %3d car.  niveau %5.2f %%   variation interne %4.2f dB"
                  % (rang, len(phrase), niveau, interne), flush=True)
        resultats[etiquette] = lignes
        print("")

    print("=" * 76)
    print(" SYNTHESE")
    print("=" * 76)
    print(" %-22s %9s %9s %9s %10s %13s"
          % ("serie", "median", "mini", "maxi", "ecart dB", "interne dB"))
    for etiquette, _voix in series(options.voix):
        lignes = resultats.get(etiquette) or []
        if not lignes:
            continue
        niveaux = sorted(ligne[1] for ligne in lignes)
        internes = sorted(ligne[2] for ligne in lignes)
        print(" %-22s %8.2f%% %8.2f%% %8.2f%% %9.2f %12.2f"
              % (etiquette, mediane(niveaux), niveaux[0], niveaux[-1],
                 en_db(niveaux[-1], niveaux[0]), mediane(internes)))
    print("")
    print(" A LIRE : « ecart dB » = entre la phrase la plus faible et la plus forte")
    print(" (plus c'est petit, plus le volume est REGULIER). « interne dB » = la")
    print(" variation A L'INTERIEUR d'une phrase, que le module audio_gain ne")
    print(" corrige PAS (il ne corrige que le niveau global de chaque phrase).")
    print("")
    print(" Rien n'a ete modifie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
