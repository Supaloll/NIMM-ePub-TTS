# -*- coding: utf-8 -*-
"""
ETUDE (lecture seule, aucun appel IA, gratuit) : quelle part du travail
d'attribution pourrait etre faite SANS IA, par de simples regles Python ?

Idee : un roman contient enormement de phrases purement narratives ("Il
ferma la porte."), qui ne demandent aucun raisonnement. Si une regle de
detection de dialogue les ecarte de facon fiable, on ne paie l'IA que pour
les repliques -- soit beaucoup moins d'appels, et surtout beaucoup moins de
tokens de sortie (la partie la plus chere).

Methode : on compare, phrase par phrase, ce que l'IA a REELLEMENT repondu
(en base, apres le casting du 13/09/2026) avec ce qu'une regle aurait dit.
Cela mesure a la fois le GAIN et la FIABILITE de la regle.

Lancer depuis la racine : python test_voix/_etude_pretraitement.py 28
"""
import sys
import re
import sqlite3
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from core.epub_parser import get_chapters
from modules import voice_casting as vc

BOOK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 28

# --- Regles : une phrase peut contenir du DIALOGUE si... ---
RE_MARQUES = re.compile(r'[«»"“”]|\u2014|(^|\s)[-–]\s')
RE_VERBES = re.compile(
    r"\b(dit|dis|dire|répond|repond|répliqu|repliqu|s'écri|s'ecri|murmur|"
    r"demand|ajout|reprit|reprenn|répét|repet|soupir|grommel|lanç|lança|"
    r"observ|poursuiv|s'exclam|exclaim|protest|conclu|rappel|précis|precis|"
    r"expliqu|pens[ae]|songea|reconnu|avou|annonç|annonc|cria|appela|"
    r"repondit|susurr|bougonna|maugréa|rican)\w*\b",
    re.IGNORECASE)


def contient_dialogue(texte, dans_une_citation=False):
    """True si la phrase peut contenir du dialogue (donc a confier a l'IA).

    Point clef : une longue replique est souvent DECOUPEE en plusieurs
    phrases par le decoupage automatique, et seule la premiere porte le
    guillemet ouvrant. Une phrase situee a l'interieur d'une citation
    encore ouverte fait donc partie du dialogue, meme sans aucun marqueur.
    """
    if dans_une_citation:
        return True
    if RE_MARQUES.search(texte):
        return True
    if RE_VERBES.search(texte):
        return True
    return False


conn = sqlite3.connect('file:{}?mode=ro'.format((BASE / 'data' / 'nimm_epub.db').as_posix()), uri=True)
book = conn.execute("SELECT filename, title FROM books WHERE id = ?", (BOOK_ID,)).fetchone()
attributions = {}
for r in conn.execute("SELECT chapter_index, sentence_idx, speaker FROM speaker_attribution WHERE book_id = ?",
                      (BOOK_ID,)):
    attributions[(r[0], r[1])] = r[2]
conn.close()

chapters = get_chapters(str(BASE / 'data' / 'library' / book[0]))

total = 0
ecartees = 0          # phrases que la regle envoie au narrateur SANS IA
ecartees_ok = 0       # ... et que l'IA avait bien mises en narration
ecartees_erreur = 0   # ... mais que l'IA avait attribuees a un personnage
gardees = 0           # phrases que la regle confie a l'IA
gardees_dialogue = 0  # ... qui sont bien des repliques
exemples_erreur = []

for ch in chapters:
    sentences = vc._split_chapter_sentences(ch['text'])
    citation_ouverte = 0
    for s in sentences:
        locuteur = attributions.get((ch['index'], s['id']))
        dedans = citation_ouverte > 0
        # Etat de la citation mis a jour AVANT le test : ainsi la phrase qui
        # OUVRE la citation est elle aussi consideree comme dialogue.
        texte = s['texte']
        citation_ouverte += texte.count('«') - texte.count('»')
        if citation_ouverte < 0:
            citation_ouverte = 0
        if locuteur is None:
            continue
        total += 1
        est_dialogue_ia = (locuteur != 'narration')
        if contient_dialogue(texte, dedans):
            gardees += 1
            if est_dialogue_ia:
                gardees_dialogue += 1
        else:
            ecartees += 1
            if not est_dialogue_ia:
                ecartees_ok += 1
            else:
                ecartees_erreur += 1
                if len(exemples_erreur) < 12:
                    exemples_erreur.append((ch['index'], s['id'], locuteur))

# Les phrases DEJA en narration dans la base (mesure directe, sans regle)
nb_narration = sum(1 for v in attributions.values() if v == 'narration')

print('')
print('=' * 68)
print('POTENTIEL D\'UN PRETRAITEMENT SANS IA -- {}'.format(book[1]))
print('=' * 68)
print('Phrases analyses          : {:,}'.format(total).replace(',', ' '))
print('Dont narration (mesure IA): {:,} ({:.1f} %)'.format(
    nb_narration, 100.0 * nb_narration / max(total, 1)).replace(',', ' '))
print('Dont repliques (mesure IA): {:,} ({:.1f} %)'.format(
    total - nb_narration, 100.0 * (total - nb_narration) / max(total, 1)).replace(',', ' '))
print('')
print('CE QUE LA REGLE FERAIT')
print('  Phrases confiees a l\'IA : {:,} ({:.1f} % du livre)'.format(
    gardees, 100.0 * gardees / max(total, 1)).replace(',', ' '))
print('     dont vraies repliques : {:,} ({:.1f} % de precision)'.format(
    gardees_dialogue, 100.0 * gardees_dialogue / max(gardees, 1)).replace(',', ' '))
print('  Phrases ecartees (narration gratuite) : {:,} ({:.1f} % du livre)'.format(
    ecartees, 100.0 * ecartees / max(total, 1)).replace(',', ' '))
print('     dont l\'IA disait bien narration   : {:,} ({:.1f} % de fiabilite)'.format(
    ecartees_ok, 100.0 * ecartees_ok / max(ecartees, 1)).replace(',', ' '))
print('     et {:,} repliques qui seraient PERDUES ({:.2f} % du livre)'.format(
    ecartees_erreur, 100.0 * ecartees_erreur / max(total, 1)).replace(',', ' '))
print('')
print('GAIN DE TRAVAIL POUR L\'IA : {:.0f} % de phrases en moins'.format(
    100.0 * ecartees / max(total, 1)))
if exemples_erreur:
    print('')
    print('Exemples de repliques que la regle raterait (chapitre, phrase, locuteur) :')
    for ch_index, sid, loc in exemples_erreur:
        print('   chapitre {:>3}, phrase {:>4} : {}'.format(ch_index + 1, sid, loc))
print('')
print('Fin de l\'etude.')
