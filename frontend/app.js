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

// Libelle d'une voix dans les menus deroulants : « Adèle (F) — 🇫🇷 France (Kyutai) ».
// Le genre en clair (F = femme, M = masculin) permet de reperer d'un coup
// d'oeil une voix feminine pour un personnage feminin ; le drapeau vient du
// champ region du catalogue, commun a Edge, Kokoro, Piper et Kyutai.
function _libelleVoix(v) {
  const etiquette = v.gender === 'F' ? ' (F)' : (v.gender === 'M' ? ' (M)' : '');
  return v.name + etiquette + ' \u2014 ' + v.region;
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

// Texte du bouton de bascule selon l'etat des moteurs. Fonction PURE (aucun
// acces au DOM, aucun appel reseau) : c'est elle que le test extrait du fichier
// reel (test_voix/test_bouton_moteur.js).
function _libelleMoteur(etat) {
  const prets = [], chargements = [];
  Object.keys(etat || {}).forEach((prefixe) => {
    const info = (etat || {})[prefixe] || {};
    const nom  = info.nom || prefixe;
    if (info.pret)       prets.push(nom);
    else if (info.actif) chargements.push(nom);
  });

  if (prets.length) {
    return { texte: '\uD83C\uDF99\uFE0F Voix de personnages : ' + prets.join(' + ')
                    + (prets.length > 1 ? ' prets' : ' pret') + ' \u2014 changer',
             eteint: false };
  }
  if (chargements.length) {
    return { texte: '\u23F3 ' + chargements.join(' + ') + ' : chargement en cours...',
             eteint: false };
  }
  return { texte: '\uD83C\uDF99\uFE0F Voix de personnages : moteur eteint '
                  + '\u2014 en allumer un',
           eteint: true };
}

// Bouton sous les reglages du lecteur. Sans lui, l'absence des voix d'un
// moteur eteint ressemblerait a un bug, et un moteur en cours de chargement
// (10 a 20 s) ressemblerait a une panne. Depuis le 15/09/2026 il sert aussi a
// CHANGER de moteur (demande de Laurent : un seul a la fois).
function _afficherEtatMoteurs() {
  const el = document.getElementById('moteur-etat');
  if (!el) return;

  if (_moteurMessage) {
    el.textContent = _moteurMessage;
    el.classList.remove('moteur-etat-off');
    return;
  }

  const libelle = _libelleMoteur(_moteursEtat);
  el.textContent = libelle.texte;
  el.classList.toggle('moteur-etat-off', libelle.eteint);
  el.title = 'Changer de moteur de voix (un seul a la fois)';
}

// ---- Changement de moteur : fenetre de choix ----

async function _ouvrirMoteurModal() {
  // Etat frais : on ne propose pas a l'aveugle (le moteur a pu etre allume ou
  // eteint depuis l'affichage de la page, par exemple par un lanceur a la main).
  await loadMoteurs(true);
  _remplirMoteurModal();
  document.getElementById('moteur-modal').classList.remove('hidden');
}

function _fermerMoteurModal() {
  document.getElementById('moteur-modal').classList.add('hidden');
}

// Detail affiche sous chaque moteur : allume et pret, en chargement, ou eteint.
function _detailMoteur(prefixe) {
  const info = (_moteursEtat || {})[prefixe] || {};
  if (info.pret)  return 'allum\u00E9 et pr\u00EAt';
  if (info.actif) return 'chargement en cours...';
  return '\u00E9teint';
}

function _remplirMoteurModal() {
  ['xtts', 'kyutai'].forEach((prefixe) => {
    const el = document.getElementById('moteur-detail-' + prefixe);
    if (el) el.textContent = _detailMoteur(prefixe);
  });
  const note = document.getElementById('moteur-modal-note');
  if (!note) return;
  // Pendant une ecoute, changer de moteur arrete la lecture : la suite des
  // phrases appartenait a l'autre moteur. On le dit AVANT le clic.
  note.textContent = (_ttsState === 'playing' || _ttsState === 'paused')
    ? 'Changer de moteur arr\u00EAte la lecture en cours.'
    : '';
}

// Bascule d'un moteur a l'autre : le SERVEUR eteint l'autre AVANT d'allumer
// celui-ci, et attend qu'il ait rendu la carte graphique. Les deux ne tiennent
// pas ensemble (environ 3,8 Go chacun sur une carte de 8 Go).
async function _basculerMoteur(cible) {
  _fermerMoteurModal();
  _moteurMessage = '';
  _afficherEtatMoteurs();

  try {
    const res = await fetch('/api/moteur/basculer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ moteur: cible }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      _moteurMessage = '\u26A0\uFE0F ' + (data.detail || 'changement impossible');
      _afficherEtatMoteurs();
      return;
    }

    _moteursEtat  = data.etat || _moteursEtat;
    _moteursQuand = Date.now();
    if (data.demarre && _moteursEtat[cible]) {
      // Il vient d'etre lance : son modele charge encore.
      _moteursEtat[cible] = Object.assign({}, _moteursEtat[cible],
                                          { actif: true, pret: false });
    }
    _afficherEtatMoteurs();
    await loadVoices();             // les voix de l'autre moteur disparaissent
    if (cible === 'aucun') return;
    _surveillerMoteur(cible);
  } catch (e) {
    console.error('Erreur changement de moteur de voix:', e);
    _moteurMessage = '\u26A0\uFE0F serveur injoignable';
    _afficherEtatMoteurs();
  }
}

// Surveille le chargement du moteur, puis recharge les voix : elles viennent
// d'apparaitre dans les menus (un moteur non pret n'en propose aucune).
function _surveillerMoteur(cible) {
  if (_moteurPollTimer) clearInterval(_moteurPollTimer);
  const fin = Date.now() + MOTEUR_ATTENTE_MAX_MS;
  _moteurPollTimer = setInterval(async () => {
    await loadMoteurs(true);
    const info = (_moteursEtat || {})[cible] || {};
    if (info.pret) {
      clearInterval(_moteurPollTimer);
      _moteurPollTimer = null;
      _moteurMessage = '';
      _afficherEtatMoteurs();
      await loadVoices();
    } else if (Date.now() > fin) {
      clearInterval(_moteurPollTimer);
      _moteurPollTimer = null;
      _moteurMessage = '\u26A0\uFE0F le moteur ne r\u00E9pond pas';
      _afficherEtatMoteurs();
    }
  }, MOTEUR_POLL_MS);
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
function _etatCasting(rows, filtre) {
  const estGenerique = (id) => _CAST_VOIX_GENERIQUES.indexOf(id) >= 0;
  const compteParVoix = {};
  rows.forEach(r => {
    const id = (r.v && r.v.voice_id) || '';
    // Les voix generiques des petits roles ne comptent PAS comme partagees :
    // elles sont partagees par construction (une voix par genre pour tous les
    // petits roles), et les signaler noierait la liste sous de fausses
    // alertes. On ne signale que le partage d'une voix DEDIEE.
    if (!id || estGenerique(id)) return;
    compteParVoix[id] = (compteParVoix[id] || 0) + 1;
  });
  const aCaster = (r) => estGenerique((r.v && r.v.voice_id) || '')
                          && r.total >= _CAST_MINOR_THRESHOLD;
  const partagee = (r) => !aCaster(r) && compteParVoix[r.v.voice_id] > 1;
  return {
    compteParVoix: compteParVoix,
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

// Menu deroulant des voix d'un personnage, organise par GENRE et filtre selon
// le choix en cours (_castGenreFiltre). La voix actuellement attribuee reste
// TOUJOURS visible, meme si le filtre la masque : sinon on croirait que le
// personnage n'a plus de voix.
function _construireMenuVoix(voiceIdActuelle) {
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

  // Le genre n'est pas repete dans chaque ligne : le groupe le donne deja.
  const libelle = (v) => v.name + ' \u2014 ' + v.region;

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

async function _openCastModal(rafraichirVoix) {
  // Les voix proposees dependent des moteurs allumes : on rafraichit leur etat
  // AVANT de construire les menus (le moteur a pu etre eteint ou demarre
  // depuis l'affichage de la page).
  // A l'OUVERTURE de la fenetre, on recharge AUSSI la liste des voix proposees
  // et le catalogue complet : sans cela, un moteur allume apres le chargement
  // de la page restait invisible (liste perimee) et ses voix attribuees
  // s'affichaient sous leur identifiant technique (constat du 15/09/2026).
  await loadMoteurs();
  if (rafraichirVoix) {
    await _chargerVoixProposees();
    await loadCatalogueVoix();
  }
  const list    = document.getElementById('cast-list');
  const voices  = (_currentBookData && _currentBookData.voices) || {};
  const aliases = (_currentBookData && _currentBookData.aliases) || {};

  document.getElementById('cast-saga-input').value = (_currentBookData && _currentBookData.saga) || '';
  _loadSagaSuggestions();

  // Regroupement des alias sous leur personnage principal (session 12/09/2026).
  const aliasOf = {};   // principal -> [alias, ...]
  Object.keys(aliases).forEach(al => {
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

  // Lignes a afficher : chaque principal suivi de ses alias.
  const rows = [];
  Object.keys(voices)
    .filter(nom => racineDe(nom) === nom)
    .sort((a, b) => totalDe(b) - totalDe(a))
    .forEach(nom => {
      rows.push({ nom: nom, v: voices[nom], total: totalDe(nom), isAlias: false });
      (aliasOf[nom] || []).slice().sort().forEach(al => {
        rows.push({ nom: al, v: voices[al], total: voices[al].line_count || 0, isAlias: true });
      });
    });

  // --- Etat des voix de ce livre (session du 15/09/2026) ---
  // Les badges et le filtre viennent de _etatCasting(), une fonction pure et
  // testee (test_voix/test_etat_casting.js) : sur un gros casting, on voit
  // d'un coup d'oeil les personnages sans voix a eux (« a caster ») et les
  // timbres partages entre plusieurs personnages.
  const etat = _etatCasting(rows, _castEtatFiltre);
  const rowsAffichees = etat.rowsFiltrees;
  const resume = document.getElementById('cast-etat-resume');
  if (resume) {
    resume.textContent = rows.length + ' personnages \u00b7 ' + etat.nbCaster
      + ' \u00e0 caster \u00b7 ' + etat.nbPartagee + ' voix partag\u00e9e'
      + (etat.nbPartagee > 1 ? 's' : '');
  }

  list.innerHTML = '';

  if (rowsAffichees.length === 0) {
    list.innerHTML = '<li class="cast-empty">'
      + (rows.length === 0
          ? 'Aucun personnage identifie pour ce livre.'
          : 'Aucun personnage dans ce filtre.') + '</li>';
  } else {
    rowsAffichees.forEach(row => {
      const nom = row.nom;
      const v   = row.v;
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
      const genreLabel = v.genre === 'F' ? 'Femme' : 'Homme';
      metaEl.textContent = genreLabel + ' \u00b7 ' + row.total + ' repliques';
      info.appendChild(nameEl);
      info.appendChild(metaEl);

      // Badge d'etat : « a caster » (voix generique alors que le personnage
      // parle beaucoup) ou « voix partagee » (meme timbre qu'un autre
      // personnage : a differencier avec la hauteur). Les petits roles restent
      // sans badge : leur voix generique est voulue.
      if (etat.aCaster(row)) {
        const badge = document.createElement('span');
        badge.className = 'cast-badge cast-badge-caster';
        badge.textContent = '\u26A0 \u00e0 caster';
        badge.title = 'Ce personnage parle souvent mais porte encore la voix '
          + 'g\u00e9n\u00e9rique des petits r\u00f4les : choisissez-lui une voix.';
        info.appendChild(badge);
      } else if (etat.partagee(row)) {
        const autres = etat.compteParVoix[v.voice_id] - 1;
        const badge = document.createElement('span');
        badge.className = 'cast-badge cast-badge-partagee';
        badge.textContent = '\u29C9 voix partag\u00e9e (' + autres + ')';
        badge.title = 'Cette voix est port\u00e9e par ' + autres
          + ' autre(s) personnage(s) : diff\u00e9renciez-les avec la hauteur.';
        info.appendChild(badge);
      }

      const select = _construireMenuVoix(v.voice_id);

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

      const sendUpdate = () => {
        const rateStr  = _formatPercent(parseInt(rateInput.value, 10));
        const pitchStr = _formatHz(parseInt(pitchInput.value, 10));
        _updateCharacterVoice(nom, select.value, rateStr, pitchStr);
      };

      select.addEventListener('change', sendUpdate);
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

  document.getElementById('cast-modal').classList.remove('hidden');
}

function _closeCastModal() {
  document.getElementById('cast-modal').classList.add('hidden');
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

const FAMILLES_VOIX = [
  ['edge',   'Edge (en ligne)'],
  ['kokoro', 'Kokoro'],
  ['piper',  'Piper'],
  ['kyutai', 'Kyutai'],
  ['xtts',   'XTTS v2'],
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
  meta.textContent = _libelleFamille(_familleDeVoix(voix.id))
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
    const options = [['', critere.libelle]];   // etat vide : le menu s'annonce
    (critere.valeurs || []).forEach(v => options.push([v.valeur, v.libelle]));
    _listeOptions(sel, options, annot[critere.cle] || '');
    _majStyleCritere(sel);
    sel.addEventListener('change', () => {
      _majStyleCritere(sel);
      _sauverAnnotationVoix(voix.id, li);
    });
    champsCriteres.push(sel);
    criteres.appendChild(sel);
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
  await loadVoices();
  await _chargerAnnotationsVoix();
  await _chargerCriteresVoix();

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
document.getElementById('cast-autogroup-btn').addEventListener('click', _autogrouperDoublons);

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

async function loadChapter(index, scrollTo, cursorTo = 0, autoPlay = false) {
  _stopTTS();
  // Les phrases du nouveau chapitre ont d'autres index : un panneau « voix de
  // la phrase » reste ouvert pointerait sur la mauvaise phrase (15/09/2026).
  _closeVoicePanel();
  if (index < 0 || index >= _totalChapters) return;
  _currentChapter = index;

  const content = document.getElementById('reader-content');
  content.innerHTML = '<p style="color:var(--text-muted)">Chargement...</p>';

  try {
    const res = await fetch(
      '/api/books/' + _currentBookId + '/chapter/' + index + '?user_id=' + _currentUserId
    );
    if (!res.ok) {
      content.innerHTML = '<p>Chapitre introuvable.</p>';
      return;
    }

    const data = await res.json();
    _chapterSpeakers = data.speakers || {};
    renderChapterContent(data.text || '');
    document.getElementById('reader-content').scrollTop = scrollTo || 0;

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

  } catch (e) {
    content.innerHTML = '<p>Erreur de chargement.</p>';
    console.error(e);
  }
}

// ============================================================
// DÉCOUPAGE & RENDU DU CHAPITRE
// ============================================================

function _buildSentences(text) {
  const paras    = text.split(/\n\n+/).map(p => p.trim()).filter(p => p.length > 5);
  const sentences    = [];
  const paraStarts   = [];

  paras.forEach((para, paraIdx) => {
    paraStarts.push(sentences.length);
    // Découpe aux fins de phrases tout en conservant la ponctuation
    const rawSents = para.split(/(?<=[.!?…»])\s+/);
    rawSents.forEach(s => {
      s = s.trim();
      if (s.length > 3) sentences.push({ text: s, paraIdx });
    });
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

// --- Navigation paragraphe ---

function _cursorParaNext() {
  const next = _paragraphStarts.find(s => s > _cursorIdx);
  if (next !== undefined) {
    _setCursor(next);
    if (_ttsState === 'playing') _abortAndRestart();
  }
}

function _cursorParaPrev() {
  const cur        = [..._paragraphStarts].reverse().find(s => s <= _cursorIdx) ?? 0;
  const curParaIdx = _paragraphStarts.indexOf(cur);
  const target     = (cur < _cursorIdx)
    ? cur
    : (curParaIdx > 0 ? _paragraphStarts[curParaIdx - 1] : 0);
  _setCursor(target);
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

function _updateMediaSession() {
  if (!('mediaSession' in navigator)) return;

  const chapterTitle = document.getElementById('chapter-info')
    ? (document.getElementById('reader-book-title').textContent || 'NIMM ePub')
    : 'NIMM ePub';

  navigator.mediaSession.metadata = new MediaMetadata({
    title:  chapterTitle,
    artist: (_currentBookData && _currentBookData.author) || '',
    album:  'NIMM ePub'
  });
  navigator.mediaSession.playbackState = 'playing';

  navigator.mediaSession.setActionHandler('play',  () => toggleTTS());
  navigator.mediaSession.setActionHandler('pause', () => toggleTTS());
  navigator.mediaSession.setActionHandler('previoustrack', () => document.getElementById('sent-prev-btn').click());
  // Le bouton ⏩ de la barre a ete retire le 15/09/2026 (doublon avec ⏭ ;
  // demande de Laurent) : les commandes du casque et de l'ecran verrouille
  // continuent d'avancer d'UNE PHRASE, comme avant, en appelant directement la
  // fonction au lieu de cliquer sur un bouton qui n'existe plus.
  navigator.mediaSession.setActionHandler('nexttrack', () => _cursorSentNext());
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

function _voiceForSentence(idx) {
  const defaultVoice = document.getElementById('voice-select').value;
  const speaker = _chapterSpeakers[idx];
  if (speaker && speaker !== 'narration' && _currentBookData && _currentBookData.voices) {
    const v = _currentBookData.voices[speaker];
    // v.voice_id VIDE = personnage sans voix dediee : les petits roles
    // (< 8 repliques) depuis le 15/09/2026. Ils sont lus par le NARRATEUR,
    // c'est-a-dire par la voix choisie dans le lecteur (defaultVoice).
    if (v && v.voice_id) return { voice: v.voice_id, pitch: v.pitch };
  }
  return { voice: defaultVoice, pitch: '+0Hz' };
}

// Playlist de lecture : UNE unite audio = UNE phrase (ou, pour les phrases
// trop longues pour une seule requete de synthese, un sous-segment de
// phrase). Aucune fusion de phrases entre elles : c'est ce qui permet a la
// surbrillance de coller a la voix (frontiere exacte entre deux phrases) et
// au rythme de lecture d'etre regulier.
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
      });
    }
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
    cache[i] = _fetchAudio(u.text, u.voice, rate, u.pitch, signal).then(blob => {
      if (!blob) cache[i] = null; // echec apres retries : pourra etre retente
      return blob;
    });
    cache[i].then(() => { inFlight--; wakeWaiters(); pump(); });
  }

  // Poids en caracteres des unites deja prechargees non encore lues.
  function aheadChars() {
    let w = 0;
    for (let i = readIdx + 1; i < nextFetch; i++) {
      w += units[i].text.length + 1;
      if (w > PREFETCH_MAX_AHEAD_CHARS) break;
    }
    return w;
  }

  // Fenetre glissante : lance les fetchs vers l'avant tant qu'on est sous
  // le plafond de caracteres et sous la limite de parallelisme.
  function pump() {
    if (_ttsSession !== mySession || signal.aborted) return;
    while (inFlight < PREFETCH_CONCURRENCY && nextFetch < units.length) {
      if (aheadChars() + units[nextFetch].text.length + 1 > PREFETCH_MAX_AHEAD_CHARS) break;
      launchFetch(nextFetch);
      nextFetch++;
    }
  }

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

  // --- Boucle de lecture, phrase par phrase ---
  for (let i = 0; i < units.length; i++) {
    if (_ttsSession !== mySession || signal.aborted) break;
    const u = units[i];

    // Le blob doit etre pret (il l'est en quasi permanence grace au
    // prefetcher). En cas de coupure reseau, on attend sans arreter.
    const blob = await waitUnitNetworkRetry(i);
    if (!blob || _ttsSession !== mySession || signal.aborted) break;

    // Reprise apres une attente reseau : on repasse en lecture.
    if (_ttsState !== 'playing') {
      _ttsState = 'playing';
      setTTSUI('playing');
    }

    // Pause silencieuse quand on change de paragraphe (ex: apres un titre)
    if (i > 0 && u.paraIdx !== units[i - 1].paraIdx) {
      await _pause(PARAGRAPH_PAUSE_MS, signal);
      if (_ttsSession !== mySession || signal.aborted) break;
    }

    readIdx = i;

    // Surbrillance : on pose le curseur sur la phrase dont l'audio va
    // reellement demarrer, et on n'y touche plus pendant toute sa duree.
    // Finie l'estimation timeupdate dans un bloc fusionne (qui faisait
    // avancer la surbrillance en avance sur la voix).
    if (u.sentIdx !== _cursorIdx) {
      _setCursor(u.sentIdx);
      _updateTTSProgress(u.sentIdx, _sentences.length);
    }

    await _playBlob(blob, signal);

    // Memoire liberee sur l'unite lue, puis la fenetre de prechargement
    // glisse d'un cran vers la suite.
    cache[i] = null;
    pump();

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
}

async function _fetchAudio(text, voice, rate, pitch, signal) {
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
        body:    JSON.stringify({ text, voice, rate, pitch }),
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

// Pause silencieuse entre deux paragraphes (ex: apres un titre).
// Elle valait 300 ms. Decision de Laurent (15/09/2026, ecoute du Comte de
// Monte-Cristo) : dans un dialogue, CHAQUE replique est un paragraphe, donc
// cette pause s'ajoutait a chaque echange et coupait le rythme -- d'autant
// plus qu'elle s'additionnait au silence de fin de phrase du moteur. Le
// silence de fin de phrase etant desormais rogne a 0,25 s cote XTTS (et a
// 0,25 s pour Edge depuis le 08/09/2026), la pause ajoutee ici devient
// inutile : la respiration naturelle de la phrase suffit. Mettre une valeur
// > 0 la retablit (300 = ancien reglage). Interrompue immediatement si le
// TTS est stoppe/aborte.
function _pause(ms, signal) {
  return new Promise(resolve => {
    const timer = setTimeout(resolve, ms);
    signal.addEventListener('abort', () => { clearTimeout(timer); resolve(); });
  });
}

const PARAGRAPH_PAUSE_MS = 0;

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
function _remplirMenuVoixPhrase(select, voixId) {
  select.innerHTML = '';
  const groupe = (etiquette, liste) => {
    if (!liste.length) return;
    const g = document.createElement('optgroup');
    g.label = etiquette;
    liste.forEach(v => {
      const o = document.createElement('option');
      o.value       = v.id;
      o.textContent = v.name + ' \u2014 ' + v.region;
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

  _remplirMenuVoixPhrase(document.getElementById('voice-phrase-select'), voixId);
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
    if (sel) sel.value = voix;
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
}

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

  // Curseur glitch — navigation
  // (le bouton « phrase suivante » ⏩ a ete retire le 15/09/2026 : il faisait
  // doublon avec ⏭, le paragraphe suivant, demande de Laurent.)
  document.getElementById('para-prev-btn').addEventListener('click', _cursorParaPrev);
  document.getElementById('para-next-btn').addEventListener('click', _cursorParaNext);
  document.getElementById('sent-prev-btn').addEventListener('click', _cursorSentPrev);

  document.getElementById('chapters-btn').addEventListener('click', openChaptersPanel);
  document.getElementById('chapters-close-btn').addEventListener('click', closeChaptersPanel);
  document.getElementById('chapters-backdrop').addEventListener('click', closeChaptersPanel);

  document.getElementById('search-btn').addEventListener('click', _runSearch);
  document.getElementById('search-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') _runSearch();
  });
  document.getElementById('search-clear-btn').addEventListener('click', _clearSearch);

  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    closeChaptersPanel();
    _fermerMoteurModal();
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

  // --- Bouton de bascule des moteurs de voix (Kyutai / XTTS v2) ---
  // Le voyant du bas de la fenetre de lecture est le bouton : il ouvre le
  // choix, et le serveur eteint l'autre moteur avant d'allumer celui-ci.
  document.getElementById('moteur-etat').addEventListener('click', _ouvrirMoteurModal);
  document.getElementById('moteur-cancel-btn').addEventListener('click', _fermerMoteurModal);
  document.getElementById('moteur-modal').addEventListener('click', e => {
    if (e.target.id === 'moteur-modal') _fermerMoteurModal();   // clic a cote
  });
  document.querySelectorAll('#moteur-modal .provider-btn').forEach(btn => {
    btn.addEventListener('click', () => _basculerMoteur(btn.dataset.moteur));
  });
}
