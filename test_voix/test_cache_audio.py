# -*- coding: utf-8 -*-
"""Verification du cache audio : compte et purge a la main (20/09/2026).

A lancer avec le Python du LECTEUR :
    python test_voix/test_cache_audio.py

Pourquoi (demande de Laurent, 18/09/2026) : le cache se purge tout seul par
quota, mais il n'avait AUCUN bouton pour le vider a la main -- et c'est
exactement ce qui manque quand on doute d'un rendu (le 18/09/2026, il a fallu
vider le dossier de cache a la main pour ecarter cette piste).

Ce que le test verifie : les deux fonctions qui servent le bouton du lecteur,
`tts_cache.stats()` (le compte affiche) et `tts_cache.purger()` (le vidage).

SECURITE : le test travaille dans un DOSSIER TEMPORAIRE et ne touche JAMAIS au
vrai cache -- il compare meme le nombre de fichiers du vrai cache avant et
apres, pour le prouver.
"""

import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import tts_cache                                          # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def main():
    vrai_cache = tts_cache.CACHE_DIR
    avant = len([p for p in vrai_cache.glob('*')]) if vrai_cache.is_dir() else 0
    print('')
    print('   le vrai cache (%s) contient %d fichier(s) : il ne sera PAS touche'
          % (vrai_cache, avant))

    with tempfile.TemporaryDirectory() as tmp:
        faux = Path(tmp) / 'tts_cache'
        faux.mkdir()
        tts_cache.CACHE_DIR = faux          # a partir d'ici, tout se passe ici

        print('')
        print('1) un cache vide')
        etat = tts_cache.stats()
        verifier('0 octet, 0 fichier',
                 etat['octets'] == 0 and etat['fichiers'] == 0, etat)
        verifier('le quota annonce est celui du module',
                 etat['quota_octets'] == tts_cache.CACHE_MAX_BYTES,
                 etat['quota_octets'])
        verifier('la version du cache est annoncee',
                 etat['version'] == tts_cache.VERSION_CACHE, etat['version'])

        print('')
        print('2) des fichiers dedans (dont une ecriture en cours)')
        (faux / 'a.wav').write_bytes(b'x' * 2048)
        (faux / 'b.wav').write_bytes(b'y' * 1024)
        (faux / 'en_cours.wav.tmp').write_bytes(b'z' * 512)
        etat = tts_cache.stats()
        verifier('le compte additionne les fichiers',
                 etat['octets'] == 3584 and etat['fichiers'] == 3, etat)

        print('')
        print('3) la purge')
        resultat = tts_cache.purger()
        verifier('la purge dit ce qu elle a libere',
                 resultat['ok'] and resultat['octets_liberes'] == 3072
                 and resultat['fichiers_supprimes'] == 2, resultat)
        verifier('la purge ne coupe PAS une ecriture en cours (.tmp)',
                 (faux / 'en_cours.wav.tmp').is_file(),
                 sorted(p.name for p in faux.iterdir()))
        restants = sorted(p.name for p in faux.iterdir())
        verifier('les fichiers de cache sont partis',
                 restants == ['en_cours.wav.tmp'], restants)
        etat = tts_cache.stats()
        verifier('le compte ne garde que l ecriture en cours',
                 etat['octets'] == 512, etat)
        verifier('une deuxieme purge ne dit plus rien avoir libere',
                 tts_cache.purger()['octets_liberes'] == 0)

        print('')
        print('4) le cache remarche apres une purge')
        tts_cache.put_audio('phrase', 'kokoro:fa_eva', '+0%', '+0Hz', 'wav', b'audio')
        verifier('on peut ecrire a nouveau dedans',
                 tts_cache.get_audio('phrase', 'kokoro:fa_eva', '+0%', '+0Hz',
                                     'wav') == b'audio')
        verifier('et le compte le voit', tts_cache.stats()['octets'] >= 5)

    tts_cache.CACHE_DIR = vrai_cache
    apres = len([p for p in vrai_cache.glob('*')]) if vrai_cache.is_dir() else 0
    verifier('le VRAI cache est intact (%d fichier(s))' % avant, avant == apres)


if __name__ == '__main__':
    print('=' * 66)
    print('VERIFICATION : cache audio (compte et purge a la main)')
    print('=' * 66)
    main()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    sys.exit(0 if ECHECS == 0 else 1)
