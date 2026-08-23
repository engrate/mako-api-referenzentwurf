# Repository befüllen — Kurzanleitung

Das Paket ist push-fertig. Voraussetzung: `git` und ein GitHub-Login mit Schreibrecht
auf `engrate/mako-api-referenzentwurf`.

```bash
# Im entpackten Ordner:
git init -b main
git add .
git commit -m "Referenzentwurf ressourcenorientierte Lokationsbuendel-API (Konsultation Mitteilung Nr. 57)"
git remote add origin git@github.com:engrate/mako-api-referenzentwurf.git
git push -u origin main

# Eingereichten Stand unveraenderlich festhalten:
git tag -a konsultation-2026-08 -m "Stand der Einreichung zur Konsultation Mitteilung Nr. 57, 31.08.2026"
git push origin konsultation-2026-08
```

Danach im Repository unter **Settings → General** die Beschreibung setzen:

> Ressourcenorientierter Referenzentwurf für den MaKo-Webdienst Lokationsbündel.
> Konsultationsbeitrag zu Mitteilung Nr. 57 der Bundesnetzagentur. OpenAPI 3.1, validiert. CC0.

Als Topics eignen sich: `openapi`, `energy`, `marktkommunikation`, `edi-energy`,
`bundesnetzagentur`, `rest-api`, `germany`.

## Was nach dem Push passiert

Der Workflow `.github/workflows/validate.yml` läuft automatisch und prüft:

1. `openapi/netzbetreiber-api.yaml` gegen die OpenAPI-3.1-Spezifikation
2. die fünf gültigen Beispiele gegen ihre Schemata
3. die beiden Negativbeispiele darauf, dass sie **abgelehnt** werden

Schlägt eine der drei Prüfungen fehl, wird der Lauf rot. Das Badge im README zeigt das
Ergebnis. Erst wenn es grün ist, sollten die Links in die Einreichung gehen — sie sind
dort bereits eingetragen und zeigen auf den Tag `konsultation-2026-08`.

## Reihenfolge

1. Push und Tag setzen
2. Warten, bis der Workflow grün ist (etwa eine Minute)
3. Repository-Beschreibung und Topics setzen
4. Prüfen, dass https://github.com/engrate/mako-api-referenzentwurf/tree/konsultation-2026-08 erreichbar ist
5. Erst dann Stellungnahme versenden und Issues einstellen
