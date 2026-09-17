# -*- coding: utf-8 -*-
"""Verifie le moteur NeuTTS DE BOUT EN BOUT (le service doit etre allume).

Ce test parle au service par le reseau, comme le fait le lecteur : il ne charge
pas le moteur lui-meme. Il verifie ce qui compte VRAIMENT a l'oreille et dans
la lecture, en quatre points :

  1. le service repond et connait ses voix (/sante, /voix) ;
  2. **la MEME phrase deux fois donne le MEME fichier** (identite octet a octet,
     SHA-256) : c'est la promesse de NeuTTS, et ce qui manquait a XTTS ;
  3. une phrase COURTE sort en une duree normale (pas de babil : XTTS faisait
     8 a 9 s sur « Manger ? », NeuTTS doit rester sous les 3 s) ;
  4. une phrase LONGUE n'est pas tronquee (duree encore proportionnelle).

Prerequis : le moteur allume (DEMARRER_NEUTTS.bat).
Usage : python test_voix/test_neutts_bout_en_bout.py [--voix ff_amelie] [--port 8084]

Attention a la duree : sur processeur, le moteur est 3 a 4 fois plus lent que
le temps reel -- ce test peut donc prendre une a deux minutes. Le lancer en
tache de fond si besoin (regles du projet sur les traitements longs).
"""

import argparse
import hashlib
import io
import json
import sys
import urllib.request
import wave

sys.stdout.reconfigure(encoding='utf-8')

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def lire_json(base, route, delai=10):
    with urllib.request.urlopen(base + route, timeout=delai) as reponse:
        return json.loads(reponse.read().decode('utf-8', 'replace'))


def demander_wav(base, texte, voix, delai=600):
    """POST /tts : renvoie les octets du WAV (ou leve une exception claire)."""
    corps = json.dumps({'texte': texte, 'voix': voix}).encode('utf-8')
    requete = urllib.request.Request(
        base + '/tts', data=corps,
        headers={'Content-Type': 'application/json; charset=utf-8'})
    with urllib.request.urlopen(requete, timeout=delai) as reponse:
        return reponse.read()


def duree_wav(octets):
    with wave.open(io.BytesIO(octets), 'rb') as fichier:
        return fichier.getnframes() / float(fichier.getframerate() or 24000)


def main():
    analyseur = argparse.ArgumentParser(
        description="Essai de bout en bout du moteur NeuTTS.")
    analyseur.add_argument('--voix', default='ff_amelie',
                           help="voix de reference (defaut : ff_amelie)")
    analyseur.add_argument('--hote', default='127.0.0.1')
    analyseur.add_argument('--port', type=int, default=8084)
    options = analyseur.parse_args()
    base = 'http://%s:%d' % (options.hote, options.port)

    print('')
    print('=' * 68)
    print('MOTEUR NEUTTS - ESSAI DE BOUT EN BOUT')
    print('=' * 68)
    print('service : %s   voix : %s' % (base, options.voix))

    print('')
    print('1) le service repond')
    try:
        sante = lire_json(base, '/sante')
    except Exception as erreur:
        print('  ECHEC le service ne repond pas (%s)' % erreur)
        print('  -> double-clique sur DEMARRER_NEUTTS.bat, puis relance.')
        print('')
        print('1 VERIFICATION(S) EN ECHEC')
        return 1
    verifier('le moteur est pret', bool(sante.get('pret')),
             'pret=%s' % sante.get('pret'))
    verifier('il annonce son appareil', bool(sante.get('appareil')),
             sante.get('appareil'))
    verifier('la graine est fixee (stabilite)', sante.get('graine') is not None,
             sante.get('graine'))
    voix = lire_json(base, '/voix').get('voix') or []
    verifier('la liste des voix est servie', bool(voix), '%d voix' % len(voix))
    verifier('la voix demandee existe', options.voix in voix, options.voix)
    if options.voix not in voix:
        print('')
        print('1 VERIFICATION(S) EN ECHEC')
        return 1

    print('')
    print('2) LA MEME PHRASE DEUX FOIS = LE MEME FICHIER (stabilite)')
    phrase = 'Bonjour. Comment allez-vous ?'
    premier = demander_wav(base, phrase, options.voix)
    second = demander_wav(base, phrase, options.voix)
    empreinte1 = hashlib.sha256(premier).hexdigest()
    empreinte2 = hashlib.sha256(second).hexdigest()
    verifier('deux prises de la meme phrase ont la meme empreinte SHA-256',
             empreinte1 == empreinte2,
             '%s... vs %s...' % (empreinte1[:16], empreinte2[:16]))
    verifier('le WAV fait plus que son en-tete', len(premier) > 1000,
             '%d octets' % len(premier))
    if empreinte1 == empreinte2:
        print('        (c est la reponse a "aussi stable que Kokoro ?" :')
        print('         sur ce moteur, oui, a graine fixe)')

    print('')
    print('3) LES PHRASES COURTES NE PARTENT PAS EN BABIL')
    for texte, plafond, duree_xtts in (('Non.', 3.0, 1.07),
                                       ('Manger ?', 3.0, 8.49),
                                       ('Que preferez-vous ?', 3.5, 9.11)):
        wav = demander_wav(base, texte, options.voix)
        duree = duree_wav(wav)
        verifier('%-22s %.2f s (XTTS : %.2f s, plafond %.1f s)'
                 % (texte, duree, duree_xtts, plafond), duree <= plafond,
                 '%.2f s' % duree)

    print('')
    print('4) UNE PHRASE LONGUE N EST PAS TRONQUEE')
    longue = ("Il marchait d'un pas lent le long de la riviere, songeant aux "
              "lettres qu'il n'avait jamais ose envoyer, et le vent dans les "
              "peupliers lui rappelait les soirs de son enfance, quand la "
              "vieille cloche sonnait doucement dans le village endormi.")
    wav = demander_wav(base, longue, options.voix)
    duree = duree_wav(wav)
    attendue = len(longue) / 14.0
    verifier('%d caracteres -> %.1f s (attendu ~%.1f s)'
             % (len(longue), duree, attendue), duree >= attendue * 0.6,
             '%.1f s' % duree)

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
