# Webshop Just Screw It — implementatieplan

> **Voor agentic workers:** VERPLICHTE SUB-SKILL: gebruik superpowers:subagent-driven-development (aanbevolen) of superpowers:executing-plans om dit plan taak voor taak uit te voeren. Stappen gebruiken checkbox-syntax (`- [ ]`).

**Doel:** Een werkende B2C-webshop voor bevestigingsmateriaal op Shopware 6 CE, draaiend in Docker op een eigen EU-VPS, met iDEAL-betaling en dropshipping via FEKO.

**Architectuur:** Shopware 6.7 Community Edition in Docker op één VPS. Caddy als reverse proxy met automatische TLS ervoor. MariaDB en Redis als containers ernaast. De catalogus komt uit een xlsx die als CSV wordt gevalideerd en geïmporteerd. Betalen via de Mollie-plugin. Geen maatwerkcode zolang standaardfunctionaliteit volstaat.

**Tech stack:** Shopware 6.7 CE, PHP 8.3+, MariaDB 10.11+, Redis, Docker Compose, Caddy, Mollie-plugin, Python 3 (alleen voor het importvalidatiescript).

**Spec:** `docs/superpowers/specs/2026-08-19-webshop-design.md`

## Globale randvoorwaarden

- Shopware 6 **Community Edition**, self-hosted. Gratis tot circa €1 mln GMV per jaar.
- Minimumeisen: PHP 8.2+ (8.4 vanaf 6.7), MySQL 8.0+ of MariaDB 10.11+, Composer 2.2+, Node 20, minimaal 4 GB RAM. Richtlijn VPS: 8 GB RAM, 4 vCPU, NVMe, EU-datacenter.
- **Dockware nooit naar productie.** Dockware is voor lokaal en CI; productie draait op `shopware/docker-base`. `dockware/dev`, `dockware/play` en `dockware/flex` zijn deprecated.
- Prijzen **inclusief 21% btw**. Bedragen in de importlijst met punt of komma als decimaalteken, nooit als tekst.
- Voorraadbeheer staat **uit**: alle artikelen altijd bestelbaar (geen closeout).
- Tot livegang staat de shop op `noindex` én achter toegangsbeperking.
- Inkoopprijzen en marges komen **niet** in de repo of in Shopware.
- Elke taak eindigt met een commit.

**Startvoorwaarde:** de VPS bestaat, draait Ubuntu 24.04 LTS (of Debian 12), is bereikbaar via SSH als root of een sudo-gebruiker, en heeft een publiek IP. De eigenaar regelt dit zelf.

---

## Fase 0 — VPS, Docker en Shopware bereikbaar

### Taak 1: VPS-basisbeveiliging

**Locatie:** de VPS, via SSH. Niets in de repo.

- [ ] **Stap 1: Maak een niet-root gebruiker met sudo**

```bash
adduser --gecos "" deploy
usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

- [ ] **Stap 2: Zet wachtwoord- en root-login uit**

Bewerk `/etc/ssh/sshd_config`:

```
PermitRootLogin no
PasswordAuthentication no
```

```bash
systemctl restart ssh
```

- [ ] **Stap 3: Controleer dat je nog binnenkomt vóór je de sessie sluit**

Open een **tweede** terminal: `ssh deploy@<ip>`.
Verwacht: je logt in. Lukt dit niet, herstel dan via de eerste sessie.
Verwacht bij `ssh root@<ip>`: geweigerd.

- [ ] **Stap 4: Firewall aan**

```bash
sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw --force enable
sudo ufw status
```

Verwacht: alleen 22, 80 en 443 staan open.

- [ ] **Stap 5: Automatische beveiligingsupdates**

```bash
sudo apt update && sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

- [ ] **Stap 6: Leg de serverkeuzes vast**

Maak `docs/server.md` in de repo met: provider, IP, OS-versie, gebruikersnaam, en de datum van inrichten. Geen wachtwoorden of sleutels.

```bash
git add docs/server.md && git commit -m "docs: serverinrichting vastgelegd"
```

---

### Taak 2: Docker installeren

**Locatie:** de VPS.

- [ ] **Stap 1: Installeer Docker Engine en de Compose-plugin**

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy
```

Log uit en weer in zodat de groep actief wordt.

- [ ] **Stap 2: Controleer de installatie**

```bash
docker run --rm hello-world
docker compose version
```

Verwacht: "Hello from Docker!" en een Compose-versie van 2.x of hoger.

---

### Taak 3: Repo omzetten naar een Shopware-project

**Bestanden:**
- Verwijderen: `src/`, `public/`, `astro.config.mjs`, `tailwind.config.mjs`, `tsconfig.json`, `package.json`, `package-lock.json`
- Aanmaken: het Shopware-project in de repo-root
- Behouden: `docs/`, `.gitignore`

De hardloop-landingspagina vervalt (spec §1). De git-historie bewaart hem.

**Waar de repo staat:** de repo bestaat op twee plekken — op de werkmachine en op de
VPS onder `~/just-screw-it`, beide gekoppeld aan dezelfde GitHub-remote. De VPS is de
enige *draaiende* omgeving; synchroniseren gaat via push en pull, nooit via scp of
handmatig kopiëren. Voer stappen 1 tot en met 5 uit op de werkmachine, tenzij anders
vermeld.

- [ ] **Stap 0: Kloon de repo op de VPS**

```bash
ssh deploy@<ip>
git clone git@github.com:steemersict/just-screw-it.git ~/just-screw-it
cd ~/just-screw-it && git branch --show-current
```

Verwacht: `feature/webshop`. Zo niet: `git checkout feature/webshop`.

- [ ] **Stap 1: Verwijder de Astro-site**

```bash
git rm -r --cached src public
rm -rf src public node_modules
git rm astro.config.mjs tailwind.config.mjs tsconfig.json package.json package-lock.json
git commit -m "chore: Astro-landingspagina verwijderd, repo wordt Shopware-project"
```

- [ ] **Stap 2: Maak het Shopware-project aan**

Op de VPS, in een tijdelijke map. `npx` vereist Node, dat taak 2 niet installeert —
installeer het dus eerst, of gebruik de Docker-route uit de documentatie:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs && node --version
```

```bash
cd /tmp
npx @shopware-ag/shopware-cli project create shop
```

Lukt npx niet, gebruik dan de gedocumenteerde alternatieve route:
<https://developer.shopware.com/docs/guides/installation/>

- [ ] **Stap 3: Verplaats het project naar de repo en commit**

```bash
cd /pad/naar/just-screw-it
cp -r /tmp/shop/. .
git add -A && git commit -m "feat: Shopware 6 projectskelet toegevoegd"
```

- [ ] **Stap 4: Controleer dat het skelet klopt**

```bash
grep -m1 '"shopware/core"' composer.json
test -f .env.example && echo "env-voorbeeld aanwezig"
```

Verwacht: `shopware/core` staat in composer.json en er is een env-voorbeeldbestand.

- [ ] **Stap 5: Controleer dat gevoelige bestanden genegeerd worden**

`.gitignore` moet minimaal bevatten: `.env`, `.env.local`, `/vendor/`, `/var/`, `/public/media/`, `/files/`.

```bash
git check-ignore -v .env vendor var
git add .gitignore && git commit -m "chore: gitignore voor Shopware"
```

---

### Taak 4: Shopware draaiend krijgen in Docker

**Bestanden:**
- Aanmaken: `compose.yaml`, `.env.example` aanvullen
- Referentie: <https://developer.shopware.com/docs/guides/hosting/installation-updates/docker.html>

- [ ] **Stap 1: Lees eerst de officiële Docker-pagina**

Open bovenstaande URL en noteer de actuele naam en tag van het productie-image (`shopware/docker-base` of opvolger) en welke omgevingsvariabelen verplicht zijn. Wijkt de documentatie af van het onderstaande voorbeeld, dan wint de documentatie.

- [ ] **Stap 2: Schrijf `compose.yaml`**

```yaml
services:
  database:
    image: mariadb:11
    environment:
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MARIADB_DATABASE: shopware
      MARIADB_USER: shopware
      MARIADB_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      retries: 10

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

  shop:
    image: ${SHOPWARE_IMAGE}
    depends_on:
      database:
        condition: service_healthy
    environment:
      APP_ENV: prod
      APP_URL: ${APP_URL}
      APP_SECRET: ${APP_SECRET}
      DATABASE_URL: mysql://shopware:${DB_PASSWORD}@database:3306/shopware
    volumes:
      - shop-media:/var/www/html/public/media
      - shop-files:/var/www/html/files
    ports:
      - "127.0.0.1:8000:8000"

volumes:
  db-data:
  redis-data:
  shop-media:
  shop-files:
```

De poort bindt bewust op `127.0.0.1`: alleen Caddy (taak 5) mag erbij, niet het open internet.

- [ ] **Stap 3: Maak `.env` met echte waarden**

```bash
cp .env.example .env
printf 'DB_ROOT_PASSWORD=%s\n' "$(openssl rand -hex 24)" >> .env
printf 'DB_PASSWORD=%s\n' "$(openssl rand -hex 24)" >> .env
printf 'APP_SECRET=%s\n' "$(openssl rand -hex 32)" >> .env
```

Vul `SHOPWARE_IMAGE` en `APP_URL` handmatig aan. `.env` is genegeerd door git — controleer dat met `git status`.

- [ ] **Stap 4: Start de stack en installeer Shopware**

```bash
docker compose up -d
docker compose logs -f shop
```

Volg de installatiestap uit de documentatie uit stap 1 (doorgaans de deployment-helper of `bin/console system:install`).

- [ ] **Stap 5: Controleer dat de shop antwoordt**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/admin
```

Verwacht: tweemaal `200`. Krijg je `500`, kijk dan in `docker compose logs shop`.

- [ ] **Stap 6: Commit**

```bash
git add compose.yaml .env.example && git commit -m "feat: docker compose stack voor Shopware, MariaDB en Redis"
```

---

### Taak 5: Caddy ervoor met TLS, toegangsbeperking en noindex

**Bestanden:**
- Aanmaken: `Caddyfile`
- Wijzigen: `compose.yaml` (caddy-service toevoegen)

Zonder deze taak staat een half afgebouwde shop open op het internet en kan Google hem indexeren. Dat werkt leerdoel 3 uit de spec actief tegen.

- [ ] **Stap 1: Schrijf de `Caddyfile`**

```
{$SITE_DOMAIN} {
	encode zstd gzip

	basic_auth {
		{$BASIC_AUTH_USER} {$BASIC_AUTH_HASH}
	}

	header {
		X-Robots-Tag "noindex, nofollow"
	}

	reverse_proxy shop:8000
}
```

- [ ] **Stap 2: Genereer de wachtwoordhash**

```bash
docker run --rm caddy:2 caddy hash-password --plaintext 'kies-hier-een-wachtwoord'
```

Zet de uitkomst als `BASIC_AUTH_HASH` in `.env`, plus `BASIC_AUTH_USER` en `SITE_DOMAIN`.

- [ ] **Stap 3: Voeg Caddy toe aan `compose.yaml`**

```yaml
  caddy:
    image: caddy:2
    depends_on: [shop]
    environment:
      SITE_DOMAIN: ${SITE_DOMAIN}
      BASIC_AUTH_USER: ${BASIC_AUTH_USER}
      BASIC_AUTH_HASH: ${BASIC_AUTH_HASH}
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
    ports:
      - "80:80"
      - "443:443"
```

Voeg `caddy-data:` en `caddy-config:` toe onder `volumes:`.

- [ ] **Stap 4: Wijs DNS naar de VPS**

Zet een A-record van je (voorlopige) domein naar het IP van de VPS. Caddy heeft dat nodig om automatisch een TLS-certificaat te halen.

- [ ] **Stap 5: Start en controleer alle drie de eigenschappen**

```bash
docker compose up -d caddy
curl -s -o /dev/null -w "%{http_code}\n" https://$SITE_DOMAIN/
curl -s -u "$BASIC_AUTH_USER:<wachtwoord>" -o /dev/null -w "%{http_code}\n" https://$SITE_DOMAIN/
curl -sI -u "$BASIC_AUTH_USER:<wachtwoord>" https://$SITE_DOMAIN/ | grep -i x-robots-tag
```

Verwacht: `401` zonder wachtwoord, `200` mét, en een `X-Robots-Tag: noindex, nofollow` in de headers. Alle drie moeten kloppen — twee van de drie is niet afgeschermd.

- [ ] **Stap 6: Commit**

```bash
git add Caddyfile compose.yaml && git commit -m "feat: Caddy met TLS, toegangsbeperking en noindex"
```

---

### Taak 6: Backups met een geteste restore

**Bestanden:**
- Aanmaken: `tools/backup.sh`

Een backup die nooit is teruggezet is geen backup maar een aanname.

- [ ] **Stap 1: Schrijf `tools/backup.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

DOEL="${1:-/var/backups/shop}"
STEMPEL="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DOEL"

docker compose exec -T database \
  mariadb-dump -u root -p"$DB_ROOT_PASSWORD" --single-transaction shopware \
  | gzip > "$DOEL/db-$STEMPEL.sql.gz"

docker run --rm \
  -v just-screw-it_shop-media:/media:ro \
  -v "$DOEL":/backup \
  alpine tar czf "/backup/media-$STEMPEL.tar.gz" -C /media .

find "$DOEL" -name '*.gz' -mtime +14 -delete
echo "backup klaar: $DOEL/db-$STEMPEL.sql.gz"
```

Controleer de volumenaam met `docker volume ls` — het voorvoegsel volgt de mapnaam.

- [ ] **Stap 2: Maak een backup en controleer dat er inhoud in zit**

```bash
chmod +x tools/backup.sh
set -a && source .env && set +a
./tools/backup.sh
ls -lh /var/backups/shop/
gzip -t /var/backups/shop/db-*.sql.gz && echo "dump is leesbaar"
```

Verwacht: bestanden groter dan nul bytes en een geldige gzip.

- [ ] **Stap 3: Test de restore, écht**

```bash
docker compose exec -T database mariadb -u root -p"$DB_ROOT_PASSWORD" \
  -e "CREATE DATABASE restoretest;"
gunzip -c /var/backups/shop/db-*.sql.gz | \
  docker compose exec -T database mariadb -u root -p"$DB_ROOT_PASSWORD" restoretest
docker compose exec -T database mariadb -u root -p"$DB_ROOT_PASSWORD" \
  -e "SELECT COUNT(*) FROM restoretest.product;"
```

Verwacht: een getal, geen foutmelding. Ruim daarna op:

```bash
docker compose exec -T database mariadb -u root -p"$DB_ROOT_PASSWORD" \
  -e "DROP DATABASE restoretest;"
```

- [ ] **Stap 4: Zet de backup in cron**

```bash
(crontab -l 2>/dev/null; echo "30 3 * * * cd $PWD && set -a && . ./.env && set +a && ./tools/backup.sh >> /var/log/shop-backup.log 2>&1") | crontab -
crontab -l
```

- [ ] **Stap 5: Commit**

```bash
git add tools/backup.sh && git commit -m "feat: backupscript met geteste restore"
```

---

## Fase 1 — Catalogus

### Taak 7: Validatiescript voor de importlijst

**Bestanden:**
- Aanmaken: `tools/valideer_import.py`
- Test: `tools/test_valideer_import.py`

**Interfaces:**
- Levert: `valideer(rijen: list[dict]) -> list[str]` — geeft een lijst foutmeldingen terug, leeg als alles klopt. Taak 9 gebruikt dit script vóór elke import.

Dit is het enige echte stuk logica in dit project, dus het enige dat tests krijgt. Python 3 uit de standaardbibliotheek, geen dependencies: `csv` handelt aanhalingstekens en puntkomma's correct af, wat zelfgeschreven splitsen niet doet.

- [ ] **Stap 1: Schrijf de falende test**

```python
import unittest
from valideer_import import valideer

BASIS = {
    'artikelnummer': 'HS-RVS-M6-40', 'product': 'Houtschroef RVS platkop',
    'categorie': 'schroeven', 'naam': 'Houtschroef RVS platkop M6x40',
    'prijs_incl_btw': '12,95', 'btw': '21', 'materiaal': 'RVS',
    'verpakkingsaantal': '100',
}

class TestValideer(unittest.TestCase):
    def test_geldige_rij_geeft_geen_fouten(self):
        self.assertEqual(valideer([BASIS]), [])

    def test_dubbel_artikelnummer(self):
        fouten = valideer([BASIS, dict(BASIS)])
        self.assertTrue(any('dubbel' in f for f in fouten))

    def test_prijs_nul_is_fout(self):
        fouten = valideer([{**BASIS, 'prijs_incl_btw': '0'}])
        self.assertTrue(any('groter dan 0' in f for f in fouten))

    def test_prijs_geen_getal(self):
        fouten = valideer([{**BASIS, 'prijs_incl_btw': 'op aanvraag'}])
        self.assertTrue(any('geen getal' in f for f in fouten))

    def test_leeg_verplicht_veld(self):
        fouten = valideer([{**BASIS, 'naam': '  '}])
        self.assertTrue(any("'naam'" in f for f in fouten))

    def test_onbekende_categorie(self):
        fouten = valideer([{**BASIS, 'categorie': 'tuinmeubels'}])
        self.assertTrue(any('onbekende categorie' in f for f in fouten))

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Stap 2: Draai de test en controleer dat hij faalt**

```bash
cd tools && python3 -m unittest test_valideer_import -v
```

Verwacht: `ModuleNotFoundError: No module named 'valideer_import'`.

- [ ] **Stap 3: Schrijf het script**

```python
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
```

- [ ] **Stap 4: Draai de tests en controleer dat ze slagen**

```bash
cd tools && python3 -m unittest test_valideer_import -v
```

Verwacht: `OK`, zes tests.

- [ ] **Stap 5: Commit**

```bash
git add tools/valideer_import.py tools/test_valideer_import.py
git commit -m "feat: validatiescript voor de importlijst"
```

---

### Taak 8: Categorieën en property groups

**Locatie:** Shopware-admin, `https://<domein>/admin`. Geen bestanden in de repo.

- [ ] **Stap 1: Maak de acht categorieën**

Catalogussen → Categorieën. Maak onder de hoofdnavigatie aan: Schroeven, Bouten en moeren, Ruwbouw, Spijkers en nieten, Gereedschap, Chemische producten, Zagen slijpen en boren, Pluggen en ankers.

De URL-namen moeten exact overeenkomen met de sleutels in `CATEGORIEEN` uit taak 7.

- [ ] **Stap 2: Maak de property groups**

Catalogussen → Eigenschappen. Maak vijf groepen aan, met per groep enkele waarden:

| Groep | Weergave | Voorbeeldwaarden |
|---|---|---|
| Materiaal | tekst | RVS, verzinkt |
| Diameter | tekst | M4, M5, M6, M8 |
| Lengte | tekst | 20 mm, 30 mm, 40 mm |
| Kopvorm | tekst | platkop, bolkop, verzonken |
| Verpakkingsaantal | tekst | 100, 200, 500 |

- [ ] **Stap 3: Zet elke groep als filter aan**

Per groep: "Filterbaar in listing" aanzetten. Zonder dit verschijnen de filters niet in de storefront, en filteren is volgens de spec de kern van deze shop.

- [ ] **Stap 4: Controleer in de storefront**

Open een categoriepagina. Verwacht: de categorie bestaat en de filterbalk is zichtbaar (nog zonder waarden, want er zijn nog geen producten).

- [ ] **Stap 5: Leg de opzet vast**

Maak `docs/catalogus.md` met de acht categorie-URL-namen en de vijf groepen met hun waarden, zodat de import ertegen gebouwd kan worden.

```bash
git add docs/catalogus.md && git commit -m "docs: categorie- en eigenschappenopzet"
```

---

### Taak 9: Dummy-catalogus importeren

**Bestanden:**
- Aanmaken: `data/dummy-producten.csv`

Echte FEKO-data is er nog niet (spec §4). Met dummy-data kun je de hele keten al testen.

- [ ] **Stap 1: Maak een dummy-CSV met vier producten en dertig varianten**

Kolomkoppen, puntkomma-gescheiden:

```
artikelnummer;product;categorie;naam;prijs_incl_btw;btw;materiaal;diameter_mm;lengte_mm;kopvorm;verpakkingsaantal;gewicht_gram;ean
HS-RVS-M4-20;Houtschroef RVS platkop;schroeven;Houtschroef RVS platkop M4x20;6,95;21;RVS;M4;20;platkop;100;280;
HS-RVS-M4-30;Houtschroef RVS platkop;schroeven;Houtschroef RVS platkop M4x30;7,95;21;RVS;M4;30;platkop;100;390;
HS-RVS-M6-40;Houtschroef RVS platkop;schroeven;Houtschroef RVS platkop M6x40;12,95;21;RVS;M6;40;platkop;100;720;
```

Vul aan tot minstens dertig regels over vier producten, verdeeld over minimaal twee categorieën.

- [ ] **Stap 2: Valideer vóór import**

```bash
python3 tools/valideer_import.py data/dummy-producten.csv
```

Verwacht: `0 fout(en) gevonden`. Zo niet: eerst de CSV repareren.

- [ ] **Stap 3: Bouw een bewust foute regel in en controleer dat het script hem vangt**

Zet tijdelijk één prijs op `0`, draai het script opnieuw.
Verwacht: exitcode 1 en de melding "prijs moet groter dan 0 zijn". Zet daarna terug.

- [ ] **Stap 4: Importeer in Shopware**

Instellingen → Import/Export. Maak een importprofiel voor producten, koppel de kolommen aan de Shopware-velden en importeer. Gebruik `product` om varianten te groeperen.

- [ ] **Stap 5: Zet voorraadbeheer uit**

Randvoorwaarde uit de spec: alle artikelen zijn altijd bestelbaar, want FEKO levert en
wij houden geen voorraad bij. Zet in het importprofiel per variant een ruime voorraad
én zet "Uitverkocht wanneer voorraad op is" (closeout) uit.

Controleer daarna op een variant in de admin dat closeout uit staat, en zet in de
storefront een testbestelling met een aantal boven de ingestelde voorraad in de
winkelwagen.
Verwacht: dat mag gewoon. Krijg je een melding dat er onvoldoende voorraad is, dan
staat closeout nog aan.

- [ ] **Stap 6: Controleer het resultaat in de storefront**

Verwacht: vier productpagina's, per pagina een variantkiezer, en filters die daadwerkelijk resultaten wegfilteren.

- [ ] **Stap 7: Commit**

```bash
git add data/dummy-producten.csv && git commit -m "feat: dummy-catalogus voor het testen van de importketen"
```

---

## Fase 2 — Betalen, verzenden en juridisch

### Taak 10: Mollie met iDEAL in testmodus

**Locatie:** Shopware-admin.

- [ ] **Stap 1: Installeer de Mollie-plugin**

Extensies → Store. Zoek de officiële Mollie-plugin voor Shopware 6, installeer en activeer. Controleer dat de pluginversie Shopware 6.7 ondersteunt.

- [ ] **Stap 2: Vul de test-API-sleutel in**

Maak een Mollie-account aan, pak de sleutel die met `test_` begint en vul die in bij de plugininstellingen. Zet de plugin op testmodus.

- [ ] **Stap 3: Zet iDEAL aan als betaalmethode**

Instellingen → Betaalmethoden: iDEAL activeren en toewijzen aan het verkoopkanaal.

- [ ] **Stap 4: Controleer in de checkout**

Leg een product in de winkelwagen en ga naar de betaalstap.
Verwacht: iDEAL staat in de lijst. Staat het er niet, controleer dan de toewijzing aan het verkoopkanaal.

---

### Taak 11: Verzendmethode

**Locatie:** Shopware-admin.

Spec §6: vast €6,95, gratis boven €75.

- [ ] **Stap 1: Maak de verzendmethode**

Instellingen → Verzendmethoden. Nieuwe methode "Standaard verzending", prijs €6,95, toewijzen aan het verkoopkanaal.

- [ ] **Stap 2: Maak de regel voor gratis verzending**

Instellingen → Rule Builder. Nieuwe regel "Bestelwaarde vanaf €75", conditie: winkelwagentotaal ≥ 75.

- [ ] **Stap 3: Koppel de regel aan een prijs van €0**

In de verzendmethode: extra prijsregel met de zojuist gemaakte regel en bedrag €0,00.

- [ ] **Stap 4: Test beide kanten van de grens**

Winkelwagen van circa €20: verwacht €6,95 verzendkosten.
Winkelwagen van circa €90: verwacht €0,00.

Test ook precies op €75 en noteer welk gedrag je ziet — grenzen zijn waar dit soort regels misgaat.

- [ ] **Stap 5: Leg de uitkomst vast**

Vul in `docs/catalogus.md` aan welk gedrag je op de grens hebt waargenomen.

```bash
git add docs/catalogus.md && git commit -m "docs: verzendregel en grensgedrag vastgelegd"
```

---

### Taak 12: Juridische pagina's

**Locatie:** Shopware-admin, Content → Shopping Experiences en Instellingen.

Spec §9. Dit is wetgeving, geen sierwerk: als dropshipper ben jij de verkoper.

- [ ] **Stap 1: Maak de verplichte pagina's**

Algemene voorwaarden, Retourneren (inclusief modelformulier voor herroeping), Privacybeleid, Cookiebeleid, Verzenden en betalen, Contact.

- [ ] **Stap 2: Zet KvK- en btw-nummer in de footer**

Instellingen → Basisinformatie, en de footer-navigatie.

- [ ] **Stap 3: Zet cookie-consent aan**

Shopware heeft dit ingebouwd. Controleer dat de melding verschijnt bij een eerste bezoek in een privévenster.

- [ ] **Stap 4: Zet de levertijdmelding op de productpagina's**

Spec §4: zonder voorraadstand wordt af en toe iets verkocht dat FEKO niet heeft. Een zichtbare levertijdmelding vangt dat op.

- [ ] **Stap 5: Loop alles na**

Klik elke footerlink aan. Verwacht: geen 404, geen lege pagina, en het herroepingsformulier is te downloaden of te kopiëren.

---

### Taak 13: Volledige testbestelling

**Locatie:** storefront en admin.

- [ ] **Stap 1: Plaats een bestelling als gast**

Product kiezen → variant kiezen → winkelwagen → gastcheckout → adres → iDEAL → betalen met de testmethode van Mollie.

- [ ] **Stap 2: Controleer de order in de admin**

Verwacht: de order staat er, met de juiste variant, het juiste totaal inclusief verzendkosten, en betaalstatus betaald.

- [ ] **Stap 3: Controleer de orderbevestiging**

Verwacht: de klant krijgt een bevestigingsmail. Komt die niet aan, dan is de mailconfiguratie het probleem — noteer dat als openstaand punt (spec §13.3).

- [ ] **Stap 4: Test de mislukte betaling**

Bestel opnieuw en kies bij Mollie "mislukt".
Verwacht: de klant komt terug in de shop met een nette melding en de order staat niet als betaald.

- [ ] **Stap 5: Leg de testronde vast**

Noteer in `docs/testrondes.md` wat je hebt getest, wat werkte en wat niet.

```bash
git add docs/testrondes.md && git commit -m "docs: eerste end-to-end testronde"
```

---

## Fase 3 — Livegang

### Taak 14: Domein, indexering en nulmeting

**Bestanden:**
- Wijzigen: `Caddyfile`

- [ ] **Stap 1: Kies en koppel het definitieve domein**

Spec §13.2: er is nog geen domein. Registreer er een, zet DNS naar de VPS en pas `SITE_DOMAIN` aan in `.env`.

- [ ] **Stap 2: Haal de toegangsbeperking en noindex weg**

Verwijder het `basic_auth`-blok en de `X-Robots-Tag`-header uit de `Caddyfile`.

```bash
docker compose restart caddy
curl -sI https://<domein>/ | grep -i x-robots-tag
```

Verwacht: **geen** uitvoer. Zie je nog een noindex-header, dan wordt je shop niet geïndexeerd.

- [ ] **Stap 3: Controleer sitemap en robots.txt**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<domein>/sitemap.xml
curl -s https://<domein>/robots.txt
```

Verwacht: `200` op de sitemap, en een robots.txt die de shop niet blokkeert.

- [ ] **Stap 4: Doe de Lighthouse-nulmeting**

Meet de homepage en één productpagina, op mobiel. Noteer LCP, CLS en INP.
Dit is je startpunt voor leerdoel 3 — zonder nulmeting kun je later niet aantonen dat je iets verbeterd hebt.

- [ ] **Stap 5: Commit**

```bash
git add Caddyfile docs/testrondes.md
git commit -m "feat: livegang, indexering aan, Lighthouse-nulmeting vastgelegd"
```

---

## Fase 4 — Leerdoelen

### Taak 15: Tweede Sales Channel voor een doelgroep

**Locatie:** Shopware-admin.

Leerdoel 1 uit de spec. Dit is de reden dat Shopware gekozen is: een tweede doelgroepgerichte frontend is hier een instelling, geen bouwproject.

- [ ] **Stap 1: Maak een tweede Sales Channel**

Bijvoorbeeld gericht op klussers versus professionals. Eigen domein of subdomein, eigen thema-instellingen.

- [ ] **Stap 2: Wijs een eigen categorieselectie toe**

Zet een andere navigatie-ingang of een beperktere categorieselectie op dit kanaal.

- [ ] **Stap 3: Voeg het subdomein toe aan Caddy en DNS**

Breid de `Caddyfile` uit met het tweede domein, wijs DNS aan, herstart Caddy.

- [ ] **Stap 4: Controleer beide kanalen**

Verwacht: beide domeinen werken, tonen een eigen selectie, en delen dezelfde producten en orders in de admin.

- [ ] **Stap 5: Commit**

```bash
git add Caddyfile && git commit -m "feat: tweede sales channel voor doelgroepgerichte storefront"
```

---

### Taak 16: Rule Builder en promoties

**Locatie:** Shopware-admin.

Leerdoel 1 en 4.

- [ ] **Stap 1: Maak een doelgroepregel**

Bijvoorbeeld: bestellingen boven een bepaald aantal stuks, of klanten uit een bepaald verkoopkanaal.

- [ ] **Stap 2: Koppel de regel aan een promotie**

Marketing → Promoties. Maak een korting die alleen geldt als de regel waar is.

- [ ] **Stap 3: Test beide kanten**

Verwacht: winkelwagen die aan de regel voldoet krijgt de korting, een die er niet aan voldoet niet. Test opnieuw expliciet op de grenswaarde.

---

### Taak 17: SEO en gestructureerde data

**Locatie:** Shopware-admin.

Leerdoel 3.

- [ ] **Stap 1: Controleer de SEO-URL-templates**

Instellingen → SEO. Verwacht: nette URL's zonder ID's, per verkoopkanaal instelbaar.

- [ ] **Stap 2: Vul meta-titels en -omschrijvingen**

Voor de acht categorieën en de vier dummy-producten. Schrijf ze voor een zoeker naar bevestigingsmateriaal, niet voor jezelf.

- [ ] **Stap 3: Controleer de gestructureerde data**

Draai een productpagina door Google's Rich Results Test.
Verwacht: het product wordt herkend, met prijs en beschikbaarheid.

- [ ] **Stap 4: Meet opnieuw met Lighthouse**

Vergelijk met de nulmeting uit taak 14. Noteer het verschil in `docs/testrondes.md`.

```bash
git add docs/testrondes.md && git commit -m "docs: SEO-instellingen en tweede Lighthouse-meting"
```

---

### Taak 18: Locatiegerichte landingspagina en Flow Builder

**Locatie:** Shopware-admin.

Leerdoel 2 en 4.

- [ ] **Stap 1: Maak een locatiegerichte landingspagina**

Content → Shopping Experiences. Bijvoorbeeld "Bevestigingsmateriaal in <plaatsnaam>", met een eigen SEO-URL, eigen meta-teksten en een selectie producten.

- [ ] **Stap 2: Zet lokale gestructureerde data erop**

Bedrijfsgegevens, adres en openingstijden, zodat de pagina lokaal kan ranken.

- [ ] **Stap 3: Maak een Flow Builder-flow**

Bijvoorbeeld: bij een nieuwe bestelling boven een bedrag een interne melding, of een opvolgmail na levering.

- [ ] **Stap 4: Test de flow**

Plaats een testbestelling die de voorwaarde raakt.
Verwacht: de flow vuurt en de actie is zichtbaar in de flow-uitvoeringen.

- [ ] **Stap 5: Leg de leeropbrengst vast**

Noteer in `docs/testrondes.md` wat werkte en wat je zou aanpassen.

```bash
git add docs/testrondes.md && git commit -m "docs: locatiegerichte pagina en flow getest"
```

---

## Openstaande punten die buiten dit plan vallen

Deze staan in spec §13 en zijn geen implementatietaken:

1. Dropship-afspraken met FEKO: tarief per zending, gedrag boven 10 kg, wie de retourvracht betaalt, en of er blanco verzonden wordt.
2. Echte FEKO-productdata en productfoto's; de dummy-catalogus uit taak 9 wordt dan vervangen.
3. Mailprovider met EU-verwerking kiezen, of mail via de eigen server.
4. bol.com-koppeling. Voorbereiding zit in het schema (EAN per variant), de bouw niet in dit plan.
