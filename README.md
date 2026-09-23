# NIMM ePub

**Un lecteur de livres EPUB qui lit à voix haute — avec une voix différente pour
chaque personnage.**

NIMM ePub s'installe sur un PC et s'utilise depuis n'importe quel appareil du
foyer (téléphone, tablette, autre ordinateur) : le navigateur sert de lecteur,
les livres restent sur le PC. Le programme attribue automatiquement une voix à
chaque personnage d'un roman — c'est le **casting** — puis lit le texte avec
cette voix, chapitre après chapitre, en mémorisant la progression de chaque
lecteur.

> **État du projet** : application personnelle, en usage quotidien chez son
> auteur, **en développement** — le code avance à chaque session, tout n'est pas
> encore fini ni figé. Le dépôt est **public** depuis le 23/09/2026, pour montrer
> le travail ; aucun livre ne l'accompagne (voir juste en dessous). Ce document
> explique ce que fait le programme et comment l'installer sur une nouvelle
> machine.
>
> **Aucun livre n'accompagne le programme.** NIMM ePub lit les fichiers EPUB
> que son utilisateur lui confie ; ces fichiers ne quittent pas son
> ordinateur, et le dépôt du programme ne contient ni livre ni extrait de
> livre — uniquement du code.

---

## Sommaire

- [Ce que sait faire NIMM ePub](#ce-que-sait-faire-nimm-epub)
- [Ce qu'il faut pour l'installer](#ce-quil-faut-pour-linstaller)
- [Installation pas à pas](#installation-pas-à-pas)
- [Démarrage](#démarrage)
- [Se servir de l'application](#se-servir-de-lapplication)
- [Les quatre moteurs de voix](#les-quatre-moteurs-de-voix)
- [Configuration](#configuration)
- [Structure du dépôt](#structure-du-dépôt)
- [Ce qui n'est pas dans le dépôt](#ce-qui-nest-pas-dans-le-dépôt)
- [Dépannage](#dépannage)
- [Licences et attributions](#licences-et-attributions)

---

## Ce que sait faire NIMM ePub

- **Bibliothèque personnelle** : on dépose un fichier EPUB (depuis le téléphone
  ou le PC), il rejoint la bibliothèque avec sa couverture, son titre et son
  auteur. Le fichier reste sur le PC.
- **Plusieurs lecteurs** : chaque personne du foyer a son profil, avec sa propre
  progression — on reprend exactement où on s'était arrêté, sur n'importe quel
  appareil.
- **Lecture à voix haute** avec quatre moteurs de voix au choix (voir plus bas),
  et la voix du narrateur restaurable à tout moment. Les silences de bord
  laissés par les moteurs distants sont rognés avant la mise en cache : environ
  une seconde de blanc en moins entre deux phrases, sans rien installer (le
  découpeur vidéo `ffmpeg` est déjà embarqué par le programme).
- **Casting automatique par IA** : le programme lit le premier chapitre, en
  établit une fiche de personnages qu'il conserve et enrichit au fil du livre,
  puis demande à une IA de donner à chaque personnage une voix cohérente avec
  son genre et son rôle. Quatre fournisseurs au choix — Gemini, DeepSeek,
  Mistral, ou un modèle **local** gratuit (Ollama) — et l'estimation du coût ou
  de la durée s'affiche **avant** de lancer le traitement. Le coût réel est
  maîtrisé (format de réponse compact, mesure faite : ~3 centimes pour
  1 000 phrases).
- **Cohérence des voix** : un personnage garde la même voix d'un bout à l'autre
  du livre, et d'un tome à l'autre lorsqu'on regroupe les tomes d'une même
  série. Les voix peuvent être verrouillées à la main, ou redistribuées
  gratuitement (sans appel à l'IA) autant de fois qu'on veut. Une réplique
  entre guillemets coupée en deux par un `!` ou un `?` intérieur reste
  attribuée au même personnage.
- **Préchargement continu** : pendant la lecture d'une phrase, la suite du
  chapitre se prépare en tâche de fond (deux requêtes simultanées au maximum,
  environ cinq minutes d'avance), pour éviter les blancs entre deux phrases.
- **Lecture assistée (mode RSVP)** : le texte s'affiche mot à mot à point fixe,
  de 100 à 250 mots par minute, avec le contexte qui s'estompe pendant les
  pauses — une aide à la lecture, utile aussi pour l'apprentissage.
- **Cascade de secours** : si un moteur distant refuse un passage (filtre de
  contenu), un second moteur — puis, en dernier recours, un moteur local
  gratuit — relit le passage. Aucun texte n'est perdu.
- **Cache audio sur disque** : un passage déjà lu n'est jamais régénéré
  (quota réglable, les plus anciens fichiers sont purgés automatiquement).
- **Application installable sur le téléphone** (PWA) : icône sur l'écran
  d'accueil, affichage plein écran, écran de veille géré.

---

## Ce qu'il faut pour l'installer

| Élément | Nécessaire ? | Remarque |
|---|---|---|
| Windows 10 ou 11 | oui | les lanceurs fournis sont des fichiers `.bat` (PowerShell/CMD) |
| **Python 3.14** | oui | version du lecteur ; à cocher « Add python.exe to PATH » pendant l'installation |
| Les dépendances du lecteur | oui | une seule commande, voir ci-dessous |
| **Modèles de voix locales** | non | ≈ 550 Mo : sans eux, seules les voix Kokoro et Piper manquent (Edge TTS et Kyutai fonctionnent sans) |
| Clé API Gemini | non | uniquement pour le casting automatique en ligne |
| **Ollama** | non | pour un casting 100 % gratuit et hors ligne (repli automatique) |
| **Python 3.12 + carte NVIDIA** | non | uniquement pour le 4e moteur de voix, Kyutai |

---

## Installation pas à pas

Toutes les commandes se tapent dans une fenêtre **PowerShell** ouverte dans le
dossier du projet (clic droit sur le dossier → « Ouvrir dans le Terminal »).

### 1. Installer Python 3.14

Télécharger Python 3.14 sur [python.org](https://www.python.org/downloads/) et
l'installer **en cochant « Add python.exe to PATH »** pendant l'installation.
Vérifier ensuite :

```powershell
python --version
```

### 2. Installer les dépendances du lecteur

Le plus propre est de les installer dans un **espace isolé** (un
« environnement virtuel ») : rien ne vient toucher au reste de l'ordinateur, et
tout se supprime en effaçant le dossier `venv`.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

C'est la seule installation à faire, une fois pour toutes. Ensuite, si vous
passez par l'environnement virtuel, pensez à l'activer avant de lancer le
programme en ligne de commande, ou lancez-le avec son interpréteur :
`.\venv\Scripts\python.exe main.py`. `START.bat` utilise le Python installé sur
la machine : il convient donc à l'installation « globale » (variante
ci-dessous).

*(Variante sans environnement virtuel, plus directe :
`python -m pip install -r requirements.txt`.)*

Dans les deux cas, ce sont les 14 paquets du lecteur, à versions figées
(environnement de référence : Python 3.14 sous Windows). Pour vérifier après
coup que tout est en place :

```powershell
python test_voix\test_requirements.py
```

### 3. Poser les modèles de voix locales (facultatif)

Ces fichiers ne sont pas dans le dépôt (trop volumineux). Ils se placent **à la
racine du projet**, à côté de `main.py`. Sans eux, le lecteur démarre et
fonctionne normalement : seules les voix Kokoro et Piper sont indisponibles.

**Le plus simple : double-cliquer sur `INSTALLER_VOIX_LOCALES.bat`.** Il
télécharge les 6 fichiers (≈ 550 Mo), reprend tout seul un téléchargement
interrompu, ne refait rien de ce qui est déjà présent et affiche un bilan à la
fin (le détail est écrit dans `installation_voix_locales.log`). Il peut être
relancé autant de fois qu'on veut.

Les mêmes fichiers peuvent aussi être posés à la main, avec les commandes
ci-dessous.

**Kokoro** — modèle et banque de voix (release officielle `kokoro-onnx`) :

```powershell
curl.exe -L -o "kokoro-v1.0.onnx" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
curl.exe -L -o "voices-v1.0.bin" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
```

**Piper** — les trois voix françaises utilisées :

```powershell
foreach ($v in 'siwis','upmc','tom') {
  curl.exe -L -o "fr_FR-$v-medium.onnx"      "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/$v/medium/fr_FR-$v-medium.onnx"
  curl.exe -L -o "fr_FR-$v-medium.onnx.json" "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/$v/medium/fr_FR-$v-medium.onnx.json"
}
```

> **À savoir sur les voix Kokoro.** Le fichier `voices-v1.0.bin` officiel
> contient 54 voix, toutes de langue étrangère (le programme force la
> prononciation française). Le fichier utilisé en service ici en contient 84 :
> 30 timbres français supplémentaires ont été créés dans un atelier séparé
> (« NIMM Voix », non fourni). Avec le fichier officiel, les 30 voix dont le
> nom est français (Mamie, Papi, Narrateur, Enfant, Mystère, Jeune, Amélie,
> Aurore, Chloé…) n'existeront pas : les 54 autres voix Kokoro fonctionnent.

### 4. Renseigner la configuration (facultatif)

Le fichier `data/config.json` contient les clés API et n'est **jamais** publié
(il est exclu du dépôt). Pour le créer, copier le modèle fourni :

```powershell
copy data\config.example.json data\config.json
```

puis l'ouvrir avec le Bloc-notes et remplacer les valeurs. Sans ce fichier, le
lecteur et les voix Edge TTS fonctionnent quand même ; seuls le casting
automatique en ligne et la cascade de secours sont indisponibles.

### 5. Installer le 4e moteur de voix, Kyutai (facultatif)

Ce moteur exige **Python 3.12** (en plus du 3.14 du lecteur) et une **carte
graphique NVIDIA** : il occupe ≈ 3,8 Go de mémoire vidéo quand il est allumé.
Il faut donc, une seule fois :

1. installer Python 3.12 depuis python.org ;
2. double-cliquer sur `kyutai_service\INSTALLER_KYUTAI.bat` (≈ 2,5 Go à
   télécharger, 10 à 20 minutes ; tout est écrit dans
   `kyutai_service\journal_installation.txt`).

Le détail est dans `kyutai_service\LIRE_MOI.md`. Rien n'est obligatoire : sans
ce moteur, les voix des trois autres moteurs restent disponibles.

---

## Démarrage

### Sur le PC

Double-cliquer sur **`START.bat`**. Une fenêtre s'ouvre ; une seconde fenêtre
s'ouvre aussi pour le **moteur de voix lourd** s'il est installé. Puis, dans un
navigateur :

```
http://localhost:8081
```

**Quel moteur de voix est allumé ?** Celui que vous avez utilisé **la dernière
fois** : `START.bat` lit le fichier `data\moteur_voix.txt`, écrit
automatiquement par `DEMARRER_XTTS.bat` (`xtts`) et `DEMARRER_KYUTAI.bat`
(`kyutai`). Pour démarrer **sans** moteur de voix, mettez simplement `aucun`
dans ce fichier.

`START.bat` ne relance jamais un second moteur : si celui-ci répond déjà, il
est laissé en place.

### Depuis le téléphone ou la tablette

Le serveur écoute sur toutes les interfaces du PC (`0.0.0.0:8081`) : sur le même
réseau Wi-Fi, on y accède avec l'adresse locale du PC :

```
http://<adresse-IP-du-PC>:8081
```

Pour connaître cette adresse sur le PC :

```powershell
ipconfig
```

L'application peut ensuite être **installée comme une application** (icône sur
l'écran d'accueil, plein écran) : dans Chrome ou Brave, menu → « Ajouter à
l'écran d'accueil » / « Installer l'application ».

> Depuis l'extérieur du foyer, l'accès se fait par un réseau privé virtuel
> (Tailscale, monté en HTTPS — voir `ARCHITECTURE.md`, section « Accès HTTPS via
> Tailscale Serve »). Ce point n'est pas nécessaire pour une installation
> locale.

### Arrêter

- Le lecteur : fermer la fenêtre du serveur.
- Le moteur Kyutai : fermer sa fenêtre (un gardien intégré libère le port et la
  mémoire de la carte graphique en quelques secondes).

---

## Se servir de l'application

1. **Déposer un livre** — le bouton **Ajouter** place un fichier EPUB dans la
   bibliothèque, depuis le téléphone comme depuis le PC. Le fichier reste sur
   l'ordinateur qui fait tourner le programme.
2. **Choisir son profil** — chaque personne du foyer a le sien ; la progression
   de lecture est gardée séparément et reprise à l'endroit exact.
3. **Écouter** — la lecture à voix haute démarre avec la voix du narrateur ;
   vitesse et hauteur se règlent à tout moment.
4. **Activer les voix par personnage** — le bouton **🎭 Activer voix multiples**
   ouvre la fenêtre « Quel moteur utiliser pour analyser ce livre ? » : Gemini
   (recommandé), DeepSeek, Mistral, ou le **modèle local** gratuit (grisé si
   Ollama n'est pas démarré). L'estimation du coût ou de la durée s'affiche
   **avant** de lancer le traitement.
5. **Corriger au besoin** — la fenêtre du casting permet de changer la voix d'un
   personnage, de la **verrouiller** pour qu'elle survive à un nouveau passage,
   de regrouper les différentes écritures d'un même nom, ou de tout
   redistribuer sans rien payer.
6. **Lire autrement** — le bouton **Mode RSVP** affiche le texte mot à mot à
   point fixe, de 100 à 250 mots par minute (160 par défaut).

---

## Les quatre moteurs de voix

Le moteur est choisi par la voix elle-même, dans les menus du lecteur. Une voix
Edge TTS n'a aucun préfixe ; les autres sont préfixées.

| Préfixe | Moteur | Où il tourne | Voix disponibles | Sortie |
|---|---|---|---|---|
| *(aucun)* | **Edge TTS** | en ligne (Microsoft) | 12 voix françaises | MP3 |
| `kokoro:` | **Kokoro** | local, processeur | 84 (dont 30 créées ici) | WAV |
| `piper:` | **Piper** | local, processeur | 4 (sur 3 modèles) | WAV |
| `kyutai:` | **Kyutai TTS 1.6B** | local, service séparé, carte graphique | 35 voix françaises | WAV |

Tous les moteurs acceptent un réglage de **vitesse**, et de **hauteur** pour
ceux qui en ont un nativement (Edge TTS). Pour Kokoro, Piper et Kyutai, qui
n'en proposent pas, la hauteur est appliquée par le lecteur sur l'audio
produit.

Le moteur **local** est aussi ce qui sert de dernier recours quand un moteur
distant refuse un passage : il est gratuit mais sa restitution à l'écoute est
nettement moins bonne.

---

## Configuration

### `data/config.json` (clés, non publié)

| Clé | Rôle |
|---|---|
| `gemini_api_key` | casting automatique en ligne (moteur principal) |
| `deepseek_api_key` | premier moteur de secours si Gemini refuse un passage |
| `mistral_api_key` | autre moteur de casting possible (non utilisé par défaut) |
| `local_model` | modèle Ollama choisi (ex. `qwen3:8b`) |
| `local_url` | adresse d'Ollama (défaut `http://127.0.0.1:11434`) |

Un modèle prêt à copier est fourni : `data/config.example.json`.

### Variables d'environnement (réglages avancés, facultatif)

| Variable | Défaut | Effet |
|---|---|---|
| `NIMM_TTS_CACHE_GB` | 20 | taille maximale du cache audio (Go) |
| `NIMM_KYUTAI_URL` | `http://127.0.0.1:8082` | adresse du service Kyutai |
| `NIMM_KYUTAI_DELAI` | 240 | attente maximale d'une phrase Kyutai (secondes) |
| `NIMM_KYUTAI_PORT` | 8082 | port du service Kyutai |
| `NIMM_KYUTAI_HOST` | `127.0.0.1` | interface d'écoute du service Kyutai |

---

## Structure du dépôt

```
nimm-epub/
├── main.py                  — serveur web (FastAPI) : toutes les routes de l'application
├── START.bat                — lancement tout-en-un (lecteur + moteur de voix, celui utilisé la dernière fois)
├── INSTALLER_VOIX_LOCALES.bat — télécharge les voix locales Kokoro et Piper (une fois)
├── requirements.txt         — dépendances du lecteur (Python 3.14)
├── core/
│   └── epub_parser.py       — lecture des fichiers EPUB (chapitres, métadonnées, couverture)
├── modules/
│   ├── tts.py               — les quatre moteurs de voix (Edge, Kokoro, Piper, Kyutai)
│   ├── tts_cache.py         — cache audio sur disque (quota réglable)
│   ├── audio_trim.py        — rognage des silences de bord
│   ├── audio_rate.py        — vitesse par post-traitement
│   ├── voice_casting.py     — casting : analyse, fiche de personnages, attribution des voix
│   └── config.py            — lecture de data/config.json (clés API)
├── frontend/                — l'interface, servie au navigateur
│   ├── index.html, app.js, styles.css
│   ├── manifest.json, sw.js — installation en application (PWA)
│   └── piper-tagger.html    — petit outil interne d'étiquetage des voix Piper
├── data/
│   ├── library/             — les livres EPUB déposés (créé au premier lancement)
│   ├── nimm_epub.db         — base SQLite : livres, profils, progression, casting
│   ├── tts_cache/           — cache audio (créé à l'usage)
│   └── config.json          — clés API (non publié ; modèle : config.example.json)
├── kyutai_service/          — le moteur de voix Kyutai, à part (Python 3.12 + PyTorch)
│   ├── INSTALLER_KYUTAI.bat, DEMARRER_KYUTAI.bat, servir_kyutai.py
│   └── LIRE_MOI.md, ATTRIBUTION.md
├── test_voix/               — outils de test et de diagnostic (développement)
├── ARCHITECTURE.md          — la logique en vigueur, en détail
├── BACKLOG.md               — les améliorations notées au fil des sessions
├── JOURNAL.md               — le carnet de session (local, non versionné)
└── README.md                — ce document
```

Le principe de base : **aucun module ne parle directement à un autre**,
`main.py` orchestre tout. Le détail complet est dans `ARCHITECTURE.md`.

---

## Ce qui n'est pas dans le dépôt

Le dépôt ne contient que le **code**. Ce qui suit est volontairement exclu (voir
`.gitignore`) et n'existe que sur la machine :

| Absent | Pourquoi | Comment l'obtenir |
|---|---|---|
| Les modèles de voix (Kokoro, Piper, Kyutai) | volumineux (de 60 Mo à 3,4 Go), téléchargeables | Kokoro/Piper : double-clic sur `INSTALLER_VOIX_LOCALES.bat` ; Kyutai : `kyutai_service\INSTALLER_KYUTAI.bat` (voir la partie « Installation ») |
| Les livres EPUB (`data/library/`) | volumineux, et la plupart sous droits d'auteur | c'est l'utilisateur qui apporte ses livres |
| La base `data/nimm_epub.db` | données personnelles (profils, progression, casting) | se crée toute seule au premier lancement |
| `data/config.json` | contient des clés API privées | copier `data/config.example.json` |
| Le cache audio (`data/tts_cache/`) | se régénère tout seul | sans objet |
| Les environnements Python (`.venv`, `kyutai_service\.venv`) | 4,5 Go, se recréent | voir les commandes d'installation |

---

## Dépannage

| Ce qu'on voit | Cause probable | Quoi faire |
|---|---|---|
| `No module named 'fastapi'` (ou autre) au démarrage | dépendances non installées | `python -m pip install -r requirements.txt` |
| `Fichier data/config.json introuvable` | fichier de configuration absent | `copy data\config.example.json data\config.json` |
| `La cle Gemini n'est pas configuree` | clé vide ou restée à la valeur d'exemple | renseigner `data/config.json` |
| Une voix Kokoro ou Piper ne produit rien | modèle correspondant absent de la racine du projet | voir l'étape 3 de l'installation |
| `Moteur local injoignable` | Ollama n'est pas démarré | lancer Ollama, ou choisir un autre moteur de casting |
| Le port 8081 est déjà occupé | un autre serveur tourne déjà sur le PC | fermer la fenêtre du serveur existante |
| Les voix Kyutai sont indisponibles | moteur non installé, éteint, ou Python 3.12 absent | voir l'étape 5 de l'installation |
| VS Code souligne `moshi.models.tts` en rouge dans `kyutai_service` | faux positif : ce dossier est analysé avec le Python 3.14 du lecteur | sans effet sur le fonctionnement (voir `LIRE_MOI.md`) |

---

## Licences et attributions

### Le programme lui-même

NIMM ePub est distribué sous **GPL-3.0** : le texte officiel de la licence est
dans le fichier `LICENSE`, à la racine du dépôt.

En clair : n'importe qui peut utiliser, modifier et partager ce programme,
gratuitement ; en échange, celui qui le redistribue — modifié ou non — doit
publier son code source sous la même licence. Personne ne peut donc refermer
ce travail.

Ce choix n'est pas seulement une préférence : plusieurs composants utilisés sont
sous **GPL-3.0** (`piper-tts`, `pedalboard`, `phonemizer-fork`) ou **AGPL-3.0**
(`EbookLib`), ce qui impose de distribuer le programme avec son code source. Une
licence permissive de type MIT serait ici trompeuse.

### Les composants tiers

| Composant | Licence |
|---|---|
| **Edge TTS** (voix en ligne, Microsoft) | service en ligne ; paquet `edge-tts` : LGPL-3.0 |
| **Kokoro** — modèle | Apache-2.0 (`hexgrad/Kokoro-82M`) |
| **Kokoro** — bibliothèque `kokoro-onnx` | MIT |
| **Piper** — code | MIT (`rhasspy/piper`) ; paquet `piper-tts` : GPL-3.0 |
| **Piper** — voix françaises | MIT (`rhasspy/piper-voices`) |
| **Kyutai TTS 1.6B** — poids | **CC BY 4.0 — attribution obligatoire** (Kyutai) |
| **Kyutai** — voix françaises (`cml-tts/fr`) | **CC BY 4.0 — attribution obligatoire** (Kyutai + jeu de données CML-TTS) |
| **Kyutai** — code `moshi` | MIT |
| **PyTorch** | BSD-3-Clause |
| **FastAPI**, **uvicorn**, **onnxruntime**, **BeautifulSoup** | MIT |
| **EbookLib** | AGPL-3.0-or-later |
| **pedalboard** (hauteur) | GPL-3.0 |
| **imageio-ffmpeg** (rognage, vitesse) | BSD-2-Clause (binaire ffmpeg : licence propre à la version embarquée) |

Les attributions détaillées du moteur Kyutai — dont l'attribution obligatoire
CC BY 4.0 — sont dans `kyutai_service/ATTRIBUTION.md` ; ce fichier doit rester
avec les fichiers concernés.

### Les livres

Le programme est distribué **seul** : ni livre, ni extrait de livre, ni
enregistrement audio ne l'accompagnent — c'est l'utilisateur qui apporte ses
propres fichiers EPUB, et ceux-ci restent chez lui. Un ouvrage acheté autorise
un usage privé, **pas** une mise à disposition du public : les enregistrements
produits à partir d'une œuvre sous droits ne peuvent pas être diffusés, quelle
que soit la voix utilisée. Seules les œuvres du domaine public peuvent l'être.





