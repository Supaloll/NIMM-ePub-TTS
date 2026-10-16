// Verifie que le NARRATEUR D'UN CHAPITRE est le personnage qui raconte, que sa
// voix suit le CASTING en direct, et que le changement de chapitre ne se trompe
// pas de voix (15/10/2026, chantier « Le Trone de Fer »).
// -------------------------------------------------------------------------
// Ce qu'on veut : dans une saga ou chaque chapitre est ecrit du point de vue d'un
// personnage, la narration d'un chapitre est lue par la VOIX de ce personnage --
// une seule voix, la meme, pour la narration ET le dialogue (decision de Laurent,
// 15/10/2026). Aucune donnee n'est touchee : seule la facon de lire change.
//
// LES CONTROLES VIENNENT DE L'AUDIT DU 15/10/2026 (Claude.AI), qui a releve deux
// points, et les deux sont ici :
//   1. « la voix de la narration ne suit pas quand tu changes la voix du
//      personnage » : la carte des POV etait prise UNE fois, donc la narration
//      gardait l'ancienne voix jusqu'a la reouverture du livre -- deux voix pour
//      la meme personne. Corrige : la carte ne dit plus que QUI raconte, et la
//      voix se relit dans le casting a chaque phrase. Le controle 3 le verifie.
//   2. « il faut que le chapitre courant soit mis a jour avant que la premiere
//      phrase du nouveau chapitre soit synthetisee » : le controle 4 construit la
//      playlist apres une bascule et regarde la TOUTE PREMIERE unite, le controle
//      7 verifie l'ordre du cablage dans `loadChapter`.
//
// Le code teste est EXTRAIT DU FICHIER REEL (jamais recopie) : les fonctions de
// reconnaissance, de fiche et de playlist. Les tests node du projet extraient deja
// `_voixDuNarrateur` (voir `test_vitesse_personnage.js`), c'est pour eux que la
// fonction garde ses gardes `typeof`.
//
// Usage : node test_voix/test_voix_narrateur_chapitre.js
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

// --- Bornes de la playlist (comme dans test_vitesse_personnage.js) ---------
const debut = source.indexOf('function _splitLongSentence');
const fin   = source.indexOf('async function _preparerMessageHorsLigne');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : la playlist est introuvable dans app.js');
  process.exit(1);
}

// --- Extraction des fonctions telles qu'elles sont dans le fichier ---------
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
const codeAux = ['_voixDuNarrateur', '_povDuChapitre', '_fichePersonnage',
                 '_morceauxDeLaPhrase', '_vitesseDeFiche',
                 // 15/10/2026 : QUI on change quand on change la voix d'une phrase
                 // (le panneau « Voir la voix », decision « ce que tu changes, c'est
                 // ce que tu entends »).
                 '_cibleDeLaPhrase', '_personnageDePhrase']
  .map(extraireFonction).join('\n');

const entete = [
  'const SPLIT_SENTENCE_CHARS = 500;',
  'const SPLIT_SEGMENT_CHARS  = 450;',
  'const NARRATEUR_VOIX_DEFAUT = "fr-FR-DeniseNeural";',
  // `PERSONNAGE_RATE_DEFAUT` n'est PAS declare ici : il est defini DANS le bloc
  // extrait (`source.slice(debut, fin)`) -- le declarer ici le declarait deux
  // fois, et `new Function` refusait le script (SyntaxError, 15/10/2026).
  'let _sentences = [];',
  'let _chapterSpeakers = [];',
  'let _currentBookData = null;',
  'let _currentChapter = 0;',
  'let _incisesNarrateur = false;',
  'let _chapterIncises = {};',
  'let _narrateurParChapitre = false;',
  'let _povDuLivre = {};',
  'const document = { getElementById: () => ({ value: "fr-FR-DeniseNeural" }) };',
].join('\n');

const api = new Function(
  entete + '\n' + codeAux + '\n' + source.slice(debut, fin)
  + '\nreturn { _voiceForSentence: _voiceForSentence,'
  + ' _buildPlaylist: _buildPlaylist,'
  + ' _voixDuNarrateur: _voixDuNarrateur,'
  + ' _cibleDeLaPhrase: _cibleDeLaPhrase,'
  + ' phrases: function (s, sp) { _sentences = s; _chapterSpeakers = sp; },'
  + ' regler: function (livre, chapitre, pov, actif) {'
  + ' _currentBookData = livre; _currentChapter = chapitre;'
  + ' _povDuLivre = pov; _narrateurParChapitre = actif; } };')();

// --- Le decor : un petit livre a plusieurs chapitres -----------------------
const MENU = 'fr-FR-DeniseNeural';
const LIVRE = {
  voices: {
    'Bran_Stark':    { voice_id: 'qwen:BRAN', pitch: '+0Hz', rate: '+0%' },
    'Catelyn_Stark': { voice_id: 'qwen:CAT',  pitch: '+5Hz', rate: '+10%' },
  },
};
const PHRASES = [
  { text: 'Il faisait sombre, dans le col.',        paraIdx: 0 },  // narration
  { text: '\u00ab O\u00f9 vas-tu ? \u00bb dit Bran.', paraIdx: 0 },  // Bran parle
  { text: 'Le vent soufflait sur les cr\u00eaneaux.', paraIdx: 1 },
];
api.phrases(PHRASES, { 0: 'narration', 1: 'Bran_Stark', 2: 'narration' });

console.log('');
console.log('1) reglage ETEINT : rien ne change (le comportement d avant)');
api.regler(LIVRE, 0, {}, false);
egal('la narration garde la voix du menu', api._voiceForSentence(0).voice, MENU);
egal('et la vitesse du menu', api._voiceForSentence(0).rate, null);
egal('une replique de personnage suit sa fiche',
     api._voiceForSentence(1).voice, 'qwen:BRAN');

console.log('');
console.log('2) reglage ALLUME : le chapitre de Bran est lu par Bran');
api.regler(LIVRE, 0, { 0: { nom: 'Bran_Stark', source: 'titre' } }, true);
egal('narration -> la voix de Bran', api._voiceForSentence(0).voice, 'qwen:BRAN');
egal('narration -> sa hauteur',      api._voiceForSentence(0).pitch, '+0Hz');
egal('narration -> sa vitesse (Normale, celle de sa fiche)',
     api._voiceForSentence(0).rate, '+0%');
egal('une seule voix : la replique de Bran est la MEME',
     api._voiceForSentence(1).voice, api._voiceForSentence(0).voice);
egal('... et la MEME vitesse', api._voiceForSentence(1).rate,
     api._voiceForSentence(0).rate);

console.log('');
console.log('3) LA VOIX SUIT LE CASTING EN DIRECT (defaut releve par l audit)');
// Laurent change la voix, la hauteur et la vitesse de Bran dans la fenetre du
// casting. La carte des POV, elle, n'a PAS bouge : elle ne porte que le nom.
LIVRE.voices['Bran_Stark'] = { voice_id: 'qwen:AUTRE', pitch: '-10Hz', rate: '+20%' };
egal('narration -> la NOUVELLE voix, sans rouvrir le livre',
     api._voiceForSentence(0).voice, 'qwen:AUTRE');
egal('narration -> la nouvelle hauteur', api._voiceForSentence(0).pitch, '-10Hz');
egal('narration -> la nouvelle vitesse', api._voiceForSentence(0).rate, '+20%');
egal('sa replique suit aussi', api._voiceForSentence(1).voice, 'qwen:AUTRE');
egal('les deux restent D ACCORD', api._voiceForSentence(0).voice,
     api._voiceForSentence(1).voice);

console.log('');
console.log('4) LA BASCULE DE CHAPITRE : la 1re phrase part a la bonne voix');
// On remet la voix d'origine de Bran : le controle 3 l'avait changee exprès.
LIVRE.voices['Bran_Stark'] = { voice_id: 'qwen:BRAN', pitch: '+0Hz', rate: '+0%' };
api.regler(LIVRE, 1, { 0: { nom: 'Bran_Stark' }, 1: { nom: 'Catelyn_Stark' } }, true);
egal('narration du chapitre 2 -> Catelyn', api._voiceForSentence(0).voice, 'qwen:CAT');
const unites = api._buildPlaylist(0, 2);
verifier('la playlist est construite', unites.length >= 3, unites.length);
egal('la TOUTE PREMIERE unite porte la voix du chapitre 2', unites[0].voice, 'qwen:CAT');
egal('et sa vitesse', unites[0].rate, '+10%');
egal('une replique d un AUTRE personnage garde SA voix',
     api._voiceForSentence(1).voice, 'qwen:BRAN');

console.log('');
console.log('5) chapitre SANS personnage reconnu : le narrateur du livre');
api.regler(LIVRE, 2, { 0: { nom: 'Bran_Stark' } }, true);
egal('la narration revient au menu', api._voiceForSentence(0).voice, MENU);

console.log('');
console.log('6) limite connue : un POV reconnu mais SANS voix au casting');
api.regler(LIVRE, 3, { 3: { nom: 'Melisandre' } }, true);
egal('aucune fiche -> le narrateur du livre', api._voiceForSentence(0).voice, MENU);
LIVRE.voices['Melisandre'] = { voice_id: '', pitch: '+0Hz', rate: '+0%' };
egal('une fiche SANS voix -> le narrateur du livre aussi',
     api._voiceForSentence(0).voice, MENU);

console.log('');
console.log('7) cablage : le chapitre courant est pose AVANT la lecture');
const debutLoad = source.indexOf('async function loadChapter');
const blocLoad  = source.slice(debutLoad, debutLoad + 6000);
const posChapitre = blocLoad.indexOf('_currentChapter = index');
const posStart    = blocLoad.indexOf('if (autoPlay) _startTTS();');
verifier('loadChapter pose _currentChapter', posChapitre >= 0, posChapitre);
verifier('... et AVANT _startTTS', posStart > posChapitre && posStart >= 0,
         posChapitre + ' / ' + posStart);
verifier('l enchainement de chapitre passe par loadChapter (donc le meme chemin)',
         source.indexOf('await loadChapter(_currentChapter + 1, 0, 0, true)') > 0);

console.log('');
console.log('8) la page ne lit AUCUNE voix dans la carte des POV');
verifier('pas de voice_id prise dans la carte',
         source.indexOf('_povDuLivre[_currentChapter].voice_id') < 0
         && source.indexOf('pov.voice_id') < 0);

console.log('');
console.log('9) QUI on change quand on change la voix d une phrase (le panneau)');
api.regler(LIVRE, 0, { 0: { nom: 'Bran_Stark' } }, true);
egal('une phrase de personnage -> ce personnage',
     api._cibleDeLaPhrase(1), 'Bran_Stark');
egal('une phrase de narration d un chapitre POV -> le personnage qui raconte',
     api._cibleDeLaPhrase(0), 'Bran_Stark');
api.regler(LIVRE, 2, { 0: { nom: 'Bran_Stark' } }, true);
egal('chapitre sans POV -> aucune cible (c est le narrateur du livre)',
     api._cibleDeLaPhrase(0), null);
api.regler(LIVRE, 0, { 0: { nom: 'Bran_Stark' } }, false);
egal('reglage eteint -> aucune cible non plus',
     api._cibleDeLaPhrase(0), null);

console.log('');
if (echecs === 0) {
  console.log('TOUT EST OK');
  process.exit(0);
}
console.log(echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(1);
