// Verification jetable (21/09/2026) : on extrait _svgCadenas du VRAI app.js,
// on imprime les deux dessins, et on fabrique un apercu HTML a ouvrir d'un
// double-clic (aucun serveur necessaire).
// Usage : node _verif_cadenas.js
'use strict';

const fs = require('fs');
const src = fs.readFileSync('frontend/app.js', 'utf8');

const debut = src.indexOf('function _svgCadenas(verrouille) {');
const fin = src.indexOf('\n}', debut) + 2;
if (debut < 0 || fin < 2) {
  console.error('ERR : _svgCadenas introuvable dans app.js');
  process.exit(1);
}
const code = src.slice(debut, fin);
// eslint-disable-next-line no-eval
const _svgCadenas = eval('(' + code.replace('function _svgCadenas', 'function') + ')');

const ferme = _svgCadenas(true);
const ouvert = _svgCadenas(false);

console.log('FERME   (verrouille)   :', ferme);
console.log('OUVERT  (deverrouille) :', ouvert);
console.log('cadenas differents ?   :', ferme !== ouvert ? 'OK' : 'ERR');
console.log('les deux sont des svg ?:', ferme.indexOf('<svg') === 0 && ouvert.indexOf('<svg') === 0 ? 'OK' : 'ERR');
console.log('anse fermee presente ? :', ferme.indexOf('10 0v4') >= 0 ? 'OK' : 'ERR');
console.log('anse ouverte presente ?:', ouvert.indexOf('9.9-1') >= 0 ? 'OK' : 'ERR');

function bouton(svg, verrouille, taille) {
  const cls = verrouille ? ' lock-btn locked' : ' lock-btn';
  const px = taille === 'mobile' ? '44px' : '30px';
  const ic = taille === 'mobile' ? '22px' : '16px';
  return '<button class="' + cls.trim() + '" style="width:' + px + ';height:' + px + '">'
       + svg.replace('<svg', '<svg style="width:' + ic + ';height:' + ic + '"')
       + '</button>';
}

const html = `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<title>Apercu des cadenas du casting - NIMM ePub (21/09/2026)</title>
<style>
  body { background:#0d0d0d; color:#e8e3da; font-family:-apple-system,'Segoe UI',sans-serif;
         margin:0; padding:24px; }
  h1 { font-size:1.1rem; font-weight:600; }
  h2 { font-size:0.9rem; font-weight:600; color:#c8a96e; margin-top:28px; }
  p  { font-size:0.82rem; color:#7a7570; line-height:1.5; max-width:640px; }
  .rangee { display:flex; align-items:center; gap:14px; margin:10px 0; flex-wrap:wrap; }
  .le-genre { font-size:0.78rem; color:#7a7570; width:250px; }
  /* Les memes regles que styles.css, recopiees ici : le bouton est un carre a
     une seule icone, le dessin prend la couleur du bouton. */
  .lock-btn { display:flex; align-items:center; justify-content:center;
              border:1px solid #2a2a2a; border-radius:6px; background:#1c1c1c;
              color:#7a7570; cursor:pointer; }
  .lock-btn.locked { border-color:#c8a96e; color:#c8a96e; background:#8a7048; }
  .emoji { font-size:1.15rem; }
</style>
</head>
<body>
  <h1>Les cadenas du casting, vus de pres</h1>
  <p>Page d'apercu generee depuis <code>frontend/app.js</code> (elle n'a besoin
     d'aucun serveur : double-clic suffit). Elle ne remplace pas un essai sur le
     telephone, elle montre seulement les deux dessins.</p>

  <h2>Avant : les emojis (ce que le code envoyait deja)</h2>
  <div class="rangee">
    <span class="le-genre">Verrouille (emoji, aura) :</span>
    <span class="emoji">🔒</span>
    <span class="le-genre">Deverrouille (emoji, sans aura) :</span>
    <span class="emoji">🔓</span>
  </div>

  <h2>Maintenant : le cadenas dessine - sur PC (bouton de 30 px)</h2>
  <div class="rangee">
    <span class="le-genre">Verrouille : cadenas FERME, dore, aura :</span>
    ${bouton(ferme, true, 'pc')}
  </div>
  <div class="rangee">
    <span class="le-genre">Deverrouille : cadenas OUVERT, gris, sans aura :</span>
    ${bouton(ouvert, false, 'pc')}
  </div>

  <h2>Maintenant : le cadenas dessine - sur telephone (bouton de 44 px)</h2>
  <div class="rangee">
    <span class="le-genre">Verrouille : cadenas FERME, dore, aura :</span>
    ${bouton(ferme, true, 'mobile')}
  </div>
  <div class="rangee">
    <span class="le-genre">Deverrouille : cadenas OUVERT, gris, sans aura :</span>
    ${bouton(ouvert, false, 'mobile')}
  </div>
</body>
</html>
`;

fs.writeFileSync('APERCU_CADENAS_20260921.html', html, 'utf8');
console.log('APERCU_CADENAS_20260921.html ecrit.');
