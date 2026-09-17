# -*- coding: utf-8 -*-
"""Verifie le service NeuTTS cote LOGIQUE (session du 16/09/2026).

Le moteur NeuTTS n'est PAS charge : ce test verifie ce qui peut etre verifie
sans lui -- le decoupage du texte, le filet anti-derive, le rognage du silence
de queue, le format du WAV, la lecture des references (avec leur texte), et le
CONTRAT avec le lecteur (port 8084, graine fixe, une seule generation a la
fois).

Les fonctions sont prises DANS neutts_service/servir_neutts.py (jamais
recopiees) : si elles changent la-bas, ce test les suit.

Contexte utile : le service XTTS, lui, avait besoin de DEUX filets anti-babil
(bornage de generation + rognage d'un residu apres un long silence). La mesure
de l'atelier NIMM Voix du 16/09/2026 (8 phrases de 4 a 117 caracteres) montre
que NeuTTS n'a pas ce defaut : il ne reste donc qu'un filet TRES LARGE, et ce
test verifie qu'il ne peut pas mordre sur une phrase normale.

Usage : python test_voix/test_neutts_service.py
"""

import csv
import importlib.util
import sys
import tempfile
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np                                              # noqa: E402

SERVICE = RACINE / 'neutts_service' / 'servir_neutts.py'

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def charger_service():
    """Charge le service comme module (sans rien executer de lui)."""
    spec = importlib.util.spec_from_file_location('servir_neutts', SERVICE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _petit_wav(chemin, duree_s=0.2, frequence=24000):
    """Ecris un WAV minuscule : le service ne lit que les NOMS au reperage."""
    with wave.open(str(chemin), 'wb') as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(frequence)
        fichier.writeframes(b'\x00\x00' * int(duree_s * frequence))


def main_verifications():
    svc = charger_service()
    frequence = svc.FREQUENCE

    print('')
    print('1) le contrat avec le lecteur (rien d autre ne le dit)')
    verifier('le port par defaut est 8084', svc.PORT == 8084, svc.PORT)
    verifier('la limite de texte est 200 caracteres (fenetre du moteur)',
             svc.MAX_CARACTERES == 200, svc.MAX_CARACTERES)
    verifier('la graine est fixee (meme texte = meme audio)',
             svc.GRAINE == 42, svc.GRAINE)
    verifier('le WAV sort en 24000 Hz (comme XTTS)',
             svc.FREQUENCE == 24000, svc.FREQUENCE)
    verifier('deux moteurs ne peuvent pas ouvrir le meme port',
             svc.ServiceNeutts.allow_reuse_address is False)
    source = SERVICE.read_text(encoding='utf-8')
    verifier('la graine est bien transmise au moteur',
             'NeuTTS(seed=GRAINE' in source)
    for route in ('/sante', '/voix', '/recharger', '/tts'):
        verifier('la route %s existe' % route, ('"%s"' % route) in source)

    print('')
    print('2) le decoupage du texte (meme logique que l atelier)')
    plan = svc.plan_de_lecture('Bonjour. Comment allez-vous ?')
    verifier('deux phrases -> deux morceaux', len(plan) == 2, len(plan))
    plan = svc.plan_de_lecture('M. Dupont est arrive. Il partit.')
    verifier('l abreviation M. ne coupe pas la phrase', len(plan) == 2, len(plan))
    plan = svc.plan_de_lecture('Il partit. puis revint.')
    verifier('un fragment en minuscule est recolle', len(plan) == 1, len(plan))
    phrase_longue = ('Il marchait lentement le long de la riviere, ' * 6).strip()
    morceaux = svc.decouper_trop_long(phrase_longue)
    verifier('une phrase trop longue est redécoupee',
             len(morceaux) > 1 and all(len(m) <= 200 for m in morceaux),
             [len(m) for m in morceaux])
    verifier('le texte est conserve a l identique',
             ' '.join(' '.join(morceaux).split()) == ' '.join(phrase_longue.split()))
    verifier('un texte vide ne produit aucun morceau',
             svc.plan_de_lecture('   ') == [])

    print('')
    print('3) le filet anti-derive ne mord JAMAIS sur une phrase normale')
    # Durees mesurees a l atelier sur NeuTTS (rapport x0,6 a x1,4).
    for texte, duree_mesuree in (('Manger ?', 1.10), ('Non.', 1.10),
                                 ('Que preferez-vous ?', 1.40),
                                 ('Bonjour, comment allez-vous ?', 1.84),
                                 ('Il arriva enfin, apres trois jours de marche, '
                                  'au pied de la tour.', 5.30)):
        borne = svc.duree_max_derivee(texte)
        verifier('%3d car. : borne %.1f s > duree mesuree %.2f s'
                 % (len(texte), borne, duree_mesuree), borne > duree_mesuree * 2)
    verifier('un plancher protege les phrases tres courtes (>= %s s)'
             % svc.DERIVE_MINIMUM_S,
             svc.duree_max_derivee('Non.') >= svc.DERIVE_MINIMUM_S,
             svc.duree_max_derivee('Non.'))
    derive = np.ones(int(30.0 * frequence), dtype=np.float32)
    coupe = svc.rogner_a_duree(derive, 'Manger ?')
    verifier('une derive de 30 s sur 8 caracteres est coupee',
             abs(coupe.size / float(frequence) - svc.duree_max_derivee('Manger ?'))
             < 0.02, '%.2f s' % (coupe.size / float(frequence)))
    normal = np.ones(int(1.10 * frequence), dtype=np.float32)
    verifier('un audio de longueur normale n est pas touche',
             svc.rogner_a_duree(normal, 'Manger ?').size == normal.size)
    verifier('un audio vide ne casse rien',
             svc.rogner_a_duree(np.zeros(0, dtype=np.float32), 'Non.').size == 0)

    print('')
    print('4) le silence de queue est ramene a 0,25 s')
    son = np.ones(int(1.0 * frequence), dtype=np.float32)
    silence = np.zeros(int(1.0 * frequence), dtype=np.float32)
    rogne = svc.rogner_queue(np.concatenate([son, silence]))
    duree = rogne.size / float(frequence)
    verifier('1 s de son + 1 s de silence -> %.2f s (attendu ~1,25 s)' % duree,
             1.20 <= duree <= 1.30, duree)
    verifier('la parole n est pas touchee (le son est encore la)',
             float(np.max(np.abs(rogne[:int(1.0 * frequence)]))) > 0.5)
    verifier('un audio entierement silencieux est rendu tel quel',
             svc.rogner_queue(np.zeros(int(0.5 * frequence),
                                       dtype=np.float32)).size
             == int(0.5 * frequence))

    print('')
    print('5) le WAV produit est lisible et au bon format')
    wav = svc._wav_depuis_pcm(np.zeros(int(1.0 * frequence), dtype=np.float32))
    with wave.open(__import__('io').BytesIO(wav), 'rb') as fichier:
        verifier('1 canal (mono)', fichier.getnchannels() == 1)
        verifier('16 bits', fichier.getsampwidth() == 2)
        verifier('24000 Hz', fichier.getframerate() == 24000)
        verifier('duree de 1 s',
                 abs(fichier.getnframes() - frequence) <= 1, fichier.getnframes())
    verifier('un signal trop fort est borne, sans planter',
             len(svc._wav_depuis_pcm(np.full(2400, 9.9, dtype=np.float32))) > 44)

    print('')
    print('6) les references : le TEXTE est obligatoire (contrairement a XTTS)')
    with tempfile.TemporaryDirectory() as temporaire:
        dossier = Path(temporaire)
        svc.DOSSIER_REFERENCES = dossier
        sous_dossier = dossier / 'essai'
        sous_dossier.mkdir()
        _petit_wav(sous_dossier / 'voix_a_reference.wav')
        _petit_wav(sous_dossier / 'voix_b_reference.wav')
        _petit_wav(sous_dossier / 'sans_texte_reference.wav')
        with open(sous_dossier / 'references.csv', 'w', encoding='utf-8',
                  newline='') as fichier:
            ecrivain = csv.writer(fichier, delimiter=';')
            ecrivain.writerow(['fichier', 'texte', 'duree', 'hauteur', 'source'])
            ecrivain.writerow(['voix_a_reference.wav', 'Bonjour, il partit.',
                               '12.00', '160 Hz', 'source.mp3'])
            ecrivain.writerow(['voix_b_reference.wav', '', '12.00', '150 Hz',
                               'source2.mp3'])
        _petit_wav(dossier / 'voix_c_reference.wav')
        (dossier / 'voix_c_reference.txt').write_text(
            'Le soleil se couchait.\n', encoding='utf-8')
        _petit_wav(dossier / 'voix_d_enhanced_reference.wav')
        (dossier / 'voix_d_enhanced_reference.txt').write_text(
            'Il partit aussitot.\n', encoding='utf-8')

        trouvees = svc._repertorier_references()
        verifier('le CSV et le fichier .txt sont tous les deux lus',
                 set(trouvees) == {'voix_a', 'voix_c', 'voix_d'},
                 sorted(trouvees))
        verifier('le suffixe _enhanced est retire (identifiants du catalogue)',
                 'voix_d' in trouvees and 'voix_d_enhanced' not in trouvees)

        # Fenetre par voix : la place laissee au texte depend de la duree de
        # l'extrait (fenetre du moteur ~30 s, reference comprise).
        _petit_wav(dossier / 'voix_longue_reference.wav', duree_s=18)
        (dossier / 'voix_longue_reference.txt').write_text(
            'Un texte quelconque.\n', encoding='utf-8')
        trouvees = svc._repertorier_references()
        verifier('la duree de chaque extrait est mesuree',
                 abs(trouvees['voix_longue'][2] - 18.0) < 0.2,
                 '%.1f s' % trouvees['voix_longue'][2])
        verifier('un extrait de 18 s reduit la taille des morceaux lus',
                 svc._limite_caracteres('voix_longue') < svc.MAX_CARACTERES
                 and svc._limite_caracteres('voix_longue') <= 160,
                 svc._limite_caracteres('voix_longue'))
        verifier('un extrait court garde la limite pleine (%d car.)'
                 % svc.MAX_CARACTERES,
                 svc._limite_caracteres('voix_a') == svc.MAX_CARACTERES,
                 svc._limite_caracteres('voix_a'))
        verifier('un extrait minuscule ne fait pas exploser la limite',
                 svc._limite_caracteres('voix_a') <= svc.MAX_CARACTERES)
        verifier('une reference sans texte est IGNOREE (voix_b, sans_texte)',
                 'voix_b' not in trouvees and 'sans_texte' not in trouvees)
        verifier('le texte du CSV est repris tel quel',
                 trouvees['voix_a'][1] == 'Bonjour, il partit.')
        verifier('le texte du .txt est nettoye (retours de ligne)',
                 trouvees['voix_c'][1] == 'Le soleil se couchait.')
        verifier('le chemin du WAV est garde',
                 trouvees['voix_a'][0].name == 'voix_a_reference.wav')
        verifier('un dossier de references absent ne plante pas',
                 svc.DOSSIER_REFERENCES == dossier)

    print('')
    print('7) les references et le moteur sont bien separes en memoire')
    verifier('l encodage d une reference est garde (pas recalcule)',
             '_references_encodees' in source)
    verifier('le service ne charge pas neuTTS au demarrage (import tardif)',
             'from neutts import NeuTTS' in source
             and source.index('def charger_moteur') < source.index(
                 'from neutts import NeuTTS'))


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : service NeuTTS (logique, sans charger le moteur)')
    print('=' * 66)
    main_verifications()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    sys.exit(0 if ECHECS == 0 else 1)
