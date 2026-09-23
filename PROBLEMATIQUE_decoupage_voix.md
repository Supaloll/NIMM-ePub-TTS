# Découpage du texte et attribution des voix — la problématique

**Ce document est fait pour être donné TEL QUEL à un autre assistant (LLM).**
Son but : décrire précisément le problème, la mécanique **déjà** en place, et les
cas qui résistent — pour obtenir des pistes concrètes et vérifiables. Écrit le
23/09/2026.

---

## 1. Le programme, en clair

Une application personnelle (locale, hors ligne pour le texte, Python + page web)
lit des romans au format ePub **à voix haute, avec une voix différente par
personnage** (« casting »). Un moteur de voix (TTS) est appelé pour chaque
morceau de texte.

Le texte d'un chapitre est donc :

1. **découpé en morceaux** (le plus souvent une phrase) ;
2. **étiqueté** : qui parle ? (le narrateur, ou un personnage) ;
3. **lu** par la voix du locuteur étiqueté — c'est ce qui donne l'immersion.

Deux règles d'or du projet :

- **le texte affiché n'est jamais modifié** : seul le texte *parlé* peut être
  nettoyé (incises retirées, majuscules, etc.) ;
- **un morceau = une voix** : la découpe ne peut pas couper au milieu d'un mot,
  et une phrase coupée en deux ne doit jamais faire changer de voix sans raison.

---

## 2. Le découpage « idéal » dont on rêve

Le critère n'est pas grammatical, il est **auditif** : chaque morceau devrait
être lu d'un bout à l'autre **par une seule voix**, et cette voix devrait être
celle qui parle réellement à ce moment du texte.

Concrètement, un découpage idéal satisfait ces six propriétés :

1. **la narration est au narrateur** — les passages de récit, les descriptions,
   les pensées rapportées, les dialogues au discours indirect
   (« Il répondit qu'il partirait ») ;
2. **la réplique est au personnage** — y compris les répliques en tirets
   (— Bonjour.), en guillemets (« Bonjour. »), sur plusieurs paragraphes, et les
   phrases courtes (cris, interjections : « Ah ! ») ;
3. **le morceau de narration qui introduit une réplique** (« Il se pencha et
   dit : « Bonjour. » ») est séparé de la réplique : la narration va au
   narrateur, la réplique au personnage ;
4. **les incises de parole** (« , dit-il, », « , répondit le comte, ») peuvent
   rester avec la réplique ou partir au narrateur — c'est un choix d'écoute —,
   mais elles ne doivent jamais **couper** une réplique en deux ni se retrouver
   orphelines ;
5. **une citation rapportée** (« J'ai jamais eu « la larme facile », comme on
   dit. ») ou **un texte lu par un personnage** (une lettre, un article, un
   ouvrage cité) ne doit pas être attribué au narrateur : c'est le personnage
   qui le lit qui le prononce ;
6. **aucun mot perdu, aucun mot déplacé** : la concaténation des morceaux doit
   redonner le texte d'origine, caractère pour caractère.

Le point le plus difficile est le **3** : décider si le morceau qui amène une
citation est du narrateur (cas du roman) ou du personnage (cas d'un entretien ou
d'un personnage qui cite un texte). Voir la section 5.

## 3. La mécanique actuelle, étape par étape

### 3.1 Le découpage en phrases

Règle unique, écrite deux fois (elle doit rester identique) : côté serveur
`modules/decoupage.py`, côté page `frontend/app.js` (`_buildSentences`). Un test
(`test_voix/test_decoupage_phrases.py`, **44 contrôles**) compare les deux.

- paragraphes séparés par une ligne vide (moins de 6 caractères : ignorés) ;
- coupe après un point, un point d'interrogation, un point d'exclamation, une
  ellipse ou un guillemet fermant, **suivi d'un espace** ;
- **sauf** si le mot qui précède le point est une abréviation française
  (`M.`, `Mme`, `Mgr`, `Dr`… et leurs formes en majuscules `MR.`, `MRS.`) : ce
  point appartient au mot. Sans cette exception, « M. | de Morcerf » coupait la
  phrase en deux (207 coupures constatées dans un seul tome) et le moteur
  inventait un son sur un morceau finissant par « monsieur » ;
- morceaux de 4 caractères ou plus conservés.

Historique : `REGLE_ANCIENNE` (avant le 18/09/2026, coupait après les
abréviations) et `REGLE_ACTUELLE` (corrigée). Les positions de chaque morceau
sont conservées (`phrases_avec_positions`) — c'est ce qui permet de **migrer**
les index quand la règle change.

### 3.2 La coupe « narration / réplique » (appelée « mode dialogue »)

C'est une **troisième règle** (`REGLE_DIALOGUE`), qui s'applique **livre par
livre** (colonne `books.decoupe_dialogue`) pour la raison expliquée en 3.4.

Après le découpage normal, chaque morceau est examiné :

- on cherche une **ouverture de citation** (`«`) dans le morceau ;
- le **texte qui précède** cette ouverture est un « **beat** » s'il **finit par
  deux points** *ou* s'il **contient un verbe de parole** — liste de **radicaux**
  (`VERBES_DE_PAROLE` : `dit`, `répond`, `s'écri`, `demand`, `repri`, `ajout`,
  `murmur`, `poursuiv`, `soupir`, `exclam`, `balbuti`, `chuchot`… ~80 entrées) ;
  chaque radical commence par une lettre ASCII, car le motif `\b` ne se comporte
  pas pareil en Python (Unicode) et en JavaScript (ASCII) ;
- **et** le morceau **suivant** commence par `«` ;
- alors le morceau est **coupé en deux, aux positions exactes** :
  le **beat** en premier (donné au **narrateur**), la **réplique** en second
  (qui reste au **personnage**).

Trois garde-fous, tous mesurés sur des cas réels :

1. le beat ne doit **pas contenir** d'ouverture de citation (sinon une réplique
   qui contient un verbe de parole serait prise pour un beat — pire que le
   défaut qu'on corrige) ;
2. une **citation racontée** (« J'ai jamais eu « la larme facile », comme on
   dit. ») n'est pas coupée : deux morceaux donneraient deux intonations
   finales ;
3. un **deux-points sans verbe de parole** (« Le sujet que j'avais donné
   était : « Le jour qui a changé ma vie. » ») ne déclenche pas la coupe.

Et un quatrième, qui vit dans la **migration** (pas dans le découpage) : si le
beat se trouve **dans une citation déjà ouverte** — un personnage qui rapporte
ses propres paroles (« …il m'a dit : « Fais ceci. » ») — le morceau **reste au
personnage** : on ne le remet **pas** au narrateur. Sinon la voix du personnage
serait coupée en deux au milieu de sa tirade. C'est la leçon dite « de
Lazarille » (21/09/2026), qui a fait **retirer du pipeline** une règle pourtant
séduisante (« un beat de narration est toujours du narrateur »).

### 3.3 L'étiquetage par l'IA (le « casting »)

Le découpage est **local et gratuit** ; l'étiquetage (« qui parle ») est fait par
un modèle de langage **payant** (`modules/voice_casting.py`), par lots de
morceaux, en JSON compact. Le prompt contient la fiche des personnages, le
chapitre, et **9 consignes**. Deux d'entre elles portent exactement notre
problème :

- **consigne 8** : « Une phrase qui contient une répartie entre guillemets ET son
  incise narrative (« … » dit Franz) va au PERSONNAGE qui parle, pas à la
  "narration". MAIS une phrase qui ne contient AUCUN mot entre guillemets et qui
  n'est qu'une INCISE DE PAROLE — « il m'a demandé. », « dit-il. », « répondit le
  comte. » — est de la NARRATION. »
- **consigne 9** : tant qu'un guillemet fermant n'est pas apparu, toutes les
  phrases d'une citation ouverte reçoivent **le même locuteur** (une citation
  coupée par un point d'exclamation interne ne change pas de voix au milieu).

C'est cette consigne 8, appliquée à la lettre sur un morceau **mixte**, qui
donnait le défaut fondateur : « Avant que j'aie pu répondre, Richie est
intervenu : «Non, c'est pas ça.» » était **un seul morceau**, donc lu **en entier
par Richie**, narration comprise. D'où la règle 3.2 : on ne demande plus à l'IA
de trancher un morceau mixte, on **coupe** avant qu'elle ne le voie.

### 3.4 Ce qui est enregistré — et pourquoi c'est contraignant

`speaker_attribution` mémorise, pour chaque livre, chapitre et **numéro de
phrase**, le locuteur. Ces numéros dépendent du découpage : **changer la règle
d'un livre déjà étiqueté décale toutes ses voix**. Trois conséquences :

- le mode dialogue est **par livre**, jamais global ;
- un livre **neuf** est casté directement en mode dialogue (activation
  automatique) ;
- un livre **déjà casté** doit être **migré** : l'outil
  `test_voix/_migrer_index_dialogue.py` recalcule la correspondance ancien
  morceau → nouveau(x) morceau(x) grâce aux positions, réécrit
  `speaker_attribution`, remappe la **reprise de lecture**
  (`progress.cursor_idx`), active le mode dialogue, puis **relit la base** pour
  contrôler. Il **refuse** de tourner sur un livre déjà en mode dialogue, et il
  fait une **copie datée de la base** avant d'écrire. Les voix, hauteurs,
  vitesses, verrous, fiches et alias ne sont **jamais** touchés — vérifié après
  coup (9 livres le 23/09/2026, casting identique).

### 3.5 Le nettoyage à l'écoute : le retrait des incises

À part du découpage, `modules/incises.py` retire les incises de parole de la
version **parlée** (jamais de la version affichée), parce qu'avec une voix par
personnage l'incise est redondante et coupe la réplique en deux. Règles
prudentes, chacune issue d'un dégât mesuré :

- on ne retire que si l'incise est **fermée** (virgule après le nom) ou
  **terminale** ;
- jamais si elle est suivie d'un complément qui deviendrait orphelin ;
- **frontière de mot** exigée avant le verbe (« maudit-il » n'est pas « dit-il ») ;
- la **casse** est respectée (« répondit le jeune homme » n'est pas une incise
  ordinaire) ;
- une **liste noire** écarte les mots en « -ant » qui ne sont pas des participes
  (`maintenant`, `pendant`, `pourtant`), sinon « , dit-il, MAINTENANT il faut
  partir. » perdait la fin de la réplique ;
- le « t » euphonique (`ajouta-t-il`) et le pronom réfléchi (`se demanda-t-elle`)
  sont reconnus.

Un code naïf proposé par un autre outil, essayé le 18/09/2026, abîmait **78 % des
phrases qu'il touchait** (588 sur 756) faute de ces garde-fous.

---

## 4. Ce qui a été corrigé, et comment (chronologie courte)

| Date | Défaut constaté (mesuré) | Correctif |
|---|---|---|
| 18/09 | point d'abréviation pris pour une fin de phrase (**207** coupures dans un tome) | découpage unifié dans `modules/decoupage.py`, testé contre la page |
| 18/09 | incises de parole lues en plein milieu d'une réplique | retrait des incises, avec 4 garde-fous (une version naïve abîmait 78 % des phrases touchées) |
| 19/09 | participe orphelin (« Merci, dit Morrel, se levant. » → « Merci se levant. ») | le geste suivant une incise fermée part avec elle ; liste noire des « -ant » |
| 19/09 | incise qui emporte la **relative** de la réplique (« C'est lui, dit Morrel, qui l'a voulu. ») | 3 familles identifiées, critère de tri (personne grammaticale, temps du verbe) ; non livré, encore ouvert |
| 21/09 | apostrophe typographique (`s’écria`) et radicaux manquants (`crier`, `soupir`…) : beats non reconnus | les deux apostrophes traitées pareil ; radicaux ajoutés ; **44 contrôles** |
| 21/09 | cris coupés par leur propre ponctuation (« « Jésus ! Jésus ! » ») : la 2ᵉ moitié repartait au narrateur | la citation ouverte garde son locuteur après `!`, `?` ou une ellipse |
| 21/09 | une règle « un beat est toujours du narrateur » cassait la voix d'un personnage qui cite ses propres paroles | règle **retirée** ; garde-fou « citation ouverte » à la place |
| 22/09 | un livre neuf casté en ancien découpage, mode dialogue à activer après coup | activation automatique au nouveau casting |
| 23/09 | 10 livres déjà castés en ancien découpage (voix décalées si on bascule) | migration des index : **9 livres, 327 morceaux** remis au narrateur, casting vérifié intact |

---

## 5. Ce qui résiste — les cas qu'on n'a pas résolus

### 5.1 Le cas principal : « Dialogues désaccordés » (livre d'entretien)

**Le livre.** Ce n'est pas un roman : deux essayistes se répondent, chacun
citant des textes, des articles, des ouvrages. Mesure sur les **1 779 phrases
attribuées** du livre :

| Locuteur | Phrases | Part |
|---|---|---|
| Naulleau | 643 | 36,1 % |
| Interlocuteur | 600 | 33,7 % |
| Soral | 325 | 18,3 % |
| narration | 210 | 11,8 % |
| Patrick Cohen | 1 | 0,1 % |

**Ce que la mécanique propose.** La simulation de la règle 3.2 détecte **68
beats** à remettre au narrateur (le 2ᵉ plus gros gain du lot, après Notre-Dame
de Paris). **Lecture faite, ces 68 morceaux ne sont pas de la narration** : ce
sont les paroles du personnage qui introduit une citation. Exemples réels
(texte exact) :

- ch. 5 — *Naulleau* : « En prologue de ces entretiens, j'ai donc entrepris de te
  lire ou de te relire, selon les cas, » → suivi d'une citation de *Sociologie
  du dragueur* ;
- ch. 9 — *Naulleau* : « Dans la mesure où tu uses de la Grosse Bertha comme
  d'autres d'une arme de poing, tu n'hésites pas à déclarer que cette réforme du
  code civil répond, je te cite » ;
- ch. 10 — *Naulleau* : « Permets-moi de te parler du passé - à chaque avancée de
  la loi… » ;
- ch. 17 — *Interlocuteur* : « Première remarque : j'ai passé sept ans au PC, j'ai
  travaillé dans la mode, le journalisme… » ;
- ch. 8 — *Naulleau* : « Remarquable fréquence du mot » ;
- ch. 31 — *Soral* : « Je ne vois pas en quoi les camps de concentration,
  invention anglaise mise en place pour la… ».

**Pourquoi la règle ne peut pas les distinguer.** Elle ne regarde que la
**forme** : deux-points, ou verbe de parole. Elle ne sait pas **qui parle**.
Dans un roman, le morceau qui introduit une citation est presque toujours du
narrateur ; dans un entretien, il est presque toujours du locuteur en cours (il
parle à la première personne : « je te lis », « Permets-moi »). Même forme,
sens opposé.

**Pourquoi le garde-fou existant ne s'applique pas.** Le garde-fou « citation
ouverte » compte les guillemets français (`«` / `»`). Dans ce livre, les
citations internes sont aussi écrites avec des guillemets d'un autre style
(« "Je ne veux pas que cette minorité… " »), donc le compteur ne voit pas la
citation ouverte et le refus ne se déclenche pas.

**Décision de Laurent, 23/09/2026 :** ce livre **n'est pas migré** pour
l'instant (les 9 autres le sont). Il attend une règle qui sait faire la
différence.

### 5.2 Le morceau qui emporte un mot de la réplique

Quelques morceaux (1 à 3 par livre) emportent avec le beat un bout de la
réplique, parce que la réplique se termine **après** l'ouverture de la citation
suivante. Exemples réels :

- « **une seule**, dit le Lucquois avec un soupir. » (Monte-Cristo T3, ch. 19) :
  « une seule » est la réponse du major Cavalcanti — ce mot serait lu par le
  narrateur ;
- « **— Fais venir trois taxis** », ai-je dit, ma voix me faisant l'effet de… »
  (Shantaram, ch. 6) : la réplique est à cheval sur deux morceaux ;
- « **», reprit le religieux à l'adresse de ser Lucas.** » (Le Chevalier Errant,
  ch. 3) : morceau qui commence par un guillemet fermant.

### 5.3 Les faux positifs de la liste de verbes de parole

Les radicaux sont cherchés **en début de mot** (`\b`), donc un mot ordinaire qui
commence par un radical est pris pour un verbe :

- « Constance et **discr**étion. » est classé « introduit une réplique » à cause
  du radical `dis` (« dis ») ;
- par extension : *discussion*, *discipline*, *discours*…

Effet : un morceau de narration attribué à un personnage peut être remis au
narrateur alors qu'il n'introduit aucune citation (ici, c'était même souhaitable,
mais **par accident**, donc non maîtrisé).

### 5.4 Le récit à la première personne

Dans *Shantaram*, il existe **deux** locuteurs distincts : « narration »
(48,5 % des phrases) et « Le narrateur » (16,2 %) — le personnage principal,
qui raconte à la première personne. Les morceaux du type
« , ai-je dit, et j'étais en effet heureux de sa compagnie » appartiennent au
**personnage**, pas à la voix narrative : la frontière entre les deux est
aujourd'hui une décision de casting, pas une règle.

---

## 6. Les chiffres du 23/09/2026 (état de référence, mesuré)

Les 10 livres « déjà castés » au 23/09/2026, mesure de la règle 3.2
(« beats » = morceaux de narration remis au narrateur ; « refusés » = laissés au
personnage parce que dans une citation ouverte) :

| # | Livre | Phrases (avant → après) | Beats | Refusés |
|---|---|---|---|---|
| 34 | Notre-Dame de Paris | 12 066 → 12 389 | 230 | 111 |
| 18 | Dialogues désaccordés | 1 779 → 1 851 | 68 | 7 |
| 35 | Le Chevalier Errant | 6 270 → 6 307 | 36 | 37 |
| 33 | Shantaram | 30 285 → 30 292 | 22 | 57 |
| 17 | Monte-Cristo T6 | 4 144 → 4 153 | 12 | 97 |
| 27 | Souvenirs d'une gamine | 6 133 → 6 190 | 11 | 0 |
| 16 | Monte-Cristo T5 | 5 105 → 5 127 | 5 | 74 |
| 14 | Monte-Cristo T3 | 4 947 → 4 972 | 5 | 127 |
| 8 | Monte-Cristo T2 | 5 036 → 5 052 | 4 | 99 |
| 15 | Monte-Cristo T4 | 5 378 → 5 388 | 2 | 82 |
| | **TOTAL** | 81 143 → 81 721 | **395** | **691** |

**État final :** 9 livres migrés (**327** morceaux remis au narrateur), casting
vérifié identique (voix, hauteur, vitesse, verrous, fiches, alias) ;
« Dialogues désaccordés » **en attente** (68 morceaux, voir 5.1).

Contrôles passés : 0 index hors bornes, 0 locuteur créé, 0 morceau orphelin ;
chaque voix pointe sur une phrase qui existe.

---

## 7. Les questions posées

1. **Le cœur du problème** : comment décider, de façon **fiable et vérifiable**,
   si un morceau qui introduit une citation appartient au **narrateur** ou au
   **locuteur en cours** ? Signaux envisageables : personnes grammaticales
   (`je` / `tu` / `nous`), présence d'une incise, longueur, type de livre, la
   distribution des locuteurs dans le livre… Quelles combinaisons, et **quel
   taux d'erreur** attendre ?
2. **Les citations imbriquées** : comment détecter une citation ouverte quel que
   soit le style de guillemets (`« »`, `" "`, `“ ”`, tirets de dialogue, citations
   sur plusieurs paragraphes) — de façon identique en Python **et** en
   JavaScript ?
3. **Le type de livre** : faut-il un mode « roman / entretien / essai » marqué par
   l'utilisateur (un bouton par livre), ou peut-on le déduire (part de narration,
   nombre de locuteurs, présence de `je` dans la narration) ?
4. **Les cas résiduels** (5.2, 5.3) : comment empêcher qu'un beat emporte un mot
   de la réplique ? Comment éviter les faux positifs de la liste de verbes
   (« discrétion ») sans perdre les vrais (« dit ») — exiger une frontière de mot
   *et* une forme verbale reconnue ?
5. **La frontière règle / IA** : où placer la limite entre une règle locale
   déterministe (gratuite, testable, identique des deux côtés) et un appel à un
   modèle (payant, non déterministe) ? Une seconde passe d'IA **sur les seuls
   morceaux douteux** (aujourd'hui 75 sur 395, soit 19 %) serait-elle
   acceptable ?
6. **L'évaluation** : comment mesurer objectivement une proposition ? Nous
   proposons un jeu d'essai (section 9) : à chaque exemple, la réponse attendue.

---

## 8. Les contraintes à respecter

1. **Rien n'est perdu** : la concaténation des morceaux doit redonner le texte
   d'origine, caractère pour caractère (les positions de coupe sont exactes).
2. **Deux implémentations** : le serveur (Python) et la page (JavaScript) doivent
   appliquer la même règle — un test compare les deux listes et les deux motifs.
3. **Migration obligatoire** : les index de phrases sont enregistrés ; toute
   évolution du découpage doit être capable de **remapper** les index d'un livre
   déjà étiqueté (et de remapper la reprise de lecture).
4. **Le texte affiché ne change jamais** ; seul le texte parlé est nettoyé.
5. **La règle est locale et gratuite** ; l'IA ne sert qu'à étiqueter des morceaux
   déjà numérotés (elle ne peut pas couper un morceau en deux).
6. **Toute règle doit être mesurée avant d'être adoptée** : nombre de morceaux
   touchés, exemples avant/après lus à la main, et un test de non-régression.
   Trois pistes « évidentes » ont été écartées ainsi (voir 4) parce que la lecture
   du texte les a démenties.

---

## 9. Le jeu d'essai (exemples réels, avec la réponse attendue)

Chaque ligne donne un extrait **réel** (issu des livres du projet) et le
comportement souhaité. Un LLM qui propose une règle peut la confronter à cette
liste — ce sont ces cas-là qui départagent.

| # | Extrait (texte réel) | Réponse attendue |
|---|---|---|
| 1 | « Avant que j'aie pu répondre, Richie est intervenu : « Non, c'est pas ça. » » | narration → **narrateur** ; réplique → **personnage** |
| 2 | « Il partit, dit-il. » | incise : à l'écoute elle peut disparaître ; **le morceau reste au personnage** |
| 3 | « En prologue de ces entretiens, j'ai donc entrepris de te lire ou de te relire, selon les cas, » (suivi d'une citation) | **personnage** (c'est lui qui parle), PAS le narrateur |
| 4 | « une seule, dit le Lucquois avec un soupir. » | **personnage** : « une seule » est sa réplique ; l'incise peut aller au narrateur, pas le mot |
| 5 | « Constance et discrétion. » | **ne doit pas** être classé « introduit une réplique » (faux positif `dis`) |
| 6 | « J'ai jamais eu « la larme facile », comme on dit. » | **un seul morceau**, citation racontée : pas de coupe |
| 7 | « Le sujet que j'avais donné était : « Le jour qui a changé ma vie. » » | **un seul morceau** (deux-points sans verbe de parole) |
| 8 | « Frère Mariano, …, s'écria : « Jésus ! Jésus ! » » | « Frère Mariano… s'écria : » → **narrateur** ; les deux « Jésus ! » → **personnage** |
| 9 | « Oudarde insista. » / « Mahiette poursuivit. » (suivi d'une réplique) | **narrateur** (vraie incise seule) |
| 10 | « Il répondit qu'il partirait le lendemain. » | **narrateur** (discours indirect) |

---

## 10. Comment utiliser ce document

- Les sections 3 et 4 décrivent **ce qui existe** : une proposition qui les ignore
  repartira de zéro sans raison.
- Les sections 5 et 9 donnent **ce qui échoue** aujourd'hui et **la façon de le
  vérifier** : c'est là qu'un regard neuf est le plus utile.
- Toute proposition est bienvenue **à condition d'être vérifiable** sur les 10
  exemples de la section 9, et de dire **combien de morceaux** elle toucherait
  dans les 10 livres du projet (81 143 phrases).
