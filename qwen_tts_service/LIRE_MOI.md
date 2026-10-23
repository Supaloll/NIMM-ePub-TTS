# Le moteur de voix Qwen3-TTS — mode d'emploi

Ce dossier contient **l'appareil de voix Qwen3-TTS** de NIMM ePub : un
programme séparé du lecteur, qui fait parler **les voix françaises libres de la
garde-robe** — **218 extraits au 21/10/2026**, dont les 35 mêmes que Kyutai
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
| **voix/** | — | la **garde-robe partagée** : les extraits (WAV) — **218 au 21/10/2026** — **et** leur texte exact (`references.csv`) |

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

## Les 3 voix de série (16/10/2026) — retirées le 17/10/2026

Trois extraits déposés par Laurent (« Voix à faires » de NIMM Voix) ont été
clonés par `qwentts.cpp` le 16/10/2026 : **Thyrion**, **Sersei** et **Saul** —
des voix de séries anglaises, qu'il a gardées parce qu'elles lui font penser aux
originales. Chaque clone dit **100 % du texte de contrôle** (41/41 mots). La
garde-robe était passée de **201 à 204 extraits**.

**Elles en ont été RETIRÉES le 17/10/2026** (demande de Laurent : « on va faire
mieux plus tard ») : les 3 WAV sont sortis de `voix/` et le tuple
`_VOIX_SERIES_16_10_2026` de `modules/tts.py` est **vide** depuis. La garde-robe
est donc revenue à **201** ce jour-là — et seuls leurs fichiers de sauvegarde
témoignent encore de leur passage.

- leur **identifiant** est le nom du fichier (`Thyrion`, `Sersei`, `Saul`) ;
- à l'écran : le **nom du personnage**, le **drapeau français** (`🇫🇷` — voix
  **françaises**, pas « étrangères » : précision de Laurent, 16/10/2026, donc
  **aucun second drapeau**) et **0 étoile** → **hors casting automatique**, mais
  **choisissables à la main** (même convention que les voix indiennes et
  Maya) ;
- **droits** : ce sont les voix d'**acteurs** d'œuvres du commerce → **usage
  privé dans l'atelier**, comme les extraits issus de livres audio du commerce.
  Leurs 3 textes avaient été mis dans `references_privees.csv`, le fichier
  **PRIVÉ (hors dépôt)** — ce sont des répliques de dialogues sous droits, et la
  règle du projet est qu'aucun texte de ce genre ne part sur le dépôt (même
  raison que pour Maya). **Ils ont été retirés le 17/10/2026** en même temps que
  les voix : le fichier privé ne contenait plus que `Maya_normale` avant
  l'arrivée des 5 voix du 19/10/2026 (copie datée du retrait :
  `references_privees.csv.bak_avant_retrait_voix_serie_20261018_1302`) ;
- l'entrée a été faite par `_essais/_entrer_voix_series_20261016.py`, avec une
  **copie datée** du fichier de textes avant
  (`references.bak_avant_thyrion_sersei_saul_20261016.csv`).

## Les 5 voix du 19/10/2026 : la garde-robe passe à 206

NIMM Voix a cloné **cinq voix françaises** de plus avec `qwentts.cpp` (mode
ICL), à partir de cinq extraits déposés par Laurent le 19/10/2026 : **Aldo**,
**Gus**, **Jesse**, **Vergès** et **Sandor**. « 5/5 » à l'oreille pour les quatre
premières, « le 04, D, est top » pour Sandor. Quatre clones sur cinq disent
**41/41 mots** du texte de contrôle ; **Jesse** en dit 40/41 (« qu'il » entendu
« qu'elle »).

- **identifiants** = nom du fichier, donc `Aldo`, `Gus`, `Jesse`, `Verges`
  (sans accent, comme le fichier), `Sandor` ; à l'écran « Vergès » garde
  l'accent ;
- **format des références** : 24 kHz, mono, PCM 16 bits, 16,4 à 20,4 s ;
- à l'écran : **drapeau français** et **aucun second drapeau** (même précision
  de Laurent que pour les voix de série), **0 étoile** → **hors casting
  automatique**, mais **choisissables à la main** ;
- **droits** : voix d'**acteurs de doublages** (œuvres du commerce) → **usage
  privé dans l'atelier**. Leurs **5 textes sont dans `references_privees.csv`**
  (le fichier **hors dépôt**), **jamais** dans `references.csv` : répliques de
  dialogues sous droits, et un texte commité reste dans l'historique Git ;
- **entrée faite** par `_essais/_entrer_5_voix_20261019.py` (rapport seul par
  défaut, `--ecrire` pour agir, idempotent), avec **copie datée automatique**
  du fichier privé avant l'écriture :
  `references_privees.csv.bak_avant_5voix_20261019`, et copie de `modules/tts.py`
  (`modules/tts.py.bak_avant_5voix_20261019`).

**Deux formats à ne pas mélanger** : le **public** `references.csv` est en
**CRLF** (213 lignes au 21/10 : en-tête + 212 voix), le **privé**
`references_privees.csv` est en **LF** (7 lignes au 19/10 : en-tête + Maya +
les 5 voix). Les deux sont en **UTF-8 sans BOM**, et l'outil d'entrée vérifie
ces trois points après écriture.

## Les 12 voix MLS du 20/10/2026 : la garde-robe passe à 218

NIMM Voix a cloné **28 lecteurs français du corpus MLS** (Meta / LibriVox,
**CC BY 4.0**) — des livres audio du domaine public. Laurent en a **retenu 24 à
l'oreille**, mais **9 d'entre eux étaient déjà ici** sous un identifiant `cml` :
c'est le **même lecteur LibriVox**, sur un autre passage, donc **le même
timbre**. Il ne restait donc que **15 timbres vraiment neufs (13 femmes,
2 hommes)**.

**Douze sont entrés le 21/10/2026** : Albertine, Angèle, Clémence, Antoinette,
Élise, Bernadette, Denise, Léonie, Margot, Germaine, Marcelle et Rose.

- **les 3 autres attendent** que NIMM Voix corrige leur **texte de référence**
  (MLS_5232_F, MLS_1817_H, MLS_2904_H) : un texte qui ne colle pas à l'audio fait
  **bégayer le clone**. Ce sont les **deux seuls hommes** du lot — la garde-robe
  n'a donc **pas gagné de timbre masculin** ce jour, et NIMM Voix propose d'en
  sortir d'autres sur simple demande (sa réserve MLS compte plus de 66 lecteurs) ;
- **dix prénoms du mémo étaient déjà pris** dans le catalogue (Amélie =
  `ff_amelie`, Delphine = `ff_delphine`, Solange = `Femme002`, Firmin =
  `homme_grave_6546546`…) : Laurent a validé les **remplaçants** ci-dessus. Le
  relevé est fait par `_essais/_verif_voix_mls_20261021.py` ;
- **0 étoile** → **hors du casting automatique**, mais **choisissables à la
  main** : ces voix sont faites pour les **petits rôles** (moins de
  `MINOR_THRESHOLD` = 8 répliques), et un figurant ne doit pas voler la voix
  d'un personnage principal ;
- à l'écran : **drapeau français**, plus « accent paysan » (Bernadette) et
  « accent québécois » (Denise) ;
- **format des références** : 24 kHz, mono, PCM 16 bits, 17,6 à 20,2 s ;
- **droits** : MLS est en **CC BY 4.0** → attribution « **MLS / LibriVox** »
  obligatoire en cas de diffusion. Ce sont des **personnes réelles** : la licence
  du corpus règle le droit du **fichier**, pas celui de la **voix** (droit de la
  personnalité, plus strict en France). Usage privé de l'atelier : OK ;
  **prudence avant tout partage large** ;
- **entrée faite** par `_essais/_entrer_voix_mls_20261021.py` (**rapport seul**
  par défaut, `--ecrire` pour agir, idempotent, **copies datées automatiques** de
  `references.csv` et de `data/annotations_voix.json` avant écriture), avec
  `_essais/_verifier_import_mls_20261021.py` pour le contrôle après coup et la
  copie datée `modules/tts.py.bak_avant_mls_20261021` ;
- **fiches d'écoute créées à 0 étoile** : elles ne devinent **rien** (âge,
  timbre, débit restent vides) — c'est l'oreille de Laurent qui les remplira.

## L'environnement Python (à lire avant de s'inquiéter)

Le lanceur cherche **dans cet ordre** :

1. `qwen_tts_service\.venv` — l'environnement **installé ici**, le jour où on
   l'aura (c'est la cible : plus aucune dépendance à l'atelier voisin) ;
2. `G:\NIMM Voix\outils\qwen3_tts\.venv` — l'environnement de **l'autre
   atelier**, utilisé pour l'essai du 26/09/2026. Rien n'y est écrit : on
   **emprunte** seulement son Python.

Si aucun des deux n'existe, le lanceur le dit et s'arrête : il n'installe et ne
télécharge **jamais** rien tout seul.
