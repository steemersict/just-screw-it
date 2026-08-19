# Webshop Just Screw It — ontwerp

Datum: 2026-08-19
Branch: `feature/webshop`
Status: ter review

## 1. Wat we bouwen

Een B2C-webshop voor bevestigingsmateriaal, gedropshipt via FEKO BV. 300-500 SKU's
in acht categorieën. Gastcheckout, iDEAL, prijzen inclusief btw, geen klantaccounts,
geen voorraadstand.

De webshop wordt de hoofdsite. De bestaande hardloop-landingspagina verhuist naar
een subpagina en blijft verder ongewijzigd.

## 2. Stack en waarom

| Onderdeel | Keuze |
|---|---|
| Frontend | Astro 5 (bestaand), statische catalogus |
| Hosting | Cloudflare Workers |
| Orders | Cloudflare D1 |
| Betalen | Mollie (iDEAL), €0,32 per transactie |
| Ordermail | nog te kiezen, zie open punt 10.3 |
| Productdata | xlsx → `products.json` in de repo |

Afgewogen en afgevallen:

- **Snipcart** — minste code, maar DPA dateert uit mei 2018, noemt geen
  doorgiftemechanisme, geen hostinglocatie en geen subverwerkerslijst. Bovendien
  2% per transactie en orders buiten eigen beheer, wat botst met de bol.com-plannen.
- **WooCommerce / Shopware** — betekent een PHP-applicatie en het einde van deze
  codebase; Shopware is bij 500 SKU's B2C bovendien overgedimensioneerd.
- **Payload CMS + plugin-ecommerce op Workers** — geeft een klik-admin, maar
  Payload-op-Workers is een pilot (OpenNext-adapter, zelfgebouwde D1-adapter) en de
  ecommerce-plugin heeft Stripe als standaardadapter, dus voor iDEAL schrijf je
  alsnog zelf een Mollie-adapter.
- **Merchant (Workers + D1 + Hono)** — de maker adviseert het zelf af voor productie.
- **Medusa / Vendure** — draaien niet op Workers; vereisen een langlopende
  Node-server met Postgres.

## 3. Architectuur

Statische catalogus, dynamische checkout.

```
products.xlsx  ──npm run import──▶  src/data/products.json  ──build──▶  statische pagina's
                                                            └────────▶  /producten.json (filterindex)

browser ──POST /api/checkout──▶ Worker ──▶ Mollie ──▶ betaalpagina
                                   │
Mollie ──POST /api/mollie-webhook──▶ Worker ──▶ D1 (orders) ──▶ ordermail
```

De catalogus zit in de build en kost bij het bekijken geen enkele serveraanroep.
Alleen afrekenen raakt een Worker.

### 3.1 Meerdere frontends later

De backend is vanaf dag één een JSON-API, zodat een tweede, doelgroepgerichte
frontend dezelfde Worker en dezelfde `products.json` kan gebruiken. Wat we nu
bewust *niet* bouwen: kanalen- of tenantmodel, GraphQL, aparte backend-service,
authenticatie.

**Bekend plafond:** doelgroepgerichte content is gratis, doelgroepgerichte prijzen
niet. Zodra een tweede frontend eigen prijzen krijgt (bijvoorbeeld zakelijke
staffels), kunnen prijzen niet meer in de build gebakken worden. Upgradepad:
prijzen uit D1 serveren in plaats van uit JSON, met de catalogus als fallback.

## 4. Productdata

Bron is een xlsx die de eigenaar onderhoudt, gevoed vanuit FEKO's prijslijst.
De build leest géén Excel. `npm run import` zet de xlsx om naar
`src/data/products.json`, dat wordt meegecommit. Voordelen: prijswijzigingen zijn
zichtbaar als diff, de build blijft simpel, en een kapotte spreadsheet haalt de
shop niet stilletjes onderuit.

Structuur: families met varianten. Eén pagina per familie ("Houtschroef RVS
platkop"), met een kiezer voor de maat. Elke variant is een eigen SKU met eigen
prijs. Schatting: 8 categorieën, 40-60 families, 300-500 SKU's.

Velden per SKU:

| Veld | Verplicht | Opmerking |
|---|---|---|
| `sku` | ja | uniek |
| `familie` | ja | verwijst naar bestaande familie |
| `categorie` | ja | één van de acht |
| `naam` | ja | |
| `prijs_incl_btw` | ja | eurocent, integer |
| `btw_tarief` | ja | 21 |
| `verpakkingsaantal` | ja | stuks per doos/zak |
| `materiaal` | ja | facet, bijv. RVS / verzinkt |
| `diameter_mm` | nee | facet |
| `lengte_mm` | nee | facet |
| `kopvorm` | nee | facet |
| `gewicht_gram` | nee | wordt verplicht zodra verzenden op gewicht gaat, zie §7 |
| `ean` | nee | vooruitlopend op bol.com, zie §9 |
| `afbeelding` | nee | valt terug op categoriebeeld |

Inkoopprijzen en marges blijven in de spreadsheet en komen niet in de repo of de HTML.

## 5. Pagina's en URL's

```
/                              home, shop
/{categorie}/                  8 categoriepagina's
/{categorie}/{familie}/        familiepagina met variantkiezer
/zoeken                        zoeken en filteren
/winkelwagen
/afrekenen
/bestelling/{id}               bevestiging na betaling
/hardlopen                     bestaande landingspagina, verhuisd
/algemene-voorwaarden /retourneren /privacy /verzenden-en-betalen /contact
```

## 6. Zoeken en filteren

Hier zit de waarde van deze shop: bij bevestigingsmateriaal is het vinden van de
juiste schroef het hele probleem.

Eén index van ~500 items (±100 kB) wordt bij de build gegenereerd en filtert
client-side. Facetten: categorie, materiaal, diameter, lengte, kopvorm,
verpakkingsaantal. Tekstzoek op naam en SKU, zodat "M6x40 rvs" werkt.

Geen zoekserver, geen Algolia. Bij deze omvang is dat overhead zonder opbrengst.

## 7. Winkelwagen, verzending en afrekenen

Winkelwagen in `localStorage`, alleen SKU's en aantallen — nooit prijzen.

Afrekenen:

1. Browser POST't SKU's en aantallen naar `/api/checkout`.
2. De Worker **herberekent alle prijzen server-side** uit `products.json`. Prijzen
   uit de client worden genegeerd.
3. Worker maakt een Mollie-betaling en schrijft de order als `open` in D1.
4. Browser volgt de Mollie-betaallink.
5. Mollie roept `/api/mollie-webhook` aan; de Worker haalt de status op bij Mollie
   (vertrouwt de webhook-inhoud niet), werkt de order bij en verstuurt de ordermail.
   De webhook is idempotent: dezelfde melding tweemaal verwerken verandert niets.

Verzendkosten bij livegang: vast €6,95, gratis boven €75. `gewicht_gram` staat wel
in de data maar wordt nog niet gebruikt, zodat er een zwaartestaffel bij kan zodra
FEKO's dropship-tarief bekend is, zonder de productdata opnieuw te maken.

Er lopen gesprekken met FEKO over een vast dropship-tarief; zodra dat er is, wordt
dat de basis onder het verzendtarief. Punten om daar te regelen: tarief per
zending, wat er gebeurt boven 10 kg, en wie de retourvracht betaalt.

Marktbenchmark voor die onderhandeling: PostNL zakelijk circa €7,10, DHL circa
€6,45 naar een huisadres, circa €5,45 via MyParcel bij ~150 zendingen per maand.

Terugbetalingen gaan met de hand via het Mollie-dashboard. Geen code.

## 8. Orderafhandeling

Order komt binnen per mail en staat in D1. De eigenaar bestelt handmatig bij FEKO,
FEKO verzendt naar de klant. Geen admin-UI bij livegang. Een read-only orderpagina
komt er pas als de mailstroom gaat irriteren.

Zonder voorraadstand wordt af en toe iets verkocht dat FEKO niet heeft. Dat is een
bewuste keuze. Ondervanging: zichtbare levertijdmelding op productpagina's en
terugbetalen bij nee-verkoop.

## 9. bol.com

Wordt nu niet gebouwd. Eén voorbereiding die later niet in te halen is: `ean` per
SKU in het schema. Zonder EAN kun je op bol niet aanbieden.

Waarschuwing voor dat moment: bol rekent hard af op levertijd en annuleringen, dus
"geen voorraadstand" wordt daar duurder dan op de eigen site.

## 10. Juridisch en privacy

### 10.1 Verplichte pagina's
Algemene voorwaarden, retourrecht van 14 dagen inclusief modelformulier,
privacy- en cookiebeleid, zichtbare verzend- en betaalinformatie, KvK- en
btw-nummer in de footer. Als dropshipper ben jij de verkoper: retouren en garantie
komen bij jou terecht, ook al zie je het pakket nooit.

### 10.2 AVG
Klantgegevens staan in D1 op het eigen Cloudflare-account, met EU-locatiehint.
Verwerkers: Cloudflare, Mollie (Nederlands) en de mailprovider. Verwerkingsregister
en privacyverklaring benoemen alle drie.

### 10.3 Open punten vóór livegang
1. Dropship-afspraken met FEKO vastleggen: tarief per zending, retourprocedure,
   of er blanco (zonder FEKO-branding) verzonden wordt.
2. Mailprovider kiezen met EU-verwerking; Resend is Amerikaans, dus regio en DPA
   controleren of een EU-alternatief nemen.
3. D1 aanmaken met EU-locatiehint en dat verifiëren.
4. Domeinnaam bepalen: `justscrewitrunning.com` staat nu in `astro.config.mjs` en
   past niet bij een bevestigingsmaterialenshop.

## 11. Wat we bewust niet bouwen

Geen klantaccounts, geen voorraadbeheer, geen wishlist, geen reviews, geen
meertaligheid, geen B2B-prijzen, geen PIM, geen admin-UI, geen adapterlaag rond
Mollie, geen kanalenmodel.

## 12. Verificatie

Eén runnable check: een validatiescript over `products.json` dat faalt bij dubbele
SKU's, prijs ≤ 0, ontbrekende verplichte velden, een variant zonder bestaande
familie, of een onbekende categorie. Draait in de build, zodat een kapotte
spreadsheet nooit een schroef van €0,00 live zet.

Daarnaast tests op het enige echt kritische stuk logica: de prijsherberekening in
`/api/checkout` (client-prijzen worden genegeerd, totaal klopt, verzendgrens werkt)
en de idempotentie van de Mollie-webhook.
