# Bildepakke til dashbordet

Dette repoet fyller seg selv med naturbilder fra hele verden, hentet fra vinnerne i
fotokonkurransen **Wiki Loves Earth** på Wikimedia Commons. Hvert bilde har sted,
fotograf og lisens (CC BY-SA eller tilsvarende) i `bilder/index.json`.

## Slik virker det

- `hent_bilder.py` trekker tilfeldige vinnerbilder, laster dem ned i 1600 px og
  skriver metadata til `bilder/index.json`. Bare liggende bilder, ingen gjentakelser.
- `.github/workflows/bildepakke.yml` kjører skriptet den 1. hver måned og legger
  nye bilder i repoet. Den kan også kjøres manuelt under **Actions → Bildepakke →
  Run workflow**, der du kan velge antall (første gang: 60).
- Dashbordet henter bildene herfra og viser ett nytt hver dag, med sted og
  fotograf under.

## Lisens

Bildene tilhører fotografene og er utgitt under de lisensene som står i
`bilder/index.json` (som regel CC BY-SA 4.0). Krediter fotografen og oppgi
lisensen når et bilde vises. Skriptet og oppsettet kan brukes fritt.
