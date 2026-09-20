// Verifie que la VOIX DU NARRATEUR appartient bien a CHAQUE LIVRE (20/09/2026).
// ----------------------------------------------------------------------
// Constat de Laurent : « la voix narrateur passe d'un livre a l'autre ; chaque
// livre devrait avoir son narrateur ». Deux defauts corriges ce jour-la :
//   1. un livre SANS voix enregistree gardait celle du livre precedent ;
//   2. une voix enregistree indisponible (moteur eteint) etait remplacee EN
//      SILENCE par la voix du livre precedent.
// Meme technique que les autres tests : le bloc est extrait DU FICHIER REEL
// (jamais recopie : renomme ou deplace, le test echoue bruyamment), avec un
// faux DOM minimal et un faux fetch.
//
// Usage : node test_voix/test_narrateur_par_livre.js
'use strict';

const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'frontend', 'app.js');
const source = fs.readFileSync(APP, 'utf8');

const debut = source.indexOf('const NARRATEUR_VOIX_DEFAUT');
let fin = source.indexOf("document.getElementById('voice-select').addEventListener('change'");
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : bloc de la voix du narrateur introuvable dans app.js');
  process.exit(1);
}
const codeBloc = source.slice(debut, fin);

const ARIANE = 'fr-CH-ArianeNeural';
const KYUTAI = 'kyutai:12205_11650_000004-0002';

// Catalogue tel que /api/voices le renvoie quand le moteur Kyutai est ETEINT.
const CATALOGUE_EDGE = [
  { id: ARIANE, name: 'Ariane', gender: 'F', region: 'Suisse' },
  { id: 'fr-FR-HenriNeural', name: 'Henri', gender: 'M', region: 'France' },
];
// ... et tel qu'il l'est quand le moteur est ALLUME.
const CATALOGUE_AVEC_KYUTAI = CATALOGUE_EDGE.concat([
  { id: KYUTAI, name: 'Eleonore', gender: 'F', region: 'France (Kyutai)' },
]);

let echecs = 0;
function verifier(description, condition, valeur) {
  if (condition) {
    console.log('  OK    ' + description);
  } else {
    echecs++;
    console.log('  ECHEC ' + description + '  ->  ' + String(valeur));
  }
}

// Execute le VRAI code du narrateur pour le livre ouvert.
function restaurer(voixEnregistree, livreId, catalogue) {
  const select = { value: 'valeur-du-livre-precedent' };
  const message = { textContent: 'message-du-livre-precedent' };
  const appels = [];
  const fauxDocument = {
    getElementById(id) {
      if (id === 'voice-select') return select;
      if (id === 'narrateur-etat') return message;
      return null;
    },
  };
  const fauxFetch = (url, options) => {
    appels.push({ url: url, corps: options && options.body });
    return { catch() {} };
  };
  const corps = 'var _currentBookId = ' + JSON.stringify(livreId) + ';\n'
    + 'var _currentUserId = 7;\n'
    + 'var _currentBookData = ' + JSON.stringify({ narrator_voice: voixEnregistree }) + ';\n'
    + codeBloc + '\n'
    + '_restaurerVoixNarrateur(' + JSON.stringify(voixEnregistree) + ');\n'
    + 'return { choix: _currentBookData.narrator_voice };';
  const fabrique = new Function('document', '_allVoices', 'fetch', corps);
  const resultat = fabrique(fauxDocument, catalogue, fauxFetch);
  return {
    voixMenus: select.value,
    memoire: resultat.choix,
    message: message.textContent,
    appels: appels,
  };
}

console.log('1) un livre SANS voix de narrateur enregistree');
let a = restaurer(null, 14, CATALOGUE_EDGE);
verifier('le menu repart sur la voix par defaut (Ariane)', a.voixMenus === ARIANE, a.voixMenus);
verifier('la voix n\'est plus celle du livre precedent',
  a.voixMenus !== 'valeur-du-livre-precedent', a.voixMenus);
verifier('la memoire du livre est mise a jour', a.memoire === ARIANE, a.memoire);
verifier('la valeur est ENREGISTREE pour ce livre (1 appel)', a.appels.length === 1,
  a.appels.length);
verifier('l\'appel vise le livre ouvert et son proprietaire',
  a.appels[0] && a.appels[0].url === '/api/books/14/narrator?user_id=7',
  a.appels[0] && a.appels[0].url);
verifier('et envoie bien la voix par defaut',
  a.appels[0] && a.appels[0].corps === JSON.stringify({ voice: ARIANE }),
  a.appels[0] && a.appels[0].corps);
verifier('aucun message affiche (tout va bien)', a.message === '', a.message);

console.log('1 bis) le meme livre, ouvert une seconde fois');
let ab = restaurer(ARIANE, 14, CATALOGUE_EDGE);
verifier('sa voix est retrouvee', ab.voixMenus === ARIANE, ab.voixMenus);
verifier('plus aucune ecriture (elle est deja enregistree)', ab.appels.length === 0,
  ab.appels.length);

console.log('2) un livre AVEC sa voix, et cette voix est disponible');
let b = restaurer('fr-FR-HenriNeural', 27, CATALOGUE_EDGE);
verifier('le menu retrouve SA voix', b.voixMenus === 'fr-FR-HenriNeural', b.voixMenus);
verifier('aucune ecriture inutile', b.appels.length === 0, b.appels.length);
verifier('aucun message', b.message === '', b.message);

console.log('3) un livre AVEC sa voix, mais son moteur est ETEINT (voix Kyutai)');
let c = restaurer(KYUTAI, 28, CATALOGUE_EDGE);
verifier('le menu ne garde PAS la voix du livre precedent',
  c.voixMenus === ARIANE, c.voixMenus);
verifier('le choix du livre n\'est PAS ecrase (il revient au rallumage)',
  c.memoire === KYUTAI, c.memoire);
verifier('aucune ecriture en base (le choix reste acquis)', c.appels.length === 0,
  c.appels.length);
verifier('le message est AFFICHE', c.message.length > 0, c.message);
verifier('le message nomme la voix du livre', c.message.indexOf(KYUTAI) > 0, c.message);
verifier('le message dit que le moteur est eteint',
  c.message.indexOf('moteur') > 0 && c.message.indexOf('\u00e9teint') > 0, c.message);

console.log('3 bis) le moteur est rallume : SA voix revient');
let cb = restaurer(KYUTAI, 28, CATALOGUE_AVEC_KYUTAI);
verifier('le menu retrouve la voix Kyutai du livre', cb.voixMenus === KYUTAI, cb.voixMenus);
verifier('le message disparait', cb.message === '', cb.message);
verifier('aucune ecriture', cb.appels.length === 0, cb.appels.length);

console.log('4) aucun livre ouvert (aucun silence dangereux)');
let d = restaurer(null, null, CATALOGUE_EDGE);
verifier('le menu repart quand meme sur la voix par defaut',
  d.voixMenus === ARIANE, d.voixMenus);
verifier('aucun appel reseau sans livre', d.appels.length === 0, d.appels.length);

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
