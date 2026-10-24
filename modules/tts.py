# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import re
import os
import asyncio
import time
import edge_tts
from modules import tts_cache as _tts_cache
from modules import audio_trim as _audio_trim
from modules import audio_rate as _audio_rate
from modules import audio_gain as _audio_gain
from modules import audio_queue as _audio_queue
from modules import incises as _incises
from modules import majuscules as _majuscules
from modules import nombres as _nombres
from modules import prononciation as _prononciation

# ==============================================================
# NIVEAU DE PAROLE VISE (mesure du 21/09/2026)
# ==============================================================
# `modules/audio_gain.py` ramene la parole DANS UNE FOURCHETTE de +/- 3 dB
# autour de la cible d'Edge TTS (8,5 %), commune a tous les moteurs : c'est le
# niveau que Laurent n'a jamais trouve faible.
# Mesure du 21/09/2026 (`test_voix/_mesurer_pocket_defauts.py`, dix phrases d'un
# long paragraphe de 22/11/63, lues une par une comme en lecture) :
#   - Kyutai : niveau median 6,6 % (de 3,8 a 10,8 %) -- eparpille a la sortie du
#     moteur (9,1 dB d'ecart), RAMENE a ~2 dB par le module ;
#   - Pocket : median 9,6 % (de 7,5 a 12,8 %) -- 4,6 dB d'ecart, ramene a ~3,6 dB.
# Autrement dit : le module fait deja l'essentiel (il remonte les phrases
# faibles) ; la fourchette ajoutee le 21/09/2026 corrige le RESTE, ce qui est
# au-dessus de +3 dB de la cible (les phrases a 12,8 % de Pocket).

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


# --- Kokoro : on donne les PHONEMES, pas le texte (21/09/2026) --------------
# Cause etablie le 20/09/2026 (mesure + verdict d'oreille, atelier NIMM Voix) :
# pour `lang=fr-fr`, Kokoro n'a pas de phonemiseur francais -- il appelle
# espeak-ng, dont les dictionnaires de toutes les langues cohabitent. Quand un
# mot est reconnu dans le dictionnaire ANGLAIS (« Andrea », « Marthe »...),
# espeak-ng change de langue et MARQUE la frontiere dans sa sortie :
# `(en)ˈandɹiə(fr)`. Le tokenizer de kokoro-onnx GARDE ces caracteres, qui sont
# dans son vocabulaire : Laurent entendait « énAndréa fe ».
# En phonemisant NOUS-MEMES, en retirant ces marques, puis en donnant les
# phonemes au moteur (`is_phonemes=True`), plus aucune syllabe inventee -- y
# compris sur les mots que `modules/prononciation.py` ne connait pas.
#
# Le motif est VOLONTAIREMENT etroit (`(en)`, `(fr)`, `(en-us)`...) : un motif
# large comme `\([^)]*\)` mangerait tout ce qu'il y a entre deux parentheses du
# texte. Les codes de langue d'espeak-ng font deux ou trois lettres.
MARQUE_LANGUE = re.compile(r"\([a-z]{2}(?:-[a-z]{2})?\)")


def _phonemes_kokoro(text: str) -> str:
    """Phonemes francais d'un texte, SANS les marques de langue d'espeak-ng."""
    phonemes = _kokoro.tokenizer.phonemize(text, "fr-fr")
    return MARQUE_LANGUE.sub("", phonemes)


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
    {"id": "kokoro:fm_baptiste",  "name": "Baptiste",  "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 0},
    {"id": "kokoro:fm_camille",   "name": "Camille",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 0},
    {"id": "kokoro:fm_etienne",   "name": "Étienne",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 2},
    {"id": "kokoro:fm_hugo",      "name": "Hugo",      "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 0},
    {"id": "kokoro:fm_lucas",     "name": "Lucas",     "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 3},
    {"id": "kokoro:fm_vincent",   "name": "Vincent",   "region": "\U0001F1EB\U0001F1F7 France (NIMM Voix)", "gender": "M", "stars": 2},
    # --- Accent allemand (fabriquees dans NIMM Voix, importees le 20/09/2026) --
    # 10 voix FRANCAISES a accent allemand : le texte est lu en francais force
    # (lang="fr-fr"), l'accent vient du timbre. Ce sont des melanges de voix
    # Kokoro allemandes (df_eva, dm_bernd, df_victoria, dm_martin) et de
    # ff_siwis, trois d'entre elles etant tirees vers les aigus ou les graves.
    # Recettes et verdicts d'oreille de Laurent : NIMM Voix,
    # sorties/validation_accent_allemand_20260920/FICHE_VOIX.txt
    # Timbres importes dans voices-v1.0.bin le 20/09/2026 (84 -> 94 voix),
    # fichier de voix inchange par ailleurs (verifie voix par voix).
    # ET 0 ETOILE A L'IMPORT (decision du 20/09/2026) : une voix notee 0 est
    # ECARTEE du casting automatique, mais reste choisissable a la main
    # (voice_casting.py, « regle des paliers »). Ces voix ne se glisseront donc
    # pas toutes seules dans un livre francais : les notes d'ecoute de Laurent
    # (fenetre « Ecouter les voix »), reportees par
    # _appliquer_annotations_voix.py, les feront entrer dans le pool comme les
    # autres. Les PRENOMS ont ete donnes le 20/09/2026 (demande de Laurent :
    # « juste des prenoms allemands »), apres son taggage dans « Ecouter les
    # voix » : ils ne portent plus les etiquettes de l'atelier (fort/trio/
    # grave/aigue). Correspondance avec les timbres d'origine, pour s'y
    # retrouver plus tard :
    #   Eva      = df_eva 25 % (accent leger)   Lena     = df_eva 50 % (aigus)
    #   Viktoria = df_victoria 50 %             Greta    = df_victoria 75 %
    #   Bernd    = dm_bernd 50 %                Klaus    = dm_bernd 85 %
    #   Wolfgang = dm_bernd 50 % (graves)       Martin   = dm_martin 100 %
    #   Otto     = dm_martin 75 %               Heinrich = dm_martin 50 % (graves)
    {"id": "kokoro:fa_eva",           "name": "Eva",      "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:fa_victoria",      "name": "Viktoria",    "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "F", "stars": 0},
    {"id": "kokoro:fa_bernd",         "name": "Bernd",        "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "M", "stars": 2},
    {"id": "kokoro:fa_martin",        "name": "Martin",       "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "M", "stars": 2},
    {"id": "kokoro:fa_bernd_fort",    "name": "Klaus",        "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "M", "stars": 0},
    {"id": "kokoro:fa_victoria_trio", "name": "Greta",        "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "F", "stars": 2},
    {"id": "kokoro:fa_martin_trio",   "name": "Otto",         "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "M", "stars": 0},
    {"id": "kokoro:fa_eva_aigue",     "name": "Lena",         "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "F", "stars": 0},
    {"id": "kokoro:fa_bernd_grave",   "name": "Wolfgang",     "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "M", "stars": 2},
    {"id": "kokoro:fa_martin_grave",  "name": "Heinrich",     "region": "\U0001F1E9\U0001F1EA Allemagne (NIMM Voix)", "gender": "M", "stars": 0},
    # --- Etats-Unis (americain) ---
    {"id": "kokoro:af_alloy",   "name": "Alloy",      "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_aoede",   "name": "Aoede",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_bella",   "name": "Bella",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 3},
    {"id": "kokoro:af_heart",   "name": "Heart",       "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_jessica", "name": "Jessica",     "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_kore",    "name": "Kore",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_nicole",  "name": "Nicole",      "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 2},
    {"id": "kokoro:af_nova",    "name": "Nova",        "region": "\U0001F1FA\U0001F1F8 Etats-Unis", "gender": "F", "stars": 1},
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
    {"id": "kokoro:bm_george",   "name": "George",    "region": "\U0001F1EC\U0001F1E7 Royaume-Uni", "gender": "M", "stars": 2},
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
    {"id": "kokoro:zf_xiaobei",  "name": "Xiaobei",  "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "F", "stars": 2},
    {"id": "kokoro:zf_xiaoni",   "name": "Xiaoni",   "region": "\U0001F1E8\U0001F1F3 Chine", "gender": "F", "stars": 2},
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
    # Les premieres lettres sont rendues INSENSIBLES A LA CASSE ([Mm] et non
    # « M ») : un texte traduit de l'anglais ecrit « MR. CURRIE » (constat de
    # Laurent, 21/09/2026, 22/11/63 chapitre 10) -- sans cela, le moteur recevait
    # « MR. » tel quel et INVENTAIT un son (« [féè] »). Les garde-fous du haut
    # restent : frontiere de mot, et lookahead (l'abreviation doit etre un mot
    # complet), donc « mer », « Proust » ou « amr » ne sont jamais touches.
    (re.compile(r"\b[Mm][Mm]\.(?=\s|$|»|\")"), "Messieurs"),
    (re.compile(r"(?<![.\w])M\b\.?(?=\s+[A-ZÀ-ÖØ-Ý])"), "Monsieur"),
    (re.compile(r"(?<![.\w])M\.(?=\s|$|»|\")"), "Monsieur"),
    (re.compile(r"\b[Mm][Rr]\.?(?=\s|$|»|\")"), "Monsieur"),
    (re.compile(r"\b[Mm][Gg][Rr]\b\.?(?=\s|$|»|\")"), "Monseigneur"),
    (re.compile(r"\b[Mm][Mm][Ee][Ss]\b\.?(?=\s|$|»|\")"), "Mesdames"),
    (re.compile(r"\b[Mm][Mm][Ee]\b\.?(?=\s|$|»|\")"), "Madame"),
    (re.compile(r"\b[Mm][Ll][Ll][Ee][Ss]\b\.?(?=\s|$|»|\")"), "Mesdemoiselles"),
    (re.compile(r"\b[Mm][Ll][Ll][Ee]\b\.?(?=\s|$|»|\")"), "Mademoiselle"),
    (re.compile(r"\b[Dd][Rr]\b\.?(?=\s|$|»|\")"), "Docteur"),
    (re.compile(r"\b[Pp][Rr]\b\.?(?=\s|$|»|\")"), "Professeur"),
    (re.compile(r"\b[Ss][Tt][Ee]\b\.?(?=\s|$|»|\")"), "Sainte"),
    (re.compile(r"\b[Ss][Tt]\b\.?(?=\s|$|»|\")"), "Saint"),
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


# ==============================================================
# PONCTUATION QUI DERANGE LA VOIX (reglages d'ecoute)
# ==============================================================

# Point d'exclamation : LAISSE TEL QUEL dans le texte envoye au moteur
# (decision de Laurent, 04/10/2026).
#
# HISTORIQUE. Du 18/09/2026 au 03/10/2026, le « ! » etait RETIRE du texte envoye
# au moteur et remplace par la VIRGULE (phrase de 25 caracteres ou moins) ou le
# POINT (phrase plus longue) : les moteurs d'ALORS (Kokoro, Edge) le jouaient
# comme une MONTERE de hauteur (« Il partit ! » -> « Il partiiiiit », « Oh ! » ->
# « OOOOOOoooooh »). Ce choix venait d'une ecoute du 18/09/2026 (banc
# `test_voix/ecoute_ponctuation_20260918_1937`, 6 phrases reelles du tome 5),
# faite avec CES moteurs-la.
#
# Le moteur en service a change (Qwen3-TTS en C++, sur la carte, en Q8_0) et
# Laurent a demande le 04/10/2026 de REMETTRE le « ! » : « remettre les points
# d'exclamation comme des points d'exclamation au lieu des virgules ou des
# points ». Les trois constantes qui portaient l'ancien reglage
# (PONCTUATION_EXCLAMATION, PONCTUATION_EXCLAMATION_COURTE, SEUIL_INTERJECTION)
# disparaissent avec lui. Pour revenir en arriere A L'OREILLE, le banc
# `test_voix/_banc_qwen_exclamations.py` rejoue le « ! » face a la virgule et au
# point. ON NE TOUCHE JAMAIS au texte affiche : la phrase garde son « ! ».

# Mots sur lesquels un point final NE DOIT JAMAIS etre ajoute.
# Retour d'ecoute de Laurent du 18/09/2026 : « les silences apres les M. (lu
# monsieur) ou Mme (lu madame) ». Mesure du meme jour (test_voix/
# _diag_retours_ecoute.py) : la page decoupe les phrases APRES le point d'une
# abreviation, donc le moteur recoit un morceau qui se termine par
# « ... le temps de complimenter Monsieur » (207 fois dans un seul tome de
# Monte-Cristo). Lui ajouter un point final en fait une VRAIE fin de phrase,
# avec la respiration qui va avec -- d'ou le silence entendu. Sans ce point, la
# phrase s'enchaine directement a la suivante.
MOTS_SANS_POINT_FINAL = re.compile(
    r"\b(?:Monsieur|Messieurs|Madame|Mesdames|Mademoiselle|Mesdemoiselles"
    r"|Monseigneur|Docteur|Professeur|Saint|Sainte|numéro)$")


def _clean_text(text: str, vocabulaire=None, ponctuation_libre=False) -> str:
    """Prepare le texte pour la synthese vocale.

    `vocabulaire` (facultatif) : les mots que le LIVRE ecrit en casse normale
    (voir `modules/majuscules.py`). Quand il est fourni, les mots TOUT EN
    MAJUSCULES qui y figurent sont remis en casse normale : sinon un moteur
    neuronal traite « LUI » ou « DE » comme un sigle, et la lecture part en
    biais (demande de Laurent, 19/09/2026). Les VRAIS sigles (« JFK », « FBI »)
    ne sont pas au vocabulaire et restent tels quels, ce qui est voulu.
    Sans vocabulaire (appels de test, textes hors livre), rien ne change.

    `ponctuation_libre` (facultatif, ajoute le 23/10/2026) : quand il est VRAI,
    on ne touche PAS a la ponctuation du livre -- `;`, ` : ` et les parentheses
    restent tels quels, et une virgule finale n'est PAS changee en point. Le
    reste du nettoyage (majuscules, incises, abreviations, nombres, espaces)
    s'applique comme d'habitude. FAUX par defaut : le comportement de tous les
    moteurs ne change pas d'un caractere.

    POURQUOI CE PARAMETRE. Les conversions de ponctuation datent des moteurs
    d'AVANT Qwen (Edge, Kokoro : 17 et 18/09/2026), qui prononçaient la
    ponctuation ou n'en faisaient aucune pause. Le moteur en service depuis le
    26/09/2026 (Qwen3-TTS sur la carte) lit la ponctuation naturellement --
    constat de Laurent, 23/10/2026, sur un passage ou un « : » sortait en
    virgule et une virgule en fin de phrase. Banc d'ecoute du meme jour
    (`test_voix/_banc_qwen_ponctuation.py`) : **verdict, la ponctuation du livre
    est la reference POUR QWEN**, et `synthesize_qwen` active donc ce drapeau.
    Les autres moteurs restent a FAUX tant qu'on ne les a pas reecoutes.
    """
    # Les majuscules D'ABORD : les autres regles lisent mieux un texte en casse
    # normale, et la casse n'a aucun effet sur la prononciation.
    text = _majuscules.reduire_majuscules(text, vocabulaire)

    # Sauts de ligne -> simple espace (pas de virgule, qui ajouterait une
    # pause artificielle au milieu d'un texte deja decoupe en phrases).
    text = text.replace("\n", " ")

    # Supprime les crochets, les caracteres de controle et les emojis
    text = re.sub(r'\[[^\]]{0,30}\]', '', text)

    # --- INCISES DE PAROLE, TOUT DEBUT --------------------------------------
    # On les retire AVANT de toucher a la ponctuation : la suite du nettoyage
    # transforme « ; » et « : » en VIRGULES, ce qui fabriquerait de fausses
    # incises fermees (« il partit ; repondit le comte , ... ») et supprimerait
    # le sujet de la phrase. Regle prudente : `modules/incises.py`.
    text = _incises.retirer_incises(text)

    # --- LA PONCTUATION DU LIVRE, OU LA PONCTUATION ARRANGEE -----------------
    # Tout ce bloc vient des moteurs d'AVANT Qwen (17 et 18/09/2026). Il reste
    # le comportement par defaut ; `ponctuation_libre=True` le saute pour
    # entendre ce que le moteur fait de la ponctuation de l'auteur.
    if not ponctuation_libre:
        # Point-virgule -> virgule (17/09/2026, constat de Laurent) : les
        # moteurs neuronaux essaient de PRONONCER la ponctuation forte qu'ils ne
        # savent pas ignorer, et le « ; » sortait parfois en « euh ». La virgule
        # garde la respiration sans le son parasite.
        text = text.replace(';', ',')

        # Deux-points -> virgule (17/09/2026 au soir, constat de Laurent : « la
        # ponctuation des ":" n'a pas de pause du tout »). On ne touche qu'au
        # deux-points PRECEDE D'UNE ESPACE -- c'est la typographie francaise, et
        # cela evite de casser « 14:30 » ou une adresse.
        text = re.sub(r'\s+:\s*', ', ', text)

        # Parentheses -> virgules (meme jour, meme constat) : le moteur les
        # ignore, donc l'incise n'etait entouree d'AUCUNE pause. Deux virgules
        # redonnent la respiration attendue de part et d'autre.
        text = text.replace('(', ', ').replace(')', ',')

    # Le « ?! » est traite TOUT A LA FIN de ce nettoyage : il ne doit pas etre
    # transforme par la regle de fin de segment (sinon le « ? » se retrouverait
    # suivi d'un point). Le « ! » seul, lui, n'est PLUS touche (04/10/2026).

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

    # --- LES NOMBRES, EN LETTRES (03/10/2026, demande de Laurent) -----------
    # Un moteur de voix lit des LETTRES, pas des CHIFFRES : sur « a 180 degres »
    # il inventait (« pi huit-cent »), alors que « cent quatre-vingts » passe
    # tout seul. Meme principe que les prenoms (`modules/prononciation.py`) :
    # le texte AFFICHE ne bouge jamais, seul celui envoye au moteur change.
    # Vaut pour TOUS les moteurs, et la cle de cache portant le texte, les
    # phrases qui portent un nombre se regenerent toutes seules (pas besoin de
    # monter VERSION_CACHE).
    text = _nombres.pour_lecture(text)

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
    # Le point final n'est PAS ajoute apres une abreviation developpee
    # (Monsieur, Madame, Docteur...) : voir MOTS_SANS_POINT_FINAL ci-dessus.
    # C'est ce qui supprime le silence entendu apres « M. » / « Mme » le
    # 18/09/2026.
    #
    # PONCTUATION LIBRE (23/10/2026) : une virgule finale RESTE une virgule.
    # C'est ici que la virgule de Laurent devenait un point -- « ... sans le
    # moindre avion, et l'avion tout aussi introuvable du Pentagone. » : le
    # moteur recevait une vraie fin de phrase la ou l'auteur avait une virgule,
    # d'ou la voix qui « tombe ». En libre, la ponctuation du livre part telle
    # quelle ; en revanche, un texte sans AUCUNE ponctuation finale recoit
    # toujours son point (frontiere dont le moteur a besoin pour s'arreter).
    if text and text[-1] in ',;:':
        if not ponctuation_libre:
            text = text[:-1].rstrip() + '.'
    elif (text and text[-1] not in '.!?:…»"'
          and not MOTS_SANS_POINT_FINAL.search(text)):
        text += '.'

    # --- LE « ?! » EN DERNIER (le « ! » seul est LAISSE TEL QUEL) -----------
    # Place ici EXPRES : apres la regle de fin de segment, sinon le « ? » se
    # retrouverait suivi d'un point.
    # Le « ?! » est a part : c'est une INTERROGATION suivie d'une exclamation,
    # et on garde le « ? » seul (cas rare, pas rejoue a l'oreille). Laurent a
    # demande le 04/10/2026 de REMETTRE le « ! » seul (voir le bloc en haut du
    # fichier) : « remettre les points d'exclamation comme des points
    # d'exclamation au lieu des virgules ou des points ».
    # En PONCTUATION LIBRE, le « ?! » reste quand meme ramene a « ? »
    # (23/10/2026) : c'est la prudence du 04/10/2026, prise AVEC Qwen en
    # service, et ce cas rare n'a jamais ete rejoue a l'oreille. Tout le reste
    # de la ponctuation, lui, part tel quel.
    text = re.sub(r'\?\s*!+', '?', text)

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
                            pitch: str = DEFAULT_PITCH,
                            vocabulaire=None):
    """
    Generateur async : stream l'audio MP3 chunk par chunk.
    Utilise directement par la route /api/tts de main.py.
    Gere automatiquement les textes longs en les decoupant.
    Chaque chunk passe par le cache disque : un passage deja genere est
    renvoye depuis le disque sans re-solliciter Edge TTS.
    """
    text = _clean_text(text, vocabulaire)
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
                           rate: str = DEFAULT_RATE, vocabulaire=None) -> bytes:
    """
    Retourne l'audio complet en bytes.
    Utile pour les textes courts (titres de chapitres, etc.)
    """
    audio = b""
    async for chunk in synthesize_stream(text, voice, rate,
                                         vocabulaire=vocabulaire):
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


async def synthesize_kokoro(text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz",
                            vocabulaire=None) -> bytes:
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
    text = _clean_text(text, vocabulaire)
    if not text:
        return b""

    # Prononciation francaise imposee (21/09/2026) : les mots que le
    # phonemiseur prendrait pour de l'anglais sont reecrits pour la LECTURE
    # (`modules/prononciation.py`), et l'apostrophe courbe redevient droite
    # (espeak-ng ne reconnait pas « d’aujourd’hui »). Le texte AFFICHE n'est
    # jamais touche : on ne modifie que ce qui part vers le moteur.
    # Comme la cle du cache porte sur le texte transforme, changer la table ne
    # peut PAS resservir un ancien audio.
    text = _prononciation.pour_lecture(text)

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
            # On donne les PHONEMES (voir `_phonemes_kokoro`) : le moteur ne
            # phonemise plus lui-meme, donc les marques de langue d'espeak-ng
            # ne peuvent plus finir dans l'audio.
            phonemes = _phonemes_kokoro(text)
            samples, sample_rate = _kokoro.create(
                phonemes, voice=voice_id, speed=speed, is_phonemes=True
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
    {"id": "piper:siwis:0", "name": "Siwis",   "region": "\U0001F1EB\U0001F1F7 France (Piper)", "gender": "F", "stars": 2},
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


async def synthesize_piper(text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz",
                           vocabulaire=None) -> bytes:
    """
    Synthese Piper pour une phrase. Chargement du modele a la volee s'il
    n'est pas deja en memoire (sans effet si deja charge). Vitesse geree
    nativement par Piper (length_scale). Pitch applique en post-traitement
    (librosa) si different de +0Hz. Execute dans un thread separe (Piper
    est synchrone/CPU) pour ne pas bloquer le serveur pendant la generation.
    """
    text = _clean_text(text, vocabulaire)
    if not text:
        return b""

    # Prononciation francaise imposee (21/09/2026) : Piper RETIRE les marques de
    # langue d'espeak-ng (donc pas de syllabes inventees), mais il garde la
    # PRONONCIATION anglaise (« Marthe » -> *marth*, mesure du 20/09/2026).
    # Meme table que Kokoro, et meme regle : le texte affiche ne bouge pas.
    text = _prononciation.pour_lecture(text)

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
    {"id": "kyutai:10177_10625_000134-0003", "name": "Blanche", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},    # etait Kyutai 02
    {"id": "kyutai:10179_11051_000005-0001", "name": "Céleste", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 1},    # etait Kyutai 03
    {"id": "kyutai:12080_11650_000047-0001", "name": "Diane", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},      # etait Kyutai 04
    {"id": "kyutai:12205_11650_000004-0002", "name": "Éléonore", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},   # etait Kyutai 05
    {"id": "kyutai:12977_10625_000037-0001", "name": "Fanny", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},      # etait Kyutai 06
    {"id": "kyutai:1406_1028_000009-0003", "name": "Augustin", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},    # etait Kyutai 07
    {"id": "kyutai:1591_1028_000108-0004", "name": "Geneviève", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},   # etait Kyutai 08
    {"id": "kyutai:1770_1028_000036-0002", "name": "Bertrand", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},    # etait Kyutai 09
    {"id": "kyutai:2114_1656_000053-0001", "name": "Claude", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 2},      # etait Kyutai 10, accent canadien
    {"id": "kyutai:2154_2576_000020-0003", "name": "Hélène", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},      # etait Kyutai 11
    {"id": "kyutai:2216_1745_000007-0001", "name": "Damien", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 12, accent canadien
    {"id": "kyutai:2223_1745_000009-0002", "name": "Edmond", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 13
    {"id": "kyutai:2465_1943_000152-0002", "name": "Irène", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},       # etait Kyutai 14
    {"id": "kyutai:296_1028_000022-0001", "name": "Fernand", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 15
    {"id": "kyutai:3267_1902_000075-0001", "name": "Jeanne", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},      # etait Kyutai 16
    {"id": "kyutai:4193_3103_000004-0001", "name": "Gaston", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 17
    {"id": "kyutai:4482_3103_000063-0001", "name": "Hubert", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 18
    {"id": "kyutai:4724_3731_000031-0001", "name": "Isidore", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},     # etait Kyutai 19
    {"id": "kyutai:4937_3731_000004-0001", "name": "Julien", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 20
    {"id": "kyutai:5207_3078_000031-0002", "name": "Victoire", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 2},    # etait Kyutai 21
    {"id": "kyutai:5476_3103_000072-0001", "name": "Mathilde", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},    # etait Kyutai 22
    {"id": "kyutai:577_394_000070-0001", "name": "Ninon", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},         # etait Kyutai 23
    {"id": "kyutai:5790_4893_000052-0001", "name": "Léon", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},        # etait Kyutai 24
    {"id": "kyutai:579_2548_000015-0001", "name": "Odette", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 2},       # etait Kyutai 25
    {"id": "kyutai:5830_4703_000037-0001", "name": "Perrine", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},     # etait Kyutai 26
    {"id": "kyutai:6318_7016_000027-0002", "name": "Marcel", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 27
    {"id": "kyutai:7142_2432_000124-0003", "name": "Norbert", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},     # etait Kyutai 28
    {"id": "kyutai:7400_2928_000100-0001", "name": "Renée", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},       # etait Kyutai 29
    {"id": "kyutai:7591_6742_000149-0002", "name": "Suzanne", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},     # etait Kyutai 30
    {"id": "kyutai:7601_7727_000062-0001", "name": "Octave", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 31
    {"id": "kyutai:7762_8734_000048-0002", "name": "Monique", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "F", "stars": 3},     # etait Kyutai 32
    {"id": "kyutai:8128_7016_000047-0002", "name": "Quentin", "region": "\U0001F1E8\U0001F1E6 Canada (Kyutai)", "gender": "M", "stars": 1},     # etait Kyutai 33 -- RETENUE le 23/09/2026 (1 etoile, accent canadien)
    {"id": "kyutai:928_486_000075-0001", "name": "Raymond", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 34
    {"id": "kyutai:9834_9697_000150-0003", "name": "Simon", "region": "\U0001F1EB\U0001F1F7 France (Kyutai)", "gender": "M", "stars": 3},      # etait Kyutai 35
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
                            contexte: str = "",
                            vocabulaire=None) -> bytes:
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
    text = _clean_text(text, vocabulaire)
    if not text:
        return b""

    contexte = _clean_text(contexte, vocabulaire) if contexte else ""
    cle = (contexte + "\x00" + text) if contexte else text

    cached = _tts_cache.get_audio(cle, voice, rate, pitch, "wav")
    if cached is not None:
        return cached

    wav_bytes = await _demander_au_moteur_kyutai(text, _kyutai_voix_id(voice),
                                                 contexte)
    if not wav_bytes:
        return b""

    # Rognage du silence de QUEUE (23/09/2026, demande de Laurent) : le moteur
    # Kyutai ne rogne pas ses bords -- il garde la respiration qu'il vient de
    # produire (0,30 a 0,43 s mesurees les 17 et 21/09/2026 ; queue MEDIANE de
    # 0,37 s sur les 300 fichiers du cache le 23/09/2026). A l'ecoute, Laurent a
    # trouve les pauses APRES LES POINTS trop longues et les SAUTS DE LIGNE trop
    # rapides : la queue est ramenee a 0,20 s ICI, et la pause entre paragraphes
    # remonte a 600 ms dans `frontend/app.js` (les deux se cumulent, on regle
    # donc les deux ensemble).
    # Le rognage se fait AVANT la vitesse, la hauteur et le niveau : c'est le son
    # natif du moteur qu'on rogne -- le meme esprit que XTTS et NeuTTS, qui
    # rognent dans leur service. Le fichier mis en cache est deja rogne.
    wav_bytes = _audio_queue.rogner_queue_wav(wav_bytes)

    # Vitesse puis hauteur (aucun des deux n'existe dans le moteur).
    wav_bytes = _audio_rate.appliquer_vitesse(wav_bytes, _percent_to_speed(rate))
    wav_bytes = _apply_pitch_shift(wav_bytes, _hz_to_semitones(pitch))

    # Niveau : le moteur Kyutai ne regle pas son volume de sortie, et ses
    # phrases s'eparpillent a la sortie (mesure du 21/09/2026 : de 3,8 a 10,8 %
    # de la pleine echelle, soit 9,1 dB d'ecart -- le module les ramene a ~2 dB).
    # On corrige ICI, apres la vitesse et la hauteur, pour que ce soit le niveau
    # definitif qui parte au cache : une phrase relue ne redevient jamais faible.
    wav_bytes = _audio_gain.normaliser_wav_parole(wav_bytes)

    _tts_cache.put_audio(cle, voice, rate, pitch, "wav", wav_bytes)
    return wav_bytes


# ==============================================================
# QWEN3-TTS -- moteur de CLONAGE (Alibaba), ajoute le 26/09/2026
# ==============================================================
# Cinquieme moteur de clonage, et le seul dont la licence soit LIBRE des deux
# cotes : code ET poids en **Apache-2.0** (`Qwen/Qwen3-TTS-12Hz-0.6B-Base`).
# L'audio produit est donc PARTAGEABLE, ce qu'XTTS v2 (CPML, non commercial)
# ne permet pas -- c'est ce qui a decide Laurent a l'essayer.
#
# MEMES 35 EXTRAITS QUE KYUTAI, donc MEMES VOIX ET MEMES PRENOMS (verifie le
# 26/09/2026 : les 35 identifiants du catalogue sont exactement les 35
# references de sa garde-robe, dans les deux sens). Seul le moteur change :
# `kyutai:10087_11650_000028-0002` et `qwen:10087_11650_000028-0002` sont le
# MEME enregistrement de voix, lu par deux moteurs differents.
#
# CE QUI LE DISTINGUE DES AUTRES (mesures des 25 et 26/09/2026) :
#   - il a besoin du TEXTE EXACT de l'extrait, en plus de l'extrait (le
#     service le lit dans `qwen_tts_service/voix/references.csv`) ;
#   - PAS DE STREAMING dans la version installee (`qwen-tts` 0.1.1) : l'audio
#     sort d'un bloc, donc 2 a 4 s avant le premier son d'un chapitre ;
#   - il rend PARFOIS une phrase vide (0,36 s de silence) : le service relance
#     tout seul ;
#   - VITESSE, mesure du 26/09/2026 sur la RTX 4060, phrase par phrase (notre
#     facon de demander) : **x0,45 a x0,50 le temps reel**, soit environ DEUX
#     FOIS trop lent pour suivre la lecture. Ni l'attention « sdpa » (x0,49)
#     ni deux generations de front (x0,50) n'y changent rien : la carte n'est
#     qu'a 27 % pendant la generation, l'attente est dans la boucle du modele.
#     NIMM Voix mesure x1,2 a x1,6, mais en envoyant QUATRE PHRASES PAR APPEL.
#     Le prechargement du lecteur (2 phrases d'avance, 5 000 caracteres)
#     encaisse le demarrage, pas un chapitre entier : attendre des blancs.
#   - le « contexte glissant » de Kyutai (fin de la phrase precedente) n'a
#     PAS d'equivalent ici : il est transmis puis ignore par le service.

QWEN_URL = os.environ.get("NIMM_QWEN_URL", "http://127.0.0.1:8086")
# Delai large : une phrase se calcule en gros en DEUX FOIS sa duree de lecture
# (mesure du 26/09/2026), et la premiere phrase d'une voix paie en plus son
# empreinte (0,7 a 1,4 s).
QWEN_DELAI_S = float(os.environ.get("NIMM_QWEN_DELAI", "600") or "600")

# ATTENTION : le catalogue `QWEN_VOICES` est CONSTRUIT PLUS BAS, apres le
# catalogue Pocket -- voir sa section en fin de catalogues. Il reprend les TROIS
# familles (Kyutai, Kokoro, Pocket), donc il ne peut pas etre ecrit ici : Python
# ne connaitrait pas encore `KOKORO_VOICES` ni `POCKET_VOICES` (erreur attrapee
# le 28/09/2026, quand le catalogue est passe de 35 a 157 voix).


class QwenIndisponible(RuntimeError):
    """Le service Qwen3-TTS ne repond pas (moteur eteint ou en chargement)."""


def _qwen_voix_id(voice: str) -> str:
    """Retire le prefixe 'qwen:' pour obtenir l'identifiant de la voix."""
    return voice.split(":", 1)[1] if ":" in voice else voice


async def _demander_au_moteur_qwen(texte: str, identifiant_voix: str) -> bytes:
    """Envoie une phrase au service Qwen3-TTS et renvoie le WAV brut.

    Le service tourne a cote (`qwen_tts_service/`, Python 3.12 + PyTorch,
    port 8086). Il relance lui-meme une phrase revenue vide : ici, on ne voit
    qu'un WAV, ou une erreur claire.
    """
    import httpx

    try:
        async with httpx.AsyncClient(timeout=QWEN_DELAI_S) as client:
            reponse = await client.post(
                QWEN_URL + "/tts",
                json={"texte": texte, "voix": identifiant_voix},
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
            httpx.RemoteProtocolError, httpx.WriteError) as erreur:
        raise QwenIndisponible(
            "Le moteur de voix Qwen3-TTS ne repond pas ("
            + type(erreur).__name__ + "). Double-clique sur "
            "DEMARRER_QWEN_TTS.bat (dossier qwen_tts_service), puis relance "
            "la lecture."
        )

    if reponse.status_code != 200:
        detail = ""
        try:
            detail = (reponse.json() or {}).get("erreur", "")
        except Exception:
            detail = ""
        raise QwenIndisponible(
            "Le moteur de voix Qwen3-TTS a refuse la phrase (code %d%s)."
            % (reponse.status_code, (" : " + detail) if detail else "")
        )

    return reponse.content


async def synthesize_qwen(text: str, voice: str, rate: str = "+0%",
                          pitch: str = "+0Hz", vocabulaire=None) -> bytes:
    """
    Synthese Qwen3-TTS pour une phrase. Le moteur tourne dans son propre
    service (Python 3.12 + PyTorch), appele ici en HTTP local.

    Vitesse : aucun reglage natif -> post-traitement ffmpeg (atempo).
    Hauteur : aucun reglage natif -> post-traitement _apply_pitch_shift
    (Rubber Band), comme pour Kokoro, Piper et Kyutai.
    L'audio final est mis en cache disque, exactement comme les autres
    moteurs : un passage deja lu ne redemande rien au moteur.

    Cache : la cle porte le PREFIXE de la voix (`qwen:...`), donc elle ne
    peut pas confondre un rendu Qwen avec un rendu Kyutai de la meme voix --
    c'est pour cela que VERSION_CACHE n'a pas eu besoin de bouger.
    """
    texte_avant = text
    # PONCTUATION LIBRE (verdict d'oreille de Laurent, 23/10/2026) : Qwen recoit
    # le texte tel que l'AUTEUR l'a ponctue -- « ; », « : » et parentheses ne
    # sont plus convertis, et une virgule finale reste une virgule. Le banc
    # `test_voix/_banc_qwen_ponctuation.py` (lot
    # `test_voix/ecoute_ponctuation_libre_20261023_1109/`) a fait entendre les
    # deux versions sur le meme passage de « Dialogues desaccordes » : « la
    # ponctuation du livre » est la reference. Les AUTRES moteurs gardent les
    # regles du 17/09/2026 (le drapeau est FAUX par defaut) : ils n'ont pas ete
    # reecoutes, et rien ne prouve que ces regles leur soient inutiles.
    text = _clean_text(text, vocabulaire, ponctuation_libre=True)
    if not text:
        return b""

    # MODE DIAGNOSTIC (03/10/2026, demande de Laurent). Quand `NIMM_DIAGNOSTIC=1`,
    # deux choses changent : on IGNORE le cache (chaque phrase est vraiment
    # fabriquee au moment ou elle est lue) et on trace CHAQUE etape du traitement
    # dans `modules/diagnostic.py`. Sans la variable, rien ne change du tout.
    from modules import diagnostic
    suivi = diagnostic.actif()
    etapes = []
    debut_total = time.perf_counter() if suivi else 0.0

    if not suivi:
        cached = _tts_cache.get_audio(text, voice, rate, pitch, "wav")
        if cached is not None:
            return cached

    debut_moteur = time.perf_counter() if suivi else 0.0
    wav_bytes = await _demander_au_moteur_qwen(text, _qwen_voix_id(voice))
    secondes_moteur = (time.perf_counter() - debut_moteur) if suivi else 0.0
    if not wav_bytes:
        return b""
    if suivi:
        etapes.append(('01_brut_moteur', wav_bytes))

    # Rognage du silence de QUEUE, comme pour Kyutai (23/09/2026) : le moteur
    # garde la respiration qu'il vient de produire, et Laurent trouve les
    # pauses apres les points trop longues. On regle la queue ICI, et la pause
    # entre paragraphes reste a 600 ms dans `frontend/app.js`.
    wav_bytes = _audio_queue.rogner_queue_wav(wav_bytes)
    if suivi:
        etapes.append(('02_rognage_queue', wav_bytes))

    # Vitesse puis hauteur (aucun des deux n'existe dans le moteur).
    wav_bytes = _audio_rate.appliquer_vitesse(wav_bytes, _percent_to_speed(rate))
    if suivi:
        etapes.append(('03_vitesse', wav_bytes))
    wav_bytes = _apply_pitch_shift(wav_bytes, _hz_to_semitones(pitch))
    if suivi:
        etapes.append(('04_hauteur', wav_bytes))

    # Niveau : normalise comme les autres moteurs, pour qu'aucune phrase ne
    # « decroche » a cote de ses voisines. C'EST ICI que le gain peut atteindre
    # x4 (+12 dB) sur une phrase faible : c'est l'etape a regarder quand un
    # bruit de fond devient audible.
    wav_bytes = _audio_gain.normaliser_wav_parole(wav_bytes)
    if suivi:
        etapes.append(('05_normalisation', wav_bytes))

    # Fondu d'entree (29/09/2026, retour d'ecoute de Laurent) : la respiration
    # posee entre deux phrases rendait audible un « tic » d'attaque -- un
    # transitoire que la normalisation amplifie. Laurent a choisi 100 ms a
    # l'oreille (banc : 0 / 25 / 50 / 100 ms). Applique EN DERNIER, apres la
    # normalisation : c'est l'audio final qui est adouci.
    wav_bytes = _audio_gain.fondu_entree_wav(wav_bytes)
    if suivi:
        etapes.append(('06_fondu_entree', wav_bytes))

    if suivi:
        diagnostic.enregistrer(texte_avant, text, voice, rate, pitch, etapes,
                               secondes_moteur,
                               time.perf_counter() - debut_total)
    else:
        _tts_cache.put_audio(text, voice, rate, pitch, "wav", wav_bytes)
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
    {"id": "xtts:8128_7016_000047-0002", "name": "Quentin", "region": "\U0001F1E8\U0001F1E6 Canada (XTTS)", "gender": "M", "stars": 1},
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
    {"id": "neutts:8128_7016_000047-0002", "name": "Quentin", "region": "\U0001F1E8\U0001F1E6 Canada (NeuTTS)", "gender": "M", "stars": 1},
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


# ==============================================================
# POCKET TTS -- moteur de CLONAGE de Kyutai (CPU), ajoute le 21/09/2026
# ==============================================================
# Sixieme moteur. Pocket TTS est le « petit frere » de Kyutai TTS 1.6B :
# 100 M de parametres (contre 1,8 milliard), il tourne sur le PROCESSEUR et
# n'occupe donc PAS la carte graphique -- il cohabite avec Kyutai, Edge,
# Kokoro et Piper. Il clone une voix depuis un extrait de reference (WAV),
# sans avoir besoin du texte dit dans l'extrait (contrairement a NeuTTS).
#
# MEMES EXTRAITS QUE LES VOIX `dp_*` D'XTTS (et de NeuTTS) : ce sont les
# enregistrements du domaine public prepares par Laurent. Les PRENOMS SONT
# DONC LES MEMES (Marthe, Solange, Theodore...) -- decision de Laurent du
# 20/09/2026 : « s'ils existent deja dans un autre moteur, autant les
# utiliser, c'est bien plus intuitif ». Un seul est nouveau : JEAN_EDGAR,
# valide le 18/09, qui devient **Edgar**.
#
# SECOND LOT, importe le 23/09/2026 (les 10 derniers du catalogue) : dix voix
# SANS jumelle, nees d'extraits de LIVRES AUDIO DU COMMERCE, donc avec des
# prenoms neufs (Aubin, Cyprien, Lazare, Prosper, Firmin, Gaspard, Timoleon,
# Sylvain, Anselme, Barnabe). Voir le commentaire du bloc, plus bas.
#
# Mesures du 20/09/2026 (meme machine) : ratio 0,82 (1 h d'audio = 49 min de
# calcul), modele charge en 1,7 s, encodage d'une voix 3,8 s, 2,3 Go de RAM au
# pic. Le service tourne sur le port 8085 (`pocket_tts_service/`).
#
# ATTENTION (constat de Laurent, 20/09/2026) : sur un texte de 1 ou 2 mots, ce
# moteur sort parfois un QUASI-SILENCE (« un tic ») -- corrige cote service par
# une regeneration automatique (voir `servir_pocket_tts.py`).

POCKET_URL = os.environ.get("NIMM_POCKET_URL", "http://127.0.0.1:8085")
# Delai large : le moteur est plus LENT que Kyutai (~0,85 le temps reel) et la
# PREMIERE phrase d'une voix paie en plus son encodage (3,8 s mesure).
POCKET_DELAI_S = float(os.environ.get("NIMM_POCKET_DELAI", "240") or "240")

POCKET_VOICES = [
    # --- les 9 voix feminines (memes extraits que les voix dp_* de XTTS) ---
    {"id": "pocket:Femme001", "name": "Marthe", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    {"id": "pocket:Femme002", "name": "Solange", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    {"id": "pocket:Femme003", "name": "Yvette", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    {"id": "pocket:Femme004", "name": "Henriette", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    {"id": "pocket:Femme32321312445", "name": "Georgette", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    {"id": "pocket:Femme48897", "name": "Thérèse", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    {"id": "pocket:Femme65465464", "name": "Colette", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    {"id": "pocket:Femme6566554478", "name": "Juliette", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    {"id": "pocket:Femme65699878", "name": "Madeleine", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "F", "stars": 3},
    # --- les 9 voix masculines ---
    {"id": "pocket:Homme001", "name": "Marius", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:Homme002", "name": "Théodore", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:Homme004", "name": "Édouard", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:Homme1122544987", "name": "Victor", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:Homme1122545656487", "name": "Robert", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:Homme313213265", "name": "Paul", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:Homme65462104", "name": "Jules", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:Homme87976454321", "name": "Arthur", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    # --- LES 10 VOIX DU LOT DU 23/09/2026 (importees le 23/09/2026) -------
    # Dix nouveaux extraits prepares par Laurent, clones par l'atelier NIMM
    # Voix dans un seul lot, tous retenus et notes 3 etoiles par son ecoute du
    # 23/09/2026 (sorties\pocket_tts_retenues_20260923\). Ce sont les noms de
    # fichiers de l'atelier (ils disent d'ou vient la voix) ; le PRENOM est ce
    # que Laurent voit dans le lecteur.
    # ATTENTION, provenance DIFFERENTE du lot du 20/09 : ces 10 extraits
    # viennent de LIVRES AUDIO DU COMMERCE (Lizzie, Audible), lus par des
    # COMEDIENS PROFESSIONNELS (personnes reelles, oeuvres protegees). Ecoute
    # privee : d'accord. PARTAGE : interdit sans l'accord de la personne --
    # detail extrait par extrait dans ORIGINE_ET_LICENCE.txt du lot, et
    # `pocket_tts_service\ATTRIBUTION.md`.
    {"id": "pocket:homme_aigu_6877654", "name": "Aubin", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_aigu_987654", "name": "Cyprien", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_grave_5649798", "name": "Lazare", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_grave_65121598", "name": "Prosper", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_grave_6546546", "name": "Firmin", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_grave_6549821", "name": "Gaspard", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_normal_21545605", "name": "Timoléon", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_normal_65465987312", "name": "Sylvain", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_normal65465409", "name": "Anselme", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    {"id": "pocket:homme_voix_grave265146", "name": "Barnabé", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
    # --- l'unique voix SANS jumelle : JEAN_EDGAR, valide le 18/09/2026 ---
    # Il n'a ni etoiles ni criteres releves : il faudra l'ecouter pour les
    # remplir (etoiles provisoires a 3, comme les autres voix retenues).
    {"id": "pocket:JEAN_EDGAR", "name": "Edgar", "region": "\U0001F1EB\U0001F1F7 France (Pocket TTS)", "gender": "M", "stars": 3},
]
# --- FIN CATALOGUE POCKET TTS ---


# ==============================================================
# CATALOGUE QWEN3-TTS -- CONSTRUIT, 157 voix (28/09/2026)
# ==============================================================
# POURQUOI ICI, ET PAS DANS LA SECTION QWEN : ce catalogue reprend les TROIS
# familles de voix -- Kyutai, Kokoro et Pocket -- donc il doit etre construit
# APRES leurs catalogues. Ecrit a sa place « logique » (pres de la section Qwen),
# il plantait : `KOKORO_VOICES` et `POCKET_VOICES` n'existaient pas encore
# (NameError attrape le 28/09/2026, en passant de 35 a 157 voix).
#
# POURQUOI TROIS FAMILLES : NIMM Voix a **clone** dans qwentts.cpp les voix que
# nous avions deja -- les 35 Kyutai (CML-TTS), les 94 Kokoro et les 28
# « Decoupage OK » (nos 28 references Pocket). MEME identifiant, donc meme
# prenom, meme genre et memes etoiles : seule la LECTURE change de moteur.
# Construit et non recopie, comme avant : deux tables ecrites a la main
# finiraient par diverger -- c'est exactement ce que le memo de NIMM Voix veut
# eviter (« un seul jeu de noms et de notes dans les deux ateliers »).
#
# Verifie le 28/09/2026 : les 157 extraits sont chez le moteur et chacun a sa
# voix connue ici (`_essais/_test_catalogue_qwen.py`, `_essais/_etat_157_voix.py`).


def _region_qwen(region: str) -> str:
    """La region d'une voix, avec le moteur remplace par « (Qwen) ».

    Les catalogues sources portent « (NIMM Voix) », « (Kyutai) »,
    « (Pocket TTS) »... : c'est le meme drapeau et le meme pays, un autre moteur.
    """
    return re.sub(r"\([^)]*\)\s*$", "(Qwen)", region).strip()


QWEN_VOICES = [
    {"id": "qwen:" + v["id"].split(":", 1)[1],
     "name": v["name"],
     "region": _region_qwen(v["region"]),
     "gender": v["gender"],
     "stars": v["stars"]}
    for v in KYUTAI_VOICES + KOKORO_VOICES + POCKET_VOICES
]

# ==============================================================
# LA VOIX DE LA FAMILLE (29/09/2026) : elle n'entre par AUCUNE boucle
# ==============================================================
# `Maya_normale` a ete clonee par l'atelier NIMM Voix a partir d'un
# enregistrement de Laurent avec sa fille : ce n'est la jumelle d'AUCUNE voix
# existante, donc elle ne peut pas sortir de `KYUTAI_VOICES + KOKORO_VOICES +
# POCKET_VOICES` -- on l'ecrit a la main, ici.
#
# Ce qu'il faut savoir :
#   - la REFERENCE vit avec les autres, dans `qwen_tts_service/voix/` (le WAV
#     est hors Git, comme les 157 autres) et le moteur la connait deja ;
#   - son TEXTE de reference est PRIVE : il vit dans
#     `qwen_tts_service/voix/references_privees.csv`, hors Git (Maya a lu le
#     debut d'un roman du commerce), et le service lit ce fichier EN PLUS ;
#   - `gender` "F" sert a l'AFFICHAGE (le symbole devant son prenom) et aux
#     filtres de la fenetre de voix. Sa presence ne la fait PAS entrer dans le
#     casting automatique : le pool (`DEDICATED_VOICES_F/M`,
#     modules/voice_casting.py) ne puise que dans KYUTAI, EDGE et KOKORO, et
#     aucune voix Qwen n'y figure ;
#   - `stars` : **0 etoile, volontairement** (demande de Laurent, 29/09/2026 :
#     « il faut la sortir d'un casting automatique »). C'est la convention ecrite
#     du projet : une voix notee 0 reste **choisissable A LA MAIN** mais est
#     ECARTEE du pool automatique, comme les voix Piper ecartees et la voix
#     Kyutai n° 33. Double securite : elle est hors pool aujourd'hui (le pool
#     n'ouvre pas sur Qwen) ET elle le resterait si le pool s'ouvrait un jour.
#     Laurent : « Elle peut rester, mais je ne l'utiliserai pas tres souvent,
#     sauf cas particulier » -- c'est exactement ce que 0 etoile exprime.
#
# VOIX D'UNE PERSONNE REELLE : usage PRIVE (accord de Maya pour l'atelier).
QWEN_VOICES.append(
    {"id": "qwen:Maya_normale", "name": "Maya",
     "region": "\U0001F3E0 Famille (Qwen)", "gender": "F", "stars": 0},
)

# ==============================================================
# LES 25 VOIX CML-TTS « cml_restants » (30/09/2026) : entrees par la passerelle
# ==============================================================
# Meme cas que Maya : elles n'entrent par AUCUNE boucle -- on les ecrit ici.
# NIMM Voix a clone les 25 voix CML-TTS qui restaient (« vague 6 », dossier
# `cml_restants`) et les a deposees le 30/09/2026 avec le memo
# `_MEMO_25_VOIX_CML_20260930/` (leurs textes et leurs droits).
#
# CES 25 VOIX EXISTAIENT DEJA AU CATALOGUE, EN XTTS : ce sont exactement les 25
# `xtts:cmlXXXX` versees le 14/09/2026 -- meme extrait, donc meme timbre et meme
# prenom. On ajoute leur JUMELLE Qwen, comme pour les 35 Kyutai le 29/09/2026 :
# `xtts:cml3344` -> `qwen:cml3344`. Aucun livre ne les lisait (verifie le
# 30/09/2026 avec `test_voix/_etat_familles_voix.py`) : cet ajout est purement
# ADDITIF.
#
# LES ETOILES SONT CELLES DU 30/09/2026, et ce n'est pas un detail : Laurent a
# REECOUTE les 25 CLONES ce jour-la et en a renote 12 (memo, tableau du point 3).
# SON OREILLE DU 30/09 FAIT FOI ; les fiches `xtts:` gardent, elles, leurs
# etoiles du 14/09 (rien n'est efface). Quatre references ont ete reprises et
# validees 5/5 (`cml2771`, `cml3182`, `cml5526`, `cml7239` : les premieres
# commencaient au milieu d'un mot, defaut de bord connu) et `cml7614` est une
# VOIX D'ENFANT (age et role « enfant » dans les annotations d'ecoute).
#
# La mention d'accent est un simple libelle d'affichage (comme pour les 157) :
# Laurent l'a nommee « paysan », « anglais », « canadien » et « maghrebin ».
#
# DROITS : banque CML-TTS, licence CC BY 4.0 -- libre, y compris pour un
# PARTAGE, a condition de citer « Kyutai + CML-TTS » (contrairement a
# `Maya_normale`, qui est une voix privee).
_VOIX_CML_30_09_2026 = (
    # (identifiant, prenom, genre, etoiles, mention d'accent)
    ("cml1840", "Achille", "M", 3, ""),
    # `cml1649` : accent ALLEMAND (le memo du 30/09 annoncait « anglais » ; Laurent
    # a corrige le soir meme, « au temps pour moi » -- sa fiche du 14/09 disait
    # deja « allemand », et c'est elle qui avait raison).
    ("cml1649", "Berthe", "F", 3, "allemand"),
    ("cml1869", "Cécile", "F", 3, ""),
    ("cml2033", "Lucie", "F", 3, "anglais"),
    ("cml2316", "Joséphine", "F", 1, ""),
    ("cml2771", "Lucien", "M", 3, ""),
    ("cml3060", "Armand", "M", 2, ""),
    ("cml3182", "Maurice", "M", 3, ""),
    ("cml3344", "Honoré", "M", 3, ""),
    ("cml3503", "Félix", "M", 3, ""),
    ("cml5525", "Émile", "M", 3, ""),
    ("cml5526", "Hippolyte", "M", 2, ""),
    ("cml6070", "Estelle", "F", 2, ""),
    ("cml6249", "Célestin", "M", 3, "paysan"),
    ("cml6348", "Hortense", "F", 2, "espagnol/italien"),
    ("cml6381", "Gabrielle", "F", 2, ""),
    ("cml7239", "Hector", "M", 3, "maghrébin"),
    ("cml7377", "Ernest", "M", 3, ""),
    ("cml7423", "Basile", "M", 2, "canadien"),
    ("cml7614", "Gustave", "M", 3, ""),
    ("cml9804", "Alphonse", "M", 3, ""),
    ("cml10065", "Auguste", "M", 2, ""),
    ("cml12501", "Charles", "M", 3, ""),
    ("cml12512", "Eugène", "M", 3, ""),
    ("cml12823", "Agathe", "F", 3, ""),
)
QWEN_VOICES += [
    {"id": "qwen:" + identifiant, "name": prenom,
     "region": ("\U0001F1EB\U0001F1F7 France (Qwen)"
                + (" - accent " + accent if accent else "")),
     "gender": genre, "stars": etoiles}
    for identifiant, prenom, genre, etoiles, accent in _VOIX_CML_30_09_2026
]

# ==============================================================
# LES 18 VOIX INDIENNES (10/10/2026) -- pour SHANTARAM
# ==============================================================
# Fabriquees par l'atelier NIMM Voix : des timbres montes en melangeant les
# QUATRE voix hindi de Kokoro (hf_alpha, hf_beta, hm_omega, hm_psi) a des voix
# espagnoles, italiennes et anglaises, puis CLONEES par qwentts.cpp. Laurent
# les a gardees a l'oreille (72 extraits ecoutes, 24 retenues, puis un elagage
# mesure en a garde 18 : 10 hommes, 8 femmes) et les 18 clones disent TOUT le
# texte (18/18 a 41/41 mots, verifie par transcription). Paquet recu le
# 10/10/2026 (memo MEMO_FAMILLE_HINDI_10-10-2026) : les 18 WAV sont dans
# `qwen_tts_service/voix/` et leurs 18 lignes dans `references.csv`.
#
# POURQUOI HORS BOUCLE : comme `Maya_normale`, elles n'ont AUCUNE jumelle dans
# les catalogues existants -- ce sont des timbres NEUFS, on les ecrit a la main.
#
# LE NOM est un PRENOM INDIEN, donne le 10/10/2026 (demande de Laurent : « si tu
# peux les nommer avec des prenoms Hindou »). L'IDENTIFIANT, lui, NE BOUGE PAS :
# il reste `hindi_*`, le nom du fichier -- c'est ainsi que NIMM Voix les connait
# et que le moteur les appelle (le nom du fichier EST l'identifiant de la voix).
#
# LE DRAPEAU : la `region` porte le drapeau INDIEN. Le libelle affiche TOUJOURS
# le drapeau francais en premier (la langue), puis celui-ci -- soit « 🇫🇷🇮🇳 »,
# exactement comme « 🇫🇷🇬🇧 » pour les voix anglaises (app.js,
# `_secondDrapeauDeVoix`). FICHIER VOLONTAIREMENT en UTF-8 : ne pas le
# re-encoder en ASCII.
#
# 0 ETOILE A L'IMPORT, comme les 10 voix « accent allemand » du 20/09/2026 : une
# voix notee 0 reste CHOISISSABLE A LA MAIN mais est ECARTEE du casting
# automatique. Laurent ne les a pas encore notees a l'oreille ; leur fiche
# d'ecoute (`data/annotations_voix.json`, role « etranger ») les fera entrer
# dans le pool le jour ou il les notera.
#
# DROITS : voix 100 % SYNTHETIQUES (Kokoro + melanges, Apache-2.0), AUCUNE
# personne reelle. PARTAGEABLES, comme les 30 voix du catalogue.
_VOIX_HINDI_10_10_2026 = (
    # (identifiant, prenom, genre, etoiles)
    ("hindi_h07_jeune",       "Arjun",   "M", 0),
    ("hindi_h13_adulte",      "Rohan",   "M", 0),
    ("hindi_h14_adulte_aigu", "Vikram",  "M", 0),
    ("hindi_h17_enfant",      "Aryan",   "M", 0),
    ("hindi_h19_grave",       "Suresh",  "M", 0),
    ("hindi_h20_grave",       "Ramesh",  "M", 0),
    ("hindi_h02_adulte",      "Rajesh",  "M", 0),
    ("hindi_h06_jeune_aigu",  "Kiran",   "M", 0),
    ("hindi_h09_adulte",      "Sanjay",  "M", 0),
    ("hindi_h16_jeune_aigu",  "Amit",    "M", 0),
    ("hindi_f02_adulte",      "Priya",   "F", 0),
    ("hindi_f06_grave",       "Meera",   "F", 0),
    ("hindi_f07_adulte_aigu", "Anjali",  "F", 0),
    ("hindi_f08_jeune_aigu",  "Sneha",   "F", 0),
    ("hindi_f09_vieux_aigu",  "Kamala",  "F", 0),
    ("hindi_f12_grave",       "Lakshmi", "F", 0),
    ("hindi_f14_grave",       "Radha",   "F", 0),
    ("hindi_f16_jeune_aigu",  "Deepa",   "F", 0),
)
QWEN_VOICES += [
    {"id": "qwen:" + identifiant, "name": prenom,
     "region": "\U0001F1EE\U0001F1F3 Inde (Qwen)",
     "gender": genre, "stars": etoiles}
    for identifiant, prenom, genre, etoiles in _VOIX_HINDI_10_10_2026
]

# ==============================================================
# LES 12 VOIX MLS (20/10/2026) -- pour les PETITS ROLES
# ==============================================================
# Fabriquees par l'atelier NIMM Voix a partir du corpus MLS (Meta /
# LibriVox, CC BY 4.0) : lecteurs francais de livres audio du domaine
# public. 28 voix clonees, 24 retenues a l'oreille de Laurent, dont 9
# etaient DEJA ici sous un identifiant `cml` (meme lecteur LibriVox,
# autre passage) : il restait donc 15 timbres NEUFS, dont 3 dont le
# texte de reference est encore a arbitrer (`MLS_5232_F`, `MLS_1817_H`,
# `MLS_2904_H` -- NIMM Voix les regenere sur la foi de son
# `09_textes_a_relire.csv`). Ces 3-la ne sont donc PAS entrees, et ce
# sont les 2 SEULS timbres d'homme du lot : ce sont 12 voix de FEMME
# qui arrivent ici.
#
# PRENOMS : proposition du memo du 20/10/2026, corrigee le 21/10/2026
# la ou le prenom etait DEJA pris dans le catalogue -- Amelie,
# Blanche, Delphine, Fanny, Jeanne, Ninon, Solange, Yvette, Firmin et
# Marius avaient deja leur voix (`qwen:ff_amelie`, `qwen:ff_delphine`,
# `qwen:Femme002`...). Releve par `_essais/_verif_voix_mls_20261021.py`,
# nouveaux prenoms valides par Laurent le 21/10/2026.
#
# 0 ETOILE A L'IMPORT : elles sont destinees aux personnages de moins
# de 8 repliques (MINOR_THRESHOLD) et doivent rester HORS du pool
# automatique -- un figurant ne doit pas voler la voix d'un personnage
# principal. C'est la convention du projet (Maya_normale, hindi, ...).
#
# DROITS : MLS = CC BY 4.0 -> attribution « MLS / LibriVox »
# obligatoire en cas de diffusion. Ce sont des PERSONNES REELLES : la
# licence du corpus ne regle pas le droit de la personnalite (plus
# strict en France). Usage prive de l'atelier : OK ; prudence avant
# tout partage large.
_VOIX_MLS_20_10_2026 = (
    # (identifiant, prenom, genre, etoiles, mention d'accent)
    ("MLS_10620_F", "Albertine",  "F", 0, ""),
    ("MLS_12709_F", "Angèle",     "F", 0, ""),
    ("MLS_12713_F", "Clémence",   "F", 0, ""),
    ("MLS_12981_F", "Antoinette", "F", 0, ""),
    ("MLS_13634_F", "Élise",      "F", 0, ""),
    ("MLS_1474_F",  "Bernadette", "F", 0, "paysan"),
    ("MLS_2085_F",  "Denise",     "F", 0, "quebecois"),
    ("MLS_3204_F",  "Léonie",     "F", 0, ""),
    ("MLS_3698_F",  "Margot",     "F", 0, ""),
    ("MLS_4512_F",  "Germaine",   "F", 0, ""),
    ("MLS_12968_F", "Marcelle",   "F", 0, ""),
    ("MLS_123_F",   "Rose",       "F", 0, ""),
)
QWEN_VOICES += [
    {"id": "qwen:" + identifiant, "name": prenom,
     "region": ("\U0001F1EB\U0001F1F7 France (Qwen)"
                + (" - accent " + accent if accent else "")),
     "gender": genre, "stars": etoiles}
    for identifiant, prenom, genre, etoiles, accent in _VOIX_MLS_20_10_2026
]

# ==============================================================
# LES 3 VOIX DE SERIE (16/10/2026) -- Thyrion, Sersei et Saul
# ==============================================================
# Demande de Laurent, mot pour mot : « On va cloner des nouvelles voix [...] Il y
# a Thyrion, Sersei et Saul. Elles ressemblent bien aux originales, en tout cas
# elles m'y font penser, donc on va les appeler comme ca. »
#
# LE CLONAGE : trois extraits deposes par Laurent dans « Voix a faires » de
# l'atelier NIMM Voix (17,1 a 17,4 s chacun), clones par qwentts.cpp le
# 16/10/2026 -- lot `sorties\trois_voix_thyrion_sersei_saul_20261016`. Laurent a
# garde les TROIS a l'oreille, et le controle machine dit la meme chose : les
# trois clones disent 100 % du texte de controle (41 / 41 mots, relus par
# Whisper -- `VERIFICATION_DU_TEXTE.txt` du lot).
#
# POURQUOI HORS BOUCLE : comme `Maya_normale` et les 18 voix indiennes, ce sont
# des timbres NEUFS -- aucune jumelle dans `KYUTAI_VOICES + KOKORO_VOICES +
# POCKET_VOICES` : on les ecrit a la main, ici. Leurs 3 WAV sont dans
# `qwen_tts_service/voix/` et leurs 3 lignes de texte dans le fichier **PRIVE**
# `references_privees.csv` (**hors depot**) : ce sont des repliques de dialogues
# d'oeuvres sous droits, et la regle du projet est qu'aucun texte de ce genre ne
# part sur le depot -- exactement comme celui de Maya. Elles avaient d'abord ete
# posees dans le fichier public par erreur ; elles ont ete **basculees avant tout
# commit** (`_essais/_basculer_textes_series_prive_20261016.py`) et le service,
# qui lit les DEUX fichiers, n'y voit aucune difference. Outil d'entree :
# `_essais/_entrer_voix_series_20261016.py` ; copies datees AVANT l'ecriture :
# `references.bak_avant_thyrion_sersei_saul_20261016.csv` (le public) et
# `references_privees.csv.bak_avant_bascule_prive_20261016` (le prive).
#
# L'IDENTIFIANT est le nom du fichier (`Thyrion`, `Sersei`, `Saul`) -- c'est ainsi
# que le moteur les appelle ; le PRENOM affiche est le nom du personnage, et
# l'orthographe est celle de Laurent : « Thyrion » et « Sersei ».
#
# LE DRAPEAU : `region` porte le drapeau FRANCAIS, et rien d'autre -- precision
# de Laurent, 16/10/2026 : « le drapeau doit etre francais, ce sont des voix
# 100 % francaises. Pas voix etrangeres, ni de drapeau autre que FR. » Ces voix
# sont clonees pour LIRE du francais : c'est la langue qui compte. La region ne
# porte donc AUCUN second drapeau (ni Royaume-Uni, ni autre) : app.js
# (`_secondDrapeauDeVoix`) n'affiche que « FR », comme pour les autres voix
# francaises. La premiere idee (drapeau britannique, parce que les series sont
# anglaises) a ete ecartee par Laurent le meme jour.
#
# 0 ETOILE A L'IMPORT (convention du 20/09/2026, comme les 18 voix indiennes et
# Maya) : une voix notee 0 reste CHOISISSABLE A LA MAIN mais est ECARTEE du
# casting automatique. Laurent ne les a pas encore notees a l'oreille ; sa fiche
# d'ecoute (`data/annotations_voix.json`) les fera entrer dans le pool le jour ou
# il les notera. AUCUNE fiche n'est ecrite ici -- comme pour Maya et JEAN_EDGAR,
# on n'invente pas des criteres (age, timbre, accent) qu'on n'a pas mesures.
#
# DROITS : ce sont les voix d'ACTEURS d'oeuvres du commerce (Game of Thrones,
# Better Call Saul) : usage PRIVE dans l'atelier, comme les extraits venus de
# livres audio du commerce (`qwen_tts_service/ATTRIBUTION.md`). Pour partager un
# jour, il faudrait des extraits libres de droits. Le portage et le modele, eux,
# sont libres (MIT / Apache-2.0).
# RETIREES LE 17/10/2026 (demande de Laurent) : les 3 voix de serie sont
# sorties de la garde-robe -- « on va faire mieux plus tard », avec un
# programme d'extraction a fabriquer (les extraits d'origine restent dans
# `NIMM Voix/Voix a faires/`). Le tuple est VIDE : le code qui suit
# (`QWEN_VOICES += [...]`) fonctionne avec une liste vide.
_VOIX_SERIES_16_10_2026 = ()
QWEN_VOICES += [
    {"id": "qwen:" + identifiant, "name": prenom,
     "region": "\U0001F1EB\U0001F1F7 France (Qwen)",
     "gender": genre, "stars": etoiles}
    for identifiant, prenom, genre, etoiles in _VOIX_SERIES_16_10_2026
]

# ==============================================================
# LES 5 VOIX DU 19/10/2026 -- Aldo, Gus, Jesse, Verges, Sandor
# ==============================================================
# Clonees par NIMM Voix (lot `sorties\les_5_voix_retenues_20261019`),
# gardees par Laurent a l'oreille le 19/10/2026 (5/5 pour les quatre
# premieres, « le 04, D, est top » pour Sandor). Memo :
# `passerelle_NIMM_ePub\ENVOYES_par_NIMM_Voix\
# MEMO_5_VOIX_19-10-2026_pour_la_session_NIMM_ePub.md`. Elles sont arrivees
# dans `qwen_tts_service\voix/` (5 WAV de plus : 201 -> 206).
#
# POURQUOI HORS BOUCLE : comme `Maya_normale`, les 18 voix indiennes et les
# 3 voix de serie, ce sont des timbres NEUFS -- aucune jumelle dans
# `KYUTAI_VOICES + KOKORO_VOICES + POCKET_VOICES` : on les ecrit a la main.
#
# PRIVEES : voix d'acteurs de doublages -> audio et textes en usage prive
# (textes dans `references_privees.csv`, hors depot, jamais dans le public).
# Outil d'entree : `_essais/_entrer_5_voix_20261019.py` (rapport seul par
# defaut, `--ecrire` pour agir) ; copie datee du fichier prive AVANT
# l'ecriture : `references_privees.csv.bak_avant_5voix_20261019`.
#
# IDENTIFIANT = nom du fichier sans `_reference` ; « Verges » sans accent,
# parce que le fichier n'en porte pas (l'atelier retire les accents des
# noms de fichiers). Le PRENOM affiche garde l'orthographe de Laurent.
# GENRE : « M » (code des 18 voix indiennes). Un « H » ecrit par erreur le
# 17/10 rendait les voix invisibles.
# 0 ETOILE : hors casting automatique, choisissable a la main.
# DRAPEAU : francais et rien d'autre (precision de Laurent, 16/10/2026 :
# « ce sont des voix 100 % francaises ») -- aucun second drapeau.
_VOIX_19_10_2026 = (
    # (identifiant, prenom, genre, etoiles)
    ("Aldo",   "Aldo",   "M", 0),
    ("Gus",    "Gus",    "M", 0),
    ("Jesse",  "Jesse",  "M", 0),
    ("Verges", "Vergès", "M", 0),
    ("Sandor", "Sandor", "M", 0),
)
QWEN_VOICES += [
    {"id": "qwen:" + identifiant, "name": prenom,
     "region": "\U0001F1EB\U0001F1F7 France (Qwen)",
     "gender": genre, "stars": etoiles}
    for identifiant, prenom, genre, etoiles in _VOIX_19_10_2026
]

# ==============================================================
# LES 2 VOIX DU 22/10/2026 -- Soral et Naulleau
# ==============================================================
# Clonees par NIMM Voix (lot `sorties\soral_naulleau_20261022` : deux extraits
# deposes par Laurent dans « Voix a faires », nettoyes par DeepFilterNet,
# egalises vers le profil median de la garde-robe, -23 dBFS, bords 100 ms).
# Entendues par Laurent le 22/10 au soir : « Les 2 clones m'ont l'air bien. Je
# vais les tester sur des livres. » Il demande donc leur entree en garde-robe.
# Outil d'entree : `NIMM Voix\_atelier\
# _entrer_soral_naulleau_chez_nimm_epub.py` (rapport seul par defaut,
# `--ecrire` pour agir) ; copie datee du fichier prive AVANT l'ecriture :
# `references_privees.csv.bak_avant_soral_naulleau_20261023`.
#
# POURQUOI HORS BOUCLE : comme `Maya_normale`, les 18 voix indiennes, les 3
# voix de serie et les 5 du 19/10, ce sont des timbres NEUFS -- aucune jumelle
# dans `KYUTAI_VOICES + KOKORO_VOICES + POCKET_VOICES` : on les ecrit a la main.
#
# PRIVEES : voix de PERSONNES REELLES (voix publiques), sources non libres,
# usage strictement prive (decision de Laurent du 22/10/2026). Leurs textes
# sont dans `references_privees.csv` (hors depot), JAMAIS dans
# `references.csv` (le public) : un texte committe reste dans l'historique,
# meme retire apres.
#
# IDENTIFIANT = nom du fichier sans `_reference`. PRENOM affiche = orthographe
# de Laurent (il a ecrit « Nolleau » ; le fichier depose s'appelait
# `Naulleau.wav`, on garde cette orthographe, c'est le nom reel). GENRE « M »
# (code des 18 voix indiennes ; un « H » ecrit par erreur le 17/10 rendait les
# voix invisibles). 0 ETOILE : hors casting automatique, choisissable a la
# main, comme les 5 voix du 19/10. DRAPEAU francais et rien d'autre.
_VOIX_22_10_2026 = (
    # (identifiant, prenom, genre, etoiles)
    ("Naulleau", "Naulleau", "M", 0),
    ("Soral",    "Soral",    "M", 0),
)
QWEN_VOICES += [
    {"id": "qwen:" + identifiant, "name": prenom,
     "region": "\U0001F1EB\U0001F1F7 France (Qwen)",
     "gender": genre, "stars": etoiles}
    for identifiant, prenom, genre, etoiles in _VOIX_22_10_2026
]


# ---------------------------------------------------------------------------
# VOIX DU 23/10/2026 (session 147) : Freeman, Martial et Mike, trois doublures
# VF deposees par Laurent dans "Voix a faires". Nettoyees, egalisees (cible
# MEDIANE de la garde-robe) et clonees : 41/41 mots chacune.
#
# LA COULEUR A ETE CHOISIE PAR SON OREILLE : deux versions avaient ete
# fabriquees (cible mediane / cible Ariane Edge). Verdict de Laurent :
# "la variante mediane est mieux, je n'ai pas le son qui diminue sur les fins
# de phrases". Mesure : la cible Ariane creusait -6 dB entre 905 Hz et
# 2281 Hz. Voir ARCHITECTURE.md, recette du 23/10/2026.
#
# PRIVEES : personnes reelles (comediens de doublage), sources non libres
# (extraits YouTube decoupes sous Audacity), usage strictement prive. Textes
# dans `references_privees.csv` (hors depot), JAMAIS dans le public.
# GENRE "M". 0 ETOILE : hors casting automatique, choisissable a la main.
# DRAPEAU francais et rien d'autre.
_VOIX_23_10_2026 = (
    # (identifiant, prenom, genre, etoiles)
    ("Freeman", "Freeman", "M", 0),
    ("Martial", "Martial", "M", 0),
    ("Mike",    "Mike",    "M", 0),
)
QWEN_VOICES += [
    {"id": "qwen:" + identifiant, "name": prenom,
     "region": "\U0001F1EB\U0001F1F7 France (Qwen)",
     "gender": genre, "stars": etoiles}
    for identifiant, prenom, genre, etoiles in _VOIX_23_10_2026
]


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
                          pitch: str = "+0Hz", vocabulaire=None) -> bytes:
    """
    Synthese XTTS v2 pour une phrase. Le moteur tourne dans son propre
    service (Python 3.12 + PyTorch), appele ici en HTTP local.

    Vitesse : aucun reglage natif -> post-traitement ffmpeg (atempo).
    Hauteur : aucun reglage natif -> post-traitement _apply_pitch_shift
    (Rubber Band), comme pour Kokoro, Piper et Kyutai.
    L'audio final est mis en cache disque, exactement comme les autres
    moteurs : un passage deja lu ne redemande rien au moteur.
    """
    text = _clean_text(text, vocabulaire)
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
                            pitch: str = "+0Hz", vocabulaire=None) -> bytes:
    """Synthese NeuTTS pour une phrase. Le moteur tourne dans son propre
    service (Python 3.12 + PyTorch), appele ici en HTTP local.

    Vitesse : aucun reglage natif -> post-traitement ffmpeg (atempo), comme
    pour XTTS. Hauteur : post-traitement _apply_pitch_shift (Rubber Band),
    comme pour Kokoro, Piper, Kyutai et XTTS.
    L'audio final est mis en cache disque, exactement comme les autres
    moteurs : un passage deja lu ne redemande rien au moteur -- et c'est ce
    qui rend la lenteur du moteur supportable a l'usage.
    """
    text = _clean_text(text, vocabulaire)
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


# ==============================================================
# POCKET TTS -- le client du service (voir POCKET_VOICES plus haut)
# ==============================================================

class PocketIndisponible(RuntimeError):
    """Le service Pocket TTS ne repond pas (moteur eteint ou en chargement)."""


def _pocket_voix_id(voice: str) -> str:
    """Retire le prefixe 'pocket:' pour obtenir l'identifiant de la voix."""
    return voice.split(":", 1)[1] if ":" in voice else voice


async def _demander_au_moteur_pocket(texte: str, identifiant_voix: str) -> bytes:
    """Envoie une phrase au service Pocket TTS et renvoie le WAV brut."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=POCKET_DELAI_S) as client:
            reponse = await client.post(
                POCKET_URL + "/tts",
                json={"texte": texte, "voix": identifiant_voix},
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
            httpx.RemoteProtocolError, httpx.WriteError) as erreur:
        raise PocketIndisponible(
            "Le moteur de voix Pocket TTS ne repond pas ("
            + type(erreur).__name__ + "). Il s'allume avec le lecteur ; sinon, "
            "double-clique sur DEMARRER_POCKET_TTS.bat, puis relance la lecture."
        )

    if reponse.status_code != 200:
        detail = ""
        try:
            detail = (reponse.json() or {}).get("erreur", "")
        except Exception:
            detail = ""
        raise PocketIndisponible(
            "Le moteur de voix Pocket TTS a refuse la phrase (code %d%s)."
            % (reponse.status_code, (" : " + detail) if detail else "")
        )

    return reponse.content


async def synthesize_pocket(text: str, voice: str, rate: str = "+0%",
                            pitch: str = "+0Hz", vocabulaire=None) -> bytes:
    """Synthese Pocket TTS pour une phrase (service HTTP local, port 8085).

    Ce que ce moteur a de particulier (appris le 20/09/2026) :
      - il tourne sur le PROCESSEUR et cohabite donc avec les autres moteurs ;
      - il est LENT (~0,85 le temps reel) : c'est le CACHE AUDIO qui rend la
        lecture confortable (une phrase deja lue ne redemande rien) ;
      - la PREMIERE phrase d'une voix paie son encodage (3,8 s, une fois) ;
      - sur un texte de 1 ou 2 mots il sort parfois un quasi-silence : le
        service le detecte et regenere (garde-fou du cote moteur) ;
      - vitesse et hauteur n'existent PAS en natif -> meme post-traitement que
        Kyutai, XTTS et NeuTTS ;
      - son NIVEAU de sortie varie d'une prise a l'autre : on le ramene au
        niveau des autres moteurs, exactement comme pour Kyutai.
    """
    text = _clean_text(text, vocabulaire)
    if not text:
        return b""

    cached = _tts_cache.get_audio(text, voice, rate, pitch, "wav")
    if cached is not None:
        return cached

    wav_bytes = await _demander_au_moteur_pocket(text, _pocket_voix_id(voice))
    if not wav_bytes:
        return b""

    # Vitesse puis hauteur (aucun des deux n'existe dans le moteur).
    wav_bytes = _audio_rate.appliquer_vitesse(wav_bytes, _percent_to_speed(rate))
    wav_bytes = _apply_pitch_shift(wav_bytes, _hz_to_semitones(pitch))

    # Niveau : le moteur ne regle pas son volume de sortie et ses prises varient
    # (mesure du 21/09/2026 : de 7,5 a 12,8 %, soit 4,6 dB d'ecart ; le module
    # ramene les phrases fortes dans la fourchette). On corrige AVANT la mise en
    # cache : une phrase relue ne redevient pas faible.
    wav_bytes = _audio_gain.normaliser_wav_parole(wav_bytes)

    _tts_cache.put_audio(text, voice, rate, pitch, "wav", wav_bytes)
    return wav_bytes


