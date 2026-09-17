# -*- coding: utf-8 -*-
"""
Appareil de voix Kyutai TTS 1.6B -- service local pour NIMM ePub.

Ce programme charge UNE FOIS le moteur Kyutai (3,4 Go sur la carte
graphique) puis repond a trois questions, en HTTP, sur le reseau local :

    GET  /sante  -> le moteur est-il pret ? (et quelles infos GPU)
    GET  /voix   -> la liste des voix francaises disponibles
    POST /tts    -> {"texte": "...", "voix": "..."} -> fichier WAV

Il vivote A COTE du lecteur, dans son propre environnement Python 3.12
(NIMM ePub tourne sur Python 3.14 et ne peut pas heberger PyTorch).
Le lecteur l'appelle donc par le reseau, comme il appelle deja Edge TTS.

Pourquoi un serveur separe ?
  - le lecteur reste leger (aucune dependance PyTorch ajoutee) ;
  - le moteur n'est charge qu'une fois, pas a chaque phrase ;
  - une seule generation a la fois (le moteur n'est pas « thread-safe ») :
    les demandes sont mises a la queue leu leu, jamais en parallele.

Lancement : DEMARRER_KYUTAI.bat (ou : .venv\\Scripts\\python.exe servir_kyutai.py)
Reglages (variables d'environnement, valeurs par defaut entre parentheses) :
    NIMM_KYUTAI_PORT   (8082)   port d'ecoute
    NIMM_KYUTAI_HOST   (127.0.0.1)  adresse d'ecoute (locale par defaut)
    NIMM_KYUTAI_CFG    (2.0)    guidage par la voix (qualite/fidelite)
    NIMM_KYUTAI_POIDS  (vide)   chemin du modele si range ailleurs
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

# torch.compile() est impossible sous Windows (Triton n'existe pas) :
# NO_TORCH_COMPILE=1 est le remede indique par la FAQ de Kyutai.
os.environ.setdefault('NO_TORCH_COMPILE', '1')
# Le stockage « xet » de Hugging Face a deja bloque un telechargement
# le 11/09/2026 : on le desactive preventivement.
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

# ==============================================================
# CHEMINS ET REGLAGES
# ==============================================================

ICI = Path(__file__).resolve().parent
DOSSIER_VOIX = ICI / "voix_fr" / "cml-tts" / "fr"
DOSSIER_MODELE = ICI / "modele"
# Voix d'autres familles de la banque Kyutai (anglaises, CC0...), rangees ici
# pour les essais : sous-dossier = famille (vctk, voice-donations, ears...).
# Elles ne sont PAS dans le catalogue du lecteur : elles servent a tester ce
# que donne une voix etrangere sur du texte francais.
DOSSIER_AUTRES = ICI / "voix_autres"

# Nom du gros fichier du modele (identique dans le depot Hugging Face).
NOM_GROS_FICHIER = "dsm_tts_1e68beda@240.safetensors"
REPO_MODELE = "kyutai/tts-1.6b-en_fr"

HOTE = os.environ.get("NIMM_KYUTAI_HOST", "127.0.0.1")
PORT = int(os.environ.get("NIMM_KYUTAI_PORT", "8082") or "8082")
CFG = float(os.environ.get("NIMM_KYUTAI_CFG", "2.0") or "2.0")
# Respiration ajoutee en FIN de phrase, en secondes (0 = aucune).
# Demande de Laurent (17/09/2026) : « le point passe tres tres vite ». Mesure
# avant reglage : le moteur s'arrete net sur le dernier mot et laisse 0,30 a
# 0,43 s de silence selon la phrase ; on ajoute donc 0,10 s, comme Edge cote
# lecteur (rognage passe de 0,25 a 0,35 s le meme jour).
SILENCE_QUEUE_S = float(
    os.environ.get("NIMM_KYUTAI_SILENCE_QUEUE", "0.10") or "0.10")

# --- Contexte glissant (idee de Laurent, 17/09/2026) -----------------------
# Le moteur demarre A FROID sur chaque phrase : sa hauteur et son energie
# « repartent » a chaque fois (sautes de volume, voix moins chantee), et une
# phrase courte manque de matiere. Laurent a montre qu'en lui donnant LA FIN DE
# LA PHRASE PRECEDENTE, la voix est plus stable et mieux posee.
# On genere donc « contexte + phrase », puis on COUPE dans un silence pour ne
# garder que la phrase -- l'auditeur n'entend jamais le contexte.
# MESURE (banc du 17/09/2026) : 6 mots suffisent ; une phrase ENTIERE de
# contexte sature la fenetre du modele et TRONQUE la phrase a lire (1,4 s au
# lieu de 9,6 s). D'ou les deux garde-fous ci-dessous.
CONTEXTE_CARACTERES_MAX = 90       # au-dela, on ne garde que la fin du contexte
SILENCE_COUPE_S = 0.12             # silence minimal ou l'on accepte de couper
MARGE_CONTEXTE_S = 0.25            # on cherche le silence apres (fin - 0,25 s)
BLOC_ANALYSE_S = 0.01              # granularite d'analyse du son
SEUIL_SON = 0.012                  # meme seuil que les autres outils d'atelier

# Une seule generation a la fois : le moteur n'aime pas les appels
# simultanes (meme precaution que le verrou Kokoro du lecteur).
_verrou = threading.Lock()

_tts = None                      # le moteur, charge une seule fois
_voix_cache = {}                 # id de voix -> chemin du fichier
_infos = {"pret": False, "moteur": REPO_MODELE, "appareil": "",
          "voix": 0, "cfg": CFG, "charge_en": 0.0}


def trouver_poids():
    """Cherche le gros fichier du modele, dans l'ordre :
       1. NIMM_KYUTAI_POIDS (si defini) ;
       2. kyutai_service/modele/ (copie locale au projet) ;
       3. cache de l'utilisateur (%USERPROFILE%\\.cache\\kyutai_modele).
    Renvoie un chemin, ou None si introuvable."""
    candidats = []
    force = os.environ.get("NIMM_KYUTAI_POIDS", "").strip()
    if force:
        candidats.append(Path(force))
    candidats.append(DOSSIER_MODELE / NOM_GROS_FICHIER)
    candidats.append(Path(os.path.expanduser("~")) / ".cache" / "kyutai_modele"
                          / NOM_GROS_FICHIER)
    for chemin in candidats:
        if chemin.is_file():
            return chemin
    return None


def _repertorier_voix():
    """Associe chaque voix (id lisible) a son chemin.

    Deux endroits sont explores :

      1. DOSSIER_VOIX -- les 35 voix FRANCAISES libres (banque cml-tts/fr).
         Les fichiers s'appellent, par exemple :
             10087_11650_000028-0002_enhanced.wav.1e68beda@240.safetensors
         et l'identifiant retenu est la partie lisible avant
         « _enhanced.wav » : 10087_11650_000028-0002.
      2. DOSSIER_AUTRES -- des voix d'AUTRES familles (vctk, voice-donations,
         ears...) rangees en sous-dossiers pour les essais d'accent. Leur
         identifiant est prefixe par le nom de la famille, pour ne jamais
         entrer en collision avec les voix francaises.

    On ne code pas en dur le suffixe « .1e68beda@240 » : il depend du modele
    et pourrait changer avec une version future.
    """
    global _voix_cache
    marqueur = "_enhanced.wav"
    candidats = {}

    def _ajouter(nom, fichier):
        """Enregistre un fichier candidat pour cette voix."""
        candidats.setdefault(nom, []).append(fichier)

    def _nom_de_voix(nom_fichier):
        """Nom lisible d'une voix, selon la convention de la famille.

        cml-tts/fr : <nom>_enhanced.wav.1e68beda@240.safetensors
        vctk, dons : <nom>.wav.1e68beda@240.safetensors
        (la famille est indiquee par un sous-dossier dans voix_autres)
        """
        if marqueur in nom_fichier:
            return nom_fichier.split(marqueur)[0]
        if ".wav." in nom_fichier:
            return nom_fichier.split(".wav.")[0]
        return None

    if DOSSIER_VOIX.is_dir():
        for fichier in sorted(DOSSIER_VOIX.glob("*.safetensors")):
            nom = _nom_de_voix(fichier.name)
            if nom:
                _ajouter(nom, fichier)

    if DOSSIER_AUTRES.is_dir():
        for fichier in sorted(DOSSIER_AUTRES.rglob("*.safetensors")):
            nom = _nom_de_voix(fichier.name)
            if nom:
                famille = fichier.relative_to(DOSSIER_AUTRES).parts[0]
                _ajouter("%s_%s" % (famille, nom), fichier)

    # Une meme voix peut avoir plusieurs empreintes (l'enregistrement brut et
    # sa version nettoyee « _enhanced »). C'est la version nettoyee que l'on
    # garde, exactement comme lors des premiers essais valides.
    trouves = {}
    for nom, fichiers in candidats.items():
        ameliores = [f for f in fichiers if marqueur in f.name]
        trouves[nom] = (ameliores or fichiers)[0]

    _voix_cache = trouves
    return trouves


# ==============================================================
# CHARGEMENT DU MOTEUR (une seule fois, au demarrage)
# ==============================================================

def charger_moteur():
    """Charge le moteur Kyutai en memoire vive (carte graphique).

    Appele au demarrage du service : le chargement prend quelques
    secondes, puis chaque phrase est generee sans rien recharger.
    """
    global _tts

    import torch
    from moshi.models.loaders import CheckpointInfo
    from moshi.models.tts import DEFAULT_DSM_TTS_REPO, TTSModel

    poids = trouver_poids()
    if poids is None:
        print("ARRET : gros fichier du modele introuvable.")
        print("Lance d'abord : .venv\\Scripts\\python.exe _telecharger.py")
        sys.exit(1)

    _repertorier_voix()
    if not _voix_cache:
        print("ARRET : aucune voix trouvee dans %s" % DOSSIER_VOIX)
        print("Lance d'abord : .venv\\Scripts\\python.exe _telecharger.py")
        sys.exit(1)

    if torch.cuda.is_available():
        appareil = torch.device("cuda")
        nom_appareil = "cuda : %s" % torch.cuda.get_device_name(0)
    else:
        appareil = torch.device("cpu")
        nom_appareil = "cpu (aucune carte graphique detectee : ce sera lent)"

    print("Chargement du moteur Kyutai (%s)..." % nom_appareil)
    t0 = time.time()
    infos_modele = CheckpointInfo.from_hf_repo(
        DEFAULT_DSM_TTS_REPO, moshi_weights=str(poids))
    _tts = TTSModel.from_checkpoint_info(
        infos_modele, n_q=32, temp=0.6, device=appareil)

    _infos["appareil"] = nom_appareil
    _infos["voix"] = len(_voix_cache)
    _infos["charge_en"] = round(time.time() - t0, 1)
    _infos["pret"] = True
    print("Moteur pret en %.1f s -- %d voix francaises disponibles."
          % (_infos["charge_en"], len(_voix_cache)))


def _wav_depuis_pcm(pcm, frequence):
    """Convertit l'audio du moteur (nombres flottants) en fichier WAV
    16 bits mono -- meme format que Kokoro et Piper dans le lecteur."""
    import numpy as np
    if hasattr(pcm, "float"):
        donnees = pcm.float().cpu().numpy()
    else:
        donnees = np.asarray(pcm, dtype=np.float32)
    donnees = np.clip(donnees, -1.0, 1.0)
    donnees = (donnees * 32767.0).astype("<i2")

    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(frequence))
        fichier.writeframes(donnees.tobytes())
    return tampon.getvalue()


def _en_numpy(sons):
    """Convertit l'audio du moteur en tableau numpy 1D (tenseur ou tableau).

    `simple_generate` rend un TENSEUR PyTorch, qui peut vivre sur la carte
    graphique : `np.asarray` le refuse alors (erreur 500 constatee le
    17/09/2026). On repasse donc par `.detach().cpu()`.
    """
    import numpy as np

    if hasattr(sons, "detach"):
        return sons.detach().cpu().float().numpy().reshape(-1)
    return np.asarray(sons, dtype=np.float32).reshape(-1)


def _blocs_parles(sons, frequence):
    """[(debut, fin)] en echantillons des blocs de son audible."""
    import numpy as np

    pas = max(1, int(BLOC_ANALYSE_S * frequence))
    blocs = []
    for debut in range(0, len(sons), pas):
        bloc = sons[debut:debut + pas]
        if bloc.size and float(np.max(np.abs(bloc))) >= SEUIL_SON:
            if blocs and debut - blocs[-1][1] <= pas * 1.5:
                blocs[-1] = (blocs[-1][0], debut + bloc.size)
            else:
                blocs.append((debut, debut + bloc.size))
    return blocs


def _ou_commence_la_phrase(sons_contexte, sons_long, frequence):
    """Ou commence la phrase, dans l'audio « contexte + phrase ».

    On sait ou finit le contexte (mesure sur sa propre generation), et on
    cherche le premier VRAI SILENCE apres ce point : on coupe donc dans un
    silence, jamais au milieu d'un mot. Si aucun silence franc n'est trouve,
    on coupe a la fin mesuree du contexte (moins sur, mais la phrase est
    entiere).
    """
    blocs_contexte = _blocs_parles(sons_contexte, frequence)
    fin_contexte = blocs_contexte[-1][1] if blocs_contexte else 0
    blocs = _blocs_parles(sons_long, frequence)
    limite = fin_contexte - int(MARGE_CONTEXTE_S * frequence)
    for rang in range(1, len(blocs)):
        silence = blocs[rang][0] - blocs[rang - 1][1]
        if silence >= SILENCE_COUPE_S * frequence and blocs[rang][0] >= limite:
            # On coupe DANS le silence, un peu APRES la fin du dernier son du
            # contexte. Couper pile sur la frontiere laissait passer quelques
            # echantillons du dernier mot du contexte : ils s'entendaient comme
            # un petit « tic » avant chaque phrase (constat de Laurent,
            # 17/09/2026). La marge reste dans le silence, donc elle ne mange
            # jamais le debut de la phrase.
            marge = int(0.04 * frequence)
            return (min(blocs[rang][0], blocs[rang - 1][1] + marge),
                    fin_contexte, True)
    return min(fin_contexte, len(sons_long)), fin_contexte, False


def generer_wav(texte, identifiant_voix, cfg=None, contexte=""):
    """Genere une phrase avec une voix. Renvoie les octets du WAV.

    `contexte` (facultatif) : la FIN DE LA PHRASE PRECEDENTE. Le moteur lit
    alors « contexte + phrase » et on ne garde que la phrase, coupee dans un
    silence (voir les constantes CONTEXTE_* ci-dessus).

    Leve une exception si la voix est inconnue ou si la generation
    echoue : l'appelant (le service) transforme cela en message clair.
    """
    if _tts is None:
        raise RuntimeError("le moteur n'est pas encore charge")

    if identifiant_voix not in _voix_cache:
        raise ValueError("voix inconnue : %s" % identifiant_voix)

    coef = CFG if cfg is None else float(cfg)
    chemin_voix = str(_voix_cache[identifiant_voix])

    contexte = (contexte or "").strip()
    if len(contexte) > CONTEXTE_CARACTERES_MAX:
        # On ne garde que la FIN du contexte, et on repart a la premiere espace
        # pour ne pas commencer au milieu d'un mot.
        contexte = contexte[-CONTEXTE_CARACTERES_MAX:]
        espace = contexte.find(' ')
        if espace > 0:
            contexte = contexte[espace + 1:]

    with _verrou:
        if contexte:
            import numpy as np
            frequence = _tts.mimi.sample_rate
            sons_contexte = _tts.simple_generate(
                contexte, chemin_voix, cfg_coef=coef, show_progress=False)[0]
            sons_long = _tts.simple_generate(
                contexte + ' ' + texte, chemin_voix, cfg_coef=coef,
                show_progress=False)[0]
            sons_long = _en_numpy(sons_long)
            coupe, fin_contexte, sur = _ou_commence_la_phrase(
                _en_numpy(sons_contexte), sons_long, frequence)
            print("  contexte : %d car., fin a %.2f s, coupe a %.2f s (%s)"
                  % (len(contexte), fin_contexte / float(frequence),
                     coupe / float(frequence),
                     "silence" if sur else "estimation"))
            pcm = sons_long[coupe:]
        else:
            resultats = _tts.simple_generate(
                texte, chemin_voix, cfg_coef=coef, show_progress=False)
            pcm = resultats[0]
    # Respiration de fin de phrase (voir SILENCE_QUEUE_S ci-dessus) : le moteur
    # s'arrete net sur le dernier mot.
    if SILENCE_QUEUE_S > 0:
        longueur = int(SILENCE_QUEUE_S * _tts.mimi.sample_rate)
        if hasattr(pcm, "cpu"):                     # tenseur PyTorch
            import torch
            pcm = torch.cat([pcm, torch.zeros(longueur, dtype=pcm.dtype,
                                              device=pcm.device)])
        else:                                       # tableau numpy
            import numpy as np
            pcm = np.concatenate([np.asarray(pcm),
                                  np.zeros(longueur, dtype=np.float32)])
    return _wav_depuis_pcm(pcm, _tts.mimi.sample_rate)


# ==============================================================
# LE SERVICE HTTP (bibliotheque standard uniquement : rien a installer
# en plus de PyTorch et moshi)
# ==============================================================

# Taille maximale acceptee pour une phrase (securite : le lecteur envoie
# toujours une phrase courte, mais on ne laisse pas un texte enorme
# occuper la carte graphique pendant des minutes).
TEXTE_MAX = 5000


class Repondeur(BaseHTTPRequestHandler):
    server_version = "NIMMKyutai/1.0"

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
            # Re-scanne les dossiers de voix SANS recharger le moteur : permet
            # d'ajouter une voix (ou un lot d'essai) sans redemarrer le service.
            _repertorier_voix()
            print("voix rechargees : %d" % len(_voix_cache))
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

        t0 = time.time()
        try:
            # `contexte` (facultatif) : la fin de la phrase precedente, pour que
            # le moteur ne demarre pas a froid (voir CONTEXTE_* en haut).
            wav = generer_wav(texte, voix, demande.get("cfg"),
                              demande.get("contexte") or "")
        except ValueError as erreur:
            self._envoyer_json(400, {"erreur": str(erreur)})
            return
        except Exception as erreur:          # panne du moteur
            print("ERREUR generation : %s" % erreur)
            self._envoyer_json(500, {"erreur": "generation impossible : %s" % erreur})
            return

        duree = (time.time() - t0)
        print("phrase generee  voix=%-28s  %5.1f s de calcul  %d octets"
              % (voix, duree, len(wav)))
        self._envoyer(200, wav, "audio/wav")

    # --- journal lisible -----------------------------------------

    def log_message(self, format, *args):
        """Une ligne courte par appel, lisible dans la fenetre du moteur.

        Les interrogations `GET /sante` ne sont PAS affichees (meme regle que le
        service XTTS, 15/09/2026) : c'est le voyant du lecteur, qui demande
        toutes les 5 secondes si le moteur est pret -- cela remplissait la
        fenetre sans rien apprendre.
        """
        ligne = format % args
        if 'GET /sante' in ligne:
            return
        print("%s - %s" % (self.address_string(), ligne))


class ServiceKyutai(ThreadingHTTPServer):
    """Serveur du moteur, avec un garde-fou indispensable sous Windows.

    Par defaut, Python autorise deux serveurs a ouvrir le MEME port
    (option SO_REUSEADDR). Sur Windows, cela veut dire que deux moteurs
    pouvaient demarrer en silence -- constate le 12/09/2026 : deux modeles
    charges en meme temps, 2 x 3,8 Go de carte graphique, machine saturee.
    On interdit donc le partage : le deuxieme demarrage echoue, le service
    s'arrete proprement et le premier continue de repondre.
    """

    allow_reuse_address = False


def _surveiller_la_console():
    """Eteint le moteur si sa fenetre disparait (fenetre ou onglet ferme).

    Pourquoi : sous Windows, un programme qui n'ecrit jamais dans sa console
    ne s'apercoit pas que celle-ci a ete fermee -- le moteur continuait alors
    de tourner (port occupe, 3,8 Go de carte graphique) alors que Laurent
    croyait l'avoir eteint (constate le 12/09/2026). Ce gardien rend le geste
    naturel -- fermer la fenetre -- vraiment efficace.

    Principe : tant que la fenetre existe, la lecture du clavier reste en
    attente (personne ne tape dans cette fenetre). Des que la fenetre est
    fermee, la lecture revient immediatement avec une chaine VIDE (fin de
    flux) : c'est le signal. Si une touche est frappee, on continue
    simplement a surveiller.

    Le gardien ne s'active que si le moteur tourne dans une VRAIE console
    (fenetre) : lance sans console (outils, tests, stdin redirige), il ne
    s'active pas. La variable NIMM_KYUTAI_SURVEILLER_CONSOLE=1 force
    l'activation, ce qui permet de tester le mecanisme.
    """
    force = os.environ.get("NIMM_KYUTAI_SURVEILLER_CONSOLE", "") == "1"
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
            print("Fenetre fermee : arret du moteur de voix Kyutai.")
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
    print("===== NIMM ePub : appareil de voix Kyutai TTS 1.6B =====")

    if _moteur_deja_en_route():
        print("ARRET : un moteur de voix Kyutai tourne deja sur %s:%d." % (HOTE, PORT))
        print("Rien a faire : la fenetre deja ouverte suffit.")
        sys.exit(1)

    # Le port est ouvert AVANT le chargement du modele -- celui-ci prend une
    # quinzaine de secondes. Deux consequences voulues :
    #   1. START.bat voit tout de suite que le moteur est en route, et ne
    #      lance donc JAMAIS un second moteur (deux moteurs occuperaient
    #      2 x 3,8 Go de carte graphique) ;
    #   2. pendant le chargement, /sante repond « pret : false » et /tts
    #      repond « moteur en cours de chargement » -- message clair plutot
    #      qu'une erreur de connexion.
    try:
        service = ServiceKyutai((HOTE, PORT), Repondeur)
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

    import threading
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
