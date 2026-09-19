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
| `LANCER_BANC_ECOUTE_XTTS.bat` | fabrique un **lot d'écoute XTTS** (qualité des phrases : attaque, incise, tiret, phrase courte, fin de phrase) sur deux voix |
| `LANCER_BANC_PONCTUATION.bat` | fabrique un **lot d'écoute sur la ponctuation du « ! »** (point / virgule / suspension / rien) **et sur les incises** (gardées ou retirées), sur les mêmes phrases réelles d'un livre — **Kyutai allumé**. Tu écoutes et tu classes, je règle ensuite |
| `LANCER_OU_SONT_MES_VOIX.bat` | affiche **où en sont tes voix** : combien de personnages lisent avec chaque moteur, combien sont verrouillés, et si chaque voix attribuée existe bien dans le catalogue (rien n'est modifié) |
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

## ✅ Les vérifications, sans rien allumer et sans rien payer

### Python (`python test_voix/nom_du_test.py`)

| Test | Ce qu'il vérifie |
|---|---|
| `test_annotations_voix.py` | annotations d'écoute : critères fixes, enregistrement, refus des valeurs inconnues (sauvegarde et restaure tes notes) |
| `test_attribution_criteres.py` | attribution des voix par critères : classement, rôles réservés, verrous, déterminisme |
| `test_borne_babil_xtts.py` | garde-fou anti-babil : bornes de génération du service XTTS |
| `test_rogner_babil_xtts.py` | coupure du babil isolé par un silence |
| `test_rogner_queue_xtts.py` | rognage du silence de queue XTTS (0,25 s) |
| `test_neutts_service.py` | service NeuTTS : découpage du texte, filet anti-dérive, silence de queue, découpage des références (leur texte est obligatoire), contrat avec le lecteur (port 8084, graine fixe, une seule génération à la fois) |
| `test_nettoyage_tts.py` | le **texte envoyé au moteur** : plus de point d'exclamation (il faisait monter la voix), **plus de point final après « M. » / « Mme »** (c'était le silence entendu), et les réglages précédents (point-virgule, parenthèses, deux-points) toujours en place — 18 contrôles, rien à allumer |
| `test_niveau_audio.py` | le **volume des phrases** : une phrase Kyutai trop faible est remontée au niveau des autres moteurs, une phrase déjà forte n'est pas touchée, aucune saturation, et un fichier illisible revient inchangé — 10 contrôles, rien à allumer |
| `test_decoupage_phrases.py` | le **découpage des phrases** : plus de coupe après « M. » / « Mme » (c'était le silence entendu), les vraies fins de phrase coupent toujours, les positions servent de base à la migration, aucun mot n'est perdu — et **la règle de la page est identique à celle du serveur** (19 contrôles, rien à allumer) |
| `test_ponctuation_incises.py` | les **4 ponctuations du « ! »** que le banc compare (et que « rien du tout » ne colle pas deux mots), et le **retrait des incises** : elles partent **en entier, complément compris**, le sujet de la phrase (« le jeune homme ») n'est jamais supprimé, et une phrase qui n'est que l'incise garde son texte (jamais vidée) — 29 contrôles, rien à allumer |
| `test_incise_seule.py` | les phrases qui **ne sont qu'une incise** (« dit Monte-Cristo. », isolées par le découpage au « ! » / « ? ») : elles sont détectées, une phrase normale ne l'est jamais, et le **court silence** joué à leur place est un WAV valide et vraiment muet — 15 contrôles, rien à allumer |
| `test_pool_casting.py` | ordre du pool automatique du casting |
| `test_ids_ecran.py` | chaque élément cherché par le code existe dans la page |
| `test_recaste_ia.py` | re-cast avec l'IA : cadre des voix proposées, prompt, lecture et validation de la réponse de l'IA, découpage des phrases — **sans appeler l'IA** |
| `test_import_main.py` | le serveur s'importe et expose ses routes |
| `test_requirements.py` | l'environnement correspond à `requirements.txt` |
| `test_pas_de_secrets.py` | rien de secret ni de personnel ne partirait avec un `git push` : clés d'API en clair, fichiers sensibles suivis, audio / EPUB / base SQLite, environnements Python des moteurs |

### JavaScript (`node test_voix/nom_du_test.js`)

| Test | Ce qu'il vérifie |
|---|---|
| `test_criteres_voix.js` | les menus de critères de la page **et** ceux du serveur sont les mêmes |
| `test_libelle_voix.js` | le **libellé d'une voix** dans les menus (demande de Laurent, 19/09/2026) : drapeau(s), âge, timbre et moteur — les drapeaux des voix Edge (elles n'en avaient aucun), le 2ᵉ drapeau des accents, les libellés exacts du serveur (« mûr », « très aigu ») |
| `test_etat_casting.js` | badges « à caster » / « voix partagée » |
| `test_filtre_genre.js` | menus de voix (femmes / hommes) |
| `test_voix_ecoutables.js` | voix d'un moteur éteint (jamais de substitution silencieuse) |
| `test_message_reseau.js` | message parlé quand le réseau tombe |
| `test_chargement_chapitre.js` | le **chargement d'un chapitre** : le chapitre est demandé avant que le lecteur ne change d'état, une panne passagère est retentée, un échec **ne fait plus sauter** le chapitre (phrases vidées, bouton « Réessayer »), et une pause sans signal n'explose plus — exécute le vrai code de la page, sans navigateur |
| `test_voix_phrase.js` | panneau « voix de cette phrase » |
| `test_bouton_moteur.js` | bouton de bascule des moteurs de voix |

### Ceux qui demandent quelque chose d'allumé

Les scripts dont le nom parle de **moteur**, **kyutai**, **xtts**, **neutts**,
**bascule**, **local** ou **casting** attendent soit le serveur, soit un moteur de
voix : `test_bascule_moteur.py`, `test_kyutai_branchement.py`,
`test_neutts_bout_en_bout.py` (moteur NeuTTS allumé, port 8084 : stabilité
bit à bit, phrases courtes, phrase longue), `test_moteur_local.py`,
`test_nettoyage_xtts.py`, `test_pretraitement_tts.py`, `test_start_moteur.py`,
`test_voix_ecoutables.py`, `test_repli_local.py`… À lancer seulement si le
moteur concerné est allumé (sinon l'échec est normal).

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
| `_essai_separateur.py` | quel **séparateur** entre contexte et phrase force une pause détectable (c'est ce qui a montré que les points de suspension la créent, ~1,2 s) |
| `_generer_catalogue_neutts.py` | reconstruit `NEUTTS_VOICES` dans `modules/tts.py` à partir des extraits du moteur (rapport seul par défaut, `--ecrire` pour écrire) |
| `_basculer_voix_xtts_vers_neutts.py` | bascule les voix XTTS d'un livre vers leurs jumelles NeuTTS (mêmes prénoms) : rapport seul par défaut, `--ecrire` copie la base avant d'écrire |
| `_basculer_voix_kyutai_vers_neutts.py` | bascule les voix Kyutai vers leurs jumelles NeuTTS (mêmes extraits) ; refuse d'écrire si une voix n'existe pas chez le moteur : rapport seul par défaut, `--ecrire` copie la base avant d'écrire |
| `_basculer_voix_neutts_vers_kyutai.py` | **le sens inverse** (NeuTTS → Kyutai, décision du 17/09/2026) : transposition à l'identique, refus d'écrire s'il reste une voix sans jumelle |
| `_remplacer_voix_sans_jumelle.py` | pour les voix **sans** jumelle Kyutai : choisit une voix Kyutai **du même profil d'écoute** (les voix Kyutai ne sont pas annotées, mais leurs jumelles NeuTTS le sont) — rapport seul par défaut |
| `_heriter_annotations_xtts_vers_neutts.py` | recopie les annotations d'écoute des voix XTTS **et** Kokoro sur leurs jumelles NeuTTS (l'accent est remis à « neutre », voir l'en-tête) |
| `_diag_retours_ecoute.py` | les **retours d'écoute de Laurent** (18/09/2026), en trois parties : quelles phrases du livre sont **coupées après une abréviation** (le silence après « M. » / « Mme »), le **niveau audio** des fichiers en cache par famille de moteur, et l'**effet de la normalisation** sur les phrases réelles — lecture seule, rien à allumer |
| `_mesurer_niveau.py` | le **niveau d'un fichier audio** (crête, niveau global, et surtout **niveau de la parole** : c'est lui qui dit si une voix est faible) — on peut lui donner autant de fichiers qu'on veut, WAV ou MP3 |
| `_analyse_extraits_dialogue.py` | **quelles voix ont un extrait de DIALOGUE et lesquelles une narration** : lit la transcription gardée de chaque extrait de référence (`neutts_service/references/*/references.csv`) et dit, famille par famille, lesquelles « lisent une histoire » au lieu de « parler » — lecture seule, rien à allumer (`--tout` montre le texte de chaque extrait) |
| `_migrer_index_phrases.py` | ⚠️ **écrit dans la base** avec `--ecrire` (copie la base avant) : remappe les index de phrases après la correction du découpage. **Sans argument : simulation** (rien n'est écrit). `--verifier` contrôle APRÈS coup que chaque voix pointe sur une phrase qui existe |
| `_montrer_attribution.py` | **qui parle, phrase par phrase, et avec quelle voix** dans un chapitre (`--livre 16 --chapitre 9`) : le locuteur, la voix attribuée (et sa vitesse), et le texte — lecture seule. Indispensable pour vérifier une phrase douteuse sans tout réécouter |
| `_mesurer_incises_supprimables.py` | combien de phrases contiennent une **incise de parole** (« , dit-il, »), de quel type, et **ce que ferait un code de suppression** : il essaie sur de vraies phrases et compte celles qu'il abîme (idée de Laurent, 18/09/2026) — lecture seule, rien à allumer |
| `_banc_ponctuation_exclamation.py` | fabrique le **lot d'écoute de la ponctuation du « ! »** (4 variantes) **et des incises** (gardées/retirées), sur les phrases réelles d'un livre : dossier `ecoute_ponctuation_<date>` avec les WAV numérotés, un index (ce qu'on demande), les textes exacts envoyés, et le lanceur d'écoute — **Kyutai allumé** (voir `LANCER_BANC_PONCTUATION.bat`) |
| `_mesurer_exclamations.py` | combien de « ! » sont des **interjections courtes** (pour régler le seuil), et combien d'**abréviations collées** à un prénom (Mlle suivi d'un espace insécable, comme dans le tome 5) — lecture seule, rien à allumer |
| `_diag_incises_reelles.py` | **pourquoi il reste des incises** : il sépare celles qui sont retirées, celles qui sont gardées **exprès** (non fermées), celles qui échappent par **verbe inconnu**, et les phrases qui ne sont **qu'une incise** (« demanda Morrel. ») — c'est l'outil qui a expliqué le « elles sont toujours présentes » du 18/09/2026 |
| `_mesurer_cas_tordus_20260919.py` | **combien de phrases tombent dans les cas tordus du 19/09/2026** (chapitre 96) : phrase qui n'est qu'une incise (silence joué), incise gardée à cause d'un **point-virgule** (« , dit le comte ; »), incise coupée sur une **civilité sans point** (« dit Mme Danglars »), **verbe + complément** avant le nom (« dit avec un sourire le comte »), et phrases de **8 caractères ou moins** (celles envoyées seules au moteur). Il **simule aussi le correctif** « le point-virgule ferme l'incise » **sans rien modifier** : combien de phrases il toucherait, combien perdraient tout leur texte, et des exemples avant / après — lecture seule, rien à allumer (`--livre 16`) |
| `_tester_tts_serveur.py` | ce que le **serveur** renvoie vraiment pour une phrase : il interroge le lecteur en marche (`POST /api/tts`, port 8081) et compare l'audio du texte **nettoyé** et du texte **d'origine** — le moyen le plus direct de savoir si un doute vient du nettoyage ou du **cache** (serveur allumé) |
| `_essai_garde_fou_start.py` | qui serait arrêté par le **garde-fou de `START.bat`** (les serveurs qui écoutent sur le port 8081), **sans rien arrêter** — utile pour vérifier que NIMM (port 8080) et le relais Tailscale ne sont jamais visés |

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
