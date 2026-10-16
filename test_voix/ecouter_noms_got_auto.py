# -*- coding: utf-8 -*-
"""LES NOMS ANGLAIS PRIS EN CHARGE PAR LA FORMULE -- le premier lot AUTOMATIQUE.

DEMANDE DE LAURENT (16/10/2026), mot pour mot : « Pour les lots, on peut essayer
avec des prenoms anglais, peut-etre meme avec des noms de Game of thrones pour voir
ce que ca donne, si c'est mieux en anglais ou francais. Let's go ! »

CE QUE CE LOT A DE DIFFERENT : les graphies candidates ne sont PAS ecrites a la
main. Elles sont FABRIQUEES A L'INSTANT par la formule de
`test_voix/_essai_prononciation_anglaise.py` (phonemes anglais -> graphie
francaise : une table + des leviers). C'est le premier lot ou LA MACHINE TRAVAILLE
SEULE -- si Laurent valide, il n'a plus a corriger les noms un par un.

CE QU'ON ECOUTE, POUR CHAQUE NOM (3 fichiers, toujours la meme phrase porteuse) :

    1_CIBLE_anglaise  le nom dit par une VRAIE voix anglaise (Edge en-US) : le
                      repere de l'oreille, pas une lecture ;
    2_FRANCAIS        le nom tel que le livre l'ecrit, avec SA voix du casting
                      (c'est ce qu'on entend en lisant aujourd'hui) ;
    3_ANGLAIS         la graphie de la FORMULE, MEME voix, meme phrase.

ET LA QUESTION, NOM PAR NOM : mieux en francais (2), mieux en anglais (3), ou
aucune des deux ?

D'OU VIENNENT LES NOMS ET LES VOIX : du CASTING du *Trone de Fer*
(`data/nimm_epub.db`, livre 42, table `voices`) -- les personnages les plus
bavards, tous lus par le moteur en service (Qwen).

CE QU'IL FAUT ALLUMER : le moteur Qwen sur la carte (le lanceur double-clic s'en
charge ; ce script ATTEND qu'il reponde, et REFUSE de partir sinon : il n'invente
jamais d'audio). La FORMULE, elle, ne demande aucun moteur : c'est espeak-ng, deja
installe pour Kokoro.

LECTURE SEULE : ni la base, ni les voix, ni le service. Sortie datee dans
`test_voix/ecoute_noms_got_auto_<AAAAMMJJ-HHMM>/` avec LISEZ-MOI et RECAP.

Usage : python test_voix/ecouter_noms_got_auto.py
"""

import asyncio
import datetime
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(ICI))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

from modules import tts as _tts            # noqa: E402  (le chemin du lecteur)
import _essai_prononciation_anglaise as _formule   # noqa: E402  (LA FORMULE)
import ecouter_prenoms_22_11_63 as _commun         # noqa: E402  (les outils communs)

SUIVI = ICI / '_dernier_lot_got_auto.txt'

# ============================================================
# LES NOMS : les plus bavards du Trone de Fer, avec LEUR voix du casting
# ============================================================
# (nom du livre, voix du casting, genre). Le nombre de repliques est le compte
# reel de la base : ce sont les noms qu'on entend tout le temps. Tous sont lus
# par le moteur en service (Qwen).
CAS = [
    ('Eddard Stark',        'qwen:1406_1028_000009-0003',   'H'),   # 968 repliques
    ('Robert Baratheon',    'qwen:1770_1028_000036-0002',   'H'),   # 485
    ('Catelyn Stark',       'qwen:10177_10625_000134-0003', 'F'),   # 459
    ('Tyrion Lannister',    'qwen:2216_1745_000007-0001',   'H'),   # 417
    ('Jon Snow',            'qwen:2223_1745_000009-0002',   'H'),   # 378
    ('Petyr Baelish',       'qwen:296_1028_000022-0001',    'H'),   # 269
    ('Arya Stark',          'qwen:12080_11650_000047-0001', 'F'),   # 234
    ('Sansa Stark',         'qwen:12205_11650_000004-0002', 'F'),   # 130
    ('Jaime Lannister',     'qwen:7601_7727_000062-0001',   'H'),   # 87
    ('Cersei Lannister',    'qwen:12977_10625_000037-0001', 'F'),   # 90
    ('Daenerys Targaryen',  'qwen:1591_1028_000108-0004',   'F'),   # 80
    ('Sandor Clegane',      'qwen:5790_4893_000052-0001',   'H'),   # 94
    # LE TEMOIN, deja juge a l'oreille le 16/10/2026 : Laurent a dit que « Jake »
    # et « Epping » sont BIEN lus aujourd'hui. La formule doit donc le laisser
    # tranquille -- si elle le change, c'est qu'elle a un defaut.
    ('Jake Epping',         'qwen:1770_1028_000036-0002',   'H'),   # temoin
]


def _arguments():
    """`--attente` suit le demarrage du moteur ; `--sans-cible` s'en passe."""
    import argparse
    analyseur = argparse.ArgumentParser(
        description="Les noms anglais du Trone de Fer, par la FORMULE (lot automatique).")
    analyseur.add_argument('--attente', type=int, default=180,
                           help="secondes d'attente du moteur (defaut 180)")
    analyseur.add_argument('--sans-cible', action='store_true',
                           help="ne pas fabriquer la cible anglaise (Edge)")
    return analyseur.parse_args()


def _graphies_automatiques():
    """LA FORMULE SEULE : un nom -> sa graphie, et les deux scores qui vont avec.

    Aucun moteur de voix n'est necessaire ici : le phonetiseur (espeak-ng) est
    local, gratuit, et deja installe pour Kokoro. C'est le coeur du lot : ce que
    la machine propose, sans qu'on ecrive une seule graphie a la main.
    """
    phonemize = _formule._charger_le_phonetiseur()
    stable = _formule._verifier_la_stabilite(phonemize)
    resultats = []
    for nom, voix, genre in CAS:
        cible = _formule._ipa(phonemize, nom, 'en-us')
        graphie = _formule._graphie(cible, _formule.LEVIERS)
        lu_anglais = _formule._ipa(phonemize, graphie, 'fr-fr') if graphie else ''
        lu_francais = _formule._ipa(phonemize, nom, 'fr-fr')
        resultats.append({
            'nom': nom,
            'voix': voix,
            'genre': genre,
            'cible': cible,
            'graphie': graphie,
            'score_anglais': _formule._proximite(cible, lu_anglais) if lu_anglais else 0.0,
            'score_francais': _formule._proximite(cible, lu_francais) if lu_francais else 0.0,
        })
    return resultats, stable


def _lisez_moi(chemin, avec_cible, lignes_formule, stable):
    """Le mode d'emploi du dossier + la table des graphies trouvees par la machine."""
    lignes = [
        "LES NOMS ANGLAIS DU TRONE DE FER -- PREMIER LOT AUTOMATIQUE",
        "=" * 66,
        "",
        "Demande de Laurent (16/10/2026) : « on peut essayer avec [...] des noms de",
        "Game of thrones pour voir ce que ca donne, si c'est mieux en anglais ou",
        "francais. »",
        "",
        "CE QU'IL Y A DE NOUVEAU : AUCUNE graphie n'a ete ecrite a la main. Elles",
        "sortent de la FORMULE (phonemes anglais -> graphie francaise), calculee",
        "sur ta machine, hors ligne, en quelques secondes. Si tu valides, on ne",
        "corrige plus les noms un par un.",
        "",
        "CE QUE TU ECOUTES, POUR CHAQUE NOM (toujours la meme phrase) :",
        "   1_CIBLE_anglaise  une VRAIE voix anglaise (Edge en-US) : le repere de",
        "                     ton oreille -- elle dit le nom SEUL, ce n'est pas",
        "                     une lecture ;",
        "   2_FRANCAIS        le nom tel que le LIVRE l'ecrit, avec SA voix du",
        "                     casting : c'est ce que tu entends en lisant ;",
        "   3_ANGLAIS         la graphie de la FORMULE, MEME voix, meme phrase.",
        "",
        "CE QUE TU ME DIS, NOM PAR NOM : « 2 » (mieux en francais), « 3 » (mieux en",
        "anglais), « les deux pareils », ou « aucune des deux ».",
        "",
        "DEUX CHOSES A SAVOIR",
        "  - Le score affiche est une MESURE DES PHONEMES, pas ton oreille : il sert",
        "    a TRIER et a ETALONNER la formule, jamais a la remplacer. Il donne deja",
        "    raison a ton verdict sur « Jake » (voir le temoin, en bas).",
        "  - Le francais n'a ni le h, ni le th, ni l'accent anglais : la formule fait",
        "    au plus proche, elle ne fait pas un Anglais.",
        "",
        "LA TABLE DES GRAPHIES" if stable else
        "LA TABLE DES GRAPHIES (ATTENTION : phonetiseur INSTABLE, mesure a refaire)",
        "-" * 66,
        "",
    ]
    for rang, ligne in enumerate(lignes_formule, 1):
        lignes.append('%02d  %s' % (rang, ligne['nom']))
        lignes.append('    voix : %s' % ligne['voix'])
        lignes.append('    graphie de la formule : %s' % ligne['graphie'])
        lignes.append('    score : %3.0f %% en anglais   contre   %3.0f %% lu tel quel'
                      % (ligne['score_anglais'], ligne['score_francais']))
        if ligne['graphie'].lower() == ligne['nom'].lower():
            lignes.append('    (la formule ne change RIEN : elle juge le nom deja bon)')
        lignes.append('')
    chemin.write_text('\n'.join(lignes) + '\n', encoding='utf-8')


def _recap(chemin, etat_moteur, avec_cible, blocs, debut, stable):
    """Le journal du lot : le moteur, la formule, et les TEXTES EXACTS envoyes."""
    lignes = [
        "RECAP -- LES TEXTES EXACTS ENVOYES (a garder pour refaire le lot)",
        "=" * 66,
        "date             : %s" % debut,
        "moteur           : %s" % (etat_moteur.get('moteur') or '?'),
        "appareil         : %s" % (etat_moteur.get('appareil') or '?'),
        "langue du moteur : %s" % (etat_moteur.get('langue') or '?'),
        "cible anglaise   : %s" % ('Edge en-US (gratuit, en ligne)' if avec_cible
                                  else 'non demandee'),
        "formule          : test_voix/_essai_prononciation_anglaise.py",
        "leviers          : %s" % _formule.LEVIERS,
        "phonetiseur      : %s" % ('stable' if stable else 'INSTABLE'),
        "",
    ]
    lignes.extend(blocs)
    chemin.write_text('\n'.join(lignes) + '\n', encoding='utf-8')


async def main():
    options = _arguments()
    debut = datetime.datetime.now()
    print('=' * 70)
    print('  LES NOMS ANGLAIS DU TRONE DE FER -- premier lot AUTOMATIQUE')
    print('=' * 70)

    # -- 1. LA FORMULE (aucun moteur : espeak-ng, local et gratuit) -------------
    print('  la formule travaille...')
    lignes_formule, stable = _graphies_automatiques()
    print('  phonetiseur : %s'
          % ('stable' if stable else 'INSTABLE -- a lire avec prudence'))
    for ligne in lignes_formule:
        change = '' if ligne['graphie'].lower() != ligne['nom'].lower() else '  (inchangee)'
        print('    %-22s -> %-24s %3.0f %%  (lu tel quel %3.0f %%)%s'
              % (ligne['nom'], ligne['graphie'], ligne['score_anglais'],
                 ligne['score_francais'], change))

    # -- 2. LE MOTEUR (allume par le lanceur ; on attend qu'il reponde) ---------
    etat = _commun._attendre_le_moteur(options.attente)
    if not etat:
        print('')
        print('  LE MOTEUR QWEN NE REPOND PAS (port 8086).')
        print('  Allume-le (fenetre DEMARRER_QWENTTS_CPP_GPU.bat), puis relance.')
        return 1
    print('')
    print('  moteur   : %s -- %s'
          % (etat.get('moteur') or '?', etat.get('appareil') or '?'))

    dossier = ICI / ('ecoute_noms_got_auto_%s' % debut.strftime('%Y%m%d-%H%M'))
    dossier.mkdir(parents=True, exist_ok=True)
    SUIVI.write_text(str(dossier), encoding='utf-8')
    print('  dossier  : %s' % dossier.name)
    print('')

    blocs = []
    for rang, ligne in enumerate(lignes_formule, 1):
        nom, graphie = ligne['nom'], ligne['graphie']
        base = '%02d_%s' % (rang, _commun._nom_de_fichier(nom))
        print('  [%2d/%d] %s' % (rang, len(lignes_formule), nom))
        bloc = ['%02d | %s | voix %s | genre %s | formule %3.0f %%  contre  lu tel quel %3.0f %%'
                % (rang, nom, ligne['voix'], ligne['genre'],
                   ligne['score_anglais'], ligne['score_francais']),
                '     CIBLE anglaise         : %s' % ligne['cible'],
                '     graphie de la formule  : %s' % graphie]

        # -- la CIBLE : le repere de l'oreille (le nom seul, en anglais) --------
        if options.sans_cible:
            bloc.append('     CIBLE : non demandee (--sans-cible)')
        else:
            try:
                mp3 = await _commun._nom_en_anglais(nom, ligne['genre'])
                chemin = dossier / ('%s__1_CIBLE_anglaise.wav' % base)
                if mp3 and _commun._mp3_vers_wav(mp3, chemin):
                    bloc.append('     CIBLE : %.2f s'
                                % _commun._noter(chemin, '1_CIBLE_anglaise'))
                else:
                    bloc.append('     CIBLE : ECHEC (Edge)')
                    print('      cible anglaise : ECHEC (Edge)')
            except Exception as erreur:
                bloc.append('     CIBLE : ECHEC (%s)' % type(erreur).__name__)
                print('      cible anglaise : ECHEC (%s)' % type(erreur).__name__)

        # -- 2_FRANCAIS puis 3_ANGLAIS : MEME voix, MEME phrase porteuse -------
        for etiquette, texte in (('2_FRANCAIS', _commun.CARRIERE % nom),
                                 ('3_ANGLAIS', _commun.CARRIERE % graphie)):
            try:
                octets = await _commun._phrase_lue(texte, ligne['voix'])
            except _tts.QwenIndisponible as erreur:
                print('')
                print('  LE MOTEUR A LACHE EN PLEIN LOT : %s' % erreur)
                print('  (les fichiers deja fabriques restent dans le dossier)')
                return 1
            duree = _commun._ecrire(dossier / ('%s__%s.wav' % (base, etiquette)),
                                    octets, etiquette)
            bloc.append('     %-10s : « %s » -- %.2f s' % (etiquette, texte, duree))

        blocs.append('\n'.join(bloc))
        print('')

    _lisez_moi(dossier / 'LISEZ-MOI.txt', not options.sans_cible, lignes_formule, stable)
    _recap(dossier / 'RECAP.txt', etat, not options.sans_cible, blocs,
           debut.strftime('%d/%m/%Y %H:%M'), stable)

    nombre = len(list(dossier.glob('*.wav')))
    print('=' * 70)
    print('  C EST PRET : %d noms, %d fichiers audio' % (len(lignes_formule), nombre))
    print('  %s' % dossier)
    print('=' * 70)
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))


