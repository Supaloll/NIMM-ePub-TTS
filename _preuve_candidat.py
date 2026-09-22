# -*- coding: utf-8 -*-
"""PREUVE (mesure seule) -- la regle candidate sur les phrases exactes de Laurent.

Reprend les phrases du 22/09/2026 (22/11/63, chapitres 10 et 11) et applique :
  - la regle d'AUJOURD'HUI (modules/incises.py) ;
  - la regle CANDIDATE (prototypee dans _moisson_incise_proto.py), limitee aux
    incises TERMINALES (celles qui finissent la phrase) : c'est la variante
    prudente.

Rien n'est modifie dans les modules : ce script ne fait qu'appeler.
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.incises import retirer_incises                    # noqa: E402
import _moisson_incise_proto as proto                          # noqa: E402

PHRASES = [
    # Le cas signale n1 (la fillette) : l'incise dit QUI parle.
    '– Annette Founijello, m’a-t-elle répondu.',
    'C’est la plus jolie Mouseketeer du Club Mickey Mouse.',
    '« Merci, monsieur, me dit Annette Founijello.',
    '– Et tu es aussi jolie qu’elle, l’ai-je complimentée.',
    # Le cas signale n2 (la narration entre tirets) : regle DIFFERENTE.
    '– il a brandi la baïonnette devant son visage pâle aux traits tirés –, « ce sera moi.',
    # Temoins : ce qui est deja retire aujourd'hui ne doit pas bouger.
    '– Vraiment, dit-il.',
    '– Baissez le ton », lui ai-je recommandé.',
]

print('%d phrases examinees.' % len(PHRASES))
for phrase in PHRASES:
    aujourd = retirer_incises(phrase)
    spans = proto.spans_candidats(phrase)
    candidat = proto.retirer(phrase, spans) if spans else phrase
    # La variante prudente : on ne garde que les incises TERMINALES.
    terminaux = [s for s in spans if not any(
        c.isalpha() for c in phrase[s[1]:])]
    prudent = proto.retirer(phrase, terminaux) if terminaux else phrase
    print('')
    print('  PHRASE    : %s' % phrase)
    print('  aujourd hui  : %s%s'
          % (aujourd, '   (rien retire)' if aujourd == phrase else ''))
    print('  candidat     : %s%s'
          % (candidat, '   (rien retire)' if candidat == phrase else ''))
    print('  prudent      : %s%s'
          % (prudent, '   (rien retire)' if prudent == phrase else ''))
