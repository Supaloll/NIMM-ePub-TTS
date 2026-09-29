# -*- coding: utf-8 -*-
"""Appareil de voix qwentts.cpp -- service local de NIMM ePub (port 8086).

CE QUE C'EST : Qwen3-TTS **en C++/GGML** (`qwentts.cpp`), donc SANS PyTorch et
SANS carte graphique : il tourne sur le PROCESSEUR, ce qui laisse la carte libre
pour Kyutai ou Pocket. Il remplace notre ancien service Transformers
(`qwen_tts_service/`), qui demandait Python 3.12 + PyTorch + 2,6 a 3,8 Go de
carte, et qui n'arrivait qu'a x0,45 a x0,51 le temps reel.

VALIDATION (28/09/2026) : Laurent a ECOUTE et valide -- « c'est vraiment bon,
pas d'accrocs, prosodie impec, on a notre moteur ! » -- sur un banc d'ecoute
100 % Qwen (le chapitre d'essai, 15 personnages et le narrateur).

CONTRAT, le meme que tous nos services de voix :
    GET  /sante      -> {"pret": true, ...} : c'est LUI qui decide de tout, car
                        tant qu'il ne repond pas, le lecteur ne propose AUCUNE
                        voix `qwen:` (choix du 14/09/2026) ;
    GET  /voix       -> {"voix": [...], "nombre": N}
    POST /tts        -> {"texte": "...", "voix": "..."} -> OCTETS WAV
    POST /recharger  -> re-scanne le dossier des voix sans recharger le moteur.

DEUX CHOIX DE MISE EN OEUVRE, mesures le 28/09/2026 (3 prises par reglage) :
  1. on consomme le FLUX du moteur (`stream`) -- son mode le plus rapide, **x0,94
     le temps reel** contre x0,66 sans le chevauchement -- puis on rend un WAV
     COMPLET : le contrat ne bouge pas pour le lecteur, et le defaut des « 2 s
     perdues » du flux disparait puisqu'on le consomme jusqu'au bout ;
  2. les trois reglages qui font ce gain : fils dedies au decodage du codec,
     livraison par tranches de 2 images, et priorite d'entame. Cette derniere
     EXIGE les deux autres : le moteur REFUSE au lieu de degrader en silence.

LES VOIX : les 35 memes extraits que Kyutai (`qwen_tts_service/voix/`, avec leur
TEXTE exact dans `references.csv`), lues ici avec le meme identifiant que dans le
lecteur : `10087_11650_000028-0002`, sans le suffixe du fichier. Le texte active
le mode **ICL** (reference plus son texte), celui qui ameliore la ressemblance.

CE QU'ON SAIT DU MOTEUR (i5-12400F, 6 coeurs, mesures des 28 et 29/09/2026) :
  - chargement 1,4 a 2,2 s ; premier son 0,51 a 0,63 s (a chaud : 5,0 a 5,6 s
    sur la TOUTE premiere phrase d'un moteur fraichement charge) ;
  - debit x0,94 le temps reel le 28/09 (Q8_0, flux, trois reglages) ; **x1,04 a
    x1,20 le 29/09 avec les GGUF Q4_K_M** (banc de debit : 4, 6, 8 et 12 coeurs
    mesures -- 6 coeurs, le reglage de ce service, est le MEILLEUR ; 12 coeurs
    tombent a x0,25, l'hyperthreading cassant tout) ;
  - 1,2 Go de fichiers sur le disque (Q4_K_M : 884 Mo au lieu de 1,2 Go),
    AUCUNE carte graphique ;
  - le PREMIER appel d'une voix est plus lent (empreinte a preparer, une fois par
    voix : x0,53 puis x0,93). `NIMM_QWENTTS_PRECHAUFFE=1` les prepare en tache de
    fond au demarrage : desactive par defaut, a decider a l'usage -- Laurent a
    trouve cette attente perfectible le 28/09/2026.

Lancement : DEMARRER_QWENTTS_CPP.bat
Variables : NIMM_QWENTTS_PORT (8086), _HOST, _VOIX, _LANGUE (french),
            _CODEC_FILS (4), _FRAMES (2), _COEURS (6), _PRECHAUFFE (0),
            _MODELES (q4 ; « q8 » force les anciens GGUF)

Licences : port et code **MIT**, modele et codec **Apache-2.0**, voix **CC BY
4.0** (Kyutai + CML-TTS) : l'audio produit peut sortir de l'atelier, avec
attribution (voir ATTRIBUTION.md).
"""

import io
import json
import os
import sys
import threading
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

ICI = Path(__file__).resolve().parent
MODELS = ICI / 'models'

# ============================================================
# LES MODELES EN SERVICE (29/09/2026) : les GGUF **Q4_K_M**
# ============================================================
# Laurent a ECOUTE les deux quantifications du meme moteur, cote a cote (banc
# `test_voix/LANCER_BANC_ECOUTE_QWENTTS_Q4.bat` : 2 voix, 2 phrases par voix,
# meme phrase et memes reglages). Verdict, mot pour mot : « les versions Q4_K_M
# sont les plus jolies a l'oreille. La prosodie et la clarte sont un demi-cran
# au-dessus. » La mesure dit la meme chose : **+20 % de debit** en moyenne (de
# +7 a +46 % selon la phrase), pour des durees d'audio equivalentes -- donc le
# candidat ne derape pas.
#
# Les Q8_0 (947 + 278 Mo, les anciens) RESTENT sur le disque : c'est eux, le
# retour arriere. Trois facons de revenir, de la plus simple a la plus explicite :
#   1. supprimer les deux fichiers Q4 -> repli AUTOMATIQUE sur les Q8_0 ;
#   2. NIMM_QWENTTS_MODELES=q8 (variable d'environnement) ;
#   3. reprendre `servir_qwentts_cpp.py.bak_avant_bascule_q4_20260929`.
NOMS_Q4 = ('qwen-talker-0.6b-base-Q4_K_M.gguf',
           'qwen-tokenizer-12hz-Q4_K_M.gguf')
NOMS_Q8 = ('qwen-talker-0.6b-base-Q8_0.gguf',
           'qwen-tokenizer-12hz-Q8_0.gguf')


def _choisir_modeles():
    """(talker, codec, nom lisible) -- les Q4_K_M par defaut, les Q8_0 en repli.

    Le repli est SILENCIEUX cote lecteur (le contrat ne bouge pas), mais il est
    DIT dans la fenetre du moteur : sans cela, un retour aux Q8_0 passerait
    inapercu -- la lecon des trois fenetres du 28/09/2026.
    """
    choix = (os.environ.get('NIMM_QWENTTS_MODELES') or '').strip().lower()
    if choix in ('q4', 'q4_k_m'):
        return (MODELS / NOMS_Q4[0], MODELS / NOMS_Q4[1], '0.6B base Q4_K_M')
    if choix in ('q8', 'q8_0'):
        return (MODELS / NOMS_Q8[0], MODELS / NOMS_Q8[1], '0.6B base Q8_0')
    if (MODELS / NOMS_Q4[0]).exists() and (MODELS / NOMS_Q4[1]).exists():
        return (MODELS / NOMS_Q4[0], MODELS / NOMS_Q4[1], '0.6B base Q4_K_M')
    print('NOTE : les GGUF Q4_K_M sont absents -- repli sur les Q8_0 '
          '(NIMM_QWENTTS_MODELES=q4 pour forcer les Q4).', flush=True)
    return (MODELS / NOMS_Q8[0], MODELS / NOMS_Q8[1], '0.6B base Q8_0')


TALKER, CODEC, NOM_MODELE = _choisir_modeles()

# Dossier des voix : par defaut celles de NOTRE atelier (les 35 extraits communs
# avec Kyutai, et leur texte exact). Reglable si un jour on ecoute un autre jeu.
DOSSIER_VOIX = Path(os.environ.get('NIMM_QWENTTS_VOIX')
                    or (ICI.parent / 'qwen_tts_service' / 'voix'))
FICHIER_TEXTES = DOSSIER_VOIX / 'references.csv'
# ============================================================
# LES TEXTES PRIVES (29/09/2026) : les voix de la famille
# ============================================================
# Premier cas : `Maya_normale`, la voix de la fille de Laurent, clonee par
# NIMM Voix. Son texte de reference ne peut PAS etre versionne : `references.csv`
# est suivi par Git (il porte les corrections de texte relues a la main), et
# Maya a lu le debut d'un roman du commerce. Une regle ecrite du BACKLOG est
# claire -- « aucun extrait d'oeuvre sous droits dans les fichiers versionnes ».
#
# Le service lit donc les DEUX fichiers : le public (`references.csv`) puis
# celui-ci, qui est **HORS Git** (`.gitignore`). Une voix presente dans les deux
# prend le texte du PRIVE. Le fichier est optionnel : s'il n'existe pas, rien ne
# change (c'est ce qui rend l'ajout sans risque).
FICHIER_TEXTES_PRIVES = DOSSIER_VOIX / 'references_privees.csv'
# Suffixes de fichiers de reference reconnus : les NOTRES (`..._enhanced_reference.wav`,
# les 35 extraits Kyutai) et ceux des voix clonees par NIMM Voix
# (`..._reference.wav` : 94 Kokoro + 28 « Decoupage OK », arrives le 28/09/2026).
# L'identifiant de voix est le nom du fichier SANS le suffixe reconnu,
# exactement comme dans le catalogue du lecteur (`10087_11650_000028-0002`,
# `ff_romane`, `Femme001`) : c'est ce que la page envoie, et la moindre
# difference laisserait le personnage muet.
SUFFIXES_FICHIERS = ('_enhanced_reference.wav', '_reference.wav')

HOTE = os.environ.get('NIMM_QWENTTS_HOST', '127.0.0.1') or '127.0.0.1'
PORT = int(os.environ.get('NIMM_QWENTTS_PORT', '8086') or '8086')
LANGUE = os.environ.get('NIMM_QWENTTS_LANGUE', 'french') or 'french'
CODEC_FILS = int(os.environ.get('NIMM_QWENTTS_CODEC_FILS', '4') or '4')
FRAMES = int(os.environ.get('NIMM_QWENTTS_FRAMES', '2') or '2')
COEURS = int(os.environ.get('NIMM_QWENTTS_COEURS', '6') or '6')
PRECHAUFFE = os.environ.get('NIMM_QWENTTS_PRECHAUFFE', '') == '1'

# Une phrase plus longue que ca est refusee : le lecteur n'en envoie jamais
# d'aussi longues, et on ne laisse pas un texte enorme occuper le processeur.
TEXTE_MAX = 5000
# Nombre de reprises si le moteur rend un silence (meme garde-fou que le service
# Kyutai et que notre ancien service Qwen : une sortie vide n'est pas une phrase).
REPRISES = 2
# En dessous de ce niveau, la sortie du moteur est un SILENCE (meme garde-fou
# que le service Kyutai et que leur service : une sortie vide n'est pas une phrase).
SEUIL_SILENCE = 0.01

# ============================================================
# GARDE-FOU DE DERIVE (29/09/2026)
# ============================================================
# Laurent a entendu un GARGOUILLIS en changeant la voix de Lord_ivrogne (livre
# 35, voix `homme_aigu_6877654`, prenom Aubin). Le journal du moteur a montre
# **163,84 s d'audio pour une replique de 8 jetons** : 163,84 s = 2048 frames
# divise par 12,5 Hz, soit EXACTEMENT son plafond de frames -- le moteur ne s'est
# jamais arrete (aucun EOS) : il a DERIVE. La cause est un texte de reference
# TRANSCRIT (references.csv dit « le trois males pharaon » la ou l'audio dit
# « le trois-mats le Pharaon ») : en mode ICL, le moteur recoit un audio qui dit
# une chose et un texte qui en dit une autre.
#
# Remede, le MEME que le service NeuTTS (`neutts_service/servir_neutts.py`,
# `duree_max_derivee`) : un plafond de duree, volontairement ENORME (3 fois la
# duree plausible, plus 1 s, avec un plancher de 3 s). Aucune phrase francaise
# lue normalement ne peut l'atteindre : c'est un filet de securite contre un
# emballement, pas une contrainte de lecture.
CARACTERES_PAR_SECONDE = 14.0
MARGE_DERIVE = 3.0
MARGE_DERIVE_S = 1.0
DERIVE_MINIMUM_S = 3.0


def duree_max_derivee(texte):
    """Duree au-dela de laquelle on considere que le moteur a DERIVE."""
    calculee = ((len(texte) / CARACTERES_PAR_SECONDE) * MARGE_DERIVE
                + MARGE_DERIVE_S)
    return max(DERIVE_MINIMUM_S, calculee)

_moteur = None                   # le moteur, charge une fois
_voix_cache = {}                 # identifiant de voix -> (chemin WAV, texte)
_empreintes = {}                 # identifiant -> empreinte (timbre + codes ICL)
_verrou = threading.Lock()       # une seule generation a la fois
_contexte_signale = False        # le champ « contexte » a-t-il ete signale ?
_infos = {
    "pret": False,
    "moteur": "qwentts.cpp (%s)" % NOM_MODELE,
    "appareil": "processeur",
    "langue": LANGUE,
    "codec_fils": CODEC_FILS,
    "frames": FRAMES,
    "coeurs": COEURS,
    "voix": 0,
}


# ============================================================
# LES VOIX : un WAV de reference ET son texte exact
# ============================================================

def _lire_un_fichier_de_textes(chemin):
    """{nom de fichier: texte} d'UN fichier de textes (colonnes separees par ;).

    Le format est celui du projet : fichier;texte;duree;hauteur;source.
    """
    textes = {}
    if not chemin.exists():
        return textes
    with open(chemin, encoding='utf-8-sig') as fichier:
        for ligne in fichier.read().splitlines():
            if not ligne.strip() or ligne.startswith('fichier;'):
                continue
            morceaux = ligne.split(';')
            if len(morceaux) >= 2:
                textes[morceaux[0].strip()] = morceaux[1].strip()
    return textes


def _lire_textes():
    """{nom de fichier: texte} : le fichier PUBLIC, puis le PRIVE par-dessus.

    Colonnes separees par des points-virgules : fichier;texte;duree;hauteur;source.
    Le texte de reference est ce qui active le mode **ICL** (reference plus son
    texte) : sans lui, le moteur clone le timbre seul, et la ressemblance est
    moins bonne -- c'est la difference entre « ca ressemble a la voix » et « c'est
    la voix ». D'ou l'interet de garder le texte de chaque voix, y compris celui
    de Maya, mais HORS du fichier versionne (voir `FICHIER_TEXTES_PRIVES`).
    """
    textes = _lire_un_fichier_de_textes(FICHIER_TEXTES)
    if not textes:
        print("ATTENTION : %s est absent ou vide -- lecture en mode timbre seul."
              % FICHIER_TEXTES.name, flush=True)
    textes.update(_lire_un_fichier_de_textes(FICHIER_TEXTES_PRIVES))
    return textes


def _compter_textes_prives():
    """Combien de textes viennent du fichier PRIVE (pour le dire au demarrage)."""
    return len(_lire_un_fichier_de_textes(FICHIER_TEXTES_PRIVES))


def _repertorier_voix():
    """Re-scanne le dossier des voix : identifiant -> (chemin WAV, texte).

    L'identifiant est le nom du fichier **sans son suffixe**, exactement comme
    dans le catalogue du lecteur (`10087_11650_000028-0002`) : c'est ce que la
    page envoie, et la moindre difference laisserait le personnage muet.
    """
    global _voix_cache
    textes = _lire_textes()
    trouvees = {}
    manquants = []
    if DOSSIER_VOIX.is_dir():
        for fichier in sorted(DOSSIER_VOIX.glob('*.wav')):
            identifiant = fichier.name
            for suffixe in SUFFIXES_FICHIERS:
                if identifiant.endswith(suffixe):
                    identifiant = identifiant[:-len(suffixe)]
                    break
            texte = textes.get(fichier.name, '')
            if not texte:
                manquants.append(fichier.name)
            trouvees[identifiant] = (fichier, texte)
    _voix_cache = trouvees
    _infos["voix"] = len(trouvees)
    if manquants:
        print("ATTENTION : %d voix sans texte dans les fichiers de textes (%s, "
              "%s) -- lues en mode timbre seul."
              % (len(manquants), FICHIER_TEXTES.name,
                 FICHIER_TEXTES_PRIVES.name), flush=True)


def _audio_24k(chemin):
    """Un WAV mono 24 kHz en float32 entre -1 et 1 (ce que le moteur attend)."""
    import numpy as np

    with wave.open(str(chemin), 'rb') as fichier:
        canaux = fichier.getnchannels()
        largeur = fichier.getsampwidth()
        frequence = fichier.getframerate()
        brut = fichier.readframes(fichier.getnframes())
    if largeur != 2:
        raise ValueError('WAV non 16 bits : %s' % chemin)
    donnees = np.frombuffer(brut, dtype=np.int16).astype(np.float32)
    if canaux > 1:
        donnees = donnees.reshape(-1, canaux).mean(axis=1)
    if frequence != 24000:
        raise ValueError('WAV en %d Hz, or le moteur attend 24 000 : %s'
                         % (frequence, chemin))
    return donnees / 32768.0


def _wav_depuis_pcm(sons, frequence):
    """Des echantillons float32 -> un WAV mono 16 bits, pret a envoyer."""
    import numpy as np

    entier = np.clip(np.asarray(sons, dtype=np.float32), -1.0, 1.0)
    entier = (entier * 32767.0).astype('<i2')
    memoire = io.BytesIO()
    with wave.open(memoire, 'wb') as sortie:
        sortie.setnchannels(1)
        sortie.setsampwidth(2)
        sortie.setframerate(int(frequence))
        sortie.writeframes(entier.tobytes())
    return memoire.getvalue()


def _est_vide(sons):
    """Le moteur a-t-il rendu un silence ? (meme garde-fou que Kyutai).

    On ne juge PAS le pic absolu d'une phrase : une phrase courte peut etre
    faible. On juge un seuil tres bas -- en dessous, c'est un silence.
    """
    import numpy as np

    if sons is None or len(sons) == 0:
        return True
    return float(np.abs(np.asarray(sons)).max()) < SEUIL_SILENCE


# ============================================================
# LE MOTEUR : charge une fois, puis chaque phrase sans rien recharger
# ============================================================

def charger_moteur():
    """Charge qwentts.cpp en memoire (processeur), une fois pour toutes.

    Mesures du 28/09/2026 : 1,4 a 2,2 s. Aucune carte graphique n'est touchee,
    et c'est ce qui permet a ce moteur de COHABITER avec Kyutai ou Pocket.
    """
    global _moteur

    from qwentts_cpp_cpu import QwenTTS

    _repertorier_voix()
    if not _voix_cache:
        print("ARRET : aucune voix exploitable dans %s" % DOSSIER_VOIX)
        print("(il faut un .wav ET sa ligne dans %s)" % FICHIER_TEXTES.name)
        sys.exit(1)

    # La priorite d'entame EXIGE le chevauchement du codec ET une cadence de 2 ou
    # 4 images : sans les deux, le moteur REFUSE au lieu de degrader en silence
    # (contrainte decouverte le 28/09/2026). On la pose donc AVANT de construire
    # le contexte, et nos deux autres reglages la respectent.
    os.environ.setdefault('QWENTTS_CPU_STARTUP_PRIORITY', 'second_chunk')

    print("Chargement du moteur qwentts.cpp (processeur) : %d coeurs, %d fils de "
          "codec, tranches de %d images." % (COEURS, CODEC_FILS, FRAMES),
          flush=True)
    debut = time.time()
    _moteur = QwenTTS(str(TALKER), str(CODEC),
                      cpu_threads=COEURS,
                      cpu_codec_threads=CODEC_FILS,
                      cpu_stream_frames=FRAMES)
    _infos["charge_en"] = round(time.time() - debut, 1)
    _infos["voix"] = len(_voix_cache)

    # Le prechauffage se fait AVANT d'annoncer « pret » : tant que les empreintes
    # ne sont pas pretes, la premiere phrase de chaque voix paie l'attente (x0,53
    # puis x0,93) -- exactement ce que Laurent a entendu le 28/09/2026. Desactive
    # par defaut : 35 empreintes prennent quelques minutes.
    if PRECHAUFFE:
        _prechauffer_les_voix()

    _infos["pret"] = True
    print("Moteur pret en %.1f s -- %d voix disponibles."
          % (_infos["charge_en"], len(_voix_cache)), flush=True)
    print("Service pret : http://%s:%d   (/sante, /voix, /tts)"
          % (HOTE, PORT), flush=True)


def _prechauffer_les_voix():
    """Prepare les empreintes de toutes les voix, une par une.

    Appele seulement si NIMM_QWENTTS_PRECHAUFFE=1 (voir `charger_moteur`).
    """
    debut = time.time()
    for identifiant in sorted(_voix_cache):
        try:
            with _verrou:
                _empreinte(identifiant)
        except Exception as erreur:
            print("  empreinte impossible pour %s : %s" % (identifiant, erreur),
                  flush=True)
    print("Empreintes prechauffees : %d voix en %.1f s"
          % (len(_voix_cache), time.time() - debut), flush=True)


def _empreinte(identifiant):
    """L'empreinte d'une voix (timbre + codes ICL), calculee UNE fois puis gardee.

    POURQUOI UN CACHE : la preparation coute une dizaine de secondes par voix
    (mesure du 28/09/2026) ; la refaire a chaque phrase serait ruineux.

    L'appelant doit tenir le VERROU : le moteur n'accepte qu'un appel a la fois.
    """
    if identifiant not in _empreintes:
        chemin, _texte = _voix_cache[identifiant]
        debut = time.time()
        reference = _moteur.extract_voice_ref(_audio_24k(chemin))
        _empreintes[identifiant] = (reference.ref_spk_emb,
                                    reference.ref_codes)
        print("  empreinte de la voix %s prete en %.1f s"
              % (identifiant, time.time() - debut), flush=True)
    return _empreintes[identifiant]


# ============================================================
# LA GENERATION D'UNE PHRASE
# ============================================================

def generer_wav(texte, identifiant_voix):
    """Genere une phrase en CONSOMMANT LE FLUX. Renvoie (octets WAV, duree).

    POURQUOI LE FLUX : c'est le mode le plus rapide du moteur (mesure du
    28/09/2026 : x0,94 le temps reel avec les trois reglages, contre x0,66 sans
    le chevauchement). On accumule tout, puis on rend un WAV COMPLET : le contrat
    du lecteur ne change pas, et le defaut des « 2 s perdues en fin de flux »
    disparait, puisqu'on consomme jusqu'au bout au lieu de s'arreter au dernier
    morceau recu.
    """
    import numpy as np

    if _moteur is None:
        raise RuntimeError("le moteur n'est pas encore charge")
    if identifiant_voix not in _voix_cache:
        raise ValueError("voix inconnue : %s" % identifiant_voix)

    with _verrou:
        spk, codes = _empreinte(identifiant_voix)
        _chemin, texte_reference = _voix_cache[identifiant_voix]
        taux = 24000
        plafond = duree_max_derivee(texte)
        sons = np.zeros(0, dtype=np.float32)
        derive = False
        for essai in range(REPRISES + 1):
            morceaux = []
            for bloc, taux in _moteur.stream(
                    text=texte, lang=LANGUE, ref_spk_emb=spk, ref_codes=codes,
                    ref_text=texte_reference):
                morceaux.append(bloc)
            sons = (np.concatenate(morceaux) if morceaux
                    else np.zeros(0, dtype=np.float32))
            if _est_vide(sons):
                if essai < REPRISES:
                    print("  phrase VIDE (silence) -- reprise %d/%d"
                          % (essai + 1, REPRISES), flush=True)
                else:
                    print("  phrase VIDE (silence) -- plus de reprise",
                          flush=True)
                continue
            duree_essai = len(sons) / float(taux) if taux else 0.0
            if duree_essai > plafond:
                # DERIVE : le moteur s'est emballe (constat du 29/09/2026, voix
                # Aubin : 163,84 s d'audio pour une replique de 8 jetons). On
                # RELANCE -- c'est un tirage aleatoire, la generation suivante
                # peut etre juste. On ne livre jamais un gargouillis de plusieurs
                # minutes.
                derive = True
                if essai < REPRISES:
                    print("  phrase DERIVEE (%.1f s pour %d caracteres, plafond "
                          "%.1f s) -- reprise %d/%d"
                          % (duree_essai, len(texte), plafond, essai + 1,
                             REPRISES), flush=True)
                else:
                    print("  phrase DERIVEE (%.1f s pour %d caracteres, plafond "
                          "%.1f s) -- plus de reprise, elle sera rognee"
                          % (duree_essai, len(texte), plafond), flush=True)
                continue
            if essai:
                print("  phrase relancee apres %d essai(s) rate(s)" % essai,
                      flush=True)
            derive = False
            break

        # DERNIER FILET : le moteur n'a jamais rendu de phrase plausible. On
        # rogne la derniere generation (le remede du service NeuTTS) plutot que
        # de rendre plusieurs minutes de babil -- le lecteur, lui, jouerait tout.
        if derive:
            maximum = int(plafond * taux)
            if len(sons) > maximum:
                print("  phrase ROGNEE a %.1f s (rien de plausible rendu)"
                      % plafond, flush=True)
                sons = sons[:maximum]

    duree = len(sons) / float(taux) if taux else 0.0
    return _wav_depuis_pcm(sons, taux), duree


# ============================================================
# LE SERVICE HTTP (bibliotheque standard : rien a installer en plus)
# ============================================================

class Repondeur(BaseHTTPRequestHandler):
    server_version = "NIMMQwentts/1.0"

    # --- reponses -------------------------------------------------

    def _envoyer(self, code, contenu, type_contenu):
        self.send_response(code)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(contenu)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(contenu)

    def _envoyer_json(self, code, donnees):
        contenu = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
        self._envoyer(code, contenu, "application/json; charset=utf-8")

    def _lire_corps(self):
        taille = int(self.headers.get("Content-Length") or 0)
        if taille <= 0:
            return {}
        return json.loads(self.rfile.read(taille).decode("utf-8"))

    # --- routes ---------------------------------------------------

    def do_GET(self):
        chemin = self.path.split("?")[0]
        if chemin == "/sante":
            self._envoyer_json(200, dict(_infos))
        elif chemin == "/voix":
            self._envoyer_json(200, {
                "voix": sorted(_voix_cache.keys()),
                "nombre": len(_voix_cache),
            })
        else:
            self._envoyer_json(404, {"erreur": "adresse inconnue"})

    def do_POST(self):
        chemin = self.path.split("?")[0]

        if chemin == "/recharger":
            # Re-scanne le dossier des voix SANS recharger le moteur : on peut
            # ainsi ajouter une voix sans redemarrer le service (nos 35 voix
            # viendront peut-etre s'agrandir -- voix Kokoro clonees, langues
            # etrangeres...).
            _repertorier_voix()
            print("voix rechargees : %d" % len(_voix_cache), flush=True)
            self._envoyer_json(200, {"voix": len(_voix_cache),
                                     "liste": sorted(_voix_cache.keys())})
            return

        if chemin != "/tts":
            self._envoyer_json(404, {"erreur": "adresse inconnue"})
            return

        try:
            demande = self._lire_corps()
        except Exception:
            self._envoyer_json(400, {"erreur": "demande illisible (JSON attendu)"})
            return

        texte = (demande.get("texte") or "").strip()
        voix = (demande.get("voix") or "").strip()

        if not texte:
            self._envoyer_json(400, {"erreur": "texte vide"})
            return
        if len(texte) > TEXTE_MAX:
            self._envoyer_json(400, {"erreur": "texte trop long"})
            return
        if not _infos["pret"]:
            self._envoyer_json(503, {"erreur": "moteur en cours de chargement"})
            return

        # Le « contexte glissant » du service Kyutai (fin de la phrase precedente)
        # n'a pas d'equivalent ici : on l'IGNORE, mais on le DIT une fois -- un
        # silence ferait croire que le reglage fonctionne encore.
        global _contexte_signale
        if demande.get("contexte") and not _contexte_signale:
            _contexte_signale = True
            print("NOTE : champ « contexte » recu et ignore -- ce moteur n'a pas "
                  "ce reglage.", flush=True)

        debut = time.time()
        try:
            wav, duree = generer_wav(texte, voix)
        except ValueError as erreur:
            self._envoyer_json(400, {"erreur": str(erreur)})
            return
        except Exception as erreur:          # panne du moteur
            print("ERREUR generation : %s" % erreur, flush=True)
            self._envoyer_json(500, {"erreur": "generation impossible : %s"
                                              % erreur})
            return

        calcul = time.time() - debut
        # Le RAPPORT AU TEMPS REEL est le chiffre qui dit si le moteur tient sur
        # un chapitre (> 1 = plus vite qu'on ne lit).
        rapport = (duree / calcul) if calcul else 0.0
        print("phrase generee  voix=%-28s  %5.1f s de calcul  %5.1f s d'audio"
              "  x%.2f le temps reel" % (voix, calcul, duree, rapport),
              flush=True)
        self._envoyer(200, wav, "audio/wav")

    # --- journal lisible ------------------------------------------

    def log_message(self, format, *args):
        """Une ligne courte par appel, lisible dans la fenetre du moteur.

        Les interrogations `GET /sante` ne sont PAS affichees : c'est le voyant du
        lecteur, qui demande toutes les 5 secondes si le moteur est pret -- cela
        remplirait la fenetre sans rien apprendre (meme regle que Kyutai, XTTS et
        Pocket).
        """
        if args and isinstance(args[0], str) and "GET /sante" in args[0]:
            return
        BaseHTTPRequestHandler.log_message(self, format, *args)


class ServiceQwentts(ThreadingHTTPServer):
    """Le serveur du moteur.

    `allow_reuse_address = False` est VOLONTAIRE : si le port est deja pris par un
    moteur encore allume, on veut une erreur claire -- pas deux services qui se
    partagent le meme port. C'est exactement ce qui est arrive le 28/09/2026, avec
    trois fenetres de moteur ouvertes en meme temps : les phrases se repartissaient
    entre elles, et chacune devait recharger les voix.
    """

    daemon_threads = True
    allow_reuse_address = False


def _moteur_deja_en_route():
    """Un service repond-il deja sur notre port ? (garde-fou du double lancement)"""
    import socket

    try:
        with socket.create_connection((HOTE, PORT), timeout=0.5):
            return True
    except OSError:
        return False


def _charger_en_fond():
    """Charge le moteur sans bloquer l'ouverture du port.

    POURQUOI : le lecteur interroge /sante et attend `pret`. Il vaut mieux qu'il
    voie « en chargement » pendant 1,5 s plutot que de ne rien voir du tout.
    """
    try:
        charger_moteur()
    except Exception as erreur:
        print("ECHEC du chargement : %s : %s" % (type(erreur).__name__, erreur),
              flush=True)
        print("Le service repond, mais il restera « non pret ».", flush=True)


def main():
    print("=" * 70)
    print("NIMM ePub : appareil de voix qwentts.cpp (Qwen3-TTS en C++/GGML)")
    print("=" * 70)
    print("moteur   : %s" % TALKER.name)
    print("codec    : %s" % CODEC.name)
    print("voix     : %s" % DOSSIER_VOIX)
    _prives = _compter_textes_prives()
    if _prives:
        print("textes   : %s + %d texte(s) PRIVE(S) dans %s (hors Git)"
              % (FICHIER_TEXTES.name, _prives, FICHIER_TEXTES_PRIVES.name))
    print("adresse  : http://%s:%d   (fermer la fenetre ARRETE le moteur)"
          % (HOTE, PORT))
    print("reglages : %d coeurs | %d fils de codec | tranches de %d images | %s"
          % (COEURS, CODEC_FILS, FRAMES, LANGUE))
    print("prechauffage des empreintes : %s" % ("oui" if PRECHAUFFE else "non"))
    print("")

    if not TALKER.exists() or not CODEC.exists():
        print("ARRET : il manque un modele dans %s" % MODELS)
        print("  attendu : %s" % TALKER.name)
        print("            %s" % CODEC.name)
        return 1

    if _moteur_deja_en_route():
        print("Un moteur repond deja sur le port %d : rien a faire." % PORT)
        print("(garde-fou : deux moteurs sur le meme port se partageraient les "
              "phrases, et chacun rechargerait les voix)")
        return 0

    threading.Thread(target=_charger_en_fond, daemon=True).start()

    try:
        service = ServiceQwentts((HOTE, PORT), Repondeur)
    except OSError as erreur:
        print("ARRET : impossible d'ouvrir le port %d : %s" % (PORT, erreur))
        return 1

    print("Service en ecoute. Cette fenetre EST le moteur.", flush=True)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("Arret demande : le moteur s'arrete.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

