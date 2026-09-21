# -*- coding: utf-8 -*-
"""Verifie la PRONONCIATION FRANCAISE IMPOSEE (Kokoro et Piper) -- 21/09/2026.

Ce que le script controle, sans rien allumer (le phonemiseur d'espeak-ng est
fourni par le paquet deja installe, et le modele Kokoro n'est PAS charge) :

  1. la table de prononciation (`modules/prononciation.py`) : chaque mot est
     remplace par sa graphie francaise, la casse est respectee, et les mots qui
     CONTIENNENT le mot cle ne sont jamais touches (« Andreas » n'est pas
     « Andréas ») ;
  2. l'apostrophe courbe redevient droite pour la lecture ;
  3. la MESURE qui protege la table : chaque graphie, donnee au phonemiseur, ne
     doit PLUS basculer en anglais (aucune marque de langue) ET le mot d'origine
     doit bien basculer -- sinon l'entree ne sert a rien, et c'est signale ;
  4. le mecanisme cote moteur : `_phonemes_kokoro` retire les marques de langue
     et ne modifie RIEN quand il n'y en a pas ;
  5. le remede de bout en bout : « Andrea » prepare par la table donne
     EXACTEMENT les phonemes de « Andréa » (le meme son francais) ;
  6. la table n'est appliquee QUE juste avant la synthese (`modules/tts.py`) :
     le texte affiche n'est jamais touche.

A lancer avec le Python du lecteur :
    python test_voix/test_prononciation_kokoro.py
"""

import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from modules import prononciation as _prononciation      # noqa: E402
from modules import tts as _tts                          # noqa: E402
from kokoro_onnx.tokenizer import Tokenizer              # noqa: E402

ECHECS = 0


REMPLACEMENTS_ASCII = {
    'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e', 'É': 'E', 'È': 'E',
    'à': 'a', 'â': 'a', 'À': 'A', 'î': 'i', 'ï': 'i',
    'ô': 'o', 'ö': 'o', 'û': 'u', 'ù': 'u', 'ü': 'u',
    'ç': 'c', 'œ': 'oe', '«': '"', '»': '"',
    '\u2019': "'", '\u2018': "'", '…': '...',
}


def ascii_(texte):
    """Detail lisible et SANS accents : un accent ne doit jamais casser
    l'affichage d'un terminal (regle du projet), et Laurent lit ces lignes."""
    texte = str(texte)
    for avant, apres in REMPLACEMENTS_ASCII.items():
        texte = texte.replace(avant, apres)
    return texte.encode('ascii', 'backslashreplace').decode('ascii')


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + ascii_(nom))
    else:
        print('  ECHEC ' + ascii_(nom)
              + ('  -> ' + ascii_(detail) if detail else ''))
        ECHECS += 1


def phonemes(texte, tokenizer):
    """Phonemes BRUTS du phonemiseur (comme Kokoro les demanderait)."""
    return tokenizer.phonemize(texte, 'fr-fr')


def main():
    tokenizer = Tokenizer()          # espeak-ng seul : pas de modele, pas de WAV
    table = _prononciation.PRONONCIATION

    print('')
    print('1) la table remplace le mot, et respecte la casse')
    verifier('« Andrea » devient « Andréa »',
             _prononciation.pour_lecture('Andrea') == 'Andréa',
             ascii_(_prononciation.pour_lecture('Andrea')))
    verifier('« andrea » en minuscules devient « andréa »',
             _prononciation.pour_lecture('andrea') == 'andréa',
             ascii_(_prononciation.pour_lecture('andrea')))
    verifier('« ANDREA » ne reste PAS en capitales (espeak les epellerait)',
             _prononciation.pour_lecture('ANDREA') == 'Andréa',
             ascii_(_prononciation.pour_lecture('ANDREA')))
    verifier('la phrase entiere est traitee, ponctuation intacte',
             _prononciation.pour_lecture('Andrea partit, puis Nathan.') ==
             'Andréa partit, puis Natan.',
             ascii_(_prononciation.pour_lecture('Andrea partit, puis Nathan.')))

    print('')
    print('2) seuls les MOTS ENTIERS sont touches')
    verifier('« Andreas » n est pas touche',
             _prononciation.pour_lecture('Andreas') == 'Andreas',
             ascii_(_prononciation.pour_lecture('Andreas')))
    verifier('« dosages » n est pas touche',
             _prononciation.pour_lecture('dosages') == 'dosages',
             ascii_(_prononciation.pour_lecture('dosages')))
    verifier('« sur le dos » est touche (mot entier)',
             _prononciation.pour_lecture('sur le dos') == 'sur le dô',
             ascii_(_prononciation.pour_lecture('sur le dos')))

    print('')
    print('3) l apostrophe courbe redevient droite (defaut d espeak-ng)')
    verifier('« d\u2019aujourd\u2019hui » devient « d\'aujourd\'hui »',
             _prononciation.pour_lecture('d\u2019aujourd\u2019hui') ==
             "d'aujourd'hui",
             ascii_(_prononciation.pour_lecture('d\u2019aujourd\u2019hui')))

    print('')
    print('4) MESURE de la table au phonemiseur (la preuve, pas la croyance)')
    for mot, graphie in sorted(table.items()):
        brut = phonemes(mot, tokenizer)
        corrige = phonemes(graphie, tokenizer)
        verifier('%-9s bascule bien en anglais aujourd hui (marque presente)'
                 % mot, '(' in brut, ascii_(brut))
        verifier('%-9s -> %-8s ne bascule plus (aucune marque)'
                 % (mot, graphie), '(' not in corrige, ascii_(corrige))

    print('')
    print('5) cote moteur : les marques de langue sont retirees')
    # Le modele ONNX n'est PAS charge (300 Mo) : on remplace `_kokoro` par un
    # faux objet dont le TOKENIZER est le vrai. `_phonemes_kokoro` ne se sert que
    # de lui -- c'est donc bien la fonction reelle qui est verifiee.
    class FauxKokoro:
        pass

    faux = FauxKokoro()
    faux.tokenizer = tokenizer
    vrai_kokoro = _tts._kokoro
    _tts._kokoro = faux
    try:
        avec = _tts._phonemes_kokoro('Andrea')
        verifier('« Andrea » : plus aucune marque de langue',
                 '(' not in avec and ')' not in avec, ascii_(avec))
        verifier('aucune parenthese de langue oubliee par le motif',
                 not re.search(r'\([a-z]{2}\)', avec), ascii_(avec))
        identique = (_tts._phonemes_kokoro('Andréa')
                     == phonemes('Andréa', tokenizer))
        verifier('un texte sans marque n est pas modifie du tout',
                 identique, ascii_(_tts._phonemes_kokoro('Andréa')))

        print('')
        print('6) le remede de bout en bout : la table + les phonemes')
        remede = _tts._phonemes_kokoro(_prononciation.pour_lecture('Andrea'))
        attendu = phonemes('Andréa', tokenizer)
        verifier('« Andrea » prepare sonne EXACTEMENT comme « Andréa »',
                 remede == attendu, ascii_(remede) + ' / ' + ascii_(attendu))
    finally:
        _tts._kokoro = vrai_kokoro

    print('')
    print('7) le texte affiche n est jamais touche')
    source_tts = (RACINE / 'modules' / 'tts.py').read_text(encoding='utf-8')
    verifier('la table est appelee dans tts.py (Kokoro ET Piper)',
             source_tts.count('_prononciation.pour_lecture(') == 2,
             source_tts.count('_prononciation.pour_lecture('))
    autres = []
    for element in ('modules', 'core', 'main.py'):
        chemin = RACINE / element
        fichiers = ([chemin] if chemin.is_file()
                    else [p for p in chemin.rglob('*') if p.is_file()])
        for fichier in fichiers:
            # `prononciation.py` DEFinit la fonction, `tts.py` l'appelle : les
            # deux sont legitimes. Tout autre fichier qui la cite serait un
            # affichage modifie -- ce qu'on ne veut pas.
            if fichier.suffix != '.py' or fichier.name in ('tts.py',
                                                           'prononciation.py'):
                continue
            if 'pour_lecture' in fichier.read_text(encoding='utf-8',
                                                   errors='replace'):
                autres.append(fichier.name)
    verifier('aucun autre fichier ne l appelle (le texte affiche reste intact)',
             not autres, autres)

    print('')
    print('=' * 66)
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('=' * 66)
    return ECHECS


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
