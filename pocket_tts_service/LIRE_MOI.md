# pocket_tts_service — l'appareil de voix Pocket TTS

Ce dossier est le **moteur de voix Pocket TTS** (Kyutai) de NIMM ePub : un
moteur de **clonage**, qui lit n'importe quel texte avec le timbre d'un
**extrait de référence** de 3 à 15 secondes. Il vit **à côté du lecteur**, dans
son propre environnement Python 3.14, et il est appelé par le réseau — comme
`kyutai_service` (8082), `xtts_service` (8083) et `neutts_service` (8084).

**Pourquoi un dossier à part, alors que Python 3.14 est la version du
lecteur ?** Pour la même raison que les autres : le lecteur tourne **sans
PyTorch** (modèles ONNX légers, Kokoro et Piper). Y ajouter PyTorch (≈ 300 Mo)
et 641 Mo de modèle, ce serait alourdir un lecteur qui fonctionne bien. Ici le
moteur est isolé : il peut être installé, allumé, éteint ou supprimé **sans
toucher au lecteur**.

**Ce qui le distingue des autres moteurs :**

| | |
|---|---|
| Il tourne sur le **processeur** | pas sur la carte graphique : il **cohabite** donc avec Kyutai (qui l'occupe, lui), Edge, Kokoro et Piper |
| Il est **léger** | 100 M de paramètres (Kyutai : 1,8 milliard) — environ 300 Mo d'environnement |
| Il **clone** | un WAV de référence suffit ; **pas besoin du texte dit dans l'extrait** (contrairement à NeuTTS) |
| Il est **lent** | environ 1× le temps réel en français (`french_24l` non distillé, « aperçu » chez Kyutai) → la mesure le dira précisément |
| Il **varie** | **il n'est pas déterministe** (aucune graine dans le moteur) : volume et durée changent d'une prise à l'autre — d'où l'importance de la normalisation de niveau du lecteur |

---

## 🖱️ Les fichiers à double-cliquer

| Fichier | Quand | Ce qu'il fait |
|---|---|---|
| `INSTALLER_POCKET_TTS.bat` | **une seule fois** | crée l'environnement dédié et installe PyTorch **CPU** + `pocket-tts` (5 à 15 min). Relançable sans risque |
| `DEMARRER_POCKET_TTS.bat` | pour allumer le moteur **seul** (essai, diagnostic) | affiche ce que dit le moteur, sur le port **8085**. Fermer la fenêtre l'éteint |

Tout est écrit dans `journal_installation.txt` (l'installation) et
`journal_console.txt` (l'allumage à la main). En usage normal, c'est
**`START.bat`** qui allume le moteur, **dans sa fenêtre** (depuis le 21/09/2026,
demande de Laurent : fermer la fenêtre éteint le moteur, comme pour Kyutai).
Le service écrit aussi `arrete_volontaire.txt` quand sa fenêtre se ferme : c'est
le marqueur qui dit au lecteur « ne me rallume pas tout seul » (voir « Le
service » plus bas).

**Le modèle français n'est PAS téléchargé par l'installation** : il se charge au
premier usage (641 Mo), et il est **déjà dans le cache Hugging Face de cette
machine** (l'atelier NIMM Voix l'a récupéré le 17/09/2026, conditions acceptées).

## 🎙️ Les voix

```
voix\
    Femme001_reference.wav    ... 28 fichiers au 23/09/2026 : les VOIX de Laurent
    Homme002_reference.wav        - 18 copiées le 20/09/2026 (17 retenues du lot
    homme_grave_5649798_...         du 20/09 + JEAN_EDGAR) ;
                                  - 10 copiées le 23/09/2026 (le lot des
                                    « nouveaux découpages », toutes retenues).
```

- **Un fichier de voix = un extrait audio** : c'est ce que le moteur utilise
  pour parler avec ce timbre. Il n'y a **rien à fusionner** dans
  `voices-v1.0.bin` (ce fichier-là, ce sont les voix Kokoro).
- Extrait : **10 à 20 s** de parole (idéal), **jamais moins de 5 s** ; le moteur
  **tronque à 30 s**, et une référence plus longue rend la voix **plus grave**
  (mesuré : 133 Hz à 2 s → 116 Hz à 6,5 s).
- Étoiles, genres et mesures : les 18 voix du 20/09 sont dans
  `G:\NIMM Voix\sorties\pocket_tts_retenues_20260920\INDEX_RETENUES.txt` ; les
  10 voix du 23/09 dans
  `G:\NIMM Voix\sorties\pocket_tts_retenues_20260923\INDEX_RETENUES.txt`.
- Ajouter des voix : **copier le WAV** dans `voix\` (nom = identifiant +
  `_reference.wav`), ajouter la ligne au catalogue `POCKET_VOICES`
  (`modules/tts.py`), puis écrire leurs critères d'écoute avec
  `python test_voix/_importer_voix_pocket.py --ecrire` (après avoir lu
  l'aperçu). Le service les voit à son redémarrage, ou après `POST /recharger`.

## 📊 La mesure du 20/09/2026 — RÉSULTATS (étape 1 terminée)

Machine de Laurent : **i5-12400F (6 cœurs)**, 32 Go de RAM, RTX 4060.
Commande : `.venv\Scripts\python.exe _mesurer_debit.py` (voix **Femme001**,
phrases de Monte-Cristo, `max_tokens = 200`).

| Mesure | Valeur |
|---|---|
| **Chargement du modèle** | **1,7 s** (le modèle est en cache disque : aucun téléchargement) |
| **Encodage d'une voix** | **3,8 s** (une seule fois, au démarrage du service) |
| Phrase courte (« Non. », 4 car.) | 0,7 s d'audio en 0,7 s → **ratio 0,99** |
| Phrase moyenne (125 car.) | 8,9 s d'audio en 7,2 s → **ratio 0,81** |
| Phrase longue (295 car.) | 14,5 s d'audio en 12,0 s → **ratio 0,83** |
| **Ratio moyen** | **0,82** → le moteur est **plus RAPIDE que le temps réel** (×1,2) |
| **Projection** | **1 h d'audio ≈ 49 min de calcul** |
| **Mémoire** | 2,0 Go après calcul, **pic 2,3 Go** (RAM, pas carte graphique) |
| **Cœurs utilisés** | 6 par défaut |

**Deux constats qui comptent pour la suite :**

1. **Brider à 4 cœurs ne coûte RIEN** : la même mesure avec `--threads 4` donne
   **0,82** aussi (0,80 / 0,83 par phrase). On pourra donc **laisser 2 cœurs**
   au lecteur, à Kokoro et à Piper sans rien perdre. ✅
2. **Les phrases courtes ont un ratio proche de 1** (0,99-1,02) : il y a un
   **coût fixe par appel**, donc les répliques courtes coûtent cher au prorata.
   C'est une raison de plus pour **ne pas hacher** le texte en minuscules
   morceaux (la recette `max_tokens = 200` coupe déjà entre les phrases).

**Conséquence pratique** : ce n'est **pas** un moteur « à la volée » comme Edge
ou Kokoro, mais **49 min de calcul pour 1 h d'écoute** — donc parfaitement
utilisable avec le **cache audio** du lecteur : on génère en avance, et la
deuxième écoute est instantanée. À comparer : XTTS ≈ ×3,3 le temps réel,
Kyutai ≈ ×2,3, NeuTTS ×0,7 (carte graphique).

**À écouter** : `ECOUTER_LA_MESURE.bat` (ou le dossier `sortie_mesure\`) — trois
WAV, la voix **Femme001**, en trois longueurs de texte.

## 🔧 Les outils


| Fichier | Question à laquelle il répond |
|---|---|
| `servir_pocket_tts.py` | **le service** (port 8085) : c'est lui qui reçoit les phrases du lecteur |
| `tester_service.py` | **l'écoute de contrôle** : interroge le service comme le fait le lecteur, écrit un lot d'écoute dans `sortie_ecoute\` avec son `index_ecoute.txt` |
| `_mesurer_debit.py` | **combien de temps de calcul pour combien d'audio ?** Charge le modèle, chronomètre le chargement, l'encodage de la voix et chaque phrase, écrit 3 WAV à écouter et un `rapport_mesure.txt`. Options : `--voix`, `--quantize`, `--threads` |
| `ECOUTER_LA_MESURE.bat` | **double-clic** : ouvre le dossier des trois WAV de mesure, avec ce qu'il faut juger |
| `INSTALLER_POCKET_TTS.bat` | installe l'environnement (ci-dessus) |

**Usage** (depuis ce dossier) :

```cmd
.venv\Scripts\python.exe tester_service.py
.venv\Scripts\python.exe tester_service.py --voix Marthe --voix Theodore
.venv\Scripts\python.exe _mesurer_debit.py
.venv\Scripts\python.exe _mesurer_debit.py --threads 4 --quantize
```

## 🔌 Le service (port 8085)

Même contrat que `kyutai_service`, `xtts_service` et `neutts_service` — le
lecteur ne voit pas la différence :

| Adresse | Rôle |
|---|---|
| `GET http://127.0.0.1:8085/sante` | « es-tu prêt ? » (`pret: true` = modèle chargé) |
| `GET http://127.0.0.1:8085/voix` | la liste des voix disponibles |
| `POST http://127.0.0.1:8085/tts` | `{"texte": "...", "voix": "..."}` → un WAV |
| `POST http://127.0.0.1:8085/recharger` | relit le dossier des voix, **sans redémarrer** |

Ce qui le distingue des autres services :

- **une seule génération à la fois** : le modèle n'est pas thread-safe (c'est
  écrit dans son code) et il occupe déjà 4 cœurs ;
- **4 cœurs par défaut** (`NIMM_POCKET_TTS_COEURS`) : les 2 autres restent au
  lecteur, à Kokoro et à Piper (mesure du 20/09/2026 : brider ne coûte rien) ;
- **le texte est re-nettoyé ici** (apostrophe courbe, tiret cadratin, `…` → `...`)
  par sécurité, même si le lecteur nettoie déjà ;
- **la première phrase d'une voix paie son encodage** : 3,8 s (mesuré — la
  totalité du « Non. » à 4,4 s de calcul, c'est ça). Ensuite, c'est ~0,85 ;
- **le contexte glissant est ignoré** : l'API de Pocket TTS ne le propose pas
  (contrairement à Kyutai). Le lecteur peut l'envoyer, on ne s'en sert pas.

**Sans fenêtre** : `START.bat` lancera le service en arrière-plan, avec sa sortie
dans un journal. Pour l'éteindre sans fenêtre, le lecteur le fait par le port.

## ⚠️ Les pièges déjà payés (mesures de l'atelier NIMM Voix, 17-20/09/2026)

Le détail complet est dans `MEMO_POCKET_TTS_pour_la_session_NIMM_ePub.md`, à la
racine du projet.

1. **Le texte doit être nettoyé** : l'apostrophe courbe (**’**) et le tiret
   cadratin (**—**) **ne sont pas dans le vocabulaire** du modèle français
   (« de d'habitude », « é gréé »). Attention : il connaît `...` mais **pas**
   `…` — l'**inverse** du mémo XTTS/NeuTTS.
2. **Découper en morceaux d'environ 200 tokens**, coupés **entre les phrases**
   (à 50, il coupe au milieu et on entend un parasite à chaque collage ; à 250,
   il décroche et saute du texte).
3. **Les phrases de plus de ~350 caractères sont sautées** : à découper.
4. **Aucun réglage de volume ni de vitesse** dans le moteur, et les deux varient
   d'une prise à l'autre → normaliser au montage (chez nous :
   `modules/audio_gain.py` du lecteur) et ralentir par `atempo` si besoin.
5. **Débit élevé** : 20 à 25 caractères/seconde (une lecture humaine naturelle
   en fait ~15). Ce n'est pas la voix, c'est **le moteur**.
6. **Pas de carte graphique** : Kyutai (les auteurs) a mesuré qu'il n'y gagne
   rien (lot de taille 1, modèle minuscule) ; et la carte est déjà prise par
   Kyutai 1.6B (3,8 à 5,6 Go sur 8).

## 📜 Licences

Le détail complet (et les obligations d'attribution) est dans **`ATTRIBUTION.md`**,
dans ce dossier. L'essentiel :

- **Le moteur** : poids **CC BY 4.0** (citer **Kyutai**), code **MIT** ; dépôt
  Hugging Face « gated » (conditions acceptées le 17/09/2026 sur cette machine).
- **Les 18 voix du 20/09/2026** : 17 viennent d'extraits du **domaine public**
  (libres, y compris pour un partage) ; **JEAN_EDGAR** vient d'un enregistrement
  d'une **personne réelle** → écoute privée sans problème, **partage = accord de
  la personne**.
- **Les 10 voix du 23/09/2026** (importées depuis l'atelier NIMM Voix) : leurs
  extraits viennent de **livres audio du commerce** (Lizzie, Audible), lus par
  des **comédiens professionnels**. Écoute **privée** : d'accord. **Partage :
  interdit** sans l'accord de la personne — et l'extrait d'origine ne se diffuse
  pas. Le détail est dans la section **2 bis** d'`ATTRIBUTION.md`.
- Ne **pas** ajouter ici les voix `expresso` / `ears` de la banque Kyutai
  (**CC BY-NC** : ni commercial, ni partage).

## 🚧 Ce qui reste à faire (chantier ouvert le 20/09/2026)

1. ✅ **Installation + mesure du débit réel** (étape 1) — **FAITE le 20/09/2026**
   (voir « La mesure du 20/09/2026 — RÉSULTATS » ci-dessus) ;
2. 🔶 **le service** — **FAIT le 20/09/2026** : `servir_pocket_tts.py` (port 8085),
   `DEMARRER_POCKET_TTS.bat` et `tester_service.py` sont en place et éprouvés
   (18 voix, ratios 0,85-0,86). *Reste* : le lancement **sans fenêtre par
   `START.bat`** et le **voyant dans le lecteur** ;
3. **le catalogue** : `POCKET_VOICES` dans `modules/tts.py` (préfixe `pocket:`),
   avec les prénoms, genres et étoiles des 18 voix — **hérités de XTTS** (mêmes
   extraits) — et l'icône **🎒** dans les menus ;
4. **le branchement** : branche `pocket:` dans `POST /api/tts`, menus et casting,
   puis **l'écoute de Laurent avant de conclure**.

