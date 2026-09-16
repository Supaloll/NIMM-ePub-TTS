# -*- coding: utf-8 -*-
"""Test LARGE et A L'AVEUGLE, regroupe PAR PHRASE (16/09/2026, demande de Laurent).

Pourquoi ce second test : le premier (12 echantillons, phrases melangees)
donnait une tendance trop faible, et Laurent a fait remarquer -- tres justement
-- que comparer deux PHRASES DIFFERENTES n'aide pas : « les prosodies sont
tellement variees sur 2 phrases differentes ». Il veut pouvoir comparer a
l'oreille LA MEME phrase, plusieurs fois.

Principe :
  - chaque phrase est generee 10 fois : 5 fois AVEC son point final, 5 fois
    SANS -- dans un ordre melange ;
  - tous les tirages d'une meme phrase portent le meme prefixe (`phraseA_01` a
    `phraseA_10`), donc Laurent peut les enchainer et comparer ce qui est
    comparable ;
  - il ne sait PAS lesquels ont le point : la correspondance est dans
    `correspondance.txt`, a n'ouvrir qu'apres avoir note.

Ce qu'on lui demande : une note par fichier (1 = plat / 2 = moyen /
3 = chantant, vivant). On croise ensuite avec la correspondance.

Le moteur XTTS doit etre allume. Usage :
    python test_voix/_banc_large_point_final.py
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
    ("phraseA", "Il arriva enfin, après trois jours de marche, au pied de la tour."),
    ("phraseB", "Elle le regarda longuement, puis détourna les yeux."),
]
PAR_VARIANTE = 5          # 5 avec le point + 5 sans = 10 tirages par phrase
VOIX = "dp_femme003"
LIBELLE_VOIX = "Yvette"
GRAINE = 20260916


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
    dossier = ICI / ('point_large_' + horodatage)
    dossier.mkdir(parents=True, exist_ok=True)

    hasard = random.Random(GRAINE)
    print("Test large par phrase — dossier : %s" % dossier)
    print("voix : %s | %d tirages par phrase (moitie avec le point)"
          % (LIBELLE_VOIX, PAR_VARIANTE * 2))
    print("=" * 74)

    lignes_corr = ["CORRESPONDANCE DU TEST — %s"
                   % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
                   "A N'OUVRIR QU'APRES AVOIR NOTE LES FICHIERS.", '']
    index = [
        "MEME PHRASE, 10 FOIS : LAQUELLE EST LA PLUS « CHANTANTE » ?",
        "%s — voix %s" % (datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
                          LIBELLE_VOIX), '',
        "Chaque serie contient LA MEME phrase, generee 10 fois. La moitie des",
        "tirages a ete envoyee au moteur SANS son point final : on ne peut pas",
        "savoir lesquels a l'ecoute (l'ordre est melange).", '',
        "CE QU'ON TE DEMANDE : pour CHAQUE fichier, une note :",
        "   1 = plat (la voix descend partout, peu de relief)",
        "   2 = moyen",
        "   3 = chantant, vivant (la voix monte et descend)", '',
        "Ecoute une serie en entier avant de comparer l'autre :",
        "  phraseA_01 ... phraseA_10  (la meme phrase que celle du constat)",
        "  phraseB_01 ... phraseB_10  (l'autre phrase, pour verifier)",
        '',
        "Puis donne la liste a Cline, par exemple :",
        "  phraseA : 1,3,2,3,3,1,2,3,2,3",
        "  phraseB : 2,3,1,3,2,3,3,1,2,3", '',
        "NE PAS OUVRIR correspondance.txt AVANT : c'est la reponse.", '',
        "Ce qu'on cherche : si les « sans point » sont nettement plus souvent",
        "notes 3, on retire le point final dans le service XTTS. Sinon, on",
        "garde tout comme aujourd'hui.",
    ]

    for code, phrase in PHRASES:
        index.append('')
        index.append('--- %s : « %s »' % (code, phrase))
        tirages = [("avec_point", phrase)] * PAR_VARIANTE + \
                  [("sans_point", retirer_point(phrase))] * PAR_VARIANTE
        hasard.shuffle(tirages)
        print('')
        print('%s : « %s »' % (code, phrase))
        for position, (variante, texte) in enumerate(tirages, 1):
            try:
                wav = demander(texte, VOIX)
            except Exception as erreur:
                print('  %02d ECHEC : %s' % (position, erreur))
                continue
            duree, segments, residu = mesurer(wav)
            nom = '%s_%02d.wav' % (code, position)
            (dossier / nom).write_bytes(wav)
            lignes_corr.append('%s  <-  %s  [%.2f s, %d segment(s)]'
                               % (nom,
                                  'AVEC le point' if variante == 'avec_point'
                                  else 'SANS le point', duree, len(segments)))
            print('  %s  (%.2f s, %d segment(s))' % (nom, duree, len(segments)))

    (dossier / 'correspondance.txt').write_text('\n'.join(lignes_corr),
                                                encoding='utf-8')
    (dossier / 'index.txt').write_text('\n'.join(index), encoding='utf-8')
    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    print('')
    print("A ecouter : double-clic sur %s" % (dossier / 'ECOUTER_LE_LOT.cmd'))
    print("(correspondance cachee dans correspondance.txt)")
    return 0


if __name__ == '__main__':
    sys.exit(main_banc())
