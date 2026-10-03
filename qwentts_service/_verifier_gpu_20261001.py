# -*- coding: utf-8 -*-
"""Vérifie que les deux paquets qwentts.cpp cohabitent dans le venv (01/10/2026).

Aucun modèle chargé : on regarde juste que les deux imports existent, et on lit
leurs drapeaux. Sert après l'installation de la roue carte graphique.
"""
import sys

sys.stdout.reconfigure(encoding='utf-8')

for nom in ('qwentts_cpp', 'qwentts_cpp_cpu'):
    try:
        module = __import__(nom)
        print('%-16s OK   version=%s  CPU_ONLY=%s'
              % (nom, getattr(module, '__version__', '?'),
                 getattr(module, 'CPU_ONLY', '?')))
    except Exception as erreur:
        print('%-16s ECHEC %s : %s' % (nom, type(erreur).__name__, erreur))
