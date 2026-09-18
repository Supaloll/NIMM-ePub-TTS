# -*- coding: utf-8 -*-
"""Verification du banc « ponctuation du ! » et du retrait des incises.

A lancer avec le Python du LECTEUR (aucun moteur nécessaire) :
    python test_voix/test_ponctuation_incises.py

Ce qui est verifie, et pourquoi :

1. **Les 4 ponctuations** comparees par le banc (point, virgule, suspension,
   rien) sont bien produites, y compris quand le « ! » est AU MILIEU de la
   phrase — et « rien du tout » ne colle pas deux mots ensemble.
2. **Le retrait des incises est PRUDENT** : il ne touche que les incises
   fermées (virgule après) ou terminales, JAMAIS celles suivies d'un
   complément (« , dit-il en souriant, » laisserait « en souriant » tout seul),
   et jamais une incise non fermée au milieu d'une réplique.
3. **Aucun mot n'est inventé ni perdu** : le texte retiré est toujours une
   incise, jamais le sujet de la phrase (c'est le piège du code proposé
   ailleurs, qui supprimait « le jeune homme »).
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / 'test_voix'))
sys.stdout.reconfigure(encoding='utf-8')

from _banc_ponctuation_exclamation import variantes_ponctuation        # noqa: E402
from modules.incises import incises, retirer_incises                 # noqa: E402

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


def texte_de(phrase, code):
    for c, _libelle, texte in variantes_ponctuation(phrase):
        if c == code:
            return texte
    return None


def main():
    print('')
    print('=' * 74)
    print('VERIFICATION : ponctuation du « ! » et retrait des incises')
    print('=' * 74)

    print('')
    print('1) les quatre ponctuations (le « ! » est en fin de phrase)')
    phrase = '\u2014 Oh !'
    egal('P1 le point', texte_de(phrase, 'P1'), '\u2014 Oh.')
    egal('P2 la virgule', texte_de(phrase, 'P2'), '\u2014 Oh,')
    egal('P3 la suspension', texte_de(phrase, 'P3'), '\u2014 Oh\u2026')
    egal('P4 rien du tout', texte_de(phrase, 'P4'), '\u2014 Oh')

    print('')
    print('2) le « ! » AU MILIEU de la phrase')
    milieu = '\u2014 Ha ! que voulez-vous ?'
    egal('P1 remplace le milieu', texte_de(milieu, 'P1'),
         '\u2014 Ha. que voulez-vous ?')
    egal('P4 garde un espace entre les mots', texte_de(milieu, 'P4'),
         '\u2014 Ha que voulez-vous ?')
    verifier('P4 ne colle pas deux mots',
             'Haque' not in (texte_de(milieu, 'P4') or ''))

    print('')
    print('3) les incises de parole sont trouvees (y compris le « t » euphonique)')
    verifier('incise a pronom terminale',
             incises('\u2014 Il partit, dit-il.') != [])
    verifier('incise a nom encadree',
             incises('\u2014 Le fait est, dit Barrois, que je meurs de soif.') != [])
    verifier('incise a nom en fin de replique',
             incises('\u00ab Mon ami, dit Beauchamp.') != [])
    verifier('t euphonique : ajouta-t-il',
             incises('\u2014 Et moi, ajouta-t-il, je partirai.') != [])
    verifier('t euphonique : demanda-t-elle',
             incises('\u00ab Vraiment, demanda-t-elle, et pourquoi ?') != [])
    verifier('t euphonique : dit-on',
             incises('C\u2019est, dit-on, la meilleure part.') != [])
    egal('retrait avec t euphonique',
         retirer_incises('\u2014 Et moi, ajouta-t-il, je partirai.'),
         '\u2014 Et moi je partirai.')

    print('')
    print('3 bis) les formes qui MANQUAIENT (trouvees le 18/09 au soir)')
    verifier('civilite + particule : M. de Villefort',
             incises('\u2014 Oui, dit M. de Villefort, elle sera lente.') != [])
    egal('retrait de « dit M. de Villefort »',
         retirer_incises('\u2014 Oui, dit M. de Villefort, elle sera lente.'),
         '\u2014 Oui elle sera lente.')
    egal('retrait de « reprit la jeune fille »',
         retirer_incises('\u2014 Moi, reprit la jeune fille, je reste.'),
         '\u2014 Moi je reste.')
    egal('retrait de « dit le comte » (nom commun)',
         retirer_incises('\u2014 Vraiment, dit le comte, vous croyez ?'),
         '\u2014 Vraiment vous croyez ?')
    verifier('particule avec apostrophe : dit M. d\u2019Avrigny',
             incises('\u2014 Prenez garde, dit M. d\u2019Avrigny, elle sera lente.') != [])

    print('')
    print('3 ter) les verbes PRONOMINAUX et les imparfaits (remarque de Laurent)')
    egal('« se demanda-t-elle » (le « se » n est pas laisse orphelin)',
         retirer_incises('\u2014 Et lui, se demanda-t-elle, que faisait-il ?'),
         '\u2014 Et lui que faisait-il ?')
    egal('« se reprit-il » entre virgules',
         retirer_incises('\u2014 Non, se reprit-il, ce n est pas cela.'),
         '\u2014 Non ce n est pas cela.')
    egal('imparfait : « disait-il »',
         retirer_incises('\u2014 Vraiment, disait-il, vous croyez ?'),
         '\u2014 Vraiment vous croyez ?')
    verifier('« se reprit-il aussitot » : gardee car suivie d un mot',
             retirer_incises('\u2014 Non, se reprit-il aussitot.') ==
             '\u2014 Non, se reprit-il aussitot.')

    print('')
    print('3 quater) la RELATIVE qui suit l incise part avec elle (18/09 au soir)')
    egal('le cas de Laurent : « dit Cavalcanti, qui se grisait... »',
         retirer_incises('c\u2019est magnifique, dit Cavalcanti, qui se grisait '
                         '\u00e0 ce bruit m\u00e9tallique de paroles dor\u00e9es.'),
         'c\u2019est magnifique')
    egal('« que » conjonction : la suite est GARDEE (Le fait est que...)',
         retirer_incises('\u2014 Le fait est, dit Barrois, que je meurs de soif.'),
         '\u2014 Le fait est que je meurs de soif.')
    egal('question apres l incise : rien n est emporte',
         retirer_incises('\u2014 Et lui, se demanda-t-elle, que faisait-il ?'),
         '\u2014 Et lui que faisait-il ?')
    egal('decrochage « mais » : la suite est GARDEE',
         retirer_incises('\u2014 Il partit, dit-il, qui souriait, mais il revint.'),
         '\u2014 Il partit, mais il revint.')
    egal('decrochage « et » : la suite est GARDEE',
         retirer_incises('\u2014 Il partit, dit-il, qui souriait, et il revint.'),
         '\u2014 Il partit, et il revint.')
    egal('relative COORDONNEE : « , et qui comprit… » part avec l incise',
         retirer_incises('c\u2019est fini, dit Monte-Cristo, qui sentit l\u2019adresse '
                         'perfide du jeune homme, et qui comprit la port\u00e9e de ses '
                         'paroles ; ma protection vous est acquise.'),
         'c\u2019est fini; ma protection vous est acquise.')
    egal('la QUESTION du personnage, en fin de phrase, ne bloque plus',
         retirer_incises('c\u2019est fini, dit Monte-Cristo, qui sentit l\u2019adresse, '
                         'et qui comprit la port\u00e9e ; ma protection vous est acquise, '
                         'n\u2019est-ce pas ?'),
         'c\u2019est fini; ma protection vous est acquise, n\u2019est-ce pas ?')
    egal('sans relative, rien ne change',
         retirer_incises('\u2014 Il partit, dit-il.'), '\u2014 Il partit.')
    # NB : ici le point est celui de la phrase d'origine (il reste en place).

    print('')
    print('4) le retrait est PRUDENT (les pieges ne sont pas touches)')
    egal('incise terminale retiree',
         retirer_incises('\u2014 Il partit, dit-il.'),
         '\u2014 Il partit.')
    egal('incise encadree retiree',
         retirer_incises('\u2014 Le fait est, dit Barrois, que je meurs de soif.'),
         '\u2014 Le fait est que je meurs de soif.')
    egal('incise suivie d un complement : retiree EN ENTIER (18/09 au soir)',
         retirer_incises('\u2014 Il partit, dit-il en souriant.'),
         '\u2014 Il partit')
    egal('incise terminale avec complement',
         retirer_incises('bonjour, dit-il au comte.'), 'bonjour')
    # NB : le point final est remis par `_clean_text` (regle de fin de segment) :
    # c'est pour cela que `test_nettoyage_tts.py` attend « — Il partit. ».
    egal('incise en TETE de phrase (apres un « ! » qui coupe)',
         retirer_incises('fit celui-ci avec sa voix demi-railleuse, comment '
                         'vous portez-vous ?'),
         'comment vous portez-vous ?')
    egal('phrase qui n est QUE l incise : gardee entiere (jamais videe)',
         retirer_incises('ajouta Valentine en s\u2019adressant \u00e0 Noirtier.'),
         'ajouta Valentine en s\u2019adressant \u00e0 Noirtier.')
    egal('incise NON fermee au milieu : NON retiree',
         retirer_incises('\u2014 Mais vous, dit Morrel vous qui \u00eates si cher ?'),
         '\u2014 Mais vous, dit Morrel vous qui \u00eates si cher ?')

    print('')
    print('5) le mot APRES le verbe n est jamais supprime a tort')
    # Le piege du code propose ailleurs : « repondit le jeune homme » sortait
    # « jeune homme » (le sujet disparaissait, le sens cassait).
    phrase_piege = "j\u2019\u00e9coute, r\u00e9pondit le jeune homme ; parlez."
    resultat = retirer_incises(phrase_piege)
    verifier('« le jeune homme » est conserve',
             'jeune homme' in resultat, resultat)
    verifier('la phrase n a pas perdu son sens',
             resultat != 'j\u2019\u00e9coute ; parlez.')

    print('')
    print('%d controles, %d en echec' % (CONTROLES, ECHECS))
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
