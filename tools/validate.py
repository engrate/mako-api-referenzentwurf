#!/usr/bin/env python3
"""
Validiert den Referenzentwurf:

1. Die OpenAPI-Datei gegen die OpenAPI-3.1-Spezifikation.
2. Jedes Beispiel gegen das zugehörige Schema aus der OpenAPI-Datei.
3. Die Negativbeispiele: Sie MÜSSEN abgelehnt werden. Wird eines von ihnen
   akzeptiert, schlägt die Prüfung fehl — denn dann leistet das Schema nicht,
   was es leisten soll.

Aufruf:  python3 tools/validate.py
"""

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate as validate_openapi

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "openapi" / "netzbetreiber-api.yaml"
EXAMPLES = sorted((ROOT / "examples").glob("*.json"))

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"

failures = []


def head(text):
    print(f"\n{text}\n{'-' * len(text)}")


# ---------------------------------------------------------------- 1. OpenAPI
head("1. OpenAPI-Spezifikation")

spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
try:
    validate_openapi(spec)
    print(f"{GREEN}OK{RESET}  {SPEC_PATH.name} ist gültiges OpenAPI {spec['openapi']}")
except Exception as exc:                                   # noqa: BLE001
    print(f"{RED}FEHLER{RESET}  {exc}")
    failures.append(SPEC_PATH.name)

paths = spec.get("paths", {})
verbs = ("get", "put", "post", "patch", "delete")
n_ops = sum(1 for p in paths.values() for k in p if k in verbs)
by_verb = {v: sum(1 for p in paths.values() if v in p) for v in verbs}
print(f"     {len(paths)} Pfade, {n_ops} Operationen, "
      f"{len(spec['components']['schemas'])} Schemas")
print(f"     Verbverteilung: " + ", ".join(f"{v.upper()}={n}" for v, n in by_verb.items()))


# ------------------------------------------------- 2./3. Beispiele
head("2. Beispiele gegen die Schemas")

# Die Beispiel-Dateien tragen erklärende Felder mit führendem Unterstrich.
# Sie sind nicht Teil der Nutzdaten und werden vor der Prüfung entfernt.
def strip_meta(node):
    if isinstance(node, dict):
        return {k: strip_meta(v) for k, v in node.items() if not k.startswith("_")}
    if isinstance(node, list):
        return [strip_meta(v) for v in node]
    return node


def resolve_local_refs(node, root):
    """Löst '#/components/schemas/X'-Referenzen auf, damit Draft202012Validator
    ohne Registry arbeiten kann.

    OpenAPI 3.1 erlaubt Geschwisterfelder neben '$ref' (in 3.0 war das ungültig
    und wurde von Werkzeugen verworfen). Sie werden hier über das aufgelöste
    Ziel gelegt.
    """
    if isinstance(node, dict):
        if "$ref" in node and str(node["$ref"]).startswith("#/"):
            target = root
            for part in node["$ref"].lstrip("#/").split("/"):
                target = target[part]
            resolved = resolve_local_refs(target, root)
            siblings = {k: resolve_local_refs(v, root)
                        for k, v in node.items() if k != "$ref"}
            if isinstance(resolved, dict):
                return {**resolved, **siblings}
            return resolved
        return {k: resolve_local_refs(v, root) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve_local_refs(v, root) for v in node]
    return node


def schema_for(name):
    raw = {"$ref": f"#/components/schemas/{name}"}
    resolved = resolve_local_refs(raw, spec)
    # OpenAPI-eigene Schlüsselwörter, die JSON Schema nicht kennt, entfernen.
    def clean(node):
        if isinstance(node, dict):
            return {k: clean(v) for k, v in node.items()
                    if k not in ("discriminator", "xml", "externalDocs")}
        if isinstance(node, list):
            return [clean(v) for v in node]
        return node
    return clean(resolved)


for path in EXAMPLES:
    doc = json.loads(path.read_text(encoding="utf-8"))
    expect_invalid = doc.get("_erwartet") == "ungueltig"
    schema_name = doc.get("_schema", "LocationBundleDocument")
    payload = strip_meta(doc)

    validator = Draft202012Validator(schema_for(schema_name))
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))

    if expect_invalid:
        if errors:
            first = errors[0]
            where = "/" + "/".join(str(p) for p in first.path)
            print(f"{GREEN}OK{RESET}  {path.name}")
            print(f"     erwartungsgemäß abgelehnt bei {where}")
            print(f"     {YELLOW}{first.message[:150]}{RESET}")
        else:
            print(f"{RED}FEHLER{RESET}  {path.name} wurde akzeptiert, "
                  f"hätte aber abgelehnt werden müssen")
            failures.append(path.name)
    else:
        if errors:
            print(f"{RED}FEHLER{RESET}  {path.name} ({schema_name})")
            for err in errors[:5]:
                where = "/" + "/".join(str(p) for p in err.path)
                print(f"     {where}: {err.message[:150]}")
            failures.append(path.name)
        else:
            print(f"{GREEN}OK{RESET}  {path.name} ({schema_name})")


# ---------------------------------------------------------------- Ergebnis
head("Ergebnis")
if failures:
    print(f"{RED}{len(failures)} Prüfung(en) fehlgeschlagen:{RESET} "
          + ", ".join(failures))
    sys.exit(1)

print(f"{GREEN}Alle Prüfungen bestanden.{RESET}")
print(f"{len(EXAMPLES)} Beispiele geprüft, davon "
      f"{sum(1 for p in EXAMPLES if 'UNGUELTIG' in p.name)} Negativbeispiele, "
      f"die korrekt abgelehnt wurden.")
