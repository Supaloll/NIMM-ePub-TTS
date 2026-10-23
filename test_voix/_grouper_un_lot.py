# -*- coding: utf-8 -*-
"""RECOLLER UN LOT D'ECOUTE EN UN FICHIER PAR NOM -- pour ecouter sans cliquer 39 fois.

D'OU VIENT CET OUTIL (16/10/2026, retour de Laurent, mot pour mot : « Alors tu me
donnes des chemins de fichiers .py, mais je n'ai pas les liens pour les ecouter »).
Le lot automatique du Trone de Fer compte 39 fichiers (13 noms x 3 prises) : a
l'oreille, comparer trois versions d'un nom oblige a cliquer trois fichiers et a se
souvenir du premier -- c'est penible, et c'est LA faute a ne pas refaire.

CE QU'IL FAIT : il prend un dossier de lot (le DERNIER par defaut, ou celui qu'on
lui donne en argument), et il recolle les prises ENSEMBLE, dans l'ordre :
    1_CIBLE_anglaise, puis 2_FRANCAIS (ou AUJOURD'HUI), puis 3_ANGLAIS (ou B1, B2...)
avec 0,70 s de silence entre chaque prise. Resultat : UN fichier par nom, a
ecouter d'un seul geste.

Il ecrit tout dans un sous-dossier `POUR_ECOUTER/` (les fichiers d'origine ne sont
JAMAIS touches) :
  - `01_Eddard_Stark__CIBLE-FRANCAIS-ANGLAIS.wav` : une prise par nom ;
  - `00_ECOUTER_DANS_L_ORDRE.m3u` : la liste, dans l'ordre, pour un lecteur.

Les noms lisibles sont ceux des fichiers d'origine : rien n'est invente.

LECTURE SEULE sur le projet : il ne touche QUE le dossier du lot. Aucun moteur,
aucun acces Internet, rien de facture.

Usage :
    python test_voix/_grouper_un_lot.py                     (le dernier lot)
    python test_voix/_grouper_un_lot.py <dossier du lot>    (celui-la)
"""

import re
import sys
import wave
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# Les suivis ecrits par les bancs (le plus recent gagne) : c'est ainsi qu'on
# retrouve « le dernier lot » sans rien demander a Laurent.
SUIVIS = ['_dernier_lot_got_auto.txt', '_dernier_lot_prenoms.txt',
          '_dernier_lot_ponctuation.txt']

# Un fichier de lot : « 01_eddard_stark__2_FRANCAIS.wav »
MOTIF = re.compile(r'^(\d+)_(.+?)__(\d+)_(.+)\.wav$', re.IGNORECASE)

PAUSE_S = 0.70          # silence insere entre deux prises


def _dernier_lot():
    """Le dossier du dernier lot fabrique (par les fichiers de suivi des bancs)."""
    trouves = []
    for suivi in SUIVIS:
        fichier = ICI / suivi
        if fichier.is_file():
            chemin = Path(fichier.read_text(encoding='utf-8').strip())
            if chemin.is_dir():
                trouves.append((chemin.stat().st_mtime, chemin))
    if trouves:
        return sorted(trouves, reverse=True)[0][1]
    lots = sorted(ICI.glob('ecoute_*'), key=lambda p: p.stat().st_mtime,
                  reverse=True)
    return lots[0] if lots else None


def _lire_le_lot(dossier):
    """Les groupes du lot : {numero: (nom, [(numero de prise, etiquette, chemin)])}."""
    groupes = {}
    for fichier in sorted(dossier.glob('*.wav')):
        trouve = MOTIF.match(fichier.name)
        if not trouve:
            continue
        groupe, nom, prise, etiquette = trouve.groups()
        groupes.setdefault(int(groupe), (nom, []))[1].append(
            (int(prise), etiquette, fichier))
    for _numero, (_nom, prises) in groupes.items():
        prises.sort()
    return groupes


def _coller(prises, sortie, pause_s=PAUSE_S):
    """Recolle les prises d'un nom en UN fichier, avec un silence entre elles."""
    with wave.open(str(prises[0][2]), 'rb') as premier:
        canaux = premier.getnchannels()
        largeur = premier.getsampwidth()
        taux = premier.getframerate()
    silence = b'\x00' * int(taux * pause_s) * canaux * largeur
    with wave.open(str(sortie), 'wb') as sortie_wav:
        sortie_wav.setnchannels(canaux)
        sortie_wav.setsampwidth(largeur)
        sortie_wav.setframerate(taux)
        for rang, (_numero, _etiquette, chemin) in enumerate(prises):
            with wave.open(str(chemin), 'rb') as entree:
                sortie_wav.writeframes(entree.readframes(entree.getnframes()))
            if rang < len(prises) - 1:
                sortie_wav.writeframes(silence)
    return sortie


def _nom_lisible(nom_de_fichier):
    """« eddard_stark » -> « Eddard Stark » (le nom vient du fichier, rien d'invente)."""
    return nom_de_fichier.replace('_', ' ').title()


def _nettoyer(sortie):
    """Vide le dossier d'ecoute POUR_ECOUTER -- c'est LE dossier de cet outil.

    POURQUOI (16/10/2026) : l'outil doit pouvoir se relancer sans laisser derriere
    lui des fichiers MAL NOMMES -- c'est arrive le jour meme : le libelle d'une
    prise est passe de « ANGLAISE-... » a « CIBLE-ANGLAISE-... », et les treize
    anciens fichiers sont restes dans le dossier (une vraie source d'erreur pour
    Laurent : lequel ouvrir ?).

    DONC : ne mettez RIEN d'autre dans POUR_ECOUTER, tout ce qu'il contient est
    refabrique a chaque passage. Les fichiers D'ORIGINE du lot, eux, sont dans le
    dossier du dessus : ils ne sont JAMAIS touches.
    """
    enleves = []
    for fichier in list(sortie.glob('*.wav')) + list(sortie.glob('*.m3u')):
        fichier.unlink()
        enleves.append(fichier.name)
    return enleves


def _a_lire(sortie, faits, dossier):
    """La petite notice DU dossier d'ecoute : ce qu'on entend, et quoi repondre.

    Si le lot porte sa PROPRE notice (`LISEZ-MOI.txt`, ecrite par le banc qui l'a
    fabrique), c'est elle qui est recopiee : le texte generique ci-dessous parle
    d'un lot de prenoms (trois prises : cible anglaise, francais, anglais) et
    n'aurait aucun sens pour un autre banc.
    """
    notice_du_lot = dossier / 'LISEZ-MOI.txt'
    if notice_du_lot.is_file():
        (sortie / 'A_LIRE.txt').write_text(
            notice_du_lot.read_text(encoding='utf-8'), encoding='utf-8')
        return
    lignes = [
        "A LIRE AVANT D ECOUTER -- %d noms" % len(faits),
        "=" * 60,
        "",
        "Chaque fichier contient TROIS prises du MEME nom, dans cet ordre (le nom",
        "du fichier le redit) :",
        "",
        "    1_CIBLE_anglaise   une VRAIE voix anglaise : le repere",
        "    2_FRANCAIS         le nom tel que le livre l'ecrit",
        "    3_ANGLAIS          la graphie proposee (la formule)",
        "",
        "Il y a 0,70 s de silence entre deux prises : c'est la frontiere.",
        "",
        "CE QU'IL FAUT REPONDRE, NOM PAR NOM :",
        "    « 2 »        mieux en francais",
        "    « 3 »        mieux en anglais",
        "    « pareil »   les deux se valent",
        "    « aucune »   les deux sont a revoir",
        "",
        "Le fichier 00_ECOUTER_DANS_L_ORDRE.m3u les fait defiler TOUS, dans l'ordre,",
        "avec un lecteur (VLC, Media Player...) : un seul double-clic et tu ecoutes",
        "tout le lot d'affilee.",
        "",
        "Les prises d'ORIGINE sont dans le dossier du dessus (%s) : ce dossier-ci"
        % dossier.name,
        "est REFABRIQUE a chaque passage de l'outil, n'y range rien.",
    ]
    (sortie / 'A_LIRE.txt').write_text('\n'.join(lignes) + '\n', encoding='utf-8')


def main():
    if len(sys.argv) > 1:
        dossier = Path(sys.argv[1])
    else:
        dossier = _dernier_lot()
    if not dossier or not dossier.is_dir():
        print('  Aucun dossier de lot trouve.')
        print('  Usage : python test_voix/_grouper_un_lot.py <dossier du lot>')
        return 1

    groupes = _lire_le_lot(dossier)
    if not groupes:
        print('  Aucun fichier de lot dans : %s' % dossier)
        return 1

    sortie = dossier / 'POUR_ECOUTER'
    sortie.mkdir(exist_ok=True)
    enleves = _nettoyer(sortie)
    if enleves:
        print('  (nettoyage : %d ancien(s) fichier(s) fabriques par cet outil)'
              % len(enleves))

    print('=' * 70)
    print('  RECOLLAGE DU LOT POUR L ECOUTE')
    print('=' * 70)
    print('  lot    : %s' % dossier.name)
    print('  sortie : %s' % sortie.name)
    print('  pauses : %.2f s entre deux prises' % PAUSE_S)
    print('')

    faits = []
    for numero in sorted(groupes):
        nom, prises = groupes[numero]
        # Les libelles des prises, dans l'ordre, SANS repeter deux fois de suite
        # le meme : un banc qui tire deux fois la meme variante donnerait sinon
        # « A-AUJOURDHUI-A-AUJOURDHUI » dans le nom du fichier recolle.
        libelles = []
        for _n, etiquette, _c in prises:
            libelle = etiquette.replace('_', '-').upper()
            if not libelles or libelles[-1] != libelle:
                libelles.append(libelle)
        etiquettes = '-'.join(libelles)
        cible = sortie / ('%02d_%s__%s.wav'
                          % (numero, _nom_lisible(nom), etiquettes))
        _coller(prises, cible)
        faits.append(cible)
        print('  %02d  %-24s %d prises  ->  %s'
              % (numero, _nom_lisible(nom), len(prises), cible.name))

    # La liste, dans l'ordre : elle sert a un lecteur (VLC, Media Player...).
    liste = sortie / '00_ECOUTER_DANS_L_ORDRE.m3u'
    lignes = ['#EXTM3U']
    for cible in faits:
        lignes.append('#EXTINF:-1,%s' % cible.stem)
        lignes.append(cible.name)
    liste.write_text('\n'.join(lignes) + '\n', encoding='utf-8')
    _a_lire(sortie, faits, dossier)

    print('')
    print('=' * 70)
    print('  PRET : %d noms, %d fichiers dans  %s'
          % (len(faits), len(faits), sortie))
    print('  Chaque fichier porte les prises DANS L ORDRE annonce par son nom :')
    print('  %s' % faits[0].stem.split('__')[-1])
    print('=' * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())

