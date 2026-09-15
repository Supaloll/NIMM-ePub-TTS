// Verifie QUAND le message audio « pas de reseau » doit se declencher
// (idee de Laurent, 15/09/2026), SANS navigateur.
// ----------------------------------------------------------------------
// La decision vit dans frontend/app.js (_fautPrevenirReseau). Ce test extrait
// la fonction DU FICHIER REEL et verifie les regles voulues :
//   - rien tant que le message n'a pas pu etre prepare (on ne joue rien) ;
//   - une PREMIERE annonce apres quelques secondes d'attente ;
//   - puis au plus une annonce toutes les MESSAGE_RAPPEL_MS (on ne harcele pas) ;
//   - et jamais deux fois au meme moment.
//
// Usage : node test_voix/test_message_reseau.js
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

const debut = source.indexOf('function _fautPrevenirReseau');
const fin = source.indexOf('function _prevenirReseauCoupe');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : fonction _fautPrevenirReseau introuvable dans app.js');
  process.exit(1);
}
const codeFonction = source.slice(debut, fin);

// Les constantes sont lues dans app.js : une seule source de verite.
function constante(nom) {
  const m = source.match(new RegExp(nom + '\\s*=\\s*(\\d+)'));
  if (!m) {
    console.error('ECHEC : constante ' + nom + ' introuvable dans app.js');
    process.exit(1);
  }
  return parseInt(m[1], 10);
}
const ATTENTES = constante('MESSAGE_ATTENTES_AVANT');
const RAPPEL   = constante('MESSAGE_RAPPEL_MS');
console.log('  (constantes lues dans app.js : ' + ATTENTES + ' attentes avant la'
            + ' 1re annonce, rappel toutes les ' + (RAPPEL / 1000) + ' s)');

function preparer(messagePret) {
  const corps = 'var _messageHorsLigne = ' + (messagePret ? '"blob:test"' : 'null') + ';\n'
    + 'var MESSAGE_ATTENTES_AVANT = ' + ATTENTES + ';\n'
    + 'var MESSAGE_RAPPEL_MS = ' + RAPPEL + ';\n'
    + codeFonction + '\nreturn _fautPrevenirReseau;';
  return new Function(corps)();
}

console.log('');
console.log('1) message pas encore prepare : on ne joue rien');
const rien = preparer(false);
verifier('aucune annonce, meme apres beaucoup d attentes',
        !rien(1, 0, 0) && !rien(ATTENTES, 0, 0) && !rien(50, 0, 999999));

console.log('');
console.log('2) message prepare : premiere annonce apres le seuil');
const faut = preparer(true);
verifier('pas d annonce a la 1re attente (on laisse le reseau revenir)',
        !faut(1, 0, 0));
verifier('annonce a la ' + ATTENTES + 'e attente', faut(ATTENTES, 0, 0));
verifier('pas de doublon juste apres (meme attente)',
        !faut(ATTENTES + 1, 0, 1000));

console.log('');
console.log('3) longue coupure : on rappelle, mais sans harceler');
verifier('pas de rappel avant le delai', !faut(8, 0, RAPPEL - 1000));
verifier('rappel une fois le delai ecoule', faut(8, 0, RAPPEL));
verifier('le rappel fonctionne aussi tres loin dans la coupure',
        faut(30, 0, RAPPEL + 60000));

console.log('');
console.log('4) apres une annonce recente, silence');
verifier('aucun rappel 5 s apres une annonce', !faut(12, 5000, 10000));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
