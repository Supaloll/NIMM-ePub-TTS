# -*- coding: utf-8 -*-
"""Le retrait des INCISES de parole, avant l'envoi au moteur — règle unique.

Décision de Laurent, 18/09/2026, après avoir écouté le banc
(`test_voix/ecoute_ponctuation_20260918_1937`) : « à chaque fois les incises ont
bien disparu […] et en plus la voix me paraît plus fluide ». Avec une voix
différente par personnage, l'incise qui dit QUI parle est redondante, et elle
coupe la voix du personnage au milieu de sa réplique.

Mesure faite avant de décider (tome 5, 5 105 phrases) : **289 phrases avec
incise = 5,66 %**, dont 104 à pronom (« dit-elle ») et 185 à nom (« dit
Morrel ») — soit 0,94 % du texte lu.

RÈGLE PRUDENTE (une suppression naïve casse du texte, c'est mesuré) :
  - on ne retire une incise que si elle est **fermée** (virgule après le nom)
    ou **terminale** (elle finit la phrase) ;
  - on ne touche JAMAIS une incise suivie d'un COMPLÉMENT (« , dit-il en
    souriant, » laisserait « en souriant » tout seul) ;
  - on exige une **frontière de mot** avant le verbe, sinon « maudit-il » ou
    « interdit-elle » seraient pris pour « dit-il » ;
  - on respecte la **casse**, sinon « répondit le jeune homme » deviendrait une
    incise et le sujet disparaîtrait de la phrase.
Le code proposé à Laurent par un autre outil, essayé le même soir, abîmait
**78 % des phrases qu'il touchait** (588 sur 756) faute de ces garde-fous.

Le texte AFFICHÉ n'est jamais modifié : seule la version parlée change.
"""

import re

VERBES = ('dit', 'dis', 'dirent', 'répondit', 'repondit', 'répondirent',
          'repondirent', 'répond', 'repond', 'répliqua', 'repliqua',
          'répliquèrent', 'repliquerent', 's\'écria', 's\'ecria', 'écria',
          'ecria', 's\'écrièrent', 's\'ecrierent', 'cria', 'crièrent',
          'crierent', 'demanda', 'demandèrent', 'demanderent', 'demande',
          'reprit', 'reprirent', 'reprend', 'ajouta', 'ajoutèrent',
          'ajouterent', 'ajoute', 'murmura', 'murmurèrent', 'murmurerent',
          'murmure', 'poursuivit', 'poursuit', 'continua', 'continuèrent',
          'continuerent', 'hasarda', 'observa', 'remarqua', 's\'exclama',
          'exclama', 's\'exclamèrent', 'prononça', 'balbutia', 'balbutièrent',
          'soupira', 'soupirèrent', 'grommela', 'gronda', 'tonna', 'vociféra',
          'interrompit', 'interrompirent', 'fit', 'firent', 'répéta', 'repeta',
          'répète', 'avoua', 'déclara', 'declara', 'conclut', 'acheva',
          'commença', 'termina', 'insista', 'objecta', 'riposta', 'répartit',
          'interrogea', 'questionna', 'exigea', 'ordonna', 'supplia', 'pria',
          'songea', 'gémit', 'sanglota', 'plaida', 'protesta', 'appela',
          'appelèrent', 'conseilla', 'répondit-on',
          # Imparfaits et formes courantes du recit : « , disait-il, ».
          'disait', 'répondait', 'demandait', 'ajoutait', 'reprenait',
          'murmurait', 'continuait', 'répétait', 's\'écriait', 'criait',
          'poursuivait', 'observait', 'remarquait', 'songeait', 'pensait',
          'balbutiait', 'soupirait', 'grommelait', 'insistait', 'avouait',
          'déclarait', 'expliquait', 'racontait', 'concluait', 'ajoutait-on')

# Traits d'union possibles dans « dit-il » (clavier, typographique, insécable).
TIRETS = '\u002d\u2010\u2011\u2012\u2013'

# Un COMPLÉMENT après l'incise : depuis le 18/09/2026 au soir, on ne le refuse
# plus — on RETIRE l'incise en entier, bornee par la virgule fermante (voir
# `_etendre`). Cette constante reste la pour memoire des premieres versions.
DEBUT_COMPLEMENT = re.compile(
    r"^(?:en\s|d[\u2019']un[e]?\s|à\s|au\s|avec\s|sans\s|tout\s|comme\s"
    r"|paraissant|souriant|pleurant|haussant|baissant|serrant|tendant|reprenant)",
    re.IGNORECASE)

# Longueur maximale de ce qu'on accepte d'avaler APRÈS le verbe : « au comte »,
# « avec sa voix demi-railleuse », « en souriant ». Au-delà, c'est autre chose
# qu'une incise (une vraie proposition) et on ne touche à rien.
LONGUEUR_SUITE_MAX = 70

# Le « t » euphonique : « ajouta-T-il », « demanda-T-elle », « dit-ON ».
# Il manquait dans la premiere version, et c'est TRES frequent en francais :
# mesure du 18/09/2026 au soir, c'est ce qui laissait passer des incises chez
# Laurent alors que le reste fonctionnait.
EUPHONIQUE = '(?:[%s]t)?' % TIRETS

# Le pronom REFLECHI devant le verbe : « , SE demanda-t-elle », « , SE reprit-il »,
# « , S'ecria-t-il ». Remarque TRES juste de Laurent (18/09/2026) : sans lui, le
# motif exigeait le verbe juste apres la virgule, et toutes ces formes etaient
# ignorees (l'incise restait, elle ne laissait pas de « se » orphelin).
REFLEXIF = r"(?:se\s+|s[\u2019'])?"

# Incise à PRONOM : « , dit-il, » « , s'écria-t-il, » « , se demanda-t-elle, ».
MOTIF_PRONOM = re.compile(
    r'[,—]\s*\b%s(?:%s)%s[%s\s]?(?:il|elle|on|je|nous|vous|ils|elles)\b\s*,?'
    % (REFLEXIF, '|'.join(v for v in VERBES if not v.endswith('-il')),
       EUPHONIQUE, TIRETS))

# Un NOM apres le verbe de parole. Trois formes, toutes tres frequentes :
#   « Morrel »            (nom propre simple)
#   « M. de Villefort »   (civilite + PARTICULE : d'Avrigny, de Morcerf, l'abbe)
#   « le comte »          (nom commun avec article : « , dit le comte, »)
# Les deux dernieres manquaient dans la premiere version : mesure du
# 18/09/2026 au soir, c'est CE QUI laissait passer des incises chez Laurent
# alors que le reste fonctionnait (« , dit M. de Villefort, »).
CIVILITE = r"(?:(?:M|MM|Mme|Mmes|Mlle|Mlles|Mgr|Dr|Pr)\.\s*)?"
PARTICULE = r"(?:d[\u2019']|de\s|du\s|des\s|l[\u2019'])"
DEMONSTRATIF = (r"(?:celui-ci|celui-là|celle-ci|celle-là|ceux-ci|ceux-là"
                r"|celles-ci|celles-là)")
NOM_APRES_VERBE = (r"(?:[A-ZÀ-ÖØ-Ý][\w\u00c0-\u00ff'-]*"      # Morrel
                   r"|%s[\w\u00c0-\u00ff'-]+"                  # d'Avrigny, l'abbe
                   r"|%s"                                      # celui-ci
                   r"|(?:le|la|les|un|une)(?:\s+[\w\u00c0-\u00ff'-]+){1,2}"
                   r")" % (PARTICULE, DEMONSTRATIF))          # le comte, la jeune fille

# --- Les DÉBUTS d'incise ---------------------------------------------------
# On ne demande plus la virgule fermante dans le motif : l'incise peut porter un
# complément (« , dit-il au comte, », « fit celui-ci avec sa voix demi-railleuse, »).
# C'est `_etendre` qui trouve la fin, et `_ferme_ou_terminal` qui valide.
# Incise à PRONOM : « , dit-il », « , s'écria-t-elle », « , se demanda-t-elle ».
MOTIF_PRONOM = re.compile(
    r'[,—]\s*\b%s(?:%s)%s[%s\s]?(?:il|elle|on|je|nous|vous|ils|elles)\b'
    % (REFLEXIF, '|'.join(v for v in VERBES if not v.endswith('-il')),
       EUPHONIQUE, TIRETS))

# Incise à NOM, après une virgule ou un tiret : « , dit Barrois », « , dit M. de
# Villefort », « , dit le comte », « , fit celui-ci ».
MOTIF_NOM = re.compile(
    r'[,—]\s*(?:%s)\s+%s%s' % ('|'.join(VERBES), CIVILITE, NOM_APRES_VERBE))

# Incise EN TÊTE de phrase : « fit celui-ci avec sa voix demi-railleuse, comment
# vous portez-vous ? ». Cas fréquent depuis que le découpage sépare les phrases
# au « ! » : l'incise ouvre le morceau (exemple de Laurent, 18/09/2026).
MOTIF_DEBUT = re.compile(
    r'^(?:%s)\s+%s%s' % ('|'.join(VERBES), CIVILITE, NOM_APRES_VERBE))


# Un PRONOM RELATIF juste après l'incise : la description continue.
# « , dit Cavalcanti, QUI SE GRISAIT à ce bruit métallique de paroles dorées. »
# Retirer l'incise SEULE laisse « qui se grisait… » orphelin, et le lecteur le lit
# tout seul (défaut constaté par Laurent le 18/09/2026). On emporte donc la
# relative avec l'incise : « c'est magnifique. ».
# « que » est VOLONTAIREMENT absent de la liste : il est ambigu (« Le fait est,
# dit-il, QUE je meurs de soif » = conjonction, pas relative). Défaut attrapé par
# un test le 18/09/2026 au soir.
DEBUT_RELATIVE = re.compile(
    r"^(?:qui|dont|o[uù]|auquel|auxquels|auxquelles|laquelle|lequel|lesquels"
    r"|lesquelles|desquels|desquelles|duquel)\b",
    re.IGNORECASE)

# Mais on ne va pas au-delà d'un DÉCROCHAGE de sens : il appartient à l'auteur.
# Deux subtilités apprises le 18/09/2026 au soir :
#   - le POINT-VIRGULE est une frontière sûre (il sépare deux propositions) ;
#   - « et qui… », « et dont… » n'est PAS un décrochage : c'est une **relative
#     coordonnée**, qui décrit encore le personnage et doit partir avec l'incise
#     (« , dit Monte-Cristo, qui sentit…, ET QUI COMPRIT… ; ma protection… »).
MOTIF_DECROCHAGE = re.compile(
    r';'
    r'|,\s*(?:mais|or|car|donc|cependant|pourtant|toutefois|ensuite|alors'
    r'|quand|lorsque)\b'
    r"|,\s*et\s+(?!qui\b|que\b|qu[\u2019']|dont\b|o[uù]\b|auquel\b|auxquels\b"
    r'|auxquelles\b|laquelle\b|lequel\b|lesquels\b|lesquelles\b)'
    r'|,\s*puis\s+(?!qui\b)')

LONGUEUR_MAX = 200


def _etendre_relative(phrase, fin):
    """Emporte la relative qui suit l'incise (« , dit X, qui souriait. »)."""
    suite = phrase[fin:]
    if not DEBUT_RELATIVE.match(suite.strip()):
        return fin
    debut = fin + (len(suite) - len(suite.lstrip()))
    reste = phrase[debut:]
    # GARDE-FOU : si la PROPOSITION qui suit l'incise est une QUESTION, ce n'est
    # pas une relative (« , se demanda-t-elle, que faisait-il ? ») : on ne
    # l'emporte pas. On ne regarde donc que la proposition immédiate -- un « ? »
    # situé tout à la fin d'une longue phrase est la question du personnage, pas
    # un signe de relative (cas réel du tome 5 : phrase de 409 caractères finissant
    # par « le bonheur de votre connaissance ?) », constat de Laurent 18/09/2026).
    premiere_proposition = re.split(r'(?<=[.!?;])', reste, maxsplit=1)[0]
    if premiere_proposition.rstrip().endswith(('?', '!')):
        return fin
    decrochage = MOTIF_DECROCHAGE.search(reste)
    if decrochage and decrochage.start() > 0:
        fin_relative = debut + decrochage.start()
    else:
        fin_relative = len(phrase)
    # La limite porte sur ce qu'on EMPORTE (la relative), pas sur tout ce qui
    # reste de la phrase : chez Dumas, la suite peut être longue après le
    # point-virgule (« ; ma protection ne vous a été acquise qu'après… »).
    if fin_relative - debut > LONGUEUR_MAX:
        return fin                      # trop long : on ne s'y aventure pas
    return fin_relative


def _matches(phrase):
    """[(debut, fin)] de tout ce qui RESSEMBLE a une incise (sans filtre)."""
    trouves = []
    for motif in (MOTIF_DEBUT, MOTIF_PRONOM, MOTIF_NOM):
        for m in motif.finditer(phrase):
            trouves.append((m.start(), m.end()))
    return sorted(trouves)


def _etendre(phrase, fin):
    """Étend la fin de l'incise jusqu'à la virgule suivante (ou la fin).

    C'est ce qui permet de retirer « , dit-il au comte, » ou « fit celui-ci avec
    sa voix demi-railleuse, » **en entier**, sans laisser « au comte » ni « avec
    sa voix… » tout seuls. On refuse l'extension si la suite contient une
    ponctuation forte (donc une autre phrase) ou si elle est trop longue.

    Idée de Laurent (18/09/2026) : « je ne vois pas comment supprimer une incise
    comme [fit celui-ci avec sa voix demi-railleuse] de façon mécanique ». C'est
    mécanique — à condition de borner : une virgule au plus, pas de phrase
    entière, une longueur limitée.
    """
    suite = phrase[fin:]
    virgule = suite.find(',')
    if virgule == -1:
        reste = suite.strip()
        # On tolere la ponctuation FINALE de la phrase (« au comte. », « au
        # comte ! ») : c'est la borne naturelle de l'incise terminale.
        coeur = reste.rstrip('.!?\u2026\u00bb ')
        # ET on exige que la suite ressemble a un COMPLÉMENT (« au comte »,
        # « en souriant ») : sans ce garde-fou, une replique mal ponctuee
        # (« dit Morrel vous qui etes si cher ? ») serait avalee en entier.
        if (reste and len(reste) <= LONGUEUR_SUITE_MAX
                and not re.search(r'[.!?\u2026:;]', coeur)
                and DEBUT_COMPLEMENT.match(reste)):
            return len(phrase)
        return fin
    reste = suite[:virgule + 1]
    if len(reste.strip()) <= LONGUEUR_SUITE_MAX \
            and not re.search(r'[.!?\u2026:;]', reste):
        return fin + virgule + 1
    return fin


def _ferme_ou_terminal(phrase, debut, fin):
    """L'incise est-elle fermée (virgule après) ou terminale (fin de phrase) ?"""
    texte = phrase[debut:fin]
    apres = phrase[fin:].strip()
    return (texte.rstrip().endswith(',')
            or apres in ('', '.', '!', '?', '\u2026', '\u00bb'))


def incises(phrase):
    """[(debut, fin)] des incises RETIRABLES d'une phrase (règle prudente)."""
    trouvees = []
    for debut, fin_base in _matches(phrase):
        fin = fin_base
        if not _ferme_ou_terminal(phrase, debut, fin):
            fin = _etendre(phrase, fin_base)
        if not _ferme_ou_terminal(phrase, debut, fin):
            continue
        # La description qui suit (« qui se grisait… ») part AVEC l'incise :
        # sinon elle resterait seule, et serait lue comme une phrase bizarre.
        # On l'accepte telle quelle : c'est une décision de la règle, pas une
        # incise « fermée » qu'il faudrait valider de nouveau.
        fin_relative = _etendre_relative(phrase, fin)
        if fin_relative > fin:
            fin = fin_relative
        trouvees.append((debut, fin))
    return trouvees


def incises_gardees(phrase):
    """[(texte, raison)] des incises VOLONTAIREMENT laissées en place.

    Sert au diagnostic (et à la transparence) : quand Laurent entend encore une
    incise, on veut savoir POURQUOI. Depuis le 18/09/2026 au soir, les incises
    suivies d'un complément sont retirées **en entier** (la virgule fermante sert
    de borne) : il ne reste donc que les cas où l'incise n'est **pas fermée** —
    la retirer couperait la phrase au milieu d'une réplique.
    """
    gardees = []
    for debut, fin_base in _matches(phrase):
        fin = fin_base
        if not _ferme_ou_terminal(phrase, debut, fin):
            fin = _etendre(phrase, fin_base)
        if not _ferme_ou_terminal(phrase, debut, fin):
            gardees.append((phrase[debut:fin], 'non_fermee'))
    return gardees


def retirer_incises(phrase):
    """La phrase sans ses incises retirables (ou la phrase inchangée)."""
    trouvees = incises(phrase)
    if not trouvees:
        return phrase
    texte = phrase
    for debut, fin in sorted(trouvees, reverse=True):
        texte = texte[:debut] + ' ' + texte[fin:]
    texte = re.sub(r'\s{2,}', ' ', texte)
    # On retire l'espace parasite AVANT le point et la virgule, mais on GARDE
    # celui qui precede « ? » et « ! » : c'est la typographie francaise, et le
    # moteur la prononce naturellement (meme regle que `_clean_text`).
    texte = re.sub(r'\s+([.,;:\u2026])', r'\1', texte)
    texte = re.sub(r',\s*,+', ',', texte)
    texte = texte.strip()
    # GARDE-FOU VITAL : certaines phrases ne SONT qu'une incise (« ajouta
    # Valentine en s'adressant a Noirtier. »). Les vider ferait disparaitre la
    # phrase -- et le moteur refuserait un texte vide, donc plus aucun son.
    # Dans ce cas on ne retire rien : la phrase reste entiere.
    if not re.search(r'[A-Za-zÀ-ÖØ-öø-ÿ]', texte):
        return phrase
    return texte
