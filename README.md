# MaKo-API — Referenzentwurf

[![Validierung](https://github.com/engrate/mako-api-referenzentwurf/actions/workflows/validate.yml/badge.svg)](https://github.com/engrate/mako-api-referenzentwurf/actions/workflows/validate.yml)
[![Lizenz: CC0-1.0](https://img.shields.io/badge/Lizenz-CC0--1.0-lightgrey.svg)](LICENSE)

**Ressourcenorientierter Referenzentwurf für den MaKo-Webdienst Lokationsbündel.**

Anlage zur Stellungnahme der Engrate AB zur Konsultation **Mitteilung Nr. 57** der
Bundesnetzagentur (Datenformate zur Abwicklung der Marktkommunikation, Frist 31.08.2026).

Der eingereichte Stand ist unter dem Tag
[`konsultation-2026-08`](https://github.com/engrate/mako-api-referenzentwurf/tree/konsultation-2026-08)
festgehalten. Verweise in der Stellungnahme und in den Konsultationsbeiträgen zeigen auf
diesen Tag, nicht auf `main`.

> **Kein offizielles Dokument** der Bundesnetzagentur, des BDEW oder der Projektgruppe
> EDI@Energy. Konsultationsbeitrag eines Marktteilnehmers.

## Worum es geht

Die Stellungnahme trägt vor, dass die konsultierten „API-Webdienste" keine
ressourcenorientierten Web-APIs sind, sondern asynchroner Dokumentenversand über HTTP —
und dass damit das strukturelle Grundproblem der Marktkommunikation, die replizierte
Stammdatenhaltung, unverändert in die neue Technik übernommen wird.

Dieser Entwurf belegt, dass es anders geht. Er modelliert denselben Fachinhalt wie
`api/masterData/locationBundleV1.yaml` (Branch `2026-07-31-consultation`) —
ressourcenorientiert, nach den Empfehlungen des gemeinsamen Konsultationsbeitrags
„Gestaltung von Web-APIs für die Marktkommunikation" (decarbon1ze, Mako365, hochfrequenz,
metiundo, Kraken, sonnen) vom Oktober 2025 zur Konzeptkonsultation der Mitteilung Nr. 53.

Er ändert **keine Fachlichkeit**: Identifikatoren, Zeitpunkt-Semantik, Marktrollen und die
Antwortcodes der Entscheidungsbaumdiagramme sind unverändert übernommen. Geändert wird
ausschließlich das Kommunikationsmuster.

## Prüfen

```bash
pip install -r requirements.txt
python3 tools/validate.py
```

Dieselbe Prüfung läuft bei jedem Push automatisch über GitHub Actions — das Ergebnis steht
im Badge oben. Der Konsultationsbeitrag trägt vor, fachliche Bedingungen gehörten in das
Schema und seien dort automatisiert prüfbar; dieser Workflow ist der Beleg dafür.

Das Werkzeug validiert die Spezifikation gegen OpenAPI 3.1 und jedes Beispiel gegen das
zugehörige Schema. Für die beiden mit `UNGUELTIG` benannten Beispiele gilt die umgekehrte
Erwartung: Werden sie akzeptiert, schlägt die Prüfung fehl — denn dann leistet das Schema
nicht, was es leisten soll.

## Inhalt

| Datei | Inhalt |
|---|---|
| `Gegenueberstellung.md` | Vier Geschäftsvorfälle in beiden Varianten, mit Aufrufzählung und antizipierten Einwänden |
| `openapi/netzbetreiber-api.yaml` | OpenAPI 3.1 — 14 Pfade, 22 Operationen, 61 Schemas |
| `examples/01–03` | Gültige Bündel: pauschale MaLo, Überschusseinspeisung, Speicher mit Ladepunkt und Kaskade |
| `examples/04–05` | Negativbeispiele, die abgelehnt werden müssen |
| `examples/06–07` | Clearing-Fall mit Zustand, leichtgewichtiges Änderungsereignis |
| `tools/validate.py` | Prüfwerkzeug |
| `.github/workflows/validate.yml` | CI-Workflow, führt die Prüfung bei jedem Push aus |

## Die wesentlichen Unterschiede

| | Konsultiert | Hier |
|---|---|---|
| HTTP-Verben | nur `POST` (4 Operationen) | `GET` 13, `PUT` 2, `POST` 3, `PATCH` 2, `DELETE` 2 |
| Lesezugriff | nicht vorhanden | auf jede Ressource |
| Identität | Fachschlüssel im Body | URL je Ressource, Verlinkung über `href` |
| Aktualisierung | Vollübermittlung des Bündels | `PATCH` auf Teilressource mit `If-Match` |
| Zeitscheiben-Ende | implizit | `validFrom` **und** `validTo` |
| Fachliche Bedingungen | Prosa im Anwendungshandbuch | `oneOf` + `discriminator` im Schema |
| Fehlermeldung | kein Response-Body definiert | RFC 9457 mit JSON-Pointer |
| Clearing | Aufruf ohne Rückbezug und Endzustand | Ressource mit Zustand, Frist und Abschluss |
| Benachrichtigung | Vollversand an alle Berechtigten | Ereignis mit URL, Abruf nach Bedarf |
| Sicherheit | nicht spezifiziert | OAuth 2.0 mit Scopes, mTLS alternativ |
| Nebenläufigkeit | nicht geregelt | `ETag` / `If-Match` |
| Umsetzungsstand | nicht erkennbar | `GET /versions` |

## Bezug zu den bereits eingereichten Konsultationsbeiträgen

Stand 21.08.2026 liegen im Repository zwölf Konsultationsbeiträge vor (#164–#175), davon
elf von einem einzigen Marktteilnehmer. **Elf der zwölf betreffen `calculationFormula*`.**
Zum Lokationsbündel gibt es genau einen Beitrag — #175 zum Muster der Lokationsbündel-ID.

Beitrag **#172** prüft `calculationFormulaV1.yaml` ausführlich gegen RFC-Vorgaben und
schränkt seinen Geltungsbereich ausdrücklich ein:

> „Es wurde in dieser Prüfung keine Aussage darüber getroffen und auch nicht untersucht, ob
> die übrigen API-Dateien im Repository dieselben, andere oder keine der unten beschriebenen
> Abweichungen aufweisen. […] auch wenn eine strukturelle Ähnlichkeit (gleiche Kopiervorlage,
> gleicher Autor, gleicher Erstellungszeitraum) eine Wahrscheinlichkeit für ähnliche
> Abweichungen nahelegt."

Dieser Referenzentwurf liefert genau diesen Nachweis für `locationBundleV1.yaml`: Die
Befunde zu fehlenden Response-Bodies, fehlenden `securitySchemes`, fehlender `operationId`
und `$ref`-Geschwisterfeldern treten dort identisch auf — und darüber hinaus Mängel, die in
`calculationFormula` keine Entsprechung haben (Zeitscheiben ohne Ende, Clearing ohne
Endzustand, Antwort ohne Ablehnungsmöglichkeit).

**Zur Lokationsbündel-ID:** Wir teilen die Auffassung aus #175, dass das Muster `G` statt
`F` lauten muss. Dieser Entwurf verwendet weiterhin `F`, um gegen den konsultierten Stand
vergleichbar zu bleiben; die Stelle ist im Schema entsprechend kommentiert.

## Lizenz

[CC0 1.0 Universal](LICENSE) — frei verwendbar, einschließlich der Übernahme in offizielle
Dokumente der Bundesnetzagentur, des BDEW oder der Projektgruppe EDI@Energy. Eine
Namensnennung ist nicht erforderlich.

## Kontakt

Engrate AB · Drottninggatan 32 · 111 51 Stockholm · Schweden
Rainer Notter · rainer@engrate.io
