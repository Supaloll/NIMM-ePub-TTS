# -*- coding: utf-8 -*-
"""Essai (sans risque) du garde-fou de START.bat : qui serait arrete ?

Le garde-fou de START.bat arrete les processus PYTHON qui ecoutent sur le port
8081 (le serveur du lecteur). Ce script montre exactement ce qu'il ferait, sans
rien arreter :

    python test_voix/_essai_garde_fou_start.py

Pourquoi il existe (lecon du 18/09/2026) : un premier garde-fou filtrait les
processus par NOM DE SCRIPT (`main.py`). Or NIMM, le chatbot de Laurent
(G:\\NIMM), utilise lui aussi un `main.py` -- et il tourne sur le port 8080. Le
garde-fou l'avait donc arrete par erreur. Le filtre par PORT ne peut pas se
tromper : le port 8081 appartient au lecteur, point. Et on exige un processus
Python, pour ne jamais toucher le relais Tailscale qui ecoute aussi sur 8081.
"""

import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

COMMANDE = (
    "$pids = Get-NetTCPConnection -LocalPort 8081 -State Listen "
    "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess "
    "-Unique; "
    "foreach ($p in $pids) { "
    "$proc = Get-Process -Id $p -ErrorAction SilentlyContinue; "
    "if ($proc -and $proc.ProcessName -like 'python*') { "
    "'ARRETERAIT  : ' + $p + ' (' + $proc.ProcessName + ')' "
    "} else { "
    "'LAISSE TRANQUILLE : ' + $p + ' (' + $proc.ProcessName + ')' "
    "} }"
)


def main():
    print('')
    print('=' * 74)
    print('ESSAI DU GARDE-FOU DE START.bat (port 8081) — RIEN N EST ARRETE')
    print('=' * 74)
    resultat = subprocess.run(
        ['powershell', '-NoProfile', '-Command', COMMANDE],
        capture_output=True, text=True, encoding='utf-8', timeout=60)
    sortie = (resultat.stdout or '').strip()
    print('')
    if sortie:
        for ligne in sortie.splitlines():
            print('  ' + ligne)
    else:
        print('  aucun processus n ecoute sur 8081 : rien a arreter.')
    if resultat.stderr and resultat.stderr.strip():
        print('')
        print('  (messages de PowerShell : %s)' % resultat.stderr.strip()[:200])
    print('')
    print('  Rappel : NIMM (chatbot, port 8080) n est JAMAIS concerne.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
