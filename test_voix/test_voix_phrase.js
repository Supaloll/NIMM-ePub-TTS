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
  // LA LISTE DES VOIX (22/09/2026) : elle remplace le menu déroulant
  // `voice-phrase-select`, qui n'existe plus. Les LIGNES sont construites par le
  // code, donc seuls le conteneur, la recherche et le compteur sont dans la page.
  'voice-phrase-liste', 'voice-phrase-recherche', 'voice-phrase-recap',
  'voice-phrase-ecouter-btn', 'voice-phrase-note',
  // Ligne d'usage de la voix choisie (19/09/2026) : libre, portee par X,
  // partagee... ECRITE, car sur mobile il n'y a ni survol ni appui long.
  'voice-phrase-usage',
  // Porte vers la fenetre du casting (20/09/2026) : ouvrir la vraie fenetre SUR
  // le personnage de la phrase, pour tout ce que le panneau ne fait pas.
  'voice-phrase-cast-btn',
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
// La borne de fin a change le 22/09/2026 : `_remplirMenuVoixPhrase` (le menu
// deroulant) n'existe plus, remplace par la liste des voix. On s'arrete donc a
// `_openVoicePanel`, qui suit immediatement.
const fin   = source.indexOf('function _openVoicePanel');
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
console.log('4) la LISTE des voix, sur deux lignes (22/09/2026)');

// Demande de Laurent (voie B) : le MENU DÉROULANT est remplacé par une liste de
// VRAIS éléments de page, où chaque voix se lit sur deux lignes —
//   1re : symbole, prénom, drapeaux, âge et timbre ;
//   2e  : icône du moteur, puis l'état (« · LIBRE », « · Edmond »).
// La construction des lignes est une fonction PURE (`_lignesVoixListe`, la même
// que pour la liste du casting) : on
// l'extrait DU FICHIER RÉEL et on l'éprouve sans DOM, sans navigateur (le rendu
// n'est que du dessin par-dessus).
function extraire(debutNom, finNom) {
  const d = source.indexOf(debutNom);
  const f = source.indexOf(finNom);
  if (d < 0 || f <= d) {
    console.error('ECHEC : ' + debutNom + ' introuvable dans app.js');
    process.exit(1);
  }
  return source.slice(d, f);
}
const CODE_LISTE = [
  extraire('const DRAPEAU_FR', 'function _secondDrapeauDeVoix'),
  extraire('function _secondDrapeauDeVoix', 'function _libelleCritere'),
  extraire('function _libelleCritere', 'function _identiteVoix'),
  extraire('function _identiteVoix', 'function _libelleVoix'),
  extraire('function _familleDeVoix', 'function _libelleFamille'),
  extraire('function _libelleFamille', 'async function _chargerAnnotationsVoix'),
  extraire('function _cleRecherche', 'function _filtrerPersonnages'),
  extraire('function _filtrerVoixLibres', 'function _etatCasting'),
  extraire('function _lignesVoixListe', 'function _peindreListeVoixPhrase'),
].join('\n');

const ICO_EDGE = '\u2601\uFE0F';
const ICO_XTTS = '\uD83E\uDDEC';
const SYM_F    = '\u2640\uFE0F';
const FR       = '\uD83C\uDDEB\uD83C\uDDF7';
const FAMILLES = [['edge', 'Edge (en ligne)', ICO_EDGE],
                  ['kokoro', 'Kokoro', '\uD83C\uDF8E'],
                  ['xtts', 'XTTS v2', ICO_XTTS]];
const CRITERES = [
  { cle: 'age', libelle: 'Age', valeurs: [{ valeur: 'adulte', libelle: 'adulte' }] },
  { cle: 'timbre', libelle: 'Timbre', valeurs: [{ valeur: 'grave', libelle: 'grave' }] },
];

const VOIX_PROPOSEES = [
  { id: 'edge:adele',  name: 'Adele',  region: 'France', gender: 'F' },
  { id: 'edge:bruno',  name: 'Bruno',  region: 'France', gender: 'M' },
  { id: 'kokoro:zz',   name: 'Zoe',    region: 'France' },
  { id: 'xtts:anna',   name: 'Anna',   region: 'France', gender: 'F' },
];
const ANNOTATIONS = { 'xtts:anna': { age: 'adulte', timbre: 'grave' } };

function lignes(voix, voixId, marque, recherche, libelleAbsente) {
  const fabrique = new Function(
    '_annotationsVoix', '_criteresVoix', 'FAMILLES_VOIX',
    CODE_LISTE + '\nreturn _lignesVoixListe;');
  const calcul = fabrique(ANNOTATIONS, CRITERES, FAMILLES);
  return calcul(voix, voixId, marque, recherche, libelleAbsente);
}
const voixDe = (rendues, id) =>
  rendues.find(l => l.genre === 'voix' && l.id === id);
const groupes = (rendues) =>
  rendues.filter(l => l.genre === 'groupe').map(l => l.libelle);

const rendu = lignes(VOIX_PROPOSEES, 'edge:bruno', () => ' \u00B7 LIBRE');
verifier('les trois groupes sont la, dans l ordre Femmes, Hommes, Autres',
         JSON.stringify(groupes(rendu))
           === JSON.stringify(['\uD83D\uDC69 Femmes', '\uD83D\uDC68 Hommes',
                               'Autres']),
         JSON.stringify(groupes(rendu)));
verifier('un groupe sans voix n est pas ecrit (pas de titre orphelin)',
         groupes(lignes([VOIX_PROPOSEES[0]], '', () => '')).length === 1);

const anna = voixDe(rendu, 'xtts:anna');
verifier('1re ligne : symbole, prenom, drapeaux, age et timbre',
         anna.identite === SYM_F + ' Anna ' + FR + ' adulte grave', anna.identite);
verifier('2e ligne : icone du moteur, puis l etat de la voix',
         anna.deuxiemeLigne === ICO_XTTS + ' \u00B7 LIBRE', anna.deuxiemeLigne);
verifier('une voix sans annotation porte quand meme son moteur',
         voixDe(rendu, 'edge:adele').deuxiemeLigne === ICO_EDGE + ' \u00B7 LIBRE',
         voixDe(rendu, 'edge:adele').deuxiemeLigne);
verifier('la voix choisie est marquee, et elle seule',
         rendu.filter(l => l.actuelle).length === 1
         && voixDe(rendu, 'edge:bruno').actuelle === true);

const nomsGroupe = lignes([VOIX_PROPOSEES[3], VOIX_PROPOSEES[0]], '', () => '')
  .filter(l => l.genre === 'voix').map(l => l.id);
verifier('les voix d un groupe sont rangees par prenom',
         JSON.stringify(nomsGroupe) === JSON.stringify(['edge:adele', 'xtts:anna']),
         JSON.stringify(nomsGroupe));

verifier('la recherche garde la voix cherchee (et son groupe)',
         lignes(VOIX_PROPOSEES, '', () => '', 'adel').length === 2,
         JSON.stringify(lignes(VOIX_PROPOSEES, '', () => '', 'adel')));
verifier('une recherche sans resultat ne rend AUCUNE voix',
         lignes(VOIX_PROPOSEES, '', () => '', 'zzzzz')
           .filter(l => l.genre === 'voix').length === 0);
verifier('la recherche ignore les accents',
         lignes([{ id: 'edge:amelie', name: 'Am\u00e9lie', region: 'France',
                   gender: 'F' }], '', () => '', 'amelie').length === 2);

// Une voix attribuee mais PLUS PROPOSEE (moteur eteint, voix retiree) doit
// rester visible, sous son nom : c'est la regle du 14/09/2026 (jamais de
// substitution muette, jamais un choix efface sans le dire).
const horsListe = lignes(VOIX_PROPOSEES, 'xtts:cml9804', () => '', '',
                         'Alphonse \u2014 France (XTTS)');
verifier('la voix hors liste est AJOUTEE, sous son nom',
         (voixDe(horsListe, 'xtts:cml9804') || {}).identite
           === 'Alphonse \u2014 France (XTTS)',
         JSON.stringify(voixDe(horsListe, 'xtts:cml9804')));
verifier('elle est sous « Voix actuelle », marquee comme actuelle et hors liste',
         groupes(horsListe).some(g => g.indexOf('Voix actuelle') >= 0)
         && voixDe(horsListe, 'xtts:cml9804').actuelle === true
         && voixDe(horsListe, 'xtts:cml9804').horsListe === true);
verifier('elle n a PAS de 2e ligne (son nom la dit deja en entier)',
         voixDe(horsListe, 'xtts:cml9804').deuxiemeLigne === '');

// Le CABLAGE : la liste est peinte a l ouverture et apres un choix, le tap
// choisit, le ▶ ecoute, la recherche filtre. Sans ces liens, la liste resterait
// muette a l ecran -- c'est le genre de defaut qui ne se voit qu'a l'usage.
verifier('le panneau peint la liste a son ouverture',
         source.includes('_voicePhraseVoix      = voixId;')
         && source.includes('_peindreListeVoixPhrase();'));
verifier('le tap sur une ligne choisit cette voix',
         source.includes("choix.addEventListener('click', () => _choisirVoixPhrase(l.id))"));
verifier('le ▶ ecoute LA voix de la ligne, sans rien changer',
         source.includes("play.addEventListener('click', () => _apercuVoixPhrase(l.id, play))"));
verifier('la recherche filtre la liste',
         source.includes("document.getElementById('voice-phrase-recherche')")
         && source.includes('_voicePhraseRecherche = e.target.value;'));
verifier('le choix enregistre bien pour TOUT le personnage',
         source.includes('await _updateCharacterVoice(nom, voixId, rate, pitch)'));
verifier('la recherche repart vide a l ouverture ET a la fermeture',
         (source.match(/_voicePhraseRecherche = '';/g) || []).length >= 3,
         (source.match(/_voicePhraseRecherche = '';/g) || []).length);
verifier('le select du menu deroulant n existe plus nulle part',
         !source.includes("getElementById('voice-phrase-select')")
         && !page.includes('id="voice-phrase-select"'),
         'page=' + page.includes('id="voice-phrase-select"')
         + ' code=' + source.includes("getElementById('voice-phrase-select')"));

console.log('');
console.log('5) la porte vers le casting (20/09/2026)');
// Demande de Laurent : « cette modale est moins riche que casting des voix ».
// Plutot que d'appauvrir le panneau ou de le remplacer -- il est le SEUL a dire
// QUI PARLE dans cette phrase -- on ajoute une PORTE vers la vraie fenetre, sur
// le personnage de la phrase. Ce que le test protege :
//   - le bouton est CACHE pour la narration : le narrateur n'a pas de ligne
//     dans le casting (sa voix se change dans le menu du haut) ;
//   - la porte FERME le panneau avant d'ouvrir : jamais deux fenetres empilees,
//     et on retrouve sa lecture en fermant le casting ;
//   - elle remet les filtres d'etat ET la recherche a zero avant d'ouvrir,
//     sinon elle ouvrirait le casting sur une liste ou le personnage est
//     invisible -- sans que rien ne l'explique ;
//   - elle surligne le personnage avec _allerAuPersonnage, soit EXACTEMENT le
//     reperage des noms cliquables du badge « partagee avec ... » (19/09/2026).
verifier('le bouton est CACHE pour la narration',
         source.includes("porteCasting.classList.toggle('hidden', !nom)"));
// On isole le bloc DE LA PORTE (de son bouton a la fin de son gestionnaire) :
// le fichier est en fin de ligne Windows (CRLF), donc on evite d'y chercher des
// retours a la ligne -- et le controle porte ainsi sur ce bloc, pas sur tout le
// fichier (ou _closeVoicePanel() apparait aussi pour la croix et le fond).
const debutPorte = source.indexOf(
  "document.getElementById('voice-phrase-cast-btn').addEventListener");
const blocPorte = source.slice(debutPorte, source.indexOf('});', debutPorte));
verifier('la porte existe et ne fait rien sans personnage',
         debutPorte >= 0
         && blocPorte.includes("addEventListener('click', async () => {")
         && blocPorte.includes('const nom = _personnageDePhrase(_voicePhraseIdx);')
         && blocPorte.includes('if (!nom) return;'));
verifier('elle ferme le panneau avant d ouvrir le casting',
         blocPorte.includes('_closeVoicePanel();')
         && blocPorte.indexOf('_closeVoicePanel();')
            < blocPorte.indexOf('await _openCastModal();'));
verifier('elle revient a la liste complete (filtre d etat + recherche)',
         blocPorte.includes("if (_castEtatFiltre !== 'T' || _castRecherche.trim()) {")
         && blocPorte.includes("_castEtatFiltre = 'T';")
         && blocPorte.includes("_castRecherche = '';"));
verifier('elle surligne le personnage (meme reperage que le badge de partage)',
         blocPorte.includes('_allerAuPersonnage(nom);'));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
