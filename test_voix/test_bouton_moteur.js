// Verifie le bouton de bascule des moteurs de voix (session du 15/09/2026).
// ----------------------------------------------------------------------
// Meme technique que test_voix_ecoutables.js : la fonction _libelleMoteur est
// extraite DU FICHIER REEL (jamais recopiee : renommee ou deplacee, le test
// echoue bruyamment), et on verifie aussi que le bouton, la fenetre de choix
// et le branchement existent bien dans index.html et app.js.
//
// Demande de Laurent : sous le lecteur, un bouton qui passe d'un moteur de voix
// a l'autre -- « soit l'un, soit l'autre ». Le voyant disait deja l'etat ; il
// doit maintenant aussi permettre de changer.
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

const eteint = (nom) => ({ nom: nom, actif: false, pret: false });
const MOTEURS_ETEINTS = { kyutai: eteint('Kyutai'), xtts: eteint('XTTS v2') };
const XTTS_PRET   = { kyutai: eteint('Kyutai'), xtts: { nom: 'XTTS v2', actif: true, pret: true } };
const XTTS_CHARGE = { kyutai: eteint('Kyutai'), xtts: { nom: 'XTTS v2', actif: true, pret: false } };
const LES_DEUX    = { kyutai: { nom: 'Kyutai', actif: true, pret: true },
                      xtts:   { nom: 'XTTS v2', actif: true, pret: true } };

console.log('');
console.log('='.repeat(66));
console.log('VERIFICATION : bouton de bascule des moteurs de voix');
console.log('='.repeat(66));

// --- 1. Ce que le bouton affiche ---
console.log('');
console.log('1) le libelle du bouton selon l etat des moteurs');

let l = _libelleMoteur(XTTS_PRET);
verifier('moteur pret : le nom est affiche', l.texte.indexOf('XTTS v2') >= 0, l.texte);
verifier('moteur pret : il invite a changer', l.texte.indexOf('changer') >= 0, l.texte);
verifier('moteur pret : pas assombri', l.eteint === false, String(l.eteint));

l = _libelleMoteur(XTTS_CHARGE);
verifier('en chargement : le nom du moteur est affiche',
         l.texte.indexOf('XTTS v2') >= 0, l.texte);
verifier('en chargement : ca se voit', /chargement/.test(l.texte), l.texte);
verifier('en chargement : pas assombri', l.eteint === false, String(l.eteint));

l = _libelleMoteur(MOTEURS_ETEINTS);
verifier('aucun moteur : ca se voit', /[e\u00E9]teint/.test(l.texte), l.texte);
verifier('aucun moteur : on invite a en allumer un',
         /allumer/.test(l.texte), l.texte);
verifier('aucun moteur : bouton assombri', l.eteint === true, String(l.eteint));

l = _libelleMoteur(LES_DEUX);
verifier('cas anormal (deux moteurs) : les deux noms sont affiches',
         l.texte.indexOf('Kyutai') >= 0 && l.texte.indexOf('XTTS v2') >= 0, l.texte);

verifier('etat absent : aucun plantage', !!_libelleMoteur(undefined));
verifier('etat null : aucun plantage', !!_libelleMoteur(null));
verifier('etat vide : annonce un moteur eteint',
         _libelleMoteur({}).eteint === true, JSON.stringify(_libelleMoteur({})));

// --- 2. Le bouton et la fenetre de choix dans la page ---
console.log('');
console.log('2) le bouton et la fenetre de choix existent dans index.html');

verifier('le voyant est devenu un BOUTON',
         /<button[^>]*id="moteur-etat"/.test(page));
verifier('il est annonce aux lecteurs d ecran',
         /id="moteur-etat"[\s\S]{0,120}aria-label="Changer de moteur/.test(page));
verifier('la fenetre de choix existe', /id="moteur-modal"/.test(page));
['xtts', 'kyutai', 'aucun'].forEach((cible) => {
  verifier('le choix « ' + cible + ' » est propose',
           page.indexOf('data-moteur="' + cible + '"') >= 0);
});
verifier('chaque moteur affiche son etat dans la fenetre',
         /id="moteur-detail-xtts"/.test(page) && /id="moteur-detail-kyutai"/.test(page));
verifier('il y a un bouton pour fermer', /id="moteur-cancel-btn"/.test(page));
verifier('la fenetre a une ligne pour prevenir que la lecture s arretera',
         /id="moteur-modal-note"/.test(page));

// --- 3. Le branchement dans app.js ---
console.log('');
console.log('3) le branchement dans app.js');

verifier('un clic sur le bouton ouvre la fenetre',
         source.indexOf("getElementById('moteur-etat').addEventListener('click', _ouvrirMoteurModal)") >= 0);
verifier('le bouton Fermer ferme la fenetre',
         source.indexOf("getElementById('moteur-cancel-btn').addEventListener('click', _fermerMoteurModal)") >= 0);
verifier('les trois choix sont branches',
         source.indexOf("querySelectorAll('#moteur-modal .provider-btn')") >= 0
         && source.indexOf('_basculerMoteur(btn.dataset.moteur)') >= 0);
verifier('la bascule appelle la route du serveur',
         source.indexOf("'/api/moteur/basculer'") >= 0);
verifier('elle envoie le moteur choisi en POST',
         source.indexOf('JSON.stringify({ moteur: cible })') >= 0);
verifier('elle surveille le chargement du moteur',
         source.indexOf('MOTEUR_POLL_MS') >= 0 && source.indexOf('_surveillerMoteur') >= 0);
verifier('le libelle du bouton vient bien de _libelleMoteur',
         source.indexOf('_libelleMoteur(_moteursEtat)') >= 0);
verifier('un echec est annonce dans le bouton (pas en silence)',
         source.indexOf('_moteurMessage = ') >= 0);
verifier('Echap ferme aussi la fenetre',
         source.indexOf('_fermerMoteurModal();') >= 0);

console.log('');
console.log('='.repeat(66));
console.log(ECHECS === 0 ? 'TOUT EST OK' : ECHECS + ' VERIFICATION(S) EN ECHEC');
console.log('='.repeat(66));
process.exit(ECHECS === 0 ? 0 : 1);
