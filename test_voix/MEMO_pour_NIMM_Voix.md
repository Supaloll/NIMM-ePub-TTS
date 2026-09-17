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

---

*Écrit le 17/09/2026, à la demande de Laurent, pour l'atelier NIMM Voix.*
