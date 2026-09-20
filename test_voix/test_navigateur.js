// Verifie le NOM DU NAVIGATEUR affiche par le bouton d'installation (20/09/2026).
// ----------------------------------------------------------------------
// Pourquoi ce test : Laurent ne pouvait pas savoir dans quel navigateur il se
// trouvait (constat du 20/09/2026 : une application INSTALLEE n'affiche aucune
// barre d'adresse, donc rien ne dit qui l'heberge). L'application le dit
// maintenant dans la note du bouton « 📲 Installer l'application ».
//
// La fonction est extraite DU FICHIER REEL (jamais recopiee) et interrogee sur
// de VRAIES chaines de navigateurs : c'est le genre de detection qui se casse en
// silence -- et elle sert justement quand quelque chose ne marche pas.
//
// Usage : node test_voix/test_navigateur.js
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

const debut = source.indexOf('function _nomNavigateur');
const fin   = source.indexOf('async function _proposerInstallation');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : _nomNavigateur introuvable dans app.js');
  process.exit(1);
}
const extrait = new Function(source.slice(debut, fin)
  + '\nreturn { _nomNavigateur: _nomNavigateur };')();
const nommer = extrait._nomNavigateur;

// `_appareilMobile` vit juste avant le bouton d'installation.
const debutMobile = source.indexOf('function _appareilMobile');
const finMobile   = source.indexOf('function _majBoutonInstaller');
if (debutMobile < 0 || finMobile <= debutMobile) {
  console.error('ECHEC : _appareilMobile introuvable dans app.js');
  process.exit(1);
}
const mobile = new Function(source.slice(debutMobile, finMobile)
  + '\nreturn _appareilMobile;')();

// Chaines reelles (Android), raccourcies a l'essentiel.
const CHROME  = 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36';
const BRAVE   = 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36';
const FIREFOX = 'Mozilla/5.0 (Android 13; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0';
const SAFARI  = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const EDGE    = 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 EdgA/120.0.0.0';

console.log('');
console.log('1) chaque navigateur est reconnu');
verifier('Chrome', nommer(CHROME) === 'Chrome', nommer(CHROME));
verifier('Firefox (Android)', nommer(FIREFOX) === 'Firefox', nommer(FIREFOX));
verifier('Safari (iPhone)', nommer(SAFARI) === 'Safari', nommer(SAFARI));
// Edge et Brave se presentent comme « Chrome » dans leur chaine : ils doivent
// etre reconnus AVANT.
verifier('Edge (EdgA)', nommer(EDGE) === 'Edge', nommer(EDGE));
verifier('une chaine vide ne casse rien',
         nommer('') === 'ce navigateur', nommer(''));

console.log('');
console.log('1 bis) le bouton d installation ne s adresse qu aux telephones');
const MAC = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15';
const WINDOWS = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
verifier('Android (telephone)',
         mobile('Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 Mobile Safari/537.36') === true);
verifier('iPhone',
         mobile('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile/15E148 Safari/604.1') === true);
verifier('Windows (ordinateur) : pas de bouton', mobile(WINDOWS) === false);
verifier('Mac de bureau : pas de bouton', mobile(MAC, false, 1440) === false);
verifier('iPad qui se declare comme un Mac (toucher + petit ecran)',
         mobile(MAC, true, 820) === true);
verifier('grand ecran tactile (ordinateur) : pas de bouton',
         mobile(WINDOWS, true, 1600) === false);
verifier('le bouton suit bien les deux conditions (deja installee OU ordinateur)',
         source.includes('_applicationInstallee() || !_appareilMobile()'));

console.log('');
console.log('2) le nom sert bien dans la note du bouton');
verifier('la note NOMME le navigateur en cours',
         source.includes("'Installation non proposée ici (tu es dans '")
         && source.includes('+ _nomNavigateur()'));
verifier('elle dit aussi les deux causes possibles',
         source.includes('INTÉGRÉ') && source.includes('ouvre son menu'));
verifier('et elle previent pour Firefox (raccourci seulement)',
         source.includes("n\\'installe") && source.includes("qu\\'un raccourci"));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
