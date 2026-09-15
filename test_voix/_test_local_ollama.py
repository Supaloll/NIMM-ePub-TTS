# -*- coding: utf-8 -*-
"""
Test LOCAL via Ollama (session du 13/09/2026) -- AUCUN euro depense,
tout se passe sur le PC.

Objet : faire analyser un chapitre par un modele local et comparer, phrase
par phrase, avec le casting GEMINI deja enregistre pour ce meme chapitre.
C'est la reponse a la question de Laurent : « verifier la qualite demande
d'ecouter tout le livre ». Ici la reference existe deja : on mesure un taux
d'accord automatiquement, sans rien ecouter.

Lancer depuis la racine :
    python test_voix/_test_local_ollama.py 16
    python test_voix/_test_local_ollama.py 16 Qwen2.5:latest
"""
import sys
import json
import time
import sqlite3
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

# API NATIVE d'Ollama : seule facon de fixer num_ctx (constat du 13/09/2026 :
# Ollama bride le contexte a 4096 tokens par defaut, alors que notre prompt en
# fait ~7800 -- le modele ne voyait qu'une partie du texte).
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
CONTEXTE_TOKENS = 16384
BOOK_ID = 28
CHAPITRE = int(sys.argv[1]) if len(sys.argv) > 1 else 16
MODELE = sys.argv[2] if len(sys.argv) > 2 else "Qwen2.5:latest"


def appeler_ollama(prompt):
    """Envoie le prompt au modele local. Retourne (texte, duree, usage)."""
    corps = {
        "model": MODELE,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_ctx": CONTEXTE_TOKENS, "num_predict": 4096},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(corps).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=1800) as r:
        rep = json.loads(r.read().decode("utf-8"))
    usage = {
        "prompt_tokens": rep.get("prompt_eval_count") or 0,
        "completion_tokens": rep.get("eval_count") or 0,
    }
    return (rep.get("message") or {}).get("content", ""), time.time() - t0, usage


def extraire_json(texte):
    """Le modele encadre parfois son JSON de balises ``` : on recupere l'objet."""
    texte = (texte or "").strip()
    if texte.startswith("```"):
        texte = texte.split("```")[1] if "```" in texte[3:] else texte[3:]
        if texte.lower().startswith("json"):
            texte = texte[4:]
    debut = texte.find("{")
    fin = texte.rfind("}")
    if debut >= 0 and fin > debut:
        texte = texte[debut:fin + 1]
    return json.loads(texte)


print('')
print('=' * 70)
print('TEST LOCAL (Ollama) -- modele {}'.format(MODELE))
print('=' * 70)

conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
fiche = [{'nom': r[0], 'genre': r[1], 'age': r[2]} for r in conn.execute(
    "SELECT character_name, genre, age FROM cast_fiche WHERE book_id = ? ORDER BY character_name",
    (BOOK_ID,))]
verite = {(r[0], r[1]): r[2] for r in conn.execute(
    "SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution "
    "WHERE book_id = ? AND chapter_index = ?", (BOOK_ID, CHAPITRE))}
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))
sentences = vc._split_chapter_sentences(chapters[CHAPITRE]['text'])
lots = [sentences[i:i + vc.BATCH_SIZE] for i in range(0, len(sentences), vc.BATCH_SIZE)]

print('Livre    : {}'.format(book[1]))
print('Chapitre : {} ("{}"), {} phrases, {} lots'.format(
    CHAPITRE + 1, chapters[CHAPITRE]['title'], len(sentences), len(lots)))
print('Fiche    : {} personnages (la fiche reelle du livre)'.format(len(fiche)))
print('Reference: casting Gemini deja en base pour ce chapitre')
print('')
print('Debut des envois au modele local...')
print('')

tot_phrases = 0
tot_accord = 0
desaccords = []
erreurs = 0
duree_totale = 0.0
tok_entree = tok_sortie = 0

for numero, lot in enumerate(lots, start=1):
    ids = {s['id'] for s in lot}
    try:
        texte, duree, usage = appeler_ollama(vc._build_prompt(fiche, lot))
    except Exception as e:
        print('  lot {} : ERREUR d\'appel ({})'.format(numero, str(e)[:120]), flush=True)
        erreurs += 1
        continue

    duree_totale += duree
    tok_entree += int(usage.get('prompt_tokens') or 0)
    tok_sortie += int(usage.get('completion_tokens') or 0)

    try:
        norm = vc._normaliser_reponse(extraire_json(texte), fiche, ids)
    except Exception as e:
        print('  lot {} : reponse illisible ({}) en {:.0f} s'.format(
            numero, str(e)[:100], duree), flush=True)
        erreurs += 1
        continue

    accord_lot = 0
    for p in norm['phrases']:
        ref = verite.get((CHAPITRE, p['id']))
        if ref is None:
            continue
        tot_phrases += 1
        if (p['locuteur'] != 'narration') == (ref != 'narration'):
            tot_accord += 1
            accord_lot += 1
        else:
            desaccords.append((p['id'], p['locuteur'], ref))
    print('  lot {} ({} phrases) : {:.0f} s, accord {}/{}, sortie {} tokens'.format(
        numero, len(lot), duree, accord_lot, len(lot),
        int(usage.get('completion_tokens') or 0)), flush=True)

print('')
print('=' * 70)
print('RESULTAT')
print('=' * 70)
print('Duree totale           : {:.1f} s ({:.1f} min) pour {} phrases'.format(
    duree_totale, duree_totale / 60.0, len(sentences)))
if tot_phrases:
    print('Phrases comparees      : {}'.format(tot_phrases))
    print('Meme diagnostic        : {} ({:.1f} %)'.format(
        tot_accord, 100.0 * tot_accord / tot_phrases))
    print('Desaccords narration/replique : {} ({:.1f} %)'.format(
        len(desaccords), 100.0 * len(desaccords) / tot_phrases))
print('Lots en erreur         : {}'.format(erreurs))
print('Tokens locaux (entree/sortie) : {} / {}'.format(tok_entree, tok_sortie))
if tot_phrases:
    print('')
    print('EXTRAPOLATION pour un livre de 25 000 phrases :')
    print('  temps estime : ~{:.1f} h'.format(
        duree_totale / max(tot_phrases, 1) * 25000 / 3600.0))
print('')
if desaccords:
    print('Premiers desaccords (phrase : local -> reference Gemini) :')
    for sid, nouveau, ref in desaccords[:20]:
        print('  phrase {:>4} : {:<26} -> {}'.format(sid, str(nouveau)[:26], ref))
    print('')
    print('  Chaque desaccord peut etre ecoute plus tard, avec son contexte,')
    print('  au lieu du livre entier : c\'est la verification ciblee.')
print('')
print('Fin du test local.')

