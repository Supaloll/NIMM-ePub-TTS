# `qwentts_service/` — le moteur de voix Qwen3-TTS en C++/GGML

**En une phrase** : c'est le moteur qui fait parler les voix `qwen:` du lecteur.
Il porte Qwen3-TTS **en C++/GGML** (le portage `qwentts.cpp`), donc **sans
PyTorch et sans carte graphique** : il tourne sur le **processeur**, et il
**cohabite** avec Kyutai et Pocket au lieu de les remplacer.

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
| Voix | les **183 références** de `../qwen_tts_service/voix/` — le dossier est **partagé** (même matériau, avec le texte exact qui active le mode ICL) : **35** extraits Kyutai/CML-TTS, **94** Kokoro et **28** « Découpage OK » (copiés le 28/09/2026), **25** CML-TTS « cml_restants » (30/09/2026) et la voix privée **Maya** |
| Modèles | **Q4_K_M depuis le 29/09/2026** (629 + 255 Mo), choisis **à l'oreille par Laurent** : « les plus jolies à l'oreille, prosodie et clarté un demi-cran au-dessus ». Les **Q8_0** (947 + 278 Mo) restent sur le disque en **repli automatique** |
| Réglages | 6 cœurs, **4 fils de codec**, tranches de **2 images**, priorité d'entame |
| Débit mesuré | **×1,0 à ×1,2 le temps réel** (Q4_K_M, 29/09/2026) — avant, ×0,94 avec les Q8_0 (28/09) |
| Mémoire | **884 Mo de fichiers** (Q4_K_M), aucune carte graphique |

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
  est en **UTF-8 sans BOM et fins de ligne LF** (relevé par NIMM Voix le
  29/09). L'outil de fusion (`_essais/_fusionner_textes_qwen.py`) écrivait en
  **CRLF** sans le vouloir — Python traduit `\n` en `\r\n` sous Windows :
  corrigé le 30/09/2026 par `newline=''`.

## Les textes de référence : un fichier PUBLIC, un fichier PRIVÉ (29/09/2026)

Le mode **ICL** a besoin du **texte** de chaque extrait (c'est ce qui fait la
différence entre « ça ressemble à la voix » et « c'est la voix »). Il y a
désormais **deux** fichiers de textes, et le service lit **les deux** :

| Fichier | Contenu | Sur le dépôt |
|---|---|---|
| `references.csv` | les **157 voix « publiques »** (35 Kyutai, 94 Kokoro, 28 « Découpage OK ») | **oui** — c'est lui qui porte les corrections de texte relues à la main |
| `references_privees.csv` | les voix de la **famille** (`Maya_normale` pour commencer) | **non** — il reste sur le PC |

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
3. **Il ne prend pas la carte graphique** : inutile d'éteindre Kyutai « pour lui
   faire de la place » — les deux cohabitent, c'est même tout l'intérêt.

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
