// Verifie le sort d'une voix dont le moteur n'est pas pret dans la fenetre du
// casting (session du 14/09/2026).
// ----------------------------------------------------------------------
// Meme technique que test_filtre_genre.js : la fonction `_lignesVoixPersonnage`
// (elle s'appelait `_construireMenuVoix` jusqu'au 22/09/2026, quand c'etait
// encore un menu deroulant) est extraite DU FICHIER REEL (jamais recopiee :
// renommee ou deplacee, le test echoue bruyamment), avec l'etat des moteurs tel
// que /api/moteurs le renvoie. Depuis qu'elle rend une LISTE DE LIGNES, il n'y a
// plus besoin de faux DOM : on eprouve la regle, pas le dessin.
//
// Demande de Laurent : une voix qu'on ne peut pas ecouter tout de suite ne
// doit pas etre proposee ; et un personnage qui en portait une doit afficher
// « pas de voix » -- JAMAIS etre remplace en silence par une autre voix.
//
// Usage : node test_voix/test_voix_ecoutables.js
'use strict';

const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'frontend', 'app.js');
const source = fs.readFileSync(APP, 'utf8');

const debut = source.indexOf('function _lignesVoixPersonnage');
let fin = source.indexOf('function _openCastModal');
if (fin > 0 && source.slice(fin - 6, fin) === 'async ') fin -= 6;
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : fonction _lignesVoixPersonnage introuvable dans app.js');
  process.exit(1);
}
const codeFonction = source.slice(debut, fin);

const VOIX_KYUTAI = 'kyutai:12205_11650_000004-0002';

// Catalogue tel que /api/voices le renvoie moteur Kyutai ETEINT : les voix
// Kyutai n'y figurent plus (c'est precisement l'objet de cette session).
const CATALOGUE_SANS_KYUTAI = [
  { id: 'fr-CH-ArianeNeural', name: 'Ariane', gender: 'F', region: 'Suisse' },
  { id: 'fr-FR-HenriNeural',  name: 'Henri',  gender: 'M', region: 'France' },
];
// ... et tel qu'il l'est quand le moteur est ALLUME ET PRET.
const CATALOGUE_AVEC_KYUTAI = CATALOGUE_SANS_KYUTAI.concat([
  { id: VOIX_KYUTAI, name: 'Eleonore', gender: 'F', region: 'France (Kyutai)' },
]);

const MOTEURS_ETEINTS = {
  kyutai: { nom: 'Kyutai',  actif: false, pret: false },
  xtts:   { nom: 'XTTS v2', actif: false, pret: false },
};
const MOTEURS_CHARGEMENT = {
  kyutai: { nom: 'Kyutai',  actif: true,  pret: false },
  xtts:   { nom: 'XTTS v2', actif: false, pret: false },
};
const MOTEURS_PRETS = {
  kyutai: { nom: 'Kyutai',  actif: true,  pret: true },
  xtts:   { nom: 'XTTS v2', actif: false, pret: false },
};

function menuPour(voixActuelle, catalogue, etatMoteurs, noms) {
  const corps = 'var _castGenreFiltre = "T";\n'
    + 'var _moteursEtat = ' + JSON.stringify(etatMoteurs || {}) + ';\n'
    + codeFonction + '\nreturn _lignesVoixPersonnage;';
  const fabrique = new Function('_allVoices', '_libelleCatalogue', corps);
  // `noms` = catalogue complet (id -> libelle). Sans lui, la fonction se
  // comporte comme avant le 15/09/2026 : message generique sans prenom.
  const libelle = (id) => (noms || {})[id] || '';
  const construire = fabrique(catalogue, libelle);
  return construire(voixActuelle);
}

// --- Helpers : on lit les LIGNES, pas un menu. ---
function groupes(lignes) {
  return lignes.filter(l => l.genre === 'groupe').map(l => l.libelle);
}
function optionsDe(lignes, label) {
  const ids = [];
  let dedans = false;
  lignes.forEach(l => {
    if (l.genre === 'groupe') dedans = (l.libelle === label);
    else if (dedans) ids.push(l.id);
  });
  return ids;
}
// Ce qui s'ecrit pour une voix : sa ligne 1, puis sa ligne 2 (moteur + etat).
function libellesDe(lignes, label) {
  const ids = optionsDe(lignes, label);
  return ids.map(id => {
    const l = lignes.find(x => x.genre === 'voix' && x.id === id);
    return l ? (l.identite + (l.deuxiemeLigne ? ' ' + l.deuxiemeLigne : '')) : '';
  });
}
// La voix que la liste marque comme celle du personnage (le ✔).
function voixActive(lignes) {
  const l = lignes.find(x => x.genre === 'voix' && x.actuelle);
  return l ? l.id : null;
}

const AVERTISSEMENT = '\u26A0\uFE0F Voix introuvable';
const PAS_DE_VOIX = (raison) => '\u26A0\uFE0F Pas de voix (' + raison + ')';

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
console.log('1) moteur Kyutai ETEINT, un personnage porte une voix Kyutai');
const a = menuPour(VOIX_KYUTAI, CATALOGUE_SANS_KYUTAI, MOTEURS_ETEINTS);
verifier('un groupe « pas de voix » est affiche',
  groupes(a).includes(PAS_DE_VOIX('Kyutai eteint')), groupes(a).join(' | '));
verifier('ce n\'est PAS le message « voix introuvable »',
  !groupes(a).includes(AVERTISSEMENT), groupes(a).join(' | '));
verifier('le libelle dit « Pas de voix - Kyutai eteint »',
  libellesDe(a, PAS_DE_VOIX('Kyutai eteint'))[0] === 'Pas de voix \u2014 Kyutai eteint',
  libellesDe(a, PAS_DE_VOIX('Kyutai eteint'))[0]);
verifier('la voix du personnage reste marquee d un ✔ (aucune substitution silencieuse)',
  voixActive(a) === VOIX_KYUTAI, String(voixActive(a)));
verifier('les voix encore ecoutables sont bien proposees',
  optionsDe(a, '\uD83D\uDC69 Femmes').includes('fr-CH-ArianeNeural'));

// Avec le catalogue complet (route /api/voix_catalogue, 15/09/2026), le
// libelle porte le PRENOM de la voix en plus de la raison : c'est ce que
// Laurent voit desormais au lieu de l'identifiant technique.
console.log('1 bis) meme cas, mais avec le catalogue complet charge');
const NOMS = {}; NOMS[VOIX_KYUTAI] = 'Adèle (F) \u2014 France (Kyutai)';
const a2 = menuPour(VOIX_KYUTAI, CATALOGUE_SANS_KYUTAI, MOTEURS_ETEINTS, NOMS);
verifier('le libelle commence par le prenom de la voix',
  (libellesDe(a2, PAS_DE_VOIX('Kyutai eteint'))[0] || '').indexOf('Adèle') === 0,
  libellesDe(a2, PAS_DE_VOIX('Kyutai eteint'))[0]);
verifier('et se termine par la raison (moteur eteint)',
  (libellesDe(a2, PAS_DE_VOIX('Kyutai eteint'))[0] || '').indexOf('Kyutai eteint') > 0,
  libellesDe(a2, PAS_DE_VOIX('Kyutai eteint'))[0]);

console.log('2) moteur ALLUME mais modele encore en chargement');
const b = menuPour(VOIX_KYUTAI, CATALOGUE_SANS_KYUTAI, MOTEURS_CHARGEMENT);
verifier('en chargement = pas encore ecoutable -> « pas de voix »',
  groupes(b).includes(PAS_DE_VOIX('Kyutai en chargement')), groupes(b).join(' | '));
verifier('le libelle le dit clairement (chargement, pas eteint)',
  libellesDe(b, PAS_DE_VOIX('Kyutai en chargement'))[0] === 'Pas de voix \u2014 Kyutai en chargement',
  libellesDe(b, PAS_DE_VOIX('Kyutai en chargement'))[0]);

console.log('3) moteur PRET, la voix est au catalogue');
const c = menuPour(VOIX_KYUTAI, CATALOGUE_AVEC_KYUTAI, MOTEURS_PRETS);
verifier('aucun groupe d\'avertissement',
  !groupes(c).some(g => g.indexOf('\u26A0\uFE0F') === 0), groupes(c).join(' | '));
verifier('la voix Kyutai est proposee normalement, avec les femmes',
  optionsDe(c, '\uD83D\uDC69 Femmes').includes(VOIX_KYUTAI));

console.log('4) moteur PRET mais la voix a disparu du catalogue');
const d = menuPour(VOIX_KYUTAI, CATALOGUE_SANS_KYUTAI, MOTEURS_PRETS);
verifier('c\'est bien « voix introuvable » (et pas « pas de voix »)',
  groupes(d).includes(AVERTISSEMENT) && !groupes(d).includes(PAS_DE_VOIX('Kyutai eteint')),
  groupes(d).join(' | '));

console.log('5) voix normale (Edge) alors que les moteurs sont eteints');
const e = menuPour('fr-CH-ArianeNeural', CATALOGUE_SANS_KYUTAI, MOTEURS_ETEINTS);
verifier('aucun avertissement : elle est toujours ecoutable',
  !groupes(e).some(g => g.indexOf('\u26A0\uFE0F') === 0), groupes(e).join(' | '));
verifier('elle reste marquee d un ✔', voixActive(e) === 'fr-CH-ArianeNeural',
  String(voixActive(e)));

console.log('6) etat des moteurs inconnu (echec de /api/moteurs) : securite');
const f = menuPour(VOIX_KYUTAI, CATALOGUE_SANS_KYUTAI, {});
verifier('on retombe sur « voix introuvable », sans plantage',
  groupes(f).includes(AVERTISSEMENT), groupes(f).join(' | '));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
