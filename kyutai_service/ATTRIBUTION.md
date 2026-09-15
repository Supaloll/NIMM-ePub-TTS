# Attributions et licences — moteur Kyutai dans NIMM ePub

Tout ce qui suit est utilisé uniquement pour **écouter des livres à titre
privé** sur la machine de Laurent. Les attributions sont obligatoires
(licences CC BY) : ce fichier doit rester avec les fichiers concernés.

## 1. Le moteur (modèle de synthèse vocale)

- **Kyutai TTS 1.6B** — `kyutai/tts-1.6b-en_fr`
  - Auteur : **Kyutai** (laboratoire de recherche français, Paris)
  - Licence : **CC BY 4.0** (attribution obligatoire)
  - Fichiers concernés : `modele/dsm_tts_1e68beda@240.safetensors`
    (3,43 Go) + tokeniseurs et configuration dans le cache Hugging Face.

## 2. Les voix (35 timbres français)

- **kyutai/tts-voices**, dossier `cml-tts/fr`
  - Licence : **CC BY 4.0** (attribution obligatoire)
  - Source des enregistrements : jeu de données **CML-TTS**
    (attribution : **Kyutai** + jeu de données **CML-TTS**)
  - Fichiers concernés : `voix_fr/cml-tts/fr/` — pour chaque voix, une
    empreinte `.safetensors` (256 Ko, celle qui sert à la synthèse) et
    l'enregistrement de référence `.wav` (environ 10 s).

## 3. Ce que NIMM ePub n'utilise PAS

Les autres dossiers de la même banque de voix sont **écartés** :

- `expresso/` et `ears/` : licence **CC BY-NC** → usage privé uniquement,
  pas utilisés ici ;
- `vctk/`, `alba-mackenna/` (CC BY), `voice-zero` et les voix CC0 :
  non utilisés pour l'instant.

## 4. Code du moteur

- paquet **`moshi` 0.2.13** (code d'inférence de Kyutai) : licence MIT,
  voir `LICENSE` du projet Kyutai (`kyutai-labs/delayed-streams-modeling`).
- **PyTorch** 2.9.1 : licence BSD-3-Clause (voir `torch` installé dans
  `.venv`).
