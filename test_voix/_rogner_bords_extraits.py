# -*- coding: utf-8 -*-
"""Rogne les SILENCES DE BORD des extraits de reference des voix Qwen (29/09/2026).

POURQUOI : la mesure des 157 extraits (`_analyser_references_qwen.py`) montre que
**20 d'entre eux** ont un bord « sale » (plus de 0,20 s de silence), avec des cas
a plus d'une seconde : `af_kore` (1,04 s en queue), `am_puck` (0,98 s), `am_onyx`
(0,63 s)... Ces silences n'apportent rien a l'exemple donne au moteur : ils
allongent l'empreinte et diluent les codes ICL. Les rogner est MECANIQUE et ne
touche PAS a la voix : on ne coupe que du silence.

COMMENT : on garde `MARGE_S` (50 ms) de silence de chaque cote du premier et du
dernier echantillon ou l'on PARLE. La marge evite de mordre sur l'attaque d'un mot.

SECURITE : rapport seul par defaut. Avec `--ecrire`, chaque fichier modifie est
d'abord COPIE dans un dossier date (`voix/_bords_avant_<AAAAMMJJ_HHMM>/`), puis
le WAV est reecrit, puis **relu et remesure** (un rognage qui n'a pas marche est
signale).

CE QU'IL FAUT FAIRE APRES -- et c'est important :
  1. **redemarrer le moteur Qwen** : les empreintes des voix sont gardees EN
     MEMOIRE, elles ne verraient pas les fichiers rognes ;
  2. **monter VERSION_CACHE** (`modules/tts_cache.py`) : le cache audio contient
     des phrases generese avec les ANCIENNES references ; sans nouvelle version,
     le lecteur resservirait l'ancien rendu (c'est la regle du projet depuis le
     17/09/2026).

Usage :
    python test_voix/_rogner_bords_extraits.py            # rapport seul
    python test_voix/_rogner_bords_extraits.py --ecrire
"""
import shutil
import sys
import wave
from array import array
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "qwen_tts_service" / "voix"
SUFFIXES = ("_enhanced_reference.wav", "_reference.wav")

SEUIL_SILENCE = 0.005          # en dessous : silence (meme seuil que les autres outils)
SEUIL_DECLENCHEMENT_S = 0.20   # on ne rogne que si un bord depasse cette duree
MARGE_S = 0.05                 # silence GARDE de chaque cote (50 ms)

sys.stdout.reconfigure(encoding="utf-8")


def mesurer(chemin):
    """(frequence, echantillons, tete_s, queue_s) ou None si illisible."""
    try:
        with wave.open(str(chemin), "rb") as fichier:
            frequence = fichier.getframerate() or 1
            largeur = fichier.getsampwidth()
            canaux = fichier.getnchannels()
            brut = fichier.readframes(fichier.getnframes())
    except Exception as e:
        print("  (illisible : %s -- %s)" % (chemin.name, str(e)[:60]))
        return None
    if largeur != 2 or not brut:
        return None
    echantillons = array("h")
    echantillons.frombytes(brut[:len(brut) - (len(brut) % 2)])
    if canaux > 1:
        echantillons = echantillons[::canaux]
    seuil = int(SEUIL_SILENCE * 32768)
    premier = next((i for i, v in enumerate(echantillons) if abs(v) > seuil), None)
    if premier is None:
        return None                       # tout est silence : on n'y touche pas
    dernier = len(echantillons) - 1 - next(
        i for i, v in enumerate(reversed(echantillons)) if abs(v) > seuil)
    return (frequence, echantillons,
            premier / float(frequence),
            (len(echantillons) - 1 - dernier) / float(frequence))


def rogner(frequence, echantillons, tete_s, queue_s):
    """Garder MARGE_S de silence de chaque cote de la parole."""
    debut = max(0, int((tete_s - MARGE_S) * frequence))
    fin = min(len(echantillons),
              len(echantillons) - max(0, int((queue_s - MARGE_S) * frequence)))
    return echantillons[debut:fin]


def ecrire_wav(chemin, echantillons, frequence):
    with wave.open(str(chemin), "wb") as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(frequence)
        fichier.writeframes(echantillons.tobytes())


def bords_du_signal(frequence, echantillons):
    """(silence de tete, silence de queue) d'un signal rogne."""
    seuil = int(SEUIL_SILENCE * 32768)
    premier = next((i for i, v in enumerate(echantillons) if abs(v) > seuil), 0)
    dernier = len(echantillons) - 1 - next(
        (i for i, v in enumerate(reversed(echantillons)) if abs(v) > seuil), 0)
    return premier / float(frequence), (len(echantillons) - 1 - dernier) / float(frequence)


def main():
    ecrire = "--ecrire" in sys.argv
    horodatage = datetime.now().strftime("%Y%m%d_%H%M")
    sauvegardes = DOSSIER / ("_bords_avant_%s" % horodatage)

    print("")
    print("=" * 76)
    print(" ROGNAGE DES BORDS DES EXTRAITS DE REFERENCE (voix Qwen)")
    print("=" * 76)
    print(" dossier : %s" % DOSSIER.name)
    print(" regle   : silence de tete ou de queue > %.2f s -> on en garde %.2f s"
          % (SEUIL_DECLENCHEMENT_S, MARGE_S))
    print(" mode    : %s"
          % ("ECRITURE" if ecrire else "rapport seul (rien n'est modifie)"))
    print("")

    candidats = []
    total = 0
    for fichier in sorted(DOSSIER.glob("*.wav")):
        total += 1
        mesure = mesurer(fichier)
        if not mesure:
            continue
        frequence, echantillons, tete, queue = mesure
        if tete <= SEUIL_DECLENCHEMENT_S and queue <= SEUIL_DECLENCHEMENT_S:
            continue
        candidats.append((fichier, frequence, echantillons, tete, queue))

    print(" %d extraits lus, %d a rogner." % (total, len(candidats)))
    print("")
    print(" %-34s %8s %8s %8s %8s"
          % ("extrait", "tete av.", "queue av.", "tete ap.", "queue ap."))
    for fichier, frequence, echantillons, tete, queue in candidats:
        apres = rogner(frequence, echantillons, tete, queue)
        tete_apres, queue_apres = bords_du_signal(frequence, apres)
        print(" %-34s %7.2f s %7.2f s %7.2f s %7.2f s"
              % (fichier.name[:34], tete, queue, tete_apres, queue_apres))

    if not candidats:
        print("")
        print(" Rien a faire : tous les bords sont propres.")
        return 0

    if not ecrire:
        print("")
        print(" (rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        print(" A FAIRE ENSUITE si on ecrit : redemarrer le moteur Qwen, et monter")
        print(" VERSION_CACHE dans modules/tts_cache.py (le cache garde l'ancien rendu).")
        return 0

    sauvegardes.mkdir(parents=True, exist_ok=True)
    modifies = 0
    for fichier, frequence, echantillons, tete, queue in candidats:
        shutil.copy2(str(fichier), str(sauvegardes / fichier.name))
        ecrire_wav(fichier, rogner(frequence, echantillons, tete, queue), frequence)
        controle = mesurer(fichier)          # on RELIT ce qui vient d'etre ecrit
        if not controle:
            print("  ATTENTION : %s illisible apres ecriture" % fichier.name)
            continue
        _f, _e, tete_apres, queue_apres = controle
        if tete_apres > MARGE_S + 0.05 or queue_apres > MARGE_S + 0.05:
            print("  ATTENTION : %s garde un bord de %.2f/%.2f s"
                  % (fichier.name, tete_apres, queue_apres))
        else:
            modifies += 1

    print("")
    print(" extraits rognes ET controles : %d" % modifies)
    print(" copies d'origine : %s" % sauvegardes.name)
    print(" RETOUR ARRIERE : recopier ces fichiers dans %s" % DOSSIER.name)
    print("")
    print(" A FAIRE MAINTENANT : (1) redemarrer le moteur Qwen (ses empreintes sont")
    print(" en memoire) ; (2) monter VERSION_CACHE dans modules/tts_cache.py, sinon")
    print(" le lecteur resservirait l'ancien rendu pour les phrases deja en cache.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
