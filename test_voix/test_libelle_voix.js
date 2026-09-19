// Verifie le LIBELLE d'une voix dans les menus (demande de Laurent, 19/09/2026).
// ---------------------------------------------------------------------------
// Format demande :
//   « [Prenom] [drapeau de la langue] [2e drapeau eventuel] [Age] [Timbre] — [Moteur] »
// soit « Alice <FR> Jeune aigu — Kyutai » et « Amelie <FR><GB> Mure grave — Kokoro ».
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
//   6. le moteur est nomme comme dans le reste du lecteur.
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
  extraire('function _libelleCritere', 'function _libelleVoix'),
  extraire('function _libelleVoix', 'async function loadMoteurs'),
  extraire('function _familleDeVoix', 'function _libelleFamille'),
  extraire('function _libelleFamille', 'async function _chargerAnnotationsVoix'),
].join('\n');

// La famille des moteurs, telle que la page la declare (libelles compris).
const FAMILLES = [['edge', 'Edge (en ligne)'], ['kokoro', 'Kokoro'],
                  ['piper', 'Piper'], ['kyutai', 'Kyutai'],
                  ['xtts', 'XTTS v2'], ['neutts', 'NeuTTS']];

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
     'Henri ' + FR + ' mûr grave \u2014 Edge (en ligne)');

console.log('');
console.log('2) le libelle du timbre vient du serveur (« très aigu », pas « tres_aigu »)');
egal('Rosalie (jeune, très aigu)',
     fabriquer({ 'kokoro:ff_rosalie': { age: 'jeune', timbre: 'tres_aigu' } })(
       V('kokoro:ff_rosalie', 'Rosalie',
         '\uD83C\uDDEB\uD83C\uDDF7 France (NIMM Voix)', 'F')),
     'Rosalie ' + FR + ' jeune très aigu \u2014 Kokoro');

console.log('');
console.log('3) le 2e drapeau : la region quand elle en porte un');
egal('une voix americaine',
     fabriquer({})(V('kokoro:af_heart', 'Heart',
                     '\uD83C\uDDFA\uD83C\uDDF8 Etats-Unis', 'F')),
     'Heart ' + FR + US + ' \u2014 Kokoro');

console.log('');
console.log('4) le 2e drapeau : l accent NOMME dans la region (XTTS)');
egal('une voix XTTS a accent allemand',
     fabriquer({})(V('xtts:cml1', 'Otto',
                     '\uD83C\uDDEB\uD83C\uDDF7 France (XTTS) - accent allemand', 'M')),
     'Otto ' + FR + DE + ' \u2014 XTTS v2');

console.log('');
console.log('5) le 2e drapeau : l accent ANNOTE par Laurent');
egal('Aurore (accent anglais annote)',
     fabriquer({ 'kokoro:ff_aurore':
                 { accent: 'anglais', age: 'mur', timbre: 'voile' } })(
       V('kokoro:ff_aurore', 'Aurore',
         '\uD83C\uDDEB\uD83C\uDDF7 France (NIMM Voix)', 'F')),
     'Aurore ' + FR + GB + ' mûr voilé \u2014 Kokoro');
egal('Nicola (accent italien annote)',
     fabriquer({ 'kokoro:im_nicola':
                 { accent: 'italien', age: 'vieux', timbre: 'grave' } })(
       V('kokoro:im_nicola', 'Nicola', '\uD83C\uDDEE\uD83C\uDDF9 Italie', 'M')),
     'Nicola ' + FR + IT + ' vieux grave \u2014 Kokoro');

console.log('');
console.log('6) le 2e drapeau : un pays ecrit en clair (les 12 voix Edge)');
egal('une voix canadienne',
     fabriquer({})(V('fr-CA-SylvieNeural', 'Sylvie', 'Canada', 'F')),
     'Sylvie ' + FR + CA + ' \u2014 Edge (en ligne)');
egal('une voix belge',
     fabriquer({})(V('fr-BE-GerardNeural', 'Gerard', 'Belgique', 'M')),
     'Gerard ' + FR + BE + ' \u2014 Edge (en ligne)');

console.log('');
console.log('7) une voix sans annotation reste propre');
egal('aucun espace en trop',
     fabriquer({})(V('kokoro:ff_chloe', 'Chloé',
                     '\uD83C\uDDEB\uD83C\uDDF7 France (NIMM Voix)', 'F')),
     'Chloé ' + FR + ' \u2014 Kokoro');
verifier('aucun espace double dans le libelle',
         fabriquer({})(V('x', 'X', 'France', 'F')).indexOf('  ') < 0);

console.log('');
console.log('8) une valeur inconnue ne casse pas le libelle');
egal('la valeur technique reste lisible',
     fabriquer({ 'x': { age: 'inconnu' } })(V('x', 'X', 'France', 'F')),
     'X ' + FR + ' inconnu \u2014 Edge (en ligne)');

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);

