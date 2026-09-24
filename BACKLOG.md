# BACKLOG — NIMM ePub

Backlog des améliorations à faire, notées au fil des sessions.
**Convention (voulue par Laurent) : on traite les items un par un, par
priorité, à raison d'une ou deux par session — jamais tout d'un coup.**

- Cocher `[x]` quand l'item est livré.
- Les détails techniques des items livrés sont documentés dans ARCHITECTURE.md.
- Depuis le **22/09/2026**, un item livré tient sur **une seule ligne** (titre +
  date) : ils sont rangés à la fin du fichier, section « ✅ Déjà livré », et les
  leçons qu'ils portaient sont gardées avec eux. **Ce qui reste à faire est donc
  toujours en haut**, dans les sections de priorité — c'est la liste de travail.

---

## 🚩 À FAIRE EN PRIORITÉ — décidé le 22/09/2026

- [x] **🚑 Les 53 morceaux qui étaient DANS une réplique en tiret — ✅ FAIT le
  23/09/2026 à 15 h** (note urgente de Claude, confirmée par la mesure).
  *La cause* : `_beat()` refuse un morceau qui contient `«`, mais une **réplique
  en tiret** n'en contient pas — elle a un verbe de parole et le morceau suivant
  commence par `«` (chez Dumas : la première réplique est entre `«`, les
  suivantes en tiret). Elle a donc été prise pour un beat et **remise au
  narrateur**. *Mesure* (`_essais/_mesurer_dans_la_replique.py`) : **134**
  morceaux sont dans une réplique en tiret (dont **79 préexistants** — Claude
  annonçait ~80 sur les 173), et **81 sont déjà au personnage**. Restent **53**
  à réparer : **14** par la migration du 23/09 et **39** par le **rattrapage des
  beats** du même jour (celui-ci a fait cette erreur parce qu'il ne testait que
  la tête du morceau). *Outil prêt* : `test_voix/_restaurer_hors_replique.py`
  (simulation : **53**, exemples tous justes — Caderousse, Karla, Dunk,
  Grongoire, « Le narrateur » de Shantaram) — il **restaure l'étiquette
  d'origine** de la copie `bak_avant_dialogue_20260922_1311`, ce n'est pas un
  nouveau casting : copie datée avant, contrôle après. *Règle à intégrer
  ensuite* (étape 4 de Claude) : `dans_la_replique(ligne, position)` — une ligne
  à tiret est une citation ouverte jusqu'à son `»` — et elle **remplace le
  garde-fou G1** de R8, sans son coût de prudence.
  *Fait le 23/09/2026 à 15 h* : **53 morceaux rendus à leur personnage** (copie
  datée `nimm_epub.db.bak_avant_restauration_repliques_20260923_1459`), et le
  contrôle des phrases hors casting sur trois états (22/09, avant restauration,
  actuel) montre que **la restauration n'a inventé aucune étiquette** (107 → 103
  pour le T2, 136 → 131 pour le T6, 306 → 303 pour Notre-Dame : ce sont des
  états **préexistants**, du casting, pas du découpage).

- [ ] **🎧 Les répliques en tiret attribuées au narrateur — 147 morceaux**
  (retour d'écoute de Laurent, 23/09/2026 : « – Ah bah ! » lu par le narrateur
  dans *Notre-Dame*, ch. 28). **Décision de Laurent le même jour : on ne touche
  à rien pour le moment** — ce livre a peut-être été casté par un modèle moins
  bon que Gemini (« un livre *DeepSeek* », dit-il), et son étiquetage d'origine
  est douteux par endroits : mieux vaut ne pas corriger au coup par coup tant
  qu'on ne sait pas si c'est un défaut isolé ou une **famille**. L'outil de
  correction ciblée est prêt pour le jour où on voudra
  (`test_voix/_corriger_locuteur.py` + `CORRIGER_UN_MORCEAU.bat`).
  *Mesure* (`_essais/_mesurer_repliques_tiret.py`) :
  **147** morceaux commencent par un tiret **et** appartiennent au narrateur, dont
  **71** courts et exclamatifs — mais l'essentiel des 147 sont des **digressions
  de l'auteur** (« – Ce qui prouve cette vérité neuve : … ») ou des tirets de
  continuation : **aucune règle simple ne tranche** (« tiret = réplique » est
  faux ici). *Diagnostic* (`_essais/_diagnostiquer_passage.py` : les trois états
  de la base donnent le **même** résultat) : le défaut vient de **l'étiquetage
  d'origine par l'IA**, pas de la migration ni du rattrapage. *En attendant une
  règle* : correction ciblée, morceau par morceau, avec
  `test_voix/_corriger_locuteur.py` (+ lanceur `CORRIGER_UN_MORCEAU.bat`,
  copie datée avant écriture). *Piste à creuser* : dans ce même passage, l'IA a
  donné à **Oudarde_Musnier** une tirade qui appartient à **Gervaise** — le nom
  de la personne **interpellée** dans la réplique (« que dites-vous donc là,
  damoiselle Oudarde Musnier ? ») trompe l'étiquetage. À mesurer comme famille.

- [ ] **🧩 Les 74 beats « impurs » + les 12 morceaux à 2ᵉ personne — suite du
  rattrapage** (23/09/2026). Le rattrapage du compteur est **fait** pour
  l'essentiel (**155** morceaux remis au narrateur — voir « ✅ Déjà livré »,
  23/09/2026). Restent deux familles, volontairement laissées de côté parce
  qu'un morceau y appartient peut-être encore au personnage :
  - **74 IMPURS** : le morceau porte la fin d'une réplique (« une seule, dit le
    Lucquois avec un soupir. », « — Fais venir trois taxis », ai-je dit… ») →
    règle **R3** (coupe en trois : la tête reste au personnage, l'incise part
    au narrateur ; si aucun point de coupe, on ne coupe pas) ;
  - **12 à 2ᵉ PERSONNE** : « Si elle avait commis un second crime, **je vous**
    dirais : » (docteur d'Avrigny, T5), « Vivant, mes meilleurs amis évitent ma
    maison… » (Morrel, T2), « Rappelle-toi ce que nous a dit si souvent notre
    bon père : » — des morceaux de **discours** : à relire un par un à l'oreille
    avant de décider.
  *Outil* : `test_voix/_rattraper_beats_derive.py --avec-impurs --avec-personne`
  (simulation par défaut, puis `--ecrire`). Les deux listes sont déjà écrites :
  `_essais/_rattrapage_simu5.txt`.
  *Réponse chiffrée à Claude, à transmettre* :
  `REPONSE_DE_CLINE_a_Claude_20260923.md`.

- [ ] **🧪 Les règles proposées par Claude (23/09/2026) : état des mesures**
  (une règle à la fois, chacune avec son chiffre **et** la lecture de ses cas).
  - **R1 — compteur par paragraphe** : ✅ **LIVRÉ le 23/09/2026** — compteur
    corrigé dans `_migrer_index_dialogue.py` (`--livre 18` passe de 68/7 à
    71/4, ce qui valide le correctif), et **155** morceaux rattrapés sur les
    livres déjà migrés. Restent les 74 impurs (R3) et 12 à 2ᵉ personne.
  - **R2 — terminaisons verbales strictes** : ⛔ **écarté, mesuré deux fois**.
    Avec sa liste **complétée** (il a reconnu l'oubli de `u`, `us`, `ut`, `s`,
    `ient`, `îmes`, `îtes`), R2 perdrait **23** beats sur les 166 détectés par
    verbe — et **21 des 23 sont des cas où le narrateur est JUSTE** (« Vivant,
    mes meilleurs amis évitent ma maison », « Guillaume Rym crut devoir
    intervenir. », « Heureusement la discrète damoiselle… ») : c'est de la
    **narration que l'IA avait donnée à un personnage**. Donc R2, même corrigé,
    **retire des corrections utiles**. *Son compromis, retenu* : R2 complet +
    une **liste noire COURTE** des vrais verbes non-parole (*exige*, *repris*).
    Chiffres : `_essais/_mesurer_demandes_claude.py`.
  - **R4 — 2e personne** : ✅ **retenu, `ton / ta / tes` sortis** (homographes du
    nom commun : « d'un **ton** sec » = 4 des 5 cas de Notre-Dame). Ce filtre est
    celui qui a sauvé les 12 morceaux de **discours** du rattrapage.
  - **R5 — mode par livre (+ score)** : ✅ **retenu**. Le score proposé
    (« entretien si narration < 20 % **et** deux locuteurs > 15 % ») classe
    parfaitement nos livres : **seul le livre 18 sort en « entretien »**. *À
    figer dans un test avec les 11 livres comme cas gelés* ; **réserve de
    Claude acceptée** : un **roman épistolaire** serait classé « entretien » à
    tort (le bouton corrige d'un clic). Chiffres :
    `_essais/_mesurer_score_mode_livre.py`.
  - **R6 — dans le doute, hériter** : ✅ **retenu** — c'est la **variante A** qui
    existe déjà dans l'outil de migration (option à brancher, pas une
    réécriture).
  - **R3 — beat impur (coupe en trois)** : à faire, **75 cas mesurés** (plus que
    l'estimation de Claude, qui venait du document et non d'une mesure), avec le
    garde-fou « si aucun point de coupe, ne pas couper ». **À lire en premier**
    (demande de Claude) : ceux qui contiennent un `»` sans commencer par une
    minuscule ni par `»` — c'est un **troisième motif** qu'il n'avait pas prévu,
    et il faut savoir où couper dans ces cas-là.
  - **R7 — citation refermée dans la phrase** : à mesurer (coupes annulées).
    **Ordre décidé : R7 AVANT R3** (argument de Claude, retenu) — R7 **annule**
    des coupes, donc il réduit ce que R3 a à traiter ; R3 en ajoute.
  - **R8 — ré-étiquetage STRUCTUREL des préexistants** : ⏸️ **mesurée deux fois,
    PAS EN BASE avant relecture**. L'idée de Claude : la liste de verbes fait
    deux métiers (couper un morceau mixte / ré-étiqueter un morceau
    **préexistant** suivi d'une citation) ; pour le second, le verbe est un
    critère **parasite** (« Le roi se leva. » suivi d'une citation est de la
    narration). *Première mesure* : 161 morceaux, dont beaucoup sont de la
    **vraie narration** (« Valentine poussa un gémissement. »). *Puis Claude a
    relu le surplus **ligne par ligne** et a trouvé qu'environ **un tiers est
    faux**, en deux familles : (1) des **textes LUS par un personnage**
    (testament, acte, lettre de mourant, signalement — propriété 5 du document) ;
    (2) la **deuxième phrase d'une réplique en tiret** (« — Oui. Ils me
    haïssent… »). *Ses trois garde-fous, mesurés* :
    **G1** (la **LIGNE** du morceau ouvre un dialogue) → 82 ;
    **G1+G2** (1re personne dans un livre à la 3e personne) → 74 ;
    **G1+G2+G3** (le morceau suit un bloc du même locuteur) → **56**.
    **105 retenus sur 161**, et les témoins survivent. G2 (8 retenus, tous
    justes) et G3 (18, tous justes) sont excellents ; **G1 est conservateur** —
    il retient aussi de la vraie narration, parce qu'une même ligne peut
    contenir la réplique **puis** du récit : indiscernable localement, donc on
    protège. *Chiffres* : `_essais/_mesurer_r8_garde_fous.py` ; *relecture* :
    `_essais/POUR_LE_LLM/r8_garde_fous.txt` (les 56), `r2_textes_complets_T5_T3.txt`,
    `preexistants_173.txt`. *Colonne à ajouter au rapport* :
    `ORIGINE = coupe | verbe | structure`. *Shantaram* : 2 morceaux seulement.
  - **Compteurs `NE_DE_LA_COUPE` / `PREEXISTANT`** : ✅ **mesurés** — sur les
    **896** beats, **723 nés de la coupe** et **173 préexistants** : c'est la
    mesure que Claude demandait (« combien de narration l'IA donne aux
    personnages »). Verdict : **0,2 % des 81 000 phrases** seulement, donc **le
    casting n'a pas un problème massif** — et ces 173 morceaux-là, invisibles à
    la règle (ils n'introduisent aucune citation), montrent que le vrai sujet
    restant est **la qualité de l'étiquetage par l'IA**, pas la découpe.

- [ ] **🔄 « Dialogues désaccordés » (livre 18) en narration séparée — EN ATTENTE
  D'UNE RÈGLE** (décision de Laurent, 23/09/2026). Les **9 autres** livres déjà
  castés sont **faits** (voir « ✅ Déjà livré », 23/09/2026 — **327 morceaux**).
  Ici, la **lecture des beats** (la leçon du 21/09 : un chiffre ne vaut rien sans
  la lecture du texte) a montré que les **68** morceaux proposés ne sont **pas**
  de la narration : ce sont les paroles du personnage qui introduit une citation —
  « En prologue de ces entretiens, j'ai donc entrepris de te lire… » (Naulleau),
  « Première remarque : j'ai passé sept ans au PC… » (Interlocuteur). Mesure :
  **narration 11,8 %** du livre, contre 36,1 % Naulleau, 33,7 % Interlocuteur,
  18,3 % Soral. La règle actuelle regarde la **forme** (deux-points ou verbe de
  parole) et ne peut pas savoir **qui parle** : elle donnerait ces 68 passages au
  narrateur et **couperait la voix du personnage en deux** (leçon de Lazarille).
  *Ce qui est prêt pour reprendre* : l'outil `test_voix/_migrer_index_dialogue.py
  --livre 18` (simulation, aucun frais) et la **problématique complète** rédigée
  pour être soumise à un autre assistant : `PROBLEMATIQUE_decoupage_voix.md`
  (mécanique actuelle, cas traités, cas qui résistent, jeu d'essai de 10 exemples
  réels). *Pistes déjà identifiées* : personnes grammaticales (`je` / `tu`) dans
  le morceau, mode « roman / entretien » par livre, et détection des guillemets
  non français (« " " ») pour que le garde-fou « citation ouverte » fonctionne
  aussi dans ce livre.

- [ ] **📄 AUDIT d'`ARCHITECTURE.md` — étape 1 FAITE le 22/09/2026 (titres + sommaire) ; le reste à trancher**
  (décidé par Laurent le 22/09/2026 : « Je vais ouvrir une nouvelle session pour
  l'audit de ARCHITECTURE.md, parce que je me suis encore éparpillé dans
  celle-ci. » → **cette note existe pour qu'on démarre directement dessus**.)
  *Ce qui est déjà fait (22/09/2026)* :
  - le **BACKLOG** est réduit (items livrés en une ligne : 490 Ko → 270 Ko) et
    rangé ; l'**outil d'audit** existe : `test_voix/AUDITER_DOCUMENTATION.bat`
    (double-clic, **lecture seule**) — il compare les documents au **code** :
    fichiers cités disparus, identifiants (fonctions, constantes) disparus,
    routes absentes de `main.py`, colonnes absentes de la base, tests disparus,
    items du BACKLOG déjà livrés ;
  - cinq dérives réelles ont été corrigées (dont une contradiction sur
    `_forcer_beats_en_narration`, un nom de fonction qui n'a jamais existé,
    l'item « cache audio » resté ouvert alors qu'il était livré).
  *Consigne de Laurent, 22/09/2026 — c'est elle qui fixe l'objectif* :
  « Idéalement, ce que je voudrais, c'est que ce document **TE** soit utile. Il
  faut qu'il soit "pratique" à lire pour **TOI**. C'est un peu un journal de
  bord, mais qui doit **t'aider dans les recherches**. Je ne le lis pas, je l'ai
  créé au début pour toi, mais il devient très gros et peut être pas pratique à
  lire pour toi. Si tu peux le réorganiser pour qu'il te serve mieux, je m'en
  remets à ta décision. » → **c'est un document de travail pour l'IA, pas un
  livre pour Laurent.**
  *Étape 1, LIVRÉE et prouvée (22/09/2026)* — la structure des titres, **sans
  déplacer une seule ligne de contenu** :
  - **42 titres réparés** : les **34 `###` qui étaient des SUJETS à part** et se
    trouvaient imbriqués sous « Profils familiaux (multi-utilisateurs) »
    (ligne 1512) passent en `##` — cette section n'avale plus 2 740 lignes
    (61,5 % du fichier) mais **70 lignes**, et **la plus grosse section du
    document passe de 2 740 à 416 lignes** ;
  - les **8 sujets écrits en gras** au milieu d'une autre section (banque de
    voix, paliers d'étoiles, symboles de genre, ordre du pool, NIMM Voix,
    détail de `voice_casting.py`…) deviennent de **vrais titres** ;
  - **un sommaire en tête** (63 entrées, **calculé** depuis les titres) et un
    **mode d'emploi du document** : « état actuel = phrases sans date, histoire
    = passages datés, identifiants du code en accents graves » ;
  - **aucune ligne de contenu touchée** : l'outil `_restructurer_architecture.py`
    tient la comptabilité des **4 453 lignes** d'origine — 4 409 inchangées
    + 42 titres + 2 remplacées — et **refuse d'écrire** si le compte ne tombe
    pas juste. Copie datée :
    `ARCHITECTURE.md.bak_avant_audit_structure_20260922_1413` ;
  - **vérifié APRÈS** : l'audit redonne **exactement les mêmes 11 références**
    (seuls les numéros de ligne ont bougé), les **40 tests passent**, et le
    contrôle du sommaire est **branché dans l'auditeur** (section 7 : sommaire
    conforme ; plus grosse section sous le seuil de 500 lignes).
  *Deux chiffres de cette note, corrigés par la mesure* : elle annonçait
  **108 `##` et 87 `###`** (le vrai compte était **21 `##`, 85 `###`**), et
  « une table des matières qui ne correspond pas au contenu » — en réalité il
  n'y avait **aucun sommaire**. *(Honnêteté technique : un chiffre faux dans une
  note fait perdre une session.)*
  *Réponse technique à retenir* : **les autres documents renvoient aux sections
  de `ARCHITECTURE.md` par leur TITRE**, jamais par un numéro de ligne —
  vérifié le 22/09/2026 (`BACKLOG.md` renvoie à « Mode dialogue », « Lire écran
  verrouillé », « Accès HTTPS via Tailscale »…) → **on ne renomme jamais un titre
  de cette page** sans corriger tous les renvois.
  ⚠️ **Et la vérité sur le fond : rien à réparer.** Les 11 références qui
  touchent `ARCHITECTURE.md` (dont `books.narrator_rate`, `_xtts_pool`,
  `_sans_fenetre`, `_remplirMenuVoixPhrase`) sont **toutes légitimes** : le
  document raconte lui-même qu'elles ont été écartées ou renommées (« piste
  écartée », « les anciennes… », « ex-… »). C'est donc un travail de
  **lisibilité**, pas de vérité — exactement ce que la note supposait.
  ⚠️ **LA QUESTION CAPITALE DE LAURENT (22/09/2026)** : « Est-ce que ce qui est
  écrit dans ce document reflète réellement l'état du code ? C'est un point
  capital. » **Réponse mesurée, pas une opinion** — et il faut savoir ce que
  l'audit du matin ne voyait pas : il vérifie les **NOMS** (le fichier cité
  existe, la fonction citée existe, la route existe, la colonne existe), il ne
  vérifie **jamais si la phrase dit vrai**. Nouveau contrôle livré :
  `_verifier_faits_architecture.py` (racine, **lecture seule**) — il confronte
  au code les **phrases vérifiables** : plan du dossier, **constantes citées
  avec leur valeur**, ports, fichiers de données, version de cache. Verdict :
  - ✅ **fidèles** : les constantes (`MINOR_THRESHOLD` = 8, `NARRATEUR_VOIX_DEFAUT`
    = `fr-CH-ArianeNeural`, le seuil des petits rôles identique dans les deux
    codes), **les cinq ports** (8081 à 8085), les **fichiers de données**
    (`config.json`, `moteur_voix.txt`, `annotations_voix.json`, la base), la
    **version de cache** de la page, et **les 11 références** de l'audit
    (vérifiées une par une) ;
  - ❌ **une vraie dérive, invisible jusqu'ici** : le **plan du dossier** en tête
    du document datait de plusieurs sessions — il oubliait **5 modules sur 12**
    (`decoupage.py`, `incises.py`, `silence.py`, `majuscules.py`,
    `prononciation.py`), **4 dossiers** (`test_voix/`, `xtts_service/`,
    `neutts_service/`, `pocket_tts_service/`), la description de `tts.py`
    s'arrêtait à **4 moteurs sur 7**, et `manifest.json` avait **déménagé** dans
    `frontend/` sans que le plan le suive. **Corrigé le 22/09/2026** : le plan
    compte maintenant **59 entrées, toutes vérifiées existantes** — et le
    vérificateur le contrôle à chaque passage ;
  - ⚠️ **une nuance** : le doc écrivait `PERSONNAGE_RATE_DEFAUT` = « Normale »
    quand le code porte `'+0%'` (c'est le **libellé** du réglage, pas sa
    valeur). Reformulé.
  *Leçon à garder* : **le plan du dossier échappait à tous les contrôles**
  parce qu'il est écrit sans accents graves — un audit qui ne lit que ce qui
  est entre `` ` `` laisse passer tout le texte en prose. C'est pourquoi ce
  deuxième outil existe.
  *Les trois étapes — état au 22/09/2026 (soir)* :
  1. ✅ **FAITE — déménagement.** Les pistes du 21/08 et les **deux idées RSVP**
     sont ici (deux items créés), les **quatre notes périmées** ont été retirées,
     et les renvois recousus (dont un renvoi de ce BACKLOG vers
     `ARCHITECTURE.md`, qui serait devenu mort). Outil :
     `_demenager_pistes_architecture.py`. **Découverte au passage** : la note
     « Profil Nadia créé » cachait un **fait faux** — le document disait
     « Laurent et Maya » à trois endroits, alors que la base a **3 profils**
     (`init_db()` insère Nadia depuis le 21/08/2026) ; corrigé.
  2. ✅ **FAITE — regroupement en parties.** Les **61 sujets** sont rangés en
     **10 parties** (projet, serveur, page, texte lu, casting, voix, moteurs,
     mode dialogue, écoute, historique), le **sommaire suit**, et le contenu de
     chaque sujet est **identique au caractère près** — preuve affichée par
     `_regrouper_architecture.py`, qui refuse de tourner deux fois. Un renvoi
     devenu inutile a été retiré (« Profils familiaux — renvoi »). **Aucun titre
     n'a été renommé** : les renvois des autres documents (« Mode dialogue »,
     « Lire écran verrouillé »…) fonctionnent toujours.
  3. 🔄 **EN COURS — état actuel / chronique.** Chaque sujet doit commencer par un
     bloc « **Aujourd'hui** » **court et vérifiable**, la chronique datée restant
     dessous ; **11 sujets sur 61** sont faits (le narrateur, le changement de
     moteur, le mode dialogue, **« Logique TTS — app.js »**,
     **« modules/tts.py — Synthèse vocale »**, **« frontend/ — Interface »**,
     **« 🎒 Moteur de voix Pocket TTS »**, **« Report des notes d'écoute dans les
     catalogues »**, **« 🎭 Distribution de voix par personnage (IA) »**,
     **« Symboles ♀️/♂️ de genre devant les prénoms »** et **« 🔒 Lire écran
     verrouillé »**) et le vérificateur de faits compte l'avancement (sa
     section 8).
     **Un sujet par session**, à poursuivre : c'est ce chantier qui répond
     définitivement à la question « le document dit-il la vérité ? », parce que
     c'est lui qui rend l'état actuel **court, nommé et vérifiable**.
     *Session du 23/09/2026 — sujet fait : « Logique TTS — app.js », un bloc de
     **44 lignes** (10 constats + les tests : structures de phrases, vitesse par
     fiche, préchargement et « réserve à bloc », phrases-fleuves, pause, réseau,
     états, mobile, navigation, tiroir).*
     *Session du 23/09/2026 (le soir de la même journée) — sujet fait :
     **« modules/tts.py — Synthèse vocale »**, un bloc de **60 lignes**
     (9 constats + les tests : les sept moteurs et l'aiguillage par préfixe, les
     services à part et leurs 503, le nettoyage du texte, les phonèmes de Kokoro,
     vitesse et hauteur, le niveau de la parole, le cache, les catalogues), et
     **deux vraies dérives corrigées** : le sujet annonçait « les **quatre**
     moteurs de voix » alors que le module en porte **sept** (le tableau du Rôle
     ne listait ni **NeuTTS** ni **Pocket**), et trois comptes de voix étaient
     périmés — Kokoro **84 → 94** (les voix allemandes du 20/09), XTTS **60 → 79**,
     NeuTTS et Pocket **absents**. Les comptes sont maintenant **mesurés**
     (`_essais/_mesurer_voix_tts.py`) **et contrôlés** : la **section 9** du
     vérificateur de faits lit le tableau du Rôle et compare chaque nombre au
     catalogue du code. **Preuve** (`_essais/_preuve_controle_tts.py`) : le
     contrôle **crie 5 fois** sur la copie d'avant la session, et **se tait** sur
     le document d'aujourd'hui. Le sujet passe de 347 à **410 lignes** (sous le
     seuil de 500).
     *Session du 23/09/2026 (fin de soirée) — sujet fait : **« frontend/ —
     Interface »**, un bloc de **48 lignes** (9 constats + les tests : les quatre
     vues, les trois fichiers, le service worker, la PWA et ses icônes, le bouton
     d'installation, la grille de la bibliothèque, le chargement d'un chapitre,
     l'accès), et **deux vraies dérives corrigées** :
     - le sujet annonçait « **Deux vues dans une seule page** » (bibliothèque et
       lecteur) alors que la page en porte **quatre** : `view-profile` (« Qui
       lit ? », arrivé avec les profils familiaux) et `view-rsvp` (le mode RSVP)
       n'étaient jamais comptés ici — chacun documenté dans sa partie, mais le
       sujet qui décrit la page disait faux depuis le 20/08 ;
     - le bouton « Installer l'application » a une **troisième** raison de
       disparaître, jamais écrite : `_majBoutonInstaller()` le cache aussi **sur
       ordinateur** (`_appareilMobile()`) depuis le 20/09/2026.
     **Nouveau contrôle** : la **section 10** du vérificateur de faits lit le bloc,
     compte les vues réelles dans `index.html`, les retrouve dans `showView()`,
     compare `CHARGEMENT_ESSAIS` / `CHARGEMENT_PAUSE_MS` au code et exige que les
     quatre fonctions du bouton soient nommées. **Preuve**
     (`_essais/_preuve_controle_vues.py`, lecture seule) : le contrôle **crie
     4 fois** sur la copie d'avant la session, et **se tait** sur le document
     d'aujourd'hui. Le sujet passe de **228 à 300 lignes** (sous le seuil de 500).
     ⚠️ **La leçon de ce sujet** : **aucun test ne couvrait les vues** — c'est le
     trou qui a laissé passer la dérive pendant cinq semaines. Le contrôle neuf ne
     teste pas la page (ce n'est pas son rôle), il empêche le **document** de
     raconter autre chose que le code.
     *Session du 23/09/2026 (la suite de la suite) — sujet fait : **« 🎒 Moteur de
     voix Pocket TTS »**, un bloc de **58 lignes** (onze constats + les tests : le
     service et ses quatre routes, la double préparation du texte, le verrou et
     les cœurs, l'auto-extinction, le catalogue et ses fichiers de voix, le tic
     corrigé à la source, le niveau, la cohabitation et le veilleur, l'arrêt
     volontaire, la page, le modèle), et **trois dérives corrigées** :
     - **« 100 M de paramètres »** — c'est le chiffre des variantes **légères** de
       Pocket TTS (`config/english.yaml` : **6 couches**). Le modèle que NIMM ePub
       utilise, `french_24l`, en porte **336 M** (**24 couches**), mesuré le
       23/09/2026 dans l'en-tête de `model.safetensors` (358 tenseurs, BF16,
       641 Mo) — **sans rien charger** : l'outil lit l'en-tête du fichier de poids ;
     - **« Sixième moteur »** — le lecteur en compte **sept** (Edge compris), et
       Pocket est le **quatrième « lourd »**, après Kyutai, XTTS et NeuTTS, comme
       le disent les sujets voisins ;
     - **« la vérification de l'accent des 18 voix »** (« Ce qui reste ») — le
       catalogue est passé à **28 voix** le 23/09/2026, et les dix nouvelles ont
       le **même** trou : un accent `neutre` posé par l'outil, jamais entendu.
     Deux endroits portaient le même « 100 M » et ont été corrigés au passage : le
     tableau du Rôle du sujet `modules/tts.py` et `pocket_tts_service/LIRE_MOI.md`.
     **Nouveau contrôle** : la **section 11** du vérificateur de faits vérifie le
     **nombre de voix** du catalogue, que **chaque voix a son WAV**
     (`pocket_tts_service/voix/` : 28 fichiers, **aucun manquant, aucun
     orphelin**), les **cinq constantes** du service (`NIVEAU_MINI`, `ESSAIS_MAX`,
     `PORT`, `COEURS`, `INACTIF_MIN`), le drapeau **`cohabite`** de `MOTEURS_VOIX`,
     l'ancien nom `_sans_fenetre` (le sujet l'écrit « ex- ») et le **nombre de
     paramètres** lu dans le poids. **Preuve**
     (`_essais/_preuve_controle_pocket.py`, lecture seule) : le contrôle **crie
     6 fois** sur la copie d'avant la session et **se tait** sur le document
     d'aujourd'hui. Le sujet passe de **173 à 254 lignes** (sous le seuil de 500).

     *Session du 23/09/2026 (fin de soirée) — sujet fait : **« Report des notes
     d'écoute dans les catalogues »**, le plus utile de la série parce qu'il
     prolonge le travail de Laurent sur ses notes d'écoute.* Il s'ouvre par un
     bloc « Aujourd'hui » de **57 lignes** (le report, l'outil, la barre d'état,
     les voix libres, la recherche) et il a demandé **quatre corrections** —
     deux chiffres et deux affirmations :
     - **« les trois boutons »** de la barre d'état : il y en a **quatre** depuis
       le 19/09/2026 (« 🔓 Voix libres ») — et `test_ids_ecran.py` vérifiait déjà
       les quatre : c'est le **document seul** qui était en retard ;
     - **« 175 personnages »** pour le livre de référence : **176** aujourd'hui
       (relevé en base), et le test disait déjà 176 ;
     - **« Jake Epping (3 634 répliques) »** : **3 615** (relevé en base) ;
     - **« une voix portée par dix-huit personnages dans 22/11/63 »** : la plus
       grande famille **hors voix génériques** en porte **3** (`kokoro:fm_papi`) ;
       les 67 porteurs de `piper:upmc:1` sont la voix générique des petits rôles,
       comptée à part. Le chiffre vivait **aussi dans un commentaire du code**
       (`frontend/app.js`) : corrigé là également, et **sans chiffre** — un
       chiffre écrit dans un commentaire redevient faux au re-cast suivant.
     **Ce que la mesure a trouvé** (`_essais/_mesurer_faits_notes.py`, lecture
     seule) : **360 voix annotées**, **356 reportées** (l'aperçu répond « TOUT EST
     À JOUR »), **une seule** voix du catalogue jamais annotée — `pocket:JEAN_EDGAR`
     (Edgar), laissée à l'oreille de Laurent — et **quatre notes Piper** hors
     catalogues (`piper:siwis:0`, `piper:tom:0`, `piper:upmc:0`, `piper:upmc:1`) :
     rien à reporter pour elles. **Détail sans conséquence** : dix notes Pocket
     portent `M` (convention des catalogues) au lieu de `H` — la conversion ne
     connaît que H/F, donc le genre du catalogue est conservé tel quel, et la page
     lit `M` comme « homme ».
     **Nouveau contrôle** : la **section 12** du vérificateur de faits tient les
     faits **stables** du sujet (l'outil de report et ses garde-fous, les **six**
     catalogues balayés, le **nombre de boutons** de la barre d'état, les **deux**
     seuils et les **deux** voix génériques, le **plafond de six noms**, et le
     nombre de contrôles annoncé pour les **trois** tests JavaScript). **Preuve**
     (`_essais/_preuve_controle_notes.py`, lecture seule) : le contrôle **crie
     neuf fois** sur la copie d'avant la session — dont une fois sur les « trois
     boutons » — et **se tait** sur le document d'aujourd'hui. Le sujet passe de
     **162 à 239 lignes** (sous le seuil de 500).

     *Session du 23/09/2026 (le neuvième sujet, le plus gros des restants) —
     sujet fait : **« 🎭 Distribution de voix par personnage (IA) »**, un bloc
     « Aujourd'hui » de **60 lignes** (les quatre moteurs et le défaut, le repli
     automatique, l'estimation avant paiement, les deux passes, les paquets de
     150 phrases, la reprise qui ne repaie jamais un chapitre, le découpage avant
     l'IA, les huit colonnes de `voices`, la voix décidée à la lecture, les onze
     routes, les clés et la configuration du moteur local, les tests). C'est le
     sujet qui portait **le plus de dérives de tout l'audit** — cinq :
     - **« DeepSeek par défaut »** était faux : depuis le 23/08/2026, c'est
       **Gemini** le défaut et le bouton « recommandé » — et le sujet voisin
       « 🔀 Système multi-moteur » le disait déjà : deux pages du **même**
       document se contredisaient ;
     - **le modèle local (Ollama)** — arrivé le **13/09/2026** — n'était **nulle
       part** dans `ARCHITECTURE.md` (zéro occurrence du mot « Ollama ») : le
       sujet annonçait un système à **trois** moteurs qui en compte **quatre** ;
     - **une seule route** décrite là où le code en porte **onze**
       (`/cast/estimate`, `/cast/voice`, `/cast/lock`, `/cast/reassign`,
       `reassign_ia`, `autogroup`, `ungroup`, `group`, `propagate-saga`…), plus
       `GET /api/llm/local` ;
     - la table `voices` annoncée à **quatre** colonnes : elle en porte **huit**
       (`genre`, `line_count`, `rate` et `locked` en plus) ;
     - des attributs `data-voice` / `data-pitch` posés « sur chaque `<span>` » qui
       n'existent **nulle part** dans la page — la voix d'une phrase se décide
       **à la lecture** (`_voiceForSentence`), seul `data-idx` est gravé.
     **Nouveau contrôle** : la **section 13** du vérificateur de faits tient ces
     faits-là (les quatre moteurs et leur aiguillage, le défaut, le repli
     `MOTEURS_DE_SECOURS`, les **onze** routes comparées une par une, les **huit**
     colonnes de `voices`, l'absence de `data-voice`, le seuil des petits rôles,
     les tests cités et leur nombre de contrôles). **Preuve**
     (`_essais/_preuve_controle_casting.py`, lecture seule) : le contrôle **crie
     17 fois** sur la copie d'avant la session et **se tait** sur le document
     d'aujourd'hui. Copie datée :
     `ARCHITECTURE.md.bak_avant_etat_casting_20260923`. Le sujet passe de **159 à
     282 lignes** (les 60 lignes du bloc, plus les notes de correction) — sous le
     seuil de 500.
     ⚠️ **Le sujet voisin reste à corriger, et c'est noté ici exprès** :
     « 🔀 Système multi-moteur — Gemini / Mistral / DeepSeek » (62 lignes) porte
     le même retard dans son **titre** (« Gemini / Mistral / DeepSeek » : le
     moteur local manque) et dans son paragraphe « Choix du moteur » (il décrit
     **trois** boutons, la fenêtre en porte **quatre** depuis le 13/09/2026).
     **Vérifié le 23/09/2026 : aucun autre document ne renvoie à ce titre** — la
     règle « on ne renomme jamais un titre de cette page sans corriger les
     renvois » s'applique donc sans risque ; à faire quand ce sujet passera, le
     sommaire recalculé au passage.

     *Session du 23/09/2026 (le dixième sujet) — sujet fait : **« Symboles ♀️ / ♂️
     de genre devant les prénoms »**, un bloc « Aujourd'hui » de **57 lignes** qui
     tient les quatre morceaux d'un même sujet composite (les symboles de genre du
     19/09, les icônes des moteurs, la mise à l'échelle des boutons de la barre du
     lecteur et le bouton « Vider le cache », tous du 20/09). **Trois dérives**,
     toutes dans le même sujet :*
     - **un tableau d'icônes qui s'arrêtait à six moteurs** : `FAMILLES_VOIX` en
       porte **sept** depuis l'arrivée de **Pocket TTS** (**🎒**) le 21/09/2026 —
       et son icône n'était contrôlée par **aucun** test (`test_ids_ecran.py`
       vérifie les six autres, une par une) ;
     - **un exemple de libellé périmé le jour même** : le sujet annonçait « ♀️ Eva
       🇩🇪 **Allemagne (NIMM Voix)** … — **Kokoro** » là où le code écrit
       « ♀️ Eva 🇫🇷🇩🇪 adulte médium — 🎎 » — les **drapeaux** remplacent le pays
       en toutes lettres, la provenance ne s'écrit plus, et le moteur est réduit à
       son **icône seule** ;
     - **une règle de style annoncée « les trois »** alors qu'elle en porte
       **six** (`#multivoice-btn`, `#voices-open-btn`, `#bookmarks-open-btn`,
       `#rsvp-open-btn`, `#cache-open-btn`, `#incises-btn`) — et le bouton du cache,
       annoncé « le prochain concerné », l'avait rejointe **le jour même**.
     Et une **quatrième dérive, dans le code cette fois** : `modules/tts_cache.py`
     annonçait « défaut : **20 Go** » dans son en-tête alors que la valeur est
     **2 Go** depuis le 17/09/2026 (le commentaire de la constante, lui, disait
     juste) — **corrigé**, et désormais **contrôlé**. Deux détails sortis en
     écrivant le contrôle : l'icône **⚡** du tableau s'écrivait **sans** son
     sélecteur emoji (le code porte `\u26A1\uFE0F`) — corrigé aux deux endroits du
     sujet ; et le **défaut `H`** de la colonne `genre` se vérifie à la **source**
     (`main.py`, la déclaration de la table), pas dans la base.
     **Nouveau contrôle** : la **section 14** du vérificateur de faits — la
     fonction des symboles et ses deux conventions `M`/`H`, les trois emplacements,
     le libellé exact, **les sept icônes comparées une par une** (c'est ce contrôle
     qui aurait attrapé Pocket), le nombre de boutons de la règle commune, les deux
     routes du cache, son quota, et les **six** tests cités avec leur nombre de
     contrôles. **Preuve** (`_essais/_preuve_controle_symboles.py`, lecture seule) :
     **10 écarts** sur la copie d'avant, **0** sur le document d'aujourd'hui. Copie
     datée : `ARCHITECTURE.md.bak_avant_etat_symboles_20260923`. Le sujet passe de
     **145 à 229 lignes** (sous le seuil de 500).

     *Session du 23/09/2026 (le onzième sujet) — sujet fait : **« 🔒 Lire écran
     verrouillé : la « réserve à bloc », et le lecteur »**, un bloc « Aujourd'hui »
     de **50 lignes** qui tient les huit constats du sujet et les tests (la vraie
     cause, qui est la batterie d'Android ; la réserve « à bloc » et ses quatre
     constantes ; les huit actions du lecteur du système ; le lecteur intégré et
     ses sept télécommandes ; le collage des phrases ; la pause venue d'ailleurs).
     **Une dérive, de la même famille que celle du casting** : le sujet annonçait
     « **160 contrôles** au total » pour `test_voix/test_ids_ecran.py` alors que la
     **même page** écrivait **168** vingt lignes plus haut — et le test en
     **exécute 168** (dont **25** dans sa seule section « 3 sexies », celle du
     lecteur). Le chiffre faux est parti ; la chronique renvoie maintenant au
     compte tenu par le bloc « Aujourd'hui ».*
     **Nouveau contrôle** : la **section 15** du vérificateur de faits — les
     quatre constantes du préchargement avec leur valeur, le déclencheur de la
     réserve « à bloc », les **huit** actions du lecteur du système, les **sept**
     télécommandes du lecteur intégré, les fonctions du collage et son filet, la
     pause venue de l'extérieur, **et le nombre de contrôles des quatre tests
     cités**, compté **par exécution** (les sections 12 et 14 comptaient les
     `verifier(` **écrits** : 22 au lieu de 42 pour le lecteur intégré).
     **Preuve** (`_essais/_preuve_controle_ecran.py`, lecture seule) : **13 écarts**
     sur la copie d'avant, **0** sur le document d'aujourd'hui ; copie datée
     `ARCHITECTURE.md.bak_avant_etat_ecran_20260923`. Le sujet passe de **130 à
     183 lignes** ; audit documentaire **78 alertes avant, 78 après** (les mêmes),
     plus grosse section **471 lignes** (sous le seuil de 500), suite complète
     **« TOUT EST OK »**.
     *Session du 23/09/2026 (le douzième sujet) — sujet fait : **« ✂️ Rognage des
     silences de bord »** (113 lignes au départ), avec un bloc « Aujourd'hui » qui
     tient les constats et les tests. C'est le sujet le plus **dépassé** de la
     série après le casting : il parlait d'un monde à **deux** rognages (Edge et
     XTTS) alors que le code en compte **trois**, dans trois fichiers différents,
     plus un moteur qui règle sa respiration au lieu de rogner. **Trois dérives** :
     - **« ~0,15 s en fin » était faux** : `modules/audio_trim.py` porte **0,35 s**
       depuis le 17/09/2026 (0,15 s au départ, 0,25 s le 15/09, puis 0,35 s le
       17/09 après l'écoute de Kyutai) — la chronique, elle, était restée au
       08/09/2026 ;
     - **« 12 contrôles »** pour `test_voix/test_rogner_babil_xtts.py` : il en
       **exécute 11** (compté en le lançant — 14 et 16, eux, étaient justes) ;
     - **NeuTTS et Kyutai manquaient au sujet** : NeuTTS **rogne** depuis le
       16/09/2026 (`rogner_queue()`, même marge de 0,25 s qu'Edge et qu'XTTS, plus
       un filet anti-dérive très large, `duree_max_derivee()`) ; Kyutai, lui, règle
       sa **respiration** de fin de phrase (`SILENCE_QUEUE_S`, ajoutée puis retirée
       le 17/09/2026 — donc **0** par défaut) ; et Pocket, qui ne rogne rien,
       **régénère** une prise trop faible (`NIVEAU_MINI` = 0,05, `ESSAIS_MAX` = 4).
     **Une quatrième correction, de vérité celle-ci** : le sujet annonçait que
     « le rognage change la **clé du cache audio** » — la clé porte en réalité
     `VERSION_CACHE` (**17** aujourd'hui) + le texte + la voix + la vitesse + la
     hauteur, et le rognage n'y apparaît nulle part : ce qui invalide un rendu,
     c'est la **version**, incrémentée à la main. Reformulé.
     **Nouveau contrôle** : la **section 16** du vérificateur de faits — les marges
     réelles du filtre d'Edge (-45 dB, 0,08 s / 0,35 s), le rognage en place
     **avant** la mise en cache, les constantes du service XTTS et ses **deux**
     filets (les bornes de longueur **recalculées** avec le code du service), le
     rognage de NeuTTS, la respiration de Kyutai, ce que Pocket fait à la place, la
     version du cache, et les **quatre** tests cités, comptés **par exécution**
     (14 / 16 / **11** / 46).
     **Preuve** (`_essais/_preuve_controle_rognage.py`, lecture seule) : **17
     écarts** sur la copie d'avant, **0** sur le document d'aujourd'hui ; copie
     datée `ARCHITECTURE.md.bak_avant_etat_rognage_20260923`. Le sujet passe de
     **113 à 164 lignes** ; audit documentaire **78 alertes avant, 78 après** (les
     mêmes), plus grosse section **471 lignes**, suite complète **« TOUT EST OK »**.
     - **Un fait à ne pas perdre** : **aucun des quatre tests** du rognage n'est
       dans la liste du **lanceur** `test_voix/lancer_tous_les_tests.py` — ils ne
       tournent que si on les appelle à la main (le piège du 21/09/2026, noté ici
       plutôt que corrigé : la liste des tests hors lanceur est un chantier à part).
     - **Mesure** : `_essais/_mesurer_faits_rognage.py` (lecture seule) refait tous
       ces relevés. ⚠️ **Piège de parcours, appris à ses dépens** : les quatre
       dossiers `*_service` embarquent chacun leur environnement Python —
       **42 626 fichiers `.py`** dans tout l'arbre. Un script qui balaie le projet
       doit s'arrêter aux dossiers de **code** (une mesure y a perdu dix minutes).
     - *Détail de méthode* : les deuxième et troisième mesures du script ont montré
       que **lire une constante ne va pas de soi** — celles des services s'écrivent
       aussi sur deux lignes (`float(os.environ.get("NIMM_...", "0.0"))`), et il a
       fallu **écrire un vrai script** plutôt qu'un `findstr` : la mesure d'un
       sujet est un outil, pas une commande jetable.


     - **Leçon de comptage, gardée avec le onzième sujet** : le nombre de contrôles
       d'un test ne se lit pas dans son texte. `test_lecteur_media.js` écrit **22** appels
       `verifier(` et en **exécute 42** (les boucles des sept télécommandes et des
       quinze identifiants de la fenêtre) ; `test_ids_ecran.py` passe de **70** à
       **168**. C'est la raison du contrôle par exécution de la section 15. Les
       chiffres du sujet se remesurent avec `_essais/_mesurer_faits_ecran.py`
       (lecture seule : il lance les quatre tests et compare au document).
     - ~~*Point signalé, non tranché*~~ **TRANCHÉ le 24/09/2026** : le document
       annonçait `test_ids_ecran.py` **70** dans le sujet « Symboles de genre »
       (les **écrits**) et **168** dans « frontend/ — Interface » (les
       **exécutés**) — deux conventions pour le même test. C'est la session du
       24/09/2026 qui a tranché, en le faisant : ce test a gagné des contrôles (la
       modale des voix, puis ses filtres), donc les deux chiffres étaient périmés
       et le vérificateur `_verifier_faits_architecture.py` l'a **vu et dit**
       (« 2 écarts à lire »). La convention est maintenant **écrite sur place**,
       dans chaque phrase : `**187** pour le fichier entier` = les **exécutés**
       (c'est ce que le vérificateur mesure), et un chiffre de section = les
       **écrits**, sauf quand la phrase s'appuie sur l'exécution (section « 3
       sexies »). Les deux phrases le disent désormais — plus de convention
       implicite.

     *Décision de Laurent, le soir du 23/09/2026* : **on reste à UN sujet par
     session** (« on va rester prudent, 1 par session »), chaque sujet étant
     traité dans une **session propre**. **Douze** sujets sont **faits** :
     « Logique TTS — app.js », **« modules/tts.py — Synthèse vocale »**,
     **« frontend/ — Interface »**, **« 🎒 Moteur de voix Pocket TTS »**,
     **« Report des notes d'écoute dans les catalogues »**,
     **« 🎭 Distribution de voix par personnage (IA) »**, **« Symboles ♀️/♂️ de
     genre devant les prénoms »**, **« 🔒 Lire écran verrouillé »** et **« ✂️
     Rognage des silences de bord »** (les quatre derniers sont décrits ci-dessus),
     plus les trois de la première heure (le narrateur, le changement de moteur et
     le mode dialogue) — la liste complète est à l'**étape 3** ci-dessus.
     La suite est **nommée ici**, pour que la prochaine session reprenne sans
     chercher : *Extraits de voix libres de droits pour XTTS* (**110 lignes**),
     puis *🛠️ Réparer les moteurs de voix* (101). Les tailles se
     remesurent avec `_essais/_mesurer_sujets_architecture.py`.
     - ⚠️ **UNE VRAIE DÉRIVE TROUVÉE, ET CORRIGÉE le 23/09/2026** : la page
       annonçait `PARAGRAPH_PAUSE_MS` **passé à 0** (15/09/2026) alors que le code
       portait **300** depuis le **17/09/2026** — un retour arrière raconté dans le
       commentaire du code, jamais écrit dans la page. **Six jours de faux** sur la
       pause entre paragraphes (soit, à l'oreille, 0,3 s qui existaient bel et
       bien). La chronique du sujet porte désormais le fait daté, et la valeur est
       **contrôlée** par `_verifier_faits_architecture.py` (section 4) ;
       **preuve** que ce contrôle *aurait* attrapé l'ancien état :
       `_essais/_preuve_controle_pause.py` (lecture seule).
     - **Attention au plafond** : ce sujet passe de **416 à 471 lignes** et le
       seuil de l'audit est de **500 lignes par section** — toute addition à
       « Logique TTS — app.js » devra être courte, sinon l'audit alertera (c'est
       son rôle).
     - **Mesurer avant de choisir le sujet** : `_essais/_mesurer_sujets_architecture.py`
       (lecture seule) classe les 61 sujets par taille. Tailles du **23/09/2026
       (le douzième sujet)** : `Logique TTS — app.js` (471, fait), `modules/tts.py`
       — Synthèse vocale (422, fait), `frontend/` — Interface (300, fait),
       **Distribution de voix par personnage (IA) (282, fait)**, **Moteur de voix
       Pocket TTS (254, fait)**, **Report des notes d'écoute (239, fait)**,
       **Symboles ♀️/♂️ de genre (229, fait)**, **Lire écran verrouillé (183,
       fait)** et **Rognage des silences de bord (164, fait)** ; les gros qui
       restent : Extraits de voix libres de droits pour XTTS (110), Réparer les
       moteurs de voix (101), En-tête compact de la fenêtre du casting (95).
  4. **outils** (racine, cités dans `test_voix/LIRE_MOI.md`) :
     `_restructurer_architecture.py` (titres + sommaire),
     `_regrouper_architecture.py` (parties),
     `_demenager_pistes_architecture.py` (déménagement),
     `_corriger_separateurs_architecture.py` (les séparateurs en double),
     `_analyse_structure_architecture.py` (mesure),
     `_verifier_faits_architecture.py` (les faits) — à garder tels quels, ou à
     déplacer dans `test_voix/` avec un lanceur double-clic (à trancher).
  *Rappel des autres chantiers ouverts* : les **35 tests Python hors lanceur**
  (item « Suite de tests automatisés + CI », priorité 3) — le piège du 21/09 :
  un test absent de la liste du lanceur **ne tourne jamais**.

---

## 🔴 Priorité 1 — Lecture audio (confort immédiat)

- [ ] **🎚️ Les pauses restent IRRÉGULIÈRES : tous les moteurs ne rognent pas leur
  queue** — **diagnostiqué le 24/09/2026**, à partir du retour d'écoute de Laurent
  (« les pauses ont l'air un peu aléatoires avec Kyutai, parfois ça enchaîne vite,
  parfois non ; à l'oreille, la pause des sauts de ligne et des points est
  sensiblement identique »). **Décision de Laurent le même jour : on ne touche à
  rien pour le moment** (« ça fluidifie un peu mieux qu'avant l'écoute ») — l'item
  reste ouvert pour que le diagnostic ne se reperde pas.
  *Ce qui marche déjà* : le rognage de Kyutai du 23/09/2026 fait son travail.
  Mesure sur les fichiers produits depuis le changement
  (`_essais/_mesurer_bords_cache.py --recent 304`, lecture seule) :
  **203 fichiers sur 303** ont une queue **≤ 0,25 s**, **médiane 0,19 s** — la
  queue médiane est bien passée de 0,37 s à 0,19 s.
  *La cause de l'irrégularité, mesurée* : **les livres mélangent les moteurs** —
  relevé du 24/09/2026 (`_essais/_repartition_moteurs_voix.py`, lecture seule) :
  **682 personnages en Piper, 203 en Kyutai, 161 en Kokoro, 78 en Edge**, 2 en
  Pocket. Or seuls **Kyutai** (0,20 s depuis le 23/09), **Edge** (0,35 s) et
  **XTTS / NeuTTS** (0,25 s) rognent leur queue : **Piper, Kokoro et Pocket ne
  rognent rien**. Dans un même chapitre, une phrase du narrateur (Kyutai) et une
  réplique en Piper n'ont donc pas la même respiration — c'est ça, le « hasard ».
  Deuxième cause, plus discrète : le silence de **tête** va de 0,00 à **1,77 s**
  (médiane 0,08 s), et la pause entendue est `queue + tête` (on peut voir le
  profil de fin d'un fichier : `_essais/_mesurer_bords_cache.py --profil <début
  du nom>`).
  *Le remède, si Laurent le décide un jour* : rogner aussi Piper, Kokoro et
  Pocket — la fonction existe déjà (`modules/audio_queue.py`,
  `rogner_queue_wav`) et travaille sur un WAV, donc sur tous ces moteurs ; il
  faudrait la brancher dans `synthesize_piper` / `synthesize_kokoro` /
  `synthesize_pocket` et incrémenter `VERSION_CACHE`. **À mesurer avant** : la
  variabilité réelle de chaque moteur, moteur par moteur
  (`test_voix/_mesurer_pause_phrases.py`, lecteur et moteurs allumés).
  **INFO DE LAURENT, 24/09/2026 — c'est Pocket TTS qui lit chez lui** : « il y a
  aussi Pocket TTS qui est en moteur actif ». Vérifié dans le code, et c'est
  cohérent : `data/moteur_voix.txt` ne porte que le moteur **LOURD** (il dit
  « kyutai »), tandis que **Pocket TTS cohabite** (processeur) et n'y figure
  jamais ; il est donc disponible en permanence, et le narrateur du livre d'essai
  37 est bel et bien `pocket:Homme87976454321` (`books.narrator_voice`).
  Or **`synthesize_pocket` ne rogne rien** (vérifié : vitesse, hauteur, niveau —
  c'est tout), et Pocket est un moteur **génératif** : sa queue de silence
  **varie d'une prise à l'autre**. C'est très plausiblement ÇA, le « parfois ça
  enchaîne vite, parfois non » entendu le 24/09 — un moteur qui ne rogne rien, et
  qui en plus ne redonne jamais deux fois le même silence.
  ➡️ **Cible prioritaire du remède : POCKET TTS** (le moteur d'écoute de Laurent),
  avant Piper et Kokoro.
  *Leçon à garder* : le 23/09, l'hypothèse était « la queue non rognée de Kyutai
  explique les pauses trop longues ». Le test terrain l'a **partiellement
  démentie** — la queue est bien rognée, mais une **deuxième** source de
  variabilité (les autres moteurs) se cachait derrière. C'est écrit ici pour
  qu'on ne la redécouvre pas.
  *Piste examinée le 24/09/2026* (idée de Laurent : « est-ce que ça peut venir du
  contexte glissant ? Peut-être en le supprimant pour essayer ? ») :
  **non, pas pour les sauts de ligne** — `_buildPlaylist` ne donne un contexte
  qu'aux suites de phrases du **même locuteur dans le même paragraphe** : jamais
  après un saut de ligne, jamais quand la voix change. Et sa **suppression a déjà
  été essayée** le 21/09/2026 (lot d'écoute
  `test_voix/ecoute_contexte_20260921_1835` : phrase seule / 3 mots / 8 mots) —
  verdict de Laurent, écrit dans `app.js` : sans contexte, « l'attaque est
  écrasée », le premier phonème part avalé ; le **3 mots** est retenu, et le
  contexte n'agit donc que sur le **début** des phrases (la coupe du service peut
  y laisser un mot du précédent : 4 cas sur 6 avec 8 mots, **aucun** avec 3).
  *Et une part de variabilité qui ne se règle pas* : **Kyutai n'est pas
  déterministe** (mesuré le 21/09/2026 par `test_voix/_mesurer_contexte_mots.py` :
  deux demandes identiques donnent deux audios différents) — le moteur explique
  donc lui-même qu'un défaut « n'arrive que de temps en temps ».
  *Un interrupteur a été posé le 24/09/2026* pour pouvoir refaire l'essai en
  conditions réelles : `CONTEXTE_MOTS = 0` (`frontend/app.js`) **désactive** le
  contexte, avec un garde-fou contre le piège `slice(-0)` (qui aurait donné le
  contexte le **plus long** au lieu d'aucun). L'essai est **sans perte** : le
  contexte entre dans la clé du cache, donc l'aller (sans contexte) et le retour
  (avec les 3 mots) sont immédiats et se font dans les deux sens.

- [ ] **✂️ Découpage : séparer la NARRATION des RÉPLIQUES (mode dialogue, livre
  par livre)** — demandé et commencé le **21/09/2026**. Laurent : « j'aimerais
  bien avoir des marqueurs nets sur "dialogue" et "narrateur". Que dans un
  passage où narrateur et dialogues sont présents, les voix soient cohérentes
  avec le texte. […] C'est vraiment la seule chose qui manque cruellement pour
  une immersion totale. »
  *Ce qu'il faut savoir* : le découpage n'est **pas** fait par l'IA. Il est fait
  par une **règle locale** (`modules/decoupage.py`, recopiée à l'identique dans
  la page), et Gemini ne fait qu'**étiqueter** des morceaux déjà découpés : il ne
  peut donc pas « découper » quoi que ce soit. Le levier, c'est **notre règle** —
  et elle ne coûte rien.
  *Le défaut, mesuré* (livre 28, « 22/11/63 », 24 841 morceaux) : **606**
  morceaux contiennent du texte avant un `«`. Trois variantes de règle ont été
  comparées ; la retenue (le texte avant la citation finit par **deux-points**
  ET contient un **verbe de parole**) vise **166 morceaux, dont 159 sont
  aujourd'hui attribués à un personnage** : c'est le personnage qui lit la
  narration (« Avant que j'aie pu répondre, Richie est intervenu : »). Une
  variante plus large (298 morceaux) attrapait des citations racontées
  (`Le sujet que j'avais donné était : …`), d'où le choix prudent.
  *Livré le 21/09/2026 (testé, pas encore éprouvé à l'oreille)* :
  - `modules/decoupage.py` : `REGLE_DIALOGUE`, `VERBES_DE_PAROLE`,
    `introduit_une_replique()`. La coupe ne s'applique **jamais** à une citation
    racontée (`J'ai jamais eu « la larme facile », comme on dit.`), qui doit
    rester d'un seul morceau sous peine d'être lue en deux fois ;
  - `frontend/app.js` : la même règle, **mot pour mot** — les deux listes de
    verbes sont comparées par le test, et chaque radical commence par une lettre
    ASCII (sinon `\b` ne se comporte pas pareil en Python et en JavaScript) ;
  - **un mode PAR LIVRE** (`books.decoupe_dialogue`, ajout non destructif) : les
    13 livres déjà castés gardent le découpage d'origine, caractère pour
    caractère. C'est indispensable : leurs numéros de phrases sont ENREGISTRÉS
    (`speaker_attribution`), un découpage différent décalerait leurs voix ;
  - `test_voix/MODE_DIALOGUE.bat` (+ `regler_mode_dialogue.py`) : liste des
    livres, puis activer/désactiver, avec **copie datée de la base** avant
    d'écrire ;
  - `test_voix/test_decoupage_phrases.py` : **36 contrôles** (la règle, ses trois
    garde-fous, les positions exactes — la migration en dépend —, aucun texte
    perdu, et les verbes de parole identiques côté page).
  *Livre de test choisi par Laurent* : **« Lazarille de Tormes »** (anonyme,
  1554, domaine public ; 13 chapitres, 155 000 caractères) — **64 cas** à
  corriger pour un casting estimé à **0,07 $**. Le choix d'un livre NEUF est
  volontaire : on ne touche à **aucun** livre casté.
  *Protocole d'essai* : castage du livre en mode **origine**, on note 3-4
  passages ; puis **mode dialogue** + re-cast ; on réécoute **les mêmes**
  passages. Coût total ≈ **0,15 $** (mesure du journal : 0,0047 € par appel IA ;
  un livre entier va de **0,06 €** — Lazarille — à **1,41 €** — Shantaram ;
  chiffres **corrigés le 22/09/2026**, voir « Prix d'un re-cast » plus bas).
  *ESSAI RÉEL, fait le 21/09/2026 (protocole tenu)* : le livre de test a été
  casté **deux fois** — une fois en mode **origine**, puis (après activation du
  mode dialogue et remise à zéro de son attribution) une fois en mode
  **dialogue**. Chaque castage a coûté les 0,07 $ annoncés (16 puis 18 appels).
  *Résultat mesuré dans la base* : le découpage passe de **912 à 986 morceaux**
  (+74), et sur les **75 beats de narration** du livre, **73 sont maintenant lus
  par le NARRATEUR** avec la réplique attribuée au PERSONNAGE (les 2 restants :
  un beat dont la réplique est restée « narration », à écouter). Exemples :
  - AVANT : `Alors Frère Girolamo, sentant le moment venu d'opérer le faux
    miracle…` → locuteur enregistré = **Frere Girolamo** ;
  - APRÈS : le beat = **narration**, et « Jésus-Christ, mon Seigneur… » =
    **Frere Girolamo** ;
  - AVANT : `Et le More, riant, répondit : « Hi…` → **Zaide** ;
  - APRÈS : `Et le More, riant, répondit :` = **narration**, « Hi… » = **Zaide** ;
  - AVANT : `La foule, voyant ce nouveau miracle… cria à son tour : « Jésus !` →
    **Foule** ; APRÈS : le beat = **narration**, « Jésus ! » = **Foule**.
  *Preuves* : `_comparer_decoupage_livre.py 36 origine|dialogue` (lecture seule),
  et les relevés conservés dans `_avant_origine_36.txt` / `_apres_dialogue_36.txt`.
  *Défauts trouvés par Laurent le 21/09/2026, en écoutant le livre de test* — il a
  entendu « quelque chose qui cloche » sur un passage précis, et il avait
  raison : **trois symptômes, deux vrais défauts**.
  1. **Apostrophe typographique** (vrai bug de la règle) : le livre écrit
     `s’écria` avec l'apostrophe **courbe**, la liste de verbes utilisait
     l'apostrophe **droite** → ces beats n'étaient **pas reconnus**, donc **pas
     coupés** : `Frère Mariano, …, s’écria : « Jésus !` restait **un seul
     morceau**, et le personnage lisait la narration. *Corrigé* : les deux
     apostrophes sont traitées pareil (`introduit_une_replique`, dans
     `modules/decoupage.py` **et** dans la page), avec un test de
     non-régression (`test_decoupage_phrases.py`, désormais **39 contrôles**).
     **Même famille, trouvée juste après par Laurent** : la liste contenait
     `cria` mais pas **`crier`** (l'infinitif) → `… se mit à crier, le montrant
     du doigt avec terreur : « Maman, la bête !` n'était pas coupé, et le beat
     était lu par **Frère de Lazarillo**. *Corrigé* : radicaux ajoutés (`crie`,
     `soupir`, `balbuti`, `bredouill`, `prononç`, `chuchot`, `articul`), test de
     non-régression à l'appui → **41 contrôles**. Effet mesuré : le livre de test
     passe de 987 à **989 morceaux**.
  2. **Beats attribués au personnage malgré la coupe** : l'IA voit une réplique
     dans un morceau qui finit par un verbe de parole **et commence par le nom
     du personnage** (mesure : 2 cas dans le livre de test). Une règle
     **déterministe** a été écrite pour ce cas (`_forcer_beats_en_narration` :
     un beat hors citation ouverte remis au narrateur, aucun appel IA, aucune
     facture) — puis **RETIRÉE du pipeline le 21/09/2026, après mesure** : ses
     deux seules trouvailles dans « Lazarille de Tormes » se trouvaient **dans**
     le long discours d'un personnage qui rapporte ses propres paroles (citation
     imbriquée), et les forcer au narrateur aurait coupé sa voix au milieu de sa
     tirade. Le passage est devenu correct **sans elle**, par les deux correctifs
     ci-dessus (apostrophe typographique, cris). La fonction **reste dans le code
     comme MESURE** (elle sert à `_corriger_livre.py`), elle n'est **plus
     appelée**. *(Texte corrigé le 22/09/2026 : le BACKLOG annonçait ici un
     correctif qui n'est pas appliqué — le dire, sinon la croyance revient.)*
  3. Le troisième symptôme (« La foule, … cria à son tour : » lu par *Foule*)
     était un **état transitoire** : la page avait le nouveau découpage (986
     morceaux) mais les **anciennes** attributions (912 lignes) → voix décalées.
     Une simple **relecture** de la page remet les voix justes — c'est écrit en
     clair dans la sortie de `regler_mode_dialogue.py`.
  *Corrigé aussi* : les **cris coupés** par leur propre ponctuation
  (« « Jésus ! Jésus ! » » — 12 cas dans le livre de test) dont la seconde
  moitié restait au narrateur. La citation ouverte garde désormais son locuteur
  quand la suite reprend par une majuscule après un `!`, un `?` ou une ellipse
  (`LONGUEUR_CRI`, morceau court, sans beat).
  *Second re-cast après redémarrage (0,07 $), et **vérification morceau par
  morceau*** : le passage exact entendu par Laurent est devenu **correct** —
  « Frère Mariano, … s'écria : » au **narrateur**, les deux « Jésus ! » au
  **personnage**, « La foule, … cria à son tour : » au **narrateur**. Le
  troisième symptôme (beat de la Foule lu par *Foule*) venait d'un **état
  transitoire de la page** (nouveau découpage + anciens index, page restée
  ouverte pendant le re-cast) : une relecture suffit.
  *Deux pistes explorées, puis ÉCARTÉES — c'est le plus important à garder* :
  mesurées sur ce livre, elles étaient **fausses**, et seule la lecture du texte
  l'a montré.
  1. une règle « un beat de narration est toujours du narrateur » proposait
     **13 corrections**, dont **11 étaient des phrases de NARRATION**
     (« Je m'approchai et lui montrai le pain. ») et **2 des citations
     imbriquées** dans le long discours de l'écuyer : appliquée, elle aurait
     abîmé le livre. La règle est **retirée du pipeline** ; elle reste comme
     **mesure**, dans un outil qui n'écrit jamais (`_corriger_livre.py`) ;
  2. les détecteurs « beat apparent » et « fragment orphelin »
     (`_mesurer_fragments_36.py`) **sur-signalent** : ils comptent sans lire le
     texte. *Leçon consignée* : **un chiffre ne vaut rien sans la lecture des
     morceaux concernés**.
  *Coût total de l'essai* : trois castages du livre de test, **≈ 0,13 $**
  (0,09 $ mesurés pour les deux premiers).

  *Laboratoire d'essai (même soir, idée de Laurent)* : plutôt qu'un livre entier
  pénible à lire, **un chapitre d'un livre qu'il connaît** — chapitre 28 de
  **« 22/11/63 »** (« Sadie »), le plus dialogué du livre (14 beats, 137 `«`,
  144 tirets). Un **EPUB d'un seul chapitre** est fabriqué et importé par l'API
  (`_creer_epub_chapitre.py` + `_importer_epub.py`) → **livre n°37**
  « 22/11/63 - chapitre d'essai (Sadie) - decoupage », en **mode dialogue**.
  Le livre n°28 de Laurent n'est **jamais** touché. *Leçon* : Lazarille, pénible
  à lire, reste au tiroir comme « piège à typographie » (il a révélé les deux
  bugs ci-dessus), mais **22/11/63 est le bon terrain** : personnages connus,
  oreille de Laurent fiable.
  *Résultat de la passe 1 (prompt d'aujourd'hui, 0,06 $)* : **14 beats sur 14
  lus par le NARRATEUR**, et les **14 répliques** attribuées aux bons personnages
  (Dr Ellerton, George de Mohrenschildt, Sadie Dunhill, Jake Epping…). Autrement
  dit : **après les deux correctifs de code, ce chapitre ne présente plus aucun
  défaut mesurable**. Le détail est dans `_passe1_37.txt`.
  *Mesure complémentaire* : `_mesurer_sans_signe.py` trouve **284 morceaux**
  attribués à un personnage « sans signe de dialogue » — mais la **lecture** des
  textes montre que ce sont des **suites de répliques** (« Et endormie. »,
  « Chez toi. », « Je sais. », « CHapel 5-6323. »), donc **légitimes**. C'est la
  confirmation que ce filtre (déjà désactivé dans `voice_casting`) sur-signale :
  **284 sur 1243**, soit 23 % du chapitre.
  *Pistes de PROMPT, prêtes mais NON testées* (aucun défaut mesurable sur ce
  chapitre pour les éprouver — on ne les testera que si l'oreille de Laurent
  trouve quelque chose) : (1) « un morceau qui annonce une réplique est du récit,
  **sauf** dans une citation » (la règle que le code ne savait pas juger) ;
  (2) fournir le **numéro de paragraphe** de chaque morceau ; (3) demander à l'IA
  une liste **`melange`** signalant les morceaux qui mélangent récit et réplique
  — un thermomètre de notre découpage. Coût d'un essai : ~0,06 $ la passe.
  *Pourquoi un chatbot semble réussir et pas notre prompt* (question de Laurent,
  consignée) : l'IA reçoit des morceaux **déjà découpés par nous** et doit donner
  **un seul** nom à chacun (un morceau mixte n'a pas de bonne réponse) ; elle
  répond **130 étiquettes** par appel, en JSON compact, et doit rester cohérente
  sur ~25 000 morceaux ; un chatbot lit le passage entier, peut hésiter et
  s'expliquer, une seule fois, sans contrainte de coût. **Le levier principal
  reste donc le découpage (notre code, gratuit) — pas l'intelligence de l'IA.**

  *Trois nouveaux cas, trouvés par Laurent à l'oreille le même soir, sur le
  chapitre d'essai* — et **aucun n'est un problème de prompt** :
  1. **Beat sans verbe de parole** : « Puis : « D'accord, j'ai pu le faire. » »
     restait **un seul morceau**, donc lu par le personnage. Les quatre cas du
     chapitre, **lus un par un**, montrent que le signal est le **deux-points**
     juste avant la citation, pas le verbe (« Puis : », « …deux secondes de
     répit, puis : », « …crié : » — et « crié », participe, n'était pas reconnu
     non plus, « …une seconde tentative : »). *Livré le 21/09/2026* : la règle
     devient **deux-points OU verbe de parole** (`introduit_une_replique`,
     Python **et** page) ; **44 contrôles** au vert. Effet mesuré : **+5
     morceaux** dans le chapitre d'essai, **+46** dans Lazarille (lus : des
     phrases de récit ou d'appareil critique séparées de leur citation, toutes
     légitimes), et 24 841 → **25 216** dans « 22/11/63 ».
  2. **Incise isolée sans virgule** : « m'a-t-elle demandé. » occupe **tout un
     morceau** (`modules/incises.py` attend « , dit-il, » : la forme sans
     virgules, et les participes comme « demandé », lui échappent) → c'est le
     personnage qui la lit. **Mesuré** : 3 cas dans le chapitre, 2 dans
     Lazarille (« lui dis-je. », « s'écria-t-il. »). *À FAIRE* : étendre
     `incises.py` (délicat : ce module a ses propres tests, et retirer du texte
     est risqué). **Sans re-cast** : l'incise est retirée à la synthèse.
     *Mesure à l'échelle du livre (22/09/2026)* : **134 phrases** dans 22/11/63
     (0,53 %), dont **114 terminales** ; **697** dans Shantaram (2,30 %), 6 dans
     le tome 5. Un **prototype de règle est prêt et validé sur les phrases de
     Laurent** (voir « Retours d'écoute du 22/09/2026 », ci-dessous) : la forme
     composée est le trou le plus rentable des règles d'incises.
  3. **Acronymes** : « URSS » (et « TSBD ») ne sont pas prononcés comme « FBI »
     et « CIA ». *À FAIRE* : entrées dans la table de `modules/prononciation.py`
     — **validées à l'oreille de Laurent** (la règle du module : une graphie
     fausse serait pire que le défaut). **Sans re-cast** non plus : la table
     s'applique à la synthèse.
  *Verdict d'ensemble de Laurent, à mi-écoute* : « c'est nettement mieux
  qu'avant. C'est même excellent ! »

  *À faire* : **l'écoute par Laurent**, puis la décision pour ses autres
  livres — **migration gratuite** des index (les étiquettes existantes sont
  recollées sur le nouveau découpage) ou **re-cast** (≈ **0,06 €** pour un petit
  livre, ≈ **1,14 €** pour le plus gros de la bibliothèque — barème vérifié le
  22/09/2026, plus bas). Les 13 livres déjà castés sont restés en
  mode origine pendant tout l'essai : aucun n'a été touché.
  *Relevé du 22/09/2026 (Cline), pour préparer cette décision* : la
  bibliothèque compte **15 livres**, dont **13 sont castés** — et **11 de ces 13
  sont encore en mode origine** (Lazarille et le chapitre d'essai sont les deux
  seuls en mode dialogue), soit **105 984 phrases attribuées** à migrer. Un
  re-cast complet coûterait donc **≈ 4 €** (mesure du 22/09/2026 — et non 24 €
  comme écrit d'abord, voir « Prix d'un re-cast » plus bas) contre **0 €** pour
  une migration des index : c'est la migration qu'il faut instruire en premier.
  ⚠️ **Point dur à trancher avant d'écrire quoi que ce soit** : les morceaux de
  narration **nés de la coupe** hériteraient de l'étiquette du personnage
  (c'est exactement le défaut n° 2 ci-dessus, dont la règle a été retirée). Une
  migration **sans règle** ne ferait donc pas gagner ce que le mode dialogue
  apporte ; **avec** une règle, elle ne doit viser que les **morceaux nés de
  notre propre coupe** et **jamais** ceux qui se trouvent dans une citation
  ouverte (les 2 cas de Lazarille). À mesurer avant d'écrire.
  *Retour d'écoute de Laurent, 22/09/2026 (matin)* : « les écoutes que j'ai
  faites au sujet de la découpe du texte et de l'attribution des voix, incises
  lues par le narrateur, les passages qui sont bien détectés selon les
  personnages […] pour ce que j'ai écouté le résultat est très bon ». Écoute
  approfondie prévue dans l'après-midi. **C'est ce verdict qui décide de la
  suite** : migration des index (0 €) ou re-cast des livres restés en mode
  origine.
  *Prix d'un re-cast — CORRIGÉ le 22/09/2026 après vérification*. Le premier
  chiffre écrit ici (« 0,23 € les 1 000 phrases », d'où **5,71 €** pour
  « 22/11/63 ») venait d'une **ligne du BACKLOG jamais recalibrée** (« ~1,15 €
  pour un gros tome ») : elle datait d'**avant** la calibration sur facture du
  14/09/2026. Le vrai barème est celui de `modules/voice_casting.py`
  (0,42 $/M en entrée, 3,50 $/M en sortie, **calibré sur la facture Google** de
  Shantaram : 30 293 phrases → **0,98 €** facturés). Estimations de
  l'application, marge de prudence comprise : « Lazarille » (912 phrases)
  ≈ **0,06 €** ; un tome du Comte de Monte-Cristo (≈ 5 000) ≈ **0,26 €** ;
  « Dialogues désaccordés » (1 779) ≈ **0,12 €** ; « Notre-Dame de Paris »
  (12 066) ≈ **0,60 €** ; « 22/11/63 » (24 841) ≈ **1,14 €** ; « Shantaram »
  (30 285) ≈ **1,41 €**. **Les 10 livres encore en mode origine ≈ 4 € au total.**
  ⚠️ **Réponse à la question de Laurent (« le mode dialogue coûte-t-il moins cher
  à caster ? »)** : **non, le prix est le même** — mesuré, à la formule de
  l'appli : « 22/11/63 » 1,141 € → 1,150 € (**+0,8 %**, moins d'un centime),
  Monte-Cristo T5, Shantaram et Lazarille : **écart nul**. C'est logique : le
  découpage fin **ajoute** des morceaux (375 de plus sur 24 841), et l'IA en
  étiquette un de plus, mais chacun est plus court. **Ce que le mode dialogue
  apporte n'est donc pas le prix, c'est la justesse** : sur un livre **jamais
  casté**, il fait faire la bonne attribution **du premier coup** — donc pas de
  second passage à payer, et rien à corriger à la main. **Pour un livre neuf,
  activer le mode dialogue AVANT le casting.**
  ⚠️ **Piège à connaître avant de payer** : le **re-cast « gratuit »** du bouton
  (12/09/2026) ne redistribue que les **voix** dans le catalogue courant — il ne
  refait **pas** le « qui parle ». Il ne dit donc **rien** du nouveau découpage.
  Le seul essai qui parle vraiment du découpage est la **migration des index
  (0 €)**, ou un re-cast **payant**.
  **MIGRATION DU 22/11/63 — FAITE le 22/09/2026** (décision de Laurent : « on
  écrit sur 22/11/63 […] si tu peux faire tout le livre je suis preneur »).
  Outil neuf `test_voix/_migrer_index_dialogue.py` : il **simule** par défaut,
  n'écrit qu'avec `--ecrire`, et accepte `--base` pour **répéter sur une copie**.
  Ce qui a été fait, dans cet ordre : répétition sur une **copie** de la base,
  contrôle, puis écriture sur la vraie base — qui a pris sa **copie datée**
  avant : `data/nimm_epub.db.bak_avant_dialogue_20260922_1311`.
  *Mesuré* : 24 841 → **25 216** morceaux (+375 répliques détachées, qui gardent
  leur personnage) ; **593** beats détectés, dont **257 remis au narrateur**
  (1,03 % des phrases) et **99 laissés tranquilles** (dans une citation ouverte).
  *Étendue vérifiée le 22/09/2026* (question de Laurent : « tout le livre, ou
  seulement le chapitre 3 ? ») : la migration a touché **34 des 38 chapitres**
  (les 4 autres n'ont pas de dialogue à séparer), et la narration y a grandi de
  **+342 morceaux** au total. Le chapitre 3 n'était que **l'exemple lu** à
  Laurent, pas la limite du travail.
  *Contrôlé après écriture* : chaque voix pointe sur une phrase qui existe, tous
  les locuteurs sont dans le casting, et la comparaison de la base d'avant avec
  celle d'après montre que **`voices` est IDENTIQUE** (voix, hauteur, vitesse,
  **verrous**), comme `cast_fiche`, `character_aliases` et `books.narrator_voice`
  — seul `decoupe_dialogue` passe de 0 à 1, avec `line_count` recompté (20
  personnages sur 176). **Le casting de Laurent n'a pas bougé d'un iota.**
  *Exemple réel (chapitre 3)* : « Et moi, avec un sourire : » passe au
  **narrateur**, et « « Vous l'avez déjà fait… » » reste à **Jake Epping**.
  *Deux erreurs de l'outil, trouvées en LISANT les exemples* (leçon du 21/09) :
  la coupe met le **beat en premier** (c'est donc lui qui héritait du personnage,
  et non le morceau neuf), et un morceau qui **commence par `«`** n'est jamais un
  beat. Les deux sont corrigées, avec l'explication, dans le code.
  *À faire par Laurent* : **recharger la page du lecteur** (le navigateur garde
  le casting et le découpage en mémoire), puis écouter le chapitre 3.
  *Reste* : les **10 autres livres** encore en mode origine — même outil, 0 €.
  **DÉCOUPAGE AVANT L'IA — AUTOMATIQUE (22/09/2026)**, demande de Laurent :
  « Il faut que ce soit automatique, si je caste un nouveau livre, il doit être
  découpé avant envoi à Gemini. »
  *Livré dans `main.py`* : quand un casting démarre sur un livre **jamais
  attribué** (aucune ligne dans `speaker_attribution`), le mode dialogue est
  activé **avant** le premier appel à l'IA — le découpage fin est donc celui que
  l'IA étiquette. Un livre **déjà attribué** n'est jamais touché : ses numéros de
  phrases sont enregistrés, et c'est la migration qui répare les index.
  L'**estimation de coût** affichée avant lancement suit la même règle (sinon on
  annoncerait un prix pour un autre découpage).
  *Garde-fou* : `test_voix/test_decoupage_auto_casting.py` (**11 contrôles**),
  ajouté au lanceur global — il vérifie la condition, la règle annoncée, l'ORDRE
  (découper avant d'appeler) et l'accord du prix affiché.
  *Effet pour Laurent* : un livre neuf est découpé et attribué correctement **du
  premier coup** — le **Tome 1 du Comte** (jamais casté, 4 791 phrases ≈ 0,26 €)
  est le premier candidat.
  *Détails* : ARCHITECTURE.md, « Mode dialogue ».
  *Piste complémentaire (non retenue pour l'instant)* : dans « 22/11/63 »,
  **44 morceaux** de « citation racontée » sont attribués à un personnage — des
  erreurs d'étiquetage que la règle de découpage ne corrige pas, mais qu'une
  consigne plus précise du prompt pourrait viser.

### Retours d'écoute du 18/09/2026 (une demi-journée d'écoute, 6 h)

- [ ] **Clignotement de la modale entre deux morceaux — à trancher** (20/09/2026).
  Après le collage, Laurent voit encore la **modale de lecture clignoter** quand un
  morceau se termine : les **premiers** morceaux d'un chapitre sont **courts** (on
  ne colle que ce qui est **déjà téléchargé** à cet instant), donc Android range la
  modale puis la ressort. Il l'a jugé **pas dramatique** (« je passerais par
  l'application ouverte »), mais l'option proposée reste ouverte : **faire attendre
  la réserve** quelques secondes (avec un plafond) avant de lancer un morceau —
  sauf le tout premier, pour que la lecture démarre tout de suite. Question posée
  à Laurent (fréquence des clignotements) : **en attente de sa réponse**.

- [ ] **Réévaluer la surbrillance après rognage des silences**
  Le rognage devrait rendre le curseur synchrone. Si un résidu persiste,
  compenser côté client (pose du curseur légèrement différée après `play`).

- [ ] **Bascule chapitre → chapitre écran éteint (cas limite connu)**
  La fin d'un chapitre peut s'interrompre si le réseau est suspendu (il faut
  charger le texte + synthétiser le début du chapitre suivant). Piste :
  pré-synthétiser/précharger le chapitre suivant en approchant de la fin.
  *Amélioré le 20/09/2026* : la **réserve « à bloc »** (voir l'item livré plus
  haut) remplit tout le chapitre dès que la page passe en arrière-plan, donc la
  lecture arrive à la fin du chapitre avec **tout le chapitre en mémoire** — la
  coupure ne peut plus venir du chapitre en cours. Il reste le **début du
  suivant** (texte + premières phrases), qui n'est pas encore préchargé.

### Retours d'écoute du 19/09/2026 (chapitre 96, « Le contrat ») — les INCISES

Écoute du chapitre 96 du *Comte de Monte-Cristo* (tome 5, index 21). Verdict de
Laurent : « les incises ont énormément disparu déjà ; on affinera une prochaine
fois ». Ce qui reste se range en **trois causes distinctes**, chacune mesurée le
19/09/2026 par un nouvel outil (`test_voix/_mesurer_cas_tordus_20260919.py`,
lecture seule) sur les **5 105 phrases** du tome 5 :

- [ ] **Éprouver les règles d'incises par un TEST ADVERSE (idée de Laurent,
  19/09/2026)** — « Tu me listes les règles, et je les donne à un LLM qui va
  essayer de les contourner, pour voir quels cas de figure passeraient encore. »
  Le document à copier-coller est prêt : **`REGLES_INCISES_a_eprouver.md`**
  (racine du projet). Il contient le contexte, les **6 étapes** de la règle, les
  **5 garde-fous**, les exemples déjà connus (pour ne pas les voir reproposés) et
  la mission : chercher des phrases françaises **réalistes** où la règle
  (A) retire à tort, (B) rate une incise, ou (C) produit un texte bizarre.
  *Pourquoi ça vaut le coup* : deux formulations de tests se sont déjà révélées
  fausses aujourd'hui (voir l'item du point-virgule), et l'angle mort de
  `_diag_incises_reelles.py` n'avait été trouvé que par hasard. Une machine qui
  **cherche à casser** la règle trouvera ce que nos yeux habitués ne voient plus.
  *Suite à donner* : pour chaque cas trouvé et confirmé par Laurent, ajouter un
  **contrôle dans `test_nettoyage_tts.py`** (et `test_ponctuation_incises.py`),
  puis décider du correctif. Un cas non confirmé à l'oreille ne devient PAS une
  règle.
  *PREMIER RETOUR (Claude.AI, 19/09/2026)* : 40 cas proposés, **18 confirmés**
  dans le vrai code (outil `test_voix/_verifier_cas_test_adverse.py`). Ses
  phrases sont **inventées** (il le dit lui-même) : la fréquence réelle devait
  donc être mesurée — c'est fait pour la famille la plus grave (ci-dessous).
  **Défauts CONFIRMÉS, par gravité** :
  - **le RÉCIT mangé** (son cas A1) : « Il ouvrit la porte, appela la femme de
    chambre, et attendit. » → « Il ouvrit la porte et attendit. » Une **action
    disparaît** : un verbe de parole (« appela ») employé comme verbe ordinaire
    est pris pour une incise. **Mesuré : 8 phrases de NARRATION sur 1 344** dans
    le tome 5 (0,6 %), dont une **destructrice** : « Mais le comte, sans
    s'arrêter à ce cri, **continua de tordre le poignet du bandit jusqu'à ce
    que**, le bras disloqué, il tombât… » → le sens est détruit. Outil :
    `test_voix/_mesurer_narration_abimee.py`.
  - **la réplique TRONQUÉE par la relative** (A2, A3) : « — C'est lui, dit
    Morrel, qui l'a voulu. » → « — C'est lui ». L'étape D emporte une relative
    qui appartient à la **réplique**.
    ⏸️ **ANALYSE FINE faite le 19/09/2026** (l'outil
    `_mesurer_vague1_20260919.py` montre désormais **ce que le module FAIT**, et
    non plus seulement la présence du motif) : sur les **14 phrases**, **9 ont un
    problème réel**, en **trois familles** :
    1. **la relative appartient à la RÉPLIQUE** et part avec l'incise :
       ch.8 ph.110 « — Ce n'est pas moi, dit Caderousse, **qui ai voulu tuer le
       juif**, c'est la Carconte. » → « — Ce n'est pas moi » (la réplique perd sa
       fin) ; ch.11 ph.202 « , dit le président, **qui vous a conseillé cette
       démarche**… ». **Critère de tri trouvé** : ces relatives portent un
       **pronom de la 1ʳᵉ/2ᵉ personne** ou un **verbe au passé composé** (« qui AI
       voulu », « qui VOUS a conseillé »), tandis que celles qui décrivent le
       locuteur sont à l'**imparfait** ou au **passé simple** (« qui ne pouvait »,
       « qui sentit »).
    2. **l'emportement va TROP LOIN**, au-delà de la virgule qui ferme la
       relative : ch.13 ph.126 « — Hier, monsieur, dit le jeune homme, dont la
       tête s'embarrassait, **j'étais chez vous**… » → « — Hier, monsieur ».
    3. **la relative reste collée à la réplique** quand elle est trop longue pour
       être emportée (`LONGUEUR_MAX`) : le texte devient **bancal** —
       ch.6 ph.24 « — Mais, dit Danglars, qui, de son côté, ne s'apercevait
       pas… » → « — **Mais qui, de son côté, ne s'apercevait pas**… ». Correctif
       probable : **si on ne peut pas emporter la relative, ne pas retirer
       l'incise du tout** (mieux vaut une incise lue qu'un texte bancal).
    *Les 4 autres phrases sont correctes* : l'incise et sa relative qui décrit le
    locuteur partent ensemble, comme voulu (« dit Cavalcanti, qui se grisait… »,
    validé par Laurent le 18/09).
    ⏸️ **À faire dans une session à froid** : c'est la règle la plus subtile du
    module (trois sous-cas, chacun avec son garde-fou), et le correctif du même
    jour (C1) a montré qu'un motif « large » cache toujours un piège — le
    premier jet aurait emporté « , dit-il, **maintenant** il faut partir. »
  - **les IMPÉRATIFS de la liste** (A4, A5) : « — Parle, **dis la vérité**, et je
    t'écoute. » → « — Parle et je t'écoute. » Les formes de présent ou
    d'impératif (dis, demande, ajoute, répète…) déclenchent un faux retrait.
  - **le PARTICIPE orphelin** (C1) : « — Merci, dit Morrel, **se levant**. » →
    « — Merci se levant. » C'est le garde-fou « jamais de mot orphelin » qui
    tombe.
    ✅ **CORRIGÉ le 19/09/2026** : le geste qui suit une incise **fermée** part
    avec elle (`_etendre_participle`, `modules/incises.py`) — participe présent,
    forme pronominale (« se levant »), « en + participe », ou geste (« avec un
    col »). **Deux garde-fous ajoutés**, après avoir trouvé chacun son propre
    piège : (1) une **liste noire** des mots en « -ant » qui ne sont pas des
    participes (`maintenant`, `pendant`, `pourtant`…) — sans elle, « , dit-il,
    MAINTENANT il faut partir. » perdait la fin de la réplique ; (2) les groupes
    qui parlent de la **réplique** (pronoms et possessifs de la 1ʳᵉ/2ᵉ personne :
    « avec vous », « en me regardant ») ne sont **jamais** emportés.
    `VERSION_CACHE` 11 → **12**. **6 contrôles** ajoutés à
    `test_nettoyage_tts.py` (2 cas légitimes + 4 pièges) → **37 contrôles, 0
    échec**. Effet mesuré : la narration abîmée passe de **8 à 7** phrases dans
    le tome 5.
    *Complément du même soir (après écoute)* : une **énumération de gestes** part
    maintenant **en entier** (« avec un col, avec un habit, avec un gilet
    blanc… ») — sinon seul le premier morceau partait et le texte restait bancal
    (« voyez avec un habit ouvert… »), constaté à l'oreille au chapitre 90 du
    tome 5. `VERSION_CACHE` 12 → **13**, **2 contrôles** de plus (**39** au
    total, 0 échec).
    ⏸️ *Reste imparfait sur 2 phrases TRÈS longues* du tome 5 (énumérations et
    relatives imbriquées : chapitre 81 phrase 20 « …beau-père », dit Cavalcanti,
    se laissant entraîner… » et chapitre 90 phrase 252) : le geste part, mais le
    texte parlé reste bancal. Ces cas relèvent de la **même famille que A2/A3** —
    à traiter ensemble, à froid.
  - **les NOMS COMPOSÉS jamais reconnus** (B2) : « dit le comte de
    Monte-Cristo », « dit Valentine de Villefort », « dit M. Morrel père »,
    « dit l'abbé Faria », « dit le procureur du roi » → **l'incise reste LUE**,
    et c'est le personnage le plus bavard du roman.
  - **l'incise à PRONOM en tête de morceau jamais reconnue** (B1) : après un
    « ! » ou un « ? », le découpage isole « dit-il. » / « demanda-t-elle. » —
    `MOTIF_DEBUT` n'existe qu'en forme NOM, donc ces morceaux sont **lus**.
    C'est probablement **la plus grosse fuite** du dispositif.
  - **une incohérence confirmée** (B5) : « dit le comte gravement » **part**,
    alors que « répondit Morrel froidement » **reste**. Même famille, deux
    sorts — à traiter ensemble.
  *Faible priorité* : tirets fermants (B6), imparfaits pluriels (B7), adverbes
  (B5), réflexif avec un nom (B4), virgules de vocatif (C3).
  *Plan proposé, en 2 vagues* (à valider par Laurent) : **vague 1 — ne plus rien
  casser** (A1, A2, A3, A4, A5, C1) ; **vague 2 — ne plus rien laisser passer**
  (B1, B2, puis B3 à B7). Chaque vague : un **contrôle de test par cas**, une
  **mesure avant/après** sur le tome 5, et une **écoute** de Laurent.
  *DEUXIÈME RETOUR (Mistral, 19/09/2026, même document)* : 11 cas proposés,
  passés dans le vrai code → **2 vrais seulement**, dont un déjà connu, plus
  **1 vrai sur le fait mais à fausse cause**. Le reste est **faux** : trois de ses
  « défauts graves » sont en réalité le comportement **voulu** (« Je ne sais,
  murmura-t-il en baissant les yeux, si cela est juste. » → « Je ne sais si cela
  est juste. » est correct ; « Partons, dit-il, avant que la nuit ne tombe ! » →
  « Partons avant que la nuit ne tombe ! » est correct ; « Le comte, dit-il, est
  un homme dangereux. » → « Le comte est un homme dangereux. » est correct).
  ⚠️ **Son conseil le plus dangereux est à écarter** : il propose de **ne pas
  retirer** l'incise quand le mot suivant est le sujet de la phrase — cela
  supprimerait une foule de retraits légitimes. **Ne pas l'appliquer.**
  *Pourquoi cet écart* : Claude a **lu `incises.py` et fait tourner 100+ phrases**
  dans le vrai code ; Mistral a raisonné « au bon sens », sans tester. Leçon à
  garder pour les prochains tests adverses : **exiger du modèle qu'il exécute**,
  ou trier systématiquement par `_verifier_cas_test_adverse.py`.
  *Ce qu'il apporte quand même* : (1) il **converge avec Claude** sur les
  **verbes manquants** (« chuchota », « lança »…) et le **complément avant le
  nom** → ces deux cas passent en **priorité renforcée** ; (2) il confirme les
  **adverbes** (« de nouveau ») ; (3) il révèle une **incohérence réelle** : la
  relative part ou reste **selon le signe final** — « C'est lui, dit Morrel, qui
  l'a voulu. » perd la relative, alors que « C'est lui, s'écria-t-elle, qui a
  tout fait **!** » la garde (le garde-fou « proposition qui finit par ? ou ! »
  de `_etendre_relative` s'applique). À traiter avec les cas A2/A3 de Claude.
  *Croisement des deux retours* (ce que les DEUX ont trouvé, donc à faire
  d'abord) : **les verbes de parole absents de la liste** et **le complément
  avant le nom**.
  *Mesure de la VAGUE 1 dans le vrai tome 5 (19/09/2026, outil
  `test_voix/_mesurer_vague1_20260919.py`)* — ordres de grandeur, motifs simples :
  - **A2/A3** (incise + relative emportée) : **14 phrases**, dont 13 répliques.
    ⚠️ **À TRIER** : ces 14 incluent les BONNES relatives, qui décrivent le
    personnage et doivent partir (« … dit Mme de Villefort, **qui ne pouvait**… »).
    Le défaut de Claude ne concerne que celles qui appartiennent à la **réplique**
    (« , dit Morrel, **qui l'a voulu** »). Le tri se fera sur le **temps du
    verbe** : imparfait ou passé simple → décrit le locuteur, on emporte ;
    **passé composé** → appartient à la réplique, on ne touche pas.
  - **A4/A5** (impératif pris pour une incise) : **0 phrase dans le tome 5 !** Le
    défaut est réel **sur la phrase inventée** par Claude (« — Parle, dis la
    vérité… »), mais cette tournure **n'existe pas chez Dumas**. À revérifier sur
    un autre livre (Shantaram, King) avant d'y consacrer du travail :
    **fausse piste pour l'instant**.
  - **C1** (participe orphelin) : **2 phrases**, toutes deux des répliques
    (« dit Cavalcanti, **se laissant entraîner**… », « dit Beauchamp, **avec un
    col**… »).
  *Conclusion* : la vague 1 est **beaucoup plus petite** que le tableau de Claude
  ne le laissait croire. Priorités réelles : **C1** (2 phrases, correctif clair),
  puis **A2/A3** (14 phrases, avec un tri à faire). **A4/A5** en attente d'une
  vérification sur un autre livre.
  *Ordre validé par Laurent le 19/09/2026* : **vague 1 d'abord**, puis la
  **3ᵉ voie** (ne retirer les incises que dans les répliques) **en ceinture de
  sécurité** — rappel : la 3ᵉ voie ne protège que le **récit** (8 phrases du
  tome 5), jamais les répliques.
  *Aussi mesuré le 19/09/2026, pour mémoire* : l'heuristique « ne retirer les
  incises que dans les phrases qui commencent par un tiret » **ne marche pas** —
  elle sauverait 6 phrases de narration mais **raterait 162 incises de réplique**
  (239 répliques sans tiret sur 756, car le découpage coupe les longues
  répliques). C'est ce qui justifie la **3ᵉ voie par le locuteur**, et non par la
  forme.

- [ ] **Les civilités sans point coupent le motif** (`Mme`, `Mlle`, `Mgr`) —
  cause du « dit Mme Danglars en signant. » **lu**. Le motif prend « Mme » pour
  le nom et s'arrête là : il ne voit jamais « Danglars », donc l'incise n'est
  pas retirée. `CIVILITE` n'accepte aujourd'hui que la forme **avec point**
  (`M.`, `Dr.`), alors que `modules/decoupage.py` connaît déjà les
  `ABREVIATIONS_SANS_POINT`.
  *Mesure* : **4 phrases** dans tout le tome 5 (0,08 %) — Laurent est tombé sur
  un cas rare. Correctif minuscule, risque quasi nul.

- [ ] **Verbe + complément : le motif ne voit rien du tout** — cause du
  « dit **avec un imperceptible sourire de mépris** le comte » **lu**. Le motif
  attend le nom **juste après** le verbe ; ici un complément s'intercale.
  *Mesure* : **61 phrases** (1,2 %) — « dit alors Valentine au jeune homme qui
  la dévorait des yeux », « répondit le jeune homme ; », « dit rudement le
  docteur ».
  *Attention* : c'est le cas le plus **risqué** des trois (une règle trop large
  mange du texte). À mesurer avant/après sur 5 105 phrases, et à écouter, comme
  le banc du 18/09/2026 — **pas** d'adoption sans écoute.

- [ ] **Les incises à la 1ʳᵉ personne (« répondis-je », « fis-je ») — le récit
  au « je »** (constat de Laurent, 19/09/2026, à propos de Stephen King,
  *22/11/63* : le narrateur ET le personnage sont la même personne, la frontière
  est floue). Mesure faite le jour même, sur 8 tournures réelles :

  | Phrase | Ce que la règle fait |
  |---|---|
  | `— Ça m'étonne, dis-je.` | ✅ retirée |
  | `— Ça m'étonne, dis-je à voix basse, et je partis.` | ✅ retirée (complément emporté) |
  | `— Ça m'étonne, murmura-t-il.` | ✅ retirée |
  | `— Ça m'étonne, répondis-je.` | ❌ **non détectée** |
  | `— Ça m'étonne, fis-je en riant.` | ❌ **non détectée** |
  | `— Ça m'étonne, ai-je dit.` | ❌ **non détectée** |
  | `— Ça m'étonne, j'ai dit.` | ❌ **non détectée** |

  *Cause, précise* : la liste `VERBES` (`modules/incises.py`) contient « dis »,
  « répondit », « fit »… mais **pas les 1ʳᵉˢ personnes du passé simple**
  (« répondis », « fis », « murmurai », « m'écriai », « demandai »), ni les formes
  **composées** (« ai-je dit », « j'ai dit »). Or un récit au « je » en est plein :
  le tome de King les accumule, et Laurent les entend.
  *Piste de correctif* : compléter les formes en `-is` / `-ai` de la 1ʳᵉ personne
  (le motif `MOTIF_PRONOM` les acceptera tel quel : « , répondis-je » suit
  exactement la même forme que « , dis-je »). Les formes composées
  (« ai-je dit ») demandent, elles, un **motif séparé** — à mesurer.
  ✅ *Mesuré le 22/09/2026, à l'échelle du livre (22/11/63)* : les formes
  composées sont **le trou le plus rentable** des règles d'incises — **134
  phrases** dans ce seul livre (0,53 %), dont **114 terminales**, et **697** dans
  Shantaram (2,30 %). Le pronom « je » manquait aussi dans le motif (`ai-je`,
  `lui ai-je`), et les **participes accentués** (« répondu ») étaient absents de
  la liste. Un prototype est **validé sur les phrases exactes de Laurent**
  (« – Annette Founijello, m'a-t-elle répondu. » → « – Annette Founijello. »).
  Voir « Retours d'écoute du 22/09/2026 », ci-dessus.
  ⏸️ **EN ATTENTE du retour de Claude** (test adverse lancé le 19/09/2026, voir
  l'item correspondant) : Laurent a demandé à ne pas s'éparpiller. On regroupera
  les cas trouvés par Claude et celui-ci en **un seul chantier mesuré**.
  *À ne pas confondre avec un sujet de CASTING* : dans un récit à la 1ʳᵉ
  personne, la voix du **narrateur** devrait être celle du personnage principal
  — sinon l'écoute est bancale, indépendamment des incises. À vérifier le jour
  où on ouvrira *22/11/63*.

- [ ] **Les interjections tronquées : « Lèze » pour « Eh », « Nèk » pour
  « Ah »** — constat de Laurent (19/09/2026). Ce n'est **pas** un défaut

  d'incise, et ce n'est **pas** Kyutai (hypothèse de Cline, **démentie** par la
  base — à garder, sinon la croyance revient) : la base dit
  `Andrea Cavalcanti → kokoro:im_nicola` pour « Eh ! » et
  `Comte de Monte-Cristo → fr-FR-HenriNeural` (Edge) pour « Ah ! ».
  *Ce que le moteur reçoit* (`_clean_text`) : **5 caractères** —
  `« Eh,` et `— Ah,` : le **signe de dialogue est collé devant** et le `!` est
  devenu une **virgule** (règle des phrases courtes, `SEUIL_INTERJECTION`).
  *Mesure* : **379 phrases** du tome 5 font **8 caractères ou moins** (7,4 %).
  *Trois explications possibles, non tranchées* : (1) le signe de dialogue en
  tête ; (2) la virgule à la place du `!` ; (3) le texte trop court, sans
  matière. **Ne rien coder avant de les avoir départagées à l'oreille** : c'est
  le rôle d'un petit banc d'écoute (même méthode que
  `_banc_ponctuation_exclamation.py`), à fabriquer → item séparé ci-dessous.

- [ ] **Fabriquer le banc d'écoute des interjections courtes** — l'outil qui
  tranchera : la **même** interjection (« Eh ! », « Ah ! », « Oh ! », « Non ! »)
  passée aux voix réellement concernées (Kokoro `im_nicola` +15 %, Edge
  `fr-FR-HenriNeural` −5 %), en variantes : avec et sans le **signe de dialogue**
  en tête (`«` / `—`), avec `!`, avec `,`, avec `.`, et rattachée à la **phrase
  suivante**. Sortie : un dossier d'écoute daté + un lanceur double-clic, comme
  les autres bancs. **Le moteur doit être allumé.**

- [ ] **`_diag_incises_reelles.py` a un ANGLE MORT** — découvert le 19/09/2026.
  Son compteur « incises gardées pour une bonne raison » **saute** les phrases
  dès qu'une incise retirable y est détectée (`continue`, ligne 177) et son
  `MOTIF_LARGE` n'accepte que les incises **à pronom** et **à nom propre** ; il
  ne voit donc **pas** les incises à **nom commun** (« , dit le comte », « , dit
  le jeune homme »). Résultat : il annonce **19** incises gardées là où la mesure
  complète en compte **151**. Ses bilans sont donc **optimistes** — à corriger,
  sinon l'outil fait croire que le travail est fini.

- [ ] **Le scanner de prononciation d'un livre (étape 2)** — suite de l'item
  « syllabes inventées », livré le 21/09/2026. Aujourd'hui la table de
  `modules/prononciation.py` se remplit **à la main**, mot par mot, après mesure
  au phonémiseur et écoute. L'étape 2 est un **outil qui parcourt un livre** et
  rend la **liste des mots à corriger** — « 12 mots dans ce livre, voici
  lesquels » — avec leur fréquence : de quoi traiter un nouveau livre en quelques
  minutes au lieu de tout relire. **L'outil existe déjà côté NIMM Voix**
  (`scripts/tester_prenoms_kokoro.py`, sa partie scanner, et le lanceur
  `CHERCHER_PRENOMS_DUN_LIVRE.cmd` qui prend un EPUB par glisser-déposer) : il
  s'agit de le **rapatrier** — ou de reprendre sa méthode — et de le brancher sur
  les livres de la bibliothèque. Rien à décider, juste à faire : niveau 2.

- [ ] **Les prénoms prononcés « à l'anglaise », et des syllabes inventées autour**
  — chantier ouvert le **20/09/2026**, **cause trouvée** (question de Laurent :
  « quand Kokoro prononce un prénom, genre *Andréa*, j'entends `[énAndréafe]` — il
  invente des syllabes qui n'existent pas. De quoi ça vient ? »).
  *Cause, vérifiée de bout en bout le 20/09/2026* : pour `lang=fr-fr`, Kokoro n'a
  **pas** de phonémiseur français — il appelle **espeak-ng** (via `phonemizer`),
  un moteur **multi-langues** dont les dictionnaires de toutes les langues
  cohabitent. Quand un mot est reconnu dans le dictionnaire **anglais** (le cas de
  beaucoup de prénoms : `Andrea`, `Marthe`, `Arthur`, `Nathan`, `Ethan`,
  `Maëlys`, `Noah`, `Mathis` — **8 prénoms sur 48 testés**), espeak-ng **change de
  langue** et **marque la frontière** dans sa sortie : `(en)ˈandɹiə(fr)`.
  Le tokenizer de **kokoro-onnx 0.4.7** (appelé par `synthesize_kokoro`,
  `lang="fr-fr"`) **filtre la sortie caractère par caractère** au lieu de retirer
  cette marque : `"".join(filter(lambda p: p in self.vocab, phonemes))`. Or
  **`(`, `)`, `e`, `n`, `f`, `r` sont dans son vocabulaire** → la marque est
  **prononcée** : `(en)` ≈ « é-n » et `(fr)` ≈ « fe ». Voilà **les syllabes en
  trop**, juste avant et juste après le prénom.
  *Verdict d'oreille de Laurent (20/09/2026)*, sur le lot de NIMM Voix : « C'est
  toujours C qui prononce les prénoms correctement. Et A j'entends les syllabes
  ajoutées. B c'est la prononciation anglaise. Donc tous les C sont ok pour moi. »
  → **cause établie** : le code, le phonémiseur et l'oreille disent la même chose.
  *Dans NOS livres, mesure du 20/09/2026* : le **tome 5 de Monte-Cristo** écrit le
  prénom **sans accent** → le scanner y trouve **159 occurrences de `andrea`**, et
  **49 mots « anglais » pour 267 occurrences** au total (dont `d'Armilly` 16,
  `d'aujourd'hui` 3, `dos` 3, `assieds-toi` 2, `l'h` 2, `qu'hier` 2, et le
  filigrane `bibebook` 14). Le défaut **ne touche donc pas que les prénoms** :
  c'est **tout mot** que le dictionnaire anglais revendique. *Piper est touché
  aussi*, plus discrètement : son phonémiseur (`piper/phonemize_espeak.py`)
  **retire** les marques de langue, donc **pas de syllabes en trop**, mais il garde
  **la prononciation anglaise** (`Marthe` → *marth* avec le « th », mesuré le
  20/09/2026). *Réserve honnête* : Edge TTS, Kyutai, XTTS et NeuTTS ne passent
  **pas** par espeak-ng → non concernés (à confirmer à l'oreille).
  *Remède proposé (**niveau 3** : ça change ce qui est entendu)* : une **table de
  prononciation** (mot → graphie française : `Andrea → Andréa`, `Marthe → Marte`,
  `Arthur → Artur`, `Nathan → Natan`…), appliquée **au texte parlé seulement** —
  le texte affiché ne bouge pas, exactement le patron déjà en place pour les
  abréviations (`_expand_abbreviations`) et les capitales. À brancher pour
  **Kokoro et Piper** uniquement, dans `_clean_text()`. **Deux pièges connus à
  traiter** : (1) monter `VERSION_CACHE` (14 → 15), sinon les phrases déjà
  écoutées resservent l'ancien défaut — la leçon du 17/09 ; (2) chaque entrée de la
  table doit être **mesurée au phonémiseur** avant d'être gardée, puis validée par
  une **écoute A/B**.
  *Preuve, lot d'écoute et outil* : ils vivent dans l'atelier **NIMM Voix**
  (`sorties/diagnostic_prenoms_20260920/`, `scripts/tester_prenoms_kokoro.py`,
  lanceurs `TESTER_PRENOMS_KOKORO.cmd` et `CHERCHER_PRENOMS_DUN_LIVRE.cmd`) ; la
  démonstration complète est écrite dans son `ARCHITECTURE.md`, section « Défaut de
  prononciation des prénoms ».
  *Étape 2, après la table* : un outil qui **scanne un livre** et propose la liste
  des mots à corriger (« 12 mots à corriger dans ce livre, voici lesquels ») — le
  scanner existe déjà côté NIMM Voix.
  **Rappel de gouvernance** : Laurent a choisi le **20/09/2026** de **documenter
  d'abord, sans coder** — la correction n'est pas lancée.

- [ ] **RSVP — les mots longs débordent du cadre** (idée du 21/08/2026, portée ici
  le 22/09/2026 depuis `ARCHITECTURE.md`) : certains mots (« traitements »,
  « appréhendé »…) sortent légèrement du cadre sur mobile (`#rsvp-word`, police
  à `2.6rem`). À faire : réduire un peu la police, ou la réduire
  **dynamiquement** selon la longueur du mot affiché.

- [ ] **RSVP — le fondu de contexte à l'arrêt est confus** (idée du 21/08/2026,
  portée ici le 22/09/2026 depuis `ARCHITECTURE.md`) : le texte de fondu
  (`#rsvp-fade-text`) se superpose au chapitre visible derrière, plusieurs
  colonnes de texte se chevauchent, la lisibilité en souffre. À revoir : fond
  plus opaque derrière le texte de fondu, et/ou repositionnement pour ne plus
  recouvrir le texte du lecteur.

### Retours d'écoute du 22/09/2026 (22/11/63, chapitres 10 et 11) — la moisson

Laurent a écouté « quelques heures » du livre 28 (chapitres 10 et 11) : « voilà la
première moisson, mais à vrai dire ça se fait de plus en plus rare ». **Six causes
distinctes**, toutes **mesurées** le 22/09/2026 par des outils jetables en lecture
seule (`_moisson_22_11_63.py`, `_moisson_motifs.py`, `_moisson_incise_proto.py`,
`_preuve_candidat.py`, `_voix_narrateur.py`).

- [ ] **1. Incises de participe et d'auxiliaire — l'incise qui dit QUI parle est
  lue par le PERSONNAGE** (cas signalé : « – Annette Founijello, m'a-t-elle
  répondu. », dite par la fillette déguisée). C'est la famille de l'item
  « incise isolée sans virgule » du 19/09 (ci-dessus), mesurée ici **à l'échelle
  du livre** : **134 phrases** dans 22/11/63 (0,53 % du livre), dont **114
  terminales** ; **697** dans Shantaram (2,30 %), 6 dans le tome 5, 3 dans
  Notre-Dame de Paris, 8 dans le chapitre d'essai. *Cause* : la liste `VERBES`
  connaît « dit / répondit », mais **pas les participes** (« répondu »,
  « recommandé », « confirmé »), **pas l'auxiliaire** (« m'a-t-elle … »,
  « lui ai-je … ») et **pas le pronom devant le verbe** (« me dit Annette »).
  *Prototype mesuré le 22/09/2026* (règle candidate, **rien n'a été modifié**) :
  il retire exactement les deux phrases entendues → « – Annette Founijello. » et
  « « Merci, monsieur. », et rattrape au passage « – Baissez le ton », lui ai-je
  recommandé. » → « – Baissez le ton ». ».
  *Deux défauts PRÉEXISTANTS que la règle rendrait plus fréquents — à trancher* :
  (a) la **virgule de jonction** disparaît quand l'incise est coupée au milieu
  (« Hé, a-t-il dit en ricanant, on n'est jamais assez prudent ! » → « Hé on
  n'est jamais assez prudent ! ») ; (b) un **complément long** reste emporté avec
  l'incise (« …, a-t-elle dit d'une voix posée en me regardant tout en rêvant à
  autre chose. » → « … magnifique »). Ce sont **les comportements déjà validés le
  18/09** sur « , dit-il, » : la règle n'en invente pas de nouveaux, elle les
  applique à des formes qu'elle ratait. *À faire* : étendre `incises.py`,
  **incrémenter `VERSION_CACHE`** (le texte parlé change), rejouer le test adverse
  et un banc d'écoute. **Sans re-cast** : l'incise est traitée à la lecture
  (retirée, ou confiée au narrateur — voir l'item 1bis juste après).

- [ ] **1bis. OÙ SE PREND LA DÉCISION : incise MUETTE ou incise AU NARRATEUR ?
  (réflexion de Laurent, 22/09/2026 — la plus importante de la session)** —
  « Entre un Monte-Cristo, où elles sont inutiles la plupart du temps, et Stephen
  King, c'est tout à fait différent : quand il écrit des « j'ai dit », ça fait
  partie du récit, plus que des « dit untel » dans Monte-Cristo. Reste à savoir
  où on place ça… »
  **Ce qui débloque la question (constat technique du 22/09/2026)** : les deux
  comportements sont possibles **sans re-cast, sans re-découpage, et sans toucher
  aux index d'attribution**. Le lecteur construit **déjà** des unités audio plus
  fines qu'une phrase pour les phrases longues (`_buildPlaylist` /
  `_splitLongSentence`, `frontend/app.js`, `SPLIT_SENTENCE_CHARS`) : chaque unité
  porte son propre texte, sa voix, sa hauteur et sa vitesse, et **toutes gardent
  le même index de phrase** (le curseur reste posé sur la phrase). Traiter une
  incise n'est donc qu'une **variante de ce découpage** : soit on ne pousse pas le
  morceau (elle est **muette**), soit on le pousse avec la **voix du narrateur**.
  Environ 15 lignes dans la page ; le cache audio prend chaque morceau
  séparément, donc rien à migrer.
  **Où placer ce réglage — trois pistes, à trancher** :
  - **(A) Par livre, deux positions** (« incises muettes » / « incises au
    narrateur »), dans le menu du lecteur, à côté de la voix du narrateur — qui
    est **déjà** un réglage par livre (`books.narrator_voice`). Simple,
    prévisible, et c'est Laurent qui tranche à l'oreille, une fois par livre.
  - **(B) Le même réglage + une règle automatique** : incise au « je » (récit du
    narrateur-protagoniste) **gardée**, incise sur un tiers (« m'a-t-elle
    répondu », « dit Morrel ») **muette**, le réglage restant là pour forcer.
    Plus confortable, mais c'est une heuristique à régler et à mesurer.
  - **(C) Aucun réglage** : tout muet (comportement d'aujourd'hui) ou tout au
    narrateur. À n'envisager que si le réglage par livre s'avère inutile à l'usage.
  ✅ **DÉCIDÉ par Laurent le 22/09/2026 : (A) PAR LIVRE, AVEC UN BOUTON** —
  « Idéalement un bouton (dans casting) avec « incises lues » ou « incises non
  lues » […] la règle est bonne pour le moment, les incises à la 1ʳᵉ personne sont
  bonnes : inexistantes dans Monte-Cristo, et faisant partie de la narration dans
  22/11/63. »
  *Pourquoi un bouton et pas une règle automatique — MESURÉ le 22/09/2026*
  (outil `_moisson_profil_incises.py`, part des incises au « je » sur tous les
  livres castés) :

  | Livre | incises | dont au « je » | ce que l'oreille de Laurent dit |
  |---|---|---|---|
  | Monte-Cristo t. 5 | 788 | **1 %** | « inexistantes » ✔ |
  | Monte-Cristo t. 6 | 596 | **0 %** | idem ✔ |
  | Notre-Dame de Paris | 772 | **0 %** | idem ✔ |
  | Shantaram | 717 | **51 %** | récit à la 1ʳᵉ personne ✔ |
  | **22/11/63** | 274 | **25 %** | « font partie de la narration » ✔ |

  **Le seuil automatique est un piège** : un critère naïf (« plus de 30 % au
  "je" ») classerait 22/11/63 en « roman classique » — c'est-à-dire **le contraire
  de ce que Laurent entend** sur le seul livre dont on parle. Le profil doit donc
  **informer** (« ce livre : 274 incises, dont 25 % au "je" »), **jamais trancher**.
  C'est la réponse honnête à « pour savoir à l'avance sur un livre inconnu, c'est
  impossible » : on ne saura pas, mais on peut montrer les nombres.

  *Emplacement retenu — avis de Cline* : le réglage vit **par livre**, comme
  `books.narrator_voice`, donc **dans le menu du lecteur, à côté de la voix du
  narrateur** (`#settings-menus`, `frontend/index.html`) — c'est là que sont déjà
  la voix et la vitesse du narrateur, et c'est le menu qu'on a sous les yeux **au
  moment où l'on entend le défaut**. Le libellé doit dire QUI lit (sinon « lues »
  ne dit rien) : **« Incises : muettes » / « Incises : lues par le narrateur »**.
  Si Laurent veut le bouton **aussi** dans la fenêtre du casting : possible, et
  sans risque de divergence — ce serait **la même valeur**, vue de deux endroits,
  pas deux réglages.

  ⚠️ **LE PIÈGE À ÉVITER, identifié le 22/09/2026** (sinon la fonction paraîtrait
  cassée) : aujourd'hui le serveur retire les incises **dans la synthèse**
  (`_clean_text` → `retirer_incises`) et une phrase qui n'est **qu'une incise**
  devient un **silence** (`_est_incise_seule`, `main.py`). En mode « lues », le
  morceau-confiance envoyé au serveur serait donc **muet**. Il faut un **drapeau
  explicite** sur la requête de synthèse (« ne retire pas les incises ici »).
  ⚠️ **À écouter avant de généraliser** : un morceau séparé = un **micro-silence**
  possible à la jonction, et sur ce morceau c'est la **vitesse du menu** (celle du
  narrateur) qui s'applique, pas celle du personnage. C'est ce que le banc
  d'écoute servira à juger.

  **Ordre des travaux, mis à jour après la décision** :
  **(1)** le réglage par livre + le bouton (l'audio change : c'est le chantier) ;
  **(2)** un **banc d'écoute** des deux positions sur les vraies phrases, pour
  juger à l'oreille (si « lues » déçoit, il reste « muettes ») ;
  **(3)** l'**item 1** (les formes manquantes) : il devient alors **sans risque**,
  puisque le comportement est un choix par livre — et les 134 incises de 22/11/63
  suivront le réglage choisi pour ce livre.

  ✅ **LIVRÉ le 22/09/2026 (étape 1)** — réglage par livre, bouton, et rien d'autre :
  - **Base** : colonne `books.incises_narrateur` (0 = muettes, 1 = lues), ajout non
    destructif, **défaut 0** → aucun des 10 livres déjà castés ne change de
    comportement tant que le bouton n'est pas touché.
  - **Serveur** : `PUT /api/books/{id}/incises` (enregistre le réglage pour le
    livre) et `GET /api/books/{id}/chapter/{i}/incises` (renvoie les positions des
    incises du chapitre). **C'est le SERVEUR qui calcule les positions**
    (`modules/incises.py`) : la page n'applique aucune règle, elle coupe aux
    positions reçues — donc une seule copie de la règle, et l'item 1 profitera à la
    lecture sans toucher au JavaScript.
  - **Le piège du silence, évité** : `/api/tts` reçoit un drapeau `incise_a_lire`.
    Sans lui, un morceau qui n'est qu'une incise (« , dit-il. ») est remplacé par un
    court silence (`_est_incise_seule`) — vérifié le 22/09/2026 sur `, fit-il
    d'une voix sifflante.` : **SILENCE** sans le drapeau, **dit** avec. La décision
    est isolée dans `_doit_taire_l_incise()`, donc testable sans lancer de moteur.
  - **Page** : bouton `#incises-btn` dans la barre du lecteur, juste après « Vider
    le cache » — son libellé PORTE l'état (« 🔇 Incises : muettes » / « 🗣️ Incises :
    lues par le narrateur »). Il enregistre le choix pour le livre et **relance la
    lecture depuis la phrase en cours** (même mécanisme que le changement de voix
    d'un personnage). Le découpage se fait dans `_morceauxDeLaPhrase` : la phrase
    est coupée aux positions reçues, l'incise part avec la **voix du narrateur**,
    et tous les morceaux gardent le même `sentIdx` (le surlignage ne bouge pas).
  - **Invariant vérifié** : les morceaux **reconstruisent la phrase à l'identique**
    (aucun caractère perdu). Un premier jet perdait le point final d'une incise
    terminale — trouvé par le test, corrigé (la ponctuation orpheline est
    rattachée au morceau voisin au lieu d'être jetée).
  - **Tests** : `_test_morceaux_incises.py` (bout en bout sur le vrai chapitre 10
    de 22/11/63 : colonne, positions, reconstruction, drapeau) — et surtout un
    **test de PARITÉ Python / JavaScript** : le script extrait la VRAIE fonction
    `_morceauxDeLaPhrase` de `frontend/app.js`, la fait tourner sous `node`
    (`_test_morceaux_js.js`) et compare les morceaux un par un. Deux tests de la
    suite ont été mis à jour pour la nouvelle dépendance, sans rien assouplir :
    `test_vitesse_personnage.js` (il **extrait** désormais les vraies fonctions
    `_voixDuNarrateur` et `_morceauxDeLaPhrase` au lieu d'ignorer qu'elles
    existent) et `test_chargement_chapitre.js` (témoin pour le chargement
    d'incises, pour ne pas fausser son compteur d'appels réseau). **Suite
    complète au vert.**
  - **Banc d'écoute LIVRÉ (étape 2)** : `test_voix/LANCER_BANC_INCISES.bat`
    (double-clic) → dossier `test_voix/ecoute_incises_<date>/` avec les WAV
    numérotés, un `index.txt` (ce qu'on demande) et `ECOUTER_LE_LOT.cmd`. Un lot
    a été fabriqué **le 22/09/2026 à 23h13** (14 fichiers) → **écouté et jugé par
    Laurent** (verdict ci-dessous). Chaque fichier passe par le **vrai chemin du
    lecteur** (`/api/tts` avec
    le drapeau `incise_a_lire`, collage des morceaux comme la page), et le banc
    **prévient** si le serveur en marche ne connaît pas encore le drapeau (sinon il
    produirait des incises muettes en croyant tester « lues »).
  - **Premiers enseignements du lot** (à confirmer par l'oreille) :
    (a) en « muettes », `– Ouais, fit-il d'une voix sifflante.` perd **tout** le
    « fit-il d'une voix sifflante » — 0,50 s au lieu de 2,66 s. C'est le
    comportement validé le 18/09 (l'incise part avec son complément), mais on le
    voit ici **en secondes** ;
    (b) quand le personnage est chez un moteur et le narrateur chez un autre
    (**Piper 22 050 Hz / Kyutai 24 000 Hz**, cas de la fillette), les morceaux **ne
    peuvent pas être collés** : le lecteur les joue un par un, et un petit silence
    reste possible à la jonction. Le banc écrit alors **B1, B2** ;
    (c) quand le personnage a la **même voix que le narrateur** (Jake Epping dans
    22/11/63, récit à la 1ʳᵉ personne), « lues » ne change presque rien : c'est
    rassurant, le réglage ne dégrade pas ce livre-là.
  - *Piste notée au passage* : **un seul format audio en sortie du serveur**
    (rééchantillonner chaque moteur en 24 000 Hz mono 16 bits) permettrait de coller
    **aussi entre deux moteurs**. Le lecteur y gagnerait ses morceaux longs (donc la
    modale Android, correctif du 20/09/2026) dès qu'un dialogue change de moteur —
    ce qui arrive **déjà** aujourd'hui entre deux phrases. À ouvrir un jour.
  - **VERDICT DE LAURENT (22/09/2026, à l'écoute du lot)** : « je trouve que c'est
    plus immersif, même si c'est un peu moins qualitatif ». → Pour 22/11/63, la
    décision est **« incises lues par le narrateur »**. Le défaut reste « muettes »
    partout ailleurs : **aucun autre livre ne change sans décision**.
    *Restent sans réponse* les deux questions de détail du banc (petit silence à la
    jonction, vitesse du narrateur sur le morceau d'incise) : rien de gênant n'a
    été signalé, à confirmer à la prochaine écoute.
  - **Reste à faire** : l'**item 1** (étape 3 : les formes d'incises manquantes,
    134 phrases dans 22/11/63).

- [ ] **7. Baisser la fréquence audio fait-il GAGNER en réactivité ?**
  (question de Laurent, 22/09/2026 : « je suis sur un casque audio, ce n'est pas ma
  priorité : si on baisse la fréquence, est-ce qu'on gagne en réactivité ? »)
  **Réponse : non, pas chez nos moteurs.** La fréquence est une propriété du
  **modèle entraîné**, pas un curseur d'exécution : XTTS v2 = **24 000 Hz** natif
  (la chaîne de préparation des extraits le confirme), Kokoro = **24 000 Hz**,
  Kyutai = **24 000 Hz**, Piper = **22 050 Hz** — ces deux derniers mesurés au banc
  des incises du 22/09/2026 (c'est même ce qui empêche de coller un morceau Piper et
  un morceau Kyutai). La vitesse de génération suit **deux** choses : la **taille du
  modèle** et la **durée de parole produite** (donc la longueur du texte) — jamais
  la fréquence de sortie. Repère déjà mesuré : Kyutai calcule **×3,3 plus vite que
  le temps réel** sur la RTX 4060 (27,4 s d'audio en 8,3 s, soit **1 h d'audio
  ≈ 18 min de calcul**).
  **Là où une fréquence plus basse gagne vraiment : le TRANSFERT.** WAV 24 000 Hz
  mono 16 bits = **48 ko/s** (≈ 2,9 Mo/min) ; 16 000 Hz = 32 ko/s ; **MP3 32 kbit/s
  = 4 ko/s**, soit **12 fois moins**. Sur le téléphone à travers le tunnel Tailscale,
  c'est le seul levier que la fréquence ouvre — et il est mesurable.
  *En pratique, la réactivité se joue ailleurs* : le **choix du moteur** (Piper et
  Kokoro sont bien plus rapides que Kyutai 1,6B), la **longueur de la phrase**, et
  surtout le **cache + le préchargement**, déjà en place — on n'attend plus au fil
  du chapitre. Le seul moment où un moteur lent se paie est la **première** écoute
  d'un chapitre (constat déjà écrit, chantier NeuTTS, item 3).
  *Piste à ouvrir un jour, si Laurent le veut* : envoyer l'audio en **MP3 bas débit**
  au lieu du WAV quand la lecture passe par le tunnel (gain de **transfert**, pas de
  génération). À mesurer avant de promettre quoi que ce soit.
  *Outil prêt* : `_mesurer_vitesse_moteurs.py` — il **chronomètre les moteurs** sur
  la même phrase neuve (Piper, Kokoro, Kyutai, Edge) et rapporte le rapport
  « × temps réel », avec le poids du WAV et sa cadence. **Non lancé le 22/09/2026 à
  23h20 : NIMM était éteint** (serveur absent sur le port 8081). À lancer une
  prochaine fois, serveur allumé, pour avoir les chiffres de la machine.
    ⚠️ **Pour l'essayer maintenant : relancer NIMM** (START.bat) — le serveur en
    marche ne connaît pas les nouveaux points d'entrée.
  *Note utile* : dans 22/11/63, une incise au « je » est lue par la voix de
  **Jake Epping**, et `books.narrator_voice` porte **la même voix** — donc
  « garder » ou « confier au narrateur » ne change rien à l'oreille **dans ce
  livre**. La différence s'entend sur les incises de **tiers** (le cas Annette).

- [ ] **2. Narration ENTRE TIRETS au milieu d'une réplique — lue par le
  personnage** (cas signalé : « – il a brandi la baïonnette devant son visage pâle
  aux traits tirés –, « ce sera moi. »). **Mesure : 1 phrase sur 25 216** dans
  22/11/63. Deux raisons de ne pas ouvrir le chantier maintenant : le découpage ne
  coupe pas À L'INTÉRIEUR d'une réplique, et le lecteur construit **une unité
  audio = une phrase, avec une seule voix** (`_voiceForSentence`, `app.js`) ;
  couper la phrase demanderait de **remigrer les 25 216 index** d'attribution pour
  une seule phrase. *Piste, pas ce soir* : mesurer la fréquence du motif dans les
  autres livres avant d'ouvrir quoi que ce soit.
  ⏸️ **SANS RÉPONSE de Laurent au 22/09/2026** : dans la question du « 🔗 même
  voix », il n'a tranché que la case « même voix » (voir item 4). Cet item reste
  donc **ouvert** — à reposer quand le sujet reviendra (il ne coûte rien tant qu'on
  ne l'ouvre pas : **1 phrase sur 25 216** dans 22/11/63).

- [ ] **3. Genre des petits rôles : une fillette lue par une voix d'homme** — la
  « Fillette déguisée » (6 répliques, donc < 8 = petit rôle) porte le genre **H**
  dans la fiche, donc la voix générique **Pierre** (`piper:upmc:1`). Le livre
  compte **86 petits rôles** (67 en voix homme, 19 en voix femme) : le mécanisme
  marche, c'est le **genre de la fiche** qui est faux. Le modèle s'est trompé, et
  le repli `deviner_genre` ne rattrape rien : il connaît « fille », « jeune
  fille », mais **pas « fillette »**, ni « gamine ». Deux correctifs indépendants :
  (a) compléter `_MOTS_F` (`fillette`, `gamine`, `petite fille`, `demoiselle`,
  `nourrisson`…) — gratuit et sans re-cast, mais **ne corrige que les castings
  FUTURS** (la fiche de ce livre restera « H ») ; (b) **dans l'application, le
  genre d'un personnage n'est pas modifiable** : seule sa VOIX l'est (vérifié le
  22/09/2026 : aucun point d'entrée ne touche `cast_fiche`).
  ✅ **DÉCIDÉ par Laurent (22/09/2026) : (a) seulement.** On complète les mots
  manquants de `_MOTS_F` (`modules/voice_casting.py`) — `fillette`, `gamine`,
  `petite fille`, `demoiselle` — et **PAS** de boutons ♀ / ♂ dans la fenêtre du
  casting pour l'instant.
  *Conséquence assumée* : la fiche de 22/11/63 restera « H » (ce sont les castings
  FUTURS qui seront mieux devinés) ; la fillette garde donc Pierre **jusqu'à ce que
  Laurent lui donne une voix à la main** — ce qui reste possible sans code.
  *À faire (petit item, sans risque)* : compléter la liste, puis relancer
  `test_voix/test_reprise_casting.py` (il vérifie `deviner_genre`) et la suite.

- [ ] **4. Deux noms pour la même personne : « Col-bleu sans bretelles » et
  « Bill Turcotte »** — Laurent s'étonne que Bill Turcotte ne soit étiqueté que
  sur la **dernière** phrase du passage. **Ce n'est pas un bug** : le narrateur
  décrit le personnage (« le col bleu sans bretelles ») avant de le nommer, et
  l'incise « grinça Bill Turcotte » donne le nom au modèle — d'où **une étiquette
  par phrase**. Le regroupement 🔗 est déjà en base (`Bill Turcotte → Col-bleu
  sans bretelles`), c'est le travail de Laurent. Ce que 🔗 ne fait pas, par choix
  (les pseudos du *Comte* gardent leur voix) : **il ne réunit pas les voix**. Ici
  les deux sont le même timbre (`kokoro:am_onyx`) mais à **+0 Hz / +4 Hz** — d'où
  un léger changement en pleine scène.
  ✅ **DÉCIDÉ par Laurent (22/09/2026) : OUI, une case « même voix » au moment du
  🔗.** Contrat retenu : la case est **facultative et décochée par défaut** — 🔗
  continue donc de réunir les noms SANS toucher aux voix (ce qu'il faut pour les
  pseudos du Comte de Monte-Cristo) ; **cochée**, elle aligne la voix, la hauteur et
  la vitesse de l'alias sur celles du nom principal (le cas Bill Turcotte /
  Col-bleu : +0 Hz d'un côté, +4 Hz de l'autre aujourd'hui).
  *À faire* : ajouter l'option à `POST /api/books/{id}/cast/group` (même alignement
  que le regroupement automatique, voir `/cast/autogroup`) + la case dans la fenêtre
  du casting.

- [ ] **5. « George Amberson » n'existe pas comme personnage — et c'est une
  bonne nouvelle** — question de Laurent (22/09/2026) : « je vois Jake Epping,
  mais pas Georges Amberson, alors que les 2 devraient être présents, non ? »
  Vérifié dans **toute la base** : **0 ligne** contenant « Amberson » dans
  `voices`, `cast_fiche` et `speaker_attribution`. Le modèle a gardé **« Jake
  Epping »** d'un bout à l'autre du livre, alors que d'autres personnages
  l'appellent « monsieur Amberson » dans le texte. Conséquence : un seul nom,
  **une seule voix** — c'est le résultat SOUHAITÉ (sinon il aurait eu deux voix,
  comme Bill / Col-bleu). L'item ouvert du 19/09 est donc **déjà réglé dans ce
  livre** : `books.narrator_voice` vaut **la voix de Jake Epping**
  (`kyutai:1770_1028_000036-0002`), aussi pour la narration. À revérifier le jour
  où un autre récit à la 1ʳᵉ personne sera casté.

- [ ] **6. Le modèle du casting peut-il PROPOSER les alias ? (idée de Laurent,
  22/09/2026)** — oui, et c'est presque gratuit : la Passe 2 du casting reçoit
  **déjà** la fiche complète (176 noms pour ce livre) et renvoie **déjà** une table
  de `fusion` pour les doublons d'écriture (`_build_passe2_prompt`). Ajouter une
  liste d'**alias proposés** (« Col-bleu sans bretelles » = « Bill Turcotte »,
  avec la raison) **ne coûte aucun appel supplémentaire** sur un nouveau casting ;
  pour un livre déjà casté, un petit appel séparé (outil `_PAYANT_…` + `--je-paie`,
  comme les autres appels facturés). Les propositions iraient dans
  `character_aliases` — la table du 🔗 — donc visibles en retrait sous le nom
  principal et **détachables d'un clic (✂)**, et **jamais appliquées sans
  validation** : un alias faux, c'est deux personnes différentes qui partagent une
  voix au re-cast.
  ✅ **DÉCIDÉ par Laurent (22/09/2026) : ON OUVRE LE CHANTIER**, et les propositions
  seront **affichées dans la table du 🔗** — rangées sous le nom principal, avec ✂
  pour détacher — donc **jamais appliquées sans sa validation**.
  *À faire, dans cet ordre* : (1) étendre la **Passe 2** (aucun appel en plus sur un
  nouveau casting) ; (2) un outil **`_PAYANT_...`** pour un livre **déjà casté**
  (garde-fou `--je-paie`, comme les autres appels facturés) ; (3) l'affichage des
  propositions en attente dans la fenêtre du casting.
  **À faire APRÈS l'étape 3** (les incises) : un chantier à la fois.


## 🟠 Priorité 2 — Voix & casting
- [ ] **🎯 « LE POURQUOI » DU CASTING : l'étiquetage, la source des défauts
  résiduels** — constat de Laurent, 23/09/2026 : « là on fait du cas par cas, ça
  contredit *l'esprit plutôt que la lettre* ; le LLM qui traite le casting
  n'arrive pas à attribuer correctement les rôles, alors qu'on lui mâche le
  travail. Peut-être qu'il faudrait réessayer, comme les choses ont changé, et
  peut-être améliorer le prompt. »
  *Ce que les mesures du jour disent* : l'étiquetage n'est **pas mauvais** — il
  se trompe sur **0,2 %** des phrases (173 morceaux de narration donnés à des
  personnages sur ~81 000). Mais ses erreurs se concentrent sur **cinq formes**
  typographiques que le prompt ne lui explique pas :
  1. **la réplique en tiret** (chez Dumas : 1ʳᵉ réplique entre `«`, suivantes en
     tiret) — prise pour un beat de narration (**79** cas) ;
  2. **le texte LU par un personnage** : testament, acte notarié, lettre de
     mourant, signalement de passeport, signature (**~15** cas sur le surplus
     R8) ;
  3. **le nom interpellé dans la réplique** : « que dites-vous donc là,
     damoiselle Oudarde Musnier ? » attribué à… Oudarde (Notre-Dame ch. 28) ;
  4. **le récit encadré** : le long récit de Bertuccio ou de Caderousse, où la
     narration appartient au personnage qui raconte ;
  5. **les pensées en italique** (22/11/63, Chevalier Errant) dont l'italique a
     disparu à l'extraction (piste non vérifiée : si l'ePub marque `<em>`/`<i>`,
     une étiquette « italique » par morceau rendrait ces cas décidables).
  *Les trois leviers, dans l'ordre de simplicité* : (1) **le découpage** —
  mâcher encore mieux (c'est gratuit et déjà bien avancé) ; (2) **le
  post-traitement** — nos règles R1..R8 corrigent l'aval ; (3) **le prompt** —
  lui apprendre ces cinq formes, avec les exemples réels qu'on a maintenant.
  *L'essai qui rendrait la réponse mesurable* : **re-caster un livre sur une
  copie** (le chapitre d'essai n° 37 existe pour ça ; les verrous « je garde »
  sont préservés), puis **comparer** les étiquettes avec les actuelles : combien
  de ces cinq formes restent ? Le chiffre avant/après tranche.
  *Document à écrire* (le pendant de `PROBLEMATIQUE_decoupage_voix.md`, pour le
  casting) : ce que le LLM reçoit, les cinq formes, les leviers, un jeu d'essai.
  **À faire à froid, une chose à la fois.**

- [ ] **🧪 MESURER LE CASTING IA SEUL, avant d'ajouter du contexte narratif** —
  protocole proposé par Claude (23/09/2026), à exécuter **avant** toute
  construction. *La question de Laurent* : un humain repère sans effort qui
  parle parce qu'il lit le chapitre en continu (qui est présent, à qui c'est le
  tour, le ton). Donner ce contexte au casting — résumé de scène, personnages
  présents — le rendrait-il meilleur ? Ou en deux passes (notes de scène, puis
  casting) ?
  *Pourquoi ne pas construire tout de suite* : (1) **le taux d'erreur du casting
  IA pris seul n'a jamais été mesuré** ; (2) le contexte **intra-chapitre**
  existe déjà (le prompt reçoit le chapitre entier et la fiche personnages) —
  c'est le contexte **entre chapitres** qui manquerait plausiblement (qui reste
  présent, l'identité du « je » d'un livre à l'autre, une relation qui explique
  un ton) ; (3) une architecture à **deux passes** double l'appel payant et
  **accumule les erreurs** : une passe « notes » fausse, invisible, pollue
  silencieusement le casting qui s'appuie dessus.
  *Protocole* : **1.** un échantillon difficile (Monte-Cristo T3 ch. 8, dialogue
  en tiret et Bertuccio qui raconte ; Notre-Dame ch. 55, longue lecture ; un
  chapitre d'entretien à citation imbriquée ; un chapitre de Shantaram pour le
  cas « Le narrateur » / « narration ») ; **2.** une **vérité de référence
  humaine**, morceau par morceau, faite **à neuf** (pas une relecture de ce que
  l'IA a produit) — c'est le travail le plus coûteux, et le seul qui rende la
  suite mesurable ; **3.** faire tourner `voice_casting.py` **sans aucune règle**
  de migration, comparer → taux d'erreur par chapitre **et la liste des erreurs
  à lire** (c'est elle qui dit si le manque est du contexte ou autre chose) ;
  **4.** seulement si le taux le justifie : refaire **avec** une ligne de
  contexte inter-chapitres, même échantillon, même vérité ; **5.** décision —
  casting fiable → on ne construit rien ; le contexte corrige → construire avec
  le chiffre exact du gain et du coût ; le contexte ne corrige pas → le problème
  est ailleurs (confusion entre personnages, consignes 8/9, structure du
  prompt).
  *Ce que le protocole ne dit pas* (délibérément) : ni le format du contexte, ni
  le prompt à deux passes, ni où stocker un résumé — pas d'implémentation sur une
  hypothèse non vérifiée.
  *Note de Cline (23/09 au soir) — **la mesure gratuite est FAITE** :
  `test_voix/_mesurer_casting_erreurs.py` (+ lanceur `MESURER_LE_CASTING.bat`)
  sur les 4 chapitres difficiles. Résultat, en séparant ce qui est défendable de
  ce qui ne l'est pas :

  | Chapitre | Erreurs **dures** | Taux |
  |---|---|---|
  | Notre-Dame ch. 55 (le long mémoire) | **60** | 6,47 % |
  | Monte-Cristo T3 ch. 8 (Bertuccio) | 7 | 1,47 % |
  | Dialogues désaccordés ch. 9 (entretien) | 0 | 0 % |
  | Shantaram ch. 6 (récit à la 1ʳᵉ personne) | 1 | 0,03 % |
  | **TOTAL** | **68** | **1,52 %** |

  « Dures » = une réplique lue par le narrateur, ou un locuteur que le casting
  ne connaît pas. À part : 27 « discutables » (une incise seule chez un
  personnage — la consigne 8 dit non, l'oreille tranche) et une liste « à lire »
  qui n'est **pas** un compte (le dialogue continu d'un personnage n'est pas une
  erreur : c'est ce qui a fait croire à 62 % sur le livre d'entretien avant
  correction de l'outil).
  *Ce que ça dit* : le casting est bon sur 3 chapitres sur 4 ; **un seul cas
  concentre 60 des 68 erreurs** — le chapitre 55 de Notre-Dame, où un personnage
  lit un long mémoire. C'est donc **ce chapitre qu'il faut lire** (verité de
  référence humaine) avant de conclure quoi que ce soit sur le contexte
  narratif : lire un mémoire officiel par le narrateur est-il une faute, ou un
  choix acceptable ? **Premier travail de la prochaine session**, et il coûte
  une lecture, pas un euro.
  *Note de Cline (23/09/2026, juste après la mesure) — **les cas sont lus, et
  deux biais de l'outil sont apparus.** Les 68 « erreurs dures » ne sont pas
  toutes des erreurs d'attribution, loin de là :
  1. **46 des 60 de Notre-Dame ch. 55 ne sont pas des fautes de l'IA.** Ce sont
  trois noms — Évêque_de_Verdun (35), Olivier_le_Daim (8),
  Gouverneur_de_la_Bastille (3) — qui **existent dans le texte** et que l'IA a
  **bien** identifiés comme locuteurs... mais qui ne sont pas dans `voices` :
  l'app les lit donc avec la **voix du narrateur** (repli silencieux, `app.js`
  l. 1592 ; `ARCHITECTURE.md` l. 1991-1994). C'est un **trou de casting** — une
  voix à créer —, pas une erreur d'attribution. Vérifié en base : ces trois noms ont
  0 fiche dans `cast_fiche` et 0 alias. Seule vraie faute du lot : **2 morceaux
  de narration** donnés à Olivier_le_Daim (#826 « En cet instant Olivier le
  Daim rentra. », #829 « C'est lui qui prit la parole : »).
  2. **Trois des 14 « répliques au narrateur » sont en fait des incises seules**
  (#136 « dit le roi. », #165 « interrompit le roi. », #379 « repartit le roi… »)
  — or la **consigne 8** demande justement de les mettre en narration : l'IA a
  obéi. L'outil range « réplique » et « incise » dans la même famille sans les
  distinguer : **défaut de l'outil**, à corriger (gratuit). Les 13 autres incises
  seules du chapitre sont, elles, données à un personnage (le roi, Gringoire,
  Coictier, Coppenole) : c'est la famille « à discuter », où l'oreille tranche.
  *Ce qui reste vraiment en cause* — **21 morceaux sur 4 481 phrases (0,47 %)**,
  et c'est **un seul type de défaut** : un **morceau de dialogue ou de récit
  continu donné au narrateur**. Notre-Dame, 11 morceaux : #125 (le mémoire lu),
  #143 (« – Voilà des bêtes qui sont chères, dit Louis XI. »), #152, #236,
  #381-382, #422-426, #665 ; Monte-Cristo T3 ch. 8, **7 morceaux, #456 à #476**
  (paragraphes du récit de Bertuccio, entre guillemets) ; Shantaram #3. Plus les
  **2 morceaux de narration** donnés à Olivier_le_Daim (point 1).
  → Ordre de grandeur corrigé : **de l'ordre de 1 % au plus**, et **aucun**
  chapitre où le casting se trompe en masse. Conclusion provisoire (à confirmer
  par l'oreille de Laurent) : **le contexte narratif n'est pas le levier.** Les
  leviers gratuits restent le balisage des répliques en tiret, les cinq formes
  de dialogue, et la **création des trois voix manquantes** de Notre-Dame.
  Liste de lecture prête : `_essais/_a_lire_casting.txt` (chaque cas avec sa
  ligne complète ; dossier `_essais/`, hors dépôt).

  *Vérifié avant d'écouter (23/09/2026)* : les cas sont **toujours en base** —
  69 des 73 de Notre-Dame, **20 sur 20** à Monte-Cristo T3 ch. 8, 2 sur 2 à
  Shantaram. Seuls 4 ont été corrigés par la migration du matin (#210, #220,
  #829, #845, passés en narration : c'est juste). Comparaison faite **par
  position dans le texte**, **jamais** par le texte du morceau : « Sire ! » et
  « cria le roi. » reviennent des dizaines de fois dans le chapitre, et un
  appariement par texte compare le mauvais morceau — premier essai **faux**,
  refait dans la soirée. Détail savoureux : #826 (« En cet instant Olivier le
  Daim rentra. ») reste attribué à Olivier_le_Daim, mais comme ce nom n'a pas
  de voix, le repli sur le narrateur **produit le bon résultat sonore** : un
  défaut d'étiquette **invisible à l'oreille**.

  *Puis l'oreille de Laurent, et son verdict (23/09/2026, même soirée)* : après
  écoute dans le lecteur, il tranche net — « quelque chose ne va pas du tout
  dans ce livre » (Notre-Dame) et, pour Monte-Cristo, « c'est de la narration
  dans de la narration : il faut que ce soit Bertuccio **ou** le narrateur, les
  deux mélangés c'est étrange ». Ses relevés sont **exacts** : dans un même
  discours du roi, il a entendu narration → Jacques_Charmolue → Louis XI, et la
  fin de réplique « Il ne m'arrache pas une dent qui ne soit un diamant. » lue
  par le narrateur. **La mesure ne voyait rien de tout ça** : elle ne comptait
  que 4 familles « propres », et un locuteur jamais nommé dans son chapitre
  n'y entrait pas.
  *Mesure refaite avec deux indicateurs neufs* (`_essais/_mesurer_desordre_tmp.py`) :
  **la voix change en pleine parole** (un morceau attribué à un AUTRE personnage
  sans qu'une réplique s'ouvre, ou la narration qui poursuit une réplique après
  une incise) → **182 morceaux à Notre-Dame** (1,50 % de ses 12 171 phrases),
  **1 seul** à Monte-Cristo T3 ch. 8 ; et **locuteur jamais nommé dans son
  chapitre** → **739 morceaux** (6,07 %) — une **alerte**, pas un compte :
  Frollo n'est réellement nommé nulle part dans « Lasciate ogni speranza ».
  Deux vrais défauts en sont sortis : un locuteur nommé « **Narrateur** »
  (majuscule : ce n'est pas la convention `narration`) sur 68 morceaux de la
  NOTE de 1832, et « **JaquesCoppenole** » (orthographe fautive) sur 14 morceaux
  du ch. 6, alors que le reste du livre dit Jacques_Coppenole — **deux
  personnages pour un seul**.
  *Deux leçons de méthode, écrites pour ne pas les repayer* : (1) un critère
  trop **grossier** a d'abord compté 208 « coupures » à Monte-Cristo (c'étaient
  les tours de parole normaux du dialogue), un critère trop **large** ensuite
  1 134 à Notre-Dame (c'était le narrateur qui décrit) — c'est le critère
  ci-dessus qui tient, vérifié sur les deux livres ; (2) **jamais de `-replace`
  PowerShell sur un script accentué** : `Set-Content -Encoding UTF8` a corrompu
  les tirets et les guillemets du script (`'—'` devenu `'â€”'`), le détecteur ne
  reconnaissait plus les répliques et les chiffres étaient **faux** — même
  famille de piège que le 16/09.

  *Et un point rassurant* : la « contradiction » du casting par la migration
  (Bertuccio, Beauchamp, où l'IA avait raison) est **déjà réparée** — c'est la
  restauration des 53 morceaux du 23/09.

  *Décisions de Laurent (23/09/2026, fin de soirée)*, après son écoute :
  **1. La règle du récit encadré** — formulation de Laurent, à appliquer telle
  quelle : « si un personnage raconte une histoire, il devient le narrateur le
  temps du récit. Quand son récit finit, c'est le narrateur du livre qui reprend
  son rôle de narrateur. » Donc, dans un bloc encadré de guillemets, **la narration
  appartient à qui raconte**, et **l'incise suit la même règle** : jamais
  d'aller-retour entre deux voix dans le même récit (c'est exactement l'étrangeté
  qu'il a entendue sur Monte-Cristo T3 ch. 8). À mesurer avant d'appliquer :
  combien de morceaux de narration dans les récits encadrés, et sur quels livres.
  **2. Notre-Dame de Paris reste TEL QUEL** pour le moment (« je ne suis pas sûr de
  lire tout de suite ») : les 182 cas sont instruits et écrits, on ne répare pas
  maintenant. Espoir de Laurent, à garder tel quel : « d'ici 1 mois on aura
  tellement progressé qu'il se castera pour 0,10 € ».
  **3. L'évêque de Verdun** : toute sa tirade est lue par le narrateur, et il n'a
  pas de fiche de personnage — cas compris, rien à faire pour l'instant.

  *Question ouverte de Laurent, posée le 23/09/2026 au soir* : **faut-il
  uniformiser la ponctuation des textes** « à nos normes » avant le casting, pour
  faciliter le travail du LLM et du découpage ? Il observe « des `--`, des `«`,
  parfois rien, parfois même `-- «` ». **Mesuré le soir même** sur les 15 livres de
  la bibliothèque (outils `_essais/_formes_dialogue_tmp.py` et
  `_essais/_motifs_dialogue_tmp.py`) :
  - `--` (deux traits ASCII) : **0 occurrence**, partout. Le guillemet droit aussi
  (0). Donc ces deux formes ne viennent **pas** de la bibliothèque — reste à
  savoir où Laurent les voit (question posée) ;
  - en revanche **deux tirets coexistent** : `—` **14 858** fois et `–` **6 983**
  fois (32 % des tirets sont des demi-cadratins) : c'est la vraie hétérogénéité ;
  - « tiret ET guillemet » collés : **2 cas seulement** (tiret AVANT guillemet,
  dans « Dialogues désaccordés ») ; et **la convention classique existe bel et
  bien** : `«` + **espace insécable** + tiret moyen = **159 fois** dans le seul
  tome 3 de Monte-Cristo. Ma première mesure disait « 0 » : elle cherchait une
  espace **normale**, alors que l'édition écrit une espace **insécable** (U+00A0)
  et un tiret **moyen** (U+2013). Leçon de plus : **ne jamais supposer un
  caractère**, afficher ses codes (`repr`) — c'est Laurent qui a vu l'erreur ;
  - **42,8 % des lignes n'ont aucune marque** — et pour deux livres c'est presque
  tout : « Dialogues désaccordés » 99,4 %, « Lazarille de Tormès » 96,6 %. Là, il
  n'y a **rien à uniformiser** : l'information manque, et aucune normalisation ne
  peut l'inventer.
  *Puis Laurent apporte une correction décisive* : lui voit, dans Monte-Cristo,
  le guillemet PUIS le tiret, et des guillemets « jamais fermants ». Il a raison
  sur les deux tableaux : l'école enseigne la convention **moderne** (tiret
  seul), Monte-Cristo suit la **classique** (guillemets qui courent + tirets
  dedans). La mesure ci-dessous, refaite, lui donne raison — mes premiers
  chiffres (« 386 blocs », « 62 % ») étaient **faux** et sont corrigés ici.

  *Ce que Laurent voit, et qui change la conclusion (mesure refaite)* : dans
  Monte-Cristo, **chaque réplique** peut s'ouvrir par `«` + insécable + tiret, et
  **les guillemets ne se ferment pas** (tome 3 : **676 guillemets ouverts pour
  372 fermants**, donc **304 jamais fermés**). La vraie signature du **récit
  encadré** n'est donc pas « un guillemet non fermé » (il y en a partout), mais
  **une longue SÉRIE de paragraphes qui commencent par un guillemet** — le
  guillemet est reposé à chaque paragraphe du récit. Mesuré
  (`_essais/_series_guillemets_tmp.py`) :
  - Monte-Cristo T2 : série la plus longue = **251 paragraphes** ; T3 **165** ;
    T1 28, T4 40, T5 31, T6 9 ;
  - partout ailleurs les séries sont **courtes** — 22/11/63 : 4, Shantaram : 3,
    Notre-Dame : 6 : ce sont des citations normales, pas des récits.
  Conclusion pour la règle de Laurent : elle se détecte par **la longueur de la
  série** (seuil à calibrer), et elle est **massive dans Monte-Cristo**. On ne
  touche pas aux guillemets : ils portent l'information.

  *Ce que ça implique* : un filtre « normes maison » se justifie, mais **plus
  étroit qu'imaginé** (deux tirets à ramener à un seul, espaces à uniformiser), et
  il ne réglera ni Lazarille ni le livre d'entretien. Point important pour la
  suite : nos règles de **découpage** ne se servent **pas** des tirets
  aujourd'hui (`modules/decoupage.py` coupe sur la ponctuation forte ; la règle
  « dialogue » s'appuie sur un beat à deux-points ou verbe de parole) — donc
  uniformiser ne changerait presque rien au découpage **tant que** le découpage
  n'apprend pas à reconnaître un tiret comme début de tour de parole (ce qui est
  justement le manque de Notre-Dame). Et le filtre ne doit **jamais** toucher les
  fichiers EPUB ni le texte affiché : seulement la version d'analyse, comme pour
  le « ! » (voir ARCHITECTURE.md, « le texte affiché garde son `!` »).
  *Décision* : **mesurer avant de construire** — sur 2 ou 3 livres, comparer
  avant/après normalisation : combien de répliques correctement reconnues, combien
  de morceaux mieux découpés. Gratuit, lecture seule, et ça évite d'y croire sur
  parole.



- [ ] **🗣️ Renommer « Le narrateur » en « Lin » (Shantaram, livre 33)** — retour
  d'écoute de Laurent, 23/09/2026 : « un personnage qui doit être Lin, j'imagine.
  Lin n'existe même pas dans le casting. » Mesure : le casting a bien un
  personnage « **Le narrateur** » (voix `fr-FR-HenriNeural`, **verrouillé**, 4 912
  répliques), et le texte du livre appelle son héros « **Lin** » 606 fois (et
  « Linbaba » 69 fois). Le renommage touche : `voices` (1 ligne), `cast_fiche`
  (1), `speaker_attribution` (4 912) — « Lin » n'existe nulle part, donc aucun
  doublon. *Outil de diagnostic* : `_essais/_renommage_personnage.py` (lecture
  seule). L'application n'a **pas** de route de renommage : il faudra un petit
  outil d'atelier (copie datée avant, contrôle après), ou l'ajouter au casting.

- [ ] **🗣️ Récits à la PREMIÈRE personne : la narration et le héros ont deux
  voix** (constat du 23/09/2026, en écoutant Shantaram). Dans un récit à la
  1ʳᵉ personne, **c'est le héros qui raconte** : il devrait donc y avoir UNE voix,
  pas deux. Mesure sur Shantaram (livre 33) : « narration » = **14 713** phrases
  (48,6 %) lues par la voix du narrateur du livre (`fr-CH-ArianeNeural`, une voix
  **féminine**) et « Le narrateur » = **4 912** phrases (16,2 %) lues par
  `fr-FR-HenriNeural` (un homme). Exemple entendu : « — Fais venir trois
  taxis », ai-je dit… (Henri), puis trois morceaux plus loin « Une demi-heure
  plus tard, **j'**étais à l'arrière d'un taxi… » (Ariane) — la voix change au
  milieu du récit. *Les autres livres de la même famille sont à vérifier* :
  22/11/63 (56 % de narration), Souvenirs d'une gamine (52 %), Lazarille (72 %).
  *Deux options à trancher avec Laurent* : (a) **fusionner** — tout mettre sur la
  voix du héros (cohérent avec le livre) ; (b) **garder** la voix du narrateur du
  livre pour la narration et celle du personnage pour ses paroles (choix
  esthétique, mais il faut alors que la voix du narrateur soit choisie exprès).

- [ ] **🎯 Le chapitre d'essai devient le TEXTE DE RÉFÉRENCE, puis on compare les
  LLM (DeepSeek en premier)** — demandé par Laurent le **21/09/2026 au soir** :
  « Quand il sera parfait, il servira de texte de référence, et on fera le cast
  avec d'autres LLM (Deepseek en priorité), il était moins bon que Gemini avant
  le travail qu'on a fait, peut-être que maintenant les 2 se valent. » Et sur
  l'écoute : « c'est nettement mieux qu'avant. C'est même excellent ! »
  *Ce qui est en place* : le **livre n°37** « 22/11/63 - chapitre d'essai (Sadie) -
  decoupage » — **un seul chapitre**, 81 429 caractères, **1248 morceaux** en mode
  dialogue, **14 beats**. Copie fabriquée par `_creer_epub_chapitre.py`, importée
  par l'API (`_importer_epub.py`) : le livre n°28 de Laurent n'est **jamais**
  touché, et le chapitre peut être re-casté autant de fois qu'on veut
  (~0,06 $ la passe, mesure du journal).
  *État des correctifs du même soir* : quatre défauts trouvés **à l'oreille de
  Laurent**, tous **dans notre code** et aucun dans le prompt — **deux livrés**
  (apostrophe typographique, beat sans verbe de parole « Puis : ») et **deux en
  attente** (incise isolée « m'a-t-elle demandé. », acronymes URSS / TSBD). Les
  deux derniers **ne demanderont aucun re-cast** : ils agissent à la synthèse
  (retrait d'incise, table de prononciation).
  *Protocole prévu, quand Laurent jugera le chapitre **parfait à l'oreille*** :
  on rejoue **le même chapitre** avec les autres moteurs d'IA — **DeepSeek**
  d'abord (~1 centime le chapitre, clé déjà en place), puis Mistral et le moteur
  local — et on compare **morceau par morceau** les étiquettes obtenues
  (`_comparer_decoupage_livre.py`, `_mesurer_sans_signe.py`, `_zoom_passage.py`).
  Le texte est identique, le découpage est identique : **seul le LLM change**,
  ce qui rend la comparaison directe. Les pistes de prompt (règle « un morceau
  qui annonce une réplique est du récit », numéros de paragraphe, liste
  `melange`) restent **en réserve** pour cette étape — elles n'ont pas été
  testées faute de défaut mesurable, pas faute d'idée.
  *Pourquoi ça compte* : DeepSeek était **moins bon que Gemini** avant ces
  travaux ; s'ils se valent maintenant, il devient une **alternative** (autre
  fournisseur, tarif différent).

- [ ] **🎭 Casting : tri par âge, libellé plus court dans les fenêtres étroites,
  et une voix qui ne doit pas être remplacée en silence** — trois demandes de
  Laurent, notées le **21/09/2026** (retour d'écoute de 6 h).
  1. **Tri par âge** : « des boutons juste pour trier les voix par âge pour le
     moment : Enfant 👦, Jeune 👨‍🦱, Adulte 🧑‍🦲, Vieux 👴 ». Les valeurs
     existent déjà dans ses **annotations d'écoute** (`CRITERES_VOIX["age"]` :
     `enfant`, `jeune`, `adulte`, `mur`, `vieux`) — **335 voix annotées** au
     21/09/2026 (enfant 7, jeune 84, adulte 157, **mûr 73**, vieux 14).
     **✅ LIVRÉ le 21/09/2026** :
     - **c'est un FILTRE** : quatre boutons 👦 Enfant / 👨‍🦱 Jeune / 🧑‍🦲 Adulte /
       👴 Vieux, plus « Tous les âges » ; cliquer sur « Jeune » **n'affiche que
       les jeunes**, et le bouton actif affiche la catégorie choisie ;
     - **un filtre Homme / Femme** sur les mêmes lignes (♀️ Femmes / ♂️ Hommes /
       « Hommes et femmes ») : l'âge est celui de la **voix portée**, le genre
       celui de la **fiche** du personnage ;
     - **« mûr » est retiré** : la valeur disparaît de `CRITERES_VOIX`
       (`main.py`), et les **73 voix** qui la portaient ont été **migrées vers
       « adulte »** (`data/annotations_voix.json`, copie datée
       `...bak_avant_4_ages_20260921_1904`) — sans cette migration, l'API aurait
       refusé toute modification sur ces 73 fiches (elle rejette les valeurs hors
       liste). Âges après migration : **adulte 230, jeune 84, vieux 14,
       enfant 7** ;
     - parce que le serveur sert **une seule liste**, les 4 âges valent **aussi**
       pour les menus d'annotation de la fenêtre **« Écouter les voix »** (c'est
       la question de Laurent : « tu peux modifier dans "écouter voix" également ? »
       → oui, et **sans double travail**) ;
     - une ligne jamais annotée (âge inconnu) **ne passe aucun filtre d'âge** :
       c'est voulu — on cherche ce qu'on a entendu, pas ce qu'on ignore ;
     - le filtre **se combine** avec la recherche et avec la barre d'état, et il
       est **remis à zéro** à la fermeture de la fenêtre (comme la recherche :
       jamais de filtre oublié qui ferait croire à des personnages disparus).
     *Vérifications* : `test_voix/test_filtre_age_casting.js` (**30 contrôles**,
     rien à allumer) ; `test_ids_ecran.py`, `test_lire_moi.py` et les autres tests
     au vert (**36 tests** au total).
     **Ses décisions, dans ses mots** (21/09/2026) :
     - c'est un **FILTRE**, pas un tri : « On filtre selon le critère
       sélectionné. Cliquer sur "jeune" n'affiche que les jeunes. Les boutons
       qui sont actifs affichent la catégorie. » ;
     - **« mûr » disparaît** des voix : « On garde juste enfant ; jeune ;
       adulte ; vieux » → les **73 voix annotées « mûr » sont rangées dans
       Adulte** (migration de `data/annotations_voix.json`, **avec copie datée**
       — et la valeur est retirée de la liste proposée, sinon elle réapparaît
       dans les menus) ;
     - **en plus, un filtre Homme / Femme** : « Idéalement un filtre ; Homme /
       Femme et les 4 âges. »
     *Où* : sur les **lignes de personnages** du casting (leur voix a un âge et
     un genre), à côté des deux barres existantes (« Femmes / Hommes » des voix
     proposées, « État des personnages »).
  2. **Le texte de l'aperçu des voix est trop long** dans les fenêtres étroites :
     « le texte est très gros, avant il tenait sur une ligne ». Diagnostic : ce
     n'est pas la police, c'est le **libellé** — `♀️ Amélie 🇫🇷🇬🇧 Mûre grave — 🎎`
     (symbole de genre + prénom + deux drapeaux + âge + timbre + icône du
     moteur) dans un menu large de **45 %** (`.cast-voice-select`) ; avant,
     « Amélie 🇫🇷 — Kokoro » tenait sur une ligne. Correctif proposé : **libellé
     court** (symbole + prénom + drapeau) dans les deux fenêtres étroites
     (casting et « Voir qui parle »), **libellé complet** là où il y a la place
     (fenêtre « Écouter les voix »).
     **22/09/2026 — suite : le « fond très clair » et la « grosse police » ne
     viennent PAS de l'application.** Laurent, en regardant le pied du lecteur :
     « Quand j'ouvre le menu où j'ai toutes les voix, la police de caractère est
     très grande, sur fond très clair. » Vérifié dans `frontend/styles.css` :
     **aucun fond blanc n'y existe** (toutes les couleurs sortent de `:root` —
     `--bg #0d0d0d`, `--bg-surface #161616`, `--bg-card #1c1c1c`…), et
     `color-scheme: dark` est déclaré depuis le **15/09/2026**. Ce qu'il voit est
     donc la **liste déroulante dessinée par le téléphone** (un `<select>`
     natif) : ses couleurs et sa taille de police appartiennent à Android, pas à
     nous — **aucun CSS ne les atteint**, ni `font-size`, ni `background`.
     Deux issues possibles, **à trancher avec Laurent** :
     **(A)** **raccourcir les libellés** (le correctif déjà proposé au point 2
     ci-dessus : symbole + prénom + drapeau dans les fenêtres étroites) — petit,
     sûr, et la ligne tient alors sur une ligne ; mais le fond clair **reste**,
     puisque c'est le téléphone qui le dessine ;
     **(B)** **remplacer la liste déroulante par une fenêtre de l'application**
     (fond sombre, police choisie, libellés complets comme il les demande) —
     c'est un chantier plus lourd, à mener sur les **trois** menus de voix (une
     ligne du casting, « Voix de cette phrase », et la voix du narrateur).
     **Sa question, et la réponse mesurée** : Laurent a demandé s'il était
     possible de **forcer un saut de ligne** dans le libellé d'une voix — « si
     oui, on laisse sur la 1ère ligne : Prénom - drapeaux - âge et timbre ; sur
     la 2ème ligne : moteur - nom du personnage portant la voix / LIBRE ».
     **La réponse est NON**, et elle a été **mesurée** le 22/09/2026
     (`test_voix/test_libelle_deux_lignes_rendu.py`, Chromium) : un libellé qui
     porte un saut de ligne occupe **exactement la même hauteur** qu'un autre —
     le navigateur **aplatit** le saut, même avec `white-space: pre-line` sur les
     options (la règle s'applique bien à l'option, la hauteur ne bouge pas).
     Seul reste le repli **automatique** d'un libellé trop long — c'est ce que
     Laurent voyait —, mais il est **subi** : on ne choisit pas où il tombe. Le
     saut de ligne et la règle CSS ont donc été **retirés le jour même** (garder
     du code sans effet ferait croire que ça marche) ; la trace est dans
     `app.js` (`_libelleVoix`) et `styles.css`, pour ne pas refaire l'essai.
     **Conséquence** : les deux voies ci-dessus restent les seules, et (B) est la
     seule qui donnera ses **deux lignes choisies**.
     **CHOIX DE LAURENT, 22/09/2026 : la VOIE (B).** Sa réponse : « B — remplace
     le menu par une liste NIMM : deux lignes comme je les veux, fond sombre,
     petite police. » La voie (A) — libellés courts — **n'est donc pas retenue**
     pour l'instant.
     *Ce que ça veut dire, concrètement* : le **menu déroulant** laisse la place à
     une **liste de l'application** — de vrais éléments de page, donc **fond
     sombre, police choisie**, et lisible sur **deux lignes** :
       1. symbole, prénom, drapeaux, âge et timbre ;
       2. icône du moteur, puis l'état de la voix (« · LIBRE », « · Edmond »,
          « · narrateur », « · partagée (2) »).
     Chaque ligne garde un **▶ d'écoute**, et l'on choisit en tapant la ligne (au
     lieu du changement dans le menu).
     *Plan en trois étapes* — une par session au plus, chacune utilisable seule :
       **1.** le panneau **« Voix de cette phrase »** (un personnage, un choix :
         le plus simple, et le plus rapide à juger à l'œil sur le téléphone) ;
       **2.** le **casting** : une ligne de personnage par menu déroulant, donc le
         plus gros morceau ;
       **3.** la **voix du narrateur**, dans le pied du lecteur.
     *Risque annoncé et accepté* : **un tap de plus** pour changer une voix (le
     bouton montre la voix actuelle, il ouvre la liste), là où le menu déroulant
     s'ouvrait d'un seul tap. En échange : plus de fond clair, plus de grosse
     police, plus de lignes coupées au hasard.
     *À faire dans le même mouvement, sinon la suite de tests rougit* (c'est
     voulu : ces tests disent la vérité sur l'écran) : `test_voix/test_voix_phrase.js`
     (il vérifie `voice-phrase-select` et extrait `_remplirMenuVoixPhrase`),
     `test_voix/test_filtre_genre.js`, `test_voix/test_voix_ecoutables.js` et
     `test_voix/test_etat_casting.js` (ils extraient `_construireMenuVoix`), plus
     les `getElementById` des menus dans `frontend/app.js` (contrôlés par
     `test_voix/test_ids_ecran.py`).
     **✅ ÉTAPE 1 LIVRÉE le 22/09/2026 — le panneau « Voix de cette phrase ».**
     Le menu déroulant `#voice-phrase-select` a **disparu de la page et du
     code**. À sa place : un **champ de recherche**, un **compteur** (« 175 voix »),
     et une **liste de l'application** — chaque voix sur **DEUX lignes**
     (`♀️ Anna 🇫🇷 adulte grave` puis `🧬 · LIBRE`), un **▶** par voix pour
     l'écouter, et **un tap sur la ligne** pour choisir ; la voix portée par le
     personnage est marquée d'un **✔** et d'un liséré doré.
     *Ce qui a été fait, dans l'ordre* : `_libelleVoix` **scindé** en
     `_identiteVoix()` (symbole, prénom, drapeaux, âge, timbre) et
     `_iconeMoteurVoix()` (l'icône du moteur), ce qui garde le libellé **d'une
     ligne** partout ailleurs (badges, tiroir des voix libres, fenêtre d'écoute) ;
     une fonction **pure** `_lignesVoixListe()` qui rend les lignes (groupes
     Femmes / Hommes / Autres, tri par prénom, recherche, voix **hors liste**
     gardée sous « ⚠️ Voix actuelle ») ; `_peindreListeVoixPhrase()` qui les
     dessine ; `_choisirVoixPhrase()` qui reprend **exactement** l'ancien
     gestionnaire `change` ; `_apercuVoixPhrase(voixId, btn)` pour que **chaque ▶
     écoute SA voix**.
     *Deux défauts trouvés par le test, et corrigés* : la 2e ligne affichait
     **deux espaces** avant le « · » (la marque d'état arrive **déjà** précédée
     d'une espace), et la voix **hors liste** n'avait aucune 2e ligne définie.
     *Fichiers* : `frontend/index.html` (`#voice-phrase-liste`,
     `#voice-phrase-recherche`, `#voice-phrase-recap`), `frontend/styles.css`
     (`.voix-liste-*`), `frontend/app.js` — copies datées
     `*.bak_avant_liste_voix_20260922`, assets en `?v=20260922-4`.
     *Tests adaptés* (ils vérifiaient le menu déroulant) :
     `test_voix/test_voix_phrase.js` (la fonction pure, **50 contrôles**),
     `test_voix/test_libelle_voix.js` (les deux morceaux du libellé),
     `test_voix/test_ids_ecran.py` (côté page). *Vérifications* :
     `LANCER_TOUS_LES_TESTS.bat` — **TOUT EST OK**.
     *À voir par Laurent* : taper sur une phrase, puis choisir une voix — deux
     lignes par voix, fond sombre, la voix portée marquée d'un ✔, et la
     recherche pour retrouver un prénom dans 175 voix.
     **Son essai, et l'ajustement demandé le soir même** : « C'est beau, j'adore !
     Sur la ligne qui montre [moteur][nom personnage/LIBRE] : police blanche. La
     taille est ok. » La **2e ligne** passe donc en **BLANC** comme la première
     (elle était en gris, `--text-muted`), la taille ne bouge pas, et le contrôle
     de rendu le vérifie désormais (`rgb(232, 227, 218)`). Assets en
     `?v=20260922-5`.
     *Suite* : **étape 2** (les menus du casting) puis **étape 3** (la voix du
     narrateur).
     **✅ ÉTAPE 2 LIVRÉE le 22/09/2026 — les menus du CASTING.**
     Le `<select>` de chaque ligne de personnage a disparu : à sa place, un
     **BOUTON** (« ♀️ Anna 🇫🇷 — 🧬 », ellipse si c'est long) qui **déplie la
     LISTE sous la ligne du personnage** (un seul encart ouvert à la fois,
     hauteur limitée à 240 px, défilement à l'intérieur — le personnage concerné
     reste juste au-dessus, on ne peut donc pas se tromper de destinataire).
     *Les règles du menu sont GARDÉES telles quelles* — c'est le point sensible,
     et les tests qui les protégeaient ont été **réécrits sur la nouvelle
     structure plutôt que supprimés** :
       - le **filtre « Voix proposées »** (Toutes / Femmes / Hommes) limite
         toujours la liste ;
       - la **voix actuelle reste TOUJOURS visible**, même si le filtre la cache
         (groupe « ⚠️ Voix actuelle ») ou si son moteur est éteint ;
       - « **Pas de voix (Kyutai éteint)** » et « **Voix introuvable** » restent
         distincts, et le prénom du catalogue s'affiche au lieu de l'identifiant
         technique ;
       - la règle de **partage / déplacement** (choix explicite, jamais de
         substitution muette) est **inchangée** : `choisirVoix()` reprend le corps
         de l'ancien gestionnaire `change` à la lettre.
     *Architecture* : `_lignesVoixPersonnage()` (fonction **pure**, éprouvée sans
     DOM), `_boutonVoixPersonnage()` + `_libelleVoixBouton()`,
     `_basculerListeVoixPersonnage()`. La fonction de liste du panneau a été
     renommée **`_lignesVoixListe`** : elle sert désormais les DEUX endroits, et
     son ancien nom (« Phrase ») serait devenu trompeur.
     *Défaut trouvé par les tests, et corrigé* : la voix hors liste s'affichait
     **au-dessus de son titre** (« ⚠️ Voix actuelle ») — un `unshift` de trop dans
     le bon ordre ; le titre passe maintenant en premier.
     *Tests réécrits* (ils éprouvaient le menu déroulant) :
     `test_voix/test_filtre_genre.js` et `test_voix/test_voix_ecoutables.js`
     (sur la fonction pure, **sans faux DOM** : on éprouve la règle, pas le
     dessin), `test_voix/test_etat_casting.js` (borne de tranche) et
     `test_voix/test_tiroir_voix_libres.js` (l'annulation ET le verrou remettent
     l'ancienne voix : les deux sont vérifiés maintenant, pas une seule).
     *Fichiers* : `frontend/app.js`, `frontend/styles.css` (`.cast-voice-btn`,
     `.voix-liste-encart`), assets en `?v=20260922-6` — copies datées
     `*.bak_avant_liste_voix_20260922` (prises avant l'étape 1).
     *À voir par Laurent* : ouvrir le casting, taper sur le bouton de voix d'un
     personnage — la liste se déplie dessous, deux lignes par voix, au thème.
     *Suite* : **étape 3** (la voix du narrateur, dans le pied du lecteur).
  3. **Une voix ne doit pas être remplacée toute seule** : quand le moteur
     Pocket TTS s'est endormi (panne du matin), Laurent a retrouvé **une autre
     voix** sur son personnage — « ça m'oblige à re-sélectionner la voix pocket
     et la remettre sur le personnage ». Cause **à établir** : le menu d'une
     ligne de personnage dont la voix n'est pas proposée retombe sur sa première
     option — reste à voir si cette valeur est **enregistrée** au passage.
     C'est exactement ce que la règle du 14/09/2026 interdit : *jamais de
     substitution silencieuse*. Son idée, notée telle quelle : un bouton
     **« sauvegarder le casting »**, pour pouvoir revenir à un état connu.
  *Vérifications à prévoir* : un test JS sur le **libellé court** et sur les
  **boutons d'âge** (même méthode que `test_recherche_casting.js`), et un test
  qui **échoue** si la voix d'un personnage change sans que Laurent l'ait
  demandé.

### Retours d'écoute du 18/09/2026

- [ ] **Kokoro allemand et thaï : ça EXISTE (vérifié le 19/09/2026)** — idée de
  Laurent : « il faudrait télécharger les voix Kokoro en allemand et thaï, je
  crois qu'elles existent. Je ferais des mélanges avec ces voix pour Kokoro dans
  NIMM Voix ». Vérification faite (page officielle **et** API Hugging Face) :
  **Kokoro v1.0 n'a NI allemand NI thaï** — ses langues sont l'américain (11F/9M),
  l'anglais britannique (4F/4M), le japonais (4F/1M), le mandarin (4F/4M),
  l'espagnol (1F/2M), le français (**une seule voix : `ff_siwis`**), le hindi
  (2F/2M), l'italien (1F/1M) et le portugais-brésilien (1F/2M).
  **Mais Laurent avait raison** : les fine-tunes communautaires existent, tous en
  **Apache-2.0** (licence notée d'avance : utilisables, et **mélangeables**).
  *Allemand* — le plus utile :
  - `cryptomilk/kokoro-german-kerstin` : fournit `voices/df_kerstin.bin` **et**
    `df_kerstin.pt` — même format que nos banques de voix, et la convention
    `df_` (deutsch féminin) suit celle de Kokoro, comme notre `ff_` français ;
  - `crane-local-ai/Kokoro-82M-v1.0-German-ONNX` (97 téléchargements) : un
    **Kokoro allemand COMPLET** (`onnx/model.onnx` + `voices/df_kerstin.bin`) →
    de quoi faire tourner un moteur Kokoro allemand de bout en bout ;
  - `kikiri-tts/kikiri-german-base-51speakers-synthetic` : **51 locuteurs**
    allemands, mais **un seul** voicepack livré (`voices/victoria.pt`) : les
    autres voix sont **dans** `kikiri_german_base_51spk_ep4.pth` (~2 Go), à
    extraire — travail technique, à ne tenter que si les autres ne suffisent pas.
  *Thaï* — le plus prêt à l'emploi : `kunato/wayu-kokoro-thai-v1` (Apache-2.0)
    fournit **12 voicepacks `.pt`**, déjà nommés par âge et timbre
    (`f_teen_bright`, `f_elderly_soft`, `f_mid_warm`, `m_elderly_deep`…) →
    directement mélangeables comme nos voix de l'atelier.
  *Où* : le travail se fait dans **NIMM Voix** (téléchargement, fusion des
  banques, mélanges), pas ici. *À vérifier là-bas, avant tout mélange* : que les
  vecteurs `.pt`/`.bin` allemands et thaïs ont bien la **même dimension de
  style** que les nôtres (256), sinon le mélange est impossible ; puis
  **écouter**, comme toujours (une mesure ne remplace pas l'oreille).
  *Note de licence* : Apache-2.0 pour les trois dépôts → aucune restriction, et
  la provenance est notée ici (règle d'or de l'atelier NIMM Voix).
  ⏰ **Laurent le redemande le 19/09/2026 au soir** : « on regarde si on peut
  importer la voix allemande ? » → **prochaine chose à faire, après les
  onglets** (chantier dans NIMM Voix, pas ici).
  ✅ **Suite du 20/09/2026 — l'import allemand EST FAIT dans le lecteur.** Le
  chantier NIMM Voix a abouti le matin même : trois lots écoutés, **10 voix à
  accent allemand retenues** (« je crois qu'on est plutôt pas mal avec ça »),
  figées dans `voix_generees/voices-accent-allemand.bin` (recettes et verdicts :
  `sorties/validation_accent_allemand_20260920/FICHE_VOIX.txt`). Côté lecteur,
  les **deux étapes** de la fiche ont été faites, dans l'ordre :
  (1) **timbres fusionnés** dans `voices-v1.0.bin` → **84 → 94 voix**, copie
  datée `.bak_avant_accent_allemand_20260920`, et **aucune des 84 voix d'avant
  n'a changé** (vérifié par empreinte md5 voix par voix) ;
  (2) **10 lignes** dans `KOKORO_VOICES` (`modules/tts.py`), région
  🇩🇪 **Allemagne (NIMM Voix)**, sur le modèle des voix NIMM
  (`kokoro:fa_eva`, `fa_victoria`, `fa_bernd`, `fa_martin`, `fa_bernd_fort`,
  `fa_victoria_trio`, `fa_martin_trio`, `fa_eva_aigue`, `fa_bernd_grave`,
  `fa_martin_grave`).
  ⭐ **Décision du 20/09/2026 : elles entrent à 0 étoile** — dans la « règle des
  paliers » (`voice_casting.py`), une voix notée 0 est **écartée du casting
  automatique mais reste choisissable à la main** : elles ne peuvent donc pas
  se glisser toutes seules dans un livre français. **C'est Laurent qui les
  notera** dans « 🎧 Écouter les voix » (toutes les rubriques), et le report
  (`_appliquer_annotations_voix.py`) a été **appliqué le 20/09/2026 :
  35 changements**, dont **Eva, Bernd, Martin, Greta et Wolfgang passés à
  ⭐⭐**. Ces voix restent pourtant **écartées du pool automatique** du casting,
  parce que leur rôle est annoté **« étranger »** (`_voix_reservee`,
  `voice_casting.py`) : c'est voulu, et c'est ce qui les empêche de tomber sur
  un personnage français. **Renommées le 20/09/2026** (demande de Laurent : « juste des prénoms
  allemands »), après son taggage dans « Écouter les voix ». Les **identifiants
  ne changent pas** (`fa_*`) : ses notes d'écoute (étoiles, âge, timbre, accent,
  rôle) **restent attachées**. Eva (`fa_eva`), **Viktoria** (`fa_victoria`),
  Bernd (`fa_bernd`), Martin (`fa_martin`), **Klaus** (`fa_bernd_fort`),
  **Greta** (`fa_victoria_trio`), **Otto** (`fa_martin_trio`), **Lena**
  (`fa_eva_aigue`), **Wolfgang** (`fa_bernd_grave`), **Heinrich**
  (`fa_martin_grave`). Les 10 prénoms ont été **vérifiés uniques** dans tout le
  catalogue (aucun doublon avec une voix d'un autre moteur), et la
  correspondance avec les timbres d'origine est écrite **en commentaire** dans
  `modules/tts.py` (Eva = df_eva 25 %, Lena = df_eva 50 %, Klaus = dm_bernd
  85 %, etc.).
  *Vérifié* : les 10 voix **parlent** par le vrai chemin du lecteur
  (`test_voix/_tester_voix_kokoro_importees.py` : 2,28 à 2,71 s d'audio, crête
  -4,0 à -5,7 dBFS, aucune muette), `/api/voices` en propose **110**,
  `test_pool_casting.py` (pool **inchangé**) et `test_voix_ecoutables.py` verts,
  et l'aperçu de `_appliquer_annotations_voix.py` lit bien les 10 nouvelles.
  *Outils* : `test_voix/_importer_voix_kokoro.py` (aperçu par défaut,
  `--ecrire` avec copie datée automatique) et
  `test_voix/_tester_voix_kokoro_importees.py`. Détails dans ARCHITECTURE.md.
  **Reste ouvert dans cet item** : le **thaï** (même route, quand Laurent
  voudra) et la mise à l'oreille des voix allemandes dans le lecteur.

- [ ] **Kokoro FRANÇAIS : quelqu'un a-t-il entraîné un modèle ?** — question de
  Laurent, 19/09/2026 : « vérifier si personne n'a fait du fine tuning Kokoro
  pour le Français (je rêve, mais c'est gratuit) ».
  *Première recherche, le 19/09/2026* : sur Hugging Face, `kokoro french` ne
  renvoie **rien**, et `kokoro-fr` **un seul** modèle, qui n'est pas du français
  (un anglais « espeak-free »). Donc **rien trouvé pour l'instant** — mais la
  recherche reste à reprendre plus finement : il faut éplucher les **fine-tunes
  déclarés** de `hexgrad/Kokoro-82M` (56 modèles sur sa page, plus les
  quantifications et les adaptateurs), car un modèle français peut porter un nom
  qui ne contient pas « kokoro » (comme l'allemand, signé `kikiri-tts`).
  *Pourquoi ça vaut le coup* : le français de Kokoro ne tient aujourd'hui qu'à
  **une seule voix** (`ff_siwis`) — c'est justement pour ça que l'atelier NIMM
  Voix a fabriqué ses 30 voix par mélange. Un vrai fine-tune français donnerait
  des voix natives, sans mélange.
  *À faire* : reprendre la recherche sur l'API Hugging Face par **modèle parent**
  (`base_model:finetune:hexgrad/Kokoro-82M`) et par **langue** (`fr`), puis
  écouter ce qui existe. **Rien ne sera intégré avant écoute** (règle de
  l'atelier).
  🔎 **Et pour l'entraîner soi-même : le chantier EXISTE DÉJÀ** (piste Gemini du
  19/09/2026 examinée le soir même). L'atelier **NIMM Voix** a ouvert un chantier
  « vraie voix française par entraînement » le **11/09/2026** : outil
  `voicepack_train` (`vivienhenz24/voicepack_train`, Apache-2.0) **installé et
  vérifié** (PyTorch 2.11 + CUDA 12.8, RTX 4060 reconnue, phonémisation française
  OK), corpus de **1 879 extraits d'entraînement + 99 de validation** préparé
  (le livre audio de Laurent, `outils/corpus/voix_pro/`, avec `manifest_ok.csv`).
  **Pourquoi ça s'est arrêté (trouvé le 19/09/2026 dans `logs/_train_pro.log`)** :
  lancé le 11/09 à 23h03, il a **échoué dès le step 1** sur
  `AssertionError: (758, 512)` — **Kokoro a une fenêtre de 512 phonèmes**, et un
  extrait du corpus en fait **758** : le programme refuse et s'arrête. C'est
  exactement le « **corpus à re-découper plus court** » déjà noté dans le
  `LISEZ-MOI_des_dossiers.md` de l'atelier.
  ✅ **La VRAM n'est PAS le problème** : le journal mesure **4,25 Go au pic** sur
  les 8 Go de la 4060.
  *Sur la piste de Gemini, le tri honnête* : **juste** sur « Kokoro est petit, la
  4060 suffit, 3-5 Go de VRAM » (mesuré : 4,25 Go) ; **faux** sur « 15-30 min
  d'audio suffisent » — l'essai de 7,5 min du 11/09 a donné une voix **quasi
  identique au départ**, et le trainer exige des extraits couvrant **les 510
  longueurs de phrase** (référence : 13 100 extraits, LJSpeech) ; **inutile** sur
  « prends les scripts de `kikiri-tts` » (l'outil est déjà installé ici) ; son
  « Stage 2 » correspond à l'option **`--lr-decoder > 0`** de l'outil, déjà
  repérée par l'atelier — **à garder pour plus tard**, quand l'entraînement du
  vecteur seul donnera déjà un résultat.
  *Prochaine étape, dans NIMM Voix* : (1) repérer et **redécouper les extraits
  au-delà de 510 phonèmes** (le `manifest_ok.csv` et `filtrer_manifest.py` sont
  là pour ça) ; (2) relancer `_train_pro2.cmd` ; (3) **écouter**. Rien ici ne
  demande de matériel nouveau.
  ⏱️ *Combien de temps ? — mesuré, pas deviné (19/09/2026)*. Question de Laurent :
  « quelques heures ? ». Le premier essai (VoxPopuli, **57 extraits**, 10 époques)
  a tourné de **15h45 à 16h16**, avec un checkpoint par époque : 15:45, 15:47,
  15:50, 15:51, 15:53, 15:56, 16:00, 16:06, 16:11, 16:16 → **570 étapes en
  ~31 min**, soit **≈ 3,3 s par étape** (et les époques **s'allongent** : 2 min
  puis 5 min 20 — les extraits longs coûtent cher).
  `_train_pro2.cmd` ne demande que **3 époques** sur **1 879 extraits** =
  **5 637 étapes** → **≈ 5 h** au rythme de VoxPopuli, **davantage** (8 à 12 h)
  car le livre audio a des extraits plus longs que VoxPopuli.
  → **Donc : une NUIT**, pas « quelques heures ». Bonne nouvelle :
  `--save-every-epoch` écrit `voice_pack_epoch001.pt`, `002`… → **on peut écouter
  et convertir après CHAQUE époque** sans attendre la fin.
  *Méthode de l'atelier, à appliquer* : ne pas se fier à cette extrapolation —
  **relancer et laisser tourner 20-30 min**, puis lire la croissance de
  `training/voix_pro/history.jsonl` (une ligne par étape) : c'est le **rythme
  réel** sur CE corpus.
  ⚠️ *Rappel de licence* : le corpus vient de **`Reference Pro/Stephen King -
  22_11_63`** (audiobook **acheté**) → **usage privé** : la voix obtenue ne se
  partage jamais, elle vit dans une banque séparée (`voix_privees/`) et sa fiche
  porte la mention « usage privé — ne pas diffuser ».
  ⏸️ *Mettre en pause et reprendre plus tard : OUI, c'est possible* (vérifié le
  19/09/2026 dans `kokoro/pipeline.py`, ligne 153 : `if voice.endswith('.pt')` —
  la voix de départ peut être un **FICHIER**). Il n'existe **pas** d'option
  `--resume`, mais on relance un entraînement en pointant `--voice-init` sur le
  dernier checkpoint :
  `--voice-init "..\training\voix_pro\voice_pack_epoch002.pt"`.
  *Les quatre choses à savoir* :
  1. l'optimiseur Adam **repart de zéro** — la reprise n'est pas
     mathématiquement identique à un entraînement continu, mais **ça
     fonctionne** : le pack garde ses acquis et continue de s'affiner ;
  2. il n'y a **pas de scheduler** de taux d'apprentissage (le `--lr` reste le
     même) : rien à recaler, tant mieux pour la reprise ;
  3. couper fait perdre l'**époque en cours** — les époques **terminées** sont
     sauvées (`voice_pack_epochNNN.pt`) ;
  4. `--save-every-epoch` numérote les époques **de la session** : à la reprise,
     utiliser un **autre `--out-dir`** (`training\voix_pro_2`) pour ne pas
     écraser les fichiers de la veille. Et `apres_train_pro.py` attend
     `voice_pack_trained.pt` (le **FINAL**) : pour écouter une session
     partielle, copier le checkpoint voulu sous ce nom.
  *Où ça se conduit* : dans **l'atelier NIMM Voix** (VS Code ouvert sur
  `G:\NIMM Voix`), là où sont le `.venv`, les scripts et les corpus — Cline y
  travaille avec les règles de CET atelier.

- [ ] **Fish Audio (S2 / S1-mini) : le clonage avec ÉMOTIONS et plusieurs voix —
  à évaluer** (question de Laurent, 19/09/2026 : « jette un œil sur Fish Audio,
  c'est un truc chinois qui clone des voix à la volée ; je ne sais pas si c'est
  embarqué dans un service web, ou s'ils ont partagé le logiciel à part du
  site »). **Réponse vérifiée le 19/09/2026 : les DEUX.** Il y a le service web
  (`fish.audio`, avec playground et API payante) **et** le logiciel complet,
  librement téléchargeable : dépôt GitHub `fishaudio/fish-speech` (« SOTA Open
  Source TTS », 32,7 k étoiles), documentation `speech.fish.audio`, poids sur
  Hugging Face, avec WebUI, ligne de commande, serveur d'inférence et Docker.
  *Ce qui le rend intéressant pour nous* (c'est exactement ce qui manque aux
  moteurs actuels) :
  - **clonage à partir de 10 à 30 s** d'audio (XTTS et Pocket TTS demandent
    davantage, ou tronquent à 30 s) ;
  - **marqueurs d'émotion dans le texte** : `(angry)`, `(whispering)`,
    `(laughing)`, `(sighing)`… et en langage naturel pour S2 (`[laugh]`,
    `[whispers]`, `[super happy]`) — de quoi donner un vrai JEU à un personnage ;
  - **plusieurs locuteurs dans un seul audio de référence**, avec les jetons
    `<|speaker:i|>` : une seule génération peut contenir plusieurs voix ;
  - **génération multi-tours** (le contexte précédent améliore la suite).
  *Pistes de « voix de qualité » demandées par Laurent : c'est la plus sérieuse
  rencontrée jusqu'ici.*
  *Modèles* : **S2-Pro (4B)** sur Hugging Face (le plus récent, le meilleur) ;
  **S1-mini (0.5B)** — version distillée **légère** — et **S1 (4B)**, qui lui est
  **propriétaire** (non téléchargeable : ne pas confondre).
  *Langues* : le **français est supporté** (13 langues pour S1, ~50 pour S2).
  *Licences — ATTENTION, c'est le point sensible* : le code **et** les poids sont
  passés à la **« Fish Audio Research License »** (révisée le 07/03/2026), qui
  autorise **gratuitement la recherche et le NON-COMMERCIAL** — la licence
  définit explicitement le « Non-Commercial Purpose » comme l'**usage personnel
  (hobbyist)** ou l'évaluation, donc le nôtre est **couvert** ; S1-mini est sous
  **CC-BY-NC-SA-4.0**. En revanche : **tout usage commercial exige une licence
  séparée** (business@fish.audio), il faut **garder la notice d'attribution** et
  afficher « Built with Fish Audio » si on distribue. À retenir pour les items
  « PARTAGE » et « Diffusion » : **aucun usage commercial** avec ces voix.
  S1-mini est de plus **« gated »** (compte Hugging Face + acceptation des
  conditions obligatoires).
  *Contrainte matérielle — MESURÉE le 19/09/2026, et c'est le point qui
  bloque* : la documentation d'installation (`speech.fish.audio/install`) exige
  **24 Go de VRAM** pour l'inférence, et un système **Linux ou WSL** (« System:
  Linux, WSL » ; le `torch.compile` n'est même **pas supporté sous Windows
  natif**). Or la machine de Laurent a une **RTX 4060 (8 Go de VRAM)** et 32 Go
  de RAM : **trois fois moins de mémoire graphique que nécessaire**. Les
  performances annoncées (RTF 0,195 ; ~100 ms avant le premier son) sont mesurées
  sur une **NVIDIA H200**, ce qui n'a rien à voir.
  → **S2-Pro est hors de portée en l'état** sur cette machine. Le dépôt prévoit
  heureusement un mode **CPU-only** (`BACKEND=cpu`), lent mais utilisable pour
  fabriquer quelques voix, et **S1-mini (0,5B)** — plus léger — mérite un essai
  (l'outillage actuel du dépôt ne vise plus que S2 : il faudrait une version
  antérieure du dépôt pour S1-mini).
  *Ordre conseillé, dans l'esprit de l'atelier (« on essaie sur un petit cas
  avant d'investir du temps »)* : (1) juger d'abord la **qualité du français et
  du clonage** avec le **playground web** (`fish.audio`, gratuit) sur nos propres
  extraits — 10 minutes suffisent ; (2) **seulement si** c'est nettement mieux
  que Pocket TTS / NeuTTS / XTTS, monter l'installation locale (WSL2 + GPU, ou
  S1-mini, ou CPU) ; (3) **rien n'est intégré ici avant d'avoir écouté**.
  ⚠️ Ne pas oublier la cohabitation GPU : Kyutai et XTTS ne peuvent déjà pas
  tourner en même temps sur cette machine (voir l'item correspondant).
  *Où* : l'essai se fait dans **NIMM Voix**, avec la règle de l'atelier :
  **licence notée d'abord**, puis écoute et mesure sur du français.


  remontée de Laurent (18/09/2026), après un essai dans l'atelier **NIMM Voix** :
  « j'ai écouté un extrait de POCKET TTS, qui est très prometteur. Apparemment on
  peut "fabriquer" des voix pour ce moteur aussi, et il me semble qu'il est très
  léger. »
  L'atelier le connaît déjà de nom — `test_voix/MEMO_pour_NIMM_Voix.md` a été
  écrit « à réutiliser sur Pocket TTS », et le mémo Kyutai parle de « la méthode,
  à rejouer sur Pocket TTS » : ce serait donc un candidat sérieux pour le
  **cinquième moteur**, **léger** (donc sans bataille pour la carte graphique,
  contrairement à Kyutai et XTTS qui ne peuvent pas cohabiter) et capable
  d'accueillir **nos propres voix**.
  *À faire, dans cet ordre* : (1) l'essai dans **NIMM Voix** — qualité sur du
  français, débit, poids, licence, stabilité ; (2) seulement ensuite, la question
  de l'intégration ici (branchement dans `modules/tts.py` sur le modèle des autres
  services, catalogue de voix, critères d'écoute).
  *Règle de l'atelier* : **ne rien intégrer avant d'avoir écouté et mesuré**.
  **POINT DE DÉPART — ce qui est DÉJÀ ÉTABLI au 20/09/2026** (rassemblé ici pour
  ne pas le refouiller ; tout vient de mesures d'atelier ou de vérifications
  faites ce jour-là) :
  - **moteur installé et opérationnel dans NIMM Voix** :
    `G:\NIMM Voix\outils\pocket_tts\.venv`, **Python 3.14** (`C:\Python314`,
    `torch 2.14.0+cpu`) ;
  - **il tourne sur le PROCESSEUR, pas sur la carte graphique** → il **cohabite**
    avec Edge, Kokoro et Piper… **et avec Kyutai**, le seul à occuper la carte
    (3,8 à 5,6 Go). C'est le premier moteur « lourd » dans ce cas ;
  - **Python 3.14 = la version du lecteur** : contrairement à Kyutai, XTTS et
    NeuTTS (Python 3.12 obligatoire), il n'est pas forcé de vivre à part pour
    cette raison (le README officiel annonce 3.10 → 3.14) ;
  - modèle **français `french_24l`** (641 Mo, dépôt **gated**), poids
    **CC BY 4.0**, code **MIT** ;
  - **recette validée à l'écoute** le 17/09 (verdict « C'est propre ») :
    nettoyage du texte + `--max-tokens 200` + réglages par défaut ;
  - **il CLONE** : un extrait de 3 à 15 s suffit (le moteur tronque à 30 s), et
    la voix **devient plus grave si l'extrait s'allonge** (**133 Hz à 2 s →
    116 Hz à 6,5 s**, mesuré et entendu) ;
  - **débit ≈ 1× le temps réel** en français (variante non distillée, « aperçu »
    chez Kyutai) : **1 h d'audio ≈ 1 h de calcul** → il faudra **pré-générer**,
    le **cache audio** du lecteur prenant le relais ensuite ;
  - **aucun réglage de vitesse dans le moteur** → même remède que Kyutai :
    post-traitement `atempo` du lecteur. **Testé le 20/09/2026 sur Kyutai** (même
    mécanisme) : à **−30 %** le timbre tient (Laurent n'entend qu'un « à peine
    plus grave »), et **−30 % tombe presque juste** pour ramener les ~22 car/s
    de Pocket TTS vers les ~15 car/s d'une lecture naturelle ;
  - **défauts connus, à traiter au montage** : pauses entre segments de **0,8 à
    1,6 s** (l'atelier les ramène à 0,40 s), **niveau irrégulier** (jusqu'à
    ~5 dB *à l'intérieur* d'une phrase — le `modules/audio_gain.py` du lecteur
    est fait pour ça), phrases **de plus de ~350 caractères sautées** ;
  - **vocabulaire limité** : apostrophe courbe (`’`) et tiret cadratin (`—`)
    **absents** → à nettoyer ; attention, il connaît `...` mais **pas** `…`
    (l'inverse du mémo XTTS/NeuTTS) ;
  - **extraits disponibles pour cloner** : `Extraits de voix\Découpage OK`
    (22 MP3 + la banque CML-TTS) ;
  - ⚠️ **une voix Pocket TTS ne se transvase PAS dans Kyutai 1.6B** (autre
    moteur, autres empreintes) : les deux mondes restent séparés.
  *Les trois décisions à prendre AVANT de coder* : (1) **où vit le moteur** —
    dossier `pocket_tts_service/` avec service HTTP local (modèle
    `kyutai_service`, port libre) **ou** intégration plus directe, puisqu'il
    accepte Python 3.14 ; (2) **quelles voix** au catalogue : les extraits de
    Laurent, la banque CML-TTS, et les futures **voix génériques** des petits
    rôles (une voix homme, une voix femme — pas encore choisies) ;
    (3) **allumage** : avec `START.bat` ou **à la demande** (il ne prend pas la
    carte, mais il prend le **processeur** — 6 cœurs, partagés avec Kokoro et
    Piper — et il est lent).
  **ÉTAPE 1 FAITE le 20/09/2026 — installation et MESURES.** Le moteur est
  installé **chez NIMM ePub** : `pocket_tts_service\.venv` (**torch 2.14.0+cpu**,
  `pocket-tts` **3.1.0**, les mêmes versions que l'atelier), dans un
  **environnement à part** (le lecteur reste sans PyTorch) ; les **18 voix** sont
  copiées dans `pocket_tts_service\voix\` (14,4 Mo). Le modèle français
  (641 Mo) était **déjà en cache** : rien à télécharger.
  *Mesures* (`_mesurer_debit.py`, voix **Femme001**, phrases de Monte-Cristo,
  `max_tokens 200`) : chargement du modèle **1,7 s** ; encodage d'une voix
  **3,8 s** ; 125 caractères → **8,9 s d'audio en 7,2 s** (ratio **0,81**) ;
  295 caractères → **14,5 s en 12,0 s** (ratio **0,83**) ; « Non. » → **0,99**.
  **Ratio moyen 0,82** = **1 h d'audio ≈ 49 min de calcul** : le moteur est
  **plus rapide que le temps réel** (×1,2), mieux que le « ~1× » annoncé par
  l'atelier. **Mémoire : 2,0 Go après calcul, pic 2,3 Go** (RAM seulement, la
  carte graphique n'est pas touchée).
  *Deux constats pour la suite* : (1) **brider à 4 cœurs ne coûte RIEN**
  (même 0,82) → on peut laisser 2 cœurs au lecteur, à Kokoro et à Piper ;
  (2) les **phrases courtes** ont un ratio proche de 1 (coût fixe par appel) →
  ne pas hacher le texte en minuscules morceaux.
  *Fichiers créés* : `pocket_tts_service\` — `INSTALLER_POCKET_TTS.bat`,
  `_mesurer_debit.py`, `ECOUTER_LA_MESURE.bat`, `LIRE_MOI.md`, `voix\` (18 WAV),
  `sortie_mesure\` (3 WAV + `rapport_mesure.txt`). **Rien d'existant n'a été
  touché** : aucun fichier du lecteur modifié.
  *Pièges payés au passage, à garder* : `cmd /c <script.bat>` échoue sous
  PowerShell (**lancer le .bat directement** avec `Start-Process`) ; `scipy`
  écrit des WAV **float32** que le module `wave` refuse (**écrire en int16**) ;
  sans `argtypes`/`restype` explicites, `GetProcessMemoryInfo` renvoie
  **toujours 0** (handle tronqué à 32 bits — c'est ce qui affichait « 0 Mo ») ;
  et `python.exe` **bufferise** sa sortie quand elle va dans un fichier
  (`line_buffering=True` dans les scripts de service).
  *Reste à faire* : l'**écoute de Laurent** (`ECOUTER_LA_MESURE.bat`), puis
  l'**étape 2** — le service sur le port **8085**, lancé **sans fenêtre**.
  **DÉCISIONS DU 20/09/2026 (soir) — prénoms, critères, prégénération.**
  *Écoute de Laurent : validée*, avec une réserve de timbre décrite par lui :
  « les voix un peu basse fréquence, comme si on limitait un peu la plage des
  Hertz, moins de grave surtout, et pas mal d'aigus — mais très convenable, la
  voix ne saute pas, la prosodie est bonne ». Essai approfondi prévu au travail
  le lendemain. *(Cette réserve est cohérente avec un codec audio à bas débit :
  c'est le moteur, pas l'extrait.)*
  *Les 18 voix ont DÉJÀ un passé* : ce sont les **mêmes extraits** que les voix
  **`dp_*` de XTTS** (`xtts:dp_femme001` = **Marthe**, `xtts:dp_homme002` =
  **Théodore**, `xtts:dp_homme004` = **Édouard**…), avec **prénom, genre,
  étoiles ET critères d'écoute déjà relevés** par Laurent (âge, timbre, débit,
  accent, registre). Donc : **on reprend les mêmes prénoms** pour
  `POCKET_VOICES` (il retrouvera ses voix) et **on hérite les annotations**,
  avec le même genre d'outil que
  `test_voix/_heriter_annotations_xtts_vers_neutts.py`.
  ⚠️ **Doublons de prénom assumés** : les mêmes extraits portent déjà les mêmes
  prénoms en Kyutai, XTTS et NeuTTS — c'est voulu, et **aucun test ne
  l'interdit** (`test_pool_casting.py` ne contrôle pas les doublons de prénoms).
  *Reste à nommer* : **JEAN_EDGAR** (validé le 18/09, avant le lot). « Jean » et
  « Edgar » sont **libres** parmi les **169 prénoms** déjà utilisés, mais
  « Jean » côtoie « Jeanne » (déjà pris) — à trancher avec Laurent.
  *Icône* : **🎒 Pocket TTS** (choix de Laurent), à ajouter dans
  `FAMILLES_VOIX` (`frontend/app.js`) **et** dans les tests qui la vérifient
  (`test_voix/test_ids_ecran.py`, `test_voix/test_libelle_voix.js`).
  *Prégénération — DÉCISION DIFFÉRÉE (choix de Laurent).* Il teste beaucoup et
  change souvent de voix : **on ne précharge rien pour le moment**. Quand les
  voix seront calées et qu'il écoutera ses livres tranquillement, **précharger
  le plus possible** redeviendra la meilleure option (mesure : 49 min de calcul
  pour 1 h d'audio). À rouvrir dans une session dédiée.
  **ÉTAPE 2 FAITE le 20/09/2026 — LE SERVICE.**
  `pocket_tts_service\servir_pocket_tts.py` (**port 8085**), écrit sur le même
  patron que `servir_kyutai.py` et avec le **même contrat** que les autres
  moteurs (`GET /sante`, `GET /voix`, `POST /tts` en JSON → WAV,
  `POST /recharger`) : le lecteur ne verra pas la différence. Deux
  particularités : **une seule génération à la fois** (le modèle n'est pas
  thread-safe) et **4 cœurs** par défaut (`NIMM_POCKET_TTS_COEURS`), les 2
  autres restant au lecteur, à Kokoro et à Piper. Le texte est **re-nettoyé
  côté service** (apostrophe courbe, tiret cadratin, `…` → `...`) en plus du
  nettoyage du lecteur.
  *Éprouvé* : modèle chargé en **1,6 s**, **18 voix** annoncées, phrases
  générées par HTTP aux ratios attendus (**0,85** et **0,86**) ;
  `tester_service.py` écrit un lot d'écoute (`pocket_tts_service\sortie_ecoute\`)
  avec son `index_ecoute.txt`.
  *À savoir* : la **première phrase d'une voix paie son encodage** (**3,8 s**)
  — le « Non. » a coûté 4,4 s de calcul pour 0,7 s d'audio ; c'est normal, une
  seule fois par voix et par démarrage.
  *Fichiers* : `servir_pocket_tts.py`, `DEMARRER_POCKET_TTS.bat` (allumage à la
  main, pour voir ce que dit le moteur), `tester_service.py`, `LIRE_MOI.md`.
  *Reste* : le lancement **sans fenêtre par `START.bat`**, le **voyant** dans le
  lecteur, puis le **catalogue** (prénoms hérités, icône 🎒) et le
  **branchement** — étapes 3 et 4.
  **ÉTAPES 3 ET 4 FAITES le 21/09/2026 — CATALOGUE ET BRANCHEMENT.** Laurent :
  « si tu es partant pour continuer les étapes 3 et 4, et j'écouterais dans NIMM
  ePub directement ce que ça donne ? »
  *D'abord le « tic » signalé par Laurent* (« j'ai juste le premier audio “non”
  qui ne fait quasi aucun son, juste un tic de quelques millisecondes »).
  Mesure : sur **5 prises** du même texte court, la crête vaut **0,8 / 0,7 /
  45,5 / 18,0 / 4,5 %** — le moteur n'a **aucune graine**, il sort donc un
  quasi-silence **environ une fois sur deux** sur 1 ou 2 mots. Remède mesuré :
  le service **régénère** tant que la crête reste sous **5 %** (4 essais au
  plus, on garde le meilleur). Après correction : **42,8 / 8,2 / 40,1 / 19,2 /
  35,8 %**. Coût nul sur les phrases normales (toujours au-dessus de 60 %).
  *(À savoir : la durée minimale d'un WAV est **0,72 s** — deux textes courts
  donnent des fichiers de même taille mais de contenus différents. C'est le
  moteur, pas le cache.)*
  *Le catalogue* : `POCKET_VOICES` = **18 voix**, prénoms **repris des voix
  jumelles** (Marthe, Solange, Yvette, Henriette, Georgette, Thérèse, Colette,
  Juliette, Madeleine, Marius, Théodore, Édouard, Victor, Robert, Paul, Jules,
  Arthur) + **Edgar** (option A retenue par Laurent pour `JEAN_EDGAR`).
  *Les critères d'écoute* : **hérités** des 17 jumelles NeuTTS par le nouvel
  outil `test_voix/_heriter_annotations_neutts_vers_pocket.py` (copie datée de
  `data/annotations_voix.json` faite — 350 voix au total) : **Laurent n'a rien à
  ré-annoter**. Restent à son oreille : **Edgar** (aucune jumelle) et l'**accent**
  des 18 voix (Pocket TTS garde la diction de l'extrait, jamais mesurée ici).
  *Le branchement* : branche `pocket:` dans `POST /api/tts`, client
  `synthesize_pocket()`, exposition dans `/api/voices` (seulement si le service
  est **prêt**) et dans `/api/voix_catalogue`, icône **🎒** dans `FAMILLES_VOIX`
  (`app.js`) et dans le filtre de la page (`index.html`).
  *La cohabitation* : Pocket TTS porte le drapeau **`cohabite: True`** dans
  `MOTEURS_VOIX` — la bascule de moteur du lecteur ne l'éteint **jamais** (c'est
  le seul moteur qui n'occupe pas la carte graphique) — et `START.bat` le lance
  **sans fenêtre** en même temps que Kyutai (demande de Laurent du 21/09/2026).
  Comme il tourne caché, il **s'éteint tout seul** après **30 min sans une
  seule phrase** (`NIMM_POCKET_TTS_INACTIF`), pour ne pas garder 2,3 Go pour
  rien : c'est le garde-fou ajouté le jour même.
  *Fichiers touchés* : `modules/tts.py` (`POCKET_VOICES`, `synthesize_pocket`,
  `_demander_au_moteur_pocket`, `PocketIndisponible`), `main.py` (branche
  `/api/tts`, `MOTEURS_VOIX`, `basculer_moteur_voix`, `/api/voices`,
  `/api/voix_catalogue`), `frontend/app.js` (`FAMILLES_VOIX`),
  `frontend/index.html` (filtre + `?v=20260921-1`),
  `pocket_tts_service/servir_pocket_tts.py` (garde-fou anti-tic,
  auto-extinction), `START.bat` (lancement sans fenêtre),
  `test_voix/_heriter_annotations_neutts_vers_pocket.py` (**nouveau**),
  `test_voix/LIRE_MOI.md`, `ARCHITECTURE.md`.
  *Vérifications* : **19 tests JavaScript** (0 échec), `test_bascule_moteur.py`,
  `test_import_main.py`, `test_pool_casting.py`, `test_lire_moi.py`,
  `test_ids_ecran.py`, `test_pas_de_secrets.py`, `test_js_syntax.py` : OK.
  Bout en bout **à travers le lecteur** (le vrai chemin : nettoyage, vitesse,
  hauteur, normalisation, cache) : **163 voix** proposées dont **18 Pocket
  TTS**, et 3 phrases synthétisées avec `pocket:Femme001` — crêtes **37,7 /
  46,1 / 69,2 %**.
  *Sauvegarde* : `data/annotations_voix.json` (copie datée par l'outil
  d'héritage). Les fichiers du lecteur sont dans Git, les modifications sont
  décrites ci-dessus.
  **Ce que Laurent doit écouter** : dans NIMM ePub, choisir une voix
  **🎒 Pocket TTS** (par ex. **Marthe**) et lire un chapitre. À juger : la voix,
  la prosodie, et surtout le **débit** (20 à 25 caractères/seconde contre ~15
  pour une lecture naturelle) — le curseur de vitesse du casting, ou le menu du
  narrateur, peuvent compenser.
  *Reste* : le **voyant** détaillé du moteur dans la fenêtre du lecteur (l'état
  est déjà exposé par `/api/moteurs`), **Edgar** (étoiles + critères),
  l'**accent** des 18 voix, et la **prégénération** (différée à la demande de
  Laurent).

- [ ] **XTTS : l'INÉGALITÉ du moteur — constat de Laurent, 16/09/2026**
  Après une écoute longue de Monte-Cristo : « les voix XTTS sont très inégales,
  même pour une même voix : 3 phrases excellentes, puis il hachure, bafouille,
  traîne, monte dans les aigus, ou la prosodie part en vrille. Avec Kokoro, la
  même phrase 50 fois de suite serait lue de la même façon — Kokoro tient mieux
  la route sur le long terme, même si la qualité brute est discutable. »
  *Cause, mesurée* : XTTS **échantillonne** (`temperature` 0,75 par défaut) :
  chaque synthèse est un **nouveau tirage**. Kokoro est **déterministe** par
  construction. Ce n'est pas une question de qualité, mais de **nature**.
  Preuves du même jour : `Non.` a donné 0,53 / 0,79 / 1,03 / 1,11 s selon le
  tirage ; sur 20 tirages de deux phrases, la prosodie jugée « vivante » a varié
  de 2/6 à 8/10 ; et 5 segments de parole sur une phrase de 18 caractères (le
  « hachurage » entendu).
  *Levier jamais testé : la TEMPÉRATURE de génération.* Le service expose
  désormais des **réglages optionnels** (`temperature`, `top_k`, `top_p`,
  `repetition_penalty`, `length_penalty`) via `{"reglages": {...}}` dans POST
  `/tts` — **sans réglage, le comportement ne change pas**. Banc de mesure :
  `test_voix/_banc_stabilite_xtts.py` (même phrase 5 fois × 3 réglages :
  défaut / 0,60 / 0,45), qui compare l'**écart de durée** et le nombre de
  segments. Lanceur double-clic : `test_voix/LANCER_TEST_STABILITE.bat`.
  **Verdict de Laurent après écoute (16/09/2026) : « c'est presque pire. »**
  La série `tres_sage` (0,45) est la **plus mauvaise** : « il accélère, il
  ralentit, les intonations sont étranges ». Et surtout : **à l'oreille, on ne
  peut pas dire quel extrait a la température la plus haute ou la plus basse** —
  le réglage n'apporte donc **rien de lisible**. *Conclusion : baisser la
  température ne stabilise PAS XTTS ; la variabilité est structurelle, pas un
  simple réglage.* Le moteur **reste en place** (avec ses 79 voix) mais ce n'est
  pas la solution à long terme : il faudra expérimenter autre chose (voir les
  pistes ci-dessous et l'item « État de l'art TTS français »).
  *Note de fond (question de Laurent, 16/09/2026)* : « les voix Edge, c'est
  comme Kokoro ? La même phrase sera toujours lue de la même façon ? » **Oui** —
  et c'est la distinction qui explique tout : les moteurs **classiques**
  (Edge, Kokoro, Piper, MMS, MeloTTS — réseaux non autorégressifs) sont
  **déterministes** : un texte → un audio ; les moteurs **génératifs** (XTTS,
  Gemini TTS, NeuTTS — modèles autorégressifs type LLM audio) **échantillonnent**
  → chaque tirage diffère. Or **le clonage zero-shot vient de la famille
  générative** : c'est pourquoi « clonage » et « stabilité » sont aujourd'hui en
  **tension**. La sortie de cette tension passe par le **fine-tuning** d'un
  moteur déterministe (Piper, par exemple) sur une voix donnée.

- [ ] **Pistes de sortie : des voix personnalisées QUI NE VARIENT PAS**
  (ouvert le 16/09/2026, après le verdict XTTS). Trois pistes, dans l'ordre de
  simplicité ;
  **(1) Entraîner une voix sur un moteur DÉTERMINISTE.** Kokoro est un modèle
  de type StyleTTS2 : le fine-tuning existe mais **sans recette publique
  simple** (plusieurs heures d'audio propre + GPU + risque d'abîmer le modèle).
  **Piper** est la piste réaliste : entraînement **documenté**, résultat
  **déterministe** et qui tourne **sur processeur**. C'est la seule voie connue
  pour « ma voix, stable, hors ligne ».
  **(2) Services Google — tarifs relevés le 16/09/2026**
  (`cloud.google.com/text-to-speech/pricing` et la doc Gemini TTS) :
  - **Gemini TTS** (modèles `gemini-2.5-flash-tts`, `-pro-tts`, `3.1-flash-tts`) :
  voix **prédéfinies** (une trentaine, multi-locuteurs possible pour un
  dialogue), mais **le style, l'accent, le rythme et le ton se pilotent en
  langage naturel** — c'est exactement la piste « prosodie adaptée au
  personnage » née le même jour. Tarif : entrée 0,50 $/M tokens texte,
  sortie **10 $/M tokens audio** (25 tokens = 1 s d'audio) → environ
  **0,015 $ la minute d'audio** (≈ 1,4 c€), soit **≈ 9 $ pour 10 heures**.
  Limites annoncées par Google : qualité qui **dérive au-delà de quelques
  minutes** (d'où un découpage), erreurs 500 aléatoires (prévoir des reprises)
  et le modèle peut **lire les instructions** si le prompt est brouillon.
  - **Cloud TTS classique** : Neural2 **16 $/M caractères**, Chirp 3: HD
  **30 $/M**, Studio **160 $/M**, WaveNet / Standard **4 $/M**, avec 1 à 4 M de
  caractères **gratuits** par mois selon la gamme.
  - **Instant Custom Voice (CLONAGE Google)** : **60 $/M caractères**, à partir
  d'un extrait de voix **avec consentement**. Le modèle de voix est **entraîné**
  → clonage **stable**, contrairement à XTTS. Ordre de grandeur : un roman de
  500 000 caractères ≈ **30 $** ; la saga Monte-Cristo entière (≈ 2,5 M
  caractères) ≈ **150 $**.
  **(3) Autres moteurs gratuits** : **NeuTTS-Nano-French** (clonage 3-15 s,
  194 Mo, **sur processeur** — licence « gated » à accepter et dérive possible) ;
  **Kyutai TTS 1.6B** (déjà installé, 35 voix françaises natives — stabilité à
  mesurer).
  *Fiche NeuTTS-Nano-French, relevée le 16/09/2026 sur le dépôt officiel*
  (`github.com/neuphonic/neutts` + Hugging Face `neuphonic`) — **c'est la piste
  retenue par Laurent** :
  - modèles : `neuphonic/neutts-nano-french` (+ variantes **GGUF Q8/Q4**, plus
    légères et plus rapides) ; 0,2 B de paramètres ; **tourne sur CPU en temps
    réel, sans GPU** ; aussi en anglais, espagnol et allemand ;
  - installation : **`pip install neutts`** (PyPI) — le dépôt fournit
    `examples/` et un **`TRAINING.md`** (donc fine-tuning possible plus tard) ;
  - **clonage** : il faut **deux fichiers** — un extrait **`.wav`** (mono,
    16-44 kHz, **3 à 15 s**, propre, parole continue) **et le texte exact de cet
    extrait** (contrairement à XTTS, qui n'a pas besoin du texte) ; le dépôt
    fournit un exemple français : `samples/juliette.wav` ;
  - ⭐ **POINT CAPITAL — la génération est ÉCHANTILLONNÉE mais avec une GRAINE
    (seed)** : sans seed, chaque appel tire au hasard ; **avec un seed imposé,
    mêmes entrées + même seed = audio IDENTIQUE**, sur les deux moteurs (PyTorch
    et GGUF). C'est précisément « la stabilité de Kokoro avec le clonage »
    recherchée le 16/09/2026 — **à vérifier à l'oreille** (le seed est imprimé à
    chaque appel, donc une prise qu'on aime peut être rejouée à l'identique) ;
  - chaque audio généré porte par défaut un **watermark Perth** (marque
    inaudible) — bon à savoir avant tout partage.
  *Reste à faire dans l'atelier NIMM Voix* : installer (`pip install neutts`
  dans un petit venv), télécharger le modèle français, préparer une référence
  (3-15 s + son texte), puis **mesurer la reproductibilité avec un seed fixe**
  (même phrase × 5) et écouter.
  **Suite du 16/09/2026 (annonce de Laurent, atelier NIMM Voix) : NeuTTS est
  installé.** Objectif visé par Laurent : un **moteur unique** qui reprendrait
  les voix déjà construites — les voix Kokoro (dont les 30 « France (NIMM
  Voix) » et leurs mélanges), les voix de la banque CML-TTS, et les 35 voix
  clonées XTTS — donc « unifier Kokoro + XTTS dans le même moteur ». Il parle
  d'un possible **moteur principal de NIMM ePub** « si la piste se confirme ».
  Rien n'est mesuré à ce jour, et **rien n'est ajouté ici** : ce bloc fige les
  questions à remonter à l'atelier NIMM Voix, toutes nées de ce qui a déjà
  invalidé XTTS (cf. ci-dessus).
  1. **Reproductibilité avec un seed fixe** : même phrase × 5, même seed →
     audio identique ? C'est le point qui a fait condamner XTTS ici
     (variabilité structurelle, insensible à la température). Sans cette
     réponse, l'intérêt est limité.
  2. **Babil sur les phrases courtes** : NeuTTS est **aussi autorégressif**.
     Refaire les trois phrases témoins du 16/09/2026 (« Que préférez-vous ? »,
     « Manger ? », « Non. ») et comparer au babil XTTS ; s'il apparaît, les
     deux filets de `xtts_service` (bornage par `max_new_tokens` + rognage du
     résidu après silence) devront être repris.
  3. **Vitesse sur processeur** : temps de synthèse par phrase rapporté à la
     durée audio. La lecture se fait **phrase par phrase avec cache** : un
     moteur plus lent que le temps réel reste utilisable, mais pas agréable à
     la **première** écoute d'un chapitre.
  4. **Tenue sur un long texte** : un chapitre enchaîne 20 à 40 phrases (la
     dérive du clonage instantané est le risque annoncé).
  5. **Accent** : le français de `neutts-nano-french` est-il **natif** ? C'est
     le reproche fait aux voix Kokoro qui a lancé toute cette recherche.
  6. **Référence = wav + texte exact** : les 35 extraits
     (`kyutai_service\voix_fr\cml-tts\fr\`) ont-ils leur transcription
     disponible (CML-TTS en fournit peut-être) ? Sinon, à transcrire une fois.
  7. **Réutilisation des voix Kokoro** : les 30 voix « France (NIMM Voix) »
     sont des **mélanges de styles internes** au modèle Kokoro — on ne peut
     pas en extraire un wav. Les « récupérer » dans NeuTTS suppose donc de les
     **générer puis cloner**. **CORRECTION du 16/09/2026, le test ayant eu
     lieu : l'hypothèse écrite ici est DÉMENTIE.** J'avais prévu que le clonage
     reprendrait l'**accent forcé** du modèle anglais et ne ferait donc que
     déplacer le défaut. Résultat inverse, au verdict d'écoute de Laurent sur
     les 30 voix passées dans NeuTTS
     (`sorties\test_neutts_lot30_20260916\`) : « les accents Kokoro ont
     disparu, les voix ont du caractère (murmure, accent très très léger),
     tout est lu en français très compréhensible ». *Explication retenue, à
     confirmer* : l'extrait de référence ne porterait que le **timbre** — la
     prononciation venant du modèle **français** de NeuTTS, pas de la source.
     Si c'est confirmé, le procédé s'applique à **n'importe quel extrait**,
     même synthétique. ⚠️ **Constat à l'oreille, pas mesure** : la comparaison
     chiffrée de l'index (durée + hauteur face aux voix d'origine) reste à
     regarder, et **la stabilité (point 1) n'est toujours pas tranchée**.
  *Suite du chantier dans NIMM Voix (16/09/2026, annonce de Laurent)* :
  **30 voix Kokoro sur 30** produites en `.wav` par NeuTTS ; chaîne en 3 étages
  (lot Kokoro → **79 références** préparées + transcrites par Whisper → les
  **19 voix libres de droits**) ; nouveaux outils `_preparer_references.py`
  (conversion, rognage, recadrage à 12 s sur le passage le plus parlé,
  transcription) et `tester_neutts.py --dossier-references` (clonage d'un
  dossier entier, chaque référence avec son propre texte). Restent en attente :
  les **60 voix CML-TTS** (préparées, non clonées), les **54 Kokoro
  officielles** (WAV déjà disponibles dans NIMM Voix, texte connu), et le
  **test de stabilité**. *Piste LibriVox évoquée par Laurent* : à vérifier
  l'intérêt, puisque **CML-TTS est déjà du LibriVox** (lecteurs bénévoles de
  livres du domaine public, CC BY 4.0) et que le gisement français y a déjà
  été relevé comme **quasi épuisé** — ~67 lecteurs au total, 25 déjà versés
  (voir l'item « Voix françaises supplémentaires : creuser CML-TTS »). Un
  balayage LibriVox direct apporterait donc surtout des **lecteurs absents du
  jeu**, à trier au cas par cas (audio plus bruité : c'est ce qui avait fait
  écarter le jeu `mls`).
  **Suite du 16/09/2026, fin de soirée (NIMM Voix)** : l'inventaire des
  79 références est confirmé — **35 CML-Kyutai + 25 CML-XTTS + les 19 voix
  libres de droits**. La préparation des **60 CML-TTS** est terminée
  (**523,8 s** d'audio traitée en **114 s**, transcription à **1,4 s** par
  extrait ; leurs extraits font **7 à 8 s**, donc **sans recadrage**), et leur
  clonage a été lancé **automatiquement** par le veilleur 3.
  **Décision de Laurent (16/09/2026), sur la crainte de perdre les accents des
  54 voix Kokoro officielles si elles sont clonées** : « il me reste les voix
  Kokoro, qui elles ont les accents, plus ou moins atténués. Donc je ne perds
  rien, j'ai juste un peu plus de timbre, avec ou sans accents. » Autrement
  dit : les voix Kokoro **restent en place** (moteur local, sans moteur à
  allumer) et les clones NeuTTS ne les remplacent pas — ils les **doublent**
  d'une version française. La question « que perd-on ? » est donc tranchée :
  rien, au prix d'une **liste de voix plus longue** (et des étoiles / critères
  d'écoute à renseigner pour les nouveaux timbres).
  *Si la piste se confirme, l'intégration est déjà cadrée* : licence tranchée
  le 14/09/2026 (composant **externe**, jamais embarqué — NIMM ePub reste
  GPL-3.0 pur) ; le traiter **exactement comme `xtts_service`** (dossier
  `neutts_service\`, port après 8082/8083, `/sante` + `/voix` + `/tts`,
  `INSTALLER_` / `DEMARRER_` en double-clic, gardien de fenêtre) et branche
  `neutts:` dans `/api/tts` (`main.py`).
  **MESURES DU 16/09/2026** (mémo NIMM Voix,
  `G:\NIMM Voix\MEMO_NeuTTS_pour_la_session_NIMM_ePub.md`) — dont une
  **CORRECTION d'une affirmation écrite ici même** : le « modèle de 194 Mo qui
  tourne sur processeur » laissait croire qu'il cohabiterait avec Kyutai ou
  XTTS. **C'est faux** : au pic, NeuTTS occupe **3,50 Go de mémoire vidéo** (sur
  8) — à comparer aux 3,8 Go de Kyutai et d'XTTS : **les trois ne cohabitent pas
  sur la carte**. Sur processeur, en revanche, il cohabite (aucune mémoire
  vidéo) mais il est **~6 fois plus lent**.
  - **Pas de babil** : sur 8 phrases de 4 à 117 caractères, **aucun
    débordement**, durée **proportionnelle au texte** — « Manger ? » **1,10 s**
    (XTTS : 8,49 s), « Que préférez-vous ? » **1,40 s** (XTTS : 9,11 s),
    « Non. » **1,10 s** (XTTS : un résidu de 0,26 s après silence). Les deux
    filets d'`xtts_service` sont donc **inutiles au départ** — à garder
    seulement en secours si une dérive apparaissait un jour.
  - **Vitesse** : **×0,7 le temps réel** sur la RTX 4060 (33,4 s de calcul pour
    25,0 s d'audio) ; **×3 à ×4 sur processeur**. Chargement **~10 s** à chaud.
    Piste de vitesse **non essayée** : les backbones **GGUF Q8/Q4** (195-253 Mo
    au lieu de 915 Mo), via `llama-cpp-python`.
  - **Graine** : `neutts 1.4.1` exécute `torch.manual_seed(seed)` **à chaque
    appel** de `infer` → avec un `seed` fixé dans le constructeur, la
    reproductibilité est **structurelle**. Sans `seed`, le moteur **imprime**
    celle qu'il a tirée (`Using seed N`, sur **stdout**) : une prise peut donc
    être rejouée. L'épreuve d'identité **octet à octet** (SHA-256, 5 prises,
    `seed=42`) est en cours côté NIMM Voix.
  - **Fenêtre** : 2048 tokens ≈ **30 s d'audio, référence comprise** → découper
    le texte à **200 caractères** et recadrer les références à **12 s**, sinon
    **troncature silencieuse**.
  - **Premier téléchargement : 4,2 Go** et non 2,6 — le codec tire en plus
    `facebook/w2v-bert-2.0` (2,2 Go). **Ici, tout est déjà en cache**
    (`C:\Users\Supalol\.cache\huggingface`, 5,3 Go) → installation **sans
    téléchargement**.
  - **Dépôts « gated »**, codec compris ; **`espeak-ng` inutile** (la roue
    `neutts` embarque la DLL et les dictionnaires français) ; filigrane **PerTh**
    invisible sur chaque audio.
  - **Deux pièges d'installation** : torch **≥ 2.11** imposé par `torchtune`
    (2.8 échoue : `cannot import name 'ScalingType'`) ; **`torchao==0.16.0`**
    épinglée en `--no-deps` (la 0.18 a supprimé `torchao.dtypes.nf4tensor`,
    réclamé par torchtune).
  **FAIT le 16/09/2026 (soirée) — le service existe, et il est VÉRIFIÉ.**
  `neutts_service\` est en place (port **8084**, sur le modèle d'`xtts_service`) :
  installation réussie en quelques minutes (roues PyTorch et modèles **déjà en
  cache** sur le PC), **109 voix** annoncées (60 CML-TTS + 19 voix libres +
  30 Kokoro), et **essai de bout en bout réussi sur le processeur**
  (`test_voix/test_neutts_bout_en_bout.py`, 11 contrôles) :
  - **STABILITÉ PROUVÉE, AU BIT PRÈS** : deux synthèses de la même phrase
    donnent exactement le même fichier (**empreintes SHA-256 identiques**).
    C'est la réponse à la question qui avait fait condamner XTTS ici.
  - phrases courtes : « Non. » **0,97 s**, « Manger ? » **1,10 s**,
    « Que préférez-vous ? » **1,46 s** (XTTS : 1,07 / **8,49** / **9,11**) →
    **aucun babil**, et des durées cohérentes avec les mesures de l'atelier
    (1,10 / 1,40).
  - phrase longue : 240 caractères → **12,8 s**, non tronquée.
  **BRANCHEMENT FAIT le 16/09/2026 (soirée, sur le go de Laurent)** :
  `modules/tts.py` (`NEUTTS_VOICES` **généré** par
  `test_voix/_generer_catalogue_neutts.py`, plus `synthesize_neutts`) ;
  `main.py` (branche `neutts:`, fiche moteur 8084 dans `MOTEURS_VOIX`,
  `/api/voices`, `/api/voix_catalogue`) ; `voice_casting.py` (pool : NeuTTS
  **en dernier** dans chaque palier d'étoiles, la raison est écrite dans
  `_pool_par_paliers`) ; `START.bat` (**allume NeuTTS, ne lance plus XTTS ni
  Kyutai** — les deux restent disponibles à la main) ; interface (entrée NeuTTS
  dans la fenêtre de choix du moteur et dans le filtre des familles de voix).
  *Vérifié le soir même* : **288 voix proposées au lecteur, dont 109 NeuTTS**,
  moteur vu comme allumé et prêt, et toute la batterie de tests du projet au
  vert (`test_pool_casting.py` étendu à la 4e famille, `test_import_main.py`,
  `test_ids_ecran.py`, `test_libelles_voix.py`, les tests JavaScript, plus les
  deux tests NeuTTS). Copies de sûreté : `*.bak_avant_neutts_20260916`
  (`main.py`, `START.bat`, `modules/tts.py`, `modules/voice_casting.py`,
  `frontend/app.js`).
  **BASCULE DES VOIX DES LIVRES — FAITE le 16/09/2026 au soir** (objectif de
  Laurent : remplacer les voix de NIMM ePub par NeuTTS à la place d'XTTS et/ou
  Kyutai). **8 livres, 160 personnages** passés de `xtts:` à leur jumelle
  `neutts:` (mêmes prénoms, mêmes timbres) par
  `test_voix/_basculer_voix_xtts_vers_neutts.py` — rapport seul par défaut,
  `--ecrire` copie la base **avant** d'écrire. Après bascule : **160 personnages
  en NeuTTS, 0 en XTTS** (sur 1238 personnages en base). Copie de sûreté :
  `data/nimm_epub.db.bak_avant_bascule_neutts_20260916_2103`.
  *Le cache audio n'a PAS été purgé, et n'a pas besoin de l'être* : les clés de
  cache sont un hachage de (texte + voix + vitesse + hauteur), donc les voix
  NeuTTS ont de **nouvelles clés** et l'audio se régénère tout seul ; les
  anciens fichiers XTTS deviennent simplement inutilisés. Purger ne libérerait
  que **299 Mo** (1885 fichiers) et ferait perdre la relecture instantanée — et
  hors ligne — de tout ce qui a déjà été écouté, tous moteurs confondus.
  **BASCULE DES VOIX KYUTAI — FAITE le 17/09/2026** (demande de Laurent ce
  jour-là : « remplacer les voix XTTS par celles de NeuTTS dans mes castings » —
  or il ne restait **aucune** voix XTTS : c'est le **Kyutai** qui restait).
  *Pourquoi ça comptait double* : `START.bat` n'allume plus Kyutai (seulement
  NeuTTS) — les **63 personnages** concernés (livres 16, 17, 26, 30, 31, 32 et
  **Notre-Dame de Paris**) s'appuyaient donc sur un moteur **éteint**, autrement
  dit un audio injouable : la bascule **répare** ces livres en plus de
  simplifier.
  Outil : `test_voix/_basculer_voix_kyutai_vers_neutts.py` (nouveau, calqué sur
  la version XTTS). Il **vérifie que chaque jumelle `neutts:` existe vraiment**
  chez le moteur *et* dans le catalogue du lecteur, et **refuse d'écrire** si une
  seule voix manque — on ne distribue jamais une voix inexistante.
  *Résultat* : **223 personnages en NeuTTS** (160 + 63), **0 en XTTS, 0 en
  Kyutai**. Copie de sûreté :
  `data/nimm_epub.db.bak_avant_bascule_kyutai_20260917_0511`.
  *Verrous* : les 63 personnages concernés n'étaient **pas** verrouillés, mais le
  script bascule **aussi** les verrouillés — c'est voulu, et c'est la réponse à
  la question de Laurent. Un **verrou protege du re-cast automatique** (il fige
  la voix d'un personnage) ; il n'interdit pas de **corriger un moteur à la
  main**, et il **suit le personnage** : un personnage verrouillé le reste, sur
  sa voix NeuTTS. Les verrous de la base, en clair : **18 Edge, 36 Kokoro,
  11 NeuTTS = 65 au total** (`voices.locked`).
  *Nouvel outil de contrôle* : `test_voix/_etat_familles_voix.py` (lecture seule)
  — combien de personnages par moteur, combien de verrous, et **santé** : chaque
  voix attribuée existe-t-elle dans le catalogue du lecteur ? (état au
  17/09/2026 : **323 voix au catalogue, aucune voix attribuée manquante**).
  Lanceur double-clic : `test_voix\LANCER_OU_SONT_MES_VOIX.bat`.
  *Ce qui reste hors NeuTTS* (sur 1238 personnages) : **470 Edge**, **371
  Kokoro**, **93 Piper**, **81 sans voix**. Edge et Piper **n'ont pas de jumelle
  NeuTTS** (ce sont d'autres voix, figées) ; Kokoro en a 30 — un choix à faire
  plus tard, ce n'est pas une bascule automatique.
  *Le cache audio, une fois de plus, n'a rien besoin de* : les clés sont un
  hachage de (texte + voix + vitesse + hauteur), les voix NeuTTS ont de
  nouvelles clés, l'audio se régénère.
  **RÉVISION D'ÉCOUTE — 17/09/2026 : le verdict de Laurent est NÉGATIF.**
  « La lecture est trop aléatoire en qualité », après écoute des livres basculés
  la veille. C'est un **démenti direct** de ce qui avait justifié la bascule :
  les mesures d'alors portaient sur la **STABILITÉ** (durée d'une phrase,
  empreinte SHA-256 identique entre deux prises) — **jamais sur la qualité
  d'écoute**. Leçon à garder : **stabilité n'est pas qualité**.
  *Deux causes identifiées dans le code, le jour même* :
  (1) **la recollure** — le service redécoupe toute unité de plus de ~200
  caractères en morceaux, génère **chacun séparément** (sa propre attaque, sa
  propre fin) puis les recolle sans silence : une phrase longue s'entend comme
  2 à 4 prises collées. Mesure sur le chapitre IV de *Notre-Dame de Paris* :
  **19 unités sur 196 (10 %)**, jusqu'à **3 morceaux**.
  (2) **le nettoyage des signes de dialogue n'a JAMAIS été reporté sur NeuTTS** :
  le service XTTS retire les guillemets et traite le tiret cadratin avant l'envoi
  (`servir_xtts.py`, `nettoyer_pour_xtts` — mesure du 15/09 : sinon le moteur les
  **prononce**), le service NeuTTS ne nettoie rien. Mesure sur le même chapitre :
  **33 unités sur 196 (17 %)** portent des guillemets ou un tiret.
  *Outils livrés le jour même* : `test_voix/_diagnostic_neutts_phrase.py` (où le
  texte sera découpé : morceaux par phrase, limite de chaque voix, signes reçus
  bruts, phrases courtes — **hors ligne, lecture seule**) et
  `test_voix/_banc_ecoute_neutts.py` + `LANCER_BANC_ECOUTE_NEUTTS.bat` (lot
  d'écoute : vraies phrases du livre, puis la même phrase avec/sans les signes,
  phrases courtes, phrase longue d'un bloc puis coupée en deux).
  *Premières mesures du banc* (`ecoute_neutts_20260917_1234`, voix Frollo,
  livre 34) : la variante **« garder le guillemet ouvrant, retirer le fermant »
  est la PIRE** — 6,30 s au lieu de 3,64 s pour la phrase, et **13,30 s** pour
  la réplique à tiret (contre 3,84 s en brut), avec des silences internes
  jusqu'à 0,96 s ; les **phrases courtes** gardent des silences internes de 0,3 à
  0,4 s (« Non. » = 1,34 s dont **0,4 s de silence**) ; la **phrase longue**
  sort en 17,4 s / **19 segments** d'un bloc contre 16,2 s / 12 segments coupée
  en deux requêtes. **À confirmer à l'oreille** : ce sont des mesures, pas un
  verdict.
  *Pistes du brief extérieur (Lia, 17/09/2026)* : normalisation conditionnelle
  par moteur, fusion des phrases courtes, bascule vers un moteur stable sous un
  seuil. Les trois sont réalisables — mais les deux premières **recouvrent en
  grande partie ce qui existe déjà** (`_clean_text`, `nettoyer_pour_xtts`), et la
  troisième demande une **voix de secours par personnage** (la table `voices`
  n'a qu'une voix). Deux affirmations du brief sont **démenties par le code** :
  « texte envoyé brut » (faux) et « non reproductible, car chaque génération est
  différente » (faux pour NeuTTS : graine fixe, empreinte SHA-256 identique sur
  processeur **et** carte graphique).
  **VERDICT D'ÉCOUTE DE LAURENT (lot `ecoute_neutts_20260917_1234`)** —
  notation 1 diction qui accroche, 2 débit irrégulier, 3 mot inventé,
  4 gargouillis, 5 prosodie qui repart :
  01 réplique à tiret (voix Frollo) : **4** · 02 la même (autre voix) : **propre** ·
  03 guillemets (Frollo) : **2**, « le [éééé] en début de phrase » ·
  04 la même (autre voix) : **propre** · 05 narration (Frollo) : **propre** ·
  06 narration (autre voix) : **2** · 07 guillemets **bruts** : **propre** ·
  08 guillemets nettoyés comme XTTS : **propre** · 09 guillemet ouvrant seul :
  **1, 2, 4** · 10 tiret **brut** : **propre** · 11 tiret nettoyé comme XTTS :
  **2** · 12 tiret remplacé par une virgule : **1, 2, 3, 4** ·
  13 « Non. » : **3** · 14 « — Oui. » : **4** · 15 « Manger ? » : **propre** ·
  16 « Il partit. » : **3**, « dit deux fois le même mot » ·
  17 phrase longue d'un bloc : **propre** · 18 la même coupée en deux : **5**.
  *Ce que ce verdict ÉLIMINE* :
  - **les signes de dialogue** : 07 et 10 (**bruts**) sont propres → « reporter
    le nettoyage XTTS sur NeuTTS » est une **fausse piste**, et ce nettoyage
    **dégrade** (11 = 2 alors que 10 était propre) ;
  - **le découpage du service** : 17 (19 segments) est propre ;
  - **la règle « garder le guillemet ouvrant »** : 09 et 12 sont les pires
    (12 cumule les quatre défauts) — mesures et oreille d'accord, deux fois.
  *Ce qu'il DÉSIGNE* :
  - **les phrases courtes** : 01, 03, 13, 14, 16 dérapent (13 à 16 caractères) ;
    la seule qui passe est **« Manger ? »** — l'interrogation porte l'intonation ;
  - **la VOIX** : les mêmes phrases de 13 caractères sont **sales avec Frollo**
    (01 : 4 ; 03 : 2) et **propres avec la voix 4193** (02 et 04) → une part du
    défaut tient à l'**extrait de référence** et à sa transcription ;
  - **la coupe arbitraire** : couper au milieu (18) s'entend (5), la coupe du
    service aux virgules (17) ne s'entend pas.
  *Sur le « résidu » comme indicateur automatique* : il a vu juste sur 7 des
  10 fichiers fautifs, mais s'est déclenché 3 fois sur des fichiers **propres**
  (07, 08, 10 : ce sont des respirations) → bon pour **trier**, pas pour
  condamner. Le nombre de « segments » n'est pas un indicateur (05 : 8 segments,
  propre).
  *Proportions à retenir* : chapitre IV (196 unités) → **10 % de phrases
  courtes**, **17 % avec guillemets ou tiret** ; chapitres X et XXV → ~1 % de
  phrases courtes. Le défaut n'est donc pas réparti uniformément dans un livre.
  *Suite ouverte le même jour* : volet `--volet voix` du banc (les mêmes phrases
  courtes lues par 6 voix du livre) pour trier les voix **propres** des voix
  **sales**, avant tout chantier sur le contexte des phrases courtes.
  **VOLET « QUELLES VOIX DÉRAPENT ? » — lot `ecoute_neutts_20260917_1617`
  (4 phrases courtes × 6 voix du livre), verdict de Laurent** :
  V1 (1770, Frollo) : 4 / 4 / propre / 3 (« il partit » dit deux fois) ·
  V2 (4193) : propre / 1 (silence avant « oui ») / 4 (« mang[é]ér ») / propre ·
  V3 (4937) : 4 / propre / « manger » dit deux fois / propre ·
  V4 (12205, Esmeralda) : 4 / 4 / propre / 4 ·
  V5 (1591) : propre / 4 / propre / 4 ·
  V6 (5790) : 3 / 1 et 4 / propre / 1.
  *Conclusion : la piste « la voix » est DÉMENTIE à son tour.* **Aucune voix
  n'est propre** : chacune dérape sur 2 ou 3 des 4 phrases. Mon observation de
  la veille (« le défaut suit la voix » : 01 contre 02) reposait sur **deux**
  fichiers — l'échantillon était trop petit. Le volet voix a été fabriqué pour
  cela, il a tranché contre moi.
  *Ce qui reste est en revanche très net* : **« Manger ? » passe chez 4 voix sur
  6**, alors que **« — Oui. » dérape chez 5 voix sur 6** et **« Non. » chez 4**.
  Les défauts sont des **gargouillis**, des **répétitions de mot** (« il partit »
  deux fois, « manger » deux fois), un **chevauchement de syllabes**
  (« mang[é]ér ») et un **silence parasite avant le mot** — jamais une erreur de
  sens : c'est un moteur qui **démarre à froid sur un texte trop court**.
  *Trois mécanismes trouvés dans le service, jamais réglés* :
  1. **la TEMPÉRATURE de génération** — `neutts.infer()` a pour défaut
     **`temperature=1.0`** et `top_k=50`, et le service l'appelle **sans rien
     préciser**, donc à 1,0 : très élevé pour un TTS de clonage, et c'est le
     réglage qui pilote exactement ces symptômes. **Jamais essayé** sur NeuTTS
     (l'atelier n'avait testé la température que sur XTTS, sans effet) ;
  2. **le plancher du filet de rognage** — `duree_max_derivee()` vaut
     `max(3.0 s, …)` : une phrase de 4 caractères peut donc durer **3 secondes**
     sans être coupée, et tout le dérapage passe sous le filet (mesuré : « Non. »
     à **2,68 s** avec Esmeralda) ;
  3. **aucun rognage de TÊTE** — `rogner_queue()` ne traite que la fin de
     l'audio (le service XTTS, lui, rogne aussi le début) : le « silence avant
     oui » entendu deux fois reste dans le fichier.
  *Reste aussi, non testé* : `neutts.infer()` n'offre **aucune longueur max**
  (`max_length` = la fenêtre du modèle, pas le texte) → le seul bornage possible
  est le rognage après coup, et il faut donc le calibrer.
  **COMPARAISON NeuTTS / KYUTAI sur les mêmes voix — 17/09/2026** (proposition de
  Laurent : « Kyutai me semble le plus solide des trois neuronales » ; les deux
  moteurs partagent les mêmes extraits, donc les mêmes identifiants de voix, ce
  qui rend la comparaison honnête). Même chapitre, mêmes 4 phrases courtes,
  mêmes 6 voix, banc identique (`--moteur kyutai`, port 8082) :
  - « **Non.** » : NeuTTS de **1,06 à 2,68 s** (jusqu'à 3 segments, silence de
    0,68 s) contre Kyutai **0,56 à 0,88 s, toujours 1 segment** — moyenne
    **1,55 s contre 0,72 s** ;
  - « **— Oui.** » : NeuTTS **1 seul fichier sur 6 en un seul segment** (silences
    jusqu'à 1,14 s) contre Kyutai **6 sur 6, aucun silence** ;
  - « **Manger ?** » : NeuTTS de **0,65 à 2,26 s** (très variable) contre Kyutai
    **1,20 à 1,60 s** (régulier) ;
  - « **Il partit.** » : comparable (les deux découpent en 2-3 segments).
  *Vitesse* : le lot Kyutai des 24 fichiers s'est fabriqué en **une minute**
  (NeuTTS mettait ~4 minutes).
  *Outils* : banc étendu à `--moteur neutts|kyutai` (le livre 34 n'a plus de voix
  Kyutai depuis la bascule : le banc **transpose** les voix du casting — mêmes
  identifiants — et écarte celles absentes du moteur) ; nouveau lanceur
  `LANCER_BANC_ECOUTE_KYUTAI.bat`. Rappel : les deux moteurs **ne cohabitent
  pas** sur la carte graphique.
  *Reste à faire* : **l'écoute** du lot `ecoute_kyutai_20260917_1639` (mêmes
  numéros V1..V6 que le lot NeuTTS → comparaison directe fichier par fichier).
  **DÉCISION DU 17/09/2026 : KYUTAI L'EMPORTE.** Verdict de Laurent sur le lot
  `ecoute_kyutai_20260917_1639` : « **tout est propre** » — « parfois les mots
  traînent un peu, parfois ils sont dits rapidement, mais en l'état, tout est
  propre ». Les mêmes fichiers en NeuTTS donnaient des gargouillis, des
  répétitions de mots et des pauses parasites.
  *Ce que Laurent retient* : « ce moteur est plus lourd, mais de qualité bien
  supérieure » ; et **c'est un moteur en partie français** (Kyutai est un
  laboratoire français) — un argument qui compte pour lui, sans chauvinisme.
  Il ajoute : « je ne regrette pas d'avoir essayé d'autres pistes, c'est bien de
  ratisser large » (les pistes NeuTTS et les mesures ont servi à comprendre).
  *Suites ouvertes* :
  (1) **rebasculer les 223 personnages NeuTTS vers Kyutai** (même opération que
  la bascule du matin, **en sens inverse**) et faire allumer **Kyutai** par
  `START.bat` au lieu de NeuTTS ;
  (2) **améliorer la PROSODIE** (demande de Laurent : nettoyage du texte,
  ponctuation, « des astuces »). Levier propre à Kyutai trouvé dans le code :
  **`cfg`** — le « guidage par la voix », `NIMM_KYUTAI_CFG`, aujourd'hui **2.0**,
  valeurs valides **1.0 à 4.0 par pas de 0.5** (`valid_cfg_conditionings`,
  `moshi/models/tts.py`). **Jamais essayé** ;
  (3) **fabriquer des voix Kyutai** (voir ci-dessous).
  **CRÉER DES VOIX KYUTAI — oui, c'est possible (vérifié le 17/09/2026).**
  Une voix Kyutai n'est ni un modèle ni un audio : c'est un petit fichier
  `.safetensors` contenant les **jetons audio d'un extrait**, encodés par le
  codec **Mimi** du moteur. Vérifié sur les 35 empreintes françaises
  (`kyutai_service/_inspecter_empreinte.py`) : clé `speaker_wavs`, forme
  **(1, 512, 125)** — 125 jetons ≈ **5 secondes** d'audio ; le moteur accepte
  jusqu'à **5 empreintes par voix** (`make_condition_attributes`).
  *Convention de nommage* (lue dans `servir_kyutai.py`, `_repertorier_voix`) :
  `voix_fr/` → `<nom>_enhanced.wav.<suffixe>.safetensors` (identifiant = partie
  avant `_enhanced.wav`) ; `voix_autres/<famille>/` →
  `<nom>.wav.<suffixe>.safetensors` (identifiant préfixé par la famille). Le
  suffixe (`1e68beda@240`) dépend du modèle et n'est pas codé en dur.
  *Ce que cela ouvre* :
  - **importer chez Kyutai les voix qu'on n'a que chez NeuTTS** — les 19 extraits
    libres `dp_*` et les 30 voix Kokoro, dont les WAV sont dans
    `neutts_service/references/` → **49 voix de plus** chez le moteur retenu ;
  - **créer des voix personnelles** (la voix de Laurent) depuis un extrait de
    ~5 s ;
  - la piste de Laurent « **créer avec XTTS, puis importer dans Kyutai** » est
    valable — un WAV produit par XTTS s'encode comme un autre — mais elle
    n'apporte rien de plus que l'extrait source, **sauf** quand cet extrait est
    court ou bruité : XTTS peut alors en produire un long et propre.
  *À vérifier avant de promettre* : l'encodage d'un WAV par Mimi demandera un
  petit script dans l'environnement du moteur (`get_prefix()`, dans
  `moshi/models/tts.py`, montre la voie). **Rien n'a encore été fabriqué.**
  **FABRICATION D'EMPREINTES — ESSAI RÉUSSI le 17/09/2026.** Outil :
  `kyutai_service/_fabriquer_empreintes.py` (à lancer avec le python du moteur,
  **service éteint** : il charge le modèle pour lui, ~4 s).
  *Trois pièges rencontrés, tous résolus, à garder* :
  1. `mimi.encode()` rend les **codes discrets** (32 codebooks) — ce n'est PAS
     une empreinte ; il faut **`encode_to_latent(..., quantize=True)`** pour
     obtenir les **latents à 512 dimensions** (`moshi/models/compression.py`) ;
  2. Mimi attend un audio de forme **(lot, canaux, échantillons)** : sans la
     double dimension, il refuse ;
  3. les voix françaises vivent dans **`voix_fr/cml-tts/fr/`** (constante
     `DOSSIER_VOIX` de `servir_kyutai.py`), **pas** dans `voix_fr/` : un fichier
     déposé un cran trop haut reste **invisible** (le service n'annonce pas une
     voix de plus — c'est ainsi que le piège a été vu).
  *Preuve* : la voix libre `Femme001` (extraite de
  `neutts_service/references/voix_libres_dp/`) a donné une empreinte
  **(1, 512, 75)** — même structure que la banque — le service annonce **42 voix
  au lieu de 41**, et cette voix importée lit « Non. » en **0,56 s / 1 segment**
  (NeuTTS allait jusqu'à 2,68 s avec des pauses). Lot de contrôle :
  `test_voix/ecoute_kyutai_20260917_1659`.
  *Ce que ça débloque, DANS CET ORDRE* :
  (1) fabriquer les **29 empreintes manquantes** (19 voix libres `dp_*` + les
  voix `cml####` dont les WAV sont dans `neutts_service/references/`) → les
  **26 voix sans jumelle Kyutai** rentrent dans le rang et la bascule devient
  possible ; **basculer avant cela laisserait ces personnages en NeuTTS, donc
  deux moteurs à allumer — impossible, ils ne cohabitent pas sur la carte** ;
  (2) **basculer** les 222 personnages (`_basculer_voix_neutts_vers_kyutai.py`,
  rapport seul par défaut, copie de la base avant écriture) ;
  (3) faire allumer **Kyutai** par `START.bat` (aujourd'hui il allume NeuTTS) ;
  (4) **ensuite seulement**, l'idée de Laurent : fabriquer des empreintes pour
  les voix **Edge, Kokoro et Piper** — il faudra d'abord **leur faire lire** un
  extrait de ~5 s, puisque ces voix n'ont pas de WAV de référence → « tous les
  timbres avec un seul moteur ».
  **DÉMENTI LE MÊME SOIR : les 44 empreintes étaient INAUDIBLES.** Verdict de
  Laurent à l'écoute : « les voix sont des gargouillis, inaudibles ». Erreur de
  méthode de ma part : fabrication **en série** sur la foi d'une **forme de
  tenseur** correcte (1, 512, 125), **sans faire écouter un seul essai avant**.
  Tout a été **supprimé** le soir même (fichiers datés du 17/09 ; les **35
  empreintes de la banque, datées du 12/09, n'ont pas été touchées**) et le
  moteur est revenu à **41 voix**.
  *La cause est mesurée* : l'**échelle** du latent. Empreintes de la banque :
  écart-type **0,66** (valeurs de -3,9 à 3,4). Les miennes : **0,069** sans
  réglage, **3,03** avec le codec du modèle TTS. Facteur 9,5 dans un sens,
  4,6 dans l'autre — le moteur ne sait plus quoi faire de la voix.
  *Deux réglages essayés sans succès* : un gain RMS cible (-19 dBFS) **sature**
  ces extraits (très faibles au départ) ; viser l'écart-type de la banque par
  itérations ne suffit pas (le codec normalise en interne).
  *Ce qui manque, identifié précisément* : le **codec Mimi dédié aux voix**. Le
  script OFFICIEL de Kyutai (`moshi/scripts/tts_make_voice.py`, récupéré comme
  référence dans `kyutai_service/_reference_tts_make_voice.py`) fait
  `loaders._quantizer_kwargs["n_q"] = 16` puis charge un Mimi séparé
  (`<poids>_mimi_voice.safetensors`, **16 codebooks**) — alors que le codec du
  modèle TTS en a **32**. C'est ce codec qui produit des latents à l'échelle
  0,66.
  *Où le trouver : introuvable pour l'instant.* Le dépôt `kyutai/tts-1.6b-en_fr`
  ne contient que **6 fichiers** (aucun `*_mimi_voice*`) ; `kyutai/mimi` a
  `model.safetensors` et `tts_b6369a24.safetensors` (autre signature) ;
  `kyutai/tts-voices` n'en a pas non plus.
  *Outils laissés sur place* : `_lister_depot_modele.py` (liste les fichiers
  d'un dépôt Hugging Face), `_inspecter_empreinte.py` (forme **et statistiques**
  — c'est lui qui révèle une empreinte fausse), `_fabriquer_empreintes.py`
  (étalonnage + commentaires de tous ces pièges).
  *Leçon de méthode, à garder* : **une empreinte ne se valide pas par sa forme,
  mais à l'oreille** — et **jamais en série avant l'essai**. Une empreinte fausse
  ne casse rien (le moteur rend des gargouillis), mais elle abîme la confiance.
  *Pistes pour reprendre* : demander à l'atelier **NIMM Voix** comment il a
  fabriqué ses propres empreintes (il a peut-être déjà ce codec, ou le cache du
  poids), ou chercher `*_mimi_voice.safetensors` dans les **révisions** du dépôt
  Hugging Face.
  ⚠️ **Conséquence sur la suite** : tant que ce codec n'est pas trouvé, les voix
  sans empreinte Kyutai (26 voix de casting) **ne peuvent pas être importées**,
  donc la bascule des 222 personnages reste **bloquée** — et `START.bat` doit
  continuer à allumer **NeuTTS** en attendant.
  **LA CAUSE EST TRANCHÉE, PREUVE À L'APPUI (17/09/2026, avec l'atelier NIMM
  Voix)** : ce n'est **ni le niveau, ni la normalisation** — c'est le **codec**.
  Outil : `kyutai_service/_calibrer_encodage.py` (nouveau). Il encode **le WAV
  exact de la banque** (`10087_11650_000028-0002_enhanced.wav`, pris dans
  l'atelier voisin) avec le codec Mimi du modèle, à **8 niveaux (×1 à ×40)**, et
  compare chaque latent à l'empreinte officielle :
  - **corrélation 0,010 puis 0,008** — aucune corrélation, à aucun niveau ;
  - l'écart-type du latent **ne bouge pas** (0,0703 → 0,0723) : le codec
    **normalise en interne**, le volume d'entrée n'a donc aucun effet ;
  - dès ×2 le signal **sature** (le WAV de la banque est déjà fort) : voilà
    l'origine de mon écart-type 3,03 — un signal écrasé, pas un réglage.
  *Conclusion* : les empreintes officielles viennent d'un **codec différent**
  (le `*_mimi_voice.safetensors` à 16 codebooks), **publié nulle part** —
  vérifié par l'atelier NIMM Voix sur les trois dépôts possibles
  (`kyutai/tts-1.6b-en_fr`, `kyutai/mimi`, `kyutai/tts-voices` : 404). Le nom
  `1e68beda_240_mimi_voice.safetensors` est une **convention de nommage du
  script officiel de Kyutai**, pas un fichier réel.
  *Conséquence définitive* : **fabriquer une voix Kyutai à partir d'un WAV est
  impossible avec ce qu'on a**. L'idée de Laurent (« prendre des extraits de
  Edge, Kokoro, Piper pour tout ramener dans un seul moteur ») reste **bloquée**
  jusqu'à ce codec.
  *Piège à connaître, rencontré ce soir* : nos outils plantaient avec
  `TritonMissing` au chargement du codec — sous Windows `torch.compile` est
  impossible, il faut `NO_TORCH_COMPILE=1` **avant** l'import (le service le
  fait déjà ; `_fabriquer_empreintes.py` et `_calibrer_encodage.py` corrigés).
  *Ce qui reste ouvert* : rebasculer les **196 personnages** (sur 222) dont la
  voix existe chez Kyutai, en donnant aux **26** restants une voix Kyutai proche
  (choix à faire à l'oreille) — ou **rester en NeuTTS**. Décision de Laurent.
  **BASCULE COMPLÈTE FAITE le 17/09/2026 au soir** (choix de Laurent : « re-cast
  automatique ») : **222 personnages en Kyutai, 0 en NeuTTS**.
  - **180 personnages** transposés à l'identique (`neutts:X` → `kyutai:X`) par
    `_basculer_voix_neutts_vers_kyutai.py --ecrire` — même extrait, même timbre ;
  - **42 personnages** dont la voix n'avait pas de jumelle (19 extraits libres +
    voix `cml####`) ont reçu une voix Kyutai choisie **par profil d'écoute**
    (`_remplacer_voix_sans_jumelle.py --ecrire`) : les 35 voix Kyutai ne sont
    **pas** annotées, mais leurs **jumelles NeuTTS le sont** (mêmes extraits) →
    le choix se fait sur **timbre, âge, débit, registre**, jamais au hasard.
    **4** de ces 42 partagent une voix (livres à 40 personnages : les **17 voix
    masculines Kyutai** sont épuisées) — c'est le comportement habituel du
    lecteur quand le pool est vide (« voix partagée »).
  - Copies de sûreté : `nimm_epub.db.bak_avant_remplacement_voix_20260917_1752`
    et `nimm_epub.db.bak_avant_bascule_kyutai_20260917_1752`.
  - **`START.bat` allume désormais Kyutai** (port 8082) et non plus NeuTTS ;
    `data/moteur_voix.txt` (réglage propre à la machine, lu par le lanceur) est
    passé à `kyutai`. NeuTTS et XTTS restent lançables à la main.
  - *État final mesuré* : **kyutai 222 · edge 471 · kokoro 371 · piper 93 ·
    81 sans voix** = 1238 personnages ; **santé des voix : OK** (toutes les voix
    attribuées existent au catalogue) ; **65 verrous** préservés.
  - *Piège documenté au passage* : la **base** écrit le genre **H**, les
    **catalogues de voix** écrivent **M** — toute comparaison de genre doit
    passer par la famille (`== "F"`), comme le fait déjà `voice_casting.py`.
  **INCIDENT DU 17/09/2026 À 18h00, PUIS CORRECTIF** : après la bascule, Laurent
  a lancé un **re-cast** sur le livre 28 (*22/11/63*). Le lecteur a alors affiché
  « erreur » sur beaucoup de personnages : **31 voix XTTS et 47 voix NeuTTS**
  leur avaient été attribuées, plus **84 personnages sans voix** — or seul Kyutai
  était allumé, et **une voix dont le moteur est éteint ne lit rien**.
  *Cause, écrite dans le code* : `voice_casting.py`, fonction `_kyutai_pool` —
  « **cette fonction n'est PLUS utilisée** pour composer DEDICATED_VOICES_F/M —
  **Kyutai a été retiré du pool automatique** au profit de XTTS v2 (décision du
  14/09/2026) ». Ce choix datait d'avant Kyutai comme moteur principal : tout
  re-cast distribuait donc des voix Edge/XTTS/Kokoro/NeuTTS, **jamais Kyutai**.
  *Réparation (choix de Laurent : « répare tout »)* :
  (1) **base** — restauration de `bak_avant_bascule_kyutai_20260917_1752` (état
  d'avant la bascule), puis re-bascule → **222 personnages en Kyutai, 0 en
  NeuTTS ou XTTS** ; l'état fautif est gardé sous
  `nimm_epub.db.bak_avant_reparation_20260917_1847` ;
  (2) **code** — `_pool_par_paliers` compose désormais le pool ainsi :
  **Kyutai d'abord** (le moteur que `START.bat` allume), puis **Edge**, puis
  **Kokoro** ; **XTTS et NeuTTS en sont RETIRÉS** (leur moteur n'est plus allumé
  automatiquement, donc leurs voix ne liraient pas) mais restent choisissables
  **à la main**.
  *Conséquence assumée* : sur les très gros livres (pool de 68 voix max) des
  voix sont **partagées** — c'est préférable à des voix muettes.
  *Tests mis à jour* : `test_pool_casting.py` vérifie maintenant que Kyutai est
  **en tête** du pool et qu'XTTS/NeuTTS en sont **absents** (l'ancien test
  l'interdisait explicitement). Toute la batterie est au vert.
  *Outil de contrôle ajouté* : `test_voix/_controler_voix_kyutai.py` (lecture
  seule) — compare la **base**, le **catalogue du lecteur** et les **empreintes
  du moteur**, liste les voix qui demandent un **autre** moteur et les
  personnages **sans voix**. C'est lui qui a localisé le problème en une commande.
  **SUITE À 19h — UN SECOND CHEMIN ÉTAIT RESTÉ EN ARRIÈRE.** Malgré le correctif
  du pool par paliers, un nouveau re-cast du livre 28 a remis **31 voix XTTS et
  48 NeuTTS**, toutes muettes : le lecteur répondait **503 Service Unavailable**
  (message visible seulement dans la console du serveur) et Laurent n'entendait
  rien, sans rien voir s'afficher dans NIMM ePub.
  *Cause* : `_index_voix()` — l'index utilisé par le **re-cast par critères** et
  par le **re-cast avec l'IA** — contenait encore `XTTS_VOICES` et
  `NEUTTS_VOICES`. Le correctif précédent n'avait touché que
  `_pool_par_paliers`.
  *Correctif* : `_index_voix()` ne contient plus que **Kyutai, Edge et Kokoro**.
  Et pour que les voix Kyutai (qui ne sont pas annotées) restent choisies sur des
  critères **entendus**, `_classement_voix` lit désormais l'annotation de leur
  **jumelle NeuTTS** (`_jumelle_neutts` — mêmes extraits, donc même profil).
  *Effet de bord mesuré* : les voix de vieux sont rares dans le pool restreint
  (et beaucoup sont **réservées par rôle**) ; pour « homme âgé », il ne reste
  parfois **qu'une** voix, dont le timbre n'est pas « grave ». Le test
  `test_attribution_criteres.py` a été ajusté (il exigeait un timbre grave,
  calibré sur l'ancien catalogue) — l'âge reste exigé.
  *Base réparée* : **263 personnages en Kyutai**, aucun sur un autre moteur,
  aucun muet. Copies : `bak_avant_remplacement_voix_20260917_1858` et
  `bak_avant_bascule_kyutai_20260917_1858`.
  *À améliorer (noté)* : le **503 ne s'affiche pas côté client** — le lecteur ne
  sait pas qu'une voix demande un moteur éteint, et l'utilisateur n'entend
  simplement rien. Un message clair serait préférable (« cette voix demande un
  autre moteur »).
  *Leçon* : **corriger un endroit ne suffit pas** — le même catalogue de voix est
  lu par DEUX chemins (pool par paliers, index par critères). Les deux ont été
  traités, et `_controler_voix_kyutai.py` vérifie l'état final.
  **RÉGLAGES DE PAUSE — 17/09/2026 au soir (écoute de Kyutai par Laurent).**
  Trois remarques de Laurent, mesurées avant d'y toucher :
  « le point passe très très vite » ; « je crois qu'on a réduit la pause, même
  pour Edge et Kokoro ? » ; « il faudrait augmenter la pause de peut-être
  100 millisecondes ».
  *Mesures* (`test_voix/_mesurer_pause_phrases.py`, nouveau — silence de tête /
  parole / silence de queue, via le lecteur) : **Kyutai 300 à 430 ms** de queue,
  **Edge 231 à 238 ms**, **Kokoro 96 à 109 ms**, **Piper 106 à 111 ms**.
  *Ce que Laurent avait senti, et c'était juste* : `frontend/app.js`,
  `PARAGRAPH_PAUSE_MS` — la pause **entre paragraphes** (et chaque réplique de
  dialogue est un paragraphe) valait **300 ms**, elle a été mise à **0** le
  15/09/2026 parce qu'elle s'additionnait au rognage de l'époque. Elle touche
  **tous** les moteurs : d'où sa remarque sur Edge et Kokoro.
  *Réglages appliqués (+100 ms demandés par Laurent)* :
  1. `PARAGRAPH_PAUSE_MS` : 0 → **100 ms** (un tiers de l'ancienne valeur, pour
     ne pas recoller les répliques) ;
  2. `modules/audio_trim.py` (Edge) : marge de fin 0,25 s → **0,35 s** ;
  3. `kyutai_service/servir_kyutai.py` : nouvelle constante
     `SILENCE_QUEUE_S` = **0,10 s** ajoutée en fin de chaque phrase (réglable par
     `NIMM_KYUTAI_SILENCE_QUEUE`). Mesure après réglage sur une phrase inédite :
     Kyutai **630 ms** de queue.
  *À savoir* : deux réglages ne prennent effet qu'au **redémarrage** — le
  rognage Edge au redémarrage du **lecteur** (`audio_trim` est chargé en
  mémoire), et la pause de paragraphe au **rafraîchissement de la page**.
  *Reste ouvert* : la **hauteur qui varie d'une phrase à l'autre** (constat de
  Laurent : « parfois il part sur la phrase suivante avec une intonation assez
  différente »). Cause : chaque phrase est générée **indépendamment**, le moteur
  tire sa prosodie à chaque fois. Levier à tester : **`cfg`** (`NIMM_KYUTAI_CFG`,
  aujourd'hui 2,0 ; valeurs valides 1,0 à 4,0 par pas de 0,5) — banc à l'aveugle
  à faire, comme pour le reste.
  **QUATRE DEMANDES DE LAURENT — 17/09/2026 (écoute de Kyutai).**
  (1) **Voix du narrateur sauvegardée, PAR LIVRE** — livré. Elle n'était gardée
  nulle part (aucun `localStorage`, aucune colonne) : le menu repartait donc de
  la voix par défaut à chaque rechargement. Choix de Laurent : « **par
  utilisateur**, et idéalement **par livre** — je n'ai pas la même pour
  Monte-Cristo et pour 22/11/63 ». Fait ainsi : colonne
  **`books.narrator_voice`** (migration non destructive dans `init_db`, même
  méthode que `saga`), route **`PUT /api/books/{id}/narrator`**, restauration à
  l'ouverture du livre (`_restaurerVoixNarrateur`) et enregistrement au
  changement du menu. La voix voyage donc **avec le livre**, d'un appareil à
  l'autre. Vérifié en direct : deux livres gardent bien deux voix différentes.
  (2) **`;` remplacé par `,`** dans `_clean_text` — les moteurs neuronaux
  essaient de **prononcer** la ponctuation forte et le point-virgule sortait
  parfois en « euh ».
  (3) **`(` et `)` remplacés par des virgules** — le moteur les ignorait, donc
  l'incise n'était entourée d'**aucune pause**, d'où la demande de Laurent
  (« il faudrait l'équivalent d'une virgule »).
  (4) **Cache ramené de 20 Go à 2 Go** — Laurent : « le cache ne me sert pas, je
  ne réécoute que très rarement un passage déjà entendu ». La purge automatique
  fait le reste ; le bouton « vider le cache » reste à faire.
  *Et une confirmation utile* : le **casting Monte-Cristo** a été fait avec
  **DeepSeek** comme moteur principal, et Laurent le juge insuffisant pour le
  découpage des dialogues. Or `main.py` dit déjà
  `MOTEURS_DE_SECOURS = ["deepseek", "local"]` : DeepSeek **n'est** qu'un
  moteur de **rattrapage**, Gemini reste le principal. Il suffit donc de
  **relancer le casting avec Gemini** — rien à changer dans le code.
  **CONTEXTE GLISSANT — INTÉGRÉ le 17/09/2026 au soir** (idée de Laurent,
  validée par son écoute : « plus de sautes de volume, les voix paraissent plus
  chantantes »). C'est la réponse au défaut le plus tenace du projet : le moteur
  démarrait **à froid** sur chaque phrase.
  *Principe* : pour la phrase B, on envoie « les 6-8 derniers mots de A, puis B »,
  le moteur lit tout, et **on coupe l'audio pour ne garder que B** — l'auditeur
  n'entend jamais le contexte.
  *Où, dans le code* :
  - `frontend/app.js` — `_buildPlaylist` donne à chaque unité le contexte de la
    précédente (`CONTEXTE_MOTS = 8`), `_fetchAudio` l'envoie (`context`) ;
  - `main.py` — champ `context` dans `TTSRequest`, transmis à Kyutai seulement ;
  - `modules/tts.py` — `synthesize_kyutai(..., contexte)`, et **le contexte
    entre dans la clé de cache** (même phrase après un autre contexte = autre
    audio) ;
  - `kyutai_service/servir_kyutai.py` — `generer_wav(..., contexte)` génère le
    contexte SEUL pour connaître la fin de son dernier son, puis
    « contexte + phrase », et coupe **dans le premier silence franc**
    (`SILENCE_COUPE_S = 0,12 s`, `MARGE_CONTEXTE_S = 0,25 s`).
  *Garde-fou mesuré* : un contexte trop long **sature la fenêtre** du modèle et
  **tronque la phrase** — avec la phrase précédente ENTIÈRE, une phrase de 9,6 s
  est sortie en **1,4 s**. D'où `CONTEXTE_CARACTERES_MAX = 90` côté service et
  8 mots côté page.
  *Effet mesuré, mêmes phrases* : **moins de micro-coupures** (11 segments au
  lieu de 13 ; 20 au lieu de 23) et des durées comparables.
  *Piège rencontré* : `simple_generate` rend un **tenseur PyTorch** (parfois sur
  la carte graphique) — un `np.asarray` direct provoquait une **erreur 500**. Il
  faut passer par `.detach().cpu()` (`_en_numpy` dans le service).
  *Vérifié de bout en bout* : service seul (115 Ko avec contexte) **et** via le
  lecteur (148 Ko).
  *Mémo transmis à NIMM Voix* : `test_voix/MEMO_pour_NIMM_Voix.md` — le nettoyage
  du texte, le contexte glissant, les pauses, le piège des phrases courtes et la
  méthode, à rejouer sur **Pocket TTS**.
  **RÈGLE DU MÊME LOCUTEUR — ajoutée le 17/09/2026 au soir** (idée de Laurent, en
  entendant deux effets secondaires : un « tic » avant chaque phrase, et une
  pause de plusieurs secondes à chaque changement de personnage).
  *Le tic* : on coupait **pile** à la fin du dernier son du contexte, ce qui
  laissait passer quelques échantillons du dernier mot (discontinuité audible).
  On coupe désormais **40 ms dans le silence** (`_ou_commence_la_phrase`).
  *La pause* : cause mesurée — **chaque appel au moteur paie un coût fixe
  d'environ 3 s** de préparation. Le contexte faisant **deux appels par phrase**,
  ce coût était payé deux fois : phrase de 150 caractères, **6,38 s seule contre
  10,13 s avec contexte** (et **4,12 s** pour le contexte seul, 8 mots !). La
  génération devenait **plus lente que la lecture** → attente, surtout au
  changement de personnage (tout part d'un coup, et le service ne génère qu'une
  phrase à la fois).
  *La règle de Laurent* : **le contexte ne s'applique qu'entre deux phrases du
  MÊME locuteur** (même voix). Au changement de personnage, pas de contexte —
  c'est **plus juste prosodiquement** (un locuteur ne prête pas son élan à un
  autre) **et** ça supprime la double génération là où elle coûtait le plus. Le
  narrateur suit la même règle : s'il porte la voix d'un personnage (cas de
  *22/11/63*, où le narrateur **est** Jake Epping), la continuité est conservée.
  *Implémentation* : `frontend/app.js`, `_buildPlaylist` —
  `if (units[i].voice !== units[i - 1].voice) continue;` **et**
  `if (units[i].paraIdx !== units[i - 1].paraIdx) continue;`.
  *Complément du même soir (idée de Laurent, en entendant le résidu de coupe)* :
  **aucun contexte après un saut de ligne**. Un nouveau paragraphe ouvre un
  **nouveau propos** : le modèle n'a pas besoin de l'élan du précédent, c'est le
  cas où le résidu s'entendait, et le double travail du moteur s'y paie sans
  bénéfice. Le contexte ne sert donc plus qu'à une **suite de phrases du même
  locuteur dans le même paragraphe** — les longues tirades et les narrations
  continues, là où l'enchaînement s'entend vraiment.
  *Piste notée pour la suite* : générer **deux phrases en un seul appel**
  (`contexte + A + B`), puis couper en deux — le coût fixe serait amorti et B
  aurait son contexte naturellement. Chantier (le lecteur reçoit une phrase par
  requête aujourd'hui), à ouvrir plus tard.
  **DEUX AJOUTS DU MÊME SOIR (constats de Laurent, 17/09/2026).**
  (1) **Le cache pouvait rejouer un ANCIEN rendu** : Laurent entendait
  « l'ancien défaut sur quelques lignes, puis les mises à jour ». Cause : la clé
  de cache ne dépend que du texte, donc les phrases dont le texte **n'avait pas
  changé** étaient servies depuis les fichiers d'**avant** les corrections.
  Correctif : **`VERSION_CACHE`** (`modules/tts_cache.py`, aujourd'hui **2**)
  entre dans la clé — tout fichier produit par une version antérieure n'est plus
  servi, donc une correction de prétraitement ne peut plus être contredite par
  le cache. **À incrémenter** dès que le texte envoyé au moteur change. Le stock
  existant a été **purgé** (2 766 fichiers, 406 Mo).
  (2) **` : ` → `, `** dans `_clean_text` : Laurent n'entendait **aucune pause**
  sur les deux-points. On ne touche qu'au deux-points **précédé d'une espace**
  (typographie française), ce qui préserve « 14:30 » et les adresses.
  **COUPE DU CONTEXTE — trois corrections successives, le même soir.** Laurent
  entendait **le dernier mot du paragraphe précédent** devant la phrase du
  paragraphe suivant (« montagne. Va faire un petit tour, avait dit Al. »).
  *Cause 1* : la coupe tombait sur une **virgule du contexte** (le contexte en
  contient), donc trop tôt. *Cause 2, plus fine* : la durée du contexte mesurée
  **seul** sous-estime sa place dans la version longue — suivi d'une phrase, le
  modèle le lit un peu plus lentement. *Cause 3* : **sans séparateur**, le modèle
  enchaîne contexte et phrase **sans pause détectable** (0,31 s de silence au
  mieux, mesuré) : aucun repère pour couper.
  *Correctifs, mesurés à chaque fois* (`test_voix/_essai_separateur.py`,
  `_diag_coupe_contexte.py`, `_verifier_contexte_service.py`) :
  1. **points de suspension** entre le contexte et la phrase → le modèle marque
     une **vraie pause de ~1,2 s** (mesuré : 0,31 s sans eux, 1,18 s avec) ;
  2. on génère le **préfixe exact** (`contexte + " ... "`), et non le contexte
     nu : le texte est **identique jusqu'à la frontière**, donc sa durée mesurée
     est fiable (l'estimation par proportion, elle, ne l'était pas) ;
  3. on **ne coupe jamais avant la fin du contexte** (marge de 0,20 s), et on
     choisit le silence **le plus long** parmi ceux qui sont à la frontière ou
     après (c'est la pause des points de suspension).
  *Résultat mesuré* : la coupe tombe à **0,08 s de la frontière** (journal du
  service : « frontière a 7,28 s, coupe a 7,20 s »), contre **1,5 s de résidu**
  au départ.
  *Réserve honnête* : le moteur **varie d'une génération à l'autre**, donc la
  comparaison des durées n'est pas un juge parfait (un même cas mesuré « −0,32 s »
  puis « +1,09 s »). **C'est l'oreille de Laurent qui tranche** ; s'il reste un
  résidu, le réglage suivant est simple (couper un peu plus loin après la
  frontière).
  **DERNIER AJUSTEMENT DU SOIR — la tolérance de coupe était trop large.**
  Laurent entendait encore « **pas marché** » à la fin de la phrase ET au début
  de la suivante (extrait de *22/11/63*). Cause : le code **tolérait** de couper
  jusqu'à **0,20 s AVANT** la fin mesurée du contexte — or un mot comme
  « marché » dure 0,3 à 0,4 s, donc il restait. Correctifs :
  - tolérance ramenée à **50 ms** (juste de quoi absorber l'imprécision) ;
  - s'il n'y a aucun silence franc à la frontière, on prend le **premier silence
    qui suit** la fin du contexte (même court), et en dernier recours le passage
    le plus calme **juste après** — **jamais dans le contexte**.
  *Contrôle après réglage* (`_verifier_contexte_service.py`, **4 cas** dont les
  deux de Laurent) : **TOUT EST OK** — saut de ligne à **−0,02 s**, « pas
  marché » à **+0,60 s sur une phrase de 13,9 s** (une respiration, plus un
  mot).
  **INCISES DE DIALOGUE (« il m'a demandé ») — le prompt demandait le
  contraire.** Constat de Laurent, 17/09/2026 : dans *22/11/63*, la phrase
  « Vous êtes qui, putain ? il m'a demandé. » faisait lire **« il m'a
  demandé »** par Carton Jaune au lieu du narrateur.
  *Cause* : la consigne 8 du prompt de la passe 1 disait exactement l'inverse —
  « attribue TOUJOURS la phrase entière au personnage qui parle, **même si
  l'incise elle-même est techniquement de la prose narrative** » — et la
  consigne 9 (« tant que la citation n'est pas refermée, TOUTES les phrases
  gardent le même locuteur ») s'appliquait d'autant mieux que le guillemet
  fermant **manque** dans ce passage. L'IA appliquait donc les règles **à la
  lettre**.
  *Correctif* : la consigne 8 distingue maintenant deux cas — une phrase qui
  **contient** une réplique entre guillemets va au personnage ; une phrase qui
  n'est **qu'une incise de parole** (« il m'a demandé. », « dit-il. »,
  « répondit le comte. », « demanda-t-elle. ») est de la **NARRATION**, même si
  la citation précédente n'a pas été refermée. La consigne 9 porte l'exception.
  *Périmètre* : cela vaut pour les **prochains castings et re-casts** ; un livre
  déjà casté garde son attribution (elle vient de l'IA) — pour le corriger, il
  faut **relancer le casting**.
  *Manque signalé au passage* : il n'existe **aucun outil pour corriger le
  locuteur d'une phrase à la main** (le panneau « voix de cette phrase » change
  la voix d'un personnage ou celle du lecteur, **pas** l'attribution). À prévoir
  si le cas se reproduit souvent — c'est un outil d'atelier à part entière.
  **« SI JE RE-CASTE LES TOMES 5 ET 6, VAIS-JE RETROUVER LES VOIX ? » — OUI.**
  (question de Laurent, 17/09/2026, inquiet du changement de moteur survenu
  entre-temps). *Vérifié dans le code* : `_fetch_saga_voix_figees` (`main.py`,
  1284) reprend les voix des autres tomes de la même saga — **le tome le plus
  anciennement ajouté fait référence** en cas de divergence — et il ne regarde
  **que l'identifiant de la voix, jamais le moteur**. Le passage d'XTTS/NeuTTS à
  Kyutai ne casse donc rien, **tant que les identifiants suivent** : c'est
  exactement ce qu'a fait la bascule (mêmes identifiants, empreintes Kyutai).
  *Contrôlé* : la saga « Monte Cristo » (5 tomes) est **cohérente** —
  **134 personnages communs, une seule voix pour chacun** d'un tome à l'autre
  (nouvel outil `test_voix/_controler_saga.py`).
  *Les deux seules nuances à connaître* :
  1. la **voix du narrateur** n'est pas couverte par la saga : elle est **par
     livre** (mis en place le 17/09/2026) → à choisir une fois pour le T5 et une
     fois pour le T6, la même que les tomes précédents si on veut la continuité ;
  2. les personnages dont la voix n'existait pas chez Kyutai ont une voix de
     remplacement — dans Monte-Cristo, **Beauchamp seul** (`cml3060` →
     `kyutai:4482_3103_000063-0001`), mais **la même dans tous les tomes**.
  *Re-caster le T5/T6* reprend donc ces voix automatiquement (le re-cast gratuit
  comme le casting complet).
  **FABRICATION EN SÉRIE — FAITE le 17/09/2026 (soirée).** 44 empreintes
  fabriquées à partir de `neutts_service/references/` : **25 voix CML-TTS**
  (`cml####`, dont les WAV faisaient défaut chez Kyutai) et **18 voix libres**
  (`dp_*`, la 19ᵉ — `Femme001` — avait été fabriquée pour l'essai). Les **35
  empreintes de la banque officielle n'ont PAS été touchées** (`--manquantes`).
  Le moteur annonce désormais **85 voix** (41 + 44). Toutes sortent avec la
  forme **(1, 512, 75)** et l'extrait est **tronqué à 6 s** (une empreinte trop
  longue mange la place du texte dans la fenêtre du modèle).
  ⚠️ **Reste à faire avant de basculer** : ces 44 voix existent **chez le
  moteur** mais **pas dans le catalogue du lecteur** (`KYUTAI_VOICES`, dans
  `modules/tts.py`) — or le script de bascule refuse toute voix absente du
  catalogue. Il faut donc **compléter `KYUTAI_VOICES`** en **préservant les
  prénoms déjà choisis à la main pour les 35 voix existantes** (Éléonore,
  Bertrand, Gaston… ne doivent pas être écrasés) et en **héritant** des prénoms,
  genres et étoiles du catalogue NeuTTS (les identifiants sont les mêmes) pour
  les 44 nouvelles. Ensuite seulement : bascule des 222 personnages, puis
  `START.bat` sur Kyutai.
  *Reste à relever au moment du chantier* : la **liste exacte des voix
  françaises** disponibles chez Google (doc « list-voices-and-types »), le
  nombre de voix **Gemini TTS** et leur caractère (homme/femme/âge) — au doigt
  mouillé, non.
  *Si ça ne suffit pas* — pistes déjà recensées (voir « État de l'art TTS
  français », priorité 2) : **Kyutai TTS 1.6B** (déjà installé, 35 voix
  françaises **natives**, pas d'accent forcé → à tester pour la stabilité) ;
  **NeuTTS-Nano-French** (clonage 3-15 s, 194 Mo, **tourne sur processeur**) ;
  Piper / MMS-TTS / MeloTTS (déterministes, comme Kokoro, mais peu de voix).
  ⚠️ **Le vrai choix à poser** : **aucun autre moteur ne sait cloner les voix de
  Laurent** — Kokoro/Piper/MMS ont des voix figées, et Kyutai exige des
  empreintes qu'on ne sait pas fabriquer. Abandonner XTTS, c'est abandonner le
  clonage maison (sauf NeuTTS-Nano, ou un Piper entraîné sur sa voix).


- [ ] **Re-cast : ne pas distribuer les voix à ACCENT au hasard** (constat de
  Laurent, 16/09/2026). Question posée : « les Cavalcanti vont-ils recevoir une
  voix italienne ? » Réponse : **non** — l'attribution des voix n'utilise jamais
  l'IA (ni au casting, ni au re-cast) : elle ne connaît que le **genre**, l'**âge**
  et les **étoiles/annotations**. La fiche des personnages (`cast_fiche`) ne
  contient **aucune** information de nationalité ou d'accent.
  *Ce qui se passe aujourd'hui* : les voix **étrangères** (Kokoro `im_`, `em_`,
  `fm_`, `pm_`, `hm_`, `jm_`, et les voix Edge `fr-CA-*`) parlent français
  **avec un accent**. Deux origines bien distinctes, à ne pas confondre :
  (1) **le choix de Laurent** — c'est **lui** qui a assigné à la main les voix
  italiennes et espagnoles aux personnages concernés (Cavalcanti, Bertuccio,
  Haydée, Ali-Tebelin, Vampa, Peppino, l'abbé Faria…) : rien d'automatique, et
  c'est du travail qu'il ne veut pas perdre ;
  (2) les **attributions automatiques** — quand le pool neutre s'épuise (livres
  à 60-175 personnages), les voix accentuées restantes sont distribuées sans que
  personne ne l'ait demandé.
  Mesure du 16/09/2026 sur la saga Monte-Cristo
  (`test_voix/_personnages_a_accent.py`) : **307 personnages** portent une voix
  accentuée, dont seulement **38 verrouillés**.
  ⚠️ **Piège à connaître** : assigner une voix **à la main ne la protège pas** —
  seul le **verrou** (case « garder ») survit à un re-cast.
  *Risque* : un re-cast redistribue toutes les voix **non verrouillées** → ces
  accents (justes ou non) seraient perdus, et l'accent pourrait tomber sur des
  personnages français. À l'inverse, les voix dont le **rôle** est annoté
  `étranger` (18 voix, dont `im_nicola`, `em_santa`) sont **exclues du pool
  automatique** : elles ne partiront pas au hasard.
  *Pistes, dans l'ordre de simplicité* : (1) **verrouiller** à la main les
  personnages étrangers qui comptent (l'outil `_personnages_a_accent.py` les
  liste livre par livre) ; (2) dans `_classement_voix`, **reléguer les voix
  accentuées en fin de classement** pour les personnages dont on ne sait rien,
  afin qu'un accent ne tombe pas sur un Français par épuisement du pool ;
  (3) **étape 2 (« Re-caster avec l'IA »)** : le LLM lit le texte et peut
  déduire qu'un personnage parle étranger — il faudrait alors ajouter un champ
  d'accent à la fiche des personnages. À trancher avec Laurent.

- [ ] **Piste : donner un caractère « chantant » ou « plat » à un personnage**
  — idée de Laurent, 16/09/2026, née des tests sur le point final (« dans une
  narration, parfois le côté plat fait partie de la prosodie adaptée » ; « on
  pourrait forcer un peu le côté chantant d'un personnage… à voir »).
  *Ce qui existe déjà, gratuitement* : le **re-cast par critères** choisit la
  voix d'après les annotations d'écoute — un personnage qu'on veut vivant peut
  déjà recevoir une voix notée `debit = vif` avec le timbre adapté.
  *Ce qui manquerait pour aller plus loin* : l'expressivité **d'un tirage** ne se
  règle pas aujourd'hui. Il faudrait exposer les paramètres de génération du
  moteur XTTS (`temperature`, `length_penalty`), les faire passer du lecteur au
  service, les stocker par personnage (table `voices`) et les rendre réglables
  dans la fenêtre du casting. **Chantier complet** : à ouvrir seulement si le
  besoin se confirme à l'usage.
  *À savoir* : les deux tests à l'aveugle du 16/09/2026 montrent que la prosodie
  d'un tirage **varie beaucoup** d'un essai à l'autre (moteur stochastique) — un
  réglage par personnage agirait donc sur une **tendance**, jamais sur chaque
  phrase. Et le côté plat n'est pas un défaut : c'est parfois la bonne couleur.

- [ ] **Voix XTTS créées à partir d'extraits LIBRES DE DROITS (chantier de
  Laurent, ouvert le 15/09/2026)** — *en cours, décision de Laurent : ajout au
  catalogue **groupé à la fin***.
  Laurent récupère des extraits de voix du **domaine public**, les nettoie dans
  **Audacity**, et les dépose en **MP3** dans `Extraits de voix\` (dossier
  ignoré par Git, comme tout l'audio — voir `.gitignore`).
  *Méthode retenue* (reprise de l'atelier NIMM Voix,
  `G:\NIMM Voix\outils\xtts_tts\_preparer_reference.py`) : conversion en **WAV
  mono 24 000 Hz 16 bits** (format natif du moteur) + **rognage des silences de
  bord** (ffmpeg -45 dB, marge 0,10 s), puis versement dans
  `xtts_service\voix_fr\` sous `<identifiant>_enhanced.wav`.
  *Repères de durée* (valeurs de l'atelier, confirmées par la config du modèle
  installé : `max_ref_len = 30 s`) : **idéal 10-20 s** ; **6 s = minimum** ;
  au-delà de 30 s le moteur ne garde rien de plus.
  *Outils créés pour ce chantier* :
  - `xtts_service/_preparer_extraits.py` — conversion + mesures (durée, silence
    de tête, silence de queue) + verdict, **refus d'écraser** une voix en
    place, mode `--verser` qui écrit dans la banque **et recharge le moteur à
    chaud** (`POST /recharger`, aucun redémarrage) ;
  - `xtts_service/_ecouter_extraits_dp.py` — fabrique le **lot d'écoute**
    comparatif : pour chaque voix, `..._reference.wav` (l'extrait entendu par
    le moteur) puis `..._clone.wav` (le même passage lu par le clone), plus
    `index_ecoute.txt` et `ECOUTER_LE_LOT.cmd` (lecture à la suite) ;
  - `xtts_service/sortie_ecoute_dp/` (sortie, ignorée par Git) ;
  - `xtts_service/VOIX_LIBRES.txt` — **tableau de suivi** : identifiant ↔ prénom
    ↔ genre ↔ durée ↔ fichier source, plus la réserve de prénoms et les étapes
    finales. C'est le document à relire pour l'ajout groupé.
  **État au 15/09/2026** : **19 voix préparées et versées dans le moteur (79
  voix au total**, 60 CML + 19 libres) **et AJOUTÉES AU CATALOGUE le même
  jour** — Laurent a choisi de les verser **sans attendre son verdict sur le
  lot 2** (option : « je te dirai après écoute dans le lecteur si l'une
  m'énerve ») ; le retrait d'une voix est possible à tout moment (une entrée à
  retirer de `XTTS_VOICES` + son WAV à retirer de la banque). **Lot 1 (7 voix)
  VALIDÉ À L'OREILLE** par Laurent (« elles sont top ») ; **lot 2 (12 voix)** en
  écoute. Identifiants et prénoms **attribués** (détail complet
  dans `xtts_service/VOIX_LIBRES.txt`) —
  **lot 1** : `dp_femme001` → **Marthe**, `dp_femme002` → **Solange**,
  `dp_femme003` → **Yvette**, `dp_femme004` → **Henriette**, `dp_homme001` →
  **Marius**, `dp_homme002` → **Théodore**, `dp_homme004` → **Édouard** ;
  **lot 2** : `dp_femme121235456` → **Rose**, `dp_femme32321312445` →
  **Georgette**, `dp_femme48897` → **Thérèse**, `dp_femme65465464` →
  **Colette**, `dp_femme6566554478` → **Juliette**, `dp_femme65699878` →
  **Madeleine**, `dp_homme1122544987` → **Victor**,
  `dp_homme1122545656487` → **Robert**, `dp_homme313213265` → **Paul**,
  `dp_homme45788656512` → **Albert**, `dp_homme65462104` → **Jules**,
  `dp_homme87976454321` → **Arthur**.
  *Nomenclature* : Laurent a nommé ses fichiers avec **des numéros « au
  hasard »** (`Femme121235456.mp3`…) — les identifiants de voix reprennent donc
  ces numéros (peu importe : seul le **prénom** est visible dans le lecteur).
  Les anciens extraits sont rangés dans `Extraits de voix\Découpage OK\`.
  *Réserve de prénoms vérifiée libre* (aucun doublon avec les 151 voix de toutes
  les familles) : femmes — Yvonne, Angèle, Clémence, Germaine, Sidonie,
  Bertille, Adeline, Lucile, Nadine, Virginie, Élise, Fernande, Martine,
  Simone, Odile, Pascale, Brigitte, Monique ; hommes — Raoul, René, Roger,
  André, Casimir, Théophile, Anatole, Barnabé, Firmin, Gédéon, Ismaël, Joachim,
  Léandre, Narcisse, Ovide, Pamphile.
  *Ajout au catalogue : **FAIT** le 15/09/2026.* Les 19 entrées ont été
  ajoutées à **`XTTS_VOICES`** (`modules/tts.py`, bloc commenté « Voix issues
  d'extraits LIBRES DE DROITS »), avec le format habituel
  `{"id": "xtts:dp_xxx", "name": …, "region": "🇫🇷 France (XTTS)",
  "gender": "F"/"M", "stars": 2}` — cette liste alimente **à la fois** les
  **menus** du lecteur **et** le **pool du casting automatique**. Vérifié :
  **79 voix XTTS** au catalogue, **10 femmes + 9 hommes** libres, **aucun
  doublon de prénom**, et **chacune des 19 est présente dans la banque du
  moteur**. *Vérification* : `modules/tts.py` compile ; `test_libelles_voix.py`,
  `test_ids_ecran.py`, `test_pool_casting.py`, `test_voix_ecoutables.py`/`.js`,
  `test_etat_casting.js`, `test_filtre_genre.js` → **tous OK**.
  *Reste à faire* : **relancer le lecteur** (la liste est lue au démarrage :
  avant relance, il annonce encore 60 voix XTTS) ; puis écouter dans la fenêtre
  « Écouter les voix » et **fixer les étoiles** définitives (2 partout pour
  l'instant) ; le tableau de suivi `VOIX_LIBRES.txt` reste la référence pour les
  prochains lots (34 prénoms encore libres).
  *Rappel licence* : XTTS v2 est en CPML (usage **non commercial**), donc
  l'audio produit ne se partage pas — voir `xtts_service/ATTRIBUTION.md`.





- [ ] **Décider du sort des 6 voix « de rôle » NIMM dans le pool auto**
  Mamie, Papi, Narrateur, Enfant, Mystère, Jeune sont notées 3 étoiles, donc
  en tête du pool automatique : un casting (ou un re-cast) peut les attribuer
  à des personnages au hasard, alors qu'elles visent des rôles précis. À
  trancher : les exclure de `DEDICATED_VOICES_F/M` (réservées à la main) ou
  les laisser participer.

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

- [ ] **Réécouter et ajuster les notes « stars » Kokoro** au fil de l'usage
  (elles sont indicatives) — utile car le pool automatique du casting pioche
  par note décroissante.

- [ ] **XTTS : retours d'écoute de Laurent (une heure du Comte de
  Monte-Cristo, 15/09/2026)** — deux constats, chiffrés à l'atelier le même
  jour, *en attente de décision*.
  **(1) « Changements de rythme » sur les successions de petites phrases**
  (échanges courts entre deux interlocuteurs) ; Laurent soupçonnait le
  préchargement du lecteur. **La mesure dément : ce n'est pas le débit du
  moteur.** Nouvel outil `xtts_service/_mesurer_debit_xtts.py` (mesure sur le
  moteur allumé, RTX 4060) : répliques courtes **0,47 s de calcul pour 1,4 s
  d'audio** (facteur 0,32) et phrase longue **4,78 s pour 15,7 s** (facteur
  0,30) → le moteur produit **environ 3 fois plus vite que la lecture**, et le
  coût est **proportionnel à la durée** (rapport longue/courte = 1,0 : aucun
  coût fixe par phrase qui pénaliserait les dialogues). **Élargir la fenêtre de
  préchargement ne changerait donc rien** : la file n'est pas vide par manque
  de débit. Ce qu'il reste à regarder, ce sont les **intervalles** entre les
  phrases : un silence de queue **variable** (0,54 à 0,91 s) donne un
  espacement irrégulier d'une réplique à l'autre — auquel s'ajoute la **pause
  de 300 ms** appliquée à chaque changement de paragraphe
  (`PARAGRAPH_PAUSE_MS`, `frontend/app.js`), donc **à chaque réplique** dans un
  dialogue. Voir le constat (2).
  **(2) Les points marquent une pause plus longue qu'avec Kokoro ou Edge**, et
  il reste **quelques sons étranges** (respirations, artefacts) en fin de
  phrase ; Laurent propose de **couper net après le point**, ou du moins plus
  tôt qu'aujourd'hui. Mesure : nouvel outil
  `xtts_service/_mesurer_bords_xtts.py` (sans moteur, sur les 19 WAV du lot
  d'écoute) → **silence de queue moyen 0,59 s (0,54 à 0,91 s)**, silence de
  tête négligeable (0,00 à 0,02 s), et des **pauses internes de 0,30 à 0,35 s**
  un peu partout. Rappel : Edge est **déjà rogné** (`modules/audio_trim.py`,
  0,25 s de queue) mais **XTTS ne l'est pas** — c'est exactement l'item
  « XTTS : rogner les silences de bord » ci-dessus, **remis sur la table par
  cette écoute**.
  *Décisions possibles* — **✅ DÉCISION DE LAURENT le 15/09/2026 : les DEUX
  remèdes, faits le jour même.**
  **(1) Rognage** du silence de queue XTTS à **0,25 s** (même marge qu'Edge),
  dans `servir_xtts.py` : constante `SILENCE_QUEUE_S`, fonction `rogner_queue()`
  appelée à la fin de `generer_wav()`. En numpy (déjà utilisé là-bas), aucune
  dépendance ajoutée ; la **parole n'est jamais touchée** ; en cas de doute
  (audio vide, silence total, erreur) l'audio est renvoyé tel quel.
  **(2) Pause entre paragraphes supprimée** : `PARAGRAPH_PAUSE_MS`
  (`frontend/app.js`) passe de **300 ms à 0** — dans un dialogue, chaque
  réplique est un paragraphe, la pause s'ajoutait donc à chaque échange.
  Remettre 300 la rétablit.
  *Vérification faite* : `test_voix/test_rogner_queue_xtts.py` (14 contrôles,
  **sans moteur** : queue d'origine 0,54 / 0,60 / 0,91 / 2,00 s → 0,25 s ;
  parole intacte avant le dernier son ; rien de rallongé ; aucun plantage) et
  mesure sur les **19 vrais WAV du lot** via la nouvelle option
  `_mesurer_bords_xtts.py --rogner` : queue **0,54-0,91 s → 0,26 s partout**
  (0,25 s + arrondi du bloc d'analyse de 20 ms). `node --check` OK sur
  `app.js`.
  ⚠ Deux points pour l'écoute de Laurent : **fermer puis relancer la fenêtre du
  moteur XTTS** (le service allumé tourne encore avec l'ancien code en
  mémoire), et écouter un passage **pas encore lu** (les phrases déjà écoutées
  gardent l'ancien son, elles sont dans le cache du lecteur).
  *À savoir* : le rognage se ferait **dans le service** (`servir_xtts.py`, en
  numpy, comme prévu dans l'item ci-dessus), jamais dans `modules/tts.py` qui
  est partagé par tous les moteurs ; et il **change la clé du cache audio**
  côté lecteur — les phrases déjà lues gardent l'ancien rendu jusqu'à purge de
  `data/tts_cache/`.

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
  **Reprise du 16/09/2026 — banc d'écoute prêt.** Depuis ce constat, deux
  correctifs sont passés (bornage anti-babil + coupure du résidu après un
  silence) : l'état réel n'est donc plus celui du 15/09. Un **banc d'écoute**
  régénère les cas pièges **avec le code d'aujourd'hui**, sur **deux voix**
  contrastées (une aiguë vive, une grave posée) :
      python test_voix/_banc_ecoute_xtts.py      (moteur XTTS allumé)
  Il écrit `test_voix/ecoute_xtts_<date>/` avec les WAV numérotés, un
  `index.txt` (phrase + ce qu'on cherche à entendre) et un lanceur
  `ECOUTER_LE_LOT.cmd` en double-clic. Les cas : **A** attaque après retrait
  des guillemets, **B** incise avec tiret (remplacé par une virgule),
  **C** tiret cadratin en tête, **D** `Non.` (ultra-court), **E** fin de phrase.
  *Mesures du 16/09/2026* (à confronter à l'écoute) : **A** : 0,89 s propre avec
  Yvette, mais **2,23 s et 5 segments** avec Augustin ; **C** : **résidu de
  0,86 à 0,94 s** pour les deux voix (au-dessus du seuil de coupure de
  0,35 s, donc conservé) ; **D** : propre avec Yvette, **4 segments** avec
  Augustin ; **E** : 4,59 s avec Augustin (un peu long). **En attente** : le
  verdict de Laurent sur les 10 fichiers — c'est lui qui décide quels cas
  méritent un remède (le tiret d'incise conservé est la piste la plus simple).
  *Banc régénéré le même jour après redémarrage du service* (donc avec les deux
  correctifs actifs) : le gain est net — **A** avec Augustin passe de 2,23 s /
  5 segments à **0,93 s / 1 segment**, **D** de 0,79 s à **0,53 s**, **E** de
  4,59 s à **3,25 s**, et le résidu du **C** disparaît avec Augustin.
  Restent deux résidus de **~0,8 s** (C avec Yvette, B avec Augustin), au-dessus
  du seuil de coupure : à juger à l'oreille. *Rappel* : le moteur est
  stochastique, deux tirages de la même phrase ne donnent pas le même résultat.
  *Lanceur créé pour Laurent* : `test_voix/LANCER_BANC_ECOUTE_XTTS.bat`
  (double-clic ; il vérifie que le moteur XTTS est allumé).
  **Défaut supplémentaire trouvé le 16/09/2026 — le moteur PRONONCE le point
  final.** Écoute de Laurent sur `B_incise_dp_femme003.wav` : « la voix lit
  *point* à la fin de sa phrase : … au pied de la tour **[point]**, quasiment
  pas de pause entre "tour" et "point" ». C'est le même travers que pour les
  guillemets (XTTS ne sait pas *ignorer* la ponctuation, il essaie de la
  prononcer) — et c'est **intermittent** (moteur stochastique).
  *Comparaison A/B préparée* : `test_voix/_banc_point_final.py` envoie la même
  phrase **avec** puis **sans** son point final, 3 fois chacune, sur deux fins
  de phrase (12 fichiers dans `test_voix/point_final_<date>/`). **A** = avec le
  point (ce que le lecteur envoie aujourd'hui), **B** = sans. *Mesures du
  16/09/2026* : un tirage **A** (3ᵉ répétition de la phrase du constat) part en
  **2,20 s** de résidu — le cas à écouter — tandis que la plupart des autres
  tirages sont propres des deux côtés, ce qui confirme l'aspect aléatoire.
  *Décision attendue* : si les **B** disent la phrase sans « point » **et**
  gardent une vraie fin de phrase (pas d'intonation montée, pas de mot coupé),
  alors on retire le **point final** dans `nettoyer_pour_xtts()` (une ligne,
  avec un test) — les `?` et `!` sont conservés, ils portent l'intonation.
  *Premier verdict de Laurent (banc A/B)* : **aucun « point » prononcé** dans
  les 12 fichiers (donc Yvette ne le fait pas toujours : c'est bien
  intermittent). Mais il a repéré autre chose, plus fin : la **prosodie**.
  Sur `accuse_r1_A_avec_point` la voix « descend partout » (plate) alors que
  `accuse_r1_B_sans_point` **bouge** (montées sur « enfin », « marche »).
  *Test à l'aveugle pour trancher* (`test_voix/_banc_aveugle_point_final.py`,
  12 échantillons mélangés, 6 avec le point, 6 sans, correspondance cachée) :
  classement de Laurent — **vivants** = 01, 03, 05, 07, 08, 10 ;
  **plats** = 02, 04, 06, 09, 11, 12.
  *Croisement* : **sans le point → 4 vivants sur 6**, **avec le point →
  2 sur 6**. Tendance en faveur du retrait, mais **insuffisante pour conclure**
  (à 6 contre 6, un 4-2 peut venir du hasard). *Analyse plus parlante* : en
  regroupant par PHRASE, la phrase du constat est jugée vivante 2 fois sur 6 et
  la phrase témoin 4 fois sur 6 — **la variabilité entre phrases et entre
  tirages pèse plus que la ponctuation finale**. Laurent précise que même les
  tirages « plats » sont « d'une qualité remarquable » : l'écart ne porte que
  sur une prosodie moins « chantante ».
  *Ce qui reste acquis* : le point final peut être **prononcé** (« point ») de
  façon intermittente — défaut réel, entendu une fois ; le retirer supprime ce
  risque sans dégrader la prosodie (aucune perte constatée sur 12 échantillons).
  *Verdict du test LARGE (20 tirages, phrases groupées — demande de Laurent)* :
  même phrase 10 fois de suite, variantes toujours mélangées et cachées.
  Classement de Laurent — **vivants** : A03, A06, A08, A10, B01, B03, B04, B05,
  B07, B10 ; **plats** : A02, A04, A07, A09, B02, B06, B08, B09 ; deux cas
  particuliers (**A01 et A04**) finissent « comme une interrogation ».
  Croisement (outil `test_voix/_depouiller_point_final.py`) :
  **AVEC le point → 7 vivants / 2 plats** ; **SANS le point → 3 vivants /
  6 plats** — et la tendance tient **dans les deux séries séparément**.
  **Conclusion : l'hypothèse « le point final bride la prosodie » est
  DÉMENTIE.** Les deux tests se contredisent : aucun effet démontré, et si effet
  il y a, il irait plutôt dans l'autre sens (le point aiderait).
  *Décision : on NE retire PAS le point final.* Aucun bénéfice démontré, et le
  risque associé (« point » prononcé) est **rare** : entendu une seule fois sur
  une trentaine de tirages, et pas du tout dans le test large.
  *Remarques de Laurent, à garder* : (1) le côté « plat » **n'est pas un défaut**
  — « dans une narration, parfois le côté plat fait partie de la prosodie
  adaptée » ; (2) deux tirages finissent « comme une interrogation » alors que la
  phrase est déclarative (A01 avec le point, A04 sans) : défaut intermittent,
  **indépendant du point final**, à surveiller ; (3) **piste à explorer un jour**
  : « forcer un peu le côté chantant d'un personnage ». Les leviers réels sont
  l'**extrait de référence** (XTTS imite son style : une référence vive donne un
  clone vif — c'est déjà ce que font les critères `debit` et `timbre` du
  re-cast) et les **paramètres de génération** du moteur (`temperature`,
  `length_penalty`), aujourd'hui **non exposés**. À ouvrir comme un chantier à
  part entière, pas à improviser.

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
  ⚠️ **Rectifié le 23/09/2026** : la n° 33 (**Quentin**) **n'est plus écartée** —
  elle porte `stars: 1` depuis le 20/09/2026, et **Laurent l'a confirmée
  RETENUE** le 23/09/2026 (1 étoile, **accent canadien** : région
  « Canada (Kyutai) » et drapeau 🇨🇦, dans les **trois** catalogues qui clonent
  cet extrait). Elle est donc **dans** le pool automatique ; le détail est dans
  « Déjà livré » à la date du 23/09/2026.
  **Étiquetage livré (12/09/2026, suite)** : chaque voix Kyutai porte
  désormais, comme les voix Edge / Kokoro / Piper, un **prénom français**
  (35 prénoms, **aucun en double** avec les 91 noms déjà utilisés — contrôle
  automatique dans `test_voix/test_pool_casting.py`), le **drapeau**
  `🇫🇷 France (Kyutai)` et son **genre (F/M)**. Le genre apparaît maintenant
  dans **tous** les menus déroulants pour **toutes** les familles, sous la
  forme « Prénom (F) — 🇫🇷 France (Kyutai) ».

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

  **Verdict de Laurent (15/09/2026) — le chantier Piper est CLOS.** Après avoir
  écouté **plus de 100 voix Piper** : « lamentables, très très mauvais,
  inutilisable pour NIMM ePub ». Décision : **on n'investit plus dans Piper**
  (ni nouveaux modèles communautaires, ni entraînement) — le chantier
  « fabriquer des voix » reste ouvert **sur Kokoro seulement**, « un jour »,
  sans aucune urgence (« j'ai l'impression que le fine tuning est plus
  accessible », et c'est exact : une voix Kokoro est un vecteur de 256 nombres,
  le reste du modèle reste gelé).
  *À savoir* : les **4 voix Piper** encore proposées dans les menus ne servent
  plus à rien depuis le 15/09/2026 — les petits rôles sont désormais lus par le
  narrateur (voir « Distribution fine des petits rôles ») et Piper est hors du
  pool automatique. Les retirer des menus n'aurait donc **aucune conséquence**
  sur le casting ; elles resteraient dans le **catalogue complet**, qui sert à
  **nommer** les voix des livres déjà castés.
  **Décision de Laurent (15/09/2026) : on les LAISSE dans les menus** (« elles
  ne servent plus mais elles ne font pas de mal »). Le chantier Piper étant clos,
  les retirer ne rapporterait rien. À reprendre seulement si un jour la liste
  des voix devient pénible à parcourir sur mobile — cela relève alors de l'item
  « Regroupement `<optgroup>` des voix par pays dans les menus ».

  **Usage d'XTTS v2 : assumé, privé, et c'est le bon choix** (15/09/2026).
  Verdict de Laurent : « mes livres, mes voix, et mes oreilles ». Sa licence
  étant **non commerciale**, l'audio produit ne doit **jamais** être publié ni
  partagé — mais tant que NIMM ePub reste **privé**, il n'y a **aucune**
  conséquence, et c'est le moteur qui donne les meilleurs résultats à l'oreille.
  À ne pas oublier le jour où le projet s'ouvrira : voir l'item « PARTAGE :
  quelles voix peut-on laisser dans un dépôt public ? ».

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

## 🟡 Priorité 3 — Robustesse & architecture

- [ ] **Centraliser le découpage en phrases**
  **Quatre** implémentations coexistent : `_buildSentences` (app.js),
  `_split_sentences` (main.py), `_split_chapter_sentences` (voice_casting.py) et
  `modules/decoupage.py` — cette dernière porte la règle de **référence**,
  recopiée **mot pour mot** dans la page (le test compare les deux listes de
  verbes de parole). Risque de divergence silencieuse à chaque évolution de règle
  → une seule fonction partagée + tests.
  *(Relevé du 22/09/2026, audit de la documentation : les quatre existent
  toujours. La page porte en plus la règle du **mode dialogue**, pour la
  recherche et la carte des morceaux.)*

- [ ] **Suite de tests automatisés + CI**
  *Une partie est faite (21/09/2026)* : la suite existe et se lance en
  double-clic — `LANCER_TOUS_LES_TESTS.bat`, **39 tests** (22 JavaScript +
  17 Python) au vert le 22/09/2026 — avec sa leçon : un test absent de la liste
  du lanceur **ne tourne jamais** (`test_attribution_criteres.py` avait dérivé
  sans que rien ne le signale). *Ce qui manque encore* : la **CI** (GitHub
  Actions sur les fichiers Python/JS).
  *Relevé du 22/09/2026, audit de la documentation* : **35 tests Python** vivent
  encore **hors** du lanceur global — c'est exactement le piège du 21/09 (un test
  absent de la liste **ne tourne jamais**, et il dérive sans que rien ne le
  signale). Plusieurs n'ont besoin d'**aucun moteur** (`test_cache_audio.py`,
  `test_pwa_manifeste.py`, `test_requirements.py`, `test_estimation_cout.py`
  paraissent dans ce cas) : les trier et les ajouter au lanceur est un petit
  chantier à part entière. La liste complète s'obtient avec
  `python test_voix/_auditer_documentation.py` (section 5).

- [ ] **Découper les gros fichiers en modules**
  Tailles relevées le **22/09/2026** (audit de la documentation) :
  `frontend/app.js` **6 109 lignes**, `main.py` **2 572**,
  `modules/voice_casting.py` **1 908**, `modules/tts.py` **1 371** — les
  « ~1900 lignes » et « ~900 lignes » écrites ici dataient de la création de
  l'item. À découper quand la navigation dans le code devient pénible ; le
  chiffre fait maintenant jalon, donc l'item est **mesurable**.

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
  *Garde-fou automatique ajouté le 17/09/2026* : `test_voix/test_pas_de_secrets.py`
  contrôle ce que Git emporterait (fichiers suivis **+** nouveaux non ignorés) :
  clés d'API écrites en clair (`sk-`, `hf_`, `gsk_`, `AIza`, jeton `Bearer`),
  fichiers sensibles suivis, audio / EPUB / base SQLite versionnés, environnements
  Python des moteurs, extraits de référence NeuTTS. **Honnêteté** : sa première
  version ne détectait rien — le motif cherchait `sk_` alors que les clés
  s'écrivent `sk-` ; le trou a été trouvé en collant une **fausse clé** dans un
  fichier d'essai (non détectée → motif corrigé → détectée, fichier supprimé).
  Leçon : un garde-fou qui dit « OK » doit être **éprouvé par un cas faux**.
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

## ♿ Accessibilité — chantier ouvert le 15/09/2026 (avec Nando)

**Pourquoi maintenant** : Nando rejoint le projet comme relecteur (invitation
envoyée le 15/09/2026). Il est **aveugle** et travaille au **lecteur d'écran**.
Il peut déjà lire le code et juger l'architecture, mais il ne pourra pas
**utiliser** NIMM ePub tant que ce chantier n'est pas fait — et c'est lui qui
saura le mieux dire ce qui manque. À mener **par petites étapes, avec lui**.

**État des lieux, mesuré le 15/09/2026** (il y a déjà un début, ce n'est pas un
désert) :
- `frontend/index.html` : `<html lang="fr">` ✓, **34 `aria-label`**,
  **5 `aria-modal`**, **13 `role`** (dont les fenêtres en `role="dialog"`) ;
- **36 boutons**, dont la plupart portent un **texte visible** (donc lus) — le
  seul à surveiller est la croix de la recherche (`#search-clear-btn`) ;
- **manques identifiés** : aucune **alternative textuelle** sur les couvertures
  de livres (elles sont créées par `app.js`, aucun `alt=`) ; **aucun `aria-live`**
  (le changement de chapitre, l'état de lecture, la coupure réseau, les erreurs
  ne sont **jamais annoncés**) ; **structure de titres très pauvre** (2 titres
  seulement) alors que la navigation par titres est le premier outil d'un
  lecteur d'écran ; **aucun piège de focus** dans les 5 fenêtres modales ;
  **focus visible** peu travaillé (3 règles `:focus`) ; pas de
  `prefers-reduced-motion` (l'animation « glitch » du curseur) ;
  **0 `tabindex`**.
- Ce que Laurent dit bien : **rien de tout cela n'est nécessaire pour lire et
  comprendre le code** — c'est un chantier d'interface, à faire à part.

**Pistes, par ordre d'utilité** (à discuter avec Nando avant de commencer) :
1. **Annonces (`aria-live`)** : dire à voix haute le chapitre en cours, l'état
   de la lecture (chargement / lecture / pause), la reprise après coupure
   réseau, et les erreurs ;
2. **Alternatives textuelles** des couvertures (« Couverture de <titre>, de
   <auteur> ») ;
3. **Structure de titres** (`h1` de page, `h2` par section, `h3` par fenêtre)
   pour permettre la navigation rapide ;
4. **Fenêtres modales** : piège de focus, retour du focus au bouton d'origine,
   fermeture au clavier (`Échap`) ;
5. **Labels** des rares boutons-icônes, **focus visible** net partout,
   `prefers-reduced-motion` pour l'animation du curseur ;
6. Le **test de référence** : NVDA (gratuit, Windows) — et, si possible, un
   parcours complet « ouvrir un livre, lancer la lecture, changer de chapitre,
   changer une voix ».


## 🟢 Priorité 4 — Produit

- [ ] **Un tableau de bord des moteurs de voix** (idée du 21/09/2026) — qui
  tourne, **depuis quand**, quelle mémoire, quel moteur est « attendu » et lequel
  dort. L'information existe déjà (le voyant **🛠️ Réparer**, `/api/moteurs`, les
  journaux de chaque service) mais elle est **dispersée** : sur le PC il faut
  ouvrir les fenêtres des moteurs, et sur le téléphone seul le voyant parle. Ce
  serait le premier endroit où regarder quand « quelque chose cloche sans qu'on
  sache quoi ». À faire **après** ce qui sert tous les jours : niveau 4.

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
  ⏸ **Décision de Laurent, 20/09/2026 : ON ATTEND.** « Pour l'export MP3, on
  attend que j'aie des voix très bonnes, il y a encore quelques-unes à régler
  avant la touche finale d'export en MP3. » L'item reste **ouvert, sans date** :
  c'est la qualité des voix qui décidera du moment. Rien d'autre à faire ici
  d'ici là — le découpage proposé ci-dessus reste valable.



- [ ] **Réglages par profil** (voix/vitesse par défaut, taille de police,
  thème) — la progression est déjà par utilisateur, pas les préférences.

- [ ] **Surveiller la qualité des voix Edge « trop robotiques »** (signalée
  par Laurent) — Kokoro répond en partie ; à confirmer sur plusieurs
  personnages.

- [ ] **Gard « citation ouverte »** : surveiller les tirets de dialogue
  coupés par un `!`/`?` interne (pas encore rencontré en pratique).

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

## ⚪ Actions utilisateur (pas du code)

- [ ] **Tester le casting enrichi (Kokoro + seuil 8)** sur un nouveau livre
  dès que les crédits sont rechargés.
  *Barème vérifié le 22/09/2026* : un livre neuf coûte **0,06 € à 1,41 €** selon
  sa taille (estimation de l'application, calibrée sur une facture Google réelle
  — Shantaram, 30 293 phrases, facturé **0,98 €**). Le livre le plus petit à
  caster ici est « Marathoniens » (3 583 phrases ≈ **0,17 €**) ; le plus gros
  jamais casté est le **Tome 1 du Comte** (4 791 phrases ≈ **0,26 €**).
  ⚠️ Et **activer le mode dialogue AVANT**, pour un livre neuf : le prix est le
  même (±1 %), et l'attribution est juste du premier coup.

- [ ] **📡 Tailscale : deux gestes qui évitent une panne** (relevé le
  20/09/2026, après deux jours de connexion difficile depuis le téléphone).
  1. **Désactiver l'expiration de la clé de ce PC** dans la console Tailscale
     (Machines → `desktop-j60c3lb` → *Disable key expiry*) : elle **expire le
     24/10/2026** et, ce jour-là, l'ordinateur **sort du tailnet** — plus aucune
     appli ne serait joignable, sans qu'on comprenne pourquoi.
  2. **Vérifier la résolution de nom sur le téléphone** : le **DNS sécurisé**
     de Firefox (Paramètres → Vie privée → DNS sécurisé → **Désactivé**) et, sur
     Android, « **DNS privé** » qui ne doit pas viser un fournisseur
     (Cloudflare/NextDNS). C'est **déjà la cause identifiée** d'un problème
     identique (voir ARCHITECTURE, « DNS sécurisé ») : le nom `*.ts.net` ne se
     résout plus **même VPN actif**, alors que tout ce qui passe **par l'IP**
     continue de marcher (le launcher, par exemple).
  *Le diagnostic complet (ce qui marche en IP, ce qui échoue en nom, et les
  commandes de contrôle) est écrit dans ARCHITECTURE.md — mémo « l'appli ne
  s'affiche pas depuis le téléphone ».*

---

## ✅ Déjà livré (pour mémoire)

- **Dans le casting on filtre les PERSONNAGES, dans la modale des voix on cherche
  la VOIX** (24/09/2026, demande de Laurent). Deux changements d'un même geste,
  parce qu'ils se répondent :
  1. **Retrait des cinq boutons d'âge** (Tous les âges / 👦 Enfant / 👨‍🦱 Jeune /
     🧑‍🦲 Adulte / 👴 Vieux) de la fenêtre du casting. Laurent : « Elle ne sert à
     rien ici. Elle devrait servir à sélectionner les personnages, pas les
     voix. » Ce qui lui a été dit **franchement** : ces boutons ne *triaient*
     pas, ils *filtraient* les lignes de personnages sur l'**âge de la VOIX
     portée** — une vérification réelle (« qui parle avec une voix de vieux ? »),
     mais qui n'a pas sa place sous une liste de personnages. La barre ne garde
     donc que le **genre du personnage**, sous l'étiquette « **Personnages :** ».
  2. **Ajout de deux rangs de pastilles dans la modale « Voix de *<personnage>* »**
     (livrée le même jour) : `#cast-voix-genre-actions` (Toutes / ♀️ Femmes / ♂️
     Hommes) et `#cast-voix-age-actions` (Tous / 👦 Enfant / 👨‍🦱 Jeune / 🧑‍🦲
     Adulte / 👴 Vieux). Elles filtrent la **liste des voix** sur le **tag** de
     chacune (genre du catalogue, âge des notes d'écoute) et **sans fermer** la
     fenêtre : on essaie « Vieux », on regarde, on essaie « Enfant », on choisit.
     Un **compte** (`#cast-voix-recap`) dit ce que la liste montre, la **voix
     portée** reste toujours visible (groupe « ⚠️ Voix actuelle »), et les
     filtres sont **remis à zéro à la fermeture**.
  **Deux refus de Laurent, notés ici pour ne pas les reproposer** : le **champ de
  recherche par prénom** (« je ne me souviendrais jamais de tous ces prénoms »)
  et le **timbre** (« c'est anecdotique »).
  *Vérifications* : `test_voix/test_filtre_age_casting.js` **réécrit** — il
  surveillait le filtre d'âge des personnages, il surveille maintenant celui des
  voix — **44 contrôles** ; `test_voix/test_entete_casting.js` adapté (le filtre
  de liste actif ne dépend plus que du genre) ; `test_ids_ecran.py` (nouveaux
  éléments, et disparition de l'ancien groupe) ; `test_libelle_deux_lignes_rendu.py`
  (la liste garde **499 px** sous les filtres, et les pastilles tiennent sur un
  rang qui défile) ; **toute la batterie** au vert. *Détail* : ARCHITECTURE.md,
  sujet « Distribution de voix par personnage (IA) » et ses deux tableaux de
  barres de filtre.

- **La liste des voix d'un personnage s'ouvre dans une MODALE** (24/09/2026,
  demande de Laurent : « une genre de modale classique, qui prend plus de place
  sur l'écran (mobile et pc), pour une meilleure visibilité »). La liste était
  dépliée **dans la ligne du personnage** (`.voix-liste-encart`) depuis le
  22/09/2026 : sa largeur était celle de la colonne du casting et sa hauteur de
  **240 px** au plus, soit quatre ou cinq voix visibles sur un téléphone. Elle
  s'affiche maintenant dans `#cast-voix-modal` : **560 px** de large sur un
  ordinateur (contre 440 pour la fenêtre du casting), **toute la largeur de
  l'écran** sur un téléphone, des lignes de **52 px** (texte 0,9 rem, ▶ de
  40 px), un titre qui porte le **nom du personnage**, et quatre façons de
  fermer (croix, « Fermer », clic à côté, Échap) plus la fermeture **avec la
  fenêtre du casting**. Le contenu ne change pas d'un iota (même fonction pure
  `_lignesVoixPersonnage`, mêmes groupes, mêmes deux lignes par voix, même ▶
  **qui ne ferme rien** : on écoute, on compare, on choisit). La fonction
  devient `_ouvrirVoixPersonnage()` — `_basculerListeVoixPersonnage()` et
  `.voix-liste-encart` disparaissent — et `_boutonVoixPersonnage()` reçoit le nom
  du personnage pour porter `aria-haspopup="dialog"`. *Vérification* :
  `test_voix/test_libelle_deux_lignes_rendu.py` section 3 (**20 contrôles**,
  téléphone 360 px **et** écran 1200 px, Chromium) + `test_ids_ecran.py`.
  *Piège du jour, gardé avec l'item* : `node --check` a attrapé une **collision
  de nom** — le paramètre `nom` ajouté à `_boutonVoixPersonnage()` écrasait la
  variable locale `nom` qui écrit le libellé ; vérifier la syntaxe n'est pas une
  formalité. *Détail* : ARCHITECTURE.md, sujet « Distribution de voix par
  personnage (IA) ».

- **Les pauses de Kyutai : queue rognée à 0,20 s, sauts de ligne à 600 ms**
  (23/09/2026, demande de Laurent : « les pauses après les points un peu
  longues, les sauts de ligne trop rapides »). Les deux réglages se **cumulent**
  — le silence après un saut de ligne, c'est la queue du moteur **plus** la pause
  du lecteur — donc ils ont été changés **ensemble**, sinon les sauts de ligne
  auraient perdu de l'air au lieu d'en gagner. Mesure avant de toucher
  (`_essais/_mesurer_bords_cache.py`, lecture seule, sur les **300 WAV du cache**,
  aucun moteur allumé) : queue **médiane 0,37 s**, maximum **1,15 s**, **219
  fichiers sur 300** au-delà de 0,18 s — c'est la respiration du modèle (0,30 à
  0,43 s), que **rien ne rognait** (le service de Kyutai ne règle que sa
  respiration, à 0 par défaut). `modules/audio_queue.py`
  (`QUEUE_GARDEE_S = 0,20`) est appelé par `synthesize_kyutai` **avant** la
  vitesse, la hauteur et le niveau, donc **avant la mise en cache** ;
  `VERSION_CACHE` passe à **18** (sans quoi les phrases déjà écoutées gardaient
  l'ancien silence) et `PARAGRAPH_PAUSE_MS` de 300 à **600 ms**. Effet à
  l'oreille : environ **0,20 s après un point** (au lieu de 0,37 s) et **0,80 s
  après un saut de ligne** (au lieu de 0,67 s). *Vérification* :
  `test_voix/test_rogner_queue_kyutai.py` (**18 contrôles**, rien à allumer) +
  la suite complète des tests. *Détail* : ARCHITECTURE.md, sujet « ✂️ Rognage
  des silences de bord ».

- **La voix « Quentin » (Kyutai n° 33) : constatée, retenue, et passée au
  drapeau canadien** (23/09/2026) : en écrivant l'état actuel de
  `modules/tts.py`, on a trouvé que cette voix était écrite « **écartée**,
  `stars: 0` » **partout** — `ARCHITECTURE.md`, BACKLOG, **et le commentaire de
  sa propre ligne de code** — alors que le code portait **`stars: 1`** depuis le
  commit **`6da7d2d` du 20/09/2026** : elle était donc **déjà dans le pool
  automatique** (la règle est `stars > 0`, `voice_casting.py`).
  **Décision de Laurent, 23/09/2026** : elle est **retenue** à 1 étoile, et son
  timbre a un **accent canadien** → région « **Canada (Kyutai)** » et drapeau
  🇨🇦, appliqué aux **trois** catalogues qui clonent ce même extrait (`kyutai:`,
  `xtts:`, `neutts:`). Copie datée du module avant écriture :
  `modules/tts.py.bak_avant_quentin_20260923`. Les 34 autres voix Kyutai sont
  intactes. *Leçon* : une valeur qui change dans un commit **sans que le
  commentaire de sa ligne suive** est une dérive invisible — celle-ci a vécu
  trois jours en contradiction avec trois documents.

- **`test_niveau_audio.py` : l'attente réparée, pas le module** (23/09/2026) :
  la suite était revenue avec **un test rouge**, `test_niveau_audio.py` — et
  c'est un **lancement de `test_kyutai_branchement.py`** qui l'avait provoqué,
  sans le vouloir : ce test **écrit** le témoin
  `test_voix/kyutai_branchement_normal.wav` (la phrase lui est servie par le
  **cache disque** quand le moteur est éteint), et le témoin est passé de
  **7,1 %** (le chiffre noté dans le commentaire) à **8,6 %**. Or depuis la
  révision du 21/09/2026 la correction du niveau est **bornée des deux côtés** :
  une phrase **déjà à la cible** (8,5 %) n'est plus remontée — le test attendait
  donc une remontée qui n'avait plus lieu d'être. **Le module avait raison.**
  Le contrôle a été réécrit (deux contrôles qui tiennent **quel que soit** le
  niveau du témoin : jamais éloigné de la cible, et corrigé dans le bon sens
  s'il est hors fourchette de ±3 dB), et le niveau du témoin est **affiché** —
  le jour où il changera encore, on saura pourquoi sans chercher. Copie datée
  avant écriture : `test_voix/test_niveau_audio.py.bak_avant_temoin_20260923`.
  Suite complète : **« TOUT EST OK », 40 tests**.

- **Rattrapage de la dérive du compteur de citation ouverte** (23/09/2026) :
  `_citation_ouverte()` comptait les guillemets depuis le **début du chapitre**
  au lieu du **paragraphe** — après un passage lu à voix haute, tout le reste du
  chapitre était refusé. Signalé par un relecteur externe, **mesuré puis
  corrigé** : **155 morceaux** de narration remis au narrateur sur les livres
  déjà migrés (8, 14, 15, 16, 17, 28, 33, 34, 35 — 22/11/63 compris, migré le
  22/09 avec le même défaut), via le nouvel outil
  `test_voix/_rattraper_beats_derive.py` (copie datée de la base avant,
  contrôle après : index dans les bornes, locuteurs au casting, **reste à
  corriger : 0**). Le correctif du compteur est dans `_migrer_index_dialogue.py`
  (il profitera à la migration du livre 18). *Laissés exprès* : **74 morceaux
  « impurs »** (règle R3) et **12 morceaux à 2ᵉ personne** — dont le cas du
  docteur d'Avrigny (« Si elle avait commis un second crime, **je vous**
  dirais : »), qui est du **discours de personnage** : c'est la règle R6, « dans
  le doute, ne pas dégrader ». *Leçon* : le premier filtre (1ʳᵉ **et** 2ᵉ
  personne) écartait 46 morceaux, dont « Il **m'**a adressé un sourire en
  ajoutant : » — de la narration dans un récit à la première personne. La
  **2ᵉ personne seule** garde 12 cas, tous justes.

- **Migration des 9 livres déjà castés en narration séparée** (23/09/2026) :
  `test_voix/_migrer_index_dialogue.py` a remappé les index **et** activé le mode
  dialogue pour **9 des 10** livres déjà castés (Monte-Cristo T2→T6, Souvenirs
  d'une gamine, Shantaram, Notre-Dame de Paris, le Chevalier Errant) — **327
  morceaux** de narration remis au narrateur. **Le livre 18 « Dialogues
  désaccordés » est laissé de côté** : la lecture a montré que ses 68 beats sont
  du **discours de personnage** (item à part, avec la problématique écrite dans
  `PROBLEMATIQUE_decoupage_voix.md`). *Le casting de Laurent n'a pas bougé d'un
  iota* : voix, hauteur, vitesse, verrous, fiches et alias **prouvés identiques**
  (`_essais/_preuve_casting_intact.py`, comparaison avec la copie du 22/09) ;
  0 index hors bornes, 0 locuteur créé, 0 morceau orphelin, reprise de lecture
  remappée sur la même phrase. Copies datées de la base avant écriture
  (`nimm_epub.db.bak_avant_dialogue_20260923_*`). *Deux outils neufs* :
  `test_voix/_etat_migration_dialogue.py` (qui doit migrer, en une page) et
  `test_voix/_simuler_migration_dialogue.py` (mesure des dix livres d'un coup,
  en tâche de fond) ; lanceur double-clic `test_voix/MIGRER_DIALOGUE.bat`.
  *Leçon de méthode vérifiée une fois de plus* : la mesure reproduisait le devis
  **à l'unité près** (395 beats / 691 refusés), mais c'est la **lecture** des
  beats qui a évité une erreur de 68 morceaux — un chiffre juste ne dit pas que
  le texte a raison.

- **Bouton de bascule des moteurs de voix** (15/09/2026) : le voyant du bas de
  la fenêtre de lecture est devenu un bouton (XTTS v2 / Kyutai / aucun), avec
  la règle « un seul moteur à la fois » appliquée côté serveur **et** dans
  `START.bat`. Récap complet dans l'item du BACKLOG et dans ARCHITECTURE.md.

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

---

### Les items livrés, en une ligne (réduction A1 du 22/09/2026)

Réduction demandée par Laurent : le **titre** et la **date** suffisent pour retrouver
un item ; le récit technique vit dans `ARCHITECTURE.md`. Les phrases de
**leçon** (un démenti, une mesure, un piège) sont gardées sous l'item quand
elles se lisent seules ; celles qui ne se lisent pas seules (restes de listes) sont
recopiées **telles quelles** à la fin de ce fichier, parce que rien ne doit
disparaître. *Réduction du 22/09/2026 : le fichier passe de **~490 Ko à ~270 Ko**
(taille sur le disque ; 6 789 → 3 898 lignes).*

#### 🔴 Priorité 1 — Lecture audio (confort immédiat)

- [x] **🪗 Le menu du bas devient un TIROIR : les sept commandes de lecture, et
  rien d'autre** (22/09/2026).
- [x] **Le bouton du bas ne change plus de moteur : il RÉPARE — et Pocket TTS
  redémarre avec le lecteur** (21/09/2026).
  ⚠️ Leçon : `main.py` tolère désormais un BOM en tête de ce fichier (piège
    PowerShell).

  ⚠️ Leçon : `neutts` dans le pense-bête). Leçon : **un `.bat` s'écrit
    TOUJOURS en CRLF**. `START.bat` lui-même est sain (178 lignes en CRLF,
    vérifié) : la faute était dans mon script de diagnostic, jetable.

- [x] **🎒 Pocket TTS : volume qui s'affaisse dans un long paragraphe, et
  débuts de mots mangés** (21/09/2026).
- [x] **⚡ Kyutai : les derniers mots de la phrase d'avant s'entendent parfois
  au début de la suivante** (21/09/2026).
- [x] **Volume des voix Kyutai : niveau ramené à celui des autres moteurs**
  (18/09/2026).
- [x] **Un chapitre pouvait être sauté après une « erreur de chargement » —
  corrigé** (18/09/2026).
- [x] **Bouton « vider le cache audio » dans les réglages** (20/09/2026).
  ⚠️ Leçon : `frontend/styles.css` (leçon du 20/09/2026 : « Onglets » avait
    gardé l'apparence native du navigateur, plus grand et plus clair que ses
    voisins). C'est le **prochain chantier prévu**.

- [x] **Les incises de parole sont RETIRÉES du texte parlé** (18/09/2026).
  ⚠️ Leçon : À retenir : on retire soit **toute** l'incise, soit **rien** —
    jamais un morceau.

- [x] **Banc d'écoute : quelle ponctuation remplacer le « ! » ?**
  (18/09/2026).
- [x] **Les points d'exclamation sont retirés du texte envoyé au moteur**
  (18/09/2026).
- [x] **Le silence après « M. » (lu monsieur) / « Mme » : cause trouvée,
  garde-fou posé** (18/09/2026).
- [x] **Ne plus couper les phrases après une abréviation — le vrai correctif**
  (18/09/2026).
- [x] **Babil du moteur XTTS sur les phrases courtes — corrigé** (16/09/2026).
- [x] **Rogner les silences de bord des fichiers TTS** (08/09/2026).
- [x] **Préchargement « burst » au passage en arrière-plan** (20/09/2026).
- [x] **Lecteur intégré « façon Deezer » + lecteur système complet**
  (20/09/2026).
- [x] **Les phrases sont collées en UN SEUL morceau (la modale reste
  affichée)** (20/09/2026).
- [x] **Pause par le casque, et bouton de lecture qui dit la VÉRITÉ**
  (20/09/2026).
- [x] **Résidus de balises dans le texte lu (« M class="textsuperscript">lle
  »)** (20/09/2026).
- [x] **Bouton « Installer l'application » : seulement sur téléphone**
  (20/09/2026).
- [x] **Installation de l'application : l'option manquait dans Chrome**
  (20/09/2026).
- [x] **UX pendant une coupure réseau** (15/09/2026).
- [x] **Un changement de voix ne s'applique pas pendant la lecture (surtout
  sur mobile)** (15/09/2026).
- [x] **Voir et changer la voix d'une phrase (tap mobile + bouton PC)**
  (15/09/2026).
- [x] **Panneau « Voir la voix » → une PORTE vers le casting** (20/09/2026).
- [x] **Icônes des moteurs + « 🔖 Onglets » à la même échelle** (20/09/2026).
- [x] **Barre de navigation : quatre flèches symétriques, RSVP déplacé**
  (20/09/2026).
- [x] **Bibliothèque mobile : le titre du livre en entier sous la couverture**
  (15/09/2026).
- [x] **Couvertures écrasées sur mobile dès que la bibliothèque est remplie**
  (16/09/2026).
- [x] **Barre de lecture : suppression du bouton ⏩ (phrase suivante)**
  (15/09/2026).
- [x] **Barre de réglages du lecteur : boutons compacts et thème sombre
  cohérent** (15/09/2026).
- [x] **Le point-virgule ferme l'incise** (19/09/2026).
  ⚠️ Leçon : — donc le contrôle visait un **mot orphelin**, pas le retrait. Il
    vérifie maintenant cela précisément : jamais d'orphelin après le verbe, et
    la réplique garde ses deux morceaux.

- [x] **Le cas « Danglars » : rien à changer** (19/09/2026).
- [x] **Les mots TOUT EN MAJUSCULES sont lus normalement** (19/09/2026).
  ⚠️ Leçon : ⚠️ Piège évité : il faut compter « Jim » (majuscule initiale)
    comme casse normale, **pas** seulement les mots tout en minuscules — sinon
    « JIM » était classé sigle à tort.

- [x] **Des ONGLETS : marquer un passage et le retrouver** (19/09/2026).
  ⚠️ Leçon : ⚠️ **Piège noté pour la suite** : `TestClient` n'exécute **pas**
    le « lifespan » de l'application, donc pas de `init_db()` — un test qui
    touche une table doit appeler `main.init_db()` lui-même.

  ⚠️ Leçon : 🔎 **Leçon du premier essai de Laurent (19/09/2026 au soir)** : le
    panneau s'ouvrait mais la pose échouait (« Impossible de poser l'onglet
    »). **Cause trouvée en direct** : le serveur qui répondait était
    **l'ANCIEN**, lancé avant la livraison → `GET /api/bookmarks/16` renvoyait
    **404**.

- [x] **« MR. CURRIE » lu « MR[féè]. CURRIE » — corrigé** (21/09/2026).
- [x] **Les syllabes inventées autour des prénoms : CORRIGÉ (étape 1)**
  (21/09/2026).

#### 🟠 Priorité 2 — Voix & casting

- [x] **⚙️ Filtres ne s'ouvrait pas : le tiroir des réglages était ÉCRASÉ à
  5 px** (22/09/2026). *(Signalé par Laurent : « quelque chose empêche
  l'ouverture de ⚙️ Filtres, sur PC et mobile ».)*
  ⚠️ Leçon : **un panneau peut s'ouvrir ET rester invisible**. L'état était bon
  (`aria-expanded="true"`, la classe `hidden` retirée) : c'est la **hauteur** qui
  manquait — 5 px sur ordinateur, 12 px sur téléphone, pour un contenu de
  427 px, parce que le tiroir était le seul élément autorisé à se réduire face à
  une longue liste de personnages. D'où la règle qui manquait : **un garde-fou
  qui ne mesure que l'état ne voit pas ce genre de panne** — il faut mesurer le
  RENDU (`test_filtres_rendu.py`, avec une liste de 120 personnages).
- [x] **🧹 La fenêtre du casting respire : en-tête compact, tiroir des
  réglages, et la fenêtre ne sort plus de l'écran** (21/09/2026).
- [x] **🎭 Les petits rôles sont joués par DEUX voix : Jessica (femmes) et
  Pierre (hommes)** (21/09/2026).
- [x] **🔒 Le cadenas du casting est un DESSIN, plus un emoji : verrouillé et
  déverrouillé ne se ressemblent plus sur le téléphone** (21/09/2026).
- [x] **La vitesse réglée sur un personnage n'était JAMAIS appliquée —
  corrigé** (20/09/2026).
- [x] **La voix du NARRATEUR passe d'un livre à l'autre — chaque livre doit
  garder la sienne** (20/09/2026).
- [x] **Voir les voix par THÈME, et non par moteur** (20/09/2026).
- [x] **Menus de voix : des DRAPEAUX et tes notes d'écoute** (19/09/2026).
- [x] **Timbre : « très grave » et « très aigu » ajoutés** (19/09/2026).
  ⚠️ Leçon : *Hypothèse, pas acquis* : Laurent dit « je pense que ça
    améliorera » — la mesure ci-dessus dit seulement ce que contiennent les
    extraits actuels, elle ne prouve pas encore l'effet sur la prosodie. À
    confirmer à l'oreille.

- [x] **Critères FIXES d'annotation des voix (listes déroulantes)**
  (16/09/2026).
- [x] **Re-cast par critères (gratuit) — étape 1 de l'attribution assistée**
  (16/09/2026).
- [x] **Étape 2 — bouton « Re-caster avec l'IA »** (16/09/2026).
- [x] **Re-cast : la cohérence de SAGA est désormais préservée** (16/09/2026).
- [x] **Nouvel ordre du pool automatique de casting, avec XTTS v2**
  (14/09/2026).
- [x] **Filtre / regroupement par genre (H/F) dans la fenêtre du casting**
  (12/09/2026).
- [x] **Ne proposer dans les menus que les voix « écoutables » selon le moteur
  allumé** (14/09/2026).
- [x] **Barre de recherche dans la fenêtre du casting** (20/09/2026).
- [x] **START.bat : rallumer le DERNIER moteur utilisé** (14/09/2026).
  ⚠️ Leçon : *Deux pièges `cmd` trouvés au test et documentés dans
    `ARCHITECTURE.md`* : une **parenthèse dans un texte** à l'intérieur d'un
    bloc `if (...)` ferme le bloc et **arrête tout le script** ; et un bloc
    `if exist ( for ... )` sur plusieurs lignes déraille aussi.

- [x] **Bouton de bascule entre les moteurs de voix (Kyutai ↔ XTTS v2)**
  (15/09/2026).
  ⚠️ Leçon : `_pids_moteur_kyutai()`) ; **ne jamais interrompre une génération
    en cours** (les demandes sont mises en file une par une) ; prévenir que la
    lecture s'arrêtera si la voix en cours appartenait à l'autre moteur.

- [x] **Regrouper les appellations d'un même personnage — étape 1 (doublons
  d'écriture)** (12/09/2026).
- [x] **Regrouper les appellations d'un même personnage — étape 2
  (rattachement manuel des pseudonymes)** (12/09/2026).
- [x] **Regroupement par alias sur mobile** (12/09/2026).
- [x] **Distribution fine des petits rôles** (12/09/2026).
- [x] **XTTS v2 : la voix « bute » sur les guillemets `« »`** (15/09/2026).
- [x] **XTTS : rogner les silences de bord des fichiers générés**
  (15/09/2026).
- [x] **Notes « stars » définitives pour les 35 voix XTTS v2** (16/09/2026).
  ⚠️ Leçon : *Piège évité au passage* : `piper:tom:0` sert de constante
    `GENERIC_VOICE_M` dans `modules/voice_casting.py` — mais elle **n'est plus
    utilisée** depuis le 15/09/2026 (les petits rôles sont lus par le
    narrateur). Si un jour on redonne une voix aux petits rôles, il faudra
    choisir une autre voix que Tom.

- [x] **Peut-on cloner les voix Kokoro avec XTTS, comme on l'a fait pour
  Kyutai ? — question de Laurent (14/09/2026), analysée et tranchée : NON.**
  (14/09/2026).
- [x] **🎧 Fenêtre « Écouter les voix » (le listener)** (14/09/2026).
- [x] **Règle des paliers d'étoiles pour le pool automatique** (15/09/2026).
- [x] **Report des notes d'écoute dans les catalogues (étape 3 du listener)**
  (15/09/2026).
- [x] **Badges d'état dans la fenêtre du casting** (15/09/2026).
- [x] **Noms des voix dans la fenêtre du casting (identifiants au lieu des
  prénoms)** (15/09/2026).
- [x] **Voir les voix LIBRES et PAR QUI une voix est partagée** (19/09/2026).
- [x] **Prendre une voix déjà attribuée : « Partager » ou « Déplacer »**
  (19/09/2026).
- [x] **Attribuer une voix libre depuis la fiche du personnage** (19/09/2026).
- [x] **Symboles ♀️ / ♂️ pour repérer le genre d'un coup d'œil** (20/09/2026).
  ⚠️ Leçon : *Pièges à ne pas oublier* : écrire les symboles avec leur
    **sélecteur emoji** (`\u2640\uFE0F` = ♀️ et `\u2642\uFE0F` = ♂️), sinon
    ils s'affichent en petit noir et blanc ; et **le genre vide** (« ni F ni M
    ») ne doit pas tomber sur « Homme »

- [x] **Reprise d'une analyse voix multiples interrompue** (13/09/2026).
- [x] **Savoir pourquoi l'IA a refusé de répondre** (13/09/2026).
- [x] **Parade aux filtres de l'IA (refus de traiter un passage)**
  (13/09/2026).
- [x] **Optimisation du coût : format de réponse compact** (13/09/2026).
  ⚠️ Leçon : *Surprise* : **0 token de réflexion** mesuré — l'hypothèse « la
    réflexion explique la facture » n'est PAS confirmée ; le coût venait
    surtout du volume de réponse demandé, que ce chantier attaque directement.

- [x] **Incises lues par le narrateur** (13/09/2026).
- [x] **Moteur local intégré + repli automatique des passages refusés par
  Google** (13/09/2026).
- [x] **Libération automatique de la carte graphique pendant une analyse
  locale** (13/09/2026).
- [x] **Cascade de secours Gemini → DeepSeek → local** (14/09/2026).
- [x] **Estimation de coût recalibrée** (14/09/2026).
  ⚠️ Leçon : *À retenir* : le **comptage des tokens était juste**, ce sont les
    **prix unitaires** qui étaient approximatifs — ils venaient d'ordres de
    grandeur, jamais d'une facture. DeepSeek et Mistral restent dans ce cas :
    à calibrer de la même façon le jour où Laurent donnera le montant réel.

- [x] **La saga transmet désormais aussi la FICHE des personnages**
  (14/09/2026).
  ⚠️ Leçon : *À retenir* : la saga doit transmettre **les deux** — les voix
    (pour l'attribution) et la fiche (pour que le modèle réutilise les mêmes
    noms).

- [x] **Journal des erreurs de casting** (14/09/2026).
- [x] **Parade aux réponses illisibles (JSON malformé)** (14/09/2026).
  ⚠️ Leçon : *Leçon* : sans le journal `data/journal_erreurs_casting.log`, ce
    bug aurait été indétectable après coup (le message n'existait que dans la
    console) ; il a révélé à la fois la cause ET la ligne de code en cause.

- [x] **Installer le moteur XTTS v2 dans NIMM ePub** (14/09/2026).
  ⚠️ Leçon : **Deux pièges mesurés, documentés dans `requirements.txt`** :
    PyTorch **2.8** obligatoire (2.9+ réclame `torchcodec`, qui réclame les
    DLL FFmpeg « partagées » absentes ici) et `transformers` **borné à la
    branche 4.x** (transformers 5.x fait échouer l'import de TTS).

- [x] **Licence NeuTTS lue et tranchée — 14/09/2026** (14/09/2026).
- [x] **« Les retraits se font-ils mécaniquement, ou avec un LLM ? »**
  (18/09/2026).

- [x] **🎒 Pocket TTS : le second lot (10 voix) entre au catalogue — 18 → 28**
  (23/09/2026). Les dix voix du lot NIMM Voix du 23/09
  (`pocket_tts_retenues_20260923`) sont copiées dans `pocket_tts_service\voix\`
  (**28 WAV**) et ajoutées à `POCKET_VOICES` (`modules/tts.py`) sous des
  **prénoms neufs** — Aubin, Cyprien, Lazare, Prosper, Firmin, Gaspard,
  Timoléon, Sylvain, Anselme, Barnabé (vérifiés uniques dans les 339 entrées du
  catalogue) — et **directement à 3 étoiles** (choix de Laurent) : elles peuvent
  donc entrer dans le **casting automatique**. Nouvel outil
  `test_voix/_importer_voix_pocket.py` (rapport seul, `--ecrire` avec copie
  datée) pour écrire leurs critères d'écoute : ces voix n'ont **aucune jumelle**,
  l'héritage NeuTTS ne pouvait rien pour elles, et `pocket:JEAN_EDGAR` reste
  **volontairement** laissé à l'oreille de Laurent. Vérifié : moteur relancé →
  **« MOTEUR PRET : 28 voix disponibles »**, deux voix synthétisées par le
  service (Lazare 3,8 s / Cyprien 3,3 s), `data/annotations_voix.json` de 350 à
  **360** (copie datée), copies datées de `modules/tts.py` et du fichier
  d'annotations, et **tous les tests** (`LANCER_TOUS_LES_TESTS`) : TOUT EST OK.
  ⚠️ Leçon : **une note venue d'un autre atelier peut décrire un état périmé.**
  Le mémo de NIMM Voix (écrit dans la nuit du 20 au 21/09) affirme que « NIMM
  ePub n'a encore aucun service Pocket TTS » : c'était vrai à l'heure où il a
  été écrit, mais le service **existait déjà ici** (installé le 20/09, branché
  le 21/09, 18 voix au catalogue). Quand un atelier parle de l'état de l'autre,
  **c'est le disque qui tranche** — le mémo le dit lui-même : « si quelque chose
  ne colle pas avec ce que tu vois sur le disque, c'est le disque qui a raison ».
  ⚠️ Leçon : **même moteur, licences différentes.** Les 18 voix du 20/09 venaient
  du **domaine public** ; les 10 du 23/09 viennent de **livres audio du commerce**
  (Lizzie, Audible, lus par des comédiens professionnels) : écoute **privée**
  d'accord, **partage interdit** sans l'accord de la personne. Un lot n'hérite
  jamais des droits du lot précédent : la provenance se note **lot par lot**
  (`pocket_tts_service/ATTRIBUTION.md`, section 2 bis).

#### 🟡 Priorité 3 — Robustesse & architecture

- [x] **🔌 Pocket TTS s'éteint en fermant sa fenêtre (comme Kyutai), et le
  veilleur respecte l'arrêt volontaire** (21/09/2026).
- [x] **Serveurs fantômes sur le port 8081 — le piège, et son garde-fou**
  (18/09/2026).
  ⚠️ Leçon : *Le piège* : fermer la fenêtre de commande ne tue pas toujours le
    processus Python. Le port 8081 reste pris par l'**ancien serveur** ; le
    nouveau ne peut pas démarrer (erreur d'une seconde, la fenêtre se ferme)
    et c'est l'ancien qui répond, **avec l'ancien code en mémoire**.

- [x] **Ménage : environnements de moteurs dupliqués retirés de l'atelier**
  (16/09/2026).
- [x] **Le mauvais moteur de voix peut se lancer tout seul** (15/09/2026).
- [x] **Cache audio : statistiques et purge** (20/09/2026).
- [x] **Sécuriser et documenter `test_voix/`** (16/09/2026).

#### 🌍 Diffusion / partage — idée de Laurent (14/09/2026, à ouvrir dans quelques jours)

- [x] **README d'installation** (14/09/2026).
- [x] **Installateur des voix locales** (14/09/2026).
- [x] **Vérification « aucun livre dans le dépôt »** (14/09/2026).
- [x] **Licence du programme : GPL-3.0** (14/09/2026).

- [x] **🔐 Le dépôt passe PUBLIC — contrôle de sécurité complet** (23/09/2026).
  Demande de Laurent (« J'ai passé le dépôt en public, tu crois que j'ai bien
  fait ? ») : vérifié **par la mesure**, pas à l'œil — `git ls-files`,
  `git log -S` (chaque clé connue), `git rev-list origin/main --objects`, et les
  **466 fichiers** jamais ajoutés depuis le premier commit, passés au crible.
  **Verdict : ce qui est publié est propre.** Aucune clé d'API (`cles_api.txt`
  n'est entré dans **aucun** objet Git, pas même dans les points de restauration
  de l'IDE), aucun `data/config.json`, aucune base `nimm_epub.db`, aucun livre,
  aucun audio, aucun extrait d'œuvre sous droits dans les fichiers versionnés
  (`passage_monte_cristo.txt` = 609 caractères de **Dumas, domaine public**).
  `HEAD` local et `origin/main` étaient le même commit au moment du contrôle.
  ⚠️ Leçon : l'adresse e-mail de l'auteur est dans les **63 commits** — donc
  visible publiquement, et non effaçable sans réécrire l'historique (à ne pas
  tenter). Ce qui reste possible : mettre l'adresse *noreply* de GitHub pour les
  commits **suivants**.
  ⚠️ Leçon : les points de restauration locaux de l'IDE
  (`refs/cline/checkpoints/*`) contiennent, **eux**, un EPUB sous droits et 7
  extraits de voix MP3 — **pas atteignables depuis `origin/main`**, donc non
  publiés, mais **ne jamais lancer `git push --mirror`** (ni un refspec large) :
  ça les enverrait. Et partir du principe qu'un dépôt public est **lu** : ce qui
  y entre doit être publiable.
  ⚠️ Leçon : le `README.md` annonçait « **dépôt privé** pour l'instant » — faux
  depuis le passage en public ; corrigé le même jour (**« en développement »**).
  **Décision de Laurent, le même soir** : **le dépôt RESTE public** — « je fais
  pas de pub, il n'y a personne qui va tomber dessus par hasard ». Assumé, le
  contrôle ci-dessus étant passé. *Rappel honnête* : un dépôt public est indexé
  par les moteurs et les robots d'aspiration du code **même sans publicité** —
  sans conséquence ici, puisque rien de sensible n'y est ; mais la règle qui en
  découle vaut pour la suite : **n'entre dans ce dépôt que ce qui est
  publiable**.
  Contrôle à refaire dans l'autre sens le jour où le dépôt redevient privé.


#### ⚪ Actions utilisateur (pas du code)

- [x] **Tester l'écran verrouillé sous Brave** (20/09/2026).
  ⚠️ Leçon : ⚠️ **Leçon** : ce réglage est **la première chose à vérifier**
    avant de chercher dans le code — il a coûté deux jours de doute. Détails
    dans ARCHITECTURE.md (« Lire écran verrouillé »).


---

### Leçons recopiées TELLES QUELLES (elles ne se lisent pas seules)

Ces phrases viennent de l'ancien fichier, où elles étaient prises dans
des listes à puces. Elles ne se lisent pas seules (début ou fin
tronqués) : elles sont recopiées **telles quelles** plutôt que
raccommodées à la va-vite, parce que **rien ne doit disparaître** — et
l'audit du 22/09/2026 a montré que plusieurs ne sont **pas** dans
`ARCHITECTURE.md`. Le titre de leur item est dans la liste, ci-dessus.

- Le bouton du bas ne change plus de moteur : il RÉPARE — et Pocket TTS  —
  *Deux pièges d'atelier trouvés le même jour, et corrigés* (ils dormaient
  depuis le 16/09/2026) : - **`test_start_moteur.py` tuait le lecteur de
  Laurent** : sa « copie neutre » de `START.bat` ne neutralisait pas le
  garde-fou du 18/09/2026

- Le bouton du bas ne change plus de moteur : il RÉPARE — et Pocket TTS  —
  complet** fonctionne. Leçon écrite dans le test.

- Le bouton du bas ne change plus de moteur : il RÉPARE — et Pocket TTS  —
  *Deux pièges de plus, trouvés en testant le geste FORT (et corrigés)* : -
  **un nom court ne se résout plus dans un `cmd` lancé par le lecteur** : le
  bouton « Redémarrer » ouvrait bien une fenêtre, mais elle disait «
  `START.bat` n'est pas reconnu » — et le lecteur **n'était jamais

- 🎒 Pocket TTS : volume qui s'affaisse dans un long paragraphe, et début —
  résultat dément l'attribution** : - **Pocket TTS est STABLE** : niveaux des
  dix phrases `42 39 38 40 30 37 40 34 29 38` → de la première à la dernière
  **−1,1 dB seulement** (une oscillation normale de ±1,5 dB). **Il n'y a pas
  d'affaissement.**

- 🎒 Pocket TTS : volume qui s'affaisse dans un long paragraphe, et début —
  l'ancien niveau (leçon du 17/09/2026).

- ⚡ Kyutai : les derniers mots de la phrase d'avant s'entendent parfois  — -
  et **le piège que Laurent redoutait est réel** : avec **une virgule dans le
  contexte** (« pas, alors »), la virgule fait une pause de **~0,5 s** qui
  arrive **avant** celle du séparateur — les points de suspension tombent
  alors à 0,28 / 0,43 / 0,70 s.

- Les incises de parole sont RETIRÉES du texte parlé — phrases déjà générées
  ne repassent pas par la règle — c'est le piège habituel après un changement
  de texte ; 2. la règle **ratait trois formes très fréquentes** chez Dumas :
  - le **« t » euphonique** (« ajouta-**t**-il », « demanda-**t**-elle ») ;

- Les phrases sont collées en UN SEUL morceau (la modale reste affichée) —
  suit grâce à des durées **calculées** (donc pas de dérive, le piège du
  15/09/2026), et la **barre du lecteur système avance en douceur** au lieu de
  sauter d'une phrase à l'autre.

- Le point-virgule ferme l'incise — *Deux tests ont démenti une formulation
  trop étroite, et ont été REFORMULÉS (avec la raison écrite dedans, pour que
  la question ne revienne pas)* : - `test_nettoyage_tts.py` : le contrôle « le
  sujet de la phrase n'est jamais supprimé » exigeait que « jeune homme »
  RESTE dans « j'écoute, répondit le

- Le point-virgule ferme l'incise — le point-virgule orphelin est nettoyé, et
  un mot piège (« maudit-il ») n'est pas pris pour une incise (ce dernier
  garde-fou n'était testé nulle part). - `test_ponctuation_incises.py` : même
  cas. Son commentaire expliquait le vrai

- Des ONGLETS : marquer un passage et le retrouver — **Règle à retenir** : une
  modification dans `modules/` ou `main.py` demande un

- Les syllabes inventées autour des prénoms : CORRIGÉ (étape 1) — écoutées
  doivent être refaites (leçon du 17/09).

- Critères FIXES d'annotation des voix (listes déroulantes) — étoiles et la
  remarque libre restent à part ; un critère renseigné se voit (bordure
  accentuée).

- Re-cast par critères (gratuit) — étape 1 de l'attribution assistée — accent
  « paysan »** sont volontairement ignorés : trop peu renseignés (constat sur
  les 148 voix annotées).

- Bouton de bascule entre les moteurs de voix (Kyutai ↔ XTTS v2) — modèle
  (n'annoncer « prêt » qu'avec `pret: true`) ; **ne jamais tuer un processus
  au hasard** (cibler par ligne de commande, comme

- Report des notes d'écoute dans les catalogues (étape 3 du listener) —
  **Monique** — un prénom masculin sur une voix féminine est un piège dans le
  casting ; - les **5 voix laissées en « – »** par Laurent avec une remarque
  de défaut (« probleme timbre », « probleme de souffle », « souffle »)
  devaient en fait

- Symboles ♀️ / ♂️ pour repérer le genre d'un coup d'œil — *Les deux pièges
  annoncés sont traités* : les symboles portent leur
