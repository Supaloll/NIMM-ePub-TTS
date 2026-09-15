# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent

# ==============================================================
# LECTURE DES CLES ET DU TEXTE
# ==============================================================

def lire_cles():
    cles = {}
    with open(BASE_DIR / "cles_api.txt", "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            cles[cle.strip()] = valeur.strip()
    return cles

def lire_chapitre():
    with open(BASE_DIR / "chapitre_test.txt", "r", encoding="utf-8") as f:
        return f.read()

# ==============================================================
# LE PROMPT COMMUN AUX 3 IA
# ==============================================================

PROMPT_SYSTEME = """Tu es un analyste litteraire specialise dans l'attribution de dialogues en francais.

On te donne un extrait de roman francais. Decoupe-le toi-meme en phrases
(numerote-les a partir de 1, dans l'ordre du texte), puis pour CHAQUE phrase,
determine qui parle :
- "narration" si c'est le narrateur (description, action, pas de dialogue)
- le nom canonique complet du personnage si c'est une replique ou une pensee
  rapportee (ex: "Morrel_pere" et "Morrel_Maximilien" pour bien les distinguer,
  jamais juste "Morrel" tout seul quand les deux sont presents dans l'extrait)
- "lettre" pour un texte lu a voix haute (courrier, document)

Regles importantes :
- Une replique non taguee se deduit souvent par l'alternance des tours de
  parole : relis les repliques precedentes pour comprendre qui repond a qui.
- Si un locuteur est designe de facon vague ("une voix", "quelqu'un") et que
  son identite est revelee seulement dans une phrase ulterieure, resous-le
  retroactivement avec le nom reel.
- Si deux repliques de personnages differents semblent fusionnees dans le
  meme paragraphe source (pas de separateur clair), scinde-les et signale-le
  dans "anomalie".
- Indique un niveau de confiance : "haute", "moyenne" ou "basse".
- Precise le genre deduit du personnage (H/F) pour guider le choix de voix.

Reponds UNIQUEMENT en JSON valide, sans texte autour, sans balises markdown,
selon ce schema exact :
{
  "personnages": [
    {"nom": "Morrel_pere", "genre": "H"},
    {"nom": "Julie", "genre": "F"}
  ],
  "phrases": [
    {"id": 1, "texte": "...", "locuteur": "narration", "confiance": "haute"},
    {"id": 2, "texte": "...", "locuteur": "Morrel_pere", "genre": "H", "confiance": "haute", "anomalie": null}
  ]
}
"""

# ==============================================================
# APPELS AUX 3 PROVIDERS
# ==============================================================

def appeler_claude(texte, cle_api):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": cle_api,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-sonnet-5",
        "max_tokens": 32000,
        "thinking": {"type": "disabled"},
        "system": PROMPT_SYSTEME,
        "messages": [{"role": "user", "content": texte}],
    }
    r = requests.post(url, headers=headers, json=body, timeout=300)
    r.raise_for_status()
    data = r.json()
    return _nettoyer_json(
        "".join(bloc.get("text", "") for bloc in data.get("content", []))
    )


def appeler_claude_haiku(texte, cle_api):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": cle_api,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-haiku-4-5",
        "max_tokens": 64000,
        "system": PROMPT_SYSTEME,
        "messages": [{"role": "user", "content": texte}],
    }
    r = requests.post(url, headers=headers, json=body, timeout=300)
    r.raise_for_status()
    data = r.json()
    return _nettoyer_json(
        "".join(bloc.get("text", "") for bloc in data.get("content", []))
    )


def appeler_mistral(texte, cle_api):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {cle_api}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "mistral-large-latest",
        "max_tokens": 16000,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {"role": "user", "content": texte},
        ],
    }
    r = requests.post(url, headers=headers, json=body, timeout=300)
    r.raise_for_status()
    data = r.json()
    return _nettoyer_json(data["choices"][0]["message"]["content"])


def _nettoyer_json(texte_brut):
    """Retire les balises ```json ... ``` que certains modeles ajoutent
    malgre la consigne de ne pas le faire."""
    t = texte_brut.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def appeler_deepseek(texte, cle_api):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {cle_api}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "deepseek-chat",
        "max_tokens": 16000,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {"role": "user", "content": texte},
        ],
    }
    r = requests.post(url, headers=headers, json=body, timeout=300)
    r.raise_for_status()
    data = r.json()
    return _nettoyer_json(data["choices"][0]["message"]["content"])


def appeler_gemini(texte, cle_api):
    # Modele stable actuel (verifie sur https://ai.google.dev/gemini-api/docs/models,
    # la gamme a evolue : gemini-2.5-pro n'existe plus en 2026).
    modele = "gemini-3.7-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent?key={cle_api}"
    body = {
        "contents": [{"parts": [{"text": PROMPT_SYSTEME + "\n\n" + texte}]}],
    }
    r = requests.post(url, json=body, timeout=120)
    r.raise_for_status()
    data = r.json()
    parts = data["candidates"][0]["content"]["parts"]
    return _nettoyer_json("".join(p.get("text", "") for p in parts))


# ==============================================================
# SAUVEGARDE DES RESULTATS
# ==============================================================

def sauver_resultat(nom_provider, contenu_brut):
    chemin = BASE_DIR / f"resultat_{nom_provider}.txt"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu_brut)
    print(f"  -> Sauvegarde dans {chemin.name}")


# ==============================================================
# PROGRAMME PRINCIPAL
# ==============================================================

def main():
    print("Lecture des cles API et du chapitre test...")
    cles = lire_cles()
    texte = lire_chapitre()
    print(f"Chapitre charge ({len(texte)} caracteres).\n")

    providers = [
        ("claude_haiku", appeler_claude_haiku, "ANTHROPIC_API_KEY"),
        ("gemini", appeler_gemini, "GOOGLE_API_KEY"),
    ]

    for nom, fonction, nom_cle in providers:
        cle = cles.get(nom_cle, "")
        if not cle or "colle_ta_cle" in cle:
            print(f"[{nom}] Cle API manquante dans cles_api.txt — ignore.")
            continue

        print(f"[{nom}] Envoi de la requete...")
        debut = time.time()
        derniere_erreur = None
        for tentative in range(1, 4):
            try:
                resultat = fonction(texte, cle)
                duree = time.time() - debut
                print(f"[{nom}] Reponse recue en {duree:.1f}s.")
                sauver_resultat(nom, resultat)
                derniere_erreur = None
                break
            except Exception as e:
                derniere_erreur = e
                if "529" in str(e) and tentative < 3:
                    print(f"[{nom}] Serveur surcharge (529), nouvel essai dans 15s ({tentative}/3)...")
                    time.sleep(15)
                else:
                    break
        if derniere_erreur:
            print(f"[{nom}] ERREUR : {derniere_erreur}")
        print()

    print("Termine. Regarde les fichiers resultat_*.txt dans ce dossier.")


if __name__ == "__main__":
    main()

