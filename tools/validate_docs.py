#!/usr/bin/env python3
"""
Validiert die Mintlify-Dokumentation:

1. docs.json ist gültiges JSON und traegt die Pflichtfelder.
2. Jede in der Navigation genannte Seite existiert als .mdx-Datei.
3. Jede .mdx-Datei ist ueber die Navigation erreichbar.
4. Jede referenzierte OpenAPI-Datei liegt am angegebenen Ort und enthaelt
   Operationen.
   Ausserdem: KEIN Navigationseintrag der Form 'METHOD /pfad'. Solche
   Eintraege werden vom Build stillschweigend verworfen und unterdruecken
   dabei die automatische Erzeugung der Operationsseiten - der Bereich
   bleibt dann ohne Fehlermeldung vollstaendig leer.
5. Logo und Favicon liegen am angegebenen Ort.

Die Pruefung kommt ohne Netzzugriff und ohne Node.js aus. Sie ersetzt nicht
den Mintlify-Build, faengt aber die Fehler ab, die eine Dokumentation still
zerfallen lassen: tote Navigationseintraege und verwaiste Seiten.

Aufruf:  python3 tools/validate_docs.py
"""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS_JSON = ROOT / "docs.json"
VERBS = ("get", "put", "post", "patch", "delete", "head", "options", "trace")

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"

failures = []


def head(text):
    print(f"\n{text}\n{'-' * len(text)}")


def ok(text):
    print(f"{GREEN}OK{RESET}  {text}")


def fail(text, detail=None):
    print(f"{RED}FEHLER{RESET}  {text}")
    if detail:
        print(f"     {YELLOW}{detail}{RESET}")
    failures.append(text)


# ------------------------------------------------------------ 1. docs.json
head("1. Konfiguration")

try:
    config = json.loads(DOCS_JSON.read_text(encoding="utf-8"))
    ok(f"{DOCS_JSON.name} ist gueltiges JSON")
except Exception as exc:                                    # noqa: BLE001
    fail(f"{DOCS_JSON.name} ist kein gueltiges JSON", exc)
    sys.exit(1)

for field in ("name", "theme", "navigation"):
    if field not in config:
        fail(f"Pflichtfeld '{field}' fehlt in {DOCS_JSON.name}")
if not config.get("colors", {}).get("primary"):
    fail("Pflichtfeld 'colors.primary' fehlt in docs.json")

if not failures:
    ok("Pflichtfelder name, theme, colors.primary und navigation vorhanden")


# ------------------------------------- Navigation rekursiv einsammeln
def walk(node, pages, specs, spec_stack, in_pages=False):
    """Sammelt Seitenverweise und ordnet ihnen die jeweils geltende
    OpenAPI-Datei zu.

    Als Seitenverweis gilt ausschliesslich ein String innerhalb einer
    'pages'-Liste oder unter 'root' — nicht jeder String der Konfiguration,
    denn Gruppennamen, Symbole und externe Links sind keine Seiten.

    'openapi' gilt fuer den gesamten Teilbaum und wird von einer tieferen
    Angabe ueberschrieben.
    """
    if isinstance(node, dict):
        spec = node.get("openapi")
        if spec:
            entries = spec if isinstance(spec, list) else [spec]
            specs.update(entries)
            spec_stack = spec_stack + [entries]
        for key, value in node.items():
            if key == "openapi":
                continue
            if key == "root" and isinstance(value, str):
                pages.append((value, spec_stack[-1] if spec_stack else None))
                continue
            walk(value, pages, specs, spec_stack, in_pages=(key == "pages"))
    elif isinstance(node, list):
        for item in node:
            walk(item, pages, specs, spec_stack, in_pages=in_pages)
    elif isinstance(node, str) and in_pages:
        pages.append((node, spec_stack[-1] if spec_stack else None))


page_refs, spec_refs = [], set()
walk(config["navigation"], page_refs, spec_refs, [])

# Reine Seitenverweise von 'METHOD /pfad'-Angaben trennen.
UPPER_VERBS = tuple(v.upper() for v in VERBS)
mdx_refs = [(p, s) for p, s in page_refs
            if p.split(" ")[0].upper() not in UPPER_VERBS]
op_refs = [(p, s) for p, s in page_refs
           if p.split(" ")[0].upper() in UPPER_VERBS]


# ------------------------------------------------------------ 2. Seiten
head("2. Seiten der Navigation")

for ref, _ in mdx_refs:
    if not (ROOT / f"{ref}.mdx").is_file():
        fail(f"Navigationseintrag '{ref}' hat keine Datei {ref}.mdx")
if not any(f.startswith("Navigationseintrag") for f in failures):
    ok(f"{len(mdx_refs)} Navigationseintraege verweisen auf vorhandene Seiten")


# --------------------------------------------------- 3. Verwaiste Seiten
head("3. Verwaiste Seiten")

referenced = {ref for ref, _ in mdx_refs}
ignored = {".git", "node_modules", ".github"}
orphans = sorted(
    str(path.relative_to(ROOT).with_suffix(""))
    for path in ROOT.rglob("*.mdx")
    if not any(part in ignored for part in path.relative_to(ROOT).parts)
    and str(path.relative_to(ROOT).with_suffix("")) not in referenced
)
if orphans:
    for orphan in orphans:
        fail(f"{orphan}.mdx ist ueber die Navigation nicht erreichbar")
else:
    ok(f"Alle {len(referenced)} Seiten sind ueber die Navigation erreichbar")


# ------------------------------------------------------------ 4. OpenAPI
head("4. OpenAPI-Verweise")

loaded = {}
for ref in sorted(spec_refs):
    path = ROOT / ref.lstrip("/")
    if not path.is_file():
        fail(f"OpenAPI-Datei '{ref}' nicht gefunden", f"erwartet unter {path}")
        continue
    try:
        loaded[ref] = yaml.safe_load(path.read_text(encoding="utf-8"))
        routes = loaded[ref].get("paths", {})
        n_ops = sum(1 for p in routes.values() for k in p if k in VERBS)
        if not n_ops:
            fail(f"OpenAPI-Datei '{ref}' enthaelt keine Operationen")
        else:
            ok(f"{ref} — {len(routes)} Pfade, {n_ops} Operationen, "
               f"werden automatisch erzeugt")
    except Exception as exc:                                # noqa: BLE001
        fail(f"OpenAPI-Datei '{ref}' ist nicht lesbar", exc)

# Einzeln aufgefuehrte Operationen sind hier unzulaessig: der Build verwirft
# sie stillschweigend UND erzeugt dann auch keine Operationsseiten mehr.
for ref, _ in op_refs:
    fail(f"Navigationseintrag '{ref}' ist ein Operationseintrag",
         "Solche Eintraege werden vom Build verworfen und unterdruecken die "
         "automatische Erzeugung: der Bereich bleibt dann leer. Stattdessen nur "
         "'openapi' setzen und die Operationsseiten automatisch erzeugen lassen.")
if not op_refs:
    ok("Keine Operationseintraege in der Navigation (korrekt)")


# -------------------------------------------------------------- 5. Bilder
head("5. Bilder")

assets = []
if isinstance(config.get("logo"), dict):
    assets += [config["logo"].get(k) for k in ("light", "dark")]
elif isinstance(config.get("logo"), str):
    assets.append(config["logo"])
assets.append(config.get("favicon"))

for asset in [a for a in assets if isinstance(a, str) and not a.startswith("http")]:
    if not (ROOT / asset.lstrip("/")).is_file():
        fail(f"Bilddatei '{asset}' nicht gefunden")
if not any(f.startswith("Bilddatei") for f in failures):
    ok(f"{len([a for a in assets if a])} Bilddateien vorhanden")


# ------------------------------------------------------------- Ergebnis
head("Ergebnis")
if failures:
    print(f"{RED}{len(failures)} Pruefung(en) fehlgeschlagen.{RESET}")
    sys.exit(1)

print(f"{GREEN}Alle Pruefungen bestanden.{RESET}")
n_ops = sum(1 for s in loaded.values()
            for p in s.get("paths", {}).values() for k in p if k in VERBS)
print(f"{len(referenced)} Seiten, {len(spec_refs)} OpenAPI-Datei(en) mit "
      f"{n_ops} automatisch erzeugten Operationsseiten.")
