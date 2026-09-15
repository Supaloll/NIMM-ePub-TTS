# -*- coding: utf-8 -*-
"""
Compare plusieurs MODELES LOCAUX sur plusieurs chapitres, pendant la nuit
(session du 13/09/2026). AUCUN euro depense.

But : choisir le meilleur modele local possible sur la machine de Laurent,
avec des chiffres, sans rien ecouter -- la reference est le casting Gemini
deja enregistre pour chaque chapitre.

Le rapport est ecrit dans data/rapport_modeles_locaux.txt (les chapitres sont
choisis pour representer des cas differents : dialogue dense, recit, etc.).

Lancer depuis la racine :
    python test_voix/_test_nuit_modeles.py
    python test_voix/_test_nuit_modeles.py 4,12,20
    python test_voix/_test_nuit_modeles.py 4,12,20 "Qwen2.5:latest"
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

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
CONTEXTE_TOKENS = 16384        # modeles legers (Qwen2.5 : 4,7 Go)
CONTEXTE_TOKENS_LOURD = 10240  # modeles de 8B : assez pour le prompt (~7800
                               # mots) PLUS la reponse, sans deborder la carte
BOOK_ID = 28
RAPPORT = BASE / 'data' / 'rapport_modeles_locaux.txt'

CHAPITRES = [int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else '4,12,20').split(',')]
if len(sys.argv) > 2:
    MODELES = [m.strip() for m in sys.argv[2].split(',')]
else:
    MODELES = [
        "Qwen2.5:latest",
        "huihui_ai/qwen3-abliterated:8b",
        "deepseek-r1:8b",
    ]


def est_modele_lourd(modele):
    """Un modele de ~8B en Q4 (5 Go) PLUS un contexte de 16 384 mots ne tient
    pas dans les 8 Go de la carte (constat du 13/09/2026 : qwen3-abliterated
    chargeait 7,6 Go, dont 17 % du calcul renvoye sur le processeur -- 20 a 50
    fois plus lent). On reduit donc le contexte pour ces modeles."""
    return any(x in modele.lower() for x in ('qwen3', 'gemma4', 'r1', '14b', '32b', 'aya', 'granite'))


def appeler(prompt, modele):
    lourd = est_modele_lourd(modele)
    corps = {
        "model": modele,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_ctx": CONTEXTE_TOKENS_LOURD if lourd else CONTEXTE_TOKENS,
            "num_predict": 4096,
        },
    }
    if lourd:
        # Les modeles de raisonnement reflechissent avant de repondre : tres
        # lent, et parfaitement inutile pour cette tache repetitive. On coupe.
        corps["think"] = False
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(corps).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=3600) as r:
        rep = json.loads(r.read().decode("utf-8"))
    return (rep.get("message") or {}).get("content", ""), time.time() - t0


def modeles_installes():
    """Liste des modeles presents dans Ollama (aucun appel payant)."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [m.get("name", "") for m in (data.get("models") or [])]
    except Exception:
        return []


def attendre_modeles(modeles, timeout_min=150):
    """
    Attend que TOUS les modeles demandes soient telecharges avant de lancer
    les mesures : lance juste apres avoir clique sur les telechargements, le
    script patiente tout seul (verification toutes les 30 s).
    """
    debut = time.time()
    while True:
        presents = [m.lower() for m in modeles_installes()]
        manquants = [m for m in modeles
                     if not any(p == m.lower() or p.split(":")[0] == m.lower().split(":")[0]
                                for p in presents)]
        if not manquants:
            return True
        if time.time() - debut > timeout_min * 60:
            print("Delai d'attente depasse. Modeles encore absents : {}".format(
                ", ".join(manquants)), flush=True)
            return False
        print("En attente des telechargements ({} modele(s) restant(s) : {}). "
              "Verification toutes les 30 s...".format(
                  len(manquants), ", ".join(manquants)), flush=True)
        time.sleep(30)


def extraire_json(texte):
    texte = (texte or "").strip()
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut >= 0 and fin > debut:
        texte = texte[debut:fin + 1]
    return json.loads(texte)


def journaliser(lignes):
    print(lignes, flush=True)
    with open(RAPPORT, "a", encoding="utf-8") as f:
        f.write(lignes + "\n")


conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
fiche = [{'nom': r[0], 'genre': r[1], 'age': r[2]} for r in conn.execute(
    "SELECT character_name, genre, age FROM cast_fiche WHERE book_id = ?", (BOOK_ID,))]
verite = {}
for r in conn.execute("SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution WHERE book_id = ?",
                      (BOOK_ID,)):
    verite[(r[0], r[1])] = r[2]
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))

# On attend que les modeles demandes soient installes : le script peut etre
# lance juste apres avoir declenche les telechargements, il patientera seul.
modeles_pret = attendre_modeles(MODELES)

with open(RAPPORT, "w", encoding="utf-8") as f:
    f.write("RAPPORT DES MODELES LOCAUX -- {}\n".format(time.strftime('%Y-%m-%d %H:%M:%S')))
    f.write("Livre : {} | fiche de {} personnages | contexte adapte au modele (8192 si lourd, sinon 16384)\n".format(
        book[1], len(fiche)))
    f.write("Reference : casting Gemini deja en base\n\n")
    if not modeles_pret:
        f.write("Modeles manquants : arret avant les mesures.\n")

for modele in MODELES:
    journaliser('')
    journaliser('=' * 78)
    journaliser('MODELE : {}'.format(modele))
    journaliser('=' * 78)
    journaliser('{:<10} {:>8} {:>9} {:>9} {:>9} {:>9}'.format(
        'chapitre', 'duree', 'phrases', 'rappel', 'precision', 'accord'))
    for ch in CHAPITRES:
        sentences = vc._split_chapter_sentences(chapters[ch]['text'])
        ref_repliques = {s['id'] for s in sentences
                         if verite.get((ch, s['id']), 'narration') != 'narration'}
        trouve = set()
        duree = 0.0
        erreurs = 0
        for i in range(0, len(sentences), vc.BATCH_SIZE):
            lot = sentences[i:i + vc.BATCH_SIZE]
            try:
                texte, d = appeler(vc._build_prompt(fiche, lot), modele)
                norm = vc._normaliser_reponse(extraire_json(texte), fiche, {s['id'] for s in lot})
            except Exception:
                erreurs += 1
                continue
            duree += d
            for p in norm['phrases']:
                if p['locuteur'] != 'narration':
                    trouve.add(p['id'])
        rappel = 100.0 * len(trouve & ref_repliques) / max(len(ref_repliques), 1)
        precision = 100.0 * len(trouve & ref_repliques) / max(len(trouve), 1)
        accord = sum(1 for s in sentences if (s['id'] in trouve) == (s['id'] in ref_repliques))
        journaliser('{:<10} {:>7.0f}s {:>9} {:>8.0f}% {:>8.0f}% {:>8.0f}%{}'.format(
            ch + 1, duree, len(sentences), rappel, precision,
            100.0 * accord / max(len(sentences), 1),
            '  ({} lots en erreur)'.format(erreurs) if erreurs else ''))

journaliser('')
journaliser('Rappel    = part des vraies repliques trouvees (a maximiser)')
journaliser('Precision = part des attributions qui sont de vraies repliques')
journaliser('Accord    = phrases avec le meme diagnostic que Gemini')
journaliser('')
journaliser('Rapport ecrit dans {}'.format(RAPPORT))
