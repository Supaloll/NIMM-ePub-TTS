# -*- coding: utf-8 -*-
"""Fabrique des empreintes de voix KYUTAI a partir de fichiers WAV.

POURQUOI (idee de Laurent, 17/09/2026) : « si on peut prendre des extraits de
Edge, Kokoro, Piper pour les mettre dans Kyutai, on a tous les timbres en ayant
qu'un seul moteur ». C'est exactement ce que permet une empreinte.

Une voix Kyutai est un petit fichier `.safetensors` contenant les JETONS AUDIO
d'un extrait, encodes par le codec **Mimi** du moteur (cle `speaker_wavs`,
forme `(1, 512, T)` -- verifie le 17/09/2026 sur les 35 voix de la banque :
512 dimensions, 125 jetons pour ~5 s, soit 25 jetons par seconde).

Ce script encode donc n'importe quel WAV de ~5 s et range l'empreinte la ou le
service la trouvera :
    voix_fr/<nom>_enhanced.wav.1e68beda@240.safetensors   (voix francaises)
    voix_autres/<famille>/<nom>.wav.1e68beda@240.safetensors  (autres familles)
(voir `_repertorier_voix` dans servir_kyutai.py : c'est la partie avant
`_enhanced.wav` qui devient l'identifiant de la voix).

A LANCER AVEC LE PYTHON DU MOTEUR, ET MOTEUR ETEINT : ce script charge lui-meme
le modele (3,4 Go sur la carte graphique) et ne peut pas cohabiter avec le
service. En cas de doute, ferme la fenetre du service Kyutai d'abord.

Usage :
    .venv\\Scripts\\python.exe _fabriquer_empreintes.py --liste
    .venv\\Scripts\\python.exe _fabriquer_empreintes.py --source ..\\neutts_service\\references\\voix_libres_dp\\Femme001_reference.wav --nom Femme001 --ecrire
    .venv\\Scripts\\python.exe _fabriquer_empreintes.py --dossier ..\\neutts_service\\references\\voix_libres_dp --ecrire
"""

import argparse
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# torch.compile() est IMPOSSIBLE sous Windows (Triton n'existe pas) : sans ces
# deux lignes, le chargement du codec echoue avec « TritonMissing ». Le service
# Kyutai les met deja (voir servir_kyutai.py) ; nos outils doivent faire pareil.
os.environ.setdefault('NO_TORCH_COMPILE', '1')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

ICI = Path(__file__).resolve().parent
# ATTENTION : les voix francaises vivent dans un SOUS-DOSSIER precis
# (`voix_fr/cml-tts/fr`) -- c'est ce que le service explore, voir la constante
# DOSSIER_VOIX de servir_kyutai.py. Se tromper de dossier ne casse rien, mais
# la voix fabriquee reste invisible : le service ne bouge pas de nombre.
DOSSIER_VOIX = ICI / 'voix_fr' / 'cml-tts' / 'fr'
DOSSIER_AUTRES = ICI / 'voix_autres'
# Le codec DEDIE AUX VOIX (voir `charger_mimi`) : nom deduit de la signature et
# de l'epoque du modele, exactement comme le fait le script officiel de Kyutai.
DOSSIER_MODELE = ICI / 'modele'
NOM_MIMI_VOIX = '1e68beda_240_mimi_voice.safetensors'
REPO_MODELE = 'kyutai/tts-1.6b-en_fr'
# Le suffixe depend du modele (repere dans les noms de la banque) : on le lit
# sur place plutot que de le coder en dur.
SUFFIXE_DEFAUT = '.1e68beda@240.safetensors'
MARQUEUR = '_enhanced.wav'


def suffixe_du_modele():
    """Le suffixe des fichiers de la banque, s'il est present."""
    for dossier in (DOSSIER_VOIX, DOSSIER_AUTRES):
        for fichier in sorted(dossier.rglob('*.safetensors')):
            if MARQUEUR in fichier.name:
                return fichier.name.split(MARQUEUR)[1]
    return SUFFIXE_DEFAUT


def nom_de_voix(nom_fichier):
    """Identifiant lisible d'un WAV source.

    Les sources portent plusieurs suffixes selon leur origine :
        Femme001_reference.wav
        cml10065_enhanced_reference.wav
        ff_amelie_reference.wav
    On les retire tous, du plus long au plus court.
    """
    base = Path(nom_fichier).name
    for marque in ('_enhanced_reference.wav', '_reference.wav', '.wav'):
        if base.lower().endswith(marque):
            return base[:-len(marque)]
    return Path(base).stem


def charger_mimi(poids_force=None):
    """Le codec Mimi DEDIE AUX VOIX (16 codebooks), et non celui du modele TTS.

    POURQUOI C'EST LE POINT CLÉ (mesure du 17/09/2026) : les empreintes de la
    banque sont produites par un Mimi SEPARE, dont le poids doit etre un
    `*_mimi_voice.safetensors` chargé avec **16 codebooks**
    (`loaders._quantizer_kwargs["n_q"] = 16`) -- c'est ce que fait le script
    officiel de Kyutai. Avec le Mimi du modele TTS (32 codebooks), le latent
    sort a un ecart-type de **3,03** au lieu des **0,66** de la banque, et
    l'ecoute ne donne que des **gargouillis**.

    `poids_force` accepte soit un chemin, soit `depot:fichier` (telecharge
    depuis Hugging Face) : c'est ce qui permet d'ESSAYER un codec candidat
    (`kyutai/mimi:tts_b6369a24.safetensors`) et de MESURER l'ecart-type obtenu
    avant de fabriquer quoi que ce soit en serie.

    Bonus : ce codec seul est bien plus leger que le modele complet -- fabriquer
    des empreintes n'exige plus de charger les 3,4 Go du TTS.
    """
    import torch
    from moshi.models import loaders

    poids = None
    if poids_force and ':' in poids_force and not Path(poids_force).exists():
        from huggingface_hub import hf_hub_download
        depot, fichier = poids_force.split(':', 1)
        poids = Path(hf_hub_download(repo_id=depot, filename=fichier))
    elif poids_force:
        poids = Path(poids_force)
    elif DOSSIER_MODELE.is_dir():
        trouves = sorted(DOSSIER_MODELE.glob('*_mimi_voice.safetensors'))
        poids = trouves[0] if trouves else None
    if poids is None:
        from huggingface_hub import hf_hub_download
        try:
            poids = Path(hf_hub_download(repo_id=REPO_MODELE,
                                         filename=NOM_MIMI_VOIX))
        except Exception:
            print('ARRET : pas de codec voix trouve (ni --codec, ni %s dans %s).'
                  % (NOM_MIMI_VOIX, REPO_MODELE))
            sys.exit(1)

    print('Codec des voix : %s' % poids.name)
    appareil = 'cuda' if torch.cuda.is_available() else 'cpu'
    loaders._quantizer_kwargs['n_q'] = 16
    mimi = loaders.get_mimi(str(poids), device=appareil, num_codebooks=16)
    print('Codec charge (%s).' % appareil)
    return mimi


ETALON_ECART_TYPE = 0.66   # ecart-type des empreintes de la banque (mesure du 17/09)


def normaliser_volume(wav, frequence, headroom_db=22.0, plancher_energie=2e-3):
    """Ramene l'extrait a une amplitude de reference avant l'encodage.

    POURQUOI C'EST INDISPENSABLE (mesure du 17/09/2026) : sans normalisation,
    l'empreinte sortait avec un ecart-type de **0,069** au lieu des **0,658** de
    la banque -- un facteur 9,5 -- et le moteur ne produisait plus que des
    **gargouillis**.

    Le script OFFICIEL de Kyutai (`moshi/scripts/tts_make_voice.py`, option
    `--loudness-headroom 22`) mesure la loudness selon ITU-R BS.1770 avec
    `torchaudio`, qui n'est pas installe chez nous. On prend donc un RMS cible
    equivalent (une loudness de -22 LUFS correspond en pratique a un RMS
    d'environ -19 dBFS), et l'ecart-type du latent est de toute facon
    **recalibre** juste apres sur l'etalon de la banque : c'est cette
    recalibration qui garantit la bonne echelle.
    """
    if float(wav.std()) < plancher_energie:
        return wav
    cible = 10.0 ** (-19.0 / 20.0)
    return wav * (cible / float(wav.std()))


def encoder(mimi, chemin_wav, duree=10.0, headroom_db=22.0,
            quantize=False, etalonner=True, ** _ignore):
    """Encode un WAV avec Mimi -> tenseur (1, 512, jetons).

    Reproduit la methode du script officiel de Kyutai, dans cet ordre :
        1. lecture des `duree` premieres secondes (10 s par defaut, ce qui donne
           125 jetons a 12,5 jetons par seconde -- la taille de la banque) ;
        2. mixage en mono ;
        3. NORMALISATION du volume a -22 LUFS (sans elle : gargouillis) ;
        4. complement a `duree` exactement, par du silence ;
        5. encodage en latents NON quantifies (512 dimensions).
    """
    import numpy as np
    import sphn
    import torch
    import torch.nn.functional as F

    frequence = mimi.sample_rate
    appareil = next(mimi.parameters()).device
    donnees, _ = sphn.read(str(chemin_wav), 0.0, duree, sample_rate=frequence)
    longueur = int(frequence * duree)
    wav = torch.from_numpy(np.asarray(donnees)[:, :longueur]).float()
    wav = wav.mean(dim=0, keepdim=True)[None]          # mono : (1, 1, jetons)
    # PAS de gain RMS ici : mesure du 17/09/2026, un RMS cible de -19 dBFS
    # SATURE ces extraits (ils sont tres faibles au depart) et l'empreinte part
    # alors a 3,03 d'ecart-type. C'est l'ETALONNAGE plus bas -- qui vise
    # directement l'ecart-type de la banque -- qui regle l'echelle, proprement.
    manquant = longueur - wav.shape[-1]
    if manquant > 0:
        wav = F.pad(wav, (0, manquant))
    with torch.no_grad():
        jetons = mimi.encode_to_latent(wav.to(appareil), quantize=quantize)
        if etalonner:
            # L'ecart-type du latent suit l'amplitude du signal : on ajuste
            # l'extrait jusqu'a tomber sur l'etalon de la banque (0,66). C'est
            # cette recalibration qui garantit la bonne ECHELLE -- sans elle, le
            # moteur ne sort que des gargouillis (mesure du 17/09/2026).
            for _essai in range(3):
                ecart = float(jetons.float().std())
                if ecart <= 1e-6:
                    break
                facteur = ETALON_ECART_TYPE / ecart
                if abs(facteur - 1.0) < 0.02:
                    break
                wav = (wav * facteur).clamp(-0.99, 0.99)
                jetons = mimi.encode_to_latent(wav.to(appareil),
                                               quantize=quantize)
    return jetons.detach().cpu(), bool(np.asarray(donnees).shape[-1] < longueur)


def destination(nom, famille=None):
    """Le chemin du fichier d'empreinte, selon la convention du service."""
    suffixe = suffixe_du_modele()
    if famille:
        dossier = DOSSIER_AUTRES / famille
        return dossier / ('%s%s%s' % (nom, '.wav', suffixe))
    return DOSSIER_VOIX / ('%s%s%s' % (nom, MARQUEUR, suffixe))


def sources(dossier):
    """Les WAV d'un dossier (hors fichiers deja traites)."""
    return sorted(f for f in Path(dossier).rglob('*.wav'))


def main():
    analyseur = argparse.ArgumentParser(
        description="Fabrique des empreintes de voix Kyutai a partir de WAV.")
    analyseur.add_argument('--source', default=None,
                           help="un fichier WAV a transformer en voix")
    analyseur.add_argument('--dossier', default=None,
                           help="un dossier de WAV a transformer en voix")
    analyseur.add_argument('--nom', default=None,
                           help="identifiant de la voix (defaut : nom du fichier)")
    analyseur.add_argument('--famille', default=None,
                           help="range la voix dans voix_autres/<famille>")
    analyseur.add_argument('--codec', default=None,
                           help="codec Mimi a utiliser : un chemin, ou "
                                "depot:fichier (ex. kyutai/mimi:tts_b6369a24.safetensors)")
    analyseur.add_argument('--duree', type=float, default=10.0,
                           help="duree de l'extrait encode, en secondes (defaut "
                                "10, comme la banque : 125 jetons)")
    analyseur.add_argument('--non-quantifie', action='store_true',
                           help="(devenu inutile : le non quantifie est le defaut)"
                                " ; garde pour compatibilite")
    analyseur.add_argument('--manquantes', action='store_true',
                           help="ne fabriquer que les voix absentes du moteur "
                                "(ne JAMAIS ecraser la banque officielle)")
    analyseur.add_argument('--liste', action='store_true',
                           help="montre seulement ce qui serait fabrique")
    analyseur.add_argument('--ecrire', action='store_true',
                           help="ecrit vraiment les fichiers d'empreinte")
    options = analyseur.parse_args()

    if options.source:
        a_traiter = [(Path(options.source),
                      options.nom or nom_de_voix(options.source))]
    elif options.dossier:
        a_traiter = [(chemin, nom_de_voix(chemin))
                     for chemin in sources(options.dossier)]
    else:
        analyseur.print_help()
        return 1

    if options.manquantes:
        avant = len(a_traiter)
        a_traiter = [(chemin, nom) for chemin, nom in a_traiter
                     if not destination(nom, options.famille).exists()]
        print('')
        print('(--manquantes : %d voix deja presentes chez le moteur, laissees'
              ' telles quelles)' % (avant - len(a_traiter)))

    print('')
    print('=' * 70)
    print('FABRICATION D EMPREINTES DE VOIX KYUTAI')
    print('=' * 70)
    print('a fabriquer : %d voix' % len(a_traiter))
    deja = 0
    for chemin, nom in a_traiter[:10]:
        cible = destination(nom, options.famille)
        marque = ' (existe deja)' if cible.exists() else ''
        if cible.exists():
            deja += 1
        print('   %-34s -> %s%s' % (nom[:34], cible.name, marque))
    if len(a_traiter) > 10:
        print('   ... et %d autres' % (len(a_traiter) - 10))
    if deja:
        print('   (%d deja presentes : elles seront ecrasees seulement si'
              ' --ecrire)' % deja)

    if options.liste or not options.ecrire:
        print('')
        print("(rapport seul : rien n'a ete ecrit -- ajoute --ecrire)")
        return 0

    from safetensors.torch import save_file

    mimi = charger_mimi(options.codec)
    fabriquees = 0
    for chemin, nom in a_traiter:
        cible = destination(nom, options.famille)
        cible.parent.mkdir(parents=True, exist_ok=True)
        try:
            empreinte, complete = encoder(mimi, chemin,
                                          duree=options.duree,
                                          quantize=not options.non_quantifie)
        except Exception as erreur:
            print('   ECHEC %-30s : %s' % (nom[:30], erreur))
            continue
        save_file({'speaker_wavs': empreinte}, str(cible))
        fabriquees += 1
        plat = empreinte.float().reshape(-1)
        print('   OK    %-24s forme %-16s ecart-type %.3f  %s-> %s'
              % (nom[:24], tuple(empreinte.shape), float(plat.std()),
                 'COMPLETE ' if complete else '', cible.name))

    print('')
    print('empreintes fabriquees : %d' % fabriquees)
    print('A FAIRE ENSUITE : redemarrer le moteur Kyutai, puis verifier')
    print('                 que la voix apparait dans  GET /voix  et dans le')
    print('                 catalogue du lecteur (modules/tts.py).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
