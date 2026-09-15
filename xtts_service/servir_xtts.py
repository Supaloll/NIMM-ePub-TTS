# -*- coding: utf-8 -*-
"""
Appareil de voix XTTS v2 (clonage de voix) -- service local pour NIMM ePub.

Ce programme charge UNE FOIS le moteur XTTS v2 (coqui-tts, ~2,1 Go sur la
carte graphique) puis repond a trois questions, en HTTP, sur le reseau local :

    GET  /sante  -> le moteur est-il pret ? (et quelles infos carte)
    GET  /voix   -> la liste des voix disponibles (les 35 francaises)
    POST /tts    -> {"texte": "...", "voix": "..."} -> fichier WAV

Il vivote A COTE du lecteur, dans son propre environnement Python 3.12
(NIMM ePub tourne sur Python 3.14 et ne peut pas heberger PyTorch).
Le lecteur l'appelle donc par le reseau, exactement comme le moteur Kyutai.

Pourquoi un service separe ? Meme raison que pour Kyutai :
  - le lecteur reste leger (aucune dependance PyTorch ajoutee) ;
  - le moteur n'est charge qu'une fois, pas a chaque phrase ;
  - une seule generation a la fois (le moteur n'est pas « thread-safe ») :
    les demandes sont mises a la queue leu leu, jamais en parallele.

VOIX : XTTS v2 est un moteur de CLONAGE -- il n'a pas de voix « a lui ». On
lui donne un extrait de 6 a 10 secondes, et il parle avec ce timbre. Les
35 extraits francais libres de CML-TTS (CC BY 4.0, ceux deja utilises par
Kyutai) servent donc de voix, tels quels : voir _telecharger.py.

Lancement : DEMARRER_XTTS.bat (ou : .venv\\Scripts\\python.exe servir_xtts.py)
Reglages (variables d'environnement, valeurs par defaut entre parentheses) :
    NIMM_XTTS_PORT   (8083)     port d'ecoute
    NIMM_XTTS_HOST   (127.0.0.1)  adresse d'ecoute (locale par defaut)
    NIMM_XTTS_LANGUE (fr)       langue lue (XTTS en connait 17)
"""

import io
import json
import os
import re
import sys
import threading
import time
import warnings
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Licence du modele (Coqui Public Model License) : usage prive accepte. Sans
# cet accord, coqui-tts pose la question dans la console -- impossible dans
# un service qui tourne en tache de fond. Voir ATTRIBUTION.md.
os.environ.setdefault('COQUI_TOS_AGREED', '1')
# Le stockage « xet » de Hugging Face a deja bloque un telechargement le
# 11/09/2026 : on le desactive preventivement (meme precaution que Kyutai).
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')

# Bruit de bibliotheque (constate par Laurent le 15/09/2026 dans la fenetre du
# moteur) : des le premier extrait de voix lu, torchaudio -- utilise EN INTERNE
# par coqui-tts -- affiche un long avertissement de depreciation sur
# `torchaudio.load` (« In 2.9, this function's implementation will be changed to
# use torchaudio.load_with_torchcodec »). Cela ne concerne NI notre code NI la
# qualite du son, et nous ne pouvons rien y corriger : l'appel est dans la
# bibliotheque. On le tait, car un avertissement qui revient a chaque
# chargement finit par masquer les vraies erreurs dans la fenetre du moteur.
warnings.filterwarnings(
    'ignore',
    message=r"In 2\.9, this function.s implementation will be changed.*")

# ==============================================================
# CHEMINS ET REGLAGES
# ==============================================================

ICI = Path(__file__).resolve().parent
# Les extraits de voix : <identifiant>_enhanced.wav (9 a 10 s de parole,
# extraits de CML-TTS, CC BY 4.0). XTTS se contente de 6 s : ils sont
# parfaits tels quels, aucune preparation n'est necessaire.
DOSSIER_VOIX = ICI / "voix_fr"

MODULE_MODELE = "tts_models/multilingual/multi-dataset/xtts_v2"

HOTE = os.environ.get("NIMM_XTTS_HOST", "127.0.0.1") or "127.0.0.1"
PORT = int(os.environ.get("NIMM_XTTS_PORT", "8083") or "8083")
LANGUE = os.environ.get("NIMM_XTTS_LANGUE", "fr") or "fr"

# Limite MESUREE du moteur en francais : 273 caracteres. Au-dela, le moteur
# le dit lui-meme (« The text length exceeds the character limit of 273 for
# language 'fr' ») et l'audio est TRONQUE. On reste nettement en dessous,
# d'autant que son decoupage interne tomberait au hasard, sans controle du
# silence. Meme lecon que la limite de 512 phonemes rencontree avec Kokoro.
MAX_CARACTERES = 250
# Silence pose UNIQUEMENT entre deux vraies phrases -- jamais a l'interieur
# d'une phrase redécoupee (0,35 s : valeur validee a l'ecoute a l'atelier).
SILENCE_PHRASE_S = 0.35
# Sortie native du moteur : WAV mono 24 000 Hz.
FREQUENCE = 24000

# Abreviations qui finissent par un point mais ne terminent PAS une phrase.
ABREVIATIONS = ('M.', 'MM.', 'Mme', 'Mlle', 'Dr', 'St', 'Ste', 'av.', 'cf.',
                'etc.', 'p.', 'pp.', 'art.', 'fig.', 'tel.')

# Taille maximale acceptee pour une demande (securite : le lecteur envoie
# toujours une phrase courte, mais on ne laisse pas un texte enorme occuper
# la carte graphique pendant des minutes -- XTTS calcule environ 3 fois plus
# lentement que la duree du texte).
TEXTE_MAX = 3000

# Une seule generation a la fois : le moteur n'aime pas les appels
# simultanes (meme precaution que le verrou Kokoro et que Kyutai).
_verrou = threading.Lock()

_moteur = None                   # le moteur, charge une seule fois
_voix_cache = {}                 # identifiant de voix -> chemin du WAV
_infos = {"pret": False, "moteur": "coqui/XTTS-v2", "appareil": "",
          "voix": 0, "langue": LANGUE, "charge_en": 0.0}


# ==============================================================
# DECOUPAGE DU TEXTE (logique validee a l'atelier le 14/09/2026)
# ==============================================================
# Le lecteur envoie deja une phrase a la fois, mais une phrase peut etre
# longue : XTTS refuse alors de la lire en entier (273 caracteres) et
# TRONQUE l'audio. On decoupe donc ici, proprement, et on recolle.

def _commence_minuscule(morceau):
    """Vrai si le fragment commence par une minuscule (indice qu'il est la
    suite d'une phrase coupee par une ponctuation interne, par exemple un
    point d'interrogation a l'interieur d'un dialogue)."""
    for caractere in morceau:
        if caractere.isalpha():
            return caractere.islower()
    return False


def decouper_phrases(texte):
    """Decoupe en phrases sur la ponctuation forte, sans rien inventer.

    Deux precautions, pour que le silence de fin de phrase tombe toujours au
    bon endroit :
      - les abreviations courantes (« M. », « etc. »...) sont recollees a la
        phrase suivante : leur point ne termine pas la phrase ;
      - un fragment qui commence par une minuscule est recolle aussi (le
        decoupage est tombe sur une ponctuation interne, souvent dans un
        dialogue).
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
    """Redecoupe une phrase trop longue, d'abord aux virgules et
    points-virgules, puis, si besoin, aux espaces. Ces morceaux se recollent
    SANS silence : la phrase reste d'un seul tenant a l'ecoute."""
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


def plan_de_lecture(texte):
    """Plan du texte a lire : une liste de PHRASES, chaque phrase etant une
    liste de MORCEAUX. Le silence ne se pose qu'entre deux phrases."""
    plan = []
    for phrase in decouper_phrases(texte):
        morceaux = decouper_trop_long(phrase)
        if morceaux:
            plan.append(morceaux)
    return plan


# ==============================================================
# NETTOYAGE POUR LE MOTEUR (constat de Laurent, 15/09/2026)
# ==============================================================
# XTTS ne sait pas IGNORER la ponctuation de dialogue comme le font Edge,
# Kokoro et Piper : il essaie de la prononcer, et cela produit des sons
# parasites. Ecoute du lot comparatif sortie_ecoute_guillemets (voix Bertrand) :
#   - avec les guillemets « », Laurent entend « ogui ... haa » (01) et
#     « iogue ... yo » (05) : le moteur LIT les guillemets ;
#   - avec un tiret cadratin ouvrant, il entend « vous eteetes sur de vous »
#     (07) : repetition du premier mot ;
#   - sans ces signes (02 et 08), la phrase est propre et bien prosodice ;
#   - remplacer les guillemets par une VIRGULE (03) ou une ESPACE (04) donne des
#     intonations parasites (montees/descentes marquees, aigus) : on RETIRE.
# On nettoie donc le morceau juste avant l'envoi au moteur.
#
# Deux consequences a garder en tete :
#   1. cela change le TEXTE, donc la cle du cache audio du lecteur -- les
#      phrases deja lues gardent l'ancien rendu jusqu'a purge du cache ;
#   2. ce nettoyage est PROPRE A XTTS : les autres moteurs recoivent la phrase
#      telle quelle, sans changement (rien a corriger chez eux).
GUILLEMETS = ('\u00ab', '\u00bb', '"', '\u201c', '\u201d')
TIRETS_CADRATINS = ('\u2014', '\u2013')


def nettoyer_pour_xtts(texte):
    """Prepare un morceau de phrase pour XTTS (voir le commentaire ci-dessus).

    Les tirets d'union (« demanda-t-il »), les apostrophes et les points de
    suspension ne sont PAS touches : seuls les signes qui font parler le moteur
    de travers le sont.
    """
    resultat = texte.strip()
    # 1) Guillemets : le moteur les prononce -> on les retire.
    for signe in GUILLEMETS:
        resultat = resultat.replace(signe, ' ')
    resultat = resultat.strip()
    # 2) Tiret cadratin en tete : il fait repeter le premier mot. Ailleurs (une
    #    incise, ou la replique suivante dans le meme morceau), il devient une
    #    virgule : la respiration est conservee, le defaut non.
    if resultat[:1] in TIRETS_CADRATINS:
        resultat = resultat[1:]
    for signe in TIRETS_CADRATINS:
        resultat = resultat.replace(' ' + signe, ',')
        resultat = resultat.replace(signe + ' ', ', ')
        resultat = resultat.replace(signe, ',')
    # Les signes retires laissent des trous : on compacte, comme partout
    # ailleurs dans le service.
    return ' '.join(resultat.split()).strip()


# ==============================================================
# LES VOIX (extraits de reference a cloner)
# ==============================================================

def _repertorier_voix():
    """Associe chaque voix (identifiant lisible) a son extrait de reference.

    Les fichiers s'appellent, par exemple :

        10087_11650_000028-0002_enhanced.wav

    et l'identifiant retenu est la partie avant « _enhanced.wav » :
    10087_11650_000028-0002 -- exactement les identifiants deja utilises par
    le catalogue Kyutai, ce qui permet de retrouver ses reperes.
    """
    global _voix_cache
    trouvees = {}
    if DOSSIER_VOIX.is_dir():
        # rglob : les fichiers peuvent etre a plat (copie du moteur Kyutai) ou
        # ranges dans « cml-tts\fr\ » (telechargement depuis la banque).
        fichiers = sorted(DOSSIER_VOIX.rglob("*.wav"))
        # Une meme voix peut avoir deux fichiers (l'enregistrement brut et sa
        # version nettoyee « _enhanced »). C'est la version nettoyee qui est
        # retenue -- celle qui a ete ecoutee et validee.
        ameliores = [f for f in fichiers if f.stem.endswith("_enhanced")]
        for fichier in (ameliores or fichiers):
            nom = fichier.stem                      # retire le « .wav »
            if nom.endswith("_enhanced"):
                nom = nom[:-len("_enhanced")]
            if nom:
                trouvees[nom] = fichier
    _voix_cache = trouvees
    return trouvees


# ==============================================================
# CHARGEMENT DU MOTEUR (une seule fois, au demarrage)
# ==============================================================

def charger_moteur():
    """Charge XTTS v2 en memoire vive (carte graphique).

    La premiere fois, le modele (2,1 Go) se telecharge : c'est
    _telecharger.py qui s'en occupe a l'installation, donc ici il est
    normalement deja en cache. L'ordre des deux etapes compte -- les voix
    d'abord, pour pouvoir s'arreter tout de suite si elles manquent.
    """
    global _moteur

    import torch
    from TTS.api import TTS

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

    print("Chargement du modele XTTS v2 (%s)..." % nom_appareil)
    t0 = time.time()
    modele = TTS(MODULE_MODELE)
    # .to("cuda") est la facon recommandee ; le parametre gpu=True est
    # deprecie et declenche un avertissement (constate a l'atelier).
    try:
        modele = modele.to(str(appareil))
    except (AttributeError, TypeError):
        modele = TTS(MODULE_MODELE, gpu=(appareil.type == "cuda"))
    _moteur = modele

    _infos["appareil"] = nom_appareil
    _infos["voix"] = len(_voix_cache)
    _infos["charge_en"] = round(time.time() - t0, 1)
    _infos["pret"] = True
    print("Moteur pret en %.1f s -- %d voix disponibles."
          % (_infos["charge_en"], len(_voix_cache)))


def _wav_depuis_pcm(echantillons, frequence=FREQUENCE):
    """Convertit l'audio du moteur (nombres flottants) en WAV 16 bits mono --
    meme format que Kokoro, Piper et Kyutai dans le lecteur."""
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


def _lire_un_morceau(morceau, chemin_reference):
    """Fait lire UN morceau (250 caracteres au plus) avec la voix donnee.

    Le morceau passe d'abord par nettoyer_pour_xtts() : XTTS PRONONCE les
    guillemets et bute sur le tiret cadratin (ecoute de Laurent, 15/09/2026).
    """
    import numpy as np
    morceau = nettoyer_pour_xtts(morceau)
    if not morceau:
        # Le morceau ne contenait que des signes retires : il n'y a rien a
        # dire -- et surtout rien a envoyer au moteur.
        return np.zeros(0, dtype=np.float32)
    try:
        audio = _moteur.tts(text=morceau, speaker_wav=chemin_reference,
                            language=LANGUE, split_sentences=False)
    except TypeError:          # version de coqui-tts sans ce parametre
        audio = _moteur.tts(text=morceau, speaker_wav=chemin_reference,
                            language=LANGUE)
    return np.asarray(audio, dtype=np.float32)


def generer_wav(texte, identifiant_voix):
    """Genere le WAV d'un texte, avec une voix. Renvoie les octets du WAV.

    Leve une exception si la voix est inconnue ou si la generation echoue :
    le service transforme cela en message clair pour le lecteur.

    Les morceaux d'une meme phrase sont recolles SANS silence ; un silence
    court est pose entre deux vraies phrases -- c'est ce qui donne un rythme
    naturel a l'ecoute (meme regle que celle validee a l'atelier).
    """
    import numpy as np

    if _moteur is None:
        raise RuntimeError("le moteur n'est pas encore charge")
    if identifiant_voix not in _voix_cache:
        raise ValueError("voix inconnue : %s" % identifiant_voix)

    plan = plan_de_lecture(texte)
    if not plan:
        raise ValueError("texte vide")

    reference = str(_voix_cache[identifiant_voix])
    silence = np.zeros(int(SILENCE_PHRASE_S * FREQUENCE), dtype=np.float32)

    with _verrou:
        sons = []
        for rang, morceaux in enumerate(plan):
            if rang:
                sons.append(silence)
            for morceau in morceaux:
                sons.append(_lire_un_morceau(morceau, reference))

    return _wav_depuis_pcm(np.concatenate(sons))


# ==============================================================
# LE SERVICE HTTP (bibliotheque standard uniquement : rien a installer
# en plus de PyTorch et coqui-tts)
# ==============================================================

class Repondeur(BaseHTTPRequestHandler):
    server_version = "NIMMXtts/1.0"

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
            # Re-scanne le dossier des voix SANS recharger le moteur : permet
            # d'ajouter une voix sans redemarrer le service.
            _repertorier_voix()
            # On met aussi a jour le compteur affiche par /sante : sans cela il
            # restait fige au nombre de voix du demarrage (constate le
            # 14/09/2026 : /sante annoncait 35 voix alors que 60 existaient).
            _infos["voix"] = len(_voix_cache)
            print("voix rechargees : %d" % len(_voix_cache))
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

        duree = (time.time() - t0)
        print("phrase generee  voix=%-28s  %5.1f s de calcul  %d octets"
              % (voix, duree, len(wav)))
        self._envoyer(200, wav, "audio/wav")

    # --- journal lisible ------------------------------------------

    def log_message(self, format, *args):
        """Une ligne courte par appel, lisible dans la fenetre du moteur.

        Les interrogations `GET /sante` ne sont PAS affichees : c'est le voyant
        du lecteur, qui demande toutes les 5 secondes si le moteur est pret --
        cela remplissait la fenetre sans rien apprendre (constat du
        15/09/2026). Tout le reste (generations, /recharger, arret du gardien)
        reste visible.
        """
        ligne = format % args
        if 'GET /sante' in ligne:
            return
        print("%s - %s" % (self.address_string(), ligne))


class ServiceXtts(ThreadingHTTPServer):
    """Serveur du moteur, avec le meme garde-fou que Kyutai.

    Par defaut, Python autorise deux serveurs a ouvrir le MEME port
    (option SO_REUSEADDR). Sur Windows, cela veut dire que deux moteurs
    pouvaient demarrer en silence (constate le 12/09/2026 : deux modeles
    charges en meme temps, 2 x 3,8 Go de carte graphique, machine saturee).
    On interdit donc le partage : le deuxieme demarrage echoue, le service
    s'arrete proprement et le premier continue de repondre.
    """

    allow_reuse_address = False


def _surveiller_la_console():
    """Eteint le moteur si sa fenetre disparait (fenetre fermee).

    Pourquoi : sous Windows, un programme qui n'ecrit jamais dans sa console
    ne s'apercoit pas que celle-ci a ete fermee -- le moteur continuait alors
    de tourner (port occupe, memoire de la carte graphique gardee) alors que
    Laurent croyait l'avoir eteint (constate le 12/09/2026 avec Kyutai). Ce
    gardien rend le geste naturel -- fermer la fenetre -- vraiment efficace.

    Il ne s'active que si le moteur tourne dans une VRAIE console (fenetre) :
    lance sans console (outils, tests, stdin redirige), il ne s'active pas.
    La variable NIMM_XTTS_SURVEILLER_CONSOLE=1 force l'activation, ce qui
    permet de tester le mecanisme.
    """
    force = os.environ.get("NIMM_XTTS_SURVEILLER_CONSOLE", "") == "1"
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
            print("Fenetre fermee : arret du moteur de voix XTTS v2.")
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
    print("===== NIMM ePub : appareil de voix XTTS v2 (clonage) =====")

    if _moteur_deja_en_route():
        print("ARRET : un moteur de voix XTTS tourne deja sur %s:%d."
              % (HOTE, PORT))
        print("Rien a faire : la fenetre deja ouverte suffit.")
        sys.exit(1)

    # Le port est ouvert AVANT le chargement du modele (10 a 20 s). Deux
    # consequences voulues :
    #   1. START.bat voit tout de suite qu'un moteur est en route et n'en
    #      lance donc jamais un second (les deux ne tiennent pas ensemble sur
    #      la carte graphique) ;
    #   2. pendant le chargement, /sante repond « pret : false » -- le
    #      lecteur ne propose donc pas encore les voix XTTS : c'est le
    #      principe des « voix ecoutables tout de suite » (14/09/2026).
    try:
        service = ServiceXtts((HOTE, PORT), Repondeur)
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
