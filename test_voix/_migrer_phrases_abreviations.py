# -*- coding: utf-8 -*-
"""MIGRATION CIBLEE des index de phrases apres les ABREVIATIONS EN CAPITALES.

Pourquoi (21/09/2026) : `MR.`, `MRS.` et les civilites en capitales ne sont plus
reconnues comme des fins de phrase (`modules/decoupage.py`). Un chapitre a donc
**moins de phrases** qu'avant -- et comme `speaker_attribution.sentence_idx` porte
le « qui parle », **tous les index qui suivent une fusion se decalent** : un
personnage parlerait avec la voix de son voisin.

Ce que l'outil fait, pour chaque chapitre concerne (mesure du 21/09/2026 :
**17 chapitres, tous dans 22/11/63**) :

  1. il calcule les phrases **AVANT** la correction (liste d'abreviations privee
     des nouvelles formes) et **APRES** (etat actuel), positions a l'appui ;
  2. il en deduit, pour chaque ANCIENNE phrase, la NOUVELLE qui la contient ;
  3. quand plusieurs anciennes phrases tombent dans la meme nouvelle (c'est la
     fusion), il garde le locuteur de la plus **LONGUE** -- et **SIGNELE** les cas
     ou les deux locuteurs differaient, a corriger a la main si besoin ;
  4. il remplace les lignes du chapitre par les lignes remappees, dans **UNE
     transaction** (de tout ou rien) ;
  5. il recale aussi `progress.cursor_idx` du chapitre, pour que la lecture
     reprenne au meme endroit.

USAGE (la simulation n'ecrit JAMAIS rien) :
    python test_voix/_migrer_phrases_abreviations.py              (simulation)
    python test_voix/_migrer_phrases_abreviations.py --livre 28   (un seul livre)
    python test_voix/_migrer_phrases_abreviations.py --ecrire     (copie la base AVANT)
"""

import argparse
import io
import shutil
import sqlite3
import sys
import time
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
sys.path.insert(0, str(RACINE))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core import epub_parser                                      # noqa: E402
from modules import decoupage                                     # noqa: E402

BASE = RACINE / "data" / "nimm_epub.db"
SORTIE = DOSSIER / "_migrer_abreviations_rapport.txt"

# Les formes ajoutees le 21/09/2026 : ce sont elles qui fusionnent des phrases.
NOUVELLES = ('MR', 'MRS', 'MME', 'MMES', 'MLLE', 'MLLES', 'MGR', 'DR', 'PR',
             'Mrs')


def phrases_avec(texte, abreviations):
    """[(debut, fin, phrase)] avec une liste d'abreviations donnee."""
    anciennes = decoupage.ABREVIATIONS
    try:
        decoupage.ABREVIATIONS = abreviations
        return decoupage.phrases_avec_positions(texte, decoupage.REGLE_ACTUELLE)
    finally:
        decoupage.ABREVIATIONS = anciennes


def correspondance(anciennes, nouvelles):
    """[(index de l'ancienne phrase, index de la nouvelle qui la contient)].

    Les deux listes sont ordonnees et couvrent le meme texte : la nouvelle
    phrase qui contient une ancienne est celle dont l'etendue la recouvre.
    """
    resultat = []
    j = 0
    for indice, (_debut, fin, _texte) in enumerate(anciennes):
        while j + 1 < len(nouvelles) and nouvelles[j][1] < fin:
            j += 1
        resultat.append((indice, j))
    return resultat


def chemin_de_livre(nom):
    if not nom:
        return None
    for essai in (Path(nom), RACINE / "data" / "library" / nom):
        if essai.is_file():
            return essai
    return None


def etudier_un_chapitre(texte, lignes):
    """Le plan de migration d'un chapitre, sous forme de dictionnaire."""
    anciennes = phrases_avec(texte, tuple(
        valeur for valeur in decoupage.ABREVIATIONS
        if valeur not in NOUVELLES))
    nouvelles = decoupage.phrases_avec_positions(texte,
                                                 decoupage.REGLE_ACTUELLE)
    correspondances = correspondance(anciennes, nouvelles)

    par_ancien = {indice: locuteur for indice, locuteur in lignes}
    groupes = {}
    for ancien, nouveau in correspondances:
        groupes.setdefault(nouveau, []).append(ancien)

    remappees = []
    ambigues = []
    for nouveau, anciens in sorted(groupes.items()):
        plus_longue = max(anciens, key=lambda a: len(anciennes[a][2]))
        locuteur = par_ancien.get(plus_longue, "Narration")
        if len(anciens) > 1:
            locuteurs = sorted({par_ancien.get(a, "Narration")
                                for a in anciens})
            if len(locuteurs) > 1:
                ambigues.append((nouveau, locuteurs,
                                 anciennes[plus_longue][2][:70]))
        remappees.append((nouveau, locuteur))

    return {"anciennes": anciennes, "nouvelles": nouvelles,
            "correspondances": correspondances,
            "remappees": remappees, "ambigues": ambigues}


def analyser_arguments():
    analyseur = argparse.ArgumentParser(
        description="Migration des index de phrases apres les abreviations "
                    "en capitales (MR., MRS., MME....).")
    analyseur.add_argument("--livre", type=int, default=None,
                           help="ne traiter qu'un seul livre")
    analyseur.add_argument("--ecrire", action="store_true",
                           help="appliquer la migration (copie la base AVANT)")
    return analyseur.parse_args()


def planifier(connexion, seulement_livre=None):
    """Le plan complet : un dictionnaire par chapitre concerne."""
    plan = []
    for livre, titre, nom in connexion.execute(
            "SELECT id, title, filename FROM books ORDER BY id"):
        if seulement_livre and livre != seulement_livre:
            continue
        chemin = chemin_de_livre(nom)
        if chemin is None:
            continue
        try:
            chapitres = epub_parser.get_chapters(str(chemin))
        except Exception as erreur:
            print("  [livre %s] illisible : %s" % (livre, str(erreur)[:60]))
            continue
        for chapitre, contenu in enumerate(chapitres):
            texte = contenu.get("text") or ""
            if len(texte) < 6:
                continue
            lignes = connexion.execute(
                "SELECT sentence_idx, speaker FROM speaker_attribution "
                "WHERE book_id=? AND chapter_index=? ORDER BY sentence_idx",
                (livre, chapitre)).fetchall()
            if not lignes:
                continue
            etude = etudier_un_chapitre(texte, lignes)
            if len(etude["anciennes"]) == len(etude["nouvelles"]):
                continue
            etude.update({"livre": livre, "titre": titre, "chapitre": chapitre})
            plan.append(etude)
    return plan


def ecrire_le_rapport(plan, ecrit, chemin_copie):
    lignes = ["MIGRATION DES INDEX DE PHRASES (abreviations en capitales)",
              "21/09/2026 -- %s" % ("ECRITURE" if ecrit else "SIMULATION"),
              ""]
    if chemin_copie:
        lignes.append("Copie de surete : %s" % chemin_copie.name)
        lignes.append("")
    total_avant = total_apres = total_fusions = total_ambigues = 0
    for entree in plan:
        fusionnees = len(entree["anciennes"]) - len(entree["nouvelles"])
        total_avant += len(entree["anciennes"])
        total_apres += len(entree["nouvelles"])
        total_fusions += fusionnees
        total_ambigues += len(entree["ambigues"])
        lignes.append("[livre %s] %s -- chapitre %s : %d lignes -> %d "
                      "(%d fusion(s))"
                      % (entree["livre"], entree["titre"], entree["chapitre"],
                         len(entree["anciennes"]), len(entree["nouvelles"]),
                         fusionnees))
        for numero, locuteurs, extrait in entree["ambigues"]:
            lignes.append("   ATTENTION : la nouvelle phrase %d reunissait "
                          "plusieurs locuteurs (%s)" % (numero, locuteurs))
            lignes.append("     garde le locuteur de la plus longue : %r"
                          % extrait)
        lignes.append("")
    lignes.append("TOTAL : %d chapitre(s), %d ligne(s) avant, %d apres "
                  "(%d fusion(s), %d a verifier a la main)"
                  % (len(plan), total_avant, total_apres, total_fusions,
                     total_ambigues))
    SORTIE.write_text("\n".join(lignes), encoding="utf-8")
    for ligne in lignes:
        print(ligne)


def verifier(connexion, plan):
    """Apres migration : autant de lignes que de phrases, index uniques et dans
    les bornes."""
    problemes = []
    for entree in plan:
        lignes = connexion.execute(
            "SELECT sentence_idx FROM speaker_attribution "
            "WHERE book_id=? AND chapter_index=? ORDER BY sentence_idx",
            (entree["livre"], entree["chapitre"])).fetchall()
        indices = [indice for indice, in lignes]
        if len(indices) != len(entree["nouvelles"]):
            problemes.append("livre %s chapitre %s : %d lignes pour %d phrases"
                             % (entree["livre"], entree["chapitre"],
                                len(indices), len(entree["nouvelles"])))
        if len(set(indices)) != len(indices):
            problemes.append("livre %s chapitre %s : index en double"
                             % (entree["livre"], entree["chapitre"]))
        if indices and indices[-1] >= len(entree["nouvelles"]):
            problemes.append("livre %s chapitre %s : index %d hors bornes"
                             % (entree["livre"], entree["chapitre"],
                                indices[-1]))
    return problemes


def recaler_la_lecture(connexion, entree):
    """La position de lecture suit le meme decalage (si elle est dans ce
    chapitre). Rend le nombre de positions recalees."""
    colonnes = [ligne[1] for ligne in connexion.execute(
        "PRAGMA table_info(progress)")]
    if "cursor_idx" not in colonnes:
        return 0
    table = dict(entree["correspondances"])
    recalees = 0
    for (utilisateur,) in connexion.execute(
            "SELECT DISTINCT user_id FROM progress "
            "WHERE book_id=? AND chapter_index=?",
            (entree["livre"], entree["chapitre"])).fetchall():
        ligne = connexion.execute(
            "SELECT cursor_idx FROM progress "
            "WHERE user_id=? AND book_id=? AND chapter_index=?",
            (utilisateur, entree["livre"], entree["chapitre"])).fetchone()
        valeur = ligne[0] if ligne else None
        if valeur is None:
            continue
        nouveau = table.get(valeur)
        if nouveau is not None and nouveau != valeur:
            connexion.execute(
                "UPDATE progress SET cursor_idx=? "
                "WHERE user_id=? AND book_id=? AND chapter_index=?",
                (nouveau, utilisateur, entree["livre"], entree["chapitre"]))
            recalees += 1
    return recalees


def main():
    options = analyser_arguments()
    lecture = sqlite3.connect("file:%s?mode=ro" % BASE.as_posix(), uri=True)
    plan = planifier(lecture, options.livre)
    lecture.close()

    if not plan:
        print("Rien a migrer : aucun chapitre n'est concerne.")
        return 0

    chemin_copie = None
    if options.ecrire:
        horodatage = time.strftime("%Y%m%d_%H%M")
        chemin_copie = BASE.with_name(
            "nimm_epub.db.bak_avant_migration_abreviations_%s" % horodatage)
        shutil.copy2(BASE, chemin_copie)

    ecrire_le_rapport(plan, options.ecrire, chemin_copie)

    if not options.ecrire:
        print("")
        print("SIMULATION : rien n'a ete modifie. Pour appliquer :")
        print("    python test_voix/_migrer_phrases_abreviations.py --ecrire")
        return 0

    connexion = sqlite3.connect(str(BASE))
    recalees = 0
    try:
        with connexion:                # UNE transaction : tout ou rien
            for entree in plan:
                connexion.execute(
                    "DELETE FROM speaker_attribution "
                    "WHERE book_id=? AND chapter_index=?",
                    (entree["livre"], entree["chapitre"]))
                connexion.executemany(
                    "INSERT INTO speaker_attribution "
                    "(book_id, chapter_index, sentence_idx, speaker) "
                    "VALUES (?, ?, ?, ?)",
                    [(entree["livre"], entree["chapitre"], indice, locuteur)
                     for indice, locuteur in entree["remappees"]])
                recalees += recaler_la_lecture(connexion, entree)
        problemes = verifier(connexion, plan)
    finally:
        connexion.close()

    print("")
    if problemes:
        print("ATTENTION : %d probleme(s) apres la migration :"
              % len(problemes))
        for probleme in problemes:
            print("   " + probleme)
        print("La copie de surete est la : %s" % chemin_copie)
        return 1
    print("Migration TERMINEE et VERIFIEE : chaque chapitre a autant de lignes "
          "que de phrases, chaque index est unique et dans les bornes.")
    print("Positions de lecture recalees : %d" % recalees)
    print("Copie de surete : %s" % chemin_copie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
