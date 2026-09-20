// Verifie les TROIS NIVEAUX de saut de la barre de navigation (20/09/2026).
// ----------------------------------------------------------------------
// Demande de Laurent : « ⏪⏩ = saut moyen (paragraphes), ◀️▶️ = saut de phrase,
// ⏮️⏭️ = chapitre », avec le bon motif : « le saut de paragraphe correspond très
// souvent à un saut de phrase » -- donc un saut d'UN paragraphe ne se distinguait
// pas d'un saut de phrase.
//
// Les fonctions de curseur sont extraites DU FICHIER REEL (jamais recopiées :
// renommées ou déplacées, le test échoue bruyamment) et exécutées sur une grille
// de paragraphes connue :
//   - `_cursorSentPrev` / `_cursorSentNext` : ± 1 PHRASE ;
//   - `_cursorParaPrev(pas)` / `_cursorParaNext(pas)` : ± `pas` PARAGRAPHES --
//     le pas de la barre est `_PAS_PARAGRAPHES`, LU dans le fichier ;
//   - et surtout les BORDS : on ne dépasse jamais la fin du chapitre, et on ne
//     recule jamais avant le début. C'est là que ce genre de code se casse.
//
// Usage : node test_voix/test_sauts_navigation.js
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

// Le pas du saut moyen, LU dans le fichier reel : une seule valeur fait foi.
const mPas = source.match(/const _PAS_PARAGRAPHES\s*=\s*(\d+)/);
if (!mPas) {
  console.error('ECHEC : _PAS_PARAGRAPHES introuvable dans app.js');
  process.exit(1);
}
const PAS = parseInt(mPas[1], 10);

// Tranche du fichier reel : du pas aux fonctions de curseur (les deux niveaux de
// navigation vivent ensemble, juste avant `_abortAndRestart`).
const debut = source.indexOf('const _PAS_PARAGRAPHES');
const fin   = source.indexOf('// Coupe le TTS en cours et repart depuis le curseur');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : les fonctions de navigation sont introuvables dans app.js');
  process.exit(1);
}
const CODE = source.slice(debut, fin);

// Un banc d'essai : la grille des paragraphes, la position du curseur, et ce que
// le code DEMANDE (la cible passee a `_setCursor`). Le vrai `_setCursor` refuse
// toute position hors du chapitre -- ce garde-fou est a lui, et il est verifie a
// part (test_ids_ecran.py).
const PARAGRAPHES = [0, 10, 20, 30, 40, 50];
function banc(curseur, paragraphes) {
  const cibles = [];
  const api = new Function(
    '_paragraphStarts', '_cursorIdx', '_setCursor', '_ttsState', '_abortAndRestart',
    CODE
    + '\nreturn { _cursorSentPrev: _cursorSentPrev, _cursorSentNext: _cursorSentNext,'
    + ' _cursorParaPrev: _cursorParaPrev, _cursorParaNext: _cursorParaNext };')(
      paragraphes || PARAGRAPHES, curseur,
      (v) => cibles.push(v), 'idle', () => {});
  return { api, cibles, cible: () => cibles[cibles.length - 1] };
}

console.log('');
console.log('1) le pas du saut moyen, tel qu il est ecrit dans app.js');
verifier('_PAS_PARAGRAPHES vaut au moins 2 (sinon ce n est pas un saut « moyen »)',
         PAS >= 2, PAS);
verifier('les boutons ⏪ / ⏩ utilisent bien ce pas',
         source.includes('_cursorParaPrev(_PAS_PARAGRAPHES)')
         && source.includes('_cursorParaNext(_PAS_PARAGRAPHES)'));
verifier('les boutons ◀ / ▶ sont sur la phrase',
         source.includes("'sent-prev-btn').addEventListener('click', _cursorSentPrev)")
         && source.includes("'sent-next-btn').addEventListener('click', _cursorSentNext)"));

console.log('');
console.log('2) le saut MOYEN avance de ' + PAS + ' paragraphes');
let b = banc(12);                       // 12 = dans le paragraphe qui commence a 10
b.api._cursorParaNext(PAS);
// Depuis 12, le paragraphe SUIVANT est 20 : avec un pas de 4, on saute donc
// 20, 30, 40 et 50 -- on atterrit sur le dernier (la grille de test s'arrete la).
egal('depuis 12 : on saute ' + PAS + ' paragraphes (20, 30, 40, 50)',
     b.cible(), PARAGRAPHES[PARAGRAPHES.indexOf(20) + PAS - 1]);
b = banc(12);
b.api._cursorParaNext(1);
egal('avec un pas de 1, on retrouve l ancien comportement (1 paragraphe)',
     b.cible(), 20);
b = banc(12);
b.api._cursorParaPrev(PAS);
egal('en arriere : ' + PAS + ' paragraphes, borne au debut du chapitre',
     b.cible(), 0);
b = banc(12);
b.api._cursorParaPrev(1);
egal('avec un pas de 1, on revient au DEBUT du paragraphe courant', b.cible(), 10);
b = banc(10);                           // pile sur un debut de paragraphe
b.api._cursorParaPrev(1);
egal('pile sur un debut : on recule d un paragraphe (regle d origine)', b.cible(), 0);

console.log('');
console.log('3) les bords : on ne sort jamais du chapitre');
b = banc(50);                           // dernier paragraphe, pile sur son debut
b.api._cursorParaNext(PAS);
verifier('au dernier paragraphe : plus rien ne bouge',
         b.cibles.length === 0, JSON.stringify(b.cibles));
b = banc(55);                           // dans le dernier paragraphe
b.api._cursorParaNext(PAS);
verifier('dans le dernier paragraphe : plus rien ne bouge non plus',
         b.cibles.length === 0, JSON.stringify(b.cibles));
b = banc(0);
b.api._cursorParaPrev(PAS);
egal('au tout debut : on reste a 0 (jamais de position negative)', b.cible(), 0);
b = banc(45);                           // 45 = dans le dernier paragraphe
b.api._cursorParaNext(PAS);
egal('un saut qui depasse la fin est ramene au DERNIER paragraphe',
     b.cible(), 50);

console.log('');
console.log('4) le pas FIN : une phrase');
b = banc(12);
b.api._cursorSentNext();
egal('◀ / ▶ avancent d UNE phrase', b.cible(), 13);
b = banc(12);
b.api._cursorSentPrev();
egal('et reculent d UNE phrase', b.cible(), 11);
verifier('le pas fin ne depend pas de _PAS_PARAGRAPHES',
         !source.includes('_cursorSentNext(_PAS')
         && !source.includes('_cursorSentPrev(_PAS'));

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
