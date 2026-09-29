# -*- coding: utf-8 -*-
"""
MESURE : le moteur Qwen (qwentts.cpp) tient-il le temps reel, et que changent
les reglages du PROCESSEUR ?

Question de Laurent, 29/09/2026 : « sur GitHub ils parlaient de 800 fois la
vitesse de generation, est-ce qu'on peut optimiser Qwen ? » Le moteur est deja
sur son chemin optimise (x0,94 mesure le 28/09 : fils de codec, tranches de
2 images, priorite d'entame). Cet outil mesure ce qu'il reste a prendre du cote
du PROCESSEUR : le nombre de coeurs, et l'epinglage des threads.

Ce qu'il fait, pour chaque configuration :
  - charge qwentts.cpp sur le processeur (aucune carte graphique touchee) ;
  - prepare l'empreinte d'UNE voix, une seule fois (comme le service) ;
  - fait dire les MEMES phrases REELLES de livre, en CONSOMMANT LE FLUX -- le
    mode le plus rapide, celui qu'utilise le service ;
  - mesure : temps de calcul, duree d'audio, facteur x le temps reel, et le
    temps du premier son.

Ce qu'il ne fait PAS : il ne modifie ni la base, ni les voix, ni le service, et
il n'ecrit aucun fichier. Il REFUSE de partir si le service du moteur est allume
(port 8086) : les deux se partageraient les coeurs et la mesure ne voudrait rien
dire.

Garde-fou de temps : une phrase qui depasserait --plafond secondes de calcul est
interrompue proprement (annulation native), et compte comme ABANDON.

Usage (le lanceur double-clic fait tout) :
    python test_voix/_mesurer_debit_qwentts.py
    python test_voix/_mesurer_debit_qwentts.py --prises 3 --coeurs 6,8,12
    python test_voix/_mesurer_debit_qwentts.py --affinite
    python test_voix/_mesurer_debit_qwentts.py --talker ... --codec ...  (autres GGUF)
"""

import argparse
import gc
import os
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SERVICE = RACINE / 'qwentts_service'
MODELS = SERVICE / 'models'
DOSSIER_VOIX = RACINE / 'qwen_tts_service' / 'voix'
FICHIER_TEXTES = DOSSIER_VOIX / 'references.csv'
# Les textes des voix de la FAMILLE vivent dans un second fichier, HORS Git
# (Maya a lu le debut d'un roman du commerce : la ligne ne peut pas partir sur le
# depot). Le service lit les deux -- l'outil d'atelier doit voir la MEME chose,
# sinon il mesurerait une voix sans son texte (mode timbre seul).
FICHIER_TEXTES_PRIVES = DOSSIER_VOIX / 'references_privees.csv'

# Les memes suffixes que le service : l'identifiant de voix est le nom du
# fichier SANS le suffixe reconnu.
SUFFIXES_FICHIERS = ('_enhanced_reference.wav', '_reference.wav')

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

LANGUE = 'french'
PORT_SERVICE = 8086

# Le coeur de l'affichage : le x temps reel est la seule unite qui parle.
# > 1 = le moteur va plus vite que la lecture ; < 1 = le lecteur doit
# precharger pour ne pas s'arreter.

# Les phrases de mesure : TROIS vraies phrases du livre 28 (« 22/11/63 »),
# chapitre 20, de 152 a 155 caracteres -- la taille exacte de ce que le lecteur
# envoie au moteur. Elles sont figees ici pour que deux campagnes se comparent.
PHRASES = [
    'Je me suis fait installer le téléphone et la première personne que '
    'j’ai appelée fut Ellen Dockerty, qui me communiqua avec joie l’adresse '
    'de Sadie à Reno.',
    'Je lui ai écrit une lettre aussitôt après avoir raccroché, détestant '
    'mon ton guindé, artificiellement bavard mais ne sachant comment '
    'm’en dépêtrer.',
    'Ça, c’était encore ma jalousie maladive, et j’ai bouclé ma lettre en '
    'vitesse, sachant que j’avais probablement pris des accents plaintifs, '
    'et m’en foutant.',
]

# Les configurations : (nom, coeurs, fils de codec, tranches, affinite,
# affinite codec). La PREMIERE est le reglage d'aujourd'hui, celui du service
# (`qwentts_service/servir_qwentts_cpp.py`) : c'est la reference.
CONFIGS = [
    ('aujourd hui (service)', 6, 4, 2, 0, 0),
    ('4 coeurs', 4, 4, 2, 0, 0),
    ('8 coeurs', 8, 4, 2, 0, 0),
    ('12 coeurs', 12, 4, 2, 0, 0),
]

# Ajoutees par --affinite : on EPINGLE le moteur sur les six premiers CPU
# logiques (masque 0b111111 = 63), au lieu de laisser l'ordonnanceur de Windows
# promener les threads. Aucun risque : si le masque est refuse, le moteur le dit
# AVANT de charger les modeles.
CONFIGS_AFFINITE = [
    ('6 coeurs epingles 0-5', 6, 4, 2, 63, 0),
    ('codec epingle 6-11', 6, 4, 2, 63, 4032),
]

# Ajoutees par --leviers : les deux reglages du SERVICE que l'on peut encore
# pousser, puisque c'est le DECODAGE DU CODEC qui domine (12,1 s sur 12,7 s au
# premier essai du 29/09). Un fil de plus pour le codec, ou des tranches plus
# grosses, se mesurent.
CONFIGS_LEVIERS = [
    ('8 fils de codec', 6, 8, 2, 0, 0),
    ('tranches de 4 images', 6, 4, 4, 0, 0),
]


# ============================================================
# OUTILLAGE (copie fidele de ce que fait le service)
# ============================================================

def _le_service_repond():
    """Le service du moteur repond-il deja sur son port ?"""
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/sante' % PORT_SERVICE,
                                    timeout=2):
            return True
    except Exception:
        return False


def _lire_textes():
    """{nom de fichier: texte} depuis `references.csv` PUIS le fichier prive.

    Le fichier prive (voix de la famille) est lu en second : c'est le meme ordre
    que le service, et le prive gagne si une voix est dans les deux.
    """
    textes = {}
    for chemin in (FICHIER_TEXTES, FICHIER_TEXTES_PRIVES):
        if not chemin.exists():
            continue
        with open(chemin, encoding='utf-8-sig') as fichier:
            for ligne in fichier.read().splitlines():
                if not ligne.strip() or ligne.startswith('fichier;'):
                    continue
                morceaux = ligne.split(';')
                if len(morceaux) >= 2:
                    textes[morceaux[0].strip()] = morceaux[1].strip()
    return textes


def _repertorier_voix():
    """{identifiant: (chemin WAV, texte de reference)} -- comme le service."""
    textes = _lire_textes()
    trouvees = {}
    if DOSSIER_VOIX.is_dir():
        for fichier in sorted(DOSSIER_VOIX.glob('*.wav')):
            identifiant = fichier.name
            for suffixe in SUFFIXES_FICHIERS:
                if identifiant.endswith(suffixe):
                    identifiant = identifiant[:-len(suffixe)]
                    break
            trouvees[identifiant] = (fichier, textes.get(fichier.name, ''))
    return trouvees


def _audio_24k(chemin):
    """Un WAV mono 24 kHz en float32 (ce que le moteur attend)."""
    import numpy as np

    with wave.open(str(chemin), 'rb') as fichier:
        canaux = fichier.getnchannels()
        largeur = fichier.getsampwidth()
        frequence = fichier.getframerate()
        brut = fichier.readframes(fichier.getnframes())
    if largeur != 2:
        raise ValueError('WAV non 16 bits : %s' % chemin)
    donnees = np.frombuffer(brut, dtype=np.int16).astype(np.float32)
    if canaux > 1:
        donnees = donnees.reshape(-1, canaux).mean(axis=1)
    if frequence != 24000:
        raise ValueError('WAV en %d Hz, or le moteur attend 24 000 : %s'
                         % (frequence, chemin))
    return donnees / 32768.0


def _duree_plausible(texte):
    """Le meme plafond que le service (3 fois la duree plausible, plancher 3 s)."""
    return max(3.0, (len(texte) / 14.0) * 3.0 + 1.0)


# ============================================================
# UNE PHRASE, PUIS UNE CONFIGURATION ENTIERE
# ============================================================

def _generer_flux(moteur, texte, spk, codes, texte_reference, plafond_s):
    """(sons, taux, calcul, premier son, note) : une phrase, en consommant le flux.

    Rend AUSSI les echantillons : les bancs d'ecoute en ont besoin pour ecrire
    des WAV, et refaire la boucle deux fois serait un nid a divergences.

    note : '' si tout va bien, 'ABANDON' si le garde-fou de temps a coupe (le
    moteur ne s'arrete pas), 'DERIVE' si l'audio depasse le plafond du service.
    """
    import numpy as np

    annulation = threading.Event()
    minuteur = threading.Timer(plafond_s, annulation.set)
    minuteur.start()
    debut = time.perf_counter()
    premier = None
    morceaux = []
    taux = 24000
    try:
        for bloc, taux in moteur.stream(
                text=texte, lang=LANGUE, ref_spk_emb=spk, ref_codes=codes,
                ref_text=texte_reference, cancel_event=annulation):
            if premier is None:
                premier = time.perf_counter() - debut
            morceaux.append(bloc)
    finally:
        minuteur.cancel()

    calcul = time.perf_counter() - debut
    sons = (np.concatenate(morceaux) if morceaux
            else np.zeros(0, dtype=np.float32))
    duree = (len(sons) / float(taux)) if taux else 0.0
    if annulation.is_set():
        note = 'ABANDON'
    elif duree > _duree_plausible(texte):
        note = 'DERIVE'
    else:
        note = ''
    return sons, taux, calcul, (premier or 0.0), note


def _mesurer_phrase(moteur, texte, spk, codes, texte_reference, plafond_s):
    """(audio, calcul, premier son, note) : la mesure SEULE (sans les echantillons)."""
    sons, taux, calcul, premier, note = _generer_flux(
        moteur, texte, spk, codes, texte_reference, plafond_s)
    duree = (len(sons) / float(taux)) if taux else 0.0
    return duree, calcul, premier, note


def _mesurer_config(nom, coeurs, fils_codec, frames, affinite, affinite_codec,
                    options, textes, identifiant, chemin_voix, texte_reference):
    """Charge le moteur avec CES reglages, mesure tout, puis libere la memoire."""
    from qwentts_cpp_cpu import QwenTTS

    print('')
    print('-' * 78)
    print('CONFIGURATION : %s' % nom)
    print('  %d coeurs | %d fils de codec | tranches de %d images | affinite %d/%d'
          % (coeurs, fils_codec, frames, affinite, affinite_codec))
    debut = time.perf_counter()
    try:
        moteur = QwenTTS(str(options.talker), str(options.codec),
                         cpu_threads=coeurs,
                         cpu_codec_threads=fils_codec,
                         cpu_stream_frames=frames,
                         cpu_affinity=affinite,
                         cpu_codec_affinity=affinite_codec)
    except Exception as erreur:
        print('  REFUSEE par le moteur : %s : %s'
              % (type(erreur).__name__, erreur))
        return None
    print('  moteur charge en %.1f s' % (time.perf_counter() - debut))

    try:
        debut = time.perf_counter()
        reference = moteur.extract_voice_ref(_audio_24k(chemin_voix))
        print('  empreinte de la voix %s prete en %.1f s (une seule fois)'
              % (identifiant, time.perf_counter() - debut))

        if not options.sans_chauffe:
            # CHAUFFE, non comptee : la toute premiere phrase d'un moteur
            # fraichement charge paye un demarrage a froid (5,0 s avant le
            # premier son lors de l'essai du 29/09, alors que le service annonce
            # 0,5 a 0,6 s ensuite). La compter ecraserait le signal cherche : ce
            # qu'on veut comparer, c'est le REGIME ETABLI.
            _duree, calcul, premier, note = _mesurer_phrase(
                moteur, textes[0], reference.ref_spk_emb, reference.ref_codes,
                texte_reference, options.plafond)
            print('  chauffe (non comptee) : %6.2f s de calcul, premier son '
                  '%.2f s%s' % (calcul, premier,
                                ('   <<< %s' % note) if note else ''))

        mesures = []
        for prise in range(1, options.prises + 1):
            for rang, texte in enumerate(textes, 1):
                duree, calcul, premier, note = _mesurer_phrase(
                    moteur, texte, reference.ref_spk_emb, reference.ref_codes,
                    texte_reference, options.plafond)
                rapport = (duree / calcul) if calcul else 0.0
                mesures.append((rang, prise, duree, calcul, premier, rapport,
                                note))
                print('  phrase %d, prise %d : %6.2f s de calcul pour %5.2f s '
                      'd audio  x%.2f  premier son %.2f s%s'
                      % (rang, prise, calcul, duree, rapport, premier,
                         ('   <<< %s' % note) if note else ''))
        return _bilan(nom, coeurs, fils_codec, frames, affinite, mesures)
    finally:
        try:
            moteur.close()
        except Exception:
            pass
        del moteur
        gc.collect()


def _bilan(nom, coeurs, fils_codec, frames, affinite, mesures):
    """Le resume d'une configuration : moyenne, fourchette, pannes."""
    valides = [mesure for mesure in mesures if not mesure[6]]
    if not valides:
        return {'nom': nom, 'coeurs': coeurs, 'fils_codec': fils_codec,
                'frames': frames, 'affinite': affinite, 'mesures': mesures,
                'valides': 0, 'facteur': 0.0, 'facteur_min': 0.0,
                'facteur_max': 0.0, 'premier': 0.0, 'global': 0.0}
    facteurs = [mesure[5] for mesure in valides]
    audio = sum(mesure[2] for mesure in valides)
    calcul = sum(mesure[3] for mesure in valides)
    return {
        'nom': nom, 'coeurs': coeurs, 'fils_codec': fils_codec,
        'frames': frames, 'affinite': affinite, 'mesures': mesures,
        'valides': len(valides),
        'facteur': statistics.fmean(facteurs),
        'facteur_min': min(facteurs),
        'facteur_max': max(facteurs),
        'premier': statistics.fmean([mesure[4] for mesure in valides]),
        'global': (audio / calcul) if calcul else 0.0,
    }


def _verdict(reference, bilan):
    """Dit en une phrase ce qu'une configuration change par rapport au reglage d'aujourd'hui."""
    if not bilan['valides']:
        return 'AUCUNE mesure valide (a relancer)'
    if not reference['valides']:
        return 'pas de reference'
    ecart = (bilan['facteur'] / reference['facteur'] - 1.0) * 100.0
    # La lecon du projet (28/09) : deux mesures ne se distinguent que si leurs
    # FOURCHETTES ne se recoupent pas. Sinon, c'est du bruit.
    recoupement = (bilan['facteur_min'] <= reference['facteur_max']
                   and reference['facteur_min'] <= bilan['facteur_max'])
    if recoupement:
        return '%+.0f %% -- fourchettes qui se recoupent : NON ACQUIS' % ecart
    return '%+.0f %% -- fourchettes separees : acquis' % ecart


def _tableau(bilans):
    """Le resume de la campagne, et ce qu'on peut en conclure honnetement."""
    print('')
    print('=' * 92)
    print('RESUME DE LA CAMPAGNE')
    print('=' * 92)
    print('%-26s %6s %8s %8s %8s %9s'
          % ('configuration', 'coeurs', 'x moyen', 'x mini', 'x maxi', '1er son'))
    print('-' * 92)
    for bilan in bilans:
        if not bilan['valides']:
            print('%-26s %6d   aucune mesure valide' % (bilan['nom'], bilan['coeurs']))
            continue
        print('%-26s %6d %8.2f %8.2f %8.2f %7.2f s'
              % (bilan['nom'], bilan['coeurs'], bilan['facteur'],
                 bilan['facteur_min'], bilan['facteur_max'], bilan['premier']))
    print('')
    print('Lecture : x = combien de fois plus vite que la lecture. Au-dessus de')
    print('1,00 le moteur prend de l avance ; en dessous, c est le prechargement')
    print('du lecteur qui encaisse le retard (notre valeur du 28/09 : x0,94).')
    if bilans:
        reference = bilans[0]
        print('')
        print('Comparaison a la PREMIERE configuration (%s) :' % reference['nom'])
        for bilan in bilans[1:]:
            print('  - %-26s %s' % (bilan['nom'], _verdict(reference, bilan)))
        print('')
        print('Regle de lecture : une configuration ne vaut la peine d etre adoptee')
        print('que si ses prises sont au-dessus de 1,00 ET que ses fourchettes ne se')
        print('recoupent pas avec celles d aujourd hui. Sinon, c est du bruit.')


# ============================================================
# PROGRAMME
# ============================================================

def main():
    analyseur = argparse.ArgumentParser(
        description='Mesure le debit de qwentts.cpp selon les reglages du '
                    'processeur (aucune carte graphique).')
    analyseur.add_argument('--prises', type=int, default=3,
                           help='prises par phrase (defaut : 3)')
    analyseur.add_argument('--phrases', type=int, default=3,
                           help='nombre de phrases, de 1 a 3 (defaut : 3)')
    analyseur.add_argument('--coeurs', default='',
                           help='coeurs a tester, separes par des virgules '
                                '(defaut : 6,4,8,12 ; le 6 est celui d aujourd hui)')
    analyseur.add_argument('--affinite', action='store_true',
                           help='ajoute deux configurations EPINGLEES (masques de '
                                'CPU logiques)')
    analyseur.add_argument('--sans-priorite', action='store_true',
                           help='n active pas la priorite d entame (pour comparer)')
    analyseur.add_argument('--leviers', action='store_true',
                           help='ajoute les leviers du service (8 fils de codec, '
                                'tranches de 4 images)')
    analyseur.add_argument('--sans-chauffe', action='store_true',
                           help='compte aussi la toute premiere phrase, qui paye un '
                                'demarrage a froid (non recommandee)')
    analyseur.add_argument('--voix', default='',
                           help='identifiant de voix (defaut : la premiere trouvee)')
    analyseur.add_argument('--plafond', type=float, default=120.0,
                           help='secondes de calcul avant d abandonner une phrase '
                                '(defaut : 120)')
    analyseur.add_argument('--talker', type=Path,
                           default=MODELS / 'qwen-talker-0.6b-base-Q4_K_M.gguf',
                           help='le GGUF du modele (les Q4_K_M sont ceux du service '
                                'depuis le 29/09/2026 ; pour mesurer les anciens, '
                                '--talker ...Q8_0.gguf)')
    analyseur.add_argument('--codec', type=Path,
                           default=MODELS / 'qwen-tokenizer-12hz-Q4_K_M.gguf',
                           help='le GGUF du codec')
    options = analyseur.parse_args()

    try:
        import qwentts_cpp_cpu
    except ImportError:
        print('ARRET : la bibliotheque du moteur est introuvable.')
        print('Ce script doit tourner avec le Python du MOTEUR :')
        print('  qwentts_service\\.venv\\Scripts\\python.exe')
        print('Utilise le lanceur double-clic LANCER_MESURE_DEBIT_QWENTTS.bat.')
        return 1

    if _le_service_repond():
        print('ARRET : le moteur repond deja sur le port %d.' % PORT_SERVICE)
        print('Les deux se partageraient les coeurs, et la mesure ne voudrait rien')
        print('dire. Ferme la fenetre du moteur (ou le lecteur), puis relance.')
        return 1

    if not options.talker.exists() or not options.codec.exists():
        print('ARRET : il manque un modele :')
        print('  %s' % options.talker)
        print('  %s' % options.codec)
        return 1
    if not 1 <= options.phrases <= len(PHRASES):
        print('ARRET : --phrases doit etre entre 1 et %d.' % len(PHRASES))
        return 1
    if options.prises < 1:
        print('ARRET : --prises doit valoir au moins 1.')
        return 1

    voix_disponibles = _repertorier_voix()
    if not voix_disponibles:
        print('ARRET : aucune voix dans %s' % DOSSIER_VOIX)
        return 1
    if options.voix:
        if options.voix not in voix_disponibles:
            print('ARRET : voix inconnue : %s' % options.voix)
            print('(les identifiants sont les noms de fichiers sans leur suffixe)')
            return 1
        identifiant = options.voix
    else:
        identifiant = sorted(voix_disponibles)[0]
    chemin_voix, texte_reference = voix_disponibles[identifiant]

    if not options.sans_priorite:
        # Le MEME reglage que le service : la priorite d'entame.
        os.environ.setdefault('QWENTTS_CPU_STARTUP_PRIORITY', 'second_chunk')

    if options.coeurs.strip():
        try:
            demandes = [int(morceau) for morceau in options.coeurs.split(',')
                        if morceau.strip()]
        except ValueError:
            print('ARRET : --coeurs attend des nombres separes par des virgules.')
            return 1
        configs = [('coeurs %d' % nombre, nombre, 4, 2, 0, 0)
                   for nombre in demandes]
    else:
        configs = list(CONFIGS)
    if options.affinite:
        configs += CONFIGS_AFFINITE
    if options.leviers:
        configs += CONFIGS_LEVIERS

    maximum = os.cpu_count() or 1
    textes = PHRASES[:options.phrases]
    print('=' * 92)
    print('DEBIT DE qwentts.cpp SELON LES REGLAGES DU PROCESSEUR')
    print('=' * 92)
    print('bibliotheque : qwentts_cpp_cpu %s (ABI %s, processeur seul : %s)'
          % (qwentts_cpp_cpu.__version__, qwentts_cpp_cpu.QT_ABI_VERSION,
             qwentts_cpp_cpu.CPU_ONLY))
    print('modele       : %s' % options.talker.name)
    print('codec        : %s' % options.codec.name)
    print('machine      : %d coeurs logiques' % maximum)
    print('voix         : %s' % identifiant)
    if not texte_reference:
        print('ATTENTION    : cette voix n a pas de texte dans references.csv :')
        print('               elle sera lue en mode timbre seul, qui n est pas le')
        print('               mode du service (mode ICL : reference PLUS son texte).')
    print('phrases      : %d phrase(s) de %d a %d caracteres, %d prises chacune'
          % (len(textes), min(len(t) for t in textes),
             max(len(t) for t in textes), options.prises))
    print('configurations : %d' % len(configs))
    # Une phrase de ~150 caracteres coute une dizaine de secondes de calcul : on
    # ANNONCE la duree, pour que Laurent sache a quoi s'attendre.
    par_config = options.prises * len(textes) + (0 if options.sans_chauffe else 1)
    minutes = max(1, round(len(configs) * (4 + par_config * 11) / 60.0))
    print('')
    print('Ce que tu vas voir : le processeur travaille a PLEIN pendant environ')
    print('%d minutes, sur %d configuration(s). Le ventilateur peut se faire'
          % (minutes, len(configs)))
    print('entendre : c est normal, ce sont EXACTEMENT les memes calculs que')
    print('pendant la lecture d un livre, juste groupes au lieu d etre etales.')
    print('Un processeur qui chauffe se ralentit TOUT SEUL : il ne casse pas.')

    bilans = []
    for nom, coeurs, fils_codec, frames, affinite, affinite_codec in configs:
        if coeurs > maximum:
            print('')
            print('CONFIGURATION : %s -- SAUTEE : %d coeurs demandes, %d disponibles.'
                  % (nom, coeurs, maximum))
            continue
        bilan = _mesurer_config(nom, coeurs, fils_codec, frames, affinite,
                                affinite_codec, options, textes, identifiant,
                                chemin_voix, texte_reference)
        if bilan:
            bilans.append(bilan)

    _tableau(bilans)
    print('')
    print('Rien n a ete modifie : ni la base, ni les voix, ni le service.')
    print('Le reglage d aujourd hui (celui du service) est : %d coeurs, %d fils '
          'de codec, tranches de %d images.'
          % (CONFIGS[0][1], CONFIGS[0][2], CONFIGS[0][3]))
    return 0


if __name__ == '__main__':
    sys.exit(main())



