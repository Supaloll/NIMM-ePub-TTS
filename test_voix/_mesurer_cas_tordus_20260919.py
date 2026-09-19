# -*- coding: utf-8 -*-
"""MESURE JETABLE — les cas tordus du 19/09/2026, combien de phrases ?

Contexte : Laurent a ecoute le chapitre 96 (« Le Contrat ») et a signale
quatre cas. Ce script compte, sur le VRAI texte d'un tome, combien de phrases
tombent dans chaque cas. Une mesure ne remplace pas l'oreille : elle dit
seulement si le defaut est rare ou courant.

Les cas mesures :
  A. la phrase ne contient QU'UNE incise -> elle devient un court silence ;
  B. l'incise est GARDEE parce qu'elle est suivie d'un point-virgule
     (« , dit le comte ; aussi je tiens a le constater. ») ;
  C. l'incise est GARDEE et le motif s'arrete sur une civilite SANS POINT
     (« dit Mme Danglars » -> le match s'arrete a « Mme ») ;
  D. le verbe est suivi d'un COMPLEMENT avant le nom
     (« dit avec un imperceptible sourire de mepris le comte ») : le motif ne
     le voit pas du tout ;
  E. la phrase fait 8 caracteres ou moins : c'est ce que le moteur recoit
     pour « — Eh ! » / « — Ah ! », la ou il a invente des mots.

Ne modifie RIEN (lecture seule). Aucun moteur n'est appele.

Usage : python test_voix/_mesurer_cas_tordus_20260919.py --livre 16
"""

import argparse
import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

BASE = RACINE / 'data' / 'nimm_epub.db'
BIBLIOTHEQUE = RACINE / 'data' / 'library'

from modules.decoupage import phrases as _phrases                    # noqa: E402
from modules.incises import incises, incises_gardees                 # noqa: E402

# Civilites qui s'ecrivent SANS point : le motif les prend pour un nom entier.
CIVILITES_SANS_POINT = ('Mme', 'Mmes', 'Mlle', 'Mlles', 'Mgr')

# Le verbe suivi d'un mot en minuscule (donc un complement, pas un nom).
VERBE_COMPLEMENT = re.compile(
    r'[,—]\s*\b(?:dit|dis|répondit|repondit|répliqua|repliqua|reprit|ajouta'
    r'|murmura|fit|s\u2019écria|s\'ecria|cria|demanda|observa|remarqua)\s+'
    r'([a-zà-öø-ÿ][\w\u00c0-\u00ff\'-]*)')

# Un seuil court : sous cette taille, le moteur n'a presque rien a lire.
SEUIL_COURT = 8




def _texte_des_chapitres(chemin):
    """Le texte de chaque chapitre du tome, extrait comme le fait le lecteur."""
    from core.epub_parser import get_chapters
    return [c['text'] for c in get_chapters(str(chemin))]


# ============================================================
# SIMULATION DU CORRECTIF « point-virgule » (mesure a blanc, 19/09/2026)
# ============================================================
# Idee : le POINT-VIRGULE ferme une incise, au meme titre qu'une virgule. Le
# module `modules/incises.py` sait deja que « le point-virgule est une frontiere
# sure » (il s'en sert pour emporter la relative), mais il ne l'accepte pas comme
# BORNE de l'incise : « , dit le comte ; » reste donc lu.
#
# Ce bloc SIMULE la regle candidate SANS toucher au module : il rejoue la
# fonction `incises()` en acceptant en plus un « ; » juste apres le morceau
# trouve. C'est une mesure, pas une modification : rien n'est ecrit.
def _ferme_ou_terminal_pv(phrase, debut, fin):
    """Comme `_ferme_ou_terminal`, mais un « ; » juste apres ferme aussi."""
    texte = phrase[debut:fin]
    apres = phrase[fin:].strip()
    return (texte.rstrip().endswith(',')
            or apres.startswith(';')
            or apres in ('', '.', '!', '?', '\u2026', '\u00bb'))


def incises_avec_point_virgule(phrase):
    """[(debut, fin)] des incises si le « ; » fermait l'incise.

    Rejoue exactement la regle du module (etendue, relative emportee), avec la
    seule difference de la borne. Volontairement prudent : on n'accepte que le
    « ; » IMMEDIATEMENT apres le morceau reconnu, jamais plus loin.
    """
    from modules import incises as _IN
    trouvees = []
    for debut, fin_base in _IN._matches(phrase):
        fin = fin_base
        if not _ferme_ou_terminal_pv(phrase, debut, fin):
            fin = _IN._etendre(phrase, fin_base)
        if not _ferme_ou_terminal_pv(phrase, debut, fin):
            continue
        fin_relative = _IN._etendre_relative(phrase, fin)
        if fin_relative > fin:
            fin = fin_relative
        trouvees.append((debut, fin))
    return trouvees


def _phrase_sans(phrase, trouvees):
    """Le texte de la phrase une fois les incises retirees."""
    texte = phrase
    for debut, fin in sorted(trouvees, reverse=True):
        texte = texte[:debut] + ' ' + texte[fin:]
    return ' '.join(texte.split())


def _a_des_mots(texte):
    """Reste-t-il du texte prononcable (et non de la ponctuation seule) ?"""
    import re as _re
    return bool(_re.search(r'[A-Za-z\u00c0-\u024f]', texte))


def main():
    analyseur = argparse.ArgumentParser(
        description='Compte les cas tordus du 19/09/2026 dans un tome.')
    analyseur.add_argument('--livre', type=int, default=16)
    analyseur.add_argument('--exemples', type=int, default=5)
    options = analyseur.parse_args()

    conn = sqlite3.connect('file:%s?mode=ro' % BASE.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    ligne = conn.execute('SELECT * FROM books WHERE id = ?',
                         (options.livre,)).fetchone()
    if ligne is None:
        print('livre %d introuvable' % options.livre)
        return
    chemin = BIBLIOTHEQUE / ligne['filename']
    print('')
    print('=' * 78)
    print('LIVRE %d : %s' % (options.livre, ligne['title']))
    print('fichier : %s' % ligne['filename'])
    print('=' * 78)
    print('le fichier existe ? %s' % chemin.is_file())
    if not chemin.is_file():
        return

    total = {'phrases': 0, 'incise_seule': 0, 'virgule_fermee': 0,
             'civilite_sans_point': 0, 'verbe_complement': 0, 'courte': 0,
             'gardee_toutes': 0, 'gardee_seule': 0,
             'pv_touchees': 0, 'pv_vides': 0, 'pv_orphelines': 0}
    exemples = {cle: [] for cle in total if cle != 'phrases'}

    for texte in _texte_des_chapitres(chemin):
        for phrase in _phrases(texte):
            total['phrases'] += 1
            gardees = incises_gardees(phrase)
            trouves = incises(phrase)
            # A. phrase = uniquement une incise (le lecteur joue un silence)
            reste = phrase
            for debut, fin in sorted(trouves, reverse=True):
                reste = reste[:debut] + ' ' + reste[fin:]
            if trouves and not re.search(r'[A-Za-z\u00c0-\u024f]', reste):
                total['incise_seule'] += 1
                if len(exemples['incise_seule']) < options.exemples:
                    exemples['incise_seule'].append(phrase)
            if gardees:
                total['gardee_toutes'] += 1
                if not trouves:
                    total['gardee_seule'] += 1
            for texte_incise, raison in gardees:
                position = phrase.find(texte_incise)
                suite = phrase[position + len(texte_incise):].strip()
                # B. l'incise est laissee a cause d'un point-virgule
                if raison == 'non_fermee' and suite.startswith(';'):
                    total['virgule_fermee'] += 1
                    if len(exemples['virgule_fermee']) < options.exemples:
                        exemples['virgule_fermee'].append(phrase)
                # C. le motif s'arrete sur une civilite sans point
                mots = texte_incise.split()
                if mots and mots[-1] in CIVILITES_SANS_POINT:
                    total['civilite_sans_point'] += 1
                    if len(exemples['civilite_sans_point']) < options.exemples:
                        exemples['civilite_sans_point'].append(phrase)
            # D. verbe + complement : le motif ne voit rien du tout
            if not trouves and VERBE_COMPLEMENT.search(phrase):
                total['verbe_complement'] += 1
                if len(exemples['verbe_complement']) < options.exemples:
                    exemples['verbe_complement'].append(phrase)
            # E. phrase tres courte envoyee telle quelle au moteur
            if len(phrase.strip()) <= SEUIL_COURT:
                total['courte'] += 1
                if len(exemples['courte']) < options.exemples:
                    exemples['courte'].append(phrase)
            # F. SIMULATION du correctif « point-virgule » (mesure a blanc)
            candidats = incises_avec_point_virgule(phrase)
            if candidats != trouves:
                total['pv_touchees'] += 1
                nouveau = _phrase_sans(phrase, candidats)
                # Le retrait laisse parfois un « ; » ORPHELIN en debut de phrase
                # (l'incise ouvrait la phrase : « appela Valentine ; ... »). Le
                # module ne le nettoie pas aujourd'hui : la regle candidate doit
                # donc AUSSI le faire, sinon le moteur recoit un « ; » tout seul.
                if nouveau[:1] in ',;:\u2026\u00ab\u00bb"':
                    total['pv_orphelines'] += 1
                nouveau = nouveau.lstrip(' \u00ab\u00bb"\'.,;:!?\u2026\u2014-')
                if not _a_des_mots(nouveau):
                    total['pv_vides'] += 1
                if len(exemples['pv_touchees']) < options.exemples:
                    exemples['pv_touchees'].append(
                        (phrase, _phrase_sans(phrase, trouves), nouveau))

    print('')
    print('-' * 78)
    print('RESULTATS sur %d phrases' % total['phrases'])
    print('-' * 78)
    libelles = [
        ('gardee_toutes', 'phrases avec au moins une incise GARDEE (total)'),
        ('gardee_seule', 'dont phrases SANS aucune incise retirable'),
        ('incise_seule', 'A. phrase qui n est QUE l incise (silence joue)'),
        ('virgule_fermee', 'B. incise gardee a cause d un POINT-VIRGULE'),
        ('civilite_sans_point', 'C. incise coupee sur une civilite SANS POINT'),
        ('verbe_complement', 'D. VERBE + COMPLEMENT avant le nom (non vu)'),
        ('courte', 'E. phrase de %d caracteres ou moins'
                   % SEUIL_COURT),
    ]
    # La simulation se compte a part : ses exemples sont des COUPLES
    # (avant, apres), pas des phrases seules.
    simulation = [
        ('pv_touchees', 'F. SIMULATION point-virgule : phrases touchees'),
        ('pv_vides', 'dont phrases qui perdraient TOUT leur texte'),
        ('pv_orphelines', 'dont une ponctuation ORPHELINE resterait en tete'),
    ]
    for cle, libelle in libelles + simulation:
        part = 100.0 * total[cle] / max(total['phrases'], 1)
        print('  %-52s %6d  (%.3f %%)' % (libelle, total[cle], part))
    print('')
    for cle, libelle in libelles:
        if not exemples[cle]:
            continue
        print('  --- exemples de %s' % libelle)
        for phrase in exemples[cle]:
            print('      %s' % phrase[:110])
    if exemples['pv_touchees']:
        print('')
        print('  --- CE QUE LE CORRECTIF POINT-VIRGULE CHANGERAIT (avant -> apres)')
        for phrase, avant, apres in exemples['pv_touchees']:
            print('      livre : %s' % phrase[:104])
            print('      AVANT : %s' % avant[:104])
            print('      APRES : %s' % apres[:104])
            print('')
    conn.close()


if __name__ == '__main__':
    main()
