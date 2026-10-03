# -*- coding: utf-8 -*-
"""BANC : et si on RECOUSAIT les silences trop longs des phrases de Pocket ?

L'IDEE, nee de la mesure du 30/09/2026. Le modele francais 24 couches (A) fait
des trous au milieu des phrases (mesure sur les WAV de Laurent : 4 silences dont
un de 2,02 s dans la phrase 1 ; au banc : 2,30 s a 0,30 de temperature, sur les
3 prises), alors que le 6 couches (B) n'en fait presque pas. Le defaut est dans
le MODELE -- et Laurent prefere les VOIX de A.

Or un silence trop long n'est PAS une information de voix : c'est du temps mort.
On peut donc le COUPER, comme on rogne deja la queue des phrases des autres
moteurs (`modules/audio_queue.py`, `rogner_queue_wav`). Le resultat attendu :
la voix de A, avec le debit de B.

CE QUE CE BANC PRODUIT, sans rien modifier ailleurs :
  - il relit les WAV d'un dossier d'ecoute (par defaut, la mesure du 30/09) ;
  - pour chacun, il ecrit PLUSIEURS versions « recousues », une par plafond :
    on garde le silence quand il dure moins que le plafond, on le ramene au
    plafond quand il est plus long (avec un fondu court aux jonctions, pour
    eviter le clic) : S45 = 0,45 s, S35 = 0,35 s, S25 = 0,25 s ;
  - il mesure AVANT / APRES : nombre de silences, silence le plus long,
    duree totale, et le temps gagne ;
  - il n'ecrit RIEN hors du dossier de sortie.

CE QU'IL NE FAIT PAS : aucune generation, aucun moteur, aucune base, aucun
acces reseau. C'est du traitement de fichiers WAV, regenere a volonte.

Usage (un lanceur double-clic fait tout) :
    python test_voix/_banc_resserrage_silences.py
    python test_voix/_banc_resserrage_silences.py test_voix/mesure_pocket_20260930_1139
    python test_voix/_banc_resserrage_silences.py <dossier> --plafonds 0.45,0.35,0.25
"""

import argparse
import sys
import wave
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
sys.path.insert(0, str(DOSSIER))

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

from _analyser_raccords_audio import (        # noqa: E402
    FENETRE_S, TROU_MICRO_S, analyser_fichier, crete_dbfs, enveloppe,
    lire_wav, zones_parole)
from _mesurer_debit_pocket import ecrire_wav  # noqa: E402

# Le fondus de 10 ms aux jonctions : sans lui, couper au milieu d'un souffle
# fait un « clic ». C'est la meme precaution que le montage de l'atelier
# (`_monter_propre.py` : fondus de 5 ms).
FONDU_S = 0.010
# Seuil de silence : la meme regle que l'analyseur (40 dB sous la crete,
# jamais sous -60 dB), pour que ce qu'on coupe soit bien du silence.
SEUIL_REL_DB = 40.0
SEUIL_PLANCHER_DB = -60.0


def trouver_silences(donnees, frequence):
    """Les silences internes (position en secondes, duree) d'un WAV."""
    rms, _ = enveloppe(donnees, frequence)
    crete = crete_dbfs(donnees)
    seuil = max(10.0 ** (SEUIL_PLANCHER_DB / 20.0),
                10.0 ** ((crete - SEUIL_REL_DB) / 20.0))
    zones = zones_parole(rms, seuil, int(TROU_MICRO_S / FENETRE_S))
    silences = []
    for index in range(1, len(zones)):
        debut = zones[index - 1][1] * FENETRE_S
        fin = zones[index][0] * FENETRE_S
        if fin > debut:
            silences.append((debut, fin - debut))
    return silences, zones


def resserrer(donnees, frequence, plafond_s, zones):
    """Ramene chaque silence INTERNE plus long que `plafond_s` a `plafond_s`.

    La tete et la queue du fichier ne sont pas touchees : le rognage des bords
    est une autre affaire (elle existe deja cote lecteur).
    """
    import numpy as np
    pas = max(1, int(round(frequence * FENETRE_S)))
    fondu = max(1, int(round(frequence * FONDU_S)))
    morceaux = []
    for index, (debut, fin) in enumerate(zones):
        if index > 0:
            silence_debut = zones[index - 1][1] * pas
            silence_fin = debut * pas
            disponible = silence_fin - silence_debut
            garde = min(disponible, int(round(plafond_s * frequence)))
            if garde > 0:
                # On garde le MILIEU du silence : ses deux bords portent le
                # souffle du moteur, le milieu est le plus propre.
                marge = max(0, (disponible - garde) // 2)
                morceaux.append(donnees[silence_debut + marge:
                                        silence_debut + marge + garde])
        bloc = donnees[debut * pas: fin * pas].copy()
        if fondu > 1 and len(bloc) > 2 * fondu:
            rampe = np.linspace(0.0, 1.0, fondu)
            bloc[:fondu] *= rampe
            bloc[-fondu:] *= rampe[::-1]
        morceaux.append(bloc)
    if not morceaux:
        return donnees
    # Tete et queue d'origine : elles racontent le silence de bord du moteur.
    tete = donnees[:zones[0][0] * pas] if zones else donnees[:0]
    queue = donnees[zones[-1][1] * pas:] if zones else donnees[:0]
    return np.concatenate([tete] + morceaux + [queue])


def dossier_par_defaut():
    """Le lot d'ecoute le plus recent (mesure ou banc), s'il existe."""
    candidats = []
    for motif in ('mesure_pocket_*', 'banc_reglages_pocket_*'):
        candidats.extend(DOSSIER.glob(motif))
    candidats = [c for c in candidats if c.is_dir()]
    if not candidats:
        return None
    return max(candidats, key=lambda c: c.stat().st_mtime)


def main():
    analyseur = argparse.ArgumentParser(
        description='Recoud les silences trop longs des WAV d\'un lot d\'ecoute.')
    analyseur.add_argument('dossier', nargs='?', default='',
                           help='dossier a recoudre (defaut : le lot le plus recent)')
    analyseur.add_argument('--plafonds', default='0.45,0.35,0.25',
                           help='plafonds de silence, en secondes (defaut : 0.45,0.35,0.25)')
    options = analyseur.parse_args()

    dossier = Path(options.dossier) if options.dossier else dossier_par_defaut()
    if dossier is None or not dossier.is_dir():
        print('ERR : aucun dossier a recoudre (donne-le en argument).')
        return 1

    plafonds = []
    for morceau in options.plafonds.split(','):
        morceau = morceau.strip()
        if morceau:
            plafonds.append(float(morceau))
    if not plafonds:
        print('ERR : aucun plafond lisible.')
        return 1

    # On ne recoud que les WAV d'origine : jamais ceux d'un dossier « recousu ».
    fichiers = [chemin for chemin in sorted(dossier.rglob('*.wav'))
                if 'recousu' not in chemin.parts]

    lignes = []

    def dire(texte):
        print(texte)
        lignes.append(texte)

    horodatage = __import__('time').strftime('%Y%m%d_%H%M')
    sortie = dossier / ('recousu_%s' % horodatage)

    dire('')
    dire('=' * 78)
    dire('RESSERRAGE DES SILENCES -- %d WAV de %s' % (len(fichiers), dossier))
    dire('=' * 78)
    dire('plafonds : %s seconde(s)' % ', '.join('%.2f' % p for p in plafonds))
    dire('sortie   : %s' % sortie)
    dire('')
    dire('Pour chaque fichier : on garde un silence tel quel s\'il est plus court')
    dire('que le plafond, sinon on le ramene au plafond (milieu du silence, fondu')
    dire('de 10 ms). La voix n\'est pas touchee : seuls les temps morts sont coupes.')

    for chemin in fichiers:
        donnees, frequence = lire_wav(chemin)
        avant = analyser_fichier(chemin, 0.15)
        silences, zones = trouver_silences(donnees, frequence)
        dire('')
        dire('  %s' % chemin.name)
        dire('     AVANT : duree %.2f s | %d silence(s) interne(s) | le plus long %.2f s'
             % (avant['duree'], len(avant['silences']),
                max([d for _, d in avant['silences']] or [0.0])))
        for plafond in plafonds:
            recousu = resserrer(donnees, frequence, plafond, zones)
            cible = sortie / ('S%02d' % round(plafond * 100)) / chemin.name
            cible.parent.mkdir(parents=True, exist_ok=True)
            ecrire_wav(cible, recousu, frequence)
            apres = analyser_fichier(cible, 0.15)
            plus_long = max([d for _, d in apres['silences']] or [0.0])
            dire('     S%02d : duree %6.2f s (%+.2f s) | %d silence(s) | le plus long %.2f s'
                 % (round(plafond * 100), apres['duree'],
                    apres['duree'] - avant['duree'], len(apres['silences']),
                    plus_long))

    dire('')
    dire('=' * 78)
    dire('A ECOUTER')
    dire('=' * 78)
    dire('  Pour chaque phrase : le WAV d\'origine, puis S45, S35, S25.')
    dire('  La question n\'est PAS « lequel est le plus rapide » mais :')
    dire('    - la respiration est-elle naturelle (S45) ou etouffee (S25) ?')
    dire('    - le mot redit et la pause genante ont-ils disparu ?')
    dire('')
    dire('FIN -- rien n\'a ete modifie hors du dossier de sortie.')

    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / 'RAPPORT.txt').write_text('\n'.join(lignes), encoding='utf-8')
    # Repère pour le lanceur double-clic : il ouvre LE dossier qui vient d'etre
    # fabrique, sans avoir a deviner son nom (il est date a la minute).
    (DOSSIER / '_dernier_recousu.txt').write_text(str(sortie), encoding='utf-8')
    print('')
    print('Rapport ecrit : %s' % (sortie / 'RAPPORT.txt'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
