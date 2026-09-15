// Verifie la logique des menus de voix du casting SANS navigateur.
// ----------------------------------------------------------------------
// Le filtrage par genre vit dans frontend/app.js (fonction
// _construireMenuVoix). Ce test l'extrait DU FICHIER REEL (pas une copie :
// si elle est renommee ou deplacee, le test echoue bruyamment), lui donne un
// faux DOM minimal et verifie ce qui est produit :
//   - groupes Femmes / Hommes selon le filtre ;
//   - tri alphabetique dans chaque groupe ;
//   - la voix attribuee reste visible meme si le filtre la masque ;
//   - une voix disparue du catalogue est signalee, jamais remplacee en silence.
//
// Usage : node test_voix/test_filtre_genre.js
'use strict';

const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'frontend', 'app.js');
const source = fs.readFileSync(APP, 'utf8');

const debut = source.indexOf('function _construireMenuVoix');
// Fin de la tranche : la fonction SUIVANTE. Elle peut etre `async` (c'est le
// cas depuis le 14/09/2026 : _openCastModal rafraichit l'etat des moteurs de
// voix avant d'afficher les menus) : on recule donc d'un eventuel `async `
// pour ne pas couper au milieu du mot-cle. Si la fonction est renommee ou
// deplacee, le test echoue bruyamment (c'est voulu).
let fin = source.indexOf('function _openCastModal');
if (fin > 0 && source.slice(fin - 6, fin) === 'async ') fin -= 6;
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : fonction _construireMenuVoix introuvable dans app.js');
  process.exit(1);
}
const codeFonction = source.slice(debut, fin);

// --- faux DOM, juste ce qu'il faut ---
function fauxElement(tag) {
  return {
    tag, className: '', textContent: '', label: '', value: '',
    children: [],
    appendChild(enfant) { this.children.push(enfant); return enfant; },
    classList: { toggle() {}, add() {}, remove() {} },
  };
}
const fauxDocument = { createElement: fauxElement };

const VOIX = [
  { id: 'f1', name: 'Alice',     gender: 'F', region: 'France (NIMM Voix)' },
  { id: 'f2', name: 'Béatrice',  gender: 'F', region: 'France (Kyutai)' },
  { id: 'm1', name: 'Charles',   gender: 'M', region: 'Belgique' },
  { id: 'm2', name: 'David',     gender: 'M', region: 'Suisse' },
  { id: 'x1', name: 'SansGenre', gender: '',  region: 'Test' },
];

function menuPour(filtre, voixActuelle, catalogue, libelle) {
  const corps = 'var _castGenreFiltre = ' + JSON.stringify(filtre) + ';\n'
    + codeFonction + '\nreturn _construireMenuVoix;';
  const fabrique = new Function('document', '_allVoices', '_libelleCatalogue', corps);
  const construire = fabrique(fauxDocument, catalogue || VOIX, libelle || (() => ''));
  return construire(voixActuelle);
}

// Catalogue tel qu'il est REELLEMENT dans l'application : toutes les voix ont
// un genre (verifie : 135 voix, 73 F / 62 M, aucune sans genre).
const VOIX_AVEC_GENRE = VOIX.filter(v => v.gender);

function groupes(select) {
  return select.children.map(g => g.label);
}
function optionsDe(select, label) {
  const groupe = select.children.find(g => g.label === label);
  return groupe ? groupe.children.map(o => o.value) : [];
}

let echecs = 0;
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail ? '  -> ' + detail : ''));
    echecs++;
  }
}

console.log('');
console.log('1) filtre "Toutes" (defaut)');
const t = menuPour('T', 'f1');
verifier('groupes Femmes + Hommes + Autres',
  JSON.stringify(groupes(t)) === JSON.stringify(['\uD83D\uDC69 Femmes', '\uD83D\uDC68 Hommes', 'Autres']),
  groupes(t).join(' | '));
verifier('tri alphabetique des femmes',
  JSON.stringify(optionsDe(t, '\uD83D\uDC69 Femmes')) === JSON.stringify(['f1', 'f2']),
  optionsDe(t, '\uD83D\uDC69 Femmes').join(','));
verifier('voix attribuee selectionnee', t.value === 'f1', t.value);

console.log('2) filtre "Femmes"');
const f = menuPour('F', 'f1', VOIX_AVEC_GENRE);
verifier('un seul groupe Femmes', JSON.stringify(groupes(f)) === JSON.stringify(['\uD83D\uDC69 Femmes']),
  groupes(f).join(' | '));
verifier('voix masculine absente', !optionsDe(f, '\uD83D\uDC69 Femmes').includes('m1'));

console.log('3) filtre "Femmes" avec un personnage a voix masculine');
const fm = menuPour('F', 'm1', VOIX_AVEC_GENRE);
verifier('la voix actuelle est rappelee en tete',
  groupes(fm)[0] === '\u26A0\uFE0F Voix actuelle' && groupes(fm)[1] === '\uD83D\uDC69 Femmes',
  groupes(fm).join(' | '));
verifier('sa voix reste selectionnable', fm.value === 'm1', fm.value);

console.log('4) filtre "Hommes"');
const h = menuPour('M', 'm2', VOIX_AVEC_GENRE);
verifier('un seul groupe Hommes', JSON.stringify(groupes(h)) === JSON.stringify(['\uD83D\uDC68 Hommes']),
  groupes(h).join(' | '));
verifier('voix feminine absente', optionsDe(h, '\uD83D\uDC68 Hommes').indexOf('f1') === -1);

console.log('5) voix disparue du catalogue');
const inconnue = menuPour('T', 'voix-supprimee', VOIX_AVEC_GENRE);
verifier('groupe "Voix introuvable" present',
  groupes(inconnue).includes('\u26A0\uFE0F Voix introuvable'),
  groupes(inconnue).join(' | '));
verifier('la voix inconnue reste selectionnee', inconnue.value === 'voix-supprimee', inconnue.value);

console.log('6) voix sans genre renseigne (cas theorique) : securite');
const sansGenre = menuPour('F', 'f1');   // catalogue complet, avec la voix sans genre
verifier('elle reste accessible (pas de substitution silencieuse)',
  groupes(sansGenre).includes('Autres') &&
  optionsDe(sansGenre, 'Autres').indexOf('x1') !== -1,
  groupes(sansGenre).join(' | '));

// Cas REEL (Laurent, 15/09/2026, apres un re-cast de Shantaram) : le livre est
// caste avec une voix XTTS, mais la liste des voix proposees ne contient pas
// les XTTS (moteur pas encore pret, ou liste chargee avant son allumage). Le
// menu doit afficher le PRENOM de la voix, jamais son identifiant technique.
console.log('7) voix XTTS absente de la liste proposee : le prenom, pas l\'identifiant');
const LIBELLES = { 'xtts:cml9804': 'Alphonse (M) \u2014 France (XTTS)' };
const libelleCatalogue = (id) => LIBELLES[id] || '';
const xtts = menuPour('T', 'xtts:cml9804', VOIX_AVEC_GENRE, libelleCatalogue);
const avertissement = xtts.children.find(g =>
  g.label.indexOf('non proposee') >= 0 || g.label.indexOf('Pas de voix') >= 0 ||
  g.label.indexOf('introuvable') >= 0);
verifier('un groupe d\'avertissement est present', !!avertissement,
  groupes(xtts).join(' | '));
verifier('la voix est nommee par son prenom',
  !!avertissement && avertissement.children[0].textContent.indexOf('Alphonse') >= 0,
  avertissement && avertissement.children[0].textContent);
verifier('l\'identifiant technique n\'apparait pas',
  !!avertissement && avertissement.children[0].textContent.indexOf('cml9804') < 0,
  avertissement && avertissement.children[0].textContent);
verifier('la voix reste selectionnee', xtts.value === 'xtts:cml9804', xtts.value);

// Voix XTTS dont le moteur est ETEINT : le nom doit etre la aussi, avec la
// raison en clair (et non l'identifiant).
console.log('8) voix XTTS avec moteur eteint : nom + raison');
const codeMoteurs = 'var _castGenreFiltre = "T";\n'
  + 'var _moteursEtat = { xtts: { actif: false, pret: false, nom: "XTTS v2" } };\n';
const fabriqueEteint = new Function('document', '_allVoices', '_libelleCatalogue',
  codeMoteurs + codeFonction + '\nreturn _construireMenuVoix;');
const menuEteint = fabriqueEteint(fauxDocument, VOIX_AVEC_GENRE, libelleCatalogue)('xtts:cml9804');
const groupeEteint = menuEteint.children.find(g => g.label.indexOf('Pas de voix') >= 0);
verifier('le groupe dit que le moteur est eteint', !!groupeEteint,
  groupes(menuEteint).join(' | '));
verifier('le libelle porte le prenom ET la raison',
  !!groupeEteint
  && groupeEteint.children[0].textContent.indexOf('Alphonse') >= 0
  && groupeEteint.children[0].textContent.indexOf('XTTS v2 eteint') >= 0,
  groupeEteint && groupeEteint.children[0].textContent);

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
