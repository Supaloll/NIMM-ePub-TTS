# -*- coding: utf-8 -*-
"""Lot d'ecoute A/B de la prononciation francaise imposee (21/09/2026).

Deux choses, dans l'ordre :

  1. la MESURE : il ecrit ce que le phonemiseur d'espeak-ng produit pour chacun
     des mots de `modules/prononciation.py` -- le mot tel quel (marques de
     langue comprises), sans les marques, et avec la graphie francaise. C'est la
     preuve chiffree qu'une entree de la table corrige bien quelque chose ;
  2. le LOT D'ECOUTE : il genere les WAV, avec la VRAIE voix Kokoro et dans la
     MEME phrase porteuse -- « avant » (ce que Laurent entend aujourd'hui) et
     « apres » (le remede). Son oreille est le dernier juge : la table ne garde
     que les graphies qu'il valide.

Le modele Kokoro (300 Mo) est charge une fois : comptez une trentaine de
secondes au total. Rien n'est envoye sur Internet, rien n'est facture.

Aucun caractere accentue n'est ecrit a l'ecran (regle du projet) : les phonemes
partent dans `mesure_phonemes.txt`, et le mode d'emploi dans `A_LIRE.txt`.

Usage : python test_voix/_mesurer_prononciation_kokoro.py
"""

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from modules import prononciation as _prononciation      # noqa: E402
from modules import tts as _tts                          # noqa: E402

SORTIE = Path(__file__).resolve().parent / "sortie_ecoute_prononciation"

# La voix du lot : celle du narrateur Kokoro, pour que l'ecoute ressemble a une
# lecture reelle. La MEME voix sert a l'avant et a l'apres.
VOIX = "kokoro:fm_narrateur"

# Mot ecoute + phrase porteuse. La phrase est IDENTIQUE avant/apres : sans cela,
# la comparaison ne vaut rien (lecon des lots d'ecoute de l'atelier).
A_ECOUTER = [
    ("Andrea", "Alors Andrea repondit doucement."),
    ("Ethan",  "Alors Ethan repondit doucement."),
    ("Maelys", "Alors Maëlys repondit doucement."),
    ("Mathis", "Alors Mathis repondit doucement."),
    ("Noah",   "Alors Noah repondit doucement."),
    ("dos",    "Il portait le sac sur le dos."),
]

PHRASE_ENTIERE = ("Andrea, Ethan, Maëlys, Mathis et Noah se retournèrent : "
                  "le sac était posé sur le dos.")


def rendre(phonemes, chemin):
    """Genere un WAV avec la vraie voix Kokoro, a partir de PHONEMES."""
    import soundfile as sf

    samples, frequence = _tts._kokoro.create(
        phonemes, voice=_tts._kokoro_voice_id(VOIX), speed=1.0,
        is_phonemes=True)
    sf.write(str(chemin), samples, frequence)


def ecrire_la_mesure(tokenizer):
    """Les phonemes de chaque entree de la table, en clair, dans un fichier."""
    lignes = ["MESURE AU PHONEMISEUR (espeak-ng, langue fr-fr)",
              "Ecrit par test_voix/_mesurer_prononciation_kokoro.py",
              "",
              "Les marques de langue -- (en), (fr) -- sont les fragments que le",
              "tokenizer de kokoro-onnx GARDE et qui etaient PRONONCES : c'est",
              "le « en ... fe » entendu autour du prenom.",
              ""]
    for mot, graphie in sorted(_prononciation.PRONONCIATION.items()):
        brut = tokenizer.phonemize(mot, "fr-fr")
        sans_marque = _tts.MARQUE_LANGUE.sub("", brut)
        corrige = tokenizer.phonemize(graphie, "fr-fr")
        lignes.append("mot ecrit : %s" % mot)
        lignes.append("   tel quel aujourd hui : %s" % brut)
        lignes.append("   sans les marques     : %s" % sans_marque)
        lignes.append("   graphie %-9s  : %s" % (graphie, corrige))
        lignes.append("   -> marque presente : %s"
                      % ("OUI" if "(" in brut else "non"))
        lignes.append("   -> marque apres correction : %s"
                      % ("OUI" if "(" in corrige else "non"))
        lignes.append("")
    (SORTIE / "mesure_phonemes.txt").write_text("\n".join(lignes),
                                                encoding="utf-8")


def ecrire_le_mode_emploi():
    """Le mode d'emploi du lot, en francais, a cote des fichiers."""
    lignes = [
        "PRONONCIATION DES PRENOMS - LOT D'ECOUTE (21/09/2026)",
        "",
        "Ce dossier contient des PAIRES de fichiers, pour les MEMES phrases :",
        "",
        "   NN_avant_<mot>.wav   ce que tu entends AUJOURD'HUI (les marques de",
        "                        langue d'espeak-ng sont prononcees : « en » et",
        "                        « fe » de part et d'autre du prenom)",
        "   NN_apres_<mot>.wav   le REMEDE (les sons francais sont imposes)",
        "",
        "Ecoute les paires l'une apres l'autre, puis dis simplement ce que tu",
        "retiens :",
        "",
        "   - si « apres » est MEILLEUR : la graphie de ce mot est gardee ;",
        "   - si « apres » est PIRE : elle est retiree (une ligne a changer).",
        "",
        "Andrea est le TEMOIN : tu avais deja valide ce cas dans le lot de",
        "l'atelier NIMM Voix. Les cinq autres (Ethan, Maelys, Mathis, Noah,",
        "dos) sont nouveaux : ce sont eux qu'il faut departager.",
        "",
        "La phrase porteuse de chaque mot est ecrite ci-dessous.",
        "",
    ]
    for numero, (mot, phrase) in enumerate(A_ECOUTER, 1):
        lignes.append("%2d. %-7s : « %s »" % (numero, mot, phrase))
    lignes += [
        "",
        "Les deux derniers fichiers contiennent TOUS les mots d'un coup",
        "(impression generale) : 20_avant_phrase_entiere.wav et",
        "21_apres_phrase_entiere.wav.",
        "",
        "Le detail des phonemes produit pour chaque mot est dans",
        "mesure_phonemes.txt, a cote.",
    ]
    (SORTIE / "A_LIRE.txt").write_text("\n".join(lignes), encoding="utf-8")


def main():
    SORTIE.mkdir(exist_ok=True)
    for ancien in SORTIE.glob("*.wav"):
        ancien.unlink()

    print("Chargement de Kokoro (environ 300 Mo, quelques secondes)...")
    _tts._load_kokoro()
    tokenizer = _tts._kokoro.tokenizer

    ecrire_la_mesure(tokenizer)
    ecrire_le_mode_emploi()

    print("")
    print("Generation des fichiers a ecouter (voix %s)..." % VOIX)
    nombre = 0
    for numero, (mot, phrase) in enumerate(A_ECOUTER, 1):
        # AVANT : les phonemes tels qu'ils sortent du phonemiseur, marques de
        # langue comprises -- exactement ce que le moteur recevait avant le
        # correctif.
        rendre(tokenizer.phonemize(phrase, "fr-fr"),
               SORTIE / ("%02d_avant_%s.wav" % (numero, mot)))
        # APRES : la phrase preparee par `pour_lecture`, puis les phonemes sans
        # marque -- le chemin de synthese d'aujourd'hui.
        rendre(_tts._phonemes_kokoro(_prononciation.pour_lecture(phrase)),
               SORTIE / ("%02d_apres_%s.wav" % (numero, mot)))
        nombre += 2
        print("  %2d. %-7s  avant / apres" % (numero, mot))

    rendre(tokenizer.phonemize(PHRASE_ENTIERE, "fr-fr"),
           SORTIE / "20_avant_phrase_entiere.wav")
    rendre(_tts._phonemes_kokoro(_prononciation.pour_lecture(PHRASE_ENTIERE)),
           SORTIE / "21_apres_phrase_entiere.wav")
    nombre += 2

    print("")
    print("%d fichiers ecrits dans :" % nombre)
    print("  %s" % SORTIE)
    print("Le mode d'emploi du lot : A_LIRE.txt (dans ce dossier).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
