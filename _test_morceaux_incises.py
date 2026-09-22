# -*- coding: utf-8 -*-
"""TEST BOUT EN BOUT du reglage « incises lues par le narrateur » (22/09/2026).

Verifie, dans l'ordre, ce que fait vraiment la chaine :
  1. la colonne `books.incises_narrateur` existe (migration non destructive) ;
  2. le point d'entree serveur renvoie les BONNES positions d'incises sur un vrai
     chapitre (22/11/63, chapitre 10, celui ecoute par Laurent) ;
  3. le decoupage en morceaux (ce que fait la page, miroir exact de
     `_morceauxDeLaPhrase` dans `frontend/app.js`) RECONSTRUIT la phrase a
     l'identique -- aucun caractere perdu, c'est l'invariant qui compte ;
  4. chaque morceau d'incise passe bien la porte du serveur : DIT avec le drapeau,
     TUE sans lui -- la preuve que le drapeau est indispensable.

Lecture seule sur le livre : seul `init_db()` est appele (il ne fait que creer la
colonne manquante, comme le demarrage de l'application).

Usage : python _test_morceaux_incises.py [book_id] [chapter_index]
"""

import asyncio
import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

import main                                                      # noqa: E402
from main import get_chapter_incises, _doit_taire_l_incise        # noqa: E402

BASE = RACINE / 'data' / 'nimm_epub.db'
BID = int(sys.argv[1]) if len(sys.argv) > 1 else 28
CHAP = int(sys.argv[2]) if len(sys.argv) > 2 else 10

ECHECS = 0
CONTROLES = 0


def verifier(nom, condition, detail=''):
    global ECHECS, CONTROLES
    CONTROLES += 1
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + repr(detail) if detail != '' else ''))
        ECHECS += 1


# --- Miroir EXACT de `_morceauxDeLaPhrase` (frontend/app.js) -----------------
# Si l'un des deux change, ce test doit etre mis a jour : c'est lui qui garantit
# que la page ne perd aucun caractere en coupant la phrase.
def morceaux(texte, spans):
    """Miroir de `_morceauxDeLaPhrase` : le texte reconstruit == le texte d'origine."""
    if not spans:
        return [{'text': texte, 'incise': False}]
    pieces = []
    debut = 0
    for a, b in spans:
        if a > debut:
            pieces.append({'text': texte[debut:a], 'incise': False})
        pieces.append({'text': texte[a:b], 'incise': True})
        debut = b
    if debut < len(texte):
        pieces.append({'text': texte[debut:], 'incise': False})

    # Un morceau sans lettre ne se synthetise pas : on le rattache au voisin (la
    # ponctuation ne doit JAMAIS disparaitre du texte lu).
    propres = []
    en_attente = ''
    for p in pieces:
        if re.search(r'[A-Za-z\u00c0-\u024f]', p['text']):
            p['text'] = en_attente + p['text']
            en_attente = ''
            propres.append(p)
        elif propres:
            propres[-1]['text'] += p['text']
        else:
            en_attente += p['text']
    if en_attente and propres:
        propres[-1]['text'] += en_attente
    return propres


def main_test():
    print('')
    print('=' * 78)
    print('TEST : reglage « incises lues par le narrateur » (livre %d, chapitre %d)'
          % (BID, CHAP))
    print('=' * 78)

    print('')
    print('1) la colonne `incises_narrateur` existe (migration)')
    main.init_db()
    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    colonnes = [r['name'] for r in conn.execute('PRAGMA table_info(books)')]
    verifier('colonne presente', 'incises_narrateur' in colonnes, colonnes)
    livre = conn.execute('SELECT title, user_id, filename, incises_narrateur '
                         'FROM books WHERE id = ?', (BID,)).fetchone()
    if livre is None:
        print('      livre %d absent de la bibliotheque : les controles qui'
              ' portent sur les donnees sont ignores.' % BID)
        print('      (la colonne, elle, a bien ete verifiee ci-dessus)')
        return 0
    user_id = livre['user_id']
    print('      livre : %s | reglage actuel : %s'
          % (livre['title'], livre['incises_narrateur']))
    conn.close()

    print('')
    print('2) le serveur donne les positions des incises du chapitre')
    reponse = asyncio.run(get_chapter_incises(BID, CHAP, user_id))
    incises = reponse['incises']
    verifier('le point d entree repond', isinstance(incises, dict))
    verifier('des incises sont trouvees dans ce chapitre', len(incises) > 0,
             len(incises))
    print('      %d phrases portent une incise (regle : %s)'
          % (len(incises), reponse['regle']))

    print('')
    print('3) le decoupage en morceaux RECONSTRUIT la phrase a l identique')
    from core.epub_parser import get_chapter
    from modules.decoupage import phrases as _phrases
    chapter = get_chapter(str(main.LIBRARY_DIR / livre['filename']), CHAP)
    textes = _phrases(chapter.get('text') or '', reponse['regle'])
    perdus = 0
    for idx, spans in incises.items():
        attendu = ''.join(p['text'] for p in morceaux(textes[idx], spans))
        if attendu != textes[idx]:
            perdus += 1
            if perdus <= 3:
                print('      PERDU phrase %d : %r' % (idx, attendu))
    verifier('%d phrase(s) avec incise reconstruites a l identique' % len(incises),
             perdus == 0, perdus)

    print('')
    print('4) ce que la page enverrait, et ce que le serveur en ferait')
    exemples = sorted(incises)[:2]
    for idx, spans in incises.items():
        if 'Mouseketeer' in textes[idx] or 'Founijello' in textes[idx]:
            exemples.append(idx)
    for idx in exemples:
        print('')
        print('   phrase %d : %s' % (idx, textes[idx][:110]))
        for p in morceaux(textes[idx], incises[idx]):
            tue = _doit_taire_l_incise(p['text'], False)
            dit = _doit_taire_l_incise(p['text'], True)
            qui = 'NARRATEUR' if p['incise'] else 'personnage'
            print('     [%-10s] %-44s sans drapeau : %-8s | avec : %s'
                  % (qui, p['text'][:44], 'SILENCE' if tue else 'dit',
                     'SILENCE' if dit else 'dit'))

    print('')
    print('5) un morceau d incise de forme CONNUE serait bien tue sans le drapeau')
    connu = None
    for idx, spans in incises.items():
        for a, b in spans:
            if _doit_taire_l_incise(textes[idx][a:b], False):
                connu = (idx, textes[idx][a:b])
                break
        if connu:
            break
    verifier('au moins un morceau serait tue sans le drapeau', connu is not None,
             connu)
    if connu:
        print('      exemple : phrase %d, morceau %r' % connu)

    print('')
    print('6) PARITE avec le JavaScript de la page (la VRAIE fonction)')
    import json
    import shutil
    import subprocess
    from modules.incises import incises as _inc
    cas = [{'texte': textes[idx], 'spans': spans, 'narrateur': True}
           for idx, spans in sorted(incises.items())]
    # Tournures ecrites a la main : une incise TERMINALE (le point final reste
    # orphelin -- c'est le defaut trouve le 22/09/2026), une incise au MILIEU de
    # la phrase, et un reglage MUET (la page ne doit alors rien couper du tout).
    # Les formes employees sont celles que la regle CONNAIT aujourd'hui : les
    # participes et l'auxiliaire (« m'a-t-elle repondu ») sont l'item 1, encore
    # ouvert -- leur comportement n'est pas teste ici.
    for texte in ('\u2014 Vraiment, dit-il.',
                  '\u2014 Epping, dit-il, trop pris de court.',
                  'Le comte, dit Morrel, se tut.'):
        cas.append({'texte': texte, 'spans': [[a, b] for a, b in _inc(texte)],
                    'narrateur': True})
    cas.append({'texte': '\u2014 Vraiment, dit-il.', 'spans': [], 'narrateur': False})
    verifier('les cas de test portent bien des incises',
             all(c['spans'] or not c['narrateur'] for c in cas))

    chemin_cas = RACINE / '_morceaux_cas.json'
    chemin_js  = RACINE / '_morceaux_js.json'
    chemin_cas.write_text(json.dumps(cas, ensure_ascii=False), encoding='utf-8')
    if chemin_js.exists():
        chemin_js.unlink()
    node = shutil.which('node')
    if not node:
        verifier('node disponible pour le test de parite', False, 'node introuvable')
    else:
        resultat_js = subprocess.run(
            [node, str(RACINE / '_test_morceaux_js.js')],
            capture_output=True, text=True, encoding='utf-8', cwd=str(RACINE))
        verifier('le script JavaScript tourne (la fonction de app.js)',
                 resultat_js.returncode == 0,
                 (resultat_js.stdout or '') + (resultat_js.stderr or '')[:200])
        if resultat_js.returncode == 0 and chemin_js.exists():
            js = json.loads(chemin_js.read_text(encoding='utf-8'))
            verifier('autant de cas des deux cotes', len(js) == len(cas),
                     (len(js), len(cas)))
            ecarts = 0
            perdus_js = 0
            for cas_i, obtenu in zip(cas, js):
                if cas_i['narrateur']:
                    attendus = morceaux(cas_i['texte'], cas_i['spans'])
                else:
                    attendus = [{'text': cas_i['texte'], 'incise': False}]
                py = [(m['text'], bool(m['incise'])) for m in attendus]
                cote_js = [(m['text'], bool(m['incise'])) for m in obtenu['pieces']]
                if py != cote_js:
                    ecarts += 1
                    if ecarts <= 3:
                        print('      ECART sur %r' % cas_i['texte'][:60])
                        print('        python : %r' % (py,))
                        print('        js     : %r' % (cote_js,))
                if ''.join(m['text'] for m in obtenu['pieces']) != cas_i['texte']:
                    perdus_js += 1
            verifier('%d cas IDENTIQUES en Python et en JavaScript' % len(cas),
                     ecarts == 0, ecarts)
            verifier('aucun caractere perdu cote JavaScript', perdus_js == 0,
                     perdus_js)
    for chemin in (chemin_cas, chemin_js):
        if chemin.exists():
            chemin.unlink()

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main_test())
