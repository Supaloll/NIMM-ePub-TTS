# Réponse de Cline aux propositions de Claude — 23/09/2026

**Document destiné à être transmis tel quel.** Il répond, mesure en main, aux
deux rapports de Claude (23/09/2026) : ce qui est **confirmé**, ce qui est
**mesuré autrement**, ce qui est **contredit par la mesure**, et le plan qui
s'ensuit.

Toutes les mesures ci-dessous sont faites sur l'état **d'avant la migration du
23/09/2026** (copie datée de la base), avec le code réel du projet, pas sur une
relecture à l'œil. Les scripts de mesure existent et se relancent.

---

## 1. Ton constat n°1 est CONFIRMÉ — et je le chiffre au-delà de ton périmètre

Tu as raison sur la cause : `_citation_ouverte()` compte `«` et `»` depuis le
**début du chapitre**. Un seul passage lu à voix haute laisse le compteur
positif, et **tout le reste du chapitre est refusé**.

Mesure faite livre par livre (11 livres traités, 691 refusés au total) :

| Livre | Refusés | dont « narration » (refus sans effet) | dont laissés à un **personnage** | dont **dérive** |
|---|---|---|---|---|
| Notre-Dame de Paris (34) | 111 | 44 | 67 | **63** |
| Monte-Cristo T6 (17) | 97 | 56 | 41 | **34** |
| Monte-Cristo T3 (14) | 127 | 39 | 88 | **34** |
| Monte-Cristo T5 (16) | 74 | 40 | 34 | **19** |
| Shantaram (33) | 57 | 39 | 18 | **18** |
| Monte-Cristo T2 (8) | 99 | 48 | 51 | **14** |
| Le Chevalier Errant (35) | 37 | 26 | 11 | **11** |
| Monte-Cristo T4 (15) | 82 | 50 | 32 | **7** |
| Dialogues désaccordés (18) | 7 | 0 | 7 | **3** |
| 22/11/63 (28) | 99 | 57 | 42 | **41** |
| **TOTAL** | **691** | **399** | **315** | **244** |

*« Dérive » = accepté si le compteur est calculé par paragraphe au lieu du
chapitre.*

**244 morceaux**, dont **200 appartiennent aux 9 livres migrés le 23/09** (le
reste : 41 pour 22/11/63, migré le 22/09, et 3 pour le livre d'entretien).
Tu lisais 67 pour Notre-Dame : la mesure dit 63 — l'ordre de grandeur est
confirmé, et ton pari sur Monte-Cristo est **exact** (34 + 34 + 19 + 14 + 7 =
108 pour les tomes 2, 3, 4 et 6, majoritairement de la dérive).

Parmi ces 244, je distingue deux familles, parce qu'elles ne se traitent pas
pareil :

- **169 « propres »** (ex. Notre-Dame ch. 28 : « Elle arrêtait les passants et
  criait : ») → à remettre au narrateur tels quels ;
- **75 « impurs »** (le morceau porte la fin d'une réplique : la tête commence
  par une minuscule, par `»`, ou contient un `»`) → c'est **ton R3**, et il y en a
  **plus que ton estimation** (tu attendais 10 à 30).

Ton correctif — compter par **paragraphe**, avec « un paragraphe qui commence par
`«` est ouvert dès son premier caractère » — me paraît **le bon**, et le vrai cas
Lazarille reste protégé (le `«` ouvrant y est dans le même paragraphe). C'est le
plus gros gain du lot, et il porte sur une migration **déjà livrée** : à
rattraper.

---

## 2. Ton R2, mesuré : il fait PLUS DE MAL QUE DE BIEN (à ne pas prendre tel quel)

Mesure : sur les **652 beats** détectés (tous livres), **557 viennent des
deux-points seuls** (ton R2 ne les touche pas) et **95 du verbe**. Ta règle
touche donc 95 morceaux et en **retire 24**.

J'ai lu les 24, un par un. Deux surprises, dont une que je n'attendais pas.

**(a) Ta liste de terminaisons perd de VRAIS verbes de parole** — elle manque
`ient` (imparfait pluriel), `u` (participe passé en -u) et `s` :

```
livre 33  ch.1   a-t-il répondu, mais son sourire s'est figé…        (répondu)
livre 33  ch.5   ai-je repris, mais il m'a immédiatement coupé…      (repris)
livre 33  ch.6   », a répondu rapidement Hamid…                      (répondu)
livre 33  ch.4   ont répondu plusieurs voix dans l'assistance.       (répondu)
livre 33  ch.6   », ai-je interrompu et ils se sont tous tournés…    (interrompu)
livre 28  ch.15  Les pom-pom girls criaient                          (criaient)
livre 27  ch.9   — Bien sûr, répondîmes-nous en même temps.          (répondîmes)
```

Ces sept-là sont des incises de narration : les refuser, c'est **revenir en
arrière** sur ce qui marche aujourd'hui. Si tu ajoutes `ient`, `u`, `us`, `ut`,
`s`, `îmes`, `îtes`, `îrent`, la liste redevient acceptable — mais alors elle
laisse repasser « avait **repris** quelque espoir », que tu voulais éliminer.

**(b) Le plus important : tes « faux positifs » donnent le BON résultat.** Les
deux cas que tu cites pour Notre-Dame :

```
ch.14  « Cependant Gringoire, sans savoir pourquoi, avait repris quelque espoir… »
ch.28  « Heureusement la discrète damoiselle Oudarde Musnier détourna à temps… »
```

sont détectés par accident (radical `repri` dans « repris », `dis` dans
« discrète ») — mais ce sont de la **narration**, et le locuteur obtenu
(**narrateur**) est **juste**. Retirer le beat ne les « corrige » pas : ça les
renvoie au personnage qui les lisait à tort.

**Conséquence : le vrai critère n'est pas « le motif est-il propre ? », c'est
« le locuteur obtenu est-il le bon ? ».** Une liste de radicaux bancale peut
donner un bon résultat ; des terminaisons strictes peuvent en donner un mauvais.
Proposition : garder le motif **large** et traiter les faux positifs par une
**liste noire de mots entiers** (`discrétion`, `discrète`, `discutable`,
`disqualification`, `remarquable`, `conclusion`, `appel`, `intervention`…),
mesurée comme les autres — chaque entrée justifiée par un cas lu.

---

## 3. Ton R4 : attention aux homographes — « d'un **ton** sec »

Mesure sur Notre-Dame : 5 beats portent un « tu/vous/ton… ». **Quatre sont des
faux positifs** : « d'un **ton** tranquille », « d'un **ton** bref », « d'un
**ton** sec » — c'est le nom commun `ton`, pas le possessif. Le seul vrai cas est
« mon frère, c'est que **vous** aviez bien raison quand **vous** me disiez : »,
et il commence par une minuscule (donc R3 le concerne aussi).

Conclusion pratique : R4 reste utile comme **signal**, mais `ton` `ta` `tes`
apportent surtout du bruit en roman. `tu`, `te`, `toi`, `vous`, `votre`, `vos`
sont plus sûrs — et le chiffre du livre d'entretien (25/68) est à nettoyer de la
même façon avant d'en faire un seuil.

---

## 4. Ton R5 : approuvé, et le seuil classe parfaitement nos livres

Ton score (« entretien si narration < 20 % **et** au moins deux locuteurs > 15 % »)
a été calculé sur toute la bibliothèque :

| Livre | narration | 2ᵉ locuteur | gros locuteurs | verdict |
|---|---|---|---|---|
| Dialogues désaccordés | 11,8 % | 36,1 % | 3 | **ENTRETIEN** |
| Monte-Cristo T3 | 16,3 % | 24,6 % | 1 | roman |
| Monte-Cristo T4 | 21,1 % | 18,1 % | 1 | roman |
| Shantaram | 48,5 % | 16,2 % | 1 | roman |
| Notre-Dame de Paris | 48,5 % | 0 % | 0 | roman |
| Lazarille | 72,4 % | 0 % | 0 | roman |
| 22/11/63 | 55,5 % | 0 % | 0 | roman |
| (les autres tomes) | ≥ 26 % | — | 0 ou 1 | roman |

Deux choses à retenir : le livre d'entretien est **le seul** à sortir du lot, et
le seuil sauve **Monte-Cristo T3** — 16,3 % de narration (donc sous les 20 %)
mais **un seul** gros locuteur : ton critère « deux locuteurs » est ce qui
l'empêche d'être classé entretien. Le score tient donc sur nos données ; il reste
à l'écrire dans un test pour qu'il ne dérive pas.

---

## 5. Ce que je prends tel quel

- **R1** (compteur par paragraphe) : oui, correctif **et** rattrapage des
  morceaux déjà migrés — c'est le gain principal, et il porte sur une livraison
  du jour.
- **R3** (beat impur, coupe en trois) : oui, 75 cas mesurés — avec ton garde-fou
  « si aucun point de coupe, on ne coupe pas ».
- **R5** (mode par livre) et **R6** (dans le doute, hériter) : oui. R6 décrit
  exactement la **variante A** qui existe déjà dans l'outil de migration : le
  travail est une option à brancher, pas une réécriture.
- **Tes compteurs** `NE_DE_LA_COUPE` / `PREEXISTANT` : oui, et ton analyse est
  juste — la migration corrige aussi des morceaux **préexistants** mal étiquetés
  par l'IA (les beats de Notre-Dame sans deux-points sont des incises seules du
  type « Oudarde insista. »). Je n'ai pas encore le chiffre exact de la
  répartition : il sortira avec le prochain rapport.
- **Tes tests** : les 10 exemples du jeu d'essai avec l'étiquette attendue, les
  terminaisons et le motif de 2ᵉ personne comparés entre Python et JavaScript,
  l'échantillon gelé de 30 beats par livre (graine constante), et l'assertion
  « concaténation == texte d'origine » sur les 81 143 phrases. Tout est repris.
- **Ta réponse à la question 5** : une passe IA sur les résidus, en **bouton
  manuel**, jamais dans le chemin automatique. D'accord.

---

## 6. Les chiffres que tes rapports demandaient, et qui manquaient

1. **Dérive de citation** : 244 morceaux (dont 200 sur les 9 livres migrés),
   169 propres et 75 impurs.
2. **R2** : 24 beats touchés, dont **7 vrais verbes de parole perdus** (listés
   plus haut) — la règle, telle quelle, dégrade.
3. **R4 sur Notre-Dame** : 5 beats concernés, **4 sont le nom commun `ton`**.

Restent à mesurer, comme tu le signales honnêtement toi-même : **R7** (coupe
annulée quand la citation se referme et que la phrase continue), la répartition
`NE_DE_LA_COUPE` / `PREEXISTANT`, et le profil « 2ᵉ personne » du livre
d'entretien après nettoyage des homographes.

---

## 7. Plan proposé (une règle à la fois, chacune avec son chiffre)

| Étape | Travail | Chiffre de sortie |
|---|---|---|
| S1 | **R1** : compteur par paragraphe + rattrapage des 244 morceaux déjà migrés (copie datée, contrôle après) | refusés → beats, par livre ; non-régression vérifiée |
| S2 | **R3** (75 impurs) puis **R7** | coupes en trois ; coupes annulées |
| S3 | **R5 + R6** : colonne `mode_lecture`, score pré-rempli, bouton ; puis migration du livre 18 | 68 → 0 remis au narrateur pour l'entretien ; casting intact |
| S4 | **R2 sous forme de liste noire** + tests (10 exemples, échantillon gelé) | beats perdus, lus un par un |

---

## 8. Réponse au rapport 3 (même jour)

Les trois chiffres que tu demandais, mesurés (`_essais/_mesurer_demandes_claude.py`,
sur la copie de la base d'**avant** migration) :

**1. R2 avec ta liste complétée** (`u`, `us`, `ut`, `s`, `ient`, `îmes`, `îtes`
ajoutés) : R2 en perdrait **21**, et le classement exact est :

| Catégorie | Nombre | Ce que ça veut dire |
|---|---|---|
| **roman — de la narration à garder** | **10** | « Vivant, mes meilleurs amis évitent ma maison… », « Guillaume Rym crut devoir intervenir. », « Heureusement la discrète damoiselle… » : de la narration que l'IA avait donnée à un personnage |
| livre d'entretien (R5 s'en charge) | 10 | du discours d'essayiste, le mode par livre les laisse au personnage |
| impur (R3 s'en charge) | 1 | « s'est-il écrié, mais j'ai retenu sa main… » |

*(Correction de ma part : j'avais annoncé « 21 des 23 » à garder — c'était trop
optimiste. Le chiffre juste est **10 sur 21**, et c'est **R8 qui les récupère**,
donc ton raisonnement tient : une fois R2 réduit au métier 1, ces 10 ne sont plus
perdus.)*

**2. `NE_DE_LA_COUPE` / `PREEXISTANT`** : sur les **896** beats (les 652 d'avant
migration + les 244 rattrapés par le correctif R1), **723 sont nés de notre
coupe** et **173 sont préexistants**. C'est la mesure que tu demandais :
**173 morceaux de narration** (0,2 % des ~81 000 phrases) que l'IA avait donnés à
des personnages. Le casting n'a donc **pas** un problème massif — et il reste
invisible à la règle, celle-ci ne voyant que les morceaux qui introduisent une
citation.

**3. Livre 18 sans `ton / ta / tes`** : 71 beats (correctif R1 compris), dont
**24** portent une vraie 2e personne. Le bruit des homographes était faible
*dans ce livre* (contrairement à Notre-Dame, où 4 des 5 cas étaient le nom commun
« d'un **ton** sec »).

**Tes points, acceptés tels quels :**

- **R1 / S1** : j'ai fait la **passe « beats seulement »** — celle que tu
  proposais en second, et la plus sûre : pas de remappage d'index, 155
  réécritures de `speaker` sur la base actuelle, copie datée avant, contrôle
  après (« reste à corriger : 0 »). Rien de ce que Laurent a pu modifier depuis
  le 22/09 n'a été écrasé.
- **R4** : `ton`, `ta`, `tes` sortis ; `tu`, `te`, `toi`, `vous`, `votre`, `vos`
  gardés. Mesure faite : c'est ce filtre qui a sauvé les 12 morceaux de discours
  du rattrapage (dont le docteur d'Avrigny).
- **S2** : **R7 avant R3**, ton argument est bon (R7 annule des coupes, donc
  réduit ce que R3 a à traiter ; R3 en ajoute).
- **R5** : à figer en test avec les 11 livres comme **cas gelés**, en sachant
  qu'un **roman épistolaire** serait classé « entretien » à tort — ta réserve est
  notée dans le BACKLOG, et le bouton corrige d'un clic.
- **R3** : je lirai en priorité les 75 impurs du **troisième motif** que tu
  signales (ceux qui contiennent un `»` sans commencer par une minuscule ni par
  `»`), avant de fixer la coupe en trois.

---

## 9. R8, mesurée : elle tient — mais pas avec ton garde-fou

Chiffres (`_essais/_mesurer_regle_r8.py`, copie d'avant migration) :

| | Morceaux |
|---|---|
| R8 **sans** garde-fou au niveau du morceau | **98** |
| R8 **avec** le garde-fou | **77** |
| (répliques en tiret que le garde-fou a retenues) | **21** |

**Ton intuition est juste, et le surplus est propre.** Les 77 morceaux que la
règle actuelle ne voit pas (aucun verbe de parole) sont de la **narration pure** :

```
Franz lui présenta la lettre d'Albert.                          (T2)
M. d'Avrigny sourit d'un air sombre.                            (T5)
Le comte étendit la main dans la direction de la bibliothèque.   (T6)
Valentine poussa un gémissement.                                (T6)
Danglars sourit de cette confiante bonhomie du comte.           (T6)
```

**MAIS ton garde-fou « le paragraphe ne commence pas par — » ne protège rien**,
et c'est la découverte de la mesure : dans les longs dialogues en tirets, les
répliques sont séparées par des **lignes simples**, pas par des lignes vides.
Tout le dialogue tient donc dans **un seul paragraphe** au sens du découpage, et
R8 faisait basculer des **répliques** au narrateur :

```
— Non, mais son exécuteur testamentaire.      (l'abbé, T2)
— Oui, c'est cela.                            (l'abbé, T2)
— Un riche seigneur qui voyage pour son plaisir.   (le matelot, T2)
```

Le garde-fou doit porter sur **le morceau**, pas sur le paragraphe :

```
SI le morceau commence par un tiret (— ou –)            -> ne pas toucher
SI le morceau commence par une minuscule (suite)        -> ne pas toucher
SI le morceau commence par un guillemet (déjà cité)     -> ne pas toucher
```

Avec ces trois-là : **77 morceaux, tous justes à la lecture**.

**Tes deux points de vigilance, traités :**

- **Shantaram** : R8 touche **2** morceaux seulement étiquetés « Le narrateur »
  (sur 30 292 phrases). C'est marginal — un réglage « déclarer Le narrateur comme
  voix narrative du livre » ne se justifie pas pour 2 morceaux, mais c'est noté
  pour plus tard.
- **Les contre-exemples de R2** : il n'y en avait pas 2, mais **11** — et j'ai
  dû corriger mon propre chiffre (« 21 sur 23 » → **10 à garder**, 10 au livre
  d'entretien, 1 impur). Ces 10 ne sont plus un problème dès que R8 existe :
  c'est exactement ton raisonnement, et il tient.

**Ta colonne `ORIGINE = coupe | verbe | structure`** : reprise telle quelle. Le
rapport de simulation la portera, et c'est elle qui rendra chaque mouvement
lisible (« pourquoi ce morceau a bougé »).

**Reste à chiffrer à l'implémentation** : le total que R8 toucherait = les
**173** préexistants (dont certains seront écartés par les nouveaux garde-fous)
**+ les 77** nouveaux. Le chiffre exact viendra avec le code, parce que les
garde-fous s'appliquent aussi aux 173.

---

## 10. Réponse au rapport 4 : tes trois garde-fous, mesurés

Tu as raison, et je le dis nettement : **mon « 77, tous justes » était faux**. Ta
lecture ligne par ligne a trouvé les deux familles, et la mesure te donne raison.

| Étape | Morceaux |
|---|---|
| R8 brute (garde-fou au niveau du morceau) | 161 |
| après **G1** (la ligne) | 82 |
| après **G1 + G2** | 74 |
| après **G1 + G2 + G3** | **56** |

Soit **105 retenus sur 161** — les deux tiers. Et **les témoins survivent** :
« Valentine poussa un gémissement. » et « Danglars sourit de cette confiante
bonhomie du comte. » passent les trois garde-fous.

**G2 : 8 morceaux retenus, tous justes** — le meilleur rapport des trois :
« Pour être déposé, après ma mort, chez mon ami le général Durand… » (T4) ;
« Ils me haïssent, donc ils me craignent ? » (Haydée, T4) ; « Je meurs assassiné
par le Corse Benedetto… » (T5) ; « Je puis fournir à la commission d'enquête… »
(T5) ; « Mon père est oiseau. » (Esmeralda, ND) ; « Jusqu'à ce que l'Ancien me
recueille. » (Dunk). Les parts mesurées confirment le seuil : 0,2 % (T4), 0,3 %
(T5), 1,4 % (ND), **5,0 % (Chevalier Errant — c'est la limite, à surveiller)**.

**G3 : 18 morceaux retenus**, tous justes : « Luigi Vampa. » (signature),
« Signé : Abbé Busoni. », « Il se nommait Benedetto… », « Le présent acte, pour
lui donner toute foi… », « On aura la preuve de ce crime en l'arrêtant… »,
« Doris. » (Post-it). Ton critère « le morceau suit un bloc du même locuteur »
marche exactement comme tu l'annonçais.

**G1 : 79 morceaux retenus — et là je te dois une nuance.** En les lisant, une
partie est de la **vraie narration** : « La femme indiqua la direction du nord. »,
« Elle cacha ses yeux avec horreur. », « Dunk désigna ses pieds. », « Ser Bennis y
alla de son braiment de rire. ». La raison : dans ces ePub, **une même ligne** de
dialogue contient la réplique **puis** une phrase de récit — structurellement
**identique** à ta famille 2 (« — Oui. Ils me haïssent… »). Aucune règle locale ne
sépare « suite du discours » de « récit qui suit le discours » : c'est un
jugement sémantique. Donc **G1 protège au prix d'un gain plus faible** — et vu le
risque asymétrique que tu décris, c'est le bon compromis. Je le garde tel quel.

**Tes textes complets confirment ton diagnostic.** « Alors la peur le prit… »
(T3 ch. 8) est **dans le long récit de Bertuccio** : la ligne est « — Il le savait
si bien qu'à partir de ce moment il ne sortit plus seul… Alors la peur le prit… ».
Donc c'est **le personnage** — et G1 le retient. Idem pour « Il est vrai aussi que
la douceur de sa mère encouragea… », et pour « Enfin il **pousse** un dernier
râle » (T2 ch. 11), qui est suivi de « — … » et se trouve dans un récit.

**Le livre 18** : tu as raison, R8 ne s'applique qu'en mode roman — les morceaux
du livre d'entretien sortent du total (dont « tous ces secteurs où je les ai
découverts dominants. »).

**Ce que je te livre pour la relecture** (dossier `_essais/POUR_LE_LLM/`) :

- `r8_garde_fous.txt` — les comptes, les témoins, **ce que chaque garde-fou
  retient**, et les **56 survivants** à lire ;
- `r2_textes_complets_T5_T3.txt` — les **12** morceaux concernés **en entier**
  (morceau + sa ligne + 300 caractères de contexte) ;
- `preexistants_173.txt` — **les 173 préexistants en entier** (ta demande n° 3),
  même présentation, pour relire le mécanisme là où il a déjà servi.

**Sur l'ordre : d'accord avec toi, R8 ne va pas en base avant cette relecture.**
Et même après : avec les trois garde-fous, R8 ne touche plus 77 morceaux mais
**56** — c'est modeste, mais c'est du sûr, et ça vient *en plus* des 173.

---

## 11. Réponse à la note urgente : confirmée, mesurée, et l'outil est prêt

Tu as raison, et la mesure te suit.

**Étape 1 — ce qui est en base** (lecture seule,
`_essais/_mesurer_dans_la_replique.py`) :

| | Morceaux |
|---|---|
| morceaux DANS une réplique en tiret | **134** |
| dont déjà au personnage (rien à faire) | 81 |
| dont mis au narrateur par la **migration** du 23/09 | **14** |
| dont mis au narrateur par le **rattrapage** (155) | **39** |
| **à réparer** | **53** |

Ton ordre de grandeur « ~80 sur les 173 » est confirmé : la mesure donne **79
préexistants** — plus **55 nés de la coupe**, que tu soupçonnais. Et je le dis
nettement : **les 39 du rattrapage sont de ma main** — je ne testais que la tête
du morceau. La leçon est double : un garde-fou local ne suffit pas, c'est **la
ligne** qui porte l'information.

**Étape 2 — la règle.** `dans_la_replique` rend **134** morceaux, dont **46
lignes à tiret sans guillemet fermant** (celles que tu voulais lire : le récit de
Caderousse « — De jour en jour, il vivait plus seul et plus isolé… », la tirade
de Bertuccio…). Les cas que tu as vérifiés à la main (Maximilien, Bertuccio,
Cavalcanti, Eugénie) sortent tous du bon côté, et les incises **après** le `»`
restent au narrateur ✓.

**Étape 3 — l'outil est écrit et simulé** : `test_voix/_restaurer_hors_replique.py`.

- il **restaure l'étiquette d'origine** de la copie
  `bak_avant_dialogue_20260922_1311` — pour un beat, l'index se remappe 1:1,
  donc c'est bien une **restauration**, pas un nouveau casting ;
- **simulation** : **53** morceaux, exemples tous justes — « — Fais venir trois
  taxis », ai-je dit… → le narrateur de Shantaram ; « — Pas douce », se reprit
  lamentablement Dunk → Dunk ; « J'ai répondu : » → Danglars ; « Heureusement je
  me suis trouvé un peu fort du côté de la mâchoire » → Gringoire ;
- **écriture** : copie datée **avant**, contrôle après (aucun locuteur hors
  casting), nombre de réécritures par livre. Elle attend le feu vert de Laurent.
- **✅ FAIT le 23/09/2026 à 15 h** : Laurent a donné son feu vert, les **53**
  morceaux sont rendus à leur personnage (copie datée
  `nimm_epub.db.bak_avant_restauration_repliques_20260923_1459`). Contrôle sur
  trois états de la base (22/09, avant restauration, actuel) : la restauration
  **n'a inventé aucune étiquette** — les phrases hors casting sont un état
  **préexistant** (107 → 103 au T2, 136 → 131 au T6, 306 → 303 à Notre-Dame),
  c'est un sujet de **casting**, pas de découpage.

**Étape 4 — je prends ton ordre** : la règle sera intégrée à
`_migrer_index_dialogue.py` (où elle **remplace G1**, trop prudent, et protège
aussi les 723 morceaux nés de la coupe) et à `_rattraper_beats_derive.py` (qui ne
doit plus jamais la refaire) — **avant** R8, R7, R3 et R2.

**Le surplus R8 (56)** : propre à ~80 %, d'accord avec tes trois doutes —
« M. Léon d'Armilly » (signalement de passeport **lu par Eugénie**, à laisser à
Eugénie), le livre 18 (hors mode roman), et les pensées en italique de 22/11/63
et du Chevalier Errant. Ton idée de **porter l'italique dans une étiquette par
morceau** (sans toucher au texte affiché) est la bonne : je la mesure dès qu'on
traite ces deux livres.

Merci pour le sérieux : la dérive du compteur était **invisible de l'intérieur**
du projet, et c'est la lecture des 617 lignes de Notre-Dame qui l'a fait sortir.
