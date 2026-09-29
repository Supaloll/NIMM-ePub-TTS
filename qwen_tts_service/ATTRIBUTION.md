# Attributions et licences — moteur Qwen3-TTS dans NIMM ePub

Tout ce qui suit est utilisé uniquement pour **écouter des livres à titre
privé** sur la machine de Laurent. Une partie des voix exige une
**attribution obligatoire** (licence CC BY 4.0) : ce fichier doit rester avec
les fichiers concernés.

## 1. Le moteur (modèle de synthèse vocale)

- **Qwen3-TTS-12Hz-0.6B-Base** — `Qwen/Qwen3-TTS-12Hz-0.6B-Base`
  - Auteur : **Qwen** (équipe d'Alibaba)
  - Licence : **Apache-2.0** (code **et** poids) — l'audio produit est donc
    **partageable**, contrairement à XTTS v2 (non commercial) et NeuTTS.
  - Fichiers concernés : les poids du modèle, dans le cache Hugging Face de
    l'utilisateur (`%USERPROFILE%\.cache\huggingface\hub`, déjà téléchargés
    par l'atelier **NIMM Voix** — rien n'a été retéléchargé ici).

## 2. Les voix (35 timbres français)

Les extraits sont **les mêmes** que ceux du moteur Kyutai : c'est ce qui
permet de changer de moteur sans changer de voix ni de prénom.

- **kyutai/tts-voices**, dossier `cml-tts/fr`
  - Licence : **CC BY 4.0** — attribution obligatoire
  - Source des enregistrements : jeu de données **CML-TTS**
    (attribution : **Kyutai** + jeu de données **CML-TTS**)
  - Fichiers concernés : `voix/` — les 35 extraits de référence
    (`*_enhanced_reference.wav`, environ 10 s chacun) et leur texte exact
    dans `voix/references.csv`.
  - Ces fichiers ont été **copiés depuis l'atelier NIMM Voix le
    26/09/2026** (`G:\NIMM Voix\outils\qwen3_tts\reference\kyutai\`), pour
    que ce service ne dépende d'aucun autre dossier.

## 3. Code du moteur

- paquet **`qwen-tts` 0.1.1** : dépôt QwenLM, licence **Apache-2.0** ;
- **PyTorch** (2.8.0+cu128) : licence **BSD-3-Clause** ;
- environnement utilisé aujourd'hui : celui de l'atelier NIMM Voix
  (`G:\NIMM Voix\outils\qwen3_tts\.venv`, Python 3.12). Le lanceur
  `DEMARRER_QWEN_TTS.bat` cherche d'abord un environnement **local**
  (`qwen_tts_service\.venv`) et n'emprunte celui-là que s'il n'y en a pas.

## 4. Ce que NIMM ePub n'utilise PAS

- les **voix Edge** ne sont pas clonées : imiter une voix Microsoft relève
  du « custom neural voice » (accès restreint) et ne serait pas partageable ;
- les autres familles de la garde-robe Qwen (voix NIMM, accent allemand,
  domaine public, CML-TTS restantes) ne sont **pas** installées ici : seules
  les 35 voix `qwen:` du catalogue le sont, pour la bascule depuis Kyutai.
