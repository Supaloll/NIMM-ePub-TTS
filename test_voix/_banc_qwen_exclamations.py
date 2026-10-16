# -*- coding: utf-8 -*-
r"""LES POINTS D'EXCLAMATION SUR LA CARTE : le moteur Qwen Q8_0 en fait-il
ENFIN de vrais points d'exclamation ?

D'OU VIENT CE BANC (04/10/2026). Aujourd'hui, `modules/tts.py` (`_clean_text`,
tout en bas) RETIRE les « ! » avant de donner le texte au moteur :
  - phrase de 25 caracteres ou moins -> VIRGULE (`SEUIL_INTERJECTION`) ;
  - phrase plus longue               -> POINT ;
  - « ?! »                           -> « ? » .
Ce reglage a ete choisi A L'OREILLE le 18/09/2026, avec les moteurs d'ALORS
(Kokoro, Edge) : ils faisaient des « Ahhhh » / « Il partiiiiit » sur le « ! ».
Depuis, le moteur en service est Qwen3-TTS en C++ (qwentts.cpp), sur la carte,
en Q8_0 -- un moteur qui n'a rien a voir. On ne sait PLUS si ce reglage est
encore justifie : c'est ce que ce banc fait ecouter.

CE QUE LE BANC FAIT : il envoie les phrases DIRECTEMENT au moteur, en
contournant COMPLETEMENT `_clean_text` (sinon la regle du « ! » s'appliquerait
et on n'entendrait jamais le « ! »). Pour chaque phrase, SIX variantes (A a F),
la meme voix, sur la carte, 2 tirages chacune.

TROISIEME QUESTION portee par le meme banc : le defaut « Leze » pour « Eh » et
« Nek » pour « Ah » (constat de Laurent, 19/09/2026). Trois suspects, jamais
tranches : (1) le signe de dialogue colle devant ; (2) la virgule a la place du
« ! » ; (3) le texte trop court. Les variantes C/D/E/F servent a les departager.

ECOUTE A L'AVEUGLE : les fichiers portent des NOMS AU HASARD ; la table de
correspondance reste HORS du dossier d'ecoute (la cle). Laurent note sans savoir
ce qu'il ecoute, puis on croise.

GARDE-FOUS (l'essentiel) :
  - REFUSE de partir si le service du moteur repond sur le port 8086 (les deux
    se partageraient la carte, et un REPLI silencieux sur le processeur
    fausserait tout le test : on croirait tester la carte alors qu'on testerait
    le processeur) ;
  - VERIFIE la memoire video LIBRE avant de charger (lecon du 03/10/2026 : un
    jeu ouvert avait affame la carte) et REFUSE si elle est insuffisante ;
  - CONFIRME, apres chargement, que le moteur occupe VRAIMENT la carte (la
    memoire video utilisee doit bondir) : on ne se fie pas a une etiquette.

RIEN N'EST MODIFIE DANS LE PROJET : ni la base, ni les voix, ni le service, ni
les catalogues. Tout s'ecrit dans le dossier de sortie date.

A LANCER AVEC LE PYTHON DU MOTEUR (le lanceur double-clic s'en occupe) :
    qwentts_service\.venv\Scripts\python.exe test_voix\_banc_qwen_exclamations.py
"""
import argparse
import array
import csv
import datetime
import random
import re
import string
import sys
import time
import urllib.error
import urllib.request
import wave
import zipfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(ICI))          # pour _mesurer_debit_qwentts
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

import _mesurer_debit_qwentts as mesure  # noqa: E402

DOSSIER_VOIX = RACINE / 'qwen_tts_service' / 'voix'
MODELS = RACINE / 'qwentts_service' / 'models'
BIBLIOTHEQUE = RACINE / 'data' / 'library'
BASE = RACINE / 'data' / 'nimm_epub.db'

VOIX = '1770_1028_000036-0002'   # le narrateur de 22/11/63 (meme voix que les souffles)
VARIANTE = 'Q8_0'                # la variante EN SERVICE sur la carte
TIRAGES = 2
TEMPERATURE = 0.9
PLAFOND_S = 90.0
PAUSE_S = 0.40

# La carte du poste : RTX 4060, 8188 Mo. Q8_0 prend ~4,7 Go une fois charge.
# On exige une marge : sinon on refuse AVANT de charger (lecon du 03/10/2026).
VRAM_MIN_LIBRE_MO = 5500
VRAM_BOND_MIN_MO = 800           # le bond attendu quand le modele monte sur la carte
PORT_SERVICE = 8086
SERVICE = 'http://127.0.0.1:%d' % PORT_SERVICE

LIVRE_DEFAUT = 28                # 22/11/63 : le livre de la voix
SEUIL_INTERJECTION = 25          # copie de modules/tts.py (regle actuelle du « ! »)


# ==============================================================
# LES PHRASES A TESTER
# ==============================================================

INTERJECTIONS_COURTES = ['Ah !', 'Oh !', 'Eh !', 'Non !']
INTERJECTIONS_LONGUES = ['Bien sûr !', 'Ah bon !', 'Attention !',
                         'Au secours !', 'Silence !', 'Comte !']
PHRASES_ENTIERES = ['Cela recommence, comte !', 'Quel poignet !']

# Deux phrases REELLES de 22/11/63, gardees en secours si le livre ne peut pas
# etre lu au moment du banc (elles portent le vrai « ! » du livre).
PHRASES_LIVRE_SECOURS = [
    'J’avais jamais eu un A+ de toute ma vie !',
    'Jamais compté en avoir un, non plus !',
]


def variantes(base):
    """[(code, libelle, texte)] : la meme phrase en SIX variantes (A a F).

    Le texte rendu est envoye TEL QUEL au moteur (aucun nettoyage du lecteur).
    """
    base = (base or '').replace('\u00a0', ' ').strip()

    def coller(signe):
        texte = re.sub(r'\s*!+', signe, base)
        return re.sub(r'\s{2,}', ' ', texte).strip()

    colle = coller('!')            # A : « Ah! »
    francaise = coller(' !')       # B : « Ah ! » (la typographie francaise)
    return [
        ('A', "« ! » colle (pas d'espace)          ", colle),
        ('B', '« ! » a la francaise                ', francaise),
        ('C', 'virgule (regle actuelle si <= 25 car)', coller(',')),
        ('D', 'point (regle actuelle si > 25 car)  ', coller('.')),
        ('E', 'signe de dialogue devant + « ! »     ', '\u2014 ' + francaise),
        ('F', '« ! » puis la phrase suivante        ',
         francaise + ' Je comprends.'),
    ]


# ==============================================================
# LES PHRASES REELLES DU LIVRE (stdlib pur : l'epub est un zip d'XHTML)
# ==============================================================

def _texte_epub(chemin):
    """Texte brut d'un epub, balises retirees (sans bs4/ebooklib)."""
    morceaux = []
    with zipfile.ZipFile(str(chemin)) as archive:
        for nom in archive.namelist():
            if nom.lower().endswith(('.xhtml', '.html', '.htm')):
                brut = archive.read(nom).decode('utf-8', 'replace')
                morceaux.append(re.sub(r'<[^>]+>', ' ', brut))
    texte = ' '.join(morceaux)
    texte = re.sub(r'&[a-zA-Z]+;|&#\d+;', ' ', texte)   # entites restantes
    texte = texte.replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', texte)


def phrases_du_livre(livre_id, nombre):
    """(titre, [phrases reelles avec « ! »]) -- une COURTE, une plus longue."""
    import sqlite3

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    ligne = conn.execute('SELECT title, filename FROM books WHERE id = ?',
                         (livre_id,)).fetchone()
    conn.close()
    if not ligne:
        return None, []
    titre, fichier = ligne
    chemin = BIBLIOTHEQUE / fichier
    if not chemin.is_file():
        return titre, []
    texte = _texte_epub(chemin)
    phrases = [p.strip() for p in re.split(r'(?<=[.!?])\s+', texte)]
    candidates = sorted({p for p in phrases if '!' in p and 4 <= len(p) <= 130},
                        key=len)
    if not candidates:
        return titre, []
    if len(candidates) <= nombre:
        return titre, candidates
    pas = len(candidates) / float(nombre)
    return titre, [candidates[min(len(candidates) - 1, int(i * pas))]
                   for i in range(nombre)]


# ==============================================================
# GARDE-FOUS ET OUTILLAGE
# ==============================================================

def le_service_repond():
    """Le service du moteur repond-il deja sur son port (donc carte occupee) ?"""
    try:
        with urllib.request.urlopen(SERVICE + '/sante', timeout=3) as reponse:
            return reponse.status == 200
    except Exception:
        return False


def vram():
    """(total, utilise, libre) en Mo, ou None si la carte n'est pas lisible."""
    import subprocess

    try:
        sortie = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.total,memory.used,memory.free',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=20)
        valeurs = [int(v.strip()) for v in sortie.stdout.strip().split(',')]
        if len(valeurs) >= 3:
            return tuple(valeurs[:3])
    except Exception:
        pass
    return None


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


def ouvrir_moteur(variante):
    """Le moteur, ouvert comme le service le fait sur la CARTE (paquet GPU)."""
    talker = MODELS / ('qwen-talker-0.6b-base-%s.gguf' % variante)
    codec = MODELS / ('qwen-tokenizer-12hz-%s.gguf' % variante)
    for chemin in (talker, codec):
        if not chemin.is_file():
            raise FileNotFoundError('GGUF manquant : %s' % chemin)
    from qwentts_cpp import QwenTTS      # le paquet CARTE (jamais _cpu ici)
    return QwenTTS(str(talker), str(codec))


def generer(moteur, texte, spk, codes, texte_reference):
    """Une phrase, avec la TEMPERATURE du banc. Rend (sons, taux, abandon)."""
    import threading

    import numpy as np

    annulation = threading.Event()
    minuteur = threading.Timer(PLAFOND_S, annulation.set)
    minuteur.start()
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
    sons = (np.concatenate(morceaux) if morceaux
            else np.zeros(0, dtype=np.float32))
    return sons, taux, annulation.is_set()


def nom_au_hasard(utilises):
    alphabet = string.ascii_lowercase + string.digits
    while True:
        nom = ''.join(random.choice(alphabet) for _ in range(12))
        if nom not in utilises:
            utilises.add(nom)
            return nom


def assembler(chemins, frequence):
    """Les morceaux recolles en UN passage continu (petites pauses)."""
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


def ecrire_lisez_moi(dossier_ecoute, series, titre_livre, tirages):
    """Le mode d'emploi que Laurent lit AVANT d'ecouter (aucune reponse ici)."""
    lignes = [
        "LES POINTS D'EXCLAMATION SUR LA CARTE  --  moteur Qwen %s" % VARIANTE,
        '=' * 72,
        '',
        'QUESTION : le « ! » est-il enfin lu comme un VRAI point d exclamation ?',
        '',
        "Aujourd'hui, le lecteur RETIRE le « ! » avant de donner le texte au",
        'moteur (virgule si la phrase est courte, point sinon). Ce reglage date',
        "d'un AUTRE moteur (Kokoro, Edge). Ici, la MEME voix lit la MEME phrase",
        'de SIX facons, sur la carte, et les fichiers portent des NOMS AU HASARD :',
        'tu notes sans savoir ce que tu ecoutes.',
        '',
        'CE QUE TU FAIS, POUR CHAQUE DOSSIER PHRASE_NN :',
        '  1. double-clic sur le fichier qui commence par  00_PASSAGE_',
        '     (les six facons a la suite, dans un ordre au hasard) ;',
        '  2. classe-les de la meilleure a la moins bonne (1 a 6) ;',
        '  3. dis-moi celles qui sonnent MAL (par ex. un « Leze » pour « Eh »).',
        '',
        'Tu peux aussi rejouer chaque fichier separement dans le meme dossier.',
        '',
        'LES PHRASES TESTEES (%d phrases, %d tirages chacune) :'
        % (len(series), tirages),
    ]
    for rang, (genre, base) in enumerate(series, 1):
        lignes.append('  PHRASE_%02d   %-28s   %s'
                      % (rang, '« %s »' % base, genre))
    lignes += [
        '',
        'Exemple de reponse a me donner :',
        '  PHRASE_01 : 3, 1, 5, 2, 6, 4        (du meilleur au moins bon)',
        '  PHRASE_01 : la 4 sonne comme « Leze »',
        '',
        'LA CLE (quel fichier est quelle facon) est HORS de ce dossier :',
        "je croiserai tes notes avec elle APRES ton ecoute.",
        '',
        'Rappel : pour l instant, la regle du lecteur donne une VIRGULE sur une',
        'phrase de 25 caracteres ou moins, et un POINT au-dela. C est justement',
        'la question de ce banc.',
    ]
    (dossier_ecoute / 'LISEZ-MOI.txt').write_text('\n'.join(lignes) + '\n',
                                                   encoding='utf-8')


def ecrire_synthese(chemin, passages, lignes, gain):
    """La CLE lisible : A N OUVRIR QU APRES L ECOUTE."""
    texte = [
        "LES POINTS D'EXCLAMATION SUR LA CARTE -- Qwen %s -- %s"
        % (VARIANTE, time.strftime('%d/%m/%Y %H:%M')),
        '=' * 72,
        '',
        "CLE : A N'OUVRIR QU'APRES AVOIR ECOUTE.",
        '',
        'LES PRISES (une ligne par fichier, rangees par phrase) :',
    ]
    for ligne in lignes:
        texte.append('  %s  PHRASE_%02d  [%s] %s  tirage %d  %.2f s  ->  %s'
                     % (ligne['fichier'], ligne['phrase'], ligne['genre'],
                        ligne['code'], ligne['tirage'], ligne['duree'],
                        ligne['texte']))
    texte += ['', "LES PASSAGES (l ordre EXACT de ce que tu as entendu) :"]
    for passage in passages:
        texte.append('')
        texte.append('PHRASE_%02d  %s  (%s)  --  phrase : « %s »'
                     % (passage['numero'], passage['nom'], passage['genre'],
                        passage['base']))
        for position, code in enumerate(passage['ordre'], 1):
            texte.append('     %d)  %s  =  %s'
                         % (position, code, passage['textes'][code]))
    texte += [
        '',
        'Codes : A « ! » colle / B « ! » a la francaise / C virgule /',
        '        D point / E signe de dialogue devant / F suivi d une phrase.',
        'Le gain applique a tous les fichiers est x%.3f (meme niveau pour tous).'
        % gain,
        '',
        'Rien n a ete modifie dans le projet (ni base, ni voix, ni service).',
    ]
    chemin.write_text('\n'.join(texte) + '\n', encoding='utf-8')


# ==============================================================
# LE BANC
# ==============================================================

def main():
    analyseur = argparse.ArgumentParser(
        description="Les points d'exclamation sur la carte : Qwen Q8_0, a "
                    "l'oreille.")
    analyseur.add_argument('--tirages', type=int, default=TIRAGES,
                           help='nombre de tirages par variante (defaut : 2)')
    analyseur.add_argument('--livre', type=int, default=LIVRE_DEFAUT,
                           help='livre ou prendre les phrases reelles (defaut : 28)')
    analyseur.add_argument('--sans-livre', action='store_true',
                           help='ne pas lire de phrases dans le livre')
    options = analyseur.parse_args()

    print('=' * 76)
    print(" LES POINTS D'EXCLAMATION SUR LA CARTE : le moteur Qwen %s" % VARIANTE)
    print('=' * 76)
    print(' voix    : %s' % VOIX)
    print(' phrases : interjections courtes + longues + phrases entieres (+ livre)')
    print('')

    # ---- GARDE-FOU 1 : le service du moteur tourne-t-il deja ? ----
    if le_service_repond():
        print('ARRET : le service du moteur repond deja sur le port %d.'
              % PORT_SERVICE)
        print('  Les deux se partageraient la carte, et un REPLI silencieux sur')
        print('  le processeur fausserait tout le test (on croirait tester la')
        print('  carte alors qu on testerait le processeur).')
        print('  -> FERME NIMM ePub (la fenetre du moteur), puis relance ce banc.')
        return 1
    print(' garde-fou 1 : le service ne repond PAS sur %d   OK' % PORT_SERVICE)

    # ---- GARDE-FOU 2 : la memoire video est-elle suffisante ? ----
    etat = vram()
    if etat is None:
        print('ARRET : impossible de lire la memoire video (nvidia-smi muet).')
        print('  Ce banc REFUSE de partir sans savoir si la carte est libre.')
        return 1
    total, utilise, libre = etat
    print(' garde-fou 2 : memoire video : %d Mo libres sur %d (%d utilises)'
          % (libre, total, utilise))
    if libre < VRAM_MIN_LIBRE_MO:
        print('ARRET : la carte est INSUFFISAMMENT libre pour Q8_0.')
        print('  Il faut au moins %d Mo libres ; il y en a %d.'
              % (VRAM_MIN_LIBRE_MO, libre))
        print('  Un jeu, un navigateur ou un autre moteur occupe la carte :')
        print('  ferme ce qui prend la memoire video, puis relance ce banc.')
        print('  (lecon du 03/10/2026 : un jeu ouvert avait affame la carte).')
        return 1
    print('   -> %d Mo libres : de quoi charger Q8_0 (~4,7 Go).   OK' % libre)
    print('')

    # ---- La voix et son texte de reference ----
    reference = DOSSIER_VOIX / (VOIX + '_enhanced_reference.wav')
    if not reference.is_file():
        reference = DOSSIER_VOIX / (VOIX + '_reference.wav')
    if not reference.is_file():
        print('ARRET : extrait de voix introuvable pour %s' % VOIX)
        return 2
    texte_reference = ''
    with open(DOSSIER_VOIX / 'references.csv', encoding='utf-8-sig',
              newline='') as flux:
        for ligne in csv.reader(flux, delimiter=';'):
            if len(ligne) >= 2 and ligne[0].strip().startswith(VOIX):
                texte_reference = ligne[1].strip()
                break
    if not texte_reference:
        print('ARRET : le texte de reference de %s est introuvable' % VOIX)
        return 2
    print(' voix    : %s  (extrait %s)' % (VOIX, reference.name))

    # ---- Les phrases ----
    series = []
    for base in INTERJECTIONS_COURTES:
        series.append(('interjection courte', base))
    for base in INTERJECTIONS_LONGUES:
        series.append(('interjection longue', base))
    for base in PHRASES_ENTIERES:
        series.append(('phrase exclamative entiere', base))
    if not options.sans_livre:
        titre_livre, reelles = phrases_du_livre(options.livre, 2)
        if not reelles:
            reelles = PHRASES_LIVRE_SECOURS
            genre_livre = 'phrase reelle (livre non lu, secours)'
            print(' (livre %d illisible : phrases reelles de secours)'
                  % options.livre)
        else:
            genre_livre = 'phrase reelle du livre %d' % options.livre
            print(' livre %d lisible : %s' % (options.livre, titre_livre))
        for base in reelles:
            series.append((genre_livre, base))
    print(' phrase(s) a tester : %d' % len(series))

    # ---- Le dossier de sortie (date) ----
    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    lot = ICI / ('ecoute_exclamations_qwen_%s' % horodatage)
    ecoute = lot / 'A_ECOUTER'
    cle = lot / 'CLE_EXCLAMATIONS.csv'
    journal = lot / 'journal.txt'
    synthese = lot / 'SYNTHESE_EXCLAMATIONS.txt'
    for dossier in (lot, ecoute):
        dossier.mkdir(parents=True, exist_ok=True)
    for reste in list(ecoute.glob('*.wav')) + list(ecoute.glob('PHRASE_*')):
        if reste.is_dir():
            for fichier in reste.glob('*.wav'):
                fichier.unlink()
            reste.rmdir()
        else:
            reste.unlink()
    for fichier in (cle, journal, synthese):
        if fichier.is_file():
            fichier.unlink()

    def journaliser(texte=''):
        print(texte, flush=True)
        with open(journal, 'a', encoding='utf-8') as flux:
            flux.write(texte + '\n')

    print('')
    print(' sortie  : %s' % lot.name)

    # ---- Le moteur, sur la CARTE ----
    journaliser('')
    journaliser('chargement du moteur Qwen %s sur la carte...' % VARIANTE)
    avant = vram()
    try:
        moteur = ouvrir_moteur(VARIANTE)
    except Exception as erreur:
        journaliser("ARRET : le moteur n'a pas pu demarrer : %s : %s"
                    % (type(erreur).__name__, erreur))
        journaliser('  (verifie que NIMM ePub est ferme et que la carte est libre)')
        return 3

    # ---- GARDE-FOU 3 : le moteur occupe-t-il VRAIMENT la carte ? ----
    apres = vram()
    if avant and apres:
        bond = apres[1] - avant[1]
        journaliser(' memoire video : %d -> %d Mo (bond %+d Mo)'
                    % (avant[1], apres[1], bond))
        if bond < VRAM_BOND_MIN_MO:
            journaliser('ARRET : le moteur ne semble PAS avoir charge sur la carte')
            journaliser('  (bond de %d Mo, attendu > %d Mo).'
                        % (bond, VRAM_BOND_MIN_MO))
            journaliser('  Ce banc ne teste QUE la carte : on ne continue pas.')
            try:
                moteur.close()
            except Exception:
                pass
            return 3

    empreinte = moteur.extract_voice_ref(mesure._audio_24k(reference))

    utilises = set()
    lignes = []
    passages = []
    for numero, (genre, base) in enumerate(series, 1):
        dossier = ecoute / ('PHRASE_%02d' % numero)
        dossier.mkdir(parents=True, exist_ok=True)
        journaliser('')
        journaliser('PHRASE %02d (%s) : « %s »' % (numero, genre, base))
        prises_t1 = {}
        texte_de = {}
        for code, libelle, texte in variantes(base):
            for tirage in range(1, options.tirages + 1):
                sons, taux, abandon = generer(
                    moteur, texte, empreinte.ref_spk_emb, empreinte.ref_codes,
                    texte_reference)
                nom = nom_au_hasard(utilises) + '.wav'
                chemin = dossier / nom
                ecrire_flottants(sons, taux, chemin)
                duree = (len(sons) / float(taux)) if taux else 0.0
                lignes.append({'fichier': 'PHRASE_%02d/%s' % (numero, nom),
                               'phrase': numero, 'genre': genre, 'code': code,
                               'tirage': tirage, 'duree': duree,
                               'texte': texte})
                if tirage == 1:
                    prises_t1[code] = chemin
                    texte_de[code] = texte
                journaliser('  %s  [%s] %s  tirage %d : %.2f s%s'
                            % (nom, code, libelle.strip(), tirage, duree,
                               '   ABANDON' if abandon else ''))
        # Le passage : les SIX facons (tirage 1) dans un ordre au hasard.
        ordre = list(prises_t1.keys())
        random.shuffle(ordre)
        nom_passage = '00_PASSAGE_%s.wav' % nom_au_hasard(utilises)
        ecrire_wav(assembler([prises_t1[c] for c in ordre], 24000),
                   dossier / nom_passage, 24000)
        passages.append({'numero': numero, 'nom': nom_passage, 'genre': genre,
                         'base': base, 'ordre': ordre,
                         'textes': {c: texte_de[c] for c in ordre}})
        journaliser('  passage %s : ordre %s'
                    % (nom_passage, ' '.join(ordre)))

    try:
        moteur.close()
    except Exception:
        pass

    # ---- Le MEME gain pour tous : sinon le plus fort semblerait le meilleur ----
    fichiers = []
    for dossier in sorted(ecoute.iterdir()):
        if dossier.is_dir():
            fichiers.extend(sorted(dossier.glob('*.wav')))
    pics = []
    for chemin in fichiers:
        donnees, _frequence = lire_wav(chemin)
        pics.append(max(abs(v) for v in donnees) if donnees else 0)
    pic = max(pics) if pics else 0
    gain = 1.0
    if pic:
        gain = (0.90 * 32767.0) / pic
        for chemin in fichiers:
            appliquer_gain(chemin, gain)
    journaliser('')
    journaliser('nivelage : le MEME gain (x%.3f) pour les %d fichiers.'
                % (gain, len(fichiers)))

    # ---- La cle (machine) et la cle (lisible), HORS du dossier d'ecoute ----
    with open(cle, 'w', encoding='utf-8', newline='') as flux:
        graveur = csv.writer(flux, delimiter=';')
        graveur.writerow(['fichier', 'type', 'phrase', 'genre', 'variante',
                          'tirage', 'duree_s', 'texte_envoye'])
        for ligne in lignes:
            graveur.writerow([ligne['fichier'], 'prise', ligne['phrase'],
                              ligne['genre'], ligne['code'], ligne['tirage'],
                              '%.2f' % ligne['duree'], ligne['texte']])
        graveur.writerow([])
        graveur.writerow(['fichier', 'type', 'phrase', 'genre', 'ordre',
                          'variante', 'texte_envoye'])
        for passage in passages:
            chemin = 'PHRASE_%02d/%s' % (passage['numero'], passage['nom'])
            for position, code in enumerate(passage['ordre'], 1):
                graveur.writerow([chemin, 'passage', passage['numero'],
                                  passage['genre'], position, code,
                                  passage['textes'][code]])

    ecrire_lisez_moi(ecoute, series,
                     titre_livre if not options.sans_livre else None,
                     options.tirages)
    ecrire_synthese(synthese, passages, lignes, gain)
    (ICI / '_dernier_banc_exclamations.txt').write_text(str(ecoute),
                                                        encoding='utf-8')

    print('')
    print('=' * 76)
    print(' FINI : %d prises + %d passages' % (len(lignes), len(passages)))
    print('=' * 76)
    print('  a ecouter : %s' % ecoute)
    print('  la cle    : %s   (hors du dossier d ecoute)' % synthese.name)
    print('  memoire video apres le banc : %s' % (vram(),))
    return 0


if __name__ == '__main__':
    sys.exit(main())
