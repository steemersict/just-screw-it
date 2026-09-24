# Webshop Just Screw It — ontwerp

Datum: 2026-08-19
Branch: `feature/webshop`
Status: ter review
Vervangt: de eerste versie van dit spec (Astro + Cloudflare Workers + Mollie), zie git-historie

## 1. Doel en context

Een B2C-webshop voor bevestigingsmateriaal, gedropshipt via FEKO BV.
300-500 SKU's in acht categorieën. Gastcheckout, iDEAL, prijzen inclusief btw.

Dit is expliciet een **leerproject** met een mogelijke exit: draait de shop met
voldoende omzet, dan is verkoop aan FEKO een reële optie. Die twee doelen sturen
elke keuze hieronder.

Leerdoelen, in volgorde van belang:

1. Doelgroepgericht promoten
2. Locatiegericht promoten
3. SEO
4. Marketing
5. Shopware leren kennen als webshop-backend

De bestaande hardloop-landingspagina vervalt. Deze repo wordt de Shopware-repo.

## 2. Platformkeuze

**Shopware 6 Community Edition, self-hosted.**

De doorslag geeft dat leerdoel 1, 2 en 4 in Shopware ingebouwde mechanismen zijn —
Sales Channels, Rule Builder, Flow Builder, landingspagina's — in plaats van code
die we zelf schrijven. Je leert marketing bedienen in plaats van marketing bouwen.
Daarnaast is een Shopware-shop overdraagbaar: elk Shopware-bureau kan hem overnemen,
wat het exit-scenario richting FEKO reëel maakt. Maatwerk is voor een koper vooral
risico.

Afgewogen en afgevallen:

- **Astro + Cloudflare Workers + D1 + Mollie** (het eerste ontwerp) — technisch het
  goedkoopst en snelst, maar elke doelgroepgerichte frontend was een bouwproject
  geweest, en voor een koper is maatwerk een last in plaats van een asset.
- **Snipcart** — DPA uit mei 2018, geen doorgiftemechanisme, geen hostinglocatie,
  geen subverwerkerslijst; plus 2% per transactie en orders buiten eigen beheer.
- **WooCommerce** — beheer is lichter, maar multi-storefront en doelgroepsturing zijn
  er zwak, en het draagt niets bij aan de gestelde leerdoelen.
- **Payload CMS op Workers** — Payload-op-Workers is een pilot en de ecommerce-plugin
  heeft Stripe als standaardadapter; voor iDEAL schrijf je alsnog zelf een adapter.
- **Merchant (Workers + D1)** — de maker adviseert het zelf af voor productie.
- **Medusa / Vendure** — draaien niet op Workers en dragen niet bij aan de leerdoelen.

### 2.1 Randvoorwaarden en grenzen

- Community Edition is gratis tot circa €1 mln GMV per jaar (fair use policy).
  Ruim voldoende, maar relevant bij verkoop aan FEKO.
- De B2B Suite zit pas in Evolve (€2.400/mnd), niet in Rise en niet in CE. Wordt B2B
  relevant, dan is B2Bsellers een derde partij die wél op CE draait. Nu niet nodig.
- Cloudflare Workers vervalt als runtime. Shopware vraagt PHP 8.2+, MySQL 8.0+ of
  MariaDB 10.11+, Composer 2.2+, Node 20 en minimaal 4 GB RAM. Cloudflare kan er
  hooguit als CDN en WAF voor staan.

## 3. Omgeving en hosting

**Alles op een eigen EU-VPS, in Docker, vanaf dag één.**

Lokaal draaien valt af: de werkmachine heeft 8 GB RAM en Shopware vraagt al 4 GB
minimum. Met Docker Desktop erbij wordt dat een swappende machine in plaats van een
leeromgeving.

Richtlijn voor de VPS: 8 GB RAM en 4 vCPU met NVMe-opslag. Met 4 GB kun je beginnen
als OpenSearch uit blijft, maar dan zit je krap zodra de import en de indexering
tegelijk lopen. EU-datacenter, want dat draagt het AVG-verhaal uit §9.

Voor de containers zelf: Shopware's eigen Docker-opzet of de kant-en-klare
dockware-images uit de community. Bij het opzetten controleren welke tag bij
Shopware 6.7 hoort.

### 3.1 Werkwijze

Het meeste werk voor de leerdoelen gebeurt in de **Shopware-admin in de browser**:
catalogus, property groups, Sales Channels, Rule Builder, SEO-instellingen,
Flow Builder. Daar is geen lokale ontwikkelomgeving voor nodig.

Code-werk komt pas bij thema-aanpassingen en eventuele plugins. Dat gaat via git:
bewerken op de werkmachine, pushen, uitrollen op de VPS. Zo blijft de VPS de enige
draaiende omgeving zonder dat de code er alleen daar bestaat.

### 3.2 Afscherming en beheer

De shop staat vanaf dag één op het open internet. Daarom meteen, niet later:

- `noindex` en toegangsbeperking (basic auth of Cloudflare Access) tot livegang.
  Een half afgebouwde shop die geïndexeerd raakt werkt leerdoel 3 actief tegen.
- Firewall dicht op alles behalve 80, 443 en SSH; SSH alleen op sleutels.
- Automatische backups van database en bestanden, inclusief één geteste restore.
  Een backup die nooit teruggezet is, is een aanname.

## 4. Catalogus en productdata

Bron is een xlsx die de eigenaar onderhoudt, gevoed vanuit FEKO's prijslijst.
Import via Shopware's ingebouwde CSV-import; de xlsx wordt eerst naar CSV omgezet.

Structuur: **producten met varianten**, niet honderden losse artikelen. Eén product
("Houtschroef RVS platkop") met varianten over property groups. Schatting: 8
categorieën, 40-60 producten, 300-500 varianten.

Property groups (tevens de filters in de storefront):

| Groep | Voorbeeld |
|---|---|
| Materiaal | RVS, verzinkt |
| Diameter | M4, M5, M6 |
| Lengte | 20, 30, 40 mm |
| Kopvorm | platkop, bolkop, verzonken |
| Verpakkingsaantal | 100, 200, 500 stuks |

Verder per variant: eigen artikelnummer, eigen prijs inclusief 21% btw, gewicht, en
**EAN** — dat laatste vooruitlopend op bol.com, zie §8.

Inkoopprijzen en marges blijven in de spreadsheet en komen niet in Shopware.

**Voorraad staat uit.** Artikelen zijn altijd bestelbaar (geen closeout), omdat FEKO
levert en wij geen voorraadstand hebben. Gevolg: af en toe wordt iets verkocht dat
FEKO niet heeft. Ondervanging: zichtbare levertijdmelding en terugbetalen bij
nee-verkoop.

## 5. Leerdoelen, vertaald naar Shopware

| Leerdoel | Waar het landt |
|---|---|
| Doelgroepgericht promoten | Sales Channels (eigen domein, design en taal op dezelfde catalogus) plus Rule Builder voor voorwaardelijke prijzen, verzendmethoden en promoties |
| Locatiegericht promoten | Landingspagina's per regio via Shopping Experiences, eigen SEO-URL's, gestructureerde data en Google Business Profile — grotendeels platformonafhankelijk werk |
| SEO | SEO-URL-templates, meta-velden, sitemap en canonicals zitten in Shopware; Core Web Vitals vragen cache- en tuningwerk, want Shopware is niet snel out of the box |
| Marketing | Flow Builder voor automatisering, promoties en kortingscodes, nieuwsbrief-integratie |

Dat laatste punt is een echte spanning met leerdoel 3: een statische site is snel
by default, Shopware niet. Die tuning is hier onderdeel van het leren, geen bijzaak.

## 6. Betalen en verzenden

Betalen via de officiële Mollie-plugin voor Shopware 6, met iDEAL als primaire
methode. €0,32 per iDEAL-transactie, geen vaste kosten. Te verifiëren bij installatie:
pluginversie tegen Shopware 6.7.

Verzendkosten bij livegang: vast €6,95, gratis boven €75. Gewicht staat per variant
in de data, zodat een zwaartestaffel via de Rule Builder toegevoegd kan worden zodra
FEKO's dropship-tarief bekend is.

Met FEKO te regelen: tarief per zending, wat er gebeurt boven 10 kg (daar zetten
zowel PostNL als DHL een klasse-sprong), en wie de retourvracht betaalt — dat laatste
wordt bij 14 dagen bedenktijd anders een structurele kostenpost.

Marktbenchmark voor die onderhandeling: PostNL zakelijk circa €7,10, DHL circa €6,45
naar een huisadres, circa €5,45 via MyParcel bij ~150 zendingen per maand. Zit FEKO
daar duidelijk boven, dan verdient zelf verzenden een herberekening.

Terugbetalingen gaan via het Mollie-dashboard of de Shopware-administratie.

## 7. Orderafhandeling

Order komt binnen in Shopware. De eigenaar bestelt handmatig bij FEKO, FEKO verzendt
naar de klant. Geen koppeling met FEKO bij livegang — die bouw je pas als het
handwerk pijn doet, en dan pas weet je ook wat je precies moet koppelen.

## 8. bol.com

Wordt nu niet gebouwd. Eén voorbereiding die later niet in te halen is: EAN per
variant. Zonder EAN kun je op bol niet aanbieden.

Waarschuwing voor dat moment: bol rekent hard af op levertijd en annuleringen, dus
"geen voorraadstand" wordt daar duurder dan op de eigen site.

## 9. Juridisch en privacy

Verplicht: algemene voorwaarden, retourrecht van 14 dagen inclusief modelformulier,
privacy- en cookiebeleid, zichtbare verzend- en betaalinformatie, KvK- en btw-nummer
in de footer. Als dropshipper ben jij de verkoper: retouren en garantie komen bij jou
terecht, ook al zie je het pakket nooit.

AVG wordt met deze keuze eenvoudiger dan met elk SaaS-alternatief: klantgegevens staan
op de eigen EU-server. Verwerkers zijn de hoster en Mollie (Nederlands), plus een
mailprovider indien die niet zelf gehost wordt. Shopware heeft cookie-consent
ingebouwd. Verwerkingsregister en privacyverklaring benoemen alle partijen.

## 10. Wat we bewust niet bouwen

Geen B2B Suite, geen custom plugins zolang standaardfunctionaliteit volstaat, geen
FEKO-koppeling, geen voorraadbeheer, geen admin-maatwerk, geen meertaligheid.

Geen headless frontend in fase 0 t/m 4. De standaard Twig-storefront volstaat, en
headless kost precies wat Shopware hier moest opleveren: Sales Channels worden weer
bouwwerk, Shopping Experiences moeten per bloktype nagebouwd worden, en de checkout
komt opnieuw op tafel.

**Wel als fase 5 vastgelegd:** zodra de shop draait, een headless storefront als
tweede Sales Channel voor één doelgroep, naast de Twig-versie zodat ze te vergelijken
zijn. Framework: Astro, omdat de eigenaar daar zijn overige sites in bouwt. De
Shopware API-client is framework-onafhankelijk; waar een Vue-composable van Shopware
toch nodig is, kan die als island in Astro. Bevalt Astro, dan kunnen de Twig-kanalen
daarna één voor één vervangen worden, met de werkende Twig-shop als vangnet.

## 11. Fasering

| Fase | Resultaat |
|---|---|
| 0 | VPS ingericht, Shopware draait in Docker en is afgeschermd bereikbaar; Astro verwijderd uit de repo |
| 1 | Catalogus: categorieën, property groups, import vanuit de FEKO-lijst, filters werkend |
| 2 | Mollie, verzendmethode, juridische pagina's, testbestelling end-to-end |
| 3 | Livegang: eigen domein, TLS, `noindex` eraf, backups getest, Cloudflare ervoor |
| 4 | Leerdoelen: Sales Channels, Rule Builder, SEO en Core Web Vitals, Flow Builder |

## 12. Verificatie

- Een validatiescript over de importlijst dat faalt bij dubbele artikelnummers,
  prijs ≤ 0, ontbrekende verplichte velden of een onbekende categorie. Een kapotte
  spreadsheet mag nooit een schroef van €0,00 live zetten.
- Eén complete testbestelling met Mollie in testmodus: product kiezen, variant kiezen,
  afrekenen, betalen, orderbevestiging, order zichtbaar in de administratie.
- Vóór livegang: Lighthouse-meting als nulmeting voor leerdoel 3.

## 13. Open punten vóór livegang

1. Dropship-afspraken met FEKO: tarief per zending, retourprocedure, en of er blanco
   verzonden wordt zonder FEKO-branding.
2. Domein: `justscrewit.nl` staat bij Cloudflare. De shop draait op `shop.justscrewit.nl`; de root is in gebruik en wordt later gekoppeld. (Afgerond 24 sep 2026.)
3. Mailprovider kiezen met EU-verwerking, of mail via de eigen server.
4. VPS-provider kiezen en de eerste restore-test uitvoeren in fase 0.
