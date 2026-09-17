# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import re
import os
import asyncio
import edge_tts
from modules import tts_cache as _tts_cache
from modules import audio_trim as _audio_trim
from modules import audio_rate as _audio_rate

# ==============================================================
# CONFIGURATION
# ==============================================================

DEFAULT_VOICE = "fr-CH-ArianeNeural"
DEFAULT_RATE  = "+0%"
DEFAULT_PITCH = "+0Hz"

# ==============================================================
# KOKORO TTS -- voix a accent etranger, francais force
# ==============================================================
# Meme mecanique que dans l'app NIMM de reference : le timbre (voice=)
# et la langue de prononciation (lang=) sont independants dans l'API
# Kokoro. En forcant lang="fr-fr" quel que soit le timbre choisi, la
# voix lit le francais avec l'accent naturel de son timbre d'origine.

from pathlib import Path as _Path
from threading import Lock as _Lock

_KOKORO_DIR         = _Path(__file__).parent.parent
KOKORO_MODEL_PATH   = _KOKORO_DIR / "kokoro-v1.0.onnx"
KOKORO_VOICES_PATH  = _KOKORO_DIR / "voices-v1.0.bin"

_kokoro = None
_kokoro_lock = _Lock()
_kokoro_infer_lock = _Lock()  # serielise l'inference : Kokoro n'est pas thread-safe
_kokoro_ready = False


def _load_kokoro():
    """Charge le modele Kokoro en memoire (appele une seule fois)."""
    global _kokoro, _kokoro_ready
    with _kokoro_lock:
        if _kokoro is None:
            from kokoro_onnx import Kokoro
            _kokoro = Kokoro(str(KOKORO_MODEL_PATH), str(KOKORO_VOICES_PATH))
        _kokoro_ready = True


def ensure_kokoro_loaded():
    """A appeler au demarrage du serveur : precharge Kokoro dans un
    thread separe pour ne jamais bloquer Edge TTS ni le reste de
    l'appli pendant le chargement (quelques secondes)."""
    import threading
    threading.Thread(target=_load_kokoro, daemon=True).start()


# Catalogue complet des 54 voix Kokoro, taguees par pays/langue d'origine
# du timbre (region) + genre -- meme structure que FRENCH_VOICES cote
# main.py, pour s'afficher sans rien changer dans les menus existants
# (narrateur + fenetre du casting). "stars" mis a 3 sur les voix
# italiennes (usage vise : Pastrini, Vampa) et sur les voix deja
# eprouvees dans l'app NIMM de reference, 2 par defaut sur les autres --
# purement indicatif, a ajuster a l'oreille au fil de l'usage.
KOKORO_VOICES = [
    # ==========================================================
    # NOS VOIX (atelier "NIMM Voix") -- ajoutees le 12/09/2026
    # 30 timbres crees par melange de voix Kokoro et valides a
    # l'oreille. Les 6 "voix de role" sont concues pour un
    # personnage (mamie, papi, narrateur, enfant, mystere, jeune)
    # -> 3 etoiles ; les autres -> 2 etoiles.
    # Region "France (NIMM Voix)" pour les retrouver d'un coup d'oeil.
    # ==========================================================
    {"id": "kokoro:ff_mamie",     "name": "Mamie",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 3},
    {"id": "kokoro:fm_papi",      "name": "Papi",      "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 3},
    {"id": "kokoro:fm_narrateur", "name": "Narrateur", "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 3},
    {"id": "kokoro:ff_enfant",    "name": "Enfant",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 3},
    {"id": "kokoro:fm_mystere",   "name": "Mystère",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 3},
    {"id": "kokoro:fm_jeune",     "name": "Jeune",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 3},
    {"id": "kokoro:ff_amelie",    "name": "Amélie",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_aurore",    "name": "Aurore",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 3},
    {"id": "kokoro:ff_chloe",     "name": "Chloé",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_clara",     "name": "Clara",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_delphine",  "name": "Delphine",  "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_elodie",    "name": "Élodie",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_julie",     "name": "Julie",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_louise",    "name": "Louise",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_maelle",    "name": "Maëlle",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_manon",     "name": "Manon",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_margaux",   "name": "Margaux",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_noemie",    "name": "Noémie",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_pauline",   "name": "Pauline",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 0},
    {"id": "kokoro:ff_romane",    "name": "Romane",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_sarah",     "name": "Sarah",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_solene",    "name": "Solène",    "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:ff_zoe",       "name": "Zoé",       "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:fm_antoine",   "name": "Antoine",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 2},
    {"id": "kokoro:fm_baptiste",  "name": "Baptiste",  "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 2},
    {"id": "kokoro:fm_camille",   "name": "Camille",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 0},
    {"id": "kokoro:fm_etienne",   "name": "Étienne",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 2},
    {"id": "kokoro:fm_hugo",      "name": "Hugo",      "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 0},
    {"id": "kokoro:fm_lucas",     "name": "Lucas",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 3},
    {"id": "kokoro:fm_vincent",   "name": "Vincent",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 2},
    # --- Etats-Unis (americain) ---
    {"id": "kokoro:af_alloy",   "name": "Alloy",      "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_aoede",   "name": "Aoede",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_bella",   "name": "Bella",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 3},
    {"id": "kokoro:af_heart",   "name": "Heart",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_jessica", "name": "Jessica",     "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_kore",    "name": "Kore",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_nicole",  "name": "Nicole",      "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_nova",    "name": "Nova",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_river",   "name": "River",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_sarah",   "name": "Sarah",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_sky",     "name": "Sky",         "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:am_adam",    "name": "Adam",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 2},
    {"id": "kokoro:am_echo",    "name": "Echo",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 2},
    {"id": "kokoro:am_eric",    "name": "Eric",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 2},
    {"id": "kokoro:am_fenrir",  "name": "Fenrir",      "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 2},
    {"id": "kokoro:am_liam",    "name": "Liam",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 2},
    {"id": "kokoro:am_michael", "name": "Michael",     "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 3},
    {"id": "kokoro:am_onyx",    "name": "Onyx",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 2},
    {"id": "kokoro:am_puck",    "name": "Puck",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 2},
    {"id": "kokoro:am_santa",   "name": "Santa",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "M", "stars": 2},
    # --- Royaume-Uni (britannique) ---
    {"id": "kokoro:bf_alice",    "name": "Alice",     "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "F", "stars": 2},
    {"id": "kokoro:bf_emma",     "name": "Emma",      "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "F", "stars": 3},
    {"id": "kokoro:bf_isabella", "name": "Isabella",  "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "F", "stars": 2},
    {"id": "kokoro:bf_lily",     "name": "Lily",      "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "F", "stars": 2},
    {"id": "kokoro:bm_daniel",   "name": "Daniel",    "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "M", "stars": 2},
    {"id": "kokoro:bm_fable",    "name": "Fable",     "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "M", "stars": 2},
    {"id": "kokoro:bm_george",   "name": "George",    "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "M", "stars": 3},
    {"id": "kokoro:bm_lewis",    "name": "Lewis",     "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "M", "stars": 2},
    # --- Espagne ---
    {"id": "kokoro:ef_dora",  "name": "Dora",  "region": "\U0001F1EA\U0001F1F8 Espagne", "gender": "F", "stars": 2},
    {"id": "kokoro:em_alex",  "name": "Alex",  "region": "\U0001F1EA\U0001F1F8 Espagne", "gender": "M", "stars": 2},
    {"id": "kokoro:em_santa", "name": "Santa", "region": "\U0001F1EA\U0001F1F8 Espagne", "gender": "M", "stars": 2},
    # --- France (timbre natif Kokoro, sans accent force) ---
    {"id": "kokoro:ff_siwis", "name": "Siwis", "region": "\U0001F1EB\U0001F1F7 France (Kokoro)", "gender": "F", "stars": 2},
    # --- Inde (hindi) ---
    {"id": "kokoro:hf_alpha", "name": "Alpha", "region": "\U0001F1EE\U0001F1F3 Inde (Hindi)", "gender": "F", "stars": 2},
    {"id": "kokoro:hf_beta",  "name": "Beta",  "region": "\U0001F1EE\U0001F1F3 Inde (Hindi)", "gender": "F", "stars": 2},
    {"id": "kokoro:hm_omega", "name": "Omega", "region": "\U0001F1EE\U0001F1F3 Inde (Hindi)", "gender": "M", "stars": 2},
    {"id": "kokoro:hm_psi",   "name": "Psi",   "region": "\U0001F1EE\U0001F1F3 Inde (Hindi)", "gender": "M", "stars": 2},
    # --- Italie (Pastrini, Vampa...) ---
    {"id": "kokoro:if_sara",   "name": "Sara",   "region": "\U0001F1EE\U0001F1F9 Italie", "gender": "F", "stars": 3},
    {"id": "kokoro:im_nicola", "name": "Nicola", "region": "\U0001F1EE\U0001F1F9 Italie", "gender": "M", "stars": 3},
    # --- Japon ---
    {"id": "kokoro:jf_alpha",      "name": "Alpha",      "region": "\U0001F1EF\U0001F1F5 Japon", "gender": "F", "stars": 2},
    {"id": "kokoro:jf_gongitsune", "name": "Gongitsune", "region": "\U0001F1EF\U0001F1F5 Japon", "gender": "F", "stars": 2},
    {"id": "kokoro:jf_nezumi",     "name": "Nezumi",     "region": "\U0001F1EF\U0001F1F5 Japon", "gender": "F", "stars": 2},
    {"id": "kokoro:jf_tebukuro",   "name": "Tebukuro",   "region": "\U0001F1EF\U0001F1F5 Japon", "gender": "F", "stars": 1},
    {"id": "kokoro:jm_kumo",       "name": "Kumo",       "region": "\U0001F1EF\U0001F1F5 Japon", "gender": "M", "stars": 2},
    # --- Portugal / Bresil ---
    {"id": "kokoro:pf_dora",  "name": "Dora",  "region": "\U0001F1F5\U0001F1F9 Portugal/Bresil", "gender": "F", "stars": 2},
    {"id": "kokoro:pm_alex",  "name": "Alex",  "region": "\U0001F1F5\U0001F1F9 Portugal/Bresil", "gender": "M", "stars": 2},
    {"id": "kokoro:pm_santa", "name": "Santa", "region": "\U0001F1F5\U0001F1F9 Portugal/Bresil", "gender": "M", "stars": 2},
    # --- Chine ---
    {"id": "kokoro:zf_xiaobei",  "name": "Xiaobei",  "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "F", "stars": 1},
    {"id": "kokoro:zf_xiaoni",   "name": "Xiaoni",   "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "F", "stars": 1},
    {"id": "kokoro:zf_xiaoxiao", "name": "Xiaoxiao", "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "F", "stars": 1},
    {"id": "kokoro:zf_xiaoyi",   "name": "Xiaoyi",   "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "F", "stars": 1},
    {"id": "kokoro:zm_yunjian",  "name": "Yunjian",  "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "M", "stars": 1},
    {"id": "kokoro:zm_yunxi",    "name": "Yunxi",    "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "M", "stars": 1},
    {"id": "kokoro:zm_yunxia",   "name": "Yunxia",   "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "M", "stars": 1},
    {"id": "kokoro:zm_yunyang",  "name": "Yunyang",  "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "M", "stars": 1},
]


def _kokoro_voice_id(voice: str) -> str:
    """Retire le prefixe 'kokoro:' pour obtenir l'id reel attendu par Kokoro."""
    return voice.split(":", 1)[1] if ":" in voice else voice

# Taille max d'un bloc envoyé à Edge TTS en une fois. Monté à 4000 pour
# que les groupes client (max ~1500 car.) tiennent toujours en un seul
# chunk : chaque chunk est une "utterance" Edge distincte, donc une
# couture/pause potentielle au milieu du texte a chaque decoupe.
MAX_CHUNK_CHARS = 4000

# ==============================================================
# NETTOYAGE DU TEXTE
# ==============================================================

# Abreviations developpees avant la synthese vocale : la voix lit le mot
# complet ("Monsieur") au lieu de lire la lettre puis de marquer une pause
# sur le point parasite ("M" + pause).
# L'ORDRE COMPTE : MM. avant M., Mmes avant Mme, Mlles avant Mlle.
# Garde-fous :
#   - "(?<![.\\w])M" -> on ne touche pas aux initiales enchainees (R.M.)
#   - lookahead "(?=\\s|$|»|\")" -> uniquement si l'abreviation est un mot
#     complet (suivi d'un espace, d'une fin de segment, d'un guillemet)
#   - les mots commencant par St/Pr/Dr (Stéphane, Proust, Drouot...) ne
#     sont pas touches car il n'y a pas de frontiere de mot apres l'abreviation
ABBREVIATION_RULES = [
    (re.compile(r"\bMM\.(?=\s|$|»|\")"), "Messieurs"),
    (re.compile(r"(?<![.\w])M\b\.?(?=\s+[A-ZÀ-ÖØ-Ý])"), "Monsieur"),
    (re.compile(r"(?<![.\w])M\.(?=\s|$|»|\")"), "Monsieur"),
    (re.compile(r"\bMr\.?(?=\s|$|»|\")"), "Monsieur"),
    (re.compile(r"\bMgr\b\.?(?=\s|$|»|\")"), "Monseigneur"),
    (re.compile(r"\bMmes\b\.?(?=\s|$|»|\")"), "Mesdames"),
    (re.compile(r"\bMme\b\.?(?=\s|$|»|\")"), "Madame"),
    (re.compile(r"\bMlles\b\.?(?=\s|$|»|\")"), "Mesdemoiselles"),
    (re.compile(r"\bMlle\b\.?(?=\s|$|»|\")"), "Mademoiselle"),
    (re.compile(r"\bDr\b\.?(?=\s|$|»|\")"), "Docteur"),
    (re.compile(r"\bPr\b\.?(?=\s|$|»|\")"), "Professeur"),
    (re.compile(r"\bSte\b\.?(?=\s|$|»|\")"), "Sainte"),
    (re.compile(r"\bSt\b\.?(?=\s|$|»|\")"), "Saint"),
    (re.compile(r"(?<!\w)N°(?=\s|$|»|\"|\d)"), "numéro"),
    (re.compile(r"(?<!\w)n°(?=\s|$|»|\"|\d)"), "numéro"),
]


def _expand_abbreviations(text: str) -> str:
    """Developpe les abreviations courantes du francais (M. -> Monsieur,
    Mme -> Madame, Dr -> Docteur, etc.) pour que la voix lise le mot
    complet au lieu de lire une seule lettre puis de marquer une pause
    sur le point de l'abreviation."""
    for pattern, replacement in ABBREVIATION_RULES:
        text = pattern.sub(replacement, text)
    return text


def _clean_text(text: str) -> str:
    """Prepare le texte pour la synthese vocale."""

    # Sauts de ligne -> simple espace (pas de virgule, qui ajouterait une
    # pause artificielle au milieu d'un texte deja decoupe en phrases).
    text = text.replace("\n", " ")

    # Supprime les references entre crochets [1], [note], [i], etc.
    text = re.sub(r'\[[^\]]{0,30}\]', '', text)

    # Point-virgule -> virgule (17/09/2026, constat de Laurent) : les moteurs
    # neuronaux essaient de PRONONCER la ponctuation forte qu'ils ne savent pas
    # ignorer, et le « ; » sortait parfois en « euh ». La virgule garde la
    # respiration sans le son parasite.
    text = text.replace(';', ',')

    # Deux-points -> virgule (17/09/2026 au soir, constat de Laurent : « la
    # ponctuation des ":" n'a pas de pause du tout »). On ne touche qu'au
    # deux-points PRECEDE D'UNE ESPACE -- c'est la typographie francaise, et
    # cela evite de casser « 14:30 » ou une adresse.
    text = re.sub(r'\s+:\s*', ', ', text)

    # Parentheses -> virgules (meme jour, meme constat) : le moteur les ignore,
    # donc l'incise n'etait entouree d'AUCUNE pause. Deux virgules redonnent la
    # respiration attendue de part et d'autre.
    text = text.replace('(', ', ').replace(')', ',')

    # Supprime les caracteres de controle
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Supprime les emojis
    text = re.sub(
        r"[\U00010000-\U0010ffff"
        r"\U0001F600-\U0001F64F"
        r"\U0001F300-\U0001F5FF"
        r"\U0001F680-\U0001F6FF"
        r"\U0001F1E0-\U0001F1FF]+",
        "", text, flags=re.UNICODE
    )

    # Developpe les abreviations (M. -> Monsieur, Mme -> Madame, etc.)
    text = _expand_abbreviations(text)

    # Normalise les suites de points en une seule suspension. Edge TTS
    # marque une pause sur CHAQUE point sinon ("...." = 4 pauses courtes
    # a la place d'une seule). Apres l'expansion des abreviations, les
    # points restants sont de vrais points de phrase.
    text = re.sub(r"\s*\.\s*\.\s*\.", "…", text)   # ". . ." -> "..."
    text = re.sub(r"\.{2,}", "…", text)             # "..." / ".." -> "…"

    # Nettoie les virgules et espaces en double
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\s{2,}", " ", text)

    # Supprime les espaces parasites avant un point/virgule/point de
    # suspension (typo). Les espaces avant ? ! : ; sont CONSERVEES : c'est
    # la typographie francaise et Edge TTS les prononce naturellement.
    text = re.sub(r"\s+([.,…])", r"\1", text)

    text = text.strip()

    # Fin de segment : une virgule/point-virgule/deux-points en position
    # finale (segment de phrase decoupe par _split_long_sentence) devient
    # un vrai point de fin de segment -- ajouter un point apres aurait fait
    # lire "virgule puis point" a la voix. On retire aussi l'espace
    # typographique qui precede ; et : en francais.
    if text and text[-1] in ',;:':
        text = text[:-1].rstrip() + '.'
    elif text and text[-1] not in '.!?:…»"':
        text += '.'

    return text


def _split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list:
    """
    Decoupe le texte en blocs de max_chars caracteres maximum,
    en coupant aux phrases (. ! ? …) pour eviter les coupures en milieu de mot.
    Une phrase seule plus longue que max_chars est decoupee en priorite
    aux virgules/points-virgules (pauses naturelles), jamais en plein milieu
    d'un mot -- sinon Edge TTS marque une pause au milieu du texte.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""

    # Decoupe aux fins de phrases
    sentences = re.split(r"(?<=[.!?…])\s+", text)

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            # Si une phrase seule depasse la limite, on la decoupe aux
            # virgules/points-virgules d'abord, puis forcement en morceaux.
            if len(sentence) > max_chars:
                chunks.extend(_split_long_sentence(sentence, max_chars))
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def _split_long_sentence(sentence: str, max_chars: int) -> list:
    """Decoupe une phrase trop longue, en priorite aux virgules/points-virgules
    (pauses naturelles) puis en morceaux de max_chars en dernier recours."""
    pieces = re.split(r"(?<=[,;:])\s+", sentence)
    out = []
    buf = ""
    for piece in pieces:
        if buf and len(buf) + len(piece) + 1 > max_chars:
            out.append(buf)
            buf = ""
        if len(piece) > max_chars:
            # Dernier recours : coupure dure en morceaux de max_chars
            for i in range(0, len(piece), max_chars):
                out.append(piece[i:i + max_chars])
            buf = ""
        else:
            buf = ((buf + " " + piece) if buf else piece).strip()
    if buf:
        out.append(buf)
    return out


# ==============================================================
# SYNTHESE VOCALE
# ==============================================================

async def synthesize_stream(text: str, voice: str = DEFAULT_VOICE,
                            rate: str = DEFAULT_RATE,
                            pitch: str = DEFAULT_PITCH):
    """
    Generateur async : stream l'audio MP3 chunk par chunk.
    Utilise directement par la route /api/tts de main.py.
    Gere automatiquement les textes longs en les decoupant.
    Chaque chunk passe par le cache disque : un passage deja genere est
    renvoye depuis le disque sans re-solliciter Edge TTS.
    """
    text = _clean_text(text)
    if not text:
        return

    chunks = _split_into_chunks(text)

    for chunk in chunks:
        cached = _tts_cache.get_audio(chunk, voice, rate, pitch, "mp3")
        if cached is not None:
            yield cached
            continue

        parts = []
        communicate = edge_tts.Communicate(chunk, voice, rate=rate, pitch=pitch)
        async for part in communicate.stream():
            if part["type"] == "audio":
                parts.append(part["data"])
        if not parts:
            continue

        raw = b"".join(parts)
        # Rognage des silences de bord : Edge ajoute ~1 s de silence en fin
        # de phrase. Le fichier mis en cache ET envoye au client est donc
        # nettoye -> rythme naturel entre les phrases, surbrillance
        # synchrone (session du 08/09/2026).
        audio = _audio_trim.trim_mp3_silence(raw)
        _tts_cache.put_audio(chunk, voice, rate, pitch, "mp3", audio)
        yield audio


async def synthesize_bytes(text: str, voice: str = DEFAULT_VOICE,
                           rate: str = DEFAULT_RATE) -> bytes:
    """
    Retourne l'audio complet en bytes.
    Utile pour les textes courts (titres de chapitres, etc.)
    """
    audio = b""
    async for chunk in synthesize_stream(text, voice, rate):
        audio += chunk
    return audio


# ==============================================================
# PITCH / VITESSE -- conversions communes + post-traitement pitch
# ==============================================================
# Format unifie identique a Edge TTS (deja utilise partout dans l'appli) :
# rate  = "+0%"  / "-15%" / "+20%" ...
# pitch = "+0Hz" / "-15Hz" / "+20Hz" ...
# Edge gere nativement les deux. Kokoro et Piper savent gerer la vitesse
# nativement (speed / length_scale) mais pas le pitch -- pour le pitch,
# on synthetise normalement puis on decale en post-traitement (librosa).

def _percent_to_speed(rate: str) -> float:
    """'+10%' -> 1.10, '-20%' -> 0.80. Borne a [0.5, 2.0] par securite."""
    try:
        pct = float(rate.replace("%", "").replace("+", ""))
    except (ValueError, AttributeError):
        pct = 0.0
    speed = 1.0 + (pct / 100.0)
    return max(0.5, min(2.0, speed))


def _percent_to_length_scale(rate: str) -> float:
    """Piper : length_scale est l'inverse de la vitesse (plus grand = plus lent)."""
    speed = _percent_to_speed(rate)
    return 1.0 / speed


def _hz_to_semitones(pitch: str) -> float:
    """
    '+15Hz' -> ~1.9 demi-tons, en coherence avec le pas de +8Hz deja
    utilise dans voice_casting.py pour differencier deux personnages
    partageant la meme voix (+8Hz = ~1 demi-ton). Borne a [-6, +6].
    """
    try:
        hz = float(pitch.replace("Hz", "").replace("+", ""))
    except (ValueError, AttributeError):
        hz = 0.0
    semitones = hz / 8.0
    return max(-6.0, min(6.0, semitones))


def _apply_pitch_shift(wav_bytes: bytes, semitones: float) -> bytes:
    """Decale le pitch d'un WAV en memoire, sans toucher a la duree.
    No-op si le decalage est negligeable (evite un traitement inutile).
    Utilise pedalboard (Rubber Band Library) plutot que librosa : le
    vocodeur de phase de librosa produit un effet caverneux/echo marque
    sur de la voix parlee -- Rubber Band est concu pour eviter ce
    defaut (phase-locking sur les transitoires), constat confirme par
    Laurent a l'ecoute reelle."""
    if abs(semitones) < 0.05 or not wav_bytes:
        return wav_bytes

    import io
    import soundfile as sf
    from pedalboard import Pedalboard, PitchShift

    buffer_in = io.BytesIO(wav_bytes)
    samples, sample_rate = sf.read(buffer_in, dtype="float32")

    board = Pedalboard([PitchShift(semitones=semitones)])
    shifted = board(samples, sample_rate)

    buffer_out = io.BytesIO()
    sf.write(buffer_out, shifted, sample_rate, format="WAV")
    return buffer_out.getvalue()


async def synthesize_kokoro(text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """
    Synthese Kokoro pour une phrase. Le francais est FORCE en dur
    (lang="fr-fr") quel que soit le timbre (voice) choisi -- c'est ce
    qui produit l'effet d'accent tout en gardant une prononciation
    francaise comprehensible (pas de charabia).
    Vitesse geree nativement par Kokoro (speed=). Pitch applique en
    post-traitement (librosa) si different de +0Hz.
    Kokoro est synchrone/CPU -- execute dans un thread separe pour ne
    pas bloquer le serveur pendant la generation.
    """
    text = _clean_text(text)
    if not text:
        return b""

    # Cache disque : un passage deja genere (texte + voix + rate + pitch)
    # est renvoye sans recharger le modele ni re-synthetiser.
    cached = _tts_cache.get_audio(text, voice, rate, pitch, "wav")
    if cached is not None:
        return cached

    if not _kokoro_ready:
        _load_kokoro()  # 1ere utilisation : chargement synchrone (~qqs secondes), une seule fois

    voice_id = _kokoro_voice_id(voice)
    speed = _percent_to_speed(rate)
    semitones = _hz_to_semitones(pitch)

    def _generate():
        import io
        import soundfile as sf
        with _kokoro_infer_lock:
            samples, sample_rate = _kokoro.create(
                text, voice=voice_id, speed=speed, lang="fr-fr"
            )
        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format="WAV")
        wav_bytes = buffer.getvalue()
        return _apply_pitch_shift(wav_bytes, semitones)

    wav_bytes = await asyncio.to_thread(_generate)
    _tts_cache.put_audio(text, voice, rate, pitch, "wav", wav_bytes)
    return wav_bytes


# ==============================================================
# PIPER TTS -- moteur local, voix multi-locuteurs (fr_FR-mls-medium
# et 3 modeles complementaires), format d'id "piper:<modele>:<speaker_id>"
# ==============================================================
# Meme logique que Kokoro : chargement en memoire au demarrage dans un
# thread separe, cache par modele pour ne jamais recharger un .onnx
# deja en RAM. Le "length_scale" (vitesse) est deja cable en parametre,
# pret pour le reglage voix par voix a venir dans le casting.

PIPER_MODEL_FILES = {
    "siwis": "fr_FR-siwis-medium",
    "upmc":  "fr_FR-upmc-medium",
    "tom":   "fr_FR-tom-medium",
}

# Catalogue des voix Piper retenues -- le modele mls (125 locuteurs) a ete
# ecarte apres test en conditions reelles : la quasi-totalite des voix sont
# issues d'enregistrements amateurs LibriVox (bruit de fond, souffle,
# hachures), constat deja fait sur l'appli NIMM. Seules les 3 voix
# studio restent utilisables.
PIPER_VOICES = [
    {"id": "piper:siwis:0", "name": "Siwis",   "region": "\U0001F1EB\U0001F1F7 France (Piper)", "gender": "F", "stars": 3},
    {"id": "piper:tom:0",   "name": "Tom",     "region": "\U0001F1EB\U0001F1F7 France (Piper)", "gender": "M", "stars": 0},
    {"id": "piper:upmc:0",  "name": "Jessica", "region": "\U0001F1EB\U0001F1F7 France (Piper)", "gender": "F", "stars": 3},
    {"id": "piper:upmc:1",  "name": "Pierre",  "region": "\U0001F1EB\U0001F1F7 France (Piper)", "gender": "M", "stars": 1},
]

_piper_voices = {}
_piper_lock = _Lock()
_piper_infer_lock = _Lock()  # serielise l'inference : Piper n'est pas thread-safe


def _load_piper_model(model_key: str):
    """Charge un modele Piper en memoire (idempotent, une seule fois par modele)."""
    with _piper_lock:
        if model_key not in _piper_voices:
            from piper import PiperVoice
            model_path = _KOKORO_DIR / f"{PIPER_MODEL_FILES[model_key]}.onnx"
            _piper_voices[model_key] = PiperVoice.load(str(model_path))


def ensure_piper_loaded():
    """A appeler au demarrage du serveur : precharge les 4 modeles Piper
    dans un thread separe pour ne jamais bloquer le reste de l'appli."""
    import threading

    def _preload_all():
        for key in PIPER_MODEL_FILES:
            _load_piper_model(key)

    threading.Thread(target=_preload_all, daemon=True).start()


def _piper_voice_id(voice: str):
    """Decoupe 'piper:<modele>:<speaker_id>' -> (modele, speaker_id int)."""
    _, model_key, speaker_id = voice.split(":", 2)
    return model_key, int(speaker_id)


async def synthesize_piper(text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """
    Synthese Piper pour une phrase. Chargement du modele a la volee s'il
    n'est pas deja en memoire (sans effet si deja charge). Vitesse geree
    nativement par Piper (length_scale). Pitch applique en post-traitement
    (librosa) si different de +0Hz. Execute dans un thread separe (Piper
    est synchrone/CPU) pour ne pas bloquer le serveur pendant la generation.
    """
    text = _clean_text(text)
    if not text:
        return b""

    # Cache disque : un passage deja genere (texte + voix + rate + pitch)
    # est renvoye sans recharger le modele ni re-synthetiser.
    cached = _tts_cache.get_audio(text, voice, rate, pitch, "wav")
    if cached is not None:
        return cached

    model_key, speaker_id = _piper_voice_id(voice)
    _load_piper_model(model_key)
    length_scale = _percent_to_length_scale(rate)
    semitones = _hz_to_semitones(pitch)

    def _generate():
        import io
        import wave
        from piper import SynthesisConfig

        with _piper_infer_lock:
            piper_voice = _piper_voices[model_key]
            syn_config = SynthesisConfig(speaker_id=speaker_id, length_scale=length_scale)
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                piper_voice.synthesize_wav(text, wav_file, syn_config=syn_config)
        wav_bytes = buffer.getvalue()
        return _apply_pitch_shift(wav_bytes, semitones)

    wav_bytes = await asyncio.to_thread(_generate)
    _tts_cache.put_audio(text, voice, rate, pitch, "wav", wav_bytes)
    return wav_bytes


# ==============================================================
# KYUTAI TTS -- moteur francais (35 voix francaises libres)
# ==============================================================
# Quatrieme moteur, ajoute le 12/09/2026. Kyutai TTS 1.6B est un moteur
# de Kyutai (laboratoire parisien) : poids CC BY 4.0, et une banque de
# 35 voix FRANCAISES libres (CC BY 4.0, jeu de donnees CML-TTS) ou chaque
# voix est une empreinte de 256 Ko fournie toute prete (aucun entrainement).
#
# Particularite : ce moteur exige PyTorch (environnement Python 3.12),
# alors que NIMM ePub tourne sur Python 3.14 -- les deux ne peuvent pas
# cohabiter. Le moteur vit donc DANS SON PROPRE SERVICE
# (`kyutai_service/servir_kyutai.py`, lance par DEMARRER_KYUTAI.bat) et le
# lecteur l'appelle en HTTP local, comme il appelle Edge TTS par le reseau.
#
# Vitesse et hauteur : le moteur n'en a AUCUNE en natif. La vitesse est
# appliquee apres coup par ffmpeg (modules/audio_rate.py) et la hauteur par
# le post-traitement deja utilise pour Kokoro et Piper (_apply_pitch_shift).

KYUTAI_URL = os.environ.get("NIMM_KYUTAI_URL", "http://127.0.0.1:8082")
# Delai maximal d'attente du service : une phrase se calcule en gros en
# deux fois sa duree de lecture. Large, donc.
KYUTAI_DELAI_S = float(os.environ.get("NIMM_KYUTAI_DELAI", "240") or "240")

# Catalogue des 35 voix francaises libres. `gender` est renseigne a l'ecoute
# (mesure de hauteur sur les enregistrements de reference + validation de
# Laurent) ; `stars` suit le meme principe que les voix Kokoro : il sert au
# tri du pool automatique du casting.
# Region "France (Kyutai)" pour les retrouver d'un coup d'oeil.
# ORDRE : exactement le tri des identifiants de fichiers (sorted()) -- le
# numero affiche « Kyutai NN » correspond donc au fichier NN de l'ecoute
# (kyutai_service/sortie_ecoute_toutes/) et reste stable dans le temps.
KYUTAI_VOICES = [
    # Genre et etoiles : releves a l'ecoute par Laurent le 12/09/2026.
    # (`gender` : F = femme, M = masculin -- MEME convention que KOKORO_VOICES
    #  et PIPER_VOICES, indispensable au pool automatique du casting.
    #  `stars` : 3 = excellente, 1 = passable, 0 = NON retenue -- elle reste
    #  disponible a la main mais n'entre pas dans le pool automatique, comme
    #  les voix Piper ecartees.)
    # NB : la mesure de hauteur sur les enregistrements d'origine avait
    # propose un autre genre pour 19 de ces voix (voix feminines graves
    # notamment) : c'est bien l'ecoute qui fait foi.
    {"id": "kyutai:10087_11650_000028-0002", "name": "Adèle", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 2},      # etait Kyutai 01
    {"id": "kyutai:10177_10625_000134-0003", "name": "Blanche", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 2},    # etait Kyutai 02
    {"id": "kyutai:10179_11051_000005-0001", "name": "Céleste", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 1},    # etait Kyutai 03
    {"id": "kyutai:12080_11650_000047-0001", "name": "Diane", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 2},      # etait Kyutai 04
    {"id": "kyutai:12205_11650_000004-0002", "name": "Éléonore", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},   # etait Kyutai 05
    {"id": "kyutai:12977_10625_000037-0001", "name": "Fanny", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 2},      # etait Kyutai 06
    {"id": "kyutai:1406_1028_000009-0003", "name": "Augustin", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 1},    # etait Kyutai 07
    {"id": "kyutai:1591_1028_000108-0004", "name": "Geneviève", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},   # etait Kyutai 08
    {"id": "kyutai:1770_1028_000036-0002", "name": "Bertrand", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},    # etait Kyutai 09
    {"id": "kyutai:2114_1656_000053-0001", "name": "Claude", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 1},      # etait Kyutai 10, accent canadien
    {"id": "kyutai:2154_2576_000020-0003", "name": "Hélène", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 2},      # etait Kyutai 11
    {"id": "kyutai:2216_1745_000007-0001", "name": "Damien", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 1},      # etait Kyutai 12, accent canadien
    {"id": "kyutai:2223_1745_000009-0002", "name": "Edmond", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 1},      # etait Kyutai 13
    {"id": "kyutai:2465_1943_000152-0002", "name": "Irène", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 1},       # etait Kyutai 14
    {"id": "kyutai:296_1028_000022-0001", "name": "Fernand", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 1},      # etait Kyutai 15
    {"id": "kyutai:3267_1902_000075-0001", "name": "Jeanne", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 1},      # etait Kyutai 16
    {"id": "kyutai:4193_3103_000004-0001", "name": "Gaston", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 17
    {"id": "kyutai:4482_3103_000063-0001", "name": "Hubert", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 2},      # etait Kyutai 18
    {"id": "kyutai:4724_3731_000031-0001", "name": "Isidore", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 2},     # etait Kyutai 19
    {"id": "kyutai:4937_3731_000004-0001", "name": "Julien", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 20
    {"id": "kyutai:5207_3078_000031-0002", "name": "Victoire", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},    # etait Kyutai 21
    {"id": "kyutai:5476_3103_000072-0001", "name": "Mathilde", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},    # etait Kyutai 22
    {"id": "kyutai:577_394_000070-0001", "name": "Ninon", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},         # etait Kyutai 23
    {"id": "kyutai:5790_4893_000052-0001", "name": "Léon", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},        # etait Kyutai 24
    {"id": "kyutai:579_2548_000015-0001", "name": "Odette", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},       # etait Kyutai 25
    {"id": "kyutai:5830_4703_000037-0001", "name": "Perrine", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 1},     # etait Kyutai 26
    {"id": "kyutai:6318_7016_000027-0002", "name": "Marcel", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 2},      # etait Kyutai 27
    {"id": "kyutai:7142_2432_000124-0003", "name": "Norbert", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 2},     # etait Kyutai 28
    {"id": "kyutai:7400_2928_000100-0001", "name": "Renée", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 1},       # etait Kyutai 29
    {"id": "kyutai:7591_6742_000149-0002", "name": "Suzanne", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 1},     # etait Kyutai 30
    {"id": "kyutai:7601_7727_000062-0001", "name": "Octave", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 2},      # etait Kyutai 31
    {"id": "kyutai:7762_8734_000048-0002", "name": "Monique", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 2},     # etait Kyutai 32
    {"id": "kyutai:8128_7016_000047-0002", "name": "Quentin", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 0},     # etait Kyutai 33, NON retenue a l'ecoute
    {"id": "kyutai:928_486_000075-0001", "name": "Raymond", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 34
    {"id": "kyutai:9834_9697_000150-0003", "name": "Simon", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 2},      # etait Kyutai 35
]


class KyutaiIndisponible(RuntimeError):
    """Le service Kyutai ne repond pas (moteur eteint ou en chargement)."""


def _kyutai_voix_id(voice: str) -> str:
    """Retire le prefixe 'kyutai:' pour obtenir l'identifiant de la voix."""
    return voice.split(":", 1)[1] if ":" in voice else voice


async def _demander_au_moteur_kyutai(texte: str, identifiant_voix: str,
                                     contexte: str = "") -> bytes:
    """Envoie une phrase au service Kyutai et renvoie le WAV brut.

    `contexte` : la fin de la phrase precedente (facultatif). Le service lit
    « contexte + phrase » et ne renvoie que la phrase, coupee dans un silence.
    """
    import httpx

    corps = {"texte": texte, "voix": identifiant_voix}
    if contexte:
        corps["contexte"] = contexte

    try:
        async with httpx.AsyncClient(timeout=KYUTAI_DELAI_S) as client:
            reponse = await client.post(
                KYUTAI_URL + "/tts",
                json=corps,
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
            httpx.RemoteProtocolError, httpx.WriteError) as erreur:
        raise KyutaiIndisponible(
            "Le moteur de voix Kyutai ne repond pas ("
            + type(erreur).__name__ + "). Double-clique sur "
            "DEMARRER_KYUTAI.bat, puis relance la lecture."
        )

    if reponse.status_code != 200:
        detail = ""
        try:
            detail = (reponse.json() or {}).get("erreur", "")
        except Exception:
            detail = ""
        raise KyutaiIndisponible(
            "Le moteur de voix Kyutai a refuse la phrase (code %d%s)."
            % (reponse.status_code, (" : " + detail) if detail else "")
        )

    return reponse.content


async def synthesize_kyutai(text: str, voice: str, rate: str = "+0%",
                            pitch: str = "+0Hz",
                            contexte: str = "") -> bytes:
    """
    Synthese Kyutai pour une phrase. Le moteur tourne dans son propre
    service (Python 3.12 + PyTorch), appele ici en HTTP local.

    `contexte` (facultatif) : la FIN DE LA PHRASE PRECEDENTE (idee de Laurent,
    17/09/2026). Le moteur lit « contexte + phrase » puis coupe pour ne livrer
    que la phrase : la voix ne demarre plus a froid, ce qui supprime les sautes
    de volume et rend la lecture plus « chantee ». Il ENTRE DANS LA CLE DE
    CACHE : la meme phrase apres un autre contexte est un autre audio.

    Vitesse : aucun reglage natif -> post-traitement ffmpeg (atempo).
    Hauteur : aucun reglage natif -> post-traitement _apply_pitch_shift
    (Rubber Band), comme pour Kokoro et Piper.
    L'audio final est mis en cache disque, exactement comme les autres
    moteurs : un passage deja lu ne redemande rien au moteur.
    """
    text = _clean_text(text)
    if not text:
        return b""

    contexte = _clean_text(contexte) if contexte else ""
    cle = (contexte + "\x00" + text) if contexte else text

    cached = _tts_cache.get_audio(cle, voice, rate, pitch, "wav")
    if cached is not None:
        return cached

    wav_bytes = await _demander_au_moteur_kyutai(text, _kyutai_voix_id(voice),
                                                 contexte)
    if not wav_bytes:
        return b""

    # Vitesse puis hauteur (aucun des deux n'existe dans le moteur).
    wav_bytes = _audio_rate.appliquer_vitesse(wav_bytes, _percent_to_speed(rate))
    wav_bytes = _apply_pitch_shift(wav_bytes, _hz_to_semitones(pitch))

    _tts_cache.put_audio(cle, voice, rate, pitch, "wav", wav_bytes)
    return wav_bytes


# ==============================================================
# XTTS v2 -- moteur de CLONAGE (35 voix francaises, memes echantillons
# que Kyutai), branche le 14/09/2026
# ==============================================================
# Cinquieme moteur. XTTS v2 (bibliotheque coqui-tts, maintenue par le
# laboratoire suisse Idiap) clone une voix a partir d'un extrait audio :
# les 35 extraits francais libres deja utilises par Kyutai (CC BY 4.0,
# CML-TTS) servent ici de "voix a imiter", d'ou les memes identifiants
# et les memes prenoms dans le catalogue -- seule la region affichee
# change ("XTTS" au lieu de "Kyutai") pour les distinguer d'un coup
# d'oeil dans les menus.
#
# Meme raison de service separe que Kyutai : XTTS a besoin de PyTorch
# (Python 3.12), incompatible avec le Python 3.14 du lecteur. Un seul
# des deux moteurs peut tourner a la fois (une seule carte graphique).
#
# Licence a retenir (voir xtts_service/ATTRIBUTION.md) : le modele est
# en Coqui Public Model License (CPML), usage NON commercial -- valable
# aussi pour l'audio produit. C'est un moteur d'essai pour l'ecoute
# personnelle de Laurent, jamais partage.
#
# Vitesse et hauteur : aucun reglage natif -> memes post-traitements
# que Kyutai (ffmpeg pour la vitesse, Rubber Band pour la hauteur).

XTTS_URL = os.environ.get("NIMM_XTTS_URL", "http://127.0.0.1:8083")
# XTTS est plus lent que Kyutai (~x3 le temps reel, mesure) : delai large.
XTTS_DELAI_S = float(os.environ.get("NIMM_XTTS_DELAI", "240") or "240")

# Etoiles PROVISOIRES (14/09/2026) : reprises telles quelles des voix
# Kyutai correspondantes, puisque ce sont les MEMES echantillons
# d'origine -- a corriger apres l'ecoute complete des 35 voix XTTS
# (le rendu du clonage peut differer de celui de Kyutai).
XTTS_VOICES = [
    {"id": "xtts:10087_11650_000028-0002", "name": "Adèle", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 2},
    {"id": "xtts:10177_10625_000134-0003", "name": "Blanche", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 2},
    {"id": "xtts:10179_11051_000005-0001", "name": "Céleste", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 1},
    {"id": "xtts:12080_11650_000047-0001", "name": "Diane", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:12205_11650_000004-0002", "name": "Éléonore", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 2},
    {"id": "xtts:12977_10625_000037-0001", "name": "Fanny", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 2},
    {"id": "xtts:1406_1028_000009-0003", "name": "Augustin", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:1591_1028_000108-0004", "name": "Geneviève", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:1770_1028_000036-0002", "name": "Bertrand", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:2114_1656_000053-0001", "name": "Claude", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 1},
    {"id": "xtts:2154_2576_000020-0003", "name": "Hélène", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:2216_1745_000007-0001", "name": "Damien", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 1},
    {"id": "xtts:2223_1745_000009-0002", "name": "Edmond", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 2},
    {"id": "xtts:2465_1943_000152-0002", "name": "Irène", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 1},
    {"id": "xtts:296_1028_000022-0001", "name": "Fernand", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 2},
    {"id": "xtts:3267_1902_000075-0001", "name": "Jeanne", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 1},
    {"id": "xtts:4193_3103_000004-0001", "name": "Gaston", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:4482_3103_000063-0001", "name": "Hubert", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:4724_3731_000031-0001", "name": "Isidore", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 2},
    {"id": "xtts:4937_3731_000004-0001", "name": "Julien", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:5207_3078_000031-0002", "name": "Victoire", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:5476_3103_000072-0001", "name": "Mathilde", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:577_394_000070-0001", "name": "Ninon", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:5790_4893_000052-0001", "name": "Léon", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:579_2548_000015-0001", "name": "Odette", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:5830_4703_000037-0001", "name": "Perrine", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:6318_7016_000027-0002", "name": "Marcel", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 1},
    {"id": "xtts:7142_2432_000124-0003", "name": "Norbert", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:7400_2928_000100-0001", "name": "Renée", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 1},
    {"id": "xtts:7591_6742_000149-0002", "name": "Suzanne", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 2},
    {"id": "xtts:7601_7727_000062-0001", "name": "Octave", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:7762_8734_000048-0002", "name": "Monique", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 2},
    {"id": "xtts:8128_7016_000047-0002", "name": "Quentin", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 1},
    {"id": "xtts:928_486_000075-0001", "name": "Raymond", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:9834_9697_000150-0003", "name": "Simon", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    # --- Voix CML-TTS versees le 14/09/2026 (lot d'ecoute de Laurent) ---
    # 25 voix de plus, tirees du MEME jeu public CML-TTS que les 35 ci-dessus
    # (CC BY 4.0 : lecture de livres classiques par des volontaires). Genre et
    # etoiles releves par Laurent a l'ecoute ; l'accent qu'il a entendu est
    # rappele dans le libelle, pour retrouver ces voix quand un personnage
    # etranger se presente. Les 7 voix qu'il a notees 0 ne sont pas versees.
    {"id": "xtts:cml1840", "name": "Achille", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 2},
    {"id": "xtts:cml3344", "name": "Honoré", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:cml6249", "name": "Célestin", "region": "\U0001F1EB\U0001F1F7 France (XTTS) - accent paysan", "gender": "M", "stars": 1},
    {"id": "xtts:cml9804", "name": "Alphonse", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:cml10065", "name": "Auguste", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:cml1649", "name": "Berthe", "region": "\U0001F1EB\U0001F1F7 France (XTTS) - accent allemand", "gender": "F", "stars": 0},
    {"id": "xtts:cml2033", "name": "Lucie", "region": "\U0001F1EB\U0001F1F7 France (XTTS) - accent anglais", "gender": "F", "stars": 3},
    {"id": "xtts:cml3060", "name": "Armand", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 2},
    {"id": "xtts:cml3182", "name": "Maurice", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:cml5525", "name": "Émile", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:cml6348", "name": "Hortense", "region": "\U0001F1EB\U0001F1F7 France (XTTS) - accent espagnol/italien", "gender": "F", "stars": 3},
    {"id": "xtts:cml6381", "name": "Gabrielle", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 2},
    {"id": "xtts:cml7614", "name": "Gustave", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 2},
    {"id": "xtts:cml12501", "name": "Charles", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:cml12512", "name": "Eugène", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 2},
    {"id": "xtts:cml12823", "name": "Agathe", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:cml1869", "name": "Cécile", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 0},
    {"id": "xtts:cml2316", "name": "Joséphine", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 1},
    {"id": "xtts:cml2771", "name": "Lucien", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 1},
    {"id": "xtts:cml3503", "name": "Félix", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:cml5526", "name": "Hippolyte", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 1},
    {"id": "xtts:cml6070", "name": "Estelle", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 2},
    {"id": "xtts:cml7239", "name": "Hector", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 1},
    {"id": "xtts:cml7377", "name": "Ernest", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 0},
    {"id": "xtts:cml7423", "name": "Basile", "region": "\U0001F1EB\U0001F1F7 France (XTTS) - accent canadien", "gender": "M", "stars": 2},
    # --- Voix issues d'extraits LIBRES DE DROITS (domaine public), versees le
    # 15/09/2026 (chantier de Laurent) ---
    # Extraits reunis et nettoyes par Laurent dans Audacity, convertis par
    # xtts_service/_preparer_extraits.py (WAV mono 24 kHz 16 bits, silences de
    # bord rognes) puis verses dans la banque du moteur. Liste de suivi
    # (identifiant, prenom, duree, fichier source) :
    # xtts_service/VOIX_LIBRES.txt.
    # Etoiles PROVISOIRES (2) : a ajuster apres ecoute dans le lecteur.
    # LOT 1 (7 voix, validees a l'oreille par Laurent le 15/09/2026) :
    {"id": "xtts:dp_femme001", "name": "Marthe", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_femme002", "name": "Solange", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_femme003", "name": "Yvette", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_femme004", "name": "Henriette", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_homme001", "name": "Marius", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:dp_homme002", "name": "Théodore", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:dp_homme004", "name": "Édouard", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    # LOT 2 (12 voix, mises a l'ecoute le 15/09/2026 ; Laurent a demande de les
    # verser sans attendre son verdict -- retrait possible a tout moment) :
    {"id": "xtts:dp_femme121235456", "name": "Rose", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 0},
    {"id": "xtts:dp_femme32321312445", "name": "Georgette", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_femme48897", "name": "Thérèse", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_femme65465464", "name": "Colette", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_femme6566554478", "name": "Juliette", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_femme65699878", "name": "Madeleine", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "F", "stars": 3},
    {"id": "xtts:dp_homme1122544987", "name": "Victor", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:dp_homme1122545656487", "name": "Robert", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:dp_homme313213265", "name": "Paul", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:dp_homme45788656512", "name": "Albert", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 0},
    {"id": "xtts:dp_homme65462104", "name": "Jules", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
    {"id": "xtts:dp_homme87976454321", "name": "Arthur", "region": "\U0001F1EB\U0001F1F7 France (XTTS)", "gender": "M", "stars": 3},
]

# --- DEBUT CATALOGUE NEUTTS (genere) ---
# Ce bloc est GENERE par test_voix/_generer_catalogue_neutts.py : ne pas
# l'editer a la main. Il est reconstruit a partir des extraits reellement
# presents dans neutts_service\references\ (source unique), en HERITANT des
# prenoms, genres et etoiles des voix deja cataloguees (memes identifiants) :
# une voix doit porter le meme prenom d'un moteur a l'autre, sinon plus
# personne ne s'y retrouve a l'oreille. La region, elle, distingue les
# moteurs (« France (NeuTTS) » face a « France (XTTS) »).
#
# ATTENTION aux ACCENTS : les mentions « accent paysan / anglais / ... » du
# catalogue XTTS decrivaient ce que Laurent entendait SUR XTTS. Elles ne sont
# PAS reprises ici : NeuTTS prononce avec SON modele francais, donc l'accent
# s'efface (constat d'ecoute du 16/09/2026) et il faudra le renseigner a
# nouveau, a l'oreille, dans la fenetre « Ecouter les voix ».
NEUTTS_VOICES = [
    # --- cml_tts : 60 voix ---
    {"id": "neutts:10087_11650_000028-0002", "name": "Adèle", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:10177_10625_000134-0003", "name": "Blanche", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:10179_11051_000005-0001", "name": "Céleste", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 1},
    {"id": "neutts:12080_11650_000047-0001", "name": "Diane", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:12205_11650_000004-0002", "name": "Éléonore", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:12977_10625_000037-0001", "name": "Fanny", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:1406_1028_000009-0003", "name": "Augustin", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:1591_1028_000108-0004", "name": "Geneviève", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:1770_1028_000036-0002", "name": "Bertrand", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:2114_1656_000053-0001", "name": "Claude", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 1},
    {"id": "neutts:2154_2576_000020-0003", "name": "Hélène", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:2216_1745_000007-0001", "name": "Damien", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 1},
    {"id": "neutts:2223_1745_000009-0002", "name": "Edmond", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:2465_1943_000152-0002", "name": "Irène", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 1},
    {"id": "neutts:296_1028_000022-0001", "name": "Fernand", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:3267_1902_000075-0001", "name": "Jeanne", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 1},
    {"id": "neutts:4193_3103_000004-0001", "name": "Gaston", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:4482_3103_000063-0001", "name": "Hubert", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:4724_3731_000031-0001", "name": "Isidore", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:4937_3731_000004-0001", "name": "Julien", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:5207_3078_000031-0002", "name": "Victoire", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:5476_3103_000072-0001", "name": "Mathilde", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:577_394_000070-0001", "name": "Ninon", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:5790_4893_000052-0001", "name": "Léon", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:579_2548_000015-0001", "name": "Odette", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:5830_4703_000037-0001", "name": "Perrine", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:6318_7016_000027-0002", "name": "Marcel", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 1},
    {"id": "neutts:7142_2432_000124-0003", "name": "Norbert", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:7400_2928_000100-0001", "name": "Renée", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 1},
    {"id": "neutts:7591_6742_000149-0002", "name": "Suzanne", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:7601_7727_000062-0001", "name": "Octave", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:7762_8734_000048-0002", "name": "Monique", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:8128_7016_000047-0002", "name": "Quentin", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 1},
    {"id": "neutts:928_486_000075-0001", "name": "Raymond", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:9834_9697_000150-0003", "name": "Simon", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:cml10065", "name": "Auguste", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:cml12501", "name": "Charles", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:cml12512", "name": "Eugène", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:cml12823", "name": "Agathe", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:cml1649", "name": "Berthe", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 0},
    {"id": "neutts:cml1840", "name": "Achille", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:cml1869", "name": "Cécile", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 0},
    {"id": "neutts:cml2033", "name": "Lucie", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:cml2316", "name": "Joséphine", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 1},
    {"id": "neutts:cml2771", "name": "Lucien", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 1},
    {"id": "neutts:cml3060", "name": "Armand", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:cml3182", "name": "Maurice", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:cml3344", "name": "Honoré", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:cml3503", "name": "Félix", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:cml5525", "name": "Émile", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:cml5526", "name": "Hippolyte", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 1},
    {"id": "neutts:cml6070", "name": "Estelle", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:cml6249", "name": "Célestin", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 1},
    {"id": "neutts:cml6348", "name": "Hortense", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:cml6381", "name": "Gabrielle", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:cml7239", "name": "Hector", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 1},
    {"id": "neutts:cml7377", "name": "Ernest", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 0},
    {"id": "neutts:cml7423", "name": "Basile", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:cml7614", "name": "Gustave", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:cml9804", "name": "Alphonse", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    # --- kokoro : 30 voix ---
    {"id": "neutts:ff_amelie", "name": "Amélie", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_aurore", "name": "Aurore", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:ff_chloe", "name": "Chloé", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_clara", "name": "Clara", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_delphine", "name": "Delphine", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_elodie", "name": "Élodie", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_enfant", "name": "Enfant", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:ff_julie", "name": "Julie", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_louise", "name": "Louise", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_maelle", "name": "Maëlle", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_mamie", "name": "Mamie", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:ff_manon", "name": "Manon", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_margaux", "name": "Margaux", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_noemie", "name": "Noémie", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_pauline", "name": "Pauline", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 0},
    {"id": "neutts:ff_romane", "name": "Romane", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_sarah", "name": "Sarah", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_solene", "name": "Solène", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:ff_zoe", "name": "Zoé", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 2},
    {"id": "neutts:fm_antoine", "name": "Antoine", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:fm_baptiste", "name": "Baptiste", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:fm_camille", "name": "Camille", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 0},
    {"id": "neutts:fm_etienne", "name": "Étienne", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    {"id": "neutts:fm_hugo", "name": "Hugo", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 0},
    {"id": "neutts:fm_jeune", "name": "Jeune", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:fm_lucas", "name": "Lucas", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:fm_mystere", "name": "Mystère", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:fm_narrateur", "name": "Narrateur", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:fm_papi", "name": "Papi", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:fm_vincent", "name": "Vincent", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 2},
    # --- voix_libres_dp : 19 voix ---
    {"id": "neutts:Femme001", "name": "Marthe", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Femme002", "name": "Solange", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Femme003", "name": "Yvette", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Femme004", "name": "Henriette", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Femme121235456", "name": "Rose", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 0},
    {"id": "neutts:Femme32321312445", "name": "Georgette", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Femme48897", "name": "Thérèse", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Femme65465464", "name": "Colette", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Femme6566554478", "name": "Juliette", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Femme65699878", "name": "Madeleine", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "F", "stars": 3},
    {"id": "neutts:Homme001", "name": "Marius", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:Homme002", "name": "Théodore", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:Homme004", "name": "Édouard", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:Homme1122544987", "name": "Victor", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:Homme1122545656487", "name": "Robert", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:Homme313213265", "name": "Paul", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:Homme45788656512", "name": "Albert", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 0},
    {"id": "neutts:Homme65462104", "name": "Jules", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
    {"id": "neutts:Homme87976454321", "name": "Arthur", "region": "\U0001F1EB\U0001F1F7 France (NeuTTS)", "gender": "M", "stars": 3},
]
# --- FIN CATALOGUE NEUTTS ---


class XttsIndisponible(RuntimeError):
    """Le service XTTS v2 ne repond pas (moteur eteint ou en chargement)."""


def _xtts_voix_id(voice: str) -> str:
    """Retire le prefixe 'xtts:' pour obtenir l'identifiant de la voix."""
    return voice.split(":", 1)[1] if ":" in voice else voice


async def _demander_au_moteur_xtts(texte: str, identifiant_voix: str) -> bytes:
    """Envoie une phrase au service XTTS et renvoie le WAV brut."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=XTTS_DELAI_S) as client:
            reponse = await client.post(
                XTTS_URL + "/tts",
                json={"texte": texte, "voix": identifiant_voix},
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
            httpx.RemoteProtocolError, httpx.WriteError) as erreur:
        raise XttsIndisponible(
            "Le moteur de voix XTTS v2 ne repond pas ("
            + type(erreur).__name__ + "). Double-clique sur "
            "DEMARRER_XTTS.bat, puis relance la lecture."
        )

    if reponse.status_code != 200:
        detail = ""
        try:
            detail = (reponse.json() or {}).get("erreur", "")
        except Exception:
            detail = ""
        raise XttsIndisponible(
            "Le moteur de voix XTTS v2 a refuse la phrase (code %d%s)."
            % (reponse.status_code, (" : " + detail) if detail else "")
        )

    return reponse.content


async def synthesize_xtts(text: str, voice: str, rate: str = "+0%",
                          pitch: str = "+0Hz") -> bytes:
    """
    Synthese XTTS v2 pour une phrase. Le moteur tourne dans son propre
    service (Python 3.12 + PyTorch), appele ici en HTTP local.

    Vitesse : aucun reglage natif -> post-traitement ffmpeg (atempo).
    Hauteur : aucun reglage natif -> post-traitement _apply_pitch_shift
    (Rubber Band), comme pour Kokoro, Piper et Kyutai.
    L'audio final est mis en cache disque, exactement comme les autres
    moteurs : un passage deja lu ne redemande rien au moteur.
    """
    text = _clean_text(text)
    if not text:
        return b""

    cached = _tts_cache.get_audio(text, voice, rate, pitch, "wav")
    if cached is not None:
        return cached

    wav_bytes = await _demander_au_moteur_xtts(text, _xtts_voix_id(voice))
    if not wav_bytes:
        return b""

    # Vitesse puis hauteur (aucun des deux n'existe dans le moteur).
    wav_bytes = _audio_rate.appliquer_vitesse(wav_bytes, _percent_to_speed(rate))
    wav_bytes = _apply_pitch_shift(wav_bytes, _hz_to_semitones(pitch))

    _tts_cache.put_audio(text, voice, rate, pitch, "wav", wav_bytes)
    return wav_bytes


# ==============================================================
# NEUTTS -- moteur de clonage (service local, port 8084)
# ==============================================================
# Meme principe que XTTS : le moteur vit A COTE du lecteur (Python 3.12 +
# PyTorch) et repond en HTTP local, dans son dossier `neutts_service`.
#
# TROIS DIFFERENCES, toutes mesurees le 16/09/2026 (voir BACKLOG) :
#   - il est STABLE : a graine fixe, deux syntheses du meme texte donnent le
#     meme fichier A L'OCTET PRES (empreintes SHA-256 identiques, verifie sur
#     processeur et sur la carte graphique) ;
#   - il ne BABILLE pas sur les phrases courtes (« Manger ? » 1,08 s, la ou
#     XTTS sortait 8,49 s) et il tient un long passage sans deriver ;
#   - il est plus LENT : environ x0,8 le temps reel sur la carte graphique
#     (XTTS est a x3). Le cache audio absorbe les relectures ; la PREMIERE
#     ecoute d'un chapitre peut en revanche faire de petites pauses.
NEUTTS_URL = "http://127.0.0.1:8084"
# Delai large : le moteur calcule plus lentement que le temps reel, et une
# phrase longue peut demander une trentaine de secondes (une minute sur
# processeur).
NEUTTS_DELAI_S = 300.0


class NeuttsIndisponible(RuntimeError):
    """Le service NeuTTS ne repond pas (moteur eteint ou en chargement)."""


def _neutts_voix_id(voice: str) -> str:
    """Retire le prefixe 'neutts:' pour obtenir l'identifiant de la voix."""
    return voice.split(":", 1)[1] if ":" in voice else voice


async def _demander_au_moteur_neutts(texte: str, identifiant_voix: str) -> bytes:
    """Envoie une phrase au service NeuTTS et renvoie le WAV brut."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=NEUTTS_DELAI_S) as client:
            reponse = await client.post(
                NEUTTS_URL + "/tts",
                json={"texte": texte, "voix": identifiant_voix},
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
            httpx.RemoteProtocolError, httpx.WriteError) as erreur:
        raise NeuttsIndisponible(
            "Le moteur de voix NeuTTS ne repond pas ("
            + type(erreur).__name__ + "). Double-clique sur "
            "DEMARRER_NEUTTS.bat, puis relance la lecture."
        )

    if reponse.status_code != 200:
        detail = ""
        try:
            detail = (reponse.json() or {}).get("erreur", "")
        except Exception:
            detail = ""
        raise NeuttsIndisponible(
            "Le moteur de voix NeuTTS a refuse la phrase (code %d%s)."
            % (reponse.status_code, (" : " + detail) if detail else "")
        )

    return reponse.content


async def synthesize_neutts(text: str, voice: str, rate: str = "+0%",
                            pitch: str = "+0Hz") -> bytes:
    """Synthese NeuTTS pour une phrase. Le moteur tourne dans son propre
    service (Python 3.12 + PyTorch), appele ici en HTTP local.

    Vitesse : aucun reglage natif -> post-traitement ffmpeg (atempo), comme
    pour XTTS. Hauteur : post-traitement _apply_pitch_shift (Rubber Band),
    comme pour Kokoro, Piper, Kyutai et XTTS.
    L'audio final est mis en cache disque, exactement comme les autres
    moteurs : un passage deja lu ne redemande rien au moteur -- et c'est ce
    qui rend la lenteur du moteur supportable a l'usage.
    """
    text = _clean_text(text)
    if not text:
        return b""

    cached = _tts_cache.get_audio(text, voice, rate, pitch, "wav")
    if cached is not None:
        return cached

    wav_bytes = await _demander_au_moteur_neutts(text, _neutts_voix_id(voice))
    if not wav_bytes:
        return b""

    # Vitesse puis hauteur (aucun des deux n'existe dans le moteur).
    wav_bytes = _audio_rate.appliquer_vitesse(wav_bytes, _percent_to_speed(rate))
    wav_bytes = _apply_pitch_shift(wav_bytes, _hz_to_semitones(pitch))

    _tts_cache.put_audio(text, voice, rate, pitch, "wav", wav_bytes)
    return wav_bytes


