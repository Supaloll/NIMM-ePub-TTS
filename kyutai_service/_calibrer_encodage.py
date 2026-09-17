# -*- coding: utf-8 -*-
"""Calibre l'encodage d'une empreinte de voix Kyutai, en comparant a la banque.

QUESTION A LAQUELLE IL REPOND (17/09/2026) : nos empreintes fabriquees donnent
des **gargouillis**. Est-ce parce que le CODEC est le mauvais, ou seulement
parce que le NIVEAU du signal est mauvais ?

Comment on tranche, sans deviner : on prend une voix dont on a **le WAV et
l'empreinte officielle** (les 35 voix de la banque, cote a cote dans
`kyutai_service/voix_fr/cml-tts/fr/` et dans les references), on encode ce WAV
nous-memes avec PLUSIEURS gains, et pour chacun on mesure :

    - l'ecart-type du latent (la banque est a ~0,66) ;
    - la CORRELATION avec l'empreinte officielle de la meme voix.

Si une valeur de gain donne a la fois l'ecart-type de la banque ET une forte
correlation, alors le codec du modele convient : c'etait juste une question
d'echelle, et la fabrication est sauvable. Si aucune correlation n'apparait,
c'est bien le codec qui differe, et il faudra une autre source pour les voix.

Usage (avec l'environnement du moteur) :
    .venv\\Scripts\\python.exe _calibrer_encodage.py
    .venv\\Scripts\\python.exe _calibrer_encodage.py --wav <chemin.wav> --empreinte <chemin.safetensors>
"""

import argparse
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# torch.compile() est IMPOSSIBLE sous Windows (Triton n'existe pas) : sans ces
# deux lignes, le chargement du codec echoue avec « TritonMissing ». Le service
# Kyutai les met deja (voir servir_kyutai.py) ; nos outils doivent faire pareil.
os.environ.setdefault('NO_TORCH_COMPILE', '1')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

ICI = Path(__file__).resolve().parent
DOSSIER_VOIX = ICI / 'voix_fr' / 'cml-tts' / 'fr'
REPO_MODELE = 'kyutai/tts-1.6b-en_fr'
NOM_CODEC_TTS = 'tokenizer-e351c8d8-checkpoint125.safetensors'
# Gains essayes : de "tel quel" a "20 fois plus fort". Le vrai script officiel
# normalise le volume (cible -22 LUFS), donc un gain est attendu.
GAINS = (1.0, 2.0, 4.0, 6.0, 9.5, 14.0, 20.0, 40.0)


def charger_codec(nom=NOM_CODEC_TTS, codebooks=32):
    """Le codec Mimi du modele TTS (celui qui sert a LIRE les voix)."""
    import torch
    from huggingface_hub import hf_hub_download
    from moshi.models import loaders

    chemin = Path(hf_hub_download(repo_id=REPO_MODELE, filename=nom))
    appareil = 'cuda' if torch.cuda.is_available() else 'cpu'
    loaders._quantizer_kwargs['n_q'] = codebooks
    return loaders.get_mimi(str(chemin), device=appareil,
                            num_codebooks=codebooks)


def encoder_avec_gain(mimi, chemin_wav, gain, duree=10.0):
    """Encode un WAV avec un gain donne. Renvoie (latent, ecrasement)."""
    import numpy as np
    import sphn
    import torch

    frequence = mimi.sample_rate
    appareil = next(mimi.parameters()).device
    donnees, _ = sphn.read(str(chemin_wav), 0.0, duree, sample_rate=frequence)
    longueur = int(frequence * duree)
    wav = torch.from_numpy(np.asarray(donnees)[:, :longueur]).float()
    wav = wav.mean(dim=0, keepdim=True)[None]
    wav = wav - wav.mean(dim=-1, keepdim=True)
    gain_reel = gain
    pic = float(wav.abs().max())
    if pic * gain > 0.99:                      # on evite la saturation
        gain_reel = 0.99 / pic
    wav = wav * gain_reel
    manquant = longueur - wav.shape[-1]
    if manquant > 0:
        wav = torch.nn.functional.pad(wav, (0, manquant))
    with torch.no_grad():
        latent = mimi.encode_to_latent(wav.to(appareil), quantize=False)
    return latent[0].detach().cpu(), (gain_reel != gain)


def correlation(a, b):
    """Correlation de Pearson entre deux tenseurs de meme forme."""
    import torch

    x = a.float().reshape(-1)
    y = b.float().reshape(-1)
    if x.shape != y.shape:
        return None
    x = x - x.mean()
    y = y - y.mean()
    denominateur = float(x.norm() * y.norm())
    return float((x * y).sum() / denominateur) if denominateur else None


def paire_a_tester(dossier_wav):
    """Trouve un WAV dont l'empreinte officielle existe, et la renvoie."""
    from safetensors.torch import load_file   # noqa: F401 (verifie la presence)

    empreintes = {}
    for fichier in sorted(DOSSIER_VOIX.glob('*.safetensors')):
        if '_enhanced.wav' in fichier.name:
            empreintes[fichier.name.split('_enhanced.wav')[0]] = fichier
    for wav in sorted(Path(dossier_wav).glob('*.wav')):
        nom = wav.name
        # Deux conventions rencontrees : `<id>_enhanced.wav` (le WAV d'origine de
        # la banque) et `<id>_enhanced_reference.wav` (nos copies de reference).
        for marque in ('_enhanced_reference.wav', '_reference.wav',
                       '_enhanced.wav', '.wav'):
            if nom.endswith(marque):
                nom = nom[:-len(marque)]
                break
        if nom in empreintes:
            return wav, empreintes[nom]
    return None, None


def main():
    from safetensors.torch import load_file

    analyseur = argparse.ArgumentParser(
        description="Calibre l'encodage d'une empreinte de voix Kyutai.")
    analyseur.add_argument('--wav', default=None, help="WAV a encoder")
    analyseur.add_argument('--empreinte', default=None,
                           help="empreinte officielle de la meme voix")
    analyseur.add_argument('--dossier-wav', default=None,
                           help="dossier ou chercher une paire (defaut : "
                                "neutts_service/references/cml_tts)")
    options = analyseur.parse_args()

    dossier = Path(options.dossier_wav) if options.dossier_wav else (
        ICI.parent / 'neutts_service' / 'references' / 'cml_tts')
    if options.wav and options.empreinte:
        wav, empreinte = Path(options.wav), Path(options.empreinte)
    else:
        wav, empreinte = paire_a_tester(dossier)

    print('')
    print('=' * 74)
    print('CALIBRAGE DE L ENCODAGE (comparaison avec la banque Kyutai)')
    print('=' * 74)
    if not wav or not empreinte:
        print('ERR : aucune paire (WAV + empreinte officielle) trouvee.')
        print('      dossier teste : %s' % dossier)
        return 1
    print('WAV        : %s' % wav.name)
    print('empreinte  : %s' % empreinte.name)

    officielle = load_file(str(empreinte))['speaker_wavs'][0]
    print('')
    print('  banque   : forme %-14s ecart-type %.4f'
          % (tuple(officielle.shape), float(officielle.float().std())))

    mimi = charger_codec()
    print('')
    print('  %-7s %-12s %-12s %-10s %s'
          % ('gain', 'ecart-type', 'correlation', 'sature', 'verdict'))
    meilleur = None
    for gain in GAINS:
        latent, sature = encoder_avec_gain(mimi, wav, gain)
        ecart = float(latent.float().std())
        corr = correlation(latent, officielle)
        verdict = ''
        if corr is not None and corr > 0.7:
            verdict = 'CORRELE : le codec convient, seule l echelle differe'
            if meilleur is None or corr > meilleur[1]:
                meilleur = (gain, corr)
        elif corr is not None and corr > 0.3:
            verdict = 'correlation partielle'
        print('  %-7.1f %-12.4f %-12s %-10s %s'
              % (gain, ecart,
                 ('%.3f' % corr) if corr is not None else 'formes differentes',
                 'oui' if sature else 'non', verdict))

    print('')
    if meilleur:
        print("CONCLUSION : au gain %.1f, la correlation avec la banque est de "
              "%.3f." % meilleur)
        print("Le codec du modele convient donc -- il faut seulement REGLER LE")
        print("GAIN avant d'encoder, et l'ecoute doit confirmer.")
    else:
        print("CONCLUSION : aucune correlation nette avec la banque. Le codec du")
        print("modele TTS ne reproduit donc pas les empreintes officielles :")
        print("fabriquer une voix neuve demanderait le codec d'origine (non publie).")
    print('RAPPEL : aucune fabrication en serie avant une ECCOUTE de controle.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
