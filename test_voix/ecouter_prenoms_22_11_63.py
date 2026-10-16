# -*- coding: utf-8 -*-
"""LES PRENOMS ANGLAIS DE 22/11/63 : ce que le moteur en fait AUJOURD'HUI, et ce
qu'une graphie francaise « a l'anglaise » donne a l'oreille.

D'OU VIENT CE BANC (16/10/2026, demande de Laurent, mot pour mot : « Je voudrais
me pencher sur la prononciation des prenoms. Il faudrait trouver quelque chose
pour que la prononciation se fasse "a l'anglaise" quand ce sont des noms ou des
prenoms anglais. »)

CE QUI EST ETABLI AVANT D'ECRIRE UNE LIGNE (verifie le 16/10/2026, dans le code) :
  - le moteur en service, Qwen3-TTS (qwentts.cpp, port 8086), recoit UNE SEULE
    langue pour TOUTE la phrase (`lang='french'`, `servir_qwentts_cpp.py`) ; la
    liste des langues vit dans le modele : chinese, english, german, italian,
    portuguese, spanish, japanese, korean, french, russian -- une seule a la
    fois, et pas de « auto » ;
  - l'API du moteur accepte un champ `instruct` (« dis-lui comment prononcer »),
    mais le moteur le REFUSE : « --instruct is not supported for base models »
    (chaine lue dans `qwen.dll`) ;
  - Qwen ne recoit QUE du texte : pas de phonemes. Seuls Kokoro et Piper
    acceptent de vrais phonemes (espeak-ng, `is_phonemes=True`), et ils ne sont
    plus les moteurs de service.
  => LE SEUL LEVIER est donc CE QU'ON ECRIT. D'ou ce banc, qui fait ecouter TROIS
     choses pour chaque nom :

        CIBLE        le nom dit par une VRAIE voix anglaise (Edge en-US). Ce
                     n'est PAS une lecture : c'est le REPERE de l'oreille,
                     « voila a quoi ca doit ressembler ».
        AUJOURD'HUI  le nom tel que le livre l'ecrit, avec la VRAIE voix du
                     personnage (le moteur en service) : ce que tu entends.
        B1, B2, B3   des GRAPHIES candidates : le nom reecrit pour la LECTURE
                     seule. Le texte affiche ne bouge jamais -- meme patron que
                     `modules/prononciation.py`.

RIEN N'EST MODIFIE dans le projet : ni la base, ni les voix, ni le service, ni
`modules/prononciation.py`. Ce banc n'ecrit que dans son dossier de sortie, et il
ne fait entrer AUCUNE graphie dans une table : c'est l'oreille de Laurent qui
tranche, candidat par candidat (une graphie fausse s'entendrait dans tout le
livre -- la lecon est ecrite dans `modules/prononciation.py`).

CE QU'IL UTILISE (pour que l'ecoute soit celle du lecteur) : les briques de la
lecture elle-meme -- `modules/tts.py` : `synthesize_qwen` (avec ses etapes de
rognage de queue, vitesse, hauteur, normalisation et fondu d'entree) et
`synthesize_bytes` (Edge) pour la cible anglaise.

CE QU'IL FAUT ALLUMER : le moteur Qwen sur la carte. Le lanceur double-clic
(`ECOUTER_LES_PRENOMS_ANGLAIS.bat`) s'en charge ; ce script ATTEND qu'il reponde
(`--attente`, 180 s par defaut) et REFUSE de partir s'il ne vient pas : il
n'invente jamais d'audio.

SORTIE : `test_voix/ecoute_prenoms_22_11_63_<AAAAMMJJ-HHMM>/`
  - `LISEZ-MOI.txt` : la table des graphies candidates, a lire avant d'ecouter ;
  - `RECAP.txt`     : les textes EXACTS envoyes, et la duree de chaque audio ;
  - les WAV numerotes : `NN_nom__1_CIBLE_anglaise`, `__2_AUJOURD_HUI`, `__3_B1`,
    `__4_B2`... -- l'explorateur les classe dans cet ordre, c'est voulu.

Usage :
    python test_voix/ecouter_prenoms_22_11_63.py
    python test_voix/ecouter_prenoms_22_11_63.py --sans-cible
    python test_voix/ecouter_prenoms_22_11_63.py --attente 240
"""

import argparse
import asyncio
import datetime
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request
import wave
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

from modules import tts as _tts  # noqa: E402  (le chemin de synthese du lecteur)

SANTE = 'http://127.0.0.1:8086/sante'
SUIVI = ICI / '_dernier_lot_prenoms.txt'

# La phrase porteuse : IDENTIQUE pour « aujourd'hui » et pour les candidats --
# sans cela, la comparaison ne vaut rien (lecon des lots d'ecoute de l'atelier).
CARRIERE = 'Alors %s répondit doucement.'

# La cible anglaise : une VOIX ANGLAISE d'Edge, gratuite et deja utilisee par le
# lecteur (aucune cle d'API, rien de facture). Elle ne sert qu'a donner a
# l'oreille le son a atteindre.
CIBLES_ANGLAISES = {'H': 'en-US-GuyNeural', 'F': 'en-US-AriaNeural'}

# ============================================================
# LA TABLE : les noms, leurs vraies voix, et les GRAPHIES CANDIDATES
# ============================================================
# Les voix viennent du CASTING de 22/11/63 (`data/nimm_epub.db`, table `voices`),
# et le nombre de repliques est son compte reel : ce sont les personnages qu'on
# entend tout le temps. Les 12 noms gardes sont TOUS lus par le moteur en service
# (Qwen) : c'est lui qui est en question. (Sadie Clayton est lue par Edge, Lee
# Oswald par Kokoro, Richie Tozier par Edge : eux viendront dans un autre lot,
# chaque moteur reagit differemment a la meme graphie.)
#
# LES GRAPHIES SONT DES CANDIDATS, PAS DES VERITES. Elles sont ecrites ici pour
# etre ecoutees puis jugees une par une, et elles ne vivent QUE dans ce banc.
CAS = [
    {
        'nom': 'Jake Epping',
        'voix': 'qwen:1770_1028_000036-0002',
        'genre': 'H',
        'note': "le heros (3 615 repliques). Le « -ing » final n'a pas "
                "d'equivalent francais : trois candidats.",
        'candidats': ['Djeïk Epping', 'Djeïk Èpine', 'Djeïk Èpigne'],
    },
    {
        'nom': 'Al Templeton',
        'voix': 'qwen:7601_7727_000062-0001',
        'genre': 'H',
        'note': "le vieil homme du diner (1 169 repliques). Le « -ton » final "
                "anglais est un /eun/, pas un « ton » francais.",
        'candidats': ['Al Tèmpeltone', 'Al Tèmpleutène'],
    },
    {
        'nom': 'Deke Simmons',
        'voix': 'qwen:Homme001',
        'genre': 'H',
        'note': "le proviseur (338 repliques). « Simmons » se dit "
                "« SI-meunz » : le « on » francais est un piege.",
        'candidats': ['Dîke Simeunz', 'Dîke Simmins'],
    },
    {
        'nom': 'Harry Dunning',
        'voix': 'qwen:296_1028_000022-0001',
        'genre': 'H',
        'note': "le veuf au marteau (233 repliques). « Harry » se dit "
                "« HA-ri », et « Dunning » a le u de « du ».",
        'candidats': ['Hary Deunine', 'Hari Deunigne'],
    },
    {
        'nom': 'Mimi Corcoran',
        'voix': 'qwen:12080_11650_000047-0001',
        'genre': 'F',
        'note': "la bibliothecaire (198 repliques). Le o anglais de "
                "« Corcoran » tire vers le « eau ».",
        'candidats': ['Mimi Côrqueurane', 'Mimi Corcoranne'],
    },
    {
        'nom': 'Bill Turcotte',
        'voix': 'qwen:bm_daniel',
        'genre': 'H',
        'note': "le boucher (147 repliques). « Turcotte » se dit a l'anglaise "
                "« teur-KOTT », pas « tur-cotte ».",
        'candidats': ['Bil Teurcote', 'Bile Teurcotte'],
    },
    {
        'nom': 'Ellen Dockerty',
        'voix': 'qwen:12977_10625_000037-0001',
        'genre': 'F',
        'note': "l'institutrice (142 repliques). « Ellen » anglais est plus "
                "bref que notre « Ellène ».",
        'candidats': ['Èleune Doqueurti', 'Èlène Dokeurti'],
    },
    {
        'nom': 'Mike Coslaw',
        'voix': 'qwen:5790_4893_000052-0001',
        'genre': 'H',
        'note': "la baderne du lycee (138 repliques). « Mike » se dit "
                "« Maïk » : le i anglais est une diphtongue.",
        'candidats': ['Maïk Koslô', 'Maïk Cosse-lô'],
    },
    {
        'nom': 'Marguerite Oswald',
        'voix': 'qwen:1591_1028_000108-0004',
        'genre': 'F',
        'note': "LE CAS MIXTE (83 repliques) : le prenom est FRANCAIS dans ce "
                "livre, le nom est anglais. Les candidats ne touchent QUE le "
                "nom -- c'est ce qui montre qu'on ne peut pas faire une regle "
                "en bloc.",
        'candidats': ['Marguerite Ozeuwald', 'Marguerite Ozwold'],
    },
    {
        'nom': 'Beverly Marsh',
        'voix': 'qwen:2154_2576_000020-0003',
        'genre': 'F',
        'note': "la marchande de meubles (61 repliques). « Marsh » a le « ch » "
                "de « chat », et son « e » est muet.",
        'candidats': ['Bèvreli Mârch', 'Bèverli Marche'],
    },
    {
        'nom': 'Freddy Quinlan',
        'voix': 'qwen:7142_2432_000124-0003',
        'genre': 'H',
        'note': "le chemisier de Dallas (46 repliques). « Quinlan » se dit "
                "« KOUIN-lane ».",
        'candidats': ['Frédi Kwine-lane', 'Frédi Kouineulène'],
    },
    {
        'nom': 'Jacqueline Kennedy',
        'voix': 'qwen:10087_11650_000028-0002',
        'genre': 'F',
        'note': "DEUXIEME CAS MIXTE : prenom francais, nom anglais. "
                "« Kennedy » se dit « KE-neu-di ».",
        'candidats': ['Jacqueline Kènedeu', 'Jacqueline Kènedi'],
    },
]

# ============================================================
# LOT 2 -- LA REPRISE DU 16/10/2026, APRES TES PREMIERS VERDICTS
# ============================================================
# TES VERDICTS, ET CE QU'ILS DECLENCHENT (16/10/2026) :
#   01 Jake Epping   -> « Le Jake AUJOURD'HUI est ok. Epping aussi. » => RIEN A FAIRE.
#        *ET C'EST UNE LECON, ECRITE ICI POUR QU'ELLE SERVE* : mes graphies
#        « Djeïk » ont ABIME un nom que le moteur disait DEJA bien (tu as entendu
#        « Jik », le i de « ile »). Le moteur RECONNAIT donc les noms anglais tout
#        seul -- on ne reecrit QUE ce qui rate, et une seule chose a la fois.
#   02 Al Templeton  -> « Bien prononce aujourd'hui. » => RIEN A FAIRE.
#   03 Deke Simmons  -> tu veux le prenom a l'anglaise : « ok pour Dîke ».
#        Le NOM, lui, n'a pas encore ete juge : c'est l'objet des cas 1 et 2.
#   04 Harry Dunning -> aujourd'hui tu entends « Dinning » (un i au lieu du u), et
#        les DEUX candidats du lot 1 sont refuses (mais ils changeaient aussi le
#        prenom : on ne saura jamais ce qui a deplu). On repart par la VOYELLE, puis
#        par la FIN du mot, en ne touchant qu'a UNE chose par candidat.
CAS_LOT2 = [
    {
        'nom': 'Deke Simmons',
        'titre': 'Deke -- le prenom',
        'voix': 'qwen:Homme001',
        'genre': 'H',
        'note': "ton verdict : le prenom doit sonner « Dîke ». Ici le NOM est "
                "INCHANGE : seul le prenom bouge, pour juger une chose a la fois.",
        'candidats': [('Dîke Simmons', 'le prenom : e -> î')],
    },
    {
        'nom': 'Deke Simmons',
        'titre': 'Deke -- le nom',
        'voix': 'qwen:Homme001',
        'genre': 'H',
        'note': "« Simmons » se dit « SI-meunz » ; c'est le « on » francais qui est "
                "en cause. Le prenom est laisse EN L'ETAT, pour juger le nom seul.",
        'candidats': [
            ('Deke Simeunz', 'le nom : mm/o/s -> m/eu/z'),
            ('Deke Simmins', 'le nom : o -> i, la fin inchangee'),
        ],
    },
    {
        'nom': 'Harry Dunning',
        'titre': 'Dunning -- la voyelle',
        'voix': 'qwen:296_1028_000022-0001',
        'genre': 'H',
        'note': "c'est LA que tu as entendu le defaut d'aujourd'hui (« Dinning »). Le "
                "son anglais du « u » de Dunning n'est ni notre u ni notre i : on "
                "essaie les trois ecritures francaises possibles, SANS toucher au "
                "reste du mot.",
        'candidats': [
            ('Harry Deunning', 'la voyelle : u -> eu'),
            ('Harry Danning', 'la voyelle : u -> a'),
            ('Harry Denning', 'la voyelle : u -> e'),
        ],
    },
    {
        'nom': 'Harry Dunning',
        'titre': 'Dunning -- la fin du mot',
        'voix': 'qwen:296_1028_000022-0001',
        'genre': 'H',
        'note': "autre piste : si c'est la FIN qui sonne mal (« -ing » lu a la "
                "francaise), ces ecritures la corrigent SANS toucher a la voyelle. Le "
                "prenom « Harry » n'est jamais touche (il n'etait pas en cause).",
        'candidats': [
            ('Harry Dunnigne', 'la fin : ing -> igne'),
            ('Harry Dunnin', 'la fin : on enleve le g'),
        ],
    },
]

# Le lot courant : 1 = le lot du 16/10 (12 noms de 22/11/63, verdicts rendus),
# 2 = la reprise apres verdicts. `--lot 1` rejoue le premier.
LOTS = {1: CAS, 2: CAS_LOT2}
LOT_PAR_DEFAUT = 2

# ============================================================
# OUTILS
# ============================================================

def _arguments():
    analyseur = argparse.ArgumentParser(
        description='Les prenoms anglais de 22/11/63 : aujourd hui, candidats, '
                    'et la cible en vraie voix anglaise.')
    analyseur.add_argument('--attente', type=int, default=180,
                           help="secondes d'attente du moteur (defaut 180)")
    analyseur.add_argument('--lot', type=int, choices=sorted(LOTS),
                           default=LOT_PAR_DEFAUT,
                           help='le lot a fabriquer (defaut %d)' % LOT_PAR_DEFAUT)
    analyseur.add_argument('--sans-cible', action='store_true',
                           help='ne pas fabriquer la cible anglaise (Edge)')
    return analyseur.parse_args()


def _nom_de_fichier(nom):
    """« Marguerite Oswald » -> « marguerite_oswald » (nom de fichier sur)."""
    sans_accent = unicodedata.normalize('NFKD', nom)
    sans_accent = sans_accent.encode('ascii', 'ignore').decode('ascii')
    propre = ''.join(c if c.isalnum() else '_' for c in sans_accent)
    while '__' in propre:                 # « -- » et les espaces doublent le tiret
        propre = propre.replace('__', '_')
    return propre.strip('_').lower()


def _titre(cas):
    """Le titre d'un cas. Le lot 2 en a besoin : DEUX cas pour le meme nom
    (« Deke -- le prenom » et « Deke -- le nom »), sinon les fichiers se
    marcheraient dessus."""
    return cas.get('titre') or cas['nom']


def _graphie_et_note(element):
    """Un candidat s'ecrit soit « graphie », soit (« graphie », « ce qui change »).

    Le commentaire sert au lot 2, ou chaque candidat ne change QU'UNE chose : il
    dit laquelle, pour que l'oreille sache ce qu'elle juge."""
    if isinstance(element, tuple):
        return element[0], element[1]
    return element, ''


def _sante():
    """Ce que le moteur repond sur /sante, ou None s'il ne repond pas."""
    import json
    try:
        with urllib.request.urlopen(SANTE, timeout=3) as reponse:
            return json.loads(reponse.read().decode('utf-8'))
    except Exception:
        return None


def _attendre_le_moteur(secondes):
    """Attend que le moteur reponde (le lanceur l'allume juste avant)."""
    debut = time.time()
    prevenu = False
    while time.time() - debut < secondes:
        etat = _sante()
        if etat:
            return etat
        if not prevenu:
            prevenu = True
            print("  moteur pas encore pret : on attend (jusqu'a %d s)..." % secondes)
        time.sleep(3)
    return None


def _duree_wav(chemin):
    """La duree d'un WAV, en secondes."""
    with wave.open(str(chemin), 'rb') as fichier:
        images = fichier.getnframes()
        taux = fichier.getframerate() or 24000
    return images / float(taux)


def _noter(chemin, etiquette):
    """Mesure, affiche et rend la duree d'un WAV deja ecrit."""
    duree = _duree_wav(chemin)
    print('      %-16s %-32s %6.2f s' % (etiquette, chemin.name, duree))
    return duree


def _ecrire(chemin, octets, etiquette):
    """Ecrit un WAV et rend sa duree (un candidat 3 s plus long, ca se voit)."""
    chemin.write_bytes(octets)
    return _noter(chemin, etiquette)


def _mp3_vers_wav(octets_mp3, chemin_wav):
    """Edge rend du MP3 : on le met en WAV, pour un dossier homogene.

    Meme binaire ffmpeg que le rognage et la vitesse du projet
    (`imageio-ffmpeg`, deja embarque)."""
    from imageio_ffmpeg import get_ffmpeg_exe
    with tempfile.TemporaryDirectory() as temporaire:
        source = Path(temporaire) / 'entree.mp3'
        source.write_bytes(octets_mp3)
        commande = [get_ffmpeg_exe(), '-y', '-hide_banner', '-loglevel', 'error',
                    '-i', str(source), '-ar', '24000', '-ac', '1',
                    '-c:a', 'pcm_s16le', str(chemin_wav)]
        resultat = subprocess.run(commande, capture_output=True, timeout=120)
    return resultat.returncode == 0 and chemin_wav.exists()


# ============================================================
# LES DEUX CHEMINS DE SYNTHESE
# ============================================================

async def _phrase_lue(texte, voix):
    """Le chemin du LECTEUR, tel quel : `modules/tts.py`, moteur en service.

    On ne recopie rien : c'est `synthesize_qwen`, donc le nettoyage du texte, le
    moteur, puis le rognage de queue, la vitesse, la hauteur, la normalisation et
    le fondu d'entree -- exactement ce que Laurent entend en lisant."""
    return await _tts.synthesize_qwen(texte, voix)


async def _nom_en_anglais(nom, genre):
    """Le nom SEUL, dit par une vraie voix anglaise d'Edge (gratuit, en ligne).

    C'est le repere de l'oreille, pas une lecture : rien d'autre que le nom."""
    return await _tts.synthesize_bytes(nom, CIBLES_ANGLAISES[genre])


# ============================================================
# LES FICHIERS DU LOT
# ============================================================

def _lisez_moi(chemin, avec_cible, lot, table):
    """Le mode d'emploi du dossier : quoi ecouter, dans quel ordre, quoi repondre."""
    lignes = [
        "LES PRENOMS ANGLAIS DE 22/11/63 -- BANC D'ECOUTE (LOT %d)" % lot,
        "=" * 66,
        "",
        "Demande de Laurent (16/10/2026) : « Je voudrais me pencher sur la",
        "prononciation des prenoms. Il faudrait trouver quelque chose pour que la",
        "prononciation se fasse a l'anglaise quand ce sont des noms ou des prenoms",
        "anglais. »",
        "",
    ]
    if lot == 2:
        lignes.extend([
            "CE LOT-CI REPREND TES VERDICTS DU 16/10/2026 :",
            "  - « Le Jake AUJOURD'HUI est ok. Epping aussi. » -> rien a faire ;",
            "  - « Al Templeton : bien prononce aujourd'hui. »  -> rien a faire ;",
            "  - Deke : tu veux le prenom a l'anglaise (« Dîke ») ;",
            "  - Harry Dunning : aujourd'hui tu entends « Dinning ».",
            "",
            "Chaque candidat ne change QU'UNE chose, et la ligne du candidat dit",
            "laquelle : c'est ce qui rend le verdict facile a lire (dans le lot 1,",
            "les candidats changeaient des noms entiers).",
            "",
        ])
    lignes.extend([
        "CE QU'IL Y A A FAIRE",
        "  1. Pour CHAQUE nom (numerote 01, 02...), ecoute dans cet ordre :",
        "",
        "       1_" + ("CIBLE_anglaise" if avec_cible else "(pas de cible)")
        + "   le nom dit par une VRAIE voix anglaise (Edge en-US).",
        "                        C'est le REPERE : voila a quoi ca doit",
        "                        ressembler. Elle dit SEULEMENT le nom, sans",
        "                        phrase autour.",
        "       2_AUJOURD_HUI    le nom tel que le livre l'ecrit, avec SA voix du",
        "                        casting. C'est ce que tu entends en lisant.",
        "       3_B1, 4_B2...    les GRAPHIES candidates : le nom reecrit pour la",
        "                        LECTURE seule (le texte affiche ne bouge jamais).",
        "",
        "  2. Pour chaque nom, dis-moi simplement :",
        "       - « aujourd'hui ca me va »  (le moteur s'en sort tout seul), ou",
        "       - « c'est B2 »              (la graphie gagnante), ou",
        "       - « aucune »                (on essaiera autre chose).",
        "",
        "  3. Ce que tu valides entrera dans une table (une ligne par nom) et sera",
        "     revalide a l'oreille sur une phrase entiere avant d'etre garde.",
        "",
        "TROIS CHOSES A SAVOIR",
        "  - Les graphies sont des CANDIDATS, pas des verites : c'est toi qui",
        "    tranches. Aucune n'est dans le projet, elles vivent dans ce dossier.",
        "  - Le meme nom peut demander deux traitements selon le livre (dans",
        "    Monte-Cristo, « Andrea » est francais, et il le reste) : rien ne sera",
        "    decide en bloc.",
        "  - Le moteur ne peut PAS changer de langue au milieu d'une phrase (une",
        "    seule langue par appel, verifie le 16/10/2026) : le seul levier est",
        "    l'orthographe. L'audio de 2, 3, 4... passe par le MEME chemin que ta",
        "    lecture (rognage, vitesse, hauteur, niveau, fondu) ; la cible",
        "    anglaise, elle, vient d'Edge.",
        "",
        "LA TABLE DES CANDIDATS",
        "-" * 66,
        "",
    ])
    for rang, cas in enumerate(table, 1):
        lignes.append('%02d  %s' % (rang, _titre(cas)))
        lignes.append('    voix : %s' % cas['voix'])
        lignes.append('    %s' % cas['note'])
        for numero, element in enumerate(cas['candidats'], 1):
            graphie, commentaire = _graphie_et_note(element)
            lignes.append('    B%d : %s%s'
                          % (numero, graphie,
                             ('   -- ' + commentaire) if commentaire else ''))
        lignes.append('')
    chemin.write_text('\n'.join(lignes) + '\n', encoding='utf-8')


def _recap(chemin, etat_moteur, avec_cible, blocs, debut):
    """Le journal du lot : le moteur, la cible, et les TEXTES EXACTS envoyes."""
    lignes = [
        "RECAP -- LES TEXTES EXACTS ENVOYES (a garder pour refaire le lot)",
        "=" * 66,
        "date          : %s" % debut,
        "moteur        : %s" % (etat_moteur.get('moteur') or '?'),
        "appareil      : %s%s" % (etat_moteur.get('appareil') or '?',
                                  ' [REPLI processeur : %s]'
                                  % (etat_moteur.get('repli_raison') or '?')
                                  if etat_moteur.get('repli') else ''),
        "variante      : %s" % (etat_moteur.get('variante') or '?'),
        "langue du moteur : %s" % (etat_moteur.get('langue') or '?'),
        "cible anglaise : %s" % ('Edge ' + ' / '.join(sorted(CIBLES_ANGLAISES.values()))
                                 if avec_cible else 'non demandee'),
        "",
    ]
    lignes.extend(blocs)
    chemin.write_text('\n'.join(lignes) + '\n', encoding='utf-8')


# ============================================================
# LE DEROULE
# ============================================================

async def main():
    options = _arguments()
    debut = datetime.datetime.now()
    print('=' * 70)
    print('  LES PRENOMS ANGLAIS DE 22/11/63 -- banc d ecoute')
    print('=' * 70)

    etat = _attendre_le_moteur(options.attente)
    if not etat:
        print('')
        print('  LE MOTEUR QWEN NE REPOND PAS (port 8086).')
        print('  Double-clique sur  qwentts_service\\DEMARRER_QWENTTS_CPP_GPU.bat,')
        print('  attends que sa fenetre dise qu il est pret, puis relance.')
        return 1

    if etat.get('repli'):
        print('  ATTENTION : le moteur tourne sur le PROCESSEUR (repli : %s)'
              % (etat.get('repli_raison') or '?'))
    print('  moteur   : %s' % (etat.get('moteur') or '?'))
    print('  appareil : %s -- variante %s'
          % (etat.get('appareil') or '?', etat.get('variante') or '?'))

    dossier = ICI / ('ecoute_prenoms_22_11_63_lot%d_%s'
                     % (options.lot, debut.strftime('%Y%m%d-%H%M')))
    dossier.mkdir(parents=True, exist_ok=True)
    SUIVI.write_text(str(dossier), encoding='utf-8')
    print('  dossier  : %s' % dossier.name)
    print('')

    table = LOTS[options.lot]
    blocs = []
    for rang, cas in enumerate(table, 1):
        nom = cas['nom']
        base = '%02d_%s' % (rang, _nom_de_fichier(_titre(cas)))
        print('  [%2d/%d] %s' % (rang, len(table), _titre(cas)))
        bloc = ['%02d | %s | voix %s | genre %s'
                % (rang, nom, cas['voix'], cas['genre'])]

        # -- 1. LA CIBLE : le repere de l'oreille (le nom seul, en anglais).
        if options.sans_cible:
            bloc.append('    CIBLE : non demandee (--sans-cible)')
        else:
            try:
                mp3 = await _nom_en_anglais(nom, cas['genre'])
                chemin = dossier / ('%s__1_CIBLE_anglaise.wav' % base)
                if mp3 and _mp3_vers_wav(mp3, chemin):
                    duree = _noter(chemin, '1_CIBLE_anglaise')
                    bloc.append('    CIBLE : « %s » (Edge %s) -- %.2f s'
                                % (nom, CIBLES_ANGLAISES[cas['genre']], duree))
                else:
                    bloc.append('    CIBLE : ECHEC (Edge)')
                    print('      cible anglaise : ECHEC (Edge)')
            except Exception as erreur:
                bloc.append('    CIBLE : ECHEC (%s)' % type(erreur).__name__)
                print('      cible anglaise : ECHEC (%s)' % type(erreur).__name__)

        # -- 2. AUJOURD'HUI : le nom tel que le livre l'ecrit, voix du casting.
        texte_a = CARRIERE % nom
        try:
            octets = await _phrase_lue(texte_a, cas['voix'])
        except _tts.QwenIndisponible as erreur:
            print('')
            print('  LE MOTEUR A LACHE EN PLEIN LOT : %s' % erreur)
            print('  (les fichiers deja fabriques restent dans le dossier)')
            return 1
        duree = _ecrire(dossier / ('%s__2_AUJOURD_HUI.wav' % base), octets,
                        '2_AUJOURD_HUI')
        bloc.append('    A     : « %s » -- %.2f s' % (texte_a, duree))

        # -- 3. LES CANDIDATS : le nom reecrit pour la lecture seule.
        for numero, element in enumerate(cas['candidats'], 1):
            graphie, commentaire = _graphie_et_note(element)
            texte_b = CARRIERE % graphie
            try:
                octets = await _phrase_lue(texte_b, cas['voix'])
            except _tts.QwenIndisponible as erreur:
                print('')
                print('  LE MOTEUR A LACHE EN PLEIN LOT : %s' % erreur)
                print('  (les fichiers deja fabriques restent dans le dossier)')
                return 1
            etiquette = '%d_B%d' % (2 + numero, numero)
            duree = _ecrire(dossier / ('%s__%s.wav' % (base, etiquette)),
                            octets, etiquette)
            bloc.append('    B%d    : « %s » -- %.2f s%s'
                        % (numero, texte_b, duree,
                           ('   [%s]' % commentaire) if commentaire else ''))

        blocs.append('\n'.join(bloc))
        print('')

    _lisez_moi(dossier / 'LISEZ-MOI.txt', not options.sans_cible, options.lot, table)
    _recap(dossier / 'RECAP.txt', etat, not options.sans_cible, blocs,
           debut.strftime('%d/%m/%Y %H:%M'))

    nombre_wav = len(list(dossier.glob('*.wav')))
    print('=' * 70)
    print('  C EST PRET, LOT %d : %d cas, %d fichiers audio'
          % (options.lot, len(table), nombre_wav))
    print('  %s' % dossier)
    print('  Ouvre d abord  LISEZ-MOI.txt  : c est la table des graphies.')
    print('=' * 70)
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))



