# Le moteur de voix XTTS v2 — mode d'emploi

Ce dossier contient **l'appareil de voix XTTS v2** de NIMM ePub : un
programme séparé du lecteur, qui fait parler **les 35 voix françaises** de
NIMM ePub avec un moteur de **clonage** (le laboratoire suisse **Idiap**
maintient la bibliothèque `coqui-tts`).

Il vit à côté du lecteur pour la même raison que Kyutai : ce moteur a besoin
de **Python 3.12** et de PyTorch (≈ 5 Go), alors que le lecteur tourne sur
**Python 3.14**. Les deux ne peuvent pas cohabiter. L'appareil travaille donc
dans son coin, et le lecteur l'appelle par le réseau.

> ⚠️ **Licence à connaître** : le modèle `coqui/XTTS-v2` est sous *Coqui
> Public Model License* — **usage non commercial, et l'audio produit suit la
> même règle**. L'usage de Laurent (écoute personnelle, essai, loisir) est
> couvert ; **cet audio ne se diffuse pas et n'entre pas dans une banque
> partagée**. Détail dans `ATTRIBUTION.md`.

## Un seul moteur lourd à la fois

Kyutai et XTTS occupent **chacun la carte graphique** : les deux ne tiennent
pas ensemble. On allume donc **soit l'un, soit l'autre**.

**Pour l'instant, on allume XTTS à la main**, en double-cliquant sur
`DEMARRER_XTTS.bat` (il n'est pas encore branché dans `START.bat` : le
branchement viendra avec le bouton de bascule entre les deux moteurs).
Le lecteur, lui, s'adapte tout seul : les voix XTTS n'apparaissent dans les
menus que **lorsque le moteur est allumé et prêt** (c'est le principe des
« voix écoutables tout de suite » du 14/09/2026). Moteur éteint, les voix
Edge, Kokoro et Piper continuent de fonctionner normalement.

**C'est branché depuis le 14/09/2026** : les 35 voix XTTS sont dans le
catalogue du lecteur et le moteur répond bien à la lecture (`xtts:` traité
comme `kyutai:`). Un livre neuf casté automatiquement peut donc recevoir
une voix XTTS — il faudra alors **le moteur allumé pour l'écouter**.

**Pour éteindre le moteur, il suffit de fermer sa fenêtre** : un « gardien »
intégré surveille la fenêtre et s'arrête dès qu'elle disparaît (même
mécanisme que Kyutai, vérifié le 12/09/2026 : le port se libère et la mémoire
de la carte est rendue en quelques secondes).

| Fichier | Quand | Ce qu'il fait |
|---|---|---|
| **INSTALLER_XTTS.bat** | une seule fois | installe l'environnement (≈ 3,5 Go, PyTorch) et récupère les voix + le modèle (2,1 Go) |
| **DEMARRER_XTTS.bat** | pour allumer le moteur | charge le moteur (10 à 20 s) puis reste ouvert |
| **`_verifier_installation.py`** | en cas de doute | vérifie Python, PyTorch+CUDA, coqui-tts et le nombre de voix, **sans rien lancer** |

Tout se passe dans `journal_installation.txt` (à ouvrir si un message
d'erreur apparaît). Ces fichiers peuvent être relancés sans risque : ce qui
est déjà installé n'est pas refait.

## Écouter avant de brancher

L'appareil allumé, on juge la qualité **sans toucher au lecteur** :

```cmd
cd "<dossier du projet>\xtts_service"
.venv\Scripts\python.exe tester_service.py
```

Les fichiers arrivent dans `sortie_ecoute\` (3 phrases × 3 voix, les mêmes
phrases que pour Kyutai — pratique pour comparer les deux moteurs). L'option
`--longue` ajoute une phrase de plus de 273 caractères, pour vérifier que le
découpage automatique du service tient la route :

```cmd
.venv\Scripts\python.exe tester_service.py --nombre 1 --longue
```

## Ce que l'appareil écoute (pour information)

| Adresse | Rôle |
|---|---|
| `GET http://127.0.0.1:8083/sante` | « es-tu prêt ? » (état, carte graphique, nombre de voix) |
| `GET http://127.0.0.1:8083/voix` | la liste des voix disponibles |
| `POST http://127.0.0.1:8083/tts` | `{"texte": "...", "voix": "..."}` → un fichier WAV |
| `POST http://127.0.0.1:8083/recharger` | relit le dossier des voix **sans éteindre le moteur** |

Il n'écoute que sur la machine elle-même (`127.0.0.1`) : le téléphone n'y
accède pas directement, c'est le serveur du lecteur qui s'en sert.

## Contenu du dossier

| Élément | Rôle |
|---|---|
| `servir_xtts.py` | le service (charge le moteur une fois, une génération à la fois, découpe les textes longs) |
| `tester_service.py` | l'écoute de contrôle (voir plus haut) |
| `_telecharger.py` | récupère les voix de référence et déclenche le téléchargement du modèle |
| `_verifier_installation.py` | vérifie l'environnement sans rien lancer |
| `.venv/` | l'environnement Python 3.12 du moteur (non versionné, ≈ 7,7 Go) |
| `voix_fr/` | les 35 extraits de voix (copiés du moteur Kyutai, ou re-téléchargés) |
| `sortie_ecoute/` | les WAV produits par l'écoute de contrôle |
| `ATTRIBUTION.md` | licences (modèle CPML non commerciale ; extraits CC BY 4.0) |
| `requirements.txt` | les paquets du moteur et les deux pièges à ne pas rouvrir |
| `pyrightconfig.json` | réglage pour VS Code (voir « Bon à savoir ») |

## Comment le texte long est découpé (important)

Le moteur **refuse plus de 273 caractères en français** : au-delà, il le dit
lui-même et **coupe l'audio**. Le service découpe donc tout seul, selon la
logique validée à l'oreille le 14/09/2026 :

1. découper sur la **ponctuation forte** (`. ! ? …`) ;
2. **recoller** les fragments qui commencent par une minuscule — sinon un
   blanc se glisse au milieu d'une phrase ;
3. recoller aussi après les **abréviations** courantes (`M.`, `etc.`…) ;
4. au-delà de **250 caractères**, redécouper **en préférant les virgules**,
   et recoller ces morceaux **sans silence** ;
5. poser un silence (0,35 s) **uniquement entre deux vraies phrases**.

## Réglages possibles (avancé, facultatif)

| Variable | Défaut | Effet |
|---|---|---|
| `NIMM_XTTS_PORT` | 8083 | port d'écoute (à changer si occupé) |
| `NIMM_XTTS_HOST` | 127.0.0.1 | accepter aussi d'autres machines du réseau |
| `NIMM_XTTS_LANGUE` | fr | langue lue (XTTS en connaît 17) |

## Bon à savoir

- **VS Code souligne `from TTS.api import TTS` en rouge** : c'est un **faux
  positif**. VS Code analyse ce dossier avec le Python du **lecteur** (3.14),
  où `TTS` et `torch` n'existent pas — ils sont dans `.venv` (Python 3.12),
  l'environnement du moteur. Le fichier `pyrightconfig.json` de ce dossier le
  dit à VS Code. Si le message réapparaît : **recharger la fenêtre VS Code**
  (`Ctrl+Maj+P` → « Developer: Reload Window »).
- Le moteur **occupe la carte graphique** (2,2 Go au pic, mesuré) tant qu'il
  est allumé : c'est moins que Kyutai (3,8 Go), donc il laisse plus de place
  aux jeux.
- **Vitesse de calcul** : environ **×3,1 le temps réel** (mesuré : 8,9 min
  d'audio en 171 s, soit 4,08 s par phrase en moyenne). C'est plus lent que
  Kyutai, mais l'audio est **mis en cache** par le lecteur : réécouter un
  passage déjà lu ne redemande rien au moteur.
- **Aucun réglage de hauteur** dans le moteur (comme Kyutai) : la hauteur est
  gérée par le lecteur. Une vitesse existe, mais seulement au niveau bas du
  modèle — on laisse donc le lecteur s'en occuper.
- **Une seule génération à la fois** : les demandes sont mises à la queue leu
  leu (le moteur n'est pas « thread-safe »).
- Les **35 extraits de voix servent tels quels** : ils font 9 à 10 secondes
  alors que XTTS se contente de 6. Aucun nettoyage à faire.
