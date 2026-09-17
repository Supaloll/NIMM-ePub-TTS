# -*- coding: utf-8 -*-
"""Verifie le re-cast avec l'IA (etape 2) SANS appeler aucune IA.

Ce qui est verifie :
  1. le CADRE : l'IA ne peut choisir que parmi les voix que le re-cast par
     criteres autorise deja -- une voix notee 0 etoile ne peut donc JAMAIS
     lui etre proposee (c'est le garde-fou de conception) ;
  2. le PROMPT : chaque personnage y figure avec ses repliques, chaque voix
     avec sa description, et la consigne interdit de repeter une voix ;
  3. la LECTURE DE LA REPONSE : voix inventees, mauvais genres, doublons et
     personnages inconnus sont ECARTES, avec la raison ;
  4. le DECOUPAGE des phrases d'un chapitre suit celui de la page : verifie sur
     un VRAI livre caste, en comparant les indices de `speaker_attribution` au
     nombre de phrases trouvees (sinon les repliques montrees a l'IA seraient
     celles d'un autre personnage) ;
  5. la ROUTE existe et partage sa preparation avec le re-cast gratuit ;
  6. les PETITS ROLES ne sont pas soumis a l'IA.

Aucun appel reseau, aucune ecriture : ce test est gratuit et sans risque.
Usage : python test_voix/test_recaste_ia.py
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding='utf-8')

from modules import voice_casting as vc                     # noqa: E402

ECHECS = 0


def verifier(nom, condition, detail=''):
    global ECHECS
    if condition:
        print('  OK    ' + nom)
    else:
        print('  ECHEC ' + nom + ('  -> ' + str(detail) if detail else ''))
        ECHECS += 1


PERSONNAGES = [
    {"nom": "Eustace Osgris", "genre": "H", "age": "age", "repliques": 362,
     "repliques_texte": ["Viens la, gamin.", "Je te nomme ecuyer."]},
    {"nom": "L'Oeuf", "genre": "H", "age": "jeune", "repliques": 120,
     "repliques_texte": ["Je ne suis pas un gamin."]},
    {"nom": "Rohanne Tyssier", "genre": "F", "age": "adulte", "repliques": 90,
     "repliques_texte": ["Je gouverne ce chateau."]},
]


def test_cadre():
    print('')
    print('1) le cadre des voix proposees (le garde-fou de conception)')
    proposables = vc.voix_proposees_pour(PERSONNAGES)
    verifier('des voix sont proposees pour les deux genres',
             bool(proposables.get('H')) and bool(proposables.get('F')))
    index = vc._index_voix()
    zero = [v["id"] for v in proposables.get('H', []) + proposables.get('F', [])
            if int(index.get(v["id"], {}).get("stars") or 0) <= 0]
    verifier('aucune voix notee 0 etoile n est proposee a l IA', not zero,
             zero[:3])
    proposables_h = {v["id"] for v in proposables.get('H', [])}
    verifier('aucune voix de femme n est proposee pour un homme',
             not any(i.startswith(('kokoro:ff', 'kokoro:af', 'kokoro:bf'))
                     for i in proposables_h))
    verifier('les descriptions portent la description et les etoiles',
             all('(' in v["description"] and 'etoile' in v["description"]
                 for v in proposables.get('H', [])[:5]),
             proposables.get('H', [])[:1])
    exclusions = {v["id"] for v in proposables.get('H', [])}
    filtre = vc.voix_proposees_pour(PERSONNAGES, exclues=exclusions)
    verifier('une voix exclue (verrou) n est plus proposee',
             not (exclusions & {v["id"] for v in filtre.get('H', [])}))
    return proposables


def test_prompt(proposables):
    print('')
    print('2) le prompt envoye au modele')
    prompt = vc.construire_prompt_recaste_ia(PERSONNAGES, proposables)
    verifier('chaque personnage est dans le prompt',
             all(p["nom"] in prompt for p in PERSONNAGES))
    verifier('les repliques du personnage y sont',
             'Viens la, gamin.' in prompt)
    verifier('les identifiants de voix proposes y sont',
             proposables['H'][0]["id"] in prompt)
    verifier('la consigne interdit de repeter une voix',
             'deux fois' in prompt.lower())
    verifier('la consigne exige le bon genre', 'BON GENRE' in prompt)
    verifier('le format de reponse est demande en JSON',
             '"attributions"' in prompt)
    verifier('le prompt ne depasse pas une taille raisonnable',
             len(prompt) < 40000, len(prompt))


def test_lecture(proposables):
    print('')
    print('3) la lecture de la reponse du modele')
    bonne_femme = proposables['F'][0]["id"]
    # Pour eprouver le refus des doublons, il faut une voix AUTORISEE pour les
    # DEUX personnages masculins : une voix reservee aux personnages ages ne
    # l'est pas, et le refus viendrait alors d'ailleurs (c'est ce que le test a
    # montre du premier coup).
    autorisees_age = set(vc._classement_voix("H", "age"))
    bon = next((i for i in vc._classement_voix("H", "jeune")
                if i in autorisees_age), proposables['H'][0]["id"])
    reponse = {"attributions": [
        {"personnage": "Eustace Osgris", "voix": bon},
        {"personnage": "L'Oeuf", "voix": bon},                 # doublon
        {"personnage": "Rohanne Tyssier", "voix": bonne_femme},
        {"personnage": "Inconnu Total", "voix": bon},          # inconnu
        {"personnage": "L'Oeuf", "voix": "neutts:inventee"},   # voix inventee
        "pas un objet",                                        # entree illisible
    ]}
    attributions, problemes = vc.lire_attributions_ia(reponse, PERSONNAGES)
    verifier('une voix n est donnee qu une seule fois', len(attributions) == 2,
             attributions)
    verifier('le doublon est ecarte et explique',
             any('deux fois' in p for p in problemes), problemes)
    verifier('le personnage inconnu est ecarte et explique',
             any('inconnu' in p for p in problemes), problemes)
    verifier('une voix inventee est refusee',
             any('non proposee' in p for p in problemes), problemes)
    verifier('une entree illisible ne casse rien',
             any('illisible' in p for p in problemes), problemes)
    verifier('les deux attributions valides sont gardees',
             attributions.get('Eustace Osgris') == bon
             and attributions.get('Rohanne Tyssier') == bonne_femme)

    variantes, _ = vc.lire_attributions_ia(
        {"attributions": [{"personnage": "  eustace osgris ", "voix": bon}]},
        PERSONNAGES)
    verifier('une variante d ecriture du nom est retrouvee',
             list(variantes) == ['Eustace Osgris'], variantes)

    en_dict, _ = vc.lire_attributions_ia(
        {"attributions": {"Eustace Osgris": bon}}, PERSONNAGES)
    verifier('une reponse en dictionnaire est acceptee',
             en_dict.get('Eustace Osgris') == bon, en_dict)

    vide, _ = vc.lire_attributions_ia({}, PERSONNAGES)
    verifier('une reponse vide ne casse rien', vide == {})
    # Une voix d'un AUTRE genre est refusee : c'est ce qui protege du modele
    # qui « entend » une voix de femme pour un personnage masculin.
    faux, problemes_faux = vc.lire_attributions_ia(
        {"attributions": [{"personnage": "L'Oeuf", "voix": bonne_femme}]},
        PERSONNAGES)
    verifier('une voix du mauvais genre est refusee', not faux, faux)


def test_decoupage_reel():
    print('')
    print('4) le decoupage des phrases suit celui de la page (vrai livre caste)')
    import main
    conn = main.get_db()
    livre = conn.execute(
        "SELECT id, filename, saga FROM books WHERE cast_status = 'done' "
        "ORDER BY id LIMIT 1").fetchone()
    if not livre:
        print('    (aucun livre caste : controle saute)')
        conn.close()
        return
    rows = conn.execute(
        "SELECT character_name, line_count FROM voices WHERE book_id = ?",
        (livre["id"],)).fetchall()
    personnages = [{"nom": r["character_name"], "genre": "H", "age": "adulte"}
                   for r in rows if (r["line_count"] or 0) >= 8]
    extraits, ecartes = main._repliques_des_personnages(conn, livre, personnages)
    conn.close()
    print('    livre %s : %d personnage(s) soumis, %d avec extraits, '
          '%d chapitre(s) ecarte(s)'
          % (livre["id"], len(personnages), len(extraits), len(ecartes)))
    verifier('des repliques sont retrouvees', bool(extraits), len(extraits))
    # Les repliques ne sont lues que dans les PREMIERS chapitres (travail
    # borne) : on ne peut donc pas exiger la couverture de tout le livre. Ce
    # qui compte est qu'il y en ait, et que ce qui est lu soit juste.
    verifier('plusieurs personnages ont leurs repliques',
             len(extraits) >= 3, len(extraits))
    verifier('aucun extrait vide', all(extraits.values()))
    verifier('peu de chapitres sont ecartes', len(ecartes) <= 2, sorted(ecartes))
    if extraits:
        nom = sorted(extraits)[0]
        print('    exemple -- %s : %s' % (nom, extraits[nom][0][:88]))


def test_route_et_garde_fous():
    print('')
    print('5) la route, le partage du code et les garde-fous')
    source = (RACINE / "main.py").read_text(encoding="utf-8")
    verifier('la route /cast/reassign_ia existe',
             '/cast/reassign_ia' in source)
    verifier('les DEUX re-casts partagent la preparation',
             'def _preparer_recaste' in source
             and source.count('_preparer_recaste(') >= 3,
             source.count('_preparer_recaste('))
    verifier('les petits roles ne sont pas soumis a l IA',
             'MINOR_THRESHOLD' in source)
    verifier('le re-cast par IA ne touche pas aux verrous',
             'if head["locked"]:' in source)
    verifier('tout ce que l IA rend est verifie avant ecriture',
             source.index('attribuer_voix_avec_ia')
             < source.index('"par_ia": par_ia'))
    verifier('la page propose le second bouton',
             'cast-recast-ia-btn' in (RACINE / "frontend" / "index.html")
             .read_text(encoding="utf-8"))
    app = (RACINE / "frontend" / "app.js").read_text(encoding="utf-8")
    verifier('la page appelle la nouvelle route', 'reassign_ia' in app)
    verifier('la page previent que c est payant (avec le cout estime)',
             'centimes' in app)


def main():
    print('=' * 70)
    print("VERIFICATION : re-cast avec l'IA (sans appeler l'IA)")
    print('=' * 70)
    proposables = test_cadre()
    test_prompt(proposables)
    test_lecture(proposables)
    test_decoupage_reel()
    test_route_et_garde_fous()
    print('')
    print('TOUT EST OK' if ECHECS == 0
          else '%d VERIFICATION(S) EN ECHEC' % ECHECS)
    return 0 if ECHECS == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
