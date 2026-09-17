# neutts_service — l'appareil de voix NeuTTS

Ce dossier est le **moteur de voix NeuTTS** (Neuphonic) pour NIMM ePub :
un moteur de **clonage**, qui lit n'importe quel texte avec le **timbre d'un
extrait de 3 à 15 secondes**. Il tourne **à côté du lecteur**, dans son propre
environnement Python 3.12, et répond en HTTP sur le **port 8084** — exactement
comme `kyutai_service` (8082) et `xtts_service` (8083).

> **État au 16/09/2026 : le moteur est posé, mais PAS encore branché au
> lecteur.** Le branchement (menus de voix, casting, `START.bat`) est un autre
> chantier. Ce qu'on peut faire dès maintenant : allumer le moteur et vérifier
> qu'il répond.

---

## 🖱️ Les deux fichiers à double-cliquer

| Fichier | Ce qu'il fait |
|---|---|
| `INSTALLER_NEUTTS.bat` | installe l'environnement (une seule fois, quelques minutes : les roues PyTorch et les modèles sont **déjà en cache** sur ce PC) |
| `DEMARRER_NEUTTS.bat` | allume le moteur et le laisse prêt. **Fermer la fenêtre = arrêter le moteur** |

Il n'y a **rien à taper**. Si quelque chose échoue, tout est écrit dans
`journal_installation.txt`, et `_verifier_installation.py` dit en clair ce qui
manque.

---

## 🎙️ Les voix : il faut DEUX choses (c'est la différence avec XTTS)

Pour cloner une voix, NeuTTS a besoin de :

1. **un extrait `.wav`** de 3 à 15 secondes, mono, propre, parole continue ;
2. **le texte EXACT dit dans cet extrait** — sans lui, le moteur invente une
   prononciation et le résultat est inutilisable.

XTTS se contentait du son ; ici il faut les deux. C'est pourquoi l'atelier
NIMM Voix a transcrit ses 79 extraits avec **Whisper large-v3** et écrit un
`references.csv` par dossier (colonnes `fichier;texte;duree;hauteur;source`).

### Où sont les voix, et comment en ajouter une

```
references\
    cml_tts\          60 voix CML-TTS      + references.csv
    voix_libres_dp\   19 voix libres       + references.csv
    (à venir)         30 voix Kokoro, etc.
```

- **Servir les voix de l'atelier**, d'un coup :
  `python _copier_references_depuis_atelier.py --kokoro`
  (il ne fabrique rien, il recopie — et il prévient si un texte manque). Sans
  `--kokoro`, il copie les 79 références préparées (60 CML-TTS + 19 voix
  libres) ; **avec** `--kokoro`, il ajoute les **30 voix Kokoro**, dont
  l'extrait est l'échantillon de contrôle du catalogue de l'atelier ;
- **ajouter une voix à la main** : poser `ma_voix_reference.wav` **et**
  `ma_voix_reference.txt` (le texte dit dans l'extrait) dans `references\` ;
- **sans redémarrer le moteur** : `POST /recharger` (le service rescanne le
  dossier et annonce le nouveau compte).

### Les 30 voix Kokoro

Deux façons, au choix :
- recopier les extraits de contrôle du catalogue de l'atelier
  (`G:\NIMM Voix\catalogue\<voix>\echantillon_controle.wav`) — le texte est
  connu, c'est la phrase 1 de l'atelier ;
- ou **les générer ici même avec Kokoro** et écrire le texte, puisque NIMM ePub
  possède déjà Kokoro et le texte exact qu'il a lu.

### Ce que ça donne (écoute de Laurent, 16/09/2026)

Sur les 30 voix Kokoro dites par NeuTTS : **« les accents Kokoro ont disparu,
les voix ont du caractère, tout est lu en français très compréhensible »**.
C'est le comportement attendu du clonage : l'extrait de référence porte le
**timbre**, la **prononciation** vient du modèle français de NeuTTS. Les voix
Kokoro gardent donc leur timbre **sans** leur accent forcé — et comme les voix
Kokoro restent disponibles dans le lecteur (moteur local), on gagne des
timbres **en plus**, on n'en perd aucun.

---

## 📏 Ce qu'il faut savoir sur ce moteur (mesuré le 16/09/2026)

| Point | Valeur mesurée |
|---|---|
| Fenêtre du moteur | **2048 jetons ≈ 30 s d'audio, référence COMPRISE** → le service découpe le texte à **200 caractères** (au-delà : **troncature silencieuse**) |
| Taille des morceaux | **200 caractères au plus, et moins si l'extrait est long** : la place restante est calculée **par voix** d'après la durée réelle de son extrait (les échantillons Kokoro vont jusqu'à 17,3 s → morceaux plus courts) |
| Durée des références | **12 s** (recadrage de l'atelier) ; à 15 s, il ne reste presque plus de place pour le texte |
| Vitesse | **×0,7 le temps réel** sur la RTX 4060 ; **×3 à ×4 sur processeur** |
| Mémoire vidéo | **3,50 Go** au pic — donc **il ne cohabite pas** avec Kyutai ou XTTS sur la carte (3,8 Go chacun) |
| Chargement | **~10 s** à chaud ; 403 s au tout premier lancement (téléchargement compris) |
| Babil sur phrases courtes | **aucun** : 8 phrases de 4 à 117 caractères, durée proportionnelle au texte (« Manger ? » 1,10 s contre 8,49 s pour XTTS) |
| Stabilité | la **graine** est fixée dans le service (`NIMM_NEUTTS_GRAINE`, 42 par défaut) : mêmes entrées + même graine = **audio identique** |
| Empreinte | chaque audio porte un **filigrane PerTh** invisible (voir `ATTRIBUTION.md`) |

Conséquence pratique à l'usage : la lecture phrase par phrase **avec cache**
fonctionne, mais la **première** écoute d'un chapitre peut faire de petites
pauses (le moteur calcule un peu plus lentement qu'on ne lit).

---

## ⚙️ Réglages (variables d'environnement, valeurs par défaut entre parenthèses)

| Réglage | Rôle |
|---|---|
| `NIMM_NEUTTS_APPAREIL` (`auto`) | `auto` (la carte si elle est libre), `cuda`, ou `cpu` |
| `NIMM_NEUTTS_GRAINE` (`42`) | graine de génération — **c'est la stabilité** : même graine, même audio |
| `NIMM_NEUTTS_PRECODER` (`0`) | `1` = encoder toutes les références au démarrage (démarrage plus long, première phrase instantanée) |
| `NIMM_NEUTTS_PORT` (`8084`) | port d'écoute |
| `NIMM_NEUTTS_BACKBONE` / `NIMM_NEUTTS_CODEC` | modèles (français + codec) |

---

## 🔐 Le jeton Hugging Face (à lire une fois)

Les dépôts de modèles NeuTTS sont **« gated »** : il faut un compte Hugging
Face **et** avoir accepté leurs conditions — **même pour le codec**, pourtant
sous licence Apache-2.0. L'atelier NIMM Voix l'a fait, et le **jeton est
resté en cache** dans `C:\Users\<utilisateur>\.cache\huggingface\token` :
l'installation part donc toute seule ici.

⚠️ **Ne pas révoquer ce jeton tant que le chantier dure** : sans lui,
l'installation et le premier chargement échouent. Le jour où on le révoque
(ce qui est une bonne hygiène), il faut se reconnecter avec un jeton neuf via
`G:\NIMM Voix\SE_CONNECTER_A_HUGGINGFACE.cmd`.

---

## 🧰 Les fichiers de ce dossier

| Fichier | Rôle |
|---|---|
| `servir_neutts.py` | **le service** (port 8084 : `/sante`, `/voix`, `/tts`, `/recharger`) |
| `INSTALLER_NEUTTS.bat` / `DEMARRER_NEUTTS.bat` | installation et démarrage en double-clic |
| `requirements.txt` | les versions exactes validées + **les deux pièges** d'installation |
| `references\` | les extraits **et leur texte** (hors Git : voir `.gitignore`) |
| `_copier_references_depuis_atelier.py` | recopie les extraits préparés par NIMM Voix |
| `_verifier_installation.py` | dit ce qui est en place et ce qui manque (sans charger le moteur) |
| `ATTRIBUTION.md` | licences (NeuTTS, références CML-TTS, filigrane) |
| `journal_installation.txt` | la trace de l'installation (créé à l'installation) |

**Test associé** (ne charge pas le moteur) :
`python test_voix/test_neutts_service.py` — découpage du texte, filet
anti-dérive, rognage du silence, format WAV, lecture des références, et le
contrat avec le lecteur (port, graine, une seule génération à la fois).

