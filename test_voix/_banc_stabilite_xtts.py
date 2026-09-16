# -*- coding: utf-8 -*-
"""XTTS est-il STABLE ? Comparaison de trois reglages de generation.

Constat de Laurent (16/09/2026) : XTTS est tres INEGAL -- « 3 phrases
excellentes, puis il hachure, bafouille, traine, monte dans les aigus » --
alors que Kokoro redit la meme phrase 50 fois de la meme facon.
Cause : XTTS ECHANTILLONNE (temperature 0,75 par defaut) ; Kokoro, non.

Ce banc genere LA MEME PHRASE plusieurs fois avec trois reglages :
    defaut    : rien -- le comportement actuel du lecteur ;
    sage      : temperature 0,60 ;
    tres_sage : temperature 0,45.
Il mesure la STABILITE : ecart entre la duree la plus courte et la plus longue,
et nombre de segments de parole (le « hachurage »).

Le service XTTS doit etre allume ET A JOUR : le parametre « reglages » a ete
ajoute au service le 16/09/2026, donc il faut le REDEMARRER (DEMARRER_XTTS.bat)
avant ce test -- sinon les trois series seront identiques.

Usage : python test_voix/_banc_stabilite_xtts.py
Sortie : test_voix/stabilite_xtts_<date>/ (WAV + index.txt + ECOUTER_LE_LOT.cmd)
"""

import datetime
import json
import sys
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.stdout.reconfigure(encoding='utf-8')

from _banc_ecoute_xtts import demander, mesurer, SERVICE      # noqa: E402

PHRASE = "Il arriva enfin, après trois jours de marche, au pied de la tour."
VOIX = "dp_femme003"
REPETITIONS = 5
REGLAGES = [
    ("defaut", {}, "rien : le comportement actuel"),
    ("sage", {"temperature": 0.60}, "temperature 0,60"),
    ("tres_sage", {"temperature": 0.45}, "temperature 0,45"),
]


def demander_avec_reglages(texte, voix, reglages):
    """Comme demander(), mais avec les reglages de generation."""
    corps = json.dumps({"texte": texte, "voix": voix,
                        "reglages": reglages}).encode('utf-8')
    requete = urllib.request.Request(
        SERVICE + "/tts", data=corps,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=300) as reponse:
        return reponse.read()


def main_banc():
    try:
        with urllib.request.urlopen(SERVICE + "/sante", timeout=5) as reponse:
            sante = json.loads(reponse.read().decode('utf-8'))
        if not sante.get("pret"):
            print("Le moteur XTTS n'est pas encore pret (chargement en cours).")
            return 1
    except Exception as erreur:
        print("Le moteur XTTS ne repond pas sur %s (%s)." % (SERVICE, erreur))
        print("Double-clique sur xtts_service\\DEMARRER_XTTS.bat, puis relance.")
        return 1

    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = ICI / ('stabilite_xtts_' + horodatage)
    dossier.mkdir(parents=True, exist_ok=True)

    print("STABILITE D'XTTS — meme phrase, %d tirages par reglage" % REPETITIONS)
    print("phrase : « %s »" % PHRASE)
    print("dossier : %s" % dossier)
    print("=" * 78)

    lignes = ["STABILITE D'XTTS — %s"
              % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), '',
              "La MEME phrase, %d fois, avec trois reglages du moteur."
              % REPETITIONS,
              "But : une generation STABLE redit toujours la meme chose.",
              "Ecouter si les series « sage » et « tres_sage » sont plus",
              "regulieres que la serie « defaut ».", '',
              "phrase : « %s »" % PHRASE, '']
    bilans = []

    for nom, reglages, libelle in REGLAGES:
        print('')
        print('--- %s (%s)' % (nom, libelle))
        durees = []
        segments = []
        for rang in range(1, REPETITIONS + 1):
            try:
                wav = demander_avec_reglages(PHRASE, VOIX, reglages)
            except Exception as erreur:
                print('  %02d ECHEC : %s' % (rang, erreur))
                continue
            duree, morceaux, _residu = mesurer(wav)
            fichier = '%s_%02d.wav' % (nom, rang)
            (dossier / fichier).write_bytes(wav)
            durees.append(duree)
            segments.append(len(morceaux))
            print('  %s  %5.2f s | %d segment(s)' % (fichier, duree, len(morceaux)))
        if durees:
            ecart = max(durees) - min(durees)
            moyenne = sum(durees) / len(durees)
            bilans.append((nom, moyenne, ecart, sum(segments) / len(segments)))
            lignes.append('%s (%s) : duree %.2f s en moyenne, ECART %.2f s, '
                          '%.1f segment(s) en moyenne'
                          % (nom, libelle, moyenne, ecart,
                             sum(segments) / len(segments)))
            lignes.append('   fichiers : %s_01.wav a %s_%02d.wav'
                          % (nom, nom, len(durees)))
            lignes.append('')

    print('')
    print('BILAN (moins l ecart est grand, plus le moteur est STABLE) :')
    print('%-12s %10s %10s %12s' % ('reglage', 'duree moy', 'ECART', 'segments'))
    print('-' * 50)
    for nom, moyenne, ecart, seg in bilans:
        print('%-12s %9.2f s %9.2f s %11.1f' % (nom, moyenne, ecart, seg))

    lignes.append("BILAN (un ECART faible = un moteur stable) :")
    for nom, moyenne, ecart, seg in bilans:
        lignes.append('   %-10s duree moyenne %.2f s | ecart %.2f s | '
                      'segments %.1f' % (nom, moyenne, ecart, seg))
    lignes.append('')
    lignes.append("Verdict attendu : si « sage » ou « tres_sage » a un ecart")
    lignes.append("nettement plus faible ET une parole non hachee, on adopte ce")
    lignes.append("reglage par defaut dans le service (le lecteur n'aura rien a")
    lignes.append("changer).")

    (dossier / 'index.txt').write_text('\n'.join(lignes), encoding='utf-8')
    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    print('')
    print("A ecouter : double-clic sur %s" % (dossier / 'ECOUTER_LE_LOT.cmd'))
    return 0


if __name__ == '__main__':
    sys.exit(main_banc())
