# -*- coding: utf-8 -*-
"""Mesure les phrases COURTES au moteur XTTS en marche (garde-fou anti-babil).

Demande au service (port 8083) de lire quelques phrases courtes et affiche la
DUREE obtenue pour chacune, face a la duree attendue d'apres le texte. Sert a
verifier qu'une phrase de 2 mots ne part plus en bouillie.

Le moteur doit etre allume (DEMARRER_XTTS.bat). Usage :
    python test_voix/_mesurer_phrases_courtes.py [voix]
"""

import io
import json
import sys
import urllib.request
import wave

sys.stdout.reconfigure(encoding='utf-8')

SERVICE = "http://127.0.0.1:8083"
VOIX = sys.argv[1] if len(sys.argv) > 1 else "xtts:4937_3731_000004-0001"

# Une phrase TRES courte, une courte, une moyenne : les trois tailles ou le
# babil apparaissait (constat de Laurent, 16/09/2026).
PHRASES = [
    "Non.",
    "Manger ?",
    "Que preferez-vous ?",
    "Vous prendrez aussi une chambre pour la nuit ?",
    "Il y a un bon agneau roti aux herbes, et quelques canards que mon fils a chasses.",
]

# Reperes de duree : debut de phrase + debit moyen.
COUT_ATTAQUE_S = 0.30
CARACTERES_PAR_SECONDE = 14.0


def demander(texte):
    # Le SERVICE attend l'identifiant SANS le prefixe de moteur : c'est le
    # lecteur qui le retire avant l'appel (modules/tts._xtts_voix_id).
    voix = VOIX.split(':', 1)[1] if ':' in VOIX else VOIX
    corps = json.dumps({"texte": texte, "voix": voix}).encode('utf-8')
    requete = urllib.request.Request(
        SERVICE + "/tts", data=corps,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=300) as reponse:
        return reponse.read()


def duree(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes), "rb") as f:
        return f.getnframes() / float(f.getframerate())


def segments(wav_bytes, seuil=0.012, bloc_s=0.02):
    """Liste les segments de PAROLE (debut, fin, duree) d'un WAV.

    C'est ce qui distingue les deux cas : un residu SEPARE par un silence (on
    peut le couper proprement) d'un residu colle a la parole (il faudrait
    couper dans le son).
    """
    import array
    import math

    with wave.open(io.BytesIO(wav_bytes), "rb") as f:
        frequence = f.getframerate()
        brut = f.readframes(f.getnframes())
    echantillons = array.array('h')
    echantillons.frombytes(brut)
    pas = max(1, int(bloc_s * frequence))
    parles = []
    for debut in range(0, len(echantillons), pas):
        bloc = echantillons[debut:debut + pas]
        if bloc and max(abs(v) for v in bloc) / 32768.0 >= seuil:
            parles.append(debut / float(frequence))
    if not parles:
        return [], frequence
    # Regroupe les instants parles en segments continus (tolerance d'un bloc).
    trous = []
    precedent = parles[0]
    debut_segment = parles[0]
    for instant in parles[1:]:
        if instant - precedent > bloc_s * 1.5:
            trous.append((debut_segment, precedent))
            debut_segment = instant
        precedent = instant
    trous.append((debut_segment, precedent))
    return trous, frequence


def main_mesures():
    try:
        with urllib.request.urlopen(SERVICE + "/sante", timeout=5) as reponse:
            sante = json.loads(reponse.read().decode('utf-8'))
    except Exception as erreur:
        print("Le moteur XTTS ne repond pas sur %s (%s)." % (SERVICE, erreur))
        print("Double-clique sur DEMARRER_XTTS.bat, puis relance ce script.")
        return
    print("Moteur XTTS pret : %s (%s voix)" % (sante.get("pret"), sante.get("voix")))
    print("Voix de test : %s" % VOIX)
    print("")
    print("%-62s %8s %8s %s" % ("phrase", "duree", "attendu", "verdict"))
    print("-" * 100)
    for texte in PHRASES:
        try:
            wav = demander(texte)
            obtenue = duree(wav)
        except Exception as erreur:
            print("%-62s ECHEC : %s" % (texte[:62], erreur))
            continue
        attendue = COUT_ATTAQUE_S + len(texte) / CARACTERES_PAR_SECONDE
        verdict = "OK" if obtenue <= attendue * 1.6 + 0.5 else "TROP LONG"
        print("%-62s %7.2fs %7.2fs  %s"
              % (texte[:62], obtenue, attendue, verdict))
        # Detail des segments : ou est la parole, ou sont les silences ?
        try:
            morceaux, frequence = segments(wav)
            detail = ' | '.join('%.2f-%.2f' % (debut, fin) for debut, fin in morceaux)
            print("      segments de parole : %s" % detail)
            for rang in range(1, len(morceaux)):
                silence = morceaux[rang][0] - morceaux[rang - 1][1]
                if silence >= 0.15:
                    print("      silence de %.2f s avant le segment %d (%.2f s)"
                          % (silence, rang + 1,
                             morceaux[rang][1] - morceaux[rang][0]))
        except Exception as erreur:
            print("      (analyse des segments impossible : %s)" % erreur)


main_mesures()
