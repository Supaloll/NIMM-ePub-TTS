# -*- coding: utf-8 -*-
"""Script JETABLE -- verifie la logique de demarrage du moteur de voix.

Ce que le script controle, sans RIEN lancer (ni moteur, ni lecteur) :
  1. les deux lanceurs ecrivent bien leur nom dans data\\moteur_voix.txt ;
  2. START.bat lit ce fichier et choisit le bon moteur ;
  3. les cas limites : aucun fichier, "aucun", nom inconnu, espaces parasites.

Methode : une COPIE de START.bat est fabriquee avec les commandes qui
lancent reellement quelque chose (start ... et python main.py) remplacees
par des affichages, et le "pause" final retire. Rien n'est donc execute.

A lancer avec le Python du lecteur :
    python test_voix/test_start_moteur.py
"""

import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

REGLE = RACINE / "data" / "moteur_voix.txt"
COPIE = RACINE / "_test_start_neutre.bat"
ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def fabriquer_copie_neutre():
    """Copie de START.bat ou rien ne se lance vraiment."""
    source = (RACINE / "START.bat").read_text(encoding='utf-8', errors='replace')
    remplacements = [
        ('start "NIMM ePub - moteur de voix XTTS v2" /D "%~dp0xtts_service" cmd /k DEMARRER_XTTS.bat',
         'echo [NEUTRE] ici serait lance : XTTS v2'),
        ('start "NIMM ePub - moteur de voix Kyutai" /D "%~dp0kyutai_service" cmd /k DEMARRER_KYUTAI.bat',
         'echo [NEUTRE] ici serait lance : Kyutai'),
        ('python main.py', 'echo [NEUTRE] ici le lecteur demarrerait'),
        ('pause', ''),
    ]
    for avant, apres in remplacements:
        source = source.replace(avant, apres)
    COPIE.write_text(source, encoding='utf-8')
    return source


def lancer_start(contenu_regle):
    """Ecrit le fichier de regle demande puis execute la copie neutre."""
    if contenu_regle is None:
        if REGLE.exists():
            REGLE.unlink()
    else:
        REGLE.write_text(contenu_regle, encoding='utf-8')
    r = subprocess.run(['cmd', '/c', COPIE.name], cwd=str(RACINE),
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    return (r.stdout or '') + (r.stderr or '')


def test_ecriture_par_les_lanceurs():
    """Les deux lignes ajoutees aux lanceurs ecrivent-elles le bon nom ?"""
    print('')
    print('1) ce que les lanceurs ecrivent dans data\\moteur_voix.txt')
    temoin = RACINE / "data" / "_test_ecriture.txt"
    for dossier, attendu in (("xtts_service", "xtts"), ("kyutai_service", "kyutai")):
        if temoin.exists():
            temoin.unlink()
        commande = '> "..\\data\\_test_ecriture.txt" echo %s' % attendu
        subprocess.run(commande, cwd=str(RACINE / dossier), shell=True,
                       capture_output=True, text=True)
        contenu = temoin.read_text(encoding='utf-8').strip() if temoin.exists() else ''
        verifier('%s -> ecrit "%s"' % (dossier, attendu), contenu == attendu,
                 'contenu lu : %r' % contenu)
    if temoin.exists():
        temoin.unlink()


def test_choix_du_moteur():
    print('')
    print('2) ce que START.bat choisit selon le fichier de regle')
    cas = [
        (None,           'XTTS v2 (le dernier utilise)'),   # pas de fichier -> defaut
        ('xtts',         'XTTS v2 (le dernier utilise)'),
        ('kyutai',       'Kyutai (le dernier utilise)'),
        ('aucun',        'AUCUN - choix enregistre'),
        ('bidule',       "n'est pas un nom connu"),
        ('xtts\r\n',     'XTTS v2 (le dernier utilise)'),   # saut de ligne final
        ('  kyutai  \n', 'Kyutai (le dernier utilise)'),     # espaces parasites
    ]
    for contenu, attendu in cas:
        sortie = lancer_start(contenu)
        etiquette = 'aucun fichier' if contenu is None else repr(contenu)
        lignes = ' | '.join(l.strip() for l in sortie.splitlines() if l.strip())
        verifier('regle %-16s -> %s' % (etiquette, attendu),
                 attendu in sortie, 'sortie : ' + lignes[:160])


def test_garde_fou_deja_en_marche():
    print('')
    print('3) garde-fous presents dans les deux branches')
    source = COPIE.read_text(encoding='utf-8')
    for port in ('8083', '8082'):
        verifier('le port %s est teste avant tout lancement' % port,
                 ('127.0.0.1:%s/sante' % port) in source)
    verifier('deux tests du port, un par moteur',
             source.count('if not errorlevel 1 (') == 2,
             source.count('if not errorlevel 1 ('))
    verifier('les deux environnements sont verifies avant de lancer',
             'xtts_service\\.venv' in source and 'kyutai_service\\.venv' in source)


def test_parentheses_dans_les_blocs():
    """Piege cmd : dans un bloc ( ... ), une parenthese DANS UN TEXTE ferme
    le bloc -- le reste de la ligne devient une erreur de syntaxe
    (constate le 14/09/2026 : "echo ... (choix enregistre).").
    On verifie donc qu'aucun message affiche dans un bloc n'en contient."""
    print('')
    print('4) aucun message dans un bloc ne contient de parenthese')
    profondeur = 0
    fautives = []
    for numero, ligne in enumerate(
            (RACINE / "START.bat").read_text(encoding='utf-8').splitlines(), 1):
        nue = ligne.strip()
        dans_bloc = profondeur > 0
        if dans_bloc and nue.lower().startswith('echo') and ('(' in nue or ')' in nue):
            fautives.append('ligne %d : %s' % (numero, nue))
        # A jour de la profondeur : une ligne qui ouvre un bloc se termine par (
        if nue.endswith('('):
            profondeur += 1
        elif nue == ')':
            profondeur -= 1
    verifier('aucun echo de bloc ne contient de parenthese',
             not fautives, ' | '.join(fautives))


def test_parcours_complet():
    """A quoi ressemble ce que Laurent verra a l'ecran ?"""
    print('')
    print('5) parcours complet, tel qu affiche a l ecran (regle = "xtts")')
    sortie = lancer_start('xtts')
    for ligne in sortie.splitlines():
        if ligne.strip() and not ligne.startswith('Microsoft'):
            print('      ' + ligne.rstrip())


def main():
    print('=' * 66)
    print('VERIFICATION : demarrage du moteur de voix par START.bat')
    print('=' * 66)

    regle_avant = REGLE.read_text(encoding='utf-8') if REGLE.exists() else None
    try:
        fabriquer_copie_neutre()
        test_ecriture_par_les_lanceurs()
        test_choix_du_moteur()
        test_garde_fou_deja_en_marche()
        test_parentheses_dans_les_blocs()
        test_parcours_complet()
    finally:
        if COPIE.exists():
            COPIE.unlink()
        if regle_avant is None:
            if REGLE.exists():
                REGLE.unlink()
        else:
            REGLE.write_text(regle_avant, encoding='utf-8')

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('(fichier de regle et copie de test nettoyes)')
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
