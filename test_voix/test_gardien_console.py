# -*- coding: utf-8 -*-
"""Verifie que le moteur s'arrete quand sa fenetre (son entree) se ferme.

Ce que fait le script :
  1. lance le service sur un port d'ESSAI (8087), pour ne pas toucher au
     moteur en service, avec la variable qui force le gardien ;
  2. attend que le port reponde ;
  3. ferme son entree standard -- ce qui se produit quand la fenetre est
     fermee (fin de flux) ;
  4. verifie que le processus s'arrete tout seul et que le port se libere.

A lancer avec le python du venv du moteur :
    kyutai_service\\.venv\\Scripts\\python.exe test_voix\\test_gardien_console.py
"""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SERVICE = RACINE / "kyutai_service" / "servir_kyutai.py"
VENV = RACINE / "kyutai_service" / ".venv" / "Scripts" / "python.exe"
JOURNAL = RACINE / "kyutai_service" / "sortie_ecoute" / "journal_gardien.txt"

PORT = 8087
SANTE = "http://127.0.0.1:%d/sante" % PORT

sys.stdout.reconfigure(encoding='utf-8')


def port_repond(limite=60):
    debut = time.time()
    while time.time() - debut < limite:
        try:
            with urllib.request.urlopen(SANTE, timeout=1):
                return True
        except Exception:
            time.sleep(1)
    return False


def main():
    if not VENV.is_file():
        print("Venvironnement du moteur introuvable : %s" % VENV)
        return 1

    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["NIMM_KYUTAI_PORT"] = str(PORT)
    env["NIMM_KYUTAI_SURVEILLER_CONSOLE"] = "1"

    print("1) lancement du service d'essai sur le port %d..." % PORT)
    with open(JOURNAL, "w", encoding="utf-8") as journal:
        proc = subprocess.Popen([str(VENV), str(SERVICE)],
                                stdin=subprocess.PIPE, stdout=journal,
                                stderr=subprocess.STDOUT, env=env)

        print("2) attente de la reponse du port...")
        if not port_repond():
            print("   ECHEC : le port ne repond pas")
            proc.kill()
            return 1
        print("   le service repond (le modele peut encore charger)")

        print("3) fermeture de l'entree -- c'est ce qui se passe quand la fenetre")
        print("   est fermee...")
        proc.stdin.close()

        print("4) attente de l'arret automatique (le gardien veille apres 5 s)...")
        debut = time.time()
        while time.time() - debut < 40:
            if proc.poll() is not None:
                break
            time.sleep(1)

        arrete = proc.poll() is not None
        if not arrete:
            print("   ECHEC : le moteur tourne toujours apres 40 s")
            proc.kill()
        else:
            print("   OK : le moteur s'est arrete tout seul (code %s)" % proc.returncode)

    # Le port doit etre libre maintenant.
    try:
        with urllib.request.urlopen(SANTE, timeout=2):
            libre = False
    except Exception:
        libre = True
    print("   port %d libere : %s" % (PORT, "oui" if libre else "NON"))

    print("")
    print("--- journal du service ---")
    texte = JOURNAL.read_text(encoding="utf-8", errors="replace")
    print("\n".join(texte.strip().splitlines()[-6:]))
    print("")
    print("TOUT EST OK" if (arrete and libre) else "ECHEC")
    return 0 if (arrete and libre) else 1


if __name__ == "__main__":
    sys.exit(main())
