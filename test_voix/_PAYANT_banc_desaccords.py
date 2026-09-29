# -*- coding: utf-8 -*-
"""LE BANC DES DESACCORDS -- mesurer un VRAI taux d'erreur sur un VRAI chapitre.

POURQUOI IL EXISTE (reflexion de ChatGPT passee par Laurent, 24/09/2026) : le
passage piege dit **qui est le plus discipline**, pas **quel est le taux d'erreur
reel sur un roman** (23 phrases dont 22 % de cas tordus, c'est un test de
resistance). Le bon conseil etait « plus de donnees » -- mais demander a Laurent
de valider 1 000 phrases a la main n'est pas raisonnable.

D'ou ce banc : on fait analyser **le meme chapitre** par plusieurs moteurs, et on
ne montre **QUE les phrases ou ils ne sont pas d'accord** -- quelques pour cent du
chapitre. Laurent tranche sur ces quelques phrases, et on obtient une **verite
terrain sur du texte reel** (pas sur un piege).

CE QU'IL FAIT :
  1. lit un chapitre du livre (epub + decoupage officiel du projet) et la FICHE
     de personnages telle qu'elle est en base -- pour que chaque moteur travaille
     dans les memes conditions que l'appli ;
  2. interroge chaque moteur demande par le **vrai chemin de l'appli** ;
  3. confronte les attributions et classe les desaccords :
       NET      narration d'un cote, personnage de l'autre (le plus audible)
       PERSONNE deux personnages differents
       NOM      memes racines, noms differents (probablement le meme personnage)
  4. ecrit un rapport lisible, **avec une ligne a remplir** par phrase contestee
     (ce que Laurent entend aujourd'hui y figure aussi, pour comparer).

MODES GRATUITS (aucun appel) :
    python test_voix/_PAYANT_banc_desaccords.py --livre 28 --liste-chapitres
    python test_voix/_PAYANT_banc_desaccords.py --livre 28 --chapitre 14 --verifier

MODE PAYANT :
    python test_voix/_PAYANT_banc_desaccords.py --livre 28 --chapitre 14 --je-paie
    ... --providers gemini,deepseek,local --tours 1

Ce fichier REUTILISE `_PAYANT_comparer_providers_passage.py` (memes cles, meme
aiguillage des moteurs, memes replis pour OpenAI) : on n'ecrit pas deux fois la
meme chose. Lancer depuis la racine du projet.
"""

import argparse
import asyncio
import importlib.util
import json
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from core import epub_parser
from modules import decoupage
from modules import voice_casting as vc

DOSSIER = Path(__file__).resolve().parent
BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

# --- Le socle : l'outil de comparaison, reutilise tel quel -------------------
_spec = importlib.util.spec_from_file_location(
    'socle_providers', DOSSIER / '_PAYANT_comparer_providers_passage.py')
socle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(socle)

PROVIDERS_DEFAUT = 'gemini,deepseek'
PAYSAGE = {}


def _journal(message: str) -> None:
    print('  ' + message)


# ==============================================================
# LIRE LE LIVRE, LE CHAPITRE, LA FICHE
# ==============================================================

def lire_livre(livre: int) -> dict:
    con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    ligne = con.execute(
        "SELECT id, title, filename, CAST(COALESCE(decoupe_dialogue, 0) AS TEXT) "
        "AS dialogue FROM books WHERE id = ?", (livre,)).fetchone()
    if ligne is None:
        con.close()
        raise SystemExit('Livre %s introuvable dans la base.' % livre)
    fiche = [{'nom': r['character_name'], 'genre': r['genre'], 'age': r['age']}
             for r in con.execute(
                 "SELECT character_name, genre, age FROM cast_fiche "
                 "WHERE book_id = ? ORDER BY character_name", (livre,))]
    locuteurs = {(r['chapter_index'], r['sentence_idx']): r['speaker']
                 for r in con.execute(
                     "SELECT chapter_index, sentence_idx, speaker FROM "
                     "speaker_attribution WHERE book_id = ?", (livre,))}
    con.close()
    infos = dict(ligne)
    infos['dialogue'] = int(infos['dialogue'] or 0)
    infos['fiche'] = fiche
    infos['locuteurs'] = locuteurs
    return infos


def lire_chapitres(livre: dict) -> list:
    return epub_parser.get_chapters(str(BIBLIOTHEQUE / livre['filename']))


def regle_du_livre(livre: dict) -> str:
    return decoupage.REGLE_DIALOGUE if livre['dialogue'] else decoupage.REGLE_ACTUELLE


def mode_liste(livre: dict) -> int:
    """Montre les chapitres du livre : index en base, titre, debut du texte."""
    chapitres = lire_chapitres(livre)
    print('=' * 78)
    print(' %s -- %d chapitre(s)' % (livre['title'], len(chapitres)))
    print('=' * 78)
    print('  index  affiche  titre / debut du texte')
    for chapitre in chapitres:
        debut = ' '.join(chapitre['text'].split())[:58]
        print('  %-6d %-8d %s' % (chapitre['index'], chapitre['index'] + 1,
                                  (chapitre['title'] or '')[:34]))
        print('         %s' % debut)
    print('')
    print('  « index » = celui de la base (speaker_attribution) ; c\'est lui qu\'il')
    print('  faut donner a --chapitre. « affiche » = ce que montre le lecteur.')
    return 0



# ==============================================================
# CONFRONTER LES MOTEURS
# ==============================================================

# Mots qui ne disent rien de l'identite (« Le narrateur » / « Le chauffeur »).
MOTS_VIDES = {
    'le', 'la', 'les', 'l', 'un', 'une', 'des', 'du', 'de', 'd', 'au', 'aux',
    'mon', 'ma', 'mes', 'ce', 'cet', 'cette', 'son', 'sa', 'ses', 'leur',
    'leurs',
}


def proches(a: str, b: str) -> bool:
    """Deux noms qui designent PROBABLEMENT le meme personnage.

    « baptistin » / « baptistin_valet », ou « al_stevens » / « al_templeton »
    (meme prenom) : ce n'est pas forcement la meme personne -- c'est justement
    a Laurent de le dire -- mais ce n'est pas un desaccord de PERSONNE.
    """
    if a == b:
        return True
    ja, jb = a.split('_'), b.split('_')
    court, long = sorted((ja, jb), key=len)
    if long[:len(court)] == court:
        return True
    return ja[0] == jb[0] and ja[0] not in MOTS_VIDES


def nature_du_desaccord(decisions: list):
    """decisions = [(moteur, nom_normalise)] -> 'NET', 'PERSONNE', 'NOM' ou None."""
    noms = [nom for _moteur, nom in decisions]
    if len(set(noms)) == 1:
        return None                       # tout le monde d'accord
    narration = [nom for nom in noms if nom == 'narration']
    if narration and len(narration) != len(noms):
        return 'NET'                      # narration d'un cote, personnage de l'autre
    if all(proches(noms[0], autre) for autre in noms[1:]):
        return 'NOM'                      # memes racines : probablement le meme
    return 'PERSONNE'


async def analyser_un_moteur(provider: str, texte: str, fiche: list,
                             regle: str) -> dict:
    """Un chapitre par UN moteur, par le vrai chemin de l'appli."""
    debut = time.time()
    resultat = await vc.analyze_chapter(
        texte, fiche_personnages=list(fiche), provider=provider,
        provider_repli=[], regle=regle)
    return {
        'phrases': {p['id']: p['locuteur'] for p in resultat.get('phrases', [])},
        'refusees': sorted(resultat.get('refusees') or []),
        'duree': round(time.time() - debut, 1),
    }


def confronter(sentences: list, par_moteur: dict, locuteurs_base: dict,
               chapitre: int) -> dict:
    """Le cœur du banc : ou les moteurs ne sont-ils PAS d'accord ?"""
    desaccords = []
    d_accord = 0
    for phrase in sentences:
        sid = phrase['id']
        decisions = [(nom, socle.normaliser(donnees['phrases'].get(sid, '')))
                     for nom, donnees in par_moteur.items()]
        if any(not nom for _m, nom in decisions):
            continue                      # un moteur n'a rien dit de cette phrase
        nature = nature_du_desaccord(decisions)
        if nature is None:
            d_accord += 1
            continue
        desaccords.append({
            'id': sid,
            'texte': phrase['texte'],
            'nature': nature,
            'decisions': decisions,
            'base': locuteurs_base.get((chapitre, sid), '(rien en base)'),
        })
    return {
        'accord': d_accord,
        'desaccords': desaccords,
        'total': len(sentences) - sum(
            1 for p in sentences
            if any(not socle.normaliser(d['phrases'].get(p['id'], ''))
                   for d in par_moteur.values())),
    }



# ==============================================================
# LE RAPPORT
# ==============================================================

LIBELLE_NATURE = {
    'NET': 'LES DESACCORDS NETS (narration d un cote, personnage de l autre)',
    'PERSONNE': 'LES DESACCORDS DE PERSONNE (deux personnages differents)',
    'NOM': 'LES DESACCORDS DE NOM (probablement le meme personnage)',
}


def _accord_entre_moteurs(sentences: list, par_moteur: dict) -> list:
    """Combien de phrases deux moteurs tranchent de la meme facon, deux a deux."""
    noms = list(par_moteur)
    paires = []
    for i, un in enumerate(noms):
        for autre in noms[i + 1:]:
            accord = 0
            total = 0
            for phrase in sentences:
                a = socle.normaliser(par_moteur[un]['phrases'].get(phrase['id'], ''))
                b = socle.normaliser(par_moteur[autre]['phrases'].get(phrase['id'], ''))
                if not a or not b:
                    continue
                total += 1
                accord += 1 if a == b else 0
            paires.append((un, autre, accord, total))
    return paires


def ecrire_rapport(livre: dict, chapitre: int, titre_chapitre: str,
                   sentences: list, resultat: dict, par_moteur: dict,
                   regle: str) -> list:
    lignes = []
    natures = {}
    for desaccord in resultat['desaccords']:
        natures[desaccord['nature']] = natures.get(desaccord['nature'], 0) + 1
    total = resultat['total']

    lignes.append('=' * 78)
    lignes.append(' LE BANC DES DESACCORDS')
    lignes.append(' livre %s -- %s' % (livre['id'], livre['title']))
    lignes.append(' chapitre %s (index en base, affiche %s) -- %s'
                  % (chapitre, chapitre + 1, titre_chapitre))
    lignes.append(' phrases : %d | moteurs : %s | decoupe : regle %s'
                  % (total, ', '.join(socle.PROVIDERS[m]['libelle']
                                      for m in par_moteur), regle))
    lignes.append(' date : %s' % time.strftime('%Y-%m-%d %H:%M'))
    lignes.append('=' * 78)
    lignes.append('')
    lignes.append(' accord complet : %d phrase(s) sur %d (%d %%)'
                  % (resultat['accord'], total,
                     round(100.0 * resultat['accord'] / max(1, total))))
    lignes.append(' a juger : %d desaccord(s) -- %s'
                  % (len(resultat['desaccords']),
                     ', '.join('%d %s' % (nombre, nature)
                               for nature, nombre in sorted(natures.items()))))
    for nom, donnees in par_moteur.items():
        lignes.append('   %-10s %5.1f s%s'
                      % (socle.PROVIDERS[nom]['libelle'], donnees['duree'],
                         '' if not donnees['refusees']
                         else '  REFUS sur %s' % donnees['refusees'][:8]))
    paires = _accord_entre_moteurs(sentences, par_moteur)
    if paires:
        lignes.append('')
        lignes.append(' accord entre moteurs (deux a deux) :')
        for un, autre, accord, tout in paires:
            lignes.append('   %-10s / %-10s : %d/%d (%d %%)'
                          % (socle.PROVIDERS[un]['libelle'][:10],
                             socle.PROVIDERS[autre]['libelle'][:10], accord,
                             tout, round(100.0 * accord / max(1, tout))))

    for nature in ('NET', 'PERSONNE', 'NOM'):
        groupe = [d for d in resultat['desaccords'] if d['nature'] == nature]
        if not groupe:
            continue
        lignes.append('')
        lignes.append('=' * 78)
        lignes.append(' %s -- %d phrase(s)' % (LIBELLE_NATURE[nature], len(groupe)))
        lignes.append('=' * 78)
        for desaccord in groupe:
            lignes.append('')
            lignes.append(' #%-4d %s' % (desaccord['id'],
                                         ' '.join(desaccord['texte'].split())[:68]))
            for moteur, nom in desaccord['decisions']:
                lignes.append('       %-10s : %s'
                              % (socle.PROVIDERS[moteur]['libelle'][:10], nom))
            lignes.append('       en base    : %s' % desaccord['base'])
            lignes.append('       A TOI DE DIRE qui parle vraiment : '
                          '________________________________')
    lignes.append('')
    lignes.append('=' * 78)
    lignes.append(' CE QUE J ATTENDS DE TOI')
    lignes.append('=' * 78)
    lignes.append(' Ecris ta reponse apres les deux-points, sur la ligne'
                  ' « A TOI DE DIRE »,')
    lignes.append(' puis dis-le a Cline : il s en servira comme VERITE TERRAIN'
                  ' (vrai taux')
    lignes.append(' d erreur de chaque moteur, sur un vrai chapitre).')
    lignes.append(' Les desaccords NETS sont les plus audibles : commence par eux.')
    lignes.append('')
    return lignes


def ecrire_fichier(lignes: list, livre: int, chapitre: int) -> Path:
    chemin = DOSSIER / ('banc_desaccords_livre%s_ch%s_%s.txt'
                        % (livre, chapitre, time.strftime('%Y%m%d_%H%M')))
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes) + '\n')
    return chemin



# ==============================================================
# VARIANTE : GEMINI AVEC UN AUTRE NIVEAU DE REFLEXION (24/09/2026)
# ==============================================================
# Question de Laurent : « Gemini est bride, est-ce que ca nous coute en
# qualite ? » -- l'appli envoie `thinkingLevel: "LOW"`, EN DUR. Pour MESURER,
# on ajoute ici une colonne Gemini avec un AUTRE niveau : c'est le meme appel,
# ecrit ici expres, et **le code de l'appli n'est pas modifie**.
#
# Les tokens de REFLEXION sont factures au tarif de SORTIE : c'est pour ca que
# le niveau est bride a l'origine. On les compte donc separement (le journal
# des tokens les enregistre sous un nom de modele distinct).
CLE_REFLEXION = 'gemini-reflexion'
NIVEAU_APPLIQUE = {}


async def _appeler_gemini_avec_reflexion(prompt: str, niveau: str) -> dict:
    """Le meme appel que l'appli, avec le niveau de reflexion en parametre."""
    import httpx

    corps = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'responseMimeType': 'application/json',
            'thinkingConfig': {'thinkingLevel': niveau},
        },
    }
    entetes = {'x-goog-api-key': vc.get_gemini_api_key(),
               'Content-Type': 'application/json'}
    nom_modele = '%s-%s' % (vc.GEMINI_MODEL, niveau)

    async with httpx.AsyncClient(timeout=300.0) as client:
        reponse = await client.post(vc.GEMINI_URL, headers=entetes, json=corps)
        if reponse.status_code == 400:
            # Le niveau demande n'est pas accepte par cette version d'API : on
            # retente SANS thinkingConfig, et on LE DIT (sinon on croirait avoir
            # mesure un niveau qui n'a jamais ete applique).
            print('   ATTENTION : Gemini refuse thinkingLevel=%s (400) -- '
                  'appel SANS reglage de reflexion.' % niveau)
            NIVEAU_APPLIQUE[CLE_REFLEXION] = 'refuse (reglage par defaut)'
            corps['generationConfig'].pop('thinkingConfig', None)
            nom_modele = '%s-DEFAUT' % vc.GEMINI_MODEL
            reponse = await client.post(vc.GEMINI_URL, headers=entetes,
                                        json=corps)
        elif reponse.status_code in (429, 503):
            await asyncio.sleep(15)
            reponse = await client.post(vc.GEMINI_URL, headers=entetes,
                                        json=corps)

    if reponse.status_code != 200:
        raise RuntimeError('Gemini a repondu %s : %s'
                           % (reponse.status_code, reponse.text[:300]))
    donnees = reponse.json()
    motif = (donnees.get('promptFeedback') or {}).get('blockReason')
    if motif:
        raise RuntimeError('Filtre Google (%s) sur ce lot' % motif)

    vc._enregistrer_tokens(donnees.get('usageMetadata'), nom_modele)
    NIVEAU_APPLIQUE.setdefault(CLE_REFLEXION, niveau)
    texte = donnees['candidates'][0]['content']['parts'][0]['text']
    reponse_json = json.loads(texte)
    for phrase in reponse_json.get('phrases', []):
        phrase.pop('texte', None)
    return reponse_json


def ajouter_la_colonne_reflexion(niveau: str) -> None:
    """Ajoute la colonne a la liste des moteurs, et branche son appel."""
    socle.enregistrer_variante(CLE_REFLEXION, 'gemini', vc.GEMINI_MODEL)
    socle.PROVIDERS[CLE_REFLEXION]['libelle'] = 'Gemini %s' % niveau
    socle.PROVIDERS[CLE_REFLEXION]['code'] = niveau[:6].lower()

    origine = vc._call_llm

    async def _aiguillage(prompt, provider='gemini'):
        if provider == CLE_REFLEXION:
            return await _appeler_gemini_avec_reflexion(prompt, niveau)
        return await origine(prompt, provider)

    vc._call_llm = _aiguillage


# ==============================================================
# PROGRAMME PRINCIPAL
# ==============================================================

def analyser_arguments():
    analyseur = argparse.ArgumentParser(
        description="Le banc des desaccords : ou les moteurs ne sont-ils pas "
                    "d'accord, sur un vrai chapitre ?")
    analyseur.add_argument('--livre', type=int, required=True,
                           help='numero du livre (base NIMM)')
    analyseur.add_argument('--chapitre', type=int, default=None,
                           help='index du chapitre EN BASE (voir --liste-chapitres)')
    analyseur.add_argument('--liste-chapitres', action='store_true',
                           dest='liste', help='montre les chapitres (gratuit)')
    analyseur.add_argument('--verifier', action='store_true',
                           help='controle les moteurs et le cout, sans appeler')
    analyseur.add_argument('--je-paie', action='store_true', dest='je_paie',
                           help='obligatoire pour lancer (API facturees)')
    analyseur.add_argument('--providers', default=PROVIDERS_DEFAUT,
                           help='moteurs separes par des virgules (defaut : %s)'
                                % PROVIDERS_DEFAUT)
    analyseur.add_argument('--modele-openai', default=socle.MODELE_OPENAI,
                           dest='modele_openai')
    analyseur.add_argument('--modele-mistral', default='mistral-large-latest',
                           dest='modele_mistral')
    analyseur.add_argument('--reflexion', default=None, metavar='NIVEAU',
                           help="ajoute une colonne Gemini avec ce niveau de "
                                "reflexion (ex. MEDIUM) pour comparer avec le "
                                "reglage bride de l'appli (LOW)")
    return analyseur.parse_args()


async def interroger_les_moteurs(pret: dict, texte: str, fiche: list,
                                 regle: str) -> dict:
    par_moteur = {}
    for provider in pret:
        print('')
        print('--- %s ---' % socle.PROVIDERS[provider]['libelle'])
        sys.stdout.flush()
        par_moteur[provider] = await analyser_un_moteur(
            provider, texte, fiche, regle)
    return par_moteur


def mode_verifier(livre: dict, chapitre: dict, sentences: list, regle: str,
                  pret: dict) -> int:
    print('Livre %s -- %s' % (livre['id'], livre['title']))
    print('Chapitre %s (affiche %s) : %s'
          % (chapitre['index'], chapitre['index'] + 1, chapitre['title']))
    print('%d phrases a analyser (regle %s)' % (len(sentences), regle))
    print('Fiche transmise : %d personnages' % len(livre['fiche']))
    print('')
    print('Moteurs demandes :')
    for nom in pret:
        print('  PRET    %-32s %s'
              % (socle.titre_provider(nom, socle.lire_config()), pret[nom][1]))
    print('')
    print('Cout estime (une passe du seul chapitre) :')
    for nom in pret:
        if nom == CLE_REFLEXION:
            print('  %-22s tarif inconnu : la REFLEXION est facturee en plus, '
                  'comme des tokens de sortie' % socle.PROVIDERS[nom]['libelle'])
        elif nom in vc.PROVIDER_PRICES_USD:
            estimation = vc.estimate_cast_cost([chapitre['text']], nom, regle)
            print('  %-22s %s' % (socle.PROVIDERS[nom]['libelle'],
                                  estimation['cost_display']))
        else:
            print('  %-22s tarif inconnu du projet (tokens releves, cout non)'
                  % socle.PROVIDERS[nom]['libelle'])
    print('')
    print('Pour lancer pour de vrai : ajoute --je-paie')
    return 0



def main() -> int:
    args = analyser_arguments()
    livre = lire_livre(args.livre)

    if args.liste:
        return mode_liste(livre)

    if args.chapitre is None:
        print('Il manque --chapitre. Pour voir la liste : --liste-chapitres')
        return 1

    chapitres = lire_chapitres(livre)
    chapitre = next((c for c in chapitres if c['index'] == args.chapitre), None)
    if chapitre is None:
        print('Chapitre %s introuvable (le livre en compte %d : index 0 a %d). '
              'Utilise --liste-chapitres.'
              % (args.chapitre, len(chapitres), len(chapitres) - 1))
        return 1

    regle = regle_du_livre(livre)
    sentences = [{'id': sid, 'texte': phrase}
                 for sid, phrase in enumerate(decoupage.phrases(
                     chapitre['text'], regle))]
    demandes = socle.lister_demandes(args.providers)
    utilisables = socle.brancher_les_providers(
        socle.lire_cles_api(), socle.lire_config(),
        {'claude': socle.MODELE_CLAUDE, 'mistral': args.modele_mistral},
        demandes, _journal)
    pret = socle.etat_des_cles(demandes, utilisables, socle.lire_config())

    if args.reflexion:
        ajouter_la_colonne_reflexion(args.reflexion)
        if 'gemini' in pret:
            position = list(pret).index('gemini') + 1
            pret = dict(list(pret.items())[:position]
                        + [(CLE_REFLEXION, (None, 'meme cle que Gemini, niveau '
                                                  'de reflexion %s'
                                            % args.reflexion))]
                        + list(pret.items())[position:])
        else:
            pret[CLE_REFLEXION] = (None, 'niveau de reflexion %s'
                                   % args.reflexion)

    if args.verifier:
        return mode_verifier(livre, chapitre, sentences, regle, pret)

    if len(pret) < 2:
        print('Il faut AU MOINS DEUX moteurs utilisables pour parler de '
              'desaccord (un seul moteur ne se contredit pas).')
        return 1

    if not args.je_paie:
        print('=' * 72)
        print("ATTENTION : ce script appelle de VRAIES API d'IA PAYANTES.")
        print('Il analyse un chapitre entier, une fois par moteur.')
        print('')
        print('Pour verifier sans rien payer :')
        print('    python test_voix/%s --livre %s --liste-chapitres'
              % (Path(__file__).name, args.livre))
        print('    python test_voix/%s --livre %s --chapitre %s --verifier'
              % (Path(__file__).name, args.livre, args.chapitre))
        print('=' * 72)
        return 2

    debut = time.time()
    par_moteur = asyncio.run(interroger_les_moteurs(pret, chapitre['text'],
                                                    livre['fiche'], regle))
    resultat = confronter(sentences, par_moteur, livre['locuteurs'],
                          args.chapitre)
    lignes = ecrire_rapport(livre, args.chapitre, chapitre['title'], sentences,
                            resultat, par_moteur, regle)
    print('')
    for ligne in lignes:
        print(ligne)
    chemin = ecrire_fichier(lignes, livre['id'], args.chapitre)
    print('')
    print('Rapport ecrit dans %s' % chemin.name)
    print('Duree totale : %.1f s' % (time.time() - debut))
    return 0


# ==============================================================
# GARDE-FOU : ce script DEPENSE DE L'ARGENT (regle du projet)
# ==============================================================
if __name__ == '__main__':
    sys.exit(main())


