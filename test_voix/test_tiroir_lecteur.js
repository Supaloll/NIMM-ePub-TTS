// Verifie le TIROIR DU MENU DU LECTEUR (22/09/2026).
// ---------------------------------------------------
// Demande de Laurent : « Pour le menu du bas, on va faire un tiroir. Il faut
// afficher uniquement les boutons de lecture [...]. Dessous, tout le reste du
// menu qui s'ouvre en ouvrant ce menu tiroir. »
//
// Ce que ce test protege, en trois parties :
//   1. la REGLE d'affichage (`_tiroirLecteurDoitEtreOuvert`, extraite DU
//      FICHIER REEL : renommee ou deplacee, le test echoue bruyamment) : replie
//      sur telephone, ouvert sur ordinateur -- et TOUJOURS le choix de Laurent
//      quand il a touche a la poignee ;
//   2. la PAGE : la poignee existe, elle est bien ENTRE la barre de lecture et
//      les reglages, les sept commandes de lecture sont d'un cote et tout le
//      reste de l'autre (c'est exactement ce que Laurent a demande) ;
//   3. le BRANCHEMENT : le clic, l'etat a l'entree dans le lecteur, et le CSS
//      qui dessine l'etat (chevron retourne, poignee masquee sur ordinateur).
//
// Usage : node test_voix/test_tiroir_lecteur.js
'use strict';

const fs = require('fs');
const path = require('path');

const RACINE = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(RACINE, 'frontend', 'app.js'), 'utf8');
const html   = fs.readFileSync(path.join(RACINE, 'frontend', 'index.html'), 'utf8');
const css    = fs.readFileSync(path.join(RACINE, 'frontend', 'styles.css'), 'utf8');

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

// --- 1) La fonction pure, extraite du fichier reel -------------------------
const debutEcran = source.indexOf('function _castEcranEtroit');
const finEcran   = source.indexOf('// Le tiroir des reglages doit-il etre ouvert ?');
const debutTiroir = source.indexOf('function _tiroirLecteurDoitEtreOuvert');
const finTiroir   = source.indexOf('// Applique l\'etat a l\'ecran');
if (debutEcran < 0 || finEcran <= debutEcran
    || debutTiroir < 0 || finTiroir <= debutTiroir) {
  console.error('ECHEC : les fonctions du tiroir sont introuvables dans app.js');
  process.exit(1);
}
const api = new Function(
  source.slice(debutEcran, finEcran) + '\n' + source.slice(debutTiroir, finTiroir)
  + '\nreturn { _castEcranEtroit: _castEcranEtroit,'
  + ' _tiroirLecteurDoitEtreOuvert: _tiroirLecteurDoitEtreOuvert };')();

console.log('');
console.log('1) la frontiere « etroit », telle qu elle est ecrite dans app.js');
egal('640 px (telephone large) : etroit', api._castEcranEtroit(640), true);
egal('641 px : ce n est plus etroit',     api._castEcranEtroit(641), false);

console.log('');
console.log('2) sans choix de Laurent, le tiroir suit la taille de l ecran');
egal('sur un telephone (360 px) : replie',
     api._tiroirLecteurDoitEtreOuvert(null, 360), false);
egal('sur un ordinateur (1200 px) : ouvert',
     api._tiroirLecteurDoitEtreOuvert(null, 1200), true);
egal('a la frontiere exacte (640 px) : replie',
     api._tiroirLecteurDoitEtreOuvert(null, 640), false);
egal('a 641 px : ouvert',
     api._tiroirLecteurDoitEtreOuvert(null, 641), true);
// Aucune mesure disponible (node, ou navigateur muet) : on replie. Un tiroir
// ouvert par erreur prendrait la place du texte, alors qu'un tiroir replie ne
// coute qu'un tap.
egal('sans aucune mesure : replie, jamais ouvert par erreur',
     api._tiroirLecteurDoitEtreOuvert(null, undefined), false);

console.log('');
console.log('3) le choix de Laurent l emporte, meme sur l autre ecran');
egal('ouvert a la main sur un telephone : il reste ouvert',
     api._tiroirLecteurDoitEtreOuvert(true, 360), true);
egal('replie a la main sur un ordinateur : il reste replie',
     api._tiroirLecteurDoitEtreOuvert(false, 1200), false);

// --- 2) La page -----------------------------------------------------------
console.log('');
console.log('4) dans la page : la poignee sert de frontiere');
const posFooter   = html.indexOf('id="reader-footer"');
const posNav      = html.indexOf('id="reader-nav"');
const posPoignee  = html.indexOf('id="reader-tiroir-btn"');
const posReglages = html.indexOf('id="reader-settings"');
verifier('la poignee existe dans la page', posPoignee > 0);
verifier('elle est APRES la barre de lecture',
         posPoignee > posNav && posNav > posFooter, posNav + ' / ' + posPoignee);
verifier('elle est AVANT les reglages',
         posPoignee < posReglages, posPoignee + ' / ' + posReglages);
verifier('elle annonce ce qu elle ouvre (aria-controls)',
         /id="reader-tiroir-btn"[\s\S]{0,200}aria-controls="reader-settings"/.test(html));
verifier('elle n est pas cachee dans la page : le script decide au premier affichage',
         !/id="reader-tiroir-btn"[^>]*class="[^"]*hidden/.test(html)
         && !/class="[^"]*hidden[^"]*"[^>]*id="reader-tiroir-btn"/.test(html));

// Les SEPT commandes de lecture : dans la barre, et rien qu'elles au-dessus de
// la poignee -- c'est le partage demande par Laurent.
console.log('');
console.log('5) les sept commandes de lecture restent au-dessus de la poignee');
['prev-btn', 'para-prev-btn', 'sent-prev-btn', 'tts-play-btn',
 'sent-next-btn', 'para-next-btn', 'next-btn'].forEach(id => {
  const p = html.indexOf('id="' + id + '"');
  verifier('#' + id + ' est dans la barre de lecture',
           p > posNav && p < posPoignee, p);
});

console.log('');
console.log('6) tout le reste du menu est range sous la poignee');
['multivoice-btn', 'voices-open-btn', 'bookmarks-open-btn', 'rsvp-open-btn',
 'cache-open-btn', 'voice-select', 'speed-select', 'reparer-open-btn'].forEach(id => {
  const p = html.indexOf('id="' + id + '"');
  verifier('#' + id + ' est dans #reader-settings', p > posReglages, p);
});

// --- 3) Le branchement ----------------------------------------------------
console.log('');
console.log('7) le code branche la poignee');
verifier('l etat part de null (aucun choix de Laurent au depart)',
         /let _tiroirLecteurOuvert = null;/.test(source));
verifier('la poignee a bien son clic',
         source.includes("getElementById('reader-tiroir-btn').addEventListener('click'"));
verifier('le clic INVERSE l etat courant (et ne le fige pas)',
         /_tiroirLecteurOuvert = !_tiroirLecteurDoitEtreOuvert\(_tiroirLecteurOuvert\);/
           .test(source));
verifier('entrer dans le lecteur applique l etat (replie sur telephone)',
         /if \(name === 'reader'\) _appliquerTiroirLecteur\(\);/.test(source));
verifier('les reglages sont caches par la classe `hidden`',
         css.includes('.hidden { display: none !important; }'));
verifier('le redimensionnement reapplique l etat tant que Laurent n a rien choisi',
         /if \(_tiroirLecteurOuvert === null\) _appliquerTiroirLecteur\(\);/.test(source));

console.log('');
console.log('8) le dessin suit l etat annonce (aria-expanded)');
verifier('la poignee est stylée', css.includes('#reader-tiroir-btn {'));
verifier('le chevron se retourne quand le tiroir est ouvert',
         /#reader-tiroir-btn\[aria-expanded="true"\] svg \{ transform: rotate\(180deg\); \}/
           .test(css));
// L'ancre est volontairement coupee AVANT le « e » accentue de « poignee » :
// dans ce fichier de test, tout reste en ASCII.
const posMedia = css.indexOf('/* Ordinateur : pas de poign');
const blocMedia = posMedia >= 0 ? css.slice(posMedia, posMedia + 120) : '';
verifier('sur ordinateur, la poignee disparait (le tiroir reste ouvert)',
         blocMedia.includes('#reader-tiroir-btn { display: none; }'),
         blocMedia.slice(0, 60));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
