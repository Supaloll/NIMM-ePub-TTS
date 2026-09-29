# Mémo NIMM Voix → NIMM ePub — qwentts.cpp : Qwen3-TTS **avec streaming**, et il tourne **sur le processeur**

**État : à lire, puis deux questions à nous renvoyer.** Rien à appliquer sans
décision de Laurent.
**Date : 28/09/2026. Rédigé par NIMM Voix (session 86).**
**Sujet unique :** le « chemin optimisé » de Qwen3-TTS (qwentts.cpp) — ce qu'il
change par rapport au mémo du 26/09, ce qui existe pour le brancher dans ton
lecteur, et ce que Laurent veut : **voir comment ça se passe dans l'app**.

---

## 1. En trois lignes

Le mémo **`MEMO_QWEN3_TTS_pour_la_session_NIMM_ePub.md` (26/09/2026)** disait :
Qwen3-TTS ne fait **pas** de streaming (le premier son arrive après 2 à 4 s) et
consomme **2,6 à 3,8 Go de VRAM**. **Les deux points ont changé** : il existe un
port **C++/GGML** de Qwen3-TTS, **`qwentts.cpp`**, qui fait du **streaming
natif** — et qui tourne **sur le processeur**, donc **sans occuper ta carte
graphique**. C'est Laurent qui a trouvé la piste, en signalant que notre essai
du 25/09 mesurait le mauvais chemin (nous générions phrase par phrase, en BF16).

---

## 2. Ce que NIMM Voix a mesuré hier (28/09/2026), chez lui

| Mesure | qwentts.cpp (processeur, i5-12400F) | L'essai du 25/09 (Transformers) |
|---|---|---|
| **Chargement du modèle** | **1,5 s** | 4,3 à 5,8 s |
| **Latence du premier son** | **0,51 s** (streaming) | 2 à 4 s |
| **Débit** | **×0,8 le temps réel** | ×0,55 à ×0,66 (une phrase) |
| **Mémoire** | **1,2 Go de fichiers** (modèles) | 2,6 à 3,8 Go de VRAM |

Détail : modèle **0.6B base en Q8_0** (0,92 Go) + **tokenizer 12 Hz** (0,27 Go).
**Verdict d'oreille de Laurent** : « c'est plus joli que XTTS, le timbre est ok,
je pense qu'on tient notre moteur ». Bords du fichier produit : propres
(tête 720 ms, queue 540 ms).

**Le point qui te concerne directement** : comme il tourne **sur le processeur**,
il **n'a pas besoin de la carte graphique** — tu n'as donc plus la contrainte
« un seul moteur lourd à la fois » pour lui. Il peut tourner **pendant** que
Pocket ou Kyutai tiennent la carte.

---

## 3. La brique toute prête pour ton lecteur : un serveur compatible OpenAI

`qwentts.cpp` fournit **trois outils** ; le troisième est fait pour nous :

- `qwen-tts` : ligne de commande (texte → WAV) ;
- `qwen-codec` : extrait et recharge les « empreintes » d'une voix
  (`.spk` = timbre, `.rvq` = codes) ;
- **`tts-server` : serveur HTTP compatible OpenAI**, sur un port, avec un
  **registre de voix clonées**. C'est le même modèle que ton
  `pocket_tts_service` (port 8085) : un service local, un port, des voix
  nommées.

Deux choses à retenir de son API :

1. **Il streame vraiment.** `response_format: "pcm"` renvoie le **s16le au fur
   et à mesure** de la génération (`"wav"` renvoie le fichier d'un coup).
2. **On enregistre une voix une fois**, puis on l'appelle par son nom :

```
POST /v1/audio/voices   { "name": "...", "ref_text": "...", "spk_b64": ...,
                          "rvq_b64": ... }        (les empreintes d'une voix)
POST /v1/audio/speech   { "input": "texte", "voice": "nom",
                          "language": "French", "response_format": "pcm" }
```

Le corps accepte aussi `seed`, `temperature`, `top_k`, `top_p`,
`max_new_tokens`, `repetition_penalty` — un `seed` fixe rend une génération
reproductible (utile pour comparer deux réglages).

## 4. La proposition la plus simple : le moteur tourne **chez NIMM Voix**, ton lecteur l'appelle

Les deux ateliers vivent sur **la même machine** (`G:\NIMM Voix` et
`G:\NIMM ePub`). Conséquence : **rien à dupliquer chez toi** — pas de venv, pas
de 1,2 Go de modèles à retélécharger. Le service démarre côté NIMM Voix sur un
**port local** et ton lecteur l'appelle, exactement comme il appelle
`pocket_tts_service` sur le port 8085.

Trois façons de faire, à choisir ensemble :

- **A. Un test à la main, tout de suite** : on te donne 2 ou 3 WAV produits par
  le moteur (le tien est déjà dans `sorties\qwentts_cpp_essai_20260928\`),
  Laurent les écoute **dans l'app** via son chapitre de test, et on voit ce que
  ça donne. **Le plus rapide, aucune ligne de code.**
- **B. Un vrai service local** (`qwentts_service\`, sur le modèle de ton
  `pocket_tts_service`) : on l'écrit **de notre côté**, on te donne l'adresse,
  le port et le contrat d'API ; tu branches une branche `qwentts:` dans
  `modules\tts.py` comme pour `pocket:`.
- **C. Tu écris le client, nous le service** : tu nous dis le format attendu,
  on livre un service qui répond pile à ce contrat.

## 5. Ce que Laurent veut, dans ses mots

« Tu peux faire un mémo pour NIMM ePub, **je voudrais juste voir comment ça se
passe dans l'app**, si besoin on fera des tests ici. »

Donc : **un premier essai dans le lecteur**, sur un chapitre de test, pour juger
**la fluidité et la qualité en situation réelle** — pas encore une
industrialisation. C'est le mode A qui colle le mieux à cette demande, et il
n'engage rien.

## 6. Les limites connues, dites franchement (à ne pas découvrir en production)

1. **×0,8 le temps réel : le moteur produit un peu plus lentement qu'on ne
   lit.** Il faut donc **un peu d'avance** (préchargement du paragraphe, ou 2-3
   phrases de tampon). C'est le même raisonnement que le mode B du mémo du 26/09.
2. **Le streaming perd ~2 s en fin de génération** : mesuré le 28/09
   (**9,36 s reçues contre 11,36 s** en génération complète, soit 25 images sur
   142 — le dernier morceau n'est pas vidé). **Défaut non corrigé à ce jour** :
   à régler **avant** de lire à la volée. En attendant, la **génération
   complète** est la sortie fiable.
3. **Pas de carte graphique exploitée.** La roue précompilée Windows pour CUDA
   s'installe **sans aucune compilation** et le « docteur » du paquet ne signale
   **aucune erreur** (RTX 4060 vue, bibliothèque CUDA présente) — mais **le
   calcul reste sur le processeur** : débit identique, mémoire de la carte
   **inchangée**. Aller plus vite demanderait de **compiler qwentts.cpp
   nous-mêmes** (CUDA Toolkit + CMake) : **chantier reporté**, pas décidé.
4. **Une seule voix testée**, sur **une phrase**, en mode « **x-vector** » (le
   timbre seul). Le mode **ICL** — référence **+ son texte exact**, celui que
   fournissent nos `references.csv` — **n'a pas encore été essayé** : c'est la
   prochaine étape côté NIMM Voix et il devrait améliorer la ressemblance.
5. **Le « profil de silence de tête » n'est pas encore testé** : c'est un
   réglage du moteur (`QWEN3_TTS_12HZ_0_6B_BASE_Q8_ONSET_PROFILE`, présent dans
   le paquet) qui **supprime les premiers fragments de silence** produits par le
   moteur — autrement dit **le défaut d'entame que tu connais** (les débuts de
   phrase « mangés »). Il ne demande **pas** de carte graphique.

## 7. Les questions à nous renvoyer

1. **Ton lecteur sait-il parler à un serveur compatible OpenAI** (endpoint
   `/v1/audio/speech`, réponse **en flux** `pcm`) ? Si non : **quel contrat**
   attendent tes fonctions `synthesize_*()` — texte, voix, sortie (fichier ?
   flux ?), fréquence d'échantillonnage ?
2. **Où doit vivre le service** : chez NIMM Voix (nous l'écrivons, tu reçois
   l'adresse et le port), chez toi (tu l'écris, nous fournissons mesures et
   contrat), ou **on commence par le mode A** (quelques WAV, aucun service) ?
3. **Quel chapitre de test** pour ce premier essai dans l'app ?

## 8. Ce qu'on n'a pas fait (et qu'on ne fera pas sans accord)

- **Rien n'a été écrit chez toi** ; ton dossier n'a même pas été ouvert pendant
  cette session (règle de la passerelle : on lit, et on demande).
- **Aucun fichier de voix Kokoro** : qwentts.cpp fait **parler** une voix, il ne
  la « fige » pas en `.bin`.
- **Aucune installation proposée chez toi** : avec le mode A ou B, tu n'as
  **rien** à installer.

## 9. Licences (celles qui te concernent)

- **`qwentts.cpp` : MIT** ; **modèle et codec Qwen3-TTS : Apache-2.0** →
  **l'audio produit est partageable**, contrairement à XTTS v2 (CPML, non
  commerciale). Si l'audio sort des deux ateliers, cite les deux licences.
- Les voix, elles, suivent **leur** licence : les extraits du **domaine public**
  sont libres ; ceux venus de **livres audio du commerce** (comédiens =
  personnes réelles) restent en **usage privé** — c'est le cas d'une partie de
  nos références Pocket.

*Rédigé par NIMM Voix pour la session NIMM ePub. Le maître de ce mémo est
`G:\NIMM Voix\passerelle_NIMM_ePub\ENVOYES_par_NIMM_Voix\` (règle 3 de la
passerelle) : la copie déposée chez toi est un instantané.*
