# -*- coding: utf-8 -*-
"""COMPARER LES PROVIDERS SUR UN PASSAGE PIEGE (PAYANT).

POURQUOI IL EXISTE (demande de Laurent, 24/09/2026) : « faire un petit essai sur
les differents providers qu'on a, sur un passage court et litigieux, histoire de
voir depuis qu'on a fait quelques modifications, quel provider s'en sort le
mieux ».

CE QU'IL FAIT, ET POURQUOI C'EST FIABLE :

  1. il lit le passage dans `test_voix/passage_piege.txt` ;
  2. il passe par LE CHEMIN REEL DE L'APPLI -- `voice_casting.analyze_chapter`,
     donc le MEME prompt compact, la meme decoupe, le meme filet de securite.
     C'est ce qui rend la comparaison honnete : on mesure l'aujourd'hui, pas une
     vieille version du prompt (l'ancien outil `_PAYANT_test_attribution_api.py`
     portait l'ancien format : il ne repondrait pas a la question) ;
  3. chaque provider est interroge SEUL (`provider_repli=[]`) : un moteur qui
     refuse le texte est compte comme tel, ce n'est pas DeepSeek qui repond a sa
     place en cachette ;
  4. il confronte les attributions a la VERITE TERRAIN
     (`test_voix/passage_piege_verite.txt`) et sort un SCORE par provider. Le
     score est calcule APRES avoir cherche la CORRESPONDANCE entre les noms
     choisis par le modele et les notres : un modele a le droit de baptiser le
     pere « Etienne_vieil » -- ce qu'on mesure, c'est s'il met LA BONNE VOIX sur
     LA BONNE PHRASE. En revanche, un modele qui n'a qu'UN SEUL nom pour deux
     personnages est signale « FUSION » : a l'oreille, c'est une faute (deux
     personnes avec la meme voix) ;
  5. il ecrit un rapport lisible et garde la reponse brute de chacun.

GARDE-FOU (regle du projet) : ce script appelle de VRAIES API facturees. Sans
l'option explicite `--je-paie`, il explique et s'arrete.

MODES GRATUITS (aucun appel, aucun euro) :
    python test_voix/_PAYANT_comparer_providers_passage.py --decouper
        -> montre les phrases numerotees telles que le modele les recevra
    python test_voix/_PAYANT_comparer_providers_passage.py --verifier
        -> verifie les cles, la verite terrain, et annonce le cout estime

MODE PAYANT :
    python test_voix/_PAYANT_comparer_providers_passage.py --je-paie
    python test_voix/_PAYANT_comparer_providers_passage.py --je-paie --tours 2
    python test_voix/_PAYANT_comparer_providers_passage.py --je-paie --providers gemini,local

Comparer un AUTRE modele que celui de l'appli (24/09/2026 : l'abonnement Mistral
de Laurent n'a pas acces a `mistral-large-latest`, le modele du bouton Mistral
de l'appli -- l'outil sait prendre un autre modele) :
    python test_voix/_PAYANT_comparer_providers_passage.py --je-paie \
        --providers mistral --modele-mistral mistral-small-latest

Comparer PLUSIEURS modeles d'un meme moteur, cote a cote dans le MEME rapport
(24/09/2026 : le mini et le nano d'OpenAI) :
    python test_voix/_PAYANT_comparer_providers_passage.py --je-paie \
        --tours 2 --providers gemini,deepseek,openai,local \
        --modele-openai gpt-5.4-mini,gpt-5.4-nano

OU VIVENT LES CLES :
    - `data/config.json` : gemini_api_key, mistral_api_key, deepseek_api_key
      (c'est ce que l'appli utilise -- rien a faire pour ces trois-la) ;
    - `test_voix/cles_api.txt` (format NOM=valeur) ou `data/config.json` pour
      les fournisseurs que l'appli ne connait pas : OPENAI_API_KEY (OpenAI) et
      ANTHROPIC_API_KEY (Claude). Les deux fichiers sont dans `.gitignore`.

Lancer depuis la racine du projet.
"""

import argparse
import asyncio
import json
import sys
import time
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import decoupage
from modules import voice_casting as vc
from modules.config import (get_gemini_api_key, get_mistral_api_key,
                            get_deepseek_api_key)

DOSSIER = Path(__file__).resolve().parent
FICHIER_PASSAGE = DOSSIER / 'passage_piege.txt'
FICHIER_VERITE = DOSSIER / 'passage_piege_verite.txt'
FICHIER_CLES = DOSSIER / 'cles_api.txt'
CONFIG = RACINE / 'data' / 'config.json'

URL_OPENAI = "https://api.openai.com/v1/chat/completions"
URL_CLAUDE = "https://api.anthropic.com/v1/messages"
# Laurent a propose gpt-5.4-mini ou gpt-5.4-nano (24/09/2026) : le nom se
# change ici, ou avec --modele-openai.
MODELE_OPENAI = "gpt-5.4-mini"
MODELE_CLAUDE = "claude-haiku-4-5"

# Le catalogue des providers. `cle_config` / `cle_fichier` disent OU chercher la
# cle. Les tarifs viennent du projet (`PROVIDER_PRICES_USD`) : quand il n'y en a
# pas (OpenAI, Claude), le rapport annonce les tokens releves et REFUSE
# d'inventer un cout.
PROVIDERS = {
    'gemini': {
        'libelle': 'Gemini',
        'modele': vc.GEMINI_MODEL,
        'cle_config': 'gemini_api_key',
        'cle_fichier': ('GOOGLE_API_KEY', 'GEMINI_API_KEY'),
    },
    'deepseek': {
        'libelle': 'DeepSeek',
        'modele': 'deepseek-chat',
        'cle_config': 'deepseek_api_key',
        'cle_fichier': ('DEEPSEEK_API_KEY',),
    },
    'mistral': {
        'libelle': 'Mistral',
        'modele': 'mistral-large-latest',
        'cle_config': 'mistral_api_key',
        'cle_fichier': ('MISTRAL_API_KEY',),
    },
    'openai': {
        'libelle': 'OpenAI',
        'modele': MODELE_OPENAI,
        'cle_config': 'openai_api_key',
        'cle_fichier': ('OPENAI_API_KEY',),
    },
    'claude': {
        'libelle': 'Claude (Anthropic)',
        'modele': MODELE_CLAUDE,
        'cle_config': 'anthropic_api_key',
        'cle_fichier': ('ANTHROPIC_API_KEY',),
    },
    'local': {
        'libelle': 'Modele local (Ollama)',
        'modele': None,                 # lu dans data/config.json
        'cle_config': None,
        'cle_fichier': (),
    },
}

# Providers interroges quand on ne demande rien de precis.
# Claude n'y est PAS par defaut : Laurent l'a juge trop cher pour cet essai
# (24/09/2026) -- il reste disponible avec `--providers claude`.
PROVIDERS_DEFAUT = 'gemini,deepseek,mistral,openai,local'

# Le modele REELLEMENT utilise, par provider. L'appli ne jure que par un modele
# par moteur (gemini-3.7-flash, deepseek-chat, mistral-large-latest) ; pour en
# comparer un AUTRE sans toucher au code de l'appli (utile quand un abonnement
# ne donne pas acces au gros modele), on le note ici et le rapport affiche le
# modele effectif.
MODELES_EFFECTIFS = {}


def _code_court(modele: str) -> str:
    """Un code court pour la colonne du tableau (« mini », « nano »)."""
    morceaux = [m for m in modele.replace('_', '-').split('-') if m]
    return (morceaux[-1] if morceaux else modele)[:6].lower()


def enregistrer_variante(cle: str, base: str, modele: str) -> None:
    """Ajoute une COLONNE supplementaire pour un meme moteur, avec un AUTRE
    modele (demande de Laurent, 24/09/2026 : « essaie le mini ET le nano »).

    La colonne herite des cles de configuration du moteur de base -- tout le
    reste du rapport (score, tableau, erreurs) fonctionne sans changement, et le
    moteur interroge reste celui de l'appli (meme URL, meme code d'appel).
    """
    entree = dict(PROVIDERS[base])
    entree['libelle'] = '%s %s' % (entree['libelle'], _code_court(modele))
    entree['modele'] = modele
    entree['code'] = _code_court(modele)
    PROVIDERS[cle] = entree


def preparer_colonnes(demandes: list, modeles_openai: list) -> list:
    """Traduit la demande en COLONNES de comparaison.

    Un seul cas particulier : OpenAI peut etre demande avec PLUSIEURS modeles --
    chacun devient sa propre colonne, pour les comparer cote a cote dans le meme
    rapport (mini / nano).
    """
    colonnes = []
    for nom in demandes:
        if nom != 'openai':
            colonnes.append(nom)
            continue
        if len(modeles_openai) <= 1:
            colonnes.append('openai')
            continue
        for modele in modeles_openai:
            cle = 'openai:%s' % modele
            enregistrer_variante(cle, 'openai', modele)
            colonnes.append(cle)
    return colonnes


# ==============================================================
# LECTURE DES CLES
# ==============================================================

def lire_cles_api() -> dict:
    """`test_voix/cles_api.txt` : une ligne par cle, au format NOM=valeur."""
    cles = {}
    if not FICHIER_CLES.exists():
        return cles
    with open(FICHIER_CLES, 'r', encoding='utf-8') as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith('#') or '=' not in ligne:
                continue
            nom, valeur = ligne.split('=', 1)
            cles[nom.strip()] = valeur.strip()
    return cles


def lire_config() -> dict:
    try:
        with open(CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _cle_valide(valeur) -> bool:
    """Une valeur absente, ou restee au gabarit, ne compte pas comme une cle."""
    if not valeur or not isinstance(valeur, str):
        return False
    propre = valeur.strip()
    return bool(propre) and 'COLLE_TA_CLE' not in propre.upper()


def trouver_cle(provider: str, cles_fichier: dict, config: dict):
    """Retourne (valeur, provenance) ou (None, raison lisible)."""
    info = PROVIDERS[provider]
    noms = list(info['cle_fichier'])
    if info['cle_config']:
        noms.append(info['cle_config'].upper())
    noms = list(dict.fromkeys(noms))          # pas de doublon dans le message

    for nom in info['cle_fichier']:
        if _cle_valide(cles_fichier.get(nom)):
            return cles_fichier[nom].strip(), 'test_voix/cles_api.txt (%s)' % nom
    if info['cle_config'] and _cle_valide(config.get(info['cle_config'])):
        return config[info['cle_config']].strip(), \
            'data/config.json (%s)' % info['cle_config']
    for nom in noms:
        if _cle_valide(cles_fichier.get(nom)):
            return cles_fichier[nom].strip(), \
                'test_voix/cles_api.txt (%s)' % nom
    return None, 'cle absente (cherchee : %s)' % ', '.join(noms)



# ==============================================================
# LE PASSAGE, LA VERITE TERRAIN, ET LE SCORE
# ==============================================================

def lire_passage() -> str:
    with open(FICHIER_PASSAGE, 'r', encoding='utf-8') as f:
        return f.read().strip()


def lire_verite() -> dict:
    """La verite terrain : `id | locuteur attendu | note`.

    Une note qui contient « litigieux » marque un cas ou la bonne reponse se
    deduit seulement du fil du texte (suite d'une replique sans tiret, par
    exemple). Ces cas sont comptes A PART, pour ne pas melanger « le moteur s'est
    trompe » et « la question etait delicate ».
    """
    verite = {}
    if not FICHIER_VERITE.exists():
        return verite
    with open(FICHIER_VERITE, 'r', encoding='utf-8') as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith('#') or '|' not in ligne:
                continue
            morceaux = [m.strip() for m in ligne.split('|')]
            if len(morceaux) < 2 or not morceaux[0].isdigit():
                continue
            note = morceaux[2] if len(morceaux) > 2 else ''
            verite[int(morceaux[0])] = {
                'attendu': morceaux[1],
                'note': note,
                'litigieux': 'litigieux' in note.lower(),
            }
    return verite


def normaliser(nom) -> str:
    """Compare des noms sans se disputer sur les accents, la casse ou les tirets.

    « Etienne_pere » et « étienne-Père » deviennent le meme nom. En revanche
    « Etienne » tout court reste DISTINCT : ne pas desambiguiser les homonymes
    est justement l'erreur qu'on veut voir.
    """
    if nom is None:
        return ''
    texte = unicodedata.normalize('NFKD', str(nom))
    texte = ''.join(c for c in texte if not unicodedata.combining(c))
    texte = texte.lower().replace('’', "'").replace('-', '_').replace(' ', '_')
    return '_'.join(m for m in texte.split('_') if m)


def _correspondance(details: list):
    """Le modele a le DROIT d'inventer ses noms de personnages : on cherche donc
    d'abord la correspondance entre ses noms et les notres, en regardant a qui il
    attribue les phrases de chaque personnage attendu.

    Deux personnages attendus qui tombent sur le MEME nom du modele sont
    FUSIONNES : c'est une vraie faute a l'oreille (une seule voix pour deux
    personnes), et elle ne doit pas se cacher derriere un vocabulaire different.

    Retourne (correspondance {notre nom -> son nom}, {nom fusionne -> nos noms}).
    """
    par_attendu = {}
    for d in details:
        attendu, obtenu = normaliser(d['attendu']), normaliser(d['obtenu'])
        if attendu == 'narration' or not obtenu or obtenu == 'narration':
            continue
        par_attendu.setdefault(attendu, {})
        par_attendu[attendu][obtenu] = par_attendu[attendu].get(obtenu, 0) + 1

    choisi = {attendu: max(comptes.items(), key=lambda paire: paire[1])[0]
              for attendu, comptes in par_attendu.items()}

    groupes = {}
    for attendu, obtenu in choisi.items():
        groupes.setdefault(obtenu, []).append(attendu)
    fusion = {obtenu: noms for obtenu, noms in groupes.items() if len(noms) > 1}
    return choisi, fusion


def _verdict(detail: dict, choisi: dict, fusion: dict) -> str:
    """Un mot par phrase, apres correspondance des noms."""
    attendu, obtenu = normaliser(detail['attendu']), normaliser(detail['obtenu'])
    if not obtenu:
        return 'ABSENT'
    if attendu == 'narration':
        return 'OK' if obtenu == 'narration' else 'INVENTE'
    if obtenu == 'narration':
        return 'NARRATION'    # le narrateur lit une replique (le pire a l'oreille)
    if obtenu in fusion:
        return 'FUSION'       # un seul nom pour deux personnages
    if choisi.get(attendu) == obtenu:
        return 'OK'
    return 'FAUX'             # un autre personnage, distinct et mal place


def noter(resultat: dict, verite: dict, sentences: list) -> dict:
    """Compare une reponse aux attentes, et rend un bulletin lisible.

    La comparaison se fait APRES avoir etabli la correspondance des noms : le
    score mesure donc ce que Laurent entendra (le bon personnage sur la bonne
    phrase), pas la facon dont le modele a baptise ses personnages. Les noms
    choisis sont rendus a part, pour l'information.
    """
    obtenu = {p['id']: p for p in resultat.get('phrases', [])}
    texte = {s['id']: s['texte'] for s in sentences}

    details = []
    for sid in sorted(verite):
        phrase = obtenu.get(sid)
        details.append({
            'id': sid,
            'attendu': verite[sid]['attendu'],
            'obtenu': phrase['locuteur'] if phrase else '',
            'litigieux': verite[sid]['litigieux'],
            'texte': texte.get(sid, ''),
            'confiance': (phrase or {}).get('confiance'),
            'anomalie': (phrase or {}).get('anomalie'),
            'verdict': 'ABSENT',
        })

    choisi, fusion = _correspondance(details)
    compte = {}
    total_strict = ok_strict = total_delicat = ok_delicat = 0
    for detail in details:
        detail['verdict'] = _verdict(detail, choisi, fusion)
        compte[detail['verdict']] = compte.get(detail['verdict'], 0) + 1
        juste = detail['verdict'] == 'OK'
        if detail['litigieux']:
            total_delicat += 1
            ok_delicat += 1 if juste else 0
        else:
            total_strict += 1
            ok_strict += 1 if juste else 0

    def pourcent(part, tout):
        return round(100.0 * part / tout) if tout else 0

    return {
        'compte': compte,
        'details': details,
        'noms': choisi,
        'fusion': fusion,
        'score_strict': (ok_strict, total_strict, pourcent(ok_strict, total_strict)),
        'score_delicat': (ok_delicat, total_delicat,
                          pourcent(ok_delicat, total_delicat)),
    }



# ==============================================================
# LES DEUX PROVIDERS QUE L'APPLI NE CONNAIT PAS
# ==============================================================
# L'appli gere quatre moteurs (Gemini, DeepSeek, Mistral, local). Pour comparer
# AUSSI OpenAI et Claude sans toucher au code de l'appli, on enveloppe son
# aiguillage `_call_llm` le temps du script : tout le reste (prompt, decoupe,
# filet de securite, comptage des tokens) reste le code de l'appli.

def _call_claude(prompt: str, cle: str, modele: str) -> dict:
    """Appel Anthropic : meme principe que l'ancien outil d'atelier
    (`_PAYANT_test_attribution_api.py`), avec le comptage des tokens en plus."""
    import httpx
    corps = {
        'model': modele,
        'max_tokens': 16384,
        'system': 'Tu reponds uniquement par un JSON valide, sans texte autour.',
        'messages': [{'role': 'user', 'content': prompt}],
    }
    entetes = {'x-api-key': cle, 'anthropic-version': '2023-06-01',
               'content-type': 'application/json'}
    with httpx.Client(timeout=180.0) as client:
        res = client.post(URL_CLAUDE, headers=entetes, json=corps)
    if res.status_code != 200:
        raise RuntimeError('Claude a repondu %s : %s'
                           % (res.status_code, res.text[:300]))
    data = res.json()
    vc._enregistrer_tokens({
        'promptTokenCount': (data.get('usage') or {}).get('input_tokens'),
        'candidatesTokenCount': (data.get('usage') or {}).get('output_tokens'),
        'thoughtsTokenCount': 0,
    }, modele)
    texte = ''.join(b.get('text', '') for b in (data.get('content') or [])
                    if isinstance(b, dict)).strip()
    if texte.startswith('```'):
        texte = texte.split('\n', 1)[1] if '\n' in texte else texte
        if texte.rstrip().endswith('```'):
            texte = texte.rstrip()[:-3]
    return json.loads(texte.strip())


async def _call_openai_max_completion_tokens(prompt: str, cle: str,
                                              modele: str) -> dict:
    """Appel OpenAI avec le nom de parametre attendu par les modeles recents."""
    import httpx
    corps = {
        'model': modele,
        'messages': [{'role': 'user', 'content': prompt}],
        'response_format': {'type': 'json_object'},
        'max_completion_tokens': 16384,
    }
    entetes = {'Authorization': 'Bearer ' + cle,
               'Content-Type': 'application/json'}
    async with httpx.AsyncClient(timeout=180.0) as client:
        reponse = await client.post(URL_OPENAI, headers=entetes, json=corps)
    if reponse.status_code != 200:
        raise RuntimeError('%s a repondu %s : %s'
                           % (modele, reponse.status_code, reponse.text[:300]))
    donnees = reponse.json()
    vc._enregistrer_tokens({
        'promptTokenCount': (donnees.get('usage') or {}).get('prompt_tokens'),
        'candidatesTokenCount': (donnees.get('usage') or {}).get('completion_tokens'),
        'thoughtsTokenCount': ((donnees.get('usage') or {})
                               .get('completion_tokens_details') or {}
                               ).get('reasoning_tokens'),
    }, modele)
    try:
        texte = donnees['choices'][0]['message']['content']
    except (KeyError, IndexError) as e:
        raise RuntimeError('Reponse %s illisible : %s' % (modele, e))
    return json.loads(texte)


async def appeler_openai(prompt: str, cle: str, modele: str) -> dict:
    """Appel OpenAI par le code de l'appli, avec deux rattrapages mesures.

    1. PROPAGATION (mesure du 24/09/2026) : juste apres avoir ouvert les modeles
       dans le tableau de bord, le premier appel renvoie encore
       `403 does not have access to model` -- puis ca passe tout seul quelques
       minutes plus tard. On attend donc 20 secondes et on reessaie une fois,
       plutot que d'afficher un echec incomprehensible pour Laurent.
    2. PARAMETRE (meme jour) : les modeles `gpt-5.4-*` refusent `max_tokens`,
       celui qu'envoie le code de l'appli :
           400 Unsupported parameter: 'max_tokens' ... 'max_completion_tokens'
       On reessaie alors avec le nom attendu par ces modeles.
       ATTENTION : le code de l'appli n'est PAS modifie (l'appli n'appelle pas
       OpenAI) -- mais le jour ou on y branchera OpenAI, il faudra CE repli.
    """
    try:
        return await vc._call_openai_compatible(prompt, URL_OPENAI, cle, modele)
    except RuntimeError as erreur:
        message = str(erreur)
        if 'does not have access to model' in message:
            # Six essais espaces de 15 s : chez OpenAI, la propagation des
            # autorisations est MOMENTANEE et IRREGULIERE -- mesure du
            # 24/09/2026 : le meme appel passe, puis est refuse une minute plus
            # tard, puis repasse. On insiste donc, au lieu d'afficher un echec
            # incomprehensible pour Laurent.
            derniere = erreur
            for tentative in range(1, 7):
                print('   OpenAI %s : autorisations en cours de propagation -- '
                      'nouvel essai dans 15 s (%d/6).' % (modele, tentative))
                await asyncio.sleep(15)
                try:
                    return await vc._call_openai_compatible(
                        prompt, URL_OPENAI, cle, modele)
                except RuntimeError as nouvelle:
                    derniere = nouvelle
                    if 'does not have access to model' not in str(nouvelle):
                        break
            raise derniere
        if 'max_completion_tokens' not in message:
            raise
    # Le modele a refuse `max_tokens` : on renvoie le meme appel avec le nom
    # qu'il attend.
    return await _call_openai_max_completion_tokens(prompt, cle, modele)


# ==============================================================
# MESURER LES SORTIES DE CADRE (idee de ChatGPT, du 24/09/2026)
# ==============================================================
# L'appli IGNORE deja un numero invente par l'IA -- `modules/voice_casting.py`,
# `_normaliser_reponse` : « un numero inconnu (invente par l'IA) est ignore --
# il ne doit jamais atteindre la base ». Verrouiller la sortie n'apporterait donc
# rien de plus. Ce qui manquait, c'est de le MESURER : aujourd'hui, ces sorties
# de cadre disparaissent en silence, et personne ne sait si un moteur le fait.
#
# On enveloppe donc cette fonction (le code de l'appli n'est pas modifie) pour
# compter, par moteur :
#   - les numeros HORS LOT (inventes) ;
#   - les numeros DONNES A DEUX PERSONNAGES : l'appli garde le premier et jette
#     le second sans le dire -- la aussi, on veut le savoir.
HORS_CADRE = {}
PROVIDER_COURANT = {'nom': None}


def surveiller_sorties_de_cadre() -> None:
    origine = vc._normaliser_reponse

    def _enveloppe(result, fiche, ids_envoyes):
        nom_moteur = PROVIDER_COURANT.get('nom')
        if nom_moteur and isinstance(result, dict):
            compte = HORS_CADRE.setdefault(nom_moteur,
                                           {'numeros': set(), 'doublons': set()})
            repliques = result.get('repliques')
            if isinstance(repliques, dict):
                deja_vus = set()
                for ids in repliques.values():
                    if not isinstance(ids, list):
                        continue
                    for valeur in ids:
                        try:
                            i = int(valeur)
                        except (TypeError, ValueError):
                            continue
                        if i not in ids_envoyes:
                            compte['numeros'].add(i)
                        elif i in deja_vus:
                            compte['doublons'].add(i)
                        else:
                            deja_vus.add(i)
        return origine(result, fiche, ids_envoyes)

    vc._normaliser_reponse = _enveloppe


def brancher_les_providers(cles_fichier: dict, config: dict, modeles: dict,
                           demandes: list, journal) -> dict:
    """Installe l'aiguillage des moteurs que l'appli ne connait pas -- ou d'un
    AUTRE modele que celui de l'appli -- et retourne {provider: (cle, provenance)}.

    L'aiguillage se fait en enveloppant `vc._call_llm` : le code de l'appli
    n'est PAS modifie, tout le reste du chemin reste le sien.
    """
    hotes = {}
    utilisables = {}
    modele_claude = modeles.get('claude') or MODELE_CLAUDE
    modele_mistral = modeles.get('mistral') or 'mistral-large-latest'

    # --- Mistral avec un AUTRE modele que celui de l'appli ------------------
    # Constate le 24/09/2026 : l'abonnement de Laurent n'a pas acces a
    # `mistral-large-latest` (403 « not available in your subscription tier »),
    # qui est pourtant le modele du bouton Mistral de l'appli. Pour comparer, on
    # passe par le meme code compatible OpenAI, avec le modele demande.
    if modele_mistral != 'mistral-large-latest':
        try:
            cle_mistral = get_mistral_api_key()
        except Exception as e:
            cle_mistral = ''
            journal('Mistral : %s' % str(e)[:90])
        if cle_mistral:
            async def _mistral(prompt, _cle=cle_mistral, _modele=modele_mistral):
                return await vc._call_openai_compatible(
                    prompt, vc.MISTRAL_URL, _cle, _modele)
            hotes['mistral'] = _mistral
    MODELES_EFFECTIFS['mistral'] = modele_mistral

    # --- OpenAI : une COLONNE par modele demande (mini, nano...) ------------
    colonnes_openai = [(cle, PROVIDERS[cle]['modele']) for cle in demandes
                       if cle == 'openai' or cle.startswith('openai:')]
    for cle_colonne, modele in colonnes_openai:
        cle_api, provenance = trouver_cle('openai', cles_fichier, config)
        MODELES_EFFECTIFS[cle_colonne] = modele
        if not cle_api:
            journal('OpenAI ignore : %s' % provenance)
            continue

        async def _openai(prompt, _cle=cle_api, _modele=modele):
            return await appeler_openai(prompt, _cle, _modele)
        hotes[cle_colonne] = _openai
        utilisables[cle_colonne] = (cle_api, provenance
                                    + ', modele %s' % modele)

    cle, provenance = trouver_cle('claude', cles_fichier, config)
    if cle:
        async def _claude(prompt, _cle=cle, _modele=modele_claude):
            return await asyncio.to_thread(_call_claude, prompt, _cle, _modele)
        hotes['claude'] = _claude
        utilisables['claude'] = (cle, provenance
                                 + ', modele %s' % modele_claude)
    elif 'claude' in demandes:
        journal('Claude ignore : %s' % provenance)
    MODELES_EFFECTIFS['claude'] = modele_claude

    if hotes:
        origine = vc._call_llm

        async def _aiguillage(prompt, provider='gemini'):
            if provider in hotes:
                return await hotes[provider](prompt)
            return await origine(prompt, provider)

        vc._call_llm = _aiguillage

    return utilisables




# ==============================================================
# LE TOUR D'UN PROVIDER
# ==============================================================

def cout_du_provider(provider: str, tokens: dict):
    """Le cout en dollars, ou None si le projet n'a pas de tarif pour ce moteur
    (on refuse alors d'inventer un chiffre)."""
    tarifs = vc.PROVIDER_PRICES_USD.get(provider)
    if not tarifs:
        return None
    return round((tokens['entree'] / 1_000_000) * tarifs['in']
                 + ((tokens['sortie'] + tokens['reflexion']) / 1_000_000)
                 * tarifs['out'], 5)


async def interroger(provider: str, passage: str, regle: str, verite: dict,
                     sentences: list, tours: int) -> list:
    """Interroge UN provider, `tours` fois, et rend un bulletin par tour."""
    return [await _un_tour(provider, passage, regle, verite, sentences, tour)
            for tour in range(1, tours + 1)]


async def _un_tour(provider: str, passage: str, regle: str, verite: dict,
                   sentences: list, tour: int) -> dict:
    """Un tour d'un provider, avec un nouvel essai en cas de refus TEMPORAIRE.

    Pourquoi (mesure du 24/09/2026) : les autorisations d'un fournisseur
    distant peuvent etre en cours de propagation -- le meme appel passe, puis
    est refuse, puis repasse. Sans ce filet, le rapport afficherait « ECHEC »
    alors que le moteur etait simplement en train d'ouvrir.
    """
    essai = {'tour': tour, 'erreur': None, 'duree': 0.0, 'tentatives': 0}
    avant = dict(vc._TOKENS_SESSION)
    debut = time.time()
    PROVIDER_COURANT['nom'] = provider
    for tentative in range(1, 4):
        essai['tentatives'] = tentative
        try:
            resultat = await vc.analyze_chapter(
                passage, fiche_personnages=[], provider=provider,
                provider_repli=[], regle=regle)
        except Exception as e:
            essai['erreur'] = '%s : %s' % (type(e).__name__, str(e)[:300])
        else:
            essai['erreur'] = None
            break
        if 'does not have access to model' not in essai['erreur']:
            break
        if tentative < 3:
            print('   %s : refus temporaire (autorisations en cours de '
                  'propagation) -- nouvel essai du tour dans 30 s (%d/3).'
                  % (PROVIDERS[provider]['libelle'], tentative))
            await asyncio.sleep(30)

    PROVIDER_COURANT['nom'] = None
    essai['duree'] = round(time.time() - debut, 1)
    apres = dict(vc._TOKENS_SESSION)
    essai['tokens'] = {cle: apres[cle] - avant[cle]
                       for cle in ('appels', 'entree', 'sortie', 'reflexion')}
    if essai['erreur'] is None:
        essai['refusees'] = sorted(resultat.get('refusees') or [])
        essai['bulletin'] = noter(resultat, verite, sentences)
    return essai



# ==============================================================
# LE RAPPORT
# ==============================================================

CODES = {
    'OK': '.',
    'NARRATION': 'N',
    'INVENTE': 'I',
    'FUSION': 'U',
    'FAUX': 'F',
    'ABSENT': '-',
}


def nom_du_moteur(provider: str, config: dict) -> str:
    if provider in MODELES_EFFECTIFS:
        return MODELES_EFFECTIFS[provider]
    if provider == 'local':
        return config.get('local_model', 'qwen2.5:latest')
    return PROVIDERS[provider]['modele']


def titre_provider(provider: str, config: dict) -> str:
    return '%s (%s)' % (PROVIDERS[provider]['libelle'],
                        nom_du_moteur(provider, config))


def _titre(texte: str) -> list:
    return ['', '=' * 78, ' ' + texte, '=' * 78]


def _entete_rapport(passage: str, sentences: list, verite: dict,
                    resultats: dict, utilisables: dict, regle: str) -> list:
    delicats = sum(1 for v in verite.values() if v['litigieux'])
    lignes = ['=' * 78,
              ' COMPARAISON DES PROVIDERS SUR UN PASSAGE PIEGE',
              ' date : %s' % time.strftime('%Y-%m-%d %H:%M'),
              ' decoupe : regle %s (celle des livres en mode dialogue)' % regle,
              ' passage : %d phrases, %d caracteres'
              % (len(sentences), len(passage)),
              ' verite terrain : %d phrases attendues, dont %d cas delicats'
              % (len(verite), delicats),
              '=' * 78]
    lignes += _titre('QUI A ETE INTERROGE')
    config = lire_config()
    for provider in resultats:
        _cle, provenance = utilisables.get(provider, (None, ''))
        lignes.append('  %-38s %s'
                      % (titre_provider(provider, config), provenance))
    return lignes


def _lignes_scores(resultats: dict) -> list:
    """Le classement, puis le detail tour par tour."""
    lignes = _titre('LES SCORES (classes du meilleur au moins bon)')
    lignes.append('  %-22s %6s %14s %14s %8s %12s'
                  % ('provider', 'tours', 'score strict', 'cas delicats',
                     'duree', 'cout'))
    for provider, bulletins in resultats.items():
        fins = [b for b in bulletins if b['erreur'] is None]
        libelle = PROVIDERS[provider]['libelle']
        if not fins:
            lignes.append('  %-22s %6d %14s %14s %8s %12s'
                          % (libelle, len(bulletins), 'ECHEC', '-',
                             '%.1fs' % bulletins[0]['duree'], '-'))
            continue
        score = sum(b['bulletin']['score_strict'][2] for b in fins) / len(fins)
        delicat = sum(b['bulletin']['score_delicat'][2]
                      for b in fins) / len(fins)
        duree = sum(b['duree'] for b in fins) / len(fins)
        tokens = {cle: sum(b['tokens'][cle] for b in fins)
                  for cle in ('entree', 'sortie', 'reflexion')}
        cout = cout_du_provider(provider, tokens)
        if cout is None:
            affichage_cout = 'inconnu'
        elif provider == 'local':
            # Le local est gratuit : on l'ecrit, plutot que « ~0.0000 $ » qui
            # laisse croire a une petite depense.
            affichage_cout = 'gratuit'
        elif cout < 0.0001:
            affichage_cout = '< 0.0001 $'
        else:
            affichage_cout = '~%.4f $' % cout
        lignes.append('  %-22s %6d %14s %14s %8s %12s'
                      % (libelle, len(bulletins), '%.0f %%' % score,
                         '%.0f %%' % delicat, '%.1fs' % duree,
                         affichage_cout))

    # Le detail par tour : un moteur qui change d'avis d'un tour a l'autre est
    # moins fiable qu'un moteur constant, meme a score egal.
    lignes.append('')
    lignes.append('  detail par tour :')
    for provider, bulletins in resultats.items():
        for b in bulletins:
            if b['erreur']:
                lignes.append('    %-16s tour %d : ECHEC (%s)'
                              % (PROVIDERS[provider]['libelle'], b['tour'],
                                 b['erreur']))
            else:
                ok, tout, pct = b['bulletin']['score_strict']
                lignes.append(
                    '    %-16s tour %d : %d/%d (%d %%) -- %d tokens entree, '
                    '%d sortie, %d reflexion, refus : %s%s'
                    % (PROVIDERS[provider]['libelle'], b['tour'], ok, tout,
                       pct, b['tokens']['entree'], b['tokens']['sortie'],
                       b['tokens']['reflexion'], b['refusees'] or 'aucun',
                       '' if b.get('tentatives', 1) <= 1 else
                       '  (%d essais : autorisations en cours de propagation)'
                       % b['tentatives']))
    lignes.append('')
    lignes.append('  noms choisis par le modele (le score est calcule APRES '
                  'correspondance des noms,')
    lignes.append('  pour mesurer l attribution et non le bapteme) :')
    for provider, bulletins in resultats.items():
        fin = next((b for b in bulletins if b['erreur'] is None), None)
        if fin is None:
            continue
        bulletin = fin['bulletin']
        paires = ', '.join('%s -> %s' % (notre, sien)
                           for notre, sien in bulletin['noms'].items())
        lignes.append('    %-18s %s'
                      % (PROVIDERS[provider]['libelle'],
                         paires or '(aucun personnage reconnu)'))
        for obtenu, noms in bulletin['fusion'].items():
            lignes.append('      FUSION : « %s » sert pour %s'
                          % (obtenu, ' et '.join(noms)))
    return lignes



def _code_colonne(provider: str) -> str:
    """Le code de 3 a 6 lettres qui sert d'entete de colonne dans le tableau."""
    if provider == 'local':
        return 'loc'
    return PROVIDERS[provider].get('code') or PROVIDERS[provider]['libelle'][:3].lower()


def _lignes_tableau(sentences: list, verite: dict, resultats: dict) -> list:
    """Le tableau phrase par phrase : une colonne par provider."""
    lignes = _titre('LE TABLEAU, PHRASE PAR PHRASE')
    lignes.append(' code : . juste   N le narrateur lit une replique   '
                  'I un personnage lit la narration')
    lignes.append('        U un seul nom pour deux personnages   F mauvais '
                  'personnage   X fournisseur en echec')
    lignes.append('')
    colonnes = [(p, _code_colonne(p)) for p in resultats]
    lignes.append('  %-4s %-50s %-16s %s'
                  % ('#', 'phrase (telle que le modele la recoit)', 'attendu',
                     ' '.join('%-4s' % c[1] for c in colonnes)))
    for sid in sorted(verite):
        texte = next((s['texte'] for s in sentences if s['id'] == sid), '')
        if len(texte) > 50:
            texte = texte[:47] + '...'
        cases = []
        for provider, _ in colonnes:
            fin = next((b for b in resultats.get(provider) or []
                        if b['erreur'] is None), None)
            if fin is None:
                cases.append('%-4s' % 'X')
                continue
            detail = next((d for d in fin['bulletin']['details']
                           if d['id'] == sid), None)
            cases.append('%-4s' % (CODES.get(detail['verdict'], '?')
                                   if detail else '-'))
        lignes.append('  %-4d %-50s %-16s %s'
                      % (sid, texte, verite[sid]['attendu'], ' '.join(cases)))
    return lignes


def _lignes_erreurs(resultats: dict) -> list:
    """Le detail des erreurs, provider par provider : c'est la qu'on apprend
    quelque chose (quel piege tombe, et chez qui)."""
    lignes = _titre('LES ERREURS, PROVIDER PAR PROVIDER')
    for provider, bulletins in resultats.items():
        for b in bulletins:
            if b['erreur']:
                continue
            fautes = [d for d in b['bulletin']['details']
                      if d['verdict'] != 'OK']
            lignes.append('')
            lignes.append('  %s -- tour %d : %d erreur(s)'
                          % (PROVIDERS[provider]['libelle'], b['tour'],
                             len(fautes)))
            for d in fautes:
                marque = ' [delicat]' if d['litigieux'] else ''
                lignes.append('    #%-3d %s' % (d['id'], d['texte'][:70]))
                lignes.append('         attendu : %-16s obtenu : %-16s %s%s'
                              % (d['attendu'], d['obtenu'] or '(rien)',
                                 d['verdict'], marque))
                if d['confiance'] or d['anomalie']:
                    lignes.append('         (confiance %s%s)'
                                  % (d['confiance'],
                                     ', ' + str(d['anomalie'])[:60]
                                     if d['anomalie'] else ''))
    return lignes


FAMILLES = [
    ('OK', 'juste'),
    ('INVENTE', 'invente : un personnage lit la NARRATION'),
    ('NARRATION', 'confusion : le NARRATEUR lit une replique'),
    ('FUSION', 'fusion : un seul nom pour deux personnages'),
    ('FAUX', 'mauvais personnage'),
    ('ABSENT', 'absent de la reponse'),
]


def _lignes_familles(resultats: dict) -> list:
    """Le resume par FAMILLE d'erreur (idee de ChatGPT, mesuree le 24/09/2026).

    Un score unique melange des fautes qui ne se ressemblent pas : « un
    personnage lit la narration » et « le narrateur lit une replique » ne
    s'entendent pas pareil. On les compte donc separement -- c'est ce tableau qui
    explique le classement (la colonne « invente » suffit a le reproduire).

    Les deux dernieres lignes viennent de la surveillance des sorties de cadre :
    elles montrent ce que l'appli corrige EN SILENCE.
    """
    lignes = _titre("LES FAMILLES D'ERREURS (ce que chaque moteur rate, et comment)")
    colonnes = list(resultats)
    lignes.append('  %-46s %s'
                  % ('famille',
                     '  '.join('%6s' % _code_colonne(c) for c in colonnes)))
    for cle_verdict, libelle in FAMILLES:
        valeurs = []
        for provider in colonnes:
            fin = next((b for b in resultats[provider]
                        if b['erreur'] is None), None)
            valeurs.append(fin['bulletin']['compte'].get(cle_verdict, 0)
                           if fin else 0)
        lignes.append('  %-46s %s'
                      % (libelle, '  '.join('%6d' % v for v in valeurs)))
    for cle, libelle in (('numeros', 'hors cadre : numero INVENTE (appli : ignore)'),
                         ('doublons', 'hors cadre : numero donne a DEUX personnages')):
        valeurs = [len(HORS_CADRE.get(p, {}).get(cle, ())) for p in colonnes]
        lignes.append('  %-46s %s'
                      % (libelle, '  '.join('%6d' % v for v in valeurs)))
    lignes.append('')
    lignes.append("  Lecture : « invente » = un personnage lit un morceau de "
                  "narration (le defaut que")
    lignes.append("  Laurent entend le plus mal) ; « confusion » = l'inverse, "
                  "le narrateur lit une replique.")
    return lignes


def ecrire_rapport(passage: str, sentences: list, verite: dict,
                   resultats: dict, utilisables: dict, regle: str) -> list:
    lignes = _entete_rapport(passage, sentences, verite, resultats,
                             utilisables, regle)
    lignes += _lignes_scores(resultats)
    lignes += _lignes_familles(resultats)
    lignes += _lignes_tableau(sentences, verite, resultats)
    lignes += _lignes_erreurs(resultats)
    lignes.append('')
    lignes.append('=' * 78)
    lignes.append(' Rappel : le moteur local est gratuit ; les autres sont '
                  'factures sur tes cles.')
    lignes.append('=' * 78)
    return lignes



# ==============================================================
# MODES GRATUITS : DECOUPER ET VERIFIER
# ==============================================================

def mode_decouper(sentences: list, verite: dict, regle: str) -> None:
    """Montre EXACTEMENT ce que le modele recevra (et ce qu'on attend de lui).
    Aucun appel, aucun euro."""
    print('Passage : %d phrases (regle de decoupe : %s)' % (len(sentences), regle))
    if verite:
        ids = {s['id'] for s in sentences}
        sans_attendu = sorted(i for i in ids if i not in verite)
        sans_phrase = sorted(i for i in verite if i not in ids)
        print('Verite terrain : %d attendus' % len(verite))
        if sans_attendu:
            print('  ATTENTION : %d phrase(s) sans attendu : %s'
                  % (len(sans_attendu), sans_attendu))
        if sans_phrase:
            print('  ATTENTION : %d attendu(s) sans phrase : %s'
                  % (len(sans_phrase), sans_phrase))
    else:
        print('Verite terrain : aucune (fichier %s absent)' % FICHIER_VERITE.name)
    print('')
    for s in sentences:
        print('  %3d. %s' % (s['id'], s['texte']))
        attendu = verite.get(s['id'])
        if attendu:
            print('        attendu : %-16s %s'
                  % (attendu['attendu'],
                     '[delicat] ' + attendu['note'] if attendu['litigieux']
                     else attendu['note']))


def mode_verifier(passage: str, sentences: list, verite: dict, regle: str,
                  demandes: list, pret: dict, config: dict, tours: int) -> None:
    """Controle tout ce qui peut l'etre SANS appeler personne : les cles, la
    longueur du prompt, la coherence de la verite terrain, le cout estime."""
    print('Passage      : %d phrases, %d caracteres'
          % (len(sentences), len(passage)))
    print('Prompt envoye: %d caracteres (le prompt complet, fiche vide)'
          % len(vc._build_prompt([], sentences)))
    print('Tours prevus : %d par provider' % tours)
    print('')
    print('Providers demandes :')
    for nom in demandes:
        if nom in pret:
            print('  PRET    %-34s %s'
                  % (titre_provider(nom, config), pret[nom][1]))
        else:
            print('  IGNORE  %-34s (voir message ci-dessus / ci-dessous)'
                  % titre_provider(nom, config))
    print('')
    print('Cout estime par provider (une passe, sur ce seul passage) :')
    for nom in demandes:
        if nom not in pret:
            continue
        if nom in vc.PROVIDER_PRICES_USD:
            estimation = vc.estimate_cast_cost([passage], nom, regle)
            print('  %-22s %s' % (PROVIDERS[nom]['libelle'],
                                  estimation['cost_display']))
        else:
            print('  %-22s tarif inconnu du projet : les tokens SERONT '
                  'releves, le cout non' % PROVIDERS[nom]['libelle'])
    print('')
    print('Pour lancer pour de vrai : ajoute --je-paie')


# ==============================================================
# LE LANCEMENT
# ==============================================================

async def lancer(demandes: list, pret: dict, passage: str, regle: str,
                 verite: dict, sentences: list, tours: int) -> dict:
    resultats = {}
    for provider in demandes:
        if provider not in pret:
            continue
        print('')
        print('--- %s : %d tour(s) ---' % (PROVIDERS[provider]['libelle'], tours))
        sys.stdout.flush()
        resultats[provider] = await interroger(provider, passage, regle, verite,
                                               sentences, tours)
    return resultats



# ==============================================================
# PROGRAMME PRINCIPAL
# ==============================================================

def _journal(message: str) -> None:
    print('  ' + message)


def analyser_arguments():
    analyseur = argparse.ArgumentParser(
        description='Compare les providers du casting sur un passage piege.')
    analyseur.add_argument('--je-paie', action='store_true', dest='je_paie',
                           help="obligatoire pour lancer pour de vrai (API facturees)")
    analyseur.add_argument('--tours', type=int, default=1,
                           help="nombre d'essais par provider (defaut 1)")
    analyseur.add_argument('--providers', default=PROVIDERS_DEFAUT,
                           help='liste separee par des virgules (defaut : %s)'
                                % PROVIDERS_DEFAUT)
    analyseur.add_argument('--regle', default='dialogue',
                           choices=('dialogue', 'actuelle'),
                           help='regle de decoupe (defaut : dialogue)')
    analyseur.add_argument('--modele-openai', default=MODELE_OPENAI,
                           dest='modele_openai',
                           help='un ou plusieurs modeles OpenAI, separes par des '
                                'virgules : chacun devient une colonne du '
                                'tableau (ex. gpt-5.4-mini,gpt-5.4-nano)')
    analyseur.add_argument('--modele-claude', default=MODELE_CLAUDE,
                           dest='modele_claude')
    analyseur.add_argument('--modele-mistral', default='mistral-large-latest',
                           dest='modele_mistral',
                           help="modele Mistral a comparer (defaut : celui de "
                                "l'appli ; utile quand l'abonnement ne donne pas "
                                "acces a mistral-large-latest)")
    analyseur.add_argument('--decouper', action='store_true',
                           help='montre les phrases numerotees et sort (gratuit)')
    analyseur.add_argument('--verifier', action='store_true',
                           help='controle les cles et le cout, sans appeler (gratuit)')
    return analyseur.parse_args()


def lister_demandes(texte: str) -> list:
    demandes = []
    for morceau in texte.split(','):
        nom = morceau.strip().lower()
        if not nom:
            continue
        if nom not in PROVIDERS:
            _journal('Provider inconnu, ignore : %s' % nom)
            continue
        if nom not in demandes:
            demandes.append(nom)
    return demandes


def etat_des_cles(demandes: list, utilisables: dict, config: dict) -> dict:
    """Dit, pour chaque provider demande, s'il est utilisable -- et pourquoi."""
    lecture = {'gemini': get_gemini_api_key,
               'deepseek': get_deepseek_api_key,
               'mistral': get_mistral_api_key}
    pret = {}
    for nom in demandes:
        if nom in lecture:
            try:
                lecture[nom]()
                pret[nom] = (None, "cle lue par l'appli (data/config.json)")
            except Exception as e:
                _journal('%s ignore : %s'
                         % (PROVIDERS[nom]['libelle'], str(e)[:90]))
        elif nom == 'local':
            etat = vc.local_disponible()
            if etat.get('disponible'):
                pret[nom] = (None, 'gratuit (Ollama), modele %s'
                             % etat.get('modele'))
            else:
                _journal('Modele local ignore : %s' % etat.get('raison'))
        elif nom in utilisables:
            pret[nom] = utilisables[nom]
    return pret


def ecrire_fichier_rapport(lignes: list) -> Path:
    chemin = DOSSIER / ('rapport_passage_piege_%s.txt'
                        % time.strftime('%Y%m%d_%H%M'))
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes) + '\n')
    return chemin



def main() -> int:
    args = analyser_arguments()
    regle = (decoupage.REGLE_DIALOGUE if args.regle == 'dialogue'
             else decoupage.REGLE_ACTUELLE)
    passage = lire_passage()
    sentences = vc._split_chapter_sentences(passage, regle)
    verite = lire_verite()

    if args.decouper:
        mode_decouper(sentences, verite, args.regle)
        return 0

    demandes = lister_demandes(args.providers)
    modeles_openai = [m.strip() for m in args.modele_openai.split(',') if m.strip()]
    demandes = preparer_colonnes(demandes, modeles_openai)
    cles_fichier = lire_cles_api()
    config = lire_config()
    modeles = {'claude': args.modele_claude, 'mistral': args.modele_mistral}
    utilisables = brancher_les_providers(cles_fichier, config, modeles,
                                         demandes, _journal)
    surveiller_sorties_de_cadre()
    pret = etat_des_cles(demandes, utilisables, config)

    if args.verifier:
        mode_verifier(passage, sentences, verite, args.regle, demandes, pret,
                      config, args.tours)
        return 0

    if not args.je_paie:
        print('=' * 72)
        print("ATTENTION : ce script appelle de VRAIES API d'IA PAYANTES.")
        print('Chaque appel est facture sur tes cles.')
        print('')
        print('Sur un passage court le cout est faible (voir --verifier), mais')
        print("ce n'est PAS un test de non-regression : c'est un outil d'atelier.")
        print('')
        print('Pour verifier sans rien payer :')
        print('    python test_voix/%s --decouper' % Path(__file__).name)
        print('    python test_voix/%s --verifier' % Path(__file__).name)
        print('Pour lancer pour de vrai :')
        print('    python test_voix/%s --je-paie' % Path(__file__).name)
        print('=' * 72)
        return 2

    if not pret:
        print('Aucun provider utilisable : rien a lancer.')
        return 1

    if args.tours < 1:
        print('--tours doit valoir au moins 1.')
        return 1

    debut = time.time()
    resultats = asyncio.run(lancer(demandes, pret, passage, regle, verite,
                                   sentences, args.tours))
    lignes = ecrire_rapport(passage, sentences, verite, resultats, pret,
                            args.regle)
    print('')
    for ligne in lignes:
        print(ligne)
    chemin = ecrire_fichier_rapport(lignes)
    print('')
    print('Rapport enregistre dans %s' % chemin.name)
    print('Duree totale : %.1f s' % (time.time() - debut))
    return 0


# ==============================================================
# GARDE-FOU : ce script DEPENSE DE L'ARGENT (regle du projet)
# ==============================================================
# Meme principe que `_PAYANT_test_attribution_api.py` : il envoie un VRAI texte
# a de VRAIES API. Le lanceur en double-clic demande donc explicitement « OUI »
# avant de passer `--je-paie` -- un double-clic seul ne paie jamais.
if __name__ == '__main__':
    sys.exit(main())

