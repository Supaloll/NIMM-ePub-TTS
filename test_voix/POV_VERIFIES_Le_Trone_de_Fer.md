# Les POV du Trône de Fer, VÉRIFIÉS — 15/10/2026

**Ce que c'est.** La vérification, chapitre par chapitre, des **surnoms** et des **titres
descriptifs** qui échappent à la reconnaissance automatique. C'est la matière de la table
`pov_surnoms` (voir `ARCHITECTURE.md`, sujet « Le narrateur d'un chapitre est le personnage
qui raconte ») : elle se remplira **au premier tome casté**, et ce document dit **qui**
rattacher **à quoi**.

**Comment c'est vérifié — deux sources, jamais une seule :**

1. **La mesure, dans le texte** (`test_voix/_proposer_surnoms_pov.py`) : combien de fois
   chaque nom est **nommé dans le chapitre même**. C'est la preuve interne, gratuite et
   reproductible. Un vrai POV est nommé **des dizaines de fois** dans ses propres chapitres ;
2. **Wikipédia FR**, page *A Feast for Crows*, section « Personnages principaux » (récupérée
   le 15/10/2026) : elle donne la liste officielle des POV et **leur nombre de chapitres** —
   ce qui permet de départager deux candidats (voir « LE NOYÉ » ci-dessous).

**La règle qui en sort** : au-delà de **3 mentions** du nom dans le chapitre, c'est un POV
**prouvé**. En dessous, c'est à confirmer — et le texte ne le dira pas toujours : c'est le cas
de **SCHLINGUE**.

---

## AFFC (tomes 10, 11, 12) — POV confirmés par Wikipédia FR

| Surnom du chapitre | Proposition | Mesure dans le chapitre | Source |
|---|---|---|---|
| `LE PROPHÈTE` | **Aeron Greyjoy** | **Aeron 40**, Tifs-Trempes 23 | Wikipédia : « Aeron Greyjoy, dit Tifs-Trempes, **prophète du Dieu Noyé** (2 chapitres) » |
| `LE NOYÉ` | **Aeron Greyjoy** | Balon 15, **Aeron 15**, Victarion 13 | Wikipédia : Aeron a **2** chapitres, Victarion en a **2** (« Le Capitaine de fer » + « Le Ravisseur ») — et le « prêtre noyé », c'est Aeron |
| `LE CAPITAINE DES GARDES` | **Areo Hotah** | **Hotah 24**, Lancehélion 18 | Wikipédia : « Areo Hotah, **capitaine des gardes** du prince Doran (1 chapitre) » |
| `LE CHEVALIER SOUILLÉ` | **Arys du Rouvre** | **Arys 23**, Myrcella 16 | Wikipédia : « Arys du Rouvre, **chevalier de la Garde Royale** en mission à Dorne (1 chapitre) » |
| `LE CAPITAINE DE FER` | **Victarion Greyjoy** | **Victarion 33**, Euron 18 | Wikipédia : « Victarion Greyjoy, **capitaine de la Flotte de Fer** (2 chapitres) » |
| `LE RAVISSEUR` | **Victarion Greyjoy** | **Victarion 50**, Euron 36 | Wikipédia : c'est son **2ᵉ** chapitre |
| `LA FILLE DE LA SEICHE` | **Asha Greyjoy** | **Asha 32**, Harloi 23 | Wikipédia : « Asha Greyjoy, **la fille de Balon Greyjoy** (1 chapitre) » |
| `LE FAISEUR DE REINES` | **Arianne Martell** | **Arianne 29**, Myrcella 20 | Wikipédia : « Arianne Martell, fille du prince Doran (2 chapitres) » (elle veut **faire** une reine de Myrcella) |
| `LA PRINCESSE EN LA TOUR` | **Arianne Martell** | **Arianne 38**, Hotah 17 | Wikipédia : c'est son **2ᵉ** chapitre |
| `ALAYNE` | **Sansa Stark** | **Alayne 27** puis **65**, Petyr 32 puis 25 | Alayne est le **pseudonyme** de Sansa (Petyr = son « père ») |
| `CAT DES CANAUX` | **Arya Stark** | **Arya 13**, Brusco 14 | « Cat des canaux » est le nom de rue d'Arya à Braavos |

---

## ADWD (tomes 13, 14, 15) — POV confirmés par la mesure

| Surnom du chapitre | Proposition | Mesure dans le chapitre | Remarque |
|---|---|---|---|
| `LE DOMESTIQUE DU MARCHAND` | **Quentyn Martell** | **Quentyn 40**, Gerris 22 | ✅ net |
| `LE LORD PERDU` | **Jon Connington** | **Griff 45**, Aegon | « Griff » est son nom d'emprunt |
| `LE GRIFFON RESSUSCITÉ` | **Jon Connington** | **Connington 39** | ✅ net |
| `LE PRINCE DE WINTERFELL` | **Theon Greyjoy** | **Theon 34**, Ramsay 27 | ✅ net |
| `LE TOURNE-CASAQUE` | **Theon Greyjoy** | **Theon 33**, Dustin 24 | ✅ net |
| `UN FANTÔME À WINTERFELL` | **Theon Greyjoy** | **Theon 27**, Bolton 17 | ✅ net |
| `LA PRISE DU ROI` | **Asha Greyjoy** | **Asha 40**, Justin 20 | ✅ net |
| `LE SACRIFICE` | **Asha Greyjoy** | **Asha 37**, Justin 18 | ✅ net |
| `LE PRÉTENDANT DE FER` | **Victarion Greyjoy** | **Victarion 43** | ✅ net |
| `LE BRISEUR DE ROI` | **Barristan Selmy** | **Barristan 55**, Selmy 22 | ✅ net |
| `LE CHEVALIER ÉCARTÉ` | **Barristan Selmy** | Hizdahr 23, **Barristan 22** | ✅ net |
| `LA MAIN DE LA REINE` | **Barristan Selmy** | **Barristan 39**, Selmy 16 | ✅ net |
| `LE PRÉTENDANT ÉCONDUIT` | **Quentyn Martell** | **Quentyn 20**, Gerris 12 | ✅ net |
| `LE DOMPTEUR DE DRAGONS` | **Quentyn Martell** | **Quentyn 28**, Gerris 16 | ✅ net |
| `LES ERRE-AU-VENT` | **Quentyn Martell** | **Quentyn** (compagnie des Erre-au-Vent) | ✅ net |
| `LA PETITE AVEUGLE` | **Arya Stark** | Pynto 9, **Arya 7** | ✅ net |
| `SCHLINGUE` (3 chapitres) | **Theon Greyjoy** | **Schlingue 26 / 45 / 50**, Ramsay 17 / 37 / 44 | ⚠️ **le texte ne dit JAMAIS « Theon »** : c'est le livre qui cache qui est Reek. C'est **le cas d'école** de la table |
| `LA LAIDERONNE` | **Arya Stark** | Noir 6, Multiface 6, Canaux 6 | ⚠️ **à confirmer** : la mesure est faible (Arya n'est pas dans les cinq premiers). Ma lecture le dit, mais ce n'est pas prouvé ici |

**Total : 29 surnoms ou titres descriptifs**, dont **27 nets** et **2 à confirmer**.

---

## Ce qui n'est PAS un surnom (et ne doit pas être relié)

- **Les prénoms** des tomes 01 à 09 (`BRAN`, `CATELYN`, `EDDARD`, `JON`, `ARYA`, `SANSA`,
  `TYRION`, `DAENERYS`, `DAVOS`, `THEON`, `JAIME`, `SAMWELL`) : ils seront reconnus **tout
  seuls** dès que le tome sera casté — **aucune ligne à écrire**. C'est eux qui allongent la
  liste aujourd'hui : le livre n'est pas encore casté, donc aucun nom ne peut être rapproché.
- **Les pages de garde et les notes** : « Chapitre 1 » (page de titre), « PRINCIPAUX
  PERSONNAGES », « RÉSUMÉ », « REMERCIEMENTS », « Une argutie » (note de l'auteur), « DU MÊME
  AUTEUR », « PRÉLUDE ». La narration en revient au **narrateur du livre**, et c'est voulu.
- **Les prologues** (« PRÉLUDE ») : ils ont bien un POV, mais il change d'un tome à l'autre et
  meurt presque toujours à la fin du chapitre — on ne les relie pas.

## Le cas du Chevalier Errant (tome 00) — pas un surnom

Ses cinq chapitres s'appellent « Chapitre N » : **aucun candidat à rattacher**, donc la table
ne peut rien pour lui. Et il n'en a pas besoin : son POV est **unique** (Dunk), nommé **211 /
170 / 209 / 175 fois** dans ses quatre chapitres. Ce livre se règle par le **menu du
narrateur** (choisir la voix de Dunk) — c'est déjà ce qu'il fait.

## Ce qu'on en fera

1. **Importer et caster** le premier tome du Trône de Fer (le casting est **partagé par la
   saga** : une fois fait, les tomes suivants en héritent) ;
2. **Écrire la table** d'un coup, à la portée de la **saga** (`saga:Trone de fer`), avec
   l'outil : `python test_voix/_proposer_surnoms_pov.py --livre <n> --ecrire "LE NOYÉ=Aeron"`.
   L'outil **rapproche** le nom donné du casting (« Aeron » trouve « Aeron_Greyjoy ») et
   **refuse** un personnage absent : ce refus est le contrôle — un nom que le casting n'a pas
   produit (orthographe différente, personnage secondaire) sera **signalé**, jamais écrit ;
3. **Vérifier à l'oreille**, sur le premier chapitre d'un tome à surnom.

**Rappel** : la table est **vide** aujourd'hui, et **aucun** livre ne change tant qu'aucune
ligne n'y est écrite.
