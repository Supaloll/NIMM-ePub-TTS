# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import re
import shutil
import sqlite3
import asyncio
import subprocess
import urllib.request
import time
import traceback
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.epub_parser import sniff_image_type

# Le module qui compose le pool automatique du casting : il a besoin des notes
# (etoiles) des voix Edge, qui vivent ici meme (FRENCH_VOICES) -- voir l'appel
# definir_voix_edge() juste apres la definition du catalogue.
from modules import voice_casting

# --- Chemins ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LIBRARY_DIR = DATA_DIR / "library"
DB_PATH = DATA_DIR / "nimm_epub.db"
FRONTEND_DIR = BASE_DIR / "frontend"
PIPER_TAGS_PATH = DATA_DIR / "piper_gender_tags.json"
# Ce que Laurent note en ecoutant une voix dans la fenetre « Ecouter les voix »
# (genre entendu, etoiles, remarque). Reglage LOCAL, hors Git : il SURCHARGE
# le catalogue sans le modifier. Reporter ces notes dans le catalogue
# (modules/tts.py) reste une etape volontairement manuelle.
ANNOTATIONS_VOIX_PATH = DATA_DIR / "annotations_voix.json"

DATA_DIR.mkdir(exist_ok=True)
LIBRARY_DIR.mkdir(exist_ok=True)

# Cascade de secours pour les passages qu'un moteur distant REFUSE (filtre de
# contenu). Essayee dans l'ordre (session du 14/09/2026) :
#   1. DeepSeek -- resultat quasi identique a Gemini (97,3 % d'accord, mesure)
#      pour environ 1 centime par chapitre ;
#   2. le moteur local, en tout dernier recours : gratuit, sans filtre de
#      contenu, mais son resultat est inutilisable a l'ecoute (verdict mesure
#      du 14/09/2026) -- mieux vaut cela que rien du tout.
MOTEURS_DE_SECOURS = ["deepseek", "local"]

# --- Voix françaises ---
FRENCH_VOICES = [
    {"id": "fr-FR-VivienneMultilingualNeural", "name": "Vivienne", "region": "France",   "gender": "F", "stars": 3},
    {"id": "fr-FR-DeniseNeural",               "name": "Denise",   "region": "France",   "gender": "F", "stars": 3},
    {"id": "fr-FR-EloiseNeural",               "name": "Eloise",   "region": "France",   "gender": "F", "stars": 2},
    {"id": "fr-FR-HenriNeural",                "name": "Henri",    "region": "France",   "gender": "M", "stars": 3},
    {"id": "fr-FR-RemyMultilingualNeural",      "name": "Remy",     "region": "France",   "gender": "M", "stars": 3},
    {"id": "fr-BE-CharlineNeural",             "name": "Charline", "region": "Belgique", "gender": "F", "stars": 2},
    {"id": "fr-BE-GerardNeural",               "name": "Gerard",   "region": "Belgique", "gender": "M", "stars": 3},
    {"id": "fr-CA-SylvieNeural",               "name": "Sylvie",   "region": "Canada",   "gender": "F", "stars": 2},
    {"id": "fr-CA-AntoineNeural",              "name": "Antoine",  "region": "Canada",   "gender": "M", "stars": 0},
    {"id": "fr-CA-JeanNeural",                 "name": "Jean",     "region": "Canada",   "gender": "M", "stars": 0},
    {"id": "fr-CH-ArianeNeural",               "name": "Ariane",   "region": "Suisse",   "gender": "F", "stars": 3},
    {"id": "fr-CH-FabriceNeural",              "name": "Fabrice",  "region": "Suisse",   "gender": "M", "stars": 0},
]
DEFAULT_VOICE = "fr-CH-ArianeNeural"

# --- Pool automatique du casting : regle des paliers d'etoiles ---
# Decision de Laurent (15/09/2026) : le pool se parcourt par paliers d'etoiles
# (3, puis 2, puis 1) et, dans chaque palier, Edge, puis XTTS v2, puis Kokoro ;
# une voix notee 0 etoile a l'ecoute est ECARTEE du pool (elle reste
# choisissable a la main). Les etoiles des voix Edge vivent dans FRENCH_VOICES
# et nulle part ailleurs : on les transmet une fois au demarrage, pour que le
# report des notes d'ecoute (test_voix/_appliquer_annotations_voix.py) soit la
# seule chose a mettre a jour quand une note change.
voice_casting.definir_voix_edge(FRENCH_VOICES)

# --- Base de données ---
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    # --- Profils familiaux ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL
        )
    """)
    existing_users = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    if existing_users["n"] == 0:
        conn.execute("INSERT INTO users (name) VALUES ('Laurent')")
        conn.execute("INSERT INTO users (name) VALUES ('Maya')")

    nadia_exists = conn.execute("SELECT COUNT(*) AS n FROM users WHERE name = 'Nadia'").fetchone()
    if nadia_exists["n"] == 0:
        conn.execute("INSERT INTO users (name) VALUES ('Nadia')")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id              INTEGER NOT NULL,
            filename             TEXT NOT NULL,
            title                TEXT,
            author               TEXT,
            cover_path           TEXT,
            date_added           TEXT DEFAULT (datetime('now')),
            multi_voice_enabled  INTEGER DEFAULT 0,
            cast_status          TEXT DEFAULT 'none'
        )
    """)
    # Ajout non destructif de la colonne "saga" -- regroupe des tomes
    # d'une meme oeuvre pour partager le casting entre eux (session du
    # 22/08/2026). NULL = livre autonome, comportement inchange.
    books_cols = [r["name"] for r in conn.execute("PRAGMA table_info(books)").fetchall()]
    if "saga" not in books_cols:
        conn.execute("ALTER TABLE books ADD COLUMN saga TEXT DEFAULT NULL")
    # Ajout non destructif de la colonne "narrator_voice" (17/09/2026, demande
    # de Laurent) : la voix du NARRATEUR choisie pour CE livre. Elle n'etait
    # gardee nulle part -- le menu de la page repartait donc de la voix par
    # defaut a chaque rechargement, alors que Laurent n'utilise pas la meme
    # voix pour Monte-Cristo et pour 22/11/63. NULL = voix par defaut.
    if "narrator_voice" not in books_cols:
        conn.execute("ALTER TABLE books ADD COLUMN narrator_voice TEXT DEFAULT NULL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user_id          INTEGER NOT NULL,
            book_id          INTEGER NOT NULL,
            chapter_index    INTEGER DEFAULT 0,
            scroll_position  INTEGER DEFAULT 0,
            cursor_idx       INTEGER DEFAULT 0,
            last_read        TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, book_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS voices (
            book_id         INTEGER NOT NULL,
            character_name  TEXT NOT NULL,
            voice_id        TEXT NOT NULL,
            pitch           TEXT NOT NULL,
            genre           TEXT DEFAULT 'H',
            line_count      INTEGER DEFAULT 0,
            PRIMARY KEY (book_id, character_name)
        )
    """)
    # Ajout non destructif de la colonne "rate" (vitesse) si elle n'existe
    # pas encore -- evite de supprimer/recreer la base maintenant qu'elle
    # contient de vraies donnees (bibliotheque, progression de lecture).
    voices_cols = [r["name"] for r in conn.execute("PRAGMA table_info(voices)").fetchall()]
    if "rate" not in voices_cols:
        conn.execute("ALTER TABLE voices ADD COLUMN rate TEXT DEFAULT '+0%'")
    # Verrou manuel par personnage (case "garder" de la fenetre du casting) :
    # un personnage verrouille conserve sa voix lors d'un re-cast, les autres
    # sont redistribues dans le catalogue courant (session du 12/09/2026).
    if "locked" not in voices_cols:
        conn.execute("ALTER TABLE voices ADD COLUMN locked INTEGER DEFAULT 0")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS speaker_attribution (
            book_id         INTEGER NOT NULL,
            chapter_index   INTEGER NOT NULL,
            sentence_idx    INTEGER NOT NULL,
            speaker         TEXT NOT NULL,
            PRIMARY KEY (book_id, chapter_index, sentence_idx)
        )
    """)
    # Regroupement d'alias : "ces noms designent la meme personne"
    # (session du 12/09/2026). Le nom principal garde sa fiche ; chaque
    # alias garde sa propre ligne de voix (donc sa voix reste modifiable
    # independamment), mais partage la meme voix de base au moment du
    # regroupement. Table purement descriptive : aucun nom n'est supprime.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS character_aliases (
            book_id         INTEGER NOT NULL,
            alias_name      TEXT NOT NULL,
            canonical_name  TEXT NOT NULL,
            PRIMARY KEY (book_id, alias_name)
        )
    """)
    # Fiche de personnages memorisee au fil de l'analyse multi-voix
    # (session du 13/09/2026). Sans elle, une analyse interrompue en cours
    # de route obligeait a tout refaire -- et donc a tout repayer -- depuis
    # le premier chapitre. Avec elle, la reprise retrouve la fiche exacte
    # du dernier chapitre analyse et repart de la, sans rien recalculer.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cast_fiche (
            book_id         INTEGER NOT NULL,
            character_name  TEXT NOT NULL,
            genre           TEXT DEFAULT 'H',
            age             TEXT DEFAULT 'adulte',
            PRIMARY KEY (book_id, character_name)
        )
    """)
    # Au demarrage du serveur, aucun traitement IA ne peut etre en cours :
    # les taches de fond ne survivent pas a un arret du programme. Un livre
    # laisse en 'processing' par un arret en pleine analyse resterait sinon
    # bloque pour toujours (le bouton refuserait de relancer). On le repasse
    # en 'error' : la reprise repartira du premier chapitre manquant, sans
    # rien recalculer (session du 13/09/2026).
    conn.execute("UPDATE books SET cast_status = 'error' WHERE cast_status LIKE 'processing%'")
    conn.commit()
    conn.close()

# --- Démarrage ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from modules.tts import ensure_kokoro_loaded, ensure_piper_loaded
    ensure_kokoro_loaded()
    ensure_piper_loaded()
    print("NIMM ePub demarre sur http://0.0.0.0:8081")
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.middleware("http")
async def no_cache_api(request, call_next):
    """Empeche tout navigateur de mettre en cache les reponses de l'API,
    quelle que soit la route -- evite les soucis de donnees perimees
    (titres, couvertures, statut du cast...) constates sur Firefox mobile."""
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

# --- Modèles Pydantic ---
class ProgressData(BaseModel):
    chapter_index: int
    scroll_position: int
    cursor_idx: int = 0

class TTSRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE
    rate: str = "+0%"
    pitch: str = "+0Hz"
    # Fin de la phrase PRECEDENTE (facultatif) : donnee au moteur Kyutai pour
    # qu'il ne demarre pas a froid (idee de Laurent, 17/09/2026). Ignoree par
    # les autres moteurs.
    context: str = ""

class VoiceUpdateRequest(BaseModel):
    character_name: str
    voice_id: str
    rate: str = "+0%"
    pitch: str = "+0Hz"

class VoiceLockRequest(BaseModel):
    character_name: str
    locked: bool

class AliasDetachRequest(BaseModel):
    alias_name: str

class AliasGroupRequest(BaseModel):
    alias_name: str
    canonical_name: str

class SagaUpdateRequest(BaseModel):
    saga: str

# ==============================================================
# ROUTES
# ==============================================================

@app.get("/")
async def index():
    return FileResponse(
        str(FRONTEND_DIR / "index.html"),
        headers={"Cache-Control": "no-store"}
    )

@app.get("/sw.js")
async def service_worker():
    return FileResponse(
        str(FRONTEND_DIR / "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )

@app.get("/api/voices")
async def get_voices():
    from modules.tts import (KOKORO_VOICES, PIPER_VOICES, KYUTAI_VOICES,
                             XTTS_VOICES, NEUTTS_VOICES)
    # Seules les voix ECOUTABLES TOUT DE SUITE sont proposees (14/09/2026,
    # demande de Laurent). Edge, Kokoro et Piper le sont toujours ; les voix
    # Kyutai, XTTS v2 et NeuTTS seulement si LEUR moteur est ALLUME ET PRET.
    # Sinon on pouvait en choisir une moteur eteint et ne le decouvrir qu'en
    # plein chapitre. Voir /api/moteurs pour l'etat affiche.
    etat = etat_moteurs_voix()
    voix = FRENCH_VOICES + KOKORO_VOICES + PIPER_VOICES
    if _moteur_voix_pret(etat, "kyutai"):
        voix = voix + KYUTAI_VOICES
    if _moteur_voix_pret(etat, "xtts"):
        voix = voix + XTTS_VOICES
    if _moteur_voix_pret(etat, "neutts"):
        voix = voix + NEUTTS_VOICES
    return voix

@app.get("/api/voix_catalogue")
async def get_voix_catalogue():
    """TOUTES les voix du catalogue, moteurs eteints compris.

    A ne pas confondre avec /api/voices, qui ne propose que les voix ECOUTABLES
    TOUT DE SUITE (decision de Laurent du 14/09/2026). Celle-ci sert a NOMMER :
    une voix deja attribuee a un personnage doit s'afficher
    « Alphonse — France (XTTS) », jamais « xtts:cml9804 ».

    Pourquoi (constat de Laurent, 15/09/2026, apres un re-cast d'un roman contemporain) :
    la fenetre du casting affichait l'identifiant brut des voix XTTS. Cause :
    la liste des voix proposees ne contient les XTTS que si LEUR MOTEUR EST
    PRET, et cette liste peut dater d'avant l'allumage du moteur. Le catalogue
    complet, lui, est toujours joignable.

    Chaque voix porte `famille` (edge, kokoro, piper, kyutai, xtts) et `dispo`
    (lisible tout de suite, ou non).
    """
    from modules.tts import (KOKORO_VOICES, PIPER_VOICES, KYUTAI_VOICES,
                             XTTS_VOICES, NEUTTS_VOICES)
    etat = etat_moteurs_voix()
    dispo = {"kyutai": _moteur_voix_pret(etat, "kyutai"),
             "xtts": _moteur_voix_pret(etat, "xtts"),
             "neutts": _moteur_voix_pret(etat, "neutts")}

    def _famille(identifiant: str) -> str:
        return identifiant.split(":")[0] if ":" in identifiant else "edge"

    voix = (FRENCH_VOICES + KOKORO_VOICES + PIPER_VOICES + KYUTAI_VOICES
            + XTTS_VOICES + NEUTTS_VOICES)
    return [{**v, "famille": _famille(v["id"]),
             "dispo": dispo.get(_famille(v["id"]), True)} for v in voix]


@app.get("/api/moteurs")
async def get_moteurs():
    """Etat des moteurs de voix lourds : Kyutai (8082), XTTS v2 (8083).

    Sert au voyant affiche sous les reglages du lecteur : sans lui, l'absence
    des voix d'un moteur eteint ressemblerait a un bug, et un moteur encore en
    train de charger son modele ressemblerait a une panne.
    """
    return etat_moteurs_voix()


class BasculeMoteurRequest(BaseModel):
    moteur: str        # "xtts", "kyutai" ou "aucun"


@app.post("/api/moteur/basculer")
async def basculer_moteur(request: BasculeMoteurRequest):
    """Allume UN moteur de voix et eteint l'AUTRE -- jamais les deux.

    Appelee par le bouton de bascule du lecteur (le voyant « Voix de
    personnages », sous les reglages). Elle note aussi le choix dans
    data/moteur_voix.txt, pour que START.bat rallume le MEME moteur au prochain
    demarrage. Renvoie l'etat frais des moteurs, pour que le voyant se mette a
    jour tout de suite (sans attendre les 5 s de memoire du serveur).
    """
    resultat = basculer_moteur_voix(request.moteur)
    if not resultat.get("ok"):
        raise HTTPException(status_code=400, detail=resultat.get("message"))
    return resultat

# --- Annotations des voix (fenetre « Ecouter les voix », 14/09/2026) ---
# Permet d'ecouter n'importe quelle voix disponible et de la noter SANS
# toucher au catalogue : c'est ce qui remplace les lots d'ecoute par fichiers.
# Le fichier de notes est local (data/annotations_voix.json, hors Git).
#
# Depuis le 16/09/2026 (demande de Laurent), les annotations ne sont plus
# seulement du texte libre : elles comportent des CRITERES FIXES, choisis dans
# des listes fermees (age, timbre, debit, accent, registre, role). Objectif :
# des annotations calibrees, que l'attribution automatique des voix pourra lire
# plus tard. La remarque libre reste disponible pour les nuances.
#
# Les listes ci-dessous sont la SEULE source de verite : elles sont servies a
# la page par GET /api/annotations_voix/criteres, donc une valeur ajoutee ici
# apparait aussitot dans les menus du lecteur (aucune liste a tenir en double).
# Chaque entree : (cle technique, libelle affiche, [(valeur, libelle), ...]).
CRITERES_VOIX = [
    ("age", "Age percu", [
        ("enfant", "enfant"), ("jeune", "jeune"), ("adulte", "adulte"),
        ("mur", "mûr"), ("vieux", "vieux"),
    ]),
    ("timbre", "Timbre", [
        ("grave", "grave"), ("medium", "médium"), ("aigu", "aigu"),
        ("rocailleux", "rocailleux"), ("cristallin", "cristallin"),
        ("voile", "voilé"),
    ]),
    ("debit", "Debit", [
        ("lent", "lent"), ("pose", "posé"), ("normal", "normal"),
        ("vif", "vif"),
    ]),
    ("accent", "Accent", [
        ("neutre", "neutre"), ("paysan", "paysan"), ("canadien", "canadien"),
        ("anglais", "anglais"), ("allemand", "allemand"),
        ("espagnol", "espagnol"), ("italien", "italien"), ("autre", "autre"),
    ]),
    ("registre", "Registre", [
        ("noble", "noble"), ("neutre", "neutre"), ("populaire", "populaire"),
        ("savant", "savant"),
    ]),
    ("role", "Role reserve", [
        ("narrateur", "narrateur"), ("enfant", "enfant"), ("vieux", "vieux"),
        ("etranger", "étranger"), ("secondaire", "secondaire"),
    ]),
]
CRITERES_VOIX_CLES = [cle for cle, _, _ in CRITERES_VOIX]
CRITERES_VOIX_VALEURS = {cle: [v for v, _ in valeurs]
                         for cle, _, valeurs in CRITERES_VOIX}


def _lire_annotations_voix() -> dict:
    if ANNOTATIONS_VOIX_PATH.exists():
        try:
            donnees = json.loads(ANNOTATIONS_VOIX_PATH.read_text(encoding="utf-8"))
            return donnees if isinstance(donnees, dict) else {}
        except Exception:
            return {}
    return {}


def _ecrire_annotations_voix(annotations: dict):
    ANNOTATIONS_VOIX_PATH.write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


class AnnotationVoixRequest(BaseModel):
    voice_id: str
    genre: str = ""     # "H", "F" ou "" (non renseigne)
    stars: int = -1     # -1 = non renseigne ; 0 = a ecarter ; 1 a 3 = note
    note: str = ""      # remarque libre, en complement des criteres fixes
    # Criteres FIXES (voir CRITERES_VOIX) : "" = non renseigne.
    age: str = ""
    timbre: str = ""
    debit: str = ""
    accent: str = ""
    registre: str = ""
    role: str = ""


@app.get("/api/annotations_voix")
async def get_annotations_voix():
    """Notes prises par Laurent en ecoutant les voix (dict indexe par voix)."""
    return _lire_annotations_voix()


@app.get("/api/annotations_voix/criteres")
async def get_criteres_voix():
    """Listes FERMEES des criteres d'annotation d'une voix.

    Source de verite unique : la page construit ses menus deroulants a partir
    de cette reponse, donc les valeurs proposees sont exactement celles que le
    serveur accepte (aucune liste a tenir en double).
    """
    return [
        {"cle": cle, "libelle": libelle,
         "valeurs": [{"valeur": v, "libelle": l} for v, l in valeurs]}
        for cle, libelle, valeurs in CRITERES_VOIX
    ]


@app.post("/api/annotations_voix")
async def set_annotation_voix(request: AnnotationVoixRequest):
    """Enregistre (ou efface) l'annotation d'une voix.

    Une annotation entierement vide est SUPPRIMEE : le catalogue reprend alors
    ses propres valeurs, comme si rien n'avait ete annote.

    Les criteres fixes sont VERIFIES : une valeur hors liste est refusee
    (erreur 400), pour que le fichier de notes reste exploitable par la machine
    (l'attribution automatique des voix lira ces criteres).
    """
    if not request.voice_id:
        raise HTTPException(status_code=400, detail="voice_id manquant")

    criteres = {
        "age": request.age.strip(),
        "timbre": request.timbre.strip(),
        "debit": request.debit.strip(),
        "accent": request.accent.strip(),
        "registre": request.registre.strip(),
        "role": request.role.strip(),
    }
    for cle, valeur in criteres.items():
        if valeur and valeur not in CRITERES_VOIX_VALEURS[cle]:
            raise HTTPException(
                status_code=400,
                detail="valeur inconnue pour « %s » : %s" % (cle, valeur))

    annotations = _lire_annotations_voix()
    vide = (not request.genre.strip() and request.stars < 0
            and not request.note.strip()
            and not any(criteres.values()))
    if vide:
        annotations.pop(request.voice_id, None)
    else:
        entree = {
            "genre": request.genre.strip(),
            "stars": int(request.stars),
            "note": request.note.strip(),
        }
        entree.update(criteres)
        annotations[request.voice_id] = entree
    _ecrire_annotations_voix(annotations)
    return {"ok": True, "annotations": annotations}


# --- Profils ---

@app.get("/api/users")
async def list_users():
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Bibliothèque ---

@app.get("/api/books")
async def list_books(user_id: int):
    conn = get_db()
    rows = conn.execute("""
        SELECT b.*, p.chapter_index, p.last_read
        FROM books b
        LEFT JOIN progress p ON b.id = p.book_id AND p.user_id = b.user_id
        WHERE b.user_id = ?
        ORDER BY p.last_read DESC, b.date_added DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/books/upload")
async def upload_book(user_id: int, file: UploadFile = File(...)):
    if not file.filename.endswith(".epub"):
        raise HTTPException(400, "Format accepte : .epub uniquement")

    dest = LIBRARY_DIR / file.filename
    with open(str(dest), "wb") as f:
        shutil.copyfileobj(file.file, f)

    from core.epub_parser import get_metadata
    meta = get_metadata(str(dest))

    cover_path = None
    cover_bytes = meta.get("cover_bytes")
    if cover_bytes:
        cover_ext = sniff_image_type(cover_bytes)
        if cover_ext:
            cover_filename = Path(file.filename).stem + "_cover." + cover_ext
            cover_dest = LIBRARY_DIR / cover_filename
            with open(str(cover_dest), "wb") as f:
                f.write(cover_bytes)
            cover_path = cover_filename

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO books (user_id, filename, title, author, cover_path) VALUES (?, ?, ?, ?, ?)",
        (user_id, file.filename, meta.get("title", file.filename),
         meta.get("author", "Auteur inconnu"), cover_path)
    )
    book_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"id": book_id, "title": meta.get("title"), "author": meta.get("author")}

@app.delete("/api/books/{book_id}")
async def delete_book(book_id: int, user_id: int):
    conn = get_db()
    book = conn.execute(
        "SELECT * FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")
    book = dict(book)
    epub_path = LIBRARY_DIR / book["filename"]
    if epub_path.exists():
        epub_path.unlink()
    if book["cover_path"]:
        cover_path = LIBRARY_DIR / book["cover_path"]
        if cover_path.exists():
            cover_path.unlink()
    conn.execute("DELETE FROM books WHERE id = ? AND user_id = ?", (book_id, user_id))
    conn.execute("DELETE FROM progress WHERE book_id = ? AND user_id = ?", (book_id, user_id))
    conn.commit()
    conn.close()
    return {"ok": True}

# --- Lecture ---

@app.get("/api/books/{book_id}")
async def get_book(book_id: int, user_id: int):
    conn = get_db()
    book = conn.execute(
        "SELECT * FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    conn.close()
    if not book:
        raise HTTPException(404, "Livre introuvable")
    book = dict(book)
    epub_path = str(LIBRARY_DIR / book["filename"])
    from core.epub_parser import get_chapters
    chapters = get_chapters(epub_path)
    book["chapters"] = [{"index": c["index"], "title": c["title"], "word_count": len(c["text"].split())} for c in chapters]
    book["chapter_count"] = len(chapters)

    conn = get_db()
    voice_rows = conn.execute(
        "SELECT character_name, voice_id, pitch, rate, genre, line_count, locked FROM voices WHERE book_id = ?", (book_id,)
    ).fetchall()
    alias_rows = conn.execute(
        "SELECT alias_name, canonical_name FROM character_aliases WHERE book_id = ?", (book_id,)
    ).fetchall()
    conn.close()
    book["voices"] = {
        row["character_name"]: {
            "voice_id": row["voice_id"],
            "pitch": row["pitch"],
            "rate": row["rate"] or "+0%",
            "genre": row["genre"],
            "line_count": row["line_count"],
            "locked": row["locked"] or 0
        }
        for row in voice_rows
    }
    # alias -> nom principal (regroupement affiche dans la fenetre du casting)
    book["aliases"] = {row["alias_name"]: row["canonical_name"] for row in alias_rows}

    return book


class NarratorVoiceRequest(BaseModel):
    """Voix du narrateur choisie pour un livre."""
    voice: str = ""


@app.put("/api/books/{book_id}/narrator")
async def set_narrator_voice(book_id: int, demande: NarratorVoiceRequest,
                             user_id: int):
    """Retient la voix du NARRATEUR pour CE livre.

    Demande de Laurent (17/09/2026) : le menu de la page n'etait sauvegarde
    nulle part, et il n'utilise pas la meme voix de narration d'un livre a
    l'autre. La valeur voyage avec le LIVRE (et son proprietaire), pas avec
    l'appareil : elle suit donc d'un appareil a l'autre.
    """
    conn = get_db()
    conn.execute(
        "UPDATE books SET narrator_voice = ? WHERE id = ? AND user_id = ?",
        (demande.voice, book_id, user_id))
    conn.commit()
    conn.close()
    return {"ok": True, "narrator_voice": demande.voice}

@app.get("/api/books/{book_id}/chapter/{chapter_index}")
async def get_chapter(book_id: int, chapter_index: int, user_id: int):
    conn = get_db()
    book = conn.execute(
        "SELECT * FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    conn.close()
    if not book:
        raise HTTPException(404, "Livre introuvable")
    epub_path = str(LIBRARY_DIR / book["filename"])
    from core.epub_parser import get_chapter
    chapter = get_chapter(epub_path, chapter_index)
    if chapter is None:
        raise HTTPException(404, "Chapitre introuvable")

    conn = get_db()
    speaker_rows = conn.execute(
        "SELECT sentence_idx, speaker FROM speaker_attribution WHERE book_id = ? AND chapter_index = ?",
        (book_id, chapter_index)
    ).fetchall()
    conn.close()
    chapter["speakers"] = {
        row["sentence_idx"]: row["speaker"] for row in speaker_rows
    }

    return chapter

# --- Distribution de voix par personnage (IA) ---

# --- Moteur de voix Kyutai et analyse locale : la bataille pour la carte ---
# Le moteur de voix Kyutai occupe environ 5,6 Go des 8 Go de memoire video.
# Un modele de langage local en a besoin de 5 a 6 Go : les deux ne peuvent pas
# cohabiter. Pendant une analyse en LOCAL, on eteint donc le moteur de voix
# (on n'ecoute pas de livre pendant ce temps), et on le rallume a la fin
# (session du 13/09/2026, demande de Laurent).
# Un casting en ligne (Gemini, DeepSeek, Mistral) ne touche a RIEN : le texte
# part sur internet, la carte reste libre.

KYUTAI_URL = "http://127.0.0.1:8082/sante"
XTTS_URL = "http://127.0.0.1:8083/sante"
NEUTTS_URL = "http://127.0.0.1:8084/sante"
_kyutai_coupe_pour_casting = False


def _moteur_voix_actif(prefixe: str) -> bool:
    """Le moteur repond-il ? (donc occupe-t-il deja la carte graphique ?)"""
    try:
        urllib.request.urlopen(MOTEURS_VOIX[prefixe]["sante"], timeout=2).read()
        return True
    except Exception:
        return False


def _moteur_kyutai_actif() -> bool:
    """Le moteur de voix Kyutai repond-il ? (donc occupe-t-il la carte ?)"""
    return _moteur_voix_actif("kyutai")


# --- Quelles voix sont ECOUTABLES tout de suite ? (session du 14/09/2026) ---
# Demande de Laurent : les menus ne doivent proposer que des voix qu'on peut
# ecouter immediatement. Avant, les 35 voix Kyutai etaient listees en
# permanence : on pouvait en choisir une moteur eteint et ne le decouvrir qu'en
# plein chapitre (erreur 503 bien expliquee, mais au mauvais moment).
#
# Les moteurs LEGERS n'ont aucun service a allumer -> leurs voix sont toujours
# proposees : Edge (en ligne), Kokoro et Piper (processeur).
# Les moteurs LOURDS doivent etre ALLUMES **et PRETS** (modele charge, donc
# /sante renvoie « pret: true ») : Kyutai sur le port 8082, XTTS v2 sur 8083.
# Rappel : un seul des deux peut tourner a la fois (carte graphique).

# Fiche de chaque moteur de voix LOURD : nom affiche, adresse de sante, dossier
# et lanceur (exactement ceux de START.bat), et les motifs qui permettent de
# RETROUVER ses processus. On ne tue jamais un python au hasard : on cible la
# ligne de commande (le serveur, ou la fenetre de console qui l'heberge).
MOTEURS_VOIX = {
    "kyutai": {"nom": "Kyutai",  "sante": KYUTAI_URL,
               "dossier": "kyutai_service", "lanceur": "DEMARRER_KYUTAI.bat",
               "motifs": ("servir_kyutai", "DEMARRER_KYUTAI")},
    "xtts":   {"nom": "XTTS v2", "sante": XTTS_URL,
               "dossier": "xtts_service", "lanceur": "DEMARRER_XTTS.bat",
               "motifs": ("servir_xtts", "DEMARRER_XTTS")},
    "neutts": {"nom": "NeuTTS", "sante": NEUTTS_URL,
               "dossier": "neutts_service", "lanceur": "DEMARRER_NEUTTS.bat",
               "motifs": ("servir_neutts", "DEMARRER_NEUTTS")},
}

# Le pense-bete du DERNIER moteur utilise. Il est ecrit par les deux lanceurs de
# moteur et relu par START.bat : c'est ce qui fait revenir le bon moteur au
# prochain demarrage (demande de Laurent, 14/09/2026). Le bouton de bascule du
# lecteur ecrit ici, lui aussi.
MOTEUR_VOIX_PATH = DATA_DIR / "moteur_voix.txt"

# Le resultat est garde 5 s en memoire : /api/voices et /api/moteurs sont
# appeles a chaque affichage de menu, on ne va pas interroger les services
# a chaque fois (et un moteur eteint fait attendre 1 s avant d'abandonner).
_ETAT_MOTEURS = {"quand": 0.0, "etat": None}
ETAT_MOTEURS_TTL_S = 5.0


def _sante_moteur(sante: str) -> dict:
    """Interroge le /sante d'un moteur : repond-il ? a-t-il fini de charger ?

    `actif` = le service repond (il charge peut-etre encore son modele) ;
    `pret`  = le modele est charge, donc ses voix peuvent vraiment etre lues.
    """
    try:
        with urllib.request.urlopen(sante, timeout=1) as reponse:
            infos = json.loads(reponse.read().decode("utf-8", "replace"))
        return {"actif": True, "pret": bool(infos.get("pret"))}
    except Exception:
        return {"actif": False, "pret": False}


def etat_moteurs_voix(force: bool = False) -> dict:
    """Etat des moteurs de voix lourds : {prefixe: {nom, actif, pret}}."""
    maintenant = time.time()
    if (not force and _ETAT_MOTEURS["etat"] is not None
            and maintenant - _ETAT_MOTEURS["quand"] < ETAT_MOTEURS_TTL_S):
        return _ETAT_MOTEURS["etat"]

    etat = {}
    for prefixe, infos in MOTEURS_VOIX.items():
        detail = _sante_moteur(infos["sante"])
        detail["nom"] = infos["nom"]
        etat[prefixe] = detail

    _ETAT_MOTEURS["quand"] = maintenant
    _ETAT_MOTEURS["etat"] = etat
    return etat


def _moteur_voix_pret(etat: dict, prefixe: str) -> bool:
    """Les voix de ce moteur peuvent-elles etre lues tout de suite ?"""
    return bool((etat.get(prefixe) or {}).get("pret"))


def _pids_moteur_voix(prefixe: str) -> list:
    """PIDs des processus d'un moteur : le serveur lui-meme (servir_kyutai.py,
    servir_xtts.py) et la fenetre de console qui l'heberge (DEMARRER_KYUTAI.bat,
    DEMARRER_XTTS.bat). Les deux sont necessaires : tuer la fenetre avec ses
    enfants ferme aussi le moteur proprement. On cible la LIGNE DE COMMANDE :
    jamais un python au hasard."""
    motifs = MOTEURS_VOIX[prefixe]["motifs"]
    cible = ("Get-CimInstance Win32_Process | Where-Object { "
             + " -or ".join("$_.CommandLine -like '*{}*'".format(m) for m in motifs)
             + " } | Select-Object -ExpandProperty ProcessId")
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', cible],
                           capture_output=True, text=True, timeout=25)
        return [int(x) for x in r.stdout.split() if x.strip().isdigit()]
    except Exception as e:
        print("   Impossible de reperer le moteur {} : {}".format(
            MOTEURS_VOIX[prefixe]["nom"], str(e)[:120]))
        return []


def _arreter_moteur_voix(prefixe: str) -> bool:
    """Eteint un moteur de voix pour liberer la memoire video."""
    pids = _pids_moteur_voix(prefixe)
    if not pids:
        return False
    for pid in pids:
        # /T tue aussi les processus enfants (le serveur python).
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)],
                       capture_output=True, text=True)
    return True


def _relancer_moteur_voix(prefixe: str) -> bool:
    """Rallume un moteur de voix dans sa propre fenetre, exactement comme le
    fait START.bat (meme dossier, meme lanceur, meme titre de fenetre)."""
    infos = MOTEURS_VOIX[prefixe]
    dossier = BASE_DIR / infos["dossier"]
    bat = dossier / infos["lanceur"]
    if not bat.exists():
        return False
    try:
        subprocess.Popen(
            'start "NIMM ePub - moteur de voix {}" /D "{}" cmd /k {}'.format(
                infos["nom"], dossier, infos["lanceur"]),
            shell=True, cwd=str(dossier))
        return True
    except Exception as e:
        print("   Impossible de relancer le moteur {} : {}".format(
            infos["nom"], str(e)[:120]))
        return False


# Noms historiques : le moteur Kyutai etait le seul pilotable a ses debuts
# (analyse locale en repli). On les garde pour ne rien casser.
def _pids_moteur_kyutai() -> list:
    return _pids_moteur_voix("kyutai")


def _arreter_moteur_kyutai() -> bool:
    return _arreter_moteur_voix("kyutai")


def _relancer_moteur_kyutai() -> bool:
    return _relancer_moteur_voix("kyutai")
# --- Changer de moteur de voix : UN SEUL a la fois (15/09/2026) ---
# Demande de Laurent : un bouton sous les reglages du lecteur pour passer d'un
# moteur a l'autre, « soit l'un, soit l'autre ». Raison technique : Kyutai et
# XTTS v2 occupent chacun environ 3,8 Go de carte graphique, les deux ensemble
# ne tiennent pas (mesure du 15/09/2026 : 7,6 Go sur 8). C'est aussi la reponse
# au mauvais moteur qui se lancait tout seul : plus rien ne s'allume sans que
# Laurent l'ait demande, et l'autre est TOUJOURS eteint avant.

def _moteur_voix_installe(prefixe: str) -> bool:
    """Le moteur est-il installe sur ce PC ? Meme controle que START.bat :
    sans son environnement, son lanceur ne pourrait rien demarrer."""
    return (BASE_DIR / MOTEURS_VOIX[prefixe]["dossier"] / ".venv" / "Scripts"
            / "python.exe").exists()


def _ecrire_moteur_retenu(valeur: str) -> None:
    """Note le choix pour le PROCHAIN demarrage : c'est ce fichier que START.bat
    relit (meme pense-bete que les deux lanceurs de moteur)."""
    try:
        MOTEUR_VOIX_PATH.write_text(valeur + "\n", encoding="utf-8")
    except Exception as e:
        print("   Impossible d'enregistrer le moteur de voix retenu : {}".format(
            str(e)[:120]))


def _attendre_extinction(prefixe: str, secondes: float = 20.0) -> bool:
    """Attend qu'un moteur ait vraiment rendu la carte graphique.

    Le port se ferme quand le processus est parti : on attend sa disparition
    AVANT d'allumer l'autre, sinon les deux se croiseraient en memoire video.
    """
    fin = time.time() + secondes
    while time.time() < fin:
        if not _moteur_voix_actif(prefixe):
            return True
        time.sleep(0.5)
    return not _moteur_voix_actif(prefixe)


def basculer_moteur_voix(cible: str) -> dict:
    """Allume UN moteur de voix et eteint l'AUTRE -- jamais les deux.

    `cible` : "xtts", "kyutai" ou "aucun" (demarrer sans moteur lourd).
    Renvoie toujours un compte rendu lisible, jamais une exception : c'est le
    bouton de bascule du lecteur qui appelle cette fonction.
    """
    cible = (cible or "").strip().lower()
    if cible != "aucun" and cible not in MOTEURS_VOIX:
        return {"ok": False,
                "message": "Moteur de voix inconnu : {}".format(cible or "(vide)")}

    etat = etat_moteurs_voix(force=True)
    messages = []

    # 1. Eteindre ce qui doit l'etre : l'AUTRE moteur, ou les deux pour "aucun".
    a_eteindre = (list(MOTEURS_VOIX) if cible == "aucun"
                  else [p for p in MOTEURS_VOIX if p != cible])
    eteints = []
    for prefixe in a_eteindre:
        if not (etat.get(prefixe) or {}).get("actif"):
            continue
        nom = MOTEURS_VOIX[prefixe]["nom"]
        if _arreter_moteur_voix(prefixe) and _attendre_extinction(prefixe):
            eteints.append(nom)
        else:
            # On refuse d'allumer quoi que ce soit : deux moteurs ne tiennent
            # pas ensemble sur la carte graphique.
            return {"ok": False, "moteur": cible,
                    "message": ("{} tourne encore et n'a pas pu etre eteint : "
                                "rien n'a ete allume".format(nom))}
    if eteints:
        messages.append(" et ".join(eteints) + " eteint")

    # 2. Allumer le moteur demande... s'il ne tourne pas deja.
    demarre = False
    if cible in MOTEURS_VOIX:
        infos = MOTEURS_VOIX[cible]
        frais = (etat_moteurs_voix(force=True).get(cible) or {})
        if frais.get("pret"):
            messages.append(infos["nom"] + " etait deja pret")
        elif frais.get("actif"):
            messages.append(infos["nom"] + " finit de charger")
        elif not _moteur_voix_installe(cible):
            return {"ok": False, "moteur": cible,
                    "message": "{} n'est pas installe sur ce PC".format(infos["nom"])}
        elif _relancer_moteur_voix(cible):
            demarre = True
            messages.append(infos["nom"]
                            + " demarre, pret dans une quinzaine de secondes")
        else:
            return {"ok": False, "moteur": cible,
                    "message": "Impossible de demarrer {}".format(infos["nom"])}
    elif cible == "aucun" and not eteints:
        messages.append("aucun moteur ne tournait")

    # 3. Noter le choix : c'est ce que START.bat relira au prochain demarrage.
    _ecrire_moteur_retenu(cible)

    return {"ok": True, "moteur": cible, "demarre": demarre,
            "message": " ; ".join(messages) if messages else "rien a faire",
            "etat": etat_moteurs_voix(force=True)}





def _liberer_la_carte_pour_analyse_locale() -> None:
    """Avant une analyse en LOCAL : eteint le moteur de voix s'il tourne, et
    retient qu'on l'a fait (pour pouvoir le rallumer ensuite)."""
    global _kyutai_coupe_pour_casting
    if not _moteur_kyutai_actif():
        return
    if _arreter_moteur_kyutai():
        _kyutai_coupe_pour_casting = True
        print("Moteur de voix Kyutai eteint : la carte graphique est liberee "
              "pour l'analyse locale (il sera rallume a la fin).")


def _restaurer_moteur_kyutai() -> None:
    """Apres une analyse locale : rallume le moteur de voix, mais seulement
    si c'est NOUS qui l'avions eteint, et s'il ne tourne pas deja (au cas ou
    Laurent l'aurait rallume entre-temps)."""
    global _kyutai_coupe_pour_casting
    if not _kyutai_coupe_pour_casting:
        return
    _kyutai_coupe_pour_casting = False
    if _moteur_kyutai_actif():
        return
    if _relancer_moteur_kyutai():
        print("Analyse terminee : moteur de voix Kyutai rallume.")


# --- Reprise d'un casting interrompu (session du 13/09/2026) ---
# Objectif : ne JAMAIS refaire payer un chapitre deja analyse. L'attribution
# etant enregistree chapitre par chapitre, la base suffit a savoir ou
# l'analyse s'est arretee ; la fiche de personnages, elle, est memorisee
# dans la table cast_fiche pour que la reprise reparte avec la meme fiche
# que celle qu'avait l'IA au moment de l'interruption.

def _chapitres_deja_traites(conn, book_id: int) -> set:
    """Index des chapitres deja analyses -- donc deja payes."""
    rows = conn.execute(
        "SELECT DISTINCT chapter_index FROM speaker_attribution WHERE book_id = ?",
        (book_id,)
    ).fetchall()
    return {row["chapter_index"] for row in rows}


def _sauver_fiche(conn, book_id: int, personnages: list) -> None:
    """Memorise la fiche de personnages construite par l'IA."""
    for perso in personnages or []:
        nom = (perso.get("nom") or "").strip()
        if not nom:
            continue
        conn.execute("""
            INSERT INTO cast_fiche (book_id, character_name, genre, age)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(book_id, character_name) DO UPDATE SET
                genre = excluded.genre,
                age   = excluded.age
        """, (book_id, nom, perso.get("genre", "H"), perso.get("age", "adulte")))


def _journaliser_erreur_casting(book_id: int, erreur, chapitre=None) -> str:
    """
    Conserve la raison d'un echec de casting dans
    data/journal_erreurs_casting.log (session du 14/09/2026).

    Pourquoi : le message n'apparaissait que dans la console du serveur, donc
    il etait perdu des que Laurent ne l'avait pas sous les yeux. Avec ce
    journal, on peut diagnostiquer un echec a posteriori, sans refaire d'appel
    payant.
    """
    try:
        chemin = DATA_DIR / "journal_erreurs_casting.log"
        with open(chemin, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 72 + "\n")
            f.write("{}  livre {}  {}\n".format(
                time.strftime("%Y-%m-%d %H:%M:%S"), book_id,
                "chapitre {}".format(chapitre) if chapitre is not None else ""))
            f.write("Erreur : {}\n".format(erreur))
            f.write(traceback.format_exc()[:4000] + "\n")
        return str(chemin)
    except Exception:
        return ""


def _fiche_de_la_saga(conn, saga: str, user_id: int, exclude_book_id: int) -> list:
    """
    Fiche de personnages construite a partir des AUTRES tomes de la meme saga
    (session du 14/09/2026).

    Sans cela, un tome neuf repart d'une fiche VIDE : le modele reinvente les
    noms (« Albert » au lieu d'« Albert de Morcerf »), le personnage n'est donc
    pas reconnu a l'heure d'attribuer les voix, et il en recoit une NOUVELLE --
    alors que la saga est justement faite pour eviter cela. Mesure du
    14/09/2026 sur le tome 5 de Monte-Cristo : 32 personnages sur 42
    consideres comme nouveaux, faute de fiche heritee.
    """
    if not saga:
        return []
    rows = conn.execute("""
        SELECT v.character_name AS nom, v.genre AS genre
        FROM voices v JOIN books b ON b.id = v.book_id
        WHERE b.saga = ? AND b.user_id = ? AND b.id != ?
        GROUP BY v.character_name
        ORDER BY v.character_name
    """, (saga, user_id, exclude_book_id)).fetchall()
    return [{"nom": row["nom"], "genre": row["genre"] or "H", "age": "adulte"}
            for row in rows]


def _charger_fiche(conn, book_id: int) -> list:
    """Fiche de personnages memorisee (liste vide si aucune)."""
    rows = conn.execute(
        "SELECT character_name, genre, age FROM cast_fiche WHERE book_id = ? ORDER BY character_name",
        (book_id,)
    ).fetchall()
    return [{"nom": r["character_name"], "genre": r["genre"], "age": r["age"]} for r in rows]


def _fiche_de_secours(conn, book_id: int) -> list:
    """Fiche reconstruite a partir des noms deja attribues, quand la fiche
    d'origine n'a pas ete memorisee (cas du tout premier plantage, anterieur
    a l'ajout de la table cast_fiche). Le genre est alors devine d'apres le
    prenom -- une erreur de genre ne change qu'une voix, et se corrige a la
    main dans la fenetre du casting."""
    from modules.voice_casting import deviner_genre
    rows = conn.execute("""
        SELECT speaker AS nom, COUNT(*) AS nb FROM speaker_attribution
        WHERE book_id = ? AND speaker != 'narration'
        GROUP BY speaker ORDER BY nb DESC
    """, (book_id,)).fetchall()
    return [{"nom": r["nom"], "genre": deviner_genre(r["nom"]), "age": "adulte"} for r in rows]


def _charger_resultats_en_base(conn, book_id: int) -> dict:
    """Relit en base l'attribution des chapitres deja traites, sous la meme
    forme que les resultats renvoyes par l'IA. Indispensable pour que la
    Passe 2 (fusion des noms) s'applique AUSSI a ces chapitres, et pour que
    la reecriture finale en base reste complete."""
    rows = conn.execute("""
        SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution
        WHERE book_id = ? ORDER BY chapter_index, sentence_idx
    """, (book_id,)).fetchall()
    par_chapitre = {}
    for r in rows:
        par_chapitre.setdefault(r["chapter_index"], []).append(
            {"id": r["sentence_idx"], "locuteur": r["speaker"]}
        )
    return {
        idx: {"personnages": [], "phrases": phrases}
        for idx, phrases in par_chapitre.items()
    }


def _save_attribution(conn, book_id: int, chapter_index: int, phrases: list) -> None:
    """Enregistre le locuteur de chaque phrase d'un chapitre en base."""
    for p in phrases:
        conn.execute("""
            INSERT INTO speaker_attribution (book_id, chapter_index, sentence_idx, speaker)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(book_id, chapter_index, sentence_idx) DO UPDATE SET speaker = excluded.speaker
        """, (book_id, chapter_index, p["id"], p.get("locuteur", "narration")))
    conn.commit()


async def _process_remaining_chapters(book_id: int, chapters: list, fiche_depart: list, premier_resultat: dict, premier_index: int, provider: str = "gemini", voix_figees: dict = None) -> None:
    """
    Tache de fond : analyse les chapitres qui n'ont pas encore d'attribution
    (le premier d'entre eux -- premier_index -- a deja ete traite et
    sauvegarde avant l'appel a cette fonction, de facon synchrone, pour la
    barre de progression visible cote UI).
    Les chapitres deja en base, meme issus d'un lancement precedent
    interrompu, ne sont JAMAIS reanalyses : ils sont relus tels quels
    (session du 13/09/2026 -- on ne paie jamais deux fois le meme chapitre).
    Une fois tous les chapitres traites, lance la Passe 2 (fusion des
    doublons + attribution des voix) et enregistre le resultat final.
    premier_resultat / premier_index valent None quand l'analyse reprend
    alors que tous les chapitres sont deja en base : il ne reste plus que
    la Passe 2 a faire.
    """
    from modules import voice_casting

    total = len(chapters)

    conn = get_db()
    resultats_base = _charger_resultats_en_base(conn, book_id)
    conn.close()

    # Un emplacement par chapitre, dans l'ordre du livre : rempli soit par la
    # relecture en base (deja paye), soit par le chapitre fait en direct,
    # soit laisse vide pour l'analyse a venir.
    resultats = [None] * total
    for i, chapter in enumerate(chapters):
        if premier_index is not None and chapter["index"] == premier_index:
            resultats[i] = premier_resultat
        elif chapter["index"] in resultats_base:
            resultats[i] = resultats_base[chapter["index"]]

    fiche = fiche_depart
    faits = sum(1 for r in resultats if r is not None)

    try:
        # La fiche est memorisee des maintenant : si l'analyse s'arrete ici,
        # une reprise repartira de la fiche exacte du dernier chapitre
        # analyse, au lieu de la reconstruire a l'aveugle.
        conn = get_db()
        _sauver_fiche(conn, book_id, fiche)
        conn.execute(
            "UPDATE books SET cast_status = ? WHERE id = ?",
            (f"processing:{faits}/{total}", book_id)
        )
        conn.commit()
        conn.close()

        for i, chapter in enumerate(chapters):
            if resultats[i] is not None:
                continue  # deja paye lors d'un lancement precedent

            result = await voice_casting.analyze_chapter(
                chapter["text"], fiche_personnages=fiche, provider=provider,
                provider_repli=MOTEURS_DE_SECOURS,
            )
            fiche = result["personnages"]
            resultats[i] = result
            faits += 1

            conn = get_db()
            _save_attribution(conn, book_id, chapter["index"], result["phrases"])
            _sauver_fiche(conn, book_id, fiche)
            conn.execute(
                "UPDATE books SET cast_status = ? WHERE id = ?",
                (f"processing:{faits}/{total}", book_id)
            )
            conn.commit()
            conn.close()

        # fiche_brute est transmise explicitement : sur une reprise, la fiche
        # ne peut pas etre deduite des resultats, puisque les chapitres relus
        # en base ne portent pas de fiche de personnages.
        consolidation = await voice_casting.consolidate_book(
            resultats, provider=provider, voix_figees=voix_figees, fiche_brute=fiche or None
        )
        if not consolidation.get("voix"):
            raise RuntimeError("Passe 2 sans voix generee (fiche vide ou reponse IA incomplete)")

        conn = get_db()
        # La fusion des doublons a deja ete appliquee en memoire a
        # 'resultats' par consolidate_book -- on reecrit donc l'attribution
        # complete en base pour que les noms de personnages soient definitifs.
        conn.execute("DELETE FROM speaker_attribution WHERE book_id = ?", (book_id,))
        for chapter, result in zip(chapters, resultats):
            _save_attribution(conn, book_id, chapter["index"], result["phrases"])

        conn.execute("DELETE FROM voices WHERE book_id = ?", (book_id,))
        for nom, v in consolidation["voix"].items():
            conn.execute(
                "INSERT INTO voices (book_id, character_name, voice_id, pitch, rate, genre, line_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (book_id, nom, v["voice_id"], v["pitch"], v.get("rate", "+0%"), v.get("genre", "H"), v.get("line_count", 0))
            )

        # Cout reel mesure (session du 13/09/2026). Le fournisseur annonce
        # lui-meme ses tokens, y compris ceux de reflexion que l'estimation
        # d'avant-lancement ne comptait pas : on les affiche pour pouvoir
        # comparer avec la facture reelle.
        t = voice_casting.tokens_session(provider)
        print("Tokens IA mesures : {} appels | entree {} | sortie {} | reflexion {} "
              "-> ~{:.2f} $ estimes (tarifs de reference de l'app)".format(
                  t["appels"], t["entree"], t["sortie"], t["reflexion"], t["cout_usd_estime"]))

        conn.execute("UPDATE books SET cast_status = 'done' WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()

    except Exception as e:
        conn = get_db()
        conn.execute("UPDATE books SET cast_status = 'error' WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()
        _journaliser_erreur_casting(book_id, e)
        print(f"Erreur casting voix (livre {book_id}) : {e}")

    finally:
        # Quoi qu'il arrive -- succes ou echec -- on rallume le moteur de voix
        # s'il avait ete eteint pour liberer la carte pendant cette analyse.
        _restaurer_moteur_kyutai()


@app.get("/api/books/{book_id}/cover")
async def get_cover(book_id: int, user_id: int):
    conn = get_db()
    book = conn.execute(
        "SELECT cover_path FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    conn.close()
    if not book or not book["cover_path"]:
        raise HTTPException(404, "Couverture introuvable")
    cover_path = LIBRARY_DIR / book["cover_path"]
    if not cover_path.exists():
        raise HTTPException(404, "Couverture introuvable")

    # Le type MIME est deduit du contenu reel du fichier, pas de son
    # extension : certains fichiers sont des PNG stockes avec .jpg.
    with open(str(cover_path), "rb") as f:
        head = f.read(16)
    ext = sniff_image_type(head)
    media = {
        "png":  "image/png",
        "jpg":  "image/jpeg",
        "gif":  "image/gif",
        "webp": "image/webp",
    }.get(ext)
    if media:
        return FileResponse(str(cover_path), media_type=media, headers={"Cache-Control": "no-store"})
    return FileResponse(str(cover_path), headers={"Cache-Control": "no-store"})

def _fetch_saga_voix_figees(conn, saga: str, user_id: int, exclude_book_id: int) -> dict:
    """
    Recupere les voix deja figees sur les autres tomes de la meme saga
    (le tome le plus anciennement ajoute fait reference en cas de
    divergence). Cle = nom de personnage exact (session du 22/08/2026).
    """
    if not saga:
        return {}
    rows = conn.execute(
        """
        SELECT v.character_name, v.voice_id, v.pitch, v.rate, v.genre
        FROM voices v
        JOIN books b ON v.book_id = b.id
        WHERE b.saga = ? AND b.user_id = ? AND b.id != ?
        ORDER BY b.date_added ASC, b.id ASC
        """,
        (saga, user_id, exclude_book_id)
    ).fetchall()
    figees = {}
    for row in rows:
        figees.setdefault(row["character_name"], {
            "voice_id": row["voice_id"],
            "pitch": row["pitch"],
            "rate": row["rate"] or "+0%",
            "genre": row["genre"],
        })
    return figees


@app.get("/api/llm/local")
async def local_engine_status():
    """
    Etat du moteur de langage LOCAL (Ollama) : l'interface s'en sert pour
    proposer -- ou desactiver -- le choix « modele local » dans la fenetre de
    selection du moteur, et pour expliquer quoi faire si Ollama ne repond pas
    (session du 13/09/2026). Aucun appel payant, aucun texte transmis.
    """
    from modules import voice_casting
    return voice_casting.local_disponible()


@app.get("/api/books/{book_id}/cast/estimate")
async def get_cast_estimate(book_id: int, user_id: int, provider: str = "gemini"):
    """
    Estimation du cout d'un lancement voix multiples (tokens + USD) SANS
    lancer d'appel IA : decoupe les chapitres en phrases, compte les appels
    Passe 1 + Passe 2, applique les tarifs du provider choisi. Affiche a
    l'utilisateur avant qu'il ne valide ("Activer voix multiples").
    Seuls les chapitres RESTANT a analyser sont comptes : sur une reprise,
    l'estimation annonce ce qui reste reellement a payer, jamais le livre
    entier (session du 13/09/2026).
    """
    conn = get_db()
    book = conn.execute(
        "SELECT * FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    deja_traites = _chapitres_deja_traites(conn, book_id)
    conn.close()
    if not book:
        raise HTTPException(404, "Livre introuvable")

    epub_path = str(LIBRARY_DIR / book["filename"])
    from core.epub_parser import get_chapters
    from modules import voice_casting

    chapters = get_chapters(epub_path)
    if not chapters:
        raise HTTPException(400, "Livre vide, impossible d'estimer le cout")

    restants = [c for c in chapters if c["index"] not in deja_traites]
    texts = [c.get("text") or "" for c in restants]
    return voice_casting.estimate_cast_cost(texts, provider)


@app.post("/api/books/{book_id}/cast")
async def start_casting(book_id: int, user_id: int, provider: str = "gemini"):
    """
    Demarre -- ou REPREND -- l'analyse multi-voix d'un livre. Traite le
    premier chapitre restant en direct (l'appelant attend la reponse --
    d'ou la barre de progression visible cote UI), puis lance les chapitres
    suivants en tache de fond.
    Les chapitres deja analyses lors d'un lancement precedent ne sont JAMAIS
    refactures : la reprise repart exactement ou l'analyse s'etait arretee,
    et si tous les chapitres sont deja la, seule la Passe 2 est relancee
    (session du 13/09/2026 -- plus jamais deux fois le meme chapitre paye).
    Si le livre appartient a une saga, les personnages deja castes sur
    d'autres tomes gardent leur voix/pitch/vitesse (session du 22/08/2026).
    """
    conn = get_db()
    book = conn.execute(
        "SELECT * FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")
    book = dict(book)

    # Garde-fou : deux lancements simultanes sur le meme livre feraient payer
    # deux fois les memes chapitres (deux taches de fond en parallele, chacune
    # ignorant le travail de l'autre).
    if str(book.get("cast_status") or "").startswith("processing"):
        conn.close()
        raise HTTPException(409, "Un traitement voix multiples est deja en cours pour ce livre.")

    voix_figees = _fetch_saga_voix_figees(conn, book.get("saga"), user_id, book_id)
    deja_traites = _chapitres_deja_traites(conn, book_id)
    # Fiche de depart, par ordre de fiabilite :
    #   1. la fiche memorisee de CE livre (reprise apres une erreur) ;
    #   2. a defaut, une fiche reconstruite depuis ses noms deja en base ;
    #   3. a defaut, la fiche des AUTRES TOMES de la meme saga -- indispensable
    #      pour qu'un tome neuf reutilise les noms canoniques des precedents
    #      (sinon les personnages changent de voix d'un tome a l'autre).
    fiche_depart = (_charger_fiche(conn, book_id)
                    or _fiche_de_secours(conn, book_id)
                    or _fiche_de_la_saga(conn, book.get("saga"), user_id, book_id))

    conn.execute(
        "UPDATE books SET multi_voice_enabled = 1, cast_status = 'processing' WHERE id = ?",
        (book_id,)
    )
    conn.commit()
    conn.close()

    epub_path = str(LIBRARY_DIR / book["filename"])
    from core.epub_parser import get_chapters
    from modules import voice_casting

    chapters = get_chapters(epub_path)
    if not chapters:
        raise HTTPException(400, "Livre vide, impossible d'analyser les voix")

    # Analyse en LOCAL : le modele de langage a besoin de la carte graphique,
    # que le moteur de voix Kyutai occupe (5,6 Go sur 8). On l'eteint donc le
    # temps du traitement, et on le rallume a la fin. Un casting EN LIGNE
    # (Gemini, DeepSeek, Mistral) ne touche a rien : le texte part sur
    # internet, la carte reste libre.
    if provider == "local":
        _liberer_la_carte_pour_analyse_locale()

    restants = [c for c in chapters if c["index"] not in deja_traites]

    if not restants:
        # Tous les chapitres sont deja payes : on ne relance QUE la Passe 2
        # (fusion des noms + attribution des voix), bien moins couteuse
        # qu'une nouvelle Passe 1.
        conn = get_db()
        conn.execute(
            "UPDATE books SET cast_status = ? WHERE id = ?",
            (f"processing:{len(chapters)}/{len(chapters)}", book_id)
        )
        conn.commit()
        conn.close()

        asyncio.create_task(
            _process_remaining_chapters(book_id, chapters, fiche_depart, None, None, provider, voix_figees)
        )

        return {
            "ok": True,
            "reprise": True,
            "chapter_count": len(chapters),
            "cast_status": f"processing:{len(chapters)}/{len(chapters)}"
        }

    premier = restants[0]
    try:
        first_result = await voice_casting.analyze_chapter(
            premier["text"], fiche_personnages=fiche_depart, provider=provider,
            provider_repli=MOTEURS_DE_SECOURS,
        )
    except Exception as e:
        # L'echec du premier chapitre ne doit pas laisser le livre bloque en
        # 'processing' (le bouton refuserait alors de relancer, et il
        # faudrait redemarrer l'app). On repasse en 'error' : la reprise
        # repartira de CE chapitre, rien d'autre n'a ete facture entre-temps.
        conn = get_db()
        conn.execute("UPDATE books SET cast_status = 'error' WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()
        print(f"Erreur casting voix (livre {book_id}, chapitre {premier['index'] + 1}) : {e}")
        # L'analyse s'arrete : on rend le moteur de voix tout de suite.
        _restaurer_moteur_kyutai()
        raise HTTPException(502, f"Analyse du chapitre {premier['index'] + 1} impossible : {e}")

    conn = get_db()
    _save_attribution(conn, book_id, premier["index"], first_result["phrases"])
    _sauver_fiche(conn, book_id, first_result["personnages"])
    faits = len(deja_traites) + 1
    conn.execute(
        "UPDATE books SET cast_status = ? WHERE id = ?",
        (f"processing:{faits}/{len(chapters)}", book_id)
    )
    conn.commit()
    conn.close()

    asyncio.create_task(
        _process_remaining_chapters(book_id, chapters, first_result["personnages"], first_result, premier["index"], provider, voix_figees)
    )

    return {
        "ok": True,
        "reprise": bool(deja_traites),
        "chapter_count": len(chapters),
        "cast_status": f"processing:{faits}/{len(chapters)}"
    }


@app.get("/api/books/{book_id}/cast/status")
async def get_cast_status(book_id: int, user_id: int):
    """Renvoie l'avancement du traitement multi-voix pour un livre."""
    conn = get_db()
    book = conn.execute(
        "SELECT cast_status, multi_voice_enabled FROM books WHERE id = ? AND user_id = ?",
        (book_id, user_id)
    ).fetchone()
    conn.close()
    if not book:
        raise HTTPException(404, "Livre introuvable")
    return dict(book)


@app.put("/api/books/{book_id}/cast/voice")
async def update_character_voice(book_id: int, user_id: int, request: VoiceUpdateRequest):
    """Change manuellement la voix attribuee a un personnage."""
    conn = get_db()
    book = conn.execute(
        "SELECT id FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")

    conn.execute(
        "UPDATE voices SET voice_id = ?, rate = ?, pitch = ? WHERE book_id = ? AND character_name = ?",
        (request.voice_id, request.rate, request.pitch, book_id, request.character_name)
    )

    # Propagation automatique aux autres tomes de la meme saga (choix de
    # Laurent, session du 22/08/2026) : si ce personnage existe deja dans
    # un tome frere (meme nom exact), sa voix/pitch/vitesse est alignee.
    # Ne cree jamais de nouvelle ligne dans un tome frere -- uniquement
    # les personnages qui y sont deja references.
    saga_row = conn.execute("SELECT saga FROM books WHERE id = ?", (book_id,)).fetchone()
    if saga_row and saga_row["saga"]:
        conn.execute(
            """
            UPDATE voices SET voice_id = ?, rate = ?, pitch = ?
            WHERE character_name = ? AND book_id IN (
                SELECT id FROM books WHERE saga = ? AND user_id = ? AND id != ?
            )
            """,
            (request.voice_id, request.rate, request.pitch,
             request.character_name, saga_row["saga"], user_id, book_id)
        )

    conn.commit()
    conn.close()
    return {"ok": True}


@app.put("/api/books/{book_id}/cast/lock")
async def lock_character_voice(book_id: int, user_id: int, request: VoiceLockRequest):
    """
    Verrouille (ou deverrouille) la voix d'un personnage : un personnage
    verrouille garde sa voix lors d'un re-cast, les autres sont redistribues
    par POST /cast/reassign (session du 12/09/2026).
    """
    conn = get_db()
    book = conn.execute(
        "SELECT id FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")

    conn.execute(
        "UPDATE voices SET locked = ? WHERE book_id = ? AND character_name = ?",
        (1 if request.locked else 0, book_id, request.character_name)
    )
    conn.commit()
    conn.close()
    return {"ok": True, "locked": bool(request.locked)}


def _preparer_recaste(rows, alias_rows, fiche_rows, figees_saga):
    """Prepare un re-cast : groupes d'alias, personnages, voix figees.

    PARTAGEE par les DEUX re-casts -- le gratuit (par criteres) et celui avec
    l'IA -- pour qu'ils ne divergent jamais sur les verrous et la coherence de
    saga. C'est la seule facon d'etre sur que « Re-caster » et « Re-caster avec
    l'IA » respectent exactement les memes regles.

    Renvoie (groupes, personnages, compte_phrases, voix_figees, by_name).
    """
    # Un personnage peut etre un GROUPE d'alias : on traite le groupe comme
    # une seule fiche (repliques additionnees) et on applique la meme voix a
    # tous ses membres, sauf ceux verrouilles individuellement.
    alias_map = {r["alias_name"]: r["canonical_name"] for r in alias_rows}
    by_name = {r["character_name"]: r for r in rows}
    groupes = {}
    for r in rows:
        canon = alias_map.get(r["character_name"], r["character_name"])
        if canon not in by_name:
            canon = r["character_name"]
        groupes.setdefault(canon, []).append(r)

    # On rejoue la meme attribution que lors du casting initial, en passant
    # les groupes verrouilles comme "voix figees" -- mecanisme deja utilise
    # pour les sagas, donc comportement identique et eprouve.
    personnages = []
    compte_phrases = {}
    voix_figees = {}
    ages_fiche = {r["character_name"]: (r["age"] or "adulte") for r in fiche_rows}
    for canon, membres in groupes.items():
        head = by_name.get(canon, membres[0])
        personnages.append({"nom": canon, "genre": head["genre"] or "H",
                            "age": ages_fiche.get(canon) or "adulte"})
        compte_phrases[canon] = sum((m["line_count"] or 0) for m in membres)
        if head["locked"]:
            voix_figees[canon] = {
                "voice_id": head["voice_id"],
                "pitch": head["pitch"],
                "rate": head["rate"] or "+0%",
                "genre": head["genre"] or "H",
            }

    # Les voix des AUTRES TOMES completent les verrous, sans les ecraser : un
    # personnage deja caste dans la saga (voir le tome le plus ancien) garde sa
    # voix, meme s'il n'est pas verrouille dans ce tome-ci. C'est ce qui preserve
    # la coherence d'une saga lors d'un re-cast.
    for nom, fiche in figees_saga.items():
        voix_figees.setdefault(nom, fiche)

    return groupes, personnages, compte_phrases, voix_figees, by_name


@app.post("/api/books/{book_id}/cast/reassign")
async def reassign_voices(book_id: int, user_id: int, par_criteres: bool = True):
    """
    Re-cast GRATUIT d'un livre deja caste : on garde l'attribution des
    locuteurs deja stockee (table speaker_attribution) et on redistribue
    uniquement les voix dans le catalogue courant -- nouvelles voix Kokoro
    incluses -- sans AUCUN appel IA.

    Les personnages verrouilles (case "garder" de la fenetre du casting)
    conservent exactement leur voix ; les autres recoivent une nouvelle voix
    dediee ou generique selon leur nombre de repliques. Le pitch et la
    vitesse existants sont conserves : seule la voix change.

    par_criteres (16/09/2026, actif par defaut) : les voix sont choisies
    d'apres les ANNOTATIONS D'ECOUTE de Laurent (age, timbre, debit -- voir
    voice_casting._classement_voix), et d'apres l'AGE reel des personnages
    (table cast_fiche). Les personnages verrouilles et les voix figees de
    saga restent prioritaires.
    `?par_criteres=false` revient au tri precedent, par paliers d'etoiles :
    utile pour comparer les deux attributions sur un meme livre.
    """
    conn = get_db()
    book = conn.execute(
        "SELECT id, cast_status, saga FROM books WHERE id = ? AND user_id = ?",
        (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")
    if (book["cast_status"] or "none") != "done":
        conn.close()
        raise HTTPException(400, "Ce livre n'est pas encore caste")

    rows = conn.execute(
        "SELECT character_name, voice_id, pitch, rate, genre, line_count, locked FROM voices WHERE book_id = ?",
        (book_id,)
    ).fetchall()
    alias_rows = conn.execute(
        "SELECT alias_name, canonical_name FROM character_aliases WHERE book_id = ?", (book_id,)
    ).fetchall()
    # L'AGE des personnages n'est pas dans la table voices (qui ne stocke que la
    # voix attribuee) : il vient de la FICHE du casting. Sans lui, l'attribution
    # par criteres traiterait tout le monde comme un adulte (constat du
    # 16/09/2026 : l'ancien re-cast forcait "adulte" en dur).
    fiche_rows = conn.execute(
        "SELECT character_name, age FROM cast_fiche WHERE book_id = ?", (book_id,)
    ).fetchall()
    # Coherence de SAGA (16/09/2026, demande de Laurent) : les voix des AUTRES
    # TOMES font reference, comme au casting complet. Sans cela, un re-cast sur
    # un tome rendait a un personnage une voix DIFFERENTE de celle de son tome
    # de reference (le plus ancien ajoute) -- la saga partait en morceaux.
    # Le re-cast ne le faisait pas jusqu'ici : seul le casting complet appelait
    # cette fonction. Les verrous locaux du livre re-caste restent prioritaires
    # (voir plus bas : ils sont ecrits en premier dans voix_figees).
    figees_saga = _fetch_saga_voix_figees(conn, book["saga"], user_id, book_id)
    conn.close()
    if not rows:
        raise HTTPException(400, "Aucun personnage a re-caster")

    from modules import voice_casting

    # Preparation PARTAGEE avec le re-cast par IA (voir _preparer_recaste) :
    # groupes d'alias, ages lus dans cast_fiche, verrous, voix figees de saga.
    groupes, personnages, compte_phrases, voix_figees, by_name = _preparer_recaste(
        rows, alias_rows, fiche_rows, figees_saga)

    nouvelles = voice_casting.assign_voices(personnages, compte_phrases,
                                            voix_figees=voix_figees,
                                            par_criteres=par_criteres)

    conn = get_db()
    modifies = 0
    for canon, membres in groupes.items():
        head = by_name.get(canon, membres[0])
        if head["locked"]:
            voix_groupe = head["voice_id"]
        else:
            cible = nouvelles.get(canon)
            if not cible:
                continue
            voix_groupe = cible["voice_id"]
        for m in membres:
            # un alias verrouille individuellement garde sa voix propre
            if m["locked"] and m["character_name"] != canon:
                continue
            conn.execute(
                "UPDATE voices SET voice_id = ? WHERE book_id = ? AND character_name = ?",
                (voix_groupe, book_id, m["character_name"])
            )
            modifies += 1
    conn.commit()
    conn.close()
    return {"ok": True, "modifies": modifies, "gardes": len(voix_figees)}


def _decouper_phrases_du_chapitre(texte: str) -> list:
    """Les phrases d'un chapitre, decoupees COMME LE FAIT LA PAGE.

    C'est indispensable : `speaker_attribution.sentence_idx` est calcule sur ce
    decoupage precis (frontend/app.js, `_buildSentences`) -- paragraphes
    separes par une ligne vide, puis phrases coupees apres un point, un point
    d'interrogation, d'exclamation, une ellipse ou un guillemet fermant, et
    phrases de 4 caracteres ou plus conservees.

    Si ce decoupage s'ecarte de celui de la page, l'appelant s'en apercoit (il
    compare les indices au nombre de phrases) et se passe des repliques :
    mieux vaut un re-cast sans extraits qu'un re-cast avec les repliques d'un
    AUTRE personnage.
    """
    phrases = []
    for paragraphe in re.split(r"\n\n+", texte or ""):
        paragraphe = paragraphe.strip()
        if len(paragraphe) <= 5:
            continue
        for brute in re.split(r"(?<=[.!?\u2026\u00bb])\s+", paragraphe):
            morceau = brute.strip()
            if len(morceau) > 3:
                phrases.append(morceau)
    return phrases


def _repliques_des_personnages(conn, book, personnages, maximum=3,
                               chapitres_max=20):
    """{nom: [replique, ...]} : quelques repliques des premiers chapitres.

    Le texte n'est pas en base (la table `speaker_attribution` ne garde que
    « qui parle ») : il faut donc relire l'epub. On borne le travail -- on
    s'arrete des que chaque personnage a ses repliques, et apres
    `chapitres_max` chapitres. Un re-cast doit rester une operation de
    quelques secondes, pas une relecture complete du livre.

    Renvoie aussi les chapitres ECARTES (decoupage non aligne sur celui de la
    page), pour pouvoir le dire a l'utilisateur plutot que de faire semblant.
    """
    from core.epub_parser import get_chapters

    noms = {p["nom"] for p in personnages}
    trouvees = {}
    ecartes = set()
    chemin = str(LIBRARY_DIR / book["filename"])

    try:
        chapitres = get_chapters(chemin)
    except Exception:
        return trouvees, ecartes

    # Une SEULE lecture du livre (l'analyse est faite une fois), puis on
    # parcourt les premiers chapitres : c'est la que les personnages se
    # presentent, et cela suffit pour entendre leur facon de parler.
    for position, chapitre in enumerate(chapitres[:chapitres_max]):
        index = chapitre.get("index", position)
        rows = conn.execute(
            "SELECT sentence_idx, speaker FROM speaker_attribution "
            "WHERE book_id = ? AND chapter_index = ?",
            (book["id"], index)
        ).fetchall()
        if not rows:
            continue
        phrases = _decouper_phrases_du_chapitre(chapitre.get("text") or "")
        if not phrases or max(r["sentence_idx"] for r in rows) >= len(phrases):
            ecartes.add(index)
            continue
        for row in rows:
            nom = row["speaker"]
            if nom not in noms or len(trouvees.get(nom, [])) >= maximum:
                continue
            trouvailles = trouvees.setdefault(nom, [])
            texte = phrases[row["sentence_idx"]]
            if texte not in trouvailles:
                trouvailles.append(texte)

    return trouvees, ecartes


@app.post("/api/books/{book_id}/cast/reassign_ia")
async def reassign_voices_ia(book_id: int, user_id: int, provider: str = "gemini"):
    """
    Re-cast AVEC l'IA (etape 2, livree le 16/09/2026) -- le second bouton de la
    fenetre du casting, a cote du re-cast gratuit.

    Ce que l'IA apporte : elle LIT des repliques du personnage et en deduit sa
    position sociale, son registre de langue, le fait de parler etranger et son
    temperament -- ce qu'aucune table ne contient. Comme elle n'entend pas les
    timbres, elle choisit sur DESCRIPTION (les annotations d'ecoute).

    Garde-fous, identiques au re-cast gratuit :
      - « qui parle » n'est PAS recalcule : seules les voix changent, donc
        c'est rapide et sans reabonnement (quelques centimes) ;
      - les personnages VERROUILLES et les voix FIGEES DE SAGA ne bougent pas ;
      - les PETITS ROLES (< MINOR_THRESHOLD repliques) ne sont pas soumis a
        l'IA : ils gardent la voix generique, comme aujourd'hui ;
      - l'IA ne peut choisir que parmi les voix que le re-cast par criteres
        autorise deja (voir voice_casting.voix_proposees_pour) ;
      - tout ce que l'IA rend d'illisible ou d'interdit est ECARTE, et le
        personnage garde alors sa voix par criteres (repli).
    Rien n'est ecrit tant que la reponse de l'IA n'a pas ete verifiee.
    """
    from modules import voice_casting

    conn = get_db()
    book = conn.execute(
        "SELECT id, filename, cast_status, saga FROM books WHERE id = ? AND user_id = ?",
        (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")
    if (book["cast_status"] or "none") != "done":
        conn.close()
        raise HTTPException(400, "Ce livre n'est pas encore caste")

    rows = conn.execute(
        "SELECT character_name, voice_id, pitch, rate, genre, line_count, locked FROM voices WHERE book_id = ?",
        (book_id,)
    ).fetchall()
    if not rows:
        conn.close()
        raise HTTPException(400, "Aucun personnage a re-caster")
    alias_rows = conn.execute(
        "SELECT alias_name, canonical_name FROM character_aliases WHERE book_id = ?",
        (book_id,)
    ).fetchall()
    fiche_rows = conn.execute(
        "SELECT character_name, age FROM cast_fiche WHERE book_id = ?", (book_id,)
    ).fetchall()
    figees_saga = _fetch_saga_voix_figees(conn, book["saga"], user_id, book_id)

    groupes, personnages, compte_phrases, voix_figees, by_name = _preparer_recaste(
        rows, alias_rows, fiche_rows, figees_saga)

    # Seuls les roles qui comptent sont soumis a l'IA : les petits roles
    # gardent leur voix generique (regle du 22/08/2026, inchangee).
    soumis = [p for p in personnages
              if compte_phrases.get(p["nom"], 0) >= voice_casting.MINOR_THRESHOLD]
    repliques, ecartes = _repliques_des_personnages(conn, book, soumis)
    conn.close()
    for personnage in soumis:
        personnage["repliques"] = compte_phrases.get(personnage["nom"], 0)
        personnage["repliques_texte"] = repliques.get(personnage["nom"], [])

    if not soumis:
        raise HTTPException(400, "Aucun personnage assez present pour un re-cast IA")

    exclues = {fiche["voice_id"] for fiche in voix_figees.values()}
    try:
        resultat = await voice_casting.attribuer_voix_avec_ia(
            soumis, exclues=exclues, provider=provider)
    except Exception as erreur:
        raise HTTPException(
            502, "L'IA n'a pas pu repondre ({}). RIEN n'a ete modifie.".format(
                str(erreur)[:160]))
    attributions = resultat.get("attributions") or {}

    # Repli pour tout ce que l'IA n'a pas attribue (ou a attribue a tort) : le
    # personnage garde alors exactement la voix du re-cast par criteres.
    nouvelles = voice_casting.assign_voices(personnages, compte_phrases,
                                            voix_figees=voix_figees,
                                            par_criteres=True)

    conn = get_db()
    modifies = 0
    par_ia = 0
    for canon, membres in groupes.items():
        head = by_name.get(canon, membres[0])
        if head["locked"]:
            voix_groupe = head["voice_id"]
        elif canon in attributions:
            voix_groupe = attributions[canon]
            par_ia += 1
        else:
            cible = nouvelles.get(canon)
            if not cible:
                continue
            voix_groupe = cible["voice_id"]
        for membre in membres:
            if membre["locked"] and membre["character_name"] != canon:
                continue
            conn.execute(
                "UPDATE voices SET voice_id = ? WHERE book_id = ? AND character_name = ?",
                (voix_groupe, book_id, membre["character_name"])
            )
            modifies += 1
    conn.commit()
    conn.close()

    return {"ok": True, "modifies": modifies, "gardes": len(voix_figees),
            "par_ia": par_ia, "soumis": len(soumis),
            "petits_roles": len(personnages) - len(soumis),
            "extraits": sum(1 for p in soumis if p["repliques_texte"]),
            "chapitres_ecartes": sorted(ecartes),
            "problemes": (resultat.get("problemes") or [])[:5],
            "tokens": voice_casting.tokens_session(provider)}
@app.post("/api/books/{book_id}/cast/autogroup")
async def autogroup_voice_duplicates(book_id: int, user_id: int, apply: bool = False):
    """
    Detecte les personnages ecrits de plusieurs facons (accents, tirets,
    article initial) et propose de les regrouper. Sans 'apply', renvoie
    seulement les groupes detectes (apercu) ; avec 'apply=1', cree les
    regroupements et aligne la voix de base des alias sur le principal.
    Gratuit (aucun appel IA), reversible (aucun nom n'est supprime).
    """
    conn = get_db()
    book = conn.execute(
        "SELECT id FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")

    rows = conn.execute(
        "SELECT character_name, line_count FROM voices WHERE book_id = ?", (book_id,)
    ).fetchall()
    deja_alias = {r["alias_name"] for r in conn.execute(
        "SELECT alias_name FROM character_aliases WHERE book_id = ?", (book_id,))}

    from modules import voice_casting

    items = [
        {"nom": r["character_name"], "line_count": r["line_count"] or 0}
        for r in rows if r["character_name"] not in deja_alias
    ]
    groupes = voice_casting.find_writing_duplicate_groups(items)
    apercu = [{"principal": g[0], "doublons": g[1:]} for g in groupes]

    if not apply:
        conn.close()
        return {"ok": True, "applied": False, "groupes": apercu, "count": len(groupes)}

    nb_alias = 0
    for groupe in groupes:
        principal = groupe[0]
        canon_row = conn.execute(
            "SELECT voice_id, pitch, rate FROM voices WHERE book_id = ? AND character_name = ?",
            (book_id, principal)
        ).fetchone()
        for alias in groupe[1:]:
            conn.execute(
                """
                INSERT INTO character_aliases (book_id, alias_name, canonical_name)
                VALUES (?, ?, ?)
                ON CONFLICT(book_id, alias_name) DO UPDATE SET canonical_name = excluded.canonical_name
                """,
                (book_id, alias, principal)
            )
            if canon_row:
                conn.execute(
                    "UPDATE voices SET voice_id = ?, pitch = ?, rate = ? WHERE book_id = ? AND character_name = ?",
                    (canon_row["voice_id"], canon_row["pitch"], canon_row["rate"] or "+0%", book_id, alias)
                )
            nb_alias += 1

    conn.commit()
    conn.close()
    return {"ok": True, "applied": True, "groupes": apercu,
            "count": len(groupes), "alias_crees": nb_alias}


@app.post("/api/books/{book_id}/cast/ungroup")
async def ungroup_voice_alias(book_id: int, user_id: int, request: AliasDetachRequest):
    """Detache un alias de sa fiche : le nom n'a jamais ete supprime, il
    redevient un personnage independant avec sa propre voix."""
    conn = get_db()
    book = conn.execute(
        "SELECT id FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")

    conn.execute(
        "DELETE FROM character_aliases WHERE book_id = ? AND alias_name = ?",
        (book_id, request.alias_name)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/books/{book_id}/cast/group")
async def group_voice_alias(book_id: int, user_id: int, request: AliasGroupRequest):
    """Rattache MANUELLEMENT un nom a un personnage : « ces deux noms
    designent la meme personne ».

    Sert aux PSEUDONYMES, que la regle automatique ne peut pas deviner :
    « Edmond Dantes », « Le comte de Monte-Cristo », « l'abbe Busoni »,
    « Simbad le marin » sont un seul et meme personnage (demande de Laurent,
    12/09/2026). Meme table que les doublons d'ecriture, donc meme affichage
    en retrait sous le principal, meme bouton ✂ pour detacher.

    DIFFERENCE IMPORTANTE avec le regroupement automatique : ici les VOIX ne
    sont pas touchees. Chaque appellation garde la sienne, ce qui est
    justement voulu (« Monte-Cristo n'a pas la meme voix que l'abbe Busoni »).
    """
    conn = get_db()
    book = conn.execute(
        "SELECT id FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")

    alias = (request.alias_name or "").strip()
    canon = (request.canonical_name or "").strip()
    if not alias or not canon:
        conn.close()
        raise HTTPException(400, "Les deux noms sont necessaires.")
    if alias == canon:
        conn.close()
        raise HTTPException(400, "Un nom ne peut pas etre rattache a lui-meme.")

    noms = {r["character_name"] for r in conn.execute(
        "SELECT character_name FROM voices WHERE book_id = ?", (book_id,))}
    if alias not in noms or canon not in noms:
        conn.close()
        raise HTTPException(404, "Nom inconnu dans ce livre.")

    # Le principal vise doit etre une RACINE : s'il est lui-meme rattache a
    # quelqu'un, on remonte a sa racine, pour ne jamais creer de chaine
    # (A -> B -> C) que l'affichage ne saurait pas representer.
    for _ in range(10):
        row = conn.execute(
            "SELECT canonical_name FROM character_aliases WHERE book_id = ? AND alias_name = ?",
            (book_id, canon)
        ).fetchone()
        if not row or not row["canonical_name"] or row["canonical_name"] == canon:
            break
        canon = row["canonical_name"]
    if canon == alias:
        conn.close()
        raise HTTPException(400, "Rattachement impossible : cela creerait un cycle.")

    # Les noms deja rattaches a `alias` suivent le mouvement (sinon ils
    # resteraient accroches a un nom devenu alias lui-meme).
    conn.execute(
        "UPDATE character_aliases SET canonical_name = ? WHERE book_id = ? AND canonical_name = ?",
        (canon, book_id, alias)
    )
    conn.execute(
        """
        INSERT INTO character_aliases (book_id, alias_name, canonical_name)
        VALUES (?, ?, ?)
        ON CONFLICT(book_id, alias_name) DO UPDATE SET canonical_name = excluded.canonical_name
        """,
        (book_id, alias, canon)
    )
    conn.commit()
    conn.close()
    return {"ok": True, "alias_name": alias, "canonical_name": canon}


@app.get("/api/sagas")
async def list_sagas(user_id: int):
    """Liste les noms de saga deja utilises par cet utilisateur (autocompletion cote UI)."""
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT saga FROM books WHERE user_id = ? AND saga IS NOT NULL AND saga != '' ORDER BY saga",
        (user_id,)
    ).fetchall()
    conn.close()
    return [row["saga"] for row in rows]


@app.put("/api/books/{book_id}/saga")
async def update_book_saga(book_id: int, user_id: int, request: SagaUpdateRequest):
    """Associe (ou retire, si vide) ce livre a une saga."""
    conn = get_db()
    book = conn.execute(
        "SELECT id FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")

    saga = request.saga.strip() or None
    conn.execute("UPDATE books SET saga = ? WHERE id = ?", (saga, book_id))
    conn.commit()
    conn.close()
    return {"ok": True, "saga": saga}


@app.post("/api/books/{book_id}/cast/propagate-saga")
async def propagate_saga_casting(book_id: int, user_id: int):
    """
    Pousse le casting actuel de ce livre (voix + pitch + vitesse par
    personnage) vers tous les autres tomes de la meme saga. Cree la
    ligne si le personnage n'existe pas encore chez le tome frere, la
    met a jour sinon (ne touche jamais au line_count existant du tome
    frere). Pense pour les sagas partiellement castees avant l'existence
    de ce systeme (ex: Monte-Cristo, session du 22/08/2026).
    """
    conn = get_db()
    book = conn.execute(
        "SELECT saga FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    if not book:
        conn.close()
        raise HTTPException(404, "Livre introuvable")
    if not book["saga"]:
        conn.close()
        raise HTTPException(400, "Ce livre n'a pas de saga renseignee")

    siblings = conn.execute(
        "SELECT id FROM books WHERE saga = ? AND user_id = ? AND id != ?",
        (book["saga"], user_id, book_id)
    ).fetchall()

    source_voices = conn.execute(
        "SELECT character_name, voice_id, pitch, rate, genre FROM voices WHERE book_id = ?",
        (book_id,)
    ).fetchall()

    for sibling in siblings:
        for v in source_voices:
            conn.execute(
                """
                INSERT INTO voices (book_id, character_name, voice_id, pitch, rate, genre, line_count)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT (book_id, character_name) DO UPDATE SET
                    voice_id = excluded.voice_id,
                    rate     = excluded.rate,
                    pitch    = excluded.pitch,
                    genre    = excluded.genre
                """,
                (sibling["id"], v["character_name"], v["voice_id"], v["pitch"], v["rate"] or "+0%", v["genre"])
            )

    conn.commit()
    conn.close()
    return {"ok": True, "tomes_mis_a_jour": len(siblings)}


# --- Progression ---

@app.get("/api/progress/{book_id}")
async def get_progress(book_id: int, user_id: int):
    conn = get_db()
    progress = conn.execute(
        "SELECT * FROM progress WHERE book_id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    conn.close()
    if not progress:
        return {"book_id": book_id, "user_id": user_id, "chapter_index": 0, "scroll_position": 0, "cursor_idx": 0}
    return dict(progress)

@app.post("/api/progress/{book_id}")
async def save_progress(book_id: int, user_id: int, data: ProgressData):
    conn = get_db()
    conn.execute("""
        INSERT INTO progress (user_id, book_id, chapter_index, scroll_position, cursor_idx, last_read)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id, book_id) DO UPDATE SET
            chapter_index   = excluded.chapter_index,
            scroll_position = excluded.scroll_position,
            cursor_idx      = excluded.cursor_idx,
            last_read       = excluded.last_read
    """, (user_id, book_id, data.chapter_index, data.scroll_position, data.cursor_idx))
    conn.commit()
    conn.close()
    return {"ok": True}

# --- Recherche ---

import re as _re
import unicodedata as _unicodedata


def _normalize_for_search(s: str) -> str:
    """Minuscules + suppression des accents, pour une recherche souple."""
    s = s.lower()
    s = _unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if _unicodedata.category(c) != 'Mn')
    return s


def _split_sentences(paragraph: str) -> list:
    raw = _re.split(r'(?<=[.!?…»])\s+', paragraph)
    return [s.strip() for s in raw if len(s.strip()) > 3]


@app.get("/api/books/{book_id}/search")
async def search_book(book_id: int, q: str, user_id: int):
    if not q or len(q.strip()) < 1:
        return {"query": q, "results": []}

    conn = get_db()
    book = conn.execute(
        "SELECT * FROM books WHERE id = ? AND user_id = ?", (book_id, user_id)
    ).fetchone()
    conn.close()
    if not book:
        raise HTTPException(404, "Livre introuvable")

    epub_path = str(LIBRARY_DIR / book["filename"])
    from core.epub_parser import get_chapters
    chapters = get_chapters(epub_path)

    needle = _normalize_for_search(q.strip())
    results = []

    for chapter in chapters:
        text = chapter.get("text", "") or ""
        paras = [p.strip() for p in _re.split(r'\n\n+', text) if len(p.strip()) > 5]

        for para_idx, para in enumerate(paras):
            sentences = _split_sentences(para)
            for sentence in sentences:
                norm_sentence = _normalize_for_search(sentence)
                # recherche mot exact (bordures de mot) dans la phrase normalisee
                pattern = r'\b' + _re.escape(needle) + r'\b'
                if _re.search(pattern, norm_sentence):
                    results.append({
                        "chapter_index": chapter["index"],
                        "chapter_title": chapter.get("title") or ("Chapitre " + str(chapter["index"] + 1)),
                        "paragraph_index": para_idx,
                        "sentence_text": sentence,
                    })

    return {"query": q, "results": results}


# --- TTS ---

@app.post("/api/tts")
async def tts(request: TTSRequest):
    if request.voice.startswith("kokoro:"):
        from modules.tts import synthesize_kokoro
        audio = await synthesize_kokoro(request.text, request.voice, request.rate, request.pitch)
        async def generate_kokoro():
            yield audio
        return StreamingResponse(generate_kokoro(), media_type="audio/wav")

    if request.voice.startswith("piper:"):
        from modules.tts import synthesize_piper
        audio = await synthesize_piper(request.text, request.voice, request.rate, request.pitch)
        async def generate_piper():
            yield audio
        return StreamingResponse(generate_piper(), media_type="audio/wav")

    if request.voice.startswith("kyutai:"):
        # Le moteur Kyutai tourne dans SON PROPRE service (Python 3.12 +
        # PyTorch, lance par kyutai_service/DEMARRER_KYUTAI.bat) : on l'appelle
        # en HTTP local, comme Edge TTS est appele par le reseau.
        # `request.context` (fin de la phrase precedente) est transmis : c'est
        # ce qui evite au moteur de demarrer a froid (17/09/2026).
        from modules.tts import synthesize_kyutai, KyutaiIndisponible
        try:
            audio = await synthesize_kyutai(request.text, request.voice,
                                            request.rate, request.pitch,
                                            request.context)
        except KyutaiIndisponible as erreur:
            # 503 : erreur "definitive" (moteur eteint), pas une coupure
            # reseau. Le client affiche le message et arrete la lecture au
            # lieu de reessayer sans fin.
            raise HTTPException(status_code=503, detail=str(erreur))
        async def generate_kyutai():
            yield audio
        return StreamingResponse(generate_kyutai(), media_type="audio/wav")

    if request.voice.startswith("xtts:"):
        # Le moteur XTTS v2 tourne dans SON PROPRE service (Python 3.12 +
        # PyTorch, lance par xtts_service/DEMARRER_XTTS.bat) : on l'appelle
        # en HTTP local, exactement comme Kyutai.
        from modules.tts import synthesize_xtts, XttsIndisponible
        try:
            audio = await synthesize_xtts(request.text, request.voice,
                                          request.rate, request.pitch)
        except XttsIndisponible as erreur:
            # 503 : erreur "definitive" (moteur eteint), pas une coupure
            # reseau. Le client affiche le message et arrete la lecture au
            # lieu de reessayer sans fin.
            raise HTTPException(status_code=503, detail=str(erreur))
        async def generate_xtts():
            yield audio
        return StreamingResponse(generate_xtts(), media_type="audio/wav")

    if request.voice.startswith("neutts:"):
        # Le moteur NeuTTS tourne dans SON PROPRE service (Python 3.12 +
        # PyTorch, lance par neutts_service/DEMARRER_NEUTTS.bat) : on l'appelle
        # en HTTP local, exactement comme Kyutai et XTTS v2.
        from modules.tts import synthesize_neutts, NeuttsIndisponible
        try:
            audio = await synthesize_neutts(request.text, request.voice,
                                             request.rate, request.pitch)
        except NeuttsIndisponible as erreur:
            # 503 : erreur "definitive" (moteur eteint), pas une coupure
            # reseau. Le client affiche le message et arrete la lecture au
            # lieu de reessayer sans fin.
            raise HTTPException(status_code=503, detail=str(erreur))
        async def generate_neutts():
            yield audio
        return StreamingResponse(generate_neutts(), media_type="audio/wav")

    from modules.tts import synthesize_stream
    async def generate():
        async for chunk in synthesize_stream(
            request.text, request.voice, request.rate, request.pitch
        ):
            yield chunk
    return StreamingResponse(generate(), media_type="audio/mpeg")


# --- Piper : outil de tagging Homme/Femme ---

class PiperTagRequest(BaseModel):
    model: str
    speaker_id: int
    gender: str  # "H" ou "F"

def _load_piper_tags() -> dict:
    if PIPER_TAGS_PATH.exists():
        return json.loads(PIPER_TAGS_PATH.read_text(encoding="utf-8"))
    return {}

def _save_piper_tags(tags: dict):
    PIPER_TAGS_PATH.write_text(json.dumps(tags, ensure_ascii=False, indent=2), encoding="utf-8")

@app.get("/api/piper/models")
async def piper_models():
    from modules.tts import PIPER_MODEL_FILES, _piper_voices, _load_piper_model
    result = {}
    for key in PIPER_MODEL_FILES:
        _load_piper_model(key)
        result[key] = _piper_voices[key].config.num_speakers
    return result

@app.get("/api/piper/tags")
async def get_piper_tags():
    return _load_piper_tags()

@app.post("/api/piper/tags")
async def save_piper_tag(request: PiperTagRequest):
    tags = _load_piper_tags()
    tags[f"{request.model}:{request.speaker_id}"] = request.gender
    _save_piper_tags(tags)
    return {"ok": True, "count": len(tags)}

@app.get("/api/piper/preview")
async def piper_preview(model: str, speaker_id: int):
    from modules.tts import synthesize_piper
    voice = f"piper:{model}:{speaker_id}"
    audio = await synthesize_piper("Bonjour, je suis d'humeur bavarde ce soir.", voice)
    async def generate():
        yield audio
    return StreamingResponse(generate(), media_type="audio/wav")

# --- Lancement direct ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=False)
