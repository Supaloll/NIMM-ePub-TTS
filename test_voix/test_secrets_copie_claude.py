# -*- coding: utf-8 -*-
"""Cherche des SECRETS dans les fichiers de la « copie pour Claude ».

Demande de Claude.AI (01/10/2026) : avant la vraie copie, parcourir les fichiers
LISTES et chercher les mots api_key, apikey, secret, token, password, Bearer,
sk-, AIza. On rapporte le fichier et la ligne.

Deux familles :
  - MOTIFS FORTS (signature d'une vraie cle) : `sk-`, `AIza`, `Bearer `,
    `api_key =` / `apikey =`, `password =`, `secret =`. Ceux-la font ECHOUER le
    scan (code 1) : ce sont des secrets probables.
  - MOTS LARGES (peuvent etre innocents : « max_new_tokens » !) : token, secret,
    password, api_key, apikey. On les LISTE, mais ils ne font pas echouer.

Lecture seule : ce script ne copie RIEN et n'ecrit RIEN.
Usage : python test_voix/test_secrets_copie_claude.py
"""
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(RACINE))

import _synchroniser_copie_claude as copie      # noqa: E402

# Motifs FORTS : signature d'une cle, ou affectation explicite.
FORTS = [r'sk-[A-Za-z0-9_\-]{8,}', r'AIza[0-9A-Za-z_\-]{10,}',
         r'Bearer\s+[A-Za-z0-9_\-\.]{8,}',
         r'(?i)api[_-]?key\s*[:=]\s*["\'][^"\']{8,}["\']',
         r'(?i)(password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']',
         r'(?i)secret\s*[:=]\s*["\'][^"\']{6,}["\']']
# Mots larges : signales, non bloquants.
LARGES = r'(?i)(api[_-]?key|apikey|secret|token|password|bearer|sk-|aiza)'


def main():
    print('')
    print('=' * 66)
    print(' SCAN DE SECRETS -- fichiers de la copie pour Claude')
    print('=' * 66)
    _prefixe, chemins = copie.lire_liste()
    chemins = chemins or []
    fichiers = []
    for rel in chemins:
        full = RACINE / rel
        if full.is_file() and not copie.refus(rel):
            fichiers.append((rel, full))

    forts, larges = [], []
    for rel, full in fichiers:
        try:
            texte = full.read_text(encoding='utf-8', errors='replace')
        except Exception as erreur:
            print('  (illisible : %s : %s)' % (rel, erreur))
            continue
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for motif in FORTS:
                if re.search(motif, ligne):
                    forts.append((rel, numero, ligne.strip()[:120]))
                    break
            if re.search(LARGES, ligne):
                larges.append((rel, numero, ligne.strip()[:120]))

    print('')
    print('fichiers parcourus : %d' % len(fichiers))
    print('')
    print('--- MOTIFS FORTS (secrets probables) : %d ---' % len(forts))
    for rel, numero, texte in forts:
        print('  %s : ligne %d : %s' % (rel, numero, texte))
    if not forts:
        print('  AUCUN.')

    print('')
    print('--- MOTS LARGES (souvent innocents) : %d occurrence(s) ---'
          % len(larges))
    par_fichier = {}
    for rel, numero, texte in larges:
        par_fichier.setdefault(str(rel), []).append(numero)
    for nom in sorted(par_fichier):
        numeros = par_fichier[nom]
        print('  %-52s %d  (lignes %s)' % (nom, len(numeros),
              ', '.join(str(n) for n in numeros[:12])
              + ('...' if len(numeros) > 12 else '')))

    print('')
    print('=' * 66)
    if forts:
        print('ALERTE : %d motif(s) FORT(S) a lire avant de copier.' % len(forts))
        return 1
    print('AUCUN SECRET PROBABLE. (les mots larges sont a survoler)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
