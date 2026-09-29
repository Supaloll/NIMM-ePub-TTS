# Le moteur de voix Qwen3-TTS — mode d'emploi

Ce dossier contient **l'appareil de voix Qwen3-TTS** de NIMM ePub : un
programme séparé du lecteur, qui fait parler **les 35 mêmes voix françaises
libres que Kyutai** (les mêmes extraits, donc les mêmes timbres et les mêmes
prénoms) avec le moteur **Qwen3-TTS** d'Alibaba.

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
| **voix/** | — | les 35 extraits (WAV) **et** leur texte exact (`references.csv`) |

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

## L'environnement Python (à lire avant de s'inquiéter)

Le lanceur cherche **dans cet ordre** :

1. `qwen_tts_service\.venv` — l'environnement **installé ici**, le jour où on
   l'aura (c'est la cible : plus aucune dépendance à l'atelier voisin) ;
2. `G:\NIMM Voix\outils\qwen3_tts\.venv` — l'environnement de **l'autre
   atelier**, utilisé pour l'essai du 26/09/2026. Rien n'y est écrit : on
   **emprunte** seulement son Python.

Si aucun des deux n'existe, le lanceur le dit et s'arrête : il n'installe et ne
télécharge **jamais** rien tout seul.
