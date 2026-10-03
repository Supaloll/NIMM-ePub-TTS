# -*- coding: utf-8 -*-
"""BANC « CHAPITRE » — UN SEUL FICHIER a ecouter, trie par la MACHINE.

POURQUOI (30/09/2026). Laurent a ecoute 36 prises une par une et a dit, tres
justement : « je ne suis pas la pour deboguer un moteur ». Reponse : ce banc
fabrique **UN SEUL WAV** — un vrai chapitre, plusieurs phrases a la suite, avec
les pauses du lecteur — et **la machine fait le tri** :

  1. **preparation** : le chapitre est lu par le MEME lecteur d'EPUB que
     l'application, decoupe en phrases et nettoye par le MEME code que le
     lecteur (`modules/tts.py`, `_clean_text`) ;
  2. **generation** : le moteur Pocket LEGER (6 couches, config
     `french_leger.yaml`) fait lire chaque phrase PLUSIEURS FOIS, a la
     temperature demandee (0,70 par defaut) ;
  3. **tri automatique**, deux criteres mesurables :
       - les TROUS (silence interne de 0,50 s ou plus) — mesure fiable ;
       - la TRANSCRIPTION (Whisper, deja installe) : les mots de plus de trois
         lettres qui apparaissent en trop ou disparaissent par rapport au texte
         attendu — c'est ce qui attrape les repetitions et les mots manges.
     (Les noms propres sont ecartes de la comparaison : Whisper les ecorche.)
  4. **recousu** : la prise retenue passe au resserrage des silences
     (`_banc_resserrage_silences.py`, plafond 0,45 s) ;
  5. **assemblage** : 300 ms entre deux phrases, 800 ms quand une phrase ouvre
     un paragraphe — exactement les pauses du lecteur.

CE QU'ON ECOUTE A LA FIN : un seul fichier, une fois, comme une vraie lecture.
Le rapport dit, pour chaque phrase, la prise retenue et ce qu'elle valait.

CE QU'IL NE FAIT PAS : aucune modification de la base, des voix, du service ou
du lecteur. Le moteur Pocket doit etre ETEINT (le banc refuse sinon).

Usage (le lanceur double-clic fait tout) :
    python _essais/_banc_chapitre_pocket.py
    python _essais/_banc_chapitre_pocket.py --livre 15 --chapitre 4 --phrases 12
    python _essais/_banc_chapitre_pocket.py --tirages 3 --temperature 0.7
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / 'test_voix'))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

from _analyser_raccords_audio import analyser_fichier, lire_wav   # noqa: E402
from _banc_resserrage_silences import resserrer, trouver_silences  # noqa: E402
from _mesurer_debit_pocket import ecrire_wav                      # noqa: E402

BIBLIOTHEQUE = RACINE / 'data' / 'library'
PYTHON_POCKET = RACINE / 'pocket_tts_service' / '.venv' / 'Scripts' / 'python.exe'
GENERATEUR = RACINE / 'test_voix' / '_generer_chapitre_pocket.py'
VOIX_DEFAUT = RACINE / 'pocket_tts_service' / 'voix' / 'Femme001_reference.wav'
REPERE = RACINE / 'test_voix' / '_dernier_chapitre.txt'

SEUIL_TROU_S = 0.50        # un silence interne de cette taille est un trou
PLAFOND_SILENCE_S = 0.45   # ce que le recousu laisse passer, au maximum
PAUSE_PHRASE_MS = 300      # les pauses du lecteur (frontend/app.js)
PAUSE_PARAGRAPHE_MS = 800
PORT_SERVICE_POCKET = 8085


# ============================================================
# 1) LA PREPARATION : le chapitre, decoupe et nettoye comme le lecteur
# ============================================================

def texte_du_chapitre(livre, chapitre):
    """Le texte du chapitre, lu par le MEME lecteur d'EPUB que l'application."""
    import sqlite3
    base = (RACINE / 'data' / 'nimm_epub.db').as_posix()
    connexion = sqlite3.connect('file:%s?mode=ro' % base, uri=True)
    ligne = connexion.execute('SELECT filename FROM books WHERE id = ?',
                              (livre,)).fetchone()
    connexion.close()
    if not ligne:
        raise RuntimeError('livre %s introuvable' % livre)
    from core.epub_parser import get_chapter
    contenu = get_chapter(str(BIBLIOTHEQUE / ligne[0]), chapitre)
    if not contenu:
        raise RuntimeError('chapitre %s introuvable' % chapitre)
    return contenu['text']


def decouper_en_morceaux(phrase, maximum_caracteres):
    """Coupe une phrase trop longue, de preference aux virgules.

    POURQUOI (mesure de l'atelier, memo Pocket de l'atelier NIMM Voix) : au-dela
    d'environ 350 caracteres, ce moteur ACCELERE et AVALE du texte. Le banc du
    30/09 a montre pire : une phrase de 355 caracteres (le tout premier essai du
    banc « chapitre ») est sortie en 22,1 s avec 6 trous. Le lecteur, lui,
    n'envoie rien de plus long que ~500 caracteres -- donc **trop long** pour ce
    moteur : c'est un defaut a corriger cote lecteur, et ce banc coupe a 200
    caracteres (la taille ou le moteur tient) en attendant.

    On coupe aux virgules, points-virgules et deux-points (des pauses naturelles
    de la phrase) ; en dernier recours entre deux mots, jamais dans un mot.
    """
    if len(phrase) <= maximum_caracteres:
        return [phrase]
    morceaux, courant = [], ''
    for bout in re.split(r'(?<=[,;:…])\s+', phrase):
        if len(bout) > maximum_caracteres:
            for mot in bout.split():
                if courant and len(courant) + len(mot) + 1 > maximum_caracteres:
                    morceaux.append(courant)
                    courant = ''
                courant = ((courant + ' ' + mot) if courant else mot).strip()
            continue
        if courant and len(courant) + len(bout) + 1 > maximum_caracteres:
            morceaux.append(courant)
            courant = ''
        courant = ((courant + ' ' + bout) if courant else bout).strip()
    if courant:
        morceaux.append(courant)
    return morceaux


def phrases_du_chapitre(texte, maximum, maximum_caracteres=200):
    """[(phrase, premier_du_paragraphe)] : TOUTES les phrases, dans l'ordre.

    Difference avec le banc de respiration (qui ne gardait que les paragraphes
    de plusieurs phrases) : ici on veut la lecture TELLE QU'ELLE EST, donc on
    garde aussi les paragraphes d'une seule phrase — c'est souvent une replique
    de dialogue, et c'est justement ce qui doit sonner juste.

    Et les phrases trop longues sont DECOUPEES (voir `decouper_en_morceaux`) :
    c'est ce que le lecteur devrait faire pour ce moteur.
    """
    passages = []
    for paragraphe in re.split(r'\n\s*\n', texte or ''):
        paragraphe = ' '.join(paragraphe.split())
        if not paragraphe:
            continue
        phrases = [p.strip() for p in
                   re.split(r'(?<=[.!?…])\s+(?=[«"A-ZÀ-Ý—-])', paragraphe)]
        phrases = [p for p in phrases if len(p) >= 3]
        for rang, phrase in enumerate(phrases):
            morceaux = decouper_en_morceaux(phrase, maximum_caracteres)
            for position, morceau in enumerate(morceaux):
                passages.append((morceau, rang == 0 and position == 0))
                if len(passages) >= maximum:
                    return passages
    return passages


def nettoyer(texte):
    """Le MEME nettoyage que le lecteur (`modules/tts.py`, `_clean_text`)."""
    from modules.tts import _clean_text
    return _clean_text(texte)


# ============================================================
# 2) LE TRI : les trous (fiables) et la transcription (indices)
# ============================================================

def charger_whisper():
    """Le modele de transcription : deja installe et deja en cache."""
    import whisper
    return whisper.load_model('base')


def mots_a_comparer(attendu):
    """(mots a comparer, mots IGNORES) -- les noms propres sont ignores.

    Whisper ecorche les prenoms et les lieux (« Ellen Dockerty » devient
    « Elendokerti ») : compter ces ecarts serait accuser le moteur a tort. On ne
    compare donc que les mots de plus de trois lettres ECRITS EN MINUSCULES, et
    on met de cote ceux qui portent une majuscule dans le texte attendu.
    """
    mots = re.findall(r"[A-Za-zÀ-ÿ']{4,}", attendu.replace('’', "'"))
    a_comparer, ignores = [], set()
    for mot in mots:
        if mot[0].isupper():
            ignores.add(mot.lower())
        else:
            a_comparer.append(mot.lower())
    return a_comparer, ignores


def compter_anomalies(attendu, transcrit):
    """(nombre d'anomalies, mots disparus, mots en trop) -- comparaison d'ENSEMBLES.

    Ce n'est PAS un alignement mot a mot : on regarde si les mots attendus sont
    la, et si des mots non attendus sont apparus (insertions, hesitations,
    repetitions). C'est exactement ce qui a permis de voir « il y a appelle » et
    « l... adresse » dans les prises fautives du 30/09.
    """
    a_comparer, ignores = mots_a_comparer(attendu)
    dits = [m.lower() for m in re.findall(r"[A-Za-zÀ-ÿ']{4,}",
                                          transcrit.replace('’', "'"))]
    ensemble_dits = set(dits)
    ensemble_attendus = set(a_comparer)
    disparus = sorted(m for m in ensemble_attendus if m not in ensemble_dits)
    en_trop = sorted(m for m in set(dits)
                     if m not in ensemble_attendus and m not in ignores)
    return len(disparus) + len(en_trop), disparus, en_trop


def noter_prise(chemin, attendu, modele_whisper):
    """Les deux mesures d'une prise : les trous, et ce que dit la transcription."""
    fiche = analyser_fichier(chemin, 0.15)
    silences = [duree for _, duree in fiche['silences']]
    trous = [duree for duree in silences if duree >= SEUIL_TROU_S]
    transcrit = modele_whisper.transcribe(str(chemin), language='fr',
                                          fp16=False)['text'].strip()
    anomalies, disparus, en_trop = compter_anomalies(attendu, transcrit)
    donnees, frequence = lire_wav(chemin)
    return {'chemin': chemin, 'duree': len(donnees) / float(frequence),
            'trous': len(trous),
            'plus_long': max(silences) if silences else 0.0,
            'anomalies': anomalies, 'disparus': disparus, 'en_trop': en_trop,
            'en_trop_nb': len(en_trop), 'transcrit': transcrit}


def choisir_prise(prises):
    """La meilleure prise. L'ORDRE des criteres compte :

      1. les TROUS mesures (fiable : c'est ce qui s'entend) ;
      2. les mots EN TROP (un mot ajoute = repetition ou hesitation : c'est le
         signe le plus sur de la transcription) ;
      3. le nombre total d'anomalies (mots disparus compris -- mais ceux-la
         peuvent venir d'un rate de Whisper sur un mot rare, d'ou leur poids
         plus faible) ;
      4. la duree la plus proche de ses camarades.
    """
    durees = sorted(prise['duree'] for prise in prises)
    mediane = durees[len(durees) // 2]
    return min(prises, key=lambda prise: (prise['trous'], prise['en_trop_nb'],
                                          prise['anomalies'],
                                          abs(prise['duree'] - mediane)))


def silence(ms, frequence):
    """Un silence de `ms` millisecondes, au format des echantillons du moteur."""
    import numpy as np
    return np.zeros(max(1, int(round(frequence * ms / 1000.0))), dtype='float64')


# ============================================================
# 3) LE MONTAGE : recousu + pauses du lecteur + UN SEUL fichier
# ============================================================

def assembler(prises_retenues):
    """Le chapitre entier : chaque prise recousue, separee comme le fait le lecteur."""
    import numpy as np
    frequence = prises_retenues[0]['frequence']
    morceaux = []
    for index, prise in enumerate(prises_retenues):
        if index > 0:
            pause = (PAUSE_PARAGRAPHE_MS if prise['premier_du_paragraphe']
                     else PAUSE_PHRASE_MS)
            morceaux.append(silence(pause, frequence))
        morceaux.append(prise['donnees'])
    return np.concatenate(morceaux), frequence


def service_allume():
    """Le service Pocket repond-il ? (ses coeurs seraient pris)."""
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/sante'
                                    % PORT_SERVICE_POCKET, timeout=3) as reponse:
            return reponse.status == 200
    except (urllib.error.URLError, OSError):
        return False


def main():
    analyseur = argparse.ArgumentParser(
        description='Fabrique UN SEUL fichier a ecouter : un chapitre lu par le '
                    'Pocket LEGER a 0,70, trie par la machine et recousu.')
    analyseur.add_argument('--livre', type=int, default=15,
                           help='identifiant du livre (defaut : 15, Monte-Cristo T4)')
    analyseur.add_argument('--chapitre', type=int, default=4,
                           help='index du chapitre (defaut : 4, « Le telegraphe »)')
    analyseur.add_argument('--phrases', type=int, default=12,
                           help='nombre de phrases montees (defaut : 12)')
    analyseur.add_argument('--caracteres', type=int, default=200,
                           help='morceaux de 200 caracteres au maximum (defaut : '
                                '200 -- au-dela de ~350 le moteur avale du texte)')
    analyseur.add_argument('--tirages', type=int, default=2,
                           help='tirages par phrase (defaut : 2)')
    analyseur.add_argument('--temperature', type=float, default=0.70,
                           help='temperature du moteur leger (defaut : 0.70)')
    analyseur.add_argument('--voix', default=str(VOIX_DEFAUT),
                           help='extrait de reference du narrateur')
    analyseur.add_argument('--sortie', default='',
                           help='dossier de travail (defaut : un dossier date)')
    options = analyseur.parse_args()

    lignes = []

    def dire(texte):
        print(texte)
        lignes.append(texte)

    if not PYTHON_POCKET.is_file():
        print('ERR : le moteur Pocket n\'est pas installe (venv absent).')
        return 1
    if not GENERATEUR.is_file():
        print('ERR : generateur absent : %s' % GENERATEUR)
        return 1
    if not Path(options.voix).is_file():
        print('ERR : la voix %s n\'existe pas.' % options.voix)
        return 1
    if service_allume():
        print('')
        print('Le service Pocket REPOND sur le port %d : ferme sa fenetre.'
              % PORT_SERVICE_POCKET)
        return 1

    dossier = (Path(options.sortie) if options.sortie
               else RACINE / 'test_voix' / ('banc_chapitre_pocket_%s'
                                            % time.strftime('%Y%m%d_%H%M')))
    dossier.mkdir(parents=True, exist_ok=True)

    dire('')
    dire('=' * 78)
    dire('BANC « CHAPITRE » -- un seul fichier, trie par la machine')
    dire('=' * 78)
    dire('livre %d, chapitre %d | %d phrases | %d tirage(s) | temperature %.2f'
         % (options.livre, options.chapitre, options.phrases, options.tirages,
            options.temperature))
    dire('moteur : Pocket LEGER (6 couches), voix %s' % Path(options.voix).name)
    dire('tri    : trous de %.2f s et plus  +  transcription (Whisper)' % SEUIL_TROU_S)
    dire('montage: recousu a %.2f s, pauses du lecteur (%d / %d ms)'
         % (PLAFOND_SILENCE_S, PAUSE_PHRASE_MS, PAUSE_PARAGRAPHE_MS))

    # --- 1) preparation du texte, comme le lecteur -------------------------
    texte = texte_du_chapitre(options.livre, options.chapitre)
    passages = phrases_du_chapitre(texte, options.phrases * 3, options.caracteres)
    phrases = []
    for brut, premier in passages:
        propre = nettoyer(brut)
        if not propre:
            continue
        phrases.append({'index': len(phrases) + 1, 'texte': propre,
                        'premier_du_paragraphe': premier})
        if len(phrases) >= options.phrases:
            break
    if not phrases:
        dire('ERR : aucune phrase trouvee dans ce chapitre.')
        return 1
    (dossier / 'phrases.json').write_text(
        json.dumps({'livre': options.livre, 'chapitre': options.chapitre,
                    'tirages': options.tirages,
                    'temperature': options.temperature,
                    'voix': str(options.voix), 'phrases': phrases},
                   ensure_ascii=False, indent=1), encoding='utf-8')
    dire('')
    dire('1) %d phrase(s) preparee(s) (texte du chapitre, nettoye comme le lecteur)'
         % len(phrases))

    # --- 2) generation par le moteur, dans son environnement ---------------
    dire('')
    dire('2) generation par le moteur (une a deux minutes)...')
    resultat = subprocess.run([str(PYTHON_POCKET), str(GENERATEUR), str(dossier)],
                              capture_output=True, text=True, encoding='utf-8')
    for ligne in (resultat.stdout or '').splitlines():
        dire('   %s' % ligne)
    if resultat.returncode != 0:
        dire('ERR : la generation a echoue.')
        for ligne in (resultat.stderr or '').splitlines()[-10:]:
            dire('   %s' % ligne)
        return 1

    # --- 3) tri par la machine, recousu, assemblage ------------------------
    dire('')
    dire('3) tri par la machine (trous mesures + transcription)...')
    modele_whisper = charger_whisper()
    retenues = []
    parfaites = 0
    for phrase in phrases:
        prises = []
        for tirage in range(1, options.tirages + 1):
            chemin = dossier / ('brut_%02d_%d.wav' % (phrase['index'], tirage))
            if chemin.exists():
                prises.append(noter_prise(chemin, phrase['texte'], modele_whisper))
        if not prises:
            continue
        choisie = choisir_prise(prises)
        if choisie['trous'] == 0 and choisie['anomalies'] == 0:
            parfaites += 1
        donnees, frequence = lire_wav(choisie['chemin'])
        _, zones = trouver_silences(donnees, frequence)
        recousu = resserrer(donnees, frequence, PLAFOND_SILENCE_S, zones)
        retenues.append({'donnees': recousu, 'frequence': frequence,
                         'premier_du_paragraphe': phrase['premier_du_paragraphe'],
                         'texte': phrase['texte'], 'choisie': choisie,
                         'prises': prises})
        dire('   phrase %02d : %s retenue  (trous %d, en trop %d, anomalies %d, %.1f s)'
             % (phrase['index'], choisie['chemin'].name, choisie['trous'],
                choisie['en_trop_nb'], choisie['anomalies'], choisie['duree']))
        dire('                texte     : %s' % phrase['texte'][:110])
        dire('                transcrit : %s' % choisie['transcrit'][:110])
        if choisie['en_trop']:
            dire('                mots EN TROP (le signe qui compte) : %s'
                 % ', '.join(choisie['en_trop'][:12]))
        for autre in prises:
            if autre is choisie:
                continue
            dire('                ecartee : %s (trous %d, en trop %d, anomalies %d)'
                 % (autre['chemin'].name, autre['trous'], autre['en_trop_nb'],
                    autre['anomalies']))

    if not retenues:
        dire('ERR : aucune prise exploitable.')
        return 1

    donnees_finales, frequence = assembler(retenues)
    nom = ('CHAPITRE_livre%d_chap%d_pocket_leger_T%03d.wav'
           % (options.livre, options.chapitre, round(options.temperature * 100)))
    cible = dossier / nom
    ecrire_wav(cible, donnees_finales, frequence)
    duree_finale = len(donnees_finales) / float(frequence)

    dire('')
    dire('=' * 78)
    dire('LE FICHIER A ECOUTER')
    dire('=' * 78)
    dire('  %s' % cible)
    dire('  duree : %.1f s | %d phrase(s) | %d parfaite(s) apres tri'
         % (duree_finale, len(retenues), parfaites))
    dire('')
    dire('  « Parfaite » veut dire : AUCUN trou mesure et AUCUNE anomalie de')
    dire('  transcription. Pour les autres phrases, le tri a retenu la moins')
    dire('  mauvaise — c\'est dit phrase par phrase plus haut, et le detail')
    dire('  (transcription, mots en trop ou disparus) est dans ce rapport.')
    dire('')
    dire('FIN -- rien n\'a ete modifie (ni base, ni voix, ni service).')

    (dossier / 'RAPPORT.txt').write_text('\n'.join(lignes), encoding='utf-8')
    REPERE.write_text(str(cible), encoding='utf-8')
    print('')
    print('Rapport : %s' % (dossier / 'RAPPORT.txt'))
    return 0


if __name__ == '__main__':
    sys.exit(main())


