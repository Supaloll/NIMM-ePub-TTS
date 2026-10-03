# -*- coding: utf-8 -*-
"""BANC DE REGLAGES POCKET : quelle TEMPERATURE donne la voix de A sans ses trous ?

POURQUOI (30/09/2026). Apres avoir ecoute les deux modeles francais, Laurent a
tranche, mot pour mot : « Le B est mieux dans la mesure ou les raccords sont
meilleurs. Mais A est de meilleure qualite. Le A a un probleme de coupure /
collage / raccord de phrases : soit il fait une pause au moment de la coupure,
soit il repete 2 fois le meme mot. [...] Je dirais A, parce que les voix sont
quand meme meilleures, mais il faut reussir a coller les morceaux de phrases
correctement. »

Ce que la MESURE a dit sur ses 6 WAV (`_analyser_raccords_audio.py`) :
  - A (24 couches) : 18 silences internes, dont un de 2,02 s -- la phrase 1
    dure 13,4 s avec 4,7 s de silence, la meme phrase en B en fait 8,3 s avec
    0,4 s de silence ;
  - B (6 couches) : 7 silences internes, aucun au-dela de 0,60 s.
Le defaut de A est donc MESURE, et il est dans le MODELE (le banc ne recolle
rien : chaque WAV est UN appel au moteur).

CE QUE CE BANC CHERCHE : le reglage du modele A qui garde ses voix mais se
comporte comme B. Le seul levier accessible sans toucher au moteur est la
TEMPERATURE d'echantillonnage (`temp`, celle du service aujourd'hui : 0,3).
L'atelier NIMM Voix avait note le meme genre d'effet sur NeuTTS (temperature a
1,0 = repetitions et pauses parasites). Donc on balaie :

    0,30 (aujourd'hui) | 0,50 | 0,70 (le defaut du paquet) | 0,90

Chaque temperature passe sur les MEMES 3 phrases reelles de livre, avec
PLUSIEURS tirages (le moteur n'a pas de graine : deux tirages ne se ressemblent
jamais). Chaque WAV est ensuite MESURE par l'analyseur de raccords : nombre de
silences internes, silence le plus long, duree -- donc le banc ne se contente
pas de poser des fichiers a ecouter, il COMPTE les defauts.

LE VERDICT RESTE A L'OREILLE (regle de l'atelier : un moteur se juge en
ecoutant), mais les compteurs disent ou chercher.

CE QU'IL NE FAIT PAS : aucune modification de la base, des voix, du service ou
du lecteur. Le seul acces reseau est le cache Hugging Face (les deux modeles y
sont deja depuis le 30/09).

Usage (le lanceur double-clic fait tout) :
    python test_voix/_banc_reglages_pocket.py
    python test_voix/_banc_reglages_pocket.py --temperatures 0.3,0.5,0.7 --tirages 3
    python test_voix/_banc_reglages_pocket.py --variantes a      (seulement le 24 couches)
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
sys.path.insert(0, str(DOSSIER))

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

from _mesurer_debit_pocket import (          # noqa: E402
    COEURS, PORT_SERVICE, PHRASES, TOKENS, VARIANTES,
    charger_modele, duree_du_wav, ecrire_wav, memoire_mo, service_allume)
from _analyser_raccords_audio import analyser_fichier   # noqa: E402

# Le seuil qui separe une respiration normale d'un TROU : une virgule vaut
# 0,2 a 0,4 s, une hesitation de modele vaut plus d'une demi-seconde. C'est ce
# seuil qui decide du verdict PROPRE / FAUTIF dans le rapport.
SEUIL_TROU_S = 0.50
# Second critere, plus sensible : les silences internes de 0,15 s et plus sont
# COMPTES (le rapport donne les deux chiffres).
SEUIL_MESURE_S = 0.15


def mesurer_prise(chemin, caracteres=0):
    """Les defauts d'un WAV deja ecrit : trous (fiables), indices, debit.

    HONNETETE (lecon du 30/09/2026) : les deux criteres ne se valent pas.
      - les TROUS (silence interne de SEUIL_TROU_S ou plus) sont MESURES sans
        ambiguite : c'est ce qui fait le verdict PROPRE / FAUTIF ;
      - les REPETITIONS sont des INDICES : testes sur les trois exemples ecoutes
        par Laurent, les detecteurs ont rate celle qu'il a entendue dans la
        phrase 2 du 6 couches et signale un faux positif dans la phrase 1 du
        meme modele (« beaucoup plus fluide » pour lui). Ils sont donc COMPTES
        A PART (a ecouter), jamais un verdict a eux seuls ;
      - le DEBIT DE PAROLE (caracteres par seconde de parole, silences exclus)
        dit la VARIABILITE d'un tirage, et il aide a reperer le tirage qui
        s'ecarte de ses camarades. ATTENTION, hypothese DEMENTIE le 30/09/2026 :
        on croyait qu'une repetition rallongeait la prise -- mesure sur la
        phrase 2 du 6 couches, la prise ou Laurent a entendu la repetition
        (« mais ne sachant, mais ne sachant comment ») a un debit PLUS BAS
        (20,3 car./s) que ses camarades (23,4). Conclusion a garder : AUCUNE de
        nos mesures ne detecte les repetitions de facon fiable ; seule
        l'oreille le peut pour l'instant (une transcription automatique serait
        la vraie solution -- piste a ouvrir, elle n'est pas installee).
    """
    fiche = analyser_fichier(chemin, SEUIL_MESURE_S)
    silences = [duree for _, duree in fiche['silences']]
    plus_long = max(silences) if silences else 0.0
    trous = [duree for duree in silences if duree >= SEUIL_TROU_S]
    parole = (fiche['duree'] - sum(silences) - fiche['tete'] - fiche['queue'])
    repetitions = (len(fiche['suspects']) + len(fiche['repetitions'])
                   + len(fiche['reprises']))
    debit = (caracteres / parole) if (caracteres and parole > 0) else 0.0
    return {'duree': fiche['duree'], 'parole': parole,
            'silences': len(silences), 'plus_long': plus_long, 'trous': len(trous),
            'repetitions': repetitions, 'debit': debit,
            'verdict': 'PROPRE' if not trous else 'FAUTIF'}


def balayer_variante(etiquette, court, facon, valeur, temperatures, tirages,
                     voix, dossier, dire):
    """Une variante de modele, toutes les temperatures, tous les tirages."""
    dire('')
    dire('=' * 78)
    dire('MODELE %s -- %s' % (etiquette, court))
    dire('=' * 78)

    debut = time.time()
    modele = charger_modele(facon, valeur, temp=temperatures[0])
    dire('  chargement : %.1f s' % (time.time() - debut))
    debut = time.time()
    etat = modele.get_state_for_audio_prompt(str(voix))
    dire('  voix encodee : %.1f s' % (time.time() - debut))

    resultats = []
    for temperature in temperatures:
        # `temp` est un simple attribut du modele : on le change SANS recharger
        # (chaque chargement coute 5 a 20 s sur cette machine).
        modele.temp = temperature
        sous_dossier = dossier / ('%s_%s' % (etiquette, court)) / ('T%03d'
                                                                  % round(temperature * 100))
        sous_dossier.mkdir(parents=True, exist_ok=True)
        dire('')
        dire('  temperature %.2f' % temperature)
        dire('     %-8s %5s %8s %9s %9s %5s %7s  %s'
             % ('phrase', 'tir.', 'duree', 'silences', 'le + long', 'rep.',
                'car./s', 'verdict'))
        for numero, (nom, texte) in enumerate(PHRASES, start=1):
            for tirage in range(1, tirages + 1):
                debut = time.time()
                audio = modele.generate_audio(etat, texte, max_tokens=TOKENS)
                calcul = time.time() - debut
                chemin = sous_dossier / ('p%d_T%03d_t%02d.wav'
                                         % (numero, round(temperature * 100), tirage))
                ecrire_wav(chemin, audio.detach().cpu().numpy(), modele.sample_rate)
                mesure = mesurer_prise(chemin, len(texte))
                mesure.update({'temperature': temperature, 'phrase': nom,
                               'tirage': tirage, 'calcul': calcul,
                               'fichier': chemin})
                resultats.append(mesure)
                dire('     %-8s %5d %7.2f s %9d %8.2f s %5d %6.1f  %s'
                     % (nom, tirage, mesure['duree'], mesure['silences'],
                        mesure['plus_long'], mesure['repetitions'],
                        mesure['debit'], mesure['verdict']))

    del modele
    return resultats


def bilan_par_temperature(etiquette, court, resultats, dire):
    """Le classement des temperatures de cette variante."""
    dire('')
    dire('  BILAN %s -- %s (sur %d prises)'
         % (etiquette, court, len(resultats)))
    dire('     %-7s %7s %9s %9s %6s %8s'
         % ('temp.', 'duree', 'silences', 'le + long', 'rep.', 'fautives'))
    temperatures = []
    for mesure in resultats:
        if mesure['temperature'] not in temperatures:
            temperatures.append(mesure['temperature'])
    gagnantes = []
    for temperature in temperatures:
        prises = [m for m in resultats if m['temperature'] == temperature]
        fautives = [m for m in prises if m['verdict'] == 'FAUTIF']
        avec_repetition = [m for m in prises if m['repetitions']]
        moyenne_silences = statistics.mean(m['silences'] for m in prises)
        plus_long = max(m['plus_long'] for m in prises)
        moyenne_duree = statistics.mean(m['duree'] for m in prises)
        dire('     %-7.2f %6.2f s %9.1f %8.2f s %6d %5d / %d'
             % (temperature, moyenne_duree, moyenne_silences, plus_long,
                len(avec_repetition), len(fautives), len(prises)))
        gagnantes.append((len(fautives), len(avec_repetition), plus_long,
                          temperature))
    gagnantes.sort()
    dire('')
    dire('     La plus sage : temperature %.2f (%d prise(s) fautive(s) : '
         'trous OU repetitions, %d avec repetition, silence le plus long '
         '%.2f s)'
         % (gagnantes[0][3], gagnantes[0][0], gagnantes[0][1], gagnantes[0][2]))
    dire('     ATTENTION : le classement ne juge que les TROUS. La voix, la')
    dire('     prosodie et la clarte se jugent a l\'oreille -- les WAV sont')
    dire('     ranges par temperature, un dossier par temperature.')


def tirer_les_plus_sains(resultats, dire):
    """Par temperature et par phrase, QUEL tirage est le plus sain ?

    C'est le coeur de la strategie du 30/09/2026 : le moteur n'est pas
    deterministe, donc une repetition ou un trou n'appartient qu'a UNE prise --
    en re-tirant, on a de bonnes chances d'en obtenir une propre. Reste a
    choisir sans oreille : on retient un tirage SANS TROU dont le debit de
    parole est le plus proche de la mediane de ses camarades (une repetition
    allonge la prise, donc s'ecarte de la mediane).
    """
    dire('')
    dire('  TIRAGES LES PLUS SAINS (ni trou, debit le plus proche de la mediane)')
    temperatures = []
    for mesure in resultats:
        if mesure['temperature'] not in temperatures:
            temperatures.append(mesure['temperature'])
    for temperature in temperatures:
        dire('')
        dire('     temperature %.2f' % temperature)
        phrases = []
        for mesure in resultats:
            if mesure['phrase'] not in phrases:
                phrases.append(mesure['phrase'])
        for phrase in phrases:
            prises = [m for m in resultats
                      if m['temperature'] == temperature and m['phrase'] == phrase]
            debits = [m['debit'] for m in prises if m['debit']]
            if not debits:
                continue
            mediane = statistics.median(debits)
            candidats = [m for m in prises if m['verdict'] == 'PROPRE'] or prises
            retenu = min(candidats, key=lambda m: abs(m['debit'] - mediane))
            ecart = 100.0 * (retenu['debit'] - mediane) / mediane if mediane else 0.0
            dire('       %-8s -> %s (debit %.1f car./s, ecart a la mediane '
                 '%+.0f %%)'
                 % (phrase, retenu['fichier'].name, retenu['debit'], ecart))
            autres = [m for m in prises if m is not retenu]
            if autres:
                dire('                  autres tirages : %s'
                     % ', '.join('%s %.1f car./s%s'
                                 % (m['fichier'].name, m['debit'],
                                    '' if m['verdict'] == 'PROPRE' else ' (TROU)')
                                 for m in autres))


def main():
    analyseur = argparse.ArgumentParser(
        description='Banc de reglages Pocket TTS : quelle temperature fait '
                    'disparaitre les trous du modele 24 couches ?')
    analyseur.add_argument('--temperatures', default='0.3,0.5,0.7,0.9',
                           help='temperatures a balayer (defaut : 0.3,0.5,0.7,0.9)')
    analyseur.add_argument('--tirages', type=int, default=3,
                           help='tirages par phrase et par temperature (defaut : 3)')
    analyseur.add_argument('--variantes', default='a,b',
                           help='a = 24 couches (les voix de Laurent), '
                                'b = 6 couches (les raccords propres)')
    analyseur.add_argument('--voix',
                           default=str(RACINE / 'pocket_tts_service' / 'voix'
                                       / 'Femme001_reference.wav'),
                           help='WAV de reference de la voix')
    analyseur.add_argument('--sortie', default='',
                           help='dossier des WAV (defaut : un dossier date)')
    options = analyseur.parse_args()

    lignes = []

    def dire(texte):
        print(texte)
        lignes.append(texte)

    temperatures = []
    for morceau in options.temperatures.split(','):
        morceau = morceau.strip()
        if not morceau:
            continue
        try:
            temperatures.append(float(morceau))
        except ValueError:
            dire('ERR : temperature illisible : %s' % morceau)
            return 1
    if not temperatures:
        dire('ERR : aucune temperature a balayer.')
        return 1

    demandees = [lettre.strip().lower()
                 for lettre in options.variantes.split(',') if lettre.strip()]
    a_faire = [v for v in VARIANTES if v[0].lower() in demandees]
    if not a_faire:
        dire('ERR : aucune variante a mesurer (--variantes a,b).')
        return 1

    if not Path(options.voix).is_file():
        dire('ERR : la voix %s n\'existe pas.' % options.voix)
        return 1

    if service_allume():
        dire('')
        dire('Le service Pocket TTS REPOND deja sur le port %d.' % PORT_SERVICE)
        dire('Ferme sa fenetre, puis relance ce banc : sinon les deux se')
        dire('partageraient les coeurs et les chiffres ne voudraient rien dire.')
        return 1

    horodatage = time.strftime('%Y%m%d_%H%M')
    dossier = (Path(options.sortie) if options.sortie
               else DOSSIER / ('banc_reglages_pocket_%s' % horodatage))
    dossier.mkdir(parents=True, exist_ok=True)

    dire('')
    dire('=' * 78)
    dire('BANC DE REGLAGES POCKET -- la voix de A, les raccords de B ?')
    dire('=' * 78)
    dire('temperatures   : %s' % ', '.join('%.2f' % t for t in temperatures))
    dire('tirages/phrase : %d' % options.tirages)
    dire('modeles        : %s' % ', '.join(
        '%s = %s' % (v[0], v[1]) for v in a_faire))
    dire('voix           : %s' % options.voix)
    dire('reglages       : %d coeurs, max_tokens %d (ceux du service)' % (COEURS, TOKENS))
    dire('trou compte a partir de %.2f s de silence interne' % SEUIL_TROU_S)
    dire('')
    dire('  Cela fait %d prises en tout, et chaque prise est MESUREE en sortie.'
         % (len(a_faire) * len(temperatures) * options.tirages * len(PHRASES)))

    tous = {}
    for variante in a_faire:
        etiquette, court, facon, valeur = variante
        resultats = balayer_variante(etiquette, court, facon, valeur,
                                     temperatures, options.tirages,
                                     Path(options.voix), dossier, dire)
        tous[etiquette] = (court, resultats)
        bilan_par_temperature(etiquette, court, resultats, dire)
        tirer_les_plus_sains(resultats, dire)

    dire('')
    dire('=' * 78)
    dire("CE QU'IL FAUT FAIRE MAINTENANT : ECOUTER")
    dire('=' * 78)
    dire('  Les WAV sont ranges un dossier par modele et par temperature :')
    for etiquette, (court, _) in tous.items():
        base = dossier / ('%s_%s' % (etiquette, court))
        dire('    %s : %s' % (etiquette, base))
    dire('')
    dire("  La bonne facon d'ecouter : prendre UNE phrase, et passer les")
    dire("  temperatures dans l'ordre (T030, T050, T070, T090), plusieurs")
    dire('  tirages. Deux questions, dans cet ordre :')
    dire('    1. les trous (la pause au milieu, le mot qui repart) ont-ils')
    dire("       disparu ?  -> c'est ce que les compteurs disent deja ;")
    dire('    2. la voix est-elle restee celle de A ?')
    dire('')
    dire('FIN -- rien n\'a ete modifie (ni base, ni voix, ni service).')

    (dossier / 'RAPPORT.txt').write_text('\n'.join(lignes), encoding='utf-8')
    # Repère pour le lanceur double-clic : sans lui, il devait DEVINER le nom du
    # dossier (date a la minute) et le 30/09/2026 il n'a rien ouvert du tout --
    # Laurent a cherche ses fichiers a la main. Meme solution que le recousu.
    (DOSSIER / '_dernier_banc.txt').write_text(str(dossier), encoding='utf-8')
    print('')
    print('Rapport ecrit : %s' % (dossier / 'RAPPORT.txt'))
    return 0


if __name__ == '__main__':
    sys.exit(main())

