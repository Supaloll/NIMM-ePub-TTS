# -*- coding: utf-8 -*-
"""
Garde-fou de DERIVE du service Qwen3-TTS (ajoute le 29/09/2026).

Ce qu'il verifie, SANS charger le moteur (la bibliotheque du moteur est importee
DANS une fonction, pas au niveau du module) :

  1. le plafond `duree_max_derivee` : 3 fois la duree plausible plus 1 s,
     plancher 3 s -- la MEME regle que le service NeuTTS ;
  2. une phrase NORMALE passe telle quelle, sans etre touchee ;
  3. une phrase qui DERIVE (le moteur s'emballe, constat du 29/09/2026 : 163,84 s
     d'audio pour une replique de 8 jetons) est RELANCEE, et si elle derive
     encore, elle est ROGNEE au plafond : on ne livre jamais 163 s de babil ;
  4. une derive SUIVIE d'une phrase juste rend la phrase juste : une relance
     suffit, c'est tout l'interet de relancer plutot que de rogner.

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
               ref_text=None):
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
    print('1) le plafond est celui de NeuTTS (3 x duree plausible + 1 s)')
    verifier('texte vide : plancher de 3 s',
             service.duree_max_derivee('') == 3.0,
             service.duree_max_derivee(''))
    verifier('14 caracteres : 4 s',
             abs(service.duree_max_derivee('a' * 14) - 4.0) < 0.01,
             service.duree_max_derivee('a' * 14))
    verifier('140 caracteres : 31 s',
             abs(service.duree_max_derivee('a' * 140) - 31.0) < 0.01,
             service.duree_max_derivee('a' * 140))

    texte = 'Oui, je suis la.'
    plafond = service.duree_max_derivee(texte)

    print('')
    print('2) une phrase NORMALE passe telle quelle')
    preparer([2.0])
    _wav, duree = service.generer_wav(texte, 'essai')
    verifier('la duree rendue est celle du moteur (2 s)',
             abs(duree - 2.0) < 0.05, duree)

    print('')
    print('3) une phrase qui DERIVE est relancee, puis ROGNEE')
    moteur = preparer([163.84])
    _wav, duree = service.generer_wav(texte, 'essai')
    verifier('le moteur a ete appele %d fois (2 reprises)' % (service.REPRISES + 1),
             moteur.appels == service.REPRISES + 1, moteur.appels)
    verifier('ce qui sort est RAMENE au plafond, jamais 163 s',
             abs(duree - plafond) < 0.05, duree)

    print('')
    print("4) une derive SUIVIE d'une phrase juste rend la phrase juste")
    moteur = preparer([163.84, 1.5])
    _wav, duree = service.generer_wav(texte, 'essai')
    verifier('la relance a suffi (1,5 s rendus)', abs(duree - 1.5) < 0.05, duree)
    verifier('deux appels au moteur, pas trois', moteur.appels == 2, moteur.appels)

    print('')
    print('=' * 66)
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('=' * 66)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
