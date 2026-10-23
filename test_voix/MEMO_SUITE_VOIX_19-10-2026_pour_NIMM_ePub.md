# Mémo pour NIMM ePub — la suite des neuf voix (19/10/2026)

**État : à jour — écrit depuis le disque de NIMM ePub, le 19/10/2026, après les
corrections d'oreille de Laurent.**
**Sujet unique : ce qui est déjà appliqué, ce qui reste à faire sur l'audio, et
la règle anti-bruit sur les extraits de clonage.**
**Où vit ce mémo : `G:\NIMM ePub\test_voix\`.**

---

## Compte rendu du 20/10/2026 (matin)

- **7 références réparées et installées** dans `qwen_tts_service/voix/` :
  Théodore (coupe à **6,50 s**), Édouard (coupe à **0,45 s** + matage
  **−6 dB** au-dessus de 3 kHz), Aubin (coupe à **8,30 s**), Berthe, Joséphine
  et Maya (DeepFilterNet + égalisation), Maurice (égalisation).
- **Achille et Cécile** : audio **inchangé** (couper dans une phrase continue
  risquait de manger un mot) ; leur **texte corrigé** est en production.
- **Sauvegarde** :
  `_essais/_reparation_9_voix_20261019/SAUVEGARDE_PRODUCTION_20261020_0702`.
- **Écoute** : `_essais/_reparation_9_voix_20261019/A_ECOUTER/` (bouton
  `ECOUTER_LA_REPARATION_DES_9_VOIX.cmd`) — AVANT/APRÈS références et clones,
  au même niveau.
- **Contrôles** : Whisper relit les références recoupées (Théodore, Édouard,
  Aubin) : le texte est exact. Les **18 clones** (p1 sur 4 s + p2 entier) ont
  été relus : les **neuf p1** démarrent sur le bon texte et les **neuf p2**
  disent la phrase complète — **plus de babil**.
- **Ce qui reste** : l'oreille de Laurent ; éventuellement recouper la fin
  d'Achille/Cécile sur un extrait plus long ; étendre les filtres anti-bruit
  au reste de la garde-robe.

*Les sections ci-dessous sont le diagnostic et le plan initial ; le compte
rendu ci-dessus fait foi.*

---

## 0. En deux lignes

Laurent a relu les **neuf voix** dans la fenêtre d'écoute et a enregistré son
CSV à la racine. **Cinq textes ont changé** et sont **déjà appliqués** dans les
deux fichiers du service (public + privé), avec copies datées ; **quatre textes
étaient déjà justes**. Il reste **l'audio** : quelques débuts/fins à recouper,
du souffle à retirer, et de l'égalisation. C'est le travail de NIMM Voix, avec
la nouvelle règle : **filtrer le bruit sur les extraits qui servent au clonage,
pas seulement sur les clones**.

---

## 1. Ce que Laurent a corrigé (CSV `_corrections_oreille.csv`, racine)

| Voix | Texte | Ce qu'il a noté |
|---|---|---|
| Théodore (`Homme002`) | **changé** (282 car.) : commence par « tait méconaissable… » | « Parasite au début. Il manque la première partie de la phrase, qui commence sur “tait”, un mot coupé. » |
| Édouard (`Homme004`) | inchangé | « Parasite au début : un petit son “K”, il suffit de couper un tout petit peu le début. » |
| Aubin (`homme_aigu_6877654`) | inchangé (253 car., finit « Morgi ») | « finit sur un mot coupé — cap de Morgion » |
| Maya (`Maya_normale`) | **changé** (425 car., « sornettes »…) | « Voix qui sature sur les débuts de mots. Problème de micro. » |
| Achille (`cml1840`) | **changé** (135 car.) : commence par « Madame… », finit « organisa… » | « la fin est coupée sur un mot » |
| Berthe (`cml1649`) | inchangé | « voix de très mauvaise qualité. Souffle, et métallique. » |
| Cécile (`cml1869`) | **changé** (183 car.) : ajoute « Madame, je vous supplie… confon… » | (rien) |
| Joséphine (`cml2316`) | inchangé | « voix de très mauvaise qualité. Très métallique, et bruit de fond. » |
| Maurice (`cml3182`) | **changé** (173 car.) : ponctuation et guillemets | (rien) |

**Détail qui compte** : Laurent a écrit le **mot coupé** quand il l'entendait
(`tait`, `organisa…`, `confon…`, `Morgi`). C'est la bonne méthode pour aligner
le texte sur l'audio — mais **ça ne répare pas la coupe**. Pour les voix
concernées, il faudra recouper l'audio **et** raccourcir le texte du même coup
(voir § 3).

---

## 2. Ce qui est déjà appliqué chez NIMM ePub

- **5 lignes changées** : `Homme002`, `cml1840`, `cml1869`, `cml3182` dans
  `qwen_tts_service\voix\references.csv`, et `Maya_normale` dans
  `references_privees.csv` (hors Git).
- **4 lignes déjà justes** : `Homme004`, `cml1649`, `cml2316`,
  `homme_aigu_6877654` — le CSV de Laurent et la production étaient identiques.
- **Copies datées avant écriture** :
  `references.csv.bak_avant_corrections_laurent_20261019_1845` et
  `references_privees.csv.bak_avant_corrections_laurent_20261019_1845`.
- **Aucun WAV touché** ; les fins de ligne sont conservées (public **CRLF**,
  privé **LF**) ; les durées, hauteurs, sources et **les 201 autres voix** sont
  **identiques** (relecture du script : 4 changements publics, 1 privé, 0 autre
  ligne modifiée).
- Le crochet `[` de Laurent (`[tait…`) a été **retiré** : c'est une notation,
  pas une parole. Son texte appliqué commence donc par « tait méconaissable… ».
- **Outil** : `test_voix\_appliquer_corrections_oreille_19_10.py` (rapport seul
  par défaut, `--ecrire` pour appliquer, relecture de contrôle après écriture).
- **Garde-fou des textes privés** : le CSV d'oreille a été **séparé**. Le
  fichier versionné `test_voix\_corrections_oreille.csv` ne contient plus que
  les **voix publiques** (67 corrections) ; le texte de **Maya** vit dans
  `test_voix\_corrections_oreille_privees.csv`, **ignoré par Git** (1
  correction). La copie téléchargée à la racine est ignorée elle aussi. Copie
  datée du nettoyage :
  `_corrections_oreille.csv.bak_avant_separation_privee_20261019_1851` ; le
  bouton « Télécharger mes corrections » **fusionne** les deux fichiers.

---

## 3. Ce qui reste à faire sur l'audio (NIMM Voix)

| Voix | Reste à faire | Texte à ajuster ensuite ? |
|---|---|---|
| **Théodore** | l'audio commence sur un **mot coupé** (« tait ») : recouper au début de « Le château… » (on perd ≈ 4 s, la référence reste ≈ 16 s) | **oui** : retirer la phrase « tait méconaissable… l'écurie. » du texte, sinon le texte dira plus que l'audio |
| **Édouard** | petit parasite **« K »** au tout début : recouper quelques dizaines de ms (garder 100 ms de silence propre) | non |
| **Aubin** | la fin est **coupée** (« Morgi ») : recouper à la fin de « … Trieste et Naples. » et garder la première phrase | **oui** : retirer la fin « Comme d'habitude… Morgi » |
| **Achille** | la fin est **coupée** (« organisa… ») : recouper sur un mot complet, par exemple après « courage » | **oui** : retirer « parmi les organisa… » |
| **Berthe** | souffle + couleur métallique : DeepFilterNet, puis égalisation médiane ; la source est médiocre, à surveiller | non |
| **Maya** | **saturation** sur les débuts de mots (micro) : DeepFilterNet ne répare pas la saturation → décrucher (de-clipper) si possible, ou ré-extraire un passage non saturé | non (texte déjà appliqué) |
| **Cécile** | la fin est **coupée** (« confon… ») : recouper à la fin de « … de si mauvaise augure. » (la citation est complète) | **oui** : retirer « Madame, je vous supplie… confon… » |
| **Joséphine** | bords sales + souffle + niveau faible : 100 ms de silence aux bords, DeepFilterNet, niveau −23 dBFS, puis égalisation | non |
| **Maurice** | métallique : égalisation médiane, puis matage −3 dB au-dessus de 3 kHz si besoin | non (texte déjà appliqué) |

**Règle d'or** : **on ne recoupe jamais un WAV sans mettre le texte à jour dans
le même geste**. C'est exactement ce qui a produit le babil : un audio qui dit
une chose, un texte qui en dit une autre.

---

## 4. La nouvelle règle : filtrer le bruit SUR LES EXTRAITS DE CLONAGE

Idée de Laurent, 19/10/2026 : « on devrait appliquer les filtres anti-bruit sur
les extraits qui servent au clonage. » **Il a raison, et c'est le bon endroit** :
dans le lecteur, la « voix » est l'extrait de référence ; le moteur le recopie à
chaque phrase. Nettoyer le clone après coup, c'est nettoyer la conséquence ;
nettoyer la référence, c'est traiter la cause.

### La chaîne proposée (dans cet ordre)

1. **Mesurer d'abord** : `mesurer_timbre_voix.py` (fond, écart voix/fond),
   `mesurer_bords_extrait.py` (bords), `mesurer_attaques_lot.py` (attaque),
   `mesurer_spectre_voix.py` (couleur).
2. **Démixer seulement si nécessaire** : `Demucs` si l'extrait contient musique
   ou effets. Sur une voix seule (CML, Kyutai), **`--sans-demucs`** : sinon on
   abîme le timbre pour rien.
3. **DeepFilterNet** pour le bruit large bande : souffle, fond, bruit de micro.
   C'est lui qui traite Berthe, Joséphine, Maya.
4. **Passe-haut ≈ 80 Hz** pour le grondement ; **pas de passe-bas** : les aigus
   font partie de la voix.
5. **Décrucher (de-clipper) si la source sature** — Maya. DeepFilterNet ne
   répare **pas** la saturation ; si le passage est trop abîmé, **ré-extraire**
   un passage non saturé est plus sûr.
6. **Égalisation médiane** (`recadrer_spectre_voix.py`, profil
   `sorties\recadrage_spectre_20261017\profil_cible.json`, bornée ±6 dB) pour la
   couleur, puis **matage −3 dB au-dessus de 3 kHz** si le métallique persiste.
7. **Niveau et format** : niveau de parole **−23 dBFS**, pics **0,97**, **100 ms**
   de silence aux deux bords, **24 kHz mono PCM16**.

### Les garde-fous, appris à l'atelier

- **Ne pas filtrer les 206 voix en aveugle** : un débruiteur mal dosé **éteint**
  la voix (perte d'aigus, voix étouffée). On commence par **les neuf**, on
  mesure, on écoute en A/B, puis on étend **famille par famille**.
- **Deux prises par version** : le clone n'est pas déterministe.
- **Whisper sur les 4 premières secondes** : le texte doit être là, sans babil.
- **A/B obligatoire** : AVANT / APRÈS, même niveau, dans un seul fichier.
- **Droits** : Maya et les voix d'acteurs restent **privées** ; le nettoyage ne
  change rien à ça.

### Ce que ça ne répare pas

- un **mot coupé** au début ou à la fin (il faut **recouper**, pas filtrer) ;
- une **saturation** déjà inscrite dans l'audio (il faut décrucher ou ré-extraire) ;
- un **texte faux** (il faut le corriger — c'est fait pour les neuf).

---

## 5. Procédure d'application, quand NIMM Voix renvoie le paquet

1. **Copie datée** de `qwen_tts_service\voix\` et des deux CSV.
2. Remplacer **seulement** les WAV des voix concernées, **sous le même nom**
   (`Homme002_reference.wav`, etc.) — jamais un nom en double.
3. Si le WAV a été **recoupé**, mettre **le texte à jour dans le même geste**
   (§ 3) : le texte doit dire exactement ce que dit le nouvel audio.
4. **Redémarrer Qwentts** (`START.bat` ou
   `qwentts_service\DEMARRER_QWENTTS_CPP_GPU.bat`) : il garde en mémoire le
   texte **et** l'empreinte de chaque voix.
5. **Vider le cache audio** du lecteur (bouton « 🧹 Vider le cache ») : sinon il
   rejoue l'ancien son.
6. **Re-tester** avec le protocole du § 6, puis rendre compte à Laurent.

---

## 6. Protocole de contrôle (le même que le diagnostic)

1. Deux phrases : la phrase de contrôle (« Le 24 février 1815… ») et
   « Pardon, dit-il, je ne vous ai pas entendu. »
2. **Deux prises par voix** (température 0,9 : le clone n'est pas déterministe).
3. **Whisper large-v3** sur les 4 premières secondes : mots attendus, pas de
   babil.
4. Mesures : silence de tête, niveau des 10 premières fenêtres, niveau médian,
   centre spectral, marge de bruit, bords.
5. Une voix n'est **OK** que si **les deux prises** passent.

Les scripts sont dans `G:\NIMM ePub\_essais\` :
`_diag_9_voix_20261019.py`, `_asr_prefixes_20261019.py`,
`_asr_references_20261019.py`.

---

## 7. Fichiers, preuves et sauvegardes

| Objet | Chemin |
|---|---|
| Les corrections de Laurent | `G:\NIMM ePub\_corrections_oreille.csv` (racine, **ignoré par Git**) |
| Le même fichier, côté outil | `G:\NIMM ePub\test_voix\_corrections_oreille.csv` (voix publiques, versionné) |
| Les corrections de Maya | `G:\NIMM ePub\test_voix\_corrections_oreille_privees.csv` (**ignoré par Git**) |
| Les textes publics | `G:\NIMM ePub\qwen_tts_service\voix\references.csv` |
| Le texte privé (Maya) | `...\voix\references_privees.csv` (hors Git) |
| Sauvegarde avant application | `references.csv.bak_avant_corrections_laurent_20261019_1845` |
| Sauvegarde privée | `references_privees.csv.bak_avant_corrections_laurent_20261019_1845` |
| L'outil d'application | `test_voix\_appliquer_corrections_oreille_19_10.py` |
| La réparation audio (coupes, filtres, EQ) | `_essais\_reparer_9_voix_20261019.py` |
| L'installation (copies datées, textes) | `_essais\_installer_reparation_9_voix.py` |
| Le dossier d'écoute AVANT/APRÈS | `_essais\_reparation_9_voix_20261019\A_ECOUTER\` |
| Le lanceur d'écoute | `ECOUTER_LA_REPARATION_DES_9_VOIX.cmd` (racine) |
| Le diagnostic audio | `_essais\_diag_9_voix_20261019\` + `_asr_prefixes.log` + `_asr_references.log` |
| Le mémo détaillé (NIMM Voix) | `test_voix\MEMO_VOIX_A_REFAIRE_19-10-2026_pour_NIMM_Voix.md` |

**Ce qui n'a pas été touché par cette application** : les neuf WAV de référence,
`modules\tts.py`, les annotations d'écoute et les autres voix. Seule la colonne
`texte` des cinq lignes concernées a changé.

---

## 8. Les trois pièges à ne pas rouvrir

1. **Recouper un WAV sans changer le texte** : le babil revient immédiatement.
   Le couple audio + texte est indissociable.
2. **Filtrer avant d'avoir mesuré** : un débruiteur trop fort éteint la voix.
   Mesurer, A/B, deux prises.
3. **Croire un seul tirage** : le clone n'est pas déterministe. Une voix n'est
   « OK » que si **deux prises** passent le contrôle Whisper.

---

## 9. Qui fait quoi

| Tâche | Qui |
|---|---|
| Textes des neuf voix | **fait** (NIMM ePub, 19/10/2026) |
| Recoupes audio (Théodore, Édouard, Aubin, Achille, Cécile) | **NIMM Voix** |
| Décruchage / saturation (Maya) | **NIMM Voix** |
| Filtres anti-bruit (Berthe, Joséphine, Maya) | **NIMM Voix** |
| Égalisation / matage (Édouard, Maurice, Joséphine, Berthe) | **NIMM Voix** |
| Installation du paquet, redémarrage, cache, tests | **NIMM ePub** |

---

*Écrit le 19/10/2026 depuis le disque de NIMM ePub. Si un chiffre de ce mémo
contredit le disque, c'est le disque qui a raison : dites-le, on corrige.*



