# -*- coding: utf-8 -*-
"""Verifie qu'AUCUN secret ni aucune donnee personnelle ne part dans le depot.

Pourquoi ce test existe : le depot a ete reparti de zero le 15/09/2026 (« code
seul, aucun livre, aucune cle »), et l'item « Hygiene du depot » du BACKLOG
demande de garder cette promesse. Une cle d'API collee un soir dans un script
partirait au prochain `git push` sans que personne ne s'en apercoive -- ce test
l'attrape AVANT.

Ce qu'il regarde :
  1. les cles d'API ecrites EN CLAIR (sk-..., AIza..., gsk_..., hf_...,
     « Bearer <jeton> ») dans tous les fichiers que Git emporterait ;
  2. les fichiers sensibles qui seraient SUIVIS par Git (cles, config, base,
     annotations personnelles) ;
  3. les fichiers de donnees qui n'ont jamais a etre versionnes (audio, EPUB,
     base SQLite, environnement Python des moteurs).

Il regarde exactement ce que Git emporterait : fichiers suivis + fichiers
nouveaux NON ignores (`git ls-files --cached --others --exclude-standard`).
Usage : python test_voix/test_pas_de_secrets.py
"""

import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

ECHECS = 0

# Motifs de cles REELLES : un prefixe connu suivi d'une longue valeur, entre
# guillemets (donc une chaine ecrite en dur -- une variable lue depuis un
# fichier ou un os.environ ne ressemble pas a ca).
MOTIFS = (
    (r'''["'](?:sk-|hf_|gsk_)[A-Za-z0-9_\-]{16,}["']''', 'cle d API en clair'),
    (r'''["']AIza[0-9A-Za-z_\-]{20,}["']''', 'cle Google en clair'),
    (r'''["']Bearer\s+[A-Za-z0-9._\-]{24,}["']''', 'jeton Bearer en clair'),
)

# Fichiers qui ne doivent JAMAIS etre suivis par Git.
INTERDITS_SUIVIS = (
    'test_voix/cles_api.txt',
    'data/config.json',
    'data/annotations_voix.json',
    'data/moteur_voix.txt',
    'data/nimm_epub.db',
)

# Extensions de donnees qui n'ont rien a faire dans le depot.
EXTENSIONS_INTERDITES = ('.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aif',
                         '.aiff', '.epub', '.onnx', '.bin', '.db')

# On ne lit que du texte, et pas les gros fichiers.
EXTENSIONS_TEXTE = ('.py', '.js', '.html', '.css', '.bat', '.cmd', '.md',
                    '.json', '.txt', '.csv', '.yml', '.yaml', '.toml', '.cfg',
                    '.ini', '.sh', '.ps1')
TAILLE_MAX = 2 * 1024 * 1024


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def fichiers_du_depot():
    """Ce que Git emporterait : suivis + nouveaux non ignores."""
    resultat = subprocess.run(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
        capture_output=True, text=True, encoding='utf-8', cwd=str(RACINE))
    if resultat.returncode != 0:
        return None, resultat.stderr.strip()
    return [ligne for ligne in resultat.stdout.splitlines() if ligne.strip()], ''


def fichiers_suivis():
    """Les fichiers reellement versionnes (suivis par Git)."""
    resultat = subprocess.run(['git', 'ls-files'], capture_output=True,
                              text=True, encoding='utf-8', cwd=str(RACINE))
    return [ligne for ligne in resultat.stdout.splitlines() if ligne.strip()]



def main():
    print('')
    print('=' * 68)
    print('VERIFICATION : ce que le depot peut emporter (secrets, donnees)')
    print('=' * 68)

    a_committer, erreur = fichiers_du_depot()
    verifier('la liste des fichiers a committer a pu etre lue',
             a_committer is not None, erreur)
    if a_committer is None:
        return 1
    suivis = fichiers_suivis()

    # 1) Les cles en clair, fichier par fichier.
    trouvailles = []
    lus = 0
    for relatif in a_committer:
        chemin = RACINE / relatif
        if chemin.suffix.lower() not in EXTENSIONS_TEXTE:
            continue
        try:
            if chemin.stat().st_size > TAILLE_MAX:
                continue
            texte = chemin.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        lus += 1
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for motif, description in MOTIFS:
                if re.search(motif, ligne):
                    trouvailles.append('%s:%d  (%s)' % (relatif, numero,
                                                        description))
    print('  (%d fichiers de texte examines)' % lus)
    verifier('aucune cle d API en clair', not trouvailles, trouvailles[:10])

    # 2) Les fichiers sensibles ne doivent pas etre suivis.
    sensibles = [nom for nom in INTERDITS_SUIVIS if nom in suivis]
    verifier('aucun fichier sensible suivi par Git', not sensibles, sensibles)

    # 3) Aucune donnee lourde ou sous droits dans le depot.
    donnees = [nom for nom in suivis
               if Path(nom).suffix.lower() in EXTENSIONS_INTERDITES]
    verifier('aucun audio, EPUB ni base SQLite versionne', not donnees,
             donnees[:10])

    # 4) Les environnements Python des moteurs restent dehors.
    environnements = [nom for nom in a_committer
                      if '/.venv/' in '/' + nom.replace('\\', '/')]
    verifier('aucun environnement Python des moteurs', not environnements,
             environnements[:5])

    # 5) Les references audio de NeuTTS (extraits, meme libres de droits) non plus.
    references = [nom for nom in a_committer if 'neutts_service/references' in
                  nom.replace('\\', '/')]
    verifier('aucun extrait de reference NeuTTS versionne', not references,
             references[:5])

    print('')
    if ECHECS:
        print('N ECHEC : %d controle(s) en erreur.' % ECHECS)
        return 1
    print('TOUT EST OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())

