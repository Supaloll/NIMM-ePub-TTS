# -*- coding: utf-8 -*-
"""Bilan des annotations d'ecoute (criteres fixes) : que peut-on en faire ?

Lecture seule, aucun appel reseau. Repond aux questions qu'on se pose AVANT
d'ecrire une attribution assistee :
  - quels criteres sont renseignes, et a quel point (couverture) ;
  - quelles valeurs existent vraiment (et lesquelles manquent) ;
  - pour un profil de personnage donne, combien de voix sont disponibles ;
  - quelles annotations visent des voix absentes du catalogue du moment.

Usage : python test_voix/_etat_annotations_voix.py
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

import main                                                     # noqa: E402
from modules import tts                                         # noqa: E402

ANNOTATIONS = RACINE / 'data' / 'annotations_voix.json'
CRITERES = list(main.CRITERES_VOIX_CLES)


def catalogue_complet():
    """{identifiant: fiche} pour tous les moteurs du lecteur."""
    fiches = {}
    for source in (main.FRENCH_VOICES, tts.KOKORO_VOICES, tts.XTTS_VOICES,
                   tts.KYUTAI_VOICES, tts.PIPER_VOICES):
        for voix in source:
            fiches[voix['id']] = voix
    return fiches


def genre_de(fiche):
    g = (fiche or {}).get('gender') or ''
    return 'H' if g == 'M' else g


def main_bilan():
    fiches = catalogue_complet()
    notes = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))

    print('Annotations : %d voix annotees (catalogue du lecteur : %d voix)'
          % (len(notes), len(fiches)))
    print('')

    print('1) COUVERTURE PAR CRITERE')
    for cle in ['genre', 'stars'] + CRITERES:
        remplies = [v for v in notes.values() if v.get(cle) not in ('', None, -1)]
        # stars a part : 0 est une vraie valeur (voix a ecarter)
        if cle == 'stars':
            remplies = [v for v in notes.values()
                        if isinstance(v.get('stars'), int) and v.get('stars') >= 0]
        print('   %-9s %3d / %d' % (cle, len(remplies), len(notes)))
    print('')

    print('2) QUELLES VALEURS EXISTENT (voix masculines / feminines)')
    for cle in ['age', 'timbre', 'debit', 'registre', 'accent', 'role']:
        par_valeur = defaultdict(lambda: [0, 0])
        for ident, note in notes.items():
            valeur = note.get(cle)
            if not valeur:
                continue
            genre = note.get('genre') or genre_de(fiches.get(ident))
            par_valeur[valeur][0 if genre == 'F' else 1] += 1
        ligne = ', '.join('%s %dF/%dH' % (val, nb[0], nb[1])
                          for val, nb in sorted(par_valeur.items(),
                                                key=lambda x: -sum(x[1])))
        print('   %-9s %s' % (cle, ligne or '(aucune)'))
    print('')

    print('3) VALEURS ANNONCEES PAR LE SERVEUR MAIS JAMAIS UTILISEES')
    for critere in main.CRITERES_VOIX:
        cle, libelle, valeurs = critere
        utilisees = {n.get(cle) for n in notes.values() if n.get(cle)}
        absentes = [v for v, _ in valeurs if v not in utilisees]
        if absentes:
            print('   %-22s %s' % (libelle, ', '.join(absentes)))
    print('')

    print('4) PROFILS UTILES POUR UN CASTING (voix disponibles)')
    profils = [
        ('homme, vieux, grave', 'H', {'age': ['vieux', 'mur'], 'timbre': ['grave']}),
        ('homme, vieux (tout timbre)', 'H', {'age': ['vieux', 'mur']}),
        ('homme, jeune', 'H', {'age': ['enfant', 'jeune']}),
        ('homme, grave (tout age)', 'H', {'timbre': ['grave']}),
        ('femme, jeune', 'F', {'age': ['enfant', 'jeune']}),
        ('femme, vieille', 'F', {'age': ['vieux', 'mur']}),
        ('femme, cristallin ou aigu', 'F', {'timbre': ['cristallin', 'aigu']}),
        ('voix avec accent non neutre', '', {'accent': ['paysan', 'canadien',
                                                       'anglais', 'allemand',
                                                       'espagnol', 'italien',
                                                       'autre']}),
        ('voix reservees a un role', '', {'role': ['narrateur', 'enfant',
                                                   'vieux', 'etranger',
                                                   'secondaire']}),
        ('HOMME a accent espagnol/italien', 'H',
         {'accent': ['espagnol', 'italien']}),
        ('HOMME a accent canadien', 'H', {'accent': ['canadien']}),
        ('HOMME a accent anglais', 'H', {'accent': ['anglais']}),
        ('FEMME a accent espagnol/italien', 'F',
         {'accent': ['espagnol', 'italien']}),
    ]
    for libelle, genre_voulu, attendus in profils:
        trouvees = []
        for ident, note in notes.items():
            if genre_voulu:
                genre = note.get('genre') or genre_de(fiches.get(ident))
                if genre != genre_voulu:
                    continue
            if all(note.get(cle) in valeurs for cle, valeurs in attendus.items()):
                trouvees.append((fiches.get(ident, {}).get('name', ident),
                                 note.get('stars', '?')))
        trouvees.sort(key=lambda x: (-(x[1] if isinstance(x[1], int) else 0), x[0]))
        print('   %-30s %2d  %s' % (libelle, len(trouvees),
                                    ', '.join('%s(%s)' % (n, s) for n, s in trouvees[:8])))
    print('')

    print('5) ET LES VOIX NOTABLES A PART')
    ecartees = [ident for ident, n in notes.items() if n.get('stars') == 0]
    orphelines = [ident for ident in notes if ident not in fiches]
    print('   voix ecartees (0 etoile)          : %d' % len(ecartees))
    print('   annotations sans voix au catalogue : %d %s'
          % (len(orphelines), ', '.join(orphelines[:6])))


main_bilan()
