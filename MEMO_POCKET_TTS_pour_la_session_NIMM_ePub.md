# Mémo pour la session NIMM ePub — installer Pocket TTS et importer des voix clonées

_Écrit par la session NIMM Voix dans la nuit du 20 au 21/09/2026, à la demande
de Laurent (« tu peux laisser une note pour NIMM ePub, il saura quoi faire »)._

Ce mémo ne demande **rien** : il transmet un état des lieux, une procédure
vérifiée et les pièges déjà payés. **Rien n'a été modifié chez toi** — NIMM ePub
a seulement été **lu** (dossiers des services, ATTRIBUTION.md, LISEZ-MOI du
service Kyutai).

---

## 1) Ce que Laurent veut

Il a fait **cloner 18 voix françaises avec Pocket TTS** dans NIMM Voix, les a
**écoutées** et a **retenu 17 voix sur 19** (+ JEAN EDGAR, validée le 18/09).
Il veut **les importer dans le lecteur** NIMM ePub.

Point à savoir avant tout : **ces voix ne sont PAS des fichiers de voix Kokoro**
(`voices-*.bin`). Le fichier de voix, ici, c'est un **extrait audio de
référence** (WAV) que **Pocket TTS recharge** pour parler avec ce timbre. Il n'y
a donc rien à fusionner dans `voices-v1.0.bin` : c'est un **nouveau moteur** à
brancher, comme l'ont été Kyutai, NeuTTS et XTTS.

## 2) Où sont les voix (et ce qu'elles sont)

```
G:\NIMM Voix\sorties\pocket_tts_retenues_20260920\
    A_fichiers_de_voix\   18 x <voix>_reference.wav   <-- LES FICHIERS DE VOIX
                          WAV mono 24 kHz, 12,5 s a 28 s (le moteur tronque a 30 s)
    B_ecoute\             36 WAV : 01 (texte de reference) + 02 (phrase piegee)
    INDEX_RETENUES.txt    verdicts de Laurent, etoiles, mesures voix par voix
    FICHE_VOIX.txt        provenance, licences, marche a suivre
```

Durées mesurées (fichier de référence) : de **12,5 s** (`Femme48897`) à
**28,0 s** (`JEAN_EDGAR`). Rappel de la règle de l'atelier, mesurée le 18/09 :
viser **10 à 20 s** de parole, **jamais moins de 5 s** (en dessous, le résultat
dérive : 2 s et 6,5 s de référence donnent près de 2 demi-tons d'écart).

Les deux voix **écartées** par Laurent (`Femme121235456`, `Homme45788656512`)
sont dans le lot d'écoute `sorties\pocket_tts_decoupage_ok_20260920\` mais **pas**
dans le dossier des retenues.

## 3) Installer le moteur (procédure **vérifiée** ici)

Ce qui tourne aujourd'hui dans NIMM Voix : **`pocket-tts` 3.1.0**,
**Python 3.14.3**, **PyTorch 2.14.0+cpu** (donc **sans carte graphique** : le
moteur est fait pour le processeur).

Le script d'installation existe déjà et fait tout :
**`G:\NIMM Voix\outils\pocket_tts\_installer_pocket_tts.cmd`** — il crée un
environnement **dédié**, installe **PyTorch CPU** puis **pocket-tts**, et écrit
un journal (`G:\NIMM Voix\logs\pocket_tts_install_20260917.log`). Compte **5 à
15 minutes** de téléchargement (≈ 300 Mo pour PyTorch CPU au lieu de 3 Go).

Les trois commandes qu'il exécute, si tu préfères les refaire chez toi :

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python.exe -m pip install pocket-tts
```

**Le modèle français se télécharge au premier usage** : `--language french_24l`
→ `model.safetensors` de **641 Mo** dans le dépôt Hugging Face
`kyutai/pocket-tts`. ⚠️ **Ce dépôt est « gated »** : Laurent doit **accepter les
conditions une fois** sur la page du dépôt (sinon erreur 403). C'est la seule
étape qui dépend de lui — et elle est **déjà faite** sur cette machine, donc si
ton service utilise le même cache Hugging Face, rien à télécharger.

## 4) Les deux façons de s'en servir

**a) En ligne de commande (le plus simple pour un essai) :**

```cmd
.venv\Scripts\pocket-tts.exe generate --language french_24l ^
    --text "Le texte a lire" ^
    --voice "G:\NIMM Voix\sorties\pocket_tts_retenues_20260920\A_fichiers_de_voix\Femme001_reference.wav" ^
    --max-tokens 200 ^
    --output-path "sortie.wav"
```

**b) En service (recommandé pour le lecteur, c'est le modèle de tes services
existants)** : Pocket TTS a une commande `serve` intégrée — le moteur est chargé
**une seule fois**, ce qui supprime le rechargement du modèle à chaque phrase
(ici, chaque génération relance le programme et recharge tout : c'est ce qui
fait 35 à 47 s par voix).

```cmd
.venv\Scripts\pocket-tts.exe serve --language french_24l ^
    --default-voice "<chemin d'un WAV de reference>" --host 127.0.0.1 --port <port>
```

Ce qu'il expose (vérifié dans le code du paquet, `pocket_tts\main.py`) :

| Route | Rôle |
|---|---|
| `GET /` | petite page de démonstration |
| `GET /health` | « es-tu prêt ? » |
| `POST /tts` | formulaire `text` (+ `voice_url` **facultatif** : une autre voix pour cette requête) → WAV |

Deux remarques utiles : la **voix par défaut est résolue au démarrage** (une
requête sans `voice_url` ne paie donc pas l'encodage de la voix), et donner
`--voice <wav>` en ligne de commande fait que **le nom de fichier suffit** comme
référence — pas besoin de passer par les voix prédéfinies de Kyutai.

## 5) Le mode d'emploi du texte — les pièges DÉJÀ payés

C'est la partie la plus précieuse : ces constats viennent de **mesures** faites
ici les 17 et 18/09. À ne pas redécouvrir à tes frais.

1. **Le nettoyage du texte est obligatoire.** L'apostrophe courbe (**U+2019**)
   et le tiret cadratin (**U+2014**) **ne sont pas dans le vocabulaire** du
   modèle français : le moteur les reçoit comme des octets bruts au milieu des
   mots (« de d'habitude », « Don't habitude », « é gréé »).
   ⚠️ **Divergence à retenir** : ta chaine XTTS/NeuTTS recommande d'écrire `…`
   au lieu de `...` — ici c'est **l'inverse** : le tokenizer de Pocket TTS
   connaît `...` (c'est même un marqueur de frontière de phrase) et **pas** `…`.
2. **Découper par morceaux d'environ 200 tokens** (`--max-tokens 200`) et
   **couper entre les phrases**. Mesuré : à 50 tokens, le texte est coupé au
   milieu des phrases et on entend un parasite **à chaque collage** ; à **250
   tokens le moteur décroche** (14,8 s d'audio au lieu de 29 s, du texte n'est
   pas lu). Recette validée par l'oreille de Laurent : **nettoyage + 200 tokens
   + réglages par défaut** (température 0,7).
3. **Les phrases très longues sont sautées** : au-delà d'environ **350
   caractères**, le moteur accélère et **avale du texte**. À découper.
4. **Le contexte glissant** (ta règle, implémentée ici) : envoyer le contexte
   **seulement quand la phrase est prononcée par le même locuteur** que la
   précédente ; jamais de contexte pour la première phrase, jamais après un
   changement de personnage. Rappel mesuré : un contexte trop long **tronque** la
   phrase à lire (9,6 s devient 1,4 s).
5. **Aucun réglage de volume ni de vitesse** : il n'existe **rien** dans le
   moteur (relevé du `--help` : langue, voix, température, *noise clamp*, seuil
   de fin, *frames after EOS*, `--max-tokens`, étapes de décodage,
   quantification, dispositif — rien d'autre). Et **les deux varient d'une
   génération à l'autre** : trois prises du même texte donnent **−21,2 / −23,7 /
   −24,5 dBFS** et 11,3 / 12,3 / 13,2 s (aucune graine fixée). **Remède au
   montage** (`_monter_propre.py` : gain par segment, écarts de 7,2 dB ramenés à
   0,4 dB, fondus de 5 ms, pauses ramenées de 0,8-1,6 s à 0,40 s) — et **chez
   toi, tes deux curseurs** (hauteur, vitesse) font déjà le reste.
6. **Le débit est élevé** : environ **20 à 25 caractères/seconde** là où une
   lecture humaine naturelle en fait **15**. Ce n'est pas la voix, c'est **le
   moteur** (dix extraits différents donnent la même durée) — donc à traiter au
   lecteur, pas à la source.
7. **`estelle`** (la voix française fournie par Kyutai) **sort étouffée** :
   vérifié, le clone direct depuis son audio d'origine est encore plus sombre
   (centre du spectre 448 Hz contre 640 Hz). Nous l'avons **écartée** — les 18
   voix de Laurent viennent de **ses** extraits.
8. **Vitesse d'exécution** : environ **1× le temps réel** sur processeur (le
   français est une variante `24l` **non distillée**, que Kyutai annonce
   « seulement en aperçu »). Conséquence pratique : générer **en avance**, jamais
   à la volée dans un lecteur.

## 6) L'empreinte pré-calculée : faut-il la faire ?

Un fichier de voix figé (comme une empreinte du moteur 1.6B) s'obtient ainsi :

```cmd
.venv\Scripts\pocket-tts.exe export-voice "<audio ou dossier>" "<sortie.safetensors>" --language french_24l
```

Ce que ça coûte, et pourquoi **nous ne l'avons pas fait** (choix assumé) :

- chaque empreinte pèse **environ 33 Mo** (contre 256 Ko pour une empreinte du
  moteur 1.6B) → **18 voix ≈ 600 Mo** ;
- le **WAV de référence suffit** au moteur, et c'est un fichier lisible,
  transportable et vérifiable à l'oreille ;
- la commande `serve` **charge la voix une fois au démarrage** : l'avantage de
  vitesse de l'empreinte disparaît dans ce mode.

À faire **seulement si** ton service veut éviter tout encodage au démarrage, ou
si Laurent veut **figer** les voix. Réserve : une empreinte est liée aux poids
**actuels** du modèle (« states precomputed with the released weights »), et le
français de Pocket TTS est annoncé comme un **aperçu** → si Kyutai publie une
version finale, il faudra recalculer.

## 7) Les outils de NIMM Voix que tu peux lire ou réutiliser

Tous sous `G:\NIMM Voix\` :

| Outil | Ce qu'il fait |
|---|---|
| `outils\pocket_tts\_installer_pocket_tts.cmd` | l'installation (§3) |
| `outils\pocket_tts\_cloner_dossier.py` | clone **tout un dossier** en **un seul lot** (nivelage commun, index, CSV) |
| `outils\pocket_tts\_cloner_voix_depuis_fichier.py` | clone **un** fichier (MP3 → WAV 24 kHz, rognage des silences, mesures) |
| `outils\pocket_tts\_nettoyer_texte.py` | **le nettoyage du texte** (la liste complète des caractères à traiter) ; avec `_tester_tokenizer.py` et `_inspecter_texte.py` |
| `outils\pocket_tts\_monter_propre.py` | nivelage par segment, fondus de 5 ms, pauses ramenées à 0,40 s |
| `outils\pocket_tts\_mesurer_niveau.py` | niveau dBFS fenêtre par fenêtre + détection des chutes |
| `outils\pocket_tts\_mesurer_silences.py`, `_voir_decoupage.py` | silences d'un WAV ; morceaux réellement générés |
| `outils\pocket_tts\_test_contexte_long.py` | le contexte glissant (ta règle, implémentée) |
| `outils\pocket_tts\_apercu_francais.py`, `_comparer_reglages.py` | lots d'écoute, variantes A à D |
| `outils\pocket_tts\_tester_duree_reference.py`, `_tester_accent.py`, `_tester_voix_estelle.py` | les épreuves déjà citées au §5 |
| `scripts\mesurer_timbre_voix.py` | souffle de fond + aigus d'une voix |
| `scripts\mesurer_expressivite_voix.py` | mélodie (demi-tons), dynamique, part de parole |
| `scripts\mesurer_debit_voix.py` | caractères/seconde de parole réelle |
| `scripts\comparer_deux_voix.py` | deux voix côte à côte (débit, hauteur, mélodie, brillance) |
| `ARCHITECTURE.md` | le chantier Pocket TTS (étapes 8 à 18) et le journal de bord |
| `sorties\pocket_tts_*\` | les lots d'écoute, avec leurs `index_ecoute.txt` |

⚠️ Ces scripts sont **écrits pour l'arborescence de NIMM Voix** (chemins
relatifs) et sortent des `.txt` **en ASCII pur** (leçon du 17/09 : accents et
caractères spéciaux ne passent pas toujours en fenêtre noire). **Ne les déplace
pas** : lis-les, reprends la logique, ou appelle-les avec leur propre
environnement. Si tu as besoin d'une pièce **adaptée à ton service**, dis-le à
Laurent : l'atelier peut la préparer.

## 8) Licences et droits (à ne pas confondre)

- **Les 18 voix** : 17 viennent d'extraits du **domaine public** (extraits
  préparés par Laurent dans Audacity) → libres, y compris pour un partage.
  **JEAN EDGAR** vient d'un enregistrement fourni par Laurent : **personne
  réelle** → écoute privée sans problème, **partage = son accord** (à noter dans
  la fiche de la voix).
- **Le moteur** : poids **CC BY 4.0** → **citer Kyutai** si l'outil est partagé.
  L'audio produit, lui, suit les droits de **la voix**, pas ceux du moteur.
- Ne pas ajouter ici les voix `expresso` / `ears` de la banque Kyutai
  (**CC BY-NC** : usage non commercial, pas de partage).

## 9) Ce qui n'a PAS été fait, et ce qu'il faut éviter

- **Aucun fichier de NIMM ePub n'a été créé, modifié ni supprimé** par cette
  session : NIMM ePub a seulement été **lu**. Ce mémo est le seul dépôt déposé
  chez toi, et c'est un **nouveau** fichier.
- L'**installation du service Pocket TTS chez toi n'est pas faite** : c'est une
  décision à prendre **avec Laurent** (service séparé comme `neutts_service` ?
  appel direct du CLI ? quel port ? quel cache de voix ?).
- Rappels de l'atelier : **sauvegarde datée** avant toute modification d'un
  fichier de référence (`voices-v1.0.bin`, catalogues, base), **lanceur
  double-clic** pour tout ce que Laurent doit lancer lui-même, et **aucune
  suppression** (données, voix, lots) sans son accord.

## 10) Où lire les chiffres complets

`G:\NIMM Voix\ARCHITECTURE.md` : le chantier **Pocket TTS** (étapes 8 à 18) et
le **journal de bord** (sessions 57, 58, 60, 61). Les index des lots
(`sorties\pocket_tts_*\index_ecoute.txt`) donnent les mesures **voix par voix**.

Si quelque chose ici ne colle pas avec ce que tu vois sur le disque, **c'est le
disque qui a raison** : signale-le à Laurent, on corrigera le mémo.


