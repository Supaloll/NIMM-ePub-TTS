# -*- coding: utf-8 -*-
r"""LA PONCTUATION DU LIVRE, DONNEE TELLE QUELLE A QWEN -- 23/10/2026.

D'OU VIENT CE BANC. Laurent ecoutait « Dialogues desaccordes » et a entendu,
dans un seul passage :

    « Il existe bien des facons valables d'y repondre, au nombre desquelles je
      ne classerai pas celle que tu proposes dans Comprendre l'Empire[,] :
      « Une verite officielle ... tellement intenable -[respiration] avec
      notamment ... dont la tour n° 7 tombee sans le moindre avion,[POINT] et
      l'avion tout aussi introuvable du Pentagone. »

Deux choses, a cet endroit :
  - le DEUX-POINTS est devenu une VIRGULE -> c'est `_clean_text`
    (`modules/tts.py`), regle du 17/09/2026, du temps d'Edge et Kokoro ;
  - la VIRGULE avant « et l'avion » est tombee comme une FIN DE PHRASE ->
    suspect n° 1 : la regle « virgule finale -> point » du meme `_clean_text` ;
    suspect n° 2 : le moteur lui-meme (Qwen 0.6B) ; suspect n° 3 : le garde-fou
    de derive du service, qui coupe une phrase en deux et recolle avec 0,10 s.

CE QUE LE BANC FAIT : il envoie le passage AU SERVICE QWEN DEJA ALLUME
(port 8086, celui de la carte), en plusieurs variantes, et ecrit un lot
d'ecoute pret a entendre. AUCUN texte n'est invente : chaque variante est
ecrite dans `index_ecoute.txt`, avec la ou les requetes reellement envoyees.

LES VARIANTES (une par fichier) :
  A  le texte d'AUJOURD'HUI (deux-points -> virgule), 2 tirages
  B  la ponctuation DU LIVRE (`ponctuation_libre=True`), 2 tirages
  C  B, mais guillemets « » retires (le moteur les prononce-t-il ?)
  D  B, mais coupe au DEUX-POINTS en deux requetes (0,60 s entre les deux)
  E  l'extrait court (la fin de la phrase), ponctuation du livre
  F  le meme extrait court avec un VRAI point a la place de la virgule
     (point de repere : c'est le son d'une fin de phrase, pour comparer)

POURQUOI DEUX TIRAGES pour A et B : le moteur est a temperature 0,9, donc deux
tirages du MEME texte ne sonnent pas pareil. Laurent a dit « parfois » : si le
defaut n'apparait qu'a un tirage sur deux, c'est le moteur, pas nos regles.

GARDE-FOUS :
  - REFUSE de partir si le service ne repond pas sur le port 8086, ou s'il
    n'est pas pret, ou s'il a REPLIE sur le processeur (on croirait tester la
    carte) ;
  - RIEN N'EST MODIFIE : ni la base, ni les voix, ni le service, ni les
    catalogues. Tout s'ecrit dans un dossier de lot date, dans `test_voix/` ;
  - le cache du lecteur n'est PAS touche : le banc parle au service, pas a
    `synthesize_qwen`.

POUR ECOUTER : glisser le dossier du lot sur
`test_voix\OUVRIR_UN_LOT_POUR_ECOUTER.bat` (il recolle les tirages de chaque
nom dans l'ordre et ouvre le dossier).

A LANCER AVEC LE PYTHON DU LECTEUR (aucune dependance en plus) :
    python test_voix\_banc_qwen_ponctuation.py
    python test_voix\_banc_qwen_ponctuation.py --voix Soral --tirages 1
"""

import argparse
import datetime
import io
import json
import re
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

from modules import audio_gain, audio_queue        # noqa: E402
from modules.tts import _clean_text               # noqa: E402

PORT_SERVICE = 8086
SERVICE = 'http://127.0.0.1:%d' % PORT_SERVICE
DELAI_S = 600.0

# La voix du passage. Naulleau est celui qui parle : il repond a Soral, dont
# il cite « Comprendre l'Empire ». --voix accepte n'importe quel identifiant du
# service (Soral, Gus, fm_narrateur...).
VOIX_DEFAUT = 'Naulleau'

# Deux tirages sur A et B : le moteur est stochastique (temperature 0,9).
TIRAGES_DEFAUT = 2

# La pause que le lecteur met entre deux paragraphes (frontend/app.js).
PAUSE_REQUETES_S = 0.60

# LE PASSAGE, tel qu'il est dans le livre (apostrophes typographiques).
PASSAGE = (
    'Il existe bien des façons valables d’y répondre, au nombre desquelles je '
    'ne classerai pas celle que tu proposes dans Comprendre l’Empire : « Une '
    'vérité officielle sur les attentats du 11 septembre tellement intenable - '
    'avec notamment les questions troublantes de l’écroulement des trois tours '
    'du WTC, dont la tour n° 7 tombée sans le moindre avion, et l’avion tout '
    'aussi introuvable du Pentagone. »'
)

# La fin de la phrase seule : c'est la qu'on a entendu la virgule « tomber ».
EXTRAIT = ('dont la tour n° 7 tombée sans le moindre avion, et l’avion tout '
           'aussi introuvable du Pentagone.')


# ==============================================================
# LE SERVICE (lecture seule : on lui parle, on ne le modifie pas)
# ==============================================================

def _sante():
    """L'etat du service. Refuse tout si la carte n'est pas celle qui travaille."""
    try:
        with urllib.request.urlopen(SERVICE + '/sante', timeout=15) as reponse:
            etat = json.loads(reponse.read().decode('utf-8'))
    except (urllib.error.URLError, OSError) as erreur:
        raise SystemExit(
            '\n  Le service Qwen ne repond pas sur le port %d (%s).\n'
            '  Double-clique sur qwentts_service\\DEMARRER_QWENTTS_CPP_GPU.bat,\n'
            '  puis relance ce banc.\n' % (PORT_SERVICE, type(erreur).__name__))
    if not etat.get('pret'):
        raise SystemExit('\n  Le service repond, mais le moteur charge encore. '
                         'Attends la fin du chargement.\n')
    if 'carte' not in str(etat.get('appareil', '')).lower():
        raise SystemExit(
            '\n  Le moteur tourne sur « %s », pas sur la carte : le banc refuse\n'
            '  (on croirait tester la carte graphique). Relance le service avec\n'
            '  DEMARRER_QWENTTS_CPP_GPU.bat.\n' % etat.get('appareil'))
    return etat


def _demander(texte, voix):
    """Une requete au moteur. Renvoie (octets WAV, etiquettes du service)."""
    donnees = json.dumps({'texte': texte, 'voix': voix}).encode('utf-8')
    requete = urllib.request.Request(
        SERVICE + '/tts', data=donnees,
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(requete, timeout=DELAI_S) as reponse:
            return reponse.read(), (reponse.headers.get('X-NIMM-Etiquettes') or '')
    except urllib.error.HTTPError as erreur:
        detail = ''
        try:
            detail = (json.loads(erreur.read().decode('utf-8')) or {}).get('erreur', '')
        except Exception:
            pass
        raise SystemExit('\n  Le moteur a refuse une requete (code %d%s).\n'
                         % (erreur.code, (' : ' + detail) if detail else ''))


def _post_traiter(wav):
    """La chaine du lecteur, sauf vitesse et hauteur (neutres dans ce banc).

    Meme ordre que `synthesize_qwen` : queue rognee, niveau ramene dans la
    fourchette, fondu d'entree. C'est ce que Laurent entend dans le lecteur.
    """
    wav = audio_queue.rogner_queue_wav(wav)
    wav = audio_gain.normaliser_wav_parole(wav)
    return audio_gain.fondu_entree_wav(wav)


def _coller(prises, pause_s=PAUSE_REQUETES_S):
    """Recolle des WAV (meme format) avec `pause_s` de silence entre eux."""
    with wave.open(io.BytesIO(prises[0]), 'rb') as premier:
        canaux = premier.getnchannels()
        largeur = premier.getsampwidth()
        taux = premier.getframerate()
    silence = b'\x00' * int(taux * pause_s) * canaux * largeur
    flux = io.BytesIO()
    with wave.open(flux, 'wb') as sortie:
        sortie.setnchannels(canaux)
        sortie.setsampwidth(largeur)
        sortie.setframerate(taux)
        for index, octets in enumerate(prises):
            if index:
                sortie.writeframes(silence)
            with wave.open(io.BytesIO(octets), 'rb') as prise:
                sortie.writeframes(prise.readframes(prise.getnframes()))
    return flux.getvalue()


def _duree(wav):
    with wave.open(io.BytesIO(wav), 'rb') as lecture:
        return lecture.getnframes() / float(lecture.getframerate() or 1)


# ==============================================================
# LES VARIANTES
# ==============================================================

# ==============================================================
# ECRITURE DU LOT
# ==============================================================

def _ecrire_notice(dossier, voix, etat, lignes):
    """LISEZ-MOI.txt : ce qu'on ecoute, et quoi ecouter DEDANS."""
    texte = '\n'.join([
        "LOT D'ECOUTE -- LA PONCTUATION DONNEE TELLE QUELLE A QWEN",
        '=' * 74,
        '',
        'Fait le %s' % datetime.datetime.now().strftime('%d/%m/%Y a %H:%M'),
        'Moteur : %s -- %s -- variante %s'
        % (etat.get('moteur'), etat.get('appareil'), etat.get('variante')),
        'Voix   : %s' % voix,
        '',
        "LE PASSAGE (tel qu'il est dans le livre) :",
        '',
        PASSAGE,
        '',
        '-' * 74,
        'CE QUE TU AS ENTENDU, ET CE QUE CE LOT ESSAIE DE DEPARTAGER',
        '-' * 74,
        '',
        "  1. le DEUX-POINTS apres « Comprendre l'Empire » sort en VIRGULE.",
        "     -> c'est une regle du lecteur (17/09/2026), du temps d'Edge et",
        '        Kokoro. Les variantes B/C/D/E lui donnent le vrai deux-points.',
        '',
        '  2. la VIRGULE avant « et l\'avion » tombe comme une FIN DE PHRASE.',
        '     -> trois suspects : (a) la regle « virgule finale -> point » du',
        '        lecteur ; (b) le moteur lui-meme ; (c) le garde-fou du service,',
        '        qui coupe une phrase trop longue en deux.',
        "        A et B sont tires DEUX FOIS chacun : si le defaut ne sort qu'une",
        '        fois sur deux, c\'est le moteur (temperature 0,9), pas nos regles.',
        '',
        '  3. le tiret « - » au milieu fait une respiration. Il est identique',
        '     dans toutes les variantes : on ne cherche pas a le changer ici.',
        '',
        '-' * 74,
        'LES FICHIERS',
        '-' * 74,
        '',
    ])
    texte += '\n'.join(lignes)
    texte += '\n' + '\n'.join([
        '',
        '-' * 74,
        'COMMENT ECOUTER',
        '-' * 74,
        '',
        "Glisse ce dossier sur  test_voix\\OUVRIR_UN_LOT_POUR_ECOUTER.bat :",
        "il recolle les tirages de chaque nom dans l'ordre et ouvre le dossier.",
        '',
        "Tu peux aussi ouvrir les fichiers un par un. Les prises d'origine ne",
        'sont jamais modifiees : le recollage se fait dans un sous-dossier.',
        '',
    ])
    (dossier / 'LISEZ-MOI.txt').write_text(texte, encoding='utf-8')


def _ecrire_index(dossier, entrees, resultats):
    """index_ecoute.txt : un bloc par variante, avec le texte envoye et ta place."""
    lignes = [
        "INDEX D'ECOUTE -- a remplir par Laurent",
        '=' * 74,
        '',
        'Sous chaque bloc, ecris ce que tu entends : « le deux-points sonne',
        "comme une virgule », « la virgule tombe », « c'est bon », etc.",
        '',
    ]
    for entree in entrees:
        numero, nom, etiquette, textes, note = entree
        lignes.append('-' * 74)
        lignes.append('[%02d] %s -- %s' % (numero, nom, etiquette.replace('_', ' ')))
        lignes.append('     %s' % note)
        lignes.append('')
        lignes.append('     texte(s) envoye(s) au moteur :')
        for index, texte in enumerate(textes, 1):
            prefixe = '       requete %d : ' % index if len(textes) > 1 else '       '
            lignes.append(prefixe + '« ' + texte + ' »')
        lignes.append('')
        for nom_fichier, duree, etiquettes in resultats.get(numero, []):
            lignes.append('     %-46s %5.1f s  %s'
                          % (nom_fichier, duree,
                             ('[' + etiquettes + ']') if etiquettes else ''))
        lignes.append('')
        lignes.append('     ton verdict : ..................................................')
        lignes.append('                   ..................................................')
        lignes.append('')
    (dossier / 'index_ecoute.txt').write_text('\n'.join(lignes), encoding='utf-8')


# ==============================================================
# LES VARIANTES
# ==============================================================

def variantes():
    """[(numero, nom, etiquette, [textes envoyes], note)] -- dans l'ordre d'ecoute.

    Chaque entree porte la ou les requetes REELLEMENT envoyees au moteur : le
    lot d'ecoute les recopie dans `index_ecoute.txt`, rien n'est suppose.
    """
    aujourdhui = _clean_text(PASSAGE)
    livre = _clean_text(PASSAGE, ponctuation_libre=True)
    sans_guillemets = re.sub(r'\s{2,}', ' ',
                             livre.replace('«', ' ').replace('»', ' ')).strip()
    # Coupe au DEUX-POINTS : deux requetes, comme le lecteur le fait quand il
    # separe un beat de narration d'une replique.
    morceaux = re.split(r'(?<=:) ', livre, maxsplit=1)
    if len(morceaux) != 2:
        morceaux = [livre]
    extrait_livre = _clean_text(EXTRAIT, ponctuation_libre=True)
    # Le POINT DE REPERE : la meme phrase, mais avec un VRAI point la ou le
    # livre a une virgule. Si l'extrait « livre » sonne comme ceci, c'est que
    # le moteur traite la virgule comme une fin de phrase.
    extrait_point = _clean_text(
        EXTRAIT.replace(', et l’avion', '. Et l’avion'),
        ponctuation_libre=True)

    return [
        (1, 'le_passage', 'A_aujourdhui', [aujourdhui],
         "le texte d'AUJOURD'HUI : le deux-points est change en virgule, comme "
         "dans le lecteur"),
        (2, 'le_passage', 'B_ponctuation_du_livre', [livre],
         'la ponctuation DU LIVRE : deux-points, virgules, tiret et guillemets '
         'tels quels'),
        (3, 'le_passage', 'C_livre_sans_guillemets', [sans_guillemets],
         'B, mais guillemets « » retires : le moteur les prononce-t-il ?'),
        (4, 'le_passage', 'D_livre_deux_requetes', list(morceaux),
         'B, mais coupe au DEUX-POINTS en deux requetes (0,60 s entre les deux, '
         'la pause du lecteur entre deux paragraphes)'),
        (5, 'extrait_court', 'E_livre', [extrait_livre],
         "la fin de la phrase seule, ponctuation du livre : la virgule avant "
         "« et l'avion » tombe-t-elle encore ?"),
        (6, 'extrait_court', 'F_point_de_repere', [extrait_point],
         "la MEME fin de phrase avec un VRAI point a la place de la virgule : "
         "c'est le son d'une fin de phrase, pour comparer"),
    ]


# ==============================================================
# PROGRAMME
# ==============================================================

def main():
    analyseur = argparse.ArgumentParser(
        description='Donner a Qwen la ponctuation du livre, et ecouter.')
    analyseur.add_argument('--voix', default=VOIX_DEFAUT,
                           help='identifiant de voix du service (defaut : %s)'
                                % VOIX_DEFAUT)
    analyseur.add_argument('--tirages', type=int, default=TIRAGES_DEFAUT,
                           help='tirages par variante (defaut : %d)'
                                % TIRAGES_DEFAUT)
    analyseur.add_argument('--dossier', default='',
                           help='dossier de lot (defaut : un dossier date)')
    options = analyseur.parse_args()

    etat = _sante()
    entrees = variantes()
    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = Path(options.dossier) if options.dossier else (
        ICI / ('ecoute_ponctuation_libre_' + horodatage))
    dossier.mkdir(parents=True, exist_ok=True)

    print('')
    print('=' * 74)
    print('LA PONCTUATION DU LIVRE, DONNEE TELLE QUELLE A QWEN')
    print('=' * 74)
    print('  moteur : %s -- %s -- %s'
          % (etat.get('moteur'), etat.get('appareil'), etat.get('variante')))
    print('  voix   : %s' % options.voix)
    print('  lot    : %s' % dossier)
    print('')

    resultats = {}
    lignes_notice = []
    for numero, nom, etiquette, textes, note in entrees:
        tirages = options.tirages if etiquette[:1] in ('A', 'B') else 1
        lignes_notice.append('  %02d  %-22s %s' % (numero, etiquette, note))
        for tirage in range(1, tirages + 1):
            prises = []
            etiquettes = []
            for texte in textes:
                wav, marques = _demander(texte, options.voix)
                prises.append(_post_traiter(wav))
                if marques:
                    etiquettes.append(marques)
            audio = prises[0] if len(prises) == 1 else _coller(prises)
            nom_fichier = '%02d_%s__%d_%s.wav' % (numero, nom, tirage, etiquette)
            (dossier / nom_fichier).write_bytes(audio)
            resultats.setdefault(numero, []).append(
                (nom_fichier, _duree(audio), ' '.join(etiquettes)))
            print('  %-46s %5.1f s  %s'
                  % (nom_fichier, _duree(audio),
                     ('[' + ' '.join(etiquettes) + ']') if etiquettes else ''))
            lignes_notice.append('      %s : %5.1f s%s'
                                 % (nom_fichier, _duree(audio),
                                    ('  [%s]' % ' '.join(etiquettes))
                                    if etiquettes else ''))

    _ecrire_notice(dossier, options.voix, etat, lignes_notice)
    _ecrire_index(dossier, entrees, resultats)
    (ICI / '_dernier_lot_ponctuation.txt').write_text(str(dossier), encoding='utf-8')

    print('')
    print('=' * 74)
    print("C'EST PRET")
    print('=' * 74)
    print('  %d fichiers dans : %s' % (
        sum(len(liste) for liste in resultats.values()), dossier))
    print('')
    print('  A FAIRE MAINTENANT :')
    print('    - glisser ce dossier sur test_voix\\OUVRIR_UN_LOT_POUR_ECOUTER.bat')
    print('    - remplir index_ecoute.txt (un verdict par bloc)')
    print('')
    print("  Aucun texte n'a ete invente : les requetes envoyees sont")
    print('  recopiees dans index_ecoute.txt.')
    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())

