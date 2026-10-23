# -*- coding: utf-8 -*-
"""Ecouter chaque voix et REECRIRE le texte de sa reference -- NIMM ePub.

POURQUOI (02/10/2026, demande de Laurent). Le clonage d'une voix (mode ICL)
aligne l'AUDIO de reference sur SON TEXTE. Quand les deux ne correspondent pas
exactement -- le texte commence ou finit sur un mot incomplet, ou il manque un
mot -- le moteur recoit un couple incoherent et fabrique un defaut : un mot
parasite au tout debut des phrases (le « te »), ou une voix qui part en derive.

Le seul juge fiable, c'est l'oreille : les transcriptions automatiques se
trompent. Mesure du 02/10/2026 (atelier NIMM Voix) : jusqu'a 10,4 s de decalage
entre Whisper et l'alignement force, et 46 mots « entendus » la ou 42 sont
reellement places.

Cet outil ouvre donc UNE PAGE dans le navigateur, ou pour chaque voix :
  - on ECOUTE la reference (avec un bouton « rejouer le debut de 2 s », parce
    que le defaut est justement au debut) ;
  - on REECRIT, a la main, exactement ce qu'on entend ;
  - on ENREGISTRE : la correction est notee tout de suite, jamais perdue.

CE QU'IL ECRIT, ET RIEN D'AUTRE :
  test_voix\\_corrections_oreille.csv
      (voix ; texte entendu ; remarque ; quand) -- voix PUBLIQUES seulement ;
  test_voix\\_corrections_oreille_privees.csv
      (meme format) -- voix de `references_privees.csv` (Maya). Ce fichier est
      IGNORE PAR GIT : le CSV public est versionne, et un texte d'oeuvre sous
      droits ne doit jamais partir sur le depot ;
  test_voix\\_corrections_oreille_etat.json (ou on en etait : la derniere voix)
Le fichier de production `references.csv` n'est JAMAIS touche : appliquer les
corrections est un geste separe, apres validation (copie datee d'abord).

LA REMARQUE EST UNE CASE A PART (ajoutee le 03/10/2026 a la demande de Laurent,
apres qu'il a trouve un son parasite EN FIN de phrase). Elle ne part JAMAIS dans
la voix : la colonne du texte doit contenir exactement ce que la voix dit, rien
d'autre -- sinon le moteur lirait la remarque comme du texte et deraillerait a
nouveau. La remarque sert a retrouver les voix A REPARER : un parasite au debut
ou a la fin veut dire que l'AUDIO est coupe au milieu d'un mot, donc qu'il faut
RECOUPER la reference, pas corriger son texte.

AUCUNE API, rien a installer : uniquement la bibliotheque standard de Python.

Usage :
    python test_voix/_corriger_references_a_l_oreille.py
    python test_voix/_corriger_references_a_l_oreille.py --port 8099
    python test_voix/_corriger_references_a_l_oreille.py --sans-navigateur
    python test_voix/_corriger_references_a_l_oreille.py --lot DOSSIER

`--lot DOSSIER` (ajoute le 03/10/2026) : au lieu des voix de production, on
travaille sur un LOT pose dans ce dossier (il doit contenir un `references.csv`
et les WAV). Les corrections s'ecrivent alors DANS le lot. C'est ce qui sert
pour les 35 voix Kyutai recoupees : on ecoute le fichier recoupe ET on corrige
son texte au meme endroit.

LE 19/10/2026 : la liste affiche le PRENOM du catalogue a cote du nom de
fichier (« Theodore (Homme002) »), la recherche accepte le prenom, et le
bouton « Les 9 voix signalees » isole le lot signale par Laurent. Les DEUX
fichiers de textes sont lus (public + prive) : Maya, qui vit dans le prive,
apparait enfin.
"""
import argparse
import csv
import io
import json
import shutil
import sqlite3
import sys
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
DOSSIER_VOIX = RACINE / 'qwen_tts_service' / 'voix'
CSV_REFERENCES = DOSSIER_VOIX / 'references.csv'
# Le fichier PRIVE (hors Git) porte les textes d'œuvres sous droits, dont celui
# de Maya. Le service lit les DEUX et le prive gagne sur le public ; cet outil
# doit faire pareil, sinon Maya n'apparait pas dans la liste (constat du
# 19/10/2026 : elle manquait, il ne restait que 8 voix sur les 9 signalees).
CSV_PRIVEES = DOSSIER_VOIX / 'references_privees.csv'
DB = RACINE / 'data' / 'nimm_epub.db'
CSV_CORRECTIONS = DOSSIER / '_corrections_oreille.csv'
# Les corrections des voix PRIVEES (Maya) vivent dans un fichier SEPARE, ignore
# par Git : le CSV principal est versionne, et un texte d'oeuvre sous droits ne
# doit JAMAIS partir sur le depot (regle du projet). Le 19/10/2026, Maya est
# apparue dans le CSV principal des que l'outil a lu le fichier prive : ce
# fichier-ci est la reparation.
CSV_CORRECTIONS_PRIVEES = DOSSIER / '_corrections_oreille_privees.csv'
FICHIER_ETAT = DOSSIER / '_corrections_oreille_etat.json'
PORT_DEFAUT = 8099
# Les suffixes que le SERVICE reconnait (la meme liste que `SUFFIXES_FICHIERS` de
# `qwentts_service/servir_qwentts_cpp.py`) : les voix Kyutai, elles, portent
# `_enhanced_reference.wav`. CORRIGE LE 03/10/2026 : avec un seul suffixe connu,
# ces 35 voix s'affichaient avec un « _enhanced » colle au nom -- et le lecteur
# ne leur retrouvait plus leur usage dans les livres.
SUFFIXES = ('_enhanced_reference.wav', '_reference.wav')

# LES NEUF VOIX SIGNALEES PAR LAURENT LE 19/10/2026.
# La cle est le nom COURT du fichier de reference (sans suffixe) : c'est ce que
# `lire_references` fabrique, et donc ce que la page affiche a cote du prenom.
# Ce lot sert seulement a ISOLER ces voix dans la liste (bouton « Les 9 voix
# signalees ») : il ne modifie ni les voix ni les notes de Laurent.
VOIX_SIGNALEES_19_10_2026 = {
    'Homme002': 'Théodore',
    'Homme004': 'Édouard',
    'homme_aigu_6877654': 'Aubin',
    'Maya_normale': 'Maya',
    'cml1840': 'Achille',
    'cml1649': 'Berthe',
    'cml1869': 'Cécile',
    'cml2316': 'Joséphine',
    'cml3182': 'Maurice',
}


def lire_catalogue():
    """{nom court: {'prenom', 'region'}} depuis le catalogue Qwen du lecteur.

    POURQUOI (19/10/2026, retour de Laurent) : dans la fenetre d'ecoute, les
    voix s'appelaient `Homme002`, `cml1840`... -- des noms de FICHIERS, pas les
    prenoms qu'il connait (Theodore, Achille). Le catalogue de `modules/tts.py`
    est la seule source qui donne le prenom affiche ; on le lit ici, sans rien
    modifier. Si l'import echoue, la page continue de fonctionner avec les noms
    de fichiers (aucune voix ne disparait).
    """
    try:
        if str(RACINE) not in sys.path:
            sys.path.insert(0, str(RACINE))
        from modules import tts
    except Exception:
        return {}
    catalogue = {}
    for fiche in getattr(tts, 'QWEN_VOICES', []):
        identifiant = (fiche.get('id') or '').strip()
        if ':' in identifiant:
            identifiant = identifiant.split(':', 1)[1]
        for suffixe in SUFFIXES:
            if identifiant.endswith(suffixe):
                identifiant = identifiant[:-len(suffixe)]
                break
        if identifiant:
            catalogue[identifiant] = {
                'prenom': (fiche.get('name') or '').strip(),
                'region': (fiche.get('region') or '').strip(),
            }
    return catalogue


def nom_court(fichier):
    """`Homme002_reference.wav` -> `Homme002` (le nom que la page affiche)."""
    for suffixe in SUFFIXES:
        if fichier.endswith(suffixe):
            return fichier[:-len(suffixe)]
    return fichier


def cle_voix(identifiant):
    """`qwen:Femme004` et la reference `Femme004` : la meme cle.

    La base du lecteur range les voix prefixees par leur moteur
    (`qwen:Femme004`) ; le fichier des references ne porte que le nom.
    """
    texte = (identifiant or '').strip()
    if ':' in texte:
        texte = texte.split(':', 1)[1]
    return texte


def lire_references():
    """Les voix du service Qwen, telles que le service les lit.

    Rend une liste de dicts : fichier, nom, prenom, region, texte, duree,
    hauteur, signalee. Le PRENOM vient du catalogue (`modules/tts.py`) : c'est
    celui que Laurent connait (« Theodore »), a cote du nom de fichier
    (`Homme002`).

    LES DEUX FICHIERS SONT LUS, comme le service : `references.csv` (public)
    puis `references_privees.csv` (hors Git), le PRIVE ecrasant le public a nom
    de fichier egal. Sans cela, Maya (`Maya_normale`, texte prive) manquait.
    """
    lignes = []
    for chemin in (CSV_REFERENCES, CSV_PRIVEES):
        if not chemin.is_file():
            continue
        with open(chemin, encoding='utf-8-sig', newline='') as fichier:
            morceaux = list(csv.reader(fichier, delimiter=';'))
        if morceaux and morceaux[0] and morceaux[0][0].strip() == 'fichier':
            morceaux = morceaux[1:]
        lignes.extend(morceaux)

    # Le PRIVE gagne sur le public, comme dans le service : meme nom de fichier,
    # la derniere ligne lue est celle du fichier prive.
    par_fichier = {}
    for ligne in lignes:
        if len(ligne) >= 2 and ligne[0].strip():
            par_fichier[ligne[0].strip()] = ligne

    catalogue = lire_catalogue()
    voix = []
    for nom, ligne in par_fichier.items():
        court = nom
        for suffixe in SUFFIXES:
            if nom.endswith(suffixe):
                court = nom[:-len(suffixe)]
                break
        fiche = catalogue.get(court, {})
        voix.append({
            'fichier': nom,
            'nom': court,
            'prenom': fiche.get('prenom', ''),
            'region': fiche.get('region', ''),
            'texte': ligne[1].strip(),
            'duree': ligne[2].strip() if len(ligne) > 2 else '',
            'hauteur': ligne[3].strip() if len(ligne) > 3 else '',
            'signalee': court in VOIX_SIGNALEES_19_10_2026,
        })
    return voix


def lire_usages():
    """Ou chaque voix sert, d'apres la base du lecteur (OUVERTE EN LECTURE SEULE).

    Rend {nom_de_voix: {'narrateur': [titres], 'roles': [(titre, perso, n)]}}.
    """
    usages = {}
    if not DB.is_file():
        return usages
    try:
        base = sqlite3.connect('file:%s?mode=ro' % DB.as_posix(), uri=True)
    except sqlite3.Error:
        return usages
    try:
        for titre, voix in base.execute(
                'select title, narrator_voice from books '
                "where narrator_voice is not null and narrator_voice <> ''"):
            fiche = usages.setdefault(cle_voix(voix),
                                      {'narrateur': [], 'roles': []})
            if titre not in fiche['narrateur']:
                fiche['narrateur'].append(titre)
        for titre, perso, voix, repliques in base.execute(
                'select b.title, v.character_name, v.voice_id, v.line_count '
                'from voices v join books b on b.id = v.book_id'):
            fiche = usages.setdefault(cle_voix(voix),
                                      {'narrateur': [], 'roles': []})
            fiche['roles'].append((titre, perso, repliques or 0))
    finally:
        base.close()
    return usages


def resumer_usage(nom, usages):
    """Une phrase en francais qui dit a quoi sert cette voix, chez Laurent."""
    usage = usages.get(nom)
    if not usage or (not usage['narrateur'] and not usage['roles']):
        return {'resume': 'Pas encore utilisee dans tes livres.',
                'priorite': 2}
    morceaux = []
    titres = usage['narrateur']
    if titres:
        if len(titres) == 1:
            morceaux.append('Narrateur de « %s »' % titres[0])
        elif len(titres) == 2:
            morceaux.append('Narrateur de « %s » et de « %s »'
                            % (titres[0], titres[1]))
        else:
            morceaux.append('Narrateur de %d livres' % len(titres))
    roles = usage['roles']
    if roles:
        livres = len(set(role[0] for role in roles))
        repliques = sum(role[2] for role in roles)
        if len(roles) == 1:
            morceaux.append('joue « %s » dans « %s » (%d repliques)'
                            % (roles[0][1], roles[0][0], repliques))
        else:
            morceaux.append('joue %d personnages dans %d livre(s) '
                            '(%d repliques)' % (len(roles), livres, repliques))
    return {'resume': ' ; '.join(morceaux),
            'priorite': 0 if titres else 1}


def noms_prives():
    """Noms courts des voix qui vivent dans `references_privees.csv` (Maya...).

    Sert a SEPARER les corrections : le texte d'une voix privee ne doit pas
    partir dans le CSV versionne (regle du projet : aucun texte d'oeuvre sous
    droits sur le depot).
    """
    prives = set()
    if not CSV_PRIVEES.is_file():
        return prives
    with open(CSV_PRIVEES, encoding='utf-8-sig', newline='') as fichier:
        lignes = list(csv.reader(fichier, delimiter=';'))
    if lignes and lignes[0] and lignes[0][0].strip() == 'fichier':
        lignes = lignes[1:]
    for ligne in lignes:
        if ligne and ligne[0].strip():
            prives.add(nom_court(ligne[0].strip()))
    return prives


def _lire_un_fichier_corrections(chemin):
    """{nom: {'texte':..., 'remarque':..., 'le':...}} pour UN fichier.

    DEUX FORMES DU FICHIER SONT ACCEPTEES : l'ancienne (sans la case remarque,
    ecrite avant le 03/10/2026) et la nouvelle. C'est l'EN-TETE qui tranche --
    sans cela, les lignes deja notees seraient relues de travers, et « quand »
    se retrouverait range dans la remarque.
    """
    donnees = {}
    if not chemin.is_file():
        return donnees
    with open(chemin, encoding='utf-8', newline='') as fichier:
        lignes = list(csv.reader(fichier, delimiter=';'))
    if not lignes:
        return donnees
    entete = [mot.strip().lower() for mot in lignes[0]]
    avec_remarque = 'remarque' in entete
    for ligne in lignes[1:]:
        if len(ligne) < 2 or not ligne[0].strip():
            continue
        donnees[ligne[0].strip()] = {
            'texte': ligne[1],
            'remarque': ligne[2].strip()
                        if (avec_remarque and len(ligne) > 2) else '',
            'le': ligne[3].strip() if (avec_remarque and len(ligne) > 3)
                  else (ligne[2].strip() if len(ligne) > 2 else ''),
        }
    return donnees


def lire_corrections():
    """Les corrections des DEUX fichiers : public (versionne) + prive (Maya)."""
    donnees = {}
    for chemin in (CSV_CORRECTIONS, CSV_CORRECTIONS_PRIVEES):
        donnees.update(_lire_un_fichier_corrections(chemin))
    return donnees


def ecrire_corrections(donnees):
    """Ecrit le fichier PUBLIC et le fichier PRIVE (separation des textes).

    POURQUOI DEUX FICHIERS (19/10/2026) : le CSV des corrections est versionne.
    Depuis que l'outil lit aussi les voix privees, Maya y est apparue avec le
    texte d'un livre du commerce -- interdit sur le depot. On ecrit donc :
      - `_corrections_oreille.csv` : les voix PUBLIQUES seulement ;
      - `_corrections_oreille_privees.csv` : les voix de references_privees.csv
        (Maya), fichier ignore par Git.

    `csv.writer` protege les textes qui contiennent un point-virgule : sans lui,
    une seule virgule de trop casserait la ligne -- et ce fichier est la SEULE
    copie du travail d'ecoute de Laurent.
    """
    prives = noms_prives()
    for chemin, public in ((CSV_CORRECTIONS, True),
                           (CSV_CORRECTIONS_PRIVEES, False)):
        with open(chemin, 'w', encoding='utf-8', newline='') as fichier:
            graveur = csv.writer(fichier, delimiter=';')
            graveur.writerow(['nom', 'texte_entendu', 'remarque', 'le'])
            for cle in sorted(donnees):
                if public and cle in prives:
                    continue
                if not public and cle not in prives:
                    continue
                fiche = donnees[cle]
                graveur.writerow([cle, fiche['texte'],
                                  fiche.get('remarque', ''), fiche['le']])


def contenu_corrections():
    """Le CSV FUSIONNE (public + prive) pour le telechargement.

    Le fichier public ne contient pas Maya ; le prive est ignore par Git. Pour
    que Laurent telecharge TOUT son travail d'un coup, on fusionne les deux au
    moment de l'envoi -- sans jamais ecrire le prive dans le public.
    """
    tampon = io.StringIO()
    graveur = csv.writer(tampon, delimiter=';')
    graveur.writerow(['nom', 'texte_entendu', 'remarque', 'le'])
    donnees = lire_corrections()
    for cle in sorted(donnees):
        fiche = donnees[cle]
        graveur.writerow([cle, fiche['texte'],
                          fiche.get('remarque', ''), fiche['le']])
    return tampon.getvalue().encode('utf-8')


def lire_etat():
    if not FICHIER_ETAT.is_file():
        return {}
    try:
        return json.loads(FICHIER_ETAT.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def construire_donnees():
    """Tout ce dont la page a besoin, en une seule fois."""
    usages = lire_usages()
    corrections = lire_corrections()
    voix = []
    for item in lire_references():
        resume = resumer_usage(item['nom'], usages)
        item['resume'] = resume['resume']
        item['priorite'] = resume['priorite']
        item['corrigee'] = item['nom'] in corrections
        voix.append(item)
    # Les neuf voix signalees le 19/10/2026 d'abord (Laurent doit les trouver
    # tout de suite), puis les narrateurs de ses livres (c'est la que le defaut
    # s'entend), puis le reste.
    voix.sort(key=lambda v: (0 if v['signalee'] else 1, v['priorite'],
                             v['nom'].lower()))
    return {
        'voix': voix,
        'corrections': {nom: {'texte': fiche['texte'],
                              'remarque': fiche.get('remarque', '')}
                        for nom, fiche in corrections.items()},
        'faites': len(corrections),
        'signalees': sum(1 for v in voix if v['signalee']),
        'remarquees': sum(1 for fiche in corrections.values()
                          if fiche.get('remarque')),
        'derniere': lire_etat().get('derniere', ''),
    }


class Serveur(BaseHTTPRequestHandler):
    """Le petit serveur local qui sert la page, l'audio et les corrections."""

    page = b''
    moteur = None

    def log_message(self, *arguments):
        """Aucun bruit dans la console : Laurent lit ce qu'on y ecrit."""

    def _repondre(self, code, contenu, genre='text/html; charset=utf-8',
                  entete=None):
        self.send_response(code)
        self.send_header('Content-Type', genre)
        self.send_header('Content-Length', str(len(contenu)))
        if entete:
            self.send_header(entete[0], entete[1])
        self.end_headers()
        self.wfile.write(contenu)

    def _json(self, donnees, code=200):
        self._repondre(code,
                       json.dumps(donnees, ensure_ascii=False).encode('utf-8'),
                       'application/json; charset=utf-8')

    def do_GET(self):
        adresse = urllib.parse.urlparse(self.path)
        if adresse.path == '/':
            self._repondre(200, self.page)
        elif adresse.path == '/donnees.json':
            self._json(construire_donnees())
        elif adresse.path == '/audio':
            parametres = urllib.parse.parse_qs(adresse.query)
            self._servir_audio((parametres.get('nom') or [''])[0])
        elif adresse.path == '/corrections.csv':
            self._repondre(200, contenu_corrections(), 'text/csv; charset=utf-8',
                           ('Content-Disposition',
                            'attachment; filename=_corrections_oreille.csv'))
        else:
            self._repondre(404, 'pas trouve'.encode('utf-8'),
                           'text/plain; charset=utf-8')

    def _servir_audio(self, nom):
        """Le fichier de reference. On n'accepte QU'UN nom de fichier simple."""
        if not nom or Path(nom).name != nom or '..' in nom:
            self._repondre(400, 'nom de fichier invalide'.encode('utf-8'),
                           'text/plain; charset=utf-8')
            return
        fichier = DOSSIER_VOIX / nom
        if not fichier.is_file():
            self._repondre(404, 'audio introuvable'.encode('utf-8'),
                           'text/plain; charset=utf-8')
            return
        self._repondre(200, fichier.read_bytes(), 'audio/wav')

    def do_POST(self):
        adresse = urllib.parse.urlparse(self.path)
        if adresse.path == '/arret':
            self._json({'ok': True})
            print('')
            print('ARRET demande depuis la page.')
            if self.moteur is not None:
                self.moteur.shutdown()
            return
        if adresse.path != '/enregistrer':
            self._repondre(404, 'pas trouve'.encode('utf-8'),
                           'text/plain; charset=utf-8')
            return
        try:
            taille = int(self.headers.get('Content-Length') or 0)
            demande = json.loads(self.rfile.read(taille).decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            self._json({'ok': False, 'erreur': 'demande illisible'}, 400)
            return
        nom = str(demande.get('nom') or '').strip()
        texte = str(demande.get('texte') or '').strip()
        remarque = str(demande.get('remarque') or '').strip()
        if not nom or not texte:
            self._json({'ok': False, 'erreur': 'nom ou texte vide'}, 400)
            return
        corrections = lire_corrections()
        corrections[nom] = {'texte': texte,
                            'remarque': remarque,
                            'le': time.strftime('%d/%m/%Y %H:%M')}
        ecrire_corrections(corrections)
        etat = lire_etat()
        etat['derniere'] = nom
        FICHIER_ETAT.write_text(json.dumps(etat, ensure_ascii=False),
                                encoding='utf-8')
        print('  enregistre : %-34s (%d caracteres%s)'
              % (nom[:34], len(texte),
                 ', remarque' if remarque else ''))
        self._json({'ok': True, 'faites': len(corrections)})


class Moteur(ThreadingHTTPServer):
    """Le serveur de la page.

    `allow_reuse_address = False` -- PIEGE PAYE LE 03/10/2026 : Python active
    SO_REUSEADDR par defaut, et sous Windows cela permet a DEUX fenetres
    d'ecouter le MEME port EN MEME TEMPS. Ce soir-la, Laurent avait l'outil
    ouvert et un second essai tournait : la page et les donnees venaient tantot
    de l'ancienne version, tantot de la nouvelle, et il etait impossible de
    savoir qui repondait. En refusant la reutilisation, la deuxieme fenetre
    s'arrete net et le dit clairement -- c'est le garde-fou de `main()`.
    """

    allow_reuse_address = False
    daemon_threads = True


PAGE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corriger le texte des voix - NIMM ePub</title>
<style>
:root{--bleu:#1d4ed8;--gris:#5b6472;--fond:#f4f6fa;--carte:#ffffff;--bord:#dde3ec}
*{box-sizing:border-box}
body{margin:0;font-family:"Segoe UI",Roboto,Arial,sans-serif;background:var(--fond);color:#1b2333}
header{background:#12203a;color:#fff;padding:14px 20px}
header h1{margin:0 0 5px;font-size:19px}
header p{margin:0;font-size:13px;color:#c3cddf;max-width:1080px;line-height:1.45}
header strong{color:#fff}
#barre{display:flex;gap:16px;align-items:center;margin-top:11px;flex-wrap:wrap;font-size:13px}
#compteur{font-size:16px;font-weight:700}
button{font-family:inherit;font-size:13px;padding:7px 12px;border-radius:7px;border:1px solid var(--bord);background:#fff;cursor:pointer}
button:hover{border-color:var(--bleu)}
button.principal{background:var(--bleu);color:#fff;border-color:var(--bleu);font-weight:600}
button.danger{color:#a11;border-color:#e6c0c0}
button:disabled{opacity:.45;cursor:default}
button.filtre-actif{background:var(--bleu);color:#fff;border-color:var(--bleu);font-weight:600}
#lot{display:block;width:calc(100% - 24px);margin:8px 12px 2px;text-align:left}
#liste li .badge{display:inline-block;background:#d92b2b;color:#fff;border-radius:4px;padding:0 5px;font-size:10.5px;font-weight:700;margin-left:6px;vertical-align:1px}
main{display:grid;grid-template-columns:320px 1fr;gap:16px;padding:16px 20px 40px;align-items:start}
aside{background:var(--carte);border:1px solid var(--bord);border-radius:10px;overflow:hidden}
#recherche{width:100%;border:0;border-bottom:1px solid var(--bord);padding:11px 12px;font-size:14px;font-family:inherit}
#liste{list-style:none;margin:0;padding:0;max-height:68vh;overflow:auto}
#liste li{padding:8px 12px;border-bottom:1px solid #f0f3f8;cursor:pointer;font-size:13px}
#liste li:hover{background:#eef3ff}
#liste li.actif{background:#dbe6ff;border-left:3px solid var(--bleu)}
#liste li .nom{font-weight:600}
#liste li .petit{color:var(--gris);font-size:11.5px;margin-top:2px}
#liste li.faite .nom{color:#1a7f37}
#liste li.faite .nom::after{content:"  (notee)"}
#liste li.areparer .nom::after{content:"  (A REPARER)";color:#a11;font-weight:700}
section{background:var(--carte);border:1px solid var(--bord);border-radius:10px;padding:16px 18px}
h2{margin:0 0 2px;font-size:18px}
#usage{color:var(--gris);font-size:13px;margin:0 0 12px}
#forme{width:100%;height:70px;display:block;border:1px solid var(--bord);border-radius:8px;background:#fbfcfe;cursor:pointer}
audio{width:100%;margin:10px 0}
.rangee{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px}
.etiq{font-size:12px;color:var(--gris);text-transform:uppercase;letter-spacing:.4px;margin:12px 0 5px}
#ecoute{font-size:12px;color:var(--gris);line-height:1.5;margin:0 0 4px}
textarea{width:100%;min-height:150px;font-family:inherit;font-size:15px;line-height:1.5;padding:11px 12px;border:1px solid var(--bord);border-radius:8px;resize:vertical}
textarea:focus{outline:2px solid var(--bleu);border-color:var(--bleu)}
#message{font-size:13px;margin-left:10px;color:#1a7f37;font-weight:600}
#message.erreur{color:#a11}
.petit{color:var(--gris);font-size:12px}
.aide{font-size:12.5px;color:var(--gris);line-height:1.55;margin-top:14px}
kbd{background:#eef1f6;border:1px solid var(--bord);border-radius:4px;padding:1px 5px;font-size:12px}
</style>
</head>
<body>
<header>
  <h1>&#127911; Corriger le texte des voix, &agrave; l'oreille</h1>
  <p><strong>&Eacute;coute la r&eacute;f&eacute;rence, puis r&eacute;&eacute;cris EXACTEMENT ce que tu entends.</strong>
  Le clonage d'une voix s'appuie sur le texte de sa r&eacute;f&eacute;rence : s'il ne colle pas &agrave; l'audio,
  le moteur fabrique un mot parasite au d&eacute;but des phrases. Ta correction est enregistr&eacute;e
  <strong>tout de suite</strong>, jamais perdue. <strong>Rien n'est appliqu&eacute; aux voix</strong> : remplacer
  le texte de production sera un geste s&eacute;par&eacute;, apr&egrave;s ton accord.</p>
  <div id="barre">
    <span id="compteur">&hellip;</span>
    <button id="telecharger">&#128190; T&eacute;l&eacute;charger mes corrections</button>
    <button id="arreter" class="danger">&#9209; Arr&ecirc;ter l'outil</button>
    <span id="etatOutil" class="petit"></span>
  </div>
</header>
<main>
  <aside>
    <input id="recherche" type="search" placeholder="Chercher un pr&eacute;nom, un fichier, un livre&hellip;">
    <button id="lot">&#11088; Les 9 voix signal&eacute;es</button>
    <p class="petit" style="margin:2px 12px 8px">Th&eacute;odore, &Eacute;douard, Aubin, Maya, Achille, Berthe, C&eacute;cile, Jos&eacute;phine, Maurice.</p>
    <ul id="liste"></ul>
  </aside>
  <section id="fiche">
    <h2 id="nom">&hellip;</h2>
    <p id="usage"></p>
    <canvas id="forme" width="900" height="70"></canvas>
    <audio id="audio" controls preload="auto"></audio>
    <div class="rangee">
      <button id="debut">&#128257; Rejouer le d&eacute;but (2 s)</button>
      <button id="avant">&#9664; 2 s avant</button>
      <button id="apres">&#9654; 2 s apr&egrave;s</button>
      <span id="duree" class="petit"></span>
    </div>
    <p id="ecoute"></p>
    <div class="etiq">Texte actuel de la r&eacute;f&eacute;rence (ce que le moteur lit aujourd'hui)</div>
    <p id="texteActuel"></p>
    <div class="etiq">Ce que TOI tu entends &mdash; r&eacute;&eacute;cris-le exactement</div>
    <textarea id="texte" spellcheck="false" placeholder="&Eacute;cris ici, mot pour mot, ce que dit la voix&hellip;"></textarea>
    <div class="etiq">Remarque (facultatif) &mdash; ce que tu constates, mais qui n'est PAS du texte</div>
    <div class="rangee" style="margin-bottom:5px">
      <button data-etiquette="Parasite au d&eacute;but">+ Parasite au d&eacute;but</button>
      <button data-etiquette="Parasite &agrave; la fin">+ Parasite &agrave; la fin</button>
      <button data-etiquette="Autre probl&egrave;me">+ Autre probl&egrave;me</button>
      <button id="viderRemarque">Vider</button>
    </div>
    <textarea id="remarque" spellcheck="false" style="min-height:62px" placeholder="Ex. : &laquo; petit son parasite &agrave; la toute fin, certainement le d&eacute;but d'un autre mot &raquo;"></textarea>
    <p class="aide" style="margin-top:6px">Cette case <strong>ne part jamais dans la voix</strong> : elle dit seulement ce qu'il y a &agrave; r&eacute;parer. Un son parasite au <strong>d&eacute;but</strong> ou &agrave; la <strong>fin</strong> veut dire que l'audio de r&eacute;f&eacute;rence est coup&eacute; <strong>au milieu d'un mot</strong> &mdash; alors ce n'est pas le texte qu'il faut changer, c'est la <strong>d&eacute;coupe de la r&eacute;f&eacute;rence</strong>.</p>
    <div class="rangee" style="margin-top:10px">
      <button id="enregistrer" class="principal">&#128190; Enregistrer (Ctrl+Entr&eacute;e)</button>
      <button id="suivante">&#9197; Voix suivante</button>
      <button id="remettre">&#8634; Remettre le texte actuel</button>
      <span id="message"></span>
    </div>
    <div class="aide">
      <b>Comment s'en servir.</b> &Eacute;coute le d&eacute;but avec <kbd>Rejouer le d&eacute;but</kbd>, et v&eacute;rifie
      aussi la <b>fin</b> : c'est aux deux bouts que s'entend un son parasite. R&eacute;&eacute;cris ensuite,
      mot pour mot, ce que la voix dit vraiment &mdash; guillemets, ponctuation et majuscules
      compris. Un mot qui manque ou un mot en trop, et le clonage d&eacute;raille.
      <b>Ctrl+Entr&eacute;e</b> enregistre et passe &agrave; la voix suivante ; tu peux fermer la page et
      revenir plus tard, tu reprendras o&ugrave; tu t'es arr&ecirc;t&eacute;. Dans la liste, le <b>trait vert</b>
      marque les voix d&eacute;j&agrave; not&eacute;es, <b>(A REPARER)</b> en rouge celles qui ont une remarque,
      et l'&eacute;toile &#11088; celles qui lisent d&eacute;j&agrave; tes livres.
      <br>Les <b>neuf voix signal&eacute;es le 19/10/2026</b> sont en t&ecirc;te de liste, avec leur
      <b>pr&eacute;nom</b> et un badge <b>&laquo; &agrave; reprendre &raquo;</b> ; le bouton
      <b>Les 9 voix signal&eacute;es</b> les isole.
    </div>
  </section>
</main>
<script>
"use strict";
var donnees = {voix: [], corrections: {}, faites: 0, derniere: ""};
var courante = null;
var filtreLot = false;
var onde = null;
var audio = document.getElementById("audio");
var texte = document.getElementById("texte");
var message = document.getElementById("message");
var liste = document.getElementById("liste");
var remarque = document.getElementById("remarque");

function compterRemarquees() {
  var nombre = 0;
  Object.keys(donnees.corrections).forEach(function (nom) {
    if (donnees.corrections[nom].remarque) { nombre += 1; }
  });
  return nombre;
}

function mettreCompteur() {
  var total = donnees.faites + " voix not\u00e9e(s) sur " + donnees.voix.length;
  var aReparer = compterRemarquees();
  if (aReparer) {
    total += "  \u2014  " + aReparer + " \u00e0 r\u00e9parer";
  }
  document.getElementById("compteur").textContent = total;
}

function afficherListe() {
  var filtre = document.getElementById("recherche").value.trim().toLowerCase();
  liste.innerHTML = "";
  donnees.voix.forEach(function (v) {
    if (filtreLot && !v.signalee) { return; }
    var cherchable = (v.nom + " " + (v.prenom || "") + " " +
                      (v.region || "") + " " + v.resume).toLowerCase();
    if (filtre && cherchable.indexOf(filtre) < 0) {
      return;
    }
    var li = document.createElement("li");
    var fiche = donnees.corrections[v.nom];
    if (fiche) { li.className = "faite"; }
    if (fiche && fiche.remarque) { li.className += " areparer"; }
    if (courante && courante.nom === v.nom) { li.className += " actif"; }
    var nom = document.createElement("div");
    nom.className = "nom";
    var libelle = v.prenom ? (v.prenom + "  (" + v.nom + ")") : v.nom;
    nom.textContent = (v.priorite === 0 ? "\u2B50 " : "") + libelle;
    if (v.signalee) {
      var badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = "\u00e0 reprendre";
      nom.appendChild(badge);
    }
    var petit = document.createElement("div");
    petit.className = "petit";
    petit.textContent = v.resume;
    li.appendChild(nom);
    li.appendChild(petit);
    li.onclick = function () { choisir(v.nom); };
    liste.appendChild(li);
  });
}

function choisir(nom) {
  var choisi = null;
  donnees.voix.forEach(function (v) { if (v.nom === nom) { choisi = v; } });
  if (!choisi) { return; }
  courante = choisi;
  document.getElementById("nom").textContent = choisi.prenom
    ? choisi.prenom + "  (" + choisi.nom + ")" : choisi.nom;
  var details = [];
  if (choisi.region) { details.push(choisi.region); }
  if (choisi.duree) {
    details.push("r\u00e9f\u00e9rence de " + choisi.duree + " s, " + choisi.hauteur);
  }
  document.getElementById("usage").textContent = choisi.resume +
    (details.length ? "   \u2014   " + details.join(" \u00b7 ") : "");
  document.getElementById("texteActuel").textContent = choisi.texte;
  var deja = Object.prototype.hasOwnProperty.call(donnees.corrections, nom);
  texte.value = deja ? donnees.corrections[nom].texte : choisi.texte;
  remarque.value = deja ? (donnees.corrections[nom].remarque || "") : "";
  message.textContent = deja ? "d\u00e9j\u00e0 not\u00e9e" : "";
  message.className = "";
  document.getElementById("duree").textContent = "";
  document.getElementById("ecoute").textContent =
    "Tu peux cliquer dans l'image du son pour te placer pr\u00e9cis\u00e9ment.";
  audio.src = "/audio?nom=" + encodeURIComponent(choisi.fichier);
  audio.load();
  dessiner(choisi.fichier);
  afficherListe();
  mettreCompteur();
  texte.focus();
}

function enregistrer() {
  if (!courante) { return; }
  var contenu = texte.value.trim();
  var note = remarque.value.trim();
  if (!contenu) {
    message.textContent = "le texte est vide : \u00e9cris ce que tu entends";
    message.className = "erreur";
    return;
  }
  var nom = courante.nom;
  fetch("/enregistrer", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({nom: nom, texte: contenu, remarque: note})
  }).then(function (reponse) { return reponse.json(); })
    .then(function (retour) {
      if (!retour.ok) {
        message.textContent = "non enregistr\u00e9 : " + (retour.erreur || "");
        message.className = "erreur";
        return;
      }
      donnees.corrections[nom] = {texte: contenu, remarque: note};
      donnees.faites = retour.faites;
      donnees.derniere = nom;
      courante.corrigee = true;
      message.textContent = "enregistr\u00e9 (" + retour.faites + " au total)";
      message.className = "";
      afficherListe();
      mettreCompteur();
    })
    .catch(function () {
      message.textContent =
        "probl\u00e8me d'enregistrement : v\u00e9rifie que la fen\u00eatre noire est toujours ouverte";
      message.className = "erreur";
    });
}

function suivante() {
  if (!courante) { return; }
  var rang = -1;
  donnees.voix.forEach(function (v, i) {
    if (v.nom === courante.nom) { rang = i; }
  });
  if (rang >= 0 && rang + 1 < donnees.voix.length) {
    choisir(donnees.voix[rang + 1].nom);
  } else {
    message.textContent = "c'\u00e9tait la derni\u00e8re de la liste";
    message.className = "";
  }
}

function enregistrerEtSuivre() {
  enregistrer();
  suivante();
}

function ajouterEtiquette(mot) {
  var contenu = remarque.value.trim();
  if (contenu.indexOf(mot) >= 0) { return; }
  remarque.value = contenu ? (contenu + " ; " + mot) : mot;
}

var boutonsEtiquette = document.querySelectorAll("button[data-etiquette]");
Array.prototype.forEach.call(boutonsEtiquette, function (bouton) {
  bouton.onclick = function () { ajouterEtiquette(bouton.dataset.etiquette); };
});
document.getElementById("viderRemarque").onclick = function () {
  remarque.value = "";
};

function dessiner(fichier) {
  onde = null;
  var toile = document.getElementById("forme");
  var pinceau = toile.getContext("2d");
  pinceau.clearRect(0, 0, toile.width, toile.height);
  fetch("/audio?nom=" + encodeURIComponent(fichier))
    .then(function (reponse) { return reponse.arrayBuffer(); })
    .then(function (tampon) {
      var Contexte = window.AudioContext || window.webkitAudioContext;
      if (!Contexte) { return null; }
      var contexte = new Contexte();
      return contexte.decodeAudioData(tampon).then(function (son) {
        onde = {donnees: son.getChannelData(0), duree: son.duration};
        try { contexte.close(); } catch (e) { }
        return null;
      }).catch(function () {
        try { contexte.close(); } catch (e) { }
        return null;
      });
    })
    .then(function () { tracer(); })
    .catch(function () { tracer(); });
}

function tracer(position) {
  var toile = document.getElementById("forme");
  var pinceau = toile.getContext("2d");
  var largeur = toile.width;
  var hauteur = toile.height;
  var milieu = hauteur / 2;
  pinceau.clearRect(0, 0, largeur, hauteur);
  if (onde) {
    var signal = onde.donnees;
    var pas = Math.max(1, Math.floor(signal.length / largeur));
    pinceau.fillStyle = "#8aa2c8";
    for (var x = 0; x < largeur; x++) {
      var debut = x * pas;
      var crete = 0;
      for (var i = 0; i < pas && debut + i < signal.length; i++) {
        var valeur = Math.abs(signal[debut + i]);
        if (valeur > crete) { crete = valeur; }
      }
      var h = Math.max(1, crete * milieu * 0.95);
      pinceau.fillRect(x, milieu - h, 1, h * 2);
    }
  }
  if (position !== undefined && onde && onde.duree) {
    pinceau.fillStyle = "#d92b2b";
    var curseur = Math.min(largeur - 1,
                          Math.max(0, Math.round(position / onde.duree * largeur)));
    pinceau.fillRect(curseur, 0, 2, hauteur);
  }
}

function animer() {
  if (audio.paused) { return; }
  tracer(audio.currentTime);
  window.requestAnimationFrame(animer);
}

audio.addEventListener("play", function () { window.requestAnimationFrame(animer); });
audio.addEventListener("loadedmetadata", function () {
  document.getElementById("duree").textContent =
    "dur\u00e9e " + audio.duration.toFixed(2) + " s";
});

document.getElementById("forme").onclick = function (evenement) {
  if (!onde || !audio.duration) { return; }
  var cadre = this.getBoundingClientRect();
  var part = (evenement.clientX - cadre.left) / cadre.width;
  audio.currentTime = Math.max(0,
    Math.min(audio.duration - 0.05, part * audio.duration));
  tracer(audio.currentTime);
};
document.getElementById("debut").onclick = function () {
  audio.currentTime = 0;
  audio.play();
  window.setTimeout(function () { audio.pause(); }, 2000);
};
document.getElementById("avant").onclick = function () {
  audio.currentTime = Math.max(0, audio.currentTime - 2);
};
document.getElementById("apres").onclick = function () {
  if (audio.duration) {
    audio.currentTime = Math.min(audio.duration - 0.05, audio.currentTime + 2);
  }
};
document.getElementById("enregistrer").onclick = enregistrerEtSuivre;
document.getElementById("suivante").onclick = enregistrerEtSuivre;
document.getElementById("remettre").onclick = function () {
  if (!courante) { return; }
  texte.value = courante.texte;
  message.textContent = "texte actuel remis";
  message.className = "";
};
document.getElementById("telecharger").onclick = function () {
  window.location = "/corrections.csv";
};
document.getElementById("arreter").onclick = function () {
  document.getElementById("etatOutil").textContent =
    "outil arr\u00eat\u00e9 : tu peux fermer cette page";
  fetch("/arret", {method: "POST"}).catch(function () { });
};
document.getElementById("recherche").addEventListener("input", afficherListe);

var boutonLot = document.getElementById("lot");
boutonLot.onclick = function () {
  filtreLot = !filtreLot;
  boutonLot.className = filtreLot ? "filtre-actif" : "";
  afficherListe();
};

document.addEventListener("keydown", function (evenement) {
  if (evenement.ctrlKey && evenement.key === "Enter") {
    evenement.preventDefault();
    enregistrerEtSuivre();
  }
});

fetch("/donnees.json")
  .then(function (reponse) { return reponse.json(); })
  .then(function (chargees) {
    donnees = chargees;
    mettreCompteur();
    afficherListe();
    var depart = donnees.derniere;
    var existe = false;
    donnees.voix.forEach(function (v) { if (v.nom === depart) { existe = true; } });
    if (!existe) { depart = donnees.voix.length ? donnees.voix[0].nom : ""; }
    if (depart) { choisir(depart); }
    document.getElementById("etatOutil").textContent = donnees.faites
      ? (donnees.faites + " voix d\u00e9j\u00e0 not\u00e9es \u2014 tu reprends o\u00f9 tu t'\u00e9tais arr\u00eat\u00e9")
      : "aucune voix not\u00e9e pour l'instant";
  })
  .catch(function () {
    document.getElementById("etatOutil").textContent =
      "impossible de lire la liste des voix : ferme la page et relance le lanceur";
  });
</script>
</body>
</html>
"""


def main():
    analyseur = argparse.ArgumentParser(
        description='Ecouter chaque voix et reecrire le texte de sa reference.')
    analyseur.add_argument('--port', type=int, default=PORT_DEFAUT,
                           help='port local (defaut %d)' % PORT_DEFAUT)
    analyseur.add_argument('--sans-navigateur', action='store_true',
                           help='ne pas ouvrir le navigateur tout seul')
    analyseur.add_argument('--lot', default='',
                           help='travailler sur un LOT de voix (un dossier) au '
                                'lieu des voix de production')
    analyseur.add_argument('--migrer', action='store_true',
                           help='separe les corrections privees (Maya) du CSV '
                                'versionne, puis quitte')
    options = analyseur.parse_args()

    # `--lot` : on ecoute et on corrige les voix d'un DOSSIER donne (un lot de
    # travail) au lieu des voix de production. Le fichier des corrections vit
    # alors DANS le lot : les deux travaux ne se melangent jamais.
    if options.lot:
        global DOSSIER_VOIX, CSV_REFERENCES, CSV_PRIVEES
        global CSV_CORRECTIONS, CSV_CORRECTIONS_PRIVEES, FICHIER_ETAT
        DOSSIER_VOIX = Path(options.lot).resolve()
        CSV_REFERENCES = DOSSIER_VOIX / 'references.csv'
        CSV_PRIVEES = DOSSIER_VOIX / 'references_privees.csv'
        CSV_CORRECTIONS = DOSSIER_VOIX / '_corrections_oreille.csv'
        CSV_CORRECTIONS_PRIVEES = DOSSIER_VOIX / '_corrections_oreille_privees.csv'
        FICHIER_ETAT = DOSSIER_VOIX / '_corrections_oreille_etat.json'

    if options.migrer:
        # Separation en deux fichiers : le public (versionne) et le prive
        # (Maya, ignore par Git). Copie datee avant, puis relecture.
        for chemin in (CSV_CORRECTIONS, CSV_CORRECTIONS_PRIVEES):
            if chemin.is_file():
                copie = chemin.with_name(
                    chemin.name + '.bak_avant_separation_privee_'
                    + time.strftime('%Y%m%d_%H%M'))
                shutil.copy2(chemin, copie)
                print('Copie datee : %s' % copie.name)
        donnees = lire_corrections()
        ecrire_corrections(donnees)
        prives = noms_prives()
        public = _lire_un_fichier_corrections(CSV_CORRECTIONS)
        prive = _lire_un_fichier_corrections(CSV_CORRECTIONS_PRIVEES)
        fuites = sorted(set(public) & prives)
        print('Public : %d | Prive : %d' % (len(public), len(prive)))
        if fuites:
            print('ECHEC : voix privee(s) encore dans le public : %s'
                  % ', '.join(fuites))
            return 1
        print('TOUT EST OK')
        return 0

    if not CSV_REFERENCES.is_file():
        print('ARRET : le fichier des references est introuvable :')
        print('  %s' % CSV_REFERENCES)
        return 2
    voix = lire_references()
    if not voix:
        print('ARRET : aucune voix dans %s' % CSV_REFERENCES.name)
        return 2

    Serveur.page = PAGE.encode('utf-8')
    try:
        moteur = Moteur(('127.0.0.1', options.port), Serveur)
    except OSError as erreur:
        print('ARRET : le port %d est deja pris.' % options.port)
        print('  (%s)' % erreur)
        print('')
        print("  Le plus souvent, c'est que l'outil est DEJA OUVERT dans une")
        print('  autre fenetre : ferme cette fenetre-la (ou clique sur son')
        print('  bouton "Arreter l\'outil"), puis relance ce fichier.')
        print('')
        print('  (Autre port possible : --port 8100)')
        return 1
    Serveur.moteur = moteur

    adresse = 'http://127.0.0.1:%d/' % options.port
    print('=' * 62)
    print('  NIMM ePub - CORRIGER LE TEXTE DES VOIX A L OREILLE')
    print('=' * 62)
    print('  voix a ecouter  : %d' % len(voix))
    print('  deja notees     : %d' % len(lire_corrections()))
    print('  dossier         : %s' % DOSSIER_VOIX)
    print('  page            : %s' % adresse)
    print('  corrections     : %s (+ %s)'
          % (CSV_CORRECTIONS.name, CSV_CORRECTIONS_PRIVEES.name))
    print('')
    print('  RIEN n est applique aux voix : ce fichier attend ton accord.')
    print('  Pour ARRETER : le bouton de la page, ou Ctrl+C ici.')
    print('')
    if not options.sans_navigateur:
        webbrowser.open(adresse)
    try:
        moteur.serve_forever()
    except KeyboardInterrupt:
        print('')
        print('ARRET par Ctrl+C.')
    finally:
        moteur.server_close()
    print('')
    print('  voix notees au total : %d' % len(lire_corrections()))
    print('  fichier : %s' % CSV_CORRECTIONS)
    print('  prive   : %s' % CSV_CORRECTIONS_PRIVEES)
    return 0


if __name__ == '__main__':
    sys.exit(main())
