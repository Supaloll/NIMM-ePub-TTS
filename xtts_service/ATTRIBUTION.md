# Attributions et licences — moteur XTTS v2 dans NIMM ePub

Tout ce qui suit est utilisé uniquement pour **écouter des livres à titre
privé** sur la machine de Laurent. Deux licences différentes se croisent ici,
et **elles ne disent pas la même chose** :

- les **extraits de voix** (CML-TTS) sont **libres**, y compris pour un
  partage, à condition de citer les auteurs ;
- le **moteur** (modèle XTTS v2) est **non commercial**, et son audio aussi.

## 1. Le moteur (modèle de synthèse vocale)

- **XTTS v2** — `coqui/XTTS-v2`
  - Auteur d'origine : **Coqui** ; bibliothèque reprise et maintenue par le
    laboratoire suisse **Idiap** (`idiap/coqui-ai-TTS`).
  - Licence : **Coqui Public Model License (CPML)** — texte lu le 14/09/2026 :
    « This license allows only non-commercial use of a machine learning model
    **and its outputs** ».
  - **Ce que cela veut dire en clair** :
    - l'usage de Laurent (écoute personnelle, essai, loisir) est **couvert** :
      la licence cite explicitement « personal use for research, experiment,
      and testing… personal study, private entertainment, hobby projects » ;
    - **aucun usage commercial** de l'audio produit, et pas d'entraînement
      d'un autre modèle avec ce moteur à des fins commerciales ;
    - l'audio peut être transmis à quelqu'un d'autre **uniquement pour un
      usage non commercial et en joignant cette licence**.
  - **Conséquence pratique** : l'audio XTTS **n'entre pas** dans une banque de
    voix destinée à un partage public. C'est un **moteur d'essai**, installé
    comme composant externe optionnel — **jamais embarqué** dans NIMM ePub.
  - Fichiers concernés : le modèle (2,09 Go) est téléchargé par `coqui-tts`
    dans le cache de l'utilisateur au premier chargement, puis réutilisé.

## 2. Les voix (35 extraits français de référence)

- **kyutai/tts-voices**, dossier `cml-tts/fr`
  - Licence : **CC BY 4.0** (attribution obligatoire)
  - Source des enregistrements : jeu de données **CML-TTS**
    (attribution : **Kyutai** + jeu de données **CML-TTS**)
  - Fichiers concernés : `voix_fr/` — les 35 extraits de référence
    (`<identifiant>_enhanced.wav`, 9 à 10 s chacun, ≈ 500 Ko).
  - Ce sont **exactement les extraits déjà utilisés par le moteur Kyutai**
    de NIMM ePub : `_telecharger.py` les copie depuis
    `kyutai_service\voix_fr\cml-tts\fr\` (et les re-télécharge depuis la
    banque si ce dossier n'existe plus).
  - XTTS v2 **clone** ces voix : il ne les contient pas. Les extraits
    eux-mêmes restent libres (CC BY 4.0), mais **l'audio produit** par le
    moteur suit la licence du moteur (voir plus haut).

## 3. Code et bibliothèques

- **coqui-tts 0.27.5** (fork maintenu par **Idiap**) : licence **MPL-2.0**
  (Mozilla Public License 2.0) — vérifié dans les métadonnées du paquet le
  14/09/2026.
- **PyTorch 2.8.0+cu128** et **torchaudio 2.8.0+cu128** : licence
  **BSD-3-Clause** (voir `torch` installé dans `.venv`).
- **transformers 4.57.6** : licence **Apache-2.0**.
- Aucun de ces paquets n'est embarqué dans NIMM ePub : ils vivent dans
  `xtts_service/.venv`, un environnement **séparé**, installé par
  `INSTALLER_XTTS.bat` et appelé par le réseau (HTTP sur `127.0.0.1`).

## 4. La voix personnelle de Laurent

L'extrait de son livre audio (Stephen King, lu par un comédien
professionnel) a servi au **test** dans l'atelier NIMM Voix : usage privé,
**jamais diffusé** (la voix d'un comédien est protégée en France). Il n'est
**pas** dans ce dossier : seules les voix CML-TTS ci-dessus y sont utilisées.
