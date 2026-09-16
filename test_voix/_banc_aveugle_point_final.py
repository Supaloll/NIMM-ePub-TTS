# -*- coding: utf-8 -*-
"""Test A L'AVEUGLE : le point final bride-t-il la PROSODIE ? (16/09/2026)

Constat de Laurent, a l'ecoute du banc precedent : avec le point final, la voix
« descend partout » et bouge peu ; sans le point, elle est plus vivante
(montees sur « enfin », « marche »). Mais le moteur est ALEATOIRE : un seul
tirage ne prouve rien. Ce banc masque donc les variantes.

Principe :
  - la meme phrase est generee plusieurs fois AVEC et SANS son point final ;
  - les fichiers sont renommes `echantillon_01.wav`, `02`... dans un ordre
    melange : IMPOSSIBLE de savoir laquelle est laquelle en ecoutant ;
  - la correspondance est ecrite dans `correspondance.txt`, a n'ouvrir qu'APRES
    avoir donne son classement (sinon le test ne vaut rien).

Ce qu'on demande a Laurent : ecouter les 12 echantillons et dire lesquels ont
une voix qui BOUGE (montees et descentes variees). Puis on revele : si les
« sans point » sont nettement majoritaires, on retire le point final dans le
service XTTS ; sinon, c'est du hasard et on garde tout comme aujourd'hui.

Le moteur XTTS doit etre allume. Usage :
    python test_voix/_banc_aveugle_point_final.py
"""

import datetime
import json
import random
import sys
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.stdout.reconfigure(encoding='utf-8')

from _banc_ecoute_xtts import demander, mesurer, SERVICE      # noqa: E402

PHRASES = [
    ("A", "Il arriva enfin, après trois jours de marche, au pied de la tour."),
    ("B", "Elle le regarda longuement, puis détourna les yeux."),
]
REPETITIONS = 3
VOIX = "dp_femme003"
GRAINE = 20260916          # pour que le melange soit reproductible


def retirer_point(phrase):
    """La meme phrase sans son point final (on ne touche ni ? ni !)."""
    return phrase[:-1].rstrip() if phrase.endswith('.') else phrase


def main_banc():
    try:
        with urllib.request.urlopen(SERVICE + "/sante", timeout=5) as reponse:
            sante = json.loads(reponse.read().decode('utf-8'))
        if not sante.get("pret"):
            print("Le moteur XTTS n'est pas encore pret (chargement en cours).")
            return 1
    except Exception as erreur:
        print("Le moteur XTTS ne repond pas sur %s (%s)." % (SERVICE, erreur))
        return 1

    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = ICI / ('aveugle_point_' + horodatage)
    dossier.mkdir(parents=True, exist_ok=True)

    # 1) Fabriquer les tirages, sans les ranger dans l'ordre.
    tirages = []
    for code, phrase in PHRASES:
        for repetition in range(1, REPETITIONS + 1):
            tirages.append(("avec_point", code, phrase))
            tirages.append(("sans_point", code, retirer_point(phrase)))

    hasard = random.Random(GRAINE)
    ordre = list(range(len(tirages)))
    hasard.shuffle(ordre)

    print("Test a l'aveugle — dossier : %s" % dossier)
    print("12 echantillons, ordre melange. Chaque echantillon : ~3 a 4 s.")
    print("=" * 74)

    correspondance = ["CORRESPONDANCE DU TEST A L'AVEUGLE — %s"
                      % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
                      "A N'OUVRIR QU'APRES AVOIR DONNE SON CLASSEMENT.", '']
    melange = []
    for position, index in enumerate(ordre, 1):
        variante, code, phrase = tirages[index]
        texte = phrase if variante == 'avec_point' else retirer_point(phrase)
        try:
            wav = demander(texte, VOIX)
        except Exception as erreur:
            print("echantillon %02d : ECHEC (%s)" % (position, erreur))
            continue
        duree, segments, residu = mesurer(wav)
        nom = 'echantillon_%02d.wav' % position
        (dossier / nom).write_bytes(wav)
        melange.append((position, nom, variante, code, duree, len(segments)))
        correspondance.append('%s  <-  phrase %s, %s  [%.2f s, %d segment(s)]'
                              % (nom, code,
                                 'AVEC le point' if variante == 'avec_point'
                                 else 'SANS le point', duree, len(segments)))
        print('echantillon %02d : genere (%.2f s, %d segment(s))'
              % (position, duree, len(segments)))

    (dossier / 'correspondance.txt').write_text('\n'.join(correspondance),
                                                encoding='utf-8')

    index = [
        "TEST A L'AVEUGLE : LA VOIX BOUGE-T-ELLE MIEUX SANS LE POINT FINAL ?",
        datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), '',
        "12 echantillons de la MEME voix. La moitie des phrases ont ete",
        "envoyees au moteur SANS leur point final (l'autre moitie avec).",
        "L'ordre a ete melange : personne ne peut savoir a l'ecoute.", '',
        "CE QU'ON TE DEMANDE :",
        "  1. ecoute les 12 fichiers (ils durent 3 a 4 secondes chacun) ;",
        "  2. note ceux dont la VOIX BOUGE : montees et descentes variees,",
        "     vivantes -- par opposition a une voix qui descend partout,",
        "     plate ;",
        "  3. donne la liste a Cline (par exemple « 02, 05, 07, 09, 11 »).",
        "     Il revelera alors qui avait le point et qui ne l'avait pas.", '',
        "NE PAS OUVRIR correspondance.txt avant d'avoir repondu !",
        "Le verdict : si les « sans point » sont nettement majoritaires,",
        "on retire le point final dans le service XTTS -- et c'est une ligne.",
    ]
    (dossier / 'index.txt').write_text('\n'.join(index), encoding='utf-8')
    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    print('')
    print("A ecouter : double-clic sur %s" % (dossier / 'ECOUTER_LE_LOT.cmd'))
    print("(la correspondance est cachee dans correspondance.txt — ne pas l'ouvrir")
    print(" avant d'avoir donne son classement !)")
    return 0


if __name__ == '__main__':
    sys.exit(main_banc())
