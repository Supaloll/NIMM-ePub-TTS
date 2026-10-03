# -*- coding: utf-8 -*-
"""Synchronisation « copie pour Claude » -- NIMM ePub.

But : remplir un dossier  copie_pour_Claude\\  (a la racine) avec des COPIES
plates des fichiers listes dans  copie_pour_Claude_liste.txt , pour que Laurent
les glisse d'un seul geste dans un projet Claude.

Regles :
  - SENS UNIQUE : originaux -> copie. Rien n'est JAMAIS ecrit hors de
    copie_pour_Claude\\ (le dossier, son _INDEX.txt et son _ETAT_DU_JOUR.md).
  - Le dossier est VIDE puis RECOPIE entierement a chaque synchro (aucun reste
    d'une ancienne version).
  - Le nom d'une copie porte son chemin : modules/tts.py -> modules__tts.py .
  - GARDE-FOUS : certains fichiers ne sont JAMAIS copies, meme s'ils figurent
    dans la liste (secrets, bases, audio, modeles, sauvegardes .bak, .venv...).
    En cas de doute, on ne copie pas et on le dit.
  - Un fichier de plus de 2 Mo est ignore et signale.

Usage :
  python _synchroniser_copie_claude.py            (vraie synchro)
  python _synchroniser_copie_claude.py --blanc    (test a blanc : rien ecrit)
"""
import re
import shutil
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent
LISTE = RACINE / 'copie_pour_Claude_liste.txt'
SORTIE = RACINE / 'copie_pour_Claude'
NOTES = RACINE / 'copie_pour_Claude_notes.md'
TAILLE_MAX = 2 * 1024 * 1024

# Jamais copies, quoi qu'il arrive.
DOSSIERS_INTERDITS = {'.venv', 'node_modules', '__pycache__', '.git',
                      'tts_cache', '.mypy_cache', '.pytest_cache'}
EXTENSIONS_INTERDITES = {'.wav', '.mp3', '.flac', '.ogg', '.m4a',
                         '.gguf', '.safetensors', '.pt', '.bin', '.onnx',
                         '.db', '.sqlite', '.sqlite3',
                         '.env', '.pfx', '.pem', '.key'}
NOMS_INTERDITS = {'references_privees.csv'}


def refus(rel):
    """Rend la raison du refus, ou None si le fichier peut etre copie."""
    parties = [p.lower() for p in rel.parts]
    nom = rel.name.lower()
    for dossier in parties[:-1]:
        if dossier in DOSSIERS_INTERDITS:
            return "dossier reserve (%s)" % dossier
    if nom in NOMS_INTERDITS:
        return "fichier prive (%s)" % nom
    if nom == 'config.json' and 'data' in parties:
        return "data/config.json (reglages/secrets)"
    if nom.startswith('.env'):
        return "fichier .env"
    if '.bak' in nom:
        return "sauvegarde (.bak)"
    if rel.suffix.lower() in EXTENSIONS_INTERDITES:
        return "extension interdite (%s)" % rel.suffix.lower()
    return None


def lire_liste():
    """(prefixe, chemins) : la liste, et sa directive « # prefixe: EPUB ».

    Une ligne `# prefixe: EPUB` (ou `#prefixe=EPUB`) fixe le PREFIXE du projet,
    mis devant le nom des copies ET des fichiers fabriques.
    """
    if not LISTE.is_file():
        print("ARRET : la liste est absente : %s" % LISTE)
        return None, None
    prefixe = ''
    chemins = []
    for ligne in LISTE.read_text(encoding='utf-8').splitlines():
        texte = ligne.strip()
        if not texte:
            continue
        if texte.startswith('#'):
            reste = texte.lstrip('#').strip()
            mot = reste.split(':', 1)[0].split('=', 1)[0].strip().lower()
            if mot == 'prefixe':
                prefixe = reste.split(':', 1)[-1].split('=', 1)[-1].strip()
            continue
        chemins.append(Path(texte.replace('\\', '/')))
    return prefixe, chemins


def lire_derniere_synchro(prefixe=''):
    """L'heure de la synchro precedente, lue dans l'ETAT_DU_JOUR du dossier."""
    etat = SORTIE / nom_genere('ETAT_DU_JOUR.md', prefixe)
    if not etat.is_file():
        return None
    trouve = re.search(r'Synchro du (\d{2}/\d{2}/\d{4} \d{2}:\d{2})',
                       etat.read_text(encoding='utf-8', errors='replace'))
    if not trouve:
        return None
    try:
        return time.mktime(time.strptime(trouve.group(1), '%d/%m/%Y %H:%M'))
    except Exception:
        return None


def _ecrire(chemin, texte):
    """Ecrit un fichier en UTF-8, fins de ligne Windows (CRLF).

    On donne le texte tel quel (avec des \\n) : Python les traduit en CRLF sur
    Windows. NE PAS pre-remplacer les \\n par \\r\\n -- `write_text` traduirait
    ENCORE et on obtiendrait des doubles retours (\\r\\r\\n). Vu et corrige le
    01/10/2026.
    """
    chemin.write_text(texte, encoding='utf-8')


def _vider_le_dossier():
    """Enleve tout ce qu'il y a DANS copie_pour_Claude (garde le dossier)."""
    if not SORTIE.exists():
        return
    for enfant in SORTIE.iterdir():
        if enfant.is_dir():
            shutil.rmtree(enfant)
        else:
            enfant.unlink()


def preparer_plan(chemins):
    """Trie chaque chemin : a copier / disparu / refuse / trop gros."""
    a_copier, disparus, refuses, trop_gros = [], [], [], []
    for rel in chemins:
        full = RACINE / rel
        if not full.exists():
            disparus.append(rel)
            continue
        if full.is_dir():
            refuses.append((rel, "c'est un dossier, pas un fichier"))
            continue
        raison = refus(rel)
        if raison:
            refuses.append((rel, raison))
            continue
        taille = full.stat().st_size
        if taille > TAILLE_MAX:
            trop_gros.append((rel, taille))
            continue
        a_copier.append((rel, full, taille))
    return a_copier, disparus, refuses, trop_gros


def nom_plat(rel, prefixe=''):
    """modules/tts.py -> EPUB__modules__tts.py (le projet, puis le chemin).

    Le PREFIXE du projet (EPUB, VOIX...) evite que deux copies glissees dans le
    MEME projet Claude ne s'ecrasent : `ETAT.md` devient `EPUB__ETAT.md` chez
    l'un et `VOIX__ETAT.md` chez l'autre.
    """
    return (prefixe + '__' if prefixe else '') + '__'.join(rel.parts)


def nom_genere(nom, prefixe=''):
    """Le nom d'un fichier FABRIQUE par la synchro (ETAT_DU_JOUR, INDEX)."""
    return (prefixe + '__' if prefixe else '') + nom


def ecrire_index(a_copier, disparus, refuses, trop_gros, maintenant, prefixe=''):
    lignes = ["Copie pour Claude -- index", "=" * 50,
              "Synchro du %s" % maintenant, "",
              "FICHIERS COPIES (%d)" % len(a_copier)]
    total = 0
    for rel, _full, taille in a_copier:
        total += taille
        lignes.append("  %8d o  %s" % (taille, nom_plat(rel, prefixe)))
    lignes.append("")
    lignes.append("TOTAL : %d fichier(s), %d o (~%d Ko)"
                  % (len(a_copier), total, int(total / 1024)))
    familles = (
        ("DANS LA LISTE MAIS INTROUVABLES",
         [("%s" % rel, "") for rel in disparus]),
        ("IGNORES -- INTERDITS", refuses),
        ("IGNORES -- PLUS DE 2 Mo",
         [("%s" % rel, "%d o" % t) for rel, t in trop_gros]),
    )
    for titre, morceaux in familles:
        if not morceaux:
            continue
        lignes.append("")
        lignes.append("%s (%d)" % (titre, len(morceaux)))
        for nom, detail in morceaux:
            lignes.append("  %s%s"
                          % (nom, ("  ->  " + detail) if detail else ""))
    _ecrire(SORTIE / nom_genere('INDEX.txt', prefixe), "\n".join(lignes) + "\n")
    return total


def ecrire_etat(a_copier, derniere, maintenant, prefixe=''):
    lignes = ["# %s -- %s" % (nom_genere('ETAT_DU_JOUR.md', prefixe), RACINE.name), "",
              "**Synchro du %s**" % maintenant]
    if derniere:
        modifs = [(rel, full.stat().st_mtime) for rel, full, _t in a_copier
                  if full.stat().st_mtime > derniere]
        modifs.sort(key=lambda x: -x[1])
        lignes.append("Fichiers modifies depuis la synchro precedente : %d"
                      % len(modifs))
        for rel, _m in modifs[:8]:
            lignes.append("- %s" % rel)
        if len(modifs) > 8:
            lignes.append("- ... et %d autre(s)" % (len(modifs) - 8))
    else:
        lignes.append("(premiere synchro : aucun point de comparaison)")
    if NOTES.is_file():
        lignes.append("")
        lignes.append("## Decisions / reste (notes de session)")
        notes = [l for l in NOTES.read_text(encoding='utf-8',
                                            errors='replace').splitlines()
                 if l.strip()]
        lignes.extend(notes[:8])
    _ecrire(SORTIE / nom_genere('ETAT_DU_JOUR.md', prefixe),
            "\n".join(lignes[:20]) + "\n")


def _familles(disparus, refuses, trop_gros):
    return (("refus (jamais copies)", refuses),
            ("plus de 2 Mo, ignores",
             [("%s" % r, "%d o" % t) for r, t in trop_gros]),
            ("dans la liste mais introuvables",
             [("%s" % r, "") for r in disparus]))


def main():
    blanc = '--blanc' in sys.argv
    prefixe, chemins = lire_liste()
    if chemins is None:
        return 2
    a_copier, disparus, refuses, trop_gros = preparer_plan(chemins)
    total = sum(t for _r, _f, t in a_copier)

    print("=" * 60)
    print("COPIE POUR CLAUDE -- %s"
          % ("TEST A BLANC (rien n'est ecrit)" if blanc else "SYNCHRO REELLE"))
    print("=" * 60)
    print("liste    : %s" % LISTE.name)
    print("sortie   : %s" % SORTIE)
    print("prefixe  : %s" % (prefixe or "(aucun)"))
    print("a copier : %d fichier(s), %d o (~%d Ko)"
          % (len(a_copier), total, int(total / 1024)))
    print("disparus : %d" % len(disparus))
    print("interdits: %d" % len(refuses))
    print("trop gros: %d" % len(trop_gros))
    for titre, morceaux in _familles(disparus, refuses, trop_gros):
        if not morceaux:
            continue
        print("")
        print("-- %s --" % titre)
        for nom, detail in morceaux:
            print("   %s%s" % (nom, ("  ->  " + detail) if detail else ""))

    if blanc:
        print("")
        print("TEST A BLANC : rien n'a ete copie.")
        return 0

    maintenant = time.strftime('%d/%m/%Y %H:%M')
    derniere = lire_derniere_synchro(prefixe)
    SORTIE.mkdir(exist_ok=True)
    _vider_le_dossier()
    for rel, full, _taille in a_copier:
        shutil.copy2(full, SORTIE / nom_plat(rel, prefixe))
    ecrire_index(a_copier, disparus, refuses, trop_gros, maintenant, prefixe)
    ecrire_etat(a_copier, derniere, maintenant, prefixe)
    print("")
    print("SYNCHRO FAITE : %d fichier(s), %d o (~%d Ko)"
          % (len(a_copier), total, int(total / 1024)))
    print("dossier : %s" % SORTIE)
    print("a lire d'abord : %s" % nom_genere('ETAT_DU_JOUR.md', prefixe))
    return 0


if __name__ == '__main__':
    sys.exit(main())
