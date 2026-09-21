// Verifie le voyant « Reparer les moteurs de voix » (21/09/2026).
// ----------------------------------------------------------------------
// Meme technique que test_voix_ecoutables.js : la fonction _libelleMoteur est
// extraite DU FICHIER REEL (jamais recopiee : renommee ou deplacee, le test
// echoue bruyamment), et on verifie aussi que le voyant, la fenetre de
// reparation et le branchement existent bien dans index.html et app.js.
//
// Demande de Laurent (21/09/2026) : un clic par erreur sur l'ANCIEN bouton
// (celui qui CHANGEAIT de moteur, en bas de la fenetre de lecture) avait
// eteint Pocket TTS et fait disparaitre ses 18 voix du casting. Ce bouton a
// donc disparu, remplace par un voyant qui ne sait que RALLUMER ce qui s'est
// eteint -- et qui ne parle QUE des moteurs ATTENDUS (sinon il crierait en
// permanence pour un moteur eteint volontairement).
//
// Usage : node test_voix/test_bouton_moteur.js
'use strict';

const fs   = require('fs');
const path = require('path');

const APP  = path.join(__dirname, '..', 'frontend', 'app.js');
const HTML = path.join(__dirname, '..', 'frontend', 'index.html');
const source = fs.readFileSync(APP, 'utf8');
const page   = fs.readFileSync(HTML, 'utf8');

// --- la fonction reelle, extraite du fichier ---
const debut = source.indexOf('function _libelleMoteur');
const fin   = source.indexOf('function _afficherEtatMoteurs');
if (debut < 0 || fin <= debut) {
  console.error('ECHEC : fonction _libelleMoteur introuvable dans app.js');
  process.exit(1);
}
const _libelleMoteur = new Function('return ' + source.slice(debut, fin))();

let ECHECS = 0;
function verifier(nom, condition, detail) {
  if (condition) {
    console.log('  OK    ' + nom);
  } else {
    console.log('  ECHEC ' + nom + (detail ? '  -> ' + detail : ''));
    ECHECS++;
  }
}

// Un moteur tel que /api/moteurs le renvoie : `attendu` dit s'il DEVRAIT
// tourner maintenant (Pocket TTS, qui cohabite, et le moteur lourd retenu dans
// data/moteur_voix.txt).
const moteur = (nom, actif, pret, attendu) =>
  ({ nom: nom, actif: actif, pret: pret, attendu: attendu, cohabite: false });
const POCKET = (actif, pret) => moteur('Pocket TTS', actif, pret, true);

const POCKET_PRET   = { pocket: POCKET(true, true) };
const POCKET_CHARGE = { pocket: POCKET(true, false) };
const POCKET_ETEINT = { pocket: POCKET(false, false) };
// Kyutai est en service, XTTS dort VOLONTAIREMENT : rien a signaler.
const XTTS_LIBRE    = { kyutai: moteur('Kyutai', true, true, true),
                        xtts:   moteur('XTTS v2', false, false, false),
                        pocket: POCKET(true, true) };
const DEUX_ETEINTS  = { pocket: POCKET(false, false),
                        kyutai: moteur('Kyutai', false, false, true) };
// Rien d'attendu du tout (Pocket pas installe, aucun moteur lourd retenu).
const RIEN_ATTENDU  = { kyutai: moteur('Kyutai', false, false, false),
                        pocket: moteur('Pocket TTS', false, false, false) };

console.log('');
console.log('='.repeat(66));
console.log('VERIFICATION : voyant « Reparer les moteurs de voix »');
console.log('='.repeat(66));

// --- 1. Ce que le voyant affiche ---
console.log('');
console.log('1) le libelle du voyant selon l etat des moteurs');
console.log('   (seuls les moteurs ATTENDUS comptent)');

let l = _libelleMoteur(POCKET_PRET);
verifier('moteur attendu et pret : son nom est affiche',
         l.texte.indexOf('Pocket TTS') >= 0, l.texte);
verifier('moteur attendu et pret : ca se voit que tout va bien',
         /marche/.test(l.texte), l.texte);
verifier('moteur attendu et pret : pas de mise en garde', l.eteint === false,
         String(l.eteint));

l = _libelleMoteur(POCKET_CHARGE);
verifier('en chargement : le nom du moteur est affiche',
         l.texte.indexOf('Pocket TTS') >= 0, l.texte);
verifier('en chargement : ca se voit', /chargement/.test(l.texte), l.texte);
verifier('en chargement : pas de mise en garde', l.eteint === false,
         String(l.eteint));

l = _libelleMoteur(POCKET_ETEINT);
verifier('moteur attendu et eteint : ca se voit',
         /[e\u00E9]teint/.test(l.texte), l.texte);
verifier('moteur attendu et eteint : on invite a reparer',
         /r\u00E9parer/.test(l.texte), l.texte);
verifier('moteur attendu et eteint : voyant mis en avant',
         l.eteint === true, String(l.eteint));

l = _libelleMoteur(XTTS_LIBRE);
verifier('un moteur NON attendu ne fait pas crier le voyant (XTTS dort)',
         l.texte.indexOf('XTTS') < 0 && l.eteint === false, l.texte);

l = _libelleMoteur(DEUX_ETEINTS);
verifier('deux moteurs attendus eteints : les deux sont nommes',
         l.texte.indexOf('Pocket TTS') >= 0 && l.texte.indexOf('Kyutai') >= 0,
         l.texte);
verifier('deux moteurs attendus eteints : le pluriel est juste',
         /teints/.test(l.texte), l.texte);

l = _libelleMoteur(RIEN_ATTENDU);
verifier('rien d attendu : aucun voyant (pas de bruit pour rien)',
         l.texte === '' && l.eteint === false, JSON.stringify(l));

verifier('etat absent : aucun plantage', !!_libelleMoteur(undefined));
verifier('etat null : aucun plantage', !!_libelleMoteur(null));
verifier('etat vide : aucun voyant, aucun plantage',
         _libelleMoteur({}).texte === '', JSON.stringify(_libelleMoteur({})));

// --- 2. Le voyant et la fenetre de reparation dans la page ---
console.log('');
console.log('2) le voyant et la fenetre de reparation existent dans index.html');

verifier('le voyant est un BOUTON',
         /<button[^>]*id="reparer-open-btn"/.test(page));
verifier('il est annonce aux lecteurs d ecran',
         /id="reparer-open-btn"[\s\S]{0,120}aria-label="R\u00E9parer/.test(page));
verifier('la fenetre de reparation existe', /id="reparer-modal"/.test(page));
verifier('le geste DOUX est propose', /id="relancer-moteurs-btn"/.test(page));
verifier('le geste FORT est propose', /id="redemarrer-serveur-btn"/.test(page));
verifier('chaque geste dit ce qu il fait',
         /id="relancer-moteurs-detail"/.test(page)
         && /id="redemarrer-serveur-detail"/.test(page));
verifier('il y a un bouton pour fermer', /id="reparer-cancel-btn"/.test(page));
verifier('la fenetre a une ligne pour dire pourquoi une voix manque',
         /id="reparer-modal-note"/.test(page));
verifier('le voile de redemarrage existe (l ecran ne reste pas fige)',
         /id="redemarrage-voile"/.test(page));

// --- 2 bis. L'ancien bouton de CHANGEMENT de moteur a bien disparu ---
// C'est lui qui avait eteint Pocket TTS par erreur, et fait disparaitre ses
// 18 voix du casting : plus rien de tout cela ne doit subsister.
console.log('');
console.log('2 bis) l ancien bouton de changement de moteur a disparu');

verifier('plus aucun bouton « moteur-etat » dans la page',
         page.indexOf('id="moteur-etat"') < 0);
verifier('plus aucune fenetre « moteur-modal »',
         page.indexOf('id="moteur-modal"') < 0);
verifier('plus aucun choix de moteur dans la page',
         page.indexOf('data-moteur=') < 0);
verifier('plus aucune reference dans le script',
         source.indexOf('moteur-etat') < 0
         && source.indexOf('moteur-modal') < 0
         && source.indexOf('_basculerMoteur') < 0);
verifier('la route de bascule n est plus appelee par la page',
         source.indexOf("'/api/moteur/basculer'") < 0);

// --- 3. Le branchement dans app.js ---
console.log('');
console.log('3) le branchement dans app.js');

verifier('un clic sur le voyant ouvre la fenetre',
         source.indexOf("getElementById('reparer-open-btn').addEventListener('click', _ouvrirReparerModal)") >= 0);
verifier('le bouton Fermer ferme la fenetre',
         source.indexOf("getElementById('reparer-cancel-btn').addEventListener('click', _fermerReparerModal)") >= 0);
verifier('le geste DOUX appelle la route du serveur',
         source.indexOf("'/api/moteurs/relancer'") >= 0);
verifier('le geste FORT appelle la route du serveur',
         source.indexOf("'/api/serveur/redemarrer'") >= 0);
verifier('le geste FORT demande CONFIRMATION avant de partir',
         source.indexOf('window.confirm(question)') >= 0);
verifier('il attend le retour du serveur, puis recharge la page',
         source.indexOf('_attendreLeServeur') >= 0
         && source.indexOf('location.reload()') >= 0);
verifier('la relance surveille le chargement et recharge les voix',
         source.indexOf('MOTEUR_POLL_MS') >= 0
         && source.indexOf('_surveillerReparation') >= 0
         && source.indexOf('await loadVoices()') >= 0);
verifier('le libelle du voyant vient bien de _libelleMoteur',
         source.indexOf('_libelleMoteur(_moteursEtat)') >= 0);
verifier('un echec est annonce dans le voyant (pas en silence)',
         source.indexOf('_moteurMessage = ') >= 0);
verifier('Echap ferme aussi la fenetre',
         source.indexOf('_fermerReparerModal();') >= 0);

console.log('');
console.log('='.repeat(66));
console.log(ECHECS === 0 ? 'TOUT EST OK' : ECHECS + ' VERIFICATION(S) EN ECHEC');
console.log('='.repeat(66));
process.exit(ECHECS === 0 ? 0 : 1);
