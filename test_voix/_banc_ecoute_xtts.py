# -*- coding: utf-8 -*-
"""Banc d'ecoute XTTS : les cas pieges du 15/09/2026, apres nos correctifs.

Item du BACKLOG « XTTS : defauts residuels entendus le 15/09/2026 » :
  (1) attaque du premier mot (« sourezet » pour « Vous etes sur ») et voix
      aigue en debut de phrase ;
  (2) respiration / inspiration en fin de phrase ;
  (3) mot mange dans une incise courte (« Il arriva [en]fin »), ou le nettoyage
      remplace le tiret cadratin par une virgule -- le tiret d'incise TEL QUEL
      n'a jamais ete ecoute.

Le moteur n'est pas parfaitement repetable (constat du BACKLOG) : ce banc
genere donc chaque cas avec DEUX voix, et mesure ce qui est mesurable
(duree, segments de parole, residu apres un silence).

Le moteur XTTS doit etre allume. Usage :
    python test_voix/_banc_ecoute_xtts.py
Sortie : test_voix/ecoute_xtts_<date>/ (WAV + index.txt + ECOUTER_LE_LOT.cmd)
"""

import datetime
import io
import json
import sys
import urllib.request
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

SERVICE = "http://127.0.0.1:8083"

# Deux voix contrastees : une aigue et vive, une grave et posee.
VOIX = [
    ("dp_femme003", "Yvette (aigue, vive)"),
    ("1406_1028_000009-0003", "Augustin (grave, pose)"),
]

# Les cas pieges, avec ce qu'on cherche a entendre.
CAS = [
    ("A_attaque", "« Vous êtes sûr ? »",
     "attaque du premier mot, apres retrait des guillemets"),
    ("B_incise", "Il arriva enfin, après trois jours de marche, au pied de la tour.",
     "mot mange dans une incise (le tiret devient une virgule)"),
    ("C_tiret_tete", "— Je ne sais pas, dit-il doucement.",
     "tiret cadratin en tete de replique"),
    ("D_tres_court", "Non.",
     "phrase ultra-courte : babil ?"),
    ("E_fin", "Elle le regarda longuement, puis détourna les yeux.",
     "respiration ou inspiration en fin de phrase"),
]

COUT_ATTAQUE_S = 0.30
CARACTERES_PAR_SECONDE = 20.0


def demander(texte, voix):
    corps = json.dumps({"texte": texte, "voix": voix}).encode('utf-8')
    requete = urllib.request.Request(
        SERVICE + "/tts", data=corps,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=300) as reponse:
        return reponse.read()


def mesurer(wav_bytes):
    """(duree, segments de parole, residu apres le dernier silence long)."""
    import array

    with wave.open(io.BytesIO(wav_bytes), "rb") as f:
        frequence = f.getframerate()
        brut = f.readframes(f.getnframes())
    echantillons = array.array('h')
    echantillons.frombytes(brut)
    duree = len(echantillons) / float(frequence)
    pas = max(1, int(0.02 * frequence))
    parles = []
    for debut in range(0, len(echantillons), pas):
        bloc = echantillons[debut:debut + pas]
        if bloc and max(abs(v) for v in bloc) / 32768.0 >= 0.012:
            parles.append((debut, debut + len(bloc)))
    segments = []
    for debut, fin in parles:
        if segments and debut - segments[-1][1] <= pas * 1.5:
            segments[-1] = (segments[-1][0], fin)
        else:
            segments.append((debut, fin))
    residu = 0.0
    for rang in range(len(segments) - 1, 0, -1):
        silence = (segments[rang][0] - segments[rang - 1][1]) / float(frequence)
        if silence >= 0.30:
            residu = (segments[-1][1] - segments[rang][0]) / float(frequence)
            break
    return (duree,
            [(a / float(frequence), b / float(frequence)) for a, b in segments],
            residu)


def main_banc():
    try:
        with urllib.request.urlopen(SERVICE + "/sante", timeout=5) as reponse:
            sante = json.loads(reponse.read().decode('utf-8'))
    except Exception as erreur:
        print("Le moteur XTTS ne repond pas sur %s (%s)." % (SERVICE, erreur))
        print("Double-clique sur xtts_service\\DEMARRER_XTTS.bat, puis relance.")
        return 1
    if not sante.get("pret"):
        print("Le moteur XTTS n'est pas encore pret (chargement en cours).")
        return 1

    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = Path(__file__).resolve().parent / ('ecoute_xtts_' + horodatage)
    dossier.mkdir(parents=True, exist_ok=True)

    print("Banc d'ecoute XTTS — dossier : %s" % dossier)
    print("=" * 74)
    lignes = ["BANC D'ECOUTE XTTS — %s"
              % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), '']

    for code, phrase, but in CAS:
        lignes.append('%s : « %s »' % (code, phrase))
        lignes.append('   ce qu on cherche : %s' % but)
        for voix, libelle in VOIX:
            try:
                wav = demander(phrase, voix)
            except Exception as erreur:
                print('%-13s %-24s ECHEC : %s' % (code, libelle, erreur))
                continue
            duree, segments, residu = mesurer(wav)
            nom = '%s_%s.wav' % (code, voix.replace(':', '_'))
            (dossier / nom).write_bytes(wav)
            attendue = COUT_ATTAQUE_S + len(phrase) / CARACTERES_PAR_SECONDE
            verdict = 'normal' if duree <= attendue * 1.5 + 0.6 else 'TROP LONG'
            print('%-13s %-24s %6.2fs (%s) | %d segment(s) | residu %.2f s'
                  % (code, libelle, duree, verdict, len(segments), residu))
            lignes.append('   %-24s -> %-34s [%.2f s, %d segment(s), '
                          'residu %.2f s]'
                          % (libelle, nom, duree, len(segments), residu))
        lignes.append('')

    lignes.append("A ECOUTER : ce qui est propre, et ce qui deraille.")
    lignes.append("Noter les codes qui derailent, puis voir le BACKLOG")
    lignes.append("(item « XTTS : defauts residuels entendus le 15/09/2026 »).")
    (dossier / 'index.txt').write_text('\n'.join(lignes), encoding='utf-8')

    # Un lanceur en double-clic, comme les lots d'ecoute de l'atelier.
    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    print('')
    print("Index : %s" % (dossier / 'index.txt'))
    print("Pour ecouter : double-clic sur ECOUTER_LE_LOT.cmd")
    return 0


if __name__ == '__main__':
    sys.exit(main_banc())
