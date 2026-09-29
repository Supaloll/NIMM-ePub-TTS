# Licences et attribution — `qwentts_service/`

**Tout ce qui suit autorise le partage de l'audio produit**, avec attribution.
C'est la différence avec XTTS v2, dont la licence interdit l'usage commercial.

## Le moteur

- **`qwentts.cpp`** (portage C++/GGML de Qwen3-TTS, ServeurpersoCom) : **MIT**.
- **Le paquet Python** `realtimetts-qwen-native-cpu` (KoljaB) : **MIT**.
- **Qwen3-TTS** (modèle et codec, équipe Qwen / Alibaba) : **Apache-2.0**.

## Les voix

- Les **35 extraits** viennent de **CML-TTS** (lecture de textes du domaine
  public) : **CC BY 4.0**. Ce sont **les mêmes** que ceux de Kyutai — c'est ce
  qui permet de passer d'un moteur à l'autre sans changer de voix.
- Attribution à citer si l'audio sort des ateliers : **Kyutai + CML-TTS**, plus
  **Qwen3-TTS** (Apache-2.0) et **qwentts.cpp** (MIT).

## Ce que ça change à l'usage

L'audio produit **peut** sortir de l'atelier (partage, publication), avec
l'attribution ci-dessus. Les voix, elles, suivent leur propre licence : celles
du **domaine public** sont libres ; les extraits venus de **livres audio du
commerce** (comédiens = personnes réelles) restent en **usage privé**.
