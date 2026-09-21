# -*- coding: utf-8 -*-
"""Le service de voix Pocket TTS de NIMM ePub (port 8085).

Modele Kyutai Pocket TTS, langue FRANCAISE (`french_24l`), qui tourne sur le
PROCESSEUR (pas de carte graphique : Kyutai, ses auteurs, ont mesure qu'il n'y
gagne rien, et la carte est deja prise par Kyutai 1.6B). Une voix = un extrait
de reference (`voix\\<nom>_reference.wav`) : le moteur l'encode une fois (3,8 s
mesure) et garde le resultat en memoire.

Contrat IDENTIQUE aux autres moteurs de la maison -- le lecteur ne voit pas la
difference (`modules/tts.py` appelle les quatre de la meme facon) :
    GET  /sante      -> {"pret": true/false, ...}   (c'est ce que teste le lecteur)
    GET  /voix       -> {"voix": [...], "nombre": n}
    POST /tts        {"texte": ..., "voix": ...}  -> WAV brut (audio/wav)
    POST /recharger  -> relit le dossier des voix, sans redemarrer

Reglages (variables d'environnement, valeurs par defaut entre parentheses) :
    NIMM_POCKET_TTS_PORT    (8085)    port d'ecoute
    NIMM_POCKET_TTS_HOST    (127.0.0.1)  cette machine seulement
    NIMM_POCKET_TTS_COEURS  (4)       coeurs laisses au moteur ; les 2 autres
                                      restent au lecteur, a Kokoro et a Piper
                                      (mesure du 20/09/2026 : brider a 4 ne
                                      coute RIEN en vitesse)
    NIMM_POCKET_TTS_TOKENS  (200)     taille des morceaux (recette de l'atelier)

UNE SEULE GENERATION A LA FOIS : le modele n'est pas thread-safe (c'est ecrit
dans son propre code) et il occupe deja plusieurs coeurs. Les requetes font la
queue -- c'est aussi ce qui evite d'entendre deux phrases se melanger.
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
DOSSIER_VOIX = ICI / "voix"
# Le fichier qui dit « Pocket TTS a ete eteint VOLONTAIREMENT » : ecrit quand la
# FENETRE du moteur se ferme, il est lu par le veilleur du lecteur (`main.py`).
# Sans lui, le veilleur rallumait le moteur 30 secondes plus tard, et le geste
# naturel de Laurent -- fermer la fenetre pour l'eteindre -- ne servait a rien
# (constat du 21/09/2026 : « Pocket TTS reste allume, je n'ai pas moyen de
# l'eteindre »). Il est efface des que le moteur redemarre.
MARQUEUR_ARRET = ICI / "arrete_volontaire.txt"

PORT = int(os.environ.get("NIMM_POCKET_TTS_PORT", "8085") or "8085")
HOTE = os.environ.get("NIMM_POCKET_TTS_HOST", "127.0.0.1") or "127.0.0.1"
COEURS = int(os.environ.get("NIMM_POCKET_TTS_COEURS", "4") or "4")
TOKENS = int(os.environ.get("NIMM_POCKET_TTS_TOKENS", "200") or "200")
LANGUE = "french_24l"

# Le lecteur n'envoie plus de tres longues phrases (il decoupe a ~500
# caracteres), mais on garde un plafond : au-dela, le moteur saute du texte.
TEXTE_MAX = 1200

# GARDE-FOU CONTRE LE « TIC » (voir generer_wav) : en dessous de 5 % de la
# pleine echelle, la prise est un quasi-silence -- on regenere. Apres
# ESSAIS_MAX tentatives, on garde le meilleur essai plutot que d'echouer.
NIVEAU_MINI = 0.05
ESSAIS_MAX = 4

# AUTO-EXTINCTION : le service tourne SANS fenetre (lance par START.bat), donc
# rien ne rappelle a Laurent qu'il est la. Sans ce garde-fou il resterait
# allume indefiniment, avec ~2,3 Go de memoire pris pour rien. Apres ce nombre
# de minutes SANS UNE SEULE PHRASE demandee, il s'arrete de lui-meme.
#
# 30 min -> 3 h le 21/09/2026 : a 30 min, le moteur s'endormait EN PLEINE
# JOURNEE d'ecoute (constat de Laurent : « j'ai ecoute une voix Pocket TTS, puis
# le moteur s'est eteint, et la voix a disparu du casting »). Le lecteur sait
# maintenant le rallumer tout seul (voir le veilleur, main.py), mais autant
# qu'il n'ait pas a le faire : la memoire n'est liberee que si le lecteur reste
# ouvert sans qu'on ecoute pendant 3 h.
# 0 = jamais (utile pour les essais et les mesures).
INACTIF_MIN = int(os.environ.get("NIMM_POCKET_TTS_INACTIF", "180") or "180")

DERNIERE_ACTIVITE = time.time()   # mise a jour a chaque phrase demandee

# Etat du service, lu par /sante et par le lecteur.
_infos = {
    "pret": False,          # le modele est charge : les voix peuvent etre lues
    "modele": LANGUE,
    "langue": LANGUE,
    "coeurs": COEURS,
    "voix": 0,
    "erreur": "",
    "version": "PocketTTS/1.0",
}

_modele = None                      # le modele, charge une fois
_voix_cache = {}                    # nom de voix -> etat encode (3,8 s la 1re fois)
_verrou_generation = threading.Lock()   # une seule generation a la fois


# ============================================================
# LE TEXTE : petit nettoyage de securite, PROPRE a Pocket TTS
# ============================================================
# Le lecteur envoie deja un texte nettoye (abreviations, incises...), mais
# Pocket TTS a ses exigences a lui, mesurees par l'atelier : l'apostrophe
# courbe et le tiret cadratin NE SONT PAS dans son vocabulaire (on entendait
# « de d'habitude », « e gree »), et il connait `...` mais pas `…` -- soit
# l'inverse du memo XTTS/NeuTTS. On repare donc aussi ICI : un service doit
# rester juste meme s'il est appele directement.
REMPLACEMENTS = (
    ("\u2019", "'"),      # apostrophe courbe
    ("\u2018", "'"),
    ("\u201c", '"'),
    ("\u201d", '"'),
    ("\u2014", "-"),      # tiret cadratin
    ("\u2013", "-"),      # tiret demi-cadratin
    ("\u2026", "..."),    # il connait "..." mais pas "…"
    ("\u00a0", " "),      # espace insecable
    ("\t", " "),
)


def nettoyer_texte(texte: str) -> str:
    """Rend le texte lisible par Pocket TTS (voir REMPLACEMENTS)."""
    for avant, apres in REMPLACEMENTS:
        texte = texte.replace(avant, apres)
    return " ".join(texte.split()).strip()


# ============================================================
# LE MODELE ET LES VOIX
# ============================================================

def charger_modele():
    """Charge le modele francais (1,7 s mesure : il est en cache disque)."""
    global _modele
    import torch

    # On BRIDE le moteur : les coeurs laisses libres servent au lecteur, a
    # Kokoro et a Piper. Mesure du 20/09/2026 : brider a 4 ne coute rien.
    torch.set_num_threads(COEURS)

    from pocket_tts import TTSModel

    debut = time.time()
    _modele = TTSModel.load_model(language=LANGUE)
    print("modele %s charge en %.1f s (%d coeurs)"
          % (LANGUE, time.time() - debut, COEURS))
    repertorier_voix()
    _infos["pret"] = True


def repertorier_voix():
    """Liste les voix du dossier `voix\\` : un fichier = une voix.

    L'identifiant d'une voix est son nom de fichier SANS `_reference` :
    `Femme001_reference.wav` -> voix `Femme001`. C'est cet identifiant qui
    voyage dans le catalogue du lecteur (`pocket:Femme001`).
    """
    _voix_cache.clear()
    if DOSSIER_VOIX.is_dir():
        for fichier in sorted(DOSSIER_VOIX.glob("*_reference.wav")):
            _voix_cache[fichier.name[:-len("_reference.wav")]] = None
    _infos["voix"] = len(_voix_cache)
    return len(_voix_cache)


def _fichier_de_voix(nom: str):
    """Le WAV de reference d'une voix, ou None."""
    for candidat in (nom + "_reference.wav", nom + ".wav", nom):
        chemin = DOSSIER_VOIX / candidat
        if chemin.is_file():
            return chemin
    return None


def etat_de_voix(nom: str):
    """L'etat encode d'une voix : 3,8 s la PREMIERE fois, puis memoire."""
    if _modele is None:
        raise RuntimeError("modele non charge")
    if nom not in _voix_cache:
        raise ValueError("voix inconnue : %s" % nom)
    if _voix_cache[nom] is None:
        fichier = _fichier_de_voix(nom)
        if fichier is None:
            raise ValueError("fichier de voix introuvable : %s" % nom)
        debut = time.time()
        _voix_cache[nom] = _modele.get_state_for_audio_prompt(str(fichier))
        print("voix %-28s encodee en %.1f s" % (nom, time.time() - debut))
    return _voix_cache[nom]


def _en_wav(donnees, frequence: int) -> bytes:
    """Convertit les echantillons du moteur en WAV mono 16 bits."""
    import numpy as np

    if donnees.ndim == 2 and donnees.shape[0] <= 2:
        donnees = donnees.T               # [canaux, echantillons] -> l'inverse
    if donnees.ndim == 2 and donnees.shape[1] > 1:
        donnees = donnees[:, 0]           # le lecteur ne sert que du mono
    if donnees.dtype.kind == "f":
        donnees = np.clip(donnees, -1.0, 1.0)
        donnees = (donnees * 32767.0).astype("int16")

    memoire = io.BytesIO()
    with wave.open(memoire, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(int(frequence))
        wav.writeframes(donnees.tobytes())
    return memoire.getvalue()


def _crete(wav_bytes: bytes) -> float:
    """Creta du WAV (0 a 1) : sert a reconnaitre un QUASI-SILENCE."""
    import numpy as np

    with wave.open(io.BytesIO(wav_bytes), "rb") as fichier:
        donnees = np.frombuffer(fichier.readframes(fichier.getnframes()),
                                dtype="int16")
    if not len(donnees):
        return 0.0
    return float(np.abs(donnees).max()) / 32768.0


def generer_wav(texte: str, nom_voix: str) -> bytes:
    """Le WAV d'une phrase (mono, 24 kHz, 16 bits) : ce que le lecteur attend.

    GARDE-FOU CONTRE LE « TIC » (constate par Laurent le 20/09/2026) : sur un
    texte de 1 ou 2 mots, ce moteur n'a PAS de graine aleatoire -- il sort donc
    un quasi-silence (crete ~0,7 %) environ UNE FOIS SUR DEUX, et un nouveau
    tirage donne une vraie voix (mesure : 5 prises de « Non. » -> 0,8 / 0,7 /
    45,5 / 18,0 / 4,5 % ; « Merci. » -> jusqu'a 59,6 %). On regenere donc tant
    que le niveau est anormalement bas, et on garde le MEILLEUR essai si tous
    les tirages sont mauvais. Cout : nul sur les phrases normales (elles
    sortent toujours au-dessus de 60 %), une fraction de seconde sur les
    repliques courtes.
    """
    texte = nettoyer_texte(texte)
    if not texte:
        raise ValueError("texte vide")

    meilleur = None
    meilleure_crete = -1.0
    for essai in range(1, ESSAIS_MAX + 1):
        # Une seule generation a la fois (le modele n'est pas thread-safe). Le
        # verrou couvre AUSSI l'encodage de la voix : deux requetes qui arrivent
        # en meme temps ne doivent pas encoder la meme voix deux fois.
        with _verrou_generation:
            etat = etat_de_voix(nom_voix)
            audio = _modele.generate_audio(etat, texte, max_tokens=TOKENS)
            donnees = audio.detach().cpu().numpy()
            frequence = int(_modele.sample_rate)

        wav = _en_wav(donnees, frequence)
        crete = _crete(wav)
        if crete > meilleure_crete:
            meilleur, meilleure_crete = wav, crete
        if crete >= NIVEAU_MINI:
            if essai > 1:
                print("  phrase courte : %d essai(s) -- le 1er tirage sortait "
                      "un quasi-silence (%.1f %%)" % (essai, meilleure_crete * 100))
            return wav

    print("  ATTENTION : niveau tres faible apres %d essais (%.1f %%) -- "
          "texte = %s" % (ESSAIS_MAX, meilleure_crete * 100, texte[:40]))
    return meilleur


# ============================================================
# LE SERVICE HTTP (meme contrat que Kyutai, XTTS et NeuTTS)
# ============================================================

class Repondeur(BaseHTTPRequestHandler):
    server_version = "NIMPPocketTTS/1.0"

    # --- reponses --------------------------------------------------

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
            self._envoyer_json(200, {"voix": sorted(_voix_cache.keys()),
                                     "nombre": len(_voix_cache)})
        else:
            self._envoyer_json(404, {"erreur": "adresse inconnue"})

    def do_POST(self):
        chemin = self.path.split("?")[0]

        if chemin == "/recharger":
            # Relit le dossier des voix SANS redemarrer : c'est ce qui permet
            # d'ajouter une voix a la main et de l'entendre aussitot.
            repertorier_voix()
            print("voix rechargees : %d" % len(_voix_cache))
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

        debut = time.time()
        global DERNIERE_ACTIVITE
        DERNIERE_ACTIVITE = time.time()     # le moteur n'est pas inactif
        try:
            # `contexte` est IGNORE : Pocket TTS n'a pas de contexte glissant
            # dans son API (contrairement a Kyutai). Le lecteur peut l'envoyer,
            # on ne s'en sert simplement pas.
            wav = generer_wav(texte, voix)
        except ValueError as erreur:
            self._envoyer_json(400, {"erreur": str(erreur)})
            return
        except Exception as erreur:          # panne du moteur
            print("ERREUR generation : %s" % erreur)
            self._envoyer_json(500, {"erreur": "generation impossible : %s" % erreur})
            return

        calcul = time.time() - debut
        print("phrase generee  voix=%-22s  %5.1f s de calcul  %d octets"
              % (voix, calcul, len(wav)))
        self._envoyer(200, wav, "audio/wav")

    # --- journal lisible ------------------------------------------

    def log_message(self, format, *args):
        """Une ligne courte par appel ; les GET /sante sont tus.

        C'est le voyant du lecteur qui demande toutes les 5 secondes si le
        moteur est pret : cela remplirait le journal sans rien apprendre
        (meme regle que les services XTTS et Kyutai).
        """
        ligne = format % args
        if "GET /sante" in ligne:
            return
        print("%s - %s" % (self.address_string(), ligne))


class ServicePocket(ThreadingHTTPServer):
    """Serveur du moteur, avec le garde-fou Windows de la maison.

    Par defaut, Python autorise deux serveurs a ouvrir le MEME port
    (SO_REUSEADDR) : sous Windows, deux moteurs pourraient demarrer en silence
    (piege constate le 12/09/2026 sur Kyutai : deux modeles charges, machine
    saturee). On interdit le partage : le second demarrage echoue proprement et
    le premier continue de repondre.
    """

    allow_reuse_address = False


def _moteur_deja_en_route() -> bool:
    """Un moteur repond-il deja sur HOTE:PORT ? (test rapide, 0,5 s max)"""
    import socket
    try:
        with socket.create_connection((HOTE, PORT), timeout=0.5):
            return True
    except OSError:
        return False


def _surveiller_la_console():
    """Eteint le moteur si sa fenetre disparait (fenetre fermee).

    Pourquoi : sous Windows, un programme qui n'ecrit jamais dans sa console ne
    s'apercoit pas que celle-ci a ete fermee -- le moteur continuait alors de
    tourner alors que Laurent croyait l'avoir eteint (constate le 12/09/2026
    pour Kyutai). Ce gardien rend le geste naturel -- fermer la fenetre --
    vraiment efficace.

    Depuis le 21/09/2026, `START.bat` ouvre CETTE fenetre (il lancait le moteur
    cache auparavant) : le gardien s'active donc aussi en usage normal, et
    fermer la fenetre eteint vraiment Pocket TTS. Il laisse en partant le
    MARQUEUR_ARRET, que lit le veilleur du lecteur pour ne pas rallumer le
    moteur tout seul.

    Le gardien ne s'active que si le moteur tourne dans une VRAIE console
    (fenetre) : lance sans console (outils, tests, stdin redirige), il ne
    s'active pas. La variable NIMM_POCKET_TTS_SURVEILLER_CONSOLE=1 force
    l'activation, ce qui permet de tester le mecanisme.
    """
    force = os.environ.get("NIMM_POCKET_TTS_SURVEILLER_CONSOLE", "") == "1"
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
            print("Fenetre fermee : arret du moteur de voix Pocket TTS.")
            try:
                # On laisse une trace : le moteur s'arrete VOLONTAIREMENT, et le
                # veilleur du lecteur ne doit pas le rallumer tout seul.
                MARQUEUR_ARRET.write_text(
                    time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
            except Exception:
                pass
            sys.stdout.flush()
            os._exit(0)


def _surveiller_inactivite():
    """Eteint le moteur apres INACTIF_MIN minutes sans la moindre phrase.

    Le service tourne SANS fenetre : sans ce garde-fou il resterait allume
    indefiniment, avec environ 2,3 Go de memoire pris pour rien, et Laurent
    n'aurait aucun moyen de s'en apercevoir. Il se rallume tout seul au
    prochain demarrage de START.bat.
    """
    if INACTIF_MIN <= 0:
        print("  auto-extinction : DESACTIVEE (NIMM_POCKET_TTS_INACTIF=0)")
        return
    while True:
        time.sleep(30)
        repos = (time.time() - DERNIERE_ACTIVITE) / 60.0
        if repos >= INACTIF_MIN:
            print("  aucune phrase depuis %d min : le moteur s'eteint tout seul."
                  % INACTIF_MIN)
            sys.stdout.flush()
            os._exit(0)


def main():
    print("")
    print("===== NIMM ePub : appareil de voix Pocket TTS (francais) =====")
    print("")

    if _moteur_deja_en_route():
        print("ARRET : un moteur Pocket TTS repond deja sur %s:%d." % (HOTE, PORT))
        print("Rien a faire : le moteur deja allume suffit.")
        sys.exit(1)

    # Le moteur (re)demarre : le marqueur d'arret volontaire n'a plus lieu
    # d'etre. C'est ce qui permet de le rallumer a la main (ou par START.bat)
    # apres l'avoir eteint en fermant sa fenetre.
    try:
        MARQUEUR_ARRET.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # On ouvre le port AVANT de charger le modele (1,7 s mesure) : START.bat
    # voit ainsi tout de suite que le moteur est en route et ne le relance pas ;
    # et pendant le chargement, /sante repond « pret : false » (le lecteur sait
    # alors que les voix ne sont pas encore lisibles, au lieu d'une erreur).
    try:
        service = ServicePocket((HOTE, PORT), Repondeur)
    except OSError as erreur:
        print("ARRET : impossible d'ouvrir le port %d (%s)." % (PORT, erreur))
        print("Le service est peut-etre deja allume, ou le port est pris par")
        print("un autre programme (NIMM_POCKET_TTS_PORT permet d'en changer).")
        sys.exit(1)

    print("  Modele  : %s (processeur, %d coeurs)" % (LANGUE, COEURS))
    print("  Voix    : %s" % DOSSIER_VOIX)
    print("  Adresse : http://%s:%d" % (HOTE, PORT))
    print("")
    print("  Chargement du modele...")
    _infos["erreur"] = ""

    # Le modele se charge en tache de fond : le service repond deja, et /sante
    # dit « pas encore pret » le temps du chargement.
    def _charger():
        try:
            charger_modele()
            print("  MOTEUR PRET : %d voix disponibles." % _infos["voix"])
            print("")
        except Exception as erreur:
            _infos["erreur"] = str(erreur)
            print("  ECHEC du chargement : %s" % erreur)

    threading.Thread(target=_charger, daemon=True).start()
    threading.Thread(target=_surveiller_la_console, daemon=True).start()
    threading.Thread(target=_surveiller_inactivite, daemon=True).start()

    try:
        service.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("Arret demande (Ctrl+C).")
    finally:
        service.server_close()
        print("Moteur Pocket TTS arrete.")


if __name__ == "__main__":
    main()

