# -*- coding: utf-8 -*-
"""Vérification du DÉCOUPAGE DES PHRASES (modules/decoupage.py), 18/09/2026.

A lancer avec le Python du LECTEUR (aucun moteur nécessaire) :
    python test_voix/test_decoupage_phrases.py

Ce qui est vérifié, et pourquoi :

1. **La règle corrigée** : une phrase n'est plus coupée après le point d'une
   abréviation de civilité (« … complimenter M. de Morcerf … » est UNE phrase).
   C'était la cause du silence entendu par Laurent après « monsieur ».
2. **L'ancienne règle est bien l'ancienne** : le même texte donne DEUX phrases
   avec `REGLE_ANCIENNE` — c'est ce qui permet de migrer les index de
   `speaker_attribution` sans deviner.
3. **Les positions sont justes** : le texte de chaque phrase est EXACTEMENT
   celui du chapitre à [debut:fin]. La migration des voix repose là-dessus.
4. **Aucun texte perdu** : la réunion des phrases recouvre tout le contenu du
   chapitre — un mot oublié serait un mot jamais lu.
5. **La page fait la même chose que le serveur** : le motif de coupe et la liste
   des abréviations de `frontend/app.js` sont comparés à ceux du module Python
   (ils ne peuvent pas être partagés, mais ils doivent rester identiques).
"""

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.decoupage import (
    phrases, phrases_avec_positions, phrases_d_un_paragraphe,
    MOTIF_COUPE, ABREVIATIONS, REGLE_ANCIENNE,
)

APP_JS = RACINE / 'frontend' / 'app.js'

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


def egal(nom, obtenu, attendu):
    verifier(nom, obtenu == attendu, '%r  (attendu %r)' % (obtenu, attendu))


def main():
    print('')
    print('=' * 74)
    print('VERIFICATION : decoupage des phrases (le silence apres M. / Mme)')
    print('=' * 74)

    print('')
    print('1) une abreviation ne finit plus la phrase')
    le_cas_de_laurent = (
        '\u2014 Quand il vous plaira, repondit Beauchamp, laissez-moi seulement '
        'le temps de complimenter M. de Morcerf ; il a fait preuve aujourd\u2019hui '
        'd\u2019une generosite si chevaleresque.')
    phrases_laurent = phrases(le_cas_de_laurent)
    egal('le cas entendu par Laurent : UNE phrase', len(phrases_laurent), 1)
    egal('et elle commence par le tiret de dialogue',
         phrases_laurent[0].startswith('\u2014 Quand il vous plaira'), True)
    egal('Mme sans point ne coupe pas non plus',
         phrases('Il salua Mme Dupont et partit.'), ['Il salua Mme Dupont et partit.'])
    egal('MM. reste dans sa phrase',
         phrases('Il attendit MM. les deputes.'), ['Il attendit MM. les deputes.'])
    egal('Mgr et Dr gardent leur phrase',
         phrases('Mgr l eveque et le Dr Rieux arriverent.'),
         ['Mgr l eveque et le Dr Rieux arriverent.'])
    # Cas de Laurent (21/09/2026, 22/11/63 chapitre 10) : un texte traduit de
    # l'anglais ecrit « MR. CURRIE ». Non reconnu, « MR. » coupait la phrase
    # juste avant le nom -- et le moteur, seul devant ce morceau, inventait un
    # son (« [féè] »). Les formes en capitales sont donc dans la liste.
    egal('MR. en capitales reste dans sa phrase',
         phrases('Et l\u2019etiquette sur son bureau indiquait MR.\u00a0CURRIE.'),
         ['Et l\u2019etiquette sur son bureau indiquait MR. CURRIE.'])
    egal('la variante Mr. aussi',
         phrases('Il salua Mr.\u00a0Currie.'), ['Il salua Mr. Currie.'])
    egal('MME. en capitales aussi',
         phrases('Il salua MME.\u00a0Dupont.'), ['Il salua MME. Dupont.'])

    print('')
    print('2) mais une VRAIE fin de phrase coupe toujours')
    egal('deux phrases normales',
         phrases('Il arriva. Elle partit.'), ['Il arriva.', 'Elle partit.'])
    egal('apres une abreviation, la phrase suivante est bien separee',
         phrases('Il salua M. Dupont. Puis il partit.'),
         ['Il salua M. Dupont.', 'Puis il partit.'])
    egal('le point d interrogation coupe',
         phrases('Viens-tu ? Il attendit.'), ['Viens-tu ?', 'Il attendit.'])

    print('')
    print('3) l ancienne regle est bien l ancienne (pour la migration)')
    anciennes = phrases(le_cas_de_laurent, REGLE_ANCIENNE)
    egal('le meme texte donnait DEUX phrases', len(anciennes), 2)
    egal('la 1re finissait par l abreviation',
         anciennes[0].endswith('complimenter M.'), True)
    egal('la 2e commencait par le nom',
         anciennes[1].startswith('de Morcerf'), True)

    print('')
    print('4) les positions sont justes (base de la migration)')
    chapitre = ('Premier paragraphe, avec M. Dupont dedans.\n\n'
                'Deuxieme paragraphe. Il continue ici.\n\n'
                'Troisieme paragraphe, court.')
    positions = phrases_avec_positions(chapitre)
    verifier('chaque phrase correspond exactement au texte a [debut:fin]',
             all(chapitre[debut:fin] == texte for debut, fin, texte in positions))
    verifier('les positions sont croissantes',
             all(positions[i][0] < positions[i + 1][0]
                 for i in range(len(positions) - 1)))
    verifier('trois paragraphes, quatre phrases (le 2e en contient deux)',
             len(positions) == 4, len(positions))

    print('')
    print('5) aucun texte perdu (un mot oublie serait un mot jamais lu)')

    def sans_ponctuation(t):
        return re.sub(r'[\s\u00ab\u00bb\u2014]+', '', t)

    lu = ''.join(texte for _d, _f, texte in positions)
    verifier('tout le texte est couvert',
             sans_ponctuation(lu) == sans_ponctuation(chapitre),
             len(sans_ponctuation(lu)))

    print('')
    print('6) la page fait la meme chose que le serveur')
    js = APP_JS.read_text(encoding='utf-8')
    motif_js = re.search(r"para\.split\(/([^/]+)/\)", js)
    verifier('le motif de coupe de app.js existe', motif_js is not None)
    if motif_js:
        egal('motif identique a celui du serveur', motif_js.group(1), MOTIF_COUPE)
    abrev_js = re.search(r'const ABREVIATIONS[^=]*=\s*\[(.*?)\]', js, re.S)
    if abrev_js:
        valeurs_js = tuple(re.findall(r"'([^']+)'", abrev_js.group(1)))
        egal('liste des abreviations identique', valeurs_js, ABREVIATIONS)
    else:
        print('  OK    (la page n a pas encore sa liste : a verifier a la bascule)')

    print('')
    print('7) la recherche du livre suit la meme regle')
    egal('phrases d un paragraphe isole',
         phrases_d_un_paragraphe('Il salua M. Dupont. Puis il partit.'),
         ['Il salua M. Dupont.', 'Puis il partit.'])

    print('')
    print('%d controles, %d en echec' % (CONTROLES, ECHECS))
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
