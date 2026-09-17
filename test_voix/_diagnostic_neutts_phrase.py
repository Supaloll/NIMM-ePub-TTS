# -*- coding: utf-8 -*-
"""Ou le moteur NeuTTS va-t-il découper ton texte ? (lecture seule)

QUESTION A LAQUELLE IL REPOND (échange du 17/09/2026, constat de Laurent :
« la lecture est trop aléatoire en qualité ») : le service NeuTTS ne lit pas la
phrase d'un bloc. Il la REDECOUPE en morceaux, parce que la fenetre du moteur
(~30 s, reference comprise) l'y oblige, puis il RECOLLE les morceaux sans
silence. Chaque morceau est une prise independante : sa propre attaque, sa
propre fin, son propre debit. Une phrase lue en 3 morceaux s'entend donc comme
3 prises collees -- c'est la cause STRUCTURELLE de l'irregularite ressentie
(aucun hasard la-dedans : la graine du moteur est fixe).

Cet outil dit, AVANT toute ecoute :
    - combien de morceaux chaque phrase du chapitre demande ;
    - quelle est la limite de chaque voix (elle depend de la duree de son
      extrait de reference : une voix dont l'extrait est long lit moins) ;
    - quelles phrases sont COURTES (peu de contexte pour le modele) ;
    - quelles phrases portent des guillemets ou des tirets de dialogue -- les
      signes que le service XTTS retire avant l'envoi, et que NeuTTS recoit
      encore BRUTS.

Il ne modifie rien et n'allume aucun moteur : tout se calcule sur disque.

Usage :
    python test_voix/_diagnostic_neutts_phrase.py --livre 34 --chapitre 0
    python test_voix/_diagnostic_neutts_phrase.py --livre 34 --voix 12205_11650_000004-0002
    python test_voix/_diagnostic_neutts_phrase.py --texte "— Non."
"""

import argparse
import importlib.util
import re
import sqlite3
import sys
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
SERVICE = RACINE / 'neutts_service' / 'servir_neutts.py'

# Les memes seuils que le lecteur (frontend/app.js).
SPLIT_SENTENCE_CHARS = 500
SPLIT_SEGMENT_CHARS = 450
# Une phrase plus courte que cela laisse tres peu de contexte au modele : c'est
# la ou les defauts de diction se concentrent (constat XTTS du 16/09/2026).
PHRASE_COURTE = 15


def charger_service():
    """Le module du service NeuTTS, pour lire SES constantes (jamais recopiees)."""
    spec = importlib.util.spec_from_file_location('servir_neutts', SERVICE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def duree_wav(chemin):
    """Duree d'un WAV en secondes (0 si illisible)."""
    try:
        with wave.open(str(chemin), 'rb') as fichier:
            return fichier.getnframes() / float(fichier.getframerate())
    except Exception:
        return 0.0


def limites_par_voix(service):
    """{identifiant de voix: (duree de l'extrait, limite en caracteres)}."""
    limites = {}
    for identifiant, valeurs in service._repertorier_references().items():
        # `_repertorier_references` renvoie (chemin, texte, duree) selon la
        # version : on prend la duree quand elle est la, sinon on la mesure.
        duree = valeurs[2] if len(valeurs) > 2 and valeurs[2] else duree_wav(valeurs[0])
        restant = service.FENETRE_TOTALE_S - duree - service.MARGE_FENETRE_S
        limite = max(service.CARACTERES_MINIMUM,
                     min(service.MAX_CARACTERES,
                         int(restant * service.CARACTERES_PAR_SECONDE)))
        limites[identifiant] = (duree, limite)
    return limites


def phrases_du_texte(texte):
    """Les unites de synthese du LECTEUR : phrases, puis sous-segments.

    Meme regle que frontend/app.js : coupure apres . ! ? … », phrases de plus
    de 3 caracteres, et sous-segments au-dela de 500 caracteres (coupes aux
    virgules), pour ne jamais couper au milieu d'un texte.
    """
    unites = []
    for paragraphe in re.split(r'\n\n+', texte):
        paragraphe = paragraphe.strip()
        if len(paragraphe) <= 5:
            continue
        for phrase in re.split(r'(?<=[.!?\u2026\u00bb])\s+', paragraphe):
            phrase = phrase.strip()
            if len(phrase) <= 3:
                continue
            unites.extend(_sous_segments(phrase))
    return unites


def _sous_segments(phrase):
    if len(phrase) <= SPLIT_SENTENCE_CHARS:
        return [phrase]
    sortie = []
    courant = ''
    for morceau in re.split(r'(?<=[,;:])\s+', phrase):
        if courant and len(courant) + len(morceau) + 1 > SPLIT_SEGMENT_CHARS:
            sortie.append(courant)
            courant = ''
        if len(morceau) > SPLIT_SEGMENT_CHARS:
            for debut in range(0, len(morceau), SPLIT_SEGMENT_CHARS):
                sortie.append(morceau[debut:debut + SPLIT_SEGMENT_CHARS])
            courant = ''
        else:
            courant = (courant + ' ' + morceau) if courant else morceau
    if courant:
        sortie.append(courant)
    return sortie


def morceaux_prevus(texte, limite, service):
    """Combien de morceaux le service decoupera (sa propre fonction)."""
    plan = service.plan_de_lecture(texte, limite)
    return sum(len(morceaux) for _phrase, morceaux in plan)


def nettoyage_xtts(texte):
    """Ce que XTTS fait et que NeuTTS ne fait PAS (voir servir_xtts.py:276).

    Guillemets retires, tiret cadratin de tete retire, les autres deviennent
    une virgule. Recopie assumee de la regle du service XTTS (son module importe
    PyTorch, donc on ne l'importe pas ici).
    """
    resultat = texte.strip()
    for signe in ('\u00ab', '\u00bb', '"', '\u201c', '\u201d'):
        resultat = resultat.replace(signe, ' ')
    resultat = resultat.strip()
    if resultat[:1] in ('\u2014', '\u2013'):
        resultat = resultat[1:]
    for signe in ('\u2014', '\u2013'):
        resultat = resultat.replace(' ' + signe, ',')
        resultat = resultat.replace(signe + ' ', ', ')
        resultat = resultat.replace(signe, ',')
    return ' '.join(resultat.split()).strip()


def chapitre_du_livre(book_id, chapitre):
    """(texte, titre, erreur) d'un chapitre, lu dans l'EPUB du livre."""
    connection = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    ligne = connection.execute(
        'SELECT filename, title FROM books WHERE id = ?', (book_id,)).fetchone()
    connection.close()
    if not ligne:
        return None, None, 'livre %s inconnu dans la base' % book_id

    candidats = [Path(ligne[0]),
                 RACINE / ligne[0],
                 RACINE / 'data' / ligne[0],
                 RACINE / 'data' / 'library' / ligne[0]]
    chemin = next((c for c in candidats if c.is_file()), None)
    if chemin is None:
        return None, None, 'aucun EPUB trouve pour %s' % ligne[0]

    sys.path.insert(0, str(RACINE))
    from core.epub_parser import get_chapter
    donnees = get_chapter(str(chemin), chapitre)
    if not donnees:
        return None, None, 'chapitre %s introuvable dans %s' % (chapitre, chemin.name)
    return donnees['text'], donnees['title'], ''


def voix_du_livre(book_id, prefixe='neutts:'):
    """[(voix du casting, nombre de personnages)], les plus BAVARDES d'abord.

    Tri par nombre de repliques cumulees : c'est ce que Laurent entend le plus,
    donc ce qu'il faut lui faire ecouter (et non l'ordre alphabetique).
    `prefixe` choisit le moteur : 'neutts:' ou 'kyutai:'.
    """
    connection = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    lignes = connection.execute(
        "SELECT voice_id, COUNT(1), SUM(COALESCE(line_count, 0)) FROM voices "
        "WHERE book_id = ? AND voice_id LIKE ? "
        "GROUP BY voice_id ORDER BY 3 DESC, 2 DESC",
        (book_id, prefixe + '%')).fetchall()
    connection.close()
    return [(voix, nombre) for voix, nombre, _repliques in lignes]


def identifiant_court(voix):
    """'neutts:abc' -> 'abc' (ce que le service attend)."""
    return voix.split(':', 1)[1] if ':' in voix else voix


def analyse(unites, limite, service):
    """Les indicateurs d'un lot d'unites pour une limite donnee."""
    resultat = []
    for texte in unites:
        resultat.append({
            'texte': texte,
            'longueur': len(texte),
            'morceaux': morceaux_prevus(texte, limite, service),
            'courte': len(texte) < PHRASE_COURTE,
            'guillemets': ('\u00ab' in texte or '\u00bb' in texte),
            'tiret': (texte.lstrip()[:1] in ('\u2014', '\u2013')),
        })
    return resultat


def resume(analyses):
    """Les compteurs d'un lot analyse."""
    return {
        'total': len(analyses),
        'multi': sum(1 for a in analyses if a['morceaux'] > 1),
        'pires': max((a['morceaux'] for a in analyses), default=0),
        'courtes': sum(1 for a in analyses if a['courte']),
        'guillemets': sum(1 for a in analyses if a['guillemets']),
        'tirets': sum(1 for a in analyses if a['tiret']),
    }


def main():
    analyseur = argparse.ArgumentParser(
        description="Ou le moteur NeuTTS va-t-il decouper ton texte ?")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="numero du livre (voir la base)")
    analyseur.add_argument('--chapitre', type=int, default=0,
                           help="numero du chapitre (0 = premier)")
    analyseur.add_argument('--voix', default=None,
                           help="une voix (avec ou sans le prefixe neutts:)")
    analyseur.add_argument('--texte', default=None,
                           help="analyser une phrase au lieu d'un chapitre")
    analyseur.add_argument('--max', type=int, default=25,
                           help="lignes de detail affichees (25 par defaut)")
    options = analyseur.parse_args()

    service = charger_service()
    limites = limites_par_voix(service)
    print('')
    print('=' * 74)
    print('NEUTTS : OU LE TEXTE VA-T-IL ETRE DECOUPE ?  (lecture seule)')
    print('=' * 74)
    print('fenetre du moteur  : %.0f s (reference comprise), marge %.0f s'
          % (service.FENETRE_TOTALE_S, service.MARGE_FENETRE_S))
    print('limite par defaut  : %d caracteres   (minimum %d)'
          % (service.MAX_CARACTERES, service.CARACTERES_MINIMUM))
    print('extraits connus    : %d voix' % len(limites))

    # --- Quelles voix examiner ? ---
    voix = []
    if options.voix:
        court = identifiant_court(options.voix)
        if court not in limites:
            print('')
            print('ERR : voix inconnue du moteur : %s' % court)
            proches = [c for c in sorted(limites) if c[:6] == court[:6]]
            if proches:
                print('      peut-etre : %s' % ', '.join(proches[:5]))
            return 1
        voix = [(court, 0)]
    elif options.livre is not None:
        voix = [(identifiant_court(v), n) for v, n in voix_du_livre(options.livre)]
    if not voix:
        classees = sorted(limites.items(), key=lambda item: item[1][1])
        voix = [(classees[0][0], 0), (classees[-1][0], 0)] if classees else []
    if not voix:
        print('')
        print('ERR : aucune voix NeuTTS connue (extraits absents ?).')
        return 1

    # --- Quel texte examiner ? ---
    if options.texte:
        unites = [options.texte]
        titre = '(phrase fournie en ligne de commande)'
    else:
        if options.livre is None:
            print('')
            print('ERR : il faut --livre, ou --texte pour une phrase isolee.')
            return 1
        texte, titre, erreur = chapitre_du_livre(options.livre, options.chapitre)
        if erreur:
            print('')
            print('ERR : %s' % erreur)
            return 1
        unites = phrases_du_texte(texte)

    print('')
    print('texte  : %s' % titre)
    print('unites de synthese (une unite = une requete au moteur) : %d'
          % len(unites))

    # --- Le paysage, voix par voix ---
    print('')
    print('-' * 74)
    print('CE QUE CHAQUE VOIX IMPOSE  (sa limite depend de son extrait)')
    print('-' * 74)
    print('  %-30s %8s %8s   %s'
          % ('voix', 'extrait', 'limite', 'unites decoupees'))
    analyses_par_voix = {}
    for court, nombre in voix[:8]:
        duree, limite = limites[court]
        analyses = analyse(unites, limite, service)
        analyses_par_voix[court] = (limite, analyses)
        r = resume(analyses)
        print('  %-30s %7.1fs %8d   %d / %d  (%.0f %%), jusqu a %d morceaux%s'
              % (court[:30], duree, limite, r['multi'], r['total'],
                 100.0 * r['multi'] / max(1, r['total']), r['pires'],
                 '  [%d personnage(s)]' % nombre if nombre else ''))

    # --- Detail pour la premiere voix ---
    court, _nombre = voix[0]
    limite, analyses = analyses_par_voix[court]
    print('')
    print('-' * 74)
    print('DETAIL avec la voix %s (limite %d caracteres)' % (court[:32], limite))
    print('-' * 74)
    print('  %-4s %6s %9s  %s' % ('n', 'car.', 'morceaux', 'indicateurs'))
    for rang, a in enumerate(analyses[:options.max], 1):
        marques = []
        if a['courte']:
            marques.append('COURTE')
        if a['guillemets']:
            marques.append('guillemets')
        if a['tiret']:
            marques.append('tiret')
        if a['morceaux'] > 1:
            marques.append('RECOLLURE')
        print('  %-4d %6d %9d  %s' % (rang, a['longueur'], a['morceaux'],
                                      ', '.join(marques) or '-'))
    if len(analyses) > options.max:
        print('  ... (%d unites de plus, voir --max)' % (len(analyses) - options.max))

    # --- Les signes que XTTS nettoie et que NeuTTS recoit bruts ---
    r = resume(analyses)
    print('')
    print('-' * 74)
    print('LES SIGNES DE DIALOGUE (le nettoyage jamais reporte sur NeuTTS)')
    print('-' * 74)
    print('  unites avec guillemets « » : %d' % r['guillemets'])
    print('  unites avec tiret en tete  : %d' % r['tirets'])
    print('  total concerne              : %d / %d  (%.0f %%)'
          % (r['guillemets'] + r['tirets'], r['total'],
             100.0 * (r['guillemets'] + r['tirets']) / max(1, r['total'])))
    print('  Rappel : le service XTTS les RETIRE avant l envoi')
    print('  (servir_xtts.py, nettoyer_pour_xtts) ; NeuTTS les recoit tels quels.')

    print('')
    print('-' * 74)
    print('LES PHRASES COURTES (peu de contexte pour le modele)')
    print('-' * 74)
    print('  unites de moins de %d caracteres : %d / %d  (%.0f %%)'
          % (PHRASE_COURTE, r['courtes'], r['total'],
             100.0 * r['courtes'] / max(1, r['total'])))
    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())
