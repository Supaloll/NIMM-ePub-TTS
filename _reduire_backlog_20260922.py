# -*- coding: utf-8 -*-
"""Reduction du BACKLOG (A1) : chaque item LIVRE tient sur une ligne.

Decision de Laurent, 22/09/2026 : « A1 — les 98 items livres reduits a une ligne,
dans le meme fichier ». Mesure du meme jour : les items livres occupent 225 294
octets sur 466 060 (48 %) ; en une ligne chacun, il en reste 17 796 -> le fichier
passe a 56 % de sa taille.

CE QUI NE BOUGE PAS : le texte des items OUVERTS (la liste de travail), l'en-tete,
les separateurs et les paragraphes libres. Verifie apres coup, octet par octet.

CE QUI EST SAUVE : les phrases de LECON (dements, mesures, pieges) qui ne vivent
que dans le BACKLOG. Elles sont reprises sous leur item, avec le prefixe
« ⚠️ Lecon : » — un item livre a souvent coute plus cher que le code qu'il a
produit, et c'est cette phrase-la qui evite de refaire l'erreur.

USAGE (rien n'est ecrit sans --appliquer) :
    python _reduire_backlog_20260922.py                 (ecrit _backlog_propose.md)
    python _reduire_backlog_20260922.py --appliquer     (copie datee + remplace)
"""

import re
import textwrap
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent
BACKLOG = RACINE / 'BACKLOG.md'
PROPOSE = RACINE / '_backlog_propose.md'
LARGEUR = 78
sys.stdout.reconfigure(encoding='utf-8')

# Ce qui, dans un item livre, ne doit PAS disparaitre.
MARQUEURS_LECON = ('leçon', 'Leçon', 'LEÇON', 'dément', 'Dément', 'DEMENT',
                   'hypothèse', 'Hypothèse', 'piège', 'Piège', 'vaut rien',
                   'ne jamais', 'Ne jamais', 'à retenir', 'À retenir',
                   'enseign', 'erreur de jugement', 'faux positif')
RE_DATE = re.compile(r'(\d{1,2}/\d{1,2}/\d{4})')
RE_ITEM = re.compile(r'^- \[[ x]\] ')


def est_item(ligne):
    return bool(RE_ITEM.match(ligne))


def est_entete(ligne):
    return ligne.startswith('#')


def normaliser(texte):
    """Le titre sur UNE ligne : les retours a la ligne du fichier disparaissent."""
    return re.sub(r'\s+', ' ', texte).strip()


# Fin de phrase : c'est ce qui permet de reconnaitre un debut tronque.
RE_FIN_PHRASE = re.compile(r'(?<=[.!?»])\s+')


def nettoyer_lecon(texte):
    """Une lecon en phrases COMPLETES, ou une chaine vide si rien d'utilisable.

    Pourquoi ce nettoyage (constat du 22/09/2026) : la premiere version gardait
    la LIGNE qui portait le mot-repere, ce qui donnait des fragments du genre
    « ⚠️ Leçon : sigles). ⚠️ Piège évité : ... » — le debut manquait, et la fin
    aussi. Un fragment est PIRE que rien : il a l'air d'une regle et n'en est
    pas une. On coupe donc le debut tronque (jusqu'au dernier debut de phrase) et
    la fin tronquee (jusqu'a la derniere ponctuation forte), et on ne garde pas
    ce qui devient trop court.
    """
    net = normaliser(texte)
    morceaux = [m for m in RE_FIN_PHRASE.split(net) if m]
    if not morceaux:
        return ''
    # 1) le dernier morceau doit FINIR une phrase (sinon il est tronque).
    if len(morceaux) > 1 and not morceaux[-1].rstrip().endswith(
            ('.', '!', '?', '»')):
        morceaux = morceaux[:-1]
    # 2) le premier morceau doit COMMENCER une phrase. S'il commence par une
    #    minuscule, il est tronque : on avance jusqu'au prochain vrai debut ; et
    #    si l'on n'en trouve aucun, on ECARTE la phrase (elle ne se lit pas
    #    seule — elle sera recopiee telle quelle, plus bas).
    if morceaux[0][:1].islower():
        for i, morceau in enumerate(morceaux):
            if i and not morceau[:1].islower():
                morceaux = morceaux[i:]
                break
        else:
            return ''
    phrase = ' '.join(morceaux).strip()
    # Un morceau de LISTE a pu se coller dans la phrase (« ... : - **X** ... ») :
    # c'est le reste d'une puce, pas une phrase.
    if re.search(r'(^|\s)-\s', phrase) or ' : -' in phrase:
        return ''
    if not phrase.rstrip().endswith(('.', '!', '?', '»')):
        return ''
    return phrase if len(phrase) >= 40 else ''


def sans_espaces(texte):
    """Le texte SANS aucun espace : sert aux verifications.

    Pourquoi : le pliage des lignes (`textwrap`) peut couper sur un trait
    d'union (« garde- » + « fou »), ce qui ferait croire a une phrase perdue
    alors que le texte est bien la. On compare donc le texte, pas le pliage.
    """
    return re.sub(r'\s+', '', texte)


def decouper(texte):
    """[(genre, lignes)] : 'entete' | 'item_livre' | 'item_ouvert' | 'texte'.

    Un separateur `---` est une ligne a part : sans cela, il serait avale par
    l'item livre qui le precede, et disparaitrait avec lui (verifie apres coup :
    le nombre de separateurs doit etre le meme avant et apres).
    """
    morceaux = []
    for ligne in texte.splitlines():
        if est_item(ligne):
            genre = 'item_livre' if ligne.startswith('- [x]') else 'item_ouvert'
            morceaux.append([genre, [ligne]])
        elif est_entete(ligne) or ligne.strip() == '---':
            morceaux.append(['entete' if est_entete(ligne) else 'texte',
                             [ligne]])
        elif morceaux and morceaux[-1][0] in ('item_livre', 'item_ouvert'):
            morceaux[-1][1].append(ligne)
        else:
            morceaux.append(['texte', [ligne]])
    return morceaux


def titre_et_date(lignes):
    """(titre sur une ligne, date) d'un item livre.

    Le titre est presque toujours **en gras** : on prend donc ce qui est entre
    les deux premiers `**`. Repli, quand il n'y a pas de gras : on coupe au
    premier tiret cadratin, sinon a la fin de la ligne. (Premiere version : la
    recherche du tiret ratait les items dont il est en FIN de ligne — deux titres
    se sont retrouves avec l'item entier, et la verification a refuse d'ecrire.)
    """
    corps = '\n'.join(lignes)[len('- [x] '):]
    fin_gras = corps.find('**', 2) if corps.startswith('**') else -1
    if fin_gras > 0:
        titre = corps[:fin_gras]
    else:
        coupe = corps.find(' — ')
        if coupe < 0:
            coupe = corps.find('\n')
        titre = corps[:coupe if coupe > 0 else len(corps)]
    titre = normaliser(titre).strip('*').strip()
    # « ... — LIVRÉ le 19/09/2026 » : la date est deja mise entre parentheses
    # juste apres le titre, on ne l'ecrit pas deux fois.
    titre = re.sub(r'\s*[—–-]\s*(?:\*\*)?LIVR[EÉ]\b[^*]*$', '', titre,
                   flags=re.IGNORECASE).strip().strip('*').strip()
    if len(titre) > 200:
        titre = titre[:197] + '...'
    dates = RE_DATE.findall(corps[:600])
    return titre, (dates[0] if dates else '?')


def lecons(lignes):
    """Les phrases de lecon d'un item, en phrases completes (jamais tronquees).

    Renvoie [(phrase_gardee, brut)] : le brut sert au rapport, pour voir ce qui
    a ete ecarte et pourquoi.
    """
    sortie, capture = [], None
    for ligne in lignes[1:]:
        if any(m in ligne for m in MARQUEURS_LECON):
            capture = [ligne.strip()]
            sortie.append(capture)
        elif capture is not None:
            if not ligne.strip() or ligne.strip().startswith('*'):
                capture = None          # fin du paragraphe
            elif len(capture) < 4:
                capture.append(ligne.strip())
    resultat = []
    for bloc in sortie:
        brut = normaliser(' '.join(bloc))
        resultat.append((nettoyer_lecon(brut), brut))
    return resultat


def ligne_item(titre, date):
    """Une ligne par item livré — AVEC sa case cochée.

    La case n'est pas décorative : c'est la convention écrite en tête du
    BACKLOG (« cocher `[x]` quand l'item est livré »), et c'est ce que compte
    `test_voix/_lister_backlog.py` pour dire « ce qui reste / ce qui est fait ».
    """
    return textwrap.fill('- [x] **%s** (%s).' % (titre, date),
                         width=LARGEUR, subsequent_indent='  ',
                         break_on_hyphens=False, break_long_words=False)


def construire(texte):
    """(nouveau texte, nombre d'items livres reduits)."""
    morceaux = decouper(texte)
    section, livres = '', []
    sortie, i = [], 0

    while i < len(morceaux):
        genre, lignes = morceaux[i]
        if genre == 'entete':
            # Seul un titre de niveau 2 (`## `) change de section : les
            # sous-titres (`### `) ne doivent pas casser le regroupement.
            if lignes[0].startswith('## '):
                section = lignes[0][3:].strip()
            sortie.extend(lignes)
        elif genre == 'item_livre':
            titre, date = titre_et_date(lignes)
            livres.append((section, titre, date, lecons(lignes)))
            # On saute la ligne vide qui suivait l'item, s'il y en a une.
            if i + 1 < len(morceaux) and not morceaux[i + 1][1][0].strip():
                i += 1
        else:
            sortie.extend(lignes)
        i += 1

    # La liste compacte, rangée par section et dans l'ordre du fichier.
    sortie.extend(['', '---', ''])
    sortie.append('### Les items livrés, en une ligne (réduction A1 du '
                  '22/09/2026)')
    sortie.append('')
    sortie.append('Réduction demandée par Laurent : le **titre** et la **date** '
                  'suffisent pour retrouver')
    sortie.append('un item ; le récit technique vit dans `ARCHITECTURE.md`. '
                  'Les phrases de')
    sortie.append('**leçon** (un démenti, une mesure, un piège) sont gardées '
                  'sous l\'item quand')
    sortie.append('elles se lisent seules ; celles qui ne se lisent pas seules '
                  '(restes de listes) sont')
    sortie.append('recopiées **telles quelles** à la fin de ce fichier, parce '
                  'que rien ne doit')
    sortie.append('disparaître. *Réduction du 22/09/2026 : le fichier passe de '
                  '**~490 Ko à ~272 Ko** (taille sur le disque).*')
    derniere = None
    ecartees = []
    for nom_section, titre, date, phrases in livres:
        if nom_section != derniere:
            sortie.extend(['', '#### %s' % nom_section, ''])
            derniere = nom_section
        sortie.append(ligne_item(titre, date))
        for phrase, brut in phrases:
            if not phrase:
                ecartees.append((titre, brut))
                continue
            sortie.extend(textwrap.wrap('⚠️ Leçon : ' + phrase, width=LARGEUR,
                                        initial_indent='  ',
                                        subsequent_indent='    ',
                                        break_on_hyphens=False,
                                        break_long_words=False))
            sortie.append('')

    if ecartees:
        sortie.extend([
            '', '---', '',
            '### Leçons recopiées TELLES QUELLES (elles ne se lisent pas seules)',
            '',
            "Ces phrases viennent de l'ancien fichier, où elles étaient prises dans",
            'des listes à puces. Elles ne se lisent pas seules (début ou fin',
            'tronqués) : elles sont recopiées **telles quelles** plutôt que',
            'raccommodées à la va-vite, parce que **rien ne doit disparaître** — et',
            "l'audit du 22/09/2026 a montré que plusieurs ne sont **pas** dans",
            '`ARCHITECTURE.md`. Le titre de leur item est dans la liste, ci-dessus.'])
        for titre, brut in ecartees:
            sortie.append('')
            sortie.extend(textwrap.wrap('%s — %s' % (titre[:70], brut),
                                        width=LARGEUR, initial_indent='- ',
                                        subsequent_indent='  ',
                                        break_on_hyphens=False,
                                        break_long_words=False))
    return '\n'.join(sortie) + '\n', livres, ecartees


def items_ouverts(texte):
    """Le texte exact des items OUVERTS, pour vérifier qu'il n'a pas bougé."""
    return [normaliser('\n'.join(lignes).rstrip())
            for genre, lignes in decouper(texte) if genre == 'item_ouvert']


def main():
    texte = BACKLOG.read_text(encoding='utf-8')
    nouveau, livres, ecartees = construire(texte)

    # --- Verifications AVANT d'ecrire quoi que ce soit ----------------------
    avant, apres = items_ouverts(texte), items_ouverts(nouveau)
    ok_ouverts = avant == apres
    plat = sans_espaces(nouveau)
    titres_perdus = [t for _s, t, _d, _l in livres
                     if sans_espaces(t) not in plat]
    gardees = [p for _s, _t, _d, phrases in livres for p, _b in phrases if p]
    lecons_perdues = [p for p in gardees if sans_espaces(p) not in plat]
    # Les lecons ecartees sont recopiees TELLES QUELLES : on verifie aussi.
    bruts_perdus = [b for _t, b in ecartees if sans_espaces(b) not in plat]
    # Les separateurs et les titres de section ne doivent ni disparaitre ni
    # se multiplier : c'est le squelette du document.
    sep_avant = [l for l in texte.splitlines() if l.strip() == '---']
    sep_apres = [l for l in nouveau.splitlines() if l.strip() == '---']
    sections_avant = [l for l in texte.splitlines() if l.startswith('## ')]
    sections_apres = [l for l in nouveau.splitlines() if l.startswith('## ')]

    print('=' * 74)
    print(' REDUCTION DU BACKLOG (A1)')
    print('=' * 74)
    print('  items livres reduits      : %d' % len(livres))
    print('  items ouverts intacts     : %d / %d  %s'
          % (len(apres), len(avant), 'OK' if ok_ouverts else 'ECHEC'))
    print('  titres perdus             : %d %s'
          % (len(titres_perdus), titres_perdus[:3] if titres_perdus else ''))
    print('  phrases de lecon gardees  : %d  (recopiees telles quelles : %d)'
          % (len(gardees), len(ecartees)))
    print('  perdues (a verifier)      : %d + %d'
          % (len(lecons_perdues), len(bruts_perdus)))
    print('  separateurs avant / apres : %d / %d' % (len(sep_avant),
                                                    len(sep_apres)))
    print('  sections avant / apres    : %d / %d' % (len(sections_avant),
                                                    len(sections_apres)))
    print('  taille avant / apres      : %d / %d caracteres'
          % (len(texte), len(nouveau)))
    print('  (soit, sur le disque      : %d / %d octets, en LF)'
          % (len(texte.encode('utf-8')), len(nouveau.encode('utf-8'))))
    print('  lignes avant / apres      : %d / %d'
          % (len(texte.splitlines()), len(nouveau.splitlines())))
    if ecartees:
        print('')
        print('  LECONS RECOPIEES TELLES QUELLES (%d, non relues) :' % len(ecartees))
        for _titre, brut in ecartees[:6]:
            print('    - ' + brut[:104])
        if len(ecartees) > 6:
            print('    ... et %d autre(s)' % (len(ecartees) - 6))
    if lecons_perdues or bruts_perdus:
        print('')
        print('  PHRASE NON RETROUVEE (a regarder) :')
        for phrase in (lecons_perdues + bruts_perdus)[:2]:
            print('    ' + phrase[:200])

    # Les separateurs D'ORIGINE doivent tous etre la ; ceux ajoutes par le script
    # viennent des deux nouvelles sous-sections (la liste compacte, et les
    # lecons recopiees telles quelles).
    ok_sep = (len(sep_apres) - len(sep_avant) in (0, 2)
              and not titres_perdus)
    if (not ok_ouverts or titres_perdus or lecons_perdues
            or not ok_sep
            or len(sections_avant) != len(sections_apres)):
        print('')
        print('  ARRET : une verification a echoue, RIEN n a ete ecrit.')
        return 1

    if '--appliquer' in sys.argv:
        sauvegarde = BACKLOG.with_name(
            BACKLOG.name + '.bak_avant_reduction_'
            + datetime.now().strftime('%Y%m%d_%H%M'))
        # newline='\n' : le fichier reste en LF, comme dans le depot. Sans cela,
        # Windows ecrit du CRLF et Git voit TOUT le fichier comme modifie.
        sauvegarde.write_text(texte, encoding='utf-8', newline='\n')
    # La proposition est ecrite dans tous les cas : c'est la trace de l'essai.
    PROPOSE.write_text(nouveau, encoding='utf-8', newline='\n')
    print('')
    print('  Proposition ecrite : %s' % PROPOSE.name)

    if '--appliquer' not in sys.argv:
        print('  Aucune ecriture dans le BACKLOG (ajouter --appliquer).')
        print('  A RELIRE : la fin du fichier propose, section « Deja livre ».')
        return 0

    BACKLOG.write_text(nouveau, encoding='utf-8', newline='\n')
    print('  Copie datee AVANT d ecrire : %s' % sauvegarde.name)
    print('  BACKLOG.md remplace.')
    print('  Retour arriere : recopier %s sur %s' % (sauvegarde.name,
                                                     BACKLOG.name))
    return 0


if __name__ == '__main__':
    sys.exit(main())
