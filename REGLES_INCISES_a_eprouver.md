# Les règles de retrait des incises — à éprouver

**Ce document est fait pour être donné TEL QUEL à un autre assistant (LLM).**
Son but : trouver les phrases où ces règles se trompent. Écrit le 19/09/2026.

---

## 1. Le contexte (ce que fait le programme)

Le programme lit des romans à voix haute avec **une voix différente par
personnage**. Avant d'envoyer une phrase au moteur vocal, un **nettoyage** est
appliqué.

**Règle d'or : le texte AFFICHÉ ne change jamais.** Seule la version *parlée*
est nettoyée.

Une des opérations du nettoyage consiste à **retirer les incises de parole** :
les bouts qui disent *qui* parle (« , dit-il, », « , répondit le comte, »).
Pourquoi : avec une voix par personnage, l'auditeur *entend* déjà qui parle ; ces
incises coupent la réplique en deux.

Exemple réel :

    le livre dit     : — Il partit, dit-il.
    le moteur reçoit : — Il partit.

---

## 2. Les règles, dans l'ordre

### Étape A — repérer ce qui RESSEMBLE à une incise

Trois formes sont cherchées, **et seulement trois** :

1. **Incise à pronom** : une virgule ou un tiret, puis un VERBE de parole, le
   « t » euphonique éventuel, puis un pronom.
   → `, dit-il` • `, s'écria-t-elle` • `, se demanda-t-elle` • `, ajouta-t-on`
2. **Incise à nom** : une virgule ou un tiret, puis un VERBE de parole, puis un
   nom. Ce nom peut être un nom propre (`Morrel`), une civilité avec point
   (`M. de Villefort`), un démonstratif (`celui-ci`), ou un **nom commun avec
   article** (`le comte`, `la jeune fille`).
   → `, dit Barrois` • `, dit M. de Villefort` • `, dit le comte` • `, fit celui-ci`
3. **Incise en TÊTE de phrase** (elle ouvre le morceau) :
   → `fit celui-ci avec sa voix demi-railleuse, comment vous portez-vous ?`

Un **verbe de parole** est un mot d'une **liste fermée** (~110 formes). Les plus
courants : dit, dis, dirent, répondit, répond, répliqua, s'écria, cria, demanda,
reprit, ajouta, murmura, poursuivit, continua, hasarda, observa, remarqua,
s'exclama, prononça, balbutia, soupira, grommela, gronda, tonna, vociféra,
interrompit, fit, répéta, avoua, déclara, conclut, acheva, commença, termina,
insista, objecta, riposta, répartit, interrogea, questionna, exigea, ordonna,
supplia, pria, songea, gémit, sanglota, plaida, protesta, appela, conseilla —
plus leurs formes à l'imparfait (disait, répondait, demandait, ajoutait,
reprenait, murmurait, continuait, répétait, criait, observait, songeait,
pensait, expliquait, racontait, déclarait, balbutiait, soupirait, grommelait,
insistait, avouait, concluait).

⚠️ **Un verbe de parole qui n'est pas dans cette liste n'est pas détecté du
tout** : l'incise reste et sera lue.

### Étape B — décider si on PEUT la retirer

Une incise n'est retirée que si elle est :

- **fermée** : ce qui suit commence par une **virgule** ou un **point-virgule** ;
- ou **terminale** : il ne reste rien après, ou seulement un point, un point
  d'exclamation, un point d'interrogation, des points de suspension, ou un
  guillemet fermant.

Sinon on essaie d'**étendre** (étape C). Si ça ne suffit pas, **on ne retire
rien du tout** : l'incise reste et sera lue.

### Étape C — étendre jusqu'à la virgule suivante

« , dit-il au comte, » → l'extension emporte « au comte, ». Bornes :

- une seule virgule au plus ;
- la suite ne doit contenir **aucune ponctuation forte** (`. ! ? … : ;`) ;
- la suite ne doit pas dépasser ~70 caractères.

### Étape D — la relative part avec l'incise

Si l'incise est suivie d'une **relative** (qui, dont, où, auquel, laquelle…),
elle part avec elle :

    — C'est magnifique, dit Cavalcanti, qui se grisait à ce bruit.
    → — C'est magnifique.

Mais on s'arrête à un **décrochage de sens** : un point-virgule, ou une
conjonction de coordination (`mais`, `or`, `car`, `donc`, `cependant`, `puis`…).
La relative **coordonnée** (`et qui…`) part avec l'incise ; le `que` de
conjonction, non.

### Étape E — une phrase qui n'est QU'une incise

« demanda Morrel. » ne devient pas vide : le programme joue un **court silence**
(150 ms) à la place. Sinon le moteur vocal recevrait un texte vide, et la phrase
disparaîtrait de l'écoute.

### Étape F — le nettoyage final

- la **ponctuation basse restée en tête** de phrase après un retrait est
  supprimée (espace, `,` `;` `:` `.` `…`) — mais **jamais** le tiret de dialogue
  ni le guillemet ouvrant, qui sont légitimes ;
- `;` devient `,` ; ` : ` devient `,` ; les parenthèses deviennent des virgules ;
- le `!` devient `,` dans une phrase **courte** (25 caractères ou moins), et `.`
  dans une phrase entière ;
- un point final n'est jamais ajouté après « Monsieur », « Madame », « Docteur »…

---

## 3. LES GARDE-FOUS (ce qui ne doit JAMAIS arriver)

1. **Jamais de mot orphelin.** « j'écoute, répondit le jeune homme ; parlez. » ne
   doit JAMAIS donner « j'écoute jeune homme ; parlez. » (le mot reste collé,
   le sens casse).
2. **Jamais de phrase vidée** (sinon : plus aucun son).
3. **Jamais de suppression du sujet de la réplique** : seuls les mots de
   l'incise partent.
4. **La casse et la forme du nom comptent** : `répondit le jeune homme` est une
   incise, mais pas `répondit avec humeur` (pas de nom) ni `répondit fort`.
5. **Frontière de mot** : « maudit-il » ou « interdit-elle » ne doivent pas être
   pris pour « dit-il » / « dit-elle ».

---

## 4. EXEMPLES (déjà connus — ne les repropose pas)

**RETIRÉ** (le texte parlé) :

    — Il partit, dit-il.                                → — Il partit.
    — Le fait est, dit Barrois, que je meurs de soif.   → — Le fait est que je meurs de soif.
    — Il partit, dit-il en souriant.                    → — Il partit.
    bonjour, dit-il au comte.                           → bonjour.
    j'écoute, répondit le jeune homme ; parlez.         → j'écoute ; parlez.
    criait Villefort ; où est-il ?                      → où est-il ?      (incise en tête)

**GARDÉ** (et donc **lu**, faute de mieux) :

    — Mais vous, mademoiselle, dit Morrel vous qui êtes si chère ?   (incise NON fermée)
    ajouta Valentine en s'adressant à Noirtier.                      (la phrase n'est QUE l'incise)
    — Non, dit avec un imperceptible sourire de mépris le comte.     (complément AVANT le nom)

**CAS CONNUS ET NON RÉSOLUS** (à ne pas re-signaler, sauf si tu apportes mieux) :

    — Eh !        (une interjection de 5 caractères : le moteur invente un mot)
    dit Mme Danglars en signant.     (civilité SANS point : le motif s'arrête à « Mme »)
    , dit avec un sourire le comte   (complément avant le nom : non détecté)

---

## 5. TA MISSION

Tu es un **chercheur de failles**. On te donne ces règles ; ton but est de
trouver les phrases **françaises réalistes** (roman du XIXᵉ siècle, style Dumas)
où elles se trompent.

Cherche trois familles de défauts, par ordre d'importance :

**A. RETRAIT À TORT** *(le plus grave)* — la règle retire du texte qui ne devait
pas partir : un mot de la réplique, un morceau de description, le sujet…
Donne la phrase, ce que la règle fait, et pourquoi c'est faux.

**B. RETRAIT MANQUÉ** — l'incise reste lue alors qu'elle devrait partir. Cherche
en particulier :
- les **verbes de parole absents de la liste** (chuchota, susurra, rugit, bégaya,
  persifla, lança, jeta, lâcha, rétorqua, s'indigna, s'écria-t-il de nouveau…),
- les **constructions inhabituelles** : incise au milieu d'une incidente, incise
  après un point d'exclamation, **deux incises dans la même phrase**, incise
  inversée (« le comte dit », « ce fut Morrel qui répondit »), incise après une
  parenthèse, incise avec le verbe avant le nom (« demanda, d'une voix sèche, le
  comte »).

**C. EFFET DE BORD** — la règle produit un texte bizarre : double virgule,
ponctuation orpheline, phrase qui perd son sens, majuscule en plein milieu, deux
incises qui se chevauchent.

**Contraintes** : pas de phrases artificielles ; pas de cas déjà cités en
section 4 ; et **explique toujours par quelle étape précise le défaut passe**.

---

## 6. CE QUE TU DOIS RENDRE

Un tableau, une ligne par cas trouvé :

| # | Phrase du livre | Ce que la règle fait | Le défaut | Gravité | Correction proposée |
|---|---|---|---|---|---|

Puis, à la fin : **les 5 cas les plus dangereux**, classés, avec la raison.

Si une famille ne te donne rien, **dis-le franchement** plutôt que d'inventer
des cas impossibles : on préfère un « je n'ai rien trouvé » honnête à dix faux
positifs.
