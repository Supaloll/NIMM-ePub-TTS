# -*- coding: utf-8 -*-
"""LE PHONETISEUR AUX ORDRES DES NOMS ANGLAIS -- l'ESSAI du 16/10/2026.

CE QUE LAURENT A DEMANDE, mot pour mot : « *ca serait de prendre la prononciation
des noms anglais "a l'anglaise", qui ferait une transcription automatique sur les
noms lus en francais. Mais je ne sais pas si c'est possible. Que ca se fasse
automatiquement. Est-ce qu'un outil existe pour ca ? Je sais qu'il y a des
phonetiseurs qui tournent en python. Donc si mon idee est faisable, j'imaginais un
programme qui extrait les noms anglais, les passe dans un phonetiseur, regarde
comment ils sont prononces, et fait une transcription pour la prononciation en
francais.* »

LA REPONSE, ET ELLE EST VERIFIEE ICI, PAS PROMISE :

  1. LE PHONETISEUR EXISTE DEJA DANS LE PROJET -- espeak-ng, par le paquet
     `phonemizer` : c'est LUI qui sert a Kokoro depuis le 21/09/2026. Il tourne en
     python, hors ligne, gratuitement, et il sait dire **l'anglais ET le francais**.
     Il n'y a donc rien a installer.
  2. CE QUI N'EXISTE PAS TOUT FAIT : la conversion « phonemes anglais -> GRAPHIE
     francaise ». C'est LA FORMULE a ecrire, et c'est ce que ce fichier met au
     point. Elle tient en UNE TABLE (chaque phoneme anglais -> la graphie
     francaise qui s'en approche) plus QUELQUES LEVIERS (les choix globaux, comme
     le son du « u » de Dunning) -- pas de cas par cas.
  3. CE QUE CE FICHIER FAIT, DANS L'ORDRE : il prend un nom anglais, demande ses
     phonemes a espeak-ng (en-us), applique la formule, puis RE-PHONEMISE la
     graphie obtenue EN FRANCAIS et MESURE l'ecart avec la cible anglaise. Le
     score affiche est INDICATIF et pas encore etalonne : c'est l'oreille de
     Laurent qui l'etalonnera (sur deux ou trois noms), apres quoi la formule
     fait le reste du livre.

LES LIMITES, DITES FRANCHEMENT (le francais n'a pas ces sons) :
  - le **h** anglais est MUET en francais (« Harry » perd son souffle) ;
  - le **th** se rapproche de « s » ou « z » (« the » -> « ze ») ;
  - la **place de l'accent** ne se transcrit pas : le rythme du nom restera un peu
    francais. C'est la limite honnete de la methode.

LECTURE SEULE : ni la base, ni les voix, ni le service, ni `modules/` ne sont
touches. Aucun moteur a allumer, rien de facture, aucun acces Internet.
Le detail chiffre part dans `test_voix/_essai_prononciation_anglaise.txt` (les
phonemes a l'ecran seraient illisibles : regle du projet).

Usage : python test_voix/_essai_prononciation_anglaise.py
"""

import io
import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

SORTIE = ICI / '_essai_prononciation_anglaise.txt'

# ============================================================
# LE PHONETISEUR (espeak-ng, par `phonemizer` : il est deja la)
# ============================================================

def _charger_le_phonetiseur():
    """Rend une fonction `phonemize(texte, language=..., backend=...)`.

    UN MOTEUR PROPRE A CHAQUE APPEL -- et ce n'est pas du zele, c'est une MESURE
    du 16/10/2026 : espeak-ng garde un ETAT entre les appels, et melanger
    l'anglais et le francais dans la meme session le fait DERAILER. « Harry
    Dunning » demande en anglais apres une dizaine d'appels en francais ne rendait
    plus que « h » : la formule sortait alors une graphie VIDE, et l'essai
    tombait. On refait donc un moteur a chaque appel (quelques millisecondes).
    """
    import espeakng_loader
    from phonemizer.backend import EspeakBackend
    from phonemizer.backend.espeak.wrapper import EspeakWrapper

    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())

    def phonemize(texte, language='fr-fr', backend='espeak'):
        return EspeakBackend(language=language).phonemize([texte])
    return phonemize


def _verifier_la_stabilite(phonemize):
    """GARDE-FOU : le meme nom donne-t-il TOUJOURS le meme resultat ?

    On l'appelle AVANT de mesurer, et on l'ecrit dans le rapport : sans cela, une
    mesure faite sur un phonetiseur deraille se lirait comme une verite.
    """
    temoin = 'Harry Dunning'
    avant = phonemize(temoin, language='en-us', backend='espeak')
    phonemize('Deke Simmons', language='fr-fr', backend='espeak')   # on melange
    apres = phonemize(temoin, language='en-us', backend='espeak')
    return avant == apres



def _ipa(phonemize, texte, langue):
    """Les phonemes d'un texte, sans les marques de langue d'espeak-ng.

    La marque (« (en) », « (fr) ») apparait quand espeak-ng change de
    dictionnaire au milieu d'un mot : c'est le defaut etabli le 20/09/2026, et
    elle n'a rien a faire dans une mesure.

    GARDE-FOU (16/10/2026) : sur une graphie que le moteur francais ne sait pas
    lire, espeak-ng peut rendre une liste VIDE -- et `[0]` faisait tomber tout
    l'essai. On rend donc une chaine vide, que les appelants savent traiter.
    """
    resultat = phonemize(texte, language=langue, backend='espeak')
    if not resultat:
        return ''
    return re.sub(r'\([a-z]{2}(?:-[a-z]{2})?\)', '', resultat[0]).strip()


# ============================================================
# LA FORMULE : chaque phoneme anglais -> la graphie francaise la plus proche
# ============================================================
# L'ORDRE COMPTE : les phonemes de DEUX caracteres viennent d'abord (le programme
# essaie toujours le motif le plus long, sinon « eɪ » serait lu « e » puis « ɪ »).
# Les valeurs entre accolades sont des LEVIERS : des choix GLOBAUX, tranches UNE
# FOIS a l'oreille, qui valent ensuite pour tout le livre.
FORMULE = [
    # -- voyelles longues et diphtongues ------------------------------------
    ('iː', 'i'),     ('ɪə', 'ie'),   ('eɪ', 'é'),   ('aɪ', 'aï'),
    ('ɔɪ', 'oï'),    ('əʊ', 'ô'),    ('oʊ', 'ô'),   ('aʊ', 'ao'),
    ('eə', 'èr'),    ('ʊə', 'our'),  ('ɑː', 'â'),   ('ɔː', 'ô'),
    ('uː', 'ou'),    ('ɜː', 'eu'),   ('ɪ', 'i'),    ('ʊ', 'ou'),
    # -- voyelles breves ----------------------------------------------------
    ('æ', 'a'),      ('ʌ', '{u_bref}'), ('ə', 'e'), ('e', 'è'), ('ɒ', 'o'),
    ('ɔ', 'o'),      ('ɑ', 'a'),     ('ɛ', 'è'),
    # -- consonnes a deux caracteres ---------------------------------------
    ('tʃ', 'tch'),   ('dʒ', 'dj'),   ('ŋ', '{fin_ing}'),
    # -- consonnes ----------------------------------------------------------
    ('ʃ', 'ch'),     ('ʒ', 'j'),     ('θ', 's'),    ('ð', 'z'),
    ('ɹ', 'r'),      ('ɡ', 'g'),     ('j', 'y'),    ('w', 'w'),
    # -- les lettres qui s'ecrivent PAREIL en francais ----------------------
    # (mesure du 16/10/2026 : sans ces lignes, la formule les PERDAIT -- « Al
    # Templeton » sortait en « a èee ». C'est le filet de securite qui les
    # rattrapait avant, et c'est la table qui doit les porter.)
    ('b', 'b'),      ('d', 'd'),     ('f', 'f'),    ('g', 'g'),
    ('k', 'k'),      ('l', 'l'),     ('m', 'm'),    ('n', 'n'),
    ('p', 'p'),      ('s', 's'),     ('t', 't'),    ('v', 'v'),
    ('z', 'z'),      ('a', 'a'),     ('i', 'i'),    ('o', 'o'), ('u', 'ou'),
    # -- les symboles de l'anglais AMERICAIN (rencontres sur « Dockerty ») ----
    ('ɚ', 'eur'),    ('ɝ', 'eur'),   ('ɾ', 't'),    ('ɐ', 'e'),
    # -- le « h » anglais n'existe pas en francais : il DISPARAIT ------------
    ('h', ''),
]

# LES LEVIERS : les seuls choix globaux de la formule. Chacun vient d'un cas reel
# (le « u » de Dunning, la fin de Epping/Dunning) ; c'est l'OREILLE qui tranche,
# une fois, et pour tout le livre ensuite.
LEVIERS = {
    'u_bref': 'eu',      # le /ʌ/ de « Dunning », « Cullum » : 'eu' | 'a' | 'e'
    'fin_ing': 'ng',     # la fin /ŋ/ de « Dunning », « Epping » : 'ng' | 'ngne'
}
LEVIERS_POSSIBLES = {'u_bref': ['eu', 'a', 'e'], 'fin_ing': ['ng', 'ngne', 'nne']}

# Les lettres qui font une VOYELLE dans une graphie francaise (sert a la regle
# des nasales, plus bas).
VOYELLES = set('aeiouyéèêàâôûùîïœø')


def _eviter_les_nasales(mot):
    """Double le n ou le m qui declencherait une nasale francaise.

    LE PIEGE (constat du 16/10/2026) : « Simmons » lu par un moteur francais sort
    en « Si-mon » -- le « on » francais est NASAL, alors que l'anglais dit
    « si-meunz ». Le remede est celui de la langue francaise elle-meme : une
    DOUBLE consonne empeche la nasale (« bonne » se dit /bɔn/, « bon » se dit
    /bɔ̃/). Donc : un n ou un m precede d'une voyelle et suivi d'une consonne (ou
    de la fin du mot) est double. « Simenz » -> « Simennz ».
    """
    sortie = []
    for rang, lettre in enumerate(mot):
        sortie.append(lettre)
        if lettre not in 'nm':
            continue
        avant = mot[rang - 1] if rang else ''
        apres = mot[rang + 1] if rang + 1 < len(mot) else ''
        if apres == lettre:
            continue                      # deja double : rien a faire
        if avant in VOYELLES and (apres == '' or apres not in VOYELLES):
            sortie.append(lettre)
    return ''.join(sortie)


def _graphie(ipa, leviers):
    """LA FORMULE, APPLIQUEE : une suite de phonemes anglais -> une graphie francaise.

    Aucun cas par cas : on parcourt les phonemes, on prend le motif le plus long,
    et on ecrit la graphie de la table. Ce que la table ne connait pas est recopie
    tel quel (mieux vaut une lettre qu'un trou).
    """
    reste = re.sub(r'[ˈˌ.]', '', ipa)          # accents et frontieres : inutiles
    morceaux = []
    while reste:
        for phoneme, rendu in FORMULE:
            if reste.startswith(phoneme):
                morceaux.append(rendu.format(**leviers))
                reste = reste[len(phoneme):]
                break
        else:
            # Un caractere INCONNU de la table n'est JAMAIS recopie tel quel : il
            # est IGNORE (sauf l'espace, qui separe les mots). Le recopier a
            # produit le pire resultat de l'essai du 16/10/2026 -- « Dockerty »
            # sortait en « de aaksɑ̃siʁkɔ̃flɛks ka ʃwɑːhʊk ɑːtap i » (23 %),
            # parce que deux symboles anglais americains (ɚ, ɾ) sont partis au
            # moteur francais tels quels.
            inconnu = reste[0]
            reste = reste[1:]
            if inconnu.isspace():
                morceaux.append(' ')            # on garde les espaces entre les mots
            elif inconnu.isascii() and inconnu.isalpha():
                morceaux.append(inconnu)        # une lettre simple : telle quelle
            # tout autre SYMBOLE est IGNORE (mesure du 16/10/2026)
    return _eviter_les_nasales(''.join(morceaux))


# ============================================================
# LE TRI AUTOMATIQUE : mesurer de combien une graphie s'approche de l'anglais
# ============================================================

def _phonemes(ipa):
    """Une chaine IPA -> une liste de phonemes (les motifs longs d'abord)."""
    connus = sorted({p for p, _ in FORMULE if len(p) > 1}, key=len, reverse=True)
    reste = re.sub(r'[ˈˌ.]', '', ipa)
    sortie = []
    while reste:
        for motif in connus:
            if reste.startswith(motif):
                sortie.append(motif)
                reste = reste[len(motif):]
                break
        else:
            sortie.append(reste[0])
            reste = reste[1:]
    return sortie


def _famille(phoneme):
    """V (voyelle) ou C (consonne) : une voyelle pour une voyelle est moins grave
    qu'un k pour un n."""
    return 'V' if any(c in 'aeiouyøœɐɪʊəɛɔæʌɜɒɑ' for c in phoneme) else 'C'


def _proximite(cible, obtenu):
    """De 0 % (rien a voir) a 100 % (les memes phonemes).

    Distance de Levenshtein sur les PHONEMES : insertion ou suppression = 1,
    substitution = 1, mais 0,4 seulement dans la MEME famille. C'est ce score qui
    triera les candidats tout seul -- quand l'oreille l'aura etalonne.
    """
    a, b = _phonemes(cible), _phonemes(obtenu)
    if not a and not b:
        return 100.0
    grille = [[0.0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        grille[i][0] = float(i)
    for j in range(len(b) + 1):
        grille[0][j] = float(j)
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cout = 0.0
            elif _famille(a[i - 1]) == _famille(b[j - 1]):
                cout = 0.4
            else:
                cout = 1.0
            grille[i][j] = min(grille[i - 1][j] + 1.0,
                               grille[i][j - 1] + 1.0,
                               grille[i - 1][j - 1] + cout)
    distance = grille[len(a)][len(b)]
    return max(0.0, 100.0 * (1.0 - distance / float(max(len(a), len(b)))))


def _ligne_du_tableau(phonemize, nom):
    """Tout ce qu'on sait d'un nom : la cible, ce que dit le francais, la formule.

    On note aussi les MARQUES DE LANGUE d'espeak-ng (« (en) ») : quand il en met,
    c'est que LUI-MEME a reconnu un mot anglais en lisant du francais -- c'est un
    detecteur GRATUIT de « ce nom est anglais », verifie sur les livres le
    20/09/2026. Il servira a ne pas passer a l'anglaise les noms francais.
    """
    cible = _ipa(phonemize, nom, 'en-us')                    # la CIBLE : l'anglais
    brut_fr = phonemize(nom, language='fr-fr', backend='espeak')[0]
    marques = re.findall(r'\([a-z]{2}(?:-[a-z]{2})?\)', brut_fr)
    lu = re.sub(r'\([a-z]{2}(?:-[a-z]{2})?\)', '', brut_fr).strip()
    graphie = _graphie(cible, LEVIERS)
    graphie_lue = _ipa(phonemize, graphie, 'fr-fr')
    return {
        'nom': nom,
        'cible': cible,
        'lu': lu,
        'marques': marques,
        'graphie': graphie,
        'graphie_lue': graphie_lue,
        'score_lu': _proximite(cible, lu),
        'score_graphie': _proximite(cible, graphie_lue),
    }


def _essayer_les_leviers(phonemize, nom):
    """Le TRI AUTOMATIQUE en clair : toutes les combinaisons de leviers, notees.

    C'est la promesse de la demande de Laurent : la machine essaie, note et classe
    -- l'oreille ne juge plus que les premieres lignes, au lieu de tout.
    """
    cible = _ipa(phonemize, nom, 'en-us')
    resultats = []
    for u_bref in LEVIERS_POSSIBLES['u_bref']:
        for fin_ing in LEVIERS_POSSIBLES['fin_ing']:
            leviers = {'u_bref': u_bref, 'fin_ing': fin_ing}
            graphie = _graphie(cible, leviers)
            score = _proximite(cible, _ipa(phonemize, graphie, 'fr-fr'))
            resultats.append((score, u_bref, fin_ing, graphie))
    resultats.sort(reverse=True)
    return resultats


# ============================================================
# LES NOMS DE L'ESSAI
# ============================================================
# Les 12 noms du banc d'ecoute du 16/10/2026 (ceux que Laurent a sous les
# oreilles), plus quelques-uns du meme livre lus par d'autres moteurs : on voit
# ainsi la formule sur des noms qu'il connait deja.
NOMS = [
    'Jake Epping', 'Al Templeton', 'Deke Simmons', 'Harry Dunning',
    'Mimi Corcoran', 'Bill Turcotte', 'Ellen Dockerty', 'Mike Coslaw',
    'Marguerite Oswald', 'Beverly Marsh', 'Freddy Quinlan',
    'Jacqueline Kennedy', 'Sadie Clayton', 'Lee Oswald', 'Richie Tozier',
    'Edwin Walker',
]


def _detail(phonemize, nom):
    """Montre UN nom en detail : ce qui entre, ce qui sort.

    A l'ecran, tout est en ASCII (`ascii`) : les phonemes IPA sont illisibles dans
    une console Windows, et c'est la regle du projet. Mais la STRUCTURE se lit.
    """
    cible = _ipa(phonemize, nom, 'en-us')
    graphie = _graphie(cible, LEVIERS)
    print('  nom       : %s' % nom)
    print('  BRUT en-us   : %s' % ascii(phonemize(nom, language='en-us',
                                                  backend='espeak')))
    print('  BRUT fr-fr   : %s' % ascii(phonemize(nom, language='fr-fr',
                                                  backend='espeak')))
    print('  IPA anglais  : %s' % ascii(cible))
    print('  graphie      : %s' % ascii(graphie))
    print('  lu en fr     : %s' % ascii(phonemize(nom, language='fr-fr',
                                                 backend='espeak')))
    print('  graphie en fr: %s' % ascii(phonemize(graphie, language='fr-fr',
                                                  backend='espeak')))
    print('')


def _arguments():
    """Les options : `--nom` sert de LOUPE sur un nom precis."""
    import argparse
    analyseur = argparse.ArgumentParser(
        description="L'essai du phonetiseur sur les noms anglais de 22/11/63.")
    analyseur.add_argument('--nom', action='append', default=[],
                           help='montre un nom en detail (repetable)')
    return analyseur.parse_args()


def main():
    options = _arguments()
    phonemize = _charger_le_phonetiseur()

    if options.nom:
        for nom in options.nom:
            _detail(phonemize, nom)
        return 0

    lignes = [
        "L'ESSAI DU PHONETISEUR SUR LES NOMS ANGLAIS (16/10/2026)",
        "=" * 66,
        "Phonetiseur : espeak-ng, par le paquet `phonemizer` -- DEJA installe dans",
        "le projet (c'est celui qui sert a Kokoro depuis le 21/09/2026).",
        "",
        "   CIBLE   = les phonemes ANGLAIS du nom : ce qu'on veut entendre.",
        "   LU      = les phonemes FRANCAIS du nom tel qu'il est ecrit (le defaut).",
        "   FORMULE = la graphie construite AUTOMATIQUEMENT, et ce que le francais",
        "             en dit -- puis la proximite des deux avec la CIBLE.",
        "   MARQUES = les bascules de langue d'espeak-ng : quand il ecrit « (en) »",
        "             en lisant du francais, C'EST LUI qui a reconnu de l'anglais.",
        "",
    ]
    print('=' * 70)
    print('  ESSAI DU PHONETISEUR SUR LES NOMS ANGLAIS')
    print('=' * 70)
    stable = _verifier_la_stabilite(phonemize)
    print('  phonetiseur stable (meme nom, meme resultat) : %s'
          % ('OK' if stable else 'NON -- mesure a refaire'))
    lignes.append('Phonetiseur stable (meme nom, meme resultat) : %s'
                  % ('OK' if stable else 'NON -- mesure a refaire'))
    lignes.append('')

    mieux = 0
    for nom in NOMS:
        try:
            ligne = _ligne_du_tableau(phonemize, nom)
        except Exception as erreur:
            # Un nom qui resiste ne doit pas faire perdre tout le reste : on le
            # note, et on continue (garde-fou du 16/10/2026, appris a l'essai).
            print('  %-22s ECHEC (%s)' % (nom, type(erreur).__name__))
            lignes.append('%s : ECHEC (%s)' % (nom, type(erreur).__name__))
            lignes.append('')
            continue
        if ligne['score_graphie'] > ligne['score_lu']:
            mieux += 1
        marques = ('  bascule : ' + ' '.join(ligne['marques'])) if ligne['marques'] else ''
        lignes.extend([
            '%s%s' % (ligne['nom'], marques),
            '   CIBLE        : %s' % ligne['cible'],
            '   LU (defaut)  : %s   -> proximite %.0f %%'
            % (ligne['lu'], ligne['score_lu']),
        ])
        if ligne['marques']:
            # C'est un point de methode, mesure le 16/10/2026 : espeak-ng bascule
            # TOUT SEUL en anglais pour les noms qu'il reconnait. Sa « lecture
            # francaise » n'est donc PAS ce que fait le moteur Qwen, qui est un
            # autre moteur -- c'est l'oreille de Laurent qui dit ce que Qwen fait.
            lignes.append('   (espeak-ng bascule TOUT SEUL en anglais sur ce nom :'
                          ' la ligne LU n est donc pas ce que le moteur Qwen fait.)')
        lignes.extend([
            '   FORMULE      : %s' % ligne['graphie'],
            '   FORMULE, LUE : %s   -> proximite %.0f %%'
            % (ligne['graphie_lue'], ligne['score_graphie']),
            '',
        ])
        print('  %-22s formule %3.0f %%   contre   aujourd hui %3.0f %%'
              % (nom, ligne['score_graphie'], ligne['score_lu']))

    lignes.extend(['', '=' * 66,
                   'LE TRI AUTOMATIQUE : toutes les combinaisons de leviers',
                   '=' * 66, '',
                   'Chaque ligne = une formule complete, notee sur les phonemes.',
                   'La machine garde les premieres, l oreille ne juge que celles-la.',
                   ''])
    for nom in ('Jake Epping', 'Deke Simmons', 'Harry Dunning'):
        lignes.append(nom)
        try:
            essais = _essayer_les_leviers(phonemize, nom)
        except Exception as erreur:
            lignes.append('   ECHEC (%s)' % type(erreur).__name__)
            essais = []
        for score, u_bref, fin_ing, graphie in essais:
            lignes.append('   %3.0f %%   u_bref=%-2s  fin_ing=%-4s  ->  %s'
                          % (score, u_bref, fin_ing, graphie))
        lignes.append('')

    lignes.extend([
        '=' * 66,
        'CE QUE DIT CET ESSAI',
        '  1. le phonetiseur est DEJA LA, il parle les DEUX langues, hors ligne et',
        '     gratuitement : il n y a rien a installer ;',
        '  2. la formule est UNE TABLE de ~40 lignes plus QUELQUES LEVIERS globaux :',
        '     aucun cas par cas a maintenir ;',
        '  3. sur %d noms, la formule bat la lecture francaise actuelle sur %d.'
        % (len(NOMS), mieux),
        '',
        'CE QUE CE N EST PAS ENCORE : ce score n est pas etalonne. C est l oreille',
        'de Laurent qui l etalonnera sur deux ou trois noms ; ensuite la formule',
        'triera toute seule, et il n aura plus a juger 100 noms un par un.',
        '',
        'LES LIMITES DU FRANCAIS, dites franchement :',
        '  - le h anglais est muet en francais (le souffle de Harry se perd) ;',
        '  - le th devient s ou z (« the » -> « ze ») ;',
        '  - la place de l ACCENT ne se transcrit pas : le rythme restera un peu',
        '    francais, quelle que soit la graphie.',
    ])
    SORTIE.write_text('\n'.join(lignes) + '\n', encoding='utf-8')

    print('')
    print('  detail chiffre (les phonemes sont illisibles a l ecran) : %s'
          % SORTIE.name)
    print('  la formule fait mieux que la lecture actuelle sur %d noms sur %d.'
          % (mieux, len(NOMS)))
    return 0


if __name__ == '__main__':
    sys.exit(main())



