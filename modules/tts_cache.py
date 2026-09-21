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
#   3 = 17/09/2026, fin de soiree : respiration de fin de phrase retiree cote
#       Kyutai (-100 ms) et pause entre paragraphes ramenee a 300 ms
#   4 = 18/09/2026 : point d'exclamation retire du texte envoye au moteur,
#       point final supprime apres une abreviation (M. -> Monsieur), et niveau
#       de parole des voix Kyutai ramene a celui des autres moteurs
#   5 = 18/09/2026 au soir (banc d'ecoute) : le « ! » devient une VIRGULE dans
#       les phrases courtes (interjections) et reste un POINT dans les phrases
#       entieres ; les INCISES de parole (« , dit-il, ») sont retirees du texte
#       parle (le texte affiche ne change pas)
#   6 = 18/09/2026, plus tard dans la soiree : la regle des incises apprend le
#       « t » euphonique (« ajouta-t-il », « demanda-t-elle »), les PARTICULES
#       nobles (« , dit M. de Villefort, », tres frequentes) et les noms communs
#       avec article (« , dit le comte, ») -- sans cette version, les phrases
#       deja en cache servaient l'ANCIEN rendu et les incises semblaient
#       toujours la (constat de Laurent : « elles sont toujours presentes »)
#   7 = 18/09/2026, fin de soiree : les verbes PRONOMINAUX (« , se demanda-t-elle, »)
#       et les imparfaits (« , disait-il, »), remarque de Laurent -- et le retrait
#       passe AVANT les conversions de ponctuation, sinon de fausses incises
#       etaient fabriquees (« ; » et « : » devenaient des virgules)
#   8 = 18/09/2026, dernier tour de la soiree : les incises sont retirees EN
#       ENTIER, complement compris (« , dit-il au comte, », « , fit celui-ci
#       avec sa voix demi-railleuse, »), et l'incise qui OUVRE une phrase est
#       reconnue (le decoupage coupe au « ! », l'incise n'est plus entre deux
#       virgules). Exemples donnes par Laurent, tous deux corriges.
#   9 = 18/09/2026, toute fin de soiree : la RELATIVE qui suit l'incise part avec
#       elle (« , dit Cavalcanti, qui se grisait a ce bruit metallique… ») ;
#       « que » reste volontairement dehors (conjonction : « Le fait est que… ») ;
#       et une phrase qui n'est QUE l'incise reçoit un court silence
#       (`modules/silence.py`, 150 ms) au lieu d'etre lue.
#  10 = 18/09/2026, derniers cas tordus signales par Laurent : la RELATIVE
#       COORDONNEE (« , dit Monte-Cristo, qui sentit…, et qui comprit… ; ») part
#       avec l'incise jusqu'au point-virgule, et une QUESTION du personnage en fin
#       de phrase ne bloque plus l'extension (le « ? » etait regarde trop loin).
#  11 = 19/09/2026 : le POINT-VIRGULE ferme desormais une incise de parole
#       (« , dit le comte ; aussi je tiens a le constater. ») : il separe deux
#       propositions, c'est une frontiere sure. La ponctuation ORPHELINE laissee
#       en tete de phrase par ce retrait (31 phrases du tome 5) est nettoyee.
#       Mesure avant de decider : 67 phrases touchees dans le tome 5, aucune ne
#       perd tout son texte. Sans cet increment, les phrases deja en cache
#       serviraient l'ANCIEN rendu et l'incise semblerait toujours lue.
#  12 = 19/09/2026 : le GESTE qui suit une incise FERMEE part desormais avec
#       elle (« , dit Morrel, se levant. » ne laisse plus « se levant. »
#       orphelin, ce qui violait le garde-fou « jamais de mot orphelin »). Cas
#       trouve par le TEST ADVERSE (Claude.AI, cas C1) : 2 phrases dans le
#       tome 5. Les faux participes (maintenant, pendant, pourtant) et les
#       groupes qui parlent de la replique (« avec vous ») sont preserves.
#  13 = 19/09/2026, meme soiree : une ENUMERATION de gestes part desormais EN
#       ENTIER (« , dit Beauchamp, avec un col, avec un habit, avec un gilet
#       blanc... »). Sans cela, seul le premier morceau partait et le texte
#       restait bancal (« voyez avec un habit ouvert... ») -- constate a
#       l'oreille, chapitre 90 du tome 5.
#  14 = 19/09/2026 : les mots TOUT EN MAJUSCULES qui sont des mots du livre sont
#       remis en casse normale avant l'envoi au moteur (« c'est LUI » ne sonne
#       plus comme un sigle). Les vrais sigles (« JFK », « FBI ») restent
#       intacts. Le vocabulaire du livre est appris une fois (main.py).
#  15 = 21/09/2026 : PRONONCIATION FRANCAISE IMPOSEE. Kokoro recoit desormais
#       les PHONEMES au lieu du texte, sans les marques de langue d'espeak-ng
#       (« (en)ˈandɹiə(fr) » etaient PRONONCEES : « énAndréa fe »), et les mots
#       que le phonemiseur prend pour de l'anglais sont reecrits pour la lecture
#       (`modules/prononciation.py`, Kokoro ET Piper). Les phrases deja
#       ecoutees doivent donc etre refaites : sans ce numero, le cache
#       resservirait l'ancien defaut -- c'est la lecon du 17/09/2026.
#  16 = 21/09/2026 : NIVEAU DES PHRASES DANS LES DEUX SENS. `modules/audio_gain.py`
#       ne fait plus que REMONTER les phrases faibles : il ramene aussi les
#       phrases TROP FORTES vers la cible (jamais plus de -6 dB, pour ne rien
#       ecraser), afin qu'aucune phrase ne « decroche » a cote de ses voisines
#       (mesure : de 7,5 a 12,8 % chez Pocket, 3,6 dB d'ecart apres l'ancienne
#       regle). Meme raison que les fois precedentes : une phrase deja en cache
#       porte l'ancien niveau.
#  17 = 21/09/2026, meme jour : le cache est purge une seconde fois parce que la
#       mise au point a change la regle en cours de route (une bande de +/- 3 dB
#       avait ete essayee, puis abandonnee -- elle laissait 3,7 dB d'ecart, soit
#       le defaut lui-meme). Aucun fichier livre ne portait cette version : c'est
#       un nettoyage de l'essai, pas un nouveau reglage.
VERSION_CACHE = 17


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


def stats() -> dict:
    """Etat du cache disque : octets utilises, quota, nombre de fichiers.

    Sert au bouton « Vider le cache audio » du lecteur, qui affiche le compte
    (« Vider le cache (604 Mo) »). LECTURE SEULE : rien n'est modifie.
    """
    octets = 0
    fichiers = 0
    try:
        for p in CACHE_DIR.rglob("*"):
            if p.is_file():
                fichiers += 1
                octets += p.stat().st_size
    except OSError:
        pass
    return {
        "octets": octets,
        "quota_octets": CACHE_MAX_BYTES,
        "fichiers": fichiers,
        "version": VERSION_CACHE,
    }


def purger() -> dict:
    """Vide le cache audio et renvoie ce qui a ete libere.

    Pourquoi c'est sans danger : le cache est REGENERABLE par nature -- c'est de
    l'audio deja synthetise, et le moteur le refera a l'identique (la synthese
    est deterministe). Le vider ne fait donc perdre qu'une chose : la premiere
    ecoute d'un passage deja lu redemandera le calcul au moteur.

    Demande de Laurent (18/09/2026) : le cache se purge seul par quota, mais il
    n'avait aucun moyen de le vider a la main -- exactement ce qui manque quand
    on doute d'un rendu.

    Les fichiers `.tmp` (une ecriture en cours) sont laisses de cote : on ne
    coupe jamais une synthese en train de s'ecrire.
    """
    global _known_total, _written_since_purge
    liberes = 0
    supprimes = 0
    with _lock:
        try:
            fichiers = [p for p in CACHE_DIR.glob("*")
                        if p.is_file() and not p.name.endswith(".tmp")]
        except OSError:
            fichiers = []
        for p in fichiers:
            try:
                taille = p.stat().st_size
                p.unlink()
                liberes += taille
                supprimes += 1
            except OSError:
                pass
        _known_total = _dir_size()
        _written_since_purge = 0
    return {"ok": True, "fichiers_supprimes": supprimes, "octets_liberes": liberes}


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
