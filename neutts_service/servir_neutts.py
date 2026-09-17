# -*- coding: utf-8 -*-
"""
Appareil de voix NeuTTS (clonage de voix) -- service local pour NIMM ePub.

Ce programme charge UNE FOIS le moteur NeuTTS (Neuphonic) puis repond a trois
questions, en HTTP, sur le reseau local :

    GET  /sante  -> le moteur est-il pret ? (et quelles infos)
    GET  /voix   -> la liste des voix disponibles (les references)
    POST /tts    -> {"texte": "...", "voix": "..."} -> fichier WAV

Il vit A COTE du lecteur, dans son propre environnement Python 3.12 (NIMM ePub
tourne sur Python 3.14 et ne peut pas heberger PyTorch). Le lecteur l'appelle
donc par le reseau, exactement comme Kyutai (8082) et XTTS v2 (8083).
PORT : 8084.

Meme principe que le service XTTS : le moteur n'est charge qu'une fois, et une
seule generation tourne a la fois (le moteur n'est pas « thread-safe »).

VOIX : NeuTTS est un moteur de CLONAGE -- il n'a pas de voix « a lui ». On lui
donne un extrait de 3 a 15 secondes ET LE TEXTE EXACT de cet extrait (deux
choses, contrairement a XTTS : sans le texte, rien ne fonctionne). Les
references sont dans le dossier `references` : les extraits francais libres de
droits (CML-TTS, CC BY 4.0, et les extraits du domaine public), avec leur
transcription enregistree une fois pour toutes dans un `references.csv`.

DIFFERENCE IMPORTANTE AVEC XTTS -- la STABILITE. XTTS etait inegal d'une prise
a l'autre (mesure du 16/09/2026 : 0,93 / 1,07 / 1,11 s pour la meme phrase), et
baisser la temperature n'y changeait rien. NeuTTS, lui, rejoue son tirage
aleatoire a partir d'une GRAINE : `neutts` execute `torch.manual_seed(graine)`
a chaque appel, donc **memes entrees + meme graine = audio identique**. La
graine est donc fixee ici une fois pour toutes (reglage NIMM_NEUTTS_GRAINE).

Garde-fou contre le babil (le defaut qui a coute une journee a XTTS) : mesure
du 16/09/2026 a l'atelier NIMM Voix -- 8 phrases de 4 a 117 caracteres, AUCUN
debordement, duree proportionnelle au texte (« Manger ? » 1,10 s contre 8,49 s
pour XTTS). Les filets d'XTTS ne sont donc pas repris tels quels : il ne reste
qu'un filet TRES LARGE (rogner_a_duree), qui ne peut se declencher que sur une
vraie derive, jamais sur une phrase lue normalement.

Lancement : DEMARRER_NEUTTS.bat (ou : .venv\\Scripts\\python.exe servir_neutts.py)
Reglages (variables d'environnement, valeurs par defaut entre parentheses) :
    NIMM_NEUTTS_PORT       (8084)   port d'ecoute
    NIMM_NEUTTS_HOST       (127.0.0.1)  adresse d'ecoute (locale par defaut)
    NIMM_NEUTTS_APPAREIL   (auto)   auto | cuda | cpu
    NIMM_NEUTTS_BACKBONE   (neuphonic/neutts-nano-french)
    NIMM_NEUTTS_CODEC      (neuphonic/neucodec)
    NIMM_NEUTTS_GRAINE     (42)     graine de generation (reproductibilite)
    NIMM_NEUTTS_PRECODER   (0)      1 = encoder TOUTES les references au
                                    demarrage (demarrage plus long, mais
                                    premiere phrase instantanee pour chaque
                                    voix) ; 0 = a la demande, puis en memoire
"""

import io
import json
import os
import re
import sys
import threading
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# Le stockage « xet » de Hugging Face a deja bloque un telechargement (11/09 et
# 16/09/2026) : on le desactive preventivement, comme le font les deux autres
# services et comme le fait deja l'atelier NIMM Voix (tester_neutts.py).
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

# ==============================================================
# CHEMINS ET REGLAGES
# ==============================================================

ICI = Path(__file__).resolve().parent
# Les references : un sous-dossier par provenance, avec un `references.csv`
# (colonnes `fichier;texte;...`, ecrit par l'atelier NIMM Voix). Un fichier
# `<nom>_reference.wav` accompagne d'un `<nom>_reference.txt` est aussi accepte :
# cela permet d'ajouter une voix a la main, sans passer par le CSV.
DOSSIER_REFERENCES = ICI / "references"

BACKBONE = os.environ.get("NIMM_NEUTTS_BACKBONE") or "neuphonic/neutts-nano-french"
CODEC = os.environ.get("NIMM_NEUTTS_CODEC") or "neuphonic/neucodec"
APPAREIL = (os.environ.get("NIMM_NEUTTS_APPAREIL") or "auto").strip().lower()
GRAINE = int(os.environ.get("NIMM_NEUTTS_GRAINE") or "42")
PRECODER = os.environ.get("NIMM_NEUTTS_PRECODER") == "1"

HOTE = os.environ.get("NIMM_NEUTTS_HOST") or "127.0.0.1"
PORT = int(os.environ.get("NIMM_NEUTTS_PORT") or "8084")

# Fenetre MESUREE du moteur : 2048 jetons, soit environ 30 s d'audio
# REFERENCE COMPRISE. Avec une reference de 12 s, il reste ~18 s pour le texte.
# Un morceau trop long est TRONQUE PAR LE MOTEUR SANS MESSAGE D'ERREUR : d'ou la
# limite de 200 caracteres, identique a celle de l'atelier NIMM Voix.
MAX_CARACTERES = 200
# ... mais 200 caracteres ne sont valables QUE si la reference est courte. Les
# extraits prepares font 12 s au plus, pourtant un extrait ajoute a la main
# peut etre plus long : les echantillons de controle de Kokoro vont jusqu'a
# 17,3 s (mesure du 16/09/2026). La place restante pour le texte est donc
# calculee POUR CHAQUE VOIX d'apres la duree reelle de son extrait : c'est le
# role de _limite_caracteres().
FENETRE_TOTALE_S = 30.0     # la fenetre du moteur, reference comprise
MARGE_FENETRE_S = 2.0       # marge de securite (respiration en fin de morceau)
CARACTERES_MINIMUM = 60     # plancher : une phrase courte reste d'un morceau
# Silence pose UNIQUEMENT entre deux vraies phrases -- jamais a l'interieur
# d'une phrase redecoupee (meme valeur que le service XTTS : 0,35 s).
SILENCE_PHRASE_S = 0.35
# Sortie native du moteur : WAV mono 24 000 Hz (comme XTTS).
FREQUENCE = 24000
# Rognage du silence de queue : marge mesuree sur XTTS (0,25 s), appliquee ici
# pour que l'enchainement des phrases soit regulier.
SILENCE_QUEUE_S = 0.25
# Seuil d'amplitude au-dessous duquel on considere qu'il n'y a pas de parole.
SEUIL_SON = 0.012
BLOC_ANALYSE_S = 0.02

# ---- Filet TRES LARGE contre une derive (jamais contre une phrase normale) --
# L'atelier a mesure, sur 8 phrases de 4 a 117 caracteres, des rapports de
# duree de x0,6 a x1,4 : la duree reste proportionnelle au texte. Ce filet ne
# coupe donc que ce qu'aucune phrase francaise ne peut produire : au-dela de
# TROIS FOIS la duree plausible plus une seconde.
#
# Le PLANCHER de 3 s compte pour les phrases tres courtes : sur « Non. »
# (4 caracteres), le calcul seul donnerait 1,86 s, ce qui resterait trop juste
# -- « Non. » a ete mesure a 1,10 s, mais le moteur respire parfois davantage,
# et couper une syllabe serait pire que de laisser passer un emballement de
# 3 s (un vrai babil de XTTS, lui, faisait 8 a 9 s).
CARACTERES_PAR_SECONDE = 14.0
MARGE_DERIVE = 3.0
MARGE_DERIVE_S = 1.0
DERIVE_MINIMUM_S = 3.0

TEXTE_MAX = 3000

# Une phrase, ses abreviations : leur point interne ne termine PAS la phrase.
ABREVIATIONS = ('M.', 'MM.', 'Mme', 'Mlle', 'Dr', 'St', 'Ste', 'av.', 'cf.',
                'etc.', 'p.', 'pp.', 'art.', 'fig.', 'tel.')

# --- Etat partage par le service -------------------------------------------
_moteur = None
_verrou = threading.Lock()          # une seule generation a la fois
_voix_cache = {}                    # identifiant -> (chemin du WAV, texte exact)
_references_encodees = {}           # identifiant -> reference encodee en memoire
_infos = {"pret": False, "moteur": "neuphonic/neutts-nano-french",
          "appareil": "", "voix": 0, "charge_en": 0.0,
          "graine": GRAINE, "references_encodees": 0}

# ==============================================================
# OUTILS AUDIO (aucune dependance en plus : numpy est deja la,
# avec PyTorch)
# ==============================================================

def _wav_depuis_pcm(echantillons, frequence=FREQUENCE):
    """Convertit l'audio du moteur (nombres flottants) en WAV 16 bits mono --
    meme format que Kokoro, Piper, Kyutai et XTTS dans le lecteur."""
    import numpy as np
    donnees = np.clip(np.asarray(echantillons, dtype=np.float32), -1.0, 1.0)
    donnees = (donnees * 32767.0).astype("<i2")

    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(frequence))
        fichier.writeframes(donnees.tobytes())
    return tampon.getvalue()


def rogner_queue(sons, frequence=FREQUENCE):
    """Ramene le silence de FIN de phrase a SILENCE_QUEUE_S.

    Mesure d'atelier sur XTTS : chaque phrase se terminait par 0,54 a 0,91 s de
    silence -- long ET variable d'une phrase a l'autre, ce qui rendait les
    dialogues irreguliers. On applique ici la meme marge qu'Edge (0,25 s). La
    parole, elle, n'est jamais touchee : on coupe APRES le dernier son audible.
    """
    import numpy as np

    try:
        donnees = np.asarray(sons, dtype=np.float32)
        if donnees.size == 0:
            return donnees
        pas = max(1, int(BLOC_ANALYSE_S * frequence))
        dernier_son = 0
        for debut in range(0, donnees.size, pas):
            bloc = donnees[debut:debut + pas]
            if bloc.size and float(np.max(np.abs(bloc))) >= SEUIL_SON:
                dernier_son = debut + bloc.size
        if dernier_son == 0:                      # aucun son : rien a rogner
            return donnees
        fin = dernier_son + int(SILENCE_QUEUE_S * frequence)
        return donnees[:min(donnees.size, fin)]
    except Exception:
        return sons


def duree_max_derivee(texte):
    """Duree au-dela de laquelle on considere que le moteur a DERIVE.

    Volontairement enorme (3 fois la duree plausible, plus 1 s, avec un
    plancher de 3 s) : aucune phrase francaise lue normalement ne peut
    l'atteindre. C'est un filet de securite contre un emballement, pas une
    contrainte de lecture.
    """
    calculee = ((len(texte) / CARACTERES_PAR_SECONDE) * MARGE_DERIVE
                + MARGE_DERIVE_S)
    return max(DERIVE_MINIMUM_S, calculee)


def rogner_a_duree(sons, texte, frequence=FREQUENCE):
    """Coupe la fin d'un audio qui depasse duree_max_derivee().

    Dernier filet seulement : sur les 8 phrases mesurees a l'atelier (4 a 117
    caracteres), il ne s'est jamais declenche.
    """
    import numpy as np

    try:
        donnees = np.asarray(sons, dtype=np.float32)
        maximum = int(duree_max_derivee(texte) * frequence)
        if donnees.size <= maximum:
            return donnees
        return donnees[:maximum]
    except Exception:
        return sons


# ==============================================================
# DECOUPAGE DU TEXTE (meme logique que l'atelier NIMM Voix et que
# le service XTTS : rien d'invente, on ne touche pas au sens)
# ==============================================================

def _commence_minuscule(morceau):
    """Un fragment qui commence par une minuscule ne commence pas une phrase."""
    for caractere in morceau:
        if caractere.isalpha():
            return caractere.islower()
    return False


def decouper_phrases(texte):
    """Decoupe en phrases sur la ponctuation forte.

    Les abreviations courantes (`M.`, `etc.`...) et les fragments qui
    commencent par une minuscule sont RECOLLES : leur point ne termine pas la
    phrase. C'est la logique validee par l'atelier NIMM Voix.
    """
    morceaux = re.split(r'(?<=[.!?\u2026])\s+', texte)
    morceaux = [m.strip() for m in morceaux if m.strip()]
    phrases = []
    for morceau in morceaux:
        recolle = bool(phrases) and (phrases[-1].endswith(ABREVIATIONS)
                                     or _commence_minuscule(morceau))
        if recolle:
            phrases[-1] = phrases[-1] + ' ' + morceau
        else:
            phrases.append(morceau)
    return phrases


def decouper_trop_long(phrase, maximum=MAX_CARACTERES):
    """Redecoupe une phrase trop longue pour la fenetre du moteur : d'abord aux
    virgules et points-virgules, puis aux espaces si besoin."""
    if len(phrase) <= maximum:
        return [phrase]
    morceaux = []
    reste = phrase
    while len(reste) > maximum:
        coupe = -1
        for separateur in (', ', '; ', ': ', ' '):
            coupe = reste.rfind(separateur, 0, maximum)
            if coupe > 0:
                coupe += len(separateur)
                break
        if coupe <= 0:
            coupe = maximum
        morceaux.append(reste[:coupe].strip())
        reste = reste[coupe:].strip()
    if reste:
        morceaux.append(reste)
    return [m for m in morceaux if m]


def plan_de_lecture(texte, maximum=MAX_CARACTERES):
    """Plan de lecture : [(phrase, [morceaux...]), ...]."""
    texte = ' '.join((texte or '').split())
    if not texte:
        return []
    return [(phrase, decouper_trop_long(phrase, maximum))
            for phrase in decouper_phrases(texte)]

# ==============================================================
# LES VOIX (extraits de reference a cloner, AVEC leur texte)
# ==============================================================

def _duree_wav(chemin):
    """Duree d'un WAV, en secondes (0.0 si illisible).

    Lue dans l'en-tete du fichier : aucun son n'est charge en memoire. Elle
    sert a savoir COMBIEN de la fenetre du moteur (~30 s, reference comprise)
    est deja prise par l'extrait, donc quelle place il reste pour le texte.
    """
    try:
        with wave.open(str(chemin), "rb") as fichier:
            frequence = fichier.getframerate() or FREQUENCE
            return fichier.getnframes() / float(frequence)
    except Exception:
        return 0.0


def _lire_transcriptions(dossier):
    """{nom de fichier -> texte} du `references.csv` d'un dossier, s'il existe.

    Format ecrit par l'atelier NIMM Voix (Whisper large-v3 a transcrit chaque
    extrait) : `fichier;texte;duree;hauteur;source`, en UTF-8, separateur « ; ».
    """
    import csv

    chemin = dossier / "references.csv"
    textes = {}
    if not chemin.exists():
        return textes
    try:
        with open(chemin, "r", encoding="utf-8", newline="") as fichier:
            for ligne in csv.DictReader(fichier, delimiter=";"):
                nom = (ligne.get("fichier") or "").strip()
                if nom:
                    textes[nom] = (ligne.get("texte") or "").strip()
    except Exception as erreur:
        print("ATTENTION : %s illisible (%s)" % (chemin.name, str(erreur)[:80]))
    return textes


def _repertorier_references():
    """Associe chaque voix a (chemin du WAV, texte EXACT, duree de l'extrait).

    NeuTTS a besoin des DEUX (contrairement a XTTS, qui se contente du son).
    Deux facons d'ajouter une voix, sans toucher au code :
      - le `references.csv` du dossier (les 79 references de l'atelier) ;
      - un simple `<nom>_reference.txt` a cote du `<nom>_reference.wav`.
    Une reference sans texte est IGNOREE (et le dit) : sans lui, le moteur
    invente une prononciation, et le resultat est inutilisable.
    """
    global _voix_cache

    trouvees = {}
    doublons = []
    sans_texte = []

    if not DOSSIER_REFERENCES.is_dir():
        print("ATTENTION : dossier de references absent : %s" % DOSSIER_REFERENCES)
        _voix_cache = {}
        return _voix_cache

    dossiers = [DOSSIER_REFERENCES]
    dossiers += sorted(p for p in DOSSIER_REFERENCES.rglob("*") if p.is_dir())

    for dossier in dossiers:
        textes = _lire_transcriptions(dossier)
        for wav in sorted(dossier.glob("*_reference.wav")):
            base = wav.name[:-len("_reference.wav")]
            if not base:
                continue
            # Les extraits CML-TTS s'appellent <identifiant>_enhanced : le
            # suffixe est retire pour retrouver EXACTEMENT l'identifiant du
            # catalogue du lecteur (meme regle que servir_xtts.py). Sans cela,
            # les voix NeuTTS porteraient d'autres identifiants que les voix
            # XTTS, et il faudrait tout re-saisir a la main.
            if base.endswith("_enhanced"):
                identifiant = base[:-len("_enhanced")]
            else:
                identifiant = base
            if not identifiant:
                continue
            texte = textes.get(wav.name, "")
            if not texte:
                jumeau = dossier / (base + "_reference.txt")
                if jumeau.exists():
                    texte = " ".join(jumeau.read_text(
                        encoding="utf-8", errors="replace").split())
            if not texte:
                sans_texte.append(wav.name)
                continue
            if identifiant in trouvees:
                doublons.append(identifiant)
            trouvees[identifiant] = (wav, texte, _duree_wav(wav))

    _voix_cache = trouvees
    if sans_texte:
        print("ATTENTION : %d reference(s) ignoree(s), texte manquant : %s"
              % (len(sans_texte), ", ".join(sorted(sans_texte)[:5])))
    if doublons:
        print("ATTENTION : %d identifiant(s) present(s) deux fois (le dernier "
              "gagne) : %s" % (len(doublons), ", ".join(sorted(set(doublons))[:5])))
    return trouvees

# ==============================================================
# CHARGEMENT DU MOTEUR (une seule fois, au demarrage)
# ==============================================================

def charger_moteur():
    """Charge NeuTTS (backbone + codec) en memoire.

    Memoire video mesuree a l'atelier NIMM Voix le 16/09/2026 : **3,50 Go** au
    pic (le modele fait 0,2 Md de parametres, mais le codec et l'encodeur
    `facebook/w2v-bert-2.0` pesent lourd). Chargement ~10 s a chaud.

    L'ordre compte : les references d'abord, pour pouvoir s'arreter tout de
    suite si elles manquent (un service sans voix ne sert a rien).
    """
    global _moteur

    import torch
    from neutts import NeuTTS

    _repertorier_references()
    if not _voix_cache:
        print("ARRET : aucune reference trouvee dans %s" % DOSSIER_REFERENCES)
        print("Attendu : des fichiers <nom>_reference.wav avec leur texte")
        print("(references.csv du dossier, ou <nom>_reference.txt a cote).")
        sys.exit(1)

    if APPAREIL == "cuda" and not torch.cuda.is_available():
        print("ATTENTION : la carte graphique a ete demandee mais n'est pas "
              "disponible -- on passe sur le processeur (3 a 4 fois plus lent).")
        appareil = "cpu"
    elif APPAREIL == "cpu":
        appareil = "cpu"
    elif torch.cuda.is_available():
        appareil = "cuda"
    else:
        appareil = "cpu"

    if appareil == "cuda":
        nom_appareil = "cuda : %s" % torch.cuda.get_device_name(0)
    else:
        nom_appareil = "cpu (3 a 4 fois plus lent que la carte graphique)"

    print("Chargement du moteur NeuTTS (%s)..." % nom_appareil)
    print("  backbone : %s" % BACKBONE)
    print("  codec    : %s" % CODEC)
    t0 = time.time()

    reglages = dict(backbone_repo=BACKBONE, backbone_device=appareil,
                    codec_repo=CODEC, codec_device=appareil)
    try:
        # La GRAINE est ce qui rend le moteur reproductible : `neutts` execute
        # torch.manual_seed(graine) a chaque appel, donc memes entrees + meme
        # graine = audio identique. C'est ce qui manquait a XTTS.
        _moteur = NeuTTS(seed=GRAINE, **reglages)
        print("  graine fixee : %d (meme texte = meme audio)" % GRAINE)
    except TypeError:
        # Garde-fou : si une version de neutts n'accepte pas encore `seed`,
        # on continue sans (le moteur imprimera alors la graine qu'il a tiree).
        print("  ATTENTION : cette version de neutts refuse le reglage 'seed'.")
        print("  Le moteur reste utilisable, mais ses prises varieront :")
        print("  garder la graine qu'il affiche pour rejouer un audio identique.")
        _moteur = NeuTTS(**reglages)

    if PRECODER:
        # Encodage de TOUTES les references des maintenant (demarrage plus
        # long, mais la premiere phrase de chaque voix sera instantanee).
        print("  encodage des references (NIMM_NEUTTS_PRECODER=1)...")
        for rang, identifiant in enumerate(sorted(_voix_cache), 1):
            try:
                _reference_encodee(identifiant)
            except Exception as erreur:
                print("    reference non encodable %s : %s"
                      % (identifiant, str(erreur)[:80]))
            if rang % 25 == 0:
                print("    %d/%d" % (rang, len(_voix_cache)))

    _infos["appareil"] = nom_appareil
    _infos["voix"] = len(_voix_cache)
    _infos["charge_en"] = round(time.time() - t0, 1)
    _infos["pret"] = True
    print("Moteur pret en %.1f s -- %d voix disponibles."
          % (_infos["charge_en"], len(_voix_cache)))


def _reference_encodee(identifiant):
    """La reference encodee d'une voix (calculee une fois, gardee en memoire).

    Pourquoi : l'encodage de l'extrait est un travail qui ne depend PAS du
    texte a lire. `examples/encode_reference.py` de NeuTTS recommande d'ailleurs
    de le faire « ahead of time » pour reduire la latence. On le fait donc au
    premier usage de chaque voix, puis on le garde.
    """
    if identifiant in _references_encodees:
        return _references_encodees[identifiant]
    chemin = _voix_cache[identifiant][0]
    t0 = time.time()
    codes = _moteur.encode_reference(str(chemin))
    _references_encodees[identifiant] = codes
    _infos["references_encodees"] = len(_references_encodees)
    print("reference encodee : %-32s %.1f s" % (identifiant, time.time() - t0))
    return codes

# ==============================================================
# GENERATION
# ==============================================================

def _lire_un_morceau(morceau, identifiant_voix):
    """Fait lire UN morceau (200 caracteres au plus) avec la voix donnee.

    Renvoie un tableau de nombres flottants (l'audio brut du moteur).
    """
    import numpy as np

    texte_reference = _voix_cache[identifiant_voix][1]
    codes = _reference_encodee(identifiant_voix)
    # `infer` cree son propre tirage a partir de la graine du moteur : c'est ce
    # qui rend la sortie reproductible d'un appel a l'autre.
    resultat = _moteur.infer(morceau, codes, texte_reference)
    if hasattr(resultat, "detach"):            # tenseur PyTorch (carte ou cpu)
        resultat = resultat.detach().cpu().numpy()
    return np.asarray(resultat, dtype=np.float32).reshape(-1)


def _limite_caracteres(identifiant_voix):
    """Combien de caracteres cette voix peut lire en UN morceau.

    La fenetre du moteur (~2048 jetons, soit ~30 s) comprend la REFERENCE : une
    voix dont l'extrait fait 17 s ne peut pas lire 200 caracteres (~14 s de
    parole) -- le moteur tronquerait SANS RIEN DIRE. On calcule donc la place
    restante pour CHAQUE voix, d'apres la duree reelle de son extrait (mesuree
    une fois au reperage, dans l'en-tete du WAV).
    """
    duree = _voix_cache.get(identifiant_voix, (None, None, 0.0))[2]
    if not duree:
        return MAX_CARACTERES
    restant = FENETRE_TOTALE_S - duree - MARGE_FENETRE_S
    return max(CARACTERES_MINIMUM,
               min(MAX_CARACTERES, int(restant * CARACTERES_PAR_SECONDE)))


def generer_wav(texte, identifiant_voix):
    """Genere le WAV d'un texte, avec une voix. Renvoie les octets du WAV.

    Leve une exception si la voix est inconnue ou si la generation echoue : le
    service transforme cela en message clair pour le lecteur.

    Les morceaux d'une meme phrase sont recolles SANS silence ; un silence
    court est pose entre deux VRAIES phrases -- c'est ce qui donne un rythme
    naturel a l'ecoute (meme regle que le service XTTS et que l'atelier). Le
    silence de queue est ensuite ramene a SILENCE_QUEUE_S.
    """
    import numpy as np

    if _moteur is None:
        raise RuntimeError("le moteur n'est pas encore charge")
    if identifiant_voix not in _voix_cache:
        raise ValueError("voix inconnue : %s" % identifiant_voix)

    plan = plan_de_lecture(texte, _limite_caracteres(identifiant_voix))
    if not plan:
        raise ValueError("texte vide")

    silence = np.zeros(int(SILENCE_PHRASE_S * FREQUENCE), dtype=np.float32)

    with _verrou:                      # une seule generation a la fois
        sons = []
        for rang, (_phrase, morceaux) in enumerate(plan):
            if rang:
                sons.append(silence)
            for morceau in morceaux:
                sons.append(_lire_un_morceau(morceau, identifiant_voix))

    if not sons:
        raise ValueError("texte vide")
    audio = np.concatenate(sons)
    # Filet tres large : ne coupe que ce qu'aucune phrase francaise ne produit.
    audio = rogner_a_duree(audio, texte)
    return _wav_depuis_pcm(rogner_queue(audio))

# ==============================================================
# LE SERVICE HTTP (bibliotheque standard uniquement : rien a installer
# en plus de PyTorch et neutts)
# ==============================================================

class Repondeur(BaseHTTPRequestHandler):
    server_version = "NIMMNeutts/1.0"

    # --- reponses ------------------------------------------------

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

    # --- lecture du corps ----------------------------------------

    def _lire_corps(self):
        taille = int(self.headers.get("Content-Length") or 0)
        if taille <= 0:
            return {}
        brut = self.rfile.read(taille)
        return json.loads(brut.decode("utf-8"))

    # --- routes --------------------------------------------------

    def do_GET(self):
        route = self.path.split("?")[0]
        if route == "/sante":
            self._envoyer_json(200, dict(_infos))
        elif route == "/voix":
            self._envoyer_json(200, {
                "voix": sorted(_voix_cache.keys()),
                "nombre": len(_voix_cache),
            })
        else:
            self._envoyer_json(404, {"erreur": "adresse inconnue"})

    def do_POST(self):
        route = self.path.split("?")[0]

        if route == "/recharger":
            # Re-scanne le dossier des references SANS recharger le moteur :
            # permet d'ajouter une voix (un extrait + son texte) sans
            # redemarrer le service. Les references encodees deja en memoire
            # sont conservees.
            _repertorier_references()
            _infos["voix"] = len(_voix_cache)
            print("references rechargees : %d" % len(_voix_cache))
            self._envoyer_json(200, {"voix": len(_voix_cache),
                                     "liste": sorted(_voix_cache.keys())})
            return

        if route != "/tts":
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

        t0 = time.time()
        try:
            wav = generer_wav(texte, voix)
        except ValueError as erreur:
            self._envoyer_json(400, {"erreur": str(erreur)})
            return
        except Exception as erreur:          # panne du moteur
            print("ERREUR generation : %s" % erreur)
            self._envoyer_json(500, {"erreur": "generation impossible : %s" % erreur})
            return

        duree = time.time() - t0
        print("phrase generee  voix=%-32s  %5.1f s de calcul  %d octets"
              % (voix, duree, len(wav)))
        self._envoyer(200, wav, "audio/wav")

    # --- journal lisible ------------------------------------------

    def log_message(self, format, *args):
        """Une ligne courte par appel, lisible dans la fenetre du moteur.

        Les interrogations `GET /sante` ne sont PAS affichees : c'est le voyant
        du lecteur, qui demande toutes les 5 secondes si le moteur est pret --
        cela remplirait la fenetre sans rien apprendre (meme choix que le
        service XTTS).
        """
        ligne = format % args
        if 'GET /sante' in ligne:
            return
        print("%s - %s" % (self.address_string(), ligne))


class ServiceNeutts(ThreadingHTTPServer):
    """Serveur du moteur, avec le meme garde-fou que Kyutai et XTTS.

    Par defaut, Python autorise deux serveurs a ouvrir le MEME port (option
    SO_REUSEADDR) : sur Windows, deux moteurs pouvaient donc demarrer en
    silence (constate le 12/09/2026 avec Kyutai : deux modeles charges en meme
    temps, machine saturee). On interdit le partage : le deuxieme demarrage
    echoue proprement, le premier continue de repondre.
    """

    allow_reuse_address = False

def _surveiller_la_console():
    """Eteint le moteur si sa fenetre disparait (fenetre fermee).

    Pourquoi : sous Windows, un programme qui n'ecrit jamais dans sa console ne
    s'apercoit pas que celle-ci a ete fermee -- le moteur continuait alors de
    tourner (port occupe, memoire de la carte graphique gardee) alors que
    Laurent croyait l'avoir eteint (constate le 12/09/2026 avec Kyutai, puis
    repris tel quel pour XTTS). Ce gardien rend le geste naturel -- fermer la
    fenetre -- vraiment efficace.

    Il ne s'active que si le moteur tourne dans une VRAIE console (fenetre) :
    lance sans console (outils, tests, stdin redirige), il ne s'active pas.
    La variable NIMM_NEUTTS_SURVEILLER_CONSOLE=1 force l'activation, ce qui
    permet de tester le mecanisme.
    """
    force = os.environ.get("NIMM_NEUTTS_SURVEILLER_CONSOLE", "") == "1"
    try:
        est_console = bool(sys.stdin) and sys.stdin.isatty()
    except Exception:
        est_console = False
    if not (force or est_console):
        return

    time.sleep(5)          # on laisse la fenetre s'installer avant de veiller
    while True:
        try:
            touche = sys.stdin.read(1)
        except Exception:
            touche = ""
        if touche == "":
            print("")
            print("Fenetre fermee : arret du moteur de voix NeuTTS.")
            sys.stdout.flush()
            os._exit(0)


def _moteur_deja_en_route() -> bool:
    """Un moteur repond-il deja sur HOTE:PORT ? (test rapide, 0,5 s max)"""
    import socket
    try:
        with socket.create_connection((HOTE, PORT), timeout=0.5):
            return True
    except OSError:
        return False


def main():
    print("")
    print("===== NIMM ePub : appareil de voix NeuTTS (clonage) =====")

    if _moteur_deja_en_route():
        print("ARRET : un moteur NeuTTS tourne deja sur %s:%d."
              % (HOTE, PORT))
        print("Rien a faire : la fenetre deja ouverte suffit.")
        sys.exit(1)

    # Le port est ouvert AVANT le chargement du modele (~10 s a chaud, bien
    # plus long au tout premier lancement). Deux consequences voulues :
    #   1. le lecteur voit tout de suite qu'un moteur est en route ;
    #   2. pendant le chargement, /sante repond « pret : false » -- le lecteur
    #      ne propose donc pas encore les voix NeuTTS : c'est le principe des
    #      « voix ecoutables tout de suite » (14/09/2026).
    try:
        service = ServiceNeutts((HOTE, PORT), Repondeur)
    except OSError as erreur:
        print("ARRET : impossible d'ouvrir le port %d (%s)." % (PORT, erreur))
        print("Un autre programme occupe peut-etre ce port.")
        sys.exit(1)

    print("Adresse : http://%s:%d   (Ctrl+C pour arreter)" % (HOTE, PORT))
    print("")

    def _charger_en_fond():
        """Charge le moteur pendant que le service repond deja."""
        try:
            charger_moteur()
        except Exception as erreur:
            print("ECHEC du chargement du moteur : %s" % erreur)
        if not _infos["pret"]:
            # Inutile de laisser un service ouvert sans moteur : on s'arrete.
            # Le lecteur, lui, continue de fonctionner normalement.
            print("Le service s'arrete : le moteur n'a pas pu etre charge.")
            os._exit(1)
        print("Le moteur est pret : les phrases peuvent etre demandees.")

    threading.Thread(target=_charger_en_fond, daemon=True).start()
    # Gardien : fermer la fenetre eteint le moteur (voir _surveiller_la_console).
    threading.Thread(target=_surveiller_la_console, daemon=True).start()

    try:
        service.serve_forever()
    except KeyboardInterrupt:
        print("Arret demande : fermeture du service.")
    finally:
        service.server_close()


if __name__ == "__main__":
    main()






