# -*- coding: utf-8 -*-
"""
Test de parsing JS avec esprima.
"""
import esprima
import sys

sys.stdout.reconfigure(encoding='utf-8')

CODE_JS = """
function addition(a, b) {
    var total = a + b;
    return total;
}

var resultat = addition(2, 3);
console.log(resultat);
"""


def main():
    ast = esprima.parseScript(CODE_JS)
    print(f"AST cree avec {len(ast.body)} declaration(s) au niveau racine.")

    # Verifie que la fonction et la variable sont bien detectees
    types = [node.type for node in ast.body]
    print(f"Types detectes : {', '.join(types)}")

    if "FunctionDeclaration" in types and "VariableDeclaration" in types:
        print("Parsing JS OK - fonction et variable detectees.")
    else:
        print("Parsing JS ERR - structure inattendue.")
        return 1

    # Test de l'API tokenizer pour verifier que le module est complet
    tokens = esprima.tokenize("var x = 1;")
    print(f"Tokenisation OK - {len(tokens)} token(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
