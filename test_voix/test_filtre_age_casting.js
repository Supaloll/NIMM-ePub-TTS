// Verifie les FILTRES DES VOIX : le GENRE et l'AGE, dans la modale des voix.
// --------------------------------------------------------------------------
// Histoire de ce fichier, parce qu'il a change de metier : il verifiait jusqu'au
// 24/09/2026 le filtre par age des LIGNES DE PERSONNAGES (les cinq boutons de la
// fenetre du casting, 21/09/2026). Laurent les a retires, et il a explique
// pourquoi : « Elle ne sert à rien ici. Elle devrait servir à sélectionner les
// personnages, pas les voix. [...] Donc juste Homme / Femme. On retire Tous les
// âges Enfant Jeune Adulte Vieux. » Puis sa demande du meme jour : « Je veux bien
// soit un champ de recherche dans la modale qui s'ouvre : Homme / Femme, Enfant,
// jeune, adulte, vieux. Sous forme de boutons [...] Les boutons [...] doivent
// trier les voix selon leur tag. »
//
// Le filtrage vit donc maintenant dans frontend/app.js, sur des VOIX :
//   - `_ageDeLaVoix` lit l'age annote de la voix (ses notes d'ecoute) ;
//   - `_lignesVoixPersonnage` (fonction PURE) ne garde que les voix qui passent
//     les deux filtres ;
//   - `_lignePasseFiltres` ne porte plus QUE le genre du personnage.
// Ce test extrait ces fonctions DU FICHIER REEL (jamais une copie : renommees ou
// deplacees, il echoue bruyamment) et verifie :
//   - l'age vient de la VOIX, pas du personnage ; une voix jamais annotee ne
//     passe AUCUN filtre d'age (on ne devine pas) ;
//   - le genre des voix vient de leur catalogue (F / M) ;
//   - les deux filtres se COMBINENT ;
//   - la voix PORTEE par le personnage reste toujours visible, meme masquee ;
//   - les boutons sont bien dans la MODALE (et plus dans la fenetre du casting),
//     leur clic REFAIT la liste sans fermer la fenetre, et les filtres sont remis
//     a zero a la fermeture.
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

// Les notes d'ecoute, telles que /api/annotations_voix les renvoie : c'est ce que
// le filtre d'age lit. On les installe en GLOBAL, comme dans la page ou
// `_annotationsVoix` vit dans le fichier.
global._annotationsVoix = {
  'kokoro:ff_enfant': { age: 'enfant', timbre: 'aigu' },
  'kyutai:jeune1':    { age: 'jeune',  timbre: 'medium' },
  'kyutai:adulte1':   { age: 'adulte', timbre: 'grave' },
  'edge:vieux1':      { age: 'vieux',  timbre: 'grave' },
  'piper:sansAge':    { timbre: 'medium' },          // annotee, mais sans age
};

// Tranche du fichier reel : de `_ageDeLaVoix` a `_openCastModal` (la fonction
// suivante). Elle porte `_ageDeLaVoix`, `_lignePasseFiltres`, la fonction PURE
// `_lignesVoixPersonnage` et les fonctions de la modale. Un renommage ou un
// deplacement fait echouer ce test bruyamment (c'est voulu).
const debut = source.indexOf('function _ageDeLaVoix');
// Fin de la tranche : la fonction SUIVANTE, qui est `async` (elle rafraichit
// l'etat des moteurs avant d'afficher) -- on recule donc d'un eventuel `async `
// pour ne pas couper au milieu du mot-cle.
let fin = source.indexOf('function _openCastModal');
if (fin > 0 && source.slice(fin - 6, fin) === 'async ') fin -= 6;
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : les fonctions du filtre des voix sont introuvables '
                + 'dans app.js');
  process.exit(1);
}
const code = source.slice(debut, fin);

// Le catalogue des voix, tel que /api/voices le renvoie : identifiant, prenom,
// genre. Les identifiants sont ceux des notes ci-dessus.
const VOIX = [
  { id: 'kokoro:ff_enfant', name: 'Bébé',   gender: 'F', region: 'France' },
  { id: 'kyutai:jeune1',    name: 'Jeanne', gender: 'F', region: 'France' },
  { id: 'kyutai:adulte1',   name: 'Adèle',  gender: 'F', region: 'France' },
  { id: 'edge:vieux1',      name: 'Victor', gender: 'M', region: 'France' },
  { id: 'piper:sansAge',    name: 'Pierre', gender: 'M', region: 'France' },
];

// Le fichier reel, execute avec un filtre donne. Les deux filtres sont installes
// COMME dans la page (deux variables du module, lues par la fonction pure) : ce
// qu'on eprouve est donc bien la regle du code, jamais une copie.
function extraire(age, genre, catalogue) {
  const fabrique = new Function('_allVoices', '_libelleCatalogue',
    'var _castGenreFiltre = ' + JSON.stringify(genre) + ';\n'
    + 'var _castAgeVoixFiltre = ' + JSON.stringify(age) + ';\n'
    + code
    + '\nreturn { _ageDeLaVoix: _ageDeLaVoix,'
    + ' _lignePasseFiltres: _lignePasseFiltres,'
    + ' _lignesVoixPersonnage: _lignesVoixPersonnage };');
  return fabrique(catalogue || VOIX, () => '');
}

const apiTout      = extraire('T', 'T');
const ageDeLaVoix  = apiTout._ageDeLaVoix;
const passe        = apiTout._lignePasseFiltres;

// Ce que la modale montrerait avec un filtre donne (le 3e argument est la voix
// que porte le personnage, si l'on veut verifier qu'elle reste visible).
function lignesPour(age, genre, voixActuelle, catalogue) {
  return extraire(age, genre, catalogue)
    ._lignesVoixPersonnage(voixActuelle || '', null);
}
const idsDesVoix = (lignes) => lignes
  // La ligne « (lu par le narrateur) » n'a pas d'identifiant : ce n'est pas une
  // voix du catalogue, elle est donc comptee a part (section 4).
  .filter(l => l.genre === 'voix' && l.id)
  .map(l => l.id);
const groupesDe  = (lignes) => lignes.filter(l => l.genre === 'groupe').map(l => l.libelle);

console.log('');
console.log('='.repeat(66));
console.log('VERIFICATION : filtre par age de la voix et genre du personnage');
console.log('='.repeat(66));

console.log('');
console.log('1) l age lu sur la VOIX (ses notes d ecoute)');
verifier('voix annotee « jeune » -> age « jeune »',
         ageDeLaVoix('kyutai:jeune1') === 'jeune', ageDeLaVoix('kyutai:jeune1'));
verifier('voix annotee mais SANS age -> aucun age',
         ageDeLaVoix('piper:sansAge') === '', ageDeLaVoix('piper:sansAge'));
verifier('voix inconnue -> aucun age, aucun plantage',
         ageDeLaVoix('voix:inconnue') === '' && ageDeLaVoix('') === '');

console.log('');
console.log('2) le filtre par age, applique aux VOIX (et non aux personnages)');
verifier('« Tous » laisse passer les cinq voix',
         idsDesVoix(lignesPour('T', 'T')).length === 5,
         idsDesVoix(lignesPour('T', 'T')).join(', '));
verifier('« jeune » ne garde QUE les jeunes',
         JSON.stringify(idsDesVoix(lignesPour('jeune', 'T')))
         === JSON.stringify(['kyutai:jeune1']),
         idsDesVoix(lignesPour('jeune', 'T')).join(', '));
verifier('« enfant » ne garde QUE les enfants',
         JSON.stringify(idsDesVoix(lignesPour('enfant', 'T')))
         === JSON.stringify(['kokoro:ff_enfant']),
         idsDesVoix(lignesPour('enfant', 'T')).join(', '));
verifier('« adulte » ne garde QUE les adultes',
         JSON.stringify(idsDesVoix(lignesPour('adulte', 'T')))
         === JSON.stringify(['kyutai:adulte1']),
         idsDesVoix(lignesPour('adulte', 'T')).join(', '));
verifier('« vieux » ne garde QUE les vieux',
         JSON.stringify(idsDesVoix(lignesPour('vieux', 'T')))
         === JSON.stringify(['edge:vieux1']),
         idsDesVoix(lignesPour('vieux', 'T')).join(', '));
verifier('une voix jamais annotee ne passe AUCUN filtre d age',
         !idsDesVoix(lignesPour('jeune', 'T')).includes('piper:sansAge')
         && !idsDesVoix(lignesPour('enfant', 'T')).includes('piper:sansAge'));
verifier('un age sans aucune voix : la liste est vide, sans plantage',
         idsDesVoix(lignesPour('vieux', 'T',
                               '', [{ id: 'kyutai:jeune1', name: 'Jeanne',
                                      gender: 'F', region: 'France' }])).length === 0);

console.log('');
console.log('3) le filtre par GENRE des voix, et sa COMBINAISON avec l age');
verifier('« Femmes » ne garde que des voix feminines',
         JSON.stringify(idsDesVoix(lignesPour('T', 'F')))
         === JSON.stringify(['kyutai:adulte1', 'kokoro:ff_enfant',
                             'kyutai:jeune1']),
         idsDesVoix(lignesPour('T', 'F')).join(', '));
verifier('« Hommes » ne garde que des voix masculines',
         JSON.stringify(idsDesVoix(lignesPour('T', 'M')))
         === JSON.stringify(['piper:sansAge', 'edge:vieux1']),
         idsDesVoix(lignesPour('T', 'M')).join(', '));
verifier('« adulte » + « Femmes » : les DEUX conditions comptent',
         JSON.stringify(idsDesVoix(lignesPour('adulte', 'F')))
         === JSON.stringify(['kyutai:adulte1'])
         && idsDesVoix(lignesPour('jeune', 'M')).length === 0,
         idsDesVoix(lignesPour('adulte', 'F')).join(', '));

console.log('');
console.log('4) la voix PORTEE par le personnage reste TOUJOURS visible');
// Le personnage porte une voix « vieux », et l'on demande le filtre « jeune » :
// sa voix doit rester affichee, sinon on croirait qu'il n'en a plus.
const masquee = lignesPour('jeune', 'T', 'edge:vieux1');
verifier('elle est rappelee en tete, dans « Voix actuelle »',
         groupesDe(masquee)[0] === '\u26A0\uFE0F Voix actuelle',
         groupesDe(masquee).join(' | '));
verifier('et elle n apparait qu UNE fois',
         idsDesVoix(masquee).filter(id => id === 'edge:vieux1').length === 1,
         idsDesVoix(masquee).join(', '));
verifier('sans filtre, elle est simplement marquee « actuelle » (le ✔)',
         (lignesPour('T', 'T', 'edge:vieux1')
           .find(l => l.id === 'edge:vieux1') || {}).actuelle === true);
verifier('la ligne « (lu par le narrateur) » reste, elle aussi, visible',
         (lignesPour('jeune', 'T', '')
           .find(l => l.genre === 'voix' && l.id === '') || {}).actuelle === true);

console.log('');
console.log('5) le filtre des LIGNES de personnages ne porte plus QUE le genre');
verifier('la fonction ne prend plus que DEUX arguments (plus d age)',
         passe.length === 2, passe.length);
verifier('« F » ne garde que les femmes',
         passe({ v: { genre: 'F' } }, 'F') === true
         && passe({ v: { genre: 'H' } }, 'F') === false);
verifier('« H » garde les hommes, ecrits H comme M',
         passe({ v: { genre: 'H' } }, 'H') === true
         && passe({ v: { genre: 'M' } }, 'H') === true,
         'H et M doivent tous deux passer');
verifier('un genre vide ne passe NI femmes NI hommes',
         passe({ v: { genre: '' } }, 'F') === false
         && passe({ v: { genre: '' } }, 'H') === false);
verifier('« T » laisse passer tout le monde',
         passe({ v: { genre: 'F' } }, 'T') === true
         && passe({ v: { genre: 'M' } }, 'T') === true);
verifier('filtre absent (undefined) : tout passe',
         passe({ v: { genre: 'F' } }, undefined) === true);
verifier('cas tordus : ligne sans fiche, ligne nulle',
         passe({ nom: 'X' }, 'F') === false && passe(null, 'F') === false);

console.log('');
console.log('6) les boutons sont dans la MODALE, plus dans la fenetre du casting');
verifier('l ancien groupe d ages a disparu de la fenetre du casting',
         page.indexOf('id="cast-age-actions"') < 0);
verifier('les deux groupes de filtres sont dans la modale',
         page.indexOf('id="cast-voix-age-actions"') >= 0
         && page.indexOf('id="cast-voix-genre-actions"') >= 0);
['T', 'enfant', 'jeune', 'adulte', 'vieux'].forEach(age => {
  verifier('le bouton d age « ' + age + ' » est propose',
           page.indexOf('data-age="' + age + '"') >= 0);
});
verifier('les VOIX se filtrent aussi par genre (F / M)',
         page.indexOf('data-genre="F"') >= 0
         && page.indexOf('data-genre="M"') >= 0);
verifier('« mur » a bien disparu',
         page.indexOf('data-age="mur"') < 0);
verifier('le filtre des PERSONNAGES garde, lui, son genre',
         page.indexOf('data-perso="F"') >= 0
         && page.indexOf('data-perso="H"') >= 0
         && /id="cast-filtre-bar"/.test(page));
verifier('le compte des voix est annonce dans la modale',
         page.indexOf('id="cast-voix-recap"') >= 0);
verifier('aucun champ de recherche de voix (choix de Laurent, 24/09/2026)',
         page.indexOf('cast-voix-recherche') < 0);
verifier('le compteur du filtre des personnages est toujours dans la page',
         /id="cast-filtre-resume"/.test(page));

console.log('');
console.log('7) le branchement dans app.js');
verifier('un clic sur un age REFAIT la liste sans fermer la modale',
         source.indexOf("querySelectorAll('#cast-voix-age-actions button')") >= 0
         && source.indexOf('_castAgeVoixFiltre = btn.dataset.age') >= 0
         && source.indexOf('_peindreVoixPersonnage();') >= 0);
verifier('un clic sur un genre de VOIX aussi',
         source.indexOf("querySelectorAll('#cast-voix-genre-actions button')") >= 0
         && source.indexOf('_castGenreFiltre = btn.dataset.genre') >= 0);
verifier('le bouton ACTIF est mis en evidence',
         source.indexOf('b.dataset.age === _castAgeVoixFiltre') >= 0
         && source.indexOf('b.dataset.genre === _castGenreFiltre') >= 0);
verifier('le filtre d age s applique bien a la LISTE DES VOIX',
         source.indexOf('.filter(passeAge)') >= 0);
verifier('le filtre des personnages n a plus l age',
         source.indexOf('_lignePasseFiltres(r, _castPersoGenre)') >= 0);
verifier('les filtres sont remis a zero a la fermeture de la modale',
         source.indexOf("_castAgeVoixFiltre = 'T';") >= 0
         && source.indexOf("_castGenreFiltre   = 'T';") >= 0);
verifier('les etats initiaux sont bien « T »',
         source.indexOf("let _castAgeVoixFiltre = 'T';") >= 0
         && source.indexOf("let _castPersoGenre    = 'T';") >= 0);

console.log('');
console.log('='.repeat(66));
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
console.log('='.repeat(66));
process.exit(echecs === 0 ? 0 : 1);
