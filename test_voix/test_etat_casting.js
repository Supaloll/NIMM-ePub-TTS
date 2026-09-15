// Verifie les badges et le filtre d'etat de la fenetre du casting, SANS
// navigateur (session du 15/09/2026).
// ----------------------------------------------------------------------
// La logique vit dans frontend/app.js (fonction _etatCasting). Ce test
// l'extrait DU FICHIER REEL (jamais une copie : si la fonction est renommee
// ou deplacee, le test echoue bruyamment) et verifie ce qu'elle produit :
//   - « a caster »  : le personnage parle souvent mais porte encore la voix
//                     generique des petits roles -> il n'a pas de voix a lui ;
//   - « partagee »  : sa voix est aussi portee par d'autres personnages ;
//   - un VRAI petit role (peu de repliques, voix generique) ne recoit AUCUN
//     badge : c'est le cas normal, il ne doit pas noyer la liste ;
//   - le filtre « a caster » / « voix partagee » ne garde que les bonnes lignes.
//
// Usage : node test_voix/test_etat_casting.js
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

const debut = source.indexOf('function _etatCasting');
const fin = source.indexOf('function _construireMenuVoix');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : fonction _etatCasting introuvable dans app.js');
  process.exit(1);
}
const codeFonction = source.slice(debut, fin);

// Le seuil des petits roles est LU dans app.js : une seule valeur fait foi,
// et test_voix/test_pool_casting.py verifie qu'elle egale celle du serveur.
const seuil = source.match(/_CAST_MINOR_THRESHOLD\s*=\s*(\d+)/);
const generiques = source.match(/_CAST_VOIX_GENERIQUES\s*=\s*\[([^\]]+)\]/);
if (!seuil || !generiques) {
  console.error('ECHEC : seuil ou voix generiques introuvables dans app.js');
  process.exit(1);
}
const SEUIL = parseInt(seuil[1], 10);
const VOIX_GENERIQUES = generiques[1].split(',').map(s => s.trim().replace(/^'|'$/g, ''));

const fabrique = new Function(
  'const _CAST_MINOR_THRESHOLD = ' + SEUIL + ';\n'
  + 'const _CAST_VOIX_GENERIQUES = ' + JSON.stringify(VOIX_GENERIQUES) + ';\n'
  + codeFonction + '\nreturn _etatCasting;');
const etatCasting = fabrique();

const GENERIQUE_F = VOIX_GENERIQUES[0];
const GENERIQUE_M = VOIX_GENERIQUES[1];

function ligne(nom, voice_id, total) {
  return { nom: nom, v: { voice_id: voice_id }, total: total };
}

// --- Un casting de dix personnages, comme un vrai livre ---
const ROWS = [
  ligne('Principal 1', 'fr-FR-DeniseNeural', 900),   // voix dediee
  ligne('Principal 2', 'xtts:voix1', 700),            // voix dediee
  ligne('Partage 1', 'xtts:voix3', 400),              // meme voix que Partage 2
  ligne('Partage 2', 'xtts:voix3', 350),              // meme voix que Partage 1
  ligne('Sans voix 1', GENERIQUE_M, 120),             // gros role sans voix a lui
  ligne('Sans voix 2', GENERIQUE_F, 60),              // idem, voix feminine
  ligne('Petit role 1', GENERIQUE_F, 2),              // petit role normal
  ligne('Petit role 2', GENERIQUE_M, 1),              // petit role normal
  ligne('Petit role 3', GENERIQUE_F, 3),              // juste sous le seuil
];

console.log('1) detection des personnages « a caster »');
const etat = etatCasting(ROWS, 'T');
verifier('un gros role en voix generique est « a caster »',
         etat.aCaster(ROWS[4]) && etat.aCaster(ROWS[5]));
verifier('un petit role (2 repliques) ne l est PAS', !etat.aCaster(ROWS[6]));
verifier('un personnage juste sous le seuil ne l est PAS', !etat.aCaster(ROWS[8]));
verifier('un role a voix dediee ne l est jamais', !etat.aCaster(ROWS[0]));
verifier('compteur de personnes a caster = 2', etat.nbCaster === 2, etat.nbCaster);

console.log('');
console.log('2) detection des voix partagees');
verifier('les deux personnages au meme timbre sont « partagee »',
         etat.partagee(ROWS[2]) && etat.partagee(ROWS[3]));
verifier('le compte est bien de 2 personnages',
         etat.compteParVoix['xtts:voix3'] === 2, etat.compteParVoix['xtts:voix3']);
verifier('une voix unique n est pas « partagee »', !etat.partagee(ROWS[0]));
verifier('un personnage « a caster » n est pas compte deux fois',
         !etat.partagee(ROWS[4]));
verifier('compteur de voix partagees = 1', etat.nbPartagee === 1, etat.nbPartagee);
// La voix generique des petits roles est partagee par construction : elle ne
// doit jamais etre signalee, sinon la liste serait pleine de faux alertes.
verifier('la voix generique des petits roles n est pas « partagee »',
         etat.compteParVoix[GENERIQUE_F] === undefined
         && !etat.partagee(ROWS[6]) && !etat.partagee(ROWS[7]));

console.log('');
console.log('3) filtre par etat des personnages');
const caster = etatCasting(ROWS, 'caster');
verifier('filtre « a caster » : seulement les bonnes lignes',
         caster.rowsFiltrees.length === 2
         && caster.rowsFiltrees.every(r => r.v.voice_id.indexOf('piper:') === 0),
         caster.rowsFiltrees.map(r => r.nom));
const partagee = etatCasting(ROWS, 'partagee');
verifier('filtre « partagee » : seulement les bonnes lignes',
         partagee.rowsFiltrees.length === 2
         && partagee.rowsFiltrees.every(r => r.v.voice_id === 'xtts:voix3'),
         partagee.rowsFiltrees.map(r => r.nom));
verifier('filtre « Tous » : toutes les lignes',
         etatCasting(ROWS, 'T').rowsFiltrees.length === ROWS.length);

console.log('');
console.log('4) securite (donnees incompletes)');
const bancal = [ligne('Sans voix du tout', '', 50), { nom: 'Vide', v: null, total: 0 }];
let plantage = null;
let etatBancal = null;
try {
  etatBancal = etatCasting(bancal, 'T');
} catch (e) {
  plantage = e.message;
}
verifier('aucun plantage sur une voix vide', plantage === null, plantage);
verifier('une voix vide n est ni « a caster » ni « partagee »',
         etatBancal
         && !etatBancal.aCaster(bancal[0]) && !etatBancal.partagee(bancal[0])
         && !etatBancal.aCaster(bancal[1]));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
