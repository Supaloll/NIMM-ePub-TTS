# -*- coding: utf-8 -*-
"""MIGRER LES PETITS ROLES vers les deux voix generiques (Jessica / Pierre).

Decision de Laurent, 21/09/2026 : tout personnage de MOINS de 8 repliques est
joue par une voix generique selon son genre -- Jessica (femmes) et Pierre
(hommes), les deux en Piper -- et CHAQUE petit role en recoit une VARIANTE
differentielle par sa hauteur et sa vitesse (11 x 13 = 143 combinaisons
possibles pour une meme voix, voir PITCH_VARIANTES dans voice_casting.py).

Cet outil applique cette decision aux livres DEJA CASTES, et il ne touche a
RIEN d'autre :
    - seules les lignes de moins de 8 repliques (MINOR_THRESHOLD) sont visees ;
    - les lignes VERROUILLEES sont laissees telles quelles (un verrou = « je
      garde cette voix ») ;
    - la VOIX, la HAUTEUR et la VITESSE sont ecrites ENSEMBLE : la variante est
      repartie par livre ET par genre, dans l'ordre de traitement (les
      personnages les plus presents d'abord), pour que deux petits roles d'un
      meme livre n'aient jamais le meme couple (hauteur, vitesse). Au-dela de
      143 petits roles d'un meme genre dans un livre, on recommence au debut
      (accepte par Laurent) ;
    - les roles de 8 repliques et plus ne sont pas regardes du tout ;
    - rien n'est supprime, rien n'est ajoute.

SECURITE : l'outil ne fait rien tant qu'on ne le lui demande pas -- il montre
d'abord ce qu'il ferait (mode « essai »). Avec --appliquer, il fait
AUTOMATIQUEMENT une copie datee de la base AVANT d'ecrire (via l'API de
sauvegarde de SQLite, donc une copie coherente meme si le lecteur tourne) et
il imprime le nom de cette copie : c'est le retour arriere.

Usage :
    python test_voix/migrer_petits_roles.py             (essai, n'ecrit rien)
    python test_voix/migrer_petits_roles.py --appliquer (ecrit, avec copie)
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules.voice_casting import (MINOR_THRESHOLD, GENERIC_VOICE_F,
                                   GENERIC_VOICE_M, _voix_generique,
                                   _variante_generique, NB_VARIANTES_GENERIQUES,
                                   PITCH_VARIANTES, RATE_VARIANTES)

BASE = RACINE / 'data' / 'nimm_epub.db'


def _voix_dans_le_catalogue(voice_id: str) -> bool:
    """La voix existe-t-elle dans le catalogue ?

    On lit le SOURCE de modules/tts.py au lieu d'importer le moteur : ce script
    ne doit rien charger de lourd, et il tourne pendant que le lecteur travaille.
    Une faute de frappe sur l'identifiant rendrait un casting muet : mieux vaut
    le refuser ici.
    """
    source = (RACINE / 'modules' / 'tts.py').read_text(encoding='utf-8')
    return ('"id": "%s"' % voice_id) in source


def _nom_voix(voice_id: str) -> str:
    """Nom lisible d'une voix generique, pour les comptes rendus."""
    if voice_id == GENERIC_VOICE_F:
        return 'Jessica'
    if voice_id == GENERIC_VOICE_M:
        return 'Pierre'
    return voice_id


def _plan(cur):
    """Ce que l'outil ecrirait : [(book_id, nom, voix, hauteur, vitesse)].

    Seules les lignes de moins de MINOR_THRESHOLD repliques, NON verrouillees,
    d'un livre existant, et dont la voix, la hauteur ou la vitesse ne sont pas
    encore celles prevues : l'outil est donc REJOUABLE (une ligne deja conforme
    n'est pas retouchee).

    La VARIANTE (hauteur, vitesse) est repartie par livre ET par genre, dans
    l'ordre de traitement (les plus presents d'abord, puis par nom) : deux
    petits roles d'un meme livre ne peuvent donc pas avoir le meme couple,
    jusqu'a NB_VARIANTES_GENERIQUES (143) par genre. Au-dela, on recommence au
    debut -- c'est voulu et accepte (deux petits roles partageraient alors
    exactement la meme voix).
    """
    cur.execute("""
        SELECT v.book_id, v.character_name, v.voice_id, v.genre, v.line_count,
               v.pitch, v.rate
          FROM voices v
         WHERE v.line_count < ?
           AND (v.locked IS NULL OR v.locked = 0)
           AND v.book_id IN (SELECT id FROM books)
         ORDER BY v.book_id, v.line_count DESC, v.character_name
    """, (MINOR_THRESHOLD,))
    rangs = {}
    plan = []
    for book_id, nom, voice_id, genre, _n, pitch, rate in cur.fetchall():
        cle = (book_id, 'F' if genre == 'F' else 'H')
        rang = rangs.get(cle, 0)
        rangs[cle] = rang + 1
        voix = _voix_generique(genre)
        hauteur, vitesse = _variante_generique(rang)
        if (voice_id or '', pitch or '', rate or '') != (voix, hauteur, vitesse):
            plan.append((book_id, nom, voix, hauteur, vitesse))
    return plan


def _compte_non_touche(cur) -> tuple:
    """(lignes verrouillees, lignes de livres supprimes) : ce qu'on laisse."""
    cur.execute('SELECT COUNT(*) FROM voices WHERE line_count < ? AND locked = 1',
                (MINOR_THRESHOLD,))
    verrouillees = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM voices WHERE line_count < ? '
                'AND book_id NOT IN (SELECT id FROM books)', (MINOR_THRESHOLD,))
    orphelines = cur.fetchone()[0]
    return verrouillees, orphelines


def main():
    appliquer = '--appliquer' in sys.argv

    print('=' * 68)
    print(' PETITS ROLES : une voix par genre, et une VARIANTE chacun')
    print('   femmes -> Jessica = %s   |   hommes -> Pierre = %s'
          % (GENERIC_VOICE_F, GENERIC_VOICE_M))
    print('   seuil : moins de %d repliques' % MINOR_THRESHOLD)
    print('   variantes : %d hauteurs x %d vitesses = %d par voix'
          % (len(PITCH_VARIANTES), len(RATE_VARIANTES), NB_VARIANTES_GENERIQUES))
    print('=' * 68)

    manquantes = [v for v in (GENERIC_VOICE_F, GENERIC_VOICE_M)
                  if not _voix_dans_le_catalogue(v)]
    if manquantes:
        print('ARRET : voix absente(s) du catalogue : %s' % ', '.join(manquantes))
        return 2

    con = sqlite3.connect('file:' + str(BASE) + '?mode=ro', uri=True)
    cur = con.cursor()
    lignes = _plan(cur)
    titres = dict(cur.execute('SELECT id, title FROM books'))
    verrouillees, orphelines = _compte_non_touche(cur)

    par_livre = {}
    for book_id, nom, voix, hauteur, vitesse in lignes:
        par_livre.setdefault(book_id, []).append((nom, voix, hauteur, vitesse))

    print('')
    print('%d ligne(s) a mettre en forme, livre par livre :' % len(lignes))
    for book_id in sorted(par_livre, key=lambda b: (titres.get(b) or '')):
        ex = par_livre[book_id]
        print('   %-42s %3d ligne(s)'
              % ((titres.get(book_id) or '?')[:42], len(ex)))
        for nom, voix, hauteur, vitesse in ex[:3]:
            print('        %-26s %-8s hauteur %5s | vitesse %5s'
                  % (nom[:26], _nom_voix(voix), hauteur, vitesse))

    print('')
    print('Laissees telles quelles (jamais touchees) :')
    print('   %5d ligne(s) VERROUILLEE(S) -- un verrou veut dire « je garde »'
          % verrouillees)
    print('   %5d ligne(s) de livres supprimes (invisibles dans l application)'
          % orphelines)
    con.close()

    if not lignes:
        print('')
        print('Rien a faire : tout est deja conforme.')
        return 0

    if not appliquer:
        print('')
        print('MODE ESSAI : rien n a ete ecrit.')
        print('Pour appliquer pour de vrai, lancer MIGRER_PETITS_ROLES.bat')
        return 0

    # --- Copie datee AVANT d'ecrire : c'est le retour arriere ----------------
    horodate = datetime.now().strftime('%Y%m%d_%H%M')
    copie = BASE.with_name(BASE.name + '.bak_avant_petits_roles_' + horodate)
    source = sqlite3.connect(str(BASE))
    cible = sqlite3.connect(str(copie))
    with cible:
        source.backup(cible)
    cible.close()
    source.close()
    print('')
    print('Copie de la base faite AVANT d ecrire : ' + copie.name)

    # --- Ecriture : une seule colonne, une seule transaction ----------------
    con = sqlite3.connect(str(BASE))
    con.execute('PRAGMA busy_timeout = 20000')
    cur = con.cursor()
    changees = 0
    for book_id, nom, voix, hauteur, vitesse in lignes:
        cur.execute('UPDATE voices SET voice_id = ?, pitch = ?, rate = ? '
                    'WHERE book_id = ? AND character_name = ?',
                    (voix, hauteur, vitesse, book_id, nom))
        changees += cur.rowcount
    con.commit()

    # --- Controle : on relit ce qui vient d'etre ecrit ----------------------
    restantes = len(_plan(cur))
    cur.execute('SELECT COUNT(*) FROM voices WHERE voice_id IN (?, ?)',
                (GENERIC_VOICE_F, GENERIC_VOICE_M))
    porteurs = cur.fetchone()[0]
    con.close()

    print('')
    print('Ecrit : %d ligne(s) mises a jour.' % changees)
    print('Controle : %d ligne(s) restant a mettre en forme (doit valoir 0).'
          % restantes)
    print('Controle : %d ligne(s) portent maintenant une voix generique.' % porteurs)
    print('Hauteurs et vitesses : REPARTIES (chaque petit role a sa variante).')
    print('Pense a RECHARGER la page du lecteur pour voir (et entendre) le '
          'nouveau casting.')
    print('Retour arriere : remplacer data/%s par %s' % (BASE.name, copie.name))
    return 0 if restantes == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

