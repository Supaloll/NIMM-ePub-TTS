# Mémo — XTTS v2 (clonage de voix française) : installation, voix, cohabitation avec Kyutai

> **⚠️ Mise à jour du 16/09/2026 — les environnements de l'atelier ont été
> retirés.** Les `.venv` de `outils\xtts_tts` et `outils\kyutai_tts` (≈ 12 Go) ont
> été **supprimés volontairement** : **NIMM ePub a désormais les siens**
> (`xtts_service\.venv` et `kyutai_service\.venv`, mêmes tailles, vérifiés
> complets), et **aucun code du lecteur ne dépendait de l'atelier** — vérifié :
> les seules mentions de « NIMM Voix » dans NIMM ePub sont des **commentaires**
> et le libellé `France (NIMM Voix)` de 30 voix Kokoro.
> **Conservés** dans l'atelier : les scripts, `reference` (extraits), la banque
> Kyutai (`voix_fr`), **`whisper-large-v3`**, les corpus et les recettes
> d'entraînement (`training`, `voicepack_train`).
> **Conséquence pratique** : les chemins cités plus bas qui pointent vers
> `outils\xtts_tts\.venv\Scripts\python.exe` **n'existent plus**. Pour tester
> XTTS, utiliser désormais `g:\NIMM ePub\xtts_service\.venv\Scripts\python.exe`.

_Écrit le 14/09/2026 par la session Cline de l'atelier **NIMM Voix**
(`<atelier NIMM Voix>`), à la demande de Laurent. L'atelier NIMM Voix est un dossier
**séparé** : il sert à essayer les moteurs de voix avant de les intégrer ici.
**Rien n'a été modifié dans NIMM ePub** — ce mémo est la seule chose déposée
(il n'est pas branché au programme)._

## En une phrase

Le moteur **XTTS v2** (clonage de voix, 17 langues dont le français) **tourne
déjà sur la RTX 4060 de Laurent, dans un bac à sable séparé** — Laurent l'a
**écouté et validé sur 9 minutes de texte** ; ce mémo explique comment il a été
installé, comment récupérer **les 35 voix françaises déjà présentes ici** comme
voix de clonage, et comment organiser la **cohabitation avec Kyutai** (un seul
des deux à la fois : les deux ne tiennent pas ensemble sur la carte graphique).

---

## 1. Comment XTTS v2 a été installé (procédure exacte)

Tout est écrit et commenté dans un seul fichier, à lire **avant** de refaire
l'installation :

    <atelier NIMM Voix>\outils\xtts_tts\_install_xtts.cmd

Le principe est **exactement celui de `kyutai_service`** : un environnement
Python 3.12 séparé, à côté du lecteur (qui tourne en 3.14), plus un service qui
répond en HTTP. Étapes :

1. créer le bac à sable avec **Python 3.12**
   (`<python 3.12>`,
   le même que `kyutai_service\.venv`) ;
2. `python -m pip install --upgrade pip` ;
3. **PyTorch 2.8 en CUDA 12.8** :
   `pip install "torch==2.8.*" "torchaudio==2.8.*" --index-url https://download.pytorch.org/whl/cu128`
4. **la bibliothèque `coqui-tts`** (fork maintenu par le laboratoire Idiap — le
   projet Coqui d'origine est abandonné), **avec une borne haute sur
   transformers** : `pip install coqui-tts "transformers>=4.57,<5"`.

### Les deux pièges (ils coûtent chacun une demi-journée si on ne les connaît pas)

- **Piège 1 — `transformers` trop récent.** `coqui-tts` 0.27.5 exige
  `transformers >= 4.57` **sans borne haute** ; pip installe donc la version 5,
  dans laquelle la fonction `isin_mps_friendly` a disparu de
  `transformers.pytorch_utils` → l'import de `TTS` échoue. Remède : imposer
  `transformers>=4.57,<5` (4.57.6 chez Laurent).
- **Piège 2 — PyTorch 2.9 et plus réclame `torchcodec`.** Depuis PyTorch 2.9,
  `coqui-tts` refuse de démarrer sans la bibliothèque `torchcodec`, et
  `torchcodec` a besoin des **DLL FFmpeg « partagées »** (`avcodec-*.dll`…).
  L'installation ffmpeg de la machine est un **build statique** (aucune DLL) →
  erreur `Could not load libtorchcodec`. Remède retenu : **PyTorch 2.8**, avec
  lequel `coqui-tts` repasse par `torchaudio` et tout fonctionne. Un PyTorch
  plus récent n'apporte rien ici.

### Ce que l'installation fait comme poids

- PyTorch CUDA : ~3,5 Go (plus ~3 Go pendant le téléchargement) ;
- `coqui-tts` et ses dépendances : quelques centaines de Mo ;
- **le modèle XTTS v2 : 2,09 Go**, téléchargé **au premier chargement** (pas à
  l'installation), puis mis en cache.

### La licence du modèle — point à ne pas perdre de vue

Le modèle `coqui/XTTS-v2` est sous **« Coqui Public Model License » (CPML)** :
elle n'autorise que l'usage **non commercial**, **du modèle ET de ses sorties**
(les audios générés). Texte exact, lu le 14/09/2026 : « This license allows only
non-commercial use of a machine learning model **and its outputs** ». Trois
conséquences pratiques :

- l'usage de Laurent (écoute personnelle, essai, loisir) est **couvert** : la
  CPML cite explicitement « personal use for research, experiment, and
  testing… personal study, private entertainment, hobby projects » ;
- **aucun usage commercial** de l'audio généré, et pas d'entraînement d'un
  autre modèle avec ce moteur à des fins commerciales ;
- l'audio **peut être transmis** à quelqu'un d'autre, mais **seulement pour un
  usage non commercial et en joignant la licence** (« anyone who gets… their
  output from you also gets a copy of these terms »). En pratique, donc : du
  XTTS reste **hors de la banque de voix destinée au partage public** ;
- au premier téléchargement, le moteur demande l'accord sur cette licence ; il
  peut être donné d'avance avec `COQUI_TOS_AGREED=1` (c'est ce que font les
  scripts de l'atelier, avec le commentaire qui va bien).

### Mesures relevées sur la RTX 4060 (14/09/2026)

| Mesure | Valeur |
|---|---|
| Modèle chargé en | 10 à 12 s |
| Mémoire vidéo au pic | **2,21 Go** (sur 8) |
| 42 phrases = **8,9 min d'audio** | calculées en **171 s** → **×3,1 le temps réel** |
| Temps moyen par phrase | **4,08 s** (de 0,53 s à 11,01 s) |
| Sortie | WAV mono **24 000 Hz** |

### Vérifier que le bac à sable est bon (sans rien télécharger)

    <atelier NIMM Voix>\outils\xtts_tts\.venv\Scripts\python.exe <atelier NIMM Voix>\outils\xtts_tts\_verifier_installation.py

Affiche Python, PyTorch + CUDA, transformers et l'import de `coqui-tts`. À
reprendre/adapter pour un vérificateur maison de l'installation XTTS ici.

---

## 2. Les voix françaises sont DÉJÀ là : ne rien télécharger

C'est la bonne nouvelle de ce mémo. **Les 35 voix françaises que Laurent
utilise avec Kyutai sont déjà présentes dans NIMM ePub**, et se trouvent être
**exactement le format dont XTTS a besoin** comme référence de clonage :

    <dossier du projet>\kyutai_service\voix_fr\cml-tts\fr\<identifiant>_enhanced.wav

- **35 fichiers WAV** (≈ 450 à 550 Ko chacun, soit ≈ 9 à 10 s de parole) ;
- une seule voix par fichier, propre, déjà nettoyée par Kyutai ;
- provenance **CML-TTS**, licence **CC BY 4.0** (attribution : Kyutai + CML-TTS,
  voir `kyutai_service\ATTRIBUTION.md`) — les **extraits eux-mêmes** sont libres
  de droits, y compris pour un partage, sous réserve de l'attribution (le
  **moteur XTTS**, lui, reste en usage non commercial : voir § 7) ;
- chaque fichier a en plus sa **« empreinte »** `.safetensors` de 250 Ko (utile
  au seul moteur Kyutai — XTTS n'en a pas besoin).

**XTTS v2 se contente de 6 secondes de référence** : ces extraits de 9-10 s
sont donc parfaits tels quels. Aucun téléchargement, aucune préparation à
faire. Le catalogue Kyutai de `modules/tts.py` (section « KYUTAI TTS », avec
ses 35 entrées `kyutai:<identifiant>` et leurs prénoms français — Adèle,
Blanche, Céleste, Diane…) fournit **déjà la liste des identifiants et les
genres** : il suffit de la réutiliser.

### Ce qu'il reste à faire pour cette bibliothèque de voix XTTS

1. faire un **service XTTS** qui liste ces voix (`GET /voix`) et sait en
   cloner une à la demande (`POST /tts`) — même schéma que
   `servir_kyutai.py` ;
2. proposer à Laurent un **lot d'écoute** des 35 voix clonées (une phrase
   identique pour toutes), avec un `index_ecoute.txt` à annoter : il a
   l'habitude, il l'a fait pour Kyutai ;
3. **réutiliser les 35 prénoms** du catalogue Kyutai pour retrouver ses
   repères, avec une région distincte (par exemple « 🇫🇷 France (XTTS) ») et un
   identifiant distinct (`xtts:<identifiant>`) — attention, **la voix « Adèle »
   de Kyutai et celle d'XTTS ne sont pas identiques** (deux moteurs
   différents) : à Laurent de dire s'il préfère les mêmes prénoms ou des noms
   neufs ;
4. noter dans la fiche de chaque voix : source (CML-TTS), licence
   (**CC BY 4.0**), attribution (**Kyutai + CML-TTS**) — c'est la règle de
   l'atelier et elle vaut ici aussi.

---

## 3. Mettre Kyutai en veille

Demande de Laurent : **Kyutai doit passer en veille**, parce qu'il occupe
plusieurs gigaoctets de carte graphique (mesuré à l'atelier : ≈ 3,8 Go pour le
modèle seul) et que **les deux moteurs ne peuvent pas tourner ensemble**.

Concrètement, dans NIMM ePub :

1. **`START.bat`** : le bloc qui allume le moteur Kyutai (`kyutai_service\
   DEMARRER_KYUTAI.bat`, test `curl http://127.0.0.1:8082/sante`) doit être
   **neutralisé** — en commentaire (`rem`), avec une note qui explique comment
   le rétablir. Le lecteur, lui, démarre normalement.
2. **Rien à supprimer** : le dossier `kyutai_service`, son `.venv`, ses voix et
   ses scripts restent en place. Réveiller Kyutai = relancer
   `DEMARRER_KYUTAI.bat` (ou rétablir le bloc de `START.bat`).
3. **Le code du lecteur n'a pas besoin de changer** : quand le moteur Kyutai ne
   tourne pas, les voix `kyutai:` remontent déjà une erreur claire
   (`KyutaiIndisponible` : « le moteur de voix Kyutai ne repond pas… lance
   DEMARRER_KYUTAI.bat »). C'est le comportement voulu en veille.
4. **Documentation** : le dire dans `LIRE_MOI.md` du service, dans
   `ARCHITECTURE.md` et dans le BACKLOG de NIMM ePub, pour que personne (ni
   Cline, ni Laurent dans trois mois) ne croie à une panne.

---

## 4. Le « switch » : un seul moteur lourd à la fois

Ce que Laurent veut : pouvoir **basculer** entre Kyutai et XTTS v2, **jamais
les deux en même temps**. Trois façons de le faire, de la plus simple à la plus
complète — **à trancher avec lui** :

- **(a) Deux lanceurs, aucun automatisme** *(le plus simple, recommandé)* :
  `START.bat` ne lance plus aucun moteur lourd ; on double-clique soit sur
  `DEMARRER_KYUTAI.bat`, soit sur un nouveau `DEMARRER_XTTS.bat`, selon ce
  qu'on veut écouter. Un seul geste, aucune confusion possible, aucun risque
  d'écraser la mémoire de la carte graphique.
- **(b) Un menu au démarrage** : `START.bat` demande « Quel moteur de voix ?
  1 = Kyutai, 2 = XTTS v2, 0 = aucun » puis lance le bon. Pratique, mais un
  choix à faire à chaque démarrage, et gênant si le démarrage vient du
  téléphone.
- **(c) Garde-fou automatique** : les deux moteurs restent lançables, mais
  chacun **refuse de démarrer si l'autre répond** (test `/sante` réciproque).
  Plus fin, un peu plus de code, et Laurent ne comprend pas toujours *pourquoi*
  ça refuse.

Dans tous les cas, prévoir un **petit état du moteur** — un `GET /sante` sur
chaque port (Kyutai : **8082** ; XTTS : proposer **8083**) — et idéalement un
indicateur côté écran du lecteur. Si les deux services coexistent, il est aussi
utile de **détecter « port déjà occupé »** pour afficher « un moteur de voix est
déjà en route » plutôt qu'une trace technique.

---

## 5. Python 3.14 ≠ 3.12 : pourquoi XTTS doit être un service séparé

Le lecteur tourne en **Python 3.14** (`C:\Python314`). Les deux moteurs lourds
exigent **Python 3.12 + PyTorch** : ils ne peuvent pas vivre dans le lecteur.
Ils travaillent donc **chacun dans son propre environnement**, à côté, et
communiquent par le réseau — c'est la règle déjà posée avec Kyutai, ce mémo ne
fait que la répéter pour XTTS.

- Kyutai : `kyutai_service\.venv` (Python 3.12) + `servir_kyutai.py`, port 8082 ;
- XTTS v2 : pour l'instant `<atelier NIMM Voix>\outils\xtts_tts\.venv` (Python 3.12)
  dans l'atelier → **à installer ici** (par exemple `xtts_service\.venv`), port
  8083, avec son `INSTALLER_XTTS.bat`, son `DEMARRER_XTTS.bat` et son
  `LIRE_MOI.md`, exactement comme pour Kyutai.

### Arrêter le moteur Kyutai (procédure sûre)

- **Le geste normal : fermer sa fenêtre.** Le service embarque un « gardien »
  qui s'arrête dès que la fenêtre disparaît ; la mémoire de la carte est rendue
  en quelques secondes, et le lecteur continue de fonctionner.
- **Si la fenêtre a été perdue** : identifier le bon processus — **ne jamais
  tuer les Python du lecteur, qui tournent en 3.14** :

      Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
          Select-Object ProcessId,CreationDate,CommandLine | Format-List

  puis `Stop-Process -Id <PID>` sur celui dont la ligne de commande contient
  `servir_kyutai.py` **et** `kyutai_service\.venv` (vérifier le chemin : c'est
  le seul garde-fou).
- **Vérifier que le moteur est bien éteint** :

      curl -s -o NUL --max-time 2 http://127.0.0.1:8082/sante

  (échec = moteur arrêté ; c'est le test déjà utilisé dans `START.bat`).
- **Ne jamais interrompre une génération en cours** : les demandes sont mises
  en file d'attente une par une (le moteur n'est pas « thread-safe »).

---

## 6. Ce que Laurent attend, concrètement (liste de travail)

1. **Installer XTTS v2 dans NIMM ePub** comme **service séparé**, sur le modèle
   exact de `kyutai_service` (dossier + `.venv` Python 3.12 + `INSTALLER_…bat`
   + `DEMARRER_…bat` + `LIRE_MOI.md` + `servir_xtts.py`), sur un **port libre**
   (proposer 8083) — **sans jamais ajouter PyTorch au lecteur**.
2. **Récupérer les voix françaises déjà disponibles** (§ 2) : les 35 extraits
   de `kyutai_service\voix_fr\cml-tts\fr\` servent **tels quels** de référence
   de clonage. Aucun téléchargement. Catalogue + licences + attribution.
3. **Lot d'écoute** des voix clonées, avec `index_ecoute.txt` à annoter, pour
   que Laurent choisisse ses préférées (il l'a fait pour Kyutai, il attend la
   même chose ici).
4. **Mettre Kyutai en veille** (§ 3) : `START.bat` n'allume plus le moteur lourd
   automatiquement ; le dossier reste en place, prêt à être réveillé.
5. **Mettre en place le « switch »** (§ 4) : **un seul moteur lourd à la fois**.
   Option à choisir avec Laurent.
6. **Documenter** : `ARCHITECTURE.md`, `BACKLOG.md` (l'entrée « Pistes de
   clonage de voix française à évaluer » existe déjà) et le `LIRE_MOI.md` du
   nouveau service.
7. **Rester à 1 ou 2 items par session** — c'est la règle de Laurent, et il y a
   ici de quoi faire plusieurs sessions : (installation + veille de Kyutai)
   d'abord, puis (voix + lot d'écoute), puis (switch).

## 7. Points de vigilance (à ne pas rater)

- **Licence du modèle : CPML, non commerciale — elle couvre le modèle ET les
  audios produits.** XTTS v2 est un **moteur d'essai** : son audio **n'entre
  pas** dans une banque de voix destinée à un partage public, et **aucun usage
  commercial** n'est permis ; une transmission ponctuelle est autorisée **à
  condition de joindre la licence** et de rester hors commerce. Comme pour
  Kyutai et NeuTTS, la bonne façon de l'intégrer est un **composant externe
  optionnel** (dossier à part,
  environnement à part, installé par l'utilisateur, appelé par le réseau) —
  **jamais embarqué dans le programme**.
- **La voix de référence de Laurent est privée.** L'extrait de son livre audio
  (Stephen King, lu par un comédien professionnel) a servi au **test** : usage
  privé, jamais diffusé (la voix d'un comédien est protégée en France). Pour
  une source **libre de droits** — le point qui compte le jour où l'on voudra
  partager —, ce sont **les 35 voix CML-TTS (CC BY 4.0)** qu'il faut
  utiliser : c'est tout l'intérêt du § 2.
- **Limite de longueur : 273 caractères en français.** Au-delà, le moteur
  prévient lui-même (« The text length exceeds the character limit of 273 for
  language 'fr' … truncated audio ») et coupe : le script de l'atelier découpe
  donc en morceaux de **250 caractères**, recollés **sans silence**, et ne
  place un silence qu'en **fin de vraie phrase**. **À vérifier chez vous** :
  `MAX_CHUNK_CHARS` dans `modules/tts.py` — s'il dépasse 250, prévoir un
  découpage propre dans la branche XTTS.
- **Vitesse et hauteur.** Le moteur **n'a aucun réglage de hauteur** (comme
  Kyutai) : la hauteur reste gérée par le lecteur. Une **vitesse** existe, mais
  seulement au niveau bas du modèle (`synthesize(..., speed=1.0)`) — l'API
  simple ne la transmet pas ; donc, en pratique, laisser le lecteur s'en
  occuper.
- **Une seule génération à la fois**, comme Kyutai (le moteur n'est pas
  « thread-safe ») : garder la file d'attente du modèle existant.
- **Première mise en route : 2,09 Go à télécharger.** Prévenir Laurent, ou
  faire comme pour Kyutai (un `_telecharger.py` dédié à l'installation, qui
  affiche une barre de progression).
- **Ne rien modifier dans l'atelier `<atelier NIMM Voix>`** : il est là comme
  référence (lecture seule pour cette session).

---

## 8. Questions à trancher avec Laurent (avant d'agir)

**Réponses du 14/09/2026** :
1. **Quel moteur par défaut ?** → **le dernier moteur utilisé** : celui qui
   tournait la dernière fois se rallume au lancement de NIMM ePub (via un
   petit fichier de réglage `data\moteur_voix.txt`, avec la possibilité de
   choisir « aucun »). Précautions : ne rien relancer si un moteur tourne
   déjà, et éteindre l'autre avant d'allumer (un seul à la fois).
2. **Quelle forme de « switch » ?** → un **bouton dans NIMM ePub**, à faire
   **après** l'installation de XTTS (l'option (a) « deux lanceurs à la main »
   sert de repli).
3. **Les 35 voix XTTS : quels noms ?** → *à trancher au moment du branchement
   dans le lecteur* : mêmes prénoms que le catalogue Kyutai (recommandé :
   Laurent retrouve ses repères), avec la région « 🇫🇷 France (XTTS) » et
   l'identifiant `xtts:<identifiant>`.
4. **Garde-t-on Kyutai installé** (≈ 4,5 Go) même en veille ? → **oui**, rien
   n'est supprimé (confirmé : XTTS est plus léger, mais Kyutai reste en place
   tant que la comparaison à l'oreille n'est pas faite).

### Historique de la question initiale

1. **Quel moteur par défaut ?** Kyutai passe en veille : est-ce XTTS v2 qui
   prend sa place « par défaut », ou ne lance-t-on **aucun** moteur lourd au
   démarrage (le plus économe) ?
2. **Quelle forme de « switch » ?** option (a), (b) ou (c) du § 4. La plus
   simple — et celle qui correspond le mieux à « l'un ou l'autre » — est **(a) :
   deux lanceurs à la main, aucun automatisme**.
3. **Les 35 voix XTTS : quels noms ?** mêmes prénoms que le catalogue Kyutai
   (Adèle, Blanche, Céleste…) ou noms neufs, pour éviter la confusion entre les
   deux moteurs ? Et veut-il **les 35 d'un coup**, ou **8 à 10 d'abord** pour un
   premier tri ?
4. **Garde-t-on Kyutai installé** (≈ 4,5 Go sur le disque) même en veille ? Rien
   ne se supprime sans son accord.

---

## Annexe A — Où sont les fichiers (atelier `<atelier NIMM Voix>`, en lecture seule)

| Fichier | Ce qu'on y trouve |
|---|---|
| `outils\xtts_tts\_install_xtts.cmd` | **l'installation complète et commentée** (les deux pièges inclus) |
| `outils\xtts_tts\_verifier_installation.py` | vérification du bac à sable (PyTorch, CUDA, coqui-tts) |
| `outils\xtts_tts\_preparer_reference.py` | fabriquer une référence (WAV mono 24 kHz, silences rognés) depuis n'importe quel audio |
| `outils\xtts_tts\_test_xtts.cmd` | lancer le test complet (~3 min de calcul) |
| `outils\xtts_tts\reference\` | voix de référence préparée + note d'origine (`ORIGINE_de_la_reference.txt`) |
| `scripts\tester_xtts.py` | **le script à réutiliser pour le service** : découpage, génération phrase par phrase, assemblage, mesures |
| `sorties\test_xtts_20260914\` | le test écouté et validé par Laurent (WAV 8,9 min + `mesures.txt` + `index_ecoute.txt`) |
| `ECOUTER_TEST_XTTS.cmd` | réécouter ce test |
| `ARCHITECTURE.md` | item de BACKLOG « Tester XTTS v2 » + journal (session 55) |

## Annexe B — Le code XTTS v2 minimal (tel qu'utilisé et validé)

```python
import os
os.environ.setdefault("COQUI_TOS_AGREED", "1")   # licence CPML : usage privé
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
wav = tts.tts(text=phrase, speaker_wav=reference_wav, language="fr",
              split_sentences=False)
```

- `.to("cuda")` est la façon **recommandée** (le paramètre `gpu=True` est
  déprécié, il déclenche un avertissement) — vérifié chez Laurent : le modèle
  est bien sur la carte, 2,2 Go au pic ;
- la sortie est en **24 000 Hz** (rééchantillonner si le lecteur attend autre
  chose) ;
- générer **phrase par phrase**, jamais le texte entier (mémoire + limite de
  273 caractères) ;
- le WAV sort **avant** les réglages du lecteur : le rognage des silences et
  l'accord de vitesse du lecteur s'appliquent ensuite, comme pour les autres
  moteurs.

## Annexe C — Le découpage de texte validé (dans `scripts/tester_xtts.py`)

1. découper sur la **ponctuation forte** (`. ! ? …`) ;
2. **recoller les fragments qui commencent par une minuscule** — sinon on place
   un blanc au milieu d'une phrase (défaut constaté et corrigé) ;
3. recoller aussi après les **abréviations** courantes (`M.`, `etc.`…) ;
4. au-delà de **250 caractères**, redécouper **en préférant les virgules**, et
   recoller ces morceaux **sans silence** ;
5. poser un silence (0,35 s) **uniquement entre deux vraies phrases**.




