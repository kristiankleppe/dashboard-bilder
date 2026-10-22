#!/usr/bin/env python3
"""
Henter nye naturbilder fra Wiki Loves Earth-vinnerne på Wikimedia Commons og
legger dem i mappen bilder/, med metadata i bilder/index.json.

Kjøres av GitHub Actions (se .github/workflows/bildepakke.yml), men kan også
kjøres lokalt:  python hent_bilder.py 15

- Trekker tilfeldige vinnerbilder (nasjonale og internasjonale) fra årene 2016–i fjor.
- Hopper over bilder som allerede ligger i index.json, og tar bare liggende bilder.
- Laster ned i 1600 px bredde. Fotograf, lisens, sted/beskrivelse og lenke lagres.
Krav: Python 3.8+, bare standardbiblioteket.
"""
import datetime
import html
import json
import os
import random
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "Dashbord-bildepakke/1.1 (GitHub Actions; privat dashbord)"
ANTALL = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].strip() else 15
MAKS_TOTALT = 400
BREDDE = 1600
MAPPE = "bilder"
INDEX = os.path.join(MAPPE, "index.json")
I_AAR = datetime.date.today().year
AAR = list(range(2016, I_AAR))  # fjorårets vinnere er normalt kåret


def api(params):
    params = dict(params, format="json", formatversion="2")
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    for forsok in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            if forsok == 2:
                raise
            time.sleep(3 + forsok * 3)


def medlemmer(kat, typ):
    ut, cont = [], {}
    while True:
        svar = api(dict(action="query", list="categorymembers", cmtitle=kat, cmtype=typ, cmlimit="500", **cont))
        ut += [m["title"] for m in svar.get("query", {}).get("categorymembers", [])]
        cont = svar.get("continue")
        if not cont:
            return ut


def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def info(titler):
    svar = api(dict(action="query", prop="imageinfo", titles="|".join(titler),
                    iiprop="url|extmetadata|mime|size", iiurlwidth=str(BREDDE),
                    iiextmetadatafilter="ImageDescription|Artist|LicenseShortName|DateTimeOriginal"))
    ut = []
    for side in svar.get("query", {}).get("pages", []):
        ii = (side.get("imageinfo") or [None])[0]
        if not ii or not ii.get("thumburl") or not str(ii.get("mime", "")).startswith("image/"):
            continue
        if (ii.get("width") or 0) < (ii.get("height") or 0) * 1.15 or (ii.get("width") or 0) < BREDDE:
            continue  # bare liggende bilder med nok oppløsning
        meta = ii.get("extmetadata", {})
        ut.append({
            "commons": side["title"],
            "tittel": re.sub(r"^File:|\.[A-Za-z0-9]+$", "", side["title"]).replace("_", " "),
            "beskrivelse": strip_html(meta.get("ImageDescription", {}).get("value", ""))[:400],
            "fotograf": strip_html(meta.get("Artist", {}).get("value", ""))[:120],
            "lisens": strip_html(meta.get("LicenseShortName", {}).get("value", "")),
            "dato": strip_html(meta.get("DateTimeOriginal", {}).get("value", ""))[:40],
            "side": ii.get("descriptionurl", ""),
            "bilde_url": ii["thumburl"],
        })
    return ut


def last_ned(url, sti):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(sti, "wb") as f:
        shutil.copyfileobj(r, f)


def main():
    os.makedirs(MAPPE, exist_ok=True)
    index = json.load(open(INDEX, encoding="utf-8")) if os.path.exists(INDEX) else []
    har = {r["commons"] for r in index}
    if len(index) >= MAKS_TOTALT:
        print(f"Allerede {len(index)} bilder, henter ikke flere.")
        return

    kandidater = set()
    for aar in random.sample(AAR, k=min(4, len(AAR))):  # noqa: S311
        rot = f"Category:Winners of Wiki Loves Earth {aar}"
        try:
            kandidater.update(medlemmer(rot, "file"))
            for sub in medlemmer(rot, "subcat"):
                kandidater.update(medlemmer(sub, "file"))
        except Exception as e:  # noqa: BLE001
            print(f"Hoppet over {aar}: {e}")
    kandidater = [k for k in kandidater if k not in har]
    random.shuffle(kandidater)
    print(f"{len(kandidater)} kandidater. Henter {ANTALL} nye.")

    nye, i = [], 0
    while len(nye) < ANTALL and i < len(kandidater):
        bunke = kandidater[i:i + 50]
        i += 50
        for r in info(bunke):
            if len(nye) >= ANTALL:
                break
            if not r["fotograf"] or not r["lisens"]:
                continue
            n = len(index) + len(nye) + 1
            slug = re.sub(r"[^A-Za-z0-9]+", "-", r["tittel"]).strip("-")[:60] or "bilde"
            fil = f"{n:04d}-{slug}.jpg"
            try:
                last_ned(r["bilde_url"], os.path.join(MAPPE, fil))
            except Exception as e:  # noqa: BLE001
                print(f"Hoppet over {r['tittel']}: {e}")
                continue
            r["fil"] = fil
            r["hentet"] = datetime.date.today().isoformat()
            nye.append(r)
            print(f"{n:4d}  {r['tittel'][:70]}")
            time.sleep(0.3)

    index += nye
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print(f"Ferdig: {len(nye)} nye, {len(index)} totalt.")


if __name__ == "__main__":
    main()
