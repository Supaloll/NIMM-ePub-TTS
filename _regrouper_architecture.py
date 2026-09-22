# -*- coding: utf-8 -*-
"""Regroupe les sujets de ARCHITECTURE.md en PARTIES thematiques (une fois).

POURQUOI (decision de Laurent, 22/09/2026 — « que ce document TE soit utile ») :
apres la remise en place des titres (le 22/09/2026), le document avait 62 sujets
justes mais ranges dans l'ordre du JOURNAL : le casting, les moteurs, le cache et
le mode dialogue se suivent au fil des soirs, pas par sujet. Pour chercher, il
faut donc balayer tout le fichier.

Ce que fait cet outil : il range les 62 sujets en **10 parties** (le projet, le
serveur, la page, le texte lu, le casting, les voix, les moteurs, le mode
dialogue, l'ecoute, l'historique). Chaque sujet devient un `###` de sa partie,
et ses propres sous-titres descendent d'un cran.

LA PREUVE, ligne par ligne : les seules lignes qui changent sont les TITRES
(niveau + un cran) et les 10 titres de partie ajoutes. Tout le CONTENU est
compare avant/apres -- meme nombre de lignes, memes lignes. L'outil refuse
d'ecrire si un seul sujet n'est pas range, ou range deux fois.

Usage : python _regrouper_architecture.py            (apercu)
        python _regrouper_architecture.py --ecrire   (copie datee + ecriture)
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent
FICHIER = RACINE / 'ARCHITECTURE.md'

# Le plan de rangement : chaque partie, et les sujets qu'elle porte. Les sujets
# sont designes par un PREFIXE de leur titre (le script exige que le prefixe ne
# designe QU'UN sujet, sinon il refuse : c'est le garde-fou anti-collision).
PARTIES = [
    ('🧭 Le projet — vue d\'ensemble', [
        'Structure du dossier',
        'Principe général',
        'Flux principal',
        'Dépendances Python',
        'Workflow de développement',
        'Ordre de développement des fichiers',
    ]),
    ('🖥️ Le serveur : main.py et la base', [
        'main.py — Routes HTTP',
        'data/nimm_epub.db',
        '👨‍👩‍👧 Profils familiaux (multi-utilisateurs) — main.py',
    ]),
    ('🎬 La page (frontend) et la lecture', [
        'frontend/ — Interface',
        'Logique TTS — app.js',
        'Recherche dans le livre',
        'Effet glitch',
        'Mode RSVP',
        '📝 Deux idées RSVP',
        'Temps de lecture restant',
        'Cache busting',
        'START.bat — Lancement',
        '🔌 Serveurs fantômes',
        '🧹 Cache HTTP',
    ]),
    ('🔤 Le texte lu : extraction, nettoyage, découpage', [
        'core/epub_parser.py',
        'modules/tts.py — Synthèse vocale',
    ]),
    ('🎭 Le casting : qui parle, avec quelle voix', [
        '🎭 Distribution de voix par personnage',
        '🔀 Système multi-moteur',
        'Module voice_casting.py',
        '🧬 Bug corrigé',
        '🎯 Gard déterministe',
        '🧩 Regroupement des alias',
        '♻️ Re-cast d\'un livre déjà casté',
        '🎭 Les petits rôles',
        '🎭 Fenêtre du casting',
        '🎭 Filtres du casting',
        '🎭 En-tête compact',
        '🎧 Fenêtre « Écouter les voix »',
        'Critères FIXES d\'annotation',
        'Attribution des voix par critères',
        'Report des notes d\'écoute',
    ]),
    ('🎙️ Les voix : les pools et les notes d\'écoute', [
        '🔊 Banque de voix',
        '🔼 Règle des paliers d\'étoiles',
        'Ordre du pool automatique',
        '🎚️ Nouvel ordre du pool automatique',
        'Symboles ♀️ / ♂️ de genre',
        'Noms des voix',
        '🎨 NIMM Voix',
        'Voix du narrateur',
    ]),
    ('🗣️ Les moteurs de voix', [
        '🎛️ Changer de moteur de voix',
        '🎙️ Voix « écoutables »',
        '🛠️ Réparer les moteurs',
        '🗣️ Intégration Kokoro TTS',
        '🗣️ Prononciation française imposée',
        '🎙️ Moteur XTTS v2',
        'Extraits de voix libres de droits',
        '🎙️ Moteur de voix NeuTTS',
        '🎒 Moteur de voix Pocket TTS',
    ]),
    ('✂️ Le mode dialogue : narration et répliques', [
        '✂️ Mode dialogue',
    ]),
    ('🔒 Écouter dans de bonnes conditions', [
        '🔒 Lecture écran éteint',
        '🔒 Lire écran verrouillé',
        '💾 Cache audio serveur',
        '✂️ Rognage des silences',
    ]),
    ('📜 Journal des sessions passées', [
        '✅ Validation terrain complète',
        '🎬 Pistes ouvertes',
    ]),
]

# Les sujets qui disparaissent volontairement : un renvoi devenu inutile (la
# section qu'il annoncait est desormais juste au-dessus, dans la meme partie).
A_SUPPRIMER = [
    '👨‍👩‍👧 Profils familiaux (multi-utilisateurs) — renvoi',
]

# Un titre Markdown : des `#` suivis d'un ESPACE. Le document contient une seule
# ligne qui commence par `#` sans etre un titre (`#sent-prev-btn, …`, du CSS
# cite) : sans espace, elle n'est pas touchee. Verifie le 22/09/2026.
TITRE = re.compile(r'^(#{1,6}) (.*?)\s*$')


def _cle(texte):
    """Une clé de comparaison : sans emoji, sans tiret long, espaces réduits.

    Les emojis des titres sont difficiles à recopier à l'identique (séquences
    ZWJ, variantes de présentation) : on les retire des DEUX côtés, comme les
    tirets longs. « 👨‍👩‍👧 Profils familiaux — main.py » et le même titre tapé
    autrement deviennent la même clé.
    """
    net = re.sub(r'[\U0001F000-\U0001FAFF\u2190-\u21FF\u2600-\u27BF'
                 r'\u2B00-\u2BFF\uFE0F\u200D]', '', texte)
    net = net.replace('—', '-').replace('–', '-')
    return re.sub(r'\s+', ' ', net).strip().lower()


def decouper(lignes):
    """(preamble, [(titre_du_sujet, lignes_du_bloc)]) pour les sujets `##`."""
    debut = next((n for n, l in enumerate(lignes) if l.startswith('## ')), None)
    if debut is None:
        raise SystemExit('Aucun titre `##` trouve : le fichier a change.')
    blocs, courant, titre = [], [], None
    for ligne in lignes[debut:]:
        if ligne.startswith('## '):
            if titre is not None:
                blocs.append((titre, courant))
            titre, courant = ligne[3:].strip(), []
        else:
            courant.append(ligne)
    blocs.append((titre, courant))
    return lignes[:debut], blocs


def associer(titres):
    """Range chaque sujet dans sa partie. Refuse si un sujet manque ou double."""
    rangees, souci = {}, []
    cles = {t: _cle(t) for t in titres}
    for partie, prefixes in PARTIES:
        for prefixe in prefixes:
            veut = _cle(prefixe)
            trouve = [t for t in titres if cles[t].startswith(veut)]
            if len(trouve) != 1:
                souci.append('« %s » designe %d sujet(s) (il en faut 1)'
                             % (prefixe, len(trouve)))
            elif trouve[0] in rangees:
                souci.append('« %s » est range deux fois' % trouve[0])
            else:
                rangees[trouve[0]] = partie
    supprimes = [t for t in titres
                 if any(cles[t].startswith(_cle(p)) for p in A_SUPPRIMER)]
    for titre in titres:
        if titre not in rangees and titre not in supprimes:
            souci.append('sujet NON RANGE : « %s »' % titre[:70])
    return rangees, supprimes, souci


def monter_d_un_cran(lignes):
    """Un sujet devient `###` : ses propres titres descendent d'un cran."""
    sortie = []
    for ligne in lignes:
        m = TITRE.match(ligne)
        sortie.append('#' * (len(m.group(1)) + 1) + ' ' + m.group(2)
                      if m else ligne)
    return sortie


def contenu(blocs):
    """{titre: lignes de CONTENU} : tout sauf les lignes de titre."""
    return {t: [l for l in lignes if not TITRE.match(l)] for t, lignes in blocs}


def bloc_sommaire(rangees, blocs):
    """Une puce par PARTIE, ses sujets en sous-puces."""
    lignes = ['**Sommaire**', '']
    for partie, _prefixes in PARTIES:
        lignes.append('- **%s**' % partie)
        for titre, _corps in blocs:
            if rangees.get(titre) == partie:
                lignes.append('  - %s' % titre)
    lignes.append('')
    return lignes


def reassembler(preamble, blocs, rangees, sommaire):
    """Le nouveau document : les parties dans l'ordre, avec leurs sujets."""
    depart = next(n for n, l in enumerate(preamble)
                  if l.strip() == '**Sommaire**')
    fin = depart + 1
    while fin < len(preamble) and (not preamble[fin].strip()
                                   or preamble[fin].startswith(('- ', '  - '))):
        fin += 1
    nouveau = preamble[:depart] + sommaire + preamble[fin:]

    for rang, (partie, _prefixes) in enumerate(PARTIES):
        # Pas de `---` avant la premiere partie : le preambule en porte deja un.
        nouveau += ([] if rang == 0 else ['---', ''])
        nouveau += ['## %s' % partie, '']
        for titre, lignes in blocs:
            if rangees.get(titre) != partie:
                continue
            nouveau.append('### %s' % titre)
            nouveau += monter_d_un_cran(lignes)
    return nouveau


def main():
    ecrire = '--ecrire' in sys.argv
    brut = FICHIER.read_text(encoding='utf-8')
    fin_par_nl = brut.endswith('\n')
    lignes = brut.splitlines()

    preamble, blocs = decouper(lignes)
    titres = [t for t, _l in blocs]
    rangees, supprimes, souci = associer(titres)

    print('=' * 74)
    print(' REGROUPEMENT de ARCHITECTURE.md en parties%s'
          % ('' if ecrire else '  (apercu -- rien n est ecrit)'))
    print('=' * 74)
    print('  %d sujets lus, %d parties' % (len(titres), len(PARTIES)))
    for partie, _prefixes in PARTIES:
        dedans = [t for t in titres if rangees.get(t) == partie]
        print('')
        print('  ## %s  (%d sujets)' % (partie, len(dedans)))
        for titre in dedans:
            print('       %s' % titre[:78])

    print('')
    if souci:
        print('--- REFUS ---')
        for probleme in souci:
            print('  %s' % probleme)
        return 1
    print('  tous les sujets sont ranges (aucun oublie, aucun doublon)')
    for titre in supprimes:
        print('  supprime volontairement : %s' % titre[:70])

    sommaire = bloc_sommaire(rangees, blocs)
    nouveau = reassembler(preamble, blocs, rangees, sommaire)

    # LA PREUVE : le contenu de chaque sujet garde est identique, au caractere pres.
    avant = contenu(blocs)
    apres = contenu([(t, l) for t, l in blocs if rangees.get(t)])
    print('')
    print('--- preuve ---')
    print('  sujets ranges                    : %d' % len(apres))
    print('  sujets supprimes                 : %d' % len(supprimes))
    print('  lignes de contenu avant          : %d'
          % sum(len(v) for v in avant.values()))
    print('  lignes de contenu apres (garde)  : %d'
          % sum(len(v) for v in apres.values()))
    changes = [t for t in apres if avant.get(t) != apres[t]]
    print('  sujets dont le contenu a change  : %s'
          % (changes if changes else 'AUCUN'))
    print('  sommaire                         : %d parties, %d sujets'
          % (len(PARTIES), sum(1 for l in sommaire if l.startswith('  - '))))
    print('  fichier : %d lignes -> %d lignes'
          % (len(lignes), len(nouveau)))
    if changes:
        print('  REFUS : le contenu doit rester identique, rien n est ecrit.')
        return 1

    if not ecrire:
        print('')
        print('  Apercu seulement : ajoute --ecrire pour appliquer'
              ' (avec copie datee).')
        return 0

    copie = FICHIER.with_name(FICHIER.name + '.bak_avant_regroupement_'
                              + datetime.now().strftime('%Y%m%d_%H%M'))
    if not copie.exists():
        shutil.copy2(FICHIER, copie)
    FICHIER.write_text('\n'.join(nouveau) + ('\n' if fin_par_nl else ''),
                       encoding='utf-8')
    print('')
    print('  Copie datee   : %s' % copie.name)
    print('  Fichier ecrit : %s (%d lignes)' % (FICHIER.name, len(nouveau)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
