# Lokationsbündel: zwei Architekturen im Vergleich

## Gegenüberstellung der konsultierten Fassung mit einem ressourcenorientierten Referenzentwurf

**Anlage zur Stellungnahme zur Konsultation Mitteilung Nr. 57 der Bundesnetzagentur**

---

**Gegenstand des Vergleichs**

| | |
|:------------------|:-------------------------------------------------------------|
| Konsultierte Fassung | `api/masterData/locationBundleV1.yaml`, Branch `2026-07-31-consultation`, Repository `EDI-Energy/api-electricity` |
| Referenzentwurf | `openapi/netzbetreiber-api.yaml` — https://github.com/engrate/mako-api-referenzentwurf/tree/konsultation-2026-08 |
| Fachlicher Umfang | identisch — Übermittlung, Antwort, Clearing und Netzbetreiberwechsel von Lokationsbündeln |
| Stand der Auswertung | 21.08.2026 |

**Zweck dieses Dokuments.** Die Stellungnahme trägt vor, dass die konsultierten Dienste keine ressourcenorientierten Web-APIs sind, sondern asynchroner Dokumentenversand über HTTP. Dieses Dokument belegt die Behauptung nicht durch Begriffe, sondern durch Ablaufvergleiche: Es spielt vier reale Geschäftsvorfälle in beiden Varianten durch und zählt Aufrufe, Fehlermöglichkeiten, Zustandshaltung und Clearing-Anlässe.

**Was der Referenzentwurf nicht ist.** Er ist kein vollständiger Ersatzvorschlag und kein offizielles Dokument. Er lässt Themen bewusst offen, die für den Nachweis nicht erforderlich sind — Massendatenerstbefüllung, Archivierung, Mandantentrennung. Er ändert keine Fachlichkeit: Identifikatoren, Zeitpunkt-Semantik, Marktrollen und die Antwortcodes der Entscheidungsbaumdiagramme sind unverändert übernommen.

---

# 1. Der strukturelle Unterschied in einem Satz

In der konsultierten Fassung **versendet** der Netzbetreiber das Lokationsbündel an alle Berechtigten, die es lokal replizieren. Im Referenzentwurf **hält** der Netzbetreiber das Lokationsbündel, und die Berechtigten **rufen es ab**, wenn sie es brauchen.

Alles Weitere folgt daraus.

---

# 2. Was die Spezifikationen objektiv unterscheidet

Die folgenden Angaben sind aus den Spezifikationsdateien ausgezählt, nicht geschätzt.

| Merkmal | Konsultierte Fassung | Referenzentwurf |
|:-----------------------------|:-------------------------------|:-------------------------------|
| OpenAPI-Version | 3.0.0 | 3.1.0 |
| Pfade | 4 | 14 |
| Operationen | 4 | 22 |
| HTTP-Verben | nur `POST` | `GET` 13, `PUT` 2, `POST` 3, `PATCH` 2, `DELETE` 2 |
| Leseoperationen | 0 | 13 |
| `operationId` vergeben | 0 von 4 | 22 von 22 |
| Response-Bodies definiert | 0 (auch nicht für `400`/`422`) | für alle Operationen |
| Fehlerformat | nicht definiert | RFC 9457 Problem Details mit JSON-Pointer |
| `securitySchemes` | nicht vorhanden | OAuth 2.0 mit Scopes, mTLS als Alternative |
| `servers` | nicht vorhanden | mit Variablenmuster für die Verzeichnisdienstauflösung |
| `oneOf` / `discriminator` | 1 / 0 | 9 / 3 |
| `additionalProperties: false` | 0 Schemas | alle Knoten- und Kantentypen |
| Zeitscheiben-Ende | kein Feld — implizit | `validTo` explizit, `null` für offen |
| Paginierung / Filterung / Sortierung | nicht vorhanden | auf allen Listenressourcen |
| Nebenläufigkeitsschutz | nicht vorhanden | `ETag` / `If-Match` |
| Zwischenspeicherbarkeit | nicht möglich | `ETag`, `Cache-Control`, `Last-Modified`, `304` |
| Abkündigung | Freitext | `Deprecation` / `Sunset` nach RFC 8594 |
| Umsetzungsstand abfragbar | nein | `GET /versions` |
| Duplizierte Schemas | 4 (Clearing-Kopien) | 0 |
| Reine Array-Wrapper-Dateien | 20 von 59 | 0 |

Zwei Befunde aus der konsultierten Fassung verdienen gesonderte Erwähnung, weil sie unabhängig von der Architekturfrage zu korrigieren sind:

**`$ref` mit Geschwisterfeldern.** Praktisch jede fachliche `description` im Datenmodell steht neben einem `$ref`. In OpenAPI 3.0 ersetzt `$ref` das gesamte Objekt — diese Beschreibungen werden von jedem konformen Generator und Renderer verworfen. Die fachliche Dokumentation der Felder ist damit faktisch nicht Teil der Spezifikation. In OpenAPI 3.1 wäre dieselbe Schreibweise gültig; das ist einer der Gründe, warum der Referenzentwurf 3.1 verwendet.

**Widerspruch zwischen Prosa und Schema.** Die Pfadbeschreibung zu `/masterData/locationBundle/result/v1` sagt, der Antwortende gebe unter `locationBundleId` die ID des Bündels an. Das Schema `resultLocationBundle` enthält dieses Feld nicht. Der Bezug läuft ausschließlich über den `referenceId`-Header.

---

# 3. Vier Geschäftsvorfälle im Ablaufvergleich

Angenommene Konstellation: ein Lokationsbündel mit drei Berechtigten — Lieferant, Messstellenbetreiber, Messwertverarbeiter — und dem verantwortlichen Netzbetreiber.

## 3.1 Vorfall A: Der Lieferant will vor einem Prozessschritt wissen, ob sein Stand aktuell ist

Dies ist der häufigste und zugleich folgenreichste Vorgang. Ein Lieferant, der eine Zusage machen, eine Abrechnung erstellen oder eine Bestellung auslösen will, braucht Gewissheit über die Bündelstruktur.

**Konsultierte Fassung**

| Schritt | Aufruf | Anmerkung |
|:----------|:--------------------------------------------------|:----------------------|
| — | — | **Nicht möglich.** Es existiert kein Leseendpunkt. |

Der Lieferant hat drei Handlungsmöglichkeiten: Er verlässt sich auf den zuletzt zugesandten Stand, ohne prüfen zu können, ob dieser noch gilt. Oder er eröffnet ein Clearing, um eine Rückmeldung zu erzwingen — was den Klärfall erzeugt, den man vermeiden wollte. Oder er greift zum Telefon.

**Referenzentwurf**

| Schritt | Aufruf | Antwort |
|:----------|:--------------------------------------------------|:----------------------|
| 1 | `GET /location-bundles/F1234848431?valid-at=2027-11-01`, `If-None-Match: "a3f1c9e2"` | `304 Not Modified` — kein Nutzdatentransfer |

Ein Aufruf, keine Nutzdaten, wenige Millisekunden. Bei geändertem Stand liefert derselbe Aufruf `200` mit genau der Zeitscheibe, die zum angefragten Stichtag gilt — nicht dem gesamten Bündel.

**Bewertung.** Dies ist der wesentliche Unterschied. Ein Lieferant, der zu Prozessbeginn den aktuellen Stand abruft, kann auf einen Schiefstand reagieren, **bevor** er Zusagen macht oder Transaktionen auslöst, die anschließend nur manuell rückabzuwickeln sind. In der konsultierten Fassung ist dieser Vorgang architektonisch ausgeschlossen.

## 3.2 Vorfall B: Der Netzbetreiber ändert das Bündel, drei Berechtigte sind zu informieren

**Konsultierte Fassung**

| Schritt | Richtung | Aufruf | Nutzlast |
|:----------|:------------|:------------------------------------|:---------------------|
| 1 | NB an LF | `POST /masterData/locationBundle/v1` | vollständiges Bündel, alle Zeitscheiben |
| 2 | NB an MSB | `POST /masterData/locationBundle/v1` | dasselbe vollständige Bündel |
| 3 | NB an MWV | `POST /masterData/locationBundle/v1` | dasselbe vollständige Bündel |
| 4 | LF an NB | `POST /masterData/locationBundle/result/v1` | Antwortcode, immer positiv |
| 5 | MSB an NB | `POST /masterData/locationBundle/result/v1` | Antwortcode, immer positiv |
| 6 | MWV an NB | `POST /masterData/locationBundle/result/v1` | Antwortcode, immer positiv |

**Sechs Aufrufe**, davon drei mit vollständiger Nutzlast. Jeder der drei Berechtigten hält anschließend eine eigene Kopie des Bündels vor, die ab diesem Moment altern kann.

Zur Antwort in den Schritten 4 bis 6 ist anzumerken: Das Schema `resultLocationBundle` beschreibt ausdrücklich, die Antwort sei „immer, dass der Empfänger des Lokationsbündels die Daten übernommen hat". Es gibt keine Ablehnung. Die Antwort trägt damit keine Entscheidungsinformation — sie ist eine Empfangsbestätigung, für die HTTP bereits einen Statuscode vorsieht.

**Referenzentwurf**

| Schritt | Richtung | Aufruf | Nutzlast |
|:----------|:------------|:------------------------------------|:---------------------|
| 1 | NB intern | `PATCH /location-bundles/F1234848431` auf dem eigenen Server | nur die geänderte Zeitscheibe |
| 2 | NB an LF | Ereignis `locationBundleChanged` | Typ, Zeitpunkt, URL, ETag — rund 200 Byte |
| 3 | NB an MSB | Ereignis `locationBundleChanged` | dito |
| 4 | NB an MWV | Ereignis `locationBundleChanged` | dito |
| 5–7 | Berechtigte an NB | `GET /location-bundles/F1234848431` — **wenn und wann sie es brauchen** | nur die benötigte Zeitscheibe |

**Bewertung — hier ist der Vorteil geringer, als es zunächst scheint.** Zählt man die Schritte 5 bis 7 mit, kommt man ebenfalls auf sechs Marktkommunikationsvorgänge. Wir halten es für wichtig, das offen zu benennen, statt einen Rechenvorteil zu behaupten, den es nicht gibt.

Der Unterschied liegt nicht in der Anzahl, sondern in drei anderen Punkten:

- Die Abrufe der Schritte 5 bis 7 sind **fakultativ und zeitlich entkoppelt**. Ein Messwertverarbeiter, der die Bündelstruktur erst zum Monatsende braucht, ruft sie zum Monatsende ab — und erhält dann den dann gültigen Stand, nicht den von vor drei Wochen.
- Die Ereignisse sind **um Größenordnungen kleiner** als die Vollübermittlungen.
- Vor allem: Die Berechtigten müssen **nicht replizieren**. Wer nicht repliziert, kann keinen Schiefstand haben.

## 3.3 Vorfall C: Abweichende Sicht — eine Tranche fehlt

Der Lieferant beliefert seit dem 01.10.2027 eine dritte Tranche, die im Bündel nicht enthalten ist.

**Konsultierte Fassung**

| Schritt | Richtung | Aufruf | Anmerkung |
|:----------|:------------|:------------------------------------|:---------------------|
| 1 | NB an LF | `POST /masterData/locationBundle/v1` | Bündel wird zugestellt |
| 2 | LF an NB | `POST /masterData/locationBundle/result/v1` | Pflichtantwort, positiv — obwohl der LF widerspricht |
| 3 | LF an NB | `POST /masterData/locationBundleClearing/v1` | Reklamation |
| 4 | NB an LF | `POST /masterData/locationBundle/v1` | Korrektur als **Vollübermittlung** des gesamten Bündels |
| 5 | LF an NB | `POST /masterData/locationBundle/result/v1` | Pflichtantwort auf die Korrektur |

**Fünf Aufrufe**, davon zwei Vollübermittlungen. Bei drei Berechtigten kommen für die Korrektur zwei weitere Vollübermittlungen plus zwei Antworten hinzu: **neun Aufrufe**.

Vier strukturelle Probleme in diesem Ablauf:

1. **Der Clearing-Aufruf trägt keine Vorgangsreferenz.** Der Pfad `/locationBundleClearing/v1` kennt keinen `referenceId`-Header. Das Clearing lässt sich damit keiner konkreten vorangegangenen Übermittlung zuordnen, sondern nur der Lokation.
2. **Es gibt keinen Antwortkanal zum Clearing.** `resultLocationBundle` ist ausdrücklich die „Antwort auf die Übermittlung von Lokationsbündeln", nicht auf ein Clearing. Der Lieferant erfährt nicht, ob und wie sein Clearing bearbeitet wird — er merkt es allenfalls daran, dass irgendwann eine korrigierte Übermittlung eintrifft.
3. **Es gibt keinen definierten Endzustand.** Das Clearing hat keinen Zustand, keine Frist und keinen Abschluss. Ob ein Fall offen, in Bearbeitung oder erledigt ist, ist außerhalb der beteiligten Sachbearbeitung nicht feststellbar.
4. **Schritt 2 erzwingt eine unzutreffende Aussage.** Der Lieferant muss den Empfang mit einem Code bestätigen, der ausdrücklich Übernahme bedeutet, obwohl er widerspricht.

**Referenzentwurf**

| Schritt | Richtung | Aufruf | Antwort |
|:----------|:------------|:------------------------------------|:---------------------|
| 1 | LF an NB | `POST /location-bundles/F.../clearing-cases` mit `observedETag`, `expected`, `reason` | `201 Created` mit `Location` auf den Fall |
| 2 | NB intern | `PATCH /location-bundles/F...` — Korrektur | — |
| 3 | NB intern | `PATCH /clearing-cases/{id}` zu `state: beigelegt`, `resolution.correctedBundle` | — |
| 4 | NB an LF, MSB, MWV | Ereignis `clearingCaseResolved` bzw. `locationBundleChanged` | — |
| 5 | LF an NB | `GET /clearing-cases/{id}` — optional, sofern der LF nicht dem Ereignis vertraut | `200` mit Zustand und Verweis auf den korrigierten Stand |

**Zwei Marktkommunikationsaufrufe** in der Pflicht, dazu Ereignisse und fakultative Abrufe. Der Fall hat eine URL; beide Seiten können jederzeit abrufen, wie der Stand ist. `observedETag` hält fest, auf welchen Stand sich der Fall bezieht, auch wenn der Netzbetreiber zwischenzeitlich ändert. Der Zustandsübergang ist im Schema festgelegt; ein unzulässiger Übergang wird mit `422` und Begründung abgelehnt.

Die Antwortcodes der Entscheidungsbaumdiagramme bleiben erhalten — sie werden lediglich an einer Ressource mit Zustand geführt statt in einem Aufruf ohne Rückbezug.

## 3.4 Vorfall D: Ein neuer Lieferant übernimmt eine Marktlokation

**Konsultierte Fassung.** Der Lieferant kann nichts tun. Er ist darauf angewiesen, dass der Netzbetreiber ihm das Bündel aktiv zusendet. Bleibt die Zusendung aus — weil sie übersehen wurde, weil die Berechtigung im System des Netzbetreibers noch nicht gepflegt war, weil die Zustellung fehlschlug —, gibt es keinen Weg, sie anzufordern. Der Lieferant beginnt die Belieferung ohne Kenntnis der Bündelstruktur oder klärt telefonisch.

**Referenzentwurf**

| Schritt | Aufruf | Antwort |
|:----------|:--------------------------------------------------|:----------------------|
| 1 | `GET /location-bundles?market-location=57685676748` | Liste der Bündel, die diese Marktlokation enthalten |
| 2 | `GET /location-bundles/{id}?valid-at=2027-11-01` | Die zum Lieferbeginn gültige Zeitscheibe |

Selbstbedienung, sobald die Berechtigung besteht. Kein Wartezustand, kein Anlass für einen Klärfall.

---

# 4. Zusammenfassung des Ablaufvergleichs

| Vorfall | Konsultiert | Referenzentwurf | Wesentlicher Unterschied |
|:--------------------------|:-------------------|:------------------|:-------------------------------------|
| A — Stand prüfen | nicht möglich | 1 Aufruf, meist ohne Nutzdaten | Schiefstand wird erkennbar, **bevor** Folgehandlungen ausgelöst werden |
| B — Änderung verteilen | 6 Aufrufe, 3 Vollübermittlungen | 3 Ereignisse plus fakultative Abrufe | Abruf zeitlich entkoppelt; keine Replikation beim Berechtigten |
| C — Reklamation | 5 bis 9 Aufrufe, kein Endzustand | 2 Aufrufe, Vorgang mit Zustand und Frist | Clearing wird nachvollziehbar und abschließbar |
| D — neuer Berechtigter | nicht möglich | 2 Aufrufe | Selbstbedienung statt Wartezustand |

Der Ablaufvergleich zeigt, dass die Zahl der Aufrufe nicht das entscheidende Kriterium ist — in Vorfall B ist sie vergleichbar. Entscheidend ist, dass zwei der vier alltäglichen Vorgänge in der konsultierten Fassung architektonisch **gar nicht** durchführbar sind und in der Praxis auf manuelle Klärung ausweichen müssen.

---

# 5. Fachliche Bedingungen: vom Anwendungshandbuch in das Schema

Der Referenzentwurf enthält zwei Negativbeispiele, die belegen sollen, dass die Verlagerung fachlicher Bedingungen in das Schema kein theoretischer Gewinn ist.

## 5.1 Pauschale Messlokation mit OBIS-Kennzahl

Mitteilung Nr. 57 sieht vor, dass künftig jede Marktlokation Strom mindestens eine zugeordnete Messlokation aufweist — bei zählerlosen Marktlokationen eine pauschale Messlokation ohne Messeinrichtung.

Der Payload `04-UNGUELTIG-pauschal-mit-obis.json` ordnet einer pauschalen Messlokation eine Konfigurations-ID und eine OBIS-Kennzahl zu. Fachlich ist das unmöglich.

- **In der konsultierten Fassung** wäre dieser Payload schemagültig. Die Unterscheidung zwischen pauschaler und gemessener Messlokation ist dort nicht modelliert; die Bedingung steht als natürlichsprachliche Bedingung im Anwendungshandbuch und wird von jedem Marktpartner eigenständig implementiert. Der Fehler fällt im Produktivbetrieb auf — als Klärfall.
- **Im Referenzentwurf** ist `metering` eine tagged union über `iMS`, `mME` und `pauschal`. Der Typ `pauschal` sieht weder `configurationId` noch `obisCodes` vor, und `additionalProperties: false` schließt sie aus. Jeder Standardvalidator lehnt den Payload zur Entwurfszeit ab, mit JSON-Pointer auf die Fundstelle.

## 5.2 Unzulässige Zuordnung

Der Payload `05-UNGUELTIG-unzulaessige-kante.json` ordnet eine Marktlokation unmittelbar einer Netzlokation zu. Im Datenmodell hängen Marktlokationen an Messlokationen.

Der Referenzentwurf modelliert die Zuordnungen als typisierte Kanten mit einem abschließenden Katalog zulässiger Quell-Ziel-Kombinationen. Die unzulässige Kante wird abgelehnt.

Dies beantwortet zugleich einen Antrag aus der Stellungnahme: Der dort geforderte Katalog fachlicher Validierungsregeln für Lokationsbündel muss nicht als Prosa im Anwendungshandbuch stehen. Er kann Teil des Schemas sein und ist dann automatisiert prüfbar.

## 5.3 Prüfnachweis

Das beiliegende Prüfwerkzeug `tools/validate.py` validiert die Spezifikation gegen OpenAPI 3.1 und jedes Beispiel gegen das zugehörige Schema. Für die Negativbeispiele gilt die umgekehrte Erwartung: Werden sie akzeptiert, schlägt die Prüfung fehl.

```
1. OpenAPI-Spezifikation
   OK  netzbetreiber-api.yaml ist gültiges OpenAPI 3.1.0
       14 Pfade, 22 Operationen, 61 Schemas
       Verbverteilung: GET=13, PUT=2, POST=3, PATCH=2, DELETE=2

2. Beispiele gegen die Schemas
   OK  01-pauschale-marktlokation.json
   OK  02-ueberschusseinspeisung.json
   OK  03-speicher-ladepunkt.json
   OK  04-UNGUELTIG-pauschal-mit-obis.json
       erwartungsgemäß abgelehnt bei /data/timeSlices/0/members/1
   OK  05-UNGUELTIG-unzulaessige-kante.json
       erwartungsgemäß abgelehnt bei /data/timeSlices/0/relations/0
   OK  06-clearing-fall.json
   OK  07-aenderungsereignis.json

Alle Prüfungen bestanden.
```

---

# 6. Antizipierte Einwände

Wir halten es für redlich, die Einwände gegen den Vorschlag selbst zu benennen und zu beantworten, statt sie abzuwarten.

## „Synchrone Abfragen erzeugen Lastspitzen, die Netzbetreiber nicht bewältigen können."

Das ist der ernsthafteste Einwand. Drei Antworten:

Erstens sind Lokationsbündel Stammdaten, die sich selten ändern. `ETag`, `Cache-Control` und bedingte Anfragen führen dazu, dass der überwiegende Teil der Abrufe mit `304` ohne Nutzdaten beantwortet wird. HTTP ist bei korrekter Nutzung von Caching auf genau dieses Lastprofil ausgelegt.

Zweitens ist die Lastspitze im Push-Modell nicht kleiner, sondern nur anders verteilt: Dort erzeugt jede Änderung sofort eine Vollübermittlung an jeden Berechtigten, unabhängig davon, ob dieser die Daten braucht. Im Pull-Modell entsteht Last nur bei tatsächlichem Bedarf.

Drittens: Die Stellungnahme beantragt ohnehin Mindestanforderungen an Verfügbarkeit und Kapazität sowie eine normierte Retry-Strategie. Diese Anforderungen sind im Pull-Modell nicht höher — sie werden dort nur sichtbar, weil das Verhalten des Gegenübers unmittelbar spürbar ist.

## „Netzbetreiber müssten dann erstmals eine Serverinfrastruktur betreiben."

Das müssen sie ohnehin. Die konsultierten Dienste sind bidirektional: Jeder Marktpartner muss alle vier Endpunkte serverseitig implementieren, um Übermittlungen, Antworten und Clearings entgegenzunehmen. Die Stellungnahme weist darauf hin, dass für Netzbetreiber ohne bisherige API-Anbindung damit ohnehin ein neues Betriebsmodell entsteht.

Der Unterschied ist gering: Statt vier `POST`-Endpunkten sind Leseoperationen bereitzustellen. Leseoperationen sind der besser beherrschte Fall — sie sind zustandslos, cachefähig, horizontal skalierbar und lassen sich einem vorgelagerten Dienst überlassen.

## „Der Versand ist revisionssicher, der Abruf nicht."

Der Einwand trifft nicht zu. Auch im Referenzentwurf protokolliert der Verantwortliche jede Änderung mit Zeitpunkt und `ETag`, und jeder Abruf ist serverseitig protokollierbar. Der Unterschied besteht darin, **wo** der Nachweis geführt wird: beim Verantwortlichen statt bei jedem Empfänger einzeln. Das ist die verlässlichere Konstruktion, weil es genau eine Wahrheit gibt statt n Kopien.

Für den Nachweis, welchen Stand ein Berechtigter zu einem bestimmten Zeitpunkt gesehen hat, sieht der Entwurf `observedETag` im Clearing-Fall vor.

## „Das ist ein zu großer Bruch für den Termin 01.10.2027."

Der Referenzentwurf ist nicht als Ersatz für die konsultierte Fassung zum Termin gedacht. Die Stellungnahme schlägt in Abschnitt 3.9 vor, mindestens einen Dienst zusätzlich als ressourcenorientierten Lesedienst auf einem Entwicklungsserver bereitzustellen und in der Konsultationsrunde Februar 2027 über die Übernahme zu entscheiden. Der Termin bleibt unberührt.

Dass dieser Entwurf mit begrenztem Aufwand entstehen konnte, weil das Datenmodell bereits erarbeitet ist, stützt die Einschätzung, dass der Pilotaufwand überschaubar wäre.

## „Ohne zentrale Instanz ist die Endpunktauflösung ungelöst."

Sie ist im Referenzentwurf identisch zur konsultierten Fassung gelöst: über den dezentralen Verzeichnisdienst. Der `servers`-Block bildet dies als Variablenmuster ab, statt leer zu bleiben.

---

# 7. Was der Referenzentwurf nicht ändert

Damit kein Missverständnis entsteht:

- **Identifikatoren** — Lokationsbündel-ID, NeLo-ID, MaLo-ID, MeLo-ID, TR-ID, SR-ID, Marktpartner-ID sind unverändert übernommen, einschließlich der Prüfmuster.
- **Marktrollen und Zuständigkeiten** — der Netzbetreiber bleibt der Verantwortliche für das Lokationsbündel.
- **Entscheidungsbaumdiagramme und Antwortcodes** — unverändert, lediglich an einer Ressource mit Zustand geführt.
- **Zeitpunkt-Semantik** — der Tagesbeginn 00:00 Uhr gesetzlicher deutscher Zeit bleibt maßgeblich. Der Entwurf überträgt ihn als Kalenderdatum statt als UTC-Zeitstempel, weil das weniger fehleranfällig ist, drückt aber denselben Sachverhalt aus.
- **Sicherheitsniveau** — Zertifikate der Smart-Metering-PKI bleiben die Grundlage. OAuth 2.0 tritt hinzu, um Zugriffe abzubilden, die eine reine Marktpartner-Authentisierung nicht abdecken kann.
- **Fachlicher Inhalt des Lokationsbündels** — dieselben Objekte, dieselben Zuordnungen, dieselben Zeitscheiben.

---

# 8. Inhalt der Anlage

```
referenzentwurf/
├── README.md                          Einstieg und Hinweise zur Prüfung
├── openapi/
│   └── netzbetreiber-api.yaml         OpenAPI 3.1, 14 Pfade, 22 Operationen, 61 Schemas
├── examples/
│   ├── 01-pauschale-marktlokation.json     pauschale MaLo ohne Zähler
│   ├── 02-ueberschusseinspeisung.json      PV mit Eigenverbrauch, zwei Zeitscheiben
│   ├── 03-speicher-ladepunkt.json          Speicher, Ladepunkt, Kaskade, Tranchen
│   ├── 04-UNGUELTIG-pauschal-mit-obis.json Negativbeispiel: muss abgelehnt werden
│   ├── 05-UNGUELTIG-unzulaessige-kante.json Negativbeispiel: muss abgelehnt werden
│   ├── 06-clearing-fall.json               Clearing-Fall mit Zustand und Abschluss
│   └── 07-aenderungsereignis.json          leichtgewichtiges Änderungsereignis
├── tools/
│   └── validate.py                    Prüfwerkzeug für Spezifikation und Beispiele
└── Gegenueberstellung.md              dieses Dokument
```

Die Anlage steht unter CC0 zur freien Verwendung, einschließlich der Übernahme in offizielle Dokumente. Öffentlich abrufbar unter https://github.com/engrate/mako-api-referenzentwurf/tree/konsultation-2026-08 — der eingereichte Stand ist dort als Tag `konsultation-2026-08` festgehalten.

---

**Hinweis.** Dieser Referenzentwurf ist ein Konsultationsbeitrag und kein offizielles Dokument der Bundesnetzagentur, des BDEW oder der Projektgruppe EDI@Energy. Die Auswertung der konsultierten Spezifikation erfolgte am 21.08.2026 auf dem Branch `2026-07-31-consultation`.
