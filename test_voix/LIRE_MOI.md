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
| `ECOUTER_PRONONCIATION.bat` | le **lot d'écoute de la prononciation des prénoms** (21/09/2026) : pour chaque prénom, ce que Kokoro dit **avant** et **après** le correctif — c'est ton oreille qui valide la graphie |
| `LANCER_BANC_ECOUTE_XTTS.bat` | fabrique un **lot d'écoute XTTS** (qualité des phrases : attaque, incise, tiret, phrase courte, fin de phrase) sur deux voix |
| `LANCER_BANC_PONCTUATION.bat` | fabrique un **lot d'écoute sur la ponctuation du « ! »** (point / virgule / suspension / rien) **et sur les incises** (gardées ou retirées), sur les mêmes phrases réelles d'un livre — **Kyutai allumé**. Tu écoutes et tu classes, je règle ensuite |
| `LANCER_OU_SONT_MES_VOIX.bat` | affiche **où en sont tes voix** : combien de personnages lisent avec chaque moteur, combien sont verrouillés, et si chaque voix attribuée existe bien dans le catalogue (rien n'est modifié) |
| `MIGRER_PETITS_ROLES.bat` | 🎭 **donne Jessica (femmes) et Pierre (hommes) à tous les petits rôles** (moins de 8 répliques) des livres **déjà castés** (21/09/2026) : il montre d'abord ce qu'il ferait (essai), puis, si tu réponds **O**, il applique — avec **copie datée de la base avant d'écrire** |
| `MODE_DIALOGUE.bat` | ✂️ **sépare la narration des répliques, LIVRE PAR LIVRE** (21/09/2026) : dans « Richie est intervenu : «Non…» », le beat revient au narrateur et la réplique au personnage. Il affiche la liste des livres, puis demande le numéro et **A** (activer) ou **D** (revenir au découpage d'origine). Attention : un livre **déjà casté** doit être **re-casté** après, car les numéros de phrases changent |
| `LANCER_BANC_ECOUTE_NEUTTS.bat` | fabrique un **lot d'écoute NeuTTS** (livre et chapitre au choix) pour comprendre où la voix dérape : vraies phrases du livre, signes de dialogue avec/sans, phrases courtes, phrase longue d'un bloc puis coupée en deux — **le moteur NeuTTS doit être allumé** |
| `LANCER_BANC_ECOUTE_KYUTAI.bat` | le **même lot sur Kyutai** (mêmes phrases, mêmes voix : les deux moteurs partagent les mêmes extraits) pour **comparer** les deux — **Kyutai allumé, NeuTTS éteint** (ils ne cohabitent pas sur la carte graphique) |
| `_PAYANT_lancer_test_attribution.bat` | ⚠️ **payant** : appelle de vraies API d'IA — il demande confirmation avant de partir |

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
| `test_reparer_moteurs.py` | le **voyant « Réparer » et le veilleur Pocket TTS** (21/09/2026) : `START.bat` allume Pocket TTS **avant** le choix du moteur lourd (c'était LA cause de la panne — le bloc vivait après les « goto lecteur » de Kyutai, il n'était donc **jamais atteint**), **Pocket TTS est toujours attendu** (il cohabite) et XTTS non, le veilleur le **rallume** quand il le trouve éteint — en le **disant**, sans essais en rafale, et sans le relancer s'il charge encore —, le lancement **sans fenêtre** vise le bon script dans le bon dossier, les **deux routes** du panneau existent en POST, et l'auto-extinction du service est passée à **180 min** — **30 contrôles, rien à allumer** |
| `test_prononciation_kokoro.py` | la **prononciation française imposée** (21/09/2026) : la table de `modules/prononciation.py` remplace les mots que le phonémiseur prend pour de l'anglais (casse respectée, **mots entiers** seulement : « Andreas » n'est pas touché), l'apostrophe courbe redevient droite, et surtout la **mesure** qui protège la table — chaque graphie, donnée au phonémiseur, **ne bascule plus** en anglais alors que le mot d'origine **bascule**, sans quoi l'entrée ne sert à rien. Vérifie aussi que les **marques de langue** `(en)…(fr)` sont bien retirées par `_phonemes_kokoro`, et que « Andrea » préparé sonne **exactement** comme « Andréa » — **rien à allumer** (le phonémiseur seul est utilisé, pas le modèle) |
| `test_recaste_ia.py` | re-cast avec l'IA : cadre des voix proposées, prompt, lecture et validation de la réponse de l'IA, découpage des phrases — **sans appeler l'IA** |
| `test_import_main.py` | le serveur s'importe et expose ses routes |
| `test_requirements.py` | l'environnement correspond à `requirements.txt` |
| `test_pas_de_secrets.py` | rien de secret ni de personnel ne partirait avec un `git push` : clés d'API en clair, fichiers sensibles suivis, audio / EPUB / base SQLite, environnements Python des moteurs |
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
| `_diag_retours_ecoute.py` | les **retours d'écoute de Laurent** (18/09/2026), en trois parties : quelles phrases du livre sont **coupées après une abréviation** (le silence après « M. » / « Mme »), le **niveau audio** des fichiers en cache par famille de moteur, et l'**effet de la normalisation** sur les phrases réelles — lecture seule, rien à allumer |
| `_mesurer_niveau.py` | le **niveau d'un fichier audio** (crête, niveau global, et surtout **niveau de la parole** : c'est lui qui dit si une voix est faible) — on peut lui donner autant de fichiers qu'on veut, WAV ou MP3 |
| `_analyse_extraits_dialogue.py` | **quelles voix ont un extrait de DIALOGUE et lesquelles une narration** : lit la transcription gardée de chaque extrait de référence (`neutts_service/references/*/references.csv`) et dit, famille par famille, lesquelles « lisent une histoire » au lieu de « parler » — lecture seule, rien à allumer (`--tout` montre le texte de chaque extrait) |
| `_migrer_index_phrases.py` | ⚠️ **écrit dans la base** avec `--ecrire` (copie la base avant) : remappe les index de phrases après la correction du découpage. **Sans argument : simulation** (rien n'est écrit). `--verifier` contrôle APRÈS coup que chaque voix pointe sur une phrase qui existe |
| `_migrer_phrases_abreviations.py` | ⚠️ **écrit dans la base** avec `--ecrire` (copie la base avant) : **même travail, mais pour les abréviations en capitales et « Mrs »** (21/09/2026). Il est **distinct** de l'outil ci-dessus, et c'est voulu : il compare la liste d'abréviations **privée des nouvelles formes** à l'état actuel, alors que l'autre compare l'ancienne règle du 18/09 — les confondre migrerait **deux fois**. **Sans argument : simulation** (le rapport dit combien de chapitres, combien de fusions, et quels cas ont des locuteurs mélangés) |
| `_montrer_attribution.py` | **qui parle, phrase par phrase, et avec quelle voix** dans un chapitre (`--livre 16 --chapitre 9`) : le locuteur, la voix attribuée (et sa vitesse), et le texte — lecture seule. Indispensable pour vérifier une phrase douteuse sans tout réécouter |
| `_mesurer_incises_supprimables.py` | combien de phrases contiennent une **incise de parole** (« , dit-il, »), de quel type, et **ce que ferait un code de suppression** : il essaie sur de vraies phrases et compte celles qu'il abîme (idée de Laurent, 18/09/2026) — lecture seule, rien à allumer |
| `_banc_ponctuation_exclamation.py` | fabrique le **lot d'écoute de la ponctuation du « ! »** (4 variantes) **et des incises** (gardées/retirées), sur les phrases réelles d'un livre : dossier `ecoute_ponctuation_<date>` avec les WAV numérotés, un index (ce qu'on demande), les textes exacts envoyés, et le lanceur d'écoute — **Kyutai allumé** (voir `LANCER_BANC_PONCTUATION.bat`) |
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
| `_mesurer_pocket_defauts.py` | les **deux défauts signalés à l'oreille sur Pocket TTS** (21/09/2026 : « volume qui diminue si le paragraphe est très long » et « débuts de mots mangés »), **mesurés phrase par phrase** comme le fait la lecture : niveau de **parole** de chaque phrase d'un long paragraphe (1115 caractères de 22/11/63) + niveau d'**attaque** comparé à celui de la même phrase, **avec Kyutai en témoin**. Résultat : Pocket est **stable** (−1,1 dB), c'est **Kyutai** qui décroche (−10 dB sur une phrase) — et les débuts écrasés existent sur **les deux** |

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
