'use strict';

// ============================================================
// STATE
// ============================================================

let _currentUserId   = null;
let _currentBookId   = null;
let _currentBookData = null;
let _castPollTimer   = null;
let _chapterSpeakers = {};
let _allVoices       = [];
// Catalogue COMPLET des voix (toutes familles, moteurs eteints compris),
// charge par /api/voix_catalogue. Il ne sert PAS a proposer des voix (c'est le
// role de _allVoices, limite aux voix ecoutables tout de suite) mais a les
// NOMMER : une voix deja attribuee doit s'afficher « Alphonse — France (XTTS) »
// et jamais « xtts:cml9804 » (constat de Laurent, 15/09/2026).
let _catalogueVoix   = [];
let _currentChapter  = 0;
let _totalChapters   = 0;
let _ttsState        = 'idle'; // 'idle' | 'loading' | 'playing' | 'paused'
let _ttsAbort        = null;
let _ttsSession      = 0;
let _progressTimer   = null;
// Erreur "definitive" signalee par le serveur pendant la lecture (moteur de
// voix Kyutai eteint, par exemple) : on previent une fois et on s'arrete, au
// lieu de reessayer sans fin (le reseau, lui, reste retente indefiniment).
let _ttsFatalError   = null;
// Filtre par genre des voix proposees dans la fenetre du casting : 'T'
// (toutes), 'F' (femmes) ou 'M' (hommes). Avec 135 voix au catalogue, cela
// evite de chercher une voix feminine au milieu de tout le reste.
let _castGenreFiltre = 'T';

// --- Etat des PERSONNAGES dans la fenetre du casting (15/09/2026) ---
// A ne pas confondre avec _castGenreFiltre : celui-ci filtre les VOIX
// proposees dans les menus deroulants, _castEtatFiltre filtre les LIGNES de
// personnages (tous / a caster / voix partagee).
let _castEtatFiltre = 'T';

// Barre de recherche des PERSONNAGES de la fenetre du casting (20/09/2026,
// item du BACKLOG du 14/09/2026) : le texte tape dans #cast-search. Il est
// garde ici, et non lu dans le champ au moment de l'affichage, pour que
// l'ecran puisse etre reconstruit (filtre d'etat, changement de voix) SANS
// faire perdre la recherche en cours. Remis a zero a la fermeture : on rouvre
// toujours la fenetre sur la liste complete.
let _castRecherche = '';

// --- Filtre par AGE DE LA VOIX et par GENRE DU PERSONNAGE (21/09/2026) ---
// Demande de Laurent : « Des boutons juste pour trier les voix par age [...]
// Cliquer sur "jeune" n'affiche que les jeunes. Les boutons qui sont actifs
// affichent la categorie. Idealement un filtre ; Homme / Femme et les 4 ages. »
// Troisieme filtre de LIGNES (avec l'etat et la recherche) -- a ne pas
// confondre avec _castGenreFiltre, qui filtre les VOIX des menus deroulants.
//   _castAgeFiltre   : 'T' ou 'enfant' / 'jeune' / 'adulte' / 'vieux' -- l'age
//                      annote de la VOIX que porte le personnage ;
//   _castPersoGenre  : 'T', 'F' ou 'H' -- le genre de la FICHE du personnage.
// Les deux se combinent avec l'etat et la recherche, et sont remis a zero a la
// fermeture (comme la recherche : on rouvre toujours sur la liste complete).
let _castAgeFiltre  = 'T';
let _castPersoGenre = 'T';

// Seuil des petits roles : le MEME que MINOR_THRESHOLD cote serveur
// (modules/voice_casting.py), verifie par test_voix/test_pool_casting.py.
// Il sert ici a distinguer un petit role normal (voix generique voulue) d'un
// personnage qui parle beaucoup et n'a pas encore de voix a lui : « a caster ».
const _CAST_MINOR_THRESHOLD = 8;

// Les deux voix generiques partagees des petits roles (cf. GENERIC_VOICE_F/M).
const _CAST_VOIX_GENERIQUES = ['piper:siwis:0', 'piper:tom:0'];

// --- Message audio « pas de reseau » (15/09/2026) ---
// _messageHorsLigne : URL (blob) du message prepare, ou null si pas encore pret.
// _messageAudio     : l'element audio en cours, pour pouvoir le couper.
// _messageHorsLigneQuand : date de la derniere annonce (pour espacer).
let _messageHorsLigne      = null;
let _messageAudio          = null;
let _messageHorsLigneQuand = 0;

// Etat des moteurs de voix lourds (Kyutai 8082, XTTS v2 8083), charge depuis
// /api/moteurs : { kyutai: {nom, actif, pret}, xtts: {...} }. Un moteur eteint
// (ou encore en train de charger) ne propose AUCUNE voix a l'ecran : ses voix
// disparaissent des menus, et un personnage qui en portait une affiche
// « pas de voix » dans la fenetre du casting, a corriger a la main
// (session du 14/09/2026, demande de Laurent).
let _moteursEtat  = {};
let _moteursQuand = 0;      // horodatage du dernier chargement reussi
// Etat du cache audio (20/09/2026) : { octets, quota_octets, fichiers, version },
// lu par /api/cache_audio. Sert au libelle du bouton « 🧹 Vider le cache ».
let _cacheEtat    = null;
const MOTEURS_TTL_MS = 5000;

// Changement de moteur (bouton de bascule, 15/09/2026) : un moteur met 10 a
// 20 secondes a charger son modele. Apres un clic, on interroge donc le serveur
// toutes les 3 s jusqu'a ce qu'il soit pret -- sans cela le bouton resterait
// sur « moteur eteint » et on croirait que le clic n'a rien fait.
let _moteurPollTimer = null;
let _moteurMessage   = '';   // message d'echec a afficher a la place du libelle
const MOTEUR_POLL_MS        = 3000;
const MOTEUR_ATTENTE_MAX_MS = 180000;   // 3 min : au-dela, on le dit

// Sur mobile, la sélection de texte est interceptée par le navigateur
// (menu natif copier/coller) : un tap simple sur une phrase remplace
// donc "Lire à partir d'ici" (voir la section SELECTION DE TEXTE).
const _isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

// Curseur & structure phrases/paragraphes
let _sentences       = [];  // [{text, paraIdx}, ...]
let _paragraphStarts = [];  // index de la 1ère phrase de chaque paragraphe
let _cursorIdx       = 0;   // position du curseur glitch

// Recherche dans le livre
let _searchResults    = [];
let _searchInFlight   = false;

// Mode RSVP
let _rsvpWords        = [];   // mots du chapitre courant, a plat
let _rsvpWordIdx       = 0;
let _rsvpPressed       = false;
let _rsvpTimer         = null;
let _rsvpFadeTimer     = null;
const RSVP_PUNCT_STRONG = /[.!?…:;»"]$/;
const RSVP_PUNCT_COMMA  = /,$/;

// Moteur glitch aléatoire
let _glitchEl        = null;
let _glitchRAF       = null;
let _glitchNextAt    = 0;
let _glitchActive    = false;

// ============================================================
// INIT
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
  // Service worker : garantit que les mises a jour arrivent sur mobile/PWA
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(e => {
      console.error('Echec enregistrement service worker:', e);
    });
  }
  await loadVoices();
  await loadProfiles();
  bindEvents();
});

// ============================================================
// PROFILS
// ============================================================

async function loadProfiles() {
  try {
    const res   = await fetch('/api/users');
    const users = await res.json();
    renderProfiles(users);
  } catch (e) {
    console.error('Erreur chargement profils:', e);
  }
}

function renderProfiles(users) {
  const grid = document.getElementById('profile-grid');
  grid.innerHTML = '';

  users.forEach(user => {
    const btn = document.createElement('button');
    btn.className = 'profile-card';
    btn.setAttribute('role', 'listitem');
    btn.textContent = user.name;
    btn.addEventListener('click', () => selectProfile(user.id));
    grid.appendChild(btn);
  });
}

function selectProfile(userId) {
  _currentUserId = userId;
  showView('library');
  loadLibrary();
}

// ============================================================
// VOIX
// ============================================================

// ============================================================
// LIBELLE D'UNE VOIX DANS LES MENUS
// ============================================================
// Format demande par Laurent (19/09/2026) :
//   « [Prenom] [drapeau] [Age] [Timbre] - [Moteur] »,
// par exemple « Alice <drapeau FR> Jeune aigu - Kyutai ».
// Sa regle : « je ne lis qu'en francais de toute facon » -> le drapeau de la
// LANGUE (le francais) vient TOUJOURS en premier, et un SECOND drapeau dit d'ou
// viennent le timbre ou l'accent : « Amelie <FR><GB> Mure grave - Kokoro ».
// L'age et le timbre sont les CRITERES D'ECOUTE de Laurent (sa fenetre
// « Ecouter les voix », rangees dans data/annotations_voix.json) : une voix pas
// encore annotee n'en affiche aucun, et le libelle reste lisible.
//
// Le genre (F)/(M) a disparu de ce libelle : le format demande ne le prevoit
// pas, et les menus du casting groupent deja « Femmes » / « Hommes ».
const DRAPEAU_FR = '\uD83C\uDDEB\uD83C\uDDF7';

// Un drapeau emoji s'ecrit avec DEUX « indicateurs regionaux » : d'ou ce motif
// en UTF-16 (0xD83C + 0xDDE6..0xDDFF, deux fois de suite).
const MOTIF_DRAPEAU = /\uD83C[\uDDE6-\uDDFF]\uD83C[\uDDE6-\uDDFF]/g;

// Pays ou accent ecrits EN TOUTES LETTRES. Le meme tableau sert aux deux cas :
//   - les 12 voix Edge, dont la region s'ecrit « France », « Canada »,
//     « Belgique », « Suisse » : elles n'affichaient AUCUN drapeau ;
//   - les accents nommes dans la region (« France (XTTS) - accent allemand »)
//     et ceux que Laurent annote lui-meme (anglais, italien...).
// « paysan » est un REGISTRE, pas un pays : volontairement absent.
const DRAPEAUX_PAR_MOT = {
  'france':   '\uD83C\uDDEB\uD83C\uDDF7',
  'canada':   '\uD83C\uDDE8\uD83C\uDDE6',
  'belgique': '\uD83C\uDDE7\uD83C\uDDEA',
  'suisse':   '\uD83C\uDDE8\uD83C\uDDED',
  'allemand': '\uD83C\uDDE9\uD83C\uDDEA',
  'anglais':  '\uD83C\uDDEC\uD83C\uDDE7',
  'canadien': '\uD83C\uDDE8\uD83C\uDDE6',
  'espagnol': '\uD83C\uDDEA\uD83C\uDDF8',
  'italien':  '\uD83C\uDDEE\uD83C\uDDF9',
};

// Le SECOND drapeau, par ordre de fiabilite :
//   1. un drapeau DEJA ecrit dans la region (le plus precis : Etats-Unis, Japon) ;
//   2. un accent NOMME dans la region (« accent allemand ») ;
//   3. un pays ecrit en clair (Canada, Belgique, Suisse...) ;
//   4. l'accent annote par Laurent dans la fenetre d'ecoute.
// Jamais le drapeau francais : il est deja devant. '' si la voix est francaise
// sans accent.
function _secondDrapeauDeVoix(v) {
  const region = String((v && v.region) || '');
  const trouves = (region.match(MOTIF_DRAPEAU) || [])
    .filter(drapeau => drapeau !== DRAPEAU_FR);
  if (trouves.length) {
    return trouves[0];
  }
  const bas = region.toLowerCase();
  const mots = Object.keys(DRAPEAUX_PAR_MOT);
  for (let i = 0; i < mots.length; i++) {
    if (bas.indexOf(mots[i]) >= 0 && DRAPEAUX_PAR_MOT[mots[i]] !== DRAPEAU_FR) {
      return DRAPEAUX_PAR_MOT[mots[i]];
    }
  }
  // `typeof` : certains tests node evaluent ces fonctions HORS de app.js.
  const annots = (typeof _annotationsVoix === 'undefined') ? {} : _annotationsVoix;
  const annote = annots[(v && v.id) || ''] || {};
  return DRAPEAUX_PAR_MOT[annote.accent] || '';
}

// Le libelle AFFICHE d'une valeur de critere (« mur » -> « mûr »,
// « tres_aigu » -> « très aigu »). Les libelles viennent du SERVEUR
// (`CRITERES_VOIX`, main.py) : une seule liste a maintenir.
function _libelleCritere(cle, valeur) {
  if (!valeur) {
    return '';
  }
  const criteres = (typeof _criteresVoix === 'undefined') ? [] : _criteresVoix;
  const critere = criteres.find(c => c.cle === cle);
  if (!critere) {
    return String(valeur);
  }
  const trouve = (critere.valeurs || []).find(x => x.valeur === valeur);
  return trouve ? trouve.libelle : String(valeur);
}

// Symbole du GENRE d'une voix ou d'un personnage, a poser DEVANT un prenom
// (item du BACKLOG du 19/09/2026, demande de Laurent : « on laisse le prenom,
// mais on ajoute les symboles, ca sera plus simple a l'oeil »).
// Fonction PURE (aucun DOM, aucun appel reseau) : verifiee par
// test_voix/test_libelle_voix.js, qui l'extrait du fichier reel.
// Deux pieges signales d'avance au BACKLOG, tous les deux evites ici :
//   - les symboles portent leur SELECTEUR EMOJI (\uFE0F), sinon ils s'affichent
//     en petit noir et blanc selon les claviers et les polices ;
//   - un genre INCONNU (ni F, ni M, ni H) ne recoit AUCUN symbole : mieux vaut
//     rien qu'un genre faux. Les fiches de PERSONNAGE ecrivent « H » pour un
//     homme (colonne `genre` de la table `voices`, defaut 'H'), les CATALOGUES
//     de voix ecrivent « M » : les deux sont acceptes.
function _symboleGenre(genre) {
  if (genre === 'F') return '\u2640\uFE0F';                  // femme
  if (genre === 'M' || genre === 'H') return '\u2642\uFE0F'; // homme
  return '';
}

function _libelleVoix(v) {
  const annots = (typeof _annotationsVoix === 'undefined') ? {} : _annotationsVoix;
  const annote = annots[v.id] || {};
  let notes = '';
  const age = _libelleCritere('age', annote.age);
  if (age) {
    notes += ' ' + age;
  }
  const timbre = _libelleCritere('timbre', annote.timbre);
  if (timbre) {
    notes += ' ' + timbre;
  }
  // Le moteur, montre par son ICONE (20/09/2026) : dans un menu etroit, le nom
  // (« — Kokoro ») prenait la place du prenom, de l'age et du timbre — c'est
  // justement ce que Laurent voulait remplacer. Le nom complet reste partout ou
  // il y a la place : ligne d'une voix dans « Ecouter les voix », en-tete de
  // groupe du tiroir, menu de filtre des moteurs, bouton des moteurs.
  // Le `typeof` protege le test node, qui isole cette fonction sans lui fournir
  // la table des icones : sans icone, aucun tiret orphelin n'est ecrit.
  const iconeMoteur = (typeof _iconeFamille === 'function')
    ? _iconeFamille(_familleDeVoix(v.id)) : '';
  const moteur = iconeMoteur ? ' \u2014 ' + iconeMoteur : '';
  // Le symbole du genre passe DEVANT le prenom (20/09/2026) : c'est la ou
  // l'oeil le trouve quand la liste n'est pas deja rangee par genre --
  // fenetre « Ecouter les voix » (rangee par moteur), tiroir des voix libres,
  // menu du narrateur. Dans les menus du CASTING, deja groupes « Femmes » /
  // « Hommes », il est redondant mais jamais faux : on le garde partout pour
  // que le meme prenom se lise de la meme facon dans toute l'application.
  const symbole = _symboleGenre(v.gender);
  return (symbole ? symbole + ' ' : '')
    + v.name + ' ' + DRAPEAU_FR + _secondDrapeauDeVoix(v) + notes + moteur;
}

// ---- Etat des moteurs de voix lourds (Kyutai, XTTS v2) ----
// Interroge le serveur sur les moteurs allumes, puis met a jour le voyant.
// Appele avant de construire un menu de voix : le moteur a pu etre eteint ou
// demarre depuis l'affichage de la page. Le resultat est garde 5 s en memoire
// (le serveur garde le sien 5 s aussi) pour ne pas interroger a chaque fois.
async function loadMoteurs(force) {
  const maintenant = Date.now();
  if (!force && _moteursQuand && (maintenant - _moteursQuand) < MOTEURS_TTL_MS) {
    return;
  }
  try {
    const res = await fetch('/api/moteurs');
    _moteursEtat  = (await res.json()) || {};
    _moteursQuand = Date.now();
  } catch (e) {
    console.error('Erreur chargement etat des moteurs de voix:', e);
  }
  _afficherEtatMoteurs();
}

// Texte du voyant « Réparer les moteurs de voix » selon l'etat des moteurs.
// Fonction PURE (aucun acces au DOM, aucun appel reseau) : c'est elle que le
// test extrait du fichier reel (test_voix/test_bouton_moteur.js).
//
// Depuis le 21/09/2026, elle ne parle QUE des moteurs ATTENDUS (`attendu`,
// calcule par le serveur : Pocket TTS, qui cohabite avec tout le monde, et le
// moteur lourd RETENU dans data/moteur_voix.txt). Sinon le voyant crierait pour
// XTTS eteint VOLONTAIREMENT (Kyutai est le moteur en service) : un voyant qui
// crie en permanence ne dit plus rien.
function _libelleMoteur(etat) {
  // L'ICONE du moteur accompagne son nom (comme partout ailleurs). Le `typeof`
  // protege le test node, qui isole cette fonction seule (sans la table des
  // icones) : le nom est ecrit dans tous les cas, l'icone s'ajoute quand elle
  // est connue.
  const avecIcone = (prefixe, nom) => ((typeof _libelleFamilleIcone === 'function')
    ? _libelleFamilleIcone(prefixe) : nom);
  const prets = [], chargements = [], eteints = [];
  Object.keys(etat || {}).forEach((prefixe) => {
    const info = (etat || {})[prefixe] || {};
    if (!info.attendu) return;
    const nom = avecIcone(prefixe, info.nom || prefixe);
    if (info.pret)       prets.push(nom);
    else if (info.actif) chargements.push(nom);
    else                 eteints.push(nom);
  });

  if (eteints.length) {
    return { texte: '\u26A0\uFE0F ' + eteints.join(' + ')
                    + ' \u00E9teint' + (eteints.length > 1 ? 's' : '')
                    + ' \u2014 appuyer pour r\u00E9parer',
             eteint: true };
  }
  if (chargements.length) {
    return { texte: '\u23F3 ' + chargements.join(' + ') + ' : chargement en cours...',
             eteint: false };
  }
  if (prets.length) {
    return { texte: '\uD83D\uDEE0\uFE0F Moteurs de voix : ' + prets.join(' + ')
                    + ' en marche',
             eteint: false };
  }
  // Rien d'attendu (aucun moteur retenu, et Pocket TTS pas installe) : aucun
  // voyant du tout, plutot qu'un voyant qui ne dit rien.
  return { texte: '', eteint: false };
}

// Voyant sous les reglages du lecteur. Sans lui, l'absence des voix d'un moteur
// eteint ressemblerait a un bug ; et Laurent n'aurait AUCUN moyen de rallumer un
// moteur depuis son telephone. Il remplace (21/09/2026) l'ancien bouton de
// CHANGEMENT de moteur, qui etait un piege : un clic par erreur dessus eteignait
// un moteur en marche, et ses voix disparaissaient du casting (panne du
// 21/09/2026, les 18 voix Pocket TTS).
function _afficherEtatMoteurs() {
  const el = document.getElementById('reparer-open-btn');
  if (!el) return;

  if (_moteurMessage) {
    el.textContent = _moteurMessage;
    el.classList.remove('reparer-etat-off');
    return;
  }

  const libelle = _libelleMoteur(_moteursEtat);
  el.textContent = libelle.texte;
  el.classList.toggle('reparer-etat-off', libelle.eteint);
  el.title = libelle.eteint
    ? 'Réparer les moteurs de voix : relancer ce qui s\'est éteint'
    : 'Réparer les moteurs de voix';
}

// ============================================================
// CACHE AUDIO — compte et purge a la main (20/09/2026)
// ============================================================
// Demande de Laurent (18/09/2026) : le cache se purge deja tout seul (quota de
// 2 Go, et VERSION_CACHE quand le texte envoye au moteur change), mais il
// n'avait AUCUN bouton pour le forcer -- c'est exactement ce qui manque quand on
// doute d'un rendu (le 18/09/2026, il a fallu vider le dossier a la main pour
// ecarter cette piste). Sans danger : le cache ne contient que de l'audio DEJA
// synthetise, que le moteur refera a l'identique.

// Taille lisible : « 604 Mo », « 1,2 Go », « 12 Ko ». Fonction PURE (aucun DOM,
// aucun appel reseau) : test_voix/test_cache_audio.js l'extrait du fichier reel.
function _formatOctets(octets) {
  const o = Number(octets) || 0;
  if (o >= 1024 * 1024 * 1024) {
    return (o / (1024 * 1024 * 1024)).toFixed(1).replace('.', ',') + ' Go';
  }
  if (o >= 1024 * 1024) return Math.round(o / (1024 * 1024)) + ' Mo';
  if (o >= 1024)        return Math.round(o / 1024) + ' Ko';
  return o + ' o';
}

// Libelle du bouton : « 🧹 Vider le cache (604 Mo) ». Sans compte connu (serveur
// pas encore repondu, ou erreur), il reste court et sans chiffre : jamais un
// « undefined » dans la barre du lecteur.
function _libelleBoutonCache(etat) {
  const connu = !!etat && typeof etat.octets === 'number';
  return '\uD83E\uDDF9 Vider le cache'
    + (connu ? ' (' + _formatOctets(etat.octets) + ')' : '');
}

async function _chargerEtatCache() {
  const btn = document.getElementById('cache-open-btn');
  if (!btn) return;
  try {
    const res = await fetch('/api/cache_audio');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    _cacheEtat = await res.json();
  } catch (e) {
    console.error('Erreur lecture du cache audio:', e);
    _cacheEtat = null;
  }
  btn.textContent = _libelleBoutonCache(_cacheEtat);
  if (_cacheEtat && _cacheEtat.fichiers) {
    btn.title = _cacheEtat.fichiers + ' phrase(s) déjà synthétisée(s) — quota '
      + _formatOctets(_cacheEtat.quota_octets) + '.\nLes vider ne perd aucune '
      + 'donnée : le moteur les recréera à la prochaine écoute.';
  }
}

async function _viderCacheAudio() {
  const btn = document.getElementById('cache-open-btn');
  let msg = 'Vider le cache audio ?\n\n';
  if (_cacheEtat && _cacheEtat.octets) {
    msg += 'Cela libérera ' + _formatOctets(_cacheEtat.octets)
         + ' (' + _cacheEtat.fichiers + ' phrases déjà synthétisées).\n';
  }
  msg += 'Aucune donnée n\'est perdue : c\'est de l\'audio déjà synthétisé, que '
       + 'le moteur recréera à la prochaine écoute.';
  if (!window.confirm(msg)) return;

  btn.disabled = true;
  try {
    const res = await fetch('/api/cache_audio/vider', { method: 'POST' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const r = await res.json();
    await _chargerEtatCache();          // le compte affiche repart a zero
    alert('Cache vidé : ' + _formatOctets(r.octets_liberes) + ' libérés ('
          + r.fichiers_supprimes + ' phrases).');
  } catch (e) {
    console.error('Erreur purge du cache audio:', e);
    alert('Le cache n\'a pas pu être vidé : ' + e.message);
  } finally {
    btn.disabled = false;
  }
}

// ---- Réparer les moteurs de voix : fenêtre de réparation ----
// Demande de Laurent (21/09/2026) : « un bouton qui me propose de relancer
// START.bat, comme ca si quelque chose cloche je peux le relancer depuis
// l'application ». C'est un vrai trou qu'on comble : le lanceur du PC REFUSE de
// relancer quand le lecteur tourne déjà (« déjà en marche, rien à lancer »),
// donc un moteur éteint ou planté était intouchable depuis le téléphone.
//
// Deux gestes, du plus doux au plus fort : relancer les moteurs de voix, ou
// redémarrer NIMM ePub en entier. AUCUN des deux n'ÉTEINT un moteur : c'est ce
// qui rend impossible la panne du 21/09/2026, où un clic par erreur sur
// l'ancien bouton avait fait disparaître les 18 voix Pocket TTS du casting.

async function _ouvrirReparerModal() {
  // Etat frais : on ne propose pas a l'aveugle (le moteur a pu etre allume ou
  // eteint depuis l'affichage de la page, par exemple par un lanceur a la main).
  await loadMoteurs(true);
  _remplirReparerModal();
  document.getElementById('reparer-modal').classList.remove('hidden');
}

function _fermerReparerModal() {
  document.getElementById('reparer-modal').classList.add('hidden');
}

// Detail affiche sous chaque moteur : allume et pret, en chargement, ou eteint.
function _detailMoteur(prefixe) {
  const info = (_moteursEtat || {})[prefixe] || {};
  if (info.pret)  return 'allum\u00E9 et pr\u00EAt';
  if (info.actif) return 'chargement en cours...';
  return '\u00E9teint';
}

// Etat de chaque moteur ECRIT dans la fenetre : c'est lui qui dit pourquoi une
// voix n'est pas proposee dans les menus (moteur eteint ou en chargement).
function _remplirReparerModal() {
  const detail = document.getElementById('relancer-moteurs-detail');
  if (detail) {
    const lignes = Object.keys(_moteursEtat || {}).map((prefixe) => {
      const info = _moteursEtat[prefixe] || {};
      const nom  = (typeof _libelleFamilleIcone === 'function')
        ? _libelleFamilleIcone(prefixe) : (info.nom || prefixe);
      return nom + ' : ' + _detailMoteur(prefixe);
    });
    detail.textContent = lignes.join(' · ');
  }
  const note = document.getElementById('reparer-modal-note');
  if (!note) return;
  // Pendant une ecoute : le geste doux ne coupe rien, le geste fort si. On le
  // dit AVANT le clic, jamais apres.
  note.textContent = (_ttsState === 'playing' || _ttsState === 'paused')
    ? 'Relancer les moteurs ne coupe pas la lecture. Red\u00E9marrer NIMM ePub, si.'
    : '';
}

// GESTE DOUX : demander au serveur de rallumer les moteurs ATTENDUS (Pocket TTS
// qui cohabite, et le moteur lourd retenu). Il ne touche PAS au lecteur : la
// lecture en cours continue, et l'audio deja pret n'est pas refait.
async function _relancerMoteurs() {
  const btn = document.getElementById('relancer-moteurs-btn');
  btn.disabled = true;
  try {
    const res = await fetch('/api/moteurs/relancer', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || ('HTTP ' + res.status));

    _moteursEtat  = data.etat || _moteursEtat;
    _moteursQuand = Date.now();
    _moteurMessage = '\uD83D\uDEE0\uFE0F ' + (data.message || 'relance demand\u00E9e');
    _afficherEtatMoteurs();
    _remplirReparerModal();
    _surveillerReparation();
  } catch (e) {
    console.error('Erreur relance des moteurs de voix:', e);
    _moteurMessage = '\u26A0\uFE0F ' + e.message;
    _afficherEtatMoteurs();
  } finally {
    btn.disabled = false;
  }
}

// Surveille les moteurs relances, puis recharge les voix : un moteur qui charge
// encore son modele ne propose AUCUNE voix (c'est ce qui faisait croire a une
// panne, le 21/09/2026). Au-dela de MOTEUR_ATTENTE_MAX_MS, on le DIT au lieu de
// tourner en boucle sans rien dire.
function _surveillerReparation() {
  if (_moteurPollTimer) clearInterval(_moteurPollTimer);
  const fin = Date.now() + MOTEUR_ATTENTE_MAX_MS;
  _moteurPollTimer = setInterval(async () => {
    await loadMoteurs(true);
    _remplirReparerModal();
    const enAttente = Object.keys(_moteursEtat || {}).filter((prefixe) => {
      const info = _moteursEtat[prefixe] || {};
      return info.attendu && !info.pret;
    });
    if (!enAttente.length) {
      clearInterval(_moteurPollTimer);
      _moteurPollTimer = null;
      _moteurMessage = '';
      _afficherEtatMoteurs();
      await loadVoices();          // les voix disparues reviennent dans les menus
    } else if (Date.now() > fin) {
      clearInterval(_moteurPollTimer);
      _moteurPollTimer = null;
      _moteurMessage = '\u26A0\uFE0F un moteur ne r\u00E9pond pas \u2014 relancer depuis le PC';
      _afficherEtatMoteurs();
    }
  }, MOTEUR_POLL_MS);
}

// GESTE FORT : redemarrer NIMM ePub en entier. Le SERVEUR lance START.bat comme
// un double-clic sur le PC : il arrete le serveur en cours (donc CETTE page perd
// sa connexion) et en demarre un neuf, avec le code a jour. C'est le geste qui
// manquait depuis le telephone : le lanceur du PC, lui, refuse de relancer tant
// que le lecteur tourne.
async function _redemarrerServeur() {
  const question = 'Red\u00E9marrer NIMM ePub ?\n\n'
    + 'La lecture en cours s\u2019arr\u00EAte. La page se rechargera toute seule dans '
    + 'une quinzaine de secondes.\n'
    + 'Ta position de lecture est enregistr\u00E9e : tu reprendras o\u00F9 tu en es.\n\n'
    + 'Une fen\u00EAtre de commande s\u2019ouvrira sur le PC (comme un double-clic sur '
    + 'START.bat).';
  if (!window.confirm(question)) return;

  const btn = document.getElementById('redemarrer-serveur-btn');
  btn.disabled = true;
  _fermerReparerModal();
  try {
    const res = await fetch('/api/serveur/redemarrer', { method: 'POST' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
  } catch (e) {
    console.error('Erreur redemarrage du serveur:', e);
    btn.disabled = false;
    alert('Le red\u00E9marrage n\u2019a pas pu \u00EAtre demand\u00E9 : ' + e.message
          + '\n\nRelance NIMM ePub depuis le PC (START.bat).');
    return;
  }
  await _attendreLeServeur();
}

// Attend le retour du serveur, puis recharge la page. Pendant l'attente, un
// voile couvre l'ecran et dit ce qui se passe (sinon l'ecran resterait fige sans
// rien expliquer). Au-dela d'une minute et demie, on envoie Laurent sur le PC.
async function _attendreLeServeur() {
  const voile = document.getElementById('redemarrage-voile');
  if (voile) voile.classList.remove('hidden');
  const fin = Date.now() + 90000;
  while (Date.now() < fin) {
    await new Promise(r => setTimeout(r, 2000));
    try {
      const res = await fetch('/api/moteurs?apres=' + Date.now(), { cache: 'no-store' });
      if (res.ok) {
        location.reload();
        return;
      }
    } catch (e) {
      // Le serveur est encore eteint : c'est NORMAL pendant une quinzaine de
      // secondes (START.bat arrete l'ancien, puis demarre le nouveau). On
      // reessaie, sans rien dire a l'ecran.
    }
  }
  if (voile) voile.classList.add('hidden');
  alert('Le serveur n\u2019est pas revenu au bout d\u2019une minute et demie.\n\n'
        + 'Rouvre NIMM ePub sur le PC (START.bat) : la fen\u00EAtre de commande dit '
        + 'ce qui s\u2019est pass\u00E9.');
}

// Catalogue COMPLET des voix : toutes les familles, moteurs eteints compris.
// Sert uniquement a NOMMER une voix (jamais a la proposer) : sans lui, une
// voix XTTS attribuee s'affichait sous son identifiant technique
// (« xtts:cml9804 ») des que son moteur n'etait pas pret.
async function loadCatalogueVoix() {
  try {
    const res  = await fetch('/api/voix_catalogue');
    _catalogueVoix = (await res.json()) || [];
  } catch (e) {
    console.error('Erreur chargement du catalogue des voix:', e);
  }
}

// Libelle lisible d'une voix du catalogue : « Alphonse — 🇫🇷 France (XTTS) ».
// Renvoie '' si la voix est inconnue (voix retiree du catalogue).
function _libelleCatalogue(voiceId) {
  const catalogue = (typeof _catalogueVoix === 'undefined') ? [] : _catalogueVoix;
  const v = catalogue.find(x => x.id === voiceId);
  if (!v) return '';
  return _libelleVoix(v);
}

// Est-elle ecoutable tout de suite ? (le catalogue le dit, sans deviner)
function _dispoCatalogue(voiceId) {
  const catalogue = (typeof _catalogueVoix === 'undefined') ? [] : _catalogueVoix;
  const v = catalogue.find(x => x.id === voiceId);
  return v ? v.dispo !== false : true;
}

// Recupere la liste des voix PROPOSEES (celles ecoutables tout de suite),
// sans toucher a l'ecran. La fenetre du casting s'en sert pour reconstruire ses
// menus d'un seul geste, sans reinitialiser la voix de narration du lecteur.
async function _chargerVoixProposees() {
  try {
    const res  = await fetch('/api/voices');
    _allVoices = (await res.json()) || [];
  } catch (e) {
    console.error('Erreur chargement des voix proposees:', e);
  }
}

async function loadVoices() {
  try {
    // Les voix proposees dependent des moteurs allumes : on connait leur etat
    // AVANT de construire le menu (un moteur eteint ne propose aucune voix).
    await loadMoteurs();
    await _chargerVoixProposees();
    // ...et le catalogue COMPLET, qui sert a NOMMER une voix deja attribuee
    // meme quand son moteur est eteint (15/09/2026).
    await loadCatalogueVoix();
    // Les NOTES d'ecoute de Laurent (age, timbre) et les libelles des criteres
    // (voir /api/annotations_voix/criteres) : le libelle d'une voix les affiche
    // depuis le 19/09/2026, donc la modale du casting doit les avoir AVANT de
    // construire ses menus. La fenetre « Ecouter les voix » n'a plus besoin de
    // les charger a part : cet appel les couvre.
    await _chargerAnnotationsVoix();
    await _chargerCriteresVoix();
    const sel  = document.getElementById('voice-select');
    // La voix de narration DEJA CHOISIE est conservee : recharger la liste (au
    // demarrage, apres un re-cast, ou en ouvrant le casting) ne doit pas
    // remettre Ariane d'office.
    const choisie = sel.value;
    sel.innerHTML = '';
    _allVoices.forEach(v => {
      const opt = document.createElement('option');
      opt.value       = v.id;
      opt.textContent = _libelleVoix(v);
      sel.appendChild(opt);
    });
    sel.value = (choisie && _allVoices.some(v => v.id === choisie))
      ? choisie : 'fr-CH-ArianeNeural';
  } catch (e) {
    console.error('Erreur chargement voix:', e);
  }
}

// ============================================================
// VOIX DU NARRATEUR : elle appartient au LIVRE (17/09/2026)
// ============================================================
// Demande de Laurent : « la voix du narrateur n'est pas sauvegardee apres un
// rechargement », et surtout « je n'ai pas la meme pour Monte-Cristo et pour
// 22/11/63 ». Elle est donc retenue PAR LIVRE, en base (table books, colonne
// narrator_voice) : elle suit le livre d'un appareil a l'autre.
//
// 20/09/2026 -- DEUX DEFAUTS CORRIGES (constat de Laurent : « la voix narrateur
// passe d'un livre a l'autre ; chaque livre devrait avoir son narrateur ») :
//   1. un livre SANS valeur enregistree gardait la voix du livre precedent (la
//      restauration sortait sans rien faire), et rien n'etait ecrit pour lui.
//      Il recoit maintenant la voix par DEFAUT, et cette valeur est ENREGISTREE
//      pour ce livre : chacun a SA voix, et elle le suit.
//   2. si la voix enregistree n'etait pas proposee (moteur eteint), le menu
//      gardait l'autre voix EN SILENCE (un console.warn, invisible pour
//      Laurent) : on repart sur le defaut et on le DIT sous les menus, SANS
//      ecraser le choix du livre (il revient des que le moteur est rallume).
const NARRATEUR_VOIX_DEFAUT = 'fr-CH-ArianeNeural';

// Affiche (ou efface) la ligne d'explication sous les menus du lecteur.
function _messageNarrateur(texte) {
  const el = document.getElementById('narrateur-etat');
  if (el) el.textContent = texte || '';
}

// Enregistre la voix du narrateur pour le LIVRE ouvert (et son proprietaire).
function _enregistrerVoixNarrateur(voix) {
  if (!_currentBookId) return;               // aucun livre ouvert : rien a lier
  fetch('/api/books/' + _currentBookId + '/narrator?user_id=' + _currentUserId, {
    method:  'PUT',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ voice: voix })
  }).catch(() => { /* le choix reste valable pour la session en cours */ });
}

// Met la voix du narrateur dans le menu (si elle est proposee) ; memoriser =
// garder la trace en memoire du livre ; enregistrer = ecrire pour ce livre.
function _poserVoixNarrateur(voix, memoriser, enregistrer) {
  const sel = document.getElementById('voice-select');
  if (sel && _allVoices.some(v => v.id === voix)) sel.value = voix;
  if (memoriser && _currentBookData) _currentBookData.narrator_voice = voix;
  if (enregistrer) _enregistrerVoixNarrateur(voix);
}

function _restaurerVoixNarrateur(voix) {
  const sel = document.getElementById('voice-select');
  if (!sel) return;

  const enregistree = (voix || '').trim();

  // (1) Ce livre n'a JAMAIS eu de voix de narrateur : on ne garde pas celle du
  // livre precedent (elle « passait » d'un livre a l'autre). On remet le defaut
  // ET on l'enregistre pour ce livre.
  if (!enregistree) {
    _poserVoixNarrateur(NARRATEUR_VOIX_DEFAUT, true, true);
    _messageNarrateur('');
    return;
  }

  // (2) La voix du livre existe mais n'est pas proposee : son moteur est sans
  // doute eteint. On le DIT, on lit au defaut, et on NE TOUCHE PAS au choix du
  // livre (ni en memoire, ni en base) : il revient des que le moteur est rallume.
  if (!_allVoices.some(v => v.id === enregistree)) {
    console.warn('Voix du narrateur indisponible pour ce livre :', enregistree);
    _poserVoixNarrateur(NARRATEUR_VOIX_DEFAUT, false, false);
    _messageNarrateur('Voix du narrateur de ce livre : ' + enregistree
      + ' \u2014 indisponible (moteur \u00e9teint, ou liste des voix non charg\u00e9e). '
      + 'La voix par d\u00e9faut lit en attendant ; votre choix reste enregistr\u00e9.');
    return;
  }

  // (3) Cas normal : ce livre a SA voix, et elle est proposee.
  _poserVoixNarrateur(enregistree, true, false);
  _messageNarrateur('');
}

document.getElementById('voice-select').addEventListener('change', (e) => {
  // Memoire locale mise a jour tout de suite (19/09/2026) : sans cela, la
  // fenetre du casting continuait de traiter l'ANCIENNE voix comme celle du
  // narrateur (elle la marquait « · narrateur ») jusqu'au rechargement.
  if (_currentBookData) _currentBookData.narrator_voice = e.target.value;
  _messageNarrateur('');                     // choix explicite : plus d'alerte
  _enregistrerVoixNarrateur(e.target.value);
});

// ============================================================
// BIBLIOTHEQUE
// ============================================================

async function loadLibrary() {
  try {
    const res   = await fetch('/api/books?user_id=' + _currentUserId);
    const books = await res.json();
    renderLibrary(books);
  } catch (e) {
    console.error('Erreur chargement bibliotheque:', e);
  }
}

function renderLibrary(books) {
  const grid  = document.getElementById('book-grid');
  const empty = document.getElementById('library-empty');
  grid.innerHTML = '';

  if (!books || books.length === 0) {
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');

  books.forEach(book => {
    const card = document.createElement('div');
    card.className = 'book-card';
    card.setAttribute('role', 'listitem');

    if (book.cover_path) {
      const img = document.createElement('img');
      img.className = 'book-cover';
      img.src       = '/api/books/' + book.id + '/cover?user_id=' + _currentUserId + '&v=2';
      img.alt       = book.title || 'Couverture';
      img.loading   = 'lazy';
      img.onerror   = () => { img.replaceWith(makePlaceholder()); };
      card.appendChild(img);
    } else {
      card.appendChild(makePlaceholder());
    }

    const info = document.createElement('div');
    info.className = 'book-info';

    const titleEl = document.createElement('div');
    titleEl.className   = 'book-title';
    titleEl.textContent = book.title || book.filename;

    const authorEl = document.createElement('div');
    authorEl.className   = 'book-author';
    authorEl.textContent = book.author || '';

    const bar  = document.createElement('div');
    bar.className = 'book-progress-bar';
    const fill = document.createElement('div');
    fill.className = 'book-progress-fill';
    fill.style.width = (book.chapter_index && book.chapter_index > 0) ? '35%' : '0%';
    bar.appendChild(fill);

    info.appendChild(titleEl);
    info.appendChild(authorEl);
    info.appendChild(bar);
    card.appendChild(info);

    const delBtn = document.createElement('button');
    delBtn.className = 'book-delete-btn';
    delBtn.innerHTML = '&#x2715;';
    delBtn.setAttribute('aria-label', 'Supprimer ' + (book.title || book.filename));
    delBtn.addEventListener('click', e => {
      e.stopPropagation();
      confirmDelete(book.id, book.title || book.filename);
    });
    card.appendChild(delBtn);

    card.addEventListener('click', () => openBook(book.id));
    grid.appendChild(card);
  });
}

function makePlaceholder() {
  const div = document.createElement('div');
  div.className   = 'book-cover-placeholder';
  div.textContent = '📖';
  return div;
}

// ============================================================
// UPLOAD
// ============================================================

document.getElementById('upload-input').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  e.target.value = '';

  const progress = document.getElementById('upload-progress');
  const label    = document.getElementById('upload-label');
  progress.classList.remove('hidden');
  label.textContent = 'Envoi de ' + file.name + '...';

  const body = new FormData();
  body.append('file', file);

  try {
    const res = await fetch('/api/books/upload?user_id=' + _currentUserId, { method: 'POST', body });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      label.textContent = 'Erreur : ' + (err.detail || 'upload echoue');
      setTimeout(() => progress.classList.add('hidden'), 3000);
      return;
    }
    label.textContent = 'Livre ajoute !';
    setTimeout(() => progress.classList.add('hidden'), 1500);
    await loadLibrary();
  } catch (err) {
    label.textContent = 'Erreur reseau.';
    setTimeout(() => progress.classList.add('hidden'), 3000);
  }
});

// ============================================================
// SUPPRESSION
// ============================================================

let _pendingDeleteId = null;

function confirmDelete(bookId, title) {
  _pendingDeleteId = bookId;
  document.getElementById('delete-modal-text').textContent =
    'Supprimer "' + title + '" ?';
  document.getElementById('delete-modal').classList.remove('hidden');
  document.getElementById('delete-cancel-btn').focus();
}

document.getElementById('delete-cancel-btn').addEventListener('click', () => {
  document.getElementById('delete-modal').classList.add('hidden');
  _pendingDeleteId = null;
});

document.getElementById('delete-confirm-btn').addEventListener('click', async () => {
  if (!_pendingDeleteId) return;
  document.getElementById('delete-modal').classList.add('hidden');
  try {
    await fetch('/api/books/' + _pendingDeleteId + '?user_id=' + _currentUserId, { method: 'DELETE' });
    await loadLibrary();
  } catch (err) {
    console.error('Erreur suppression:', err);
  }
  _pendingDeleteId = null;
});

// ============================================================
// LECTEUR — OUVERTURE
// ============================================================

async function openBook(bookId) {
  try {
    const userQuery = '?user_id=' + _currentUserId;
    const [bookRes, progRes] = await Promise.all([
      fetch('/api/books/' + bookId + userQuery),
      fetch('/api/progress/' + bookId + userQuery)
    ]);
    if (!bookRes.ok) return;

    _currentBookData = await bookRes.json();
    const progress   = await progRes.json();

    _currentBookId  = bookId;
    _totalChapters  = _currentBookData.chapter_count;
    _currentChapter = progress.chapter_index || 0;

    // Chaque livre a SA voix de narration : on restaure celle du livre ouvert
    // (Monte-Cristo et 22/11/63 n'ont pas la meme, demande du 17/09/2026).
    // Depuis le 20/09/2026, un livre qui n'en a AUCUNE recoit la voix par defaut
    // ET cette valeur est enregistree : il ne part plus avec la voix du livre
    // precedent. L'appel vient APRES `_currentBookId` : l'enregistrement vise
    // bien le livre qu'on ouvre.
    _restaurerVoixNarrateur(_currentBookData.narrator_voice);

    document.getElementById('reader-book-title').textContent =
      _currentBookData.title || 'Sans titre';

    showView('reader');
    renderChaptersList();
    await loadChapter(_currentChapter, progress.scroll_position || 0, progress.cursor_idx || 0);

    _updateMultivoiceBtn();
    if ((_currentBookData.cast_status || 'none').startsWith('processing')) {
      _startCastPolling();
    } else {
      _stopCastPolling();
    }

  } catch (e) {
    console.error('Erreur ouverture livre:', e);
  }
}

// ============================================================
// VOIX MULTIPLES PAR PERSONNAGE
// ============================================================

function _parsePercent(str) {
  const n = parseInt((str || '+0%').replace('%', '').replace('+', ''), 10);
  return isNaN(n) ? 0 : n;
}
function _parseHz(str) {
  const n = parseInt((str || '+0Hz').replace('Hz', '').replace('+', ''), 10);
  return isNaN(n) ? 0 : n;
}
function _formatPercent(n) { return (n >= 0 ? '+' : '') + n + '%'; }
function _formatHz(n) { return (n >= 0 ? '+' : '') + n + 'Hz'; }

// Etat d'un casting : ce que la fenetre du casting affiche comme badges et
// comme filtre de personnages (session du 15/09/2026).
// Fonction PURE (aucun acces au DOM, aucun appel reseau) : elle est donc
// verifiable telle quelle par test_voix/test_etat_casting.js, comme
// _construireMenuVoix l'est par test_filtre_genre.js.
//   - « a caster » : le personnage parle souvent (au moins le seuil des petits
//     roles) mais porte encore une voix generique -> il n'a pas de voix a lui,
//     c'est le premier a traiter ;
//   - « partagee » : sa voix est aussi portee par d'autres personnages, a
//     differencier avec la hauteur (pitch).
// ============================================================
// RECHERCHE DANS LA FENETRE DU CASTING (20/09/2026)
// ============================================================
// Demande de Laurent (item du BACKLOG du 14/09/2026) : sur un livre a 175
// personnages, « retrouver un nom a la main devient long ». Le champ de
// recherche filtre les lignes PENDANT la frappe.
// Les deux fonctions ci-dessous sont PURES (aucun DOM, aucun appel reseau) :
// verifiees par test_voix/test_recherche_casting.js.

// Cle de comparaison d'un nom : minuscules, sans accents, apostrophes, tirets
// et underscores reduits a des espaces. C'est la MEME regle que le serveur
// (`normalize_character_name`, modules/voice_casting.py), a une difference
// pres : l'article initial n'est PAS retire (« Le Comte » se trouve en tapant
// « le »). Dans une recherche en direct, ce qui est tape doit filtrer, pas
// disparaitre.
// Volontairement ecrite ici plutot que d'appeler _normalizeSearch (la
// recherche DANS LE LIVRE, definie plus bas) : la fonction reste autonome,
// donc verifiable seule par le test.
function _cleRecherche(s) {
  return (s || '').toLowerCase().normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/['\u2019\-_]/g, ' ')
    .replace(/\s+/g, ' ').trim();
}

// Lignes du casting retenues par la recherche. On compare le NOM du personnage
// ET ceux de ses ALIAS : ce sont les variantes du meme nom, elles se lisent
// ensemble. Dans les deux sens, car une famille est incomplete sinon :
//   - le personnage trouve garde ses alias (on voit toutes ses appellations) ;
//   - un alias trouve fait remonter son personnage (sans lui, on ne saurait
//     pas a qui il appartient : la ligne d'alias s'affiche en retrait SOUS lui).
// `rows` vient de _lignesPersonnages : chaque principal est suivi de ses alias,
// dans l'ordre d'affichage -- c'est ce qui permet de reconstituer les familles
// sans consulter la base.
function _filtrerPersonnages(rows, recherche) {
  const liste = rows || [];
  const q = _cleRecherche(recherche);
  if (!q) return liste;   // champ vide : rien n'est filtre, comme avant

  const groupes = [];
  liste.forEach(r => {
    const dernier = groupes[groupes.length - 1];
    if (r.isAlias && dernier) dernier.alias.push(r);
    else groupes.push({ principal: r, alias: [] });
  });

  const retenues = [];
  groupes.forEach(g => {
    if (_cleRecherche(g.principal.nom).indexOf(q) >= 0) {
      retenues.push(g.principal);
      g.alias.forEach(a => retenues.push(a));
      return;
    }
    const trouves = g.alias.filter(a => _cleRecherche(a.nom).indexOf(q) >= 0);
    if (!trouves.length) return;
    retenues.push(g.principal);
    trouves.forEach(a => retenues.push(a));
  });
  return retenues;
}

// Filtre par AGE de la VOIX et par GENRE du PERSONNAGE (21/09/2026).
// Fonctions PURES (aucun DOM, aucun appel reseau) : extraites du fichier reel
// par test_voix/test_filtre_age_casting.js, comme _filtrerPersonnages.
//
// L'AGE vient des ANNOTATIONS D'ECOUTE de la voix portee (la fenetre « Ecouter
// les voix »), pas du personnage : c'est la voix qui a un age. Une voix jamais
// annotee n'a donc PAS d'age -- et elle ne passe pas un filtre d'age, ce qui est
// voulu : on cherche ce qu'on a entendu, pas ce qu'on ne sait pas.
// Le GENRE vient de la FICHE du personnage (colonne `genre` : 'H' par defaut,
// 'F' pour une femme). On accepte 'M' comme masculin : les CATALOGUES de voix
// ecrivent « M », les fiches ecrivent « H » (meme tolerance que _symboleGenre).
function _ageDeLaVoix(voiceId) {
  const annotations = (typeof _annotationsVoix === 'undefined')
    ? {} : _annotationsVoix;
  const annote = annotations[voiceId || ''] || {};
  return annote.age || '';
}

function _lignePasseFiltres(row, ageFiltre, genreFiltre) {
  if (!row) return false;
  const fiche = row.v || {};

  if (ageFiltre && ageFiltre !== 'T') {
    if (_ageDeLaVoix(fiche.voice_id) !== ageFiltre) return false;
  }

  if (genreFiltre && genreFiltre !== 'T') {
    const genre = String(fiche.genre || '').toUpperCase();
    const estFemme = genre === 'F';
    const estHomme = genre === 'H' || genre === 'M';
    if (genreFiltre === 'F' && !estFemme) return false;
    if (genreFiltre === 'H' && !estHomme) return false;
  }
  return true;
}

// Meme recherche, appliquee aux VOIX LIBRES du tiroir : la, la liste ne montre
// plus des personnages mais des VOIX (leur prenom et leur provenance). C'est la
// meme barre de recherche : selon l'onglet ouvert, elle ne doit pas avoir l'air
// morte. On passe par _cleRecherche pour que la regle de comparaison (accents,
// casse, tirets) reste LA MEME partout.
function _filtrerVoixLibres(voix, recherche) {
  const liste = voix || [];
  const q = _cleRecherche(recherche);
  if (!q) return liste;
  return liste.filter(v => _cleRecherche(
    (v.name || '') + ' ' + (v.region || '')).indexOf(q) >= 0);
}

function _etatCasting(rows, filtre) {
  const estGenerique = (id) => _CAST_VOIX_GENERIQUES.indexOf(id) >= 0;
  const compteParVoix = {};
  // Les NOMS en plus du compte (19/09/2026) : « voix partagee (2) » ne dit pas
  // AVEC QUI. Or sur mobile il n'y a ni survol ni appui long pour aller le
  // chercher (precision de Laurent) : les noms sont donc gardes ici, pour
  // pouvoir etre ECRITS a l'ecran.
  const nomsParVoix = {};
  rows.forEach(r => {
    const id = (r.v && r.v.voice_id) || '';
    // Les voix generiques des petits roles ne comptent PAS comme partagees :
    // elles sont partagees par construction (une voix par genre pour tous les
    // petits roles), et les signaler noierait la liste sous de fausses
    // alertes. On ne signale que le partage d'une voix DEDIEE.
    if (!id || estGenerique(id)) return;
    compteParVoix[id] = (compteParVoix[id] || 0) + 1;
    (nomsParVoix[id] = nomsParVoix[id] || []).push({
      nom: r.nom, total: r.total || 0,
    });
  });
  const aCaster = (r) => estGenerique((r.v && r.v.voice_id) || '')
                          && r.total >= _CAST_MINOR_THRESHOLD;
  const partagee = (r) => !aCaster(r) && compteParVoix[r.v.voice_id] > 1;
  return {
    compteParVoix: compteParVoix,
    nomsParVoix: nomsParVoix,
    aCaster: aCaster,
    partagee: partagee,
    nbCaster: rows.filter(aCaster).length,
    nbPartagee: Object.keys(compteParVoix)
      .filter(id => compteParVoix[id] > 1).length,
    rowsFiltrees: rows.filter(r => {
      if (filtre === 'caster')   return aCaster(r);
      if (filtre === 'partagee') return partagee(r);
      return true;
    }),
  };
}

// Noms de personnages en une ligne lisible : « Edmond, Busoni et 2 autres ».
// Les badges doivent rester courts, meme sur un casting a 175 personnages.
function _resumeNoms(noms, max) {
  const liste = noms || [];
  const garde = max || 2;
  if (!liste.length) return '';
  if (liste.length <= garde) return liste.join(', ');
  const reste = liste.length - garde;
  return liste.slice(0, garde).join(', ') + ' et ' + reste
    + ' autre' + (reste > 1 ? 's' : '');
}

// Hauteur a appliquer quand on PARTAGE une voix deja portee (19/09/2026) : la
// plus petite difference encore libre, par pas de 4 Hz (le pas des curseurs du
// casting). `pitchesUtilises` = les hauteurs (en Hz, nombres) des personnages
// qui portent DEJA la voix ; on renvoie un nombre, que l'appelant ecrit en
// « +8Hz ». Le principe : deux personnages au meme timbre doivent s'entendre
// differemment, et on ne reprend JAMAIS une hauteur deja prise (sinon deux
// d'entre eux resteraient indiscernables).
// Fonction PURE (aucun DOM, aucun appel reseau) : verifiee par
// test_voix/test_etat_casting.js.
function _pitchPartageLibre(pitchesUtilises) {
  const utilises = pitchesUtilises || [];
  const candidats = [8, -8, 12, -12, 16, -16, 4, -4, 20, -20, 0];
  const trouve = candidats.find(p => utilises.indexOf(p) < 0);
  return (trouve === undefined) ? 0 : trouve;
}

// USAGE DES VOIX D'UN LIVRE (19/09/2026) : ce que la fenetre du casting, ses
// menus et le panneau « Voir la voix » affichent a cote de chaque voix.
// Fonction PURE (aucun DOM, aucun appel reseau) : elle recoit l'etat calcule
// par _etatCasting -- qui sait desormais QUELS personnages portent quelle voix
// -- puis la liste des voix PROPOSEES (celles ecoutables tout de suite) et la
// voix du narrateur. Verifiee par test_voix/test_etat_casting.js.
// Aucun texte « au survol » n'est produit : tout doit pouvoir s'ECRIRE a
// l'ecran, car sur mobile il n'y a ni survol ni appui long.
//   - « LIBRE »     : aucun personnage ne la porte -> c'est la ou piocher ;
//   - « partagee »  : plusieurs personnages la portent (les noms sont donnes) ;
//   - « narrateur » : elle lit la narration de ce livre, donc elle est prise ;
//   - « generique » : voix des petits roles (Piper siwis/tom), partagee par
//     construction : jamais comptee comme libre.
function _etatVoix(etatCasting, voixProposees, voixNarrateur) {
  const generique   = (id) => _CAST_VOIX_GENERIQUES.indexOf(id) >= 0;
  const narrateur   = voixNarrateur || '';
  const proposees   = (voixProposees || []).filter(v => v && v.id);
  const nomsParVoix = (etatCasting && etatCasting.nomsParVoix) || {};
  const porteurs    = (id) => nomsParVoix[id] || [];
  const libres      = proposees.filter(v => !generique(v.id)
    && porteurs(v.id).length === 0 && v.id !== narrateur);

  // Marque courte, collee au libelle d'une voix dans un MENU deroulant : ces
  // menus sont etroits (45 % de la ligne du personnage), donc ni noms ni
  // phrases ici -- les noms vont dans le badge (depliable au tap) et dans le
  // panneau « Voir la voix », ou il y a la place de les ecrire.
  const marque = (id) => {
    if (!id) return '';
    if (generique(id)) return ' \u00b7 petits r\u00f4les';
    if (id === narrateur) return ' \u00b7 narrateur';
    const n = porteurs(id).length;
    if (n === 0) return ' \u00b7 LIBRE';
    if (n === 1) return ' \u00b7 ' + porteurs(id)[0].nom;
    return ' \u00b7 partag\u00e9e (' + n + ')';
  };

  // Phrase COMPLETE, en texte plein : c'est elle que le badge deplie au tap et
  // que « Voir la voix » ecrit sous le menu. Jamais un survol.
  const phrase = (id) => {
    if (!id) return '';
    if (generique(id)) {
      return 'Voix g\u00e9n\u00e9rique des petits r\u00f4les : tous les '
        + 'personnages de moins de ' + _CAST_MINOR_THRESHOLD
        + ' r\u00e9pliques la partagent, par genre.';
    }
    const noms = porteurs(id);
    if (id === narrateur) {
      // La voix du narrateur est PRISE (elle lit tout le non-dialogue). Mais un
      // PERSONNAGE peut aussi parler avec : dans « 22/11/63 », le narrateur EST
      // Jake Epping, et Laurent a choisi la MEME voix pour les deux -- c'est un
      // choix valable, pas une erreur. On l'ECRIT, sinon la fiche ferait croire
      // que ce personnage n'a pas sa voix.
      const aussi = noms.length
        ? ' ' + noms.length + ' personnage' + (noms.length > 1 ? 's' : '')
          + ' parle' + (noms.length > 1 ? 'nt' : '') + ' aussi avec : '
          + _resumeNoms(noms.map(x => x.nom), 4)
          + ' (choix valable : le narrateur peut \u00eatre un personnage).'
        : '';
      return 'C\u2019est la voix du NARRATEUR de ce livre : elle lit tout ce '
        + 'qui n\u2019est pas du dialogue.' + aussi;
    }
    if (!noms.length) {
      return 'Libre : aucun personnage ne porte cette voix.';
    }
    if (noms.length === 1) {
      return 'Port\u00e9e par ' + noms[0].nom + ' (' + noms[0].total
        + ' r\u00e9pliques).';
    }
    // Au-dela de six noms, la phrase deviendrait un pave (un livre reel a une
    // voix portee par DIX-HUIT personnages) : on s'arrete a six et on renvoie a
    // l'onglet « Voix partagee », qui les liste TOUS, un par ligne.
    const montres = noms.slice(0, 6)
      .map(x => x.nom + ' (' + x.total + ' r\u00e9pliques)');
    const reste = noms.length - montres.length;
    return 'Port\u00e9e par ' + noms.length + ' personnages : '
      + montres.join(', ')
      + (reste > 0
          ? ' et ' + reste + ' autre' + (reste > 1 ? 's' : '')
            + ' (onglet « Voix partag\u00e9e » pour la liste compl\u00e8te)'
          : '')
      + '. Diff\u00e9renciez-les avec la hauteur (pitch).';
  };

  return {
    nomsParVoix: nomsParVoix,
    porteurs: porteurs,
    libres: libres,
    nbLibres: libres.length,
    nbProposees: proposees.length,
    marque: marque,
    phrase: phrase,
  };
}

// Menu deroulant des voix d'un personnage, organise par GENRE et filtre selon
// le choix en cours (_castGenreFiltre). La voix actuellement attribuee reste
// TOUJOURS visible, meme si le filtre la masque : sinon on croirait que le
// personnage n'a plus de voix.
// `etatVoix` (19/09/2026) ajoute l'etat de chaque voix au libelle (« · libre »,
// « · partagée (2) ») : c'est au moment de CHOISIR qu'on a besoin de savoir si
// la voix est libre. Il est facultatif : le test node qui isole cette fonction
// ne le fournit pas, et rien ne doit changer pour lui.
function _construireMenuVoix(voiceIdActuelle, etatVoix) {
  const usage = (!etatVoix || typeof etatVoix.marque !== 'function')
    ? () => '' : (id) => etatVoix.marque(id);
  const select = document.createElement('select');
  select.className = 'cast-voice-select';

  // Personnage SANS voix dediee (petit role, < 8 repliques depuis le
  // 15/09/2026) : ses repliques sont lues par le NARRATEUR. On l'affiche
  // clairement, sinon le menu montrerait la premiere voix du catalogue comme
  // si elle lui etait attribuee. Choisir cette entree redonne au personnage
  // la voix du narrateur (voice_id vide) ; choisir une voix l'en detache.
  if (!voiceIdActuelle) {
    const groupe = document.createElement('optgroup');
    groupe.label = '\uD83D\uDDE3\uFE0F Sans voix dediee';
    const opt = document.createElement('option');
    opt.value       = '';
    opt.textContent = '(lu par le narrateur)';
    groupe.appendChild(opt);
    select.appendChild(groupe);
  }

  // Pourquoi une voix attribuee peut manquer au catalogue : soit son moteur
  // n'est pas pret (ses voix ne sont alors pas proposees), soit elle n'existe
  // plus. Les deux cas sont distingues a l'affichage, jamais confondus. Le
  // `typeof` protege le test node, qui isole cette fonction du reste de app.js.
  const raisonIndispo = (id) => {
    if (!id || id.indexOf(':') < 0) return '';
    const prefixe = id.split(':')[0];
    const etat    = (typeof _moteursEtat === 'undefined') ? {} : _moteursEtat;
    const info    = etat[prefixe];
    if (!info || info.pret) return '';
    const nom = info.nom || prefixe;
    return info.actif ? nom + ' en chargement' : nom + ' eteint';
  };

  // Meme libelle que partout ailleurs depuis le 19/09/2026 : drapeaux, age,
  // timbre et moteur (« Alice <drapeau FR> Jeune aigu — Kyutai »). Le genre
  // n'est pas repete dans chaque ligne : le groupe « Femmes » / « Hommes » le
  // donne deja.
  // `typeof` : le test node qui isole cette fonction ne fournit pas
  // `_libelleVoix` ; il retombe alors sur l'ancien libelle (nom + region), ce
  // que ce test ne regarde pas.
  const libelle = (v) => ((typeof _libelleVoix === 'function')
    ? _libelleVoix(v) : v.name + ' \u2014 ' + v.region) + usage(v.id);

  const ajouterGroupe = (etiquette, voix) => {
    if (!voix.length) return;
    const groupe = document.createElement('optgroup');
    groupe.label = etiquette;
    voix.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = libelle(v);
      groupe.appendChild(opt);
    });
    select.appendChild(groupe);
  };

  const parGenre = (genre) => _allVoices
    .filter(v => (v.gender || '') === genre)
    .sort((a, b) => a.name.localeCompare(b.name, 'fr'));

  const actuelle = _allVoices.filter(v => v.id === voiceIdActuelle);
  if (_castGenreFiltre !== 'T' && actuelle.length &&
      (actuelle[0].gender || '') !== _castGenreFiltre) {
    ajouterGroupe('\u26A0\uFE0F Voix actuelle', actuelle);
  }
  if (_castGenreFiltre === 'T' || _castGenreFiltre === 'F') {
    ajouterGroupe('\uD83D\uDC69 Femmes', parGenre('F'));
  }
  if (_castGenreFiltre === 'T' || _castGenreFiltre === 'M') {
    ajouterGroupe('\uD83D\uDC68 Hommes', parGenre('M'));
  }
  ajouterGroupe('Autres', _allVoices.filter(v => !v.gender));

  // Securite : une voix attribuee qui n'est plus proposee doit quand meme
  // s'afficher, sinon le menu montrerait l'air de rien une AUTRE voix, ou
  // effacerait le choix sans le dire.
  if (voiceIdActuelle && !_allVoices.some(v => v.id === voiceIdActuelle)) {
    const raison = raisonIndispo(voiceIdActuelle);
    // Le NOM vient du catalogue complet (fonction du reste de app.js) : le
    // `typeof` protege le test node, qui isole cette fonction du fichier.
    const nom    = (typeof _libelleCatalogue === 'function')
      ? _libelleCatalogue(voiceIdActuelle) : '';
    const groupe = document.createElement('optgroup');
    const opt    = document.createElement('option');
    if (nom) {
      // La voix EXISTE au catalogue : on affiche son prenom, jamais son
      // identifiant technique (constat de Laurent le 15/09/2026 : les voix
      // XTTS s'affichaient « xtts:cml9804 » au lieu d'« Alphonse », parce que
      // la liste des voix proposees ne contenait que les moteurs deja prets).
      groupe.label    = raison
        ? '\u26A0\uFE0F Pas de voix (' + raison + ')'
        : '\u26A0\uFE0F Voix actuelle (non proposee ici)';
      opt.textContent = nom + (raison ? ' \u2014 ' + raison : '');
    } else if (raison) {
      // Voix inconnue du catalogue mais moteur identifie (moteur eteint ou en
      // chargement) : on garde le message d'origine, qui est deja clair.
      groupe.label    = '\u26A0\uFE0F Pas de voix (' + raison + ')';
      opt.textContent = 'Pas de voix \u2014 ' + raison;
    } else {
      // Vraiment absente du catalogue : la, l'identifiant est l'information
      // utile (voix retiree, ou livre caste avec un autre catalogue).
      groupe.label    = '\u26A0\uFE0F Voix introuvable';
      opt.textContent = voiceIdActuelle;
    }
    opt.value = voiceIdActuelle;
    groupe.appendChild(opt);
    select.appendChild(groupe);
  }

  select.value = voiceIdActuelle;
  return select;
}

async function _openCastModal(rafraichirVoix, listeSeule) {
  // Les voix proposees dependent des moteurs allumes : on rafraichit leur etat
  // AVANT de construire les menus (le moteur a pu etre eteint ou demarre
  // depuis l'affichage de la page).
  // A l'OUVERTURE de la fenetre, on recharge AUSSI la liste des voix proposees
  // et le catalogue complet : sans cela, un moteur allume apres le chargement
  // de la page restait invisible (liste perimee) et ses voix attribuees
  // s'affichaient sous leur identifiant technique (constat du 15/09/2026).
  // `listeSeule` (20/09/2026) : la barre de recherche reconstruit l'affichage a
  // CHAQUE lettre tapee. On saute alors tout ce qui parle au serveur (etat des
  // moteurs, voix proposees, catalogue, suggestions de saga) : rien n'a bouge
  // depuis l'ouverture de la fenetre, et une requete par lettre rendrait la
  // frappe molle sur un livre a 176 personnages.
  if (!listeSeule) {
    await loadMoteurs();
    if (rafraichirVoix) {
      await _chargerVoixProposees();
      await loadCatalogueVoix();
    }
  }
  const list    = document.getElementById('cast-list');
  const voices  = (_currentBookData && _currentBookData.voices) || {};
  const aliases = (_currentBookData && _currentBookData.aliases) || {};

  if (!listeSeule) {
    document.getElementById('cast-saga-input').value = (_currentBookData && _currentBookData.saga) || '';
    _loadSagaSuggestions();
  }

  // La recherche en cours est ECRITE dans le champ : l'affichage peut etre
  // reconstruit sans passer par la frappe (filtre d'etat, changement de voix),
  // et le champ doit toujours montrer ce qui filtre vraiment la liste.
  const recherche      = _castRecherche.trim();
  const champRecherche = document.getElementById('cast-search');
  if (champRecherche && champRecherche.value !== _castRecherche) {
    champRecherche.value = _castRecherche;
  }

  // Lignes a afficher : chaque principal suivi de ses alias. Construites par
  // _lignesPersonnages (partagee depuis le 19/09/2026 avec le panneau « Voir la
  // voix » : les deux comptent ainsi EXACTEMENT les memes repliques).
  const rows = _lignesPersonnages(voices, aliases);

  // La voix du NARRATEUR du livre compte comme PRISE : elle lit tout ce qui
  // n'est pas du dialogue. Sans cela elle serait proposee comme « libre », et
  // l'attribuer a un personnage donnerait deux roles pour une seule voix.
  // Le MENU du haut fait foi (il a pu changer depuis le chargement du livre) ;
  // la valeur enregistree par livre sert de secours quand il est vide.
  const choixNarrateur = document.getElementById('voice-select');
  const narrateurVoix  = (choixNarrateur && choixNarrateur.value)
    || (_currentBookData && _currentBookData.narrator_voice) || '';

  // --- Etat des voix de ce livre (session du 15/09/2026) ---
  // Les badges et le filtre viennent de _etatCasting(), une fonction pure et
  // testee (test_voix/test_etat_casting.js) : sur un gros casting, on voit
  // d'un coup d'oeil les personnages sans voix a eux (« a caster ») et les
  // timbres partages entre plusieurs personnages.
  const etat = _etatCasting(rows, _castEtatFiltre);
  // Etat d'USAGE de chaque voix : libre, prise, partagee, voix du narrateur. Il
  // alimente les badges, les menus deroulants et le tiroir « Voix libres ».
  const etatVoix = _etatVoix(etat, _allVoices, narrateurVoix);
  // Recherche (20/09/2026) : elle se COMBINE avec le filtre d'etat. Les deux
  // calculs d'etat ci-dessus restent faits sur TOUT le livre -- sans cela, les
  // compteurs et les badges « partagee avec ... » mentiraient des la premiere
  // lettre tapee, car les autres porteurs d'une meme voix disparaitraient du
  // compte. On garde donc les MEMES objets de ligne : le reste de l'affichage
  // (badges, regroupement par voix) ne voit aucune difference.
  const rowsTrouvees = _filtrerPersonnages(rows, recherche);
  const rowsAffichees = etat.rowsFiltrees
    .filter(r => rowsTrouvees.indexOf(r) >= 0)
    // Troisieme filtre (21/09/2026) : age de la VOIX et genre du PERSONNAGE.
    // Il se combine avec les deux autres, et il ne compte PAS dans les badges ni
    // dans les partages : ceux-ci restent calcules sur tout le livre.
    .filter(r => _lignePasseFiltres(r, _castAgeFiltre, _castPersoGenre));

  // Compteur du filtre d'age / de genre : il dit ce que la liste MONTRE, et sur
  // combien de personnages -- sans lui, une liste vide n'expliquerait rien.
  const resumeFiltre = document.getElementById('cast-filtre-resume');
  if (resumeFiltre) {
    const filtreActif = _castAgeFiltre !== 'T' || _castPersoGenre !== 'T';
    if (filtreActif && _castEtatFiltre !== 'libres') {
      resumeFiltre.textContent = rowsAffichees.length + ' personnage'
        + (rowsAffichees.length > 1 ? 's' : '') + ' affich\u00E9'
        + (rowsAffichees.length > 1 ? 's' : '') + ' sur ' + rows.length;
    } else {
      resumeFiltre.textContent = '';
    }
  }
  const resume = document.getElementById('cast-etat-resume');
  if (resume) {
    resume.textContent = rows.length + ' personnages \u00b7 ' + etat.nbCaster
      + ' \u00e0 caster \u00b7 ' + etat.nbPartagee + ' voix partag\u00e9e'
      + (etat.nbPartagee > 1 ? 's' : '')
      + ' \u00b7 ' + etatVoix.nbLibres + ' voix libre'
      + (etatVoix.nbLibres > 1 ? 's' : '');
  }

  // Le bouton « Voix libres » porte son compte : la reserve se voit sans avoir
  // a ouvrir l'onglet.
  const btnLibres = document.querySelector(
    '#cast-etat-actions button[data-etat="libres"]');
  if (btnLibres) {
    btnLibres.textContent = '\uD83D\uDD13 Voix libres (' + etatVoix.nbLibres + ')';
  }
  // Les moteurs eteints : leurs voix ne sont pas proposees, donc invisibles ici.
  _majInfoVoixLibres();

  list.innerHTML = '';

  // Compteur de la recherche : il dit ce que la liste MONTRE et sur combien de
  // lignes. Sans lui, un nom mal tape donnerait une liste vide sans que rien
  // n'explique pourquoi (et sur mobile, aucune infobulle n'est lisible).
  const resumeRecherche = document.getElementById('cast-search-resume');
  const ecrireResumeRecherche = (texte) => {
    if (resumeRecherche) resumeRecherche.textContent = recherche ? texte : '';
  };

  if (_castEtatFiltre === 'libres') {
    // Meme barre, autre liste : ici la liste ne montre plus des personnages
    // mais des VOIX, donc on cherche leur prenom (et leur provenance).
    _afficherVoixLibres(list, etatVoix, undefined, recherche);
    const nbLibresAffichees = _filtrerVoixLibres(etatVoix.libres, recherche).length;
    ecrireResumeRecherche(nbLibresAffichees + ' voix libre'
      + (nbLibresAffichees > 1 ? 's' : '') + ' sur ' + etatVoix.libres.length);
  } else if (rowsAffichees.length === 0) {
    const vide = document.createElement('li');
    vide.className = 'cast-empty';
    vide.textContent = recherche
      ? 'Aucun personnage ne correspond à « ' + recherche + ' ».'
      : (rows.length === 0
          ? 'Aucun personnage identifie pour ce livre.'
          : 'Aucun personnage dans ce filtre.');
    list.appendChild(vide);
    ecrireResumeRecherche('');
  } else {
    ecrireResumeRecherche(rowsAffichees.length + ' personnage'
      + (rowsAffichees.length > 1 ? 's' : '') + ' sur ' + rows.length);
    // Vue « Voix partagee » : on GROUPE les lignes par voix. Dans l'ordre
    // habituel (du plus bavard au plus discret), deux personnages qui partagent
    // un timbre ne sont JAMAIS voisins : le partage restait donc invisible.
    // Ici, une voix = un en-tete qui ECRIT les noms des porteurs (sur mobile,
    // pas de survol possible : tout ce qui compte doit etre ecrit).
    let voixPrecedente = null;
    rowsAffichees.forEach(row => {
      const nom = row.nom;
      const v   = row.v;
      if (_castEtatFiltre === 'partagee' && v.voice_id !== voixPrecedente) {
        voixPrecedente = v.voice_id;
        // L'en-tete donne la voix et le NOMBRE de porteurs : les noms sont
        // juste en dessous, un par ligne -- inutile de les repeter ici (un
        // livre reel a une voix portee par 18 personnages).
        const entete = document.createElement('li');
        entete.className = 'cast-group';
        entete.textContent = '\u29C9 '
          + (_libelleCatalogue(v.voice_id) || v.voice_id) + ' \u2014 '
          + etatVoix.porteurs(v.voice_id).length + ' personnages';
        list.appendChild(entete);
      }
      const li = document.createElement('li');
      li.className = 'cast-row' + (row.isAlias ? ' cast-row-alias' : '');

      const top = document.createElement('div');
      top.className = 'cast-row-top';

      const info = document.createElement('div');
      info.className = 'cast-row-info';
      const nameEl = document.createElement('span');
      nameEl.className = 'cast-name';
      nameEl.textContent = nom;
      const metaEl = document.createElement('span');
      metaEl.className = 'cast-meta';
      // Genre du personnage : SYMBOLE devant, puis le mot en toutes lettres
      // (item du BACKLOG du 19/09/2026) : « ♀️ Femme · 33 repliques » se
      // repere d'un coup d'oeil sur un casting de 175 personnages. Le mot reste
      // pour l'instant ; l'usage dira s'il devient inutile.
      // Un genre INCONNU n'ecrit NI signe NI mot : avant, l'ancien code
      // retombait sur « Homme » des que le genre n'etait pas 'F', donc pouvait
      // annoncer un genre FAUX. Mieux vaut « 33 repliques » que « Homme ».
      const genreLabel   = (v.genre === 'F') ? 'Femme' : (v.genre ? 'Homme' : '');
      const symboleGenre = _symboleGenre(v.genre);
      metaEl.textContent = (genreLabel
        ? (symboleGenre ? symboleGenre + ' ' : '') + genreLabel + ' \u00b7 '
        : '') + row.total + ' repliques';
      info.appendChild(nameEl);
      info.appendChild(metaEl);

      // Badge d'etat : « a caster » (voix generique alors que le personnage
      // parle beaucoup) ou « voix partagee » (meme timbre qu'un autre
      // personnage : a differencier avec la hauteur). Les petits roles restent
      // sans badge : leur voix generique est voulue.
      // Depuis le 19/09/2026, le badge de partage ECRIT les noms (demande de
      // Laurent : « je ne sais pas par quel personnage ») et se DEPLIE AU TAP :
      // sur mobile il n'y a ni survol ni appui long, donc le texte doit etre
      // atteignable par un simple tap.
      if (etat.aCaster(row)) {
        const badge = document.createElement('span');
        badge.className = 'cast-badge cast-badge-caster';
        badge.textContent = '\u26A0 \u00e0 caster';
        badge.title = 'Ce personnage parle souvent mais porte encore la voix '
          + 'g\u00e9n\u00e9rique des petits r\u00f4les : choisissez-lui une voix.';
        info.appendChild(badge);
      } else if (etat.partagee(row)) {
        const autres = etatVoix.porteurs(v.voice_id)
          .filter(x => x.nom !== nom).map(x => x.nom);
        const badge = document.createElement('span');
        badge.className = 'cast-badge cast-badge-partagee';
        badge.textContent = '\u29C9 partag\u00e9e avec ' + _resumeNoms(autres);
        badge.title = etatVoix.phrase(v.voice_id);
        info.appendChild(badge);
        info.appendChild(_detailPartageVoix(etatVoix, v.voice_id, badge));
      } else if (narrateurVoix && v.voice_id === narrateurVoix) {
        // Ce personnage parle avec la VOIX DU NARRATEUR (19/09/2026). Dans
        // « 22/11/63 », le narrateur EST Jake Epping : Laurent a choisi la meme
        // voix pour les deux, volontairement -- ce n'est pas une erreur, et
        // c'est meme le cas normal d'un recit a la premiere personne. On le
        // SIGNALE sans rien interdire, et sans le compter comme un partage
        // entre personnages. A savoir : changer la voix du narrateur ne change
        // PAS celle du personnage, les deux reglages sont separes.
        const badge = document.createElement('span');
        badge.className = 'cast-badge cast-badge-narrateur';
        badge.textContent = '\uD83C\uDF99 voix du narrateur';
        badge.title = etatVoix.phrase(v.voice_id);
        info.appendChild(badge);
      }

      const select = _construireMenuVoix(v.voice_id, etatVoix);

      const lockBtn = document.createElement('button');
      lockBtn.type = 'button';
      lockBtn.className = 'cast-lock-btn' + (v.locked ? ' locked' : '');
      lockBtn.textContent = v.locked ? '\uD83D\uDD12' : '\uD83D\uDD13';
      lockBtn.title = v.locked
        ? 'Voix verrouillee : elle sera conservee lors du re-cast.'
        : 'Verrouiller cette voix pour la conserver lors du re-cast.';
      lockBtn.addEventListener('click', () => _toggleCharacterLock(nom, lockBtn));

      top.appendChild(info);
      top.appendChild(select);
      top.appendChild(lockBtn);

      // 🗣️ « Prendre une voix libre » (19/09/2026) : ouvre la liste des voix que
      // PERSONNE ne porte encore, avec ▶ pour écouter et « Choisir » pour la
      // donner a ce personnage. On part d'ici (le personnage qu'on caste) plutot
      // que du tiroir, ou il faudrait ensuite le retrouver parmi 175.
      // L'icone est une TETE QUI PARLE, et non un cadenas ouvert : 🔓 dit deja
      // « deverrouille » sur le bouton juste a cote (retouche demandee par
      // Laurent le 19/09/2026 : un seul signe pour deux choses differentes,
      // c'etait deux sens pour une icone).
      const libreBtn = document.createElement('button');
      libreBtn.type = 'button';
      libreBtn.className = 'cast-libre-btn';
      libreBtn.textContent = '\uD83D\uDDE3\uFE0F';
      libreBtn.title = 'Prendre une voix libre : celles que personne ne porte encore.';
      libreBtn.addEventListener('click', () => _ouvrirVoixLibres(nom));
      top.appendChild(libreBtn);

      if (row.isAlias) {
        const detachBtn = document.createElement('button');
        detachBtn.type = 'button';
        detachBtn.className = 'cast-detach-btn';
        detachBtn.textContent = '\u2702';
        detachBtn.title = 'Detacher : ce nom redevient un personnage independant, avec sa propre voix.';
        detachBtn.addEventListener('click', () => _detacherAlias(nom));
        top.appendChild(detachBtn);
      }

      // Rattachement manuel (pseudonymes) : « ce nom designe la meme personne
      // que ... ». Indispensable pour Monte-Cristo / Edmond Dantes / abbe
      // Busoni / Simbad le marin, qu'aucune regle d'ecriture ne relie.
      const linkBtn = document.createElement('button');
      linkBtn.type = 'button';
      linkBtn.className = 'cast-link-btn';
      linkBtn.textContent = '\uD83D\uDD17';
      linkBtn.title = "Rattacher ce nom a un personnage : alias, pseudonyme... "
        + "Il s'affichera sous lui, mais gardera SA voix.";
      linkBtn.addEventListener('click', () => _ouvrirRattachement(nom, li));
      top.appendChild(linkBtn);

      const sliders = document.createElement('div');
      sliders.className = 'cast-row-sliders';

      const rateVal = _parsePercent(v.rate);
      const rateGroup = document.createElement('div');
      rateGroup.className = 'cast-slider-group';
      const rateLabel = document.createElement('label');
      rateLabel.textContent = 'Vitesse ' + _formatPercent(rateVal);
      const rateInput = document.createElement('input');
      rateInput.type = 'range';
      rateInput.min = '-30';
      rateInput.max = '30';
      rateInput.step = '5';
      rateInput.value = String(rateVal);
      rateGroup.appendChild(rateLabel);
      rateGroup.appendChild(rateInput);

      const pitchVal = _parseHz(v.pitch);
      const pitchGroup = document.createElement('div');
      pitchGroup.className = 'cast-slider-group';
      const pitchLabel = document.createElement('label');
      pitchLabel.textContent = 'Pitch ' + _formatHz(pitchVal);
      const pitchInput = document.createElement('input');
      pitchInput.type = 'range';
      pitchInput.min = '-20';
      pitchInput.max = '20';
      pitchInput.step = '4';
      pitchInput.value = String(pitchVal);
      pitchGroup.appendChild(pitchLabel);
      pitchGroup.appendChild(pitchInput);

      const playBtn = document.createElement('button');
      playBtn.type = 'button';
      playBtn.className = 'cast-play-btn';
      playBtn.textContent = '\u25B6\uFE0F';
      playBtn.title = 'Ecouter un aperçu';
      playBtn.addEventListener('click', () => {
        const rateStr  = _formatPercent(parseInt(rateInput.value, 10));
        const pitchStr = _formatHz(parseInt(pitchInput.value, 10));
        _previewCharacterVoice(nom, select.value, rateStr, pitchStr, playBtn);
      });

      sliders.appendChild(rateGroup);
      sliders.appendChild(pitchGroup);
      sliders.appendChild(playBtn);

      // `return` : le changement de voix ATTEND l'enregistrement (voir juste
      // apres). Sans cela, l'affichage serait recalcule AVANT que la fiche du
      // personnage ne soit a jour, donc avec l'ANCIENNE voix.
      const sendUpdate = () => {
        const rateStr  = _formatPercent(parseInt(rateInput.value, 10));
        const pitchStr = _formatHz(parseInt(pitchInput.value, 10));
        return _updateCharacterVoice(nom, select.value, rateStr, pitchStr);
      };

      // Changement de VOIX : on enregistre PUIS on recalcule tout l'affichage
      // (19/09/2026, constat de Laurent : apres avoir donne une voix libre a un
      // personnage, sa fiche continuait d'annoncer « Portee par 2 personnages :
      // ... »). Les curseurs de vitesse et de hauteur, eux, ne changent rien a
      // QUI porte quelle voix : ils ne declenchent pas de recalcul, sinon la
      // fiche sauterait pendant qu'on regle.
      select.addEventListener('change', async () => {
        // La voix choisie est-elle deja portee par un AUTRE personnage ? Alors
        // c'est un CHOIX a faire, plus un accident silencieux (19/09/2026).
        const voix   = select.value;
        const autres = etatVoix.porteurs(voix).filter(x => x.nom !== nom);
        if (autres.length) {
          const pitchPropose = _pitchPartageLibre(autres.map(x => _parseHz(
            ((_currentBookData.voices || {})[x.nom] || {}).pitch)));
          const choix = await _demanderPartage(nom, voix, autres, pitchPropose,
                                              narrateurVoix);
          if (choix === 'annuler') {
            select.value = v.voice_id;   // rien ne bouge, comme avant le choix
            return;
          }
          if (choix === 'partager') {
            // La hauteur ANNONCEE dans la modale est ecrite dans le curseur :
            // Laurent la voit, et elle partira avec l'enregistrement.
            pitchInput.value = String(pitchPropose);
            pitchLabel.textContent = 'Pitch ' + _formatHz(pitchPropose);
          } else if (!await _deplacerAutresVersGenerique(autres)) {
            select.value = v.voice_id;   // echec (verrou) : on ne change rien
            return;
          }
        }
        const ok = await sendUpdate();
        if (ok === false) {
          alert('Le changement de voix n\'a pas pu être enregistré : '
            + 'l\'affichage revient donc sur la voix précédente.');
        }
        await _rafraichirCastingApresChangement();
      });
      rateInput.addEventListener('input', () => {
        rateLabel.textContent = 'Vitesse ' + _formatPercent(parseInt(rateInput.value, 10));
      });
      rateInput.addEventListener('change', sendUpdate);
      pitchInput.addEventListener('input', () => {
        pitchLabel.textContent = 'Pitch ' + _formatHz(parseInt(pitchInput.value, 10));
      });
      pitchInput.addEventListener('change', sendUpdate);

      li.appendChild(top);
      li.appendChild(sliders);
      list.appendChild(li);
    });
  }

  // Barre de filtre par genre : on met en evidence le choix en cours.
  document.querySelectorAll('#cast-gender-actions button').forEach(b => {
    b.classList.toggle('actif', b.dataset.genre === _castGenreFiltre);
  });

  // Barre de filtre par etat des personnages : meme mise en evidence.
  document.querySelectorAll('#cast-etat-actions button').forEach(b => {
    b.classList.toggle('actif', b.dataset.etat === _castEtatFiltre);
  });

  // Barre de filtre par age de la voix et par genre du personnage (21/09/2026) :
  // meme mise en evidence -- c'est ce qui montre d'un coup d'oeil la categorie
  // choisie, comme Laurent l'a demande.
  document.querySelectorAll('#cast-age-actions button').forEach(b => {
    b.classList.toggle('actif', b.dataset.age === _castAgeFiltre);
  });
  document.querySelectorAll('#cast-perso-genre-actions button').forEach(b => {
    b.classList.toggle('actif', b.dataset.perso === _castPersoGenre);
  });

  document.getElementById('cast-modal').classList.remove('hidden');
}

// ============================================================
// VOIX LIBRES ET PARTAGES DE VOIX (19/09/2026)
// ============================================================
// Demande de Laurent : dans un casting a beaucoup de personnages, « je ne vois
// pas quelle voix est libre » et « je ne sais pas par quel personnage une voix
// est partagee ». Les reponses sont ici, et elles sont ECRITES a l'ecran --
// jamais cachees derriere un survol, car sur mobile il n'y a ni survol ni
// appui long.

// Lignes du casting : chaque personnage principal suivi de ses alias, du plus
// bavard au plus discret (les repliques d'un alias comptent pour son
// personnage). Extrait de _openCastModal le 19/09/2026 pour que le panneau
// « Voir la voix » compte EXACTEMENT les memes repliques : une seule regle.
function _lignesPersonnages(voices, aliases) {
  const aliasOf = {};   // principal -> [alias, ...]
  Object.keys(aliases || {}).forEach(al => {
    const canon = aliases[al];
    if (voices[al] && voices[canon]) (aliasOf[canon] = aliasOf[canon] || []).push(al);
  });
  const racineDe = (nom) => {
    const canon = aliases[nom];
    return (canon && voices[canon]) ? canon : nom;
  };
  const totalDe = (nom) => {
    let total = voices[nom] ? (voices[nom].line_count || 0) : 0;
    (aliasOf[nom] || []).forEach(al => { total += (voices[al].line_count || 0); });
    return total;
  };

  const rows = [];
  Object.keys(voices)
    .filter(nom => racineDe(nom) === nom)
    .sort((a, b) => totalDe(b) - totalDe(a))
    .forEach(nom => {
      rows.push({ nom: nom, v: voices[nom], total: totalDe(nom), isAlias: false });
      (aliasOf[nom] || []).slice().sort().forEach(al => {
        rows.push({ nom: al, v: voices[al], total: voices[al].line_count || 0,
                    isAlias: true });
      });
    });
  return rows;
}

// Etat d'usage des voix du LIVRE OUVERT : meme calcul que la fenetre du casting
// (memes fonctions pures), pour le panneau « Voir la voix ».
function _etatVoixLivre() {
  const voices  = (_currentBookData && _currentBookData.voices)  || {};
  const aliases = (_currentBookData && _currentBookData.aliases) || {};
  const etat    = _etatCasting(_lignesPersonnages(voices, aliases), 'T');
  const choix   = document.getElementById('voice-select');
  // Le MENU fait foi (il a pu changer depuis le chargement du livre) ; la
  // valeur enregistree par livre sert de secours quand il est vide.
  const narrateur = (choix && choix.value)
    || (_currentBookData && _currentBookData.narrator_voice) || '';
  return _etatVoix(etat, _allVoices, narrateur);
}

// Detail d'un partage de voix, DEPLIE AU TAP sur le badge. Pourquoi un tap et
// non un survol : sur mobile il n'y a ni survol ni appui long (precision de
// Laurent, 19/09/2026) -- et un tap fonctionne partout, PWA comprise.
function _detailPartageVoix(etatVoix, voiceId, badge) {
  const detail = document.createElement('div');
  detail.className = 'cast-partage-detail hidden';

  const phrase = document.createElement('p');
  phrase.className = 'cast-partage-phrase';
  phrase.textContent = etatVoix.phrase(voiceId);
  detail.appendChild(phrase);

  // Les co-porteurs, en BOUTONS (demande de Laurent, 19/09/2026 : « pouvoir
  // cliquer sur Cycliste Schwinn pour arriver sur sa fiche »). Des boutons et
  // non des liens dans la phrase : sur mobile, une cible tactile doit etre
  // franche, et un nom au milieu d'un paragraphe ne se tape pas bien.
  const porteurs = etatVoix.porteurs(voiceId);
  if (porteurs.length > 1) {
    const chips = document.createElement('div');
    chips.className = 'cast-partage-chips';
    porteurs.forEach(p => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'cast-partage-chip';
      btn.textContent = p.nom + ' (' + p.total + ')';
      btn.title = 'Aller \u00e0 la fiche de ' + p.nom;
      btn.addEventListener('click', () => _allerAuPersonnage(p.nom, note));
      chips.appendChild(btn);
    });
    detail.appendChild(chips);
  }

  // Message d'explication si un nom n'est pas affiche (filtre en cours) : mieux
  // vaut le dire que de ne rien faire quand on tape.
  const note = document.createElement('p');
  note.className = 'cast-partage-note';
  detail.appendChild(note);

  const basculer = () => detail.classList.toggle('hidden');
  badge.setAttribute('role', 'button');
  badge.setAttribute('tabindex', '0');
  badge.addEventListener('click', basculer);
  badge.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); basculer(); }
  });
  return detail;
}

// Amene l'ecran sur la fiche d'un personnage, depuis le partage d'une voix
// (demande de Laurent, 19/09/2026). Fait defiler la liste, met la ligne en
// evidence un court instant, et renvoie false si la ligne n'est PAS affichee
// (un filtre la cache) : dans ce cas l'appelant le DIT, plutot que de ne rien
// faire en silence.
function _allerAuPersonnage(nom, note) {
  const liste = document.getElementById('cast-list');
  const lignes = liste
    ? Array.prototype.slice.call(liste.querySelectorAll('li.cast-row')) : [];
  const cible = lignes.find(li => {
    const el = li.querySelector('.cast-name');
    return !!el && el.textContent === nom;
  });
  if (!cible) {
    if (note) {
      note.textContent = nom + ' n\u2019appara\u00eet pas dans ce filtre : '
        + 'choisissez \u00ab Tous \u00bb pour le voir.';
    }
    return false;
  }
  if (note) note.textContent = '';
  if (typeof cible.scrollIntoView === 'function') {
    cible.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
  cible.classList.add('cast-row-survol');
  setTimeout(() => cible.classList.remove('cast-row-survol'), 1600);
  return true;
}

// --- « Partager / Deplacer » une voix deja portee (19/09/2026) ---
// Decide avec Laurent le 15/09/2026 (item du BACKLOG) : quand on choisit pour un
// personnage une voix qu'un AUTRE porte deja, l'appli ne fait plus semblant de
// rien -- elle DEMANDE. Une modale plutot qu'un `confirm` : il y a DEUX issues
// possibles, et le texte doit nommer les personnages concernes.
// La reponse revient par une promesse : 'partager' | 'deplacer' | 'annuler'.
let _partageRepondre = null;   // la reponse en attente (une seule a la fois)

function _demanderPartage(nom, voiceId, autres, pitchPropose, voixNarrateur) {
  const noms = autres.map(x => x.nom);
  const plusieurs = noms.length > 1;
  document.getElementById('partage-texte').textContent =
    'La voix « ' + (_libelleCatalogue(voiceId) || voiceId) + ' » est déjà '
    + 'portée par ' + noms.length + ' personnage' + (plusieurs ? 's' : '')
    + ' : ' + noms.join(', ') + '.';
  const morceaux = [
    'Partager : ' + noms.join(', ') + ' garde' + (plusieurs ? 'nt' : '')
      + ' la voix, et ' + nom + ' la reçoit avec une hauteur de '
      + _formatHz(pitchPropose) + ' pour rester distinguable.',
    'Déplacer : ' + noms.join(', ') + ' repasse' + (plusieurs ? 'nt' : '')
      + ' « à caster » (voix générique provisoire), et ' + nom
      + ' garde la voix.',
  ];
  if (voiceId === voixNarrateur) {
    morceaux.push('À savoir : c\u2019est aussi la VOIX DU NARRATEUR de ce livre.');
  }
  document.getElementById('partage-note').textContent = morceaux.join(' ');
  const modal = document.getElementById('partage-modal');
  modal.classList.remove('hidden');
  return new Promise((resoudre) => {
    _partageRepondre = (choix) => {
      _partageRepondre = null;
      modal.classList.add('hidden');
      resoudre(choix);
    };
  });
}

// « Deplacer » : la voix reste au personnage qui vient de la prendre, et l'AUTRE
// (ou les autres) repasse « a caster » -- voix GENERIQUE des petits roles de son
// genre, jamais un vide (un vide casserait la lecture). Un personnage VERROUILLE
// n'est jamais deplace : le verrou existe pour ca, on le dit et on ne touche a
// rien. Renvoie false si rien n'a pu etre fait (l'appelant remet alors le menu
// comme avant).
async function _deplacerAutresVersGenerique(autres) {
  const verrouilles = autres.filter(x => {
    const fiche = (_currentBookData.voices || {})[x.nom] || {};
    return !!fiche.locked;
  });
  if (verrouilles.length) {
    alert('Impossible de déplacer : ' + verrouilles.map(x => x.nom).join(', ')
      + ' est verrouillé (🔒). Déverrouillez-le d\u2019abord, ou choisissez '
      + '« Partager ».');
    return false;
  }
  for (let i = 0; i < autres.length; i++) {
    const fiche = (_currentBookData.voices || {})[autres[i].nom] || {};
    // La voix generique depend du GENRE : piper:siwis:0 (femmes) ou
    // piper:tom:0 (hommes) -- les deux constantes du casting.
    const generique = (fiche.genre === 'F')
      ? _CAST_VOIX_GENERIQUES[0] : _CAST_VOIX_GENERIQUES[1];
    const ok = await _updateCharacterVoice(autres[i].nom, generique,
                                           fiche.rate || '+0%', '+0Hz');
    if (!ok) {
      alert('Impossible de déplacer : la voix de ' + autres[i].nom
        + ' n\u2019a pas pu être modifiée.');
      return false;
    }
  }
  return true;
}

// Reponses de la modale : chacune rend la main au changement de voix qui attend
// (voir _demanderPartage). Fermer la modale ou taper a cote = Annuler : jamais
// de choix par inadvertance.
document.getElementById('partage-partager-btn').addEventListener('click', () => {
  if (_partageRepondre) _partageRepondre('partager');
});
document.getElementById('partage-deplacer-btn').addEventListener('click', () => {
  if (_partageRepondre) _partageRepondre('deplacer');
});
document.getElementById('partage-annuler-btn').addEventListener('click', () => {
  if (_partageRepondre) _partageRepondre('annuler');
});
document.getElementById('partage-close-btn').addEventListener('click', () => {
  if (_partageRepondre) _partageRepondre('annuler');
});
document.getElementById('partage-modal').addEventListener('click', (e) => {
  if (e.target.id === 'partage-modal' && _partageRepondre) {
    _partageRepondre('annuler');
  }
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && _partageRepondre) _partageRepondre('annuler');
});

// Tiroir « Voix libres » : les voix ECOUTABLES TOUT DE SUITE qu'aucun
// personnage (ni le narrateur) ne porte, rangees par moteur comme dans
// « Ecouter les voix », avec ▶ pour les reconnaitre.
// `choisir` (facultatif, 19/09/2026) : quand il est fourni, chaque voix gagne un
// bouton « Choisir » qui attribue cette voix au personnage ouvert -- c'est le
// meme affichage, reutilise par la fenetre « Voix libres pour <nom> ».
function _afficherVoixLibres(list, etatVoix, choisir, recherche) {
  // `recherche` (20/09/2026, facultatif) : la barre de recherche de la fenetre
  // du casting s'applique ici aussi, ou la liste ne montre plus des personnages
  // mais des VOIX (leur prenom). Vide ou absent : tout le tiroir, comme avant.
  const libres = _filtrerVoixLibres(etatVoix.libres, recherche);
  if (!etatVoix.nbProposees) {
    const vide = document.createElement('li');
    vide.className = 'cast-empty';
    vide.textContent = 'Aucune voix proposée pour l\u2019instant : les moteurs '
      + 'sont peut-être encore en cours de chargement.';
    list.appendChild(vide);
    return;
  }
  if (!etatVoix.libres.length) {
    const vide = document.createElement('li');
    vide.className = 'cast-empty';
    vide.textContent = 'Aucune voix libre : toutes les voix proposées sont déjà '
      + 'portées par un personnage.';
    list.appendChild(vide);
    return;
  }
  if (!libres.length) {
    // Recherche sans resultat. A dire : un tiroir vide et muet ferait croire
    // que toutes les voix sont prises, alors que c'est le filtre qui a parle.
    const vide = document.createElement('li');
    vide.className = 'cast-empty';
    vide.textContent = 'Aucune voix libre ne correspond à « '
      + (recherche || '').trim() + ' ».';
    list.appendChild(vide);
    return;
  }
  FAMILLES_VOIX.forEach(([cle, libelle, icone]) => {
    const duMoteur = libres
      .filter(v => _familleDeVoix(v.id) === cle)
      .sort((a, b) => (a.name || '').localeCompare(b.name || '', 'fr'));
    if (!duMoteur.length) return;
    const titre = document.createElement('li');
    titre.className = 'cast-group';
    // Le nom ET son icone (« 🎎 Kokoro · 12 ») : ici il y a la place, et l'icone
    // fait le lien avec les libelles des voix, ou elle est seule (20/09/2026).
    titre.textContent = ((icone || '') ? icone + ' ' : '') + libelle
      + ' \u00b7 ' + duMoteur.length;
    list.appendChild(titre);
    duMoteur.forEach(v => {
      const li = document.createElement('li');
      li.className = 'cast-voix-libre';
      const nom = document.createElement('span');
      nom.className = 'cast-voix-libre-nom';
      nom.textContent = (typeof _libelleVoix === 'function')
        ? _libelleVoix(v) : v.name + ' \u2014 ' + v.region;
      const actions = document.createElement('div');
      actions.className = 'cast-voix-libre-actions';
      const play = document.createElement('button');
      play.type = 'button';
      play.className = 'cast-play-btn';
      play.textContent = '\u25B6\uFE0F';
      play.title = 'Écouter un aperçu de cette voix';
      play.addEventListener('click', () => _previewVoixLibre(v.id, v.name, play));
      actions.appendChild(play);
      if (typeof choisir === 'function') {
        const ok = document.createElement('button');
        ok.type = 'button';
        ok.className = 'cast-voix-libre-choisir';
        ok.textContent = 'Choisir';
        ok.title = 'Donner cette voix au personnage';
        ok.addEventListener('click', () => choisir(v));
        actions.appendChild(ok);
      }
      li.appendChild(nom);
      li.appendChild(actions);
      list.appendChild(li);
    });
  });
}

// Apercu d'une voix LIBRE : comme pour un personnage, on ne fait dire qu'un mot
// (le prenom de la voix) -- c'est assez pour reconnaitre un timbre, et court,
// donc rapide meme sur un moteur lourd.
function _previewVoixLibre(voiceId, nom, btn) {
  return _previewCharacterVoice(nom || voiceId, voiceId, '+0%', '+0Hz', btn);
}

// --- Fenetre « Voix libres pour <nom> » (19/09/2026) ---
// Le pendant du tiroir : au lieu de partir d'une voix et de chercher QUI la
// prendra (parmi 175 personnages, ce qui est justement le probleme qu'on veut
// eviter), on part du PERSONNAGE qu'on est en train de caster et on lui choisit
// une voix encore libre. Meme liste, meme ▶, donc rien de nouveau a apprendre.
async function _ouvrirVoixLibres(nom) {
  // Les voix proposees dependent des moteurs allumes : on rafraichit avant de
  // construire la liste, comme partout ailleurs dans le casting.
  await loadMoteurs();
  if (!_allVoices.length) await _chargerVoixProposees();
  if (!_catalogueVoix.length) await loadCatalogueVoix();
  const etatVoix = _etatVoixLivre();
  document.getElementById('voixlibres-titre').textContent =
    '\uD83D\uDDE3\uFE0F Voix libres pour ' + nom;
  document.getElementById('voixlibres-note').textContent = etatVoix.nbLibres
    ? etatVoix.nbLibres + ' voix que personne n\u2019utilise encore : \u25B6 '
      + 'pour écouter, « Choisir » pour la donner à ' + nom + '.'
    : '';
  const list = document.getElementById('voixlibres-list');
  list.innerHTML = '';
  _afficherVoixLibres(list, etatVoix, (v) => _donnerVoixLibre(nom, v));
  document.getElementById('voixlibres-modal').classList.remove('hidden');
}

function _fermerVoixLibres() {
  document.getElementById('voixlibres-modal').classList.add('hidden');
}

// Donne une voix libre a un personnage : sa vitesse et sa hauteur sont
// CONSERVEES (on ne passe pas par le choix Partager / Deplacer, justement parce
// que la voix est libre -- personne d'autre ne la porte).
async function _donnerVoixLibre(nom, voix) {
  const fiche = (_currentBookData.voices || {})[nom] || {};
  const ok = await _updateCharacterVoice(nom, voix.id, fiche.rate || '+0%',
                                         fiche.pitch || '+0Hz');
  const note = document.getElementById('voixlibres-note');
  if (!ok) {
    note.textContent = 'La voix n\u2019a pas pu être enregistrée : vérifiez que '
      + 'le moteur de cette voix est bien allumé.';
    return;
  }
  _fermerVoixLibres();
  await _rafraichirCastingApresChangement();
}

document.getElementById('voixlibres-close-btn')
  .addEventListener('click', _fermerVoixLibres);
document.getElementById('voixlibres-annuler-btn')
  .addEventListener('click', _fermerVoixLibres);
document.getElementById('voixlibres-modal').addEventListener('click', (e) => {
  if (e.target.id === 'voixlibres-modal') _fermerVoixLibres();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') _fermerVoixLibres();
});

// Ce que le tiroir des voix libres NE PEUT PAS montrer : les voix dont le
// moteur est eteint ne sont pas proposees (/api/voices ne sert que les voix
// ecoutables tout de suite). Sans ce message, on croirait qu'elles sont prises.
function _majInfoVoixLibres() {
  const info = document.getElementById('cast-libres-info');
  if (!info) return;
  if (_castEtatFiltre !== 'libres') { info.textContent = ''; return; }
  const compte = {};
  (_catalogueVoix || []).forEach(v => {
    if (v.dispo === false) {
      const f = v.famille || _familleDeVoix(v.id);
      compte[f] = (compte[f] || 0) + 1;
    }
  });
  // Icone + nom : ici c'est une PHRASE, il faut les deux (« 🎎 Kokoro (12 voix)
  // et 🧬 XTTS v2 (3 voix) »). Garde-fou `typeof` : ce morceau est evalue par un
  // test node qui peut ne pas fournir la table des icones.
  const noms = Object.keys(compte)
    .map(f => ((typeof _libelleFamilleIcone === 'function')
      ? _libelleFamilleIcone(f) : String(f)) + ' (' + compte[f] + ' voix)');
  info.textContent = noms.length
    ? '\u26A0\uFE0F ' + noms.join(' et ') + ' ne sont pas proposées ici : leur '
      + 'moteur est éteint (elles ne sont donc pas forcément prises).'
    : '';
}

// Recalcule l'AFFICHAGE de la fenetre du casting apres un CHANGEMENT DE VOIX
// (19/09/2026, constat de Laurent : apres avoir donne une voix libre a un
// personnage, sa fiche continuait d'annoncer « Portee par 2 personnages : ... »).
// Pourquoi c'est necessaire : les badges de partage, les groupes par voix, les
// marques « · LIBRE » des menus, le tiroir des voix libres et le resume sont
// tous calcules a l'OUVERTURE de la fenetre.
// Deux precautions :
//   - on ne recharge RIEN du serveur (ni voix, ni catalogue, ni moteurs) : la
//     fiche du personnage est deja a jour en memoire, seul l'affichage suit ;
//   - on REMET LA LISTE A SA POSITION : sur un casting de 176 personnages,
//     revenir en haut apres chaque changement serait insupportable.
// Jeton de rafraichissement : si deux voix sont changees coup sur coup, seul le
// DERNIER recalcul doit remettre la liste a sa position -- sinon une position
// perimee ferait sauter l'affichage. Meme esprit que `_ttsSession` pour la
// lecture.
let _castRefreshToken = 0;

async function _rafraichirCastingApresChangement() {
  const modal = document.getElementById('cast-modal');
  if (!modal || modal.classList.contains('hidden')) return;
  const liste = document.getElementById('cast-list');
  const position = liste ? liste.scrollTop : 0;
  const jeton = ++_castRefreshToken;
  await _openCastModal();
  if (jeton !== _castRefreshToken) return;
  const apres = document.getElementById('cast-list');
  if (apres) apres.scrollTop = position;
}

function _closeCastModal() {
  document.getElementById('cast-modal').classList.add('hidden');
  // La recherche ne survit PAS a la fermeture (20/09/2026) : on rouvre toujours
  // la fenetre sur la liste complete. Sans cela, un personnage cherche la fois
  // precedente semblerait avoir disparu du livre -- le genre de fausse alerte
  // qui coute un quart d'heure.
  _castRecherche = '';
  const champ = document.getElementById('cast-search');
  if (champ) champ.value = '';
  // Les filtres d'AGE et de GENRE non plus (21/09/2026) : meme raison -- on
  // rouvre toujours la fenetre sur la liste complete, jamais sur un filtre
  // oublie (un « jeune » resté actif ferait croire a des personnages disparus).
  _castAgeFiltre  = 'T';
  _castPersoGenre = 'T';
}

async function _updateCharacterVoice(characterName, voiceId, rate, pitch) {
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/cast/voice?user_id=' + _currentUserId,
      {
        method:  'PUT',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ character_name: characterName, voice_id: voiceId, rate: rate, pitch: pitch })
      }
    );
    if (!res.ok) throw new Error('Echec mise a jour voix');
    if (_currentBookData.voices[characterName]) {
      _currentBookData.voices[characterName].voice_id = voiceId;
      _currentBookData.voices[characterName].rate = rate;
      _currentBookData.voices[characterName].pitch = pitch;
    }

    // Le changement doit s'ENTENDRE tout de suite (constat de Laurent,
    // 15/09/2026, surtout sur mobile). La playlist de lecture et son
    // prechargement sont construits UNE FOIS au lancement et figent la voix de
    // chaque phrase : sans ce qui suit, la suite du chapitre continuait avec
    // les anciennes voix, et il fallait fermer puis rouvrir l'application.
    // Choix retenu (BACKLOG, option b) : on relance la lecture depuis la phrase
    // en cours -- simple et fiable. On ne le fait PAS quand la lecture est en
    // pause : l'utilisateur n'a pas demande a repartir, et la pause est
    // conservee (la prochaine lecture reconstruira la playlist).
    if (_ttsState === 'playing' || _ttsState === 'loading') {
      _stopTTS();
      _startTTS();
    }
    // true / false : le panneau « voix de la phrase » s'en sert pour dire si le
    // changement a bien ete enregistre (15/09/2026). Les autres appels
    // (fenetre du casting) ignorent simplement cette valeur.
    return true;
  } catch (e) {
    console.error('Erreur mise a jour voix personnage:', e);
    return false;
  }
}

async function _previewCharacterVoice(characterName, voiceId, rate, pitch, btn) {
  // Personnage sans voix dediee (petit role lu par le narrateur) : l'apercu
  // utilise alors la voix du lecteur, plutot que d'echouer.
  if (!voiceId) {
    const choix = document.getElementById('voice-select');
    voiceId = choix ? choix.value : voiceId;
  }
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = '\u23F3';
  try {
    const res = await fetch('/api/tts', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ text: characterName, voice: voiceId, rate: rate, pitch: pitch })
    });
    if (!res.ok) throw new Error('Echec apercu voix');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.addEventListener('ended', () => URL.revokeObjectURL(url));
    audio.play();
  } catch (e) {
    console.error('Erreur apercu voix personnage:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

// ============================================================
// ECOUTER LES VOIX (listener) -- session du 14/09/2026
// ============================================================
// Une fenetre qui liste TOUTES les voix ecoutables tout de suite (la liste
// vient de /api/voices : celles d'un moteur eteint en sont deja exclues),
// avec un bouton d'ecoute sur chacune et de quoi la noter (genre, etoiles,
// remarque). Les notes restent sur l'ordinateur : c'est ce qui remplace les
// lots d'ecoute par fichiers utilises jusqu'ici.

// Phrase IDENTIQUE pour toutes les voix : c'est ce qui rend la comparaison
// juste. Elle contient des pieges utiles (nombres, noms propres, accents,
// liaisons) et sert deja aux lots d'ecoute du projet.
const PHRASE_ECOUTE = 'Le 24 février 1815, la vigie de Notre-Dame de la Garde '
  + 'signala le trois-mâts le Pharaon, venant de Smyrne, Trieste et Naples.';

// Les moteurs de voix, dans l'ordre d'affichage. Troisieme element : leur
// ICONE (20/09/2026, demande de Laurent : « trouver des icones pour les
// moteurs, histoire d'avoir un visuel sur les moteurs plutot que les noms »).
// UNE SEULE LISTE : on change une icone ici, et elle change partout (libelles
// des voix, fenetre « Ecouter les voix », tiroir des voix libres, bouton des
// moteurs). Aucune marque, aucun logo sous licence : des reperes VISIBLES et
// distincts, choisis pour dire quelque chose du moteur :
//   - Edge est le seul moteur EN LIGNE  -> le nuage ;
//   - Kokoro est un modele japonais     -> la poupee japonaise ;
//   - Piper (le joueur de flute)        -> la note de musique ;
//   - Kyutai est le moteur LOCAL rapide -> l'eclair ;
//   - XTTS v2 est le moteur de CLONAGE  -> la molecule ;
//   - NeuTTS est le plus RECENT         -> la fiole.
//   - Pocket TTS tient dans la poche    -> le sac a dos (21/09/2026).
const FAMILLES_VOIX = [
  ['edge',   'Edge (en ligne)', '\u2601\uFE0F'],
  ['kokoro', 'Kokoro',          '\uD83C\uDF8E'],
  ['piper',  'Piper',           '\uD83C\uDFB6'],
  ['kyutai', 'Kyutai',          '\u26A1\uFE0F'],
  ['xtts',   'XTTS v2',         '\uD83E\uDDEC'],
  ['neutts', 'NeuTTS',          '\uD83E\uDDEA'],
  ['pocket', 'Pocket TTS',      '\uD83C\uDF92'],
];

let _annotationsVoix = {};                       // { voiceId: {genre, stars, note} }
let _criteresVoix   = [];                        // listes FERMEES (voir /api/annotations_voix/criteres)
let _ecouteurFiltre = { recherche: '', famille: 'T' };
let _ecouteurAudio = null;                       // l'audio en cours d'ecoute

// Les voix Edge n'ont aucun prefixe : c'est la famille par defaut.
function _familleDeVoix(id) {
  const p = (id || '').split(':')[0];
  return FAMILLES_VOIX.some(f => f[0] === p) ? p : 'edge';
}

function _libelleFamille(cle) {
  const trouve = FAMILLES_VOIX.find(f => f[0] === cle);
  return trouve ? trouve[1] : cle;
}

// Icone d'un moteur (« \u2601\uFE0F » pour Edge), ou '' quand la famille est
// inconnue -- jamais un caractere de remplacement. Fonction PURE : extraite du
// fichier reel par test_voix/test_libelle_voix.js.
function _iconeFamille(cle) {
  const trouve = FAMILLES_VOIX.find(f => f[0] === cle);
  return (trouve && trouve[2]) ? trouve[2] : '';
}

// Libelle d'un moteur AVEC son icone (« \uD83C\uDF8E Kokoro ») : pour les
// endroits ou il y a la place de garder le nom -- en-tete de groupe du tiroir,
// ligne d'une voix dans « Ecouter les voix », menu de filtre des moteurs,
// fenetre de choix du moteur. Dans les menus ETROITS (le libelle d'une voix du
// casting), c'est l'icone SEULE qui sert : le nom y prenait la moitie de la
// ligne, et c'est justement ce que Laurent voulait remplacer.
function _libelleFamilleIcone(cle) {
  const icone = _iconeFamille(cle);
  const nom   = _libelleFamille(cle);
  return icone ? icone + ' ' + nom : nom;
}

async function _chargerAnnotationsVoix() {
  try {
    const res = await fetch('/api/annotations_voix');
    if (res.ok) _annotationsVoix = (await res.json()) || {};
  } catch (e) {
    console.error('Erreur chargement annotations voix:', e);
    _annotationsVoix = {};
  }
}

// Les criteres fixes d'annotation (age, timbre, debit, accent, registre, role)
// viennent du SERVEUR : une seule liste a maintenir (main.py, CRITERES_VOIX),
// donc les menus du lecteur ne peuvent pas deriver de ce que le serveur accepte.
async function _chargerCriteresVoix() {
  try {
    const res = await fetch('/api/annotations_voix/criteres');
    if (res.ok) _criteresVoix = (await res.json()) || [];
  } catch (e) {
    console.error('Erreur chargement criteres voix:', e);
    _criteresVoix = [];
  }
}

// Enregistre l'etat COMPLET d'une ligne (tous les champs d'un coup) : plus simple
// et plus sur qu'un enregistrement champ par champ.
async function _sauverAnnotationVoix(voiceId, ligne) {
  const corps = {
    voice_id: voiceId,
    genre:    ligne.querySelector('.voice-genre').value,
    stars:    parseInt(ligne.querySelector('.voice-stars').value, 10),
    note:     ligne.querySelector('.voice-note').value,
  };
  // Les criteres fixes : un menu deroulant par critere (classe .voice-critere,
  // avec son critere dans data-critere). Une valeur vide = non renseigne.
  ligne.querySelectorAll('.voice-critere').forEach(sel => {
    corps[sel.dataset.critere] = sel.value;
  });
  try {
    const res = await fetch('/api/annotations_voix', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(corps),
    });
    if (!res.ok) throw new Error('Echec enregistrement annotation');
    const data = await res.json();
    _annotationsVoix = data.annotations || {};
    ligne.classList.toggle('voice-row-annotee',
      !!_annotationsVoix[voiceId]);
    _majRecapEcouteur();
  } catch (e) {
    console.error('Erreur enregistrement annotation voix:', e);
  }
}

// Ecoute une voix avec la phrase de reference. On coupe la precedente : sinon
// deux voix se superposeraient si Laurent en lance une autre pendant l'ecoute.
async function _ecouterVoix(voiceId, btn) {
  if (_ecouteurAudio) {
    _ecouteurAudio.pause();
    _ecouteurAudio = null;
  }
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = '\u23F3';
  try {
    const res = await fetch('/api/tts', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ text: PHRASE_ECOUTE, voice: voiceId,
                                rate: '+0%', pitch: '+0Hz' })
    });
    if (!res.ok) throw new Error('Echec ecoute voix');
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const audio = new Audio(url);
    _ecouteurAudio = audio;
    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(url);
      if (_ecouteurAudio === audio) _ecouteurAudio = null;
    });
    audio.play();
  } catch (e) {
    console.error('Erreur ecoute voix:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

function _listeOptions(select, valeurs, valeurChoisie) {
  valeurs.forEach(([valeur, texte]) => {
    const option = document.createElement('option');
    option.value = valeur;
    option.textContent = texte;
    select.appendChild(option);
  });
  select.value = valeurChoisie;
}

// Un critere renseigne se voit d'un coup d'oeil (bordure accentuee) : sans
// cela, six menus ou presque tous affichent leur libelle se ressemblent.
function _majStyleCritere(sel) {
  if (sel.value) sel.classList.add('renseigne');
  else sel.classList.remove('renseigne');
}

// Une ligne de l'ecouteur : bouton d'ecoute, identite de la voix, puis les
// notes rapides (genre, etoiles, remarque) et, sur une seconde ligne, les
// criteres fixes (age, timbre, debit, accent, registre, role).
// Nom COURT d'une rubrique de critere, ecrit DEVANT son menu (item du BACKLOG
// du 19/09/2026, demande de Laurent : « une fois une valeur choisie, la ligne
// affiche "adulte" ou "aigu" sans dire de quelle rubrique il s'agit »).
// Fonction PURE (aucun DOM, aucun appel reseau) : verifiee par
// test_voix/test_criteres_voix.js, qui l'extrait du fichier reel.
// Pourquoi court : six menus doivent tenir sur la ligne d'un telephone.
// Le libelle COMPLET du serveur reste dans l'infobulle du menu, et une
// rubrique INCONNUE (ajoutee plus tard cote serveur) retombe dessus -- jamais
// d'etiquette vide, jamais un menu sans nom.
const _LIBELLES_COURTS_CRITERES = {
  age: '\u00C2ge', timbre: 'Timbre', debit: 'D\u00E9bit',
  accent: 'Accent', registre: 'Registre', role: 'R\u00F4le',
};

function _libelleCourtCritere(critere) {
  const c = critere || {};
  return _LIBELLES_COURTS_CRITERES[c.cle] || c.libelle || c.cle || '';
}

function _construireLigneVoix(voix) {
  const li = document.createElement('li');
  li.className = 'voice-row';
  li.dataset.famille  = _familleDeVoix(voix.id);
  li.dataset.recherche = ((voix.name || '') + ' ' + (voix.region || '')).toLowerCase();

  const annot = _annotationsVoix[voix.id] || {};
  if (_annotationsVoix[voix.id]) li.classList.add('voice-row-annotee');

  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'voice-play-btn';
  btn.textContent = '\u25B6';
  btn.title = 'Ecouter cette voix (phrase de reference)';
  btn.addEventListener('click', () => _ecouterVoix(voix.id, btn));

  const info = document.createElement('div');
  info.className = 'voice-info';
  const nom = document.createElement('span');
  nom.className = 'voice-name';
  nom.textContent = voix.name || voix.id;
  const meta = document.createElement('span');
  meta.className = 'voice-meta';
  // Icone du moteur PUIS son nom : cette deuxieme ligne est la fiche d'identite
  // de la voix, il y a la place (20/09/2026). Sans icone (famille inconnue), le
  // nom seul suffit -- jamais de trou dans le libelle.
  const famille = _familleDeVoix(voix.id);
  meta.textContent = ((typeof _libelleFamilleIcone === 'function')
    ? _libelleFamilleIcone(famille) : _libelleFamille(famille))
    + ' \u00b7 ' + (voix.region || '');
  info.appendChild(nom);
  info.appendChild(meta);

  const notes = document.createElement('div');
  notes.className = 'voice-notes';

  const genre = document.createElement('select');
  genre.className = 'voice-genre';
  genre.title = 'Genre entendu (H = homme, F = femme)';
  // Le catalogue ecrit M pour masculin : on affiche H, la convention de
  // l'ecoute et du casting (H/F).
  const genreCatalogue = (voix.gender === 'M') ? 'H' : (voix.gender || '');
  _listeOptions(genre, [['', '\u2013'], ['H', 'H'], ['F', 'F']],
                annot.genre || genreCatalogue);

  const etoiles = document.createElement('select');
  etoiles.className = 'voice-stars';
  etoiles.title = 'Note (3 = excellente, 0 = a ecarter)';
  const etoileCatalogue = (typeof voix.stars === 'number') ? voix.stars : -1;
  _listeOptions(etoiles,
                [['-1', '\u2013'], ['0', '\u2606'], ['1', '\u2605'],
                 ['2', '\u2605\u2605'], ['3', '\u2605\u2605\u2605']],
                String((annot.stars !== undefined && annot.stars >= 0)
                       ? annot.stars : etoileCatalogue));

  const remarque = document.createElement('input');
  remarque.type = 'text';
  remarque.className = 'voice-note';
  remarque.placeholder = 'remarque';
  remarque.title = 'Remarque libre (accent, defaut entendu...)';
  remarque.value = annot.note || '';

  // Criteres FIXES (demande de Laurent, 16/09/2026) : une 2e ligne de menus
  // deroulants, sous les notes. On SELECTIONNE au lieu de noter, et les listes
  // viennent du serveur : les annotations sont donc calibrees, et
  // l'attribution automatique des voix pourra les lire plus tard.
  const criteres = document.createElement('div');
  criteres.className = 'voice-criteres';
  const champsCriteres = [];
  _criteresVoix.forEach(critere => {
    const sel = document.createElement('select');
    sel.className = 'voice-critere';
    sel.dataset.critere = critere.cle;
    sel.title = critere.libelle;
    // Etat vide : un simple tiret, comme les menus « genre » et « etoiles ».
    // AVANT le 20/09/2026, c'etait le LIBELLE de la rubrique -- et c'est
    // exactement ce qui posait probleme : il n'apparaissait que tant que rien
    // n'etait choisi, donc le nom de la rubrique disparaissait des la premiere
    // valeur selectionnee (constat de Laurent, 19/09/2026).
    const options = [['', '\u2013']];
    (critere.valeurs || []).forEach(v => options.push([v.valeur, v.libelle]));
    _listeOptions(sel, options, annot[critere.cle] || '');
    _majStyleCritere(sel);
    sel.addEventListener('change', () => {
      _majStyleCritere(sel);
      _sauverAnnotationVoix(voix.id, li);
    });
    champsCriteres.push(sel);
    // Le nom de la rubrique est maintenant ECRIT, une fois pour toutes,
    // DEVANT son menu : « Âge [– ] », « Timbre [grave] ». L'etiquette et son
    // menu vivent dans le meme petit groupe, pour qu'un passage a la ligne sur
    // telephone ne les separe jamais.
    const champ = document.createElement('span');
    champ.className = 'voice-critere-champ';
    const etiquette = document.createElement('span');
    etiquette.className = 'voice-critere-label';
    etiquette.textContent = _libelleCourtCritere(critere);
    champ.appendChild(etiquette);
    champ.appendChild(sel);
    criteres.appendChild(champ);
  });

  // On n'enregistre qu'a la sortie du champ : eviter un appel reseau a chaque
  // frappe. Les listes deroulantes, elles, partent tout de suite.
  [genre, etoiles].forEach(champ => champ.addEventListener('change',
    () => _sauverAnnotationVoix(voix.id, li)));
  [remarque].forEach(champ => champ.addEventListener('change',
    () => _sauverAnnotationVoix(voix.id, li)));

  notes.appendChild(genre);
  notes.appendChild(etoiles);
  notes.appendChild(remarque);

  li.appendChild(btn);
  li.appendChild(info);
  li.appendChild(notes);
  if (champsCriteres.length) li.appendChild(criteres);
  return li;
}

function _majRecapEcouteur() {
  const recap = document.getElementById('voices-recap');
  if (!recap) return;
  const affichees = document.querySelectorAll('#voices-list .voice-row').length;
  const annotees  = Object.keys(_annotationsVoix).length;
  recap.textContent = affichees + ' voix'
    + (annotees ? ' \u00b7 ' + annotees + ' annot\u00e9e(s)' : '');
}

function _rafraichirEcouteurVoix() {
  const list = document.getElementById('voices-list');
  if (!list) return;
  list.innerHTML = '';
  const recherche = _ecouteurFiltre.recherche.trim().toLowerCase();
  const famille   = _ecouteurFiltre.famille;

  const retenues = _allVoices.filter(v => {
    if (famille !== 'T' && _familleDeVoix(v.id) !== famille) return false;
    if (recherche) {
      const cible = ((v.name || '') + ' ' + (v.region || '')).toLowerCase();
      if (!cible.includes(recherche)) return false;
    }
    return true;
  });

  if (retenues.length === 0) {
    const vide = document.createElement('li');
    vide.className = 'cast-empty';
    vide.textContent = 'Aucune voix ne correspond.';
    list.appendChild(vide);
  } else {
    // Groupe par moteur : les familles dans l'ordre, comme les menus.
    FAMILLES_VOIX.forEach(([cle, libelle]) => {
      const duGroupe = retenues.filter(v => _familleDeVoix(v.id) === cle);
      if (!duGroupe.length) return;
      const titre = document.createElement('li');
      titre.className = 'voice-group';
      titre.textContent = libelle + ' \u00b7 ' + duGroupe.length;
      list.appendChild(titre);
      duGroupe.forEach(v => list.appendChild(_construireLigneVoix(v)));
    });
  }
  _majRecapEcouteur();
}

async function _ouvrirEcouteurVoix() {
  // Les voix proposees dependent des moteurs allumes : on rafraichit AVANT de
  // construire la liste (le moteur a pu etre eteint ou demarre entre-temps).
  await loadMoteurs();
  // `loadVoices` charge aussi les annotations d'ecoute et les criteres : les
  // libelles de voix les affichent depuis le 19/09/2026.
  await loadVoices();

  _ecouteurFiltre.recherche = '';
  _ecouteurFiltre.famille   = 'T';
  const champ  = document.getElementById('voices-search');
  if (champ) champ.value = '';
  const select = document.getElementById('voices-famille');
  if (select) select.value = 'T';

  _rafraichirEcouteurVoix();
  document.getElementById('voices-modal').classList.remove('hidden');
}

function _fermerEcouteurVoix() {
  // On coupe l'ecoute en cours : rien ne doit continuer en arriere-plan.
  if (_ecouteurAudio) {
    _ecouteurAudio.pause();
    _ecouteurAudio = null;
  }
  document.getElementById('voices-modal').classList.add('hidden');
}

// Verrouille / deverrouille la voix d'un personnage (case "garder").
// Un personnage verrouille conserve sa voix lors d'un re-cast.
async function _toggleCharacterLock(characterName, btn) {
  const v = (_currentBookData && _currentBookData.voices)
    ? _currentBookData.voices[characterName] : null;
  const newLocked = !(v && v.locked);

  btn.disabled = true;
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/cast/lock?user_id=' + _currentUserId,
      {
        method:  'PUT',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ character_name: characterName, locked: newLocked })
      }
    );
    if (!res.ok) throw new Error('Echec verrouillage');
    if (v) v.locked = newLocked ? 1 : 0;
    btn.classList.toggle('locked', newLocked);
    btn.textContent = newLocked ? '\uD83D\uDD12' : '\uD83D\uDD13';
    btn.title = newLocked
      ? 'Voix verrouillee : elle sera conservee lors du re-cast.'
      : 'Verrouiller cette voix pour la conserver lors du re-cast.';
  } catch (e) {
    console.error('Erreur verrouillage voix personnage:', e);
  } finally {
    btn.disabled = false;
  }
}

// Re-cast GRATUIT : redistribue les voix non verrouillees dans le catalogue
// courant (nouvelles voix incluses), sans aucun appel IA. Le pitch et la
// vitesse existants sont conserves, seule la voix change.
async function _recasterLivre() {
  const voices = (_currentBookData && _currentBookData.voices) || {};
  const verrouilles = Object.keys(voices).filter(n => voices[n].locked);

  let msg = 'Re-caster ce livre ?\n\n';
  msg += 'Toutes les voix NON verrouillees (\uD83D\uDD13) seront redistribuees '
       + 'dans le catalogue actuel (nouvelles voix incluses).\n';
  if (verrouilles.length > 0) {
    msg += '\nVoix conservees (' + verrouilles.length + ') : ' + verrouilles.join(', ') + '\n';
  } else {
    msg += '\nAucune voix verrouillee : TOUS les personnages changeront de voix.\n';
  }
  msg += '\nC\'est gratuit (aucun appel IA). La vitesse et la hauteur ne changent pas.';
  if (!confirm(msg)) return;

  const btn = document.getElementById('cast-recast-btn');
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Re-cast en cours...';
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/cast/reassign?user_id=' + _currentUserId,
      { method: 'POST' }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Echec re-cast');
    }
    const data = await res.json();

    // Recharge le livre pour recuperer les nouvelles voix, puis reaffiche
    // la fenetre du casting a jour.
    try {
      const bookRes = await fetch('/api/books/' + _currentBookId + '?user_id=' + _currentUserId);
      if (bookRes.ok) {
        const freshBook = await bookRes.json();
        _currentBookData.voices  = freshBook.voices || {};
        _currentBookData.aliases = freshBook.aliases || {};
      }
    } catch (e) {
      console.error('Erreur rechargement voix du livre:', e);
    }
    _openCastModal(true);
    alert('Re-cast termine : ' + data.modifies + ' voix redistribuees, '
          + data.gardes + ' conservee(s).');
  } catch (e) {
    console.error('Erreur re-cast:', e);
    alert('Impossible de re-caster : ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

// Re-cast AVEC l'IA (etape 2, 16/09/2026) : le second bouton, a cote du gratuit.
// L'IA lit quelques repliques de chaque personnage et en deduit ce qu'aucune
// table ne contient (position sociale, registre de langue, parler etranger,
// temperament), puis choisit la voix dont la DESCRIPTION correspond le mieux.
// Garde-fous : verrous et voix figees de saga respectes, petits roles non
// soumis a l'IA, et tout ce que l'IA rend d'inutilisable est ecarte (le
// personnage garde alors exactement la voix du re-cast par criteres).
async function _recasterAvecIA() {
  const voices = (_currentBookData && _currentBookData.voices) || {};
  const verrouilles = Object.keys(voices).filter(n => voices[n].locked);

  let msg = 'Re-caster ce livre AVEC l\'IA ?\n\n';
  msg += 'L\'IA lit quelques repliques de chaque personnage et en deduit sa '
       + 'position sociale, son registre de langue, s\'il parle etranger et son '
       + 'temperament : elle choisit ensuite la voix qui correspond le mieux.\n\n';
  msg += 'Quelques centimes (Gemini, le moteur par defaut). Les personnages '
       + 'verrouilles et les voix figees de saga ne bougent pas ; les petits '
       + 'roles (moins de 8 repliques) gardent leur voix actuelle.\n';
  if (verrouilles.length > 0) {
    msg += '\nVoix conservees (' + verrouilles.length + ') : '
         + verrouilles.join(', ') + '\n';
  }
  if (!confirm(msg)) return;

  const btn = document.getElementById('cast-recast-ia-btn');
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Re-cast IA en cours...';
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/cast/reassign_ia?user_id='
      + _currentUserId + '&provider=gemini',
      { method: 'POST' }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Echec du re-cast IA');
    }
    const data = await res.json();

    // Recharge le livre pour recuperer les nouvelles voix, puis reaffiche la
    // fenetre du casting a jour (meme chose que le re-cast gratuit).
    try {
      const bookRes = await fetch('/api/books/' + _currentBookId + '?user_id=' + _currentUserId);
      if (bookRes.ok) {
        const freshBook = await bookRes.json();
        _currentBookData.voices  = freshBook.voices || {};
        _currentBookData.aliases = freshBook.aliases || {};
      }
    } catch (e) {
      console.error('Erreur rechargement voix du livre:', e);
    }
    _openCastModal(true);

    let bilan = 'Re-cast IA termine : ' + data.modifies + ' voix modifiee(s), dont '
              + data.par_ia + ' choisie(s) par l\'IA, '
              + data.gardes + ' conservee(s).\n';
    bilan += '\n' + data.soumis + ' personnage(s) soumis a l\'IA ('
           + data.extraits + ' avec leurs repliques) ; '
           + data.petits_roles + ' petit(s) role(s) laisse(s) de cote.';
    if (data.chapitres_ecartes && data.chapitres_ecartes.length) {
      bilan += '\n\nChapitres ignores (decoupage inattendu) : '
             + data.chapitres_ecartes.join(', ')
             + ' -- l\'IA a decide sans leurs repliques.';
    }
    if (data.problemes && data.problemes.length) {
      bilan += '\n\nReponses ecartees de l\'IA :\n- ' + data.problemes.join('\n- ');
    }
    alert(bilan);
  } catch (e) {
    console.error('Erreur re-cast IA:', e);
    alert('Impossible de re-caster avec l\'IA : ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

// Detache un alias : le nom redevient un personnage independant (il n'a
// jamais ete supprime), avec sa propre voix.
async function _detacherAlias(aliasName) {
  const ok = confirm(
    'Detacher \u00ab ' + aliasName + ' \u00bb ?\n\n' +
    'Ce nom redevient un personnage independant, avec sa propre voix. ' +
    'Aucun nom n\'est supprime.'
  );
  if (!ok) return;
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/cast/ungroup?user_id=' + _currentUserId,
      {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ alias_name: aliasName })
      }
    );
    if (!res.ok) throw new Error('Echec detachement');
    if (_currentBookData && _currentBookData.aliases) {
      delete _currentBookData.aliases[aliasName];
    }
    _openCastModal();
  } catch (e) {
    console.error('Erreur detachement alias:', e);
    alert('Impossible de detacher : ' + e.message);
  }
}

// Rattachement manuel d'un nom a un personnage (pseudonymes). Ouvre un petit
// panneau sous la ligne : une liste deroulante (personnages les plus presents
// d'abord) + Rattacher / Annuler. Utilise pour Monte-Cristo / Edmond Dantes /
// abbe Busoni / Simbad le marin, que la regle automatique ne peut pas deviner.
function _ouvrirRattachement(nom, li) {
  // Un seul panneau ouvert a la fois.
  document.querySelectorAll('.cast-link-panel').forEach(p => p.remove());

  const voices  = (_currentBookData && _currentBookData.voices)  || {};
  const aliases = (_currentBookData && _currentBookData.aliases) || {};

  // Candidats : tous les autres personnages. On ecarte soi-meme, et ceux qui
  // sont deja rattaches a soi (ils s'affichent deja juste en dessous).
  const enfants = new Set(Object.keys(aliases).filter(al => aliases[al] === nom));
  const candidats = Object.keys(voices)
    .filter(n => n !== nom && !enfants.has(n))
    .sort((a, b) => (voices[b].line_count || 0) - (voices[a].line_count || 0));

  const panel = document.createElement('div');
  panel.className = 'cast-link-panel';

  const info = document.createElement('p');
  info.className = 'cast-link-info';
  info.textContent = '\u00ab ' + nom + ' \u00bb sera affiche sous le personnage '
    + 'choisi. Sa voix ne change pas : chaque appellation garde la sienne.';
  panel.appendChild(info);

  const select = document.createElement('select');
  select.className = 'cast-link-select';
  const vide = document.createElement('option');
  vide.value = '';
  vide.textContent = '\u2014 choisir le personnage principal \u2014';
  select.appendChild(vide);
  candidats.forEach(n => {
    const opt = document.createElement('option');
    opt.value = n;
    opt.textContent = n + '  (' + (voices[n].line_count || 0) + ' repliques)';
    select.appendChild(opt);
  });
  panel.appendChild(select);

  const actions = document.createElement('div');
  actions.className = 'cast-link-actions';

  const okBtn = document.createElement('button');
  okBtn.type = 'button';
  okBtn.className = 'cast-link-ok';
  okBtn.textContent = 'Rattacher';
  okBtn.addEventListener('click', () => {
    if (!select.value) {
      alert('Choisis d\u2019abord le personnage principal.');
      return;
    }
    _rattacherAlias(nom, select.value);
  });

  const cancelBtn = document.createElement('button');
  cancelBtn.type = 'button';
  cancelBtn.className = 'cast-link-cancel';
  cancelBtn.textContent = 'Annuler';
  cancelBtn.addEventListener('click', () => panel.remove());

  actions.appendChild(okBtn);
  actions.appendChild(cancelBtn);
  panel.appendChild(actions);

  li.appendChild(panel);
}

async function _rattacherAlias(aliasName, canonicalName) {
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/cast/group?user_id=' + _currentUserId,
      {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ alias_name: aliasName, canonical_name: canonicalName })
      }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Echec rattachement');
    }
    const bookRes = await fetch(
      '/api/books/' + _currentBookId + '?user_id=' + _currentUserId
    );
    if (bookRes.ok) {
      const fresh = await bookRes.json();
      if (_currentBookData) {
        _currentBookData.aliases = fresh.aliases || {};
        _currentBookData.voices  = fresh.voices  || {};
      }
    }
    _openCastModal();
  } catch (e) {
    console.error('Erreur rattachement alias:', e);
    alert('Impossible de rattacher : ' + e.message);
  }
}

// Regroupe les doublons d'ecriture (accents, tirets, article initial) apres
// une confirmation qui liste les regroupements proposes. Gratuit, reversible.
async function _autogrouperDoublons() {
  const btn = document.getElementById('cast-autogroup-btn');
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Analyse...';
  try {
    const url = '/api/books/' + _currentBookId + '/cast/autogroup?user_id=' + _currentUserId;

    const apercuRes = await fetch(url + '&apply=false', { method: 'POST' });
    if (!apercuRes.ok) throw new Error('Echec analyse');
    const apercu = await apercuRes.json();

    if (!apercu.count) {
      alert('Aucun doublon d\'ecriture detecte sur ce livre.');
      return;
    }

    let msg = 'Regrouper les doublons d\'ecriture detectes ?\n\n';
    apercu.groupes.forEach(g => {
      msg += '\u2022 ' + g.principal + '\n     <-- ' + g.doublons.join(', ') + '\n';
    });
    msg += '\n' + apercu.count + ' regroupement(s). Aucun nom n\'est supprime '
         + '(reversible avec le bouton \u2702). Gratuit.';
    if (!confirm(msg)) return;

    const applyRes = await fetch(url + '&apply=true', { method: 'POST' });
    if (!applyRes.ok) {
      const err = await applyRes.json().catch(() => ({}));
      throw new Error(err.detail || 'Echec regroupement');
    }
    const data = await applyRes.json();

    try {
      const bookRes = await fetch('/api/books/' + _currentBookId + '?user_id=' + _currentUserId);
      if (bookRes.ok) {
        const freshBook = await bookRes.json();
        _currentBookData.voices  = freshBook.voices || {};
        _currentBookData.aliases = freshBook.aliases || {};
      }
    } catch (e) {
      console.error('Erreur rechargement voix du livre:', e);
    }
    _openCastModal();
    alert('Regroupement termine : ' + data.alias_crees + ' alias rattaches.');
  } catch (e) {
    console.error('Erreur regroupement doublons:', e);
    alert('Impossible de regrouper : ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

document.getElementById('cast-close-btn').addEventListener('click', _closeCastModal);
document.getElementById('cast-modal').addEventListener('click', (e) => {
  if (e.target.id === 'cast-modal') _closeCastModal();
});
document.getElementById('cast-recast-btn').addEventListener('click', _recasterLivre);
document.getElementById('cast-recast-ia-btn').addEventListener('click', _recasterAvecIA);
document.getElementById('cast-autogroup-btn').addEventListener('click', _autogrouperDoublons);

// Barre de recherche du casting (20/09/2026) : on reconstruit l'affichage a
// chaque lettre tapee, mais SANS repasser par le serveur (2e argument
// `listeSeule`) : rien n'a bouge depuis l'ouverture, et une requete par lettre
// rendrait la frappe molle sur un livre a 176 personnages. Le texte est garde
// dans _castRecherche pour survivre aux reconstructions (filtre d'etat,
// changement de voix) : sans cela, il s'effacerait tout seul au premier clic.
document.getElementById('cast-search').addEventListener('input', (e) => {
  _castRecherche = e.target.value;
  _openCastModal(false, true);
});

// --- Ecouter les voix (listener, 14/09/2026) ---
document.getElementById('voices-open-btn').addEventListener('click', _ouvrirEcouteurVoix);
document.getElementById('voices-close-btn').addEventListener('click', _fermerEcouteurVoix);
document.getElementById('voices-modal').addEventListener('click', (e) => {
  if (e.target.id === 'voices-modal') _fermerEcouteurVoix();
});
document.getElementById('voices-search').addEventListener('input', (e) => {
  _ecouteurFiltre.recherche = e.target.value;
  _rafraichirEcouteurVoix();
});
document.getElementById('voices-famille').addEventListener('change', (e) => {
  _ecouteurFiltre.famille = e.target.value;
  _rafraichirEcouteurVoix();
});

// Filtre par genre des voix proposees dans le casting (Toutes / Femmes /
// Hommes) : on reconstruit la fenetre pour appliquer le filtre a tous les
// menus de voix d'un coup.
document.querySelectorAll('#cast-gender-actions button').forEach(btn => {
  btn.addEventListener('click', () => {
    _castGenreFiltre = btn.dataset.genre;
    _openCastModal();
  });
});

// --- Filtre par etat des personnages (session du 15/09/2026) ---
// Tous / a caster / voix partagee : celui-ci filtre les LIGNES de personnages
// (l'autre barre ne filtre que les voix proposees dans les menus).
document.querySelectorAll('#cast-etat-actions button').forEach(btn => {
  btn.addEventListener('click', () => {
    _castEtatFiltre = btn.dataset.etat;
    _openCastModal();
  });
});

// --- Filtre par age de la VOIX et par genre du PERSONNAGE (21/09/2026) ---
// Deux groupes de boutons dans la MEME barre : l'age annote de la voix que
// porte le personnage, et le genre de sa fiche. Comme les deux autres barres,
// chaque clic reconstruit la fenetre : les quatre filtres se combinent (etat,
// recherche, age, genre), et aucun ne touche aux badges ni aux compteurs de
// voix -- ceux-ci restent calcules sur tout le livre.
document.querySelectorAll('#cast-age-actions button').forEach(btn => {
  btn.addEventListener('click', () => {
    _castAgeFiltre = btn.dataset.age;
    _openCastModal();
  });
});

document.querySelectorAll('#cast-perso-genre-actions button').forEach(btn => {
  btn.addEventListener('click', () => {
    _castPersoGenre = btn.dataset.perso;
    _openCastModal();
  });
});

async function _loadSagaSuggestions() {
  try {
    const res = await fetch('/api/sagas?user_id=' + _currentUserId);
    if (!res.ok) return;
    const sagas = await res.json();
    const list = document.getElementById('cast-saga-list');
    list.innerHTML = '';
    sagas.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s;
      list.appendChild(opt);
    });
  } catch (e) {
    console.error('Erreur chargement sagas:', e);
  }
}

async function _saveSaga() {
  const sagaInput = document.getElementById('cast-saga-input');
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/saga?user_id=' + _currentUserId,
      {
        method:  'PUT',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ saga: sagaInput.value })
      }
    );
    if (!res.ok) throw new Error('Echec sauvegarde saga');
    const data = await res.json();
    if (_currentBookData) _currentBookData.saga = data.saga;
  } catch (e) {
    console.error('Erreur sauvegarde saga:', e);
  }
}

async function _propagateSagaCasting() {
  const btn = document.getElementById('cast-propagate-btn');
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Propagation...';
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/cast/propagate-saga?user_id=' + _currentUserId,
      { method: 'POST' }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Echec propagation');
    }
    const data = await res.json();
    alert('Casting applique a ' + data.tomes_mis_a_jour + ' autre(s) tome(s) de la saga.');
  } catch (e) {
    console.error('Erreur propagation saga:', e);
    alert("Impossible de propager : verifie qu'une saga est renseignee pour ce livre.");
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

document.getElementById('cast-saga-input').addEventListener('change', _saveSaga);
document.getElementById('cast-propagate-btn').addEventListener('click', _propagateSagaCasting);

function _updateMultivoiceBtn() {
  const btn = document.getElementById('multivoice-btn');
  if (!_currentBookData) return;

  const status = _currentBookData.cast_status || 'none';

  if (status === 'done') {
    btn.textContent = '🎭 Voix multiples actives';
    btn.disabled = false;
    btn.classList.add('active');
  } else if (status.startsWith('processing')) {
    const progress = status.split(':')[1] || '';
    btn.textContent = '🎭 ' + progress;
    btn.disabled = true;
    btn.classList.remove('active');
  } else if (status === 'error') {
    btn.textContent = '🎭 Erreur, reessayer';
    btn.disabled = false;
    btn.classList.remove('active');
  } else {
    btn.textContent = '🎭 Voix multiples';
    btn.disabled = false;
    btn.classList.remove('active');
  }
}

function _stopCastPolling() {
  if (_castPollTimer) {
    clearInterval(_castPollTimer);
    _castPollTimer = null;
  }
}

function _startCastPolling() {
  _stopCastPolling();
  _castPollTimer = setInterval(async () => {
    if (!_currentBookId) { _stopCastPolling(); return; }
    try {
      const res = await fetch(
        '/api/books/' + _currentBookId + '/cast/status?user_id=' + _currentUserId
      );
      if (!res.ok) return;
      const data = await res.json();
      _currentBookData.cast_status = data.cast_status;
      _currentBookData.multi_voice_enabled = data.multi_voice_enabled;

      if (data.cast_status === 'done') {
        try {
          const bookRes = await fetch('/api/books/' + _currentBookId + '?user_id=' + _currentUserId);
          if (bookRes.ok) {
            const freshBook = await bookRes.json();
            _currentBookData.voices  = freshBook.voices || {};
            _currentBookData.aliases = freshBook.aliases || {};
          }
        } catch (e) {
          console.error('Erreur rechargement voix du livre:', e);
        }
      }

      _updateMultivoiceBtn();
      if (data.cast_status === 'done' || data.cast_status === 'error') {
        _stopCastPolling();
      }
    } catch (e) {
      console.error('Erreur verification statut voix multiples:', e);
    }
  }, 4000);
}

async function _onMultivoiceBtnClick() {
  if (!_currentBookId) return;

  const status = (_currentBookData && _currentBookData.cast_status) || 'none';
  if (status === 'done') {
    // Ouverture de la fenetre : on recharge la liste des voix proposees et le
    // catalogue complet (un moteur a pu etre allume depuis l'affichage de la
    // page) -- voir _openCastModal().
    _openCastModal(true);
    return;
  }

  _openProviderModal();
}

async function _openProviderModal() {
  const modal = document.getElementById('provider-modal');
  modal.classList.remove('hidden');

  // Etat du moteur LOCAL avant tout le reste (route serveur, aucun appel
  // payant) : s'il est indisponible -- Ollama arrete, ou modele absent -- le
  // bouton est grise et explique pourquoi, et on ne lui demande pas
  // d'estimation. Le repli automatique des passages refuses par Google
  // utilise le meme moteur : on prefere le dire clairement des maintenant.
  let localInfo = { disponible: false, raison: '' };
  try {
    const r = await fetch('/api/llm/local');
    localInfo = await r.json();
  } catch (e) {
    console.error('Etat du moteur local indisponible:', e);
  }
  const btnLocal = document.querySelector('.provider-btn[data-provider="local"]');
  if (btnLocal && !localInfo.disponible) {
    btnLocal.disabled = true;
    const el = btnLocal.querySelector('.provider-estimate');
    if (el) el.textContent = 'indisponible : ' + (localInfo.raison || 'Ollama arrêté');
  }

  // Estimation du cout pour chaque moteur (route serveur sans appel IA :
  // decoupe des chapitres + tarifs). Affichee sous chaque bouton avant que
  // l'utilisateur ne valide le lancement.
  ['gemini', 'deepseek', 'mistral', 'local'].forEach(async (p) => {
    if (p === 'local' && !localInfo.disponible) return;
    const el = document.querySelector('.provider-btn[data-provider="' + p + '"] .provider-estimate');
    if (!el) return;
    el.textContent = 'estimation...';
    try {
      const res = await fetch(
        '/api/books/' + _currentBookId + '/cast/estimate?user_id=' + _currentUserId + '&provider=' + p
      );
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      el.textContent = data.cost_display + ' · ' + data.calls + ' appels';
    } catch (e) {
      el.textContent = 'indisponible';
    }
  });
}

function _closeProviderModal() {
  document.getElementById('provider-modal').classList.add('hidden');
}

async function _startCasting(provider) {
  _closeProviderModal();

  const btn = document.getElementById('multivoice-btn');
  btn.disabled = true;
  btn.textContent = 'Demarrage...';

  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/cast?user_id=' + _currentUserId + '&provider=' + provider,
      { method: 'POST' }
    );
    if (!res.ok) {
      // Le serveur explique precisement pourquoi il refuse (traitement deja
      // en cours, chapitre impossible a analyser...) : on affiche SON message
      // plutot qu'un "Echec du demarrage" muet (session du 13/09/2026).
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || ('Echec du demarrage (HTTP ' + res.status + ')'));
    }
    const data = await res.json();
    _currentBookData.cast_status = data.cast_status;
    _currentBookData.multi_voice_enabled = true;
    _updateMultivoiceBtn();
    _startCastPolling();
  } catch (e) {
    console.error('Erreur demarrage voix multiples:', e);
    _currentBookData.cast_status = 'error';
    _updateMultivoiceBtn();
    alert(e.message || "Impossible de demarrer l'analyse voix multiples.");
  }
}

document.querySelectorAll('.provider-btn').forEach(btn => {
  btn.addEventListener('click', () => _startCasting(btn.dataset.provider));
});
document.getElementById('provider-cancel-btn').addEventListener('click', _closeProviderModal);
document.getElementById('provider-modal').addEventListener('click', (e) => {
  if (e.target.id === 'provider-modal') _closeProviderModal();
});

// ============================================================
// CHARGEMENT CHAPITRE
// ============================================================

// Nombre d'essais de chargement d'un chapitre, et pause entre deux essais.
// Pourquoi (constat de Laurent, 18/09/2026) : « parfois le chapitre ne se charge
// pas correctement, et zappe complètement un chapitre : il passe du
// quatre-vingt-un au quatre-vingt-trois, surtout après une erreur de
// chargement ». Un échec de chargement est presque toujours PASSAGER (serveur
// occupé à préparer une voix, réseau qui vacille) : on retente avant d'abandonner.
const CHARGEMENT_ESSAIS   = 3;
const CHARGEMENT_PAUSE_MS = 1200;

// Demande UN chapitre au serveur. Renvoie null si c'est impossible (réseau,
// serveur, chapitre introuvable) : l'appelant décide quoi faire, et surtout
// n'écrit RIEN dans l'état du lecteur avant d'avoir le chapitre en main.
async function _demanderChapitre(index) {
  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/chapter/' + index + '?user_id=' + _currentUserId
    );
    if (!res.ok) {
      console.error('Chapitre ' + (index + 1) + ' : réponse du serveur ' + res.status);
      return null;
    }
    return await res.json();
  } catch (e) {
    console.error('Chapitre ' + (index + 1) + ' : réseau indisponible', e);
    return null;
  }
}

// Affiche l'échec de chargement, avec un bouton pour recommencer TOUT DE SUITE.
// Les phrases du chapitre précédent sont VIDÉES : sans cela, appuyer sur
// « lecture » rejouait l'ancien chapitre, et à sa fin le lecteur passait au
// chapitre SUIVANT — c'est ainsi qu'un chapitre disparaissait de l'écoute.
function _afficherEchecChapitre(content, index, scrollTo, cursorTo, autoPlay) {
  _sentences       = [];
  _paragraphStarts = [];
  _cursorIdx       = 0;

  content.innerHTML = '';
  const message = document.createElement('p');
  message.style.color = 'var(--text-muted)';
  message.textContent = 'Le chapitre ' + (index + 1) + " n'a pas pu se charger. "
    + "Rien n'est perdu : réessaie, ou passe par le sommaire.";
  const bouton = document.createElement('button');
  bouton.className   = 'chapter-retry-btn';
  bouton.textContent = 'Réessayer ce chapitre';
  bouton.addEventListener('click',
    () => loadChapter(index, scrollTo, cursorTo, autoPlay));
  content.appendChild(message);
  content.appendChild(bouton);
}

async function loadChapter(index, scrollTo, cursorTo = 0, autoPlay = false) {
  _stopTTS();
  // Les phrases du nouveau chapitre ont d'autres index : un panneau « voix de
  // la phrase » reste ouvert pointerait sur la mauvaise phrase (15/09/2026).
  _closeVoicePanel();
  if (index < 0 || index >= _totalChapters) return false;

  const content = document.getElementById('reader-content');
  content.innerHTML = '<p style="color:var(--text-muted)">Chargement...</p>';

  // --- Le chapitre est DEMANDÉ avant que quoi que ce soit ne change ---------
  // `_currentChapter` et les phrases en mémoire ne bougent qu'une fois le
  // chapitre REÇU. Avant le 18/09/2026, le compteur était posé avant la
  // requête : une erreur laissait le lecteur sur le chapitre raté, gardait les
  // phrases de l'ancien chapitre, et l'enchaînement automatique sautait le
  // chapitre manquant.
  let data = null;
  for (let essai = 1; essai <= CHARGEMENT_ESSAIS; essai++) {
    data = await _demanderChapitre(index);
    if (data) break;
    if (essai < CHARGEMENT_ESSAIS) await _pause(CHARGEMENT_PAUSE_MS);
  }

  if (!data) {
    _afficherEchecChapitre(content, index, scrollTo, cursorTo, autoPlay);
    return false;
  }

  // --- Chargement RÉUSSI : c'est seulement ici que le chapitre change ------
  _currentChapter = index;
  _chapterSpeakers = data.speakers || {};
  renderChapterContent(data.text || '');
  content.scrollTop = scrollTo || 0;

  document.getElementById('chapter-title-display').textContent = data.title || '';
  document.getElementById('chapter-counter').textContent =
    (index + 1) + ' / ' + _totalChapters;

  document.getElementById('prev-btn').disabled = (index === 0);
  document.getElementById('next-btn').disabled = (index === _totalChapters - 1);

  document.querySelectorAll('.chapter-item').forEach((el, i) => {
    el.classList.toggle('active', i === index);
  });

  if (_sentences.length > 0) _setCursor(cursorTo);

  if (autoPlay) _startTTS();
  saveProgress();
  return true;
}

// ============================================================
// DÉCOUPAGE & RENDU DU CHAPITRE
// ============================================================

// Abréviations françaises après lesquelles un point ne finit JAMAIS une phrase :
// c'est une civilité, le nom qui suit fait partie de la même phrase.
// DOIT rester identique à `ABREVIATIONS` dans modules/decoupage.py — le test
// test_voix/test_decoupage_phrases.py compare les deux fichiers.
const ABREVIATIONS_SANS_FIN = ['M', 'MM', 'Mme', 'Mmes', 'Mlle', 'Mlles', 'Mgr',
                               'Dr', 'Pr', 'St', 'Ste', 'Mr', 'Mx', 'Mrs',
                               'MR', 'MRS', 'MME', 'MMES', 'MLLE', 'MLLES',
                               'MGR', 'DR', 'PR'];
// Celles qui s'écrivent sans point mais ne finissent pas une phrase non plus.
const ABREVIATIONS_SANS_POINT = ['Mme', 'Mmes', 'Mlle', 'Mlles', 'Mgr'];

// Le dernier mot de ce morceau est-il une abréviation de civilité ?
function _finitParAbreviation(morceau) {
  const mots = (morceau || '').split(/\s+/).filter(m => m);
  if (!mots.length) return false;
  let dernier = mots[mots.length - 1].replace(/^[«»"()]+/, '');
  dernier = dernier.replace(/[»"]+$/, '');
  const sansPoint = dernier.replace(/\.+$/, '');
  if (ABREVIATIONS_SANS_FIN.indexOf(sansPoint) === -1) return false;
  return dernier.endsWith('.') || ABREVIATIONS_SANS_POINT.indexOf(sansPoint) !== -1;
}

function _buildSentences(text) {
  const paras    = text.split(/\n\n+/).map(p => p.trim()).filter(p => p.length > 5);
  const sentences    = [];
  const paraStarts   = [];

  paras.forEach((para, paraIdx) => {
    paraStarts.push(sentences.length);
    // Découpe aux fins de phrases (ponctuation conservée), puis RECOLLE les
    // morceaux coupés après une abréviation : « … complimenter M. » et
    // « de Morcerf ; … » sont UNE phrase. C'était la cause du silence entendu
    // après « monsieur » (constat de Laurent, 18/09/2026) — et le fait de
    // recoller décale les index, ce qui a demandé de migrer la base
    // (test_voix/_migrer_index_phrases.py).
    const rawSents = para.split(/(?<=[.!?…»])\s+/);
    let courant = '';
    rawSents.forEach(s => {
      s = s.trim();
      if (!s) return;
      courant = courant ? courant + ' ' + s : s;
      if (!_finitParAbreviation(courant)) {
        if (courant.length > 3) sentences.push({ text: courant, paraIdx });
        courant = '';
      }
    });
    if (courant.length > 3) sentences.push({ text: courant, paraIdx });
  });

  return { sentences, paraStarts };
}

function renderChapterContent(text) {
  const { sentences, paraStarts } = _buildSentences(text);
  _sentences       = sentences;
  _paragraphStarts = paraStarts;
  _cursorIdx       = 0;

  const content = document.getElementById('reader-content');
  content.innerHTML = '';

  let currentPara = -1;
  let pEl = null;

  sentences.forEach((s, idx) => {
    if (s.paraIdx !== currentPara) {
      pEl = document.createElement('p');
      content.appendChild(pEl);
      currentPara = s.paraIdx;
    }
    const span = document.createElement('span');
    span.className   = 'sentence-span';
    span.dataset.idx = idx;
    span.textContent = s.text + ' ';
    pEl.appendChild(span);
  });
}

// ============================================================
// CURSEUR GLITCH
// ============================================================

function _glitchLoop(ts) {
  if (!_glitchEl || !_glitchActive) return;
  _glitchRAF = requestAnimationFrame(_glitchLoop);
  if (ts < _glitchNextAt) return;

  if (Math.random() < 0.15) {
    const dx   = (Math.random() - 0.5) * 10;
    const dy   = (Math.random() - 0.5) * 4;
    const swap = Math.random() > 0.5;
    const c1   = swap ? '#ff0040' : '#00e5ff';
    const c2   = swap ? '#00e5ff' : '#ff0040';
    _glitchEl.style.transform  = `translate(${dx}px,${dy}px)`;
    _glitchEl.style.textShadow = `${-dx}px 0 ${c1},${dx}px 0 ${c2}`;
    _glitchEl.style.color      = '#fff';
    _glitchEl.style.filter     = 'blur(0.4px)';
    _glitchNextAt = ts + 40 + Math.random() * 80;
  } else {
    _glitchEl.style.transform  = '';
    _glitchEl.style.textShadow = '';
    _glitchEl.style.color      = 'var(--accent)';
    _glitchEl.style.filter     = '';
    _glitchNextAt = ts + 100 + Math.random() * 500;
  }
}

function _startGlitch(el) {
  _stopGlitch();
  _glitchEl     = el;
  _glitchActive = true;
  _glitchNextAt = 0;
  _glitchRAF    = requestAnimationFrame(_glitchLoop);
}

function _stopGlitch() {
  _glitchActive = false;
  if (_glitchRAF) { cancelAnimationFrame(_glitchRAF); _glitchRAF = null; }
  if (_glitchEl) {
    _glitchEl.style.transform  = '';
    _glitchEl.style.textShadow = '';
    _glitchEl.style.color      = '';
    _glitchEl.style.filter     = '';
    _glitchEl = null;
  }
}

function _setCursor(idx) {
  if (idx < 0 || idx >= _sentences.length) return;
  document.querySelectorAll('.glitch-active').forEach(
    el => el.classList.remove('glitch-active')
  );
  _stopGlitch();
  const span = document.querySelector('[data-idx="' + idx + '"]');
  if (span) {
    span.classList.add('glitch-active');
    _startGlitch(span);
    span.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
  _cursorIdx = idx;
  _updateTimeRemaining();
  clearTimeout(_progressTimer);
  _progressTimer = setTimeout(saveProgress, 3000);
}

// --- Navigation paragraphe (et le saut MOYEN de la barre) ---
// Decision de Laurent, 20/09/2026 : « le saut de paragraphe correspond tres
// souvent a un saut de phrase » -- donc sauter UN paragraphe ne se distinguait
// pas d'un saut de phrase. La barre a maintenant TROIS niveaux de saut, et les
// boutons ⏪ / ⏩ (DEUX triangles) sautent plusieurs paragraphes d'un coup.
// Une seule ligne a changer pour ajuster le pas.
const _PAS_PARAGRAPHES = 4;

function _cursorParaNext(pas) {
  const n       = Math.max(1, pas || 1);
  const suivant = _paragraphStarts.find(s => s > _cursorIdx);
  if (suivant === undefined) return;          // deja au dernier paragraphe
  // On part du paragraphe SUIVANT, puis on avance encore (n - 1) -- borne au
  // dernier paragraphe, on ne depasse jamais la fin du chapitre.
  const cible = _paragraphStarts[
    Math.min(_paragraphStarts.indexOf(suivant) + (n - 1),
             _paragraphStarts.length - 1)];
  _setCursor(cible);
  if (_ttsState === 'playing') _abortAndRestart();
}

function _cursorParaPrev(pas) {
  const n          = Math.max(1, pas || 1);
  const cur        = [..._paragraphStarts].reverse().find(s => s <= _cursorIdx) ?? 0;
  const curParaIdx = _paragraphStarts.indexOf(cur);
  // Regle d'origine conservee : le curseur est DANS un paragraphe -> on recule a
  // son DEBUT ; il est pile sur un debut -> on recule d'un paragraphe.
  const base       = (cur < _cursorIdx) ? curParaIdx : Math.max(0, curParaIdx - 1);
  const cible      = _paragraphStarts[Math.max(0, base - (n - 1))];
  _setCursor(cible);
  if (_ttsState === 'playing') _abortAndRestart();
}

// --- Navigation phrase ---

function _cursorSentNext() {
  _setCursor(_cursorIdx + 1);
  if (_ttsState === 'playing') _abortAndRestart();
}

function _cursorSentPrev() {
  _setCursor(_cursorIdx - 1);
  if (_ttsState === 'playing') _abortAndRestart();
}

// Coupe le TTS en cours et repart depuis le curseur
function _abortAndRestart() {
  if (_ttsAbort) { _ttsAbort.abort(); _ttsAbort = null; }
  _ttsState = 'idle';
  _startTTS();
}

// ============================================================
// TTS — MOTEUR
// ============================================================

function toggleTTS() {
  if (_ttsState === 'playing') { _pauseTTS(); return; }
  if (_ttsState === 'paused')  { _resumeTTS(); return; }
  if (_ttsState === 'loading') { _stopTTS(); return; }
  _startTTS();
}

// Couverture du livre en cours, en URL ABSOLUE : l'ecran verrouille et la
// notification systeme refusent un chemin relatif.
function _urlCouvertureLivre() {
  if (!_currentBookId) return '';
  return location.origin + '/api/books/' + _currentBookId + '/cover?user_id='
    + _currentUserId + '&v=2';
}

// Identite affichee par le SYSTEME (notification + ecran verrouille) : titre du
// livre, auteur, chapitre, et la COUVERTURE.
// Demande de Laurent, 20/09/2026 : « un genre de lecteur en mode PWA, avec la
// barre de progression qui represente la phrase lue... une petite modale qui
// ressemblerait a la lecture de Deezer ». La couverture et la progression sont
// les deux reperes qui font qu'Android traite la page comme un VRAI lecteur
// media -- et c'est aussi ce qui l'aide a rester en vie ecran verrouille.
function _updateMediaSession() {
  if (!('mediaSession' in navigator)) return;

  const livre = (document.getElementById('reader-book-title')
    ? document.getElementById('reader-book-title').textContent : '') || 'NIMM ePub';
  const chapitre = document.getElementById('chapter-title-display')
    ? document.getElementById('chapter-title-display').textContent : '';
  const couverture = _urlCouvertureLivre();

  navigator.mediaSession.metadata = new MediaMetadata({
    title:  livre,
    artist: (_currentBookData && _currentBookData.author) || '',
    album:  chapitre || 'NIMM ePub',
    artwork: couverture
      ? [{ src: couverture, sizes: '512x512', type: 'image/jpeg' }] : []
  });
  navigator.mediaSession.playbackState = 'playing';

  // Memes pas que la barre du lecteur (voir la section Navigation) :
  // ◀ / ▶ une phrase, ⏪ / ⏩ quatre paragraphes, ⏮ / ⏭ un chapitre. Le casque
  // n'utilise que `previoustrack` / `nexttrack` (la phrase) ; l'ecran
  // verrouille, lui, propose tout ce qu'on declare ici.
  const lier = (nom, action) => {
    try {
      navigator.mediaSession.setActionHandler(nom, action);
    } catch (e) { /* action non supportee par ce navigateur : on continue */ }
  };
  lier('play',          () => toggleTTS());
  lier('pause',         () => toggleTTS());
  lier('stop',          () => _stopTTS());
  lier('previoustrack', () => _cursorSentPrev());
  lier('nexttrack',     () => _cursorSentNext());
  lier('seekbackward',  () => _cursorParaPrev(_PAS_PARAGRAPHES));
  lier('seekforward',   () => _cursorParaNext(_PAS_PARAGRAPHES));
  // La barre du lecteur systeme, si on la tire : notre echelle est celle du
  // CHAPITRE, donc un numero de phrase.
  lier('seekto', (details) => {
    if (details && typeof details.seekTime === 'number') {
      _setCursor(Math.round(details.seekTime));
    }
  });
}

// Barre de progression du lecteur SYSTEME (notification + ecran verrouille),
// demandee par Laurent le 20/09/2026. Echelle : le CHAPITRE -- position =
// nombre de phrases deja lues, duree = phrases du chapitre. La lecture avancant
// phrase par phrase, la barre avance d'un cran a chaque phrase, en coherence
// exacte avec la barre de l'application.
// `try` : `setPositionState` refuse (TypeError) une position hors bornes, et
// une barre ne doit JAMAIS pouvoir casser la lecture.
function _majPositionMediaSession(idx, total) {
  if (!('mediaSession' in navigator)) return;
  if (typeof navigator.mediaSession.setPositionState !== 'function') return;
  const duree = Math.max(1, total || 0);
  const pos   = Math.min(Math.max(0, idx || 0), duree);
  try {
    navigator.mediaSession.setPositionState({
      duration: duree, position: pos, playbackRate: 1
    });
  } catch (e) { /* barre non mise a jour : la lecture continue */ }
}

function _startTTS() {
  if (_sentences.length === 0) return;
  _updateMediaSession();
  _runTTS(_cursorIdx);
}

function _resumeTTS() {
  _runTTS(_cursorIdx);
}

function _pauseTTS() {
  _ttsState = 'paused';
  if (_ttsAbort) { _ttsAbort.abort(); _ttsAbort = null; }
  _couperMessageHorsLigne();
  setTTSUI('paused');
  if ('mediaSession' in navigator) navigator.mediaSession.playbackState = 'paused';
  // Le curseur reste sur la phrase en cours
}

function _stopTTS() {
  _ttsState = 'idle';
  if (_ttsAbort) { _ttsAbort.abort(); _ttsAbort = null; }
  _couperMessageHorsLigne();
  setTTSUI('idle');
  _updateTTSProgress(0, 1);
  if ('mediaSession' in navigator) navigator.mediaSession.playbackState = 'none';
  // Le curseur reste en place
}

// Lecture phrase par phrase. Chaque phrase est synthetisee separement :
// l'audio demarre exactement quand la voix commence la phrase, la
// surbrillance est donc synchrone (plus d'estimation au fil du temps dans
// un bloc fusionne de plusieurs phrases).
//
// Pour ne jamais dependre du reseau au moment du passage d'une phrase a
// l'autre, un prefetcher de fond precharge la SUITE DU CHAPITRE en
// continu (parallelisme borne) au lieu de garder seulement 2 blobs
// d'avance : apres quelques dizaines de secondes de lecture, plusieurs
// minutes d'audio sont deja en memoire. C'est ce qui permet aussi de
// tenir l'ecran verrouille : quand le reseau est suspendu par Android, la
// lecture continue sur le buffer deja precharge au lieu de s'arreter.
const PREFETCH_CONCURRENCY     = 2;      // requetes audio simultanees max
const PREFETCH_MAX_AHEAD_CHARS = 5000;   // fenetre de prechargement max (caracteres ~5-6 min d'audio)

// RESERVE « A BLOC » (20/09/2026, demande de Laurent : « la lecture s'arrete si
// je verrouille le telephone, c'est aleatoire »). Constat mesure : la reserve
// normale (~5-6 min) suffit tant que le reseau vit, mais Android coupe plus ou
// moins vite le reseau d'une page en arriere-plan -- la lecture s'arrete donc
// quand la reserve est vide, « parfois apres quelques secondes, parfois ca tient
// longtemps ». Quand la page passe EN ARRIERE-PLAN pendant une lecture, on leve
// donc le plafond de la fenetre (tout le reste du chapitre) : la reserve se
// remplit pendant que le reseau repond encore, et la lecture tient ensuite sur
// la memoire. Bornage volontairement large mais pas infini : sur un chapitre
// enorme, on ne veut pas remplir la memoire du telephone sans limite.
const PREFETCH_MAX_AHEAD_CHARS_BURST = 400000;

let _prechargementBurst = false;   // reserve « a bloc » (ecran eteint / verrouille)
let _pumpCourant = null;           // `pump` de la session de lecture en cours

// Le declencheur : la page passe en arriere-plan (ecran eteint, verrouillage,
// changement d'application) PENDANT une lecture. On leve le plafond et on
// relance `pump` immediatement -- sans cela, la fenetre deja atteinte ne se
// remplirait qu'au fil des phrases lues, donc trop tard.
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) return;
  if (_ttsState !== 'playing' && _ttsState !== 'loading') return;
  _prechargementBurst = true;
  if (_pumpCourant) _pumpCourant();
});
const FETCH_TIMEOUT_MS         = 20000;  // abandon d'une requete qui ne repond pas
// Les voix Kyutai sont calculees par un moteur externe (carte graphique) :
// une phrase se calcule en gros en deux fois sa duree de lecture. Sans ce
// delai plus large, une longue phrase serait abandonnee en plein calcul.
const KYUTAI_TIMEOUT_MS        = 90000;
const RETRY_NETWORK_WAIT_MS    = 4000;   // pause avant de retenter apres un echec reseau

// --- MESSAGE AUDIO « PAS DE RESEAU » (idee de Laurent, 15/09/2026) ---
// Quand la lecture attend le reseau, le lecteur faisait patienter a l'ecran
// (spinner) sans rien dire. Laurent a voulu l'ENTENDRE aussi : un petit message
// parle, prepare UNE fois au lancement de la lecture (le reseau est disponible
// a ce moment-la), puis joue pendant l'attente. C'est un blob garde en memoire,
// donc il fonctionne meme reseau coupe. « Une feature inutile, donc
// indispensable. »
// LE TEXTE EST ICI, EN UNE SEULE LIGNE : a changer sans rien casser.
const MESSAGE_HORS_LIGNE =
  'Pas de réseau, veuillez patienter. Dès que le réseau sera disponible, '
  + 'la lecture reprendra. Merci pour votre patience.';
// Nombre d'attentes consecutives avant la premiere annonce (4 s chacune).
const MESSAGE_ATTENTES_AVANT = 2;
// Delai minimum entre deux annonces pendant une longue coupure : on ne veut
// pas harceler l'auditeur.
const MESSAGE_RAPPEL_MS = 45000;

// Au-dela de cette taille, une phrase est decoupee en sous-segments pour
// la synthese (aux virgules) : aucune requete ne produit de coupure en
// plein milieu d'un texte. Tous les sous-segments gardent le meme index
// de phrase : le curseur reste pose sur la phrase (surlignee) pendant
// toute la duree de lecture de ses sous-segments.
const SPLIT_SENTENCE_CHARS = 500;
const SPLIT_SEGMENT_CHARS  = 450;

function _splitLongSentence(text) {
  if (text.length <= SPLIT_SENTENCE_CHARS) return [text];
  const out  = [];
  let cur    = '';
  const parts = text.split(/(?<=[,;:])\s+/);
  for (const part of parts) {
    if (cur && (cur.length + part.length + 1) > SPLIT_SEGMENT_CHARS) {
      out.push(cur);
      cur = '';
    }
    if (part.length > SPLIT_SEGMENT_CHARS) {
      for (let k = 0; k < part.length; k += SPLIT_SEGMENT_CHARS) {
        out.push(part.slice(k, k + SPLIT_SEGMENT_CHARS));
      }
      cur = '';
    } else {
      cur = (cur ? cur + ' ' : '') + part;
    }
  }
  if (cur) out.push(cur);
  return out;
}

// Vitesse d'un PERSONNAGE qui a une voix dediee mais AUCUN reglage de vitesse :
// « Normale ». A retenir : le menu du bas (Lente / Moderee / Normale / Rapide /
// Tres rapide) n'est PAS un reglage general de la lecture -- c'est celui du
// NARRATEUR (decision de Laurent, 20/09/2026, le soir). Toute la lecture suit
// donc sa vitesse normale, sauf les personnages regles dans le casting et le
// narrateur (recit + petits roles, qui sont lus par lui).
const PERSONNAGE_RATE_DEFAUT = '+0%';

// Vitesse demandee par la FICHE d'un personnage. Fonction PURE (testable sans
// navigateur) : renvoie la valeur de la fiche quand elle porte un VRAI reglage,
// `null` sinon.
//
// Pourquoi `null` pour le neutre : « +0% » est ce que porte une fiche a
// laquelle Laurent n'a pas touche (1 101 personnages sur 1 232 le
// 20/09/2026). Une fiche au neutre n'exprime donc rien -- meme cas qu'une fiche
// sans vitesse du tout.
//
// REVISION DU 20/09/2026 (soir, decision de Laurent) : le menu du bas etant le
// reglage du NARRATEUR, un personnage sans reglage lit a
// `PERSONNAGE_RATE_DEFAUT` (« Normale ») et non a la vitesse du menu. Les
// phrases qui passent par la voix du narrateur (recit, petits roles) gardent,
// elles, la vitesse du menu.
function _vitesseDeFiche(rate) {
  if (rate === null || rate === undefined) return null;
  const valeur = String(rate).trim();
  if (valeur === '' || valeur === '+0%' || valeur === '0%' || valeur === '+0'
      || valeur === '-0%') {
    return null;
  }
  return valeur;
}

function _voiceForSentence(idx) {
  const defaultVoice = document.getElementById('voice-select').value;
  const speaker = _chapterSpeakers[idx];
  if (speaker && speaker !== 'narration' && _currentBookData && _currentBookData.voices) {
    const v = _currentBookData.voices[speaker];
    // v.voice_id VIDE = personnage sans voix dediee : les petits roles
    // (< 8 repliques) depuis le 15/09/2026. Ils sont lus par le NARRATEUR,
    // c'est-a-dire par la voix choisie dans le lecteur (defaultVoice).
    //
    // La VITESSE suit la voix (correctif du 20/09/2026, regle clarifiee par
    // Laurent le soir) :
    //   - un personnage qui a SA voix et SON reglage de vitesse (curseurs de
    //     la fenetre du casting) est lu a CETTE vitesse ;
    //   - un personnage qui a SA voix mais AUCUN reglage lit a « Normale »
    //     (`PERSONNAGE_RATE_DEFAUT`) : le menu du bas n'est pas un reglage
    //     general, c'est celui du NARRATEUR ;
    //   - le recit et les petits roles (lus par le narrateur) gardent `null`,
    //     donc la vitesse du menu -- c'est le tempo du narrateur.
    // Avant ce correctif, la vitesse n'etait JAMAIS transmise a la synthese :
    // les curseurs du casting s'enregistraient en base sans que rien ne
    // s'entende (131 fiches concernees, mesure du 20/09/2026).
    if (v && v.voice_id) {
      return { voice: v.voice_id, pitch: v.pitch,
               rate: _vitesseDeFiche(v.rate) || PERSONNAGE_RATE_DEFAUT };
    }
  }
  return { voice: defaultVoice, pitch: '+0Hz', rate: null };
}

// Playlist de lecture : UNE unite audio = UNE phrase (ou, pour les phrases
// trop longues pour une seule requete de synthese, un sous-segment de
// phrase). Aucune fusion de phrases entre elles : c'est ce qui permet a la
// surbrillance de coller a la voix (frontiere exacte entre deux phrases) et
// au rythme de lecture d'etre regulier.
// Nombre de MOTS de la phrase precedente envoyes comme CONTEXTE au moteur
// Kyutai (idee de Laurent, 17/09/2026). But : que la voix ne demarre plus a
// froid (hauteur qui « part » differemment d'une phrase a l'autre, phrases
// courtes qui manquent de matiere).
//
// 8 -> 3 le 21/09/2026, MESURE (la demande de Laurent : « peut-etre envoyer
// moins de contexte glissant, par exemple 3 mots au lieu de 8 ? »).
// Le service COUPE l'audio pour ne garder que la phrase ; quand la coupe tombe
// un peu tot, la fin du contexte reste et s'entend (« Je ne pense pas. Pense
// pas Mais tu as peut etre raison »), et quand elle tombe tard, c'est le debut
// de la phrase qui est mange. Mesure du 21/09/2026 (duree de PAROLE, qui est
// le bon signal -- les silences, eux, varient) sur SIX cas reels :
//
//   contexte de 8 mots : 4 cas sur 6 laissaient un residu (+0,40 a +0,73 s),
//                        dont le tiret de dialogue et les guillemets fermants
//                        (ce que Laurent soupconnait : « plus recurrent avec
//                        de la ponctuation ») ;
//   contexte de 3 mots : AUCUN residu, aucun rognage sur les six cas ;
//   contexte de 2 mots : aucun probleme non plus.
//
// Et une decouverte utile : le moteur Kyutai n'est PAS deterministe (deux
// demandes identiques donnent deux audios differents) -- c'est ce qui explique
// que le defaut n'arrive que « de temps en temps ».
//
// Le contexte garde son role (demarrer « en cours de lecture ») : 3 mots
// suffisent a donner l'elan, et il y a moins de matiere a couper de travers.
// Si les debuts de phrase paraissaient a nouveau « a froid », la valeur a
// essayer est 5 ou 6 (une seule ligne a changer).
//
// VERDICT D'OREILLE DE LAURENT (21/09/2026, sur le lot
// `test_voix/ecoute_contexte_20260921_1835` : phrase seule / 3 mots / 8 mots) :
// « Le 3 mots part avec un peu de retard, mais c'est tres bien. Le "seul" part
// presque en avalant le premier phoneme, le premier son. Le 8 ressemble pas mal
// au 3. Je pense que le reglage est tres bien. » -- donc : le contexte SERT
// (sans lui, l'attaque est ecrasee), et 3 mots suffisent.
// NOTE UTILE POUR PLUS TARD : si un debut de phrase semble « mange », le premier
// reflexe est de regarder si cette phrase avait un contexte -- il n'y en a PAS
// apres un saut de paragraphe ni quand le locuteur change (voir _buildPlaylist).
const CONTEXTE_MOTS = 3;

// Le contexte envoye : les derniers mots de l'unite precedente.
function _contexteDe(texte) {
  const mots = (texte || '').trim().split(/\s+/).filter(m => m);
  if (mots.length <= CONTEXTE_MOTS) return mots.join(' ');
  return mots.slice(-CONTEXTE_MOTS).join(' ');
}

function _buildPlaylist(startIdx, endIdx) {
  const units = [];
  const last  = Math.min(
    endIdx === undefined ? _sentences.length - 1 : endIdx,
    _sentences.length - 1
  );

  for (let i = startIdx; i <= last; i++) {
    const s = _sentences[i];
    const v = _voiceForSentence(i);

    // Phrase trop longue : decoupee en sous-segments de synthese aux
    // virgules/points-virgules (aucune coupure en plein milieu d'un texte).
    // Tous les sous-segments portent le meme index de phrase : le curseur
    // reste pose sur la phrase jusqu'a la fin de son dernier sous-segment.
    const segs = _splitLongSentence(s.text);
    for (const seg of segs) {
      units.push({
        text:    seg,
        sentIdx: i,
        paraIdx: s.paraIdx,
        voice:   v.voice,
        pitch:   v.pitch,
        // Vitesse de la phrase (regle clarifiee le 20/09/2026) : celle de la
        // fiche quand le personnage en a une, « Normale » quand il a une voix
        // dediee mais aucun reglage, et `null` pour le recit et les petits
        // roles -- la phrase prend alors la vitesse du menu, qui est le reglage
        // du NARRATEUR (voir `launchFetch`, dans `_runTTS`).
        rate:    v.rate,
      });
    }
  }

  // Contexte entre deux phrases SEULEMENT si elles sont du MEME locuteur ET
  // DANS LE MEME PARAGRAPHE (idee de Laurent, 17/09/2026 au soir) :
  //   - locuteur : le contexte d'une replique d'un autre personnage serait lu
  //     avec la voix du nouveau venu -- un locuteur preterait son elan a un
  //     autre, ce qui n'a pas de sens ;
  //   - paragraphe (saut de ligne) : un nouveau paragraphe ouvre un NOUVEAU
  //     PROPOS ; le modele n'a pas besoin de l'elan du precedent. C'est aussi
  //     le cas ou la coupe du contexte laissait s'entendre le dernier mot du
  //     paragraphe d'avant (« montagne. Va faire un petit tour... »), et ou le
  //     double travail du moteur se paie sans benefice (attente audible).
  //   - temps : chaque generation avec contexte en fait DEUX (le contexte est
  //     genere seul pour connaitre la frontiere).
  // Donc : le contexte ne sert plus qu'a une SUITE de phrases du meme locuteur
  // dans le meme paragraphe -- la ou l'enchainement s'entend vraiment.
  for (let i = 1; i < units.length; i++) {
    if (units[i].voice !== units[i - 1].voice) continue;
    if (units[i].paraIdx !== units[i - 1].paraIdx) continue;
    units[i].context = _contexteDe(units[i - 1].text);
  }
  return units;
}

// ============================================================
// MESSAGE AUDIO « PAS DE RESEAU » (idee de Laurent, 15/09/2026)
// ============================================================
// Prepare le message : UNE requete au serveur, faite au lancement de la lecture
// (le reseau est disponible a ce moment-la). Le blob est ensuite garde en
// memoire, donc il peut etre joue meme si le reseau tombe. Aucune erreur n'est
// remontee : si le message n'a pas pu etre prepare, la lecture s'en passe.
async function _preparerMessageHorsLigne() {
  if (_messageHorsLigne) return;              // deja prepare pour cette session
  try {
    const choix = document.getElementById('voice-select');
    const voix  = (choix && choix.value) ? choix.value : 'fr-CH-ArianeNeural';
    const res = await fetch('/api/tts', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        text: MESSAGE_HORS_LIGNE, voice: voix, rate: '+0%', pitch: '+0Hz'
      })
    });
    if (!res.ok) return;
    _messageHorsLigne = URL.createObjectURL(await res.blob());
  } catch (e) {
    // Reseau deja coupe, ou moteur indisponible : on se passera du message.
  }
}

// Faut-il annoncer la coupure MAINTENANT ? Fonction PURE, testable sans
// navigateur (test_voix/test_message_reseau.js) : premiere annonce apres
// MESSAGE_ATTENTES_AVANT attentes, puis au plus une toutes les
// MESSAGE_RAPPEL_MS -- on ne veut pas harceler l'auditeur.
function _fautPrevenirReseau(attentes, depuis, maintenant) {
  if (!_messageHorsLigne) return false;       // rien de pret a jouer
  if (attentes === MESSAGE_ATTENTES_AVANT) return true;
  if (attentes > MESSAGE_ATTENTES_AVANT
      && (maintenant - depuis) >= MESSAGE_RAPPEL_MS) return true;
  return false;
}

// Joue le message. Ne bloque jamais la lecture et ne leve jamais d'erreur :
// c'est un confort, pas une fonction vitale.
function _prevenirReseauCoupe(attentes) {
  if (!_fautPrevenirReseau(attentes, _messageHorsLigneQuand, Date.now())) return;
  _messageHorsLigneQuand = Date.now();
  try {
    _couperMessageHorsLigne();
    _messageAudio = new Audio(_messageHorsLigne);
    _messageAudio.play().catch(() => {});
  } catch (e) {
    // On continue sans message.
  }
}

// Coupe le message en cours (arret de la lecture, mise en pause, reprise).
function _couperMessageHorsLigne() {
  if (_messageAudio) {
    try { _messageAudio.pause(); } catch (e) { /* deja termine */ }
    _messageAudio = null;
  }
}

async function _runTTS(startIdx, endIdx) {
  if (_sentences.length === 0 || startIdx >= _sentences.length) return;

  _ttsSession++;
  const mySession = _ttsSession;
  _ttsAbort      = new AbortController();
  _ttsState      = 'loading';
  _ttsFatalError = null;
  setTTSUI('loading');

  const rate   = document.getElementById('speed-select').value;
  const signal = _ttsAbort.signal;

  // Le message « pas de reseau » se prepare MAINTENANT, pendant que le reseau
  // est la (idee de Laurent, 15/09/2026). Sans `await` : il ne doit jamais
  // retarder le demarrage de la lecture.
  _preparerMessageHorsLigne();

  const units = _buildPlaylist(startIdx, endIdx);
  if (units.length === 0) {
    _ttsState = 'idle';
    setTTSUI('idle');
    return;
  }

  // --- Prefetcher ---
  // Cache des blobs audio, une entree par unite de lecture. Un prefetcher
  // avance en continu dans la playlist (fenetre glissante plafonnee a
  // PREFETCH_MAX_AHEAD_CHARS) : la lecture trouve toujours ses blobs deja
  // prets et ne depend jamais du reseau au moment du passage d'une phrase
  // a la suivante. Apres quelques dizaines de secondes, plusieurs minutes
  // d'audio sont en memoire -- c'est ce qui permet a la lecture de tenir
  // quand Android suspend le reseau de la page (ecran verrouille).
  const cache   = new Array(units.length).fill(null);
  // Les blobs DEJA telecharges, accessibles tout de suite : c'est ce qui permet
  // de coller plusieurs phrases en un seul morceau (voir _collerWav).
  const blobs   = new Array(units.length).fill(null);
  let readIdx   = -1;      // unite dont la lecture a demarre (-1 = pas encore)
  let nextFetch = 0;       // prochaine unite a demander au serveur
  let inFlight  = 0;       // requetes en vol
  let attentesReseau = 0;  // attentes consecutives depuis la derniere reussite
  const wakeups = [];      // resolveurs reveilles quand un fetch se termine

  function wakeWaiters() {
    while (wakeups.length) wakeups.shift()();
  }

  function launchFetch(i) {
    if (cache[i] || i >= units.length) return;
    inFlight++;
    const u = units[i];
    // Vitesse de la phrase (regle de Laurent, 20/09/2026) : `u.rate` porte
    // soit la vitesse de la fiche, soit « Normale »
    // (`PERSONNAGE_RATE_DEFAUT`) pour un personnage sans reglage. Il n'est NUL
    // que pour le recit et les petits roles : ces phrases-la suivent le menu,
    // qui est le reglage du NARRATEUR.
    cache[i] = _fetchAudio(u.text, u.voice, u.rate || rate, u.pitch, signal,
                           u.context).then(blob => {
      if (!blob) { cache[i] = null; return null; }  // echec : pourra etre retente
      blobs[i] = blob;                              // pret pour le collage
      return blob;
    });
    cache[i].then(() => { inFlight--; wakeWaiters(); pump(); });
  }

  // Poids en caracteres des unites deja prechargees non encore lues.
  // `limiteFenetre()` : plafond normal, ou plafond leve quand la page est passée
  // en arriere-plan (reserve « a bloc », voir _prechargementBurst).
  function limiteFenetre() {
    return _prechargementBurst ? PREFETCH_MAX_AHEAD_CHARS_BURST
                              : PREFETCH_MAX_AHEAD_CHARS;
  }

  function aheadChars() {
    let w = 0;
    for (let i = readIdx + 1; i < nextFetch; i++) {
      w += units[i].text.length + 1;
      if (w > limiteFenetre()) break;
    }
    return w;
  }

  // Fenetre glissante : lance les fetchs vers l'avant tant qu'on est sous
  // le plafond de caracteres et sous la limite de parallelisme.
  function pump() {
    if (_ttsSession !== mySession || signal.aborted) return;
    while (inFlight < PREFETCH_CONCURRENCY && nextFetch < units.length) {
      if (aheadChars() + units[nextFetch].text.length + 1 > limiteFenetre()) break;
      launchFetch(nextFetch);
      nextFetch++;
    }
  }

  // La reserve « a bloc » doit pouvoir relancer ce `pump` depuis le declencheur
  // `visibilitychange` (qui vit au niveau du fichier, pas dans cette session).
  // La session courante sert de garde-fou : un `pump` perime ne fait rien.
  _pumpCourant = pump;

  function waitUnit(i) {
    if (!cache[i]) launchFetch(i);
    return cache[i];
  }

  // Attend le blob d'une unite, mais au maximum maxMs (demarrage : on ne
  // veut pas retarder la lecture si la 2e phrase traine).
  function waitUnitBriefly(i, maxMs) {
    const p = waitUnit(i);
    if (!p) return Promise.resolve(null);
    return new Promise(resolve => {
      const timer = setTimeout(() => resolve(null), maxMs);
      p.then(blob => { clearTimeout(timer); resolve(blob); });
    });
  }

  // Attend le blob d'une unite en retentant patiemment quand le reseau ne
  // repond pas (reseau suspendu par l'ecran verrouille, coupure Tailscale,
  // etc.). Ne sort que si la lecture est stoppee ou si la session change :
  // des que le reseau revient, la lecture repart d'elle-meme. Les fetchs
  // individuels ont deja leur propre timeout (FETCH_TIMEOUT_MS), donc une
  // requete bloquee ne nous fige jamais.
  async function waitUnitNetworkRetry(i) {
    for (;;) {
      if (_ttsSession !== mySession || signal.aborted) return null;
      const blob = await waitUnit(i);
      if (blob) { attentesReseau = 0; return blob; }
      if (_ttsSession !== mySession || signal.aborted) return null;
      // Erreur definitive signalee par le serveur (moteur Kyutai eteint) :
      // on affiche le message et on s'arrete, au lieu d'attendre sans fin.
      if (_ttsFatalError) {
        _ttsState = 'idle';
        setTTSUI('idle');
        alert(_ttsFatalError);
        _ttsFatalError = null;
        return null;
      }
      // Reseau indisponible : on precharge ce qu'on peut et on reessaie.
      // Le message audio « pas de reseau » se declenche ici (15/09/2026) :
      // toute premiere annonce apres quelques secondes d'attente, puis au plus
      // une toutes les MESSAGE_RAPPEL_MS.
      attentesReseau++;
      _prevenirReseauCoupe(attentesReseau);
      pump();
      if (_ttsState !== 'loading') { _ttsState = 'loading'; setTTSUI('loading'); }
      await _pause(RETRY_NETWORK_WAIT_MS, signal);
    }
  }

  // --- Demarrage ---
  // Precharge immediatement les premieres unites puis attend que la 1re
  // soit prete avant de lancer l'audio (UI en 'loading' le temps du fetch).
  pump();
  const firstBlob = await waitUnitNetworkRetry(0);
  if (!firstBlob) return;

  // La 2e phrase est deja en cours de prechargement (lancee par pump) :
  // on la laisse finir quelques instants pour demarrer avec au moins
  // 2 phrases d'avance en main, sans jamais retarder la lecture.
  if (units.length > 1) {
    await waitUnitBriefly(1, 3000);
    if (_ttsSession !== mySession || signal.aborted) return;
  }

  // --- Boucle de lecture, par MORCEAUX COLLES (20/09/2026) ---
  // On ne joue plus phrase par phrase : on colle tout ce qui est DEJA
  // telecharge (tant que le format est le meme) en un SEUL morceau, joue d'un
  // trait. C'est ce qui garde la modale de lecture affichee sur le telephone et
  // supprime les micro-blancs entre les phrases.
  // Filet : si le collage est impossible (format inattendu), la phrase est jouee
  // seule, exactement comme avant.
  const pauseAvant = (k) => (k > 0 && units[k].paraIdx !== units[k - 1].paraIdx)
    ? PARAGRAPH_PAUSE_MS : 0;

  for (let i = 0; i < units.length; ) {
    if (_ttsSession !== mySession || signal.aborted) break;

    // Le premier blob du morceau doit etre pret (coupure reseau : on attend sans
    // arreter, comme avant).
    const premier = await waitUnitNetworkRetry(i);
    if (!premier || _ttsSession !== mySession || signal.aborted) break;

    // Reprise apres une attente reseau : on repasse en lecture.
    if (_ttsState !== 'playing') {
      _ttsState = 'playing';
      setTTSUI('playing');
    }

    // Tout ce qui est deja en memoire, tant que le format reste le meme.
    const parties = [];
    let fin = i;
    while (fin < units.length) {
      const blob = (fin === i) ? premier : blobs[fin];
      if (!blob) break;                     // pas encore telecharge : on s'arrete
      const entete = await _enteteDeBlob(blob);
      if (!entete) break;                   // format inattendu : on s'arrete
      if (parties.length && !_memesFormats(parties[0].entete, entete)) break;
      parties.push({ blob: blob, entete: entete, pauseAvantMs: pauseAvant(fin) });
      fin++;
    }

    const morceau = _collerWav(parties);

    // Memoire : le morceau colle GARDE les donnees d'origine (Blob.slice ne copie
    // rien, il pointe dessus), on peut donc relacher nos references.
    for (let k = i; k < fin; k++) { cache[k] = null; blobs[k] = null; }
    readIdx = fin - 1;   // la fenetre de prechargement repart de la FIN du
    pump();              // morceau, sinon elle croirait avoir deja tout

    if (!morceau) {
      // Filet : collage impossible -> la phrase seule, comme avant.
      if (units[i].sentIdx !== _cursorIdx) _setCursor(units[i].sentIdx);
      _updateTTSProgress(units[i].sentIdx, _sentences.length);
      await _playBlob(premier, signal);
      i++;
      continue;
    }

    await _jouerMorceauColle(morceau, units, i, parties, signal);
    i = fin;

    // Une pause venue d'ailleurs (casque, appel telephonique, autre application)
    // arrete proprement la session ICI : la suite repartira du curseur a la
    // prochaine pression de lecture, sans reprendre toute seule au milieu.
    if (_ttsState === 'paused') break;

    if (_ttsSession !== mySession || signal.aborted) break;
  }

  // --- Fin de session ---
  if (_ttsSession === mySession && _ttsState === 'playing') {
    _ttsState = 'idle';
    setTTSUI('idle');
    _updateTTSProgress(0, 1);
    if ('mediaSession' in navigator) navigator.mediaSession.playbackState = 'none';
    // Lecture continue uniquement (pas de plage delimitee par une selection) :
    // on enchaîne sur le chapitre suivant.
    if (endIdx === undefined && _currentChapter < _totalChapters - 1) {
      await loadChapter(_currentChapter + 1, 0, 0, true);
    }
  }
}

function _updateTTSProgress(idx, total) {
  const pct = total > 0 ? Math.round((idx / total) * 100) : 0;
  document.getElementById('tts-progress-fill').style.width = pct + '%';
  // La MEME progression alimente les deux autres ecrans de lecture (20/09/2026) :
  // le lecteur du systeme (notification + ecran verrouille) et le lecteur
  // integre « facon Deezer », s'il est ouvert.
  _majPositionMediaSession(idx, total);
  if (typeof _majLecteurIntegre === 'function') _majLecteurIntegre(idx, total);
}

// ============================================================
// LECTEUR INTEGRE « FACON DEEZER » (20/09/2026)
// ============================================================
// Demande de Laurent : « je vois bien un genre de lecteur en mode PWA, avec la
// barre de progression qui represente la phrase lue. Une petite modale qui
// ressemblerait a la lecture de Deezer. »
// Ouverture : la BARRE DE PROGRESSION du lecteur (le repere naturel -- c'est ce
// qu'on fait partout), qui porte un petit ⤢ pour l'annoncer sans mot.
// Utile et pas decoratif : la fenetre dit QUI PARLE et QUELLE PHRASE est en
// cours, ce qui n'existe dans aucun lecteur audio.

function _lecteurOuvert() {
  const m = document.getElementById('lecteur-modal');
  return !!m && !m.classList.contains('hidden');
}

function _ouvrirLecteur() {
  // On REMPLIT avant d'afficher : sinon la fenetre s'ouvrirait vide un instant.
  _majLecteurIntegre(_cursorIdx, _sentences.length);
  _majLecteurEtat(_ttsState);
  document.getElementById('lecteur-modal').classList.remove('hidden');
}

function _fermerLecteur() {
  document.getElementById('lecteur-modal').classList.add('hidden');
}

// Etat du bouton de lecture (▶️ / ⏸), comme la barre du bas. Pendant un
// chargement, l'icone reste celle de la lecture et c'est le titre qui dit
// « Chargement » -- jamais un etat invente.
function _majLecteurEtat(state) {
  if (!_lecteurOuvert()) return;
  const enLecture = (state === 'playing');
  const play  = document.getElementById('lecteur-icon-play');
  const pause = document.getElementById('lecteur-icon-pause');
  if (play)  play.classList.toggle('hidden', enLecture);
  if (pause) pause.classList.toggle('hidden', !enLecture);
  const btn = document.getElementById('lecteur-play-btn');
  if (btn) {
    btn.title = (state === 'loading') ? 'Chargement en cours…'
              : (enLecture ? 'Pause' : 'Lecture');
  }
}

// Tout ce que la fenetre affiche : le livre, le chapitre, qui parle, la phrase
// en cours, et la progression du chapitre.
function _majLecteurIntegre(idx, total) {
  if (!_lecteurOuvert()) return;
  const el = (id) => document.getElementById(id);
  const livre = (el('reader-book-title') || {}).textContent || '';
  el('lecteur-titre').textContent = livre;
  el('lecteur-auteur').textContent =
    (_currentBookData && _currentBookData.author) || '';
  const chapitre = (el('chapter-title-display') || {}).textContent || '';
  el('lecteur-chapitre').textContent = 'Chapitre ' + (_currentChapter + 1)
    + ' / ' + _totalChapters + (chapitre ? ' · ' + chapitre : '');

  const nom = _personnageDePhrase(idx);
  el('lecteur-qui').textContent = nom ? '\uD83D\uDDE3\uFE0F ' + nom
                                     : '\uD83C\uDF99\uFE0F Narrateur';
  const texte = (_sentences[idx] && _sentences[idx].text) || '';
  el('lecteur-phrase').textContent =
    (texte.length > 160) ? texte.slice(0, 157) + '\u2026' : texte;

  const pct = total > 0 ? Math.round((idx / total) * 100) : 0;
  el('lecteur-barre-fill').style.width = pct + '%';
  el('lecteur-compteur').textContent = total > 0
    ? (idx + 1) + ' / ' + total + ' phrases · ' + pct + ' %' : '';

  // La couverture, seulement si le livre en a une : jamais de cadre vide.
  const img = el('lecteur-couverture');
  if (img) {
    const url = _urlCouvertureLivre();
    const aCouverture = !!(_currentBookData && _currentBookData.cover_path);
    if (url && aCouverture) {
      if (img.getAttribute('src') !== url) img.src = url;
      img.classList.remove('hidden');
    } else {
      img.removeAttribute('src');
      img.classList.add('hidden');
    }
  }
}

// --- Branchements du lecteur ---
document.getElementById('lecteur-close-btn').addEventListener('click', _fermerLecteur);
document.getElementById('lecteur-modal').addEventListener('click', (e) => {
  if (e.target.id === 'lecteur-modal') _fermerLecteur();   // clic a cote
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && _lecteurOuvert()) _fermerLecteur();
});
// La barre de progression OUVRE le lecteur (au doigt comme au clavier).
document.getElementById('tts-progress-row').addEventListener('click', _ouvrirLecteur);
document.getElementById('tts-progress-row').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); _ouvrirLecteur(); }
});
// Les boutons du lecteur sont des TELECOMMANDES de la barre du bas : on clique
// sur les VRAIS boutons. Une seule logique de navigation a maintenir, et les pas
// sont forcement les bons (◀ ▶ la phrase, ⏪ ⏩ quatre paragraphes, ⏮ ⏭ le
// chapitre, et le bouton de lecture partage l'etat de la barre).
[['lecteur-prev-chap', 'prev-btn'],
 ['lecteur-prev-para', 'para-prev-btn'],
 ['lecteur-prev-sent', 'sent-prev-btn'],
 ['lecteur-play-btn',  'tts-play-btn'],
 ['lecteur-next-sent', 'sent-next-btn'],
 ['lecteur-next-para', 'para-next-btn'],
 ['lecteur-next-chap', 'next-btn']].forEach(([boutonLecteur, boutonBarre]) => {
  const b = document.getElementById(boutonLecteur);
  if (b) b.addEventListener('click', () => document.getElementById(boutonBarre).click());
});

// L'identifiant du livre OUVERT (0 si aucun). Il part avec chaque demande de
// synthese : le serveur s'en sert pour remettre en casse normale les mots TOUT
// EN MAJUSCULES qui sont des mots de CE livre (« DE », « LUI »), sans toucher
// aux sigles (« JFK », « FBI »). Demande de Laurent, 19/09/2026.
function _livreCourantId() {
  const d = (typeof _currentBookData === 'undefined') ? null : _currentBookData;
  return (d && d.id) ? d.id : 0;
}

async function _fetchAudio(text, voice, rate, pitch, signal, context) {
  // Retry renforcé pour le tunnel Tailscale : en mobile, chaque requête TTS
  // traverse le tunnel VPN. Quand l'écran est éteint ou le téléphone est
  // verrouillé, Android peut suspendre le réseau de la page SANS erreur :
  // la requête resterait bloquée pour toujours (aucun catch, donc aucun
  // retry). Un timeout par tentative (FETCH_TIMEOUT_MS) abandonne la
  // requête zombie et permet de la relancer -- c'est ce qui permet à la
  // lecture de repartir seule dès que le réseau revient.
  const backoff = [1000, 2000, 4000];
  for (let a = 0; a <= backoff.length; a++) {
    if (signal.aborted) return null;
    const timeoutCtrl = new AbortController();
    const onAbort     = () => timeoutCtrl.abort();
    signal.addEventListener('abort', onAbort);
    const delai = voice.startsWith('kyutai:') ? KYUTAI_TIMEOUT_MS : FETCH_TIMEOUT_MS;
    const timer = setTimeout(() => timeoutCtrl.abort(), delai);
    try {
      const res = await fetch('/api/tts', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ text, voice, rate, pitch,
                                  context: context || '',
                                  book_id: _livreCourantId() }),
        signal:  timeoutCtrl.signal
      });
      if (res.status === 503) {
        // Erreur definitive cote serveur (ex: moteur de voix Kyutai eteint) :
        // inutile de reessayer. On retient le message pour l'afficher une
        // seule fois, et on sort sans relancer la requete.
        const err = await res.json().catch(() => ({}));
        _ttsFatalError = err.detail || 'Moteur de voix indisponible.';
        return null;
      }
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.blob();
    } catch (e) {
      if (signal.aborted) return null;
      console.error('TTS fetch (essai ' + (a + 1) + '/' + (backoff.length + 1) + '):', e);
      if (a < backoff.length) await _pause(backoff[a], signal);
    } finally {
      clearTimeout(timer);
      signal.removeEventListener('abort', onAbort);
    }
  }
  return null;
}

// Joue un blob audio jusqu'à sa fin. AUCUN suivi de position au fil du
// temps : depuis que la lecture est phrase par phrase, la frontière entre
// deux phrases est exacte (le curseur est posé quand l'audio démarre, il
// n'y a plus rien à estimer pendant la lecture).
// ============================================================
// COLLAGE DES PHRASES EN UN SEUL MORCEAU (20/09/2026)
// ============================================================
// Demande de Laurent : « la modale de lecture disparait entre deux paragraphes,
// puisqu'il n'y a plus de voix... c'est comme si j'avais une playlist de
// centaines de morceaux de quelques secondes ». C'est exactement ce que faisait
// le lecteur : un petit fichier audio PAR PHRASE -- plus de son pendant la
// preparation de la suivante, et Android range sa modale des qu'il n'y a plus
// de son. Correction : COLLER les phrases en UN SEUL long morceau, joue d'un
// trait. Deux effets : la modale du telephone reste affichee (comme pour une
// video) et le son n'a plus de micro-blanc entre les phrases.
//
// Les fichiers du lecteur sont des WAV (audio non compresse) : on peut donc les
// recoller EXACTEMENT, en fabriquant une seule en-tete et en pointant sur les
// donnees d'origine. `Blob.slice` ne COPIE rien : le collage ne consomme pas de
// memoire en plus. Les fonctions de lecture d'en-tete sont PURES (un tableau
// d'octets en entree) : verifiees par test_voix/test_collage_wav.js.

// Lit l'en-tete d'un WAV : format, canaux, cadence, resolution, et ou commence
// le son. Retourne null si ce n'est pas un WAV lisible.
// `tailleFichier` (facultatif) : la taille REELLE du fichier, quand on n'a lu
// que son DEBUT (c'est ce que fait _enteteDeBlob : 64 octets suffisent pour
// l'en-tete). Sans elle, on ne peut pas savoir si le fichier est complet --
// et croire qu'un morceau de 2 minutes ne fait que 64 octets serait une drole
// d'idee (c'est l'erreur que le test du collage a attrapee le 20/09/2026).
function _enteteWav(octets, tailleFichier) {
  const vue = new DataView(octets.buffer, octets.byteOffset, octets.byteLength);
  const txt = (pos, n) => {
    let s = '';
    for (let i = 0; i < n; i++) s += String.fromCharCode(vue.getUint8(pos + i));
    return s;
  };
  if (vue.byteLength < 44 || txt(0, 4) !== 'RIFF' || txt(8, 4) !== 'WAVE') return null;

  const dispo = (tailleFichier === undefined) ? vue.byteLength : tailleFichier;
  let pos = 12;
  let entete = null;
  while (pos + 8 <= vue.byteLength) {
    const nom    = txt(pos, 4);
    const taille = vue.getUint32(pos + 4, true);
    const debut  = pos + 8;
    if (nom === 'fmt ' && debut + 16 <= vue.byteLength) {
      entete = {
        format:  vue.getUint16(debut, true),        // 1 = PCM, 3 = flottant
        canaux:  vue.getUint16(debut + 2, true),
        cadence: vue.getUint32(debut + 4, true),
        bits:    vue.getUint16(debut + 14, true),
      };
    } else if (nom === 'data') {
      if (!entete) return null;
      entete.debutDonnees  = debut;
      // Un fichier tronque (ecriture interrompue) ne doit pas nous tromper :
      // on garde la plus petite des deux tailles.
      entete.tailleDonnees = Math.min(taille, Math.max(0, dispo - debut));
      return entete;
    }
    pos = debut + taille + (taille % 2);   // les morceaux sont alignes sur 2 octets
  }
  return null;   // pas de bloc de donnees : on ne sait pas coller ca
}

// Duree exacte (en secondes) du son decrit par une en-tete : nombre d'octets
// divises par le debit. C'est CE calcul qui remplace l'estimation quand on joue
// un morceau colle (la surbrillance reste donc exacte).
function _dureeWav(entete) {
  if (!entete || !entete.cadence || !entete.canaux || !entete.bits) return 0;
  const debit = entete.cadence * entete.canaux * (entete.bits / 8);
  return debit > 0 ? (entete.tailleDonnees / debit) : 0;
}

// Deux morceaux ne se collent que s'ils ont EXACTEMENT le meme format : c'est ce
// qui protege des voix Piper (22050 Hz) qui ne peuvent pas etre collees aux
// autres (24000 Hz). Elles mettent simplement fin au morceau en cours.
function _memesFormats(a, b) {
  return !!a && !!b && a.format === b.format && a.canaux === b.canaux
      && a.cadence === b.cadence && a.bits === b.bits;
}

// Fabrique l'en-tete du morceau colle (meme format que le premier morceau), en
// annoncant la taille TOTALE du son. Format classique de 44 octets : RIFF,
// fmt (16 octets), data.
function _enteteWavColle(entete, tailleDonnees) {
  const vue = new DataView(new ArrayBuffer(44));
  const ecrire = (pos, s) => {
    for (let i = 0; i < s.length; i++) vue.setUint8(pos + i, s.charCodeAt(i));
  };
  const debit = entete.cadence * entete.canaux * (entete.bits / 8);
  ecrire(0, 'RIFF');
  vue.setUint32(4, 36 + tailleDonnees, true);
  ecrire(8, 'WAVE');
  ecrire(12, 'fmt ');
  vue.setUint32(16, 16, true);
  vue.setUint16(20, entete.format, true);
  vue.setUint16(22, entete.canaux, true);
  vue.setUint32(24, entete.cadence, true);
  vue.setUint32(28, debit, true);
  vue.setUint16(32, entete.canaux * (entete.bits / 8), true);   // alignement
  vue.setUint16(34, entete.bits, true);
  ecrire(36, 'data');
  vue.setUint32(40, tailleDonnees, true);
  return new Uint8Array(vue.buffer);
}

// Un petit morceau de SILENCE : il garde la pause entre deux paragraphes A
// L'INTERIEUR du morceau colle (sans lui, elle disparaitrait : il n'y a plus de
// silence entre deux fichiers, puisqu'il n'y a plus qu'UN fichier).
function _blobSilence(entete, dureeMs) {
  const debit  = entete.cadence * entete.canaux * (entete.bits / 8);
  const taille = Math.max(0, Math.round(debit * (dureeMs / 1000)));
  return new Blob([new Uint8Array(taille)], { type: 'audio/wav' });
}

// Colle une suite de phrases en UN SEUL blob WAV.
// `parties` : [{ blob, entete, pauseAvantMs }].
// Retourne null si les formats ne sont pas compatibles : l'appelant repart alors
// en lecture phrase par phrase (le filet, jamais un silence).
function _collerWav(parties) {
  if (!parties || !parties.length) return null;
  const entete = parties[0].entete;
  if (!entete || !parties.every(p => _memesFormats(entete, p.entete))) return null;

  const morceaux = [];
  let total = 0;
  parties.forEach((p, i) => {
    if (i > 0 && p.pauseAvantMs > 0) {
      const silence = _blobSilence(entete, p.pauseAvantMs);
      morceaux.push(silence);
      total += silence.size;
    }
    morceaux.push(p.blob.slice(p.entete.debutDonnees));
    total += p.entete.tailleDonnees;
  });
  return new Blob([_enteteWavColle(entete, total)].concat(morceaux),
                  { type: 'audio/wav' });
}

// En-tete d'un blob audio (on ne lit que le DEBUT du fichier : c'est tout ce dont
// on a besoin, et ca reste rapide meme sur un morceau long). La taille REELLE du
// fichier est transmise : sans elle, un fichier de 2 minutes semblerait ne durer
// que 64 octets.
async function _enteteDeBlob(blob) {
  try {
    const debut = new Uint8Array(await blob.slice(0, 64).arrayBuffer());
    return _enteteWav(debut, blob.size);
  } catch (e) {
    return null;
  }
}

// Joue un morceau COLLE et fait suivre la surbrillance. Les durees sont
// CALCULEES (taille du son / cadence) et non estimees : c'est ce qui permet de
// revenir a un seul morceau sans perdre la precision du curseur (le probleme qui
// avait fait abandonner les blocs fusionnes le 15/09/2026).
async function _jouerMorceauColle(blob, units, debut, parties, signal) {
  const url   = URL.createObjectURL(blob);
  const audio = document.getElementById('tts-audio-player');

  // Bornes de chaque phrase dans le morceau (en secondes, pauses comprises).
  const bornes = [];
  let t = 0;
  parties.forEach((p, k) => {
    t += (p.pauseAvantMs || 0) / 1000;
    const duree = _dureeWav(p.entete);
    bornes.push({ debut: t, duree: duree, unit: units[debut + k] });
    t += duree;
  });

  // Le curseur est pose AVANT de jouer : la surbrillance ne doit jamais arriver
  // en retard sur la voix.
  if (bornes.length && bornes[0].unit.sentIdx !== _cursorIdx) {
    _setCursor(bornes[0].unit.sentIdx);
  }
  _updateTTSProgress(bornes.length ? bornes[0].unit.sentIdx : _cursorIdx,
                     _sentences.length);

  await new Promise(resolve => {
    let termine = false;
    const cleanup = () => {
      if (termine) return;
      termine = true;
      audio.onended      = null;
      audio.onerror      = null;
      audio.onpause      = null;
      audio.ontimeupdate = null;
      URL.revokeObjectURL(url);
      resolve();
    };
    audio.onended = cleanup;
    audio.onerror = cleanup;
    signal.addEventListener('abort', () => { audio.pause(); cleanup(); });

    // PAUSE VENUE D'AILLEURS (20/09/2026) : un appel telephonique, une autre
    // application qui prend le son, le systeme... L'element audio s'arrete SANS
    // evenement de fin : le lecteur attendait alors pour toujours, et le bouton
    // continuait d'afficher « Pause » alors que plus rien ne jouait (constat de
    // Laurent, le soir meme). On remet donc l'etat de l'application EN PHASE avec
    // la realite. Et c'est ce qui rend le bouton du CASQUE utile : a la pression
    // suivante, l'application se sait en pause -- donc elle REPREND la lecture.
    audio.onpause = () => {
      // Notre propre pause est deja annoncee (`_ttsState` vaut 'paused'), et une
      // fin naturelle du morceau declenche aussi 'pause' : aucun des deux ne doit
      // etre pris pour une interruption.
      if (_ttsState !== 'playing' || audio.ended) return;
      _ttsState = 'paused';
      setTTSUI('paused');
      if ('mediaSession' in navigator) navigator.mediaSession.playbackState = 'paused';
      cleanup();
    };

    let courante = -1;
    audio.ontimeupdate = () => {
      const tc = audio.currentTime;
      let idx = 0;
      while (idx + 1 < bornes.length && tc >= bornes[idx + 1].debut) idx++;
      const b = bornes[idx];
      if (idx !== courante) {
        courante = idx;
        if (b.unit.sentIdx !== _cursorIdx) _setCursor(b.unit.sentIdx);
        _updateTTSProgress(b.unit.sentIdx, _sentences.length);
      }
      // Barre du lecteur systeme : elle avance en DOUCEUR (phrase + fraction de
      // phrase) au lieu de sauter d'une phrase a l'autre.
      const dansPhrase = b.duree > 0
        ? Math.max(0, Math.min(1, (tc - b.debut) / b.duree)) : 0;
      _majPositionMediaSession(b.unit.sentIdx + dansPhrase, _sentences.length);
    };

    audio.src = url;
    audio.play().catch(cleanup);
  });
}

async function _playBlob(blob, signal) {
  if (!blob) return;
  const url   = URL.createObjectURL(blob);
  const audio = document.getElementById('tts-audio-player');
  await new Promise(resolve => {
    const cleanup = () => {
      audio.onended = null;
      audio.onerror = null;
      URL.revokeObjectURL(url);
      resolve();
    };
    audio.onended = cleanup;
    audio.onerror = cleanup;
    signal.addEventListener('abort', () => { audio.pause(); cleanup(); });
    audio.src = url;
    audio.play().catch(cleanup);
  });
}

// Pause silencieuse entre deux paragraphes (ex: apres un titre, ou entre deux
// repliques d'un dialogue : chaque replique est un paragraphe).
// Elle valait 300 ms. Decision de Laurent (15/09/2026, ecoute du Comte de
// Monte-Cristo) : elle a ete mise a 0, car elle s'additionnait au silence de
// fin de phrase du moteur (rogne a 0,25 s cote XTTS et Edge).
// REVISION DU 17/09/2026 (ecoute de Kyutai) : « le point passe tres tres vite »
// -> remise a 100 ms, puis, apres le contexte glissant, Laurent a trouve les
// pauses de fin de phrase « un tout petit peu longues » et les SAUTS DE LIGNE
// « tres rapides » : la pause entre paragraphes repasse donc a 300 ms (sa
// valeur d'origine), et la respiration ajoutee en fin de phrase cote Kyutai est
// retiree. Interrompue immediatement si le TTS est stoppe/aborte.
function _pause(ms, signal) {
  return new Promise(resolve => {
    const timer = setTimeout(resolve, ms);
    // `signal` est facultatif : une pause hors lecture (nouvel essai de
    // chargement d'un chapitre, par exemple) n'a rien a interrompre.
    if (signal) signal.addEventListener('abort', () => { clearTimeout(timer); resolve(); });
  });
}

const PARAGRAPH_PAUSE_MS = 300;

// ============================================================
// SELECTION DE TEXTE — "Lire à partir d'ici" (desktop uniquement)
// ============================================================

function _showSelectionTooltip(rect) {
  const tip  = document.getElementById('selection-tooltip');
  const left = rect.left + rect.width / 2;
  const top  = rect.top - 44;
  tip.style.left = left + 'px';
  tip.style.top  = (top < 8 ? rect.bottom + 8 : top) + 'px';
  tip.classList.remove('hidden');
}

function _hideSelectionTooltip() {
  document.getElementById('selection-tooltip').classList.add('hidden');
}

// Calcule la plage de phrases couverte par une selection du navigateur.
// Retourne {startIdx, endIdx} ou null si la selection ne touche aucune phrase.
function _selectionSentenceRange(sel) {
  const startSpan = sel.anchorNode?.parentElement?.closest('.sentence-span')
    ?? sel.anchorNode?.parentElement;
  const endSpan = sel.focusNode?.parentElement?.closest('.sentence-span')
    ?? sel.focusNode?.parentElement;
  const a = startSpan?.dataset?.idx;
  const b = endSpan?.dataset?.idx;
  if (a === undefined || b === undefined) return null;
  const startIdx = Math.min(parseInt(a, 10), parseInt(b, 10));
  const endIdx   = Math.max(parseInt(a, 10), parseInt(b, 10));
  return { startIdx, endIdx };
}

document.getElementById('reader-content').addEventListener('mouseup', () => {
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || sel.toString().trim().length < 2) {
    _hideSelectionTooltip();
    return;
  }

  const range = _selectionSentenceRange(sel);

  // Desktop : on etend la selection au debut de la premiere phrase couverte
  // et a la fin de la derniere -- la selection est alors toujours un nombre
  // entier de phrases (jamais 1 seul mot au milieu d'une phrase), et la
  // lecture qui en decoulera devient previsible et reguliere.
  // Mobile : on laisse les poignees natives controler la selection (etendre
  // casserait le copier/coller du telephone) ; le bouton lira quand meme la
  // plage de phrases couvertes via _selectionSentenceRange.
  if (range && !_isTouchDevice) {
    const startSpan = document.querySelector('[data-idx="' + range.startIdx + '"]');
    const endSpan   = document.querySelector('[data-idx="' + range.endIdx + '"]');
    if (startSpan && endSpan) {
      const startText = startSpan.firstChild || startSpan;
      const endText   = endSpan.firstChild || endSpan;
      const newRange  = document.createRange();
      newRange.setStart(startText, 0);
      newRange.setEnd(endText, (endText.textContent || '').length);
      sel.removeAllRanges();
      sel.addRange(newRange);
    }
  }

  const rect = sel.getRangeAt(0).getBoundingClientRect();
  _showSelectionTooltip(rect);
});

// Sur mobile, la selection de texte est interceptee par le navigateur
// (long press -> menu natif copier/coller).
// Le TAP SIMPLE ne declenche PLUS la lecture (demande de Laurent, 15/09/2026) :
// il ouvre le panneau « voix de cette phrase », qui dit a qui appartient la
// voix et permet de la changer. Pour lire a partir d'une phrase, la selection
// longue + bouton « Lire a partir d'ici » reste disponible (voir plus haut).
// Les clics souris sont ignores (desktop) pour garder la selection de texte.
document.getElementById('reader-content').addEventListener('click', (e) => {
  if (!_isTouchDevice || e.pointerType === 'mouse') return;
  const span = e.target.closest('.sentence-span');
  if (!span) return;
  const idx = parseInt(span.dataset.idx, 10);
  if (Number.isNaN(idx)) return;

  // Fin d'une selection (longue pression) : le tap ne doit pas ouvrir le
  // panneau par-dessus, l'utilisateur visait le bouton du tooltip.
  const sel = window.getSelection();
  if (sel && !sel.isCollapsed && sel.toString().trim().length >= 2) return;

  _openVoicePanel(idx);
});

// Sur mobile, le tooltip "Lire a partir d'ici" s'affiche aussi au-dessus
// d'une selection longue (poignees natives du navigateur) : selectionchange
// est plus fiable que mouseup sur tactile. Le bouton fonctionne alors en
// lecture bornee, comme sur desktop.
document.addEventListener('selectionchange', () => {
  if (!_isTouchDevice) return;
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || sel.toString().trim().length < 2) {
    _hideSelectionTooltip();
    return;
  }
  const range = sel.getRangeAt(0);
  const node  = range.commonAncestorContainer;
  const inReader = (node.nodeType === 1 ? node : node.parentElement)
    ?.closest?.('#reader-content');
  if (!inReader) {
    _hideSelectionTooltip();
    return;
  }
  const rect = range.getBoundingClientRect();
  _showSelectionTooltip(rect);
});

document.addEventListener('mousedown', e => {
  if (!e.target.closest('#selection-tooltip')) _hideSelectionTooltip();
});

document.getElementById('read-from-here-btn').addEventListener('click', () => {
  const sel = window.getSelection();
  if (!sel) return;
  const range = _selectionSentenceRange(sel);
  _hideSelectionTooltip();
  sel.removeAllRanges();
  if (!range) return;

  _stopTTS();
  _setCursor(range.startIdx);

  // Selection sur plusieurs phrases : on lit exactement cette plage puis on
  // s'arrete (plus de lecture qui part "n'importe ou"). Selection sur une
  // seule phrase : lecture continue a partir d'elle, comportement historique.
  if (range.startIdx < range.endIdx) {
    _runTTS(range.startIdx, range.endIdx);
  } else {
    _startTTS();
  }
});

// ============================================================
// PANNEAU « VOIX DE LA PHRASE » (tap mobile / bouton du tooltip PC)
// ============================================================
// Demande de Laurent (15/09/2026) : sur mobile, un tap sur une phrase doit
// d'abord MONTRER a qui appartient la voix, et permettre de la changer -- il
// n'entraine donc plus la lecture. Sur PC, le meme panneau s'ouvre avec le
// bouton « Voir la voix » du tooltip de selection (a cote de « Lire a partir
// d'ici »), pour la phrase touchee par la selection.
//
// Le panneau ne fait que deux choses : dire qui parle, et changer SA voix. Il
// s'appuie sur ce qui existe deja : PUT /cast/voice via _updateCharacterVoice()
// (qui relance la lecture si elle tournait), le catalogue pour NOMMER la voix
// et la liste des voix proposees (_allVoices) pour la changer. Pour une phrase
// de NARRATION, il n'y a pas de personnage : c'est la voix du lecteur (menu du
// haut) qui est affichee et modifiee.

let _voicePhraseIdx = -1;      // phrase ouverte dans le panneau (-1 = ferme)
let _apercuVoixAudio = null;   // apercu sonore en cours (pour le couper au besoin)

// Coupe l'apercu en cours (comme _couperMessageHorsLigne pour le message
// « pas de reseau ») : deux apercus ne doivent jamais se superposer.
function _couperApercuVoix() {
  if (_apercuVoixAudio) {
    try { _apercuVoixAudio.pause(); } catch (e) { /* deja termine */ }
    _apercuVoixAudio = null;
  }
}

// Personnage d'une phrase : null quand c'est le narrateur (la phrase n'a pas de
// personnage attribue, elle est lue avec la voix du lecteur).
function _personnageDePhrase(idx) {
  const nom = _chapterSpeakers ? _chapterSpeakers[idx] : null;
  if (!nom || nom === 'narration') return null;
  return nom;
}

// Fiche de casting d'un personnage : { voice_id, rate, pitch, genre, ... }.
function _fichePersonnage(nom) {
  if (!nom || !_currentBookData || !_currentBookData.voices) return null;
  return _currentBookData.voices[nom] || null;
}

// Voix reellement utilisee pour une phrase (meme regle que _voiceForSentence).
function _voixDePhrase(idx) {
  const nom = _personnageDePhrase(idx);
  if (nom) {
    const fiche = _fichePersonnage(nom);
    if (fiche && fiche.voice_id) return fiche.voice_id;
  }
  const choix = document.getElementById('voice-select');
  return choix ? choix.value : '';
}

// Menu des voix : memes groupes que la fenetre du casting (Femmes / Hommes /
// Autres), pour retrouver ses reperes.
// Depuis le 19/09/2026, son libelle est celui des AUTRES menus (drapeaux, age,
// timbre et moteur) : demande de Laurent, « le meme affichage que dans le menu
// Casting des voix ». Le `typeof` protege le test node, qui isole cette
// fonction sans lui fournir `_libelleVoix`.
// `etatVoix` (19/09/2026) ajoute l'etat d'usage au libelle (« · LIBRE »,
// « · partagée (2) ») : c'est ici qu'on choisit, donc ici qu'on a besoin de
// savoir si la voix est libre. Facultatif (le test node ne le fournit pas).
function _remplirMenuVoixPhrase(select, voixId, etatVoix) {
  const usage = (!etatVoix || typeof etatVoix.marque !== 'function')
    ? () => '' : (id) => etatVoix.marque(id);
  select.innerHTML = '';
  const groupe = (etiquette, liste) => {
    if (!liste.length) return;
    const g = document.createElement('optgroup');
    g.label = etiquette;
    liste.forEach(v => {
      const o = document.createElement('option');
      o.value       = v.id;
      o.textContent = ((typeof _libelleVoix === 'function')
        ? _libelleVoix(v) : v.name + ' \u2014 ' + v.region) + usage(v.id);
      g.appendChild(o);
    });
    select.appendChild(g);
  };
  const parGenre = g => _allVoices
    .filter(v => (v.gender || '') === g)
    .sort((a, b) => a.name.localeCompare(b.name, 'fr'));

  groupe('\uD83D\uDC69 Femmes', parGenre('F'));
  groupe('\uD83D\uDC68 Hommes', parGenre('M'));
  groupe('Autres', _allVoices.filter(v => !v.gender));

  // Une voix attribuee mais NON proposee (moteur eteint) doit quand meme
  // s'afficher : sinon le menu montrerait l'air de rien une autre voix.
  if (voixId && !_allVoices.some(v => v.id === voixId)) {
    const g = document.createElement('optgroup');
    g.label = '\u26A0\uFE0F Voix actuelle';
    const o = document.createElement('option');
    o.value       = voixId;
    o.textContent = _libelleCatalogue(voixId) || voixId;
    g.appendChild(o);
    select.appendChild(g);
  }
  select.value = voixId || '';
}

function _openVoicePanel(sentIdx) {
  if (sentIdx < 0 || sentIdx >= _sentences.length) return;
  _voicePhraseIdx = sentIdx;

  const nom    = _personnageDePhrase(sentIdx);
  const fiche  = _fichePersonnage(nom);
  const voixId = _voixDePhrase(sentIdx);

  const texte = _sentences[sentIdx].text || '';
  document.getElementById('voice-phrase-extrait').textContent =
    (texte.length > 150 ? texte.slice(0, 147) + '...' : texte);

  document.getElementById('voice-phrase-personnage').textContent =
    nom ? nom : 'Narration';

  // La voix, nommee comme partout ailleurs (jamais un identifiant technique),
  // avec les reglages du personnage quand ils ne sont pas neutres.
  let info = _libelleCatalogue(voixId) || voixId;
  if (nom && fiche) {
    const reglages = [];
    if (fiche.rate  && fiche.rate  !== '+0%')  reglages.push('vitesse ' + fiche.rate);
    if (fiche.pitch && fiche.pitch !== '+0Hz') reglages.push('hauteur ' + fiche.pitch);
    if (reglages.length) info += ' (' + reglages.join(', ') + ')';
  }
  document.getElementById('voice-phrase-voix').textContent = info;

  document.getElementById('voice-phrase-label').textContent = nom
    ? 'Changer la voix de ' + nom + ' (toutes ses phrases)'
    : 'Changer la voix du lecteur';
  document.getElementById('voice-phrase-note').textContent = '';

  // Etat de la voix dans TOUT le livre : libre, prise par un personnage,
  // partagee, ou voix du narrateur. Ecrit en TEXTE PLEIN sous le menu, car sur
  // mobile il n'y a ni survol ni appui long pour aller le chercher (demande de
  // Laurent, 19/09/2026 : « je ne vois pas quelle voix est libre »).
  const etatVoix = _etatVoixLivre();
  _remplirMenuVoixPhrase(document.getElementById('voice-phrase-select'), voixId,
                         etatVoix);
  // `if` : la ligne peut manquer si le navigateur sert une page plus ancienne
  // que le script (cache) -- on ne veut jamais empecher le panneau de s'ouvrir.
  const ligneUsage = document.getElementById('voice-phrase-usage');
  if (ligneUsage) ligneUsage.textContent = etatVoix.phrase(voixId);

  // PORTE VERS LE CASTING (20/09/2026) : le panneau ne fait que changer une
  // voix ; pour le reste (cadenas 🔒, curseurs vitesse et hauteur, tiroir 🗣️ des
  // voix libres, badges d'etat), le bouton juste a cote ouvre la vraie fenetre
  // SUR ce personnage, mis en evidence.
  // Elle est CACHEE pour la NARRATION : le narrateur n'a pas de ligne dans le
  // casting (sa voix se change dans le menu du haut), le bouton n'aurait donc
  // rien a viser.
  // `if` : comme pour la ligne d'usage juste au-dessus, on ne veut jamais
  // empecher le panneau de s'ouvrir (page plus ancienne que le script, cache).
  const porteCasting = document.getElementById('voice-phrase-cast-btn');
  if (porteCasting) porteCasting.classList.toggle('hidden', !nom);

  document.getElementById('voice-phrase-panel').classList.remove('hidden');
}

function _closeVoicePanel() {
  _voicePhraseIdx = -1;
  _couperApercuVoix();
  document.getElementById('voice-phrase-panel').classList.add('hidden');
}

// Apercu : la voix choisie dit un extrait de LA phrase ouverte, avec les
// reglages du personnage (ou la vitesse du lecteur pour la narration).
async function _apercuVoixPhrase() {
  if (_voicePhraseIdx < 0) return;
  const idx   = _voicePhraseIdx;
  const btn   = document.getElementById('voice-phrase-ecouter-btn');
  const note  = document.getElementById('voice-phrase-note');
  const voix  = document.getElementById('voice-phrase-select').value;
  const nom   = _personnageDePhrase(idx);
  const fiche = _fichePersonnage(nom);
  const vitesse = document.getElementById('speed-select');
  const rate  = (nom && fiche && fiche.rate)  ? fiche.rate
              : (vitesse ? vitesse.value : '+0%');
  const pitch = (nom && fiche && fiche.pitch) ? fiche.pitch : '+0Hz';
  const texte = (((_sentences[idx] || {}).text) || 'Bonjour.').slice(0, 120);

  btn.disabled = true;
  const avant = btn.textContent;
  btn.textContent = '\u23F3';
  note.textContent = '';
  _couperApercuVoix();
  try {
    const res = await fetch('/api/tts', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ text: texte, voice: voix, rate: rate, pitch: pitch })
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const url   = URL.createObjectURL(await res.blob());
    const audio = new Audio(url);
    _apercuVoixAudio = audio;
    audio.addEventListener('ended', () => {
      _apercuVoixAudio = null;
      URL.revokeObjectURL(url);
    });
    audio.play().catch(() => {});
  } catch (e) {
    // Moteur eteint, voix indisponible... : on le dit sans bloquer le panneau.
    note.textContent = 'Aperçu indisponible pour cette voix.';
    console.error('Erreur apercu voix phrase:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = avant;
  }
}

document.getElementById('voice-phrase-ecouter-btn')
  .addEventListener('click', _apercuVoixPhrase);

document.getElementById('voice-phrase-close-btn')
  .addEventListener('click', _closeVoicePanel);

// PORTE VERS LE CASTING (20/09/2026, demande de Laurent : « cette modale est
// moins riche que casting des voix »). Le panneau ne change qu'UNE voix ; pour
// le reste, on ouvre la vraie fenetre SUR le personnage, mis en evidence.
// Trois precautions :
//   - la NARRATION n'a pas de ligne dans le casting : le bouton est cache (voir
//     _openVoicePanel), et ce garde-fou evite un clic dans le vide ;
//   - on FERME le panneau avant d'ouvrir : jamais deux fenetres empilees, et on
//     retrouve sa lecture en fermant le casting ;
//   - la porte ramene TOUJOURS au personnage : si un filtre d'etat (« a
//     caster », « voix partagee », « voix libres ») ou la recherche le cachait,
//     on revient d'abord a la liste complete. Sans cela, la fenetre s'ouvrirait
//     sans rien montrer -- et sans que rien n'explique pourquoi.
// Le surlignage reutilise _allerAuPersonnage : c'est EXACTEMENT le reperage des
// noms cliquables du badge « partagee avec ... » (19/09/2026), rien de nouveau
// a apprendre.
document.getElementById('voice-phrase-cast-btn').addEventListener('click', async () => {
  const nom = _personnageDePhrase(_voicePhraseIdx);
  if (!nom) return;
  _closeVoicePanel();
  if (_castEtatFiltre !== 'T' || _castRecherche.trim()) {
    _castEtatFiltre = 'T';
    _castRecherche = '';
  }
  await _openCastModal();
  _allerAuPersonnage(nom);
});

// Taper a cote de la feuille ferme le panneau (le fond couvre l'ecran).
document.getElementById('voice-phrase-panel').addEventListener('click', (e) => {
  if (e.target.id === 'voice-phrase-panel') _closeVoicePanel();
});

// Changement de voix : applique tout de suite. Pour un personnage, c'est sa
// voix dans TOUT le livre (comme la fenetre du casting) -- et
// _updateCharacterVoice relance la lecture si elle tournait ; pour la
// narration, c'est la voix du lecteur (le menu du haut).
document.getElementById('voice-phrase-select').addEventListener('change', async (e) => {
  if (_voicePhraseIdx < 0) return;
  const idx  = _voicePhraseIdx;
  const voix = e.target.value;
  const nom  = _personnageDePhrase(idx);
  const note = document.getElementById('voice-phrase-note');

  if (nom) {
    const fiche = _fichePersonnage(nom);
    const rate  = (fiche && fiche.rate)  || '+0%';
    const pitch = (fiche && fiche.pitch) || '+0Hz';
    note.textContent = 'Enregistrement...';
    const ok = await _updateCharacterVoice(nom, voix, rate, pitch);
    note.textContent = ok
      ? 'Voix changée pour ' + nom + ' (toutes ses phrases).'
      : 'Le changement n\'a pas pu être enregistré.';
  } else {
    const sel = document.getElementById('voice-select');
    if (sel) {
      sel.value = voix;
      // On PREVIENT le menu du haut (19/09/2026) : l'enregistrement pour ce
      // livre part de SON gestionnaire 'change'. Sans cela, changer la voix du
      // narrateur depuis ce panneau n'etait pas retenu apres un rechargement
      // (defaut trouve en corrigeant le rafraichissement du casting).
      sel.dispatchEvent(new Event('change'));
    }
    // La playlist de lecture est construite au lancement : sans ce qui suit,
    // la suite du chapitre garderait l'ancienne voix (meme regle que pour un
    // personnage, decision du 15/09/2026).
    if (_ttsState === 'playing' || _ttsState === 'loading') {
      _stopTTS();
      _startTTS();
    }
    note.textContent = 'Voix du lecteur changée.';
  }

  document.getElementById('voice-phrase-voix').textContent =
    _libelleCatalogue(voix) || voix;
  // L'etat de la voix choisie se met a jour tout de suite : c'est la reponse a
  // « est-elle libre ? » au moment precis ou l'on change de voix.
  const etatVoix = _etatVoixLivre();
  const ligneUsage = document.getElementById('voice-phrase-usage');
  if (ligneUsage) ligneUsage.textContent = etatVoix.phrase(voix);

  // La fenetre du casting, si elle est ouverte derriere, doit suivre elle aussi
  // (badges de partage, marques « libre », tiroir des voix libres) : sinon elle
  // garderait le calcul fait a son ouverture -- meme defaut que ci-dessus.
  await _rafraichirCastingApresChangement();
});

// PC : bouton « Voir la voix » du tooltip de selection -- ouvre le panneau sur
// la premiere phrase couverte par la selection (comme « Lire a partir d'ici »).
document.getElementById('show-voice-btn').addEventListener('click', () => {
  const sel   = window.getSelection();
  const range = sel ? _selectionSentenceRange(sel) : null;
  _hideSelectionTooltip();
  if (sel) sel.removeAllRanges();
  if (range) _openVoicePanel(range.startIdx);
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') _closeVoicePanel();
});

function setTTSUI(state) {
  const btn   = document.getElementById('tts-play-btn');
  const play  = document.getElementById('icon-play');
  const pause = document.getElementById('icon-pause');
  const spin  = document.getElementById('icon-spin');
  btn.className = state === 'playing' ? 'playing'
                : state === 'loading' ? 'loading'
                : state === 'paused'  ? 'paused'
                : '';
  play.classList.toggle('hidden',  state !== 'idle' && state !== 'paused');
  pause.classList.toggle('hidden', state !== 'playing');
  spin.classList.toggle('hidden',  state !== 'loading');
  // Le lecteur integre, s'il est ouvert, suit le MEME etat (son bouton de
  // lecture ne doit jamais montrer ▶️ pendant que ca joue).
  if (typeof _majLecteurEtat === 'function') _majLecteurEtat(state);
}

// ============================================================
// INSTALLER L'APPLICATION (PWA) — 20/09/2026
// ============================================================
// Pourquoi : Laurent cherchait l'option « Installer » dans Chrome sans la
// trouver (Chrome ne la propose qu'a certaines conditions, et ne dit JAMAIS
// pourquoi il refuse). Ce bouton sert dans les deux cas :
//   - le navigateur sait installer (Chromium) : il declenche SA fenetre
//     d'installation, sans avoir a chercher l'icone dans la barre d'adresse ;
//   - il ne propose rien (Firefox, ou navigateur qui ne juge pas l'application
//     installable) : le bouton EXPLIQUE ou chercher, au lieu de ne rien faire.
// Le bouton disparait quand l'application tourne DEJA comme une application
// installee (`display-mode: standalone`).

let _inviteInstallation = null;   // l'invitation du navigateur, gardee pour le clic

window.addEventListener('beforeinstallprompt', (e) => {
  // On empeche la mini-banniere automatique du navigateur : c'est NOTRE bouton
  // qui propose, au moment ou Laurent est dans l'application.
  e.preventDefault();
  _inviteInstallation = e;
});

window.addEventListener('appinstalled', () => {
  _inviteInstallation = null;
  const btn  = document.getElementById('installer-btn');
  const note = document.getElementById('installer-note');
  if (btn) btn.classList.add('hidden');
  if (note) {
    note.textContent = 'Application installée : ouvre-la depuis son icône '
      + '(elle s\'ouvrira en plein écran, sans les barres du navigateur).';
    note.classList.remove('hidden');
  }
});

// L'application tourne-t-elle DEJA comme une application installee ?
function _applicationInstallee() {
  const modeApp = (typeof window.matchMedia === 'function')
    && window.matchMedia('(display-mode: standalone)').matches;
  return !!modeApp || window.navigator.standalone === true;
}

// L'appareil est-il un telephone / une tablette ? Le bouton d'installation n'a
// pas de raison d'apparaitre sur un ORDINATEUR (les navigateurs y proposent deja
// l'installation dans leur barre d'adresse) : constat de Laurent, 20/09/2026
// (« elle s'affiche maintenant sur la version PC »). Fonction PURE : verifiee par
// test_voix/test_navigateur.js.
function _appareilMobile(userAgent, tactile, largeur) {
  const ua = userAgent
    || (typeof navigator !== 'undefined' ? (navigator.userAgent || '') : '');
  if (/Android|iPhone|iPad|iPod|Mobile/i.test(ua)) return true;
  // Les iPad recents se declarent comme un Mac : ils ont le toucher et un petit
  // ecran, ce qui suffit a les reconnaitre (et evite de priver un ordinateur
  // tactile grand ecran de... rien du tout, puisque le navigateur s'en charge).
  const toucher = (tactile !== undefined) ? tactile
    : (typeof navigator !== 'undefined' && navigator.maxTouchPoints > 1);
  const petit = (largeur !== undefined) ? largeur
    : (typeof window !== 'undefined' ? window.innerWidth : 0);
  return !!(toucher && petit > 0 && petit <= 900);
}

function _majBoutonInstaller() {
  const btn = document.getElementById('installer-btn');
  if (!btn) return;
  // Deux raisons de ne PAS montrer ce bouton : l'application est deja installee,
  // ou on est sur un ordinateur.
  btn.classList.toggle('hidden',
                       _applicationInstallee() || !_appareilMobile());
}

// Nom du navigateur en cours : on le DIT quand l'installation coince, parce que
// Laurent ne pouvait pas savoir dans lequel il se trouvait (constat du
// 20/09/2026 : une application installee n'affiche AUCUNE barre d'adresse, donc
// rien ne dit qui l'heberge). Fonction PURE (elle ne lit que la chaine du
// navigateur) : verifiee par test_voix/test_navigateur.js.
// Ordre important : Brave et Edge se presentent comme « Chrome » dans leur
// chaine, il faut donc les reconnaitre AVANT.
function _nomNavigateur(userAgent) {
  const ua = userAgent
    || (typeof navigator !== 'undefined' ? (navigator.userAgent || '') : '');
  if (typeof navigator !== 'undefined' && navigator.brave) return 'Brave';
  if (/Firefox|FxiOS/i.test(ua)) return 'Firefox';
  if (/EdgA|Edg\//i.test(ua))    return 'Edge';
  if (/OPR|Opera/i.test(ua))     return 'Opera';
  if (/Chrome|CriOS/i.test(ua))  return 'Chrome';
  if (/Safari/i.test(ua))        return 'Safari';
  return 'ce navigateur';
}

async function _proposerInstallation() {
  const note = document.getElementById('installer-note');
  if (!_inviteInstallation) {
    // Le navigateur n'a rien propose : on dit OU chercher, et POURQUOI il n'y a
    // rien -- la cause n° 1 (constat de Laurent, 20/09/2026) est qu'on est dans
    // le navigateur INTEGRE d'une autre application (un lien ouvert depuis NIMM
    // ou depuis le launcher, par exemple) : ces fenetres ne savent PAS installer
    // d'application, et c'est une limite d'Android, pas un defaut de l'atelier.
    // On NOMME aussi le navigateur en cours : rien d'autre ne le dit a l'ecran
    // quand l'application installée n'a plus de barre d'adresse.
    if (note) {
      note.textContent = 'Installation non proposée ici (tu es dans '
        + _nomNavigateur() + '). Deux causes possibles : (1) tu es dans le '
        + 'navigateur INTÉGRÉ à une autre application (page ouverte depuis NIMM '
        + 'ou le launcher) : ces fenêtres ne savent pas installer — ouvre '
        + 'l\'adresse directement dans Chrome ou Brave ; (2) sinon, ouvre son menu '
        + '(⋮) puis « Installer l\'application ». (Firefox, lui, n\'installe '
        + 'qu\'un raccourci.)';
      note.classList.remove('hidden');
    }
    return;
  }
  _inviteInstallation.prompt();
  const choix = await _inviteInstallation.userChoice;
  _inviteInstallation = null;
  if (note && choix && choix.outcome === 'dismissed') {
    note.textContent = 'Installation annulée : tu peux la reprendre quand tu veux.';
    note.classList.remove('hidden');
  }
}

document.getElementById('installer-btn').addEventListener('click', _proposerInstallation);
_majBoutonInstaller();

// ============================================================
// NAVIGATION VUES
// ============================================================

function showView(name) {
  const profile = document.getElementById('view-profile');
  const lib     = document.getElementById('view-library');
  const reader  = document.getElementById('view-reader');
  const rsvp    = document.getElementById('view-rsvp');
  profile.classList.toggle('hidden', name !== 'profile');
  profile.classList.toggle('active', name === 'profile');
  lib.classList.toggle('hidden', name !== 'library');
  lib.classList.toggle('active', name === 'library');
  reader.classList.toggle('hidden', name !== 'reader');
  reader.classList.toggle('active', name === 'reader');
  rsvp.classList.toggle('hidden', name !== 'rsvp');
  rsvp.classList.toggle('active', name === 'rsvp');
}

// ============================================================
// PANNEAU CHAPITRES
// ============================================================

function openChaptersPanel()  {
  document.getElementById('chapters-panel').classList.remove('hidden');
}
function closeChaptersPanel() {
  document.getElementById('chapters-panel').classList.add('hidden');
}

// ============================================================
// ONGLETS (marque-pages de lecture) — 19/09/2026
// ============================================================
// Demande de Laurent : « actuellement si je vais a un endroit du livre, l'endroit
// est le dernier visite, mais j'aimerais bien pouvoir me faire une liste
// d'onglets ». La reprise de lecture continue de garder le DERNIER endroit : ces
// marques viennent EN PLUS, par livre et par profil.

let _onglets = [];                       // les onglets du livre ouvert

// Un extrait court d'une phrase, pour reconnaitre l'endroit dans la liste.
function _extraitPhrase(idx) {
  const item = (_sentences && _sentences[idx]) ? _sentences[idx] : null;
  const texte = item ? String(item.text || '') : '';
  const propre = texte.replace(/\s+/g, ' ').trim();
  return propre.length > 70 ? propre.slice(0, 70) + '\u2026' : propre;
}

async function _chargerOnglets() {
  if (!_currentBookId) return [];
  try {
    const res = await fetch('/api/bookmarks/' + _currentBookId
                            + '?user_id=' + _currentUserId);
    if (res.status === 404) {
      // Le serveur qui repond est une ANCIENNE version (lancee avant que les
      // onglets existent) : le dire clairement, sinon on croit que le bouton ne
      // marche pas. Constat de Laurent, 19/09/2026.
      _noteOnglets('\u26A0\uFE0F Le serveur doit \u00eatre red\u00e9marr\u00e9 '
                   + '(fermer le lecteur, puis START.bat).');
      _onglets = [];
      return _onglets;
    }
    if (res.ok) _onglets = (await res.json()) || [];
  } catch (e) {
    console.error('Erreur chargement des onglets:', e);
    _onglets = [];
  }
  return _onglets;
}

// Le petit mot sous la liste (« Onglet pose », « serveur a redemarrer »...).
function _noteOnglets(texte) {
  const note = document.getElementById('bookmarks-note');
  if (note) note.textContent = texte;
}

function _renderOnglets() {
  const list = document.getElementById('bookmarks-list');
  const vide = document.getElementById('bookmarks-vide');
  list.innerHTML = '';
  vide.classList.toggle('hidden', _onglets.length > 0);
  _onglets.forEach(onglet => {
    const li = document.createElement('li');
    li.className = 'bookmark-item';

    const label = document.createElement('span');
    label.className   = 'bookmark-label';
    label.textContent = onglet.label || ('Chapitre ' + (onglet.chapter_index + 1));

    const supprimer = document.createElement('button');
    supprimer.type      = 'button';
    supprimer.className = 'bookmark-del-btn';
    supprimer.textContent = '\u2715';
    supprimer.title     = 'Supprimer cet onglet';
    supprimer.addEventListener('click', (ev) => {
      ev.stopPropagation();           // sinon le clic ouvrirait l'onglet
      _supprimerOnglet(onglet.id);
    });

    li.appendChild(label);
    li.appendChild(supprimer);
    li.addEventListener('click', () => {
      closeBookmarksPanel();
      loadChapter(onglet.chapter_index, 0, onglet.cursor_idx || 0);
    });
    list.appendChild(li);
  });
}

async function _marquerCetEndroit() {
  if (!_currentBookId) return;
  const bouton = document.getElementById('bookmark-add-btn');
  bouton.disabled = true;
  _noteOnglets('');
  const extrait = _extraitPhrase(_cursorIdx);
  const label = 'Chapitre ' + (_currentChapter + 1)
    + (extrait ? ' \u2014 ' + extrait : '');
  try {
    const res = await fetch('/api/bookmarks/' + _currentBookId
                            + '?user_id=' + _currentUserId, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ chapter_index: _currentChapter,
                                cursor_idx: _cursorIdx, label: label })
    });
    if (!res.ok) {
      // 404 = le serveur qui repond est une ANCIENNE version, lancee avant que
      // les onglets existent : le dire clairement (constat de Laurent,
      // 19/09/2026), sinon on croit que le bouton ne marche pas.
      _noteOnglets(res.status === 404
        ? '\u26A0\uFE0F Le serveur doit \u00eatre red\u00e9marr\u00e9 '
          + '(fermer le lecteur, puis START.bat).'
        : '\u26A0\uFE0F Impossible de poser l\u2019onglet (HTTP '
          + res.status + ').');
      return;
    }
    await _chargerOnglets();
    _renderOnglets();
    _noteOnglets('Onglet pos\u00e9.');
  } catch (e) {
    console.error('Erreur pose onglet:', e);
    _noteOnglets('\u26A0\uFE0F Impossible de poser l\u2019onglet.');
  } finally {
    bouton.disabled = false;
  }
}

async function _supprimerOnglet(identifiant) {
  if (!_currentBookId) return;
  try {
    await fetch('/api/bookmarks/' + _currentBookId + '/' + identifiant
                + '?user_id=' + _currentUserId, { method: 'DELETE' });
    await _chargerOnglets();
    _renderOnglets();
  } catch (e) {
    console.error('Erreur suppression onglet:', e);
  }
}

async function openBookmarksPanel() {
  document.getElementById('bookmarks-note').textContent = '';
  document.getElementById('bookmarks-panel').classList.remove('hidden');
  await _chargerOnglets();
  _renderOnglets();
}
function closeBookmarksPanel() {
  document.getElementById('bookmarks-panel').classList.add('hidden');
}

// ============================================================
// PROGRESSION
// ============================================================

function saveProgress() {
  if (!_currentBookId) return;
  const scroll = Math.round(
    document.getElementById('reader-content').scrollTop
  );
  fetch('/api/progress/' + _currentBookId + '?user_id=' + _currentUserId, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ chapter_index: _currentChapter, scroll_position: scroll, cursor_idx: _cursorIdx })
  }).catch(() => {});
}

document.getElementById('reader-content').addEventListener('scroll', () => {
  clearTimeout(_progressTimer);
  _progressTimer = setTimeout(saveProgress, 5000);
});

// ============================================================
// TEMPS DE LECTURE RESTANT
// ============================================================

function _getWPM() {
  const rate = document.getElementById('speed-select').value;
  const pct  = parseInt(rate, 10) || 0;
  return Math.round(150 * (1 + pct / 100));
}

function _formatDuration(wordCount) {
  const minutes = Math.round(wordCount / _getWPM());
  if (minutes < 1)  return '< 1 min';
  if (minutes < 60) return minutes + ' min';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? h + 'h ' + m + 'min' : h + 'h';
}

function _updateTimeRemaining() {
  const el = document.getElementById('tts-time-remaining');
  if (!el || !_currentBookData || _sentences.length === 0) return;

  const wordsNow = _sentences
    .slice(_cursorIdx)
    .reduce((acc, s) => acc + s.text.split(/\s+/).length, 0);

  let wordsAfter = 0;
  for (let i = _currentChapter + 1; i < _currentBookData.chapters.length; i++) {
    wordsAfter += _currentBookData.chapters[i].word_count || 0;
  }

  const minutes = Math.round((wordsNow + wordsAfter) / _getWPM());
  if (minutes < 1)       el.textContent = '< 1 min';
  else if (minutes < 60) el.textContent = '~' + minutes + ' min';
  else {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    el.textContent = m > 0 ? '~' + h + 'h ' + m + 'min' : '~' + h + 'h';
  }
}

// ============================================================
// MODE RSVP
// ============================================================

function _rsvpBuildWords() {
  // Reconstruit la liste de mots a plat depuis _sentences, en
  // associant chaque mot a l'index de phrase auquel il appartient
  _rsvpWords = [];
  _sentences.forEach((s, sentIdx) => {
    const words = s.text.split(/\s+/).filter(w => w.length > 0);
    words.forEach((w, i) => {
      _rsvpWords.push({
        text: w,
        sentIdx: sentIdx,
        isLastOfSentence: i === words.length - 1
      });
    });
  });
}

function _rsvpFindStartWordIdx(cursorSentIdx) {
  const idx = _rsvpWords.findIndex(w => w.sentIdx === cursorSentIdx);
  return idx === -1 ? 0 : idx;
}

function _rsvpPivotIndex(word) {
  // 2eme lettre du mot (1ere si mot d'1 seul caractere)
  return word.length <= 1 ? 0 : 1;
}

function _rsvpRenderWord(word) {
  const pivot = _rsvpPivotIndex(word);
  const before = word.slice(0, pivot);
  const letter = word.charAt(pivot);
  const after  = word.slice(pivot + 1);
  const el = document.getElementById('rsvp-word');
  el.innerHTML = _escapeHtml(before) +
    '<span class="rsvp-pivot">' + _escapeHtml(letter) + '</span>' +
    _escapeHtml(after);

  // Positionne le mot pour que la lettre pivot tombe sur le marqueur fixe
  requestAnimationFrame(() => {
    const pivotSpan = el.querySelector('.rsvp-pivot');
    if (!pivotSpan) return;
    const wordRect  = el.getBoundingClientRect();
    const pivotRect = pivotSpan.getBoundingClientRect();
    const offset    = (pivotRect.left + pivotRect.width / 2) - wordRect.left;
    el.style.marginLeft = (-offset) + 'px';
  });
}

function _escapeHtml(s) {
  return s.replace(/&/g, '&').replace(/</g, '<').replace(/>/g, '>');
}

function _rsvpGetWPM() {
  return parseInt(document.getElementById('rsvp-speed-slider').value, 10) || 160;
}

function _rsvpStepDelay() {
  return 60000 / _rsvpGetWPM();
}

function _rsvpScheduleNext() {
  clearTimeout(_rsvpTimer);
  const current = _rsvpWords[_rsvpWordIdx];
  let extraPause = 0;
  if (current) {
    if (RSVP_PUNCT_STRONG.test(current.text))      extraPause = 300;
    else if (RSVP_PUNCT_COMMA.test(current.text))  extraPause = 200;
  }
  _rsvpTimer = setTimeout(() => {
    if (!_rsvpPressed) return;
    _rsvpAdvance();
  }, _rsvpStepDelay() + extraPause);
}

function _rsvpAdvance() {
  if (_rsvpWordIdx >= _rsvpWords.length - 1) {
    _rsvpStop();
    return;
  }
  _rsvpWordIdx++;
  const w = _rsvpWords[_rsvpWordIdx];
  _rsvpRenderWord(w.text);
  _setCursor(w.sentIdx);
  _rsvpScheduleNext();
}

function _rsvpToggle() {
  if (_rsvpPressed) {
    _rsvpStop();
  } else {
    _rsvpStart();
  }
}

function _rsvpStart() {
  if (_rsvpWords.length === 0) return;
  _rsvpPressed = true;
  clearTimeout(_rsvpFadeTimer);
  document.getElementById('rsvp-fade-text').classList.remove('visible');
  const btn = document.getElementById('rsvp-push-btn');
  btn.classList.add('active');
  btn.textContent = 'Arrêter';

  const w = _rsvpWords[_rsvpWordIdx];
  if (w) {
    _rsvpRenderWord(w.text);
    _setCursor(w.sentIdx);
  }
  _rsvpScheduleNext();
}

function _rsvpStop() {
  _rsvpPressed = false;
  clearTimeout(_rsvpTimer);
  const btn = document.getElementById('rsvp-push-btn');
  btn.classList.remove('active');
  btn.textContent = 'Lancer la lecture';
  _rsvpShowFadeContext();
}

function _rsvpShowFadeContext() {
  const w = _rsvpWords[_rsvpWordIdx];
  if (!w) return;

  const sentIdx = w.sentIdx;

  // Mots de la phrase courante uniquement
  const sentWords    = _rsvpWords.filter(x => x.sentIdx === sentIdx);
  const curPosInSent = sentWords.findIndex(x => x === w);

  const fadeEl = document.getElementById('rsvp-fade-text');
  fadeEl.innerHTML = '';

  // Phrase complete affichee en continu, avec la lettre pivot
  // du mot en cours mise en rouge (meme logique que le mot RSVP)
  sentWords.forEach((sw, i) => {
    if (i === curPosInSent) {
      const pivot  = _rsvpPivotIndex(sw.text);
      const before = sw.text.slice(0, pivot);
      const letter = sw.text.charAt(pivot);
      const after  = sw.text.slice(pivot + 1);

      const span = document.createElement('span');
      span.innerHTML = _escapeHtml(before) +
        '<span class="rsvp-fade-pivot">' + _escapeHtml(letter) + '</span>' +
        _escapeHtml(after);
      fadeEl.appendChild(span);
    } else {
      fadeEl.appendChild(document.createTextNode(sw.text));
    }
    if (i < sentWords.length - 1) fadeEl.appendChild(document.createTextNode(' '));
  });

  requestAnimationFrame(() => fadeEl.classList.add('visible'));
}

function openRSVP() {
  _stopTTS();
  _rsvpBuildWords();
  if (_rsvpWords.length === 0) return;
  _rsvpWordIdx = _rsvpFindStartWordIdx(_cursorIdx);

  const w = _rsvpWords[_rsvpWordIdx];
  _rsvpRenderWord(w.text);
  document.getElementById('rsvp-fade-text').classList.remove('visible');
  document.getElementById('rsvp-push-btn').classList.remove('active');

  showView('rsvp');
}

function closeRSVP() {
  _rsvpStop();
  showView('reader');
  saveProgress();
}

// ============================================================
// RECHERCHE DANS LE LIVRE
// ============================================================

function _normalizeSearch(s) {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

async function _runSearch() {
  const input = document.getElementById('search-input');
  const q = input.value.trim();
  if (!q || !_currentBookId || _searchInFlight) return;

  _searchInFlight = true;
  const list = document.getElementById('search-results-list');
  list.innerHTML = '<li class="search-empty-state">Recherche en cours...</li>';
  list.classList.remove('hidden');
  document.getElementById('chapters-list').classList.add('hidden');

  try {
    const res = await fetch('/api/books/' + _currentBookId + '/search?q=' + encodeURIComponent(q) + '&user_id=' + _currentUserId);
    const data = await res.json();
    _searchResults = data.results || [];
    _renderSearchResults(q);
  } catch (e) {
    console.error('Erreur recherche:', e);
    list.innerHTML = '<li class="search-empty-state">Erreur lors de la recherche.</li>';
  } finally {
    _searchInFlight = false;
  }
}

function _renderSearchResults(query) {
  const list  = document.getElementById('search-results-list');
  const info  = document.getElementById('search-results-info');
  const count = document.getElementById('search-results-count');

  info.classList.remove('hidden');
  count.textContent = _searchResults.length +
    (_searchResults.length === 1 ? ' resultat' : ' resultats');

  list.innerHTML = '';

  if (_searchResults.length === 0) {
    list.innerHTML = '<li class="search-empty-state">Aucun resultat pour "' + query + '".</li>';
    return;
  }

  const normQuery = _normalizeSearch(query);

  _searchResults.forEach(r => {
    const li = document.createElement('li');
    li.className = 'search-result-item';

    const chapEl = document.createElement('span');
    chapEl.className   = 'search-result-chapter';
    chapEl.textContent = r.chapter_title;

    const ctxEl = document.createElement('div');
    ctxEl.className = 'search-result-context';
    ctxEl.innerHTML = _highlightMatch(r.sentence_text, normQuery);

    li.appendChild(chapEl);
    li.appendChild(ctxEl);

    li.addEventListener('click', () => _goToSearchResult(r));
    list.appendChild(li);
  });
}

function _highlightMatch(sentence, normQuery) {
  const words = sentence.split(/(\s+)/);
  return words.map(w => {
    const cleaned = _normalizeSearch(w.replace(/[.,!?;:»"'…]/g, ''));
    if (cleaned === normQuery) {
      return '<mark>' + w + '</mark>';
    }
    return w;
  }).join('');
}

async function _goToSearchResult(result) {
  closeChaptersPanel();
  _clearSearch();

  await loadChapter(result.chapter_index, 0, 0);

  // Cherche la phrase correspondante dans _sentences une fois le chapitre charge
  const idx = _sentences.findIndex(s => s.text === result.sentence_text);
  if (idx !== -1) {
    _setCursor(idx);
  }
}

function _clearSearch() {
  _searchResults = [];
  document.getElementById('search-input').value = '';
  document.getElementById('search-results-list').classList.add('hidden');
  document.getElementById('search-results-list').innerHTML = '';
  document.getElementById('search-results-info').classList.add('hidden');
  document.getElementById('chapters-list').classList.remove('hidden');
}

// ============================================================
// LISTE DES CHAPITRES
// ============================================================

function renderChaptersList() {
  const list = document.getElementById('chapters-list');
  list.innerHTML = '';
  if (!_currentBookData || !_currentBookData.chapters) return;

  _currentBookData.chapters.forEach((ch, i) => {
    const li = document.createElement('li');
    li.className = 'chapter-item' + (i === _currentChapter ? ' active' : '');

    const num = document.createElement('span');
    num.className   = 'chapter-num';
    num.textContent = i + 1;

    const label = document.createElement('span');
    label.className   = 'chapter-label';
    label.textContent = ch.title || 'Chapitre ' + (i + 1);

    const dur = document.createElement('span');
    dur.className   = 'chapter-dur';
    dur.textContent = ch.word_count ? _formatDuration(ch.word_count) : '';

    li.appendChild(num);
    li.appendChild(label);
    li.appendChild(dur);
    li.addEventListener('click', () => {
      closeChaptersPanel();
      loadChapter(i, 0);
    });

    list.appendChild(li);
  });
}

// ============================================================
// BINDINGS
// ============================================================

function bindEvents() {
  document.getElementById('back-btn').addEventListener('click', () => {
    _stopTTS();
    saveProgress();
    showView('library');
    loadLibrary();
  });

  document.getElementById('prev-btn').addEventListener('click', () => {
    if (_currentChapter > 0) loadChapter(_currentChapter - 1, 0);
  });
  document.getElementById('next-btn').addEventListener('click', () => {
    if (_currentChapter < _totalChapters - 1) loadChapter(_currentChapter + 1, 0);
  });

  document.getElementById('tts-play-btn').addEventListener('click', () => toggleTTS());

  // Curseur glitch — navigation (barre refaite le 20/09/2026, demande de
  // Laurent) : SIX fleches symetriques, et TROIS niveaux de saut --
  //   ⏮ / ⏭  chapitre precedent / suivant ;
  //   ⏪ / ⏩  saut MOYEN : _PAS_PARAGRAPHES paragraphes d'un coup ;
  //   ◀ / ▶  phrase precedente / suivante (le pas fin).
  // Pourquoi le saut moyen existe (motif de Laurent) : « le saut de paragraphe
  // correspond tres souvent a un saut de phrase » -- un saut d'UN paragraphe ne
  // se distinguait donc pas d'un saut de phrase ; en sautant plusieurs
  // paragraphes, les trois niveaux sont vraiment distincts.
  // Les fonctions `_cursorSentPrev/Next` sont aussi celles du CASQUE
  // (`navigator.mediaSession`, previoustrack/nexttrack) : le pas du casque et
  // celui des fleches ◀/▶ restent ainsi identiques.
  document.getElementById('sent-prev-btn').addEventListener('click', _cursorSentPrev);
  document.getElementById('sent-next-btn').addEventListener('click', _cursorSentNext);
  document.getElementById('para-prev-btn')
    .addEventListener('click', () => _cursorParaPrev(_PAS_PARAGRAPHES));
  document.getElementById('para-next-btn')
    .addEventListener('click', () => _cursorParaNext(_PAS_PARAGRAPHES));

  document.getElementById('chapters-btn').addEventListener('click', openChaptersPanel);
  document.getElementById('chapters-close-btn').addEventListener('click', closeChaptersPanel);
  document.getElementById('chapters-backdrop').addEventListener('click', closeChaptersPanel);

  // Onglets de lecture (19/09/2026) : ouvrir la liste, la fermer, en poser un.
  document.getElementById('bookmarks-open-btn').addEventListener('click', openBookmarksPanel);
  document.getElementById('bookmarks-close-btn').addEventListener('click', closeBookmarksPanel);
  document.getElementById('bookmarks-backdrop').addEventListener('click', closeBookmarksPanel);
  document.getElementById('bookmark-add-btn').addEventListener('click', _marquerCetEndroit);

  document.getElementById('search-btn').addEventListener('click', _runSearch);
  document.getElementById('search-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') _runSearch();
  });
  document.getElementById('search-clear-btn').addEventListener('click', _clearSearch);

  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    closeChaptersPanel();
    _fermerReparerModal();
    document.getElementById('delete-modal').classList.add('hidden');
  });

  document.getElementById('speed-select').addEventListener('change', () => {
    _updateTimeRemaining();
  });

  document.getElementById('multivoice-btn').addEventListener('click', _onMultivoiceBtnClick);

  // --- RSVP ---
  document.getElementById('rsvp-open-btn').addEventListener('click', openRSVP);
  document.getElementById('rsvp-close-btn').addEventListener('click', closeRSVP);

  const pushBtn = document.getElementById('rsvp-push-btn');
  pushBtn.addEventListener('click', () => _rsvpToggle());

  const speedSlider = document.getElementById('rsvp-speed-slider');
  speedSlider.addEventListener('input', () => {
    document.getElementById('rsvp-speed-label').textContent = speedSlider.value + ' mots/min';
  });

  // --- Réparer les moteurs de voix (21/09/2026) ---
  // Le voyant du bas de la fenetre de lecture ouvre le panneau. Il ne CHANGE
  // plus de moteur (choix de Laurent : la bascule se fait sur le PC, par le
  // lanceur de chaque moteur) : il ne sait que RALLUMER ce qui s'est eteint.
  // Aucun geste de ce panneau ne peut donc eteindre un moteur par erreur.
  document.getElementById('reparer-open-btn').addEventListener('click', _ouvrirReparerModal);
  document.getElementById('reparer-cancel-btn').addEventListener('click', _fermerReparerModal);
  document.getElementById('reparer-modal').addEventListener('click', e => {
    if (e.target.id === 'reparer-modal') _fermerReparerModal();   // clic a cote
  });
  document.getElementById('relancer-moteurs-btn').addEventListener('click', _relancerMoteurs);
  document.getElementById('redemarrer-serveur-btn').addEventListener('click', _redemarrerServeur);

  // --- Cache audio : compte affiche et purge a la main (20/09/2026) ---
  // Le compte est lu une fois au demarrage (et remis a jour apres une purge) :
  // sur un cache de 2 Go, la taille change lentement, inutile de l'interroger
  // en boucle.
  document.getElementById('cache-open-btn').addEventListener('click', _viderCacheAudio);
  _chargerEtatCache();
}
