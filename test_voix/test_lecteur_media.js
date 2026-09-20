// Verifie le LECTEUR INTEGRE et la MEDIA SESSION (20/09/2026).
// ----------------------------------------------------------------------
// Demandes de Laurent, le meme jour : « la lecture s'arrete si je verrouille le
// telephone » et « je vois bien un genre de lecteur... une petite modale qui
// ressemblerait a la lecture de Deezer ».
//
// Tout est extrait du FICHIER REEL (jamais recopie : renomme ou deplace, le test
// echoue bruyamment). Ce qu'il protege :
//   1. la BARRE DE PROGRESSION du lecteur systeme : `setPositionState` ne doit
//      JAMAIS recevoir une position hors bornes -- il leve une TypeError, et une
//      barre ne doit pas pouvoir casser la lecture ;
//   2. la RESERVE « A BLOC » : quand la page passe en arriere-plan PENDANT une
//      lecture, le plafond du prechargement est leve et le remplissage relance ;
//      hors lecture, rien ne se declenche ;
//   3. les BRANCHEMENTS du lecteur integre : ses sept boutons sont des
//      telecommandes de la barre du bas (bons ids deux a deux), et c'est la
//      barre de progression qui l'ouvre.
//
// Usage : node test_voix/test_lecteur_media.js
'use strict';

const fs = require('fs');
const path = require('path');

const RACINE = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(RACINE, 'frontend', 'app.js'), 'utf8');
const page   = fs.readFileSync(path.join(RACINE, 'frontend', 'index.html'), 'utf8');

let echecs = 0;
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail !== undefined ? '  -> ' + detail : ''));
    echecs++;
  }
}

// ------------------------------------------------------------------
// 1) La position envoyee au lecteur systeme (barre de progression)
// ------------------------------------------------------------------
console.log('');
console.log('1) la barre de progression du lecteur systeme');

const debutPos = source.indexOf('function _majPositionMediaSession');
const finPos   = source.indexOf('function _startTTS');
if (debutPos < 0 || finPos <= debutPos) {
  console.error('ECHEC : _majPositionMediaSession introuvable dans app.js');
  process.exit(1);
}
const CODE_POS = source.slice(debutPos, finPos);

// Un faux lecteur systeme qui REFUSE (comme le vrai) une position hors bornes :
// c'est exactement ce que fait `setPositionState` dans un navigateur.
function bancPosition(mediaSession) {
  const appels = [];
  const faux = mediaSession || {
    setPositionState(etat) {
      appels.push(etat);
      if (!(etat.duration > 0)) throw new TypeError('duration must be positive');
      if (etat.position < 0 || etat.position > etat.duration) {
        throw new TypeError('position must be between 0 and duration');
      }
    }
  };
  const maj = new Function('navigator', CODE_POS + '\nreturn _majPositionMediaSession;')(
    { mediaSession: faux });
  return { maj, appels, faux };
}

let b = bancPosition();
b.maj(5, 10);
verifier('position et duree transmises', b.appels.length === 1
  && b.appels[0].duration === 10 && b.appels[0].position === 5
  && b.appels[0].playbackRate === 1, JSON.stringify(b.appels));
b = bancPosition();
b.maj(50, 10);
verifier('position AU-DELA de la duree : bornee, jamais refusee',
  b.appels.length === 1 && b.appels[0].position === 10, JSON.stringify(b.appels));
b = bancPosition();
b.maj(-3, 10);
verifier('position negative : ramenee a 0',
  b.appels.length === 1 && b.appels[0].position === 0, JSON.stringify(b.appels));
b = bancPosition();
b.maj(0, 0);
verifier('chapitre sans phrase : duree 1 (jamais 0) et position 0',
  b.appels.length === 1 && b.appels[0].duration === 1 && b.appels[0].position === 0,
  JSON.stringify(b.appels));
// Le point qui compte : meme si le lecteur systeme refuse tout, la lecture ne
// doit jamais casser (l'appel est protege).
b = bancPosition({ setPositionState() { throw new TypeError('refus'); } });
let casse = false;
try { b.maj(3, 10); } catch (e) { casse = true; }
verifier('un refus du lecteur systeme ne remonte JAMAIS dans la lecture', !casse);
b = bancPosition({});
let casse2 = false;
try { b.maj(3, 10); } catch (e) { casse2 = true; }
verifier('navigateur sans setPositionState : aucun plantage', !casse2);
let casse3 = false;
try {
  const maj = new Function('navigator', CODE_POS + '\nreturn _majPositionMediaSession;')({});
  maj(1, 2);
} catch (e) { casse3 = true; }
verifier('navigateur sans mediaSession du tout : aucun plantage', !casse3);

// ------------------------------------------------------------------
// 2) La reserve « a bloc » (ecran eteint / verrouille)
// ------------------------------------------------------------------
console.log('');
console.log('2) la reserve « a bloc » quand la page passe en arriere-plan');

const debutBurst = source.indexOf('let _prechargementBurst = false;');
const finBurst   = source.indexOf('async function _runTTS');
if (debutBurst < 0 || finBurst <= debutBurst) {
  console.error('ECHEC : la reserve « a bloc » est introuvable dans app.js');
  process.exit(1);
}
const CODE_BURST = source.slice(debutBurst, finBurst);

// Faux document : on veut seulement savoir QUI est appele quand la page passe en
// arriere-plan -- c'est le signal qu'Android envoie au verrouillage.
function bancBurst() {
  let ecouteur = null;
  const fauxDoc = {
    hidden: false,
    addEventListener(nom, fn) { if (nom === 'visibilitychange') ecouteur = fn; },
  };
  const api = new Function(
    'document',
    'var _ttsState = "playing";\n' + CODE_BURST
    + '\nreturn { estBurst: () => _prechargementBurst,'
    + ' setEtat: (v) => { _ttsState = v; },'
    + ' setPump: (f) => { _pumpCourant = f; } };')(fauxDoc);
  return {
    api, fauxDoc,
    declencher(hidden) { fauxDoc.hidden = hidden; if (ecouteur) ecouteur(); },
  };
}

let pompes = 0;
let bb = bancBurst();
bb.api.setPump(() => { pompes++; });
bb.declencher(true);
verifier('en arriere-plan pendant une lecture : la reserve « a bloc » s active',
         bb.api.estBurst() === true);
verifier('et le remplissage est relance tout de suite', pompes === 1, pompes);
bb = bancBurst();
bb.api.setEtat('idle');
bb.declencher(true);
verifier('hors lecture : rien ne se declenche (rien a precharger)',
         bb.api.estBurst() === false && pompes === 1);
bb = bancBurst();
bb.api.setPump(() => { pompes++; });
bb.declencher(false);
verifier('le retour au premier plan ne declenche rien',
         bb.api.estBurst() === false && pompes === 1);
verifier('le plafond leve est bien celui utilise par les calculs',
         source.includes('function limiteFenetre()')
         && source.includes('PREFETCH_MAX_AHEAD_CHARS_BURST')
         && source.includes('if (w > limiteFenetre()) break;')
         && source.includes('> limiteFenetre()) break;'));

// ------------------------------------------------------------------
// 3) Le lecteur integre : ses telecommandes et sa porte d'entree
// ------------------------------------------------------------------
console.log('');
console.log('3) le lecteur integre « facon Deezer »');

const PAIRES = [['lecteur-prev-chap', 'prev-btn'],
                ['lecteur-prev-para', 'para-prev-btn'],
                ['lecteur-prev-sent', 'sent-prev-btn'],
                ['lecteur-play-btn',  'tts-play-btn'],
                ['lecteur-next-sent', 'sent-next-btn'],
                ['lecteur-next-para', 'para-next-btn'],
                ['lecteur-next-chap', 'next-btn']];
const sourceCompact = source.replace(/\s+/g, ' ');
PAIRES.forEach(([lecteur, barre]) => {
  verifier('« ' + lecteur + ' » telecommande « ' + barre + ' »',
           sourceCompact.includes("['" + lecteur + "', '" + barre + "']"));
});
verifier('la barre de progression ouvre le lecteur',
         source.includes("document.getElementById('tts-progress-row')"
                         + ".addEventListener('click', _ouvrirLecteur)"));
verifier('la barre de progression s annonce (petit signe + titre)',
         page.includes('id="tts-progress-ouvrir"')
         && page.includes('Ouvrir le lecteur'));
verifier('Echap ferme le lecteur',
         source.includes("e.key === 'Escape' && _lecteurOuvert()"));
// Les elements de la fenetre doivent exister dans la page : un identifiant
// manquant ferait planter TOUT le script au chargement.
['lecteur-modal', 'lecteur-inner', 'lecteur-close-btn', 'lecteur-couverture',
 'lecteur-titre', 'lecteur-auteur', 'lecteur-chapitre', 'lecteur-qui',
 'lecteur-phrase', 'lecteur-barre', 'lecteur-barre-fill', 'lecteur-compteur',
 'lecteur-boutons', 'lecteur-icon-play', 'lecteur-icon-pause'].forEach((id) => {
  verifier('element #' + id + ' dans la page', page.includes('id="' + id + '"'));
});
// La MEDIA SESSION : la couverture et la progression, ce qui fait qu'Android
// traite la page comme un vrai lecteur (et l'aide a tenir ecran verrouille).
verifier('la couverture du livre habille le lecteur systeme',
         source.includes('artwork: couverture'));
verifier('la position est mise a jour a chaque phrase',
         source.includes('_majPositionMediaSession(idx, total);'));
verifier('le lecteur integre suit la meme progression',
         source.includes('_majLecteurIntegre(idx, total);'));
verifier('le bouton de lecture du lecteur suit l etat reel',
         source.includes('_majLecteurEtat(state);'));
verifier('les boutons du lecteur systeme suivent les trois pas de la barre',
         source.includes("lier('seekbackward',  () => _cursorParaPrev(_PAS_PARAGRAPHES));")
         && source.includes("lier('seekforward',   () => _cursorParaNext(_PAS_PARAGRAPHES));")
         && source.includes("lier('nexttrack',     () => _cursorSentNext());")
         && source.includes("lier('previoustrack', () => _cursorSentPrev());"));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
