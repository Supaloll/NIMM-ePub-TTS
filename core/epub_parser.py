# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import re
import struct
import html
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

# ==============================================================
# UTILITAIRES INTERNES
# ==============================================================

def _html_to_text(html_content: str) -> str:
    """
    Convertit le HTML d'un chapitre EPUB en texte propre.
    Gere les retours a la ligne internes aux paragraphes
    (frequents sur les EPUB convertis depuis papier).
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Supprime scripts et styles
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Remplace les <br> par un espace
    for br in soup.find_all("br"):
        br.replace_with(" ")

    # Ajoute un marqueur unique apres chaque bloc de paragraphe
    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4"]):
        tag.append("\n§¶§\n")

    text = soup.get_text()

    # Decoupe aux marqueurs de paragraphe
    raw_paragraphs = text.split("\n§¶§\n")

    cleaned_paragraphs = []
    for para in raw_paragraphs:
        # Collapse tous les sauts de ligne internes en espace simple
        # (corrige les EPUB avec retours à la ligne de page papier)
        para = re.sub(r'[ \t]*\n[ \t]*', ' ', para)
        # Supprime les espaces multiples
        para = re.sub(r' {2,}', ' ', para)
        # Decode les entites HTML residuelles (&agrave; → à, etc.)
        para = html.unescape(para)
        para = para.strip()
        if len(para) > 1:
            cleaned_paragraphs.append(para)

    return "\n\n".join(cleaned_paragraphs)


def _extract_chapter_title(html_content: str, fallback: str) -> str:
    """Cherche un titre dans le HTML du chapitre."""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in ["h1", "h2", "h3", "title"]:
        el = soup.find(tag)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return fallback


def _is_content_document(item) -> bool:
    """Filtre les documents qui contiennent du vrai texte (pas les nav, toc, etc.)"""
    name = item.get_name().lower()
    excluded = ["toc", "nav", "ncx", "cover"]
    for ex in excluded:
        if ex in name:
            return False
    return True


def sniff_image_type(data: bytes):
    """Detecte le type d'une image a partir de ses magic bytes.
    Retourne 'png', 'jpg', 'gif', 'webp' ou None si inconnu.
    """
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _image_dimensions(data: bytes):
    """Retourne (largeur, hauteur) en pixels, ou (None, None)."""
    # PNG : IHDR en-tete, largeur/hauteur en big-endian
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return w, h

    # JPEG : scan des marqueurs jusqu'au SOF (SOF0/SOF2, etc.)
    if data[:3] == b"\xff\xd8\xff":
        i = 2
        n = len(data)
        sof = (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
               0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)
        while i + 9 < n:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in sof:
                h = (data[i + 5] << 8) | data[i + 6]
                w = (data[i + 7] << 8) | data[i + 8]
                return w, h
            if marker == 0xD8 or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = (data[i + 2] << 8) | data[i + 3]
            if length < 2:
                break
            i += 2 + length

    # GIF : largeur/hauteur en little-endian
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        w = struct.unpack("<H", data[6:8])[0]
        h = struct.unpack("<H", data[8:10])[0]
        return w, h

    # WEBP (conteneur VP8X : dimensions canvas 24 bits little-endian)
    if data[:4] == b"RIFF" and len(data) >= 40 and data[12:16] == b"VP8X":
        w = (data[24] | (data[25] << 8) | (data[26] << 16)) + 1
        h = (data[27] | (data[28] << 8) | (data[29] << 16)) + 1
        return w, h

    return None, None


# ==============================================================
# FONCTIONS PUBLIQUES
# ==============================================================

def get_metadata(epub_path: str) -> dict:
    """
    Retourne les metadonnees du livre :
    title, author, cover_bytes (bytes ou None)
    """
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        return {"title": None, "author": None, "cover_bytes": None, "error": str(e)}

    # Titre
    title = None
    titles = book.get_metadata("DC", "title")
    if titles:
        title = titles[0][0]

    # Auteur
    author = None
    creators = book.get_metadata("DC", "creator")
    if creators:
        author = creators[0][0]

    # Couverture — plusieurs methodes selon les EPUB
    cover_bytes = None

    # Methode 1 : metadata OPF "cover" (reference explicite du manifest)
    cover_meta = book.get_metadata("OPF", "cover")
    if cover_meta:
        cover_id = cover_meta[0][1].get("content", "")
        cover_item = book.get_item_with_id(cover_id)
        if cover_item is not None and cover_item.get_type() == ebooklib.ITEM_IMAGE:
            cover_bytes = cover_item.get_content()

    # Methode 2 : item dont l'id OU le nom de fichier contient "cover"
    # (ex. Images/cover.jpg dont l'id est juste "image1")
    if not cover_bytes:
        for item in book.get_items():
            if item.get_type() != ebooklib.ITEM_IMAGE:
                continue
            candidate = (item.get_id() + " " + item.get_name()).lower()
            if "cover" in candidate:
                cover_bytes = item.get_content()
                break

    # Methode 3 : meilleure image — evite badges, qrcodes, espaceurs
    # et bandeaux qui ne sont pas des couvertures.
    if not cover_bytes:
        best = None
        best_score = -1
        for item in book.get_items():
            if item.get_type() != ebooklib.ITEM_IMAGE:
                continue
            data = item.get_content()
            w, h = _image_dimensions(data)
            if w is not None and h is not None:
                if w < 150 or h < 200:
                    continue          # icone, badge, qrcode, espaceur...
                if w / h > 1.2:
                    continue          # bandeau/banniere, pas une couverture
                score = w * h
            else:
                score = len(data)     # dimensions inconnues : taille fichier
            if score > best_score:
                best_score = score
                best = item
        if best is not None:
            cover_bytes = best.get_content()

    return {
        "title": title,
        "author": author,
        "cover_bytes": cover_bytes,
    }


def get_chapters(epub_path: str) -> list:
    """
    Retourne la liste ordonnee des chapitres :
    [{"index": 0, "title": "...", "text": "...texte brut..."}, ...]
    L'ordre respecte la spine du fichier EPUB.
    """
    try:
        book = epub.read_epub(epub_path)
    except Exception:
        return []

    chapters = []
    index = 0

    # La spine donne l'ordre de lecture officiel
    for item_id, _ in book.spine:
        item = book.get_item_with_id(item_id)
        if item is None:
            continue
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        if not _is_content_document(item):
            continue

        html = item.get_content().decode("utf-8", errors="replace")
        text = _html_to_text(html)

        # Ignore les chapitres vides (pages de garde, etc.)
        if len(text.strip()) < 50:
            continue

        title = _extract_chapter_title(html, fallback=f"Chapitre {index + 1}")

        chapters.append({
            "index": index,
            "title": title,
            "text": text,
        })
        index += 1

    return chapters


def get_chapter(epub_path: str, chapter_index: int) -> dict | None:
    """
    Retourne un chapitre specifique par son index.
    Retourne None si l'index est hors limites.
    """
    chapters = get_chapters(epub_path)
    if chapter_index < 0 or chapter_index >= len(chapters):
        return None
    return chapters[chapter_index]
