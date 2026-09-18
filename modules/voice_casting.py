# -*- coding: utf-8 -*-
"""
Passe 1 -- Attribution des personnages par chapitre via Gemini.
Le chapitre est pre-decoupe en phrases numerotees cote serveur
(meme logique que la recherche dans le livre) ; Gemini se contente
d'attribuer un locuteur a chaque numero, sans jamais retaper le texte.
"""
import re
import json
import time
import asyncio
import math
import unicodedata
from pathlib import Path

import httpx

from modules.config import (
    get_gemini_api_key, get_mistral_api_key, get_deepseek_api_key,
    get_local_model, get_local_url,
)
from modules.tts import KOKORO_VOICES, KYUTAI_VOICES, XTTS_VOICES, NEUTTS_VOICES

MISTRAL_URL  = "https://api.mistral.ai/v1/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

GEMINI_MODEL = "gemini-3.7-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


# ==============================================================
# DECOUPAGE DU CHAPITRE
# ==============================================================

def _split_chapter_sentences(text: str) -> list:
    """
    Decoupe en phrases numerotees -- LA regle unique du projet
    (`modules/decoupage.py`), identique a `_buildSentences()` cote page, a
    `_decouper_phrases_du_chapitre()` (re-cast, main.py) et a la recherche.

    Historique : la regle etait ecrite ICI, en double, et coupait les phrases
    apres le point d'une abreviation (« ... complimenter M. » / « de Morcerf »).
    Laurent l'entendait comme un silence apres « monsieur ». Depuis le
    18/09/2026 il n'y a plus qu'une regle, et elle recolle ces morceaux ; les
    index de `speaker_attribution` ont ete migres en consequence
    (test_voix/_migrer_index_phrases.py).
    """
    from modules.decoupage import phrases as _decouper
    return [{"id": sid, "texte": phrase}
            for sid, phrase in enumerate(_decouper(text))]


# ==============================================================
# PROMPT
# ==============================================================

def _build_prompt(fiche_personnages: list, sentences: list) -> str:
    """
    Construit le prompt de la Passe 1, en FORMAT COMPACT (session du
    13/09/2026, apres une facture de 5,64 € pour un seul livre).

    Deux gaspillages ont ete identifies dans l'ancien format :
      1. il fallait RECOPIER toute la fiche de personnages dans chaque
         reponse (jusqu'a 175 personnages en fin de livre) -- alors que le
         code coté Python accumule deja cette fiche d'un chapitre a l'autre ;
      2. chaque phrase avait droit a un objet JSON complet (~80 caracteres),
         y compris les 55 % de phrases purement narratives.
    Le format compact ecrit le nom d'un personnage UNE SEULE fois, ne
    demande que les personnages NOUVEAUX, et considere comme narration
    toute phrase absente des listes.
    """
    fiche_json = json.dumps(fiche_personnages, ensure_ascii=False)
    phrases_json = json.dumps(
        [{"id": s["id"], "texte": s["texte"]} for s in sentences],
        ensure_ascii=False
    )

    return f"""Tu analyses un chapitre de roman francais pour attribuer chaque phrase a son locuteur, en vue d'une narration audio avec une voix differente par personnage.

FICHE DE PERSONNAGES CONNUS (venant des chapitres precedents) :
{fiche_json}

PHRASES DU CHAPITRE (deja numerotees, ne pas modifier le texte, ne pas le reproduire dans ta reponse) :
{phrases_json}

CONSIGNES :
1. Pour chaque phrase, determine qui parle : "narration" (le narrateur) ou le nom canonique d'un personnage.
2. Reutilise en priorite les noms canoniques deja presents dans la fiche ci-dessus. REGLE ABSOLUE : si un personnage a deja un nom canonique dans la fiche, reutilise-le EXACTEMENT tel quel d'un chapitre a l'autre, meme si un autre nom te semblerait plus juste ou plus complet -- la coherence prime sur tout le reste.
3. Si un personnage nouveau apparait, ajoute-le a la fiche avec un nom canonique UNIQUE et EXPLICITE. Si plusieurs personnages pourraient partager le meme nom court (ex: un pere et un fils homonymes, ou deux personnes portant le meme prenom), desambiguise avec un suffixe souligne explicite, par exemple "Nom_pere" / "Nom_fils", "Nom_ainee" / "Nom_cadette" -- jamais un nom nu ambigu. ATTENTION : c'est une convention de nommage, pas une liste de personnages -- elle ne s'applique qu'aux personnages reellement presents dans le chapitre fourni. N'invente jamais un personnage qui n'apparait pas dans le texte.
4. Resous les designations indirectes ("le jeune homme", "sa fille", "l'inconnu"...) vers le nom canonique reel quand le contexte le permet clairement.
5. Pour chaque personnage de la fiche (nouveau ou existant) : genre ("H" ou "F"), et age approximatif ("jeune", "adulte", ou "age").
6. Si tu hesites sur le locuteur d'une phrase, mets son numero dans la liste "douteux" -- c'est la seule facon de signaler une incertitude dans ce format.
7. Si un personnage nouveau apparait, ajoute-le a "nouveaux" avec son nom canonique, son genre et son age. Ne recopie JAMAIS les personnages deja presents dans la fiche : ils sont deja enregistres.
8. Une phrase qui contient une repartie entre guillemets ET son incise narrative (« ... » dit Franz) va au PERSONNAGE qui parle, pas a "narration". MAIS une phrase qui ne contient AUCUN mot entre guillemets et qui n'est qu'une INCISE DE PAROLE -- « il m'a demande. », « dit-il. », « repondit le comte. », « demanda-t-elle. », « fit-il en riant. » -- est de la NARRATION : elle decrit qui parle, elle n'est PAS prononcee par lui. Cette regle s'applique MEME si la citation qui precede n'a pas ete refermee (guillemet fermant manquant, texte mal ponctue ou decoupage en plusieurs phrases).
9. Une citation entre guillemets peut se retrouver decoupee sur plusieurs phrases consecutives a cause d'un point d'exclamation ou d'interrogation present A L'INTERIEUR MEME de la citation, avant son guillemet fermant final (exemple : « Ah ! si vous saviez... » peut arriver decoupe en deux phrases distinctes : « Ah ! » puis si vous saviez.... Dans ce cas, verifie si le guillemet fermant » n'apparait pas encore : tant que la citation n'est pas refermee, TOUTES les phrases qui en font partie doivent recevoir EXACTEMENT le meme locuteur, du debut a la fin -- ne change jamais de locuteur au milieu d'une citation encore ouverte. SEULE EXCEPTION : une INCISE DE PAROLE isolee dans sa propre phrase (consigne 8) reste de la NARRATION.

Le livre analyse peut etre n'importe quel roman francais. Base-toi EXCLUSIVEMENT sur la fiche de personnages et le chapitre fournis ci-dessus : ne fais jamais appel a ta connaissance d'ouvrages existants pour inventer des noms, des personnages ou des liens.

Reponds UNIQUEMENT avec un JSON de cette forme exacte, sans texte autour, sans repeter le texte des phrases :
{{
  "nouveaux": [{{"nom": "...", "genre": "H", "age": "adulte"}}],
  "repliques": {{"Nom exact du personnage": [3, 5, 8]}},
  "douteux": []
}}

REGLES DE CE FORMAT, a respecter a la lettre :
- "nouveaux" : UNIQUEMENT les personnages qui ne figurent PAS deja dans la fiche ci-dessus. Ne recopie JAMAIS la fiche existante (elle est deja enregistree) ; si aucun personnage nouveau n'apparait, mets [].
- "repliques" : pour chaque personnage qui parle dans ce lot, la liste des numeros des phrases qu'il prononce. Le nom s'ecrit EXACTEMENT comme dans la fiche.
- "douteux" : la liste des numeros des phrases dont tu n'es pas certain -- souvent vide.
- Toute phrase qui n'apparait dans AUCUNE liste est consideree comme de la NARRATION : ne la mentionne pas du tout.
- N'utilise QUE les numeros de phrases fournis ci-dessus : n'invente jamais de numero, et n'oublie pas une phrase qui est bel et bien prononcee."""


# ==============================================================
# APPEL API GEMINI
# ==============================================================

# ==============================================================
# DIAGNOSTIC D'UN REFUS DE L'IA (session du 13/09/2026)
# ==============================================================
# Le 13/09/2026, une analyse s'est arretee avec le message
# "Reponse Gemini illisible : 'candidates'" : Google avait repondu, mais
# sans aucune proposition exploitable. La RAISON exacte (filtre de
# securite, texte protege, reponse coupee...) etait dans sa reponse et le
# programme la jetait -- impossible de comprendre l'echec, et l'argent de
# l'appel etait deja depense. On l'explique desormais en francais clair et
# on conserve la reponse brute dans data/journal_erreurs_gemini.log, pour
# pouvoir diagnostiquer sans refaire (et repayer) un appel.

class ReponseIllisible(RuntimeError):
    """
    Le fournisseur a repondu, mais sa reponse n'est pas exploitable : JSON
    malforme (une accolade au lieu d'un crochet, par exemple) ou structure
    inattendue.

    Verifie le 14/09/2026 : DeepSeek a produit un JSON invalide a la colonne
    459 d'un lot du tome 5 de Monte-Cristo, ce qui a fait **echouer tout le
    casting du livre** (15 chapitres traites, puis arret). Une generation est
    aleatoire : le meme lot renvoye une deuxieme fois donne tres souvent un
    JSON valide. D'ou la parade : NOUVEL ESSAI, puis decoupage du lot (voir
    _analyser_lot) -- et non l'arret du traitement.
    """


class BlocageContenu(RuntimeError):
    """
    Le fournisseur d'IA a refuse de TRAITER le texte envoye (filtre de
    securite), au lieu de mal repondre.

    Verifie le 13/09/2026 sur "un roman de 38 chapitres" : Google a renvoye
    promptFeedback.blockReason = PROHIBITED_CONTENT sur un lot de 150
    phrases, puis a ACCEPTE exactement le meme lot 20 minutes plus tard,
    sans aucune modification. Ce filtre est donc INTERMITTENT -- d'ou deux
    parades dans l'ordre : reessayer (voir _call_gemini), puis, si le refus
    persiste, reduire la taille du lot (voir _analyser_lot).
    """


def _expliquer_reponse_gemini(data: dict) -> str:
    """Traduit en francais la raison pour laquelle Gemini n'a renvoye
    aucune reponse exploitable."""
    if not isinstance(data, dict):
        return "Reponse inattendue (ce n'est pas du JSON)."

    feedback = data.get("promptFeedback") or {}
    blocage = feedback.get("blockReason")
    if blocage:
        return (f"Google a REFUSE la demande avant meme de repondre "
                f"(motif : {blocage}). Le texte envoye a ete arrete par ses filtres.")

    candidats = data.get("candidates")
    if isinstance(candidats, list):
        if not candidats:
            return "Google a renvoye une liste de reponses VIDE (aucune proposition)."
        fin = candidats[0].get("finishReason")
        return (f"La reponse de Google est vide (fin : {fin or 'inconnue'}) : "
                "la generation s'est arretee avant d'ecrire le texte attendu.")

    erreur = data.get("error")
    if erreur:
        return f"Google a signale une erreur : {erreur.get('message') or erreur}"

    return "La reponse de Google ne contient aucune proposition exploitable."


def _journaliser_reponse_gemini(data: dict, raison: str) -> str:
    """Ecrit la reponse brute de Google dans un fichier journal (jamais
    versionne : data/ et les .log sont ignores par Git). Retourne le chemin
    du fichier, ou un message d'echec -- cette fonction ne doit JAMAIS
    faire echouer l'analyse."""
    try:
        dossier = Path(__file__).resolve().parent.parent / "data"
        dossier.mkdir(exist_ok=True)
        chemin = dossier / "journal_erreurs_gemini.log"
        with open(chemin, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 70 + "\n")
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "  " + raison + "\n")
            f.write("--- Reponse brute de Google (limitee a 20000 caracteres) ---\n")
            f.write(json.dumps(data, ensure_ascii=False, indent=2)[:20000] + "\n")
        return str(chemin)
    except Exception as e:
        return f"journal indisponible ({e})"


# ==============================================================
# MESURE DU COUT REEL (session du 13/09/2026)
# ==============================================================
# L'estimation affichee avant lancement s'est revelee 2,5 a 3 fois trop
# basse sur "un roman de 38 chapitres" : ~1,48 $ annonces pour les 22 derniers chapitres,
# alors que la facture Google est passee de 14,96 € a 9,32 € (~4,24 € pour
# cette reprise seule, 5,64 € en tout). Cause principale presumee : les
# tokens de REFLEXION du modele, factures au tarif de sortie, que rien ne
# comptait. On enregistre desormais ce que le fournisseur annonce lui-meme
# (usageMetadata), et l'application peut afficher le cout reel.

JOURNAL_TOKENS = Path(__file__).resolve().parent.parent / "data" / "journal_tokens.csv"

_TOKENS_SESSION = {"appels": 0, "entree": 0, "sortie": 0, "reflexion": 0}


def _enregistrer_tokens(usage: dict, modele: str) -> None:
    """Cumule les tokens reellement factures, d'apres la reponse du
    fournisseur, et les ajoute au journal `data/journal_tokens.csv` (fichier
    local de mesure, non versionne).
    Ne doit JAMAIS faire echouer un traitement : toute erreur est ignoree.
    Seules les reponses REUSSIES sont comptees (un prompt refuse par un
    filtre ne produit aucun token de sortie)."""
    try:
        if not isinstance(usage, dict):
            return
        entree = int(usage.get("promptTokenCount") or 0)
        sortie = int(usage.get("candidatesTokenCount") or 0)
        reflexion = int(usage.get("thoughtsTokenCount") or 0)
        _TOKENS_SESSION["appels"] += 1
        _TOKENS_SESSION["entree"] += entree
        _TOKENS_SESSION["sortie"] += sortie
        _TOKENS_SESSION["reflexion"] += reflexion

        dossier = JOURNAL_TOKENS.parent
        dossier.mkdir(exist_ok=True)
        nouveau = not JOURNAL_TOKENS.exists()
        with open(JOURNAL_TOKENS, "a", encoding="utf-8") as f:
            if nouveau:
                f.write("horodatage;modele;tokens_entree;tokens_sortie;tokens_reflexion\n")
            f.write("{};{};{};{};{}\n".format(
                time.strftime("%Y-%m-%d %H:%M:%S"), modele, entree, sortie, reflexion))
    except Exception:
        pass


def tokens_session(provider: str = "gemini") -> dict:
    """Tokens cumules depuis le demarrage, avec le cout estime applique aux
    tarifs du moteur choisi (0 $ pour le moteur local). La reflexion (tokens
    de pensee) est facturee par Google comme de la SORTIE : elle est comptee
    comme telle."""
    cumul = dict(_TOKENS_SESSION)
    tarifs = PROVIDER_PRICES_USD.get(provider, PROVIDER_PRICES_USD["gemini"])
    cumul["cout_usd_estime"] = round(
        (cumul["entree"] / 1_000_000) * tarifs["in"]
        + ((cumul["sortie"] + cumul["reflexion"]) / 1_000_000) * tarifs["out"], 3)
    return cumul


async def _call_gemini(prompt: str) -> dict:
    api_key = get_gemini_api_key()

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "LOW"}
        }
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        res = None
        data = None
        blocages = 0
        for tentative in range(1, 7):
            try:
                res = await client.post(GEMINI_URL, headers=headers, json=body)
            except httpx.HTTPError as e:
                raise RuntimeError(f"Erreur reseau Gemini : {e}")

            if res.status_code == 400 and "thinkingConfig" in body.get("generationConfig", {}):
                # thinkingLevel refuse par cette version d'API -- on retente sans
                body["generationConfig"].pop("thinkingConfig", None)
                res = await client.post(GEMINI_URL, headers=headers, json=body)

            if res.status_code in (429, 503) and tentative < 6:
                # Surcarge temporaire cote Google (high demand) -- nouvel essai
                await asyncio.sleep(15)
                continue

            if res.status_code == 200:
                data = res.json()
                motif = (data.get("promptFeedback") or {}).get("blockReason")
                if motif and blocages < 3:
                    # Filtre de securite : il est INTERMITTENT (voir
                    # BlocageContenu). Un texte refuse ne genere rien, donc
                    # ce nouvel essai ne coute pas de tokens de sortie.
                    blocages += 1
                    print("   Filtre Google ({}) sur {} caracteres -- "
                          "nouvel essai {}/3...".format(motif, len(prompt), blocages))
                    await asyncio.sleep(10)
                    continue

            break

        if res.status_code != 200:
            raise RuntimeError(f"Gemini a repondu {res.status_code} : {res.text[:300]}")

        # Refus persistant : on le signale au code appelant par une exception
        # dediee, afin qu'il puisse retenter avec un lot plus petit.
        motif = (data.get("promptFeedback") or {}).get("blockReason")
        if motif:
            raison = _expliquer_reponse_gemini(data)
            chemin = _journaliser_reponse_gemini(data, raison)
            raise BlocageContenu(f"{raison} (reponse complete de Google : {chemin})")

        # Reponse acceptee : on compte ce que Google annonce avoir facture.
        _enregistrer_tokens(data.get("usageMetadata"), GEMINI_MODEL)

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raison = _expliquer_reponse_gemini(data)
        chemin = _journaliser_reponse_gemini(data, raison)
        raise ReponseIllisible(
            f"Reponse Gemini illisible : {e}. {raison} "
            f"(reponse complete de Google conservee dans {chemin})"
        )

    # Verrou de securite : meme si Gemini recopie/reformule du texte dans
    # sa reponse malgre la consigne, on le supprime activement ici. Seul
    # le champ "id" (numero de phrase) est utilise en aval -- le texte
    # source affiche et lu vient TOUJOURS de epub_parser.py, jamais d'une
    # reponse IA.
    for phrase in parsed.get("phrases", []):
        phrase.pop("texte", None)

    return parsed


async def _call_openai_compatible(prompt: str, url: str, api_key: str, model: str) -> dict:
    """
    Meme principe que _call_gemini, pour les APIs compatibles OpenAI
    (Mistral, DeepSeek) : reponse JSON forcee, retry sur surcharge,
    et meme verrou de securite (suppression du champ "texte" recopie).
    """
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "max_tokens": 16384
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        res = None
        for tentative in range(1, 6):
            try:
                res = await client.post(url, headers=headers, json=body)
            except httpx.HTTPError as e:
                raise RuntimeError(f"Erreur reseau ({model}) : {e}")

            if res.status_code in (429, 503) and tentative < 5:
                await asyncio.sleep(15)
                continue
            break

        if res.status_code != 200:
            raise RuntimeError(f"{model} a repondu {res.status_code} : {res.text[:300]}")

        data = res.json()

        # Mesure du cout reel, comme pour Gemini (session du 14/09/2026) : sans
        # cela, impossible de comparer le cout de DeepSeek ou Mistral. Ces
        # moteurs renvoient les memes informations dans "usage", avec des noms
        # de champs differents (format OpenAI).
        _enregistrer_tokens({
            "promptTokenCount": (data.get("usage") or {}).get("prompt_tokens"),
            "candidatesTokenCount": (data.get("usage") or {}).get("completion_tokens"),
            "thoughtsTokenCount": 0,
        }, model)

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise ReponseIllisible(f"Reponse {model} illisible (structure inattendue) : {e}")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        extrait = text[max(0, e.pos - 150):e.pos + 150]
        raise ReponseIllisible(
            f"Reponse {model} n'est pas un JSON valide : {e}\n"
            f"--- Extrait autour de l'erreur ---\n{extrait}\n"
            f"--- Fin de la reponse recue : {len(text)} caracteres, "
            f"se termine par : ...{text[-100:]}"
        )

    for phrase in parsed.get("phrases", []):
        phrase.pop("texte", None)

    return parsed


# ==============================================================
# MOTEUR LOCAL (Ollama) -- session du 13/09/2026
# ==============================================================
# Le meme travail peut etre confie a un modele de langage installe sur le
# poste : aucun euro, aucun texte envoye a l'exterieur, et AUCUN filtre de
# contenu -- un modele local accepte une scene violente que Google refuse.
# Contrepartie : qualite inferieure (mesuree : precision 34-46 % sur
# "un roman de 38 chapitres") et traitement plus lent (~1 h pour un livre entier).

def _modele_local_lourd(modele: str) -> bool:
    """Un modele de ~8B (5 Go) PLUS un contexte de 16 384 mots ne tient pas
    dans 8 Go de memoire video : Ollama renvoie alors 17 % du calcul sur le
    processeur, 20 a 50 fois plus lent (constat du 13/09/2026). On reduit
    donc le contexte pour ces modeles."""
    return any(x in (modele or "").lower()
               for x in ('qwen3', 'gemma', 'r1', '14b', '32b', 'aya', 'granite'))


def _enregistrer_tokens_ollama(data: dict, modele: str) -> None:
    """Compte les mots echanges avec le moteur local. Ils sont GRATUITS,
    mais les compter permet de comparer les modeles entre eux."""
    _enregistrer_tokens({
        "promptTokenCount": data.get("prompt_eval_count"),
        "candidatesTokenCount": data.get("eval_count"),
        "thoughtsTokenCount": 0,
    }, modele)


async def _call_ollama(prompt: str) -> dict:
    """
    Appel au modele de langage local (Ollama). Deux reglages sont
    indispensables :
      - num_ctx : Ollama bride le contexte a 4 096 mots par defaut, alors que
        le prompt en fait ~7 800. Sans ce reglage, le modele ne voit qu'une
        PARTIE du texte et "oublie" la moitie des repliques : 51 % d'accord
        avec la reference, contre 83 % apres correction ;
      - think=false : les modeles de raisonnement reflechissent longuement
        avant de repondre, ce qui est inutile pour cette tache repetitive.
    """
    modele = get_local_model()
    lourd = _modele_local_lourd(modele)
    corps = {
        "model": modele,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            # 10 240 pour les modeles de 8B : le prompt fait ~7 800 mots, il
            # faut de la place pour la reponse par-dessus. (Un essai a 8 192
            # avec une fiche compacte a degrade la qualite : voir BACKLOG.)
            "num_ctx": 10240 if lourd else 16384,
            "num_predict": 4096,
        },
    }
    if lourd:
        corps["think"] = False

    url = get_local_url().rstrip("/") + "/api/chat"
    try:
        async with httpx.AsyncClient(timeout=1800.0) as client:
            res = await client.post(url, json=corps)
    except httpx.HTTPError as e:
        raise RuntimeError(
            "Moteur local injoignable ({}). Verifie qu'Ollama tourne sur ce "
            "poste. Detail : {}".format(url, e)
        )

    if res.status_code != 200:
        raise RuntimeError("Moteur local : reponse {} : {}".format(
            res.status_code, res.text[:300]))

    data = res.json()
    _enregistrer_tokens_ollama(data, modele)
    texte = (data.get("message") or {}).get("content") or ""
    try:
        parsed = json.loads(texte)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Reponse du modele local illisible (JSON invalide) : {}".format(e))

    for phrase in parsed.get("phrases", []):
        if isinstance(phrase, dict):
            phrase.pop("texte", None)
    return parsed


def local_disponible() -> dict:
    """Etat du moteur local, pour l'interface : Ollama repond-il, et le
    modele configure est-il installe ? Aucun appel payant, aucun texte
    transmis."""
    modele = get_local_model()
    url = get_local_url().rstrip("/") + "/api/tags"
    try:
        with httpx.Client(timeout=4.0) as client:
            res = client.get(url)
        if res.status_code != 200:
            return {"disponible": False, "modele": modele,
                    "raison": "Ollama repond code {}".format(res.status_code)}
        modeles = [m.get("name", "") for m in (res.json().get("models") or [])]
        # Comparaison INSENSIBLE a la casse : Ollama renomme parfois
        # ("Qwen2.5:latest" alors que la configuration dit "qwen2.5:latest").
        cible = modele.lower()
        presentes = [m.lower() for m in modeles]
        present = any(m == cible or m.split(":")[0] == cible.split(":")[0]
                      for m in presentes)
        return {
            "disponible": present,
            "modele": modele,
            "modeles_installes": modeles,
            "raison": "" if present else "le modele '{}' n'est pas installe".format(modele),
        }
    except Exception as e:
        return {"disponible": False, "modele": modele,
                "raison": "Ollama ne repond pas ({})".format(str(e)[:80])}


async def _call_llm(prompt: str, provider: str = "gemini") -> dict:
    """
    Aiguillage vers le moteur choisi. "provider" attendu :
    "gemini" (defaut), "mistral" ou "deepseek".
    """
    if provider == "mistral":
        return await _call_openai_compatible(
            prompt, MISTRAL_URL, get_mistral_api_key(), "mistral-large-latest"
        )
    if provider == "deepseek":
        return await _call_openai_compatible(
            prompt, DEEPSEEK_URL, get_deepseek_api_key(), "deepseek-chat"
        )
    if provider == "local":
        # Modele de langage installe sur le poste : gratuit, sans filtre de
        # contenu, et le texte ne sort jamais de la machine.
        return await _call_ollama(prompt)
    return await _call_gemini(prompt)


def _harmonize_open_quotes(sentences: list, phrases: list) -> None:
    """
    Filet de securite deterministe (complement de la consigne 9) :
    quand une citation entre guillemets est coupee sur plusieurs
    phrases consecutives par le decoupage automatique (a cause d'un
    ! ou ? interne, avant le guillemet fermant final), force TOUTES
    les phrases du fragment a avoir le meme locuteur -- celui du
    fragment le plus fiable du groupe (non-narration, meilleure
    confiance, et en cas d'egalite le dernier -- il porte souvent
    l'incise "dit untel" qui permet d'identifier le vrai locuteur).
    Modifie "phrases" en place.

    Le guillemet fermant peut manquer (typographie frequente dans
    cette edition) : dans ce cas le fragment se termine des que la
    phrase suivante ne continue plus la citation -- nouvelle citation
    ("«"), nouveau tour de dialogue ("-"/"—"), ou debut en majuscule
    (une suite apres un ! ou ? interne reprend toujours en minuscule).
    """
    phrases_by_id = {p["id"]: p for p in phrases}
    confiance_rang = {"haute": 3, "moyenne": 2, "basse": 1}

    def _harmonize(span: list) -> None:
        if len(span) <= 1:
            return
        candidats = [
            phrases_by_id[i] for i in span
            if phrases_by_id.get(i, {}).get("locuteur") != "narration"
        ]
        if not candidats:
            return
        gagnant = candidats[0]
        for c in candidats[1:]:
            if confiance_rang.get(c.get("confiance"), 0) >= confiance_rang.get(gagnant.get("confiance"), 0):
                gagnant = c
        for i in span:
            p = phrases_by_id.get(i)
            if p and p["locuteur"] != gagnant["locuteur"]:
                p["locuteur"] = gagnant["locuteur"]
                p["confiance"] = "haute"
                p["anomalie"] = "locuteur harmonise automatiquement (citation fragmentee sur plusieurs phrases)"

    span = []
    balance = 0
    for s in sentences:
        texte = s["texte"]
        # Citation encore ouverte et la phrase suivante ne la continue pas :
        # le fragment est termine, on l'harmonise avant d'enchainer.
        if span and balance > 0:
            continue_la_citation = texte[0].islower() if texte else False
            if not continue_la_citation:
                _harmonize(span)
                span = []
                balance = 0
        span.append(s["id"])
        balance += texte.count("«") - texte.count("»")
        if balance <= 0:
            _harmonize(span)
            span = []
            balance = 0
    # Fragment final : citation encore ouverte en fin de chapitre
    _harmonize(span)


# ==============================================================
# TRAITEMENT D'UN CHAPITRE (PASSE 1)
# ==============================================================

BATCH_SIZE = 150  # phrases max envoyees par appel -- au-dela, certains
                  # moteurs (DeepSeek en tete) tronquent leur reponse
                  # avant la fin, meme avec un max_tokens genereux.

# Taille de paquet REDUITE pour le moteur local (session du 13/09/2026) : le
# prompt d'un paquet de 150 phrases fait ~5 800 mots, ce qui tient tout juste
# dans un contexte de 8 192 ; 130 phrases laissent une marge de securite pour
# les chapitres aux phrases longues. Sans cette marge, la reponse du modele
# serait tronquee. Avec la fiche compacte, le contexte redescend a 8 192 et
# la carte graphique suffit (plus de 20 a 50 fois plus lent).
# Le moteur local travaille aussi par paquets de BATCH_SIZE phrases : un essai
# de reduction a 130 phrases n'a rien apporte (voir BACKLOG, 14/09/2026).
BATCH_SIZE_LOCAL = 150


def _fusionner_fiches(fiche_a: list, fiche_b: list) -> list:
    """Fusionne deux fiches de personnages par leur nom (la premiere gagne).
    Utile quand un lot est coupe en deux : chaque moitie peut decouvrir des
    personnages differents, et aucun ne doit etre perdu."""
    vus = {}
    for fiche in (fiche_a or [], fiche_b or []):
        for p in fiche:
            if isinstance(p, dict) and p.get("nom"):
                vus.setdefault(p["nom"], p)
    return list(vus.values())


def _rattacher_au_canonique(nom: str, fiche: list) -> str:
    """
    Ramene un nom renvoye par l'IA sur le nom CANONIQUE de la fiche, quand la
    correspondance est certaine.

    Mesure du 14/09/2026 : une grande partie des « erreurs de personnage » du
    moteur local sont en fait de simples VARIANTES du bon nom -- « Al » pour
    « Al Templeton », « Frank Anicetti » pour « Frank Anicetti_pere »,
    « l'adolescent » pour « Adolescent ». Ce n'est pas une erreur
    d'identification, c'est un non-respect du nom canonique.

    On ne devine jamais : si plusieurs candidats sont possibles, le nom est
    laisse tel quel.
    """
    if not nom or not fiche:
        return nom
    noms = [p.get("nom") for p in fiche if isinstance(p, dict) and p.get("nom")]
    if nom in noms:
        return nom

    cle = normalize_character_name(nom)
    if not cle:
        return nom

    # 1. Meme nom a la casse, aux accents et aux articles pres.
    exacts = [n for n in noms if normalize_character_name(n) == cle]
    if len(exacts) == 1:
        return exacts[0]

    # 2. L'un est le DEBUT de l'autre ("Al" -> "Al Templeton").
    debut = [n for n in noms
             if normalize_character_name(n).startswith(cle + " ")
             or cle.startswith(normalize_character_name(n) + " ")]
    if len(debut) == 1:
        return debut[0]

    return nom


def _normaliser_reponse(result: dict, fiche: list, ids_envoyes: set) -> dict:
    """
    Ramene la reponse de l'IA a la structure interne attendue partout
    ailleurs : {"personnages": [...], "phrases": [{"id", "locuteur",
    "confiance", "anomalie"}]}.

    Deux formats sont acceptes :
      - le format COMPACT (celui du prompt actuel) : {"nouveaux": [...],
        "repliques": {"Nom": [ids]}, "douteux": [ids]}. Toute phrase absente
        des listes est de la narration : on l'ajoute ici explicitement, avec
        une confiance haute, pour que le filet de securite de
        analyze_chapter ne la signale pas a tort comme "oubliee par l'IA" ;
      - l'ancien format verbeux, CONSERVE EN SECOURS : si un moteur repond a
        l'ancienne mode, rien ne casse.
    """
    if not isinstance(result, dict):
        raise ReponseIllisible("Reponse IA illisible : ce n'est pas un objet JSON.")

    # --- Ancien format : on le laisse passer tel quel ---
    if isinstance(result.get("phrases"), list):
        return {
            "personnages": result.get("personnages") or fiche,
            "phrases": result["phrases"],
        }

    # --- Format compact ---
    repliques = result.get("repliques")
    if not isinstance(repliques, dict):
        # ReponseIllisible (et non RuntimeError) : c'est ce qui permet a
        # _analyser_lot de REESSAYER le lot au lieu d'arreter tout le casting.
        # Oubli corrige le 14/09/2026, apres un arret reel sur le chapitre 31
        # de Notre-Dame de Paris.
        raise ReponseIllisible(
            "Reponse IA illisible : ni 'repliques' ni 'phrases' dans la reponse."
        )

    douteux = set()
    for x in (result.get("douteux") or []):
        try:
            douteux.add(int(x))
        except (TypeError, ValueError):
            continue

    phrases = []
    vus = set()
    for nom, ids in repliques.items():
        nom = (nom or "").strip()
        if not nom or not isinstance(ids, list):
            continue
        # Le nom est ramene au nom canonique de la fiche quand la
        # correspondance est certaine (voir _rattacher_au_canonique).
        nom = _rattacher_au_canonique(nom, fiche)
        for x in ids:
            try:
                i = int(x)
            except (TypeError, ValueError):
                continue
            # Securite : un numero inconnu (invente par l'IA) est ignore -- il
            # ne doit jamais atteindre la base.
            if i not in ids_envoyes or i in vus:
                continue
            vus.add(i)
            phrases.append({
                "id": i,
                "locuteur": nom,
                "confiance": "basse" if i in douteux else "haute",
                "anomalie": "locuteur incertain (signale par l'IA)" if i in douteux else None,
            })

    # Tout le reste est de la narration.
    for i in sorted(ids_envoyes - vus):
        phrases.append({
            "id": i,
            "locuteur": "narration",
            "confiance": "haute",
            "anomalie": None,
        })

    phrases.sort(key=lambda p: p["id"])
    return {
        "personnages": _fusionner_fiches(fiche, result.get("nouveaux") or []),
        "phrases": phrases,
    }


# Nombre maximal de lots abandonnes (phrases laissees au narrateur) sur un
# chapitre : borne le nombre d'appels si un contenu est massivement refuse.
MAX_LOTS_ABANDONNES = 25


async def _analyser_lot(fiche: list, batch: list, provider: str, refusees: set,
                        profondeur: int = 0) -> dict:
    """
    Analyse un lot de phrases, en se protegeant de deux facons differentes de
    mal se passer cote fournisseur :
      1. REFUS DE TRAITER LE TEXTE (filtre de securite, verifie le 13/09/2026
         sur "un roman de 38 chapitres") : _call_gemini reessaie deja un refus passager, car ce
         filtre est intermittent ;
      2. REPONSE ILLISIBLE (JSON malforme -- verifie le 14/09/2026 : DeepSeek a
         produit une accolade au lieu d'un crochet, ce qui faisait echouer TOUT
         le casting du livre) : on RENVOIE le meme lot, car une generation est
         aleatoire et un JSON valide arrive tres souvent du deuxieme coup.
    Si l'un ou l'autre resiste :
      - le lot est coupe en deux et chaque moitie repart separement ;
      - une phrase seule encore en echec est abandonnee, et son id est ajoute a
        "refusees" : le filet de securite de analyze_chapter l'attribuera au
        narrateur, en inscrivant la raison dans la fiche.
    """
    ids_envoyes = {s["id"] for s in batch}
    erreur = None

    for essai in range(1, 4):
        try:
            resultat = await _call_llm(_build_prompt(fiche, batch), provider)
            return _normaliser_reponse(resultat, fiche, ids_envoyes)
        except BlocageContenu as e:
            # Inutile de retenter ici : _call_gemini a deja fait ses reessais.
            erreur = e
            break
        except ReponseIllisible as e:
            erreur = e
            if essai < 3:
                print("   Reponse illisible (essai {}/3) -- nouvel essai.".format(essai))
                continue

    # Echec persistant : on reduit le lot, puis on abandonne les dernieres
    # phrases qui resistent encore.
    if len(batch) <= 1:
        print("   Phrase {} non attribuable ({}) -- donnee au narrateur.".format(
            batch[0]["id"], str(erreur)[:90]))
        refusees.add(batch[0]["id"])
        return {"personnages": [], "phrases": []}

    if len(refusees) >= MAX_LOTS_ABANDONNES:
        print("   Trop d'echecs sur ce chapitre : le reste passe au narrateur.")
        for s in batch:
            refusees.add(s["id"])
        return {"personnages": [], "phrases": []}

    milieu = len(batch) // 2
    print("   Lot de {} phrases en echec -- coupe en deux ({} + {}) et renvoye.".format(
        len(batch), milieu, len(batch) - milieu))

    resultat = {"personnages": [], "phrases": []}
    for moitie in (batch[:milieu], batch[milieu:]):
        sous = await _analyser_lot(fiche, moitie, provider, refusees, profondeur + 1)
        # Fusion par nom : chaque moitie peut decouvrir des personnages
        # differents, aucun ne doit etre perdu.
        resultat["personnages"] = _fusionner_fiches(
            resultat["personnages"], sous.get("personnages") or []
        )
        resultat["phrases"].extend(sous.get("phrases", []))
    return resultat


async def _rattraper_refusees(sentences: list, phrases: list, refusees: set,
                              fiche: list, replis: list) -> int:
    """
    Un moteur distant a REFUSE certaines phrases (filtre de contenu). On les
    confie a des moteurs de SECOURS, essayes dans l'ordre (session du
    14/09/2026).

    Pourquoi un ordre : DeepSeek rend un resultat quasi identique a Gemini
    (97,3 % d'accord, mesure) pour environ 1 centime par chapitre, alors que le
    moteur LOCAL ruinait le resultat a l'ecoute (verdict du 14/09/2026). Le
    local ne sert donc plus que si aucun moteur distant n'accepte le texte.

    Les phrases sont regroupees par lots, dans l'ordre du chapitre, pour
    conserver un minimum de contexte. Toute erreur est absorbee : l'echec d'un
    moteur de secours ne doit jamais faire echouer le chapitre entier.
    """
    if not replis:
        return 0

    par_id_phrases = {p["id"]: p for p in phrases}
    a_traiter = {s["id"]: s for s in sentences if s["id"] in refusees}
    corrigees = 0

    for moteur in replis:
        if not a_traiter:
            break
        lot_complet = list(a_traiter.values())
        print("   {} phrase(s) refusee(s) -- rattrapage avec le moteur {}.".format(
            len(lot_complet), moteur))
        recuperees = set()
        for i in range(0, len(lot_complet), BATCH_SIZE_LOCAL):
            lot = lot_complet[i:i + BATCH_SIZE_LOCAL]
            try:
                resultat = await _analyser_lot(fiche, lot, moteur, set())
            except Exception as e:
                print("   Rattrapage avec {} impossible : {}".format(moteur, str(e)[:140]))
                continue
            for p in resultat.get("phrases", []):
                cible = par_id_phrases.get(p["id"])
                if cible is None or p.get("locuteur") in (None, "narration"):
                    continue
                cible["locuteur"] = p["locuteur"]
                cible["confiance"] = p.get("confiance", "moyenne")
                cible["anomalie"] = ("rattrapee par {} (refusee par le moteur "
                                     "principal)".format(moteur))
                corrigees += 1
                recuperees.add(p["id"])

        for i in recuperees:
            a_traiter.pop(i, None)
        if recuperees:
            print("   {} phrase(s) rattrapee(s) par {}.".format(len(recuperees), moteur))

    return corrigees


# ==============================================================
# CONTROLE DE VRAISEMBLANCE DES REPLIQUES (moteur local uniquement)
# ==============================================================
# Mesure du 14/09/2026 sur un chapitre de "un roman de 38 chapitres" : le moteur local avait
# invente 180 dialogues, et 152 d'entre eux ne portaient AUCUN signe de
# dialogue (ni guillemet, ni tiret cadratin, ni verbe de parole).
#
# Deux reglages ont ete mesures, AUCUN n'apporte de gain net :
#   - filtre strict : accord 77 % MAIS rappel effondre de 82 % a 45 % (trop de
#     vraies repliques perdues, a cause des repliques au tiret qui courent sur
#     plusieurs phrases) ;
#   - filtre avec garde-fou (phrase suivant une replique du meme personnage) :
#     rappel 76 %, precision 54 %, accord 69 % -- soit a peine mieux que les
#     67 % de depart, pour une regle en plus.
# Le controle est donc DESACTIVE, mais conserve et documente : il pourrait
# devenir utile sur un roman aux dialogues plus clairement marques (guillemets
# systematiques), ou combine a une meilleure detection des suites de replique.
ACTIVER_FILTRE_VRAISEMBLANCE = False

_RE_MARQUE_DIALOGUE = re.compile(r'[«»"]|\u2014|(^|\s)[-–]\s')
_RE_VERBE_PAROLE = re.compile(
    r"\b(dit|dis|répond|repond|demand|s'écri|s'ecri|murmur|ajout|reprit|"
    r"soupir|grommel|poursuiv|observ|reprenn|répét|repet|cria|appela|"
    r"expliqu|avou|annonc|annonç|protest|conclut|lança|lanca|hasarda|"
    r"marmonna|bougonna|rican|s'exclam)", re.IGNORECASE)


def _a_un_signe_de_dialogue(texte: str) -> bool:
    """La phrase porte-t-elle un signe objectif de dialogue ? (independant de
    toute IA : guillemets, tiret de dialogue, verbe de parole)"""
    return bool(_RE_MARQUE_DIALOGUE.search(texte) or _RE_VERBE_PAROLE.search(texte))


def _filtrer_repliques_non_vraisemblables(sentences: list, phrases: list) -> int:
    """
    Controle de vraisemblance EN SORTIE, reserve au moteur LOCAL (le moteur
    distant est fiable : c'est lui qui sert de reference).

    Toute phrase attribuee a un personnage alors qu'elle ne porte aucun signe
    de dialogue -- et qu'elle n'est pas a l'interieur d'une citation encore
    ouverte -- est rendue au narrateur.

    La seconde precaution est essentielle : une longue replique est decoupee
    en plusieurs phrases et seule la PREMIERE porte le tiret cadratin. Deux
    garde-fous evitent donc d'amputer les vraies repliques :
      - une phrase situee dans une citation encore ouverte (« ... ») ;
      - une phrase qui SUIT une replique du meme personnage : dans le style
        francais, une replique au tiret peut courir sur plusieurs phrases,
        seule la premiere portant le tiret.
    Sans le second garde-fou, le rappel chutait de 82 % a 45 % (mesure).
    """
    par_id = {p["id"]: p for p in phrases}
    citation_ouverte = 0
    dernier_locuteur = None
    retires = 0
    for s in sentences:
        texte = s["texte"]
        # Une citation non refermee se termine des que la phrase suivante ne la
        # continue plus (meme regle que _harmonize_open_quotes).
        if citation_ouverte > 0 and texte and not texte[0].islower():
            citation_ouverte = 0

        p = par_id.get(s["id"])
        locuteur_avant = p.get("locuteur") if p is not None else None
        if (p is not None
                and locuteur_avant not in (None, "narration")
                and citation_ouverte == 0
                and not _a_un_signe_de_dialogue(texte)
                and locuteur_avant != dernier_locuteur):
            p["locuteur"] = "narration"
            p["confiance"] = "basse"
            p["anomalie"] = ("remise au narrateur : aucun signe de dialogue "
                             "(controle de vraisemblance)")
            retires += 1

        # On retient le locuteur PROPOSE (avant tout retrait) : la phrase
        # suivante du meme personnage est consideree comme la suite de sa
        # replique, et donc conservee.
        dernier_locuteur = locuteur_avant

        citation_ouverte += texte.count("«") - texte.count("»")
        if citation_ouverte < 0:
            citation_ouverte = 0
    return retires


async def analyze_chapter(chapter_text: str, fiche_personnages: list, provider: str = "gemini",
                          provider_repli: str = None) -> dict:
    """
    Analyse un chapitre : decoupe en phrases, appelle le moteur choisi
    (provider : "gemini", "mistral" ou "deepseek"), retourne la fiche
    mise a jour + l'attribution phrase par phrase.
    Les chapitres longs (plus de BATCH_SIZE phrases) sont traites en
    plusieurs appels successifs plutot qu'un seul, pour ne jamais
    depasser ce que le moteur peut renvoyer d'un coup -- la fiche de
    personnages voyage d'un morceau a l'autre exactement comme elle
    voyage deja d'un chapitre a l'autre.

    provider_repli (optionnel) : moteur(s) de secours, essayes DANS L'ORDRE,
    uniquement pour les phrases que le moteur principal a refusees (filtre de
    contenu). Accepte une chaine ("local") ou une liste
    (["deepseek", "local"]). En pratique (mesures du 14/09/2026) : DeepSeek
    d'abord -- resultat quasi identique a Gemini pour ~1 centime par chapitre --
    et le moteur local en tout dernier recours seulement.
    """
    sentences = _split_chapter_sentences(chapter_text)
    if not sentences:
        return {"personnages": fiche_personnages, "phrases": [], "sentences": []}

    fiche = fiche_personnages
    phrases = []

    refusees = set()
    # Le moteur local travaille par paquets plus petits : son contexte est
    # limite par la memoire de la carte graphique (voir BATCH_SIZE_LOCAL).
    taille_paquet = BATCH_SIZE_LOCAL if provider == "local" else BATCH_SIZE
    for i in range(0, len(sentences), taille_paquet):
        batch = sentences[i:i + taille_paquet]
        # _analyser_lot protege du refus de filtre du fournisseur : nouvel
        # essai, puis reduction du lot si le refus persiste.
        result = await _analyser_lot(fiche, batch, provider, refusees)
        # Une fiche vide renvoyee par l'IA ne remplace jamais la fiche
        # accumulee (cas vu en production) : sans ce garde-fou, toute la
        # fiche du livre est perdue et la Passe 2 est court-circuitée.
        personnages = result.get("personnages")
        if not personnages:
            personnages = fiche
        fiche = personnages
        phrases.extend(result.get("phrases", []))

    # Filet de securite : si l'IA a saute une phrase dans sa reponse
    # (arrive parfois sur de longues listes), on la complete nous-memes
    # avec "narration" par defaut plutot que de la laisser sans voix.
    # Deux causes bien distinctes, annoncees clairement dans la fiche :
    # la phrase a ete refusee par le filtre du fournisseur, ou l'IA l'a
    # simplement oubliee dans sa reponse.
    ids_recus = {p["id"] for p in phrases}
    for s in sentences:
        if s["id"] not in ids_recus:
            if s["id"] in refusees:
                anomalie = ("non attribuable automatiquement (refus du filtre ou "
                            "reponse illisible) -- laissee au narrateur, a corriger "
                            "a la main si besoin")
            else:
                anomalie = "id absent de la reponse IA -- complete automatiquement"
            phrases.append({
                "id": s["id"],
                "locuteur": "narration",
                "confiance": "basse",
                "anomalie": anomalie
            })
    # Controle de vraisemblance, reserve au moteur LOCAL (desactive par
    # defaut : voir ACTIVER_FILTRE_VRAISEMBLANCE, aucun gain net mesure).
    if provider == "local" and ACTIVER_FILTRE_VRAISEMBLANCE:
        retires = _filtrer_repliques_non_vraisemblables(sentences, phrases)
        if retires:
            print("   Controle de vraisemblance : {} phrase(s) rendue(s) au narrateur.".format(retires))

    phrases.sort(key=lambda p: p["id"])
    _harmonize_open_quotes(sentences, phrases)

    # Filet de dernier recours : les phrases que le moteur distant a REFUSEES
    # (filtre de contenu) sont confiees au moteur local, qui n'applique aucun
    # filtre. Sans cela, ces passages -- souvent les plus violents du roman --
    # resteraient lus par le narrateur.
    # Moteurs de secours, essayes dans l'ordre : on accepte une chaine ou une
    # liste. Aucun n'est essaye s'il est identique au moteur principal.
    replis = provider_repli
    if isinstance(replis, str):
        replis = [replis]
    replis = [r for r in (replis or []) if r and r != provider]
    if refusees and replis:
        await _rattraper_refusees(sentences, phrases, refusees, fiche, replis)

    return {
        "personnages": fiche,
        "phrases": phrases,
        "sentences": sentences,
        "refusees": sorted(refusees),
    }


# ==============================================================
# TRAITEMENT SEQUENTIEL DE PLUSIEURS CHAPITRES
# ==============================================================

async def analyze_chapters(chapters: list) -> list:
    """
    Traite une liste de chapitres a la suite, en faisant voyager la fiche
    de personnages de l'un a l'autre (elle s'enrichit au fil de l'eau,
    comme prevu dans l'architecture).

    chapters : liste de textes bruts, dans l'ordre de lecture.
    Retourne une liste de resultats (meme structure que analyze_chapter),
    un par chapitre, dans le meme ordre.
    """
    fiche = []
    resultats = []

    for chapter_text in chapters:
        result = await analyze_chapter(chapter_text, fiche_personnages=fiche)
        fiche = result["personnages"]
        resultats.append(result)

    return resultats


# ==============================================================
# REPRISE APRES ERREUR : DEVINER LE GENRE D'UN NOM
# ==============================================================
# Sert UNIQUEMENT dans un cas precis (session du 13/09/2026) : un livre
# dont l'analyse s'est arretee en cours de route AVANT que la fiche de
# personnages ne soit memorisee en base (voir table cast_fiche, main.py).
# Les noms de personnages sont alors lisibles en base, mais leur genre
# n'y est pas stocke -- le prenom est le seul indice disponible.
#
# Une erreur ici ne casse rien : elle donne simplement une voix d'homme
# a une femme (ou l'inverse), ce qui se corrige en deux clics dans la
# fenetre du casting. C'est infiniment preferable a refaire payer les
# chapitres deja analyses.

_PRENOMS_F = {
    "adeline", "agathe", "agnes", "alice", "amelie", "anna", "anne", "annette",
    "ariane", "audrey", "aurelie", "beatrix", "beatrice", "bernadette",
    "berthe", "beverly", "blanche", "brigitte", "camille", "caroline",
    "catherine", "cecile", "chantal", "charlotte", "christiane", "christine",
    "claire", "clara", "clemence", "colette", "constance", "corinne",
    "delphine", "denise", "diane", "edith", "eleanor", "elisabeth", "elise",
    "elodie", "eloise", "emilie", "emma", "ellen", "estelle", "eugenie",
    "fabienne", "fanny", "florence", "francoise", "gabrielle", "genevieve",
    "georgette", "germaine", "gisele", "helene", "henriette", "hortense",
    "isabelle", "jacqueline", "jeanne", "jeannette", "jenny", "josephine",
    "julie", "juliette", "justine", "kate", "katherine", "laure", "laurence",
    "leonie", "lucie", "louise", "madeleine", "manon", "marcelle",
    "marguerite", "marie", "marianne", "marthe", "mathilde", "maud",
    "melanie", "michele", "mimi", "monique", "nadine", "nathalie", "nicole",
    "nina", "noemie", "odette", "olga", "pauline", "paulette", "peggy",
    "penelope", "rachel", "renee", "rita", "rose", "rosalie", "sabine",
    "sadie", "sally", "sarah", "severine", "simone", "sophie", "stephanie",
    "suzanne", "sylvie", "therese", "valentine", "valerie", "veronique",
    "victorine", "virginie", "vivianne", "yvette", "yvonne", "zoe",
}

# Termes generiques qui trahissent un personnage feminin meme quand le
# prenom est inconnu ("la jeune fille", "Mme Verdier", "seur Marthe"...).
_MOTS_F = (
    "femme", "fille", "mere", "dame", "madame", "mademoiselle", "mme",
    "mlle", "seur", "soeur", "tante", "grand-mere", "veuve", "epouse",
    "marquise", "comtesse", "duchesse", "baronne", "princesse", "reine",
    "servante", "cuisiniere", "bonne", "nourrice", "institutrice",
)


def deviner_genre(nom: str) -> str:
    """
    Devine H/F a partir d'un nom de personnage, sans appel IA.
    Retourne "F" si le prenom est dans la liste feminine ou si le nom
    contient un terme forcement feminin ; "H" dans tous les autres cas
    (y compris en cas de doute -- le doute est corrigeable a la main).
    """
    s = normalize_character_name(nom)
    if not s:
        return "H"
    mots = s.split()
    if mots and mots[0] in _PRENOMS_F:
        return "F"
    for mot in mots:
        if mot in _MOTS_F:
            return "F"
    return "H"


# ==============================================================
# PASSE 2 -- CONSOLIDATION ET ATTRIBUTION DES VOIX
# ==============================================================

# Voix dediees proposees a l'attribution automatique des personnages.
#
# REGLE DES PALIERS (decision de Laurent, 15/09/2026 -- elle remplace l'ordre
# du 14/09/2026) : le pool se parcourt par PALIERS D'ETOILES (3, puis 2, puis
# 1) et, dans chaque palier, les moteurs se suivent toujours dans le meme
# ordre : Edge, puis XTTS v2, puis Kokoro. Autrement dit : les 3 etoiles Edge,
# puis les 3 etoiles XTTS, puis les 3 etoiles Kokoro, puis on recommence a
# 2 etoiles (Edge, XTTS, Kokoro), etc.
# Une voix notee 0 etoile a l'ecoute est ECARTEE du pool automatique, sur tous
# les moteurs (elle reste choisissable a la main) : c'est le moyen de retirer
# une voix du casting automatique.
#
# Voix Edge exclues du pool, raisons inchangees :
# - Ariane : voix par defaut du narrateur (DEFAULT_VOICE) ;
# - Vivienne : voix "Multilingual" au passe de deraillement linguistique ;
# - Eloise / Fabrice : remplacees par les voix Piper Siwis/Tom pour les petits
#   roles (decision du 14/09/2026).
# Piper reste hors du pool automatique (voix jugees inaudibles a l'ecoute
# reelle par Laurent), mais sert la voix generique des petits roles ci-dessous.
# Kyutai reste hors du pool automatique depuis le 14/09/2026 (il demeure
# choisissable a la main) : la fonction _kyutai_pool() est conservee pour
# pouvoir revenir en arriere en une ligne.
_EDGE_POOL_F = ["fr-FR-DeniseNeural", "fr-BE-CharlineNeural",
                "fr-CA-SylvieNeural"]
_EDGE_POOL_M = ["fr-FR-HenriNeural", "fr-FR-RemyMultilingualNeural",
                "fr-BE-GerardNeural", "fr-CA-AntoineNeural",
                "fr-CA-JeanNeural"]

# Notes (etoiles) des voix Edge : elles vivent dans FRENCH_VOICES, cote
# main.py, et sont TRANSMISES ici au demarrage par definir_voix_edge(). Une
# seule liste fait ainsi reference -- celle que met a jour le report des notes
# d'ecoute (test_voix/_appliquer_annotations_voix.py). Les valeurs ci-dessous
# ne sont qu'un repli, pour un test qui n'appellerait pas la fonction ; elles
# correspondent au catalogue Edge du 15/09/2026.
_EDGE_STARS = {
    "fr-FR-DeniseNeural": 3,
    "fr-BE-CharlineNeural": 2,
    "fr-CA-SylvieNeural": 2,
    "fr-FR-HenriNeural": 3,
    "fr-FR-RemyMultilingualNeural": 3,
    "fr-BE-GerardNeural": 2,
    "fr-CA-AntoineNeural": 0,
    "fr-CA-JeanNeural": 0,
}


def _notes(catalogue: list) -> dict:
    """{identifiant: etoiles} d'un catalogue de voix."""
    return {v["id"]: int(v.get("stars", 0)) for v in catalogue}


def _edge_pool(genre: str) -> tuple:
    """(identifiants Edge du pool, etoiles correspondantes), dans l'ordre du
    catalogue. Les voix notees 0 sont retirees ici : c'est le filtre qui les
    ecarte du pool automatique."""
    identifiants = _EDGE_POOL_F if genre == "F" else _EDGE_POOL_M
    retenues = [i for i in identifiants if int(_EDGE_STARS.get(i, 0)) > 0]
    return retenues, _EDGE_STARS


def _pool_par_paliers(genre: str) -> list:
    """Pool automatique d'un genre, par paliers d'etoiles.

    Paliers 3 -> 2 -> 1 etoile ; dans chaque palier, Edge, puis XTTS v2, puis
    Kokoro (decision de Laurent du 15/09/2026), et EN DERNIER les voix NeuTTS
    (ajout du 16/09/2026). A etoile egale et dans un meme moteur, l'ordre du
    catalogue est conserve : assign_voices traite les personnages du plus
    present au moins present, donc les meilleurs timbres partent aux roles
    principaux.

    POURQUOI NEUTTS EN DERNIER (et non en tete, alors que c'est le moteur le
    plus stable) : le pool automatique ne connait PAS l'etat des moteurs, et
    une voix dont le moteur est eteint ne serait pas lisible. XTTS et NeuTTS
    occupent tous les deux la carte graphique (un seul a la fois), donc mettre
    NeuTTS devant XTTS aurait envoye un nouveau casting vers des voix
    indisponibles. En dernier, il sert quand les autres sont epuises -- ce qui
    est deja beaucoup sur un livre a 175 personnages -- et Laurent le choisit
    a la main pour l'essayer. Deplacer cette ligne suffit a changer l'ordre.
    """
    edge, notes_edge = _edge_pool(genre)
    # ORDRE ET CONTENU REVUS LE 17/09/2026, apres un re-cast rate :
    #   - Kyutai EN PREMIER : c'est le moteur que START.bat allume, donc le seul
    #     gros moteur dont les voix sont LISIBLES sans rien faire de plus ;
    #   - puis Edge (toujours disponible, en ligne) et Kokoro (local) ;
    #   - XTTS et NeuTTS sont RETIRES du pool : leur moteur n'est plus allume
    #     automatiquement, et une voix dont le moteur est ETEINT ne produit RIEN
    #     (le lecteur affiche « erreur »). Mesure du 17/09/2026 : un re-cast
    #     lance a 18h00 sur le livre 28 avait distribue 31 voix XTTS et 47 voix
    #     NeuTTS, toutes muettes, et laisse 84 personnages sans voix.
    #     Ils restent choisissables A LA MAIN dans la fenetre du casting.
    familles = (
        (_kyutai_pool(genre), _notes(KYUTAI_VOICES)),
        (edge, notes_edge),
        ([v["id"] for v in KOKORO_VOICES if v.get("gender") == genre],
         _notes(KOKORO_VOICES)),
    )
    pool = []
    for etoiles in (3, 2, 1):
        for identifiants, notes in familles:
            pool.extend(i for i in identifiants if notes.get(i, 0) == etoiles)
    return pool


def definir_voix_edge(voix_edge: list) -> None:
    """Transmet les notes des voix Edge et reconstruit le pool automatique.

    Appelee par main.py au demarrage, juste apres FRENCH_VOICES : les etoiles
    des voix Edge (et leurs corrections eventuelles dans la fenetre « Ecouter
    les voix ») n'existent qu'a cet endroit, et c'est ce qui evite d'avoir
    deux listes a tenir a jour.
    """
    for voix in voix_edge:
        identifiant = voix.get("id")
        if identifiant in _EDGE_STARS:
            _EDGE_STARS[identifiant] = int(voix.get("stars", 0))
    _recalculer_pools()


def _recalculer_pools() -> None:
    """(Re)compose DEDICATED_VOICES_F/M selon la regle des paliers."""
    global DEDICATED_VOICES_F, DEDICATED_VOICES_M
    DEDICATED_VOICES_F = _pool_par_paliers("F")
    DEDICATED_VOICES_M = _pool_par_paliers("M")


def _kyutai_pool(genre: str) -> list:
    """Voix Kyutai d'un genre, triees par note (stars) decroissante.

    ATTENTION (14/09/2026) : cette fonction n'est PLUS utilisee pour
    composer DEDICATED_VOICES_F/M -- Kyutai a ete retire du pool
    automatique au profit de XTTS v2 (decision de Laurent du 14/09/2026,
    voir plus bas). Elle est conservee telle quelle pour pouvoir revenir
    en arriere facilement, et parce que les voix Kyutai restent
    choisissables A LA MAIN (elles sont toujours dans le catalogue).

    Historique -- choix de Laurent (12/09/2026) : les voix Kyutai
    passaient **en premier** dans le pool automatique, avant Edge et
    Kokoro -- ce sont des timbres francais NATIFS (les 35 voix libres de
    Kyutai, etiquetees a l'ecoute).

    Une voix notee 0 etoile a l'ecoute (la n° 33) est EXCLUE : elle reste
    choisissable a la main, comme les voix Piper ecartees.

    A savoir : ces voix ne fonctionnent que si le moteur Kyutai est allume
    (DEMARRER_KYUTAI.bat). Un livre caste avec elles demande donc le moteur
    pour etre ecoute -- sinon le lecteur affiche un message clair.
    """
    voix = [v for v in KYUTAI_VOICES
            if v.get("gender") == genre and int(v.get("stars", 0)) > 0]
    voix.sort(key=lambda v: -int(v.get("stars", 0)))
    return [v["id"] for v in voix]


# Composition effective des deux pools, selon la regle des paliers decrite
# plus haut. Elle est refaite des que main.py transmet les notes des voix Edge
# (definir_voix_edge), pour que le report des notes d'ecoute soit pris en
# compte sans redemarrage du code.
_recalculer_pools()

# Voix partagee pour les personnages mineurs (peu de repliques) -- Piper
# depuis le 14/09/2026 (decision de Laurent : Siwis/Tom remplacent
# Eloise/Fabrice). Piper reste par ailleurs hors du pool automatique
# ci-dessus, uniquement utilise ici pour les petits roles.
#
# ATTENTION (15/09/2026) : ces deux voix ne sont PLUS attribuees par defaut.
# A l'ecoute de Shantaram, Laurent les a trouvees « inaudibles, vraiment
# moches » : les petits roles (< MINOR_THRESHOLD repliques) sont desormais lus
# par le NARRATEUR (voir assign_voices). Ces deux constantes restent donc
# comme EMPLACEMENT des deux voix neutres que Laurent choisira plus tard
# (une femme, un homme) : il suffira de les y mettre, puis de re-caster.
GENERIC_VOICE_F = "piper:siwis:0"
GENERIC_VOICE_M = "piper:tom:0"

PITCH_BY_AGE = {"jeune": "+15Hz", "adulte": "+0Hz", "age": "-15Hz"}
# Personnages avec moins de ce nombre de repliques sur TOUT le livre ->
# voix generique partagee par genre (ils ne consomment pas une voix dediee,
# ce qui preserve le pool pour les roles qui comptent vraiment).
MINOR_THRESHOLD = 8


def _build_passe2_prompt(fiche_brute: list) -> str:
    fiche_json = json.dumps(fiche_brute, ensure_ascii=False)
    return f"""Tu consolides la fiche de personnages d'un roman francais, construite au fil de la lecture chapitre par chapitre. Elle contient parfois des doublons (le meme personnage nomme differemment a deux endroits, ex: "Matelot" et "Matelots").

FICHE BRUTE :
{fiche_json}

CONSIGNES :
1. Identifie les doublons evidents (variantes d'un meme personnage : pluriel/singulier, orthographe legerement differente, meme role generique repete).
2. Pour chaque nom de la fiche brute, indique vers quel nom canonique final il doit etre fusionne (peut etre lui-meme s'il n'a pas de doublon).
3. Produis la liste finale des personnages uniques (genre, age), sans doublons.
4. Ne fusionne PAS deux personnages differents juste parce qu'ils se ressemblent -- en cas de doute, garde-les separes.

Reponds UNIQUEMENT avec un JSON de cette forme exacte :
{{
  "fusion": {{"nom_original_1": "nom_final", "nom_original_2": "nom_final"}},
  "personnages": [{{"nom": "nom_final", "genre": "H", "age": "adulte"}}]
}}

Le dictionnaire "fusion" doit contenir UNE entree pour CHAQUE nom present dans la fiche brute, y compris ceux qui ne changent pas (mappes vers eux-memes)."""


def _apply_fusion(resultats: list, fusion: dict) -> None:
    """Reecrit les 'locuteur' de chaque phrase de chaque chapitre selon la table de fusion. Modifie resultats en place."""
    for res in resultats:
        for p in res.get("phrases", []):
            loc = p.get("locuteur")
            if loc in fusion:
                p["locuteur"] = fusion[loc]


def _count_phrases_by_character(resultats: list) -> dict:
    counts = {}
    for res in resultats:
        for p in res.get("phrases", []):
            loc = p.get("locuteur", "narration")
            counts[loc] = counts.get(loc, 0) + 1
    return counts


# ==============================================================
# REGROUPEMENT DES DOUBLONS D'ECRITURE (session du 12/09/2026)
# ==============================================================
# Meme personne ecrite de plusieurs facons selon les chapitres :
# accents, tirets/apostrophes, ou article initial en trop
# ("Gerard de Villefort" / "Gerard de Villefort" accentue,
#  "Le comte de Monte-Cristo" / "Comte de Monte-Cristo"...).
# On reste VOLONTAIREMENT conservateur : on ne fusionne que si les noms
# sont identiques APRES normalisation. Aucun nom de famille n'est
# supprime, donc "Baron Danglars" et "Baronne Danglars" (personnes
# differentes) ne sont jamais confondus.

# Article initial retire avant comparaison (et uniquement celui-la).
_LEADING_ARTICLE_RE = re.compile(r'^(?:le|la|les|l|un|une|des|du|de)\s+')


def normalize_character_name(name: str) -> str:
    """Cle de comparaison d'un nom de personnage : minuscules, sans
    accents, apostrophes/tirets/underscores reduits a des espaces,
    ponctuation retiree, article initial enleve."""
    s = (name or "").lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace("'", " ").replace("\u2019", " ").replace("-", " ").replace("_", " ")
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = _LEADING_ARTICLE_RE.sub('', s)
    return s


def find_writing_duplicate_groups(items: list) -> list:
    """Regroupe des personnages ecrits de facon quasi identique.

    items : liste de dicts {\"nom\": str, \"line_count\": int}.
    Retourne une liste de groupes (chaque groupe = liste de noms, taille
    >= 2, triee du plus present au moins present). Le PREMIER nom de
    chaque groupe est le \"principal\" propose (celui qui a le plus de
    repliques)."""
    buckets = {}
    for it in items:
        nom = (it.get("nom") or "").strip()
        if not nom:
            continue
        cle = normalize_character_name(nom)
        if not cle:
            continue
        buckets.setdefault(cle, []).append(it)

    groupes = []
    for cle in sorted(buckets):
        membres = buckets[cle]
        if len(membres) < 2:
            continue
        membres.sort(key=lambda x: (-(x.get("line_count") or 0), x["nom"]))
        groupes.append([m["nom"] for m in membres])
    return groupes


# ==============================================================
# ATTRIBUTION PAR CRITERES (annotations d'ecoute) -- 16/09/2026
# ==============================================================
# Demande de Laurent : que le re-cast GRATUIT tienne compte des criteres
# annotes a l'ecoute (age, timbre, debit, accent, registre, role -- voir
# CRITERES_VOIX dans main.py), et pas seulement des etoiles. Les annotations
# vivent dans data/annotations_voix.json (fenetre « Ecouter les voix »).
#
# Principe : pour chaque personnage on CLASSE les voix disponibles (les plus
# adaptees d'abord), puis on prend la premiere encore libre. Aucun appel IA :
# c'est deterministe, gratuit, et testable.
#
# Constat du 16/09/2026 sur les 148 voix annotees : le REGISTRE (137 voix
# « neutre » pour 1 « noble ») et l'ACCENT « paysan » (aucune voix) ne portent
# pas assez d'information -> ils sont volontairement IGNORES ici. Le ROLE, lui,
# sert a RESERVER une voix : elle sort du pool automatique (comme les voix de
# role NIMM), sauf quand le role correspond a l'age du personnage.
#
# Piper reste hors de ce pool : ses voix ont ete jugees inaudibles a l'ecoute
# (decision de Laurent, 15/09/2026).

ANNOTATIONS_VOIX_PATH = Path(__file__).parent.parent / "data" / "annotations_voix.json"

_annotations_cache = {"mtime": None, "donnees": {}}


def lire_annotations_voix() -> dict:
    """Annotations d'ecoute, relues seulement si le fichier a change."""
    try:
        mtime = ANNOTATIONS_VOIX_PATH.stat().st_mtime
    except OSError:
        _annotations_cache["mtime"] = None
        _annotations_cache["donnees"] = {}
        return {}
    if _annotations_cache["mtime"] != mtime:
        try:
            _annotations_cache["donnees"] = json.loads(
                ANNOTATIONS_VOIX_PATH.read_text(encoding="utf-8"))
        except Exception:
            _annotations_cache["donnees"] = {}
        _annotations_cache["mtime"] = mtime
    return _annotations_cache["donnees"]


# Age de voix souhaite pour un age de personnage, du plus proche au plus
# eloigne. Les fiches du casting n'ont que trois ages (jeune, adulte, age),
# les voix en ont cinq.
AGES_PAR_PERSONNAGE = {
    "enfant": ["enfant", "jeune", "adulte"],
    "jeune":  ["jeune", "enfant", "adulte"],
    "adulte": ["adulte", "mur", "jeune"],
    "age":    ["vieux", "mur", "adulte"],
}

# Timbre attendu par genre et age : sert a ORDONNER, jamais a exclure.
TIMBRES_ATTENDUS = {
    ("H", "age"):    ["grave", "rocailleux", "medium"],
    ("H", "mur"):    ["grave", "medium", "rocailleux"],
    ("H", "adulte"): ["medium", "grave", "aigu"],
    ("H", "jeune"):  ["medium", "aigu", "grave"],
    ("H", "enfant"): ["aigu", "medium"],
    ("F", "age"):    ["medium", "grave", "voile"],
    ("F", "mur"):    ["medium", "voile", "grave"],
    ("F", "adulte"): ["medium", "aigu", "cristallin"],
    ("F", "jeune"):  ["cristallin", "aigu", "medium"],
    ("F", "enfant"): ["aigu", "cristallin", "medium"],
}

# Debit attendu par age : un vieux seigneur parle lentement, un gamin vite.
DEBITS_ATTENDUS = {
    "age":    ["lent", "pose", "normal", "vif"],
    "mur":    ["pose", "lent", "normal", "vif"],
    "adulte": ["normal", "pose", "vif", "lent"],
    "jeune":  ["vif", "normal", "pose", "lent"],
    "enfant": ["vif", "normal", "pose", "lent"],
}


def _index_voix() -> dict:
    """{identifiant: {'genre', 'stars'}} pour les moteurs du pool automatique.

    TROIS FAMILLES SEULEMENT (revu le 17/09/2026) : **Kyutai** (le moteur que
    START.bat allume), **Edge** (en ligne, toujours disponible) et **Kokoro**
    (local). XTTS et NeuTTS en sont RETIRES : leur moteur n'etant plus allume
    automatiquement, une voix attribuee chez eux ne lit RIEN -- le lecteur
    repond 503 sans rien afficher. C'est ce qui avait remis **79 voix muettes**
    sur le livre 28 au re-cast du 17/09 a 19h, alors que le pool par paliers
    etait deja corrige : ce chemin-ci (re-cast par criteres et re-cast IA) en
    etait reste a l'ancienne liste.
    """
    index = {}
    for ident in _EDGE_POOL_M:
        index[ident] = {"genre": "H", "stars": int(_EDGE_STARS.get(ident, 0))}
    for ident in _EDGE_POOL_F:
        index[ident] = {"genre": "F", "stars": int(_EDGE_STARS.get(ident, 0))}
    for liste in (KOKORO_VOICES, KYUTAI_VOICES):
        for voix in liste:
            index[voix["id"]] = {
                "genre": "F" if voix.get("gender") == "F" else "H",
                "stars": int(voix.get("stars", 0)),
            }
    return index


def _jumelle_neutts(ident: str) -> str:
    """`kyutai:X` -> `neutts:X` : meme extrait, donc meme profil d'ecoute.

    Les voix Kyutai ne sont pas annotees a l'ecoute, mais leurs jumelles NeuTTS
    oui (ce sont les memes extraits de reference). C'est cette annotation qui
    permet de choisir une voix Kyutai sur des criteres ENTENDUS.
    """
    if ident.startswith("kyutai:"):
        return "neutts:" + ident.split(":", 1)[1]
    return ident


def _voix_reservee(annotation: dict, ages: list) -> bool:
    """Vrai si la voix est RESERVEE a la main (role annote hors de l'age vise).

    Une voix « vieux » reste utilisable pour un personnage age, une voix
    « enfant » pour un enfant ; « narrateur », « etranger » et « secondaire »
    sortent du pool automatique, comme les voix de role NIMM.
    """
    role = (annotation or {}).get("role") or ""
    return bool(role) and role not in ages


def _classement_voix(genre: str, age: str) -> list:
    """Voix dediees d'un personnage, de la plus adaptee a la moins adaptee."""
    index = _index_voix()
    annotations = lire_annotations_voix()
    ages = AGES_PAR_PERSONNAGE.get(age, ["adulte", "mur", "jeune"])
    timbres = TIMBRES_ATTENDUS.get((genre, age), [])
    debits = DEBITS_ATTENDUS.get(age, [])

    classement = []
    for ident, fiche in index.items():
        if fiche["genre"] != genre or fiche["stars"] <= 0:
            continue                      # mauvais genre, ou voix ecartee
        annotation = (annotations.get(ident)
                      or annotations.get(_jumelle_neutts(ident))
                      or {})
        if _voix_reservee(annotation, ages):
            continue
        age_voix = annotation.get("age") or ""
        timbre = annotation.get("timbre") or ""
        debit = annotation.get("debit") or ""
        # Le plus important d'abord : l'age, puis le timbre, puis les etoiles,
        # puis le debit. L'identifiant departage les ex aequo pour que le
        # resultat soit TOUJOURS le meme (et donc testable).
        note = (
            ages.index(age_voix) if age_voix in ages else len(ages),
            timbres.index(timbre) if timbre in timbres else len(timbres),
            -fiche["stars"],
            debits.index(debit) if debit in debits else len(debits),
            ident,
        )
        classement.append((note, ident))
    classement.sort()
    return [ident for _, ident in classement]



# ==============================================================
# ETAPE 2 -- RE-CAST AVEC L'IA (16/09/2026, validee par Laurent)
# ==============================================================
# Le re-cast GRATUIT (par criteres, ci-dessus) classe les voix sur les
# annotations d'ecoute. Celui-ci va plus loin : l'IA LIT LES REPLIQUES du
# personnage et en deduit ce qu'aucune table ne contient -- position sociale,
# registre de langue, fait de parler etranger, temperament.
#
# Elle ne peut PAS entendre un timbre : elle choisit donc sur DESCRIPTION, ce
# qui n'est possible que parce que les voix sont annotees (age, timbre, debit,
# registre, accent, etoiles).
#
# GARDE-FOU DE CONCEPTION : l'IA ne choisit JAMAIS dans tout le catalogue. Pour
# chaque personnage, les voix proposees sont exactement celles que les regles
# du re-cast gratuit autorisent deja (meme genre, plus de 0 etoile, role
# reserve ecarte). L'IA ne fait donc que RE-ORDONNER -- elle ne peut pas
# introduire une voix que le re-cast gratuit aurait refusee.
#
# Deux fonctions sont PURES (aucun appel reseau, donc testables) :
# `construire_prompt_recaste_ia` et `lire_attributions_ia`. L'appel au modele
# est isole dans `attribuer_voix_avec_ia`.

def description_voix(ident: str, fiche: dict, annotation: dict) -> str:
    """Une ligne de description d'une voix, lisible par un modele."""
    morceaux = ["femme" if fiche.get("genre") == "F" else "homme"]
    for cle, etiquette in (("age", "age"), ("timbre", "timbre"),
                           ("debit", "debit"), ("registre", "registre"),
                           ("accent", "accent"), ("role", "role reserve")):
        valeur = (annotation or {}).get(cle)
        if valeur:
            morceaux.append("%s %s" % (etiquette, valeur))
    etoiles = int(fiche.get("stars") or 0)
    return "%s (%s, %d etoile%s)" % (ident, ", ".join(morceaux), etoiles,
                                     "s" if etoiles > 1 else "")


def voix_proposees_pour(personnages: list, exclues=None) -> dict:
    """{genre: [{'id', 'description'}, ...]} : ce que l'IA a le droit de voir.

    Les voix proposees sont celles du re-cast par criteres (`_classement_voix`),
    personnage par personnage, sans doublon : l'ordre est celui des criteres
    (le meilleur d'abord), ce qui aide le modele quand il hesite.
    """
    exclues = set(exclues or ())
    annotations = lire_annotations_voix()
    index = _index_voix()
    par_genre = {}
    for personnage in personnages:
        genre = personnage.get("genre") or "H"
        age = personnage.get("age") or "adulte"
        liste = par_genre.setdefault(genre, [])
        connus = {v["id"] for v in liste}
        for ident in _classement_voix(genre, age):
            if ident in exclues or ident in connus:
                continue
            liste.append({"id": ident,
                          "description": description_voix(
                              ident, index.get(ident, {"genre": genre}),
                              annotations.get(ident) or {})})
    return par_genre


def construire_prompt_recaste_ia(personnages: list, voix: dict) -> str:
    """Le prompt envoye au modele (fonction PURE : aucun appel reseau).

    Il contient les personnages AVEC quelques repliques -- c'est ce qui permet
    au modele de juger registre, position sociale et temperament -- et les voix
    avec leur description entendue a l'ecoute.
    """
    blocs = []
    for personnage in personnages:
        lignes = ["- %s (genre %s, age %s, %d repliques)"
                  % (personnage.get("nom"),
                     "F" if personnage.get("genre") == "F" else "H",
                     personnage.get("age") or "adulte",
                     personnage.get("repliques") or 0)]
        for replique in (personnage.get("repliques_texte") or [])[:3]:
            lignes.append('    dit : "%s"' % replique)
        blocs.append("\n".join(lignes))

    blocs_voix = []
    for genre, etiquette in (("F", "FEMMES"), ("H", "HOMMES")):
        liste = voix.get(genre) or []
        if not liste:
            continue
        blocs_voix.append("%s :" % etiquette)
        blocs_voix.extend("- %s" % v["description"] for v in liste)

    return """Tu attribues une voix a chaque personnage d'un roman, en lisant ce
qu'il dit dans le texte.

PERSONNAGES :
%s

VOIX DISPONIBLES (identifiant, puis description telle qu'entendue a l'ecoute) :
%s

CONSIGNES :
1. Choisis pour chaque personnage UNE voix du BON GENRE, en te fondant sur ce
   que ses repliques revelent : age, position sociale (seigneur, servante,
   enfant...), registre de langue (soutenu, populaire), fait de parler
   etranger (titres, mots etrangers), temperament (vif, pose, doux).
2. N'utilise QUE les identifiants de voix fournis ci-dessus, et JAMAIS deux fois
   le meme identifiant.
3. Si tu hesites, choisis quand meme : ce re-cast est reversible.
4. Ne recopie AUCUN texte du roman dans ta reponse.

Reponds UNIQUEMENT avec un JSON de cette forme exacte :
{"attributions": [{"personnage": "nom", "voix": "identifiant", "pourquoi": "en 5 mots"}]}""" % (
        "\n".join(blocs), "\n".join(blocs_voix))


def lire_attributions_ia(reponse, personnages: list) -> tuple:
    """(attributions, problemes) : lit et VERIFIE la reponse du modele.

    Controles, dans cet ordre :
      - le personnage existe (a une variante d'ecriture pres) ;
      - la voix a bien ete proposee pour CE personnage, c'est-a-dire qu'elle
        passe les regles du re-cast par criteres (meme genre, plus de 0 etoile,
        role reserve ecarte) ;
      - une voix n'est donnee qu'a un seul personnage.

    Tout ce qui ne passe pas est ECARTE et explique : le personnage concerne
    gardera alors sa voix par criteres (repli, voir main.py).
    """
    par_nom = {p["nom"]: p for p in personnages}
    autorisees = {}
    for nom, personnage in par_nom.items():
        autorisees[nom] = set(_classement_voix(personnage.get("genre") or "H",
                                               personnage.get("age") or "adulte"))

    entrees = (reponse or {}).get("attributions") or []
    if isinstance(entrees, dict):        # au cas ou le modele rende un objet
        entrees = [{"personnage": nom, "voix": ident}
                   for nom, ident in entrees.items()]

    attributions, problemes, prises = {}, [], set()
    for entree in entrees:
        if not isinstance(entree, dict):
            problemes.append("entree illisible : %r" % (entree,))
            continue
        nom = str(entree.get("personnage") or "").strip()
        ident = str(entree.get("voix") or "").strip()

        if nom not in par_nom:
            # Tolerance : le modele peut rendre une variante du nom.
            canonique = next(
                (c for c in par_nom
                 if normalize_character_name(c) == normalize_character_name(nom)),
                None)
            if canonique is None:
                problemes.append("personnage inconnu : %s" % nom)
                continue
            nom = canonique

        if nom in attributions:
            continue                     # deja attribue : on garde le premier
        if ident not in autorisees[nom]:
            problemes.append("voix non proposee pour %s : %s" % (nom, ident))
            continue
        if ident in prises:
            problemes.append("voix donnee deux fois : %s" % ident)
            continue
        attributions[nom] = ident
        prises.add(ident)
    return attributions, problemes


async def attribuer_voix_avec_ia(personnages: list, exclues=None,
                                 provider: str = "gemini") -> dict:
    """Attribue les voix avec l'IA et renvoie {attributions, problemes}.

    `personnages` : [{"nom", "genre", "age", "repliques", "repliques_texte"}]
    `exclues`     : voix a ne pas proposer (verrous et voix figees de saga).

    Les exceptions du fournisseur (contenu bloque, reponse illisible) remontent
    telles quelles : c'est l'appelant qui decide quoi en dire a l'utilisateur.
    """
    voix = voix_proposees_pour(personnages, exclues)
    if not any(voix.values()):
        return {"attributions": {}, "problemes": ["aucune voix proposee"]}
    prompt = construire_prompt_recaste_ia(personnages, voix)
    reponse = await _call_llm(prompt, provider)
    attributions, problemes = lire_attributions_ia(reponse, personnages)
    return {"attributions": attributions, "problemes": problemes}



def assign_voices(personnages_finaux: list, compte_phrases: dict, voix_figees: dict = None,
                  par_criteres: bool = False) -> dict:
    """
    Attribue voix + pitch a chaque personnage.
    Personnages deja presents dans voix_figees (autre tome de la meme
    saga) : voix/pitch/vitesse repris tels quels, aucune nouvelle
    attribution (session du 22/08/2026).
    Personnages avec peu de repliques -> voix generique partagee par genre.
    Les autres -> voix dediee piochee dans le pool, avec variation de
    pitch supplementaire si le pool est epuise (plus de personnages que
    de voix dediees disponibles pour ce genre).

    par_criteres (16/09/2026) : au lieu de piocher dans le pool par paliers
    d'etoiles, on CLASSE les voix selon les annotations d'ecoute (age, timbre,
    debit -- voir _classement_voix) et on prend la premiere encore libre. Le
    pool par paliers reste le repli quand aucune annotation n'existe.
    """
    voix_figees = voix_figees or {}
    # Les voix deja figees (meme saga, autre tome) comptent comme prises : un
    # personnage nouveau ne doit pas heriter de la voix d'un aine.
    prises = set(fixe.get("voice_id") for fixe in voix_figees.values()
                 if fixe.get("voice_id"))

    # Traite les personnages les plus presents en premier, pour que les
    # roles principaux aient la priorite sur le pool de voix dediees
    tries = sorted(
        personnages_finaux,
        key=lambda p: compte_phrases.get(p.get("nom"), 0),
        reverse=True
    )

    idx_f = 0
    idx_m = 0
    voix = {}

    for perso in tries:
        nom = perso.get("nom")
        genre = perso.get("genre", "H")
        age = perso.get("age", "adulte")
        count = compte_phrases.get(nom, 0)
        pitch_base = PITCH_BY_AGE.get(age, "+0Hz")

        if nom in voix_figees:
            fixe = voix_figees[nom]
            voix[nom] = {
                "voice_id": fixe["voice_id"],
                "pitch": fixe["pitch"],
                "rate": fixe.get("rate", "+0%"),
                "genre": fixe.get("genre", genre),
                "line_count": count,
            }
            continue

        if count < MINOR_THRESHOLD:
            # PETIT ROLE (< 8 repliques) : aucune voix dediee depuis le
            # 15/09/2026 (decision de Laurent a l'ecoute de Shantaram : les
            # voix generiques Piper etaient « inaudibles, vraiment moches »).
            # Ses repliques sont lues par le NARRATEUR -- la voix choisie dans
            # le lecteur -- ce qui est coherent : c'est bien le narrateur qui
            # rapporte ce que dit le personnage.
            # La ligne est CONSERVEE avec un voice_id VIDE : le personnage reste
            # visible dans la fenetre du casting, avec la mention « lu par le
            # narrateur », et on peut lui redonner une voix a la main. Le jour
            # ou Laurent aura choisi deux voix neutres, il suffira de definir
            # GENERIC_VOICE_F/M ci-dessus (un re-cast recreera tout).
            voice_id = ""
            pitch = "+0Hz"
        else:
            if par_criteres:
                # Classement par annotations d'ecoute : on prend la premiere
                # voix encore libre. Si tout est pris (plus de personnages que
                # de voix), on reprend la mieux classee et on decale le pitch,
                # exactement comme le faisait le pool par paliers.
                pool = _classement_voix(genre, age) or (
                    DEDICATED_VOICES_F if genre == "F" else DEDICATED_VOICES_M)
                libres = [v for v in pool if v not in prises]
                voice_id = libres[0] if libres else pool[0]
                cycle = 0 if libres else 1
                prises.add(voice_id)
            else:
                pool = DEDICATED_VOICES_F if genre == "F" else DEDICATED_VOICES_M
                idx = idx_f if genre == "F" else idx_m
                voice_id = pool[idx % len(pool)]
                cycle = idx // len(pool)  # si on retombe sur une voix deja utilisee
                if genre == "F":
                    idx_f += 1
                else:
                    idx_m += 1
            # Decale le pitch de base si la voix est deja prise par un autre
            # personnage, pour les differencier malgre la voix identique
            base_hz = int(pitch_base.replace("Hz", "").replace("+", ""))
            pitch = f"{'+' if base_hz + cycle * 8 >= 0 else ''}{base_hz + cycle * 8}Hz"

        voix[nom] = {"voice_id": voice_id, "pitch": pitch, "rate": "+0%", "genre": genre, "line_count": count}

    return voix


async def consolidate_book(resultats: list, provider: str = "gemini", voix_figees: dict = None, fiche_brute: list = None) -> dict:
    """
    Passe 2 complete : fusionne les alias, reecrit les attributions de
    chaque chapitre, compte les repliques, attribue voix + pitch.
    Modifie resultats en place (locuteurs fusionnes).
    voix_figees (optionnel) : personnages deja castes sur un autre tome
    de la meme saga -- leur voix/pitch/vitesse est reprise telle quelle
    au lieu de repiocher dans le pool (session du 22/08/2026).
    fiche_brute (optionnel) : fiche de personnages a consolider, fournie
    par l'appelant. Utile pour la REPRISE (session du 13/09/2026) : quand
    l'analyse reprend apres une erreur, la fiche d'origine est relue
    depuis la base (table cast_fiche) au lieu d'etre deduite des
    resultats -- et sur un livre deja entierement analyse, le dernier
    resultat relu en base ne porte aucune fiche.
    """
    if not resultats:
        return {"fusion": {}, "personnages": [], "voix": {}, "compte_phrases": {}}

    if fiche_brute is None:
        fiche_brute = resultats[-1].get("personnages", [])
    if not fiche_brute:
        # La fiche du dernier chapitre peut etre vide (cas vu en production) :
        # on reconstruit la fiche brute a partir de tous les chapitres pour ne
        # jamais court-circuiter la Passe 2.
        vus = {}
        for res in resultats:
            for p in res.get("personnages", []):
                nom = p.get("nom")
                if nom:
                    vus[nom] = p
        fiche_brute = list(vus.values())
    if not fiche_brute:
        return {"fusion": {}, "personnages": [], "voix": {}, "compte_phrases": {}}

    prompt = _build_passe2_prompt(fiche_brute)
    result = await _call_llm(prompt, provider)

    fusion = result.get("fusion", {})
    personnages_finaux = result.get("personnages", fiche_brute)

    _apply_fusion(resultats, fusion)
    compte_phrases = _count_phrases_by_character(resultats)
    voix = assign_voices(personnages_finaux, compte_phrases, voix_figees=voix_figees)

    return {
        "fusion": fusion,
        "personnages": personnages_finaux,
        "voix": voix,
        "compte_phrases": compte_phrases
    }


# ==============================================================
# ESTIMATION DU COUT AVANT LANCEMENT (PASSE 1 + PASSE 2)
# ==============================================================
# Tarifs en USD par million de tokens (entree/sortie).
# CALIBRES LE 14/09/2026 sur une facture Google REELLE : le casting de
# "un roman contemporain" (30 293 phrases, 211 appels, 1 617 072 tokens d'entree et
# 110 892 de sortie) a ete facture 0,98 EUR, alors que les tarifs precedents
# (0,30 / 2,50 $) ne donnaient que 0,76 $ -- soit 40 % de moins.
# Les deux tarifs Gemini ont donc ete releves proportionnellement, ce qui
# redonne exactement la facture reelle :
#   1,617 M x 0,42 + 0,111 M x 3,50 = 1,068 $ ~ 0,98 EUR
# A la difference des autres moteurs, Gemini n'est PAS une estimation : c'est
# une calibration sur facture. Les tarifs DeepSeek et Mistral restent des
# ordres de grandeur, jamais confirmes par une facture -- a ajuster de la meme
# facon le jour ou Laurent nous donnera le montant reel.
PROVIDER_PRICES_USD = {
    "gemini":   {"in": 0.42, "out": 3.50},   # calibre sur facture (14/09/2026)
    "deepseek": {"in": 0.27, "out": 1.10},   # deepseek-chat (ordre de grandeur)
    "mistral":  {"in": 2.00, "out": 6.00},   # mistral-large-latest (ordre de grandeur)
    # Moteur LOCAL (Ollama) : gratuit par nature, le modele tourne sur le
    # poste. Les tarifs a zero evitent tout cas particulier dans les
    # estimations et dans le decompte du cout.
    "local":    {"in": 0.00, "out": 0.00},
}

# Approximations de tokenisation (sans appel reseau) :
# - ~4 caracteres par token en francais
# - chaque phrase envolee ajoute ~45 caracteres d'enrobage JSON (id + texte)
# - chaque phrase renvoyee coute ~22 tokens de sortie (JSON locuteur)
# - la Passe 2 (consolidation) ajoute ~600 tokens de sortie et 1 appel
CHARS_PER_TOKEN = 4
JSON_OVERHEAD_CHARS = 45
# Mesure du 14/09/2026, APRES le passage au format compact : la reponse du
# modele ne fait plus que ~5 mots par phrase (2 859 tokens de sortie mesures
# pour 557 phrases, soit 5,1), contre 22 estimes du temps de l'ancien format
# verbeux. Sans cette correction, l'estimation affichee annoncait 2 a 3 fois le
# cout reel (0,06 $ annonces pour 0,0155 $ payes sur le livre de test).
TOKENS_OUT_PER_SENTENCE = 5
PASSE2_OUT_TOKENS = 600
# Marge de prudence affichee a l'utilisateur (fiche de personnages qui
# grossit, retries, tokens de sortie variables) : x1.5 sur le brut.
COST_SAFETY_MARGIN = 1.5


def _format_cost(usd: float) -> str:
    if usd < 0.01:
        return "< 0.01 $"
    if usd < 10:
        return f"~{usd:.2f} $"
    return f"~{usd:.0f} $"


def estimate_cast_cost(chapters_texts: list, provider: str = "gemini") -> dict:
    """
    Estime le cout (tokens + USD) d'un lancement voix multiples SANS faire
    aucun appel IA : on decoupe les chapitres en phrases, on compte les
    appels (Passe 1 : ceil(phrases / BATCH_SIZE) par chapitre, + 1 Passe 2),
    on approxime les tokens puis on applique les tarifs du provider.
    Retourne le brut, le majore (affichage prudent) et une chaine prete
    a l'emploi.
    """
    provider = provider if provider in PROVIDER_PRICES_USD else "gemini"
    base_prompt_chars = len(_build_prompt([], []))

    total_sentences = 0
    total_chars = 0
    calls = 0
    chapters_count = 0

    for text in chapters_texts:
        if not text or not text.strip():
            continue
        chapters_count += 1
        sents = _split_chapter_sentences(text)
        if not sents:
            continue
        total_sentences += len(sents)
        total_chars += sum(len(s["texte"]) for s in sents)
        calls += math.ceil(len(sents) / BATCH_SIZE)

    calls += 1  # Passe 2 (consolidation des personnages)

    tokens_in = int((base_prompt_chars * calls + total_chars
                     + total_sentences * JSON_OVERHEAD_CHARS) / CHARS_PER_TOKEN)
    tokens_out = int(total_sentences * TOKENS_OUT_PER_SENTENCE) + PASSE2_OUT_TOKENS

    price = PROVIDER_PRICES_USD[provider]
    cost_usd = (tokens_in / 1_000_000) * price["in"] + (tokens_out / 1_000_000) * price["out"]
    cost_usd_max = round(cost_usd * COST_SAFETY_MARGIN, 2)

    return {
        "provider": provider,
        "chapters": chapters_count,
        "sentences": total_sentences,
        "calls": calls,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost_usd, 2),
        "cost_usd_max": cost_usd_max,
        # Le moteur local ne coute rien : on l'annonce clairement plutot que
        # d'afficher "< 0.01 $", qui laisserait croire a une petite depense.
        "cost_display": ("gratuit (sur votre PC)" if provider == "local"
                         else _format_cost(cost_usd_max)),
    }
