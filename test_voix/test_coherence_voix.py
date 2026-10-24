# -*- coding: utf-8 -*-
"""Verifie que le CATALOGUE des voix et le DISQUE disent la meme chose.

Pourquoi (24/10/2026, demande de Laurent) : il clone des voix dans NIMM Voix,
puis trois choses doivent arriver ensemble dans NIMM ePub -- le fichier de
reference dans le dossier du service, sa ligne de TEXTE, et son entree dans le
CATALOGUE (`modules/tts.py`). En oublier une ne casse rien tout de suite :

  - entree au catalogue SANS fichier  -> le personnage est muet a la lecture ;
  - fichier SANS entree au catalogue  -> la voix n'apparait dans AUCUN menu
    (elle peut deja etre attribuee a un livre, donc on l'entend sans pouvoir
    la choisir) ;
  - fichier SANS texte (qwen, neutts) -> le service refuse la voix, ou le
    moteur invente une prononciation ;
  - duree ANNONCEE tres differente de celle du fichier -> le texte colle
    probablement a un AUTRE enregistrement (signale « A LIRE », pas en echec :
    la duree du CSV vient de la transcription, avant rognage des bords).

Le meme jour, une simple date de fichier m'a fait annoncer a tort que deux voix
manquaient au catalogue : cet outil repond a la question par la LISTE, pas par
le dossier.

CE QU'IL LIT (conventions relevees dans les services, pas devinees) :
  qwen    qwen_tts_service/voix/       <id>_reference.wav ou <id>_enhanced_reference.wav
          + TEXTE dans references.csv (public) ou references_privees.csv (prive)
  kyutai  kyutai_service/voix_fr/      <id>_enhanced.wav.<marqueur>.safetensors
  xtts    xtts_service/voix_fr/        <id>_enhanced.wav
  neutts  neutts_service/references/   <id>_reference.wav (+ texte : references.csv
                                       du dossier, ou <id>_reference.txt)
  pocket  pocket_tts_service/voix/     <id>_reference.wav
  kokoro, piper, edge : aucun fichier par voix (modeles ou cloud) -- non verifies.

LECTURE SEULE : rien n'est ecrit, aucun moteur n'est allume, rien n'est facture.

Usage : python test_voix/test_coherence_voix.py
"""

import csv
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(RACINE))

ECHECS = 0
MAX_MONTRES = 15        # on n'inonde pas l'ecran : au-dela, on compte seulement

# Les suffixes de fichier reconnus par qwentts_service/servir_qwentts_cpp.py
# (SUFFIXES_FICHIERS), du plus long au plus court : l'ordre compte.
SUFFIXES_QWEN = ('_enhanced_reference.wav', '_reference.wav')

# Ecart de duree A PARTIR DUQUEL on signale une voix (voir la comparaison) : la
# duree du references.csv vient de la transcription, AVANT rognage des bords --
# elle depasse donc normalement le WAV de quelques dixiemes, parfois 1,9 s. Un
# ecart de 2 s n'est plus un arrondi : c'est le signe d'un texte colle a un
# AUTRE enregistrement (cas Theodore, 24/10/2026 : 19,86 s annoncees, 13,67 s
# dans le fichier).
ECART_DUREE_A_LIRE_S = 2.0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def _montrer(liste, quoi):
    """Affiche les premiers elements d'une liste d'ecarts (le reste est compte)."""
    for element in liste[:MAX_MONTRES]:
        print('          ' + quoi + ' : ' + element)
    if len(liste) > MAX_MONTRES:
        print('          ... et %d autres' % (len(liste) - MAX_MONTRES))


# ---------------------------------------------------------------------------
# 1. Le catalogue (la source de verite pour les menus et la lecture)
# ---------------------------------------------------------------------------

def charger_catalogue():
    """{famille: {identifiant: entree}} depuis modules/tts.py, et les doublons."""
    from modules.tts import (QWEN_VOICES, KYUTAI_VOICES, XTTS_VOICES,
                             NEUTTS_VOICES, POCKET_VOICES)

    familles = [('qwen', QWEN_VOICES), ('kyutai', KYUTAI_VOICES),
                ('xtts', XTTS_VOICES), ('neutts', NEUTTS_VOICES),
                ('pocket', POCKET_VOICES)]
    catalogue = {}
    doublons = {}
    for famille, liste in familles:
        entrees = {}
        dupes = []
        for voix in liste:
            identifiant = str(voix.get('id') or '').split(':', 1)[-1]
            if not identifiant:
                continue
            if identifiant in entrees:
                dupes.append(identifiant)
                continue
            entrees[identifiant] = voix
        catalogue[famille] = entrees
        doublons[famille] = dupes
    return catalogue, doublons


# ---------------------------------------------------------------------------
# 2. Le disque (ce que les services savent vraiment lire)
# ---------------------------------------------------------------------------

def _sans_suffixe(nom, suffixes):
    for suffixe in suffixes:
        if nom.endswith(suffixe):
            return nom[:-len(suffixe)]
    return None


def voix_qwen():
    """{id: chemin} des references Qwen (les deux suffixes du service)."""
    dossier = RACINE / 'qwen_tts_service' / 'voix'
    if not dossier.is_dir():
        return None
    trouvees = {}
    for fichier in sorted(dossier.glob('*_reference.wav')):
        identifiant = _sans_suffixe(fichier.name, SUFFIXES_QWEN)
        if identifiant:
            # Le service retient la version « _enhanced » si les deux existent.
            if identifiant not in trouvees or '_enhanced' in fichier.name:
                trouvees[identifiant] = fichier
    return trouvees


def textes_qwen():
    """({id avec texte}, {id: duree annoncee}) depuis le public puis le prive.

    Le PRIVE gagne, comme dans le service (servir_qwentts_cpp.py) : c'est une
    voix presente dans les deux fichiers qui compte.
    """
    dossier = RACINE / 'qwen_tts_service' / 'voix'
    textes = {}
    durees = {}
    for nom_fichier in ('references.csv', 'references_privees.csv'):
        chemin = dossier / nom_fichier
        if not chemin.exists():
            continue
        try:
            with open(chemin, 'r', encoding='utf-8', newline='') as flux:
                for ligne in csv.DictReader(flux, delimiter=';'):
                    fichier = (ligne.get('fichier') or '').strip()
                    identifiant = _sans_suffixe(fichier, SUFFIXES_QWEN)
                    if not identifiant:
                        continue
                    if (ligne.get('texte') or '').strip():
                        textes[identifiant] = True
                    try:
                        durees[identifiant] = float((ligne.get('duree') or '').strip())
                    except (TypeError, ValueError):
                        pass
        except Exception as erreur:
            print('  ATTENTION : %s illisible (%s)'
                  % (nom_fichier, str(erreur)[:80]))
    return set(textes), durees


def _duree_wav(chemin):
    """Duree reelle d'un WAV, ou None s'il est illisible."""
    import wave
    try:
        with wave.open(str(chemin), 'rb') as flux:
            return flux.getnframes() / float(flux.getframerate())
    except Exception:
        return None


def voix_kyutai():
    """{id: chemin} des empreintes Kyutai (voix_fr seulement)."""
    dossier = RACINE / 'kyutai_service' / 'voix_fr'
    if not dossier.is_dir():
        return None
    trouvees = {}
    for fichier in sorted(dossier.rglob('*.safetensors')):
        # Deux conventions dans le service : <id>_enhanced.wav.<marqueur>
        # (famille cml-tts) et <id>.wav.<marqueur> (autres familles).
        if '_enhanced.wav' in fichier.name:
            identifiant = fichier.name.split('_enhanced.wav')[0]
        elif '.wav.' in fichier.name:
            identifiant = fichier.name.split('.wav.')[0]
        else:
            continue
        trouvees.setdefault(identifiant, fichier)
    return trouvees


def voix_xtts():
    """{id: chemin} des extraits XTTS v2 (la version « _enhanced » gagne)."""
    dossier = RACINE / 'xtts_service' / 'voix_fr'
    if not dossier.is_dir():
        return None
    trouvees = {}
    for fichier in sorted(dossier.rglob('*.wav')):
        identifiant = fichier.stem
        if identifiant.endswith('_enhanced'):
            identifiant = identifiant[:-len('_enhanced')]
            trouvees[identifiant] = fichier
        else:
            trouvees.setdefault(identifiant, fichier)
    return trouvees


def voix_neutts():
    """({id: chemin}, {id avec texte}) des references NeuTTS.

    Les extraits CML s'appellent `<id>_enhanced_reference.wav` : le service
    retire `_reference.wav` PUIS `_enhanced` pour retrouver l'identifiant du
    catalogue (servir_neutts.py, meme regle que servir_xtts.py). Le texte, lui,
    est indexe sur le NOM DE FICHIER COMPLET (avec `_enhanced`).
    """
    dossier = RACINE / 'neutts_service' / 'references'
    if not dossier.is_dir():
        return None, set()

    def _identifiant(base):
        if base.endswith('_enhanced'):
            return base[:-len('_enhanced')]
        return base

    trouvees = {}
    avec_texte = set()
    for fichier in sorted(dossier.rglob('*_reference.wav')):
        base = fichier.name[:-len('_reference.wav')]
        if not base:
            continue
        identifiant = _identifiant(base)
        if not identifiant:
            continue
        trouvees.setdefault(identifiant, fichier)
        # Le texte : un <base>_reference.txt a cote du WAV (base AVEC _enhanced)...
        if (fichier.parent / (base + '_reference.txt')).exists():
            avec_texte.add(identifiant)
    # ... ou le references.csv du dossier (un par provenance).
    for chemin in sorted(dossier.rglob('references.csv')):
        try:
            with open(chemin, 'r', encoding='utf-8', newline='') as flux:
                for ligne in csv.DictReader(flux, delimiter=';'):
                    nom = (ligne.get('fichier') or '').strip()
                    base = (nom[:-len('_reference.wav')]
                            if nom.endswith('_reference.wav') else nom)
                    identifiant = _identifiant(base)
                    if identifiant and (ligne.get('texte') or '').strip():
                        avec_texte.add(identifiant)
        except Exception as erreur:
            print('  ATTENTION : %s illisible (%s)'
                  % (chemin.name, str(erreur)[:80]))
    return trouvees, avec_texte


def voix_pocket():
    """{id: chemin} des voix Pocket TTS."""
    dossier = RACINE / 'pocket_tts_service' / 'voix'
    if not dossier.is_dir():
        return None
    trouvees = {}
    for fichier in sorted(dossier.glob('*_reference.wav')):
        identifiant = fichier.name[:-len('_reference.wav')]
        if identifiant:
            trouvees.setdefault(identifiant, fichier)
    return trouvees


# ---------------------------------------------------------------------------
# 3. La comparaison, famille par famille
# ---------------------------------------------------------------------------

def comparer(famille, dossier_lisible, au_catalogue, sur_disque,
             textes=None, quoi_des_textes='TEXTE', durees=None):
    """Compare catalogue et disque pour une famille. Renvoie son nombre d'ecarts."""
    print('')
    print('%s -- %s' % (famille.upper(), dossier_lisible))
    ecarts_avant = ECHECS

    if sur_disque is None:
        print('  --    dossier absent : non verifiable (service pas installe ici)')
        return 0

    print('  OK    %d voix au catalogue, %d fichier(s) sur le disque'
          % (len(au_catalogue), len(sur_disque)))

    sans_fichier = sorted(i for i in au_catalogue if i not in sur_disque)
    verifier('aucune voix du catalogue sans fichier', not sans_fichier,
             '%d : %s' % (len(sans_fichier), ', '.join(sans_fichier[:MAX_MONTRES])))
    if sans_fichier:
        _montrer(sans_fichier, 'muette')

    orphelins = sorted(i for i in sur_disque if i not in au_catalogue)
    # Un fichier sans entree au catalogue n'est pas forcement une faute (essai,
    # voix retiree) : on le SIGNALE sans bloquer. C'est une voix que Laurent ne
    # peut pas choisir dans les menus, et c'est exactement le doute du 24/10.
    if orphelins:
        print('  A LIRE  %d fichier(s) sans entree au catalogue (invisibles'
              ' dans les menus) :' % len(orphelins))
        _montrer(orphelins, 'hors catalogue')
    else:
        print('  OK    aucun fichier sans entree au catalogue')

    if textes is not None:
        sans_texte = sorted(i for i in au_catalogue if i not in textes)
        verifier('chaque voix du catalogue a son %s' % quoi_des_textes,
                 not sans_texte,
                 '%d : %s' % (len(sans_texte), ', '.join(sans_texte[:MAX_MONTRES])))
        sans_texte_disque = sorted(i for i in sur_disque if i not in textes)
        verifier('chaque fichier a son %s' % quoi_des_textes,
                 not sans_texte_disque,
                 '%d : %s' % (len(sans_texte_disque),
                              ', '.join(sans_texte_disque[:MAX_MONTRES])))

    if durees:
        # LA DUREE ANNONCEE DANS LE TEXTE, FACE A CELLE DU FICHIER. Attention :
        # ce n'est PAS une egalite attendue. La duree du `references.csv` vient de
        # la TRANSCRIPTION (avant rognage des bords) : elle depasse donc souvent
        # le WAV, de 0,3 a 1,9 s, et c'est normal. On ne signale que les GRANDS
        # ecarts -- la ou le texte colle probablement a un AUTRE enregistrement.
        # C'est le cas Theodore du 24/10/2026 : sa ligne annonce 19,86 s, le
        # fichier en fait 13,67 s.
        ecarts_duree = []
        for identifiant in sorted(sur_disque):
            declaree = durees.get(identifiant)
            if declaree is None:
                continue
            reelle = _duree_wav(sur_disque[identifiant])
            if reelle is None:
                continue
            if abs(declaree - reelle) >= ECART_DUREE_A_LIRE_S:
                ecarts_duree.append((abs(declaree - reelle), identifiant,
                                     declaree, reelle))
        ecarts_duree.sort(reverse=True)
        if ecarts_duree:
            print('  A LIRE  %d voix ou la duree ANNONCEE s ecarte de %.1f s ou'
                  ' plus du fichier (texte d un autre audio ? extrait recoupe'
                  ' sans son texte ?) :'
                  % (len(ecarts_duree), ECART_DUREE_A_LIRE_S))
            for _, identifiant, declaree, reelle in ecarts_duree[:MAX_MONTRES]:
                print('          %s : annonce %.2f s, fichier %.2f s'
                      % (identifiant, declaree, reelle))
        else:
            print('  OK    aucune duree annoncee ne s ecarte de %.1f s ou plus'
                  ' du fichier' % ECART_DUREE_A_LIRE_S)

    return ECHECS - ecarts_avant


def preuve_de_detection():
    """Prouve que l'outil DETECTE vraiment un ecart.

    Un filet qui ne sait pas dire « echec » ne dit rien. On lui donne donc un
    faux catalogue et un faux disque, avec un cas connu d'avance : une voix
    muette (au catalogue, pas sur le disque) et un intrus (sur le disque, pas au
    catalogue). Rien de reel n'est lu ici, et cette preuve ne compte pas dans le
    bilan -- elle verifie l'outil, pas les voix.
    """
    global ECHECS
    print('')
    print('7) preuve de detection (faux noms, expres)')
    avant = ECHECS
    ecarts = comparer('preuve', 'dossier imaginaire',
                      {'Voix_A': {}, 'Voix_B': {}},
                      {'Voix_B': 'faux', 'Voix_C': 'faux'})
    ECHECS = avant
    if ecarts == 1:
        print('  OK    la voix muette (Voix_A) est bien signalee ECHEC,')
        print('        et l intrus (Voix_C) est bien signale A LIRE')
    else:
        print('  ECHEC la preuve de detection n a pas vu l ecart (%d)' % ecarts)
        ECHECS += 1


# ---------------------------------------------------------------------------
# 4. Le bilan
# ---------------------------------------------------------------------------

def main():
    print('=' * 68)
    print('VERIFICATION : le CATALOGUE des voix et le DISQUE disent la meme chose')
    print('=' * 68)
    print('(lecture seule : rien n\'est ecrit, aucun moteur n\'est allume)')

    catalogue, doublons = charger_catalogue()

    print('')
    print('0) le catalogue lui-meme')
    for famille in ('qwen', 'kyutai', 'xtts', 'neutts', 'pocket'):
        verifier('%s : aucun identifiant en double' % famille,
                 not doublons[famille],
                 ', '.join(doublons[famille][:MAX_MONTRES]))

    ecarts = {}
    textes_qwen_vus, durees_qwen_vues = textes_qwen()
    ecarts['qwen'] = comparer('qwen', 'qwen_tts_service\\voix',
                              catalogue['qwen'], voix_qwen(),
                              textes_qwen_vus, 'TEXTE (public ou prive)',
                              durees_qwen_vues)
    ecarts['kyutai'] = comparer('kyutai', 'kyutai_service\\voix_fr',
                                catalogue['kyutai'], voix_kyutai())
    ecarts['xtts'] = comparer('xtts', 'xtts_service\\voix_fr',
                              catalogue['xtts'], voix_xtts())
    sur_disque_neutts, textes_neutts = voix_neutts()
    ecarts['neutts'] = comparer('neutts', 'neutts_service\\references',
                                catalogue['neutts'], sur_disque_neutts,
                                textes_neutts, 'TEXTE')
    ecarts['pocket'] = comparer('pocket', 'pocket_tts_service\\voix',
                                catalogue['pocket'], voix_pocket())

    print('')
    print('6) le compte, famille par famille')
    for famille in ('qwen', 'kyutai', 'xtts', 'neutts', 'pocket'):
        print('        %-7s catalogue %4d    ecarts %d'
              % (famille, len(catalogue[famille]), ecarts[famille]))
    print('        kokoro, piper, edge : pas de fichier par voix (modeles ou'
          ' cloud), non verifiables')

    print('')
    print('RAPPEL : une voix du catalogue SANS fichier = personnage muet ;')
    print('         un fichier SANS entree au catalogue = voix invisible dans'
          ' les menus.')
    preuve_de_detection()

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())



