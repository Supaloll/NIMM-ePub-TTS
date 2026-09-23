# 🧭 La méthode de l'atelier

*Ce document dit comment on travaille ici. Il est là parce que Laurent l'a
demandé — « parfois je suis un peu perdu sur la méthode » (23/09/2026). Il ne
remplace pas les règles (`.clinerules`) ni le BACKLOG : il les met en ordre.*

---

## En une phrase

**On ne croit pas un chiffre sans lire le texte, et on ne croit pas une règle
sans l'avoir mesurée.** Tout le reste en découle.

---

## La boucle, en cinq temps

### 1. Comprendre — « qui a fait ça ? »

Avant de corriger, on cherche **qui est responsable** du défaut :

- **l'IA de casting** (elle a étiqueté de travers) ;
- **le découpage** (la coupe a séparé ce qu'il ne fallait pas) ;
- **une de nos règles** (la migration, le rattrapage : ils écrasent parfois une
  étiquette juste).

L'outil qui répond à ça : `_essais/_diagnostiquer_passage.py` — il montre le même
passage dans **trois états** de la base (avant tout, après migration, maintenant).
C'est ce qui a disculpé la migration le 23/09 sur Notre-Dame ch. 28.

### 2. Mesurer — gratuit d'abord

On produit **un chiffre**, et on le produit **sur une copie datée ou en lecture
seule**. Jamais sur la base vivante.

- la mesure la plus utile est souvent **gratuite** (lecture seule) ;
- un appel payant ne se justifie que quand la réponse ne peut pas être obtenue
  autrement — et il passe toujours par un outil dont le nom porte `PAYANT` et qui
  refuse de partir sans `--je-paie`.

### 3. Lire — le chiffre ne suffit jamais

On **lit les cas**, un par un. La leçon du 21/09/2026 : *« un chiffre ne vaut
rien sans la lecture du texte »*. Trois exemples vécus le 23/09 :

- le devis annonçait « 395 beats » et c'était juste — mais 68 d'entre eux
  auraient coupé la voix d'un personnage en deux : la **lecture** l'a évité ;
- une règle proposée par un autre modèle **perdait sept vraies incises** : il
  fallait lire les 23 cas pour le voir ;
- et un de mes propres chiffres (« 21 des 23 ») était faux : la lecture du
  classement l'a corrigé.

### 4. Décider — et c'est Laurent qui décide

Cline **explique** : ce que ça change, les risques, les options en français. Il
ne présente jamais un bloc de code à valider. Laurent tranche — et sa décision
s'écrit (BACKLOG, JOURNAL).

### 5. Écrire — puis vérifier

Pour toute écriture dans la base :

1. **copie datée AVANT** (`nimm_epub.db.bak_avant_<quoi>_<date>`) ;
2. l'écriture ;
3. **contrôle APRÈS** : chaque index dans les bornes, aucun locuteur inventé, le
   casting intact ;
4. la **commande de retour arrière**, imprimée à la fin ;
5. et un **lanceur double-clic** (`.bat`) : Laurent ne tape jamais une commande.

---

## Les règles d'or (elles ne se négocient pas)

- **Jamais** d'écriture en base sans copie datée et contrôle après.
- **Jamais** un chiffre présenté sans avoir lu le texte derrière.
- **Une hypothèse démentie s'écrit** au BACKLOG (sinon la croyance revient).
- **Toute commande destinée à Laurent existe en double-clic**.
- **Le doute ne dégrade pas** : quand une règle ne sait pas trancher, on ne
  touche pas (règle R6, « dans le doute, hériter »).
- **L'oreille de Laurent passe avant tout** : elle est le juge final, et c'est
  elle qui a trouvé les répliques en tiret.

---

## Où sont les choses

| Document | Ce qu'il raconte |
|---|---|
| `BACKLOG.md` | **la liste de travail** — ce qui reste à faire, par priorité. En haut, les urgences. |
| `JOURNAL.md` | **l'histoire de la collaboration** — ce qui a marqué, l'ambiance. Lu au début de chaque session. |
| `ARCHITECTURE.md` | **comment le code fonctionne** (bloc « Aujourd'hui » par sujet, puis la chronique). |
| `test_voix/LIRE_MOI.md` | **quel outil fait quoi**, et **quel lanceur double-cliquer**. |
| `_essais/POUR_LE_LLM/` | les dossiers prêts à transmettre à un autre assistant. |
| `PROBLEMATIQUE_decoupage_voix.md` | le dossier de fond sur le découpage (à donner à un LLM). |

---

## Un exemple, pris à la journée du 23/09/2026

1. **Mesure** : la migration a refusé 244 morceaux à tort (compteur de citation
   ouverte calculé par chapitre au lieu du paragraphe).
2. **Lecture** : « Elle arrêtait les passants et criait : » est de la narration →
   le refus était bien une erreur.
3. **Décision** : Laurent valide le rattrapage.
4. **Écriture** : 155 morceaux remis au narrateur, copie datée, contrôle
   (« reste à corriger : 0 »).
5. **Puis re-mesure** : un relecteur extérieur relit le surplus ligne par ligne →
   il trouve 53 répliques encore chez le narrateur → **on remesure, on lit, on
   restaure**.
6. **Et on s'arrête** quand c'est l'oreille qui doit parler.

---

*Un chiffre, un texte, une décision, une copie datée. C'est tout.* 🙂
