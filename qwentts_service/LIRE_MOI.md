# `qwentts_service/` — le moteur de voix Qwen3-TTS en C++/GGML

**En une phrase** : c'est le moteur qui fait parler les voix `qwen:` du lecteur.
Il porte Qwen3-TTS **en C++/GGML** (le portage `qwentts.cpp`), donc **sans
PyTorch**. **Par défaut il tourne sur le processeur** (il cohabite alors avec
Kyutai et Pocket) ; depuis le **01/10/2026** il peut aussi tourner sur la
**carte graphique** — bouton `DEMARRER_QWENTTS_CPP_GPU.bat`, avec **repli
automatique** sur le processeur si la carte manque.

**Validé à l'oreille** par Laurent le **28/09/2026**, sur un banc d'écoute
100 % Qwen (le chapitre d'essai, 15 personnages et le narrateur) : « c'est
vraiment bon, pas d'accrocs, prosodie impec, on a notre moteur ! »

## Comment il s'allume

- **En usage normal : rien à faire.** `START.bat` l'allume tout seul, comme
  Pocket, et le veilleur du lecteur le rallume s'il s'endort. Son port est le
  **8086** — celui que le lecteur appelle **par défaut** : aucune variable
  d'environnement n'est nécessaire.
- **À la main**, pour voir ce qu'il raconte : double-clic sur
  `DEMARRER_QWENTTS_CPP.bat`. La fenêtre qui s'ouvre **est** le moteur :
  **la fermer l'éteint**.

## Ce qu'il faut savoir

| | |
|---|---|
| Port | **8086** (`NIMM_QWENTTS_PORT` pour le changer) |
| Voix | les **218 références** de `../qwen_tts_service/voix/` — le dossier est **partagé** (même matériau, avec le texte exact qui active le mode ICL) : **35** extraits Kyutai/CML-TTS, **94** Kokoro et **28** « Découpage OK » (copiés le 28/09/2026), **25** CML-TTS « cml_restants » (30/09/2026), **18** voix indiennes `hindi_*` (10/10/2026), les **5 voix du 19/10/2026** (`Aldo`, `Gus`, `Jesse`, `Verges`, `Sandor`), les **12 voix MLS** du 21/10/2026 (`MLS_*`) et la voix privée **Maya** — les **3 voix de série** du 16/10 (`Thyrion`, `Sersei`, `Saul`) ont été **retirées le 17/10/2026** |
| Modèles | **Q4_K_M depuis le 29/09/2026** (629 + 255 Mo), choisis **à l'oreille par Laurent** : « les plus jolies à l'oreille, prosodie et clarté un demi-cran au-dessus ». Les **Q8_0** (947 + 278 Mo) restent sur le disque en **repli automatique** |
| Réglages | 6 cœurs, **4 fils de codec**, tranches de **2 images**, priorité d'entame |
| Débit mesuré | **×1,0 à ×1,2 le temps réel** (Q4_K_M, 29/09/2026) — avant, ×0,94 avec les Q8_0 (28/09) |
| Mémoire | **884 Mo de fichiers** (Q4_K_M) ; sur le processeur : aucune carte ; sur la carte : **~3,7 Go de mémoire vidéo** |

## Depuis le 01/10/2026 : le moteur peut tourner sur la CARTE GRAPHIQUE

Deux façons de l'allumer — **le même service**, le même port, les mêmes voix :

- `DEMARRER_QWENTTS_CPP.bat` → **processeur** (le défaut, inchangé) ;
- `DEMARRER_QWENTTS_CPP_GPU.bat` → **carte graphique** (Q4_K_M). Mesure du
  01/10/2026 : **×3,9 sur une phrase courte** (3,7 s d'audio en 0,9 s), ~**3,7 Go
  de mémoire vidéo**, moteur chargé en ~5 s.

**Si la carte échoue, le service reprend tout seul sur le processeur** (il ne
s'arrête jamais) : `/sante` porte alors `repli: true` avec la raison. Ce sont les
réglages `NIMM_QWENTTS_MOTEUR=gpu` et `NIMM_QWENTTS_VARIANTE=Q4_K_M` qui le
demandent ; le **garde-fou anti-dérive** a été renforcé en même temps (plafond
d'images **540** = 43,2 s + relance **coupée en deux**). Retour au processeur :
fermer la fenêtre, puis `DEMARRER_QWENTTS_CPP.bat`.

## Depuis le 29/09/2026 : le modèle allégé **Q4_K_M** (choisi à l'oreille)

Laurent a écouté les **deux quantifications du même moteur, côte à côte** (banc
`test_voix/LANCER_BANC_ECOUTE_QWENTTS_Q4.bat` : 2 voix, 2 phrases par voix, même
phrase et mêmes réglages, fichiers `A = Q8_0` et `B = Q4_K_M`). Verdict, mot pour
mot :

> « Les versions Q4_K_M sont les plus jolies à l'oreille. La prosodie et la
> clarté sont un demi-cran au-dessus. »

La mesure dit la même chose : **+20 % de débit en moyenne** (+7 % à +46 % selon la
phrase), pour des durées d'audio équivalentes — le candidat **ne dérape pas**.

**Ce qui a changé** : `servir_qwentts_cpp.py` charge les GGUF **Q4_K_M**. Rien
d'autre — ni le lecteur, ni le contrat (`/sante`, `/voix`, `/tts`), ni les voix.

**Comment revenir aux Q8_0**, du plus simple au plus explicite :

1. **supprimer les deux fichiers Q4** de `models/` : le service retombe **tout
   seul** sur les Q8_0, et le dit dans sa fenêtre ;
2. poser `NIMM_QWENTTS_MODELES=q8` avant de lancer le moteur ;
3. reprendre `servir_qwentts_cpp.py.bak_avant_bascule_q4_20260929`.

**Ce que ça ne règle pas** : la **première phrase d'une voix** reste lente (9,2 à
9,5 s mesurés le 29/09) — c'est l'empreinte à préparer, pas la vitesse de calcul.

## Les 25 voix CML-TTS « cml_restants » (30/09/2026) : la garde-robe passe à 183

NIMM Voix a cloné les **25 voix CML-TTS qui restaient** (« vague 6 ») et les a
déposées ici le 30/09/2026 avec un mémo (`_MEMO_25_VOIX_CML_20260930/`) et leurs
textes. Résultat : la garde-robe passe de **158 à 183 voix**, `/voix` annonce
**183** (vérifié) et les 25 nouveaux extraits répondent (essai du 30/09 :
4,6 à 5,9 s d'audio pour une phrase de 70 caractères, aucun dérapage).

**Ce ne sont PAS des voix nouvelles** : ce sont les jumelles Qwen des 25 voix
`xtts:cmlXXXX` versées le 14/09/2026 — même extrait, donc même timbre et même
prénom (`xtts:cml3344` → `qwen:cml3344`). Laurent les a **réécoutées le
30/09/2026** et en a renoté 12 : **c'est son verdict du 30/09 qui figure au
catalogue**, pas les étoiles du 14/09.

Ce qu'il faut savoir :

- **quatre références ont été reprises** (`cml2771`, `cml3182`, `cml5526`,
  `cml7239`) : les premières commençaient au milieu d'un mot — c'est le défaut
  de bord déjà connu, le moteur recopie le tout début de la référence au début
  de chaque phrase ;
- **`cml7614` est une voix d'ENFANT** (« Gustave ») : `age` et `rôle` « enfant »
  dans les annotations d'écoute ;
- **droits : CC BY 4.0** (banque CML-TTS de Kyutai), attribution obligatoire
  « Kyutai + CML-TTS » — voir `ATTRIBUTION.md`, dans `qwen_tts_service/`. C'est
  l'inverse de `Maya_normale`, qui reste privée ;
- **piège de format, à ne pas refaire** : le `references.csv` de la garde-robe
  est en **UTF-8 sans BOM** et, **depuis début octobre, en fins de ligne CRLF**
  (relevé du 16/10/2026 : **204 CRLF, aucun LF seul** ; **201** depuis le retrait
  des 3 voix de série le 17/10, toujours en CRLF) — le relevé du 29/09 qui
  disait « LF » ne vaut donc plus, et la sauvegarde d'avant le lot hindi (celle
  du 03/10/2026) était **déjà** toute en CRLF. Le piège reste entier : Python
  traduit `\n` en `\r\n` sous Windows, donc **tout outil qui écrit ce fichier
  doit surveiller ses fins de ligne** (l'outil de fusion
  `_essais/_fusionner_textes_qwen.py` écrivait du CRLF sans le vouloir, corrigé
  le 30/09/2026 par `newline=''` ; l'outil d'entrée des voix du 16/10/2026, lui,
  écrit du CRLF **volontairement** et le vérifie).

## Les 18 voix indiennes (10/10/2026) : la garde-robe est passée à 201

NIMM Voix a fabriqué **18 voix « indiennes »** pour lire *Shantaram* et les a
déposées ici le 10/10/2026 avec leur paquet et leur mémo
(`MEMO_FAMILLE_HINDI_10-10-2026`, dossier `passerelle_NIMM_ePub`). La garde-robe
est passée de **183 à 201 voix**, et `/voix` annonçait **201** — elle est à
**206** depuis le 19/10/2026 (après un aller-retour par 204 le 16/10, puis le
retrait des 3 voix de série le 17/10 ; voir « Les 5 voix du 19/10/2026 »), puis à
**218 depuis le 21/10/2026** (les 12 voix MLS ; voir « Les 12 voix MLS du
21/10/2026 »).

- **ce ne sont PAS des timbres existants** : ce sont des **mélanges** des 4 voix
  hindi de Kokoro (`hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`) avec des voix
  espagnoles, italiennes et anglaises, puis **clonés** par `qwentts.cpp` ;
- **18/18 clones disent TOUT le texte** (41/41 mots, vérifié par transcription) ;
- **droits** : 100 % synthétiques (Kokoro, Apache-2.0), **partageables** — leurs
  textes vont donc dans `references.csv` (le public), jamais dans le privé ;
- **nom affiché** : un **prénom indien** ; l'**identifiant** reste `hindi_*` (le
  nom du fichier, comme NIMM Voix les connaît) ;
- **classement** : rôle « étranger », **0 étoile** à l'import → **hors casting
  automatique**, mais **choisissables à la main** (même convention que les voix
  à accent du 20/09/2026) ;
- **deux références** (`hindi_h13_adulte`, `hindi_h14_adulte_aigu`) commencent
  au mot « se » (« se couchait derrière les collines… ») : texte et audio
  restent cohérents entre eux, c'est ce qui compte pour l'ICL (signalé par
  NIMM Voix) — un recoupement est possible depuis la source si besoin.

## Les 3 voix de série (16/10/2026) : passées à 204, retirées le 17/10/2026

Laurent a déposé trois extraits dans « Voix a faires » de NIMM Voix (Saul,
Sersei, Thyrion) et les a fait cloner par `qwentts.cpp` le 16/10/2026 : ce sont
des voix de séries anglaises, gardées à l'oreille — « elles ressemblent bien aux
originales ». Les **trois clones disent 100 % du texte de contrôle** (41/41 mots,
relus par Whisper), et la garde-robe est passée de **201 à 204 voix**.
**Elles ont été RETIRÉES le 17/10/2026** (demande de Laurent : « on va faire mieux
plus tard ») : les 3 WAV sont sortis du dossier et le tuple
`_VOIX_SERIES_16_10_2026` de `modules/tts.py` est **vide** depuis — la garde-robe
est revenue à **201** ce jour-là.

- leur **identifiant** est le nom du fichier : `Thyrion`, `Sersei`, `Saul`
  (l'orthographe est celle de Laurent, pas celle des séries) ;
- à l'écran, elles portaient **le nom du personnage** et le **drapeau français**
  (`🇫🇷`) — ce sont des voix **françaises**, pas des voix « étrangères »
  (précision de Laurent, 16/10/2026), donc **aucun second drapeau** :
  `modules/tts.py`, catalogue `QWEN_VOICES` ;
- **0 étoile** à l'import → **hors casting automatique**, mais
  **choisissables à la main** (même convention que les voix indiennes et Maya) ;
- leurs 3 lignes de texte étaient dans `references_privees.csv`, le fichier
  **PRIVÉ (hors dépôt)** : leurs répliques sont des **dialogues d'œuvres sous
  droits**, et la règle du projet est qu'aucun texte de ce genre ne part sur le
  dépôt (même raison que pour Maya). **Retirées le 17/10 avec les voix** : le
  fichier privé ne contenait plus que `Maya_normale` avant le lot du 19/10
  (copie datée : `references_privees.csv.bak_avant_retrait_voix_serie_20261018_1302`).
  L'**audio** reste lui aussi en **usage privé dans l'atelier** : ces voix sont
  celles d'**acteurs** d'œuvres du commerce (voir `ATTRIBUTION.md`) ;
- **entrée faite** par `_essais/_entrer_voix_series_20261016.py` (rapport seul
  par défaut, `--ecrire` pour agir) et, **avant** lui, une **copie datée** du
  fichier de textes : `references.bak_avant_thyrion_sersei_saul_20261016.csv`.

## Les 5 voix du 19/10/2026 : la garde-robe passe à 206

Cinq extraits déposés par Laurent dans « Voix à faires » ont été clonés par
`qwentts.cpp` le 19/10/2026 : **Aldo**, **Gus**, **Jesse**, **Vergès** et
**Sandor**. Quatre clones sur cinq disent **41/41 mots** du texte de contrôle
(**Jesse** : 40/41, « qu'il » entendu « qu'elle »), et la garde-robe passe de
**201 à 206 voix** (`/voix` annonce **206**).

- **identifiants** = nom du fichier : `Aldo`, `Gus`, `Jesse`, `Verges` (sans
  accent, comme le fichier), `Sandor` ; à l'écran « Vergès » garde l'accent ;
- **références** : 24 kHz, mono, PCM 16 bits (les deux autres formats lèvent
  une erreur), 16,4 à 20,4 s ;
- à l'écran : **drapeau français**, **aucun second drapeau**, **0 étoile** →
  **hors casting automatique**, choisissables **à la main** ;
- **textes PRIVÉS** : les 5 lignes sont dans `references_privees.csv` (hors
  dépôt), **jamais** dans `references.csv` — répliques de dialogues sous droits.
  Le privé est en **LF** (7 lignes au 19/10), le public en **CRLF** (201 lignes
  au 19/10, **213 au 21/10** après les voix MLS) ;
- **droits** : voix d'**acteurs de doublages** → **usage privé dans l'atelier**
  (voir `ATTRIBUTION.md`) ;
- **entrée faite** par `_essais/_entrer_5_voix_20261019.py` (rapport seul par
  défaut, `--ecrire`, idempotent), avec **copies datées avant** :
  `references_privees.csv.bak_avant_5voix_20261019` et
  `modules/tts.py.bak_avant_5voix_20261019`.

## Les 12 voix MLS du 20/10/2026 : la garde-robe passe à 218

NIMM Voix a cloné **28 lecteurs français du corpus MLS** (Meta / LibriVox,
**CC BY 4.0**) et Laurent en a **retenu 24 à l'oreille**. Mais **9 de ces
lecteurs étaient déjà ici** sous un identifiant `cml` (même lecteur, autre
passage) : il ne restait que **15 timbres neufs**, et **12 sont entrés le
21/10/2026** (les 3 autres attendent la correction de leur texte de référence) :
**Albertine, Angèle, Clémence, Antoinette, Élise, Bernadette, Denise, Léonie,
Margot, Germaine, Marcelle et Rose**.

- **fichiers** : `MLS_<lecteur>_F_reference.wav`, 24 kHz mono PCM 16 bits,
  17,6 à 20,2 s — même format que le reste du dossier ;
- **textes dans `references.csv`** (le **public**) : MLS est en **CC BY 4.0**,
  donc rien de sous droits ; attribution « **MLS / LibriVox** » obligatoire en cas
  de diffusion, et **personnes réelles** → prudence avant tout partage large ;
- **0 étoile** → **hors casting automatique**, choisissables à la main : ce sont
  des voix de **petits rôles** ;
- **détail complet** (pourquoi 12 et pas 15, les prénoms déjà pris, les copies
  datées) : `../qwen_tts_service/LIRE_MOI.md`, section « Les 12 voix MLS du
  20/10/2026 ».

## Les textes de référence : un fichier PUBLIC, un fichier PRIVÉ (29/09/2026)

Le mode **ICL** a besoin du **texte** de chaque extrait (c'est ce qui fait la
différence entre « ça ressemble à la voix » et « c'est la voix »). Il y a
désormais **deux** fichiers de textes, et le service lit **les deux** :

| Fichier | Contenu | Sur le dépôt |
|---|---|---|
| `references.csv` | les **voix « publiques »** — les lots utilisables LIBREMENT (35 Kyutai, 94 Kokoro, 28 « Découpage OK », 25 CML-TTS, 18 indiennes : **201 lignes au 19/10/2026**, en-tête compris) | **oui** — c'est lui qui porte les corrections de texte relues à la main |
| `references_privees.csv` | les voix **qui ne partent pas** : celle de la **famille** (`Maya_normale`) **et** les **5 voix du 19/10/2026** (`Aldo`, `Gus`, `Jesse`, `Verges`, `Sandor`), dont les répliques viennent d'œuvres sous droits (**7 lignes au 19/10**, en-tête compris) | **non** — il reste sur le PC |

**Pourquoi ce partage** : Maya a lu le début d'un roman du commerce, et la règle
du projet est qu'**aucun extrait d'œuvre sous droits ne part sur le dépôt**. Son
texte vit donc à part, dans le fichier privé, que le service lit **en plus** (si
une voix portait un texte dans les deux, c'est le **privé** qui gagne). Le fichier
est **optionnel** : s'il n'existe pas, rien ne change.

**Pour ajouter une voix de la famille plus tard** : la référence `.wav` va dans
ce dossier (avec les autres, elle est hors dépôt), sa **ligne de texte** va dans
`references_privees.csv`, et son **entrée de catalogue** s'écrit **à la main**
dans `QWEN_VOICES` (`modules/tts.py`) — ces voix ne sortent d'aucun catalogue
existant, donc elles n'entrent par aucune boucle.

## Les trois pièges déjà payés

1. **Une seule fenêtre de moteur à la fois.** Si le port 8086 est déjà pris, le
   service **refuse** de démarrer — c'est voulu. Le 28/09/2026, trois fenêtres
   ouvertes se partageaient le même port : les phrases tombaient sur des moteurs
   frais, qui devaient **recharger les voix** à chaque fois.
   **Attention en le vérifiant** : dans le gestionnaire de tâches, **un seul
   moteur apparaît en DEUX lignes** — le relais du venv
   (`.venv\Scripts\python.exe`, quelques Mo) et le Python de base qu'il lance
   (`C:\Python314\python.exe`, environ 1,9 Go) portent la **même** ligne de
   commande et la **même** seconde de démarrage. Ce n'est **pas** un doublon.
   Le repère fiable est `netstat -ano | findstr :8086` : **un seul** `LISTENING`,
   et c'est le Python de base (constat du 30/09/2026).
2. **La première phrase d'une voix est plus lente** (~10 s) : le moteur prépare
   son **empreinte** (timbre + codes ICL), une fois par voix ; ensuite ×0,93.
   `NIMM_QWENTTS_PRECHAUFFE=1` prépare les 35 empreintes au démarrage (désactivé
   par défaut : cela prend quelques minutes).
3. **Sur le processeur (le défaut), il ne prend pas la carte graphique** :
   inutile d'éteindre Kyutai « pour lui faire de la place » — les deux
   cohabitent. **Sur la carte** (bouton GPU), au contraire, il l'occupe
   (~3,7 Go) : ne lancez pas Kyutai en même temps.

## Ce que le service fait d'une phrase qui DÉRAPE (29/09/2026)

Laurent a entendu un **gargouillis** en changeant la voix de Lord_ivrogne (livre
35) : le moteur avait fabriqué **163,84 s d'audio pour une réplique de 8 jetons**
— exactement son plafond de frames, sans jamais s'arrêter. Il avait **dérivé**,
et la cause est dans les **données** : le texte de référence de cette voix est
**transcrit** (« le trois **mâles** pharaon » au lieu de « le trois-**mâts** le
Pharaon »), donc le moteur recevait un audio qui dit une chose et un texte qui en
dit une autre.

Le service porte désormais le **même garde-fou que NeuTTS**
(`duree_max_derivee` : 3 fois la durée plausible, plus 1 s, plancher 3 s) :

1. une phrase qui dépasse ce plafond est **relancée** — c'est un tirage
   aléatoire, la génération suivante est souvent juste ;
2. si elle dérape encore après les deux reprises, elle est **rognée** au plafond
   : on ne livre **jamais** plusieurs minutes de babil ;
3. tout est écrit dans la fenêtre du moteur : `phrase DERIVEE (163.8 s pour 16
   caracteres, plafond 4.4 s) -- reprise 1/2`.

*Vérifié à froid* par `test_voix/test_garde_fou_derive_qwentts.py` : il branche
un **faux moteur** (aucun modèle chargé, aucun calcul), et vérifie les trois
comportements — phrase normale intacte, dérive relancée, dérive rognée.

## Les fichiers

- `servir_qwentts_cpp.py` — le service (contrat `/sante`, `/voix`, `/tts`,
  `/recharger`, exactement comme les autres moteurs) ;
- `DEMARRER_QWENTTS_CPP.bat` — l'allumage à la main ;
- `models/` — les GGUF **en service** (Q4_K_M depuis le 29/09/2026 :
  `qwen-talker-0.6b-base-Q4_K_M.gguf`, 629 Mo, et `qwen-tokenizer-12hz-Q4_K_M.gguf`,
  255 Mo) **et** les anciens Q8_0 (947 + 278 Mo) gardés comme **repli** — le tout
  **hors Git** ;
- `../qwen_tts_service/voix/references.csv` — les textes des voix publiques
  (**versionné**) et `references_privees.csv` — les textes des voix de la
  **famille** (**hors Git**) ; le service lit les deux ;
- `.venv/` — l'environnement du moteur (Python 3.14, paquet
  `realtimetts-qwen-native-cpu`) : **pas de PyTorch**, rien de lourd ;
- `LIRE_MOI.md` (ce fichier) et `ATTRIBUTION.md` (licences).

## Installer ce moteur sur un autre PC

1. `python -m venv .venv` puis
   `.venv\Scripts\python -m pip install realtimetts-qwen-native-cpu==0.4.2` ;
2. copier les deux GGUF dans `models/` ;
3. vérifier : `python _essais\_verifier_service_qwentts.py` (santé + une phrase).
