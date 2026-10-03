# -*- coding: utf-8 -*-
"""GENERATEUR du banc « chapitre » : fait lire les phrases par le Pocket LEGER.

Ce script tourne dans le VENV DU MOTEUR POCKET (c'est le seul qui a PyTorch et
`pocket_tts`). Il n'est JAMAIS lance a la main : `_essais/_banc_chapitre_pocket.py`
le prepare le travail, l'appelle, puis fait le tri et l'assemblage (cote python
de base, la ou Whisper est installe).

Ce qu'il fait, et rien d'autre :
  1. il lit `phrases.json` (prepare par le meme banc : le texte du chapitre,
     deja decoupe et nettoye comme le fait le lecteur) ;
  2. il charge le modele LEGER (config `french_leger.yaml`) a la temperature
     demandee ;
  3. il fait lire chaque phrase PLUSIEURS FOIS (le moteur n'a pas de graine :
     une repetition ou un trou n'appartient qu'a une prise) et ecrit chaque
     prise en WAV brut (`brut_<phrase>_<tirage>.wav`).

Aucun tri ici, aucun assemblage : c'est le travail du banc.

Usage (par le banc) :
    pocket_tts_service\\.venv\\Scripts\\python.exe _essais\\_generer_chapitre_pocket.py <dossier>
"""

import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / 'test_voix'))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

from _mesurer_debit_pocket import charger_modele, ecrire_wav   # noqa: E402

CONFIG_LEGER = RACINE / 'pocket_tts_service' / 'configs' / 'french_leger.yaml'
TOKENS = 200          # la recette de l'atelier


def main():
    if len(sys.argv) < 2:
        print('ERR : il faut le dossier du banc en argument.')
        return 1
    dossier = Path(sys.argv[1])
    fiche = json.loads((dossier / 'phrases.json').read_text(encoding='utf-8'))
    phrases = fiche['phrases']
    tirages = int(fiche.get('tirages', 2))
    temperature = float(fiche.get('temperature', 0.70))
    voix = Path(fiche['voix'])

    print('generateur Pocket : %d phrase(s) x %d tirage(s), temperature %.2f'
          % (len(phrases), tirages, temperature))
    debut = time.time()
    modele = charger_modele('config', str(CONFIG_LEGER), temp=temperature)
    etat = modele.get_state_for_audio_prompt(str(voix))
    print('modele leger charge et voix encodee en %.1f s' % (time.time() - debut))

    total = 0
    for phrase in phrases:
        for tirage in range(1, tirages + 1):
            debut = time.time()
            audio = modele.generate_audio(etat, phrase['texte'], max_tokens=TOKENS)
            cible = dossier / ('brut_%02d_%d.wav' % (phrase['index'], tirage))
            ecrire_wav(cible, audio.detach().cpu().numpy(), modele.sample_rate)
            total += 1
            print('  phrase %02d tirage %d : %.2f s de calcul'
                  % (phrase['index'], tirage, time.time() - debut))
    print('%d prise(s) ecrite(s) dans %s' % (total, dossier))
    return 0


if __name__ == '__main__':
    sys.exit(main())
