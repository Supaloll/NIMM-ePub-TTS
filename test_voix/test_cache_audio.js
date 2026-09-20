// Verifie le LIBELLE du bouton « Vider le cache » (20/09/2026).
// ----------------------------------------------------------------------
// Demande de Laurent (18/09/2026) : un bouton pour vider le cache audio a la
// main, AVEC le compte affiche (« 604 Mo sur 2 Go »).
//
// Les deux fonctions sont extraites DU FICHIER REEL (jamais recopiees : si
// l'une est renommee ou deplacee, le test echoue bruyamment) :
//   - `_formatOctets` : la taille lisible (« 604 Mo », « 1,2 Go », « 12 Ko ») ;
//   - `_libelleBoutonCache` : le texte du bouton, qui ne doit JAMAIS afficher
//     « undefined » ni un chiffre faux quand le serveur n'a pas encore repondu.
//
// L'autre moitie de la verification (le compte et la purge, cote serveur) est
// dans `test_voix/test_cache_audio.py`, qui travaille sur un cache bidon.
//
// Usage : node test_voix/test_cache_audio.js
'use strict';

const fs = require('fs');
const path = require('path');

const source = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'app.js'), 'utf8');

let echecs = 0;
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail !== undefined ? '  -> ' + detail : ''));
    echecs++;
  }
}
function egal(nom, obtenu, attendu) {
  verifier(nom, obtenu === attendu, JSON.stringify(obtenu)
                                    + ' au lieu de ' + JSON.stringify(attendu));
}

// De `_formatOctets` a la fonction suivante : les deux vivent ensemble.
const debut = source.indexOf('function _formatOctets');
const fin   = source.indexOf('async function _chargerEtatCache');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : les fonctions du cache sont introuvables dans app.js');
  process.exit(1);
}
const api = new Function(
  source.slice(debut, fin)
  + '\nreturn { _formatOctets: _formatOctets,'
  + ' _libelleBoutonCache: _libelleBoutonCache };')();
const octets = api._formatOctets;
const libelle = api._libelleBoutonCache;

console.log('');
console.log('1) la taille lisible');
egal('zero octet', octets(0), '0 o');
egal('quelques octets', octets(512), '512 o');
egal('des kilo-octets', octets(2048), '2 Ko');
egal('des mega-octets (le cas courant)', octets(604 * 1024 * 1024), '604 Mo');
egal('des giga-octets, avec une virgule francaise',
     octets(Math.round(1.2 * 1024 * 1024 * 1024)), '1,2 Go');
egal('une valeur absente ne casse rien', octets(undefined), '0 o');
egal('une valeur nulle non plus', octets(null), '0 o');

console.log('');
console.log('2) le libelle du bouton');
const ICONE = '\uD83E\uDDF9';
egal('avec un compte connu : la taille est ecrite',
     libelle({ octets: 604 * 1024 * 1024 }), ICONE + ' Vider le cache (604 Mo)');
egal('un compte a zero s ecrit aussi (0 o)',
     libelle({ octets: 0 }), ICONE + ' Vider le cache (0 o)');
// LE point important : au demarrage, le serveur n'a pas encore repondu. Le
// bouton doit rester propre, jamais « undefined Mo ».
egal('serveur pas encore repondu : aucune taille inventee',
     libelle(null), ICONE + ' Vider le cache');
egal('etat vide : idem',
     libelle({}), ICONE + ' Vider le cache');
egal('valeur non numerique : idem',
     libelle({ octets: 'beaucoup' }), ICONE + ' Vider le cache');
verifier('jamais le mot « undefined » dans le bouton',
         libelle(null).indexOf('undefined') < 0
         && libelle({ octets: 'beaucoup' }).indexOf('undefined') < 0);
verifier('le bouton dit toujours ce qu il fait',
         libelle(null).indexOf('Vider le cache') > 0);

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
