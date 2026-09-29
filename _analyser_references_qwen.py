# -*- coding: utf-8 -*-
"""
Mesure LECTURE SEULE : les REFERENCES des voix Qwen.

Pourquoi (29/09/2026) : Laurent demande « est-ce qu'il ne vaudrait pas mieux
refaire toutes les voix proprement, avec les bords propres et une phrase bien
adaptee pour Kokoro ? ». Avant de repondre, on REGARDE :

  1. d'ou vient chaque texte de reference (colonne « source » de references.csv) :
     un texte ecrit par l'atelier NIMM Voix n'est pas un texte transcrit ;
  2. les BORDS : combien de silence en tete et en queue de chaque extrait.

Rien n'est modifie : on ne fait que lire des WAV et un CSV.
"""
import csv
import sys
import wave
from array import array
from pathlib import Path

RACINE = Path(__file__).resolve().parent
DOSSIER = RACINE / "qwen_tts_service" / "voix"
CSV = DOSSIER / "references.csv"
SUFFIXES = ("_enhanced_reference.wav", "_reference.wav")

SEUIL_SILENCE = 0.005      # en dessous : silence (meme ordre que les services)
BORD_SALE_S = 0.20         # au-dela : le bord est « sale », il y a a rogner

sys.stdout.reconfigure(encoding="utf-8")


def lire_references():
    """[{fichier, texte, duree, hauteur, source}] depuis references.csv."""
    lignes = []
    with open(CSV, "r", encoding="utf-8") as f:
        lecteur = csv.reader(f, delimiter=";")
        for rang, champs in enumerate(lecteur):
            if rang == 0 and champs and champs[0].lower() == "fichier":
                continue                      # en-tete
            if len(champs) < 2:
                continue
            lignes.append({
                "fichier": champs[0],
                "texte": champs[1],
                "duree": champs[2] if len(champs) > 2 else "",
                "hauteur": champs[3] if len(champs) > 3 else "",
                "source": champs[4] if len(champs) > 4 else "",
            })
    return lignes


def famille_source(source):
    """Un libelle court pour la provenance du texte."""
    s = (source or "").lower()
    if "kokoro (nimm)" in s:
        return "texte de l'atelier (Kokoro niMM)"
    if "accent allemand" in s:
        return "texte de l'atelier (Kokoro accent allemand)"
    return "texte NON atelier (transcrit)"


def mesurer_bords(chemin):
    """(duree, silence_tete, silence_queue, crete) d'un WAV, ou None."""
    try:
        with wave.open(str(chemin), "rb") as f:
            frequence = f.getframerate() or 1
            largeur = f.getsampwidth()
            canaux = f.getnchannels()
            brut = f.readframes(f.getnframes())
        duree = len(brut) / float(frequence * largeur * canaux)
        if largeur != 2 or not brut:
            return duree, None, None, None
        valeurs = array("h")
        valeurs.frombytes(brut[:len(brut) - (len(brut) % 2)])
        if canaux > 1:                        # on ne garde qu'un canal sur deux
            valeurs = valeurs[::canaux]
        maximum = max((abs(v) for v in valeurs), default=0)
        seuil = int(SEUIL_SILENCE * 32768)
        premier = next((i for i, v in enumerate(valeurs) if abs(v) > seuil), None)
        if premier is None:
            return duree, duree, duree, 0.0   # tout est silence
        dernier = len(valeurs) - 1 - next(
            i for i, v in enumerate(reversed(valeurs)) if abs(v) > seuil)
        return (duree, premier / float(frequence),
                (len(valeurs) - 1 - dernier) / float(frequence),
                maximum / 32768.0)
    except Exception as e:
        print("  (illisible : %s -- %s)" % (chemin.name, e))
        return None


def main():
    references = lire_references()
    print("references.csv : %d lignes" % len(references))
    print("")

    groupes = {}
    for r in references:
        groupes.setdefault(famille_source(r["source"]), []).append(r)
    print("Provenance du TEXTE de reference :")
    for nom, lignes in sorted(groupes.items(), key=lambda x: -len(x[1])):
        distincts = len({l["texte"] for l in lignes})
        print("  %-44s %3d voix   (%d texte(s) distinct(s))"
              % (nom, len(lignes), distincts))
        exemple = lignes[0]["texte"]
        print("      ex. : %s" % (exemple[:96] or "(vide)"))
    print("")

    print("Bords des extraits (silence < %.3f, bord « sale » > %.2f s) :"
          % (SEUIL_SILENCE, BORD_SALE_S))
    par_famille = {}
    sales = []
    total = 0
    for fichier in sorted(DOSSIER.glob("*.wav")):
        nom = fichier.name
        court = nom
        for suffixe in SUFFIXES:
            if nom.endswith(suffixe):
                court = nom[:-len(suffixe)]
                break
        mesure = mesurer_bords(fichier)
        total += 1
        if not mesure:
            continue
        duree, tete, queue, _crete = mesure
        famille = ("enhanced" if nom.endswith("_enhanced_reference.wav")
                   else "reference")
        infos = par_famille.setdefault(famille, {"n": 0, "tete": [], "queue": []})
        infos["n"] += 1
        if tete is not None:
            infos["tete"].append(tete)
            infos["queue"].append(queue)
            if tete > BORD_SALE_S or queue > BORD_SALE_S:
                sales.append((court, tete, queue, duree))

    for famille, infos in sorted(par_famille.items()):
        tetes = infos["tete"]
        queues = infos["queue"]
        if not tetes:
            continue
        print("  %-10s %3d extraits : silence de tete %.3f s en moyenne "
              "(max %.2f) ; queue %.3f s (max %.2f)"
              % (famille, infos["n"], sum(tetes) / len(tetes), max(tetes),
                 sum(queues) / len(queues), max(queues)))
    print("")
    print("  extraits avec un bord « sale » (> %.2f s) : %d sur %d"
          % (BORD_SALE_S, len(sales), total))
    for nom, tete, queue, duree in sorted(sales,
                                          key=lambda x: -max(x[1], x[2]))[:15]:
        print("      %-34s tete %.2f s  queue %.2f s  (duree %.2f s)"
              % (nom[:34], tete, queue, duree))
    if len(sales) > 15:
        print("      ... et %d autre(s)" % (len(sales) - 15))
    print("")
    print("Rien n'a ete modifie.")


if __name__ == "__main__":
    main()
