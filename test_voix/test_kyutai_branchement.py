# -*- coding: utf-8 -*-
"""Verification du branchement du moteur Kyutai dans le lecteur.

A lancer avec le Python du LECTEUR (3.14), moteur Kyutai allume :
    python test_voix/test_kyutai_branchement.py

Ce que le script verifie, sans passer par le navigateur :
  1. le catalogue des 35 voix Kyutai est bien expose ;
  2. une phrase se synthetise et donne un WAV valide (24 kHz mono) ;
  3. la vitesse (-20 %) et la hauteur (+20 Hz) sont bien appliquees ;
  4. le cache disque evite de redemander la phrase au moteur ;
  5. si le moteur est eteint, une erreur KyutaiIndisponible est levee
     (c'est ce que /api/tts transforme en 503 + message clair).
"""

import asyncio
import io
import os
import sys
import time
import wave
from pathlib import Path

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

from modules import tts  # noqa: E402

PHRASE = ("Le 24 février 1815, la vigie de Notre-Dame de la Garde signala "
          "le trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples.")
DOSSIER = os.path.join(RACINE, "test_voix")


def infos(octets):
    with wave.open(io.BytesIO(octets), "rb") as f:
        return f.getnframes() / float(f.getframerate()), f.getframerate()


def hauteur(octets):
    """F0 median (Hz) par autocorrelation -- meme methode que l'atelier."""
    try:
        import numpy as np
    except ImportError:
        return None
    with wave.open(io.BytesIO(octets), "rb") as f:
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


async def main():
    print("1) catalogue")
    print("   voix Kyutai : %d" % len(tts.KYUTAI_VOICES))
    identifiants = [v["id"] for v in tts.KYUTAI_VOICES]
    noms = [v["name"] for v in tts.KYUTAI_VOICES]
    assert len(identifiants) == 35, "le catalogue ne fait pas 35 voix"
    assert len(identifiants) == len(set(identifiants)), "identifiants en double"
    assert len(noms) == len(set(noms)), "noms en double"
    assert all(i.startswith("kyutai:") for i in identifiants), "prefixe manquant"
    # L'ordre doit suivre le tri des identifiants (regle du catalogue : le
    # numero affiche « Kyutai NN » correspond au fichier NN de l'ecoute).
    attendu = ["kyutai:" + i for i in
               sorted(i.split(":", 1)[1] for i in identifiants)]
    assert identifiants == attendu, "l'ordre du catalogue ne suit pas les fichiers"
    # Chaque voix du catalogue doit exister reellement dans le service.
    dossier = Path(RACINE) / "kyutai_service" / "voix_fr" / "cml-tts" / "fr"
    presentes = {f.name.split("_enhanced.wav")[0] for f in dossier.glob("*.safetensors")}
    manquantes = [i for i in identifiants if i.split(":", 1)[1] not in presentes]
    assert not manquantes, "voix absentes du service : %s" % manquantes
    print("   ordre conforme aux fichiers, %d voix presentes dans le service"
          % len(presentes))
    # Etiquettes d'ecoute : chaque voix doit avoir un genre et une note.
    par_genre = {}
    par_notes = {}
    for v in tts.KYUTAI_VOICES:
        par_genre[v["gender"]] = par_genre.get(v["gender"], 0) + 1
        par_notes[v["stars"]] = par_notes.get(v["stars"], 0) + 1
    assert all(g in ("F", "M") for g in par_genre), \
        "genre manquant ou inattendu (F = femme, M = masculin) : %s" % par_genre
    print("   genres : %s   etoiles : %s" % (par_genre, par_notes))
    voix = tts.KYUTAI_VOICES[1]["id"]
    print("   voix testee : %s (%s)" % (voix, tts.KYUTAI_VOICES[1]["name"]))

    print("2) synthese normale")
    t0 = time.time()
    audio = await tts.synthesize_kyutai(PHRASE, voix)
    duree, frequence = infos(audio)
    print("   %.1f s d'audio, %d Hz, %d octets, calcul %.1f s"
          % (duree, frequence, len(audio), time.time() - t0))
    assert frequence == 24000, "frequence inattendue"
    chemin = os.path.join(DOSSIER, "kyutai_branchement_normal.wav")
    with open(chemin, "wb") as f:
        f.write(audio)

    print("3) vitesse et hauteur")
    t0 = time.time()
    lent = await tts.synthesize_kyutai(PHRASE, voix, rate="-20%")
    duree_lente, _ = infos(lent)
    print("   vitesse -20 %% : %.1f s (calcul %.1f s)" % (duree_lente, time.time() - t0))
    assert duree_lente > duree * 1.10, "la vitesse n'a pas ete appliquee"
    with open(os.path.join(DOSSIER, "kyutai_branchement_vitesse.wav"), "wb") as f:
        f.write(lent)

    t0 = time.time()
    aigu = await tts.synthesize_kyutai(PHRASE, voix, pitch="+20Hz")
    duree_aigue, _ = infos(aigu)
    f0_normal, f0_aigu = hauteur(audio), hauteur(aigu)
    print("   hauteur +20 Hz : %.1f s, F0 %.0f Hz -> %.0f Hz (calcul %.1f s)"
          % (duree_aigue, f0_normal or 0, f0_aigu or 0, time.time() - t0))
    if f0_normal and f0_aigu:
        assert f0_aigu > f0_normal + 10, "la hauteur n'a pas ete appliquee"
    with open(os.path.join(DOSSIER, "kyutai_branchement_hauteur.wav"), "wb") as f:
        f.write(aigu)

    print("4) cache disque")
    t0 = time.time()
    encore = await tts.synthesize_kyutai(PHRASE, voix)
    print("   deuxieme appel : %.3f s, %d octets (identique : %s)"
          % (time.time() - t0, len(encore), encore == audio))
    assert encore == audio, "le cache n'a pas rendu le meme audio"

    print("5) moteur eteint -> erreur claire")
    ancienne = tts.KYUTAI_URL
    tts.KYUTAI_URL = "http://127.0.0.1:8099"   # port mort : personne n'ecoute
    try:
        await tts.synthesize_kyutai("Phrase de controle.", voix)
        print("   ECHEC : aucune erreur levee")
        return 1
    except tts.KyutaiIndisponible as erreur:
        print("   OK, message : %s" % erreur)
    finally:
        tts.KYUTAI_URL = ancienne

    print("")
    print("TOUT EST OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
