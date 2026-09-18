// Verifie le CHARGEMENT D'UN CHAPITRE (constat de Laurent, 18/09/2026) :
// « parfois le chapitre ne se charge pas correctement, et zappe completement un
// chapitre : il passe du quatre-vingt-un au quatre-vingt-trois, surtout apres
// une erreur de chargement ».
//
// Ce test EXECUTE le vrai code de frontend/app.js (extrait du fichier, comme
// test_message_reseau.js), avec un faux DOM et un faux serveur. Ce qu'il
// verifie, et pourquoi :
//   1. le chapitre est DEMANDE avant que l'etat du lecteur ne change : une
//      panne ne doit pas laisser le compteur sur le chapitre rate ;
//   2. une panne PASSAGERE est retentee (c'est le cas le plus frequent) ;
//   3. apres un echec, les phrases du chapitre PRECEDENT sont videes -- sinon la
//      lecture rejouait l'ancien chapitre et l'enchainement sautait le manquant ;
//   4. l'echec propose de recommencer tout de suite (bouton) ;
//   5. une pause peut se faire SANS signal d'interruption (la fonction _pause
//      plantait sinon, et le chargement d'un chapitre n'a pas de signal).
//
// Usage : node test_voix/test_chargement_chapitre.js
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

// --- Le code reel, extrait du fichier ------------------------------------
const debutChapitre = source.indexOf('const CHARGEMENT_ESSAIS');
const finChapitre   = source.indexOf('function _buildSentences');
if (debutChapitre < 0 || finChapitre <= debutChapitre) {
  console.error('ECHEC : le bloc de chargement de chapitre est introuvable dans app.js');
  process.exit(1);
}
const codeChapitre = source.slice(debutChapitre, finChapitre);

const debutPause = source.indexOf('function _pause(ms, signal)');
const finPause   = source.indexOf('const PARAGRAPH_PAUSE_MS');
if (debutPause < 0 || finPause <= debutPause) {
  console.error('ECHEC : la fonction _pause est introuvable dans app.js');
  process.exit(1);
}
const codePause = source.slice(debutPause, finPause);

function constante(nom) {
  const m = source.match(new RegExp(nom + '\\s*=\\s*(\\d+)'));
  if (!m) {
    console.error('ECHEC : constante ' + nom + ' introuvable dans app.js');
    process.exit(1);
  }
  return parseInt(m[1], 10);
}
const ESSAIS = constante('CHARGEMENT_ESSAIS');
console.log('  (constantes lues dans app.js : ' + ESSAIS + ' essais par chargement)');

// --- Le faux lecteur : DOM minimal, serveur pilote par la liste `reponses` ---
function preparerLecteur(reponses) {
  const corps = `
    var _currentChapter = 5;            // le lecteur affiche le chapitre 6
    var _totalChapters = 20;
    var _currentBookId = 1;
    var _currentUserId = 1;
    var _chapterSpeakers = {};
    var _sentences = [{ text: 'TEXTE DE L ANCIEN CHAPITRE' }];
    var _paragraphStarts = [0];
    var _cursorIdx = 3;
    var appels = 0;
    var crees = [];
    var enfants = [];
    var lecteur = { innerHTML: '', scrollTop: 0, appendChild(el) { enfants.push(el); } };
    function noeud(tag) {
      const n = { tag: tag || 'div', innerHTML: '', textContent: '', disabled: false,
                  style: {}, className: '', scrollTop: 0,
                  appendChild(el) { enfants.push(el); },
                  classList: { toggle() {} }, addEventListener() {} };
      if (tag) crees.push(n);
      return n;
    }
    var document = {
      getElementById(cle) { return cle === 'reader-content' ? lecteur : noeud(); },
      createElement(tag) { return noeud(tag); },
      querySelectorAll() { return []; }
    };
    var console = { error() {}, log() {} };
    var _stopTTS = () => {};
    var _closeVoicePanel = () => {};
    var renderChapterContent = () => {};
    var _setCursor = () => {};
    var _startTTS = () => {};
    var saveProgress = () => {};
    ${codePause}
    _pause = () => Promise.resolve();   // pas d'attente reelle dans le test
    var reponses = ${JSON.stringify(reponses)};
    var fetch = () => {
      appels += 1;
      const r = reponses.shift();
      if (r && r.coupure) return Promise.reject(new Error('reseau coupe'));
      return Promise.resolve({
        ok: !!(r && r.ok), status: (r && r.statut) || 200,
        json: () => Promise.resolve({ text: 'Texte du nouveau chapitre.',
                                      title: 'Titre', speakers: { 0: 'Paul' } })
      });
    };
    ${codeChapitre}
    return {
      charger: loadChapter,
      etat: () => ({ chapitre: _currentChapter, phrases: _sentences.length,
                     intervenants: Object.keys(_chapterSpeakers).length,
                     html: lecteur.innerHTML, enfants: enfants.length,
                     boutons: crees.filter(n => n.tag === 'button').length }),
      appels: () => appels
    };
  `;
  return new Function(corps)();
}

async function scenario(nom, reponses, attendus) {
  console.log('');
  console.log(nom);
  const lecteur = preparerLecteur(reponses);
  const resultat = await lecteur.charger(7, 0, 0, false);
  const etat = lecteur.etat();
  verifier('la fonction rend ' + attendus.retour, resultat === attendus.retour, resultat);
  verifier('nombre d appels au serveur = ' + attendus.appels,
           lecteur.appels() === attendus.appels, lecteur.appels());
  verifier('chapitre affiche = ' + attendus.chapitre,
           etat.chapitre === attendus.chapitre, etat.chapitre);
  verifier('phrases en memoire = ' + attendus.phrases,
           etat.phrases === attendus.phrases, etat.phrases);
  if (attendus.bouton !== undefined) {
    verifier('bouton « Reessayer » propose : ' + attendus.bouton,
             (etat.boutons > 0) === attendus.bouton, etat.boutons);
  }
}

(async () => {
  console.log('');
  console.log('1) le chapitre est demande AVANT de changer l etat du lecteur');
  const posDemande = codeChapitre.indexOf('data = await _demanderChapitre(index)');
  const posChange  = codeChapitre.indexOf('_currentChapter = index');
  verifier('la demande precede l affectation du chapitre courant',
           posDemande > 0 && posChange > posDemande, posDemande + ' / ' + posChange);

  await scenario('2) panne persistante : on retente, on garde le chapitre courant',
                 [{ ok: false, statut: 500 }, { coupure: true }, { ok: false, statut: 500 }],
                 { retour: false, appels: ESSAIS, chapitre: 5, phrases: 0, bouton: true });
  await scenario('3) panne passagere (un seul echec) : le chapitre se charge quand meme',
                 [{ ok: false, statut: 503 }, { ok: true }],
                 { retour: true, appels: 2, chapitre: 7, phrases: 1, bouton: false });
  await scenario('4) tout va bien : un seul appel',
                 [{ ok: true }],
                 { retour: true, appels: 1, chapitre: 7, phrases: 1, bouton: false });

  console.log('');
  console.log('5) une pause sans signal d interruption ne plante pas');
  const pauseReelle = new Function(codePause + '\nreturn _pause;')();
  let pauseOk = false;
  try {
    await Promise.race([
      pauseReelle(5),
      new Promise((_, rej) => setTimeout(() => rej(new Error('pause bloquee')), 1000))
    ]);
    pauseOk = true;
  } catch (e) {
    pauseOk = false;
  }
  verifier('_pause(ms) sans signal aboutit', pauseOk);

  console.log('');
  console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
  process.exit(echecs === 0 ? 0 : 1);
})();
