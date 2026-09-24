# test_voix — le dossier d'atelier

Ce dossier contient **deux choses très différentes**, et c'est ce qui rendait la
lecture difficile :

1. les **vérifications du projet** (des tests qui ne coûtent rien et qui disent
   « TOUT EST OK » ou « N ECHEC ») ;
2. des **outils d'atelier** accumulés depuis le début : diagnostics, mesures,
   comparaisons de modèles. Certains appellent de vraies API (donc facturent).

Ce fichier dit en une page ce qu'on peut lancer sans risque — et ce qu'il faut
éviter.

---

## 🖱️ Comment lancer un outil (sans taper de commande)

Tu n'as **pas** besoin de savoir taper des commandes : les actions utiles ont un
**lanceur en double-clic** (un fichier `.bat`, comme ailleurs dans le projet).

| Lanceur (double-clic) | Ce qu'il fait |
|---|---|
| `LANCER_TOUS_LES_TESTS.bat` | **lance TOUS les tests d'un coup** (page + serveur, une quarantaine de secondes) et n'affiche que l'essentiel : à la fin, tu dois lire « **TOUT EST OK** ». Rien n'est modifié, rien n'est facturé, aucun moteur n'est démarré — c'est le réflexe à prendre avant de considérer une modification comme livrée |
| `AUDITER_DOCUMENTATION.bat` | **vérifie que la documentation dit encore la vérité sur le code** (22/09/2026) : fichiers cités qui n'existent plus, fonctions/constantes disparues, routes absentes de `main.py`, colonnes de table absentes de la base, tests disparus, items du BACKLOG déjà livrés. Le rapport **défile à l'écran** et reste dans `_audit_documentation.txt` — **lecture seule**, rien à allumer |
| `VERIFIER_FAITS_ARCHITECTURE.bat` | **vérifie les PHRASES de `ARCHITECTURE.md`**, là où l'audit ne regarde que les noms (23/09/2026) : le plan du dossier, les constantes citées **avec leur valeur**, les ports des moteurs, les fichiers de données, la version de cache, le sujet `modules/tts.py` (ses sept moteurs et ses nombres de voix), le sujet `frontend/ — Interface` (les vues de la page), le sujet `Pocket TTS` (catalogue, constantes du service, modèle) et le sujet `Report des notes d'écoute` (l'outil de report et ses garde-fous, les boutons d'état, les seuils, le plafond de noms, les tests cités), et le sujet `Distribution de voix par personnage (IA)` (les **quatre** moteurs et le défaut, le repli automatique, les **onze** routes du casting, les **huit** colonnes de la table `voices`, les tests cités), et le sujet `Rognage des silences de bord` (les marges réelles du filtre d'Edge, le rognage des services **XTTS** et **NeuTTS**, la respiration de **Kyutai** — 0 par défaut —, ce que fait **Pocket** à la place, la clé du cache, et les **quatre** tests cités, comptés en les lançant). À la fin, tu dois lire « **0 ecart(s) a lire** » — **lecture seule**, rien à allumer |
| `ECOUTER_PRONONCIATION.bat` | le **lot d'écoute de la prononciation des prénoms** (21/09/2026) : pour chaque prénom, ce que Kokoro dit **avant** et **après** le correctif — c'est ton oreille qui valide la graphie |
| `LANCER_BANC_ECOUTE_XTTS.bat` | fabrique un **lot d'écoute XTTS** (qualité des phrases : attaque, incise, tiret, phrase courte, fin de phrase) sur deux voix |
| `LANCER_BANC_PONCTUATION.bat` | fabrique un **lot d'écoute sur la ponctuation du « ! »** (point / virgule / suspension / rien) **et sur les incises** (gardées ou retirées), sur les mêmes phrases réelles d'un livre — **Kyutai allumé**. Tu écoutes et tu classes, je règle ensuite |
| `LANCER_BANC_INCISES.bat` | fabrique un **lot d'écoute des INCISES DE PAROLE** (22/09/2026) : pour chaque phrase, **A = incise muette** (comportement d'aujourd'hui) et **B = incise dite par le narrateur** (le nouveau bouton du lecteur). Deux séries : les incises déjà reconnues (réglables tout de suite) et celles que l'étape 3 apportera (« m'a-t-elle répondu »). Il montre aussi si les morceaux se collent — **serveur NIMM + Kyutai allumés** |
| `LANCER_OU_SONT_MES_VOIX.bat` | affiche **où en sont tes voix** : combien de personnages lisent avec chaque moteur, combien sont verrouillés, et si chaque voix attribuée existe bien dans le catalogue (rien n'est modifié) |
| `MIGRER_PETITS_ROLES.bat` | 🎭 **donne Jessica (femmes) et Pierre (hommes) à tous les petits rôles** (moins de 8 répliques) des livres **déjà castés** (21/09/2026) : il montre d'abord ce qu'il ferait (essai), puis, si tu réponds **O**, il applique — avec **copie datée de la base avant d'écrire** |
| `MODE_DIALOGUE.bat` | ✂️ **sépare la narration des répliques, LIVRE PAR LIVRE** (21/09/2026) : dans « Richie est intervenu : «Non…» », le beat revient au narrateur et la réplique au personnage. Il affiche la liste des livres, puis demande le numéro et **A** (activer) ou **D** (revenir au découpage d'origine). Attention : un livre **déjà casté** doit être **re-casté** après, car les numéros de phrases changent |
| `MIGRER_DIALOGUE.bat` | ✂️🔄 **le MÊME mode dialogue, mais pour un livre DÉJÀ CASTÉ — sans re-cast** (23/09/2026) : il fait **les deux en une fois**, un livre à la fois — il **remappe les numéros de phrases** (qui parle) **et** active le mode dialogue, pour que les voix ne se décalent pas. Ton casting ne bouge pas (voix, hauteurs, vitesses, verrous, voix du narrateur : jamais touchés). Il affiche les livres concernés, puis pour le numéro choisi il montre d'abord un **essai** (les beats remis au narrateur), et si tu réponds **O** il applique — avec **copie datée de la base avant d'écrire**. **N'utilise pas `MODE_DIALOGUE.bat` sur ces livres-là** : activer le mode sans migrer les index décalerait les voix |
| `MESURER_LE_CASTING.bat` | 🧪 **mesurer le casting IA, gratuitement** (23/09/2026) : avant de construire du contexte narratif pour le casting, on regarde ce qu'il **rate vraiment**, sur **4 chapitres difficiles** (Notre-Dame ch. 55 — le long mémoire, Monte-Cristo T3 ch. 8 — Bertuccio, un chapitre d'entretien, Shantaram ch. 6). Il compte les erreurs **dures** (une réplique lue par le narrateur ; un locuteur que le casting ne connaît pas), les **discutables** (une incise seule chez un personnage : la consigne 8 dit non, l'oreille tranche) et une liste **à lire**. **Lecture seule**, rien à allumer, rien de facturé |
| `OU_EN_SONT_MES_LIVRES.bat` | 📊 **le tableau de bord, en une page** (23/09/2026, demande de Laurent : « je ne sais pas trop où on en est ») : pour chaque livre, le nombre de phrases, le **découpage** (origine / narration séparée), la **part de narration**, les **personnages** et les **gros locuteurs**, les **incises** (muettes ou lues) et les **locuteurs hors casting à revoir au casting**. **Lecture seule**, rien à allumer, rien de facturé |
| `CORRIGER_UN_MORCEAU.bat` | 🎧 **corriger la voix d'un passage entendu de travers** (23/09/2026, retour d'écoute de Laurent) : tu donnes le **numéro du livre** puis un **extrait du texte** entendu (« Ah bah ») ; il dit **qui le lit aujourd'hui**, te donne la liste des personnages au casting, et si tu tapes le nom exact d'un personnage il corrige — **copie datée de la base avant**. Il refuse d'écrire si l'extrait désigne plusieurs morceaux ou si le nom n'est pas au casting. Sert quand aucune règle ne sait trancher (une réplique courte lue par le narrateur, par exemple) |
| `LANCER_BANC_ECOUTE_NEUTTS.bat` | fabrique un **lot d'écoute NeuTTS** (livre et chapitre au choix) pour comprendre où la voix dérape : vraies phrases du livre, signes de dialogue avec/sans, phrases courtes, phrase longue d'un bloc puis coupée en deux — **le moteur NeuTTS doit être allumé** |
| `LANCER_BANC_ECOUTE_KYUTAI.bat` | le **même lot sur Kyutai** (mêmes phrases, mêmes voix : les deux moteurs partagent les mêmes extraits) pour **comparer** les deux — **Kyutai allumé, NeuTTS éteint** (ils ne cohabitent pas sur la carte graphique) |
| `_PAYANT_lancer_test_attribution.bat` | ⚠️ **payant** : appelle de vraies API d'IA — il demande confirmation avant de partir |
| `APPLIQUER_LES_NOTES_D_ECOUTE.bat` | 🎧 **fait remonter tes notes d'écoute dans les catalogues** (23/09/2026) : les **étoiles** (0 étoile = voix écartée du casting automatique) et le **genre**. Il montre d'abord ce qu'il ferait, puis, si tu réponds **O**, il applique — avec **copie datée** de `main.py` et de `modules/tts.py` — et il finit par le contrôle du pool de casting. À faire **après** ton passage dans « 🎧 Écouter les voix », et **relance le lecteur** ensuite |

Les lanceurs vérifient **tout seuls** que le moteur dont ils ont besoin est
allumé, et ils **attendent à la fin** (la fenêtre reste ouverte pour que tu lises
le résultat — ferme-la quand tu as fini).

Et si un jour tu veux lancer un `.py` à la main (les commandes citées dans ce
fichier) : ouvre ce dossier dans l'explorateur, **clic droit dans un espace vide
→ « Ouvrir dans le Terminal »**, puis colle la commande
(`python test_voix/le_script.py`). C'est tout — et tu peux aussi simplement
demander un lanceur, c'est deux minutes à fabriquer.

---

## ⚠️ D'ABORD : les deux fichiers qui COÛTENT de l'argent

| Fichier | Ce qu'il fait |
|---|---|
| `_PAYANT_test_attribution_api.py` | envoie un **vrai chapitre** aux API d'IA (Gemini, Mistral, DeepSeek) — **chaque appel est facturé** |
| `_PAYANT_lancer_test_attribution.bat` | son lanceur (double-clic) — il demande confirmation avant de partir |
| `_PAYANT_recaster_un_livre.py` | **re-caste un livre ENTIER** (un livre déjà casté ne peut pas l'être depuis l'interface) : copie datée de la base, effacement de l'attribution, estimation du coût, confirmation, casting, suivi — **facturé** |
| `_PAYANT_lancer_recaster_un_livre.bat` | son lanceur double-clic (il enchaîne les contrôles de cohérence à la fin) |

Ils sont **renommés et protégés le 16/09/2026** : sans l'option `--je-paie`, le
script affiche un avertissement et **s'arrête sans rien envoyer**. Avant, un
simple double-clic suffisait à payer.

**Trois autres scripts appellent une IA, mais en LOCAL (Ollama) : c'est
gratuit** — ils font seulement travailler la carte graphique :
`_test_local_ollama.py`, `_test_local_variantes.py`, `_test_nuit_modeles.py`.

---

## 🎚️ Ajouter des voix Kokoro au lecteur (ça ÉCRIT — mais avec copie datée)

`_importer_voix_kokoro.py` ajoute au fichier de voix du lecteur
(`voices-v1.0.bin`) les **timbres** d'un fichier de voix venu de l'atelier
NIMM Voix (un lecteur Kokoro ne sait pas lire des WAV : il lui faut le timbre).

    python test_voix/_importer_voix_kokoro.py                   -> APERCU, ecrit rien
    python test_voix/_importer_voix_kokoro.py --quoi accent_allemand --ecrire

Ce qu'il fait **tout seul** : **copie datée** du fichier de voix avant d'écrire,
refus de tout nom déjà pris (un doublon écraserait une voix existante en
silence), contrôle de la forme des timbres, puis **relecture du fichier écrit**
(compte exact, et aucune voix d'avant n'a bougé). Les voix ne sont utilisables
qu'après leur **ajout dans la liste `KOKORO_VOICES`** — les deux vont ensemble.

`_tester_voix_kokoro_importees.py` vérifie ensuite qu'elles **parlent** vraiment :
il fait parler le moteur par le **vrai chemin du lecteur** et mesure durée et
niveau (aucune parole = échec). L'oreille reste juge, dans « 🎧 Écouter les
voix ».

**Et pour les ICÔNES de l'application** : `_generer_icones_pwa.py` les régénère
à partir du logo maître (aperçu par défaut, `--ecrire` pour fabriquer les
fichiers). C'est le geste quand un navigateur **refuse d'installer**
l'application : la taille annoncée dans `frontend/manifest.json` doit correspondre
au fichier, sinon Chrome rejette les icônes et n'affiche pas « Installer »
(vérifié par `test_pwa_manifeste.py`).

---

## 🎭 Les PETITS RÔLES : Jessica (femmes) et Pierre (hommes) — ça ÉCRIT aussi

Décision de Laurent du 21/09/2026 : tout personnage de **moins de 8 répliques**
est joué par une voix générique selon son genre — **Jessica** (`piper:upmc:0`)
et **Pierre** (`piper:upmc:1`), les deux en Piper — et **chacun reçoit sa
propre variante** de hauteur et de vitesse : **11 hauteurs × 13 vitesses =
143 variantes par voix**. Avant, ces petits rôles n'avaient **aucune** voix :
c'était le **narrateur** qui les lisait.

`migrer_petits_roles.py` applique cette décision aux **livres déjà castés** :

    python test_voix/migrer_petits_roles.py             -> ESSAI, n'ecrit rien
    python test_voix/migrer_petits_roles.py --appliquer -> ecrit (copie datee)

Ce qu'il fait **tout seul** : d'abord un **essai** (livre par livre, avec des
exemples de la répartition : quel personnage, quelle voix, quelle hauteur,
quelle vitesse), puis — seulement avec `--appliquer` — une **copie datée de la
base AVANT d'écrire**, l'écriture de **trois colonnes** (`voice_id`, `pitch`,
`rate`), et une **relecture** de contrôle (aucune ligne ne doit rester à mettre
en forme).

Ce qu'il ne touche **jamais** : les rôles de 8 répliques et plus, et les lignes
**verrouillées** (un verrou veut dire « je garde cette voix »). Les variantes
sont réparties **par livre et par genre**, si bien que deux petits rôles du même
livre **n'ont jamais la même voix au timbre près** (jusqu'à 143 par genre ; le
plus gros besoin mesuré est de 85, dans Monte-Cristo T6).

Le lanceur double-clic **`MIGRER_PETITS_ROLES.bat`** fait l'essai, demande
« J'applique ? (O/N) », puis applique et affiche le nom de la copie de retour
arrière. **Recharge la page** du lecteur ensuite, pour voir le nouveau casting.

---

## 🎧 Tes notes d'écoute des voix : les faire APPLIQUER (ça ÉCRIT aussi)

Quand tu annotes une voix dans « **🎧 Écouter les voix** » (étoiles, genre, âge,
timbre, débit, accent, registre, rôle), tes notes sont rangées dans
`data/annotations_voix.json` — un fichier **local**, qui ne touche à rien
d'autre. Deux d'entre elles seulement doivent **remonter dans les catalogues** :

- les **étoiles** : c'est ce qui décide si la voix entre dans le **pool
  automatique du casting** (0 étoile = voix **écartée** du pool, mais toujours
  choisissable à la main) ;
- le **genre** (`H`/`F` côté écoute → `M`/`F` côté catalogues).

C'est le travail de `_appliquer_annotations_voix.py` :

    python test_voix/_appliquer_annotations_voix.py             -> APERCU, n'ecrit rien
    python test_voix/_appliquer_annotations_voix.py --ecrire     -> applique (copies datees)

Il écrit dans `main.py` (voix Edge) et `modules/tts.py` (Kokoro, Kyutai, XTTS,
**NeutTS et Pocket TTS**), **seulement** sur les lignes des voix annotées, et il
fait **avant** une **copie datée** de chaque fichier
(`.bak_avant_annotations_voix`) : c'est le retour arrière. Les autres critères
(âge, timbre, débit, accent, registre, rôle) et ta **remarque libre** restent
dans le fichier de notes, où le casting automatique les lit directement.

Le lanceur double-clic **`APPLIQUER_LES_NOTES_D_ECOUTE.bat`** enchaîne tout :
l'aperçu, la question « J'applique ? (O/N) », le report, puis le **contrôle du
pool** (`test_pool_casting.py`). **Relance le lecteur** (`START.bat`) après :
les catalogues sont lus au démarrage du lecteur.

---

## ✅ Les vérifications, sans rien allumer et sans rien payer

### Python (`python test_voix/nom_du_test.py`)

| Test | Ce qu'il vérifie |
|---|---|
| `test_annotations_voix.py` | annotations d'écoute : critères fixes, enregistrement, refus des valeurs inconnues (sauvegarde et restaure tes notes) |
| `test_attribution_criteres.py` | attribution des voix par critères : classement, rôles réservés, verrous, déterminisme |
| `test_cache_audio.py` | le **cache audio** (20/09/2026) : le compte (taille, quota, nombre de fichiers) et la **purge à la main** du bouton « 🧹 Vider le cache » — dans un **dossier temporaire**, jamais le vrai cache (il compare même le nombre de fichiers du vrai cache avant/après pour le prouver), une **écriture en cours** (`.tmp`) n'est jamais coupée, et le cache remarche après un vidage |
| `test_pwa_manifeste.py` | l'**application installable** (20/09/2026) : le manifeste annonce ce qu'il faut (`standalone`, `start_url`), **chaque icône déclarée EXISTE à la taille annoncée** (c'est ce qui manquait — Chrome refusait donc d'installer l'application), au moins une icône de 192 px et une de 512 px, une icône **maskable**, les liens de la page, et le service worker qui répond aux requêtes |
| `test_residus_html.py` | les **résidus de balises** dans le texte lu (20/09/2026) : le vrai cas du Tome 5 (« M class="textsuperscript">lle Danglars ») est **nettoyé** — la phrase redevient « laissons Mlle Danglars » —, et le **texte normal n'est jamais touché** (guillemets français, tirets de dialogue, apostrophes, égalités, chevrons, balises légitimes) |
| `test_borne_babil_xtts.py` | garde-fou anti-babil : bornes de génération du service XTTS |
| `test_rogner_babil_xtts.py` | coupure du babil isolé par un silence |
| `test_rogner_queue_xtts.py` | rognage du silence de queue XTTS (0,25 s) |
| `test_rogner_queue_kyutai.py` | rognage du silence de queue **Kyutai** (0,20 s, 23/09/2026) : la queue est ramenée à la marge quel que soit le silence d'origine, la parole et la tête ne sont jamais touchées, le format du WAV ne change pas, et le rognage est bien branché **avant** la mise en cache — **18 contrôles**, rien à allumer |
| `test_neutts_service.py` | service NeuTTS : découpage du texte, filet anti-dérive, silence de queue, découpage des références (leur texte est obligatoire), contrat avec le lecteur (port 8084, graine fixe, une seule génération à la fois) |
| `test_nettoyage_tts.py` | le **texte envoyé au moteur** : plus de point d'exclamation (il faisait monter la voix), **plus de point final après « M. » / « Mme »** (c'était le silence entendu), et les réglages précédents (point-virgule, parenthèses, deux-points) toujours en place — 18 contrôles, rien à allumer |
| `test_niveau_audio.py` | le **volume des phrases** : une phrase Kyutai trop faible est remontée au niveau des autres moteurs, une phrase déjà forte n'est pas touchée, aucune saturation, et un fichier illisible revient inchangé — 10 contrôles, rien à allumer |
| `test_decoupage_phrases.py` | le **découpage des phrases** : plus de coupe après « M. » / « Mme » (c'était le silence entendu), les vraies fins de phrase coupent toujours, les positions servent de base à la migration, aucun mot n'est perdu — et **la règle de la page est identique à celle du serveur** (19 contrôles, rien à allumer) |
| `test_ponctuation_incises.py` | les **4 ponctuations du « ! »** que le banc compare (et que « rien du tout » ne colle pas deux mots), et le **retrait des incises** : elles partent **en entier, complément compris**, le sujet de la phrase (« le jeune homme ») n'est jamais supprimé, et une phrase qui n'est que l'incise garde son texte (jamais vidée) — 29 contrôles, rien à allumer |
| `test_onglets.py` | les **onglets de lecture** (marque-pages, demande de Laurent 19/09/2026) : la table est créée, on pose un onglet et on le retrouve **avec son chapitre, sa position et son libellé**, chaque profil ne voit que les siens, on peut le retirer, et la liste est rangée dans l'ordre de lecture |
| `test_majuscules.py` | les mots **TOUT EN MAJUSCULES** : le vocabulaire du livre s'apprend (y compris « Jim » avec sa majuscule initiale), les mots connus repassent en casse normale (« DE » → « de », « BASTILLE » → « Bastille »), les **sigles** (« JFK », « FBI ») et les **chiffres romains** (« XIV ») ne sont jamais touchés, et sans vocabulaire rien ne change — **16 contrôles**, dont 4 sur le vrai 22/11/63 |
| `test_incise_seule.py` | les phrases qui **ne sont qu'une incise** (« dit Monte-Cristo. », isolées par le découpage au « ! » / « ? ») : elles sont détectées, une phrase normale ne l'est jamais, et le **court silence** joué à leur place est un WAV valide et vraiment muet — 15 contrôles, rien à allumer |
| `test_pool_casting.py` | ordre du pool automatique du casting |
| `test_ids_ecran.py` | chaque élément cherché par le code existe dans la page |
| `test_reparer_moteurs.py` | le **voyant « Réparer » et le veilleur Pocket TTS** (21/09/2026) : `START.bat` allume Pocket TTS **avant** le choix du moteur lourd (c'était LA cause de la panne — le bloc vivait après les « goto lecteur » de Kyutai, il n'était donc **jamais atteint**), **Pocket TTS est toujours attendu** (il cohabite) et XTTS non, le veilleur le **rallume** quand il le trouve éteint — en le **disant**, sans essais en rafale, et sans le relancer s'il charge encore —, le lancement **sans fenêtre** vise le bon script dans le bon dossier, les **deux routes** du panneau existent en POST, et l'auto-extinction du service est passée à **180 min** — **35 contrôles, rien à allumer** |
| `test_prononciation_kokoro.py` | la **prononciation française imposée** (21/09/2026) : la table de `modules/prononciation.py` remplace les mots que le phonémiseur prend pour de l'anglais (casse respectée, **mots entiers** seulement : « Andreas » n'est pas touché), l'apostrophe courbe redevient droite, et surtout la **mesure** qui protège la table — chaque graphie, donnée au phonémiseur, **ne bascule plus** en anglais alors que le mot d'origine **bascule**, sans quoi l'entrée ne sert à rien. Vérifie aussi que les **marques de langue** `(en)…(fr)` sont bien retirées par `_phonemes_kokoro`, et que « Andrea » préparé sonne **exactement** comme « Andréa » — **rien à allumer** (le phonémiseur seul est utilisé, pas le modèle) |
| `test_recaste_ia.py` | re-cast avec l'IA : cadre des voix proposées, prompt, lecture et validation de la réponse de l'IA, découpage des phrases — **sans appeler l'IA** |
| `test_import_main.py` | le serveur s'importe et expose ses routes |
| `test_requirements.py` | l'environnement correspond à `requirements.txt` |
| `test_pas_de_secrets.py` | rien de secret ni de personnel ne partirait avec un `git push` : clés d'API en clair, fichiers sensibles suivis, audio / EPUB / base SQLite, environnements Python des moteurs |
| `test_filtres_rendu.py` | le **tiroir des filtres du casting, vu à l'écran** (22/09/2026) : il reprend le **vrai** bloc de la fenêtre du casting et la **vraie** feuille de styles, remplit la liste avec **120 personnages** (c'est la liste LONGUE qui déclenchait la panne), puis mesure dans un navigateur que le tiroir ouvert garde une **hauteur utile** (au moins 240 px — il tombait à **5 px** avant la correction : le bouton « ⚙️ Filtres » semblait ne rien faire), qu'**aucune barre n'est écrasée**, que la liste garde de la place et que la fenêtre **ne déborde pas** de l'écran — **12 contrôles**. Playwright, rien d'autre |
| `test_tiroir_lecteur_rendu.py` | le **tiroir du menu du bas, vu à l'écran** (22/09/2026, demande de Laurent) : il reprend le **vrai** pied du lecteur et la **vraie** feuille de styles, puis mesure dans un navigateur — sur un téléphone de 360 px, tiroir replié, **aucun réglage n'est montré**, les **sept commandes de lecture tiennent sur une ligne**, la poignée est **large et fine**, et **rien ne déborde** ; tiroir ouvert, **tous les réglages sont là** et le texte **cède la place** (mesuré : 137 px de pied replié contre 249 px ouvert) ; sur ordinateur (1200 px), la **poignée disparaît** et les réglages restent, comme avant — **19 contrôles**. Il a besoin de **Playwright** (comme `test_couverture_mobile.py`), rien d'autre |
| `test_libelle_deux_lignes_rendu.py` | **peut-on forcer un saut de ligne dans un menu déroulant ?** (question de Laurent, 22/09/2026) : il mesure, dans un vrai navigateur, le libellé d'un choix. Résultat : celui qui porte un saut de ligne occupe la **même hauteur** qu'un autre — le saut est **aplati** ; et un libellé plus long que le menu se replie **tout seul**, mais sans qu'on choisisse où. **Deuxième partie** : la **liste de l'application** qui remplace ce menu fait bien, elle, **deux lignes** — fond `rgb(13, 13, 13)` (le thème, pas du blanc), 2e ligne **sous** la première et **alignée**, 2e ligne **en blanc** (demande de Laurent), et la voix portée par le personnage qui ressort (couleur d'accent + graisse). **Troisième partie** : l'**encart du casting** déplié sous un personnage — 240 px de haut au plus, **défilant** (20 lignes testées), fond du thème, et le **bouton de voix** qui coupe proprement un libellé trop long (ellipse) sans casser la ligne. **18 contrôles**, **Playwright** requis, rien d'autre |

### JavaScript (`node test_voix/nom_du_test.js`)

| Test | Ce qu'il vérifie |
|---|---|
| `test_criteres_voix.js` | les menus de critères de la page **et** ceux du serveur sont les mêmes — et depuis le 20/09/2026, **la rubrique est écrite devant chaque menu** (étiquettes exactes « Âge, Timbre, Débit, Accent, Registre, Rôle », étiquette et menu dans le **même groupe**, option vide = tiret, et une **rubrique inconnue** qui retombe sur son libellé complet — 25 contrôles) |
| `test_libelle_voix.js` | le **libellé d'une voix** dans les menus (demande de Laurent, 19/09/2026) : **symbole du genre** devant le prénom (♀️ / ♂️, **rien** si le genre est inconnu — jamais un genre faux —, sélecteur emoji compris), **icône du moteur** (☁️ Edge, 🎎 Kokoro, 🎶 Piper, ⚡ Kyutai, 🧬 XTTS v2, 🧪 NeuTTS — 20/09/2026), drapeau(s), âge, timbre — les drapeaux des voix Edge (elles n'en avaient aucun), le 2ᵉ drapeau des accents, les libellés exacts du serveur (« mûr », « très aigu ») |
| `test_etat_casting.js` | badges « à caster » / « voix partagée » — et depuis le 19/09/2026 : **avec qui** une voix est partagée, **quelles voix sont libres** (hors voix génériques et hors voix du narrateur) et **quelle hauteur** appliquer quand on partage (jamais une hauteur déjà prise) |
| `test_filtre_genre.js` | menus de voix (femmes / hommes) |
| `test_filtre_age_casting.js` | le **filtre par âge de la voix et par genre du personnage** dans le casting (21/09/2026, demande de Laurent : « Cliquer sur "jeune" n'affiche que les jeunes [...] Idéalement un filtre ; Homme / Femme et les 4 âges ») : l'âge est lu sur les **annotations d'écoute de la voix portée** (une voix jamais annotée ne passe **aucun** filtre d'âge — on ne devine pas), le genre sur la **fiche** ('H' et 'M' passent « Hommes », un genre vide ne passe ni l'un ni l'autre), les deux filtres **se combinent**, les cas tordus ne plantent pas — et la barre est bien **branchée** (les 4 âges sans « mûr », les 2 genres, le bouton actif mis en évidence, la remise à zéro à la fermeture) |
| `test_entete_casting.js` | l'**en-tête compact de la fenêtre du casting** (22/09/2026, demande de Laurent : « sur mobile le menu déroulant pour choisir les personnages et leurs voix est minuscule [...] souvent la modale sort de l'écran vers le bas ») : l'en-tête ne garde que **trois** commandes (recherche, Filtres, fermeture), le **tiroir** `#cast-tools` contient bien les quatre blocs de réglages et la liste des personnages reste **après** lui, les compteurs **restent visibles tiroir replié** (sinon une liste courte semblerait amputée), les **quatre âges** de voix et pas cinq (« Tous les âges » n'est pas une catégorie), les **fonctions pures** extraites du fichier réel (écran étroit/large, tiroir ouvert/replié, filtre de liste actif), la **hauteur en `dvh`** — la fenêtre ne peut plus sortir de l'écran —, la hauteur minimale de la liste, les pastilles d'état qui **défilent sur une ligne**, et les **noms cliquables placés avant l'explication** d'un partage — **45 contrôles, rien à allumer** |
| `test_recherche_casting.js` | la **recherche dans la fenêtre du casting** (20/09/2026, item du BACKLOG du 14/09/2026) : la frappe filtre **sans accents ni casse** (« EDMOND » = « Edmond », « jean luc » = « Jean-Luc »), un personnage trouvé **garde ses alias** et taper un **alias** fait remonter son personnage, l'**article initial n'est pas retiré** (taper « le » filtre, contrairement à la règle du serveur), le tiroir des **voix libres** est filtré par prénom et provenance, et la barre est bien **câblée** (champ, compteur, remise à zéro à la fermeture, croisement avec le filtre d'état) — **33 contrôles**, rien à allumer |
| `test_tiroir_voix_libres.js` | le **tiroir des voix libres**, le **dépliage des partages**, la modale **« Partager / Déplacer »** et l'**attribution d'une voix libre** (19/09/2026) : voix rangées par moteur, libellés écrits, ▶ d'écoute, tiroir vide qui dit *pourquoi*, badge qui se déplie **au tap**, **noms cliquables placés avant l'explication** et qui mènent à la fiche (défilement compris, 22/09/2026), recalcul après un changement de voix, choix Partager / Déplacer (hauteur annoncée, verrou respecté), bouton « Choisir » qui donne la voix au personnage |
| `test_voix_ecoutables.js` | voix d'un moteur éteint (jamais de substitution silencieuse) |
| `test_message_reseau.js` | message parlé quand le réseau tombe |
| `test_chargement_chapitre.js` | le **chargement d'un chapitre** : le chapitre est demandé avant que le lecteur ne change d'état, une panne passagère est retentée, un échec **ne fait plus sauter** le chapitre (phrases vidées, bouton « Réessayer »), et une pause sans signal n'explose plus — exécute le vrai code de la page, sans navigateur |
| `test_voix_phrase.js` | panneau « voix de cette phrase », l'**état de la voix choisie écrit sous le menu** (libre / portée par X / partagée — 19/09/2026) et la **porte vers le casting** (20/09/2026 : bouton caché pour la narration, panneau fermé avant l'ouverture, filtres remis à zéro, surlignage du personnage) — 34 contrôles |
| `test_bouton_moteur.js` | le **voyant « Réparer les moteurs de voix »** (21/09/2026) : son libellé selon l'état des moteurs — il ne parle **que des moteurs attendus**, donc un XTTS éteint volontairement ne le fait pas crier —, et surtout que l'**ancien bouton de CHANGEMENT de moteur a bien disparu** (c'est lui qui avait éteint Pocket TTS par erreur, et fait disparaître ses 18 voix du casting), avec le câblage des deux gestes (relancer les moteurs / redémarrer NIMM ePub, ce dernier **après confirmation**) |
| `test_cache_audio.js` | le **libellé du bouton « 🧹 Vider le cache »** (20/09/2026) : la taille lisible (604 Mo, 1,2 Go, 12 Ko — virgule française) et surtout qu'il n'affiche **jamais** « undefined » quand le serveur n'a pas encore répondu |
| `test_vitesse_personnage.js` | la **vitesse de chaque phrase** (20/09/2026) : une fiche **réglée** impose sa vitesse, un personnage **sans réglage** lit à **Normale** — le menu du bas est le réglage du **narrateur**, pas un réglage général —, la **narration** et les **petits rôles** (lus par le narrateur) suivent le **menu**, le **personnage réglé et le non réglé ne se contaminent pas**, la **voix et la hauteur** de la fiche passent toujours, et le **câblage** est vérifié dans `frontend/app.js` (l'ancien appel qui ignorait la fiche fait échouer le test) — **27 contrôles**, rien à allumer |

| `test_sauts_navigation.js` | les **trois niveaux de saut** de la barre (20/09/2026) : ⏮⏭ le **chapitre**, ⏪⏩ **`_PAS_PARAGRAPHES` paragraphes d'un coup** (le pas est **lu dans `frontend/app.js`**), ◀▶ **une phrase** — et surtout les **bords** : jamais au-delà du dernier paragraphe (un saut trop long y est ramené), jamais avant le début, et le pas de 1 redonne exactement l'ancien comportement |
| `test_lecteur_media.js` | le **lecteur intégré** et le **lecteur du système** (20/09/2026) : la barre de progression envoyée au téléphone est **bornée** (position hors bornes ramenée, durée jamais 0) et **un refus du système ne casse jamais la lecture** ; la **réserve « à bloc »** s'active quand la page passe en arrière-plan **pendant** une lecture (et pas hors lecture) ; les **7 boutons** du lecteur sont les télécommandes de la barre du bas, et c'est la **barre de progression** qui l'ouvre |
| `test_navigateur.js` | le **nom du navigateur** affiché par le bouton d'installation (20/09/2026) : Chrome, Firefox, Safari, Edge — et surtout que **Brave et Edge soient reconnus AVANT Chrome** (les deux se présentent comme « Chrome » dans leur chaîne), parce que cette mention sert justement quand quelque chose ne marche pas (une application installée n'a **aucune** barre d'adresse : rien d'autre ne dit dans quel navigateur on est) — et que le bouton ne s'affiche **pas** sur ordinateur |
| `test_collage_wav.js` | le **collage des phrases en un seul morceau** (20/09/2026) : lecture de l'en-tête WAV, **durée exacte**, fichier tronqué jamais lu au-delà de sa fin, en-tête du morceau collé annonçant la **bonne** taille totale, morceau collé qui se **relit** comme un WAV valide de la bonne durée, silence des pauses inséré, et **refus du collage** entre deux formats différents (le filet qui protège les voix Piper) |
| `test_pause_casque.js` | la **pause venue de l'extérieur** et le **bouton du casque** (20/09/2026) : une pause qu'Android déclenche sans nous (appel, autre application) remet l'application **en phase avec la réalité** (bouton et lecteur du système sur « Pause ») et **rend la main** ; notre **propre** pause n'est pas prise pour une interruption ; la **fin naturelle** d'un morceau non plus ; et l'écouteur est retiré après la fin |
| `test_narrateur_par_livre.js` | la **voix du narrateur appartient à chaque livre** (20/09/2026) : un livre sans voix enregistrée reçoit le **défaut et l'enregistre** (fini le narrateur qui « passait » d'un livre à l'autre), un livre avec SA voix la retrouve, une voix indisponible (moteur éteint) affiche un **message** au lieu d'être remplacée en silence — sans écraser le choix du livre, et jamais d'écriture sans livre ouvert (24 contrôles, rien à allumer) |
| `test_tiroir_lecteur.js` | le **tiroir du menu du bas** (22/09/2026, demande de Laurent) : la barre du lecteur ne garde que les **sept commandes de lecture**, tout le reste du menu se range sous la poignée. Il éprouve la **règle** (`_tiroirLecteurDoitEtreOuvert`, extraite du **vrai** `frontend/app.js` : replié sur téléphone, ouvert sur ordinateur, et **toujours le choix de Laurent** dès qu'il a touché la poignée), la **place de chaque commande** dans la page (les sept au-dessus de la poignée, tous les réglages en dessous), et le **branchement** (le clic, l'état à l'entrée dans le lecteur, le chevron retourné, la poignée masquée sur ordinateur) — **38 contrôles**, rien à allumer |

### Ceux qui demandent quelque chose d'allumé

Les scripts dont le nom parle de **moteur**, **kyutai**, **xtts**, **neutts**,
**bascule**, **local** ou **casting** attendent soit le serveur, soit un moteur de
voix : `test_bascule_moteur.py`, `test_kyutai_branchement.py`,
`test_neutts_bout_en_bout.py` (moteur NeuTTS allumé, port 8084 : stabilité
bit à bit, phrases courtes, phrase longue), `test_moteur_local.py`,
`test_nettoyage_xtts.py`, `test_pretraitement_tts.py`, `test_start_moteur.py`,
`test_voix_ecoutables.py`, `test_repli_local.py`… À lancer seulement si le
moteur concerné est allumé (sinon l'échec est normal).

**Deux exceptions** (21/09/2026), qui ne lancent rien et n'attendent rien — tout
est simulé ou lu dans les fichiers : `test_reparer_moteurs.py` et
`test_bouton_moteur.js`. On peut donc les lancer à tout moment.

---

## 🔧 Les outils de diagnostic (lecture seule, aucun risque)

La plupart sont préfixés `_` et datent d'une session d'atelier. Les plus utiles
aujourd'hui :

| Outil | Question à laquelle il répond |
|---|---|
| `_mesurer_phrases_courtes.py` | le moteur XTTS en marche : telle phrase sort-elle trop longue ? (avec le détail parole / silence) — **le moteur doit être allumé** |
| `_chercher_babil_cache.py` | quelles phrases d'un livre ont un audio anormalement long ? (`--purger` nettoie les fautives, `dossier` copie les fichiers à écouter) |
| `_tracer_phrase_cache.py` | pour UNE phrase : son texte exact, sa voix, son fichier de cache et sa durée réelle |
| `_inspecter_phrase_xtts.py` | ce que reçoit **vraiment** le moteur (découpage et nettoyage du service, caractère par caractère) |
| `_apercu_recaste_criteres.py` | ce que changerait un re-cast par critères, **sans rien écrire** |
| `_etat_annotations_voix.py` | bilan des annotations d'écoute : couverture, valeurs rares, valeurs jamais utilisées |
| `_etat_couvertures.py` | état des couvertures (base + disque : format, dimensions, fichiers manquants) |
| `_top_repliques_livre.py` | les personnages les plus bavards d'un livre (pour choisir quelles voix créer) |
| `_cout_casting.py` | coût d'un casting par livre et par jour, avec la formule de l'application |
| `_lister_backlog.py` | les items du BACKLOG encore à faire, par section |
| `_chercher_residus_html.py` | **du HTML dans le texte lu** : parcourt les livres de la bibliothèque avec le **vrai parseur** et signale tout résidu (balise, attribut orphelin, entité non décodée) — `--livre 16` pour un seul, `--html` pour voir la **balise d'origine** (c'est ce qui a permis de trouver la conversion cassée du Tome 5) |
| `_etat_casting_livre.py` | état d'un casting (verrouillés, petits rôles, voix prises) |
| `_rapprocher_neutts_xtts.py` | quelles voix NeuTTS correspondent à quelles voix déjà cataloguées (pour leur garder les mêmes prénoms et étoiles) |
| `_etat_familles_voix.py` | combien de personnages lisent avec chaque moteur (Edge, Kokoro, Kyutai, XTTS, NeuTTS, Piper), et combien sont verrouillés — lecture seule |
| `_controler_voix_kyutai.py` | **contrôle complet d'un casting** : les voix de la base existent-elles au catalogue **et** chez le moteur ? lesquelles demandent un **autre moteur** (elles resteraient muettes) ? combien de personnages **sans voix** ? — lecture seule, rien à allumer |
| `_controler_saga.py` | les personnages d'une **saga** (plusieurs tomes) gardent-ils la même voix d'un tome à l'autre ? (c'est ce qui fera tache à l'écoute) |
| `_diagnostic_neutts_phrase.py` | où le moteur NeuTTS va découper un chapitre (combien de morceaux par phrase, limite de chaque voix, guillemets et tirets reçus bruts, phrases courtes) — hors ligne, rien à allumer |
| `_banc_ecoute_neutts.py` | fabrique un lot d'écoute NeuTTS : de vraies phrases d'un livre, puis la même phrase avec/sans les signes de dialogue, des phrases courtes, une phrase longue d'un bloc puis coupée en deux (voir `LANCER_BANC_ECOUTE_NEUTTS.bat`) |
| `_banc_contexte_kyutai.py` | **la même phrase, avec et sans le contexte de la précédente** (idée de Laurent : envoyer la fin de la phrase d'avant, ne garder que l'audio de la phrase courante) : lot de 2× N fichiers à comparer à l'oreille |
| `_mesurer_pause_phrases.py` | combien de silence y a-t-il en tête et en queue de chaque phrase, moteur par moteur (mesure via le lecteur) |
| `_verifier_contexte_service.py` | contrôle de la **coupe du contexte glissant** : la phrase coupée fait-elle la longueur de la phrase seule ? (3 cas pièges, dont le saut de ligne) |
| `_diag_coupe_contexte.py` | montre la **structure exacte** de l'audio « contexte + phrase » : où sont les silences, où finit le contexte, où la coupe a été placée |
| `_essai_separateur.py` | **quelle ponctuation fait une pause franche — et toujours la même — entre le contexte et la phrase ?** (question de Laurent, 21/09/2026 : « il faudrait une ponctuation traitée toujours de la même façon, pour avoir un point fixe de secondes »). Mesure faite : **aucune ne donne une pause constante** — les points de suspension sont les plus réguliers (0,91 s ± 0,06) **quand le contexte finit proprement**, mais la pause tombe à 0,3 s selon la fin du contexte, et « ? » comme « ; » n'en font parfois **aucune** ; une **virgule dans le contexte** fabrique une pause de ~0,5 s qui peut être confondue avec le repère. **Conclusion mesurée : pas de point fixe possible** (voir BACKLOG) |
| `_generer_catalogue_neutts.py` | reconstruit `NEUTTS_VOICES` dans `modules/tts.py` à partir des extraits du moteur (rapport seul par défaut, `--ecrire` pour écrire) |
| `_basculer_voix_xtts_vers_neutts.py` | bascule les voix XTTS d'un livre vers leurs jumelles NeuTTS (mêmes prénoms) : rapport seul par défaut, `--ecrire` copie la base avant d'écrire |
| `_basculer_voix_kyutai_vers_neutts.py` | bascule les voix Kyutai vers leurs jumelles NeuTTS (mêmes extraits) ; refuse d'écrire si une voix n'existe pas chez le moteur : rapport seul par défaut, `--ecrire` copie la base avant d'écrire |
| `_basculer_voix_neutts_vers_kyutai.py` | **le sens inverse** (NeuTTS → Kyutai, décision du 17/09/2026) : transposition à l'identique, refus d'écrire s'il reste une voix sans jumelle |
| `_remplacer_voix_sans_jumelle.py` | pour les voix **sans** jumelle Kyutai : choisit une voix Kyutai **du même profil d'écoute** (les voix Kyutai ne sont pas annotées, mais leurs jumelles NeuTTS le sont) — rapport seul par défaut |
| `_heriter_annotations_xtts_vers_neutts.py` | recopie les annotations d'écoute des voix XTTS **et** Kokoro sur leurs jumelles NeuTTS (l'accent est remis à « neutre », voir l'en-tête) |
| `_heriter_annotations_neutts_vers_pocket.py` | recopie les annotations des voix **NeuTTS** sur leurs jumelles **Pocket TTS** (21/09/2026 — mêmes extraits, identifiants identiques : `neutts:Femme001` → `pocket:Femme001`) ; l'**accent** reste à vérifier à l'oreille, `pocket:JEAN_EDGAR` n'ayant aucune jumelle |
| `_importer_voix_pocket.py` | 🎒 **annote les voix Pocket TTS qui n'ont pas de jumelle** (23/09/2026 : le lot des 10 « nouveaux découpages »). Pour chaque voix `pocket:` du catalogue sans annotation, il vérifie que son WAV existe dans `pocket_tts_service\voix\`, puis écrit ses critères (timbre lu sur la hauteur mesurée dans le clone, débit `vif`, 3 étoiles) — **rapport seul par défaut**, `--ecrire` fait une copie datée et **n'écrase jamais** les annotations existantes. `pocket:JEAN_EDGAR` est **volontairement laissé de côté** (`LAISSEES_A_L_OREILLE`) : c'est l'oreille de Laurent qui doit le remplir |
| `_diag_retours_ecoute.py` | les **retours d'écoute de Laurent** (18/09/2026), en trois parties : quelles phrases du livre sont **coupées après une abréviation** (le silence après « M. » / « Mme »), le **niveau audio** des fichiers en cache par famille de moteur, et l'**effet de la normalisation** sur les phrases réelles — lecture seule, rien à allumer |
| `_mesurer_niveau.py` | le **niveau d'un fichier audio** (crête, niveau global, et surtout **niveau de la parole** : c'est lui qui dit si une voix est faible) — on peut lui donner autant de fichiers qu'on veut, WAV ou MP3 |
| `_analyse_extraits_dialogue.py` | **quelles voix ont un extrait de DIALOGUE et lesquelles une narration** : lit la transcription gardée de chaque extrait de référence (`neutts_service/references/*/references.csv`) et dit, famille par famille, lesquelles « lisent une histoire » au lieu de « parler » — lecture seule, rien à allumer (`--tout` montre le texte de chaque extrait) |
| `_migrer_index_phrases.py` | ⚠️ **écrit dans la base** avec `--ecrire` (copie la base avant) : remappe les index de phrases après la correction du découpage. **Sans argument : simulation** (rien n'est écrit). `--verifier` contrôle APRÈS coup que chaque voix pointe sur une phrase qui existe |
| `_migrer_phrases_abreviations.py` | ⚠️ **écrit dans la base** avec `--ecrire` (copie la base avant) : **même travail, mais pour les abréviations en capitales et « Mrs »** (21/09/2026). Il est **distinct** de l'outil ci-dessus, et c'est voulu : il compare la liste d'abréviations **privée des nouvelles formes** à l'état actuel, alors que l'autre compare l'ancienne règle du 18/09 — les confondre migrerait **deux fois**. **Sans argument : simulation** (le rapport dit combien de chapitres, combien de fusions, et quels cas ont des locuteurs mélangés) |
| `_migrer_index_dialogue.py` | 📐 **la migration des index pour le MODE DIALOGUE** (22/09/2026) : pour un livre déjà casté, il dit combien de morceaux la coupe sépare, combien de « beats » (le bout de narration qui annonce une réplique) passeraient au **narrateur** (`--variante B`, celle qui corrige) ou resteraient au personnage (`--variante A`), combien sont **laissés tranquilles** parce qu'ils sont dans une citation ouverte, et il **montre les morceaux à LIRE**. Il rappelle aussi ce qu'il ne touche **jamais** : les voix par personnage, les réglages, les verrous, les alias, la voix du narrateur — **seul le « qui parle » bouge**. **Sans `--ecrire` : SIMULATION, rien n'est écrit.** Avec `--ecrire` : copie datée de la base **avant**, contrôle **après** (chaque voix doit pointer sur une phrase qui existe). `--base <fichier>` permet de **répéter sur une copie** avant de toucher la vraie base. Usage : `--livre 28 --variante B` |
| `_montrer_attribution.py` | **qui parle, phrase par phrase, et avec quelle voix** dans un chapitre (`--livre 16 --chapitre 9`) : le locuteur, la voix attribuée (et sa vitesse), et le texte — lecture seule. Indispensable pour vérifier une phrase douteuse sans tout réécouter |
| `_mesurer_incises_supprimables.py` | combien de phrases contiennent une **incise de parole** (« , dit-il, »), de quel type, et **ce que ferait un code de suppression** : il essaie sur de vraies phrases et compte celles qu'il abîme (idée de Laurent, 18/09/2026) — lecture seule, rien à allumer |
| `_banc_ponctuation_exclamation.py` | fabrique le **lot d'écoute de la ponctuation du « ! »** (4 variantes) **et des incises** (gardées/retirées), sur les phrases réelles d'un livre : dossier `ecoute_ponctuation_<date>` avec les WAV numérotés, un index (ce qu'on demande), les textes exacts envoyés, et le lanceur d'écoute — **Kyutai allumé** (voir `LANCER_BANC_PONCTUATION.bat`) |
| `_banc_incises.py` | fabrique le **lot d'écoute des incises de parole** (22/09/2026) : **A = muette** / **B = dite par le narrateur**, par le **vrai chemin du lecteur** (requêtes à `/api/tts` avec le drapeau `incise_a_lire`, collage des morceaux comme la page). Dossier `ecoute_incises_<date>` (WAV + index + textes exacts + lanceur). Il **signale** quand deux moteurs ne se collent pas (formats différents) et quand le serveur en marche est trop ancien pour connaître le drapeau (voir `LANCER_BANC_INCISES.bat`) |
| `_mesurer_exclamations.py` | combien de « ! » sont des **interjections courtes** (pour régler le seuil), et combien d'**abréviations collées** à un prénom (Mlle suivi d'un espace insécable, comme dans le tome 5) — lecture seule, rien à allumer |
| `_diag_incises_reelles.py` | **pourquoi il reste des incises** : il sépare celles qui sont retirées, celles qui sont gardées **exprès** (non fermées), celles qui échappent par **verbe inconnu**, et les phrases qui ne sont **qu'une incise** (« demanda Morrel. ») — c'est l'outil qui a expliqué le « elles sont toujours présentes » du 18/09/2026 |
| `_mesurer_cas_tordus_20260919.py` | **combien de phrases tombent dans les cas tordus du 19/09/2026** (chapitre 96) : phrase qui n'est qu'une incise (silence joué), incise gardée à cause d'un **point-virgule** (« , dit le comte ; »), incise coupée sur une **civilité sans point** (« dit Mme Danglars »), **verbe + complément** avant le nom (« dit avec un sourire le comte »), et phrases de **8 caractères ou moins** (celles envoyées seules au moteur). Il **simule aussi le correctif** « le point-virgule ferme l'incise » **sans rien modifier** : combien de phrases il toucherait, combien perdraient tout leur texte, et des exemples avant / après — lecture seule, rien à allumer (`--livre 16`) |
| `_verifier_cas_test_adverse.py` | **les cas trouvés par le TEST ADVERSE**, passés dans le vrai code : chaque phrase proposée par un autre assistant (Claude.AI, Mistral…), avec le texte du livre, ce que le module en fait et ce que le moteur reçoit — c'est ce qui permet de trier le vrai du faux (18 cas sur 40 confirmés le 19/09/2026) — lecture seule, rien à allumer |
| `_mesurer_narration_abimee.py` | **les phrases de NARRATION abîmées par le retrait des incises** (croise la base `speaker_attribution` et `modules/incises.py`) : une phrase de récit ne devrait jamais être modifiée, or un verbe de parole employé comme verbe ordinaire (« , appela la femme de chambre, ») en fait disparaître une action — mesuré : **8 sur 1 344** dans le tome 5, dont une destructrice (`--livre 16`) |
| `_mesurer_majuscules_20260919.py` | **les mots TOUT EN MAJUSCULES** d'un livre (ou de tous : `--tous`), avec leur fréquence — et **l'idée qui les trie** : un mot écrit aussi en casse normale ailleurs dans le livre est un mot de la langue (« DE » et « de », « JIM » et « Jim ») → à mettre en minuscules ; un mot qui n'apparaît jamais autrement est un **sigle** (« JFK », « FBI ») → à ne pas toucher. Mesure : 22/11/63 a **531 phrases** touchées, 682 mots convertibles — lecture seule, rien à allumer |
| `_mesurer_vague1_20260919.py` | **combien de phrases sont concernées par la « vague 1 »** des défauts du test adverse : l'incise qui emporte la **relative** (« , dit Morrel, qui l'a voulu »), l'**impératif** pris pour une incise, et le **participe orphelin** (« dit Morrel, se levant ») — motifs simples, donc des ordres de grandeur à confirmer (`--livre 16`) |
| `_tester_tts_serveur.py` | ce que le **serveur** renvoie vraiment pour une phrase : il interroge le lecteur en marche (`POST /api/tts`, port 8081) et compare l'audio du texte **nettoyé** et du texte **d'origine** — le moyen le plus direct de savoir si un doute vient du nettoyage ou du **cache** (serveur allumé) |
| `_essai_garde_fou_start.py` | qui serait arrêté par le **garde-fou de `START.bat`** (les serveurs qui écoutent sur le port 8081), **sans rien arrêter** — utile pour vérifier que NIMM (port 8080) et le relais Tailscale ne sont jamais visés |
| `_mesurer_prononciation_kokoro.py` | **la prononciation des prénoms, mesurée et à écouter** (21/09/2026) : il écrit ce que le phonémiseur d'espeak-ng produit pour chaque mot de la table (tel quel, sans les marques, et avec la graphie française) dans `sortie_ecoute_prononciation/mesure_phonemes.txt`, puis génère un **lot d'écoute A/B** (`01_avant_Andrea.wav` / `01_apres_Andrea.wav`…) avec la vraie voix Kokoro — c'est ce lot qui tranche une graphie. Lanceur double-clic : `ECOUTER_PRONONCIATION.bat` (rien à allumer, rien de facturé) |
| `_ecouter_contexte_kyutai.py` | **le CONTEXTE GLISSANT de Kyutai, à écouter** (21/09/2026) : pour de vraies phrases d'un livre, il écrit **trois versions** à travers le vrai service — `01_seule.wav` (sans contexte), `02_3mots.wav` (le réglage d'aujourd'hui), `03_8mots.wav` (le réglage d'avant) — plus un index et un lanceur de dossier (voir `ecoute_contexte_<date>/`) : c'est ce lot qui dit si le contexte sert vraiment, et si un mot de la phrase précédente s'entend encore. **Kyutai allumé**. Usage : `--livre 28 --chapitre 10` |
| `_mesurer_contexte_mots.py` | la **même question, mais mesurée** (21/09/2026) : il compare la **durée de PAROLE** (et non la durée totale, qui bouge avec les respirations) de la phrase seule, avec 8, 3 et 2 mots de contexte, sur six cas dont ceux de Laurent (point-virgule, points de suspension, tiret de dialogue, guillemet fermant, phrase précédente longue). Il vérifie aussi que **le moteur est déterministe** — il ne l'est **pas**, et c'est ce qui explique que le défaut n'arrive que de temps en temps. Différence avec `_verifier_contexte_service.py` : celui-ci compare des **durées totales** sur quatre cas de contrôle, celui-là mesure la **parole** et fait varier la longueur du contexte |
| `_auditer_documentation.py` | **l'audit de la DOCUMENTATION contre le CODE** (22/09/2026, demande de Laurent) : il compare ce que disent `ARCHITECTURE.md`, le `BACKLOG.md`, les modes d'emploi et les mémos avec ce que dit **vraiment le code** — fichiers cités qui n'existent plus, identifiants de code (fonction, constante) qui n'existent plus, routes HTTP absentes de `main.py`, colonnes de table absentes de la base, tests disparus, et items du BACKLOG dont le sujet est déjà livré. Le « ! » devant une référence marque un document d'**état actuel** (les mémos sont des notes datées) ; `--tout` affiche toutes les alertes au lieu de 25 par section. **Section 7 (22/09/2026)** : il vérifie aussi que le **sommaire** de `ARCHITECTURE.md` correspond à ses vrais titres `##` (un sommaire faux envoie au mauvais endroit) et qu'aucune section ne dépasse **500 lignes** (une section géante rend le plan inutile). **Lecture seule**, rien à allumer, rien de facturé — et ses alertes sont à **LIRE** : certaines sont légitimes (une page qui raconte l'histoire d'un fichier disparu) |
| `_analyse_structure_architecture.py` | la **structure de `ARCHITECTURE.md`, mesurée** (racine du projet, **lecture seule**) : nombre de titres par niveau, taille de chaque section, ce qui est imbriqué sous la plus grosse, et les liens internes. C'est lui qui a prouvé, le 22/09/2026, qu'une seule section avalait **2 740 lignes = 61,5 % du document**. Usage : `python _analyse_structure_architecture.py` |
| `_verifier_faits_architecture.py` | **les FAITS de `ARCHITECTURE.md` contre le code** (racine du projet, **lecture seule**, 22/09/2026) : il répond à la question de Laurent « est-ce que ce qui est écrit reflète vraiment l'état du code ? ». L'audit `_auditer_documentation.py` vérifie les **NOMS** (le fichier cité existe, la fonction citée existe) ; celui-ci vérifie les **PHRASES** : le **plan du dossier** (chaque entrée existe-t-elle encore à cet endroit, et qu'oublie-t-il ?), les **constantes citées avec leur valeur**, les **ports** des moteurs, les **fichiers de données**, la **version de cache** de la page. Chaque fait est écrit en clair dans le script, avec sa façon d'être vérifié — pas de devinette. Il a trouvé, le 22/09/2026 : un plan du dossier vieux de plusieurs sessions (5 modules sur 12 absents, le manifeste PWA déplacé dans `frontend/`, 4 dossiers oubliés). Le **23/09/2026**, il a trouvé une dérive que personne n'avait vue : la **pause entre paragraphes** annoncée à `0` alors que le code portait `300` depuis le 17/09/2026 — cette valeur est désormais **contrôlée** par lui (section 4). Le même soir, il a trouvé une **seconde** dérive invisible, dans le sujet `frontend/ — Interface` : celui-ci annonçait **deux** vues alors que la page en porte **quatre** (le choix du profil et le mode RSVP) — c'est la **section 10**, et sa preuve s'affiche avec `_essais/_preuve_controle_vues.py`. Le **23/09/2026** encore, il a trouvé une **troisième** dérive, dans le sujet « Moteur de voix Pocket TTS » : celui-ci annonçait **100 M de paramètres** — le chiffre des variantes légères de Pocket TTS — alors que le modèle français `french_24l` que le projet utilise en porte **336 M** (comptés dans l'en-tête du fichier de poids, 641 Mo) ; c'est la **section 11**, sa mesure s'affiche avec `_essais/_mesurer_faits_pocket.py` et sa preuve avec `_essais/_preuve_controle_pocket.py`. Et le **23/09/2026** (nuit), une **quatrième** dérive, dans le sujet « Report des notes d'écoute » : il parlait encore des **trois** boutons de la barre d'état du casting, alors que le **quatrième** (« 🔓 Voix libres ») est arrivé le 19/09/2026 — le test, lui, vérifiait déjà les quatre ; le même sujet portait trois chiffres périmés (176 personnages et non 175, **3 615** répliques pour Jake Epping et non 3 634, et une famille de voix partagée qui en porte **3** et non « dix-huit »). C'est la **section 12**, sa mesure s'affiche avec `_essais/_mesurer_faits_notes.py` et sa preuve avec `_essais/_preuve_controle_notes.py`. Et le **23/09/2026** (fin de soirée), une **cinquième** dérive — la plus grosse des cinq —, dans le sujet « Distribution de voix par personnage (IA) » : le document annonçait **DeepSeek par défaut** alors que c'est **Gemini** depuis le 23/08/2026 (le sujet voisin « Système multi-moteur » disait déjà l'inverse : les deux se contredisaient dans le même document), il ignorait le **modèle local** (Ollama, 13/09/2026) — **absent de tout le document** —, **une** seule route là où le code en porte **onze**, une table `voices` de **quatre** colonnes (**huit** aujourd'hui) et des attributs `data-voice` / `data-pitch` qui n'existent **nulle part** dans la page (la voix d'une phrase se décide **à la lecture**). C'est la **section 13**, et sa preuve s'affiche avec `_essais/_preuve_controle_casting.py` : elle crie **17 fois** sur la copie d'avant la session. Et le **23/09/2026** (fin de soirée), une **sixième** dérive, dans le sujet « Rognage des silences de bord » : il annonçait « ~0,15 s » de silence de queue pour Edge alors que `modules/audio_trim.py` porte **0,35 s** depuis le 17/09/2026, « **12 contrôles** » pour `test_rogner_babil_xtts.py` (il en exécute **11**), ignorait le rognage de **NeuTTS** (16/09/2026) comme la respiration de **Kyutai** (**0** par défaut), et attribuait au rognage une **clé de cache** qui porte en réalité la `VERSION_CACHE` du prétraitement. C'est la **section 16**, sa mesure s'affiche avec `_essais/_mesurer_faits_rognage.py` et sa preuve avec `_essais/_preuve_controle_rognage.py` (**17** écarts sur la copie d'avant, **0** sur le document d'aujourd'hui). Usage : `python _verifier_faits_architecture.py` |
| `_regrouper_architecture.py` | **le rangement de `ARCHITECTURE.md` en parties** (racine du projet, 22/09/2026) : il range les 61 sujets en **10 parties** thématiques (projet, serveur, page, texte lu, casting, voix, moteurs, mode dialogue, écoute, historique). **Aucun titre n'est renommé** (donc les renvois des autres documents continuent de fonctionner), et il **prouve** que le contenu de chaque sujet est identique au caractère près. Il refuse d'écrire si un sujet n'est pas rangé ou l'est deux fois, et **refuse de tourner deux fois**. Copie datée automatique. `--ecrire` pour appliquer |
| `_corriger_separateurs_architecture.py` | **les séparateurs `---` en double** (racine du projet, 22/09/2026, **lecture seule sans option**) : artefact laissé par le regroupement (l'ancien bloc finissait par son propre `---`, et le regroupement en ajoute un). Il remplace `---` / vide / `---` / vide par un seul séparateur, et **prouve** que le contenu est identique au caractère près (mêmes lignes non vides, moins exactement 3 séparateurs). `--ecrire` pour appliquer |
| `_demenager_pistes_architecture.py` | **le déménagement des idées de travail** (racine du projet, 22/09/2026) : il a retiré d'`ARCHITECTURE.md` les pistes du 21/08 déjà recopiées dans le `BACKLOG.md` et quatre notes périmées (l'état Git de ce soir-là, le compte de voix « 66 entrées », « Nettoyage de `test_voix/` », le profil Nadia qui était du déjà livré), remplacées par un renvoi court. Deux signatures de lignes sont vérifiées avant écriture : il refuse de tourner sur un fichier qui a bougé, ou deux fois. Copie datée automatique |
| `_restructurer_architecture.py` | **la réparation des TITRES de `ARCHITECTURE.md`** (racine du projet, 22/09/2026, décision de Laurent : « que ce document TE soit utile […] pratique à lire pour TOI ») : il a remis au bon niveau les 34 `###` qui étaient des **sujets à part** imbriqués sous « Profils familiaux », transformé en titres les 8 sujets écrits en gras, et **inséré un sommaire calculé**. Il ne touche à **aucune ligne de contenu** : il tient la comptabilité des lignes une par une et **refuse d'écrire** si le compte ne tombe pas juste. `--ecrire` pour appliquer ; sans option, un **aperçu**. Il **refuse de tourner deux fois** |
| `_mesurer_pocket_defauts.py` | les **deux défauts signalés à l'oreille sur Pocket TTS** (21/09/2026 : « volume qui diminue si le paragraphe est très long » et « débuts de mots mangés »), **mesurés phrase par phrase** comme le fait la lecture : niveau de **parole** de chaque phrase d'un long paragraphe (1115 caractères de 22/11/63) + niveau d'**attaque** comparé à celui de la même phrase, **avec Kyutai en témoin**. Résultat : Pocket est **stable** (−1,1 dB), c'est **Kyutai** qui décroche (−10 dB sur une phrase) — et les débuts écrasés existent sur **les deux** |
| `_etat_migration_dialogue.py` | **qui doit passer en mode dialogue, en une page** (23/09/2026) : il sépare les livres **à migrer** (castés, encore en découpage d'origine), ceux **déjà en mode dialogue** (interdits à la migration) et ceux **pas castés** (rien à migrer), avec le nombre de phrases, de chapitres et de personnages — lecture seule, rien à allumer |
| `_simuler_migration_dialogue.py` | **la migration mesurée sur TOUS les livres d'un coup** (23/09/2026) : il enchaîne l'outil de référence livre par livre (un gros livre peut prendre plusieurs minutes, donc on le lance en tâche de fond), range un rapport détaillé par livre dans le dossier `_essais` et en écrit un **résumé**. **Il n'écrit JAMAIS dans la base** (`--ecrire` n'est pas transmis) : c'est la mesure à lire avant d'appliquer. `--livres 34 18` pour n'en prendre que quelques-uns |
| `_restaurer_hors_replique.py` | 🚑 **rendre à leur personnage les morceaux qui sont DANS une réplique en tiret** (23/09/2026, note urgente de Claude) : `_beat()` refuse un morceau qui contient `«`, mais une **réplique en tiret** n'en contient pas — elle a donc été prise pour un beat et remise au narrateur (**53** morceaux mesurés, dont **39** par le rattrapage du même jour). L'outil **restaure l'étiquette d'origine** de la copie `bak_avant_dialogue_20260922_1311` (l'index se remappe 1:1 : c'est une restauration, pas un casting), avec **copie datée avant** et **contrôle après**. Simulation par défaut ; `--livres`, `--ecrire`, `--exemples` |
| `_mesurer_casting_erreurs.py` | 🧪 **le casting IA rate-t-il beaucoup ?** (23/09/2026) : mesure **gratuite** des erreurs sur 4 chapitres difficiles, séparées en **dures** (réplique au narrateur, locuteur hors casting), **discutables** (incise seule chez un personnage) et **à lire** (dialogue continu — surtout pas un compte : dans un entretien ou un récit à la 1ʳᵉ personne, c'est normal). Résultat du 23/09 : **68 erreurs dures sur 4 481 phrases (1,52 %)**, dont **60 dans un seul chapitre** — le long mémoire de *Notre-Dame*, ch. 55, qui est le vrai cas à instruire. Lanceur : `MESURER_LE_CASTING.bat` |
| `_etat_des_livres.py` | 📊 **le tableau de bord des livres, en une page** (23/09/2026, demande de Laurent : « je ne sais pas trop où on en est ») : pour chaque livre, le nombre de phrases attribuées, le **mode de découpage** (origine / dialogue), la **part de narration**, le nombre de personnages et de **gros locuteurs** (plus de 15 % — c'est le critère du futur réglage « roman / entretien »), les **incises** (muettes ou lues) et les **locuteurs hors casting** à revoir — lecture seule |
| `_corriger_locuteur.py` | 🎧 **changer le locuteur d'UN morceau précis** (23/09/2026, retour d'écoute) : on cherche par **extrait de texte** (`--livre 34 --texte "Ah bah"`), l'outil affiche le morceau et **qui le lit aujourd'hui**, puis `--locuteur <nom du casting> --ecrire` corrige — avec **copie datée de la base avant** et relecture après. Il **refuse** si l'extrait désigne plusieurs morceaux, ou si le personnage n'est pas au casting. Lanceur double-clic : `CORRIGER_UN_MORCEAU.bat` |
| `_rattraper_beats_derive.py` | 🔧 **le rattrapage des beats perdus par la dérive du compteur** (23/09/2026) : la migration des livres déjà castés avait compté les guillemets par **chapitre** au lieu du **paragraphe**, ce qui laissait à des personnages **244 morceaux de narration** (« Elle arrêtait les passants et criait : »). Cet outil les remet au narrateur sur les livres **déjà migrés** (8, 14, 15, 16, 17, 27, 28, 33, 34, 35) — **155 morceaux écrits le 23/09** — en laissant de côté, exprès, les morceaux qui portent une **2ᵉ personne** (« je vous dirais : » du docteur d'Avrigny : c'est du discours de personnage) et les **impurs** de la règle R3 (session à venir). Simulation par défaut ; `--ecrire` fait une **copie datée de la base** avant et **contrôle après** (index dans les bornes, locuteurs au casting, plus rien à corriger). Options : `--livres`, `--avec-personne`, `--avec-impurs`, `--exemples` |

Usage : `python test_voix/_nom_de_l_outil.py` (certains attendent un numéro de
livre ou un chapitre : le mode d'emploi est en tête de chaque fichier).

---

## 📄 Les données : à NE PAS supprimer

- `cles_api.txt` — tes clés d'API (**hors Git**, jamais publié) ;
- `chapitre_test.txt` — le chapitre de référence pour les comparaisons ;
- `resultat_*.json` / `resultat_*.txt` — les sorties de comparaisons de modèles
  (12-13/09/2026), utiles comme traces ;
- `*.wav` — des extraits d'écoute (comparaisons de voix, branchements) ;
- `ecoute_babil/` — les 3 fichiers où le babil XTTS a été constaté (16/09/2026) ;
- les `*.log` des tests longs (traces de ce qui s'est passé).

---

## Comment lire un test

- `TOUT EST OK` → tout va bien, rien à faire ;
- `N VERIFICATION(S) EN ECHEC` → quelque chose a bougé : **le texte au-dessus
  dit quoi**. Les tests sont écrits pour qu'un échec soit explicite (ils
  refusent souvent de deviner) ;
- code de sortie `0` = succès, `1` = échec, `2` = refus volontaire (garde-fou,
  par exemple le script payant sans `--je-paie`).

_Ajouter un test ?_ Regarde un test existant du même genre : les noms sont
explicites, la sortie est en français, et un test qui touche à tes données
(annotations, casting) **sauvegarde puis restaure** ce qu'il a modifié.
