# -*- coding: utf-8 -*-
"""Le DECOUPAGE AVANT L'IA : un livre neuf est decoupe avant d'etre envoye.

Demande de Laurent (22/09/2026) : « Il faut suivre cette logique : d'abord le
decoupage, puis l'envoi a Gemini pour l'attribution des voix. Il faut que ce soit
automatique, si je caste un nouveau livre, il doit etre decoupe avant envoi a
Gemini. »

Ce que ce test verifie :
  1. `_livre_jamais_attribue` dit VRAI pour un livre sans aucune attribution, et
     FAUX des qu'une seule ligne existe -- c'est la condition qui autorise a
     changer le decoupage ;
  2. `_regle_pour_casting` rend la regle du MODE DIALOGUE pour un livre jamais
     attribue, et suit le drapeau du livre sinon ;
  3. dans le code de `start_casting`, l'activation du mode dialogue vient AVANT
     le premier appel a l'IA (`analyze_chapter`) ;
  4. l'estimation de cout utilise la MEME regle que le casting (sinon on annonce
     un prix pour un autre decoupage) ;
  5. un livre DEJA attribue n'est pas touche : changer son decoupage decalerait
     ses voix (c'est le role de la migration, pas du casting).

Les points 1 et 2 portent sur des fonctions REELLES, avec une petite base en
memoire. Les points 3 a 5 sont LUS dans le code source, comme le fait
test_start_moteur.py pour START.bat : c'est le chemin qu'on veut proteger, pas
une copie.

Usage : python test_voix/test_decoupage_auto_casting.py
"""

import os
import sqlite3
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.stdout.reconfigure(encoding='utf-8')

import main                                                     # noqa: E402
from modules.decoupage import REGLE_ACTUELLE, REGLE_DIALOGUE     # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


def corps_de(nom):
    """Le texte de la fonction `nom` dans main.py (jusqu'a la route suivante)."""
    source = (open(os.path.join(RACINE, 'main.py'), encoding='utf-8').read())
    debut = source.index('async def %s(' % nom)
    fin = source.find('\n@app.', debut)
    return source[debut:fin if fin > 0 else len(source)]


# --- 1) La condition : aucun numero de phrase a respecter ------------------
conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE speaker_attribution (book_id INTEGER, '
             'chapter_index INTEGER, sentence_idx INTEGER, speaker TEXT)')
verifier('un livre sans aucune attribution est vu comme JAMAIS attribue',
         main._livre_jamais_attribue(conn, 42) is True)
conn.execute('INSERT INTO speaker_attribution VALUES (42, 1, 0, "narration")')
conn.commit()
verifier('une SEULE attribution protege le livre (on ne change plus son '
         'decoupage)', main._livre_jamais_attribue(conn, 42) is False)
verifier('un AUTRE livre reste vu comme jamais attribue',
         main._livre_jamais_attribue(conn, 43) is True)
conn.close()

# --- 2) La regle annoncee --------------------------------------------------
verifier('livre jamais attribue -> narration separee',
         main._regle_pour_casting({'decoupe_dialogue': 0}, True)
         == REGLE_DIALOGUE)
verifier('livre deja attribue, en mode origine -> on ne touche a rien',
         main._regle_pour_casting({'decoupe_dialogue': 0}, False)
         == REGLE_ACTUELLE)
verifier('livre deja en mode dialogue -> narration separee',
         main._regle_pour_casting({'decoupe_dialogue': 1}, False)
         == REGLE_DIALOGUE)

# --- 3) L'ordre : decouper D'ABORD, appeler l'IA ensuite -------------------
casting = corps_de('start_casting')
verifier('start_casting active le mode dialogue',
         'decoupe_dialogue = 1' in casting)
verifier('cette activation est reservee aux livres jamais attribues',
         '_livre_jamais_attribue(conn, book_id)' in casting)
position_mode = casting.find('decoupe_dialogue = 1')
position_ia = casting.find('analyze_chapter')
verifier('elle vient AVANT le premier appel a l IA',
         -1 < position_mode < position_ia,
         'mode a %s, IA a %s' % (position_mode, position_ia))

# --- 4) L'estimation parle du MEME decoupage que le casting -----------------
estimation = corps_de('get_cast_estimate')
verifier('l estimation de cout utilise la regle du casting',
         '_regle_pour_casting(book, jamais_attribue)' in estimation)
verifier('elle sait si le livre a deja des attributions',
         '_livre_jamais_attribue(conn, book_id)' in estimation)

print('')
print('TOUT EST OK' if ECHECS == 0
      else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
sys.exit(0 if ECHECS == 0 else 1)
