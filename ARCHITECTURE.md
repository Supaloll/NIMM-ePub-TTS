# NIMM ePub — Architecture

_Décrit la logique en vigueur. À mettre à jour quand une logique change._

---

## Structure du dossier

```
nimm-epub/
├── main.py                — Serveur FastAPI, toutes les routes HTTP
├── core/
│   └── epub_parser.py     — Extraction chapitres, métadonnées, images de couverture
├── modules/
│   ├── tts.py             — Synthèse vocale : Edge, Kokoro, Piper, Kyutai (routage par préfixe)
│   ├── tts_cache.py       — Cache audio disque (quota réglable, purge des plus anciens)
│   ├── audio_trim.py      — Rognage des silences de bord (ffmpeg embarqué)
│   ├── audio_rate.py      — Vitesse par post-traitement ffmpeg (moteurs sans réglage natif)
│   ├── voice_casting.py   — Casting IA : analyse, fiche de personnages, attribution des voix
│   └── config.py          — Clés API (data/config.json, hors Git)
├── kyutai_service/        — Moteur de voix Kyutai, lancé À PART (Python 3.12 + PyTorch)
│   ├── servir_kyutai.py   — Service HTTP local (127.0.0.1:8082)
│   ├── INSTALLER_KYUTAI.bat — Installation unique (environnement, voix, modèle)
│   ├── DEMARRER_KYUTAI.bat  — Allume le moteur
│   ├── tester_service.py  — Écoute de contrôle du branchement
│   ├── tester_toutes_voix.py — Lot d'écoute des 35 voix (étiquetage H/F, étoiles)
│   ├── voix_fr/           — Les 35 voix françaises libres (hors Git)
│   └── LIRE_MOI.md        — Mode d'emploi + ATTRIBUTION.md (licences)
├── frontend/
│   ├── index.html         — Interface unique : bibliothèque + lecteur
│   ├── app.js             — Logique client : navigation, upload, TTS, curseur glitch
│   └── styles.css         — UI mobile-first, PWA-ready, animation glitch
├── data/
│   ├── library/           — EPUBs stockés sur le PC
│   └── nimm_epub.db       — SQLite : progression de lecture, métadonnées
├── manifest.json          — Déclaration PWA (icône, nom, affichage plein écran)
├── START.bat              — Lance le serveur sur le port 8081
└── ARCHITECTURE.md        — Ce fichier
```

---

## Principe général

NIMM ePub est un serveur local Python (FastAPI) accessible depuis n'importe quel
appareil connecté au même réseau Tailscale. Le navigateur du téléphone sert de
lecteur — les fichiers EPUB restent sur le PC.

Aucun module ne parle directement à un autre. main.py orchestre tout.

---

## Flux principal

1. L'utilisateur ouvre NIMM ePub dans le navigateur (http://[IP-Tailscale]:8081)
2. Il upload un EPUB depuis son téléphone → stocké dans data/library/
3. Il sélectionne un livre dans sa bibliothèque
4. Le texte est extrait chapitre par chapitre par epub_parser.py
5. Le chapitre est découpé en phrases et paragraphes côté client (app.js)
6. Il lit dans le navigateur, avec TTS Edge si souhaité
7. Sa progression (chapitre + position) est sauvegardée automatiquement en SQLite

---

## main.py — Routes HTTP

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

## core/epub_parser.py — Parseur EPUB

### Rôle
Ouvre un fichier EPUB (zip), en extrait les chapitres dans l'ordre,
les métadonnées (titre, auteur), et la couverture si disponible.

### Fonctions principales
- `get_metadata(epub_path)` — titre, auteur, couverture (bytes)
- `get_chapters(epub_path)` — liste ordonnée {index, titre, texte_brut}
- `get_chapter(epub_path, n)` — texte brut du chapitre N

### Bibliothèque utilisée
`ebooklib` + `BeautifulSoup4` pour le parsing HTML interne des EPUB.

---

## modules/tts.py — Synthèse vocale

### Rôle
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

### Paramètres supportés
- `voice` — identifiant de la voix (ex: fr-CH-ArianeNeural)
- `rate` — vitesse de lecture (ex: +0%, +25%)
- `pitch` — hauteur de la voix (ex: +0Hz, -10Hz, +5Hz) — exposé au frontend
  depuis l'intégration voix multiples (chaque phrase peut avoir son propre
  pitch selon le personnage qui parle)

### Voix françaises disponibles

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

#### Voix Kyutai (35, libres — 12/09/2026)

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

#### La banque de voix Kyutai, en entier (relevé du 12/09/2026)

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

### Fonctions
- `synthesize_stream(text, voice, rate, pitch)` → stream MP3 (Edge TTS)
- `synthesize_bytes(text, voice, rate)` → bytes MP3 complets (Edge TTS)
- `synthesize_kokoro(text, voice, rate, pitch)` → WAV (vitesse native, hauteur post-traitée)
- `synthesize_piper(text, voice, rate, pitch)` → WAV (idem, `length_scale`)
- `synthesize_kyutai(text, voice, rate, pitch)` → WAV (service HTTP local ; vitesse par `audio_rate.py`, hauteur par `_apply_pitch_shift`)
- `KyutaiIndisponible` — exception levée quand le service Kyutai ne répond pas ; transformée en **HTTP 503** par `/api/tts`.

Quelle que soit la branche, l'audio final est **mis en cache disque**
(`modules/tts_cache.py`) sous la clé texte + voix + vitesse + hauteur : un
passage déjà lu ne redemande rien au moteur (voir la section « Cache audio »).

### Nettoyage du texte avant synthèse
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
  avant `?`/`!`/`:`/`;` (typographie française, prononcée naturellement).
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

---

## data/nimm_epub.db — Base SQLite

### Tables

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

## frontend/ — Interface

### Deux vues dans une seule page
- **Bibliothèque** : grille de livres (couverture + titre + auteur), bouton upload
- **Lecteur** : texte du chapitre, navigation chapitres, barre TTS, curseur glitch

### Cartes de livres sur mobile — titre en entier (15/09/2026)
Demande de Laurent : sur son téléphone, la **couverture était rognée** par le
cadre de la vignette et le titre, limité à deux lignes, ne disait pas toujours
de quel livre il s'agissait. Choix retenu (**option A**) : la vignette reste
**recadrée** au format 2/3 (`.book-cover`, `object-fit: cover`) pour garder une
grille régulière, et c'est le **texte sous la vignette** qui rattrape
l'information — sur mobile, `.book-title` ne se limite plus à 2 lignes :
il s'affiche **en entier**, un peu plus grand, et `.book-author` passe à la
ligne au lieu d'être tronqué (`@media (max-width: 640px)`,
`frontend/styles.css`).

### Grille de la bibliothèque — hauteur des lignes (16/09/2026)
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

### Pas de framework
HTML/CSS/JS vanilla. Même approche que NIMM.

### PWA
- manifest.json déclaré dans index.html
- Installable sur l'écran d'accueil Android depuis Chrome
- Fonctionne en plein écran via Tailscale
- `frontend/icon.png` (512×512) et `frontend/apple-touch-icon.png`
  (180×180) — fichiers requis par `manifest.json` et `index.html`,
  absents lors de la création initiale du projet (cause du logo
  générique affiché par Firefox tant qu'ils manquaient). Générés à
  partir du logo NIMM ePub (livre + bouche + ondes sonores, sans texte).

### Accès HTTPS via Tailscale Serve
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

---

## Logique TTS — app.js

### Structure de données
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

### Curseur glitch
- Toujours actif sur une phrase, que le TTS soit en lecture ou non
- Sert de repère visuel au coup d'œil (pas besoin de regarder l'écran)
- Remplace le tooltip "Lire à partir d'ici" sur mobile
- Le tooltip reste disponible sur desktop (sélection de texte → clic)

### Sélection de texte régularisée (desktop, 23/08/2026, 2e passe)
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

### "Lire à partir d'ici" sur mobile (23/08/2026, 2e passe — **modifié le 15/09/2026**)
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

### Panneau « voix de cette phrase » (15/09/2026)
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
- **Changement** : menu des voix construit par `_remplirMenuVoixPhrase()`
  (groupes Femmes / Hommes / Autres, comme la fenêtre du casting). Une voix en
  place mais **non proposée** (moteur éteint) est **ajoutée au menu** avec son
  nom : elle ne peut donc pas être remplacée en silence. Pour un **personnage**,
  l'enregistrement passe par `_updateCharacterVoice()` (route
  `PUT /api/books/{id}/cast/voice`, la même que la fenêtre du casting) —
  elle renvoie maintenant **`true`/`false`** pour que le panneau dise si
  l'enregistrement a réussi ; pour *Narration*, c'est `#voice-select` (voix du
  lecteur) qui est changé. Dans les deux cas, une lecture en cours est
  **relancée** pour que le changement s'entende tout de suite (playlist figée
  par construction, cf. la règle du 15/09/2026).
- **Aperçu** : bouton « ▶ Écouter » (`_apercuVoixPhrase()`) — la voix
  choisie dit un extrait **de la phrase ouverte**, avec la vitesse et la
  hauteur du personnage (celles du lecteur pour la narration) ; si le moteur
  est éteint, le panneau l'indique sans se bloquer.
- **Fermeture** : croix, tap à côté de la feuille, ou touche `Échap`. Le
  panneau est aussi fermé au **changement de chapitre** (les index de phrases
  changent, il pointerait sur la mauvaise phrase).
- **Présentation** : feuille collée en bas d'écran sur mobile (avec l'animation
  `slide-up`), petite fenêtre centrée à partir de 641 px de large
  (`frontend/styles.css`). *Vérification* : `test_voix/test_voix_phrase.js`
  (24 contrôles, sans navigateur).

### Navigation
| Bouton | Action |
|---|---|
| ⏮ | Début du paragraphe précédent |
| ⏪ | Phrase précédente |
| ▶️ / ⏸ | Lecture / Pause depuis le curseur |
| ⏭ | Début du paragraphe suivant |
| `<` / `>` | Chapitre précédent / suivant (encadrent la barre) |

**Le bouton « phrase suivante » ⏩ a été retiré le 15/09/2026** (demande de
Laurent : il faisait doublon avec ⏭, car dans un dialogue un paragraphe fait
souvent une seule phrase). Les commandes du casque et de l'écran verrouillé
(`navigator.mediaSession`, `nexttrack`) continuent d'avancer **d'une phrase** :
elles appellent directement `_cursorSentNext()` au lieu de cliquer sur un
bouton qui n'existe plus. ⏪ reste disponible (reculer d'une phrase reste
utile quand ⏮ saute tout le paragraphe).

La navigation pendant la lecture coupe le TTS en cours et repart
immédiatement depuis la nouvelle position du curseur.

### Préchargement audio (lecture phrase par phrase — session du 08/09/2026)
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

### États TTS
`idle` → `loading` → `playing` ⇄ `paused` → `idle`

Sur pause : le curseur reste sur la phrase en cours.
Sur stop : le curseur reste en place (ne revient pas au début).

### Persistance du curseur
`cursor_idx` est sauvegardé 3 secondes après chaque mouvement du curseur
(via `_setCursor`), en plus des événements scroll et changement de chapitre.
À l'ouverture d'un livre, le curseur glitch est restauré exactement
sur la dernière phrase lue.

### Découpage audio — phrases et sous-segments (session du 08/09/2026)
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

### Pause entre paragraphes
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

## Recherche dans le livre — main.py + app.js

### Rôle
Recherche un mot exact dans l'ensemble des chapitres d'un livre (pas
seulement le chapitre en cours), insensible aux accents et à la casse.

### Backend — `/api/books/{id}/search?q=...`
- Appelle `get_chapters()` pour récupérer tout le texte du livre
- Normalise le texte et la requête (`_normalize_for_search` : minuscules +
  suppression des accents via `unicodedata`)
- Découpe chaque chapitre en paragraphes (`\n\n+`) puis en phrases
  (`_split_sentences`, même logique que côté client)
- Recherche le mot avec bordures de mot (`\b...\b`) → mot exact uniquement,
  pas de correspondance partielle ("chat" ne trouve pas "chaton")
- Retourne pour chaque occurrence : `chapter_index`, `chapter_title`,
  `paragraph_index`, `sentence_text`

### Frontend — panneau chapitres
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

## Effet glitch — styles.css

Animation CSS `@keyframes glitch` sur la classe `.glitch-active` :
- 3 éclairs rapides (~40ms chacun) en début de cycle
- Pause ~500ms
- Cycle total : 0.8s
- Effet : décalage RGB rouge/cyan + flou + déplacement

---

## Mode RSVP (lecture mot-à-mot) — app.js + styles.css

### Contexte
Conçu à l'origine pour aider Maya (difficultés de lecture à voix haute :
anticipation/déformation de mots comme "étant" → "était"). Le mode isole
un mot à la fois pour empêcher le cerveau de deviner la suite à partir du
contexte — elle doit décoder ce qui est réellement écrit.

### Principe — point fixe + lettre pivot
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

### Contrôle — tap pour démarrer / tap pour arrêter
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

### Mode "secours" au relâchement — fondu de contexte
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

### Synchronisation avec le reste de l'appli
- `_rsvpBuildWords()` reconstruit `_rsvpWords[]` à partir de `_sentences[]`
  à chaque ouverture (chaque mot garde son `sentIdx` d'origine)
- `_rsvpFindStartWordIdx()` démarre au mot correspondant à `_cursorIdx`
- Pendant le défilement, `_setCursor(w.sentIdx)` est appelé à chaque mot →
  le curseur glitch (et donc la sauvegarde de progression) reste synchro
- Mutuellement exclusif avec le TTS : `openRSVP()` appelle `_stopTTS()`

### Vue dédiée — `showView()`
`#view-rsvp` est une 3ème vue au même titre que bibliothèque/lecteur.
**Point d'attention** : `showView(name)` doit explicitement gérer les
3 vues (`lib`, `reader`, `rsvp`) — toute nouvelle vue ajoutée à l'avenir
doit être ajoutée dans cette fonction, sinon elle garde sa classe `hidden`
d'origine et s'affiche avec une taille de 0×0 (bug rencontré et corrigé
lors de l'implémentation du RSVP).

---

## Cache busting (mises à jour mobile/PWA)

### Problème
Le navigateur (et plus encore une PWA installée) garde `app.js` et
`styles.css` en cache de façon agressive sur mobile. Sans mécanisme de
contournement, une modification de code peut ne jamais apparaître sur le
téléphone même après plusieurs rechargements classiques.

### Solution — paramètre de version dans index.html
`frontend/index.html` référence les fichiers avec un suffixe `?v=...` :

```html
<link rel="stylesheet" href="/static/styles.css?v=20260630-1" />
<script src="/static/app.js?v=20260630-1"></script>
```

Le navigateur considère une URL différente (`?v=` différent) comme une
ressource différente à retélécharger, ignorant le cache de l'ancienne
version.

### Convention de version
Format `YYYYMMDD`, avec suffixe `-1`, `-2`, etc. si plusieurs sessions de
modification ont lieu le même jour (ex: `20260630`, puis `20260630-1`
pour une deuxième session le même jour).

### Règle de session
**En fin de session, dès que `app.js` ou `styles.css` ont été modifiés**,
monter le numéro de version dans les 2 lignes correspondantes
d'`index.html` avant de commit/push. Réflexe à appliquer systématiquement,
au même titre que la mise à jour de ce fichier `ARCHITECTURE.md`.

---

## START.bat — Lancement

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

## Dépendances Python

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

## Workflow de développement

### Rôles
- **Laurent** — product owner, valide chaque choix avant production de code
- **Claude** — analyse, propose, produit les blocs sur confirmation
- **Cline (VSCode + DeepSeek)** — exécute les blocs dans le projet

### Règles strictes
- Analyse et discussion sans limite — le code, c'est du sur-mesure validé
- Aucun bloc de code produit sans confirmation explicite de Laurent
- Un bloc à la fois, confirmation entre chaque
- Les blocs sont copiables directement dans Cline (FIND/REPLACE)

### Format des blocs

```
⚠️ ## Bloc #XX
➡️ fichier cible : [filename]
**FIND**
[texte exact à trouver — ou "(fichier existant — remplacer tout le contenu)" / "(fichier inexistant — créer)"]
**REPLACE**
[remplacement complet]
```

---

## Ordre de développement des fichiers
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

## Temps de lecture restant

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

## Profils familiaux (multi-utilisateurs) — main.py + index.html + app.js + styles.css

### Rôle
Permet à plusieurs membres de la famille (Laurent, Maya) d'utiliser
NIMM ePub depuis leurs propres téléphones via Tailscale, chacun avec sa
bibliothèque et ses progressions de lecture totalement séparées. Pas de
mot de passe — simple écran "Qui lit ?" au démarrage de l'app.

### Base de données

**Table `users`** (nouvelle) :
```
users (id, name)
```
Remplie automatiquement au premier démarrage si vide : "Laurent" et
"Maya" insérés par `init_db()`.

**Table `books`** : gagne une colonne `user_id INTEGER NOT NULL` —
chaque livre appartient à un seul profil dès sa création (pas de partage
entre profils, chacun uploade indépendamment, y compris pour un même
roman lu par les deux).

**Table `progress`** : la clé primaire passe de `book_id` seul à
**`(user_id, book_id)`** composite. Permet en théorie à deux profils
d'avoir chacun leur progression sur un même `book_id` (même si dans la
pratique actuelle, un livre n'appartient qu'à un profil).

### Routes API
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
(`[{"id":1,"name":"Laurent"}, {"id":2,"name":"Maya"}]`).

### Frontend — écran "Qui lit ?"
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

### Migration
Aucune migration automatique des anciennes données (`books`/`progress`
sans `user_id`) — décision validée : on est repartis d'une base SQLite
vidée manuellement (suppression de `data/nimm_epub.db` et des fichiers
dans `data/library/`) avant le premier démarrage avec la nouvelle
structure.



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

**🔊 Banque de voix (session du 08/09/2026 — pool élargi aux Kokoro)**
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

**🔼 Règle des paliers d'étoiles — session du 15/09/2026** (décision de Laurent ;
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

**Report des notes d'écoute dans les catalogues — étape 3 du listener**
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

**Noms des voix : jamais d'identifiant technique dans les menus**
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
`loadCatalogueVoix`, `_libelleCatalogue`, `_construireMenuVoix`,
`_openCastModal(rafraichirVoix)`). *Vérifications* :
`test_voix/test_libelles_voix.py` (catalogue complet, « Alphonse » pour
`xtts:cml9804`, `dispo` comparé à `/api/moteurs`, et contrôle sur un vrai livre
casté — les 125 personnages d'un roman contemporain ont tous un nom au catalogue) et
`test_voix/test_filtre_genre.js` (cas 7 et 8 : prénom affiché, identifiant
absent).

**Piste ouverte (décidée le 15/09/2026, pas encore faite)** : le geste
« prendre une voix déjà attribuée » — une confirmation en français proposant
**Partager** (l'autre garde la voix, la hauteur est décalée et affichée) ou
**Déplacer** (l'autre personnage passe « à caster »), plus un tiroir des
**voix encore libres** du livre.


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
`piper:tom:0`).

**Ordre du pool automatique (session du 12/09/2026 — Kyutai en tête)**
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

**🎨 NIMM Voix — fournisseur de voix externes (session du 11/09/2026)**

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

**Module voice_casting.py — détail technique**
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
silence. Construction : `_construireMenuVoix()` dans `app.js`.

**Contenu :** un personnage par ligne (`#cast-modal` /
`.cast-row`), triés par nombre de répliques décroissant :
- Nom du personnage (nom canonique tel qu'attribué par Gemini)
- Badge "Homme/Femme · N répliques" (`genre`/`line_count`, stockés en
  base depuis `assign_voices()` → `voice_casting.py`)
- Menu déroulant (`<select>`) listant toutes les voix disponibles
  (`_allVoices`, chargé une fois via `/api/voices`, avec tags nom/genre/région
  déjà présents dans les catalogues côté serveur), voix actuelle
  présélectionnée. Depuis le 12/09/2026, le libellé est construit par
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
- Paramètres → Réseau → VPN → Tailscale → **VPN toujours actif** si proposé.
- Utiliser la **PWA installée** (Ajouter à l'écran d'accueil) plutôt que le
  navigateur classique : meilleur traitement en arrière-plan.

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

### 🔌 Arrêt propre du serveur depuis le launcher
**Idée :** Ajouter un bouton "Arrêter" dans le launcher qui envoie un signal
d'arrêt au serveur EPUB (SIGTERM ou route `/shutdown`). Évite les processus
fantômes qui occupent le port 8081 sans être vraiment actifs.
Le START.bat pourrait aussi tuer automatiquement tout processus sur 8081
avant de démarrer.

### 👨‍👩‍👧 Profils familiaux (multi-utilisateurs)
✅ **Réalisé** — voir section dédiée "Profils familiaux — main.py + index.html
+ app.js + styles.css" plus bas dans ce document.

### 🔤 RSVP — taille de police sur mots longs
Certains mots longs ("traitements", "appréhendé"...) débordent légèrement
du cadre sur mobile en mode RSVP (`#rsvp-word`). Réduire un peu
`font-size` de `#rsvp-word` (actuellement `2.6rem`), ou prévoir une
réduction dynamique selon la longueur du mot affiché.

### 🌫️ RSVP — clarté du fondu de contexte à l'arrêt
Le texte de fondu affiché à l'arrêt (`#rsvp-fade-text`) est jugé confus
visuellement (plusieurs colonnes de texte qui se chevauchent avec le
texte du chapitre en arrière-plan, lisibilité réduite). À revoir : fond
plus opaque derrière le texte de fondu, et/ou repositionnement pour ne
plus se superposer au texte du lecteur visible derrière.

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

### 🎬 Prochaine session — pistes ouvertes
- **🎚️ Réglage du pitch depuis la fenêtre du casting** — demande de
  Laurent le 21/08/2026, pas encore implémenté. Principe : ajouter un
  contrôle de pitch à côté du menu déroulant de voix, par personnage,
  dans `#cast-modal` — la colonne `pitch` existe déjà dans la table
  `voices`, seule l'édition manuelle manque (aujourd'hui uniquement
  écrit automatiquement par `assign_voices()`). **Piège à anticiper** :
  Kokoro n'a pas de paramètre de pitch (contrairement à Edge TTS) — le
  contrôle devra se désactiver/masquer automatiquement quand une voix
  `kokoro:` est sélectionnée pour ce personnage, plutôt que d'envoyer un
  pitch qui n'aura aucun effet.
- **Commit Git** : la quasi-totalité de la session du 21/08 est déjà
  commitée (`245876e "On part sur Deepseek en LLM..."`). Restaient, en
  fin de session, 4 fichiers modifiés non commités : `modules/voice_casting.py`
  (`BATCH_SIZE`, découpage par paquets de 150 phrases), `frontend/app.js`
  (affichage compact `🎭 X/N` du bouton pendant l'analyse), `main.py`
  (profil Nadia, bloc #79) et `frontend/styles.css` (safe-area mobile,
  blocs #80-81). Un nouveau livre a aussi été importé
  dans la bibliothèque.
- Nettoyage de `test_voix/` (scripts de dev devenus obsolètes,
  protégés par `.gitignore`, aucune urgence)
- Continuer à surveiller la qualité perçue des voix Edge TTS "trop
  robotiques" signalée par Laurent après écoute réelle — Kokoro (livré
  ce soir) devrait déjà répondre en partie à ce point, à confirmer à
  l'usage sur plusieurs personnages
- Catalogue de voix devenu long (12 Edge + 54 Kokoro = 66 entrées dans
  les menus déroulants) — si ça devient pénible à parcourir sur mobile,
  prévoir un regroupement visuel par pays (`<optgroup>` ou équivalent)
- Même piège que la fiche de personnages, à surveiller côté tirets de
  dialogue coupés par un `!`/`?` interne (voir section gard citation
  ouverte) — pas encore rencontré en pratique, backlog seulement
- ✅ **Profil Nadia créé** (21/08/2026, bloc #79) : Nadia (l'épouse de
  Laurent) a maintenant son profil (`users`, id 3), avec sa propre
  bibliothèque et sa propre progression de lecture, séparées de Laurent
  et Maya. Ajouté dans `init_db()` avec une garde d'idempotence (n'est
  inséré que si absent) — même mécanique que les profils existants,
  activé immédiatement en exécutant `init_db()` sans attendre le
  redémarrage du serveur.

### ✅ Validation terrain complète — session du 21/08/2026
Système multi-moteur + Kokoro + gard citation ouverte testés de bout en
bout sur le Tome II du Comte de Monte-Cristo en conditions réelles :
20/20 chapitres analysés avec DeepSeek, 56 voix générées (dont la voix
italienne Kokoro pour Pastrini/Vampa), aucune erreur, écoute réelle
confirmée concluante par Laurent.

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
- **voyant** `#moteur-etat` sous les réglages du lecteur : « Voix de
  personnages : Kyutai pret » / « chargement en cours… » / « moteur eteint » ;
  depuis le 15/09/2026 c'est un **bouton** qui ouvre le choix du moteur
  (voir « Changer de moteur » plus bas) ;
- dans la fenêtre du casting, `_construireMenuVoix()` distingue désormais
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

**Garde-fou au démarrage (`START.bat`)** : chaque branche teste d'abord le port
de **l'AUTRE** moteur. S'il tourne déjà, **rien n'est lancé** et la fenêtre le
dit (« pour changer de moteur : bouton en bas de la fenêtre du lecteur »). Le
test `test_voix/test_start_moteur.py` a été complété en conséquence : il vérifie
que chaque branche teste bien les **deux** ports, **l'autre avant le sien**.

**Vérifications livrées** : `test_voix/test_bascule_moteur.py` (50 contrôles,
**sans rien lancer** — les deux moteurs sont simulés en mémoire et le fichier de
réglage est redirigé vers un témoin, remis en place à la fin) et
`test_voix/test_bouton_moteur.js` (31 contrôles : libellé extrait du **vrai**
`app.js`, présence du bouton et de la fenêtre de choix dans `index.html`,
branchements).

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
voix générique partagée.

Aucun livre déjà casté n'est affecté : `assign_voices` ne s'applique qu'aux
nouveaux castings (les voix déjà enregistrées ne sont jamais réécrites).

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

**Vérifications** : `test_voix/test_annotations_voix.py` (**29 contrôles** :
listes annoncées, enregistrement, refus des valeurs inconnues, annotation
remise à zéro, annotation ancienne, redémarrage) et
`test_voix/test_criteres_voix.js` (**20 contrôles**, sans navigateur) : ce
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

## 🎙️ Moteur de voix NeuTTS (livré le 16/09/2026)

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




