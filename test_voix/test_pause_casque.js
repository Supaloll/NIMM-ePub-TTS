// Verifie la PAUSE VENUE DE L'EXTERIEUR et le bouton du CASQUE (20/09/2026).
// ----------------------------------------------------------------------
// Constat de Laurent, le soir meme : « quand la lecture est arretee, le bouton
// affiche souvent Pause » et « je voudrais pouvoir mettre pause avec le casque,
// et reprendre la lecture ». LES DEUX ONT LA MEME CAUSE : quand Android met
// l'audio en pause sans nous (appel telephonique, autre application qui prend le
// son, systeme...), AUCUN evenement de fin ne nous est envoye. Le lecteur
// attendait alors pour toujours, `_ttsState` restait sur 'playing' -- donc le
// bouton disait « Pause », et le casque envoyait « pause » au lieu de « play ».
//
// Ce que le test verifie (fonctions extraites DU FICHIER REEL, faux element
// audio) :
//   - une pause VENUE D'AILLEURS remet l'etat sur « paused », previent l'ecran
//     et le lecteur du telephone, et rend la main (le lecteur ne reste pas
//     suspendu) ;
//   - notre PROPRE pause n'est pas prise pour une interruption ;
//   - la FIN NATURELLE d'un morceau (qui declenche aussi un evenement de pause)
//     n'est pas prise pour une interruption non plus ;
//   - apres la fin d'un morceau, l'ecouteur est retire (le morceau suivant pose
//     le sien).
//
// Usage : node test_voix/test_pause_casque.js
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

// Tranche du fichier reel : tout le collage, jusqu'a _playBlob.
const debut = source.indexOf('function _dureeWav');
const fin   = source.indexOf('async function _playBlob');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : les fonctions de lecture sont introuvables dans app.js');
  process.exit(1);
}
const CODE = source.slice(debut, fin);

// Un faux element audio : on declenche NOUS-MEMES les evenements, comme le ferait
// le navigateur.
function fauxAudio() {
  return {
    src: '', currentTime: 0, ended: false, pauses: 0,
    onended: null, onerror: null, onpause: null, ontimeupdate: null,
    play() { return Promise.resolve(); },
    pause() { this.pauses++; },
  };
}

function banc() {
  const audio = fauxAudio();
  const etats = [];
  const curseurs = [];
  const fauxDoc = { getElementById: () => audio };
  const fauxURL = { createObjectURL: () => 'blob:test', revokeObjectURL: () => {} };
  const fauxNav = { mediaSession: { playbackState: 'playing' } };
  const api = new Function(
    'document', 'URL', '_setCursor', '_updateTTSProgress',
    '_majPositionMediaSession', 'setTTSUI', 'navigator',
    'var _ttsState = "playing";\nvar _cursorIdx = -1;\nvar _sentences = new Array(10);\n' + CODE
    + '\nreturn { _jouerMorceauColle: _jouerMorceauColle,'
    + ' etat: () => _ttsState, setEtat: (v) => { _ttsState = v; } };')(
      fauxDoc, fauxURL, (v) => curseurs.push(v), () => {}, () => {},
      (s) => etats.push(s), fauxNav);
  return { api, audio, etats, curseurs, fauxNav };
}

// Un vrai WAV PCM 16 bits mono, comme ceux du lecteur.
function wav(cadence, dureeMs) {
  const octets = Math.round(cadence * (dureeMs / 1000)) * 2;
  const vue = new DataView(new ArrayBuffer(44 + octets));
  const ecrire = (pos, s) => {
    for (let i = 0; i < s.length; i++) vue.setUint8(pos + i, s.charCodeAt(i));
  };
  ecrire(0, 'RIFF'); vue.setUint32(4, 36 + octets, true); ecrire(8, 'WAVE');
  ecrire(12, 'fmt '); vue.setUint32(16, 16, true); vue.setUint16(20, 1, true);
  vue.setUint16(22, 1, true); vue.setUint32(24, cadence, true);
  vue.setUint32(28, cadence * 2, true); vue.setUint16(32, 2, true);
  vue.setUint16(34, 16, true); ecrire(36, 'data');
  vue.setUint32(40, octets, true);
  return new Uint8Array(vue.buffer);
}

const UNITS = [{ sentIdx: 4, paraIdx: 1 }, { sentIdx: 5, paraIdx: 1 }];

function partiesPretes() {
  const entete = { format: 1, canaux: 1, cadence: 24000, bits: 16,
                   debutDonnees: 44, tailleDonnees: 48000 };
  return [
    { blob: new Blob([wav(24000, 1000)]), entete: entete, pauseAvantMs: 0 },
    { blob: new Blob([wav(24000, 1000)]), entete: entete, pauseAvantMs: 300 },
  ];
}

(async () => {
  console.log('');
  console.log('1) une pause venue d ailleurs (appel, autre application...)');
  let b = banc();
  const promesse = b.api._jouerMorceauColle(
    new Blob([wav(24000, 2000)]), UNITS, 0, partiesPretes(),
    { aborted: false, addEventListener: () => {} });
  verifier('l ecouteur de pause est en place', typeof b.audio.onpause === 'function');
  b.audio.onpause();                 // <- le navigateur, sans nous demander
  await promesse;                    // le lecteur doit rendre la main
  verifier('l application se sait EN PAUSE', b.api.etat() === 'paused', b.api.etat());
  verifier('l ecran est mis a jour', b.etats.indexOf('paused') >= 0,
           JSON.stringify(b.etats));
  verifier('le lecteur du telephone aussi',
           b.fauxNav.mediaSession.playbackState === 'paused',
           b.fauxNav.mediaSession.playbackState);

  console.log('');
  console.log('2) notre PROPRE pause n est pas une interruption');
  b = banc();
  const fauxSignal = { aborted: false, ecouteurs: [],
                       addEventListener(nom, fn) { this.ecouteurs.push(fn); } };
  const p2 = b.api._jouerMorceauColle(new Blob([wav(24000, 500)]), UNITS, 0,
                                      partiesPretes(), fauxSignal);
  b.api.setEtat('paused');           // <- c'est NOUS qui mettons en pause
  b.audio.pause();                   // le navigateur previent l'element...
  b.audio.onpause();                 // ...qui envoie son evenement de pause
  fauxSignal.aborted = true;
  fauxSignal.ecouteurs.forEach(f => f());   // l'abandon, comme _pauseTTS
  await p2;
  verifier('aucun etat invente', b.etats.length === 0, JSON.stringify(b.etats));

  console.log('');
  console.log('3) la FIN NATURELLE du morceau ne compte pas comme une pause');
  b = banc();
  const finMorceau = b.api._jouerMorceauColle(
    new Blob([wav(24000, 500)]), UNITS, 0, partiesPretes(),
    { aborted: false, addEventListener: () => {} });
  b.audio.ended = true;              // le morceau est termine...
  b.audio.onpause();                 // ...et le navigateur envoie 'pause'
  verifier('l etat reste en lecture (ce n est pas une interruption)',
           b.api.etat() === 'playing', b.api.etat());
  b.audio.onended();                 // la fin, elle, termine le morceau
  await finMorceau;
  verifier('et l ecouteur est retire apres la fin', b.audio.onpause === null);

  console.log('');
  console.log('4) le lecteur s arrete proprement sur une pause exterieure');
  verifier('la boucle de lecture abandonne quand l application est en pause',
           source.includes("if (_ttsState === 'paused') break;"));

  console.log('');
  console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
  process.exit(echecs === 0 ? 0 : 1);
})();
