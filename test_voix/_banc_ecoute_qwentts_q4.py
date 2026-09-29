# -*- coding: utf-8 -*-
"""
BANC D'ECOUTE : deux quantifications du moteur Qwen cote a cote -- Q8_0 (l'ANCIEN
modele, garde sur le disque) contre Q4_K_M (celui EN SERVICE depuis le 29/09/2026).

Question de Laurent, 29/09/2026 : « pour B il faut tester ce que ca donne a
l'oreille ». Le modele d'aujourd'hui fait 947 Mo et son codec 278 Mo ; les
versions Q4_K_M font 629 Mo et 255 Mo. Moins de bits = moins d'octets a lire
pour chaque calcul, donc un debit meilleur -- mais la VOIX peut y perdre, et
seule l'oreille de Laurent peut le dire.

Ce que fait l'outil, pour CHAQUE voix demandee et CHAQUE phrase : il fabrique
DEUX WAV cote a cote, marques A et B.

    A = Q8_0     (l'ANCIEN modele, garde sur le disque : la reference d'avant)
    B = Q4_K_M   (celui EN SERVICE depuis le 29/09/2026)

...et il MESURE les deux (temps de calcul, x le temps reel, duree d'audio) :
sans chiffre, on ne saurait pas ce que l'oreille a paye, ni si le candidat
rend la meme chose.

Les fichiers vont dans `test_voix/sortie_banc_qwentts_q4/`, avec un RECAP.txt
qui redit tout noir sur blanc. LECTURE SEULE sur le projet : ni la base, ni les
voix, ni le service ne sont touches. Les GGUF Q4_K_M sont a cote des Q8_0 dans
`qwentts_service/models/` : le service, lui, continue d'utiliser les Q8_0 (il
cherche des noms de fichiers exacts).

L'outil REFUSE de partir si le service du moteur repond sur le port 8086 (les
deux se partageraient les coeurs) ou s'il manque un des deux GGUF Q4_K_M.

Usage (le lanceur double-clic fait tout) :
    python test_voix/_banc_ecoute_qwentts_q4.py
    python test_voix/_banc_ecoute_qwentts_q4.py --voix af_kore
    python test_voix/_banc_ecoute_qwentts_q4.py --phrases 3
"""

import argparse
import sys
import time
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# Le module de mesure porte les phrases, la lecture des voix et la generation :
# on le reutilise tel quel, pour que le banc et la mesure ne divergent jamais.
import _mesurer_debit_qwentts as mesure  # noqa: E402

SORTIE = Path(__file__).resolve().parent / 'sortie_banc_qwentts_q4'
MODELS = mesure.MODELS

# A = l'ANCIENNE quantification (Q8_0, gardee sur le disque) ; B = celle EN
# SERVICE depuis le 29/09/2026 (Q4_K_M, choisie a l'oreille par Laurent). Meme
# moteur, memes reglages : seul le POIDS des modeles change.
QUANTIFICATIONS = [
    ('A', 'Q8_0', MODELS / 'qwen-talker-0.6b-base-Q8_0.gguf',
     MODELS / 'qwen-tokenizer-12hz-Q8_0.gguf'),
    ('B', 'Q4_K_M', MODELS / 'qwen-talker-0.6b-base-Q4_K_M.gguf',
     MODELS / 'qwen-tokenizer-12hz-Q4_K_M.gguf'),
]

# Deux timbres bien differents : une voix du catalogue Kyutai (celle de Sadie,
# que Laurent connait par coeur) et une voix clonee du catalogue Kokoro.
VOIX_DEFAUT = ['10087_11650_000028-0002', 'af_kore']

# Les reglages du service, tels quels.
COEURS, FILS_CODEC, FRAMES = 6, 4, 2


def _ecrire_wav(sons, taux, chemin):
    """Des echantillons float32 -> un WAV mono 16 bits, comme le service."""
    import numpy as np

    entier = np.clip(np.asarray(sons, dtype=np.float32), -1.0, 1.0)
    entier = (entier * 32767.0).astype('<i2')
    with wave.open(str(chemin), 'wb') as sortie:
        sortie.setnchannels(1)
        sortie.setsampwidth(2)
        sortie.setframerate(int(taux))
        sortie.writeframes(entier.tobytes())


def _mesurer_une_quantification(etiquette, nom, talker, codec, options,
                                voix_disponibles, identifiants, textes,
                                resultats):
    """Charge CE moteur UNE fois, puis fabrique les WAV de toutes les voix."""
    import gc

    from qwentts_cpp_cpu import QwenTTS

    print('')
    print('-' * 78)
    print('QUANTIFICATION %s -- %s' % (etiquette, nom))
    print('  modele : %s' % talker.name)
    print('  codec  : %s' % codec.name)
    debut = time.perf_counter()
    moteur = QwenTTS(str(talker), str(codec), cpu_threads=COEURS,
                     cpu_codec_threads=FILS_CODEC, cpu_stream_frames=FRAMES)
    print('  moteur charge en %.1f s' % (time.perf_counter() - debut))

    try:
        for rang_voix, identifiant in enumerate(identifiants):
            chemin_voix, texte_reference = voix_disponibles[identifiant]
            debut = time.perf_counter()
            reference = moteur.extract_voice_ref(mesure._audio_24k(chemin_voix))
            print('  voix %s : empreinte prete en %.1f s' % (identifiant, time.perf_counter() - debut))

            if rang_voix == 0 and not options.sans_chauffe:
                # La premiere phrase d'un moteur frais est a froid (5 s avant le
                # premier son) : on la donne a manger, sans la compter.
                mesure._generer_flux(moteur, textes[0], reference.ref_spk_emb,
                                     reference.ref_codes, texte_reference,
                                     options.plafond)
                print('  chauffe (non comptee) : faite')

            for rang, texte in enumerate(textes, 1):
                sons, taux, calcul, premier, note = mesure._generer_flux(
                    moteur, texte, reference.ref_spk_emb, reference.ref_codes,
                    texte_reference, options.plafond)
                duree = (len(sons) / float(taux)) if taux else 0.0
                rapport = (duree / calcul) if calcul else 0.0
                nom_fichier = '%s__phrase%d__%s_%s.wav' % (identifiant, rang,
                                                           etiquette, nom)
                _ecrire_wav(sons, taux, SORTIE / nom_fichier)
                resultats.append({
                    'etiquette': etiquette, 'nom': nom, 'voix': identifiant,
                    'phrase': rang, 'caracteres': len(texte), 'audio': duree,
                    'calcul': calcul, 'rapport': rapport, 'premier': premier,
                    'note': note, 'fichier': nom_fichier,
                })
                print('  phrase %d : %6.2f s de calcul, %5.2f s d audio, x%.2f, '
                      'premier son %.2f s  ->  %s%s'
                      % (rang, calcul, duree, rapport, premier, nom_fichier,
                         ('   <<< %s' % note) if note else ''))
    finally:
        try:
            moteur.close()
        except Exception:
            pass
        del moteur
        gc.collect()


def _resume(resultats):
    """Le tableau A / B a l'ecran, et le RECAP.txt qui accompagne les WAV."""
    print('')
    print('=' * 100)
    print('RESUME -- A = Q8_0 (l ancien modele)   B = Q4_K_M (celui en service)')
    print('=' * 100)
    print('%-38s %5s %10s %10s %9s %16s'
          % ('voix / phrase', 'car.', 'A x temps', 'B x temps', 'gain',
             'audio A / B'))
    print('-' * 100)

    couples = {}
    for resultat in resultats:
        couples.setdefault((resultat['voix'], resultat['phrase']), {})[
            resultat['etiquette']] = resultat

    lignes = []
    gains = []
    for (voix, phrase), paire in sorted(couples.items()):
        a = paire.get('A')
        b = paire.get('B')
        if not a or not b:
            print('%-38s %5s   une seule quantification disponible'
                  % ('%s / phrase %d' % (voix, phrase), '?'))
            continue
        gain = ((b['rapport'] / a['rapport'] - 1.0) * 100.0
                if a['rapport'] else 0.0)
        gains.append(gain)
        print('%-38s %5d %10.2f %10.2f %+8.0f %% %7.2f /%6.2f s'
              % ('%s / phrase %d' % (voix, phrase), a['caracteres'],
                 a['rapport'], b['rapport'], gain, a['audio'], b['audio']))
        lignes.append('%s / phrase %d : A %.2f x (%.2f s d\'audio) -- B %.2f x '
                      '(%.2f s d\'audio) -- %+.0f %%'
                      % (voix, phrase, a['rapport'], a['audio'], b['rapport'],
                         b['audio'], gain))

    if gains:
        moyenne = sum(gains) / len(gains)
        print('')
        print('Gain du Q4_K_M (celui en service) : %+.0f %% de debit' % moyenne)
    print('')
    print('A ECOUTER : les fichiers de %s' % SORTIE)
    print('  ...__A_Q8_0.wav   = l ancien modele (Q8_0, garde comme repli)')
    print('  ...__B_Q4_K_M.wav = celui EN SERVICE depuis le 29/09/2026')
    print('Ecoute les DEUX d une meme voix, l un apres l autre, et dis ce qui')
    print('change : timbre, clarte, accrocs, respiration, prosodie.')

    with open(SORTIE / 'RECAP.txt', 'w', encoding='utf-8') as fichier:
        fichier.write('BANC D ECOUTE QWEN -- Q8_0 (A) contre Q4_K_M (B)\n')
        fichier.write('Genere le %s\n\n' % time.strftime('%d/%m/%Y %H:%M'))
        fichier.write('A = Q8_0, l ANCIEN modele (garde sur le disque comme repli).\n')
        fichier.write('B = Q4_K_M, celui EN SERVICE depuis le 29/09/2026 '
                      '(choisi a l oreille par Laurent : « les plus jolies a '
                      'l oreille »).\n')
        fichier.write('Les deux ont ete generes avec les MEMES reglages '
                      '(%d coeurs, %d fils de codec, tranches de %d images) '
                      'et la MEME phrase.\n\n'
                      % (COEURS, FILS_CODEC, FRAMES))
        fichier.write('Mesures (x temps reel : plus grand = plus rapide) :\n')
        for ligne in lignes:
            fichier.write('  %s\n' % ligne)
        if gains:
            fichier.write('\nGain moyen du candidat : %+.0f %%\n'
                          % (sum(gains) / len(gains)))
        fichier.write('\nCe qu il reste a faire : ECOUTER, et decider.\n')


# ============================================================
# PROGRAMME
# ============================================================

def main():
    analyseur = argparse.ArgumentParser(
        description='Banc d ecoute : Q8_0 (aujourd hui) contre Q4_K_M (candidat).')
    analyseur.add_argument('--voix', default=','.join(VOIX_DEFAUT),
                           help='identifiants de voix, separes par des virgules '
                                '(defaut : la voix de Sadie + une voix clonee)')
    analyseur.add_argument('--phrases', type=int, default=2,
                           help='nombre de phrases, de 1 a 3 (defaut : 2)')
    analyseur.add_argument('--sans-chauffe', action='store_true',
                           help='compte la premiere phrase, qui paye le demarrage '
                                'a froid (non recommandee)')
    analyseur.add_argument('--plafond', type=float, default=120.0,
                           help='secondes de calcul avant d abandonner une phrase')
    options = analyseur.parse_args()

    try:
        import qwentts_cpp_cpu
    except ImportError:
        print('ARRET : la bibliotheque du moteur est introuvable.')
        print('Ce banc doit tourner avec le Python du MOTEUR :')
        print('  qwentts_service\\.venv\\Scripts\\python.exe')
        print('Utilise le lanceur LANCER_BANC_ECOUTE_QWENTTS_Q4.bat.')
        return 1

    if mesure._le_service_repond():
        print('ARRET : le moteur repond deja sur le port %d.'
              % mesure.PORT_SERVICE)
        print('Ferme sa fenetre, puis relance : les deux se partageraient les')
        print('coeurs, et les mesures ne voudraient rien dire.')
        return 1

    for etiquette, nom, talker, codec in QUANTIFICATIONS:
        for fichier in (talker, codec):
            if not fichier.exists():
                print('ARRET : il manque %s' % fichier)
                if etiquette == 'B':
                    print('Les deux GGUF Q4_K_M viennent de :')
                    print('  https://huggingface.co/Serveurperso/Qwen3-TTS-GGUF')
                    print('(qwen-talker-0.6b-base-Q4_K_M.gguf et '
                          'qwen-tokenizer-12hz-Q4_K_M.gguf, 629 + 255 Mo)')
                return 1
            # Un telechargement interrompu laisse un fichier TROP PETIT : le
            # moteur echouerait au chargement, avec un message obscur. On le dit
            # ici, en clair (lecon du 29/09/2026 : les tailles de Hugging Face
            # sont en Mo decimaux, un fichier de 599,8 Mio EST complet).
            plancher = (600_000_000 if 'talker' in fichier.name
                        else 250_000_000)
            if fichier.stat().st_size < plancher:
                print('ARRET : %s est INCOMPLET (%d octets, il en faut au moins '
                      '%d).' % (fichier.name, fichier.stat().st_size, plancher))
                print('Relance le telechargement de ce fichier.')
                return 1

    if not 1 <= options.phrases <= len(mesure.PHRASES):
        print('ARRET : --phrases doit etre entre 1 et %d.' % len(mesure.PHRASES))
        return 1

    voix_disponibles = mesure._repertorier_voix()
    identifiants = [morceau.strip() for morceau in options.voix.split(',')
                    if morceau.strip()]
    if not identifiants:
        print('ARRET : aucune voix demandee.')
        return 1
    for identifiant in identifiants:
        if identifiant not in voix_disponibles:
            print('ARRET : voix inconnue : %s' % identifiant)
            print('(les identifiants sont les noms de fichiers sans leur suffixe)')
            return 1

    textes = mesure.PHRASES[:options.phrases]
    SORTIE.mkdir(parents=True, exist_ok=True)

    print('=' * 92)
    print('BANC D ECOUTE -- A = Q8_0 (l ancien) contre B = Q4_K_M (celui en service)')
    print('=' * 92)
    print('moteur  : qwentts_cpp_cpu %s (ABI %s, processeur seul : %s)'
          % (qwentts_cpp_cpu.__version__, qwentts_cpp_cpu.QT_ABI_VERSION,
             qwentts_cpp_cpu.CPU_ONLY))
    print('voix    : %s' % ', '.join(identifiants))
    print('phrases : %d, de %d a %d caracteres'
          % (len(textes), min(len(t) for t in textes),
             max(len(t) for t in textes)))
    print('reglages: %d coeurs, %d fils de codec, tranches de %d images (ceux '
          'du service)' % (COEURS, FILS_CODEC, FRAMES))
    print('sortie  : %s' % SORTIE)
    print('')
    print('Le processeur travaille a plein pendant deux a quatre minutes : le')
    print('ventilateur peut se faire entendre, c est normal.')

    resultats = []
    for etiquette, nom, talker, codec in QUANTIFICATIONS:
        _mesurer_une_quantification(etiquette, nom, talker, codec, options,
                                    voix_disponibles, identifiants, textes,
                                    resultats)

    _resume(resultats)
    print('')
    print('Le service, lui, utilise les Q4_K_M depuis le 29/09/2026 (choisis a')
    print('l oreille) ; les Q8_0 restent sur le disque comme repli automatique.')
    return 0


if __name__ == '__main__':
    sys.exit(main())


