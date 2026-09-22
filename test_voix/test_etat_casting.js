// Verifie les badges et le filtre d'etat de la fenetre du casting, SANS
// navigateur (session du 15/09/2026).
// ----------------------------------------------------------------------
// La logique vit dans frontend/app.js (fonction _etatCasting). Ce test
// l'extrait DU FICHIER REEL (jamais une copie : si la fonction est renommee
// ou deplacee, le test echoue bruyamment) et verifie ce qu'elle produit :
//   - « a caster »  : le personnage parle souvent mais porte encore la voix
//                     generique des petits roles -> il n'a pas de voix a lui ;
//   - « partagee »  : sa voix est aussi portee par d'autres personnages ;
//   - un VRAI petit role (peu de repliques, voix generique) ne recoit AUCUN
//     badge : c'est le cas normal, il ne doit pas noyer la liste ;
//   - le filtre « a caster » / « voix partagee » ne garde que les bonnes lignes ;
//   - AVEC QUI une voix est partagee (19/09/2026) : le badge n'ecrit plus
//     « partagee (2) » mais « partagee avec Edmond, Busoni » ;
//   - quelles voix sont LIBRES (_etatVoix) : ni portees par un personnage, ni
//     la voix du NARRATEUR du livre, ni les voix generiques des petits roles ;
//   - les deux textes d'usage d'une voix : la marque courte des menus
//     (« · LIBRE », « · partagee (2) ») et la phrase complete ECRITE dans le
//     panneau « Voir la voix » -- sur mobile il n'y a ni survol ni appui long,
//     donc tout ce qui compte doit etre ecrit.
//
// Usage : node test_voix/test_etat_casting.js
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

const debut = source.indexOf('function _etatCasting');
// La borne de fin a change le 22/09/2026 : `_construireMenuVoix` (le menu
// deroulant du casting) n'existe plus, remplace par `_lignesVoixPersonnage`.
const fin = source.indexOf('function _lignesVoixPersonnage');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : fonction _etatCasting introuvable dans app.js');
  process.exit(1);
}
const codeFonction = source.slice(debut, fin);

// Le seuil des petits roles est LU dans app.js : une seule valeur fait foi,
// et test_voix/test_pool_casting.py verifie qu'elle egale celle du serveur.
const seuil = source.match(/_CAST_MINOR_THRESHOLD\s*=\s*(\d+)/);
const generiques = source.match(/_CAST_VOIX_GENERIQUES\s*=\s*\[([^\]]+)\]/);
if (!seuil || !generiques) {
  console.error('ECHEC : seuil ou voix generiques introuvables dans app.js');
  process.exit(1);
}
const SEUIL = parseInt(seuil[1], 10);
const VOIX_GENERIQUES = generiques[1].split(',').map(s => s.trim().replace(/^'|'$/g, ''));

const fabrique = new Function(
  'const _CAST_MINOR_THRESHOLD = ' + SEUIL + ';\n'
  + 'const _CAST_VOIX_GENERIQUES = ' + JSON.stringify(VOIX_GENERIQUES) + ';\n'
  + codeFonction
  + '\nreturn { _etatCasting: _etatCasting, _etatVoix: _etatVoix,'
  + ' _resumeNoms: _resumeNoms, _pitchPartageLibre: _pitchPartageLibre };');
const extrait     = fabrique();
const etatCasting = extrait._etatCasting;
const calculUsage = extrait._etatVoix;
const resumeNoms  = extrait._resumeNoms;
const pitchLibre  = extrait._pitchPartageLibre;

const GENERIQUE_F = VOIX_GENERIQUES[0];
const GENERIQUE_M = VOIX_GENERIQUES[1];

function ligne(nom, voice_id, total) {
  return { nom: nom, v: { voice_id: voice_id }, total: total };
}

// --- Un casting de dix personnages, comme un vrai livre ---
const ROWS = [
  ligne('Principal 1', 'fr-FR-DeniseNeural', 900),   // voix dediee
  ligne('Principal 2', 'xtts:voix1', 700),            // voix dediee
  ligne('Partage 1', 'xtts:voix3', 400),              // meme voix que Partage 2
  ligne('Partage 2', 'xtts:voix3', 350),              // meme voix que Partage 1
  ligne('Sans voix 1', GENERIQUE_M, 120),             // gros role sans voix a lui
  ligne('Sans voix 2', GENERIQUE_F, 60),              // idem, voix feminine
  ligne('Petit role 1', GENERIQUE_F, 2),              // petit role normal
  ligne('Petit role 2', GENERIQUE_M, 1),              // petit role normal
  ligne('Petit role 3', GENERIQUE_F, 3),              // juste sous le seuil
];

console.log('1) detection des personnages « a caster »');
const etat = etatCasting(ROWS, 'T');
verifier('un gros role en voix generique est « a caster »',
         etat.aCaster(ROWS[4]) && etat.aCaster(ROWS[5]));
verifier('un petit role (2 repliques) ne l est PAS', !etat.aCaster(ROWS[6]));
verifier('un personnage juste sous le seuil ne l est PAS', !etat.aCaster(ROWS[8]));
verifier('un role a voix dediee ne l est jamais', !etat.aCaster(ROWS[0]));
verifier('compteur de personnes a caster = 2', etat.nbCaster === 2, etat.nbCaster);

console.log('');
console.log('2) detection des voix partagees');
verifier('les deux personnages au meme timbre sont « partagee »',
         etat.partagee(ROWS[2]) && etat.partagee(ROWS[3]));
verifier('le compte est bien de 2 personnages',
         etat.compteParVoix['xtts:voix3'] === 2, etat.compteParVoix['xtts:voix3']);
verifier('une voix unique n est pas « partagee »', !etat.partagee(ROWS[0]));
verifier('un personnage « a caster » n est pas compte deux fois',
         !etat.partagee(ROWS[4]));
verifier('compteur de voix partagees = 1', etat.nbPartagee === 1, etat.nbPartagee);
// La voix generique des petits roles est partagee par construction : elle ne
// doit jamais etre signalee, sinon la liste serait pleine de faux alertes.
verifier('la voix generique des petits roles n est pas « partagee »',
         etat.compteParVoix[GENERIQUE_F] === undefined
         && !etat.partagee(ROWS[6]) && !etat.partagee(ROWS[7]));

console.log('');
console.log('3) filtre par etat des personnages');
const caster = etatCasting(ROWS, 'caster');
verifier('filtre « a caster » : seulement les bonnes lignes',
         caster.rowsFiltrees.length === 2
         && caster.rowsFiltrees.every(r => r.v.voice_id.indexOf('piper:') === 0),
         caster.rowsFiltrees.map(r => r.nom));
const partagee = etatCasting(ROWS, 'partagee');
verifier('filtre « partagee » : seulement les bonnes lignes',
         partagee.rowsFiltrees.length === 2
         && partagee.rowsFiltrees.every(r => r.v.voice_id === 'xtts:voix3'),
         partagee.rowsFiltrees.map(r => r.nom));
verifier('filtre « Tous » : toutes les lignes',
         etatCasting(ROWS, 'T').rowsFiltrees.length === ROWS.length);

console.log('');
console.log('4) securite (donnees incompletes)');
const bancal = [ligne('Sans voix du tout', '', 50), { nom: 'Vide', v: null, total: 0 }];
let plantage = null;
let etatBancal = null;
try {
  etatBancal = etatCasting(bancal, 'T');
} catch (e) {
  plantage = e.message;
}
verifier('aucun plantage sur une voix vide', plantage === null, plantage);
verifier('une voix vide n est ni « a caster » ni « partagee »',
         etatBancal
         && !etatBancal.aCaster(bancal[0]) && !etatBancal.partagee(bancal[0])
         && !etatBancal.aCaster(bancal[1]));

console.log('');
console.log('5) les NOMS des porteurs (avec QUI est-elle partagee ?)');
const etatNoms = etatCasting(ROWS, 'T');
verifier('les porteurs sont connus, du plus bavard au plus discret',
         JSON.stringify((etatNoms.nomsParVoix['xtts:voix3'] || []).map(x => x.nom))
           === JSON.stringify(['Partage 1', 'Partage 2']),
         JSON.stringify(etatNoms.nomsParVoix['xtts:voix3']));
verifier('chaque porteur vient avec son nombre de repliques',
         (etatNoms.nomsParVoix['xtts:voix3'] || []).map(x => x.total).join(',')
           === '400,350',
         JSON.stringify((etatNoms.nomsParVoix['xtts:voix3'] || []).map(x => x.total)));
verifier('une voix portee par un seul personnage a UN porteur',
         (etatNoms.nomsParVoix['fr-FR-DeniseNeural'] || []).length === 1);
verifier('la voix generique des petits roles n a aucun porteur liste',
         etatNoms.nomsParVoix[GENERIQUE_F] === undefined);

console.log('');
console.log('6) quelles voix sont LIBRES (le reservoir ou piocher)');
// Un catalogue propose reduit, comme un livre reel : des voix portees, une
// partagee, deux libres, une generique et la voix du narrateur.
const NARRATEUR = 'edge:narrateur';
const PROPOSEES = [
  { id: 'fr-FR-DeniseNeural', name: 'Denise' },    // portee par Principal 1
  { id: 'xtts:voix1',         name: 'Alphonse' },  // portee par Principal 2
  { id: 'xtts:voix3',         name: 'Busoni' },    // partagee
  { id: 'xtts:voix9',         name: 'Yousef' },    // LIBRE
  { id: 'kokoro:libre2',      name: 'Zoe' },       // LIBRE
  { id: GENERIQUE_F,          name: 'Siwis' },     // generique : jamais libre
  { id: NARRATEUR,            name: 'Ariane' },    // narrateur : prise
];
const avis = calculUsage(etatNoms, PROPOSEES, NARRATEUR);
verifier('seules les deux vraies libres sont proposees',
         JSON.stringify(avis.libres.map(v => v.id))
           === JSON.stringify(['xtts:voix9', 'kokoro:libre2']),
         JSON.stringify(avis.libres.map(v => v.id)));
verifier('le compte des voix libres suit', avis.nbLibres === 2, avis.nbLibres);
verifier('une voix portee par un personnage n est pas libre',
         !avis.libres.some(v => v.id === 'xtts:voix1'));
verifier('une voix partagee n est pas libre non plus',
         !avis.libres.some(v => v.id === 'xtts:voix3'));
verifier('la voix generique des petits roles n est jamais libre',
         !avis.libres.some(v => v.id === GENERIQUE_F));
verifier('la voix du NARRATEUR est prise, donc pas libre',
         !avis.libres.some(v => v.id === NARRATEUR));
verifier('toutes les voix proposees sont comptees',
         avis.nbProposees === PROPOSEES.length, avis.nbProposees);

console.log('');
console.log('7) la marque courte des menus deroulants');
verifier('voix libre', avis.marque('xtts:voix9') === ' \u00b7 LIBRE',
         avis.marque('xtts:voix9'));
verifier('voix prise : le nom de son porteur',
         avis.marque('xtts:voix1') === ' \u00b7 Principal 2',
         avis.marque('xtts:voix1'));
verifier('voix partagee : le nombre de porteurs',
         avis.marque('xtts:voix3') === ' \u00b7 partag\u00e9e (2)',
         avis.marque('xtts:voix3'));
verifier('voix du narrateur', avis.marque(NARRATEUR) === ' \u00b7 narrateur',
         avis.marque(NARRATEUR));
verifier('voix generique des petits roles',
         avis.marque(GENERIQUE_F) === ' \u00b7 petits r\u00f4les',
         avis.marque(GENERIQUE_F));
verifier('aucune marque sans voix', avis.marque('') === '', avis.marque(''));

console.log('');
console.log('8) la phrase complete ECRITE (panneau « Voir la voix »)');
verifier('voix libre', avis.phrase('xtts:voix9').indexOf('Libre') === 0,
         avis.phrase('xtts:voix9'));
verifier('un seul porteur : son nom et ses repliques',
         avis.phrase('xtts:voix1').indexOf('Principal 2') > 0
         && avis.phrase('xtts:voix1').indexOf('700') > 0,
         avis.phrase('xtts:voix1'));
const phrasePartagee = avis.phrase('xtts:voix3');
verifier('partagee : le nombre ET les noms (jamais un « (2) » tout seul)',
         phrasePartagee.indexOf('2 personnages') > 0
         && phrasePartagee.indexOf('Partage 1') > 0
         && phrasePartagee.indexOf('Partage 2') > 0,
         phrasePartagee);
verifier('generique : la phrase dit pourquoi elle est partagee',
         avis.phrase(GENERIQUE_F).indexOf('Voix g\u00e9n\u00e9rique') === 0
         && avis.phrase(GENERIQUE_F).indexOf('petits r\u00f4les') > 0,
         avis.phrase(GENERIQUE_F));
verifier('narrateur : la phrase dit que c est la voix du narrateur',
         avis.phrase(NARRATEUR).indexOf('NARRATEUR') > 0,
         avis.phrase(NARRATEUR));
verifier('aucune phrase sans voix', avis.phrase('') === '', avis.phrase(''));

// Cas REEL de Laurent (19/09/2026, « 22/11/63 ») : le narrateur EST Jake
// Epping, et il a choisi la MEME voix pour les deux -- volontairement. La
// phrase doit dire LES DEUX roles, sinon la fiche laisserait croire que Jake
// n'a pas sa voix ; et cette voix reste PRISE, donc jamais « libre ».
const casNarrateur = calculUsage(
  etatCasting([ligne('Jake Epping', NARRATEUR, 843)], 'T'),
  [{ id: NARRATEUR, name: 'Ariane' }], NARRATEUR);
verifier('la voix du narrateur reste prise, jamais « libre »',
         casNarrateur.nbLibres === 0 && casNarrateur.libres.length === 0);
verifier('la phrase dit AUSSI quel personnage parle avec',
         casNarrateur.phrase(NARRATEUR).indexOf('Jake Epping') > 0,
         casNarrateur.phrase(NARRATEUR));
verifier('et rappelle que le narrateur PEUT etre un personnage',
         casNarrateur.phrase(NARRATEUR).indexOf('narrateur peut') > 0,
         casNarrateur.phrase(NARRATEUR));
verifier('la marque courte reste « narrateur » (les menus sont etroits)',
         casNarrateur.marque(NARRATEUR) === ' \u00b7 narrateur',
         casNarrateur.marque(NARRATEUR));
verifier('le personnage compte bien UN porteur de cette voix',
         (casNarrateur.nomsParVoix[NARRATEUR] || []).length === 1);

// Cas REEL (livre « 22/11/63 », 19/09/2026) : une voix portee par DIX-HUIT
// personnages. La phrase doit rester lisible et renvoyer a l'onglet « Voix
// partagee », qui les liste tous un par ligne.
const beaucoup = [];
for (let i = 1; i <= 9; i++) beaucoup.push(ligne('Porteur ' + i, 'xtts:foule', 100 - i));
const avisFoule = calculUsage(etatCasting(beaucoup, 'T'),
                              [{ id: 'xtts:foule', name: 'Foule' }], '');
verifier('au-dela de six noms, elle renvoie a l onglet « Voix partagee »',
         avisFoule.phrase('xtts:foule').indexOf('9 personnages') > 0
         && avisFoule.phrase('xtts:foule').indexOf('et 3 autres') > 0
         && avisFoule.phrase('xtts:foule').indexOf('Voix partag') > 0,
         avisFoule.phrase('xtts:foule'));
verifier('mais le compte total reste juste',
         avisFoule.nomsParVoix['xtts:foule'].length === 9);

console.log('');
console.log('9) le resume des noms (le badge doit rester court)');
verifier('un nom', resumeNoms(['Edmond']) === 'Edmond');
verifier('deux noms', resumeNoms(['Edmond', 'Busoni']) === 'Edmond, Busoni');
verifier('trois noms : deux + « et 1 autre »',
         resumeNoms(['Edmond', 'Busoni', 'Simbad']) === 'Edmond, Busoni et 1 autre',
         resumeNoms(['Edmond', 'Busoni', 'Simbad']));
verifier('quatre noms : deux + « et 2 autres »',
         resumeNoms(['A', 'B', 'C', 'D']) === 'A, B et 2 autres',
         resumeNoms(['A', 'B', 'C', 'D']));
verifier('aucun nom', resumeNoms([]) === '' && resumeNoms() === '');

console.log('');
console.log('10) securite (donnees absentes)');
let plantageUsage = null;
let avisVide = null;
try {
  avisVide = calculUsage(null, null, null);
} catch (e) {
  plantageUsage = e.message;
}
verifier('aucun plantage sans etat ni liste de voix', plantageUsage === null,
         plantageUsage);
verifier('aucune marque ni phrase sans voix (jamais « undefined »)',
         avisVide.marque('') === '' && avisVide.phrase('') === '');
verifier('une voix inconnue est vue comme libre (aucun porteur)',
         avisVide.marque('x') === ' \u00b7 LIBRE', avisVide.marque('x'));

console.log('');
console.log('11) hauteur proposee quand on PARTAGE une voix deja portee');
// Demande de Laurent (BACKLOG du 15/09/2026) : quand on donne a un personnage
// une voix qu'un autre porte deja, on lui applique une hauteur differente --
// sinon les deux timbres resteraient indiscernables.
verifier('la voix n est portee par personne : on propose +8Hz',
         pitchLibre([]) === 8, pitchLibre([]));
verifier('aucune donnee du tout : +8Hz aussi, sans plantage',
         pitchLibre() === 8, pitchLibre());
verifier('+0Hz est pris : on propose +8Hz',
         pitchLibre([0]) === 8, pitchLibre([0]));
verifier('0 et +8 sont pris : on descend a -8Hz',
         pitchLibre([0, 8]) === -8, pitchLibre([0, 8]));
verifier('et on continue par +12, puis -12',
         pitchLibre([0, 8, -8]) === 12 && pitchLibre([0, 8, -8, 12]) === -12,
         pitchLibre([0, 8, -8, 12]));
const prises = [0, 8, -8, 12, -12];
verifier('la hauteur proposee n est JAMAIS deja prise',
         prises.indexOf(pitchLibre(prises)) < 0, pitchLibre(prises));
verifier('c est la plus petite difference libre',
         pitchLibre(prises) === 16, pitchLibre(prises));
verifier('tout est pris : on retombe sur +0Hz (jamais de plantage)',
         pitchLibre([0, 8, -8, 12, -12, 16, -16, 4, -4, 20, -20]) === 0,
         pitchLibre([0, 8, -8, 12, -12, 16, -16, 4, -4, 20, -20]));
verifier('toujours un pas de 4 Hz (le pas du curseur du casting)',
         [8, -8, 12, -12, 16].every(p => (p % 4) === 0));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
