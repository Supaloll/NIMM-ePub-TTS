# -*- coding: utf-8 -*-
"""Banc d'ecoute : QUELLE PONCTUATION REMPLACER LE « ! » ? (+ les incises).

Retour d'ecoute de Laurent (18/09/2026) : les interjections (« Oh », « Ah »,
« Eh ») sont « nettement mieux », mais « ca traine encore un peu ». Le « ! » est
retire du texte envoye au moteur et remplace par un POINT (une seule ligne a
changer : `PONCTUATION_EXCLAMATION`, modules/tts.py). Ce banc compare QUATRE
ponctuations sur les MEMES phrases reelles de Laurent, pour choisir a l'oreille :

    P1  le point        « Oh. »      (le reglage actuel)
    P2  la virgule      « Oh, »
    P3  la suspension   « Oh… »
    P4  rien du tout    « Oh »

Deuxieme question portee par le MEME banc (idee de Laurent du meme soir) : les
INCISES de parole (« , dit-il, ») — les garder, ou les retirer puisqu'une voix
par personnage dit deja qui parle ?

    I1  l'incise gardee  « — Il partit, dit-il. »
    I2  l'incise retiree « — Il partit. »

Sortie : test_voix/ecoute_ponctuation_<date>/ (WAV numerotes + index.txt +
ECOUTER_LE_LOT.cmd). Le moteur Kyutai doit etre allume.

IMPORTANT : le texte des variantes est envoye au moteur TEL QUEL (sans passer par
le nettoyage du lecteur), sinon celui-ci rajouterait un point partout et le banc
ne comparerait plus rien.

Usage :
    python test_voix/_banc_ponctuation_exclamation.py
    python test_voix/_banc_ponctuation_exclamation.py --livre 16 --phrases 6
"""

import argparse
import datetime
import json
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.decoupage import phrases as _decouper                   # noqa: E402

SERVICE = "http://127.0.0.1:8082"
BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'


def demander(texte, voix):
    """Un texte au service Kyutai, TEL QUEL (aucun nettoyage : voir l'en-tete).

    En cas de refus du service, on remonte SON message (il dit precisement ce
    qui ne va pas : « voix inconnue », « texte vide »...) : « HTTP Error 400 »
    tout seul ne dit rien a personne.
    """
    corps = json.dumps({"texte": texte, "voix": voix},
                       ensure_ascii=False).encode('utf-8')
    requete = urllib.request.Request(
        SERVICE + "/tts", data=corps,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(requete, timeout=180) as reponse:
            return reponse.read()
    except urllib.error.HTTPError as erreur:
        try:
            detail = erreur.read().decode('utf-8', 'replace')
        except Exception:
            detail = ''
        raise RuntimeError('%s : %s' % (erreur.code, detail[:120]))


def _duree(octets):
    """Duree en secondes d'un WAV en memoire."""
    import io
    import wave
    try:
        with wave.open(io.BytesIO(octets), 'rb') as f:
            return f.getnframes() / float(f.getframerate())
    except Exception:
        return 0.0



# ==============================================================
# LES QUATRE PONCTUATIONS
# ==============================================================

def variantes_ponctuation(phrase):
    """[(code, libelle, texte)] : la meme phrase, avec 4 ponctuations."""
    def remplacer(signe):
        texte = re.sub(r'\s*!+', signe, phrase)
        texte = re.sub(r'\s{2,}', ' ', texte)
        return texte.strip()

    return [
        ('P1', 'le point (reglage actuel)', remplacer('.')),
        ('P2', 'la virgule', remplacer(',')),
        ('P3', 'la suspension', remplacer('\u2026')),
        ('P4', 'rien du tout', remplacer(' ')),
    ]


# La règle de retrait des incises vit dans `modules/incises.py` : c'est la MEME
# que celle qui sert a la lecture (modules/tts.py). Un banc d'ecoute qui
# testerait une autre regle que celle du lecteur ne prouverait rien.
from modules.incises import incises, retirer_incises                # noqa: E402




# ==============================================================
# LE BANC
# ==============================================================

def lire_livre(livre_id):
    """(livre, phrases, voix classees par nombre de repliques)."""
    from core.epub_parser import get_chapters

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    livre = conn.execute('SELECT * FROM books WHERE id = ?',
                         (livre_id,)).fetchone()
    if livre is None:
        conn.close()
        return None, [], []
    voix = conn.execute(
        'SELECT voice_id, line_count FROM voices WHERE book_id = ? '
        'ORDER BY line_count DESC', (livre_id,)).fetchall()
    conn.close()

    chapitres = get_chapters(str(BIBLIOTHEQUE / livre['filename']))
    phrases = []
    for chapitre in chapitres:
        phrases.extend(_decouper(chapitre.get('text') or ''))
    return dict(livre), phrases, [dict(v) for v in voix]


def echantillon(phrases, nombre):
    """Un echantillon VARIE : des courtes, des moyennes, des longues."""
    tries = sorted(phrases, key=len)
    if len(tries) <= nombre:
        return tries
    pas = len(tries) / float(nombre)
    return [tries[min(len(tries) - 1, int(i * pas))] for i in range(nombre)]


def _index_du_lot(livre, voix_courte):
    """Ce que Laurent lit avant d'ecouter (le mode d'emploi du lot)."""
    return [
        "A ECOUTER : LA PONCTUATION DU POINT D EXCLAMATION (ET LES INCISES)",
        '%s - livre : %s - voix : %s'
        % (datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
           livre['title'][:50], voix_courte),
        '',
        "Le « ! » n'est plus envoye au moteur (il faisait monter la voix). Il est",
        "remplace par un POINT pour l'instant. Ce lot compare QUATRE choix sur les",
        'MEMES phrases de ton livre :',
        '',
        "   P1 = le point      (ce que tu entends aujourd'hui)",
        '   P2 = la virgule',
        '   P3 = la suspension',
        '   P4 = rien du tout',
        '',
        'DEUXIEME QUESTION, dans le meme lot : les INCISES (« , dit-il, »).',
        "   I1 = l'incise est gardee   (ce que tu entends aujourd'hui)",
        "   I2 = l'incise est retiree  (« - Il partit. »)",
        '',
        "CE QU'ON TE DEMANDE :",
        '   pour chaque numero de phrase, ecoute les 4 fichiers a la suite',
        '   (P_1_P1, P_1_P2, P_1_P3, P_1_P4), puis classe-les du meilleur au',
        '   moins bon. Exemple de reponse a donner a Cline :',
        '       1 : P1, P3, P2, P4',
        '       2 : P3, P1, P4, P2',
        '       incises : I2 mieux que I1 partout',
        '',
        "Ce qu'on cherche : la ponctuation qui EVITE la voix qui « traine » sur les",
        'interjections (« Oh », « Ah », « Eh »), sans casser le sens.',
        '',
        'Les textes exacts envoyes au moteur sont dans variantes.txt.',
    ]


def main():
    analyseur = argparse.ArgumentParser(
        description="Banc d'ecoute : la ponctuation du « ! » et les incises.")
    analyseur.add_argument('--livre', type=int, default=16,
                           help='livre ou prendre les phrases (defaut : 16)')
    analyseur.add_argument('--phrases', type=int, default=6,
                           help='nombre de phrases par serie (defaut : 6)')
    analyseur.add_argument('--voix', default=None,
                           help='voix Kyutai a utiliser (defaut : la plus bavarde du livre)')
    options = analyseur.parse_args()

    try:
        with urllib.request.urlopen(SERVICE + '/sante', timeout=5) as reponse:
            sante = json.loads(reponse.read().decode('utf-8'))
        if not sante.get('pret'):
            print('Le moteur Kyutai est encore en train de charger : attends un peu.')
            return 1
    except Exception as erreur:
        print('Le moteur Kyutai ne repond pas sur %s (%s).' % (SERVICE, erreur))
        print('Double-clique sur kyutai_service\\DEMARRER_KYUTAI.bat, puis relance.')
        return 1

    livre, phrases, voix = lire_livre(options.livre)
    if livre is None:
        print('Livre %d introuvable.' % options.livre)
        return 1

    # La voix : celle du livre si elle est Kyutai (le plus fidele a l'ecoute),
    # sinon la premiere voix Kyutai du catalogue.
    choix = options.voix
    if not choix:
        for v in voix:
            if v['voice_id'].startswith('kyutai:'):
                choix = v['voice_id']
                break
    if not choix:
        from modules.tts import KYUTAI_VOICES
        choix = KYUTAI_VOICES[0]['id']
    voix_courte = choix.split(':', 1)[1] if ':' in choix else choix

    # Les deux series de phrases, choisies dans SON livre.
    avec_exclamation = echantillon([p for p in phrases if '!' in p],
                                   options.phrases)
    avec_incise = echantillon([p for p in phrases if incises(p)],
                              options.phrases)

    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = ICI / ('ecoute_ponctuation_%s' % horodatage)
    dossier.mkdir(parents=True, exist_ok=True)
    index = _index_du_lot(livre, voix_courte)
    variantes = ['TEXTES EXACTS ENVOYES AU MOTEUR (pour verifier, pas pour ecouter)',
                 '']
    total = 0

    print('')
    print('Banc : %s | voix %s' % (livre['title'][:46], voix_courte))
    print('phrases du livre : %d (%d avec « ! », %d avec incise)'
          % (len(phrases), len([p for p in phrases if '!' in p]),
             len([p for p in phrases if incises(p)])))
    print('=' * 74)

    for numero, phrase in enumerate(avec_exclamation, 1):
        print('')
        print('PHRASE %d : %s' % (numero, phrase[:78]))
        variantes.append('--- PHRASE %d : %s' % (numero, phrase))
        for code, libelle, texte in variantes_ponctuation(phrase):
            nom = 'P_%d_%s.wav' % (numero, code)
            try:
                wav = demander(texte, voix_courte)
            except Exception as erreur:
                print('   %s ECHEC : %s' % (nom, erreur))
                continue
            (dossier / nom).write_bytes(wav)
            variantes.append('%s  [%s]  %.2f s  ->  %s'
                             % (nom, libelle, _duree(wav), texte))
            print('   %s (%s) %.2f s' % (nom, libelle, _duree(wav)))
            total += 1

    for numero, phrase in enumerate(avec_incise, 1):
        sans = retirer_incises(phrase)
        if sans == phrase:
            continue
        print('')
        print('INCISE %d : %s' % (numero, phrase[:78]))
        variantes.append('--- INCISE %d : %s' % (numero, phrase))
        for code, libelle, texte in (('I1', 'incise gardee', phrase),
                                     ('I2', 'incise retiree', sans)):
            nom = 'I_%d_%s.wav' % (numero, code)
            try:
                wav = demander(texte, voix_courte)
            except Exception as erreur:
                print('   %s ECHEC : %s' % (nom, erreur))
                continue
            (dossier / nom).write_bytes(wav)
            variantes.append('%s  [%s]  %.2f s  ->  %s'
                             % (nom, libelle, _duree(wav), texte))
            print('   %s (%s) %.2f s' % (nom, libelle, _duree(wav)))
            total += 1

    (dossier / 'index.txt').write_text('\n'.join(index), encoding='utf-8')
    (dossier / 'variantes.txt').write_text('\n'.join(variantes), encoding='utf-8')
    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    print('')
    print('%d fichiers ecrits dans %s' % (total, dossier.name))
    print('Ecouter : double-clic sur ECOUTER_LE_LOT.cmd')
    return 0


if __name__ == '__main__':
    sys.exit(main())
