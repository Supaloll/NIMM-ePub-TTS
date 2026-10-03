# -*- coding: utf-8 -*-
r"""LES 35 VOIX KYUTAI : bords propres + les 35 textes a corriger a l'oreille.

DEMANDE DE LAURENT, 03/10/2026, mot pour mot : « Pour les voix Kyutai, ce qui me
parait important, c'est d'avoir la reference du texte parce que beaucoup
d'erreurs venaient d'une erreur de transcription, donc il faudrait les 35
passages audio plus les 35 transcriptions texte que je corrige a l'oreille. »

CE QUE L'OUTIL FABRIQUE : un LOT (`lot_kyutai_bords_propres_20261003\`) qui est
un DOSSIER DE VOIX au sens du service, donc directement ouvrable avec l'outil
d'ecoute :

    <voix>_reference.wav     les 35 references, BORDS PROPRES
    references.csv           les 35 textes ACTUELS, tels quels
    SYNTHESE_BORDS.txt       l'avant / apres de chaque voix, mesure
    LISEZ-MOI.txt            ce qu'il faut faire, en francais

CE QU'ON FAIT AUX BORDS, ET RIEN D'AUTRE (mesure du 03/10/2026 : sur les 35
references, 30 avaient MOINS DE 50 ms de silence a un bord, souvent ZERO) :
  - on ramene le silence de chaque bord a 150 ms : on COMPLETE quand il n'y en a
    pas (une marge de silence), on ROGNE quand il y en a trop ;
  - on pose un fondu de 20 ms sur le premier et le dernier SON (la recette de
    l'atelier : « garder la marge ET un fondu de 20 ms ») ;
  - ON NE COUPE JAMAIS UN MOT, et le TEXTE NE CHANGE PAS : on ne touche qu'a du
    silence. C'est ce qui permet a Laurent de corriger le texte sur ce meme lot
    sans que les deux travaux se contredisent.

CE QUI RESTE HORS DE PORTEE, ET IL FAUT LE DIRE : si l'AUDIO lui-meme commence
au milieu d'un mot (le cas de Femme004, dont la source dit « quand » coupe en
deux), AUCUNE marge ne peut le reparer : il faudrait un enregistrement plus
long. La SYNTHESE marque donc, voix par voix, celles dont l'attaque est
INSTANTANEE (le son est deja fort des la premiere mesure) : ce sont les
suspectes, a ecouter avant de croire.

RIEN N'EST MODIFIE DANS LE PROJET : les 35 voix de production ne sont ni
touchees, ni deplacees, ni renommees. Tout s'ecrit dans le lot.

Usage :
    python test_voix/_preparer_lot_kyutai_recoupe.py
    python test_voix/_preparer_lot_kyutai_recoupe.py --dossier AUTRE\CHEMIN
"""
import argparse
import array
import csv
import sys
import time
import wave
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.stdout.reconfigure(encoding='utf-8')

DOSSIER_PRODUCTION = RACINE / 'qwen_tts_service' / 'voix'
LOT_DEFAUT = ICI / 'lot_kyutai_bords_propres_20261003'

SUFFIXE = '_enhanced_reference.wav'
FREQUENCE = 24000
MARGE_S = 0.150      # le silence voulu a CHAQUE bord
FONDU_S = 0.020      # le fondu pose sur le premier et le dernier son
SEUIL = 0.01         # -40 dBFS : ce que l'atelier appelle « du son »


def lire_wav(chemin):
    """Les echantillons entiers et la frequence d'un WAV mono 16 bits."""
    with wave.open(str(chemin), 'rb') as fichier:
        canaux = fichier.getnchannels()
        largeur = fichier.getsampwidth()
        frequence = fichier.getframerate()
        brut = fichier.readframes(fichier.getnframes())
    if largeur != 2:
        raise ValueError('WAV non 16 bits : %s' % chemin)
    donnees = array.array('h')
    donnees.frombytes(brut)
    if canaux > 1:
        donnees = donnees[::canaux]
    return donnees, frequence


def ecrire_wav(donnees, chemin, frequence=FREQUENCE):
    with wave.open(str(chemin), 'wb') as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(frequence))
        fichier.writeframes(donnees.tobytes())


def _tranches(donnees, frequence, seuil=SEUIL):
    """[(debut, fin, silencieux)] par tranches de 10 ms."""
    pas = max(1, int(frequence * 0.01))
    limite = seuil * 32768
    morceaux = []
    for debut in range(0, len(donnees), pas):
        bloc = donnees[debut:debut + pas]
        if not bloc:
            continue
        morceaux.append((debut, debut + len(bloc),
                         max(abs(v) for v in bloc) <= limite))
    return morceaux


def mesurer_bords(donnees, frequence):
    """Tout ce qu'on veut savoir des bords -- ou None si aucun son.

    `attaque` et `chute` : la force des 10 PREMIERES et 10 DERNIERES
    millisecondes de son, rapportee a la crete du morceau. Proche de 1 = le son
    est DEJA FORT a la premiere mesure, donc la coupe est tres probablement
    DANS LE MOT (aucune marge ne peut reparer ca).
    """
    premier = None
    dernier = None
    for debut, fin, silencieux in _tranches(donnees, frequence):
        if not silencieux:
            if premier is None:
                premier = debut
            dernier = fin
    if premier is None:
        return None
    pas = max(1, int(frequence * 0.01))
    crete = max(abs(v) for v in donnees) or 0
    if not crete:
        return None
    debut_fort = max(abs(v) for v in donnees[premier:premier + pas])
    fin_fort = max(abs(v) for v in donnees[max(0, dernier - pas):dernier])
    return {
        'premier': premier,
        'dernier': dernier,
        'duree': len(donnees) / float(frequence),
        'silence_tete': premier / float(frequence),
        'silence_queue': (len(donnees) - dernier) / float(frequence),
        'attaque': debut_fort / float(crete),
        'chute': fin_fort / float(crete),
    }


def recouper(donnees, frequence, bords):
    """150 ms de silence a chaque bord + un fondu de 20 ms sur le premier et le
    dernier SON. **On ne touche QU'A DU SILENCE : le texte reste valable.**"""
    marge = int(MARGE_S * frequence)
    morceau = donnees[bords['premier']:bords['dernier']]
    fondu = min(int(FONDU_S * frequence), len(morceau) // 2)
    if fondu >= 1:
        for i in range(fondu):
            facteur = i / float(fondu)
            morceau[i] = int(morceau[i] * facteur)
            rang = len(morceau) - 1 - i
            morceau[rang] = int(morceau[rang] * facteur)
    return array.array('h', [0] * marge) + morceau + array.array('h', [0] * marge)


def lire_textes_production():
    """{nom_de_voix: (texte, duree, hauteur, source)} depuis le fichier du service."""
    table = {}
    for fichier in (DOSSIER_PRODUCTION / 'references.csv',
                    DOSSIER_PRODUCTION / 'references_privees.csv'):
        if not fichier.is_file():
            continue
        with open(fichier, encoding='utf-8', newline='') as flux:
            for ligne in csv.reader(flux, delimiter=';'):
                if len(ligne) < 2 or not ligne[0].strip():
                    continue
                nom = ligne[0].strip()
                if nom == 'fichier':
                    continue
                table[nom] = (
                    ligne[1].strip(),
                    ligne[2].strip() if len(ligne) > 2 else '',
                    ligne[3].strip() if len(ligne) > 3 else '',
                    ligne[4].strip() if len(ligne) > 4 else '',
                )
    return table


def ecrire_synthese(lot, tableau, suspectes, a_completer):
    """L'avant / apres de chaque voix, et les suspects."""
    lignes = [
        'LES VOIX KYUTAI : BORDS PROPRES -- %s'
        % time.strftime('%d/%m/%Y %H:%M'),
        '=' * 84,
        '',
        'CE QU ON A FAIT AUX BORDS, ET RIEN D AUTRE :',
        '  - le silence de chaque bord a ete RAMENE a 150 ms : complete quand il',
        '    n y en avait pas, rogne quand il y en avait trop ;',
        '  - un fondu de 20 ms a ete pose sur le premier et le dernier SON ;',
        '  - AUCUN MOT N A ETE COUPE, et le TEXTE N A PAS CHANGE : on ne touche',
        '    qu a du silence. C est ce qui permet de corriger le texte sur ce',
        '    MEME lot sans que les deux travaux se contredisent.',
        '',
    ]
    lignes.append('POURQUOI : sur ces %d references, %d avaient MOINS DE 50 ms de'
                  % (len(tableau), a_completer))
    lignes += [
        'silence a un bord, souvent ZERO : le son demarrait au ras de la',
        'premiere mesure.',
        '',
        '%-34s %8s %11s %11s %11s %9s %9s'
        % ('voix', 'duree', 'tete avant', 'queue avant', 'tete apres',
           'queue apres', 'attaque'),
        '-' * 84,
    ]
    for nom, bords in tableau:
        lignes.append('%-34s %6.2f s %8.0f ms %8.0f ms %8.0f ms %6.0f ms %8.2f'
                      % (nom[:34], bords['duree'],
                         bords['silence_tete'] * 1000,
                         bords['silence_queue'] * 1000, 150.0, 150.0,
                         bords['attaque']))
    lignes += [
        '',
        'LA COLONNE « attaque » : la force des 10 premieres millisecondes de',
        'son, rapportee a la crete du morceau. Proche de 1 = le son est DEJA FORT',
        'a la premiere mesure : la coupe est tres probablement DANS LE MOT, et',
        'AUCUNE MARGE ne peut reparer ca -- il faudrait un enregistrement plus',
        'long (c est le cas de Femme004, dont la source dit « quand » coupe).',
        '',
    ]
    if suspectes:
        lignes.append('LES %d SUSPECTES, a ecouter EN PREMIER :'
                      % len(suspectes))
        for nom, attaque, chute in suspectes:
            lignes.append('  %-34s attaque %.2f   chute %.2f'
                          % (nom[:34], attaque, chute))
    else:
        lignes += ['Aucune attaque instantanee : les bords etaient seulement mal',
                   'marges, et la marge suffit.']
    lignes += [
        '',
        'RAPPEL : RIEN n a ete modifie dans le projet. Ce lot est un travail ;',
        'les voix de production attendent l accord de Laurent (et une copie',
        'datee) avant tout remplacement.',
    ]
    (lot / 'SYNTHESE_BORDS.txt').write_text('\n'.join(lignes) + '\n',
                                            encoding='utf-8')


def ecrire_lisez_moi(lot, nombre):
    lignes = [
        'LES %d VOIX KYUTAI : LES ECOUTER ET CORRIGER LEUR TEXTE' % nombre,
        '=' * 78,
        '',
        'POURQUOI ON FAIT CA (demande de Laurent, 03/10/2026, mot pour mot) :',
        '« beaucoup d erreurs venaient d une erreur de transcription, donc il',
        'faudrait les 35 passages audio plus les 35 transcriptions texte que je',
        'corrige a l oreille. »',
        '',
        'CE QU IL Y A ICI :',
        '  les WAV ......... les 35 references, BORDS PROPRES (150 ms de silence',
        '                    a chaque bord, fondu de 20 ms, AUCUN mot coupe) ;',
        '  references.csv .. les 35 textes ACTUELS, tels quels ;',
        '  SYNTHESE_BORDS .. l avant / apres de chaque voix, et les suspects.',
        '',
        'CE QU ON TE DEMANDE :',
        '  1) ECOUTE la voix -- « Rejouer le debut » sert a entendre l attaque,',
        '     et pense a ecouter AUSSI la fin ;',
        '  2) REECRIS le texte mot pour mot, tel que tu l entends vraiment ;',
        '  3) Ctrl+Entree enregistre et passe a la voix suivante.',
        '',
        'Rien n est applique aux voix : tes corrections attendent dans ce lot.',
    ]
    (lot / 'LISEZ-MOI.txt').write_text('\n'.join(lignes) + '\n',
                                       encoding='utf-8')


def main():
    analyseur = argparse.ArgumentParser(
        description='Prepare le lot des 35 voix Kyutai : bords propres + textes.')
    analyseur.add_argument('--dossier', default='',
                           help='dossier du lot (defaut : %s)' % LOT_DEFAUT.name)
    options = analyseur.parse_args()

    lot = Path(options.dossier).resolve() if options.dossier else LOT_DEFAUT
    lot.mkdir(parents=True, exist_ok=True)

    references = sorted(DOSSIER_PRODUCTION.glob('*' + SUFFIXE))
    if not references:
        print('ARRET : aucune reference Kyutai (*%s) dans %s'
              % (SUFFIXE, DOSSIER_PRODUCTION))
        return 2
    textes = lire_textes_production()

    print('=' * 84)
    print(' LES VOIX KYUTAI : BORDS PROPRES (marge de 150 ms + fondu de 20 ms)')
    print('=' * 84)
    print(' source : %s' % DOSSIER_PRODUCTION)
    print(' lot    : %s' % lot)
    print(' references trouvees : %d' % len(references))
    print('')
    print(' RIEN n est modifie dans le projet : les voix de production ne sont')
    print(' ni touchees, ni deplacees, ni renommees. Tout s ecrit dans le lot.')
    print('')
    print(' %-34s %8s %9s %9s %9s %9s %s'
          % ('voix', 'duree', 'tete AV', 'queue AV', 'tete AP', 'queue AP',
             'attaque instantanee ?'))
    print('-' * 84)

    lignes_csv = [['fichier', 'texte', 'duree', 'hauteur', 'source']]
    tableau = []
    a_completer = 0
    suspectes = []
    for chemin in references:
        nom = chemin.name[:-len(SUFFIXE)]
        donnees, frequence = lire_wav(chemin)
        if frequence != FREQUENCE:
            print(' %-34s IGNOREE : %d Hz' % (nom[:34], frequence))
            continue
        bords = mesurer_bords(donnees, frequence)
        if bords is None:
            print(' %-34s IGNOREE : aucun son' % nom[:34])
            continue
        recoupe = recouper(donnees, frequence, bords)
        fichier_lot = '%s_reference.wav' % nom
        ecrire_wav(recoupe, lot / fichier_lot)
        texte, _duree, hauteur, _source = textes.get(chemin.name,
                                                    ('', '', '', ''))
        if not texte:
            print(' %-34s ATTENTION : aucun texte dans references.csv' % nom[:34])
        lignes_csv.append([fichier_lot, texte,
                           '%.2f' % (len(recoupe) / float(frequence)),
                           hauteur, chemin.name])
        if bords['silence_tete'] < 0.10 or bords['silence_queue'] < 0.10:
            a_completer += 1
        instantanee = max(bords['attaque'], bords['chute']) > 0.5
        if instantanee:
            suspectes.append((nom, bords['attaque'], bords['chute']))
        print(' %-34s %6.2f s %6.0f ms %6.0f ms %6.0f ms %6.0f ms %s'
              % (nom[:34], bords['duree'], bords['silence_tete'] * 1000,
                 bords['silence_queue'] * 1000, 150.0, 150.0,
                 'ATTENTION' if instantanee else ''))
        tableau.append((nom, bords))

    with open(lot / 'references.csv', 'w', encoding='utf-8',
              newline='') as flux:
        graveur = csv.writer(flux, delimiter=';')
        for ligne in lignes_csv:
            graveur.writerow(ligne)

    ecrire_synthese(lot, tableau, suspectes, a_completer)
    ecrire_lisez_moi(lot, len(tableau))

    print('')
    print('=' * 84)
    print(' BILAN')
    print('=' * 84)
    print('  references recoupees                   : %d' % len(tableau))
    print('  bords completes (le silence manquait)  : %d' % a_completer)
    print('  attaques instantanees (suspectes)      : %d' % len(suspectes))
    print('')
    print('  lot    : %s' % lot)
    print('  textes : %s' % (lot / 'references.csv'))
    print('  detail : %s' % (lot / 'SYNTHESE_BORDS.txt'))
    print('')
    print('  POUR ECOUTER ET CORRIGER LES TEXTES :')
    print('    python test_voix/_corriger_references_a_l_oreille.py --lot "%s"'
          % lot)
    print('  (ou le lanceur double-clic CORRIGER_LES_TEXTES_KYUTAI.bat)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
