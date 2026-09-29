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
| Voix | les **35 extraits communs avec Kyutai**, lus dans `../qwen_tts_service/voix/` — le dossier est **partagé** (même matériau, avec le texte exact qui active le mode ICL) |
| Réglages | 6 cœurs, **4 fils de codec**, tranches de **2 images**, priorité d'entame |
| Débit mesuré | **×0,94 le temps réel** : le moteur est au niveau de la lecture |
| Mémoire | 1,2 Go de fichiers, **aucune carte graphique** |

## Les trois pièges déjà payés

1. **Une seule fenêtre de moteur à la fois.** Si le port 8086 est déjà pris, le
   service **refuse** de démarrer — c'est voulu. Le 28/09/2026, trois fenêtres
   ouvertes se partageaient le même port : les phrases tombaient sur des moteurs
   frais, qui devaient **recharger les voix** à chaque fois.
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
- `models/` — les deux GGUF (`qwen-talker-0.6b-base-Q8_0.gguf`, 947 Mo, et
  `qwen-tokenizer-12hz-Q8_0.gguf`, 278 Mo), **hors Git** ;
- `.venv/` — l'environnement du moteur (Python 3.14, paquet
  `realtimetts-qwen-native-cpu`) : **pas de PyTorch**, rien de lourd ;
- `LIRE_MOI.md` (ce fichier) et `ATTRIBUTION.md` (licences).

## Installer ce moteur sur un autre PC

1. `python -m venv .venv` puis
   `.venv\Scripts\python -m pip install realtimetts-qwen-native-cpu==0.4.2` ;
2. copier les deux GGUF dans `models/` ;
3. vérifier : `python _essais\_verifier_service_qwentts.py` (santé + une phrase).
