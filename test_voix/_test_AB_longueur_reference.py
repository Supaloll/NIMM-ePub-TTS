# -*- coding: utf-8 -*-
r"""LE TEST A/B DE LA LONGUEUR DE REFERENCE -- meme voix, courte contre longue.

D'OU VIENT CE TEST (03/10/2026). Laurent a remarque que beaucoup de references
font 7-8 secondes et il pense que la qualite des voix vient de la : « je suis sur
que la qualite des voix vient de ca, l'extrait est trop court ». La mesure a
montre que, pour les 35 voix Kyutai, il n'y a PAS de secondes perdues (le depot
`kyutai/tts-voices` ne publie qu'un audio par voix, deja court) -- mais aussi que
le service recoit l'audio ENTIER sans qu'on sache si la bibliotheque C++ interne
le plafonne. Autrement dit : la lecture du code ne peut pas trancher. SEULE
L'OREILLE DE LAURENT PEUT LE DIRE.

CE QUE FAIT L'OUTIL, pour deux voix :
  1. il lit la reference de PRODUCTION de la voix et son texte exact ;
  2. il fabrique DEUX references, coupees EXACTEMENT PAREIL (marge de 150 ms de
     silence a chaque bord, fondu de 20 ms, aucune coupe dans un mot) :
        COURTE = les N premieres phrases (la ou la voix se fait entendre) ;
        LONGUE = la reference entiere ;
  3. il fait dire LA MEME PHRASE aux deux, TROIS fois chacune (la generation a
     une part de hasard : trois tirages evitent de juger sur un coup de chance) ;
  4. il pose les WAV sous des NOMS AU HASARD et laisse la cle HORS du dossier
     d'ecoute : Laurent note chaque fichier sans savoir ce qu'il ecoute.

Ce que le test isole : LA LONGUEUR DE LA REFERENCE, et rien d'autre. Meme voix,
meme enregistrement, meme texte au depart, meme moteur, meme phrase, meme
tirage. Si la reference longue rend une voix meilleure, Laurent l'entendra ; si
les deux se valent, on ne refait que la COUPE (le vrai defaut mesure : 30
references sur 35 coupees au ras d'un mot).

RIEN N'EST MODIFIE DANS LE PROJET : ni la base, ni `qwen_tts_service/voix`, ni
le service, ni les catalogues. L'outil charge ses references de test EN MEMOIRE
(`extract_voice_ref`) et ecrit uniquement dans son dossier de sortie.

Le moteur tourne DANS le processus (`qwentts_cpp_cpu`, sur le processeur) : le
service de la carte, sur le port 8086, n'est ni touche ni arrete. Il faut donc
lancer ce script avec le python du moteur :
    qwentts_service\.venv\Scripts\python.exe test_voix\_test_AB_longueur_reference.py
(le lanceur double-clic s'en occupe).

Usage :
    ...\python.exe test_voix\_test_AB_longueur_reference.py
    ...\python.exe test_voix\_test_AB_longueur_reference.py --tirages 2
    ...\python.exe test_voix\_test_AB_longueur_reference.py --voix Femme001
"""
import argparse
import array
import csv
import random
import re
import statistics
import string
import sys
import time
import wave
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(ICI))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# Le module de mesure porte la lecture des WAV, la generation et les modeles :
# on le reutilise tel quel, pour que le banc et le service ne divergent jamais.
import _mesurer_debit_qwentts as mesure  # noqa: E402

VOIX_PRODUCTION = RACINE / 'qwen_tts_service' / 'voix'
LOT = ICI / 'sortie_test_AB_longueur'
ECOUTE = LOT / 'A_ECOUTER'
REFS = LOT / 'REFERENCES_DE_TEST'
CLE = LOT / 'CLE_TEST_AB.csv'
JOURNAL = LOT / 'journal.txt'
SYNTHESE = LOT / 'SYNTHESE_TEST_AB.txt'

# Les modeles EN SERVICE aujourd'hui (Q4_K_M, choisis a l'oreille le 29/09) :
# le test doit parler avec la meme voix que le lecteur, sinon il ne vaut rien.
MODELE_TALKER = mesure.MODELS / 'qwen-talker-0.6b-base-Q4_K_M.gguf'
MODELE_CODEC = mesure.MODELS / 'qwen-tokenizer-12hz-Q4_K_M.gguf'

FREQUENCE = 24000
MARGE_S = 0.150        # la marge de silence gardee a CHAQUE bord (recette de l'atelier)
FONDU_S = 0.020        # le fondu qui evite le clic sec, aux deux bords
PAUSE_MIN_S = 0.200    # duree minimale d'un silence INTERNE accepte comme pause
SEUIL = 0.01           # -40 dBFS : ce que l'atelier appelle « du son »

# La phrase lue par les deux references : le texte de controle de l'atelier, deja
# utilise pour comparer les 94 voix Kokoro -- donc un point de repere connu.
PHRASE = ("Le soleil se couchait derrière les collines et la vieille cloche de "
          "l'église sonnait doucement dans le soir paisible. Il marchait d'un pas "
          "lent le long de la rivière, songeant aux lettres qu'il n'avait jamais "
          "osé envoyer.")

# (voix, nombre de phrases gardees pour la version COURTE). Deux timbres tres
# differents, et deux contrastes de longueur : Femme001 passe de 1 phrase sur 3 a
# la totalite ; Homme004 de 2 sur 3 a la totalite.
VOIX = [
    ('Femme001', 1),
    ('Homme004', 2),
]
TIRAGES = 3
PLAFOND_GENERATION_S = 180.0


def journaliser(texte=''):
    """Affiche a l'ecran ET ecrit dans le journal du lot."""
    print(texte, flush=True)
    with open(JOURNAL, 'a', encoding='utf-8') as fichier:
        fichier.write(texte + '\n')


def texte_de_la_voix(nom):
    """Le texte de reference d'une voix : lu dans le fichier du service."""
    for fichier in (VOIX_PRODUCTION / 'references.csv',
                    VOIX_PRODUCTION / 'references_privees.csv'):
        if not fichier.is_file():
            continue
        with open(fichier, encoding='utf-8', newline='') as flux:
            for ligne in csv.reader(flux, delimiter=';'):
                if len(ligne) >= 2 and ligne[0].strip() == nom + '_reference.wav':
                    return ligne[1].strip()
    return None


def premieres_phrases(texte, nombre):
    """Les `nombre` premieres phrases (coupees apres . ? ! suivis d'un espace)."""
    morceaux = re.split(r'(?<=[.!?])\s+', texte.strip())
    return ' '.join(morceaux[:nombre]).strip()


def lire_wav(chemin):
    """(echantillons entiers, frequence) d'un WAV mono 16 bits."""
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


def ecrire_flottants(sons, taux, chemin):
    """Les echantillons flottants rendus par le moteur -> un WAV 16 bits."""
    import numpy as np

    entier = np.clip(np.asarray(sons, dtype=np.float32), -1.0, 1.0)
    entier = (entier * 32767.0).astype('<i2')
    with wave.open(str(chemin), 'wb') as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(taux))
        fichier.writeframes(entier.tobytes())


def _tranches(donnees, frequence, seuil=SEUIL):
    """[(debut, fin, silencieux)] par tranches de 10 ms -- le seuil de l'atelier."""
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


def premier_et_dernier_son(donnees, frequence):
    """(premier echantillon audible, premier echantillon APRES le dernier son)."""
    premier = None
    dernier = None
    for debut, fin, silencieux in _tranches(donnees, frequence):
        if not silencieux:
            if premier is None:
                premier = debut
            dernier = fin
    return premier, dernier


def pauses_internes(donnees, frequence):
    """Les silences d'au moins PAUSE_MIN_S situes ENTRE deux sons (donc pas les bords)."""
    premier, dernier = premier_et_dernier_son(donnees, frequence)
    if premier is None:
        return [], None, None
    minimum = int(PAUSE_MIN_S * frequence)
    pauses = []
    courant = None
    for debut, fin, silencieux in _tranches(donnees, frequence):
        if debut < premier or fin > dernier:
            continue
        if silencieux:
            courant = (debut, fin) if courant is None else (courant[0], fin)
        else:
            if courant and courant[1] - courant[0] >= minimum:
                pauses.append(courant)
            courant = None
    if courant and courant[1] - courant[0] >= minimum:
        pauses.append(courant)
    return pauses, premier, dernier


def fenetre(donnees, frequence, premier, fin_son):
    """La reference coupee PROPREMENT : la MEME marge de silence aux deux bords.

    On coupe a `fin_son` -- un echantillon situe APRES le dernier mot (soit la fin
    de la reference, soit le debut d'une pause interne) --, on garde MARGE_S de
    silence, et si l'audio n'en a pas assez (il commence ou finit au ras d'un mot)
    on COMPLETE avec du silence. **Aucun mot n'est coupe** : c'est la regle de
    Laurent, et le defaut mesure (30 references sur 35 coupees au ras).
    """
    marge = int(MARGE_S * frequence)
    debut = int(max(0, premier - marge))
    fin = int(min(len(donnees), fin_son + marge))
    morceau = donnees[debut:fin]
    manque_tete = marge - (premier - debut)
    if manque_tete > 0:
        morceau = array.array('h', [0] * manque_tete) + morceau
    manque_queue = marge - (fin - fin_son)
    if manque_queue > 0:
        morceau = morceau + array.array('h', [0] * manque_queue)
    return morceau


def fondre(morceau, frequence):
    """Un fondu de FONDU_S aux deux bords : evite le clic sec, sans rien couper."""
    nombre = min(int(FONDU_S * frequence), len(morceau) // 2)
    for i in range(nombre):
        facteur = i / float(nombre)
        morceau[i] = int(morceau[i] * facteur)
        rang = len(morceau) - 1 - i
        morceau[rang] = int(morceau[rang] * facteur)
    return morceau


def preparer_references(voix=None):
    """Fabrique la reference COURTE et la reference LONGUE de chaque voix."""
    preparations = []
    for nom, nombre_phrases in (voix or VOIX):
        chemin = VOIX_PRODUCTION / (nom + '_reference.wav')
        if not chemin.is_file():
            print('ARRET : reference introuvable : %s' % chemin)
            return None
        texte_long = texte_de_la_voix(nom)
        if not texte_long:
            print('ARRET : aucun texte pour %s dans references.csv' % nom)
            return None
        texte_court = premieres_phrases(texte_long, nombre_phrases)
        if len(texte_court) >= len(texte_long) - 5:
            print('ARRET : %s n a pas assez de phrases pour faire une version '
                  'courte' % nom)
            return None
        donnees, frequence = lire_wav(chemin)
        if frequence != FREQUENCE:
            print('ARRET : %s est en %d Hz (le moteur attend 24 000)'
                  % (nom, frequence))
            return None
        pauses, premier, dernier = pauses_internes(donnees, frequence)
        if premier is None:
            print('ARRET : aucun son audible dans %s' % chemin)
            return None
        if not pauses:
            print('ARRET : aucune pause interne dans %s' % chemin)
            return None
        # OU COUPER LA VERSION COURTE ? La part du texte court dans le texte long
        # donne la position attendue ; on prend la pause interne la PLUS PROCHE.
        attendu = premier + (dernier - premier) * (len(texte_court)
                                                  / float(len(texte_long)))
        pause = min(pauses, key=lambda p: abs(p[0] - attendu))
        ecart = abs(pause[0] - attendu) / float(len(donnees))
        if ecart > 0.15:
            print('ARRET : %s -- la pause la plus proche de la fin de la phrase '
                  'est a %.0f %% de l audio : on ne saurait pas couper sans '
                  'risquer de trancher un mot.' % (nom, ecart * 100))
            return None

        long_audio = fondre(fenetre(donnees, frequence, premier, dernier), frequence)
        court_audio = fondre(fenetre(donnees, frequence, premier, pause[0]), frequence)

        journaliser('')
        journaliser('%s -- reference de production : %.2f s, %d mots'
                    % (nom, len(donnees) / float(frequence),
                       len(texte_long.split())))
        journaliser('  coupe de la version COURTE : la pause interne la plus proche '
                    'de la fin des %d premiere(s) phrase(s)' % nombre_phrases)
        journaliser('    (attendue a %.2f s, pause trouvee a %.2f s, ecart %.1f %% '
                    'de l audio)'
                    % ((attendu - premier) / float(frequence),
                       (pause[0] - premier) / float(frequence), ecart * 100))
        for etiquette, audio, texte in (('court', court_audio, texte_court),
                                        ('long', long_audio, texte_long)):
            fichier = '%s_%s_reference.wav' % (nom, etiquette)
            ecrire_wav(audio, REFS / fichier)
            preparations.append({
                'voix': nom,
                'etiquette': etiquette,
                'fichier': fichier,
                'texte': texte,
                'secondes': len(audio) / float(frequence),
                'mots': len(texte.split()),
                'chemin': REFS / fichier,
            })
            journaliser('  %-5s : %5.2f s de reference, %3d mots de texte -> %s'
                        % (etiquette, len(audio) / float(frequence),
                           len(texte.split()), fichier))
    return preparations


def nom_au_hasard(utilises):
    """Un nom de 16 caracteres : la convention des lots d'ecoute aveugle."""
    alphabet = string.ascii_lowercase + string.digits
    while True:
        nom = ''.join(random.choice(alphabet) for _ in range(16))
        if nom not in utilises:
            utilises.add(nom)
            return nom


def appliquer_gain(chemin, gain):
    """Le meme gain a tous les fichiers : c'est ce qui rend l'A/B honnete."""
    donnees, frequence = lire_wav(chemin)
    for i in range(len(donnees)):
        valeur = int(donnees[i] * gain)
        if valeur > 32767:
            valeur = 32767
        elif valeur < -32768:
            valeur = -32768
        donnees[i] = valeur
    ecrire_wav(donnees, chemin, frequence)


def generer(preparations, tirages):
    """Fait dire LA MEME PHRASE a chaque reference, `tirages` fois."""
    from qwentts_cpp_cpu import QwenTTS

    journaliser('')
    journaliser('chargement du moteur (Q4_K_M, sur le processeur) -- le service de '
                'la carte, lui, n est pas touche...')
    debut = time.perf_counter()
    moteur = QwenTTS(str(MODELE_TALKER), str(MODELE_CODEC),
                     cpu_threads=6, cpu_codec_threads=4, cpu_stream_frames=2)
    journaliser('  moteur charge en %.1f s' % (time.perf_counter() - debut))

    utilises = set()
    lignes = []
    ecoutes = []
    for fiche in preparations:
        debut = time.perf_counter()
        reference = moteur.extract_voice_ref(mesure._audio_24k(fiche['chemin']))
        journaliser('')
        journaliser('%s / %s : empreinte de la voix prete en %.1f s'
                    % (fiche['voix'], fiche['etiquette'],
                       time.perf_counter() - debut))
        for tirage in range(1, tirages + 1):
            sons, taux, calcul, premier_son, note = mesure._generer_flux(
                moteur, PHRASE, reference.ref_spk_emb, reference.ref_codes,
                fiche['texte'], PLAFOND_GENERATION_S)
            nom = nom_au_hasard(utilises) + '.wav'
            chemin = ECOUTE / nom
            ecrire_flottants(sons, taux, chemin)
            duree = (len(sons) / float(taux)) if taux else 0.0
            ecoutes.append(chemin)
            lignes.append({'fichier': nom, 'voix': fiche['voix'],
                           'reference': fiche['etiquette'], 'tirage': tirage,
                           'secondes': duree, 'calcul_s': calcul,
                           'premier_son_s': premier_son, 'note': note})
            journaliser('  tirage %d : %.2f s d audio en %.1f s de calcul (%s)'
                        % (tirage, duree, calcul, note or 'OK'))
        del reference

    # LE MEME GAIN POUR TOUT LE LOT : sans cela, une reference un peu plus forte
    # ferait croire a une voix meilleure -- et le test ne voudrait plus rien dire.
    pics = []
    for chemin in ecoutes:
        donnees, _frequence = lire_wav(chemin)
        pics.append(max(abs(v) for v in donnees) if donnees else 0)
    pic = max(pics) if pics else 0
    if pic:
        gain = (0.90 * 32767.0) / pic
        for chemin in ecoutes:
            appliquer_gain(chemin, gain)
        journaliser('')
        journaliser('nivelage : le MEME gain (x%.3f) pour les %d fichiers, donc '
                    'aucun avantage de volume.' % (gain, len(ecoutes)))

    with open(CLE, 'w', encoding='utf-8', newline='') as fichier:
        graveur = csv.writer(fichier, delimiter=';')
        graveur.writerow(['fichier', 'voix', 'reference', 'tirage', 'secondes',
                          'calcul_s', 'premier_son_s', 'note'])
        for ligne in lignes:
            graveur.writerow([ligne['fichier'], ligne['voix'],
                              ligne['reference'], ligne['tirage'],
                              '%.2f' % ligne['secondes'],
                              '%.1f' % ligne['calcul_s'],
                              '%.2f' % ligne['premier_son_s'], ligne['note']])
    try:
        moteur.close()
    except Exception:
        pass
    return lignes


def ecrire_lisez_moi(lignes):
    """La feuille d'ecoute : des noms au hasard, une note a donner."""
    ordre = [ligne['fichier'] for ligne in lignes]
    random.shuffle(ordre)
    texte = [
        'LE TEST A/B DE LA LONGUEUR DES REFERENCES -- %d fichiers a ecouter'
        % len(ordre),
        '=' * 78,
        '',
        'QUESTION : une reference de voix PLUS LONGUE donne-t-elle une voix',
        'MEILLEURE ? Ici, la MEME voix lit la MEME phrase avec deux references',
        "coupees EXACTEMENT pareil : l'une COURTE, l'autre LONGUE. Rien d'autre ne",
        'change. Personne ne sait laquelle est laquelle -- c est fait expres.',
        '',
        'CE QU ON TE DEMANDE : une note de 1 a 5 pour chaque fichier',
        '    1 = mauvaise   2 = moyenne   3 = bien   4 = tres bien   5 = excellente',
        'et, si tu entends un defaut, lequel.',
        '',
        'FICHIER (nom au hasard)   | NOTE 1-5 | un defaut ?  (rien / parasite debut /',
        '                                                      parasite fin / autre)',
        '-' * 78,
    ]
    for nom in ordre:
        texte.append('%-25s | ........ | ........................................'
                     % nom)
    texte += [
        '-' * 78,
        '',
        'Tu peux remplir ici, dans Notepad. Quand tu as fini, dis-le : je',
        'croiserai tes notes avec la CLE, qui est HORS de ce dossier.',
        '',
        'A SAVOIR : il y a 3 tirages par reference, dans un ordre melange. Une voix',
        'peut donc sortir deux fois tres bien et une fois moins bien : c est le',
        'hasard du moteur, pas la reference.',
        '',
        'LES REFERENCES ELLES-MEMES sont dans le dossier voisin',
        "`REFERENCES_DE_TEST`. Ne les ecoute QU'APRES avoir note : leur longueur",
        'te dirait laquelle est laquelle.',
    ]
    (ECOUTE / 'LISEZ-MOI.txt').write_text('\n'.join(texte) + '\n',
                                          encoding='utf-8')


def ecrire_synthese(preparations, lignes):
    """Le recapitulatif chiffre : ce qui a ete fabrique, et comment."""
    texte = [
        'TEST A/B DE LA LONGUEUR DES REFERENCES -- %s'
        % time.strftime('%d/%m/%Y %H:%M'),
        '=' * 78,
        '',
        'CE QUE LE TEST ISOLE : la LONGUEUR de la reference, et RIEN d autre.',
        'Meme voix, meme enregistrement de depart, meme texte, meme moteur',
        '(Q4_K_M sur le processeur), meme phrase, memes tirages.',
        'Les deux references sont coupees AVEC LA MEME RECETTE : une marge de',
        '150 ms de silence a chaque bord (completee si l audio n en a pas) et un',
        'fondu de 20 ms. AUCUN MOT N EST COUPE.',
        '',
        'LES REFERENCES FABRIQUEES',
        '-' * 78,
    ]
    for fiche in preparations:
        texte.append('  %-10s %-6s %6.2f s  %3d mots  %s'
                     % (fiche['voix'], fiche['etiquette'], fiche['secondes'],
                        fiche['mots'], fiche['fichier']))
    texte += ['', 'LES %d FICHIERS D ECOUTE' % len(lignes), '-' * 78]
    for nom_voix in sorted(set(ligne['voix'] for ligne in lignes)):
        for etiquette in ('court', 'long'):
            morceaux = [ligne for ligne in lignes
                        if ligne['voix'] == nom_voix
                        and ligne['reference'] == etiquette]
            if not morceaux:
                continue
            durees = [m['secondes'] for m in morceaux]
            texte.append('  %-10s reference %-5s : %d tirage(s), %.2f a %.2f s '
                         'd audio' % (nom_voix, etiquette, len(morceaux),
                                      min(durees), max(durees)))
            anormaux = [m for m in morceaux if m['note']]
            if anormaux:
                texte.append('      ATTENTION : %d tirage(s) marque(s) %s'
                             % (len(anormaux),
                                ', '.join(sorted(set(m['note']
                                                     for m in anormaux)))))
    texte += [
        '',
        'LA CLE (a lire APRES l ecoute) : %s' % CLE,
        '   colonnes : fichier ; voix ; reference (court/long) ; tirage ; duree ;',
        '   secondes de calcul ; premier son ; note du banc',
        '',
        'SI LES NOTES SONT LES MEMES des deux cotes : la longueur ne change rien.',
        'On ne refait alors que la COUPE (le vrai defaut mesure : 30 references',
        'sur 35 coupees au ras d un mot).',
        'SI LA REFERENCE LONGUE GAGNE : Laurent avait raison, et on repart des',
        'enregistrements complets du corpus pour refaire les 35 references.',
    ]
    SYNTHESE.write_text('\n'.join(texte) + '\n', encoding='utf-8')


def main():
    analyseur = argparse.ArgumentParser(
        description='Test A/B : la longueur de la reference change-t-elle la voix ?')
    analyseur.add_argument('--tirages', type=int, default=TIRAGES,
                           help='tirages par reference (defaut %d)' % TIRAGES)
    analyseur.add_argument('--voix', default='',
                           help='limiter a certaines voix (separees par une virgule)')
    options = analyseur.parse_args()

    for modele in (MODELE_TALKER, MODELE_CODEC):
        if not modele.is_file():
            print('ARRET : modele introuvable : %s' % modele)
            return 2

    voix = VOIX
    if options.voix:
        demandees = [morceau.strip() for morceau in options.voix.split(',')
                     if morceau.strip()]
        voix = [item for item in VOIX if item[0] in demandees]
        if not voix:
            print('ARRET : voix inconnue (%s). Connues : %s'
                  % (options.voix, ', '.join(item[0] for item in VOIX)))
            return 2
    if options.tirages < 1:
        print('ARRET : --tirages doit valoir au moins 1.')
        return 2

    for dossier in (LOT, ECOUTE, REFS):
        dossier.mkdir(parents=True, exist_ok=True)
    for reste in list(ECOUTE.glob('*.wav')) + list(REFS.glob('*.wav')):
        reste.unlink()
    for fichier in (CLE, JOURNAL, SYNTHESE):
        if fichier.is_file():
            fichier.unlink()

    print('=' * 78)
    print(' TEST A/B -- LA LONGUEUR DE LA REFERENCE CHANGE-T-ELLE LA VOIX ?')
    print('=' * 78)
    print(' voix    : %s' % ', '.join(item[0] for item in voix))
    print(' tirages : %d par reference' % options.tirages)
    print(' sortie  : %s' % LOT)
    print('')
    print(' RIEN n est modifie dans le projet : ni la base, ni les voix du')
    print(' service, ni les catalogues. Les references de test sont chargees EN')
    print(' MEMOIRE, et tout s ecrit dans le dossier de sortie.')
    print('')

    preparations = preparer_references(voix)
    if not preparations:
        return 1
    lignes = generer(preparations, options.tirages)
    ecrire_lisez_moi(lignes)
    ecrire_synthese(preparations, lignes)

    print('')
    print('=' * 78)
    print(' FINI : %d fichiers a ecouter' % len(lignes))
    print('=' * 78)
    print('  a ecouter : %s' % ECOUTE)
    print('  feuille   : %s' % (ECOUTE / 'LISEZ-MOI.txt'))
    print('  synthese  : %s' % SYNTHESE)
    print('  la cle    : %s   (hors du dossier d ecoute)' % CLE)
    print('')
    print('  Dis-moi tes notes, et je croise avec la cle.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
