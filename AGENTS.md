# AGENTS.md — guidance for AI coding agents in this repo

## Project

- `products.py`: single-file Python 3 CLI for a small store's product
  inventory (course ISBA2438). **Standard library only** — never add
  third-party imports, and never create `requirements.txt` (its absence is a
  graded constraint, not an oversight).
- Spec of record: `PRD.md`. QA gate: `TEST-MATRIX.md` (every row must pass).
  User docs: `README-OUTLINE.md` (the final `README.md` is built from it).
  Recording plan: `DEMO-SCRIPT.md`.
- One operation per invocation. Never prompt, never read stdin.

## Commands (Windows PowerShell)

- Run the tool: `py -3 products.py [--file PATH] COMMAND [OPTIONS]`
  (`python3` on macOS/Linux).
- Syntax check: `py -m py_compile products.py`
- Type check (optional, only if mypy happens to be installed; NOT a submission
  requirement): `py -m mypy products.py --strict`
- Smoke test: `py -3 products.py --help` and each command's `--help` must exit
  0 **without creating `products.json`**.
- During testing always use `--file` pointing into a scratch/temp directory —
  never create or pollute a real `products.json` in the workspace root.

## Hard constraints (handout contract — breaking any of these is a defect)

- Exit codes: `0` success/help · `1` ID not found, invalid stored data, or
  file read/write failure · `2` invalid syntax, missing args, invalid values.
- Read-only commands (`list`, `get`, `search`, `summary`, all `--help`) must
  never create or modify the data file.
- A failed command must leave the data file byte-identical and must never
  consume an ID.
- Expected errors print a concise stderr message — never a Python traceback.
- `--file PATH` only before the command; missing parent dirs are not created.

## Conventions

- Type hints per PRD §9; `from __future__ import annotations` at the top of
  `products.py`.
- Prices are validated strings stored/printed with exactly two decimals
  (`"4.50"`); regex-validate before any write. Exact money math uses
  `decimal.Decimal`, never floats.
- Keep all code in `products.py`; no packaging, no build files.

## Verification workflow

1. `py -m py_compile products.py`
2. Work through `TEST-MATRIX.md` sections A–F in order, in a scratch
   directory. After any fix, re-run the entire section, not just the failed
   row.
3. Before submission, re-run sections D and E (custom commands) — the
   recorded demo depends on them.
