# MOTEURS DE VOIX — le tableau, en un coup d'œil

_Écrit le 30/09/2026, à la demande de Laurent : « je fais tellement d'essais que
je ne sais même plus ce qui clone, ce qui est léger »._
_Mis à jour le **01/10/2026** : **Qwen tourne maintenant sur la carte graphique**
(×3,9 à ×7,5) — c'est le **moteur retenu** pour lire les livres._

**Comment lire ce tableau.** Une seule question par colonne, et la réponse est
**oui / non / où ça en est** :

- **Clone ?** — le moteur peut-il parler avec **la voix d'un extrait** que tu lui
  donnes (tes 30 extraits, les voix CML-TTS, la voix de ta fille…) ?
- **Français ?** — ce qu'il fait du français : **natif** (entraîné en français),
  **correct** (compétent mais pas français d'origine), **accent** (il lit du
  français avec un accent étranger).
- **Léger ?** — combien de fois il fait l'audio **plus vite que la lecture**
  (« × le temps réel »). C'est LE chiffre qui décide des blancs : **en dessous
  de ×1,2, ça coupe** dès que le PC fait autre chose ; à ×3 et plus, on est
  tranquille.
- **Où ça en est** — en service, testé, écarté, ou à essayer.

---

## Les moteurs, un par ligne

| Moteur | Clone ? | Français ? | Léger ? (× le temps réel) | Où ça en est |
|---|---|---|---|---|
| **Edge** (en ligne, Microsoft) | non | correct (voix natives FR) | très rapide (c'est un service) | **en service** — mais aucune des voix n'est la tienne |
| **Piper** (local) | non | natif (voix FR natives) | très rapide (ONNX, CPU) | **en service** — petits rôles ; 3 voix seulement, sans clonage |
| **Kokoro** (local, 82 M) | **non, sauf piste** (voir plus bas) | **une seule voix FR** (`ff_siwis`) | très rapide (ONNX, CPU) | **en service** ; ses 94 voix sont **anglaises** (d'où l'accent) — ses 94 jumelles Qwen existent |
| **Qwen3-TTS** (qwentts.cpp, 0,6 B) | oui (**201 voix FR** — c'est le roi du clonage) | natif | **×3,9 à ×7,5 sur la CARTE** (×1,04 à ×1,20 sur le processeur) | ⭐ **EN SERVICE, SUR LA CARTE GRAPHIQUE depuis le 01/10/2026** — décision de Laurent : « on reste sur ce moteur et sur la carte graphique » |
| **Pocket TTS 24 couches** (Kyutai, 672 Mo) | oui | natif | ×1,40 à ×1,56 | **écarté le 30/09** définitivement : pauses **au milieu des mots**, « j'avais » lu « je avait », mots inventés — 4 prises propres sur 36 |
| **Pocket TTS 6 couches** (le **léger**, 219 Mo) | oui (les mêmes 28 voix clonées) | natif | **×4,12** | **écarté le 30/09 au soir** : verdict de Laurent sur un chapitre entier — « **5 % du texte c'est un mot mâché, oublié, bégayé** ». Les chiffres étaient bons (17 prises saines sur 18, zéro trou après recousu) : **l'oreille a tranché** |
| **Kyutai TTS** (1,6 B, carte graphique) | **techniquement oui, mais impossible chez nous** — il manque le codec voix (16 codebooks) que Kyutai n'a jamais publié (vérifié le 30/09/2026) | natif | ≈ ×2,3 (carte graphique) | ⭐ **le seul moteur que l'oreille de Laurent a validé sur un vrai chapitre** (« **tout est propre** », 17/09/2026) — prêt à tourner (venv, **141 fichiers**, modèle en cache), **indépendant du processeur** — **mais seulement 35 voix publiques (CML-TTS)** : insuffisant pour un livre |
| **XTTS v2** (carte graphique) | oui | natif | ≈ ×3,3 (carte graphique) | testé, écarté pour le défaut de « babil » |
| **NeuTTS Air** (carte graphique) | oui (avec le **texte** de l'extrait) | correct | **×0,7** (carte graphique) — plus lent que la lecture | **écarté** (gargouillis, répétitions) |
| **NeuTTS Nano French** (228 M) | oui | natif | **à mesurer** | **piste** : GGUF q4/q8 existent (donc rapide sur processeur), licence à lire |
| **Kokoro + adaptateur de clonage** | **oui** (clonage « léger ») | anglais d'origine, à éprouver en FR | très rapide (Kokoro reste Kokoro, 82 M) | **piste neuve du 30/09** — testable **sans entraînement** |
| **Kokoro français fine-tuné** | non (mais **plusieurs voix FR**) | natif | très rapide (82 M) | **piste neuve du 30/09** — recette publique, GPU à louer |

**Les deux moteurs « en ligne payants »** (Gemini TTS, Edge « premium ») ne sont
pas dans ce tableau : ils lisent bien, mais **ils ne clonent pas** tes voix et
coûtent à la phrase.

---

## Ce qui compte vraiment, dit simplement

1. **Le clonage, on l'a** : Qwen (201 voix) et Pocket (28 voix) clonent tes
   extraits. Le problème n'était pas là — il était dans **la tenue**. **Réglé
   pour Qwen** le 01/10/2026 en le passant sur la **carte graphique** (×3,9 à
   ×7,5 : plus de blancs). Pocket, lui, reste écarté (trous et mots mangés).
2. **La qualité « Kokoro » que tu aimes** vient de deux choses : un modèle
   **léger et stable** (82 M, ONNX) et des **voix faites pour lui** (pas des
   extraits clonés). C'est pour ça qu'il ne coupe pas et ne fait pas de babil.
3. **Ce qui manque à Kokoro, c'est le français** : une seule voix FR
   (`ff_siwis`), et **pas de clonage** — d'où tes deux pistes, qui sont les
   bonnes (voir ci-dessous).

---

## 🐈 Les deux pistes Kokoro (vérifiées le 30/09/2026)

### Piste 1 — cloner sur Kokoro, **sans rien entraîner** (à essayer en premier)

- **L'outil existe** : `remsky/kokoro-inno-clone-tuner` — un adaptateur de
  **9,6 millions de paramètres** (à côté des 82 M de Kokoro), licence
  **Apache-2.0**, mis à jour le **15/09/2026**, **585 000 téléchargements**.
- **Ce qu'il fait** : on lui donne un **extrait** (comme à Pocket ou à Qwen), il
  en sort un **fichier de voix Kokoro** (`.pt`) ; ensuite Kokoro parle avec
  cette voix **comme avec n'importe laquelle de ses 54 voix**. Installation :
  `pip install inno-kokoro`, puis `enroll(extrait, tuner)`.
- **Ce que ça vaut, honnêtement** (mesures de l'auteur, pas les nôtres) : le
  rendu ressemble à la voix de référence **à environ un tiers** (score d'identité
  **0,32**, sur une échelle où la vraie personne vaut 1,00 et où F5-TTS — qui
  clone presque parfaitement — vaut 0,94). C'est **deux fois mieux que de
  prendre la voix Kokoro la plus proche** (0,15). Donc : **pas un clonage
  fidèle** — une voix **du même registre** que la tienne.
- ⚠️ **Deux réserves** : l'adaptateur a été entraîné **en anglais** (LibriTTS,
  VoxPopuli, Emilia), et personne n'a mesuré son comportement sur du français.
- **Pourquoi ça vaut quand même l'essai** : Kokoro tourne **déjà** chez nous, en
  ONNX, sans carte graphique, sans blancs. Si le clonage tient, on a **la
  stabilité de Kokoro + des voix proches des tiennes + la vitesse** — la
  combinaison que tu cherches depuis le début. Et ça se teste **en une soirée,
  sans serveur à louer**.

### Piste 2 — un Kokoro **français** entraîné (plusieurs voix FR natives)

- **La recette est publique et complète** : `semidark/kikiri-tts` (ex-
  `kokoro-deutsch`), avec guide d'entraînement, guide de dépannage, sous-module
  StyleTTS2 corrigé. Pipeline documenté de bout en bout : préparation des
  données → conversion des poids → **étape 1** (base multi-locuteurs) →
  **étape 2** (une voix) → extraction du fichier de voix.
- **Les précédents sont nombreux** : **allemand** (51 voix, ~51 h d'audio),
  hébreu, marathi, kannada, tamoul, kazakh… et **hexgrad lui-même a publié un
  fine-tune officiel en chinois** (`Kokoro-82M-v1.1-zh`). Ce n'est donc pas de
  la science-fiction.
- **Ce que ça coûte** (chiffres officiels du README de Kokoro) : le modèle
  complet (8 langues, 54 voix) a coûté **1 000 h de A100 80 Go ≈ 1 000 $**
  (tarif 2025, ~1 $/h). Le fine-tune allemand, lui, tient en **51 h d'audio /
  51 locuteurs** pour l'étape 1, puis **455 à 627 phrases par voix** pour
  l'étape 2. Un GPU loué coûte aujourd'hui **0,3 à 2 $/h** selon la carte :
  **un essai français sérieux se compte en dizaines d'euros**, pas en milliers.
- **Les données françaises libres existent — et tu en connais déjà** :
  - **SIWIS** (11 h, CC-BY) : c'est **déjà** dans les données d'entraînement de
    Kokoro (c'est écrit dans son README) et c'est la source de la voix Piper
    « Siwis » de ton catalogue ;
  - **MLS français** (~1 000 h, CC-BY) : le gros du volume, des centaines de
    locuteurs ;
  - **Common Voice FR** (CC0), **VoxPopuli FR**, **M-AILABS**, **CML-TTS FR**
    (les 25 voix que NIMM Voix a déjà clonées !).
- **Et la réponse à ta crainte — « jamais assez d'extraits pour plusieurs
  voix »** : pour l'étape 1 (le « plusieurs voix »), on **n'utilise pas tes
  extraits** : on prend des corpus publics, qui apportent **des dizaines de
  locuteurs français** (femmes, hommes, âges différents). **Tes extraits ne
  servent qu'à une chose : cloner** (piste 1, ou étape 2 d'une voix précise).

### Ce que je propose, dans l'ordre

1. **Piste 1 d'abord** (clonage Kokoro, sans entraînement) : on installe, on
   clone **2 ou 3 de tes voix** (un homme, une femme), et **tu écoutes**. Si ça
   sonne juste, le problème est réglé **sans serveur, sans entraînement, sans
   blancs**.
2. **Si la piste 1 déçoit** : la piste 2 devient un chantier long — recette
   prête, données libres, **GPU loué à l'heure** pour un essai.
3. **Et en parallèle, on termine ce qui est presque prêt** : le **Pocket
   6 couches à 0,70** (×4,12, un seul fichier à écouter) — c'est le **filet de
   sécurité** : si Kokoro ne donne rien, on a déjà un moteur qui tient.


