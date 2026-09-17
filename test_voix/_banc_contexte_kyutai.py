# -*- coding: utf-8 -*-
"""Banc d'ecoute : lire une phrase AVEC le contexte de la precedente.

IDEE DE LAURENT (17/09/2026), textuelle : « on envoie A, Kyutai lit, puis pour
la phrase B on lui envoie la toute fin, quelques mots de A, et on ne produit
l'audio que de B. Comme si les bouts se chevauchaient, mais on n'entendrait
toujours qu'une seule phrase, jamais la fin de la precedente. »

POURQUOI CA DEVRAIT MARCHER : un modele de TTS auto-regressif demarre a froid
sur chaque segment -- d'ou la hauteur qui « part » differentment d'une phrase a
l'autre, et les phrases COURTES qui manquent de matiere. En lui donnant la fin
de la phrase precedente, il demarre « en cours de lecture ».

COMMENT ON COUPE : jamais a l'aveugle, toujours DANS UN SILENCE.
  1. on genere le contexte SEUL  -> on note la fin de son dernier son (t1) ;
  2. on genere contexte + phrase -> on cherche le premier silence franc a
     partir de t1 - 250 ms, et on coupe LA (le raccord tombe donc dans un
     silence, jamais au milieu d'un mot).
Le fichier livre contient ensuite les deux versions, a ecouter l'une apres
l'autre : « sans contexte » (aujourd'hui) puis « avec contexte ».

Le moteur Kyutai doit etre allume. Usage :
    python test_voix/_banc_contexte_kyutai.py --livre 28 --chapitre 3
Sortie : test_voix/ecoute_contexte_<date>/ (WAV + index.txt + lanceur)
"""

import argparse
import datetime
import io
import json
import sys
import urllib.request
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _diagnostic_neutts_phrase import chapitre_du_livre, phrases_du_texte  # noqa: E402
from _banc_ecoute_xtts import mesurer                                    # noqa: E402

SERVICE = "http://127.0.0.1:8084"      # mis a jour par --moteur
MOTEURS = {'kyutai': 'http://127.0.0.1:8082', 'neutts': 'http://127.0.0.1:8084'}
# Longueur du contexte : les derniers MOTS de la phrase precedente.
MOTS_CONTEXTE = 6
# On accepte de reculer un peu avant t1 pour tomber sur un vrai silence.
MARGE_RECHERCHE_S = 0.25
SILENCE_MIN_S = 0.12
SEUIL = 0.012


def lire_echantillons(octets):
    """(frequence, array d'entiers) d'un WAV."""
    import array

    with wave.open(io.BytesIO(octets), "rb") as fichier:
        frequence = fichier.getframerate()
        brut = fichier.readframes(fichier.getnframes())
    echantillons = array.array('h')
    echantillons.frombytes(brut)
    return frequence, echantillons


def ecrire_wav(frequence, echantillons):
    """Reconstruit un WAV 16 bits mono a partir d'echantillons."""
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(frequence)
        fichier.writeframes(echantillons.tobytes())
    return tampon.getvalue()


def blocs_parles(frequence, echantillons, pas_s=0.01):
    """[(debut, fin)] des blocs de son audible, en secondes."""
    pas = max(1, int(pas_s * frequence))
    blocs = []
    for debut in range(0, len(echantillons), pas):
        bloc = echantillons[debut:debut + pas]
        if bloc and max(abs(v) for v in bloc) / 32768.0 >= SEUIL:
            if blocs and debut - blocs[-1][1] <= pas * 1.5:
                blocs[-1] = (blocs[-1][0], debut + len(bloc))
            else:
                blocs.append((debut, debut + len(bloc)))
    return [(a / float(frequence), b / float(frequence)) for a, b in blocs]


def ou_couper(contexte, phrase, voix):
    """L'audio de la phrase seule, generee AVEC le contexte devant.

    Renvoie (wav, explication) : on genere le contexte seul pour connaitre la
    fin de son dernier son, puis `contexte + phrase` et on coupe dans le
    premier silence franc qui suit. La phrase n'est donc jamais amputee, et le
    raccord ne tombe jamais au milieu d'un mot.
    """
    wav_contexte = demander(contexte, voix)
    frequence, echantillons = lire_echantillons(wav_contexte)
    blocs = blocs_parles(frequence, echantillons)
    fin_contexte = blocs[-1][1] if blocs else 0.0

    wav_long = demander(contexte + ' ' + phrase, voix)
    frequence, echantillons = lire_echantillons(wav_long)
    blocs = blocs_parles(frequence, echantillons)

    limite = fin_contexte - MARGE_RECHERCHE_S
    coupe = None
    for rang in range(1, len(blocs)):
        silence = blocs[rang][0] - blocs[rang - 1][1]
        if silence >= SILENCE_MIN_S and blocs[rang][0] >= limite:
            coupe = blocs[rang - 1][1]        # fin du dernier son du contexte
            break
    if coupe is None:
        # Aucun silence franc trouve : on coupe a la fin mesuree du contexte
        # (moins sur qu'un silence, mais on ne perd pas la phrase).
        coupe = fin_contexte
    debut = max(0, int(coupe * frequence))
    return (ecrire_wav(frequence, echantillons[debut:]),
            'contexte %.2f s, coupe a %.2f s' % (fin_contexte, coupe))


def contexte_de(phrase, mots=MOTS_CONTEXTE):
    """Le contexte pris dans une phrase.

    `mots` = 0 -> la phrase ENTIERE (question de Laurent : « je ne sais pas
    s'il faut une phrase complete ou si la fin de la phrase precedente
    suffit ») ; sinon, ses `mots` derniers mots.
    """
    if mots <= 0:
        return phrase
    morceaux = phrase.split()
    return ' '.join(morceaux[-mots:]) if len(morceaux) > mots else phrase


def demander(texte, voix):
    """Un texte au service du moteur (comme le fait le lecteur)."""
    corps = json.dumps({"texte": texte, "voix": voix}).encode('utf-8')
    requete = urllib.request.Request(
        SERVICE + "/tts", data=corps,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=180) as reponse:
        return reponse.read()


def main():
    global SERVICE

    analyseur = argparse.ArgumentParser(
        description="Banc d'ecoute : la meme phrase, avec et sans contexte.")
    analyseur.add_argument('--moteur', default='kyutai',
                           choices=('kyutai', 'neutts'))
    analyseur.add_argument('--livre', type=int, default=28)
    analyseur.add_argument('--chapitre', type=int, default=3)
    analyseur.add_argument('--texte-fichier', default=None,
                           help="un passage fourni (un fichier, une phrase par "
                                "ligne) au lieu d'un chapitre du livre")
    analyseur.add_argument('--mots', default='6,0',
                           help="longueurs de contexte a comparer, separees par "
                                "des virgules ; 0 = la phrase precedente ENTIERE "
                                "(defaut : 6,0)")
    analyseur.add_argument('--voix', default=None,
                           help="voix du moteur (defaut : la plus bavarde du livre)")
    analyseur.add_argument('--phrases', type=int, default=4,
                           help="combien de phrases consecutives tester")
    options = analyseur.parse_args()

    SERVICE = MOTEURS[options.moteur]
    variantes = [int(m) for m in options.mots.split(',') if m.strip() != '']

    voix = options.voix
    if not voix:
        try:
            from _diagnostic_neutts_phrase import voix_du_livre
            prefixe = 'kyutai:' if options.moteur == 'kyutai' else 'neutts:'
            liste = voix_du_livre(options.livre, prefixe)
            voix = liste[0][0].split(':', 1)[1] if liste else None
        except Exception:
            voix = None
    if not voix:
        print('ERR : aucune voix trouvee (donnez --voix).')
        return 1

    if options.texte_fichier:
        source = Path(options.texte_fichier)
        if not source.is_file():
            print('ERR : fichier introuvable : %s' % source)
            return 1
        texte = source.read_text(encoding='utf-8')
        titre = source.name
    else:
        texte, titre, erreur = chapitre_du_livre(options.livre, options.chapitre)
        if erreur:
            print('ERR : %s' % erreur)
            return 1
    phrases = [p for p in phrases_du_texte(texte) if len(p.split()) >= 4]
    if len(phrases) < options.phrases + 1:
        print('ERR : pas assez de phrases (il en faut %d apres la premiere).'
              % options.phrases)
        return 1

    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = (Path(__file__).resolve().parent
               / ('ecoute_contexte_%s' % horodatage))
    dossier.mkdir(parents=True, exist_ok=True)

    print('')
    print('=' * 78)
    print('PHRASE SEULE  contre  PHRASE AVEC CONTEXTE (plusieurs longueurs)')
    print('=' * 78)
    print('moteur : %s   voix : %s' % (options.moteur, voix))
    print('texte  : %s' % titre)
    print('contextes testes : %s'
          % ', '.join(('phrase entiere' if m == 0 else '%d mots' % m)
                      for m in variantes))
    print('dossier : %s' % dossier.name)

    lignes = ["BANC D'ECOUTE — PHRASE SEULE contre PHRASE AVEC CONTEXTE", '',
              'texte : %s' % titre, 'voix : %s' % voix, '',
              "Chaque phrase est lue plusieurs fois, DANS CET ORDRE :",
              "  _seule    = la phrase seule (ce que fait le lecteur aujourd'hui)",
              "  _ctx6     = avec les 6 derniers mots de la phrase precedente",
              "  _ctx0     = avec la phrase precedente ENTIERE",
              "(la partie de contexte n'est jamais entendue : la coupe tombe",
              "dans un silence, et seule la phrase est gardee).", '',
              "LA QUESTION : quelle version est la mieux posee, la plus stable,",
              "la plus 'chantee' ? La phrase precedente entiere apporte-t-elle",
              "quelque chose de plus que sa fin ?", '']

    rang = 0
    for index in range(1, options.phrases + 1):
        phrase = phrases[index]
        print('')
        print('  phrase %d : « %s »' % (index, phrase[:64]))

        rang += 1
        seul = demander(phrase, voix)
        nom = '%02d_p%d_seule.wav' % (rang, index)
        (dossier / nom).write_bytes(seul)
        duree, segments, _res = mesurer(seul)
        print('    %02d %-26s %6.2fs | %d segment(s)' % (rang, 'seule', duree,
                                                         len(segments)))
        lignes.append('%02d  phrase %d SEULE : « %s »' % (rang, index, phrase[:70]))
        lignes.append('     mesure : %.2f s, %d segment(s)' % (duree, len(segments)))

        for mots in variantes:
            rang += 1
            contexte = contexte_de(phrases[index - 1], mots)
            etiquette = 'contexte phrase entiere' if mots == 0 else ('contexte %d mots' % mots)
            nom = '%02d_p%d_ctx%d.wav' % (rang, index, mots)
            try:
                avec, detail = ou_couper(contexte, phrase, voix)
            except Exception as erreur_tts:
                print('    %02d %-26s ECHEC : %s' % (rang, etiquette, erreur_tts))
                continue
            (dossier / nom).write_bytes(avec)
            duree2, segments2, _r2 = mesurer(avec)
            print('    %02d %-26s %6.2fs | %d segment(s)  (%s)'
                  % (rang, etiquette, duree2, len(segments2), detail))
            lignes.append('%02d  la MEME, %s : « %s… » devant'
                          % (rang, etiquette, contexte[:45]))
            lignes.append('     mesure : %.2f s, %d segment(s)  (%s)'
                          % (duree2, len(segments2), detail))
        lignes.append('')

    lignes.append("GRILLE : 1 diction qui accroche · 2 debit irregulier · 3 mot")
    lignes.append("invente · 4 gargouillis · 5 prosodie qui repart.")
    lignes.append("Dis surtout : SEULE, CTX6 ou CTX0 ? et pourquoi.")
    (dossier / 'index.txt').write_text('\n'.join(lignes), encoding='utf-8')
    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    print('')
    print('Index  : %s' % (dossier / 'index.txt'))
    print('Ecouter: double-clic sur ECOUTER_LE_LOT.cmd')
    return 0


if __name__ == '__main__':
    sys.exit(main())

