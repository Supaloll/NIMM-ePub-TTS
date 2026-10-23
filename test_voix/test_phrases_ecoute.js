// Verifie le TEXTE D'ECOUTE de la fenetre « Ecouter les voix » (21/10/2026).
// ----------------------------------------------------------------------
// Demande de Laurent : trois lots d'une dizaine de phrases, et trois phrases
// enchainees a chaque ecoute, tirees au hasard -- « ça donnera l'impression
// d'un texte a chaque fois different ». L'oreille ne s'habitue plus a une
// phrase unique, et les trois dimensions d'une voix passent a chaque fois :
// la voix nue, les pieges de prononciation, la prosodie.
//
// Ce que le test protege :
//   1. LA MATIERE : trois lots de dix phrases, toutes differentes, ecrites
//      pour etre LUES par un moteur (pas de didascalie -- le serveur les
//      retire --, pas de « ! », longueur raisonnable), et la phrase de
//      reference du projet (Pharaon) toujours presente dans le lot 2 ;
//   2. LE TIRAGE : une phrase par lot, exactement trois, ordre melange,
//      jamais deux fois le meme texte de suite, les trente phrases sortent
//      vraiment, et les trois lots peuvent ouvrir le texte ;
//   3. LE BRANCHEMENT : `_ecouterVoix` envoie bien ce tirage a /api/tts, et
//      l'ancienne phrase unique (`PHRASE_ECOUTE`) a disparu du fichier.
//
// Tout est extrait du FICHIER REEL (frontend/app.js), jamais recopie : si le
// bloc est renomme ou deplace, le test echoue bruyamment.
//
// Usage : node test_voix/test_phrases_ecoute.js
'use strict';

const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'frontend', 'app.js');
const source = fs.readFileSync(APP, 'utf8');

let echecs = 0;
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail !== undefined ? '  -> ' + detail : ''));
    echecs++;
  }
}

// --- 1. Extraction du bloc, tel qu'il est dans le fichier ---
const debutLots = source.indexOf('const LOTS_PHRASES_ECOUTE');
const finLotsRel = debutLots < 0 ? -1 : source.slice(debutLots).search(/\n\];\r?\n/);
const debutTirage = source.indexOf('let _dernierTexteEcoute');
const finTirageRel = debutTirage < 0 ? -1
  : source.slice(debutTirage).search(/\n\}\r?\n/);

if (debutLots < 0 || finLotsRel < 0 || debutTirage < 0 || finTirageRel < 0) {
  console.error('ECHEC : les lots de phrases ou le tirage sont introuvables dans app.js');
  console.error('       (debutLots=' + debutLots + ' debutTirage=' + debutTirage + ')');
  process.exit(1);
}

const code = source.slice(debutLots, debutLots + finLotsRel + 3) + '\n'
           + source.slice(debutTirage, debutTirage + finTirageRel + 2);

let LOTS_PHRASES_ECOUTE;
let _tirerTexteEcoute;
try {
  const fabrique = new Function(
    code + '\nreturn { LOTS_PHRASES_ECOUTE, _tirerTexteEcoute };');
  ({ LOTS_PHRASES_ECOUTE, _tirerTexteEcoute } = fabrique());
} catch (erreur) {
  console.error('ECHEC : le bloc extrait ne s\'evalue pas (' + erreur.message + ')');
  process.exit(1);
}

// --- 2. La matiere : trois lots de dix phrases ---
console.log('');
console.log('1) trois lots de dix phrases');

verifier('les lots existent', Array.isArray(LOTS_PHRASES_ECOUTE));
verifier('trois lots', LOTS_PHRASES_ECOUTE.length === 3,
         LOTS_PHRASES_ECOUTE.length);
verifier('dix phrases par lot',
         LOTS_PHRASES_ECOUTE.every(lot => Array.isArray(lot) && lot.length === 10),
         LOTS_PHRASES_ECOUTE.map(lot => lot.length).join(' + '));

const TOUTES = LOTS_PHRASES_ECOUTE.reduce((tout, lot) => tout.concat(lot), []);
verifier('trente phrases en tout', TOUTES.length === 30, TOUTES.length);
verifier('aucune phrase en double',
         new Set(TOUTES).size === TOUTES.length,
         TOUTES.length - new Set(TOUTES).size + ' doublon(s)');

const PHARAON = 'Le 24 février 1815, la vigie de Notre-Dame de la Garde signala '
  + 'le trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples.';
verifier('la phrase de reference du projet est toujours la (lot 2)',
         LOTS_PHRASES_ECOUTE[1].indexOf(PHARAON) === 0,
         LOTS_PHRASES_ECOUTE[1][0]);

const problemes = [];
TOUTES.forEach((phrase, rang) => {
  const ou = 'phrase ' + (rang + 1);
  if (typeof phrase !== 'string') {
    problemes.push(ou + ' : pas un texte');
    return;
  }
  if (phrase !== phrase.trim()) problemes.push(ou + ' : espace au bord');
  if (phrase.indexOf('  ') >= 0) problemes.push(ou + ' : double espace');
  if (phrase.length < 20 || phrase.length > 170) {
    problemes.push(ou + ' : longueur ' + phrase.length);
  }
  if (!/[.?!]$/.test(phrase)) problemes.push(ou + ' : pas de ponctuation finale');
  if (!/^[A-Z\u00C0-\u00DE]/.test(phrase)) {
    problemes.push(ou + ' : ne commence pas par une majuscule');
  }
  // Le nettoyage du serveur GARDE « ! » depuis le 04/10/2026 : il fait monter
  // la voix et fausserait la comparaison entre deux voix.
  if (phrase.indexOf('!') >= 0) problemes.push(ou + ' : point d\'exclamation');
  // Guillemets, cadratin, parentheses et point-virgule : le serveur les retire
  // ou les remplace, et le texte perdrait sa ponctuation avant la voix.
  if (/[\u00AB\u00BB\u201C\u201D\u2014;()"]/.test(phrase)) {
    problemes.push(ou + ' : caractere retire par le nettoyage');
  }
  if (/\s:/.test(phrase)) problemes.push(ou + ' : deux-points typographique');
  // Didascalie de parole (« , dit-il, ») : modules/incises.py la retire du
  // texte parle, et la phrase arriverait mutilee au moteur.
  if (/,\s*(dit|répondit|demanda|reprit|ajouta|murmura|s'écria|poursuivit)\b/i
        .test(phrase)) {
    problemes.push(ou + ' : didascalie de parole');
  }
});
verifier('les trente phrases sont propres a etre lues', problemes.length === 0,
         problemes.join(' | '));

// --- 3. Le tirage : une phrase par lot, ordre melange ---
console.log('');
console.log('2) le tirage des trois phrases');

// Les 6000 textes possibles (10 x 10 x 10 combinaisons, six ordres chacune) :
// c'est la liste EXACTE de ce que le tirage a le droit de rendre.
const TOUS_LES_TEXTES = new Set();
LOTS_PHRASES_ECOUTE[0].forEach(a => {
  LOTS_PHRASES_ECOUTE[1].forEach(b => {
    LOTS_PHRASES_ECOUTE[2].forEach(c => {
      const trois = [a, b, c];
      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
          for (let k = 0; k < 3; k++) {
            if (i === j || j === k || i === k) continue;
            TOUS_LES_TEXTES.add([trois[i], trois[j], trois[k]].join(' '));
          }
        }
      }
    });
  });
});
verifier('6000 textes possibles (1000 combinaisons x 6 ordres)',
         TOUS_LES_TEXTES.size === 6000, TOUS_LES_TEXTES.size);

// Analyse d'un tirage : quel numero de phrase vient de chaque lot, et le texte
// est-il EXACTEMENT ces trois phrases (rien de perdu, rien en trop), dans
// l'ordre ou on les entend ?
function analyser(texte) {
  const numeros = LOTS_PHRASES_ECOUTE.map(
    lot => lot.findIndex(phrase => texte.indexOf(phrase) >= 0));
  const places = [];
  numeros.forEach((numero, lot) => {
    if (numero >= 0) {
      const phrase = LOTS_PHRASES_ECOUTE[lot][numero];
      places.push({ position: texte.indexOf(phrase), phrase });
    }
  });
  // L'ordre qui compte est celui du TEXTE (le tirage melange les lots), pas
  // celui des lots : on remet les trois phrases bout a bout dans l'ordre ou
  // elles apparaissent, et le resultat doit etre le texte, au caractere pres.
  places.sort((a, b) => a.position - b.position);
  const exact = places.length === 3
    && places[0].position === 0
    && places.map(place => place.phrase).join(' ') === texte;
  return { numeros, exact };
}

const TIRAGES = 400;
const vus = new Set();
const numerosVus = LOTS_PHRASES_ECOUTE.map(() => new Set());
const premiersLots = new Set();
let horsListe = '';
let inexacts = '';
let suitesIdentiques = '';
let precedent = '';
let troisPhrases = true;

for (let n = 0; n < TIRAGES; n++) {
  const texte = _tirerTexteEcoute();
  if (!TOUS_LES_TEXTES.has(texte) && !horsListe) horsListe = texte;
  const detail = analyser(texte);
  if (!detail.exact && !inexacts) inexacts = texte;
  if (detail.numeros.some(numero => numero < 0)) troisPhrases = false;
  if (texte === precedent && !suitesIdentiques) suitesIdentiques = texte;
  precedent = texte;
  vus.add(texte);
  detail.numeros.forEach((numero, lot) => {
    if (numero >= 0) numerosVus[lot].add(numero);
  });
  // L'ordre se lit sur le lot de la phrase qui OUVRE le texte.
  const premier = detail.numeros.findIndex((numero, lot) => numero >= 0
    && texte.indexOf(LOTS_PHRASES_ECOUTE[lot][numero]) === 0);
  if (premier >= 0) premiersLots.add(String(premier));
}

verifier('chaque tirage est un des 6000 textes possibles', !horsListe, horsListe);
verifier('chaque tirage fait exactement trois phrases, rien de plus',
         !inexacts, inexacts);
verifier('une phrase par lot, dans les ' + TIRAGES + ' tirages', troisPhrases);
verifier('jamais deux fois le meme texte de suite', !suitesIdentiques,
         suitesIdentiques);
verifier('les trente phrases sortent vraiment',
         numerosVus.every(numeros => numeros.size === 10),
         numerosVus.map(numeros => numeros.size).join(' + '));
verifier('les trois lots peuvent ouvrir le texte',
         premiersLots.size === 3, [...premiersLots].join(', '));
verifier('les tirages sont varies (plus de 250 textes differents sur 400)',
         vus.size > 250, vus.size);

// --- 4. Le branchement dans la page ---
console.log('');
console.log('3) le branchement dans la fenetre « Ecouter les voix »');

const debutEcoute = source.indexOf('async function _ecouterVoix');
const finEcoute = source.indexOf('function _listeOptions', debutEcoute);
const corpsEcoute = (debutEcoute < 0 || finEcoute <= debutEcoute)
  ? '' : source.slice(debutEcoute, finEcoute);

verifier('_ecouterVoix existe', corpsEcoute.length > 0);
verifier('_ecouterVoix envoie le tirage a /api/tts',
         corpsEcoute.indexOf('text: _tirerTexteEcoute()') >= 0);
verifier('_ecouterVoix ne fait qu\'un seul appel au moteur (un texte, pas trois)',
         (corpsEcoute.match(/\/api\/tts/g) || []).length === 1,
         (corpsEcoute.match(/\/api\/tts/g) || []).length);
verifier('l\'ancienne phrase unique a disparu du fichier',
         source.indexOf('PHRASE_ECOUTE') < 0);
verifier('l\'infobulle annonce les trois phrases',
         source.indexOf('3 phrases tirees au hasard') >= 0);

console.log('');
console.log(echecs === 0
  ? 'TOUT EST OK (' + TOUTES.length + ' phrases, ' + TOUS_LES_TEXTES.size
    + ' textes possibles)'
  : echecs + ' CONTROLE(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
