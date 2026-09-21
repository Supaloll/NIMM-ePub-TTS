# BACKLOG — NIMM ePub

Backlog des améliorations à faire, notées au fil des sessions.
**Convention (voulue par Laurent) : on traite les items un par un, par
priorité, à raison d'une ou deux par session — jamais tout d'un coup.**

- Cocher `[x]` quand l'item est livré.
- Les détails techniques des items livrés sont documentés dans ARCHITECTURE.md.

---

## 🔴 Priorité 1 — Lecture audio (confort immédiat)

- [x] **Le bouton du bas ne change plus de moteur : il RÉPARE — et Pocket TTS
  redémarre avec le lecteur** — livré le **21/09/2026**. Retour d'écoute de
  Laurent (6 h) : « j'ai cliqué par erreur sur la ligne tout en bas, qui me
  permet de changer de serveur, apparemment ça a coupé le moteur POCKET TTS. Je
  ne trouve plus les voix à l'intérieur du casting. Il faudrait retirer ce
  bouton, de toutes façons je ne changerais de moteur que depuis le PC. »
  *Les deux causes, trouvées en lisant l'état de la machine* :
  1. `data/moteur_voix.txt` contenait bien `kyutai` : le clic n'avait **rien
     cassé** ;
  2. mais **`START.bat` n'a jamais allumé Pocket TTS** : son bloc vivait
     **après** le bloc Kyutai, dont **tous** les chemins finissent par
     `goto lecteur`. Il était donc **inatteignable**. Le PC avait redémarré à
     05:53 (le service Pocket s'était tu à 01:25, **sans message d'arrêt** :
     arrêt machine, pas panne), et à 09:46 `START.bat` a allumé Kyutai puis
     sauté le bloc Pocket. Or le casting ne propose que les voix **écoutables
     tout de suite** : sans service, plus une seule des 18 voix Pocket TTS — et
     **aucun moyen de les rallumer en les demandant**.
  *Ce qui a été livré* :
  1. **le bouton de changement de moteur est retiré** (`index.html`, `app.js`,
     `styles.css`) : la bascule se fait sur le PC, par le lanceur de chaque
     moteur. Le test vérifie maintenant que **rien** de l'ancien dispositif ne
     subsiste ;
  2. **`START.bat` allume Pocket TTS AVANT le choix du moteur lourd** (label
     `:pocket_pret`, plus aucun `goto lecteur` dans ce chemin) ;
  3. **le lecteur VEILLE sur Pocket TTS** : une ronde discrète (30 s, fil de
     fond `_veiller_moteurs`) le rallume s'il le trouve éteint, **en le disant**
     dans la console, sans essais en rafale (repos de 60 s, puis 10 min après
     6 échecs). C'est la réponse à la vraie difficulté : un rallumage **à la
     demande** est impossible, puisque ses voix ne sont plus dans le casting
     quand il est éteint ;
  4. **l'endormissement du service passe de 30 min à 3 h**
     (`NIMM_POCKET_TTS_INACTIF`) : à 30 min, il s'endormait **en pleine journée
     d'écoute** (c'est exactement ce qui est arrivé ce matin) ;
  5. **le voyant devient « 🛠️ Réparer les moteurs de voix »** : son libellé ne
     parle **que des moteurs ATTENDUS** (Pocket TTS, qui cohabite, et le moteur
     lourd retenu) — sinon il crierait en permanence pour XTTS éteint
     volontairement. Il ouvre un panneau à **deux gestes** : « 🛠️ Relancer les
     moteurs » (doux : rallume ce qui manque, **sans couper la lecture**) et
     « 🔄 Redémarrer NIMM ePub » (fort : lance `START.bat` comme un double-clic,
     **après confirmation**, avec voile de redémarrage et rechargement
     automatique de la page). **Aucun des deux n'éteint un moteur** : la panne
     du jour ne peut plus se reproduire par un clic ;
  6. deux routes nouvelles : `POST /api/moteurs/relancer` et
     `POST /api/serveur/redemarrer`. Le lanceur du PC, lui, **refuse** de
     relancer quand le lecteur tourne déjà (« déjà en marche, rien à lancer ») :
     c'est exactement le trou que le geste fort comble.
  *Vérifications* : **30 contrôles** nouveaux (`test_voix/test_reparer_moteurs.py`,
  rien à allumer) et `test_bouton_moteur.js` réécrit (voyant, disparition de
  l'ancien bouton, câblage des deux gestes) ; **19 tests JavaScript** et les
  tests Python légers au vert. **Contrôle en vrai** : `START.bat` relancé à la
  main → port 8085 ouvert, `/api/moteurs` → `pocket actif=true pret=true
  ATTENDU=true` et `kyutai ATTENDU=true`, `/api/voices` → **163 voix dont 18
  Pocket TTS**. La preuve du correctif est dans `test_start_moteur.py` : il
  vérifie que le port **8085 est testé avant le 8082**, et qu'aucun
  `goto lecteur` ne saute plus le bloc.
  *Deux pièges d'atelier trouvés le même jour, et corrigés* (ils dormaient
  depuis le 16/09/2026) :
  - **`test_start_moteur.py` tuait le lecteur de Laurent** : sa « copie
    neutre » de `START.bat` ne neutralisait pas le garde-fou du 18/09/2026
    (« on arrête le serveur qui écoute sur 8081 »), donc le test arrêtait pour
    de vrai le serveur en marche. Deux autres motifs ne matchaient plus rien
    (ils dataient de l'époque NeuTTS) : le test **lançait aussi le lanceur de
    Kyutai pour de vrai**, sept fois. Il neutralise maintenant **tout**
    (5 remplacements) et **vérifie** qu'aucun lancement ne reste possible dans
    la copie ;
  - **le nom court ne suffit plus pour lancer un `.bat`** : depuis Python 3.11,
    les processus enfants reçoivent `NoDefaultCurrentDirectoryInExePath=1`, donc
    `cmd /c _test.bat` échoue (« n'est pas reconnu ») là où le **chemin
    complet** fonctionne. Leçon écrite dans le test.
  *Effet de bord à connaître* : `test_start_moteur.py` écrit dans le **vrai**
  `data/moteur_voix.txt` (c'est ce que fait `START.bat`) et le restaure à la
  fin. **Ne pas lancer deux fois en même temps** : deux instances se marchent
  dessus et laissent le pense-bête sale (constaté le 21/09/2026, remis à la
  main). `main.py` tolère désormais un BOM en tête de ce fichier (piège
  PowerShell).
  *Deux pièges de plus, trouvés en testant le geste FORT (et corrigés)* :
  - **un nom court ne se résout plus dans un `cmd` lancé par le lecteur** : le
    bouton « Redémarrer » ouvrait bien une fenêtre, mais elle disait
    « `START.bat` n'est pas reconnu » — et le lecteur **n'était jamais
    relancé**. Cause : `start "..." /D ... cmd /k START.bat` passe un **nom
    court**, et depuis Python 3.11 les processus enfants reçoivent
    `NoDefaultCurrentDirectoryInExePath=1` (cmd ne cherche plus dans le dossier
    courant). Corrigé **aux deux endroits** (`_lancer_start_bat_apres_reponse`
    et `_relancer_moteur_voix`, qui portait le même défaut latent depuis le
    15/09/2026) : le lanceur est appelé par son **chemin complet**, avec
    `CREATE_NEW_CONSOLE` — le double-clic exact. **Vérifié en vrai** : lecteur
    relancé, **PID changé** (12876 → 11380), Pocket TTS intact ;
  - **une copie de `START.bat` écrite par Python en LF seul fait DÉRAILLER
    cmd** : la copie de diagnostic, écrite avec des fins de ligne LF, a été
    « lue de travers » par cmd, qui a **exécuté le texte de ses propres
    commentaires** — jusqu'à lancer `neutts_service\DEMARRER_NEUTTS.bat`, donc
    le moteur **NeuTTS**, que personne n'avait demandé (et qui a écrit
    `neutts` dans le pense-bête). Leçon : **un `.bat` s'écrit TOUJOURS en
    CRLF**. `START.bat` lui-même est sain (178 lignes en CRLF, vérifié) : la
    faute était dans mon script de diagnostic, jetable.

- [x] **🎒 Pocket TTS : volume qui s'affaisse dans un long paragraphe, et débuts
  de mots mangés** — **réglé le 21/09/2026** (voir la mise au point en fin
  d'item ; les deux symptômes ont été mesurés, puis l'un corrigé et l'autre
  expliqué). Relevé par Laurent le **21/09/2026**, à l'oreille, sur son
  PC : « Pocket TTS a tendance à diminuer le volume si le paragraphe est très
  long, et à manger les débuts de mots en début de phrase. »
  *MESURE DU 21/09/2026* (`test_voix/_mesurer_pocket_defauts.py` : le paragraphe
  le plus long d'un chapitre de 22/11/63, **1115 caractères**, demandé **phrase
  par phrase** comme le fait la lecture — le niveau est celui de la **parole**,
  et l'attaque est comparée au niveau habituel de la **même** phrase). **Le
  résultat dément l'attribution** :
  - **Pocket TTS est STABLE** : niveaux des dix phrases `42 39 38 40 30 37 40 34
    29 38` → de la première à la dernière **−1,1 dB seulement** (une oscillation
    normale de ±1,5 dB). **Il n'y a pas d'affaissement.**
  - **Kyutai, lui, décroche** : `25 35 28 38 **9** 33 28 33 23 30` → une phrase
    sort à **8,8 %** là où ses voisines sont à **~30 %**, soit **−10 dB** : c'est
    *exactement* l'impression d'un « volume qui baisse » dans un long passage.
    Écart total du moteur sur ce paragraphe : de 8,8 % à 37,5 %, **12,6 dB**.
  - **Pourquoi le correctif existant n'aide pas** : `modules/audio_gain.py`
    (18/09/2026) a été écrit pour **remonter** les phrases trop faibles
    (« on n'atténue JAMAIS », cible **8,5 %**). Or les sorties brutes de Kyutai
    et Pocket sont **au-dessus** de cette cible (25 à 42 %) : le module ne
    **fait donc rien** sur la plupart d'entre elles, et surtout il **n'égalise
    pas** les phrases entre elles. Une phrase faible reste faible à côté de ses
    voisines fortes.
  - **Les débuts de mots mangés ne sont pas propres à Pocket** : sur les reprises
    de phrase précédées d'un silence, **2 sur 5** sont sous −6 dB chez Pocket
    (−10,9 et −8,5 dB) et **3 sur 7** chez Kyutai (−16,4 dB sur « Il n'était
    pas… »). *Réserve honnête* : la mesure ne sait pas distinguer une **attaque
    vraiment écrasée** d'un **premier son naturellement doux** (un mot qui
    commence par « l », « s », « f ») — il faudra affiner avant de conclure.
  *MISE AU POINT DU 21/09/2026 (soir) — la mesure a corrigé le diagnostic, deux
  fois* :
  1. **l'échelle de mesure n'était pas la bonne** : mon premier outil mesurait la
     **crête** par tranche de 2 s, alors que le module du lecteur mesure la
     **moyenne par fenêtre de 30 ms**. Sur la bonne échelle, les niveaux sont
     bien plus bas que ce que j'annonçais — Kyutai de **3,8 à 10,8 %** (médiane
     6,6), Pocket de **7,5 à 12,8 %** (médiane 9,6) — et **le module faisait déjà
     l'essentiel** (il remontait les phrases faibles vers 8,5 %). Mon affirmation
     « il ne fait rien sur ces moteurs » était **fausse** ;
  2. **une « bande de ± 3 dB » a été essayée, puis ABANDONNÉE** : elle laissait
     en place les petites variations — mesuré, il restait **3,7 dB d'écart**
     entre les phrases d'un même paragraphe, soit **le défaut lui-même**. Ces
     variations ne sont pas des nuances voulues : c'est l'instabilité du moteur.
  *CORRECTIF LIVRÉ* (`modules/audio_gain.py`) : la correction va maintenant
  **dans les deux sens** — une phrase trop faible est remontée **jusqu'à la
  cible** (comme avant), une phrase trop forte est **ramenée vers la cible**,
  sans jamais perdre plus de **−6 dB** (`GAIN_MIN`), pour ne rien écraser. Une
  correction inaudible (moins de 2 %) n'est pas appliquée.
  *Le bug attrapé au passage* : l'ancien garde-fou `gain <= 1,02` rejetait
  **toutes** les atténuations, puisque le gain est désormais **inférieur** à 1 ;
  il compare maintenant l'**écart** (`abs(gain − 1) < 0,02`). **C'est le test qui
  l'a trouvé**, avant toute écoute — l'intérêt de réécrire les tests quand la
  règle change.
  *RÉSULTAT MESURÉ, de bout en bout* (les dix phrases du paragraphe de 22/11/63,
  demandées au **lecteur**, comme en lecture) :
  ```
  AVANT (sortie brute du moteur) : 10.8 7.3 6.0 7.2 3.8 5.6 5.4 5.5 7.1 6.6  -> écart 9,1 dB
  APRES (module du lecteur)      : 8.5 8.4 8.5 8.4 8.4 8.5 7.9 8.5 8.1 8.5  -> écart 0,7 dB
  ```
  `VERSION_CACHE` passe à **17** (16 = le réglage, 17 = la purge de l'essai
  abandonné) : les phrases déjà écoutées sont refaites, sinon elles garderaient
  l'ancien niveau (leçon du 17/09/2026).
  *Vérifications* : `test_voix/test_niveau_audio.py` réécrit pour la nouvelle
  règle (**14 contrôles** : une phrase vraiment faible atteint la cible, une
  phrase déjà à la cible n'est pas touchée, une phrase trop forte est ramenée
  mais jamais de plus de 6 dB, les garde-fous tiennent) ; **36 tests** au vert.
  *LES DÉBUTS DE MOTS MANGÉS : QUESTION CLOSE (21/09/2026)*. Verdict d'écoute de
  Laurent, après le lot : « je ne les ai entendus que dans les extraits que tu
  m'as fait écouter tout à l'heure. Dans le livre, les débuts de paragraphes sont
  ok. Je n'entends rien de particulier. » Et la mesure explique **pourquoi** :
  l'attaque écrasée apparaît sur une phrase envoyée **SANS CONTEXTE** — c'est
  précisément ce que faisait le lot (des phrases isolées), alors que la lecture
  réelle en envoie un (3 mots, réglage du même jour) dès que la phrase précédente
  a le même locuteur et le même paragraphe. **Ce n'est donc pas un défaut du
  moteur : c'est le démarrage à froid**, celui que le contexte glissant corrige
  et dont l'absence s'entend dans un lot d'écoute. Rien à corriger.
  *Note de Laurent, à garder* : il avait déjà observé ce phénomène ailleurs, sur
  de **longs textes** où des personnages se donnent la réplique — la voix
  commençait normalement puis **devenait un murmure**, jusqu'à presque
  disparaître. C'est le même défaut de fond (une génération auto-régressive
  **dérive** sur un long texte) — et **l'architecture du lecteur s'en protège
  déjà** en découpant **phrase par phrase** : chaque requête repart avec un
  contexte court, et le module de niveau ramène chaque phrase à la cible (mesure
  du 21/09/2026 : **écart entre phrases 0,7 dB**). C'est un argument de plus en
  faveur du découpage, à ne pas « optimiser » un jour en envoyant des paragraphes
  entiers.

- [x] **⚡ Kyutai : les derniers mots de la phrase d'avant s'entendent parfois
  au début de la suivante** — **corrigé le 21/09/2026** (contexte glissant de
  **8 à 3 mots**, validé à l'oreille ; voir le détail en fin d'item). Relevé par
  Laurent le **21/09/2026** : « les mots sont parfois mangés, surtout au début
  d'une phrase, et parfois le TTS répète les derniers mots de la phrase qui
  finit » (exemple de son écoute :
  « Je ne pense pas. **Pense pas** Mais tu as peut être raison »).
  *Cause probable, lue dans le code* : le **contexte glissant** de Kyutai
  (`_buildPlaylist` → `_fetchAudio` → `synthetize_kyutai` →
  `kyutai_service/servir_kyutai.py`). Pour la phrase B, le moteur génère
  « les 8 derniers mots de A, puis B », et le service **coupe** ce qu'il faut
  jeter en cherchant un silence (`SILENCE_COUPE_S = 0,12 s`,
  `MARGE_CONTEXTE_S = 0,25 s`). Si la coupe tombe **trop tard**, la fin du
  contexte s'entend (« Pense pas ») ; **trop tôt**, c'est le début de B qui est
  mangé. Les deux défauts décrits par Laurent, d'un seul coup.
  *Ce n'est pas Kokoro* : `main.py` ne transmet `context` **qu'à la branche
  Kyutai** — vérifié le 21/09/2026. *(L'oreille de Laurent le confirme : « pour
  les répétitions, c'est clairement Kyutai ».)*
  *Piste de Laurent (21/09/2026)* : « peut-être envoyer moins de contexte
  glissant, par exemple 3 mots au lieu de 8 ? Et j'ai l'impression que c'est
  plus récurrent quand il y a de la ponctuation comme des ; ou des « ou des ... ».
  »
  **MESURE ET CORRECTIF DU MÊME JOUR** (Laurent a donné son feu vert pour
  avancer sans lui). D'abord la mécanique, pour mémoire : le service **ne sait
  pas** « lire le contexte sans le dire ». Il génère **« contexte + phrase »**
  d'un seul tenant, puis **coupe** l'audio dans un silence pour ne livrer que la
  phrase. Deux façons de se tromper : **couper trop tôt** → la fin du contexte
  reste et s'entend (« Pense pas ») ; **couper trop tard** → le début de la
  phrase est mangé. La mesure porte donc sur la **durée de PAROLE** (les moments
  où l'on parle, sans les silences : la durée totale, elle, bouge avec les
  respirations).
  *Sur six cas construits* (l'exemple de Laurent, un point-virgule, des points
  de suspension, un tiret de dialogue, un guillemet fermant, une phrase
  précédente longue) :
  - **8 mots** : **4 cas sur 6** gardaient un **résidu** (+0,40 à **+0,73 s**) —
    le tiret de dialogue et le guillemet fermant en tête, ce qui confirme son
    intuition sur la ponctuation ;
  - **3 mots** : **aucun** résidu, aucun rognage ;
  - 2 mots : aucun problème non plus.
  *Sur quatre phrases RÉELLES de 22/11/63* (outil : `test_voix/_ecouter_contexte_kyutai.py`,
  qui produit un lot d'écoute phrase seule / 3 mots / 8 mots **à travers le vrai
  service** ; mesure des fichiers : parole identique à ±0,2 s avec **3 mots**,
  mais **rognage** de **−0,63 s** et **−0,37 s** avec **8 mots** — l'autre
  moitié du symptôme, « les mots mangés en début de phrase »).
  *Découverte au passage* : **le moteur Kyutai n'est PAS déterministe** (deux
  demandes identiques rendent deux audios différents) — c'est ce qui explique
  que le défaut n'arrive que « de temps en temps » : selon le tirage, la coupe
  tombe bien ou mal.
  *CORRECTIF LIVRÉ* : `CONTEXTE_MOTS` passe de **8 à 3** dans `frontend/app.js`
  (une ligne — la demande de Laurent — avec toute la mesure dans le
  commentaire). Reversible : si les débuts de phrase paraissaient à nouveau « à
  froid », la valeur à essayer est **5 ou 6**.
  **VERDICT D'OREILLE DE LAURENT (21/09/2026)**, sur le lot
  `test_voix/ecoute_contexte_20260921_1835` (phrase seule / 3 mots / 8 mots, à
  travers le vrai service) : « **Le 3 mots part avec un peu de retard, mais c'est
  très bien. Le "seul" part presque en avalant le premier phonème, le premier
  son. Le 8 ressemble pas mal au 3. Je pense que le réglage est très bien.** »
  → **le réglage est validé**, et son oreille apporte la preuve que le contexte
  **sert** : sans lui, **l'attaque est écrasée** (c'est le « démarrage à froid »
  que le contexte glissant était venu corriger, 17/09/2026).
  *Note utile pour la suite* : si un **début de phrase** semble « mangé », le
  **premier réflexe** est de regarder si cette phrase **avait un contexte** — il
  n'y en a **pas** après un saut de paragraphe, ni quand le locuteur change
  (`_buildPlaylist`, frontend/app.js). C'est écrit dans le commentaire du code,
  à l'endroit où la valeur se règle.
  *PISTE OUVERTE PAR SON OREILLE* : ces phrases **sans contexte** sont donc
  **nombreuses** dans un livre de dialogues (chaque réplique ouvre souvent un
  paragraphe), et **toutes** ont l'attaque écrasée. Or on ne peut pas leur
  prêter le contexte d'un **autre** personnage (décision du 17/09 : « un locuteur
  prêterait son élan à un autre »). Idée à éprouver, si Laurent trouve ces
  attaques gênantes à l'usage : leur donner une **amorce neutre**, prononcée
  **avec la voix du nouveau venu** (le moteur lit ce qu'on lui donne, dans la
  voix demandée) — l'élan serait là **sans** emprunter la voix d'un autre.
  À mesurer comme le reste (durée de parole + lot d'écoute), et à ne lancer que
  si le besoin se confirme à l'oreille.
  *RESTE OUVERT* : améliorer la **coupe du service** (`servir_kyutai.py`,
  `_ou_commence_la_phrase`) pour garder un contexte long **sans** résidu. La
  cause est déjà écrite dans le code : `fin_contexte` est mesuré sur le contexte
  rendu **seul**, alors que suivi d'une phrase il est lu un peu plus lentement →
  la coupe tombe trop tôt. Piste : repérer le **silence long** créé par le
  séparateur « … » (le service génère déjà « contexte ... phrase ») au lieu de se
  fier à une estimation proportionnelle. Niveau 3, à valider à l'oreille avec le
  lot ci-dessus.

  **LA QUESTION DU « POINT FIXE » — réponse mesurée (21/09/2026)**. Laurent :
  « Est-ce qu'il existe une ponctuation qui est traitée toujours de la même façon
  par Kyutai ? Si oui, on aurait un point fixe de secondes, toujours le même [...]
  Le truc c'est qu'il faut une ponctuation qui ne provoque pas de coupure dans le
  contexte qu'on lui aurait donné. »
  *Mesure* (`test_voix/_essai_separateur.py`, étendu pour l'occasion : **3 essais
  par séparateur** — c'est la **constance** qui compte, pas seulement l'existence
  d'une pause) : on glisse un signe entre 3 mots de contexte et la phrase, et on
  relève la **plus longue pause** de chaque essai.
  - **points de suspension** : 0,90 / 0,94 / 0,88 s → **0,91 s, écart 0,06 s** —
    le plus régulier, **mais seulement quand le contexte finit proprement** ;
  - **point** : 0,88 / 0,84 / 0,93 s → écart 0,09 s ;
  - **point d'interrogation** : 0,97 / 0,78 / **0,12 s** → écart 0,85 s : il ne
    fait parfois **aucune** pause ;
  - **point-virgule** : 0,85 / 0,84 / **0,29 s** → écart 0,56 s ;
  - **deux-points** 0,34 s, **saut de ligne** 0,12 s : pauses trop courtes (le
    saut de ligne est transformé en espace par le nettoyage) ;
  - et **le piège que Laurent redoutait est réel** : avec **une virgule dans le
    contexte** (« pas, alors »), la virgule fait une pause de **~0,5 s** qui
    arrive **avant** celle du séparateur — les points de suspension tombent alors
    à 0,28 / 0,43 / 0,70 s.
  **Conclusion : aucun signe ne donne une pause constante.** La durée dépend du
  **contexte** (longueur, dernière lettre, virgule interne) et de la phrase qui
  suit, et le moteur n'est pas déterministe. **Le point fixe est donc écarté,
  mesure à l'appui — pas par principe.** Ce qui reste vrai : les points de
  suspension sont le repère le plus fiable (le service les utilise déjà), et un
  contexte de **3 mots est trop court pour contenir une pause gênante** — c'est
  déjà en place depuis le même jour.
  *Piste gardée pour plus tard* (seulement si un défaut revient à l'oreille) :
  situer la frontière par **alignement** — le service génère déjà la phrase seule
  **et** « contexte + phrase » — au lieu de se fier à une durée.

- [x] **Volume des voix Kyutai : niveau ramené à celui des autres moteurs** —
  livré le **18/09/2026**. Constat de Laurent : « le volume des voix Kyutai est
  très, très faible ».
  *Mesure* (`test_voix/_mesurer_niveau.py`, sur le **niveau de la parole seule**,
  et non le niveau global faussé par les silences) : **Edge 8,4 %** de la pleine
  échelle contre **Kyutai 6,2 %**, et jusqu'à **3,4 %** sur certaines phrases —
  soit jusqu'à **-8 dB**. Le moteur Kyutai ne règle pas son niveau de sortie (le
  script officiel de la banque de voix, lui, normalise à -22 LUFS).
  *Correction* : `modules/audio_gain.py` mesure le niveau de la parole (fenêtres
  de 30 ms où l'on parle vraiment) et applique le gain qui l'amène à la cible
  **8,5 %** (le niveau d'Edge). Garde-fous : gain **plafonné à ×4**, crête de
  sortie bornée (**jamais de saturation**), **aucune atténuation** (on ne baisse
  jamais), et tout échec renvoie l'audio d'origine.
  *Mesure de l'effet* sur 120 phrases réelles du cache : niveau de parole médian
  **5,4 % → 8,2 %** (≈ +3,6 dB), le plus bas 2,1 % → 4,6 %, gain médian ×1,45.
  Appliqué dans `synthesize_kyutai` **avant la mise en cache**, après vitesse et
  hauteur : une phrase relue ne redevient jamais faible.
  *Vérification* : `test_voix/test_niveau_audio.py` (10 contrôles, sans moteur).
  *Effet de bord voulu* : `VERSION_CACHE` passe à **4** — les anciens fichiers de
  cache ne sont plus servis, donc le nouveau niveau s'entend dès la première
  écoute, sans purge à faire à la main.

- [x] **Un chapitre pouvait être sauté après une « erreur de chargement » —
  corrigé** — livré le **18/09/2026**. Constat de Laurent : « il passe du
  quatre-vingt-un au quatre-vingt-trois, surtout après une erreur de
  chargement ».
  *Cause* : `loadChapter()` (`frontend/app.js`) posait `_currentChapter = index`
  **avant** la requête. En cas d'échec, la page affichait « Erreur de
  chargement », mais le compteur était **déjà** passé au chapitre raté et les
  phrases de l'ancien chapitre restaient en mémoire : à la fin de leur lecture,
  l'enchaînement appelait `loadChapter(_currentChapter + 1)` — le chapitre raté
  était donc **sauté**.
  *Correction, en trois temps* : (1) le chapitre est **demandé d'abord**
  (`_demanderChapitre`), et `_currentChapter` n'est posé qu'une fois la réponse
  **reçue** ; (2) un échec est **retenté** — 3 essais, 1,2 s entre deux
  (`CHARGEMENT_ESSAIS`, `CHARGEMENT_PAUSE_MS`) — car une panne de chargement est
  presque toujours **passagère** (serveur occupé, réseau qui vacille) ; (3) en
  cas d'échec définitif, les phrases du chapitre précédent sont **vidées**
  (`_afficherEchecChapitre`) — plus de lecture fantôme — et un bouton
  **« Réessayer ce chapitre »** apparaît dans la page, avec un message qui
  rappelle que rien n'est perdu.
  *Effet de bord corrigé au passage* : `_pause(ms)` **plantait** si on l'appelait
  sans signal d'interruption (elle le supposait toujours présent) ; un chargement
  de chapitre n'en a pas. Elle est désormais tolérante.
  *Vérification* : `test_voix/test_chargement_chapitre.js` — **17 contrôles**,
  sans navigateur : le test **exécute le vrai code de `app.js`** sur un faux
  lecteur et un faux serveur (panne persistante, panne passagère, chargement
  normal).

- [x] **Bouton « vider le cache audio » dans les réglages** — **LIVRÉ le
  20/09/2026** (récap en fin d'item). Demande de Laurent du 18/09/2026 (pas
  urgent). Aujourd'hui le cache se purge seul
  par quota (`modules/tts_cache.py`, 2 Go) et par **version** (`VERSION_CACHE` :
  dès que le texte envoyé au moteur change, les anciens fichiers ne sont plus
  servis). Mais Laurent n'a **aucun bouton** pour le forcer à la main, et c'est
  exactement ce qui manque quand on doute d'un rendu : le cache a dû être vidé à
  la main le 18/09/2026 pour écarter cette piste (`test_voix/
  _tester_tts_serveur.py` prouvait que le serveur, lui, nettoyait bien le texte).
  À faire : une route de purge côté serveur, un bouton dans les réglages du
  lecteur, et le compte affiché (« 604 Mo sur 2 Go »).
  ⚙️ **Précision de Laurent, 20/09/2026** : ce bouton devra être **à la même
  échelle et dans le même style** que « 🎭 Voix multiples », « 🎧 Écouter les
  voix » et « 🔖 Onglets » — les quatre partagent la **même règle de style** dans
  `frontend/styles.css` (leçon du 20/09/2026 : « Onglets » avait gardé
  l'apparence native du navigateur, plus grand et plus clair que ses voisins).
  C'est le **prochain chantier prévu**.
  **LIVRÉ le 20/09/2026.** Le bouton **« 🧹 Vider le cache »** est dans la barre
  du lecteur, à la **même échelle et dans le même style** que les autres, et il
  **affiche le compte** : « 🧹 Vider le cache (604 Mo) ».
  - **Serveur** : deux routes neuves — `GET /api/cache_audio` (taille, quota,
    nombre de fichiers ; **lecture seule**) et `POST /api/cache_audio/vider`
    — servies par `modules/tts_cache.py` (`stats()`, `purger()`). **Sans danger
    pour les données** : le cache ne contient que de l'audio **déjà synthétisé**,
    régénérable à l'identique (la synthèse est déterministe) ; seule
    conséquence, la première écoute d'un passage déjà lu redemande le calcul au
    moteur ;
  - **Garde-fou** : une **écriture en cours** (`.tmp`, une phrase en train d'être
    synthétisée) **n'est jamais coupée** par la purge ;
  - **Écran** : libellé composé par `_libelleBoutonCache()` (« 604 Mo », « 1,2
    Go », « 12 Ko », virgule française), **jamais « undefined »** quand le
    serveur n'a pas répondu, et **confirmation** avant de vider (« Cela libérera
    604 Mo (2596 phrases)… »), avec le compte remis à jour ensuite.
  *Vérifications* : **nouveaux** `test_voix/test_cache_audio.py` (le compte et la
  purge, dans un **dossier temporaire** — il compare même le nombre de fichiers
  du **vrai** cache avant/après pour prouver qu'il n'y a pas touché, et vérifie
  qu'un `.tmp` survit à la purge) et `test_voix/test_cache_audio.js` (le libellé,
  tailles lisibles, jamais « undefined ») ; `test_voix/test_ids_ecran.py` (le
  bouton, les deux routes, la règle de style partagée). Détails dans
  ARCHITECTURE.md.

- [x] **Les incises de parole sont RETIRÉES du texte parlé** — livré le
  **18/09/2026**, décision de Laurent après écoute le soir même : « à chaque fois
  les incises ont bien disparu […] et en plus la voix me paraît plus fluide ».
  *Réglage* : `modules/incises.py` (règle prudente), appelé par `_clean_text`
  (`modules/tts.py`) **après** le développement des abréviations. Le texte
  **affiché** ne change pas : seule la version parlée. Un banc d'écoute futur
  teste **la même règle** (le banc importe `modules.incises`).
  *Réveil du 18/09/2026 au soir — « elles sont toujours présentes »* : deux
  causes, mesurées par `test_voix/_diag_incises_reelles.py` (lecture seule) :
  1. **le cache servait l'ancien rendu** (`VERSION_CACHE` passé à **6**) : les
     phrases déjà générées ne repassent pas par la règle — c'est le piège
     habituel après un changement de texte ;
  2. la règle **ratait trois formes très fréquentes** chez Dumas :
     - le **« t » euphonique** (« ajouta-**t**-il », « demanda-**t**-elle ») ;
     - les **particules nobles** (« , dit **M. de Villefort**, ») — le motif
       exigeait une majuscule après la civilité, or « d'Avriguy », « de
       Morcerf » commencent par une minuscule ;
     - les **noms communs avec article** (« , dit **le comte**, », « , reprit
       **la jeune fille**, »).
     Résultat : **289 → 311 incises retirées** sur le tome 5.
  3. **les verbes PRONOMINAUX et les imparfaits** — signalé par Laurent lui-même
     (« est-ce que ça ne va pas coincer sur "se demanda-t-elle" ? ») : il avait
     raison. Le motif exigeait le verbe **juste après la virgule**, donc
     « , **se** demanda-t-elle, » et « , **se** reprit-il, » étaient ignorés
     (sans dégât : l'incise restait entière, aucun « se » orphelin). Idem les
     imparfaits (« , disait-il, »). Corrigé : **314 incises retirées**.
     À retenir : on retire soit **toute** l'incise, soit **rien** — jamais un
     morceau.
  *Tour suivant, exemples de Laurent à l'appui* (18/09/2026, fin de soirée) : il
  donne **trois phrases précises** où l'incise est encore lue —
  « … dit-il au comte. », « fit celui-ci avec sa voix demi-railleuse, comment
  vous portez-vous ? » et « , dit-il, » — et il doute que ce soit automatisable.
  **C'est automatisable**, mesures à l'appui (`_diag_incises_reelles.py`) :
  - **l'incise est retirée EN ENTIER, complément compris** : on étend le retrait
    jusqu'à la **virgule fermante** (« , dit-il au comte, »), ou jusqu'au point
    final si la suite ressemble à un complément (« au comte. », « en souriant. »).
    Bornes strictes : une seule virgule, pas de ponctuation forte, **≤ 70
    caractères** (`LONGUEUR_SUITE_MAX`).
  - **l'incise qui OUVRE la phrase** est reconnue (`MOTIF_DEBUT`) : depuis que le
    découpage sépare les phrases au « ! », « fit celui-ci avec sa voix
    demi-railleuse, comment vous portez-vous ? » n'est plus « entre virgules ».
  - les **démonstratifs** (« celui-ci », « celle-là ») rejoignent les sujets
    reconnus.
  Résultat sur le tome 5 : **361 incises retirées** (289 à l'origine) et
  **19 seulement gardées** (non fermées : les retirer couperait la réplique).
  *Garde-fou trouvé par le contrôle de sécurité intégré* : une phrase qui n'est
  **que** l'incise (« ajouta Valentine en s'adressant à Noirtier. ») devenait
  **vide** — plus aucun son, et le moteur refuserait un texte vide. Désormais,
  si le retrait vide la phrase, **on ne retire rien**.
  *Dernier cas, réglé le 18/09/2026 au soir* (constat de Laurent, extrait à
  l'appui) : « — Ah ! vraiment **?** dit Monte-Cristo. » — le « ? » **coupe la
  phrase**, donc « dit Monte-Cristo. » devient une **phrase à part entière**. Ces
  phrases ne peuvent pas être vidées (le moteur refuse un texte vide, et la
  phrase disparaîtrait de l'écoute) : le lecteur renvoie désormais un **court
  silence** (`modules/silence.py`, `SILENCE_INCISE_MS = 150`, réglable en une
  ligne ; 0 désactive). Décision prise dans la route `/api/tts`
  (`_est_incise_seule`, `main.py`) : **91 phrases** de ce genre dans le seul
  tome 5. L'incise n'est plus **entendue**, elle reste **affichée**, et le rythme
  est conservé. *Vérification* : `test_voix/test_incise_seule.py` (15 contrôles).
  *Puis le cas de la RELATIVE (même soir, extrait de Laurent à l'appui)* :
  « c'est magnifique, dit Cavalcanti, **qui se grisait à ce bruit métallique de
  paroles dorées.** » — l'incise était bien retirée, mais la **relative restait
  seule** et se faisait lire ! Désormais la relative part **avec** l'incise
  → « c'est magnifique. »
  *Et deux cas tordus de plus, apportés par Laurent (toujours le 18/09)* :
  (1) la **relative coordonnée** — « , dit Monte-Cristo, qui sentit l'adresse
  perfide du jeune homme, **et qui comprit** la portée de ses paroles **;** ma
  protection ne vous a été acquise qu'après… » : le « , et qui » n'est PAS un
  décrochage, c'est encore la description du personnage. Le retrait va donc
  jusqu'au **point-virgule**, et la réplique reprend après (« — Vous vous abusez
  complètement, monsieur, ma protection… ») ;
  (2) la **question du personnage** — la phrase fait **409 caractères** et finit
  par un « ? » (« … le bonheur de votre connaissance ?) ») : ce « ? » n'est pas un
  signe de question *après l'incise*, il ne doit donc pas bloquer l'extension. Le
  garde-fou ne regarde plus que la **proposition immédiate**.
  Quatre garde-fous au total, chacun posé par un défaut attrapé par les tests :
  (a) **« que » est exclu** des relatifs (c'est le plus souvent une
  conjonction : « Le fait est, dit Barrois, **que** je meurs de soif ») ;
  (b) une **question juste après l'incise** n'est jamais emportée
  (« , se demanda-t-elle, **que faisait-il ?** » — sinon la phrase finissait en
  « — Et lui ») ; (c) un **décrochage de sens** (« mais », « or », « puis »…, ou
  le point-virgule) arrête l'extension, mais **« et qui »** n'en est pas un ;
  (d) la **longueur emportée** est bornée (200 caractères), pas la phrase entière.
  *Compromis assumé, à valider à l'oreille* : retirer l'incise en entier emporte
  aussi son **complément** (« dit la jeune femme **en donnant son flacon à
  Valentine** » → l'action n'est plus entendue, mais elle reste **à l'écran**).
  Si Laurent préfère garder ces détails, on revient à la version prudente : une
  seule condition à retirer dans `modules/incises.py`.
  *Idée de Laurent (18/09/2026), mesurée le soir même.*
  *Son raisonnement* : avec une voix différente par personnage, l'incise qui dit
  qui parle est redondante — et elle coupe la voix du personnage au milieu de sa
  réplique.
  *Mesure* (`test_voix/_mesurer_incises_supprimables.py`, tome 5 : 5 105 phrases) :
  **289 phrases avec incise = 5,66 %**, dont 104 à pronom (« dit-elle ») et 185 à
  nom (« dit Morrel ») — soit **4 122 caractères = 0,94 % du texte** lu.
  *Ce n'est PAS la même chose que l'étude du 13/09/2026* (écartée, 0,8 %) : celle-là
  comptait les incises **formant une phrase à part**, déjà lues par le narrateur
  (donc déjà correctes). Ici, ce sont les incises **au milieu** d'une réplique,
  aujourd'hui lues par la voix du personnage.
  *Un code proposé ailleurs a été essayé* (trois expressions régulières) :
  **il touche 756 phrases dont 588 sans aucune incise — 78 % de ses retouches
  abîment le texte**, parce qu'il n'exige ni frontière de mot avant le verbe, ni
  incise encadrée ou terminale, et qu'il ignore la casse. Dégâts réels :
  « répondit le jeune homme » → « jeune homme » supprimé ; « reprit la jeune
  fille » → sens faux ; « dit Morrel vous qui… » (incise non fermée) supprimée
  quand même. **À ne surtout pas reprendre tel quel.**
  *Ce qui serait prudent* : n'accepter que les incises **fermées** (virgule après
  le nom) ou **terminales**, refuser celles suivies d'un complément (« , dit-il en
  souriant, » — il resterait « en souriant » tout seul), exiger une frontière de
  mot avant le verbe, respecter la casse. Le réglage se ferait dans
  `_clean_text` : **aucun impact** sur la base, la page, le découpage ou les voix.
  *À faire avant de décider* : l'**écouter**. Le banc d'écoute de l'item suivant
  portera les deux variantes (ponctuation **et** incises gardées/supprimées) en
  même temps, sur les mêmes phrases.
  *Écoute faite le 18/09/2026 — deux remarques de Laurent, expliquées* :
  (1) `I_1_I2` (« Oui, fit-il. » sans incise) sort un « ouiiiii » : c'est une
  phrase de **6 caractères**, et le banc envoie les phrases **sans contexte** —
  dans la lecture, le **contexte glissant** évite justement ce démarrage à
  froid (mesure du 17/09/2026, BACKLOG) ;
  (2) `I_6_I2` prononce « mleu » pour « Mlle » : ce n'est **pas** un défaut du
  livre, c'est un **artefact du banc**, qui envoie le texte **brut**. Le tome 5
  écrit `Mlle\xa0Eugénie` (espace **insécable**, 72 cas mesurés par
  `test_voix/_mesurer_exclamations.py`) et la lecture **développe** l'abréviation
  avant l'envoi (`Mademoiselle`), ce que verrouille désormais
  `test_voix/test_nettoyage_tts.py`.

- [x] **Banc d'écoute : quelle ponctuation remplacer le « ! » ?** — livré le
  **18/09/2026**, **tranché par Laurent à l'oreille** le soir même.
  *Sa réponse, phrase par phrase (le lot `ecoute_ponctuation_20260918_1937`)* :
  virgule en tête pour « Oh ! », « — Oh ! », « « Comte ! » et « quel poignet ! »
  (à égalité avec « rien du tout » sur celle-là) ; **point** en tête pour
  « — Cela recommence, comte ! » (égalité point/virgule sur la phrase longue).
  La **suspension** n'a jamais été choisie.
  *Réglage retenu* : le `!` devient une **VIRGULE** dans les phrases **courtes**
  (interjections) et reste un **POINT** dans les phrases **entières** — seuil
  **25 caractères** (`SEUIL_INTERJECTION`, `modules/tts.py`). Répartition
  mesurée sur le tome 5 : **65 %** des 934 phrases exclamatives sont courtes
  (donc virgule), **35 %** entières (donc point).
  Demande de Laurent (18/09/2026). Le `!` est retiré depuis aujourd'hui (il fait
  monter la voix), mais le **point** n'est peut-être pas le meilleur choix : à
  comparer à l'oreille, sur des phrases réelles du livre, entre le **point**, la
  **virgule**, le **point de suspension** et la **suppression pure**.
  *Objectif précisé par le retour d'oreille du 18/09 au soir* : les
  interjections (« Oh », « Ah », « Eh ») sont **nettement mieux** mais il reste
  une **traîne** ; le banc doit chercher la ponctuation qui la raccourcit le
  plus, pas seulement celle qui évite la montée de hauteur.
  **Lot fabriqué le 18/09/2026** : `LANCER_BANC_PONCTUATION.bat` (double-clic,
  Kyutai allumé) fabrique un dossier `test_voix/ecoute_ponctuation_<date>/` avec
  **36 fichiers** : 6 phrases réelles du tome 5 × les 4 ponctuations
  (`P_n_P1`…`P_n_P4`), plus 6 phrases à incise × 2 (`I_n_I1` gardée, `I_n_I2`
  retirée), un `index.txt` qui dit quoi noter, et `variantes.txt` qui garde le
  texte exact envoyé au moteur.
  *Premier repère mesuré (durée de « Oh ! » sur une voix Kyutai)* :
  point **0,72 s** / virgule **0,56 s** / suspension **0,88 s** / rien **0,80 s**.
  La **virgule** est la plus courte et la **suspension** la plus longue, mais
  c'est la **traîne** perçue qui tranchera, pas la durée.
  *Vérification des briques* : `test_voix/test_ponctuation_incises.py`
  (**16 contrôles**) : les 4 ponctuations sont bien produites, et le retrait
  d'incise ne touche **jamais** une incise suivie d'un complément, ni une incise
  non fermée, ni le sujet de la phrase.
  *Attendu* : classement des 4 variantes par Laurent, phrase par phrase (voir
  `index.txt` du lot), puis réglage d'une seule ligne dans `modules/tts.py`.
  *Deuxième variante à porter dans le même banc* (idée de Laurent du même soir,
  voir l'item précédent) : **les incises gardées ou supprimées** (« — Il partit,
  dit-il. » vs « — Il partit. »). Un seul lot d'écoute pour les deux questions.
  L'atelier sait déjà fabriquer ce genre de lot (`_banc_large_point_final.py`,
  `_banc_contexte_kyutai.py` ont fait exactement ce travail pour le point final).
  Le réglage à changer tient en une ligne : `PONCTUATION_EXCLAMATION` dans
  `modules/tts.py`.

### Retours d'écoute du 18/09/2026 (une demi-journée d'écoute, 6 h)

- [x] **Les points d'exclamation sont retirés du texte envoyé au moteur** —
  livré le **18/09/2026**. Constat de Laurent : « Retirer les points
  d'exclamation ». Les moteurs neuronaux **jouent** ce signe comme une montée de
  hauteur : `Il partit !` sortait en « Il partiiiiit », et les interjections
  (`Oh !`) en « OOOOOOoooooh ».
  On ne touche **pas** au texte affiché : la phrase garde son `!` à l'écran, il
  ne disparaît que de ce qui part au moteur. Le `?` reste intact (`Quoi ?!` →
  `Quoi ?`), les suites (`!!`, `!!!`) sont ramenées à un seul signe, et l'espace
  typographique qui précède est retiré (sinon la voix ferait deux pauses).
  *Technique* : `modules/tts.py`. Depuis le banc d'écoute du 18/09/2026 au soir,
  ce ne sont plus « une ligne » mais **deux signes selon la longueur de la
  phrase** (`PONCTUATION_EXCLAMATION`, `PONCTUATION_EXCLAMATION_COURTE`,
  `SEUIL_INTERJECTION`) — voir l'item du banc, plus bas.
  *Vérification* : `test_voix/test_nettoyage_tts.py` (**27 contrôles**, sans moteur).
  *Retour d'oreille de Laurent (18/09/2026 au soir, après la séance)* : « les
  "Oh", "Ah", "Eh" sont nettement mieux. C'est bien pour une exclamation, ça
  traîne encore un peu, mais ça ne me choque pas. » — donc **validé**, avec une
  **traîne finale** à essayer de raccourcir : c'est justement l'objet du banc
  d'écoute de la ponctuation (item plus bas).

- [x] **Le silence après « M. » (lu monsieur) / « Mme » : cause trouvée,
  garde-fou posé** — livré le **18/09/2026**. Constat de Laurent : « les silences
  après les M. ou Mme […] comme s'ils héritaient du silence d'un point ».
  *Cause mesurée* (outil `test_voix/_diag_retours_ecoute.py`) : la **page**
  découpe les phrases **après le point d'une abréviation**, donc le moteur reçoit
  un morceau qui se termine par l'abréviation seule. Exemple réel du tome 5 de
  *Monte-Cristo* : `… le temps de complimenter M.` devient la phrase 1, et
  `de Morcerf ; il a fait preuve…` la phrase 2. Le nettoyage ajoutait alors un
  **point final** à la phrase 1 (« … complimenter Monsieur. »), c'est-à-dire une
  **vraie fin de phrase** avec sa respiration — le silence entendu.
  *Garde-fou livré* : plus de point final ajouté après `Monsieur`, `Madame`,
  `Messieurs`, `Mesdames`, `Mademoiselle(s)`, `Monseigneur`, `Docteur`,
  `Professeur`, `Saint(e)`, `numéro` (`MOTS_SANS_POINT_FINAL`, `modules/tts.py`).
  La phrase s'enchaîne donc directement à la suivante — le contexte glissant fait
  le reste.
  *Mesure* : **207 coupures** de ce type dans le seul tome 5 (21 chapitres
  touchés) : le défaut était fréquent, pas anecdotique.
  *Retour d'oreille de Laurent (18/09/2026 au soir)* : « les M. qui sont lus
  "monsieur" font une pause beaucoup plus petite maintenant » — **validé**, et
  d'autant mieux que les **sauts de ligne et les pauses de phrases** sont
  désormais trouvés corrects. La coupure en deux morceaux reste tout de même :
  c'est l'item suivant qui la fera disparaître.
  *Reste à faire* : le vrai correctif est de **ne plus couper après une
  abréviation** (item suivant).

- [x] **Ne plus couper les phrases après une abréviation — le vrai correctif** —
  livré le **18/09/2026**. C'était la suite de l'item précédent : le garde-fou
  supprimait le point final, mais la phrase restait **coupée en deux**.
  *Correction* : une **règle unique**, écrite une seule fois
  (`modules/decoupage.py`) et appelée par les **quatre** endroits qui
  découpaient chacun de leur côté — la page (`app.js`, `_buildSentences`), le
  casting (`voice_casting.py`), le re-cast (`main.py`) et la recherche
  (`main.py`). Une phrase n'est plus coupée après `M.`, `MM.`, `Mme`, `Mmes`,
  `Mlle(s)`, `Mgr`, `Dr`, `Pr`, `St`, `Ste` : le nom qui suit fait partie de la
  phrase.
  *Mesure* : **1 075 fusions** sur **107 101 phrases** (296 chapitres, 14 livres),
  dont **207 dans le seul tome 5** — soit 1 075 silences parasites en moins.
  *Le point délicat* : recoller les phrases **décale tous les index**, or la
  table `speaker_attribution` dit « qui parle » phrase par phrase, et
  `progress.cursor_idx` retient où le lecteur s'est arrêté. D'où une
  **migration** (`test_voix/_migrer_index_phrases.py`) : chaque nouvelle phrase
  étant la **réunion** d'anciennes, on retrouve la nouvelle par **comparaison de
  positions** (aucune devinette), on remappe, et on garde le locuteur de la
  phrase la plus longue quand deux locuteurs se retrouvent réunis.
  *Déroulé* : simulation d'abord (**0 attribution sans cible**, chiffres annoncés
  = chiffres écrits), copie datée de la base
  (`nimm_epub.db.bak_avant_migration_20260918` **et** une copie horodatée
  automatique), puis écriture. **Contrôle après migration**
  (`--verifier`) : **106 026 attributions vérifiées, 0 hors bornes**.
  *À vérifier à l'oreille* : **28 fusions** réunissent deux phrases dont les
  locuteurs étaient différents (l'IA avait attribué les morceaux tronqués de
  deux façons) — le locuteur de la plus longue a été gardé, et les 28 cas sont
  listés par le script. À corriger au cas par cas dans la fenêtre du casting si
  l'écoute les fait entendre.
  *Vérification* : `test_voix/test_decoupage_phrases.py` (**19 contrôles**, dont
  la comparaison entre la règle de la page et celle du serveur).


- [x] **Babil du moteur XTTS sur les phrases courtes — corrigé** — livré le
  **16/09/2026**. Constat de Laurent (chapitre 2 du *Chevalier Errant*) : après
  une réplique de l'aubergiste, près de **4 secondes** de bouillie
  inintelligible. Le texte envoyé au moteur était **propre** : la cause est le
  moteur lui-même, **auto-régressif**, qui sur un texte court n'a pas assez de
  matière pour s'arrêter et **continue d'inventer**.
  *Mesures* : « Que préférez-vous ? » (19 car.) rendait **9,11 s** au lieu de
  ~1,4 s ; « — Manger ? » (10 car.) 8,49 s ; « Elles sont toutes à Sorbier. »
  (28 car.) 6,27 s. Les 3 seules phrases fautives du livre sont les plus
  **courtes**, et le balayage des **8 autres livres castés** ne trouve **rien** :
  c'est propre au **clonage XTTS**, jamais aux autres moteurs.
  *Correction* : bornage de la génération d'après le texte (`max_new_tokens` :
  19 car. → 3,04 s, 250 car. → 32,7 s) + rognage de secours. Les phrases de
  longueur normale ne sont jamais contraintes.
  *Technique* : `xtts_service/servir_xtts.py` (`duree_max_morceau`,
  `tokens_max_morceau`, `rogner_a_duree`, `_lire_un_morceau`).
  *Vérification* : `test_voix/test_borne_babil_xtts.py` (**16 contrôles**, sans
  charger le moteur) ; outils de diagnostic : `test_voix/_inspecter_phrase_xtts.py`
  (texte exact envoyé au moteur), `_tracer_phrase_cache.py` (fichier de cache
  et durée réelle), `_chercher_babil_cache.py` (balayage d'un livre, `--purger`).
  *Purge* : les 3 fichiers de cache fautifs ont été supprimés (copies d'écoute
  gardées dans `test_voix/ecoute_babil/`) — **le service XTTS doit être
  redémarré** pour appliquer la correction.
  **Suite le même jour — il restait « ce genre de bizarreries »** (2ᵉ constat de
  Laurent : une pause, puis un « babile » après `— Non.`). Mesure sur le moteur
  **en marche** (`test_voix/_mesurer_phrases_courtes.py`, qui demande de vraies
  synthèses au service) : `Non.` sort en 1,07 s dont **0,26 s de mot + 0,34 s de
  silence + 0,18 s de babil**, et `…pour la nuit ?` en 2,51 s dont un
  micro-résidu de 0,06 s après 0,36 s de silence. Le babil est donc **isolé par
  un silence franc** : un **second filet** le coupe **dans le silence**
  (`rogner_babil_apres_silence`, seuils `SEUIL_SILENCE_LONG_S = 0,30 s` et
  `RESIDU_MAX_S = 0,35 s`). Une phrase normale n'est jamais coupée : ses pauses
  internes font 0,04 s, et un long silence suivi d'une vraie suite de phrase
  (plus de 0,35 s) n'est pas touché. *Vérification* :
  `test_voix/test_rogner_babil_xtts.py` (**12 contrôles**, sans moteur, sur les
  motifs mesurés). *À savoir* : le moteur est **stochastique** — deux synthèses
  de la même phrase donnent des durées différentes (0,93 / 1,07 / 1,11 s
  observées pour `Non.`) : c'est ce qui justifie d'avoir **deux** filets.

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

- [x] **Préchargement « burst » au passage en arrière-plan** — **LIVRÉ le
  20/09/2026**. Mise en attente le 08/09/2026 en demandant **le test de Laurent
  d'abord** (« peut-être inutile si un navigateur gère déjà bien la lecture en
  arrière-plan »). **Le test est fait, et le verdict est net** (20/09/2026) :
  - **en onglet Chrome** (donc **pas** la PWA installée), **verrouiller le
    téléphone arrête la lecture immédiatement** ;
  - en laissant l'écran s'éteindre **tout seul**, ça tient bien mieux : le
    problème est donc le passage en **arrière-plan**, pas l'écran noir ;
  - « c'est aléatoire : parfois après quelques secondes, parfois ça tient
    longtemps » → **c'est exactement l'état de la réserve** au moment du
    verrouillage.
  *Ce qui a été fait* : quand `document.visibilityState` passe à `hidden` pendant
  une lecture, le plafond de la fenêtre de préchargement est **levé**
  (`PREFETCH_MAX_AHEAD_CHARS_BURST` = 400 000 caractères, soit tout le reste du
  chapitre) et le remplissage est **relancé tout de suite** (`_pumpCourant`).
  La réserve se remplit donc pendant que le réseau répond encore, et la lecture
  tient ensuite sur la mémoire. **Hors lecture, rien ne se déclenche.**
  *Vérification* : `test_voix/test_lecteur_media.js` (la réserve s'active en
  arrière-plan pendant une lecture, **pas** hors lecture, et le plafond levé est
  bien celui utilisé par les calculs). Fichier : `frontend/app.js`.
  ✅ **Verdict du 20/09/2026 au soir — et c'était le TÉLÉPHONE, pas l'application.**
  Le test est fait : avec Brave **installé** et sur « optimisée », la lecture
  s'arrêtait **~20 secondes** après le verrouillage ; passé à Batterie « **non
  restreinte** », elle tient (2 minutes et plus, même en quittant le lecteur). La
  réserve « à bloc » **n'était donc pas la cause du symptôme** — mais elle reste
  un **filet utile** (moins de dépendance au réseau en arrière-plan, et elle
  améliore la bascule de chapitre), donc elle est gardée. *Ce qui a été confirmé
  au passage* : la **notification de lecture** (couverture, titre, boutons)
  apparaît et s'ouvre en plein écran au tap — la Media Session fonctionne.
  *À faire par Laurent (5 minutes)* : verrouiller pendant 5 minutes pour
  confirmer sur la durée, et vérifier que la notification montre bien la
  **couverture** et la **barre de progression**.

- [x] **Lecteur intégré « façon Deezer » + lecteur système complet** — **livré le
  20/09/2026**. Demande de Laurent : « je vois bien un genre de lecteur en mode
  PWA, avec la barre de progression qui représente la phrase lue. Une petite
  modale qui ressemblerait à la lecture de Deezer. »
  1. **Le lecteur du SYSTÈME** (notification + écran verrouillé) est maintenant
     complet : **couverture du livre**, **barre de progression**
     (`setPositionState`, échelle = le chapitre), titre + auteur + **chapitre**,
     et les boutons ▶/⏸ · ⏮⏭ (chapitre) · ◀▶ (phrase) · ⏪⏩ (4 paragraphes) —
     soit **les mêmes pas que la barre du bas**. La position envoyée est
     **bornée et protégée** : un refus du système ne peut **jamais** casser la
     lecture (vérifié) ;
  2. **Le lecteur intégré** (`#lecteur-modal`) s'ouvre en tapant la **barre de
     progression** (qui porte un petit ⤢ pour l'annoncer), et affiche :
     couverture, titre, auteur, chapitre, **qui parle**, **la phrase en cours**,
     la barre de progression et le compteur (« 120 / 480 phrases · 25 % ») ;
  3. **Ses sept boutons sont des TÉLÉCOMMANDES** de la barre du bas : ils cliquent
     sur les vrais boutons (donc **aucune logique de navigation en double**) et
     partagent la même famille visuelle (flèches blanches sur marron foncé).
  *Vérifications* : **nouveau** `test_voix/test_lecteur_media.js` (barre du
  système bornée et jamais cassante, réserve « à bloc », les 7 télécommandes
  deux à deux, la porte d'entrée par la barre de progression, les 15 éléments de
  la fenêtre) ; `test_voix/test_ids_ecran.py` (§ 3 sexies) ; `test_js_syntax.py` ;
  et **les 15 tests JS** verts. Détails dans ARCHITECTURE.md.

- [x] **Les phrases sont collées en UN SEUL morceau (la modale reste affichée)** —
  **livré le 20/09/2026**. Demande de Laurent : « la modale disparait entre deux
  paragraphes, puisqu'il n'y a plus de voix […] c'est comme si j'avais une
  playlist de centaines de morceaux de quelques secondes, et entre chaque, elle
  disparaît. Est-ce qu'on peut la laisser affichée en permanence ? »
  *Ce qui a été fait* : le lecteur ne joue plus un fichier par phrase mais **un
  seul long morceau**, fabriqué **dans le navigateur** en recollant les WAV déjà
  téléchargés (`_collerWav`) : la **modale de lecture reste affichée** (comme pour
  une vidéo) et le son n'a plus de **micro-blanc** entre les phrases. La **pause
  entre paragraphes** est insérée en silence dans le morceau, la **surbrillance**
  suit grâce à des durées **calculées** (donc pas de dérive, le piège du
  15/09/2026), et la **barre du lecteur système avance en douceur** au lieu de
  sauter d'une phrase à l'autre.
  *Pourquoi c'est possible* : les fichiers sont des **WAV** — 399 sur 400 du
  cache sont en **24000 Hz mono 16 bits** (une voix Piper, en 22050 Hz, termine
  simplement le morceau). Le collage ne **copie rien** (`Blob.slice` pointe sur
  les données d'origine).
  *Filet* : si un format est inattendu, `_collerWav` renvoie `null` et la phrase
  est jouée seule, exactement comme avant.
  *Vérification* : **nouveau** `test_voix/test_collage_wav.js` (**20 contrôles**)
  — **et il a attrapé une vraie erreur au passage** : l'en-tête annonçait une
  taille minuscule (la lecture ne lit que 64 octets du fichier, et le garde-fou
  « fichier tronqué » en concluait 0,4 ms ✗), ce qui aurait rendu le morceau
  **inaudible** en production. Corrigé en transmettant la **taille réelle** du
  blob. Détails dans ARCHITECTURE.md (« Lire écran verrouillé »).

- [x] **Pause par le casque, et bouton de lecture qui dit la VÉRITÉ** — **livré le
  20/09/2026**. Demande de Laurent, le soir : « je voudrais pouvoir mettre pause
  avec le casque, et reprendre la lecture » + « souvent la lecture est arrêtée,
  mais le bouton affiche Pause ». **Les deux ont une seule cause** : quand Android
  met l'audio en pause **sans nous** (appel, autre application qui prend le son,
  système), **aucun événement de fin** n'est envoyé → le lecteur attendait pour
  toujours et `_ttsState` restait sur `'playing'` ✗ → le bouton mentait, et le
  **casque** envoyait « pause » au lieu de « play ».
  *Corrigé* : l'application **écoute son lecteur** (`audio.onpause`) et remet son
  état en phase : une pause **venue d'ailleurs** passe en « Pause » (à l'écran
  **et** sur le lecteur du système) et **rend la main** ; notre propre pause et la
  **fin naturelle** d'un morceau ne sont pas confondues avec une interruption.
  *Vérification* : **nouveau** `test_voix/test_pause_casque.js` (**8 contrôles**,
  faux élément audio) ; **18 tests JS** verts. Détails dans ARCHITECTURE.md.
  *Reste à confirmer par Laurent* : casque en pause → reprise ; et le bouton qui
  affiche le bon état après un appel téléphonique.

- [x] **Résidus de balises dans le texte lu (« M class="textsuperscript">lle »)** —
  **livré le 20/09/2026**. Trouvé par Laurent au chapitre 98 du Comte de
  Monte-Cristo (**Tome 5**), dans une phrase : « laissons **M
  `class="textsuperscript">`lle Danglars**… ». *Cause exacte*, vue dans le fichier
  EPUB lui-même : le livre a été converti à la va-vite et contient une balise
  cassée avec le « **>** » **échappé** → donc du **texte** pour le navigateur :
  `M<supu0003c span=""> class="textsuperscript"&gt;<span class="ecrm">lle</span>`.
  Le parseur n'était **pas** en faute (il recopiait le fichier ✗).
  *Corrigé* : `_html_to_text` retire ces morceaux-là ; le texte normal n'est jamais
  touché (tests sur guillemets français, tirets de dialogue, apostrophes,
  égalités, chevrons). Comme le texte est extrait **à la lecture**, la correction
  vaut pour **tous les livres** — **mais il faut redémarrer le lecteur** (correctif
  côté serveur).
  *Vérifications* : **nouveau** `test_voix/test_residus_html.py` (**11 contrôles**)
  et l'outil **nouveau** `test_voix/_chercher_residus_html.py`, qui parcourt les
  livres avec le **vrai parseur** : **379 documents, 13 livres, zéro résidu** après
  correction (il en avait trouvé **un seul**, dans `epub_split_019.xhtml` du
  Tome 5). Détails dans ARCHITECTURE.md.

- [ ] **Clignotement de la modale entre deux morceaux — à trancher** (20/09/2026).
  Après le collage, Laurent voit encore la **modale de lecture clignoter** quand un
  morceau se termine : les **premiers** morceaux d'un chapitre sont **courts** (on
  ne colle que ce qui est **déjà téléchargé** à cet instant), donc Android range la
  modale puis la ressort. Il l'a jugé **pas dramatique** (« je passerais par
  l'application ouverte »), mais l'option proposée reste ouverte : **faire attendre
  la réserve** quelques secondes (avec un plafond) avant de lancer un morceau —
  sauf le tout premier, pour que la lecture démarre tout de suite. Question posée
  à Laurent (fréquence des clignotements) : **en attente de sa réponse**.

- [x] **Bouton « Installer l'application » : seulement sur téléphone** —
  **livré le 20/09/2026**. Constat de Laurent : « elle s'affiche maintenant sur la
  version PC ». Le bouton n'apparaît plus que sur **téléphone / tablette**
  (`_appareilMobile`, fonction **pure** : Android, iPhone, iPad — et les iPad
  récents qui se déclarent comme un Mac, reconnus par le toucher + le petit
  écran), et toujours pas quand l'application tourne déjà installée.
  *Vérification* : `test_voix/test_navigateur.js` (§ 1 bis : six appareils
  testés) et `test_voix/test_ids_ecran.py` (§ 3 septies).

- [x] **Installation de l'application : l'option manquait dans Chrome** —
  **livré le 20/09/2026**. Constat de Laurent : « j'ai essayé d'installer l'app
  sur Chrome mais je n'ai pas d'option pour. J'ai réussi avec NIMM (chatbot),
  mais pas NIMM ePub. J'arrive avec Brave et Firefox. »
  *Cause trouvée* : le manifeste déclarait **la même image 512×512** en
  `192x192`, `512x512` **et** `2048x2048`. **Chrome vérifie que la taille
  annoncée correspond au fichier** : il rejetait donc **toutes** les icônes — et
  sans icône valide de 192 px, il ne propose pas l'installation. (Brave est plus
  permissif ; « installer » avec Firefox Android n'est qu'un **raccourci**, pas
  une application.)
  *Corrigé* : **un fichier par taille** — `icon-192.png` (192×192),
  `icon-512.png` (512×512), `apple-touch-icon.png` (180×180) et
  `icon-maskable-512.png` (512×512 **avec marge de sécurité**, pour que le
  lanceur Android ne rogne pas le logo) — plus les `<link rel="icon">` dans la
  page, un `start_url` propre (`/`) et un `id`. Les icônes se **régénèrent** du
  logo maître (`frontend/image_NIMM_ePub.png`) avec
  `test_voix/_generer_icones_pwa.py --ecrire`.
  *Vérifications* : **nouveaux** `test_voix/test_pwa_manifeste.py` (**28
  contrôles** : le manifeste, **la taille réelle de chaque icône**, les critères
  d'installation de Chrome, le service worker) et
  `test_voix/_generer_icones_pwa.py` (aperçu, `--ecrire`, puis relecture
  « chaque icône déclarée = son fichier »).
  *Reste à faire par Laurent* : **réinstaller** l'application depuis Chrome
  (menu ⋮ → « Installer l'application », après un rechargement de la page), et
  pour ce qui touche à l'écran verrouillé, **préférer Chrome ou Brave** (Media
  Session complète + application installée). Détails dans ARCHITECTURE.md.
  **Complément du même jour** : un bouton **« 📲 Installer l'application »** dans
  la bibliothèque, parce que Chrome ne dit **jamais** *pourquoi* il refuse. Il
  déclenche la fenêtre d'installation du navigateur quand elle existe
  (`beforeinstallprompt`), **explique où chercher** sinon (Firefox, ou navigateur
  qui ne juge pas l'application installable), et **disparaît** quand
  l'application tourne déjà installée. *Vérification* :
  `test_voix/test_ids_ecran.py` (§ 3 septies, 8 contrôles).

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

- [x] **Voir et changer la voix d'une phrase (tap mobile + bouton PC)** — livré
  le **15/09/2026** (demande de Laurent). Sur **mobile**, un tap sur une phrase
  ouvrait la lecture à partir de là ; il ouvre désormais un **panneau « voix de
  cette phrase »** qui dit **qui parle** (personnage, ou *Narration*) et avec
  **quelle voix** (nommée comme partout : « Alphonse — 🇫🇷 France (XTTS) », avec
  vitesse et hauteur si elles ne sont pas neutres), et permet de **changer
  cette voix** — menu par groupes Femmes / Hommes / Autres + bouton
  **▶ Écouter** un aperçu de la phrase. **Le tap ne lance plus la lecture** ;
  lire à partir d'une phrase reste possible par **sélection longue** (bouton
  « Lire à partir d'ici »), qui n'a pas bougé. Sur **PC**, le tooltip de
  sélection gagne un second bouton **« 🎭 Voir la voix »**, qui ouvre le même
  panneau pour la phrase touchée par la sélection.
  *Effets à connaître* : changer la voix d'un personnage s'applique à
  **toutes ses phrases du livre** (c'est le casting, comme la fenêtre dédiée)
  et se propage aux autres tomes de la saga ; pour *Narration*, c'est la voix
  du lecteur qui change. Le changement **s'entend tout de suite** : la lecture
  en cours est relancée (même règle que le 15/09/2026 pour le casting).
  *Technique* : `frontend/app.js` — `_personnageDePhrase()`, `_fichePersonnage()`,
  `_voixDePhrase()`, `_remplirMenuVoixPhrase()`, `_openVoicePanel()`,
  `_closeVoicePanel()`, `_apercuVoixPhrase()` ; `_updateCharacterVoice()`
  renvoie désormais **`true`/`false`** (réussite de l'enregistrement) ; le
  panneau est **fermé au changement de chapitre**. `frontend/index.html`
  (`#voice-phrase-panel`, bouton du tooltip), `frontend/styles.css` (feuille en
  bas d'écran sur mobile, petite fenêtre centrée sur PC).
  *Vérification* : `test_voix/test_voix_phrase.js` (**24 contrôles** le
  15/09/2026 ; **34 depuis le 20/09/2026**, avec la porte vers le casting) :
  identifiants page/code, à qui appartient une phrase, quelle voix est utilisée,
  et que le menu **n'efface jamais** une voix en place.

- [x] **Panneau « Voir la voix » → une PORTE vers le casting** — **livré le
  20/09/2026**. Idée de Laurent, le jour même : « la modale qui s'ouvre via
  "Voir la voix" pourrait ouvrir directement "casting des voix" à la voix
  sélectionnée, non ? Cette modale est moins riche que "casting des voix". »
  *Ce qui a été décidé, et pourquoi* : on n'a **pas remplacé** le panneau par le
  casting, on lui a ajouté une **porte**. Trois raisons : (1) le panneau est le
  **seul** à savoir dire **QUI PARLE dans cette phrase** — le casting est par
  livre, pas par phrase ; (2) le geste fréquent (je lis, je tape, je change la
  voix) doit rester **léger**, alors que le casting est une grosse fenêtre
  (176 lignes, badges, saga, re-cast) qui ferait perdre la position de lecture ;
  (3) le saut vers une fiche **existait déjà** (`_allerAuPersonnage`, celui des
  noms cliquables du badge « partagée avec… »), donc la porte était presque
  gratuite.
  *Ce qu'elle fait* : un bouton **« 🎭 Ouvrir dans le casting »**
  (`#voice-phrase-cast-btn`) → ferme le panneau, ouvre la fenêtre du casting
  **sur le personnage**, surligné un instant. Trois garde-fous : **cachée pour
  la narration** (le narrateur n'a pas de ligne dans le casting : sa voix se
  change dans le menu du haut) ; **une seule fenêtre** à la fois (on ferme le
  panneau) ; et la porte **ramène toujours au personnage** — si un filtre d'état
  (« ⚠ à caster », « ⧉ voix partagée », « 🔓 voix libres ») ou la recherche le
  cachait, on revient d'abord à la liste complète, sinon la fenêtre s'ouvrirait
  sur une liste où il est invisible, **sans rien expliquer**.
  *Vérifications* : `test_voix/test_voix_phrase.js` (**34 contrôles**, dont 5
  pour la porte : bouton caché pour la narration, panneau fermé avant
  l'ouverture, filtres remis à zéro, surlignage) et `test_voix/test_ids_ecran.py`
  (l'identifiant du bouton est dans la page **et** dans le code). Détails dans
  ARCHITECTURE.md.
  *Reste possible* (option B discutée le 20/09/2026, **écartée par Laurent** le
  même jour : « pas de curseurs, le raccourci pour les besoins plus poussés, on
  laisse comme ça ») : ajouter les curseurs **vitesse et hauteur** dans le
  panneau. C'est le seul manque du panneau, mais la porte vers le casting suffit.

- [x] **Icônes des moteurs + « 🔖 Onglets » à la même échelle** — **livré le
  20/09/2026**. Deux demandes de Laurent, le même jour.
  1. **Les ICÔNES des moteurs** : « trouver des icônes pour les moteurs,
     histoire d'avoir un visuel sur les moteurs plutôt que les noms ». Une
     **seule table** (`FAMILLES_VOIX`, `app.js`) porte maintenant, pour chaque
     moteur, son libellé **et** son icône : ☁️ Edge (le seul **en ligne**),
     🎎 Kokoro (modèle **japonais**), 🎶 Piper (le **joueur de flûte**), ⚡
     Kyutai (le moteur **local** rapide), 🧬 XTTS v2 (le moteur de **clonage**),
     🧪 NeuTTS (le plus **récent**). Aucune marque ni logo sous licence : des
     repères choisis pour dire quelque chose du moteur, et **changeables en une
     ligne**. Où : le **libellé d'une voix** montre l'icône **seule** (« ♀️ Eva
     🇫🇷🇩🇪 adulte médium — 🎎 »), parce que c'est là que le nom prenait la
     moitié de la ligne (menus étroits du casting) ; partout où il y a la place,
     le nom reste, précédé de son icône (ligne d'une voix dans « 🎧 Écouter les
     voix », en-tête de groupe du tiroir des voix libres, menu de filtre,
     fenêtre de choix du moteur, bouton des moteurs).
     **Bonus trouvé au passage** : la liste de filtre des moteurs **n'avait pas
     NeuTTS**, alors que ses voix sont bien proposées → ajouté.
  2. **« 🔖 Onglets » à la même échelle** : le bouton n'était pas dans la
     **règle de style commune** des boutons du lecteur — il gardait donc
     l'apparence native du navigateur (plus grand, fond plus clair) à côté de
     « 🎭 Voix multiples » et « 🎧 Écouter les voix ». Les trois partagent
     maintenant la **même règle** (`frontend/styles.css`), donc la même échelle.
  *Vérifications* : `test_voix/test_libelle_voix.js` (libellés **exacts** avec
  l'icône du moteur), `test_voix/test_tiroir_voix_libres.js` (en-têtes de groupe
  « 🎎 Kokoro · 1 »), `test_voix/test_bouton_moteur.js` (le nom reste écrit dans
  le bouton — l'icône s'y ajoute) et `test_voix/test_ids_ecran.py` (les 6 icônes
  déclarées, l'icône seule dans le libellé d'une voix, la règle de style
  partagée par les trois boutons, NeuTTS filtrable). Détails dans
  ARCHITECTURE.md.

- [x] **Barre de navigation : quatre flèches symétriques, RSVP déplacé** —
  **livré le 20/09/2026**. Demande de Laurent : « J'ai 2 boutons "retour rapide"
  qui font la même chose. Si tu peux en retirer un, et mettre tous les boutons
  comme des icônes : [⏮️ Chapitre précédent][⏪ retour rapide][⏩ avance
  rapide][⏭️ Chapitre suivant]. Une couleur qui corresponde au thème général, un
  genre de marron foncé, flèches blanches. »
  *Ce qui a été fait* : la barre est **symétrique** —
  `[⏮ chapitre préc.] [⏪ phrase préc.] [▶️/⏸] [⏩ phrase suiv.] [⏭ chapitre
  suiv.]` — et les **quatre flèches sont des SVG** (dessinées), en **blanc sur
  fond marron foncé** (variables `--nav-btn`, `--nav-btn-survol`,
  `--nav-btn-bord`, dérivées de l'or du thème).
  *Pourquoi des SVG* : **un emoji ne peut pas être blanc** — il garde ses
  couleurs, ou s'affiche en petit noir et blanc selon le clavier : c'est ce qui
  faisait **deux familles de boutons** dans la même barre (chevrons dessinés pour
  les chapitres, emojis ⏮⏪⏭ pour les phrases).
  ⚠️ **La première version, livrée le matin, avait SUPPRIMÉ les sauts de
  paragraphe** (le pas de la barre était la phrase). **Laurent a corrigé le tir
  dans la journée** : « le saut de paragraphe correspond très souvent à un saut
  de phrase », donc un saut d'**un** paragraphe ne se distinguait pas d'un saut
  de phrase — il propose **trois niveaux**, et c'est mieux. **Version finale** :
  **⏮/⏭ le chapitre** · **⏪/⏩ le saut MOYEN = `_PAS_PARAGRAPHES` (4)
  paragraphes d'un coup**, constante ajustable **en une ligne** ·
  **◀/▶ la phrase** (le pas fin). Les sauts sont **bornés** : jamais au-delà du
  dernier paragraphe (le saut y est ramené), jamais avant le début du chapitre.
  (Le casque et l'écran verrouillé sont sur la phrase :
  `previoustrack`/`nexttrack` de `navigator.mediaSession` = les flèches ◀/▶ ✔.)
  *Et* : le mode **RSVP** quitte la barre de navigation (c'est un **mode**, pas
  une flèche) et rejoint la ligne des boutons d'action, sous le nom
  **« 👀 Lecture Rapide »**.
  *Vérifications* : **nouveau** `test_voix/test_sauts_navigation.js` (**les trois
  niveaux** : le pas lu dans `app.js`, le chapitre, les 4 paragraphes, la phrase,
  et **les bords** — jamais au-delà du dernier paragraphe, jamais avant le
  début) ; `test_voix/test_ids_ecran.py` (les 6 flèches présentes, la **même
  règle de style** pour les six, le resserrement sur téléphone, la disparition de
  `#tts-nav`, le RSVP **hors** de la barre, le bouton du cache sur la ligne des
  boutons d'action) ; **les 14 tests JS** verts ; `node --check frontend/app.js`.
  Détails dans ARCHITECTURE.md.

- [x] **Bibliothèque mobile : le titre du livre en entier sous la couverture**
  — livré le **15/09/2026** (demande de Laurent). Sur mobile, les couvertures
  restent **recadrées** au format 2/3 (la grille reste bien régulière) mais le
  **titre n'est plus coupé** : plus de limitation à deux lignes, taille un peu
  augmentée, et le nom de l'auteur passe à la ligne au lieu d'être tronqué.
  Comme le titre est rogné sur l'image de couverture elle-même, c'est ce texte
  qui dit de quel livre il s'agit. *Technique* : `frontend/styles.css`, règles
  mobiles `.book-title` / `.book-author` (`@media (max-width: 640px)`).

- [x] **Couvertures écrasées sur mobile dès que la bibliothèque est remplie**
  — livré le **16/09/2026** (constat de Laurent : « comme un jeu de cartes qu'on
  ferait glisser »). Avec assez de livres pour remplir plusieurs lignes de la
  grille (18 chez Laurent), le navigateur comprimait la hauteur des lignes :
  chaque vignette était réduite à une bande du tiers haut, largeur intacte, et
  les cartes se chevauchaient. Avec un ou deux livres, le phénomène était
  invisible. Les fichiers eux-mêmes étaient sains (18 couvertures valides en
  base et sur le disque, formats et dimensions normaux).
  *Technique* : `frontend/styles.css` — `#book-grid` reçoit
  **`grid-auto-rows: max-content`** : les lignes prennent la hauteur réelle de
  leur contenu, au lieu de la hauteur minimale d'une carte (vue comme nulle,
  la vignette ayant un ratio 2/3 qui dépend de la largeur de sa colonne).
  *Vérification* : `test_voix/test_couverture_mobile.py` (Playwright, sans
  serveur ni données : injecte le vrai `styles.css`, 12 livres, texte normal
  puis agrandi) — avant correctif 12/12 cartes écrasées, après 0/12.

- [x] **Barre de lecture : suppression du bouton ⏩ (phrase suivante)** — livré le
  **15/09/2026** (demande de Laurent : il faisait doublon avec ⏭, le paragraphe
  suivant — dans un dialogue, un paragraphe fait souvent une seule phrase).
  Les commandes du **casque et de l'écran verrouillé** (`navigator.mediaSession`,
  action `nexttrack`) continuent d'avancer **d'une phrase** : elles appellent
  directement `_cursorSentNext()` au lieu de cliquer sur le bouton retiré.
  **⏪ (phrase précédente) reste** : reculer d'une phrase reste utile quand ⏮
  saute tout le paragraphe. *Fichiers* : `frontend/index.html` (bouton retiré),
  `frontend/app.js` (MediaSession + listener du bouton), `frontend/styles.css`
  (règles du bouton).

- [x] **Barre de réglages du lecteur : boutons compacts et thème sombre
  cohérent** — livré le **15/09/2026** (demande de Laurent : « moins gros, plus
  esthétique »). Le bouton **« 🎧 Écouter les voix » n'avait aucun style** : il
  affichait l'apparence native du navigateur (fond clair, grande taille) au
  milieu du thème sombre — c'est lui qui « faisait blanc ». Les deux boutons
  (« 🎭 Voix multiples », libellé raccourci, et « 🎧 Écouter les voix »)
  partagent maintenant le **même look compact**, et les **deux menus** (voix du
  narrateur + vitesse) sont groupés dans `#settings-menus`, sur leur propre
  rangée : la voix prend la place restante, la vitesse sa taille naturelle.
  En complément, `color-scheme: dark` est déclaré dans `:root` : les **listes
  déroulantes** des menus (voix, casting, notes…) et les **barres de défilement**
  s'affichent en sombre au lieu de blanc.
  *Technique* : `frontend/index.html` (`#settings-menus`, libellés),
  `frontend/styles.css` (`:root`, `#reader-settings`, `#multivoice-btn`,
  `#voices-open-btn`, `#voice-select`, `#speed-select`), `frontend/app.js`
  (libellés du bouton multi-voix).
  *Vérification* : `node --check frontend/app.js` ; **tous** les identifiants
  utilisés par `app.js` existent encore dans la page (contrôle passé : 84/84) ;
  `test_voix/test_ids_ecran.py` et les autres tests JS → **tout OK**.


### Retours d'écoute du 19/09/2026 (chapitre 96, « Le contrat ») — les INCISES

Écoute du chapitre 96 du *Comte de Monte-Cristo* (tome 5, index 21). Verdict de
Laurent : « les incises ont énormément disparu déjà ; on affinera une prochaine
fois ». Ce qui reste se range en **trois causes distinctes**, chacune mesurée le
19/09/2026 par un nouvel outil (`test_voix/_mesurer_cas_tordus_20260919.py`,
lecture seule) sur les **5 105 phrases** du tome 5 :

- [x] **Le point-virgule ferme l'incise — LIVRÉ le 19/09/2026** — cause du
  « dit le comte » **lu** encore. Exemple réel écouté par Laurent : « Il n'y
  aurait cependant point de ma faute, **dit le comte** ; aussi je tiens à le
  constater. » La règle de retrait n'accepte que deux fins : une **virgule** ou
  la **fin de la phrase**. Un `;` n'est ni l'un ni l'autre → l'incise reste et
  est **lue**. Or `modules/incises.py` sait déjà que « le point-virgule est une
  frontière sûre » : il l'utilise dans `MOTIF_DECROCHAGE` pour emporter la
  relative, mais pas pour **fermer** l'incise.
  *Mesure* : **67 phrases** du tome 5 (1,3 %) ; **19** d'entre elles n'ont que
  ce cas (l'outil `_diag_incises_reelles.py` ne voit que celles-là, d'où l'écart
  apparent entre les deux outils — voir l'item « angle mort », plus bas).
  *Correctif envisagé* : accepter `;` (et à examiner `:`) comme borne de
  fermeture dans `_ferme_ou_terminal`. Risque faible. **Incrémenter
  `VERSION_CACHE`** (le texte envoyé au moteur change).
  ✅ **LIVRÉ le 19/09/2026.** Mesure à blanc d'abord (outil
  `test_voix/_mesurer_cas_tordus_20260919.py`, section « SIMULATION ») : **67
  phrases** touchées dans le tome 5, **aucune** ne perd tout son texte, mais
  **31** laisseraient une ponctuation orpheline en tête. Le correctif a donc deux
  volets : (1) `_ferme_ou_terminal` accepte un « ; » **immédiatement** après
  l'incise (jamais plus loin : la règle mesurée) ; (2) `retirer_incises` nettoie
  la ponctuation basse restée en tête (`lstrip` sur espace, `,;:.…`) — **jamais**
  le tiret de dialogue ni le guillemet ouvrant, qui sont légitimes.
  `VERSION_CACHE` passé de **10 à 11** (`modules/tts_cache.py`).
  *Vérifié après coup, sur le vrai texte* : incises gardées **151 → 84** (−67,
  exactement le chiffre annoncé) ; le cas « point-virgule » tombe à **0** ;
  l'incise seule (94), les civilités (4) et les phrases courtes (379) sont
  **inchangées** — le correctif fait ce qu'il annonçait, et rien d'autre.
  *Deux tests ont démenti une formulation trop étroite, et ont été REFORMULÉS
  (avec la raison écrite dedans, pour que la question ne revienne pas)* :
  - `test_nettoyage_tts.py` : le contrôle « le sujet de la phrase n'est jamais
    supprimé » exigeait que « jeune homme » RESTE dans « j'écoute, répondit le
    jeune homme ; parlez. ». Il avait été écrit **avant** que le module apprenne
    les noms communs avec article (« , dit le comte, ») et ne passait que **par
    accident** (le `;` n'était pas une fin reconnue). **Décision de Laurent le
    19/09/2026 : on retire** — c'est la même construction que « dit le comte ; ».
    Le contrôle est remplacé par trois : l'incise à nom commun + `;` est retirée,
    le point-virgule orphelin est nettoyé, et un mot piège (« maudit-il ») n'est
    pas pris pour une incise (ce dernier garde-fou n'était testé nulle part).
  - `test_ponctuation_incises.py` : même cas. Son commentaire expliquait le vrai
    danger — « le piège du code proposé ailleurs : “jeune homme” sortait TOUT
    SEUL » — donc le contrôle visait un **mot orphelin**, pas le retrait. Il
    vérifie maintenant cela précisément : jamais d'orphelin après le verbe, et la
    réplique garde ses deux morceaux. **Plus juste et plus fort qu'avant.**
  *Copies de sécurité* : `modules/incises.py.bak_avant_point_virgule_20260919`
  et `modules/tts_cache.py.bak_avant_point_virgule_20260919`.
  *Reste à faire* : le `:` (deux-points) n'est **pas** traité — à mesurer plus
  tard, séparément, comme prévu ci-dessus.

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

- [x] **Le cas « Danglars » : rien à changer** — vérifié le **19/09/2026**,
  Laurent avait raison de dire « c'est plutôt pas mal découpé, rien à changer ».
  Dans « Oh ! mon Dieu ! fit Danglars du même ton dont il aurait dit : Ma foi,
  la chose m'est bien indifférente ! », l'attribution (« fit Danglars ») n'est
  **pas** lue et la suite l'est : c'est exactement le comportement voulu.

- [x] **Les mots TOUT EN MAJUSCULES sont lus normalement — LIVRÉ le
  19/09/2026** — demande de Laurent : « les mots en majuscule donnent une
  prononciation bizarre, il faudrait modifier pour qu'ils soient lus
  normalement ». **Option B retenue** (le lecteur apprend le vocabulaire du
  livre), plus juste qu'une liste de sigles à tenir à la main.
  *Comment ça marche* : le serveur apprend **une fois par livre** les mots que
  ce livre écrit en **casse normale** (« de », « Bastille », « Jim ») — 0,8 s
  pour les 24 455 mots de 22/11/63, donc jamais d'attente à la lecture. Ensuite,
  avant l'envoi au moteur, tout mot **TOUT EN MAJUSCULES** qui est dans ce
  vocabulaire repasse en casse normale (`DE` → `de`, `BASTILLE` → `Bastille`,
  `JIM` → `Jim`). Ce qui n'y est pas — les **vrais sigles** (`JFK`, `FBI`,
  `DSK`, `TSBD`) — reste intact : le moteur les épelle, et c'est voulu.
  Les **chiffres romains** (`XIV`) et les lettres seules (`M.`) ne sont jamais
  touchés. Le **texte affiché ne change pas** : seul le texte parlé.
  *Technique* : nouveau module `modules/majuscules.py` (vocabulaire + réduction),
  `_clean_text(text, vocabulaire=None)` et les 7 fonctions de synthèse qui le
  transmettent, cache `_VOCABULAIRES` dans `main.py`, `book_id` ajouté à la
  requête TTS (envoyé par la page), `VERSION_CACHE` 13 → **14**.
  *Vérification* : **nouveau test** `test_voix/test_majuscules.py`
  (**16 contrôles**, dont 4 sur le vrai 22/11/63 : « LUI » et « DE » sont des
  mots du livre, « JFK » n'en est pas) ; les 10 tests Python et les 9 tests
  JavaScript sont au vert. *Reste à faire par Laurent* : **redémarrer le
  lecteur** puis écouter 22/11/63.
  *Limite connue, honnête* : un mot que le livre écrit **toujours** en
  majuscules (jamais autrement) ne peut pas être reconnu — il restera tel quel.
  Le cas est rare (les romans écrivent le même mot des deux façons), mais il
  existe.

  *Mesure dans TOUS ses livres* (outil
  `test_voix/_mesurer_majuscules_20260919.py --tous`) : les tomes de Monte-Cristo
  n'en ont **presque aucun** (4 à 5 phrases, des mentions légales : BIBEBOOK,
  ISBN, BY-SA) — en revanche **22/11/63 a 531 phrases** touchées (1 742
  occurrences, 873 mots distincts), Latude 188, Shantaram 145, « Souvenirs d'une
  gamine effrontée » 137, Dialogues 98, Notre-Dame 77, Le Chevalier Errant 6.
  *Deux familles bien distinctes* : des **mots de la langue mis en majuscules
  pour insister** (DE 67, LA 60, VOUS 30, MOI 45, LUI 36, ELLE 32, PAS 23,
  JAMAIS…) — ce sont eux qui sonnent mal ; et de **vrais sigles** (OK 113, FN 30,
  CIA 19, DSK 18, JFK 15, FBI 15, TSBD 15, KGB, PCF…) — que le moteur **épelle**,
  et c'est **voulu**.
  *Heuristique trouvée et MESURÉE le 19/09/2026* : un mot en majuscules est un mot
  de la langue s'il est écrit **aussi en casse normale ailleurs dans le même
  livre** (« DE » et « de », « JIM » et « Jim ») ; s'il n'apparaît **jamais**
  autrement, c'est un sigle. Essai sur 22/11/63 : **682 mots distincts
  convertibles (1 423 occurrences)**, les sigles préservés, et le tri est juste
  sur les 30 mots les plus fréquents (23 bons, les 7 autres étant de vrais
  sigles). ⚠️ Piège évité : il faut compter « Jim » (majuscule initiale) comme
  casse normale, **pas** seulement les mots tout en minuscules — sinon « JIM »
  était classé sigle à tort.
  *Deux façons de faire, à trancher par Laurent* :
  **(A) liste blanche de sigles** dans `modules/tts.py` (les ~35 sigles relevés
  dans ses livres) et conversion de tout le reste — simple, tout de suite, aucun
  changement d'architecture, liste à compléter au besoin ;
  **(B) vocabulaire du livre** — le serveur apprend les mots du livre au fil des
  chapitres servis et ne convertit que ceux qu'il connaît : plus juste, mais il
  faut transmettre ce vocabulaire au nettoyage (architecture), et le comportement
  s'améliore au fil de la lecture.
  *Dans les deux cas* : le texte **affiché** ne change pas (seul le texte parlé),
  les **chiffres romains** (XIV…) ne sont pas touchés, et la règle s'appliquera à
  **tous les moteurs** (le nettoyage est commun).

- [x] **Des ONGLETS : marquer un passage et le retrouver — LIVRÉ le
  19/09/2026** — demande de Laurent : « actuellement si je vais à un endroit du
  livre, l'endroit est le dernier visité, mais j'aimerais bien pouvoir me faire
  une liste d'onglets ». **La reprise de lecture ne change pas** : les onglets
  viennent EN PLUS.
  *Ce qui existe maintenant* : un bouton **« 🔖 Onglets »** dans la barre du
  lecteur ouvre un panneau (même style que la liste des chapitres) ; dedans, un
  bouton **« 🔖 Marquer cet endroit »** pose une marque à l'endroit exact où on
  lit, et la liste montre chaque onglet avec **son chapitre et le début de la
  phrase** (« Chapitre 22 — Il n'y aurait cependant… »). **Un clic ramène à
  l'endroit**, une croix supprime l'onglet (sans l'ouvrir). Chaque **profil** a
  les siens, chaque **livre** aussi.
  *Technique* : table `bookmarks` créée dans `init_db()` (main.py), 3 routes
  (`GET`/`POST /api/bookmarks/{book_id}`, `DELETE …/{bookmark_id}`), bouton et
  panneau dans `index.html`, styles **mutualisés** avec le panneau des chapitres
  (`styles.css`), logique dans `app.js` (`openBookmarksPanel`,
  `_marquerCetEndroit`, `_renderOnglets`, `_supprimerOnglet`). Le libellé est
  préparé par la page (chapitre + extrait de phrase).
  *Vérification* : **nouveau test** `test_voix/test_onglets.py` (**11
  contrôles** : création, contenu gardé, isolation par profil, suppression,
  ordre de lecture) ; `test_ids_ecran.py` confirme que tous les éléments de
  l'écran existent ; les 9 tests JavaScript sont au vert.
  ⚠️ **Piège noté pour la suite** : `TestClient` n'exécute **pas** le
  « lifespan » de l'application, donc pas de `init_db()` — un test qui touche
  une table doit appeler `main.init_db()` lui-même.
  🔎 **Leçon du premier essai de Laurent (19/09/2026 au soir)** : le panneau
  s'ouvrait mais la pose échouait (« Impossible de poser l'onglet »). **Cause
  trouvée en direct** : le serveur qui répondait était **l'ANCIEN**, lancé avant
  la livraison → `GET /api/bookmarks/16` renvoyait **404**. `START.bat` gère ce
  cas tout seul (il arrête le serveur déjà en marche et le dit :
  « on croirait que rien ne change »), et le message d'erreur de la page dit
  désormais **explicitement** « Le serveur doit être redémarré (fermer le
  lecteur, puis START.bat) » au lieu du vague « Impossible de poser l'onglet ».
  **Règle à retenir** : une modification dans `modules/` ou `main.py` demande un
  **redémarrage du lecteur** ; une modification dans `frontend/` demande un
  **rechargement de la page** (Ctrl+F5, à cause du service worker). Les deux
  souvent : redémarrer, puis Ctrl+F5.
  *État des lieux* : la base a déjà `progress` (user_id, book_id, chapter_index,
  scroll_position, cursor_idx, last_read — clé unique `(user_id, book_id)`) et les
  routes `GET`/`POST /api/progress/{book_id}`. Il faut donc une **table EN PLUS**,
  pas remplacer l'existante : `bookmarks` (id, user_id, book_id, chapter_index,
  cursor_idx, libellé, created_at).
  *À faire* : (1) `CREATE TABLE IF NOT EXISTS bookmarks` dans `init_db()`
  (main.py, à côté des autres) ; (2) trois routes — lister les onglets d'un livre,
  en ajouter un, en supprimer un ; (3) côté page : un bouton **« marquer cet
  endroit »** près des réglages du lecteur, et un panneau **« Mes onglets »** qui
  liste les marques (chapitre + un extrait de phrase pour reconnaître) et ramène
  au bon endroit au clic — **le même mécanisme que la reprise de lecture** et que
  le clic sur un résultat de recherche sont déjà en place.
  *Prévoir* : un libellé **automatique** (« chapitre 96 — Il n'y aurait… ») que
  Laurent pourra renommer s'il veut ; pas de limite au nombre d'onglets ; et
  l'onglet doit survivre au changement de profil (chaque utilisateur a les siens,
  comme `progress`).
  *À valider avant de coder* : l'ergonomie (où mettre le bouton, comment afficher
  la liste) — c'est du **niveau 3** (nouvelle table en base + écran).

- [x] **« MR. CURRIE » lu « MR[féè]. CURRIE » — corrigé** — livré le **21/09/2026**.
  Retour d'écoute de Laurent : « J'ai encore des bizarreries, avec le passage
  "MR. CURIE" (moteur Kyutai) lit : "Et l'étiquette sur son bureau indiquait
  MR[féè]. CURRIE" » (22/11/63 de Stephen King, chapitre 10 ; le vrai mot est
  **CURRIE**, avec deux R).
  *Cause, trouvée dans le texte réel* : le livre écrit « **MR.** » suivi d'une
  **espace insécable** puis « CURRIE » (une étiquette anglaise, traduite telle
  quelle). Or **`MR` en capitales n'était reconnu nulle part** :
  - le **découpage** coupait donc la phrase juste avant le nom → le moteur
    recevait un morceau finissant par « MR. », **seul devant trois lettres**, et
    il **inventait un son** (« [féè] ») ; le nom partait ensuite dans un second
    morceau de **six caractères** ;
  - le **nettoyage** ne développait pas « MR. » (les règles ne connaissaient que
    « Mr. » et « M. ») : le moteur ne lisait donc jamais « Monsieur ».
  *Corrigé aux trois endroits* : `ABREVIATIONS` (`modules/decoupage.py`) **et**
  sa copie de la page (`frontend/app.js`, que le test compare) reçoivent les
  formes **en capitales** (`MR`, `MME`, `MMES`, `MLLE`, `MLLES`, `MGR`, `DR`,
  `PR`), et `ABBREVIATION_RULES` (`modules/tts.py`) devient **insensible à la
  casse** pour ces civilités (`[Mm][Rr]` et non « Mr »). Résultat vérifié : la
  phrase redevient **une seule**, et le moteur reçoit « … indiquait **Monsieur**
  CURRIE. »
  *Effet de bord MESURÉ avant de garder la correction* : changer le découpage
  **déplace la numérotation des phrases**, donc le « qui parle »
  (`speaker_attribution.sentence_idx`). Balayage des **340 chapitres** des
  13 livres : **17 chapitres** concernés — **tous dans 22/11/63** (le chapitre 9
  pour « MR. CURRIE », seize autres pour « **Mrs** ») — et ce livre **est casté**.
  - **« Mrs » : la pause, mesurée AVANT de décider** (moteur Kyutai, la voix du
    narrateur de 22/11/63, une phrase réelle lue en quatre variantes) : tel quel
    **5,76 s**, **sans le point 5,84 s** (le point n'est donc **pas** coupable),
    écrit « Madame » 6,24 s, **coupé en deux morceaux 6,48 s** — le second
    morceau s'ouvrant sur **0,46 s de silence**. C'est la **coupure** qui crée la
    grande pause entendue : « Mrs » rejoint donc la liste, comme les capitales.
  - **La LECTURE de « Mrs » n'est PAS touchée**, et c'est un choix argumenté : en
    français « Mrs » = *Messieurs*, en anglais « Mrs » = *Misses* (Madame). Le
    scanner tranche pour **ses** livres (42 fois sur 42, toujours suivi d'un nom :
    *Mrs. Symonds*, *Starrett*, *Levesque*, *Bowie*, *Clayton*…), mais un livre
    qui mêlerait les deux usages ne peut pas être tranché automatiquement. Le
    moteur dit « Misses », ce qui lui convient, et le remède (« Madame ») reste
    **une ligne dans le nettoyage** — sans aucun effet sur les index.
  - **Migration faite le 21/09/2026** (son choix : « on y va »), avec un outil
    écrit pour l'occasion — `test_voix/_migrer_phrases_abreviations.py` : il
    compare la liste **privée des nouvelles formes** à l'état actuel, et non
    l'ancienne règle du 18/09, sinon il migrerait **deux fois**. Résultat :
    **42 fusions**, 13 023 → **12 981** lignes, **1 cas** à locuteurs mélangés
    (signalé : une réplique de Marnie Cullum réunie à de la narration — le
    locuteur le plus long est gardé), **1 position de lecture** recalée, et
    **vérification passée** (autant de lignes que de phrases, index uniques et
    dans les bornes). Copie de la base avant écriture :
    `data/nimm_epub.db.bak_avant_migration_abreviations_20260921_1822`.
  *Vérifications* : `test_voix/test_decoupage_phrases.py` (+4 cas : `MR.`,
  `Mr.`, `MME.` restent dans leur phrase) et `test_voix/test_nettoyage_tts.py`
  (+2 cas : `MR.` → « Monsieur », `MME.` → « Madame ») ; les tests voisins
  (`test_ids_ecran.py`, `test_majuscules.py`, `test_incise_seule.py`) au vert.

- [x] **Les syllabes inventées autour des prénoms : CORRIGÉ (étape 1)** — livré le
  **21/09/2026**. Retour d'écoute de Laurent : « les voix Kokoro ont certainement
  des balises qui font prononcer certains mots comme ceci (`enAndréafe`). Ça doit
  être `EN_Andréa_FR` qui est prononcé par Kokoro. C'est très présent sur les
  prénoms, mais sur certains mots également. »
  *Ce qui a été livré, en deux mécanismes* (`modules/prononciation.py` et
  `modules/tts.py`) :
  1. **Kokoro reçoit les PHONÈMES, plus le texte** (`is_phonemes=True`) : on
     phonémise nous-mêmes, puis on **retire les marques de langue**
     (`(en)ˈandɹiə(fr)`) qu'espeak-ng insère et que le tokenizer de
     kokoro-onnx **prononçait**. Fini les « én … fe », **partout** — y compris
     sur les mots que la table ne connaît pas ;
  2. **une table de prononciation** pour les mots que le phonémiseur revendique
     (Kokoro **et** Piper) : la phrase est réécrite pour la **lecture seule** —
     `Andrea → Andréa`, `Marthe → Marte`, `Arthur → Artur`, `Nathan → Natan`
     (les quatre **validés à l'oreille** le 20/09/2026), plus `Ethan → Étan`,
     `Maëlys → Maélis`, `Mathis → Matis`, `Noah → Noa` et `dos → dô`
     (proposés, **en attente de son oreille**). L'apostrophe courbe redevient
     droite au passage (« d’aujourd’hui » partait en anglais).
  *Mesure* (`test_voix/sortie_ecoute_prononciation/mesure_phonemes.txt`) : les
  neuf mots passent d'un son **anglais marqué** à un son **français**
  (`andrea : (en)ˈandɹiə(fr)` → `ɑ̃dʁeˈa` ; `dos : (en)dˈɒs(fr)` → `dˈoː`). Et
  dans le lot, la phrase entière **maigrit de 35 %** (368 Ko → 238 Ko) : c'est le
  temps des syllabes en trop qui disparaît.
  *Vérifications* : **31 contrôles** (`test_voix/test_prononciation_kokoro.py`),
  dont un **garde-fou de la table** — chaque graphie doit cesser de basculer en
  anglais **et** son mot d'origine doit basculer, sinon l'entrée ne sert à rien
  et le test le signale. `VERSION_CACHE` passe à **15** : les phrases déjà
  écoutées doivent être refaites (leçon du 17/09).
  **VERDICT D'OREILLE DE LAURENT, le 21/09/2026 : « tous les "après" sont ok.
  C'est parfait ! »** — les neuf entrées de la table sont donc **validées**, et
  la correction est **en service** (vérifié sur le lecteur en marche : la phrase
  d'exemple passe de 2,62 s à 2,18 s, et l'audio renvoyé est exactement le
  fichier « après » du lot).
  *Ce qui reste* : l'**étape 2** — le scanner qui parcourt un livre et propose la
  liste des mots à corriger (il existe côté NIMM Voix, à rapatrier) ; et, si un
  jour un mot résiste, l'ajouter à la table après l'avoir **mesuré et écouté**
  (le lot se regénère par `test_voix/ECOUTER_PRONONCIATION.bat`).

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

## 🟠 Priorité 2 — Voix & casting

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

- [x] **La vitesse réglée sur un personnage n'était JAMAIS appliquée — corrigé** —
  livré le **20/09/2026** (choix **A1** validé par Laurent ; **la règle a été
  révisée le soir même** — voir « RÉVISION DU MÊME JOUR » en fin d'item). Retour d'écoute de
  Laurent, le même jour : « il faudrait vider le cache d'une voix quand je change
  le pitch ou la vitesse, sinon il lit tout à la vitesse précédente. Ça n'a pas
  l'air de refaire le texte si un réglage a changé. »
  *Diagnostic — le cache était innocent* : la clé du cache contient bien la
  vitesse **et** la hauteur (`_hash_key(text, voice, rate, pitch)`), et
  `/api/tts` transmet les deux au moteur. Le défaut était dans la **playlist de
  lecture** : `_buildPlaylist()` mettait la **voix** et la **hauteur** dans
  chaque phrase, mais **pas la vitesse** ; `_runTTS` lisait celle du **menu du
  haut une seule fois** et l'appliquait à toutes les phrases. Les curseurs de
  vitesse de la fenêtre du casting s'enregistraient donc en base **sans aucun
  effet audible** — et comme la vitesse envoyée ne changeait pas, la clé de
  cache restait identique : le lecteur resservait le **même** audio (d'où
  l'impression que « le texte n'est pas refait »).
  *Mesure* (base lue en **LECTURE SEULE** le 20/09/2026) : **1 232 fiches**, dont
  **131** avec une vitesse réglée jamais entendue (de **−25 % à +20 %** :
  Carlini +20 %, Luigi Vampa +15 %, le père Dantès −25 %…) et **594** avec une
  hauteur — cette dernière **fonctionnait** déjà (le `pitch` était transmis).
  *Correction (**A1**)* : **la fiche du personnage remplace le menu pour ce
  personnage** ; le menu du haut reste le réglage général de la lecture (et
  celui du narrateur). Garde-fou ajouté : **le neutre ne compte pas** — une
  fiche à `+0%` (**1 101** personnages) rend `null` et suit le menu ; sans cela,
  le menu « Lente » n'aurait plus ralenti **aucun** dialogue (on aurait
  remplacé un défaut par un autre).
  *Fichiers touchés* : `frontend/app.js` (nouvelle fonction **pure**
  `_vitesseDeFiche()`, `_voiceForSentence()`, `_buildPlaylist()`,
  `launchFetch()`), `frontend/index.html` (`?v=20260920-16`),
  `test_voix/test_vitesse_personnage.js` (**nouveau**, 23 contrôles),
  `test_voix/LIRE_MOI.md`.
  *Vérifications* : les **19 tests JavaScript** de l'atelier passent (le nouveau
  compris), `node --check` sur `app.js`, `test_ids_ecran.py`,
  `test_import_main.py`, `test_lire_moi.py`, `test_js_syntax.py`,
  `test_js_parse.py` : OK.
  *Sauvegardes* : `frontend/app.js`, `frontend/index.html`, `BACKLOG.md` et
  `ARCHITECTURE.md`, en `.bak_avant_vitesse_personnage_20260920`.
  *Ce que Laurent doit voir* : dans la fenêtre du casting, régler la vitesse d'un
  personnage s'entend **tout de suite** (la lecture repart de la phrase en
  cours, mécanisme du 15/09) ; les personnages dont le curseur n'a jamais été
  touché suivent toujours le **menu du haut**, comme la narration.
  *La hauteur n'a pas changé* : elle était déjà transmise, avec un effet
  volontairement discret (curseur de ±20 Hz à **8 Hz par demi-ton** → **±2,5
  demi-tons** au maximum). L'élargir serait un **autre** item, non demandé.
  *Reste ouvert* : la vitesse du **menu du haut** ne s'entend qu'à la reprise
  d'une lecture (son gestionnaire ne relance rien, et la fenêtre de
  préchargement garde l'ancienne vitesse) — petit correctif possible, non
  demandé à ce jour.

  **RÉVISION DU MÊME JOUR (soir) — la règle se simplifie.** Laurent précise sa
  pensée : « je voulais que le narrateur, celui du menu, ait son propre tempo.
  Tout est lu à vitesse normale, sauf pour ceux ayant un réglage de vitesse. Le
  narrateur a son réglage dans le menu. » Autrement dit : **le menu du bas n'est
  pas un réglage général — c'est celui du NARRATEUR.**
  *Ce qui change par rapport à la livraison du matin* : un personnage qui a une
  voix dédiée mais **aucun** réglage de vitesse lit désormais à **« Normale »**
  (constante `PERSONNAGE_RATE_DEFAUT`, `+0%`) et **non** à la vitesse du menu ;
  le menu **ne touche plus aux dialogues**. Le **récit** et les **petits rôles**
  (lus par le narrateur) gardent, eux, la vitesse du menu — ce sont eux qui ont
  le tempo du narrateur. Motif de Laurent pour les petits rôles : « fais au plus
  simple » — il prévoit de leur donner bientôt des **voix génériques** (une voix
  homme et une voix femme réservées à cet usage, pas encore choisies).
  *Conséquence à connaître* : mettre le menu sur « Très rapide » accélère le
  **récit**, pas les dialogues — pour accélérer un personnage, c'est son curseur
  dans la fenêtre du casting qu'il faut bouger.
  *Piste abandonnée le même jour* : la vitesse du narrateur **par livre**
  (colonne `books.narrator_rate`, proposée puis écartée par Laurent) n'est
  **pas** retenue — le menu reste un réglage **global**. Donc **aucune écriture
  en base, aucune colonne ajoutée, pas de copie de base nécessaire**.
  *Fichiers touchés (révision)* : `frontend/app.js` (constante
  `PERSONNAGE_RATE_DEFAUT`, `_voiceForSentence`, commentaires de la playlist et
  de `launchFetch`), `frontend/index.html` (`?v=20260920-17`),
  `test_voix/test_vitesse_personnage.js` (**27 contrôles** — dont « menu sur
  Lente : le personnage sans réglage reste à Normale »), `test_voix/LIRE_MOI.md`.
  *Sauvegardes (révision)* : `.bak_avant_menu_narrateur_20260920` pour
  `frontend/app.js`, `frontend/index.html`, `BACKLOG.md`, `ARCHITECTURE.md`,
  `test_voix/LIRE_MOI.md` et `test_voix/test_vitesse_personnage.js`.
  *Ce que Laurent doit voir* : le casting fonctionne comme avant (les 131 fiches
  réglées s'entendent enfin), **plus** : le menu du bas ne change que le
  **narrateur**, et les dialogues non réglés restent à vitesse normale.
  *Effet à connaître* : si le menu était sur « Rapide » ou « Lente », les
  phrases des personnages non réglés reviennent à Normale — la vitesse entrant
  dans la clé du cache, elles **se régénèrent une fois**.
  **✅ VALIDÉ À L'OREILLE par Laurent le 20/09/2026** (« Testé et validé. ») :
  les personnages réglés s'entendent enfin, et le menu du bas ne change plus que
  le **narrateur**. L'item est **clos** de bout en bout — reste seulement, si le
  besoin revient, le petit correctif « menu du bas pendant une lecture ».


- [x] **La voix du NARRATEUR passe d'un livre à l'autre — chaque livre doit garder
  la sienne** — **LIVRÉ le 20/09/2026** (correction **A + B**, validée par Laurent
  le même jour). Constat de Laurent, **20/09/2026** : « la voix narrateur passe
  d'un livre à l'autre, alors que le narrateur du livre A devrait rester sur son
  livre, et si je choisis un narrateur B pour un autre livre, il devrait rester
  enregistré. En gros, chaque livre devrait avoir son narrateur, pas un même
  narrateur qui passe de livre en livre. »
  *Ce qui existe déjà* (livré le 17/09/2026) : la voix du narrateur est bien
  **par livre** en base — colonne `books.narrator_voice`, route
  `PUT /api/books/{id}/narrator`, restauration au chargement du livre par
  `_restaurerVoixNarrateur()` (`frontend/app.js`). Le défaut n'est donc pas un
  manque : c'est un **trou dans la chaîne**.
  *Cause trouvée le 20/09/2026* (LECTURE SEULE de `data/nimm_epub.db`, rien
  modifié) : **10 livres sur 14 n'ont AUCUNE valeur** dans `narrator_voice`
  (Tomes 1, 2, 3, 4 et 6 de Monte-Cristo, Marathoniens, Dialogues désaccordés,
  Latude, Shantaram, Notre-Dame de Paris). Les 4 qui en ont une : Tome 5
  (`fr-FR-DeniseNeural`), Gamine effrontée, 22/11/63 et Chevalier Errant (voix
  Kyutai). Or, à l'ouverture d'un livre **sans valeur**, la restauration ne fait
  **rien** — le garde-fou `if (!sel || !voix || sel.value === voix) return;`
  sort immédiatement — donc le menu `#voice-select` **garde la voix du livre
  précédent**, et la lecture part avec elle : c'est le narrateur qui « passe »
  d'un livre à l'autre. Et comme rien n'est écrit pour ce livre, le choix ne
  « reste » pas non plus.
  *Second défaut, même endroit* : si la voix enregistrée n'est **pas proposée**
  (moteur éteint), la restauration est **silencieuse** — un simple
  `console.warn('Voix du narrateur indisponible pour ce livre')`, invisible pour
  Laurent — et le menu garde la voix de l'autre livre sans que rien ne le dise.
  *Correction proposée (**niveau 3** : c'est le comportement de lecture)* :
  **(1)** à l'ouverture d'un livre **sans valeur enregistrée**, remettre le menu
  sur la voix de narration **par défaut** (Ariane) ; **(2)** **enregistrer** cette
  valeur pour le livre — chaque livre a alors SA voix, et elle le suit d'un
  appareil à l'autre ; **(3)** quand la voix enregistrée n'est pas disponible, le
  **dire** à l'écran au lieu de garder l'autre voix en silence.
  *À ne pas oublier dans la même session* : monter le `?v=` dans
  `frontend/index.html` (**règle de session** : `app.js` modifié → cache-busting,
  sinon le téléphone garde l'ancien code) ; **copie datée de `data/nimm_epub.db`**
  avant toute écriture ; le changement de voix ne s'applique qu'au **prochain
  chargement de chapitre** (comportement connu du lecteur).
  *Ce qui a été livré (**A + B**, validé par Laurent le 20/09/2026)* :
  **(1)** un livre sans voix enregistrée reçoit la voix **par défaut** (Ariane) **et
  cette valeur est écrite en base** — chaque livre a SA voix ; l'appel de
  restauration est passé **après** `_currentBookId = bookId` dans `openBook()`,
  sans quoi l'écriture aurait visé le livre précédent ; **(2)** une voix
  enregistrée **indisponible** (moteur éteint) fait lire au défaut **et le dit**
  dans une nouvelle ligne sous les menus (`#narrateur-etat`), **sans écraser le
  choix du livre** — il revient au rallumage.
  *Fichiers touchés* : `frontend/app.js` (bloc « voix du narrateur » réécrit :
  `NARRATEUR_VOIX_DEFAUT`, `_messageNarrateur`, `_enregistrerVoixNarrateur`,
  `_poserVoixNarrateur`, `_restaurerVoixNarrateur`), `frontend/index.html` (la
  ligne `#narrateur-etat`, et `?v=20260920-1` sur les deux fichiers),
  `frontend/styles.css` (style de la ligne),
  `test_voix/test_narrateur_par_livre.js` (nouveau), `test_voix/LIRE_MOI.md`.
  *Vérifications* : le nouveau test JS passe (**24 contrôles** — il exécute le
  **vrai** code de `app.js`, jamais une copie), les **10 autres tests JS** de
  l'atelier passent aussi, `test_ids_ecran.py` et `test_lire_moi.py` : OK.
  *Sauvegardes* : `data/nimm_epub.db`, `frontend/app.js`, `frontend/index.html` et
  `ARCHITECTURE.md`, en `.bak_avant_narrateur_par_livre_20260920`.
  *Ce que Laurent doit voir* : ouvrir un livre sans voix enregistrée → le menu
  repart sur **Ariane** (plus la voix du livre d'avant) ; choisir une voix, fermer,
  rouvrir → **elle est là** ; ouvrir un livre dont la voix est une voix Kyutai,
  moteur éteint → la **ligne d'explication** apparaît sous les menus, et la voix
  revient dès que le moteur est rallumé (aucun choix perdu).

### Retours d'écoute du 18/09/2026

- [x] **Voir les voix par THÈME, et non par moteur** — **traité le 20/09/2026 :
  PAS NÉCESSAIRE** (décision de Laurent : « idem pour les voix par thème, pas
  nécessaire »). L'item est **clos**, à rouvrir seulement si le besoin revient.
  Les deux manques « immédiats » qu'il portait ont été **livrés le même jour**
  (voir le récap en fin d'item) : les étiquettes des rubriques étaient déjà
  faites, l'échelle `tres_grave`/`tres_aigu` était en place depuis le 19/09.
  À savoir si le sujet revient un jour : les thèmes **existent déjà côté
  données** — ce sont les critères d'écoute (`CRITERES_VOIX`), et ils sont
  remplis (250 voix annotées sur 265). Ce qui manquerait serait seulement
  l'écran.
  *Historique de l'idée* : demande de
  Laurent (18/09/2026) : « améliorer l'affichage des voix, il faut que je voie
  plutôt par thèmes dans le style : voix grave/aiguë, âge, rapide, etc. ».
  *Bonne nouvelle* : les thèmes **existent déjà**, ce sont les critères d'écoute
  (`CRITERES_VOIX`, `main.py`) — âge (enfant / jeune / adulte / mûr / vieux),
  timbre (grave / médium / aigu / rocailleux / cristallin / voilé), débit (lent /
  posé / normal / vif), accent, registre, rôle réservé. Ils sont même **remplis** :
  250 voix sur 265 pour l'âge, le timbre et le débit (bilan
  `test_voix/_etat_annotations_voix.py`).
  *Ce qui manque est donc seulement l'ÉCRAN* : la fenêtre d'écoute des voix et
  celle du casting se lisent aujourd'hui **par moteur** (Edge, Kokoro, Piper,
  Kyutai, XTTS, NeuTTS) et par genre. Projet : des **boutons de thème** qui
  filtrent (femmes jeunes et aiguës, hommes mûrs et graves, voix vives, accents
  non neutres...) et un tri par thème, **les mêmes filtres dans les deux
  fenêtres**. Chantier frontend à découper avant de coder (l'écran d'écoute et
  l'écran de casting doivent partager la même logique — et le pool automatique du
  casting lit déjà ces critères).
  *Complément de Laurent, 19/09/2026* : « je continue d'annoter les voix, et il
  faudrait que je voie les rubriques (Âge : jeune, adulte, mûr, vieux ;
  Timbre : très aigu, aigu, moyenne, grave, très grave) ». Deux manques
  **distincts** :
  (1) **voir à quoi correspond chaque menu** : une fois une valeur choisie, la
  ligne affiche « adulte » ou « aigu » **sans dire de quelle rubrique il
  s'agit** — le libellé n'apparaît que sur un menu **vide**, en guise d'option
  (`app.js`, `_construireLigneVoix`). Correctif minimal et immédiat : une
  **étiquette visible devant chaque menu** (« Âge », « Timbre », « Débit »…).
  (2) **une échelle de hauteur** pour le timbre : Laurent demande
  **très aigu / aigu / moyenne / grave / très grave**, là où la liste actuelle
  mêle trois **hauteurs** (grave, médium, aigu) et trois **textures**
  (rocailleux, cristallin, voilé).
  ⚠️ **Ne pas remplacer, AJOUTER** : ces valeurs servent déjà (**250 voix
  annotées** : aigu 85, médium 81, grave 58, voilé 20, rocailleux 4,
  cristallin 2 ; âge : adulte 118, jeune 63, mûr 53, vieux 10, enfant 6).
  Ajouter `tres_aigu` et `tres_grave` ne perd rien ; remplacer rendrait
  **26 annotations orphelines** (voilé, rocailleux, cristallin). Décision de
  Laurent à prendre.
  ✅ **Avancé le 20/09/2026 — les deux manques « immédiats » sont traités, le
  chantier d'écran reste à faire.**
  (1) **Les rubriques sont maintenant ÉCRITES devant chaque menu** de critères
  (« Âge [– ] », « Timbre [grave] »…) : c'était le correctif minimal demandé, il
  est livré. Avant, le nom de la rubrique était porté par l'**option vide** du
  menu, donc il **disparaissait dès qu'une valeur était choisie**
  (`_construireLigneVoix`) : Laurent lisait « adulte » sans savoir à quoi ça
  répondait. Étiquette courte et **pure** (`_libelleCourtCritere`), libellé
  complet du serveur en **infobulle**, option vide devenue un **tiret** (comme
  les menus genre/étoiles), et l'étiquette est collée à son menu dans le même
  groupe (`.voice-critere-champ`) pour qu'un retour à la ligne sur téléphone ne
  les sépare jamais. Les libellés de `CRITERES_VOIX` ont reçu leurs **accents**
  au passage (« Âge perçu », « Débit », « Rôle réservé ») : **seuls les
  libellés** changent, aucune clé ni valeur ne bouge, donc **aucune annotation
  perdue**.
  (2) **L'échelle est DÉJÀ en place** : `tres_grave` et `tres_aigu` ont été
  **ajoutés le 19/09/2026** dans `CRITERES_VOIX`, en gardant les trois hauteurs
  et les trois textures d'origine. Il n'y a donc **rien à trancher** de ce côté.
  *Vérifications* : `test_voix/test_criteres_voix.js` (**25 contrôles** : les
  étiquettes exactes dans l'ordre du serveur, étiquette + menu dans le même
  groupe, tiret de l'état vide, et une **rubrique inconnue** qui affiche son
  libellé complet) et `test_voix/test_ids_ecran.py` (**104 contrôles**).
  *Ce qui reste* : l'écran « par thème » lui-même (boutons de thème, tri, les
  mêmes filtres dans les deux fenêtres) — **le plat de résistance**, à découper
  avant de coder. Détails dans ARCHITECTURE.md.

- [x] **Menus de voix : des DRAPEAUX et tes notes d'écoute — LIVRÉ le
  19/09/2026** — demande de Laurent : « retirer France, Espagne, Italie, etc. et
  ne laisser que les drapeaux ». Pour les voix Kokoro : « selon l'accent, plus ou moins
  prononcé, je pourrais mettre 2 drapeaux — un français et un deuxième pour
  l'accent. Les langues étrangères très prononcées, on laisse un seul drapeau. »
  *État mesuré le 19/09/2026* (23 libellés distincts, champ `region` de
  `modules/tts.py` et `main.py`) :
  - **12 voix Edge n'ont AUCUN code pays** : « France » (5), « Canada » (3),
    « Belgique » (2), « Suisse » (2) — incohérence à corriger d'abord ;
  - les autres nomment le pays **et** le moteur : « France (NeuTTS) » (109),
    « France (XTTS) » (74), « France (Kyutai) » (35), « France (NIMM Voix) »
    (30), « France (Piper) » (4), « France (Kokoro) » (1) ;
  - les accents XTTS sont écrits **dans le texte** : « France (XTTS) - accent
    allemand / anglais / canadien / paysan / espagnol-italien » ;
  - pays du timbre : États-Unis (20), Chine (8), Royaume-Uni (8), Japon (5),
    Inde-Hindi (4), Portugal/Brésil (3), Espagne (3), Italie (2).
  *Format demandé par Laurent, 19/09/2026 (sa réponse, à garder telle quelle)* :
  « [Prénom] [drapeau] [Âge] [Timbre] [Accent] [Moteur] » — ses exemples :
  `Alice 🇫🇷 Jeune aigu - Kyutai` et `Amélie 🇫🇷🇬🇧 Mûre grave - Kokoro`.
  *Ce qu'il voit aujourd'hui* (relevé par lui le 19/09/2026) :
  - Kokoro / Kyutai / Piper, modale du casting : `Prénom — 🇫🇷 France` ;
  - **Edge, PARTOUT : `Prénom — France`** — aucun drapeau : ce sont exactement
    les **12 voix sans code pays** relevées ci-dessus ;
  - menu de changement de voix d'un personnage :
    `Prénom — 🇫🇷 France (Kyutai)` ;
  - fenêtre « Écouter les voix » : `Prénom — 🇫🇷 France (Kyutai)`.
  ✅ **Les drapeaux s'affichent bien en IMAGE chez Laurent** (constaté le
  19/09/2026) : l'alerte « Windows affiche les drapeaux en deux lettres » ne
  s'applique **pas** à sa machine — ne plus s'en servir d'argument.
  *Règle des drapeaux validée par Laurent* : « je ne lis qu'en français de toute
  façon » → le **drapeau principal est toujours 🇫🇷**, et le **2ᵉ drapeau** est
  celui du pays du **timbre** (ou de l'**accent**) quand la voix vient d'ailleurs.
  Pas besoin d'une case « intensité de l'accent » : **2 drapeaux suffisent**.
  *Cas particuliers à trancher* : (1) « accent paysan » — ce n'est pas un pays ;
  (2) « accent espagnol/italien » — deux pays pour une seule voix ; (3) les voix
  Edge `fr-BE`, `fr-CA`, `fr-CH` (accent régional francophone : 🇫🇷🇧🇪, 🇫🇷🇨🇦,
  🇫🇷🇨🇭 ?) ; (4) les **voix sans âge ni timbre annotés** (que montre-t-on à la
  place ?).
  *Où sont les rubriques affichées* : l'**Âge** et le **Timbre** du libellé sont
  les **annotations d'écoute** (`data/annotations_voix.json`), pas les
  catalogues — la page les a déjà en mémoire (`_annotationsVoix`). ⚠️ Vérifier
  qu'elles sont chargées **avant** la construction des menus du casting (sinon
  les libellés seraient vides au premier affichage).
  ✅ **LIVRÉ le 19/09/2026.** Format en place dans les **deux** menus (celui du
  narrateur dans les réglages, et celui du casting) : `Prénom 🇫🇷[2ᵉ drapeau] âge
  timbre — Moteur`. Exemples réels : `Henri 🇫🇷 mûr grave — Edge (en ligne)`,
  `Aurore 🇫🇷🇬🇧 mûr voilé — Kokoro`, `Sylvie 🇫🇷🇨🇦 — Edge (en ligne)`.
  *Comment le 2ᵉ drapeau est choisi*, dans cet ordre : un drapeau **déjà écrit
  dans la région** (le plus précis : États-Unis, Japon), sinon un **accent nommé
  dans la région** (« France (XTTS) - accent allemand »), sinon un **pays écrit
  en clair** (France, Canada, Belgique, Suisse — les **12 voix Edge qui
  n'avaient aucun drapeau**), sinon l'**accent annoté par Laurent**. Le drapeau
  français est toujours devant et n'est jamais répété.
  *L'âge et le timbre* viennent des annotations d'écoute, affichés avec les
  **libellés du serveur** (« mûr », « très aigu »). Une voix pas encore annotée
  n'affiche rien de plus, le libellé reste propre. `loadVoices()` charge
  désormais les annotations **et** les critères : la modale du casting les a donc
  toujours sous la main (c'était le risque : des libellés vides au premier
  affichage).
  ⚠️ *Changement assumé, à valider par Laurent* : le **genre (F)/(M) a disparu**
  du libellé — le format demandé ne le prévoit pas et les menus du casting
  groupent déjà « Femmes » / « Hommes ». Si le repère manque dans le menu du
  narrateur, on le remettra.
  *Technique* : `frontend/app.js` (`_libelleVoix`, `_secondDrapeauDeVoix`,
  `_libelleCritere`, plus le libellé du menu du casting qui appelle maintenant la
  même fonction).
  *Étendu le 19/09/2026, après essai de Laurent* : le panneau **« Voix de cette
  phrase »** (menu « Voir la voix » depuis le casting, sur PC comme au tap sur
  mobile) gardait son **ancien** libellé (`_remplirMenuVoixPhrase`, ligne 3209).
  Demande de Laurent : « le même affichage que dans le menu Casting des voix ».
  Corrigé. Les notes d'écoute y sont disponibles **sans rien charger de plus** :
  `loadVoices()` est appelé au démarrage de la page (`app.js`, init ligne 116) et
  charge désormais annotations et critères ; et une annotation enregistrée met à
  jour `_annotationsVoix` en mémoire, donc le panneau suit immédiatement.
  ⚠️ Rappel : le **service worker** de la page met `app.js` en cache — après une
  modification, un simple F5 ne suffit pas toujours, il faut un **rechargement
  forcé** (Ctrl+F5) ou un vidage du cache.
  *Vérification* : **nouveau test** `test_voix/test_libelle_voix.js`
  (**11 contrôles** : voix Edge, accents région et annotés, libellés du serveur,
  valeur inconnue, espaces) ; `node --check frontend/app.js`,
  `test_voix/test_criteres_voix.js` et `test_voix/test_ids_ecran.py` → tout OK.
  *À faire par Laurent* : **redémarrer le lecteur**, recharger la page, et
  regarder ses deux menus.

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

- [x] **Timbre : « très grave » et « très aigu » ajoutés** — livré le
  **19/09/2026**, demande de Laurent : « juste ajouter le "très aigu\très grave"
  dans ce menu également ». Deux valeurs ajoutées à `CRITERES_VOIX`
  (`main.py`) : `tres_grave` et `tres_aigu`, **sans rien retirer** — les trois
  hauteurs (grave, médium, aigu) et les trois textures (rocailleux, cristallin,
  voilé) restent : **250 voix sont déjà annotées** avec, dont 26 en texture, et
  les retirer perdrait ces notes. La fenêtre « Écouter les voix » n'est pas
  touchée par ailleurs (décision de Laurent : « laisser comme il est pour le
  moment, on ajoutera/retirera des rubriques si nécessaire plus tard »).
  *Vérification* : `python -m py_compile main.py` et
  `test_voix/test_annotations_voix.py` (**tout OK**).
  *À faire par Laurent* : **redémarrer le lecteur** (`START.bat`) pour que les
  deux nouvelles valeurs apparaissent dans les menus.


  remarque de Laurent, 18/09/2026 au soir : « dans Librivox, il faut que je trouve
  des passages où le lecteur lit un dialogue. J'ai remarqué que des passages que
  j'ai pris sont des passages de "narrateur" […] Mais les passages qui contiennent
  des dialogues donnent une prosodie toute différente […] ça améliorera nettement
  l'effet "quelqu'un qui parle" plutôt que "quelqu'un qui lit". »
  *Mesuré le soir même* (nouvel outil `test_voix/_analyse_extraits_dialogue.py`,
  qui lit les transcriptions gardées dans
  `neutts_service/references/*/references.csv`) :
  - **CML-TTS** (les 35 voix Kyutai **et** les 25 CML-XTTS) : **13 extraits sur
    60 (22 %)** seulement portent un dialogue → **47 voix ont un extrait de pure
    narration** (Blanche, Diane, Éléonore, Augustin, Geneviève, Claude, Hélène,
    Damien, Edmond, Irène, Gaston, Hubert, Isidore, Julien, Victoire, Ninon,
    Léon, Odette, Marcel, Norbert, Monique, Quentin, Simon, et les `cml…`).
    C'est un chiffre **fiable** : le texte vient de la banque CML-TTS, ponctué.
  - **extraits libres de droits** (choisis à la main par Laurent) : 2 sur 19
    (11 %) — **plancher seulement** : leur texte vient d'une transcription
    automatique, qui ne met pas les guillemets de dialogue.
  - **voix Kokoro clonées** : 0 sur 30 — sans surprise : leur référence est un
    **texte de contrôle** (toujours le même), pas un extrait choisi.
  *À faire* : (1) quand un extrait est repris dans Librivox, **chercher les
  guillemets et les tirets** dans la page — c'est la marque du dialogue ;
  (2) vérifier l'effet par une écoute comparative (même voix, deux extraits :
  un dialogue et un récit). L'essai de clonage se fait dans **NIMM Voix** ; le
  résultat est à remonter ici.
  *Hypothèse, pas acquis* : Laurent dit « je pense que ça améliorera » — la
  mesure ci-dessus dit seulement ce que contiennent les extraits actuels, elle
  ne prouve pas encore l'effet sur la prosodie. À confirmer à l'oreille.

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


- [x] **Critères FIXES d'annotation des voix (listes déroulantes)** — livré le
  **16/09/2026** (demande de Laurent : « au lieu de noter, je sélectionne les
  catégories »). La fenêtre « Écouter les voix » gagne, sous chaque voix, une
  **seconde ligne de menus déroulants** : **âge perçu** (enfant / jeune /
  adulte / mûr / vieux), **timbre** (grave / médium / aigu / rocailleux /
  cristallin / voilé), **débit** (lent / posé / normal / vif), **accent**
  (neutre / paysan / canadien / anglais / allemand / espagnol / italien /
  autre), **registre** (noble / neutre / populaire / savant) et **rôle réservé**
  (narrateur / enfant / vieux / étranger / secondaire). Le genre H/F, les
  étoiles et la remarque libre restent à part ; un critère renseigné se voit
  (bordure accentuée).
  *But* : des annotations **calibrées**, lisibles par la machine — c'est la
  brique préalable à l'attribution assistée (item suivant).
  *Technique* : listes fermées dans `main.py` (`CRITERES_VOIX`, **seule source
  de vérité**, servies à la page par `GET /api/annotations_voix/criteres`) ;
  toute valeur hors liste est **refusée (400)** ; `frontend/app.js`
  (`_chargerCriteresVoix`, `_construireLigneVoix`, `_sauverAnnotationVoix`,
  `_majStyleCritere`) et `frontend/styles.css` (`.voice-criteres`).
  *Vérification* : `test_voix/test_criteres_voix.js` (**20 contrôles**, sans
  navigateur : il **lit les critères dans main.py** et vérifie que la page
  construit exactement ces menus et envoie exactement ces clés) et
  `test_voix/test_annotations_voix.py` (**29 contrôles**, annotations de
  Laurent sauvegardées puis restaurées). Les annotations d'avant (14/09) se
  relisent sans erreur. *Sauvegarde faite avant* :
  `data/annotations_voix.json.bak_avant_criteres_20260916`.

- [x] **Re-cast par critères (gratuit) — étape 1 de l'attribution assistée**
  — livré le **16/09/2026**. Le bouton « Re-caster » ne se contente plus des
  étoiles : il classe les voix selon les **annotations d'écoute** de Laurent
  (âge → timbre → étoiles → débit) et selon l'**âge réel** des personnages,
  puis attribue la première voix encore libre.
  *Gains constatés* (aperçu sur « Le Chevalier Errant », 59 personnages :
  **30 voix changeraient**) : Eustace Osgris (362 répliques, âgé) passe de Rémy
  à **Victor — vieux / grave / lent** ; Arlan de Pennytree (âgé) reçoit
  **Papi — vieux / voilé / lent** ; l'Œuf (jeune) quitte une voix **grave**
  d'ancien pour **Norbert — jeune** ; Rohanne Tyssier et Tanselle passent sur
  des voix féminines jeunes.
  *Règles* : aucune voix notée **0 étoile** n'est attribuée ; une voix dont le
  **rôle** est annoté est **réservée** (narrateur, étranger, secondaire : hors
  pool automatique), sauf « vieux » ou « enfant » quand l'âge correspond ;
  **verrous et voix figées de saga** restent prioritaires ; les petits rôles
  (< 8 répliques) gardent la voix vide (lus par le narrateur). **Registre et
  accent « paysan »** sont volontairement ignorés : trop peu renseignés
  (constat sur les 148 voix annotées).
  *Correction au passage* : l'ancien re-cast forçait l'âge **« adulte » en
  dur** pour tous les personnages ; il relit désormais la table `cast_fiche`.
  *Technique* : `modules/voice_casting.py` (`lire_annotations_voix`,
  `_index_voix`, `_voix_reservee`, `_classement_voix`, `AGES_PAR_PERSONNAGE`,
  `TIMBRES_ATTENDUS`, `DEBITS_ATTENDUS`, `assign_voices(par_criteres=True)`),
  `main.py` (`reassign_voices`, âge lu dans `cast_fiche`).
  *Vérification* : `test_voix/test_attribution_criteres.py` (**27 contrôles**,
  sans écriture en base) et `test_voix/_apercu_recaste_criteres.py` (aperçu
  avant/après, lecture seule).
  *Repli* : `?par_criteres=false` sur `/cast/reassign` redonne exactement
  l'ancien tri — pratique pour comparer les deux sur un même livre.

- [x] **Étape 2 — bouton « Re-caster avec l'IA »** (validé le 16/09/2026)
  — **livré le 16/09/2026 au soir**. À côté du re-cast gratuit, un second
  bouton « Re-caster avec l'IA » : l'IA **lit des répliques de chaque
  personnage** (20 premiers chapitres, 3 répliques chacun) et en déduit ce
  qu'aucune table ne contient — position sociale, registre de langue, parler
  étranger, tempérament — puis choisit la voix dont la **description d'écoute**
  correspond le mieux.
  *Garde-fous de conception* : l'IA ne choisit **jamais** dans tout le
  catalogue, seulement parmi les voix que le re-cast par critères autorise déjà
  (même genre, plus de 0 étoile, rôle réservé écarté) ; les **verrous** et les
  **voix figées de saga** sont respectés (même préparation partagée que le
  re-cast gratuit : `_preparer_recaste`) ; les **petits rôles**
  (< `MINOR_THRESHOLD` répliques) ne sont pas soumis à l'IA ; tout ce que l'IA
  rend d'inutilisable — voix inventée, mauvais genre, doublon, personnage
  inconnu — est **écarté en le disant**, et le personnage garde alors sa voix
  par critères. **Rien n'est écrit avant que la réponse n'ait été vérifiée.**
  *Coût* : « qui parle » n'est pas recalculé (aucun réabonnement) → quelques
  centimes, comme prévu.
  *Technique* : `modules/voice_casting.py` (`description_voix`,
  `voix_proposees_pour`, `construire_prompt_recaste_ia`,
  `lire_attributions_ia`, `attribuer_voix_avec_ia`) ; `main.py`
  (`/cast/reassign_ia`, `_preparer_recaste`, `_repliques_des_personnages`,
  `_decouper_phrases_du_chapitre`) ; `frontend/` (second bouton et fonction
  `_recasterAvecIA`).
  *Vérification* : `test_voix/test_recaste_ia.py` (**30 contrôles**, sans
  appeler l'IA : cadre, prompt, lecture et validation des réponses, découpage
  des phrases vérifié sur un vrai livre casté → **34/34 personnages** avec
  leurs répliques, 0 chapitre écarté).
  *Au passage* : les **109 voix NeuTTS** ont hérité des annotations d'écoute de
  leurs jumelles XTTS et Kokoro (`_heriter_annotations_xtts_vers_neutts.py`,
  accents remis à « neutre » — 257 voix annotées au total), sinon l'IA
  n'aurait eu aucune description à lire.
  *Reste possible plus tard* : la même attribution greffée sur la passe 2 du
  casting complet (coût quasi nul : la fiche y part déjà), et l'usage du
  **parler étranger** déduit par l'IA pour réserver les voix accentuées.

- [x] **Re-cast : la cohérence de SAGA est désormais préservée** — livré le
  **16/09/2026** (trouvé en préparant le re-cast de Monte-Cristo par Laurent, qui
  s'appuie sur son **tome 2** comme référence de la saga).
  *Le problème* : `_fetch_saga_voix_figees()` (les voix des autres tomes, le plus
  ancien ajouté faisant référence) n'était appelée que par le **casting complet**.
  Le **re-cast gratuit** ne reprenait que les **verrous du livre courant** :
  re-caster le tome 4 aurait donné à Monte-Cristo, Danglars ou Villefort une voix
  **différente** de celle de leur tome 2 — la saga partait en morceaux, alors que
  c'est justement ce que le projet protège depuis le 22/08/2026.
  *Correction* : `reassign_voices` reprend maintenant les voix des autres tomes,
  exactement comme le casting complet. Les **verrous locaux restent
  prioritaires** : un personnage verrouillé dans le livre re-casté n'est jamais
  écrasé par la fiche de saga (écriture en `setdefault`).
  *Vérification* : `test_voix/test_attribution_criteres.py` vérifie désormais que
  le re-cast appelle bien `_fetch_saga_voix_figees`.

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

- [x] **Barre de recherche dans la fenêtre du casting** — **LIVRÉ le
  20/09/2026** (récap en fin d'item). Demande de Laurent,
  14/09/2026. Sur un livre à 175 personnages, retrouver un nom à la main
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
  **LIVRÉ le 20/09/2026.** Un champ de saisie **en haut** de `#cast-modal`
  (`#cast-search`) filtre les lignes **pendant la frappe** : insensible aux
  accents et à la casse (« EDMOND » = « Edmond »), et **tirets, apostrophes et
  espaces se ressemblent** (« jean luc » trouve « Jean-Luc »).
  **La question laissée ouverte est tranchée** : oui, la recherche **révèle les
  alias** — un personnage trouvé garde ses variantes visibles, et taper un
  **alias** fait remonter **son** personnage (sans lui, la ligne d'alias
  s'afficherait seule, en retrait sous une fiche absente). Différence
  **volontaire** avec `normalize_character_name` : l'**article initial n'est pas
  retiré**, donc taper « le » filtre au lieu de s'évanouir. Un **compteur**
  écrit ce que la liste montre (« 3 personnages sur 176 »), une recherche sans
  résultat l'**écrit** au lieu de laisser un vide muet, et la recherche **se
  combine** avec le filtre d'état (« ⚠ À caster » **et** « edm ») comme avec le
  tiroir des **Voix libres** (où elle cherche le prénom d'une voix : la même
  barre ne doit pas avoir l'air morte dans cet onglet).
  *Deux détails de confort* : la frappe **n'appelle pas le serveur** (nouvel
  argument `listeSeule` de `_openCastModal`) et le texte tapé **survit aux
  reconstructions** de l'affichage (il est gardé dans `_castRecherche`), puis
  **remis à zéro à la fermeture** de la fenêtre.
  *Vérifications* : `test_voix/test_recherche_casting.js` (**33 contrôles**,
  sans navigateur), `test_voix/test_tiroir_voix_libres.js` (tiroir filtré,
  message quand rien ne correspond) et `test_voix/test_ids_ecran.py` (éléments,
  fonctions, style). *Sauvegardes d'avant-coup* : `frontend/app.js`,
  `frontend/index.html`, `frontend/styles.css`, `ARCHITECTURE.md`,
  `BACKLOG.md` — copiés en `.bak_avant_recherche_casting_20260920`. Détails dans
  ARCHITECTURE.md.

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

- [x] **Bouton de bascule entre les moteurs de voix (Kyutai ↔ XTTS v2)** —
  **LIVRÉ le 15/09/2026** (récap en fin d'item). Idée de Laurent, 14/09/2026.
  Un seul moteur à la fois : **allumer l'un éteint l'autre**
  (les deux ne tiennent pas ensemble sur la carte graphique).
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
  **Livré le 15/09/2026.** Le **voyant du bas de la fenêtre de lecture est
  devenu le bouton** — idée de Laurent : « un bouton sur le message qui est
  aujourd'hui en bas de la fenêtre, qui ferait office de switch ». Il affiche
  l'état (« Voix de personnages : XTTS v2 prêt — changer »), et au clic propose
  **XTTS v2**, **Kyutai** ou **aucun moteur** (le choix « aucun » permet de
  démarrer sans moteur lourd, comme le prévoyait la conception). Le serveur
  **éteint l'autre moteur** et **attend qu'il ait rendu la carte graphique**
  (port fermé, 20 s au maximum) avant d'allumer le nouveau — donc plus jamais
  7,6 Go sur 8. Un moteur **déjà prêt** ou **en cours de chargement** n'est pas
  relancé. Le choix est **noté** dans `data\moteur_voix.txt` : c'est ce que
  `START.bat` rallume au prochain démarrage. Un moteur **non installé** est
  refusé avec un message à l'écran, et si l'autre **refuse de s'éteindre**,
  **rien n'est allumé** (on ne tente jamais les deux ensemble). Pendant le
  chargement (10 à 20 s), le bouton se rafraîchit **tout seul** jusqu'à
  « prêt », puis les voix du moteur apparaissent dans les menus. Si une écoute
  est en cours, la fenêtre **prévient avant** qu'elle sera arrêtée. *Technique* :
  `POST /api/moteur/basculer` → `basculer_moteur_voix()` (main.py),
  `_pids_moteur_voix()` / `_arreter_moteur_voix()` / `_relancer_moteur_voix()`
  (les trois fonctions Kyutai restent, en enveloppes, pour l'analyse locale),
  côté écran `_libelleMoteur()`, `_ouvrirMoteurModal()`, `_basculerMoteur()`,
  `_surveillerMoteur()`, et la fenêtre `#moteur-modal`. *Vérification* :
  `test_voix/test_bascule_moteur.py` (**50 contrôles, aucun moteur lancé** : les
  deux sont simulés en mémoire) et `test_voix/test_bouton_moteur.js`
  (31 contrôles). Détails dans ARCHITECTURE.md.

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

- [x] **Distribution fine des petits rôles** (suite de la décision Kyutai du
  12/09/2026) — **TRANCHÉ et LIVRÉ le 15/09/2026**. Historique : les
  personnages de moins de 8 répliques ont d'abord reçu les voix Edge
  Éloise/Fabrice, puis (14/09/2026) une voix générique **Piper** partagée par
  genre (`GENERIC_VOICE_F/M` = `piper:siwis:0` / `piper:tom:0`).
  **Décision finale de Laurent** (à l'écoute de *Shantaram*, où **52 des 125
  personnages** étaient dans ce cas) : les Piper sont « **inaudibles, vraiment
  moches** » → **un petit rôle n'a plus AUCUNE voix dédiée : ses répliques sont
  lues par le NARRATEUR** (la voix choisie dans le lecteur), ce qui est
  cohérent puisque c'est bien le narrateur qui rapporte ce qu'il dit.
  *Technique* : `modules/voice_casting.py` — dans `assign_voices()`, un rôle
  sous `MINOR_THRESHOLD` reçoit un **`voice_id` VIDE** (au lieu d'une voix
  Piper) et un pitch neutre ; la **ligne est conservée** en base, donc le
  personnage reste **visible dans la fenêtre du casting** sous la mention
  « **Sans voix dédiée — (lu par le narrateur)** » et on peut lui redonner une
  voix à la main. `frontend/app.js` : `_voiceForSentence()` retombe sur la voix
  du lecteur quand `voice_id` est vide, `_construireMenuVoix()` affiche
  l'entrée « (lu par le narrateur) », `_previewCharacterVoice()` utilise la voix
  du lecteur pour l'aperçu. Les constantes `GENERIC_VOICE_F/M` **restent en
  place** : elles serviront d'emplacement pour les **deux voix neutres** que
  Laurent choisira (une femme, un homme) s'il préfère un jour donner aux petits
  rôles une voix distincte de celle du narrateur — il suffira de les y mettre
  et de re-caster.
  *Vérification* : `test_voix/test_pool_casting.py` (§ 6 mis à jour : voix vide
  au lieu de Piper, et un petit rôle ne consomme plus une voix du pool) + toute
  la batterie de tests (ids écran, libellés, état casting, filtre genre, voix de
  phrase, message réseau, import main) → **tout OK**.

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

- [x] **XTTS : rogner les silences de bord des fichiers générés** ✅ *LIVRÉ le
  15/09/2026 — décision de Laurent : on y touche (détail dans l'item « XTTS :
  retours d'écoute de Laurent »)*. Découvert le 15/09/2026 en vérifiant les
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

- [x] **Notes « stars » définitives pour les 35 voix XTTS v2** — livré le
  **16/09/2026**, et bien au-delà : les notes **provisoires** (recopiées de
  Kyutai le 14/09) sont remplacées par les **notes d'écoute réelles** de
  Laurent, prises dans la fenêtre « Écouter les voix » (ce sont ses
  **148 annotations**, dont 140 avec les six critères fixes).
  *Report dans les catalogues* (outil existant
  `test_voix/_appliquer_annotations_voix.py`, aperçu puis `--ecrire` suivis
  d'une copie datée des deux fichiers) : **12 changements** appliqués —
  `main.py` (1) et `modules/tts.py` (11). Les voix **écartées** (0 étoile)
  passent de 0 à **4** : `kokoro:ff_pauline`, `kokoro:fm_camille`,
  `kokoro:fm_hugo` et `piper:tom:0` — elles sortent du **pool automatique du
  casting** (elles restent sélectionnables à la main). Deux voix montent à
  3 étoiles (Gerard en Edge, Aurore et Lucas en Kokoro), et Célestin
  (« accent paysan ») redescend à 1 étoile après réécoute.
  *Piège évité au passage* : `piper:tom:0` sert de constante `GENERIC_VOICE_M`
  dans `modules/voice_casting.py` — mais elle **n'est plus utilisée** depuis le
  15/09/2026 (les petits rôles sont lus par le narrateur). Si un jour on
  redonne une voix aux petits rôles, il faudra choisir une autre voix que Tom.
  *Test remis à jour au passage* : `test_voix/test_libelles_voix.py` échouait
  **depuis le 15/09** (il réclamait une voix non vide pour chaque personnage,
  alors que les petits rôles ont une voix vide **par décision**) : il ignore
  désormais ces lignes et les compte au lieu de les signaler comme orphelines.
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
  **Report complet du 15/09/2026 (soir)** — Laurent a annoté **72 voix** dans la
  fenêtre « Écouter les voix » (genre, étoiles, remarque) ; le report a été
  appliqué en **deux passes : 49 changements** dans `modules/tts.py` (les notes
  Edge, elles, étaient déjà à jour). Résultat côté **XTTS** : **45 voix à 3★**,
  17 à 2★, 11 à 1★, **6 écartées (0★)** — Berthe, Cécile, Joséphine, Ernest,
  Rose et Albert. Les **19 voix libres** (lots 1 et 2) passent presque toutes à
  **3★**.
  *Deux corrections au passage* :
  - **« Prosper » est une voix de FEMME** (constat de Laurent) : genre corrigé en
    **F** côté **XTTS et Kyutai** (c'est le même extrait) et prénom remplacé par
    **Monique** — un prénom masculin sur une voix féminine est un piège dans le
    casting ;
  - les **5 voix laissées en « – »** par Laurent avec une remarque de défaut
    (« probleme timbre », « probleme de souffle », « souffle ») devaient en fait
    être **écartées** : ses annotations ont été passées à **0★** (elles sont la
    source : on corrige l'annotation, puis on reporte).
  *Convention rappelée* : dans la fenêtre d'écoute, **« – » = pas d'avis** et
  **« ☆ » = à écarter**. Une **0★** reste **sélectionnable à la main** dans les
  menus : elle n'est simplement plus proposée par le **casting automatique**.

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

- [x] **Voir les voix LIBRES et PAR QUI une voix est partagée** — livré le
  19/09/2026 (demande de Laurent : « je ne vois pas quelle voix est libre », et
  l'onglet « Voix partagée » ne disait pas par quel personnage). Trois choses :
  (1) un **4ᵉ bouton « 🔓 Voix libres (n) »** dans la barre des personnages : la
  liste montre alors les voix **écoutables tout de suite** qu'aucun personnage
  **ni le narrateur** ne porte, rangées par moteur comme dans « Écouter les
  voix », avec ▶ pour les reconnaître ; un moteur éteint est signalé sous la
  barre, sinon ses voix sembleraient prises ; (2) le badge de partage **écrit
  les noms** (« ⧉ partagée avec Edmond, Busoni ») et se **déplie au tap** —
  précision de Laurent : sur mobile il n'y a **ni survol ni appui long**, donc
  tout ce qui compte est écrit ; en vue « Voix partagée », les personnages sont
  **groupés par voix**, avec un en-tête qui les nomme ; (3) dans les menus de
  voix (casting **et** « Voir la voix »), chaque voix porte sa marque courte
  (` · LIBRE`, ` · partagée (2)`, ` · narrateur`, ` · petits rôles`) et le
  panneau « Voir la voix » **écrit** l'état de la voix choisie sous le menu.
  **Le narrateur compte comme une voix prise** : elle lit tout le non-dialogue.
  Cas particulier (question de Laurent, 19/09/2026) : **le narrateur peut ETRE
  un personnage** — dans « 22/11/63 », Jake Epping (3 634 répliques, verrouillé)
  porte exactement la voix du narrateur, et c'est **voulu**. Deux conséquences :
  cette voix n'est donc **jamais** annoncée libre (correct), et le personnage
  reçoit un badge **« 🎙 voix du narrateur »** (informatif, pas une alerte) ; la
  phrase de détail **écrit les deux rôles** (« … 1 personnage parle aussi avec :
  Jake Epping (choix valable : le narrateur peut être un personnage) »).
  *Nécessaire* : la fenêtre du casting prend désormais la voix du **menu du
  haut** comme référence (et non plus celle enregistrée dans le livre) — sinon
  un changement de voix du narrateur n'était pas vu avant rechargement.
  **Le re-cast, lui, ignore `narrator_voice`** (`modules/voice_casting.py` ne le
  lit pas) : seule la case **🔒** protège le couple narrateur = Jake, d'où
  l'intérêt du badge — il rend ce cas visible.
  **Recalcul apres un changement de voix** (constat de Laurent, 19/09/2026) : les
  badges, les groupes, les marques et le tiroir n'etaient calcules qu'a
  l'OUVERTURE de la fenetre — une voix donnee a un personnage laissait donc sa
  fiche annoncer « Portee par 2 personnages : ... » (son exemple : « Col-bleu
  sans bretelles » et « Andrew Cullum »). Corrige :
  `_rafraichirCastingApresChangement()` recalcule apres chaque changement de
  voix, en **attendant** l'enregistrement (sinon le recalcul se ferait sur
  l'ancienne voix), **sans rien recharger du serveur**, en **remettant la liste
  a sa position** (176 personnages obligent) et avec un **jeton** pour deux
  changements rapproches. Les curseurs vitesse/hauteur ne declenchent aucun
  recalcul : ils ne changent pas QUI porte la voix. Un echec d'enregistrement est
  desormais **dit** a l'ecran. Effet de bord utile du meme chantier : changer la
  voix du narrateur depuis le panneau « Voir la voix » est maintenant
  **enregistre pour le livre** (ca ne l'etait pas — l'enregistrement part du
  menu du haut).

  **Aller sur la fiche d'un co-porteur** (demande de Laurent, 19/09/2026 :
  « pouvoir cliquer sur Cycliste Schwinn pour arriver sur sa fiche ») : quand le
  badge est deplie, les co-porteurs sont des **boutons** (nom + nombre de
  repliques) qui font **defiler la liste** jusqu'a leur ligne et la mettent en
  evidence un court instant. Des boutons et non des liens dans la phrase : sur
  mobile, une cible tactile doit etre franche. Si un filtre cache le personnage,
  le tap n'est pas silencieux — l'appli ecrit pourquoi et propose « Tous ».
  *A ne pas confondre* avec l'item ouvert « Partager / Deplacer » (choisir une
  voix **deja portee**), qui est un choix d'ECRITURE en base, pas une navigation.

  *Technique* : `_etatVoix()` et `_resumeNoms()` (fonctions pures) et
  `_lignesPersonnages()` (extrait de `_openCastModal` le 19/09/2026 et partagé
  avec le panneau, pour que les deux comptent **les mêmes répliques**) dans
  `frontend/app.js` ; `#cast-libres-info` et `#voice-phrase-usage` dans
  `index.html` ; styles dans `styles.css`. *Vérifications* :
  `test_voix/test_etat_casting.js` (noms des porteurs, voix libres, marques,
  phrases) et `test_voix/test_tiroir_voix_libres.js` (**nouveau** : le rendu,
  sans navigateur). **Lecture seule : rien n'est attribué depuis le tiroir.**

- [x] **Prendre une voix déjà attribuée : « Partager » ou « Déplacer »** —
  **livré le 19/09/2026** (décidé avec Laurent le 15/09/2026). Choisir pour un
  personnage une voix qu'un AUTRE porte n'est plus un accident silencieux : une
  **modale en français** nomme la voix et ses porteurs, **annonce la hauteur qui
  sera appliquée**, et propose deux issues :
  **(a) Partager** — les autres gardent la voix, et le personnage la reçoit avec
  une hauteur décalée automatiquement (`_pitchPartageLibre` : +8, −8, +12, −12…
  la plus petite différence **encore libre**, par pas de 4 Hz — le pas des
  curseurs), écrite dans son curseur **avant** l'enregistrement, donc visible ;
  **(b) Déplacer** — les autres repassent « ⚠ À caster » avec la **voix générique
  de leur genre** (jamais un vide, qui casserait la lecture). Un personnage
  **verrouillé 🔒 n'est jamais déplacé** : on le dit et on ne touche à rien.
  Annuler (bouton, ✕, tap à côté ou Échap) remet le menu comme avant, sans rien
  enregistrer.
  *Technique* : `_pitchPartageLibre()` (fonction pure), `_demanderPartage()`,
  `_deplacerAutresVersGenerique()` dans `frontend/app.js` ; modale
  `#partage-modal` dans `index.html` ; styles dans `styles.css`.
  *Vérifications* : `test_voix/test_etat_casting.js` (hauteur proposée : jamais
  une hauteur déjà prise, la plus petite différence, aucun plantage quand tout
  est pris) et `test_voix/test_tiroir_voix_libres.js` (la modale tourne pour de
  vrai sur un faux DOM : texte, hauteur annoncée, ouverture/fermeture, réponse,
  respect du verrou).
- [x] **Attribuer une voix libre depuis la fiche du personnage** — livré le
  19/09/2026 (le « reste ouvert » de l'item ci-dessus, tranché avec Laurent).
  Chaque ligne de personnage porte un bouton **🗣️ « prendre une voix libre »** :
  il ouvre la liste des voix que personne ne porte encore (même présentation que
  le tiroir : rangées par moteur, ▶ pour écouter), et chaque voix a un bouton
  **« Choisir »** qui la donne à ce personnage en **conservant sa vitesse et sa
  hauteur**. Le casting est recalculé aussitôt, comme après tout changement.
  *Pourquoi depuis le personnage et non depuis le tiroir* (choix expliqué à
  Laurent) : partir d'une voix obligerait ensuite à choisir **qui**, parmi 175
  personnages — exactement le problème qu'on cherche à éviter. Le tiroir reste
  l'inventaire (voir + écouter).
  *Technique* : `_ouvrirVoixLibres()`, `_donnerVoixLibre()`, `_fermerVoixLibres()`
  et le paramètre `choisir` de `_afficherVoixLibres()` dans `frontend/app.js` ;
  modale `#voixlibres-modal` dans `index.html` ; styles dans `styles.css`.
  *Vérifications* : `test_voix/test_tiroir_voix_libres.js` (le bouton « Choisir »
  rend bien CETTE voix, vitesse et hauteur conservées, un échec est dit) et
  `test_voix/test_ids_ecran.py` (les 7 éléments de la fenêtre, les 3 fonctions,
  les styles).

- [x] **Symboles ♀️ / ♂️ pour repérer le genre d'un coup d'œil** — **LIVRÉ le
  20/09/2026** (récap en fin d'item). Demande de
  Laurent, 19/09/2026 : « on laisse le prénom, mais on ajoutera les symboles,
  ça sera plus simple à l'œil ». Aujourd'hui la ligne d'un personnage écrit le
  genre **en toutes lettres** (« Femme · 33 répliques », `frontend/app.js`,
  `genreLabel` dans `_openCastModal`) : sur un casting de 175 personnages, ça se
  lit mal. Où poser les symboles, par ordre d'utilité :
  1. **la ligne de personnage** (fenêtre du casting) : symbole **devant** le
     texte, pour que l'œil l'attrape — « ♀️ Femme · 33 répliques » (le mot reste
     dans un premier temps ; on verra à l'usage s'il devient inutile, auquel cas
     « ♀️ · 33 répliques » suffit) ;
  2. **les deux barres de filtres** (« Femmes » / « Hommes », fenêtre du casting
     et menu du narrateur) : « ♀️ Femmes » / « ♂️ Hommes » ;
  3. *à confirmer avec Laurent* : les libellés de voix dans les menus (le groupe
     « 👩 Femmes » / « 👨 Hommes » donne **déjà** le genre, le doubler serait
     redondant — mais le libellé d'une voix reste juste, par exemple sur mobile
     où l'on voit moins bien les en-têtes de groupe).
  *Pièges à ne pas oublier* : écrire les symboles avec leur **sélecteur emoji**
  (`\u2640\uFE0F` = ♀️ et `\u2642\uFE0F` = ♂️), sinon ils s'affichent en petit
  noir et blanc ; et **le genre vide** (« ni F ni M ») ne doit pas tomber sur
  « Homme » par défaut comme aujourd'hui — prévoir un signe neutre (ou laisser
  vide) plutôt qu'un genre faux.
  *Vérifications* : `test_voix/test_ids_ecran.py` (l'écran et le code restent
  cohérents) et un contrôle du libellé produit.
  **LIVRÉ le 20/09/2026.** Le symbole passe **devant** le prénom (précision de
  Laurent : « implémenter les symboles masculin/féminin **devant les
  prénoms** »), aux **trois** emplacements prévus :
  1. **ligne de personnage** de la fenêtre du casting → « ♀️ Femme · 33
     répliques » (le mot reste pour l'instant, comme prévu au-dessus) ;
  2. **barre « Voix proposées »** → « ♀️ Femmes » / « ♂️ Hommes » ;
  3. **libellé d'une voix**, partout (menus du casting, « 🎧 Écouter les voix »,
     tiroir des voix libres, menu du narrateur) → « ♀️ Eva 🇩🇪 Allemagne (NIMM
     Voix)… — Kokoro ». Le point « à confirmer » est **tranché : on l'a fait**,
     parce que c'est le SEUL repère de genre dans « Écouter les voix », rangée
     par **moteur** et non par genre ; dans les menus du casting, déjà groupés
     « Femmes » / « Hommes », il est redondant mais jamais faux.
  *Les deux pièges annoncés sont traités* : les symboles portent leur
  **sélecteur emoji** (`\u2640\uFE0F` et `\u2642\uFE0F` — écrits en entités HTML
  dans la page, en échappement JS dans `app.js`) ; et un **genre inconnu**
  n'écrit **plus « Homme »** (l'ancien code retombait sur « Homme » dès que le
  genre n'était pas `F`, donc pouvait annoncer un genre **faux** — la ligne
  affiche maintenant « 33 répliques », sans signe ni mot). Une seule fonction
  pure fait le travail, `_symboleGenre(genre)` (`frontend/app.js`), et elle
  accepte les **deux conventions** du projet : `F`/`M` des catalogues de voix,
  `F`/`H` des fiches de personnage.
  *Vérifications* : `test_voix/test_libelle_voix.js` — libellés **exacts**
  remis à jour, **11 → 17 contrôles**, dont un personnage annoncé « H », un
  genre **vide** et un genre **absent** (aucun symbole), et les **deux points
  de code** du sélecteur emoji ; `test_voix/test_ids_ecran.py` (**98 contrôles**
  au total, dont 7 nouveaux : symboles dans les deux fichiers, les deux boutons,
  absence de l'ancien repli sur « Homme ») ; **les 12 tests JS** verts,
  `node --check frontend/app.js`, `test_js_syntax.py` et
  `test_pool_casting.py`. Détails dans ARCHITECTURE.md.

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
- [x] **« Les retraits se font-ils mécaniquement, ou avec un LLM ? »** — question de
  Laurent du **18/09/2026**, au moment de relancer. **Réponse consignée** :
  **c'est du code, pas un LLM.** Le retrait des incises est une série
  d'**expressions régulières** locales (`modules/incises.py`), appelée à chaque
  phrase par `_clean_text` : **aucun appel réseau, aucune IA, à aucun moment de
  la lecture**. Mesure faite le même soir : **5 105 phrases en 0,204 s**, soit
  **0,04 ms par phrase** (≈ 25 000 phrases/seconde), là où un appel de LLM par
  phrase coûterait 1 à 3 secondes, de l'argent, et donnerait un résultat
  **non déterministe** (deux lectures du même passage se comporteraient
  différemment).
  *Qui décide quoi, en trois étages* : le **LLM** intervient **une seule fois par
  livre**, au **casting** (attribuer chaque phrase à un personnage) ; le **code**
  fait le **nettoyage du texte à la lecture** (incises, ponctuation, abréviations)
  ; la **base** garde les voix attribuées.
  *Est-ce qu'une règle de grammaire se code ?* Oui, à condition de distinguer :
  les règles **formelles** (typographie, morphologie) se codent de façon fiable
  — « virgule + verbe de parole + pronom collé par un trait d'union » ; les règles
  **ambigües** se codent **avec des garde-fous et des tests** — et quand on ne
  sait pas trancher, **on ne touche à rien** (c'est ce qui protège le texte :
  « que » exclu car conjonction le plus souvent, aucune extension si la suite est
  une question). Chaque cas tordu signalé par Laurent (quatre extraits le soir du
  18/09) est devenu un **test**, donc ne peut plus revenir.
  *Piste pour plus tard, si un cas vraiment tordu résiste* : demander au LLM **du
  casting** (qui lit déjà toutes les phrases) de marquer aussi les incises et de
  stocker leurs positions — la lecture resterait instantanée, le coût resterait
  celui du casting. À évaluer (volume : ~5 000 phrases par livre).

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
- [x] **Serveurs fantômes sur le port 8081 — le piège, et son garde-fou** — livré
  le **18/09/2026** au soir, après une soirée de fausses pistes.
  *Le piège* : fermer la fenêtre de commande ne tue pas toujours le processus
  Python. Le port 8081 reste pris par l'**ancien serveur** ; le nouveau ne peut
  pas démarrer (erreur d'une seconde, la fenêtre se ferme) et c'est l'ancien qui
  répond, **avec l'ancien code en mémoire**. Laurent a donc relancé plusieurs
  fois en croyant tester les correctifs du soir (banc d'écoute, incises,
  ponctuation) : **rien n'était chargé**. Il y avait même un **second** serveur
  oublié sur le port 8080, démarré le matin. Le doute est venu du bon réflexe de
  Laurent : « j'entends encore les incises **sur un chapitre que je n'ai jamais
  lu** » — aucun cache ne pouvait expliquer cela.
  *Diagnostic* : comparer l'heure de démarrage du processus qui écoute
  (`Get-NetTCPConnection` → PID → `Get-CimInstance`) avec la date de modification
  des fichiers de `modules/`. L'écart a tout dit (serveur de 14:28, correctifs de
  21:35). Nouvel outil : **`test_voix/_tester_tts_serveur.py`**, qui montre ce que
  le serveur renvoie vraiment (texte nettoyé vs texte d'origine).
  *Garde-fou livré* : **`START.bat` arrête désormais tout ancien serveur du
  lecteur** avant de démarrer (test du port 8081, puis arrêt des `main.py`).
  C'est la seconde partie de l'idée déjà notée dans ARCHITECTURE.md
  (« Arrêt propre du serveur depuis le launcher ») ; le bouton « Arrêter » dans le
  launcher reste à faire.
  *Erreur commise — et corrigée le soir même* : la première version filtrait les
  processus par **nom de script** (`main.py`) et a donc **arrêté NIMM**, le
  chatbot de Laurent (`G:\NIMM`, port **8080**), qui porte lui aussi un
  `main.py`. La version corrigée cible le **PORT 8081** et exige un processus
  **Python** : NIMM (8080) et le relais `tailscaled` (qui écoute aussi 8081, sur
  l'adresse Tailscale) ne sont plus jamais touchés. Laurent l'a signalé
  lui-même (« sur le port 8080 c'est NIMM, mon chatbot »), et la correction a été
  vérifiée par `test_voix/_essai_garde_fou_start.py` : « laisse tranquille
  tailscaled, arrêterait python 22764 ».
  *Sauvegarde* : `START.bat.bak_avant_garde_fou_serveur_20260918`.



- [x] **Ménage : environnements de moteurs dupliqués retirés de l'atelier** —
  livré le **16/09/2026**, à la demande de Laurent (« pour ne pas faire de
  doublons partout, dans 2 dossiers différents »).
  *Vérification préalable* : **aucun code de NIMM ePub ne dépend de l'atelier
  NIMM Voix**. Les 6 fichiers qui citent « NIMM Voix » sont des **commentaires**
  (méthode reprise, licences) et le **libellé** `France (NIMM Voix)` porté par
  30 voix Kokoro. Les deux moteurs existaient en double, à la taille près :
  `outils\xtts_tts\.venv` (7,7 Go) face à `xtts_service\.venv` (7,7 Go), et
  `outils\kyutai_tts\.venv` (4,4 Go) face à `kyutai_service\.venv` (4,4 Go).
  *Fait* : suppression des **deux seuls `.venv`** de l'atelier → **12,1 Go
  libérés** (disque G: passé à 85,5 Go libres). Les **modèles** (XTTS 2 Go,
  Kyutai 3,8 Go) vivent dans le **cache partagé** de Windows : rien à
  re-télécharger. Le service XTTS de NIMM ePub a continué de tourner pendant
  l'opération (vérifié après : 79 voix, toujours prêt).
  *Conservé volontairement dans l'atelier* : les scripts d'atelier,
  `reference` (extraits de voix), la banque Kyutai `voix_fr`,
  **`whisper-large-v3`** (2,9 Go — indispensable pour préparer un dataset
  d'entraînement), les corpus, `training`, `voicepack_train`, les voix générées
  et validées.
  *Trace* : un encadré en tête de `MEMO_XTTS_v2_pour_Cline.md` prévient que les
  chemins vers les `.venv` de l'atelier **n'existent plus** (utiliser
  `xtts_service\.venv`), pour qu'on ne cherche pas un environnement fantôme.

- [x] **Le mauvais moteur de voix peut se lancer tout seul** — **RÉGLÉ le
  15/09/2026** (récap en fin d'item). Constat de
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
  **Traité le 15/09/2026, avec le bouton de bascule.** Les pistes 1 et 3 n'ont
  pas été touchées (les lanceurs continuent d'écrire le réglage : c'est ce qui
  fait revenir le DERNIER moteur utilisé, voulu par Laurent) ; c'est la piste 4
  qui a été retenue, et appliquée **des deux côtés** :
  **(a) au démarrage** — `START.bat` teste maintenant le port de **l'autre**
  moteur **avant** de lancer le sien : si l'autre tourne déjà, il ne lance rien
  et le dit. C'est exactement la situation du 15/09 : Kyutai allumé à la main
  plus tôt dans la journée, puis choix « xtts » au démarrage suivant ;
  **(b) à chaud** — le bouton de bascule **éteint toujours l'autre avant
  d'allumer**, et refuse d'allumer quoi que ce soit si l'extinction échoue.
  Conséquence attendue : plus jamais **7,6 Go de carte graphique sur 8** sans
  que Laurent l'ait demandé. *Vérification* : `test_voix/test_start_moteur.py`
  (chaque branche teste bien les deux ports, l'autre avant le sien) et
  `test_voix/test_bascule_moteur.py` (50 contrôles, aucun moteur lancé).



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

- [x] **Sécuriser et documenter `test_voix/`** — livré le **16/09/2026**
  (demande de Laurent : « je me perds un peu » ; chantier choisi : rangement +
  sécurisation). Constat : le dossier compte **106 fichiers** (52 tests, 41
  outils d'atelier, des journaux), et surtout **un script appelait de vraies API
  payantes sous un nom qui ressemblait à un test** (`test_attribution.py`) — avec
  un **lanceur en double-clic** au titre anodin. Le guide le disait déjà
  (`CONTRIBUER.md`) mais **rien ne l'appliquait techniquement**.
  *Fait* : (1) renommé `_PAYANT_test_attribution_api.py` + lanceur
  `_PAYANT_lancer_test_attribution.bat`, pour que le danger se voie dans
  l'explorateur ; (2) le script **refuse de partir sans `--je-paie`** (message
  clair, code de sortie 2) et le lanceur **demande confirmation** ; (3)
  `test_voix/LIRE_MOI.md` : en une page, quels fichiers sont des tests (sans
  risque), quels sont des outils de diagnostic (lecture seule), quelles données
  ne pas supprimer — et la distinction entre le **seul script payant** et les
  **3 scripts à IA locale** (Ollama, gratuits mais qui occupent la carte
  graphique) ; (4) `CONTRIBUER.md` mis à jour (liste des vérifications enrichie
  des 4 nouveaux tests).
  *Vérification* : `test_voix/test_lire_moi.py` (**10 contrôles**) — aucun
  fichier cité par le mode d'emploi n'a disparu, le script payant est bien
  protégé, les anciens noms n'existent plus.
  *Reste en option* : supprimer les scripts d'atelier vraiment obsolètes — rien
  n'a été supprimé ici, la sécurisation suffisait.

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

- [x] **Tester l'écran verrouillé sous Brave** — **fait le 20/09/2026, et c'était
  LA clé du problème** 🎉 (piste de Laurent : « YouTube continue sous Brave
  écran verrouillé »). PWA installée + Batterie « **non restreinte** » pour Brave
  **et** Tailscale : la lecture tient désormais en arrière-plan (2 minutes et
  plus, y compris en quittant le lecteur et en revenant à l'accueil) ✔.
  *Avant ce réglage* (Brave sur « optimisée »), la lecture s'arrêtait **~20
  secondes** après le verrouillage : Android endormait le navigateur, l'application
  n'y pouvait rien.
  ⚠️ **Leçon** : ce réglage est **la première chose à vérifier** avant de chercher
  dans le code — il a coûté deux jours de doute. Détails dans ARCHITECTURE.md
  (« Lire écran verrouillé »).
- [ ] **Tester le casting enrichi (Kokoro + seuil 8)** sur un nouveau livre
  dès que les crédits sont rechargés.
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
