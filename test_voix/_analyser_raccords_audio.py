# -*- coding: utf-8 -*-
"""ANALYSE : ou sont les trous et les raccords, dans les WAV d'un lot d'ecoute ?

POURQUOI (30/09/2026, retour d'ecoute de Laurent) : « Le A a un probleme de
coupure/collage/raccord de phrases. Soit il fait une pause au moment de la
coupure, soit il repete 2 fois le meme mot. » Ce que l'oreille appelle une
coupure, il faut le MESURER -- sinon on repare a l'aveugle.

CE QU'IL MESURE, fichier par fichier (lecture seule, aucun fichier modifie) :
  - duree, crete (dBFS) ;
  - silence de TETE et de QUEUE ;
  - SILENCES INTERNES de `--silence` seconde et plus : position (en secondes
    et en % du fichier) et duree. C'est la « pause au moment de la coupure » ;
  - SEGMENTS DE PAROLE : les zones entre ces silences. Un « collage » s'entend
    comme plusieurs segments la ou on attendait une seule phrase ;
  - SUSPECTS DE REPETITION : deux fenetres de parole consecutives dont
    l'enveloppe se ressemble trop (un mot redit). C'est un INDICE, pas une
    preuve -- l'oreille tranche, et le rapport le dit.

CE QU'IL NE FAIT PAS : aucune ecoute, aucune generation, aucun appel reseau.

Usage :
    python test_voix/_analyser_raccords_audio.py <dossier>
    python test_voix/_analyser_raccords_audio.py test_voix/mesure_pocket_20260930_1139
    python test_voix/_analyser_raccords_audio.py <dossier> --silence 0.25
"""

import argparse
import sys
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

FENETRE_S = 0.02          # 20 ms : l'enveloppe RMS de reference
TROU_MICRO_S = 0.05       # un trou plus court que ca reste DANS un mot
FENETRE_MOT_S = 0.30      # la longueur d'enveloppe comparee pour les doublons
# Un mot redit peut etre UN mot (0,3 s) ou un GROUPE de mots (« mais ne sachant,
# mais ne sachant comment » = pres de 1,5 s) : l'oreille de Laurent a trouve les
# deux, et la premiere version de ce detecteur -- une seule longueur -- n'a vu
# ni l'un ni l'autre. On balaie donc toutes les longueurs, du mot au groupe.
LONGUEURS_MOTIF_S = (0.20, 0.30, 0.40, 0.50, 0.70, 0.90, 1.20, 1.60, 2.00)
SEUIL_DOUBLON = 0.85      # au-dela, deux motifs se ressemblent trop
# Une repetition de GROUPE (« mais ne sachant, mais ne sachant comment ») ressort
# moins fort qu'un mot colle a lui-meme : on descend donc le seuil pour ce
# detecteur-la, quitte a le dire « a ecouter » plutot que « fautif ».
SEUIL_REPETITION_DECALAGE = 0.80
SEUIL_REPRISE = 0.85      # au-dela, le mot d'apres le silence redit celui d'avant


def lire_wav(chemin):
    """(echantillons float mono, frequence) -- sans dependance exotique."""
    import numpy as np
    with wave.open(str(chemin), 'rb') as fichier:
        frequence = fichier.getframerate()
        canaux = fichier.getnchannels()
        largeur = fichier.getsampwidth()
        brut = fichier.readframes(fichier.getnframes())
    if largeur == 2:
        donnees = np.frombuffer(brut, dtype='<i2').astype('float64') / 32768.0
    elif largeur == 1:
        donnees = (np.frombuffer(brut, dtype='uint8').astype('float64')
                   - 128.0) / 128.0
    elif largeur == 4:
        donnees = np.frombuffer(brut, dtype='<i4').astype('float64') / 2147483648.0
    else:
        raise ValueError('largeur d\'echantillon non geree : %d' % largeur)
    if canaux > 1:
        donnees = donnees.reshape(-1, canaux).mean(axis=1)
    return donnees, frequence


def enveloppe(donnees, frequence, fenetre_s=FENETRE_S):
    """(enveloppe RMS par fenetre, nombre d'echantillons par fenetre)."""
    import numpy as np
    pas = max(1, int(round(frequence * fenetre_s)))
    nombre = len(donnees) // pas
    if nombre == 0:
        return np.zeros(0), pas
    blocs = donnees[:nombre * pas].reshape(nombre, pas)
    return np.sqrt((blocs ** 2).mean(axis=1)), pas


def crete_dbfs(donnees):
    import numpy as np
    if len(donnees) == 0:
        return -120.0
    crete = float(np.abs(donnees).max())
    if crete <= 0:
        return -120.0
    import math
    return 20.0 * math.log10(crete)


def zones_parole(rms, seuil, trou_micro):
    """Les plages [debut, fin] (en trames) ou il y a de la voix.

    Deux zones separees par un trou plus court que `trou_micro` sont FUSIONNEES :
    sinon les micro-silences a l'interieur d'un mot compteraient comme des
    « raccords ».
    """
    paroles = rms > seuil
    zones = []
    debut = None
    for index, actif in enumerate(paroles):
        if actif and debut is None:
            debut = index
        elif not actif and debut is not None:
            zones.append([debut, index])
            debut = None
    if debut is not None:
        zones.append([debut, len(paroles)])
    fusionnees = []
    for zone in zones:
        if fusionnees and (zone[0] - fusionnees[-1][1]) <= trou_micro:
            fusionnees[-1][1] = zone[1]
        else:
            fusionnees.append(list(zone))
    return fusionnees


def suspects_doublon(rms, zones, trames_mot=None):
    """Indice de repetition : un motif de parole redit juste apres lui-meme.

    On compare l'enveloppe de deux motifs CONSECUTIFS de meme longueur
    ([t, t+L] contre [t+L, t+2L]) et on balaie toutes les longueurs utiles, du
    simple mot (0,2 s) au groupe de mots (2 s). Un score eleve n'est PAS une
    preuve : c'est un endroit a ecouter, et le rapport le dit.

    Les detections tres proches sont FUSIONNEES : un meme defaut ressort
    souvent a plusieurs longueurs de motif, et on ne veut pas le compter cinq
    fois.
    """
    import numpy as np
    trouves = []
    for debut, fin in zones:
        for longueur_s in LONGUEURS_MOTIF_S:
            trames = max(2, int(round(longueur_s / FENETRE_S)))
            nombre = (fin - debut) // (2 * trames)
            for index in range(nombre):
                base = debut + index * 2 * trames
                a = rms[base: base + trames]
                b = rms[base + trames: base + 2 * trames]
                if a.std() < 1e-6 or b.std() < 1e-6:
                    continue
                score = float(np.corrcoef(a, b)[0, 1])
                if score >= SEUIL_DOUBLON:
                    trouves.append((base * FENETRE_S, longueur_s, score, trames))
    # Fusion : on garde la meilleure detection par paquet de 0,5 s.
    trouves.sort(key=lambda item: (-item[2], item[0]))
    gardes = []
    for position, longueur_s, score, trames in trouves:
        if any(abs(position - garde[0]) < 0.5 for garde in gardes):
            continue
        gardes.append((position, longueur_s, score))
    gardes.sort()
    return gardes



def repetitions_decalage(rms, zones, longueur_s=0.40, dmin_s=0.30, dmax_s=2.50):
    """Un court motif est-il rejoue PLUS LOIN dans la phrase ?

    C'est le cas que l'oreille de Laurent a entendu et que la comparaison de
    fenetres COLLEES ratait : « [...] mais ne sachant, mais ne sachant comment »
    -- le meme groupe revient 1 ou 1,5 s plus loin. On compare donc l'enveloppe
    d'une petite fenetre (0,4 s) a toutes celles situees de 0,3 a 2,5 s plus
    loin, et on garde les ressemblances fortes.

    Indice, comme les autres : a ecouter, pas une preuve.
    """
    import numpy as np
    longueur = max(2, int(round(longueur_s / FENETRE_S)))
    pas_position = max(1, int(round(0.10 / FENETRE_S)))
    pas_decalage = max(1, int(round(0.10 / FENETRE_S)))
    dmin = int(round(dmin_s / FENETRE_S))
    dmax = int(round(dmax_s / FENETRE_S))
    trouves = []
    for debut, fin in zones:
        for position in range(debut, fin - longueur, pas_position):
            a = rms[position: position + longueur]
            if a.std() < 1e-6:
                continue
            for decalage in range(dmin, dmax, pas_decalage):
                cible = position + decalage
                if cible + longueur > fin:
                    break
                b = rms[cible: cible + longueur]
                if b.std() < 1e-6:
                    continue
                score = float(np.corrcoef(a, b)[0, 1])
                if score >= SEUIL_REPETITION_DECALAGE:
                    trouves.append((position * FENETRE_S, decalage * FENETRE_S,
                                    score))
    trouves.sort(key=lambda item: (-item[2], item[0]))
    gardes = []
    for position, decalage, score in trouves:
        if any(abs(position - garde[0]) < 0.8 for garde in gardes):
            continue
        gardes.append((position, decalage, score))
    gardes.sort()
    return gardes


def reprises_apres_silence(rms, silences):
    """Le mot d'AVANT le silence est-il redit JUSTE APRES ?

    C'est le symptome decrit par Laurent mot pour mot : « soit il fait une pause
    au moment de la coupure, soit il repete 2 fois le meme mot ». Les deux
    peuvent etre le meme defaut : le moteur s'arrete, puis reprend son elan sur
    le mot qu'il venait de dire. On compare donc l'enveloppe des 0,35 s qui
    precedent le silence a celle des 0,35 s qui le suivent.
    """
    import numpy as np
    trames = max(2, int(0.35 / FENETRE_S))
    reprises = []
    for position_s, duree_s in silences:
        fin_avant = int(position_s / FENETRE_S)
        debut_apres = int((position_s + duree_s) / FENETRE_S)
        if fin_avant < trames or debut_apres + trames > len(rms):
            continue
        a = rms[fin_avant - trames: fin_avant]
        b = rms[debut_apres: debut_apres + trames]
        if a.std() < 1e-6 or b.std() < 1e-6:
            continue
        score = float(np.corrcoef(a, b)[0, 1])
        if score >= SEUIL_REPRISE:
            reprises.append((position_s, duree_s, score))
    return reprises



def analyser_fichier(chemin, seuil_silence):
    """Toutes les mesures d'un WAV, sous forme de fiche."""
    import numpy as np
    donnees, frequence = lire_wav(chemin)
    rms, pas = enveloppe(donnees, frequence)
    duree = len(donnees) / float(frequence)
    crete = crete_dbfs(donnees)
    # Le seuil de parole suit la crete : -40 dB en dessous, jamais sous -60.
    seuil = max(10.0 ** (-60.0 / 20.0), 10.0 ** ((crete - 40.0) / 20.0))
    zones = zones_parole(rms, seuil, int(TROU_MICRO_S / FENETRE_S))
    suspects = suspects_doublon(rms, zones)

    silences = []
    for index in range(1, len(zones)):
        debut_s = zones[index - 1][1] * FENETRE_S
        fin_s = zones[index][0] * FENETRE_S
        if fin_s - debut_s >= seuil_silence:
            silences.append((debut_s, fin_s - debut_s))
    tete = zones[0][0] * FENETRE_S if zones else duree
    queue = (len(rms) - zones[-1][1]) * FENETRE_S if zones else 0.0
    reprises = reprises_apres_silence(rms, silences)
    repetitions = repetitions_decalage(rms, zones)

    return {'nom': chemin.name, 'duree': duree, 'crete': crete,
            'tete': tete, 'queue': queue, 'zones': len(zones),
            'segments': [(z[0] * FENETRE_S, (z[1] - z[0]) * FENETRE_S) for z in zones],
            'silences': silences, 'suspects': suspects, 'reprises': reprises,
            'repetitions': repetitions}


def main():
    analyseur = argparse.ArgumentParser(
        description='Mesure les trous et les raccords des WAV d\'un lot d\'ecoute.')
    analyseur.add_argument('dossier', help='dossier a analyser (recursif)')
    analyseur.add_argument('--silence', type=float, default=0.15,
                           help='duree mini d\'un silence interne (defaut : 0.15 s)')
    options = analyseur.parse_args()

    dossier = Path(options.dossier)
    if not dossier.is_dir():
        print('ERR : dossier introuvable : %s' % dossier)
        return 1
    fichiers = sorted(dossier.rglob('*.wav'))
    if not fichiers:
        print('ERR : aucun WAV dans %s' % dossier)
        return 1

    lignes = []

    def dire(texte):
        print(texte)
        lignes.append(texte)

    dire('')
    dire('=' * 78)
    dire('RACCORDS ET TROUS -- %d fichiers dans %s' % (len(fichiers), dossier))
    dire('silence interne compte a partir de %.2f s' % options.silence)
    dire('=' * 78)

    total_silences = 0
    total_suspects = 0
    total_reprises = 0
    total_repetitions = 0
    fiches = []
    for chemin in fichiers:
        fiche = analyser_fichier(chemin, options.silence)
        fiches.append(fiche)
        total_silences += len(fiche['silences'])
        total_suspects += len(fiche['suspects'])
        total_reprises += len(fiche['reprises'])
        total_repetitions += len(fiche['repetitions'])
        dire('')
        dire('  %s' % fiche['nom'])
        dire('     duree %.2f s | crete %.1f dBFS | tete %.2f s | queue %.2f s | %d segment(s) de parole'
             % (fiche['duree'], fiche['crete'], fiche['tete'], fiche['queue'],
                fiche['zones']))
        for debut, duree_silence in fiche['silences']:
            dire('     SILENCE INTERNE a %.2f s (%.0f %% du fichier) : %.2f s'
                 % (debut, 100.0 * debut / fiche['duree'], duree_silence))
        for position, longueur, score in fiche['suspects']:
            dire('     SUSPECT DE MOT REDIT vers %.2f s (motif de %.2f s, '
                 'ressemblance %.2f)' % (position, longueur, score))
        for position, decalage, score in fiche['repetitions']:
            dire('     REPETITION DE GROUPE : motif rejoue vers %.2f s puis '
                 '%.2f s plus loin (ressemblance %.2f)'
                 % (position, position + decalage, score))
        for position, duree_silence, score in fiche['reprises']:
            dire('     REPRISE APRES UN SILENCE a %.2f s (silence %.2f s, '
                 'ressemblance %.2f)' % (position, duree_silence, score))

    dire('')
    dire('=' * 78)
    dire('BILAN')
    dire('=' * 78)
    dire('  fichiers analyses      : %d' % len(fiches))
    dire('  silences internes      : %d' % total_silences)
    dire('  suspects de mot redit  : %d' % total_suspects)
    dire('  reprises apres un silence : %d' % total_reprises)
    dire('  repetitions de groupe : %d' % total_repetitions)
    sans_defaut = [f for f in fiches if not f['silences'] and not f['suspects']]
    dire('  fichiers SANS defaut   : %d / %d' % (len(sans_defaut), len(fiches)))
    if total_suspects:
        dire('')
        dire('  RAPPEL : les « suspects de mot redit » sont un INDICE de mesure')
        dire('  (deux enveloppes qui se ressemblent), pas une preuve : ce sont')
        dire('  des endroits a ecouter, et l\'oreille de Laurent tranche.')
    dire('')
    dire('FIN -- lecture seule, rien n\'a ete modifie.')

    rapport = dossier / 'RACCORDS.txt'
    rapport.write_text('\n'.join(lignes), encoding='utf-8')
    print('')
    print('Rapport ecrit : %s' % rapport)
    return 0


if __name__ == '__main__':
    sys.exit(main())
