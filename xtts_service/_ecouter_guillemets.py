# -*- coding: utf-8 -*-
"""Lot d'ecoute : comment XTTS v2 se comporte avec les guillemets « ».

A lancer avec le Python du LECTEUR, MOTEUR XTTS ALLUME :
    python xtts_service/_ecouter_guillemets.py
    python xtts_service/_ecouter_guillemets.py --voix 12205_11650_000004-0002

Pourquoi (constat de Laurent, 14/09/2026, a l'ecoute d'un livre) : XTTS
« bute » sur les guillemets francais. Le lecteur envoie la phrase entiere,
telle qu'elle est attribuee au personnage, guillemets compris.

Ce lot fait ecouter LA MEME phrase traitee de plusieurs facons, pour trancher
A L'OREILLE avant de figer un remede (c'est la methode des autres lots du
projet : une seule phrase, identique pour toutes les variantes, sinon la
comparaison n'a pas de sens) :

  A. la phrase telle qu'elle part aujourd'hui, avec « »          (reference)
     puis SANS guillemets / guillemets remplaces par une VIRGULE / par une ESPACE
  B. une phrase ou un point d'interrogation tombe AU MILIEU du dialogue
     (le cas « citation ouverte » surveille au BACKLOG), avec puis sans guillemets
  C. un dialogue au TIRET cadratin, tel quel puis tiret retire

Tout est ecrit dans xtts_service/sortie_ecoute_guillemets/ (hors Git), avec
un index_ecoute.txt ou noter le verdict variante par variante.

Rien n'est modifie dans le moteur : ce script se contente d'appeler /tts.
"""

import io
import json
import os
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

SERVICE = os.environ.get('NIMM_XTTS_URL', 'http://127.0.0.1:8083')
ICI = Path(__file__).resolve().parent
SORTIE = ICI / 'sortie_ecoute_guillemets'
# Voix de reference par defaut : Bertrand, une des 60 voix XTTS (3 etoiles).
VOIX_DEFAUT = '1770_1028_000036-0002'

# Guillemets : francais, droits, et les « courbes » anglais rencontres dans
# certains EPUB.
GUILLEMETS = ('\u00ab', '\u00bb', '"', '\u201c', '\u201d')

# Tiret cadratin (dialogue a la francaise) : les deux formes rencontrees.
TIRETS = ('\u2014', '\u2013')


def _normaliser(texte):
    """Compacte les espaces multiples : le moteur aime les phrases propres."""
    return ' '.join(texte.split())


def nettoyer(texte, quoi, remplacement):
    """Retire (ou remplace) un jeu de signes, puis compacte les espaces."""
    resultat = texte
    for signe in quoi:
        if remplacement == '':
            resultat = resultat.replace(signe, ' ')
        else:
            resultat = resultat.replace(signe, remplacement)
    return _normaliser(resultat)


# --------------------------------------------------------------
# LES PHRASES DE TEST (choisies comme dans un vrai roman)
# --------------------------------------------------------------

PHRASE_A = ('\u00ab Vous \u00eates s\u00fbr de vous, monsieur ? \u00bb '
            'demanda-t-il en souriant.')
PHRASE_B = ('\u00ab Que voulez-vous ? dit-il. Il est d\u00e9j\u00e0 trop tard ! '
            '\u00bb')
PHRASE_C = ('\u2014 Vous \u00eates s\u00fbr de vous, monsieur ? '
            'demanda-t-il en souriant.')
# Phrase D : tiret cadratin d'INCISE (au milieu, pas en tete de replique). Le
# remede le remplace par une virgule : c'est ce cas qu'il faut valider ici.
PHRASE_D = ('Il arriva \u2014 enfin \u2014 \u00e0 midi, tremp\u00e9 '
            'jusqu\u2019aux os.')


def variantes():
    """[(rang, nom de fichier, explication, texte envoye au moteur)]"""
    lot = [
        ('01_A_guillemets_brut',
         'phrase A telle qu elle part aujourd hui (reference)',
         PHRASE_A),
        ('02_A_sans_guillemets',
         'phrase A, guillemets RETIRES',
         nettoyer(PHRASE_A, GUILLEMETS, '')),
        ('03_A_guillemets_virgule',
         'phrase A, guillemets remplaces par une VIRGULE',
         nettoyer(PHRASE_A, GUILLEMETS, ',')),
        ('04_A_guillemets_espace',
         'phrase A, guillemets remplaces par une ESPACE',
         nettoyer(PHRASE_A, GUILLEMETS, '  ')),
        ('05_B_ponctuation_brut',
         'phrase B (point d interrogation AU MILIEU du dialogue), reference',
         PHRASE_B),
        ('06_B_ponctuation_sans',
         'phrase B, guillemets RETIRES',
         nettoyer(PHRASE_B, GUILLEMETS, '')),
        ('07_C_tiret_brut',
         'phrase C (tiret cadratin), telle quelle',
         PHRASE_C),
        ('08_C_tiret_retire',
         'phrase C, tiret RETIRE',
         nettoyer(PHRASE_C, TIRETS, '')),
        ('09_D_incise_brute',
         'phrase D : tiret d INCISE (au milieu), tel quel -- jamais teste avant',
         PHRASE_D),
    ]
    return [(fichier, explication, _normaliser(texte))
            for fichier, explication, texte in lot]


# --------------------------------------------------------------
# DIALOGUE AVEC LE MOTEUR (HTTP, bibliotheque standard)
# --------------------------------------------------------------

def _get_json(chemin, delai=10.0):
    with urllib.request.urlopen(SERVICE + chemin, timeout=delai) as reponse:
        return json.loads(reponse.read().decode('utf-8'))


def sante(delai=10.0):
    """Etat du moteur, ou None s'il ne repond pas."""
    try:
        return _get_json('/sante', delai=delai)
    except Exception:
        return None


def generer(texte, voix, delai=180.0):
    """Demande la lecture d'un texte. Renvoie les octets du WAV."""
    corps = json.dumps({'texte': texte, 'voix': voix}).encode('utf-8')
    requete = urllib.request.Request(
        SERVICE + '/tts', data=corps,
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(requete, timeout=delai) as reponse:
            return reponse.read()
    except urllib.error.HTTPError as erreur:
        detail = ''
        try:
            detail = json.loads(erreur.read().decode('utf-8')).get('erreur', '')
        except Exception:
            pass
        raise RuntimeError('le moteur a refuse (HTTP %s) %s'
                           % (erreur.code, detail))
    except Exception as erreur:
        raise RuntimeError('moteur injoignable : %s' % erreur)


def duree_wav(octets):
    """Duree en secondes d'un WAV (0 si l'en-tete est illisible)."""
    try:
        with wave.open(io.BytesIO(octets), 'rb') as son:
            return son.getnframes() / float(son.getframerate())
    except Exception:
        return 0.0


def analyser(octets, seuil=0.012, fenetre=0.02, mini=0.15):
    """Mesure objective d'un WAV : (duree, nombre de segments, silences).

    Un « silence » est une plage d'au moins 150 ms sous le seuil d'amplitude.
    C'est ce qui permet de reperer un defaut SANS ecouter : un son parasite du
    moteur se voit a une duree qui s'allonge et a des silences anormaux.
    Renvoie (duree, segments, [(position, duree)]) ; (0, 0, []) si numpy
    manque (l'analyse est alors simplement absente de l'index).
    """
    try:
        import numpy as np
    except Exception:
        return duree_wav(octets), 0, []
    try:
        with wave.open(io.BytesIO(octets), 'rb') as son:
            frequence = son.getframerate()
            donnees = np.frombuffer(son.readframes(son.getnframes()),
                                    dtype='<i2').astype('float32') / 32768.0
    except Exception:
        return duree_wav(octets), 0, []
    duree = len(donnees) / float(frequence)
    taille = int(fenetre * frequence)
    rms = []
    for debut in range(0, len(donnees) - taille + 1, taille):
        bloc = donnees[debut:debut + taille]
        rms.append(float(np.sqrt(np.mean(bloc * bloc))))
    silencieux = [valeur < seuil for valeur in rms]

    silences, debut = [], None
    for i, vide in enumerate(silencieux + [False]):
        if vide and debut is None:
            debut = i
        elif not vide and debut is not None:
            longueur = (i - debut) * fenetre
            if longueur >= mini:
                silences.append((debut * fenetre, longueur))
            debut = None

    segments, precedent = 0, True
    for vide in silencieux:
        if not vide and precedent:
            segments += 1
        precedent = vide
    return duree, segments, silences


# --------------------------------------------------------------
# LE LOT
# --------------------------------------------------------------

def ecrire_index(voix, resultats, inacheves):
    """index_ecoute.txt : ce qui a ete envoye, ce qui est mesure, et le verdict."""
    lignes = [
        '# Lot d ecoute : XTTS v2 et les guillemets (15/09/2026)',
        '# Voix : %s' % voix,
        '#',
        "# Objet : la MEME phrase, seule la ponctuation de dialogue change. On",
        '# cherche le son bizarre entendu par Laurent a l endroit des',
        '# guillemets (constat du 14/09/2026).',
        '#',
        '# A FAIRE : ecouter dans l ordre (01, 02, 03...). Pour chaque fichier,',
        '# ecrire OK ou BIZARRE, et ou le defaut se situe (debut, milieu, fin).',
        '# Les comparaisons qui decident : 01 contre 02 (guillemets en place ou',
        "# non), puis 05 contre 06 (avec un point d interrogation au milieu du",
        '# dialogue).',
        '#',
        '# La ligne « mesure » est objective (duree, nombre de morceaux de',
        '# parole, silences) : elle sert de reperes, elle ne remplace pas',
        '# l oreille. A savoir : le moteur n est pas parfaitement repetable --',
        '# 02 et 04 ont le MEME texte, leurs petites differences donnent la',
        '# marge de variation naturelle.',
        '#',
        '# fichier                    duree   verdict (OK / BIZARRE + ou)',
        '# ---------------------------------------------------------------',
        '#',
        '# Depuis le remede (nettoyer_pour_xtts, dans le service), les fichiers',
        '# 01, 05, 07 et 09 sont NETTOYES par le moteur avant lecture : ils',
        '# doivent maintenant sonner comme 02 ou 08. C est cela qu on verifie ici.',
        '# Le sous-dossier avant_remede/ garde les memes fichiers AVANT le',
        '# remede, avec le verdict d ecoute de Laurent du 15/09/2026.',
    ]
    for nom, explication, duree, texte, segments, silences in resultats:
        lignes.append('  %-25s %5.1f s  %s' % (nom + '.wav', duree, ' ' * 26))
        lignes.append('    %s' % explication)
        lignes.append('    texte envoye : %s' % texte)
        detail = '%d morceaux de parole' % segments
        if silences:
            detail += ' ; silences : ' + ', '.join(
                '%.2f s a %.2f s' % (longueur, position)
                for position, longueur in silences)
        lignes.append('    mesure : %s' % detail)
        lignes.append('')
    if inacheves:
        lignes.append('# NON GENERE :')
        for nom, explication in inacheves:
            lignes.append('  %-25s %s' % (nom, explication))
        lignes.append('')
    return '\n'.join(lignes) + '\n'


def ecrire_a_noter(voix, resultats):
    """A_NOTER.txt : la version la plus simple possible, a remplir a la main.

    Pourquoi (remarque de Laurent, 15/09/2026) : l'index complet est trop
    charge pour ecrire ses remarques dessus (alignements, retours a la ligne).
    Ici : UNE ligne par fichier, il n'y a plus qu'a ecrire apres la fleche.
    """
    lignes = [
        'LOT A ECOUTER -- voix %s' % voix,
        '',
        "Ecouter dans l'ordre. Apres chaque fleche, ecrire ce qu'on entend",
        "(ok, bizarre au debut, inspiration a la fin, mot mange...).",
        "La ligne courte entre parentheses dit ce que le fichier teste.",
        '',
    ]
    for nom, explication, _duree, _texte, _segments, _silences in resultats:
        lignes.append('%-28s (%s)' % (nom + '.wav', explication))
        lignes.append('    ->  ' + '.' * 62)
        lignes.append('')
    return '\n'.join(lignes) + '\n'


def main():
    args = sys.argv[1:]
    voix = VOIX_DEFAUT
    if '--voix' in args:
        rang = args.index('--voix')
        if rang + 1 < len(args):
            voix = args[rang + 1]

    etat = sante()
    if etat is None:
        print('Le moteur XTTS ne repond pas sur %s.' % SERVICE)
        print('D abord : double-clic sur START.bat (ou DEMARRER_XTTS.bat),')
        print('puis relancer ce script quand la fenetre du moteur dit')
        print('« XTTS v2 pret ».')
        return 1

    print('Moteur XTTS : %s (%s voix, appareil %s)'
          % ('pret' if etat.get('pret') else 'EN CHARGEMENT',
             etat.get('voix'), etat.get('appareil')))
    if not etat.get('pret'):
        print('Attendre la fin du chargement (10 a 20 s), puis relancer.')
        return 1

    if '--liste-voix' in args:
        voix_dispo = _get_json('/voix').get('voix') or []
        print('%d voix disponibles. Par exemple : %s'
              % (len(voix_dispo), ', '.join(voix_dispo[:5])))
        return 0

    SORTIE.mkdir(exist_ok=True)
    for ancien in SORTIE.glob('*.wav'):
        ancien.unlink()

    print('')
    print('Voix : %s' % voix)
    print('Sortie : %s' % SORTIE)
    print('')

    resultats, inacheves = [], []
    lot = variantes()
    for rang, (nom, explication, texte) in enumerate(lot, start=1):
        print('%2d/%d  %s' % (rang, len(lot), explication))
        try:
            wav = generer(texte, voix)
        except RuntimeError as erreur:
            print('      -> %s' % erreur)
            inacheves.append((nom, explication))
            continue
        (SORTIE / (nom + '.wav')).write_bytes(wav)
        duree, segments, silences = analyser(wav)
        print('      -> %s.wav  %.1f s  %d octets  (%d morceaux de parole)'
              % (nom, duree, len(wav), segments))
        resultats.append((nom, explication, duree, texte, segments, silences))

    index = SORTIE / 'index_ecoute.txt'
    index.write_text(ecrire_index(voix, resultats, inacheves), encoding='utf-8')
    a_noter = SORTIE / 'A_NOTER.txt'
    a_noter.write_text(ecrire_a_noter(voix, resultats), encoding='utf-8')

    print('')
    print('%d fichier(s) ecrit(s) dans %s' % (len(resultats), SORTIE))
    if inacheves:
        print('%d NON genere(s) : %s'
              % (len(inacheves), ', '.join(n for n, _e in inacheves)))
    print('A annoter : %s   (version simple : %s)' % (index, a_noter))
    return 0 if resultats else 1


if __name__ == '__main__':
    sys.exit(main())
