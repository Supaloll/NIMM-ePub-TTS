# Attributions et licences — moteur NeuTTS (NIMM ePub)

_Relevé le 16/09/2026, à partir du dépôt officiel `github.com/neuphonic/neutts`,
de la collection Hugging Face `neuphonic` et du mémo de l'atelier NIMM Voix
(`G:\NIMM Voix\MEMO_NeuTTS_pour_la_session_NIMM_ePub.md`)._

## 1. Le logiciel et les modèles NeuTTS

- **Code et poids** : **NeuTTS Open License v1.0** (publiée le 11/12/2025).
  Ce qu'elle dit, en clair :
  - usage **gratuit** pour tout ce qui n'est **pas** commercial → l'usage
    familial de NIMM ePub est **entièrement couvert**, sans seuil ni redevance ;
  - usage commercial permis **en dessous de 5 M$ de chiffre d'affaires annuel** ;
  - **redistribution du modèle autorisée**, à condition de joindre la licence et
    de conserver les mentions d'attribution ;
  - le mot « **Output** » (contenu généré, **audio inclus**) est explicitement
    couvert : les livres audio produits suivent les mêmes règles.
- **Dépôts « gated »** : sur Hugging Face, l'accès aux modèles **et au codec**
  demande un compte et l'acceptation des conditions.

## 2. Pourquoi NeuTTS n'est PAS embarqué dans NIMM ePub

Cette licence n'est pas libre au sens strict (elle ajoute une limite
commerciale) et n'est donc **pas compatible avec la GPL-3.0** du programme :
le code de NeuTTS **ne peut pas** être intégré au dépôt de NIMM ePub.

**Solution retenue (la même que pour Kyutai et XTTS v2)** : un dossier à part
(`neutts_service`), un environnement à part (Python 3.12), installé par
l'utilisateur, **appelé par le réseau local**. NIMM ePub reste **GPL-3.0 pur** ;
NeuTTS n'est qu'un **composant externe optionnel**.

## 3. Les voix de référence (les extraits clonés)

- **CML-TTS** (`ylacombe/cml-tts`, Université fédérale de Goiás) : **CC BY 4.0**
  → **partageable**, avec attribution. Ce jeu est composé de **lecteurs
  bénévoles de livres du domaine public** (projet **LibriVox**) — exactement le
  registre de NIMM ePub.
  - **Attribution à conserver** : Kyutai (banque `kyutai/tts-voices`) +
    CML-TTS + LibriVox.
- **Extraits du domaine public** (les 19 « vraies voix » de Laurent) : issus de
  lectures libres de droits ; les fichiers sources vivent dans
  `Extraits de voix\`, **hors Git** (aucun audio ne va sur le dépôt).
- **Transcriptions** : produites localement par **Whisper large-v3** (modèle
  OpenAI, licence MIT), à l'atelier NIMM Voix, le 16/09/2026.

## 4. Le filigrane des audios produits

Chaque fichier audio généré par NeuTTS porte par défaut un **filigrane Perth**
(Perceptual Threshold, projet `resemble-ai/perth`) : une marque **inaudible**,
intégrée au signal. À savoir avant tout partage d'un audio produit ici.

## 5. À ne pas publier

Les audios produits par **XTTS v2** (licence CPML, non commerciale) et par
**NeuTTS** relèvent de licences à contraintes : ils restent **privés**, chez
chacun (c'est déjà le principe du cache audio local). Ce qui est
**partageable**, ce sont les **extraits de référence** et le **code**.
