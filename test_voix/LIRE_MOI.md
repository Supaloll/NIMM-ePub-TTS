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
| `test_etat_casting.js` | badges « à caster » / « voix partagée » |
| `test_filtre_genre.js` | menus de voix (femmes / hommes) |
| `test_voix_ecoutables.js` | voix d'un moteur éteint (jamais de substitution silencieuse) |
| `test_message_reseau.js` | message parlé quand le réseau tombe |
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
