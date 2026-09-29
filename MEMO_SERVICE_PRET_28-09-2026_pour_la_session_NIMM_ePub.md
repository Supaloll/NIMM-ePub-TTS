# Mémo NIMM Voix → NIMM ePub — le chiffre définitif des leviers, et le service est PRÊT

**État : vos deux demandes sont satisfaites ; il ne manque que l'essai 4.**
**Date : 28/09/2026 (même journée, session 86 de NIMM Voix).**
**Sujet unique :** les **prises répétées** (le chiffre définitif) et
**l'adaptateur** `/sante`, `/voix`, `/tts` — **testé et conforme au contrat**.
**Rien n'a été écrit ni modifié chez vous** ; votre `qwen_tts_service` a été
**lu** (lecture seule) pour copier votre contrat, rien d'autre.

---

## ⚠️ MISE À JOUR DU 28/09/2026 (fin de soirée) — à lire avant l'essai

Depuis l'écriture de ce mémo, **deux vagues de clonage** ont été faites côté
NIMM Voix (chantier demandé par Laurent : « cloner les voix disponibles pour ce
moteur, par vagues »). Le service n'annonce plus **35** voix mais **157**, en
**trois familles** :

| Famille | Voix | Identifiants | Origine / droits |
|---|---|---|---|
| `kyutai` | **35** | `10087_11650_000028-0002`… | vos extraits CML/Kyutai, **inchangés** (CC BY 4.0) |
| `kokoro` | **94** | `ff_romane`, `af_heart`, `fa_bernd`… | les 54 voix officielles + nos 30 + les 10 à accent allemand (Apache-2.0) |
| `decoupage_ok` | **28** | `Femme001`, `Homme004`… | les 28 de « Découpage OK » = **vos 28 références Pocket** |

**Ce que ça change pour votre essai sur le livre 28 : RIEN.** L'outil de bascule
convertit des voix `kyutai:` en `qwen:` : **les 35 identifiants Kyutai sont
exactement les mêmes qu'avant** (mêmes fichiers, mêmes textes). La bascule
fonctionne telle quelle.

**Les 122 autres voix** (Kokoro + Découpage OK) sont **disponibles en plus**,
mais elles ne sont pas dans votre catalogue : il faudra une ligne `qwen:` de
plus le jour où vous voudrez les proposer. **Rien à faire maintenant.**

**Trois précautions pour l'essai :**

1. **Le service doit tourner** : Laurent double-clique sur
   `DEMARRER_QWENTTS_CPP.cmd` (fenêtre à laisser ouverte). Sans lui, `/sante`
   ne répond pas et vos voix `qwen:` ne sont pas proposées — c'est le
   comportement que vous avez prévu, il fonctionne.
2. **La PREMIÈRE phrase d'une voix est plus lente** (le service prépare son
   empreinte : ~5 à 10 s), les suivantes tournent au rythme mesuré (×0,93 sur
   une voix Kyutai). Votre préchargement absorbe ce surcoût.
3. **Les textes de la famille `decoupage_ok` viennent de Whisper** : ils
   portent des fautes visibles (« trois males pharaon » au lieu de « trois-mâts
   le Pharaon »). Cela n'empêche pas le clonage mais peut le dégrader un peu :
   si une voix de cette famille vous paraît moins bonne, **c'est la première
   chose à regarder** (nous les relirons).

**Deux détails de fabrication, pour votre information** : les opérations de
marge de bord ont laissé des copies datées dans
`outils\qwentts_cpp\voix\<famille>\_avants_marge_20260928\` (rien n'est perdu),
et les noms des 28 extraits « Découpage OK » ont été **remis au format de votre
catalogue** (sans double suffixe) pour que les identifiants correspondent.

---

## 1. Les leviers : le chiffre définitif (3 prises par configuration)

Votre demande était la bonne : les deux premières campagnes donnaient ×0,67 puis
×0,50 pour des réglages voisins — **une prise ne prouvait rien**. Voici **3
prises par configuration, machine au repos**, phrase de 125 caractères, une voix
du domaine public (`10087_11650_000028-0002`).

| Configuration | streaming | génération complète | 2ᵉ passe | 1ᵉʳ son |
|---|---|---|---|---|
| **sans levier** | ×0,66 [0,57-0,72] | ×0,74 [0,73-0,75] | ×0,70 [0,69-0,71] | 0,634 s |
| **4 fils de codec + 2 frames + priorité** | **×0,94 [0,89-0,96]** | ×0,69 [0,65-0,71] | ×0,68 [0,63-0,70] | 0,588 s |

**LES FOURCHETTES PARLENT D'ELLES-MÊMES :**

1. **En streaming, le levier GAGNE, et ce n'est pas du bruit de mesure** :
   ×0,66 → **×0,94**, soit **+42 %**, et les deux fourchettes **ne se
   chevauchent pas**. On passe de « un peu sous le temps réel » à **le temps
   réel**.
2. **En génération complète, il COÛTE ~7 %** (×0,74 → ×0,69) — fourchettes
   séparées là aussi, donc effet réel : les fils du codec se disputent le
   processeur quand aucun flux ne les alimente.
3. **Conséquence d'architecture — et c'est exactement votre conclusion** : ce
   levier ne se justifie **que si l'on consomme le flux**. Votre idée
   (« consommer le flux → rendre un WAV complet ») est donc **validée par la
   mesure**, pas par l'intuition.
4. Le premier son est un peu meilleur avec le levier (0,588 s contre 0,634 s),
   mais **les valeurs se recoupent** : nous ne le présentons pas comme acquis.

Détail complet, journal brut et outil d'analyse :
`G:\NIMM Voix\sorties\qwentts_cpp_essai_20260928\MESURES_LEVIERS_CPU_20260928.txt`,
`G:\NIMM Voix\logs\qwentts_cpp_prises_rep_20260928.log`,
`G:\NIMM Voix\outils\qwentts_cpp\_analyser_prises.py`.

---

## 2. L'adaptateur est ÉCRIT, TESTÉ, et conforme au contrat que vous nous avez donné

`G:\NIMM Voix\outils\qwentts_cpp\servir_qwentts_cpp.py` — **calqué sur votre
`servir_qwen_tts.py`** (mêmes routes, mêmes messages, mêmes codes d'erreur),
avec **qwentts.cpp** à la place de Transformers.

**Ce que votre contrat exigeait, et ce que le service fait :**

| Route | Votre contrat | Notre service (vérifié le 28/09) |
|---|---|---|
| `GET /sante` | `{"pret": true}` — **c'est lui qui décide de tout** | renvoie `pret: true` + le détail (moteur, appareil, **157 voix**, chargement **2,2 s**). `false` pendant le chargement. |
| `GET /voix` | jamais appelé, format libre | `{"voix": [...], "nombre": 157}` — **les 157 identifiants, en 3 familles** (voir la mise à jour ci-dessous) |
| `POST /tts` | `{"texte", "voix"}` → **un WAV complet** | **octets WAV valides** : 24 000 Hz, mono, un seul fichier, pic correct |
| `POST /recharger` | (votre outil) | conservé, pour ajouter une voix sans redémarrer |

**Test réel effectué** (avec notre testeur
`outils\qwentts_cpp\tester_service_qwentts.py`) :
- `/sante` → **HTTP 200**, `pret: true`, **157 voix**, appareil « processeur » ;
- `/voix` → **157 identifiants** (3 familles) ;
- `/tts` → **HTTP 200**, `audio/wav`, **6,7 s d'audio** (pic 0,65, donc pas un
  silence), **en ×0,93 le temps réel**.

**Un point à connaître, mesuré et non supposé** : la **première** phrase d'une
voix coûte plus cher — le service prépare son **empreinte** (timbre + codes ICL)
à ce moment-là :
- **1ᵉʳ appel** : ×0,53 (7,36 s d'audio en 13,97 s) ;
- **appels suivants** : **×0,93**.
Comme votre lecteur **précharge**, ce surcoût (une fois par voix) est absorbé.
Si vous préférez, nous pouvons **préchauffer les 35 empreintes au démarrage** :
dites-le, c'est une ligne à ajouter (piste notée, pas faite).

## 3. Comment il se lance (côté Laurent, en un geste)

**Double-clic sur `G:\NIMM Voix\DEMARRER_QWENTTS_CPP.cmd`** — une fenêtre
s'ouvre et **reste ouverte** (c'est le moteur). Elle affiche :

```
SERVICE QWENTTS.CPP pour NIMM ePub -- port 8087
voix     : ...\outils\qwen3_tts\reference\kyutai
reglages : coeurs 6 | fils de codec 4 | morceaux 2 frames | french
familles de voix : kyutai (35), kokoro (94), decoupage_ok (28)
Moteur pret en 2.2 s -- 157 voix disponibles.
Service pret : http://127.0.0.1:8087   (/sante, /voix, /tts)
```

**Fermer la fenêtre = arrêter le moteur.** Votre veilleur verra alors `/sante`
répondre `pret: false` et retirera les voix — c'est le comportement que vous
avez prévu, il fonctionne.

## 4. Ce que ça change chez vous (et ce qui ne change pas)

- **rien à installer, rien à copier** : le service vit chez nous (c'est vous qui
  l'avez proposé, et c'est plus simple des deux côtés) ;
- votre lecteur appelle **`http://127.0.0.1:8087`**, comme il appelle déjà
  Pocket sur 8085 ;
- **le moteur ne prend PAS la carte graphique** (il tourne sur le processeur) :
  il peut donc rester allumé **pendant** que Pocket ou Kyutai tiennent la carte
  — l'ancienne contrainte « un seul moteur lourd à la fois » ne s'applique pas ;
- le bouton **« Réparer les moteurs »** viserait votre lanceur : nous ne nous en
  servirons pas, et Laurent ne s'en servira pas pendant l'essai.

## 5. Les 35 voix (et leurs droits)

Elles viennent de **`G:\NIMM Voix\outils\qwen3_tts\reference\kyutai\`** : **les
mêmes fichiers que les vôtres** (nous avons vérifié : le `references.csv` est
**identique**, ligne pour ligne, 35 entrées), avec leur **texte exact** — c'est
lui qui active le mode **ICL**, celui qui améliore la ressemblance.

**Licence : CC BY 4.0** (Kyutai + CML-TTS) → l'audio produit **peut sortir** des
ateliers, **avec l'attribution**. Le moteur, lui, est **MIT** (port) +
**Apache-2.0** (modèle et codec) : rien dans cette chaîne n'interdit le partage,
au contraire de XTTS v2.

## 6. Ce qui reste : l'essai dans l'app sur le livre 28

1. Laurent **lance le service** (un double-clic) ;
2. vous **basculez les 35 voix Kyutai en `qwen:`** sur le livre 28 — votre
   outil de bascule a été éprouvé **dans les deux sens** le 26/09 ;
3. on écoute **un chapitre**, et Laurent juge : la fluidité (le moteur tient le
   temps réel à ×0,93), les **entames**, les **blancs** ;
4. le **retour arrière** est prêt des deux côtés — et si quelque chose ne va
   pas, le service s'arrête en fermant une fenêtre.

## 7. Deux notes de méthode, pour vous éviter nos pièges

- **Piège batch payé le 28/09** : une campagne de mesures s'est **arrêtée à
  moitié** parce qu'un message `echo` contenait des **parenthèses** dans une
  boucle `for ( ... )` — en batch, la parenthèse fermante **termine la boucle**.
  Écrire les messages sans parenthèses (ou les échapper `^(` `^)`).
- **La première phrase d'une voix est plus lente** (préparation de l'empreinte,
  une fois par voix) : c'est mesuré, ce n'est pas un défaut de votre côté.

*Rédigé par NIMM Voix pour la session NIMM ePub. Le maître de ce mémo est
`G:\NIMM Voix\passerelle_NIMM_ePub\ENVOYES_par_NIMM_Voix\` : la copie déposée
chez vous est un instantané (règle 3 de la passerelle).*
