# Attributions et licences — moteur Pocket TTS dans NIMM ePub

_Relevé le 21/09/2026, à partir du dépôt officiel (`github.com/kyutai-labs/pocket-tts`),
de la page Hugging Face `kyutai/pocket-tts` et du mémo de l'atelier NIMM Voix
(`MEMO_POCKET_TTS_pour_la_session_NIMM_ePub.md`)._

Tout ce qui suit est utilisé uniquement pour **écouter des livres à titre
privé** sur la machine de Laurent. Les attributions sont obligatoires là où les
licences l'exigent : ce fichier doit rester avec les fichiers concernés.

## 1. Le logiciel et les poids

- **Pocket TTS** — `kyutai/pocket-tts` (et `kyutai/pocket-tts-without-voice-cloning`)
  - Auteur : **Kyutai** (laboratoire de recherche français, Paris)
  - **Code** : licence **MIT** (dépôt GitHub `kyutai-labs/pocket-tts`)
  - **Poids du modèle** : licence **CC BY 4.0** → **attribution obligatoire**
    (« Kyutai » à citer si l'outil ou une banque de voix est partagée)
  - Fichiers concernés : le modèle français `french_24l`
    (`languages/french_24l/model.safetensors`, 641 Mo) et le tokeniseur, dans le
    cache Hugging Face.
- **Dépôt « gated »** : l'accès au modèle demande un compte Hugging Face et
  l'acceptation de ses conditions. **C'est déjà fait sur cette machine**
  (17/09/2026) : l'installation n'a donc rien à télécharger.
- **Usage interdit par les auteurs** (rappelé dans leur licence) : l'usurpation
  ou le clonage d'une voix **sans consentement explicite et légal**, la
  désinformation, et tout contenu illégal, haineux ou portant atteinte à la vie
  privée. Notre usage (livres privés, extraits libres de droits) est couvert.

## 2. Les 18 voix

- **17 voix** viennent des **extraits du domaine public** préparés par Laurent
  (lectures libres de droits, découpées dans Audacity) : elles sont donc
  **libres, y compris pour un partage**.
- **`JEAN_EDGAR` (voix « Edgar »)** vient d'un enregistrement fourni par
  Laurent : **personne réelle** → l'écoute privée ne pose pas de problème, mais
  **tout partage de cette voix demande son accord** (à noter dans la fiche de
  la voix avant de la partager).
- **Ce sont les MÊMES extraits** que les voix `dp_*` d'XTTS et de NeuTTS
  (d'où les mêmes prénoms) : une seule provenance, trois moteurs.
- **Rappel de l'atelier** : cloner une voix pour l'écouter chez soi ne pose pas
  de problème ; c'est le **partage** qui est encadré (accord de la personne +
  licence de l'enregistrement).

## 3. Ce que NIMM ePub n'utilise PAS

- Les voix **`expresso`** et **`ears`** de la banque Kyutai (**CC BY-NC** :
  usage non commercial, pas de partage) ne sont **pas** employées ici.
- La voix **`estelle`** fournie par Kyutai a été **écartée** par l'atelier : elle
  sort étouffée (mesure du 18/09/2026).
- L'empreinte pré-calculée (`export-voice`, ~33 Mo par voix) n'est **pas**
  utilisée : l'extrait de référence suffit, et il reste lisible et vérifiable.

## 4. Où est le dossier ?

Le moteur vit **à côté du lecteur** (`pocket_tts_service/`), dans son propre
environnement Python, et il est appelé par le réseau local — exactement comme
Kyutai, XTTS et NeuTTS. Il ne tourne pas sur la carte graphique.
