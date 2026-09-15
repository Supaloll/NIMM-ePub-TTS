# Le moteur de voix Kyutai — mode d'emploi

Ce dossier contient **l'appareil de voix Kyutai** de NIMM ePub : un
programme séparé du lecteur, qui fait parler les 35 voix françaises
libres du moteur **Kyutai TTS 1.6B**.

Il vit à côté du lecteur pour une raison simple : ce moteur a besoin de
**Python 3.12** et de PyTorch (4,5 Go), alors que le lecteur tourne sur
**Python 3.14**. Les deux ne peuvent pas cohabiter. L'appareil travaille
donc dans son coin, et le lecteur l'appelle par le réseau, comme il
appelle déjà Edge TTS.

## Le moteur s'allume tout seul avec le lecteur

**Depuis le 12/09/2026, `START.bat` (à la racine du projet) allume le moteur
en même temps que le lecteur** : un seul double-clic — ou un seul clic dans
l'application du téléphone — et les deux fenêtres s'ouvrent. La fenêtre du
moteur peut rester ouverte sur le bureau.

**Pour éteindre le moteur, il suffit de fermer sa fenêtre.** Un « gardien »
intégré au moteur surveille sa fenêtre et s'arrête dès qu'elle disparaît
(vérifié : le port se libère et la mémoire de la carte graphique est rendue
en quelques secondes). C'est le geste naturel — pas besoin de script d'arrêt.
Le lecteur, lui, continue de fonctionner : seules les voix Kyutai deviennent
indisponibles.

`START.bat` ne lance **jamais** un second moteur : il vérifie d'abord que
celui-ci ne répond pas déjà. Et par sécurité, le moteur lui-même refuse de
démarrer deux fois (deux modèles occuperaient 2 × 3,8 Go de carte
graphique).

| Fichier | Quand | Ce qu'il fait |
|---|---|---|
| **INSTALLER_KYUTAI.bat** | une seule fois | installe l'environnement (≈ 2,5 Go à télécharger) et récupère les voix + le modèle |
| **DEMARRER_KYUTAI.bat** | pour allumer le moteur **seul** (sans le lecteur) | charge le moteur (≈ 4 s) puis reste ouvert |
| *(rien)* | usage normal | `START.bat` s'occupe de tout |

Tout se passe dans `journal_installation.txt` (à ouvrir si un message
d'erreur apparaît). Tous ces fichiers peuvent être relancés sans risque :
ce qui est déjà installé ou déjà allumé n'est pas refait.

## Écouter avant de brancher

L'appareil allumé, on peut juger la qualité **sans toucher au lecteur** :

```cmd
cd "<dossier du projet>\kyutai_service"
.venv\Scripts\python.exe tester_service.py
```

Les fichiers arrivent dans `sortie_ecoute\` (3 phrases × 3 voix), avec un
`index_ecoute.txt` qui rappelle quelle voix a lu quoi. C'est la liste à
écouter pour dire oui ou non avant le branchement dans le lecteur.

## Ce que l'appareil écoute (pour information)

| Adresse | Rôle |
|---|---|
| `GET http://127.0.0.1:8082/sante` | « es-tu prêt ? » (état, carte graphique, nombre de voix) |
| `GET http://127.0.0.1:8082/voix` | la liste des voix disponibles |
| `POST http://127.0.0.1:8082/tts` | `{"texte": "...", "voix": "..."}` → un fichier WAV |
| `POST http://127.0.0.1:8082/recharger` | relit les dossiers de voix **sans éteindre le moteur** (utile après un ajout de voix) |

Il n'écoute que sur la machine elle-même (`127.0.0.1`) : le téléphone
n'y accède pas directement, c'est le serveur du lecteur qui s'en sert.

## Contenu du dossier

| Élément | Rôle |
|---|---|
| `servir_kyutai.py` | le service (charge le moteur une fois, une génération à la fois) |
| `tester_service.py` | l'écoute de contrôle (voir plus haut) |
| `tester_toutes_voix.py` | lot d'écoute des 35 voix françaises (une par fichier) |
| `_lister_banque.py` | inventaire de la banque Kyutai : combien de voix, par famille, avec quelle licence |
| `_tester_voix_etrangeres.py` | essai « voix étrangère lue sur du texte français » (accents) |
| `_telecharger.py` | récupère les voix et le modèle (appelé par l'installateur) |
| `.venv/` | l'environnement Python 3.12 du moteur (non versionné) |
| `voix_fr/` | les 35 voix françaises (non versionné, re-téléchargeable) |
| `voix_autres/` | voix d'autres familles pour les essais d'accent (non versionné) |
| `modele/` | le gros fichier du modèle s'il n'est pas déjà dans le cache (non versionné) |
| `sortie_ecoute/`, `sortie_ecoute_toutes/`, `sortie_ecoute_etrangeres/` | les WAV produits par les écoutes |
| `ATTRIBUTION.md` | licences (CC BY 4.0 : attribution Kyutai + CML-TTS obligatoire) |
| `requirements.txt` | les 11 paquets du moteur (voir plus haut) |
| `pyrightconfig.json` | réglage pour VS Code : voir « Bon à savoir » |

## Réglages possibles (avancé, facultatif)

| Variable | Défaut | Effet |
|---|---|---|
| `NIMM_KYUTAI_PORT` | 8082 | port d'écoute (à changer si occupé) |
| `NIMM_KYUTAI_HOST` | 127.0.0.1 | accepter aussi d'autres machines du réseau |
| `NIMM_KYUTAI_CFG` | 2.0 | fidélité à la voix (1,0 à 4,0) |
| `NIMM_KYUTAI_POIDS` | — | chemin du gros fichier si rangé ailleurs |

## Bon à savoir

- **VS Code affiche « Import "moshi.models.tts" could not be resolved »** sur
  `servir_kyutai.py` : c'est un **faux positif**, pas une erreur. VS Code
  analyse ce dossier avec le Python du **lecteur** (3.14), où `moshi` et
  `torch` n'existent pas — ils sont dans `.venv` (Python 3.12), l'environnement
  du moteur. Le fichier `pyrightconfig.json` de ce dossier le dit à VS Code
  (même réglage que dans l'atelier NIMM Voix). Si le message réapparaît après
  son ajout : **recharger la fenêtre VS Code** (`Ctrl+Maj+P` → « Developer:
  Reload Window »).
- Le moteur **occupe la carte graphique** (≈ 3,8 Go) tant qu'il est
  allumé ; les jeux ou d'autres gros programmes seront à l'étroit.
- Il génère **plus vite que la lecture** (mesuré : 115 s d'audio en 50 s)
  et son audio est **mis en cache** par le lecteur comme pour Kokoro et
  Piper : réécouter un passage déjà lu ne redemande rien au moteur.
- Aucun réglage de hauteur ni de vitesse n'existe dans le moteur : c'est
  le lecteur qui s'en charge (comme il le fait déjà pour Kokoro).
