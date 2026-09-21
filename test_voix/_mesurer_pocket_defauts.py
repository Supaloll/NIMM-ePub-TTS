# -*- coding: utf-8 -*-
"""MESURE des DEUX DEFAUTS Pocket TTS (retour d'ecoute de Laurent, 21/09/2026) :

  1. « il a tendance a DIMINUER LE VOLUME si le paragraphe est tres long » ;
  2. « et a MANGER LES DEBUTS DE MOTS en debut de phrase ».

Ce que fait l'outil, sur un VRAI texte d'un livre (long, comme un paragraphe) :
  - il demande l'audio au service Pocket TTS, tel quel (aucune retouche du
    lecteur : on mesure le moteur) ;
  - il decoupe la parole en fenetres de 2 s et suit le NIVEAU DE PAROLE : si la
    derniere fenetre est nettement sous la premiere, le volume s'affaisse
    (mesure en dB, et en dB par minute) ;
  - il repere chaque debut de phrase (une reprise apres un silence d'au moins
    0,15 s) et compare l'ATTaque (les 50 premiers millisecondes audibles) au
    niveau habituel de la phrase : une attaque tres faible = un debut de mot
    mange ;
  - il refait la meme chose avec **Kyutai** sur le meme texte, comme TEMOIN :
    si les deux se comportent pareil, ce n'est pas Pocket.

Le moteur doit etre allume. LECTURE SEULE (rien n'est ecrit dans la base).

Usage : python test_voix/_mesurer_pocket_defauts.py
"""

import io
import json
import math
import sys
import urllib.request
import wave
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
sys.path.insert(0, str(RACINE))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SORTIE = DOSSIER / "_mesurer_pocket_defauts.txt"
POCKET = "http://127.0.0.1:8085/tts"
KYUTAI = "http://127.0.0.1:8082/tts"
VOIX_KYUTAI = "2114_1656_000053-0001"

SEUIL_PAROLE = 0.02 * 32768.0     # « ca parle » (meme seuil que le lecteur)
FENETRE_S = 0.030                 # fenetre d'analyse du niveau
TRANCHE_S = 2.0                   # fenetre de suivi du volume
SILENCE_PHRASE_S = 0.15           # au-dela : on considere une nouvelle phrase
ATTAQUE_MS = 50                   # ce qu'on regarde au debut d'une phrase


def demander(url, texte, voix):
    corps = json.dumps({"texte": texte, "voix": voix}).encode("utf-8")
    requete = urllib.request.Request(
        url, data=corps, headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(requete, timeout=600) as reponse:
        return reponse.read()


def lire_wav(octets):
    """(frequence, echantillons int16) d'un WAV en memoire."""
    import array
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        frequence = fichier.getframerate()
        echantillons = array.array("h")
        echantillons.frombytes(fichier.readframes(fichier.getnframes()))
    return frequence, echantillons


def niveau_parole_par_tranche(frequence, echantillons):
    """[(debut_s, niveau)] : niveau de PAROLE (creux median des fenetres qui
    parlent) par tranche de TRANCHE_S secondes."""
    pas = max(1, int(FENETRE_S * frequence))
    tranche = max(1, int(TRANCHE_S * frequence))
    resultat = []
    for debut in range(0, len(echantillons), tranche):
        morceau = echantillons[debut:debut + tranche]
        niveaux = []
        for position in range(0, len(morceau), pas):
            bloc = morceau[position:position + pas]
            if bloc and max(abs(v) for v in bloc) > SEUIL_PAROLE:
                niveaux.append(max(abs(v) for v in bloc))
        if niveaux:
            niveaux.sort()
            median = niveaux[len(niveaux) // 2]
            resultat.append((debut / float(frequence),
                             median / 32768.0 * 100.0))
    return resultat


def dB(valeur, reference):
    if valeur <= 0 or reference <= 0:
        return 0.0
    return 20.0 * math.log10(valeur / reference)


def attaques(frequence, echantillons):
    """[(debut_s, niveau d'attaque, niveau habituel)] : un point par PHRASE.

    Une phrase commence apres un silence d'au moins SILENCE_PHRASE_S ; on mesure
    alors les ATTAQUE_MS premieres millisecondes audibles, et on les compare au
    niveau habituel de la phrase (ses fenetres de parole).
    """
    pas = max(1, int(FENETRE_S * frequence))
    cadre = max(1, int(ATTAQUE_MS / 1000.0 * frequence))
    blocs = []
    for debut in range(0, len(echantillons), pas):
        bloc = echantillons[debut:debut + pas]
        if bloc and max(abs(v) for v in bloc) > SEUIL_PAROLE:
            if blocs and debut - blocs[-1][1] <= int(SILENCE_PHRASE_S * frequence):
                blocs[-1] = (blocs[-1][0], debut + len(bloc))
            else:
                blocs.append((debut, debut + len(bloc)))
    resultat = []
    for rang, (debut, fin) in enumerate(blocs):
        # On ecarte le tout premier bloc : c'est le debut du FICHIER, pas une
        # reprise de phrase (tout le monde y est plus faible).
        if rang == 0:
            continue
        morceau = echantillons[debut:debut + cadre]
        if not morceau:
            continue
        crete = max(abs(v) for v in morceau) / 32768.0 * 100.0
        niveaux = []
        for position in range(debut, fin, pas):
            bloc = echantillons[position:position + pas]
            if bloc:
                niveaux.append(max(abs(v) for v in bloc))
        if not niveaux:
            continue
        niveaux.sort()
        habituel = niveaux[len(niveaux) // 2] / 32768.0 * 100.0
        resultat.append((debut / float(frequence), crete, habituel))
    return resultat


def texte_de_livre(livre=28, chapitre=10, minimum=600):
    """Le plus long paragraphe d'un chapitre (un vrai texte a lire tout haut)."""
    import sqlite3
    from core import epub_parser

    connexion = sqlite3.connect(
        "file:%s?mode=ro" % (RACINE / "data" / "nimm_epub.db").as_posix(),
        uri=True)
    ligne = connexion.execute("SELECT filename, title FROM books WHERE id=?",
                              (livre,)).fetchone()
    connexion.close()
    if not ligne:
        return "", ""
    chemin = None
    for essai in (Path(ligne[0]), RACINE / "data" / "library" / ligne[0]):
        if essai.is_file():
            chemin = essai
            break
    if chemin is None:
        return "", ""
    chapitres = epub_parser.get_chapters(str(chemin))
    if not 0 <= chapitre < len(chapitres):
        return "", ""
    paragraphes = [p.strip() for p in
                   (chapitres[chapitre].get("text") or "").split("\n\n")]
    candidats = [p for p in paragraphes if minimum <= len(p) <= 1200]
    if not candidats:
        return "", ligne[1]
    return max(candidats, key=len), ligne[1]


def phrases_du_paragraphe(texte):
    """Les phrases du paragraphe, coupees comme le fait le lecteur."""
    from modules import decoupage
    return [p for p in decoupage.phrases(texte) if len(p) > 8]


def analyser_phrase_par_phrase(nom, url, voix, phrases):
    """Comme la lecture REELLE : une requete par phrase (jamais le paragraphe).

    On releve, pour chaque phrase : son NIVEAU de parole et son ATTAQUE (les 50
    premieres millisecondes rapportees au niveau habituel de la phrase). Puis on
    regarde si le niveau DERIVE au fil du paragraphe (c'est la plainte de
    Laurent : « il diminue le volume si le paragraphe est tres long »).
    """
    niveaux = []
    niveaux_module = []
    attaques_mesurees = []
    from modules import audio_gain
    for phrase in phrases:
        octets = demander(url, phrase, voix)
        frequence, echantillons = lire_wav(octets)
        if not echantillons:
            continue
        tranches = niveau_parole_par_tranche(frequence, echantillons)
        if tranches:
            niveaux.append(max(valeur for _, valeur in tranches))
        # Le niveau tel que le MODULE du lecteur le mesure (moyenne par fenetre
        # de 30 ms, et non crete) : c'est celui qui sert a regler le volume, donc
        # c'est lui qui calibre la cible.
        canaux, largeur, frequence_wav, ech = audio_gain._lire_wav(octets)
        mesure = audio_gain._niveau_parole(ech, frequence_wav)
        if mesure:
            niveaux_module.append(mesure)
        debuts = attaques(frequence, echantillons)
        if debuts:
            debut, crete, habituel = debuts[0]
            attaques_mesurees.append((phrase[:28], crete, habituel))

    lignes = ["%s : %d phrase(s) demandee(s) une par une" % (nom, len(phrases))]
    if niveaux_module:
        tries = sorted(niveaux_module)
        median_module = tries[len(tries) // 2]
        lignes.append("   0) NIVEAU DU MODULE (celui qui regle le volume) : %s"
                      % " ".join("%.1f" % n for n in niveaux_module))
        lignes.append("      median %.1f %%  |  du plus bas %.1f %% au plus haut "
                      "%.1f %%  (ecart %.1f dB)"
                      % (median_module, min(niveaux_module),
                         max(niveaux_module),
                         dB(max(niveaux_module), min(niveaux_module))))
    if niveaux:
        premier, dernier = niveaux[0], niveaux[-1]
        lignes.append("   1) VOLUME par phrase : %s"
                      % " ".join("%.0f" % n for n in niveaux))
        lignes.append("      premiere %.1f %%  derniere %.1f %%  (%+.1f dB)"
                      "  |  plus bas %.1f %%  |  le plus haut %.1f %%"
                      % (premier, dernier, dB(dernier, premier),
                         min(niveaux), max(niveaux)))
    if attaques_mesurees:
        faibles = [a for a in attaques_mesurees if dB(a[1], a[2]) < -6.0]
        lignes.append("   2) ATTAQUES : %d mesure(s), %d sous -6 dB"
                      % (len(attaques_mesurees), len(faibles)))
        for extrait, crete, habituel in attaques_mesurees:
            if dB(crete, habituel) < -6.0:
                lignes.append("      « %s... » : attaque %.1f %% / habituel "
                              "%.1f %%  (%+.1f dB)"
                              % (extrait, crete, habituel,
                                 dB(crete, habituel)))
    return lignes


def main():
    texte, titre = texte_de_livre()
    if not texte:
        print("Texte introuvable : verifiez la base.")
        return 1

    with urllib.request.urlopen("http://127.0.0.1:8085/voix", timeout=10) as r:
        voix_pocket = (json.loads(r.read().decode("utf-8")).get("voix") or [""])[0]

    lignes = ["MESURE DES DEUX DEFAUTS Pocket TTS (21/09/2026)",
              "texte : %d caracteres, livre %s" % (len(texte), titre or "?"),
              "voix Pocket : %s   |   voix temoin Kyutai : %s"
              % (voix_pocket, VOIX_KYUTAI),
              "Le niveau est celui de la PAROLE (fenetres de 30 ms ou l'on parle).",
              "L'attaque est comparee au niveau habituel de la MEME phrase.",
              ""]

    phrases = phrases_du_paragraphe(texte)
    print("Pocket TTS (%d phrase(s) du grand paragraphe)..." % len(phrases))
    lignes += analyser_phrase_par_phrase("POCKET TTS", POCKET, voix_pocket,
                                         phrases)
    lignes.append("")
    print("Kyutai (temoin)...")
    lignes += analyser_phrase_par_phrase("KYUTAI (temoin)", KYUTAI,
                                         VOIX_KYUTAI, phrases)
    lignes.append("")
    lignes.append("A LIRE : un ecart de volume negatif marque une baisse ; une")
    lignes.append("attaque a plus de -6 dB sous le niveau habituel est une")
    lignes.append("attaque ecrasee (debut de mot mange).")

    SORTIE.write_text("\n".join(lignes), encoding="utf-8")
    print("")
    print("\n".join(lignes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
