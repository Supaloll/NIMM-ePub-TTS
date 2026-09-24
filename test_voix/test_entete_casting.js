// Verifie l'EN-TETE COMPACT de la fenetre du casting, SANS navigateur.
// -------------------------------------------------------------------
// Demande de Laurent (21/09/2026, le soir) : « Sur mobile, le menu deroulant
// pour choisir les personnages et leurs voix est minuscule. Il faudrait gagner
// de la place sur le haut de la modale [...] Et pour l'option pour voir si les
// voix sont partagees, sur mobile je ne peux pas acceder aux noms qui sont
// cliquables, parce que souvent la modale sort de l'ecran vers le bas. »
//
// Livre le 22/09/2026. Ce que ce test protege, controle par controle :
//   - l'en-tete ne garde que TROIS commandes (recherche, Filtres, fermeture) :
//     les vingt et un controles d'avant sont ce qui etouffait la liste ;
//   - le tiroir #cast-tools contient bien les quatre blocs de reglages, et la
//     liste des personnages est APRES lui (donc jamais avalee par le tiroir) ;
//   - les compteurs (« 176 personnages · 3 a caster... ») restent HORS du
//     tiroir : replie, il ne doit pas cacher ce qui explique une liste courte ;
//   - les QUATRE ages de voix (enfant, jeune, adulte, vieux) et pas cinq
//     (precision de Laurent, 22/09/2026) ;
//   - les fonctions pures de l'en-tete, extraites du fichier reel : ecran
//     etroit ou large, tiroir ouvert ou replie, filtre de liste actif ;
//   - la fenetre ne peut plus SORTIR DE L'ECRAN (hauteur en `dvh`), la liste
//     garde une hauteur minimale, et les pastilles d'etat tiennent sur une ligne
//     qui defile ;
//   - les NOMS CLIQUABLES du badge de partage passent AVANT l'explication.
//
// Usage : node test_voix/test_entete_casting.js
'use strict';

const fs = require('fs');
const path = require('path');

const RACINE = path.join(__dirname, '..');
const page   = fs.readFileSync(path.join(RACINE, 'frontend', 'index.html'), 'utf8');
const styles = fs.readFileSync(path.join(RACINE, 'frontend', 'styles.css'), 'utf8');
const source = fs.readFileSync(path.join(RACINE, 'frontend', 'app.js'), 'utf8');

let echecs = 0;
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail !== undefined ? '  -> ' + detail : ''));
    echecs++;
  }
}

// Tranche DU FICHIER REEL (meme regle que les autres tests) : si une fonction
// est renommee ou deplacee, le test echoue bruyamment au lieu de verifier une
// copie.
function tranche(debut, fin) {
  const d = source.indexOf(debut);
  const f = source.indexOf(fin);
  if (d < 0 || f <= d) {
    console.error('ECHEC : tranche introuvable dans app.js (' + debut + ')');
    process.exit(1);
  }
  return source.slice(d, f);
}

const apiEntete = new Function(
  tranche('function _castEcranEtroit', 'function _appliquerEnteteCasting')
  + '\nreturn { _castEcranEtroit: _castEcranEtroit,'
  + ' _castOutilsDoiventEtreOuverts: _castOutilsDoiventEtreOuverts,'
  + ' _castFiltreListeActif: _castFiltreListeActif };')();

console.log('');
console.log('1) l en-tete ne garde que trois commandes');
for (const identifiant of ('cast-modal-header cast-head-actions cast-search-btn '
    + 'cast-filtres-btn cast-close-btn').split(' ')) {
  verifier('element #' + identifiant + ' present dans la page',
           page.indexOf('id="' + identifiant + '"') >= 0);
}
// L'ORDRE dans l'en-tete : la recherche, les filtres, puis la fermeture (la
// fermeture reste la derniere, comme dans toutes les fenetres de l'application).
const iRecherche = page.indexOf('id="cast-search-btn"');
const iFiltres   = page.indexOf('id="cast-filtres-btn"');
const iFermer    = page.indexOf('id="cast-close-btn"');
verifier('recherche, puis Filtres, puis fermeture',
         iRecherche > 0 && iRecherche < iFiltres && iFiltres < iFermer);

console.log('');
console.log('2) le tiroir des reglages et la liste des personnages');
const iOuvreTiroir = page.indexOf('id="cast-tools"');
const iFermeTiroir = page.indexOf('/#cast-tools');
verifier('le tiroir #cast-tools existe', iOuvreTiroir >= 0);
verifier('il est REPLIE dans la page (class="hidden")',
         page.indexOf('id="cast-tools" class="hidden"') >= 0);
verifier('il se referme par un repere /#cast-tools', iFermeTiroir > iOuvreTiroir);
for (const bloc of ('cast-gender-bar cast-filtre-bar cast-saga-bar '
    + 'cast-recast-bar').split(' ')) {
  const i = page.indexOf('id="' + bloc + '"');
  verifier('le bloc #' + bloc + ' est DANS le tiroir',
           i > iOuvreTiroir && i < iFermeTiroir);
}
// La liste vient APRES la fermeture du tiroir : elle ne peut donc jamais etre
// rangee dedans, ni disparaitre avec lui.
verifier('la liste #cast-list est APRES le tiroir',
         page.indexOf('id="cast-list"') > iFermeTiroir);

console.log('');
console.log('3) la recherche aussi se replie');
verifier('le champ est CACHE au depart (class="hidden")',
         page.indexOf('id="cast-search-bar" class="hidden"') >= 0);

console.log('');
console.log('4) les compteurs restent visibles, tiroir replie');
const iInfo = page.indexOf('id="cast-info-bar"');
verifier('la barre d information #cast-info-bar existe', iInfo >= 0);
verifier('elle est AVANT le tiroir (donc jamais cachee avec lui)',
         iInfo > 0 && iInfo < iOuvreTiroir);
for (const compteur of ('cast-etat-resume cast-filtre-resume cast-libres-info')
    .split(' ')) {
  const i = page.indexOf('id="' + compteur + '"');
  verifier('#' + compteur + ' est dans la barre d information',
           i > iInfo && i < iOuvreTiroir);
}

console.log('');
console.log('5) les QUATRE ages de voix (et pas cinq)');
// Precision de Laurent, le soir du 22/09/2026 : « elles sont passees a 4 dans
// la derniere session : Enfant, Jeune, Adulte et Vieux. 4, pas 5. » Le
// cinquieme bouton est « Tous les ages », qui n'est pas une categorie d'age.
const ages = (page.match(/data-age="[^"]+"/g) || [])
  .map(m => m.replace('data-age="', '').replace('"', ''))
  .filter((v, i, t) => t.indexOf(v) === i)
  .sort();
verifier('cinq boutons : « Tous les ages » plus les quatre ages',
         ages.join(',') === 'T,adulte,enfant,jeune,vieux', ages.join(','));
verifier('aucun age « mur » (retire le 21/09/2026)',
         page.indexOf('data-age="mur"') < 0);
for (const age of ('enfant jeune adulte vieux').split(' ')) {
  verifier('la categorie « ' + age + ' » a son bouton',
           page.indexOf('data-age="' + age + '"') >= 0);
}

console.log('');
console.log('6) les fonctions pures de l en-tete (extraites du fichier reel)');
const etroit = apiEntete._castEcranEtroit;
const doitOuvrir = apiEntete._castOutilsDoiventEtreOuverts;
const filtreActif = apiEntete._castFiltreListeActif;
verifier('640 px est un ecran etroit (meme limite que le CSS)',
         etroit(640) === true && etroit(360) === true);
verifier('641 px est un ecran large',
         etroit(641) === false && etroit(1024) === false);
verifier('sans navigateur ni argument, on suppose un ecran etroit (prudent)',
         etroit() === true);
verifier('tiroir replie sur telephone, ouvert sur ordinateur',
         doitOuvrir(null, 360) === false && doitOuvrir(null, 1024) === true);
verifier('le choix de Laurent l emporte sur la taille de l ecran',
         doitOuvrir(true, 360) === true && doitOuvrir(false, 1024) === false);
verifier('un filtre de liste actif est reconnu (le genre du personnage)',
         filtreActif('T') === false
         && filtreActif('H') === true
         && filtreActif('F') === true);
verifier('l etat de l en-tete est reapplique a chaque reconstruction',
         source.indexOf('  _appliquerEnteteCasting();') >= 0);
verifier('les deux boutons de l en-tete sont branches',
         source.indexOf("getElementById('cast-filtres-btn').addEventListener") >= 0
         && source.indexOf("getElementById('cast-search-btn').addEventListener") >= 0);
verifier('la recherche se replie a la fermeture de la fenetre',
         source.indexOf('_castRechercheOuverte = false;') >= 0);

console.log('');
console.log('7) la fenetre ne peut plus sortir de l ecran (styles)');
// `vh` se calcule sur l'ecran SANS la barre d'adresse : 80vh depassait donc le
// bas d'un telephone, et le detail « partagee avec ... » se retrouvait hors de
// l'ecran. La hauteur est desormais comptee en `dvh`, avec 80vh en repli.
verifier('la fenetre du casting est bornee a la hauteur REELLEMENT visible',
         styles.indexOf('max-height: min(80vh, calc(100dvh - 44px));') >= 0);
verifier('le repli 80vh reste (navigateurs sans dvh)',
         styles.indexOf('max-height: 80vh;') >= 0);
verifier('sur mobile, la fenetre occupe presque tout l ecran',
         styles.indexOf('max-height: calc(100dvh - 24px);') >= 0);
verifier('la liste des personnages garde une hauteur minimale',
         /#cast-list\s*\{[^}]*min-height:\s*90px/.test(styles));
verifier('le tiroir peut se reduire et defiler (la liste ne cede plus tout)',
         /#cast-tools\s*\{[^}]*flex:\s*0 1 auto/.test(styles)
         && /#cast-tools\s*\{[^}]*overflow-y:\s*auto/.test(styles));
verifier('les pastilles d etat tiennent sur une ligne qui defile',
         /#cast-etat-actions\s*\{[^}]*flex-wrap:\s*nowrap/.test(styles)
         && /#cast-etat-actions\s*\{[^}]*overflow-x:\s*auto/.test(styles));
verifier('les boutons de l en-tete ont leur style, et leur etat allume',
         styles.indexOf('#cast-filtres-btn') >= 0
         && styles.indexOf('#cast-filtres-btn.actif') >= 0);

console.log('');
console.log('8) les noms cliquables d un partage passent AVANT l explication');
const iChips  = source.indexOf('detail.appendChild(chips);');
const iPhrase = source.indexOf('detail.appendChild(phrase);');
verifier('les deux morceaux existent', iChips > 0 && iPhrase > 0);
verifier('les boutons de noms sont ajoutes en premier', iPhrase > iChips);
verifier('deplier amene le detail dans l ecran (defilement)',
         source.indexOf("detail.scrollIntoView({ block: 'nearest'") >= 0);

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK'
                         : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
