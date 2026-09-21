// Verifie le FILTRE PAR AGE et PAR GENRE des lignes du casting (21/09/2026).
// ----------------------------------------------------------------------
// Demande de Laurent : « Des boutons juste pour trier les voix par age [...]
// Cliquer sur "jeune" n'affiche que les jeunes. Les boutons qui sont actifs
// affichent la categorie. Idealement un filtre ; Homme / Femme et les 4 ages. »
//
// Le filtrage vit dans frontend/app.js (_ageDeLaVoix, _lignePasseFiltres). Ce
// test extrait ces fonctions DU FICHIER REEL (jamais une copie : renommees ou
// deplacees, il echoue bruyamment) et verifie :
//   - l'age vient de la VOIX portee (ses annotations d'ecoute), pas du
//     personnage : une voix annotee « jeune » passe le filtre « jeune » ;
//   - une voix JAMAIS annotee ne passe AUCUN filtre d'age -- on ne devine pas ;
//   - une voix annotee mais SANS age ne passe pas non plus ;
//   - le genre vient de la FICHE du personnage : 'F' passe « Femmes », 'H' et
//     'M' passent « Hommes » (les catalogues ecrivent M, les fiches H), et un
//     genre vide ne passe ni l'un ni l'autre ;
//   - « T » laisse tout passer ;
//   - les deux filtres se COMBINENT ;
//   - la barre est bien branchee dans la page : les 4 ages (sans « mur », retire
//     le meme jour), les 2 genres, la mise en evidence du bouton actif, et la
//     remise a zero a la fermeture de la fenetre.
//
// Usage : node test_voix/test_filtre_age_casting.js
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

// Les annotations d'ecoute, telles que /api/annotations_voix les renvoie : c'est
// ce que le filtre lit. On les installe en GLOBAL, comme dans la page ou
// _annotationsVoix vit dans le fichier.
global._annotationsVoix = {
  'kokoro:ff_enfant': { age: 'enfant', timbre: 'aigu' },
  'kyutai:jeune1':    { age: 'jeune',  timbre: 'medium' },
  'kyutai:adulte1':   { age: 'adulte', timbre: 'grave' },
  'edge:vieux1':      { age: 'vieux',  timbre: 'grave' },
  'piper:sansAge':    { timbre: 'medium' },          // annotee, mais sans age
};

// Tranche du fichier reel : de _ageDeLaVoix a _filtrerVoixLibres (la fonction
// suivante). Les deux fonctions du filtre y sont, ensemble.
const debut = source.indexOf('function _ageDeLaVoix');
const fin   = source.indexOf('function _filtrerVoixLibres');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : les fonctions du filtre age/genre sont introuvables '
                + 'dans app.js');
  process.exit(1);
}
const extrait = new Function(
  source.slice(debut, fin)
  + '\nreturn { _ageDeLaVoix: _ageDeLaVoix,'
  + ' _lignePasseFiltres: _lignePasseFiltres };')();
const ageDeLaVoix = extrait._ageDeLaVoix;
const passe = extrait._lignePasseFiltres;

// Une ligne du casting, telle que _lignesPersonnages la construit : `v` est la
// fiche du personnage (voix portee + genre).
const ligne = (voix, genre) => ({ nom: 'Quelqu un', v: { voice_id: voix, genre: genre }, total: 5 });

console.log('');
console.log('='.repeat(66));
console.log('VERIFICATION : filtre par age de la voix et genre du personnage');
console.log('='.repeat(66));

console.log('');
console.log('1) l age lu sur la VOIX portee');
verifier('voix annote « jeune » -> age « jeune »',
         ageDeLaVoix('kyutai:jeune1') === 'jeune', ageDeLaVoix('kyutai:jeune1'));
verifier('voix annote mais SANS age -> aucun age',
         ageDeLaVoix('piper:sansAge') === '', ageDeLaVoix('piper:sansAge'));
verifier('voix inconnue -> aucun age, aucun plantage',
         ageDeLaVoix('voix:inconnue') === '' && ageDeLaVoix('') === '');

console.log('');
console.log('2) le filtre par age');
verifier('« T » laisse passer tout le monde',
         passe(ligne('kokoro:ff_enfant', 'F'), 'T', 'T') === true
         && passe(ligne('kyutai:jeune1', 'H'), 'T', 'T') === true);
verifier('« jeune » ne garde que les jeunes',
         passe(ligne('kyutai:jeune1', 'H'), 'jeune', 'T') === true
         && passe(ligne('kyutai:adulte1', 'H'), 'jeune', 'T') === false);
verifier('« enfant » ne garde que les enfants',
         passe(ligne('kokoro:ff_enfant', 'F'), 'enfant', 'T') === true
         && passe(ligne('kyutai:jeune1', 'F'), 'enfant', 'T') === false);
verifier('une voix jamais annotee ne passe AUCUN filtre d age',
         passe(ligne('voix:inconnue', 'F'), 'jeune', 'T') === false
         && passe(ligne('piper:sansAge', 'F'), 'jeune', 'T') === false);
verifier('« vieux » ne garde que les vieux',
         passe(ligne('edge:vieux1', 'H'), 'vieux', 'T') === true
         && passe(ligne('kokoro:ff_enfant', 'H'), 'vieux', 'T') === false);

console.log('');
console.log('3) le filtre par genre du PERSONNAGE');
verifier('« F » ne garde que les femmes',
         passe(ligne('kyutai:jeune1', 'F'), 'T', 'F') === true
         && passe(ligne('kyutai:jeune1', 'H'), 'T', 'F') === false);
verifier('« H » garde les hommes, ecrits H comme M',
         passe(ligne('kyutai:jeune1', 'H'), 'T', 'H') === true
         && passe(ligne('kyutai:adulte1', 'M'), 'T', 'H') === true,
         'H et M doivent tous deux passer');
verifier('un genre vide ne passe NI femmes NI hommes',
         passe(ligne('kyutai:jeune1', ''), 'T', 'F') === false
         && passe(ligne('kyutai:jeune1', ''), 'T', 'H') === false);

console.log('');
console.log('4) les deux filtres se COMBINENT');
verifier('« jeune » + « Femmes » : les deux conditions comptent',
         passe(ligne('kyutai:jeune1', 'F'), 'jeune', 'F') === true
         && passe(ligne('kyutai:jeune1', 'H'), 'jeune', 'F') === false
         && passe(ligne('kyutai:adulte1', 'F'), 'jeune', 'F') === false);

console.log('');
console.log('5) cas tordus : aucun plantage');
verifier('ligne sans fiche', passe({ nom: 'X' }, 'jeune', 'F') === false);
verifier('ligne nulle', passe(null, 'jeune', 'F') === false);
verifier('filtres absents (undefined) : tout passe',
         passe(ligne('kokoro:ff_enfant', 'F'), undefined, undefined) === true);

console.log('');
console.log('6) la barre est branchee dans la page');
verifier('la barre existe', /id="cast-filtre-bar"/.test(page));
['T', 'enfant', 'jeune', 'adulte', 'vieux'].forEach(age => {
  verifier('le bouton « ' + age + ' » est propose',
           page.indexOf('data-age="' + age + '"') >= 0);
});
['T', 'F', 'H'].forEach(genre => {
  verifier('le bouton de genre « ' + genre + ' » est propose',
           page.indexOf('data-perso="' + genre + '"') >= 0);
});
verifier('« mur » a bien disparu de la barre',
         page.indexOf('data-age="mur"') < 0);
verifier('le compteur du filtre est dans la page',
         /id="cast-filtre-resume"/.test(page));

console.log('');
console.log('7) le branchement dans app.js');
verifier('un clic sur un age reconstruit la fenetre',
         source.indexOf("querySelectorAll('#cast-age-actions button')") >= 0
         && source.indexOf('_castAgeFiltre = btn.dataset.age') >= 0);
verifier('un clic sur un genre aussi',
         source.indexOf("querySelectorAll('#cast-perso-genre-actions button')") >= 0
         && source.indexOf('_castPersoGenre = btn.dataset.perso') >= 0);
verifier('le bouton ACTIF est mis en evidence',
         source.indexOf("b.dataset.age === _castAgeFiltre") >= 0
         && source.indexOf("b.dataset.perso === _castPersoGenre") >= 0);
verifier('le filtre s applique aux lignes du casting',
         source.indexOf('_lignePasseFiltres(r, _castAgeFiltre, _castPersoGenre)') >= 0);
verifier('les filtres sont remis a zero a la fermeture',
         source.indexOf("_castAgeFiltre  = 'T';") >= 0
         && source.indexOf("_castPersoGenre = 'T';") >= 0);
verifier('les etats initiaux sont bien « T »',
         source.indexOf("let _castAgeFiltre  = 'T';") >= 0
         && source.indexOf("let _castPersoGenre = 'T';") >= 0);

console.log('');
console.log('='.repeat(66));
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
console.log('='.repeat(66));
process.exit(echecs === 0 ? 0 : 1);
