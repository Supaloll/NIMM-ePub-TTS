# -*- coding: utf-8 -*-
"""Verification du nettoyage des RESIDUS DE BALISES dans le texte (20/09/2026).

A lancer avec le Python du LECTEUR :
    python test_voix/test_residus_html.py

Pourquoi (constat de Laurent, au chapitre 98 du Comte de Monte-Cristo, Tome 5) :
le texte lu et affiche contenait

    « M class="textsuperscript">lle Danglars »

Cause, verifiee dans le fichier EPUB lui-meme : une balise cassee par une
conversion automatique, avec le « > » ECHAPPE -- donc prise pour du TEXTE :

    M<supu0003c span=""> class="textsuperscript"&gt;<span class="ecrm">lle</span>

Ce que le test verifie : ce residu est nettoye, et le texte normal ne l'est
jamais (guillemets, tirets, apostrophes, balises legitimes).
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core.epub_parser import _html_to_text                        # noqa: E402

ECHECS = 0
MOTIF_RESIDU = 'class="textsuperscript"'


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def main():
    print('')
    print('1) le cas reel (Tome 5, chapitre 98)')
    # Le HTML est EXACTEMENT celui du livre : balise cassee + « > » echappe.
    html_reel = (
        '<p class="noindent"><span class="dropcap">E</span>'
        '<span class="small-caps">t maintenant, laissons '
        'M<supu0003c span=""> class="textsuperscript"&gt;'
        '<span class="ecrm">lle</span> Danglars et son amie rouler sur la route '
        'de Bruxelles.</span></p>')
    texte = _html_to_text(html_reel)
    print('   texte obtenu : %s' % texte)
    verifier('le morceau de balise a disparu', MOTIF_RESIDU not in texte, texte)
    verifier('la phrase est redevenue lisible',
             'laissons Mlle Danglars' in texte, texte)
    verifier('la fin de la phrase est intacte',
             'rouler sur la route de Bruxelles' in texte, texte)
    verifier('aucune balise non plus dans le texte',
             '<' not in texte and '>' not in texte, texte)

    print('')
    print('2) le texte normal n est JAMAIS touche')
    cas = [
        ('guillemets francais',
         '<p>Il dit : « Bonjour, comment allez-vous ? » puis sortit.</p>',
         'Il dit : « Bonjour, comment allez-vous ? » puis sortit.'),
        ('tirets de dialogue',
         '<p>— Vous venez ? — Oui, dit-il.</p>',
         '— Vous venez ? — Oui, dit-il.'),
        ('apostrophes et accents',
         "<p>L'abbé Faria n'avait jamais été aussi près du but.</p>",
         "L'abbé Faria n'avait jamais été aussi près du but."),
        ('une egalite dans une phrase',
         '<p>Le total était de 3 = 3, un compte rond.</p>',
         'Le total était de 3 = 3, un compte rond.'),
        ('un chevron isole (mathematiques)',
         '<p>On avait montré que a &lt; b, sans plus de détail.</p>',
         'On avait montré que a < b, sans plus de détail.'),
    ]
    for nom, html, attendu in cas:
        obtenu = _html_to_text(html)
        verifier(nom, obtenu == attendu, '%r au lieu de %r' % (obtenu, attendu))

    print('')
    print('3) une balise legitime reste retiree, comme avant')
    texte = _html_to_text(
        '<p>Le <em>Pharaon</em> entra dans le port, <strong>lentement</strong>.</p>')
    verifier('les mots restent, les balises partent',
             texte == 'Le Pharaon entra dans le port, lentement.', texte)

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : residus de balises dans le texte')
    print('=' * 66)
    sys.exit(main())
