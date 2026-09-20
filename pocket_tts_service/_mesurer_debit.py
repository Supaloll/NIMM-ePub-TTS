# -*- coding: utf-8 -*-
"""Mesure le DEBIT REEL de Pocket TTS sur cette machine (etape 1 du chantier).

Pourquoi ce script : le modele francais tourne a environ 1x le temps reel chez
l'atelier NIMM Voix (variante 24l non distillee). C'est LE chiffre qui decide
de tout : s'il faut pre-generer les chapitres, ou si la lecture a la volee est
envisageable avec le cache audio.

Ce qu'il fait, dans l'ordre :
  1. charge le modele francais (french_24l) et CHRONOMETRE le chargement ;
  2. charge la voix de reference demandee et chronometre l'encodage ;
  3. lit 3 phrases francaises de longueurs differentes (le meme texte que les
     lots d'ecoute de l'atelier) en chronometrant chacune ;
  4. ecrit les WAV dans sortie_mesure\\ (pour l'oreille) et un rapport lisible.

Usage (depuis pocket_tts_service) :
    .venv\\Scripts\\python.exe _mesurer_debit.py
    .venv\\Scripts\\python.exe _mesurer_debit.py --voix voix\\Homme002_reference.wav
    .venv\\Scripts\\python.exe _mesurer_debit.py --quantize --threads 4
"""

import argparse
import ctypes
import ctypes.wintypes
import sys
import time
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

ICI = Path(__file__).resolve().parent
LANGUE = 'french_24l'
LONGUEUR_REFERENCE = 275     # le texte des lots d'ecoute de l'atelier

# Trois phrases de longueurs differentes (Monte-Cristo, domaine public) : la
# courte dit si le moteur decroche sur les repliques, la longue si le texte
# au-dela de ~350 caracteres est saute (defaut connu du moteur).
PHRASES = [
    ("courte", "Non."),
    ("moyenne", "Le 24 fevrier 1815, la vigie de Notre-Dame de la Garde signala "
                "le trois-mats le Pharaon, venant de Smyrne, Trieste et Naples."),
    ("longue", "Comme d'habitude, un pilote cotier partit aussitot du port, rasa "
               "le chateau d'If, et alla aborder le navire entre le cap de "
               "Morgion et l'ile de Rion ; puis il jeta l'ancre, et le jeune "
               "homme que l'on voyait sur le pont se disposa a remplir son "
               "devoir, en donnant ses ordres pour le dechargement."),
]


def memoire_mo():
    """(memoire courante, pic) du processus, en Mo -- sans dependance externe."""
    class Compteurs(ctypes.Structure):
        _fields_ = [('cb', ctypes.wintypes.DWORD),
                    ('PageFaultCount', ctypes.wintypes.DWORD),
                    ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                    ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t)]
    compteurs = Compteurs()
    compteurs.cb = ctypes.sizeof(Compteurs)
    # ATTENTION (piege paye le 20/09/2026) : sans argtypes/restype explicites,
    # Windows tronque le handle du processus a 32 bits et l'appel renvoie
    # toujours 0 -- on croyait lire 0 Mo alors que le modele etait en memoire.
    noyau = ctypes.windll.kernel32
    noyau.GetCurrentProcess.restype = ctypes.wintypes.HANDLE
    psapi = ctypes.windll.psapi
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.wintypes.HANDLE,
                                           ctypes.POINTER(Compteurs),
                                           ctypes.wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL
    ok = psapi.GetProcessMemoryInfo(noyau.GetCurrentProcess(),
                                    ctypes.byref(compteurs), compteurs.cb)
    if not ok:
        return 0.0, 0.0
    return (compteurs.WorkingSetSize / 1048576.0,
            compteurs.PeakWorkingSetSize / 1048576.0)


def duree_du_wav(chemin):
    """Duree reelle du fichier ecrit : on le RELIT (jamais de calcul de tete)."""
    with wave.open(str(chemin), 'rb') as fichier:
        return fichier.getnframes() / float(fichier.getframerate())


def main():
    analyseur = argparse.ArgumentParser(
        description="Mesure le debit reel de Pocket TTS (francais).")
    analyseur.add_argument('--voix',
                           default=str(ICI / 'voix' / 'Femme001_reference.wav'),
                           help='WAV de reference de la voix (defaut : Femme001)')
    analyseur.add_argument('--quantize', action='store_true',
                           help='modele int8 (-48 %% de memoire, +27 %% de vitesse ; exige torchao)')
    analyseur.add_argument('--threads', type=int, default=0,
                           help='nombre de coeurs a utiliser (0 = laisser PyTorch decider)')
    analyseur.add_argument('--sortie', default=str(ICI / 'sortie_mesure'),
                           help='dossier des WAV produits')
    options = analyseur.parse_args()

    import numpy as np            # noqa: F401  (pocket_tts en depend de toute facon)
    import scipy.io.wavfile
    import torch

    if options.threads > 0:
        torch.set_num_threads(options.threads)

    lignes = []
    def dire(texte):
        print(texte)
        lignes.append(texte)

    dire('')
    dire('=' * 70)
    dire('MESURE DU DEBIT -- Pocket TTS, langue %s' % LANGUE)
    dire('=' * 70)
    dire('version de PyTorch : %s' % torch.__version__)
    dire('coeurs utilises par PyTorch : %d' % torch.get_num_threads())
    dire('voix de reference : %s' % options.voix)
    dire('quantification int8 : %s' % ('oui' if options.quantize else 'non'))
    ram0, _ = memoire_mo()
    dire('memoire avant chargement : %.0f Mo' % ram0)

    from pocket_tts import TTSModel

    debut = time.time()
    modele = TTSModel.load_model(language=LANGUE, quantize=options.quantize)
    chargement = time.time() - debut
    ram1, pic1 = memoire_mo()
    dire('')
    dire('1) chargement du modele : %.1f s   (memoire %.0f Mo, pic %.0f Mo)'
         % (chargement, ram1, pic1))

    debut = time.time()
    etat_voix = modele.get_state_for_audio_prompt(options.voix)
    encodage = time.time() - debut
    dire('2) encodage de la voix  : %.1f s' % encodage)

    dossier = Path(options.sortie)
    dossier.mkdir(parents=True, exist_ok=True)

    dire('')
    dire('3) generation phrase par phrase (max_tokens = 200, recette de l\'atelier)')
    dire('   %-8s %8s %9s %8s   %s' % ('phrase', 'car.', 'audio', 'calcul', 'ratio'))
    dire('   ' + '-' * 64)
    resultats = []
    for nom, texte in PHRASES:
        debut = time.time()
        audio = modele.generate_audio(etat_voix, texte, max_tokens=200)
        calcul = time.time() - debut
        donnees = audio.detach().cpu().numpy()
        if donnees.ndim == 2 and donnees.shape[0] <= 2:
            donnees = donnees.T          # [canaux, echantillons] -> [echantillons, canaux]
        # Ecriture en PCM 16 bits : c'est le format des autres WAV du projet,
        # lisible par tout le monde -- et par le module `wave` de Python, qui
        # refuse le float32 de scipy (piege paye le 20/09/2026 : "unknown
        # format: 3", soit le format IEEE float).
        if donnees.dtype.kind == 'f':
            donnees = np.clip(donnees, -1.0, 1.0)
            donnees = (donnees * 32767.0).astype('int16')
        chemin = dossier / ('%s_%s.wav' % (nom, Path(options.voix).stem))
        scipy.io.wavfile.write(str(chemin), modele.sample_rate, donnees)
        duree = duree_du_wav(chemin)     # on relit le fichier ecrit
        ratio = calcul / duree if duree else 0.0
        resultats.append((nom, len(texte), duree, calcul, ratio))
        dire('   %-8s %8d %7.1f s %7.1f s %8.2f'
             % (nom, len(texte), duree, calcul, ratio))

    ram2, pic2 = memoire_mo()
    ratios = [r[4] for r in resultats]
    durees = sum(r[2] for r in resultats)
    calcule = sum(r[3] for r in resultats)
    ratio_moyen = (calcule / durees) if durees else 0.0

    dire('')
    dire('4) BILAN')
    dire('   ratio moyen (calcul / audio) : %.2f' % ratio_moyen)
    dire('   pour 1 h d\'audio           : %.0f min de calcul'
         % (ratio_moyen * 60))
    dire('   ratio le plus rapide        : %.2f  (phrase %s)'
         % (min(ratios), resultats[ratios.index(min(ratios))][0]))
    dire('   ratio le plus lent          : %.2f  (phrase %s)'
         % (max(ratios), resultats[ratios.index(max(ratios))][0]))
    dire('   memoire : %.0f Mo apres le calcul, pic %.0f Mo' % (ram2, pic2))
    if ratio_moyen <= 0.5:
        verdict = "RAPIDE : la lecture a la volee est envisageable (avec le cache)."
    elif ratio_moyen <= 1.2:
        verdict = ("LENT (environ 1x le temps reel) : PRE-GENERER les chapitres, "
                   "le cache audio prenant le relais ensuite.")
    else:
        verdict = ("TRES LENT : PRE-GENERER obligatoirement, et prevoir un delai "
                   "audible entre deux chapitres non encore generes.")
    dire('   VERDICT : %s' % verdict)
    dire('')
    dire('   Fichiers a ecouter : %s' % dossier)
    dire('FIN')

    (dossier / 'rapport_mesure.txt').write_text('\n'.join(lignes), encoding='utf-8')


if __name__ == '__main__':
    main()

