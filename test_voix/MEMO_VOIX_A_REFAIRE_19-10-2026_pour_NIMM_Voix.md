# Mémo NIMM ePub → NIMM Voix — Neuf voix à reprendre (19/10/2026)

**État : à jour — écrit depuis le disque de NIMM ePub, le 19/10/2026.**
**Sujet unique : les neuf voix signalées par Laurent à l'écoute, la cause
mesurée, et la reprise proposée.**
**Où vit ce mémo : `G:\NIMM ePub\test_voix\` (règle 3 de la passerelle : un mémo
reste chez son auteur). Rien n'a été écrit dans NIMM Voix.**

**Mise à jour du 19/10/2026 (soir)** : Laurent a corrigé les neuf textes dans la
fenêtre d'écoute ; ils sont **appliqués** en production (5 lignes changées, 4
déjà justes), et les accents ont été alignés. **L'audio reste à reprendre** :
voir `test_voix\MEMO_SUITE_VOIX_19-10-2026_pour_NIMM_ePub.md`.

---

## 0. En deux lignes

Laurent a signalé neuf voix. Toutes sont des voix **Qwen** (`qwen:`), le moteur
que le lecteur utilise aujourd'hui : les livres ne portent que des `voice_id`
Qwen, et le service Qwen tourne (port 8086). La mesure montre que **cinq des
neuf** ont un défaut de **correspondance entre l'audio de référence et son
texte** : c'est la cause première du babil, du fragment recopié au début et des
premières syllabes mangées. **L'égaliseur n'est donc pas le premier remède** ;
il vient après le recalage des textes.

---

## 1. Ce que Laurent a entendu (mot pour mot)

| Voix | Ce qu'il entend |
|---|---|
| Théodore | « Bug, il doit y avoir un problème de clonage. Il dit n'importe quoi au début de la phrase, puis quelques mots compréhensibles. » |
| Édouard | « Voix très métallique, trop dans les aigus. » |
| Aubin | « Voix très faible et dit “le matt”, on entend le t final. Problème de clonage ? » |
| Maya | « Des sons sur certaines attaques de mots, du souffle dans le micro. Je pense qu'on peut nettoyer ça sur la source, et la re-cloner. » |
| Achille | « Problème au début de phrase, il dit quelque chose d'inaudible, à vérifier pour le re-clonage. » |
| Berthe | « Comme Maya, problème sur les attaques de mots. » |
| Cécile | « Problème au début de phrase, incompréhensible, à re-cloner. » |
| Joséphine | « Problème de volume, très faible et un peu métallique. » |
| Maurice | « Voix très métallique. » |

---

## 2. La découverte principale : le texte de référence ne dit pas toujours ce que dit l'audio

Le clonage Qwen (mode ICL) **aligne l'audio de référence sur le texte fourni**.
Si le texte ne dit pas exactement ce que dit l'audio, le moteur reçoit deux
informations contradictoires : c'est ce qui produit le babil, le fragment
recopié au début et les mots mangés. Nous avons fait relire chaque référence par
Whisper large-v3 et comparé au texte du `references.csv`.

| Voix | Ce que dit l'AUDIO (Whisper) | Ce que dit le CSV | Écart |
|---|---|---|---|
| Théodore (`Homme002`) | « **Des méconnaissables, songea Aroni en traversant la cour jusqu'à l'écurie.** Le château des seigneurs d'Albray… » | commence à « Le château des seigneurs d'Albray… » | **une phrase entière en tête n'est pas dans le texte** |
| Édouard (`Homme004`) | « Quelle différence ? Un bruit… » | « Quelle différence ? Un bruit… » | aucun écart utile (ponctuation) |
| Aubin (`homme_aigu_6877654`) | « … entre le cap de **Morgé**. » | « … entre le cap de **Morgi** » (mot coupé) | **fin tronquée** ; le clone recopie « de Morgi(l) » au début |
| Maya (`Maya_normale`) | de nombreuses différences de personnes, de noms propres et de mots | texte privé approximatif | **plusieurs écarts** (début, pronoms, noms propres) |
| Achille (`cml1840`) | « **madame** de maufrigneuse était à demi pensive… » | « de maufrigneuse était à demi pensive… » | **« madame » manque au début** |
| Berthe (`cml1649`) | identique au CSV | identique | aucun écart |
| Cécile (`cml1869`) | « … de si mauvaise augure. **Madame, je vous supplie de ne pas confondre…** » | s'arrête à « … de si mauvaise augure. » | **la fin de l'audio n'est pas dans le texte** |
| Joséphine (`cml2316`) | identique au CSV | identique | aucun écart |
| Maurice (`cml3182`) | identique au CSV (ponctuation) | identique | aucun écart |

**Ce n'est pas une hypothèse neuve, et c'est justement le problème** : le cas de
`cml1840` (« madame » manquant) avait déjà été identifié le **02/10/2026** dans
l'état du jour de la copie pour Claude, et il n'a **jamais été appliqué en
production** ; `Femme004` (« 4 mots de trop à la fin ») relève du même défaut.
Ces voix sont donc restées en service avec un texte faux. Le diagnostic ci-
dessous ne fait pas que le confirmer : il liste **les cinq cas** et donne le
geste exact pour chacun.

**Preuves à l'appui** (lecture seule, rien n'a été modifié) :

- `_essais/_diag_9_voix_20261019/` : deux phrases de contrôle par voix,
  demandées au moteur Qwen qui tourne (port 8086) ;
- `_essais/_asr_prefixes.log` : Whisper relit les 4 premières secondes ;
  Théodore y est **entièrement** du babil (« le faute, le faras, le miscule,
  l'aff, je suis enceinte »), et Achille, sur la phrase courte, sort
  « F-pargule, par-bar-par-bar-bar-gule… » ;
- `_essais/_asr_references.log` : Whisper relit les neuf références et les
  compare au CSV, ligne par ligne.

**Conséquence pratique** : avant de toucher à l'égaliseur, il faut que le texte
de chaque référence dise **exactement** ce que dit son audio. Tant que ce n'est
pas fait, un égaliseur ne peut que déplacer le défaut.

---

## 3. Diagnostic mesuré, voix par voix

Mesures faites avec les outils de l'atelier (`mesurer_spectre_voix.py`,
`mesurer_timbre_voix.py`, `mesurer_attaques_lot.py`,
`mesurer_bords_extrait.py`, `mesurer_hauteur_voix.py`). Les niveaux et les
couleurs sont ceux de la **référence Qwen** et de la **sortie du moteur** ; la
cible de la garde-robe est **-22,9 dBFS** de niveau de parole (mesure du
19/10/2026) et un centre spectral de **1004 à 1417 Hz** pour les voix Kokoro FR
de même texte.

| Voix | Symptôme | Réf. : niveau / centre / marge | Sortie : niveau / centre / brillance | Bords | Cause probable | Premier geste |
|---|---|---|---|---|---|---|
| Théodore | babil au début | -23,3 dBFS / 1069 Hz / 47 dB | -27,0 dBFS / 1227 Hz / 0,91 % | propres | **texte désaligné** (phrase en trop dans l'audio) | recaler le texte, re-tester |
| Édouard | métallique, aigus | -23,0 / **1553 Hz** / 59 dB | -21,2 / 1045 / 1,56 % | propres | référence **très claire** (au-dessus du haut de la garde-robe) | EQ médian + matage > 3 kHz |
| Aubin | faible + « le matt » | -23,0 / 1082 / 34 dB | -24,8 / 937 / 1,12 % | propres | **texte tronqué** en fin (« Morgi ») | couper la référence à « Naples. » |
| Maya | souffle sur les attaques | -23,2 / 1204 / 35 dB | -23,5 / 1148 / 2,28 % | propres | **souffle de la source** + texte approximatif | DeepFilterNet + texte exact |
| Achille | début inaudible, puis babil | -23,9 / 959 / 38 dB | -23,3 / 955 / 2,76 % | propres | **« madame » manquant** au début du texte | recaler le texte, re-tester |
| Berthe | attaques | -23,9 / 892 / **27 dB** | -24,5 / 1015 / 0,94 % | propres | marge faible (souffle) + attaques sourdes | DeepFilterNet + niveau |
| Cécile | début incompréhensible | -23,0 / **420 Hz** / 53 dB | -22,8 / 731 / 0,92 % | propres | **fin de l'audio absente du texte** | recaler le texte, re-tester |
| Joséphine | faible + métallique | -23,8 / 1041 / **25,8 dB** | -24,1 / 828 / 0,53 % | **sales (10 / 30 ms)** | bords sales + souffle + niveau | 100 ms de silence aux bords, DeepFilterNet, niveau, EQ |
| Maurice | métallique | -23,6 / **1416 Hz** / 39 dB | -24,0 / 1189 / 2,27 % | propres | référence claire + aigus du moteur | EQ médian + matage > 3 kHz |

**Ce que la mesure ne dit pas.** « Métallique » n'a pas de chiffre unique :
Édouard et Maurice sortent au-dessus de la moyenne des aigus, mais Joséphine
sort **sombre** (828 Hz de centre, 0,53 % d'aigus) alors que Laurent l'entend
métallique. La mesure guide le geste, **l'oreille tranche** : il faut écouter
l'A/B après chaque correction, jamais se fier au seul chiffre.

**Deux pièges déjà connus, rappelés** :

1. **Le clone n'est pas déterministe** (température 0,9) : deux tirages ne
   donnent jamais le même fichier. Un seul WAV ne prouve rien ; il faut **deux
   prises par version**.
2. **L'égaliseur ne répare pas le souffle** : monter les aigus le remonte
   aussi. Sur une voix soufflante, c'est **DeepFilterNet d'abord**, l'égaliseur
   ensuite.

---

## 4. Vos outils, ce qu'ils savent faire (et ce qu'ils ne savent pas)

Tous les chemins sont dans `G:\NIMM Voix\`.

| Outil | Ce qu'il fait | Quand l'utiliser ici |
|---|---|---|
| `extracteur_voix\nettoyer_voix.py` (ou `NETTOYER_UNE_VOIX.bat`) | chaîne **Demucs → DeepFilterNet → égalisation médiane (±6 dB) → niveau -23 dBFS, 24 kHz mono**, bords remis à 100 ms ; garde l'AVANT pour l'A/B | souffle (Maya, Berthe, Joséphine) ; musique/effets (pas nos extraits CML/Kyutai, voir `--sans-demucs`) |
| `scripts\recadrer_spectre_voix.py` | recadre la **couleur** vers le profil médian (`sorties\recadrage_spectre_20261017\profil_cible.json`), correction bornée ±6 dB, bords intacts, niveau conservé ; `--meme-nom` pour le paquet | Édouard, Maurice, Joséphine (métallique) |
| `scripts\mesurer_spectre_voix.py` | bandes, centre, pente, marge de bruit | vérifier la couleur avant/après |
| `scripts\mesurer_timbre_voix.py` | niveau de voix, fond, écart (souffle) | vérifier le souffle |
| `scripts\mesurer_attaques_lot.py` | silence de tête, niveau des premières fenêtres, niveau médian | vérifier une attaque faible ou un parasite |
| `scripts\mesurer_entame_fichier.py` | profil des premières secondes, blancs, pics | localiser un « clic » ou un blanc au début |
| `scripts\mesurer_bords_extrait.py` | silence de tête et de queue, verdict BORD SALE | bords d'une référence (Joséphine) |
| `scripts\mesurer_hauteur_voix.py` | F0 médian, durée | vérifier qu'une voix n'a pas été transposée |
| `scripts\tester_qwen3_tts.py` | **re-clone** une référence avec son texte exact (`--reference-texte`), découpe, recolle, mesure le débit | re-tester une voix après correction |
| `COPIER_LE_RECADRAGE_CHEZ_NIMM_EPUB.cmd` | copie un paquet recadré chez nous, avec **copie datée** | livraison finale |
| **`CORRIGER_LES_TEXTES_DES_VOIX.bat`** (chez NIMM ePub, `test_voix\`) | **page dans le navigateur** : écouter chaque référence (bouton « rejouer le début de 2 s »), **réécrire mot pour mot ce qu'on entend**, case Remarque « parasite au début / à la fin » ; écrit `_corrections_oreille.csv`, **ne touche jamais** `references.csv` | **le geste de Laurent** pour les cinq textes désalignés : c'est l'outil écrit exactement pour ce défaut (02/10/2026) |

**Ce qu'aucun outil ne sait faire** : corriger un texte qui ne correspond pas à
l'audio, enlever un parasite que le **moteur** fabrique à l'attaque (le fondu
d'entrée de `tester_qwen3_tts.py` le masque, il ne le supprime pas), ni rendre
un clone déterministe.

---

## 5. L'ordre de travail proposé (et pourquoi)

1. **Recaler les textes** (Théodore, Achille, Cécile, Aubin, Maya) — **sans
   égaliseur**. C'est la cause première ; tant qu'elle est là, tout le reste se
   juge sur un défaut. **Le geste le plus sûr est l'oreille de Laurent** :
   double-clic sur `test_voix\CORRIGER_LES_TEXTES_DES_VOIX.bat`, il écoute le
   début de chaque référence et réécrit ce qu'il entend ; ses corrections
   attendent dans `_corrections_oreille.csv`, **rien n'est appliqué tout seul**.
   La page écrit le **prénom** à côté du nom de fichier (« Théodore
   (Homme002) ») et un bouton **« Les 9 voix signalées »** isole le lot.
   Pour Maya, le texte est **privé** : la correction reste dans le privé.
2. **Re-tester** chaque voix recadrée avec les **deux mêmes phrases** que le
   diagnostic (la phrase de contrôle et « Pardon, dit-il, je ne vous ai pas
   entendu. »), **deux prises**, Whisper sur les 4 premières secondes.
3. **Nettoyer le souffle et les attaques** (Maya, Berthe, Joséphine) :
   DeepFilterNet, bords à 100 ms, niveau -23 dBFS. Pas de Demucs sur un extrait
   déjà propre (voix seule).
4. **Égaliser seulement ce qui reste** (Édouard, Maurice, Joséphine, et
   Théodore si son niveau ne revient pas après le recalage) : profil médian,
   puis **matage -3 dB au-dessus de 3 kHz** si le métallique persiste (version B
   de Gus, 19/10/2026).
5. **Livrer** les WAV + les textes exacts ; nous installons avec copie datée,
   nous redémarrons Qwen (les empreintes sont en mémoire) et nous vidons le
   cache audio du lecteur.

> **Pourquoi ne pas égaliser d'abord ?** Parce qu'un défaut de texte produit un
> babil qui n'a rien à voir avec la couleur. On risquerait d'abîmer une voix
> pour un défaut qui n'est pas le sien.

---

## 6. Ce qu'il y a à faire, voix par voix

### Théodore — `Homme002_reference.wav` (19,97 s)

- **Preuve** : Whisper entend au début « Des méconnaissables, songea Aroni en
  traversant la cour jusqu'à l'écurie. », phrase absente du CSV. Le clone part
  donc en babil.
- **Geste conseillé** : **couper la référence au début de « Le château… »**
  (on perd la phrase parasite, la référence reste ≈ 16 s, largement assez pour
  Qwen). Deuxième option : **ajouter la phrase au texte**, mot pour mot, si vous
  préférez garder l'audio entier.
- **Vérifier après** : bords propres (100 ms), puis deux prises ; les 4
  premières secondes doivent dire « Le château des seigneurs d'Albray… ».
- **Niveau** : la sortie était à -27,0 dBFS (4 dB sous la garde-robe). Après le
  recalage, re-mesurer ; si c'est toujours bas, +2 à +3 dB sur la référence, pas
  plus.

### Édouard — `Homme004_reference.wav` (20,18 s)

- **Texte** : conforme (seule la ponctuation diffère).
- **Preuve** : centre spectral **1553 Hz**, au-dessus du haut de la garde-robe
  (1417 Hz) ; la sortie est à 1,56 % d'aigus.
- **Geste** : `recadrer_spectre_voix.py` vers le profil médian. Si le métallique
  reste à l'oreille, **matage -3 dB au-dessus de 3 kHz** (version B de Gus).
- **Ne pas** baisser le niveau : la sortie est déjà à -21,2 dBFS, au-dessus de
  la cible.

### Aubin — `homme_aigu_6877654_reference.wav` (14,59 s)

- **Preuve** : le CSV s'arrête à « … le cap de **Morgi** » (mot coupé) ; Whisper
  entend un mot complet, « … le cap de **Morgé**. ». Le clone **recopie « de
  Morgi(l) » au début** de chaque phrase : c'est le « le matt » entendu par
  Laurent. **Sa propre remarque du 03/10 dans `_corrections_oreille.csv` le
  disait déjà** : « finit sur un mot coupé. - cap de Morgion ».
- **Geste conseillé** : **couper la référence à la fin de « … Trieste et
  Naples. »** (première phrase complète) et garder **exactement** ce texte. Une
  référence qui s'arrête sur une phrase complète ne peut pas recracher de
  fragment. Si vous préférez garder la fin, il faut une source qui va jusqu'au
  bout d'une phrase, pas un mot coupé.
- **À trancher aussi** : « le trois-mâts le Pharaon » (texte littéraire) contre
  ce que dit réellement le lecteur. Le moteur aligne des **sons** : gardez la
  forme qui correspond à l'audio, pas la plus jolie.
- **Niveau** : sortie à -24,8 dBFS (1,9 dB sous la cible). Re-mesurer après le
  recalage ; si besoin, +2 dB sur la référence.

### Maya — `Maya_normale_reference.wav` (20,18 s, **privée**)

- **Preuve** : le texte privé et l'audio diffèrent sur plusieurs points
  (personnes, noms propres, un « go goût » conservé). Ce n'est pas un texte
  exact, donc le clonage est mal aligné ; les attaques soufflées, elles, sont
  dans la source.
- **Geste** : (1) **nettoyer la source** avec DeepFilterNet, **sans Demucs** si
  l'enregistrement est de la voix seule ; (2) garder **100 ms de silence** aux
  deux bords ; (3) **réécrire le texte exact** de ce qui est dit (y compris un
  éventuel bredouillis, ou couper le passage bredouillé) ; (4) re-cloner et
  tester deux prises.
- **Droits** : voix d'une personne réelle, texte d'un livre du commerce —
  **usage privé**, rien ne part sur le dépôt.

### Achille — `cml1840_reference.wav` (9,95 s)

- **Preuve** : Whisper entend « **madame** de maufrigneuse était à demi
  pensive… » ; le CSV commence à « de maufrigneuse… ». Sur la phrase courte, le
  clone part en babil (« F-pargule… »).
- **Geste** : ajouter « **madame** » au début du texte, ou couper la référence
  juste avant « de maufrigneuse » (mais on perd le début de la phrase). Le plus
  simple et le plus sûr : **mettre le texte exact**, « madame de maufrigneuse
  était à demi pensive… ».
- **Vérifier après** : surtout la **phrase courte** (« Pardon, dit-il… »), c'est
  là que le babil apparaissait.

### Berthe — `cml1649_reference.wav` (10,27 s)

- **Texte** : conforme.
- **Preuve** : marge voix/fond **27 dB** (le seuil d'alerte est 25 dB ; le
  souffle commence à s'entendre) et attaques faibles.
- **Geste** : DeepFilterNet, bords à 100 ms, niveau -23 dBFS. Un léger
  passe-haut vers 80 Hz peut retirer le grondement sans toucher à la voix.
- **À garder** : l'accent allemand, c'est voulu.

### Cécile — `cml1869_reference.wav` (10,14 s)

- **Preuve** : Whisper entend, après « … de si mauvaise augure. », la suite
  « Madame, je vous supplie de ne pas confondre… », absente du CSV.
- **Geste conseillé** : **couper la référence à la fin de « … de si mauvaise
  augure. »** (la citation est complète) et garder ce texte. Deuxième option :
  ajouter la fin exacte au texte, si vous voulez garder l'audio entier.
- **Vérifier après** : la première seconde, c'est là que Laurent n'entendait
  rien.

### Joséphine — `cml2316_reference.wav` (9,82 s)

- **Preuve** : **bords sales** (10 ms de tête, 30 ms de queue), marge **25,8 dB**
  (souffle), sortie faible et « métallique » à l'oreille alors que la mesure la
  trouve sombre.
- **Geste** : **100 ms de silence aux deux bords**, DeepFilterNet, niveau
  -23 dBFS, puis recadrage médian. Si le métallique persiste, matage -3 dB
  au-dessus de 3 kHz. Si malgré tout il reste, **essayer un autre extrait** :
  une voix peut être propre en moyenne et avoir un défaut local.
- **Attention** : c'est celle qui cumule le plus de défauts ; c'est aussi celle
  où il faudra **deux prises** avant de conclure.

### Maurice — `cml3182_reference.wav` (12,74 s)

- **Texte** : conforme.
- **Preuve** : centre **1416 Hz** (haut de la garde-robe), 3,0 % d'énergie
  au-dessus de 8 kHz, sortie à 2,27 % d'aigus. La note du 14/09 disait déjà
  « bruits de bouche, à surveiller ».
- **Geste** : recadrage médian, puis **matage -3 dB au-dessus de 3 kHz** si le
  métallique persiste. DeepFilterNet peut aider sur les bruits de bouche ; à
  vérifier à l'oreille, car il peut aussi adoucir la voix.

---

## 7. Le protocole de contrôle (pour ne pas se fier à un seul tirage)

1. **Deux phrases**, toujours les mêmes :
   - « Le 24 février 1815, la vigie de Notre-Dame de la Garde signala le
     trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples. »
   - « Pardon, dit-il, je ne vous ai pas entendu. »
2. **Deux prises par voix** (température 0,9 : le clone n'est pas déterministe).
3. **Whisper large-v3** sur les **4 premières secondes** : les mots attendus
   doivent être là, sans babil. C'est le test qui a démasqué Théodore et Achille.
4. **Mesures** : silence de tête, niveau des 10 premières fenêtres, niveau médian,
   centre spectral, marge de bruit, bords.
5. Une voix n'est déclarée **OK** que si **les deux prises** passent. Une seule
   prise juste ne prouve rien (leçon du 29/09 sur Aubin).

Les scripts de diagnostic sont dans `G:\NIMM ePub\_essais\` (lecture seule) :
`_diag_9_voix_20261019.py` (demande les phrases au moteur),
`_asr_prefixes_20261019.py` (Whisper sur les 4 premières secondes),
`_asr_references_20261019.py` (Whisper sur les références, comparé au CSV).

---

## 8. Ce que NIMM ePub fera à la réception

1. **Copie datée** de `qwen_tts_service\voix\` et des deux CSV
   (`references.csv`, `references_privees.csv`) avant toute écriture.
2. Remplacement **des seuls WAV et des seules lignes concernés** ; les
   identifiants (`Homme002`, `cml1840`, `Maya_normale`…) et les noms affichés ne
   changent pas — `modules\tts.py` n'est pas touché.
3. **Redémarrage du service Qwen** (les empreintes de voix sont gardées en
   mémoire ; sans redémarrage, il utiliserait les anciennes).
4. **Purge du cache audio du lecteur** (le cache ne connaît pas le contenu de la
   référence : sans purge, il rejouerait l'ancien son).
5. **Re-test** avec le protocole du point 7, et compte rendu à Laurent.
6. Si une voix change de note ou d'accent, mise à jour de
   `data\annotations_voix.json` — pas avant l'écoute de Laurent.

---

## 9. Ce qu'il nous faut de vous

- **En priorité** : les cinq références recalées (Théodore, Achille, Cécile,
  Aubin, Maya), avec leur **texte exact**.
- **Ensuite** : les quatre nettoyées/égalisées (Édouard, Berthe, Joséphine,
  Maurice), avec l'A/B et le rapport de mesures.
- Dites-nous **quelle source** vous avez utilisée si vous ré-extrayez (pour que
  la fiche de la voix reste vraie).
- Si vous préférez, **nous pouvons faire le recalage des textes ici** (les cinq
  premiers cas) et vous ne faites que l'audio : dites lequel des deux vous
  arrange. Le texte est notre donnée, l'audio est la vôtre — mais le clone a
  besoin des deux au même endroit.

---

## 10. Fichiers et preuves (tout est local, rien n'est versionné)

| Objet | Chemin |
|---|---|
| Les références Qwen | `G:\NIMM ePub\qwen_tts_service\voix\` |
| Les textes publics | `...\voix\references.csv` |
| Le texte privé (Maya) | `...\voix\references_privees.csv` (hors Git) |
| Le diagnostic audio | `G:\NIMM ePub\_essais\_diag_9_voix_20261019\` (18 WAV) |
| Le journal du diagnostic | `...\_essais\_diag_9_voix.log` |
| Whisper sur les clones | `...\_essais\_asr_prefixes.log` |
| Whisper sur les références | `...\_essais\_asr_references.log` |
| Le profil d'égalisation | `G:\NIMM Voix\sorties\recadrage_spectre_20261017\profil_cible.json` |
| La recette des 4 voix | `G:\NIMM Voix\sorties\egalisation_4_voix_20261019\LISEZ-MOI.txt` |
| Le matage de Gus | même dossier, section « SUITE DU MÊME JOUR — GUS TROP AIGU » |

**Ce qui n'a pas été touché par ce diagnostic** : aucun WAV de référence, aucun
catalogue. Les **textes** ont été corrigés par Laurent puis **appliqués** le
19/10/2026 (voir `MEMO_SUITE_VOIX_19-10-2026_pour_NIMM_ePub.md`) ; l'**audio**
reste à reprendre. Ce mémo-ci est le diagnostic, pas la modification.

---

*Écrit le 19/10/2026 depuis le disque de NIMM ePub. Si un chiffre de ce mémo
contredit votre disque, c'est votre disque qui a raison : dites-le, on corrige.*




