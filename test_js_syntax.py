# -*- coding: utf-8 -*-
"""Verification de syntaxe de frontend/app.js via esprima.
Esprima ne supporte pas le optional chaining (?. ) ni le nullish coalescing
(??) deja presents dans le code : on les remplace dans une copie (approx.
syntaxique, les strings touchees restent valides) avant de parser."""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import esprima

src = io.open(r"g:/NIMM ePub/frontend/app.js", encoding="utf-8").read()

# Remplacements syntaxiques (approx) pour passer sous esprima.
# Ordre important : ?.( appel optionnel -> ( ; puis ?. chaînage -> . ; puis ?? -> ||
clean = src.replace("?.(", "(").replace("?.", ".").replace("??", "||")

try:
    esprima.parseScript(clean, tolerant=False)
    print("JS SYNTAX OK", len(src), "caracteres")
except esprima.Error as e:
    ligne = clean.count("\n", 0, e.index) + 1 if hasattr(e, "index") else "?"
    print("JS SYNTAX ERR ligne", ligne, "->", e)
    sys.exit(1)

