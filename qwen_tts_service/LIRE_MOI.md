# Le moteur de voix Qwen3-TTS — mode d'emploi

Ce dossier contient **l'appareil de voix Qwen3-TTS** de NIMM ePub : un
programme séparé du lecteur, qui fait parler **les voix françaises libres de la
garde-robe** — **201 extraits au 10/10/2026**, dont les 35 mêmes que Kyutai
(mêmes extraits, donc mêmes timbres et mêmes prénoms) — avec le moteur
**Qwen3-TTS** d'Alibaba.

Arrivé le **26/09/2026**, après l'essai mené dans l'atelier NIMM Voix : Laurent
a trouvé la version Qwen **au-dessus de Kyutai**, déjà très bon. Son intérêt
propre : **Apache-2.0 sur le code et les poids**, donc une voix **partageable**
— ce qu'XTTS v2 (non commercial) ne permet pas.

## Pourquoi un dossier séparé

Comme Kyutai, ce moteur a besoin de **Python 3.12 et de PyTorch**, alors que le
lecteur tourne sur **Python 3.14** : les deux ne peuvent pas cohabiter dans le
même programme. L'appareil travaille donc dans son coin et le lecteur l'appelle
par le réseau (`http://127.0.0.1:8086`), comme il appelle Edge TTS.

## Un seul moteur lourd à la fois

La carte graphique a 8 Go, et **Kyutai comme Qwen en demandent ~3,8 Go** : ils
ne tournent **jamais ensemble**. Le bouton « Voix de personnages » du lecteur
éteint l'un avant d'allumer l'autre, et `START.bat` rallume celui que
`data\moteur_voix.txt` a retenu.

| Fichier | Quand | Ce qu'il fait |
|---|---|---|
| **DEMARRER_QWEN_TTS.bat** | pour allumer le moteur (seul, ou appelé par `START.bat`) | charge le modèle (≈ 5 s) puis reste ouvert |
| **servir_qwen_tts.py** | — | le service lui-même (routes `/sante`, `/voix`, `/tts`) |
| **tester_service.py** | après une installation, ou en cas de doute | vérifie que le service répond et fait dire une vraie phrase |
| **voix/** | — | la **garde-robe partagée** : les extraits (WAV) — **201 au 10/10/2026** — **et** leur texte exact (`references.csv`) |

**Pour éteindre le moteur, il suffit de fermer sa fenêtre** : un « gardien »
intégré au service s'arrête dès que la fenêtre disparaît (même mécanisme que
Kyutai, vérifié le 12/09/2026). Le lecteur continue de fonctionner : seules les
voix `qwen:` deviennent indisponibles.

## Ce qui est différent de Kyutai (à savoir avant de juger)

1. **Il faut le texte de l'extrait** : Qwen clone avec l'extrait **et** ce qui
   y est dit. Les textes sont fournis par la copie de l'atelier NIMM Voix
   (`voix/references.csv`). Un extrait sans texte est **ignoré** et annoncé.
2. **L'empreinte d'une voix se calcule ici** (0,7 à 1,4 s), à la première
   demande, puis reste en mémoire. Kyutai, lui, recevait ses empreintes toutes
   prêtes (256 Ko par voix).
3. **Il rend parfois une phrase vide** (0,36 s de silence, 2 à 5 % des cas) :
   le service **relance** la phrase, deux fois au besoin — réglage
   `NIMM_QWEN_REPRISES`.
4. **Pas de flux (streaming)** dans la bibliothèque installée (`qwen-tts`
   0.1.1) : l'audio sort **d'un bloc**, donc **2 à 4 s avant le premier son**
   d'un chapitre. C'est le **préchargement du lecteur** qui encaisse ce délai.
5. **Le « contexte glissant » n'existe pas ici** : la fin de la phrase
   précédente (envoyée à Kyutai depuis le 17/09/2026) est reçue, **ignorée**,
   et le service le dit une fois dans sa fenêtre.

## Les 18 voix indiennes (10/10/2026)

NIMM Voix a fabriqué **18 voix « indiennes »** pour lire *Shantaram* : des
timbres montés en mélangeant les **4 voix hindi de Kokoro** à des voix
espagnoles, italiennes et anglaises, puis **clonés** par `qwentts.cpp`. Laurent
les a gardées à l'oreille (72 extraits écoutés, 24 retenues, puis un élagage
mesuré en a gardé 18 : 10 hommes, 8 femmes) et les **18 clones disent tout le
texte** (41/41 mots, vérifié par transcription). Elles sont **entièrement
synthétiques** (Kokoro, Apache-2.0), donc **partageables**.

Ce qu'il faut savoir :

- leur **identifiant** commence par `hindi_` (ex. `hindi_h17_enfant`) : c'est le
  **nom du fichier**, et c'est ce que le moteur appelle ;
- à l'écran, elles portent un **prénom indien** et le **drapeau indien** (`🇫🇷🇮🇳`)
  — `modules/tts.py`, catalogue `QWEN_VOICES` ;
- elles sont **classées « étranger »** et notées **0 étoile** à l'import : cela
  les **écarte du casting automatique**, tout en les gardant **choisissables à
  la main** (même convention que les voix à accent du 20/09/2026) ;
- leurs 18 lignes de texte sont dans `references.csv`, le fichier **public**.

Le détail de la recette et des droits est dans le mémo de NIMM Voix
(`MEMO_FAMILLE_HINDI_10-10-2026_pour_la_session_NIMM_ePub.md`).

## L'environnement Python (à lire avant de s'inquiéter)

Le lanceur cherche **dans cet ordre** :

1. `qwen_tts_service\.venv` — l'environnement **installé ici**, le jour où on
   l'aura (c'est la cible : plus aucune dépendance à l'atelier voisin) ;
2. `G:\NIMM Voix\outils\qwen3_tts\.venv` — l'environnement de **l'autre
   atelier**, utilisé pour l'essai du 26/09/2026. Rien n'y est écrit : on
   **emprunte** seulement son Python.

Si aucun des deux n'existe, le lanceur le dit et s'arrête : il n'installe et ne
télécharge **jamais** rien tout seul.
