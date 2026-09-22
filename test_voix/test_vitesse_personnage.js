// Verifie que la VITESSE d'un personnage part bien a la synthese (20/09/2026).
// --------------------------------------------------------------------------
// Defaut corrige ce jour-la : les curseurs de vitesse de la fenetre du casting
// enregistraient bien leur valeur en base, mais la playlist de lecture ne
// transmettait JAMAIS cette vitesse a la synthese (le lecteur envoyait
// toujours la vitesse du menu du haut). Consequence mesuree : 131 fiches
// reglees sans aucun effet audible, dont plusieurs a +/-20-25 %.
//
// Choix de vitesse, regle clarifiee par Laurent le 20/09/2026 (le soir) :
//   - fiche AVEC un vrai reglage        -> la phrase est lue a CETTE vitesse ;
//   - fiche SANS reglage (voix dediee)  -> « Normale » : le menu n'est pas un
//     reglage general, c'est celui du NARRATEUR ;
//   - narration et petits roles (lus par le narrateur) -> la vitesse du MENU.
//
// Le code teste est EXTRAIT DU FICHIER REEL (jamais recopie) : deux fonctions
// pures et la construction de la playlist. Le dernier controle verifie le
// CABLAGE dans app.js, parce que `_runTTS` (qui envoie la requete) n'est pas
// executable ici : si l'appel a `_fetchAudio` recommencait a ignorer `u.rate`,
// le test echouerait bruyamment.
//
// Usage : node test_voix/test_vitesse_personnage.js
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

// --- Bornes de l'extraction : de la decoupe des phrases a la fin de la
// playlist. Tout ce bloc ne depend ni du reseau ni de l'interface.
const debut = source.indexOf('function _splitLongSentence');
const fin   = source.indexOf('async function _preparerMessageHorsLigne');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : la playlist est introuvable dans app.js');
  process.exit(1);
}

// Les deux seuils de decoupe sont LUS dans le fichier (pas recopies).
function lireNombre(nom) {
  const trouve = source.match(new RegExp('const\\s+' + nom + '\\s*=\\s*(\\d+)'));
  return trouve ? parseInt(trouve[1], 10) : null;
}
const seuilPhrase  = lireNombre('SPLIT_SENTENCE_CHARS');
const seuilSegment = lireNombre('SPLIT_SEGMENT_CHARS');

// Depuis le 22/09/2026, la playlist s'appuie sur deux fonctions definies PLUS
// HAUT dans le fichier : `_voixDuNarrateur` (la voix du menu) et
// `_morceauxDeLaPhrase` (le decoupage d'une phrase en morceaux de voix, pour les
// incises confiees au narrateur). On les EXTRAIT DU FICHIER REEL, comme le reste :
// les recopier ici les laisserait deriver sans que rien ne le signale.
function extraireFonction(nom) {
  const lignes = source.split(/\r?\n/);
  const debutFn = lignes.findIndex(l => l.startsWith('function ' + nom + '('));
  if (debutFn < 0) {
    console.error('ECHEC : fonction ' + nom + ' introuvable dans app.js');
    process.exit(1);
  }
  let finFn = -1;
  for (let i = debutFn + 1; i < lignes.length; i++) {
    if (lignes[i] === '}') { finFn = i; break; }
  }
  if (finFn < 0) {
    console.error('ECHEC : fin de ' + nom + ' introuvable dans app.js');
    process.exit(1);
  }
  return lignes.slice(debutFn, finFn + 1).join('\n');
}
const codeIncises = extraireFonction('_voixDuNarrateur') + '\n'
                  + extraireFonction('_morceauxDeLaPhrase');

const entete = [
  'const SPLIT_SENTENCE_CHARS = ' + seuilPhrase + ';',
  'const SPLIT_SEGMENT_CHARS  = ' + seuilSegment + ';',
  'let _sentences = [];',
  'let _chapterSpeakers = [];',
  'let _currentBookData = null;',
  'let _voixMenu = "fr-FR-DeniseNeural";',
  'const document = { getElementById: () => ({ value: _voixMenu }) };',
  // Reglages des incises de parole (22/09/2026) : au repos, « muettes » -- c'est
  // le defaut d'un livre, et la playlist ne coupe alors RIEN.
  'let _incisesNarrateur = false;',
  'let _chapterIncises = {};',
  'const NARRATEUR_VOIX_DEFAUT = "fr-CH-ArianeNeural";',
].join('\n');

const api = new Function(
  entete + '\n' + codeIncises + '\n' + source.slice(debut, fin)
  + '\nreturn { _vitesseDeFiche: _vitesseDeFiche,'
  + ' _voiceForSentence: _voiceForSentence,'
  + ' _buildPlaylist: _buildPlaylist,'
  + ' regler: function (s, sp, livre, menu) {'
  + ' _sentences = s; _chapterSpeakers = sp; _currentBookData = livre;'
  + ' if (menu) _voixMenu = menu; } };')();

console.log('');
console.log('1) la vitesse d une fiche : le neutre ne compte pas');
egal('un vrai reglage est garde',        api._vitesseDeFiche('+20%'), '+20%');
egal('un reglage negatif aussi',         api._vitesseDeFiche('-25%'), '-25%');
egal('les espaces sont nettoyes',        api._vitesseDeFiche('  +15% '), '+15%');
egal('le neutre (plus zero pour cent) vaut pas de reglage',
     api._vitesseDeFiche('+0%'), null);
egal('« 0% » aussi',                     api._vitesseDeFiche('0%'), null);
egal('« +0 » aussi',                     api._vitesseDeFiche('+0'), null);
egal('une valeur vide aussi',            api._vitesseDeFiche(''), null);
egal('absente aussi',                    api._vitesseDeFiche(null), null);
egal('non renseignee aussi',             api._vitesseDeFiche(undefined), null);

console.log('');
console.log('2) la playlist porte la vitesse de chaque personnage');
const livre = {
  voices: {
    'Edmond Dantes': { voice_id: 'kyutai:2223_1745_000009-0002', pitch: '+4Hz', rate: '+10%' },
    'Fernand':       { voice_id: 'kyutai:296_1028_000022-0001',  pitch: '+0Hz', rate: '+0%' },
    'Petit role':    { voice_id: '',                             pitch: '+0Hz', rate: '+20%' },
  },
};
api.regler(
  [
    { text: 'Il partit.',   paraIdx: 0 },
    { text: 'Je partirai.', paraIdx: 0 },
    { text: 'Moi aussi.',   paraIdx: 0 },
    { text: 'Oui.',         paraIdx: 0 },
  ],
  ['narration', 'Edmond Dantes', 'Fernand', 'Petit role'],
  livre
);
const unites = api._buildPlaylist(0);
egal('une unite par phrase', unites.length, 4);
egal('personnage regle : SA vitesse part', unites[1].rate, '+10%');
egal('personnage sans reglage : NORMALE (le menu n est pas un reglage general)',
     unites[2].rate, '+0%');
egal('narration : la vitesse du menu s applique', unites[0].rate, null);
egal('petit role (lu par le narrateur) : idem', unites[3].rate, null);
verifier('le personnage regle et le personnage sans reglage different',
         unites[1].rate === '+10%' && unites[2].rate === '+0%');
verifier('le petit role du livre suit le narrateur, meme avec un reglage sur sa fiche',
         unites[3].rate === null);

// Le point qui compte : le MENU ne doit plus toucher les personnages. On refait
// la meme phrase avec le menu (reglage du narrateur) sur « Lente » : la
// narration le suit (elle porte `null` -> c'est le menu qui sera envoye), mais
// un personnage sans reglage reste a « Normale ».
api.regler([{ text: 'Il partit.', paraIdx: 0 }], ['narration'], livre, '-20%');
const avecMenuLent = api._buildPlaylist(0);
egal('menu sur Lente : la narration le suit (porte null)',
     avecMenuLent[0].rate, null);
api.regler([{ text: 'Moi aussi.', paraIdx: 0 }], ['Fernand'], livre, '-20%');
egal('menu sur Lente : le personnage sans reglage reste a Normale',
     api._buildPlaylist(0)[0].rate, '+0%');
api.regler([{ text: 'Je partirai.', paraIdx: 0 }], ['Edmond Dantes'], livre, '-20%');
egal('menu sur Lente : le personnage regle garde SA vitesse (+10 %)',
     api._buildPlaylist(0)[0].rate, '+10%');
verifier('la valeur par defaut d un personnage est bien Normale dans app.js',
         source.indexOf("const PERSONNAGE_RATE_DEFAUT = '+0%'") > 0);

console.log('');
console.log('3) aucune regression sur la voix et la hauteur');
egal('la voix de la fiche part toujours', unites[1].voice,
     'kyutai:2223_1745_000009-0002');
egal('la hauteur de la fiche part toujours', unites[1].pitch, '+4Hz');
egal('la narration garde la voix du menu', unites[0].voice,
     'fr-FR-DeniseNeural');
verifier('toutes les unites portent la cle rate (meme nulle)',
         unites.every(u => 'rate' in u));

console.log('');
console.log('4) cablage : le lecteur envoie bien la vitesse de la phrase');
verifier('l appel a _fetchAudio utilise u.rate avec repli sur le menu',
         source.indexOf('_fetchAudio(u.text, u.voice, u.rate || rate, u.pitch') > 0);
verifier('l ancien appel (vitesse du menu pour tout le monde) a disparu',
         source.indexOf('_fetchAudio(u.text, u.voice, rate, u.pitch') < 0);
verifier('les seuils de decoupe ont bien ete lus dans app.js',
         seuilPhrase > 0 && seuilSegment > 0);

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
