# -*- coding: utf-8 -*-
"""Script JETABLE -- verifie la logique du bouton de bascule des moteurs.

Ce que le script controle, en SIMULATION (rien n'est lance, aucun moteur n'est
allume ni eteint, data\\moteur_voix.txt n'est pas touche) :
  1. la fiche des moteurs : les deux lanceurs, les deux ports, les motifs qui
     permettent de retrouver les processus ;
  2. basculer sur XTTS ETEINT D'ABORD Kyutai : jamais les deux ensemble ;
  3. si l'autre moteur ne peut pas etre eteint, RIEN n'est allume ;
  4. le moteur choisi est note pour le prochain demarrage (relu par START.bat) ;
  5. « aucun » eteint les deux moteurs et le note ;
  6. un moteur deja pret, ou en cours de chargement, n'est pas relance ;
  7. un moteur NON INSTALLE est refuse proprement (aucun lancement) ;
  8. un nom inconnu est refuse, sans rien toucher ;
  9. la route /api/moteur/basculer existe dans l'application.

Methode : les fonctions qui parlent au monde exterieur sont REMPLACEES par des
faux (etat_moteurs_voix, _arreter_moteur_voix, _relancer_moteur_voix,
_moteur_voix_actif, _moteur_voix_installe) et le fichier de reglage est redirige
vers un temoin temporaire. Tout est remis en place a la fin.

A lancer depuis la racine : python test_voix/test_bascule_moteur.py
"""

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

import main

ECHECS = 0
TEMOIN = RACINE / "test_voix" / "_test_moteur_retenu.txt"


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


class FauxMonde:
    """Des moteurs de voix en memoire : rien de reel n'est allume ni eteint.

    `journal` garde l'ORDRE des operations : c'est lui qui prouve que l'autre
    moteur est eteint AVANT que le nouveau soit allume.
    """

    def __init__(self, etats, tuer_ok=True, installe=True):
        self.etats = {p: dict(v) for p, v in etats.items()}
        self.tuer_ok = tuer_ok
        self.installe = installe
        self.journal = []

    # --- ce que main.py appelle ---
    def etat(self, force=False):
        self.journal.append('etat(force=%s)' % force)
        return {p: dict(v) for p, v in self.etats.items()}

    def actif(self, prefixe):
        return bool(self.etats.get(prefixe, {}).get('actif'))

    def arreter(self, prefixe):
        self.journal.append('arreter:' + prefixe)
        if not self.tuer_ok:
            return False
        self.etats[prefixe] = {'actif': False, 'pret': False}
        return True

    def demarrer(self, prefixe):
        self.journal.append('demarrer:' + prefixe)
        self.etats[prefixe] = {'actif': True, 'pret': False}
        return True

    def installe_fn(self, prefixe):
        return self.installe

    def deux_allumes(self):
        return sum(1 for e in self.etats.values() if e.get('actif')) > 1


def preparer(etats, tuer_ok=True, installe=True):
    """Installe le faux monde et redirige le fichier de reglage."""
    monde = FauxMonde(etats, tuer_ok, installe)
    main.etat_moteurs_voix   = monde.etat
    main._arreter_moteur_voix = monde.arreter
    main._relancer_moteur_voix = monde.demarrer
    main._moteur_voix_actif  = monde.actif
    main._moteur_voix_installe = monde.installe_fn
    main.MOTEUR_VOIX_PATH    = TEMOIN
    if TEMOIN.exists():
        TEMOIN.unlink()
    return monde


def reglage_ecrit():
    """Ce que START.bat lira au prochain demarrage (None si rien n'a ete ecrit)."""
    return TEMOIN.read_text(encoding='utf-8') if TEMOIN.exists() else None


# --- 1. La fiche des deux moteurs ---

def test_fiche_des_moteurs():
    print('')
    print('1) la fiche des deux moteurs lourds')
    for prefixe, nom, dossier, lanceur, port in (
            ('xtts', 'XTTS v2', 'xtts_service', 'DEMARRER_XTTS.bat', '8083'),
            ('kyutai', 'Kyutai', 'kyutai_service', 'DEMARRER_KYUTAI.bat', '8082')):
        infos = main.MOTEURS_VOIX.get(prefixe, {})
        verifier('%s : nom, dossier et lanceur' % nom,
                 infos.get('nom') == nom and infos.get('dossier') == dossier
                 and infos.get('lanceur') == lanceur, infos)
        verifier('%s : son adresse de sante est le port %s' % (nom, port),
                 port in infos.get('sante', ''), infos.get('sante'))
        verifier('%s : un motif pour le serveur ET pour sa fenetre' % nom,
                 len(infos.get('motifs', ())) == 2
                 and any(m.startswith('servir_') for m in infos.get('motifs', ()))
                 and any(m.startswith('DEMARRER_') for m in infos.get('motifs', ())),
                 infos.get('motifs'))
    verifier('le fichier de reglage est bien celui que lit START.bat',
             main.MOTEUR_VOIX_PATH.name == 'moteur_voix.txt',
             str(main.MOTEUR_VOIX_PATH))


# --- 2. Basculer eteint l'autre AVANT d'allumer ---

def test_bascule_eteint_l_autre():
    print('')
    print('2) basculer sur XTTS alors que Kyutai est allume')
    monde = preparer({'xtts': {'actif': False, 'pret': False},
                      'kyutai': {'actif': True, 'pret': True}})
    res = main.basculer_moteur_voix('xtts')

    verifier('la bascule reussit', res.get('ok') is True, res)
    verifier('Kyutai est eteint AVANT que XTTS soit lance',
             'arreter:kyutai' in monde.journal and 'demarrer:xtts' in monde.journal
             and monde.journal.index('arreter:kyutai')
             < monde.journal.index('demarrer:xtts'), monde.journal)
    verifier("l'ordre complet est respecte : arret, puis demarrage",
             [o for o in monde.journal if not o.startswith('etat')]
             == ['arreter:kyutai', 'demarrer:xtts'], monde.journal)
    verifier('jamais deux moteurs allumes ensemble', not monde.deux_allumes(),
             monde.etats)
    verifier('le compte rendu dit ce qui a ete fait',
             'eteint' in res.get('message', '')
             and 'demarre' in res.get('message', ''), res.get('message'))
    verifier('le choix est note pour le prochain demarrage',
             reglage_ecrit() == 'xtts\n', repr(reglage_ecrit()))
    verifier('un seul mot dans le fichier (START.bat lit la premiere ligne)',
             (reglage_ecrit() or '').strip().split() == ['xtts'], repr(reglage_ecrit()))
    verifier("l'etat renvoye est frais, pour le bouton",
             bool(res.get('etat')) and res['etat']['xtts']['actif'] is True
             and res['etat']['kyutai']['actif'] is False, res.get('etat'))


# --- 3. Un arret qui echoue : on n'allume RIEN ---

def test_arret_impossible():
    print('')
    print("3) si l'autre moteur ne peut pas etre eteint, rien n'est allume")
    monde = preparer({'xtts': {'actif': False, 'pret': False},
                      'kyutai': {'actif': True, 'pret': True}}, tuer_ok=False)
    res = main.basculer_moteur_voix('xtts')

    verifier('la bascule est refusee', res.get('ok') is False, res)
    verifier("aucun moteur n'a ete lance",
             not [o for o in monde.journal if o.startswith('demarrer')],
             monde.journal)
    verifier("rien n'a ete note pour le prochain demarrage",
             reglage_ecrit() is None, repr(reglage_ecrit()))
    verifier('le message explique pourquoi', 'eteint' in res.get('message', ''),
             res.get('message'))


# --- 4. Rien d'allume : on allume simplement ---

def test_rien_allume():
    print('')
    print('4) basculer quand aucun moteur ne tourne')
    monde = preparer({'xtts': {'actif': False, 'pret': False},
                      'kyutai': {'actif': False, 'pret': False}})
    res = main.basculer_moteur_voix('kyutai')

    verifier('la bascule reussit', res.get('ok') is True, res)
    verifier('aucun arret inutile (rien ne tournait)',
             not [o for o in monde.journal if o.startswith('arreter')],
             monde.journal)
    verifier('Kyutai est lance', 'demarrer:kyutai' in monde.journal, monde.journal)
    verifier('et le choix est note', reglage_ecrit() == 'kyutai\n',
             repr(reglage_ecrit()))


# --- 5. Un moteur deja allume n'est pas relance ---

def test_deja_allume():
    print('')
    print('5) le moteur demande tourne deja : on ne le relance pas')
    preparer({'xtts': {'actif': True, 'pret': True},
              'kyutai': {'actif': False, 'pret': False}})
    res = main.basculer_moteur_voix('xtts')
    verifier('la bascule reussit', res.get('ok') is True, res)
    verifier('aucun nouveau lancement', res.get('demarre') is False, res)
    verifier('le compte rendu dit deja pret',
             'deja pret' in res.get('message', ''), res.get('message'))
    verifier('le choix est tout de meme note', reglage_ecrit() == 'xtts\n',
             repr(reglage_ecrit()))

    print('')
    print('     ... et pendant son chargement ?')
    monde = preparer({'xtts': {'actif': True, 'pret': False},
                      'kyutai': {'actif': False, 'pret': False}})
    res = main.basculer_moteur_voix('xtts')
    verifier('la bascule reussit', res.get('ok') is True, res)
    verifier('on ne relance pas un moteur qui charge',
             not [o for o in monde.journal if o.startswith('demarrer')],
             monde.journal)
    verifier('le compte rendu dit qu\'il finit de charger',
             'charge' in res.get('message', ''), res.get('message'))


# --- 6. Un moteur non installe : refus propre ---

def test_moteur_non_installe():
    print('')
    print("6) un moteur qui n'est pas installe sur ce PC")
    monde = preparer({'xtts': {'actif': False, 'pret': False},
                      'kyutai': {'actif': False, 'pret': False}}, installe=False)
    res = main.basculer_moteur_voix('xtts')

    verifier('la bascule est refusee', res.get('ok') is False, res)
    verifier('le message le dit clairement',
             'installe' in res.get('message', ''), res.get('message'))
    verifier("aucun lancement n'a ete tente",
             not [o for o in monde.journal if o.startswith('demarrer')],
             monde.journal)
    verifier("rien n'a ete note (le prochain demarrage reste inchange)",
             reglage_ecrit() is None, repr(reglage_ecrit()))


# --- 7. « aucun moteur » : les deux eteints ---

def test_aucun_moteur():
    print('')
    print('7) choisir « aucun moteur » (demarrer sans moteur lourd)')
    monde = preparer({'xtts': {'actif': False, 'pret': False},
                      'kyutai': {'actif': True, 'pret': True}})
    res = main.basculer_moteur_voix('aucun')

    verifier('la bascule reussit', res.get('ok') is True, res)
    verifier('le moteur allume a bien ete eteint',
             'arreter:kyutai' in monde.journal, monde.journal)
    verifier('aucun moteur relance',
             not [o for o in monde.journal if o.startswith('demarrer')],
             monde.journal)
    verifier('le reglage dit "aucun"', reglage_ecrit() == 'aucun\n',
             repr(reglage_ecrit()))

    preparer({'xtts': {'actif': False, 'pret': False},
              'kyutai': {'actif': False, 'pret': False}})
    res = main.basculer_moteur_voix('aucun')
    verifier('« aucun » sans moteur allume ne casse rien',
             res.get('ok') is True and reglage_ecrit() == 'aucun\n', res)


# --- 8. Noms de moteur limites ou inconnus ---

def test_noms_limites():
    print('')
    print('8) noms de moteur limites ou inconnus')
    preparer({'xtts': {'actif': False, 'pret': False},
              'kyutai': {'actif': False, 'pret': False}})
    for mauvais in ('', '   ', 'ollama', 'xtts2', 'les deux', 'XTTS v2'):
        res = main.basculer_moteur_voix(mauvais)
        verifier('refus de %r' % mauvais, res.get('ok') is False, res)
    verifier("un nom inconnu n'ecrit rien dans le reglage",
             reglage_ecrit() is None, repr(reglage_ecrit()))
    res = main.basculer_moteur_voix('  XTTS  ')
    verifier('les espaces et les majuscules sont toleres',
             res.get('ok') is True and reglage_ecrit() == 'xtts\n', res)


# --- 9. La route du serveur (celle qu'appelle le bouton) ---

def test_route():
    print('')
    print('9) la route appelee par le bouton existe')
    routes = [(getattr(r, 'path', ''), getattr(r, 'methods', set()) or set())
              for r in main.app.routes]
    chemins = [chemin for chemin, _ in routes]
    verifier('/api/moteur/basculer est declaree',
             '/api/moteur/basculer' in chemins, chemins)
    verifier('elle accepte POST',
             any(c == '/api/moteur/basculer' and 'POST' in m for c, m in routes),
             [sorted(m) for c, m in routes if c == '/api/moteur/basculer'])
    verifier('/api/moteurs (le voyant) est toujours la',
             '/api/moteurs' in chemins)


def main_():
    print('=' * 66)
    print('VERIFICATION : bouton de bascule des moteurs de voix')
    print('=' * 66)
    print('(rien n est lance : les deux moteurs sont simules en memoire)')

    sauve = {}
    for nom in ('etat_moteurs_voix', '_arreter_moteur_voix',
                '_relancer_moteur_voix', '_moteur_voix_actif',
                '_moteur_voix_installe', 'MOTEUR_VOIX_PATH'):
        sauve[nom] = getattr(main, nom)
    try:
        test_fiche_des_moteurs()
        test_bascule_eteint_l_autre()
        test_arret_impossible()
        test_rien_allume()
        test_deja_allume()
        test_moteur_non_installe()
        test_aucun_moteur()
        test_noms_limites()
        test_route()
    finally:
        # Tout est remis comme avant : aucun reglage de Laurent n'est laisse
        # de travers par ce test.
        for nom, valeur in sauve.items():
            setattr(main, nom, valeur)
        if TEMOIN.exists():
            TEMOIN.unlink()

    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    print('(aucun moteur allume ni eteint, fichier temoin nettoye)')
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main_())
