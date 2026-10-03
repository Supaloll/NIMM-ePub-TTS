# -*- coding: utf-8 -*-
"""MESURE : le Pocket TTS francais LEGER (6 couches) tient-il mieux le temps reel ?

La demande de Laurent (30/09/2026), mot pour mot : « il y a beaucoup de blancs
encore et parfois carrement la lecture s'arrete completement, donc on doit etre
a la limite de mon processeur [...] un modele encore plus leger si ca existe ».

Ce banc repond au chiffre qui decide de tout : combien de fois le moteur fait
l'audio plus vite que la lecture (le « x temps reel »). Un moteur a x1,04 (le
Qwen d'aujourd'hui) n'a AUCUNE marge ; un moteur a x3 en a beaucoup.

CE QU'IL COMPARE, sur les MEMES phrases reelles de livre et les memes reglages :
  A = le modele EN SERVICE (24 couches, `french_24l`, 672 Mo) -- la reference ;
  B = le modele LEGER (6 couches, `french`, 219 Mo) -- le candidat, charge par
      la config locale `pocket_tts_service/configs/french_leger.yaml` (donc
      SANS mise a jour du paquet : la 3.1.0 installee refuse `language='french'`
      mais accepte un chemin de config).
Les phrases sont celles du banc du moteur Qwen (livre 28, chapitre 20), pour
que les chiffres se comparent a ceux du 29/09/2026 (Qwen : x1,04).

CE QU'IL FAIT : pour chaque variante, il charge le modele (chronometre),
encode la voix (chronometre), puis fait dire chaque phrase plusieurs fois, en
relisant chaque WAV ecrit pour connaitre sa duree REELLE. Il pose les WAV cote
a cote dans un dossier date (A et B, phrase par phrase) pour l'oreille, et
ecrit un rapport lisible.

CE QU'IL NE FAIT PAS : il ne modifie ni la base, ni les voix, ni le service, ni
la configuration du lecteur. Il REFUSE de partir si le service Pocket tourne
(port 8085) : les deux se partageraient les coeurs et la mesure ne voudrait
rien dire.

LE SEUL EFFET DE BORD : au premier passage, le modele LEGER (219 Mo) est
telecharge dans le cache Hugging Face de la machine (le modele 24 couches y est
deja). C'est annonce par le lanceur avant de partir.

Usage (le lanceur double-clic fait tout) :
    python test_voix/_mesurer_debit_pocket.py
    python test_voix/_mesurer_debit_pocket.py --prises 3
    python test_voix/_mesurer_debit_pocket.py --variantes a        (seulement le 24 couches)
"""

import argparse
import ctypes
import ctypes.wintypes
import gc
import statistics
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SERVICE = RACINE / 'pocket_tts_service'
CONFIG_LEGER = SERVICE / 'configs' / 'french_leger.yaml'
VOIX_DEFAUT = SERVICE / 'voix' / 'Femme001_reference.wav'
DOSSIER_MESURES = Path(__file__).resolve().parent

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PORT_SERVICE = 8085
# Le reglage du service (`NIMM_POCKET_TTS_COEURS`, defaut 4) : on mesure dans
# les conditions du lecteur, les 2 autres coeurs restant au lecteur.
COEURS = 4
# Le reglage du service (`NIMM_POCKET_TTS_TEMPERATURE`, defaut 0.3).
TEMPERATURE = 0.3
# La recette de l'atelier pour le decoupage (`--max-tokens 200`).
TOKENS = 200

# TROIS vraies phrases du livre 28 (« 22/11/63 »), chapitre 20, de 152 a 155
# caracteres -- la taille exacte de ce que le lecteur envoie au moteur. Elles
# sont figees ici EN MEME TEMPS que dans le banc du Qwen, pour que deux
# campagnes de mesure se comparent.
PHRASES = [
    ('phrase1', 'Je me suis fait installer le téléphone et la première personne que '
                'j’ai appelée fut Ellen Dockerty, qui me communiqua avec joie l’adresse '
                'de Sadie à Reno.'),
    ('phrase2', 'Je lui ai écrit une lettre aussitôt après avoir raccroché, détestant '
                'mon ton guindé, artificiellement bavard mais ne sachant comment '
                'm’en dépêtrer.'),
    ('phrase3', 'Ça, c’était encore ma jalousie maladive, et j’ai bouclé ma lettre en '
                'vitesse, sachant que j’avais probablement pris des accents plaintifs, '
                'et m’en foutant.'),
]

# Les deux variantes : (etiquette, dossier court, facon de charger, valeur).
# A = ce qui lit aujourd'hui quand on choisit Pocket TTS ; B = le candidat.
VARIANTES = [
    ('A', '24couches', 'language', 'french_24l'),
    ('B', 'leger6', 'config', str(CONFIG_LEGER)),
]



def memoire_mo():
    """(memoire courante, pic) du processus, en Mo -- sans dependance externe."""
    class Compteurs(ctypes.Structure):
        _fields_ = [('cb', ctypes.wintypes.DWORD),
                    ('PageFaultCount', ctypes.wintypes.DWORD),
                    ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                    ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t)]
    compteurs = Compteurs()
    compteurs.cb = ctypes.sizeof(Compteurs)
    # ATTENTION (piege paye le 20/09/2026) : sans argtypes/restype explicites,
    # Windows tronque le handle du processus a 32 bits et l'appel renvoie
    # toujours 0 -- on croyait lire 0 Mo alors que le modele etait en memoire.
    noyau = ctypes.windll.kernel32
    noyau.GetCurrentProcess.restype = ctypes.wintypes.HANDLE
    psapi = ctypes.windll.psapi
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.wintypes.HANDLE,
                                           ctypes.POINTER(Compteurs),
                                           ctypes.wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL
    ok = psapi.GetProcessMemoryInfo(noyau.GetCurrentProcess(),
                                    ctypes.byref(compteurs), compteurs.cb)
    if not ok:
        return 0.0, 0.0
    return (compteurs.WorkingSetSize / 1048576.0,
            compteurs.PeakWorkingSetSize / 1048576.0)


def duree_du_wav(chemin):
    """Duree reelle du fichier ecrit : on le RELIT (jamais de calcul de tete)."""
    with wave.open(str(chemin), 'rb') as fichier:
        return fichier.getnframes() / float(fichier.getframerate())


def ecrire_wav(chemin, donnees, frequence):
    """Les echantillons du moteur en WAV PCM 16 bits (mono).

    Le module `wave` de Python REFUSE le float32 (piege paye le 20/09/2026 :
    « unknown format: 3 », soit le format IEEE float), d'ou la conversion
    explicite en int16.
    """
    import numpy as np
    donnees = np.asarray(donnees)
    if donnees.ndim == 2 and donnees.shape[0] <= 2:
        donnees = donnees.T          # [canaux, echantillons] -> [echantillons, canaux]
    if donnees.dtype.kind == 'f':
        donnees = np.clip(donnees, -1.0, 1.0)
        donnees = (donnees * 32767.0).astype('int16')
    donnees = donnees.astype('int16')
    with wave.open(str(chemin), 'wb') as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(int(frequence))
        fichier.writeframes(donnees.tobytes())


def service_allume():
    """Le service Pocket repond-il ? (ses coeurs seraient pris)."""
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/sante' % PORT_SERVICE,
                                    timeout=3) as reponse:
            return reponse.status == 200
    except (urllib.error.URLError, OSError):
        return False


def charger_modele(facon, valeur, temp=None):
    """Charge le modele de la variante, avec les reglages du service.

    `temp` est reglable pour les essais (banc de reglages) : par defaut, c'est
    la temperature du service (TEMPERATURE).
    """
    import torch
    from pocket_tts import TTSModel

    temperature = TEMPERATURE if temp is None else temp
    torch.set_num_threads(COEURS)
    if facon == 'language':
        return TTSModel.load_model(language=valeur, temp=temperature)
    return TTSModel.load_model(config=valeur, temp=temperature)


def mesurer_variante(etiquette, court, facon, valeur, voix, prises, dossier, dire):
    """Charge la variante, mesure ses phrases, ecrit ses WAV. Rend le bilan."""
    charge = ('langue %s' % valeur if facon == 'language'
              else 'config %s' % Path(valeur).name)
    dire('')
    dire('=' * 70)
    dire('VARIANTE %s -- %s' % (etiquette, charge))
    dire('=' * 70)

    ram0, _ = memoire_mo()
    debut = time.time()
    modele = charger_modele(facon, valeur)
    chargement = time.time() - debut
    ram1, pic1 = memoire_mo()
    dire('  chargement du modele : %.1f s   (memoire %.0f Mo, pic %.0f Mo)'
         % (chargement, ram1, pic1))

    debut = time.time()
    etat = modele.get_state_for_audio_prompt(str(voix))
    encodage = time.time() - debut
    dire('  encodage de la voix  : %.1f s' % encodage)

    sous_dossier = dossier / ('%s_%s' % (etiquette, court))
    sous_dossier.mkdir(parents=True, exist_ok=True)

    dire('')
    dire('  %-8s %5s %6s %8s %8s %10s'
         % ('phrase', 'car.', 'prise', 'audio', 'calcul', 'x t. reel'))
    dire('  ' + '-' * 56)
    resultats = []
    for numero, (nom, texte) in enumerate(PHRASES, start=1):
        for prise in range(1, prises + 1):
            debut = time.time()
            audio = modele.generate_audio(etat, texte, max_tokens=TOKENS)
            calcul = time.time() - debut
            chemin = sous_dossier / ('%02d_%s_%s_%s_prise%d.wav'
                                     % (numero, etiquette, court, nom, prise))
            ecrire_wav(chemin, audio.detach().cpu().numpy(), modele.sample_rate)
            duree = duree_du_wav(chemin)          # on relit ce qui est ecrit
            ratio = calcul / duree if duree else 0.0
            resultats.append((nom, prise, len(texte), duree, calcul, ratio))
            dire('  %-8s %5d %6d %7.1f s %7.1f s %9.2f'
                 % (nom, len(texte), prise, duree, calcul,
                    (1.0 / ratio) if ratio else 0.0))

    ram2, pic2 = memoire_mo()
    ratios = [ligne[5] for ligne in resultats]
    audio_total = sum(ligne[3] for ligne in resultats)
    calcul_total = sum(ligne[4] for ligne in resultats)
    ratio_moyen = calcul_total / audio_total if audio_total else 0.0
    x_moyen = 1.0 / ratio_moyen if ratio_moyen else 0.0
    x_plus_lent = 1.0 / max(ratios) if ratios else 0.0
    x_plus_rapide = 1.0 / min(ratios) if ratios else 0.0

    dire('')
    dire('  BILAN %s' % etiquette)
    dire('    x le temps reel (moyenne) : %.2f' % x_moyen)
    dire('    le plus lent             : %.2f  (la phrase qui donnerait un blanc)'
         % x_plus_lent)
    dire('    le plus rapide           : %.2f' % x_plus_rapide)
    dire('    1 h d\'audio demanderait  : %.0f min de calcul'
         % (ratio_moyen * 60))
    dire('    memoire : %.0f Mo, pic %.0f Mo' % (ram2, pic2))
    partout = ('LARGE marge : la lecture a la volee tient meme si le PC fait '
               'autre chose' if x_moyen >= 2.5 else
               'marge correcte' if x_moyen >= 1.5 else
               'juste : de la marge, mais peu' if x_moyen >= 1.2 else
               'PAS DE MARGE (la zone des blancs : c\'est le cas du Qwen a x1,04)')
    dire('    VERDICT : %s' % partout)
    dire('    WAV a ecouter : %s' % sous_dossier)

    # Le modele suivant ne doit pas cohabiter en memoire avec celui-ci : sur un
    # processeur a 6 coeurs, la RAM compte (2 Go par modele 24 couches).
    del modele
    gc.collect()
    return {'etiquette': etiquette, 'court': court, 'charge': charge,
            'x_moyen': x_moyen, 'x_plus_lent': x_plus_lent,
            'x_plus_rapide': x_plus_rapide,
            'chargement': chargement, 'encodage': encodage,
            'pic': pic2, 'verdict': partout,
            'secondes_audio': audio_total, 'secondes_calcul': calcul_total}


def main():
    analyseur = argparse.ArgumentParser(
        description='Mesure le debit de Pocket TTS (francais) : 24 couches '
                    'contre 6 couches.')
    analyseur.add_argument('--prises', type=int, default=2,
                           help='nombre de prises par phrase (defaut : 2)')
    analyseur.add_argument('--voix', default=str(VOIX_DEFAUT),
                           help='WAV de reference de la voix (defaut : Femme001)')
    analyseur.add_argument('--variantes', default='a,b',
                           help='a = 24 couches (service), b = 6 couches (leger)')
    analyseur.add_argument('--sortie', default='',
                           help='dossier des WAV (defaut : un dossier date)')
    options = analyseur.parse_args()

    lignes = []

    def dire(texte):
        print(texte)
        lignes.append(texte)

    dire('')
    dire('=' * 70)
    dire('DEBIT DE POCKET TTS EN FRANCAIS -- 24 couches contre 6 couches')
    dire('=' * 70)
    dire('voix de reference : %s' % options.voix)
    dire('reglages          : %d coeurs, temperature %.2f, max_tokens %d '
         '(ceux du service)' % (COEURS, TEMPERATURE, TOKENS))
    dire('prises par phrase : %d' % options.prises)

    if not Path(options.voix).is_file():
        dire('')
        dire('ERR : la voix %s n\'existe pas.' % options.voix)
        return 1

    demandees = [lettre.strip().lower()
                 for lettre in options.variantes.split(',') if lettre.strip()]
    a_faire = [variante for variante in VARIANTES
               if variante[0].lower() in demandees]

    # Le candidat B a besoin de sa config locale : on le dit AVANT de lancer
    # 3 a 6 minutes de calcul.
    if any(variante[0] == 'B' for variante in a_faire) and not CONFIG_LEGER.is_file():
        dire('')
        dire('ERR : la config du modele leger est absente :')
        dire('      %s' % CONFIG_LEGER)
        return 1

    if service_allume():
        dire('')
        dire('Le service Pocket TTS REPOND deja sur le port %d.' % PORT_SERVICE)
        dire('Ferme sa fenetre, puis relance ce banc : sinon les deux se')
        dire('partageraient les coeurs et les chiffres ne voudraient rien dire.')
        return 1

    horodatage = time.strftime('%Y%m%d_%H%M')
    dossier = (Path(options.sortie) if options.sortie
               else DOSSIER_MESURES / ('mesure_pocket_%s' % horodatage))
    dossier.mkdir(parents=True, exist_ok=True)

    bilans = []
    for variante in a_faire:
        etiquette, court, facon, valeur = variante
        if etiquette == 'B':
            dire('')
            dire('NOTE : la variante B (modele LEGER, 219 Mo) se telecharge au')
            dire('       premier passage dans le cache Hugging Face. C\'est le')
            dire('       seul acces reseau de ce banc, et il ne se fait qu\'une')
            dire('       fois (les passages suivants partent du cache).')
        bilans.append(mesurer_variante(etiquette, court, facon, valeur,
                                       Path(options.voix), options.prises,
                                       dossier, dire))

    dire('')
    dire('=' * 70)
    dire('COMPARAISON (x le temps reel : plus grand = plus de marge)')
    dire('=' * 70)
    dire('  %-4s %-30s %8s %8s %8s'
         % ('', 'moteur', 'moyenne', 'lent', 'rapide'))
    for bilan in bilans:
        dire('  %-4s %-30s %8.2f %8.2f %8.2f'
             % (bilan['etiquette'], bilan['charge'], bilan['x_moyen'],
                bilan['x_plus_lent'], bilan['x_plus_rapide']))
    dire('')
    dire('  Repere d\'atelier, pour situer : le moteur Qwen mesure le 29/09/2026')
    dire('  tournait a x1,04 le temps reel -- c\'est la zone des blancs.')
    dire('')
    dire('  Les WAV a ecouter sont ranges par phrase :')
    for variante in a_faire:
        dire('    %s : %s' % (variante[0],
                              dossier / ('%s_%s' % (variante[0], variante[1]))))
    dire('')
    dire('FIN -- rien n\'a ete modifie (ni base, ni voix, ni service).')

    (dossier / 'RAPPORT.txt').write_text('\n'.join(lignes), encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
