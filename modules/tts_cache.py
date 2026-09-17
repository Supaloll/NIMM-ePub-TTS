# -*- coding: utf-8 -*-
"""Cache disque de la synthese vocale.

La synthese TTS est deterministe : le meme texte (apres nettoyage), la meme
voix, la meme vitesse (rate) et le meme pitch produisent toujours le meme
audio. Stocker cet audio sur disque evite de re-solliciter le moteur (Edge
TTS via le reseau, Kokoro/Piper en CPU) a chaque relecture d'un passage deja
genere :

- relecture quasi instantanee (fini l'attente reseau au demarrage d'un
  chapitre deja ecoute) ;
- moins d'appels vers Microsoft (quotas, latence, cout) ;
- lecture possible sans reseau pour les passages deja ecoutes (ecran
  verrouille inclus).

Quota reglable (defaut : 20 Go) : au-dela, les fichiers les plus anciens
sont supprimes automatiquement. Les fichiers sont ecrits de facon atomique
(fichier temporaire + rename) : on ne lit jamais un fichier a moitie ecrit,
et deux requetes simultanees sur la meme cle ne se marchent pas dessus.
"""

import hashlib
import os
import threading
from pathlib import Path

# Dossier du cache. Quota : reglable via la variable d'environnement
# NIMM_TTS_CACHE_GB. RAMENE DE 20 Go A 2 Go LE 17/09/2026 (demande de Laurent) :
# « le cache ne me sert pas, je ne reecoute que tres rarement un passage deja
# entendu ». 2 Go suffisent largement pour un ou deux livres en cours -- et le
# bouton de purge evite d'attendre la purge automatique.
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "tts_cache"
_QUOTA_GB = int(os.environ.get("NIMM_TTS_CACHE_GB", "2") or "2")
CACHE_MAX_BYTES = _QUOTA_GB * 1024 * 1024 * 1024
PURGE_TARGET_BYTES = int(CACHE_MAX_BYTES * 0.75)

_lock = threading.Lock()
_known_total = None          # taille du dossier mesuree au premier ecrit
_written_since_purge = 0     # octets ecrits depuis la derniere mesure/purge


# Version du PRETRAITEMENT. A INCREMENTER des que le texte envoye au moteur
# change (regle de nettoyage, contexte glissant...) : les fichiers de cache
# d'une version anterieure ne sont plus servis, donc on n'entend JAMAIS un
# ancien rendu apres une correction. Constat de Laurent, 17/09/2026 : « quand je
# reprends une lecture, j'ai l'ancien defaut sur quelques lignes, puis j'entends
# les mises a jour » -- c'etaient les phrases dont le texte n'avait pas change,
# servies depuis le cache d'avant.
#   1 = avant le 17/09/2026 au soir (point-virgule et parentheses non traites,
#       pas de contexte glissant)
#   2 = 17/09/2026 au soir : `;` -> `,`, `()` -> virgules, ` : ` -> `, `,
#       et contexte glissant entre phrases du meme locuteur
VERSION_CACHE = 2


def _hash_key(text, voice, rate, pitch):
    """Cle de cache : hash de la VERSION, des parametres reels de la synthese."""
    h = hashlib.sha256()
    h.update(("v%d" % VERSION_CACHE).encode("utf-8"))
    h.update(b"\x00")
    h.update(text.encode("utf-8"))
    h.update(b"\x00")
    h.update(voice.encode("utf-8"))
    h.update(b"\x00")
    h.update(rate.encode("utf-8"))
    h.update(b"\x00")
    h.update(pitch.encode("utf-8"))
    return h.hexdigest()


def _dir_size():
    total = 0
    try:
        for p in CACHE_DIR.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
    except OSError:
        pass
    return total


def _purge_if_needed():
    """Supprime les fichiers les plus anciens quand le quota est depasse."""
    global _known_total, _written_since_purge
    if _known_total is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _known_total = _dir_size()
    if _known_total + _written_since_purge <= CACHE_MAX_BYTES:
        return
    try:
        files = [
            (p, p.stat().st_mtime, p.stat().st_size)
            for p in CACHE_DIR.glob("*")
            if p.is_file()
        ]
    except OSError:
        return
    files.sort(key=lambda x: x[1])  # plus ancien d'abord
    total = sum(sz for _, _, sz in files)
    for p, _, sz in files:
        if total <= PURGE_TARGET_BYTES:
            break
        try:
            p.unlink()
            total -= sz
        except OSError:
            pass
    _known_total = total
    _written_since_purge = 0


def get_audio(text, voice, rate, pitch, ext):
    """Renvoie les octets audio en cache, ou None si absent / illisible."""
    path = CACHE_DIR / f"{_hash_key(text, voice, rate, pitch)}.{ext}"
    try:
        if path.is_file():
            return path.read_bytes()
    except OSError:
        pass
    return None


def put_audio(text, voice, rate, pitch, ext, data):
    """Ecrit l'audio dans le cache (ecriture atomique, purge si quota plein)."""
    global _written_since_purge
    if not data:
        return
    key = _hash_key(text, voice, rate, pitch)
    with _lock:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _purge_if_needed()
        tmp = CACHE_DIR / f".{key}.{ext}.tmp"
        final = CACHE_DIR / f"{key}.{ext}"
        try:
            tmp.write_bytes(data)
            os.replace(tmp, final)  # atomique : jamais de fichier incomplet
            _written_since_purge += len(data)
        except OSError:
            try:
                tmp.unlink()
            except OSError:
                pass
