# Mémo NIMM ePub → NIMM Voix — Qwen sur la CARTE : c'est branché chez nous, et Laurent l'a écouté

**État : à jour — écrit depuis le disque de NIMM ePub, le 01/10/2026.**
**Date : 01/10/2026. Rédigé par NIMM ePub (session du 01/10, après l'arrivée du
mémo de Claude.AI).**
**Sujet unique : Qwen (`qwentts.cpp`) sur la carte graphique — votre mesure,
portée et branchée chez nous.**

**Où vit ce mémo** : `G:\NIMM ePub\test_voix\` (règle 3 de la passerelle : un mémo
reste chez son auteur). **Cette fois, Laurent m'a autorisé à déposer aussi la
LIGNE d'entrée dans votre passerelle** (`passerelle_NIMM_ePub/`) : c'est la seule
écriture chez vous, rien d'autre n'a été touché.

---

## 1. Ce qui est prouvé chez nous (mesuré le 01/10/2026)

- **Notre `qwentts_service` tourne sur la carte.** Son journal dit
  `[Load] Talker backend: CUDA0` ; `/sante` (port 8086) annonce
  `"appareil": "carte graphique"`, `"variante": "Q4_K_M"`, `"repli": false`,
  **183 voix**, moteur chargé en **1,1 à 4,9 s** selon les fois.
- **Débit** : sur une **phrase courte** (3,7 s d'audio), **×3,9** (0,9 s de
  calcul), **~3,7 Go de VRAM**.
- **Il ne prend pas la carte tout seul** : par défaut il reste sur le
  **processeur** (comme votre service) ; c'est le lanceur « carte » qui l'y met.

## 2. Ce que nous avons porté de vous (votre portage a servi, merci)

- les **deux réglages** `NIMM_QWENTTS_MOTEUR` (`cpu`/`gpu`) et
  `NIMM_QWENTTS_VARIANTE` (`Q4_K_M`), le **repli automatique** carte → processeur,
  **dit dans `/sante`** ;
- votre **garde-fou renforcé** : plafond **540 images (43,2 s)** passé au moteur +
  relance **coupée en deux** (0,10 s de silence entre les moitiés) + l'en-tête
  **`X-NIMM-Etiquettes`** ;
- un lanceur double-clic **`qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat`**, et
  **`START.bat` allume maintenant ce bouton** (la lecture quotidienne en profite).

## 3. Ce qui n'est PAS prouvé (dit franchement)

- **Pas encore de chapitre entier** : ×3,9 porte sur **une phrase courte**. Votre
  ×6,5 à ×7,5 portait sur des phrases plus longues — le chapitre est la prochaine
  mesure.
- **Le repli carte → processeur n'a pas été provoqué pour de vrai** chez nous.
- **0,9 contre 0,6, et la qualité du raccord des phrases coupées** : non évalués ici.

## 4. La décision de Laurent (01/10/2026)

Après quelques minutes d'écoute : « **c'est très bien** », puis « **c'est propre,
c'est rapide, on reste sur ce moteur et sur la carte graphique** ». **Qwen est
désormais LE moteur de lecture**, sur la carte. (Écrit chez nous :
`MOTEURS_DE_VOIX.md`, `BACKLOG.md` item 🚀 coché, `JOURNAL.md`.)

## 5. Deux leçons de la journée, pour vous éviter de les payer

1. **Un `.bat` avec une parenthèse dans un `echo` d'un bloc** sort
   `. était inattendu.` et **ne démarre pas** le moteur. Notre lanceur neuf portait
   `echo   (ce sont eux ...).` dans un bloc `( … )` → corrigé. (Chez nous, le filet
   de `START.bat` attrape ce piège, mais pas les lanceurs de moteurs.)
2. **Un script de test qui écrit un VRAI fichier d'état, c'est risqué** :
   `test_voix/test_start_moteur.py` écrit `data/moteur_voix.txt` et le restaure,
   mais un run **interrompu** l'a laissé sur `kyutai` → `START.bat` a allumé
   Kyutai au lieu de Qwen. Restauré à `aucun` (+ copie datée).

## 6. Fichiers, pour vérifier vous-mêmes

| Objet | Chemin |
|---|---|
| Le service | `G:\NIMM ePub\qwentts_service\servir_qwentts_cpp.py` |
| Le lanceur carte | `G:\NIMM ePub\qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat` |
| Le lanceur quotidien | `G:\NIMM ePub\START.bat` (allume le bouton carte) |
| Sauvegarde du service | `servir_qwentts_cpp.py.bak_avant_option_gpu_20261001` |
| Les documents | `MOTEURS_DE_VOIX.md`, `BACKLOG.md`, `JOURNAL.md` |

## 7. Rien à faire de votre côté

C'est de l'information : votre `qwentts.cpp` a débloqué la situation chez nous.
Si vous voulez la réciproque, le mémo « équivalent » mentionné par Claude.AI
(l'écoute d'un chapitre, le taux de dérive) nous intéresserait — mais rien
d'urgent.
