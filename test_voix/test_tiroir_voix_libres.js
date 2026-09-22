// Verifie le TIROIR DES VOIX LIBRES et le DEPLIAGE des partages de voix, SANS
// navigateur (demande de Laurent, 19/09/2026).
// ----------------------------------------------------------------------
// Les autres tests verifient les fonctions pures ; celui-ci verifie le RENDU :
// ce que la fenetre du casting affiche vraiment.
//   - le tiroir « Voix libres » range les voix par moteur, ecrit leur libelle
//     et donne un ▶ pour les ecouter ;
//   - un tiroir sans voix libre (ou sans moteur pret) dit POURQUOI, il ne
//     laisse jamais une liste vide et muette ;
//   - le badge de partage se deplie AU TAP : c'est indispensable, car sur
//     mobile il n'y a ni survol ni appui long (precision de Laurent).
//
// Usage : node test_voix/test_tiroir_voix_libres.js
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

// Tranches DU FICHIER REEL : si une fonction est renommee ou deplacee, le test
// echoue bruyamment au lieu de verifier une copie.
function tranche(debut, fin) {
  const d = source.indexOf(debut);
  const f = source.indexOf(fin);
  if (d < 0 || f <= d) {
    console.error('ECHEC : tranche introuvable dans app.js (' + debut + ')');
    process.exit(1);
  }
  return source.slice(d, f);
}

// Faux DOM minimal : juste ce qu'utilisent les deux fonctions.
function element(tag) {
  return {
    tag, className: '', textContent: '', title: '', type: '', value: '',
    children: [], ecouteurs: {},
    appendChild(c) { this.children.push(c); return c; },
    setAttribute(k, v) { this[k] = v; },
    addEventListener(nom, fn) { this.ecouteurs[nom] = fn; },
    querySelectorAll() { return []; },
    querySelector() { return null; },
    scrollIntoView() {},
    classList: {
      cache: [],
      toggle(nom) {
        const i = this.cache.indexOf(nom);
        if (i < 0) this.cache.push(nom); else this.cache.splice(i, 1);
      },
      add(nom) { this.cache.push(nom); },
      remove(nom) {
        const i = this.cache.indexOf(nom);
        if (i >= 0) this.cache.splice(i, 1);
      },
    },
  };
}
const fauxDocument = { createElement: element };

// La famille des moteurs : libelles ET icones, comme FAMILLES_VOIX (app.js).
// Depuis le 20/09/2026, l'en-tete de groupe d'un moteur porte son icone devant
// son nom (« 🎎 Kokoro · 12 »).
const FAMILLES_VOIX = [['edge', 'Edge (en ligne)', '\u2601\uFE0F'],
                       ['kokoro', 'Kokoro', '\uD83C\uDF8E'],
                       ['xtts', 'XTTS v2', '\uD83E\uDDEC']];
const familleDe   = (id) => (id.indexOf(':') > 0 ? id.split(':')[0] : 'edge');
const libelleVoix = (v) => v.name + ' \u2014 ' + v.region;

// La recherche du tiroir (20/09/2026) est une fonction PURE d'app.js. On donne
// ici la MEME tranche de code que test_recherche_casting.js : une seule regle
// de comparaison (accents, casse, tirets), jamais deux.
const fabriqueFiltre = new Function(
  tranche('function _cleRecherche', 'function _etatCasting')
    + '\nreturn { _filtrerVoixLibres: _filtrerVoixLibres };')();
const filtreVoixLibres = fabriqueFiltre._filtrerVoixLibres;

const fabriqueLibres = new Function(
  'document', 'FAMILLES_VOIX', '_familleDeVoix', '_libelleVoix',
  '_previewVoixLibre', '_filtrerVoixLibres',
  tranche('function _afficherVoixLibres', 'function _previewVoixLibre')
    + '\nreturn _afficherVoixLibres;');
const afficherLibres = fabriqueLibres(fauxDocument, FAMILLES_VOIX, familleDe,
  libelleVoix, () => 'apercu', filtreVoixLibres);

const fabriqueDetail = new Function(
  'document',
  tranche('function _detailPartageVoix', 'function _closeCastModal')
    + '\nreturn { _detailPartageVoix: _detailPartageVoix,'
    + ' _allerAuPersonnage: _allerAuPersonnage };');

// Faux DOM pour le SAUT vers une fiche : une liste de casting avec deux lignes,
// chacune portant son `.cast-name` comme dans la vraie liste.
function fausseLigne(nom) {
  const li = element('li');
  li.className = 'cast-row';
  li.defile = false;
  li.querySelector = () => ({ textContent: nom });
  li.scrollIntoView = () => { li.defile = true; };
  return li;
}
const ligneEdmond = fausseLigne('Edmond');
const ligneBusoni = fausseLigne('Busoni');
const fausseListe = element('ul');
fausseListe.querySelectorAll = () => [ligneEdmond, ligneBusoni];
const docCasting = {
  createElement: element,
  // Le code de la tranche branche aussi un ecouteur global (Echap = Annuler).
  addEventListener() {},
  // 'cast-list' = la vraie liste (pour le saut vers une fiche) ; tout le reste
  // (les boutons de la modale « Partager / Deplacer », presents dans la meme
  // tranche de code) recoit un faux element : leurs ecouteurs se branchent sans
  // rien casser, et le test de la modale est fait a part (section 7).
  getElementById: (id) => (id === 'cast-list' ? fausseListe : element('div')),
};
const apiCasting = fabriqueDetail(docCasting);
const detailPartage = apiCasting._detailPartageVoix;

// Un etat d'usage tel que _etatVoix le produit (deux voix libres, sur deux
// moteurs differents : la liste doit donc porter deux en-tetes).
const etatVoix = {
  nbProposees: 4,
  libres: [
    { id: 'kokoro:zoe',  name: 'Zoe',    region: 'France' },
    { id: 'xtts:yousef', name: 'Yousef', region: 'France (XTTS)' },
  ],
  porteurs: (id) => (id === 'xtts:voix3'
    ? [{ nom: 'Edmond', total: 900 }, { nom: 'Busoni', total: 120 }] : []),
  phrase: () => 'Portee par 2 personnages : Edmond (900), Busoni (120).',
};

console.log('');
console.log('1) tiroir des voix libres : rangees par moteur, ecrites, ecoutables');
const liste = element('ul');
afficherLibres(liste, etatVoix);
const textes = liste.children
  .map(c => (c.children[0] ? c.children[0].textContent : c.textContent));
verifier('un en-tete par moteur, suivi de ses voix (2 + 2 lignes)',
         liste.children.length === 4, textes.join(' | '));
verifier('chaque en-tete compte ses voix',
         textes[0] === '\uD83C\uDF8E Kokoro \u00b7 1'
         && textes[2] === '\uD83E\uDDEC XTTS v2 \u00b7 1',
         textes.join(' | '));
verifier('les voix libres sont ecrites en clair',
         textes[1].indexOf('Zoe') === 0 && textes[3].indexOf('Yousef') === 0,
         textes.join(' | '));
verifier('aucun « undefined » a l ecran',
         textes.every(t => t.indexOf('undefined') < 0), textes.join(' | '));
const ligneVoix = liste.children[1];
verifier('chaque voix libre a son bouton d ecoute (▶)',
         ligneVoix.children.length === 2
         && ligneVoix.children[1].children.length === 1
         && typeof ligneVoix.children[1].children[0].ecouteurs.click === 'function',
         JSON.stringify(ligneVoix.children.map(c => c.className)));

console.log('');
console.log('1 bis) dans la fenetre d un personnage, chaque voix devient attribuable');
// Meme liste, mais ouverte depuis un personnage (19/09/2026) : chaque voix gagne
// un bouton « Choisir » qui la lui donne.
const listeChoix = element('ul');
const choisies = [];
afficherLibres(listeChoix, etatVoix, (v) => choisies.push(v.id));
const actionsChoix = listeChoix.children[1].children[1];
verifier('un bouton « Choisir » par voix (en plus du ▶)',
         actionsChoix.children.length === 2
         && actionsChoix.children[1].textContent === 'Choisir',
         JSON.stringify(actionsChoix.children.map(c => c.textContent)));
actionsChoix.children[1].ecouteurs.click();
verifier('taper « Choisir » rend bien CETTE voix au personnage',
         choisies.length === 1 && choisies[0] === 'kokoro:zoe',
         JSON.stringify(choisies));

console.log('');
console.log('1 ter) la recherche du casting filtre AUSSI le tiroir (20/09/2026)');
// Meme barre de recherche, autre liste : ici ce sont des VOIX, pas des
// personnages. Si le filtre ne s'appliquait pas, le champ aurait l'air mort
// dans cet onglet.
const listeCherchee = element('ul');
afficherLibres(listeCherchee, etatVoix, undefined, 'yous');
const textesCherches = listeCherchee.children.map(
  c => (c.className === 'cast-group' ? c.textContent
                                     : c.children[0].textContent));
verifier('un seul moteur reste, avec sa seule voix',
         listeCherchee.children.length === 2
         && textesCherches[0] === '\uD83E\uDDEC XTTS v2 \u00b7 1'
         && textesCherches[1].indexOf('Yousef') === 0,
         textesCherches.join(' | '));
const listeSansRien = element('ul');
afficherLibres(listeSansRien, etatVoix, undefined, 'zzzz');
verifier('aucun resultat : on le DIT (pas un tiroir vide et muet)',
         listeSansRien.children.length === 1
         && listeSansRien.children[0].textContent
              .indexOf('Aucune voix libre ne correspond') === 0,
         JSON.stringify(listeSansRien.children.map(c => c.textContent)));
const listeSansFiltre = element('ul');
afficherLibres(listeSansFiltre, etatVoix, undefined, '');
verifier('champ vide : tout le tiroir, exactement comme avant',
         listeSansFiltre.children.length === 4,
         String(listeSansFiltre.children.length));

console.log('');
console.log('2) aucune voix libre : on dit POURQUOI, jamais une liste vide');
const listeVide = element('ul');
afficherLibres(listeVide, { nbProposees: 3, libres: [] });
verifier('message quand toutes les voix proposees sont prises',
         listeVide.children.length === 1
         && listeVide.children[0].textContent.indexOf('Aucune voix libre') === 0,
         JSON.stringify(listeVide.children.map(c => c.textContent)));

console.log('');
console.log('3) moteurs pas encore charges : on le dit (pas de faux « aucune »)');
const listeMoteurs = element('ul');
afficherLibres(listeMoteurs, { nbProposees: 0, libres: [] });
verifier('message sur les moteurs en cours de chargement',
         listeMoteurs.children.length === 1
         && listeMoteurs.children[0].textContent.indexOf('moteurs') > 0,
         JSON.stringify(listeMoteurs.children.map(c => c.textContent)));

console.log('');
console.log('4) badge de partage : le detail se deplie AU TAP (et au clavier)');
const badge  = element('span');
const detail = detailPartage(etatVoix, 'xtts:voix3', badge);
// Depuis le 22/09/2026, deplier MONTRE ce qu'on vient d'ouvrir : la fenetre
// defile jusqu'au detail. Sans cela, un partage deplie sur une ligne du bas
// restait sous le bord de l'ecran (constat de Laurent, 21/09/2026 : « la modale
// sort de l'ecran vers le bas »).
detail.defile = false;
detail.scrollIntoView = () => { detail.defile = true; };
const phrase = detail.children.find(c => c.className === 'cast-partage-phrase');
verifier('le detail ECRIT les noms (mobile : pas de survol possible)',
         !!phrase && phrase.textContent.indexOf('Edmond') > 0
         && phrase.textContent.indexOf('Busoni') > 0,
         phrase ? phrase.textContent : 'aucune phrase');
// Les NOMS CLIQUABLES passent AVANT l'explication : c'est eux qu'on vient
// taper, et l'explication fait quatre a six lignes sur un livre reel.
const chipsAvantPhrase = detail.children.indexOf(
  detail.children.find(c => c.className === 'cast-partage-chips'));
verifier('les noms cliquables passent AVANT l explication (22/09/2026)',
         chipsAvantPhrase >= 0 && chipsAvantPhrase < detail.children.indexOf(phrase),
         JSON.stringify(detail.children.map(c => c.className)));
verifier('le detail est cache tant qu on n a pas tape',
         detail.className.indexOf('hidden') > 0, detail.className);
verifier('un tap le deplie', typeof badge.ecouteurs.click === 'function'
         && badge.ecouteurs.click() === undefined);
verifier('un tap amene le detail dans l ecran (defilement)',
         detail.defile === true, String(detail.defile));
verifier('la touche Entree le deplie aussi (PC)',
         typeof badge.ecouteurs.keydown === 'function');
verifier('le badge est annonce comme un bouton (accessible)',
         badge.role === 'button' && badge.tabindex === '0');

console.log('');
console.log('4 bis) les co-porteurs sont CLIQUABLES (aller sur leur fiche)');
// Demande de Laurent (19/09/2026) : depuis « partagee avec Cycliste Schwinn »,
// taper le nom pour arriver sur SA fiche.
const chips = detail.children.find(c => c.className === 'cast-partage-chips');
verifier('un bouton par porteur, avec son nombre de repliques',
         !!chips && chips.children.length === 2
         && chips.children[0].textContent === 'Edmond (900)'
         && chips.children[1].textContent === 'Busoni (120)',
         chips ? chips.children.map(c => c.textContent).join(' | ') : 'aucun bouton');
verifier('chaque bouton declenche le saut',
         !!chips && chips.children.every(c => typeof c.ecouteurs.click === 'function'));
const noteDetail = detail.children.find(c => c.className === 'cast-partage-note');
chips.children[1].ecouteurs.click();
verifier('taper un nom fait DEFILER la liste jusqu a sa ligne',
         ligneBusoni.defile === true, String(ligneBusoni.defile));
verifier('la ligne visee est mise en evidence',
         ligneBusoni.classList.cache.indexOf('cast-row-survol') >= 0,
         JSON.stringify(ligneBusoni.classList.cache));
verifier('aucun message quand la fiche est trouvee',
         !!noteDetail && noteDetail.textContent === '', noteDetail && noteDetail.textContent);
// Un nom MASQUE par le filtre en cours (vue « a caster », par exemple) : le tap
// ne doit pas rester sans effet, on DIT pourquoi.
verifier('un nom hors filtre est annonce a l ecran, jamais un tap silencieux',
         apiCasting._allerAuPersonnage('Hattie Wilkerson', noteDetail) === false
         && noteDetail.textContent.indexOf('Hattie Wilkerson') === 0
         && noteDetail.textContent.indexOf('Tous') > 0,
         noteDetail.textContent);

console.log('');
console.log('5) le badge du casting ECRIT les noms (jamais un simple compte)');
// Verifie directement dans le CODE (c'est la qu'est construite la ligne) : le
// badge doit nommer les porteurs, et l'ancien libelle « voix partagee (n) » --
// celui qui ne disait pas AVEC QUI -- ne doit plus exister.
// ATTENTION aux barres obliques : app.js contient la SEQUENCE `\u29C9` (et non
// le caractere ⧉), donc on cherche le texte source tel qu'il est ecrit.
verifier('le badge de partage utilise _resumeNoms (des noms, pas un compte)',
         source.indexOf("'\\u29C9 partag\\u00e9e avec ' + _resumeNoms(autres)") >= 0);
verifier('l ancien libelle sans noms a bien disparu',
         source.indexOf("'\\u29C9 voix partag\\u00e9e ('") < 0);
verifier('la phrase complete reste en secours (survol PC, lecteur d ecran)',
         source.indexOf('badge.title = etatVoix.phrase(') >= 0);
verifier('le detail est bien accroche au badge (depliage au tap)',
         source.indexOf('_detailPartageVoix(etatVoix, v.voice_id, badge)') >= 0);
verifier('les noms du detail sont des boutons qui amenent a la fiche',
         source.indexOf('_allerAuPersonnage(p.nom, note)') >= 0
         && source.indexOf('cible.scrollIntoView') >= 0);
// Cas de Laurent sur « 22/11/63 » (19/09/2026) : le narrateur EST Jake Epping,
// et il porte la meme voix. Ce personnage doit etre SIGNALE dans la liste
// (badge informatif), sinon rien ne dit que le couple a ete voulu.
verifier('un personnage qui parle avec la voix du NARRATEUR est signale',
         source.indexOf("badge.className = 'cast-badge cast-badge-narrateur'") >= 0);
// Meme piege que plus haut : app.js contient la SEQUENCE `\uD83C\uDF99`, pas
// l'emoji lui-meme -- on cherche donc bien `\\u`.
verifier('le badge dit bien « voix du narrateur » (pas un partage a corriger)',
         source.indexOf("'\\uD83C\\uDF99 voix du narrateur'") >= 0);

console.log('');
console.log('6) apres un changement de voix, l affichage est RECALCULE');
// Constat de Laurent (19/09/2026) : apres avoir donne une voix libre a un
// personnage, sa fiche continuait d'annoncer « Portee par 2 personnages : ... »
// -- badges, groupes et tiroir n'etaient calcules qu'a l'OUVERTURE.
const codeRefresh = tranche('async function _rafraichirCastingApresChangement',
                            'function _closeCastModal');
verifier('le changement de voix attend l enregistrement avant de recalculer',
         source.indexOf('const ok = await sendUpdate()') >= 0
         && codeRefresh.length > 0);
verifier('il est appele depuis les TROIS endroits qui changent une voix',
         source.split('_rafraichirCastingApresChangement(').length - 1 === 4,
         source.split('_rafraichirCastingApresChangement(').length - 1);
verifier('il recalcule en rouvrant la fenetre (le seul calcul existant)',
         codeRefresh.indexOf('_openCastModal()') >= 0);
verifier('il ne recharge RIEN du serveur (donc instantane)',
         codeRefresh.indexOf('fetch(') < 0
         && codeRefresh.indexOf('_chargerVoixProposees') < 0
         && codeRefresh.indexOf('loadCatalogueVoix') < 0);
verifier('la position de la liste est remise apres le recalcul',
         codeRefresh.indexOf('apres.scrollTop = position') >= 0);
verifier('les curseurs vitesse/hauteur ne declenchent AUCUN recalcul',
         source.indexOf("rateInput.addEventListener('change', sendUpdate)") >= 0
         && source.indexOf("pitchInput.addEventListener('change', sendUpdate)") >= 0);
verifier('un echec d enregistrement est DIT, pas affiche comme un succes',
         source.indexOf("n\\'a pas pu être enregistré") >= 0);

console.log('');
console.log('7) modale « Partager / Deplacer » quand la voix est deja portee');
// Demande de Laurent (BACKLOG du 15/09/2026) : quand on donne a un personnage
// une voix qu'un AUTRE porte deja, l'appli DEMANDE au lieu de le faire en
// silence. On fait tourner la vraie fonction sur un faux DOM.
const codePartage = tranche('let _partageRepondre',
                            'async function _deplacerAutresVersGenerique');
const elementsPartage = {};
const docPartage = {
  getElementById: (id) => {
    if (!elementsPartage[id]) elementsPartage[id] = element('div');
    return elementsPartage[id];
  },
};
const apiPartage = new Function(
  'document', '_formatHz', '_libelleCatalogue',
  codePartage + '\nreturn { _demanderPartage: _demanderPartage,'
    + ' repondre: () => _partageRepondre };')(docPartage,
  (n) => (n >= 0 ? '+' : '') + n + 'Hz', () => 'Busoni \u2014 France (XTTS)');

(async () => {
  const promesse = apiPartage._demanderPartage('Jake Epping', 'xtts:voix3',
    [{ nom: 'Edmond' }, { nom: 'Busoni' }], 8, '');
  const texte = elementsPartage['partage-texte'].textContent;
  const note  = elementsPartage['partage-note'].textContent;
  verifier('le texte dit QUELLE voix est en cause', texte.indexOf('Busoni') > 0,
           texte);
  verifier('et QUELS personnages la portent, par leur nom',
           texte.indexOf('Edmond, Busoni') > 0
           && texte.indexOf('2 personnages') > 0, texte);
  verifier('la hauteur qui sera appliquee est ANNONCEE (+8Hz)',
           note.indexOf('+8Hz') > 0, note);
  verifier('les DEUX issues sont expliquees en clair',
           note.indexOf('Partager :') >= 0 && note.indexOf('Déplacer :') > 0, note);
  verifier('la modale s ouvre',
           elementsPartage['partage-modal'].classList.cache.indexOf('hidden') < 0);
  // On repond « Partager », puis on attend LA promesse de _demanderPartage
  // (le repondeur, lui, ne renvoie rien : il rend la main au choix en attente).
  apiPartage.repondre()('partager');
  const choix = await promesse;
  verifier('la reponse remonte au changement de voix (choix respecte)',
           choix === 'partager', choix);
  verifier('et la modale se referme',
           elementsPartage['partage-modal'].classList.cache.indexOf('hidden') >= 0);

  console.log('');
  console.log('8) la modale est branchee sur les bons gestes (code reel)');
  verifier('le choix est demande, pas suppose',
           source.indexOf('const choix = await _demanderPartage(') >= 0);
  // Depuis le 22/09/2026, la voix vit dans `voixChoisie` (il n'y a plus de menu
  // deroulant a remettre sur sa valeur). Les DEUX sorties en arriere -- Annuler,
  // et l'echec sur un personnage verrouille -- doivent la remettre : on verifie
  // donc les deux, pas une seulement.
  verifier('« Annuler » remet la voix precedente (et le verrou la laisse aussi)',
           (source.match(/voixChoisie = v\.voice_id;/g) || []).length >= 2,
           (source.match(/voixChoisie = v\.voice_id;/g) || []).length);
  verifier('« Partager » ecrit la hauteur annoncee dans le curseur',
           source.indexOf('pitchInput.value = String(pitchPropose)') >= 0
           && source.indexOf('_formatHz(pitchPropose)') >= 0);
  verifier('« Deplacer » ne touche pas a un personnage verrouille',
           source.indexOf('return !!fiche.locked;') >= 0
           && source.indexOf('Impossible de déplacer') >= 0);
  verifier('« Deplacer » donne la voix generique du GENRE (jamais un vide)',
           source.indexOf('_CAST_VOIX_GENERIQUES[0] : _CAST_VOIX_GENERIQUES[1]') >= 0);
  verifier('fermer la modale ou Echap = Annuler',
           source.indexOf("if (e.key === 'Escape' && _partageRepondre)") >= 0);

  console.log('');
  console.log('9) « Prendre une voix libre » depuis la fiche d un personnage');
  // Second morceau (19/09/2026) : on part du PERSONNAGE qu'on caste, pas du
  // tiroir -- sinon il faudrait ensuite le retrouver parmi 175.
  verifier('chaque ligne de personnage a le bouton « prendre une voix libre »',
           source.indexOf("libreBtn.addEventListener('click', () => _ouvrirVoixLibres(nom))") >= 0);
  verifier('la fenetre s ouvre sur les voix libres DE CE personnage',
           source.indexOf("'\\uD83D\\uDDE3\\uFE0F Voix libres pour ' + nom") >= 0);
  // Retouche demandee par Laurent le 19/09/2026 : une TETE QUI PARLE, jamais un
  // cadenas ouvert -- 🔓 dit deja « deverrouille » sur le bouton d'a cote, dans
  // la meme ligne. Deux sens pour une icone, c'etait une confusion de plus.
  verifier('l icone est 🗣️, et le verrou garde son dessin a lui seul',
           source.indexOf("libreBtn.textContent = '\\uD83D\\uDDE3\\uFE0F'") >= 0
           && source.indexOf('_peindreCadenas(lockBtn, !!v.locked)') >= 0);
  // Retour de Laurent le 21/09/2026 : sur son telephone, verrouille et
  // deverrouille se ressemblaient -- un emoji ne se dessine pas de la meme
  // facon selon l'appareil, et seule l'aura doree du bouton disait l'etat. Le
  // cadenas est donc DESSINE (SVG) : anse rabattue = verrouille, anse relevee =
  // deverrouille, et il prend la couleur du bouton.
  verifier('le cadenas est dessine : anse rabattue (verrouille) et anse relevee',
           source.indexOf('function _svgCadenas(verrouille)') >= 0
           && source.indexOf('M7 11V7a5 5 0 0 1 10 0v4') >= 0
           && source.indexOf('M7 11V7a5 5 0 0 1 9.9-1') >= 0);
  verifier('l etat se peint en UN seul endroit (dessin et infobulle ensemble)',
           source.indexOf('function _peindreCadenas(btn, verrouille)') >= 0
           && source.indexOf('_peindreCadenas(btn, newLocked)') >= 0);
  verifier('elle dit combien de voix sont libres, et quoi faire',
           source.indexOf("' voix que personne n\\u2019utilise encore : \\u25B6 '") >= 0);
  verifier('« Choisir » enregistre la voix PUIS recalcule le casting',
           source.indexOf('async function _donnerVoixLibre(nom, voix)') >= 0
           && source.indexOf('await _rafraichirCastingApresChangement();') >= 0);
  verifier('la vitesse et la hauteur du personnage sont CONSERVEES',
           source.indexOf("fiche.rate || '+0%',") >= 0
           && source.indexOf("fiche.pitch || '+0Hz'") >= 0);
  verifier('un echec d enregistrement est dit (moteur eteint, par exemple)',
           source.indexOf('n\\u2019a pas pu être enregistrée') >= 0);

  console.log('');
  console.log(echecs === 0 ? 'TOUT EST OK' : echecs + ' VERIFICATION(S) EN ECHEC');
  process.exit(echecs === 0 ? 0 : 1);
})();
