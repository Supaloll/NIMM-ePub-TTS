# -*- coding: utf-8 -*-
"""Comparaison A/B : le POINT FINAL fait-il dire « point » au moteur XTTS ?

Constat de Laurent (16/09/2026), sur le fichier B_incise_dp_femme003.wav :
« La voix lit "point" a la fin de sa phrase : ... au pied de la tour[point].
Quasiment pas de pause entre "tour" et "point". »

C'est un defaut connu du moteur : XTTS ne sait pas IGNORER la ponctuation, il
essaie de la prononcer (le BACKLOG le documente deja pour les guillemets).

Idee testee ici : lui envoyer la phrase SANS son point final. Le service ne
rajoute rien, donc on peut comparer les deux sans modifier le moteur.

Le moteur etant aleatoire, chaque variante est generee PLUSIEURS FOIS : un seul
tirage ne prouve rien.

Le moteur XTTS doit etre allume. Usage :
    python test_voix/_banc_point_final.py
Sortie : test_voix/point_final_<date>/ (WAV + index.txt + ECOUTER_LE_LOT.cmd)
"""

import datetime
import json
import sys
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.stdout.reconfigure(encoding='utf-8')

from _banc_ecoute_xtts import demander, mesurer, SERVICE      # noqa: E402

# La phrase du constat, plus un temoin : deux fins de phrase differentes.
PHRASES = [
    ("accuse", "Il arriva enfin, après trois jours de marche, au pied de la tour.",
     "la phrase exacte du constat de Laurent"),
    ("temoin", "Elle le regarda longuement, puis détourna les yeux.",
     "une autre fin de phrase, pour verifier que ce n est pas un cas isole"),
]

REPETITIONS = 3
VOIX = "dp_femme003"          # la voix du fichier ou Laurent a entendu « point »
LIBELLE_VOIX = "Yvette (la voix du constat)"


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
        print("Double-clique sur xtts_service\\DEMARRER_XTTS.bat, puis relance.")
        return 1

    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = ICI / ('point_final_' + horodatage)
    dossier.mkdir(parents=True, exist_ok=True)

    print("Comparaison A/B du point final — dossier : %s" % dossier)
    print("voix : %s" % LIBELLE_VOIX)
    print("=" * 74)
    lignes = ["POINT FINAL : AVEC ou SANS ? — %s"
              % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), '',
              "Ce qu'on cherche : le moteur dit-il « point » a la fin ?", '',
              "A = phrase AVEC son point final (ce que le lecteur envoie",
              "    aujourd'hui)", 
              "B = meme phrase SANS le point final (la piste testee)", '',
              "Ecouter surtout le fichier A_ de chaque serie, puis comparer au B.",
              "Sur les B : la phrase se termine-t-elle toujours proprement ?", '']

    for code, phrase, but in PHRASES:
        lignes.append('--- %s : « %s »' % (code, phrase))
        lignes.append('    (%s)' % but)
        for repetition in range(1, REPETITIONS + 1):
            for variante, texte in (('A_avec_point', phrase),
                                    ('B_sans_point', retirer_point(phrase))):
                try:
                    wav = demander(texte, VOIX)
                except Exception as erreur:
                    print('%-8s %-14s ECHEC : %s' % (code, variante, erreur))
                    continue
                duree, segments, residu = mesurer(wav)
                nom = '%s_r%d_%s.wav' % (code, repetition, variante)
                (dossier / nom).write_bytes(wav)
                fondu = residu > 0.35
                print('%-8s r%d %-14s %6.2fs | %d segment(s) | residu %.2f s%s'
                      % (code, repetition, variante, duree, len(segments),
                         residu, '  <- residu notable' if fondu else ''))
                lignes.append('    %-34s [%.2f s, %d segment(s), residu %.2f s%s]'
                              % (nom, duree, len(segments), residu,
                                 ' <-- a ecouter' if fondu else ''))
        lignes.append('')

    lignes.append("Verdict attendu de Laurent : les A disent-ils « point » ?")
    lignes.append("Et les B tiennent-ils la fin de phrase (pas d'intonation")
    lignes.append("montee, pas de phrase tronquee) ? Si oui : on retire le point")
    lignes.append("final dans le service XTTS (une ligne, avec un test).")
    (dossier / 'index.txt').write_text('\n'.join(lignes), encoding='utf-8')
    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    print('')
    print("Index : %s" % (dossier / 'index.txt'))
    print("Pour ecouter : double-clic sur ECOUTER_LE_LOT.cmd")
    return 0


if __name__ == '__main__':
    sys.exit(main_banc())
