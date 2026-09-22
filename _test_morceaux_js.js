// ============================================================
// PARITÉ Python / JavaScript : le découpage en MORCEAUX DE VOIX
// ============================================================
// Le Python (serveur) dit OU SONT les incises ; le JavaScript (page) coupe la
// phrase à ces positions. Les deux doivent produire EXACTEMENT les mêmes
// morceaux, sinon la phrase perdrait du texte en chemin.
//
// Ce script prend les morceaux DE LA VRAIE FONCTION de `frontend/app.js`
// (`_morceauxDeLaPhrase`), les calcule pour des cas fournis par le test Python
// (`_morceaux_cas.json`) et écrit le résultat (`_morceaux_js.json`). Le Python
// compare ensuite les deux, et vérifie que le texte reconstruit est intact.
//
// Lancement : appelé par `_test_morceaux_incises.py` (aucun moteur nécessaire).
const fs = require('fs');

const APP_JS = 'frontend/app.js';
const CAS    = '_morceaux_cas.json';
const SORTIE = '_morceaux_js.json';

// Extrait une fonction de app.js : de « function nom( » jusqu'à la première
// ligne qui ne contient qu'une accolade fermante (les accolades du corps sont
// indentées). Robuste aux fins de ligne Windows comme Unix.
function extraire(source, nom) {
  const lignes = source.split(/\r?\n/);
  const debut  = lignes.findIndex(l => l.startsWith('function ' + nom + '('));
  if (debut < 0) throw new Error('fonction introuvable dans app.js : ' + nom);
  let fin = -1;
  for (let i = debut + 1; i < lignes.length; i++) {
    if (lignes[i] === '}') { fin = i; break; }
  }
  if (fin < 0) throw new Error('fin de fonction introuvable : ' + nom);
  return lignes.slice(debut, fin + 1).join('\n');
}

const source = fs.readFileSync(APP_JS, 'utf8');
const code   = extraire(source, '_voixDuNarrateur') + '\n'
             + extraire(source, '_morceauxDeLaPhrase');

// Les globales de app.js dont ces deux fonctions ont besoin.
let _incisesNarrateur = false;
let _chapterIncises   = {};
const NARRATEUR_VOIX_DEFAUT = 'fr-CH-ArianeNeural';
const document = { getElementById: () => ({ value: 'VOIX_NARRATEUR' }) };

// Direct eval (script non strict) : les fonctions sont créées dans ce scope et
// voient les globales ci-dessus.
eval(code);

const cas = JSON.parse(fs.readFileSync(CAS, 'utf8'));
const sortie = [];
for (const c of cas) {
  _incisesNarrateur = !!c.narrateur;
  _chapterIncises   = c.spans ? { 0: c.spans } : {};
  const morceaux = _morceauxDeLaPhrase(c.texte, 0, {
    voice: 'VOIX_PERSONNAGE', pitch: '+2Hz', rate: '+5%'
  });
  sortie.push({
    texte:   c.texte,
    pieces:  morceaux.map(m => ({ text: m.text, voice: m.voice,
                                  pitch: m.pitch, rate: m.rate,
                                  incise: !!m.incise }))
  });
}
fs.writeFileSync(SORTIE, JSON.stringify(sortie, null, 1), 'utf8');
console.log('PARITE JS OK : ' + sortie.length + ' cas ecrits dans ' + SORTIE);
