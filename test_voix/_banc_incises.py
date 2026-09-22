# -*- coding: utf-8 -*-
"""BANC D'ECOUTE : les INCISES DE PAROLE, muettes ou lues par le narrateur.

Decision de Laurent (22/09/2026) : un reglage PAR LIVRE (« incises muettes » /
« incises lues par le narrateur »), changeable a l'ecoute par le bouton du
lecteur. Ce banc sert a JUGER A L'OREILLE ce que le texte ne peut pas dire :

  1. l'incise dite par le narrateur est-elle plus agreable que l'incise muette ?
  2. entend-on le MICRO-SILENCE a la jonction ? (un morceau de plus = une
     respiration possible de chaque cote)
  3. la VITESSE du menu (celle du narrateur) s'applique au morceau d'incise :
     est-ce que ca s'entend ?

Deux series, parce que la regle d'incises ne connait pas encore toutes les
formes (item ouvert du BACKLOG, « les incises a la 1re personne ») :

  SERIE 1 -- CE QUE TU PEUX REGLER TOUT DE SUITE (incises deja reconnues) :
     A = muette      (le reglage par defaut, ce que tu entends aujourd'hui)
     B = au narrateur (le nouveau bouton, tout de suite)

  SERIE 2 -- CE QUE L'ETAPE 3 APPORTERA (formes pas encore reconnues :
             « m'a-t-elle repondu », « m'a-t-il dit ») :
     A = l'incise dite par le PERSONNAGE (ce que tu entends aujourd'hui)
     B = l'incise dite par le NARRATEUR (ce que l'etape 3 donnera)

Chaque fichier WAV est fabrique par le VRAI chemin du lecteur : une requete a
`/api/tts` du serveur NIMM (port 8081), avec le drapeau `incise_a_lire` pour les
morceaux d'incise, et le collage des morceaux comme le fait la page. Ce que tu
entends ici est donc exactement ce que le lecteur produira.

Sortie : test_voix/ecoute_incises_<date>/ (WAV numerotes, index.txt,
variantes.txt = textes exacts, ECOUTER_LE_LOT.cmd).

Usage :
    python test_voix/_banc_incises.py
    python test_voix/_banc_incises.py --livre 28 --chapitres 10 11 --phrases 4
"""

import argparse
import datetime
import io
import json
import os
import re
import sqlite3
import struct
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
# Le prototype des incises est importe pour ses MOTIFS seulement : on lui demande
# de ne pas relancer sa mesure (30 s) pendant qu'on construit le banc.
os.environ.setdefault('NIMM_SANS_MESURE', '1')

from modules.decoupage import phrases as _decouper        # noqa: E402
from modules.incises import incises as _incises           # noqa: E402
from _moisson_incise_proto import spans_candidats         # noqa: E402

SERVEUR = 'http://127.0.0.1:8081'
BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

# Le serveur en marche connait-il le drapeau `incise_a_lire` ? Un morceau d'incise
# qui sort en moins de 0,2 s alors que son texte fait plus de 6 caracteres est un
# SILENCE (150 ms, `modules/silence.py`) : c'est la signature d'un serveur demarre
# AVANT cette fonction. On le dit a la fin, sinon le banc ferait croire a un defaut
# du reglage.
SILENCE_SUSPECT = False


# --- Le serveur NIMM --------------------------------------------------------

def serveur_pret():
    """(pret, message) : le serveur du LECTEUR repond-il ?"""
    try:
        with urllib.request.urlopen(SERVEUR + '/api/users', timeout=5):
            return True, ''
    except Exception as erreur:
        return False, str(erreur)


def demander(texte, voix, rate, pitch, incise_a_lire=False, book_id=0):
    """Un morceau de texte au serveur, EXACTEMENT comme le lecteur.

    `incise_a_lire` = le drapeau qui dit au serveur « ce morceau EST une incise,
    dis-la au lieu de la remplacer par un court silence ».
    """
    corps = json.dumps({'text': texte, 'voice': voix, 'rate': rate or '+0%',
                        'pitch': pitch or '+0Hz', 'book_id': book_id,
                        'incise_a_lire': bool(incise_a_lire)}).encode('utf-8')
    requete = urllib.request.Request(
        SERVEUR + '/api/tts', data=corps,
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(requete, timeout=180) as reponse:
        return reponse.read()


# --- Les WAV : lecture d'en-tete et collage (comme la page) -----------------

def format_wav(octets):
    """(canaux, cadence, bits) : ce qui doit etre IDENTIQUE pour coller deux WAV."""
    try:
        with wave.open(io.BytesIO(octets), 'rb') as f:
            return (f.getnchannels(), f.getframerate(), f.getsampwidth() * 8)
    except Exception:
        return None


def donnees_wav(octets):
    """(debut des donnees, taille annoncee) : on lit le bloc « data » de l'en-tete."""
    pos = octets.find(b'data')
    if pos < 0 or pos + 8 > len(octets):
        return None
    taille = struct.unpack('<I', octets[pos + 4:pos + 8])[0]
    return pos + 8, min(taille, len(octets) - (pos + 8))


def entete_wav(canaux, cadence, bits, taille):
    """Un en-tete WAV classique (44 octets), pour le morceau colle."""
    debit = cadence * canaux * (bits // 8)
    return (b'RIFF' + struct.pack('<I', 36 + taille) + b'WAVE'
            + b'fmt ' + struct.pack('<IHHIIHH', 16, 1, canaux, cadence, debit,
                                    canaux * (bits // 8), bits)
            + b'data' + struct.pack('<I', taille))


def coller(pieces):
    """Colle des morceaux WAV, comme le fait la page. Renvoie (octets, formats).

    `octets` vaut None si les formats different : c'est exactement ce que fait le
    lecteur (il repart alors en lecture morceau par morceau). On le DIT dans le
    compte rendu, parce que c'est precisement ce qui peut s'entendre comme un
    petit silence.
    """
    formats = [format_wav(p) for p in pieces]
    if not pieces or len(set(formats)) != 1:
        return None, formats
    bout = []
    total = 0
    for piece in pieces:
        emplacement = donnees_wav(piece)
        if emplacement is None:
            return None, formats
        debut, taille = emplacement
        bout.append(piece[debut:debut + taille])
        total += taille
    canaux, cadence, bits = formats[0]
    return entete_wav(canaux, cadence, bits, total) + b''.join(bout), formats


def duree_wav(octets):
    """Duree en secondes (0 si l'en-tete est illisible)."""
    try:
        with wave.open(io.BytesIO(octets), 'rb') as f:
            return f.getnframes() / float(f.getframerate() or 1)
    except Exception:
        return 0.0


# --- Ce qu'il faut savoir du livre ------------------------------------------

def lire_livre(book_id, chapitres):
    """(livre, phrases, voix, locuteurs) des chapitres demandes.

    `phrases` : [{chapitre, idx, texte, locuteur}] -- le texte vient de l'epub,
    les locuteurs de `speaker_attribution` (comme le lecteur).
    """
    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute(
        'SELECT id, title, filename, narrator_voice, decoupe_dialogue FROM books '
        'WHERE id = ?', (book_id,)).fetchone()
    if livre is None:
        conn.close()
        return None, [], {}, {}
    voix = {r['character_name']: dict(r) for r in conn.execute(
        'SELECT character_name, voice_id, pitch, rate, genre FROM voices '
        'WHERE book_id = ?', (book_id,))}
    locuteurs = {(r['chapter_index'], r['sentence_idx']): r['speaker']
                 for r in conn.execute(
                     'SELECT chapter_index, sentence_idx, speaker FROM '
                     'speaker_attribution WHERE book_id = ?', (book_id,))}
    conn.close()

    from core.epub_parser import get_chapters
    from modules.decoupage import REGLE_ACTUELLE, REGLE_DIALOGUE
    regle = REGLE_DIALOGUE if livre['decoupe_dialogue'] else REGLE_ACTUELLE
    phrases = []
    for chapitre in get_chapters(str(BIBLIOTHEQUE / livre['filename'])):
        if chapitre['index'] not in chapitres:
            continue
        for idx, texte in enumerate(_decouper(chapitre.get('text') or '', regle)):
            locuteur = locuteurs.get((chapitre['index'], idx), '')
            if locuteur == 'narration':
                continue                      # pas de personnage : rien a couper
            phrases.append({'chapitre': chapitre['index'], 'idx': idx,
                            'texte': texte, 'locuteur': locuteur})
    return livre, phrases, voix, regle


def morceaux(texte, spans):
    """[(texte, est_incise)] : miroir de `_morceauxDeLaPhrase` de la page."""
    if not spans:
        return [(texte, False)]
    pieces = []
    debut = 0
    for a, b in spans:
        if a > debut:
            pieces.append((texte[debut:a], False))
        pieces.append((texte[a:b], True))
        debut = b
    if debut < len(texte):
        pieces.append((texte[debut:], False))

    # La ponctuation orpheline est RATTACHEE au morceau voisin, jamais jetee
    # (le point final d'une incise terminale, par exemple).
    propres = []
    attente = ''
    for texte_piece, est_incise in pieces:
        if re.search(r'[A-Za-z\u00c0-\u024f]', texte_piece):
            propres.append((attente + texte_piece, est_incise))
            attente = ''
        elif propres:
            propres[-1] = (propres[-1][0] + texte_piece, propres[-1][1])
        else:
            attente += texte_piece
    if attente and propres:
        propres[-1] = (propres[-1][0] + attente, propres[-1][1])
    return propres


def voix_du_personnage(livre, voix, locuteur):
    """(voix, hauteur, vitesse) du personnage qui parle."""
    narrateur = (livre['narrator_voice'] or '').strip()
    fiche = voix.get(locuteur) or {}
    voix_id = (fiche.get('voice_id') or '').strip()
    if not voix_id:
        # Petit role : lu par le narrateur (regle des < 8 repliques).
        voix_id = narrateur
    hauteur = (fiche.get('pitch') or '+0Hz').strip() or '+0Hz'
    vitesse = (fiche.get('rate') or '').strip()
    if vitesse in ('', '+0%', '0%', '+0', '-0%'):
        vitesse = '+0%'
    return voix_id, hauteur, vitesse


def version_muette(texte, voix_perso, hauteur, vitesse, book_id):
    """A (muette) : la phrase ENTIERE au personnage ; le serveur retire l'incise."""
    return demander(texte, voix_perso, vitesse, hauteur, False, book_id)


def version_narrateur(texte, spans, voix_perso, hauteur, vitesse, voix_nar,
                      book_id):
    """B : la phrase coupee, chaque incise confiee au narrateur (drapeau compris).

    Renvoie (octets, formats, textes) : `octets` vaut None si les morceaux ne
    peuvent pas etre colles (formats differents d'un moteur a l'autre) -- c'est
    alors le lecteur qui jouerait morceau par morceau.
    """
    pieces = []
    textes = []
    for texte_piece, est_incise in morceaux(texte, spans):
        if est_incise:
            piece = demander(texte_piece, voix_nar, '+0%', '+0Hz', True, book_id)
            # Controle du drapeau (voir SILENCE_SUSPECT) : un silence de 150 ms a la
            # place d'une incise d'une dizaine de caracteres.
            if duree_wav(piece) < 0.2 and len(texte_piece) > 6:
                global SILENCE_SUSPECT
                SILENCE_SUSPECT = True
        else:
            piece = demander(texte_piece, voix_perso, vitesse, hauteur, False,
                             book_id)
        pieces.append(piece)
        textes.append(texte_piece)
    octets, formats = coller(pieces)
    return octets, formats, textes, pieces


# --- Le mode d'emploi du lot ------------------------------------------------

def _index_du_lot(livre, regle):
    """Ce que Laurent lit AVANT d'ecouter (le mode d'emploi)."""
    return [
        "A ECOUTER : LES INCISES DE PAROLE (« , dit-il, »)",
        '%s - livre : %s - regle de decoupage : %s'
        % (datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
           livre['title'][:50], regle),
        '',
        'Les fichiers se suivent, et sont numerotes DANS L ORDRE OU ILS SONT ECRITS.',
        '',
        '  SERIE 1 - le reglage que tu peux changer TOUT DE SUITE (bouton Incises)',
        "     S1_n_A_muette.wav     = l'incise est RETIREE du texte lu",
        "                             (ce que tu entends aujourd'hui, reglage par defaut)",
        "     S1_n_B_narrateur.wav  = l'incise est DITE PAR LE NARRATEUR",
        '                             (le nouveau bouton « lues par le narrateur »)',
        '',
        "  SERIE 2 - ce que l'etape 3 apportera (les formes que la regle ne connait",
        '            pas encore : « m a-t-elle repondu », « m a-t-il dit »)',
        "     S2_n_A_personnage.wav = l'incise dite par le PERSONNAGE (aujourd'hui)",
        "     S2_n_B_narrateur.wav  = l'incise dite par le NARRATEUR (apres l'etape 3)",
        '',
        "CE QU'ON TE DEMANDE (une reponse a donner a Cline, en francais) :",
        '   1. SERIE 1 : tu preferes A ou B ?',
        "   2. entends-tu un PETIT SILENCE a la jonction, avant et apres l'incise ?",
        "      (c'est le risque de ce reglage : un morceau de plus, donc une",
        '      respiration possible de chaque cote)',
        "   3. la VITESSE du narrateur sur le morceau d'incise te choque-t-elle ?",
        "      (c'est la vitesse du menu du bas qui s'applique la)",
        '   4. SERIE 2 : tu preferes A ou B ? (verdict sur l etape 3)',
        '',
        'Le dossier contient aussi variantes.txt : les textes EXACTS envoyes au',
        'serveur, la duree de chaque fichier et la COMPATIBILITE DES FORMATS. Quand',
        'deux moteurs differents se suivent (personnage en Kokoro, narrateur en',
        'Kyutai), le lecteur ne peut PAS coller les morceaux : il les joue un par un,',
        'et les fichiers sont alors numerotes B1, B2... C est exactement ce que tu',
        'entendrais dans le lecteur.',
    ]


def _traiter_serie(prefixe, serie, spans_de, libelles, livre, voix, voix_nar,
                   dossier, variantes):
    """Ecrit les fichiers d'une serie de phrases. Renvoie le nombre ecrit."""
    ecrits = 0
    print('')
    print('--- %s : %s ---'
          % (prefixe, "incises reconnues aujourd'hui" if prefixe == 'S1'
             else "formes pas encore reconnues (etape 3)"))
    for numero, p in enumerate(serie, 1):
        texte = p['texte']
        spans = [[a, b] for a, b in spans_de(texte)]
        voix_perso, hauteur, vitesse = voix_du_personnage(livre, voix,
                                                          p['locuteur'])
        print('')
        print('%s %d (chap. %d, phrase %d) : %s'
              % (prefixe, numero, p['chapitre'], p['idx'], texte[:70]))
        print('     locuteur : %-22s voix : %s' % (p['locuteur'][:22], voix_perso))
        variantes.append('--- %s %d (chap. %d, phrase %d) : %s'
                         % (prefixe, numero, p['chapitre'], p['idx'], texte))
        variantes.append('    locuteur %s | voix %s | hauteur %s | vitesse %s'
                         ' | incise(s) %r'
                         % (p['locuteur'], voix_perso, hauteur, vitesse, spans))

        # A -- ce qu'on entend aujourd'hui.
        try:
            a = version_muette(texte, voix_perso, hauteur, vitesse, livre['id'])
        except Exception as erreur:
            print('     A ECHEC : %s' % erreur)
            continue
        nom_a = '%s_%02d_A_%s.wav' % (prefixe, numero, libelles[0])
        (dossier / nom_a).write_bytes(a)
        ecrits += 1
        print('     %s  (%.2f s)' % (nom_a, duree_wav(a)))
        variantes.append('    %s  [%s]  %.2f s' % (nom_a, libelles[0],
                                                   duree_wav(a)))

        # B -- l'incise confiee au narrateur.
        try:
            b, formats, textes, pieces = version_narrateur(
                texte, spans, voix_perso, hauteur, vitesse, voix_nar, livre['id'])
        except Exception as erreur:
            print('     B ECHEC : %s' % erreur)
            continue
        if b is None:
            print('     formats %r : NON COLLABLES -> le lecteur joue morceau par'
                  ' morceau' % (formats,))
            variantes.append('    formats %r : non collables (le lecteur joue un'
                             ' morceau par morceau)' % (formats,))
            for k, morceau in enumerate(pieces, 1):
                nom_b = '%s_%02d_B%d_narrateur.wav' % (prefixe, numero, k)
                (dossier / nom_b).write_bytes(morceau)
                ecrits += 1
                print('     %s  (%.2f s)' % (nom_b, duree_wav(morceau)))
                variantes.append('    %s  [morceau %d]  %.2f s  %r'
                                 % (nom_b, k, duree_wav(morceau),
                                    textes[k - 1] if k <= len(textes) else ''))
        else:
            nom_b = '%s_%02d_B_%s.wav' % (prefixe, numero, libelles[1])
            (dossier / nom_b).write_bytes(b)
            ecrits += 1
            print('     %s  (%.2f s, %d morceau(x) colles)'
                  % (nom_b, duree_wav(b), len(textes)))
            variantes.append('    %s  [%s]  %.2f s  (morceaux : %r)'
                             % (nom_b, libelles[1], duree_wav(b), textes))
    return ecrits


def main():
    analyseur = argparse.ArgumentParser(
        description="Banc d'ecoute : les incises de parole, muettes ou dites par le narrateur.")
    analyseur.add_argument('--livre', type=int, default=28,
                           help='livre ou prendre les phrases (defaut : 28 = 22/11/63)')
    analyseur.add_argument('--chapitres', type=int, nargs='+', default=[10, 11],
                           help='chapitres (index en base) a fouiller (defaut : 10 11)')
    analyseur.add_argument('--phrases', type=int, default=4,
                           help='nombre de phrases par serie (defaut : 4)')
    options = analyseur.parse_args()

    pret, message = serveur_pret()
    if not pret:
        print('Le SERVEUR NIMM ne repond pas sur %s (%s).' % (SERVEUR, message))
        print('Double-clique sur START.bat (racine du projet), puis relance ce banc.')
        return 1

    livre, phrases, voix, regle = lire_livre(options.livre, set(options.chapitres))
    if livre is None:
        print('Livre %d introuvable.' % options.livre)
        return 1
    voix_nar = (livre['narrator_voice'] or '').strip()
    if not voix_nar:
        print("Ce livre n'a pas de voix de narrateur enregistree : le banc ne peut")
        print("pas montrer la version « au narrateur ». Ouvre le livre une fois dans")
        print('le lecteur (la voix par defaut y est enregistree), puis relance.')
        return 1

    print('')
    print('Banc : %s  |  narrateur : %s' % (livre['title'][:44], voix_nar))
    print('%d phrases attribuees a un personnage dans les chapitres %s (regle %s)'
          % (len(phrases), sorted(set(options.chapitres)), regle))

    # SERIE 1 : les incises que la regle reconnait AUJOURD'HUI.
    serie1 = [p for p in phrases if _incises(p['texte'])][:options.phrases]
    # SERIE 2 : celles qu'elle ne reconnait PAS ENCORE (regle candidate du
    # prototype). Le cas de la fillette (Annette Founijello), signale par Laurent
    # le 22/09/2026, passe en premier.
    serie2 = [p for p in phrases
              if not _incises(p['texte']) and spans_candidats(p['texte'])]
    serie2.sort(key=lambda p: 0 if ('Founijello' in p['texte']
                                    or 'Mouseketeer' in p['texte']) else 1)
    serie2 = serie2[:max(2, options.phrases - 1)]

    print('serie 1 (deja reglable) : %d phrase(s) | serie 2 (apres l etape 3) : %d'
          % (len(serie1), len(serie2)))
    if not serie1 and not serie2:
        print('Aucune incise dans ces chapitres : essaie --chapitres 9 10 11.')
        return 1

    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = ICI / ('ecoute_incises_%s' % horodatage)
    dossier.mkdir(parents=True, exist_ok=True)
    variantes = ['TEXTES EXACTS ENVOYES AU SERVEUR (pour verifier, pas pour ecouter)',
                 '']

    ecrits = _traiter_serie('S1', serie1, _incises, ('muette', 'narrateur'),
                            livre, voix, voix_nar, dossier, variantes)
    ecrits += _traiter_serie('S2', serie2, spans_candidats,
                             ('personnage', 'narrateur'),
                             livre, voix, voix_nar, dossier, variantes)

    (dossier / 'index.txt').write_text('\n'.join(_index_du_lot(livre, regle)),
                                       encoding='utf-8')
    if SILENCE_SUSPECT:
        variantes.append('')
        variantes.append('ATTENTION : un morceau d incise est sorti en SILENCE '
                         '(150 ms).')
        variantes.append('Le serveur NIMM en marche a ete demarre AVANT cette '
                         'fonction : il ignore')
        variantes.append('le drapeau « incise a lire ». Relance NIMM (START.bat) et '
                         'refais le lot,')
        variantes.append('sinon la version « au narrateur » est FAUSSE.')
    (dossier / 'variantes.txt').write_text('\n'.join(variantes), encoding='utf-8')
    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    if SILENCE_SUSPECT:
        print('')
        print('=' * 74)
        print(' ATTENTION : un morceau d incise est sorti en SILENCE (150 ms).')
        print(' Le serveur NIMM en marche a ete demarre AVANT cette fonction :')
        print(' il ignore le drapeau « incise a lire », donc la version')
        print(' « au narrateur » est FAUSSE.')
        print(' -> Relance NIMM (START.bat), puis refais le lot.')
        print('=' * 74)
        return 1

    print('')
    print('%d fichier(s) ecrit(s) dans %s' % (ecrits, dossier.name))
    print('Ecouter : double-clic sur ECOUTER_LE_LOT.cmd (dans ce dossier)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

