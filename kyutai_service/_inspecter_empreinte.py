# -*- coding: utf-8 -*-
"""Que contient une empreinte de voix Kyutai ? (lecture seule)

Une voix Kyutai n'est ni un modele ni un audio : c'est un petit fichier
`.safetensors` -- les JETONS AUDIO d'un extrait de reference, encodes par le
codec Mimi du moteur. C'est ce qui permet de FABRIQUER une voix a partir d'un
extrait : on encode l'extrait, on range le tenseur sous la cle `speaker_wavs`,
et le moteur la reconnait.

Cet outil sert a repondre a une question precise avant d'en fabriquer :
quelle est la FORME attendue, et combien de morceaux (de « voix ») un fichier
peut contenir ?

Usage (avec l'environnement du moteur) :
    .venv\\Scripts\\python.exe _inspecter_empreinte.py
    .venv\\Scripts\\python.exe _inspecter_empreinte.py voix_fr\\cml-tts\\fr
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ICI = Path(__file__).resolve().parent


def inspecter(dossier):
    from safetensors.torch import load_file

    fichiers = sorted(Path(dossier).glob('*.safetensors'))
    print('')
    print('=' * 70)
    print('EMPREINTES DE VOIX KYUTAI')
    print('=' * 70)
    print('dossier : %s' % dossier)
    print('fichiers : %d' % len(fichiers))
    if not fichiers:
        return 1
    for fichier in fichiers[:3]:
        stats(load_file(str(fichier)), fichier.name)
    print('')
    print("A SAVOIR : la forme se lit (blocs, jetons, dimensions). Une empreinte")
    print("couvre quelques secondes d'audio ; le moteur en accepte jusqu'a 5 par")
    print("voix (make_condition_attributes, moshi/models/tts.py).")
    print("Les STATISTIQUES disent si le contenu ressemble a celui de la banque :")
    print("une empreinte fabriquee a la meme forme mais une echelle tres")
    print("differente donne des gargouillis a l'ecoute.")
    return 0


def stats(donnees, titre):
    """Forme et statistiques d'une empreinte (pour comparer deux origines)."""
    print('')
    print('  %s' % titre)
    for cle, tenseur in donnees.items():
        plat = tenseur.float().reshape(-1)
        print('     cle %-16s forme %-18s type %s'
              % (cle, tuple(tenseur.shape), tenseur.dtype))
        print('        min %.4f   max %.4f   moyenne %.4f   ecart-type %.4f'
              % (float(plat.min()), float(plat.max()),
                 float(plat.mean()), float(plat.std())))


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--fichier':
        from safetensors.torch import load_file
        chemin = Path(sys.argv[2])
        print('')
        print('=' * 70)
        print('EMPREINTE DE VOIX KYUTAI')
        print('=' * 70)
        stats(load_file(str(chemin)), chemin.name)
        sys.exit(0)
    dossier = sys.argv[1] if len(sys.argv) > 1 else (ICI / 'voix_fr' / 'cml-tts' / 'fr')
    sys.exit(inspecter(dossier))
