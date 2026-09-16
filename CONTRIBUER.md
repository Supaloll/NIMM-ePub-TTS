# Contribuer à NIMM ePub

Merci de passer par ici ! Ce document résume tout ce qu'il faut savoir pour
installer le projet, le lancer, le tester et proposer une amélioration — sans
avoir à fouiller le dépôt.

## Ce qu'est le projet

NIMM ePub est un **serveur local** (Python / FastAPI) qui transforme un fichier
EPUB en **livre audio lu par plusieurs voix** : une voix par personnage, choisie
automatiquement par une IA, puis conservée d'un tome à l'autre dans une saga.
L'interface est une page web (HTML / CSS / JS **sans framework**), utilisable
depuis un téléphone et installable en PWA. Le projet vise un usage **personnel
et familial** : il tourne chez soi, sur son propre ordinateur.

## Les trois idées qui expliquent tout le reste

1. **Un livre = des phrases.** Le texte est découpé en phrases numérotées ; une
   phrase = une requête de synthèse = un morceau d'audio **mis en cache**. C'est
   ce découpage qui permet la surbrillance au mot près et la reprise après une
   coupure réseau.
2. **Le casting est une donnée, pas un réglage.** La voix de chaque personnage
   vit en base (table `voices`) : elle se corrige à la main à tout moment, et un
   « re-cast » regratuit redistribute les voix sans refaire d'analyse IA.
3. **Rien ne se perd.** Un **cache disque** garde chaque phrase déjà synthétisée
   et une **cascade de moteurs de secours** évite qu'une panne gâche une lecture.

## Prérequis

| Outil | Pour quoi | Remarque |
|---|---|---|
| **Python 3.14** | le lecteur (le serveur) | version de référence du projet |
| **Node.js** | les tests de logique JavaScript | rien d'autre à installer |
| **Git** | le dépôt | — |

Les **moteurs de voix lourds** (Kyutai, XTTS v2) sont **facultatifs** : ils
demandent un environnement Python 3.12 séparé et une carte graphique NVIDIA.
Le projet fonctionne sans eux (Edge en ligne, Kokoro et Piper sur processeur).

## Installation et démarrage

Suivez le **`README.md`** : il donne l'installation pas à pas (dépendances,
modèles de voix, clés d'API, lancement). En résumé :

```
python -m pip install -r requirements.txt     # les 14 paquets du lecteur
START.bat                                      # lance le lecteur (port 8081)
```

`data/config.json` (clés d'API) n'est **jamais** dans le dépôt : copiez
`data/config.example.json` et remplissez-le. Sans clés, tout fonctionne sauf
l'analyse automatique du casting (cast manuel, Edge, Kokoro et Piper restent
disponibles).

## Lancer les tests

Le projet n'a pas de framework de test : chaque vérification est un **script
autonome** qui affiche `TOUT EST OK` ou la liste de ses échecs. À lancer depuis
la racine du dépôt.

**Python** (aucun appel payant) :

```
python test_voix/test_pool_casting.py        # le pool de voix du casting
python test_voix/test_ids_ecran.py           # l'écran et le code restent d'accord
python test_voix/test_annotations_voix.py    # les notes d'écoute (sauve/restaure)
python test_voix/test_attribution_criteres.py # l'attribution des voix par critères
python test_voix/test_borne_babil_xtts.py    # garde-fou anti-babil (XTTS)
python test_voix/test_rogner_babil_xtts.py   # coupure du babil après un silence
python test_voix/test_lire_moi.py            # le mode d'emploi de test_voix/ est à jour
python test_voix/test_libelles_voix.py       # les voix ont toujours un prénom
python test_voix/test_nettoyage_xtts.py      # ponctuation retirée avant XTTS
python test_voix/test_reprise_casting.py     # reprise d'une analyse interrompue
python test_voix/test_estimation_cout.py     # estimation du coût d'une analyse
python test_voix/test_anti_blocage.py        # lots de phrases d'une analyse IA
python test_voix/test_diagnostic_gemini.py   # pourquoi l'IA a refusé de répondre
python test_voix/test_start_moteur.py        # lancement des moteurs de voix
python test_js_syntax.py                     # syntaxe de frontend/app.js
```

**JavaScript** (avec Node) :

```
node test_voix/test_etat_casting.js          # badges « à caster » / « voix partagée »
node test_voix/test_filtre_genre.js          # menus de voix (femmes/hommes)
node test_voix/test_voix_ecoutables.js       # voix d'un moteur éteint
node test_voix/test_message_reseau.js        # quand le lecteur annonce une coupure
```

**À éviter sans le vouloir** : `test_voix/_PAYANT_test_attribution_api.py` et son
lanceur `_PAYANT_lancer_test_attribution.bat` **appellent réellement les API d'IA**
(donc facturent). Ils sont **protégés depuis le 16/09/2026** : sans l'option
`--je-paie`, le script affiche un avertissement et **s'arrête sans rien
envoyer** (l'ancien nom, `test_attribution.py`, ressemblait à un test — un
double-clic sur son lanceur suffisait à partir, et donc à payer).
Trois autres scripts appellent une IA **locale** (Ollama), donc **gratuite**,
mais ils font travailler la carte graphique : `_test_local_ollama.py`,
`_test_local_variantes.py`, `_test_nuit_modeles.py`.

**Le reste du dossier** : `test_voix/LIRE_MOI.md` dit en une page quels fichiers
sont des tests (sans risque), quels sont des outils de diagnostic (lecture
seule) et quelles données ne doivent pas être supprimées.

## Les conventions du projet

Ce dépôt a une culture (elle vient du projet **NIMM**, le chatbot dont celui-ci
est le petit frère) — la suivre, c'est déjà contribuer :

- **Tout est en français** : code, commentaires, documentation, messages
  affichés. Les utilisateurs ne sont pas développeurs.
- **Un commentaire explique POURQUOI**, jamais *ce que fait* la ligne. Le
  pourquoi est souvent une décision (datée, avec le nom de la personne qui l'a
  prise), et c'est ce qui manque le plus quand on relit six mois après :
  *« Pourquoi rogner ? Parce qu'Edge ajoute ~1 s de silence en fin de phrase
  (mesuré le 08/09/2026) »* vaut mieux que *« on rogne le silence »*.
- **Un bug corrigé = un test qui le verrouille.** Tous les tests de la section
  précédente sont nés comme ça : un défaut observé, puis un script qui échoue
  bruyamment si le défaut revient.
- **Petites étapes.** Une amélioration à la fois, vérifiée, documentée. Le
  `BACKLOG.md` est la mémoire du projet : chaque item livré y raconte ce qui a
  été fait, pourquoi, et comment c'est vérifié.
- **Pas de nouvelle dépendance sans en parler.** Le lecteur tourne sur
  Python 3.14, sans PyTorch : c'est ce qui lui permet de démarrer en quelques
  secondes sur n'importe quelle machine. Les moteurs lourds vivent à côté, dans
  leurs propres environnements.
- **Pas de régression silencieuse.** Si un test ne passe plus, c'est le code
  qu'il faut corriger — pas le test à assouplir.

## Ce qui n'est JAMAIS versionné (et pourquoi)

`.gitignore` protège des choses qui ne doivent jamais entrer dans le dépôt, ni
dans son historique :

| Élément | Raison |
|---|---|
| `data/config.json` | les **clés d'API** de l'utilisateur |
| `data/library/`, `data/exports/` | les **livres** et les livres audio exportés (œuvres sous droits) |
| `data/annotations_voix.json` | les **notes d'écoute personnelles** de l'utilisateur |
| les modèles de voix (`.onnx`, `.bin`) | des centaines de Mo, téléchargeables |
| `data/tts_cache/` | le cache audio (se régénère tout seul) |
| `*_service/voix_fr/`, `*_service/.venv/` | extraits de voix et environnements Python |

Si vous ajoutez un fichier qui contient une clé, un livre ou une donnée
personnelle : **mettez-le dans `.gitignore` avant de le créer**. Un secret
entré dans l'historique Git y reste, même si on supprime le fichier ensuite.

## Les cinq moteurs de voix

| Moteur | Où il tourne | Qualité | Particularité |
|---|---|---|---|
| **Edge** (Microsoft) | en ligne | bonne | il faut Internet ; voix très stables |
| **Kokoro** | sur le **processeur** | variable | timbres étrangers avec français forcé |
| **Piper** | sur le processeur | simple | voix générique des petits rôles |
| **Kyutai** | carte graphique (~3,8 Go) | très naturelle | 35 voix françaises **libres** (CC BY) |
| **XTTS v2** | carte graphique (~2,2 Go) | très naturelle | clonage de voix (licence non commerciale) |

Un seul moteur lourd à la fois : ils se partagent la carte graphique. Le
réglage du dernier moteur utilisé est mémorisé (`data/moteur_voix.txt`).

## Les documents du projet

| Fichier | Contenu |
|---|---|
| `README.md` | installation et prise en main, pour l'utilisateur |
| `ARCHITECTURE.md` | la **mémoire technique** : comment chaque pièce fonctionne |
| `BACKLOG.md` | les décisions, les mesures, ce qui reste à faire |
| `CONTRIBUER.md` | ce document |
| `MEMO_XTTS_v2_pour_Cline.md` | les mesures et pièges du moteur XTTS v2 |

## Licences

Le programme est distribué sous **GPL-3.0** (voir `LICENSE`) : plusieurs
briques utilisées l'imposent (`piper-tts`, `pedalboard`, `phonemizer-fork`,
`EbookLib`). Les modèles de voix et les extraits de voix ont leurs propres
licences, détaillées dans `kyutai_service/ATTRIBUTION.md` et
`xtts_service/ATTRIBUTION.md` — **lisez-les avant de partager un audio produit**
(le moteur XTTS v2 est réservé à un usage non commercial).

## Proposer une amélioration

1. Créez une branche (`git switch -c ma-petite-amelioration`) ;
2. Faites la modification, **avec son test** si c'est une correction de bug ;
3. Vérifiez que les tests de la section « Lancer les tests » passent ;
4. Ouvrez une **Pull Request** ici, en expliquant en français ce que ça change
   *à l'usage* (pas seulement dans le code) — c'est le plus utile pour un
   relecteur non développeur.

Une idée sans code est tout aussi bienvenue : ouvrez une « issue » en décrivant
ce qui vous gêne à l'usage. Bon nombre d'items du `BACKLOG.md` sont nés comme
ça.
