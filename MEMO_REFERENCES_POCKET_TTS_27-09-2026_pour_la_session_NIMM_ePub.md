# Mémo pour la session NIMM ePub — références Pocket TTS recoupées, et la question des pauses entre moteurs

_Écrit par la session NIMM Voix le 27/09/2026._

Ce mémo ne demande **rien** : il transmet un état des lieux, une procédure
vérifiée et les pièges déjà payés. **Rien n'a été modifié chez toi** — NIMM ePub
n'a pas été ouvert pendant cette session.

---

## 1) Ce qui s'est passé, en trois lignes

Laurent entendait Pocket TTS « **manger les débuts de phrases** » (parfois) et
« **avaler des syllabes** » sur les petites répliques. La mesure (NIMM Voix,
27/09/2026) a montré que **le défaut ne venait pas du moteur** : nos référence
audio étaient **coupées en plein mot** à leurs deux bords. Sur nos **28
références en service**, **23 avaient au moins un bord sale** et **20 une tête à
0 ms** — alors que nos voix Kokoro, qui ne font aucun parasite, gardent 20 à
60 ms de silence en tête.

**Cause, chez nous** : `rogner_bords()` (dans
`outils/pocket_tts/_cloner_voix_depuis_fichier.py`) coupait **au ras du premier
son**, sans marge.

**Verdict de Laurent sur le test A/B** (même phrase, ancienne référence puis
référence recoupée) : « Sur la prosodie, c'est presque pareil, par contre, les
voix "après" sont un peu plus "claires", dans la qualité du son, elles sont un
peu mieux. Ça n'est pas aussi flagrant que sur Qwen, mais une légère amélioration
tout de même. **Aucun mot n'est "mangé" en début de phrase.** Je pense que les
petites répliques devraient être ok. »

## 2) Ce qu'il y a à faire chez toi (procédure)

Le nouveau jeu de références est prêt, **28 fichiers, aux noms d'origine** :

```
G:\NIMM Voix\sorties\pocket_tts_bords_propres_20260927\
    C_references_finales\        28 x <voix>_reference.wav  <-- LES FICHIERS DE VOIX
    INDEX_REFERENCES.txt         le détail voix par voix (avant / après / gardée)
```

1. **Copie datée d'abord** (règle de l'atelier) : fais une copie de tes fichiers
   actuels de `pocket_tts_service\voix` avant de remplacer, par exemple
   `voix.bak_avant_bords_propres_20260927\`.
2. **Remplace par le même nom** : les 28 fichiers portent exactement les noms
   d'origine (`Femme001_reference.wav`, `homme_grave_5649798_reference.wav`,
   `JEAN_EDGAR_reference.wav`…), donc c'est un remplacement direct, **rien à
   renommer** et **rien à changer** dans `POCKET_VOICES` ni dans `tts.py`.
3. **Refais le casting du chapitre de test** — c'est la demande de Laurent :
   « il est encore à l'ancienne coupe ». C'est ce chapitre qui doit être
   réécouté avec les références recoupées.

**Contenu du jeu, mesuré** : sur les **28 voix**, **24 références ont été
CHANGÉES** (recoupées, bords propres) et **4 sont IDENTIQUES à avant** (leurs
références étaient déjà propres : la recoupe ne les améliorait pas, on ne change
pas une voix qui va bien — c'est mesuré dans `INDEX_REFERENCES.txt`).
**3 voix gardent un bord à 40 ms**, ce qui est la zone de nos voix Kokoro (sans
**aucun défaut connu**), et **les 28 ont maintenant au moins un bord propre** :
la dernière (`homme normal65465409`), dont la source n'a **aucun silence** dans
une fenêtre de 20 s, a été **recoupée court — 10,2 s au lieu de 20 s** — avec une
recherche de silence élargie à ±12 s (bords 120 / 110 ms, vérifiés). Les durées
changent un peu (par exemple
15,1 s → 21,2 s pour `homme_normal_65465987312`) : **la référence recoupée doit
être réévaluée à l'oreille**, c'est pour ça que le chapitre de test est refait.

## 3) Comment les références ont été fabriquées (à refaire à l'identique si besoin)

- Sources : `G:\NIMM ePub\Extraits de voix\Découpage OK` (tes 30 MP3), **lues
  seulement**, rien modifié.
- Outil : `G:\NIMM Voix\outils\neutts_tts\_preparer_references.py` avec
  `--duree 20 --bords-propres --bords-propres-max 22 --portee-bords 6`
  (les bornes sont posées au **milieu d'un vrai silence** : ≥ 80 ms sous −45 dB,
  cherché jusqu'à 6 s autour de la borne).
- Trois passes ont été mesurées : ±0,6 s → **16/30** bords propres ; ±2 s →
  **23/30** ; ±6 s → **24/30**. C'est la dernière qui sert.
- Sortie : `sorties\pocket_tts_bords_propres_20260927\references_v3\`.

## 4) Ce qui a été corrigé chez nous (à savoir si tu clones une voix)

1. **Le rogneur garde maintenant 100 ms de silence à chaque bord**
   (`MARGE_SILENCE = 0.10` dans `_cloner_voix_depuis_fichier.py`). Avant, il
   coupait au ras du premier son. **Si tu clones avec ce script, prends la
   version à jour.**
2. **Attention, piège important** : `_cloner_dossier.py` **re-rogne** chaque
   référence au moment du clonage. Appliqué à une référence déjà recoupée, il
   ramenait la tête à 0 ms et **annulait** le nettoyage. Pour le test A/B, les
   références ont donc été données au moteur **telles quelles**, sans rognage
   (outil `outils\pocket_tts\_comparer_bords_propres.py`).
3. Un **outil de vérification** existe maintenant :
   `G:\NIMM Voix\_atelier\_verifier_rogneur_bords.py` — il mesure les bords
   avant/après passage du rogneur et dit si la marge a été conservée. Lancé sur
   les 30 références recoupées : **30/30 OK**.

## 5) La question des pauses quand plusieurs moteurs se mélangent (piste de Laurent)

Ses mots (27/09/2026) : « Je pense qu'un des soucis avec Pocket, c'est quand
2 moteurs se mélangent. Les pauses pour les sauts de ligne et les points se
mélangent. Si Pocket rend la réplique à un moteur Kyutai, il doit y avoir un
souci avec les règles de pauses pour les points, sauts de ligne,
ponctuation… »

Ce qu'on sait de notre côté, et qui peut aider ta session :

- **Chaque moteur a SA règle de pause** et **aucun des deux n'a de réglage de
  débit ou de volume** : côté Kyutai 1.6B, la seule balise utilisable est
  `<break time="1.5s"/>` dans le texte (mesuré le 12/09/2026), et le débit
  interne se règle par `padding_bonus` ; côté Pocket TTS, il n'y a **aucun**
  réglage de pause (la recette de l'atelier se contente de nettoyer le texte et
  de passer `--max-tokens 200`).
- Nos lots montrent que les pauses de fin de phrase, côté Pocket TTS, font
  **0,8 à 1,6 s** et sont **rattrapées au montage** par
  `outils\pocket_tts\_monter_propre.py` (silence de tête 0,2 s, fondus).
- Donc le point à regarder **chez toi**, c'est **l'orchestration** : qui insère
  les silences entre deux répliques, avec quelles valeurs, et **la règle
  dépend-elle du moteur** ? Si un même chapitre est lu par plusieurs moteurs,
  deux règles différentes se retrouvent côte à côte : c'est très probablement
  ce que Laurent entend. Nous n'avons **rien vérifié chez toi** sur ce point —
  c'est une piste à ouvrir, pas un diagnostic.

## 6) Licences (rappel de la règle de l'atelier)

- **17 voix** : extraits du **DOMAINE PUBLIC** préparés par Laurent (Audacity).
- **JEAN EDGAR** : personne réelle → écoute et usage privé libres, **partage**
  seulement avec son accord.
- **10 voix** : extraits de **livres audio du commerce**, lus par des
  **comédiens (personnes réelles)** → **USAGE PRIVÉ**, ne pas diffuser
  (catalogue détaillé dans `sorties\pocket_tts_retenues_20260923\ORIGINE_ET_LICENCE.txt`).
- Moteur **Pocket TTS** : poids **CC BY 4.0** (citer Kyutai si l'outil est
  partagé) ; l'audio produit suit les droits de la voix, pas ceux du moteur.

## 7) Pièges déjà payés (pour ne pas les repayer)

- Couper la référence **au ras du premier son** = défaut « début de phrase
  mangé » (mesuré et corrigé ici le 27/09/2026).
- À 20 s, l'option de recalage des bords était **refusée en silence** (garde
  5-15 s écrite pour un autre outil) : d'où l'option `--bords-propres-max`.
- En parole continue, l'outil ne trouvait aucun silence en ±0,6 s : d'où
  `--portee-bords`.
- Une référence rognée à 0 ms **ne peut pas être réparée par un rognage** (un
  rognage ne crée pas de silence) : il faut repartir de l'extrait d'origine.

## 8) Mesures du moteur (NIMM Voix, 27/09/2026)

Premier chronométrage de Pocket TTS chez nous (i5-12400F, 12 processeurs
logiques, 32 Go), **tout à la ligne de commande** — utile pour ton service, qui
est justement le bon outil :

- **Débit** : ×0,44 (60 caractères), ×0,62 (150), ×0,69 (300), **×0,93** (600
  caractères) ; **hors chargement du modèle : ×1,2 à ×1,5** → le
  « ~6× le temps réel » annoncé par l'éditeur **n'est pas reproduit** sur cette
  machine.
- **Le chargement du modèle coûte 9,2 s et il est payé à CHAQUE appel** de la
  ligne de commande : c'est lui qu'on voit dans le « premier son à ~10 s »,
  **constant quelle que soit la phrase**. Le moteur écrit ensuite son WAV **au
  fur et à mesure** (3 à 12 mises à jour du fichier). Autrement dit :
  **`pocket-tts serve` (modèle chaud) est la seule façon de faire du « au fil de
  l'eau »**, la ligne de commande ne le permet pas.
- **Les pauses qu'il place lui-même** (5 phrases, aucune consigne) : **0,19 à
  0,59 s entre les phrases (médiane 0,44 s)**, et **0,20 s** en fin de fichier.
- **`--max-tokens` change la lecture** (même texte de 600 caractères) :
  50 → 5 morceaux et 38,8 s d'audio ; 200 → 2 morceaux et 29,5 s ;
  **250 → 1 morceau et 14,4 s : plus de la moitié du texte n'est pas lue, sans
  message d'erreur** → **ne jamais dépasser 200**.
- **Le rythme de lecture dépend du DÉCOUPAGE** (mesuré le 27/09/2026 sur les
  fichiers du lot, avec `_mesurer_silences.py`) : à **50 ou 100 tokens** le
  moteur lit à **15,4 caractères/s** (le rythme d'une **lecture naturelle**) et
  place 16 à 18 silences ; à **200** il lit à **20,4 caractères/s** — il
  **accélère** — avec 11 silences. **Verdict de Laurent à l'oreille : « c'est le
  passage avec les phrases découpées qui est la plus propre ».** Autrement dit :
  le réglage de découpage de ton service n'est **pas neutre**, il change **la
  vitesse ET la propreté** de la lecture. À 100 tokens, un détail : le fichier
  peut **commencer par 0,90 s de silence** (le montage le retire chez nous).
- **Le moteur découpe le texte LUI-MÊME** (mesuré le 27/09/2026, sans générer un
  son) : il **empile des phrases entières** jusqu'au quota et, à **50 tokens**,
  il **coupe aussi DANS les phrases, aux virgules** (le passage de Monte-Cristo
  part en **18 morceaux**). **Une phrase sans aucune ponctuation ne peut pas être
  coupée** (392 caractères = **113 tokens, un seul morceau**) et le moteur
  **avertit lui-même** : « *generation may skip words* » → **le remède est dans
  le TEXTE** : avec les virgules ajoutées à la main, la même phrase part en
  **3 morceaux** et se lit à **16,5 car./s** au lieu de **26,0**. Le **contexte
  glissant** reste la solution de secours quand aucune ponctuation n'est
  possible.
- **ATTENTION : les LONGS textes sont défectueux, quel que soit le découpage**
  (verdict de Laurent du 27/09/2026 sur un passage de 1 993 caractères) :
  « des coupures pendant la lecture, des mots avalés » à **200 tokens**,
  « la lecture saute à 1'10 » à **100**, « bruits étranges et texte qui saute
  dans le début » à **50**. En revanche un texte de **400 caractères** (3
  morceaux) est « **très bien** », et une phrase géante **sans virgule** est
  « **pas utilisable** » (prosodie) tandis que la même **avec virgules** est
  « très bien ». **Règle pour ton service** : n'envoyer que des textes **courts**
  (votre recette « une phrase à la fois » est la bonne), et **couper vous-mêmes**
  les phrases qui n'ont aucune virgule.
- **Les « coupures » entendues = les pauses du moteur ; le MONTAGE les efface**
  (mesuré le 27/09/2026) : ramener toutes les pauses à **0,40 s** (tête à
  **0,20 s**) a supprimé **10 / 13 / 17** pauses sur trois textes de 275, 608 et
  1031 caractères (durées 22,60 → **20,00 s**, 40,92 → **37,81 s**, 66,68 →
  **60,11 s**), et il ne reste **aucune pause ≥ 0,45 s** (contre 10 / 14 / 17
  avant). **Votre chaîne de montage fait déjà ça** — c'est ce qui explique que le
  lecteur sonne mieux que le moteur brut.
- **Pocket TTS peut se FIGER en pleine génération** (vu le 27/09/2026 : une
  génération de 17 morceaux, **0 % de CPU**, en-tête WAV jamais finalisée, tout
  un test bloqué). **Relancée à l'identique, la génération a abouti** → défaut
  **intermittent**, cause **inconnue**. **Conséquence pour ton service** :
  prévois un **délai de garde** sur la génération, sinon une requête figée peut
  bloquer le service.
- **Nombre de cœurs** : 1, 3, 6 ou 12 fils → **même temps** (19,2 à 19,6 s) ;
  inutile de régler ça.

Détail complet : `G:\NIMM Voix\sorties\pocket_tts_mesures_20260927\mesures.txt`
(+ `journal.txt`, et 5 fichiers à écouter dans `A_ECOUTER\`).

---

_Traces côté NIMM Voix_ : `sorties\pocket_tts_bords_propres_20260927\`
(`A_ECOUTER\`, `C_references_finales\`, `INDEX_REFERENCES.txt`,
`FICHE_LOT.txt`, `journal_generation.txt`, `VERDICT_LAURENT_20260927.txt`),
`BACKLOG.md` (item « Mesurer et optimiser Pocket TTS »), `ETAT.md`,
`JOURNAL.md` (session 68).
