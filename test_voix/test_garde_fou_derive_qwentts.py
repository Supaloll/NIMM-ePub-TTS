# -*- coding: utf-8 -*-
"""
Garde-fou de DERIVE du service Qwen3-TTS (renforce le 01/10/2026).

Ce qu'il verifie, SANS charger le moteur (la bibliotheque du moteur est importee
DANS une fonction, pas au niveau du module) :

  1. le plafond d'images `plafond_pour` : proportionnel a la longueur du texte,
     borne dur a 540 images = 43,2 s -- la mesure du 01/10/2026 chez NIMM Voix ;
  2. une phrase NORMALE passe telle quelle, sans etre touchee ;
  3. une phrase qui DERIVE (la sortie atteint le plafond : le moteur n'a pas
     trouve son jeton de fin) est RELANCEE **coupee en deux** : c'est la longueur
     qui cause la derive, donc relancer la phrase entiere a peu de chances de
     faire mieux ;
  4. une phrase dont la 1re sortie est VIDE (silence) est relancee a l'identique.

Le faux moteur rend des blocs de la duree demandee : aucun vrai calcul, aucune
empreinte, aucun modele. Le test ne touche ni aux voix, ni a la base.
"""
import io
import sys
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(RACINE / "qwentts_service"))

import numpy as np                      # noqa: E402
import servir_qwentts_cpp as service    # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


class FauxMoteur:
    """Rend un bloc de la duree demandee, une duree par generation."""

    def __init__(self, durees):
        self.durees = list(durees)
        self.appels = 0

    def stream(self, text=None, lang=None, ref_spk_emb=None, ref_codes=None,
               ref_text=None, max_new_tokens=None, temperature=None):
        duree = self.durees[min(self.appels, len(self.durees) - 1)]
        self.appels += 1
        taux = 24000
        # Amplitude 0,5 : au-dessus du seuil de silence du service (0,01), sinon
        # la phrase serait prise pour un SILENCE et non pour une derive.
        yield np.full(int(duree * taux), 0.5, dtype=np.float32), taux


def preparer(durees):
    """Branche un faux moteur et une voix en cache. Rend le faux moteur."""
    moteur = FauxMoteur(durees)
    service._moteur = moteur
    service._voix_cache = {"essai": (Path("_inexistant.wav"), "texte de reference")}
    service._empreintes = {"essai": (None, None)}
    return moteur


def duree_du_wav(octets):
    with wave.open(io.BytesIO(octets), "rb") as f:
        return f.getnframes() / float(f.getframerate() or 1)


def main():
    print('')
    print('=' * 66)
    print(' GARDE-FOU DE DERIVE -- service Qwen3-TTS')
    print('=' * 66)

    print('')
    print("1) le plafond d'images est proportionnel, borne dur a 540")
    verifier('duree attendue : plancher de 8 s',
             service.duree_attendue('') == 8.0, service.duree_attendue(''))
    verifier('plafond court : 250 images',
             service.plafond_pour('a' * 14) == 250,
             service.plafond_pour('a' * 14))
    verifier('plafond long : borne dur a 540 images',
             service.plafond_pour('a' * 4000) == 540,
             service.plafond_pour('a' * 4000))
    verifier('une sortie de 163,84 s est une DERIVE',
             service.sortie_derivee(163.84, 'Oui, je suis la.') is True)
    verifier("une sortie de 2 s n'est pas une derive",
             service.sortie_derivee(2.0, 'Oui, je suis la.') is False)

    texte = 'Oui, je suis la.'

    print('')
    print('2) une phrase NORMALE passe telle quelle')
    preparer([2.0])
    _wav, duree, _vram, etiquettes = service.generer_wav(texte, 'essai')
    verifier('la duree rendue est celle du moteur (2 s)',
             abs(duree - 2.0) < 0.05, duree)
    verifier('aucune etiquette de derive', etiquettes == '', etiquettes)

    print('')
    print('3) une phrase qui DERIVE est relancee COUPEE EN DEUX')
    texte_long = ('Il marchait dans la rue sans regarder personne, et le vent '
                  'portait au loin le bruit des voitures qui passaient.')
    moteur = preparer([163.84, 2.0, 2.0])
    _wav, duree, _vram, etiquettes = service.generer_wav(texte_long, 'essai')
    verifier('trois appels au moteur (1 entiere + 2 moities)',
             moteur.appels == 3, moteur.appels)
    verifier("l'etiquette dit 'derivee'", 'derivee' in etiquettes, etiquettes)
    verifier("l'etiquette dit 'coupee_en_deux'",
             'coupee_en_deux' in etiquettes, etiquettes)
    verifier('les deux moities plus 0,10 s de silence (4,1 s)',
             abs(duree - 4.1) < 0.1, duree)

    print('')
    print("4) une sortie VIDE (silence) est relancee a l'identique")
    moteur = preparer([0.0, 1.5])
    _wav, duree, _vram, etiquettes = service.generer_wav(texte, 'essai')
    verifier('la reprise apres un silence rend la phrase (1,5 s)',
             abs(duree - 1.5) < 0.05, duree)
    verifier("l'etiquette dit 'vide_relancee'",
             'vide_relancee' in etiquettes, etiquettes)
    verifier('deux appels au moteur', moteur.appels == 2, moteur.appels)

    print('')
    print('=' * 66)
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('=' * 66)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
