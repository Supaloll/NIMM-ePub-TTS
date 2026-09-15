# BACKLOG — NIMM ePub

Backlog des améliorations à faire, notées au fil des sessions.
**Convention (voulue par Laurent) : on traite les items un par un, par
priorité, à raison d'une ou deux par session — jamais tout d'un coup.**

- Cocher `[x]` quand l'item est livré.
- Les détails techniques des items livrés sont documentés dans ARCHITECTURE.md.

---

## 🔴 Priorité 1 — Lecture audio (confort immédiat)

- [x] **Rogner les silences de bord des fichiers TTS** — livré le 08/09/2026.
  Mesuré le 08/09/2026 sur les fichiers réels : chaque phrase Edge contient
  ~0,25 s de silence de tête et ~1,0 s de silence de queue. En lecture phrase
  par phrase, cela crée ~1,2 s de blanc entre deux phrases et une
  surbrillance qui semble flotter. Rogner avant mise en cache.
  *Technique* : module `modules/audio_trim.py`, via le binaire ffmpeg déjà
  embarqué par `imageio-ffmpeg` (aucune installation). Kokoro/Piper (WAV)
  ont des silences courts et naturels → non rognés.
  **Ajusté le 15/09/2026** (demande de Laurent) : après le rognage,
  l'enchaînement des phrases lui paraissait un peu **sec**. La marge conservée
  en **fin de phrase** passe de **0,15 s à 0,25 s** — un ajout **très léger
  (+100 ms)**, et rien d'autre (la marge de tête reste 0,08 s). Vérifié par la
  mesure sur un vrai fichier Edge : silence de queue **0,88 s brut → 0,24 s**
  après rognage (attendu ≈ 0,25 s). À savoir : les phrases **déjà en cache**
  gardent l'ancien rendu (0,15 s) jusqu'à purge de `data/tts_cache/`.

- [ ] **Préchargement « burst » au passage en arrière-plan** ⏸ *EN ATTENTE*
  Mise en attente le 08/09/2026 : tester d'abord l'écran verrouillé sous
  Chrome/Brave (peut-être inutile si un navigateur gère déjà bien la
  lecture en arrière-plan). Si le problème persiste après ces tests,
  implémenter : quand `document.visibilityState` devient `hidden` pendant
  une lecture (verrouillage), précharger le maximum de la suite du chapitre
  pendant que le réseau répond encore. Fichier : `frontend/app.js`.

- [ ] **Réévaluer la surbrillance après rognage des silences**
  Le rognage devrait rendre le curseur synchrone. Si un résidu persiste,
  compenser côté client (pose du curseur légèrement différée après `play`).

- [ ] **Bascule chapitre → chapitre écran éteint (cas limite connu)**
  La fin d'un chapitre peut s'interrompre si le réseau est suspendu (il faut
  charger le texte + synthétiser le début du chapitre suivant). Piste :
  pré-synthétiser/précharger le chapitre suivant en approchant de la fin.

- [x] **UX pendant une coupure réseau** — **livré le 15/09/2026**, sous une
  forme plus sympa que prévu (idée de Laurent : « une feature inutile, donc
  indispensable »). Au lieu d'un simple texte à l'écran, le lecteur **parle** :
  « Pas de réseau, veuillez patienter. Dès que le réseau sera disponible, la
  lecture reprendra. Merci pour votre patience. » Le message est **préparé une
  fois au lancement de la lecture** — moment où le réseau fonctionne encore —
  avec **la voix du narrateur**, puis gardé en mémoire (blob) : il peut donc
  être joué **même réseau coupé**. Déclenchement : après ~8 s d'attente
  (2 attentes de 4 s), puis au plus une fois toutes les **45 s** — on ne
  harcèle pas l'auditeur. Il est coupé dès une mise en pause ou un arrêt.
  *Technique* : `frontend/app.js` — `MESSAGE_HORS_LIGNE` (**le texte est en haut
  du fichier, une seule ligne à changer** à volonté), `MESSAGE_ATTENTES_AVANT`,
  `MESSAGE_RAPPEL_MS`, `_preparerMessageHorsLigne()`, `_fautPrevenirReseau()`,
  `_prevenirReseauCoupe()`, `_couperMessageHorsLigne()`. *Vérification* :
  `test_voix/test_message_reseau.js` (9 contrôles, sans navigateur) : il vérifie
  qu'on **ne joue rien** si le message n'a pas pu être préparé et qu'on **ne se
  répète pas**.

- [x] **Un changement de voix ne s'applique pas pendant la lecture (surtout
  sur mobile)** — **CORRIGÉ le 15/09/2026** (constat de Laurent : « si je change
  la voix d'un personnage, il faut que je ferme l'application et que je la
  rouvre pour que ça prenne effet »). **Cause trouvée dans le code** : la playlist
  de lecture est construite **une fois** par `_runTTS()` (`frontend/app.js`) et
  garde la voix de **chaque phrase** (`units[i].voice`, `pitch`) ; le cache de
  blobs préchargés qui l'accompagne contient donc aussi l'ancienne voix. Or
  `_updateCharacterVoice()` (le changement de voix dans la fenêtre du casting)
  n'appelle **jamais** `_runTTS` : la lecture en cours continue avec les
  anciennes voix jusqu'au prochain lancement complet (d'où l'impression qu'il
  faut redémarrer l'application). C'est d'autant plus visible sur mobile, où le
  préchargement couvre plusieurs minutes d'audio.
  **Deux corrections possibles** (à valider, ça touche le cœur de la lecture) :
  **(a) fine, recommandée** — après un changement de voix, recalculer la voix
  des unités **pas encore lues** (`_voiceForSentence(units[i].sentIdx)`) et
  invalider leur blob préchargé, sans couper la phrase en cours : il faut un
  **compteur de génération** par unité pour que les fetchs déjà en vol
  n'écrasent pas la nouvelle voix ; **(b) simple** — arrêter et relancer la
  lecture depuis la phrase en cours (playlist reconstruite, blobs neufs) : la
  phrase en cours recommence, mais tout est fiable.
  **✅ OPTION (b) RETENUE ET LIVRÉE le 15/09/2026** (choix de Laurent) :
  `_updateCharacterVoice()` appelle maintenant `_stopTTS()` puis `_startTTS()`
  dès que la lecture est en cours (`playing` ou `loading`) — la phrase en cours
  reprend avec la **nouvelle** voix, sans redémarrer l'application. Quand la
  lecture est **en pause**, on ne relance rien : la pause est respectée, et la
  prochaine lecture reconstruira la playlist. *Garde-fou* :
  `test_voix/test_ids_ecran.py` (§ 7) vérifie que cet appel est toujours là.
  *Reste à valider à l'usage* : sur le mobile de Laurent, changer la voix d'un
  personnage pendant une lecture doit s'entendre **tout de suite**.
  L'option (a) reste décrite ci-dessus si l'on veut un jour éviter la reprise
  de la phrase en cours.
  *Corrigé au passage* (`frontend/sw.js`) : la branche `/api/` du service
  worker faisait `fetch().catch(() => caches.match())` alors qu'**aucune**
  réponse d'API n'est mise en cache — le repli ne renvoyait donc rien (erreur
  de fetch incompréhensible) au lieu d'un échec clair ; il renvoie maintenant
  une **erreur 503 explicite**, et les données de casting ne sont **jamais**
  servies périmées.


## 🟠 Priorité 2 — Voix & casting


- [x] **Nouvel ordre du pool automatique de casting, avec XTTS v2** — livré
  le 14/09/2026, décisions de Laurent. Ordre : **Henri et Denise** (Edge) en
  tête, puis les **35 voix XTTS v2** (triées par étoiles, provisoirement les
  mêmes que Kyutai), puis **Kokoro** (inchangé), puis les **autres voix
  Edge** (Charline, Sylvie, Rémy, Gérard, Antoine, Jean) déplacées tout à la
  fin. **Kyutai retiré du pool automatique** pour l'instant (reste
  choisissable à la main). Personnages secondaires (< 8 répliques) :
  `GENERIC_VOICE_F/M` passe d'Éloise/Fabrice à **Siwis/Tom** (Piper).
  *Technique* : `modules/voice_casting.py` (`_EDGE_PRIMARY_F/M`,
  `_EDGE_RESERVE_F/M`, `_xtts_pool`) ; tests mis à jour
  (`test_voix/test_pool_casting.py`). Aucun livre déjà casté n'est affecté.

- [ ] **Décider du sort des 6 voix « de rôle » NIMM dans le pool auto**
  Mamie, Papi, Narrateur, Enfant, Mystère, Jeune sont notées 3 étoiles, donc
  en tête du pool automatique : un casting (ou un re-cast) peut les attribuer
  à des personnages au hasard, alors qu'elles visent des rôles précis. À
  trancher : les exclure de `DEDICATED_VOICES_F/M` (réservées à la main) ou
  les laisser participer.

- [x] **Filtre / regroupement par genre (H/F) dans la fenêtre du casting** —
  livré le 12/09/2026. Menus **organisés par genre** (groupes 👩 Femmes / 👨
  Hommes, triés par ordre alphabétique) + barre **« Voix proposées : Toutes /
  Femmes / Hommes »** qui filtre **tous** les menus d'un coup. La voix
  attribuée reste toujours visible même si le filtre la masque, et une voix
  disparue du catalogue s'affiche explicitement (jamais de substitution
  silencieuse). Utile depuis que le catalogue atteint 135 voix (73 F / 62 M).

- [x] **Ne proposer dans les menus que les voix « écoutables » selon le moteur
  allumé** (idée de Laurent, 14/09/2026, notée « avant d'oublier »).
  **Livré le 14/09/2026** (menus + voyant ; détail technique dans
  `ARCHITECTURE.md`, section « Voix écoutables selon le moteur allumé ») :
  `GET /api/voices` ne renvoie plus les 35 voix Kyutai que si le moteur est
  **allumé et prêt** (`GET /sante` → `pret: true`) ; nouvelle route
  `GET /api/moteurs` ; **voyant** sous les réglages du lecteur (« Kyutai
  pret » / « chargement en cours » / « moteur eteint ») ; dans la fenêtre du
  casting, un personnage dont la voix n'est plus proposée affiche
  **« ⚠️ Pas de voix (Kyutai eteint) »**, et sa voix enregistrée **reste
  sélectionnée** (aucun remplacement silencieux). Tests :
  `test_voix/test_voix_ecoutables.py` et `test_voix/test_voix_ecoutables.js`.
  Aujourd'hui `GET /api/voices` renvoie **toujours** les 35 voix Kyutai, même
  quand le moteur est éteint : on peut donc en choisir une et n'obtenir qu'une
  erreur au moment de la lecture (503 + « le moteur de voix Kyutai ne repond
  pas… »). À traiter **avant l'arrivée d'XTTS v2** (voir
  `MEMO_XTTS_v2_pour_Cline.md`), car le problème deviendra double : les deux
  moteurs lourds **ne tournent jamais ensemble** (ils ne tiennent pas tous les
  deux sur la carte graphique), donc le menu ne doit montrer que les voix du
  moteur **réellement allumé** — Kyutai **8082**, XTTS v2 **8083**, test
  `GET /sante` (le lecteur sait déjà le faire : `_moteur_kyutai_actif()`,
  `main.py`). Les voix **Edge** (en ligne), **Kokoro** et **Piper**
  (processeur) restent toujours proposées : elles ne dépendent d'aucun moteur
  à allumer.
  **Décisions de Laurent (14/09/2026)** :
  (1) **Menus** : les voix indisponibles sont **masquées** — « on ne doit pas
      pouvoir les sélectionner » ;
  (2) **Livres déjà castés** : le personnage affiche **« Pas de voix »** dans
      la fenêtre du casting, et Laurent corrige **à la main** — aucun
      remplacement automatique (la voix enregistrée n'est jamais modifiée :
      un chapitre déjà écouté reste lisible grâce au cache, et un choix de
      voix fait à l'oreille n'est jamais écrasé en douce).
  *À prévoir aussi* : le pool automatique du casting (`voice_casting.py`)
  attribue les voix Kyutai **en priorité** — il devra être aligné, sinon un
  casting lancé moteur éteint produirait encore des voix inutilisables ; et un
  petit **état des moteurs** exposé par le lecteur (indicateur à l'écran),
  comme le prévoit le mémo XTTS (§ 4).

- [ ] **Barre de recherche dans la fenêtre du casting** (demande de Laurent,
  14/09/2026). Sur un livre à 175 personnages, retrouver un nom à la main
  devient long. Idée : un champ de saisie en haut de `#cast-modal` qui filtre
  les lignes **pendant la frappe** (recherche insensible aux accents et à la
  casse, comme `normalize_character_name`), le compteur de répliques restant
  visible. À trancher : faut-il que la recherche **révèle aussi les alias**
  d'un personnage trouvé (aujourd'hui repliés sous leur principal) ?
  *Fichiers* : `frontend/index.html` (champ), `frontend/app.js`
  (`_openCastModal` construit `rows` en 3 étapes — filtrer au bon endroit ne
  doit pas casser le regroupement des alias ni le filtre de genre existant),
  `frontend/styles.css`. *Test* : sur le modèle de
  `test_voix/test_filtre_genre.js`.

- [x] **START.bat : rallumer le DERNIER moteur utilisé** — **livré le
  14/09/2026**. Le fichier `data\moteur_voix.txt` (valeurs `xtts`, `kyutai` ou
  `aucun`) est **écrit par le lanceur du moteur** (`DEMARRER_XTTS.bat` →
  `xtts`, `DEMARRER_KYUTAI.bat` → `kyutai`) et **lu par `START.bat`**, qui
  allume le bon — ou rien du tout avec `aucun`. Fichier absent → `xtts` par
  défaut (le moteur vers lequel on va). Espaces parasites ignorés, nom inconnu
  → aucun moteur lancé, avec un message clair. Les garde-fous sont conservés
  (test du port avant tout lancement, message si le `.venv` manque).
  *Deux pièges `cmd` trouvés au test et documentés dans `ARCHITECTURE.md`* :
  une **parenthèse dans un texte** à l'intérieur d'un bloc `if (...)` ferme le
  bloc et **arrête tout le script** ; et un bloc `if exist ( for ... )` sur
  plusieurs lignes déraille aussi. *Vérification* :
  `test_voix/test_start_moteur.py` (16 contrôles, rien n'est réellement
  lancé). Ce fichier de réglage servira aussi de socle au **bouton de
  bascule** (item suivant).

- [ ] **Bouton de bascule entre les moteurs de voix (Kyutai ↔ XTTS v2)** —
  idée de Laurent, 14/09/2026. Un seul moteur à la fois : **allumer l'un
  éteint l'autre** (les deux ne tiennent pas ensemble sur la carte graphique).
  **Quand lancer un moteur ? — réponse de Laurent (14/09/2026) : le DERNIER
  moteur utilisé se rallume au lancement de NIMM ePub.** Mise en œuvre
  retenue : un petit fichier de réglage `data\moteur_voix.txt` (valeurs
  `kyutai`, `xtts` ou `aucun`), écrit par le bouton de bascule et lu par
  `START.bat` — trois précautions : **ne rien relancer** si un moteur tourne
  déjà ; **pouvoir choisir « aucun »** (pour démarrer sans moteur) ; éteindre
  l'autre moteur **avant** d'allumer le nouveau.
  **Prérequis désormais REMPLI** : XTTS v2 est **installé ici** depuis le
  14/09/2026 (voir l'item « Installer le moteur XTTS v2 dans NIMM ePub » —
  dossier `xtts_service`, port **8083**, 35 voix, testé) **et branché dans le
  lecteur** ; le **socle du choix du moteur existe aussi** depuis le
  14/09/2026 (item « START.bat : rallumer le DERNIER moteur utilisé » :
  `data\moteur_voix.txt` + `test_voix/test_start_moteur.py`). Il reste à
  ajouter le **bouton dans l'interface**, qui n'aura qu'à écrire ce fichier.
  **Ce qui est déjà prêt** : `etat_moteurs_voix()` (main.py) sait dire lequel
  tourne et s'il est prêt, et le lecteur sait **déjà** éteindre et rallumer
  Kyutai (`_arreter_moteur_kyutai()`, `_relancer_moteur_kyutai()`, utilisés
  pour libérer la carte pendant une analyse locale).
  **Points de vigilance** : les moteurs mettent **10 à 20 s** à charger leur
  modèle (n'annoncer « prêt » qu'avec `pret: true`) ; **ne jamais tuer un
  processus au hasard** (cibler par ligne de commande, comme
  `_pids_moteur_kyutai()`) ; **ne jamais interrompre une génération en cours**
  (les demandes sont mises en file une par une) ; prévenir que la lecture
  s'arrêtera si la voix en cours appartenait à l'autre moteur.

- [ ] **Édition du pitch par personnage dans la fenêtre du casting**
  (Déjà listé dans ARCHITECTURE, « pistes ouvertes ».) La colonne `pitch`
  existe en base ; seul le réglage manuel manque. Attention Kokoro : pas de
  pitch natif, mais post-traitement serveur existant (`_apply_pitch_shift`)
  — à valider à l'oreille et à documenter dans l'UI.

- [ ] **Regroupement `<optgroup>` des voix par pays dans les menus**
  Le catalogue (12 Edge + 54 Kokoro + Piper) devient long à parcourir sur
  mobile.

- [ ] **Ajouter MMS-TTS Meta (français)** comme voix de secours hors ligne
  Modèle `facebook/mms-tts-fra`, licence CC-BY-NC 4.0 (OK usage privé).
  Une seule voix — pas pour la diversité, plutôt une alternative neutre.

- [ ] **Voix de personnages sur mesure (clonage) — long terme**
  Coqui XTTS-v2 (17 langues dont le français, licence non commerciale) ou
  modèles récents (Qwen3-TTS, CosyVoice3...) : créer des voix uniques par
  personnage à partir d'échantillons de 6-10 s. Lourd (1-8 Go, GPU conseillé)
  → utilisable en **pré-génération offline** grâce au cache audio. Nécessite
  une carte graphique ou de la patience CPU.

- [x] **Regrouper les appellations d'un même personnage — étape 1 (doublons
  d'écriture)** — livré le 12/09/2026. Fusion automatique et gratuite des noms
  identiques à l'écriture près : accents, tirets/apostrophes, article initial
  (« Gerard » / « Gérard de Villefort », « Le comte de Monte-Cristo » /
  « Comte de Monte-Cristo »). Bouton « Regrouper doublons » dans la fenêtre du
  casting (aperçu confirmé avant application), réversible (bouton ✂). Table
  `character_aliases` purement descriptive : aucun nom supprimé. Chaque alias
  garde sa propre voix, modifiable indépendamment. Détails dans ARCHITECTURE.md.

- [x] **Regrouper les appellations d'un même personnage — étape 2 (rattachement
  manuel des pseudonymes)** — livré le 12/09/2026. Bouton **🔗 « rattacher à… »**
  sur chaque personnage de la fenêtre du casting : on choisit le personnage
  principal dans une **liste déroulante** (les plus présents en premier) → le
  nom s'affiche en retrait sous lui (flèche ↳), avec le total de répliques
  cumulé. **Les voix restent indépendantes** : c'est ce qui permet à
  Monte-Cristo ET à l'abbé Busoni d'être la même personne avec des voix
  différentes (accent italien pour l'abbé, par exemple) — à la différence du
  regroupement automatique, qui aligne les voix. Réversible (✂), gratuit,
  aucune donnée supprimée. Vérifié par aller-retour sur le Tome 4.
  *Reste optionnel* : des propositions par l'IA confirmées à la main, y compris
  entre tomes d'une saga ; et le cas « nom court ⊂ nom long » (« Maximilien »
  ⊂ « Maximilien Morrel ») — à ne pas automatiser aveuglément : **Morrel père**
  et **Morrel fils** sont deux personnes différentes.

- [x] **Regroupement par alias sur mobile** — traité le 12/09/2026. Cause
  identifiée : (1) les icônes du casting (🔒 verrou, ✂ détachement) faisaient
  30 px, trop petites pour le doigt → portées à **44 px** sur mobile, et la
  ligne peut passer à la ligne ; (2) le regroupement *fonctionnait* déjà (8
  doublons d'écriture sur le Tome 4), mais certains alias portent 0 réplique et
  se retrouvaient tout en bas de la liste → invisibles en pratique. C'est
  désormais expliqué dans la documentation.

- [ ] **Kyutai : les 228 voix CC0 et les accents par voix étrangère** (pistes
  ouvertes le 12/09/2026, **écoutées le même jour** par Laurent).
  (1) **228 voix CC0** (`voice-donations`, langue non déclarée) : les 2
  premières écoutées ne conviennent pas (« non », dont une « voix caverne »)
  → aucun signe de voix française cachée de ce côté pour l'instant ; d'autres
  échantillons pourront être écoutés un jour (licence **CC0** = la plus libre
  de la banque).
  **⏳ LOT D'ÉCOUTE PRÊT (14/09/2026) — en attente de Laurent.** Un outil
  dédié a été écrit pour répondre à la seule vraie inconnue (**quelle langue,
  quel accent ?**) : `kyutai_service\_ecouter_voix_cc0.py` télécharge un
  **échantillon aléatoire reproductible** (graine fixe) des enregistrements
  CC0 et les fait écouter **tels quels, sans aucun moteur** — c'est
  l'enregistrement d'origine, pas une synthèse. Lot du jour : **30 voix**
  (18,3 Mo, **5 minutes d'écoute**) dans
  `kyutai_service\sortie_ecoute_cc0\`, fichiers **numérotés `voix01_` à
  `voix30_`** pour l'ordre d'écoute, avec un `index_ecoute.txt` à annoter
  (langue / accent / à garder). Les 2 voix déjà jugées (0a67, 1410) sont
  écartées. *Premier indice à l'œil nu* : sur ces 30 tirées au hasard,
  **aucun nom n'évoque le français**, alors que deux annoncent explicitement
  leur accent (`english_with_german_accent`, `Vinith___English_India`) et que
  plusieurs sont manifestement d'origine indienne, arabe ou hispanique.
  *Rappel de licence* : la **source** est CC0 (la plus libre), mais si ces
  voix servent de modèle de **clonage à XTTS v2**, l'audio produit reste sous
  licence **non commerciale** (CPML) — pour une banque partageable, c'est
  **Kyutai** (CC BY 4.0) qu'il faudrait, comme en septembre 2026.
  **✅ VERDICT DE LAURENT (écouté le 14/09/2026) : RIEN D'EXPLOITABLE.** Sur
  les 30 voix du lot : **~90 % d'anglais**, **un peu d'espagnol**, et **une
  seule voix française** — dont l'enregistrement ressemble au captage d'une
  **conférence** (« texte louche », donc qualité d'origine douteuse). Aucun
  timbre à retenir. La piste `voice-donations` est donc **close** : ce n'est
  pas un vivier de voix françaises, et ses origines sont trop hétérogènes
  pour un usage de narration. Le script d'écoute reste disponible si un jour
  on veut interroger une autre famille de la banque.
  Autres tirages possibles : `--nombre 12`, `--graine 1` (tirage différent).
  (2) **Accents — verdict positif** : les 2 voix anglaises **VCTK** (CC BY)
  donnent un « accent anglais **léger** » jugé bon, et une voix **Ears**
  (CC BY-NC → usage privé) est retenue malgré un « accent hésitant
  indéfinissable ». Décision de Laurent : ces voix **ne rentrent pas dans le
  pool automatique** — elles s'assignent **à la main**.
  **Décision du 12/09/2026 : on n'ajoute RIEN au lecteur pour l'instant** —
  les essais restent dans `kyutai_service/voix_autres/` (hors Git, hors
  menus) et la piste sera réexaminée plus tard. Pour la reprendre : relancer
  `_tester_voix_etrangeres.py` (moteur allumé), écouter, puis — si le besoin
  se confirme — ajouter les voix retenues au catalogue du lecteur (genre +
  drapeau + nom, hors pool). Essais et `index_ecoute.txt` annoté conservés
  dans `kyutai_service/sortie_ecoute_etrangeres/`.

- [ ] **Écouter d'autres voix VCTK (anglaises) pour les accents** (idée de
  Laurent, 12/09/2026 — à faire une prochaine session). Les **2 premières**
  voix VCTK (accent anglais léger) ont été retenues, mais la famille en compte
  **106** : en écouter un lot permettrait de trouver d'autres registres
  (grave/aigu, homme/femme) et d'autres qualités d'accent, toujours pour les
  personnages étrangers — à assigner **à la main**, hors pool automatique.
  Outil prêt : `kyutai_service/_tester_voix_etrangeres.py --familles vctk
  --par-famille 10` (moteur allumé ; sortie dans `sortie_ecoute_etrangeres/`,
  avec index à annoter). Licence **CC BY 4.0** (partageable).

- [ ] **Distribution fine des petits rôles** (suite de la décision Kyutai du
  12/09/2026). **Mis à jour le 14/09/2026** : les personnages de moins de
  8 répliques reçoivent désormais une voix générique **Piper** partagée par
  genre (`GENERIC_VOICE_F/M` = `piper:siwis:0` / `piper:tom:0`, décision de
  Laurent) — les voix Edge Éloise/Fabrice ne servent plus à cela. Le reste de
  l'item reste ouvert : Laurent avait soulevé le risque qu'un petit rôle se
  retrouve avec une voix se confondant avec celle du **narrateur** (Ariane,
  Suisse, qui reste la voix du narrateur sur tous les livres). Pistes à
  trancher : un seuil à ajuster, ou l'usage de quelques voix du pool pour les
  petits rôles.

- [ ] **Réécouter et ajuster les notes « stars » Kokoro** au fil de l'usage
  (elles sont indicatives) — utile car le pool automatique du casting pioche
  par note décroissante.

- [x] **XTTS v2 : la voix « bute » sur les guillemets `« »`** — **LIVRÉ et
  VALIDÉ À L'OREILLE le 15/09/2026** (constat de
  Laurent, 14/09/2026, à l'écoute d'un livre). Les phrases de dialogue
  arrivent au moteur **avec leurs guillemets français** (le lecteur envoie la
  phrase entière, telle qu'elle est attribuée au personnage), et XTTS produit
  alors un son étrange à cet endroit. À faire : **retirer les guillemets**
  (`«`, `»`, `"`, `“`, `”`) avant de donner le texte au moteur — les autres
  moteurs les ignorent naturellement (Edge, Kokoro, Piper), donc le nettoyage
  doit viser **XTTS uniquement** pour ne rien changer à ce qui marche déjà.
  *Où* : dans le service (`xtts_service/servir_xtts.py`, avant génération) de
  préférence à `_clean_text()` du lecteur, qui est partagé par tous les
  moteurs — et qui **change les clés du cache audio** si on le modifie.
  *Méthode proposée* : un lot d'écoute comparatif (même phrase : brut / sans
  guillemets / guillemets remplacés par une virgule) pour trancher à l'oreille
  avant de figer le remède. À étendre ensuite à d'autres signes si Laurent en
  repère (tirets de dialogue `—`, points de suspension…).
  **🎧 LOT D'ÉCOUTE PRÊT (15/09/2026) — en attente de Laurent.** Outil :
  `xtts_service/_ecouter_guillemets.py` (voix Bertrand, choix `--voix`), sortie
  `xtts_service/sortie_ecoute_guillemets/` (8 WAV + `index_ecoute.txt`, hors
  Git). Le lot ne fait varier **qu'une chose à la fois** : la phrase de
  référence avec les guillemets tels quels, retirés, remplacés par une virgule,
  remplacés par une espace ; puis une phrase à **point d'interrogation interne**
  (le cas « citation ouverte ») avec et sans guillemets ; puis un dialogue au
  **tiret cadratin**, tel quel et tiret retiré. Chaque fichier est accompagné de
  sa **mesure objective** (durée, morceaux de parole, silences) : *le défaut se
  voit déjà sans écouter* — avec les guillemets, la phrase de référence dure
  **4,9 s** (contre **3,4 s** sans) et le moteur pose une pause anormale de
  0,82 s ; le **tiret cadratin**, lui, ne change rien (3,3 s contre 3,4 s).
  Reste à trancher à l'oreille : guillemets **retirés** (le texte final est
  identique à la variante « espace ») ou **remplacés par une virgule**.
  *Pour la mise en œuvre* : le nettoyage se fera dans `_lire_un_morceau()` du
  service (seul endroit où le texte part au moteur), **uniquement pour XTTS**,
  et il **change la clé du cache audio** — les phrases déjà lues garderont
  l'ancien rendu jusqu'à purge du cache.
  **✅ REMÈDE ÉCRIT le 15/09/2026, d'après l'écoute de Laurent** (verdict
  conservé dans `xtts_service/sortie_ecoute_guillemets/avant_remede/verdict_laurent.txt`).
  Ce qu'il a entendu : avec les guillemets, le moteur **prononce** des sons
  parasites (« ogui … haa », « iogué … yo ») ; avec le **tiret cadratin**, il
  **répète le premier mot** (« vous **êteêtes** sûr de vous ») — défaut
  **invisible à la mesure de durée** (3,3 s contre 3,4 s), seule l'oreille l'a
  attrapé ; remplacer les guillemets par une **virgule** déforme l'intonation et
  par une **espace** fait partir la voix dans les aigus : les deux sont
  écartés. D'où `nettoyer_pour_xtts()` dans le service : **guillemets retirés**,
  **tiret cadratin en tête de réplique retiré**, **tiret d'incise remplacé par
  une virgule** (la respiration reste). Les tirets d'union (« demanda-t-il »),
  apostrophes et points de suspension ne sont pas touchés.
  *Vérification* : `test_voix/test_nettoyage_xtts.py` (17 contrôles, sans
  moteur). *Reste à valider à l'oreille* : le même lot régénéré après le
  remède (les fichiers 01, 05, 07 et 09 doivent sonner comme 02 ou 08).
  **🎧 LOT « APRÈS REMÈDE » GÉNÉRÉ le 15/09/2026** (moteur XTTS relancé par
  Laurent, 9 fichiers + `comparaison_avant_apres.txt` dans le même dossier) :
  les durées confirment que le moteur reçoit bien le texte nettoyé — le
  fichier 01 passe de **4,9 s à 3,6 s** (il rejoint 02, 3,7 s), 05 de **5,9 s à
  5,0 s**, 07 inchangé à 3,3 s (le tiret ne pénalise plus). Écoute de Laurent
  en attente.
  **✅ VALIDÉ le 15/09/2026** (verdict complet :
  `sortie_ecoute_guillemets/verdict_laurent_apres.txt`) : **plus de sons
  parasites** sur les guillemets (« ogui … haa », « iogué … yo » disparus) et
  **plus de répétition** sur le tiret cadratin (« vous êteêtes » disparu). Les
  variantes « guillemets → virgule » et « guillemets → espace » sont
  **confirmées mauvaises** à l'oreille (intonation aiguë, respiration en tête).
  Les défauts qui restent sont d'une autre nature (bords de phrase) : voir les
  deux items suivants.

- [ ] **XTTS : rogner les silences de bord des fichiers générés** ⏸ *EN
  ATTENTE — décision de Laurent du 15/09/2026*. Découvert le 15/09/2026 en vérifiant les
  observations d'écoute de Laurent : **chaque fichier XTTS se termine par un
  long silence** — de **0,54 à 0,91 s** de queue (moyenne 0,6 s), mesuré sur
  les 9 fichiers du lot, tandis que le silence de tête est négligeable
  (0,01 à 0,03 s). Le lecteur demandant **une phrase à la fois**, cela fait
  **~0,6 s de blanc après chaque phrase** à la lecture, auquel s'ajoute le
  silence de 0,35 s posé entre deux phrases. Or le même défaut a déjà été
  corrigé pour **Edge** le 08/09/2026 (`modules/audio_trim.py` : 0,25 s de tête
  et 1,0 s de queue retirés, via le ffmpeg embarqué d'`imageio-ffmpeg`) —
  **jamais pour XTTS**. À faire : le même rognage dans le service XTTS
  (`servir_xtts.py`, en **numpy**, disponible là-bas), avec une petite marge
  pour ne pas mordre la fin du dernier mot, puis vérifier par la mesure
  (silence de queue ≈ 0) et à l'oreille (rythme de lecture plus fluide).
  **⏸ DÉCISION DE LAURENT (15/09/2026) : ON N'Y TOUCHE PAS POUR L'INSTANT.**
  Deux raisons, à garder : (1) il craint qu'on **abîme la voix** en lui retirant
  les fins de phrase — « pour ce que j'ai pu écouter, c'est relativement
  fluide » ; (2) il pense que ces défauts de bord (respirations, attaques)
  viennent surtout de ce que **la phrase est isolée** : le moteur ne voit
  qu'une phrase, sans contexte, et « respire » aux extrémités — rogner ne
  corrigerait donc pas la cause. Il préfère **écouter un début de livre** et ne
  relever que ce qui gêne vraiment, plutôt que de viser la perfection sur des
  détails : « on a retiré le plus pénible à l'oreille ». À ne reprendre que si
  une écoute prolongée le justifie.

- [ ] **XTTS : défauts résiduels entendus le 15/09/2026** (après le
  remède sur les guillemets, donc à reprendre séparément). Tous se situent aux
  **extrémités** des phrases : (1) **attaque du premier mot** — « sourezet »
  pour « Vous êtes sûr » (01), voix **aiguë en début de phrase** (03, 07, 08) ;
  (2) **respiration / inspiration en fin de phrase** (04, 05, 06) ;
  (3) **mot mangé** dans une incise courte : « Il arriva [en]fin » (09), où le
  remède remplace le tiret par une **virgule** — or le tiret d'incise **tel
  quel** n'a jamais été écouté : à tester (garder le tiret est peut-être mieux
  que la virgule, le défaut « êteêtes » ne concernait que le tiret EN TÊTE).
  ⚠ **Une partie de ces défauts est aléatoire** : 01 et 02 reçoivent
  **exactement le même texte** (le service retire les guillemets de 01) et
  pourtant 01 a un défaut d'attaque que 02 n'a pas — le moteur n'est pas
  parfaitement répétable. Conséquence : ne pas chercher à corriger un fichier
  précis, et ne pas confondre un défaut du code avec du bruit de génération.

- [ ] **Notes « stars » définitives pour les 35 voix XTTS v2** (14/09/2026).
  Les notes actuelles sont **provisoires** : elles ont été recopiées des voix
  Kyutai correspondantes, puisque XTTS clone **les mêmes extraits** (mêmes
  identifiants, mêmes prénoms, seul le libellé change : « 🇫🇷 France (XTTS) »).
  Or le rendu du clonage peut différer de celui de Kyutai → à corriger après
  le **lot d'écoute** des 35 voix (étape restante de l'item XTTS, plus haut).
  *Rappel licence* : le modèle XTTS v2 est en **CPML (usage non commercial)**,
  l'audio produit suit la même règle — voir `xtts_service/ATTRIBUTION.md`.

- [x] **Peut-on cloner les voix Kokoro avec XTTS, comme on l'a fait pour
  Kyutai ? — question de Laurent (14/09/2026), analysée et tranchée : NON.**
  *Pourquoi les deux cas n'ont rien à voir* — la banque Kyutai fournit **deux
  fichiers par voix** : une empreinte `.safetensors` **et l'enregistrement
  d'une vraie personne** (`.wav` de ~10 s, 480 à 640 Ko). C'est ce WAV qui a
  servi de modèle à XTTS. Kokoro, lui, ne fournit **que l'empreinte** : chaque
  voix est un tenseur de **130 560 nombres** (510 × 1 × 256, ~522 Ko) dans
  `voices-v1.0.bin` — il n'y a **aucun son** là-dedans, XTTS ne peut rien en
  faire. Mesuré le 14/09/2026 sur le fichier réel.
  *L'astuce possible mais déconseillée* : faire parler Kokoro, enregistrer le
  WAV, et le donner à cloner. Deux raisons de ne pas le faire : (1) XTTS
  imiterait une voix **déjà synthétique**, donc au mieux égale à Kokoro et
  souvent moins bonne (défauts reproduits en double), en particulier pour les
  54 voix officielles, étrangères, dont l'accent est justement le défaut qu'on
  fuit ; (2) on y **perdrait le meilleur atout de Kokoro** — il tourne sur le
  **processeur, sans rien allumer**, donc disponible moteur éteint, alors
  qu'XTTS exige la fenêtre du moteur (2,2 Go de carte graphique) et calcule
  ~3× plus lentement que le temps réel. Remplacer le moteur le plus léger par
  le plus lourd est un mauvais échange. **Seule exception concevable** :
  « rapatrier » un timbre précis qu'on aime et qui n'existe nulle part ailleurs
  (les 6 voix de rôle NIMM — Mamie, Papi, Narrateur, Enfant, Mystère, Jeune —
  sont des **mélanges** de timbres Kokoro, sans équivalent humain), en
  acceptant une qualité incertaine.
  *La bonne piste, à la place* : cloner de **vraies voix humaines**. Le
  dossier `kyutai_service\voix_autres\` (`voice-donations` : 228 voix **CC0**,
  `vctk`, `ears`) n'a reçu que les **empreintes** (8 `.safetensors`, aucun
  `.wav`), mais la banque d'origine fournit bien les enregistrements —
  vérifié le 14/09/2026 par l'API Hugging Face (`voice-donations/*.wav`,
  `vctk/*.wav`). À rapprocher de l'item « Chercher des voix de clonage
  supplémentaires » ci-dessous.

- [ ] **Voix françaises supplémentaires : creuser CML-TTS (la source de nos 35
  voix)** — découverte du 14/09/2026. Les 35 voix françaises actuelles viennent
  du dossier `cml-tts/fr` de la banque Kyutai, qui n'est lui-même qu'un
  **extrait** d'un jeu de données public : **CML-TTS**
  (`ylacombe/cml-tts`, Université fédérale de Goiás). Vérifié le 14/09/2026 :
  - la partie **française** compte **~115 000 extraits** (107 598 en train),
    soit **~286 heures** de lecture, à raison de 11 à 16 s par extrait ;
  - ce sont des **audiobooks du domaine public lus par des volontaires**
    (projet LibriVox) — exactement le registre de NIMM ePub ;
  - licence **CC BY 4.0** (la même que les 35 voix actuelles).
  **⚠️ CORRECTION du 14/09/2026 (soir)** — j'avais écrit un peu vite qu'il y
  avait « beaucoup plus de 35 voix françaises » : **c'est faux, et le test l'a
  montré.** En parcourant le jeu (90 pages), on n'a trouvé que **32 lecteurs
  supplémentaires** (identifiants 125 à 12981). Le jeu français compte donc
  **environ 67 lecteurs en tout** — ce qui explique enfin pourquoi la banque
  Kyutai s'était arrêtée à 35 : **elle n'avait pas fait de tri**, elle avait
  pris ce qui existait. Les zones parcourues (offset 0 à 47 200 sur 107 598
  lignes) donnaient déjà 32 lecteurs, puis plus rien pendant 40 pages.
  **→ Le gisement est donc ÉPUISÉ : 32 voix nouvelles au maximum.**
  *Ce que ça a permis* : un **lot d'écoute de 32 voix françaises** de plus,
  de vraies personnes lisant des livres classiques — de quoi étoffer
  le catalogue des rôles principaux, là où l'échec des 228 voix CC0 laissait
  un vide. *Attention* : cette piste ne vaut que pour **XTTS** (un extrait de
  6 à 10 s suffit à cloner) — pour **Kyutai** elle est inutilisable, faute
  d'outil pour fabriquer une empreinte (vérifié : le dépôt officiel
  `kyutai-labs/delayed-streams-modeling` n'expose que de quoi faire parler les
  voix de la banque, jamais d'en créer une).
  **✅ FAIT (14/09/2026, soir) — 25 voix versées dans la banque XTTS.**
  Laurent a écouté les 32 extraits et annoté l'index : **5 voix à 3 étoiles,
  11 à 2, 9 à 1, et 7 notées 0 (écartées)**. Les **25 retenues** ont été
  versées dans `xtts_service\voix_fr\` (outil
  `xtts_service\_verser_voix_cml.py`, qui vérifie l'absence de doublon de
  prénom avec les 126 déjà pris) et ajoutées à `XTTS_VOICES` —
  **le catalogue XTTS passe de 35 à 60 voix**, et les pools du casting à
  **76 voix féminines / 75 masculines**. Chacune a reçu un **prénom du
  XIXᵉ siècle** (Achille, Célestin, Hortense, Berthe…), et l'**accent entendu
  par Laurent figure dans le libellé** (« France (XTTS) - accent paysan »,
  « - accent anglais », « - accent allemand », « - accent espagnol/italien »,
  « - accent canadien ») : précieux pour les personnages étrangers, à
  assigner **à la main**.
  *Piège corrigé au passage* : le catalogue des voix utilise **F/M** alors que
  l'écoute note **H/F** — les 17 premières lignes versées en `"H"` étaient
  **invisibles du pool automatique masculin**. Détecté par comptage du pool
  (0 au lieu de 17), corrigé dans le catalogue et dans l'outil.
  *Vérifié de bout en bout, moteur allumé* : `/recharger` → 60 voix connues,
  `/api/voices` → 160 voix proposées dont les 25 nouvelles, et deux synthèses
  réelles testées (Achille, Lucie) → WAV 24 kHz valides.
  *Fichiers conservés pour écoute* : `test_voix\_test_nouvelle_voix.wav`
  (Achille) et `_test_nouvelle_voix2.wav` (Lucie) — le rendu XTTS de deux
  nouvelles voix.

- [x] **🎧 Fenêtre « Écouter les voix » (le listener)** — **LIVRÉE le
  14/09/2026** (étapes 1 et 2 ; reste l'étape 3, l'export vers le catalogue).
  Idée de Laurent,
  14/09/2026. Aujourd'hui, écouter une voix oblige à passer par la fenêtre du
  casting (assigner une voix, lancer un aperçu) : des astuces à répéter, et
  impossible de comparer deux voix côte à côte — or Laurent soupçonne que
  **2 voix Edge sont identiques**. Il veut donc **une liste de TOUTES les
  voix**, avec un bouton d'écoute sur chacune, et la possibilité de **les
  annoter** (étoiles, genre, remarque) directement dans le lecteur.
  *Bonne nouvelle : presque tout existe déjà.*
  - `_previewCharacterVoice()` (`app.js`, ~ligne 690) fait **exactement** ce
    qu'il faut : `POST /api/tts` → `blob` → `new Audio(url)` → lecture. Il ne
    reste qu'à lui donner une **vraie phrase de test** au lieu du seul nom du
    personnage ;
  - `_allVoices` contient déjà la liste chargée par `loadVoices()` depuis
    `GET /api/voices`, qui ne renvoie **que les voix écoutables tout de suite**
    (les voix d'un moteur éteint sont déjà exclues) — aucun risque de bouton
    qui échoue ;
  - les fenêtres du lecteur suivent un modèle clair (`#cast-modal`,
    `#provider-modal` : `modal-overlay` + `modal-box`), et la barre de boutons
    (`#multivoice-btn`, `#rsvp-open-btn`…) accueille facilement un bouton 🎧.
  *Découpage proposé, en trois temps* :
  1. **écoute seule** (le plus court) : fenêtre + liste groupée par famille
     (Edge, Kokoro, Piper, Kyutai, XTTS) et par genre + bouton ▶ par voix +
     barre de filtre (indispensable à 160 voix) ;
  2. **annotations** : genre (H/F), étoiles, remarque libre par voix, stockées
     **localement** (fichier type `data/annotations_voix.json`, hors Git, comme
     `piper_gender_tags.json`) — c'est ce qui remplacerait les **lots d'écoute
     par fichiers** utilisés jusqu'ici (Kyutai, XTTS, CML-TTS) ;
  3. **export vers le catalogue** : reprendre les annotations pour mettre à
     jour `XTTS_VOICES` / `KYUTAI_VOICES` (étoiles, genre), comme le fait
     aujourd'hui `_verser_voix_cml.py` à la main.
  *Points de vigilance* : les voix **Kokoro et Piper** peuvent mettre quelques
  secondes au **premier** appel (chargement du modèle) ; **Edge** exige
  Internet ; le **cache audio** du lecteur s'applique (même phrase + même voix
  = instantané ensuite) ; une phrase de test **identique pour toutes** rend la
  comparaison juste — c'est le principe des lots d'écoute actuels.
  **✅ ÉTAPES 1 ET 2 LIVRÉES le 14/09/2026.** Bouton **🎧 Écouter les voix**
  sous les réglages du lecteur → fenêtre avec la liste complète groupée par
  moteur (avec le nombre), **recherche par prénom** et **filtre par moteur**,
  **bouton ▶** devant chaque voix (la phrase de référence ci-dessus, identique
  pour toutes), et **trois champs de note** par voix : genre (H/F), étoiles
  (0 à 3), remarque libre. Les notes vont dans `data/annotations_voix.json`
  (**hors Git** : ce sont les observations personnelles de Laurent) via deux
  routes, `GET`/`POST /api/annotations_voix` ; une note **entièrement vide est
  supprimée**, et le catalogue reprend alors ses propres valeurs. Le code
  affiche **H** pour masculin (convention de l'écoute et du casting) même si le
  catalogue écrit **M**.
  *Détail qui simplifie tout* : aucune synthèse n'a été réinventée — le
  listener réutilise `POST /api/tts` (le même chemin que la narration) et
  `GET /api/voices`, qui ne renvoie **que les voix écoutables tout de suite**.
  Il coupe l'écoute en cours quand on en lance une autre, et à la fermeture.
  *Vérifications* : `test_voix/test_annotations_voix.py` (12 contrôles ; il
  **sauvegarde et restaure** les notes de Laurent) et
  `test_voix/test_ids_ecran.py` (21 contrôles de cohérence écran ↔ code).
  *Étape 3 — LIVRÉE le 15/09/2026* : l'**export** des annotations vers les
  catalogues est en place (outil `test_voix/_appliquer_annotations_voix.py`,
  aperçu avant écriture) — voir l'item « Report des notes d'écoute » ci-dessous.

- [x] **Règle des paliers d'étoiles pour le pool automatique** — livré le
  15/09/2026, décision de Laurent. Le pool ne se parcourt plus par moteur mais
  par **paliers d'étoiles** (3, puis 2, puis 1) et, dans chaque palier, les
  moteurs se suivent toujours dans le même ordre : **Edge**, puis **XTTS v2**,
  puis **Kokoro**. Une voix à **0 étoile** est **écartée** des deux pools, sur
  les trois moteurs — c'est le moyen de « retirer une voix du casting
  automatique » (demande de Laurent le 15/09/2026). Conséquence : Henri et
  Denise restent en tête (3★ Edge), Rémy suit, **Antoine, Jean et Fabrice
  (0★) sortent** du pool. *Technique* : `modules/voice_casting.py`
  (`_EDGE_POOL_F/M`, `_EDGE_STARS`, `_pool_par_paliers`, `definir_voix_edge`,
  `_recalculer_pools`) ; `main.py` transmet `FRENCH_VOICES` au démarrage, pour
  qu'une **seule liste** porte les étoiles des voix Edge. Aucun livre déjà
  casté n'est affecté.

- [x] **Report des notes d'écoute dans les catalogues (étape 3 du listener)** —
  livré le 15/09/2026. `test_voix/_appliquer_annotations_voix.py` reprend
  `data/annotations_voix.json` et met à jour **étoiles** et **genre** dans
  `main.py` (voix Edge) et `modules/tts.py` (Kokoro, Kyutai, XTTS) : **aperçu
  par défaut**, écriture seulement avec `--ecrire`, **sauvegarde automatique**
  des fichiers, et conversion **H → M** (l'écoute note H/F, les catalogues
  M/F). La **remarque libre** n'est pas reportée (les catalogues n'ont pas de
  champ pour elle). Premier report réel le 15/09/2026 : Antoine, Jean et
  Fabrice à 0★, Ariane à 3★.

- [x] **Badges d'état dans la fenêtre du casting** — livré le 15/09/2026
  (demande de Laurent : voir les personnages sans voix et les voix encore
  disponibles). Une **2ᵉ barre de filtres** au même look que celle des genres —
  « Personnages : Tous / ⚠ À caster / ⧉ Voix partagée » — mais qui filtre les
  **lignes de personnages** (l'autre filtre les voix proposées dans les menus),
  plus un **résumé** (« N personnages · n à caster · n voix partagées ») et un
  **badge par ligne** dans les deux seuls cas qui demandent une décision :
  *⚠ à caster* (au moins 8 répliques mais encore la voix générique des petits
  rôles) et *⧉ voix partagée (n)* (même timbre porté par n autres personnages,
  à différencier au pitch). Les petits rôles restent sans badge : leur voix
  générique est voulue. *Technique* : `_etatCasting()` dans `frontend/app.js`
  (fonction pure), `#cast-etat-bar` dans `index.html`, styles dans
  `styles.css` ; vérifications `test_voix/test_etat_casting.js` et
  `test_voix/test_ids_ecran.py`.

- [x] **Noms des voix dans la fenêtre du casting (identifiants au lieu des
  prénoms)** — livré le 15/09/2026, constat de Laurent après un re-cast de
  un roman contemporain : les voix XTTS s'affichaient « xtts:cml9804 » au lieu
  d'« Alphonse ». Cause : la liste des voix proposées (`/api/voices`) ne
  contient les voix XTTS que si **leur moteur est prêt**, et elle pouvait
  dater d'avant l'allumage du moteur — le menu retombait alors sur
  l'identifiant technique. Correctifs : (1) nouvelle route
  `/api/voix_catalogue` : **toutes** les voix, moteurs éteints compris, avec
  leur prénom, leur famille et un drapeau `dispo` — elle sert à **nommer**,
  jamais à proposer ; (2) la fenêtre du casting recharge la liste des voix et
  le catalogue **à son ouverture** (un moteur allumé après le chargement de la
  page est vu tout de suite) ; (3) le libellé porte le prénom, avec la raison
  quand le moteur est éteint ou en chargement ; l'identifiant n'apparaît plus
  que si la voix est **vraiment** absente du catalogue.
  *Vérifications* : `test_voix/test_libelles_voix.py` (catalogue complet,
  « Alphonse » pour `xtts:cml9804`, `dispo` comparé à `/api/moteurs`, et
  contrôle sur un vrai livre casté — les 125 personnages d'un roman contemporain) et
  `test_voix/test_filtre_genre.js` (cas « voix absente de la liste » : prénom
  affiché, identifiant absent).

- [ ] **Prendre une voix déjà attribuée : « Partager » ou « Déplacer »** —
  décidé avec Laurent le 15/09/2026, **pas encore commencé**. Quand on choisit
  une voix déjà portée par un autre personnage, une confirmation en français
  proposera **(a) Partager** (l'autre garde la voix, la hauteur est décalée
  automatiquement et affichée) ou **(b) Déplacer** (l'autre personnage passe
  « à caster », avec la voix générique provisoire — jamais un vide, qui
  casserait la lecture). À compléter par un **tiroir des voix encore libres**
  du livre (celles du pool qu'aucun personnage n'utilise), avec ▶ pour écouter
  et un clic pour attribuer : c'est le « tri » demandé par Laurent, et le
  dernier gros gain pour les castings à 175 personnages.

- [ ] **PARTAGE : quelles voix peut-on laisser dans un dépôt public ?** —
  question de Laurent (14/09/2026). Contexte : il **ne vend pas** NIMM ePub, il
  le **partage** gratuitement. Texte de la licence XTTS relu à la source le
  14/09/2026 (`coqui/XTTS-v2`, CPML 1.0.0) :
  - un usage est **non commercial** « **tant que vous ne recevez aucun paiement
    direct ou indirect** » découlant du modèle **ou de sa sortie** → un partage
    **gratuit** entre donc dans le cadre ;
  - **mais** : « Vous devez vous assurer que quiconque reçoit une copie du
    modèle, d'une modification du modèle **ou de leur sortie** reçoit aussi une
    copie de ces termes ou leur URL ». Partager de l'audio XTTS **impose donc
    d'y joindre la licence CPML**, et **impose la restriction à tous ceux qui
    le téléchargent** (eux non plus ne pourront pas s'en servir
    commercialement).
  **Ce qui est propre, et ce qui ne l'est pas** :
  - ✅ **les extraits de voix** (CML-TTS, **CC BY 4.0**) sont **pleinement
    partageables** dans le dépôt, avec attribution (Kyutai + CML-TTS +
    LibriVox) — c'est l'**ingrédient** de référence ;
  - ⚠️ **l'audio produit par XTTS** (CPML) : à éviter dans le dépôt. Deux
    raisons — mélange de licences délicat avec la **GPL-3.0** du programme
    (exactement le raisonnement qui avait fait écarter **NeuTTS** de
    l'embarqué, cf. plus bas), et surtout la restriction qu'on imposerait à
    tous les utilisateurs. **La bonne méthode** : distribuer les extraits, et
    laisser chacun **régénérer** l'audio chez lui (c'est déjà le principe du
    cache audio local) — l'audio reste alors privé, chez chacun.
  - 🔎 **Conséquence pratique** : si l'objectif devient un jour de livrer une
    **banque de voix audio partageable**, c'est **Kyutai** qu'il faut utiliser
    (modèle en **CC BY 4.0** → ses sorties sont partageables avec attribution),
    pas XTTS.

- [ ] **Veille : garder un œil sur la banque de voix libres** (demande de
  Laurent, 14/09/2026). Elles bougent (de nouvelles voix apparaissent, d'autres
  jeux de données se publient). À refaire **de temps en temps, sans urgence** :
  relancer `kyutai_service\_lister_banque.py` (inventaire de
  `kyutai/tts-voices` : 522 voix dans 110 dossiers au 14/09/2026) et regarder
  s'il existe désormais un dossier **français** ailleurs que `cml-tts/fr`
  (35 voix). Point d'attention : `cml-tts` ne couvre pas que le français — il
  contient aussi néerlandais, allemand, italien, polonais, portugais, espagnol
  (utile un jour pour des **personnages étrangers**, à assigner à la main).

- [ ] **Ce que fait NIMM (le projet de Nando) sur l'audio — relevé du
  14/09/2026**, à la demande de Laurent (« voir comment il s'y est pris »).
  Lecture seule de `<projet NIMM>` (projet distinct, rien modifié). Deux
  fonctionnalités **différentes**, qu'il ne faut pas confondre :
  1. **Livre audio DAISY** (`nimm_make_daisy`, `daisy_audio`, `mp3` dans
     `hub.py`/`coanimm.py`) : un texte → des **MP3 par chapitre** + un **index
     DAISY**, donc un format de livre audio **accessible** (lisible par Victor
     Reader, AMIS, EasyReader) avec **synchronisation texte/audio**. Voix :
     **une seule** (edge-tts type `fr-FR-DeniseNeural`, ou Voxtral Mistral).
  2. **Résumé audio à 2 voix** (`/api/coanimm/audio_overview`, façon
     « NotebookLM ») : un LLM écrit un **dialogue de podcast** entre « Hôte »
     et « Invité » (12 à 18 répliques, format strict `Hôte: …` / `Invité: …`),
     puis **Gemini TTS multi-locuteurs** lit tout le dialogue en **UNE SEULE
     requête** (`multiSpeakerVoiceConfig`, 2 voix max — Charon + Aoede par
     défaut). C'est **ça** le « à 2 voix » : un dialogue de présentation, **pas**
     la narration d'un roman.
  *Trois enseignements pour NIMM ePub* :
  - **le format DAISY** est une piste sérieuse pour un futur **export**
    (accessibilité + synchronisation), indépendante du moteur de voix ;
  - **Gemini TTS** (API Google, payante à l'usage) donne des voix très
    naturelles, mais **2 locuteurs maximum** → inutilisable pour un roman à
    175 personnages ; à réserver à un usage de type dialogue ;
  - Nando utilise aussi le **clonage de voix chez Mistral** (`voxtral:` /
    `mistral-clone:` avec un extrait audio) : même idée que XTTS, mais **en
    ligne**, donc **sans carte graphique ni moteur à allumer** — piste à
    connaître si l'installation locale devient un frein.
  *À retenir* : l'approche de NIMM ePub (casting par personnage, phrase par
  phrase, moteurs interchangeables) est **beaucoup plus ambitieuse** sur le
  multi-voix ; celles de NIMM sont plus simples mais **tout-en-un par API**.

- [ ] **Chercher des voix de clonage supplémentaires « communautaires »**
  (piste de Laurent, 14/09/2026). Il existe sur GitHub et Hugging Face des
  jeux de voix réalisées par la communauté pour XTTS. Deux précautions à
  poser **avant** tout ajout : n'utiliser que des extraits dont la
  **licence autorise le clonage** (l'extrait doit être libre — CC BY/CC0 — et
  le consentement de la personne dont la voix est reproduite doit être
  explicite), et vérifier que le libellé du catalogue reste **sans doublon de
  prénom** avec les familles existantes. À relier à l'item Kyutai « 228 voix
  CC0 » (même sujet : élargir le choix pour les rôles très nombreux).

- [ ] **Ajouter le moteur Kyutai TTS 1.6B comme 4ᵉ moteur de voix** (piste
  ouverte le 12/09/2026, testée dans l'atelier NIMM Voix).
  Kyutai TTS 1.6B (`kyutai/tts-1.6b-en_fr`) est un moteur **français et
  anglais** publié par **Kyutai** (laboratoire parisien), **poids en
  CC BY 4.0** (donc partageable), 1,8 milliard de paramètres, ~3,8 Go de
  mémoire vidéo. Il s'accompagne d'une banque de **35 voix FRANÇAISES libres**
  (`kyutai/tts-voices`, dossier `cml-tts/fr`, CC BY 4.0) : des voix de
  personnes réelles, **sans accent**, et **une voix s'ajoute sans
  entraînement** (256 Ko d'empreinte par voix). Il sait aussi tenir un
  **dialogue à deux voix dans un seul flux audio**.
  **Ce que ça apporterait** : le catalogue actuel est de 12 voix Edge (en
  ligne) + 54 Kokoro (timbres étrangers, prononciation française forcée) +
  3 Piper ; Kyutai apporte d'un coup **35 timbres français natifs**, ce qui
  réduit fortement le besoin de partager une même voix entre personnages.
  **Point d'insertion déjà repéré** : `/api/tts` aiguille selon le **préfixe du
  nom de voix** (`kokoro:…`, `piper:…`, sinon Edge TTS) → ajouter une branche
  **`kyutai:`** dans `modules/tts.py` + `main.py`, et exposer ces voix dans
  `GET /api/voices`. Les menus (narrateur + fenêtre du casting) les
  afficheront sans autre modification, comme les voix NIMM.
  **Hauteur et vitesse : rien à inventer.** Kyutai n'a **aucun réglage natif**
  de pitch ni de vitesse (vérifié dans son code) ; la mécanique existante
  s'applique telle quelle (`_apply_pitch_shift` pour la hauteur,
  `length_scale`/`atempo` pour la vitesse). Un levier interne existe en plus :
  `padding_bonus` (débit plus lent — mesuré 7,7 s → 12,6 s sur la même phrase,
  hauteur inchangée).
  **Le vrai obstacle est le poids.** NIMM ePub tourne aujourd'hui sans PyTorch
  (modèles ONNX : Piper 60 Mo, Kokoro 310 + 42 Mo). Kyutai ajoute **3,4 Go de
  modèle + ≈ 4,5 Go d'environnement PyTorch** et occupe le GPU.
  **Deux façons de faire, à trancher :**
  (a) appeler `moshi` **dans le serveur** — peu de code, mais alourdit
  NIMM ePub et son démarrage ;
  (b) lancer Kyutai **à part** (son mode serveur) et l'appeler en HTTP —
  isolation propre, le lecteur reste léger, et c'est cohérent avec l'accès
  déjà réseau (Tailscale). **Recommandation de l'atelier : (b).**
  *Vigilance technique* : prévoir un **verrou d'inférence** (un seul appel à la
  fois) et un **préchargement en tâche de fond**, comme déjà fait pour Kokoro —
  chargement mesuré à **4 s**, 3,8 Go de GPU.
  *Réalité mesurée (atelier NIMM Voix, 12/09/2026)* : 115 s d'audio calculées
  en **50 s** (2,3× le temps réel), **1 s** avant le premier son, délai
  acoustique interne **1,28 s**. Fichiers d'écoute prêts :
  `<atelier NIMM Voix>\sorties\test_kyutai_20260912\`.
  *Licence* : attribution obligatoire (Kyutai + jeu de données CML-TTS) ; dans
  la même banque de voix, `expresso/` et `ears/` sont en **CC BY-NC** (usage
  privé seulement).
  **Décision du 12/09/2026 (validée par Laurent) : option (b) retenue** — le
  moteur tourne **à part**, dans un environnement **propre au projet**
  (`kyutai_service/`, Python 3.12) : le lecteur reste sur Python 3.14, les deux
  ne peuvent pas cohabiter (vérifié : les outils du moteur n'existent pas pour
  Python 3.14). **Séance 1 livrée** : dossier `kyutai_service/` avec le service
  local (charge le moteur une fois, une génération à la fois, `GET /sante`,
  `GET /voix`, `POST /tts` en WAV), les deux raccourcis à double-cliquer
  (`INSTALLER_KYUTAI.bat` une fois, `DEMARRER_KYUTAI.bat` avant d'écouter),
  l'écoute de contrôle `tester_service.py` et les attributions CC BY 4.0
  (`ATTRIBUTION.md`). **Rien n'a été modifié dans le lecteur.** Reste à faire :
  le branchement `kyutai:` (séance 2), puis les étiquettes Homme/Femme des
  35 voix pour le pool automatique du casting (séance 3).
  **Séance 2 livrée (12/09/2026)** : branchement complet dans le lecteur —
  branche `kyutai:` dans `/api/tts`, les 35 voix dans `GET /api/voices` (donc
  dans les menus du narrateur et de la fenêtre du casting), **vitesse** par
  `modules/audio_rate.py` (ffmpeg déjà embarqué) et **hauteur** par
  `_apply_pitch_shift` (le moteur n'a aucun réglage natif des deux), mise en
  cache disque comme Kokoro/Piper, délai client porté à 90 s pour ces voix, et
  **message clair (503 + alerte) si le moteur est éteint** au lieu d'une attente
  sans fin. Vérifié de bout en bout : syllabe par syllabe sur les quatre moteurs,
  vitesse (-20 % → +2,6 s), hauteur (+20 Hz → F0 208 → 237 Hz, durée inchangée),
  cache (2ᵉ appel en 5 ms), moteur éteint (message exact).
  **Séance 3 (étiquettes) — LIVRÉE le 12/09/2026** : lot d'écoute produit
  (`kyutai_service/sortie_ecoute_toutes/`, 35 WAV + `index_ecoute.txt`), annoté
  par Laurent, puis reporté dans `KYUTAI_VOICES` : **17 féminines / 18
  masculines**, 1 à 3 étoiles, et la voix n° 33 **écartée** (`stars: 0`, comme
  les voix Piper écartées : choisissable à la main, hors pool automatique). La
  mesure automatique de hauteur avait proposé un autre genre pour 19 d'entre
  elles : l'écoute a tranché.
  **Décision du 12/09/2026** : les voix Kyutai entrent dans le **pool
  automatique du casting, EN PRIORITÉ** — avant Edge et Kokoro ; les rôles
  principaux reçoivent donc d'abord un timbre français natif, tous différents.
  La voix écartée (`stars: 0`) reste exclue du pool ; les petits rôles
  (moins de 8 répliques) gardent la voix générique Edge. Les **accents
  étrangers** restent volontairement hors du pool : assignation à la main
  (Kokoro, ou voix d'essai dans `voix_autres/`).
  **Étiquetage livré (12/09/2026, suite)** : chaque voix Kyutai porte
  désormais, comme les voix Edge / Kokoro / Piper, un **prénom français**
  (35 prénoms, **aucun en double** avec les 91 noms déjà utilisés — contrôle
  automatique dans `test_voix/test_pool_casting.py`), le **drapeau**
  `🇫🇷 France (Kyutai)` et son **genre (F/M)**. Le genre apparaît maintenant
  dans **tous** les menus déroulants pour **toutes** les familles, sous la
  forme « Prénom (F) — 🇫🇷 France (Kyutai) ».

- [x] **Reprise d'une analyse voix multiples interrompue** — livré le 13/09/2026.
  Une analyse qui s'arrêtait en cours de route (erreur IA, coupure) repartait
  **du premier chapitre** et refaisait donc payer tous les chapitres déjà
  analysés. Vécu sur un roman de 38 chapitres : arrêt au
  chapitre 17 après 16 chapitres payés (~1,40 €), sans aucun moyen de
  reprendre sans repayer. Désormais : les chapitres déjà enregistrés sont
  **relus en base** et jamais refacturés, la reprise part du premier chapitre
  manquant, et si tous les chapitres sont déjà là, seule la Passe 2 (bien
  moins coûteuse) est relancée. La fiche de personnages est **mémorisée** au
  fil de l'eau (table `cast_fiche`) pour que la reprise reparte avec la même
  fiche ; à défaut (analyse antérieure), elle est reconstruite depuis les noms
  en base, avec un genre deviné d'après le prénom (correctible à la main).
  *Garde-fous* : un 2ᵉ lancement simultané est refusé (409), et un arrêt
  brutal en pleine analyse ne laisse plus le livre bloqué.
  *Technique* : `main.py` (`_chapitres_deja_traites`, `_charger_fiche`,
  `_sauver_fiche`, `_fiche_de_secours`, `_charger_resultats_en_base`,
  `_process_remaining_chapters`, `start_casting`), table `cast_fiche`,
  `voice_casting.deviner_genre()` ; tests sans appel IA :
  `test_voix/test_reprise_casting.py` (22 contrôles).

- [x] **Savoir pourquoi l'IA a refusé de répondre** — livré le 13/09/2026.
  Un échec du type « Reponse Gemini illisible : 'candidates' » signifiait que
  Google n'avait renvoyé aucune réponse exploitable — sans jamais dire
  pourquoi, la raison étant jetée avec la réponse. Le message explique
  désormais la cause en français (blocage par filtre, liste de réponses vide,
  génération coupée, erreur d'API) et la réponse brute est conservée dans
  `data/journal_erreurs_gemini.log` (non versionné). La raison remonte aussi
  dans l'interface, au lieu du seul « Echec du demarrage ».
  *Technique* : `voice_casting._expliquer_reponse_gemini()` /
  `_journaliser_reponse_gemini()` ; test `test_voix/test_diagnostic_gemini.py`.

- [ ] **Fiabiliser l'estimation de coût affichée avant lancement** ⚠ *MESURE RÉELLE DISPONIBLE*
  **Nouvelle mesure du 14/09/2026** (petit livre, « Le Retour de l'enfant
  prodigue », 557 phrases, 8 chapitres, fiche de 5 personnages, moteur
  Gemini) : 10 appels, 27 683 tokens d'entrée, 2 859 de sortie, **coût réel
  0,0179 $ (environ 1,6 centime d'euro)** — pour une estimation affichée de
  ~0,06 $.
  **L'app annonce donc maintenant 3 fois PLUS que le coût réel**, alors
  qu'elle annonçait 2,5 à 3 fois MOINS avant le format compact. L'estimation
  doit donc être recalibrée : les constantes `TOKENS_OUT_PER_SENTENCE` (22) et
  l'approximation des entrées datent d'avant le format compact, qui a fait
  chuter la sortie à ~5 tokens par phrase (~465 tokens par appel de 150
  phrases, mesuré le 13/09/2026).
  *À faire* : abaisser `TOKENS_OUT_PER_SENTENCE` vers 5-6, revoir
  `JSON_OVERHEAD_CHARS`, puis vérifier que la nouvelle estimation encadre
  toujours la mesure réelle sur les deux livres mesurés (grand et petit).
  *Rappel* : le coût réel est désormais journalisé automatiquement dans
  `data/journal_tokens.csv` et affiché en fin de traitement.
  **Mesure du 13/09/2026 sur un roman de 38 chapitres (24 966 phrases)** :
  facture Google passée de 14,96 € à 9,32 €, soit
  **5,64 € au total** (dont ~1,40 € pour la première tentative arrêtée au
  chapitre 17, et ~4,24 € pour la reprise des 22 chapitres restants).
  Or l'app annonçait **~2,47 $ pour le livre entier** et **~1,48 $ pour les
  22 chapitres restants** : l'écart réel est d'un **facteur 2,5 à 3**.
  Hypothèse principale : le modèle « réfléchit » avant de répondre, et ces
  tokens de réflexion sont facturés au tarif de SORTIE. Sur ~168 appels, un
  raisonnement de ~10 000 tokens par appel expliquerait à lui seul l'écart.
  Piste secondaire : la fiche de personnages (124 à 175 entrées) est renvoyée
  intégralement à CHAQUE appel (~6 000 à 9 000 caractères), mais cela ne pèse
  qu'une petite fraction du total.
  **À faire, dans cet ordre :**
  1. **Compter les tokens réels** (`usageMetadata` : entrée, sortie, et
     `thoughtsTokenCount`) et les cumuler par livre — sans mesure, toute
     correction d'estimation resterait une devinette. Afficher le coût réel
     en fin de traitement.
  2. **Recalibrer l'estimation** sur ces mesures, avec une marge qui ne soit
     JAMAIS inférieure au réel.
  3. Tester une **réduction de la réflexion** (`thinkingBudget`) : économie
     attendue de 2 à 4 fois, à valider sur un chapitre déjà casté pour
     vérifier que la qualité d'attribution tient.
  4. Rappeler à l'utilisateur que **d'autres moteurs sont proposés au
     lancement** (DeepSeek, Mistral), avec des tarifs très différents.
  *Rappels* : `PROVIDER_PRICES_USD` et l'estimation sont dans
  `modules/voice_casting.py` (`estimate_cast_cost`, `COST_SAFETY_MARGIN`).

- [x] **Parade aux filtres de l'IA (refus de traiter un passage)** — livré le 13/09/2026.
  Constat du 13/09/2026 sur un roman de 38 chapitres : Google a refusé le chapitre 17
  (`promptFeedback.blockReason = PROHIBITED_CONTENT`), puis a **accepté
  exactement le même lot de 150 phrases 20 minutes plus tard**, sans aucune
  modification. Ce filtre est donc **intermittent** — et ce n'était PAS un
  problème de droit d'auteur : Google dispose d'un motif dédié à la recopie
  (`RECITATION`), absent ici.
  **Décision de Laurent : deux parades, dans cet ordre.**
  1. **Réessai** : un refus passager est renvoyé automatiquement (3 fois,
     10 s d'écart). Un texte refusé n'engendre aucun token de sortie, donc
     ces essais ne coûtent pratiquement rien.
  2. **Découpage** : si le refus persiste, le lot de phrases est coupé en deux
     et chaque moitié repart séparément (un contexte plus court passe souvent),
     récursivement jusqu'à la phrase seule. Une phrase encore refusée est
     attribuée au narrateur, avec la raison inscrite dans sa fiche : le
     chapitre reste complet et la correction se fait à la main.
  *Technique* : `voice_casting.BlocageContenu`, `_call_gemini` (réessai),
  `_analyser_lot` (découpage), `MAX_LOTS_ABANDONNES = 25` ; test sans appel IA
  `test_voix/test_anti_blocage.py` (11 contrôles) ; test ciblé à coût
  négligeable `test_voix/_test_blocage_cible.py`.

- [ ] **Faire l'attribution des voix sans aucune IA distante (piste locale)**
  Question de Laurent (13/09/2026) : « un programme Python ne peut pas faire
  ce travail ? » — si, sur deux voies, à trancher un jour :
  1. **Règles locales, sans IA** : repérer les dialogues (guillemets « »,
     tirets, incises « dit-il / répondit X »). On distingue bien narration et
     dialogue, mais l'attribution fine (qui parle dans un long échange) reste
     fragile.
  2. **Modèle de langage installé sur le PC** (comme le moteur Kyutai déjà
     installé pour la voix) : aucun filtre de sécurité, aucun envoi du texte
     à l'extérieur, plus aucun abonnement ; en contrepartie, qualité de
     compréhension inférieure à Gemini et traitement plus lent.
  À évaluer : matériel nécessaire (mémoire/carte graphique) et qualité
  obtenue sur un chapitre déjà casté, qui sert de référence.

  ### Mesures du 13/09/2026 (matériel : RTX 4060 8 Go, i5-12400F, 32 Go de RAM)
  Ollama était **déjà installé** (Qwen2.5 7,6B, Qwen3-abliterated 8,2B,
  DeepSeek-R1 8,2B, Gemma4 8B). Référence de comparaison : le casting Gemini
  du livre, chapitre par chapitre, phrase par phrase.

  **Piège décisif trouvé et corrigé** : Ollama bride le contexte à **4 096
  mots** par défaut, alors que le prompt en fait ~7 800 — le modèle ne voyait
  donc qu'**une partie du texte** (« oubli » de la moitié des répliques,
  51 % d'accord). Avec `num_ctx` à 16 384 : **83 %** sur les premiers lots.
  Second piège : un modèle de 8B (5 Go) + un contexte de 16 384 **ne tient
  pas** dans 8 Go (7,6 Go chargés, 17 % du calcul renvoyé sur le processeur,
  20 à 50 fois plus lent) → 8 192 de contexte et `think: false` pour ces
  modèles (→ 100 % sur la carte, 11 s par lot).

  **Résultats mesurés** sur 3 chapitres d'un roman de 38 chapitres (2 356 phrases),
  comparés phrase par phrase au casting Gemini de référence.
  *Rappel* = part des vraies répliques trouvées ; *précision* = part de ses
  attributions qui sont de vraies répliques ; *accord* = phrases avec le même
  diagnostic que Gemini (l'indicateur global).
  | Modèle | Rappel | Précision | Accord | Durée |
  |---|---|---|---|---|
  | Qwen2.5 (7,6B) | **92 %** | 38 % | 42 % | 7,7 min |
  | Qwen3-abliterated (8,2B) | 58 % | 39 % | 52 % | 8,1 min |
  | **qwen3:8b (8,2B)** | **70 %** | 48 % | **61 %** | 11,8 min |
  | aya-expanse:8b (8,2B) | 18 % | 27 % | 52 % | 2,6 min |
  | **granite3.3:8b (8B)** | 41 % | **49 %** | **63 %** | 9,8 min |
  | DeepSeek-R1 (8,2B) | échec : aucune réponse JSON exploitable | | | — |

  **Verdict** : deux candidats se détachent nettement — **granite3.3** (meilleur
  accord, 63 %) et **qwen3:8b** (accord 61 % mais **meilleur rappel, 70 %** :
  il oublie beaucoup moins de répliques). Aya-expanse est écarté (il rate
  82 % des répliques) et DeepSeek-R1 est inutilisable. Tous restent en dessous
  de Gemini, mais on est passé de 42 % à 63 % d'accord : le local devient
  plausible pour dépanner ou pour les passages refusés par le cloud.
  Reste à trancher par l'écoute (comparaison ciblée sur les désaccords).
  *Durées* : ~2 h pour un livre de 25 000 phrases — à améliorer (voir
  l'optimisation ci-dessus : le débordement de la carte ralentit tout).

  **Vitesse** : ~2 minutes pour 700 phrases → **~1 heure pour un livre de
  25 000 phrases**. Coût : **zéro**, et **aucun filtre de contenu** (donc
  plus jamais de blocage sur une scène violente).

  **Défaut principal : la PRÉCISION** (34-46 %). Le modèle repère bien les
  répliques mais en **invente** beaucoup : il a par exemple attribué 15
  répliques à « Silent Mike McEachern », un personnage dont le nom dit qu'il
  est muet. Le local n'est donc **pas encore utilisable pour produire**.

  **Pistes suivantes** (dans l'ordre) : consigne plus directive pour le
  local (ce qui est une réplique et ce qui ne l'est pas) ; filtrage de sa
  réponse par croisement avec les marqueurs objectifs de dialogue ; tester
  un modèle plus gros ou une seconde passe de vérification. Le local peut
  aussi servir de **pré-analyse gratuite** avant un passage Gemini.

  ### Essai d'optimisation du 14/09/2026 : RATÉ, retour en arrière
  Objectif : sortir du débordement de la carte graphique (8 % du calcul
  renvoyé sur le processeur) en réduisant le contexte de 10 240 à 8 192. Pour
  cela, la fiche de personnages devait passer en format compact (« Nom,age »
  par ligne, ~4 600 caractères de moins par appel) et les paquets de 150 à
  130 phrases.
  **Résultat mesuré sur le chapitre 5 (qwen3:8b)** :
  | | Durée | Rappel | Précision | Accord |
  |---|---|---|---|---|
  | avant | 148 s | 82 % | 52 % | 67 % |
  | après | 151 s | 99 % | 35 % | **36 %** |
  **Deux enseignements** :
  1. le débordement vers le processeur **ne ralentissait pas** le traitement :
     le temps est dominé par la **génération** des réponses, pas par la
     lecture du prompt (151 s contre 148 s, malgré 100 % sur la carte) ;
  2. le format compact de la fiche **déroute le modèle local** : il s'est mis
     à attribuer presque toutes les phrases à un personnage (rappel 99 %,
     précision 35 %). Le format JSON explicite doit être conservé.
  Tout a été remis en l'état (fiche JSON, contexte 10 240, paquets de 150).
  *À retenir* : ne pas chercher à gagner du temps en touchant au prompt — la
  qualité trinque et le gain de vitesse est nul. Le seul levier de vitesse
  réel serait un modèle plus petit, au prix de la qualité.

  ### Analyse fine des erreurs du local (14/09/2026) : ce qui rate vraiment
  Sur le chapitre 5 (681 phrases), qwen3:8b, comparaison phrase par phrase
  avec la référence Gemini :
  | Cas | Phrases | Part |
  |---|---|---|
  | Narration correcte | 263 | 38,6 % |
  | Réplique correcte (même personnage) | **36** | **5,3 %** |
  | Réplique vue, MAUVAIS personnage | **160** | **23,5 %** |
  | FAUX POSITIF (dialogue inventé) | **180** | **26,4 %** |
  | Réplique RATÉE (dialogue oublié) | 42 | 6,2 % |
  Le local déclare **376 répliques au lieu de 238** (+58 %). Autrement dit :
  il ne rate presque rien (6 %), mais il **invente du dialogue** et **se
  trompe sur le nom** — souvent sur une simple variante : « Al » au lieu de
  « Al Templeton », « l'adolescent » au lieu de « Adolescent », « Frank
  Anicetti » au lieu de « Frank Anicetti_pere ».
  **Deux corrections simples et gratuites à tester, dans cet ordre** :
  1. **Rattacher les noms au canonique** : le nom renvoyé est comparé à la
     fiche (préfixe, casse, article) puis remplacé par le nom exact. Cela
     devrait corriger une grande partie des 160 « mauvais personnages ».
  2. **Filtrer la sortie par marqueurs objectifs** : parmi les 180 faux
     positifs, **152 n'ont AUCUN marqueur de dialogue** (ni guillemet, ni
     tiret, ni verbe de parole). Un filtre les éliminerait sans toucher au
     rappel, puisque ces phrases étaient comptées à tort.
  *À noter* : une règle purement regex en ENTRÉE reste inutilisable (20 % des
  vraies répliques de ce roman n'ont aucun marqueur formel, à cause des
  répliques longues découpées en plusieurs phrases). C'est en SORTIE, comme
  contrôle de vraisemblance, qu'elle devient utile.
  *Outil* : `test_voix/_analyse_erreurs_local.py` (gratuit).

  ### Les deux correctifs mis en œuvre et MESURÉS (14/09/2026)
  | Réglage | Rappel | Précision | Accord |
  |---|---|---|---|
  | État initial (aucun correctif) | 82 % | 52 % | 67 % |
  | + rattachement des noms au canonique | 82 % | 52 % | **68 %** |
  | + filtre de vraisemblance STRICT | 45 % | **79 %** | **77 %** |
  | + filtre avec garde-fou (suite de réplique) | 76 % | 54 % | 69 % |
  **Verdict** :
  - le **filtre de vraisemblance** est **désactivé** (constante
    `ACTIVER_FILTRE_VRAISEMBLANCE = False`, conservée et documentée). Strict, il
    fait chuter le rappel de 82 % à 45 % — les répliques au tiret courent sur
    plusieurs phrases qui, elles, n'ont aucun marqueur. Avec un garde-fou
    (« phrase suivant une réplique du même personnage »), il redevient presque
    neutre (69 %) : il ne vaut pas la règle supplémentaire ;
  - le **rattachement au canonique** est **conservé** (+1 point d'accord,
    dans la marge d'erreur) pour un autre bénéfice, structurel : sans lui,
    « Al » devient un personnage distinct de « Al Templeton » dans la fiche,
    avec une voix en double. Il évite donc de polluer la fiche du livre.
  **Le vrai défaut reste entier** : le local **invente 58 % de répliques en
  trop** (376 déclarées pour 238 réelles). Corriger la détection ne suffira
  pas — il faut rendre la **consigne plus stricte** sur ce qui compte comme
  réplique (« uniquement une citation entre guillemets ou un tiret de
  dialogue »), ou passer à deux passes (une détection binaire, puis
  l'attribution). À tester la prochaine fois.

  ### VERDICT D'ÉCOUTE du moteur local (14/09/2026) : INUTILISABLE EN L'ÉTAT
  Test réel par Laurent sur « Le Retour de l'enfant prodigue » (Gide), casté
  en local (qwen3:8b) puis écouté :
  - chapitre 1 : tout est lu avec la voix du fils ;
  - chapitre 2 : les personnages changent **en pleine phrase** (« L'homme a
    besoin d'un toit sous lequel reposer sa tête » lu par le fils alors que
    c'est de la narration, puis la réplique par le père, puis retour au fils) ;
  - le narrateur est régulièrement lu par la voix du fils.
  **Arrêt du test à l'écoute.** Les pourcentages mesurés (67 % d'accord avec
  Gemini) étaient donc **trompeurs** : ils ne disent rien de la gêne réelle,
  et l'oreille tranche sans appel.
  **Conséquence** : le moteur local reste cantonné à son rôle de **rattrapage
  des passages refusés par Google** (là, une voix approximative vaut mieux que
  le narrateur qui lit une réplique). Il ne doit PAS être présenté comme un
  moteur de production.
  *À retenir* : pour juger un moteur de casting, **l'écoute est le seul juge
  fiable** — la comparaison automatique avec Gemini ne suffit pas.

  ### Gemini contre DeepSeek, mesuré et écouté (14/09/2026)
  Même livre (« Le Retour de l'enfant prodigue », 557 phrases, 8 chapitres),
  casté deux fois, puis comparé **phrase par phrase** (outil
  `_comparer_attributions.py`) :
  | | |
  |---|---|
  | Même catégorie (dialogue / narration) | **542 / 557 → 97,3 %** |
  | Même personnage nommé | 404 / 557 → 72,5 % |
  | Divergences de catégorie | **15 → 2,7 %** |
  **Coûts réels mesurés** (10 appels chacun) :
  | Moteur | Entrée | Sortie | Coût réel |
  |---|---|---|---|
  | Gemini | 27 683 | 2 859 | **0,0155 $ (1,4 centime)** |
  | DeepSeek | 28 676 | 2 108 | **0,0101 $ (0,9 centime)** |
  **Les 15 divergences sont toutes dans le MÊME passage** (chapitre 4), un
  monologue intérieur : DeepSeek attribue à l'enfant prodigue des phrases que
  Gemini laisse au narrateur. C'est le **même défaut que le local
  (sur-attribution), mais à dose infinitésimale** (15 phrases sur 557, au lieu
  d'une sur deux).
  **Écoute de Laurent** : Gemini est plus cohérent (pas de changement de
  locuteur en pleine phrase, passages ambigus laissés au narrateur) ;
  DeepSeek reste très proche. Sur ce texte, la frontière narrateur / fils /
  pensées est **ambiguë par nature** (récit introspectif), donc aucun moteur ne
  tranchera parfaitement.
  **Décision** : **Gemini reste le moteur de référence**, **DeepSeek passe
  filet de sécurité à la place du local** (cascade Gemini → DeepSeek → local,
  à implémenter) : pour quelques centimes par chapitre refusé, la qualité reste
  quasi identique, là où le local ruinait le résultat.
  *Mesure des coûts* : `_enregistrer_tokens` a été étendu aux moteurs
  compatibles OpenAI (DeepSeek, Mistral), qui n'étaient pas comptés du tout.
  Piste suggérée par Claude.AI (biais de classification forcée : sans option
  neutre explicite, un LLM « trouve » toujours une réponse) et appuyée par
  deux projets équivalents (alexandria-audiobook, audiobard). Le prompt a donc
  été renforcé : « la plupart des phrases sont de la narration, ne retiens une
  réplique que si elle porte un guillemet, un tiret ou une incise ».
  **Résultat sur le chapitre 5 : rappel 81 %, précision 46 %, accord 60 %** —
  soit 7 points de MOINS que le prompt d'origine.
  **Bilan des cinq réglages mesurés sur le même chapitre** :
  | Réglage | Rappel | Précision | Accord |
  |---|---|---|---|
  | Prompt d'origine (état de référence) | 82 % | 52 % | **67 %** |
  | + rattachement des noms au canonique | 82 % | 52 % | 68 % |
  | + filtre de vraisemblance strict | 45 % | 79 % | 77 % |
  | + filtre avec garde-fou | 76 % | 54 % | 69 % |
  | + consigne « narration par défaut » | 81 % | 46 % | 60 % |
  **Conclusion** : sur ce livre, **le prompt d'origine reste le meilleur**, et
  trois tentatives d'amélioration ont échoué. Le prompt a été affiné sur des
  sessions précédentes (Monte-Cristo) et il est bien rodé : toute retouche
  dégrade. Seul le rattachement au canonique est conservé (neutre sur
  l'accord, mais il évite les personnages en double dans la fiche).
  **Piste restante, la seule qui n'a pas encore été essayée** : la **passe de
  révision par LLM** (idée alexandria-audiobook), qui ne modifie pas la tâche
  principale mais ajoute une vérification ciblée des phrases douteuses
  (attribuées à un personnage SANS aucun marqueur de dialogue). Un LLM sait
  distinguer une suite de réplique au tiret d'une narration mal attribuée ;
  une regex, non (mesuré deux fois).

  *Outils conservés* : `test_voix/_test_nuit_modeles.py` (comparaison de
  plusieurs modèles et chapitres, écrit `data/rapport_modeles_locaux.txt`),
  `test_voix/_test_local_variantes.py` (recherche du bon réglage),
  `test_voix/_test_local_ollama.py`, et le raccourci `TESTER_MODELES_LOCAUX.bat`.

- [ ] **Tester si une phrase de contexte littéraire réduit les refus de filtre**
  Question de Laurent (13/09/2026), après avoir identifié le passage refusé
  (« Sadie » agressée : lot n°2 du chapitre 21, contenant « Sadie » et
  « tuer ») : annoncer dans le prompt qu'il s'agit d'un roman déjà publié,
  analysé à usage privé, réduirait-il les refus ?
  **Réponse honnête : effet incertain.** Google ne documente aucun moyen
  d'assouplir ses filtres par le prompt, et une formulation qui ressemble à
  une tentative de contournement peut au contraire durcir la classification.
  Une mention factuelle et sobre peut toutefois déplacer un classifieur qui
  tient compte du contexte — d'où l'idée de le **mesurer** au lieu de le
  supposer.
  *Méthode* : sur le lot fautif identifié, 5 envois sans mention puis 5 avec
  (coût ~2-3 centimes). Le filtre étant intermittent, c'est la COMPARAISON
  des deux séries qui est parlante, pas un essai isolé.
  **À faire après la fin du traitement en cours** : ne pas envoyer d'appels
  concurrents pendant qu'un casting tourne (partage du quota, risque de 429).
  *Outil* : `test_voix/_diag_lot_refuse.py` retrouve un lot à partir de la
  taille de son prompt, affichée par NIMM ePub dans la fenêtre de la console.

- [x] **Optimisation du coût : format de réponse compact** — livré le 13/09/2026.
  Après la facture de 5,64 € pour un roman de 38 chapitres, deux gaspillages ont été
  identifiés dans ce qui était demandé à l'IA :
  1. **la fiche entière devait être recopiée dans chaque réponse** (jusqu'à
     175 personnages en fin de livre) — alors que le code Python l'accumule
     déjà d'un chapitre à l'autre. Seuls les personnages **nouveaux** sont
     désormais demandés.
  2. **une fiche JSON complète par phrase** (~80 caractères), y compris les
     55 % de phrases purement narratives. Le format compact ne liste que les
     répliques, écrit le nom d'un personnage **une seule fois**, et considère
     toute phrase absente comme de la narration.
  *Mesure réelle (1 lot de 150 phrases, chapitre 17)* : **508 tokens de sortie
  au lieu de ~3 300** (6,5× moins), coût par appel divisé par ~3. Qualité
  **identique** : 150/150 phrases avec le même diagnostic narration/réplique
  que le casting de référence, et **0 fragment de citation** à re-harmoniser
  (le modèle a parfaitement suivi les consignes).
  *Surprise* : **0 token de réflexion** mesuré — l'hypothèse « la réflexion
  explique la facture » n'est PAS confirmée ; le coût venait surtout du volume
  de réponse demandé, que ce chantier attaque directement.
  *Technique* : `_build_prompt` (nouveau gabarit), `_normaliser_reponse`
  (accepte l'ancien format en secours et ignore les numéros inventés),
  `_fusionner_fiches` ; tests sans appel IA `test_voix/test_format_compact.py`
  (19 contrôles) et test réel `test_voix/_test_format_compact_reel.py`.
  *Mesure des tokens* : `_enregistrer_tokens`, `tokens_session()`,
  `data/journal_tokens.csv` (non versionné) ; le coût réel mesuré est affiché
  en fin de traitement.
  *Piste suivante* : la fiche (~6 200 caractères) est renvoyée à CHAQUE appel
  et pèse désormais l'essentiel de l'entrée — augmenter la taille des lots
  (150 → 300 phrases) réduirait l'entrée d'environ 40 %, à valider sur la
  qualité.

- [x] **Incises lues par le narrateur** (piste de Laurent, 13/09/2026) — examinée, **écartée sur mesure**.
  Idée : découper les phrases du type « … », dit Franz en souriant pour lire la
  réplique avec la voix du personnage et l'incise avec celle du narrateur, par une
  simple expression régulière locale, au moment de construire la playlist
  (`_buildPlaylist`, `app.js`) — sans toucher au LLM, au serveur ni à la base.
  Techniquement faisable et léger : les sous-segments d'une phrase partagent déjà
  le même numéro de phrase, donc la surbrillance resterait posée au bon endroit.
  **Mesure du 13/09/2026 sur un roman de 38 chapitres : 90 phrases concernées sur 11 086
  répliques, soit 0,8 %** (30 incises après guillemet, 60 après un tiret de
  dialogue), environ 3 800 caractères sur un million : **inaudible**.
  Raison : les incises sont rares dans ce roman, et lorsqu'elles forment une phrase
  à part, elles sont déjà attribuées au narrateur — donc déjà correctes.
  *Outil de mesure conservé* : `test_voix/_etude_incises.py` (gratuit) — à relancer
  sur un livre au style plus « incisant » avant de rouvrir le sujet.

- [x] **Moteur local intégré + repli automatique des passages refusés par Google** — livré le 13/09/2026.
  Demande de Laurent : « on pourrait séparer le local du cloud pour le casting ? »
  1. **4ᵉ moteur « Modèle local »** dans la fenêtre de choix : gratuit, sans
     filtre de contenu, et le texte ne sort jamais du poste. Le modèle est
     réglable dans `data/config.json` (`local_model`, défaut `qwen2.5:latest`)
     ainsi que l'adresse d'Ollama (`local_url`). Le bouton est **grisé
     automatiquement, avec la raison**, si Ollama est arrêté ou si le modèle
     n'est pas installé (route `GET /api/llm/local`). L'estimation annonce
     « gratuit (sur votre PC) » et le décompte de coût reste à zéro.
  2. **Repli automatique** : les phrases qu'un moteur distant **refuse**
     (filtre de contenu, ex. `PROHIBITED_CONTENT` de Google) sont confiées au
     moteur local, qui n'applique aucun filtre. Sans cela, ces passages —
     souvent les plus violents du roman — restaient lus par le narrateur.
     *Démonstration en test* : 5 phrases refusées → 4 récupérées par le local.
  *Technique* : `config.get_local_model()` / `get_local_url()`,
  `voice_casting._call_ollama()` (API native d'Ollama, `num_ctx` adapté et
  `think:false` pour les modèles de raisonnement), `local_disponible()`,
  `_rattraper_refusees()`, `analyze_chapter(provider_repli=...)`,
  `PROVIDER_PRICES_USD["local"]`, route `GET /api/llm/local`, bouton dans
  `frontend/index.html` et `frontend/app.js`.
  *Tests* : `test_voix/test_moteur_local.py` (6 contrôles, appel local réel) et
  `test_voix/test_repli_local.py` (5 contrôles, refus simulé + vrai local).
  *À savoir* : la qualité du moteur local reste à améliorer (précision 34-46 %,
  voir l'item « piste locale » ci-dessus) — ce chantier rend surtout le local
  **utilisable et sans risque** : on peut l'essayer sans rien payer, et il
  rattrape ce que le cloud refuse.

- [x] **Libération automatique de la carte graphique pendant une analyse locale** — livré le 13/09/2026.
  Demande de Laurent : le moteur de voix Kyutai occupe ~5,8 Go des 8 Go de la
  carte, et un modèle de langage local en demande 5 à 6 Go — les deux ne
  peuvent pas cohabiter.
  Désormais, **lancer une analyse sur le « Modèle local » éteint le moteur de
  voix** et **le rallume à la fin** du traitement, qu'il réussisse ou échoue.
  *Mesure du test* : 5 840 Mo → 1 645 Mo, soit **4,2 Go de mémoire vidéo
  libérés**, puis moteur de nouveau prêt à la fin.
  Trois précautions : une analyse **en ligne** (Gemini, DeepSeek, Mistral) ne
  touche à rien (le texte part sur internet, la carte reste libre) ; le moteur
  n'est rallumé que **si c'est l'application qui l'avait éteint** ; et il n'est
  pas relancé une seconde fois si Laurent l'a rallumé entre-temps.
  *Technique* : `_moteur_kyutai_actif()`, `_pids_moteur_kyutai()`,
  `_arreter_moteur_kyutai()` (taskkill /T, ferme aussi la fenêtre),
  `_relancer_moteur_kyutai()` (même commande que START.bat),
  `_liberer_la_carte_pour_analyse_locale()`, `_restaurer_moteur_kyutai()`
  (appelé dans un `finally`), branchement dans `start_casting`.
  *Test* : `test_voix/test_gestion_kyutai.py` (6 contrôles, moteur réel).

- [x] **Cascade de secours Gemini → DeepSeek → local** — livré le 14/09/2026.
  Jusqu'ici, un passage refusé par Google (filtre de contenu) partait
  directement au moteur local — dont on a mesuré qu'il rendait le resultat
  inutilisable à l'écoute. Désormais, la cascade est :
  1. **DeepSeek** : résultat quasi identique à Gemini (97,3 % d'accord mesuré)
     pour **environ 1 centime par chapitre** ;
  2. **le moteur local** en tout dernier recours seulement (gratuit, sans
     filtre) : mieux vaut une voix approximative que rien.
  La liste est réglable en un seul endroit : `MOTEURS_DE_SECOURS` dans
  `main.py`. `analyze_chapter(provider_repli=...)` accepte une chaîne ou une
  liste, et n'essaie jamais un moteur identique au moteur principal.
  *Mesure des coûts étendue* : `_enregistrer_tokens` compte désormais aussi les
  moteurs compatibles OpenAI (DeepSeek, Mistral), qui n'étaient pas comptés du
  tout — sans quoi tout test DeepSeek aurait été aveugle.
  *Test* : `test_voix/test_repli_local.py` (refus simulé + vrai moteur local).

- [x] **Estimation de coût recalibrée** — livré le 14/09/2026.
  Depuis le format compact, la réponse du modèle ne fait plus que ~5 mots par
  phrase au lieu des 22 estimés (`TOKENS_OUT_PER_SENTENCE`) : l'estimation
  affichée annonçait donc **4 fois le coût réel** (0,06 $ annoncés pour
  0,0155 $ payés sur le livre de test).
  Après correction, sur le même livre : **Gemini estimé 0,0200 $ pour 0,0155 $
  réels** (+29 %, marge de prudence conservée) et **DeepSeek estimé 0,0100 $
  pour 0,0101 $ réels**.
  *Vérifier de temps à autre* : comparer l'estimation et le coût mesuré
  (`data/journal_tokens.csv`) sur un nouveau livre, grand et petit.
  **Confirmation sur un GROS livre (14/09/2026, un roman contemporain, 30 293 phrases,
  211 appels, Gemini)** : notre comptage donnait **0,7624 $ (environ 0,70 €)**,
  mais la **facture Google réelle** s'élevait à **0,98 €** (solde passé de
  8,72 à 7,74 €) : nos tarifs internes sous-estimaient donc de **40 %**.
  **Calibrage effectué** : tarifs Gemini relevés proportionnellement à
  **0,42 $/M en entrée** et **3,50 $/M en sortie**, ce qui redonne exactement la
  facture (1,617 M × 0,42 + 0,111 M × 3,50 = 1,068 $ ≈ 0,98 €). Après
  calibrage, l'estimation brute d'un roman contemporain est de **1,01 $** : elle colle
  désormais à la réalité (l'affichage garde sa marge de prudence ×1,5, soit
  ~1,52 $ — à réévaluer après deux ou trois autres castings réels).
  *À retenir* : le **comptage des tokens était juste**, ce sont les **prix
  unitaires** qui étaient approximatifs — ils venaient d'ordres de grandeur,
  jamais d'une facture. DeepSeek et Mistral restent dans ce cas : à calibrer de
  la même façon le jour où Laurent donnera le montant réel.
  *Toujours 8 fois moins cher qu'hier* : 0,98 € pour un roman contemporain (30 293 phrases)
  contre 5,64 € pour un roman de 38 chapitres (24 966 phrases, donc plus petit).

- [x] **La saga transmet désormais aussi la FICHE des personnages** — livré le 14/09/2026.
  Défaut découvert en castant le tome 5 de Monte-Cristo : la saga partageait
  bien les **voix**, mais **pas la fiche des personnages**. Un tome neuf
  repartait donc avec une fiche **vide** : le modèle réinventait les noms
  (« Albert » au lieu d'« Albert de Morcerf »), le personnage n'était pas
  reconnu à l'attribution des voix, et il en recevait une **nouvelle** — alors
  que la saga existe précisément pour éviter cela.
  *Mesure* : **32 personnages sur 42** du tome 5 ont été considérés comme
  nouveaux ; seuls 10 ont hérité de leur voix du tome 2.
  *Correction* : `_fiche_de_la_saga()` construit la fiche de départ à partir
  des personnages des autres tomes de la saga. Ordre retenu pour la fiche de
  départ : fiche mémorisée du livre → fiche reconstruite depuis ses noms →
  **fiche de la saga** (117 personnages pour Monte-Cristo, vérifié).
  **Résultat mesuré après correction** (tomes 5 et 6 castés en DeepSeek) :
  | Tome | Personnages | Hérités du tome 2 | Même voix | Taux |
  |---|---|---|---|---|
  | Tome 5 | 109 | 97 | 97 | **89 %** |
  | Tome 6 | 114 | 97 | 97 | **85 %** |
  Tous les rôles majeurs (Comte, Danglars, Villefort, Mercédès, Albert de
  Morcerf, Valentine, Maximilien Morrel…) ont retrouvé **exactement** leur voix
  du tome 2. Les quelques noms non hérités sont de vrais seconds rôles
  (aubergistes, brigadiers, employés de la maison Thomson & French) qui
  n'apparaissent que dans ces tomes.
  *Coût réel total des deux tomes* : **0,2449 $ (environ 23 centimes)** pour
  9 558 phrases, échec et reprise compris.
  *À retenir* : la saga doit transmettre **les deux** — les voix (pour
  l'attribution) et la fiche (pour que le modèle réutilise les mêmes noms).

- [x] **Journal des erreurs de casting** — livré le 14/09/2026.
  Un échec de casting (coupure réseau, limite de débit du fournisseur) ne
  laissait qu'un message dans la console du serveur : perdu dès que Laurent ne
  l'avait plus sous les yeux, et impossible à diagnostiquer après coup. Les
  échecs sont désormais conservés dans `data/journal_erreurs_casting.log`
  (horodatage, livre, message et trace), sans jamais refaire d'appel payant.
  *Bonne nouvelle au passage* : l'échec du 14/09/2026 (chapitre 15 du tome 5)
  était **transitoire** — la reprise a repris au chapitre 16 et terminé
  normalement, **sans rien repayé**.

- [x] **Parade aux réponses illisibles (JSON malformé)** — livré le 14/09/2026.
  Incident réel : DeepSeek a renvoyé un JSON invalide (une accolade au lieu
  d'un crochet, colonne 459 d'un lot du tome 5 de Monte-Cristo) — et **tout le
  casting du livre s'est arrêté** après 15 chapitres.
  Désormais, `ReponseIllisible` (nouvelle exception) déclenche :
  1. **un nouvel essai du même lot** (une génération est aléatoire : un JSON
     valide arrive très souvent du deuxième coup) — 3 tentatives ;
  2. puis le **découpage du lot** en deux, comme pour un refus de filtre ;
  3. et, en dernier recours, la phrase résistante est **laissée au narrateur**
     avec la raison inscrite dans sa fiche.
  **Plus aucun échec de ce type ne peut arrêter un casting complet.**
  *Technique* : `voice_casting.ReponseIllisible`, `_analyser_lot` refondu (les
  deux parades — filtre et réponse illisible — partagent la même logique de
  réduction de lot), message d'anomalie clarifié (« non attribuable
  automatiquement (refus du filtre ou réponse illisible) »).
  *Test* : `test_voix/test_reponse_illisible.py` (7 contrôles, aucun appel IA).
  **Complément du 14/09/2026 (bug trouvé grâce au journal d'erreurs)** : la
  parade était **incomplète**. `_normaliser_reponse()` levait une erreur
  *générique* (`RuntimeError`) quand la réponse, bien que JSON valide, ne
  contenait ni `repliques` ni `phrases` — et cette erreur **traversait la
  parade** : le casting de « Notre-Dame de Paris » s'est encore arrêté, au
  chapitre 31. Corrigé en levant `ReponseIllisible` : le lot est désormais
  réessayé puis découpé comme les autres. Le test couvre maintenant ce cas
  précis (réponse valide en JSON mais sans le contenu attendu).
  *Leçon* : sans le journal `data/journal_erreurs_casting.log`, ce bug aurait
  été indétectable après coup (le message n'existait que dans la console) ; il
  a révélé à la fois la cause ET la ligne de code en cause.

- [ ] **Fabriquer de nouvelles voix : état des lieux Piper vs Kokoro**
  (exploration du 14/09/2026, à poursuivre avec Laurent). Constats mesurés :
  - **Piper** : côté français, les modèles disponibles sont déjà tous exploités —
    `siwis` (1 locuteur), `tom` (1), `upmc` (**2 seulement**, les deux en
    service), `mls_1840` (1, qualité « low »), `gilles` (1, « low ») ; le modèle
    `mls` (125 locuteurs) a été **écarté** après tests (voix LibriVox bruitées,
    souffle, hachures). Les modèles mono-locuteur n'ont **aucun vecteur à
    mélanger** : le timbre est dans les poids du réseau. Donc *fabriquer* une
    voix Piper = **entraîner un modèle complet** (corpus audio + transcriptions
    alignées + heures de calcul), pas une simple session.
  - **Kokoro** : une voix n'y est qu'un **vecteur de 256 nombres** → on peut la
    **doser** (méthode des 30 voix NIMM Voix) ou **l'entraîner seule**, le reste
    du modèle restant gelé (outil `voicepack_train`, déjà installé dans
    l'atelier NIMM Voix avec PyTorch + CUDA, corpus VoxPopuli **CC0**, premier
    essai lancé le 11/09/2026 sur la RTX 4060). Et Kokoro **tourne sans carte
    graphique** (c'est le moteur local du lecteur, 84 voix).
  → Autrement dit : Piper est le plus léger à **faire tourner**, Kokoro le plus
  accessible à **fabriquer**. À trancher : poursuivre le chantier Kokoro déjà
  ouvert, ou ouvrir un chantier d'entraînement Piper (nettement plus lourd).
  *Critère décisif pour un partage* : une voix entraînée sur un corpus **libre**
  (VoxPopuli CC0, domaine public) est partageable ; une voix clonée depuis un
  enregistrement sous droits ne l'est pas.

- [ ] **État de l'art TTS français — recherche du 14/09/2026** (pour sortir de
  l'accent des voix Kokoro). Constat de départ : Kokoro est un modèle
  **anglais** dont on force la prononciation ; seuls les timbres du pack
  français sont natifs, les autres gardent leur accent, et **le mélange ne le
  corrige pas** (les 30 voix NIMM gardent la trace de leurs ingrédients).
  Pistes recensées :
  - **Kyutai TTS 1.6B** (déjà intégré) : **35 voix françaises natives**,
    CC BY 4.0 — mais carte NVIDIA obligatoire (≈ 3,8 Go de mémoire vidéo) ;
  - **NeuTTS-Nano-French** (Neuphonic) : clonage depuis **3 à 15 secondes**
    d'audio, modèle **194 Mo en GGUF**, tourne **sur processeur** — le nombre
    de voix ne dépend donc que du nombre d'extraits. *À vérifier* : licence
    atypique (accès « gated » à accepter sur Hugging Face) et tenue réelle sur
    un long texte (le clonage instantané dérive) ;
  - **Piper, modèles français communautaires** : quelques voix existent
    (miro, tjiho 1-3, siwis Trelis…) → gain modeste (+4 à 6 voix), gratuit et
    immédiat ; licences hétérogènes (AGPL, CC BY, NC) à trier ;
  - **Supertonic 3** (Supertone) : 10 voix ONNX/processeur en 44,1 kHz,
    31 langues, licence OpenRAIL-M — mais **dépôt archivé** et timbres
    probablement non natifs ;
  - **MeloTTS-French** (MIT) et **MMS-TTS** (Meta, CC BY-NC) : 1 à 2 voix
    seulement ; **XTTS v2** : clonage de qualité mais licence **non
    commerciale** → à écarter pour un partage ;
  - **Piste de fond** : entraîner une banque **multi-locuteurs française** sur
    un corpus libre (VoxPopuli **CC0**, déjà téléchargé dans NIMM Voix ;
    CML-TTS) → des dizaines de voix natives, légères et partageables, mais
    chantier long.
  *Idée directrice* : toutes les pistes « sans accent » partagent la même
  matière première — un **locuteur français réel** sur un extrait **libre de
  droits**. Le corpus déjà téléchargé pour l'entraînement peut donc servir deux
  fois : à entraîner un modèle **et** à fournir des voix.

- [ ] **Pistes de clonage de voix française à évaluer** (demande de Laurent,
  14/09/2026 ; travail en cours dans l'atelier **NIMM Voix** — **rien n'est
  ajouté à NIMM ePub à ce stade**). Trois moteurs à tester **en complément des
  moteurs actuels** (Edge, Kokoro, Piper, Kyutai) pour fabriquer des voix de
  personnages à partir de quelques secondes d'audio. Vérifié le 14/09/2026 :
  - **1. XTTS v2 — le premier testé (en cours).** Coqui, reprise par le
    laboratoire suisse **Idiap** (le projet Coqui d'origine est abandonné).
    Bibliothèque `coqui-tts` (0.27.5, 26/01/2026), modèle `coqui/XTTS-v2` de
    **2,09 Go**, **17 langues dont le français**, clonage **zero-shot en ~6 s**
    de référence, sortie 24 000 Hz, ≈ 4 Go de mémoire vidéo → tient sur la
    RTX 4060. C'est la référence établie du clonage. **Réserve de licence** :
    le modèle est sous **Coqui Public Model License (CPML), non commerciale**
    → test d'évaluation en **usage privé** ; l'audio produit n'est **pas
    partageable**, donc **impossible à mettre dans la banque diffusée**
    (traitement identique à NeuTTS : composant externe, jamais embarqué).
  - **2. Chatterbox Multilingue v3** (Resemble AI) — à évaluer **si XTTS v2 ne
    convient pas**. Licence **MIT** : la seule des trois qui laisserait la
    porte ouverte au partage. **23 langues dont le français**, ≈ 0,5 Md de
    paramètres (≈ 2 Go) → tient sur la RTX 4060. La version multilingue v3 est
    bien publiée (dépôts étiquetés `chatterbox-v3`, 2026). **Deux points à
    connaître** : chaque fichier généré porte un **watermark PerTh** (invisible
    mais intégré), et l'éditeur vend aussi un service en ligne.
  - **3. Qwen3-TTS** (Alibaba) — à évaluer **si XTTS v2 ne convient pas**.
    Dépôt `Qwen/Qwen3-TTS-12Hz-0.6B-Base` (21/01/2026), licence
    **Apache-2.0**, **10 langues dont le français**, clonage de voix en
    **3 secondes** de référence seulement, ≈ 0,9 Md de paramètres (≈ 1,8 Go) →
    tient sur la RTX 4060 ; variantes « CustomVoice » (voix prédéfinies) et
    « VoiceDesign » (voix décrite en mots) également en Apache-2.0.
  *Ce qui existe déjà dans NIMM Voix* : bac à sable dédié (`outils/xtts_tts`)
  et script `scripts/tester_xtts.py` (texte français long → **un seul WAV**,
  temps total et temps moyen par phrase), avec un texte de test de
  **7 860 caractères (~8 min)** extrait de l'ouverture de Monte-Cristo
  (domaine public). Le test se fait **dans NIMM Voix, sur la RTX 4060** :
  aucune dépendance ajoutée ici tant que la qualité n'est pas jugée à
  l'oreille.

- [x] **Installer le moteur XTTS v2 dans NIMM ePub** (demande de Laurent,
  14/09/2026) — **service installé, démarré et testé le 14/09/2026**, sur le
  modèle exact de `kyutai_service`. Nouveau dossier `xtts_service\` :
  `servir_xtts.py` (service HTTP port **8083**, `/sante` + `/voix` + `/tts` +
  `/recharger`, une génération à la fois, gardien de fenêtre, refus de deux
  moteurs), `INSTALLER_XTTS.bat`, `DEMARRER_XTTS.bat`, `_telecharger.py`,
  `_verifier_installation.py`, `tester_service.py`, `LIRE_MOI.md`,
  `ATTRIBUTION.md`, `requirements.txt`, `.venv` Python 3.12 (**7,7 Go**).
  *Mesures du 14/09/2026 sur la RTX 4060* : modèle chargé en **9,9 s**,
  **35 voix**, sortie WAV mono 24 kHz, **≈ ×3 plus vite que le temps réel**
  (10,8 s d'audio calculés en 4,1 s).
  **Voix** : les 35 extraits de `kyutai_service\voix_fr\cml-tts\fr\` ont été
  **copiés** dans `xtts_service\voix_fr\` (ce sont les mêmes identifiants que
  le catalogue Kyutai, donc les mêmes repères) ; le modèle (2,09 Go) était
  **déjà en cache** sur la machine → **rien à télécharger**.
  **Deux pièges mesurés, documentés dans `requirements.txt`** : PyTorch **2.8**
  obligatoire (2.9+ réclame `torchcodec`, qui réclame les DLL FFmpeg
  « partagées » absentes ici) et `transformers` **borné à la branche 4.x**
  (transformers 5.x fait échouer l'import de TTS).
  **Découpage** : la limite de **273 caractères** en français est gérée par le
  service (découpage aux phrases puis aux virgules, morceaux recollés **sans
  silence**, 0,35 s **uniquement entre deux vraies phrases**) — vérifié sur un
  texte de 325 caractères : 2 morceaux (209 + 115), texte reconstitué **à
  l'identique**.
  **(1) Branché dans le lecteur — livré le 14/09/2026** : catalogue
  `XTTS_VOICES` (35 voix, `modules/tts.py`), branche `xtts:` dans
  `/api/tts`, les 35 voix dans `GET /api/voices` **quand le moteur est
  allumé et prêt** — vérifié de bout en bout (moteur allumé : `/sante` prêt
  en 10,9 s, `/api/voices` → 35 voix `xtts:`, `/api/tts` → WAV valide).
  **Reste à faire (sessions suivantes)** :
  (2) le **lot d'écoute** des 35 voix clonées (`index_ecoute.txt` à annoter),
  pour que Laurent choisisse ses préférées et corrige les étoiles
  (actuellement provisoires, reprises de Kyutai) ;
  (3) le **bouton de bascule** et le **rallumage automatique du dernier
  moteur** (voir l'item suivant).
  *Licence* : modèle **CPML, non commerciale** — l'audio XTTS reste **hors de
  toute banque diffusée**, et le moteur reste un composant **externe**
  (voir `xtts_service\ATTRIBUTION.md`).

- [x] **Licence NeuTTS lue et tranchée — 14/09/2026** (vérification demandée
  par Laurent avant tout essai). Le code comme les poids relèvent de la
  **NeuTTS Open License v1.0** (11/12/2025). Ce qu'elle dit, en clair :
  - usage **gratuit** pour tout ce qui n'est pas commercial → l'usage familial
    de NIMM ePub est **entièrement couvert**, sans seuil ni redevance ;
  - l'usage commercial est permis **en dessous de 5 M$ de chiffre d'affaires
    annuel** ; au-delà, une licence payante est exigée ;
  - la **redistribution du modèle est autorisée**, à condition de joindre la
    licence et de conserver les mentions d'attribution ;
  - le mot « Output » (contenu généré, **audio inclus**) est **explicitement
    couvert** par la licence : les livres audio produits suivent les mêmes
    règles.
  - **Point qui décide de l'intégration** : cette licence n'est pas libre au
    sens strict (elle ajoute une limite commerciale) et n'est donc **pas
    compatible avec la GPL-3.0** du programme → le code de NeuTTS **ne peut pas
    être embarqué** dans NIMM ePub.
  - **Solution retenue** : le traiter **exactement comme Kyutai** — dossier à
    part, environnement à part, installé par l'utilisateur, appelé par le
    réseau. NIMM ePub reste GPL-3.0 pur ; NeuTTS n'est qu'un composant externe
    optionnel.
  - **Deux frictions à connaître** : le modèle est « gated » sur Hugging Face
    (compte + acceptation des conditions → installation **non automatique**) ;
    et la licence du logiciel ne couvre **pas** les droits des personnes dont
    on clone la voix → n'utiliser que des extraits explicitement libres
    (VoxPopuli CC0).

## 🟡 Priorité 3 — Robustesse & architecture

- [ ] **Le mauvais moteur de voix peut se lancer tout seul** — constat de
  Laurent (15/09/2026) : au démarrage, **Kyutai** s'est lancé alors que le
  lecteur affichait « Voix de personnages : XTTS v2 prêt » — donc le réglage
  `data/moteur_voix.txt` (qui contenait bien `xtts`) n'a pas été suivi.
  Conséquence mesurée : **les deux moteurs allumés en même temps**, 7,6 Go de
  carte graphique sur 8 — ce que le projet déconseille explicitement.
  À reproduire, puis à corriger. Pistes à vérifier, dans l'ordre :
  1. `DEMARRER_KYUTAI.bat` et `DEMARRER_XTTS.bat` **écrivent** tous les deux ce
     réglage : si Kyutai a été lancé à la main plus tôt dans la journée, le
     fichier disait `kyutai` au moment du `START.bat` suivant — et Laurent a pu
     le remettre à `xtts` après (à confirmer par les horodatages) ;
  2. le lecteur lui-même sait **rallumer Kyutai** (`_relancer_moteur_kyutai()`,
     écrit pour libérer la carte pendant une analyse locale en repli) : il
     pourrait le faire sans qu'on l'ait demandé ;
  3. le **lanceur du téléphone** (`<dossier du lanceur>\launcher.py`) appelle
     `START.bat` : vérifier qu'il n'impose pas, lui, un moteur ;
  4. le double démarrage *du même* moteur est déjà bloqué (par le port), mais
     **rien n'empêche deux moteurs différents** de tourner ensemble : c'est
     peut-être le vrai garde-fou à ajouter (éteindre l'autre moteur, ou
     refuser de démarrer, avec un message clair).



- [ ] **Centraliser le découpage en phrases**
  Trois implémentations coexistent : `_buildSentences` (app.js),
  `_split_sentences` (main.py), `_split_chapter_sentences` (voice_casting.py).
  Risque de divergence silencieuse à chaque évolution de règle → une seule
  fonction partagée + tests.

- [ ] **Suite de tests automatisés + CI**
  Découpage, playlist de lecture, rognage des silences, cache, `assign_voices`
  (pools/threshold). GitHub Actions sur les fichiers Python/JS.

- [ ] **Découper les gros fichiers en modules**
  `frontend/app.js` (~1900 lignes) et `main.py` (~900 lignes) grossissent —
  à découper quand la navigation dans le code devient pénible.

- [ ] **Cache audio : statistiques et purge**
  Petite vue/endpoint pour connaître la taille du cache et le vider
  manuellement si besoin.

- [ ] **Nettoyage de `test_voix/`** (scripts de dev obsolètes, aucune
  urgence).

- [ ] **Hygiène du dépôt : clés d'API en clair, dépendances non figées, doc
  en retard** (constat de l'atelier NIMM Voix, 12/09/2026).
  (1) **Clés d'API — AUDIT FAIT le 12/09/2026, rien ne fuit.** Vérifié :
  `data/config.json` (clés Gemini, Mistral, DeepSeek) et `test_voix/cles_api.txt`
  sont **ignorés** par Git **et n'ont jamais été committés** (contrôle sur tout
  l'historique) ; les **valeurs réelles** des 3 clés ont été cherchées dans tous
  les fichiers suivis → **aucune correspondance**. Le dépôt GitHub est **privé**,
  ce qui protège aussi le reste. **Trous colmatés le même jour** : les EPUB
  étaient **suivis par Git** (13 livres + couvertures, dont un roman contemporain,
  sous droits) → **retirés du suivi** (fichiers conservés sur le disque) et
  `data/library/` désormais **ignoré** ; idem pour les extraits de livres
  (`test_voix/resultat_*.json`), les .wav de test, les `*.bak_*` et
  `server_pid.txt`. **À savoir** : les anciens EPUB restent dans l'**historique**
  Git (normal) — sans conséquence tant que le dépôt reste **privé** ; si un jour
  il devient public, nettoyer l'historique **avant** (`git filter-repo`/BFG).
  *Reste optionnel* : lire les clés depuis des **variables d'environnement**
  dans `modules/config.py` (avec `data/config.json` en repli).
  (2) **Dépendances non figées — FAIT le 12/09/2026.** Deux fichiers créés :
  `requirements.txt` (racine : les 14 paquets du **lecteur**, Python 3.14) et
  `kyutai_service/requirements.txt` (les 11 paquets du **moteur**, Python 3.12 +
  PyTorch build CUDA 12.8, avec la commande d'installation). Les versions sont
  exactes et **vérifiées automatiquement** contre l'environnement en service par
  `test_voix/test_requirements.py`. Réinstallation sur une autre machine :
  `python -m pip install -r requirements.txt`.
  (3) **Doc en retard sur le code** — *traité en grande partie le 12/09/2026*
  à l'occasion du 4ᵉ moteur : la section « modules/tts.py » décrit désormais
  les quatre moteurs (Edge, Kokoro, Piper, Kyutai) et la section
  « Dépendances Python » liste kokoro-onnx (+ onnxruntime), piper-tts,
  soundfile, pedalboard, imageio-ffmpeg, httpx et pydantic, plus
  l'environnement séparé du moteur Kyutai. Reste à vérifier au fil de l'eau.

## 🟢 Priorité 4 — Produit

- [ ] **Exporter un livre en MP3 (livre audio figé, avec le casting validé)** —
  idée de Laurent, 15/09/2026, pour plus tard : « si j'arrive à un résultat
  satisfaisant, je voudrais pouvoir exporter le livre complet avec les voix
  castées en MP3, pour le réécouter sans repasser par NIMM ePub — l'avoir
  comme un vrai livre audio ».
  **Avis : idée très pertinente, et presque rien à inventer** — tout est déjà
  là : les voix castées sont en base (table `voices`), l'audio de chaque phrase
  est déjà synthétisé et **mis en cache** (`data/tts_cache/`), et **ffmpeg est
  déjà embarqué** (`imageio-ffmpeg`) pour assembler et encoder.
  *Découpage proposé* : (1) un bouton « Exporter en MP3 » (fenêtre du casting
  ou fiche du livre) ; (2) génération **en tâche de fond** avec avancement ;
  (3) sortie dans `data/exports/<livre>/` — **un MP3 par chapitre**, un
  `playlist.m3u`, et les métadonnées (titre, auteur, numéro de piste) dans
  l'ID3, pour que le livre apparaisse proprement dans un lecteur audio.
  *Ce qui décide de la durée* : les phrases **déjà écoutées** sortent du cache →
  aucun calcul de synthèse, il ne reste que l'assemblage et l'encodage MP3
  (ffmpeg, très rapide) : **quelques minutes** pour un livre entier. Pour un
  livre **jamais écouté**, il faut synthétiser — et là, **mesure du 15/09/2026**
  (voix Bertrand, RTX 4060) : XTTS produit l'audio **×3,3 plus vite que le temps
  réel** (8,3 s de calcul pour 27,4 s d'audio ; ×2,4 sur les phrases courtes,
  ×3,4 au-delà de 100 caractères). Autrement dit **1 h de livre ≈ 18 min de
  calcul** et **10 h ≈ 3 h**, ce qui se lance très bien le soir. *(Estimation
  précédente de « 30 h pour 10 h » : fausse, corrigée le 15/09/2026 — le « ×3 »
  du mémo XTTS voulait dire « 3 fois plus rapide », pas « 3 fois plus lent ».)*
  *Points d'attention* : (1) **licence** — l'audio produit par **XTTS v2** est
  sous **CPML** (usage privé, **pas de partage public**) ; celui de **Kyutai**
  est en **CC BY** (partageable avec attribution) → l'export est destiné à
  l'**usage personnel** ; (2) les fichiers exportés **ne doivent pas entrer dans
  Git** (comme les livres) ; (3) après un export, un changement de voix **ne
  s'y applique pas** : il faut réexporter ; (4) ajouter `data/exports/` au
  `.gitignore` avant toute mise en public.
  *Bonus* : c'est aussi la réponse au cache audio — un livre exporté ne dépend
  plus ni du cache ni du serveur, et s'écoute partout (voiture, baladeur).



- [ ] **Réglages par profil** (voix/vitesse par défaut, taille de police,
  thème) — la progression est déjà par utilisateur, pas les préférences.

- [ ] **Surveiller la qualité des voix Edge « trop robotiques »** (signalée
  par Laurent) — Kokoro répond en partie ; à confirmer sur plusieurs
  personnages.

- [ ] **Gard « citation ouverte »** : surveiller les tirets de dialogue
  coupés par un `!`/`?` interne (noté dans ARCHITECTURE, pas encore
  rencontré en pratique).

## 🌍 Diffusion / partage — idée de Laurent (14/09/2026, à ouvrir dans quelques jours)

*« On verra ce qu'on peut mettre en place pour diffuser tout ce travail… je
pense qu'on n'a pas à rougir par rapport à la concurrence, et j'aimerais bien
partager tout ça plutôt que de le garder juste pour ma famille et moi. »*

**La distinction à poser d'emblée — ce sont deux choses très différentes :**

1. **Le logiciel** (NIMM ePub) : c'est le code de Laurent, il peut le partager
   comme il l'entend (dépôt public, licence libre, documentation d'installation
   pour d'autres). Rien ne l'en empêche.
2. **Les livres audio produits** : eux dépendent du **texte source**.
   - Œuvre du **domaine public** (Monte-Cristo, Notre-Dame de Paris, Gide,
     Verne, Hugo…) → diffusion libre, sans problème.
   - Œuvre **sous droits** (des romans contemporains sous droits…) → **diffusion
     impossible**, même en possédant l'ouvrage : posséder un exemplaire autorise
     un usage privé, pas une mise à disposition du public.
   → Le partage public ne portera donc que sur des œuvres libres de droits — ce
   qui laisse déjà un très vaste répertoire, et la bibliothèque de Laurent en
   contient beaucoup.

**Points à trancher au retour (rien n'est décidé) :**
- Partager en priorité **le logiciel** (pour que d'autres fabriquent leurs
  propres livres audio), des **livres audio du domaine public**, ou les deux ?
- Si le dépôt devient public : **quelle licence** (MIT ? GPL ?) et quelle
  documentation pour quelqu'un qui ne connaît pas Python ?
- Plateformes envisageables : GitHub (code), Internet Archive / LibriVox /
  YouTube (audio libre de droits), ou un site dédié.
- ⚠️ **AVANT toute mise en public du dépôt** : nettoyer l'**historique Git**
  (voir l'item « hygiène du dépôt » ci-dessus — des EPUB sous droits y sont
  présents). À faire **avant** le premier `git push` public, avec
  `git filter-repo` ou BFG.
- Ce qui donne au projet sa valeur propre, à mettre en avant : le **casting
  automatique par IA** (une voix par personnage, cohérence préservée dans les
  sagas), les **quatre moteurs de voix** (Edge, Kokoro, Piper, Kyutai), la
  **cascade de secours** (aucun passage perdu) et le **coût maîtrisé**
  (~3 centimes pour 1 000 phrases).

- [x] **README d'installation** — préparé le 14/09/2026 : `README.md` (racine)
  + modèle `data/config.example.json`. Vérifié à cette occasion :
  - les modèles de voix se téléchargent bien aux adresses indiquées (Kokoro :
    release `kokoro-onnx` v1.0 ; Piper : HuggingFace `rhasspy/piper-voices`) ;
  - les **14 paquets** du lecteur se résolvent en Python 3.14 sur un
    environnement **vierge** (essai `pip install --dry-run`, code 0) ;
  - les clés API (`data/config.json`, `test_voix/cles_api.txt`) n'ont
    **jamais** été commitées : vérifié dans **tout** l'historique Git ;
  - les livres (`data/library/`) et les modèles ne sont pas versionnés.
  *Deux points relevés au passage (à traiter le jour d'une mise en public)* :
  deux fichiers techniques sans intérêt sont encore **suivis** par Git —
  `core/__pycache__/epub_parser.cpython-314.pyc` et `server_pid.txt`
  (`git rm --cached`, ils restent sur le disque) ; et à cause de
  bibliothèques sous **GPL-3.0** (`piper-tts`, `pedalboard`,
  `phonemizer-fork`) ou **AGPL-3.0** (`EbookLib`), la licence du dépôt devra
  être **GPL-3.0** ou **AGPL-3.0** — pas MIT (détail dans le README).

- [x] **Installateur des voix locales** — livré le 14/09/2026 :
  `INSTALLER_VOIX_LOCALES.bat` (racine, un simple double-clic). Télécharge les
  6 fichiers de voix locales — Kokoro (~350 Mo) + les 3 voix Piper (~190 Mo) —
  à la racine du projet. Reprise après coupure (`curl -C -`), contrôle de
  taille, journal `installation_voix_locales.log` (ignoré par Git) et bilan
  clair en cas d'échec. Vérifié sur un dossier d'essai : les fichiers déjà
  présents ne sont **pas** re-téléchargés, les téléchargements réels sont
  valides (les trois `.json` Piper relus par `json.load`), et un échec réseau
  simulé donne bien « TERMINE AVEC 1 PROBLEME(S) » avec un code de sortie 1.

- [ ] **Installeur complet, à la façon de NIMM** (idée du 14/09/2026, à faire
  plus tard) : un seul `INSTALLER_NIMM_EPUB.bat` qui enchaîne tout sur une
  machine neuve — détecter Python (et le proposer en installation automatique
  via `winget`, comme le fait `INSTALLER_NIMM.bat`), créer l'environnement,
  installer les dépendances, télécharger les voix locales, puis annoncer
  « c'est prêt, lance START.bat ». `INSTALLER_VOIX_LOCALES.bat` (livré le
  14/09/2026) resterait le recours pour le cas « il ne manque que les voix ».
  Pour Linux, NIMM dispose d'un `INSTALLER_NIMM.sh` : à prévoir seulement si un
  partage Linux devient d'actualité — aujourd'hui, seuls des `.bat` existent
  ici.
  **Consigne de Laurent (14/09/2026)** : le moteur Kyutai (≈ 3,8 Go de mémoire
  vidéo, carte NVIDIA obligatoire) est **inutilisable sur un simple portable** →
  l'installeur ne doit le **proposer que si le matériel détecté le permet**
  (carte NVIDIA **et** mémoire vidéo suffisante), avec un message clair dans le
  cas contraire : les trois autres moteurs de voix fonctionnent sans. Piste de
  détection : `nvidia-smi`, présent avec tout pilote NVIDIA, donne le nom de la
  carte et la mémoire vidéo.

- [x] **Vérification « aucun livre dans le dépôt »** — faite le 14/09/2026 :
  l'état **actuel** du dépôt ne contient aucun EPUB (ni aucun fichier suivi de
  plus de 2 Mo). **En revanche, 22 EPUB déposés aux débuts sont présents dans
  l'HISTORIQUE** (des classiques du domaine public comme Monte-Cristo et
  Robinson Crusoé, mais aussi des romans contemporains sous droits, dont des
  fichiers téléchargés sur des sites douteux). Le
  dépôt GitHub étant **privé**, ils ne sont pas exposés
  aujourd'hui — mais ils ressortiraient tels quels le jour d'une mise en
  public. Décision de Laurent (14/09/2026) : **partager le programme, jamais
  les livres**. Reste à trancher la méthode (item suivant).

- [ ] **Retirer les livres de l'historique Git** — AVANT toute mise en public.
  **Décision de Laurent (14/09/2026) : repartir d'un dépôt neuf** — « les
  commits antérieurs n'apporteront rien de spécial au dépôt » : ils seront donc
  abandonnés à ce moment-là, ce qui efface les 22 livres **et** l'historique de
  développement d'un seul coup.
  Les deux méthodes, pour mémoire :
  **(A)** réécrire l'historique (`git filter-repo` ou BFG) puis **forcer** la
  mise à jour sur GitHub : les 32 identifiants de commits changent et GitHub
  peut conserver un temps des objets devenus inaccessibles ;
  **(B)** **repartir d'un dépôt neuf** : un seul commit initial à partir de
  l'état actuel, poussé dans un dépôt neuf — radical, sans résidu, mais
  l'historique de développement est perdu (l'essentiel est déjà raconté dans
  BACKLOG.md et ARCHITECTURE.md).
  Recommandation : **(B)**, seule méthode garantie de ne rien laisser derrière.

- [x] **Licence du programme : GPL-3.0** — décidé et appliqué le 14/09/2026. Le
  texte officiel de la licence (récupéré chez la Free Software Foundation, 674
  lignes, 35 149 octets) est dans `LICENSE`, et le README explique la décision
  en français. Raison : plusieurs
  briques utilisées (`piper-tts`, `pedalboard`, `phonemizer-fork` en GPL-3.0 ;
  `EbookLib` en AGPL-3.0) imposent qu'un programme distribué soit fourni avec
  son code source sous la même famille de licence — ce qui est de toute façon
  le cas ici. Une licence MIT serait donc **trompeuse**, et l'AGPL-3.0
  n'apporterait rien de plus pour une application locale.


## ⚪ Actions utilisateur (pas du code)

- [ ] **Tester l'écran verrouillé sous Brave** (piste Laurent — YouTube
  continue sous Brave) : PWA installée + Batterie « Sans restriction » pour
  Brave et Tailscale.
- [ ] **Tester le casting enrichi (Kokoro + seuil 8)** sur un nouveau livre
  dès que les crédits sont rechargés.

---

## ✅ Déjà livré (pour mémoire)

- **Fenêtres des moteurs : journal allégé** (15/09/2026). Deux bruits voisins
  retirés des consoles de `servir_xtts.py` et `servir_kyutai.py` : l'alerte de
  dépréciation de **torchaudio** (interne à coqui-tts, sans effet sur le son,
  constatée par Laurent dans la fenêtre du moteur) est **tue** par un filtre
  ciblé — les vrais avertissements passent toujours — et les interrogations
  `GET /sante` (le voyant du lecteur, toutes les 5 secondes) ne s'affichent
  plus. Le reste (générations, `/recharger`, arrêt du gardien de console)
  reste visible. *Vérifié* : filtre reproduit hors service sur le message
  exact de torchaudio (bien tû, alors qu'un autre avertissement s'affiche) ;
  `py_compile` des deux services et `test_voix/test_start_moteur.py` au vert.

- **Lancement groupé lecteur + moteur Kyutai** (12/09/2026) : `START.bat`
  allume désormais le moteur de voix **en même temps que le lecteur** — un
  seul lancement, y compris depuis l'application du téléphone (via
  `<dossier du lanceur>\launcher.py`, qui appelle `START.bat`). Trois protections
  contre les lancements en double, et un bug corrigé au passage : sous
  Windows, Python laissait deux moteurs ouvrir le **même port**
  (`SO_REUSEADDR`) → deux modèles chargés, **7,7 Go de carte graphique sur 8**.
  Le moteur refuse maintenant de démarrer deux fois, et son port s'ouvre
  **avant** le chargement (détection fiable dès la première seconde).
- **Fermer la fenêtre du moteur éteint vraiment le moteur** (12/09/2026) :
  constat que ce n'était PAS le cas (sous Windows Terminal, le moteur
  continuait de tourner, port occupé et 3,8 Go de carte graphique, alors que
  la fenêtre avait disparu). Un gardien intégré au service
  (`_surveiller_la_console`) détecte la disparition de la fenêtre et arrête
  le moteur proprement — geste naturel, sans script d'arrêt. Test :
  `test_voix/test_gardien_console.py`.

- **4ᵉ moteur de voix : Kyutai TTS 1.6B** (12/09/2026) — moteur lancé à part
  (`kyutai_service/`, Python 3.12 + PyTorch, `DEMARRER_KYUTAI.bat`), **35 voix
  françaises libres** (CC BY 4.0) disponibles dans les menus du narrateur et du
  casting via la branche `kyutai:`, vitesse et hauteur post-traitées (le moteur
  n'en a aucune en natif), cache disque comme Kokoro/Piper, et message clair si
  le moteur est éteint. Le lecteur reste sur Python 3.14, sans PyTorch.
  **Voix étiquetées à l'écoute** (12/09/2026) : 17 féminines / 18 masculines,
  1 à 3 étoiles, 1 écartée, chacune avec un **prénom français** (aucun en
  double avec Edge/Kokoro/Piper), le drapeau et le genre affichés dans les
  menus — et elles passent **en tête du pool automatique du casting**.

- **Lecture phrase par phrase** : surbrillance posée au démarrage réel de
  l'audio, fin de l'estimation `timeupdate` (session 08/09/2026).
- **Prefetcher de fond** en continu (fenêtre glissante ~5000 caractères,
  parallélisme 2) + reprise réseau automatique (`waitUnitNetworkRetry`).
- **Cache audio serveur** 20 Go (`modules/tts_cache.py`, purge LRU, quota
  réglable via `NIMM_TTS_CACHE_GB`).
- **Rognage des silences de bord Edge** (`modules/audio_trim.py`, via le
  ffmpeg embarqué d'`imageio-ffmpeg`, appliqué avant mise en cache).
- **Verrous d'inférence Kokoro/Piper** (thread-safe) côté serveur.
- **Casting** : pool automatique ouvert aux 54 voix Kokoro (triées par note),
  seuil des petits rôles passé de 3 à 8 répliques, Piper retiré du pool auto.
- **Re-cast gratuit d'un livre déjà casté** (12/09/2026) : verrou 🔒 par
  personnage dans la fenêtre du casting + bouton « Re-caster (gratuit) » ;
  redistribue les voix non verrouillées dans le catalogue courant sans
  aucun appel IA (le « qui parle » et le pitch/vitesse sont conservés).
- **Regroupement des doublons d'écriture** (12/09/2026) : bouton « Regrouper
  doublons » dans la fenêtre du casting → les variantes d'un même nom
  (accents, tirets, article en trop) sont rattachées à une seule fiche, avec
  la même voix de base, sans rien supprimer (réversible via ✂). Chaque alias
  garde sa propre voix, modifiable indépendamment.
- **Outil piper-tagger** (tagging H/F des voix Piper) + `piper_gender_tags.json`.
