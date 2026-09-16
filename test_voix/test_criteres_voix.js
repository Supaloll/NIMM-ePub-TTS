// Verifie les CRITERES FIXES d'annotation des voix (session du 16/09/2026).
// ----------------------------------------------------------------------
// Demande de Laurent : au lieu de noter une voix au texte libre, on choisit
// dans des listes fermees (age, timbre, debit, accent, registre, role).
//
// Ce test verifie DEUX choses, et c'est le coeur de l'affaire :
//   1. les listes proposees par la page sont EXACTEMENT celles de main.py
//      (elles sont lues ici dans le fichier du serveur : une valeur ajoutee
//      cote serveur sans passer par la page, ou l'inverse, fait echouer le
//      test) ;
//   2. ce que la page ENVOIE porte bien les cles attendues par le serveur --
//      une faute de classe ou d'identifiant perdrait l'annotation en silence.
//
// Meme technique que test_voix_ecoutables.js : les fonctions sont extraites DU
// FICHIER REEL (jamais recopiees), avec un faux DOM minimal et un faux fetch.
//
// Usage : node test_voix/test_criteres_voix.js
'use strict';

const fs = require('fs');
const path = require('path');

const APP  = path.join(__dirname, '..', 'frontend', 'app.js');
const MAIN = path.join(__dirname, '..', 'main.py');
const source = fs.readFileSync(APP, 'utf8');

// --- 1) les criteres, lus dans main.py (source de verite) -------------
function lireCriteresDuServeur() {
  const src = fs.readFileSync(MAIN, 'utf8');
  const debut = src.indexOf('CRITERES_VOIX = [');
  const fin = src.indexOf('CRITERES_VOIX_CLES');
  if (debut < 0 || fin <= debut) {
    console.error('ECHEC : CRITERES_VOIX introuvable dans main.py');
    process.exit(1);
  }
  const bloc = src.slice(debut, fin);
  const criteres = [];
  const reCritere = /\(\s*"([a-z_]+)",\s*"([^"]+)",\s*\[([\s\S]*?)\]/g;
  let m;
  while ((m = reCritere.exec(bloc)) !== null) {
    const valeurs = [];
    const reValeur = /\(\s*"([a-z_]+)",\s*"([^"]+)"\s*\)/g;
    let v;
    while ((v = reValeur.exec(m[3])) !== null) {
      valeurs.push({ valeur: v[1], libelle: v[2] });
    }
    criteres.push({ cle: m[1], libelle: m[2], valeurs: valeurs });
  }
  return criteres;
}

const CRITERES = lireCriteresDuServeur();

// --- 2) les fonctions de la page, extraites de app.js -----------------
function extraire(debutNom, finNom) {
  const debut = source.indexOf(debutNom);
  let fin = source.indexOf(finNom);
  if (fin > 0 && source.slice(fin - 6, fin) === 'async ') fin -= 6;
  if (debut < 0 || fin <= debut) {
    console.error('ECHEC : %s introuvable dans app.js', debutNom);
    process.exit(1);
  }
  return source.slice(debut, fin);
}

const CODE = [
  extraire('function _familleDeVoix', 'function _libelleFamille'),
  extraire('function _libelleFamille', 'async function _chargerAnnotationsVoix'),
  extraire('function _listeOptions', 'function _majStyleCritere'),
  extraire('function _majStyleCritere', 'function _construireLigneVoix'),
  extraire('function _construireLigneVoix', 'function _majRecapEcouteur'),
  extraire('async function _sauverAnnotationVoix', 'async function _ecouterVoix'),
].join('\n');

// --- 3) faux DOM : juste ce qu'il faut pour une ligne de voix ---------
function fauxElement(tag) {
  const el = {
    tag, className: '', textContent: '', title: '', type: '',
    placeholder: '', dataset: {}, children: [], listeners: {},
    appendChild(enfant) { this.children.push(enfant); return enfant; },
    addEventListener(nom, cb) {
      (this.listeners[nom] = this.listeners[nom] || []).push(cb);
    },
    classList: {
      add(c) {
        if (!el.className.split(/\s+/).includes(c)) {
          el.className = (el.className + ' ' + c).trim();
        }
      },
      remove(c) {
        el.className = el.className.split(/\s+/).filter(x => x !== c).join(' ');
      },
      toggle(c, actif) { if (actif) this.add(c); else this.remove(c); },
      contains(c) { return el.className.split(/\s+/).includes(c); },
    },
  };
  el.querySelectorAll = (sel) => {
    const classe = sel.replace(/^\./, '');
    const trouves = [];
    const parcourir = (noeud) => {
      noeud.children.forEach((enfant) => {
        if ((enfant.className || '').split(/\s+/).includes(classe)) {
          trouves.push(enfant);
        }
        parcourir(enfant);
      });
    };
    parcourir(el);
    return trouves;
  };
  el.querySelector = (sel) => el.querySelectorAll(sel)[0] || null;
  // Un vrai <select> ne peut PAS prendre une valeur absente de sa liste : il
  // retombe sur « rien du tout ». On reproduit ce comportement, sinon le test
  // ne dirait rien du cas « critere retire du serveur » (valeur devenue
  // inconnue dans une annotation ancienne).
  let valeurInterne = '';
  Object.defineProperty(el, 'value', {
    get() { return valeurInterne; },
    set(v) {
      const vide = (v === undefined || v === null);
      // Seul un <select> filtre : une <option> garde toujours sa valeur.
      if (el.tag !== 'select') {
        valeurInterne = vide ? '' : v;
        return;
      }
      const connue = !vide && el.children.some(o => o.value === v);
      valeurInterne = (vide || !connue) ? '' : v;
    },
  });
  return el;
}

const fauxDocument = { createElement: fauxElement };
const FAMILLES_VOIX = [['edge', 'Edge'], ['kokoro', 'Kokoro'], ['kyutai', 'Kyutai'],
                       ['xtts', 'XTTS v2'], ['piper', 'Piper']];

let envois = [];
function fauxFetch(url, options) {
  envois.push({ url: url, corps: JSON.parse((options || {}).body || '{}') });
  return Promise.resolve({
    ok: true,
    json: async () => ({ ok: true, annotations: {} }),
  });
}

let echecs = 0;
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail !== undefined ? '  -> ' + detail : ''));
    echecs++;
  }
}

// --- 4) fabrique une ligne de voix, comme le lecteur le fait ----------
function lignePour(voix, annotation, criteres) {
  // _annotationsVoix est indexe par IDENTIFIANT de voix : c'est la forme du
  // fichier de notes (data/annotations_voix.json) et de /api/annotations_voix.
  const annotees = (annotation && Object.keys(annotation).length)
    ? { [voix.id]: annotation } : {};
  const corps = 'var _annotationsVoix = ' + JSON.stringify(annotees) + ';\n'
    + 'var _criteresVoix = ' + JSON.stringify(criteres || CRITERES) + ';\n'
    + 'function _majRecapEcouteur() {}\n'
    + CODE + '\nreturn { _construireLigneVoix: _construireLigneVoix,'
    + ' _sauverAnnotationVoix: _sauverAnnotationVoix };';
  const fabrique = new Function('document', 'fetch', 'FAMILLES_VOIX', corps);
  const api = fabrique(fauxDocument, fauxFetch, FAMILLES_VOIX);
  return { li: api._construireLigneVoix(voix), api: api };
}

const CLES_SERVEUR = CRITERES.map(c => c.cle);

console.log('');
console.log('1) les criteres annonces viennent du serveur (main.py)');
verifier('six criteres', CRITERES.length === 6, CRITERES.length);
verifier('les cles attendues, dans l ordre',
  CLES_SERVEUR.join(',') === 'age,timbre,debit,accent,registre,role',
  CLES_SERVEUR.join(','));
verifier('chaque critere a des valeurs',
  CRITERES.every(c => c.valeurs.length > 0),
  CRITERES.map(c => c.cle + ':' + c.valeurs.length).join(' '));
verifier('chaque valeur a une cle et un libelle',
  CRITERES.every(c => c.valeurs.every(v => v.valeur && v.libelle)));

console.log('');
console.log('2) la ligne de voix porte un menu par critere');
const VOIX = { id: 'xtts:demo', name: 'Celestin', gender: 'M',
               region: 'France (XTTS)', stars: 2 };
const a = lignePour(VOIX, {});
const menusA = a.li.querySelectorAll('.voice-critere');
verifier('un menu par critere du serveur', menusA.length === CRITERES.length,
  menusA.length);
verifier('les menus portent les cles du serveur',
  menusA.map(m => m.dataset.critere).join(',') === CLES_SERVEUR.join(','),
  menusA.map(m => m.dataset.critere).join(','));
verifier('chaque menu propose « non renseigne » + les valeurs du serveur',
  menusA.every((m, i) => m.children.length === 1 + CRITERES[i].valeurs.length),
  menusA.map(m => m.children.length).join(','));
verifier('le premier choix annonce le critere (etat vide)',
  menusA.every((m, i) => m.children[0].value === ''
    && m.children[0].textContent === CRITERES[i].libelle));
verifier('les valeurs sont celles du serveur, dans l ordre',
  menusA.every((m, i) => m.children.slice(1).map(o => o.value).join(',')
    === CRITERES[i].valeurs.map(v => v.valeur).join(',')));
verifier('aucun critere pre-selectionne quand la voix n est pas annotee',
  menusA.every(m => m.value === ''), menusA.map(m => m.value).join(','));
verifier('un menu vide ne porte pas la classe « renseigne »',
  menusA.every(m => !m.classList.contains('renseigne')));

console.log('');
console.log('3) une annotation existante est reaffichee');
const b = lignePour(VOIX, { age: 'vieux', timbre: 'grave', stars: 3, genre: 'H' });
const menusB = b.li.querySelectorAll('.voice-critere');
const valeursB = {};
menusB.forEach(m => { valeursB[m.dataset.critere] = m.value; });
verifier('les criteres annotes sont pre-selectionnes',
  valeursB.age === 'vieux' && valeursB.timbre === 'grave',
  JSON.stringify(valeursB));
verifier('les criteres non renseignes restent vides',
  valeursB.debit === '' && valeursB.accent === '', JSON.stringify(valeursB));
verifier('seuls les criteres renseignes portent la classe « renseigne »',
  menusB.filter(m => m.classList.contains('renseigne')).length === 2,
  menusB.map(m => m.dataset.critere
    + (m.classList.contains('renseigne') ? '=X' : '=')).join(' '));

console.log('');
console.log('4) une valeur qui n existe plus retombe sur « non renseigne »');
const c = lignePour(VOIX, { timbre: 'rugueux' });
const menuTimbre = c.li.querySelectorAll('.voice-critere')
  .find(m => m.dataset.critere === 'timbre');
verifier('valeur inconnue -> menu vide', menuTimbre.value === '', menuTimbre.value);

console.log('');
console.log('5) ce qui part vers le serveur');
envois = [];
const d = lignePour(VOIX, {});
const menuAccent = d.li.querySelectorAll('.voice-critere')
  .find(m => m.dataset.critere === 'accent');
menuAccent.value = 'paysan';
(menuAccent.listeners.change || []).forEach(cb => cb());

setTimeout(() => {
  const corps = (envois[0] || {}).corps || {};
  verifier('un appel est parti vers /api/annotations_voix',
    (envois[0] || {}).url === '/api/annotations_voix', (envois[0] || {}).url);
  verifier('toutes les cles du serveur sont envoyees',
    CLES_SERVEUR.every(cle => cle in corps), Object.keys(corps).join(','));
  verifier('le genre, les etoiles et la remarque sont transmis',
    'genre' in corps && 'stars' in corps && 'note' in corps,
    Object.keys(corps).join(','));
  verifier('la valeur choisie est bien transmise', corps.accent === 'paysan',
    corps.accent);
  verifier('le menu passe en « renseigne » apres le choix',
    menuAccent.classList.contains('renseigne'));

  console.log('');
  console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
  process.exit(echecs === 0 ? 0 : 1);
}, 30);
