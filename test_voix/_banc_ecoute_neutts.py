# -*- coding: utf-8 -*-
"""Banc d'ecoute NeuTTS : ou ca derape, et pourquoi.

Objectif (echange du 17/09/2026) : Laurent juge la lecture NeuTTS « trop
aleatoire en qualite ». Ce banc ne cherche pas a le contredire : il cherche a
savoir SI le defaut vient du TEXTE envoye, et LEQUEL des trois suspects.

Trois suspects, un volet chacun :
  1. LES SIGNES DE DIALOGUE. Le service XTTS retire les guillemets « » et
     traite le tiret cadratin avant l'envoi (mesure du 15/09 : sinon le moteur
     les PRONONCE, « ogui ... haa »). Le service NeuTTS, lui, ne nettoie RIEN :
     il recoit les signes tels quels. On ecoute donc la MEME phrase avec :
        A_brut      -- ce que NeuTTS recoit aujourd'hui ;
        B_xtts      -- nettoyee comme XTTS (guillemets retires, tiret retire) ;
        C_ouvrant   -- guillemets : on garde l'ouvrant, on retire le fermant.
  2. LES PHRASES COURTES, ou le modele a trop peu de contexte.
  3. LA RECOLLURE : le service decoupe toute unite de plus de ~200 caracteres
     en morceaux, genere chacun SEPAREMENT (sa propre attaque, sa propre fin)
     et les recolle sans silence. On ecoute la meme phrase (a) d'un bloc, et
     (b) coupee en deux requetes -- ce qui reproduit la recollure.
Plus un volet SUR TON LIVRE : de vraies phrases d'un chapitre, avec les voix
reelles de son casting.

Le moteur NeuTTS doit etre allume (neutts_service\\DEMARRER_NEUTTS.bat).
Le banc est A DECOUVERT (les noms disent ce qu'on ecoute) : c'est une seance
de COMPREHENSION, pas de tri a l'aveugle. Usage :

    python test_voix/_banc_ecoute_neutts.py --livre 34 --chapitre 6
Sortie : test_voix/ecoute_neutts_<date>/ (WAV + index.txt + ECOUTER_LE_LOT.cmd)
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

from _banc_ecoute_xtts import mesurer                      # noqa: E402
from _diagnostic_neutts_phrase import (                    # noqa: E402
    chapitre_du_livre, phrases_du_texte, nettoyage_xtts, voix_du_livre)
from _rapprocher_neutts_xtts import entrees_du_catalogue   # noqa: E402

SERVICE = "http://127.0.0.1:8084"
# Le meme banc sait interroger les DEUX moteurs neuronaux qui partagent les
# memes extraits de voix (identifiants identiques) : NeuTTS (8084) et Kyutai
# (8082). C'est ce qui permet de comparer les deux sur les MEMES phrases et les
# MEMES voix -- la seule comparaison honnete entre deux moteurs.
MOTEURS = {
    'neutts': {'url': 'http://127.0.0.1:8084', 'prefixe': 'neutts:',
               'demarreur': 'neutts_service\\DEMARRER_NEUTTS.bat',
               'catalogue': 'NEUTTS_VOICES'},
    'kyutai': {'url': 'http://127.0.0.1:8082', 'prefixe': 'kyutai:',
               'demarreur': 'kyutai_service\\DEMARRER_KYUTAI.bat',
               'catalogue': 'KYUTAI_VOICES'},
}
URL_SERVICE = MOTEURS['neutts']['url']

# Deux voix du livre, plus une voix dont la REFERENCE vient d'ailleurs (extrait
# Kokoro) : c'est la piste « la qualite depend de l'extrait de reference ».
VOIX_LIVRE = 2          # combien de voix du casting on prend
VOIX_MULTIPLES = 6      # ... et combien pour le volet « quelles voix derapent »


def demander(texte, voix):
    """Envoie un texte au moteur neuronal choisi (comme le fait le lecteur)."""
    corps = json.dumps({"texte": texte, "voix": voix}).encode('utf-8')
    requete = urllib.request.Request(
        URL_SERVICE + "/tts", data=corps,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(requete, timeout=600) as reponse:
        return reponse.read()


def coller(wav_a, wav_b):
    """Recolle deux WAV (meme format), comme le fait le service entre morceaux."""
    import array

    def lire(octets):
        with wave.open(io.BytesIO(octets), "rb") as f:
            return (f.getframerate(), f.getnchannels(), f.getsampwidth(),
                    array.array('h', f.readframes(f.getnframes())))

    freq, canaux, largeur, a = lire(wav_a)
    freq2, canaux2, largeur2, b = lire(wav_b)
    if (freq, canaux, largeur) != (freq2, canaux2, largeur2):
        return wav_a                     # formats differents : on n'essaie pas
    sortie = io.BytesIO()
    with wave.open(sortie, "wb") as f:
        f.setnchannels(canaux)
        f.setsampwidth(largeur)
        f.setframerate(freq)
        f.writeframes((a + b).tobytes())
    return sortie.getvalue()


def couper_en_deux(texte):
    """Coupe un texte en deux morceaux, a une virgule ou au milieu."""
    for separateur in (', ', '; ', ': '):
        position = texte.rfind(separateur, len(texte) // 3, 2 * len(texte) // 3)
        if position > 0:
            return texte[:position + len(separateur)].strip(), texte[position + len(separateur):].strip()
    milieu = len(texte) // 2
    position = texte.find(' ', milieu)
    if position < 0:
        return texte, ''
    return texte[:position].strip(), texte[position:].strip()


def sante(service):
    try:
        with urllib.request.urlopen(service + "/sante", timeout=5) as reponse:
            return json.loads(reponse.read().decode('utf-8'))
    except Exception:
        return None


# Phrase cobaye de dialogue, avec ses variantes de nettoyage.
PHRASE_GUILLEMETS = "« Vous êtes bien sûr de vous, monseigneur ? » demanda-t-elle."
PHRASE_TIRET = "— Je ne sais pas, répondit-il doucement, et il détourna les yeux."
PHRASES_COURTES = ["Non.", "— Oui.", "Manger ?", "Il partit."]


def variantes(texte):
    """Les trois facons d'envoyer la meme phrase au moteur."""
    ouvert = texte
    # C_ouvrant : on garde le guillemet OUVrant, on retire le fermant.
    for signe in ('\u00bb', '"', '\u201c', '\u201d'):
        ouvert = ouvert.replace(signe, ' ')
    # ... et pour un tiret de dialogue, on le remplace par une virgule.
    if ouvert.lstrip()[:1] in ('\u2014', '\u2013'):
        ouvert = ouvert.lstrip()[1:]
    ouvert = ', '.join(ouvert.split()).replace(', «', ' «')
    return [('A_brut', texte, 'tel quel : ce que NeuTTS recoit aujourd hui'),
            ('B_xtts', nettoyage_xtts(texte),
             'nettoye comme XTTS : guillemets et tiret retires'),
            ('C_ouvrant', ouvert,
             'guillemet ouvrant conserve, fermant retire')]


def cas_cobayes():
    """Les cas pieges, avec ce qu'on cherche a entendre."""
    cas = []
    for etiquette, phrase in (('G_guillemets', PHRASE_GUILLEMETS),
                              ('T_tiret', PHRASE_TIRET)):
        for suffixe, texte, note in variantes(phrase):
            cas.append({'code': '%s_%s' % (etiquette, suffixe),
                        'texte': texte, 'note': note, 'voix': None,
                        'famille': 'signes'})
    for rang, phrase in enumerate(PHRASES_COURTES, 1):
        cas.append({'code': 'C%d_courte' % rang, 'texte': phrase, 'voix': None,
                    'note': 'phrase courte : peu de contexte',
                    'famille': 'courtes'})
    return cas


def cas_recollure(unite_longue):
    """La meme phrase : d'un bloc, puis coupee en deux (la recollure)."""
    if not unite_longue:
        return []
    debut, fin = couper_en_deux(unite_longue)
    return [{'code': 'R1_d_un_bloc', 'texte': unite_longue, 'voix': None,
             'note': 'le service la decoupe et recolle lui-meme (%d car.)'
                     % len(unite_longue), 'famille': 'recollure'},
            {'code': 'R2_en_deux_requetes',
             'texte': '%s ||| %s' % (debut, fin), 'voix': None,
             'note': 'DEUX requetes au moteur, recollees ici (a comparer a R1)',
             'famille': 'recollure', 'couper': True}]


def cas_du_livre(unites):
    """De vraies phrases du chapitre : un dialogue, puis de la narration."""
    dialogue = next((u for u in unites
                     if u.lstrip()[:1] in ('\u2014', '\u2013')), None)
    guillemets = next((u for u in unites if '\u00ab' in u), None)
    narration = next((u for u in unites
                      if 80 <= len(u) <= 200
                      and u.lstrip()[:1] not in ('\u2014', '\u2013')
                      and '\u00ab' not in u), None)
    cas = []
    for code, texte, note in (('L1_dialogue_tiret', dialogue,
                               'une vraie replique du chapitre (tiret)'),
                              ('L2_dialogue_guillemets', guillemets,
                               'une vraie replique du chapitre (guillemets)'),
                              ('L3_narration', narration,
                               'une phrase de narration du chapitre')):
        if texte:
            cas.append({'code': code, 'texte': texte, 'voix': None,
                        'note': note, 'famille': 'livre'})
    return cas


def cas_par_voix(voix):
    """Les MEMES phrases courtes, lues par chaque voix du livre.

    But : savoir si le defaut tient a la PHRASE ou a la VOIX. Si une voix
    derape sur tout et une autre sur rien, la cause est dans son extrait de
    reference (et sa transcription) -- et la solution est de changer cet
    extrait, pas de retoucher le texte.
    """
    cas = []
    for rang, nom in enumerate(voix, 1):
        for etiquette, phrase in (('p1_non', PHRASES_COURTES[0]),
                                  ('p2_oui', PHRASES_COURTES[1]),
                                  ('p3_manger', PHRASES_COURTES[2]),
                                  ('p4_partit', PHRASES_COURTES[3])):
            cas.append({'code': 'V%d_%s' % (rang, etiquette), 'texte': phrase,
                        'voix': nom, 'famille': 'voix',
                        'note': 'phrase courte, voix V%d' % rang})
    return cas


def main():
    global URL_SERVICE

    analyseur = argparse.ArgumentParser(
        description="Banc d'ecoute NeuTTS : les cas pieges et un extrait du livre.")
    analyseur.add_argument('--livre', type=int, default=None,
                           help="numero du livre (obligatoire pour le volet « ton livre »)")
    analyseur.add_argument('--chapitre', type=int, default=0,
                           help="numero du chapitre (0 = premier)")
    analyseur.add_argument('--voix', default=None,
                           help="forcer UNE voix (identifiant, avec ou sans neutts:)")
    analyseur.add_argument('--moteur', default='neutts',
                           choices=('neutts', 'kyutai'),
                           help="moteur neuronal a interroger (neutts ou kyutai) : "
                                "les deux partagent les memes extraits de voix")
    analyseur.add_argument('--volet', default='complet',
                           choices=('complet', 'voix'),
                           help="complet (defaut) ou voix : les memes phrases "
                                "courtes lues par plusieurs voix du livre")
    options = analyseur.parse_args()

    reglages = MOTEURS[options.moteur]
    URL_SERVICE = reglages['url']
    etat = sante(URL_SERVICE)
    if not etat:
        print("Le moteur %s ne repond pas sur %s." % (options.moteur, URL_SERVICE))
        print("Double-clique sur %s, puis relance." % reglages['demarreur'])
        return 1
    if not etat.get('pret'):
        print("Le moteur %s n'est pas encore charge (quelques dizaines de"
              % options.moteur)
        print("secondes apres l'allumage) : relance dans un moment.")
        return 1
    print("Moteur %s pret -- appareil %s, graine %s."
          % (options.moteur, etat.get('appareil'), etat.get('graine')))

    # --- Les voix : celles du livre, ou celle demandee ---
    if options.voix:
        voix = [options.voix.split(':', 1)[-1]]
    elif options.livre is not None:
        voix = [v.split(':', 1)[1]
                for v, _n in voix_du_livre(options.livre, reglages['prefixe'])]
        if not voix:
            # Le livre n'a AUCUNE voix de ce moteur (toutes basculees, par
            # exemple) : on reprend les voix NeuTTS du casting. Les deux moteurs
            # partagent les memes extraits, donc les memes identifiants -- c'est
            # exactement ce qui rend la comparaison possible.
            voix = [v.split(':', 1)[1]
                    for v, _n in voix_du_livre(options.livre, 'neutts:')]
            print("(ce livre n'a plus de voix %s : on reprend celles du casting "
                  "NeuTTS,\n memes identifiants -- c'est ce qui permet de "
                  "comparer.)" % options.moteur)
        # ... en ne gardant que celles qui existent VRAIMENT chez ce moteur.
        connues = set(entrees_du_catalogue(reglages['catalogue']))
        gardees = [v for v in voix
                   if (reglages['prefixe'] + v) in connues]
        if len(gardees) < len(voix):
            print("  (%d voix du casting n'existent pas chez %s : ecartees)"
                  % (len(voix) - len(gardees), options.moteur))
        voix = gardees
        maximum = VOIX_MULTIPLES if options.volet == 'voix' else VOIX_LIVRE
        voix = voix[:maximum] or ['12205_11650_000004-0002']
    else:
        voix = ['12205_11650_000004-0002']
    print("Voix du banc : %s" % ', '.join(voix))

    # --- Le chapitre (pour le volet « ton livre ») ---
    unites, titre = [], '(aucun livre fourni)'
    if options.livre is not None:
        texte, titre, erreur = chapitre_du_livre(options.livre, options.chapitre)
        if erreur:
            print('')
            print('ERR : %s' % erreur)
            return 1
        unites = phrases_du_texte(texte)
        print("Chapitre : %s (%d unites)" % (titre, len(unites)))

    longue = next((u for u in unites if len(u) > 250), None)
    if options.volet == 'voix':
        cas = cas_par_voix(voix)
        print("Volet VOIX : %d phrases courtes x les voix du livre"
              % len(PHRASES_COURTES))
    else:
        cas = cas_du_livre(unites) + cas_cobayes() + cas_recollure(longue)

    horodatage = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    dossier = Path(__file__).resolve().parent / (
        'ecoute_%s_%s' % (options.moteur, horodatage))
    dossier.mkdir(parents=True, exist_ok=True)
    print('')
    print('Dossier : %s' % dossier.name)
    print('=' * 74)
    return _generer(options, cas, voix, dossier, titre)


def _generer(options, cas, voix, dossier, titre):
    """Genere les WAV, mesure, et ecrit l'index + le lanceur d'ecoute."""
    lignes = ["BANC D'ECOUTE %s -- %s"
              % (options.moteur.upper(),
                 datetime.datetime.now().strftime('%d/%m/%Y %H:%M')), '']
    if options.livre is not None:
        lignes.append('Livre %s, chapitre %s : %s'
                      % (options.livre, options.chapitre, titre))
        lignes.append('')
    lignes.append("COMMENT ECOUTER (dans cet ordre) :")
    if options.volet == 'voix':
        lignes.append("  Chaque voix lit LES MEMES 4 phrases courtes, a la suite.")
        lignes.append("  But : dire quelles VOIX derapent et lesquelles sont propres.")
        lignes.append('')
        for rang, nom in enumerate(voix, 1):
            lignes.append('  V%d = %s' % (rang, nom))
        lignes.append('')
    else:
        lignes.append("  01 a 03 : TON LIVRE -- c'est le mieux place pour dire si ce")
        lignes.append("            que tu entends ressemble a ce qui t'a gene.")
        lignes.append("  puis G_ et T_ : la MEME phrase avec et sans les signes de")
        lignes.append("            dialogue (A brut / B nettoye / C ouvrant seul).")
        lignes.append("  puis R_ : la meme phrase d'un bloc, puis coupee en deux")
        lignes.append("            (deux requetes au moteur, recollees).")
        lignes.append("  puis C_ : les phrases trop courtes.")
        lignes.append('')

    rang = 0
    for cas_courant in cas:
        code = cas_courant['code']
        textes = (cas_courant['texte'].split(' ||| ')
                  if cas_courant.get('couper') else [cas_courant['texte']])
        if cas_courant.get('voix'):
            voix_du_cas = [cas_courant['voix']]
        elif cas_courant['famille'] == 'livre':
            voix_du_cas = voix
        else:
            voix_du_cas = voix[:1]
        for index, nom_voix in enumerate(voix_du_cas):
            rang += 1
            try:
                if len(textes) == 2:
                    wav = coller(demander(textes[0], nom_voix),
                                 demander(textes[1], nom_voix))
                    detail = '2 requetes (%d + %d car.)' % (len(textes[0]),
                                                            len(textes[1]))
                else:
                    wav = demander(cas_courant['texte'], nom_voix)
                    detail = '%d car.' % len(cas_courant['texte'])
            except Exception as erreur:
                print('%02d %-24s ECHEC : %s' % (rang, code, erreur))
                continue
            duree, segments, residu = mesurer(wav)
            suffixe = ('_v%d' % (index + 1)) if cas_courant['famille'] == 'livre' else ''
            nom_fichier = '%02d_%s%s.wav' % (rang, code, suffixe)
            (dossier / nom_fichier).write_bytes(wav)
            silences = [round(segments[i][0] - segments[i - 1][1], 2)
                        for i in range(1, len(segments))
                        if (segments[i][0] - segments[i - 1][1]) >= 0.20]
            print('%02d %-24s %-22s %5.2fs | %d segment(s) %s'
                  % (rang, code, nom_voix[:22], duree, len(segments),
                     ('| silences %s' % silences) if silences else ''))
            lignes.append('%02d  %s' % (rang, nom_fichier))
            lignes.append('    %s' % code)
            lignes.append('    voix %s -- %s' % (nom_voix, detail))
            lignes.append('    %s' % cas_courant['note'])
            lignes.append('    texte exact : %s'
                          % cas_courant['texte'].replace(' ||| ', '  //  '))
            lignes.append('    mesure : %.2f s, %d segment(s) de parole, '
                          'residu %.2f s%s'
                          % (duree, len(segments), residu,
                             (', silences internes %s' % silences)
                             if silences else ''))
            lignes.append('')

    lignes.append("GRILLE DE NOTATION (donne-moi juste les numeros) :")
    lignes.append("  1  diction qui accroche (un mot bizarre, une syllabe avalee)")
    lignes.append("  2  debit irregulier (ca accelere ou ralentit dans la phrase)")
    lignes.append("  3  mot invente")
    lignes.append("  4  gargouillis / bruit parasite")
    lignes.append("  5  prosodie qui repart en milieu de phrase (recollure)")
    lignes.append("  exemple : « 07 : 1 5 ; 12 : 2 » = le 07 accroche ET repart,")
    lignes.append("  le 12 a un debit irregulier.")
    (dossier / 'index.txt').write_text('\n'.join(lignes), encoding='utf-8')

    (dossier / 'ECOUTER_LE_LOT.cmd').write_text(
        '@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0index.txt"\r\n'
        'explorer "%~dp0"\r\n', encoding='utf-8')

    print('')
    print('Index   : %s' % (dossier / 'index.txt'))
    print('Ecouter : double-clic sur ECOUTER_LE_LOT.cmd')
    return 0


if __name__ == '__main__':
    sys.exit(main())
