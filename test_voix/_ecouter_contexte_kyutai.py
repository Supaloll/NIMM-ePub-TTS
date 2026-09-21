# -*- coding: utf-8 -*-
"""LOT D'ECOUTE du CONTEXTE GLISSANT (Kyutai) -- 21/09/2026.

Ce qu'on ecoute, pour des phrases REELLES d'un livre : la MEME phrase, trois
fois, en passant par le VRAI mecanisme de lecture (le service Kyutai, avec sa
coupe) :

    01_seule.wav    la phrase SEULE, sans contexte
    02_3mots.wav    avec les 3 DERNIERS MOTS de la phrase precedente
                    (le reglage d'aujourd'hui, apres la mesure du 21/09)
    03_8mots.wav    avec les 8 derniers mots (le reglage d'avant)

Pourquoi ces trois-la : le contexte sert a ce que la voix ne demarre plus « a
froid » -- mais il est COUPE par le service, et quand la coupe tombe trop tot,
la fin du contexte reste et s'entend (« Je ne pense pas. Pense pas Mais tu as
peut etre raison »). La mesure du 21/09/2026 dit que 8 mots laissent un residu
dans 4 cas sur 6, et 3 mots dans aucun : ce lot est la pour l'OREILLE de
Laurent, avec de vraies phrases de ses livres.

Le moteur Kyutai doit etre allume. La sortie va dans
`test_voix/ecoute_contexte_<date>/` (index.txt + lanceur de double-clic).

Usage : python test_voix/_ecouter_contexte_kyutai.py --livre 28 --chapitre 10
"""

import argparse
import datetime
import io
import json
import sqlite3
import sys
import urllib.request
import wave
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
sys.path.insert(0, str(RACINE))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core import epub_parser                                      # noqa: E402
from modules import decoupage                                     # noqa: E402

BASE = RACINE / "data" / "nimm_epub.db"
SERVICE = "http://127.0.0.1:8082/tts"
VOIX_DEFAUT = "2114_1656_000053-0001"          # Claude (Monte-Cristo T2)
COUPLES = 4                                    # combien de phrases a ecouter
LONGUEUR_MINI = 25                             # on ecarte les phrases trop courtes


def demander(texte, voix, contexte=""):
    corps = {"texte": texte, "voix": voix}
    if contexte:
        corps["contexte"] = contexte
    requete = urllib.request.Request(
        SERVICE, data=json.dumps(corps).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=300) as reponse:
        return reponse.read()


def duree(octets):
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        return fichier.getnframes() / float(fichier.getframerate())


def derniers_mots(texte, nombre):
    mots = texte.split()
    return " ".join(mots[-nombre:]) if mots else texte


def couples_a_ecouter(texte, combien):
    """[(phrase precedente, phrase a lire)] : des phrases REELLES, entieres."""
    phrases = decoupage.phrases(texte)
    couples = []
    for indice in range(1, len(phrases)):
        precedente, phrase = phrases[indice - 1], phrases[indice]
        if len(precedente) < LONGUEUR_MINI or len(phrase) < LONGUEUR_MINI:
            continue
        if phrase[:1] in ("-", "\u2014", "\u00ab"):
            continue                    # on garde de la narration, pas du dialogue
        couples.append((precedente, phrase))
        if len(couples) >= combien:
            break
    return couples


def chemin_de_livre(livre):
    connexion = sqlite3.connect("file:%s?mode=ro" % BASE.as_posix(), uri=True)
    ligne = connexion.execute("SELECT filename FROM books WHERE id=?",
                              (livre,)).fetchone()
    connexion.close()
    if not ligne or not ligne[0]:
        return None
    for essai in (Path(ligne[0]), RACINE / "data" / "library" / ligne[0]):
        if essai.is_file():
            return essai
    return None


def ecrire_le_lanceur(dossier):
    lanceur = dossier / "OUVRIR_LE_DOSSIER.cmd"
    lanceur.write_text(
        '@echo off\r\n'
        'chcp 65001 >nul\r\n'
        'title NIMM ePub - ecouter le contexte (Kyutai)\r\n'
        'echo.\r\n'
        'echo   Trois fichiers par phrase, a ecouter dans cet ordre :\r\n'
        'echo.\r\n'
        'echo     01_seule.wav   la phrase SEULE\r\n'
        'echo     02_3mots.wav   avec 3 mots de contexte  (aujourd hui)\r\n'
        'echo     03_8mots.wav   avec 8 mots de contexte  (avant)\r\n'
        'echo.\r\n'
        'echo   Ce qu on ecoute : 1. les premiers mots partent-ils bien\r\n'
        'echo   (pas de voix « a froid ») ? 2. entend-on la FIN de la\r\n'
        'echo   phrase precedente avant celle-ci (le defaut) ?\r\n'
        'echo.\r\n'
        'start "" "%%~dp0."\r\n'
        'pause\r\n', encoding="utf-8", newline="")
    return lanceur


def main():
    analyseur = argparse.ArgumentParser(
        description="Lot d'ecoute du contexte glissant de Kyutai.")
    analyseur.add_argument("--livre", type=int, required=True)
    analyseur.add_argument("--chapitre", type=int, required=True)
    analyseur.add_argument("--voix", default=VOIX_DEFAUT)
    options = analyseur.parse_args()

    chemin = chemin_de_livre(options.livre)
    if chemin is None:
        print("Livre %s introuvable dans la bibliotheque." % options.livre)
        return 1
    chapitres = epub_parser.get_chapters(str(chemin))
    if not 0 <= options.chapitre < len(chapitres):
        print("Chapitre %s hors bornes." % options.chapitre)
        return 1
    couples = couples_a_ecouter(chapitres[options.chapitre].get("text") or "",
                                COUPLES)
    if not couples:
        print("Aucune phrase exploitable dans ce chapitre.")
        return 1

    dossier = DOSSIER / ("ecoute_contexte_%s"
                         % datetime.datetime.now().strftime("%Y%m%d_%H%M"))
    dossier.mkdir(exist_ok=True)
    lignes = ["LOT D'ECOUTE DU CONTEXTE GLISSANT (Kyutai)",
              "livre %s, chapitre %s, voix %s"
              % (options.livre, options.chapitre, options.voix),
              ""]

    numero = 0
    for precedente, phrase in couples:
        numero += 1
        lignes.append("phrase %d : %r" % (numero, phrase[:70]))
        lignes.append("   precedee de : %r" % precedente[:70])
        for etiquette, contexte in (("seule", ""),
                                    ("3mots", derniers_mots(precedente, 3)),
                                    ("8mots", derniers_mots(precedente, 8))):
            octets = demander(phrase, options.voix, contexte)
            nom = "%02d_%s.wav" % (numero, etiquette)
            (dossier / nom).write_bytes(octets)
            lignes.append("   %-16s %6.2f s" % (nom, duree(octets)))
        lignes.append("")

    lignes.append("A ecouter : 01, 02, 03 puis la phrase suivante...")
    lignes.append("Question 1 : les premiers mots partent-ils bien (voix « a")
    lignes.append("             froid » quand il n'y a pas de contexte) ?")
    lignes.append("Question 2 : la FIN de la phrase precedente s'entend-elle")
    lignes.append("             avant celle-ci (le defaut a chasser) ?")
    (dossier / "index.txt").write_text("\n".join(lignes), encoding="utf-8")
    ecrire_le_lanceur(dossier)

    print("\n".join(lignes))
    print("")
    print("Dossier : %s" % dossier)
    print("Double-clic : OUVRIR_LE_DOSSIER.cmd (dans ce dossier)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
