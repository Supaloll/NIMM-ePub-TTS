# -*- coding: utf-8 -*-
"""Mesure objective des bords des WAV produits par XTTS (outil jetable).

Retour de Laurent du 15/09/2026 : « avec XTTS, les points marquent souvent une
pause plus longue qu'avec Kokoro ou Edge ». Ce script ne modifie RIEN : il
mesure, pour chaque WAV :

    - la duree totale ;
    - le silence de TETE (avant le premier son) ;
    - le silence de QUEUE (apres le dernier son) ;
    - les pauses internes de plus de 0,30 s (pour reperer les artefacts).

Methode identique a celle de _ecouter_guillemets.py (seuil d'amplitude 0,012,
fenetre 0,02 s, silence = plage d'au moins 0,15 s sous le seuil), pour que les
chiffres soient comparables. Aucune dependance : bibliotheque standard seule.

Usage :
    python _mesurer_bords_xtts.py                       (le lot par defaut)
    python _mesurer_bords_xtts.py <dossier>             (un autre dossier)
    python _mesurer_bords_xtts.py --rogner              (APRES le remede :
        le rognage du service est applique avant la mesure, sans relancer
        le moteur)
"""

import argparse
import sys
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent
LOT_DEFAUT = ICI / "sortie_ecoute_guillemets"

SEUIL = 0.012          # amplitude en dessous de laquelle on considere le silence
FENETRE = 0.02         # pas d'analyse (s)
MINI_SILENCE = 0.15    # duree minimale pour compter un silence (s)
PAUSE_INTERNE = 0.30   # pauses internes signalees (s)


def charger_rogneur():
    """Fonction de rognage du service (sans demarrer le moteur ni PyTorch)."""
    from importlib.util import module_from_spec, spec_from_file_location

    chemin = ICI / "servir_xtts.py"
    spec = spec_from_file_location("servir_xtts_mesure", chemin)
    service = module_from_spec(spec)
    spec.loader.exec_module(service)
    return service.rogner_queue


def lire_wav(chemin):
    """Renvoie (echantillons flottants entre -1 et 1, frequence)."""
    import array
    with wave.open(str(chemin), "rb") as f:
        canaux = f.getnchannels()
        largeur = f.getsampwidth()
        frequence = f.getframerate()
        brut = f.readframes(f.getnframes())
    if largeur != 2:
        raise ValueError("WAV non 16 bits : %s" % chemin.name)
    donnees = array.array("h")
    donnees.frombytes(brut)
    if canaux > 1:                      # on ne garde qu'un canal sur deux
        donnees = donnees[::canaux]
    return [v / 32768.0 for v in donnees], frequence


def analyser(chemin, rogner=None):
    """Renvoie (duree, silence_tete, silence_queue, segments, pauses).

    `rogner` : fonction facultative (celle du service) appliquee aux
    echantillons avant la mesure -- permet de voir ce que donneront les
    phrases APRES le rognage du silence de queue, sans relancer le moteur.
    """
    echantillons, frequence = lire_wav(chemin)
    if rogner is not None:
        echantillons = list(rogner(echantillons, frequence))
    if not echantillons:
        return 0.0, 0.0, 0.0, 0, []
    pas = max(1, int(FENETRE * frequence))

    # Amplitude max de chaque fenetre : au-dessus du seuil = de la parole.
    parles = []
    for debut in range(0, len(echantillons), pas):
        fenetre = echantillons[debut:debut + pas]
        if not fenetre:
            break
        parles.append(1.0 if max(abs(v) for v in fenetre) >= SEUIL else 0.0)

    duree = len(echantillons) / float(frequence)

    # Silences de bord.
    if not any(parles):
        return duree, duree, 0.0, 0, []
    premier = parles.index(1.0)
    dernier = len(parles) - 1 - parles[::-1].index(1.0)
    silence_tete = premier * FENETRE
    silence_queue = (len(parles) - 1 - dernier) * FENETRE

    # Segments de parole et pauses internes assez longues.
    segments = 0
    pauses = []
    dedans = False
    debut_silence = None
    for i, p in enumerate(parles):
        if p and not dedans:
            segments += 1
            dedans = True
            if debut_silence is not None:
                longueur = (i - debut_silence) * FENETRE
                if longueur >= PAUSE_INTERNE:
                    pauses.append((debut_silence * FENETRE, longueur))
                debut_silence = None
        elif not p and dedans:
            dedans = False
            debut_silence = i

    return duree, silence_tete, silence_queue, segments, pauses


def main():
    parseur = argparse.ArgumentParser(
        description="Mesure les silences de bord des WAV XTTS (sans moteur).")
    parseur.add_argument("dossier", nargs="?",
                         help="dossier a mesurer (defaut : le lot d'ecoute)")
    parseur.add_argument(
        "--rogner", action="store_true",
        help="applique d'abord le rognage du service (voir ce que donneront "
             "les phrases APRES le remede, sans relancer le moteur)")
    options = parseur.parse_args()

    dossier = Path(options.dossier) if options.dossier else LOT_DEFAUT
    if not dossier.is_dir():
        print("Dossier introuvable : %s" % dossier)
        return 1

    fichiers = sorted(dossier.rglob("*.wav"))
    if not fichiers:
        print("Aucun WAV dans %s" % dossier)
        return 1

    rogneur = charger_rogneur() if options.rogner else None

    print("Mesure des bords : %s" % dossier)
    print("(seuil %.3f, silence mini %.2f s, pauses internes > %.2f s)"
          % (SEUIL, MINI_SILENCE, PAUSE_INTERNE))
    if rogneur is not None:
        print("ROGNAGE du service applique avant mesure (silence de queue "
              "ramene a %.2f s)" % (rogneur.__globals__["SILENCE_QUEUE_S"]))
    print("")

    queues = []
    for fichier in fichiers:
        duree, tete, queue, segments, pauses = analyser(fichier, rogneur)
        queues.append(queue)
        nom = fichier.relative_to(dossier)
        print("%-40s duree %5.2f s | tete %5.2f | queue %5.2f | parole %d"
              % (str(nom), duree, tete, queue, segments))
        for position, longueur in pauses:
            print("    pause interne a %.2f s de %5.2f s" % (position, longueur))

    if queues:
        print("")
        print("Silence de queue : mini %.2f s | moyen %.2f s | maxi %.2f s"
              % (min(queues), sum(queues) / len(queues), max(queues)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
