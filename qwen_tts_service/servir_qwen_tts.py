# -*- coding: utf-8 -*-
"""
Appareil de voix Qwen3-TTS -- service local pour NIMM ePub.

Ce programme charge UNE FOIS le moteur Qwen3-TTS (0,6 B, ~3,8 Go sur la
carte graphique) puis repond a quatre questions, en HTTP, sur le reseau local :

    GET  /sante      -> le moteur est-il pret ? (et quelles infos GPU)
    GET  /voix       -> la liste des voix disponibles
    POST /tts        -> {"texte": "...", "voix": "..."} -> fichier WAV
    POST /recharger  -> re-scanne le dossier des voix (sans recharger le moteur)

Il vivote A COTE du lecteur, dans son propre environnement Python 3.12
(NIMM ePub tourne sur Python 3.14 et ne peut pas heberger PyTorch).
Le lecteur l'appelle donc par le reseau, comme il appelle deja Edge TTS.

CE QUI DIFFERE DU SERVICE KYUTAI (les deux freres, mais pas des jumeaux) :
  1. Qwen a besoin de DEUX choses par voix : l'extrait (WAV) ET LE TEXTE
     EXACT dit dans l'extrait. Kyutai se contente de l'empreinte de 256 Ko
     fournie toute prete. Les textes sont donc lus dans le `references.csv`
     du dossier des voix, a cote des WAV.
  2. Qwen ne fournit AUCUNE empreinte pre-calculee : l'empreinte d'une voix
     se calcule ici, a la premiere demande, puis reste en memoire
     (`create_voice_clone_prompt`, 0,7 a 1,4 s mesure chez NIMM Voix le
     26/09/2026). C'est ce qui evite de recalculer la reference a chaque
     phrase -- le mode d'emploi de Qwen le recommande explicitement.
  3. Qwen rend PARFOIS une phrase VIDE (0,36 s de silence, 2 a 5 % selon la
     voix, mesure NIMM Voix). Le service RELANCE donc la phrase, jusqu'a
     NIMM_QWEN_REPRISES fois (2 par defaut). Sans cela, on entendrait un
     blanc au milieu d'un chapitre.
  4. Pas de streaming dans la bibliotheque installee (qwen-tts 0.1.1) :
     l'audio sort d'un bloc, d'ou 2 a 4 s avant le premier son d'un chapitre.
     C'est le lecteur qui prend de l'avance (son prechargement), pas le moteur.
  5. Le « contexte glissant » du service Kyutai (fin de la phrase precedente)
     n'a PAS d'equivalent ici : la cle est acceptee puis ignoree, et le
     service le dit une fois dans sa fenetre. A ecouter avant de le promettre.

Lancement : DEMARRER_QWEN_TTS.bat
Reglages (variables d'environnement, valeurs par defaut entre parentheses) :
    NIMM_QWEN_PORT       (8086)     port d'ecoute
    NIMM_QWEN_HOST       (127.0.0.1) adresse d'ecoute (locale par defaut)
    NIMM_QWEN_MODELE     (Qwen/Qwen3-TTS-12Hz-0.6B-Base)
    NIMM_QWEN_LANGUE     (French)
    NIMM_QWEN_REPRISES   (2)        reprises en cas de phrase vide
    NIMM_QWEN_SURVEILLER_CONSOLE (0) force le gardien de fenetre (essais)
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

sys.stdout.reconfigure(encoding='utf-8')

# Le stockage « xet » de Hugging Face a deja bloque un telechargement le
# 11/09/2026 : on le desactive preventivement (meme precaution que Kyutai).
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

# ==============================================================
# CHEMINS ET REGLAGES
# ==============================================================

ICI = Path(__file__).resolve().parent
# Les 35 extraits francais sont ranges ICI (copie pris aupres de l'atelier
# NIMM Voix le 26/09/2026, meme source que les empreintes Kyutai) : le
# service ne depend ainsi d'aucun autre dossier.
DOSSIER_VOIX = ICI / "voix"
FICHIER_TEXTES = DOSSIER_VOIX / "references.csv"

# Suffixe des fichiers de reference : `10087_...-0002_enhanced_reference.wav`
# -> identifiant de voix `10087_...-0002` (exactement les identifiants du
# catalogue Kyutai, d'ou une bascule de livre sans rien renommer).
SUFFIXE_FICHIER = "_enhanced_reference.wav"

REPO_MODELE = os.environ.get(
    "NIMM_QWEN_MODELE", "Qwen/Qwen3-TTS-12Hz-0.6B-Base") or \
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
HOTE = os.environ.get("NIMM_QWEN_HOST", "127.0.0.1")
PORT = int(os.environ.get("NIMM_QWEN_PORT", "8086") or "8086")
LANGUE = os.environ.get("NIMM_QWEN_LANGUE", "French") or "French"
REPRISES = int(os.environ.get("NIMM_QWEN_REPRISES", "2") or "2")

# Seuil du « silence numerique » : une phrase vide rend 0,36 s de silence pur
# (mesure NIMM Voix), soit une amplitude nulle. Une VRAIE phrase courte
# (« Non. ») depasse ce seuil, meme brievement : on regarde donc le PIC, pas
# la duree (un « Non. » de 0,4 s ne doit pas etre pris pour un ratage).
SEUIL_SILENCE = 0.01

# Methode d'ATTENTION du modele. Vide = ce que la bibliotheque choisit
# elle-meme -- et sans `flash-attn` installe (impossible a compiler sous
# Windows sans Visual Studio + plusieurs Go), elle prend une version
# « manuelle » de PyTorch, LENTE. « sdpa » demande l'attention integree de
# PyTorch (memes noyaux rapides, sans rien compiler) : c'est un levier de
# vitesse a mesurer, pas une croyance -- voir la mesure du 26/09/2026.
ATTENTION = os.environ.get("NIMM_QWEN_ATTENTION", "") or ""

# Nombre de generations SIMULTANEES autorisees (1 = une a la fois, comme
# Kyutai). Pourquoi ce reglage existe : mesure du 26/09/2026 -- pendant une
# generation, la carte graphique n'est utilisee qu'a 27 %, donc l'attente est
# dans la BOUCLE du modele, pas dans la carte. Deux generations de front
# pourraient donc presque doubler le debit. C'est une MESURE a faire, pas une
# croyance ; le lecteur, lui, envoie deja deux requetes de front (son
# prechargement). Reglage : NIMM_QWEN_PARALLELE (defaut 1 = comportement sur).
PARALLELE = max(1, int(os.environ.get("NIMM_QWEN_PARALLELE", "1") or "1"))
_verrou = threading.Semaphore(PARALLELE)

_modele = None                   # le moteur, charge une seule fois
_empreintes = {}                 # identifiant de voix -> empreinte de clonage
_voix_cache = {}                 # identifiant de voix -> (chemin WAV, texte)
_infos = {"pret": False, "moteur": REPO_MODELE, "appareil": "", "voix": 0,
          "langue": LANGUE, "reprises": REPRISES, "parallele": PARALLELE,
          "charge_en": 0.0}
_contexte_signale = False        # le contexte ignore est signale UNE fois


# ==============================================================
# LES VOIX : UN EXTRAIT + LE TEXTE EXACT QUI Y EST DIT
# ==============================================================

def _lire_textes():
    """{nom de fichier: texte} depuis `references.csv` (colonnes separees
    par des points-virgules : fichier;texte;duree;hauteur;source).

    Le texte est OBLIGATOIRE pour Qwen : sans lui, la bibliotheque clone
    quand meme (`x_vector_only_mode`), mais la qualite baisse nettement
    (constat de l'atelier NIMM Voix, 26/09/2026).
    """
    textes = {}
    if not FICHIER_TEXTES.exists():
        return textes
    with open(FICHIER_TEXTES, encoding="utf-8-sig") as fichier:
        lignes = [l for l in fichier.read().splitlines() if l.strip()]
    for ligne in lignes[1:]:                       # la 1re ligne = entetes
        morceaux = ligne.split(";")
        if len(morceaux) > 1 and morceaux[0].strip():
            textes[morceaux[0].strip()] = morceaux[1].strip()
    return textes


def _repertorier_voix():
    """Re-scanne le dossier des voix : identifiant -> (WAV, texte de reference).

    L'identifiant est le nom du fichier sans son suffixe, exactement comme
    dans le catalogue du lecteur (`10087_11650_000028-0002`). Une voix SANS
    texte est ANNONCEE mais ecartee : mieux vaut la voir manquer que de
    l'entendre clonee de travers.
    """
    global _voix_cache
    textes = _lire_textes()
    trouvees = {}
    manquants = []
    if DOSSIER_VOIX.is_dir():
        for fichier in sorted(DOSSIER_VOIX.glob("*.wav")):
            identifiant = fichier.name
            if identifiant.endswith(SUFFIXE_FICHIER):
                identifiant = identifiant[:-len(SUFFIXE_FICHIER)]
            texte = textes.get(fichier.name, "")
            if not texte:
                manquants.append(fichier.name)
                continue
            trouvees[identifiant] = (fichier, texte)
    _voix_cache = trouvees
    if manquants:
        print("ATTENTION : %d extrait(s) sans texte dans %s -- ignores :"
              % (len(manquants), FICHIER_TEXTES.name), flush=True)
        for nom in manquants[:5]:
            print("    %s" % nom, flush=True)
    return trouvees


# ==============================================================
# CHARGEMENT DU MOTEUR (une seule fois, au demarrage)
# ==============================================================

def charger_moteur():
    """Charge Qwen3-TTS en memoire vive (carte graphique).

    Appele au demarrage du service : le chargement prend quelques secondes
    (4,3 a 5,8 s mesure chez NIMM Voix le 26/09/2026), puis chaque phrase est
    generee sans rien recharger.
    """
    global _modele

    import torch
    from qwen_tts import Qwen3TTSModel

    _repertorier_voix()
    if not _voix_cache:
        print("ARRET : aucune voix exploitable dans %s" % DOSSIER_VOIX)
        print("(il faut un .wav ET sa ligne dans %s)" % FICHIER_TEXTES.name)
        sys.exit(1)

    if torch.cuda.is_available():
        parametres = {"device_map": "cuda:0", "dtype": torch.bfloat16}
        nom_appareil = "cuda : %s" % torch.cuda.get_device_name(0)
    else:
        parametres = {"device_map": "cpu"}
        nom_appareil = "cpu (aucune carte graphique detectee : ce sera lent)"

    if ATTENTION:
        parametres["attn_implementation"] = ATTENTION
        print("Attention demandee : %s" % ATTENTION, flush=True)

    print("Chargement du moteur Qwen3-TTS (%s)..." % nom_appareil, flush=True)
    t0 = time.time()
    _modele = Qwen3TTSModel.from_pretrained(REPO_MODELE, **parametres)

    _infos["appareil"] = nom_appareil
    _infos["voix"] = len(_voix_cache)
    _infos["charge_en"] = round(time.time() - t0, 1)
    if torch.cuda.is_available():
        _infos["memoire_go"] = round(
            torch.cuda.max_memory_allocated() / (1024 ** 3), 2)
    _infos["pret"] = True
    print("Moteur pret en %.1f s -- %d voix disponibles."
          % (_infos["charge_en"], len(_voix_cache)), flush=True)


# ==============================================================
# LA GENERATION D'UNE PHRASE
# ==============================================================

def _en_numpy(sons):
    """Convertit l'audio du moteur en tableau numpy 1D (tenseur ou tableau)."""
    import numpy as np
    if hasattr(sons, "detach"):
        return sons.detach().cpu().float().numpy().reshape(-1).astype(np.float32)
    return np.asarray(sons, dtype=np.float32).reshape(-1)


def _wav_depuis_pcm(sons, frequence):
    """Convertit l'audio du moteur (nombres flottants) en fichier WAV
    16 bits mono -- meme format que Kokoro, Piper et Kyutai."""
    import numpy as np
    donnees = np.clip(_en_numpy(sons), -1.0, 1.0)
    donnees = (donnees * 32767.0).astype("<i2")

    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(frequence))
        fichier.writeframes(donnees.tobytes())
    return tampon.getvalue()


def _est_vide(sons):
    """Vrai si la generation est un SILENCE (le defaut connu de Qwen).

    Mesure NIMM Voix (26/09/2026) : la phrase vide fait 0,36 s de silence
    pur. On regarde donc le PIC d'amplitude, jamais la duree : une vraie
    phrase courte (« Non. ») passe sans etre prise pour un ratage.
    """
    import numpy as np
    if sons.size == 0:
        return True
    return float(np.max(np.abs(sons))) < SEUIL_SILENCE


def _empreinte(identifiant):
    """L'empreinte de clonage d'une voix -- calculee UNE fois, puis gardee.

    C'est l'equivalent des empreintes de 256 Ko de Kyutai : Qwen, lui, ne
    les fournit pas, il faut les calculer (0,7 a 1,4 s mesures). L'appelant
    doit tenir le VERROU (l'appel au moteur n'est pas « thread-safe »).
    """
    if identifiant not in _empreintes:
        chemin, texte = _voix_cache[identifiant]
        t0 = time.time()
        _empreintes[identifiant] = _modele.create_voice_clone_prompt(
            ref_audio=str(chemin),
            ref_text=texte,
            x_vector_only_mode=False,
        )
        print("  empreinte de la voix %s preparee en %.1f s"
              % (identifiant, time.time() - t0), flush=True)
    return _empreintes[identifiant]


def generer_wav(texte, identifiant_voix):
    """Genere une phrase avec une voix. Renvoie (octets WAV, duree audio).

    Leve une exception si la voix est inconnue ou si la generation echoue :
    l'appelant (le service) transforme cela en message clair.
    """
    if _modele is None:
        raise RuntimeError("le moteur n'est pas encore charge")

    if identifiant_voix not in _voix_cache:
        raise ValueError("voix inconnue : %s" % identifiant_voix)

    with _verrou:
        empreinte = _empreinte(identifiant_voix)
        sons, frequence = None, 24000
        for essai in range(REPRISES + 1):
            resultat = _modele.generate_voice_clone(
                text=texte,
                language=LANGUE,
                voice_clone_prompt=empreinte,
            )
            sons = _en_numpy(resultat[0][0])
            frequence = int(resultat[1])
            if not _est_vide(sons):
                if essai:
                    print("  phrase relancee apres %d essai(s) vide(s)" % essai,
                          flush=True)
                break
            print("  phrase VIDE (silence) -- reprise %d/%d"
                  % (essai + 1, REPRISES), flush=True)

    duree = len(sons) / float(frequence) if frequence else 0.0
    return _wav_depuis_pcm(sons, frequence), duree


# ==============================================================
# LE SERVICE HTTP (bibliotheque standard uniquement : rien a installer
# en plus de PyTorch et qwen-tts)
# ==============================================================

# Taille maximale acceptee pour une phrase (securite : le lecteur envoie
# toujours une phrase courte, mais on ne laisse pas un texte enorme occuper
# la carte graphique pendant des minutes).
TEXTE_MAX = 5000


class Repondeur(BaseHTTPRequestHandler):
    server_version = "NIMMQwen/1.0"

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
        brut = self.rfile.read(taille)
        return json.loads(brut.decode("utf-8"))

    # --- routes ---------------------------------------------------

    def do_GET(self):
        if self.path.split("?")[0] == "/sante":
            self._envoyer_json(200, dict(_infos))
        elif self.path.split("?")[0] == "/voix":
            self._envoyer_json(200, {
                "voix": sorted(_voix_cache.keys()),
                "nombre": len(_voix_cache),
            })
        else:
            self._envoyer_json(404, {"erreur": "adresse inconnue"})

    def do_POST(self):
        if self.path.split("?")[0] == "/recharger":
            # Re-scanne le dossier des voix SANS recharger le moteur : permet
            # d'ajouter une voix sans redemarrer le service.
            _repertorier_voix()
            print("voix rechargees : %d" % len(_voix_cache), flush=True)
            self._envoyer_json(200, {"voix": len(_voix_cache),
                                     "liste": sorted(_voix_cache.keys())})
            return

        if self.path.split("?")[0] != "/tts":
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

        # Le « contexte glissant » du service Kyutai (fin de la phrase
        # precedente) n'a pas d'equivalent chez Qwen : on l'IGNORE, mais on
        # le DIT une fois dans la fenetre -- un silence ferait croire que le
        # reglage fonctionne encore.
        global _contexte_signale
        if demande.get("contexte") and not _contexte_signale:
            _contexte_signale = True
            print("NOTE : « contexte » recu et ignore -- Qwen3-TTS n'a pas ce "
                  "reglage (volet 5 de l'en-tete).", flush=True)

        t0 = time.time()
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

        calcul = time.time() - t0
        # Le RAPPORT AU TEMPS REEL est la mesure qui dit si le moteur tient
        # sur un chapitre (> 1 = plus vite qu'on ne lit).
        rapport = (duree / calcul) if calcul else 0.0
        print("phrase generee  voix=%-28s  %5.1f s de calcul  %5.1f s d'audio"
              "  x%.2f le temps reel" % (voix, calcul, duree, rapport),
              flush=True)
        self._envoyer(200, wav, "audio/wav")

    # --- journal lisible ------------------------------------------

    def log_message(self, format, *args):
        """Une ligne courte par appel, lisible dans la fenetre du moteur.

        Les interrogations `GET /sante` ne sont PAS affichees : c'est le
        voyant du lecteur, qui demande toutes les 5 secondes si le moteur est
        pret -- cela remplirait la fenetre sans rien apprendre (meme regle
        que Kyutai, XTTS et Pocket).
        """
        ligne = format % args
        if "/sante" in ligne:
            return
        sys.stderr.write("  %s\n" % ligne)


class ServiceQwen(ThreadingHTTPServer):
    """Un seul moteur, un seul port : on refuse le partage d'adresse.

    Sans cela, un second lancement pourrait s'accrocher au port deja tenu et
    lancer un SECOND moteur (2 x 3,8 Go de carte graphique).
    """

    allow_reuse_address = False


def _surveiller_la_console():
    """Eteint le moteur si sa fenetre disparait (fenetre ou onglet ferme).

    Pourquoi : sous Windows, un programme qui n'ecrit jamais dans sa console
    ne s'apercoit pas que celle-ci a ete fermee -- le moteur continuerait
    alors de tourner (port occupe, 3,8 Go de carte graphique) alors que
    Laurent croit l'avoir eteint (constate le 12/09/2026 sur Kyutai). Ce
    gardien rend le geste naturel -- fermer la fenetre -- vraiment efficace.

    Principe : tant que la fenetre existe, la lecture du clavier reste en
    attente (personne ne tape dans cette fenetre). Des que la fenetre est
    fermee, la lecture revient immediatement avec une chaine VIDE (fin de
    flux) : c'est le signal.

    Le gardien ne s'active que si le moteur tourne dans une VRAIE console
    (fenetre) : lance sans console (outils, tests, stdin redirige), il ne
    s'active pas. NIMM_QWEN_SURVEILLER_CONSOLE=1 force l'activation.
    """
    force = os.environ.get("NIMM_QWEN_SURVEILLER_CONSOLE", "") == "1"
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
            print("Fenetre fermee : arret du moteur de voix Qwen3-TTS.")
            sys.stdout.flush()
            os._exit(0)
        # une touche a ete frappee : on n'arrete rien, on continue a veiller


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
    print("===== NIMM ePub : appareil de voix Qwen3-TTS =====")
    print("Modele : %s" % REPO_MODELE)
    print("")

    if _moteur_deja_en_route():
        print("ARRET : un moteur de voix Qwen tourne deja sur %s:%d."
              % (HOTE, PORT))
        print("Rien a faire : la fenetre deja ouverte suffit.")
        sys.exit(1)

    # Le port est ouvert AVANT le chargement du modele -- celui-ci prend
    # quelques secondes. Deux consequences voulues :
    #   1. START.bat voit tout de suite que le moteur est en route, et ne
    #      lance donc JAMAIS un second moteur (deux moteurs occuperaient
    #      2 x 3,8 Go de carte graphique) ;
    #   2. pendant le chargement, /sante repond « pret : false » et /tts
    #      repond « moteur en cours de chargement » -- message clair plutot
    #      qu'une erreur de connexion.
    try:
        service = ServiceQwen((HOTE, PORT), Repondeur)
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
            print("ECHEC du chargement du moteur : %s" % erreur, flush=True)
        if not _infos["pret"]:
            # Inutile de laisser un service ouvert sans moteur : on s'arrete.
            # Le lecteur, lui, continue de fonctionner normalement.
            print("Le service s'arrete : le moteur n'a pas pu etre charge.")
            os._exit(1)
        print("Le moteur est pret : les phrases peuvent etre demandees.",
              flush=True)

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
