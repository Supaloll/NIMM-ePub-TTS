# -*- coding: utf-8 -*-
"""Essai du service Qwen (qwentts.cpp) : /sante puis une phrase.

Sans dependance : bibliotheque standard seulement. Sert a prouver qu'un service
repond, sur QUOI il tourne (`appareil`), et a quelle vitesse il rend une phrase.

Usage : python _essai_service_gpu.py [port] [fichier_wav]
"""
import json
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

port = sys.argv[1] if len(sys.argv) > 1 else '8096'
sortie_wav = sys.argv[2] if len(sys.argv) > 2 else '_essai_service_gpu.wav'
base = 'http://127.0.0.1:%s' % port

with urllib.request.urlopen(base + '/sante', timeout=10) as reponse:
    sante = json.loads(reponse.read().decode('utf-8'))
print('SANTE  pret=%s  appareil=%s  variante=%s  repli=%s  voix=%s  charge=%.1f s'
      % (sante.get('pret'), sante.get('appareil'), sante.get('variante'),
         sante.get('repli'), sante.get('voix'), sante.get('charge_en') or 0.0))

corps = json.dumps({
    'texte': 'Bonjour, ceci est un essai du moteur de voix sur la carte graphique.',
    'voix': '10087_11650_000028-0002',
}).encode('utf-8')
requete = urllib.request.Request(base + '/tts', data=corps,
                                 headers={'Content-Type': 'application/json'})
debut = time.time()
with urllib.request.urlopen(requete, timeout=120) as reponse:
    octets = reponse.read()
    etiquettes = reponse.headers.get('X-NIMM-Etiquettes')
calcul = time.time() - debut
print('TTS    %d octets de WAV en %.2f s  | etiquettes : %s'
      % (len(octets), calcul, etiquettes or '(aucune)'))
with open(sortie_wav, 'wb') as fichier:
    fichier.write(octets)
print('WAV ecrit : %s' % sortie_wav)
