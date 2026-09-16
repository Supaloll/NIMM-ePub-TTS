# -*- coding: utf-8 -*-
"""
Script de verification jetable : etat des couvertures NIMM ePub.
- liste les livres en base et leur cover_path
- verifie l'existence et la taille reelle du fichier
- verifie la signature (magic bytes) de l'image
- verifie les dimensions si Pillow est disponible
Sortie ASCII uniquement.
"""
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.join("data", "nimm_epub.db")
LIB = os.path.join("data", "library")

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False


def signature(path):
    with open(path, "rb") as f:
        head = f.read(16)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if head[:3] == b"\xff\xd8\xff":
        return "jpg"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:5] == b"<?xml" or head[:1] == b"<":
        return "XML/SVG"
    return "INCONNU (" + head[:8].hex() + ")"


conn = sqlite3.connect(BASE)
print("Pillow disponible :", HAS_PIL)
print("Tables :", [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'")])
print("Colonnes books :", [d[1] for d in conn.execute("PRAGMA table_info(books)")])
print("")

rows = conn.execute(
    "SELECT id, user_id, cover_path, title FROM books ORDER BY id").fetchall()
print("Livres en base :", len(rows))
print("")
print("id | cover_path | existe | octets | type | dimensions | titre")
print("-" * 110)
for bid, uid, cp, title in rows:
    if not cp:
        print("%s | AUCUN cover_path | - | - | - | - | %s" % (bid, (title or "")[:40]))
        continue
    full = os.path.join(LIB, cp)
    if not os.path.exists(full):
        print("%s | %s | NON | - | - | - | %s" % (bid, cp, (title or "")[:40]))
        continue
    size = os.path.getsize(full)
    sig = signature(full)
    dims = "-"
    if HAS_PIL:
        try:
            with Image.open(full) as im:
                dims = "%sx%s" % im.size
        except Exception as e:
            dims = "ILLISIBLE: %s" % str(e)[:30]
    print("%s | %s | oui | %s | %s | %s | %s"
          % (bid, cp[:45], size, sig, dims, (title or "")[:35]))

print("-" * 110)
conn.close()

# Fichiers orphelins dans le dossier bibliotheque (non image / minuscules)
print("")
print("Fichiers de moins de 1024 octets dans data/library :")
n = 0
for name in sorted(os.listdir(LIB)):
    p = os.path.join(LIB, name)
    if os.path.isfile(p) and os.path.getsize(p) < 1024:
        n += 1
        print("  %s octets | %s" % (os.path.getsize(p), name))
print("Total petits fichiers :", n)

# Test direct de la route /cover du serveur local, si celui-ci repond.
print("")
print("Test de la route /api/books/{id}/cover (serveur local) :")
try:
    import json
    import urllib.request

    with urllib.request.urlopen("http://127.0.0.1:8000/api/users", timeout=5) as r:
        users = json.loads(r.read().decode("utf-8"))
    print("  users:", users)
    if users:
        uid = users[0]["id"]
        with urllib.request.urlopen(
                "http://127.0.0.1:8000/api/books?user_id=%s" % uid, timeout=5) as r:
            books = json.loads(r.read().decode("utf-8"))
        print("  livres renvoyes:", len(books))
        for b in books[:3]:
            url = "http://127.0.0.1:8000/api/books/%s/cover?user_id=%s" % (b["id"], uid)
            try:
                with urllib.request.urlopen(url, timeout=5) as r:
                    data = r.read(16)
                    print("   livre %s -> HTTP %s | type=%s | cache=%s | magic=%s"
                          % (b["id"], r.status,
                             r.headers.get("Content-Type"),
                             r.headers.get("Cache-Control"),
                             data[:4].hex()))
            except Exception as e:
                print("   livre %s -> ERREUR %s" % (b["id"], e))
except Exception as e:
    print("  serveur injoignable ou erreur :", e)
