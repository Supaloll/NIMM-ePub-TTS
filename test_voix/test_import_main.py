# -*- coding: utf-8 -*-
"""Verifie que l'app FastAPI se construit sans erreur (import de main.py)."""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"g:/NIMM ePub")

import main

print("main app OK - titre:", main.app.title)
paths = [r.path for r in main.app.routes]
print("routes /api/tts presentes:", "/api/tts" in paths)
print("route /cast/estimate:", any(p == "/api/books/{book_id}/cast/estimate" for p in paths))
