#!/usr/bin/env python3
"""Valideert de FEKO-importlijst voordat hij Shopware in gaat."""
import csv
import sys

CATEGORIEEN = {
    'schroeven', 'bouten-en-moeren', 'ruwbouw', 'spijkers-en-nieten',
    'gereedschap', 'chemische-producten', 'zagen-slijpen-boren', 'pluggen-en-ankers',
}

VERPLICHT = (
    'artikelnummer', 'product', 'categorie', 'naam',
    'prijs_incl_btw', 'btw', 'materiaal', 'verpakkingsaantal',
)


def valideer(rijen):
    fouten = []
    gezien = set()
    for nummer, rij in enumerate(rijen, start=2):
        for veld in VERPLICHT:
            if not (rij.get(veld) or '').strip():
                fouten.append(f"regel {nummer}: veld '{veld}' is leeg")

        artikelnummer = (rij.get('artikelnummer') or '').strip()
        if artikelnummer and artikelnummer in gezien:
            fouten.append(f"regel {nummer}: artikelnummer '{artikelnummer}' komt dubbel voor")
        elif artikelnummer:
            gezien.add(artikelnummer)

        categorie = (rij.get('categorie') or '').strip()
        if categorie and categorie not in CATEGORIEEN:
            fouten.append(f"regel {nummer}: onbekende categorie '{categorie}'")

        rauw = (rij.get('prijs_incl_btw') or '').strip().replace(',', '.')
        if rauw:
            try:
                if float(rauw) <= 0:
                    fouten.append(f"regel {nummer}: prijs moet groter dan 0 zijn")
            except ValueError:
                fouten.append(f"regel {nummer}: prijs '{rauw}' is geen getal")
    return fouten


def main(pad):
    with open(pad, newline='', encoding='utf-8-sig') as bestand:
        fouten = valideer(list(csv.DictReader(bestand, delimiter=';')))
    for fout in fouten:
        print(fout, file=sys.stderr)
    print(f"{len(fouten)} fout(en) gevonden")
    return 1 if fouten else 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('gebruik: valideer_import.py <bestand.csv>', file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
