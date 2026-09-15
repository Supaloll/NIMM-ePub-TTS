# -*- coding: utf-8 -*-
"""Verifie que le moteur XTTS EN MARCHE applique bien le rognage (jetable).

Le service charge son code au demarrage : s'il tourne depuis avant le remede du
15/09/2026, il genere encore des phrases avec 0,54 a 0,91 s de silence de queue.
Ce script parle au service en marche et mesure ce qui sort VRAIMENT :

    queue ~0,25 s  -> le service tourne avec le nouveau code (OK)
    queue ~0,6 s   -> le service tourne avec l'ANCIEN code (a redemarrer)

Usage : python _verif_rognage_service.py
"""

import io
import json
import sys
import urllib.request
import wave

sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:8083"
PHRASE = "Oui, monsieur, je vous entends tres bien."
SEUIL = 0.012
BLOC = 0.02


def _get_json(chemin):
    with urllib.request.urlopen(BASE + chemin, timeout=10) as rep:
        return json.loads(rep.read().decode("utf-8"))


def main():
    try:
        infos = _get_json("/sante")
        voix = (_get_json("/voix").get("voix") or [""])[0]
    except Exception as erreur:
        print("Moteur injoignable sur %s (%s)." % (BASE, erreur))
        return 1

    if not infos.get("pret"):
        print("Moteur pas encore pret.")
        return 1

    corps = json.dumps({"texte": PHRASE, "voix": voix}).encode("utf-8")
    demande = urllib.request.Request(
        BASE + "/tts", data=corps,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(demande, timeout=240) as rep:
        wav = rep.read()

    with wave.open(io.BytesIO(wav), "rb") as f:
        frequence = f.getframerate()
        import array
        donnees = array.array("h")
        donnees.frombytes(f.readframes(f.getnframes()))
    duree = len(donnees) / float(frequence)

    pas = int(BLOC * frequence)
    dernier = -1
    for debut in range(0, len(donnees), pas):
        bloc = donnees[debut:debut + pas]
        if bloc and max(abs(v) for v in bloc) >= SEUIL * 32768:
            dernier = debut
    queue = (len(donnees) - (dernier + pas)) / float(frequence) if dernier >= 0 \
        else duree

    print("Voix %s -- %d octets, %.2f s de parole+silence" % (voix, len(wav), duree))
    print("Silence de queue mesure : %.2f s" % queue)
    if queue <= 0.35:
        print("OK : le moteur EN MARCHE applique bien le rognage (0,25 s).")
        return 0
    print("ATTENTION : le moteur en marche tourne encore avec l'ANCIEN code.")
    print("Fermer sa fenetre puis le relancer (DEMARRER_XTTS.bat).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
