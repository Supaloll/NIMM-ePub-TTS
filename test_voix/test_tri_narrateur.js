// Verifie l'ORDRE du MENU DU NARRATEUR (demande de Laurent, 30/09/2026).
// ----------------------------------------------------------------------
// Demande, mot pour mot : « Pour le narrateur, il faudrait trier les voix par :
// 1 : moteur  2 : Genre  3 : Ordre alphabetique ».
//
// Avant, le menu suivait l'ordre du serveur (`/api/voices`) : groupe par moteur,
// oui, mais dans l'ordre de declaration du catalogue a l'interieur -- donc ni
// genre, ni alphabet.
//
// Ce que le test verifie :
//   1. le MENU utilise bien ce tri (garde de branchement : le jour ou quelqu'un
//      remet le `forEach` d'origine, le test echoue) ;
//   2. l'ordre des MOTEURS est celui de FAMILLES_VOIX (Edge en tete, puis
//      Kyutai, XTTS, Qwen...), et une famille hors liste se range avec Edge --
//      c'est la regle de `_familleDeVoix`, pas un rang inventé ici ;
//   3. le GENRE separe Femmes, puis Hommes, puis les voix sans genre connu ;
//   4. le PRENOM suit l'alphabet FRANCAIS : « Edouard » se range a E, donc
//      AVANT « Emile » (sans le 'fr', les accents partent apres Z -- piege
//      classique de `localeCompare`).
//
// Meme technique que les autres tests : la fonction est extraite DU FICHIER
// REEL (jamais recopiee : renommee ou deplacee, le test echoue bruyamment).
//
// Usage : node test_voix/test_tri_narrateur.js
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
  extraire('const FAMILLES_VOIX', 'let _annotationsVoix'),
  extraire('function _familleDeVoix', 'function _libelleFamille'),
  extraire('function _ordreMenuNarrateur', 'async function loadVoices'),
].join('\n');

const comparateur = new Function(CODE + '\nreturn _ordreMenuNarrateur;')();

let echecs = 0;
function verifier(description, condition, valeur) {
  if (condition) {
    console.log('  OK    ' + description);
  } else {
    echecs++;
    console.log('  ECHEC ' + description + '  ->  ' + String(valeur));
  }
}

function trier(tableau) {
  return tableau.slice().sort(comparateur).map(v => v.name).join(' | ');
}

const KYUTAI = 'kyutai:12205_11650_000004-0002';
const XTTS = 'xtts:dp_femme001';

console.log('1) le menu du narrateur utilise bien ce tri');
verifier('loadVoices trie la liste avant de remplir le menu',
  source.indexOf('.slice().sort(_ordreMenuNarrateur)') > 0);

console.log('2) l ordre des MOTEURS (FAMILLES_VOIX, Edge en tete)');
let melange = [
  { id: 'qwen:cml3344', name: 'Honore', gender: 'M' },
  { id: XTTS, name: 'Marthe', gender: 'F' },
  { id: KYUTAI, name: 'Eleonore', gender: 'F' },
  { id: 'fr-FR-HenriNeural', name: 'Henri', gender: 'M' },
  { id: 'fr-CH-ArianeNeural', name: 'Ariane', gender: 'F' },
];
verifier('Edge, puis Kyutai, puis XTTS, puis Qwen',
  trier(melange) === 'Ariane | Henri | Eleonore | Marthe | Honore',
  trier(melange));

console.log('2 bis) une famille hors liste se range avec EDGE (regle de _familleDeVoix)');
let avecInconnue = [
  { id: 'inconnu:zzz', name: 'Zoe', gender: 'F' },
  { id: 'fr-FR-HenriNeural', name: 'Henri', gender: 'M' },
  { id: KYUTAI, name: 'Eleonore', gender: 'F' },
];
verifier('elle est traitee comme Edge, pas rejetee en fin de liste',
  trier(avecInconnue) === 'Zoe | Henri | Eleonore', trier(avecInconnue));

console.log('3) le GENRE : Femmes, puis Hommes, puis sans genre connu');
let genres = [
  { id: 'qwen:cml3344', name: 'Honore', gender: 'M' },
  { id: 'qwen:cml2033', name: 'Lucie', gender: 'F' },
  { id: 'qwen:cml7377', name: 'Ernest', gender: '' },
  { id: 'qwen:cml1869', name: 'Cecile', gender: 'F' },
];
verifier('Cecile, Lucie (F) puis Honore (M) puis Ernest (sans genre)',
  trier(genres) === 'Cecile | Lucie | Honore | Ernest', trier(genres));

console.log('4) le PRENOM en alphabet FRANCAIS (accents compris)');
let accents = [
  { id: 'qwen:cml9804', name: 'Émile', gender: 'M' },
  { id: 'qwen:cml1649', name: 'Edouard', gender: 'M' },
  { id: 'qwen:cml3344', name: 'Achille', gender: 'M' },
];
verifier('« Edouard » avant « Émile » (l accent ne le renvoie pas apres Z)',
  trier(accents) === 'Achille | Edouard | Émile', trier(accents));

console.log('5) un menu deja range ne bouge pas, et la voix choisie reste la meme');
let deuxFois = trier(melange) === trier(melange.slice().reverse());
verifier('le tri ne depend pas de l ordre d arrivee', deuxFois);

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
