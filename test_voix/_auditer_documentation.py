# -*- coding: utf-8 -*-
"""Audit de la DOCUMENTATION contre le CODE (lecture seule).

POURQUOI CET OUTIL (demande de Laurent, 22/09/2026) : « je voudrais bien que tu
fasses un audit de ARCHITECTURE.md, et des documents, notes, etc. pour les
conformer a ce que le code dit. Que ca reflete reellement l'etat actuel du
code. »

La documentation de NIMM ePub est une CHRONIQUE : elle raconte les sessions, et
une chronique vieillit. Le danger n'est pas le style, c'est la REFERENCE MORTE :
un fichier renomme, une fonction supprimee, une route qui n'existe plus, une
colonne de table qui a change de nom. Exemple vecu, corrige le 22/09/2026 : le
BACKLOG annoncait que `_forcer_beats_en_narration` corrigeait les beats, alors
que la fonction n'est plus appelee depuis le 21/09/2026.

Ce que l'outil VERIFIE (tout ce qui est verifiable mecaniquement) :
  1. les FICHIERS cites dans les documents : existent-ils encore ?
  2. les IDENTIFIANTS de code cites (`VERSION_CACHE`, `showView()`) : existent-ils
     encore dans le code ?
  3. les ROUTES HTTP citees (/api/...) : existent-elles dans main.py ?
  4. les COLONNES de table citees (`books.decoupe_dialogue`) : existent-elles en
     base ?
  5. les TESTS cites : existent-ils ? et tournent-ils dans le lanceur global ?
  6. les DOUBLONS du BACKLOG : un item « a faire » dont le sujet est deja livre.

Ce qu'il ne fait PAS : il ne juge pas le style et il ne reecrit RIEN. C'est un
DIAGNOSTIC, et chaque alerte doit etre LUE dans le document : la lecon du
21/09/2026 est qu'un chiffre ne vaut rien sans la lecture du texte. Certaines
alertes sont LEGITIMES (un document qui raconte l'histoire a le droit de citer
un fichier disparu) ; d'autres sont de vraies derives a corriger.

Usage : python test_voix/_auditer_documentation.py
"""

import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = Path(__file__).resolve().parent
BASE = RACINE / 'data' / 'nimm_epub.db'
MAX_PAR_SECTION = 25 if '--tout' not in sys.argv else 10 ** 6

# Les documents audites. Les copies `*.bak_*` sont volontairement exclues : ce
# sont des sauvegardes datees, elles ont le droit d'etre perimees.
DOCUMENTS = [
    'ARCHITECTURE.md', 'BACKLOG.md', 'README.md', 'CONTRIBUER.md',
    'REGLES_INCISES_a_eprouver.md', 'MEMO_XTTS_v2_pour_Cline.md',
    'MEMO_POCKET_TTS_pour_la_session_NIMM_ePub.md',
    'test_voix/LIRE_MOI.md', 'test_voix/MEMO_pour_NIMM_Voix.md',
    'kyutai_service/LIRE_MOI.md', 'neutts_service/LIRE_MOI.md',
    'pocket_tts_service/LIRE_MOI.md', 'xtts_service/LIRE_MOI.md',
    'kyutai_service/ATTRIBUTION.md', 'neutts_service/ATTRIBUTION.md',
    'pocket_tts_service/ATTRIBUTION.md', 'xtts_service/ATTRIBUTION.md',
]

# Les documents qui decrivent l'ETAT ACTUEL du projet. Les autres (les memos)
# sont des notes datees, ecrites pour une session : une reference perimee y est
# moins grave. Le rapport trie donc les alertes : etat actuel d'abord.
DOCUMENTS_ACTIFS = {
    'ARCHITECTURE.md', 'BACKLOG.md', 'README.md', 'CONTRIBUER.md',
    'test_voix/LIRE_MOI.md', 'kyutai_service/LIRE_MOI.md',
    'neutts_service/LIRE_MOI.md', 'pocket_tts_service/LIRE_MOI.md',
    'xtts_service/LIRE_MOI.md',
}

# Fichiers cites qui vivent AILLEURS (l'atelier NIMM Voix) : leur absence ici
# est normale, elle doit etre expliquee dans le document, pas signalee.
FICHIERS_D_AILLEURS = {
    'scripts/tester_prenoms_kokoro.py', 'TESTER_PRENOMS_KOKORO.cmd',
    'CHERCHER_PRENOMS_DUN_LIVRE.cmd',
}

# Le code ou l'on cherche les identifiants cites par les documents.
MOTIFS_CODE = ['main.py', 'modules/*.py', 'core/*.py', 'test_voix/*.py',
               'frontend/*.js', 'frontend/*.html', 'frontend/*.css',
               '*_service/*.py']

# Dossiers ou l'on accepte qu'un fichier cite par son seul nom se trouve.
DOSSIERS_CONNUS = ('', 'test_voix', 'modules', 'core', 'frontend', 'data',
                   'kyutai_service', 'neutts_service', 'pocket_tts_service',
                   'xtts_service')


def lire(chemin):
    """Le texte d'un fichier, ou une chaine vide s'il n'existe pas."""
    try:
        return chemin.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def documents_audites():
    """[(nom, chemin, texte)] des documents qui existent vraiment."""
    sortie = []
    for nom in DOCUMENTS:
        chemin = RACINE / nom
        if chemin.is_file():
            sortie.append((nom, chemin, lire(chemin)))
    return sortie


def _reference(doc, numero):
    """« ARCHITECTURE.md:123 » ; le « ! » marque un document d'ETAT ACTUEL."""
    return '%s%s:%d' % ('!' if doc in DOCUMENTS_ACTIFS else '', doc, numero)


def _ou_est_le_fichier(nom, net):
    """('existe'|'variante'|'absent', nom_reel) pour un fichier cite.

    Les documents citent parfois un outil d'atelier SANS son souligne initial
    (« test_local_ollama.py » pour `_test_local_ollama.py`) : c'est une alerte
    DOUCE, a ne pas confondre avec un fichier disparu.
    """
    directs = [RACINE / net, RACINE / nom]
    directs += [RACINE / d / nom for d in DOSSIERS_CONNUS]
    if any(c.is_file() for c in directs):
        return 'existe', nom
    for variante in ([nom[1:]] if nom.startswith('_') else ['_' + nom]):
        candidats = [RACINE / variante]
        candidats += [RACINE / d / variante for d in DOSSIERS_CONNUS]
        if any(c.is_file() for c in candidats):
            return 'variante', variante
    return 'absent', nom


def corpus_code():
    """Tout le code du projet en un seul texte (pour chercher un identifiant)."""
    morceaux = []
    for motif in MOTIFS_CODE:
        for fichier in sorted(RACINE.glob(motif)):
            morceaux.append(lire(fichier))
    return '\n'.join(morceaux)


RE_FICHIER_CITE = re.compile(r'`([^`\n]{1,90}?\.(?:py|js|bat|json|md|css|html))`')
RE_BACKTICK = re.compile(r'`([^`\n]{2,70})`')
RE_ROUTE_DOC = re.compile(r'(/api/[A-Za-z0-9_\-{}$/.]*)')
RE_ROUTE_CODE = re.compile(r'@app\.(?:get|post|put|delete|patch)\(\s*[\'"]([^\'"]+)[\'"]')
RE_COLONNE = re.compile(
    r'\b(books|progress|users|voices|cast_fiche|speaker_attribution'
    r'|character_aliases)\.([a-z_]{2,})\b')


def section_fichiers():
    """1. Les fichiers cites dans les documents existent-ils encore ?

    Renvoie (disparus, cites sans leur souligne) : la seconde liste est une
    alerte douce, pas un fichier disparu.
    """
    disparus, variantes = {}, {}
    for doc, _chemin, texte in documents_audites():
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for cite in RE_FICHIER_CITE.findall(ligne):
                net = cite.strip().lstrip('./').replace('\\', '/')
                nom = net.split('/')[-1]
                if net in FICHIERS_D_AILLEURS or nom in FICHIERS_D_AILLEURS:
                    continue
                # Un GLOB, un CHEMIN A TROU ou une COMMANDE ne sont pas des
                # fichiers cites : `resultat_*.json`, `<dossier>/launcher.py`,
                # `python test_voix/script.py`. Les signaler noierait le rapport.
                if any(c in net for c in '*<>"|') or ' ' in net:
                    continue
                etat, reel = _ou_est_le_fichier(nom, net)
                if etat == 'existe':
                    continue
                if etat == 'variante':
                    variantes.setdefault(net, []).append(
                        '%s (le fichier est `%s`)' % (_reference(doc, numero), reel))
                    continue
                disparus.setdefault(net, []).append(_reference(doc, numero))
    return disparus, variantes


def _ressemble_a_un_identifiant(jeton):
    """`VERSION_CACHE`, `_forcer_beats_en_narration`, `showView()`.

    On ne garde que ce qui a une CHANCE d'etre du code : un souligne, une forme
    camelCase, ou des parentheses. C'est ce qui ecarte les mots francais, les
    balises et les sigles (« GET », « TODO »).
    """
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(\(\))?', jeton):
        return None
    nom = jeton[:-2] if jeton.endswith('()') else jeton
    if len(nom) < 4:
        return None
    # « INSTALLER_ », « voix30_ » : un raccourci pour INSTALLER_xxx.bat, pas un
    # identifiant de code.
    if nom.endswith('_'):
        return None
    if '_' not in nom and not re.search(r'[a-z][A-Z]', nom):
        return None
    return nom


def section_identifiants(corpus):
    """2. Les identifiants de code cites existent-ils encore ?"""
    alertes = {}
    for doc, _chemin, texte in documents_audites():
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for jeton in RE_BACKTICK.findall(ligne):
                jeton = jeton.strip()
                if any(c in jeton for c in '. /:\\'):
                    continue
                nom = _ressemble_a_un_identifiant(jeton)
                if nom is None:
                    continue
                # Un identifiant RENOMME ne doit pas passer : d'ou les bornes
                # (?<!\\w) / (?!\\w), qui refusent `VERSION_CACHE` quand le code
                # dit `VERSION_CACHE_AUDIO`.
                if re.search(r'(?<!\w)' + re.escape(nom) + r'(?!\w)', corpus):
                    continue
                alertes.setdefault(nom, []).append(_reference(doc, numero))
    return alertes


def _normaliser_route(route):
    """`/api/books/{id}/search?q=...` -> `/api/books/{}/search`.

    Un identifiant numerique en dur (`/api/bookmarks/16`) est un EXEMPLE de
    document : il devient le meme trou que dans le code.
    """
    net = re.sub(r'\{[^}]*\}', '{}', route.split('?')[0])
    net = re.sub(r'/\d+(?=/|$)', '/{}', net)
    return net.rstrip('/')


def section_routes():
    """3. Les routes HTTP citees existent-elles dans main.py ?"""
    routes_code = {_normaliser_route(r) for r in
                   RE_ROUTE_CODE.findall(lire(RACINE / 'main.py'))}
    alertes = {}
    for doc, _chemin, texte in documents_audites():
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for route in RE_ROUTE_DOC.findall(ligne):
                net = _normaliser_route(route)
                if net in ('/api', ''):
                    continue
                if net in routes_code:
                    continue
                alertes.setdefault(net, []).append(_reference(doc, numero))
    return routes_code, alertes


def section_colonnes():
    """4. Les colonnes de table citees existent-elles en base ?"""
    if not BASE.is_file():
        return None, {}
    conn = sqlite3.connect('file:' + BASE.as_posix() + '?mode=ro', uri=True)
    reelles = {}
    try:
        for (table,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"):
            reelles[table] = {c[1] for c in
                              conn.execute('PRAGMA table_info(%s)' % table)}
    finally:
        conn.close()
    alertes = {}
    for doc, _chemin, texte in documents_audites():
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for table, colonne in RE_COLONNE.findall(ligne):
                if colonne in reelles.get(table, ()):
                    continue
                alertes.setdefault('%s.%s' % (table, colonne),
                                   []).append(_reference(doc, numero))
    return reelles, alertes


def _tests_du_lanceur():
    """Les tests que `lancer_tous_les_tests.py` lance vraiment."""
    return set(re.findall(r'"([A-Za-z0-9_]+\.py)"',
                          lire(DOSSIER / 'lancer_tous_les_tests.py')))


def section_tests():
    """5. Les tests cites existent-ils, et tournent-ils dans le lanceur ?

    Renvoie (disparus, cites sans leur souligne, lances, a lancer a la main).
    """
    lances = _tests_du_lanceur()
    disparus, variantes = {}, {}
    for doc, _chemin, texte in documents_audites():
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for nom in re.findall(
                    r'(?<![A-Za-z0-9_/])(?:test_voix/)?'
                    r'(test_[A-Za-z0-9_]+\.(?:py|js))', ligne):
                etat, reel = _ou_est_le_fichier(nom, nom)
                if etat == 'existe':
                    continue
                if etat == 'variante':
                    variantes.setdefault(nom, []).append(
                        '%s (le fichier est `%s`)' % (_reference(doc, numero), reel))
                    continue
                disparus.setdefault(nom, []).append(_reference(doc, numero))
    existants = {f.name for f in DOSSIER.glob('test_*.py')}
    existants |= {f.name for f in DOSSIER.glob('test_*.js')}
    # Le lanceur prend TOUS les `test_*.js` (il les balaie par motif) et les
    # tests Python qu'il cite nommement. Les compter de la meme facon, sinon le
    # rapport annonce 57 tests « a lancer a la main » au lieu de 35.
    automatiques = {n for n in existants if n.endswith('.js') or n in lances}
    a_la_main = sorted(existants - automatiques)
    return disparus, variantes, sorted(automatiques), a_la_main


# Pour rapprocher les titres d'items du BACKLOG malgre les accents et le balisage.
ACCENTS = str.maketrans('àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ',
                        'aaaeeeeiioouuucAAAEEEEIIOOUUUC')
MOTS_VIDES = {
    'livre', 'livres', 'depuis', 'cette', 'apres', 'faire', 'etre', 'leurs',
    'toutes', 'nouveau', 'nouvelle', 'avec', 'dans', 'pour', 'plus', 'entre',
    'partie', 'meme', 'aussi', 'comme', 'alors', 'selon', 'quoi', 'tout',
    'tous', 'elle', 'elles', 'cela', 'celui', 'celle', 'sous', 'vers', 'deja',
    'encore', 'jamais', 'toujours', 'souvent', 'peut', 'sont', 'sera', 'trois',
}


def _mots_cles(titre):
    """Les mots qui portent le SUJET d'un titre d'item (accent et casse ecartes)."""
    net = re.sub(r'[*`_()\[\]«»"\',:;.!?—–-]', ' ', titre)
    net = net.translate(ACCENTS).lower()
    return {mot for mot in re.findall(r'[a-z0-9]{5,}', net)
            if mot not in MOTS_VIDES}


def _blocs_items(texte):
    """[{'ligne', 'fait', 'titre', 'corps'}] : les items du BACKLOG, avec leur corps.

    Comparer les TITRES seulement rate les vrais doublons : mesure du
    22/09/2026, l'item ouvert « Cache audio : statistiques et purge » et l'item
    livre « Bouton vider le cache audio » n'ont que DEUX mots communs dans leur
    titre, mais trois dans leur CORPS — et c'est celui-la qui tranche.
    """
    blocs, courant = [], None
    for numero, ligne in enumerate(texte.splitlines(), 1):
        if ligne.startswith('- [ ]') or ligne.startswith('- [x]'):
            if courant:
                blocs.append(courant)
            courant = {'ligne': numero, 'fait': ligne.startswith('- [x]'),
                       'titre': ligne[6:].strip(), 'corps': []}
        elif ligne.startswith('#'):
            if courant:
                blocs.append(courant)
            courant = None
        elif courant is not None:
            courant['corps'].append(ligne)
    if courant:
        blocs.append(courant)
    return blocs


def section_doublons_backlog():
    """6. Un item « a faire » dont le sujet est deja livre.

    LIMITE CONNUE, écrite pour qu'on ne s'y fie pas trop : la comparaison porte
    sur les **titres**. Un item dont le sujet est livré **sous un autre nom** ne
    sera pas vu — cas vécu du 22/09/2026 : « Cache audio : statistiques et
    purge » est resté ouvert des mois alors que le bouton et les deux routes
    étaient livrés (fermé à la main, en lisant la priorité 3). Un essai de
    comparaison avec le CORPS des items livrés a été fait le même jour, puis
    écarté : 24 alertes, en grande majorité fausses (mots génériques communs
    comme « moteur », « chapitre », « Laurent »). Mieux vaut peu d'alertes
    justes, et relire les sections.
    """
    blocs = _blocs_items(lire(RACINE / 'BACKLOG.md'))
    ouverts = [b for b in blocs if not b['fait']]
    livres = [b for b in blocs if b['fait']]
    mots_livres = [(b, _mots_cles(b['titre'])) for b in livres]
    signales = []
    for bloc in ouverts:
        titre = bloc['titre']
        # Cas evident : un item encore ouvert qui porte deja le mot « LIVRE ».
        if re.search(r'LIVR[EÉ]', titre):
            signales.append((bloc, 'le titre annonce deja une livraison'))
            continue
        mots = _mots_cles(titre)
        if len(mots) < 3:
            continue
        for livre, mots_livre in mots_livres:
            communs = mots & mots_livre
            if len(communs) >= 3 and len(communs) >= 0.6 * len(mots):
                signales.append((
                    bloc,
                    'meme sujet que l item livre ligne %d (%s) -- mots communs :'
                    ' %s' % (livre['ligne'], livre['titre'][:44],
                             ', '.join(sorted(communs)))))
                break
    return len(ouverts), len(livres), signales


def _afficher_section(numero, titre, alertes, complement=''):
    print('')
    print('-' * 74)
    print('%s. %s' % (numero, titre))
    print('-' * 74)
    if complement:
        print('  ' + complement)
    if not alertes:
        print('  RIEN A SIGNALER')
        return 0

    # Les references qui vivent dans un document d'ETAT ACTUEL passent d'abord :
    # c'est la que la derive coute le plus cher.
    def priorite(cle):
        return (0 if any(r.startswith('!') for r in alertes[cle]) else 1, cle)

    for i, cle in enumerate(sorted(alertes, key=priorite)):
        if i >= MAX_PAR_SECTION:
            print('  ... et %d autre(s)' % (len(alertes) - MAX_PAR_SECTION))
            break
        refs = sorted(alertes[cle], key=lambda r: (0 if r.startswith('!') else 1, r))
        print('  %-46s %s' % (cle[:46], ', '.join(refs[:3])))
    return len(alertes)


def main():
    print('=' * 74)
    print(' AUDIT DE LA DOCUMENTATION contre le CODE (lecture seule)')
    print('=' * 74)
    docs = documents_audites()
    print('%d documents : %s' % (len(docs), ', '.join(d[0] for d in docs)))
    print('Le « ! » devant une reference marque un document d ETAT ACTUEL.')
    print('Chaque alerte est a LIRE dans le document : certaines sont legitimes')
    print('(l histoire d un fichier disparu), d autres sont de vraies derives.')
    total = 0

    disparus, variantes = section_fichiers()
    total += _afficher_section('1', 'FICHIERS cites qui n existent plus', disparus)
    total += _afficher_section(
        '1 bis', 'FICHIERS cites sans leur souligne initial (alerte douce)',
        variantes)
    total += _afficher_section('2', 'IDENTIFIANTS de code cites, introuvables',
                               section_identifiants(corpus_code()))
    routes, alertes = section_routes()
    total += _afficher_section('3', 'ROUTES HTTP citees, absentes de main.py',
                               alertes, '%d routes declarees dans main.py'
                               % len(routes))
    tables, alertes = section_colonnes()
    total += _afficher_section('4', 'COLONNES de table citees, absentes de la base',
                               alertes, '%d tables en base'
                               % (len(tables) if tables else 0))
    disparus, variantes, automatiques, a_la_main = section_tests()
    total += _afficher_section(
        '5', 'TESTS cites qui n existent plus', disparus,
        '%d tests au lanceur global, %d a lancer a la main'
        % (len(automatiques), len(a_la_main)))
    total += _afficher_section(
        '5 bis', 'TESTS cites sans leur souligne initial (alerte douce)', variantes)
    ouverts, livres, doublons = section_doublons_backlog()
    print('')
    print('-' * 74)
    print('6. DOUBLONS du BACKLOG (item ouvert dont le sujet est deja livre)')
    print('-' * 74)
    print('  %d items ouverts, %d items livres' % (ouverts, livres))
    if not doublons:
        print('  RIEN A SIGNALER')
    for bloc, raison in doublons[:MAX_PAR_SECTION]:
        print('  ligne %-6d %s' % (bloc['ligne'], bloc['titre'][:58]))
        print('  %-13s %s' % ('', raison))
    total += len(doublons)

    print('')
    print('=' * 74)
    print(' %d alerte(s) a lire -- aucune ecriture, aucun fichier modifie' % total)
    print('=' * 74)
    return 0


if __name__ == '__main__':
    sys.exit(main())

