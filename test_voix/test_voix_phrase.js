// Verifie le panneau « voix de la phrase » (tache mobile / bouton PC),
// SANS navigateur (demande de Laurent, 15/09/2026).
// ----------------------------------------------------------------------
// Deux choses sont controlees, sur le FICHIER REEL (jamais une copie) :
//
// 1. LES IDENTIFIANTS : chaque element du panneau et du tooltip utilise par
//    app.js doit exister dans index.html. Sans cela, le panneau planterait a
//    l'ouverture (erreur silencieuse sur mobile, ou l'on ne peut rien voir).
// 2. LA LOGIQUE : a qui appartient une phrase, et quelle voix elle utilise.
//    - une phrase sans personnage (ou marquee « narration ») appartient au
//      NARRATEUR : c'est la voix du lecteur (menu du haut) ;
//    - une phrase d'un personnage utilise la voix de SA fiche de casting ;
//    - le menu des voix propose toutes les voix et, si la voix en place n'est
//      pas proposee (moteur eteint), elle reste AFFICHEE en tete de liste
//      plutot que d'etre remplacee en silence par une autre.
//
// Usage : node test_voix/test_voix_phrase.js
'use strict';

const fs = require('fs');
const path = require('path');

const APP  = path.join(__dirname, '..', 'frontend', 'app.js');
const HTML = path.join(__dirname, '..', 'frontend', 'index.html');
const source = fs.readFileSync(APP, 'utf8');
const page   = fs.readFileSync(HTML, 'utf8');

let echecs = 0;
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail !== undefined ? '  -> ' + detail : ''));
    echecs++;
  }
}

// --- 1. Les identifiants du panneau existent dans la page ---
console.log('');
console.log('1) identifiants du panneau et du tooltip');

const IDS = [
  'selection-tooltip', 'read-from-here-btn', 'show-voice-btn',
  'voice-phrase-panel', 'voice-phrase-close-btn', 'voice-phrase-extrait',
  'voice-phrase-personnage', 'voice-phrase-voix', 'voice-phrase-label',
  'voice-phrase-select', 'voice-phrase-ecouter-btn', 'voice-phrase-note',
  // Ligne d'usage de la voix choisie (19/09/2026) : libre, portee par X,
  // partagee... ECRITE, car sur mobile il n'y a ni survol ni appui long.
  'voice-phrase-usage',
];
IDS.forEach(id => {
  const dansPage = page.includes('id="' + id + '"');
  const dansCode = source.includes("'" + id + "'");
  verifier(id + ' : present dans la page et utilise par app.js',
           dansPage && dansCode,
           'page=' + dansPage + ' code=' + dansCode);
});

// --- 2. La logique, extraite du fichier reel ---
const debut = source.indexOf('let _voicePhraseIdx');
const fin   = source.indexOf('function _remplirMenuVoixPhrase');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : les fonctions du panneau sont introuvables dans app.js');
  process.exit(1);
}
const code = source.slice(debut, fin);

// Un faux document : une seule reponse utile, la voix du lecteur.
const fauxDocument = {
  getElementById: (id) => (id === 'voice-select'
    ? { value: 'fr-CH-ArianeNeural' } : null),
};

function fabrique(speakers, bookData) {
  return new Function(
    '_chapterSpeakers', '_currentBookData', 'document',
    code + '\nreturn { _personnageDePhrase, _fichePersonnage, _voixDePhrase };'
  )(speakers, bookData, fauxDocument);
}

console.log('');
console.log('2) a qui appartient une phrase');

// Le cas reel : la phrase 1 est d'Alphonse, la 2 est sans attribution (elle
// arrive donc avec la voix du narrateur), la 3 est un personnage non caste.
const SPEAKERS = { 1: 'Alphonse', 3: 'Bertuccio' };
const BOOK = {
  voices: {
    Alphonse: { voice_id: 'xtts:cml9804', rate: '+0%', pitch: '+0Hz' },
  },
};
const api = fabrique(SPEAKERS, BOOK);

verifier('phrase d un personnage -> son nom',
         api._personnageDePhrase(1) === 'Alphonse', api._personnageDePhrase(1));
verifier('phrase sans attribution -> narrateur (null)',
         api._personnageDePhrase(2) === null, api._personnageDePhrase(2));
verifier('phrase marquee « narration » -> narrateur (null)',
         api._personnageDePhrase(0) === null, api._personnageDePhrase(0));
verifier('chapitre entierement sans personnage -> narrateur',
         api._personnageDePhrase(999) === null, api._personnageDePhrase(999));

const sansSpeakers = fabrique({}, BOOK);
verifier('livre sans attribution du tout -> narrateur',
         sansSpeakers._personnageDePhrase(1) === null);

console.log('');
console.log('3) quelle voix est utilisee');

verifier('personnage caste -> la voix de sa fiche',
         api._voixDePhrase(1) === 'xtts:cml9804', api._voixDePhrase(1));
verifier('narrateur -> la voix du lecteur',
         api._voixDePhrase(2) === 'fr-CH-ArianeNeural', api._voixDePhrase(2));
verifier('personnage sans fiche -> la voix du lecteur (rien n est perdu)',
         api._voixDePhrase(3) === 'fr-CH-ArianeNeural', api._voixDePhrase(3));

const sansVoix = fabrique(SPEAKERS, { voices: {} });
verifier('livre sans fiche de casting -> voix du lecteur',
         sansVoix._voixDePhrase(1) === 'fr-CH-ArianeNeural');

console.log('');
console.log('4) le menu des voix ne fait rien disparaitre');

// Faux DOM minimal : juste ce qu'utilise _remplirMenuVoixPhrase.
function element(tag) {
  return {
    tag: tag, label: '', value: '', textContent: '', children: [],
    appendChild(c) { this.children.push(c); return c; },
    set innerHTML(v) { if (v === '') this.children = []; },
    get innerHTML() { return ''; },
  };
}
const fauxDocMenu = { createElement: element };

const debutMenu = source.indexOf('function _remplirMenuVoixPhrase');
const finMenu   = source.indexOf('function _openVoicePanel');
if (debutMenu < 0 || finMenu <= debutMenu) {
  console.error('ECHEC : _remplirMenuVoixPhrase introuvable dans app.js');
  process.exit(1);
}
const codeMenu = source.slice(debutMenu, finMenu);

const VOIX_PROPOSEES = [
  { id: 'edge:adele',  name: 'Adele',  region: 'France', gender: 'F' },
  { id: 'edge:bruno',  name: 'Bruno',  region: 'France', gender: 'M' },
  { id: 'kokoro:zz',   name: 'Zoe',    region: 'France' },
];

function menu(allVoices, voixId, libelle) {
  const fabriqueMenu = new Function(
    '_allVoices', '_libelleCatalogue', 'document',
    codeMenu + '\nreturn _remplirMenuVoixPhrase;'
  );
  const remplir = fabriqueMenu(allVoices, libelle, fauxDocMenu);
  const select = element('select');
  remplir(select, voixId);
  const options = [];
  select.children.forEach(g => {
    (g.children || []).forEach(o => options.push({
      valeur: o.value, texte: o.textContent, groupe: g.label,
    }));
  });
  return { select, options };
}

const propose = menu(VOIX_PROPOSEES, 'edge:bruno', () => '');
verifier('une voix proposee est selectionnee',
         propose.select.value === 'edge:bruno', propose.select.value);
verifier('les 3 voix proposees sont dans le menu',
         propose.options.length === 3, propose.options.length);

const horsListe = menu(VOIX_PROPOSEES, 'xtts:cml9804',
                       (id) => id === 'xtts:cml9804' ? 'Alphonse \u2014 France (XTTS)' : '');
verifier('une voix absente de la liste est AJOUTEE au menu',
         horsListe.options.length === 4, horsListe.options.length);
verifier('elle garde son identifiant (le choix n est pas perdu)',
         horsListe.select.value === 'xtts:cml9804', horsListe.select.value);
verifier('elle est affichee sous son NOM, jamais sous son identifiant',
         horsListe.options.some(o => o.texte.indexOf('Alphonse') === 0),
         JSON.stringify(horsListe.options.map(o => o.texte)));
verifier('elle est signalee comme « voix actuelle »',
         horsListe.options.some(o => o.groupe.indexOf('Voix actuelle') >= 0));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
