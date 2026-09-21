# -*- coding: utf-8 -*-
"""MESURE DU CONTEXTE GLISSANT de Kyutai, selon le NOMBRE DE MOTS ENVOYES.

Ecrit le 21/09/2026, pour trancher une question de Laurent : « peut-etre envoyer
moins de contexte glissant, par exemple 3 mots au lieu de 8 ? Et j'ai
l'impression que c'est plus recurrent quand il y a de la ponctuation comme des ;
ou des « ou des ... »

CE QU'ON CHERCHE : Laurent entend, de temps en temps, les derniers mots de la
phrase PRECEDENTE avant la phrase courante (« Je ne pense pas. Pense pas Mais tu
as peut etre raison »), et parfois un debut de phrase mange.

LA MECANIQUE, pour lire les chiffres : le service **ne sait pas** lire le
contexte « sans le dire ». Il genere « contexte + phrase » d'un seul tenant, puis
**coupe** l'audio dans un silence pour ne livrer que la phrase. Trop tot ->
la fin du contexte reste et s'entend ; trop tard -> le debut de la phrase part.

COMMENT ON MESURE : on demande au moteur, comme le lecteur le fait, et on mesure
la duree de PAROLE SEULE (les blocs ou l'on parle, sans les silences) :
  - PLUS de parole que la phrase seule  -> un morceau du contexte est reste ;
  - MOINS de parole                     -> c'est la phrase qui a ete rognee.
L'ecart en parole est un bien meilleur signal que la duree totale, qui bouge
avec les respirations.

On verifie aussi que le moteur est DETERMINISTE (meme demande deux fois = meme
audio), sinon aucune comparaison ne tient. Resultat du 21/09/2026 : **il ne l'est
pas** -- c'est ce qui explique que le defaut n'arrive que « de temps en temps ».

Le moteur doit etre allume. LECTURE SEULE (le moteur calcule, comme en lecture).
Pour ECOUTER au lieu de mesurer : `_ecouter_contexte_kyutai.py` (meme dossier).

Usage : python test_voix/_mesurer_contexte_mots.py
"""

import io
import json
import sys
import urllib.request
import wave
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVICE = "http://127.0.0.1:8082/tts"
SORTIE = Path(__file__).resolve().parent / "_mesurer_contexte_mots.txt"
VOIX = "2114_1656_000053-0001"          # Claude (Monte-Cristo T2)
SEUIL = 0.012                            # « ca parle » (meme seuil que les outils d'atelier)
PAS_S = 0.01

# (titre, phrase PRECEDENTE (le contexte), phrase A LIRE)
CAS = [
    ("l'exemple de Laurent",
     "Je ne pense pas.",
     "Mais tu as peut etre raison."),
    ("A finit par un point-virgule",
     "Il prit le chemin, lentement, sans se retourner, et disparut ;",
     "Le lendemain, personne ne parla plus de lui."),
    ("A finit par des points de suspension",
     "Il regarda longtemps la maison, puis la lumiere s'eteignit...",
     "Alors il comprit qu'il n'y avait plus rien a faire."),
    ("B commence par un tiret de dialogue",
     "Elle posa la lettre sur la table et attendit.",
     "- Je ne savais pas, dit-il doucement."),
    ("A se termine par un guillemet fermant",
     "Il repondit simplement : \u00ab Je ne peux pas. \u00bb",
     "Personne n'osa insister ce soir-la."),
    ("A est longue (contexte de 8 mots bien rempli)",
     "Le vieil homme traversa la cour, salua les deux gardes, puis monta "
     "lentement les marches du perron et poussa la porte.",
     "La maison sentait la cire et le bois brulant."),
]

VARIANTES = [(8, "contexte 8 mots (aujourd'hui)"),
             (3, "contexte 3 mots (l'idee de Laurent)"),
             (2, "contexte 2 mots")]


def demander(texte, contexte=""):
    corps = {"texte": texte, "voix": VOIX}
    if contexte:
        corps["contexte"] = contexte
    requete = urllib.request.Request(
        SERVICE, data=json.dumps(corps).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=300) as reponse:
        return reponse.read()


def parole(octets):
    """(duree de PAROLE, duree totale, nombre de blocs) en secondes."""
    import array
    with wave.open(io.BytesIO(octets), "rb") as fichier:
        frequence = fichier.getframerate()
        echantillons = array.array("h")
        echantillons.frombytes(fichier.readframes(fichier.getnframes()))
    pas = max(1, int(PAS_S * frequence))
    blocs = []
    for debut in range(0, len(echantillons), pas):
        morceau = echantillons[debut:debut + pas]
        if morceau and max(abs(v) for v in morceau) / 32768.0 >= SEUIL:
            if blocs and debut - blocs[-1][1] <= pas * 1.5:
                blocs[-1] = (blocs[-1][0], debut + len(morceau))
            else:
                blocs.append((debut, debut + len(morceau)))
    duree_parole = sum(b - a for a, b in blocs) / float(frequence)
    return duree_parole, len(echantillons) / float(frequence), len(blocs)


def derniers_mots(texte, nombre):
    mots = texte.split()
    return " ".join(mots[-nombre:]) if mots else texte


def main():
    lignes = []
    lignes.append("MESURE DU CONTEXTE GLISSANT (Kyutai) -- voix %s" % VOIX)
    lignes.append("La duree de PAROLE est la somme des moments ou l'on parle")
    lignes.append("(sans les silences) : c'est elle qui revele un mot en trop.")
    lignes.append("")

    # 1. Le moteur est-il deterministe ? (sinon aucune comparaison ne tient)
    essai = CAS[0][2]
    premier = demander(essai)
    second = demander(essai)
    lignes.append("Moteur deterministe (meme demande = meme audio) : %s"
                  % ("OUI" if premier == second else "NON"))
    lignes.append("")

    # 2. Le tableau
    lignes.append("%-40s %-30s %8s %8s %6s %9s  %s"
                  % ("cas", "variante", "parole", "total", "blocs", "ecart",
                     "verdict"))
    lignes.append("-" * 130)

    for titre, precedente, phrase in CAS:
        reference = parole(demander(phrase))
        for nombre, etiquette in VARIANTES:
            contexte = derniers_mots(precedente, nombre)
            coupee = parole(demander(phrase, contexte))
            ecart = coupee[0] - reference[0]
            if ecart > 0.35:
                verdict = "RESIDU (mot du contexte)"
            elif ecart < -0.35:
                verdict = "PHRASE ROGNEE"
            else:
                verdict = "coupe juste"
            lignes.append("%-40s %-30s %7.2fs %7.2fs %6d %+8.2fs  %s"
                          % (titre[:40], etiquette, coupee[0], coupee[1],
                             coupee[2], ecart, verdict))
        lignes.append("%-40s %-30s %7.2fs %7.2fs %6d"
                      % ("  (phrase SEULE = reference)", "",
                         reference[0], reference[1], reference[2]))
        lignes.append("")

    SORTIE.write_text("\n".join(lignes), encoding="utf-8")
    print("\n".join(lignes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
