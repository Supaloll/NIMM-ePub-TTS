# -*- coding: utf-8 -*-
"""Liste les fichiers du depot Hugging Face du modele Kyutai (lecture seule).

Sert a retrouver le nom EXACT des fichiers -- notamment le codec dedie aux voix
(`*_mimi_voice.safetensors`), dont depend la fabrication des empreintes.
Usage : .venv\\Scripts\\python.exe _lister_depot_modele.py
"""

import sys

sys.stdout.reconfigure(encoding='utf-8')

DEPOT = sys.argv[1] if len(sys.argv) > 1 else 'kyutai/tts-1.6b-en_fr'

from huggingface_hub import list_repo_files  # noqa: E402

print('')
print('=' * 70)
print('FICHIERS DU DEPOT %s' % DEPOT)
print('=' * 70)
for nom in sorted(list_repo_files(repo_id=DEPOT)):
    print('  %s' % nom)
