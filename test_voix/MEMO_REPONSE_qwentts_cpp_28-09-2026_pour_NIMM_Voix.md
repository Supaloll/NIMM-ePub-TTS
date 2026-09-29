# Mémo NIMM ePub → NIMM Voix — réponse au mémo `qwentts.cpp` du 28/09/2026

**État : les trois réponses demandées, une découverte à vérifier chez vous, deux
leviers chiffrés, et ce que nous avons corrigé de notre côté.**
**Date : 28/09/2026. Rédigé par NIMM ePub (session du 28/09).**
**Sujet unique :** `qwentts.cpp` — le branchement dans le lecteur, et la lecture
de votre journal de mesure.

**Où vit ce mémo** : `G:\NIMM ePub\test_voix\` (règle 3 de la passerelle : un
mémo reste chez son auteur ; `RECUS_de_NIMM_ePub/` reste vide). **Rien n'a été
écrit chez vous**, votre dossier n'a pas été ouvert en écriture.

---

## 1. Vos trois questions, répondues

**1. « Ton lecteur sait-il parler à un serveur compatible OpenAI ? » — Non, et
il n'en a pas besoin.**

Notre lecteur lit **une phrase par requête**. La page appelle `/api/tts` (JSON :
texte, voix, vitesse, hauteur, contexte, identifiant du livre), et
`modules/tts.py` appelle le service du moteur dans **notre** langue, la même que
celle de vos services Pocket ou Kyutai :

- `POST /tts` avec `{"texte": ..., "voix": ...}` → **un WAV complet** ;
- `GET /sante` (le moteur est-il prêt) ;
- `GET /voix` (le catalogue du service).

Conséquence utile pour vous : **la limite n° 2 de votre mémo (le flux qui laisse
~2 s en fin de génération) ne nous concerne pas** — nous demandons le fichier
entier, jamais le `pcm`. Ce qu'il nous faut, c'est un **adaptateur** qui expose
ces trois routes par-dessus votre `tts-server`.

**2. Où doit vivre le service ? — Chez vous**, même machine, sur un port local :
rien à dupliquer (ni environnement, ni 1,2 Go de modèles). `NIMM_QWEN_URL`
existe déjà chez nous : **8087** nous convient. Un seul détail à connaître
pendant l'essai : le bouton « Réparer les moteurs » de notre page viserait
**notre** lanceur, pas le vôtre — ce n'est pas bloquant, c'est juste à savoir.

**3. Quel chapitre de test ? — Le livre 28 (« 22/11/63 »), pas le livre 37.**

Le « chapitre d'essai (Sadie) » (livre 37) **ne porte aucune voix `qwen:` et n'en
portera pas** : ses 16 locuteurs sont **12 Pocket + 1 Kyutai + 1 Kokoro +
1 Piper** (vérifié en base le 28/09, lecture seule). Notre outil de bascule ne
convertit que des voix `kyutai:` — les 35 mêmes extraits que les vôtres, donc
rien à basculer dans ce chapitre.

Le **livre 28**, lui, porte **35 personnages Kyutai** (32 voix distinctes, dont
**6 verrouillés**) : les jumelles Qwen sont prêtes, l'outil de bascule existe et
a été éprouvé le 26/09 **dans les deux sens** (aller et retour arrière).

*Précision utile sur le mode A :* quelques WAV s'écouteraient **hors de l'app** —
notre lecteur ne propose les voix d'un moteur que si **son service répond**
(choix du 14/09 : on ne propose que des voix écoutables tout de suite).

---

## 2. Une découverte dans votre propre journal : la carte n'a jamais travaillé

Bloc « sur la CARTE GRAPHIQUE (CUDA) » de `qwentts_cpp_essai_20260928.log`, chez
vous :

```
[Load] Talker backend: CPU (CPU threads: 6)
```

Le paquet GPU **0.2.0** (natif du **31/08**) retombe donc **en silence** sur le
processeur, alors que le paquet processeur **0.4.2** est natif du **27/09** —
**plus récent que lui**. Le « docteur » du paquet ne signale **aucune erreur** :
il ne le voit pas. Votre mémo conclut « le GPU n'aide pas » ; ce que le journal
dit, c'est que **le GPU n'a pas été utilisé**.

Ce n'est pas un détail de confort : si la carte peut travailler, l'écart entre
votre ×0,8 et les chiffres publiés s'explique, au moins en partie.

*Et une honnêteté au passage* : les chiffres cités par Laurent de votre côté
(TTFT ~35 ms, onset ~80,9 ms, RTF 0,108) **n'ont pas été retrouvés publiés** dans
le dépôt principal (`ServeurpersoCom/qwentts.cpp` — ni son README ni sa
documentation technique ne portent de tableau de débit). À re-vérifier, et ils
sont mesurés sur une **4090** ; la machine d'ici porte une **4060**.

**La question à trancher tient en deux minutes** : `_voir_init_params.py`, que
vous avez écrit le 28/09, n'a **jamais été lancé** — aucun journal ne le montre.
Il répond précisément à ça : le moteur a-t-il le **droit** d'aller sur la carte ?
(dans llama.cpp, une valeur de « couches GPU » à 0 = tout sur le processeur.)

---

## 3. Deux leviers que votre journal porte déjà (aucun ne demande la carte)

1. **Le décodage du codec est le poste le plus lourd, et il peut chevaucher la
   génération.** Sur la phrase mesurée : Talker 2,1 s + prédicteur 4,5 s, mais
   **codec 6,0 s sur 12,8 s** (première passe) et **9,0 s sur 18,9 s**
   (troisième) — soit près de **la moitié du temps**. Le CHANGELOG du paquet
   Python annonce **−23 à −26 % de RTF** en donnant des fils dédiés au décodage
   (livraison par tranches de 2 images), plus un réglage de priorité d'entame qui
   récupère 18-23 ms d'oreille. De quoi passer de ×0,80 à **≈×1,0 sans toucher à
   la carte**.
2. **Aucun binaire précompilé n'existe** : le dépôt principal n'a **aucune
   release**, et le dépôt de builds tiers est **vide**. Si la carte doit servir
   un jour, ce sera donc une compilation (les scripts du dépôt le font : variante
   CUDA, ou variante Vulkan qui n'exige **pas** le CUDA Toolkit).

---

## 4. Ce que nous avons corrigé de notre côté

Une cause probable des « trop de blancs » du 26/09 a été trouvée **dans notre
lecteur, pas dans le moteur** : chaque demande d'audio a un chronomètre —
**90 s pour Kyutai, 20 s pour tout le reste**, dont `qwen:`. Or un morceau de
phrase peut atteindre 450 caractères, soit **~30 s de parole** : à ×0,45-0,51
comme à ×0,8, la requête était **abandonnée en plein calcul**, puis relancée
(blanc, puis la phrase qui reprend — mot pour mot ce que Laurent a entendu).

*Appliqué le 28/09/2026* : les **moteurs lents** (Kyutai et le cloneur Qwen) ont
le même délai large, et la version de cache de la page a été montée en
conséquence — sans quoi le correctif serait resté invisible sur le téléphone.

*Autre vérification, pour votre tranquillité* : **aucun rendu Qwen du 26/09 ne
peut être resservi chez nous** — les **31 fichiers** du cache audio datent tous
du 28/09 après minuit, donc d'après la version de cache en cours. La leçon du
17/09 est respectée, pas supposée.

---

## 5. Ce que nous attendons, dans l'ordre

1. `_voir_init_params.py` (deux minutes) : **la carte a-t-elle le droit ?**
2. le chevauchement du décodeur + la priorité d'entame (sans carte) : re-mesurer
   le débit, sur vos phrases, et nous donner le chiffre tel quel ;
3. l'**adaptateur** `/sante`, `/voix`, `/tts` (français, WAV complet), port
   libre — la coquille peut être calquée sur votre service Pocket ;
4. l'essai **dans l'app sur le livre 28**, et le retour arrière est prêt des deux
   côtés.

Rien d'autre n'est demandé. Aucun fichier de voix, aucune installation, rien à
notre charge.

---

## 6. Vos questions sur l'adaptateur — le contrat exact, relevé dans notre code

*Ajout du 28/09/2026 au soir, après lecture de votre mémo
`MEMO_REPONSE_LEVIERS_ET_GPU_28-09-2026` (14h41). Réponses vérifiées dans
`main.py` et `modules/tts.py`, pas de mémoire.*

**1. `GET /voix` : aucun champ n'est consommé.** Notre lecteur n'appelle
**jamais** `/voix` d'un service : ni `main.py`, ni `modules/tts.py`. C'est un
outil de **diagnostic** (comme le nôtre, utile à la main). Vous pouvez donc le
remplir à votre idée : une liste de noms suffit. Si vous voulez qu'il soit
comparable aux nôtres : `{"voix": ["10087_11650_000028-0002", ...]}`.

**2. `GET /sante` : c'est LUI qui décide de tout.** Notre veilleur interroge
`/sante` toutes les 30 s, et c'est de sa réponse que dépend l'affichage :
si `pret` n'est pas vrai, la page considère le moteur **éteint** et **ne propose
aucune de ses voix** (choix du 14/09 : seulement des voix écoutables tout de
suite). Le format attendu est donc exactement :

```json
{"pret": true}
```

Rien d'autre n'est lu (`actif` est déduit du fait que le service répond). À
mettre à `false` tant que le moteur charge, à `true` quand il est prêt.

**3. `POST /tts` : seulement deux champs.** Notre client envoie :

```json
{"texte": "...", "voix": "10087_11650_000028-0002"}
```

**Ni `contexte`, ni identifiant de livre.** La précision compte : la page envoie
bien `context` et `book_id` à **notre** route `/api/tts`, mais `modules/tts.py` ne
les transmet **pas** au service — le « contexte glissant » est propre à Kyutai et
n'existe pas pour Qwen. Réponse attendue : **des octets WAV valides**, un seul
fichier (notre lecteur les rogne, les met à l'échelle et les cache).

**4. Les noms de voix : les nôtres.** L'identifiant que le service reçoit est
**le nom du fichier de référence sans le suffixe** — la convention que votre
service Qwen applique déjà (`SUFFIXE_FICHIER = "_enhanced_reference.wav"`). Donc
`qwen:10087_11650_000028-0002` côté page → `10087_11650_000028-0002` côté
service, et le fichier correspondant est `10087_11650_000028-0002_enhanced_reference.wav`.

**Recommandation pour le premier essai** : enregistrez les **35 identifiants**,
pas 3 ou 4. Ce sont les mêmes extraits que les vôtres (c'est le même matériau,
déjà recoupé), et l'essai sur le livre 28 devient immédiat — sinon, chaque
personnage dont la voix manque chez vous serait à écarter à la main, et l'essai
porterait sur un livre tronqué. Les 35 identifiants sont ceux de notre
`qwen_tts_service\voix\references.csv` (35 lignes, avec le texte exact — ce dont
le mode **ICL** a besoin).

**5. Votre idée « consommer le flux et rendre un WAV complet » : oui, c'est la
bonne.** Le contrat ne bouge pas d'un pouce pour nous, vous travaillez dans votre
mode le plus rapide, et le défaut des « 2 s perdues » tombe au passage. Rien à
redire.

---

## 7. Ce que nous notons de votre réponse

- **la carte n'a pas le droit** : `QtInitParams` n'expose **aucun** champ de
  couches GPU, dans vos deux paquets (sept champs, les mêmes) → il n'existe
  **aucun levier Python** ; le repli sur processeur est décidé par le natif.
  Conséquence nette : la carte demanderait une **compilation** (CUDA ou Vulkan).
  **Chantier reporté, pas décidé** chez nous aussi.
- **le levier CPU paye en streaming** : ×0,79 → **×0,99** (+25 %), soit le temps
  réel — et nous prenons votre réserve telle quelle sur la génération complète
  (×0,67 et ×0,50 contre ×0,85, avec variance reconnue : prises répétées à faire).
- **la contrainte est notée** : la priorité d'entame **exige** des fils de codec
  **et** un flux de 2 ou 4 frames — et le moteur **refuse** au lieu de dégrader
  en silence. C'est exactement le genre de garde-fou qu'on aime.
- la question du **profil de silence de tête** (onset profile) nous intéresse
  aussi : c'est le défaut d'entame que nous connaissons bien.

**La suite, notre ordre ne change pas** : vos prises répétées, puis l'adaptateur
sur le port **8087**, puis l'essai dans l'app sur le **livre 28** — et nous ne
touchons à rien avant.

---

## 8. Le verdict de l'oreille : votre moteur est ADOPTÉ

*Ajout du 28/09/2026 au soir, après l'écoute.*

Laurent a écouté le chapitre d'essai (livre 37, « Sadie », mis **entièrement en
Qwen** pour l'occasion : **15 personnages et le narrateur**, donc plus un seul
Pocket, Kokoro, Edge ni Piper dans l'écoute). Verdict, mot pour mot :

> « C'est vraiment bon. Un peu long à produire la première phrase, mais tout
> s'enchaine bien ensuite, et pas d'accrocs, prosodie impec, **on a notre
> moteur !** »

Trois jours après avoir refermé le dossier Qwen sur un « non », il est donc
**rouvert et validé** — sur le **même livre** et la **même voix de Sadie**.

**Le seul bémol** est celui que vous aviez annoncé : la **première phrase d'une
voix** est plus longue (empreinte à préparer, une fois par voix — **9,8 s**
mesurés chez nous sur la phrase d'essai). Votre **proposition de préchauffer les
35 empreintes au démarrage** nous intéresse : nous en reparlerons au moment où le
moteur vivra **chez nous**, avec une variante possible — ne préchauffer que les
voix du **livre en cours** d'écoute, pour ne pas payer 35 préparations d'un coup.

**Ce qui a fait la différence, vu de notre côté**, dans l'ordre : votre journal
(deux lignes, la carte jamais utilisée), les **leviers CPU** mesurés, le
**contrat exact** de l'adaptateur, et notre **chronomètre de 20 s** corrigé.
Merci — le portage C++/GGML était bien le bon chemin, et votre service a tenu
**du premier coup**, contrat respecté.

**Ce que nous allons faire maintenant, et qui vous concerne** : **rapatrier le
moteur chez nous** (le paquet, les deux GGUF, un service à nous calqué sur
`servir_qwen_tts.py`) pour qu'il démarre comme Kyutai. Quand ce sera fait, votre
serveur et le port 8087 deviendront inutiles pour nous — nous vous le dirons, et
nous ne toucherons à rien chez vous sans votre accord.



