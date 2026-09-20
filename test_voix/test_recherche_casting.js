// Verifie la RECHERCHE dans la fenetre du casting, SANS navigateur.
// ----------------------------------------------------------------------
// Demande de Laurent (item du BACKLOG du 14/09/2026) : sur un livre a 175
// personnages, « retrouver un nom a la main devient long ». Livre le
// 20/09/2026 : un champ de saisie filtre les lignes PENDANT la frappe.
//
// Le filtrage vit dans frontend/app.js (_cleRecherche, _filtrerPersonnages,
// _filtrerVoixLibres). Ce test extrait ces fonctions DU FICHIER REEL (jamais
// une copie : si l'une est renommee ou deplacee, le test echoue bruyamment) et
// verifie ce qu'elles produisent :
//   - la frappe filtre sans accents ni casse (« EDMOND » = « Edmond ») ;
//   - tirets, apostrophes et espaces se ressemblent : « jean luc »,
//     « Jean-Luc » et « JEAN-LUC » trouvent le meme personnage ;
//   - un personnage trouve garde ses ALIAS (ses autres appellations), et taper
//     un ALIAS fait remonter SON personnage -- sinon la ligne d'alias
//     s'afficherait seule, sans dire a qui elle appartient ;
//   - champ vide : RIEN n'est filtre (l'ecran d'avant, exactement) ;
//   - aucun resultat : la liste est vide (c'est l'ecran qui explique pourquoi) ;
//   - l'article initial n'est PAS retire, contrairement au serveur : taper
//     « le » doit filtrer, pas s'evanouir ;
//   - le tiroir des VOIX LIBRES passe par la meme regle (prenom + provenance) ;
//   - la barre est bien branchee : champ, compteur, remise a zero, et la
//     recherche se COMBINE avec le filtre d'etat.
//
// Usage : node test_voix/test_recherche_casting.js
'use strict';

const fs = require('fs');
const path = require('path');

const RACINE = path.join(__dirname, '..');
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

// Tranche du fichier reel : de _cleRecherche a _etatCasting (la fonction
// suivante). Les trois fonctions de recherche y sont, ensemble.
const debut = source.indexOf('function _cleRecherche');
const fin = source.indexOf('function _etatCasting');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : les fonctions de recherche sont introuvables dans app.js');
  process.exit(1);
}
const extrait = new Function(
  source.slice(debut, fin)
  + '\nreturn { _cleRecherche: _cleRecherche,'
  + ' _filtrerPersonnages: _filtrerPersonnages,'
  + ' _filtrerVoixLibres: _filtrerVoixLibres };')();
const cle = extrait._cleRecherche;
const chercherPersonnages = extrait._filtrerPersonnages;
const chercherVoixLibres = extrait._filtrerVoixLibres;

// Un casting a familles, tel que _lignesPersonnages le construit : chaque
// principal suivi de ses alias, dans l'ordre de l'ecran.
function ligne(nom, isAlias) {
  return { nom: nom, isAlias: !!isAlias, v: { voice_id: 'x' }, total: 10 };
}
const ROWS = [
  ligne('Edmond Dantès'),
  ligne('Monte-Cristo', true),
  ligne('Abbé Busoni', true),
  ligne('Jean-Luc Picard'),
  ligne('Mercedes'),
  ligne('Le Comte de Monte-Cristo'),
];
function noms(rows) { return rows.map(r => r.nom); }

console.log('');
console.log('1) la cle de comparaison (accents, casse, tirets, espaces)');
verifier('les accents sont ignores', cle('Dantès') === 'dantes', cle('Dantès'));
verifier('la casse est ignoree', cle('EDMOND') === 'edmond', cle('EDMOND'));
verifier('le tiret devient un espace', cle('Jean-Luc') === 'jean luc', cle('Jean-Luc'));
verifier('l apostrophe devient un espace', cle("D'Artagnan") === 'd artagnan', cle("D'Artagnan"));
verifier('l apostrophe typographique aussi',
         cle('D\u2019Artagnan') === 'd artagnan', cle('D\u2019Artagnan'));
verifier('les espaces en trop sont nettoyes',
         cle('  Edmond   Dantès ') === 'edmond dantes', cle('  Edmond   Dantès '));
verifier('un champ vide donne une cle vide', cle('') === '' && cle(null) === '');
// Difference VOLONTAIRE avec le serveur (normalize_character_name, qui retire
// « le », « la », « les »...) : dans une recherche en direct, ce qui est tape
// doit filtrer. Sinon taper « le » ferait disparaitre les noms qui commencent
// par un article.
verifier('l article initial est conserve', cle('Le Comte') === 'le comte', cle('Le Comte'));

console.log('');
console.log('2) filtrage des personnages : la frappe, et les familles');
verifier('champ vide : rien n est filtre, dans l ordre',
         noms(chercherPersonnages(ROWS, '')).join('|') === noms(ROWS).join('|'));
verifier('champ vide (espaces seuls) : rien n est filtre non plus',
         chercherPersonnages(ROWS, '   ').length === ROWS.length);
verifier('une recherche simple trouve le personnage',
         noms(chercherPersonnages(ROWS, 'mercedes')).join('|') === 'Mercedes');
verifier('une recherche sans accents trouve le nom accentue',
         noms(chercherPersonnages(ROWS, 'dantes'))[0] === 'Edmond Dantès');
verifier('une recherche EN MAJUSCULES trouve aussi',
         noms(chercherPersonnages(ROWS, 'EDMOND'))[0] === 'Edmond Dantès');
verifier('une recherche accentuee trouve le nom sans accent',
         noms(chercherPersonnages(ROWS, 'Mercedès')).join('|') === 'Mercedes');
verifier('tirets et espaces se ressemblent (jean luc = Jean-Luc)',
         noms(chercherPersonnages(ROWS, 'jean luc')).join('|') === 'Jean-Luc Picard'
         && noms(chercherPersonnages(ROWS, 'JEAN-LUC')).join('|') === 'Jean-Luc Picard');
// Une ligne d'alias s'affiche EN RETRAIT sous son principal : seule, elle
// serait incomprehensible. La famille est donc toujours complete.
verifier('un personnage trouve garde ses alias',
         noms(chercherPersonnages(ROWS, 'edmond')).join('|')
           === 'Edmond Dantès|Monte-Cristo|Abbé Busoni',
         noms(chercherPersonnages(ROWS, 'edmond')).join('|'));
verifier('taper un alias fait remonter son personnage',
         noms(chercherPersonnages(ROWS, 'busoni')).join('|')
           === 'Edmond Dantès|Abbé Busoni',
         noms(chercherPersonnages(ROWS, 'busoni')).join('|'));
verifier('un alias d un autre personnage ne melange pas les familles',
         noms(chercherPersonnages(ROWS, 'comte')).join('|')
           === 'Le Comte de Monte-Cristo',
         noms(chercherPersonnages(ROWS, 'comte')).join('|'));
verifier('taper un article initial filtre (il n est pas avale)',
         noms(chercherPersonnages(ROWS, 'le')).join('|')
           === 'Le Comte de Monte-Cristo',
         noms(chercherPersonnages(ROWS, 'le')).join('|'));
verifier('aucun resultat : liste VIDE (l ecran dira pourquoi)',
         chercherPersonnages(ROWS, 'zzzz').length === 0);
verifier('aucune ligne inventee si la liste est vide',
         chercherPersonnages([], 'edmond').length === 0
         && chercherPersonnages(null, 'edmond').length === 0);
// L'affichage garde les MEMES objets de ligne : c'est ce qui permet de croiser
// la recherche avec le filtre d'etat (« a caster », « voix partagee »).
verifier('les lignes renvoyees sont les memes objets que celles du casting',
         chercherPersonnages(ROWS, 'edmond')[0] === ROWS[0]);

console.log('');
console.log('3) le tiroir des VOIX LIBRES passe par la meme regle');
const VOIX = [
  { id: 'kokoro:zoe', name: 'Zoë', region: 'France' },
  { id: 'xtts:yousef', name: 'Yousef', region: 'France (XTTS)' },
  { id: 'kyutai:ursula', name: 'Ursula', region: 'Allemagne' },
];
verifier('champ vide : tout le tiroir', chercherVoixLibres(VOIX, '').length === 3);
verifier('la recherche des voix ignore les accents',
         chercherVoixLibres(VOIX, 'zoe')[0].id === 'kokoro:zoe');
verifier('elle cherche aussi la provenance',
         chercherVoixLibres(VOIX, 'allemagne')[0].id === 'kyutai:ursula');
verifier('aucune voix ne correspond : liste vide',
         chercherVoixLibres(VOIX, 'zzzz').length === 0);
verifier('aucune voix inventee si le tiroir est vide',
         chercherVoixLibres([], 'zoe').length === 0
         && chercherVoixLibres(null, 'zoe').length === 0);

console.log('');
console.log('4) la barre est bien branchee (page + code)');
const html = fs.readFileSync(path.join(RACINE, 'frontend', 'index.html'), 'utf8');
verifier('le champ #cast-search est dans la fenetre du casting',
         html.indexOf('id="cast-search"') >= 0);
verifier('le compteur #cast-search-resume est la aussi',
         html.indexOf('id="cast-search-resume"') >= 0);
verifier('la frappe reconstruit la liste SANS rappeler le serveur',
         source.indexOf("document.getElementById('cast-search').addEventListener('input'") >= 0
         && source.indexOf('_openCastModal(false, true)') >= 0);
verifier('la recherche se COMBINE avec le filtre d etat',
         source.indexOf('const rowsTrouvees = _filtrerPersonnages(rows, recherche);') >= 0
         && source.indexOf('.filter(r => rowsTrouvees.indexOf(r) >= 0)') >= 0);
verifier('le tiroir des voix libres recoit la recherche',
         source.indexOf('_afficherVoixLibres(list, etatVoix, undefined, recherche)') >= 0);
// Sans remise a zero a la fermeture, un personnage cherche la fois precedente
// semblerait avoir disparu du livre.
const debutFermeture = source.indexOf('function _closeCastModal');
const corpsFermeture = source.slice(debutFermeture,
  source.indexOf('\n}', debutFermeture));
verifier('la recherche est remise a zero a la fermeture',
         corpsFermeture.indexOf("_castRecherche = ''") >= 0
         && corpsFermeture.indexOf('cast-search') >= 0);

console.log('');
console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
process.exit(echecs === 0 ? 0 : 1);
