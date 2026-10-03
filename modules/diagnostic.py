# -*- coding: utf-8 -*-
"""LE DIAGNOSTIC D'UNE PHRASE -- mode special du lecteur (03/10/2026).

Demande de Laurent, mot pour mot : « Est-ce qu'on pourrait faire un outil qui
fait que tu lances le lecteur depuis ici, dans un terminal ? Il ne faudrait pas
qu'il mette des phrases en cache en avance et dès que j'entends une anomalie, je
stoppe et je te dis de quelle phrase il s'agit. Si on fait comme ça, est-ce que
tu peux savoir ce qu'il se passe dans le traitement du texte ? »

CE MODE S'ACTIVE AVEC `NIMM_DIAGNOSTIC=1` (variable d'environnement). Quand il
est la, DEUX CHOSES CHANGENT, et rien d'autre :
  1. LE CACHE EST IGNORE : aucune phrase n'est relue du disque et aucune n'y est
     ecrite. Chaque phrase est donc REELLEMENT fabriquee au moment ou Laurent
     l'ecoute -- ce qu'il entend est ce que le moteur vient de produire, pas un
     fichier range la veille ;
  2. CHAQUE PHRASE LAISSE UNE TRACE ECRITE : le texte avant et apres le
     nettoyage, la voix, la vitesse, la hauteur, et l'audio a CHAQUE etape du
     traitement, avec son niveau mesure -- c'est ce qui permet de dire A QUEL
     MOMENT un souffle apparait.

LES ETAPES TRACEES (l'ordre exact de `modules/tts.py`, fonction `synthesize_qwen`) :
    01 le moteur brut        ce que qwentts.cpp rend, sans retouche
    02 le rognage de queue   `modules/audio_queue.py`
    03 la VITESSE            ffmpeg atempo (`modules/audio_rate.py`)
    04 la HAUTEUR            pedalboard / Rubber Band (aucun effet si +0 Hz)
    05 la NORMALISATION      `modules/audio_gain.py` -- LA ou le gain peut
                             atteindre x4 (+12 dB) sur une phrase faible, donc
                             la ou un bruit de fond pourrait devenir audible
    06 le fondu d'entree     `modules/audio_gain.py`, 100 ms

CE QU'ON ECRIT, ET OU :
    test_voix/sortie_diagnostic_phrase/journal.txt     une ligne par phrase
    test_voix/sortie_diagnostic_phrase/phrase_0001_<voix>/rapport.txt
    .../01_brut_moteur.wav ... 06_fondu.wav            les 6 etapes
    .../texte_avant.txt, texte_apres.txt               les deux textes

RIEN N'EST MODIFIE AILLEURS : la base, les voix, les catalogues et le cache du
lecteur ne sont pas touches. Ce mode ne fait qu'AJOUTER des fichiers a part.
"""
import math
import os
import re
import time
import wave
from array import array
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / 'test_voix' / 'sortie_diagnostic_phrase'
JOURNAL = SORTIE / 'journal.txt'

SEUIL_SON = 0.01          # -40 dBFS : ce que l'atelier appelle « du son »

_compteur = [0]


def actif():
    """Le mode diagnostic est-il demande ?"""
    return os.environ.get('NIMM_DIAGNOSTIC', '').strip() == '1'


def _lire_wav(octets):
    """(echantillons entiers, frequence) d'un WAV en memoire."""
    import io

    with wave.open(io.BytesIO(octets), 'rb') as fichier:
        canaux = fichier.getnchannels()
        largeur = fichier.getsampwidth()
        frequence = fichier.getframerate()
        brut = fichier.readframes(fichier.getnframes())
    donnees = array('h')
    donnees.frombytes(brut)
    if canaux > 1:
        donnees = donnees[::canaux]
    return donnees, frequence


def mesurer(octets):
    """(duree, pic, niveau moyen, plancher de bruit) en secondes et dBFS.

    Le PLANCHER est le niveau des moments les plus calmes : c'est LA que s'entend
    un souffle. Un plancher qui monte d'une etape a l'autre = le bruit a ete
    amplifie avec la parole.
    """
    if not octets:
        return None
    try:
        donnees, frequence = _lire_wav(octets)
    except Exception:
        return None
    if not donnees:
        return None
    duree = len(donnees) / float(frequence)
    pic = max(abs(v) for v in donnees) or 1e-9
    energie = sum(v * v for v in donnees) / float(len(donnees))
    niveau = (energie ** 0.5) / 32768.0
    bloc = max(1, int(frequence * 0.05))
    morceaux = []
    for debut in range(0, len(donnees) - bloc, bloc):
        tranche = donnees[debut:debut + bloc]
        carre = sum(v * v for v in tranche) / float(len(tranche))
        if carre > 0:
            morceaux.append(carre ** 0.5)
    morceaux.sort()
    bas = morceaux[:max(1, len(morceaux) // 5)] if morceaux else [1e-9]
    plancher = (sum(bas) / len(bas)) / 32768.0 or 1e-9
    return {
        'duree': duree,
        'pic_db': 20 * math.log10(pic / 32768.0),
        'niveau_db': 20 * math.log10(niveau or 1e-9),
        'plancher_db': 20 * math.log10(plancher or 1e-9),
    }


def _nom_sur(nom):
    """Un nom de dossier sans caractere interdit par Windows."""
    propre = re.sub(r'[^A-Za-z0-9_.-]+', '_', str(nom))
    return propre[:60] or 'voix'


def enregistrer(texte_avant, texte_apres, voice, rate, pitch, etapes,
                secondes_moteur=None, secondes_totales=None):
    """Ecrit la trace d'UNE phrase (rapport + les 6 etapes en WAV).

    `etapes` : [(nom, octets WAV)] dans l'ordre du traitement.
    Rend le nom du dossier cree.
    """
    _compteur[0] += 1
    numero = _compteur[0]
    SORTIE.mkdir(parents=True, exist_ok=True)
    # L'HEURE EST DANS LE NOM (corrige le 03/10/2026) : le compteur repart de
    # zero a chaque redemarrage du lecteur, donc sans l'horodatage les traces
    # d'une nouvelle session ECRASERAIENT celles de la precedente -- et ces
    # traces sont le travail d'ecoute de Laurent. Avec l'heure, on ne perd rien
    # et les dossiers restent ranges dans l'ordre.
    dossier = SORTIE / ('phrase_%s_%04d_%s'
                        % (time.strftime('%Y%m%d_%H%M%S'), numero,
                           _nom_sur(voice)))
    dossier.mkdir(exist_ok=True)

    lignes = [
        'PHRASE %04d -- %s' % (numero, time.strftime('%d/%m/%Y %H:%M:%S')),
        '=' * 78,
        '',
        'VOIX    : %s' % voice,
        'VITESSE : %s' % rate,
        'HAUTEUR : %s' % pitch,
        ('CALCUL  : %.1f s (moteur) / %.1f s (total, traitement compris)'
         % (secondes_moteur or 0.0, secondes_totales or 0.0)),
        '',
        '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -',
        'LES ETAPES DU TRAITEMENT',
        '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -',
        'etape                 duree      pic    niveau  plancher   (dBFS)',
    ]
    alerte = []
    precedente = None
    for nom, octets in etapes:
        mesures = mesurer(octets)
        if mesures is None:
            lignes.append('%-20s  (audio illisible)' % nom)
            continue
        (dossier / (nom + '.wav')).write_bytes(octets)
        lignes.append('%-20s %6.2f s %7.1f %8.1f %9.1f'
                      % (nom, mesures['duree'], mesures['pic_db'],
                         mesures['niveau_db'], mesures['plancher_db']))
        if precedente is not None:
            hausse = mesures['plancher_db'] - precedente
            if hausse >= 6.0:
                alerte.append('%s : le plancher de bruit monte de %+.1f dB'
                              % (nom, hausse))
        precedente = mesures['plancher_db']

    lignes += ['', '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -']
    if alerte:
        lignes.append("ATTENTION -- ce qui suit merite d'etre ecoute :")
        lignes += ['  ' + texte for texte in alerte]
    else:
        lignes.append('Aucune etape ne fait bondir le plancher de bruit '
                      '(seuil : +6 dB).')
    lignes += [
        '',
        '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -',
        'LE TEXTE',
        '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -',
        '',
        'AVANT (tel qu il sort du livre) :',
        '  %s' % texte_avant,
        '',
        'APRES le nettoyage du lecteur (ce que le moteur recoit vraiment) :',
        '  %s' % texte_apres,
    ]
    (dossier / 'rapport.txt').write_text('\n'.join(lignes) + '\n',
                                         encoding='utf-8')
    (dossier / 'texte_avant.txt').write_text(texte_avant or '', encoding='utf-8')
    (dossier / 'texte_apres.txt').write_text(texte_apres or '', encoding='utf-8')

    fin = [m for _n, m in [(n, mesurer(o)) for n, o in etapes] if m]
    plancher_final = fin[-1]['plancher_db'] if fin else 0.0
    ligne = ('%04d | %s | %-26s | plancher final %6.1f dBFS | %s%s'
             % (numero, time.strftime('%H:%M:%S'), str(voice)[:26],
                plancher_final, (texte_apres or '')[:52],
                '   << ' + ' / '.join(alerte) if alerte else ''))
    with open(JOURNAL, 'a', encoding='utf-8') as flux:
        flux.write(ligne + '\n')
    print('[DIAGNOSTIC] %s' % ligne, flush=True)
    return dossier.name
