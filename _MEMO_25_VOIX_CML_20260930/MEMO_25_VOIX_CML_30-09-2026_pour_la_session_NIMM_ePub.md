# Mémo NIMM Voix → session NIMM ePub — 25 VOIX NOUVELLES (CML-TTS)

**Date** : 30/09/2026 (session 89 de NIMM Voix).
**État** : **à jour : oui** — les 25 références sont figées, mesurées et
vérifiées chez nous ; elles attendent d'être **recopiées chez vous**.
**Un mémo = un sujet** : ces 25 voix (dont 4 références reprises), et rien
d'autre.

---

## 1) Ce qui est prêt chez nous — un dossier à recopier

Notre famille de voix, sur votre disque (même machine) :

    G:\NIMM Voix\outils\qwentts_cpp\voix\cml_restants\

Contenu : **25 WAV de référence** (mono 24 kHz 16 bits, 8,9 à 12,7 s), un
`references.csv` (25 lignes + en-tête, **même format que le vôtre** :
`fichier;texte;duree;hauteur;source`) et un `LISEZ-MOI.txt` (provenance et
droits).

L'identifiant de chaque voix est le nom du fichier **sans** `_reference.wav` :
`cml10065_reference.wav` -> **`cml10065`**. Côté page, cela donnera
`qwen:cml10065`, etc. — même convention que vos 158 voix actuelles.

## 2) Les trois gestes, chez vous

1. **Sauvegarde d'abord** : copie datée de votre
   `qwen_tts_service\voix\references.csv`
   (par exemple `references.csv.bak_avant_cml_20260930`) — vos sauvegardes
   précédentes restent intactes.
2. **Copier les 25 WAV** dans `qwen_tts_service\voix\` : ce sont des fichiers
   **neufs**, aucun des 25 identifiants n'existe chez vous (vérifié) — il n'y
   a donc **rien à écraser**.
3. **Ajouter les 25 lignes** à `references.csv` **sans toucher aux 158
   existantes** : elles sont en annexe (point 7), prêtes à coller, ou à
   reprendre directement dans notre fichier — **c'est lui qui fait foi**,
   l'annexe n'est qu'un instantané du 30/09/2026. Format relevé chez vous le
   29/09/2026 : UTF-8 **sans BOM**, fins de ligne **LF**, 5 colonnes.

Ensuite `/voix` doit annoncer **183** (158 + 25) et chaque voix doit rendre un
WAV valide.

**Le catalogue est votre partie** : `QWEN_VOICES` (`modules/tts.py`) se
construit à partir de `KYUTAI_VOICES + KOKORO_VOICES + POCKET_VOICES`, donc
une voix neuve n'y entre pas toute seule (même constat que pour
`Maya_normale`). Les annotations (nom affiché, genre, âge, étoiles) vivent
dans `data/annotations_voix.json` ; le point 3 vous donne ce que Laurent en a
dit à l'oreille.

## 3) Ce que Laurent en a dit, à l'oreille (30/09/2026)

Il a écouté les 25 (d'abord l'extrait à imiter, puis le clone), et noté de 1 à
3 étoiles. Ses mots sont repris tels quels :

| Voix | Étoiles | Ce qu'il en dit |
|---|---|---|
| cml10065 | ** | OK |
| cml12501 | *** | OK |
| cml12512 | *** | OK |
| cml12823 | *** | OK |
| cml1649 | *** | OK, **accent anglais** |
| cml1840 | *** | OK |
| cml1869 | *** | OK |
| cml2033 | *** | OK |
| cml2316 | * | OK (la seule à une étoile) |
| cml2771 | *** | **reprise** : son parasite de début (« ter ») a disparu, 5/5 |
| cml3060 | ** | OK |
| cml3182 | *** | **reprise** : son parasite (« èts ») a disparu, 5/5 |
| cml3344 | *** | OK |
| cml3503 | *** | OK |
| cml5525 | *** | OK |
| cml5526 | ** | **reprise** : son parasite a disparu, 5/5 |
| cml6070 | ** | OK |
| cml6249 | *** | OK, **accent paysan** — « roule les R, excellent ! » |
| cml6348 | ** | OK |
| cml6381 | ** | OK |
| cml7239 | *** | **reprise** : 5/5, « léger accent Maghreb » |
| cml7377 | *** | OK |
| cml7423 | ** | OK, **accent canadien** |
| cml7614 | *** | OK — **une voix d'ENFANT** |
| cml9804 | *** | OK |

Bilan : **14 voix à 3 étoiles**, 6 à 2 étoiles, 1 à 1 étoile, et **4 reprises
validées 5/5**. Pour sa demande du soir (« des voix pour les rôles qui
manquent : enfant, jeune, vieux, adultes »), les trouvailles utiles sont
`cml7614` (enfant), `cml6249` (paysan), `cml7423` (canadien) et `cml1649`
(anglais).

**La décision finale d'entrée au catalogue est à Laurent** : il n'a pas coché
« à garder ? », donc à vous (ou à lui, à l'écran) de trancher. Le plus simple
techniquement est de **tout déposer**, puis de n'afficher que ce qui lui plaît.

## 4) Les droits — et une différence importante avec `Maya_normale`

Ces 25 voix viennent de la **banque CML-TTS** (jeu de données publié par
Kyutai, dossier `cml-tts/fr`), **licence CC BY 4.0** : utilisation libre, y
compris pour un **partage**, **à condition de citer les auteurs**
(« Kyutai + CML-TTS »). Le texte de référence a été transcrit par Whisper sur
des lectures de **livres classiques** (domaine public).

C'est donc **l'inverse de `Maya_normale`** (voix d'une personne réelle, privée,
à garder du côté privé de votre catalogue). Ici : aucun accord à demander,
l'affichage de l'attribution est le seul geste.

Rappel qui reste vrai : l'audio produit suit les droits de la **voix**, pas du
moteur (`qwentts.cpp` MIT, modèle et codec Qwen3-TTS Apache-2.0).

## 5) Trois choses à savoir sur ces voix

1. **La première phrase paie l'empreinte** (~2 s chez nous, une fois par voix) :
   même comportement que vos 158 voix actuelles.
2. **Les textes de référence viennent de Whisper**, donc possiblement fautifs
   sur les noms propres : en cas de gargouillis, relire la colonne `texte` mot
   pour mot sur l'audio est le premier geste — c'est le piège de votre incident
   du 29/09 (`homme_aigu_6877654`).
3. **Quatre références ont été reprises le 30/09/2026** : `cml2771`,
   `cml3182`, `cml5526`, `cml7239`. Leurs versions précédentes commençaient au
   milieu d'un mot (« ...ter », « ...ets », « ...anté ») — c'est le défaut de
   bord déjà connu chez nous : **le moteur recopie le tout début de la
   référence au début de chaque phrase**. Les versions livrées ici sont
   **recoupées sur un vrai silence** depuis l'extrait d'origine, et leur texte
   a été **re-transcrit**. Si vous aviez copié une version antérieure, la
   remplacer — celle-ci est la bonne.

## 6) La preuve, relevée chez nous avec votre mécanisme

Notre dossier de famille est lu par le **même mécanisme que le vôtre**
(`_repertorier_voix()`, mêmes suffixes reconnus `_enhanced_reference.wav` et
`_reference.wav`) :

    familles de voix : kyutai (35), kokoro (94), decoupage_ok (28),
                       cml_restants (25), famille_maya (1)
    voix exploitables : 183
    cml_restants prises : 25

Contrôles complémentaires, tous faits **avant** ce mémo : **25/25 bords
propres** (marge de 100 ms minimum aux deux bords), **aucun identifiant en
double** avec les autres familles, **aucun WAV sans texte**.

Mesures de notre lot (le clone dit le texte de contrôle de l'atelier, 221
caractères) : clones de **10,8 à 15,7 s**, débit **×0,45 à ×0,65** le temps
réel **sur le processeur** — à prendre comme un **plancher**, la machine
portait en même temps votre service sur le port 8086.

## 7) Annexe — les 25 lignes à ajouter à `references.csv`

**Instantané du 30/09/2026.** Le maître reste notre fichier
`G:\NIMM Voix\outils\qwentts_cpp\voix\cml_restants\references.csv` : en cas de
doute, c'est lui qu'il faut lire (et non cette copie, qui ne se mettra pas à
jour toute seule — règle 3 de la passerelle).

```
fichier;texte;duree;hauteur;source
cml10065_reference.wav;Et comme elle se taisait, il prit son sceptre d'or et le lui posa sur le cou, et il la baisa et lui dit, « Pourquoi ne me parlez-vous point ?;10.04;117 Hz;cml10065_enhanced_reference.wav
cml12501_reference.wav;il ne lui avait pas adressé une seule fois la parole hors du tribunal de la pénitence ou encore il écoutait plus qu'il ne parlait il en eût été bien autrement;9.89;157 Hz;cml12501_enhanced_reference.wav
cml12512_reference.wav;Julien était encore dans le premier sommeil quand il fut réveillé en sursaut par les voix de deux personnes qui parlaient dans sa chambre sans trop se gêner.;9.95;204 Hz;cml12512_enhanced_reference.wav
cml12823_reference.wav;et que le bonnet de zadig était jaune c'était là de terribles indices pour un prince délicat les soupçons se tournèrent en certitude dans son esprit aigri;9.83;202 Hz;cml12823_enhanced_reference.wav
cml1649_reference.wav;si la balance de l'idiotisme ne l'importe pas de beaucoup sur le plateau dans lequel reposent les nobles et les magnifiques attributs de la raison;10.27;227 Hz;cml1649_enhanced_reference.wav
cml1840_reference.wav;de maufrigneuse était à demi pensive mêmes inquiétudes la dévoraient mais elle les supportait avec courage parmi les;9.95;136 Hz;cml1840_enhanced_reference.wav
cml1869_reference.wav;« Ces calendaires borgnes sont la cause de ce malheur. Il n'y a pas de ville qui ne tombe en ruine devant des gens de si mauvaise augure. »;10.00;263 Hz;cml1869_enhanced_reference.wav
cml2033_reference.wav;de suivre jusqu'au centre de la terre les traces de voyageurs islandais il fut modeste dans sa gloire et sa réputation;10.28;161 Hz;cml2033_enhanced_reference.wav
cml2316_reference.wav;rien n'est indigne pour une intelligence grande et simple le moindre phénomène de la nature s'il y a mystère en lui deviendra pour le sage;9.82;179 Hz;cml2316_enhanced_reference.wav
cml2771_reference.wav;Il mériterait l'épreuve des plus grands supplices, car il y a du mépris aveugle dans son insouciance ignorante. Mais celui qui vous connaît et vous apprécie ne veut plus rien des biens de la terre, se contente de vos jouissances magiques.;12.65;131 Hz;cml2771_enhanced.wav
cml3060_reference.wav;allait-il se constituer prisonnier comment de quel côté et des images affreuses des images de mort se précipitèrent dans son âme;10.21;187 Hz;cml3060_enhanced_reference.wav
cml3182_reference.wav;l'époux d'une jeune beauté partait pour l'autre monde à ses côtés sa femme lui criait attends-moi je te suis et mon âme aussi bien que la tienne est prête à s'envoler;12.74;141 Hz;cml3182_enhanced.wav
cml3344_reference.wav;Je te promets un bœuf si tu fais qu'il s'écarte. C'est ainsi que l'a dit le principal auteur. Passons à son imitateur.;9.48;145 Hz;cml3344_enhanced_reference.wav
cml3503_reference.wav;le vent emporta tout personne ne s'émut l'animal aux têtes frivoles étant fait à ses traits;9.43;111 Hz;cml3503_enhanced_reference.wav
cml5525_reference.wav;ce brigand d'enfants préparé à coup sûr une farce, car il ne décollerait pas contre les soldats. Il demandait quand on serait débarrassé de ces assassins qu'on envoyait avec des fusils;10.00;127 Hz;cml5525_enhanced_reference.wav
cml5526_reference.wav;Mais devant les ravages ardents qui se déclarèrent durant la traversée, le duc vit bien qu'il ne pouvait conserver d'autre espoir qu'en une prompte mort.;8.86;114 Hz;cml5526_enhanced.wav
cml6070_reference.wav;L'agitation d'un pistolet sans chien qu'on tient à la main en pleine rue est une telle fonction publique que Gavroche sentait croître sa verve à chaque pas.;9.41;199 Hz;cml6070_enhanced_reference.wav
cml6249_reference.wav;Une crête s'élevait haute sur sa tête. Ses yeux étaient d'escarboucle. Son cou était d'un or vert bruni.;9.63;125 Hz;cml6249_enhanced_reference.wav
cml6348_reference.wav;il semble qu'elles se relaient pour m'exercer et que leur fantaisie se succède souvent elles se plaisent à me faire redoubler de soin elles me font;10.61;170 Hz;cml6348_enhanced_reference.wav
cml6381_reference.wav;rien n'est plus fréquent que ce phénomène il y a un instant où les filles s'épanouissent en un clin d'oeil et deviennent des roses tout à coup hier on les a laissées enfants aujourd'hui;9.56;184 Hz;cml6381_enhanced_reference.wav
cml7239_reference.wav;Mais Hans semblait s'intéresser peu à la question dans laquelle son existence se trouvait en jeu. Prêt à partir si l'on donnait le signal du départ, prêt à rester à la moindre volonté de s'en mettre.;10.81;126 Hz;cml7239_enhanced.wav
cml7377_reference.wav;a disparu pour laisser régner en paix l'espèce de poêle gigantesque ornée de son tuyau qui a remplacé la sombre forteresse à neuf tours à peu près comme la bourgeoisie;10.00;123 Hz;cml7377_enhanced_reference.wav
cml7423_reference.wav;simplement un morceau de houille déboulait d'un panier trois ou quatre enfants dégringolaient du coup la tête en bas les crampes de ses membres;10.11;106 Hz;cml7423_enhanced_reference.wav
cml7614_reference.wav;sans que j'aie jamais pu savoir comment j'y avais été transportée et comment la maison avait disparu. Depuis cette époque, que j'ai toujours présente à la mémoire,;9.86;254 Hz;cml7614_enhanced_reference.wav
cml9804_reference.wav;affublé d'une fausse barbe et d'une paire de lunettes courbé en deux comme un vieillard bref vous le baron repstein et c'est vous pour une bonne raison;10.47;140 Hz;cml9804_enhanced_reference.wav
```

---

*Côté NIMM Voix, tout est consigné : `JOURNAL.md` (session 89), `ETAT.md`,
`BACKLOG.md` (« VAGUE 6 » et l'item « mélange de timbres Qwen »),
`sorties\qwentts_cpp_cml_restants_20260929\` (le lot écouté par Laurent, son
verdict, son index rempli), `sorties\cml_reparation_20260930\` (les 4
reprises, avec la comparaison AVANT/APRÈS) et
`outils\qwentts_cpp\voix\cml_restants\LISEZ-MOI.txt` (droits).*
