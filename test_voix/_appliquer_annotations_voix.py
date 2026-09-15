# -*- coding: utf-8 -*-
"""Report des notes d'ecoute dans les catalogues de voix.

A lancer avec le Python du LECTEUR :
    python test_voix/_appliquer_annotations_voix.py            (apercu seul)
    python test_voix/_appliquer_annotations_voix.py --ecrire   (applique)

Pourquoi (decision de Laurent, 15/09/2026) : la fenetre « Ecouter les voix »
laisse annoter chaque voix (genre, etoiles, remarque) et range ces notes dans
data/annotations_voix.json -- un fichier LOCAL, hors Git, qui ne touche a rien.
Tant que ces notes ne sont pas reportees dans les catalogues, elles ne servent
qu'a l'affichage : ni les menus du lecteur, ni le pool automatique du casting
ne les voient. Ce script fait le report.

Ce qui est reporte :
  - les ETOILES (0 etoile = voix ECARTEE du pool automatique du casting) ;
  - le GENRE, converti de la convention d'ecoute (H/F) vers celle des
    catalogues (M/F) -- piege deja rencontre le 14/09/2026 avec les voix XTTS.
La REMARQUE libre n'est pas reportee (les catalogues n'ont pas de champ pour
elle) : elle reste dans data/annotations_voix.json et dans la fenetre.

Securite : rien n'est ecrit sans --ecrire, l'apercu montre TOUS les changements
avant, les deux fichiers sont sauvegardes (.bak_avant_annotations_voix) et
seules les lignes des voix annotees sont touchees.

Fichiers touches : main.py (FRENCH_VOICES = voix Edge) et modules/tts.py
(KOKORO_VOICES, KYUTAI_VOICES, XTTS_VOICES).
"""

import os
import re
import sys
import json
import shutil

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

ANNOTATIONS_PATH = os.path.join(RACINE, 'data', 'annotations_voix.json')
SUFFIXE_SAUVEGARDE = '.bak_avant_annotations_voix'

# Catalogue -> (fichier, description pour l'affichage)
CIBLES = (
    (os.path.join(RACINE, 'main.py'), 'voix Edge'),
    (os.path.join(RACINE, 'modules', 'tts.py'), 'Kokoro / Kyutai / XTTS'),
)

RE_STARS  = re.compile(r'"stars":\s*(\d+)')
RE_GENRE  = re.compile(r'"gender":\s*"([A-Za-z])"')


def charger_annotations():
    """Notes d'ecoute de Laurent (dict indexe par identifiant de voix)."""
    if not os.path.exists(ANNOTATIONS_PATH):
        print('Aucun fichier de notes : %s' % ANNOTATIONS_PATH)
        print('Rien a reporter (annotez d abord des voix dans la fenetre '
              '« Ecouter les voix »).')
        return {}
    with open(ANNOTATIONS_PATH, encoding='utf-8') as f:
        return json.load(f)


def convertir_genre(genre):
    """L'ecoute note H/F, les catalogues ecrivent M/F (piege connu)."""
    g = (genre or '').strip().upper()
    if g == 'H':
        return 'M'
    if g == 'F':
        return 'F'
    return ''


def preparer_changements(annotations):
    """Compare les notes aux catalogues et prepare les lignes a reecrire.

    Retourne (par_fichier, inconnues) :
      par_fichier : {chemin: [(identifiant, ligne_avant, ligne_apres, details)]}
      inconnues   : identifiants annotes absents des catalogues.
    """
    restants = dict(annotations)
    par_fichier = {}

    for chemin, _description in CIBLES:
        with open(chemin, encoding='utf-8', newline='') as f:
            lignes = f.readlines()

        changements = []
        for index, ligne in enumerate(lignes):
            m_stars = RE_STARS.search(ligne)
            m_genre = RE_GENRE.search(ligne)
            if not m_stars or not m_genre:
                continue

            # Identifiant de la voix sur cette ligne (les catalogues ont tous
            # la forme {"id": "xxx", ...}).
            m_id = re.search(r'"id":\s*"([^"]+)"', ligne)
            if not m_id:
                continue
            identifiant = m_id.group(1)
            if identifiant not in restants:
                continue

            note = restants.pop(identifiant)
            avant_stars = int(m_stars.group(1))
            avant_genre = m_genre.group(1).upper()
            apres_genre = convertir_genre(note.get('genre')) or avant_genre

            stars = note.get('stars', -1)
            apres_stars = avant_stars if int(stars) < 0 else int(stars)

            if apres_stars == avant_stars and apres_genre == avant_genre:
                continue

            nouvelle = ligne
            if apres_stars != avant_stars:
                nouvelle = RE_STARS.sub('"stars": %d' % apres_stars, nouvelle, count=1)
            if apres_genre != avant_genre:
                nouvelle = RE_GENRE.sub('"gender": "%s"' % apres_genre, nouvelle, count=1)

            details = []
            if apres_stars != avant_stars:
                details.append('etoiles %d -> %d' % (avant_stars, apres_stars))
            if apres_genre != avant_genre:
                details.append('genre %s -> %s' % (avant_genre, apres_genre))

            changements.append((identifiant, index, avant_stars, apres_stars,
                                nouvelle, details))

        par_fichier[chemin] = (lignes, changements)

    return par_fichier, sorted(restants)


def ecrire(chemin, lignes, changements):
    """Ecrit le fichier apres sauvegarde. Seules les lignes annotees changent."""
    sauvegarde = chemin + SUFFIXE_SAUVEGARDE
    shutil.copyfile(chemin, sauvegarde)
    for _id, index, _a, _b, nouvelle, _d in changements:
        lignes[index] = nouvelle
    with open(chemin, 'w', encoding='utf-8', newline='') as f:
        f.writelines(lignes)
    return sauvegarde


def main():
    ecrire_vraiment = '--ecrire' in sys.argv
    annotations = charger_annotations()
    if not annotations:
        return 0

    print('=' * 70)
    print('REPORT DES NOTES D ECOUTE DANS LES CATALOGUES')
    print('Fichier de notes : %s' % ANNOTATIONS_PATH)
    print('%d voix annotees.' % len(annotations))
    print('=' * 70)

    par_fichier, inconnues = preparer_changements(annotations)

    total = 0
    ecartees = []
    for chemin, description in CIBLES:
        lignes, changements = par_fichier[chemin]
        print('')
        print('--- %s (%s)' % (os.path.relpath(chemin, RACINE), description))
        if not changements:
            print('    aucun changement')
            continue
        for identifiant, _index, avant, apres, _nouvelle, details in changements:
            print('    %-38s %s' % (identifiant, ', '.join(details)))
            if apres == 0 and avant != 0:
                ecartees.append(identifiant)
        total += len(changements)

    if inconnues:
        print('')
        print('--- voix annotees absentes des catalogues (ignorees)')
        for identifiant in inconnues:
            print('    %s' % identifiant)

    print('')
    print('Rappel : la REMARQUE libre reste dans %s'
          % os.path.relpath(ANNOTATIONS_PATH, RACINE))
    print('(les catalogues n ont que genre et etoiles).')

    if total == 0:
        print('')
        print('TOUT EST A JOUR : rien a ecrire.')
        return 0

    if ecartees:
        print('')
        print('ECARTEES du pool automatique du casting (0 etoile) : %s'
              % ', '.join(ecartees))

    if not ecrire_vraiment:
        print('')
        print('APERCU SEUL : %d changement(s) prepare(s).' % total)
        print('Pour appliquer :  python test_voix/_appliquer_annotations_voix.py --ecrire')
        return 0

    for chemin, _description in CIBLES:
        lignes, changements = par_fichier[chemin]
        if changements:
            sauvegarde = ecrire(chemin, lignes, changements)
            print('')
            print('Ecrit : %s (%d changement(s))'
                  % (os.path.relpath(chemin, RACINE), len(changements)))
            print('Sauvegarde : %s' % os.path.relpath(sauvegarde, RACINE))

    print('')
    print('TERMINE : %d changement(s) applique(s).' % total)
    print('Verifier le pool automatique : python test_voix/test_pool_casting.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
