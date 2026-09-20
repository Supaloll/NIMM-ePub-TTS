// Verifie le COLLAGE DES PHRASES EN UN SEUL MORCEAU (20/09/2026).
// ----------------------------------------------------------------------
// Demande de Laurent : « la modale de lecture disparait entre deux paragraphes,
// puisqu'il n'y a plus de voix... c'est comme si j'avais une playlist de
// centaines de morceaux de quelques secondes ». Le lecteur joue maintenant les
// phrases COLLEES en un seul long morceau : la modale reste affichee, et il n'y a
// plus de micro-blanc entre les phrases.
//
// Ce qui est verifie ici, sur de VRAIS WAV fabriques par le test (les fonctions
// sont extraites DU FICHIER REEL) :
//   - la lecture d'en-tete : cadence, canaux, resolution, et ou commence le son ;
//   - la DUREE EXACTE (c'est elle qui fait suivre la surbrillance : une duree
//     fausse decalerait tout le curseur) ;
//   - un fichier tronque n'est pas lu au-dela de sa fin ;
//   - l'en-tete du morceau colle annonce la BONNE taille totale ;
//   - le morceau colle se RELIT comme un WAV valide, de la bonne duree ;
//   - la pause entre paragraphes est bien inseree dans le morceau (silence) ;
//   - deux formats differents (24000 Hz et 22050 Hz) refusent de se coller :
//     c'est le filet qui protege les voix Piper.
//
// Usage : node test_voix/test_collage_wav.js
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

// Tranche du fichier reel : de _enteteWav a _jouerMorceauColle (tout le collage).
const debut = source.indexOf('function _enteteWav');
const fin   = source.indexOf('async function _jouerMorceauColle');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : les fonctions de collage sont introuvables dans app.js');
  process.exit(1);
}
const api = new Function(source.slice(debut, fin)
  + '\nreturn { _enteteWav: _enteteWav, _dureeWav: _dureeWav,'
  + ' _memesFormats: _memesFormats, _enteteWavColle: _enteteWavColle,'
  + ' _blobSilence: _blobSilence, _collerWav: _collerWav,'
  + ' _enteteDeBlob: _enteteDeBlob };')();

// Un vrai WAV PCM 16 bits mono, comme ceux du lecteur.
function wav(cadence, dureeMs, valeur) {
  const octets = Math.round(cadence * (dureeMs / 1000)) * 2;
  const vue = new DataView(new ArrayBuffer(44 + octets));
  const ecrire = (pos, s) => {
    for (let i = 0; i < s.length; i++) vue.setUint8(pos + i, s.charCodeAt(i));
  };
  ecrire(0, 'RIFF');
  vue.setUint32(4, 36 + octets, true);
  ecrire(8, 'WAVE');
  ecrire(12, 'fmt ');
  vue.setUint32(16, 16, true);
  vue.setUint16(20, 1, true);            // PCM
  vue.setUint16(22, 1, true);            // mono
  vue.setUint32(24, cadence, true);
  vue.setUint32(28, cadence * 2, true);
  vue.setUint16(32, 2, true);
  vue.setUint16(34, 16, true);
  ecrire(36, 'data');
  vue.setUint32(40, octets, true);
  for (let i = 0; i < octets; i += 2) vue.setInt16(44 + i, valeur, true);
  return new Uint8Array(vue.buffer);
}

console.log('');
console.log('1) lecture de l en-tete et duree exacte');
const tete = api._enteteWav(wav(24000, 1000, 1200));
egal('format PCM', tete.format, 1);
egal('mono', tete.canaux, 1);
egal('24000 Hz', tete.cadence, 24000);
egal('16 bits', tete.bits, 16);
egal('le son commence apres l en-tete', tete.debutDonnees, 44);
egal('taille du son', tete.tailleDonnees, 48000);
egal('duree EXACTE : 1 seconde', api._dureeWav(tete), 1);
egal('et 2,5 secondes pour un morceau plus long',
     api._dureeWav(api._enteteWav(wav(24000, 2500, 500))), 2.5);
verifier('ce qui n est pas un WAV est refuse',
         api._enteteWav(new Uint8Array([1, 2, 3, 4])) === null);
// Un fichier tronque (telechargement interrompu) ne doit JAMAIS etre lu au-dela
// de sa fin : sinon on croirait a un son plus long qu'il ne l'est.
const tronque = wav(24000, 1000, 800).slice(0, 44 + 1000);
egal('fichier tronque : on garde ce qui existe vraiment',
     api._enteteWav(tronque).tailleDonnees, 1000);

console.log('');
console.log('2) les formats compatibles seulement');
verifier('meme format -> collage autorise',
         api._memesFormats(tete, api._enteteWav(wav(24000, 500, 300))) === true);
verifier('cadences differentes (24000 / 22050) -> collage REFUSE',
         api._memesFormats(tete, api._enteteWav(wav(22050, 500, 300))) === false);
verifier('l en-tete collee annonce la taille totale',
         (() => {
           const h = api._enteteWavColle(tete, 96000);
           const vue = new DataView(h.buffer);
           return vue.getUint32(4, true) === 36 + 96000
               && vue.getUint32(40, true) === 96000
               && vue.getUint32(24, true) === 24000
               && vue.getUint16(34, true) === 16;
         })());

console.log('');
console.log('3) le silence des pauses (300 ms entre paragraphes)');
egal('silence de 300 ms = 14400 octets a 24000 Hz',
     api._blobSilence(tete, 300).size, 14400);

(async () => {
  console.log('');
  console.log('4) le morceau colle se relit comme un vrai WAV');
  const p1 = new Blob([wav(24000, 1000, 1000)]);
  const p2 = new Blob([wav(24000, 2000, -1000)]);
  const parties = [
    { blob: p1, entete: await api._enteteDeBlob(p1), pauseAvantMs: 0 },
    { blob: p2, entete: await api._enteteDeBlob(p2), pauseAvantMs: 300 },
  ];
  const colle = api._collerWav(parties);
  verifier('un morceau a bien ete fabrique', colle !== null);
  egal('taille : en-tete + les deux sons + la pause',
       colle.size, 44 + 48000 + 96000 + 14400);
  const relu = api._enteteWav(new Uint8Array(await colle.arrayBuffer()));
  egal('il se relit comme un WAV valide', relu.cadence, 24000);
  egal('sa duree totale : 1 s + 2 s + 0,3 s', api._dureeWav(relu), 3.3);

  console.log('');
  console.log('5) le filet : deux formats differents ne se collent pas');
  const p3 = new Blob([wav(22050, 500, 400)]);
  const melange = [
    { blob: p1, entete: await api._enteteDeBlob(p1), pauseAvantMs: 0 },
    { blob: p3, entete: await api._enteteDeBlob(p3), pauseAvantMs: 0 },
  ];
  verifier('collage refuse (l appelant repartira phrase par phrase)',
           api._collerWav(melange) === null);
  verifier('et une liste vide ne fabrique rien', api._collerWav([]) === null);

  console.log('');
  console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
  process.exit(echecs === 0 ? 0 : 1);
})();
