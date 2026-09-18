# Mémo pour l'atelier NIMM Voix — la voix et le texte (à réutiliser sur Pocket TTS)

Ce que NIMM ePub a appris le 16 et le 17/09/2026, en écoutant et en mesurant.
**Tout est reproductible tel quel** : ce sont des règles de texte, des réglages
de pause et une technique de génération — rien qui dépende de Kyutai.

---

## 1. Le texte, avant de le donner au moteur

Un moteur neuronal **essaie de prononcer** ce qu'il ne sait pas ignorer : d'où
des sons parasites. Ce qu'on fait, dans cet ordre :

| Règle | Pourquoi (mesuré) |
|---|---|
| Retirer les notes entre crochets `[1]`, les emojis, les caractères de contrôle | le moteur les vocalise ou bégaie |
| Développer les abréviations : `M.` → Monsieur, `Mme` → Madame, `N°` → numéro… | sinon il lit la lettre puis marque un arrêt sur le point |
| `...` → `…` | sinon **chaque point** est une pause (« .... » = 4 arrêts) |
| **`;` → `,`** | le point-virgule sortait en « euh » (constat de Laurent) |
| **`(` `)` → virgules** | le moteur les ignore : l'incise n'avait **aucune pause** autour |
| **Garder le point final** | le retirer ne change rien à la prosodie (test à l'aveugle, 2 séries), et il évite parfois une fin « en l'air » |
| Normaliser les espaces avant `.` `,` | typographie : sinon le moteur marque un blanc |
| Apostrophes typographiques `’` → `'` | **à tester sur Pocket TTS** (piste) |

**Signes de dialogue (`« »`, tiret cadratin)** : à trancher **moteur par
moteur**. Chez nous : XTTS les **prononçait** (« ogui… haa ») → on les retire
avant l'envoi ; NeuTTS n'en avait rien à faire ; Kyutai les **garde** (les
retirer dégradait). Donc : ne pas appliquer une recette d'un moteur à l'autre.

## 2. Le découpage, et la trouvaille du 17/09 : le CONTEXTE GLISSANT

- **un segment = une phrase** (jamais un paragraphe) : c'est ce qui permet de
  surligner exactement la phrase en cours ;
- attention aux moteurs qui **recollent** : NeuTTS découpe à 200 caractères puis
  recolle les morceaux, ce qui s'entend (prises collées). Kyutai ne découpe pas,
  et sa prosodie est meilleure pour cette raison.

**Le contexte glissant (idée de Laurent, à essayer sur Pocket TTS) :**

> Pour la phrase B, on envoie au moteur **la fin de la phrase A (6 à 8 mots)
> suivie de B**, puis on **coupe l'audio** pour ne garder que B. L'auditeur
> n'entend jamais le contexte.
>
> - **Effet mesuré et entendu** : plus de sautes de volume, voix « plus
>   chantée », et **moins de micro-coupures** (11 segments au lieu de 13, 20 au
>   lieu de 23 sur les mêmes phrases) ;
> - **comment couper** : générer le contexte SEUL (pour savoir où finit son
>   dernier son), puis « contexte + phrase » et couper **dans le premier silence
>   franc** qui suit — jamais à l'aveugle, jamais en plein mot ;
> - **garde-fou vital** : un contexte **trop long sature la fenêtre du modèle et
>   tronque la phrase**. Mesuré chez nous : avec la phrase précédente ENTIÈRE,
>   une phrase de 9,6 s est sortie en **1,4 s**. 6 à 8 mots suffisent ;
> - coût : une génération de plus par phrase (acceptable, et le cache absorbe).

## 3. Les pauses (le « point qui passe trop vite »)

Mesures faites sur nos moteurs, silence de **fin** de phrase :

| Moteur | silence de queue avant réglage |
|---|---|
| Kyutai | 0,30 à 0,43 s |
| Edge | 0,23 s (après rognage) |
| Kokoro / Piper | 0,10 s |

Réglages retenus chez nous (demande de Laurent : **+100 ms**) :
- silence de queue visé : **0,35 à 0,40 s** ;
- pause **entre paragraphes** (et entre deux répliques de dialogue) : **100 ms**
  — elle était à 0, c'était trop sec ;
- rognage des bords d'un fichier moteur : tête **0,08 s**, queue **0,35 s**.

## 4. Les phrases courtes : le vrai piège

Un moteur autorégressif démarre **à froid** : sur 4 à 15 caractères, il n'a pas
de matière et part en gargouillis, en mots répétés (« il partit, il parttit »)
ou en voyelles qui traînent. Constat : **« Non. »** et « — Oui. » dérapent chez
6 voix sur 6 (tous moteurs neuronaux confondus) ; **« Manger ? » passe** —
l'interrogation porte l'intonation.

Remèdes, du meilleur au moins bon :
1. **le contexte glissant** (§2) — c'est celui qui marche ;
2. fusionner la phrase courte avec sa voisine (mais on perd la frontière exacte
   de surlignage) ;
3. basculer sur un moteur stable (Edge, Kokoro) sous un seuil de caractères.

## 5. La méthode (ce qui a réellement fait avancer)

- **un seul paramètre à la fois**, et **à l'aveugle** quand il faut trancher ;
- **toujours écouter** avant de généraliser : nos mesures nous ont menti
  plusieurs fois (elles disaient « stable » alors que ça sonnait mal) ;
- **écrire les démentis** : sinon la croyance revient. Exemples consignés chez
  nous : « garder le guillemet ouvrant » (démenti **deux fois**), « le point
  final bride la prosodie » (démenti), « le défaut suit la voix » (démenti).

## 6. Choisir l'extrait qui sert de voix : un DIALOGUE, pas un récit (18/09/2026)

Le texte **lu** par le lecteur bénévole influence la prosodie que le moteur
apprend à imiter. Un extrait de **narration** donne une voix qui « lit une
histoire » ; un extrait de **dialogue** donne une voix qui « parle ». Constat de
Laurent, en écoutant les voix Kyutai : les passages de dialogue « donnent une
prosodie toute différente ».

Comment reconnaître un extrait de dialogue dans une page (Librivox, domaine
public) : chercher les **guillemets** (`« »`, `" "`) et les **tirets cadratins**
(`—`) qui ouvrent une réplique. Si la page n'en contient aucun, ce n'est pas un
dialogue, quel que soit le charme du passage.

Mesure faite dans NIMM ePub le 18/09/2026 sur les extraits déjà en service
(`test_voix/_analyse_extraits_dialogue.py`, qui lit les transcriptions gardées) :

| Famille | Extraits avec dialogue |
|---|---|
| CML-TTS (35 voix Kyutai + 25 XTTS) | **13 sur 60** (22 %) → **47 voix ont un extrait de pure narration** |
| extraits libres de droits choisis à la main | **2 sur 19** (plancher : leur texte est une transcription, qui ne met pas les guillemets) |
| voix Kokoro clonées | **0 sur 30** (leur référence est un texte de contrôle imposé) |

**ATTENTION — hypothèse, pas résultat** : ce qui est mesuré, c'est ce que
contiennent les extraits actuels ; l'effet du dialogue sur la prosodie n'est pas
encore mesuré. À confirmer par une écoute **comparative et à l'aveugle** : même
voix, deux extraits (un dialogue, un récit).

## 7. Les incises (« , dit-il, ») : à RETIRER du texte parlé (18/09/2026)

Quand chaque personnage a sa voix, l'incise qui dit **qui parle** est redondante —
et elle coupe la voix du personnage en pleine réplique. Banc d'écoute fait dans
NIMM ePub (lot `ecoute_ponctuation_20260918_1937`, 6 phrases réelles, 2 variantes
chacune) : Laurent a trouvé la version **sans incise** systématiquement
meilleure — « et en plus la voix me paraît plus fluide ».

Volume mesuré (tome 5 de Monte-Cristo, 5 105 phrases) : **289 phrases avec incise
= 5,66 %**, dont 104 à pronom (« dit-elle ») et 185 à nom (« dit Morrel »), soit
**0,94 % du texte** lu.

Règle **prudente**, mais qui va jusqu'au bout de l'incise (18/09/2026, fin de
soirée — trois exemples de Laurent où l'incise était encore lue) :

- **retirer l'incise EN ENTIER, complément compris** : le retrait s'étend jusqu'à
  la **virgule fermante** (« , dit-il au comte, ») ou jusqu'au point final si la
  suite ressemble à un complément (« , dit-il au comte. »). Bornes : une virgule
  au plus, pas de ponctuation forte, **≤ 70 caractères** ;
- **reconnaître l'incise qui OUVRE la phrase** (« fit celui-ci avec sa voix
  demi-railleuse, comment vous portez-vous ? ») : quand le découpage sépare les
  phrases au « ! », l'incise n'est plus entre deux virgules ;
- **emporter la RELATIVE qui suit l'incise** (« , dit Cavalcanti, **qui se
  grisait** à ce bruit métallique de paroles dorées. » → « c'est magnifique. »),
  sinon elle reste orpheline et se fait lire toute seule. Quatre garde-fous, tous
  posés par des cas réels : « que » est **exclu** (c'est le plus souvent une
  conjonction : « Le fait est que je meurs de soif ») ; aucune extension si la
  **proposition immédiate** est une question (« ? » ou « ! ») ; arrêt sur un
  **décrochage de sens** (« mais », « or », « puis »… **ou le point-virgule**),
  mais « **et qui** » n'en est pas un (relative coordonnée : « , dit Monte-Cristo,
  qui sentit…, et qui comprit… ; ma protection… » → on emporte jusqu'au
  point-virgule) ; et la **longueur emportée** est bornée (200 caractères), pas la
  phrase entière (chez Dumas, une phrase peut faire 400 caractères et finir par un
  « ? » qui n'a rien à voir avec l'incise) ;
- **remplacer par un court silence** (150 ms) une phrase qui n'est **que**
  l'incise (« dit Monte-Cristo. », isolée par le découpage au « ! » / « ? ») :
  on ne peut pas la vider (la phrase disparaîtrait), et l'auditeur n'a pas besoin
  de l'entendre — la voix du personnage dit déjà qui parle ;
- ne **jamais** toucher si l'incise n'est **pas fermée** : la retirer couperait
  la réplique en deux ;
- exiger une **frontière de mot** avant le verbe : « maudit-il », « interdit-il »
  ne sont pas « dit-il » ;
- respecter la **casse** : « répondit le jeune homme » n'est pas une incise ;
- **garde-fou vital** : si le retrait **vide** la phrase (une phrase qui n'est
  que l'incise), on ne retire rien — sinon le moteur reçoit un texte vide et la
  phrase **disparaît** de l'écoute.

Formes couvertes : pronom (« dit-il », « se demanda-t-elle », « ajouta-t-il »),
nom propre (« dit Barrois »), particule noble (« dit M. de Villefort »), nom
commun avec article (« dit le comte », « reprit la jeune fille »), démonstratif
(« fit celui-ci »).

**Compromis assumé** : le complément part avec l'incise (« dit-elle **en donnant
son flacon** ») — l'action n'est plus entendue, mais elle reste **affichée**.

Implémentation : `modules/incises.py` (NIMM ePub), appelée **après** le
développement des abréviations. Le texte **affiché** n'est jamais modifié.

**Deux pièges entendus sur ce banc, à connaître :**

1. un banc qui envoie le texte **brut** (sans le nettoyage du lecteur) entend
   « mleu » pour « Mlle » — c'est le banc, pas le livre : la lecture développe
   l'abréviation avant l'envoi ;
2. une phrase de **6 caractères** sans contexte glissant « traîne »
   (« Oui » → « ouiiiii ») : c'est le **contexte glissant** (§2) qui l'évite.

---

*Écrit le 17/09/2026, à la demande de Laurent, pour l'atelier NIMM Voix.
Sections 6 et 7 ajoutées le 18/09/2026 (retours d'écoute de Laurent).*
