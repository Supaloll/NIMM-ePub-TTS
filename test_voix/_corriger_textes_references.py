# -*- coding: utf-8 -*-
"""Corrige les TEXTES DE REFERENCE des voix Qwen transcrits automatiquement.

POURQUOI (29/09/2026). Le clonage ICL aligne l'audio de reference sur SON TEXTE.
Quand le texte est une transcription automatique fautive, le moteur recoit un
audio qui dit une chose et un texte qui en dit une autre : c'est ce qui a fait
DERAPER la voix d'Aubin (« le trois MALES pharaon » au lieu de « le trois-MATS le
Pharaon », 163 s de bruit). Sur les 157 textes de `references.csv`, **63** sont
des transcriptions (les 35 extraits historiques et les 28 « Decoupage OK ») ; les
94 autres ont ete ECRITS par l'atelier NIMM Voix, donc justes.

COMMENT. Ces 63 extraits sont des passages de **livres du domaine public** (Le
Rouge et le Noir, Monte-Cristo, L'Odyssee...). Le modele de langage LOCAL
(Ollama, gratuit) sait retrouver le texte exact quand il reconnait le passage --
verifie le 29/09/2026 : « trois males pharaon » -> « trois-mats le Pharaon ».

CE QU'IL FAIT, et ce qu'il ne fait pas :
  - il ne touche QUE les textes non atelier (les 63) ;
  - il demande une correction CONSERVATRICE (aucune reformulation, aucun style
    change : l'extrait est un enregistrement, le texte doit dire ce qui est lu) ;
  - il affiche les MOTS CHANGES, un par un : c'est ce qu'un humain peut relire ;
  - il ALERTE quand un texte change trop (au-dela de `SEUIL_ALERTE` des mots) :
    signe que le modele a reecrit au lieu de corriger -- le piege constate des
    l'essai (il avait ajoute un « de » qui n'existe pas dans le livre).

SECURITE : rapport seul par defaut (aucune ecriture). Avec `--ecrire`, le fichier
`references.csv` est COPIE (nom date) avant toute modification, et seule la
colonne du texte est remplacee. Le resultat est relu et compte.

GRATUIT : modele local, aucune API facturee. `--modele` permet d'en choisir un
autre (`qwen3:8b` par defaut, celui de `data/config.json`).

Usage :
    python test_voix/_corriger_textes_references.py                  # rapport seul
    python test_voix/_corriger_textes_references.py --limite 5        # essai court
    python test_voix/_corriger_textes_references.py --ecrire
"""
import argparse
import csv
import json
import shutil
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CSV = RACINE / "qwen_tts_service" / "voix" / "references.csv"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODELE_DEFAUT = "qwen3:8b"

# Au-dela de cette part de mots changes, on considere que le modele a REEcrit :
# la correction est alors signalee pour relecture humaine au lieu d'etre proposee
# comme telle.
SEUIL_ALERTE = 0.25

# EXTRAITS LAISSES DE COTE (29/09/2026). Sur les 22 corrections proposees, six
# n'ont pas ete retenues apres relecture : elles touchent des mots qui sont DEJA
# corrects (« clot » -> « clote », « champs » -> « chars », « des » -> « de ») ou
# seulement des guillemets (sans effet sur l'audio, mais le changement est
# douteux). Leur texte d'origine est donc GARDE : mieux vaut un texte imparfait
# qu'un texte faux, puisque le modele ICL aligne l'audio sur ce qu'il lit.
EXCLUS = (
    "5476_3103_000072-0001",   # « clot » -> « clote » : faux
    "Femme001_reference",      # « champs » -> « chars » : douteux
    "Femme002_reference",      # corrections vides et guillemets : douteux
    "Femme48897_reference",    # « des » -> « de » : douteux
    "7591_6742_000149-0002",   # guillemets seulement
    "928_486_000075-0001",     # guillemets seulement
)

sys.stdout.reconfigure(encoding="utf-8")

CONSIGNE = """Tu recois la transcription AUTOMATIQUE d'un extrait de livre audio
en francais (un lecteur humain enregistre, transcrit par un outil de
reconnaissance vocale). Ce sont des classiques du domaine public, et l'outil se
trompe surtout sur les mots rares et les noms propres : il ecrit par exemple
« le trois males pharaon » pour « le trois-mats le Pharaon » (Monte-Cristo).

Rends le texte EXACT qui est lu, en corrigeant UNIQUEMENT ce qui est mal
transcrit. Regles STRICTES :
- ne reformule rien, ne change pas le style : c'est un extrait de livre, il est
  deja ecrit dans un francais correct ;
- n'ajoute et ne retire aucun mot qui est correct ;
- si tu reconnais le passage (ce sont des classiques), retablis les mots exacts
  de l'auteur ;
- garde la ponctuation d'origine ;
- reponds UNIQUEMENT par le texte corrige, sans commentaire, sans guillemets.

TRANSCRIPTION A CORRIGER :
%s"""

# POURQUOI LA CONSIGNE DONNE UN EXEMPLE (mesure du 29/09/2026, `_test_consignes.py`,
# trois variantes sur le texte d'Aubin) :
#   - consigne stricte SANS exemple ....... 2 s, ne corrige PAS « trois males »
#   - consigne AVEC exemple ............... 2 s, corrige (« trois-mats le Pharaon »)
#   - consigne avec exemple + raisonnement  19 s, corrige aussi (mais 10x plus lent)
# Le modele a besoin qu'on lui MONTRE le type d'erreur cherche : sans exemple, il
# recopie le texte en ne changeant presque rien (il a juste corrige « le » en
# « les » sur ce cas), et le defaut reste. Avec l'exemple, il trouve tout seul.


def lire_lignes():
    """Toutes les lignes du CSV (la premiere est l'en-tete)."""
    with open(CSV, "r", encoding="utf-8", newline="") as fichier:
        return list(csv.reader(fichier, delimiter=";"))


def est_atelier(source):
    """Le texte vient-il de l'atelier (donc ecrit par nous, donc juste) ?"""
    s = (source or "").lower()
    return "nimm" in s or "allemand" in s


def corriger(texte, modele):
    corps = json.dumps({
        "model": modele,
        "prompt": CONSIGNE % texte,
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
    }).encode("utf-8")
    requete = urllib.request.Request(
        OLLAMA, data=corps, headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(requete, timeout=900) as reponse:
        donnees = json.loads(reponse.read().decode("utf-8", "replace"))
    return (donnees.get("response") or "").strip()


def differences(avant, apres):
    """[(avant, apres)] : les morceaux de texte qui changent, mot a mot."""
    import difflib
    mots_avant = avant.split()
    mots_apres = apres.split()
    changements = []
    for etiquette, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, mots_avant, mots_apres).get_opcodes():
        if etiquette == "equal":
            continue
        changements.append((" ".join(mots_avant[i1:i2]),
                            " ".join(mots_apres[j1:j2])))
    return changements


def part_changee(avant, apres):
    """Part des mots du texte qui ont bouge (0 a 1)."""
    import difflib
    mots_avant = avant.split()
    if not mots_avant:
        return 0.0
    inchanges = sum(bloc.size for bloc in
                    difflib.SequenceMatcher(None, mots_avant,
                                            apres.split()).get_matching_blocks())
    return 1.0 - (inchanges / float(len(mots_avant)))


def main():
    analyseur = argparse.ArgumentParser(
        description="Corrige les textes de reference transcrits (modele local).")
    analyseur.add_argument("--modele", default=MODELE_DEFAUT,
                           help="modele Ollama (defaut : %s)" % MODELE_DEFAUT)
    analyseur.add_argument("--limite", type=int, default=0,
                           help="ne traiter que les N premiers textes (essai)")
    analyseur.add_argument("--motif", default="",
                           help="ne traiter que les extraits dont le nom contient "
                                "ce motif (essai cible)")
    analyseur.add_argument("--ecrire", action="store_true",
                           help="ecrit vraiment (copie datee du CSV d'abord)")
    options = analyseur.parse_args()

    lignes = lire_lignes()
    if not lignes:
        print("ERR : %s illisible" % CSV)
        return 1
    entete, corps = lignes[0], lignes[1:]

    a_traiter = [i for i, ligne in enumerate(corps, 1)
                 if len(ligne) >= 2 and not est_atelier(
                     ligne[4] if len(ligne) > 4 else "")]
    # Les extraits ECRTES a la relecture (voir EXCLUS) : leur texte reste tel quel.
    laisses = [i for i in a_traiter
               if any(motif.lower() in corps[i - 1][0].lower()
                      for motif in EXCLUS)]
    a_traiter = [i for i in a_traiter if i not in laisses]
    if options.motif:
        a_traiter = [i for i in a_traiter
                     if options.motif.lower() in corps[i - 1][0].lower()]
    if options.limite:
        a_traiter = a_traiter[:options.limite]

    print("")
    print("=" * 76)
    print(" CORRECTION DES TEXTES DE REFERENCE TRANSCRITS")
    print("=" * 76)
    print(" fichier : %s (%d lignes)" % (CSV.name, len(corps)))
    print(" modele  : %s (local, gratuit)" % options.modele)
    print(" textes a traiter : %d (les autres ont ete ecrits par l'atelier)"
          % len(a_traiter))
    print(" laisses de cote apres relecture : %d" % len(laisses))
    for i in laisses:
        print("    %s" % corps[i - 1][0])
    print(" mode : %s" % ("ECRITURE" if options.ecrire else
                           "rapport seul (rien n'est modifie)"))
    print("")

    # Un premier appel sert de controle : si le modele ne repond pas, on s'arrete
    # avant d'avoir mouline pour rien.
    try:
        corriger("Bonjour.", options.modele)
    except Exception as e:
        print(" ERR : le modele local ne repond pas (%s)" % str(e)[:70])
        print("       Verifier qu'Ollama tourne (http://127.0.0.1:11434).")
        return 1

    corriges = {}
    alertes = []
    for rang, index in enumerate(a_traiter, 1):
        ligne = corps[index - 1]
        texte = ligne[1].strip()
        try:
            nouveau = corriger(texte, options.modele)
        except Exception as e:
            print("  %2d/%d ERREUR : %s" % (rang, len(a_traiter), str(e)[:60]))
            continue
        # Garde-fous : le service lit le CSV par `split(';')`, un point-virgule
        # introduit casserait la ligne ; un texte vide ou trop court est refuse.
        problemes = []
        if ";" in nouveau:
            problemes.append("point-virgule introduit")
        if len(nouveau) < len(texte) * 0.5:
            problemes.append("texte beaucoup plus court")
        part = part_changee(texte, nouveau)
        if part > SEUIL_ALERTE:
            problemes.append("reecriture probable (%.0f %% du texte)" % (part * 100))
        corriges[index] = nouveau
        if problemes:
            alertes.append((ligne[0], problemes))
        print("  %2d/%d %-34s %5.1f %% de mots changes%s"
              % (rang, len(a_traiter), ligne[0][:34], part * 100,
                 "   << " + " / ".join(problemes) if problemes else ""),
              flush=True)
        for avant, apres in differences(texte, nouveau)[:6]:
            print("        « %s »  ->  « %s »" % (avant[:60], apres[:60]),
                  flush=True)

    print("")
    print(" %d textes corriges proposes." % len(corriges))
    if alertes:
        print(" %d A RELIRE (garde-fou declenche) :" % len(alertes))
        for nom, problemes in alertes:
            print("    %-38s %s" % (nom[:38], " / ".join(problemes)))
    else:
        print(" aucun garde-fou declenche.")

    if not options.ecrire:
        print("")
        print(" (rapport seul : rien n'a ete modifie -- ajoute --ecrire)")
        return 0

    horodatage = datetime.now().strftime("%Y%m%d_%H%M")
    # ATTENTION au piege du 29/09/2026 : `with_suffix('.csv')` REMPLACE tout ce
    # qui suit le PREMIER point du nom -- sur « references.bak_avant_..._1600 » il
    # rendait « references.csv », donc la copie se faisait sur ELLE-MEME et Windows
    # refusait (PermissionError, WinError 32, « utilise par un autre processus »).
    # Le nom se construit donc a la main, en une fois.
    sauvegarde = CSV.with_name("%s.bak_avant_textes_corriges_%s.csv"
                               % (CSV.stem, horodatage))
    shutil.copy2(str(CSV), str(sauvegarde))

    nouvelles = [entete]
    for index, ligne in enumerate(corps, 1):
        if index in corriges and len(ligne) >= 2:
            ligne = list(ligne)
            ligne[1] = corriges[index]
        nouvelles.append(ligne)
    with open(CSV, "w", encoding="utf-8", newline="") as fichier:
        for ligne in nouvelles:
            fichier.write(";".join(ligne) + "\n")

    # CONTROLE : on relit le fichier ecrit, comme le fait le service.
    relu = lire_lignes()[1:]
    changes = sum(1 for i in corriges
                  if i <= len(relu) and len(relu[i - 1]) >= 2
                  and relu[i - 1][1].strip() == corriges[i].strip())
    print("")
    print(" textes ecrits et RELUS identiques : %d sur %d"
          % (changes, len(corriges)))
    print(" copies d'origine : %s" % sauvegarde.name)
    print(" RETOUR ARRIERE : recopier cette copie sur %s" % CSV.name)
    print("")
    print(" A FAIRE MAINTENANT : (1) redemarrer le moteur Qwen (le texte des voix")
    print(" est lu au demarrage) ; (2) monter VERSION_CACHE dans modules/tts_cache.py,")
    print(" sinon le lecteur resservirait les phrases deja generees avec l'ancien texte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
