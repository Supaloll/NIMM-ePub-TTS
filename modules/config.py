# -*- coding: utf-8 -*-
"""
Chargement de la configuration locale (clés API, etc.)
Le fichier data/config.json n'est jamais suivi par Git (voir .gitignore).
"""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise RuntimeError(
            "Fichier data/config.json introuvable. "
            "Cree-le avec : {\"gemini_api_key\": \"ta_cle_ici\"}"
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_gemini_api_key() -> str:
    config = _load_config()
    key = config.get("gemini_api_key", "")
    if not key or key == "COLLE_TA_CLE_ICI":
        raise RuntimeError(
            "La cle Gemini n'est pas configuree dans data/config.json"
        )
    return key


def get_mistral_api_key() -> str:
    config = _load_config()
    key = config.get("mistral_api_key", "")
    if not key or key == "COLLE_TA_CLE_ICI":
        raise RuntimeError(
            "La cle Mistral n'est pas configuree dans data/config.json"
        )
    return key


def get_deepseek_api_key() -> str:
    config = _load_config()
    key = config.get("deepseek_api_key", "")
    if not key or key == "COLLE_TA_CLE_ICI":
        raise RuntimeError(
            "La cle DeepSeek n'est pas configuree dans data/config.json"
        )
    return key


def get_local_model() -> str:
    """
    Modele de langage LOCAL (Ollama) utilise pour le casting hors ligne
    (session du 13/09/2026). Reglable dans data/config.json par la cle
    "local_model" ; une valeur par defaut est utilisee si elle est absente,
    pour que l'application fonctionne sans configuration supplementaire.
    """
    try:
        return _load_config().get("local_model", "qwen2.5:latest")
    except Exception:
        return "qwen2.5:latest"


def get_local_url() -> str:
    """Adresse du service Ollama installe sur le poste (defaut : port 11434)."""
    try:
        return _load_config().get("local_url", "http://127.0.0.1:11434")
    except Exception:
        return "http://127.0.0.1:11434"
