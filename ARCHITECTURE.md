# NIMM ePub — Architecture

_Décrit la logique en vigueur. À mettre à jour quand une logique change._

**Comment se servir de ce document** — c'est la **mémoire technique** du
projet (comment chaque pièce fonctionne, et pourquoi elle est ainsi). Les
tâches à faire vivent dans `BACKLOG.md`, pas ici. Pour s'y retrouver :

- **le sommaire ci-dessous suit l'ordre du fichier** : il y a **10 parties**
  (`##`), et chacune porte ses **sujets** (`###`) ;
- **le bloc « Aujourd'hui » en tête d'un sujet** est l'**état actuel**, court et
  vérifiable (fichiers, fonctions, routes, colonnes, réglages) : c'est ce qu'il
  faut lire en premier. Tout ce qui suit est la **chronique datée** — pourquoi on
  l'a fait, les mesures, les leçons ;
- **une date entre parenthèses** marque la session où le sujet a été livré ; les
  noms de code qui n'existent plus y sont écrits « ex-… » ou « les anciennes … » ;
- **les identifiants du code** (fonction, route, colonne de table) sont entre
  accents graves : c'est par eux qu'une recherche tombe juste, et c'est ce que
  les outils de contrôle vérifient ;
- **les deux outils qui surveillent ce document** (lecture seule, rien ne
  s'allume, rien n'est facturé) : `test_voix/_auditer_documentation.py` (les noms
  et les références) et `_verifier_faits_architecture.py` (les faits).

**Sommaire**

- **🧭 Le projet — vue d'ensemble**
  - Structure du dossier
  - Principe général
  - Flux principal
  - Dépendances Python
  - Workflow de développement
  - Ordre de développement des fichiers
- **🖥️ Le serveur : main.py et la base**
  - main.py — Routes HTTP
  - data/nimm_epub.db — Base SQLite
  - Profils familiaux (multi-utilisateurs) — main.py + index.html + app.js + styles.css
- **🎬 La page (frontend) et la lecture**
  - frontend/ — Interface
  - Logique TTS — app.js
  - Recherche dans le livre — main.py + app.js
  - Effet glitch — styles.css
  - Mode RSVP (lecture mot-à-mot) — app.js + styles.css
  - Cache busting (mises à jour mobile/PWA)
  - START.bat — Lancement
  - Temps de lecture restant
  - 🧹 Cache HTTP (no-store) — bibliothèque + API — session du 20/08/2026
  - 🔌 Serveurs fantômes sur le port 8081 — le piège, et son garde-fou (18/09/2026)
  - 📝 Deux idées RSVP à l'étude — déménagées
- **🔤 Le texte lu : extraction, nettoyage, découpage**
  - core/epub_parser.py — Parseur EPUB
  - modules/tts.py — Synthèse vocale
- **🎭 Le casting : qui parle, avec quelle voix**
  - 🎭 Distribution de voix par personnage (IA)
  - Report des notes d'écoute dans les catalogues — étape 3 du listener
  - Module voice_casting.py — détail technique
  - 🎭 Fenêtre du casting (visuel) — session du 20/08/2026
  - ♻️ Re-cast d'un livre déjà casté (gratuit) — session du 12/09/2026
  - 🎭 Les petits rôles : une voix par genre (Jessica / Pierre) — 21/09/2026
  - 🧩 Regroupement des alias (doublons d'écriture) — session du 12/09/2026
  - 🧬 Bug corrigé — la fiche de personnages qui rétrécissait entre chapitres
  - 🎯 Gard déterministe — citations coupées par le découpage automatique
  - 🔀 Système multi-moteur — Gemini / Mistral / DeepSeek (session du 21/08/2026)
  - 🎭 Filtres du casting : âge de la voix et genre du personnage — 21/09/2026
  - 🎭 En-tête compact de la fenêtre du casting — 22/09/2026
  - 🎧 Fenêtre « Écouter les voix » (le listener) — session du 14/09/2026
  - Critères FIXES d'annotation (16/09/2026)
  - Attribution des voix par critères (16/09/2026)
- **🎙️ Les voix : les pools et les notes d'écoute**
  - Voix du narrateur : par livre, sans héritage entre livres (20/09/2026)
  - 🔊 Banque de voix (session du 08/09/2026 — pool élargi aux Kokoro)
  - 🔼 Règle des paliers d'étoiles — session du 15/09/2026
  - Symboles ♀️ / ♂️ de genre devant les prénoms — session du 20/09/2026.
  - Noms des voix : jamais d'identifiant technique dans les menus
  - Ordre du pool automatique (session du 12/09/2026 — Kyutai en tête)
  - 🎨 NIMM Voix — fournisseur de voix externes (session du 11/09/2026)
  - 🎚️ Nouvel ordre du pool automatique de casting — session du 14/09/2026
- **🗣️ Les moteurs de voix**
  - 🗣️ Intégration Kokoro TTS — accents forcés par personnage (livré, session du 21/08/2026)
  - 🗣️ Prononciation française imposée — Kokoro et Piper (21/09/2026)
  - 🎙️ Voix « écoutables » selon le moteur allumé — session du 14/09/2026
  - 🎛️ Changer de moteur de voix : un seul à la fois — session du 15/09/2026
  - 🛠️ Réparer les moteurs de voix, et un moteur qui ne se perd plus — 21/09/2026
  - 🎙️ Moteur XTTS v2 installé comme service séparé — session du 14/09/2026
  - Extraits de voix libres de droits pour XTTS — chantier du 15/09/2026
  - 🎙️ Moteur de voix NeuTTS (livré le 16/09/2026)
  - 🎒 Moteur de voix Pocket TTS (livré le 21/09/2026)
- **✂️ Le mode dialogue : narration et répliques**
  - ✂️ Mode dialogue : la narration séparée des répliques — 21/09/2026
- **🔒 Écouter dans de bonnes conditions**
  - 🔒 Lecture écran éteint (Media Session) — session du 20/08/2026
  - 🔒 Lire écran verrouillé : la « réserve à bloc », et le lecteur (20/09/2026)
  - 💾 Cache audio serveur — session du 08/09/2026
  - ✂️ Rognage des silences de bord — session du 08/09/2026
- **📜 Journal des sessions passées**
  - 🎬 Pistes ouvertes de la session du 21/08/2026 — déménagées
  - ✅ Validation terrain complète — session du 21/08/2026

---

## 🧭 Le projet — vue d'ensemble

### Structure du dossier

```
nimm-epub/
├── main.py                — Serveur FastAPI, toutes les routes HTTP
├── core/
│   └── epub_parser.py     — Extraction chapitres, métadonnées, images de couverture
├── modules/
│   ├── tts.py             — Synthèse vocale : EDGE, KOKORO, PIPER, KYUTAI, XTTS, NEUTTS, POCKET (+ leurs catalogues)
│   ├── tts_cache.py       — Cache audio disque (quota réglable, purge des plus anciens)
│   ├── decoupage.py       — Le découpage en PHRASES : une seule règle, + celle du mode dialogue (18/09/2026)
│   ├── incises.py         — Retrait des incises de parole (« dit-il ») avant le moteur (18/09/2026)
│   ├── silence.py         — Un silence court pour la phrase qui n'est QU'UNE incise (18/09/2026)
│   ├── majuscules.py      — Mots TOUT EN MAJUSCULES remis en casse normale, sigles préservés (19/09/2026)
│   ├── prononciation.py   — Prononciation française imposée à Kokoro et Piper (20/09/2026)
│   ├── audio_trim.py      — Rognage des silences de bord (ffmpeg embarqué)
│   ├── audio_rate.py      — Vitesse par post-traitement ffmpeg (moteurs sans réglage natif)
│   ├── audio_gain.py      — Niveau de la parole ramené à celui des autres moteurs (Kyutai)
│   ├── voice_casting.py   — Casting IA : analyse, fiche de personnages, attribution des voix
│   └── config.py          — Clés API (data/config.json, hors Git)
├── kyutai_service/        — Moteur de voix Kyutai, lancé À PART (Python 3.12 + PyTorch)
│   ├── servir_kyutai.py   — Service HTTP local (127.0.0.1:8082)
│   ├── INSTALLER_KYUTAI.bat — Installation unique (environnement, voix, modèle)
│   ├── DEMARRER_KYUTAI.bat  — Allume le moteur
│   ├── tester_service.py  — Écoute de contrôle du branchement
│   ├── tester_toutes_voix.py — Lot d'écoute des 35 voix (étiquetage H/F, étoiles)
│   ├── voix_fr/cml-tts/fr/ — Les 35 voix françaises libres de la banque Kyutai (hors Git)
│   └── LIRE_MOI.md        — Mode d'emploi + ATTRIBUTION.md (licences)
├── xtts_service/          — Moteur XTTS v2 (voix clonées depuis des extraits), lancé À PART (port 8083)
│   ├── servir_xtts.py     — Service HTTP local (127.0.0.1:8083)
│   ├── INSTALLER_XTTS.bat — Installation unique (environnement, modèle, voix)
│   ├── DEMARRER_XTTS.bat  — Allume le moteur
│   └── LIRE_MOI.md        — Mode d'emploi + ATTRIBUTION.md (licences)
├── neutts_service/        — Moteur NeuTTS (voix décrites par un extrait + son texte), À PART (port 8084)
│   ├── servir_neutts.py   — Service HTTP local (127.0.0.1:8084)
│   ├── INSTALLER_NEUTTS.bat — Installation unique (environnement, torch épinglé)
│   ├── DEMARRER_NEUTTS.bat  — Allume le moteur
│   └── LIRE_MOI.md        — Mode d'emploi + ATTRIBUTION.md (licences)
├── pocket_tts_service/    — Moteur Pocket TTS (18 voix, tourne sur le processeur), À PART (port 8085)
│   ├── servir_pocket_tts.py — Service HTTP local (127.0.0.1:8085)
│   ├── INSTALLER_POCKET_TTS.bat — Installation unique (environnement, modèle, voix)
│   ├── DEMARRER_POCKET_TTS.bat  — Allume le moteur, dans SA fenêtre (l'arrêt se fait là)
│   └── LIRE_MOI.md        — Mode d'emploi + ATTRIBUTION.md (licences)
├── test_voix/             — L'atelier : les tests, les mesures, les bancs d'écoute (voir son LIRE_MOI.md)
├── Extraits de voix/      — Les extraits de voix libres de droits, sources des clonages (hors Git)
├── frontend/
│   ├── index.html         — Interface unique : bibliothèque + lecteur (+ version de cache `?v=`)
│   ├── app.js             — Logique client : navigation, lecture, casting, RSVP, mode dialogue
│   ├── styles.css         — UI mobile-first, PWA-ready, animations (glitch, cadenas)
│   └── manifest.json      — Déclaration PWA (icône, nom, affichage plein écran)
├── data/                  — Tout ce qui est local (hors Git)
│   ├── library/           — Les EPUBs stockés sur le PC
│   ├── nimm_epub.db       — SQLite : livres, profils, progression, voix, attributions
│   ├── tts_cache/         — Le cache audio (regénérable, purgé au-delà du quota)
│   ├── config.json        — Les clés API
│   ├── moteur_voix.txt    — Le moteur de voix retenu pour le prochain démarrage
│   └── annotations_voix.json — Les notes d'écoute (genre, étoiles, remarque)
├── START.bat              — Lance le lecteur (port 8081) et le moteur de voix choisi
├── README.md              — Présentation du projet
├── BACKLOG.md             — Ce qui reste à faire, par priorité
├── CONTRIBUER.md          — Les règles de travail entre Laurent et Cline
├── requirements.txt       — Les bibliothèques Python du lecteur
└── ARCHITECTURE.md        — Ce fichier : la mémoire technique
```

---

### Principe général

NIMM ePub est un serveur local Python (FastAPI) accessible depuis n'importe quel
appareil connecté au même réseau Tailscale. Le navigateur du téléphone sert de
lecteur — les fichiers EPUB restent sur le PC.

Aucun module ne parle directement à un autre. main.py orchestre tout.

---

### Flux principal

1. L'utilisateur ouvre NIMM ePub dans le navigateur (http://[IP-Tailscale]:8081)
2. Il upload un EPUB depuis son téléphone → stocké dans data/library/
3. Il sélectionne un livre dans sa bibliothèque
4. Le texte est extrait chapitre par chapitre par epub_parser.py
5. Le chapitre est découpé en phrases et paragraphes côté client (app.js)
6. Il lit dans le navigateur, avec TTS Edge si souhaité
7. Sa progression (chapitre + position) est sauvegardée automatiquement en SQLite

---

### Dépendances Python

Environnement du **lecteur** (Python 3.14, installation globale) :

```
fastapi
uvicorn
ebooklib
beautifulsoup4
edge-tts
httpx          — casting IA + appel du service Kyutai
pydantic
kokoro-onnx    (+ onnxruntime)   — moteur Kokoro
piper-tts                        — moteur Piper
soundfile                        — écriture des WAV
pedalboard                       — décalage de hauteur (Rubber Band)
imageio-ffmpeg                   — ffmpeg embarqué (rognage des silences, vitesse)
```

Environnement du **moteur Kyutai** (`kyutai_service/.venv`, Python 3.12,
séparé et non versionné) :

```
torch 2.9.1+cu128   — PyTorch, CUDA 12.8 (≈ 2,9 Go téléchargés)
moshi 0.2.13        — code d'inférence de Kyutai (poids tts-1.6b-en_fr)
sounddevice, sphn, sentencepiece, safetensors, einops, aiohttp (dépendances de moshi)
```

**Depuis le 12/09/2026, les dépendances sont figées** dans deux fichiers :

- `requirements.txt` (racine) — l'environnement du **lecteur** (Python 3.14) :
  versions exactes relevées sur l'installation qui fonctionne ;
- `kyutai_service/requirements.txt` — l'environnement **séparé** du moteur
  Kyutai (Python 3.12 + PyTorch build CUDA 12.8), avec la commande
  d'installation complète.

Deux environnements dans un même dossier de travail : VS Code analyse
`kyutai_service/` avec le Python du **lecteur**, qui ne connaît ni `moshi` ni
`torch` (ils vivent dans `.venv`) — d'où un fichier
`kyutai_service/pyrightconfig.json` (`reportMissingImports: "none"`, même
réglage que l'atelier NIMM Voix) qui évite ces faux positifs de l'éditeur.
Il n'y a donc **rien à corriger** quand VS Code souligne ces deux imports.

Réinstallation sur une autre machine : `python -m pip install -r
requirements.txt`, puis `START.bat` (et `INSTALLER_KYUTAI.bat` si on veut le
moteur de voix). Contrôle automatique de cohérence :
`test_voix/test_requirements.py` compare les deux fichiers aux environnements
réellement installés (paquet par paquet, sans réseau).

---

### Workflow de développement

#### Rôles
- **Laurent** — product owner, valide chaque choix avant production de code
- **Claude** — analyse, propose, produit les blocs sur confirmation
- **Cline (VSCode + DeepSeek)** — exécute les blocs dans le projet

#### Règles strictes
- Analyse et discussion sans limite — le code, c'est du sur-mesure validé
- Aucun bloc de code produit sans confirmation explicite de Laurent
- Un bloc à la fois, confirmation entre chaque
- Les blocs sont copiables directement dans Cline (FIND/REPLACE)

#### Format des blocs

```
⚠️ ## Bloc #XX
➡️ fichier cible : [filename]
**FIND**
[texte exact à trouver — ou "(fichier existant — remplacer tout le contenu)" / "(fichier inexistant — créer)"]
**REPLACE**
[remplacement complet]
```

---

### Ordre de développement des fichiers
1. ARCHITECTURE.md ✅
2. main.py ✅
3. core/epub_parser.py ✅
4. modules/tts.py ✅
5. data/nimm_epub.db (créé automatiquement au démarrage) ✅
6. frontend/index.html ✅
7. frontend/styles.css ✅
8. frontend/app.js ✅
9. manifest.json ✅
10. START.bat ✅

---

## 🖥️ Le serveur : main.py et la base

### main.py — Routes HTTP

| Route | Méthode | Rôle |
|---|---|---|
| `/` | GET | Sert index.html |
| `/api/books` | GET | Liste les livres de la bibliothèque |
| `/api/books/upload` | POST | Upload d'un EPUB depuis le téléphone |
| `/api/books/{id}` | GET | Métadonnées + liste des chapitres |
| `/api/books/{id}/chapter/{n}` | GET | Texte brut du chapitre N |
| `/api/books/{id}/cover` | GET | Image de couverture |
| `/api/progress/{id}` | GET | Récupère la progression sauvegardée |
| `/api/progress/{id}` | POST | Sauvegarde chapitre + position scroll |
| `/api/tts` | POST | Synthèse vocale → stream audio MP3 (voix + rate + pitch) |
| `/api/voices` | GET | Liste des voix **écoutables tout de suite** (les voix d'un moteur éteint ne sont pas proposées) |
| `/api/voix_catalogue` | GET | **Toutes** les voix du catalogue (moteurs éteints compris) : sert à **nommer** une voix déjà attribuée, avec sa famille et un drapeau `dispo` |
| `/api/moteurs` | GET | État des moteurs de voix lourds : Kyutai (8082), XTTS v2 (8083) → `{actif, pret, nom}` |
| `/api/moteur/basculer` | POST | **Change de moteur de voix** (`xtts`, `kyutai` ou `aucun`) : éteint l'autre **avant** d'allumer, note le choix pour le prochain démarrage, renvoie l'état frais. Appelée par le bouton en bas de la fenêtre de lecture |
| `/api/annotations_voix` | GET | Notes d'écoute prises dans la fenêtre « Écouter les voix » (genre, étoiles, remarque) |
| `/api/annotations_voix` | POST | Enregistre — ou **efface** si la note est vide — la note d'une voix |
| `/api/books/{id}/search` | GET | Recherche d'un mot exact dans tout le livre |
| `/api/books/{id}/cast` | POST | Démarre l'analyse voix multiples (1er chapitre en direct, suite en tâche de fond) |
| `/api/books/{id}/cast/status` | GET | Avancement du traitement (`none`/`processing:n/N`/`done`/`error`) |
| `/api/books/{id}/cast/voice` | PUT | Change manuellement la voix attribuée à un personnage |
| `/api/books/{id}/cast/lock` | PUT | Verrouille/déverrouille une voix (à conserver lors d'un re-cast) |
| `/api/books/{id}/cast/reassign` | POST | Re-cast gratuit : redistribue les voix non verrouillées sans appel IA |
| `/api/books/{id}/cast/autogroup` | POST | Détecte/regroupe les doublons d'écriture (accents, tirets, article) |
| `/api/books/{id}/cast/ungroup` | POST | Détache un alias de sa fiche (redevient indépendant) |

**Middleware global** : toute route commençant par `/api/` reçoit
automatiquement l'en-tête `Cache-Control: no-store` (voir section Cache
HTTP plus bas) — évite d'avoir à le déclarer route par route.

---

### data/nimm_epub.db — Base SQLite

#### Tables

**books**
```
books (id, filename, title, author, cover_path, date_added)
```

**progress**
```
progress (book_id, chapter_index, scroll_position, cursor_idx, last_read)
```

**books** — gagne 2 colonnes pour le chantier voix multiples :
```
multi_voice_enabled INTEGER DEFAULT 0   -- toggle par livre
cast_status          TEXT DEFAULT 'none' -- none / processing:n/N / done / error
```

**voices** (nouvelle, session voix multiples) — voix + pitch définitifs
par personnage, un livre à la fois :
```
voices (book_id, character_name, voice_id, pitch, genre, line_count)
PRIMARY KEY (book_id, character_name)
```
`genre` (H/F) et `line_count` (nombre de répliques sur tout le livre)
sont utilisés uniquement pour l'affichage dans la fenêtre du casting
(voir section dédiée plus bas) — aucun impact sur la lecture TTS
elle-même, qui n'a besoin que de `voice_id`/`pitch`.

**speaker_attribution** (nouvelle, session voix multiples) — locuteur de
chaque phrase, chapitre par chapitre :
```
speaker_attribution (book_id, chapter_index, sentence_idx, speaker)
PRIMARY KEY (book_id, chapter_index, sentence_idx)
```
`sentence_idx` correspond exactement au `data-idx` utilisé côté
`app.js` — correspondance directe, aucune conversion nécessaire à la
lecture.

---

### Profils familiaux (multi-utilisateurs) — main.py + index.html + app.js + styles.css

#### Rôle
Permet à plusieurs membres de la famille (Laurent, Maya, Nadia) d'utiliser
NIMM ePub depuis leurs propres téléphones via Tailscale, chacun avec sa
bibliothèque et ses progressions de lecture totalement séparées. Pas de
mot de passe — simple écran "Qui lit ?" au démarrage de l'app.

#### Base de données

**Table `users`** (nouvelle) :
```
users (id, name)
```
Remplie automatiquement si vide par `init_db()` : **Laurent**, **Maya** et
**Nadia** — chacun gardé par un test d'existence (`SELECT COUNT(*)`), pour que
la liste puisse s'allonger sans jamais créer de doublon.

**Table `books`** : gagne une colonne `user_id INTEGER NOT NULL` —
chaque livre appartient à un seul profil dès sa création (pas de partage
entre profils, chacun uploade indépendamment, y compris pour un même
roman lu par les deux).

**Table `progress`** : la clé primaire passe de `book_id` seul à
**`(user_id, book_id)`** composite. Permet en théorie à deux profils
d'avoir chacun leur progression sur un même `book_id` (même si dans la
pratique actuelle, un livre n'appartient qu'à un profil).

#### Routes API
Toutes les routes liées aux livres et à la progression exigent
maintenant un paramètre `user_id` (query string) et filtrent leurs
requêtes SQL en conséquence : `/api/books`, `/api/books/upload`,
`/api/books/{id}`, `/api/books/{id}/chapter/{n}`, `/api/books/{id}/cover`,
`/api/progress/{id}` (GET/POST), `/api/books/{id}/search`, `delete_book`.

Sans le bon `user_id`, ces routes renvoient 404 — un profil ne peut pas
accéder aux livres d'un autre, même en devinant un ID (sécurité simple,
cohérente avec l'absence de mot de passe : empêche le croisement
accidentel, pas une attaque délibérée).

Nouvelle route : `GET /api/users` → liste les profils disponibles
(`[{"id":1,"name":"Laurent"}, {"id":2,"name":"Maya"}, {"id":3,"name":"Nadia"}]`).

#### Frontend — écran "Qui lit ?"
Nouvelle vue `#view-profile`, affichée **en premier** au chargement de
la page (avant la bibliothèque). Contient un bouton par profil
(`.profile-card`, juste le prénom en texte, pas d'avatar), généré
dynamiquement par `renderProfiles()` à partir de `/api/users`.

Au clic sur un profil → `selectProfile(userId)` stocke l'ID dans
`_currentUserId` (variable globale JS, en mémoire uniquement, jamais
persistée), puis bascule vers la bibliothèque.

**Pas de bouton "changer de profil"** — comportement volontaire et
validé : pour changer de profil, il faut fermer et rouvrir l'app. Toute
nouvelle vue ajoutée doit penser à `showView()` (cf. point d'attention
déjà documenté dans la section RSVP plus haut — `#view-profile` y a été
ajoutée comme les autres).

`_currentUserId` est ensuite systématiquement transmis en query string
(`?user_id=...`) par toutes les fonctions JS qui appellent l'API :
`loadLibrary`, `openBook`, `loadChapter`, `saveProgress`, l'upload, la
suppression de livre, et `_runSearch`.

#### Migration
Aucune migration automatique des anciennes données (`books`/`progress`
sans `user_id`) — décision validée : on est repartis d'une base SQLite
vidée manuellement (suppression de `data/nimm_epub.db` et des fichiers
dans `data/library/`) avant le premier démarrage avec la nouvelle
structure.



---

## 🎬 La page (frontend) et la lecture

### frontend/ — Interface

#### Deux vues dans une seule page
- **Bibliothèque** : grille de livres (couverture + titre + auteur), bouton upload
- **Lecteur** : texte du chapitre, navigation chapitres, barre TTS, curseur glitch

#### Chargement d'un chapitre — jamais de chapitre sauté (18/09/2026)
Constat de Laurent : « parfois le chapitre ne se charge pas correctement, et
zappe complètement un chapitre : il passe du quatre-vingt-un au
quatre-vingt-trois, surtout après une erreur de chargement ».

Cause : `loadChapter()` posait `_currentChapter = index` **avant** la requête.
Un échec laissait donc le lecteur sur le chapitre raté, avec les phrases du
chapitre **précédent** encore en mémoire ; à la fin de leur lecture,
l'enchaînement automatique appelait `loadChapter(_currentChapter + 1)` — et le
chapitre raté était sauté.

Correction, en trois temps (`frontend/app.js`) :
- `_demanderChapitre(index)` fait la requête et renvoie `null` en cas d'échec ;
  `_currentChapter` n'est posé qu'une fois la réponse **reçue** ;
- un échec est **retenté** (`CHARGEMENT_ESSAIS = 3`, `CHARGEMENT_PAUSE_MS =
  1200`) : un échec de chargement est presque toujours passager (serveur occupé,
  réseau qui vacille) ;
- après un échec définitif, `_afficherEchecChapitre()` **vide** `_sentences` et
  `_paragraphStarts` (plus de lecture fantôme de l'ancien chapitre) et affiche un
  message ainsi qu'un bouton `.chapter-retry-btn` (« Réessayer ce chapitre »).
- Au passage, `_pause(ms, signal)` accepte désormais l'absence de signal : elle
  le supposait toujours présent, ce qui aurait fait échouer la pause entre deux
  essais.

Vérification : `test_voix/test_chargement_chapitre.js` (**17 contrôles**) —
sans navigateur, il **exécute** le vrai code de `app.js` sur un faux DOM et un
faux serveur : panne persistante, panne passagère (un seul essai), chargement
normal.

#### Cartes de livres sur mobile — titre en entier (15/09/2026)
Demande de Laurent : sur son téléphone, la **couverture était rognée** par le
cadre de la vignette et le titre, limité à deux lignes, ne disait pas toujours
de quel livre il s'agissait. Choix retenu (**option A**) : la vignette reste
**recadrée** au format 2/3 (`.book-cover`, `object-fit: cover`) pour garder une
grille régulière, et c'est le **texte sous la vignette** qui rattrape
l'information — sur mobile, `.book-title` ne se limite plus à 2 lignes :
il s'affiche **en entier**, un peu plus grand, et `.book-author` passe à la
ligne au lieu d'être tronqué (`@media (max-width: 640px)`,
`frontend/styles.css`).

#### Grille de la bibliothèque — hauteur des lignes (16/09/2026)
Constat de Laurent sur mobile : les couvertures n'apparaissaient plus que sur
une bande du tiers haut, largeur intacte, les cartes se chevauchant « comme un
jeu de cartes qu'on fait glisser ». Cause : avec assez de livres pour remplir
plusieurs lignes, le navigateur dimensionnait les pistes `auto` de `#book-grid`
sur la hauteur **minimale** d'une carte. Or cette hauteur minimale est vue
comme **nulle** : le ratio 2/3 de la vignette dépend de la largeur, qui
dépend de la colonne (référence circulaire). Les données, elles, étaient
saines (18 couvertures valides en base et sur le disque). Correctif :
`grid-auto-rows: max-content` sur `#book-grid` — chaque ligne prend la hauteur
réelle de son contenu, les vignettes conservent leur ratio 2/3.
Sur PC, l'effet est le même dès qu'il y a beaucoup de livres (titres limités à
3 lignes, donc moins de hauteur de texte, mais la grille reste concernée).
Vérification : `test_voix/test_couverture_mobile.py` (Playwright/Chromium, sans
serveur : injecte le vrai `frontend/styles.css`, 12 livres, texte normal puis
agrandi à 130 % et 200 %). Avant correctif : 12/12 cartes écrasées (115 px de
haut pour 340 à 414 px de contenu). Après : 0/12, vignette au ratio attendu.

#### Pas de framework
HTML/CSS/JS vanilla. Même approche que NIMM.

#### PWA
- manifest.json déclaré dans index.html
- Installable sur l'écran d'accueil Android depuis Chrome
- Fonctionne en plein écran via Tailscale
- `frontend/icon.png` (512×512) et `frontend/apple-touch-icon.png`
  (180×180) — fichiers requis par `manifest.json` et `index.html`,
  absents lors de la création initiale du projet (cause du logo
  générique affiché par Firefox tant qu'ils manquaient). Générés à
  partir du logo NIMM ePub (livre + bouche + ondes sonores, sans texte).

#### Accès HTTPS via Tailscale Serve
NIMM (chatbot, port 8080) et NIMM ePub (port 8081) tournent sur la même
machine et partagent le même nom Tailscale (`desktop-j60c3lb.tail6ba9d3.ts.net`),
chacun exposé en HTTPS sur un port dédié via Tailscale Serve :

```
tailscale serve --bg --https=443  http://localhost:8080   # NIMM (chatbot)
tailscale serve --bg --https=8081 http://localhost:8081   # NIMM ePub
```

- NIMM (chatbot) → `https://desktop-j60c3lb.tail6ba9d3.ts.net` (port 443
  implicite, pas visible dans l'URL)
- NIMM ePub → `https://desktop-j60c3lb.tail6ba9d3.ts.net:8081`

**Adresse de référence pour NIMM ePub : la ligne du dessus.** Éviter
l'IP Tailscale brute (`http://100.x.x.x:8081`) une fois la PWA installée
en HTTPS — mélanger les deux peut déclencher des erreurs de type
"Client sent an HTTP request to an HTTPS server" (confusion HSTS/cache
navigateur sur le même port). `tailscale serve status` permet de
vérifier les règles actives à tout moment.

**Firefox vs Chrome (PWA) :** Firefox Android installe en plein écran
mais lit le manifest de façon moins fiable que Chrome dans certains cas
(icône générique si un fichier référencé est introuvable). Vérifier que
`icon.png` et `apple-touch-icon.png` existent bien physiquement dans
`frontend/` si l'icône n'apparaît pas comme prévu.

**📲 « Je n'ai pas l'option Installer l'application » — le piège des icônes
(20/09/2026).** Constat de Laurent : Chrome lui propose d'installer **NIMM** (le
chatbot) mais **pas NIMM ePub**, alors que Brave et Firefox le laissent faire.
**Cause trouvée** : le manifeste déclarait **trois fois la même image**
(`icon.png`, 512×512) en annonçant `192x192`, `512x512` **et** `2048x2048`.
Chrome **vérifie que la taille annoncée correspond au fichier** : il rejetait donc
toutes les icônes — et sans icône valide de 192 px, l'entrée d'installation
n'apparaît pas. (Brave est plus permissif, et « installer » avec Firefox Android
n'est qu'un **raccourci**, pas une application.)

*Ce qui a été corrigé* : **un fichier par taille** — `icon-192.png` (192×192),
`icon-512.png` (512×512), `apple-touch-icon.png` (180×180) et
`icon-maskable-512.png` (512×512 **avec marge de sécurité**, pour que le lanceur
Android ne rogne pas le logo) — plus les `<link rel="icon">` correspondants dans
la page, un `start_url` propre (`/`) et un `id`. Les icônes se **régénèrent**
depuis le logo maître (`frontend/image_NIMM_ePub.png`, 1523×1523) avec
`test_voix/_generer_icones_pwa.py --ecrire`.

⚠️ **Le fichier `icon.png` (512×512) est conservé** : il n'est plus déclaré par
le manifeste, mais il peut encore servir d'icône à un raccourci déjà installé sur
un téléphone. *Vérification* : `test_voix/test_pwa_manifeste.py` (le manifeste,
**la taille réelle de chaque icône**, les critères d'installation de Chrome, et
le service worker sans lequel rien ne s'installe).

**Un bouton DANS l'application (20/09/2026).** Comme Chrome ne dit jamais
*pourquoi* il refuse d'installer (et que Laurent ne trouvait pas l'entrée du
menu), la bibliothèque porte un bouton **« 📲 Installer l'application »**
(`#installer-btn`) :

- si le navigateur sait installer (`beforeinstallprompt`, les Chromium), il
  déclenche **sa** fenêtre d'installation (`prompt()`) — plus besoin de chercher
  une icône dans la barre d'adresse ;
- s'il ne propose rien (Firefox, ou navigateur qui ne juge pas l'application
  installable), il **écrit où chercher** au lieu de ne rien faire ;
- il **disparaît** quand l'application tourne déjà comme une application
  installée (`display-mode: standalone`) ou après une installation réussie
  (`appinstalled`).

*Pourquoi deux issues* : un bouton qui reste muet au clic est un bouton qu'on
croit cassé — ici, **jamais** de silence. *Vérification* :
`test_voix/test_ids_ecran.py` (§ 3 septies).

**⚠️ Le piège qui expliquait tout (20/09/2026) : le navigateur INTÉGRÉ.** Laurent
voyait bien le bouton, mais il tombait sur la note « ton navigateur n'a pas
proposé l'installation » — et son menu (⋮) ne proposait **pas** « Installer »,
mais « **Ouvrir dans le navigateur Firefox** » et « **Ouvrir NIMM** » (avec un
bref passage par le logo et le 🥨 de NIMM avant d'afficher NIMM ePub). Lecture :
il n'était **pas dans Chrome**, mais dans le **navigateur intégré à une autre
application** (page ouverte depuis l'appli NIMM ou depuis le launcher) — et
**une fenêtre intégrée ne peut pas installer d'application**, c'est une limite
d'Android. Deuxième enseignement : son **navigateur par défaut est Firefox**, et
Firefox n'installe qu'un raccourci — d'où l'absence d'application et, plus tôt,
le DNS sécurisé, le raccourci au lieu d'une application et la lecture qui
s'arrête au verrouillage. **Le remède** : ouvrir l'adresse **directement dans
Chrome ou Brave** (icône du navigateur → taper l'adresse complète, `:8081`
compris → Entrée), et non par une page ouverte depuis une autre application. La
note du bouton dit maintenant ces deux causes.

**Pourquoi préférer CHROME ou BRAVE** (les deux Chromium) pour la PWA :
`navigator.mediaSession` y est complet — donc la **couverture**, la **barre de
progression** et les **boutons de l'écran verrouillé** fonctionnent (voir
« Lire écran verrouillé » plus bas) — et une application **installée** (WebAPK)
survit bien mieux au verrouillage qu'un onglet. Firefox Android, lui, n'installe
qu'un **raccourci**, a une Media Session réduite, et il est le navigateur de la
famille qui a déjà eu le problème de **DNS sécurisé** avec `*.ts.net`.

**🔎 Mémo diagnostic — « l'appli ne s'affiche pas depuis le téléphone »
(20/09/2026).** Vécu par Laurent : chez sa mère, **NIMM et NIMM ePub ne
s'affichaient pas**, alors que le **launcher** (`http://100.75.88.88:8765`)
répondait normalement, sans que rien n'ait changé sur le PC. **Ce contraste est
la clé du diagnostic** :

| Ce qui marche | Ce qui ne marche pas | Ce que ça veut dire |
|---|---|---|
| le launcher : IP + **HTTP** | les deux apps : **nom** + HTTPS | le tunnel est **debout**, c'est le **nom** (`*.ts.net`) ou le HTTPS qui tombe **côté téléphone** |

*Côté PC, à vérifier dans l'ordre (tout en lecture seule)* :
1. `tailscale status` → le PC et les téléphones de la famille sont-ils en ligne ?
2. `tailscale serve status` → les deux règles sont-elles là (443 → 8080,
   8081 → 8081) ?
3. les ports (`Get-NetTCPConnection -State Listen`) : **8080** (NIMM) et **8081**
   (NIMM ePub) écoutés — et sur 8081, l'**adresse Tailscale appartient à
   `tailscaled`** (le relais HTTPS), donc `http://100.75.88.88:8081` répond
   **400 « Client sent an HTTP request to an HTTPS server »** : c'est normal,
   c'est documenté juste au-dessus ;
4. le certificat : `curl -sS -o NUL -w "%{http_code} %{ssl_verify_result}"
   https://…:8081/` → attendu **200** et **0** (0 = vérification OK).
   ⚠️ **Piège du 20/09/2026** : un contrôle en **Python**
   (`ssl.create_default_context()` + `getpeercert()`) annonçait
   « certificate has expired » alors que le certificat était **valide**
   (13/09 → 12/12/2026, confirmé par `curl` **et** par .NET). **Vérifier un
   certificat avec `curl` ou `Invoke-WebRequest`, pas avec le `ssl` de Python
   sur cette machine.**
5. `tailscale cert <fqdn>` **génère** un certificat à la demande — à savoir :
   la commande **écrit deux fichiers dans le dossier courant** (`.crt` et
   `.key`). Ne jamais les laisser traîner, surtout pas dans le dépôt :
   préférer `--cert-file <chemin> --key-file <chemin>`.

*Côté téléphone*, c'est presque toujours **le même coupable**, déjà documenté
plus bas (section « cache HTTP ») : le **DNS sécurisé** (DNS over HTTPS) résout
`*.ts.net` chez Cloudflare/NextDNS **au lieu de** Tailscale → le nom ne se
résout plus, **même VPN actif**. Checklist dans l'ordre :
1. **DNS sécurisé** : Firefox (Paramètres → Vie privée → DNS sécurisé →
   **Désactivé**) ; sur Android, « **DNS privé** » ne doit pas viser un
   fournisseur ;
2. **Batterie sans restriction** pour Tailscale **et** pour le navigateur/PWA ;
3. **VPN toujours actif** si l'appareil le propose ;
4. **couper/rallumer le VPN Tailscale** sur le téléphone (10 s) **avant** de
   redémarrer : le redémarrage **reconstruit** la configuration DNS/VPN de
   Tailscale, c'est pourquoi il a « réparé » le problème le 20/09.

*Plan B possible, non retenu à ce jour* : un second accès en **HTTP clair** sur
un port libre, `tailscale serve --bg --http=8082 http://localhost:8081` → le
téléphone utiliserait `http://100.75.88.88:8082`, comme le launcher, sans
dépendre du nom ni du certificat. À décider avec Laurent (le PWA perd son
« service worker » en HTTP clair).

⏰ **À surveiller** : la **clé de ce PC expire le 24/10/2026** (`Self.KeyExpiry`
de `tailscale status --json`) — à cette date, l'ordinateur **sort du tailnet**
et plus rien n'est joignable. Désactiver l'expiration de cette machine dans la
console Tailscale (Machines → … → *Disable key expiry*).

---

### Logique TTS — app.js

#### Structure de données
Le texte de chaque chapitre est découpé côté client en deux niveaux :

```
Chapitre
 ├── Paragraphe 0
 │    ├── Phrase 0  ← span data-idx="0"
 │    ├── Phrase 1  ← span data-idx="1"
 │    └── Phrase 2  ← span data-idx="2"
 ├── Paragraphe 1
 │    ├── Phrase 3  ← span data-idx="3"
 │    └── Phrase 4  ← span data-idx="4"
 └── ...
```

- `_sentences[]` — tableau plat de toutes les phrases `{text, paraIdx}`
- `_paragraphStarts[]` — index de la première phrase de chaque paragraphe
- `_cursorIdx` — position du curseur glitch (phrase en cours)

#### Curseur glitch
- Toujours actif sur une phrase, que le TTS soit en lecture ou non
- Sert de repère visuel au coup d'œil (pas besoin de regarder l'écran)
- Remplace le tooltip "Lire à partir d'ici" sur mobile
- Le tooltip reste disponible sur desktop (sélection de texte → clic)

#### Sélection de texte régularisée (desktop, 23/08/2026, 2e passe)
Au `mouseup` sur le lecteur, `_selectionSentenceRange()` calcule la plage
de phrases couverte par la sélection (`anchorNode`/`focusNode` → spans
`.sentence-span` → `data-idx`, min/max) et la sélection est **étendue au
début de la première phrase et à la fin de la dernière** : la sélection
est toujours un nombre entier de phrases, jamais 1 seul mot au milieu
d'une phrase.
- Clic "Lire à partir d'ici" sur **plusieurs phrases** : lecture bornée
  de la première à la dernière phrase de la sélection (`_runTTS(start, end)`)
  puis arrêt — pas de passage automatique au chapitre suivant (`endIdx` défini).
- Sélection sur **une seule phrase** : lecture continue à partir d'elle,
  comportement historique inchangé.

#### "Lire à partir d'ici" sur mobile (23/08/2026, 2e passe — **modifié le 15/09/2026**)
Sur mobile, le long-press sur le texte déclenche le menu natif du navigateur
(copier/coller) : la sélection "Lire à partir d'ici" du desktop est donc
inutilisable. Le lecteur détecte l'appareil tactile (`_isTouchDevice`,
`ontouchstart` / `maxTouchPoints`) et propose :
- **Tap simple sur une phrase** : depuis le **15/09/2026** (demande de Laurent),
  il n'entraîne **plus** la lecture : il ouvre le **panneau « voix de cette
  phrase »** (voir la section suivante). Un tap ne fait rien d'autre — la
  lecture "à partir d'ici" passe désormais par la sélection longue.
- **Sélection longue** : le tooltip "Lire à partir d'ici" s'affiche aussi
  au-dessus des poignées natives (détection via `selectionchange`, plus
  fiable que `mouseup` sur tactile), avec lecture bornée de la plage couverte.
  La sélection visuelle n'est **pas** étendue aux phrases complètes sur
  mobile (contrairement au desktop) pour ne pas casser le copier/coller
  natif — le bouton calcule quand même la plage de phrases via
  `_selectionSentenceRange()`.
- Les clics souris (desktop) sont ignorés par le tap via
  `e.pointerType === 'mouse'` pour ne pas perturber la sélection de texte
  native.

#### Panneau « voix de cette phrase » (15/09/2026)
Demande de Laurent : sur mobile, il voulait voir **à qui appartient la voix**
d'une phrase et pouvoir la changer — sans que le tap lance la lecture.

- **Ouverture** : tap sur une phrase (mobile, hors fin de sélection) ou bouton
  **« 🎭 Voir la voix »** du tooltip de sélection (PC, ajouté à côté de « Lire à
  partir d'ici »). Les deux passent par `_openVoicePanel(idx)`.
- **Contenu** : début de la phrase, **qui parle** (`_personnageDePhrase()` :
  le personnage attribué, ou *Narration* quand la phrase n'en a pas — valeur
  `narration` incluse), et **la voix** réellement utilisée
  (`_voixDePhrase()` : voix de la fiche de casting, sinon voix du lecteur).
  La voix est **nommée par le catalogue** (`_libelleCatalogue`), jamais par son
  identifiant technique, et les réglages non neutres sont rappelés
  (« vitesse +10 % · hauteur −8 Hz »).
- **Changement — la LISTE des voix (22/09/2026)** : un **menu déroulant**
  (`_remplirMenuVoixPhrase`, groupes Femmes / Hommes / Autres) occupait cette
  place. Il a été **remplacé** par une **liste de l'application** (voie **B**,
  choisie par Laurent) : la liste ouverte d'un menu déroulant est **dessinée par
  le téléphone** (fond clair, grosse police), et son libellé ne peut **pas**
  passer à la ligne sur commande — c'est **mesuré**, voir « Le saut de ligne dans
  un libellé de menu » plus haut. La liste, elle, est faite de vrais éléments de
  page : elle prend le thème, et chaque voix s'écrit sur **DEUX lignes**
  — `♀️ Anna 🇫🇷 adulte grave`, puis `🧬 · LIBRE` (état de la voix). Un **▶** par
  voix l'écoute **sans rien changer**, un **tap sur la ligne** choisit la voix
  (marquée d'un **✔** et d'un liséré doré), et un **champ de recherche** filtre
  par prénom ou provenance — jusqu'à 175 voix, là où le menu les faisait défiler
  à l'aveugle. Architecture : `_lignesVoixListe()` est une fonction **pure**
  (elle rend les lignes : groupes, tri par prénom, recherche, et la voix en place
  mais plus proposée gardée sous « ⚠️ Voix actuelle »), `_peindreListeVoixPhrase()`
  les dessine, et `_choisirVoixPhrase()` reprend **exactement** l'ancien
  gestionnaire `change`. Pour un **personnage**, l'enregistrement passe par
  `_updateCharacterVoice()` (route `PUT /api/books/{id}/cast/voice`, la même que
  la fenêtre du casting) — elle renvoie **`true`/`false`** pour que le panneau
  dise si l'enregistrement a réussi ; pour *Narration*, c'est `#voice-select`
  (voix du lecteur) qui est changé. Dans les deux cas, une lecture en cours est
  **relancée** pour que le changement s'entende tout de suite (playlist figée par
  construction, cf. la règle du 15/09/2026). *Coût assumé et annoncé* : **un tap
  de plus** pour changer une voix. Le libellé d'une voix est resté **d'une
  ligne** partout ailleurs : `_libelleVoix` est désormais l'assemblage de
  `_identiteVoix()` (symbole, prénom, drapeaux, âge, timbre) et de
  `_iconeMoteurVoix()` (l'icône du moteur).
  *(Audit de la documentation, 22/09/2026 : cette page, et le BACKLOG, nommaient
  la fonction pure « _lignesVoixPhrase() » — un nom qui n'a jamais existé dans
  `app.js`. Le nom réel, vérifié, est `_lignesVoixListe()` : corrigé aux deux
  endroits.)*
- **Aperçu** : bouton « ▶ Écouter » (`_apercuVoixPhrase()`) — la voix
  choisie dit un extrait **de la phrase ouverte**, avec la vitesse et la
  hauteur du personnage (celles du lecteur pour la narration) ; si le moteur
  est éteint, le panneau l'indique sans se bloquer. Depuis le 22/09/2026, la
  fonction prend **la voix et le bouton** (`_apercuVoixPhrase(voixId, btn)`) :
  chaque ▶ de la liste écoute **SA** voix, et le bouton du bas écoute la voix
  marquée.
- **Porte vers le casting (20/09/2026)** : bouton **« 🎭 Ouvrir dans le
  casting »** (`#voice-phrase-cast-btn`). Idée de Laurent le jour même : « cette
  modale est moins riche que Casting des voix ». Le panneau ne change qu'**une**
  voix ; pour le reste — cadenas 🔒, curseurs **vitesse et hauteur**, tiroir 🗣️
  des voix libres, badges d'état — le bouton ouvre la **vraie fenêtre** sur le
  personnage, **surligné** un instant. On n'a donc **pas remplacé** le panneau :
  il est le **seul** à savoir dire **qui parle dans cette phrase** (le casting
  est par livre, pas par phrase), et le geste fréquent (lire → taper → changer
  la voix) doit rester **léger** — la fenêtre du casting, sur un livre à
  176 personnages, ferait perdre la position de lecture. Trois garde-fous :
  le bouton est **caché pour la narration** (le narrateur n'a pas de ligne dans
  le casting : sa voix se change dans le menu du haut) ; le panneau est
  **fermé** en ouvrant le casting (jamais deux fenêtres empilées) ; et la porte
  **ramène toujours au personnage** — si un filtre d'état (« ⚠ à caster »,
  « ⧉ voix partagée », « 🔓 voix libres ») ou la recherche le cachait, on revient
  d'abord à la liste complète, sinon on ouvrirait une fenêtre où il est
  invisible **sans rien expliquer**. Le surlignage réutilise
  `_allerAuPersonnage()`, celui des noms cliquables du badge « partagée avec… » :
  même repère que le 19/09/2026, rien de nouveau à apprendre.
- **Fermeture** : croix, tap à côté de la feuille, ou touche `Échap`. Le
  panneau est aussi fermé au **changement de chapitre** (les index de phrases
  changent, il pointerait sur la mauvaise phrase).
- **Présentation** : feuille collée en bas d'écran sur mobile (avec l'animation
  `slide-up`), petite fenêtre centrée à partir de 641 px de large
  (`frontend/styles.css`). La **liste des voix** défile **elle-même**
  (`max-height: 38vh`) : les boutons du bas (« ▶ Écouter », « 🎭 Ouvrir dans le
  casting ») restent donc atteignables, même avec 175 voix. *Vérification* :
  `test_voix/test_voix_phrase.js` (**50 contrôles**, sans navigateur, dont
  **19 pour la liste des voix** — deux lignes, groupes, tri, recherche, voix hors
  liste — et **5 pour la porte** vers le casting).

#### Navigation

**Barre refaite le 20/09/2026** (demande de Laurent : « J'ai 2 boutons "retour
rapide" qui font la même chose. Si tu peux en retirer un, et mettre tous les
boutons comme des icônes […] un genre de marron foncé, flèches blanches »).
Elle est maintenant **symétrique**, avec **six flèches dessinées (SVG)** autour
du bouton de lecture, et **trois niveaux de saut** — le nombre de triangles dit
la taille du pas :

| Bouton | Action |
|---|---|
| ⏮ chapitre précédent | Chapitre précédent (`#prev-btn`, assombri au premier chapitre) |
| ⏪ retour moyen | **`_PAS_PARAGRAPHES` paragraphes d'un coup** (`#para-prev-btn`) |
| ◀ phrase précédente | **Phrase** précédente (`#sent-prev-btn`) |
| ▶️ / ⏸ | Lecture / Pause depuis le curseur |
| ▶ phrase suivante | **Phrase** suivante (`#sent-next-btn`) |
| ⏩ avance moyenne | **`_PAS_PARAGRAPHES` paragraphes d'un coup** (`#para-next-btn`) |
| ⏭ chapitre suivant | Chapitre suivant (`#next-btn`, assombri au dernier chapitre) |

*Pourquoi trois niveaux* (idée de Laurent, le même jour, après essai) : « le saut
de paragraphe correspond **très souvent** à un saut de phrase » — donc sauter
**un** paragraphe ne se distinguait pas d'un saut de phrase. Le saut moyen saute
donc **plusieurs** paragraphes (`const _PAS_PARAGRAPHES = 4;` dans `app.js` —
**une seule ligne à changer** pour ajuster), et la phrase a sa propre paire
◀ / ▶. Les trois fonctions sont **bornées** : on ne dépasse jamais la fin du
chapitre (le saut est ramené au dernier paragraphe) et on ne recule jamais avant
le début. C'est exactement ce que vérifie `test_voix/test_sauts_navigation.js`
(le pas lu dans le fichier, les trois niveaux, et les bords).

*Pourquoi des SVG et non des emojis* : **un emoji ne peut pas être blanc** — il
garde ses couleurs, ou s'affiche en petit noir et blanc selon le clavier. C'est
ce qui faisait **deux familles de boutons** dans la même barre (chevrons dessinés
pour les chapitres, emojis ⏮⏪⏭ pour les phrases). Les six partagent maintenant
une seule règle de style (`#prev-btn, #next-btn, #para-prev-btn, #para-next-btn,
#sent-prev-btn, #sent-next-btn`), avec les variables `--nav-btn` /
`--nav-btn-survol` / `--nav-btn-bord` (marron foncé dérivé de l'or du thème). La
barre **se resserre sur téléphone** (`@media (max-width: 640px)` puis `380px`) :
six boutons de 40 px et le bouton de lecture ne tiennent pas autrement.

*Historique des retouches* (utile pour ne pas refaire les allers-retours) :
**15/09** — le ⏩ « phrase suivante » est retiré, il doublonnait avec ⏭
« paragraphe suivant » ; **20/09 (matin)** — on retire les deux boutons « en
arrière » côte à côte (⏮ paragraphe et ⏪ phrase, qui semblaient faire la même
chose) au profit d'une paire symétrique, le pas devenant la phrase ; **20/09
(même jour, après essai de Laurent)** — **trois niveaux** : le paragraphe revient
comme saut **moyen** (4 d'un coup) et la phrase gagne sa paire ◀ / ▶. Le
conteneur `#tts-nav` qui enveloppait les boutons a disparu au passage.

**Le mode RSVP a quitté la barre** (même jour) : c'est un **mode de lecture**, pas
une flèche. Il rejoint la ligne des boutons d'action et s'appelle maintenant
**« 👀 Lecture Rapide »** (demande de Laurent), avec le même style que ses
voisins.

*Le casque et l'écran verrouillé* restent sur la **phrase** :
`navigator.mediaSession` (`previoustrack` / `nexttrack`) appelle
`_cursorSentPrev()` / `_cursorSentNext()` — soit exactement le pas des flèches
◀ / ▶ (et non celui des ⏪ / ⏩, qui sautent plusieurs paragraphes).

La navigation pendant la lecture coupe le TTS en cours et repart
immédiatement depuis la nouvelle position du curseur.

#### Le tiroir du menu du bas (22/09/2026)

Demande de Laurent : « Pour le menu du bas, on va faire un tiroir. Il faut
afficher uniquement les boutons de lecture […]. Dessous, tout le reste du menu
qui s'ouvre en ouvrant ce menu tiroir. »

Le pied du lecteur (`#reader-footer`) est donc coupé en deux par une **poignée**,
`#reader-tiroir-btn` (un chevron SVG et le mot « Menu »), placée **entre**
`#reader-nav` (les sept commandes de lecture) et `#reader-settings` (tout le
reste) :

| Partie | Contenu | Affichage |
|---|---|---|
| Haut | `#tts-progress-row` + `#reader-nav` | toujours visible |
| Poignée | `#reader-tiroir-btn` | visible sur téléphone, **masquée au-delà de 641 px** |
| Tiroir | `#reader-settings` : voix multiples, écouter les voix, onglets, lecture rapide, vider le cache, voix du narrateur, vitesse, voyant « Réparer » | **replié sur téléphone**, toujours ouvert sur ordinateur |

*Deux règles, les mêmes que pour le tiroir du casting* : l'état de départ est
`null` (`let _tiroirLecteurOuvert = null;`) — tant que Laurent n'a pas touché la
poignée, le tiroir **suit la taille de l'écran**
(`_tiroirLecteurDoitEtreOuvert`, fonction **pure**, éprouvée par
`test_voix/test_tiroir_lecteur.js`) ; dès qu'il la touche, **son choix l'emporte**
pour toute la session, y compris après une rotation du téléphone.

*L'état est porté par `aria-expanded`, jamais par le dessin* :
`_appliquerTiroirLecteur()` masque ou montre `#reader-settings` (classe
`hidden`), pose `aria-expanded` et le libellé d'accessibilité, et **le CSS ne
fait que dessiner cet état** — le chevron se retourne
(`#reader-tiroir-btn[aria-expanded="true"] svg { transform: rotate(180deg); }`)
et la poignée prend la couleur d'accent. Le tiroir s'ouvre **vers le haut**,
d'où le chevron qui regarde en l'air quand il est fermé. Ce qu'annonce un lecteur
d'écran ne peut donc pas contredire ce qu'on voit.

Elle est appliquée à l'**entrée dans le lecteur** (`showView('reader')`) et au
**redimensionnement** — ce dernier seulement tant que Laurent n'a pas donné son
avis.

*Mesuré* (`test_voix/test_tiroir_lecteur_rendu.py`, Playwright, le vrai pied du
lecteur sur 360 px de large) : **137 px** de pied replié contre **249 px** ouvert
— **112 px rendus au texte** —, poignée de **332 × 26 px**, les sept boutons sur
**une seule ligne**, aucun débordement ; sur ordinateur (1200 px), la poignée
**n'existe pas** et les réglages restent affichés, comme avant.

#### Préchargement audio (lecture phrase par phrase — session du 08/09/2026)
Lecture **phrase par phrase** : chaque phrase est synthétisée en un fichier
audio séparé (`_buildPlaylist`, app.js). Plus aucune fusion de phrases en
« groupes » : l'audio démarre exactement quand la voix commence la phrase,
donc la surbrillance (curseur glitch) est posée sur la frontière réelle et
n'a plus besoin d'être estimée pendant la lecture (`timeupdate` supprimé).

Un **prefetcher de fond** (`_runTTS` / `pump()`) précharge la suite du
chapitre en continu, avec un parallélisme borné
(`PREFETCH_CONCURRENCY` = 2) et une fenêtre glissante plafonnée à
`PREFETCH_MAX_AHEAD_CHARS` = 5000 caractères (~5-6 min d'audio, mémoire
maîtrisée : les voix locales Kokoro/Piper renvoient du WAV non compressé).
La fenêtre glisse au fil de la lecture : en conditions normales, la
lecture ne dépend plus du réseau au moment du passage
d'une phrase à la suivante.
**Conséquence à connaître : la voix de chaque phrase est FIGÉE au lancement**
(session du 15/09/2026). `_buildPlaylist()` calcule la voix et la hauteur de
chaque phrase **une fois pour toutes** (`units[i].voice` / `pitch`, d'après
`_voiceForSentence()`), et le prefetcher télécharge les blobs correspondants :
une playlist en cours ne « voit » donc pas un changement de voix. C'est ce qui
faisait qu'après avoir modifié la voix d'un personnage dans la fenêtre du
casting, la suite du chapitre continuait avec l'**ancienne** voix — et qu'il
fallait fermer puis rouvrir l'application sur mobile pour que le changement
prenne (constat de Laurent). D'où la règle désormais appliquée par
`_updateCharacterVoice()` : **si une lecture est en cours** (`playing` ou
`loading`), on arrête et on relance depuis la phrase en cours
(`_stopTTS()` + `_startTTS()`), ce qui reconstruit la playlist et les blobs
avec les bonnes voix ; si la lecture est **en pause**, on ne relance rien (la
pause est respectée, la prochaine lecture reconstruira la playlist).
*Garde-fou* : `test_voix/test_ids_ecran.py` (§ 7). *Piste d'amélioration
notée au BACKLOG* : appliquer le changement aux seules phrases **pas encore
lues**, sans reprendre la phrase en cours.

**La VITESSE de chaque phrase — corrigée le 20/09/2026.** Jusqu'à ce jour,
`_buildPlaylist()` mettait bien la **voix** et la **hauteur** dans chaque unité
de lecture, mais **pas la vitesse** : `_runTTS` lisait celle du menu du haut
(`#speed-select`) **une seule fois**, et l'appliquait à toutes les phrases. Les
curseurs de vitesse de la fenêtre du casting enregistraient donc leur valeur en
base **sans aucun effet audible**. Mesure faite dans la base ce jour-là :
**131 fiches sur 1 232** portaient une vitesse réglée (de −25 % à +20 %) que
personne n'avait jamais entendue ; les 594 hauteurs, elles, fonctionnaient (le
`pitch` était déjà transmis).
*Règle appliquée (clarifiée par Laurent le 20/09/2026, le soir — la première
version, livrée le matin, faisait suivre le menu aux personnages non réglés)* :
`_voiceForSentence()` renvoie aussi `rate`, par la fonction **pure**
`_vitesseDeFiche()` ; l'unité porte `rate`, et `launchFetch()` appelle
`_fetchAudio(…, u.rate || rate, …)`. Trois cas :
1. **fiche avec un vrai réglage** → la vitesse de la fiche ;
2. **fiche sans réglage** (personnage avec voix dédiée, curseur jamais touché) →
   la constante de la page `PERSONNAGE_RATE_DEFAUT = '+0%'` (le réglage nommé
   **« Normale »** dans le menu) : le menu du bas **n'est pas un réglage
   général, c'est celui du NARRATEUR**, il ne touche donc plus aux dialogues ;
3. **récit et petits rôles** (lus par le narrateur) → `rate` **nul**, donc la
   **vitesse du menu** : c'est le tempo du narrateur.
*Le neutre ne compte pas* comme un réglage : une fiche à `+0%` — le cas de
**1 101** personnages — rend `null` de `_vitesseDeFiche()`, et c'est la
constante `PERSONNAGE_RATE_DEFAUT` qui décide ensuite (« Normale »).
*Piste écartée le même jour* : une colonne `books.narrator_rate` (vitesse du
narrateur **par livre**, sur le modèle de `narrator_voice`) a été proposée puis
**abandonnée** par Laurent — le menu du bas reste un réglage **global**, donc
**aucune écriture en base ni colonne ajoutée**.
*Garde-fou* : `test_voix/test_vitesse_personnage.js` (**27 contrôles**, dont
« menu sur Lente : le personnage sans réglage reste à Normale » et le
**câblage** de l'appel dans `app.js`, puisque `_runTTS` n'est pas exécutable
sans navigateur).
*Validé à l'oreille par Laurent le **20/09/2026*** (« testé et validé ») : les
personnages réglés s'entendent enfin, et le menu du bas ne change plus que le
narrateur.
*Reste ouvert* (BACKLOG) : un changement du **menu du bas** — donc de la vitesse
du narrateur — pendant une lecture ne s'entend qu'à la reprise : le gestionnaire
de `#speed-select` ne relance rien, et la fenêtre de préchargement (jusqu'à
~5-6 min d'audio) garde l'ancienne vitesse.



Chaque requête TTS a un timeout (`FETCH_TIMEOUT_MS` = 20 s) : quand
Android suspend le réseau de la page (écran verrouillé) sans lever
d'erreur, la requête zombie est abandonnée puis relancée au lieu de rester
bloquée pour toujours. La lecture **attend patiemment le réseau**
(`waitUnitNetworkRetry`) et **repart seule** dès qu'il revient.

**Le lecteur parle pendant une coupure réseau** (session du 15/09/2026) : au
lieu de faire patienter en silence (spinner), il annonce à voix haute
« Pas de réseau, veuillez patienter… ». Le message est **préparé une fois au
lancement de la lecture** — donc pendant que le réseau fonctionne encore — avec
**la voix du narrateur**, puis conservé en mémoire sous forme de blob : il peut
être joué **réseau coupé**, ce qu'aucun appel au serveur ne permettrait à ce
moment-là. Rythme : première annonce après **~8 s** d'attente
(`MESSAGE_ATTENTES_AVANT` = 2 attentes de 4 s), puis **au plus une toutes les
45 s** (`MESSAGE_RAPPEL_MS`) ; le message est coupé à la mise en pause ou à
l'arrêt. Le texte est une constante en haut de `app.js` (`MESSAGE_HORS_LIGNE`),
faite pour être changée à volonté. Si le message n'a pas pu être préparé, la
lecture s'en passe simplement (aucune erreur) — vérifié par
`test_voix/test_message_reseau.js`.


Pour les voix **Kyutai**, ce délai est porté à `KYUTAI_TIMEOUT_MS` (90 s) :
le moteur calcule une phrase en gros en deux fois sa durée de lecture, un
délai de 20 s abandonnerait une longue phrase en plein calcul. Et quand le
serveur répond **503** (moteur Kyutai éteint — erreur définitive, pas une
coupure réseau), la lecture s'arrête en affichant le message du serveur
(`_ttsFatalError`) au lieu d'attendre indéfiniment.

#### États TTS
`idle` → `loading` → `playing` ⇄ `paused` → `idle`

Sur pause : le curseur reste sur la phrase en cours.
Sur stop : le curseur reste en place (ne revient pas au début).

#### Persistance du curseur
`cursor_idx` est sauvegardé 3 secondes après chaque mouvement du curseur
(via `_setCursor`), en plus des événements scroll et changement de chapitre.
À l'ouverture d'un livre, le curseur glitch est restauré exactement
sur la dernière phrase lue.

#### Découpage audio — phrases et sous-segments (session du 08/09/2026)
`_buildPlaylist(startIdx, endIdx)` remplace l'ancien `_buildAudioGroups`
(fusion en groupes de ~1500 caractères, abandonnée). Une **unité de
lecture = une phrase**, jamais un paquet de phrases : le rythme est
régulier (fini les blocs « quelques mots » à côté de blocs d'un paragraphe
presque entier) et la surbrillance peut coller à la voix.

- Une phrase de plus de 500 caractères (`SPLIT_SENTENCE_CHARS`) reste
  découpée en sous-segments de synthèse aux virgules/points-virgules
  (max 450 car., `SPLIT_SEGMENT_CHARS`) : les phrases-fleuves des vieux
  romans ne produisent ni coupure en plein milieu du texte ni un seul
  bloc géant. Tous les sous-segments gardent le même index de phrase :
  le curseur reste posé sur la phrase pendant toute sa durée.
- `endIdx` optionnel : une **plage délimitée** (issue d'une sélection de
  texte) ne déclenche pas le passage automatique au chapitre suivant.
- Les phrases de voix/pitch différents (voix multiples) s'enchaînent
  naturellement, chacune avec sa voix — plus de notion de « groupe de
  même voix » à reconstruire.

Le curseur glitch est posé **au moment où l'audio de la phrase démarre**
et ne bouge plus jusqu'à la fin de la phrase (suppression du suivi estimé
`timeupdate` de l'ancien `_playBlob`) : la surbrillance reste au plus près
de la voix lue, au maximum une phrase à la fois.

#### Pause entre paragraphes
Dans la boucle de lecture `_runTTS`, avant de jouer une nouvelle unité
audio (phrase ou sous-segment), on compare le `paraIdx` de la phrase
précédente et de la phrase courante (`_sentences[...].paraIdx`). Si le
paragraphe change (ex : un titre de chapitre suivi du premier paragraphe
de texte), une pause silencieuse de `PARAGRAPH_PAUSE_MS` est insérée via
`_pause()` avant de poursuivre. La pause est interrompable immédiatement si le
TTS est stoppé pendant son écoulement (respect du signal d'abort).

**Mise à jour du 15/09/2026 — la pause passe à 0 (idée de Laurent, à
l'écoute d'une heure du Comte de Monte-Cristo).** La valeur avait déjà été
réduite de 500 ms à 300 ms le 23/08/2026 ; à l'usage, Laurent a constaté que
les **successions de petites répliques entre deux interlocuteurs** restaient
« hachées ». Or dans un dialogue, **chaque réplique est un paragraphe** :
la pause de 300 ms s'ajoutait donc à chaque échange, **par-dessus** le
silence de fin de phrase du moteur. La mesure faite le même jour a montré que
ce silence de queue était le vrai coupable (XTTS : 0,54 à 0,91 s, variable
d'une phrase à l'autre ; Edge : déjà ramené à 0,25 s depuis le 08/09/2026).
Une fois le silence de queue XTTS ramené lui aussi à 0,25 s (voir plus bas),
la pause ajoutée par le lecteur devenait inutile : `PARAGRAPH_PAUSE_MS` est
donc passé à **0** (mettre 300 rétablit l'ancien comportement).

Sans cette pause, deux phrases de paragraphes différents s'enchaînaient
sans aucun silence — un titre de chapitre type "La tempête" (souvent
placé dans un `<h1>` séparé dans le HTML source de l'EPUB, donc déjà bien
isolé côté texte) se faisait lire en une seule traite avec le paragraphe
suivant, sans rupture audible.

---

### Recherche dans le livre — main.py + app.js

#### Rôle
Recherche un mot exact dans l'ensemble des chapitres d'un livre (pas
seulement le chapitre en cours), insensible aux accents et à la casse.

#### Backend — `/api/books/{id}/search?q=...`
- Appelle `get_chapters()` pour récupérer tout le texte du livre
- Normalise le texte et la requête (`_normalize_for_search` : minuscules +
  suppression des accents via `unicodedata`)
- Découpe chaque chapitre en paragraphes (`\n\n+`) puis en phrases
  (`_split_sentences`, même logique que côté client)
- Recherche le mot avec bordures de mot (`\b...\b`) → mot exact uniquement,
  pas de correspondance partielle ("chat" ne trouve pas "chaton")
- Retourne pour chaque occurrence : `chapter_index`, `chapter_title`,
  `paragraph_index`, `sentence_text`

#### Frontend — panneau chapitres
- Champ `#search-input` + bouton loupe, intégré en haut du panneau chapitres
  existant (`#chapters-panel`)
- Recherche déclenchée sur validation (Entrée ou clic), pas de live-search
- Bascule entre `#chapters-list` (liste normale) et `#search-results-list`
  (résultats) selon le contexte
- Chaque résultat affiche : titre du chapitre + extrait avec le mot
  surligné (`<mark>`)
- Clic sur un résultat → `_goToSearchResult()` charge le chapitre concerné,
  puis recherche la phrase correspondante dans `_sentences[]` (matching par
  texte exact, pas par index) pour positionner le curseur glitch dessus

---

### Effet glitch — styles.css

Animation CSS `@keyframes glitch` sur la classe `.glitch-active` :
- 3 éclairs rapides (~40ms chacun) en début de cycle
- Pause ~500ms
- Cycle total : 0.8s
- Effet : décalage RGB rouge/cyan + flou + déplacement

---

### Mode RSVP (lecture mot-à-mot) — app.js + styles.css

#### Contexte
Conçu à l'origine pour aider Maya (difficultés de lecture à voix haute :
anticipation/déformation de mots comme "étant" → "était"). Le mode isole
un mot à la fois pour empêcher le cerveau de deviner la suite à partir du
contexte — elle doit décoder ce qui est réellement écrit.

#### Principe — point fixe + lettre pivot
Le repère rouge ne se déplace JAMAIS à l'écran. C'est le mot entier qui se
décale horizontalement (`marginLeft` calculé dynamiquement) pour que sa
lettre pivot tombe exactement sur ce point fixe.

Le marqueur fixe (`#rsvp-fixed-marker`) et le mot (`#rsvp-word`) sont
positionnés à `left: 15%` (au lieu de 50% à l'origine) — décalé vers la
gauche de l'écran pour laisser assez de marge à droite et permettre aux
mots longs ("traitements", "appréhendé"...) de s'afficher en entier sans
déborder du cadre visible.

- **Lettre pivot** : toujours la 2ème lettre du mot (1ère lettre si le mot
  ne fait qu'1 caractère) — règle simple, pas l'algorithme ORP complet
- **Découpage** : uniquement sur les espaces (les apostrophes restent à
  l'intérieur du mot, ex. "l'éléphant" reste un seul bloc)
- `_rsvpPivotIndex(word)` calcule l'index, `_rsvpRenderWord(word)` affiche
  le mot puis ajuste `marginLeft` via `getBoundingClientRect()` une fois
  rendu

#### Contrôle — tap pour démarrer / tap pour arrêter
~~Ancienne version : maintien du bouton (`pointerdown`/`pointerup`/
`pointerleave`/`pointercancel`).~~ Abandonné — cassait totalement sur
mobile (Android déclenchait son menu contextuel natif au "long press",
avec vibration haptique, et n'envoyait jamais l'événement au JS).

Comportement actuel : un seul `click` sur `#rsvp-push-btn` bascule entre
démarrage et arrêt (`_rsvpToggle()` → `_rsvpStart()` / `_rsvpStop()`).
Identique sur PC et mobile, plus de logique différenciée par appareil.

- 1er tap → `_rsvpStart()` : défilement automatique des mots à la
  vitesse réglée, texte du bouton → "Arrêter"
- 2ème tap → `_rsvpStop()` : arrêt immédiat sur le mot affiché, texte du
  bouton → "Lancer la lecture", affichage du fondu de contexte (inchangé)
- `-webkit-touch-callout: none` ajouté sur `#rsvp-push-btn` en sécurité
  supplémentaire contre le menu contextuel natif

- Vitesse réglable de 100 à 250 mots/minute (`#rsvp-speed-slider`)
- Pauses supplémentaires sur ponctuation (ajoutées au délai normal entre
  deux mots) :
  - Virgule `,` → +200ms
  - Point fort `. ! ? … : ; » "` → +300ms

#### Mode "secours" au relâchement — fondu de contexte
Quand le bouton est relâché, la phrase en cours apparaît en fondu
progressif (opacity 0 → 1 sur 2.5s, `#rsvp-fade-text`) :
- Affiche uniquement la phrase courante (`sentIdx` du mot en cours),
  en texte continu qui wrap normalement comme un paragraphe classique
  (`display: block`, `text-align: left`) — l'ancienne version (phrase
  précédente + phrase courante en blocs `<span>` séparés) créait des
  colonnes de texte qui se chevauchaient visuellement, jugée confuse
- Le mot en cours est affiché avec sa lettre pivot en rouge
  (`.rsvp-fade-pivot`), même logique que le mot RSVP lui-même
  (`_rsvpPivotIndex`), plutôt qu'un simple `<mark>` sur tout le mot
- Reconstruit à partir de `_rsvpWords` filtré par `sentIdx`
- Reste affiché jusqu'au prochain appui (pas de disparition automatique)
- Positionné en haut de l'écran (`#rsvp-fade-text`, `height: 38%`,
  `align-items: flex-end`) pour ne jamais chevaucher le mot RSVP affiché
  plus bas dans `#rsvp-word-zone`

#### Synchronisation avec le reste de l'appli
- `_rsvpBuildWords()` reconstruit `_rsvpWords[]` à partir de `_sentences[]`
  à chaque ouverture (chaque mot garde son `sentIdx` d'origine)
- `_rsvpFindStartWordIdx()` démarre au mot correspondant à `_cursorIdx`
- Pendant le défilement, `_setCursor(w.sentIdx)` est appelé à chaque mot →
  le curseur glitch (et donc la sauvegarde de progression) reste synchro
- Mutuellement exclusif avec le TTS : `openRSVP()` appelle `_stopTTS()`

#### Vue dédiée — `showView()`
`#view-rsvp` est une 3ème vue au même titre que bibliothèque/lecteur.
**Point d'attention** : `showView(name)` doit explicitement gérer les
3 vues (`lib`, `reader`, `rsvp`) — toute nouvelle vue ajoutée à l'avenir
doit être ajoutée dans cette fonction, sinon elle garde sa classe `hidden`
d'origine et s'affiche avec une taille de 0×0 (bug rencontré et corrigé
lors de l'implémentation du RSVP).

---

### Cache busting (mises à jour mobile/PWA)

#### Problème
Le navigateur (et plus encore une PWA installée) garde `app.js` et
`styles.css` en cache de façon agressive sur mobile. Sans mécanisme de
contournement, une modification de code peut ne jamais apparaître sur le
téléphone même après plusieurs rechargements classiques.

#### Solution — paramètre de version dans index.html
`frontend/index.html` référence les fichiers avec un suffixe `?v=...` :

```html
<link rel="stylesheet" href="/static/styles.css?v=20260630-1" />
<script src="/static/app.js?v=20260630-1"></script>
```

Le navigateur considère une URL différente (`?v=` différent) comme une
ressource différente à retélécharger, ignorant le cache de l'ancienne
version.

#### Convention de version
Format `YYYYMMDD`, avec suffixe `-1`, `-2`, etc. si plusieurs sessions de
modification ont lieu le même jour (ex: `20260630`, puis `20260630-1`
pour une deuxième session le même jour).

#### Règle de session
**En fin de session, dès que `app.js` ou `styles.css` ont été modifiés**,
monter le numéro de version dans les 2 lignes correspondantes
d'`index.html` avant de commit/push. Réflexe à appliquer systématiquement,
au même titre que la mise à jour de ce fichier `ARCHITECTURE.md`.

---

### START.bat — Lancement

Lance uvicorn sur le port 8081.
Compatible avec NIMM qui tourne simultanément sur 8080.

**Depuis le 12/09/2026, `START.bat` allume aussi un moteur de voix lourd** :
un seul lancement (double-clic, ou clic dans l'application du téléphone)
ouvre les **deux fenêtres** — le lecteur et le moteur. Trois protections :

**Quel moteur allumer ? — le DERNIER utilisé (14/09/2026).** Depuis l'arrivée
d'XTTS v2, deux moteurs lourds cohabitent sans jamais tourner ensemble. Le
choix se fait par un petit fichier de réglage, **`data\moteur_voix.txt`** :

| Valeur | Effet au démarrage |
|---|---|
| `xtts` | allume **XTTS v2** (port 8083) — **défaut** si le fichier n'existe pas |
| `kyutai` | allume **Kyutai** (port 8082) |
| `aucun` | ne lance **aucun** moteur (lecture Edge, Kokoro et Piper seulement) |

Ce fichier est **écrit automatiquement** par le lanceur du moteur :
`DEMARRER_XTTS.bat` y met `xtts`, `DEMARRER_KYUTAI.bat` y met `kyutai`. On
n'a donc rien à faire pour que le moteur qu'on utilise reste celui des
prochains démarrages ; pour en changer, il suffit d'éditer ce fichier (ou
d'allumer l'autre moteur à la main une fois). Les espaces ajoutés à la main
sont ignorés, et un nom inconnu n'allume rien (avec un message clair).
*Vérification sans rien lancer : `test_voix/test_start_moteur.py`* (16
contrôles : ce que les lanceurs écrivent, les 7 cas du fichier de réglage,
les garde-fous, et un piège `cmd` documenté plus bas).

1. **Pas de second moteur** : `START.bat` teste le port du moteur choisi
   (`curl` sur `/sante`) et saute le démarrage s'il répond déjà ;
2. **Environnement absent** : si le `.venv` du moteur n'existe pas, le
   lecteur démarre quand même (message + rappel de l'installateur) ;
3. **Garde-fou côté moteur** : `servir_kyutai.py` refuse de démarrer si un
   moteur répond déjà, **et** interdit le partage du port
   (`ServiceKyutai.allow_reuse_address = False`). C'est indispensable sous
   Windows : Python autorise par défaut deux serveurs à ouvrir le même port
   (`SO_REUSEADDR`), ce qui avait laissé **deux moteurs charger 2 × 3,8 Go**
   de carte graphique (constaté le 12/09/2026 — 7,7 Go sur 8). Depuis, le
   second démarrage s'arrête proprement.
4. **Fermer la fenêtre éteint le moteur** : `_surveiller_la_console()`
   (`servir_kyutai.py`) surveille l'entrée de la console — tant que la
   fenêtre existe, la lecture du clavier reste en attente (personne ne tape
   dans cette fenêtre) ; dès qu'elle est fermée, la lecture revient **vide**
   (fin de flux) et le moteur s'arrête proprement. Ce gardien était
   nécessaire : sous Windows, un programme qui n'écrit pas dans sa console
   ne remarque pas sa disparition — constaté le 12/09/2026, le moteur
   continuait de tourner (port occupé, 3,8 Go de carte graphique) alors que
   la fenêtre avait disparu. Il ne s'active que dans une **vraie console**
   (`sys.stdin.isatty()`), ou si `NIMM_KYUTAI_SURVEILLER_CONSOLE=1` —
   test : `test_voix/test_gardien_console.py` (fermeture de l'entrée →
   arrêt automatique, vérifié).

**Piège `cmd` à ne pas rouvrir (constaté au test le 14/09/2026)** — dans un
fichier `.bat`, à l'intérieur d'un bloc `if ... ( ... )`, une **parenthèse
présente dans un texte** ferme le bloc : `echo Moteur : AUCUN (choix
enregistre).` provoque `. était inattendu.` et **arrête tout le script**.
Les messages destinés à l'intérieur d'un bloc doivent donc s'écrire **sans
parenthèses** (`AUCUN - choix enregistre`). Deuxième leçon du même test : un
bloc `if exist ( for ... )` réparti sur plusieurs lignes déraille aussi —
la lecture du fichier de réglage utilise désormais `set /p` sur **une seule
ligne**. Les deux pièges sont surveillés par
`test_voix/test_start_moteur.py`.

Le port du moteur est **ouvert avant le chargement du modèle** (≈ 15 s) :
la détection est donc fiable dès la première seconde, et une demande de
phrase pendant le chargement reçoit un message clair (« moteur en cours de
chargement ») plutôt qu'une erreur de connexion.

**Lancement depuis le téléphone** : il passe par un petit programme séparé,
`<dossier du lanceur>\launcher.py` (lancé au démarrage de Windows par
`START_LAUNCHER.bat`, page web sur le port 8765). C'est lui qui appelle
`<dossier du projet>\START.bat` — donc rien à modifier de son côté : l'allumage du
moteur de voix en profite automatiquement, quel que soit celui choisi dans
`data\moteur_voix.txt`.

---

### Temps de lecture restant

Affiché dans deux endroits :
- **Barre TTS** : `~Xh Xmin` à droite de la barre de progression — temps
  restant depuis le curseur jusqu'à la fin du livre
- **Menu chapitres** : durée estimée de chaque chapitre

Calcul : `word_count` de chaque chapitre est inclus dans la réponse
`/api/books/{id}` (calculé à la volée depuis le texte EPUB).
Vitesse de base : 150 mots/minute, ajustée selon le sélecteur de vitesse
(`_getWPM()`). Se recalcule à chaque mouvement du curseur et changement
de vitesse.

---

### 🧹 Cache HTTP (no-store) — bibliothèque + API — session du 20/08/2026
**Problème rencontré en cascade ce soir-là :** plusieurs symptômes
différents (page non mise à jour malgré le cache-busting `?v=` sur
`app.js`/`styles.css`, couvertures de livres qui ne s'affichaient plus,
titres de livres absents) se sont révélés être la même cause générale —
le navigateur (Firefox mobile en particulier, plus agressif que Chrome/
Brave sur ce point) mettait en cache des réponses qui ne devaient
jamais l'être : la page `index.html` elle-même, les images de
couverture, et plus généralement toutes les données de l'API.

**Solution en 2 couches :**
1. `Cache-Control: no-store` explicite sur la route `/` (sert
   `index.html`) et sur `/api/books/{id}/cover`.
2. **Middleware global** (`main.py`, `no_cache_api`) : ajoute
   automatiquement `Cache-Control: no-store` sur **toute** route
   commençant par `/api/`, sans exception et sans avoir à y penser
   route par route à l'avenir — règle générale plutôt que correctifs
   au cas par cas.

**Effet secondaire découvert en cours de route (Firefox mobile
spécifiquement) :** le "DNS sécurisé" (DNS over HTTPS) de Firefox
peut résoudre les noms de domaine via son propre serveur DNS
(Cloudflare/NextDNS) plutôt que via le réseau Tailscale, empêchant la
résolution du nom `*.ts.net` même avec le VPN Tailscale actif sur le
téléphone — symptôme : message "Aucun document ne correspond aux termes
de recherche spécifiés" (Firefox interprète l'adresse comme une
recherche faute de résolution). Corrigé en désactivant le DNS sécurisé
dans Firefox (Paramètres → Vie privée et sécurité → DNS sécurisé →
Désactivé). À garder en tête si le problème resurgit sur un autre
appareil Firefox de la famille.

### 🔌 Serveurs fantômes sur le port 8081 — le piège, et son garde-fou (18/09/2026)

**Le piège, vécu le 18/09/2026 au soir** : fermer la fenêtre de commande ne tue
pas toujours le processus Python. Le port 8081 reste alors **pris par l'ancien
serveur** ; le nouveau ne peut pas démarrer (erreur affichée une seconde, puis la
fenêtre se ferme) et c'est l'**ancien** serveur qui répond — avec l'**ancien code
en mémoire**. Ce soir-là, Laurent a donc relancé plusieurs fois en croyant tester
les correctifs : rien n'était chargé (le banc d'écoute, la règle des incises, la
ponctuation des interjections). Le doute venait aussi d'un **second** serveur
oublié sur le port 8080, démarré le matin.

**Comment le diagnostiquer** : comparer l'heure de démarrage du processus qui
écoute (`Get-NetTCPConnection` → PID → `Get-CimInstance Win32_Process`) avec la
date de modification des fichiers de `modules/`. Et
`test_voix/_tester_tts_serveur.py` dit, lui, ce que le serveur renvoie vraiment.

**Garde-fou livré** : `START.bat` teste désormais le port 8081 avant de démarrer
et **arrête tout ancien serveur du lecteur**. C'est la seconde partie de l'idée
notée ci-dessous, réalisée le même soir.

⚠️ **Leçon du même soir, apprise à mes dépens** : la **première** version du
garde-fou filtrait les processus par **nom de script** (`main.py`,
`uvicorn main:app`). Or **NIMM, le chatbot de Laurent** (dossier `G:\NIMM`,
interface PC sur `localhost:8080`) utilise lui aussi un `main.py` — le garde-fou
l'a donc **arrêté par erreur**. La version corrigée cible le **PORT 8081** (la
seule signature fiable du lecteur) **et** exige un processus **Python** (pour ne
jamais toucher le relais `tailscaled`, qui écoute aussi sur 8081 mais sur
l'adresse Tailscale). Règle générale à retenir : **ne jamais identifier un
processus par le nom de son script** quand deux applications de la maison
peuvent porter le même nom.
*Essai sans risque du garde-fou* : `test_voix/_essai_garde_fou_start.py` (dit qui
serait arrêté, sans rien arrêter).

**Reste à faire (idée d'origine)** : un bouton « Arrêter » dans le launcher
(signal d'arrêt ou route `/shutdown`).


### 📝 Deux idées RSVP à l'étude — déménagées

Elles vivent dans `BACKLOG.md` depuis le **22/09/2026** (l'état actuel n'a rien à
y faire) : la **taille de police** des mots longs en RSVP (« traitements »,
« appréhendé »…) et la **clarté du fondu de contexte** à l'arrêt
(`#rsvp-fade-text`).

---

## 🔤 Le texte lu : extraction, nettoyage, découpage

### core/epub_parser.py — Parseur EPUB

#### Rôle
Ouvre un fichier EPUB (zip), en extrait les chapitres dans l'ordre,
les métadonnées (titre, auteur), et la couverture si disponible.

#### Fonctions principales
- `get_metadata(epub_path)` — titre, auteur, couverture (bytes)
- `get_chapters(epub_path)` — liste ordonnée {index, titre, texte_brut}
- `get_chapter(epub_path, n)` — texte brut du chapitre N

#### Bibliothèque utilisée
`ebooklib` + `BeautifulSoup4` pour le parsing HTML interne des EPUB.

**Résidus de balises dans le texte — nettoyés le 20/09/2026.** Constat de
Laurent, au chapitre 98 du Comte de Monte-Cristo (Tome 5) : le texte lu et
affiché contenait « **M `class="textsuperscript">`lle Danglars** ». Cause, vue
dans le fichier EPUB lui-même : une balise **cassée** par une conversion
automatique, avec le « **>** » **échappé** — donc prise pour du **texte** :

```html
M<supu0003c span=""> class="textsuperscript"&gt;<span class="ecrm">lle</span> Danglars
```

Le parseur n'était donc **pas** en faute : il recopiait fidèlement le fichier ✗.
`_html_to_text` retire maintenant ces morceaux (`re.sub(r'\s+[a-zA-Z-]+="[^"]*">')`),
juste **avant** le nettoyage des espaces : un vrai texte de roman ne contient
jamais la forme `nom="valeur">`. Effet immédiat sur **tous les livres**, puisque le
texte est extrait **à la lecture** (aucune table de chapitres en base, donc rien à
réimporter) — *mais il faut **redémarrer le lecteur** : le correctif est côté
serveur.* *Vérifications* : `test_voix/test_residus_html.py` (le cas réel nettoyé,
le texte normal intact) et l'outil `test_voix/_chercher_residus_html.py`, qui a
balayé la bibliothèque : **379 documents, 13 livres, zéro résidu** après
correction.

---

### modules/tts.py — Synthèse vocale

#### Rôle
Un seul module pour les **quatre moteurs de voix**, aiguillés par le préfixe
du nom de voix (branches dans `/api/tts`, `main.py`) :

| Préfixe | Moteur | Où tourne-t-il | Sortie |
|---|---|---|---|
| `kokoro:` | Kokoro (84 voix, dont 30 « NIMM Voix ») | local, ONNX, CPU | WAV |
| `piper:` | Piper (3 modèles, 4 voix) | local, ONNX, CPU | WAV |
| `kyutai:` | Kyutai TTS 1.6B (35 voix françaises libres) | **service séparé**, GPU | WAV |
| `xtts:` | XTTS v2 (**60 voix clonées** : 35 extraits de Kyutai + 25 versés le 14/09/2026) | **service séparé**, GPU | WAV |
| *(aucun)* | Edge TTS (12 voix) | en ligne (Microsoft) | MP3 |

Edge TTS renvoie un flux MP3 lisible directement par le navigateur ;
Kokoro, Piper, Kyutai et XTTS v2 renvoient un WAV (mise en cache identique).

**Kyutai à part, pourquoi.** Le moteur Kyutai exige PyTorch et un
environnement Python 3.12, alors que le lecteur tourne sur Python 3.14 :
les deux ne peuvent pas cohabiter (les outils du moteur n'existent pas pour
Python 3.14). Le moteur vit donc dans son propre dossier
`kyutai_service/`, lancé par `DEMARRER_KYUTAI.bat`, et le lecteur l'appelle
en HTTP local (`NIMM_KYUTAI_URL`, défaut `http://127.0.0.1:8082`) avec
`httpx`. Conséquences : le lecteur reste léger (aucune dépendance PyTorch),
le moteur n'est chargé qu'une fois (≈ 4 s, 3,8 Go de mémoire vidéo) et
**une seule phrase est générée à la fois** (le moteur n'est pas
« thread-safe » : le service sérialise les demandes). Si le moteur n'est pas
allumé, `/api/tts` répond **503** avec un message clair que le client
affiche (il arrête la lecture au lieu de réessayer sans fin).

#### Paramètres supportés
- `voice` — identifiant de la voix (ex: fr-CH-ArianeNeural)
- `rate` — vitesse de lecture (ex: +0%, +25%)
- `pitch` — hauteur de la voix (ex: +0Hz, -10Hz, +5Hz) — exposé au frontend
  depuis l'intégration voix multiples (chaque phrase peut avoir son propre
  pitch selon le personnage qui parle)

#### Voix françaises disponibles

| Identifiant | Prénom | Région | Qualité |
|---|---|---|---|
| fr-FR-VivienneMultilingualNeural | Vivienne | France | ⭐⭐⭐ Meilleure |
| fr-FR-DeniseNeural | Denise | France | ⭐⭐⭐ |
| fr-FR-EloiseNeural | Eloïse | France | ⭐⭐ |
| fr-FR-HenriNeural | Henri | France | ⭐⭐⭐ |
| fr-FR-RemyMultilingualNeural | Rémy | France | ⭐⭐⭐ |
| fr-BE-CharlineNeural | Charline | Belgique | ⭐⭐ |
| fr-BE-GerardNeural | Gérard | Belgique | ⭐⭐ |
| fr-CA-SylvieNeural | Sylvie | Canada | ⭐⭐ |
| fr-CA-AntoineNeural | Antoine | Canada | ⭐⭐ |
| fr-CA-JeanNeural | Jean | Canada | ⭐⭐ |
| fr-CH-ArianeNeural | Ariane | Suisse | ⭐⭐ |
| fr-CH-FabriceNeural | Fabrice | Suisse | ⭐⭐ |

Voix par défaut (narrateur) : `fr-CH-ArianeNeural`. Changée depuis
Vivienne (session du 20/08/2026) — Vivienne, en tant que voix
"Multilingual", dérapait de façon aléatoire vers l'espagnol ou l'anglais
sur certaines phrases, y compris en dehors du chantier voix multiples.
Ariane n'a pas ce défaut. Par cohérence, Ariane est explicitement exclue
du pool de voix dédiées aux personnages dans `voice_casting.py`
(`DEDICATED_VOICES_F`) pour ne jamais se confondre avec le narrateur.

##### Voix Kyutai (35, libres — 12/09/2026)

`KYUTAI_VOICES` expose les **35 voix françaises libres** du moteur Kyutai
TTS 1.6B (banque `kyutai/tts-voices`, dossier `cml-tts/fr`, **CC BY 4.0**).
Elles apparaissent dans les menus **comme les voix Edge, Kokoro et Piper** :
un **prénom** relevant du genre de la voix (Adèle, Blanche… Léon, Marcel…),
le **drapeau** `🇫🇷 France (Kyutai)` et le **genre** — aucun prénom n'est
en double avec les autres familles (91 noms déjà pris au 12/09/2026) ; c'est
vérifié automatiquement par `test_voix/test_pool_casting.py`. Licences :
`kyutai_service/ATTRIBUTION.md`.

Correspondance avec la fiche d'écoute : le numéro d'origine (« Kyutai 01 » …
« Kyutai 35 ») est conservé **en commentaire** à côté de chaque entrée, et
l'identifiant stocké en base reste `kyutai:<identifiant du fichier>` — il ne
change donc jamais, même si un prénom évolue un jour.

Deux éléments étaient **à renseigner à l'écoute** : le **genre** et les
**étoiles**. C'est fait le 12/09/2026, à l'écoute de Laurent (lot d'écoute
produit par `kyutai_service/tester_toutes_voix.py`) : **17 voix féminines**,
**18 masculines**, notées de 1 à 3 étoiles ; la voix n° 33 a été **écartée**
→ `stars: 0` (elle reste choisissable à la main mais n'entre pas dans le pool
automatique, comme les voix Piper écartées).
Enseignement : la mesure automatique de hauteur (sur les enregistrements de
référence CML-TTS) avait proposé un autre genre pour **19** de ces voix —
des voix féminines au timbre grave notamment : **c'est l'écoute qui fait
foi**, la mesure ne servait qu'à proposer.

Ces voix participent au pool automatique **en priorité** depuis le
12/09/2026 (voir « Ordre du pool automatique » plus bas).

##### La banque de voix Kyutai, en entier (relevé du 12/09/2026)

`kyutai_service/_lister_banque.py` (lecture seule) donne l'inventaire :
**522 voix en 4 familles** — `cml-tts/fr` (35, françaises, CC BY 4.0, **les
seules voix françaises déclarées**), `vctk` (106, anglais, CC BY 4.0),
`ears` (153, anglais expressif, CC BY-NC 4.0 : usage privé), et
`voice-donations` (228, **CC0**, langue non déclarée). Les familles autres
que le français peuvent être essayées **sur du texte français** : c'est le
texte donné qui décide de la langue lue (Kyutai n'a pas de réglage `lang=`
comme Kokoro), la question ouverte étant l'**accent** qui en résulte. Essai
prêt : `_tester_voix_etrangeres.py`, qui range les voix d'essai dans
`kyutai_service/voix_autres/` (hors Git). Le service relit ses dossiers de
voix **sans redémarrer le moteur** (`POST /recharger`).

#### Fonctions
- `synthesize_stream(text, voice, rate, pitch)` → stream MP3 (Edge TTS)
- `synthesize_bytes(text, voice, rate)` → bytes MP3 complets (Edge TTS)
- `synthesize_kokoro(text, voice, rate, pitch)` → WAV (vitesse native, hauteur post-traitée)
- `synthesize_piper(text, voice, rate, pitch)` → WAV (idem, `length_scale`)
- `synthesize_kyutai(text, voice, rate, pitch)` → WAV (service HTTP local ; vitesse par `audio_rate.py`, hauteur par `_apply_pitch_shift`)
- `KyutaiIndisponible` — exception levée quand le service Kyutai ne répond pas ; transformée en **HTTP 503** par `/api/tts`.

Quelle que soit la branche, l'audio final est **mis en cache disque**
(`modules/tts_cache.py`) sous la clé texte + voix + vitesse + hauteur : un
passage déjà lu ne redemande rien au moteur (voir la section « Cache audio »).

#### Nettoyage du texte avant synthèse
Chaque phrase passe par `_clean_text()` avant synthèse, quel que soit le
moteur (Edge TTS, Kokoro, Piper). Depuis le 23/08/2026, ce nettoyage
développe aussi les abréviations françaises courantes pour que la voix lise
le mot complet au lieu d'une lettre suivie d'une pause sur le point :
- `M.` → Monsieur, `MM.` → Messieurs, `Mme` → Madame, `Mlle` → Mademoiselle,
  `Dr` → Docteur, `St` → Saint, `n°` → numéro, etc.
- Le texte affiché dans le lecteur n'est pas modifié : seule la synthèse
  utilise la forme développée (`_expand_abbreviations()` appelé dans
  `_clean_text`).
- Garde-fous : les initiales enchaînées (`R.M.`), les mots commençant par
  St/Pr/Dr (`Stéphane`, `Proust`) et `St-Pétersbourg` (trait d'union) ne
  sont pas touchés.

**Passage anti-pauses (session du 23/08/2026, 2e passe)** — pour éviter
les pauses audibles au milieu ou entre les phrases, `_clean_text()` :
- Normalise les suites de points en une seule suspension (`...`, `. . .`,
  `..` → `…`) : Edge TTS marque une pause sur **chaque** point sinon.
  `…` est reconnu comme fin de phrase (pas de point ajouté après).
- Remplace les retours à la ligne par un simple espace (plus de virgule
  ajoutée, qui créait une pause artificielle au milieu d'un texte déjà
  découpé en phrases).
- Supprime les espaces parasites avant `.`/`,`/`…` mais **conserve** l'espace
  avant `?`/`:` (typographie française, prononcée naturellement) — pour `!`, voir
  la mise à jour du 18/09/2026 plus bas : il est retiré du texte envoyé au
  moteur, espace compris.
- `MAX_CHUNK_CHARS` passe de 2000 à **4000** : un envoi client (une phrase,
  ou un sous-segment de phrase trop longue — max ~450 car.) tient toujours
  en **un seul chunk** = une seule "utterance" Edge, sans couture/pause au
  milieu.
- `_split_into_chunks()` : une phrase seule plus longue que `max_chars`
  est découpée en priorité aux virgules/points-virgules (pauses
  naturelles, `_split_long_sentence()`), jamais en plein milieu d'un mot —
  c'était une source de pause nette au milieu d'un texte.
- En fin de segment, une virgule/point-virgule résiduelle (segment issu
  d'une phrase découpée) devient un vrai point final : la voix lit une
  pause de fin de phrase, pas "virgule puis point".

**Retours d'écoute du 18/09/2026 (deux réglages dans `_clean_text`)** —
après une demi-journée d'écoute, Laurent a demandé de retirer les points
d'exclamation et a signalé un silence après « M. » (lu « monsieur ») :

- **Point d'exclamation retiré** du texte envoyé au moteur : les moteurs
  neuronaux le jouent comme une **montée de hauteur** (« Il partit ! » →
  « Il partiiiiit », « Oh ! » → « OOOOOOoooooh »). Il est remplacé par **deux
  signes selon la longueur de la phrase**, après le banc d'écoute du 18/09/2026
  (lot `test_voix/ecoute_ponctuation_20260918_1937`, 6 phrases réelles du
  tome 5) : **VIRGULE** dans les phrases courtes (interjections — c'est le point
  qui « traînait » encore), **POINT** dans les phrases entières (une vraie fin
  de phrase). Frontière : `SEUIL_INTERJECTION = 25` caractères.
  Le traitement est appliqué **en fin de nettoyage**, après la règle de fin de
  segment, sinon la virgule des interjections redeviendrait un point. L'espace
  typographique qui précède est retiré ; le texte **affiché** garde son « ! » ;
  le `?` reste intact (`Quoi ?!` → `Quoi ?`) ; les suites (`!!`) sont ramenées
  à un seul signe. Les valeurs sont en **une ligne** chacune
  (`PONCTUATION_EXCLAMATION`, `PONCTUATION_EXCLAMATION_COURTE`).
- **Incises de parole retirées du texte parlé** (`modules/incises.py`, décision
  de Laurent du 18/09/2026 : « la voix me paraît plus fluide ») : avec une voix
  par personnage, « , dit-il, » est redondant et coupe la voix en pleine
  réplique. Mesure : **361 phrases retirées** sur le tome 5 (contre 289 à la
  première version) et **19 seulement gardées** (non fermées).
  Les incises sont retirées **en entier, complément compris** : le retrait
  s'étend jusqu'à la virgule fermante, ou jusqu'au point si la suite ressemble à
  un complément (« , dit-il au comte. »). Bornes : une virgule au plus, pas de
  ponctuation forte, ≤ 70 caractères. L'incise qui **ouvre** une phrase est
  reconnue (`MOTIF_DEBUT`) — cas fréquent depuis que le découpage sépare les
  phrases au « ! ».
  **Garde-fou vital** : si le retrait **vide** la phrase (une phrase qui n'est
  que l'incise, « ajouta Valentine en s'adressant à Noirtier. »), on ne retire
  rien — sinon la phrase disparaîtrait et le moteur refuserait un texte vide.
  **Compromis** : le complément part avec l'incise (« en donnant son flacon »),
  il n'est plus **entendu** mais reste **affiché**.
  **Dernier cas — la phrase qui n'est QUE l'incise** : le découpage sépare les
  phrases au « ! » et au « ? », donc « — Ah ! vraiment ? dit Monte-Cristo. »
  donne trois phrases, dont « dit Monte-Cristo. » seule. La vider ferait
  disparaître la phrase (le moteur refuse un texte vide) : la route `/api/tts`
  renvoie alors un **court silence** (`modules/silence.py`,
  `SILENCE_INCISE_MS = 150`, réglable). Mesure : **94 phrases** dans le tome 5.
  Vérification : `test_voix/test_incise_seule.py`.
  **La relative part avec l'incise** (`_etendre_relative`) : « , dit Cavalcanti,
  qui se grisait à ce bruit métallique de paroles dorées. » → « c'est
  magnifique. ». Garde-fous : « que » exclu (conjonction le plus souvent),
  aucune extension si la proposition immédiate est une **question** (`?` ou `!`),
  arrêt sur un **décrochage de sens** (« mais », « or », « puis »… ou le
  **point-virgule**), mais « **et qui** » n'en est pas un (relative coordonnée :
  le retrait va jusqu'au point-virgule), et la **longueur emportée** est bornée
  (200 caractères), pas la phrase entière.
  Le retrait se fait **tout au début du nettoyage**, avant la conversion
  `;` → `,` et `:` → `,` : sinon ces conversions fabriquent de **fausses
  incises** fermées (« il partit ; répondit le comte » → « … , … , … ») et le
  sujet de la phrase pouvait disparaître (défaut attrapé par un test).
  Formes couvertes : pronom (« dit-il », **« ajouta-t-il »** avec le *t*
  euphonique), nom propre (« dit Barrois »), **particule noble**
  (« dit M. de Villefort » — fréquent chez Dumas) et **nom commun avec article**
  (« dit le comte », « reprit la jeune fille »).
  La règle est **prudente** : jamais une incise suivie d'un complément
  (« , dit-il en souriant, » — il resterait « en souriant » seul), jamais une
  incise non fermée. Le texte **affiché** ne change pas.
- **Pas de point final après une abréviation développée** : la page découpe
  les phrases **après le point d'une abréviation**, donc le moteur recevait
  des morceaux finissant par l'abréviation seule (« … le temps de
  complimenter M. »). Le point final ajouté en fin de nettoyage en faisait une
  **vraie fin de phrase**, avec la respiration entendue comme un silence
  parasite (`MOTS_SANS_POINT_FINAL` : Monsieur, Messieurs, Madame, Mesdames,
  Mademoiselle(s), Monseigneur, Docteur, Professeur, Saint(e), numéro).
  Mesure : **207 coupures** de ce type dans le seul tome 5 de Monte-Cristo.
  Le correctif de fond (ne plus couper la phrase après une abréviation)
  demande de **migrer les index de `speaker_attribution`** : voir BACKLOG.

#### Niveau sonore des voix — `modules/audio_gain.py`

Le moteur Kyutai ne règle pas son niveau de sortie : mesure du 18/09/2026 sur
le cache du lecteur, **niveau de la parole** (médiane des fenêtres de 30 ms
qui contiennent vraiment du son) : **Edge 8,4 %** de la pleine échelle contre
**Kyutai 6,2 %**, et jusqu'à **3,4 %** sur certaines phrases (jusqu'à −8 dB).

`normaliser_wav_parole()` mesure ce niveau de parole et applique le gain qui
l'amène à la cible (`CIBLE_POURCENT = 8,5`, le niveau d'Edge). Garde-fous :
gain plafonné (`GAIN_MAX = 4.0`), crête de sortie bornée
(`CRETE_MAX_POURCENT = 98`), aucune atténuation, et tout format inattendu ou
tout échec renvoie l'audio d'origine. Appelé dans `synthesize_kyutai()`
**après** la vitesse et la hauteur, et **avant** la mise en cache : le niveau
définitif est celui qui part au cache. Effet mesuré sur 120 phrases réelles :
niveau de parole médian **5,4 % → 8,2 %** (≈ +3,6 dB), gain médian ×1,45.
Vérification : `test_voix/test_niveau_audio.py`.

**Révision du 21/09/2026 — la correction va maintenant dans les DEUX SENS.**
Retour d'écoute de Laurent : « le volume baisse dans un long paragraphe ».
Mesure du jour (`test_voix/_mesurer_pocket_defauts.py`, dix phrases d'un long
paragraphe de 22/11/63 demandées **une par une**, comme en lecture) : Kyutai
sort de **3,8 à 10,8 %** (médiane 6,6) et Pocket de **7,5 à 12,8 %** (médiane
9,6). L'ancienne règle **remontait** les phrases faibles vers 8,5 % — elle
faisait donc déjà l'essentiel — mais laissait les phrases **fortes** au-dessus :
chez Pocket, une phrase à 12,8 % restait **3,6 dB au-dessus** de ses voisines.

La correction est donc **bornée des deux côtés** : une phrase trop forte est
**ramenée** vers la cible, sans jamais perdre plus de `GAIN_MIN` (**−6 dB**),
pour ne rien écraser. Une *bande de ± 3 dB* a été essayée puis **abandonnée** :
elle laissait 3,7 dB d'écart, c'est-à-dire le défaut lui-même — ces variations
ne sont pas des nuances voulues, c'est l'instabilité des moteurs.

**Deux pièges corrigés le même jour, à connaître** :
1. l'ancien garde-fou « correction inaudible » (`gain <= 1.02`) rejetait
   **toutes** les atténuations, puisque le gain est désormais **inférieur** à 1 :
   il compare maintenant l'**écart** (`abs(gain − 1) < 0.02`) ;
2. l'échelle de mesure : le module mesure la **moyenne** par fenêtre de 30 ms,
   mon premier outil mesurait la **crête** — d'où un diagnostic faux au départ
   (« le module ne fait rien »). Un tableau de mesure ne vaut que par l'unité
   qu'il emploie.

**Résultat mesuré de bout en bout** (les mêmes dix phrases, demandées au
**lecteur**) : écart entre phrases **9,1 dB → 0,7 dB** (niveaux finaux de 7,9 à
8,5 %). `VERSION_CACHE` : **17** — les phrases déjà écoutées sont refaites,
sinon elles garderaient l'ancien niveau (leçon du 17/09/2026).

#### Le découpage en phrases — une seule règle, et sa migration (18/09/2026)

La règle était écrite **quatre fois** (page, casting, re-cast, recherche) et
coupait les phrases après le point d'une abréviation de civilité :
« … le temps de complimenter M. | de Morcerf ; … ». Laurent l'entendait comme un
silence après « monsieur », et le texte perdait son début à l'écran.

Elle vit désormais **une seule fois**, dans `modules/decoupage.py`, appelée par
`frontend/app.js` (`_buildSentences`, qui garde sa copie JS : le navigateur ne
lit pas le Python), `modules/voice_casting.py` (`_split_chapter_sentences`),
`main.py` (`_decouper_phrases_du_chapitre`) et la recherche
(`_split_sentences`). Le test `test_voix/test_decoupage_phrases.py` compare le
motif de coupe **et** la liste des abréviations des deux fichiers, pour qu'ils ne
puissent pas diverger en silence.

`phrases_avec_positions()` donne, pour chaque phrase, sa position dans le
chapitre — c'est ce qui a permis la **migration** des index sans rien deviner.

**La migration** (`test_voix/_migrer_index_phrases.py`) : recoller les phrases
décale tous les index, or `speaker_attribution.sentence_idx` porte « qui parle »
et `progress.cursor_idx` retient où le lecteur s'est arrêté. Chaque nouvelle
phrase étant la **réunion** d'anciennes, la correspondance se retrouve par
comparaison de positions ; quand deux locuteurs se retrouvent réunis, c'est
celui de la phrase la plus longue qui est gardé (les cas sont signalés dans le
rapport).

Bilan du 18/09/2026 : **1 075 fusions** sur 107 101 phrases (296 chapitres,
14 livres), **28 cas** à locuteurs mélangés, **0 attribution sans cible**, et
**0 index hors bornes** après écriture (option `--verifier`). Copie de la base
avant écriture : `data/nimm_epub.db.bak_avant_migration_20260918`.

**Ajout du 21/09/2026 : les civilités en CAPITALES et « Mrs ».** Un texte traduit
de l'anglais écrit `MR. CURRIE` (22/11/63, chapitre 10) — et ces formes-là
n'étaient reconnues **nulle part** : la phrase était **coupée** juste avant le
nom. Le moteur recevait alors un morceau finissant par « MR. », **seul devant
trois lettres**, et **inventait un son** (« [féè] ») ; le nom partait dans un
second morceau de **six caractères**. La liste reçoit donc **`MR`, `MRS`, `MME`,
`MMES`, `MLLE`, `MLLES`, `MGR`, `DR`, `PR`** (découpage serveur **et** page : les
deux copies restent identiques) ainsi que **`Mrs`**, et `ABBREVIATION_RULES`
(`modules/tts.py`) devient **insensible à la casse** pour ces civilités
(`MR.` → « Monsieur »).

**La pause après « Mrs », mesurée le même jour** (moteur Kyutai, la voix du
narrateur de 22/11/63, une phrase réelle lue en quatre variantes) : tel quel
**5,76 s**, **sans le point 5,84 s** (le point n'est donc **pas** coupable),
écrit « Madame » 6,24 s, et **coupé en deux morceaux 6,48 s** — le second morceau
s'ouvrant sur **0,46 s de silence**. C'est donc la **coupure** qui crée la pause
entendue : d'où l'ajout de `Mrs` à la liste.

**La migration de ce même jour** (`test_voix/_migrer_phrases_abreviations.py`,
écrit pour l'occasion : il compare la liste actuelle **privée des nouvelles
formes** à l'état actuel, et non l'ancienne règle du 18/09 — sinon il migrerait
**deux fois**) : **17 chapitres** concernés, **tous dans 22/11/63** — **42
fusions**, 13 023 → **12 981** lignes, **1 cas** à locuteurs mélangés (une
réplique de Marnie Cullum réunie à de la narration : le locuteur de la phrase la
plus longue est gardé), **1 position de lecture** recalée, et vérification
passée (autant de lignes que de phrases, index uniques et dans les bornes).
Copie de la base avant écriture :
`data/nimm_epub.db.bak_avant_migration_abreviations_20260921_1822`.

**Ce qui n'a PAS été touché, et pourquoi** : la **lecture** de « Mrs ». En
français « Mrs » = *Messieurs* ; en anglais « Mrs » = *Misses* (Madame). Le
scanner de ses livres tranche : **42 fois sur 42, c'est l'anglais** (toujours
suivi d'un nom — *Mrs. Symonds*, *Starrett*, *Levesque*, *Bowie*, *Clayton*,
*Knowles*, *Holloway*, *Oswald*, *Hall*…), et le moteur dit « Misses », ce qui
convient à Laurent. Le remède serait **une ligne dans le nettoyage** (aucun effet
sur les index) : il reste disponible, mais un livre qui mêlerait les deux usages
ne peut pas être tranché automatiquement — donc on laisse tel quel, et c'est
écrit ici.

---

## 🎭 Le casting : qui parle, avec quelle voix

### 🎭 Distribution de voix par personnage (IA)
**Idée :** Une IA scanne le livre, identifie les personnages et leurs
dialogues, et assigne une voix Edge TTS + un pitch à chacun. Le narrateur
garde toujours la voix par défaut. Les dialogues changent de voix à la
volée pendant la lecture TTS.

**Statut : intégration complète et multi-moteur (session du 21/08/2026).**
Prototype initial testé hors application (`test_voix/`) sur 2 extraits
réels du Comte de Monte-Cristo choisis pour leurs pièges : une scène à
5+ personnages avec dialogues sans tags explicites et une phrase
fusionnée sans séparateur (le suicide de Morrel père), et une scène
avec un personnage muet ne devant jamais recevoir de réplique (Ali) et
une identité volontairement non révélée par le texte à ce stade du
roman (Simbad le marin / Dantès).

**Système multi-moteur (Gemini / Mistral / DeepSeek), choix manuel à
chaque analyse — DeepSeek par défaut.** Suite à l'épuisement du crédit
Gemini (déclenché par un essai malheureux sur *Les Misérables*, un
pavé de 60+ chapitres), le pipeline ne dépend plus d'un seul
fournisseur. `voice_casting._call_llm(prompt, provider)` aiguille vers
`_call_gemini` (format natif Google) ou `_call_openai_compatible`
(format partagé par Mistral et DeepSeek, tous deux compatibles avec
l'API chat OpenAI) selon le choix fait dans la fenêtre de sélection
côté interface (voir section dédiée plus bas). Les 3 clés API vivent
dans `data/config.json` (`gemini_api_key`, `mistral_api_key`,
`deepseek_api_key`), hors Git.

**DeepSeek choisi comme défaut après tests concluants en conditions
réelles** : `deepseek-chat` (pas `deepseek-reasoner`, voir piège
ci-dessous), le moins cher des 3 options. Testé sur 2 chapitres du
Comte de Monte-Cristo (897 phrases cumulées) avec 0 phrase orpheline,
tous les personnages détectés, bonne cohérence sur les répliques
fragmentées — puis validé en conditions réelles sur un tome complet
(20 chapitres, 56 voix générées, aucune erreur).

**Modèle historique : Google Gemini Flash** (`gemini-3.7-flash`).
Sans-faute sur les tests initiaux, le seul des 5 candidats testés à
l'époque (Claude Sonnet 5, Claude Haiku 4.5, Mistral Large, Gemini
Flash, DeepSeek Chat) à avoir traité un chapitre long (56 000
caractères) intégralement en un seul appel, en ~45 secondes, sans
erreur — reste disponible dans le sélecteur, mais n'est plus le choix
par défaut.

**Solution de repli historique : Claude Haiku 4.5.** Sans-faute lui
aussi sur le premier extrait (court), mais s'est fait tronquer puis a
timeout sur le chapitre long malgré un `max_tokens` remonté à 64000 —
débit de génération très inférieur à Gemini Flash (~48 mots/s contre
~300 mots/s mesurés). Non integre au systeme multi-moteur actuel
(seuls Gemini/Mistral/DeepSeek le sont).

**Découpage par paquets de 150 phrases (`BATCH_SIZE`), quel que soit
le moteur.** Les tout premiers tests envoyaient un chapitre entier en
un seul appel — fonctionnait avec Gemini (chapitres jusqu'à 56 000
caractères), mais DeepSeek tronque sa réponse avant la fin sur les
chapitres les plus longs/bavards (plus de 450 phrases avec beaucoup de
dialogue), même avec `max_tokens` remonté à 16000. Découvert en
conditions réelles sur le Tome II (chapitre à 477+ phrases, JSON coupé
en plein milieu). Corrigé en découpant chaque chapitre en paquets de
150 phrases envoyés séparément — la fiche de personnages voyage d'un
paquet à l'autre exactement comme elle voyage déjà d'un chapitre à
l'autre, aucun changement de comportement pour l'utilisateur, juste
plus d'appels réseau (invisibles, gérés en tâche de fond).

**Piège technique identifié — à ne jamais oublier en cas de changement
de modèle :** les modèles avec réflexion interne activée par défaut
(Claude Sonnet 5 en mode adaptive thinking, DeepSeek en version
`deepseek-reasoner`) consomment une partie invisible du budget de
tokens de sortie avant même de commencer à écrire la réponse — sur une
tâche mécanique comme celle-ci, ça ne sert à rien et ça tronque les
réponses. Toujours désactiver ce mode explicitement (`thinking: {"type":
"disabled"}` chez Anthropic) ou choisir un modèle qui ne l'active pas
par défaut (Haiku 4.5, `deepseek-chat`, Gemini Flash). C'est exactement
pour cette raison que le routage DeepSeek du systeme multi-moteur
utilise en dur `"deepseek-chat"` et jamais `"deepseek-reasoner"`.

**Règle de nommage validée pour éviter les collisions d'alias :**
jamais de nom canonique ambigu (jamais juste "Morrel" quand père et fils
sont tous deux présents dans le livre) — toujours un identifiant complet
et unique par personnage (`Morrel_pere` / `Morrel_Maximilien`). Constaté
en pratique : DeepSeek a ignoré cette consigne malgré le prompt explicite
(a utilisé "Morrel" et "Maximilien" nus) — un point de vigilance si
DeepSeek est reconsidéré un jour.

**Architecture retenue — traitement séquentiel avec fiche de
personnages :** les chapitres sont traités dans l'ordre de lecture, une
fiche de personnages (nom canonique, genre, indices d'identité) voyage
d'un chapitre à l'autre et s'enrichit au fil de l'eau, pour que l'IA
désambiguïse "le jeune homme" ou "sa fille" avec le même contexte qu'un
lecteur humain plutôt que de fusionner des alias à l'aveugle après coup.

**Principe technique (inchangé) :**
- Nouvelle route `/api/books/{id}/cast` — déclenche l'analyse IA
- Nouvelle table SQLite `voices (book_id, character_name, voice_id, pitch)`
- Analyse faite une seule fois par livre, stockée définitivement
- Chaque `<span>` reçoit `data-voice` et `data-pitch` en plus de `data-idx`
- Le moteur TTS utilise les paramètres du span en cours

**Paramètre pitch déjà présent** dans `tts.py` (`DEFAULT_PITCH = "+0Hz"`),
pas encore exposé au frontend — à connecter lors de l'implémentation.

**Contrainte :** Voix françaises uniquement (usage exclusif en français).

**✅ Passe 1 et Passe 2 implémentées et testées de bout en bout**
(session du 19/08/2026), voir section dédiée "Module voice_casting.py"
plus bas dans ce document pour le détail technique complet.

**✅ Intégration complète dans l'appli (session du 20/08/2026)**

- Route `POST /api/books/{id}/cast` : traite le 1er chapitre en direct
  (l'appelant attend — barre de progression visible côté UI via
  `cast_status = "processing:1/N"`), puis lance les chapitres suivants
  en tâche de fond (`asyncio.create_task`), même principe que le
  préchargement audio x2 déjà en place pour le TTS. Fusion des alias +
  attribution des voix (Passe 2) déclenchées automatiquement une fois
  tous les chapitres traités.
- Route `GET /api/books/{id}/cast/status` : pollée toutes les 4s côté
  frontend pendant le traitement (`_startCastPolling` / `app.js`),
  arrêt automatique sur `done` ou `error`.
- Bouton "🎭" dans `#reader-settings`, 4 états visuels : à activer / en
  cours (avec avancement `n/N`) / erreur / actif — cliquer dessus une
  fois actif ouvre la fenêtre du casting (voir section dédiée plus bas)
  au lieu de relancer une analyse.

**Barre de réglages du lecteur remaniée le 15/09/2026** (demande de Laurent :
« moins gros, plus esthétique »). Elle tient maintenant en deux rangées :
les **deux boutons d'action** compacts côte à côte (« 🎭 Voix multiples »,
libellé raccourci, et « 🎧 Écouter les voix ») puis un conteneur
`#settings-menus` avec les **deux menus** — la voix du narrateur
(`#voice-select`, prend la place restante) et la vitesse (`#speed-select`,
taille naturelle). Constat qui a motivé le changement : le bouton
**« Écouter les voix » n'avait aucun style**, il gardait donc l'apparence
native du navigateur (fond clair, taille système) au milieu du thème sombre.
Au même moment, `color-scheme: dark` a été déclaré dans `:root`
(`styles.css`) pour que les **éléments natifs** (listes déroulantes des menus,
barres de défilement) s'affichent en sombre eux aussi.
- Moteur TTS (`app.js` / `_runTTS` + `_voiceForSentence`) : chaque phrase
  détermine sa voix/pitch via `_chapterSpeakers[idx]` (qui parle) croisé
  avec `_currentBookData.voices` (voix attribuée à ce personnage). Depuis
  le 08/09/2026 chaque phrase est synthétisée séparément (plus de fusion
  en groupes : la playlist est construite par `_buildPlaylist`). Repli
  automatique et silencieux sur la voix par défaut du narrateur si le
  personnage n'a pas de voix attribuée (livre pas encore analysé,
  narration, ou personnage absent du casting).
- **Incises de dialogue** ("dit Franz", "demanda-t-elle"...) : consigne
  explicite ajoutée au prompt Gemini (Passe 1, règle 8) pour toujours
  attribuer la phrase entière (réplique + incise) au personnage qui
  parle, jamais au narrateur — évite l'alternance incohérente narrateur/
  personnage constatée sur les premiers tests réels en conditions de
  conduite.
- Script de test autonome conservé dans `test_voix/` (hors de l'app,
  scratch de développement, protégé par `.gitignore`) — pas encore
  nettoyé, sans risque (gitignore), à faire un jour sans urgence.

**Validation terrain (conduite réelle)** : testé sur plusieurs chapitres
du Comte de Monte-Cristo (Laurent), changement de voix perceptible et
naturel entre narrateur et personnages, expérience jugée "bluffante".
Point faible identifié : certaines voix Edge TTS jugées trop
robotiques — motive le chantier Kokoro (voir backlog plus bas).

### Report des notes d'écoute dans les catalogues — étape 3 du listener
(15/09/2026). La fenêtre « Écouter les voix » range ses annotations dans
`data/annotations_voix.json` (fichier local, hors Git) ; l'outil
`test_voix/_appliquer_annotations_voix.py` les reporte dans les catalogues :
**aperçu par défaut**, écriture seulement avec `--ecrire`, sauvegarde
automatique des fichiers (`*.bak_avant_annotations_voix`), et conversion
**H → M** (l'écoute note H/F, les catalogues écrivent M/F). Les **étoiles** et
le **genre** sont reportés ; la **remarque libre** reste dans le fichier de
notes, les catalogues n'ayant pas de champ pour elle.

**Badges d'état dans la fenêtre du casting — session du 15/09/2026.** Une
**seconde barre de filtres** (« Personnages : Tous / ⚠ À caster / ⧉ Voix
partagée »), au même look que la barre de genre mais **pas le même rôle** :
celle du genre filtre les **voix proposées dans les menus**, la nouvelle filtre
les **lignes de personnages**. Chaque ligne reçoit un badge **seulement** dans
les deux cas qui demandent une décision :

- **⚠ à caster** : le personnage a au moins `MINOR_THRESHOLD` (8) répliques
  mais porte encore la voix générique des petits rôles — il n'a pas de voix à
  lui (c'est aussi l'état que produira un « déplacement » de voix, plus tard) ;
- **⧉ voix partagée (n)** : sa voix est portée par **n** autres personnages —
  à différencier avec la hauteur (pitch).

Un **résumé** s'affiche dans la barre : « N personnages · n à caster · n voix
partagée(s) ». Les **petits rôles** restent sans badge : leur voix générique
est voulue. La logique vit dans une fonction **pure** de `frontend/app.js`,
`_etatCasting(rows, filtre)` ; le comptage **ignore les voix génériques**,
partagées *par construction*, qui noieraient la liste sous de fausses alertes.
*Fichiers* : `frontend/index.html` (`#cast-etat-bar`, `#cast-etat-resume`),
`frontend/app.js` (`_castEtatFiltre`, `_CAST_MINOR_THRESHOLD`,
`_CAST_VOIX_GENERIQUES`, `_etatCasting`, badges), `frontend/styles.css` (barre
et badges `.cast-badge-caster` / `.cast-badge-partagee`). *Vérifications* :
`test_voix/test_etat_casting.js` (sans navigateur) et
`test_voix/test_ids_ecran.py` (les deux barres, les trois boutons, le seuil,
les badges).

**Voix libres et « partagée avec qui ? » — session du 19/09/2026.** Demande de
Laurent, sur un casting de 176 personnages : « je ne vois pas quelle voix est
libre », et l'onglet « Voix partagée » ne disait pas **par quel personnage** le
timbre était porté. Contrainte qu'il a rappelée : sur mobile il n'y a **ni
survol ni appui long** — tout ce qui compte doit donc être **écrit**, ou obtenu
au **tap** (un tap vaut un clic, y compris en PWA installée).

1. **Tiroir « Voix libres »** : un quatrième bouton dans la barre des
   personnages, qui porte son compte (« 🔓 Voix libres (68) »). La liste ne
   montre alors plus des personnages mais les voix **écoutables tout de suite**
   (`/api/voices`) qu'**aucun** personnage **ni le narrateur** ne porte, rangées
   par moteur (comme « Écouter les voix ») avec un ▶ d'écoute. Une voix dont le
   moteur est éteint ne peut pas y figurer : le tiroir le **dit** sous la barre,
   sinon ces voix sembleraient prises. **Lecture seule** — rien n'est attribué
   depuis le tiroir.
2. **Le narrateur compte comme une voix prise** (`books.narrator_voice`) : elle
   lit tout ce qui n'est pas du dialogue ; l'annoncer « libre » inviterait à lui
   donner un second rôle. **Mais le narrateur peut ÊTRE un personnage** : dans
   « 22/11/63 », Jake Epping (3 634 répliques, verrouillé) porte exactement la
   voix du narrateur, et c'est un choix de Laurent (récit à la première
   personne). Cette voix n'est donc jamais proposée comme libre, le personnage
   reçoit un badge **« 🎙 voix du narrateur »** (informatif) et la phrase de
   détail écrit **les deux rôles** (« … 1 personnage parle aussi avec : Jake
   Epping »). La référence est la voix du **menu du haut**, pas celle enregistrée
   dans le livre : un changement de voix du narrateur est vu tout de suite. À
   savoir : **le re-cast ignore `narrator_voice`** (`modules/voice_casting.py`),
   donc seule la case **🔒** protège ce couple.
3. **Le badge écrit les noms** : « ⧉ partagée avec Edmond, Busoni » (deux noms,
   puis « et N autres »), et se **déplie au tap** (rôle de bouton, `Entrée` au
   clavier) sur la phrase complète : nombre de porteurs, noms et répliques —
   plafonnée à **six noms**, puis renvoi à l'onglet « Voix partagée », qui les
   liste tous un par ligne (cas réel : une voix portée par **dix-huit**
   personnages dans « 22/11/63 »). En vue « Voix partagée », les lignes sont
   **groupées par voix**, avec un en-tête « ⧉ <voix> — n personnages ». Quand le
   badge est déplié, chaque co-porteur est un **bouton** (nom + répliques) qui
   fait **défiler la liste jusqu'à sa ligne** et la met en évidence un instant
   (`_allerAuPersonnage`) : si un filtre cache le personnage, le tap
   l'**explique** au lieu de rester sans effet.
4. **Marque d'usage dans les menus** : chaque voix porte son état au moment du
   choix (` · LIBRE`, ` · partagée (2)`, ` · narrateur`, ` · petits rôles`, ou
   ` · <nom>` s'il n'y a qu'un porteur), et le panneau « Voir la voix »
   **écrit** l'état de la voix choisie sous le menu (`#voice-phrase-usage`).
5. **Recalcul après un changement de voix** (constat de Laurent, 19/09/2026) :
   badges, groupes, marques et tiroir n'étaient calculés **qu'à l'ouverture** —
   après avoir donné une voix libre à un personnage, sa fiche continuait
   d'annoncer « Portée par 2 personnages : … ». `_rafraichirCastingApresChangement()`
   recalcule désormais après chaque changement de voix : il **attend**
   l'enregistrement (sinon il relirait l'ancienne voix), ne **recharge rien** du
   serveur, **remet la liste à sa position** et utilise un **jeton** si l'on
   change deux voix coup sur coup. Les curseurs vitesse/hauteur ne déclenchent
   aucun recalcul (ils ne changent pas *qui* porte la voix), et un échec
   d'enregistrement est maintenant **dit** à l'écran. Le panneau « Voir la
   voix » rafraîchit lui aussi la fenêtre du casting s'il la trouve ouverte, et
   son changement de voix du **narrateur** est désormais **enregistré pour le
   livre** (il ne l'était pas : l'enregistrement part du menu du haut).
6. **Prendre une voix libre depuis une fiche** (19/09/2026) : chaque ligne de
   personnage a un bouton **🗣️** (une tête qui parle — surtout pas un cadenas
   ouvert, qui dirait « déverrouillé » sur le bouton juste à côté) qui ouvre
   `#voixlibres-modal` — la liste des
   voix que **personne** ne porte (même présentation que le tiroir : rangées par
   moteur, ▶ pour écouter), avec sur chacune un bouton **« Choisir »** qui
   l'attribue au personnage en **conservant vitesse et hauteur**. Le geste part
   du **personnage**, pas du tiroir : partir d'une voix obligerait ensuite à
   chercher *qui*, parmi 175 personnages — justement ce qu'on veut éviter.

*Fichiers* : `frontend/app.js` (`_etatVoix`, `_resumeNoms` et
`_pitchPartageLibre`, fonctions **pures** ; `_lignesPersonnages`, extrait de
`_openCastModal` et **partagé** avec le panneau « Voir la voix » pour que les
deux comptent les **mêmes répliques** ; `_etatVoixLivre`, `_detailPartageVoix`,
`_allerAuPersonnage`, `_demanderPartage`, `_deplacerAutresVersGenerique`,
`_afficherVoixLibres`, `_previewVoixLibre`, `_majInfoVoixLibres`,
`_rafraichirCastingApresChangement`, `_ouvrirVoixLibres`, `_donnerVoixLibre`,
`_fermerVoixLibres`), `frontend/index.html` (`#cast-libres-info`,
`#voice-phrase-usage`, bouton `data-etat="libres"`, modales `#partage-modal` et
`#voixlibres-modal`), `frontend/styles.css` (`.cast-group`,
`.cast-partage-detail`, `.cast-partage-chip`, `.cast-voix-libre`,
`.cast-libre-btn`, badge cliquable et repliable). *Vérifications* :
`test_voix/test_etat_casting.js` (noms des porteurs, voix libres hors génériques
et hors narrateur, marques, phrases, plafond à six noms, hauteur de partage) et
`test_voix/test_tiroir_voix_libres.js` (**nouveau** : le *rendu* du tiroir, du
dépliage, de la modale Partager/Déplacer et de l'attribution d'une voix libre,
sans navigateur).

**Barre de recherche dans la fenêtre du casting** (item du BACKLOG du
14/09/2026, **livré le 20/09/2026**). Sur un livre à **175 personnages**,
retrouver un nom à la main devenait long : un champ `#cast-search` est placé **en
haut** de la fenêtre et filtre les lignes **pendant la frappe**. Trois choix,
tous dictés par l'usage réel :

1. **Comparaison indirecte** : minuscules, **sans accents**, apostrophes, tirets
   et underscores réduits à des espaces — « EDMOND », « Edmond » trouvent le
   même nom, et « jean luc » trouve **Jean-Luc**. C'est la règle de
   `normalize_character_name` (`modules/voice_casting.py`), **sauf l'article
   initial**, qui n'est pas retiré : dans une recherche en direct, taper « le »
   doit filtrer, pas s'évanouir ;
2. **Les familles restent lisibles** : un personnage trouvé **garde ses alias**
   (ses autres appellations), et taper un **alias** fait remonter **son
   personnage** — sans lui, la ligne d'alias s'afficherait seule, en retrait
   sous une fiche absente ;
3. **Elle ne laisse jamais un vide muet** : un **compteur** écrit ce que la
   liste montre (« 3 personnages sur 176 »), et une recherche sans résultat
   l'**écrit** (« Aucun personnage ne correspond à … »). Dans le **tiroir des
   voix libres**, où la liste montre des *voix* et non des personnages, la même
   barre filtre le **prénom et la provenance** — sinon elle aurait l'air morte
   dans cet onglet.

Deux détails de confort : la frappe **ne rappelle pas le serveur**
(`_openCastModal(false, true)`, argument `listeSeule`) et la recherche est gardée
dans `_castRecherche` pour **survivre aux reconstructions** de l'affichage
(filtre d'état, changement de voix). Deux garde-fous d'exactitude : les
compteurs et les badges restent calculés sur **tout le livre** (le badge
« partagée avec … » ne doit pas perdre les autres porteurs dès la première
lettre tapée), et la recherche **se combine** avec le filtre d'état
(« ⚠ À caster » **et** « edm »). Elle est **remise à zéro à la fermeture** : on
rouvre la fenêtre sur la liste complète.

*Fichiers* : `frontend/index.html` (`#cast-search-bar`, `#cast-search`,
`#cast-search-resume`), `frontend/app.js` (`_castRecherche`, `_cleRecherche`,
`_filtrerPersonnages`, `_filtrerVoixLibres`, fonctions **pures** ;
`_openCastModal` ; `_afficherVoixLibres`, `_closeCastModal`),
`frontend/styles.css` (`#cast-search-bar`, `#cast-search`,
`#cast-search-resume`). *Vérifications* : `test_voix/test_recherche_casting.js`
(33 contrôles, sans navigateur), `test_voix/test_tiroir_voix_libres.js` (le
tiroir filtré, message quand rien ne correspond) et `test_voix/test_ids_ecran.py`
(les éléments, les fonctions, le style).

### Module voice_casting.py — détail technique
- `_split_chapter_sentences()` : découpe le chapitre en phrases
  numérotées côté serveur, identique à la logique déjà utilisée côté
  client (`_buildSentences()` dans app.js) et côté recherche
  (`_split_sentences()` dans main.py) — garantit une correspondance
  exacte avec ce qui s'affiche à l'écran
- **Principe de sécurité central** : Gemini ne reçoit et ne renvoie
  jamais le texte des phrases lui-même, seulement des numéros. Même
  verrou actif côté réception (`_call_gemini` supprime activement tout
  champ "texte" que Gemini aurait pu renvoyer par erreur/reformulation)
  — le texte affiché et lu vient toujours et uniquement d'`epub_parser.py`
- `analyze_chapter()` : Passe 1 sur un seul chapitre — découpe, appelle
  Gemini avec la fiche de personnages connue, retourne la fiche mise à
  jour + l'attribution phrase par phrase
- `analyze_chapters()` : enchaîne plusieurs chapitres à la suite, fiche
  de personnages qui voyage et s'enrichit d'un chapitre à l'autre
- `consolidate_book()` : Passe 2 — fusionne les alias/doublons détectés
  dans la fiche accumulée (ex: "Matelot"/"Matelots"), réécrit les
  attributions de tous les chapitres en conséquence, compte les
  répliques par personnage, attribue voix + pitch définitifs
- `assign_voices()` : personnages avec moins de `MINOR_THRESHOLD` (= 8
  depuis le 08/09/2026, c'était 3) répliques sur tout le livre → voix
  générique partagée par genre (`fr-FR-EloiseNeural` / `fr-CH-FabriceNeural`),
  sans consommer de voix dédiée. Les autres → voix dédiée piochée dans un
  pool par genre (Edge françaises + toutes les voix Kokoro triées par
  note), avec léger décalage de pitch supplémentaire si le pool est
  épuisé (plus de personnages principaux que de voix dédiées disponibles
  pour ce genre)
- Pitch selon l'âge du personnage : `+15Hz` (jeune), `+0Hz` (adulte),
  `-15Hz` (âgé)
- Modèle utilisé : `gemini-3.7-flash`, appelé avec
  `thinkingLevel: "LOW"` (repli automatique sur le réglage par défaut si
  erreur 400), relance automatique (3 essais, pause 10s) sur erreurs
  429/503 de surcharge
- Clé API stockée dans `data/config.json` (jamais commité, voir
  `.gitignore`), chargée via `modules/config.py`
- **Coût observé** : environ 1 à 1,50 $ par livre complet de ~35
  chapitres (tarif Gemini 3.7 Flash, promo jusqu'à fin décembre 2026) —
  nécessite un compte Google AI Studio avec facturation activée (Tier 1),
  le niveau gratuit étant vite limité par le quota de requêtes/jour
- Testé avec succès sur 3 chapitres réels du Comte de Monte-Cristo
  (extraits `data/library/`) : correspondance des id parfaite (aucun
  décalage texte/voix), fusion Matelot/Matelots détectée et appliquée
  correctement, attribution voix stable entre plusieurs runs malgré
  l'ordre de réponse variable de Gemini

### 🎭 Fenêtre du casting (visuel) — session du 20/08/2026
**Rôle :** consulter et corriger manuellement le résultat de l'analyse
voix multiples, sans attendre une réanalyse complète du livre.

**Ouverture :** clic sur le bouton "🎭" du lecteur une fois à l'état
"Voix multiples actives" (`cast_status === 'done'`) → `_openCastModal()`.

**En-tête compact (22/09/2026).** La fenêtre ne porte plus que **trois**
commandes (recherche, Filtres, fermeture) : les filtres, la saga et les boutons
de re-cast sont rangés dans un **tiroir des réglages** repliable, la fenêtre ne
dépasse plus l'écran et la liste des personnages garde une hauteur minimale.
Voir la section « En-tête compact de la fenêtre du casting ».

**Filtre par genre des voix proposées (12/09/2026).** Le catalogue ayant
atteint **135 voix** (73 femmes, 62 hommes), les menus du casting sont
désormais **organisés par genre** : un groupe **👩 Femmes** et un groupe
**👨 Hommes** (`<optgroup>`), chaque groupe trié par ordre alphabétique — le
genre n'est donc plus répété sur chaque ligne. Une barre **« Voix proposées :
Toutes / Femmes / Hommes »** en haut de la fenêtre (`#cast-gender-bar`,
mémorisée dans `_castGenreFiltre`) permet de ne montrer qu'un seul genre dans
**tous** les menus d'un coup. Deux sécurités : la **voix actuellement
attribuée** reste toujours visible (groupe « ⚠️ Voix actuelle ») même si le
filtre la masque — sinon on croirait que le personnage n'a plus de voix ; et
une voix qui n'existe plus au catalogue s'affiche dans un groupe « ⚠️ Voix
introuvable » plutôt que de laisser le menu montrer une autre voix en
silence.
**Depuis le 22/09/2026, il n'y a plus de menu déroulant du tout (voie B choisie
par Laurent)** : la liste des voix est une **liste de l'application** — de vrais
éléments de page, donc au thème — et chaque voix s'écrit sur **DEUX lignes** :
l'identité (symbole, prénom, drapeaux, âge, timbre) puis l'icône du moteur et
l'état (« · LIBRE », « · Edmond »). Les groupes `👩 Femmes` / `👨 Hommes` /
`Autres` sont devenus des **titres de ligne** (`<li class="voix-liste-groupe">`).
La construction est une fonction **pure**, `_lignesVoixPersonnage()` : les règles
énumérées ci-dessus sont **inchangées** (filtre de genre, groupes, tri
alphabétique, voix actuelle toujours visible, cas « pas de voix » et
« introuvable » distincts). Elle est peinte par
`_basculerListeVoixPersonnage()`, qui déplie la liste **sous la ligne du
personnage** (un seul encart ouvert à la fois), et c'est
`_boutonVoixPersonnage()` qui remplace le `<select>` : il écrit la voix actuelle
sur une ligne et ouvre la liste au tap.

**Contenu :** un personnage par ligne (`#cast-modal` /
`.cast-row`), triés par nombre de répliques décroissant :
- Nom du personnage (nom canonique tel qu'attribué par Gemini)
- Badge "Homme/Femme · N répliques" (`genre`/`line_count`, stockés en
  base depuis `assign_voices()` → `voice_casting.py`)
- **Bouton de voix** (un `<select>` jusqu'au 22/09/2026) listant toutes les voix
  disponibles (`_allVoices`, chargé une fois via `/api/voices`, avec tags
  nom/genre/région déjà présents dans les catalogues côté serveur), voix actuelle
  affichée dessus. Il ouvre la **liste de l'application** (voir ci-dessus) **sous
  la ligne du personnage**. Depuis le 12/09/2026, le libellé est construit par
  `_libelleVoix()` (`app.js`) : **« Prénom (F) — 🇫🇷 France (Kyutai) »** —
  le genre en clair permet de repérer d'un coup d'œil une voix féminine pour
  un personnage féminin (le narrateur utilise le même libellé). Cette aide
  remplace en partie le filtre par genre encore au backlog.

**Changement de voix :** au `change` du menu déroulant,
`_updateCharacterVoice()` appelle immédiatement
`PUT /api/books/{id}/cast/voice` (pas de bouton "Enregistrer" à
chercher) — met à jour la ligne correspondante dans la table `voices`,
effectif dès la prochaine phrase lue par ce personnage.

**Piège rencontré et corrigé :** `_currentBookData.voices` n'était
chargé qu'à l'ouverture du livre, donc encore vide au moment où le
`cast_status` passait à `done` en tâche de fond — la fenêtre s'ouvrait
sur "Aucun personnage identifié" même une fois l'analyse terminée.
Corrigé en rechargeant `GET /api/books/{id}` (donc `book.voices` à
jour) au moment précis où le polling de statut détecte `done`, avant
d'arrêter le polling (`_startCastPolling` / `app.js`).

**Pas encore fait (backlog) :** catalogue de voix limité aux 12 voix
Edge TTS françaises taguées H/F/région — l'intégration Kokoro (voir
backlog plus bas) viendra enrichir ce même menu déroulant avec des voix
à accent étranger forcé en français, sans changement structurel prévu
côté fenêtre (juste plus d'entrées dans `_allVoices`).

### ♻️ Re-cast d'un livre déjà casté (gratuit) — session du 12/09/2026
**Besoin (Laurent) :** relancer un casting sur un livre déjà casté pour
récupérer les nouvelles voix, SANS supprimer puis ré-importer le livre
(ce qui coûterait un casting complet et ferait perdre la progression).

**Principe clé — pourquoi c'est gratuit :** le pipeline de casting stocke
les deux résultats séparément. « Qui parle » est gardé **définitivement**
pour tout le livre dans `speaker_attribution` ; la liste des personnages et
leur voix sont dans `voices`. Un re-cast pour *changer les voix* n'a donc
**pas besoin de rappeler l'IA** : il suffit de redistribuer les voix dans le
catalogue courant (`assign_voices()`), ce qui est du calcul local →
**0 appel IA → 0 $**. Le seul cas qui repaie le prix plein est de refaire
l'analyse complète (Passe 1 + Passe 2), pour corriger *qui parle*.

**Mécanisme implémenté :**
- Nouvelle colonne `voices.locked` (ajout non destructif, valeur par défaut
  0) : un personnage verrouillé conserve sa voix lors d'un re-cast.
- `PUT /api/books/{id}/cast/lock` : verrouille/déverrouille une voix.
- `POST /api/books/{id}/cast/reassign` : re-cast gratuit. Rejoue
  `assign_voices()` en passant les personnages verrouillés comme
  `voix_figees` — **exactement le mécanisme déjà utilisé pour les sagas**,
  donc comportement identique et éprouvé. Seul le `voice_id` est réécrit :
  **le pitch et la vitesse existants sont conservés** (l'âge des personnages
  n'est pas stocké en base, donc on ne peut pas recalculer le pitch d'âge
  après coup — on ne l'écrase pas non plus).
- Fenêtre du casting (`#cast-modal`) : un bouton 🔒 par personnage (défaut
  « non verrouillé », donc tout est redistribué) + un bouton
  **« Re-caster (gratuit) »** en bas de fenêtre, avec confirmation.
- `GET /api/books/{id}` renvoie désormais `locked` par personnage.

**Limite assumée :** la redistribution est déterministe (tri par nombre de
répliques décroissant) ; un personnage peut donc retomber sur la même voix,
et l'appli ne peut pas distinguer un ancien choix manuel d'une ancienne
attribution automatique (l'ancien casting utilisait une autre liste de voix).
D'où le verrou explicite : c'est l'utilisateur qui désigne ce qu'il garde.

**Le cadenas du casting est un DESSIN, plus un emoji (21/09/2026).** Retour de
Laurent : « sur mobile, le cadenas apparaît avec une aura quand la voix est
verrouillée, et sans son aura quand elle ne l'est pas ; je préférerais ces deux
icônes 🔒 / 🔓, comme sur PC ». Le code envoyait bien **les deux emojis** — c'est
leur **dessin** qui change d'un appareil à l'autre (constat déjà fait pour
⏮⏪⏩⏭ le 20/09/2026), assez peu lisibles sur son téléphone pour que **seule
l'aura dorée du bouton** dise l'état. Même remède que les flèches du lecteur :
un **SVG**, qui ne dépend d'aucune police.

- `_svgCadenas(verrouille)` (`frontend/app.js`) : le corps (`rect`) et l'anse en
  `stroke="currentColor"` — **anse rabattue = verrouillé**, **anse relevée =
  déverrouillé**. Le dessin prend donc la **couleur du bouton** : accent doré
  quand la voix est verrouillée, gris sinon, avec la même géométrie partout.
- `_peindreCadenas(btn, verrouille)` peint **ensemble** le dessin, l'infobulle
  et l'`aria-label` ; le bouton n'a plus de texte propre, donc l'affichage et le
  clic ne peuvent pas se contredire. Il est appelé aux **deux** endroits :
  construction de la ligne et bascule (`_toggleCharacterLock`).
- L'aura du bouton (`.cast-lock-btn.locked`) est **conservée** : elle souligne
  l'état, elle ne le porte plus seule. `styles.css` centre les deux boutons à
  icône (`display: flex`) et donne sa taille au SVG — **16 px** sur PC, **22 px**
  sur mobile (bouton de 44 px, cible du doigt).
- Les emojis de cadenas qui sont du **TEXTE** ne changent pas : le filtre
  « 🔓 Voix libres (n) » et les phrases de confirmation du re-cast. Ils sont
  écrits, pas cliqués.

*Vérifications* : `test_voix/test_tiroir_voix_libres.js` (les deux anses, l'appel
unique `_peindreCadenas(btn, newLocked)`) et la suite complète — **36 tests,
TOUT EST OK**. Copies de retour arrière datées :
`frontend/app.js.bak_avant_cadenas_svg_20260921`, idem `styles.css` et
`index.html`.

### 🎭 Les petits rôles : une voix par genre (Jessica / Pierre) — 21/09/2026

Décision de Laurent : tout personnage de **moins de `MINOR_THRESHOLD` (8)
répliques** est joué par une **voix générique selon son genre** — **Jessica**
pour les femmes, **Pierre** pour les hommes, toutes les deux en **Piper**.

Le terrain était prêt : depuis le **15/09/2026**, cette branche renvoyait un
`voice_id` **VIDE** (les petits rôles étaient lus par le **narrateur**, après le
verdict « inaudibles, vraiment moches » porté sur les voix génériques d'alors,
Siwis/Tom), et le code gardait **deux emplacements vides exprès**
(`GENERIC_VOICE_F/M`) avec ce commentaire : « le jour où Laurent aura choisi
deux voix neutres, il suffira de les y mettre, puis de re-caster ».

- **Les deux voix** : `piper:upmc:0` = **Jessica** (femme, **3 étoiles** à
  l'écoute) et `piper:upmc:1` = **Pierre** (homme, **1 étoile**), toutes les deux
  dans le modèle **studio** Piper `fr_FR-upmc-medium`. Ce ne sont PAS les voix
  refusées (Siwis/Tom) ; l'homonyme à ne pas confondre est `kokoro:af_jessica`,
  une Jessica **américaine** du catalogue Kokoro.
- `modules/voice_casting.py` : `GENERIC_VOICE_F/M` remplis, et `assign_voices()`
  appelle la nouvelle fonction `_voix_generique(genre)` au lieu d'écrire un vide.
  Un genre inconnu part sur **Pierre**, comme partout ailleurs (le genre par
  défaut d'une fiche est `H`). La hauteur reste `+0Hz` (voir « reste possible »).
- `frontend/app.js` : `_CAST_VOIX_GENERIQUES = ['piper:upmc:0', 'piper:upmc:1']`
  — **l'ordre compte** ([0] femmes, [1] hommes, cf.
  `_deplacerAutresVersGenerique`). Sans cette mise à jour, Jessica et Pierre
  auraient été comptées comme « voix partagée » des centaines de fois.
- Piper reste **hors du pool automatique** : il ne sert qu'ici, et pour ces deux
  voix.

**Livres déjà castés — migration ciblée (l'option choisie par Laurent).**
`test_voix/migrer_petits_roles.py`, avec son lanceur double-clic
`MIGRER_PETITS_ROLES.bat`, réécrit **une seule colonne** (`voice_id`) sur les
lignes de moins de 8 répliques, et **rien d'autre** : les lignes **verrouillées**
sont laissées telles quelles (**34** sur les 11 livres castés), les **hauteurs et
vitesses** de chaque personnage sont **conservées** — deux petits rôles d'une
même scène ne sonnent donc pas exactement pareil —, et les rôles de 8 répliques
et plus ne sont pas regardés du tout. L'outil fait d'abord un **essai** (aucune
écriture), puis, avec `--appliquer`, une **copie datée de la base avant
d'écrire** (API de sauvegarde de SQLite : copie cohérente même si le lecteur
tourne) et une **relecture de contrôle**. Appliqué le **21/09/2026** :
**643 lignes sur 11 livres** (copie
`nimm_epub.db.bak_avant_petits_roles_20260921_2128`), et l'outil est
**rejouable** (un second passage dit « Rien à faire »).

*Vérifications* : `test_voix/test_pool_casting.py` (§6 : un petit rôle homme
reçoit Pierre, une femme reçoit Jessica ; §7 : les deux listes client/serveur
doivent être **identiques et dans le même ordre**) et
`test_voix/test_attribution_criteres.py`. Ce dernier **ne tournait plus** : il
manquait à la liste `TESTS_PY` du lanceur de tests, et son contrôle « aucune voix
à 0 étoile attribuée » comptait Jessica/Pierre comme telles alors que Piper est
**hors** de l'index du pool automatique (et que Pierre est noté **1 étoile**).
Réparé **et ajouté à la suite** : **37 tests, TOUT EST OK**.

*À savoir* : le **serveur** ne prend le nouveau code qu'après un **redémarrage**
(bouton « 🔄 Redémarrer NIMM ePub » du panneau Réparer, ou `START.bat`) — la
migration, elle, est **déjà en base**.

**Les variantes de timbre (même jour).** Question de Laurent : « on a combien de
variations possibles entre la vitesse et la hauteur ? » Réponse mesurée, bornes
des curseurs du casting : **hauteur** de -20 à +20 Hz par pas de 4 → **11
crans** ; **vitesse** de -30 à +30 % par pas de 5 → **13 crans** ; soit
**11 × 13 = 143 couples (hauteur, vitesse) pour une même voix**
(`PITCH_VARIANTES`, `RATE_VARIANTES`, `NB_VARIANTES_GENERIQUES` et
`_variante_generique` dans `modules/voice_casting.py`). Chaque petit rôle reçoit
**sa propre variante**, répartie **par livre et par genre**.

- L'**ordre** des crans est choisi pour le dialogue : les hauteurs, à grands
  écarts (0, +8, -8, +16, -16, +4, -4, +12, -12, +20, -20), sont parcourues
  **avant** les vitesses — deux petits rôles **voisins** dans la liste ont donc
  toujours une hauteur différente.
- **Couverture** : le plus gros besoin mesuré le 21/09/2026 est de **85 petits
  rôles d'un même genre** (Monte-Cristo T6) : **143 suffit, avec 58 de marge**.
  Au-delà, on recommence au début — deux petits rôles partageraient alors
  exactement la même voix (accepté par Laurent).
- **Pourquoi c'était utile** : avant cette répartition, **422 petits rôles** de
  la base étaient **exactement identiques** (`+0Hz` **et** `+0%`) — une foule de
  Pierre et de Jessica interchangeables.
- Les rôles **dédiés** ne changent pas : ils gardent la vitesse neutre (`+0%`) et
  ne se distinguent que par la hauteur (`PITCH_BY_AGE`).
- Les bornes des variantes sont **volontairement** celles des curseurs : une
  valeur hors bornes serait ramenée par le curseur à l'affichage, et la fiche
  montrerait autre chose que ce qui est enregistré. Un test le verrouille
  (`test_pool_casting.py` §6b).

*À savoir sur l'outil de migration* : depuis cette répartition, il écrit **trois
colonnes** ensemble (`voice_id`, `pitch`, `rate`), et il reste **rejouable** —
une ligne déjà conforme n'est pas retouchée. Les 34 lignes verrouillées ne sont
jamais touchées.

### 🧩 Regroupement des alias (doublons d'écriture) — session du 12/09/2026
**Problème (Laurent) :** un même personnage apparaît éclaté dans le casting
selon la façon dont il est nommé dans le texte : `Gerard de Villefort` /
`Gérard de Villefort`, `Chateau-Renaud` / `Château-Renaud`, `Monte-Cristo` /
`Comte de Monte-Cristo` / `Le comte de Monte-Cristo`. Chaque variante recevait
sa propre voix.

**Étape 1 livrée — fusion automatique des doublons d'ÉCRITURE (gratuite) :**
- `voice_casting.normalize_character_name()` : minuscules, accents retirés,
  apostrophes/tirets/underscores réduits à des espaces, ponctuation retirée,
  article initial enlevé (`le/la/les/l'/un/une/des/du/de`).
- `voice_casting.find_writing_duplicate_groups()` : regroupe les noms dont la
  forme normalisée est identique ; le « principal » proposé est celui qui a le
  plus de répliques (le nom réellement lu dans ce tome).
- **Volontairement conservateur** : aucun nom de famille n'est retiré, donc
  `Baron Danglars` / `Baronne Danglars` et la famille `Villefort`
  (Gérard / Noirtier / Valentine) ne sont JAMAIS confondus.
- Route `POST /cast/autogroup` (`apply=false` = aperçu, `apply=true` =
  applique) + bouton « Regrouper doublons » dans la fenêtre du casting
  (aperçu confirmé avant application).

**Table `character_aliases (book_id, alias_name, canonical_name)`** : purement
descriptive. **Aucun nom n'est supprimé ni réécrit** — c'est ce qui rend le
regroupement réversible (`POST /cast/ungroup` = bouton ✂ dans la fenêtre).
Au moment du regroupement, la voix de base (voix + pitch + vitesse) du
principal est recopiée sur chaque alias.

**Chaque alias garde sa propre voix, modifiable indépendamment** (exigence
Laurent : Monte-Cristo doit pouvoir parler avec l'accent italien en Busoni,
avec l'accent anglais en commis « Thomson and French »...). Dans la fenêtre, les
alias sont affichés en retrait sous leur principal, chacun avec son menu de
voix et ses réglages : après regroupement, changer la voix d'un alias ne
change que lui.

**Re-cast compatible :** `POST /cast/reassign` traite désormais un groupe comme
UNE fiche (répliques additionnées) et applique la même voix à tous ses membres
(sauf ceux verrouillés individuellement) → un re-cast ne ré-éclate pas les
alias.

**Reste à faire (étape 2, backlog) :** rattachement MANUEL des vrais
pseudonymes (`l'abbé Italien` → `abbé Busoni`), que la règle d'écriture ne peut
pas deviner ; puis, en option, des propositions par l'IA validées à la main.

### 🧬 Bug corrigé — la fiche de personnages qui rétrécissait entre chapitres
**Symptôme constaté par Laurent** : un personnage identifié tôt dans le
livre (Franz, puis Maître Pastrini) disparaissait purement et
simplement du casting final, alors qu'il parle bel et bien à un moment
du livre.

**Cause réelle** : la fiche de personnages voyage d'un chapitre à
l'autre (`fiche = result["personnages"]`, `main.py` /
`_process_remaining_chapters`). Le prompt Passe 1 ne précisait pas que
le champ `"personnages"` renvoyé devait TOUJOURS contenir l'intégralité
de la fiche connue, même les personnages absents du chapitre en cours
— une consigne anti-hallucination existante ("n'invente jamais un
personnage absent du texte") était visiblement interprétée trop au
pied de la lettre par l'IA, qui ne renvoyait que les personnages du
chapitre courant. Résultat : un personnage absent d'un seul chapitre
sortait discrètement de la fiche, pour de bon.

**Correctif appliqué** (`_build_prompt`, `voice_casting.py`) : règle
explicite ajoutée — le champ `"personnages"` doit toujours contenir
l'intégralité des personnages connus, en plus des nouveaux du chapitre
courant ; ne jamais en supprimer un sous prétexte qu'il est absent du
chapitre en cours. Confirmé effectif sur une ré-analyse complète du
Tome II (Pastrini bien présent dans le casting final, aux côtés de 55
autres personnages).

**Point de méthode à retenir** : une consigne au prompt reste
probabiliste (l'IA peut s'en écarter sur des cas tordus, voir le gard
déterministe ci-dessous pour un exemple concret) — mais pour ce bug
précis, la consigne explicite a suffi à corriger le comportement de
façon fiable sur test réel.

### 🎯 Gard déterministe — citations coupées par le découpage automatique
**Symptôme** : une citation entre guillemets peut se retrouver coupée
sur 2 phrases consécutives par le découpeur automatique (partagé avec
l'affichage et la recherche, donc jamais modifié), à cause d'un `!` ou
`?` interne à la citation, avant son guillemet fermant `»`. Exemple
réel rencontré : `« Ah !` (phrase N) suivi de `si Votre Excellence
voulait, lui dit le patron...` (phrase N+1) — DeepSeek attribuait
parfois le premier fragment à un personnage différent du second, alors
que c'est une seule et même réplique.

**Deux tentatives, une seule fiable :**
1. *Consigne au prompt* (règle 9, `_build_prompt`) : demande à l'IA de
   détecter les citations non refermées et de garder le même locuteur
   sur tous les fragments. Fonctionne sur la majorité des cas, mais pas
   sur les cas les plus ambigus (ex: toute première réplique d'un
   chapitre, sans aucun contexte pour deviner qui parle).
2. *Gard déterministe côté code* (`_harmonize_open_quotes`,
   `voice_casting.py`) : compte les `«`/`»` phrase par phrase pour
   détecter les fragments d'une citation ininterrompue (fermeture du
   groupe aussi sur nouveau tiret de dialogue, nouveau `«`, ou reprise
   en majuscule — car une suite de citation après un `!`/`?` interne
   reprend toujours en minuscule). Force ensuite tous les fragments du
   groupe sur le locuteur le plus fiable (non-narration, meilleure
   confiance, dernier en cas d'égalité — porte souvent l'incise "dit
   untel" qui permet d'identifier le vrai locuteur). S'exécute après la
   réponse de l'IA, donc garanti et indépendant du moteur utilisé.

Validé sur cas réel (Franz/Gaetano, Tome II) : le fragment `« Ah !`
mal attribué à Franz par DeepSeek est corrigé automatiquement vers
Gaetano, avec `anomalie: "locuteur harmonise automatiquement"` pour
traçabilité.

**Non traité pour l'instant** : le même piège pour les répliques
introduites par un tiret de dialogue (`—`) coupées en deux par un `!`/
`?` interne — cas différent des guillemets (le tiret introduit
normalement une **nouvelle** réplique, souvent d'un personnage
différent, donc la même règle ne peut pas s'appliquer telle quelle).
Backlog, pas encore rencontré en pratique.

### 🔀 Système multi-moteur — Gemini / Mistral / DeepSeek (session du 21/08/2026)
**Déclencheur** : crédit Gemini épuisé après un essai sur *Les
Misérables* (60+ chapitres) — besoin de pouvoir basculer sur un autre
fournisseur sans refaire tout le travail d'intégration.

**Architecture** : `voice_casting._call_llm(prompt, provider)` est le
point d'entrée unique, utilisé par `analyze_chapter` et
`consolidate_book`. Deux implémentations en dessous :
- `_call_gemini` : format natif Google (`generateContent`,
  `thinkingConfig`)
- `_call_openai_compatible(prompt, url, api_key, model)` : format chat
  OpenAI standard, partagé par Mistral (`mistral-large-latest`) et
  DeepSeek (`deepseek-chat`) — même retry (5 tentatives, 15s de pause
  sur 429/503), `max_tokens: 16384`, `response_format: json_object`, et
  même verrou de sécurité (suppression du champ `"texte"` recopié)

**Choix du moteur** : fenêtre de sélection (`#provider-modal`,
`app.js`) qui s'ouvre au clic sur le bouton "🎭 Voix multiples"
(libellé raccourci le 15/09/2026) — 3
boutons (Gemini mis en avant comme recommandé/défaut depuis le
23/08/2026 — DeepSeek était le défaut avant, Mistral, Gemini). Le choix
voyage via `POST /api/books/{id}/cast?provider=...` jusqu'au bout du
pipeline (chapitre par chapitre + consolidation finale). Défaut serveur
si absent : `gemini`.

**Estimation du coût avant lancement (23/08/2026)** : au clic sur
"🎭 Voix multiples", le frontend appelle
`GET /api/books/{id}/cast/estimate?provider=...` (une requête par moteur)
et affiche le coût estimé sous chaque bouton du `#provider-modal`.
Aucun appel IA : `voice_casting.estimate_cast_cost()` découpe les
chapitres en phrases, compte les appels (Passe 1 : `ceil(phrases /
BATCH_SIZE)` par chapitre, + 1 Passe 2), approxime les tokens
(~4 caractères/token, ~45 chars JSON/phrase en entrée, ~22 tokens de
sortie par phrase) et applique les tarifs de `PROVIDER_PRICES_USD`
(configurable, à ajuster selon les grilles officielles). Le montant
affiché est majoré ×1.5 (`COST_SAFETY_MARGIN`) pour rester prudent.
Ordre de grandeur sur un tome complet de Monte-Cristo (4900 phrases,
52 appels) : ~0,30-0,50 $ selon le moteur.


**Clés API** : `data/config.json` — `gemini_api_key`, `mistral_api_key`,
`deepseek_api_key`, chacune via son propre getter dans `config.py`
(`get_gemini_api_key`, `get_mistral_api_key`, `get_deepseek_api_key`),
même erreur explicite si absente/placeholder. Fichier hors Git.

**Filet anti-phrase-sautée** (indépendant du moteur, dans
`analyze_chapter`) : après la réponse de l'IA, vérifie que chaque id de
phrase envoyée a bien reçu un locuteur ; toute phrase manquante est
comblée automatiquement avec `"narration"` (`confiance: "basse"`,
anomalie tracée) plutôt que de rester sans voix. Rencontré une seule
fois en test (1 phrase sur 462 sautée par DeepSeek sur un chapitre
dense), jamais revu depuis le passage au découpage par paquets de 150
phrases (voir plus haut) — probablement lié à la même cause que la
troncature.

**Script de test isolé** (`test_voix/test_passe1.py`) : accepte le
moteur en argument (`python test_voix/test_passe1.py deepseek`), permet
de tester le prompt sur un seul chapitre sans toucher à un vrai livre
ni consommer le crédit sur un livre entier. Contenu de
`test_voix/chapitre_test.txt` remplaçable à volonté pour varier les cas
de test.

### 🎭 Filtres du casting : âge de la voix et genre du personnage — 21/09/2026

**Demande de Laurent** : « Des boutons juste pour trier les voix par âge pour le
moment : Enfant 👦, Jeune 👨‍🦱, Adulte 🧑‍🦲, Vieux 👴 [...] On filtre selon le
critère sélectionné. Cliquer sur "jeune" n'affiche que les jeunes. Les boutons
qui sont actifs affichent la catégorie. Idéalement un filtre ; Homme / Femme et
les 4 âges. » Et sa question du même jour : « tu peux modifier dans "écouter
voix" également ? » — **oui, sans double travail** : c'est **une seule liste**
(`CRITERES_VOIX`, `main.py`) qui sert les deux fenêtres.

**Troisième barre de filtres, dans la fenêtre du casting** (`#cast-filtre-bar`,
`frontend/index.html`) — la troisième « famille » de filtres, à ne pas confondre
avec les deux autres :

| Barre | Ce qu'elle filtre | Où elle est depuis le 22/09/2026 |
|---|---|---|
| « Voix proposées : » (`#cast-gender-bar`) | les **voix des menus déroulants** | dans le **tiroir des réglages** |
| les pastilles d'état (`#cast-etat-bar`) | les **lignes** (à caster, voix partagée, voix libres) | **en haut de la fenêtre**, sur une ligne qui défile (l'étiquette « Personnages : » a disparu) |
| « Voix des personnages : » (`#cast-filtre-bar`, 21/09/2026) | les **lignes**, par **âge de la voix** (👦 👨‍🦱 🧑‍🦲 👴) et par **genre du personnage** (♀️ ♂️) | dans le **tiroir des réglages** |

*Le détail de ce déménagement (et ses deux causes) est dans la section
« En-tête compact de la fenêtre du casting » plus bas.*

**Où le filtre lit ce qu'il faut** (`frontend/app.js`) :

- l'**âge** vient des **annotations d'écoute de la voix que porte le
  personnage** (`_ageDeLaVoix`, table `_annotationsVoix` : la fenêtre « Écouter
  les voix »). Une voix **jamais annotée** n'a pas d'âge, donc elle **ne passe
  aucun filtre d'âge** : c'est voulu — on cherche ce qu'on a entendu, pas ce
  qu'on ignore ;
- le **genre** vient de la **fiche du personnage** (colonne `genre` : `H` par
  défaut, `F` pour une femme). `M` est accepté comme masculin, parce que les
  **catalogues** de voix écrivent « M » là où les **fiches** écrivent « H »
  (même tolérance que `_symboleGenre`) ;
- `_lignePasseFiltres(row, age, genre)` est **pure** et testée (`test_voix/test_filtre_age_casting.js`),
  comme `_filtrerPersonnages` ;
- le filtre s'applique **après** les deux autres, et il ne touche **pas** aux
  badges ni aux compteurs de voix : ceux-ci restent calculés sur **tout le
  livre** (sinon un badge « partagée avec … » mentirait dès le premier clic) ;
- un **compteur** (`#cast-filtre-resume`) dit ce que la liste montre : « 12
  personnages affichés sur 176 » ;
- les filtres sont **remis à zéro à la fermeture** de la fenêtre, comme la
  recherche : jamais un « jeune » oublié qui ferait croire à des personnages
  disparus.

**« mûr » disparaît des âges** (décision de Laurent : « On garde juste enfant ;
jeune ; adulte ; vieux »). Deux gestes, dans cet ordre :

1. **migration** des **73 voix** annotées « mûr » vers **« adulte »**
   (`data/annotations_voix.json`, copie datée
   `annotations_voix.json.bak_avant_4_ages_20260921_1904`). Sans elle, l'API
   aurait **refusé** d'enregistrer la moindre modification sur ces 73 fiches :
   elle rejette toute valeur hors liste. Âges après migration : **adulte 230,
   jeune 84, vieux 14, enfant 7** ;
2. **retrait de la valeur** de `CRITERES_VOIX` (`main.py`), avec le commentaire
   qui explique la migration — c'est ce qui la fait disparaître des **deux**
   fenêtres (annotation et filtre) en une seule fois.

Dans `modules/voice_casting.py`, les entrées « mur » restantes (timbres, débits)
**ne servent plus** et sont **gardées** telles quelles : elles ne gênent pas, et
elles redeviendraient utiles si la valeur revenait un jour. C'est écrit sur place.

**Vérifications** : `test_voix/test_filtre_age_casting.js` — **30 contrôles**
(l'âge lu sur la voix, une voix sans âge qui ne passe rien, `H`/`M` pour les
hommes, la combinaison des deux filtres, les cas tordus, la barre et son
branchement) ; **36 tests** au vert au total.

### 🎭 En-tête compact de la fenêtre du casting — 22/09/2026

**Demande de Laurent** (21/09/2026 au soir) : « Sur mobile, le menu déroulant pour
choisir les personnages et leurs voix est minuscule. Il faudrait gagner de la
place sur le haut de la modale, par exemple les icones. » Et sur les partages de
voix : « je ne peux pas accéder aux noms qui sont cliquables, parce que souvent
la modale sort de l'écran vers le bas. »

**Les deux causes, mesurées dans le code** :

1. l'en-tête portait **21 contrôles** empilés en sept blocs (2 champs, un
   `datalist`, 15 boutons de filtre, 3 boutons de re-cast), tous en
   `flex-shrink: 0` : ils **refusaient de rétrécir**. La **liste des personnages
   était le seul élément qui pouvait céder** (`flex: 1` avec `min-height: 0`) :
   elle tombait donc à presque rien — et le menu déroulant des voix avec elle ;
2. la hauteur de la fenêtre était en **`80vh`**. `vh` se calcule sur la fenêtre
   du navigateur **sans sa barre d'adresse** : dès que cette barre est visible,
   le bas de la fenêtre passe **sous l'écran**, et rien ne défilait pour
   rattraper ça. C'est exactement là qu'était le détail « partagée avec … », avec
   ses noms cliquables.

**La nouvelle forme** (`frontend/index.html`, `frontend/styles.css`) :

| Élément | Rôle |
|---|---|
| `#cast-modal-header` / `#cast-head-actions` | le titre, puis **trois** commandes : `#cast-search-btn` (recherche), `#cast-filtres-btn` (« Filtres »), `#cast-close-btn` (fermeture) |
| `#cast-search-bar` | le champ de recherche, **caché** au départ (`class="hidden"`) |
| `#cast-etat-bar` / `#cast-etat-actions` | les **quatre pastilles d'état**, sur **une seule ligne qui défile** (`flex-wrap: nowrap` + `overflow-x: auto`) |
| `#cast-info-bar` | les **compteurs**, toujours visibles : `#cast-etat-resume`, `#cast-filtre-resume`, `#cast-libres-info` |
| `#cast-tools` | le **tiroir des réglages** : voix proposées, âge/genre, saga, re-cast. Replié au départ |
| `#cast-list` | la liste des personnages, avec `min-height: 90px` : elle ne peut plus disparaître |

**Pourquoi les compteurs sont sortis du tiroir** : ils expliquent une liste
courte (« 12 personnages affichés sur 176 ») et la disparition de certaines voix
(leur moteur est éteint). Repliés avec les filtres, un filtre resté actif aurait
fait ressembler le livre à une liste amputée, **sans rien pour l'expliquer** — et
sur mobile, aucune infobulle n'est lisible.

**Le tiroir est-il ouvert ?** `_castOutilsDoiventEtreOuverts(choix, largeur)`
(`frontend/app.js`) : tant que Laurent n'y a pas touché (`null`), on suit l'écran
— **replié à 640 px ou moins, ouvert au-delà**, la même limite que les media
queries de `styles.css`. Dès qu'il touche au bouton, **son choix est gardé** dans
`_castOutilsOuverts` et respecté : sans cela le tiroir se refermerait à chaque
clic sur un filtre ou sur une voix, puisque la fenêtre est reconstruite à chaque
fois (`_openCastModal` appelle `_appliquerEnteteCasting`). Le champ de recherche,
lui, se **replie** à la fermeture (`_castRechercheOuverte`) mais reste **ouvert
tant qu'une recherche est en cours** : on ne masque pas ce qui filtre la liste.

**Le bouton « Filtres » s'allume** (`class="actif"`) quand un **filtre de liste**
est actif — âge de la voix ou genre du personnage, `_castFiltreListeActif` — :
tiroir replié, c'est le seul repère qui dit qu'un réglage est en cause.

**La fenêtre ne peut plus sortir de l'écran** : `.cast-box` porte
`max-height: min(80vh, calc(100dvh - 44px))` — les `80vh` sont conservés sur un
ordinateur (où les deux mesures sont égales) et c'est la **hauteur réellement
visible** qui l'emporte sur téléphone ; la ligne `max-height: 80vh;` placée
**avant** sert de repli aux navigateurs qui ne connaissent pas `dvh` (sans elle,
la déclaration invalide laisserait la fenêtre grandir sans limite). Sur mobile
(`max-width: 640px`), les marges se resserrent (`#cast-modal { padding: 10px }`,
`padding: 14px` dans la boîte) et la boîte est bornée à `calc(100dvh - 24px)`.

**Le détail d'un partage** (`_detailPartageVoix`) : les **noms cliquables sont
créés AVANT l'explication** (elle fait 4 à 6 lignes sur un livre réel — une voix
portée par trente personnages — et poussait les noms hors de l'écran), et
**déplier fait défiler** la fenêtre jusqu'au détail (`scrollIntoView`, avec une
garde `typeof` pour le test node, qui n'a pas de défilement).

**Le tiroir ne peut plus être ÉCRASÉ** (22/09/2026 ; bug signalé par Laurent :
« quelque chose empêche l'ouverture de ⚙️ Filtres, sur PC et mobile »). Le
panneau s'ouvrait bien — `aria-expanded` passait à `true`, la classe `hidden`
partait — mais il ne mesurait plus que **5 px de haut sur ordinateur** et **12 px
sur téléphone**, pour un contenu de **427 px** : il était le **seul** élément
autorisé à se réduire (`min-height: 0`) face à une longue liste de personnages
(123 lignes sur « 22/11/63 »). Le bouton semblait donc mort — et sur ordinateur,
le premier appui le **refermait**, puisqu'il part ouvert. Correctif : `#cast-tools`
porte **`min-height: 240px`** et **`max-height: 55vh`**, et ses barres ne se
compriment plus (`#cast-tools > * { flex-shrink: 0 }`) — c'est le tiroir qui
défile. Mesure après correction : **240 px** sur les deux écrans, les filtres
d'âge et de genre **visibles d'emblée**, la liste gardant 202 px (ordinateur) et
338 px (téléphone).
*Garde-fou* : `test_voix/test_filtres_rendu.py` (**12 contrôles**) charge le vrai
bloc du casting et la vraie feuille de styles, avec **120 personnages** — il
échoue (14 px au lieu de 240) dès que la borne disparaît, éprouvé le même jour.
*Leçon écrite* : un **état** juste ne prouve pas qu'on **voit** quelque chose ;
il faut une mesure de RENDU.

**Vérifications** : `test_voix/test_entete_casting.js` — **45 contrôles** (les
trois commandes de l'en-tête, le tiroir et son contenu, la liste après le tiroir,
les compteurs hors du tiroir, les **quatre âges et pas cinq**, les fonctions
pures sur écran étroit ou large, la hauteur en `dvh`, la hauteur minimale de la
liste, les pastilles qui défilent, les noms avant l'explication) ;
`test_voix/test_tiroir_voix_libres.js` **adapté** (la phrase n'est plus le
premier élément du détail) ; **38 tests** au vert au total,
`test_ids_ecran.py` et `test_lire_moi.py` compris.

### 🎧 Fenêtre « Écouter les voix » (le listener) — session du 14/09/2026

Idée de Laurent. Avant, écouter une voix obligeait à passer par la fenêtre du
casting (assigner une voix, lancer un aperçu) : des astuces à répéter, et
impossible de **comparer deux voix à la suite** — or il soupçonnait deux voix
Edge d'être identiques. Un bouton **🎧 Écouter les voix** (sous les réglages
du lecteur) ouvre désormais une fenêtre qui répond à ça.

**Contenu** : **toutes les voix écoutables tout de suite**, groupées par
moteur avec leur nombre (Edge, Kokoro, Piper, Kyutai, XTTS), une **recherche
par prénom**, un **filtre par moteur**, et pour chaque voix :

- un **bouton ▶** qui lit la **phrase de référence**, identique pour toutes
  (indispensable pour comparer honnêtement) :
  *« Le 24 février 1815, la vigie de Notre-Dame de la Garde signala le
  trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples. »* — la même que
  les lots d'écoute du projet (nombres, noms propres, accents, liaisons) ;
- **trois champs de note** : genre (**H**/F), étoiles (0 à 3), remarque libre.
  Une voix déjà annotée est **légèrement mise en valeur** dans la liste.

**Ce qui n'a pas été réinventé** — le listener s'appuie entièrement sur
l'existant :

- `POST /api/tts` (le chemin de la narration) pour produire le son : c'est le
  même mécanisme que l'aperçu de voix du casting
  (`_previewCharacterVoice`), auquel on a simplement donné une vraie phrase ;
- `GET /api/voices`, qui ne renvoie **que les voix dont le moteur est allumé
  et prêt** : aucun bouton ne peut donc échouer, et la liste se met à jour
  toute seule quand un moteur s'allume ou s'éteint ;
- le **cache audio** : une voix déjà écoutée se rejoue **instantanément**.

**Les notes** vont dans `data/annotations_voix.json`, **hors Git** (ce sont
les observations personnelles de Laurent), via `GET`/`POST
/api/annotations_voix`. Règles : une note **entièrement vide est supprimée**
(le catalogue reprend la main), et la convention d'affichage est **H/F**
(celle de l'écoute et du casting) même si le catalogue des voix écrit **M**.

*Pourquoi ce fichier de notes est séparé du catalogue* : Laurent doit pouvoir
annoter **sans risque**. Le catalogue reste la référence du programme, ses
notes sont sa couche personnelle — le report dans le catalogue (étoiles,
genre) reste une **étape volontaire et manuelle** (voir BACKLOG, étape 3).

**Fichiers touchés** : `frontend/index.html` (bouton + fenêtre),
`frontend/app.js` (`_ouvrirEcouteurVoix`, `_rafraichirEcouteurVoix`,
`_construireLigneVoix`, `_ecouterVoix`, `_chargerAnnotationsVoix`,
`_sauverAnnotationVoix`), `frontend/styles.css`, `main.py` (deux routes).

**Vérifications** : `test_voix/test_annotations_voix.py` (12 contrôles — il
**sauvegarde et restaure** les notes de Laurent, pour ne jamais effacer un
travail d'écoute) et `test_voix/test_ids_ecran.py` (21 contrôles : chaque
élément cherché par le code existe bien dans la page — l'erreur la plus facile
à commettre en ajoutant une fenêtre, et la plus pénible à diagnostiquer,
puisqu'un identifiant manquant tue **tout** le script sans message clair).

### Critères FIXES d'annotation (16/09/2026)
Demande de Laurent : au lieu d'écrire une note en texte libre (« grave »,
« cristalline », « nazillarde »…), **on sélectionne dans des listes fermées**.
Motif : une note libre est illisible par la machine ; des annotations calibrées
pourront alimenter plus tard l'**attribution assistée des voix** (voir BACKLOG,
« Attribution des voix assistée »).

Six critères, définis dans `main.py` (**`CRITERES_VOIX`**, seule source de
vérité) : `age` (enfant / jeune / adulte / mûr / vieux), `timbre` (grave /
médium / aigu / rocailleux / cristallin / voilé), `debit` (lent / posé /
normal / vif), `accent` (neutre / paysan / canadien / anglais / allemand /
espagnol / italien / autre), `registre` (noble / neutre / populaire / savant),
`role` (narrateur / enfant / vieux / étranger / secondaire). Le **genre H/F**,
les **étoiles** et la **remarque libre** restent à part : les étoiles restent le
critère de qualité, la remarque garde les nuances que les listes ne couvrent
pas.

`GET /api/annotations_voix/criteres` sert ces listes à la page, qui construit
ses menus avec : le lecteur ne peut donc pas proposer une valeur que le serveur
refuserait. Le `POST` **refuse (400)** toute valeur hors liste — les
annotations restent exploitables par la machine. Une annotation **entièrement
vide** reste supprimée, et une annotation **d'avant** ces critères (14/09) se
relit sans erreur (critères absents = non renseignés). Le fichier
`data/annotations_voix.json` a été **sauvegardé avant** la mise en place
(`.bak_avant_criteres_20260916`).

**Fichiers touchés** : `main.py` (`CRITERES_VOIX`, route `/criteres`, modèle,
validation), `frontend/app.js` (`_chargerCriteresVoix`, `_construireLigneVoix`,
`_sauverAnnotationVoix`, `_majStyleCritere`), `frontend/styles.css`
(`.voice-criteres`).

**Les rubriques sont ÉCRITES devant leurs menus (20/09/2026).** Constat de
Laurent, 19/09/2026 : « une fois une valeur choisie, la ligne affiche "adulte"
ou "aigu" **sans dire de quelle rubrique il s'agit** ». C'est exactement ce que
faisait le code : le nom de la rubrique était porté par l'**option vide** du
menu (`[['', critere.libelle]]`), donc il **disparaissait dès le premier choix**.
Correctif : une **étiquette écrite** devant chaque menu — « Âge [– ] », « Timbre
[grave] » — qui ne dépend jamais du choix en cours, et l'option vide devient un
**tiret** (`–`), comme les menus « genre » et « étoiles ». L'étiquette et son
menu vivent dans le **même petit groupe** (`.voice-critere-champ`), pour qu'un
passage à la ligne sur téléphone ne les sépare jamais.

Deux détails qui comptent :

- les étiquettes sont **courtes** (`_libelleCourtCritere`, fonction **pure** :
  « Âge », « Timbre », « Débit », « Accent », « Registre », « Rôle ») parce que
  six menus doivent tenir sur la ligne d'un téléphone ; le libellé **complet**
  du serveur reste dans l'**infobulle** du menu. Une rubrique **inconnue**
  (ajoutée plus tard côté serveur) retombe sur son libellé complet : jamais
  d'étiquette vide ;
- les libellés de `CRITERES_VOIX` ont reçu leurs **accents** au passage
  (« Âge perçu », « Débit », « Rôle réservé » — c'étaient des chaînes sans
  accent, visibles en infobulle). **Seuls les libellés changent** : les clés
  techniques (`age`, `timbre`, `debit`, `accent`, `registre`, `role`) et les
  valeurs restent identiques, donc **aucune annotation n'est perdue**.

*Fichiers* : `frontend/app.js` (`_libelleCourtCritere`,
`_LIBELLES_COURTS_CRITERES`, `_construireLigneVoix`), `frontend/styles.css`
(`.voice-critere-champ`, `.voice-critere-label`), `main.py` (libellés).
*Vérifications* : `test_voix/test_criteres_voix.js` (les étiquettes exactes dans
l'ordre du serveur, l'étiquette et son menu **dans le même groupe**, le tiret de
l'état vide, et une **rubrique inconnue** qui affiche son libellé complet) et
`test_voix/test_ids_ecran.py` (l'étiquette produite, le groupe, le style).
**Reste ouvert** : l'écran « par thème » lui-même (BACKLOG).

**Vérifications** : `test_voix/test_annotations_voix.py` (**29 contrôles** :
listes annoncées, enregistrement, refus des valeurs inconnues, annotation
remise à zéro, annotation ancienne, redémarrage) et
`test_voix/test_criteres_voix.js` (**25 contrôles**, sans navigateur) : ce
dernier **lit les critères dans `main.py`** et vérifie que la page construit
exactement ces menus et envoie exactement ces clés — une valeur ajoutée d'un
côté sans l'autre fait échouer le test.

### Attribution des voix par critères (16/09/2026)
Suite directe des annotations d'écoute : le **re-cast gratuit** (bouton
« Re-caster », `POST /api/books/{id}/cast/reassign`) ne se contente plus des
paliers d'étoiles — il **classe les voix selon les annotations de Laurent**.

Classement d'une voix pour un personnage (`_classement_voix`) : **âge** (une
voix « vieux » pour un personnage âgé, une voix « jeune » pour un jeune), puis
**timbre** attendu (grave pour les hommes âgés, cristallin/aigu pour les jeunes
femmes…), puis **étoiles**, puis **débit** ; l'identifiant départage les ex
æquo, ce qui rend le résultat **déterministe et testable**.

Règles appliquées :
- les voix notées **0 étoile** sont écartées ;
- une voix dont le **rôle** est annoté est **réservée** (narrateur, étranger,
  secondaire → hors pool automatique, comme les voix de rôle NIMM) ; « vieux »
  et « enfant » restent utilisables quand l'âge du personnage correspond ;
- **verrous** (case « garder ») et **voix figées de saga** restent
  prioritaires : ils sont passés en `voix_figees`, comme au casting, et
  comptent comme voix déjà prises ;
- les **petits rôles** (< 8 répliques) gardent une voix vide (lus par le
  narrateur) : seuls les grands rôles consomment une voix dédiée ;
- si le pool du genre est épuisé, on reprend la mieux classée et on **décale la
  hauteur** (même mécanisme que l'ancien tri).

**Ignorés volontairement** : le **registre** (137 voix « neutre » pour 1
« noble ») et l'**accent paysan** (0 voix) — trop peu renseignés pour classer.
À revoir quand ces critères seront mieux annotés, ou déduits par l'IA (voir
BACKLOG, « Étape 2 — bouton Re-caster avec l'IA »).

**Correction trouvée en chemin** : l'ancien re-cast forçait l'âge **« adulte »
en dur** pour tous les personnages ; il relit désormais la table `cast_fiche`,
sans quoi un classement par âge n'aurait rien pu faire.

**Repli** : `?par_criteres=false` sur la route redonne **exactement** l'ancien
tri par paliers — pratique pour comparer les deux sur un même livre.

**Aperçu avant application** : `test_voix/_apercu_recaste_criteres.py <book_id>`
montre, personnage par personnage, l'ancienne et la nouvelle voix (avec leurs
critères) **sans rien écrire**. Sur « Le Chevalier Errant » : **30 voix
changeraient sur 59**, et les incohérences disparaissent (Eustace Osgris, âgé,
passe sur *Victor — vieux/grave/lent* ; l'Œuf, jeune, quitte une voix grave
d'ancien).

**Fichiers touchés** : `modules/voice_casting.py` (`lire_annotations_voix`,
`_index_voix`, `_voix_reservee`, `_classement_voix`, `AGES_PAR_PERSONNAGE`,
`TIMBRES_ATTENDUS`, `DEBITS_ATTENDUS`, `assign_voices(..., par_criteres=True)`)
et `main.py` (`reassign_voices`).

**Vérifications** : `test_voix/test_attribution_criteres.py` (**27 contrôles**,
sans écriture en base : classement, rôles réservés, profils types, verrous,
déterminisme, repli, relecture de `cast_fiche`, cohérence de saga).

**Complément du 16/09/2026 — la cohérence de SAGA au re-cast.** Trouvé en
préparant le re-cast de la saga Monte-Cristo : `_fetch_saga_voix_figees()` (qui
reprend les voix des **autres tomes**, le plus ancien ajouté faisant référence)
n'était appelée que par le **casting complet** (`start_casting`). Le **re-cast
gratuit** ne reprenait que les **verrous du livre courant** : re-caster le tome 4
aurait donc donné à Monte-Cristo, Danglars ou Villefort une voix **différente**
de celle de leur tome 2 — alors que la cohérence entre tomes est protégée depuis
le 22/08/2026. `reassign_voices` reprend désormais ces voix, exactement comme le
casting complet ; les **verrous locaux restent prioritaires** (fusion en
`setdefault` : un verrou du livre re-casté n'est jamais écrasé). À savoir :
la fiche de saga est lue **avant** la fermeture de la connexion, avec la même
requête que le casting.

**Ce que le re-cast ne sait PAS faire (constat du même jour)** : deviner qu'un
personnage est **étranger**. L'attribution ne connaît que le **genre**, l'**âge**
et les **annotations d'écoute** ; `cast_fiche` n'a aucun champ de nationalité ou
d'accent. C'est pourquoi les voix dont le **rôle = étranger** sont annotées :
elles sortent du pool automatique et restent à assigner **à la main**. Pistes
étudiées (voir BACKLOG) : reléguer les voix accentuées en fin de classement, ou
laisser l'IA déduire l'accent du texte (étape 2 « Re-caster avec l'IA »).

---

## 🎙️ Les voix : les pools et les notes d'écoute

### Voix du narrateur : par livre, sans héritage entre livres (20/09/2026)

**Aujourd'hui — l'état actuel en clair** (vérifié contre le code le 22/09/2026) :
- la voix du narrateur appartient au **livre** : colonne `books.narrator_voice`,
  écrite par `PUT /api/books/{book_id}/narrator` ;
- côté page : `_restaurerVoixNarrateur()`, la constante
  `NARRATEUR_VOIX_DEFAUT = 'fr-CH-ArianeNeural'`, et la ligne d'état
  `#narrateur-etat` sous les menus — elle **dit** quand la voix enregistrée n'est
  pas disponible, sans rien écraser ;
- le **re-cast ignore** `narrator_voice` ; le menu de vitesse du bas est celui du
  **narrateur** (un personnage sans réglage lit à `PERSONNAGE_RATE_DEFAUT`) ;
- *vérifications* : `test_voix/test_narrateur_par_livre.js` (**24 contrôles**,
  avec le vrai code de `app.js` et un faux DOM) et `test_voix/test_ids_ecran.py`.

*Ce qui suit raconte la session du 20/09/2026 : les deux défauts trouvés, et
comment ils ont été corrigés.*

La voix du narrateur appartenait déjà au **livre** (`books.narrator_voice`,
17/09/2026) — mais **deux trous dans la chaîne** la faisaient « passer » d'un livre
à l'autre. Constat de Laurent : « la voix narrateur passe d'un livre à l'autre […]
En gros, chaque livre devrait avoir son narrateur, pas un même narrateur qui passe
de livre en livre. » Mesure du 20/09/2026 sur la base (**lecture seule**) :
**10 livres sur 14 n'avaient AUCUNE valeur** dans `narrator_voice`.

- **Défaut 1 — le livre sans valeur gardait la voix du précédent.** À l'ouverture
  d'un livre sans valeur, `_restaurerVoixNarrateur()` sortait immédiatement
  (`if (!sel || !voix …) return;`) : le menu `#voice-select` gardait la voix du
  livre d'avant, et **rien n'était écrit** pour le livre ouvert. *Corrigé* : le
  livre reçoit la voix **par défaut** (`NARRATEUR_VOIX_DEFAUT =
  'fr-CH-ArianeNeural'`) **et cette valeur est enregistrée** (`PUT
  /api/books/{id}/narrator`) → chacun a SA voix, et elle le suit d'un appareil à
  l'autre. L'appel de restauration est passé **après** `_currentBookId = bookId`
  dans `openBook()` : sans cela, l'écriture visait le livre précédent.
- **Défaut 2 — la voix indisponible était remplacée en silence.** Si la voix
  enregistrée n'est pas proposée (moteur éteint), le code se contentait d'un
  `console.warn` **invisible** et la lecture repartait avec la voix de l'autre
  livre. *Corrigé* : on lit au **défaut**, on **le dit** dans une ligne dédiée
  sous les menus (`#narrateur-etat`), et on **n'écrase rien** — ni en mémoire ni en
  base — pour que **SA** voix revienne dès que le moteur est rallumé.
- **Ce qui n'a pas changé** : le re-cast ignore toujours `narrator_voice` ; un
  changement de voix ne s'applique qu'au prochain chargement de chapitre ; le menu
  reste la source de vérité pour la lecture (les badges du casting suivent le
  menu, et la valeur enregistrée sert de secours quand le menu est vide).
- **Vérification** : nouveau test **`test_voix/test_narrateur_par_livre.js`**
  (**24 contrôles**, `node test_voix/test_narrateur_par_livre.js`) — il exécute le
  **vrai** code extrait de `app.js`, avec un faux DOM et un faux `fetch` (jamais
  une copie du code : renommé, le test échoue bruyamment). Les **10 autres tests
  JS** de l'atelier passent aussi, ainsi que `test_voix/test_ids_ecran.py` et
  `test_voix/test_lire_moi.py`.
- **Cache-busting** : `?v=` monté à **20260920-1** dans `frontend/index.html`
  (`app.js` *et* `styles.css` modifiés — règle de session).
- **Sauvegardes** avant modification, en
  `.bak_avant_narrateur_par_livre_20260920` : `data/nimm_epub.db`,
  `frontend/app.js`, `frontend/index.html`, `ARCHITECTURE.md`.

### 🔊 Banque de voix (session du 08/09/2026 — pool élargi aux Kokoro)
Le pool d'attribution automatique était limité aux voix Edge TTS françaises
(et à quelques voix Piper). Depuis la session du 08/09/2026, les pools
dédiés (`DEDICATED_VOICES_F/M` dans `voice_casting.py`) incluent **toutes
les voix Kokoro**, triées par note décroissante : comme les personnages
sont traités du plus présent au moins présent, les voix les mieux notées
partent aux rôles principaux et les timbres exotiques restent en réserve
pour les très nombreux rôles. La vraie solution à long terme pour des
timbres encore plus variés reste le clonage vocal (Coqui XTTS-v2 ou
équivalents), noté plus bas dans le backlog — et le cache audio (livré le
08/09/2026) est le socle qui rendra cette piste utilisable.

### 🔼 Règle des paliers d'étoiles — session du 15/09/2026
(décision de Laurent ;
elle remplace l'ordre du 14/09/2026). Le pool automatique du casting ne se
parcourt plus par moteur mais par **paliers d'étoiles** : palier **3 étoiles**
d'abord, puis **2**, puis **1** ; et dans chaque palier, les moteurs se suivent
toujours dans le même ordre — **Edge, puis XTTS v2, puis Kokoro**. Autrement
dit : 3★ Edge → 3★ XTTS → 3★ Kokoro → 2★ Edge → 2★ XTTS → 2★ Kokoro, etc.
Une voix notée **0 étoile** est **écartée** des deux pools, sur les trois
moteurs (elle reste choisissable à la main) : c'est ainsi qu'on « retire une
voix du casting automatique ». Conséquence visible chez Laurent : Henri et
Denise restent en tête (3★ Edge), Rémy suit, et **Antoine, Jean et Fabrice
(0★ à l'écoute) sortent** du pool. *Fichier* : `modules/voice_casting.py`
(`_EDGE_POOL_F/M`, `_EDGE_STARS`, `_notes()`, `_edge_pool()`,
`_pool_par_paliers()`, `definir_voix_edge()`, `_recalculer_pools()` ; les
anciennes `_kokoro_pool()` et `_xtts_pool()` sont intégrées dans
`_pool_par_paliers()`, `_kyutai_pool()` est conservée mais plus appelée).
*Vérification* : `test_voix/test_pool_casting.py` (ordre des paliers, 0★
écartées sur les trois moteurs, Kyutai absent, seuil des petits rôles identique
côté client et côté serveur).

**Notes des voix Edge : une seule liste** (15/09/2026). Les étoiles des voix
Edge vivent dans `FRENCH_VOICES` (`main.py`) et **nulle part ailleurs** :
`main.py` les transmet une fois au démarrage par
`voice_casting.definir_voix_edge(FRENCH_VOICES)`, qui recompose aussitôt les
deux pools. Les valeurs de repli de `voice_casting._EDGE_STARS` ne servent
qu'aux appels qui ne passent pas par `main.py` (tests).

### Symboles ♀️ / ♂️ de genre devant les prénoms — session du 20/09/2026.
Demande de Laurent, 19/09/2026 : « on laisse le prénom, mais on ajoutera les
symboles, ça sera plus simple à l'œil ». Trois emplacements, dans l'ordre
d'utilité :

1. **La ligne de personnage** (fenêtre du casting) : « ♀️ Femme · 33 répliques »
   — le symbole **devant**, puis le mot, qui reste pour l'instant (l'usage dira
   s'il devient inutile sur un casting de 175 personnages) ;
2. **La barre de filtre « Voix proposées »** : « ♀️ Femmes » / « ♂️ Hommes »
   (`#cast-gender-actions`) ;
3. **Le libellé d'une voix**, dans tous les menus et toutes les listes
   (`_libelleVoix`) : « ♀️ Eva 🇩🇪 Allemagne (NIMM Voix) … — Kokoro ». C'est le
   point que Laurent a explicitement demandé (« devant les prénoms ») : il est
   **redondant** dans les menus du casting (déjà groupés « Femmes » / « Hommes »)
   mais il est le SEUL repère dans la fenêtre « 🎧 Écouter les voix », rangée par
   **moteur**, et dans le tiroir des voix libres. On le garde partout pour que le
   même prénom se lise de la même façon dans toute l'application.

Les symboles viennent d'**une seule fonction pure**, `_symboleGenre(genre)`
(`frontend/app.js`), qui accepte **les deux conventions** du projet : `F`/`M`
pour les **catalogues de voix**, `F`/`H` pour les **fiches de personnage**
(colonne `genre` de la table `voices`, défaut `H`). Deux pièges signalés
d'avance au BACKLOG, tous les deux évités :

- les symboles portent leur **sélecteur emoji** (`\u2640\uFE0F`, `\u2642\uFE0F`) :
  sans lui, ils s'affichent en petit noir et blanc selon les claviers ;
- un **genre inconnu** n'écrit **ni signe ni mot**. L'ancien code faisait
  `v.genre === 'F' ? 'Femme' : 'Homme'`, donc annonçait « Homme » pour **tout**
  ce qui n'était pas `F` — un genre **faux** dès que la fiche était vide. La
  ligne affiche alors simplement « 33 répliques ».

*Fichiers* : `frontend/app.js` (`_symboleGenre`, `_libelleVoix`, ligne de
personnage de `_openCastModal`), `frontend/index.html` (`#cast-gender-actions`).
*Vérifications* : `test_voix/test_libelle_voix.js` (libellés exacts, `H` accepté,
genre vide **sans** symbole, et **deux points de code** vérifiés pour le
sélecteur emoji) et `test_voix/test_ids_ecran.py` (les symboles dans les deux
fichiers, les deux boutons, et l'absence de l'ancien repli sur « Homme »).

**Icônes des moteurs de voix — session du 20/09/2026.** Demande de Laurent :
« trouver des icônes pour les moteurs, histoire d'avoir un visuel sur les
moteurs plutôt que les noms ». Une **seule table** porte l'information
(`FAMILLES_VOIX`, `frontend/app.js`) : `['kokoro', 'Kokoro', '🎎']`. Deux
fonctions **pures** en dérivent : `_iconeFamille(cle)` et
`_libelleFamilleIcone(cle)` (icône + nom, ou le nom seul si l'icône manque).

| Moteur | Icône | Pourquoi |
|---|---|---|
| Edge | ☁️ | le seul moteur **en ligne** |
| Kokoro | 🎎 | modèle **japonais** |
| Piper | 🎶 | le **joueur de flûte** |
| Kyutai | ⚡ | moteur **local** rapide |
| XTTS v2 | 🧬 | moteur de **clonage** |
| NeuTTS | 🧪 | le plus **récent** |

Où chaque forme sert :

- le **libellé d'une voix** (`_libelleVoix`) montre l'icône **SEULE** :
  « ♀️ Eva 🇫🇷🇩🇪 adulte médium — 🎎 ». C'est **là** que le nom gênait : les menus
  du casting sont étroits (45 % de la ligne du personnage), et « — Kokoro » y
  prenait la place du prénom, de l'âge et du timbre ;
- **partout où il y a la place**, le nom reste, précédé de son icône : la ligne
  d'une voix dans « 🎧 Écouter les voix » (`_construireLigneVoix`), les en-têtes
  de groupe du tiroir des voix libres (`_afficherVoixLibres`), la ligne
  d'information sur les moteurs éteints, le menu de **filtre** des moteurs
  (`#voices-famille`), la fenêtre de choix du moteur (cartes `provider-btn`) et
  le **bouton des moteurs** (`_libelleMoteur`).

Aucune marque ni logo sous licence : des repères **distincts** et **changeables
en une ligne**. Deux garde-fous : `_libelleMoteur` et la ligne d'information
gardent un **`typeof`** (leur test node les isole, sans la table des icônes — le
nom s'écrit alors sans icône, jamais un tiret orphelin), et un moteur **inconnu**
n'affiche aucune icône. **Corrigé au passage** : le menu de filtre des moteurs
**n'avait pas l'option NeuTTS**, alors que ses voix sont proposées par
`/api/voices` — on ne pouvait donc pas les isoler.

**Le saut de ligne dans un libellé de menu : impossible — et mesuré
(22/09/2026).** Laurent a demandé s'il était possible de **forcer** un saut de
ligne dans le libellé d'une voix, pour lire « prénom, drapeaux, âge et timbre »
sur la première ligne et « moteur, porteur de la voix / LIBRE » sur la seconde.
La réponse est **non** : un libellé qui porte un saut de ligne occupe
**exactement la même hauteur** qu'un autre — le navigateur **aplatit** le saut,
**même** avec `white-space: pre-line` sur les options (la règle s'applique bien à
l'option, la hauteur ne bouge pas). Mesure :
`test_voix/test_libelle_deux_lignes_rendu.py`. Il ne reste que le repli
**automatique** d'un libellé trop long, et il est **subi** : on ne choisit pas où
il tombe. Le `\n` et la règle CSS ont donc été **retirés le jour même**, avec une
trace écrite dans `app.js` (`_libelleVoix`) et `styles.css` — pour que l'essai ne
soit pas refait. Une seconde ligne **choisie** demande une **liste de
l'application** (de vrais éléments de page, comme le tiroir des voix libres), pas
un `<select>` : c'est l'un des deux chemins laissés au choix de Laurent (BACKLOG,
priorité 2).

*Fichiers* : `frontend/app.js` (`FAMILLES_VOIX`, `_iconeFamille`,
`_libelleFamilleIcone`, `_libelleVoix`, `_libelleMoteur`, `_construireLigneVoix`,
`_afficherVoixLibres`, `_majInfoVoixLibres`), `frontend/index.html`
(`#voices-famille`, cartes `provider-btn`). *Vérifications* :
`test_voix/test_libelle_voix.js` (libellés exacts avec l'icône),
`test_voix/test_tiroir_voix_libres.js` (en-têtes « 🎎 Kokoro · 1 »),
`test_voix/test_bouton_moteur.js` (le nom reste écrit) et
`test_voix/test_ids_ecran.py` (les 6 icônes, l'icône seule dans le libellé,
NeuTTS filtrable).

**« 🔖 Onglets » remis à la même échelle (20/09/2026).** Constat de Laurent : le
bouton des onglets n'était **pas** dans la règle de style commune
(`#multivoice-btn, #voices-open-btn`) — il gardait l'apparence native du
navigateur (plus grand, fond plus clair) à côté de « 🎭 Voix multiples » et
« 🎧 Écouter les voix ». Les trois partagent désormais la **même règle**
(`frontend/styles.css`). *Leçon à garder* : **tout nouveau bouton de la barre du
lecteur doit être ajouté à cette règle** — le bouton « vider le cache audio »
(voir BACKLOG) est le prochain concerné. *Vérification* :
`test_voix/test_ids_ecran.py` (la règle commune porte bien les trois boutons).

**🧹 Bouton « Vider le cache audio » (20/09/2026).** Le cache se purge déjà tout
seul (quota de **2 Go**, et `VERSION_CACHE` dès que le texte envoyé au moteur
change), mais Laurent n'avait **aucun moyen de le forcer** — et c'est exactement
ce qui manque quand on doute d'un rendu (le 18/09/2026, il a fallu vider le
dossier à la main pour écarter cette piste). Deux routes et un bouton :

- **Serveur** : `GET /api/cache_audio` → `{octets, quota_octets, fichiers,
  version}` (`tts_cache.stats()`, **lecture seule**) et `POST /api/cache_audio/
  vider` → `{ok, fichiers_supprimes, octets_liberes}` (`tts_cache.purger()`).
  **Sans danger pour les données** : le cache ne contient que de l'audio **déjà
  synthétisé**, régénérable à l'identique (la synthèse est déterministe). Seule
  conséquence : la première écoute d'un passage déjà lu redemandera le calcul au
  moteur. Une **écriture en cours** (`.tmp`) n'est **jamais coupée** ;
- **Écran** : le bouton **« 🧹 Vider le cache (604 Mo) »** est dans la barre du
  lecteur, **à la même échelle et dans le même style** que « 🎭 Voix multiples »,
  « 🎧 Écouter les voix », « 🔖 Onglets » et « 👀 Lecture Rapide » (précision de
  Laurent : c'est la leçon du jour — tout nouveau bouton de cette barre rejoint
  la règle de style commune). Le libellé est composé par `_libelleBoutonCache()`
  (« 604 Mo », « 1,2 Go », « 12 Ko », **virgule française**), il **n'affiche
  jamais « undefined »** quand le serveur n'a pas encore répondu, et la purge
  demande **confirmation** en annonçant ce qui sera libéré.

*Fichiers* : `modules/tts_cache.py` (`stats`, `purger`), `main.py` (les deux
routes), `frontend/index.html` (`#cache-open-btn`), `frontend/app.js`
(`_formatOctets`, `_libelleBoutonCache`, `_chargerEtatCache`,
`_viderCacheAudio`), `frontend/styles.css` (la règle partagée).
*Vérifications* : **nouveau** `test_voix/test_cache_audio.py` (le compte et la
purge dans un **dossier temporaire** — il compare même le nombre de fichiers du
**vrai** cache avant/après pour prouver qu'il n'y a pas touché, et vérifie qu'un
`.tmp` survit à la purge) et **nouveau** `test_voix/test_cache_audio.js` (le
libellé : tailles lisibles, jamais « undefined ») ; `test_voix/test_ids_ecran.py`
(le bouton, les deux routes, la règle de style partagée).

### Noms des voix : jamais d'identifiant technique dans les menus
(15/09/2026, constat de Laurent après un re-cast d'un roman contemporain). La fenêtre
du casting affichait « `xtts:cml9804` » là où elle devait écrire
« **Alphonse** ». Cause exacte : `/api/voices` ne contient les voix XTTS (et
Kyutai) que si **leur moteur est prêt** — décision du 14/09/2026 — et cette
liste peut dater d'avant l'allumage du moteur ; le menu retombait alors sur
l'identifiant brut. Trois correctifs :

1. **Nouvelle route `/api/voix_catalogue`** : toutes les voix (Edge, Kokoro,
   Piper, Kyutai, XTTS), moteurs éteints compris, chacune avec `famille` et
   `dispo`. Elle ne sert **jamais à proposer** une voix — c'est le rôle de
   `/api/voices` — mais à la **nommer** ;
2. **Rafraîchissement à l'ouverture** : `_openCastModal(true)` recharge la
   liste des voix proposées **et** le catalogue (`loadVoices()` +
   `loadCatalogueVoix()`) ; un moteur allumé après le chargement de la page est
   donc vu tout de suite, et ses voix redeviennent **choisissables** ;
3. **Libellé** : le groupe d'avertissement d'un personnage affiche le prénom
   du catalogue — « ⚠️ Alphonse (M) — 🇫🇷 France (XTTS) — XTTS v2 éteint » — et
   l'identifiant brut n'apparaît plus que si la voix est **vraiment** absente
   du catalogue (voix retirée, livre casté avec un autre catalogue).

*Fichiers* : `main.py` (route), `frontend/app.js` (`_catalogueVoix`,
`loadCatalogueVoix`, `_libelleCatalogue`, `_lignesVoixPersonnage` — qui remplace
`_construireMenuVoix` depuis le 22/09/2026 —,
`_openCastModal(rafraichirVoix)`). *Vérifications* :
`test_voix/test_libelles_voix.py` (catalogue complet, « Alphonse » pour
`xtts:cml9804`, `dispo` comparé à `/api/moteurs`, et contrôle sur un vrai livre
casté — les 125 personnages d'un roman contemporain ont tous un nom au catalogue) et
`test_voix/test_filtre_genre.js` (cas 7 et 8 : prénom affiché, identifiant
absent).

**« Partager / Déplacer » — livré le 19/09/2026.** Choisir pour un personnage une
voix qu'un **autre** porte ouvre la modale `#partage-modal` : elle nomme la voix
et ses porteurs, **annonce la hauteur** qui serait appliquée, et propose
**Partager** (les autres gardent la voix, le personnage reçoit une hauteur
décalée automatiquement — `_pitchPartageLibre`, jamais une hauteur déjà prise,
par pas de 4 Hz — écrite dans son curseur) ou **Déplacer** (les autres repassent
« ⚠ à caster » avec la voix générique de leur genre ; un personnage 🔒 n'est
**jamais** déplacé). Annuler (bouton, ✕, tap à côté ou Échap) remet le menu comme
avant. **Reste ouvert** : le **clic pour attribuer** une voix libre depuis le
tiroir des voix libres.


**Ordre du pool automatique — session du 14/09/2026** (décision de Laurent, à
l'arrivée de XTTS v2 ; **remplacé depuis par la règle des paliers d'étoiles du
15/09/2026, décrite ci-dessus**). L'ordre était alors : **Henri et Denise**
(Edge, `_EDGE_PRIMARY_F/M`) → **60 voix XTTS v2** (`_xtts_pool()`, dont 25
notées à l'écoute par Laurent le 14/09/2026) → **Kokoro** (`_kokoro_pool()`,
inchangé) → **autres voix Edge** en réserve (`_EDGE_RESERVE_F/M` : Charline,
Sylvie, Rémy, Gérard, Antoine, Jean). **Kyutai était retiré du pool
automatique** (`_kyutai_pool()` conservée mais non appelée ; les voix Kyutai
restent choisissables à la main) ; l'item de BACKLOG porte le détail.
Garde-fous inchangés : la voix XTTS **écartée à l'écoute** (`stars: 0`) est
exclue du pool ; les **petits rôles** (moins de `MINOR_THRESHOLD` = 8
répliques) reçoivent une voix générique **Piper** (`piper:siwis:0` /
`piper:tom:0`). ⚠️ **Remplacé le 21/09/2026** : ce sont désormais **Jessica /
Pierre** (`piper:upmc:0` / `piper:upmc:1`) — voir « Les petits rôles : une voix
par genre » plus bas.

### Ordre du pool automatique (session du 12/09/2026 — Kyutai en tête)
Décision de Laurent : les **35 voix Kyutai** (timbres français natifs,
étiquetées à l'écoute) passent **en premier** dans le pool automatique,
**avant** les voix Edge éprouvées et les voix Kokoro (timbres à accent
étranger). Ordre obtenu : `_kyutai_pool()` → `_EDGE_DEDICATED_F/M` →
`_kokoro_pool()`, chacun trié par note décroissante. Concrètement, sur un
nouveau casting, les rôles principaux (8 répliques ou plus) reçoivent
d'abord une voix Kyutai, toutes différentes. Deux garde-fous :

- la voix Kyutai **écartée à l'écoute** (`stars: 0`, la n° 33) est exclue
  du pool, comme les voix Piper écartées ;
- les **petits rôles** (moins de `MINOR_THRESHOLD` = 8 répliques) gardent la
  voix générique Edge — ils ne consomment donc jamais une voix Kyutai, ni la
  voix du narrateur (point soulevé par Laurent ; la distribution fine des
  petits rôles reste à voir).

À savoir : ces voix exigent le moteur Kyutai allumé pour être écoutées
(`DEMARRER_KYUTAI.bat`). Un livre casté automatiquement avec elles demande
donc le moteur — sinon le lecteur affiche le message clair prévu. Les
**accents étrangers** restent volontairement hors du pool : ils s'assignent
à la main (voix Kokoro, ou voix étrangères en essai).

### 🎨 NIMM Voix — fournisseur de voix externes (session du 11/09/2026)

NIMM Voix est un projet séparé (dossier <atelier NIMM Voix>\) qui fabrique des voix
Kokoro supplémentaires par mélange de timbres. Il produit un fichier
voix_generees/voices-nimm.bin qui contient les 54 voix officielles de Kokoro
+ 24 voix créées (78 au total), au même format que voices-v1.0.bin (NpzFile
numpy, tenseur (510, 1, 256) par voix).

Intégration prévue dans NIMM ePub : instancier Kokoro avec
voices-nimm.bin au lieu de voices-v1.0.bin (le modèle ONNX kokoro-v1.0.onnx
reste inchangé : c'est le fichier de voix qui est échangé à l'instanciation).
Les 78 voix deviennent immédiatement
appelables par leur nom (les 54 officielles inchangées + les 24 nouvelles :
ff_romane, ff_sarah, fm_antoine, etc.), sans aucune modification du code
frontend — la structure GET /api/voices les affichera automatiquement dans
les menus déroulants.

Détail technique : la banque est compatible bit-à-bit avec voices-v1.0.bin
(même format). Kokoro-onnx accepte soit un nom de voix, soit directement un
tenseur numpy. Les voix ajoutées sont donc indiscernables des voix
officielles du point de vue du moteur.

Objectif à terme : enrichir la banque en continu pour élargir le pool du
casting automatique (aujourd'hui limité à ~32 F + ~30 M, il pourrait
atteindre 50+ par genre), et partager la banque avec d'autres utilisateurs de
Kokoro (licence Apache-2.0).

Intégration minimale : côté modules/tts.py, il suffit de changer le chemin du
fichier de voix au moment d'instancier Kokoro(...). Aucune autre modification
n'est nécessaire — le reste du pipeline (routage par préfixe kokoro:, menu
déroulant du casting, GET /api/voices) fonctionne tel quel.

**🎚️ Ajouter des voix Kokoro au lecteur — la procédure réelle (20/09/2026).**
Faute d'avoir échangé le fichier de voix, une autre route a été suivie : les
timbres fabriqués dans NIMM Voix sont **fusionnés dans `voices-v1.0.bin`**, le
fichier de référence du lecteur — **54 voix officielles + 30 voix NIMM**
(12/09/2026), puis **+ 10 voix à accent allemand** (20/09/2026) → **94 voix**.
`KOKORO_VOICES` (`modules/tts.py`) reste la **liste** de ces voix (id, nom,
région, genre, étoiles) : un timbre présent dans le fichier mais absent de la
liste est chargé mais **jamais proposé** — et l'inverse (une ligne sans timbre)
donne une voix qui **échoue à la lecture**. Les deux vont donc **toujours
ensemble**.

1. **Le timbre** — `python test_voix/_importer_voix_kokoro.py --quoi <mot>
   --ecrire` ajoute les voix **manquantes** d'un fichier source (défaut : la
   banque à accent allemand de NIMM Voix) dans `voices-v1.0.bin`. **Aperçu par
   défaut** ; `--ecrire` **copie d'abord** la cible en
   `.bak_avant_<mot>_<date>` (ce fichier est la référence de **toutes** les
   voix : sans copie, une erreur d'écriture les emporterait toutes), refuse
   tout **nom déjà pris**, vérifie la forme `(510, 1, 256)` en `float32` et un
   timbre **non vide**, puis **relit le fichier écrit** : empreinte md5 **voix
   par voix** pour prouver qu'**aucune voix d'avant n'a changé**, compte exact,
   et relecture des voix ajoutées **par leur nom** — exactement ce que fait le
   moteur (`np.load` puis `voices[nom]`, `kokoro_onnx/__init__.py`) ;
2. **La liste** — une ligne par voix dans `KOKORO_VOICES` (`modules/tts.py`),
   **sur une seule ligne** : les outils de taggage lisent le catalogue **ligne
   par ligne** (`_appliquer_annotations_voix.py`, `_rapprocher_neutts_xtts.py`).
   Convention de nom : `<pays><genre>_<prénom>` — ici **`fa_`** = français à
   accent **allemand** (`df_`/`dm_` = allemand, comme `ff_`/`fm_` = français) —
   et région **« 🇩🇪 Allemagne (NIMM Voix) »**, pour les retrouver d'un coup
   d'œil dans les menus.

*Décision du 20/09/2026 : les voix importées entrent à **0 étoile**.* Dans la
« règle des paliers » (`voice_casting.py`), une voix notée 0 est **écartée du
casting automatique mais reste choisissable à la main** : les 10 voix
allemandes ne peuvent donc pas se glisser toutes seules dans un livre français.
Ce sont les **notes d'écoute de Laurent** (fenêtre « 🎧 Écouter les voix »),
reportées par `_appliquer_annotations_voix.py`, qui les font entrer dans le
pool — comme toutes les autres voix.

*Vérifications du 20/09/2026* : `_importer_voix_kokoro.py` (aperçu puis
écriture : « aucune voix existante n'a changé » sur les **84** voix d'avant,
**94** au total) ; **nouveau** `test_voix/_tester_voix_kokoro_importees.py` —
fait **parler le moteur par le vrai chemin du lecteur** (`modules/tts.py`) et
mesure ce qui sort : **10/10 voix**, 2,28 à 2,71 s d'audio, crête **-4,0 à
-5,7 dBFS** (jamais du silence) ; `test_voix/test_pool_casting.py` (le pool
automatique est **inchangé** : 0 étoile) et `test_voix/test_voix_ecoutables.py`
(**110 voix proposées** par `/api/voices`) ; `_appliquer_annotations_voix.py`
en **aperçu** (les lignes allemandes sont bien lues par le taggage).
*Pour écouter* : `START.bat`, fenêtre « 🎧 Écouter les voix », filtre
**Kokoro** — les 10 voix portent le drapeau 🇩🇪.

### 🎚️ Nouvel ordre du pool automatique de casting — session du 14/09/2026

Décisions de Laurent à l'arrivée de XTTS v2 dans le pool automatique
(`modules/voice_casting.py`, `assign_voices`) :

- **Henri et Denise** (Edge) en tête du pool (`_EDGE_PRIMARY_F/M`) ;
- puis les **60 voix XTTS v2** (`_xtts_pool`), triées par étoiles
  décroissantes — mêmes étoiles provisoires que Kyutai ;
- puis **Kokoro** (`_kokoro_pool`, inchangé) ;
- puis les **autres voix Edge** en réserve tout à la fin
  (`_EDGE_RESERVE_F/M` : Charline, Sylvie, Rémy, Gérard, Antoine, Jean) —
  déplacées de la 2ᵉ position à la dernière ;
- **Kyutai retiré du pool automatique** pour l'instant (reste choisissable
  à la main, rien n'est supprimé du catalogue).

**Personnages secondaires** (moins de `MINOR_THRESHOLD` = 8 répliques) :
`GENERIC_VOICE_F/M` passe d'Éloise/Fabrice (Edge) à **Siwis/Tom** (Piper) —
Piper reste hors du pool automatique principal, mais sert désormais cette
voix générique partagée. *(Changement **remplacé le 21/09/2026** : **Jessica /
Pierre**, voir « Les petits rôles : une voix par genre ».)*

Aucun livre déjà casté n'est affecté : `assign_voices` ne s'applique qu'aux
nouveaux castings (les voix déjà enregistrées ne sont jamais réécrites).

---

## 🗣️ Les moteurs de voix

### 🗣️ Intégration Kokoro TTS — accents forcés par personnage (livré, session du 21/08/2026)
**Idée validée avec Laurent, implémentée le soir même :** Kokoro (déjà
en place et apprécié dans l'autre projet NIMM de Laurent) comme moteur
TTS alternatif pour certains personnages, en forçant volontairement le
frontend texte→phonétique français sur une voix au timbre étranger —
donne un accent naturel sans recourir au clonage vocal. Usage concret
validé : Maître Pastrini et Luigi Vampa (Comte de Monte-Cristo) avec un
accent italien (`im_nicola`).

**Mécanique exacte** — tout tient dans un seul paramètre forcé en dur,
quel que soit le timbre choisi (`modules/tts.py`,
`synthesize_kokoro`) :
```python
samples, sr = kokoro.create(texte, voice=voice_id, speed=1.0, lang="fr-fr")
```
`voice=` choisit le timbre/locuteur, `lang="fr-fr"` force la
prononciation française quel que soit ce timbre — c'est ce qui produit
l'accent tout en gardant une prononciation française compréhensible
(testé et confirmé, pas de charabia).

**Catalogue implémenté : 54 voix**, regroupées par pays d'origine du
timbre avec drapeau emoji dans `region` (🇺🇸 Etats-Unis ×20, 🇬🇧
Royaume-Uni ×8, 🇨🇳 Chine ×8, 🇯🇵 Japon ×5, 🇮🇳 Inde ×4, 🇪🇸 Espagne ×3,
🇵🇹 Portugal/Brésil ×3, 🇮🇹 Italie ×2, 🇫🇷 France ×1). Chaque id est
préfixé `kokoro:` (ex: `kokoro:im_nicola`) pour permettre le routage.
Liste des 54 identifiants vérifiée empiriquement via
`Kokoro(...).get_voices()` sur la machine de Laurent avant intégration
— aucun id inventé.

**Routage par préfixe, transparent pour le frontend** :
- `GET /api/voices` renvoie `FRENCH_VOICES + KOKORO_VOICES` (66 entrées
  au total) — narrateur et fenêtre du casting affichent les deux
  catalogues sans aucun changement de code frontend, juste plus
  d'options dans les mêmes menus déroulants existants.
- `POST /api/tts` : si `voice` commence par `kokoro:` → `synthesize_kokoro`
  (sortie WAV) ; sinon comportement Edge TTS inchangé (sortie MP3).

**Chargement** : modèles (`kokoro-v1.0.onnx` ~325 Mo,
`voices-v1.0.bin` ~28 Mo) copiés à la racine du projet depuis
l'installation NIMM existante de Laurent (pas de re-téléchargement).
Chargement paresseux dans un thread daemon au démarrage du serveur
(`ensure_kokoro_loaded()`, appelé dans `lifespan()`) — ne bloque jamais
Edge TTS pendant le chargement (quelques secondes). **Exclus de Git**
(`.gitignore`) : ~350 Mo à eux deux, à recopier manuellement d'une
machine à l'autre si besoin.

**Limite connue** : Kokoro n'a pas de paramètre de pitch (contrairement
à Edge TTS) — le réglage de pitch envisagé pour la fenêtre du casting
(backlog, voir plus bas) ne pourra s'appliquer qu'aux voix Edge TTS,
pas aux voix Kokoro.

### 🗣️ Prononciation française imposée — Kokoro et Piper (21/09/2026)

**Le défaut, tel que Laurent l'a entendu** : « quand Kokoro prononce un prénom,
genre Andréa, j'entends `[énAndréa fe]` — il invente des syllabes. » Cause établie
le 20/09/2026 à l'atelier NIMM Voix (mesure et verdict d'oreille dans son
`ARCHITECTURE.md`) : pour `lang=fr-fr`, Kokoro **n'a pas** de phonémiseur
français, il appelle **espeak-ng**, un moteur **multi-langues**. Quand un mot est
reconnu dans le dictionnaire **anglais**, espeak-ng **change de langue** et
**marque la frontière** : `(en)ˈandɹiə(fr)`. Le tokenizer de **kokoro-onnx**
garde ces caractères (ils sont dans son vocabulaire) → le moteur **prononce la
marque** : « én » … « fe ».

**Deux conséquences à ne pas confondre** : la marque lue à voix haute est un
défaut **en plus** du mauvais son ; même quand elle est retirée, le mot reste
**prononcé à l'anglaise** — c'est le cas de **Piper**, qui la retire
(`Marthe` → *marth*, `Nathan` → *néythane*).

**Ce qui a été livré, en deux mécanismes** :

| Mécanisme | Où | Ce qu'il corrige |
|---|---|---|
| **les phonèmes au moteur** : on phonémise nous-mêmes, on retire les marques de langue (`MARQUE_LANGUE`, motif **volontairement étroit** — `(en)`, `(fr)`, `(en-us)`… : un motif large mangerait ce qu'il y a entre deux parenthèses du texte), puis `create(..., is_phonemes=True)` | `modules/tts.py`, `_phonemes_kokoro` | les syllabes inventées, **partout** — même sur les mots que la table ne connaît pas |
| **la table de prononciation** : le mot est réécrit dans la version **PARLÉE seule**, jamais dans le texte affiché (même patron que les abréviations et les majuscules) | `modules/prononciation.py`, appelé par Kokoro **et** Piper | le **son** : `Andrea → Andréa`, `Marthe → Marte`, `Arthur → Artur`, `Nathan → Natan` (validés à l'oreille le 20/09), plus cinq propositions en attente de verdict |

**Trois garde-fous, appris des pièges déjà payés** :

1. la table ne touche que des **mots entiers** : « Andreas » et « dosages » ne
   sont pas touchés par les entrées « andrea » et « dos » ;
2. un mot **tout en majuscules** est ramené en casse de titre, jamais laissé en
   capitales : espeak-ng **épelle** les mots en capitales ;
3. la **clé du cache porte sur le texte transformé** : changer la table ne peut
   donc pas resservir un ancien audio. `VERSION_CACHE` passe quand même à **15**,
   car le changement des phonèmes, lui, n'apparaît pas dans le texte.

**Mesure** (`test_voix/sortie_ecoute_prononciation/mesure_phonemes.txt`) : les
neuf mots passent d'un son **anglais marqué** à un son **français** —
`andrea : (en)ˈandɹiə(fr)` → `ɑ̃dʁeˈa`, `dos : (en)dˈɒs(fr)` → `dˈoː`,
`maëlys : (en)mˈaɛliz(fr)` → `maelˈi`. Et dans le lot, la phrase qui contient
tous les mots **maigrit de 35 %** (368 Ko → 238 Ko) : c'est le temps des syllabes
en trop qui disparaît.

**Vérifications** : `test_voix/test_prononciation_kokoro.py` — **31 contrôles**,
dont un **garde-fou de la table** : chaque graphie doit cesser de basculer en
anglais **et** son mot d'origine doit basculer, sinon l'entrée ne sert à rien et
le test le signale (règle : on n'ajoute une entrée **qu'après l'avoir mesurée**).
Le phonémiseur seul est utilisé : le modèle de 300 Mo n'est **pas** chargé, donc
le test tourne en une seconde.

**Ce qui reste** : le **verdict d'oreille** de Laurent sur les cinq entrées
proposées (`test_voix/ECOUTER_PRONONCIATION.bat`, lot A/B avec la vraie voix
Kokoro), puis l'**étape 2** : un scanner qui parcourt un livre et propose les mots
à corriger (il existe côté NIMM Voix).

### 🎙️ Voix « écoutables » selon le moteur allumé — session du 14/09/2026

Demande de Laurent : les menus ne doivent proposer que des voix qu'on peut
écouter **tout de suite**. Avant, les 35 voix Kyutai étaient listées en
permanence : on pouvait en choisir une, moteur éteint, et ne le découvrir
qu'en plein chapitre (erreur 503 claire, mais au mauvais moment). Le problème
allait **doubler** avec l'arrivée d'XTTS v2, puisque les deux moteurs lourds
**ne tournent jamais ensemble** (une seule carte graphique).

**Ce qui décide de la disponibilité.** Les moteurs **légers** n'ont aucun
service à allumer → leurs voix sont toujours proposées (Edge en ligne, Kokoro
et Piper sur processeur). Les moteurs **lourds** doivent être **allumés ET
prêts** — Kyutai sur le port 8082, XTTS v2 sur 8083 : leur `/sante` renvoie
`pret: false` pendant le chargement du modèle (10 à 12 s pour Kyutai), et
c'est seulement une fois prêt que le moteur sait vraiment parler.

**Côté serveur (`main.py`)** :
- `MOTEURS_VOIX` : table des moteurs lourds (`kyutai`, `xtts`) avec leur nom
  lisible (affiché à l'écran), l'URL de leur `/sante`, et — depuis le
  15/09/2026 — leur **dossier, leur lanceur et les motifs de leur ligne de
  commande** (voir « Changer de moteur » plus bas) ;
- `_sante_moteur(url)` → `{actif, pret}` : `actif` = le service répond,
  `pret` = le modèle est chargé ;
- `etat_moteurs_voix(force=False)` : état des deux moteurs, **gardé 5 s en
  mémoire** — les menus ne doivent pas interroger les services à chaque
  affichage, et un moteur éteint fait attendre 1 s avant d'abandonner ;
- `GET /api/voices` : renvoie `FRENCH_VOICES + KOKORO_VOICES + PIPER_VOICES`
  toujours, et `+ KYUTAI_VOICES` **seulement** si
  `_moteur_voix_pret(etat, "kyutai")` — les voix XTTS suivront le même modèle
  quand le service existera ;
- `GET /api/moteurs` (nouvelle route) : renvoie l'état des moteurs, pour le
  voyant affiché à l'écran.

**Côté écran (`frontend/app.js`, `index.html`, `styles.css`)** :
- `loadMoteurs()` charge `/api/moteurs` **avant** de construire un menu de
  voix (le moteur a pu être éteint ou démarré depuis l'affichage de la page),
  avec la même mémoire de 5 s côté navigateur ;
- **voyant** `#reparer-open-btn` sous les réglages du lecteur : « ⚠️ Pocket TTS
  éteint — appuyer pour réparer » / « ⏳ … : chargement en cours… » /
  « 🛠️ Moteurs de voix : … en marche ». Il ne parle **que des moteurs
  ATTENDUS** (`attendu`, calculé par le serveur : Pocket TTS, qui cohabite, et
  le moteur lourd retenu dans `data/moteur_voix.txt`) — sinon il crierait en
  permanence pour XTTS éteint **volontairement**. Depuis le **21/09/2026** il
  ouvre le panneau « Réparer les moteurs de voix » : il ne CHANGE plus de moteur
  (voir « 🛠️ Réparer les moteurs de voix » plus bas) ;
- dans la fenêtre du casting, `_lignesVoixPersonnage()` distingue désormais
  **trois** cas au lieu de deux : la voix est proposée normalement ; la voix
  appartient à un moteur **non prêt** → groupe « ⚠️ Pas de voix (Kyutai
  eteint) » ou « (Kyutai en chargement) » ; la voix a réellement **disparu**
  du catalogue → « ⚠️ Voix introuvable ». Dans tous les cas la voix
  enregistrée **reste sélectionnée** : jamais de substitution silencieuse ;
- `_openCastModal()` est devenue `async` (rafraîchissement de l'état avant
  l'affichage) — de ce fait, `test_voix/test_filtre_genre.js` a été adapté :
  son repère de fin de tranche recule d'un éventuel `async `, et échoue
  toujours bruyamment si la fonction est renommée ou déplacée.

**Décision de Laurent (14/09/2026, option A)** : les voix indisponibles
**disparaissent** des menus, et un personnage qui en portait une affiche
**« Pas de voix »**, à corriger **à la main** dans la fenêtre du casting —
aucun remplacement automatique.

**Ce qui n'est PAS touché, volontairement** : la voix enregistrée d'un
personnage n'est jamais modifiée ni effacée. Un chapitre **déjà écouté** se
réécoute donc même moteur éteint (le cache disque répond avant tout appel au
moteur), et un choix de voix fait à l'oreille n'est jamais écrasé en douce.

**Reste à faire** (voir BACKLOG) : le **pool automatique** suit désormais les
paliers d'étoiles (Edge, puis XTTS v2, puis Kokoro) et **XTTS v2 est installé
ici** (service séparé, port 8083, voir `MEMO_XTTS_v2_pour_Cline.md`) ; le
**bouton de bascule** entre les deux moteurs est livré (voir ci-dessous). En
revanche, rien ne **remplace en silence** la voix d'un personnage.

**Vérifications livrées** : `test_voix/test_voix_ecoutables.py` (12 contrôles
côté serveur, sans navigateur) et `test_voix/test_voix_ecoutables.js`
(13 contrôles sur les menus, avec un faux DOM et l'état des moteurs réel de
`/api/moteurs`). Contrôle de bout en bout effectué le 14/09/2026, moteur
éteint : `/api/moteurs` → les deux moteurs « eteint », `/api/voices` → 100 voix
dont **0 Kyutai**, Ariane (narrateur) toujours proposée.

### 🎛️ Changer de moteur de voix : un seul à la fois — session du 15/09/2026

**Aujourd'hui — l'état actuel en clair** (vérifié contre le code le 22/09/2026) :
- **Edge, Kokoro et Piper** vivent dans le lecteur (toujours disponibles) ;
  les **quatre moteurs « lourds »** tournent dans leur propre service HTTP
  local : Kyutai **8082**, XTTS v2 **8083**, NeuTTS **8084**, Pocket TTS **8085** ;
- **un seul moteur lourd allumé à la fois** : `POST /api/moteur/basculer` éteint
  l'autre **avant** d'allumer le nouveau, et note le choix dans
  `data/moteur_voix.txt` (lu par `START.bat` au démarrage suivant) ;
- `GET /api/moteurs` dit l'état des quatre (`actif`, `pret`, `nom`) ;
  `POST /api/moteurs/relancer` est le bouton **« Relancer les moteurs »** ;
  `_moteur_voix_pret()` répond à « ce moteur est-il utilisable ? » ;
- un **veilleur** (`_veiller_moteurs()`) passe toutes les 30 secondes — c'est lui
  qui rallume un moteur tombé, **sauf** si l'arrêt était volontaire ;
- *vérifications* : `test_voix/test_bascule_moteur.py` et
  `test_voix/test_start_moteur.py`.

> **REMPLACÉ À L'ÉCRAN le 21/09/2026.** Ce bouton n'existe plus dans la page :
> Laurent l'a retiré après avoir éteint un moteur **par erreur**, d'un simple
> clic, et vu les 18 voix Pocket TTS disparaître du casting (voir
> « 🛠️ Réparer les moteurs de voix » ci-dessous). La **règle** décrite ici et la
> **route** `POST /api/moteur/basculer` restent vraies et en service : elles sont
> simplement appelées autrement — par le panneau « Réparer », qui ne sait que
> **rallumer**, et par les lanceurs des moteurs, sur le PC.

Demande de Laurent : « un bouton sur le message qui est aujourd'hui en bas de la
fenêtre, qui ferait office de switch sur un moteur ou l'autre ». Raison
technique : les deux moteurs lourds occupent chacun environ 3,8 Go de carte
graphique (**7,6 Go sur 8** mesurés le 15/09/2026 quand les deux tournaient
ensemble). Le bouton répond aussi au constat du même jour — **le mauvais moteur
s'était lancé tout seul** au démarrage.

**Ce que fait le bouton** (il remplace le voyant, au même endroit) :
1. il affiche l'état — « Voix de personnages : XTTS v2 pret — changer »,
   « ⏳ … : chargement en cours… », « … moteur eteint — en allumer un » ;
2. au clic, trois choix : **XTTS v2**, **Kyutai**, **Aucun moteur** ;
3. pendant le chargement (10 à 20 s), il se rafraîchit **tout seul** toutes les
   3 s jusqu'à « pret », puis les voix du moteur apparaissent dans les menus.
   Si une écoute est en cours, la fenêtre prévient qu'elle sera arrêtée.

**Côté serveur — `POST /api/moteur/basculer`** (`basculer_moteur_voix()`) :
1. **éteint l'autre moteur** s'il tourne, et **attend** que son port soit fermé
   (`_attendre_extinction`, 20 s au maximum) avant d'aller plus loin ;
2. **allume** celui qui est demandé (`_relancer_moteur_voix` : même dossier,
   même lanceur et même titre de fenêtre que `START.bat`) ; un moteur **déjà
   prêt** ou **en cours de chargement** n'est **pas relancé** ;
3. **note le choix** dans `data/moteur_voix.txt` — c'est ce fichier que
   `START.bat` relit au prochain démarrage ;
4. renvoie l'**état frais** (sans la mémoire de 5 s), pour que le bouton se
   mette à jour immédiatement.

**Les refus, volontairement bruyants** (le bouton affiche le message) : un
moteur **non installé** (`_moteur_voix_installe`, même contrôle que `START.bat`)
n'est pas lancé ; et si l'**autre refuse de s'éteindre**, **rien n'est allumé**
et le choix n'est pas noté — on ne prend jamais le risque des deux moteurs
ensemble.

**Pilotage des processus** : `_pids_moteur_voix()`, `_arreter_moteur_voix()` et
`_relancer_moteur_voix()` ont remplacé les trois fonctions qui ne connaissaient
que Kyutai — celles-ci restent, sous forme d'enveloppes, pour l'analyse locale
en repli. On **cible la ligne de commande** (`servir_xtts` / `DEMARRER_XTTS`,
`servir_kyutai` / `DEMARRER_KYUTAI`) : jamais un python au hasard, et la fenêtre
du moteur est fermée avec ses enfants (`taskkill /F /T`).

**Garde-fou au démarrage (`START.bat`)** : chaque moteur est testé **avant**
d'être lancé (port **8085** pour Pocket TTS, **8082** pour Kyutai) : s'il tourne
déjà, rien n'est lancé et la fenêtre le dit. **Depuis le 21/09/2026, Pocket TTS
est testé et lancé AVANT le choix du moteur lourd** : son bloc vivait après les
`goto lecteur` de Kyutai et n'était donc **jamais atteint** — c'est la panne du
matin (voir « 🛠️ Réparer les moteurs de voix », plus bas). Le test
`test_voix/test_start_moteur.py` vérifie désormais que le port **8085 est testé
avant le 8082**, et qu'aucun `goto lecteur` ne saute ce bloc.

**Vérifications livrées** : `test_voix/test_bascule_moteur.py` (50 contrôles,
**sans rien lancer** — les deux moteurs sont simulés en mémoire et le fichier de
réglage est redirigé vers un témoin, remis en place à la fin) et
`test_voix/test_bouton_moteur.js` (31 contrôles : libellé extrait du **vrai**
`app.js`, présence du voyant et de la fenêtre dans `index.html`, branchements —
**réécrit le 21/09/2026** pour le voyant « Réparer », voir plus bas).

### 🛠️ Réparer les moteurs de voix, et un moteur qui ne se perd plus — 21/09/2026

**Ce qui a déclenché le chantier.** Laurent, après une écoute de 6 h : « j'ai
cliqué par erreur sur la ligne tout en bas, qui me permet de changer de
serveur, apparemment ça a coupé le moteur POCKET TTS. Je ne trouve plus les
voix à l'intérieur du casting. » Deux constats, tirés de l'état réel de la
machine :

1. le clic n'avait **rien cassé** (`data/moteur_voix.txt` contenait bien
   `kyutai`) ;
2. **`START.bat` n'a jamais allumé Pocket TTS** : son bloc était **après** le
   bloc Kyutai, dont **tous** les chemins se terminent par `goto lecteur`. Il
   était donc **inatteignable**. Le PC avait redémarré à **05:53**, et à
   **09:46** `START.bat` a lancé Kyutai puis sauté Pocket (les processus portent
   ces heures).

**Pourquoi c'est grave, et pas seulement désagréable** : la page ne propose que
les voix **écoutables tout de suite** (`/api/voices`). Moteur éteint, ses
18 voix **disparaissent des menus** — donc **aucune demande** ne peut plus
partir vers lui : un « rallumage à la demande » est **impossible par
construction**. C'est cette impasse que le chantier ferme.

**Les quatre pièces livrées** :

| Pièce | Ce qu'elle fait |
|---|---|
| `START.bat` | le bloc **Pocket TTS passe AVANT le choix du moteur lourd** (label `:pocket_pret`) : il démarre à chaque lancement, sans fenêtre. Le commentaire explique le piège, pour qu'il ne revienne pas |
| le **veilleur** (`main.py`, `_veiller_moteurs`) | un fil de fond, lancé avec le lecteur : toutes les 30 s il regarde Pocket TTS et le **rallume** s'il est éteint (modèle chargé en **1,7 s** mesurés, et ce moteur tourne sur le **processeur**). Garde-fous : repos de 60 s entre deux essais, 10 min après 6 échecs, message clair dans la console |
| le **voyant « 🛠️ Réparer »** | remplace le bouton de bascule. Il ne parle que des moteurs **attendus** et ouvre un panneau à deux gestes |
| l'**endormissement à 3 h** | `NIMM_POCKET_TTS_INACTIF` passe de 30 min à **180** : à 30 min, le moteur s'endormait **en pleine journée d'écoute** |

**Le panneau « Réparer » — deux gestes, aucun ne peut éteindre :**

1. **🛠️ Relancer les moteurs** → `POST /api/moteurs/relancer` : rallume Pocket
   TTS (`_assurer_pocket_vivant`, lancé **sans fenêtre**, sortie redirigée vers
   ses journaux) **et** le moteur lourd **retenu** s'il est éteint (via
   `basculer_moteur_voix`, donc toujours **un seul** moteur lourd). La lecture
   en cours **n'est pas coupée** ;
2. **🔄 Redémarrer NIMM ePub** → `POST /api/serveur/redemarrer` : lance
   `START.bat` **comme un double-clic**, après confirmation. Le serveur
   **répond d'abord**, et `START.bat` part **1,5 s plus tard**
   (`_lancer_start_bat_apres_reponse`) : sinon le garde-fou de `START.bat` tue
   le serveur avant qu'il ait envoyé sa réponse. La page affiche un **voile de
   redémarrage** (`#redemarrage-voile`), puis **se recharge toute seule** dès
   que le serveur répond (toutes les 2 s, 90 s au maximum, avec un message clair
   si ça ne revient pas).

**Pourquoi ce geste manquait vraiment** : le lanceur du PC
(`G:\NIMM_LAUNCHER`) **refuse** de relancer quand le port est occupé (« NIMM
ePub est déjà en marche : rien à lancer »). Or le cas où l'on a besoin de
relancer est justement celui où le lecteur tourne… mais mal.

**« Attendu », la notion qui fait taire le voyant à bon escient**
(`moteurs_attendus()`) : sont attendus **Pocket TTS** (il cohabite) et le
**moteur lourd retenu** (`data/moteur_voix.txt`). XTTS ou NeuTTS éteints **par
choix** ne font donc plus crier le voyant — un voyant qui crie en permanence ne
dit plus rien. `/api/moteurs` renvoie désormais `cohabite` et `attendu` pour
chaque moteur, et `_moteur_lourd_retenu()` tolère un **BOM** en tête du fichier
(piège PowerShell).

**Deux pièges d'atelier corrigés au passage** (`test_start_moteur.py`) :

- sa « copie neutre » de `START.bat` **tuait le lecteur en marche** : le
  garde-fou du 18/09/2026 (« on arrête le serveur qui écoute sur 8081 ») n'était
  pas neutralisé. Deux motifs de remplacement ne matchaient plus rien (ils
  dataient de l'époque NeuTTS) : le test **lançait aussi le lanceur de Kyutai**
  pour de vrai, sept fois. Il neutralise maintenant **tout** et **vérifie**
  (section « 2 bis ») qu'aucun lancement ne reste possible ;
- **un nom court ne suffit plus pour lancer un `.bat`** : depuis Python 3.11,
  les processus enfants reçoivent `NoDefaultCurrentDirectoryInExePath=1`, donc
  `cmd /c _test.bat` échoue là où le **chemin complet** fonctionne.

**Le geste fort, testé pour de vrai — et deux défauts trouvés là** :

1. **Le nom court ne se résout plus dans un `cmd` lancé par le lecteur.** Le
   bouton ouvrait une fenêtre qui disait « `START.bat` n'est pas reconnu », et
   le lecteur n'était **jamais** relancé (même cause que ci-dessus, héritée par
   l'enfant). Corrigé **aux deux endroits** — `_lancer_start_bat_apres_reponse`
   **et** `_relancer_moteur_voix` (défaut latent depuis le 15/09/2026) : le
   lanceur est appelé par son **chemin complet**, avec `CREATE_NEW_CONSOLE`,
   soit le double-clic exact. *Vérifié* : lecteur relancé, **PID changé**
   (12876 → 11380), Pocket TTS intact.
2. **Un `.bat` écrit en LF seul fait dérailler cmd.** Une copie de diagnostic
   écrite par Python (donc en LF, parce que `read_text()` convertit les CRLF en
   LF) a été lue « de travers » par cmd : il a **exécuté le texte de ses propres
   commentaires**, jusqu'à lancer `neutts_service\DEMARRER_NEUTTS.bat` — donc le
   moteur **NeuTTS**, que personne n'avait demandé (il a même écrit `neutts`
   dans `data/moteur_voix.txt`, remis à la main ensuite). **Règle** : un `.bat`
   s'écrit **toujours en CRLF** ; `START.bat` est sain (178 lignes CRLF,
   vérifié).

**Vérifications** : `test_voix/test_reparer_moteurs.py` (**30 contrôles**, rien
à lancer : `START.bat`, « attendu », veilleur, commande de lancement, routes,
réglages) ; `test_voix/test_bouton_moteur.js` réécrit (voyant, disparition de
l'ancien dispositif, câblage des deux gestes) ; `test_voix/test_start_moteur.py`
remis au goût du jour (il décrivait encore la règle NeuTTS du 16/09/2026).
**Contrôle en vrai** : `START.bat` relancé → port **8085** ouvert, `pocket
actif=true pret=true attendu=true`, `/api/voices` → **163 voix dont 18 Pocket
TTS** ; puis le **geste fort** joué depuis la page → nouveau lecteur, moteurs
intacts.

### 🎙️ Moteur XTTS v2 installé comme service séparé — session du 14/09/2026

Deuxième moteur lourd de NIMM ePub, après Kyutai : **XTTS v2** (clonage de
voix, 17 langues dont le français). Il est installé **à côté** du lecteur,
comme l'exige la règle du projet — Python 3.12 + PyTorch ne peuvent pas
cohabiter avec le lecteur (3.14). Le mémo de l'atelier
(`MEMO_XTTS_v2_pour_Cline.md`) décrit la préparation ; cette section décrit ce
qui a été livré ici.

**Ce qui a été ajouté** — dossier `xtts_service/`, calqué sur
`kyutai_service/` :

| Fichier | Rôle |
|---|---|
| `servir_xtts.py` | le service HTTP : `GET /sante`, `GET /voix`, `POST /tts`, `POST /recharger` — une génération à la fois, gardien de fenêtre, refus de deux moteurs |
| `INSTALLER_XTTS.bat` | installation en 5 étapes : venv Python 3.12, pip, PyTorch 2.8 CUDA 12.8, coqui-tts, voix + modèle |
| `DEMARRER_XTTS.bat` | allume le moteur seul (et note `xtts` dans `data\moteur_voix.txt`, pour que `START.bat` le rallume ensuite) |
| `_telecharger.py` | copie les 35 extraits de voix (repli : banque Hugging Face) et fait charger le modèle |
| `_verifier_installation.py` | contrôle l'environnement **sans rien lancer** |
| `tester_service.py` | écoute de contrôle (3 phrases × N voix ; `--longue` teste le découpage) |
| `LIRE_MOI.md`, `ATTRIBUTION.md`, `requirements.txt`, `pyrightconfig.json` | documentation, licences, paquets |

**Réglages** : port **8083** (`NIMM_XTTS_PORT`), écoute locale
(`NIMM_XTTS_HOST`), langue lue (`NIMM_XTTS_LANGUE`, `fr`).

**Découpage du texte, dans le service** : XTTS refuse **plus de 273
caractères en français** (il le dit lui-même et **tronque l'audio**). Le
service découpe donc tout seul, selon la logique validée à l'oreille à
l'atelier : ponctuation forte ; recollage des fragments qui commencent par une
minuscule ; recollage après les abréviations courantes ; redécoupage au-delà
de **250 caractères** en préférant les virgules (ces morceaux se recollent
**sans silence**) ; et un silence de **0,35 s uniquement entre deux vraies
phrases**.
**Nettoyage de la ponctuation de dialogue, dans le service** (session du
15/09/2026). Contrairement à Edge, Kokoro et Piper, **XTTS ne sait pas
ignorer** la ponctuation de dialogue : il essaie de la prononcer. L'écoute
comparative de Laurent (`xtts_service/_ecouter_guillemets.py`, 9 fichiers,
voix Bertrand — verdict conservé dans
`xtts_service/sortie_ecoute_guillemets/avant_remede/verdict_laurent.txt`) a
établi :

- avec les **guillemets** `« »`, le moteur **prononce** des sons parasites
  (« ogui … haa », « iogué … yo »), et la phrase de référence passe de
  **3,4 s à 4,9 s** ;
- avec un **tiret cadratin en tête de réplique**, il **répète le premier mot**
  (« vous **êteêtes** sûr de vous ») — défaut **invisible aux mesures**
  (durée inchangée : 3,3 s contre 3,4 s), seule l'oreille l'a attrapé ;
- **remplacer** les guillemets par une virgule (intonations très marquées) ou
  par une espace (la voix part dans les aigus) **déforme la lecture** : on
  **retire**, on ne remplace pas.

D'où `nettoyer_pour_xtts()` dans `servir_xtts.py`, appliqué dans
`_lire_un_morceau()` — **le seul endroit où le texte part au moteur** :
guillemets retirés, tiret cadratin **en tête** retiré, tiret d'**incise**
remplacé par une virgule (la respiration reste). Les **tirets d'union**
(« demanda-t-il »), les apostrophes et les points de suspension ne sont **pas**
touchés, et un test le verrouille (`test_voix/test_nettoyage_xtts.py`).

*Deux conséquences* : le texte envoyé change, donc **la clé du cache audio** du
lecteur aussi (les phrases déjà lues gardent l'ancien rendu jusqu'à purge de
`data/tts_cache/`) ; et le nettoyage est **propre à XTTS** — les trois autres
moteurs reçoivent la phrase telle quelle.

*Et à la sortie du moteur* (15/09/2026) : le WAV produit passe par
`rogner_queue()`, qui ramène le **silence de queue** à `SILENCE_QUEUE_S`
(0,25 s, la même marge qu'Edge) au lieu des 0,54 à 0,91 s laissés par le
moteur — voir « Rognage des silences de bord » plus haut.

*Défauts résiduels notés au BACKLOG* (à traiter séparément) : une pause de 3 s
et un souffle final sur un dialogue à ponctuation interne (segments très
courts), et un petit accroc sur « monsieur » en fin de phrase.

### Extraits de voix libres de droits pour XTTS — chantier du 15/09/2026
XTTS v2 est un moteur de **clonage** : il ne parle qu'avec la voix d'un extrait
de référence. En plus des **60 voix CML-TTS** déjà installées, Laurent fabrique
ses propres extraits à partir d'enregistrements du **domaine public**, qu'il
nettoie dans **Audacity** et dépose en **MP3** dans `Extraits de voix\` (dossier
**ignoré par Git**, comme tout l'audio).

*Chaîne de préparation*, reprise de l'atelier NIMM Voix
(`G:\NIMM Voix\outils\xtts_tts\_preparer_reference.py`) :
1. conversion en **WAV mono 24 000 Hz 16 bits** (format natif du moteur) ;
2. **rognage des silences de bord** (ffmpeg `silenceremove` à -45 dB, marge
   conservée 0,10 s) ;
3. dépôt dans `xtts_service\voix_fr\` sous `<identifiant>_enhanced.wav` (le
   suffixe `_enhanced` est la version que le service retient).

*Repères de durée* : **10 à 20 s** (idéal) ; **6 s = minimum** ; au-delà de
**30 s** le moteur tronque et n'utilise rien de plus (config du modèle :
`max_ref_len = 30`, `gpt_cond_len = 30`). Les bords doivent être **propres**
(silences courts) : la référence est rejouée à chaque phrase.

*Outils du projet* :
- `xtts_service/_preparer_extraits.py` — conversion + mesures (durée, silence de
  tête, silence de queue) + verdict ; **refuse d'écraser** une voix en place ;
  `--verser` écrit dans la banque **et recharge le moteur à chaud**
  (`POST /recharger`, sans redémarrage) ;
- `xtts_service/_ecouter_extraits_dp.py` — **lot d'écoute** comparatif : pour
  chaque voix, `..._reference.wav` (l'extrait entendu par le moteur) puis
  `..._clone.wav` (le même passage lu par le clone), avec `index_ecoute.txt` et
  `ECOUTER_LE_LOT.cmd`.

*Ce qu'il reste à faire pour qu'une voix soit utilisable dans le lecteur* : une
entrée dans **`XTTS_VOICES`** (`modules/tts.py`) — cette même liste alimente les
**menus** *et* le **pool du casting automatique** — puis un **redémarrage** du
lecteur (la liste est lue au démarrage). État du chantier, prénoms attribués et
réserve de prénoms : voir le BACKLOG (« Voix XTTS créées à partir d'extraits
libres de droits »).





**Mesures relevées le 14/09/2026** (RTX 4060, machine de Laurent) :

| Mesure | Valeur |
|---|---|
| Modèle chargé en | **9,9 s** |
| Sortie | WAV mono **24 000 Hz** |
| Vitesse | **≈ ×3 plus RAPIDE que le temps réel** (10,8 s d'audio calculés en 4,1 s). Confirmé le 15/09/2026 : **×3,3** (8,3 s de calcul pour 27,4 s d'audio, 3 phrases ; ×2,4 sous 50 caractères, ×3,4 au-delà). Autrement dit **1 h d'audio ≈ 18 min de calcul** |
| Voix disponibles | **35** (les extraits CML-TTS déjà utilisés par Kyutai) |
| Découpage vérifié | texte de 325 caractères → 2 morceaux (209 + 115), relecture **identique** |
| Disque | `.venv` et ses dépendances : **7,7 Go** (PyTorch 2.8 CUDA) |

**Les deux pièges, à ne jamais rouvrir** (chacun coûte une demi-journée) :
PyTorch **2.8** et pas plus récent — à partir de 2.9, `coqui-tts` réclame
`torchcodec`, qui réclame les DLL FFmpeg « partagées » absentes de cette
machine (« Could not load libtorchcodec ») ; et `transformers` **borné à la
branche 4.x** — `coqui-tts` 0.27.5 l'exige sans borne haute, or transformers
5.x a supprimé `isin_mps_friendly`, ce qui fait échouer l'import de `TTS`.

**Licence** : le modèle `coqui/XTTS-v2` est sous « Coqui Public Model
License » — **usage non commercial, valable aussi pour l'audio produit**.
L'usage de Laurent (écoute personnelle, essai) est couvert ; l'audio XTTS
**n'entre pas** dans une banque diffusée (détail :
`xtts_service/ATTRIBUTION.md`). Les 35 extraits de voix, eux, sont en
**CC BY 4.0** (attribution Kyutai + CML-TTS).

**Branché dans le lecteur — session du 14/09/2026 (suite)** : catalogue
`XTTS_VOICES` (35 voix, mêmes identifiants que `KYUTAI_VOICES`, région
« 🇫🇷 France (XTTS) », étoiles **provisoires** reprises de Kyutai en
attendant l'écoute), `synthesize_xtts()` et `XttsIndisponible` dans
`modules/tts.py` (copie exacte du mécanisme Kyutai, port **8083**) ; route
`/api/tts` reconnaît le préfixe `xtts:` ; `/api/voices` ajoute les 35 voix
XTTS **seulement si le moteur est allumé et prêt** (mécanisme du 14/09/2026,
inchangé). Contrôlé de bout en bout, moteur allumé : `/sante` → `pret: true`
en 10,9 s (RTX 4060), `/api/voices` → 35 voix `xtts:`, `/api/tts` → WAV
valide (200, `audio/wav`). Tests mis à jour :
`test_voix/test_voix_ecoutables.py`, `test_voix/test_pool_casting.py`.

**Élargi à 60 voix — 14/09/2026 (soir)** : Laurent a écouté un **lot de 32
voix françaises supplémentaires**, pêchées dans le **jeu public CML-TTS**
(la source même des 35 extraits de Kyutai, en CC BY 4.0) par
`xtts_service\_ecouter_voix_cml.py`. Il en a **retenu 25** (7 notées 0,
écartées) ; elles ont été versées dans `xtts_service\voix_fr\` par
`xtts_service\_verser_voix_cml.py` et ajoutées à `XTTS_VOICES`, **avec un
prénom du XIXᵉ siècle** (Achille, Célestin, Hortense…) et un **genre relevé à
l'oreille**. Résultat : **60 voix XTTS** au catalogue, et deux pools de
casting bien plus larges (**76 voix féminines, 75 masculines** — chiffres du
14/09/2026). L'accent entendu par Laurent est **rappelé dans le libellé**
(« France (XTTS) - accent paysan », « - accent anglais »…) : précieux pour les
personnages étrangers, à assigner à la main.

**Deux pièges rencontrés et corrigés ce soir-là** :
- **convention de genre** : le catalogue des voix utilise **F/M**, alors que
  le casting et l'écoute notent **H/F**. Les 17 premières lignes versées
  portaient `"gender": "H"` → **aucune** n'entrait dans le pool automatique
  masculin (`_xtts_pool("M")` filtre sur `M`). Détecté par simple comptage du
  pool (0 au lieu de 17), corrigé dans le catalogue **et dans l'outil de
  versement** (qui convertit désormais H → M) ;
- **API du jeu** : elle a répondu **429** (trop de requêtes) puis **502**
  (panne) pendant la pêche. D'où un outil qui **télécharge au fur et à mesure**
  (rien n'est perdu), marque une **pause entre les appels**, tient un fichier
  de **reprise** (`_reprise.txt`) et sait **régénérer l'index sans réseau**
  (`--index-seulement`).

**Ce qui reste à faire** (voir BACKLOG) : les **étoiles** des 35 premières
voix XTTS restent **provisoires** (recopiées de Kyutai) — elles mériteraient
une écoute comme les 25 nouvelles ; puis le **bouton de bascule** Kyutai ↔
XTTS avec rallumage automatique du **dernier moteur utilisé** (déjà fait côté
`START.bat`, reste le bouton dans l'interface).

### 🎙️ Moteur de voix NeuTTS (livré le 16/09/2026)

**Ce que c'est** : un troisième moteur de voix « lourd », à côté de Kyutai
(8082) et XTTS v2 (8083), dans son propre service HTTP —
**`neutts_service\`, port 8084** (`/sante`, `/voix`, `/tts`, `/recharger`). Il
vit dans un environnement Python 3.12 séparé, et le lecteur l'appelle **par le
réseau**, exactement comme les deux autres.

**Pourquoi il prend la place d'XTTS comme moteur par défaut** (mesures du
16/09/2026 : atelier NIMM Voix, puis vérification ici) :

- **stable** : à graine fixe, deux synthèses du même texte donnent le même
  fichier **à l'octet près** (empreintes SHA-256 identiques, vérifié sur
  processeur **et** sur la carte graphique) ;
- **pas de babil** sur les phrases courtes (« Manger ? » 1,08 s, contre 8,49 s
  pour XTTS) et **pas de dérive** sur deux minutes de lecture ;
- **plus lent** : environ **×0,8 le temps réel** sur la RTX 4060 (XTTS : ×3),
  d'où l'importance du **cache audio**, déjà en place ;
- **3,50 Go de mémoire vidéo** au pic : il ne cohabite donc **pas** avec XTTS
  ni Kyutai, et la règle « un seul moteur lourd à la fois » continue de
  s'appliquer.

**Les voix** : ce sont des **extraits** (3 à 15 s) **accompagnés du texte
exact** dit dans l'extrait — contrairement à XTTS, le texte est **obligatoire**.
Ils vivent dans `neutts_service\references\` (hors Git), par provenance :
`cml_tts` (60 voix), `voix_libres_dp` (19), `kokoro` (30) — **109 voix** au
16/09/2026. Les 30 voix Kokoro « dites par NeuTTS » gardent leur **timbre** et
perdent leur **accent** (c'est le modèle français de NeuTTS qui réimpose la
prononciation) : constat d'écoute de Laurent, « les accents Kokoro ont
disparu, tout est lu en français très compréhensible ».

**Côté lecteur** :

- catalogue `NEUTTS_VOICES` dans `modules/tts.py`, **généré** par
  `test_voix/_generer_catalogue_neutts.py` — mêmes identifiants, mêmes
  prénoms, genres et étoiles que les voix déjà connues, avec la région
  « France (NeuTTS) » pour ne pas les confondre avec celles d'XTTS ;
- branche `neutts:` dans `POST /api/tts` (`main.py`) + fiche moteur dans
  `MOTEURS_VOIX` (`NEUTTS_URL`, 8084) : le voyant et le bouton de bascule de la
  page fonctionnent donc **sans code spécifique** (l'interface liste les
  moteurs qu'on lui donne) ;
- les voix ne sont proposées **que si le moteur est allumé et prêt**
  (`/api/voices`) ; le catalogue complet (`/api/voix_catalogue`) les nomme
  toujours, même moteur éteint ;
- **pool automatique du casting** : les voix NeuTTS sont ajoutées **en
  dernier** dans chaque palier d'étoiles — la raison est écrite dans
  `voice_casting._pool_par_paliers` (le pool ne connaît pas l'état des
  moteurs).

**Lancement** : `neutts_service\INSTALLER_NEUTTS.bat` (une seule fois, tous les
téléchargements étant déjà en cache), puis `DEMARRER_NEUTTS.bat`. Depuis le
16/09/2026, **`START.bat` l'allume tout seul** et **ne lance plus XTTS ni
Kyutai** : ces deux-là restent disponibles à la main, par leur lanceur ou par
le bouton « Voix de personnages ».

**Deux pièges d'installation** (chacun coûte une demi-journée) : torch
**≥ 2.11** (imposé par `torchtune`) et **`torchao==0.16.0`** épinglée en
`--no-deps`. Détail dans `neutts_service\requirements.txt` et
`neutts_service\LIRE_MOI.md`.

**Vérifications** : `test_voix/test_neutts_service.py` (39 contrôles, sans
charger le moteur) et `test_voix/test_neutts_bout_en_bout.py` (11 contrôles,
moteur allumé : stabilité bit à bit, phrases courtes, phrase longue).




### 🎒 Moteur de voix Pocket TTS (livré le 21/09/2026)

**Sixième moteur**, et le premier qui **cohabite avec tous les autres**. Pocket
TTS est le « petit frère » de Kyutai TTS 1.6B : **100 M de paramètres** (contre
1,8 milliard), il tourne sur le **processeur** — donc **zéro mémoire vidéo** —
et il **clone** une voix depuis un extrait de référence (sans avoir besoin du
texte dit dans l'extrait, contrairement à NeuTTS).

*Pourquoi il n'entre pas dans la règle « un seul moteur lourd à la fois »* : la
règle existe parce que Kyutai (3,8 à 5,6 Go) et XTTS/NeuTTS (3,8 et 3,5 Go) se
disputent les 8 Go de la carte. Pocket TTS n'y touche pas : il peut donc
tourner **en même temps** que Kyutai, Edge, Kokoro et Piper. Dans
`MOTEURS_VOIX` (`main.py`), il porte un drapeau **`cohabite: True`** qui le
tient à l'écart de la bascule de moteur : celle-ci ne l'allume ni ne l'éteint
jamais.

**Installation** (`pocket_tts_service/`, hors Git) : environnement dédié
**Python 3.14** avec **PyTorch 2.14.0+cpu** et **pocket-tts 3.1.0** — les mêmes
versions que l'atelier NIMM Voix. Le lecteur reste **sans PyTorch** : c'est la
raison du dossier séparé, comme pour Kyutai, XTTS et NeuTTS. Le modèle français
(`french_24l`, 641 Mo, dépôt Hugging Face *gated*, poids **CC BY 4.0**) était
**déjà en cache** sur la machine : aucun téléchargement.

**Les 18 voix** : elles viennent des extraits du domaine public préparés par
Laurent (les mêmes que les voix `dp_*` d'XTTS et de NeuTTS, plus `JEAN_EDGAR`).
Les **prénoms sont donc ceux qui existaient déjà** — décision de Laurent du
20/09/2026 (« s'ils existent déjà dans un autre moteur, autant les utiliser,
c'est bien plus intuitif ») : **Marthe, Solange, Yvette, Henriette, Georgette,
Thérèse, Colette, Juliette, Madeleine, Marius, Théodore, Édouard, Victor,
Robert, Paul, Jules, Arthur**, et **Edgar** (unique prénom nouveau, pour
`JEAN_EDGAR`). Les critères d'écoute (âge, timbre, débit, registre, rôle,
étoiles) sont **hérités** des voix jumelles de NeuTTS par
`test_voix/_heriter_annotations_neutts_vers_pocket.py` : **17 voix héritées**,
Edgar restant à annoter à l'oreille. L'**accent** est à revérifier — Pocket TTS
garde la diction de l'extrait, ce qui n'a jamais été mesuré ici.

**Le service** (`pocket_tts_service/servir_pocket_tts.py`, port **8085**) suit
exactement le contrat des autres : `GET /sante` (`pret: true/false`),
`GET /voix`, `POST /tts` (JSON → WAV), `POST /recharger`. Trois différences :

- **une seule génération à la fois** (le modèle n'est pas thread-safe, c'est
  écrit dans son code) ;
- **4 cœurs** par défaut (`NIMM_POCKET_TTS_COEURS`) : les 2 autres restent au
  lecteur, à Kokoro et à Piper — mesuré le 20/09/2026, **brider ne coûte rien**
  (ratio 0,82 avec 6 cœurs comme avec 4) ;
- **auto-extinction** après **180 min sans une seule phrase**
  (`NIMM_POCKET_TTS_INACTIF`, porté de 30 à 180 min le 21/09/2026 : à 30 min il
  s'endormait **en pleine journée d'écoute**, et ses voix disparaissaient du
  casting sous les yeux de Laurent) — il ne doit pas garder 2,3 Go pour rien.

**Démarrage** : `START.bat` le lance **dans SA FENÊTRE**, comme Kyutai
(`start "NIMM ePub - appareil de voix Pocket TTS" /D pocket_tts_service cmd /k
DEMARRER_POCKET_TTS.bat`), en même temps que Kyutai — demande de Laurent du
21/09/2026. Comme pour Kyutai : s'il tourne déjà on ne le relance pas, et s'il
n'est pas installé le lecteur démarre quand même.

**Pourquoi une fenêtre et pas un lancement caché** (changement du 21/09/2026 au
soir, demande de Laurent : *« Pocket TTS reste allumé, je n'ai pas moyen de
l'éteindre »*) : **fermer la fenêtre est le seul geste du projet pour éteindre un
moteur de voix** (règle du 12/09/2026). Le service **avait déjà** son gardien de
console (`_surveiller_la_console`), mais lancé caché il n'avait **aucune fenêtre
à fermer** : il tournait indéfiniment. La fenêtre rend donc ce gardien actif, et
**fermer la fenêtre éteint vraiment** Pocket TTS.

**L'arrêt volontaire est RESPECTÉ** (même soir) : quand sa fenêtre se ferme, le
service écrit `pocket_tts_service/arrete_volontaire.txt`, et **le veilleur du
lecteur ne le rallume plus** (`main._pocket_arrete_volontairement`). Sans ce
marqueur, il le rallumait **30 secondes plus tard** : le geste de Laurent
n'aurait servi à rien. Le marqueur disparaît dès que le moteur redémarre,
`START.bat` l'efface à chaque nouveau démarrage, et le bouton **« Relancer les
moteurs »** (un clic explicite) le force aussi.

**Le lecteur le rallume lui aussi dans une fenêtre**
(`main._demarrer_pocket_avec_fenetre`, ex-`_sans_fenetre` : `CREATE_NEW_CONSOLE`
→ `DEMARRER_POCKET_TTS.bat`) : sinon un Pocket TTS rallumé par le lecteur
n'aurait, de nouveau, aucun geste d'arrêt. Conséquence : les journaux
`journal_service*.txt` ne grandissent plus (la fenêtre montre tout) —
`journal_installation.txt` reste le journal de l'installation.

**Dans le lecteur** : `POCKET_VOICES` (18 entrées, identifiants `pocket:<fichier>`),
un client `synthesize_pocket()` / `_demander_au_moteur_pocket()` et une branche
`pocket:` dans `POST /api/tts` (503 et message clair si le moteur est éteint).
Vitesse et hauteur n'existent pas dans le moteur : mêmes post-traitements que
Kyutai, XTTS et NeuTTS (`atempo` puis Rubber Band). Le **niveau** est ramené à
celui des autres moteurs (`modules/audio_gain.py`), comme pour Kyutai, parce que
le moteur ne règle pas son volume et que ses prises varient. Les voix
n'apparaissent dans `/api/voices` que si le service **répond et est prêt** ;
`/api/voix_catalogue` les liste toujours (`famille: "pocket"`, `dispo`). L'icône
de la famille est **🎒** (`FAMILLES_VOIX`, `app.js`) et le filtre de la page la
reprend (`index.html`).

**Mesures du 20/09/2026** (i5-12400F, 6 cœurs, modèle `french_24l`) :

| Mesure | Valeur |
|---|---|
| Chargement du modèle | **1,7 s** |
| Encodage d'une voix | **3,8 s** (une fois par voix et par démarrage) |
| Ratio calcul / audio | **0,82** → **1 h d'audio ≈ 49 min de calcul** |
| Mémoire | 2,0 Go après calcul, **pic 2,3 Go** (RAM) |
| Carte graphique | **0** |

**Trois comportements du moteur à connaître** :

1. **Le « tic » des phrases courtes — corrigé.** Sur un texte de 1 ou 2 mots il
   sort un **quasi-silence** environ une fois sur deux (constat de Laurent,
   20/09/2026 : « juste un tic de quelques millisecondes »). Mesure : 5 prises
   de « Non. » donnent des crêtes de **0,8 / 0,7 / 45,5 / 18,0 / 4,5 %** ; le
   moteur n'a **aucune graine**. Le service **régénère** donc tant que la crête
   reste sous 5 % (`NIVEAU_MINI`), jusqu'à 4 essais, et garde le meilleur :
   après correction, **42,8 / 8,2 / 40,1 / 19,2 / 35,8 %**. Coût nul sur les
   phrases normales (elles sortent au-dessus de 60 %).
2. **Une durée minimale de 0,72 s** : deux textes courts différents donnent des
   WAV de **même taille** mais de contenus différents (« Non. » = 0,15 s de
   parole dans 0,72 s ; « Oui, monsieur. » = 0,69 s). C'est le moteur, pas un
   défaut de cache.
3. **Le débit est élevé** : 20 à 25 caractères/seconde, contre ~15 pour une
   lecture humaine naturelle. C'est le moteur ; le curseur de vitesse du lecteur
   fait le reste.

**Ce qui reste** (BACKLOG) : le **voyant** détaillé du moteur dans la fenêtre du
lecteur (l'état est déjà exposé par `/api/moteurs`), les **étoiles et critères
d'Edgar** (à l'oreille), la **vérification de l'accent** des 18 voix, et la
**prégénération** des chapitres (décision différée par Laurent).

**Vérifications du 21/09/2026** : les **19 tests JavaScript** passent ;
`test_bascule_moteur.py` (la bascule n'éteint plus Pocket TTS),
`test_import_main.py`, `test_pool_casting.py`, `test_lire_moi.py`,
`test_ids_ecran.py`, `test_pas_de_secrets.py` et `test_js_syntax.py` : OK. Bout
en bout **à travers le lecteur** : 3 phrases synthétisées avec `pocket:Femme001`
(crêtes 37,7 / 46,1 / 69,2 %), et **163 voix** proposées dont **18 Pocket TTS**.





---

## ✂️ Le mode dialogue : narration et répliques

### ✂️ Mode dialogue : la narration séparée des répliques — 21/09/2026

**Aujourd'hui — l'état actuel en clair** (vérifié contre le code le 22/09/2026) :
- la règle vit dans `modules/decoupage.py` (`REGLE_DIALOGUE`,
  `VERBES_DE_PAROLE`, `introduit_une_replique()`) et elle est recopiée **mot
  pour mot** dans `frontend/app.js` — un test compare les deux listes de verbes ;
- elle s'applique **livre par livre** : colonne `books.decoupe_dialogue`
  (ajout non destructif), parce que les numéros de phrases des livres déjà castés
  sont **enregistrés** et qu'un découpage différent décalerait leurs voix ;
- **activation automatique au nouveau casting** (22/09/2026) : un livre neuf est
  casté directement en mode dialogue ;
- outils : `test_voix/MODE_DIALOGUE.bat` (+ `test_voix/regler_mode_dialogue.py`)
  dit qui est en mode dialogue ; `test_voix/_migrer_index_dialogue.py` migre les
  index d'un livre déjà casté (**refuse** de tourner sur un livre déjà en mode
  dialogue) ;
- *vérifications* : `test_voix/test_decoupage_phrases.py` (**41 contrôles**) et
  `test_voix/test_decoupage_auto_casting.py`.

Demande de Laurent : « des marqueurs nets sur "dialogue" et "narrateur" […]
c'est vraiment la seule chose qui manque cruellement pour une immersion
totale. » Dans son exemple — `Avant que j'aie pu répondre, Richie est intervenu :
«Non, c'est pas ça.»` — tout était **un seul morceau**, et comme la consigne 8 du
prompt donne un morceau mixte au personnage, c'est **Richie** qui lisait la
narration.

**Le levier n'est pas l'IA.** Le découpage est une **règle locale**
(`modules/decoupage.py`, jumelle de `_buildSentences` dans la page) ; Gemini ne
fait qu'**étiqueter** des morceaux déjà numérotés — il ne peut pas en couper un
en deux. Améliorer le découpage est donc **gratuit**.

**Règle ajoutée** (`REGLE_DIALOGUE`, valeurs mesurées sur « 22/11/63 ») :

- `VERBES_DE_PAROLE` (radicaux) et `introduit_une_replique(avant)` : la coupe n'a
  lieu que si le texte avant la citation **finit par deux-points** ET **contient
  un verbe de parole** ;
- trois garde-fous : une **citation racontée** (`J'ai jamais eu « la larme
  facile », comme on dit.`) reste intacte, un **deux-points sans verbe**
  (`Le sujet que j'avais donné était : …`) ne coupe pas, un **beat sans
  deux-points** non plus. La variante large (298 morceaux dans « 22/11/63 »,
  contre **166** pour la version retenue) attrapait les citations racontées ;
- chaque radical commence par une **lettre ASCII** : `\b` n'a pas la même
  signification en Python (Unicode) et en JavaScript (ASCII) ;
- `_couper_avant_replique()` rend **deux morceaux aux positions exactes**
  (`debut`/`fin`) : la migration des index de `speaker_attribution` s'appuie
  dessus.

**Un mode PAR LIVRE, jamais global** : colonne `books.decoupe_dialogue` (ajout
non destructif, 0 par défaut). Les livres déjà castés gardent le découpage
d'origine **caractère pour caractère** — indispensable, leurs numéros de phrases
étant enregistrés dans `speaker_attribution`. La règle voyage avec le livre
partout où le texte est découpé : `main.py` (`_mode_dialogue`, `_regle_du_livre`),
le casting (`voice_casting.analyze_chapter(..., regle=)`, `analyze_chapters`),
l'estimation de coût (`estimate_cast_cost`), l'extrait de répliques et la
recherche. La page la reçoit dans `/api/books/{id}` (`decoupe_dialogue`) et la
passe à `_buildSentences(text, decoupeDialogue)`.

*Outil* : `test_voix/MODE_DIALOGUE.bat` (+ `regler_mode_dialogue.py`) — liste des
livres, activation/désactivation, **copie datée de la base** avant écriture.

*Vérifications* : `test_voix/test_decoupage_phrases.py` — **36 contrôles** : la
règle et ses trois garde-fous, l'exemple exact de Laurent, les positions exactes,
aucun texte perdu, et l'identité des listes de verbes entre Python et la page.

**Les INCISES DE PAROLE : muettes, ou lues par le narrateur** (22/09/2026, décision
de Laurent). Même famille de réglage — **par livre**, colonne
`books.incises_narrateur`, **0 par défaut** (aucun livre déjà casté ne change de
comportement). L'incise de parole (« , dit-il, », « m'a-t-il dit. ») est soit
retirée du texte parlé (**muette**, comportement historique), soit **confiée au
narrateur** : la page coupe la phrase aux positions que lui donne le serveur
(`GET /api/books/{id}/chapter/{i}/incises`, calculées par `modules/incises.py`) et
donne ce morceau à la voix du narrateur. **Aucun re-cast, aucun re-découpage, aucun
index touché** : le lecteur sait déjà jouer plusieurs morceaux pour une phrase
(phrases longues, `_splitLongSentence`), chacun portant son texte, sa voix, sa
hauteur et sa vitesse, et tous partageant le **même `sentIdx`** (la surbrillance ne
bouge pas). Le libellé du bouton **« Incises »** de la barre du lecteur
(`#incises-btn`) porte l'état : 🔇 muettes / 🗣️ lues par le narrateur.
*Pourquoi par livre* — mesuré le 22/09/2026 (part des incises au « je ») : **0 à
1 %** dans les classiques (Monte-Cristo, Notre-Dame de Paris), **25 %** dans
22/11/63, **51 %** dans Shantaram ; **aucun seuil automatique** ne sépare
proprement ces livres (un critère naïf classerait 22/11/63 en « classique », soit
le contraire de ce que Laurent entend), le style se juge à l'oreille.
*Le piège à connaître* : `/api/tts` reçoit un drapeau **`incise_a_lire`** ; sans
lui, un morceau qui n'est qu'une incise serait remplacé par un **court silence**
(`_est_incise_seule`) et la fonction paraîtrait cassée.
*Vérifications* : `_test_morceaux_incises.py` (positions réelles, reconstruction
caractère pour caractère, **parité Python / JavaScript** sur la vraie fonction
`_morceauxDeLaPhrase`) et `test_voix/test_incise_seule.py` (le drapeau).

*Prix* : un appel IA coûte **0,0047 €** (journal des appels) ; un livre entier
va de **0,06 €** (Lazarille, 912 phrases) à **1,41 €** (Shantaram, 30 285) —
estimation de l'application, **calibrée sur une facture Google réelle** : le
casting de Shantaram (30 293 phrases, 211 appels) a été **facturé 0,98 €**
(14/09/2026). *(Chiffre corrigé le 22/09/2026 : cette page annonçait « ≈ 1,15 €
l'essai complet », une estimation **d'avant** la calibration, restée là par
erreur ; le BACKLOG portait la même.)*
**Mesure du 22/09/2026, qui répond à une question de Laurent** : **le mode
dialogue ne change pas le prix** d'un casting — « 22/11/63 » 1,141 € → 1,150 €
(**+0,8 %**, moins d'un centime), écart **nul** sur Monte-Cristo T5, Shantaram et
Lazarille. Le découpage fin ajoute des morceaux (375 de plus sur 24 841), mais
chacun est plus court. L'essai complet sur le
livre de test — castage en mode origine, puis re-cast en mode dialogue — revient
à ≈ **0,15 $**.

*À faire* : l'essai à l'oreille sur « Lazarille de Tormes » (livre neuf, choisi
par Laurent pour ne toucher à aucun livre casté), puis la décision **livre par
livre** : migration **gratuite** des index, ou re-cast (≈ **0,06 à 1,41 €** selon
la taille du livre).

**Le découpage est posé AVANT l'IA, automatiquement** (22/09/2026 ; demande de
Laurent : « si je caste un nouveau livre, il doit être découpé avant envoi à
Gemini »). Dans `main.py`, `start_casting` regarde si le livre a **déjà** des
attributions (`_livre_jamais_attribue`, un `COUNT` sur `speaker_attribution`) :

- **aucune** → il active `books.decoupe_dialogue` **avant** le premier appel :
  l'IA étiquette donc le découpage fin, et le prix ne change pas (+0,8 % au pire,
  mesuré : le découpage fin crée quelques morceaux de plus, mais plus courts) ;
- **au moins une** → il ne touche à **rien** : les numéros de phrases sont
  enregistrés, et changer le découpage décalerait les voix — c'est le rôle de la
  **migration** (`test_voix/_migrer_index_dialogue.py`), pas du casting.

L'**estimation de coût** (`GET /api/books/{id}/cast/estimate`) suit la même règle
(`_regle_pour_casting`) : un prix affiché doit correspondre au découpage qui sera
réellement envoyé. *Garde-fou* : `test_voix/test_decoupage_auto_casting.py`
(**11 contrôles**, ajouté au lanceur global).

**Rattachement MANUEL des pseudonymes (12/09/2026)**
La règle automatique ne peut **pas** deviner que « Le comte de Monte-Cristo »,
« Edmond Dantès », « l'abbé Busoni » et « Simbad le marin » sont **un seul
personnage** : rien ne relie ces noms à l'écriture (constat de Laurent, qui
ne « voyait pas » de regroupement — seuls 8 doublons d'écriture avaient été
trouvés sur le Tome 4, et certains portaient 0 réplique, donc tout en bas de
la liste). D'où un bouton **🔗 « rattacher à… »** sur chaque personnage de la
fenêtre du casting :

- on choisit le **personnage principal** dans une **liste déroulante** (les
  plus présents en premier, avec leur nombre de répliques), puis « Rattacher » ;
- une ligne est ajoutée dans `character_aliases` (même table que les doublons
  d'écriture) : le nom s'affiche **en retrait sous le principal** (flèche ↳),
  avec le **total de répliques cumulé** ;
- **les VOIX ne sont PAS touchées** : chaque appellation garde la sienne —
  c'est justement ce que veut Laurent (« Monte-Cristo n'a pas la même voix que
  l'abbé Busoni »). C'est **la** différence avec le regroupement automatique
  des doublons d'écriture, qui aligne les voix sur le principal ;
- **réversible** (bouton ✂), gratuit, aucune donnée supprimée, aucune
  migration de base.

Route : `POST /api/books/{id}/cast/group?user_id=…` avec
`{alias_name, canonical_name}`. Elle refuse l'auto-rattachement, les noms
inconnus et les **cycles** ; si la cible est elle-même un alias, on remonte à
sa **racine** (jamais de chaîne A → B → C) ; les alias déjà rattachés à la
source **suivent le mouvement**. Vérifié par aller-retour sur le Tome 4
(« Edmond Dantès » → « Monte-Cristo » : 9ᵉ alias créé, voix inchangée, puis
détachement = retour à 8 alias).

---

## 🔒 Écouter dans de bonnes conditions

### 🔒 Lecture écran éteint (Media Session) — session du 20/08/2026
**Problème :** sur mobile, dès l'écran verrouillé, le navigateur
suspendait la création du prochain lecteur audio (chaque phrase créait
un `new Audio()` indépendant) — la lecture s'arrêtait net à la fin de
la phrase en cours, sans erreur visible.

**Solution :**
- Un seul élément `<audio id="tts-audio-player">` permanent dans le DOM
  (`index.html`), réutilisé pour chaque phrase (`audio.src = url`) au
  lieu d'instancier un nouvel `Audio()` à chaque fois (`_playBlob` /
  `app.js`) — signal beaucoup plus fiable pour le navigateur qu'il
  s'agit d'une vraie lecture continue à maintenir en arrière-plan.
- Déclaration explicite au navigateur via la **Media Session API**
  (`_updateMediaSession()` / `app.js`) : métadonnées (titre du livre,
  auteur) + `playbackState` synchronisé sur les 3 états (`playing` au
  démarrage, `paused` sur pause, `none` sur arrêt complet — y compris
  la fin naturelle du dernier chapitre du livre). Bonus : affiche le
  titre + boutons play/pause/précédent/suivant sur l'écran de
  verrouillage du téléphone, comme une vraie application audio.

**Validation terrain :** testé en conduite réelle (Laurent) — la
lecture continue bien après extinction de l'écran.

**Correctif du 23/08/2026 (persistance du problème en conditions réelles) :**
la lecture s'arrêtait encore après quelques secondes d'écran éteint. Cause :
l'architecture « une phrase = un fetch » ne survit pas à la suspension réseau
du navigateur en arrière-plan (1 seule phrase d'avance en mémoire). Correctif :
- Fusion des phrases en groupes de même voix/pitch/paragraphe, jusqu'à
  `MAX_GROUP_CHARS` = 1500 caractères (~1-2 min d'audio par requête) →
  quelques requêtes par chapitre au lieu d'une par phrase, et plusieurs
  minutes d'audio en mémoire d'avance.
- Retry réseau dans `_fetchAudio` (4 tentatives, backoff 1s/2s/4s) : un
  échec ponctuel ne stoppe plus la lecture.
- Curseur glitch : suivi approximatif pendant un groupe via `timeupdate`.

**Correctif du 08/09/2026 (retour à la lecture phrase par phrase) :** la
fusion en groupes causait un rythme de lecture irrégulier (des blocs de
« quelques mots » à côté de blocs d'un paragraphe presque entier) et une
surbrillance qui dérivait (position estimée au temps dans un bloc
multi-phrases, souvent en avance sur la voix). Le moteur client lit
désormais **une phrase par requête** (`_buildPlaylist`) et :
- **Surbrillance synchrone** : le curseur glitch est posé quand l'audio de
  la phrase démarre, il ne bouge plus jusqu'à la fin de la phrase (le
  suivi `timeupdate` estimé a été supprimé de `_playBlob`).
- **Prefetcher de fond en continu** (`pump()` dans `_runTTS`) : la suite
  du chapitre est préchargée phrase après phrase (parallélisme 2, fenêtre
  glissante plafonnée à `PREFETCH_MAX_AHEAD_CHARS` = 5000 caractères,
  ~5-6 min d'audio). Le buffer dépasse largement l'avance de l'ancien
  pipeline ×2 : au verrouillage de l'écran, la
  lecture continue sur les phrases déjà en mémoire.
- **Timeout par requête** (`FETCH_TIMEOUT_MS` = 20 s) : une requête
  suspendue sans erreur (réseau Android coupé) n'est plus un blocage
  éternel ; elle est relancée. Si le buffer est épuisé, la lecture attend
  le réseau (`waitUnitNetworkRetry`) et repart seule à son retour.
- Côté serveur (`modules/tts.py`), les synthèses locales **Kokoro** et
  **Piper** sont désormais sérialisées par un verrou d'inférence
  (`_kokoro_infer_lock` / `_piper_infer_lock`) : elles ne sont pas
  thread-safe, et le préfetcher maintient désormais 2 requêtes
  simultanées en continu pendant le remplissage du buffer.

Reste un cas limite connu : la bascule d'un chapitre au suivant (fin de
chapitre) peut marquer une courte interruption si le réseau est suspendu.

**Contexte réseau réel (Tailscale + mobile 4G/5G) :** l'appli est servie par
l'ordinateur de la maison, joignable depuis le mobile via le tunnel Tailscale.
Chaque requête TTS traverse le tunnel : si celui-ci est « endormi » (écran
éteint + optimisation batterie active), les fetch échouent et la lecture
s'arrête à la fin du buffer audio. Recommandations côté téléphone pour que la
lecture écran éteint tienne :
- Paramètres → Applications → **Tailscale** → Batterie → **Sans restriction**
  (faire de même pour le navigateur/PWA utilisé : Chrome, Brave, Firefox...).
  ⚠️ **C'est LE réglage qui décide** — confirmé sur le terrain le 20/09/2026 :
  avec Brave sur « optimisée », la lecture s'arrêtait ~20 s après le
  verrouillage ; passé à « **non restreinte** », elle tient (voir « Lire écran
  verrouillé » plus haut).
- Paramètres → Réseau → VPN → Tailscale → **VPN toujours actif** si proposé.
- Utiliser la **PWA installée** (Ajouter à l'écran d'accueil) plutôt que le
  navigateur classique : meilleur traitement en arrière-plan.

### 🔒 Lire écran verrouillé : la « réserve à bloc », et le lecteur (20/09/2026)

**Le problème, tel que Laurent l'a décrit** : « la lecture s'arrête si je
verrouille le téléphone (c'est aléatoire, parfois après quelques secondes,
parfois ça tient longtemps) ; par contre quand l'écran s'éteint tout seul, ça ne
semble pas poser de souci. En Chrome (donc pas la PWA), verrouiller arrête la
lecture immédiatement. »

**Ce que dit le code** (et ce qui explique l'aspect « aléatoire ») : la lecture
est **phrase par phrase**, et un **préchargeur de fond** garde une réserve
d'environ **5-6 minutes** d'audio (`PREFETCH_MAX_AHEAD_CHARS` = 5000 caractères,
fenêtre glissante, 2 requêtes en parallèle). Quand Android suspend le réseau de
la page, la lecture continue **sur la réserve**, puis **s'arrête quand elle est
vide** : c'est donc **l'état de la réserve au moment du verrouillage** qui
décide — d'où « parfois quelques secondes, parfois longtemps ». L'écran qui
s'éteint tout seul, lui, laisse la page au premier plan plus longtemps.

**Trois réponses, livrées ensemble :**

1. **La réserve « à bloc »** (`_prechargementBurst`) : dès que la page passe en
   **arrière-plan** pendant une lecture (`visibilitychange` → `hidden`), le
   plafond de la fenêtre est levé (`PREFETCH_MAX_AHEAD_CHARS_BURST` = 400 000
   caractères : tout le reste du chapitre) et le remplissage est relancé
   immédiatement par un **crochet**, `_pumpCourant` (le `pump` de la session en
   cours ; la session sert de garde-fou, un `pump` périmé ne fait rien). Le
   téléphone remplit donc sa réserve **pendant que le réseau répond encore**.
   **Hors lecture, rien ne se déclenche.**
2. **Le lecteur du système complet** : `_updateMediaSession` habille la
   notification et l'écran verrouillé avec la **couverture du livre** (en URL
   **absolue** — un chemin relatif est refusé), le titre, l'auteur et le
   **chapitre**, et déclare les boutons ▶/⏸ · `previoustrack`/`nexttrack` (la
   phrase) · `seekbackward`/`seekforward` (4 paragraphes) · `seekto` (la barre) ·
   `stop`. `_majPositionMediaSession` envoie la **progression** à chaque phrase,
   sur l'échelle du **chapitre** (position = phrases lues, durée = phrases du
   chapitre), avec deux garde-fous : la position est **bornée** et l'appel est
   **protégé** (`setPositionState` lève une `TypeError` hors bornes, et une barre
   ne doit **jamais** pouvoir casser la lecture). Un vrai lecteur média aux yeux
   d'Android, c'est aussi ce qui l'aide à ne pas endormir la page.
3. **Le lecteur intégré « façon Deezer »** (`#lecteur-modal`) : ouvert en tapant
   la **barre de progression** (qui porte un petit ⤢ pour l'annoncer), il affiche
   la couverture, le titre, l'auteur, le chapitre, **qui parle**, **la phrase en
   cours**, la progression et le compteur. Ses **sept boutons sont des
   télécommandes** de la barre du bas : ils cliquent sur les vrais boutons, donc
   **une seule logique de navigation** existe, et les pas sont forcément les bons
   (◀▶ la phrase, ⏪⏩ 4 paragraphes, ⏮⏭ le chapitre). Il suit l'état réel de la
   lecture (`_majLecteurEtat`, appelé par `setTTSUI`).

4. **Les phrases sont COLLÉES en un seul morceau** (demande de Laurent, le soir) :
   la lecture ne joue plus un fichier par phrase, elle joue **un seul long
   morceau**, fabriqué dans le navigateur en recollant les WAV déjà téléchargés.
   Pourquoi : avec un fichier par phrase, **il n'y a plus de son** pendant la
   préparation de la suivante — et Android **range sa modale de lecture** dès
   qu'il n'y a plus de son. Laurent l'a dit mieux que personne : « c'est comme si
   j'avais une playlist de centaines de morceaux de quelques secondes, et entre
   chaque, elle disparaît ». Avec un seul morceau : **la modale reste affichée**
   (comme pour une vidéo) et le son n'a plus de micro-blanc.
   *Comment c'est possible* : les fichiers du lecteur sont des **WAV** (audio non
   compressé) — vérifié sur 400 fichiers du cache : **399 en 24000 Hz mono
   16 bits** (une voix Piper, en 22050 Hz, ne se colle pas aux autres et termine
   simplement le morceau). Le collage ne **copie rien** (`Blob.slice` pointe sur
   les données d'origine, donc pas de mémoire en plus), la **pause entre
   paragraphes est insérée en silence** dans le morceau, et la surbrillance suit
   grâce à des durées **calculées** (taille du son ÷ débit) et non estimées : le
   piège du 15/09/2026 (curseur qui dérive) ne s'applique donc pas.
   *Filet* : si un format est inattendu, `_collerWav` renvoie `null` et la phrase
   est jouée **seule**, exactement comme avant (`_playBlob`). Le lecteur reste le
   même : même élément `audio`, mêmes arrêts, mêmes sauts.
   *Vérification* : **nouveau** `test_voix/test_collage_wav.js` — et il a servi
   tout de suite : il a attrapé une **taille fausse** dans l'en-tête
   (`_enteteDeBlob` ne lit que les **64 premiers octets** du fichier, et le
   garde-fou « fichier tronqué » en déduisait que la phrase ne durait que
   **0,4 ms** ✗) : le morceau collé aurait annoncé une taille minuscule, donc été
   **inaudible**. Corrigé en transmettant la **taille réelle** du blob
   (`_enteteWav(octets, tailleFichier)`). Leçon : **une taille calculée se teste**,
   sinon elle se découvre à l'oreille.

5. **L'application remet son état en phase avec le lecteur** (demande de Laurent,
   le soir : « quand la lecture est arrêtée, le bouton affiche souvent Pause » et
   « je voudrais pouvoir mettre pause avec le casque, et reprendre la lecture » —
   **les deux ont la MÊME cause**). Quand Android met l'audio en pause **sans
   nous** (appel téléphonique, autre application qui prend le son, système…),
   **aucun événement de fin** n'est envoyé : le lecteur attendait alors pour
   toujours et `_ttsState` restait sur `'playing'` ✗ → le bouton disait « Pause »
   alors que plus rien ne jouait, et le bouton du **casque** envoyait « **pause** »
   au lieu de « **play** » (l'application se croyant déjà en lecture).
   Correctif : `audio.onpause` détecte la pause **venue d'ailleurs** — notre propre
   pause et la fin naturelle d'un morceau (qui déclenche aussi cet événement) sont
   écartées — puis remet l'état sur `'paused'`, met à jour **l'écran** et le
   **lecteur du système**, et **rend la main** (`break` dans la boucle). La reprise
   part du curseur à la pression suivante, et ne repart **jamais** toute seule.
   *Vérification* : **nouveau** `test_voix/test_pause_casque.js` (pause externe
   reconnue, notre pause ignorée, fin naturelle non confondue, écouteur retiré).

**Ce qui reste à prouver** : le comportement au verrouillage ne peut être validé
que **sur le téléphone** — et **avec la PWA installée** (une page d'onglet Chrome
survit beaucoup moins bien qu'une application installée : c'est écrit dans ces
notes depuis le 15/09).

**✅ CAUSE TROUVÉE ET CONFIRMÉE SUR LE TERRAIN (20/09/2026, le soir) — et ce
n'était PAS l'application : l'OPTIMISATION DE BATTERIE d'Android.** Laurent
testait dans **Brave installé**, et la lecture s'arrêtait « après une vingtaine
de secondes » écran verrouillé. Son verdict final, en une phrase :
« **je viens de modifier le réglage de la batterie dans l'appli, ça semble ne
plus couper** » — Brave était sur « **optimisée** », il l'a passé à « **non
restreinte** », et la lecture tient depuis (2 minutes et plus, y compris en
quittant le lecteur et en revenant à l'écran d'accueil). Autrement dit : **Android
endormait le navigateur dès le verrouillage**, et l'application n'y pouvait rien
— c'est un réglage du TÉLÉPHONE, pas du code.

*Ce que sa description a confirmé au passage* : la **notification de lecture
apparaît** (couverture, titre, auteur, boutons) et **s'ouvre en plein écran** au
tap → notre Media Session fonctionne, et c'est bien le « lecteur façon Deezer »
demandé. L'écart entre **l'écran qui s'éteint tout seul** (la page reste au premier
plan → ça joue) et le **verrouillage** (la page passe en arrière-plan → ça
s'arrêtait) collait exactement à cette cause.

⚠️ **À retenir pour la prochaine fois** : avant de chercher dans le code, **vérifier
que le navigateur (et Tailscale) sont en Batterie « Sans restriction »**. C'est la
**première** chose à contrôler, et ça a coûté deux jours de doute. Le réglage se
fait dans **Paramètres Android → Applications → [Brave] → Batterie → Sans
restriction**.

*Fichiers* : `frontend/app.js` (`_prechargementBurst`, `_pumpCourant`,
`limiteFenetre`, `_updateMediaSession`, `_majPositionMediaSession`,
`_urlCouvertureLivre`, `_ouvrirLecteur`, `_fermerLecteur`, `_majLecteurIntegre`,
`_majLecteurEtat`), `frontend/index.html` (`#lecteur-modal`, `#tts-progress-row`
cliquable), `frontend/styles.css`. *Vérifications* :
`test_voix/test_lecteur_media.js` (**42 contrôles**, sans navigateur) et
`test_voix/test_ids_ecran.py` (§ 3 sexies, **160 contrôles** au total).

### 💾 Cache audio serveur — session du 08/09/2026
La synthèse TTS est déterministe : le même texte (après `_clean_text`), la
même voix, le même `rate` et le même `pitch` produisent toujours le même
audio. Depuis le passage à la lecture phrase par phrase, chaque écoute
re-sollicitait le moteur pour chaque phrase. Un **cache disque** évite de
re-générer un passage déjà synthétisé.

**Module `modules/tts_cache.py`** :
- Dossier `data/tts_cache/` (ignoré par Git), fichiers nommés par
  `sha256(texte_nettoyé + voix + rate + pitch)`, extension `.mp3` pour
  Edge, `.wav` pour Kokoro/Piper.
- **Quota 20 Go** par défaut, réglable via `NIMM_TTS_CACHE_GB` ; purge
  automatique des fichiers les plus anciens (par date) quand le quota est
  dépassé (reciblage à 75 %).
- Écriture **atomique** (fichier temporaire + `os.replace`) : on ne lit
  jamais un fichier à moitié écrit, deux requêtes simultanées sur la même
  clé ne se marchent pas dessus.

**Intégration (`modules/tts.py`)** : le cache est consulté dans
`synthesize_stream` (Edge, par chunk MP3) et dans `synthesize_kokoro` /
`synthesize_piper` (WAV complet), avant même le chargement du modèle — un
passage en cache est renvoyé sans toucher au moteur ni au réseau.

**Effets** : relecture quasi instantanée des chapitres déjà écoutés,
moins d'appels vers Microsoft Edge TTS, et lecture possible sans réseau
pour les passages déjà générés (écran verrouillé inclus).

### ✂️ Rognage des silences de bord — session du 08/09/2026
Les MP3 produits par Edge TTS contiennent ~0,25 s de silence en tête et
~1 s de silence en fin de phrase (pause de fin d'énoncé ajoutée par le
service). En lecture phrase par phrase, ces blancs s'accumulaient (~1,2 s
entre deux phrases) : rythme haché, et surbrillance qui semblait flotter.

`modules/audio_trim.py` rogne ces silences tout en **conservant des
micro-pauses naturelles** (~0,08 s en tête, ~0,15 s en fin). Technique :
le binaire `ffmpeg` **déjà embarqué** par le paquet `imageio-ffmpeg`
(installé) avec le filtre `silenceremove` appliqué dans les deux sens —
**aucune dépendance ajoutée**. En cas d'échec quelconque, l'audio original
est renvoyé : la lecture n'est jamais cassée.

Le rognage est appliqué dans `synthesize_stream` (Edge) **avant la mise en
cache** : le fichier stocké et envoyé au client est déjà nettoyé. Les voix
locales Kokoro/Piper (WAV) ont des silences courts et naturels
(0,03-0,25 s mesurés) → non rognées.

**Complément du 15/09/2026 — XTTS v2 est rogné à son tour (même marge).**
Constats d'écoute de Laurent (une heure du Comte de Monte-Cristo) : pauses de
fin de phrase **plus longues** qu'avec Kokoro ou Edge, et encore des
**respirations** en fin de phrase. Mesure sur 19 fichiers réels
(`xtts_service/_mesurer_bords_xtts.py`) : **silence de queue de 0,54 à 0,91 s,
variable d'une phrase à l'autre** (silence de tête négligeable), donc un
espacement **irrégulier** d'une phrase à l'autre — très audible dans les
dialogues. Le rognage se fait **dans le service** (`servir_xtts.py`,
`rogner_queue()`, constante `SILENCE_QUEUE_S = 0,25 s`, en numpy, aucune
dépendance ajoutée), **pas** dans `modules/tts.py` qui est partagé par tous
les moteurs. Mesure après rognage sur les mêmes fichiers : **0,26 s partout**
(0,25 s + arrondi du bloc d'analyse de 20 ms). *Vérification sans moteur* :
`test_voix/test_rogner_queue_xtts.py` (14 contrôles). *À savoir* : le rognage
change la **clé du cache audio** côté lecteur — les phrases déjà générées
gardent l'ancien rendu jusqu'à purge de `data/tts_cache/`.

**Complément du 16/09/2026 — le BABIL sur les phrases courtes (corrigé).**
Constat de Laurent, chapitre 2 du *Chevalier Errant* : après la réplique
« Il y a un bon agneau rôti aux herbes… Que préférez-vous ? », l'Aubergiste
« parle » près de **4 secondes** de bouillie inintelligible. Le texte reçu par
le moteur était **propre** (vérifié : `test_voix/_inspecter_phrase_xtts.py`
montre le découpage et le nettoyage, guillemet fermant retiré) : la cause est le
**moteur lui-même**. XTTS est **auto-régressif** : sur un texte court, il n'a
pas assez de matière pour s'arrêter et **continue d'inventer**.

Mesures (`test_voix/_tracer_phrase_cache.py` et `_chercher_babil_cache.py`,
qui retrouvent l'audio en cache d'une phrase à partir de sa clé SHA-256) :

| Phrase | Texte | Rendu | Attendu |
|---|---|---|---|
| « Que préférez-vous ? » | 19 car. | **9,11 s** | ~1,4 s |
| « — Manger ? » | 10 car. | **8,49 s** | ~0,8 s |
| « Elles sont toutes à Sorbier. » | 28 car. | **6,27 s** | ~2,0 s |

Les **3 seules** phrases fautives du livre sont les plus **courtes**, et le
balayage des **8 autres livres castés** ne trouve **rien** : le défaut est
propre au **clonage XTTS**, jamais aux moteurs Edge/Kokoro/Piper ni à Kyutai.

**Correction** (dans le service, comme le rognage des silences) : la longueur
de génération est **bornée d'après le texte** — `max_new_tokens` calculé par
`tokens_max_morceau()` (14 car./s × 1,8 + 0,6 s de marge, plancher 24 jetons
≈ 1 s, plafond 900 jetons ≈ 38 s) et transmis à la génération HuggingFace par
`inference(**hf_generate_kwargs)`. Un **rognage de secours**
(`rogner_a_duree()`) coupe la fin si le moteur ignore la borne. Bornes obtenues :
19 car. → **3,04 s**, 28 car. → 4,20 s, 250 car. → **32,7 s** : les phrases de
longueur normale ne sont donc jamais contraintes (leur rythme naturel reste
très en deçà).

*À savoir* : les phrases déjà générées **restent baveuses** tant que leur
fichier de cache existe — les 3 fautives du livre 35 ont été **purgées**
(copies d'écoute conservées dans `test_voix/ecoute_babil/`) et seront
régénérées proprement. Le **service doit être redémarré** (le code vit en
mémoire).

*Vérification sans moteur* : `test_voix/test_borne_babil_xtts.py` (**16
contrôles** : bornes, plancher/plafond de jetons, rognage de secours, cas
limites). *Diagnostic* : `_inspecter_phrase_xtts.py` (texte exact envoyé),
`_tracer_phrase_cache.py` (fichier de cache et durée), `_chercher_babil_cache.py`
(balayage d'un livre, avec `--purger` pour supprimer les audios fautifs).

**Second filet le même jour — le petit résidu après un silence.** Deuxième
constat de Laurent : sur `— Non.`, une pause puis un court « babile ». Comme le
moteur était cette fois **allumé**, la mesure est directe :
`test_voix/_mesurer_phrases_courtes.py` demande de **vraies synthèses** au
service et découpe l'audio en segments de parole (blocs de 20 ms, seuil
`SEUIL_SON`). Résultat, motif identique sur les deux cas gênants :

| Phrase | Parole | Silence | Résidu |
|---|---|---|---|
| `Non.` | 0,02-0,28 s | **0,34 s** | 0,62-0,80 s (babil) |
| `…pour la nuit ?` | 0,00-1,82 s | **0,36 s** | 2,18-2,24 s (micro-résidu) |

Le babil est donc **séparé de la phrase par un silence franc** — on peut le
couper **dans le silence**, sans jamais toucher à la parole. C'est le rôle de
`rogner_babil_apres_silence()` (appelée après `rogner_a_duree()` dans
`_lire_un_morceau()`) : s'il existe un silence ≥ `SEUIL_SILENCE_LONG_S`
(0,30 s) suivi d'au plus `RESIDU_MAX_S` (0,35 s) de parole, on coupe à la fin
du segment précédent + la marge de queue habituelle.

Garde-fous : les pauses **internes** d'une phrase sont bien plus courtes
(0,04 s mesurées) et un long silence suivi d'une **vraie** suite de phrase
(> 0,35 s) ne déclenche rien ; audio vide et silence total sont renvoyés tels
quels. *Vérification* : `test_voix/test_rogner_babil_xtts.py` (**12 contrôles**,
sans moteur, sur les motifs mesurés).

*À savoir* : le moteur est **stochastique** — la même phrase donne des durées
différentes d'une synthèse à l'autre (0,93 / 1,07 / 1,11 s observées pour
`Non.`). C'est précisément pourquoi il y a **deux** filets : la borne de
longueur (dérives longues) et la coupure après silence (petits résidus).


---

## 📜 Journal des sessions passées

### 🎬 Pistes ouvertes de la session du 21/08/2026 — déménagées

Les idées ouvertes ce soir-là **vivent maintenant dans `BACKLOG.md`**, qui est la
liste de travail : le **réglage du pitch par personnage** (« Édition du pitch par
personnage dans la fenêtre du casting »), le **regroupement des voix par pays**
(`<optgroup>`), la **surveillance des voix Edge « trop robotiques »** et le
**gard « citation ouverte »** (les tirets de dialogue coupés par un `!` ou un `?`
interne). Retirées le **22/09/2026**, avec l'accord de Laurent, parce qu'elles
n'étaient plus vraies ou plus utiles :
- l'état Git de ce soir-là (4 fichiers non commités — sans objet aujourd'hui) ;
- le compte de voix des menus (« 12 Edge + 54 Kokoro = 66 entrées » : il y en a
  **175** aujourd'hui, et la question du rangement est déjà au BACKLOG) ;
- « Nettoyage de `test_voix/` », note vague jamais traitée ;
- « ✅ Profil Nadia créé » : c'est du **déjà livré**, et ce qui compte — le
  profil — est écrit dans « Profils familiaux » (la base a **3 profils**).

*Le texte d'origine (journal du 21/08/2026) est conservé dans
`ARCHITECTURE.md.bak_avant_demenagement_20260922`.*
### ✅ Validation terrain complète — session du 21/08/2026
Système multi-moteur + Kokoro + gard citation ouverte testés de bout en
bout sur le Tome II du Comte de Monte-Cristo en conditions réelles :
20/20 chapitres analysés avec DeepSeek, 56 voix générées (dont la voix
italienne Kokoro pour Pastrini/Vampa), aucune erreur, écoute réelle
confirmée concluante par Laurent.

