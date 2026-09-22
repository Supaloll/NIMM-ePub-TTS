// Verifie le LIBELLE d'une voix dans les menus (demande de Laurent, 19/09/2026).
// ---------------------------------------------------------------------------
// Format demande :
//   « [Symbole du genre] [Prenom] [drapeau de la langue] [2e drapeau eventuel]
//     [Age] [Timbre] — [Moteur] »
// soit « ♀️ Alice <FR> Jeune aigu — Kyutai » et « ♂️ Amelie <FR><GB> Mure grave — Kokoro ».
//
// Ce que le test verifie :
//   1. le drapeau du FRANCAIS est toujours devant : Laurent « ne lit qu'en
//      francais de toute facon » ;
//   2. le 2e drapeau vient de la region quand elle en porte un (Etats-Unis,
//      Japon), sinon d'un accent NOMME dans la region (« accent allemand »),
//      sinon d'un pays ecrit en clair (Canada, Belgique, Suisse), sinon de
//      l'accent annote par Laurent ;
//   3. les voix Edge, dont la region s'ecrit « France » / « Canada », affichent
//      enfin un drapeau (elles n'en avaient AUCUN) ;
//   4. l'age et le timbre affiches sont les LIBELLES du serveur (« mûr » et non
//      « mur », « très aigu » et non « tres_aigu ») ;
//   5. une voix sans annotation reste propre (pas d'espace en trop) ;
//   6. le moteur est montre par son ICONE dans le libelle d'une voix
//      (20/09/2026, demande de Laurent : « un visuel sur les moteurs plutot que
//      les noms ») : « ♀️ Eva 🇩🇪 médium — 🎎 ». Le NOM complet reste partout ou
//      il y a la place (fenetre « Ecouter les voix », tiroir des voix libres,
//      menu de filtre, bouton des moteurs) ;
//   7. le SYMBOLE DU GENRE passe devant le prenom (20/09/2026, item du BACKLOG
//      du 19/09/2026) : ♀️ / ♂️ selon le genre, et RIEN si le genre est inconnu
//      (jamais un genre faux, piege signale d'avance). Le symbole porte bien
//      son SELECTEUR EMOJI (\uFE0F), sans quoi il s'affiche en petit noir et
//      blanc sur beaucoup de claviers et de polices.
//
// Meme technique que test_criteres_voix.js : les fonctions sont extraites DU
// FICHIER REEL (jamais recopiees) et evaluees dans un contexte minimal.
//
// Usage : node test_voix/test_libelle_voix.js
'use strict';

const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'frontend', 'app.js');
const source = fs.readFileSync(APP, 'utf8');

function extraire(debutNom, finNom) {
  const debut = source.indexOf(debutNom);
  let fin = source.indexOf(finNom);
  if (fin > 0 && source.slice(fin - 6, fin) === 'async ') fin -= 6;
  if (debut < 0 || fin <= debut) {
    console.error('ECHEC : %s introuvable dans app.js', debutNom);
    process.exit(1);
  }
  return source.slice(debut, fin);
}

const CODE = [
  extraire('const DRAPEAU_FR', 'function _secondDrapeauDeVoix'),
  extraire('function _secondDrapeauDeVoix', 'function _libelleCritere'),
  extraire('function _libelleCritere', 'function _symboleGenre'),
  extraire('function _symboleGenre', 'function _identiteVoix'),
  // Depuis le 22/09/2026, le libelle est assemble a partir de DEUX morceaux :
  // l'identite (symbole, prenom, drapeaux, age, timbre) et l'icone du moteur.
  // La LISTE DES VOIX du panneau les met sur deux lignes ; ici, on verifie le
  // libelle complet sur une ligne, tel qu'il reste partout ailleurs.
  extraire('function _identiteVoix', 'function _libelleVoix'),
  extraire('function _libelleVoix', 'async function loadMoteurs'),
  extraire('function _familleDeVoix', 'function _libelleFamille'),
  extraire('function _libelleFamille', 'async function _chargerAnnotationsVoix'),
].join('\n');

// La famille des moteurs, telle que la page la declare : libelles ET icones
// (FAMILLES_VOIX, app.js). Depuis le 20/09/2026, le libelle d'une voix montre
// l'ICONE du moteur a la place de son nom -- dans un menu etroit, le nom
// prenait la place du prenom, de l'age et du timbre.
const ICO_EDGE    = '\u2601\uFE0F';
const ICO_KOKORO  = '\uD83C\uDF8E';
const ICO_XTTS    = '\uD83E\uDDEC';
const FAMILLES = [['edge', 'Edge (en ligne)', ICO_EDGE],
                  ['kokoro', 'Kokoro', ICO_KOKORO],
                  ['piper', 'Piper', '\uD83C\uDFB6'],
                  ['kyutai', 'Kyutai', '\u26A1\uFE0F'],
                  ['xtts', 'XTTS v2', ICO_XTTS],
                  ['neutts', 'NeuTTS', '\uD83E\uDDEA']];

// Les criteres, tels que le SERVEUR les annonce (extrait de main.py).
const CRITERES = [
  { cle: 'age', libelle: 'Age percu', valeurs: [
    { valeur: 'jeune', libelle: 'jeune' }, { valeur: 'adulte', libelle: 'adulte' },
    { valeur: 'mur', libelle: 'mûr' }, { valeur: 'vieux', libelle: 'vieux' }] },
  { cle: 'timbre', libelle: 'Timbre', valeurs: [
    { valeur: 'tres_grave', libelle: 'très grave' },
    { valeur: 'grave', libelle: 'grave' }, { valeur: 'medium', libelle: 'médium' },
    { valeur: 'aigu', libelle: 'aigu' }, { valeur: 'tres_aigu', libelle: 'très aigu' },
    { valeur: 'voile', libelle: 'voilé' }] },
];

function fabriquer(annotations) {
  const corps = 'var _annotationsVoix = ' + JSON.stringify(annotations) + ';\n'
    + 'var _criteresVoix = ' + JSON.stringify(CRITERES) + ';\n'
    + 'const FAMILLES_VOIX = ' + JSON.stringify(FAMILLES) + ';\n'
    + CODE + '\nreturn _libelleVoix;';
  return new Function(corps)();
}

const FR = '\uD83C\uDDEB\uD83C\uDDF7';
const GB = '\uD83C\uDDEC\uD83C\uDDE7';
const US = '\uD83C\uDDFA\uD83C\uDDF8';
const CA = '\uD83C\uDDE8\uD83C\uDDE6';
const DE = '\uD83C\uDDE9\uD83C\uDDEA';
const BE = '\uD83C\uDDE7\uD83C\uDDEA';
const IT = '\uD83C\uDDEE\uD83C\uDDF9';
// Les symboles de genre, ecrits AVEC leur selecteur emoji, comme app.js.
const SYM_F = '\u2640\uFE0F';
const SYM_M = '\u2642\uFE0F';

let echecs = 0;
function egal(nom, obtenu, attendu) {
  if (obtenu === attendu) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + '\n         obtenu : ' + obtenu
                + '\n         attendu: ' + attendu);
    echecs++;
  }
}
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail !== undefined ? '  -> ' + detail : ''));
    echecs++;
  }
}

const V = (id, name, region, gender) => ({ id, name, region, gender });

console.log('');
console.log('1) une voix Edge francaise annotees : drapeau, age, timbre, moteur');
egal('Henri (France, mûr grave)',
     fabriquer({ 'fr-FR-HenriNeural': { age: 'mur', timbre: 'grave' } })(
       V('fr-FR-HenriNeural', 'Henri', 'France', 'M')),
     SYM_M + ' Henri ' + FR + ' mûr grave \u2014 ' + ICO_EDGE);

console.log('');
console.log('2) le libelle du timbre vient du serveur (« très aigu », pas « tres_aigu »)');
egal('Rosalie (jeune, très aigu)',
     fabriquer({ 'kokoro:ff_rosalie': { age: 'jeune', timbre: 'tres_aigu' } })(
       V('kokoro:ff_rosalie', 'Rosalie',
         '\uD83C\uDDEB\uD83C\uDDF7 France (NIMM Voix)', 'F')),
     SYM_F + ' Rosalie ' + FR + ' jeune très aigu \u2014 ' + ICO_KOKORO);

console.log('');
console.log('3) le 2e drapeau : la region quand elle en porte un');
egal('une voix americaine',
     fabriquer({})(V('kokoro:af_heart', 'Heart',
                     '\uD83C\uDDFA\uD83C\uDDF8 Etats-Unis', 'F')),
     SYM_F + ' Heart ' + FR + US + ' \u2014 ' + ICO_KOKORO);

console.log('');
console.log('4) le 2e drapeau : l accent NOMME dans la region (XTTS)');
egal('une voix XTTS a accent allemand',
     fabriquer({})(V('xtts:cml1', 'Otto',
                     '\uD83C\uDDEB\uD83C\uDDF7 France (XTTS) - accent allemand', 'M')),
     SYM_M + ' Otto ' + FR + DE + ' \u2014 ' + ICO_XTTS);

console.log('');
console.log('5) le 2e drapeau : l accent ANNOTE par Laurent');
egal('Aurore (accent anglais annote)',
     fabriquer({ 'kokoro:ff_aurore':
                 { accent: 'anglais', age: 'mur', timbre: 'voile' } })(
       V('kokoro:ff_aurore', 'Aurore',
         '\uD83C\uDDEB\uD83C\uDDF7 France (NIMM Voix)', 'F')),
     SYM_F + ' Aurore ' + FR + GB + ' mûr voilé \u2014 ' + ICO_KOKORO);
egal('Nicola (accent italien annote)',
     fabriquer({ 'kokoro:im_nicola':
                 { accent: 'italien', age: 'vieux', timbre: 'grave' } })(
       V('kokoro:im_nicola', 'Nicola', '\uD83C\uDDEE\uD83C\uDDF9 Italie', 'M')),
     SYM_M + ' Nicola ' + FR + IT + ' vieux grave \u2014 ' + ICO_KOKORO);

console.log('');
console.log('6) le 2e drapeau : un pays ecrit en clair (les 12 voix Edge)');
egal('une voix canadienne',
     fabriquer({})(V('fr-CA-SylvieNeural', 'Sylvie', 'Canada', 'F')),
     SYM_F + ' Sylvie ' + FR + CA + ' \u2014 ' + ICO_EDGE);
egal('une voix belge',
     fabriquer({})(V('fr-BE-GerardNeural', 'Gerard', 'Belgique', 'M')),
     SYM_M + ' Gerard ' + FR + BE + ' \u2014 ' + ICO_EDGE);

console.log('');
console.log('7) une voix sans annotation reste propre');
egal('aucun espace en trop',
     fabriquer({})(V('kokoro:ff_chloe', 'Chloé',
                     '\uD83C\uDDEB\uD83C\uDDF7 France (NIMM Voix)', 'F')),
     SYM_F + ' Chloé ' + FR + ' \u2014 ' + ICO_KOKORO);
verifier('aucun espace double dans le libelle',
         fabriquer({})(V('x', 'X', 'France', 'F')).indexOf('  ') < 0);

console.log('');
console.log('8) une valeur inconnue ne casse pas le libelle');
egal('la valeur technique reste lisible',
     fabriquer({ 'x': { age: 'inconnu' } })(V('x', 'X', 'France', 'F')),
     SYM_F + ' X ' + FR + ' inconnu \u2014 ' + ICO_EDGE);

console.log('');
console.log('9) le symbole du genre passe devant le prenom (item du BACKLOG)');
// « H » est la convention des FICHES DE PERSONNAGE (colonne `genre` de la
// table `voices`), « M » celle des CATALOGUES de voix : les deux doivent
// donner le symbole masculin.
egal('un personnage annonce « H » donne bien le symbole masculin',
     fabriquer({})(V('x', 'Henri', 'France', 'H')),
     SYM_M + ' Henri ' + FR + ' \u2014 ' + ICO_EDGE);
// Piege signale d'avance : le genre VIDE ne doit PAS tomber sur « Homme » (ni
// sur son symbole) -- mieux vaut rien qu'un genre faux.
egal('un genre vide n ecrit AUCUN symbole',
     fabriquer({})(V('x', 'Inconnu', 'France', '')),
     'Inconnu ' + FR + ' \u2014 ' + ICO_EDGE);
egal('un genre absent non plus (champ manquant)',
     fabriquer({})(V('x', 'Inconnu', 'France', undefined)),
     'Inconnu ' + FR + ' \u2014 ' + ICO_EDGE);
// Le piege du BACKLOG : sans selecteur emoji, le symbole sort en petit noir et
// blanc. On verifie donc les DEUX points de code, pas seulement le caractere.
const libelleF = fabriquer({})(V('x', 'Eva', 'France', 'F'));
verifier('le symbole feminin porte son selecteur emoji (\\u2640\\uFE0F)',
         libelleF.charCodeAt(0) === 0x2640 && libelleF.charCodeAt(1) === 0xFE0F,
         JSON.stringify(libelleF.slice(0, 3)));
const libelleM = fabriquer({})(V('x', 'Bernd', 'France', 'M'));
verifier('le symbole masculin porte son selecteur emoji (\\u2642\\uFE0F)',
         libelleM.charCodeAt(0) === 0x2642 && libelleM.charCodeAt(1) === 0xFE0F,
         JSON.stringify(libelleM.slice(0, 3)));
verifier('le prenom suit le symbole, apres une seule espace',
         libelleF.slice(2, 4) === ' E' && libelleM.slice(2, 4) === ' B',
         JSON.stringify([libelleF.slice(2, 4), libelleM.slice(2, 4)]));

// ESSAI DU 22/09/2026 — RETIRE, ET POURQUOI (pour ne pas le refaire) : Laurent a
// demande s'il etait possible de FORCER un saut de ligne dans le libelle d'une
// voix (« 1re ligne : Prenom - drapeaux - age et timbre ; 2e ligne : moteur -
// nom du personnage portant la voix / LIBRE »). Mesure : NON -- un libelle qui
// porte un saut de ligne occupe la MEME hauteur qu'un autre, meme avec
// `white-space: pre-line` sur les options (outil de mesure :
// test_voix/test_libelle_deux_lignes_rendu.py). Le saut de ligne et la regle CSS
// ont donc ete retires le jour meme. Il n'y a donc plus rien a verifier ici sur
// ce point : le libelle d'une voix tient sur une ligne, c'est tout.

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);

