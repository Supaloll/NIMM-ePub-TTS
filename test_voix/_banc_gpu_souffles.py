# -*- coding: utf-8 -*-
r"""LES SOUFFLES SUR LA CARTE : comparer les moteurs, a l'oreille de Laurent.

D'OU VIENT CE BANC (03/10/2026). Laurent, mot pour mot : « parfois je me
retrouve avec des parasites dans la voix comme un bruit de fond, un souffle,
juste sur une phrase […] C'est bizarre parce que quand c'etait sur CPU, c'etait
tres lent, mais c'etait tres propre. »

CE QU'ON SAIT DEJA :
  - le moteur en service est **Q4_K_M sur la CARTE**, temperature **0,9**, et
    `clamp_fp16` **desactive** (c'est le defaut du paquet : `_ouvrir_moteur()` ne
    le passe pas) ;
  - sur la CARTE, le calcul se fait en precision reduite ; sur le PROCESSEUR, il
    se fait en pleine precision. C'est la difference la plus plausible entre
    « propre » et « souffle » ;
  - `clamp_fp16` est un vrai reglage du moteur (`QwenTTS(..., clamp_fp16=True)`) :
    il borne les valeurs qui debordent du format court. C'est le levier direct.

CE QUE LE BANC COMPARE (meme voix, memes phrases, memes tirages -- seul le moteur
change), et il MESURE aussi une piste objective : la part d'energie dans les
aigus (> 6 kHz), la ou un souffle se voit :
    A = carte, Q4_K_M, clamp OFF      (ce qu'on entend aujourd'hui)
    B = carte, Q4_K_M, clamp ON       (le levier direct)
    C = processeur, Q4_K_M            (le « propre » de Laurent)
    D = carte, Q8_0, clamp OFF        (des poids plus fins, meme carte)

SORTIE : un dossier avec, pour chaque moteur, UN passage continu (les 3 phrases,
2 tirages, recolles avec une pause de 0,30 s) + un WAV par phrase. Les fichiers
portent des NOMS AU HASARD et la CLE reste HORS du dossier : Laurent note chaque
passage sans savoir ce qu'il ecoute.

GARDE-FOU : le banc REFUSE de partir si le service du moteur repond sur le port
8086 -- les deux se partageraient la carte, et un repli silencieux sur le
processeur fausserait tout le test.

RIEN N'EST MODIFIE DANS LE PROJET : ni la base, ni les voix, ni le service, ni
les catalogues. Tout s'ecrit dans le dossier de sortie.

A LANCER AVEC LE PYTHON DU MOTEUR (le lanceur double-clic s'en occupe) :
    qwentts_service\.venv\Scripts\python.exe test_voix\_banc_gpu_souffles.py
"""
import argparse
import array
import csv
import random
import string
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(ICI))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

import _mesurer_debit_qwentts as mesure  # noqa: E402

DOSSIER_VOIX = RACINE / 'qwen_tts_service' / 'voix'
MODELS = RACINE / 'qwentts_service' / 'models'
LOT = ICI / 'sortie_banc_souffles_gpu'
PASSAGES = LOT / 'A_ECOUTER'
PAR_PHRASE = LOT / 'par_phrase'
CLE = LOT / 'CLE_BANC_SOUFFLES.csv'
JOURNAL = LOT / 'journal.txt'
SYNTHESE = LOT / 'SYNTHESE_SOUFFLES.txt'

VOIX = '1770_1028_000036-0002'      # le narrateur de 22/11/63 (memes phrases)
TIRAGES = 2
TEMPERATURE = 0.9
PLAFOND_S = 120.0
PAUSE_S = 0.30
TEXTE_REFERENCE = None              # rempli au demarrage, depuis references.csv

# (etiquette, ce que c'est, appareil, variante, clamp_fp16)
MOTEURS = [
    ('A', 'carte, Q4_K_M, clamp OFF', 'gpu', 'Q4_K_M', False),
    ('B', 'carte, Q4_K_M, clamp ON', 'gpu', 'Q4_K_M', True),
    ('C', 'processeur, Q4_K_M', 'cpu', 'Q4_K_M', False),
    ('D', 'carte, Q8_0, clamp OFF', 'gpu', 'Q8_0', False),
]
COEURS, FILS_CODEC, TRANCHES = 6, 4, 2
SERVICE = 'http://127.0.0.1:8086'


def journaliser(texte=''):
    print(texte, flush=True)
    with open(JOURNAL, 'a', encoding='utf-8') as fichier:
        fichier.write(texte + '\n')


def le_service_repond():
    try:
        with urllib.request.urlopen(SERVICE + '/sante', timeout=3) as reponse:
            return reponse.status == 200
    except Exception:
        return False


def ecrire_flottants(sons, taux, chemin):
    import numpy as np

    entier = np.clip(np.asarray(sons, dtype=np.float32), -1.0, 1.0)
    entier = (entier * 32767.0).astype('<i2')
    with wave.open(str(chemin), 'wb') as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(taux))
        fichier.writeframes(entier.tobytes())


def lire_wav(chemin):
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


def ecrire_wav(donnees, chemin, frequence):
    with wave.open(str(chemin), 'wb') as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(frequence))
        fichier.writeframes(donnees.tobytes())


def generer(moteur, texte, spk, codes, texte_reference):
    """Une phrase, avec la TEMPERATURE du banc (le service passe la meme)."""
    import threading

    import numpy as np

    annulation = threading.Event()
    minuteur = threading.Timer(PLAFOND_S, annulation.set)
    minuteur.start()
    debut = time.perf_counter()
    morceaux = []
    taux = 24000
    try:
        for bloc, taux in moteur.stream(
                text=texte, lang='french', ref_spk_emb=spk, ref_codes=codes,
                ref_text=texte_reference, temperature=TEMPERATURE,
                cancel_event=annulation):
            morceaux.append(bloc)
    finally:
        minuteur.cancel()
    calcul = time.perf_counter() - debut
    sons = (np.concatenate(morceaux) if morceaux
            else np.zeros(0, dtype=np.float32))
    return sons, taux, calcul, annulation.is_set()


def part_des_aigus(donnees, frequence):
    """La MONOTEE des aigus : de l'energie des differences entre echantillons
    voisins, rapportee a l'energie totale.

    C'est un indicateur simple, et il est honnete : un SOUFFLE ajoute du bruit
    large bande, donc du contenu a haute frequence, et ce chiffre monte. Il ne
    remplace pas l'oreille -- il la guide.
    """
    import numpy as np

    signal = np.asarray(donnees, dtype=np.float64)
    if signal.size < 2 or float(np.mean(signal ** 2)) <= 0:
        return 0.0
    return float(np.mean(np.diff(signal) ** 2) / np.mean(signal ** 2))


def nom_au_hasard(utilises):
    alphabet = string.ascii_lowercase + string.digits
    while True:
        nom = ''.join(random.choice(alphabet) for _ in range(16))
        if nom not in utilises:
            utilises.add(nom)
            return nom


def ecrire_lisez_moi(passages):
    lignes = [
        'LES SOUFFLES : %d passages a ecouter' % len(passages),
        '=' * 78,
        '',
        'QUESTION : parfois, un passage porte un SOUFFLE, un bruit de fond, sur',
        'une seule phrase. On cherche D OU CA VIENT.',
        '',
        'Ici, la MEME voix lit les MEMES 3 phrases, 2 fois chacune, mais avec un',
        'MOTEUR different (carte ou processeur, poids plus ou moins fins, reglage',
        'de precision). Rien d autre ne change. Les fichiers portent des noms au',
        'hasard : on ne sait pas lequel est lequel.',
        '',
        'CE QU ON TE DEMANDE, POUR CHAQUE PASSAGE :',
        '  - entends-tu un SOUFFLE ? oui / non',
        '  - si oui : SUR QUELLE PHRASE (1, 2 ou 3), et a peu pres ou ?',
        '  - et au final : lequel sonne le PLUS PROPRE ?',
        '',
        'PASSAGE (nom au hasard)     | souffle ? | ou ? (phrase, moment)',
        '-' * 78,
    ]
    for _e, _l, _c, nom in passages:
        lignes.append('%-27s | .......... | ..........................' % nom)
    lignes += [
        '-' * 78,
        '',
        'LA CLE est HORS de ce dossier : donne-moi tes notes, je croiserai.',
        '',
        'A SAVOIR : les phrases sont des phrases REELLES de 22/11/63 -- le meme',
        'livre que la voix -- donc ce que tu entends ressemble a ta lecture.',
    ]
    (PASSAGES / 'LISEZ-MOI.txt').write_text('\n'.join(lignes) + '\n',
                                            encoding='utf-8')


def ecrire_synthese(passages, lignes, aigus_moyens):
    texte = [
        'LES SOUFFLES SUR LA CARTE -- %s' % time.strftime('%d/%m/%Y %H:%M'),
        '=' * 84,
        '',
        'CE QUI A ETE COMPARE (meme voix, memes phrases, memes tirages) :',
    ]
    for etiquette, libelle, _chemin, nom in passages:
        texte.append('  %s : %-30s -> %s' % (etiquette, libelle, nom))
    texte += [
        '',
        'LES AIGUS, MESURES (energie des differences entre echantillons voisins,',
        'rapportee a l energie totale : un SOUFFLE ajoute du bruit large bande,',
        'donc fait monter ce chiffre) :',
    ]
    for etiquette in sorted(aigus_moyens):
        texte.append('  %s : %.4f' % (etiquette, aigus_moyens[etiquette]))
    texte += [
        '',
        'La valeur la plus BASSE est la plus propre sur ce critere. C est une',
        'mesure simple, donnee pour GUIDER l oreille -- pas pour la remplacer.',
        '',
        'LE DETAIL PAR PHRASE (durees, aigus, abandons) est dans la cle :',
        '  %s' % CLE.name,
        '',
        'RAPPEL : rien n a ete modifie dans le projet (ni base, ni voix, ni',
        'service). Le moteur en service n a meme pas ete touche.',
    ]
    SYNTHESE.write_text('\n'.join(texte) + '\n', encoding='utf-8')


def ouvrir_moteur(appareil, variante, clamp):
    """Le moteur, ouvert comme le service le fait (memes reglages)."""
    talker = MODELS / ('qwen-talker-0.6b-base-%s.gguf' % variante)
    codec = MODELS / ('qwen-tokenizer-12hz-%s.gguf' % variante)
    for chemin in (talker, codec):
        if not chemin.is_file():
            raise FileNotFoundError('GGUF manquant : %s' % chemin)
    if appareil == 'gpu':
        from qwentts_cpp import QwenTTS
        return (QwenTTS(str(talker), str(codec), clamp_fp16=clamp),
                'carte graphique')
    from qwentts_cpp_cpu import QwenTTS
    return (QwenTTS(str(talker), str(codec), cpu_threads=COEURS,
                    cpu_codec_threads=FILS_CODEC,
                    cpu_stream_frames=TRANCHES), 'processeur')


def assembler(chemins, frequence):
    """Les morceaux d'un moteur recolles en UN passage continu."""
    pause = array.array('h', [0] * int(PAUSE_S * frequence))
    total = array.array('h')
    for chemin in chemins:
        donnees, _frequence = lire_wav(chemin)
        total += donnees
        total += pause
    return total


def appliquer_gain(chemin, gain):
    donnees, frequence = lire_wav(chemin)
    for i in range(len(donnees)):
        valeur = int(donnees[i] * gain)
        if valeur > 32767:
            valeur = 32767
        elif valeur < -32768:
            valeur = -32768
        donnees[i] = valeur
    ecrire_wav(donnees, chemin, frequence)


def main():
    analyseur = argparse.ArgumentParser(
        description="Comparer les moteurs sur les souffles, a l'oreille.")
    analyseur.add_argument('--tirages', type=int, default=TIRAGES)
    options = analyseur.parse_args()

    if le_service_repond():
        print('ARRET : le service du moteur repond sur %s.' % SERVICE)
        print('  Les deux se partageraient la carte, et un REPLI silencieux sur')
        print('  le processeur fausserait tout le test (on croirait tester la')
        print('  carte alors qu on testerait le processeur).')
        print('  -> ferme NIMM ePub, puis relance ce banc.')
        return 1

    reference = DOSSIER_VOIX / (VOIX + '_enhanced_reference.wav')
    if not reference.is_file():
        reference = DOSSIER_VOIX / (VOIX + '_reference.wav')
    if not reference.is_file():
        print('ARRET : reference introuvable pour %s' % VOIX)
        return 2
    texte_reference = ''
    with open(DOSSIER_VOIX / 'references.csv', encoding='utf-8',
              newline='') as flux:
        for ligne in csv.reader(flux, delimiter=';'):
            if len(ligne) >= 2 and ligne[0].strip().startswith(VOIX):
                texte_reference = ligne[1].strip()
                break
    if not texte_reference:
        print('ARRET : le texte de reference de %s est introuvable' % VOIX)
        return 2

    for dossier in (LOT, PASSAGES, PAR_PHRASE):
        dossier.mkdir(parents=True, exist_ok=True)
    for reste in list(PASSAGES.glob('*.wav')) + list(PAR_PHRASE.glob('*.wav')):
        reste.unlink()
    for fichier in (CLE, JOURNAL, SYNTHESE):
        if fichier.is_file():
            fichier.unlink()

    print('=' * 84)
    print(' LES SOUFFLES SUR LA CARTE : comparer les moteurs, a l oreille')
    print('=' * 84)
    print(' voix     : %s' % VOIX)
    print(' phrases  : %d, %d tirages chacune (les phrases de 22/11/63)'
          % (len(mesure.PHRASES), options.tirages))
    print(' sortie   : %s' % LOT)
    print(' garde-fou : le service ne repond PAS sur 8086   OK')
    print('')
    print(' RIEN n est modifie : ni la base, ni les voix, ni le service.')
    print('')

    utilises = set()
    lignes = []
    passages = []
    aigus_moyens = {}
    for etiquette, libelle, appareil, variante, clamp in MOTEURS:
        journaliser('')
        journaliser('%s -- %s' % (etiquette, libelle))
        debut = time.perf_counter()
        try:
            moteur, vrai_appareil = ouvrir_moteur(appareil, variante, clamp)
        except Exception as erreur:
            journaliser('  IMPOSSIBLE : %s : %s'
                        % (type(erreur).__name__, erreur))
            continue
        journaliser('  moteur charge en %.1f s   (appareil : %s)'
                    % (time.perf_counter() - debut, vrai_appareil))
        empreinte = moteur.extract_voice_ref(mesure._audio_24k(reference))
        morceaux = []
        mesures = []
        for rang, phrase in enumerate(mesure.PHRASES, 1):
            for tirage in range(1, options.tirages + 1):
                sons, taux, calcul, abandon = generer(
                    moteur, phrase, empreinte.ref_spk_emb,
                    empreinte.ref_codes, texte_reference)
                nom = nom_au_hasard(utilises) + '.wav'
                chemin = PAR_PHRASE / nom
                ecrire_flottants(sons, taux, chemin)
                duree = (len(sons) / float(taux)) if taux else 0.0
                donnees, frequence = lire_wav(chemin)
                aigus = part_des_aigus(donnees, frequence)
                morceaux.append(chemin)
                mesures.append(aigus)
                lignes.append({'fichier': nom, 'moteur': etiquette,
                               'libelle': libelle, 'phrase': rang,
                               'tirage': tirage, 'duree': duree,
                               'aigus': aigus, 'abandon': abandon})
                journaliser('  phrase %d tirage %d : %.2f s en %.1f s, aigus '
                            '%.4f%s' % (rang, tirage, duree, calcul, aigus,
                                        '   ABANDON' if abandon else ''))
        try:
            moteur.close()
        except Exception:
            pass
        if not morceaux:
            continue
        nom_passage = nom_au_hasard(utilises) + '.wav'
        ecrire_wav(assembler(morceaux, 24000), PASSAGES / nom_passage, 24000)
        passages.append((etiquette, libelle, PASSAGES / nom_passage,
                         nom_passage))
        aigus_moyens[etiquette] = sum(mesures) / len(mesures)

    if not passages:
        print('ARRET : aucun moteur n a pu tourner.')
        return 1

    # Le MEME gain pour tous : sinon le plus fort semblerait le meilleur.
    pics = []
    for _e, _l, chemin, _n in passages:
        donnees, _frequence = lire_wav(chemin)
        pics.append(max(abs(v) for v in donnees) if donnees else 0)
    pic = max(pics) if pics else 0
    if pic:
        gain = (0.90 * 32767.0) / pic
        for _e, _l, chemin, _n in passages:
            appliquer_gain(chemin, gain)
        journaliser('')
        journaliser('nivelage : le MEME gain (x%.3f) pour les %d passages.'
                    % (gain, len(passages)))

    with open(CLE, 'w', encoding='utf-8', newline='') as flux:
        graveur = csv.writer(flux, delimiter=';')
        graveur.writerow(['fichier', 'moteur', 'ce que c est', 'phrase',
                          'tirage', 'duree_s', 'aigus', 'abandon'])
        for ligne in lignes:
            graveur.writerow([ligne['fichier'], ligne['moteur'],
                              ligne['libelle'], ligne['phrase'],
                              ligne['tirage'], '%.2f' % ligne['duree'],
                              '%.4f' % ligne['aigus'],
                              'oui' if ligne['abandon'] else ''])
        graveur.writerow(['--- PASSAGES (a ecouter) ---', '', '', '', '', '', '',
                          ''])
        for etiquette, libelle, _chemin, nom in passages:
            graveur.writerow([nom, etiquette, libelle, '', '', '', '', ''])

    ecrire_lisez_moi(passages)
    ecrire_synthese(passages, lignes, aigus_moyens)

    print('')
    print('=' * 84)
    print(' FINI : %d passages a ecouter' % len(passages))
    print('=' * 84)
    print('  a ecouter : %s' % PASSAGES)
    print('  la cle    : %s   (hors du dossier d ecoute)' % CLE.name)
    print('  aigus mesures : %s'
          % ', '.join('%s=%.4f' % (cle, valeur)
                      for cle, valeur in sorted(aigus_moyens.items())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
