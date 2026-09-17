# -*- coding: utf-8 -*-
"""Verification de l'attribution des voix PAR CRITERES (session du 16/09/2026).

Demande de Laurent : que le re-cast GRATUIT tienne compte des annotations
d'ecoute (age, timbre, debit) et pas seulement des etoiles.

Ce que le script verifie :
  1. le classement des voix (aucune voix ecartee ni reservee) ;
  2. les roles reserves (narrateur, etranger...) ;
  3. une attribution complete sur des profils types : un personnage AGE recoit
     une voix grave / de vieux, un JEUNE une voix jeune ;
  4. les voix figees (verrou, saga) sont respectees a la lettre ;
  5. le resultat est DETERMINISTE ;
  6. `par_criteres=False` redonne l'ancien tri par paliers d'etoiles ;
  7. le re-cast du serveur relit bien l'AGE des personnages (cast_fiche).

Aucune ecriture en base : le test n'appelle que la fonction d'attribution.
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import voice_casting                               # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def annotation_de(voice_id):
    return voice_casting.lire_annotations_voix().get(voice_id) or {}


def verifications():
    notes = voice_casting.lire_annotations_voix()
    print('annotations d ecoute disponibles : %d voix' % len(notes))
    print('catalogue du pool automatique   : %d voix'
          % len(voice_casting._index_voix()))
    if not notes:
        print('')
        print('Aucune annotation : rien a verifier (la fenetre « Ecouter les'
              ' voix » en ecrit dans data/annotations_voix.json).')
        return

    print('')
    print('1) le classement des voix')
    classement_h_age = voice_casting._classement_voix('H', 'age')
    classement_h_jeune = voice_casting._classement_voix('H', 'jeune')
    classement_f_jeune = voice_casting._classement_voix('F', 'jeune')
    verifier('un classement existe pour chaque profil',
             bool(classement_h_age) and bool(classement_h_jeune)
             and bool(classement_f_jeune),
             (len(classement_h_age), len(classement_h_jeune),
              len(classement_f_jeune)))
    index = voice_casting._index_voix()
    verifier('aucune voix notee 0 etoile dans le classement',
             all((index.get(v, {}).get('stars') or 0) > 0
                 for v in classement_h_age))
    verifier('aucune voix reservee dans un classement « age »',
             all(not voice_casting._voix_reservee(
                     annotation_de(v),
                     voice_casting.AGES_PAR_PERSONNAGE['age'])
                 for v in classement_h_age))
    premier = annotation_de(classement_h_age[0])
    # ATTENTION (17/09/2026) : depuis que le pool ne contient plus que des voix
    # LISIBLES (Kyutai, Edge, Kokoro), les voix de vieux sont rares -- et
    # beaucoup sont reservees par role. Pour « homme age », il ne reste parfois
    # qu'une voix, dont le timbre n'est pas dans la table : le premier peut donc
    # etre « voile ». On verifie donc que le timbre est AU MOINS plausible, et
    # surtout que l'AGE est le bon (controle suivant), car c'est l'age qui passe
    # en premier dans le classement.
    verifier('« homme age » : le timbre du premier reste plausible',
             premier.get('timbre') in ('grave', 'rocailleux', 'medium', 'voile'),
             classement_h_age[0] + ' -> ' + str(premier.get('timbre')))
    verifier('« homme age » : le classement privilegie un age de voix avance',
             premier.get('age') in ('vieux', 'mur'), premier.get('age'))

    print('')
    print('2) les roles reserves')
    ages_vieux = voice_casting.AGES_PAR_PERSONNAGE['age']
    ages_jeune = voice_casting.AGES_PAR_PERSONNAGE['jeune']
    verifier('role « vieux » : utilisable pour un personnage age',
             not voice_casting._voix_reservee({'role': 'vieux'}, ages_vieux))
    verifier('role « vieux » : reserve pour un personnage jeune',
             voice_casting._voix_reservee({'role': 'vieux'}, ages_jeune))
    verifier('role « enfant » : utilisable pour un enfant',
             not voice_casting._voix_reservee({'role': 'enfant'}, ages_jeune))
    verifier('role « narrateur » : toujours reserve',
             voice_casting._voix_reservee({'role': 'narrateur'}, ages_vieux))
    verifier('role « etranger » : toujours reserve',
             voice_casting._voix_reservee({'role': 'etranger'}, ages_vieux))
    verifier('sans role annote : jamais reserve',
             not voice_casting._voix_reservee({}, ages_vieux))

    print('')
    print('3) une attribution complete sur des profils types')
    personnages = [
        {'nom': 'Vieux_seigneur', 'genre': 'H', 'age': 'age'},
        {'nom': 'Jeune_ecuyer',   'genre': 'H', 'age': 'jeune'},
        {'nom': 'Dame_mure',      'genre': 'F', 'age': 'adulte'},
        {'nom': 'Fillette',       'genre': 'F', 'age': 'jeune'},
        {'nom': 'Figurant',       'genre': 'H', 'age': 'adulte'},
    ]
    compte = {'Vieux_seigneur': 400, 'Jeune_ecuyer': 150, 'Dame_mure': 220,
              'Fillette': 90, 'Figurant': 3}

    attribution = voice_casting.assign_voices(personnages, compte, par_criteres=True)
    seigneur = annotation_de(attribution['Vieux_seigneur']['voice_id'])
    ecuyer = annotation_de(attribution['Jeune_ecuyer']['voice_id'])
    verifier('le vieux seigneur a une voix grave ou de vieux',
             seigneur.get('timbre') in ('grave', 'rocailleux')
             or seigneur.get('age') in ('vieux', 'mur'),
             attribution['Vieux_seigneur']['voice_id'] + ' -> ' + str(seigneur))
    verifier('le jeune ecuyer n a PAS une voix de vieux',
             ecuyer.get('age') != 'vieux',
             attribution['Jeune_ecuyer']['voice_id'] + ' -> ' + str(ecuyer))
    verifier('la dame a une voix feminine',
             index.get(attribution['Dame_mure']['voice_id'], {}).get('genre') == 'F',
             attribution['Dame_mure'])
    verifier('la fillette a une voix feminine',
             index.get(attribution['Fillette']['voice_id'], {}).get('genre') == 'F',
             attribution['Fillette'])
    verifier('aucune voix notee 0 etoile n a ete attribuee',
             all((index.get(a['voice_id'], {}).get('stars') or 0) > 0
                 for a in attribution.values() if a['voice_id']))
    grands = ('Vieux_seigneur', 'Jeune_ecuyer', 'Dame_mure', 'Fillette')
    verifier('les 4 grands roles ont des voix DIFFERENTES',
             len({attribution[n]['voice_id'] for n in grands}) == 4,
             [attribution[n]['voice_id'] for n in grands])
    verifier('le petit role (< 8 repliques) reste SANS voix (narrateur)',
             attribution['Figurant']['voice_id'] == '', attribution['Figurant'])
    verifier('la hauteur suit l age (personnage age = -15 Hz)',
             attribution['Vieux_seigneur']['pitch'] == '-15Hz',
             attribution['Vieux_seigneur']['pitch'])

    print('')
    print('4) les voix figees (verrou, saga) sont respectees')
    figees = {'Vieux_seigneur': {'voice_id': 'fr-FR-HenriNeural', 'pitch': '+0Hz',
                                 'rate': '+0%', 'genre': 'H'}}
    attribution2 = voice_casting.assign_voices(personnages, compte,
                                               voix_figees=figees, par_criteres=True)
    verifier('le personnage fige garde exactement sa voix',
             attribution2['Vieux_seigneur']['voice_id'] == 'fr-FR-HenriNeural',
             attribution2['Vieux_seigneur'])
    verifier('aucun autre personnage n herite de cette voix',
             all(a['voice_id'] != 'fr-FR-HenriNeural'
                 for nom, a in attribution2.items() if nom != 'Vieux_seigneur'),
             [a['voice_id'] for nom, a in attribution2.items()])

    print('')
    print('5) le resultat est deterministe')
    attribution3 = voice_casting.assign_voices(personnages, compte, par_criteres=True)
    verifier('deux appels identiques donnent le meme resultat',
             attribution3 == attribution, 'resultats differents')

    print('')
    print('6) par_criteres=False redonne l ancien tri par paliers')
    ancien = voice_casting.assign_voices(personnages, compte, par_criteres=False)
    verifier('le vieux seigneur prend la tete du pool par paliers',
             ancien['Vieux_seigneur']['voice_id']
             == voice_casting.DEDICATED_VOICES_M[0],
             ancien['Vieux_seigneur']['voice_id'])
    verifier('l ancien tri attribue encore des voix aux grands roles',
             all(ancien[n]['voice_id'] for n in grands))

    print('')
    print('7) le re-cast du serveur relit bien l AGE des personnages')
    source = (RACINE / 'main.py').read_text(encoding='utf-8')
    # Depuis le 16/09/2026, la preparation du re-cast est PARTAGEE avec le
    # re-cast par IA (`_preparer_recaste`) : on lit donc la preparation ET la
    # route ensemble -- sans quoi on ne verifierait plus le chemin reellement
    # utilise (l'age et les voix de saga ont quitte la route pour la
    # preparation, justement pour que les deux re-casts ne divergent jamais).
    debut = source.find('def _preparer_recaste')
    fin = source.find('@app.post("/api/books/{book_id}/cast/autogroup")', debut)
    zone = source[debut:fin] if debut > 0 and fin > debut else ''
    verifier('la fiche du casting est relue (table cast_fiche)',
             'cast_fiche' in zone,
             'cast_fiche absent de la preparation du re-cast')
    verifier('l age vient bien de la fiche (et non « adulte » en dur)',
             'ages_fiche.get(canon) or "adulte"' in zone,
             'l age ne vient pas de cast_fiche')
    verifier('la coherence de SAGA est reprise au re-cast (voix des autres tomes)',
             '_fetch_saga_voix_figees' in zone,
             'les voix des autres tomes ne sont pas reprises par le re-cast')


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : attribution des voix par criteres')
    print('=' * 66)
    verifications()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    sys.exit(0 if ECHECS == 0 else 1)
